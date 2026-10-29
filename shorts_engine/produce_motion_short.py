import os
import sys
import re
import json
import time
import random
import asyncio
import requests
import subprocess
import imageio_ffmpeg
from datetime import timedelta

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "shorts_engine"))

from engine import format_ass_time, generate_voice, get_audio_duration, build_ass_subtitles, strip_watermarks

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def download_clip_by_keyword(keyword: str, dest_path: str):
    """Download a real motion stock video clip via Mixkit/Coverr without keys."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 500000:
        print(f"  Clip for '{keyword}' cached ({round(os.path.getsize(dest_path)/(1024*1024),2)} MB).")
        return dest_path

    k_clean = keyword.strip().lower().replace(" ", "-")
    urls_to_search = [
        f"https://mixkit.co/free-stock-video/{k_clean}/",
        f"https://mixkit.co/free-stock-video/technology/",
        f"https://coverr.co/s?q={keyword.strip().lower().replace(' ', '+')}"
    ]
    
    mp4_links = []
    for u in urls_to_search:
        try:
            r = requests.get(u, headers=HEADERS, timeout=12)
            if r.status_code == 200:
                found = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-(?:1080|720|360)\.mp4', r.text)
                if not found:
                    found = re.findall(r'https://[^"\']+\.mp4', r.text)
                if found:
                    # Upgrade all stock links to clean 720p HD resolution instead of 360p mobile preview
                    hd_links = [re.sub(r'-\d+\.mp4$', '-720.mp4', link) if 'mixkit.co' in link else link for link in found]
                    mp4_links.extend(hd_links)
                    break
        except Exception:
            pass

    if not mp4_links:
        # Emergency fallback to tech
        try:
            r = requests.get("https://mixkit.co/free-stock-video/technology/", headers=HEADERS, timeout=12)
            found = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-(?:1080|720|360)\.mp4', r.text)
            if found:
                mp4_links = [re.sub(r'-\d+\.mp4$', '-720.mp4', link) for link in found]
        except Exception:
            pass

    if not mp4_links:
        raise RuntimeError(f"Could not find stock video clip for {keyword}")

    selected = random.choice(mp4_links[:6])
    print(f"  Downloading stock clip for '{keyword}': {selected}")
    r = requests.get(selected, headers=HEADERS, stream=True, timeout=30)
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*64):
            if chunk:
                f.write(chunk)
                
    print(f"  Saved clip: {round(os.path.getsize(dest_path)/(1024*1024), 2)} MB")
    return dest_path


def render_motion_video(clip_paths: list, audio_path: str, ass_path: str, output_mp4: str, duration: float):
    print(f"[4/5] Stitched rendering {len(clip_paths)} real motion clips ({duration:.2f}s total)...")
    
    per_clip = duration / len(clip_paths)
    inputs = []
    filter_parts = []
    
    for i, clip in enumerate(clip_paths):
        inputs.extend(["-stream_loop", "-1", "-i", clip])
        # Trim, scale & center-crop to 1080x1920 vertical video
        filter_parts.append(
            f"[{i}:v]trim=duration={per_clip:.3f},setpts=PTS-STARTPTS,fps=30,"
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v{i}]"
        )
        
    concat_ins = "".join(f"[v{i}]" for i in range(len(clip_paths)))
    concat_filter = f"{concat_ins}concat=n={len(clip_paths)}:v=1:a=0[vbase]"
    
    clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    subtitle_filter = f"[vbase]ass='{clean_ass}'[vfinal]"
    
    # Audio mix with subtle cinematic low rumble
    audio_input_idx = len(clip_paths)
    synth_input_idx = len(clip_paths) + 1
    audio_filter = f"[{audio_input_idx}:a][{synth_input_idx}:a]amix=inputs=2:duration=first:weights=1.0 0.12[afinal]"
    
    full_filter = ";".join(filter_parts) + ";" + concat_filter + ";" + subtitle_filter + ";" + audio_filter
    
    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-i", audio_path,
        "-f", "lavfi", "-t", f"{duration:.2f}",
        "-i", "anoisesrc=d=60:c=pink:r=44100:a=0.03,lowpass=f=120",
        "-filter_complex", full_filter,
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "19",
        "-threads", "2",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{duration:.2f}",
        output_mp4
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr[-1000:])
        raise RuntimeError("FFmpeg render failed")
    print(f"Motion video rendered: {output_mp4}")


async def produce_motion_short(video_id: str, script_text: str, clip_keywords: list, seo_meta: dict):
    target_dir = os.path.join(BASE_DIR, "videos", video_id)
    os.makedirs(target_dir, exist_ok=True)
    
    audio_file = os.path.join(target_dir, "voice.mp3")
    ass_file = os.path.join(target_dir, "captions.ass")
    output_mp4 = os.path.join(target_dir, f"{video_id}.mp4")
    meta_file = os.path.join(target_dir, "seo_metadata.txt")
    
    print(f"\n=== PRODUCING REAL-MOTION SHORT: {video_id.upper()} ===")
    words = await generate_voice(script_text, audio_file)
    dur = get_audio_duration(audio_file)
    print(f"Duration: {dur:.2f}s")
    
    build_ass_subtitles(words, ass_file)
    
    print(f"[3/5] Downloading {len(clip_keywords)} real motion stock video clips...")
    clip_paths = []
    for idx, kw in enumerate(clip_keywords):
        clip_path = os.path.join(target_dir, f"clip_{idx}.mp4")
        download_clip_by_keyword(kw, clip_path)
        clip_paths.append(clip_path)
        
    render_motion_video(clip_paths, audio_file, ass_file, output_mp4, dur)
    strip_watermarks(output_mp4)
    
    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE:\n{seo_meta['title']}\n\n")
        f.write(f"DESCRIPTION:\n{seo_meta['description']}\n\n")
        f.write(f"PINNED COMMENT:\n{seo_meta['pinned_comment']}\n")
        
    mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"\n[SUCCESS] REAL-MOTION SHORT READY: {output_mp4} ({mb:.2f} MB)\n")
    return output_mp4


SCRIPT_ROBOT = (
    "Right now, the first factories run entirely by humanoid robots without a single human inside have officially gone live. "
    "In China and the United States, robotics companies are deploying fleets of bipedal machines that work twenty-four hours a day with zero human supervision. "
    "Unlike traditional robotic arms bolted to the floor, these machines walk on two legs, use advanced AI vision to adapt to changes in real-time, and can even recharge their own batteries. "
    "Analysts predict that within five years, operating a humanoid robot will cost less than three dollars an hour, permanently replacing millions of manual warehouse and assembly jobs. "
    "Would you trust a humanoid robot inside your home? Follow ShadowMind for the hidden realities shaping our future."
)

KEYWORDS_ROBOT = [
    "robot",
    "factory",
    "artificial-intelligence",
    "technology",
    "future"
]

SEO_ROBOT = {
    "title": "The Terrifying Rise of Humanoid Robot Factories #shorts #technology",
    "description": (
        "Fully autonomous factories run entirely by humanoid robots without humans have officially gone live. Here is what is happening behind closed doors.\n\n"
        "Subscribe to @ShadowMind for hidden world trends, future tech, and global realities.\n\n"
        "#humanoidrobot #robotics #futuretech #artificialintelligence #ai #technews #shorts #shadowmind"
    ),
    "pinned_comment": "Would you trust a humanoid robot to do chores inside your home? Comment below. 👇"
}

if __name__ == "__main__":
    asyncio.run(produce_motion_short("short_07", SCRIPT_ROBOT, KEYWORDS_ROBOT, SEO_ROBOT))
