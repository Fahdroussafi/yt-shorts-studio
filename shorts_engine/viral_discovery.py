import os
import re
import json
import time
import html as html_lib
import random
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, List, Dict

CACHE_TTL = 24 * 3600  # 24h cache so YouTube search.list costs at most 100 units/day per niche

NICHE_DISCOVERY_QUERIES = {
    "dark_psychology": {
        "yt": ["dark psychology tricks #shorts", "psychological manipulation facts #shorts"],
        "wiki": "cognitive bias OR psychological manipulation OR social psychology experiment",
        "rss": "psychology experiment OR cognitive bias OR manipulation behavior",
    },
    "dark_history": {
        "yt": ["forbidden history experiment #shorts", "dark psychology experiments #shorts"],
        "wiki": "unethical human experimentation OR psychological experiment history",
        "rss": "dark history experiment OR declassified study psychology",
    },
    "body_language": {
        "yt": ["body language tricks #shorts", "how to spot a liar body language #shorts"],
        "wiki": "body language OR microexpression OR nonverbal communication deception",
        "rss": "body language psychology OR deception detection cues",
    },
    "power_dynamics": {
        "yt": ["power dynamics psychology #shorts", "social dominance psychology #shorts"],
        "wiki": "Machiavellianism OR social dominance OR framing effect psychology",
        "rss": "social power dynamics OR persuasion psychology",
    },
    "dark_profiling": {
        "yt": ["dark personality traits #shorts", "narcissist tactics psychology #shorts"],
        "wiki": "dark triad OR gaslighting OR intermittent reinforcement psychology",
        "rss": "narcissism manipulation tactics OR dark triad psychology",
    },
}


def _used_set(history: list) -> set:
    used = set()
    for e in history or []:
        for k in ("angle", "concept", "title"):
            v = re.sub(r"#\S+", "", str(e.get(k, ""))).strip().lower()
            if v:
                used.add(v)
    return used


def _fetch_youtube_viral_shorts(niche: str, token_file: str) -> List[Dict]:
    """Fetches top-viewed YouTube Shorts for a niche, cached 24h to preserve quota."""
    cache_path = f"/tmp/viral_shorts_cache_{niche}.json" if os.name != "nt" else os.path.join(os.environ.get("TEMP", "."), f"viral_shorts_cache_{niche}.json")
    now = time.time()
    if os.path.exists(cache_path):
        try:
            cached = json.load(open(cache_path, "r", encoding="utf-8"))
            if now - cached.get("ts", 0) < CACHE_TTL and cached.get("items"):
                return cached["items"]
        except Exception:
            pass

    if not token_file or not os.path.exists(token_file):
        return []

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from googleapiclient.discovery import build

        tdata = json.load(open(token_file, "r", encoding="utf-8"))
        creds = Credentials.from_authorized_user_info(tdata)
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleAuthRequest())
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())

        yt = build("youtube", "v3", credentials=creds)
        queries = NICHE_DISCOVERY_QUERIES.get(niche, NICHE_DISCOVERY_QUERIES["dark_psychology"])["yt"]
        q = random.choice(queries)
        resp = yt.search().list(
            part="snippet",
            q=q,
            type="video",
            videoDuration="short",
            order="viewCount",
            relevanceLanguage="en",
            maxResults=25,
        ).execute()

        items = []
        for it in resp.get("items", []):
            sn = it.get("snippet", {})
            raw_title = html_lib.unescape(sn.get("title") or "").strip()
            clean_title = re.sub(r"#\S+", "", raw_title).strip(" -|:")
            desc = html_lib.unescape(sn.get("description") or "").strip()[:260]
            if len(clean_title) >= 12:
                items.append({"title": clean_title, "context": desc or clean_title, "source": "youtube_viral_shorts"})

        if items:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"ts": now, "items": items}, f, indent=2)
        return items
    except Exception as e:
        print(f"YouTube viral discovery note: {e}")
        return []


