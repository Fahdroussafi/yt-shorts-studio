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
                if not any(k in low_t for k in ("gta", "grand theft auto", "vice city")):
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
            "voice": "en-US-BrianNeural",
            "visual_mode": "parkour_brainrot",
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

    art = random.choice(articles[:8])
    body = art["body"]
    if len(body) < 350 and art.get("link"):
        fetched = _fetch_article_paragraphs(art["link"])
        if len(fetched) > len(body):
            body = fetched

    script = extract_extractive_script(art["title"], body, brand_name=brand_name)

    # Trim title cleanly under 58 chars for mobile Shorts feed
    words = art["title"].split()
    short_head = ""
    for w in words:
        if len(short_head) + len(w) + 1 > 43:
            break
        short_head = f"{short_head} {w}".strip()
    yt_title = f"{short_head} #shorts #gta6"

    if topic_history_file:
        record_topic_history(topic_history_file, yt_title, "gta6_launch", art["title"])

    return {
        "title": yt_title,
        "script": script,
        "keywords": ["gaming-console", "miami-night", "neon-city", "sports-car"],
        "search_tags": ["gta 6 news", "gta vi", "gta 6 update", "gta 6 release", "gaming shorts"],
        "description": f"{art['title']} (Source: {art['outlet']} — {art['link']}). Subscribe to {brand_handle} #shorts #gta6 #gtavi #gaming",
        "pinned_comment": "Are you ready for launch day? Drop your console below.",
        "voice": "en-US-ChristopherNeural",
        "visual_mode": "parkour_brainrot",
        "source": f"rss_{art['outlet'].lower().replace(' ', '_')}_zero_ai",
    }
