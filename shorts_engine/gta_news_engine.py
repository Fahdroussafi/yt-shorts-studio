import re
import html as html_lib
import random
import requests
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Tuple

RSS_SOURCES = [
    ("RockstarINTEL", "https://rockstarintel.com/feed/"),
    ("Insider Gaming", "https://insider-gaming.com/feed/"),
    ("Eurogamer", "https://www.eurogamer.net/feed"),
    ("IGN", "https://feeds.feedburner.com/ign/games-all"),
    ("GamesRadar", "https://www.gamesradar.com/rss/"),
]

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "it",
    "its", "this", "that", "these", "those", "they", "them", "their", "you", "your", "we",
    "our", "as", "into", "about", "more", "also", "just", "now", "than", "then", "when",
}

BOILERPLATE_PHRASES = (
    "newsletter", "subscribe", "commission", "affiliate", "pre-order", "preorder",
    "appeared first on", "the post ", "sign up", "follow us", "click here", "read more",
    "check out our", "for more news", "thank you!", "privacy policy", "cookie",
    "image credit", "screenshot:", "watch the trailer below", "let us know in the comments",
    "look no further", "that's all you need", "thats all you need", "here are the steps",
    "super handy", "time zone breakdown", "learn how to", "trying to figure out how to",
)


def _strip_html(raw: str) -> str:
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html_lib.unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def _fetch_article_paragraphs(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
        if r.status_code != 200:
            return ""
        blocks = re.findall(r"<(?:p|li)[^>]*>(.*?)</(?:p|li)>", r.text, flags=re.DOTALL | re.IGNORECASE)
        cleaned = []
        for p in blocks:
            t = _strip_html(p)
            low = t.lower()
            if len(t) >= 25 and not any(bp in low for bp in BOILERPLATE_PHRASES):
                cleaned.append(t if t.endswith((".", "!", "?")) else t + ".")
        return " ".join(cleaned[:16])
    except Exception:
        return ""


_BAD_IMG_TOKENS = (
    "avatar", "logo", "icon", "gravatar", "300x169", "150x150", "400x400",
    "svg", "pixel", "doubleclick", "author", "profile", "adchoices",
    "newsletter", "badge", "emoji", "favicon", "spinner", "placeholder",
)


def _norm_img_key(url: str) -> str:
    base = url.split("?")[0].lower()
    base = re.sub(r"-\d+x\d+(?=\.\w+$)", "", base)
    base = re.sub(r"-\d+-\d+(?=\.\w+$)", "", base)
    return re.sub(r"-scaled(?=\.\w+$)", "", base)


def scrape_article_media(url: str, max_items: int = 8) -> List[str]:
    """Extracts unique high-res article images and direct mp4/webm videos from a news page."""
    if not url:
        return []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
        if r.status_code != 200:
            return []
        page = r.text
    except Exception:
        return []

    art_m = re.search(r"<article\b[^>]*>(.*?)</article>", page, re.I | re.S)
    scope = art_m.group(1) if art_m else page

    videos = []
    for v in re.findall(r'https?://[^"\'\s<>]+\.(?:mp4|webm)(?:\?[^"\'\s<>]*)?', scope, re.I):
        if v not in videos:
            videos.append(v)

    og_imgs = re.findall(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        page, re.I,
    )
    raw_imgs = re.findall(
        r'<img[^>]+(?:src|data-src|data-lazy-src)=["\'](https?://[^"\']+)["\']',
        scope, re.I,
    )

    seen_keys = set()
    images = []
    for raw in og_imgs + raw_imgs:
        u = html_lib.unescape(raw).strip()
        low = u.lower()
        if not low.startswith("http") or any(b in low for b in _BAD_IMG_TOKENS):
            continue
        key = _norm_img_key(u)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        images.append(u)

    return (videos + images)[:max_items]


def _split_clean_sentences(text: str) -> List[str]:
    # Protect common abbreviations / decimals before splitting
    safe = re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", text)
    parts = re.split(r"(?<=[.!?])\s+", safe)
    out = []
    for s in parts:
        s = s.replace("<DOT>", ".").strip()
        s = re.sub(r"https?://\S+", "", s).strip()
        low = s.lower()
        if not s or s.endswith(":") or any(bp in low for bp in BOILERPLATE_PHRASES):
            continue
        # Drop robotic multi-dot version codes like 1.002.001
        if re.search(r"\b\d+\.\d+\.\d+\b", s):
            continue
        words = s.split()
        if 6 <= len(words) <= 32:
            out.append(s)
    return out


def extract_extractive_script(
    headline: str,
    body_text: str,
    brand_name: str = "PixelBreach",
    target_words: int = 80,
) -> str:
    """Pure-Python extractive summarizer: ranks sentences by headline overlap + facts, zero AI."""
    sentences = _split_clean_sentences(body_text)
    if not sentences:
        clean_h = headline.rstrip(" .!?")
        return f"{clean_h}. Follow {brand_name} for more."

    headline_tokens = {
        re.sub(r"[^a-z0-9]", "", w.lower())
        for w in headline.split()
        if len(w) > 2
    } - STOPWORDS

    # Compute word frequencies across body for TF weighting
    freq: Dict[str, int] = {}
    for s in sentences:
        for w in s.split():
            tok = re.sub(r"[^a-z0-9]", "", w.lower())
            if len(tok) > 2 and tok not in STOPWORDS:
                freq[tok] = freq.get(tok, 0) + 1

    scored: List[Tuple[int, float, str]] = []
    for idx, s in enumerate(sentences):
        tokens = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in s.split()]
        tokens = [t for t in tokens if len(t) > 2 and t not in STOPWORDS]
        if not tokens:
            continue
        tf_score = sum(freq.get(t, 0) for t in tokens) / len(tokens)
        hl_overlap = len(set(tokens) & headline_tokens) * 2.5
        has_number = 1.8 if re.search(r"\b\d+(\.\d+)?\s*(%|gb|mb|fps|hours|days|million|billion)?\b", s.lower()) else 0.0
        pos_bonus = max(0.0, 2.5 - idx * 0.25)
        scored.append((idx, tf_score + hl_overlap + has_number + pos_bonus, s))

    # Pick top-scoring sentences up to ~target_words, then restore original chronological order
    scored.sort(key=lambda x: x[1], reverse=True)
    chosen = []
    word_total = len(headline.split()) + 6
    for idx, _sc, s in scored:
        wlen = len(s.split())
        if chosen and word_total + wlen > target_words + 15:
            continue
        chosen.append((idx, s))
        word_total += wlen
        if word_total >= target_words or len(chosen) >= 4:
            break

    chosen.sort(key=lambda x: x[0])
    clean_h = headline.rstrip(" .!?")
    body_part = " ".join(s for _, s in chosen)
    # Avoid duplicating headline if first chosen sentence already says it verbatim
    if chosen and clean_h.lower()[:25] in chosen[0][1].lower():
        script = f"{body_part} Follow {brand_name} for more."
    else:
        script = f"{clean_h}. {body_part} Follow {brand_name} for more."
    return re.sub(r"\s+", " ", script).strip()


