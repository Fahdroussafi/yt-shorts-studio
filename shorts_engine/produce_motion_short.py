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
from typing import Optional, List, Dict, Set

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "shorts_engine"))

from engine import format_ass_time, generate_voice, get_audio_duration, build_ass_subtitles, strip_watermarks
from idea_bank import NICHE_PROFILES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# In-memory candidate cache: {query_clean: (timestamp, [urls])}
_QUERY_CACHE: Dict[str, tuple] = {}
CACHE_TTL = 6 * 3600  # 6 hours

def extract_clip_id(url: str) -> str:
    """Extracts a unique, stable clip identifier from a stock video URL."""
    m = re.search(r'/videos/(\d+)/', url)
    if m:
        return f"mix_{m.group(1)}"
    m2 = re.search(r'mixkit-([^.]+?)(?:-\d+)?\.', url)
    if m2:
        return f"mix_{m2.group(1)[:25]}"
    m3 = re.search(r'coverr-([a-zA-Z0-9_-]+)', url)
    if m3:
        return f"cov_{m3.group(1)[:25]}"
    m4 = re.search(r'pexels-video-(\d+)', url)
    if m4:
        return f"pex_{m4.group(1)}"
    import hashlib
    return "clip_" + hashlib.md5(url.encode()).hexdigest()[:12]

def get_video_duration(file_path: str) -> float:
    """Gets video duration in seconds via FFmpeg stderr inspection."""
    try:
        cmd = [FFMPEG, "-i", file_path]
        res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
        m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', res.stderr)
        if m:
            h, m_m, s = m.groups()
            return int(h) * 3600 + int(m_m) * 60 + float(s)
    except Exception:
        pass
    return 12.0

