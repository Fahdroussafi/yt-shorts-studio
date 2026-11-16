import os
import sys
import time
import shutil
import requests
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple

from engine import FFMPEG, FONTS_DIR
from produce_motion_short import _run_ffmpeg, get_video_duration

_TWITCH_TOKEN_CACHE = {"token": None, "expires_at": 0.0}

GAME_MAP = {
    "gta6": ["Grand Theft Auto VI"],
    "gta5": ["Grand Theft Auto V"],
    "all": ["Grand Theft Auto VI", "Grand Theft Auto V"],
}


def get_twitch_app_token() -> str:
    """Fetches and caches Twitch App Access Token via client_credentials."""
    now = time.time()
    if _TWITCH_TOKEN_CACHE["token"] and now < _TWITCH_TOKEN_CACHE["expires_at"] - 60:
        return _TWITCH_TOKEN_CACHE["token"]

    cid = os.environ.get("TWITCH_CLIENT_ID", "").strip()
    sec = os.environ.get("TWITCH_CLIENT_SECRET", "").strip()
    if not cid or not sec:
        raise RuntimeError("TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be set in .env")

    r = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={"client_id": cid, "client_secret": sec, "grant_type": "client_credentials"},
        timeout=10,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Twitch OAuth failed ({r.status_code}): {r.text}")
    data = r.json()
    _TWITCH_TOKEN_CACHE["token"] = data["access_token"]
    _TWITCH_TOKEN_CACHE["expires_at"] = now + int(data.get("expires_in", 3600))
    return _TWITCH_TOKEN_CACHE["token"]


def fetch_viral_twitch_clips(game: str = "all", hours: int = 24, limit: int = 12, lang: str = "en") -> List[Dict]:
    """Fetches top Twitch clips for GTA VI / GTA V ranked by view velocity (views / age_hours)."""
    cid = os.environ.get("TWITCH_CLIENT_ID", "").strip()
    token = get_twitch_app_token()
    headers = {"Client-ID": cid, "Authorization": f"Bearer {token}"}

    names = GAME_MAP.get(game, GAME_MAP["all"])
    g_resp = requests.get("https://api.twitch.tv/helix/games", params={"name": names}, headers=headers, timeout=10)
    if g_resp.status_code != 200:
        raise RuntimeError(f"Twitch games lookup failed ({g_resp.status_code})")
    games = g_resp.json().get("data", [])

    now_utc = datetime.now(timezone.utc)
    started_at = (now_utc - timedelta(hours=max(1, hours))).strftime("%Y-%m-%dT%H:%M:%SZ")

    raw_clips = []
    for g in games:
        c_resp = requests.get(
            "https://api.twitch.tv/helix/clips",
            params={"game_id": g["id"], "started_at": started_at, "first": 40},
            headers=headers,
            timeout=10,
        )
        if c_resp.status_code == 200:
            for item in c_resp.json().get("data", []):
                item["_game_name"] = g["name"]
                raw_clips.append(item)

    results = []
    seen_ids = set()
    for c in raw_clips:
        cid_item = c.get("id")
        if not cid_item or cid_item in seen_ids:
            continue
        seen_ids.add(cid_item)

        if lang and lang != "all" and (c.get("language") or "").lower() != lang.lower():
            continue

        dur = float(c.get("duration") or 0)
        if dur < 10 or dur > 58:
            continue

        created_str = c.get("created_at", "")
        try:
            created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            age_hours = max(0.5, (now_utc - created_dt).total_seconds() / 3600.0)
        except Exception:
            age_hours = float(hours)

        views = int(c.get("view_count") or 0)
        velocity = round(views / age_hours, 1)

        results.append({
            "id": cid_item,
            "title": c.get("title", "Untitled Clip"),
            "broadcaster_name": c.get("broadcaster_name", "Streamer"),
            "broadcaster_url": f"https://www.twitch.tv/{c.get('broadcaster_name', '').lower()}",
            "game_name": c.get("_game_name", "GTA"),
            "view_count": views,
            "duration": round(dur, 1),
            "created_at": created_str,
            "velocity": velocity,
            "url": c.get("url"),
            "thumbnail_url": c.get("thumbnail_url"),
        })

    results.sort(key=lambda x: x["velocity"], reverse=True)
    return results[:limit]


def download_twitch_clip(clip_url: str, dest_mp4: str) -> str:
    """Downloads a Twitch clip MP4 using yt-dlp."""
    ytdlp_bin = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
    if not os.path.exists(ytdlp_bin):
        ytdlp_bin = shutil.which("yt-dlp") or "yt-dlp"

    cmd = [ytdlp_bin, "-f", "best[ext=mp4]/best", "--no-playlist", "-o", dest_mp4, clip_url]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(dest_mp4) or os.path.getsize(dest_mp4) < 50000:
        raise RuntimeError(f"Failed to download Twitch clip: {res.stderr[-400:]}")
    return dest_mp4


