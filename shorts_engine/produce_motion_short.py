import os
import sys
import re
import json
import time
import random
import asyncio
import requests
import subprocess
import urllib.parse
import imageio_ffmpeg
from typing import Optional, List, Dict, Set

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "shorts_engine"))

from engine import format_ass_time, generate_voice, get_audio_duration, build_ass_subtitles, strip_watermarks, FONTS_DIR
from idea_bank import NICHE_PROFILES

GAMEPLAY_DIR = os.path.join(BASE_DIR, "shorts_engine", "gameplay")

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

# Color Grading Film LUT Looks (Procedural FFmpeg filter chains)
COLOR_LOOKS = {
    "noir_contrast": {
        "name": "Dark Noir High-Contrast",
        "filter": "eq=contrast=1.18:brightness=-0.02:saturation=0.78,unsharp=3:3:0.6:3:3:0.0"
    },
    "cinematic_teal_orange": {
        "name": "Teal & Orange Cinema",
        "filter": "colorbalance=rs=-0.08:gs=0.02:bs=0.12:rh=0.10:gh=0.03:bh=-0.08,eq=contrast=1.12:saturation=1.15"
    },
    "cold_thriller": {
        "name": "Cold Thriller Shadow",
        "filter": "colorbalance=rs=-0.1:gs=-0.02:bs=0.15,eq=contrast=1.15:saturation=0.85,noise=alls=4:allf=t+u"
    },
    "warm_vintage": {
        "name": "Warm Golden Mystery",
        "filter": "colorbalance=rs=0.10:gs=0.04:bs=-0.08:rh=0.12:gh=0.06:bh=-0.05,eq=contrast=1.08:saturation=1.05,vignette=PI/4.5"
    },
    "crisp_hdr": {
        "name": "Crisp 4K Pop",
        "filter": "eq=contrast=1.10:saturation=1.20,unsharp=5:5:0.8:5:5:0.0"
    }
}

# Verified Physical Stock Video Slugs (Mixkit verified 20-40 HD clips each)
VERIFIED_STOCK_SLUGS = {
    "tunnel", "subway", "security-camera", "crowd", "eye", "police", "prison",
    "hospital", "ocean", "fire", "smoke", "office", "running", "night-street",
    "shadow", "silhouette", "walking-alone", "rain-window", "chess", "laboratory",
    "dark-street", "traffic", "train", "door", "clock", "stairs"
}

# Semantic dictionary mapping script triggers / spoken concepts to verified visual slugs
SCRIPT_VISUAL_TRIGGER_MAP = [
    # CCTV & Surveillance
    (re.compile(r'\b(cctv|camera|surveillance|footage|security|monitor|watch(?:ing)?|record(?:ed)?)\b', re.I), "security-camera"),
    # Underground / Tunnel / Subway
    (re.compile(r'\b(subway|train|metro|platform|commute)\b', re.I), "subway"),
    (re.compile(r'\b(tunnel|claustrophobic|underground|hallway|corridor|passage)\b', re.I), "tunnel"),
    # Crowd & Strangers
    (re.compile(r'\b(crowd|people|stranger|strangers|bystander|bystanders|group|public|hundred people)\b', re.I), "crowd"),
    # Eye contact & Staring / Face
    (re.compile(r'\b(eye|eyes|stare|staring|blink|gaze|look into|eye contact)\b', re.I), "eye"),
    # Police & Interrogation & Traps
    (re.compile(r'\b(police|interrogation|fbi|detective|cop|arrest|handcuff|suspect|interrogate)\b', re.I), "police"),
    (re.compile(r'\b(prison|jail|cell|inmate|behind bars|cage|guilty|verdict)\b', re.I), "prison"),
    # Hospital, Medicine & Brain Experiments
    (re.compile(r'\b(hospital|nurse|doctor|patient|injection|medicine|needle|clinical|ward)\b', re.I), "hospital"),
    (re.compile(r'\b(experiment|scientist|laboratory|lab|study|researchers|brain|neural)\b', re.I), "laboratory"),
    # Danger / Water / Fire
    (re.compile(r'\b(ocean|sea|water|waves|drown|drowning|shore|beach)\b', re.I), "ocean"),
    (re.compile(r'\b(fire|burn|flame|blaze|spark|smoke|alarm|fire alarm)\b', re.I), "fire"),
    # Escape / Running / Chase
    (re.compile(r'\b(run|running|flee|escape|chase|pursuit|sprint|dash)\b', re.I), "running"),
    # Night street / Walking alone / Parking
    (re.compile(r'\b(walking alone|empty street|alley|walk alone|sidewalk)\b', re.I), "walking-alone"),
    (re.compile(r'\b(parking|garage|dark street|night|city at night|midnight)\b', re.I), "dark-street"),
    # Office, Corporate, Boss, Money
    (re.compile(r'\b(boss|coworker|corporate|workplace|office|email|desk|colleague|job)\b', re.I), "office"),
    # Strategy, Chess, Shadows, Whispers
    (re.compile(r'\b(chess|strategy|tactics|game|checkmate|opponent)\b', re.I), "chess"),
    (re.compile(r'\b(rain|window|storm|weather|glass)\b', re.I), "rain-window"),
    (re.compile(r'\b(shadow|shadows|silhouette|darkness|dark room|mystery)\b', re.I), "silhouette"),
    (re.compile(r'\b(clock|seconds|timer|time|hourglass|four seconds)\b', re.I), "clock"),
]