def load_clip_history(clip_history_file: Optional[str]) -> Dict[str, dict]:
    if not clip_history_file or not os.path.exists(clip_history_file):
        return {}
    try:
        with open(clip_history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def record_clip_usage(clip_history_file: Optional[str], clip_urls: List[str]):
    if not clip_history_file:
        return
    try:
        history = load_clip_history(clip_history_file)
        now = time.time()
        for u in clip_urls:
            cid = extract_clip_id(u)
            entry = history.get(cid, {"count": 0, "last_used_ts": 0})
            entry["count"] = entry.get("count", 0) + 1
            entry["last_used_ts"] = now
            history[cid] = entry

        os.makedirs(os.path.dirname(clip_history_file), exist_ok=True)
        with open(clip_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save clip history: {e}")

def harvest_candidates_for_query(query: str) -> List[str]:
    """Scrapes Mixkit (pages 1-2), Coverr, and Pexels (if API key present) for MP4 links."""
    q_clean = query.strip().lower().replace(" ", "-")
    if not q_clean:
        return []

    now = time.time()
    if q_clean in _QUERY_CACHE:
        ts, cached_urls = _QUERY_CACHE[q_clean]
        if now - ts < CACHE_TTL and cached_urls:
            return list(cached_urls)

    results: List[str] = []

    # 1. Pexels API (Optional BYOK)
    pexels_key = os.environ.get("PEXELS_API_KEY")
    if pexels_key:
        try:
            pex_url = f"https://api.pexels.com/videos/search?query={q_clean}&orientation=portrait&per_page=12"
            pr = requests.get(pex_url, headers={"Authorization": pexels_key}, timeout=8)
            if pr.status_code == 200:
                pdata = pr.json()
                for v in pdata.get("videos", []):
                    files = v.get("video_files", [])
                    # Pick 720p or HD portrait file
                    best = next((f["link"] for f in files if f.get("height", 0) >= 720 and f.get("link")), None)
                    if best:
                        results.append(best)
        except Exception as e:
            print(f"Pexels fetch note: {e}")

    # 2. Mixkit Pages 1 & 2
    for page in [1, 2]:
        try:
            page_url = f"https://mixkit.co/free-stock-video/{q_clean}/" if page == 1 else f"https://mixkit.co/free-stock-video/{q_clean}/?page={page}"
            r = requests.get(page_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                found = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-(?:1080|720|360)\.mp4', r.text)
                for f in found:
                    hd = re.sub(r'-\d+\.mp4$', '-720.mp4', f) if 'mixkit.co' in f else f
                    if hd not in results:
                        results.append(hd)
        except Exception:
            pass

    _QUERY_CACHE[q_clean] = (now, results)
    return results

def pick_best_clip_candidate(
    candidates: List[str],
    used_in_video: Set[str],
    clip_history: Dict[str, dict]
) -> Optional[str]:
    """Selects the freshest, least-frequently-used clip from candidates avoiding repeats."""
    if not candidates:
        return None

    # Filter out clips already chosen in this video
    available = [c for c in candidates if extract_clip_id(c) not in used_in_video]
    if not available:
        # If all candidates already in this video, fallback to any candidate
        available = candidates

    scored = []
    now = time.time()
    for c in available:
        cid = extract_clip_id(c)
        hist = clip_history.get(cid, {"count": 0, "last_used_ts": 0})
        count = hist.get("count", 0)
        last_used = hist.get("last_used_ts", 0)

        # Penalty score: lower is better
        hours_since = (now - last_used) / 3600.0 if last_used > 0 else 999.0
        recency_penalty = 50.0 / (hours_since + 1.0)  # steep penalty if used in last few hours
        count_penalty = count * 15.0
        jitter = random.uniform(0.0, 3.0)  # non-deterministic tie-breaker

        penalty = count_penalty + recency_penalty + jitter
        scored.append((penalty, c))

    scored.sort(key=lambda x: x[0])
    chosen = scored[0][1]
    used_in_video.add(extract_clip_id(chosen))
    return chosen

def download_clip_with_smart_fallback(
    query: str,
    dest_path: str,
    niche: str,
    used_in_video: Set[str],
    clip_history: Dict[str, dict]
) -> tuple:
    """Harvests candidates, selects the best non-repeating clip, and downloads it."""
    profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
    niche_bank = profile.get("visual_bank", ["thinking", "shadows", "mirror", "dark-street", "candle"])

    candidates = harvest_candidates_for_query(query)

    # If primary query returned nothing, harvest from niche-specific visual bank
    if not candidates:
        fallback_queries = random.sample(niche_bank, min(3, len(niche_bank)))
        for fq in fallback_queries:
            candidates = harvest_candidates_for_query(fq)
            if candidates:
                break

    # If still nothing, try the first 3 terms from niche bank
    if not candidates:
        for fq in niche_bank[:3]:
            candidates = harvest_candidates_for_query(fq)
            if candidates:
                break

    if not candidates:
        raise RuntimeError(f"Could not find stock video clip for '{query}' in niche '{niche}'")

    # Try downloading best candidate; if it fails or produces corrupt/empty file, try next
    while candidates:
        selected_url = pick_best_clip_candidate(candidates, used_in_video, clip_history)
        if not selected_url:
            break

        print(f"  Downloading fresh clip for '{query}' -> {selected_url}")
        try:
            r = requests.get(selected_url, headers=HEADERS, stream=True, timeout=25)
            if r.status_code == 200:
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            f.write(chunk)

                if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
                    mb = round(os.path.getsize(dest_path) / (1024 * 1024), 2)
                    print(f"  Saved clip: {dest_path} ({mb} MB)")
                    return dest_path, selected_url
        except Exception as e:
            print(f"  Clip download error ({selected_url}): {e}")

        # Discard failed candidate and try next
        if selected_url in candidates:
            candidates.remove(selected_url)

    raise RuntimeError(f"Failed to download a valid clip for '{query}' across available candidates.")

def render_motion_video(clip_paths: list, audio_path: str, ass_path: str, output_mp4: str, duration: float):
    print(f"[4/5] Dynamic multi-cut rendering {len(clip_paths)} clips ({duration:.2f}s total, ~{duration/len(clip_paths):.1f}s per cut)...")

    per_clip = duration / len(clip_paths)
    inputs = []
    filter_parts = []

    for i, clip in enumerate(clip_paths):
        inputs.extend(["-stream_loop", "-1", "-i", clip])

        # Calculate random start offset so different segments of the clip are shown
        clip_dur = get_video_duration(clip)
        max_offset = max(0.0, clip_dur - per_clip - 0.5)
        offset = round(random.uniform(0.0, min(max_offset, 6.0)), 2) if max_offset > 1.0 else 0.0

        # 30% chance of subtle horizontal mirror flip for visual novelty
        flip_filter = ",hflip" if random.random() < 0.30 else ""

        filter_parts.append(
            f"[{i}:v]trim=start={offset}:duration={per_clip:.3f},setpts=PTS-STARTPTS,fps=30,"
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1{flip_filter}[v{i}]"
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

async def produce_motion_short(
    video_id: str,
    script_text: str,
    clip_keywords: list,
    seo_meta: dict,
    niche: str = "dark_psychology",
    clip_history_file: Optional[str] = None,
    target_dir: Optional[str] = None
):
    if not target_dir:
        target_dir = os.path.join(BASE_DIR, "videos", video_id)
    os.makedirs(target_dir, exist_ok=True)

    audio_file = os.path.join(target_dir, "voice.mp3")
    ass_file = os.path.join(target_dir, "captions.ass")
    output_mp4 = os.path.join(target_dir, f"{video_id}.mp4")
    meta_file = os.path.join(target_dir, "seo_metadata.txt")

    print(f"\n=== PRODUCING REAL-MOTION SHORT: {video_id.upper()} (Niche: {niche}) ===")
    words = await generate_voice(script_text, audio_file)
    dur = get_audio_duration(audio_file)
    print(f"Audio Duration: {dur:.2f}s")

    build_ass_subtitles(words, ass_file)

    # Target 8 to 10 cuts for high retention (~4 to 4.5s per scene)
    target_cuts = max(6, min(10, round(dur / 4.2)))

    profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
    niche_bank = profile.get("visual_bank", ["thinking", "shadows", "mirror", "dark-street"])

    # Expand keywords if fewer provided than target cuts
    expanded_keywords = list(clip_keywords) if clip_keywords else []
    while len(expanded_keywords) < target_cuts:
        fresh = random.choice([k for k in niche_bank if k not in expanded_keywords] or niche_bank)
        expanded_keywords.append(fresh)

    expanded_keywords = expanded_keywords[:target_cuts]

    clip_history = load_clip_history(clip_history_file)
    used_in_video: Set[str] = set()
    chosen_urls: List[str] = []
    clip_paths: List[str] = []

    print(f"[3/5] Scraping & downloading {len(expanded_keywords)} unique stock clips (No-Repeat Algorithm)...")
    for idx, kw in enumerate(expanded_keywords):
        clip_path = os.path.join(target_dir, f"clip_{idx}.mp4")
        _, chosen_url = download_clip_with_smart_fallback(
            query=kw,
            dest_path=clip_path,
            niche=niche,
            used_in_video=used_in_video,
            clip_history=clip_history
        )
        chosen_urls.append(chosen_url)
        clip_paths.append(clip_path)

    # Record clips in user history
    record_clip_usage(clip_history_file, chosen_urls)

    render_motion_video(clip_paths, audio_file, ass_file, output_mp4, dur)
    strip_watermarks(output_mp4)

    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE:\n{seo_meta['title']}\n\n")
        f.write(f"DESCRIPTION:\n{seo_meta['description']}\n\n")
        f.write(f"PINNED COMMENT:\n{seo_meta['pinned_comment']}\n")

    mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"\n[SUCCESS] REAL-MOTION SHORT READY: {output_mp4} ({mb:.2f} MB)\n")
    return output_mp4