def transcribe_with_groq_whisper(video_path: str, groq_key: str) -> List[Dict]:
    """Extracts audio and transcribes word-level timestamps via Groq Whisper."""
    if not groq_key:
        raise RuntimeError("Groq API key required for Whisper transcription.")

    temp_mp3 = video_path + ".whisper.mp3"
    ext_cmd = [FFMPEG, "-y", "-i", video_path, "-vn", "-ar", "16000", "-ac", "1", "-b:a", "48k", temp_mp3]
    _run_ffmpeg(ext_cmd)

    try:
        with open(temp_mp3, "rb") as af:
            resp = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {groq_key}"},
                files={"file": ("clip.mp3", af, "audio/mpeg")},
                data={
                    "model": "whisper-large-v3-turbo",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "word",
                },
                timeout=45,
            )
        if resp.status_code != 200:
            raise RuntimeError(f"Groq Whisper failed ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        words = []
        for w in data.get("words", []):
            txt = (w.get("word") or "").strip()
            if txt:
                words.append({"word": txt, "start": float(w["start"]), "end": float(w["end"])})
        return words
    finally:
        if os.path.exists(temp_mp3):
            try:
                os.remove(temp_mp3)
            except Exception:
                pass


def detect_facecam_box(video_path: str, duration: float) -> Optional[Tuple[int, int, int, int]]:
    """Detects a streamer facecam corner/edge box and returns (w, h, x, y) in 1.406:1 (40% top) ratio."""
    cap = None
    try:
        import cv2
        if not hasattr(cv2, "CascadeClassifier"):
            return None

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None

        cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
        vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if vid_w < 320 or vid_h < 240:
            return None

        detections = []
        for frac in (0.15, 0.45, 0.75):
            cap.set(cv2.CAP_PROP_POS_MSEC, max(500.0, duration * frac * 1000.0))
            ok, frame = cap.read()
            if not ok:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(45, 45))
            for (fx, fy, fw, fh) in faces:
                # Ignore huge center IRL faces (>38% of frame height); target corner/edge facecams
                if fh < vid_h * 0.38:
                    detections.append((fx, fy, fw, fh))

        if not detections:
            return None

        # Use median face position
        detections.sort(key=lambda b: b[0] + b[1])
        fx, fy, fw, fh = detections[len(detections) // 2]
        cx = fx + fw // 2
        cy = fy + fh // 2

        # Target 1080:768 aspect ratio (1.40625) around detected face
        crop_h = max(int(fh * 2.8), int(vid_h * 0.28))
        crop_h = min(crop_h, int(vid_h * 0.48))
        crop_w = int(crop_h * (1080.0 / 768.0))
        if crop_w > vid_w:
            crop_w = vid_w
            crop_h = int(crop_w * (768.0 / 1080.0))

        x0 = max(0, min(vid_w - crop_w, cx - crop_w // 2))
        y0 = max(0, min(vid_h - crop_h, cy - crop_h // 2))
        return (crop_w, crop_h, x0, y0)
    except Exception as e:
        print(f"Facecam detection fallback: {e}")
        return None
    finally:
        if cap is not None:
            try:
                cap.release()
            except Exception:
                pass


def render_twitch_vertical_short(
    raw_mp4: str,
    ass_path: str,
    output_mp4: str,
    duration: float,
    facecam_box: Optional[Tuple[int, int, int, int]] = None,
):
    """Renders 1080x1920 40/60 facecam+gameplay (or blurred letterbox) Short at -14 LUFS."""
    clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    clean_fonts = FONTS_DIR.replace("\\", "/").replace(":", "\\:")
    fonts_arg = f":fontsdir='{clean_fonts}'" if os.path.exists(FONTS_DIR) else ""

    if facecam_box:
        cw, ch, cx, cy = facecam_box
        v_filter = (
            f"[0:v]split=2[cam_src][gp_src];"
            f"[cam_src]crop={cw}:{ch}:{cx}:{cy},scale=1080:768:force_original_aspect_ratio=increase,crop=1080:768,setsar=1[vtop];"
            f"[gp_src]scale=1080:1152:force_original_aspect_ratio=increase,crop=1080:1152,setsar=1[vbot];"
            f"[vtop][vbot]vstack=inputs=2,drawbox=y=766:color=black@0.9:width=1080:height=4:t=fill,"
            f"fps=30,ass='{clean_ass}'{fonts_arg}[vfinal]"
        )
    else:
        v_filter = (
            f"[0:v]split=2[bg_src][fg_src];"
            f"[bg_src]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=24:4,setsar=1[vbg];"
            f"[fg_src]scale=1080:-2,setsar=1[vfg];"
            f"[vbg][vfg]overlay=(W-w)/2:(H-h)/2,fps=30,ass='{clean_ass}'{fonts_arg}[vfinal]"
        )

    a_filter = "[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[afinal]"
    full_filter = f"{v_filter};{a_filter}"

    cmd = [
        FFMPEG, "-y",
        "-i", raw_mp4,
        "-filter_complex", full_filter,
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-threads", "2",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{duration:.2f}",
        output_mp4,
    ]
    res = _run_ffmpeg(cmd)
    if res.returncode != 0 or not os.path.exists(output_mp4) or os.path.getsize(output_mp4) < 500_000:
        raise RuntimeError(f"Twitch 40/60 render failed: {res.stderr[-600:]}")
    print(f"Twitch vertical short rendered: {output_mp4}")