def map_text_to_verified_slug(text: str, fallback_slug: str = "shadow") -> str:
    """Extracts the best physical visual slug matching the spoken sentence."""
    t_clean = text.lower()
    for pattern, slug in SCRIPT_VISUAL_TRIGGER_MAP:
        if pattern.search(t_clean):
            return slug
    # If text is already a known slug or close to one
    hyphenated = t_clean.strip().replace(" ", "-")
    if hyphenated in VERIFIED_STOCK_SLUGS:
        return hyphenated
    return fallback_slug

def extract_timeline_visual_queries(
    script_text: str,
    target_cuts: int,
    keywords_from_prompt: Optional[List[str]] = None,
    niche: str = "dark_psychology"
) -> List[str]:
    """
    Parses spoken script into target_cuts chronological segments,
    matching each cut directly to what is spoken in that specific 2-4 second window.
    Guarantees every query is a verified physical slug that returns 15-35+ HD clips.
    """
    profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
    niche_bank = profile.get("visual_bank", ["silhouette", "tunnel", "subway-station", "cctv-camera", "eye-contact"])
    clean_niche_bank = [s.replace("-station", "").replace("-camera", "").replace("-contact", "") for s in niche_bank]

    # Split script into natural sentence or punctuation chunks
    raw_sentences = [s.strip() for s in re.split(r'[.!?]+', script_text) if len(s.strip()) > 8]
    if not raw_sentences:
        raw_sentences = [script_text]

    # Map chunks evenly across target_cuts
    cuts_queries: List[str] = []
    total_chunks = len(raw_sentences)

    for cut_idx in range(target_cuts):
        # Pick the sentence chunk covering this time slice
        chunk_idx = min(int((cut_idx / float(target_cuts)) * total_chunks), total_chunks - 1)
        sentence_chunk = raw_sentences[chunk_idx]

        # First priority: concrete visual matched from what is spoken right here
        matched_slug = None
        for pattern, slug in SCRIPT_VISUAL_TRIGGER_MAP:
            if pattern.search(sentence_chunk):
                matched_slug = slug
                break

        # Second priority: if cut 0/1 and prompt keywords provided, map keyword
        if not matched_slug and keywords_from_prompt and cut_idx < len(keywords_from_prompt):
            kw = keywords_from_prompt[cut_idx]
            matched_slug = map_text_to_verified_slug(kw, fallback_slug="")

        # Third priority: pick from verified niche bank cycling cleanly
        if not matched_slug:
            fallback_idx = cut_idx % len(VERIFIED_STOCK_SLUGS)
            matched_slug = list(VERIFIED_STOCK_SLUGS)[fallback_idx]

        # Prevent 3 identical clips in a row
        if len(cuts_queries) >= 2 and cuts_queries[-1] == matched_slug and cuts_queries[-2] == matched_slug:
            # Shift to another verified slug
            matched_slug = random.choice([s for s in VERIFIED_STOCK_SLUGS if s != matched_slug])

        cuts_queries.append(matched_slug)

    return cuts_queries