def fetch_gta_articles(topic_filter: Optional[str] = None, used_titles: Optional[set] = None) -> List[Dict]:
    """Fetches live GTA 6 / GTA articles from 5 verified gaming RSS outlets."""
    used_titles = used_titles or set()
    articles = []
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}

    for outlet, url in RSS_SOURCES:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.text)
            for it in root.findall(".//item")[:20]:
                title = html_lib.unescape((it.findtext("title") or "").strip())
                low_t = title.lower()
                if not any(k in low_t for k in ("gta 6", "gta vi", "grand theft auto 6", "grand theft auto vi")):
                    continue
                if not topic_filter and any(skip in low_t for skip in ("time zone", "countdown", "pre-order", "preorder", "explained")):
                    continue
                if low_t in used_titles:
                    continue
                if topic_filter and topic_filter.lower() not in low_t:
                    continue

                link = (it.findtext("link") or "").strip()
                raw_body = it.findtext("content:encoded", default="", namespaces=ns) or it.findtext("description", default="")
                clean_body = _strip_html(raw_body)
                articles.append({
                    "outlet": outlet,
                    "title": title,
                    "link": link,
                    "body": clean_body,
                })
        except Exception:
            continue

    return articles


BAD_SCRIPT_REFS = (
    "below", "above", "the table", "following steps", "click ", "gallery",
    "this guide", "these steps", "as mentioned", "watch the video",
)
DANGLING_STARTS = (
    "however,", "however ", "also,", "also ", "additionally,", "meanwhile,",
    "with that said", "on top of that", "that's why", "furthermore,",
)


def _is_good_script(script: str, headline: str, brand_name: str) -> Tuple[bool, str]:
    """Deterministic quality gate: rejects thin, broken, dangling, or reference-heavy scripts."""
    words = script.split()
    if len(words) < 55 or len(words) > 125:
        return False, f"word count {len(words)} out of bounds"

    low = script.lower()
    if any(ref in low for ref in BAD_SCRIPT_REFS):
        return False, "contains visual/page reference ('below', 'table', 'this guide')"

    body_only = script.replace(f"Follow {brand_name} for more.", "").strip()
    if body_only.lower().startswith(headline.rstrip(" .!?").lower()):
        body_only = body_only[len(headline.rstrip(" .!?")):].lstrip(" .!?")

    body_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body_only) if len(s.split()) >= 5]
    if len(body_sents) < 2:
        return False, "too few body sentences"

    if body_sents[0].lower().startswith(DANGLING_STARTS):
        return False, f"dangling opener '{body_sents[0][:25]}'"

    has_fact = bool(re.search(
        r"\b(\d+|ps5|xbox|pc|rockstar|vice city|lucia|jason|trailer|update|patch|gb|fps|hours)\b",
        body_only.lower(),
    ))
    if not has_fact:
        return False, "no concrete entity or number in body"

    return True, "ok"


