import os
import json
import requests
import re
from typing import Optional, Dict, Tuple, Any

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
KEY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini_api_key.txt")

def _ensure_env():
    if not os.environ.get("GEMINI_API_KEY") and os.path.exists(ENV_FILE):
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

def get_gemini_key(user_key_file: Optional[str] = None, allow_fallback: bool = False) -> Optional[str]:
    # 1. Check user-specific key file if provided
    if user_key_file and os.path.exists(user_key_file):
        try:
            with open(user_key_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception:
            pass
    # 2. Only allow fallback to env or global file if allow_fallback is True (admin/owner only)
    if allow_fallback:
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
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

def save_gemini_key(key: str, user_key_file: Optional[str] = None):
    target = user_key_file if user_key_file else KEY_FILE
    with open(target, "w", encoding="utf-8") as f:
        f.write(key.strip())

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
    r"\buse\s+absolute\s+silence\b",                     # Hard ban on cliché silence hooks
]

BANNED_TITLE_PATTERNS = [
    r"\b\d{4}\s+compliance\b",
    r"\bglitch\b",
    r"\bdunning[\s-]kruger\b",
    r"\bben\s+franklin\b",
    r"\bmake\s+anyone\s+like\s+you\b",
]

def validate_viral_script(payload: Dict[str, Any], niche: str) -> Tuple[bool, str]:
    """
    Audits Gemini's output against the ShadowMind High-Stakes Survival Architecture.
    """
    title = payload.get("title", "").strip()
    script_acts = payload.get("script_acts", {})
    act1 = script_acts.get("act1_hook", "").strip()
    act2 = script_acts.get("act2_mechanism", "").strip()
    act3 = script_acts.get("act3_directive", "").strip()
    act4 = script_acts.get("act4_seal", "").strip()

    full_script = f"{act1} {act2} {act3} {act4}".strip()
    words = full_script.split()
    word_count = len(words)

    # 1. Word Count Enforcement (105 to 135 words = ~38-44s)
    if not (105 <= word_count <= 135):
        return False, f"Word count out of bounds: {word_count} words (Required: 105-135)."

    # 2. Second-Person Protagonist Check in Act 1 (First 12 words must contain 'you', 'your', or 'you're')
    first_12_words = " ".join(act1.lower().split()[:12])
    if not re.search(r"\b(you|your|you're)\b", first_12_words):
        return False, f"Act 1 Hook fails 2nd-person immediacy check in first 12 words: '{first_12_words}'"

    # 3. Banned Hook Pattern Check on Act 1
    act1_lower = act1.lower()
    for pattern in BANNED_HOOK_PATTERNS:
        if re.search(pattern, act1_lower):
            return False, f"Act 1 Hook triggered banned pattern '{pattern}': '{act1}'"

    # 4. Banned Title Pattern Check
    title_lower = title.lower()
    for pattern in BANNED_TITLE_PATTERNS:
        if re.search(pattern, title_lower):
            return False, f"Title triggered banned pattern '{pattern}': '{title}'"

    # 5. Act 3 Concrete Directive Check (must contain quotation marks for spoken phrase)
    if '"' not in act3 and "'" not in act3:
        return False, "Act 3 Directive must contain an exact spoken phrase in quotation marks."

    return True, "PASSED"