def harvest_candidates_for_query(query: str) -> List[str]:
    """Scrapes Mixkit (pages 1-5), Coverr, Pixabay (if key or public), and Pexels for HD MP4 links."""
    q_clean = query.strip().lower().replace(" ", "-")
    if not q_clean:
        return []

    now = time.time()
    if q_clean in _QUERY_CACHE:
        ts, cached_urls = _QUERY_CACHE[q_clean]
        if now - ts < CACHE_TTL and cached_urls:
            return list(cached_urls)

    results: List[str] = []

    # 1. Pexels Video API (Free BYOK or env)
    pexels_key = os.environ.get("PEXELS_API_KEY")
    if pexels_key:
        try:
            pex_url = f"https://api.pexels.com/videos/search?query={q_clean}&orientation=portrait&per_page=15"
            pr = requests.get(pex_url, headers={"Authorization": pexels_key}, timeout=8)
            if pr.status_code == 200:
                pdata = pr.json()
                for v in pdata.get("videos", []):
                    files = v.get("video_files", [])
                    best = next((f["link"] for f in files if f.get("height", 0) >= 720 and f.get("link")), None)
                    if best and best not in results:
                        results.append(best)
        except Exception as e:
            print(f"Pexels fetch note: {e}")

    # 2. Pixabay Video API (Free BYOK or env)
    pixabay_key = os.environ.get("PIXABAY_API_KEY")
    if pixabay_key:
        try:
            pix_url = f"https://pixabay.com/api/videos/?key={pixabay_key}&q={urllib.parse.quote_plus(query)}&video_type=film&per_page=15"
            pr = requests.get(pix_url, timeout=8)
            if pr.status_code == 200:
                pdata = pr.json()
                for hit in pdata.get("hits", []):
                    vids = hit.get("videos", {})
                    # Prefer medium or large vertical/HD
                    cand = vids.get("medium", {}).get("url") or vids.get("large", {}).get("url") or vids.get("small", {}).get("url")
                    if cand and cand not in results:
                        results.append(cand)
        except Exception as e:
            print(f"Pixabay fetch note: {e}")

    # 3. Mixkit Pages 1 to 2 (Fast & rate-limit safe)
    for page in (1, 2):
        try:
            page_url = f"https://mixkit.co/free-stock-video/{q_clean}/" if page == 1 else f"https://mixkit.co/free-stock-video/{q_clean}/?page=2"
            r = requests.get(page_url, headers=HEADERS, timeout=6)
            if r.status_code == 200:
                found = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-(?:1080|720|360)\.mp4', r.text)
                for f in found:
                    hd = re.sub(r'-\d+\.mp4$', '-720.mp4', f) if 'mixkit.co' in f else f
                    if hd not in results:
                        results.append(hd)
            elif r.status_code == 429:
                break
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
    # Ensure query is translated to a verified physical slug
    verified_query = map_text_to_verified_slug(query, fallback_slug=query.lower().replace(" ", "-"))
    candidates = harvest_candidates_for_query(verified_query)

    # If primary query returned nothing, harvest from verified fallback slugs
    if not candidates:
        for fq in ["silhouette", "tunnel", "subway", "security-camera", "crowd", "eye", "dark-street"]:
            candidates = harvest_candidates_for_query(fq)
            if candidates:
                break

    if not candidates:
        import glob, shutil
        existing_clips = glob.glob(os.path.join(BASE_DIR, "users_data", "*", "videos", "*", "clip_*.mp4"))
        if existing_clips:
            fresh_local = [c for c in existing_clips if c not in used_in_video]
            picked = random.choice(fresh_local or existing_clips)
            used_in_video.add(picked)
            shutil.copy2(picked, dest_path)
            return True, f"local_cached_{os.path.basename(picked)}"
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

