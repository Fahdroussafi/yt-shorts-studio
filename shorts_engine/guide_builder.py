import asyncio
import json
import os
import re
import subprocess
from typing import Dict, List, Optional

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from engine import FFMPEG, generate_voice, get_audio_duration


def _find_font(bold: bool = False) -> Optional[str]:
    candidates = (
        [
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
    )
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _find_font(bold=bold)
    if path:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> List[str]:
    words = (text or "").split()
    lines: List[str] = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip()
        bbox = draw.textbbox((0, 0), cand, font=font)
        if bbox[2] - bbox[0] <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fmt_ts(sec: float) -> str:
    s = max(0, int(round(sec)))
    m, rem = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{rem:02d}" if h else f"{m}:{rem:02d}"


def generate_guide_blueprint(
    topic: str,
    brand_name: str = "PixelBreach",
    brand_handle: str = "@PixelBreach-y6",
    target_minutes: int = 6,
    user_key_file: Optional[str] = None,
    niche: str = "gta6_launch",
    topic_history_file: Optional[str] = None,
) -> Dict:
    """Generates a true 5-8 min 16:9 chaptered guide blueprint (2-stage outline + deep per-chapter narration)."""
    from concurrent.futures import ThreadPoolExecutor
    from gemini_generator import get_groq_key, generate_with_groq_lpu
    from gta_news_engine import _fetch_article_paragraphs, scrape_article_media, fetch_gta_articles
    from idea_bank import load_topic_history, record_topic_history, pick_concept_without_repeats

    raw_topic = (topic or "").strip()
    scraped_context = ""
    media_urls: List[str] = []

    # Surprise Me mode when topic is blank: auto-pick fresh real RSS article (GTA) or unused concept
    if not raw_topic:
        used_titles = set()
        for e in load_topic_history(topic_history_file):
            for k in ("angle", "concept", "title"):
                val = str(e.get(k, "")).strip().lower()
                if val:
                    used_titles.add(val)

        if niche == "gta6_launch":
            articles = fetch_gta_articles(topic_filter=None, used_titles=used_titles) or fetch_gta_articles(topic_filter=None, used_titles=set())
            if articles:
                art = articles[0]
                raw_topic = art["title"]
                body = art.get("body") or ""
                if len(body) < 500 and art.get("link"):
                    fetched = _fetch_article_paragraphs(art["link"])
                    if len(fetched) > len(body):
                        body = fetched
                scraped_context = body[:3800]
                media_urls = scrape_article_media(art.get("link", ""), max_items=10)
            else:
                raw_topic = "GTA 6 Complete Beginner Guide, Best Settings & Early Strategy"
        else:
            picked = pick_concept_without_repeats(niche=niche, history_file=topic_history_file, brand_name=brand_name, brand_handle=brand_handle)
            raw_topic = picked.get("title", "Deep Dive Guide").replace("#shorts", "").strip()
            scraped_context = picked.get("script", "")
    elif raw_topic.startswith("http://") or raw_topic.startswith("https://"):
        scraped_context = _fetch_article_paragraphs(raw_topic)[:3800]
        media_urls = scrape_article_media(raw_topic, max_items=10)
    elif len(raw_topic) > 180:
        scraped_context = raw_topic[:3800]
        raw_topic = raw_topic.splitlines()[0][:90].strip()

    target_minutes = max(5, min(10, int(target_minutes or 6)))
    num_chapters = target_minutes  # ~1 min per chapter (155 words @ +3% edge-tts = ~60s)
    words_per_ch = 155

    g_key = get_groq_key(user_key_file, allow_fallback=True)
    if not g_key:
        raise RuntimeError("Groq API key required for long-form guide generation.")

    ctx_block = f"\nReference Source Facts:\n{scraped_context}\n" if scraped_context else ""

    # Stage 1: Outline + UI Info Card specs (fast, fits cleanly inside JSON token budget)
    outline_prompt = (
        f'Plan a complete {target_minutes}-minute YouTube 16:9 guide video on:\n'
        f'Topic: "{raw_topic}"\n{ctx_block}\n'
        f'Channel: {brand_name} ({brand_handle})\n\n'
        f'Requirements:\n'
        f'- Exactly {num_chapters} chapters (Chapter 1 = Intro/Hook, middle = deep actionable tips/mechanics/comparisons, final = Summary & Outro).\n'
        f'- Mix card_type across chapters: "step" (3 concise bullets), "stats" (3-4 rated bars 0-100), "compare" (do_list vs avoid_list).\n'
        f'- Keep each bullet under 56 chars so it fits cleanly on 1920x1080 UI cards.\n'
        f'- Output strictly valid JSON:\n'
        f'{{\n'
        f'  "title": "Catchy 16:9 YouTube Guide Title (under 70 chars, NO #shorts)",\n'
        f'  "description": "2-sentence SEO summary for YouTube description",\n'
        f'  "search_tags": ["gta 6 guide", "gta 6 tips", "gta vi", "rockstar games"],\n'
        f'  "pinned_comment": "Short question for viewers in comments",\n'
        f'  "chapters": [\n'
        f'    {{\n'
        f'      "chapter_title": "Short Chapter Name",\n'
        f'      "badge": "INTRO" or "TIP 01" or "STATS" or "DO VS AVOID",\n'
        f'      "headline": "Big UI Card Headline (under 42 chars)",\n'
        f'      "card_type": "step",\n'
        f'      "bullets": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],\n'
        f'      "stats": [{{"label": "Metric", "value": 85}}],\n'
        f'      "do_list": ["Smart move 1", "Smart move 2"],\n'
        f'      "avoid_list": ["Mistake 1", "Mistake 2"]\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
    )

    outline = generate_with_groq_lpu(outline_prompt, g_key)
    if not isinstance(outline, dict) or not outline.get("chapters"):
        raise RuntimeError("Failed to generate guide outline from AI.")

    chapters = outline["chapters"][:num_chapters]
    guide_title = (outline.get("title") or raw_topic)[:85].replace("#shorts", "").strip()

    # Stage 2: Expand each chapter narration to ~155 spoken words (~60s each -> true 5/6/8 min total)
    def _expand_chapter(idx_ch):
        idx, ch = idx_ch
        is_first = idx == 0
        is_last = idx == len(chapters) - 1
        role = (
            "Opening hook & roadmap: grab viewer attention immediately and preview what this guide covers."
            if is_first
            else (
                f"Final wrap-up: recap top takeaways and close with 'Subscribe to {brand_name} for more in-depth guides.'"
                if is_last
                else f"Deep-dive explanation for Chapter {idx + 1}: explain WHY it works, give concrete examples, numbers, and step-by-step advice."
            )
        )
        p = (
            f'Write the spoken voiceover narration for Chapter {idx + 1} of {len(chapters)} in the YouTube guide "{guide_title}".\n'
            f'Chapter Title: {ch.get("chapter_title")}\n'
            f'Card Headline: {ch.get("headline")}\n'
            f'On-screen points: {json.dumps(ch.get("bullets") or ch.get("do_list") or ch.get("stats") or [])}\n'
            f'Context: {scraped_context[:1000]}\n'
            f'Role: {role}\n'
            f'Rules: Write between {words_per_ch - 10} and {words_per_ch + 20} words of natural, punchy spoken English. '
            f'No markdown, no bullet symbols, no stage directions, no "Chapter X" label.\n'
            f'Respond ONLY with JSON: {{"narration": "..."}}'
        )
        r = generate_with_groq_lpu(p, g_key)
        narr = re.sub(r"\s+", " ", (r.get("narration") or "").strip()) if isinstance(r, dict) else ""
        if len(narr.split()) < 60:
            pts = ". ".join(str(x) for x in (ch.get("bullets") or ch.get("do_list") or [ch.get("headline", "")]))
            narr = f"{ch.get('headline', '')}. {pts}. {narr}".strip()
        ch["narration"] = narr
        return ch

    with ThreadPoolExecutor(max_workers=3) as pool:
        chapters = list(pool.map(_expand_chapter, list(enumerate(chapters))))

    if topic_history_file:
        record_topic_history(topic_history_file, guide_title, niche, raw_topic)

    total_words = sum(len((c.get("narration") or "").split()) for c in chapters)

    return {
        "title": guide_title,
        "description": (outline.get("description") or raw_topic).strip(),
        "search_tags": outline.get("search_tags") or ["gta 6 guide", "gta 6 tips", "gta vi"],
        "pinned_comment": outline.get("pinned_comment") or "Which tip helped you most? Drop it below.",
        "chapters": chapters,
        "media_urls": media_urls,
        "target_minutes": target_minutes,
        "total_words": total_words,
        "model_used": outline.get("model_used", "groq-lpu"),
    }


def _download_images(media_urls: List[str], work_dir: str) -> List[str]:
    paths: List[str] = []
    for i, u in enumerate((media_urls or [])[:10]):
        if not u or u.lower().endswith((".mp4", ".webm")):
            continue
        dst = os.path.join(work_dir, f"bg_{i}.jpg")
        try:
            r = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
            if r.status_code == 200 and len(r.content) > 4000:
                with open(dst, "wb") as f:
                    f.write(r.content)
                paths.append(dst)
        except Exception:
            continue
    return paths


def render_guide_card_png(
    chapter: Dict,
    out_png: str,
    brand_name: str,
    idx: int,
    total: int,
    bg_image_path: Optional[str] = None,
) -> str:
    """Renders a 1920x1080 GTA-styled UI Info Card PNG using Pillow."""
    W, H = 1920, 1080
    canvas = Image.new("RGBA", (W, H), (10, 14, 26, 255))

    # 1. Background (blurred screenshot or gradient)
    if bg_image_path and os.path.exists(bg_image_path):
        try:
            bg = Image.open(bg_image_path).convert("RGB")
            bw, bh = bg.size
            scale = max(W / bw, H / bh)
            bg = bg.resize((int(bw * scale), int(bh * scale)), Image.Resampling.LANCZOS)
            left = (bg.width - W) // 2
            top = (bg.height - H) // 2
            bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(18))
            canvas.paste(bg.convert("RGBA"), (0, 0))
            dim = Image.new("RGBA", (W, H), (8, 12, 24, 195))
            canvas = Image.alpha_composite(canvas, dim)
        except Exception:
            pass
    else:
        grad = ImageDraw.Draw(canvas)
        for y in range(0, H, 4):
            ratio = y / H
            r = int(12 + 18 * ratio)
            g = int(16 + 10 * ratio)
            b = int(34 + 28 * (1 - ratio))
            grad.rectangle([(0, y), (W, y + 4)], fill=(r, g, b, 255))

    draw = ImageDraw.Draw(canvas)

    # Subtle cyber grid
    for gx in range(0, W, 120):
        draw.line([(gx, 0), (gx, H)], fill=(255, 255, 255, 10), width=1)
    for gy in range(0, H, 120):
        draw.line([(0, gy), (W, gy)], fill=(255, 255, 255, 10), width=1)

    # 2. Main Glassmorphic Card
    card_box = (88, 76, W - 88, H - 96)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(panel)
    p_draw.rounded_rectangle(card_box, radius=32, fill=(13, 18, 34, 228), outline=(56, 189, 248, 140), width=3)
    # Top neon accent strip
    p_draw.rounded_rectangle((88, 76, W - 88, 92), radius=8, fill=(236, 72, 153, 255))
    canvas = Image.alpha_composite(canvas, panel)
    draw = ImageDraw.Draw(canvas)

    f_badge = _load_font(26, bold=True)
    f_brand = _load_font(24, bold=True)
    f_title = _load_font(56, bold=True)
    f_sub = _load_font(34, bold=True)
    f_body = _load_font(30, bold=False)
    f_small = _load_font(24, bold=True)

    # 3. Header row: Badge + Channel + Step counter
    badge_txt = str(chapter.get("badge") or f"CHAPTER {idx + 1}").upper()[:22]
    b_box = draw.textbbox((0, 0), badge_txt, font=f_badge)
    bw = (b_box[2] - b_box[0]) + 44
    draw.rounded_rectangle((144, 132, 144 + bw, 186), radius=14, fill=(6, 182, 212, 255))
    draw.text((166, 143), badge_txt, font=f_badge, fill=(9, 14, 26, 255))

    step_txt = f"{idx + 1:02d} / {total:02d}"
    draw.text((W - 260, 142), f"@{brand_name}  •  {step_txt}", font=f_brand, fill=(148, 163, 184, 255))

    # 4. Headline
    headline = str(chapter.get("headline") or chapter.get("chapter_title") or "Guide Breakdown").strip()
    h_lines = _wrap_text(draw, headline, f_title, W - 320)[:2]
    hy = 222
    for hl in h_lines:
        draw.text((144, hy), hl, font=f_title, fill=(248, 250, 252, 255))
        hy += 70

    draw.rectangle((144, hy + 12, 340, hy + 18), fill=(236, 72, 153, 255))
    content_top = hy + 48

    # 5. Card Body by card_type
    ctype = (chapter.get("card_type") or "step").lower()
    has_inset = bool(bg_image_path and os.path.exists(bg_image_path)) and ctype == "step"
    left_max_w = 980 if has_inset else (W - 300)

    if ctype == "stats":
        stats = (chapter.get("stats") or [])[:4]
        if not stats:
            stats = [{"label": b[:28], "value": 85 - i * 12} for i, b in enumerate((chapter.get("bullets") or ["Impact", "Efficiency"])[:3])]
        sy = content_top + 10
        for st in stats:
            lbl = str(st.get("label") or "Metric")[:34]
            val = max(5, min(100, int(st.get("value") or 75)))
            draw.text((144, sy), lbl, font=f_sub, fill=(226, 232, 240, 255))
            draw.text((W - 240, sy), f"{val}%", font=f_sub, fill=(56, 189, 248, 255))
            bar_y = sy + 48
            draw.rounded_rectangle((144, bar_y, W - 154, bar_y + 26), radius=13, fill=(30, 41, 59, 255))
            fill_w = int((W - 298) * (val / 100.0))
            draw.rounded_rectangle((144, bar_y, 144 + max(26, fill_w), bar_y + 26), radius=13, fill=(56, 189, 248, 255))
            sy += 112

    elif ctype == "compare":
        do_items = (chapter.get("do_list") or chapter.get("bullets") or ["Prioritize core upgrades first"])[:3]
        avoid_items = (chapter.get("avoid_list") or ["Don't waste early cash on cosmetics"])[:3]
        col_w = 770
        # Left DO box
        draw.rounded_rectangle((144, content_top, 144 + col_w, H - 150), radius=24, fill=(6, 78, 59, 110), outline=(16, 185, 129, 200), width=2)
        draw.text((180, content_top + 26), "DO THIS", font=f_sub, fill=(52, 211, 153, 255))
        dy = content_top + 90
        for item in do_items:
            for ln in _wrap_text(draw, f"+ {item}", f_body, col_w - 72)[:2]:
                draw.text((180, dy), ln, font=f_body, fill=(236, 253, 245, 255))
                dy += 42
            dy += 22

        # Right AVOID box
        rx = 144 + col_w + 60
        draw.rounded_rectangle((rx, content_top, rx + col_w, H - 150), radius=24, fill=(127, 29, 29, 110), outline=(244, 63, 94, 200), width=2)
        draw.text((rx + 36, content_top + 26), "AVOID THIS", font=f_sub, fill=(251, 113, 133, 255))
        ay = content_top + 90
        for item in avoid_items:
            for ln in _wrap_text(draw, f"- {item}", f_body, col_w - 72)[:2]:
                draw.text((rx + 36, ay), ln, font=f_body, fill=(255, 241, 242, 255))
                ay += 42
            ay += 22

    else:  # "step"
        bullets = (chapter.get("bullets") or [chapter.get("chapter_title") or "Key Takeaway"])[:3]
        by = content_top + 8
        for b_i, b_txt in enumerate(bullets):
            box_h = 128
            draw.rounded_rectangle((144, by, 144 + left_max_w, by + box_h), radius=20, fill=(30, 41, 59, 190), outline=(71, 85, 105, 180), width=2)
            draw.rounded_rectangle((168, by + 34, 224, by + 90), radius=14, fill=(236, 72, 153, 255))
            draw.text((186, by + 44), str(b_i + 1), font=f_sub, fill=(255, 255, 255, 255))
            b_lines = _wrap_text(draw, str(b_txt), f_body, left_max_w - 130)[:2]
            ty = by + (38 if len(b_lines) == 1 else 22)
            for ln in b_lines:
                draw.text((248, ty), ln, font=f_body, fill=(241, 245, 249, 255))
                ty += 40
            by += box_h + 24

        if has_inset and bg_image_path:
            try:
                inset = Image.open(bg_image_path).convert("RGB")
                iw, ih = 560, 420
                sc = max(iw / inset.width, ih / inset.height)
                inset = inset.resize((int(inset.width * sc), int(inset.height * sc)), Image.Resampling.LANCZOS)
                il = (inset.width - iw) // 2
                it = (inset.height - ih) // 2
                inset = inset.crop((il, it, il + iw, it + ih))
                ix, iy = W - 144 - iw, content_top + 16
                draw.rounded_rectangle((ix - 6, iy - 6, ix + iw + 6, iy + ih + 6), radius=22, fill=(56, 189, 248, 255))
                canvas.paste(inset.convert("RGBA"), (ix, iy))
            except Exception:
                pass

    # 6. Bottom Progress Bar
    draw = ImageDraw.Draw(canvas)
    prog_w = int((W - 176) * ((idx + 1) / max(1, total)))
    draw.rounded_rectangle((88, H - 52, W - 88, H - 36), radius=8, fill=(30, 41, 59, 220))
    draw.rounded_rectangle((88, H - 52, 88 + max(24, prog_w), H - 36), radius=8, fill=(56, 189, 248, 255))
    draw.text((144, H - 132), f"CHAPTER: {chapter.get('chapter_title', '')}", font=f_small, fill=(148, 163, 184, 255))

    canvas.convert("RGB").save(out_png, quality=92)
    return out_png


