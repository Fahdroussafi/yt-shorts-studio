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
    """Lists recent Twitch past broadcasts (VODs) for a username or returns metadata for a single VOD URL."""
    target = (channel_or_url or "").strip()
    if not target:
        raise ValueError("Enter your Twitch username or a VOD URL.")

    is_single_vod = bool(re.search(r"twitch\.tv/videos/\d+", target, re.I))
    if is_single_vod:
        cmd = [YTDLP, "--dump-single-json", "--skip-download", "--no-warnings", target]
    else:
        handle = re.sub(r"^https?://(?:www\.)?twitch\.tv/", "", target, flags=re.I).strip("/").split("/")[0]
        archives_url = f"https://www.twitch.tv/{handle}/videos?filter=archives&sort=time"
        cmd = [YTDLP, "--flat-playlist", "--dump-single-json", "--playlist-end", str(limit), "--no-warnings", archives_url]

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


def _score_audio_contrast(audio_bytes: bytes) -> float:
    """Decodes an fMP4/TS audio window to 4kHz mono PCM and computes peak/median RMS contrast."""
    if not audio_bytes:
        return 1.0
    p = subprocess.Popen(
        [FFMPEG, "-loglevel", "error", "-i", "pipe:0", "-vn", "-ar", "4000", "-ac", "1", "-f", "s16le", "pipe:1"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    pcm, _ = p.communicate(audio_bytes, timeout=15)
    sec_bytes = 4000 * 2  # 4kHz * 2 bytes/sample
    n_secs = len(pcm) // sec_bytes
    if n_secs < 3:
        return 1.0

    rms_vals = []
    for i in range(n_secs):
        chunk = pcm[i * sec_bytes : (i + 1) * sec_bytes]
        samples = struct.unpack(f"<{len(chunk)//2}h", chunk)
        rms = math.sqrt(sum(s * s for s in samples) / max(1, len(samples)))
        rms_vals.append(rms)

    sorted_r = sorted(rms_vals)
    median_r = sorted_r[len(sorted_r) // 2]
    peak_r = max(rms_vals)
    return min(6.0, peak_r / max(80.0, median_r))


def _scan_storyboard_candidates(info: dict, top_k: int = 18) -> List[Tuple[float, float]]:
    """Pass 1: Scans sb0/sb1 storyboard sprite sheets (~1-4 MB) for frame-to-frame visual action jumps."""
    sbs = [f for f in (info.get("formats") or []) if str(f.get("format_id", "")).startswith("sb") and f.get("fragments")]
    if not sbs:
        return []
    # Prefer sb0 (higher res 220x124) over sb1
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

    tiles: List[bytes] = []
    for raw in sheets:
        if not raw:
            continue
        try:
            im = Image.open(io.BytesIO(raw)).convert("L")
            sw, sh = im.size
            for r_idx in range(rows):
                y0 = r_idx * th
                if y0 + th > sh:
                    break
                for c_idx in range(cols):
                    x0 = c_idx * tw
                    if x0 + tw > sw:
                        break
                    tile = im.crop((x0, y0, x0 + tw, y0 + th)).resize((64, 36))
                    tiles.append(tile.tobytes())
        except Exception:
            continue

    if len(tiles) < 4 or duration <= 0:
        return []

    sec_per_tile = duration / len(tiles)
    diffs = []
    for i in range(1, len(tiles)):
        a, b = tiles[i - 1], tiles[i]
        mad = sum(abs(x - y) for x, y in zip(a, b)) / len(a)
        diffs.append((i * sec_per_tile, mad))

    mean_d = sum(d for _, d in diffs) / len(diffs)
    std_d = math.sqrt(sum((d - mean_d) ** 2 for _, d in diffs) / len(diffs)) or 1.0

    scored = [(ts, max(0.0, (d - mean_d) / std_d)) for ts, d in diffs]
    scored.sort(key=lambda x: x[1], reverse=True)

    picked: List[Tuple[float, float]] = []
    for ts, z in scored:
        if ts < 15 or ts > duration - 20:
            continue
        if any(abs(ts - pts) < 90.0 for pts, _ in picked):
            continue
        picked.append((ts, z))
        if len(picked) >= top_k:
            break
    return picked


def find_vod_highlights(vod_url: str, top_n: int = 8) -> List[Dict]:
    """Two-pass highlight finder for 1-14h silent gameplay VODs: Storyboard visual jumps + Audio_Only contrast."""
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
        # Uniform fallback samples if storyboard isn't generated yet
        step = max(90.0, duration / 18.0)
        visual_cands = [(t, 1.0) for t in [step * i for i in range(1, 18)] if t < duration - 25]

    audio_fmt = next((f for f in (info.get("formats") or []) if f.get("format_id") == "Audio_Only" and f.get("url")), None)
    audio_scored: List[Tuple[float, float, float, float]] = []

    if audio_fmt:
        try:
            init_b, segs = _parse_hls_playlist(audio_fmt["url"])

            def _eval_cand(item):
                ts, vz = item
                ab, _ = _fetch_hls_window_bytes(init_b, segs, max(0.0, ts - 15.0), min(duration, ts + 25.0))
                ac = _score_audio_contrast(ab)
                combined = vz * 0.45 + ac * 0.55
                return (ts, combined, vz, ac)

            with ThreadPoolExecutor(max_workers=4) as ex:
                audio_scored = list(ex.map(_eval_cand, visual_cands))
        except Exception:
            audio_scored = [(ts, vz, vz, 1.0) for ts, vz in visual_cands]
    else:
        audio_scored = [(ts, vz, vz, 1.0) for ts, vz in visual_cands]

    audio_scored.sort(key=lambda x: x[1], reverse=True)
    final: List[Dict] = []
    for ts, score, vz, ac in audio_scored:
        if any(abs(ts - f["peak_sec"]) < 180.0 for f in final):
            continue
        st = max(0, int(ts - 12))
        et = min(int(duration), st + 32)
        if et - st < 15:
            continue
        final.append({
            "peak_sec": ts,
            "start": fmt_timestamp(st),
            "end": fmt_timestamp(et),
            "start_sec": st,
            "end_sec": et,
            "score": round(score, 2),
            "visual_z": round(vz, 2),
            "audio_spike": round(ac, 2),
        })
        if len(final) >= top_n:
            break

    return final


def download_vod_slice(vod_url: str, start_sec: float, end_sec: float, dest_mp4: str) -> float:
    """Downloads only [start_sec, end_sec] from a Twitch VOD via Python HLS (avoids static ffmpeg DNS bugs)."""
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
