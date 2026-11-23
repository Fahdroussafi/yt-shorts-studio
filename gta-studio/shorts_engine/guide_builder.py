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
    return f"{h:02d}:{m:02d}:{rem:02d}" if h else f"{m:02d}:{rem:02d}"


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
    elif niche == "gta6_launch":
        # Ground custom short topics against live GTA RSS articles matching topic keywords
        all_arts = fetch_gta_articles(topic_filter=None, used_titles=set())
        q_words = {w for w in re.findall(r"[a-z0-9]+", raw_topic.lower()) if len(w) > 2 and w not in {"gta", "the", "and", "for", "with"}}
        matched = []
        for a in all_arts:
            hay = f"{a.get('title', '')} {a.get('body', '')[:300]}".lower()
            hits = sum(1 for w in q_words if w in hay)
            if hits > 0:
                matched.append((hits, a))
        matched.sort(key=lambda x: x[0], reverse=True)
        chosen_arts = [a for _, a in matched[:2]] or all_arts[:2]
        chunks = []
        for a in chosen_arts:
            b = a.get("body") or ""
            if len(b) < 500 and a.get("link"):
                fetched = _fetch_article_paragraphs(a["link"])
                if len(fetched) > len(b):
                    b = fetched
            if b:
                chunks.append(f"[{a.get('outlet', 'Source')}] {a.get('title', '')}: {b}")
            if a.get("link") and len(media_urls) < 10:
                media_urls.extend(scrape_article_media(a["link"], max_items=5))
        scraped_context = "\n\n".join(chunks)[:3800]
        media_urls = media_urls[:10]

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
        f'- STRICT FACTUALITY: Base every bullet, quote, and chapter ONLY on Reference Source Facts (when provided) and verified official GTA info. NEVER invent fake numbers, prices, dates, mission names, or unconfirmed features. Preserve "reportedly/rumored" hedging when source is unconfirmed.\n'
        f'- Exactly {num_chapters} chapters (Chapter 1 = Intro/Hook, middle = deep commentary & breakdown, final = Summary & Outro).\n'
        f'- Visual variety across chapters using card_type:\n'
        f'  * "editorial" (USE FOR ~75% OF CHAPTERS): Full-screen subject visual with smooth Ken Burns motion, clean top chapter HUD, and synced word-highlighted captions.\n'
        f'  * "quote" (USE FOR 1-2 CHAPTERS): Highlight a key verified fact, developer quote, or source takeaway on a clean documentary card.\n'
        f'  * "compare" (USE ONLY if topic is genuinely comparing two options like PS5 vs Xbox): do_list vs avoid_list.\n'
        f'- NEVER use "stats" unless Reference Source Facts contain real benchmark numbers.\n'
        f'- Keep each bullet under 56 chars so it fits cleanly on 1920x1080 overlays.\n'
        f'- Output strictly valid JSON:\n'
        f'{{\n'
        f'  "title": "High-CTR curiosity-gap YouTube title under 65 chars (e.g. \\"99% of GTA 6 Players Will Miss THIS\\", \\"Don\'t Make This GTA 6 Day One Mistake\\"). NO channel name, NO generic \'Master X: Pro Tips\', NO #shorts, NO fake claims",\n'
        f'  "description": "2-sentence SEO summary for YouTube description",\n'
        f'  "search_tags": ["gta 6 guide", "gta 6 tips", "gta vi", "rockstar games"],\n'
        f'  "pinned_comment": "Short question for viewers in comments",\n'
        f'  "chapters": [\n'
        f'    {{\n'
        f'      "chapter_title": "Short Chapter Name",\n'
        f'      "badge": "INTRO" or "KEY DETAIL" or "BREAKDOWN" or "VERDICT",\n'
        f'      "headline": "Big Overlay Headline (under 42 chars)",\n'
        f'      "card_type": "editorial",\n'
        f'      "bullets": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],\n'
        f'      "do_list": ["Option A point 1", "Option A point 2"],\n'
        f'      "avoid_list": ["Option B point 1", "Option B point 2"]\n'
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
            f'Reference Source Facts: {scraped_context[:3800]}\n'
            f'Role: {role}\n'
            f'Rules: Write between {words_per_ch - 10} and {words_per_ch + 20} words of natural, punchy spoken English. '
            f'STRICT FACTUALITY: ONLY state facts, numbers, dates, and names supported by Reference Source Facts or On-screen points — NEVER invent fake stats, prices, dates, or mechanics. If something is rumored/unconfirmed, say "reportedly" or "unconfirmed". '
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
                with Image.open(dst) as im:
                    w, h = im.size
                ratio = w / max(1, h)
                if w < 320 or h < 180 or ratio < 0.8 or ratio > 2.5:
                    os.remove(dst)
                    continue
                paths.append(dst)
        except Exception:
            continue
    return paths