def render_motion_video(
    clip_paths: list,
    audio_path: str,
    ass_path: str,
    output_mp4: str,
    duration: float,
    color_look: Optional[str] = None,
    audio_bed: Optional[str] = None
):
    import random
    # Select or randomly pick color look & audio bed for complete visual/auditory distinctiveness
    if not color_look or color_look not in COLOR_LOOKS:
        c_key = random.choice(list(COLOR_LOOKS.keys()))
    else:
        c_key = color_look

    if not audio_bed or audio_bed not in AUDIO_BEDS:
        a_key = random.choice(list(AUDIO_BEDS.keys()))
    else:
        a_key = audio_bed

    color_cfg = COLOR_LOOKS[c_key]
    audio_cfg = AUDIO_BEDS[a_key]

    print(f"[4/5] Multi-cut render ({len(clip_paths)} cuts, {duration:.2f}s) [Color: {color_cfg['name']} | Soundscape: {audio_cfg['name']}]...")

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

        # Alternating subtle punch-in (1.1x zoom) vs standard scale for rapid pattern-interrupts
        if i % 2 == 0:
            scale_crop = "scale=1200:2133:force_original_aspect_ratio=increase,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
        else:
            scale_crop = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"

        filter_parts.append(
            f"[{i}:v]trim=start={offset}:duration={per_clip:.3f},setpts=PTS-STARTPTS,fps=30,"
            f"{scale_crop},setsar=1{flip_filter}[v{i}]"
        )

    concat_ins = "".join(f"[v{i}]" for i in range(len(clip_paths)))
    concat_filter = f"{concat_ins}concat=n={len(clip_paths)}:v=1:a=0[vbase]"

    # Apply Procedural Color Grade Look
    grade_filter = f"[vbase]{color_cfg['filter']}[vgraded]"

    clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    clean_fonts = FONTS_DIR.replace("\\", "/").replace(":", "\\:")
    fonts_arg = f":fontsdir='{clean_fonts}'" if os.path.exists(FONTS_DIR) else ""
    subtitle_filter = f"[vgraded]ass='{clean_ass}'{fonts_arg}[vfinal]"

    # Audio mix with procedural tension bed
    audio_input_idx = len(clip_paths)
    synth_input_idx = len(clip_paths) + 1
    bed_weight = audio_cfg.get("weight", 0.14)
    audio_filter = f"[{audio_input_idx}:a][{synth_input_idx}:a]amix=inputs=2:duration=first:weights=1.0 {bed_weight}[afinal]"

    full_filter = ";".join(filter_parts) + ";" + concat_filter + ";" + grade_filter + ";" + subtitle_filter + ";" + audio_filter

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-i", audio_path,
        "-f", "lavfi", "-t", f"{duration:.2f}",
        "-i", audio_cfg["filter"],
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


def get_gameplay_clip(gameplay_pref: str = "minecraft") -> str:
    """Finds a gameplay background video from the local gameplay bank."""
    if not os.path.exists(GAMEPLAY_DIR):
        os.makedirs(GAMEPLAY_DIR, exist_ok=True)
    files = [os.path.join(GAMEPLAY_DIR, f) for f in os.listdir(GAMEPLAY_DIR) if f.endswith(".mp4")]
    if not files:
        raise RuntimeError("No gameplay clips found in shorts_engine/gameplay bank.")
    pref = [f for f in files if gameplay_pref.lower() in os.path.basename(f).lower()]
    return random.choice(pref if pref else files)


