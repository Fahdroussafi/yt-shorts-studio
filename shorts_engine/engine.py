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


async def generate_voice(text: str, voice_file: str, voice: str = "en-US-ChristopherNeural", rate: str = "+6%", brand_name: Optional[str] = None):
    import edge_tts
    print("[1/5] Synthesizing voiceover with edge-tts...")
    
    # Optional channel brand outro guarantee
    text = text.strip()
    if brand_name and brand_name.lower() not in text.lower():
        text = text.rstrip(" .,!?:;-") + f". Follow {brand_name} for more."

    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    
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


# 5 High-Impact Caption Visual DNA Styles
CAPTION_STYLES = {
    "hormozi_gold": {
        "name": "Hormozi Gold",
        "font": "Arial Black",
        "fontsize": 86,
        "primary": "&H00FFFFFF",      # Base White
        "active": "&H0000D7FF",       # Electric Gold/Yellow
        "outline": "&H00000000",      # Pure Black
        "back": "&H90000000",
        "border_style": 1,
        "outline_w": 8,
        "shadow_w": 4,
        "chunk_size": 3,
        "anim": r"{\fscx110\fscy110\t(0,70,\fscx100\fscy100)}"
    },
    "crimson_alert": {
        "name": "Crimson Alert",
        "font": "Impact",
        "fontsize": 92,
        "primary": "&H00FFFFFF",
        "active": "&H002A2AFF",       # Vivid Crimson Red
        "outline": "&H00000000",
        "back": "&HB0000000",
        "border_style": 1,
        "outline_w": 9,
        "shadow_w": 5,
        "chunk_size": 2,
        "anim": r"{\fscx115\fscy115\t(0,60,\fscx100\fscy100)}"
    },
    "cyber_cyan": {
        "name": "Cyber Cyan",
        "font": "Trebuchet MS",
        "fontsize": 84,
        "primary": "&H00F0F0F0",
        "active": "&H00FFFF00",       # Neon Cyan / Aqua
        "outline": "&H001A0B2E",      # Deep Midnight
        "back": "&H80000000",
        "border_style": 1,
        "outline_w": 7,
        "shadow_w": 3,
        "chunk_size": 3,
        "anim": r"{\fscx108\fscy108\t(0,80,\fscx100\fscy100)}"
    },
    "emerald_matrix": {
        "name": "Emerald Matrix",
        "font": "Arial Black",
        "fontsize": 86,
        "primary": "&H00FFFFFF",
        "active": "&H0081B910",       # Neon Emerald Green
        "outline": "&H00000000",
        "back": "&H90000000",
        "border_style": 1,
        "outline_w": 8,
        "shadow_w": 4,
        "chunk_size": 3,
        "anim": r"{\fscx112\fscy112\t(0,65,\fscx100\fscy100)}"
    },
    "minimal_pill": {
        "name": "Minimalist Pill",
        "font": "Arial",
        "fontsize": 80,
        "primary": "&H00FFFFFF",
        "active": "&H0000E5FF",       # Amber Glow
        "outline": "&H00000000",
        "back": "&HA0151515",
        "border_style": 3,            # Opaque Pill Box
        "outline_w": 6,
        "shadow_w": 0,
        "chunk_size": 2,
        "anim": ""
    }
}

def build_ass_subtitles(words, output_ass: str, style_name: Optional[str] = None):
    """Builds dynamic animated subtitles using one of 5 visual DNA presets."""
    import random
    if not style_name or style_name not in CAPTION_STYLES:
        style_key = random.choice(list(CAPTION_STYLES.keys()))
    else:
        style_key = style_name

    cfg = CAPTION_STYLES[style_key]
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
Style: Default,{cfg['font']},{cfg['fontsize']},{cfg['primary']},&H0000FFFF,{cfg['outline']},{cfg['back']},-1,0,0,0,100,100,2,0,{cfg['border_style']},{cfg['outline_w']},{cfg['shadow_w']},2,60,60,860,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    pop_anim = cfg.get("anim", "")
    active_color = cfg["active"]
    primary_color = cfg["primary"]

    for p in phrases:
        for active_idx, w in enumerate(p["words"]):
            w_start = format_ass_time(w["start"])
            w_end = format_ass_time(w["end"])

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