async def render_long_guide_video(
    blueprint: Dict,
    output_mp4: str,
    thumb_jpg: str,
    work_dir: str,
    brand_name: str = "PixelBreach",
    voice: str = "en-US-AndrewMultilingualNeural",
    log_cb=None,
) -> Dict:
    """Synthesizes per-chapter TTS, renders 1920x1080 UI info cards, and concatenates cleanly."""
    os.makedirs(work_dir, exist_ok=True)
    chapters = blueprint.get("chapters") or []
    if not chapters:
        raise RuntimeError("Guide blueprint has no chapters.")

    bg_imgs = await asyncio.to_thread(_download_images, blueprint.get("media_urls") or [], work_dir)
    total = len(chapters)
    seg_paths: List[str] = []
    chapter_timestamps: List[str] = []
    elapsed = 0.0

    for idx, ch in enumerate(chapters):
        if log_cb:
            log_cb(f"[{idx+1}/{total}] Rendering chapter: {ch.get('chapter_title', f'Part {idx+1}')}...")
        narration = re.sub(r"\s+", " ", (ch.get("narration") or "").strip())
        if not narration:
            narration = f"{ch.get('headline', '')}. {' '.join(ch.get('bullets') or [])}"

        mp3_path = os.path.join(work_dir, f"ch_{idx}.mp3")
        png_path = os.path.join(work_dir, f"ch_{idx}.png")
        seg_mp4 = os.path.join(work_dir, f"seg_{idx}.mp4")

        await generate_voice(narration, mp3_path, voice=voice, rate="+3%", brand_name=brand_name)
        dur = max(4.0, get_audio_duration(mp3_path))
        chapter_timestamps.append(f"{_fmt_ts(elapsed)} {ch.get('chapter_title', f'Chapter {idx+1}')}")
        elapsed += dur

        bg_pick = bg_imgs[idx % len(bg_imgs)] if bg_imgs else None
        await asyncio.to_thread(render_guide_card_png, ch, png_path, brand_name, idx, total, bg_pick)

        if idx == 0:
            try:
                im = Image.open(png_path).resize((1280, 720), Image.Resampling.LANCZOS)
                im.save(thumb_jpg, quality=90)
            except Exception:
                pass

        # Render single chapter card -> 1920x1080 30fps mp4 with gentle fade in/out
        fade_out_st = max(0.2, dur - 0.35)
        vf = f"scale=1920:1080,fps=30,fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out_st:.2f}:d=0.35,format=yuv420p"
        cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-t", f"{dur:.2f}", "-i", png_path,
            "-i", mp3_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
            "-shortest", seg_mp4,
        ]
        res = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        if res.returncode != 0 or not os.path.exists(seg_mp4):
            raise RuntimeError(f"FFmpeg segment {idx} failed: {res.stderr[-250:]}")
        seg_paths.append(seg_mp4)

    concat_list = os.path.join(work_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for sp in seg_paths:
            f.write(f"file '{os.path.abspath(sp).replace(chr(92), '/')}'\n")

    concat_cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_mp4]
    c_res = await asyncio.to_thread(subprocess.run, concat_cmd, capture_output=True, text=True)
    if c_res.returncode != 0 or not os.path.exists(output_mp4):
        raise RuntimeError(f"FFmpeg concat failed: {c_res.stderr[-250:]}")

    return {
        "duration_sec": elapsed,
        "chapters_text": "\n".join(chapter_timestamps),
        "segments": len(seg_paths),
    }
