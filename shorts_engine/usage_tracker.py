import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_FILE = os.path.join(BASE_DIR, "usage_tracker.json")

# Official Google Quota Limits
GEMINI_DAILY_LIMIT = 1500  # Google AI Studio Free Tier RPD (Requests Per Day)
GEMINI_RPM_LIMIT = 15      # 15 Requests Per Minute
YOUTUBE_DAILY_LIMIT = 10000  # YouTube Data API v3 units/day (Google Cloud Project)
YOUTUBE_UPLOAD_COST = 1600  # Cost per videos.insert (Max 6 uploads/day on 10k quota)

def get_current_pt_date() -> str:
    """Google Cloud & YouTube quotas reset at Midnight Pacific Time (PT)."""
    # UTC-7 (PDT) / UTC-8 (PST)
    pt_offset = timedelta(hours=-7)
    now_pt = datetime.now(timezone.utc) + pt_offset
    return now_pt.strftime("%Y-%m-%d")

def get_seconds_until_pt_midnight() -> int:
    """Exact countdown to 12:00 AM Pacific Time (Google Cloud daily quota reset)."""
    pt_offset = timedelta(hours=-7)
    now_pt = datetime.now(timezone.utc) + pt_offset
    seconds_today = now_pt.hour * 3600 + now_pt.minute * 60 + now_pt.second
    return 86400 - seconds_today

def load_tracker(tracker_file: Optional[str] = None) -> Dict:
    path = tracker_file if tracker_file else TRACKER_FILE
    current_date = get_current_pt_date()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date_pt") == current_date:
                    return data
        except Exception:
            pass

    # Fresh Google quota day initialized at midnight PT
    initial_data = {
        "date_pt": current_date,
        "gemini_requests": 0,
        "youtube_units": 0,
        "server_reported_remaining": None
    }
    save_tracker(initial_data, path)
    return initial_data

def save_tracker(data: Dict, tracker_file: Optional[str] = None):
    path = tracker_file if tracker_file else TRACKER_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def record_gemini_request(server_remaining: Optional[int] = None, tracker_file: Optional[str] = None):
    data = load_tracker(tracker_file)
    data["gemini_requests"] = data.get("gemini_requests", 0) + 1
    if server_remaining is not None:
        data["server_reported_remaining"] = server_remaining
    save_tracker(data, tracker_file)

def record_youtube_upload(tracker_file: Optional[str] = None):
    data = load_tracker(tracker_file)
    data["youtube_units"] = data.get("youtube_units", 0) + YOUTUBE_UPLOAD_COST
    save_tracker(data, tracker_file)

def get_usage_summary(tracker_file: Optional[str] = None) -> Dict:
    data = load_tracker(tracker_file)
    sec_left = get_seconds_until_pt_midnight()
    hrs = sec_left // 3600
    mins = (sec_left % 3600) // 60
    countdown = f"{hrs:02d}h {mins:02d}m"

    gem_limit = data.get("gemini_limit", GEMINI_DAILY_LIMIT)
    gem_used = data.get("gemini_requests", 0)
    server_rem = data.get("server_reported_remaining")
    gem_rem = server_rem if server_rem is not None else max(0, gem_limit - gem_used)
    gem_pct = round((gem_used / gem_limit) * 100, 1) if gem_limit > 0 else 0.0

    yt_limit = data.get("youtube_limit", YOUTUBE_DAILY_LIMIT)
    yt_used = data.get("youtube_units", 0)
    yt_rem = max(0, yt_limit - yt_used)
    yt_pct = round((yt_used / yt_limit) * 100, 1) if yt_limit > 0 else 0.0
    uploads_left = yt_rem // YOUTUBE_UPLOAD_COST

    return {
        "date_pt": data["date_pt"],
        "timezone": "Pacific Time (PT - Google Cloud Standard)",
        "reset_countdown": countdown,
        "gemini": {
            "used": gem_used,
            "limit": gem_limit,
            "remaining": gem_rem,
            "rpm_limit": GEMINI_RPM_LIMIT,
            "percent": gem_pct
        },
        "youtube": {
            "units_used": yt_used,
            "limit": yt_limit,
            "remaining_units": yt_rem,
            "uploads_remaining": uploads_left,
            "percent": yt_pct,
            "upload_cost": YOUTUBE_UPLOAD_COST,
            "note": f"{uploads_left} uploads left on {yt_limit:,} quota (1,600 units/upload)"
        }
    }
