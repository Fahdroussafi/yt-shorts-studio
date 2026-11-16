import os
import json
import random
import requests
import re
from typing import Optional, Dict, Tuple, Any

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "groq_api_key.txt")

def _ensure_env():
    if not os.environ.get("GROQ_API_KEY") and os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass

_ensure_env()

def get_groq_key(user_key_file: Optional[str] = None, allow_fallback: bool = False) -> Optional[str]:
    # 1. Check user-specific key file if provided
    if user_key_file and os.path.exists(user_key_file):
        try:
            with open(user_key_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass

    # 2. Allow fallback to env or global file if allow_fallback is True (admin/owner)
    if allow_fallback:
        key = os.environ.get("GROQ_API_KEY")
        if key and key.strip():
            return key.strip()
        if os.path.exists(KEY_FILE):
            try:
                with open(KEY_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
            except Exception:
                pass
    return None

def save_groq_key(key: str, user_key_file: Optional[str] = None):
    target = user_key_file if user_key_file else KEY_FILE
    with open(target, "w", encoding="utf-8") as f:
        f.write(key.strip())

# Legacy compatibility aliases
get_gemini_key = get_groq_key
save_gemini_key = save_groq_key

# =====================================================================
# DETERMINISTIC ALGORITHMIC KILL-SWITCH GUARDRAILS
# =====================================================================

BANNED_HOOK_PATTERNS = [
    r"^in\s+\d{4}\b",                                    # Blocks "In 1961...", "In 1974..."
    r"^there\s+is\s+a\b",                                # Blocks "There is a terrifying..."
    r"^did\s+you\s+know\b",                              # Blocks trivia openers
    r"\bpsychologist(s)?\s+(proved|discovered|found|warn)", # Blocks academic lecture openings
    r"\b(behavioral|psychological)\s+glitch\b",          # Blocks AI-slop "glitch" phrasing
    r"\bcalled\s+the\b",                                 # Blocks naming effects in the first sentence
    r"\bknown\s+as\s+the\b",                             # Blocks naming effects in the first sentence
    r"\bdunning[\s-]kruger\b",                           # Hard ban on Dunning-Kruger
    r"\bben\s+franklin\s+effect\b",                      # Hard ban on Ben Franklin Effect
    r"\bwin\s+every\s+argument\b",                       # Hard ban on cliché argument hooks
    r"\bmake\s+anyone\s+like\s+you\b",                   # Hard ban on low-stakes self-help
    r"\bbody\s+language\s+tricks?\b"                     # Hard ban on generic body language advice
]

def validate_viral_script(data: dict, niche: str) -> Tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Output must be a valid JSON object"

    acts = data.get("script_acts", {})
    if not isinstance(acts, dict):
        return False, "Missing 'script_acts' dictionary"

    act1 = acts.get("act1_hook", "").strip()
    act2 = acts.get("act2_mechanism", "").strip()
    act3 = acts.get("act3_directive", "").strip()
    act4 = acts.get("act4_seal", "").strip()

    if not act1 or not act2 or not act3 or not act4:
        return False, "All 4 acts (act1_hook, act2_mechanism, act3_directive, act4_seal) must be non-empty"

    # Test Act 1 against Banned Hook Patterns
    for pat in BANNED_HOOK_PATTERNS:
        if re.search(pat, act1, re.IGNORECASE):
            return False, f"Act 1 hook triggered banned algorithmic pattern: {pat}"

    # Verify Second-Person Immersion in the first 6 words
    first_six_words = " ".join(act1.split()[:6]).lower()
    if not re.search(r"\b(you|your|you're|you've|yourself)\b", first_six_words):
        return False, f"Act 1 hook must address viewer directly with 'you'/'your' in the first 6 words (Found: '{first_six_words}')"

    # Verify Word Count Bounds (High Retention Pace)
    full_text = f"{act1} {act2} {act3} {act4}"
    word_count = len(full_text.split())
    if word_count < 65 or word_count > 165:
        return False, f"Total spoken word count is {word_count} words (Must be 65-165 words for ~30-45s retention)"

    # Verify Act 3 contains actionable quote / counter-phrase
    if '"' not in act3 and "'" not in act3 and "say" not in act3.lower() and "whisper" not in act3.lower() and "look" not in act3.lower():
        return False, "Act 3 must contain a concrete spoken counter-script or physical counter-directive"

    return True, "Valid"

# =====================================================================
# MULTI-PROVIDER AI SCRIPT GENERATOR
# Primary: Groq LPU (0.6s) | Fallback: OpenAI / DeepSeek Free (Zero-Key)
# =====================================================================

def _fetch_gta6_news_source(history: list) -> Optional[Tuple[str, str]]:
    """Fetches the freshest unread GTA 6 article from RockstarIntel RSS (zero-block real facts)."""
    import html as html_lib
    import xml.etree.ElementTree as ET

    used = {str(entry.get("concept", "")).lower() for entry in history}
    used.update(str(entry.get("title", "")).lower() for entry in history)
    try:
        r = requests.get("https://rockstarintel.com/feed/", headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.text)
        ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
        for it in root.findall(".//item"):
            title = html_lib.unescape((it.findtext("title") or "").strip())
            if not title or title.lower() in used:
                continue
            body = it.findtext("content:encoded", default="", namespaces=ns) or it.findtext("description", default="")
            clean = re.sub(r"<[^>]+>", " ", body)
            clean = html_lib.unescape(re.sub(r"\s+", " ", clean)).strip()
            if len(clean) >= 300:
                return title, clean
    except Exception as e:
        print(f"GTA6 RSS fetch note: {e}")
    return None


def build_prompt_and_schema(
    niche: str,
    concept: Optional[str],
    brand_name: str,
    brand_handle: str,
    surprise: bool,
    topic_history_file: Optional[str]
) -> Tuple[str, str, dict]:
    from idea_bank import NICHE_PROFILES, CONCEPTS_DATABASE, load_topic_history

    profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
    history = load_topic_history(topic_history_file)
    recent_titles = [entry.get("title", "") for entry in history[-25:] if entry.get("title")]

    chosen_angle = concept.strip() if concept and concept.strip() else ""
    auto_source_excerpt = None
    if not chosen_angle and niche == "gta6_launch":
        rss_item = _fetch_gta6_news_source(history)
        if rss_item:
            chosen_angle, rss_body = rss_item
            auto_source_excerpt = f"HEADLINE: {chosen_angle}\n\n{rss_body}"[:6000]

    if not chosen_angle:
        angles_pool = profile.get("angles", [])
        if not angles_pool:
            angles_pool = [c.get("title") for c in CONCEPTS_DATABASE.get(niche, []) if isinstance(c, dict) and c.get("title")]
        used_angles = {str(entry.get("concept", "")).lower() for entry in history}
        avail = [a for a in angles_pool if isinstance(a, str) and a.lower() not in used_angles] or angles_pool
        chosen_angle = random.choice(avail) if avail else "The Psychological Paradox"

    forbidden = ", ".join(profile.get("forbidden_tropes", []))
    recent_avoid = ", ".join(f'"{t}"' for t in recent_titles[-8:]) if recent_titles else "None"

    is_source_text = bool(auto_source_excerpt or (concept and len(concept.strip()) > 120))
    if is_source_text:
        if auto_source_excerpt:
            source_excerpt = auto_source_excerpt
        else:
            source_excerpt = chosen_angle[:6000]
            chosen_angle = source_excerpt[:120] + "..."
        prompt = f"""You are a real human YouTube Shorts editor for '{brand_name}' ({brand_handle}).
Condense ONLY the real facts from the SOURCE TRANSCRIPT / ARTICLE below into a punchy 25-32 second Short (70-95 words total).

SOURCE TEXT (TRUTH ONLY — DO NOT INVENT ANYTHING OUTSIDE THIS):
\"\"\"
{source_excerpt}
\"\"\"

STRICT RULES:
1. ZERO INVENTED FACTS: Use ONLY numbers, hardware specs, console names, and claims explicitly stated in SOURCE TEXT. Never guess, extrapolate, or add outside claims.
2. SOUND LIKE A REAL HUMAN: Short conversational sentences for voiceover. No parentheses, no robotic spec lists.
3. ACT 1 HOOK (0-3s | 12-18 words): Start with "You" / "Your" in the first 6 words framing the sharpest real point from SOURCE TEXT.
4. ACT 2 EXPLANATION (3-18s | 30-42 words): Deliver the core proof/fact cleanly from SOURCE TEXT.
5. ACT 3 TAKEAWAY (18-27s | 18-25 words): Practical takeaway or conclusion directly from SOURCE TEXT.
6. ACT 4 OUTRO (27-31s | 6-10 words): "Follow {brand_name} for more." (NEVER say "{brand_handle}" in spoken words).
7. TITLE: Under 55 chars, plain human English + #shorts.

Respond ONLY with valid JSON using this exact schema:
{{
  "title": "Punchy title under 55 chars with #shorts",
  "script_acts": {{
    "act1_hook": "0-3s hook with 'you'/'your' in first 6 words based strictly on SOURCE TEXT",
    "act2_mechanism": "3-18s core fact from SOURCE TEXT",
    "act3_directive": "18-27s takeaway from SOURCE TEXT",
    "act4_seal": "27-31s outro: Follow {brand_name} for more."
  }},
  "keywords": ["gaming-console", "miami-night", "neon-city", "sports-car", "videogame-controller"],
  "search_tags": ["gta 6 news", "gta 6 breakdown", "gaming shorts", "gta vi"],
  "description": "2-sentence summary based strictly on SOURCE TEXT. Subscribe to {brand_handle} #shorts #gaming",
  "pinned_comment": "Natural question about the video topic to spark comments",
  "voice": "{profile.get('voice_recommended', 'en-US-ChristopherNeural')}"
}}
"""
    elif niche == "gta6_launch":
        prompt = f"""You are a real human gaming YouTuber writing a 30-second GTA 6 Short for '{brand_name}' ({brand_handle}).
Write like a real gamer talking naturally into a mic — short, punchy, conversational sentences. ZERO robotic AI phrasing, ZERO spec-sheet dumping.

TARGET TOPIC: "{chosen_angle}"
CHANNEL BRAND NAME: "{brand_name}"
CHANNEL HANDLE: "{brand_handle}"

STRICT WRITING RULES:
1. ONE TOPIC ONLY: Stick strictly to "{chosen_angle}". Do NOT cram 4 consoles, TFLOPS, RAM pools, and storage into one script unless the topic specifically compares them.
2. SOUND HUMAN:
   - Never use parentheses (), tildes (~), slashes, or Newegg spec lists ("12 TFLOPS GPU, 16 GB RAM, ~802 GB usable").
   - Write how people actually talk ("225 gigabytes", "512 gig Series S", "30 FPS").
3. NO FAKE FACTS / NO MASHUPS:
   - Never invent fake console menus or settings (no "SSD-only mode", no "30 FPS settings").
   - Never mash unrelated numbers together (no "62% of physics").
   - Verified facts you may use ONLY when relevant to the topic:
     * GTA 6 launches November 19th targeting 30 FPS on PS5, PS5 Pro, Series X, and Series S (CPU runs traffic/AI simulation).
     * Xbox preload is ~225 GB; a 512 GB Series S only has ~364 GB usable, and Series X|S games cannot launch from USB external drives (Xbox Cloud Gaming streams day one).
     * PS5 Trailer 2 was ~1440p/2560x1152 upscaled to 4K with ray tracing; Series S will run lower resolution/lighting, and dataminer Tez2 spotted AMD FSR 4.1 files in Xbox preload.

STRUCTURE (70-95 WORDS TOTAL, ~25-32 SECONDS):
1. ACT 1 HOOK (0-3s | 12-18 words): Start with "You" / "Your" or a direct scroll-stopping observation about THIS topic. No "Did you know".
2. ACT 2 EXPLANATION (3-18s | 30-42 words): Explain the one core point clearly like you're telling a friend.
3. ACT 3 TAKEAWAY (18-27s | 18-25 words): Real practical tip, what to expect on Nov 19, or detail to look for.
4. ACT 4 OUTRO (27-31s | 6-10 words): "Follow {brand_name} for real GTA 6 updates." (NEVER say "{brand_handle}" or "-y6" in spoken words).
5. TITLE: Under 55 chars, plain human English + #shorts #gta6.

NEGATIVE FILTER:
- Never mention: [{forbidden}].
- Avoid recent topics: [{recent_avoid}].

Respond ONLY with valid JSON using this exact schema:
{{
  "title": "Punchy human GTA 6 title under 55 chars with #shorts #gta6",
  "script_acts": {{
    "act1_hook": "0-3s natural human hook on this single topic",
    "act2_mechanism": "3-18s clear conversational explanation (no spec-sheet dump)",
    "act3_directive": "18-27s real practical takeaway or detail to watch for",
    "act4_seal": "27-31s clean outro: Follow {brand_name} for real GTA 6 updates."
  }},
  "keywords": ["gaming-console", "miami-night", "neon-city", "sports-car", "police-lights", "videogame-controller"],
  "search_tags": ["gta 6 news", "gta 6 gameplay", "gta 6 release", "gta vi", "gta 6 shorts"],
  "description": "2-sentence human description about this GTA 6 topic. Subscribe to {brand_handle} #shorts #gta6 #gtavi #gaming",
  "pinned_comment": "Short natural question gamers will argue about in comments",
  "voice": "{profile.get('voice_recommended', 'en-US-ChristopherNeural')}"
}}
"""
    else:
        prompt = f"""You are the world-class Head Writer for a viral YouTube Shorts channel in the '{profile['name']}' niche.
Write a masterclass viral short script designed for 100%+ retention, emotional adrenaline, and zero scroll-away.

TARGET ANGLE: "{chosen_angle}"
CHANNEL BRAND NAME: "{brand_name}"
CHANNEL HANDLE: "{brand_handle}"

MANDATORY 4-ACT ARCHITECTURE (STRICT RULES):
1. ACT 1 HOOK (0-4s | 18-24 words):
   - MUST place the viewer ("YOU" / "YOUR") inside a physical emergency, danger, or counter-intuitive dilemma within the first 6 words.
   - MUST contain a visceral numeric stat, contrast, or multiplier (e.g. "five times more likely", "seventy percent", "four seconds").
   - STRICT BANS:
     * NEVER start with a year ("In 1961...", "In 1974...").
     * NEVER start with "There is a...", "Did you know...", or "A psychologist proved...".
     * NEVER use the words "human behavioral glitch" or "psychological glitch".
     * NEVER name clinical effects in Act 1.
2. ACT 2 MECHANISM (4-17s | 35-44 words):
   - Explain the evolutionary brain trap, predator tactic, or cognitive betrayal causing this danger. Keep it visceral and cinematic.
3. ACT 3 DIRECTIVE (17-31s | 28-36 words):
   - Give the viewer an exact physical counter-move AND a verbatim spoken script in quotation marks ("...") they can use to break the trap.
4. ACT 4 DYNAMIC BRANDED OUTRO (31-35s | 10-14 words - MANDATORY):
   - MUST call out your channel name using this formula:
     "Follow {brand_name} for [dynamic, context-specific reason tailored directly to this topic]."
5. TOTAL SPOKEN WORDS:
   - Strictly between 85 and 110 words total across all acts (~33-42s fast pacing).
6. TITLE RULE (CRITICAL FOR SHORTS FEED CTR):
   - Use plain, visceral everyday English (e.g. "Why Crowds Ignore Dying People (The Fix)").
   - NEVER put academic jargon, experiment names, years, or clinical terms in the title (no "Compliance Loop", "Forced Teaming", "Rosenhan", "1974", "Presupposition").

NEGATIVE FILTER:
- Never mention: [{forbidden}].
- Avoid recent topics: [{recent_avoid}].

Respond ONLY with valid JSON using this exact schema:
{{
  "title": "Visceral high-CTR title under 70 chars with #shorts and 1 niche hashtag",
  "script_acts": {{
    "act1_hook": "0-4s visceral second-person paradox hook with 'you' in first 6 words",
    "act2_mechanism": "4-21s explanation of the brain betrayal or trap",
    "act3_directive": "21-37s physical counter-move + exact spoken script in quotation marks",
    "act4_seal": "37-41s dynamic branded outro: Follow {brand_name} for [dynamic topic-specific promise]"
  }},
  "keywords": ["dark-crowd", "interrogation", "cctv-footage", "eye-contact", "shadows", "emergency-light", "tunnel", "subway"],
  "search_tags": ["real search phrase 1", "multi word search tag 2", "dark psychology tricks", "survival facts", "human behavior psychology"],
  "description": "2-sentence high-stakes description with Subscribe to {brand_handle}, #shorts and 5 hashtags",
  "pinned_comment": "Polarizing debate question to trigger intense comment arguments",
  "voice": "{profile.get('voice_recommended', 'en-US-ChristopherNeural')}"
}}
"""
    return prompt, chosen_angle, profile

def clean_and_assemble_script(parsed: dict, brand_name: str, brand_handle: str, profile: dict, chosen_angle: str) -> dict:
    acts = parsed.get("script_acts", {})
    full_script = f"{acts.get('act1_hook', '')} {acts.get('act2_mechanism', '')} {acts.get('act3_directive', '')} {acts.get('act4_seal', '')}".strip()
    clean_handle = brand_handle.lstrip("@").strip()
    if clean_handle and clean_handle.lower() != brand_name.lower():
        full_script = re.sub(re.escape(brand_handle), brand_name, full_script, flags=re.IGNORECASE)
        full_script = re.sub(rf"\b{re.escape(clean_handle)}\b", brand_name, full_script, flags=re.IGNORECASE)
    parsed["script"] = full_script
    if profile.get("id") == "gta6_launch":
        parsed["visual_mode"] = "parkour_brainrot"

    # Ensure search_tags is always a clean list of multi-word search phrases
    raw_tags = parsed.get("search_tags", [])
    if isinstance(raw_tags, str):
        parsed["search_tags"] = [t.strip() for t in raw_tags.split(",") if t.strip()]
    elif not isinstance(raw_tags, list) or not raw_tags:
        # Fallback to rich niche tags
        n_name = profile.get("name", "Dark Psychology").lower()
        parsed["search_tags"] = [
            f"{n_name} facts",
            "human behavior psychology",
            "dark psychology",
            "psychology facts",
            "body language secrets",
            "survival hacks",
            "life saving psychology"
        ]

    if brand_name.lower() != "shadowmind":
        for key in ["title", "script", "description", "pinned_comment"]:
            if key in parsed and isinstance(parsed[key], str):
                parsed[key] = re.sub(r'(?i)\btheshadowmindhq(?:-hub)?\b', brand_handle.lstrip("@"), parsed[key])
                parsed[key] = re.sub(r'(?i)@ShadowMind\b', brand_handle, parsed[key])
                parsed[key] = re.sub(r'(?i)\bShadowMind\b', brand_name, parsed[key])

    voice_pool = [
        profile.get("voice_recommended", "en-US-ChristopherNeural"),
        "en-US-ChristopherNeural",
        "en-US-GuyNeural",
        "en-US-EricNeural",
        "en-GB-RyanNeural"
    ]
    parsed["voice"] = random.choice(voice_pool)
    parsed["chosen_angle"] = chosen_angle
    return parsed

def generate_with_groq_lpu(prompt: str, api_key: str) -> Optional[dict]:
    """Generates viral script using Groq Cloud LPU in ~0.6 seconds."""
    # Prioritize qwen/qwen3.8-27b (fastest native json_object), then openai/gpt-oss-120b and 20b with ample max_tokens
    models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "allam-2-7b"]
    for model_name in models:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            max_tok = 3500 if "gpt-oss" in model_name else 1400
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a professional YouTube Shorts scriptwriter. Output strictly valid JSON matching the user schema."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.68,
                "max_tokens": max_tok
            }
            # Only add response_format for models that natively support json_object without schema conflict
            if "qwen" in model_name:
                payload["response_format"] = {"type": "json_object"}

            res = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                choice = data["choices"][0]
                content = choice.get("message", {}).get("content") or ""
                # If content is empty but model provided reasoning with json, search reasoning
                if not content.strip():
                    reasoning_text = choice.get("message", {}).get("reasoning") or ""
                    match_r = re.search(r'(\{[\s\S]*\})', reasoning_text)
                    if match_r:
                        content = match_r.group(1)

                # Strip reasoning think tags if present
                clean_content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                # Match inner json if enclosed in tags or markdown
                match = re.search(r'(\{[\s\S]*\})', clean_content)
                clean_json = match.group(1) if match else clean_content
                parsed = json.loads(clean_json)
                parsed["model_used"] = f"groq-{model_name.split('/')[-1]}"
                return parsed
            elif res.status_code in (401, 403):
                print(f"Groq auth error ({res.status_code}): {res.text}")
                break
            else:
                print(f"Groq {model_name} HTTP {res.status_code}: {res.text[:150]}")
        except Exception as e:
            print(f"Groq {model_name} error: {e}")
    return None