def render_gameplay_short(
    audio_path: str,
    ass_path: str,
    output_mp4: str,
    duration: float,
    gameplay_path: Optional[str] = None
):
    """Renders 60/30fps vertical hypnotic Minecraft Parkour / Satisfying Short in ~3-4 seconds."""
    if not gameplay_path or not os.path.exists(gameplay_path):
        gameplay_path = get_gameplay_clip()
    print(f"[4/5] Rendering High-Retention Gameplay short ({duration:.2f}s) from {os.path.basename(gameplay_path)}...")
    clip_dur = get_video_duration(gameplay_path)
    max_offset = max(0.0, clip_dur - duration - 2.0)
    offset = round(random.uniform(0.0, max_offset), 2) if max_offset > 5.0 else 0.0

    flip = ",hflip" if random.random() < 0.35 else ""
    clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    clean_fonts = FONTS_DIR.replace("\\", "/").replace(":", "\\:")
    fonts_arg = f":fontsdir='{clean_fonts}'" if os.path.exists(FONTS_DIR) else ""

    filter_complex = (
        f"[0:v]trim=start={offset}:duration={duration:.2f},setpts=PTS-STARTPTS,fps=30,"
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"eq=contrast=1.08:saturation=1.12{flip},"
        f"ass='{clean_ass}'{fonts_arg}[vfinal];"
        f"[1:a][2:a]amix=inputs=2:duration=first:weights=1.0 0.12[afinal]"
    )

    cmd = [
        FFMPEG, "-y",
        "-ss", f"{offset:.2f}",
        "-t", f"{duration:.2f}",
        "-i", gameplay_path,
        "-i", audio_path,
        "-f", "lavfi", "-t", f"{duration:.2f}",
        "-i", "anoisesrc=d=60:c=pink:r=44100:a=0.03,lowpass=f=140",
        "-filter_complex", filter_complex,
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
        print("FFmpeg gameplay render error:", res.stderr[-800:])
        raise RuntimeError("FFmpeg gameplay render failed")
    print(f"Gameplay short rendered: {output_mp4}")


def render_split_retention_short(
    clip_paths: list,
    audio_path: str,
    ass_path: str,
    output_mp4: str,
    duration: float,
    gameplay_path: Optional[str] = None
):
    """Renders 50/50 Split-Screen (Top: Cinematic Story Cuts, Bottom: Minecraft Parkour, Center: Bold Captions)."""
    if not gameplay_path or not os.path.exists(gameplay_path):
        gameplay_path = get_gameplay_clip("minecraft")
    print(f"[4/5] Rendering 50/50 Split-Screen video (Story Visuals + Parkour, {duration:.2f}s)...")
    clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    clean_fonts = FONTS_DIR.replace("\\", "/").replace(":", "\\:")
    fonts_arg = f":fontsdir='{clean_fonts}'" if os.path.exists(FONTS_DIR) else ""

    cuts = clip_paths[:min(6, len(clip_paths))] if clip_paths else []
    per_cut = duration / max(1, len(cuts))

    inputs = []
    top_parts = []
    for i, c in enumerate(cuts):
        inputs.extend(["-stream_loop", "-1", "-i", c])
        top_parts.append(
            f"[{i}:v]trim=duration={per_cut:.3f},setpts=PTS-STARTPTS,fps=30,"
            f"scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top_{i}]"
        )
    concat_top = "".join(f"[top_{i}]" for i in range(len(cuts)))
    top_chain = f"{concat_top}concat=n={len(cuts)}:v=1:a=0[vtop]" if cuts else ""

    gameplay_input_idx = len(cuts)
    inputs.extend(["-stream_loop", "-1", "-i", gameplay_path])
    gp_dur = get_video_duration(gameplay_path)
    gp_offset = round(random.uniform(0.0, max(0.0, gp_dur - duration - 2.0)), 2)

    bottom_chain = (
        f"[{gameplay_input_idx}:v]trim=start={gp_offset}:duration={duration:.2f},setpts=PTS-STARTPTS,fps=30,"
        f"scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[vbottom]"
    )

    stack_chain = "[vtop][vbottom]vstack=inputs=2[vstacked]"
    div_chain = "[vstacked]drawbox=y=958:color=black@0.9:width=1080:height=4:t=fill[vdivided]"
    sub_chain = f"[vdivided]ass='{clean_ass}'{fonts_arg}[vfinal]"

    audio_input_idx = len(inputs)
    synth_input_idx = audio_input_idx + 1
    audio_chain = f"[{audio_input_idx}:a][{synth_input_idx}:a]amix=inputs=2:duration=first:weights=1.0 0.12[afinal]"

    filter_chains = []
    if top_parts:
        filter_chains.extend(top_parts)
    if top_chain:
        filter_chains.append(top_chain)
    filter_chains.extend([bottom_chain, stack_chain, div_chain, sub_chain, audio_chain])
    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-i", audio_path,
        "-f", "lavfi", "-t", f"{duration:.2f}",
        "-i", "anoisesrc=d=60:c=pink:r=44100:a=0.03,lowpass=f=140",
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
        print("FFmpeg split render error:", res.stderr[-800:])
        raise RuntimeError("FFmpeg split render failed")
    print(f"Split retention short rendered: {output_mp4}")


async def produce_motion_short(
    video_id: str,
    script_text: str,
    clip_keywords: list,
    seo_meta: dict,
    niche: str = "dark_psychology",
    clip_history_file: Optional[str] = None,
    target_dir: Optional[str] = None,
    visual_mode: str = "cinematic_cuts"
):
    if not target_dir:
        target_dir = os.path.join(BASE_DIR, "videos", video_id)
    os.makedirs(target_dir, exist_ok=True)

    audio_file = os.path.join(target_dir, "voice.mp3")
    ass_file = os.path.join(target_dir, "captions.ass")
    output_mp4 = os.path.join(target_dir, f"{video_id}.mp4")
    meta_file = os.path.join(target_dir, "seo_metadata.txt")

    print(f"\n=== PRODUCING REAL-MOTION SHORT: {video_id.upper()} (Niche: {niche} | Mode: {visual_mode}) ===")
    words = await generate_voice(script_text, audio_file)
    dur = get_audio_duration(audio_file)
    print(f"Audio Duration: {dur:.2f}s")

    build_ass_subtitles(words, ass_file)

    if visual_mode == "parkour_brainrot":
        # Pure Hypnotic Gameplay (Minecraft Parkour / Subway Surfers)
        gameplay_file = get_gameplay_clip("minecraft")
        render_gameplay_short(audio_file, ass_file, output_mp4, dur, gameplay_file)

    elif visual_mode == "split_retention":
        # 50/50 Split Screen: Top Story Visuals + Bottom Minecraft Parkour
        gameplay_file = get_gameplay_clip("minecraft")
        target_cuts = 4
        timeline_queries = extract_timeline_visual_queries(
            script_text=script_text,
            target_cuts=target_cuts,
            keywords_from_prompt=clip_keywords,
            niche=niche
        )
        clip_paths = []
        used_in_video: Set[str] = set()
        clip_history = load_clip_history(clip_history_file)
        for idx, kw in enumerate(timeline_queries):
            c_path = os.path.join(target_dir, f"clip_{idx}.mp4")
            _, _ = download_clip_with_smart_fallback(kw, c_path, niche, used_in_video, clip_history)
            clip_paths.append(c_path)
        render_split_retention_short(clip_paths, audio_file, ass_file, output_mp4, dur, gameplay_file)

    else:
        # Standard Multi-Cut High Pacing Cinematic Stock synchronized to spoken script
        target_cuts = max(12, min(18, round(dur / 2.6)))
        timeline_queries = extract_timeline_visual_queries(
            script_text=script_text,
            target_cuts=target_cuts,
            keywords_from_prompt=clip_keywords,
            niche=niche
        )

        clip_history = load_clip_history(clip_history_file)
        used_in_video: Set[str] = set()
        chosen_urls: List[str] = []
        clip_paths: List[str] = []

        print(f"[3/5] Scraping & downloading {len(timeline_queries)} script-synchronized stock clips: {timeline_queries}...")
        for idx, kw in enumerate(timeline_queries):
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

        record_clip_usage(clip_history_file, chosen_urls)
        render_motion_video(clip_paths, audio_file, ass_file, output_mp4, dur)

    strip_watermarks(output_mp4)

    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE:\n{seo_meta['title']}\n\n")
        f.write(f"DESCRIPTION:\n{seo_meta['description']}\n\n")
        if "search_tags" in seo_meta and seo_meta["search_tags"]:
            st = seo_meta["search_tags"]
            tags_str = ", ".join(st) if isinstance(st, list) else str(st)
            f.write(f"TAGS:\n{tags_str}\n\n")
        f.write(f"PINNED COMMENT:\n{seo_meta['pinned_comment']}\n")

    mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"\n[SUCCESS] REAL-MOTION SHORT READY: {output_mp4} ({mb:.2f} MB)\n")
    return output_mp4