def _fetch_wiki_and_rss_topics(niche: str) -> List[Dict]:
    """Zero-quota fallback: real psychological phenomena, experiments, and research headlines."""
    cfg = NICHE_DISCOVERY_QUERIES.get(niche, NICHE_DISCOVERY_QUERIES["dark_psychology"])
    items: List[Dict] = []

    try:
        w = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": cfg["wiki"], "srlimit": 20, "format": "json"},
            headers={"User-Agent": "ShadowMindBot/1.0"},
            timeout=7,
        )
        if w.status_code == 200:
            for hit in w.json().get("query", {}).get("search", []):
                title = (hit.get("title") or "").strip()
                snippet = html_lib.unescape(re.sub(r"<[^>]+>", " ", hit.get("snippet") or "")).strip()
                if title and len(snippet) > 30:
                    items.append({"title": title, "context": snippet, "source": "wikipedia"})
    except Exception:
        pass

    try:
        q_rss = requests.utils.quote(cfg["rss"])
        r = requests.get(
            f"https://news.google.com/rss/search?q={q_rss}&hl=en-US&gl=US&ceid=US:en",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=7,
        )
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for it in root.findall(".//item")[:15]:
                t = html_lib.unescape((it.findtext("title") or "").strip())
                t = re.sub(r"\s+-\s+[^-]+$", "", t).strip()
                if len(t) >= 15:
                    items.append({"title": t, "context": t, "source": "google_news"})
    except Exception:
        pass

    return items


def discover_viral_angle(
    niche: str,
    history: list,
    token_file: Optional[str] = None,
) -> Optional[Tuple[str, str]]:
    """Finds an unused viral Short topic (YouTube 24h cache) or real study/phenomenon (Wiki/RSS)."""
    from idea_bank import find_duplicate_concept

    existing_items = [
        {"id": f"h_{i}", "title": str(e.get("title") or ""), "angle": str(e.get("angle") or e.get("concept") or "")}
        for i, e in enumerate(history or [])
        if isinstance(e, dict)
    ]

    yt_items = _fetch_youtube_viral_shorts(niche, token_file) if token_file else []
    fresh_yt = [it for it in yt_items if not find_duplicate_concept(it["title"], it.get("context", ""), existing_items)]
    if fresh_yt:
        pick = random.choice(fresh_yt[:12])
        return pick["title"], f"Trending viral YouTube Short topic: {pick['title']} ({pick['context']})"

    fallback_items = _fetch_wiki_and_rss_topics(niche)
    fresh_fb = [it for it in fallback_items if not find_duplicate_concept(it["title"], it.get("context", ""), existing_items)]
    if fresh_fb:
        pick = random.choice(fresh_fb[:15])
        return pick["title"], f"Real verified psychological/historical topic ({pick['source']}): {pick['title']} — {pick['context']}"

    return None


_BAD_WIKI_IMG = ("logo", "icon", "flag", "map", "diagram", "chart", "signature", "button", "arrow", "commons-logo")


def scrape_topic_media(topic_title: str, niche: str = "dark_psychology", max_images: int = 4) -> List[str]:
    """Scrapes real archival/documentary images from Wikimedia Commons & Wikipedia for ShadowMind topics."""
    clean_q = re.sub(r"#\S+", "", topic_title or "").strip()
    clean_q = re.sub(r"[^\w\s-]", " ", clean_q).strip()
    niche_q = NICHE_DISCOVERY_QUERIES.get(niche, NICHE_DISCOVERY_QUERIES["dark_psychology"])["wiki"]
    queries = [q for q in (clean_q[:80], niche_q) if q]

    urls: List[str] = []
    seen = set()
    for q in queries:
        if len(urls) >= max_images:
            break
        try:
            r = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrnamespace": 6,
                    "gsrsearch": q,
                    "gsrlimit": 12,
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime",
                    "format": "json",
                },
                headers={"User-Agent": "ShadowMindBot/1.0"},
                timeout=7,
            )
            if r.status_code != 200:
                continue
            pages = r.json().get("query", {}).get("pages", {})
            for p in pages.values():
                ii = (p.get("imageinfo") or [{}])[0]
                mime = (ii.get("mime") or "").lower()
                w = int(ii.get("width") or 0)
                h = int(ii.get("height") or 0)
                u = (ii.get("url") or "").strip()
                low = u.lower()
                if mime not in ("image/jpeg", "image/png", "image/webp"):
                    continue
                if w < 500 or h < 350 or any(b in low for b in _BAD_WIKI_IMG):
                    continue
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
                    if len(urls) >= max_images:
                        break
        except Exception:
            continue
    return urls[:max_images]