def generate_with_gemini_flash(
    niche: str,
    concept: Optional[str] = None,
    user_key_file: Optional[str] = None,
    brand_name: str = "ShadowMind",
    brand_handle: Optional[str] = None,
    allow_fallback: bool = False,
    user_tracker_file: Optional[str] = None,
    surprise: bool = False,
    topic_history_file: Optional[str] = None
) -> Optional[Dict]:
    api_key = get_gemini_key(user_key_file, allow_fallback=allow_fallback)
    if not api_key:
        return None

    if not brand_handle:
        brand_handle = f"@{brand_name}" if not brand_name.startswith("@") else brand_name

    from idea_bank import NICHE_PROFILES, get_random_niche_angle, load_topic_history, record_topic_history

    profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
    history = load_topic_history(topic_history_file)
    recent_titles = [h.get("title", "") for h in history[:25] if h.get("title")]

    if surprise or not concept or not concept.strip():
        chosen_angle = get_random_niche_angle(niche, history_file=topic_history_file)
    else:
        chosen_angle = concept.strip()

    forbidden = ", ".join(profile.get("forbidden_terms", []))
    visual_sample = ", ".join(profile.get("visual_bank", [])[:15])
    recent_avoid = "; ".join(recent_titles[:15]) if recent_titles else "None yet"
    niche_name = profile.get("name", niche)
    outro_template = profile.get("outro_phrase", f"Follow {brand_name} for psychological rules that put you five steps ahead.").format(brand_name=brand_name)

    base_prompt = f"""You are the Lead Viral Retention Architect for '{brand_name}' ({brand_handle}), an emergency human behavior, dark psychology, and high-stakes survival YouTube Shorts channel.
Generate a ruthlessly high-retention 38 to 44-second YouTube Short script for: "{niche_name}".

PRIMARY ANGLE / CONCEPT: "{chosen_angle}"

OUR EMPIRICAL GOLD STANDARD (1,200+ VIEWS, >78% VVSA):
- Title: "Why a Crowd of 100 People Will Watch You Die #shorts #psychology"
- Act 1 Hook (0-4s): "If you collapse in front of a crowd of one hundred people, you are five times more likely to die than in front of a single stranger."
- Act 2 Mechanism (4-21s): Explains why everyone waits for someone else to act (diffusion of responsibility) while you bleed out.
- Act 3 Directive (21-37s): "Never shout for help into a crowd. Look at one specific person, point directly at them, and say: 'You in the blue jacket, call an ambulance right now!'"
- Act 4 Seal (37-41s): "Calling out their clothing destroys their anonymity and forces their brain out of the trance."

MANDATORY 4-ACT ARCHITECTURE (STRICT RULES):
1. ACT 1 HOOK (0-4s | 18-24 words):
   - MUST place the viewer ("YOU" / "YOUR") inside a physical emergency, danger, or counter-intuitive dilemma within the first 6 words.
   - MUST contain a visceral numeric stat, contrast, or multiplier (e.g. "five times more likely", "seventy percent", "four seconds").
   - STRICT BANS:
     * NEVER start with a year ("In 1961...", "In 1974...").
     * NEVER start with "There is a...", "Did you know...", or "A psychologist proved...".
     * NEVER use the words "human behavioral glitch" or "psychological glitch".
     * NEVER name clinical effects in Act 1 (do NOT say "called the Dunning-Kruger effect" or "the Ben Franklin Effect").
     * NEVER use soft self-help advice ("How to win an argument", "How to make people like you").
2. ACT 2 MECHANISM (4-21s | 45-52 words):
   - Explain the evolutionary brain trap, predator tactic, or cognitive betrayal causing this danger. Keep it visceral and cinematic.
3. ACT 3 DIRECTIVE (21-37s | 38-46 words):
   - Give the viewer an exact physical counter-move AND a verbatim spoken script in quotation marks ("...") they can use to break the trap.
4. ACT 4 SEAL (37-41s | 8-12 words):
   - A chilling punchline explaining why that command works, or a seamless loop into the theme.
5. TOTAL SPOKEN WORDS:
   - Strictly between 108 and 128 words total across all acts.

NEGATIVE FILTER:
- Never mention or draw from: [{forbidden}].
- Avoid these recent titles: [{recent_avoid}].

Respond ONLY with valid JSON using this exact schema:
{{
  "title": "Visceral high-CTR title under 70 chars with #shorts and 1 niche hashtag",
  "script_acts": {{
    "act1_hook": "0-4s visceral second-person paradox hook with 'you' in first 6 words (18-24 words)",
    "act2_mechanism": "4-21s explanation of the brain betrayal or trap (45-52 words)",
    "act3_directive": "21-37s physical counter-move + exact spoken script in quotation marks (38-46 words)",
    "act4_seal": "37-41s punchy final line (8-12 words)"
  }},
  "keywords": ["dark-crowd", "interrogation", "cctv-footage", "eye-contact", "shadows", "emergency-light", "tunnel", "subway"],
  "description": "2-sentence high-stakes description with Subscribe to {brand_handle}, #shorts and 5 hashtags",
  "pinned_comment": "Polarizing debate question to trigger intense comment arguments",
  "voice": "{profile.get('voice_recommended', 'en-US-ChristopherNeural')}"
}}
"""

    MODELS_TO_TRY = [
        "gemini-2.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-3.8-flash"
    ]

    for model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        for attempt in range(1, 4):
            prompt = base_prompt
            if attempt > 1:
                prompt += "\nRE-ATTEMPT NOTICE: Ensure Act 1 starts with 'you'/'your' immediately, has NO dates or 'There is a...', and Act 3 has an exact spoken script in quotes."

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.68
                }
            }

            try:
                res = requests.post(url, json=payload, timeout=14)
                if res.status_code == 200:
                    try:
                        from usage_tracker import record_gemini_request
                        server_rem = None
                        if "x-ratelimit-remaining-requests" in res.headers:
                            try:
                                server_rem = int(res.headers["x-ratelimit-remaining-requests"])
                            except Exception:
                                pass
                        record_gemini_request(server_remaining=server_rem, tracker_file=user_tracker_file)
                    except Exception:
                        pass
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text)
                    parsed["model_used"] = model_name

                    # Programmatic validation audit against algorithmic failure modes
                    is_valid, reason = validate_viral_script(parsed, niche)
                    if not is_valid:
                        print(f"Validation rejected attempt {attempt} on {model_name}: {reason}")
                        continue

                    # Assemble full spoken script from 4 acts
                    acts = parsed.get("script_acts", {})
                    full_script = f"{acts.get('act1_hook', '')} {acts.get('act2_mechanism', '')} {acts.get('act3_directive', '')} {acts.get('act4_seal', '')}".strip()
                    parsed["script"] = full_script

                    # Sanitize any accidental ShadowMind mentions if user brand is different
                    if brand_name.lower() != "shadowmind":
                        for key in ["title", "script", "description", "pinned_comment"]:
                            if key in parsed and isinstance(parsed[key], str):
                                parsed[key] = re.sub(r'(?i)\btheshadowmindhq(?:-hub)?\b', brand_handle.lstrip("@"), parsed[key])
                                parsed[key] = re.sub(r'(?i)@ShadowMind\b', brand_handle, parsed[key])
                                parsed[key] = re.sub(r'(?i)\bShadowMind\b', brand_name, parsed[key])

                    parsed["voice"] = profile.get("voice_recommended", "en-US-ChristopherNeural")
                    parsed["chosen_angle"] = chosen_angle

                    # Record in topic history
                    record_topic_history(topic_history_file, parsed.get("title", ""), niche, chosen_angle)

                    return parsed
            except Exception as e:
                print(f"Gemini {model_name} attempt {attempt} error: {e}")

    return None
