import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER_FILE = os.path.join(BASE_DIR, "usage_tracker.json")
GCP_SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "gcp_service_account.json")

# Official Google Quota Limits
GEMINI_DAILY_LIMIT = 500   # Google AI Studio Free Tier RPD (Requests Per Day for Flash Lite)
GEMINI_RPM_LIMIT = 15      # 15 Requests Per Minute
YOUTUBE_DAILY_LIMIT = 10000  # YouTube Data API v3 units/day (Google Cloud Project)
YOUTUBE_UPLOAD_COST = 1600  # Cost per videos.insert (Max 6 uploads/day on 10k quota)

_gcp_monitoring_cache = {
    "timestamp": 0.0,
    "data": None
}

def get_current_pt_datetime():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Los_Angeles"))
    except Exception:
        # Standard Pacific fallback (UTC-8 in winter, UTC-7 in summer)
        return datetime.now(timezone.utc) - timedelta(hours=8)

def get_current_pt_date() -> str:
    """Google Cloud & YouTube quotas reset at Midnight Pacific Time (PT)."""
    return get_current_pt_datetime().strftime("%Y-%m-%d")

def get_seconds_until_pt_midnight() -> int:
    """Exact countdown to 12:00 AM Pacific Time (Google Cloud daily quota reset)."""
    now_pt = get_current_pt_datetime()
    seconds_today = now_pt.hour * 3600 + now_pt.minute * 60 + now_pt.second
    return 86400 - seconds_today

def fetch_live_gcp_youtube_quota() -> Optional[Dict]:
    """Queries real Google Cloud Monitoring API for exact quota usage on YouTube API."""
    global _gcp_monitoring_cache
    if not os.path.exists(GCP_SERVICE_ACCOUNT_FILE):
        return None

    now_ts = time.time()
    # Cache for 45s to protect GCP monitoring API rate limits
    if _gcp_monitoring_cache["data"] and (now_ts - _gcp_monitoring_cache["timestamp"] < 45):
        return _gcp_monitoring_cache["data"]

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        now_pt = get_current_pt_datetime()
        with open(GCP_SERVICE_ACCOUNT_FILE, "r", encoding="utf-8") as f:
            sa_data = json.load(f)
        project_id = sa_data.get("project_id", "shadowmind-512716")

        credentials = service_account.Credentials.from_service_account_file(
            GCP_SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/monitoring.read"]
        )
        service = build("monitoring", "v3", credentials=credentials, cache_discovery=False)

        now_utc = datetime.now(timezone.utc)
        midnight_pt = now_pt.replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            start_utc = midnight_pt.astimezone(timezone.utc)
        except Exception:
            start_utc = midnight_pt

        start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        res = service.projects().timeSeries().list(
            name=f"projects/{project_id}",
            filter='metric.type = "serviceruntime.googleapis.com/quota/rate/net_usage" AND resource.labels.service = "youtube.googleapis.com"',
            interval_startTime=start_str,
            interval_endTime=end_str
        ).execute()

        uploads_today = 0
        for ts in res.get("timeSeries", []):
            for pt in ts.get("points", []):
                val = pt.get("value", {}).get("int64Value", 0)
                uploads_today += int(val)

        units_used = uploads_today * YOUTUBE_UPLOAD_COST
        remaining_units = max(0, YOUTUBE_DAILY_LIMIT - units_used)
        uploads_left = remaining_units // YOUTUBE_UPLOAD_COST

        data = {
            "units_used": units_used,
            "limit": YOUTUBE_DAILY_LIMIT,
            "remaining_units": remaining_units,
            "uploads_remaining": uploads_left,
            "percent": round((units_used / YOUTUBE_DAILY_LIMIT) * 100, 1),
            "upload_cost": YOUTUBE_UPLOAD_COST,
            "note": f"{uploads_left} uploads left on {YOUTUBE_DAILY_LIMIT:,} quota (1,600 units/upload)",
            "is_live": True,
            "source": "google_cloud_monitoring"
        }
        _gcp_monitoring_cache = {
            "timestamp": now_ts,
            "data": data
        }
        return data
    except Exception as e:
        # Fallback cleanly to local tracker
        return None

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

def get_usage_summary(tracker_file: Optional[str] = None, allow_live_gcp: bool = True) -> Dict:
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

    # Check for genuine live GCP Monitoring quota for YouTube (Admin only)
    live_yt = fetch_live_gcp_youtube_quota() if allow_live_gcp else None
    if live_yt:
        yt_summary = live_yt
    else:
        yt_limit = data.get("youtube_limit", YOUTUBE_DAILY_LIMIT)
        yt_used = data.get("youtube_units", 0)
        yt_rem = max(0, yt_limit - yt_used)
        yt_pct = round((yt_used / yt_limit) * 100, 1) if yt_limit > 0 else 0.0
        uploads_left = yt_rem // YOUTUBE_UPLOAD_COST
        yt_summary = {
            "units_used": yt_used,
            "limit": yt_limit,
            "remaining_units": yt_rem,
            "uploads_remaining": uploads_left,
            "percent": yt_pct,
            "upload_cost": YOUTUBE_UPLOAD_COST,
            "note": f"{uploads_left} uploads left on {yt_limit:,} quota (1,600 units/upload)",
            "is_live": False,
            "source": "local_tracker"
        }

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
        "youtube": yt_summary
    }