def generate_with_pollinations_free_ai(prompt: str) -> Optional[dict]:
    """100% Free Zero-Key Fallback: OpenAI / DeepSeek endpoint."""
    try:
        url = "https://text.pollinations.ai/openai"
        payload = {
            "model": "openai",
            "messages": [
                {"role": "system", "content": "You are a professional YouTube Shorts scriptwriter. Output strictly valid JSON matching the user schema."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            # Extract JSON substring if wrapped in markdown
            match = re.search(r'(\{[\s\S]*\})', content)
            raw_json = match.group(1) if match else content
            parsed = json.loads(raw_json)
            parsed["model_used"] = "openai-free-tier"
            return parsed
    except Exception as e:
        print(f"Pollinations free AI fallback error: {e}")
    return None

def generate_ai_script(
    niche: str = "dark_psychology",
    concept: Optional[str] = None,
    user_key_file: Optional[str] = None,
    brand_name: str = "ShadowMind",
    brand_handle: str = "@TheShadowMindHQ-Hub",
    allow_fallback: bool = True,
    user_tracker_file: Optional[str] = None,
    surprise: bool = False,
    topic_history_file: Optional[str] = None
) -> Optional[dict]:
    """Unified AI script engine: Groq LPU (Primary) -> OpenAI/DeepSeek Zero-Key (Fallback)."""
    from idea_bank import record_topic_history

    if niche == "gta6_launch":
        from gta_news_engine import generate_zero_ai_gta_script
        return generate_zero_ai_gta_script(
            concept=concept,
            brand_name=brand_name,
            brand_handle=brand_handle,
            topic_history_file=topic_history_file,
        )

    prompt, chosen_angle, profile = build_prompt_and_schema(
        niche=niche,
        concept=concept,
        brand_name=brand_name,
        brand_handle=brand_handle,
        surprise=surprise,
        topic_history_file=topic_history_file
    )

    api_key = get_groq_key(user_key_file, allow_fallback=allow_fallback)

    # 1. Primary: Groq LPU (0.6s)
    parsed = None
    if api_key:
        parsed = generate_with_groq_lpu(prompt, api_key)

    # 2. Limitless Fallback: OpenAI / DeepSeek Zero-Key API
    if not parsed:
        print("Falling back to limitless Free AI Engine (OpenAI / DeepSeek Zero-Key)...")
        parsed = generate_with_pollinations_free_ai(prompt)

    if parsed:
        is_valid, reason = validate_viral_script(parsed, niche)
        if not is_valid:
            print(f"Validation rejected AI output: {reason}. Regenerating cleanly...")
            # One quick recovery attempt
            rec_prompt = prompt + f"\nRE-ATTEMPT FIX: {reason}. Ensure Act 1 starts with 'you'/'your' directly."
            if api_key:
                parsed = generate_with_groq_lpu(rec_prompt, api_key)
            if not parsed:
                parsed = generate_with_pollinations_free_ai(rec_prompt)

    if parsed:
        # Strictly record 1 single AI request per finalized script
        if parsed.get("model_used", "").startswith("groq-"):
            try:
                from usage_tracker import record_ai_request
                record_ai_request(tracker_file=user_tracker_file)
            except Exception:
                pass

        final_data = clean_and_assemble_script(parsed, brand_name, brand_handle, profile, chosen_angle)
        record_topic_history(topic_history_file, final_data.get("title", ""), niche, chosen_angle)
        return final_data

    return None

# Backward compatibility alias
generate_with_gemini_flash = generate_ai_script
