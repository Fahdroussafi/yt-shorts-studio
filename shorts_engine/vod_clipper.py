from concurrent.futures import ThreadPoolExecutor
import io
import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

from PIL import Image
import requests

from produce_motion_short import FFMPEG, _run_ffmpeg, get_video_duration

YTDLP = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
if not os.path.exists(YTDLP):
    YTDLP = "yt-dlp"

_HELIX_TOKEN = {"token": None, "expires_at": 0.0}


def _get_twitch_helix_headers() -> Optional[Dict[str, str]]:
    """Fetches and caches Twitch Helix App Access Token via TWITCH_CLIENT_ID & TWITCH_CLIENT_SECRET."""
    import time as _time
    cid = os.environ.get("TWITCH_CLIENT_ID", "").strip()
    sec = os.environ.get("TWITCH_CLIENT_SECRET", "").strip()
    if not cid or not sec:
        return None
    now = _time.time()
    if not _HELIX_TOKEN["token"] or now >= _HELIX_TOKEN["expires_at"] - 120:
        try:
            r = requests.post(
                "https://id.twitch.tv/oauth2/token",
                data={"client_id": cid, "client_secret": sec, "grant_type": "client_credentials"},
                timeout=8,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            _HELIX_TOKEN["token"] = data.get("access_token")
            _HELIX_TOKEN["expires_at"] = now + int(data.get("expires_in", 3600))
        except Exception:
            return None
    if not _HELIX_TOKEN["token"]:
        return None
    return {"Client-ID": cid, "Authorization": f"Bearer {_HELIX_TOKEN['token']}"}


def _parse_helix_duration(s: str) -> int:
    total = 0
    for val, unit in re.findall(r"(\d+)([hms])", str(s or "").lower()):
        n = int(val)
        total += n * (3600 if unit == "h" else 60 if unit == "m" else 1)
    return total


def parse_timestamp_sec(val: str) -> float:
    """Parses 'SS', 'MM:SS', or 'HH:MM:SS' into float seconds."""
    s = str(val or "").strip()
    if not s:
        return 0.0
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return float(s)
    parts = [float(p) for p in s.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError(f"Invalid timestamp '{val}'. Use MM:SS or HH:MM:SS.")


def fmt_timestamp(sec: float) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def list_twitch_vods(channel_or_url: str, limit: int = 8) -> List[Dict]:
    """Lists recent Twitch VODs/highlights via Official Helix API (primary) -> GQL -> yt-dlp fallback."""
    target = (channel_or_url or "").strip()
    if not target:
        raise ValueError("Enter your Twitch username or a VOD URL.")

    vod_m = re.search(r"twitch\.tv/videos/(\d+)", target, re.I)
    hdrs = _get_twitch_helix_headers()
    if hdrs:
        try:
            if vod_m:
                v_resp = requests.get("https://api.twitch.tv/helix/videos", params={"id": vod_m.group(1)}, headers=hdrs, timeout=8)
                raw_vids = v_resp.json().get("data", []) if v_resp.status_code == 200 else []
            else:
                handle = re.sub(r"^https?://(?:www\.|m\.)?twitch\.tv/", "", target, flags=re.I).strip("/").split("/")[0].lower()
                u_resp = requests.get("https://api.twitch.tv/helix/users", params={"login": handle}, headers=hdrs, timeout=8)
                users = u_resp.json().get("data", []) if u_resp.status_code == 200 else []
                raw_vids = []
                if users:
                    v_resp = requests.get("https://api.twitch.tv/helix/videos", params={"user_id": users[0]["id"], "first": limit}, headers=hdrs, timeout=8)
                    raw_vids = v_resp.json().get("data", []) if v_resp.status_code == 200 else []
            vods = []
            for v in raw_vids[:limit]:
                dur = _parse_helix_duration(v.get("duration", ""))
                if dur < 15:
                    continue
                thumb = (v.get("thumbnail_url") or "").replace("%{width}", "640").replace("%{height}", "360")
                vods.append({
                    "id": str(v.get("id") or ""),
                    "title": v.get("title") or f"Twitch VOD {v.get('id')}",
                    "url": v.get("url") or f"https://www.twitch.tv/videos/{v.get('id')}",
                    "duration": dur,
                    "duration_str": fmt_timestamp(dur),
                    "thumbnail": thumb,
                    "upload_date": (v.get("created_at") or "")[:10],
                })
            if vods:
                return vods
        except Exception:
            pass

    is_single_vod = bool(vod_m)
    if not is_single_vod:
        handle = re.sub(r"^https?://(?:www\.|m\.)?twitch\.tv/", "", target, flags=re.I).strip("/").split("/")[0].lower()
        try:
            q = json.dumps({"query": f'{{ user(login: "{handle}") {{ videos(first: {limit}) {{ edges {{ node {{ id title lengthSeconds broadcastType createdAt }} }} }} }} }}'})
            r = requests.post(
                "https://gql.twitch.tv/gql",
                headers={"Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko", "Content-Type": "application/json"},
                data=q, timeout=10,
            )
            if r.status_code == 200:
                edges = ((r.json().get("data") or {}).get("user") or {}).get("videos", {}).get("edges") or []
                vods = []
                for edge in edges:
                    n = edge.get("node") or {}
                    vid = str(n.get("id") or "")
                    dur = float(n.get("lengthSeconds") or 0)
                    if vid and dur >= 15:
                        vods.append({
                            "id": vid,
                            "title": n.get("title") or f"Twitch VOD {vid}",
                            "url": f"https://www.twitch.tv/videos/{vid}",
                            "duration": int(dur),
                            "duration_str": fmt_timestamp(dur),
                            "thumbnail": "",
                            "upload_date": (n.get("createdAt") or "")[:10],
                        })
                if vods:
                    return vods
        except Exception:
            pass
        archives_url = f"https://www.twitch.tv/{handle}/videos?filter=archives&sort=time"
        cmd = [YTDLP, "--flat-playlist", "--dump-single-json", "--playlist-end", str(limit), "--no-warnings", archives_url]
    else:
        cmd = [YTDLP, "--dump-single-json", "--skip-download", "--no-warnings", target]

    res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    if res.returncode != 0 or not res.stdout.strip():
        raise RuntimeError(f"Could not load Twitch VODs: {(res.stderr or 'No output')[-300:]}")

    data = json.loads(res.stdout)
    entries = [data] if is_single_vod else (data.get("entries") or [])
    vods = []
    for e in entries[:limit]:
        vid = str(e.get("id") or "").lstrip("v")
        url = e.get("webpage_url") or e.get("url") or (f"https://www.twitch.tv/videos/{vid}" if vid else "")
        dur = float(e.get("duration") or 0)
        if not url:
            continue
        vods.append({
            "id": vid,
            "title": e.get("title") or f"Twitch VOD {vid}",
            "url": url,
            "duration": int(dur),
            "duration_str": fmt_timestamp(dur) if dur else "VOD",
            "thumbnail": e.get("thumbnail") or "",
            "upload_date": e.get("upload_date") or "",
        })
    return vods


def list_twitch_channel_clips(channel_or_url: str, limit: int = 8) -> List[Dict]:
    """Fetches your own channel's Twitch clips via Official Helix API."""
    target = (channel_or_url or "").strip()
    if not target or re.search(r"twitch\.tv/videos/\d+", target, re.I):
        return []
    hdrs = _get_twitch_helix_headers()
    if not hdrs:
        return []
    handle = re.sub(r"^https?://(?:www\.|m\.)?twitch\.tv/", "", target, flags=re.I).strip("/").split("/")[0].lower()
    try:
        u_resp = requests.get("https://api.twitch.tv/helix/users", params={"login": handle}, headers=hdrs, timeout=8)
        users = u_resp.json().get("data", []) if u_resp.status_code == 200 else []
        if not users:
            return []
        c_resp = requests.get("https://api.twitch.tv/helix/clips", params={"broadcaster_id": users[0]["id"], "first": limit}, headers=hdrs, timeout=8)
        clips = c_resp.json().get("data", []) if c_resp.status_code == 200 else []
        game_ids = list({c.get("game_id") for c in clips if c.get("game_id")})
        game_map = {}
        if game_ids:
            g_resp = requests.get("https://api.twitch.tv/helix/games", params=[("id", gid) for gid in game_ids], headers=hdrs, timeout=6)
            for g in (g_resp.json().get("data", []) if g_resp.status_code == 200 else []):
                game_map[g["id"]] = g.get("name", "")
        return [{
            "id": c.get("id", ""),
            "title": c.get("title") or "Twitch Clip",
            "url": c.get("url", ""),
            "duration": int(round(float(c.get("duration") or 30))),
            "duration_str": fmt_timestamp(float(c.get("duration") or 30)),
            "game_name": game_map.get(c.get("game_id"), ""),
            "view_count": int(c.get("view_count") or 0),
        } for c in clips if c.get("url")]
    except Exception:
        return []


_TWITCH_GQL_CHAT_HASH = "b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a"


def _scan_single_vod_chat_spikes(vod_id: str, duration: int, min_msgs_per_min: int = 60) -> List[Dict]:
    """Samples evenly across a VOD via Twitch GQL chat replay and computes real msgs/min velocity."""
    if duration < 90:
        return []
    offsets = [int(duration * f) for f in (0.08, 0.18, 0.28, 0.38, 0.48, 0.58, 0.68, 0.78, 0.88)]
    hdrs = {"Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko", "Content-Type": "application/json"}

    def _probe(off: int):
        try:
            r = requests.post(
                "https://gql.twitch.tv/gql",
                headers=hdrs,
                json={
                    "operationName": "VideoCommentsByOffsetOrCursor",
                    "variables": {"videoID": str(vod_id), "contentOffsetSeconds": off},
                    "extensions": {"persistedQuery": {"version": 1, "sha256Hash": _TWITCH_GQL_CHAT_HASH}},
                },
                timeout=6,
            )
            if r.status_code != 200:
                return None
            edges = (((r.json().get("data") or {}).get("video") or {}).get("comments") or {}).get("edges") or []
            if len(edges) < 5:
                return None
            offs = [int((e.get("node") or {}).get("contentOffsetSeconds") or off) for e in edges]
            span = max(3.0, float(max(offs) - min(offs)))
            mpm = int(round((len(edges) / span) * 60.0))
            mid_node = edges[len(edges) // 2].get("node") or {}
            frags = (mid_node.get("message") or {}).get("fragments") or []
            sample = "".join(fr.get("text", "") for fr in frags).strip()[:60]
            center = offs[len(offs) // 2]
            return (mpm, center, sample)
        except Exception:
            return None

    hits = [h for h in (_probe(o) for o in offsets) if h and h[0] >= min_msgs_per_min]
    hits.sort(key=lambda x: x[0], reverse=True)
    out = []
    for mpm, center, sample in hits[:3]:
        st = max(0, center - 12)
        et = min(duration, st + 32)
        if et - st < 10:
            continue
        out.append({
            "start": fmt_timestamp(st),
            "end": fmt_timestamp(et),
            "start_sec": st,
            "end_sec": et,
            "msgs_per_min": mpm,
            "sample": sample,
        })
    return out


def scan_top_gta_chat_spikes(min_msgs_per_min: int = 80, limit_streams: int = 12, language: str = "en") -> Dict:
    """Agent 1: Polls top live GTA VI / GTA V Twitch streams via Helix and finds chat-explosion moments."""
    hdrs = _get_twitch_helix_headers()
    if not hdrs:
        raise RuntimeError("TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET are required.")

    s_resp = requests.get(
        "https://api.twitch.tv/helix/streams",
        params=[("game_id", "1867279146"), ("game_id", "32982"), ("first", 30)],
        headers=hdrs,
        timeout=8,
    )
    streams = s_resp.json().get("data", []) if s_resp.status_code == 200 else []
    if language and language != "all":
        filtered = [s for s in streams if (s.get("language") or "").lower() == language.lower()]
        if filtered:
            streams = filtered
    streams = streams[:limit_streams]

    def _inspect_streamer(st):
        uid = st.get("user_id")
        try:
            v_resp = requests.get(
                "https://api.twitch.tv/helix/videos",
                params={"user_id": uid, "type": "archive", "first": 1},
                headers=hdrs,
                timeout=8,
            )
            vids = v_resp.json().get("data", []) if v_resp.status_code == 200 else []
            if not vids:
                return []
            v = vids[0]
            dur = _parse_helix_duration(v.get("duration", ""))
            if dur < 60:
                return []
            sp_list = _scan_single_vod_chat_spikes(v["id"], dur, min_msgs_per_min=min_msgs_per_min)
            thumb = (v.get("thumbnail_url") or "").replace("%{width}", "320").replace("%{height}", "180")
            for sp in sp_list:
                sp.update({
                    "streamer": st.get("user_name") or st.get("user_login"),
                    "viewer_count": int(st.get("viewer_count") or 0),
                    "game_name": st.get("game_name") or "Grand Theft Auto",
                    "vod_id": v["id"],
                    "vod_url": v.get("url") or f"https://www.twitch.tv/videos/{v['id']}",
                    "vod_title": v.get("title") or st.get("title") or "GTA Stream",
                    "thumbnail": thumb,
                })
            return sp_list
        except Exception:
            return []

    all_spikes: List[Dict] = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(_inspect_streamer, streams):
            all_spikes.extend(res)

    all_spikes.sort(key=lambda x: x["msgs_per_min"], reverse=True)
    return {"streams_scanned": len(streams), "spikes": all_spikes[:15]}


def _parse_hls_playlist(m3u8_url: str) -> Tuple[bytes, List[Tuple[float, float, str]]]:
    """Fetches an HLS playlist and returns (init_bytes, [(start_sec, end_sec, seg_url), ...])."""
    base = m3u8_url.rsplit("/", 1)[0] + "/"
    txt = requests.get(m3u8_url, timeout=10).text
    init_bytes = b""
    init_m = re.search(r'#EXT-X-MAP:URI="([^"]+)"', txt)
    if init_m:
        u = init_m.group(1)
        init_url = u if u.startswith("http") else (base + u)
        init_bytes = requests.get(init_url, timeout=10).content

    segs = []
    t_acc = 0.0
    cur_dur = 10.0
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF:"):
            cur_dur = float(line.split(":", 1)[1].split(",")[0])
        elif line and not line.startswith("#"):
            seg_url = line if line.startswith("http") else (base + line)
            segs.append((t_acc, t_acc + cur_dur, seg_url))
            t_acc += cur_dur
    return init_bytes, segs


def _fetch_hls_window_bytes(init_bytes: bytes, segs: List[Tuple[float, float, str]], start_sec: float, end_sec: float) -> Tuple[bytes, float]:
    chosen = [s for s in segs if s[1] > start_sec and s[0] < end_sec]
    if not chosen:
        return b"", 0.0
    with ThreadPoolExecutor(max_workers=4) as ex:
        blobs = list(ex.map(lambda s: requests.get(s[2], timeout=12).content, chosen))
    return init_bytes + b"".join(blobs), max(0.0, start_sec - chosen[0][0])


def _score_audio_contrast(audio_bytes: bytes, window_start_sec: float) -> Tuple[float, float, float]:
    """Decodes an audio window and returns (sustained_spike, exact_peak_sec, median_rms)."""
    if not audio_bytes:
        return 1.0, window_start_sec + 15.0, 0.0
    p = subprocess.Popen(
        [FFMPEG, "-loglevel", "error", "-i", "pipe:0", "-vn", "-ar", "4000", "-ac", "1", "-f", "s16le", "pipe:1"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    pcm, _ = p.communicate(audio_bytes, timeout=15)
    sec_bytes = 4000 * 2  # 4kHz * 2 bytes/sample
    n_secs = len(pcm) // sec_bytes
    if n_secs < 4:
        return 1.0, window_start_sec + 15.0, 0.0

    rms_vals = []
    for i in range(n_secs):
        chunk = pcm[i * sec_bytes : (i + 1) * sec_bytes]
        samples = struct.unpack(f"<{len(chunk)//2}h", chunk)
        rms = math.sqrt(sum(s * s for s in samples) / max(1, len(samples)))
        rms_vals.append(rms)

    sorted_r = sorted(rms_vals)
    median_r = sorted_r[len(sorted_r) // 2]
    # Sustained burst: average of top 4 loudest seconds (ignores 1s UI beeps)
    top4_avg = sum(sorted_r[-4:]) / min(4, len(sorted_r))
    spike = min(6.0, top4_avg / max(120.0, median_r))
    if median_r < 150.0:  # Penalize pause/loading-screen silence -> gameplay jumps
        spike *= 0.35

    # Center exact_peak_sec on the hottest 3-second rolling burst
    best_i = max(range(n_secs - 2), key=lambda i: rms_vals[i] + rms_vals[i + 1] + rms_vals[i + 2])
    exact_peak_sec = window_start_sec + best_i + 1.5
    return spike, exact_peak_sec, median_r


def _tile_is_valid(gray_bytes: bytes) -> bool:
    """Rejects near-black loading screens and flat solid-color pause menus."""
    n = len(gray_bytes)
    mean_b = sum(gray_bytes) / n
    if mean_b < 18.0:
        return False
    std_b = math.sqrt(sum((x - mean_b) ** 2 for x in gray_bytes) / n)
    return std_b >= 18.0


def _scan_storyboard_candidates(info: dict, top_k: int = 18) -> List[Tuple[float, float, str]]:
    """Pass 1: Scans sb0/sb1 storyboard sheets, skips black/flat loading screens, and returns (ts, z, preview_b64)."""
    import base64
    sbs = [f for f in (info.get("formats") or []) if str(f.get("format_id", "")).startswith("sb") and f.get("fragments")]
    if not sbs:
        return []
    sb = sorted(sbs, key=lambda f: int(f.get("width") or 0), reverse=True)[0]
    cols = int(sb.get("columns") or 5)
    rows = int(sb.get("rows") or 10)
    tw = int(sb.get("width") or 220)
    th = int(sb.get("height") or 124)
    duration = float(info.get("duration") or 0)
    frags = sb.get("fragments") or []

    def _dl_sheet(frag):
        u = frag.get("url")
        if not u:
            return None
        try:
            r = requests.get(u, timeout=10)
            return r.content if r.status_code == 200 else None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=4) as ex:
        sheets = list(ex.map(_dl_sheet, frags))

    tiles: List[Tuple[bytes, Image.Image]] = []
    for raw in sheets:
        if not raw:
            continue
        try:
            rgb_im = Image.open(io.BytesIO(raw)).convert("RGB")
            gray_im = rgb_im.convert("L")
            sw, sh = rgb_im.size
            for r_idx in range(rows):
                y0 = r_idx * th
                if y0 + th > sh:
                    break
                for c_idx in range(cols):
                    x0 = c_idx * tw
                    if x0 + tw > sw:
                        break
                    box = (x0, y0, x0 + tw, y0 + th)
                    g_bytes = gray_im.crop(box).resize((64, 36)).tobytes()
                    tiles.append((g_bytes, rgb_im.crop(box)))
        except Exception:
            continue

    if len(tiles) < 4 or duration <= 0:
        return []

    sec_per_tile = duration / len(tiles)
    diffs = []
    for i in range(1, len(tiles)):
        a, _ = tiles[i - 1]
        b, rgb_b = tiles[i]
        if not (_tile_is_valid(a) and _tile_is_valid(b)):
            continue
        mad = sum(abs(x - y) for x, y in zip(a, b)) / len(a)
        diffs.append((i, i * sec_per_tile, mad, rgb_b))

    if not diffs:
        return []

    mean_d = sum(d for _, _, d, _ in diffs) / len(diffs)
    std_d = math.sqrt(sum((d - mean_d) ** 2 for _, _, d, _ in diffs) / len(diffs)) or 1.0

    scored = [(ts, max(0.0, (d - mean_d) / std_d), rgb_b) for _, ts, d, rgb_b in diffs]
    scored.sort(key=lambda x: x[1], reverse=True)

    picked: List[Tuple[float, float, str]] = []
    for ts, z, rgb_b in scored:
        if ts < 15 or ts > duration - 20:
            continue
        if any(abs(ts - pts) < 90.0 for pts, _, _ in picked):
            continue
        buf = io.BytesIO()
        rgb_b.save(buf, format="JPEG", quality=75)
        b64_img = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        picked.append((ts, z, b64_img))
        if len(picked) >= top_k:
            break
    return picked


def find_vod_highlights(vod_url: str, top_n: int = 8) -> List[Dict]:
    """Two-pass highlight finder: Storyboard visual jumps + sustained Audio_Only burst snapped to exact peak second."""
    res = subprocess.run(
        [YTDLP, "--dump-single-json", "--skip-download", "--no-warnings", vod_url],
        capture_output=True, text=True, timeout=25,
    )
    if res.returncode != 0 or not res.stdout.strip():
        raise RuntimeError(f"Could not inspect VOD: {(res.stderr or '')[-300:]}")
    info = json.loads(res.stdout)
    duration = float(info.get("duration") or 0)
    if duration < 20:
        raise RuntimeError("VOD is too short or still processing.")

    visual_cands = _scan_storyboard_candidates(info, top_k=18)
    if not visual_cands:
        step = max(90.0, duration / 18.0)
        visual_cands = [(t, 1.0, "") for t in [step * i for i in range(1, 18)] if t < duration - 25]

    audio_fmt = next((f for f in (info.get("formats") or []) if f.get("format_id") == "Audio_Only" and f.get("url")), None)
    audio_scored: List[Tuple[float, float, float, float, str]] = []

    if audio_fmt:
        try:
            init_b, segs = _parse_hls_playlist(audio_fmt["url"])

            def _eval_cand(item):
                ts, vz, prev_img = item
                win_start = max(0.0, ts - 18.0)
                win_end = min(duration, ts + 22.0)
                ab, trim_off = _fetch_hls_window_bytes(init_b, segs, win_start, win_end)
                actual_win_start = max(0.0, win_start - trim_off)
                ac, exact_peak, _med = _score_audio_contrast(ab, actual_win_start)
                combined = vz * 0.45 + ac * 0.55
                return (exact_peak, combined, vz, ac, prev_img)

            with ThreadPoolExecutor(max_workers=4) as ex:
                audio_scored = list(ex.map(_eval_cand, visual_cands))
        except Exception:
            audio_scored = [(ts, vz, vz, 1.0, prev_img) for ts, vz, prev_img in visual_cands]
    else:
        audio_scored = [(ts, vz, vz, 1.0, prev_img) for ts, vz, prev_img in visual_cands]

    audio_scored.sort(key=lambda x: x[1], reverse=True)
    final: List[Dict] = []
    for peak_ts, score, vz, ac, prev_img in audio_scored:
        if any(abs(peak_ts - f["peak_sec"]) < 180.0 for f in final):
            continue
        st = max(0, int(peak_ts - 12))
        et = min(int(duration), st + 30)
        if et - st < 15:
            continue
        final.append({
            "peak_sec": peak_ts,
            "start": fmt_timestamp(st),
            "end": fmt_timestamp(et),
            "start_sec": st,
            "end_sec": et,
            "score": round(score, 2),
            "visual_z": round(vz, 2),
            "audio_spike": round(ac, 2),
            "preview_img": prev_img,
        })
        if len(final) >= top_n:
            break

    return final


def download_vod_slice(vod_url: str, start_sec: float, end_sec: float, dest_mp4: str) -> float:
    """Downloads a Twitch Clip directly or slices [start_sec, end_sec] from a VOD via Python HLS."""
    if "/clip/" in vod_url or "clips.twitch.tv" in vod_url:
        res = subprocess.run([YTDLP, "-f", "best[ext=mp4]/best", "-o", dest_mp4, "--no-warnings", vod_url], capture_output=True, text=True, timeout=60)
        if res.returncode != 0 or not os.path.exists(dest_mp4):
            raise RuntimeError(f"Clip download failed: {(res.stderr or '')[-300:]}")
        actual = get_video_duration(dest_mp4)
        return min(max(actual if actual > 1.0 else 30.0, 5.0), 58.0)

    if end_sec <= start_sec:
        raise ValueError("End time must be after start time.")
    dur = min(max(end_sec - start_sec, 5.0), 58.0)
    end_clamped = start_sec + dur

    m3u8_url = subprocess.check_output(
        [YTDLP, "-g", "-f", "720p60/1080p60/480p/b[height<=1080]", "--no-warnings", vod_url],
        text=True, timeout=25,
    ).strip().splitlines()[0]

    init_b, segs = _parse_hls_playlist(m3u8_url)
    raw_bytes, trim_off = _fetch_hls_window_bytes(init_b, segs, start_sec, end_clamped)
    if not raw_bytes:
        raise RuntimeError("No HLS video segments matched that timestamp window.")

    fd, tmp_raw = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    try:
        with open(tmp_raw, "wb") as f:
            f.write(raw_bytes)
        res = _run_ffmpeg([FFMPEG, "-y", "-ss", f"{trim_off:.2f}", "-t", f"{dur:.2f}", "-i", tmp_raw, "-c", "copy", dest_mp4])
        if res.returncode != 0 or not os.path.exists(dest_mp4) or os.path.getsize(dest_mp4) < 50_000:
            raise RuntimeError(f"VOD slice trim failed: {(res.stderr or '')[-300:]}")
    finally:
        if os.path.exists(tmp_raw):
            try:
                os.remove(tmp_raw)
            except Exception:
                pass

    actual_dur = get_video_duration(dest_mp4)
    return min(max(actual_dur if actual_dur > 1.0 else dur, 5.0), 58.0)


_OPENROUTER_VISION_MODELS = [
    "nvidia/nemotron-3.5-super-vl:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
    "particle-ai/particle-1:free",
]


def analyze_clip_with_vision(clip_mp4: str, duration: float, vod_title: str = "", game_name: str = "") -> Optional[Dict]:
    """Extracts 3 frames (start, peak, end) and uses OpenRouter free Vision to generate clip-accurate hook/title/TTS."""
    import base64
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key or not os.path.exists(clip_mp4):
        return None

    times = [min(2.0, duration * 0.15), duration * 0.48, max(2.5, duration - 2.0)]
    b64_frames = []
    fd_list = []
    try:
        for t_sec in times:
            fd, jpg = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            fd_list.append(jpg)
            r = _run_ffmpeg([FFMPEG, "-y", "-ss", f"{t_sec:.2f}", "-i", clip_mp4, "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "5", jpg])
            if r.returncode == 0 and os.path.exists(jpg) and os.path.getsize(jpg) > 1000:
                b64_frames.append(base64.b64encode(open(jpg, "rb").read()).decode("ascii"))
    finally:
        for jpg in fd_list:
            if os.path.exists(jpg):
                try:
                    os.remove(jpg)
                except Exception:
                    pass

    if not b64_frames:
        return None

    ctx = f"Stream: '{vod_title}'." if vod_title else ""
    if game_name:
        ctx += f" Game: {game_name}."
    prompt_txt = (
        f"These 3 frames are the start, middle, and end of a 30s gameplay highlight clip. {ctx} "
        "Look closely at what is happening on screen and write accurate, non-generic YouTube Shorts metadata. "
        "Respond ONLY with valid JSON: "
        '{"hook_banner":"ALL CAPS 3-6 WORD HOOK UNDER 36 CHARS ABOUT THIS EXACT SCENE",'
        '"tts_opener":"One punchy 6-10 word spoken opener reacting to what happens on screen",'
        '"title":"Punchy title under 50 chars + #shorts + game hashtag",'
        '"tags":"5 comma-separated relevant search tags",'
        '"pinned_comment":"Short question about this exact moment"}'
    )
    content_blocks = [{"type": "text", "text": prompt_txt}]
    for bf in b64_frames:
        content_blocks.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{bf}"}})

    for mid in _OPENROUTER_VISION_MODELS:
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": mid,
                    "reasoning": {"enabled": False},
                    "messages": [{"role": "user", "content": content_blocks}],
                    "max_tokens": 700,
                    "temperature": 0.4,
                },
                timeout=20,
            )
            if resp.status_code != 200:
                continue
            msg = resp.json()["choices"][0]["message"]
            raw = msg.get("content") or msg.get("reasoning") or ""
            raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
            m = re.search(r"(\{[\s\S]*\})", raw)
            if not m:
                continue
            parsed = json.loads(m.group(1))
            if parsed.get("hook_banner") or parsed.get("title"):
                parsed["model_used"] = mid
                return parsed
        except Exception:
            continue
    return None


def render_vod_cinema_short(
    clip_mp4: str,
    output_mp4: str,
    duration: float,
    ass_path: Optional[str] = None,
    tts_audio_path: Optional[str] = None,
):
    """Renders 1080x1920 Cinema Frame Short from raw Series X VOD clip (game audio + optional TTS hook)."""
    ass_filter = ""
    if ass_path and os.path.exists(ass_path):
        clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        ass_filter = f",ass='{clean_ass}'"

    vf = (
        f"[0:v]trim=duration={duration:.3f},setpts=PTS-STARTPTS,fps=30,eq=contrast=1.06:saturation=1.10,split=2[bg_src][fg_src];"
        f"[bg_src]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=6:2,scale=1080:1920:flags=bilinear,setsar=1[vbg];"
        f"[fg_src]scale=1080:-2,setsar=1[vfg];"
        f"[vbg][vfg]overlay=(W-w)/2:(H-h)/2{ass_filter}[vfinal]"
    )

    inputs = ["-i", clip_mp4]
    if tts_audio_path and os.path.exists(tts_audio_path):
        inputs.extend(["-i", tts_audio_path])
        inputs.extend(["-f", "lavfi", "-t", "0.45", "-i", "aevalsrc=0.22*sin(2*PI*55*t)*exp(-6*t):d=0.45:s=44100"])
        af = (
            f"[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[agame];"
            f"[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,asplit=2[av1][av2];"
            f"[agame][av1]sidechaincompress=threshold=0.025:ratio=4:attack=20:release=250[aduck];"
            f"[aduck][av2][2:a]amix=inputs=3:duration=first:weights=0.85 1.0 0.35[afinal]"
        )
    else:
        inputs.extend(["-f", "lavfi", "-t", "0.45", "-i", "aevalsrc=0.22*sin(2*PI*55*t)*exp(-6*t):d=0.45:s=44100"])
        af = (
            f"[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[agame];"
            f"[agame][1:a]amix=inputs=2:duration=first:weights=1.0 0.35[afinal]"
        )

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", f"{vf};{af}",
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-map_metadata", "-1",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "19",
        "-threads", "2",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{duration:.2f}",
        output_mp4,
    ]
    res = _run_ffmpeg(cmd)
    if res.returncode != 0 or not os.path.exists(output_mp4) or os.path.getsize(output_mp4) < 300_000:
        raise RuntimeError(f"VOD render failed: {(res.stderr or '')[-500:]}")
