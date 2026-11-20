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
    target_words: int = 50,
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

    # Pick top-scoring sentences up to ~target_words (~18-24s spoken), then restore chronological order
    scored.sort(key=lambda x: x[1], reverse=True)
    chosen = []
    word_total = len(headline.split()) + 6
    for idx, _sc, s in scored:
        wlen = len(s.split())
        if chosen and word_total + wlen > target_words + 12:
            continue
        chosen.append((idx, s))
        word_total += wlen
        if word_total >= target_words or len(chosen) >= 2:
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


_STRIKE_RISK_TERMS = (
    "leak", "leaks", "leaker", "leaked build", "leek", "cyberleek",
    "datamined", "datamine", "play early", "early access download",
    "free download", "crack", "piracy", "mod menu", "money glitch",
    "afk bot", "duplication glitch",
)

_OFF_TOPIC_TERMS = (
    "nba", "2k27", "2k26", "fortnite", "discord", "politician",
    "conservative", "labour", "parliament", "prime minister", "badenoch",
    "trump", "biden", "election", "stocks", "share price", "investor",
    "earnings", "gta online", "event week", "shark card", "cosmetics",
    "skin pack", "time zone", "countdown", "pre-order", "preorder", "explained",
)

_HIGH_VALUE_TERMS = (
    "gameplay", "map", "vice city", "leonida", "lucia", "jason",
    "mission", "wanted", "weapon", "car", "vehicle", "secret",
    "easter egg", "mechanic", "ps5", "xbox", "screenshot", "trailer",
    "detail", "feature", "weather", "physics", "tips", "guide",
)


def _article_relevance_score(title: str) -> int:
    low = title.lower()
    return sum(2 for term in _HIGH_VALUE_TERMS if term in low)


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
                if any(term in low_t for term in _STRIKE_RISK_TERMS):
                    continue
                if not topic_filter and any(skip in low_t for skip in _OFF_TOPIC_TERMS):
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
                    "score": _article_relevance_score(title),
                })
        except Exception:
            continue

    articles.sort(key=lambda a: a.get("score", 0), reverse=True)
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
    if len(words) < 35 or len(words) > 78:
        return False, f"word count {len(words)} out of bounds"

    low = script.lower()
    if any(ref in low for ref in BAD_SCRIPT_REFS):
        return False, "contains visual/page reference ('below', 'table', 'this guide')"

    body_only = script.replace(f"Follow {brand_name} for more.", "").strip()
    if body_only.lower().startswith(headline.rstrip(" .!?").lower()):
        body_only = body_only[len(headline.rstrip(" .!?")):].lstrip(" .!?")

    body_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body_only) if len(s.split()) >= 5]
    if len(body_sents) < 1:
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


_DANGLING_END_WORDS = {
    "a", "an", "the", "as", "to", "for", "of", "in", "on", "with", "and", "or",
    "by", "at", "is", "are", "was", "were", "your", "its", "their", "here's",
    "heres", "ahead", "more", "much", "about", "highlighting", "reportedly", "grand",
}


def _strip_unbalanced_quotes(text: str) -> str:
    for q in ('"', "'", "“", "”", "‘", "’"):
        if text.count(q) % 2 == 1:
            text = text.replace(q, "")
    return re.sub(r"\s+", " ", text).strip()


def _clean_phrase_limit(text: str, max_chars: int = 48, min_words: int = 3) -> str:
    base = re.split(r"\s*[—–|]\s*", (text or "").strip())[0]
    base = re.sub(r"#\S+", "", base)
    base = _strip_unbalanced_quotes(base).strip(" .,:;-!?")
    words = base.split()
    out: List[str] = []
    for w in words:
        cand = f"{' '.join(out)} {w}".strip()
        if len(cand) > max_chars:
            break
        out.append(w)
    while len(out) > min_words and out[-1].lower().strip(",.-:!?()") in _DANGLING_END_WORDS:
        out.pop()
    return " ".join(out).strip(" .,:;-")


def _clean_short_title_and_banner(raw_title: str) -> Tuple[str, str]:
    clean_head = _clean_phrase_limit(raw_title, max_chars=48, min_words=3)
    if not clean_head:
        clean_head = "GTA 6 Major Update"
    yt_title = f"{clean_head} #shorts #gta6"
    banner = _clean_phrase_limit(clean_head, max_chars=28, min_words=2).upper()
    if len(banner.split()) < 2:
        banner = "GTA 6 UPDATE"
    return yt_title, banner


