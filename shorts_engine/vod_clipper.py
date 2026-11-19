import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional

import requests

from produce_motion_short import FFMPEG, _run_ffmpeg, get_video_duration

YTDLP = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
if not os.path.exists(YTDLP):
    YTDLP = "yt-dlp"

TWITCH_GQL_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"


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


def scan_vod_chat_spikes(vod_id: str, duration: float, top_n: int = 6) -> List[Dict]:
    """Scans Twitch GQL chat replay for hype/message spikes (returns [] silently if chat is empty)."""
    clean_id = str(vod_id or "").lstrip("v")
    if not clean_id.isdigit():
        return []

    buckets: Dict[int, int] = {}
    samples: Dict[int, str] = {}
    cursor = None
    try:
        for _ in range(10):
            variables = {"videoID": clean_id, "cursor": cursor} if cursor else {"videoID": clean_id, "contentOffsetSeconds": 0}
            payload = {
                "operationName": "VideoCommentsByOffsetOrCursor",
                "variables": variables,
                "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a"}},
            }
            r = requests.post(
                "https://gql.twitch.tv/gql",
                headers={"Client-ID": TWITCH_GQL_CLIENT_ID, "Content-Type": "application/json"},
                json=payload,
                timeout=6,
            )
            if r.status_code != 200:
                break
            comments = r.json().get("data", {}).get("video", {}).get("comments") or {}
            edges = comments.get("edges") or []
            if not edges:
                break
            for edge in edges:
                node = edge.get("node") or {}
                off = int(node.get("contentOffsetSeconds") or 0)
                b = (off // 30) * 30
                buckets[b] = buckets.get(b, 0) + 1
                if b not in samples:
                    frags = (node.get("message") or {}).get("fragments") or []
                    msg = "".join(fr.get("text", "") for fr in frags).strip()
                    if msg:
                        samples[b] = msg[:60]
                cursor = edge.get("cursor")
            if not (comments.get("pageInfo") or {}).get("hasNextPage"):
                break
    except Exception:
        return []

    if not buckets:
        return []

    ranked = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[:top_n]
    out = []
    for b, cnt in ranked:
        st = max(0, b - 10)
        et = min(int(duration) if duration > 0 else b + 30, st + 35)
        out.append({
            "start": fmt_timestamp(st),
            "end": fmt_timestamp(et),
            "start_sec": st,
            "end_sec": et,
            "messages": cnt,
            "sample": samples.get(b, ""),
        })
    return out


def download_vod_slice(vod_url: str, start_sec: float, end_sec: float, dest_mp4: str) -> float:
    """Downloads only the requested [start_sec, end_sec] slice from a Twitch VOD using yt-dlp."""
    if end_sec <= start_sec:
        raise ValueError("End time must be after start time.")
    dur = min(max(end_sec - start_sec, 5.0), 58.0)
    end_clamped = start_sec + dur

    section = f"*{fmt_timestamp(start_sec)}-{fmt_timestamp(end_clamped)}"
    cmd = [
        YTDLP,
        "--download-sections", section,
        "--force-keyframes-at-cuts",
        "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b",
        "--merge-output-format", "mp4",
        "-o", dest_mp4,
        "--no-warnings",
        vod_url,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if res.returncode != 0 or not os.path.exists(dest_mp4):
        raise RuntimeError(f"VOD slice download failed: {(res.stderr or '')[-400:]}")
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
        # Duck game audio slightly while TTS hook plays, plus 0.45s 55Hz impact
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
