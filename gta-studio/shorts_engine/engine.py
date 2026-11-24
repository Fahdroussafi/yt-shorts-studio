import os
import sys
import re
import json
import time
import asyncio
import requests
import subprocess
import imageio_ffmpeg
from datetime import timedelta
from typing import Optional

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def format_ass_time(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    centis = int(td.microseconds / 10000)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


async def generate_voice(text: str, voice_file: str, voice: str = "en-US-ChristopherNeural", rate: str = "+0%", brand_name: Optional[str] = None):
    import edge_tts
    print("[1/5] Synthesizing voiceover with edge-tts...")
    
    # Optional channel brand outro guarantee
    text = text.strip()
    if brand_name and brand_name.lower() not in text.lower():
        text = text.rstrip(" .,!?:;-") + f". Follow {brand_name} for more."

    # Validate voice against known working voices to prevent "No audio was received" errors
    working_voices = [
        "en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural",
        "en-US-BrianNeural", "en-US-SteffanNeural",
        "en-US-ChristopherNeural", "en-US-GuyNeural", "en-US-EricNeural",
        "en-GB-RyanNeural", "en-US-AvaNeural", "en-US-JennyNeural"
    ]
    selected_voice = voice if voice in working_voices else "en-US-ChristopherNeural"

    words = []
    try:
        comm = edge_tts.Communicate(text, selected_voice, rate=rate, boundary="WordBoundary")
        with open(voice_file, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start_sec = chunk["offset"] / 10_000_000
                    dur_sec = chunk["duration"] / 10_000_000
                    words.append({
                        "word": chunk["text"],
                        "start": start_sec,
                        "end": start_sec + dur_sec
                    })
    except Exception as e:
        print(f"Edge-TTS failed with {selected_voice} ({e}), falling back to en-US-ChristopherNeural...")
        words = []
        comm = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate=rate, boundary="WordBoundary")
        with open(voice_file, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start_sec = chunk["offset"] / 10_000_000
                    dur_sec = chunk["duration"] / 10_000_000
                    words.append({
                        "word": chunk["text"],
                        "start": start_sec,
                        "end": start_sec + dur_sec
                    })

    # Guard against 0-byte audio
    if not os.path.exists(voice_file) or os.path.getsize(voice_file) < 500:
        raise RuntimeError(f"Voice synthesis failed to produce audio file for voice '{selected_voice}'.")

    print(f"Generated {len(words)} word timestamps.")
    return words


def get_audio_duration(file_path: str) -> float:
    cmd = [FFMPEG, "-i", file_path, "-f", "null", "-"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 40.0


FONTS_DIR = os.path.join(BASE_DIR, "shorts_engine", "fonts")

# 5 High-Impact Caption Visual DNA Styles (Built on Anton Heavy Display Font)
CAPTION_STYLES = {
    "hormozi_gold": {
        "name": "Hormozi Gold",
        "font": "Anton",
        "fontsize": 94,
        "primary": "&H00FFFFFF",      # Base White
        "active": "&H0000D7FF",       # Electric Gold/Yellow
        "outline": "&H00000000",      # Pure Black
        "back": "&H90000000",
        "border_style": 1,
        "outline_w": 9,
        "shadow_w": 5,
        "chunk_size": 3,
        "anim": r"{\fscx112\fscy112\t(0,70,\fscx100\fscy100)}"
    },
    "crimson_alert": {
        "name": "Crimson Alert",
        "font": "Anton",
        "fontsize": 98,
        "primary": "&H00FFFFFF",
        "active": "&H002A2AFF",       # Vivid Crimson Red
        "outline": "&H00000000",
        "back": "&HB0000000",
        "border_style": 1,
        "outline_w": 10,
        "shadow_w": 6,
        "chunk_size": 2,
        "anim": r"{\fscx118\fscy118\t(0,60,\fscx100\fscy100)}"
    },
    "cyber_cyan": {
        "name": "Cyber Cyan",
        "font": "Anton",
        "fontsize": 92,
        "primary": "&H00F0F0F0",
        "active": "&H00FFFF00",       # Neon Cyan / Aqua
        "outline": "&H001A0B2E",      # Deep Midnight
        "back": "&H80000000",
        "border_style": 1,
        "outline_w": 8,
        "shadow_w": 4,
        "chunk_size": 3,
        "anim": r"{\fscx110\fscy110\t(0,80,\fscx100\fscy100)}"
    },
    "emerald_matrix": {
        "name": "Emerald Matrix",
        "font": "Anton",
        "fontsize": 94,
        "primary": "&H00FFFFFF",
        "active": "&H0081B910",       # Neon Emerald Green
        "outline": "&H00000000",
        "back": "&H90000000",
        "border_style": 1,
        "outline_w": 9,
        "shadow_w": 5,
        "chunk_size": 3,
        "anim": r"{\fscx114\fscy114\t(0,65,\fscx100\fscy100)}"
    },
}

def build_ass_subtitles(words, output_ass: str, style_name: Optional[str] = None, margin_v: int = 860, fontsize: Optional[int] = None, top_badge: Optional[str] = None, hook_banner: Optional[str] = None, fallback_duration: Optional[float] = None):
    """Builds dynamic animated subtitles with zero-gap persistent presence."""
    import random
    if not style_name or style_name not in CAPTION_STYLES:
        style_key = random.choice(list(CAPTION_STYLES.keys()))
    else:
        style_key = style_name

    cfg = CAPTION_STYLES[style_key]
    fsize = fontsize or cfg['fontsize']
    print(f"[2/5] Creating viral subtitles [Preset: {cfg['name']}]...")

    phrases = []
    chunk_size = cfg.get("chunk_size", 3)
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        if not chunk:
            continue
        phrases.append({
            "words": chunk,
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"] + 0.1
        })

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{cfg['font']},{fsize},{cfg['primary']},&H0000FFFF,{cfg['outline']},{cfg['back']},-1,0,0,0,100,100,2,0,{cfg['border_style']},{cfg['outline_w']},{cfg['shadow_w']},2,60,60,{margin_v},1
Style: Badge,Montserrat,34,&H00E2E8F0,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,2,40,40,140,1
Style: HookBanner,{cfg['font']},60,&H0000D7FF,&H0000FFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,8,4,8,50,50,515,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    overlay_end = (phrases[-1]["end"] + 1.0) if phrases else fallback_duration
    if top_badge and overlay_end:
        total_end = format_ass_time(overlay_end)
        events.append(f"Dialogue: 1,0:00:00.00,{total_end},Badge,,0,0,0,,{top_badge}")
    if hook_banner and overlay_end:
        total_end = format_ass_time(overlay_end)
        clean_banner = hook_banner.replace("{", "").replace("}", "").strip().upper()
        events.append(f"Dialogue: 2,0:00:00.00,{total_end},HookBanner,,0,0,0,,{{\\fad(150,200)}}{clean_banner}")
    pop_anim = cfg.get("anim", "")
    active_color = cfg["active"]
    primary_color = cfg["primary"]

    for p_idx, p in enumerate(phrases):
        next_phrase_start = phrases[p_idx + 1]["words"][0]["start"] if p_idx + 1 < len(phrases) else p["end"] + 0.5
        for active_idx, w in enumerate(p["words"]):
            w_start = format_ass_time(w["start"])
            if active_idx + 1 < len(p["words"]):
                # Seamless zero-gap transition to next word in the chunk
                w_end = format_ass_time(p["words"][active_idx + 1]["start"])
            else:
                # Last word in chunk: hold until next phrase begins (no dark flashes)
                hold_until = min(w["end"] + 0.45, next_phrase_start)
                w_end = format_ass_time(hold_until)

            formatted_words = []
            for idx, item in enumerate(p["words"]):
                text = item["word"].upper()
                if idx == active_idx:
                    formatted_words.append(f"{{\\c{active_color}&}}{pop_anim}{text}{{\\c{primary_color}&}}")
                else:
                    formatted_words.append(text)

            line_text = " ".join(formatted_words)
            events.append(f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{line_text}")

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events))
    print(f"Subtitles written: {len(events)} cues ({cfg['name']}).")
    return style_key


def strip_watermarks(file_path: str):
    cleaner = os.path.join(BASE_DIR, "tools", "watermarks-remover", "service", "scripts", "clean_file.py")
    if os.path.exists(cleaner):
        print(f"[5/5] Stripping AI marks with watermarks-remover...")
        bak_file = file_path + ".bak"
        if os.path.exists(bak_file):
            try:
                os.remove(bak_file)
            except Exception:
                pass
        res = subprocess.run([sys.executable, cleaner, "--in-place", file_path], capture_output=True, text=True)
        if res.stdout.strip():
            print(f"  {res.stdout.strip()}")
        if os.path.exists(bak_file):
            try:
                os.remove(bak_file)
            except Exception:
                pass