def _rewrite_gta_short_with_groq(
    headline: str,
    body_text: str,
    brand_name: str,
    user_key_file: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    """Rewrites raw RSS headline/body into punchy 18-24s spoken Shorts script + non-chopped title & banner."""
    try:
        from gemini_generator import get_groq_key, generate_with_groq_lpu
        g_key = get_groq_key(user_key_file, allow_fallback=True)
        if not g_key:
            return None
        snippet = re.sub(r"\s+", " ", body_text or "").strip()[:1200]
        prompt = (
            f'Turn this GTA 6 news article into a punchy 20-second YouTube Short.\n'
            f'Headline: {headline}\n'
            f'Facts: {snippet}\n\n'
            f'Rules:\n'
            f'- hook_banner: ALL CAPS 3-5 words, <= 28 chars, complete phrase, NO cutoffs.\n'
            f'- title: Complete catchy title <= 48 chars (NO hashtags, NO cut-off words, NO unbalanced quotes).\n'
            f'- script: 45-58 words total, spoken punchy style: 1-line hook, 2 concrete facts, end with "Follow {brand_name} for more."\n'
            f'Respond ONLY with JSON: {{"hook_banner":"...","title":"...","script":"..."}}'
        )
        res = generate_with_groq_lpu(prompt, g_key)
        if not isinstance(res, dict):
            return None
        hook = _clean_phrase_limit((res.get("hook_banner") or "").upper(), max_chars=28, min_words=2).upper()
        title_clean = _clean_phrase_limit(res.get("title") or "", max_chars=48, min_words=3)
        script_clean = re.sub(r"\s+", " ", (res.get("script") or "").strip())
        if len(script_clean.split()) < 30 or not title_clean or len(hook.split()) < 2:
            return None
        if brand_name.lower() not in script_clean.lower():
            script_clean = script_clean.rstrip(" .,!?") + f". Follow {brand_name} for more."
        return {
            "hook_banner": hook,
            "title": f"{title_clean} #shorts #gta6",
            "script": script_clean,
        }
    except Exception:
        return None


def generate_zero_ai_gta_script(
    concept: Optional[str] = None,
    brand_name: str = "PixelBreach",
    brand_handle: str = "@PixelBreach-y6",
    topic_history_file: Optional[str] = None,
    user_key_file: Optional[str] = None,
) -> Dict:
    """Builds a punchy ~20s GTA 6 Short script from real RSS news or pasted text."""
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
        short_title, hook_banner = _clean_short_title_and_banner(first_line)
        return {
            "title": short_title,
            "hook_banner": hook_banner,
            "script": script,
            "keywords": ["gaming-console", "miami-night", "neon-city", "sports-car"],
            "search_tags": ["gta 6 news", "gta vi", "gta 6 update", "gaming shorts"],
            "description": f"{first_line}. Subscribe to {brand_handle} #shorts #gta6 #gtavi #gaming",
            "pinned_comment": "What do you think about this? Drop your take below.",
            "voice": "en-US-AndrewMultilingualNeural",
            "visual_mode": "cinematic_cuts",
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

    # Prefer top-scored gameplay/detail articles first (small jitter within top 6)
    pool = list(articles[:6])
    random.shuffle(pool)
    pool.extend(articles[6:15])

    art = None
    script = ""
    best_body = ""
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
            best_body = body
            break
        print(f"Skipped '{cand['title'][:45]}': {reason}")

    if not art:
        art = pool[0]
        best_body = art["body"]
        if len(best_body) < 350 and art.get("link"):
            fetched = _fetch_article_paragraphs(art["link"])
            if len(fetched) > len(best_body):
                best_body = fetched
        script = extract_extractive_script(art["title"], best_body, brand_name=brand_name)

    rewritten = _rewrite_gta_short_with_groq(art["title"], best_body, brand_name, user_key_file=user_key_file)
    if rewritten:
        yt_title = rewritten["title"]
        hook_banner = rewritten["hook_banner"]
        script = rewritten["script"]
        source_tag = f"rss_{art['outlet'].lower().replace(' ', '_')}_groq"
    else:
        yt_title, hook_banner = _clean_short_title_and_banner(art["title"])
        source_tag = f"rss_{art['outlet'].lower().replace(' ', '_')}_zero_ai"

    if topic_history_file:
        record_topic_history(topic_history_file, yt_title, "gta6_launch", art["title"])

    media_urls = scrape_article_media(art.get("link", ""))

    return {
        "title": yt_title,
        "hook_banner": hook_banner,
        "script": script,
        "keywords": ["gaming-console", "miami-night", "neon-city", "sports-car"],
        "search_tags": ["gta 6 news", "gta vi", "gta 6 update", "gta 6 release", "gaming shorts"],
        "description": f"{art['title']} (Source: {art['outlet']} — {art['link']}). Subscribe to {brand_handle} #shorts #gta6 #gtavi #gaming",
        "pinned_comment": "Are you ready for launch day? Drop your console below.",
        "voice": "en-US-AndrewMultilingualNeural",
        "visual_mode": "cinematic_cuts",
        "media_urls": media_urls,
        "source": source_tag,
    }