def download_images(prompts, out_dir: str):
    print(f"[3/5] Downloading {len(prompts)} Flux vertical visuals...")
    img_paths = []
    for idx, p in enumerate(prompts):
        img_file = os.path.join(out_dir, f"scene_{idx}.jpg")
        if os.path.exists(img_file) and os.path.getsize(img_file) > 5000:
            print(f"  Scene {idx + 1} cached.")
            img_paths.append(img_file)
            continue
        
        encoded = requests.utils.quote(p)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&nologo=true&seed={idx * 29 + 13}"
        
        done = False
        while not done:
            print(f"  Requesting scene {idx + 1}/{len(prompts)}...")
            try:
                r = requests.get(url, timeout=40)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(img_file, "wb") as f:
                        f.write(r.content)
                    print(f"  Scene {idx + 1} downloaded ({len(r.content)} bytes).")
                    done = True
                    break
                elif r.status_code in (402, 429):
                    match = re.search(r"Retry after (\d+)s", r.text)
                    wait_sec = int(match.group(1)) + 2 if match else 45
                    print(f"  Cooldown: waiting {wait_sec}s...")
                    time.sleep(wait_sec)
                else:
                    print(f"  HTTP {r.status_code}, waiting 10s...")
                    time.sleep(10)
            except Exception as e:
                print(f"  Network error: {e}, retrying in 5s...")
                time.sleep(5)
                
        img_paths.append(img_file)
    return img_paths


def render_video(img_paths, audio_path, ass_path, output_mp4, duration: float):
    print(f"[4/5] Rendering 30fps vertical MP4 ({duration:.2f}s)...")
    out_dir = os.path.dirname(output_mp4)
    concat_file = os.path.join(out_dir, "concat.txt")
    
    per_image = duration / len(img_paths)
    lines = []
    for img in img_paths:
        clean_img = img.replace('\\', '/')
        lines.append(f"file '{clean_img}'")
        lines.append(f"duration {per_image:.3f}")
    last_img = img_paths[-1].replace('\\', '/')
    lines.append(f"file '{last_img}'")
    
    with open(concat_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    
    clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    # crop=in_w:in_h-50:0:0 strips the bottom-right corner AI logo cleanly before upscaling
    filter_complex = (
        f"[0:v]fps=30,crop=in_w:in_h-50:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"ass='{clean_ass}'[vfinal];"
        f"[1:a][2:a]amix=inputs=2:duration=first:weights=1.0 0.15[afinal]"
    )
    
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", audio_path,
        "-f", "lavfi", "-t", f"{duration:.2f}",
        "-i", "anoisesrc=d=60:c=pink:r=44100:a=0.03,lowpass=f=120",
        "-filter_complex", filter_complex,
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "20",
        "-threads", "2",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{duration:.2f}",
        output_mp4
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-800:])
        raise RuntimeError("FFmpeg render failed")
    print(f"Render complete: {output_mp4}")


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


async def produce_short(video_id: str, script_text: str, visual_prompts: list, seo_meta: dict):
    target_dir = os.path.join(BASE_DIR, "videos", video_id)
    os.makedirs(target_dir, exist_ok=True)
    
    audio_file = os.path.join(target_dir, "voice.mp3")
    ass_file = os.path.join(target_dir, "captions.ass")
    output_mp4 = os.path.join(target_dir, f"{video_id}.mp4")
    meta_file = os.path.join(target_dir, "seo_metadata.txt")
    
    print(f"\n=== PRODUCING {video_id.upper()} ===")
    words = await generate_voice(script_text, audio_file)
    dur = get_audio_duration(audio_file)
    print(f"Duration: {dur:.2f}s")
    
    build_ass_subtitles(words, ass_file)
    img_paths = download_images(visual_prompts, target_dir)
    render_video(img_paths, audio_file, ass_file, output_mp4, dur)
    strip_watermarks(output_mp4)
    
    # Save SEO Metadata
    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE:\n{seo_meta['title']}\n\n")
        f.write(f"DESCRIPTION:\n{seo_meta['description']}\n\n")
        f.write(f"PINNED COMMENT:\n{seo_meta['pinned_comment']}\n")
        
    mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"=== {video_id.upper()} READY: {output_mp4} ({mb:.2f} MB) ===\n")
    return output_mp4