def _ass_ts(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_16x9_ass_subtitles(words: List[Dict], ass_path: str) -> str:
    """Builds crisp 1920x1080 documentary ASS captions with active-word cyan highlight."""
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: DocCap,DejaVu Sans,54,&H00FFFFFF,&H00F8BD38,&H00080C18,&HB0000000,-1,0,0,0,100,100,0,0,1,4,2,2,120,120,125,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events: List[str] = []
    chunk_size = 5
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        if not chunk:
            continue
        for w_idx, active_w in enumerate(chunk):
            st = float(active_w.get("start", 0.0))
            if w_idx + 1 < len(chunk):
                en = float(chunk[w_idx + 1].get("start", st + 0.35))
            elif i + chunk_size < len(words):
                en = float(words[i + chunk_size].get("start", float(active_w.get("end", st + 0.4))))
            else:
                en = max(st + 0.4, float(active_w.get("end", st + 0.5)))
            en = max(st + 0.08, en)
            parts = []
            for j, item in enumerate(chunk):
                txt = str(item.get("word", "")).replace("{", "").replace("}", "")
                if j == w_idx:
                    parts.append(r"{\c&H00F8BD38&}" + txt + r"{\c&H00FFFFFF&}")
                else:
                    parts.append(txt)
            line = " ".join(parts)
            events.append(f"Dialogue: 0,{_ass_ts(st)},{_ass_ts(en)},DocCap,,0,0,0,,{line}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    return ass_path


def render_editorial_backdrop_jpg(
    out_jpg: str,
    bg_image_path: Optional[str] = None,
    idx: int = 0,
) -> str:
    """Builds a crisp 1920x1080 subject backdrop (blurred edge fill + centered sharp subject photo) for Ken Burns."""
    W, H = 1920, 1080
    canvas = Image.new("RGBA", (W, H), (10, 14, 26, 255))
    if bg_image_path and os.path.exists(bg_image_path):
        try:
            src = Image.open(bg_image_path).convert("RGB")
            sc_bg = max(W / src.width, H / src.height)
            bg = src.resize((int(src.width * sc_bg), int(src.height * sc_bg)), Image.Resampling.LANCZOS)
            left = (bg.width - W) // 2
            top = (bg.height - H) // 2
            bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(22))
            canvas.paste(bg.convert("RGBA"), (0, 0))
            dim = Image.new("RGBA", (W, H), (8, 12, 24, 150))
            canvas = Image.alpha_composite(canvas, dim)

            # Fit full subject image cleanly without cropping faces/logos
            sc_fg = min(W / src.width, H / src.height)
            fg_w, fg_h = max(1, int(src.width * sc_fg)), max(1, int(src.height * sc_fg))
            fg = src.resize((fg_w, fg_h), Image.Resampling.LANCZOS).convert("RGBA")
            canvas.paste(fg, ((W - fg_w) // 2, (H - fg_h) // 2))
        except Exception:
            pass
    else:
        grad = ImageDraw.Draw(canvas)
        for y in range(0, H, 4):
            ratio = y / H
            r = int(12 + (24 if idx % 2 == 0 else 14) * ratio)
            g = int(16 + 14 * ratio)
            b = int(38 + 26 * (1 - ratio))
            grad.rectangle([(0, y), (W, y + 4)], fill=(r, g, b, 255))
        for gx in range(0, W, 120):
            grad.line([(gx, 0), (gx, H)], fill=(56, 189, 248, 14), width=1)
        for gy in range(0, H, 120):
            grad.line([(0, gy), (W, gy)], fill=(56, 189, 248, 14), width=1)

    # Subtle top & bottom dark vignette for HUD + subtitle legibility
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for y in range(0, 220, 4):
        a = int(160 * (1.0 - y / 220.0))
        vd.rectangle([(0, y), (W, y + 4)], fill=(6, 9, 18, a))
    for y in range(H - 300, H, 4):
        a = int(215 * ((y - (H - 300)) / 300.0))
        vd.rectangle([(0, y), (W, y + 4)], fill=(6, 9, 18, a))
    canvas = Image.alpha_composite(canvas, vig)
    canvas.convert("RGB").save(out_jpg, quality=92)
    return out_jpg


def render_editorial_hud_png(
    chapter: Dict,
    out_png: str,
    brand_name: str,
    idx: int,
    total: int,
    all_chapters: Optional[List[Dict]] = None,
    start_ts: str = "00:00",
) -> str:
    """Minimal transparent 1920x1080 documentary HUD: top chapter badge + bottom timeline bar (center open)."""
    W, H = 1920, 1080
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    f_badge = _load_font(22, bold=True)
    f_head = _load_font(34, bold=True)
    f_brand = _load_font(22, bold=True)
    f_seg = _load_font(18, bold=True)

    # Top-left clean chapter pill + headline
    badge_txt = str(chapter.get("badge") or f"CHAPTER {idx + 1}").upper()[:18]
    headline = str(chapter.get("headline") or chapter.get("chapter_title") or "").strip()
    bb = draw.textbbox((0, 0), badge_txt, font=f_badge)
    bw = (bb[2] - bb[0]) + 28
    draw.rounded_rectangle((64, 36, 64 + bw, 76), radius=10, fill=(6, 182, 212, 240))
    draw.text((78, 43), badge_txt, font=f_badge, fill=(9, 14, 26, 255))
    draw.text((80 + bw, 43), f"[{start_ts}]", font=f_badge, fill=(226, 232, 240, 235))
    if headline:
        h_line = _wrap_text(draw, headline, f_head, 1180)[:1]
        if h_line:
            draw.text((66, 88), h_line[0], font=f_head, fill=(248, 250, 252, 245))

    # Top-right subtle channel badge
    pill_txt = f"@{brand_name}  •  {idx + 1:02d}/{total:02d}"
    pb = draw.textbbox((0, 0), pill_txt, font=f_brand)
    pw = (pb[2] - pb[0]) + 32
    draw.rounded_rectangle((W - 64 - pw, 36, W - 64, 80), radius=14, fill=(10, 14, 26, 190), outline=(56, 189, 248, 140), width=2)
    draw.text((W - 48 - pw, 46), pill_txt, font=f_brand, fill=(226, 232, 240, 235))

    # Bottom segmented chapter timeline bar
    bar_left, bar_right = 80, W - 80
    bar_w = bar_right - bar_left
    gap = 10
    n_seg = max(1, total)
    seg_w = int((bar_w - gap * (n_seg - 1)) / n_seg)
    for s_i in range(n_seg):
        sx0 = bar_left + s_i * (seg_w + gap)
        sx1 = bar_right if s_i == n_seg - 1 else (sx0 + seg_w)
        if s_i < idx:
            fill_col, txt_col = (14, 116, 144, 240), (148, 163, 184, 230)
        elif s_i == idx:
            fill_col, txt_col = (236, 72, 153, 255), (255, 255, 255, 255)
        else:
            fill_col, txt_col = (30, 41, 59, 210), (148, 163, 184, 180)
        draw.rounded_rectangle((sx0, H - 44, sx1, H - 28), radius=6, fill=fill_col)
        if all_chapters and s_i < len(all_chapters):
            c_lbl = str(all_chapters[s_i].get("chapter_title") or f"Part {s_i+1}")[:18]
            draw.text((sx0 + 4, H - 70), c_lbl, font=f_seg, fill=txt_col)

    canvas.save(out_png)
    return out_png


def _list_gameplay_videos() -> List[str]:
    gp_dir = os.environ.get("GAMEPLAY_DIR", "").strip()
    if not gp_dir or not os.path.isdir(gp_dir):
        gp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gameplay")
    if not os.path.isdir(gp_dir):
        return []
    return [os.path.join(gp_dir, f) for f in sorted(os.listdir(gp_dir)) if f.lower().endswith(".mp4")]


def render_guide_broll_overlay_png(
    chapter: Dict,
    out_png: str,
    brand_name: str,
    idx: int,
    total: int,
    bullet_idx: int = 0,
    all_chapters: Optional[List[Dict]] = None,
    start_ts: str = "00:00",
) -> str:
    """Renders a transparent 1920x1080 RGBA lower-third + segmented chapter bar for moving B-roll."""
    W, H = 1920, 1080
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Bottom gradient scrim so text + timeline stay crisp over bright gameplay
    for y in range(H - 340, H, 4):
        alpha = int(225 * ((y - (H - 340)) / 340.0))
        draw.rectangle([(0, y), (W, y + 4)], fill=(8, 12, 22, alpha))

    f_badge = _load_font(22, bold=True)
    f_brand = _load_font(22, bold=True)
    f_head = _load_font(42, bold=True)
    f_sub = _load_font(28, bold=False)
    f_small = _load_font(22, bold=True)
    f_seg = _load_font(18, bold=True)

    # Top-right subtle watermark pill
    pill_txt = f"@{brand_name}  •  {idx + 1:02d}/{total:02d}"
    pb = draw.textbbox((0, 0), pill_txt, font=f_brand)
    pw = (pb[2] - pb[0]) + 32
    draw.rounded_rectangle((W - 64 - pw, 36, W - 64, 82), radius=14, fill=(10, 14, 26, 185), outline=(56, 189, 248, 140), width=2)
    draw.text((W - 48 - pw, 46), pill_txt, font=f_brand, fill=(226, 232, 240, 235))

    # Bottom-left sleek lower-third glass card
    bullets = chapter.get("bullets") or [chapter.get("chapter_title") or "Key Takeaway"]
    active_b = str(bullets[bullet_idx % len(bullets)])
    headline = str(chapter.get("headline") or chapter.get("chapter_title") or "Guide Breakdown").strip()
    badge_txt = str(chapter.get("badge") or f"CHAPTER {idx + 1}").upper()[:20]

    box_x0, box_y0, box_x1, box_y1 = 80, H - 305, 1180, H - 125
    draw.rounded_rectangle((box_x0, box_y0, box_x1, box_y1), radius=20, fill=(11, 16, 30, 220), outline=(56, 189, 248, 160), width=2)
    draw.rounded_rectangle((box_x0, box_y0 + 18, box_x0 + 8, box_y1 - 18), radius=4, fill=(236, 72, 153, 255))

    # Badge + timestamp
    bb = draw.textbbox((0, 0), badge_txt, font=f_badge)
    bw = (bb[2] - bb[0]) + 28
    draw.rounded_rectangle((box_x0 + 28, box_y0 + 18, box_x0 + 28 + bw, box_y0 + 54), radius=10, fill=(6, 182, 212, 255))
    draw.text((box_x0 + 42, box_y0 + 24), badge_txt, font=f_badge, fill=(9, 14, 26, 255))
    draw.text((box_x0 + 44 + bw, box_y0 + 24), f"[{start_ts}]", font=f_small, fill=(148, 163, 184, 255))

    # Headline + rotating bullet
    h_lines = _wrap_text(draw, headline, f_head, box_x1 - box_x0 - 60)[:1]
    draw.text((box_x0 + 28, box_y0 + 66), h_lines[0] if h_lines else headline, font=f_head, fill=(248, 250, 252, 255))
    b_lines = _wrap_text(draw, f"▸ {active_b}", f_sub, box_x1 - box_x0 - 60)[:1]
    draw.text((box_x0 + 28, box_y0 + 122), b_lines[0] if b_lines else active_b, font=f_sub, fill=(56, 189, 248, 255))

    # Segmented chapter bar at bottom
    bar_left, bar_right = 80, W - 80
    bar_w = bar_right - bar_left
    gap = 10
    n_seg = max(1, total)
    seg_w = int((bar_w - gap * (n_seg - 1)) / n_seg)
    for s_i in range(n_seg):
        sx0 = bar_left + s_i * (seg_w + gap)
        sx1 = bar_right if s_i == n_seg - 1 else (sx0 + seg_w)
        if s_i < idx:
            fill_col, txt_col = (14, 116, 144, 240), (148, 163, 184, 230)
        elif s_i == idx:
            fill_col, txt_col = (236, 72, 153, 255), (255, 255, 255, 255)
        else:
            fill_col, txt_col = (30, 41, 59, 210), (148, 163, 184, 180)
        draw.rounded_rectangle((sx0, H - 46, sx1, H - 30), radius=6, fill=fill_col)
        if all_chapters and s_i < len(all_chapters):
            c_lbl = str(all_chapters[s_i].get("chapter_title") or f"Part {s_i+1}")[:18]
            draw.text((sx0 + 4, H - 72), c_lbl, font=f_seg, fill=txt_col)

    canvas.save(out_png)
    return out_png


def _sample_gameplay_frames(work_dir: str, needed: int, existing_count: int) -> List[str]:
    """Extracts distinct frames from local gameplay MP4s if scraped article images are scarce."""
    if needed <= 0:
        return []
    gp_dir = os.environ.get("GAMEPLAY_DIR", "").strip()
    if not gp_dir or not os.path.isdir(gp_dir):
        gp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gameplay")
    if not os.path.isdir(gp_dir):
        return []
    mp4s = [os.path.join(gp_dir, f) for f in sorted(os.listdir(gp_dir)) if f.lower().endswith(".mp4")]
    if not mp4s:
        return []
    out: List[str] = []
    for i in range(needed):
        src = mp4s[i % len(mp4s)]
        ts = 6 + (i * 11) % 45
        dst = os.path.join(work_dir, f"bg_gp_{existing_count + i}.jpg")
        try:
            r = subprocess.run(
                [FFMPEG, "-y", "-ss", str(ts), "-i", src, "-frames:v", "1", "-q:v", "4", dst],
                capture_output=True, timeout=8,
            )
            if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 4000:
                out.append(dst)
        except Exception:
            continue
    return out


def render_guide_thumbnail_jpg(
    title: str,
    out_jpg: str,
    brand_name: str = "PixelBreach",
    bg_image_path: Optional[str] = None,
) -> str:
    """Renders a clean 1280x720 high-CTR YouTube thumbnail with hero visual + bold 2-line hook."""
    W, H = 1280, 720
    canvas = Image.new("RGBA", (W, H), (10, 14, 26, 255))
    if bg_image_path and os.path.exists(bg_image_path):
        try:
            bg = Image.open(bg_image_path).convert("RGB")
            sc = max(W / bg.width, H / bg.height)
            bg = bg.resize((int(bg.width * sc), int(bg.height * sc)), Image.Resampling.LANCZOS)
            left = (bg.width - W) // 2
            top = (bg.height - H) // 2
            bg = bg.crop((left, top, left + W, top + H))
            canvas.paste(bg.convert("RGBA"), (0, 0))
        except Exception:
            pass

    # Left-to-right dark vignette for crisp text readability
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for x in range(0, W, 8):
        alpha = int(235 * max(0.28, 1.0 - (x / W) * 0.78))
        v_draw.rectangle([(x, 0), (x + 8, H)], fill=(8, 12, 24, alpha))
    canvas = Image.alpha_composite(canvas, vignette)
    draw = ImageDraw.Draw(canvas)

    # Top-left brand pill
    f_pill = _load_font(22, bold=True)
    pill_txt = f"@{brand_name}"
    pb = draw.textbbox((0, 0), pill_txt, font=f_pill)
    pw = (pb[2] - pb[0]) + 36
    draw.rounded_rectangle((64, 56, 64 + pw, 102), radius=14, fill=(6, 182, 212, 255))
    draw.text((82, 66), pill_txt, font=f_pill, fill=(9, 14, 26, 255))

    # Giant 2-3 line bold headline
    clean_t = re.sub(r"#\S+", "", (title or "GTA 6 Guide")).strip()
    f_hero = _load_font(66, bold=True)
    lines = _wrap_text(draw, clean_t, f_hero, 780)[:3]
    total_h = len(lines) * 82
    ty = max(140, (H - total_h) // 2 + 10)
    draw.rectangle((64, ty - 22, 220, ty - 14), fill=(236, 72, 153, 255))
    for i, ln in enumerate(lines):
        col = (56, 189, 248, 255) if i == len(lines) - 1 and len(lines) > 1 else (248, 250, 252, 255)
        draw.text((64 + 3, ty + 3), ln, font=f_hero, fill=(0, 0, 0, 220))
        draw.text((64, ty), ln, font=f_hero, fill=col)
        ty += 82

    canvas.convert("RGB").save(out_jpg, quality=92)
    return out_jpg


def render_guide_card_png(
    chapter: Dict,
    out_png: str,
    brand_name: str,
    idx: int,
    total: int,
    bg_image_path: Optional[str] = None,
    active_step: Optional[int] = None,
    all_chapters: Optional[List[Dict]] = None,
    start_ts: str = "00:00",
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
    header_right = f"@{brand_name}  •  {step_txt}"
    hr_box = draw.textbbox((0, 0), header_right, font=f_brand)
    hr_w = hr_box[2] - hr_box[0]
    draw.text((W - 144 - hr_w, 142), header_right, font=f_brand, fill=(148, 163, 184, 255))

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
            val_txt = f"{val}%"
            vb = draw.textbbox((0, 0), val_txt, font=f_sub)
            vw = vb[2] - vb[0]
            draw.text((144, sy), lbl, font=f_sub, fill=(226, 232, 240, 255))
            draw.text((W - 154 - vw, sy), val_txt, font=f_sub, fill=(56, 189, 248, 255))
            bar_y = sy + 48
            draw.rounded_rectangle((144, bar_y, W - 154, bar_y + 26), radius=13, fill=(30, 41, 59, 255))
            fill_w = int((W - 298) * (val / 100.0))
            draw.rounded_rectangle((144, bar_y, 144 + max(26, fill_w), bar_y + 26), radius=13, fill=(56, 189, 248, 255))
            sy += 112

    elif ctype == "compare":
        do_items = (chapter.get("do_list") or chapter.get("bullets") or ["Prioritize core upgrades first"])[:3]
        avoid_items = (chapter.get("avoid_list") or ["Don't waste early cash on cosmetics"])[:3]
        col_w = 770
        max_col_y = H - 180
        do_outline = (52, 211, 153, 255) if active_step in (None, 0) else (16, 185, 129, 90)
        do_fill = (6, 78, 59, 140) if active_step == 0 else (6, 78, 59, 95)
        avoid_outline = (251, 113, 133, 255) if active_step in (None, 1) else (244, 63, 94, 90)
        avoid_fill = (127, 29, 29, 140) if active_step == 1 else (127, 29, 29, 95)
        # Left DO box
        draw.rounded_rectangle((144, content_top, 144 + col_w, H - 150), radius=24, fill=do_fill, outline=do_outline, width=3 if active_step == 0 else 2)
        draw.text((180, content_top + 26), "DO THIS", font=f_sub, fill=(52, 211, 153, 255))
        dy = content_top + 90
        for item in do_items:
            for ln in _wrap_text(draw, f"+ {item}", f_body, col_w - 72)[:2]:
                if dy + 40 > max_col_y:
                    break
                draw.text((180, dy), ln, font=f_body, fill=(236, 253, 245, 255))
                dy += 42
            dy += 22

        # Right AVOID box
        rx = 144 + col_w + 60
        draw.rounded_rectangle((rx, content_top, rx + col_w, H - 150), radius=24, fill=avoid_fill, outline=avoid_outline, width=3 if active_step == 1 else 2)
        draw.text((rx + 36, content_top + 26), "AVOID THIS", font=f_sub, fill=(251, 113, 133, 255))
        ay = content_top + 90
        for item in avoid_items:
            for ln in _wrap_text(draw, f"- {item}", f_body, col_w - 72)[:2]:
                if ay + 40 > max_col_y:
                    break
                draw.text((rx + 36, ay), ln, font=f_body, fill=(255, 241, 242, 255))
                ay += 42
            ay += 22

    else:  # "step"
        bullets = (chapter.get("bullets") or [chapter.get("chapter_title") or "Key Takeaway"])[:3]
        by = content_top + 8
        for b_i, b_txt in enumerate(bullets):
            box_h = 128
            is_active = active_step is None or b_i == active_step
            box_fill = (30, 58, 95, 220) if (active_step is not None and is_active) else ((30, 41, 59, 190) if is_active else (20, 27, 42, 140))
            box_out = (56, 189, 248, 255) if (active_step is not None and is_active) else ((71, 85, 105, 180) if is_active else (51, 65, 85, 100))
            txt_col = (248, 250, 252, 255) if is_active else (148, 163, 184, 200)
            draw.rounded_rectangle((144, by, 144 + left_max_w, by + box_h), radius=20, fill=box_fill, outline=box_out, width=3 if (active_step is not None and is_active) else 2)
            draw.rounded_rectangle((168, by + 34, 224, by + 90), radius=14, fill=(236, 72, 153, 255) if is_active else (100, 116, 139, 180))
            draw.text((186, by + 44), str(b_i + 1), font=f_sub, fill=(255, 255, 255, 255))
            b_lines = _wrap_text(draw, str(b_txt), f_body, left_max_w - 130)[:2]
            ty = by + (38 if len(b_lines) == 1 else 22)
            for ln in b_lines:
                draw.text((248, ty), ln, font=f_body, fill=txt_col)
                ty += 40
            by += box_h + 24

        if has_inset and bg_image_path:
            try:
                inset = Image.open(bg_image_path).convert("RGBA")
                max_iw, max_ih = 600, 420
                sc = min(max_iw / inset.width, max_ih / inset.height)
                iw, ih = max(1, int(round(inset.width * sc))), max(1, int(round(inset.height * sc)))
                inset = inset.resize((iw, ih), Image.Resampling.LANCZOS)
                mask = Image.new("L", (iw, ih), 0)
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, iw - 1, ih - 1), radius=16, fill=255)
                bullets_h = len(bullets) * 128 + max(0, len(bullets) - 1) * 24
                ix = (W - 144) - iw
                iy = content_top + 8 + max(0, (bullets_h - ih) // 2)
                draw.rounded_rectangle((ix - 5, iy - 5, ix + iw + 5, iy + ih + 5), radius=20, fill=(56, 189, 248, 255))
                canvas.paste(inset, (ix, iy), mask)
            except Exception:
                pass

    # 6. YouTube-Style Segmented Chapter Timeline Bar inside Video Frame
    draw = ImageDraw.Draw(canvas)
    bar_left, bar_right = 110, W - 110
    bar_w = bar_right - bar_left
    gap = 10
    n_seg = max(1, total)
    seg_w = int((bar_w - gap * (n_seg - 1)) / n_seg)
    f_seg = _load_font(18, bold=True)

    footer_txt = f"[{start_ts}]  CHAPTER {idx + 1}/{total}: {str(chapter.get('chapter_title', '')).upper()}"
    while len(footer_txt) > 12 and (draw.textbbox((0, 0), footer_txt, font=f_small)[2] - draw.textbbox((0, 0), footer_txt, font=f_small)[0]) > (W - 288):
        footer_txt = footer_txt[:-4].rstrip() + "..."
    draw.text((144, H - 140), footer_txt, font=f_small, fill=(56, 189, 248, 255))

    for s_i in range(n_seg):
        sx0 = bar_left + s_i * (seg_w + gap)
        sx1 = bar_right if s_i == n_seg - 1 else (sx0 + seg_w)
        if s_i < idx:
            fill_col = (14, 116, 144, 240)
            txt_col = (148, 163, 184, 230)
        elif s_i == idx:
            fill_col = (236, 72, 153, 255)
            txt_col = (255, 255, 255, 255)
        else:
            fill_col = (30, 41, 59, 220)
            txt_col = (100, 116, 139, 210)
        draw.rounded_rectangle((sx0, H - 56, sx1, H - 38), radius=6, fill=fill_col)
        if all_chapters and s_i < len(all_chapters):
            c_lbl = str(all_chapters[s_i].get("chapter_title") or f"Part {s_i+1}")[:18]
            draw.text((sx0 + 4, H - 82), c_lbl, font=f_seg, fill=txt_col)

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
        ass_path = os.path.join(work_dir, f"ch_{idx}.ass")
        seg_mp4 = os.path.join(work_dir, f"seg_{idx}.mp4")

        words = await generate_voice(narration, mp3_path, voice=voice, rate="+3%", brand_name=brand_name)
        dur = max(10.0, get_audio_duration(mp3_path))
        cur_ts = _fmt_ts(elapsed)
        chapter_timestamps.append(f"{cur_ts} - {ch.get('chapter_title', f'Chapter {idx+1}')}")
        elapsed += dur

        bg_pick = bg_imgs[idx % len(bg_imgs)] if bg_imgs else None
        if idx == 0:
            try:
                await asyncio.to_thread(
                    render_guide_thumbnail_jpg,
                    blueprint.get("title") or ch.get("headline") or "GTA 6 Guide",
                    thumb_jpg,
                    brand_name,
                    bg_pick,
                )
            except Exception:
                pass

        if words:
            build_16x9_ass_subtitles(words, ass_path)

        ctype = (ch.get("card_type") or "editorial").lower()
        if ctype in ("editorial", "broll", "step"):
            backdrop_jpg = os.path.join(work_dir, f"backdrop_{idx}.jpg")
            hud_png = os.path.join(work_dir, f"hud_{idx}.png")
            await asyncio.to_thread(render_editorial_backdrop_jpg, backdrop_jpg, bg_pick, idx)
            await asyncio.to_thread(render_editorial_hud_png, ch, hud_png, brand_name, idx, total, chapters, cur_ts)

            frames = max(300, int(dur * 30) + 15)
            move_mode = idx % 4
            if move_mode == 0:
                zp = f"zoompan=z='min(zoom+0.0006,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"
            elif move_mode == 1:
                zp = f"zoompan=z='max(1.12-0.0006*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"
            elif move_mode == 2:
                zp = f"zoompan=z='1.10':x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"
            else:
                zp = f"zoompan=z='1.10':x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps=30"

            fade_out_st = max(0.2, dur - 0.35)
            ass_esc = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
            ass_filter = f",subtitles='{ass_esc}'" if words and os.path.exists(ass_path) else ""
            fc = (
                f"[0:v]scale=2240:1260,{zp},setsar=1[bg];"
                f"[bg][1:v]overlay=0:0:eof_action=repeat{ass_filter},"
                f"fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out_st:.2f}:d=0.35,format=yuv420p[vout]"
            )
            cmd = [
                FFMPEG, "-y", "-threads", "2",
                "-i", backdrop_jpg,
                "-i", hud_png,
                "-i", mp3_path,
                "-filter_complex", fc,
                "-map", "[vout]", "-map", "2:a",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
                "-t", f"{dur:.2f}",
                seg_mp4,
            ]
        else:
            step_count = 2 if ctype == "compare" else max(1, min(3, len(ch.get("bullets") or [])))
            frame_pngs: List[str] = []
            for s_i in range(step_count):
                p_png = os.path.join(work_dir, f"ch_{idx}_{s_i}.png")
                await asyncio.to_thread(
                    render_guide_card_png, ch, p_png, brand_name, idx, total, bg_pick,
                    s_i if step_count > 1 else None, chapters, cur_ts,
                )
                frame_pngs.append(p_png)

            fade_out_st = max(0.2, dur - 0.35)
            vf = f"scale=1920:1080,fps=30,fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out_st:.2f}:d=0.35,format=yuv420p"
            if len(frame_pngs) > 1:
                img_list_path = os.path.join(work_dir, f"img_concat_{idx}.txt")
                slice_dur = dur / len(frame_pngs)
                with open(img_list_path, "w", encoding="utf-8") as ilf:
                    for fp in frame_pngs:
                        ilf.write(f"file '{os.path.abspath(fp).replace(chr(92), '/')}'\n")
                        ilf.write(f"duration {slice_dur:.3f}\n")
                    ilf.write(f"file '{os.path.abspath(frame_pngs[-1]).replace(chr(92), '/')}'\n")
                v_inputs = ["-f", "concat", "-safe", "0", "-i", img_list_path]
            else:
                v_inputs = ["-i", frame_pngs[0]]

            cmd = [
                FFMPEG, "-y", "-threads", "2",
                *v_inputs,
                "-i", mp3_path,
                "-vf", vf,
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
                "-t", f"{dur:.2f}",
                seg_mp4,
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
