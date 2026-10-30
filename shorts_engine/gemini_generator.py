import os
import json
import requests
import re
from typing import Optional, Dict

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

    prompt = f"""You are a master YouTube Shorts retention scriptwriter and algorithm expert specializing in viral video pacing.
Generate a high-retention 40 to 48-second YouTube Short for the niche: "{niche_name}".

PRIMARY ANGLE/CONCEPT: "{chosen_angle}"

STRICT BOUNDARY CONSTRAINTS:
1. Stay 100% within the theme of "{niche_name}".
2. STRICT NEGATIVE FILTER: Do NOT mention or use concepts from: [{forbidden}].
3. DO NOT repeat or rephrase these recently produced titles: [{recent_avoid}].
4. The hook must grab attention in the first 3 seconds (curiosity or warning).
5. Name the psychological phenomenon, historical law, or specific mechanism.
6. Target word count: 115 to 135 words (strictly 40-46 seconds spoken).
7. OUTRO MANDATE: The final sentence MUST be: "{outro_template}".

VISUAL SCENE RULES:
Provide 8 to 10 cinematic, 1-2 word filmable stock-footage keywords aligned with this script and niche.
Example safe queries for this niche: [{visual_sample}].

Respond ONLY with valid JSON using this exact schema:
{{
  "title": "High-CTR title under 75 characters with #shorts and 1-2 niche hashtags",
  "script": "The complete 115-135 word spoken script text ending exactly with {outro_template}",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"],
  "description": "Compelling 2-3 sentence description with Subscribe to {brand_handle}, #shorts and 5 hashtags",
  "pinned_comment": "Engaging question to ignite comment section debates",
  "voice": "{profile.get('voice_recommended', 'en-US-ChristopherNeural')}"
}}
"""

    MODELS_TO_TRY = [
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.8-flash"
    ]

    for model_name in MODELS_TO_TRY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.82
            }
        }

        try:
            res = requests.post(url, json=payload, timeout=12)
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

                # Validation guard: ensure no forbidden words slipped in
                script_text = parsed.get("script", "")
                title_text = parsed.get("title", "")
                combined_lower = (script_text + " " + title_text).lower()
                forbidden_detected = [term for term in profile.get("forbidden_terms", []) if re.search(r'\b' + re.escape(term) + r'\b', combined_lower)]
                if forbidden_detected:
                    print(f"Warning: Gemini output contained forbidden terms {forbidden_detected} for niche {niche}. Retrying or sanitizing...")
                    continue

                # Sanitize any accidental ShadowMind mentions if user brand is different
                if brand_name.lower() != "shadowmind":
                    for key in ["title", "script", "description", "pinned_comment"]:
                        if key in parsed and isinstance(parsed[key], str):
                            parsed[key] = re.sub(r'(?i)\btheshadowmindhq(?:-hub)?\b', brand_handle.lstrip("@"), parsed[key])
                            parsed[key] = re.sub(r'(?i)@ShadowMind\b', brand_handle, parsed[key])
                            parsed[key] = re.sub(r'(?i)\bShadowMind\b', brand_name, parsed[key])

                # Outro Guarantee
                script = parsed.get("script", "").strip()
                if brand_name.lower() not in script.lower():
                    script = script.rstrip(" .,!?:;-")
                    script = f"{script}. {outro_template}"
                    parsed["script"] = script

                parsed["voice"] = profile.get("voice_recommended", "en-US-ChristopherNeural")
                parsed["chosen_angle"] = chosen_angle

                # Record in topic history
                record_topic_history(topic_history_file, parsed.get("title", ""), niche, chosen_angle)

                return parsed
        except Exception as e:
            print(f"Gemini {model_name} error: {e}")

    return None
