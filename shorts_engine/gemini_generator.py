import os
import json
import requests
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
    user_tracker_file: Optional[str] = None
) -> Optional[Dict]:
    api_key = get_gemini_key(user_key_file, allow_fallback=allow_fallback)
    if not api_key:
        return None

    if not brand_handle:
        brand_handle = f"@{brand_name}" if not brand_name.startswith("@") else brand_name

    prompt = f"""You are a master YouTube Shorts retention scriptwriter and algorithm expert.
Generate a high-retention 40 to 48-second YouTube Short for the niche: "{niche}".
Specific concept/angle: "{concept if concept else 'invent a shocking, named psychological trick, forbidden historical experiment, or future AI reality'}".

Rules for the script:
1. Hook in the first 3 seconds (create intense curiosity or negative warning).
2. Name the phenomenon (e.g., 'The Pratfall Effect', 'The Baseline Trap').
3. Explain the mechanism clearly with zero fluff.
4. Give an actionable rule or phrase.
5. Permanent Outro: The final sentence MUST always be the channel call-to-action: "Follow {brand_name} for [short niche punchline]." (e.g. "Follow {brand_name} for daily human psychology." or "Follow {brand_name} for dark historical breakthroughs."). ALWAYS end with a period.
6. Target word count: 110 to 135 words (strictly ~42 seconds spoken).

Respond ONLY with valid JSON using this exact schema:
{{
  "title": "Clickbait high-CTR title under 80 characters with #shorts and 1-2 relevant hashtags",
  "script": "The complete 110-135 word spoken script text ending with Follow {brand_name} for ...",
  "keywords": ["5", "cinematic", "high-contrast", "visual", "keywords"],
  "description": "Compelling 2-3 sentence description with Subscribe to {brand_handle}, #shorts and 5 hashtags",
  "pinned_comment": "Controversial or engaging question to drive comment section debates",
  "voice": "en-US-ChristopherNeural"
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
                "temperature": 0.85
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
                
                # Sanitize any accidental ShadowMind mentions if user brand is different
                if brand_name.lower() != "shadowmind":
                    import re
                    for key in ["title", "script", "description", "pinned_comment"]:
                        if key in parsed and isinstance(parsed[key], str):
                            parsed[key] = re.sub(r'(?i)\btheshadowmindhq(?:-hub)?\b', brand_handle.lstrip("@"), parsed[key])
                            parsed[key] = re.sub(r'(?i)@ShadowMind\b', brand_handle, parsed[key])
                            parsed[key] = re.sub(r'(?i)\bShadowMind\b', brand_name, parsed[key])

                # Outro Guarantee
                script = parsed.get("script", "").strip()
                if brand_name.lower() not in script.lower():
                    script = script.rstrip(" .,!?:;-")
                    outro_map = {
                        "dark_psychology": f"Follow {brand_name} for daily human psychology.",
                        "forbidden_history": f"Follow {brand_name} for dark historical breakthroughs.",
                        "future_tech": f"Follow {brand_name} for the hidden realities shaping tomorrow.",
                        "skincare_science": f"Follow {brand_name} for science-backed truths.",
                        "gaming_lore": f"Follow {brand_name} for dark gaming lore."
                    }
                    script = f"{script}. {outro_map.get(niche, f'Follow {brand_name} to stay ahead.')}"
                    parsed["script"] = script
                
                # Select voice by niche
                if niche in ["skincare_science", "beauty"]:
                    parsed["voice"] = "en-US-JennyNeural"
                elif niche in ["gaming_lore"]:
                    parsed["voice"] = "en-US-GuyNeural"
                else:
                    parsed["voice"] = "en-US-ChristopherNeural"
                    
                return parsed
        except Exception as e:
            print(f"Gemini {model_name} error: {e}")
            
    return None