def generate_zero_ai_gta_script(
    concept: Optional[str] = None,
    brand_name: str = "PixelBreach",
    brand_handle: str = "@PixelBreach-y6",
    topic_history_file: Optional[str] = None,
) -> Dict:
    """Builds a factual 30s GTA 6 Short script purely algorithmically from real RSS news or pasted text."""
    from idea_bank import load_topic_history, record_topic_history

    history = load_topic_history(topic_history_file)
    used_titles = set()
    for e in history:
        for k in ("angle", "concept", "title"):
            val = str(e.get(k, "")).strip().lower()
            if val:
                used_titles.add(val)

    # Case 1: User pasted source text (>120 chars) -> extractive summarize directly, zero AI
    if concept and len(concept.strip()) > 120:
        raw = concept.strip()
        first_line = raw.splitlines()[0][:80].strip()
        script = extract_extractive_script(first_line, raw, brand_name=brand_name)
        short_title = re.sub(r"\s+", " ", first_line)[:42].rstrip(" .,:;-") + " #shorts #gta6"
        return {
            "title": short_title,
            "script": script,
            "keywords": ["gaming-console", "miami-night", "neon-city", "sports-car"],
            "search_tags": ["gta 6 news", "gta vi", "gta 6 update", "gaming shorts"],
            "description": f"{first_line}. Subscribe to {brand_handle} #shorts #gta6 #gtavi #gaming",
            "pinned_comment": "What do you think about this? Drop your take below.",
            "voice": "en-US-AndrewMultilingualNeural",
            "visual_mode": "parkour_brainrot",
            "media_urls": [],
            "source": "extractive_zero_ai",
        }

    # Case 2: Fetch real unread GTA 6 news from IGN / Eurogamer / Insider Gaming / GamesRadar / RockstarINTEL
    topic_filter = concept.strip() if concept and concept.strip() else None
    articles = fetch_gta_articles(topic_filter=topic_filter, used_titles=used_titles)
    if not articles and topic_filter:
        articles = fetch_gta_articles(topic_filter=None, used_titles=used_titles)
    if not articles:
        articles = fetch_gta_articles(topic_filter=None, used_titles=set())

    if not articles:
        raise RuntimeError("No live GTA articles reachable from RSS feeds right now.")

    pool = list(articles[:15])
    random.shuffle(pool)

    art = None
    script = ""
    for cand in pool:
        body = cand["body"]
        if len(body) < 350 and cand.get("link"):
            fetched = _fetch_article_paragraphs(cand["link"])
            if len(fetched) > len(body):
                body = fetched
        cand_script = extract_extractive_script(cand["title"], body, brand_name=brand_name)
        ok, reason = _is_good_script(cand_script, cand["title"], brand_name)
        if ok:
            art = cand
            script = cand_script
            break
        print(f"Skipped '{cand['title'][:45]}': {reason}")

    if not art:
        art = pool[0]
        body = art["body"]
        if len(body) < 350 and art.get("link"):
            fetched = _fetch_article_paragraphs(art["link"])
            if len(fetched) > len(body):
                body = fetched
        script = extract_extractive_script(art["title"], body, brand_name=brand_name)

    # Build clean title without mid-phrase chopping (up to 65 chars + #shorts #gta6)
    base_title = re.split(r"\s*[—–|:]\s*", art["title"].strip())[0]
    if len(base_title) < 20:
        base_title = art["title"].strip()
    words = base_title.split()
    short_head = ""
    for w in words:
        if len(short_head) + len(w) + 1 > 65:
            break
        short_head = f"{short_head} {w}".strip()
    dangling_end = {"a", "an", "the", "as", "to", "for", "of", "in", "on", "with", "and", "or", "by", "at", "grand"}
    head_words = short_head.split()
    while len(head_words) > 3 and head_words[-1].lower().strip(",.-:") in dangling_end:
        head_words.pop()
    yt_title = f"{' '.join(head_words)} #shorts #gta6"

    if topic_history_file:
        record_topic_history(topic_history_file, yt_title, "gta6_launch", art["title"])

    media_urls = scrape_article_media(art.get("link", ""))

    return {
        "title": yt_title,
        "script": script,
        "keywords": ["gaming-console", "miami-night", "neon-city", "sports-car"],
        "search_tags": ["gta 6 news", "gta vi", "gta 6 update", "gta 6 release", "gaming shorts"],
        "description": f"{art['title']} (Source: {art['outlet']} — {art['link']}). Subscribe to {brand_handle} #shorts #gta6 #gtavi #gaming",
        "pinned_comment": "Are you ready for launch day? Drop your console below.",
        "voice": "en-US-AndrewMultilingualNeural",
        "visual_mode": "parkour_brainrot",
        "media_urls": media_urls,
        "source": f"rss_{art['outlet'].lower().replace(' ', '_')}_zero_ai",
    }
