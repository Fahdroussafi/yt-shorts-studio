import os
import sys
import re
import json
import time
import hmac
import hashlib
import base64
import random
import asyncio
import urllib.request
import urllib.error
import urllib.parse
import shutil
import requests
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Response, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load environment variables from .env if present
def _load_env_file(path: str = None):
    if not path:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass

_load_env_file()

# Auth & Platform Configuration
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://127.0.0.1:8051")
JWT_SECRET = os.environ.get("JWT_SECRET", "yt-shorts-studio-secret-key-2026")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@admin.com").strip().lower()
DEFAULT_BRAND_NAME = os.environ.get("DEFAULT_BRAND_NAME", "ShadowMind").strip()
DEFAULT_CHANNEL_HANDLE = os.environ.get("DEFAULT_CHANNEL_HANDLE", "@TheShadowMindHQ-Hub").strip()
DEFAULT_CHANNEL_URL = os.environ.get("DEFAULT_CHANNEL_URL", f"https://www.youtube.com/{DEFAULT_CHANNEL_HANDLE}").strip()
DEFAULT_REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost").strip()

def verify_jwt_token(token: str) -> dict:
    """Verifies HS256 JWT signature and expiration. Standard library only."""
    if not token or not isinstance(token, str):
        return None
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        message = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            JWT_SECRET.encode("utf-8"),
            message,
            hashlib.sha256
        ).digest()
        
        rem = len(sig_b64) % 4
        sig_padded = sig_b64 + ("=" * (4 - rem) if rem else "")
        actual_sig = base64.urlsafe_b64decode(sig_padded)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        rem_p = len(payload_b64) % 4
        payload_padded = payload_b64 + ("=" * (4 - rem_p) if rem_p else "")
        payload_json = base64.urlsafe_b64decode(payload_padded).decode("utf-8")
        payload = json.loads(payload_json)
        
        if "exp" in payload and time.time() > payload["exp"]:
            return None
            
        return payload
    except Exception:
        return None

def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: Valid JWT required")
    token = authorization[7:].strip()
    user = verify_jwt_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: Invalid or expired JWT")
    return user

# Workspace Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
ENGINE_DIR = os.path.join(BASE_DIR, "shorts_engine")
DASHBOARD_DIST = os.path.join(BASE_DIR, "dashboard", "dist")

sys.path.append(TOOLS_DIR)
sys.path.append(ENGINE_DIR)

app = FastAPI(title="ShadowMind YouTube Shorts Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# MULTI-TENANT STORAGE MANAGEMENT
# ==========================================
USERS_DATA_DIR = os.path.join(BASE_DIR, "users_data")
os.makedirs(USERS_DATA_DIR, exist_ok=True)
LEGACY_CLAIM_FILE = os.path.join(USERS_DATA_DIR, ".legacy_claimed.json")

# Fallback global paths
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")

def get_user_id(user: dict) -> str:
    sub = user.get("sub") or user.get("id") or user.get("email") or "default_user"
    return re.sub(r'[^a-zA-Z0-9_-]', '_', str(sub))

def is_legacy_owner(uid: str, email: Optional[str] = None) -> bool:
    if email and email.lower() == ADMIN_EMAIL:
        return True
    if os.path.exists(LEGACY_CLAIM_FILE):
        try:
            with open(LEGACY_CLAIM_FILE, "r", encoding="utf-8") as f:
                claim_data = json.load(f)
            return claim_data.get("owner_id") == uid or (email and claim_data.get("email") == email)
        except Exception:
            return False
    return False

def get_user_paths(user: dict) -> dict:
    uid = get_user_id(user)
    u_dir = os.path.join(USERS_DATA_DIR, uid)
    v_dir = os.path.join(u_dir, "videos")
    os.makedirs(v_dir, exist_ok=True)

    email = user.get("email", "").lower()
    is_admin = (email == ADMIN_EMAIL)

    # Initial Migration Check: Only admin inherits the existing platform channel and shorts
    if not os.path.exists(LEGACY_CLAIM_FILE) and is_admin:
        try:
            with open(LEGACY_CLAIM_FILE, "w", encoding="utf-8") as f:
                json.dump({"owner_id": uid, "claimed_at": time.time(), "email": user.get("email")}, f, indent=2)

            if os.path.exists(VIDEOS_DIR) and os.listdir(VIDEOS_DIR):
                for item in os.listdir(VIDEOS_DIR):
                    s = os.path.join(VIDEOS_DIR, item)
                    d = os.path.join(v_dir, item)
                    if os.path.isdir(s) and not os.path.exists(d):
                        shutil.copytree(s, d)

            for fname in ["video_mappings.json", "stats_cache.json", "usage_tracker.json", "gemini_api_key.txt", "token.json", "client_secret.json"]:
                s = os.path.join(BASE_DIR, fname)
                d = os.path.join(u_dir, fname)
                if os.path.exists(s) and not os.path.exists(d):
                    shutil.copy2(s, d)

            ch_info = {
                "channel_handle": DEFAULT_CHANNEL_HANDLE,
                "channel_url": DEFAULT_CHANNEL_URL
            }
            with open(os.path.join(u_dir, "channel_info.json"), "w", encoding="utf-8") as f:
                json.dump(ch_info, f, indent=2)
        except Exception as e:
            print(f"[Warning] Error during legacy claim: {e}")

    # Ensure baseline files exist for the user
    ch_path = os.path.join(u_dir, "channel_info.json")
    vm_path = os.path.join(u_dir, "video_mappings.json")
    sc_path = os.path.join(u_dir, "stats_cache.json")

    # If this user is the legacy owner, ensure mappings and stats are populated from root
    if is_legacy_owner(uid, user.get("email")):
        try:
            root_vm = os.path.join(BASE_DIR, "video_mappings.json")
            if (not os.path.exists(vm_path) or os.path.getsize(vm_path) <= 4) and os.path.exists(root_vm):
                shutil.copy2(root_vm, vm_path)

            root_sc = os.path.join(BASE_DIR, "stats_cache.json")
            if (not os.path.exists(sc_path) or os.path.getsize(sc_path) <= 4) and os.path.exists(root_sc):
                shutil.copy2(root_sc, sc_path)

            root_token = os.path.join(BASE_DIR, "token.json")
            user_token = os.path.join(u_dir, "token.json")
            if not os.path.exists(user_token) and os.path.exists(root_token):
                shutil.copy2(root_token, user_token)

            root_cs = os.path.join(BASE_DIR, "client_secret.json")
            user_cs = os.path.join(u_dir, "client_secret.json")
            if not os.path.exists(user_cs) and os.path.exists(root_cs):
                shutil.copy2(root_cs, user_cs)

            if not os.path.exists(ch_path) or os.path.getsize(ch_path) <= 4:
                with open(ch_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "channel_handle": DEFAULT_CHANNEL_HANDLE,
                        "channel_url": DEFAULT_CHANNEL_URL
                    }, f, indent=2)
        except Exception as e:
            print(f"[Warning] Error ensuring legacy files: {e}")

    if not os.path.exists(ch_path):
        with open(ch_path, "w", encoding="utf-8") as f:
            json.dump({"channel_handle": "", "channel_url": ""}, f, indent=2)

    if not os.path.exists(vm_path):
        with open(vm_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)

    if not os.path.exists(sc_path):
        with open(sc_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)

    return {
        "user_id": uid,
        "user_dir": u_dir,
        "videos_dir": v_dir,
        "mappings_file": vm_path,
        "stats_cache_file": sc_path,
        "usage_file": os.path.join(u_dir, "usage_tracker.json"),
        "key_file": os.path.join(u_dir, "gemini_api_key.txt"),
        "token_file": os.path.join(u_dir, "token.json"),
        "client_secret_file": os.path.join(u_dir, "client_secret.json"),
        "channel_file": ch_path,
        "topic_history_file": os.path.join(u_dir, "topic_history.json"),
        "clip_history_file": os.path.join(u_dir, "clip_history.json")
    }

def load_user_stats_cache(stats_file: str) -> dict:
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_user_stats_cache(cache: dict, stats_file: str):
    try:
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def get_user_video_mappings(mappings_file: str) -> dict:
    if os.path.exists(mappings_file):
        try:
            with open(mappings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_user_video_mapping(mappings_file: str, video_id: str, yt_id: str, status: str, publish_at: Optional[str] = None):
    mappings = get_user_video_mappings(mappings_file)
    entry = {"yt_id": yt_id, "default_status": status}
    if publish_at:
        entry["publish_at"] = publish_at
    elif video_id in mappings and "publish_at" in mappings[video_id]:
        entry["publish_at"] = mappings[video_id]["publish_at"]
    mappings[video_id] = entry
    try:
        with open(mappings_file, "w", encoding="utf-8") as f:
            json.dump(mappings, f, indent=2)
    except Exception:
        pass

def get_user_channel_info(channel_file: str) -> dict:
    if os.path.exists(channel_file):
        try:
            with open(channel_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"channel_handle": "", "channel_url": ""}

def get_user_brand(paths: dict, user: Optional[dict] = None) -> tuple:
    """
    Returns (brand_name, brand_handle).
    brand_name: clean name for spoken scripts (e.g. "ShadowMind" or "GameVortex")
    brand_handle: @handle for descriptions and titles (e.g. "@TheShadowMindHQ-Hub" or "@GameVortex")
    """
    ch_info = get_user_channel_info(paths.get("channel_file", ""))
    handle = (ch_info.get("channel_handle") or "").strip()

    if handle:
        clean = handle.lstrip("@").strip()
        if clean.lower() in [DEFAULT_CHANNEL_HANDLE.lower().lstrip("@"), DEFAULT_BRAND_NAME.lower()]:
            return DEFAULT_BRAND_NAME, DEFAULT_CHANNEL_HANDLE
        return clean, (f"@{clean}" if not handle.startswith("@") else handle)

    uid = paths.get("user_id", "")
    if uid and is_legacy_owner(uid):
        return DEFAULT_BRAND_NAME, DEFAULT_CHANNEL_HANDLE

    if user:
        name = (user.get("name") or "").strip()
        if name and name.lower() not in ["admin", "root", "user"]:
            clean_name = name.lstrip("@").strip()
            return clean_name, f"@{clean_name}"
        email = (user.get("email") or "").strip()
        if email:
            prefix = email.split("@")[0].strip()
            if prefix and prefix.lower() not in ["admin", "root"]:
                cap_p = prefix.capitalize()
                return cap_p, f"@{cap_p}"

    return "MyChannel", "@MyChannel"

PRODUCTION_TASKS: Dict[str, dict] = {}


# ==========================================
# MODELS
# ==========================================
class ProduceRequest(BaseModel):
    video_id: str
    script_text: str
    clip_keywords: List[str]
    title: str
    description: str
    pinned_comment: str
    voice: Optional[str] = "en-US-ChristopherNeural"
    niche: Optional[str] = "dark_psychology"


class UploadRequest(BaseModel):
    video_id: str
    privacy_status: str = "public"
    publish_at: Optional[str] = None


class AIKeyRequest(BaseModel):
    api_key: str


class IdeaGenerateRequest(BaseModel):
    niche: str
    concept: Optional[str] = None
    surprise: Optional[bool] = False


class ChannelSettingsRequest(BaseModel):
    channel_handle: str
    channel_url: Optional[str] = None


class YouTubeTokenRequest(BaseModel):
    token_json: str


class OAuthCallbackRequest(BaseModel):
    code_or_url: str


def extract_client_credentials(cs_data: dict) -> tuple:
    cfg = cs_data.get("installed") or cs_data.get("web") or cs_data
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    redirect_uris = cfg.get("redirect_uris", [DEFAULT_REDIRECT_URI])
    redirect_uri = redirect_uris[0] if redirect_uris else DEFAULT_REDIRECT_URI
    return client_id, client_secret, redirect_uri


def get_auth_url_for_client(client_id: str, redirect_uri: str = DEFAULT_REDIRECT_URI) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.upload",
        "access_type": "offline",
        "prompt": "consent"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


# ==========================================
# VIDEO STREAMING (HTTP 206 Partial Content)
# ==========================================
def range_stream(file_path: str, start: int, end: int, chunk_size: int = 1024 * 64):
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            bytes_to_read = min(chunk_size, remaining)
            data = f.read(bytes_to_read)
            if not data:
                break
            remaining -= len(data)
            yield data


# ==========================================
# ENDPOINTS
# ==========================================

# -------------------------------------------------------------
# NestJS Auth Proxy (Seamless same-origin authentication relay)
# -------------------------------------------------------------
@app.api_route("/api/auth/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def auth_proxy(full_path: str, req: Request):
    if req.method == "OPTIONS":
        return JSONResponse({"status": "ok"})
    
    target_url = f"{AUTH_SERVICE_URL}/api/auth/{full_path}"
    query = str(req.query_params)
    if query:
        target_url += f"?{query}"
        
    body = await req.body()
    headers = {
        "Content-Type": req.headers.get("Content-Type", "application/json")
    }
    if "Authorization" in req.headers:
        headers["Authorization"] = req.headers["Authorization"]
        
    def _forward():
        urllib_req = urllib.request.Request(
            url=target_url,
            data=body if body else None,
            headers=headers,
            method=req.method
        )
        try:
            with urllib.request.urlopen(urllib_req, timeout=10) as resp:
                resp_data = resp.read()
                return resp.status, resp_data, resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers.get("Content-Type", "application/json")
        except Exception as e:
            err_json = json.dumps({
                "statusCode": 503,
                "message": f"NestJS Auth Service offline on {AUTH_SERVICE_URL}: {str(e)}"
            }).encode("utf-8")
            return 503, err_json, "application/json"

    status_code, content, content_type = await asyncio.to_thread(_forward)
    return Response(content=content, status_code=status_code, media_type=content_type)

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": time.time(), "engine": "ShadowMind Studio v1.0"}


@app.get("/api/stats")
def get_channel_stats(user: dict = Depends(require_auth)):
    """Scrapes real-time public stats from YouTube with disk-backed caching fallback (User Scoped)."""
    paths = get_user_paths(user)
    audit_results = []
    total_views = 0
    mappings = get_user_video_mappings(paths["mappings_file"])
    stats_cache = load_user_stats_cache(paths["stats_cache_file"])
    channel_info = get_user_channel_info(paths["channel_file"])
    updated_cache = False
    updated_mappings = False

    for short_key, info in mappings.items():
        yt_id = info["yt_id"]
        cached = stats_cache.get(short_key, {})
        
        # Start with cached values
        views = cached.get("views", 0)
        likes = cached.get("likes", "0")
        title = ""
        is_live = (info.get("default_status") == "LIVE")
        is_unplayable = False

        url = f"https://www.youtube.com/watch?v={yt_id}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        })
        
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                v_match = re.search(r'"viewCount":\s*"(\d+)"', html)
                if v_match:
                    new_views = int(v_match.group(1))
                    if new_views >= views:
                        views = new_views

                l_match = re.search(r'"accessibility":\{"accessibilityData":\{"label":"(\d+[\d,]*\s*likes?)"\}\}', html)
                if l_match:
                    likes = l_match.group(1)

                t_match = re.search(r'<meta name="title" content="(.*?)">', html)
                if not t_match:
                    t_match = re.search(r'<title>(.*?)</title>', html)
                if t_match:
                    title = t_match.group(1).replace(" - YouTube", "").strip()

                is_unavailable = "Video unavailable" in html or '"status":"UNPLAYABLE"' in html
                if not is_unavailable and ('"viewCount"' in html or views > 0):
                    is_live = True
        except Exception:
            # Fall back to stats_cache on 429 rate limit or timeout
            pass

        total_views += views

        if not title:
            meta_path = os.path.join(paths["videos_dir"], short_key, "seo_metadata.txt")
            if os.path.exists(meta_path):
                try:
                    c = open(meta_path, "r", encoding="utf-8").read()
                    t_m = re.search(r'TITLE:\s*(.*?)(?=\n\n|\nDESCRIPTION:|$)', c, re.DOTALL)
                    if t_m:
                        title = t_m.group(1).strip()
                except Exception:
                    pass
        if not title:
            title = f"{short_key} #shorts"

        dir_path = os.path.join(paths["videos_dir"], short_key)
        mp4_files = [x for x in os.listdir(dir_path) if x.endswith(".mp4")] if os.path.exists(dir_path) else []
        file_size_mb = 0
        if mp4_files:
            target_mp4 = next((x for x in mp4_files if short_key in x), mp4_files[0])
            file_size_mb = round(os.path.getsize(os.path.join(dir_path, target_mp4)) / (1024 * 1024), 2)
        motion_type = "Real-Motion HD" if file_size_mb > 10 else "Still Pilot"

        # Check if scheduled for future
        has_future_publish = False
        if info.get("publish_at"):
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(info["publish_at"].replace("Z", "+00:00"))
                if dt > datetime.now(timezone.utc):
                    has_future_publish = True
            except Exception:
                pass

        if has_future_publish:
            is_scheduled = True
        elif info.get("default_status") == "SCHEDULED":
            # If marked SCHEDULED but publish_at is past, it is no longer scheduled
            is_scheduled = not bool(info.get("publish_at"))
        else:
            is_scheduled = False

        if is_scheduled:
            status_val = "SCHEDULED"
        elif is_live or info.get("default_status") == "LIVE" or (info.get("publish_at") and not has_future_publish):
            status_val = "LIVE"
            if info.get("default_status") != "LIVE":
                info["default_status"] = "LIVE"
                updated_mappings = True
        else:
            status_val = info.get("default_status", "LOCAL_READY")

        audit_results.append({
            "short_id": short_key,
            "yt_id": yt_id,
            "title": title,
            "views": views,
            "likes": likes,
            "motion_type": motion_type,
            "status": status_val,
            "publish_at": info.get("publish_at"),
            "url": f"https://youtube.com/shorts/{yt_id}"
        })

    if updated_mappings:
        try:
            with open(paths["mappings_file"], "w", encoding="utf-8") as f:
                json.dump(mappings, f, indent=2)
        except Exception:
            pass

    if updated_cache:
        save_user_stats_cache(stats_cache, paths["stats_cache_file"])

    channel_handle = channel_info.get("channel_handle") or ""
    channel_url = channel_info.get("channel_url") or ""

    # Fetch subscriber count for user's configured channel
    subscribers = "Not Connected"
    if channel_handle:
        try:
            handle_clean = channel_handle if channel_handle.startswith("@") else f"@{channel_handle}"
            ch_req = urllib.request.Request(f"https://www.youtube.com/{handle_clean}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(ch_req, timeout=6) as resp:
                ch_html = resp.read().decode("utf-8", errors="ignore")
                sub_m = re.search(r'"subscriberCountText":\{"accessibility":\{"accessibilityData":\{"label":"(.*?)"\}\}', ch_html)
                if sub_m:
                    subscribers = sub_m.group(1)
        except Exception:
            subscribers = "Connected"

    return {
        "channel_handle": channel_handle if channel_handle else "No Channel Connected",
        "channel_url": channel_url,
        "subscribers": subscribers,
        "total_views": total_views,
        "videos": audit_results
    }


@app.get("/api/videos")
def list_videos(user: dict = Depends(require_auth)):
    """Lists user-scoped shorts directories, metadata, file sizes, and video files."""
    paths = get_user_paths(user)
    v_dir = paths["videos_dir"]
    if not os.path.exists(v_dir):
        return []

    folders = sorted(os.listdir(v_dir))
    results = []
    mappings = get_user_video_mappings(paths["mappings_file"])

    for f in folders:
        dir_path = os.path.join(v_dir, f)
        if not os.path.isdir(dir_path):
            continue

        mp4_files = [x for x in os.listdir(dir_path) if x.endswith(".mp4")]
        if not mp4_files:
            continue

        # Prefer named mp4 matching folder name or latest
        target_mp4 = next((x for x in mp4_files if f in x), mp4_files[0])
        mp4_path = os.path.join(dir_path, target_mp4)
        file_size_mb = round(os.path.getsize(mp4_path) / (1024 * 1024), 2)
        mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(mp4_path)))

        # Metadata
        meta_path = os.path.join(dir_path, "seo_metadata.txt")
        title = f
        description = ""
        pinned_comment = ""
        tags = []

        if os.path.exists(meta_path):
            try:
                content = open(meta_path, "r", encoding="utf-8").read()
                t_match = re.search(r'TITLE:\s*(.*?)(?=\n\n|\nDESCRIPTION:|$)', content, re.DOTALL)
                d_match = re.search(r'DESCRIPTION:\s*(.*?)(?=\n\nPINNED COMMENT:|$)', content, re.DOTALL)
                c_match = re.search(r'PINNED COMMENT:\s*(.*)', content, re.DOTALL)

                if t_match:
                    title = t_match.group(1).strip()
                if d_match:
                    description = d_match.group(1).strip()
                    tags = re.findall(r'#(\w+)', description)
                if c_match:
                    pinned_comment = c_match.group(1).strip()
            except Exception:
                pass

        mapping = mappings.get(f, {})
        yt_id = mapping.get("yt_id")
        motion_type = "Real-Motion HD" if file_size_mb > 10 else "Still Pilot"

        results.append({
            "id": f,
            "filename": target_mp4,
            "size_mb": file_size_mb,
            "modified": mod_time,
            "title": title,
            "description": description,
            "tags": tags,
            "pinned_comment": pinned_comment,
            "motion_type": motion_type,
            "yt_id": yt_id,
            "yt_url": f"https://youtube.com/shorts/{yt_id}" if yt_id else None,
            "status": mapping.get("default_status", "LOCAL_READY")
        })

    return results


@app.api_route("/api/videos/{short_id}/stream", methods=["GET", "HEAD"])
def stream_video(short_id: str, req: Request, range: Optional[str] = Header(None)):
    """Streams the short MP4 with HTTP 206 partial range support across user partitions."""
    # Check if authorization token provided
    token = None
    auth_h = req.headers.get("Authorization")
    if auth_h and auth_h.startswith("Bearer "):
        token = auth_h[7:].strip()
    elif req.query_params.get("token"):
        token = req.query_params.get("token").strip()

    dir_path = None
    if token:
        user = verify_jwt_token(token)
        if user:
            paths = get_user_paths(user)
            p = os.path.join(paths["videos_dir"], short_id)
            if os.path.exists(p):
                dir_path = p

    # Fallback search across user partitions or legacy videos
    if not dir_path or not os.path.exists(dir_path):
        if os.path.exists(USERS_DATA_DIR):
            for u in os.listdir(USERS_DATA_DIR):
                cand = os.path.join(USERS_DATA_DIR, u, "videos", short_id)
                if os.path.exists(cand):
                    dir_path = cand
                    break
    if not dir_path or not os.path.exists(dir_path):
        cand = os.path.join(VIDEOS_DIR, short_id)
        if os.path.exists(cand):
            dir_path = cand

    if not dir_path or not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="Short directory not found")

    mp4_files = [x for x in os.listdir(dir_path) if x.endswith(".mp4")]
    if not mp4_files:
        raise HTTPException(status_code=404, detail="No MP4 found in directory")

    target_mp4 = next((x for x in mp4_files if short_id in x), mp4_files[0])
    video_path = os.path.join(dir_path, target_mp4)
    file_size = os.path.getsize(video_path)

    if not range:
        return FileResponse(video_path, media_type="video/mp4", filename=target_mp4)

    range_match = re.match(r"bytes=(\d+)-(\d*)", range)
    if not range_match:
        return Response(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)

    start = int(range_match.group(1))
    end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

    if start >= file_size:
        return Response(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)

    content_length = end - start + 1
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
    }

    return StreamingResponse(
        range_stream(video_path, start, end),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        headers=headers,
        media_type="video/mp4"
    )


@app.delete("/api/videos/{short_id}")
def delete_video(short_id: str, user: dict = Depends(require_auth)):
    """Deletes a short directory and all its files from disk (User Scoped)."""
    paths = get_user_paths(user)
    dir_path = os.path.join(paths["videos_dir"], short_id)
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="Short directory not found")
    try:
        shutil.rmtree(dir_path)
    except Exception as e:
        import gc
        gc.collect()
        time.sleep(0.3)
        try:
            shutil.rmtree(dir_path)
        except Exception:
            # Force delete via shell
            subprocess.run(["cmd", "/c", "rd", "/s", "/q", dir_path], capture_output=True)
            if os.path.exists(dir_path):
                raise HTTPException(status_code=500, detail=f"Failed to delete short: {str(e)}")

    # Remove from user's mappings
    mappings = get_user_video_mappings(paths["mappings_file"])
    if short_id in mappings:
        del mappings[short_id]
        try:
            with open(paths["mappings_file"], "w", encoding="utf-8") as f:
                json.dump(mappings, f, indent=2)
        except Exception:
            pass

    return {"success": True, "message": f"Short '{short_id}' deleted successfully."}



@app.get("/api/niches")
def get_niches(_user: dict = Depends(require_auth)):
    """Returns curated viral shorts niches with templates, hooks, and RPM metrics."""
    from idea_bank import NICHE_PROFILES
    out = []
    for p in NICHE_PROFILES.values():
        out.append({
            "id": p["id"],
            "name": p["name"],
            "rpm_range": p.get("rpm_range", "$0.18 - $0.35"),
            "retention_rate": p.get("retention_rate", "60% - 75%"),
            "voice_recommended": p.get("voice_recommended", "en-US-ChristopherNeural"),
            "description": p.get("description", ""),
            "hook_formulas": p.get("hook_formulas", []),
            "sample_keywords": p.get("visual_bank", [])[:5]
        })
    return out


def verify_gemini_api_key(key: str) -> tuple:
    if not key or not isinstance(key, str):
        return False, "API key cannot be empty."
    clean_key = key.strip()
    if len(clean_key) < 20:
        return False, "API key format invalid (too short). Google keys start with AIzaSy..."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={clean_key}"
    payload = {"contents": [{"parts": [{"text": "ping"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            return True, "Valid API key."

        # Fallback check on models list in case model naming differs
        fb_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
        fb_res = requests.get(fb_url, timeout=8)
        if fb_res.status_code == 200:
            return True, "Valid API key."

        try:
            err = res.json().get("error", {})
            msg = err.get("message", "API key not valid.")
            return False, msg
        except Exception:
            return False, f"Google rejected key (HTTP {res.status_code})"
    except Exception as e:
        return False, f"Could not reach Google API: {str(e)}"


@app.get("/api/settings/ai")
def get_ai_settings(user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    from gemini_generator import get_gemini_key
    user_custom_key = get_gemini_key(paths["key_file"], allow_fallback=False)

    # Auto-purge corrupted or fake keys (e.g. '123456' or 'sfsfsfdf')
    if user_custom_key and len(user_custom_key.strip()) < 20:
        try:
            if os.path.exists(paths["key_file"]):
                os.remove(paths["key_file"])
        except Exception:
            pass
        user_custom_key = None

    is_owner = is_legacy_owner(paths["user_id"], user.get("email"))
    system_key = get_gemini_key(paths["key_file"], allow_fallback=is_owner)
    key = user_custom_key or system_key
    masked = f"{key[:6]}...{key[-4:]}" if key and len(key) > 10 else None
    return {
        "has_key": bool(key),
        "is_custom_key": bool(user_custom_key),
        "masked_key": masked,
        "model": "gemini-3.5-flash-lite (Instant 0.8s Generation)",
        "status": "AI Flash Online (Custom Key)" if user_custom_key else ("AI Flash Online (System Pre-Configured)" if system_key else "Local Generator Active")
    }


@app.post("/api/settings/ai")
def save_ai_settings(req: AIKeyRequest, user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    key = req.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    is_valid, err_msg = verify_gemini_api_key(key)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid Gemini API Key: {err_msg}")

    from gemini_generator import save_gemini_key
    save_gemini_key(key, paths["key_file"])
    return {"success": True, "message": "Gemini Flash API Key verified with Google and saved successfully!"}


@app.delete("/api/settings/ai")
def delete_ai_settings(user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    if os.path.exists(paths["key_file"]):
        os.remove(paths["key_file"])
    return {"success": True, "message": "Gemini API Key cleared."}


@app.get("/api/settings/channel")
def get_channel_settings(user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    info = get_user_channel_info(paths["channel_file"])
    has_token = os.path.exists(paths["token_file"]) or (is_legacy_owner(paths["user_id"], user.get("email")) and os.path.exists(TOKEN_FILE))
    has_cs = os.path.exists(paths["client_secret_file"]) or os.path.exists(CLIENT_SECRETS_FILE)
    return {
        "channel_handle": info.get("channel_handle", ""),
        "channel_url": info.get("channel_url", ""),
        "has_youtube_token": has_token,
        "has_client_secret": has_cs
    }


@app.post("/api/settings/channel")
def save_channel_settings(req: ChannelSettingsRequest, user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    handle = req.channel_handle.strip()
    if handle and not handle.startswith("@"):
        handle = "@" + handle
    url = req.channel_url.strip() if req.channel_url else (f"https://www.youtube.com/{handle}" if handle else "")
    info = {"channel_handle": handle, "channel_url": url}
    with open(paths["channel_file"], "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    return {"success": True, "channel_handle": handle, "channel_url": url}


@app.get("/api/settings/youtube-auth-url")
def get_youtube_auth_url(user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    cs_file = paths["client_secret_file"]
    if not os.path.exists(cs_file):
        cs_file = CLIENT_SECRETS_FILE
    if not os.path.exists(cs_file):
        return {"has_client_secret": False, "auth_url": None}

    try:
        with open(cs_file, "r", encoding="utf-8") as f:
            cs_data = json.load(f)
        client_id, _, redirect_uri = extract_client_credentials(cs_data)
        if client_id:
            return {
                "has_client_secret": True,
                "auth_url": get_auth_url_for_client(client_id, redirect_uri),
                "client_id": client_id
            }
    except Exception:
        pass
    return {"has_client_secret": False, "auth_url": None}


@app.post("/api/settings/youtube-token")
def save_youtube_token(req: YouTubeTokenRequest, user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    try:
        parsed = json.loads(req.token_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Uploaded JSON must be a valid JSON object.")

    # Detect if user uploaded client_secret.json instead of token.json
    is_client_secret = (
        "installed" in parsed or 
        "web" in parsed or 
        ("client_id" in parsed and "client_secret" in parsed and "refresh_token" not in parsed and "token" not in parsed)
    )

    if is_client_secret:
        with open(paths["client_secret_file"], "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)

        client_id, client_secret, redirect_uri = extract_client_credentials(parsed)
        if not client_id:
            raise HTTPException(status_code=400, detail="Missing client_id in client_secret.json")

        auth_url = get_auth_url_for_client(client_id, redirect_uri)
        return {
            "success": True,
            "type": "client_secret",
            "auth_required": True,
            "auth_url": auth_url,
            "client_id": client_id,
            "message": "Client secret received! Authorize with Google to complete channel connection."
        }

    # Otherwise treat as token.json
    has_token = ("token" in parsed or "access_token" in parsed or "refresh_token" in parsed)
    if not has_token:
        raise HTTPException(status_code=400, detail="Uploaded JSON is neither a valid token.json nor client_secret.json")

    if "access_token" in parsed and "token" not in parsed:
        parsed["token"] = parsed["access_token"]

    with open(paths["token_file"], "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)

    return {
        "success": True,
        "type": "token",
        "auth_required": False,
        "message": "YouTube OAuth token connected successfully."
    }


@app.post("/api/settings/youtube-oauth-callback")
def handle_oauth_callback(req: OAuthCallbackRequest, user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    raw = req.code_or_url.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="No code or redirect URL provided.")

    code = raw
    if "code=" in raw:
        match = re.search(r'[?&]code=([^&]+)', raw)
        if match:
            code = urllib.parse.unquote(match.group(1))
        else:
            code = urllib.parse.unquote(raw.split("code=")[1].split("&")[0])

    cs_file = paths["client_secret_file"]
    if not os.path.exists(cs_file):
        cs_file = CLIENT_SECRETS_FILE
    if not os.path.exists(cs_file):
        raise HTTPException(status_code=400, detail="Missing client_secret.json. Please upload client secret first.")

    try:
        with open(cs_file, "r", encoding="utf-8") as f:
            cs_data = json.load(f)
        client_id, client_secret, redirect_uri = extract_client_credentials(cs_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read client credentials: {str(e)}")

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Invalid client credentials: missing client_id or client_secret.")

    # Exchange code with Google OAuth endpoint
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }).encode("utf-8")

    exchange_req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        with urllib.request.urlopen(exchange_req, timeout=15) as resp:
            token_resp = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        raise HTTPException(status_code=400, detail=f"Google token exchange failed ({e.code}): {err_msg}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google token exchange request failed: {str(e)}")

    access_token = token_resp.get("access_token")
    refresh_token = token_resp.get("refresh_token")
    if not access_token:
        raise HTTPException(status_code=400, detail=f"Google response missing access_token: {token_resp}")

    import datetime
    expires_in = token_resp.get("expires_in", 3600)
    expiry = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    scopes_list = [s for s in token_resp.get("scope", "https://www.googleapis.com/auth/youtube.upload").split(" ") if s]
    if not scopes_list:
        scopes_list = ["https://www.googleapis.com/auth/youtube.upload"]

    token_data = {
        "token": access_token,
        "refresh_token": refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": scopes_list,
        "universe_domain": "googleapis.com",
        "account": "",
        "expiry": expiry
    }

    with open(paths["token_file"], "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)

    return {
        "success": True,
        "message": "YouTube OAuth channel connected successfully!"
    }


@app.delete("/api/settings/youtube-token")
def disconnect_youtube(user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    if os.path.exists(paths["token_file"]):
        os.remove(paths["token_file"])
    return {"success": True, "message": "YouTube channel disconnected."}


@app.get("/api/usage")
def get_usage(user: dict = Depends(require_auth)):
    """Returns exact daily quota & credit consumption for Gemini and YouTube (User Scoped)."""
    paths = get_user_paths(user)
    from usage_tracker import get_usage_summary
    from gemini_generator import get_gemini_key

    is_owner = is_legacy_owner(paths["user_id"], user.get("email"))
    has_token = os.path.exists(paths["token_file"]) or (is_owner and os.path.exists(TOKEN_FILE))
    has_ai_key = bool(get_gemini_key(paths["key_file"], allow_fallback=is_owner))

    summary = get_usage_summary(paths["usage_file"])
    summary["youtube"]["connected"] = has_token
    summary["gemini"]["has_key"] = has_ai_key
    return summary


@app.get("/api/next-short-id")
def get_next_id(user: dict = Depends(require_auth)):
    """Calculates next sequential short folder ID automatically for the user's library."""
    paths = get_user_paths(user)
    from idea_bank import get_next_short_id
    next_id = get_next_short_id(paths["videos_dir"])
    return {"next_id": next_id}


@app.post("/api/ideas/generate")
def generate_idea(req: IdeaGenerateRequest, user: dict = Depends(require_auth)):
    """Generates dynamic viral script structure, SEO metadata, and clip keywords."""
    paths = get_user_paths(user)
    from idea_bank import NICHE_PROFILES, CONCEPTS_DATABASE, get_next_short_id, pick_concept_without_repeats, record_topic_history
    from gemini_generator import generate_with_gemini_flash
    from usage_tracker import record_gemini_request

    niche = req.niche
    # If user selected Surprise Me, preserve their selected niche! Only pick random if explicitly empty or 'random'
    if not niche or niche == "random" or (niche not in NICHE_PROFILES and niche not in CONCEPTS_DATABASE):
        niche = random.choice(list(NICHE_PROFILES.keys()))

    next_id = get_next_short_id(paths["videos_dir"])
    brand_name, brand_handle = get_user_brand(paths, user)
    is_owner = is_legacy_owner(paths["user_id"], user.get("email"))

    # 1. Try Gemini Flash AI first with user's key (fallback to system pre-configured key for admin only)
    ai_result = generate_with_gemini_flash(
        niche=niche,
        concept=req.concept,
        user_key_file=paths["key_file"],
        brand_name=brand_name,
        brand_handle=brand_handle,
        allow_fallback=is_owner,
        user_tracker_file=paths["usage_file"],
        surprise=bool(req.surprise),
        topic_history_file=paths.get("topic_history_file")
    )
    if ai_result:
        record_gemini_request(tracker_file=paths["usage_file"])
        final_script = ai_result.get("script", "").strip()
        profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
        outro_mandate = profile.get("outro_phrase", f"Follow {brand_name} for psychological rules that put you five steps ahead.").format(brand_name=brand_name)
        if brand_name.lower() not in final_script.lower():
            final_script = final_script.rstrip(" .,!?:;-") + f". {outro_mandate}"

        return {
            "source": ai_result.get("model_used", "gemini-3.5-flash-lite"),
            "next_id": next_id,
            "niche": niche,
            "title": ai_result.get("title", ""),
            "script": final_script,
            "keywords": ai_result.get("keywords", profile.get("visual_bank", ["dark", "mystery"])[:8]),
            "description": ai_result.get("description", ""),
            "pinned_comment": ai_result.get("pinned_comment", "Drop your thoughts below. 👇"),
            "voice": ai_result.get("voice", profile.get("voice_recommended", "en-US-ChristopherNeural"))
        }

    # 2. Smooth fallback to rich local combinatorial generator (History-aware)
    chosen = pick_concept_without_repeats(
        niche=niche,
        history_file=paths.get("topic_history_file"),
        brand_name=brand_name,
        brand_handle=brand_handle
    )

    if req.concept and req.concept.strip():
        chosen["title"] = f"{req.concept.strip().title()} #shorts"

    profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
    record_topic_history(paths.get("topic_history_file"), chosen["title"], niche, req.concept or "")

    return {
        "source": "local-generator",
        "next_id": next_id,
        "niche": niche,
        "title": chosen["title"],
        "script": chosen["script"],
        "keywords": chosen["keywords"],
        "description": chosen["description"],
        "pinned_comment": chosen["pinned_comment"],
        "voice": chosen.get("voice", profile.get("voice_recommended", "en-US-ChristopherNeural"))
    }


# Production Concurrency Limiter & FIFO Queue
# 1 concurrent render on 2-OCPU host reserves 1 full CPU for API, UI, and OS stability
MAX_CONCURRENT_RENDERS = int(os.environ.get("MAX_CONCURRENT_RENDERS", "1"))
RENDER_QUEUE_LIST: List[str] = []
_RENDER_SEMAPHORE: Optional[asyncio.Semaphore] = None

def get_render_semaphore() -> asyncio.Semaphore:
    global _RENDER_SEMAPHORE
    if _RENDER_SEMAPHORE is None:
        _RENDER_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_RENDERS)
    return _RENDER_SEMAPHORE


# Production Background Task Runner
async def run_production(task_id: str, req: ProduceRequest, target_videos_dir: str):
    RENDER_QUEUE_LIST.append(task_id)
    pos = len(RENDER_QUEUE_LIST)

    if pos > MAX_CONCURRENT_RENDERS:
        PRODUCTION_TASKS[task_id]["status"] = "queued"
        PRODUCTION_TASKS[task_id]["progress"] = 5
        PRODUCTION_TASKS[task_id]["queue_position"] = pos
        PRODUCTION_TASKS[task_id]["log"].append(f"[QUEUE] Server CPU busy. You are #{pos} in queue. Waiting for slot...")
    else:
        PRODUCTION_TASKS[task_id]["status"] = "processing"
        PRODUCTION_TASKS[task_id]["progress"] = 10
        PRODUCTION_TASKS[task_id]["log"].append("[QUEUE] Slot allocated. Starting production pipeline...")

    sem = get_render_semaphore()
    async with sem:
        try:
            PRODUCTION_TASKS[task_id]["status"] = "processing"
            if pos > MAX_CONCURRENT_RENDERS:
                PRODUCTION_TASKS[task_id]["log"].append("[QUEUE] Render slot ready. Starting production...")
            PRODUCTION_TASKS[task_id]["progress"] = 10
            PRODUCTION_TASKS[task_id]["log"].append("[1/5] Synthesizing voiceover with edge-tts...")

            from engine import generate_voice, get_audio_duration, build_ass_subtitles, strip_watermarks
            from produce_motion_short import download_clip_with_smart_fallback, load_clip_history, record_clip_usage, render_motion_video
            from idea_bank import NICHE_PROFILES

            target_dir = os.path.join(target_videos_dir, req.video_id)
            os.makedirs(target_dir, exist_ok=True)

            audio_file = os.path.join(target_dir, "voice.mp3")
            ass_file = os.path.join(target_dir, "captions.ass")
            output_mp4 = os.path.join(target_dir, f"{req.video_id}.mp4")
            meta_file = os.path.join(target_dir, "seo_metadata.txt")

            # Channel brand guarantee
            u_dir = os.path.dirname(target_videos_dir)
            ch_file = os.path.join(u_dir, "channel_info.json")
            user_paths_mock = {"channel_file": ch_file, "user_id": os.path.basename(u_dir)}
            brand_name, brand_handle = get_user_brand(user_paths_mock)

            clean_script = req.script_text.strip()
            if brand_name.lower() != DEFAULT_BRAND_NAME.lower():
                clean_script = re.sub(r'(?i)\btheshadowmindhq(?:-hub)?\b', brand_handle.lstrip("@"), clean_script)
                clean_script = re.sub(r'(?i)@ShadowMind\b', brand_handle, clean_script)
                clean_script = re.sub(rf'(?i)\b{DEFAULT_BRAND_NAME}\b', brand_name, clean_script)

            if brand_name.lower() not in clean_script.lower():
                clean_script = clean_script.rstrip(" .,!?:;-") + f". Follow {brand_name} for more."

            # 1. Voice
            words = await generate_voice(clean_script, audio_file, voice=req.voice or "en-US-ChristopherNeural", brand_name=brand_name)
            dur = get_audio_duration(audio_file)
            PRODUCTION_TASKS[task_id]["progress"] = 30
            PRODUCTION_TASKS[task_id]["log"].append(f"[2/5] Voice synthesized ({dur:.2f}s). Building ASS subtitles...")

            # 2. Subtitles
            build_ass_subtitles(words, ass_file)
            PRODUCTION_TASKS[task_id]["progress"] = 50

            # 3. Dynamic clip expansion & no-repeat selection
            niche = getattr(req, "niche", "dark_psychology") or "dark_psychology"
            profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
            niche_bank = profile.get("visual_bank", ["thinking", "shadows", "mirror", "dark-street", "candle"])

            # Target 8 to 10 cuts (~4 to 4.5s per scene for viral pacing)
            target_cuts = max(6, min(10, round(dur / 4.2)))
            expanded_keywords = list(req.clip_keywords) if req.clip_keywords else []
            while len(expanded_keywords) < target_cuts:
                fresh = random.choice([k for k in niche_bank if k not in expanded_keywords] or niche_bank)
                expanded_keywords.append(fresh)
            expanded_keywords = expanded_keywords[:target_cuts]

            PRODUCTION_TASKS[task_id]["log"].append(f"[3/5] Scraping & downloading {len(expanded_keywords)} unique stock clips (No-Repeat Algorithm)...")

            clip_history_file = os.path.join(u_dir, "clip_history.json")
            clip_history = load_clip_history(clip_history_file)
            used_in_video = set()
            chosen_urls = []
            clip_paths = []

            for idx, kw in enumerate(expanded_keywords):
                clip_path = os.path.join(target_dir, f"clip_{idx}.mp4")
                _, chosen_url = await asyncio.to_thread(
                    download_clip_with_smart_fallback,
                    kw,
                    clip_path,
                    niche,
                    used_in_video,
                    clip_history
                )
                chosen_urls.append(chosen_url)
                clip_paths.append(clip_path)

            record_clip_usage(clip_history_file, chosen_urls)

            PRODUCTION_TASKS[task_id]["progress"] = 70
            PRODUCTION_TASKS[task_id]["log"].append(f"[4/5] Rendering 1080x1920 vertical video ({len(clip_paths)} dynamic cuts with random offsets & flips)...")

            # 4. Render (Non-blocking async execution)
            await asyncio.to_thread(render_motion_video, clip_paths, audio_file, ass_file, output_mp4, dur)
            PRODUCTION_TASKS[task_id]["progress"] = 90
            PRODUCTION_TASKS[task_id]["log"].append("[5/5] Sanitizing metadata and stripping watermarks...")

            # 5. Clean
            await asyncio.to_thread(strip_watermarks, output_mp4)

            # 6. Save SEO
            title_to_save = req.title
            desc_to_save = req.description
            pinned_to_save = req.pinned_comment
            if brand_name.lower() != DEFAULT_BRAND_NAME.lower():
                for val_name in ["title", "desc", "pinned"]:
                    target_str = title_to_save if val_name == "title" else (desc_to_save if val_name == "desc" else pinned_to_save)
                    target_str = re.sub(r'(?i)\btheshadowmindhq(?:-hub)?\b', brand_handle.lstrip("@"), target_str)
                    target_str = re.sub(r'(?i)@ShadowMind\b', brand_handle, target_str)
                    target_str = re.sub(rf'(?i)\b{DEFAULT_BRAND_NAME}\b', brand_name, target_str)
                    if val_name == "title": title_to_save = target_str
                    elif val_name == "desc": desc_to_save = target_str
                    elif val_name == "pinned": pinned_to_save = target_str

            with open(meta_file, "w", encoding="utf-8") as f:
                f.write(f"TITLE:\n{title_to_save}\n\n")
                f.write(f"DESCRIPTION:\n{desc_to_save}\n\n")
                f.write(f"PINNED COMMENT:\n{pinned_to_save}\n")

            # Clean intermediate clips
            for cp in clip_paths:
                try:
                    if os.path.exists(cp):
                        os.remove(cp)
                except Exception:
                    pass

            mb = round(os.path.getsize(output_mp4) / (1024 * 1024), 2)
            PRODUCTION_TASKS[task_id]["status"] = "completed"
            PRODUCTION_TASKS[task_id]["progress"] = 100
            PRODUCTION_TASKS[task_id]["output_file"] = output_mp4
            PRODUCTION_TASKS[task_id]["log"].append(f"[SUCCESS] Real-motion short generated ({mb} MB): {output_mp4}")

        except Exception as e:
            PRODUCTION_TASKS[task_id]["status"] = "failed"
            PRODUCTION_TASKS[task_id]["error"] = str(e)
            PRODUCTION_TASKS[task_id]["log"].append(f"[ERROR] Production failed: {str(e)}")

        finally:
            if task_id in RENDER_QUEUE_LIST:
                RENDER_QUEUE_LIST.remove(task_id)


@app.post("/api/produce")
async def start_produce(req: ProduceRequest, background_tasks: BackgroundTasks, user: dict = Depends(require_auth)):
    """Triggers end-to-end motion short production in background (User Scoped)."""
    paths = get_user_paths(user)
    task_id = f"task_{req.video_id}_{int(time.time())}"
    PRODUCTION_TASKS[task_id] = {
        "task_id": task_id,
        "user_id": paths["user_id"],
        "video_id": req.video_id,
        "status": "queued",
        "progress": 0,
        "log": [],
        "output_file": None,
        "error": None
    }
    background_tasks.add_task(run_production, task_id, req, paths["videos_dir"])
    return {"task_id": task_id, "status": "queued", "message": f"Production of {req.video_id} queued."}


@app.get("/api/produce/status/{task_id}")
def get_produce_status(task_id: str, user: dict = Depends(require_auth)):
    paths = get_user_paths(user)
    if task_id not in PRODUCTION_TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    task = PRODUCTION_TASKS[task_id]
    if task.get("user_id") and task["user_id"] != paths["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied to this task")
    if task.get("status") == "queued" and task_id in RENDER_QUEUE_LIST:
        pos = RENDER_QUEUE_LIST.index(task_id) + 1
        task["queue_position"] = pos
    return task


@app.post("/api/upload")
def upload_to_youtube(req: UploadRequest, user: dict = Depends(require_auth)):
    """Uploads a generated short to YouTube (Public or Scheduled) using user's token.json."""
    paths = get_user_paths(user)
    dir_path = os.path.join(paths["videos_dir"], req.video_id)
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail=f"Short folder '{req.video_id}' not found")

    mp4_files = [x for x in os.listdir(dir_path) if x.endswith(".mp4")]
    if not mp4_files:
        raise HTTPException(status_code=404, detail="No MP4 file found in folder")

    target_mp4 = next((x for x in mp4_files if req.video_id in x), mp4_files[0])
    video_path = os.path.join(dir_path, target_mp4)

    # Read SEO
    meta_path = os.path.join(dir_path, "seo_metadata.txt")
    title = f"{req.video_id} #shorts"
    description = ""
    tags = ["shorts", "psychology", "darkpsychology"]

    if os.path.exists(meta_path):
        try:
            content = open(meta_path, "r", encoding="utf-8").read()
            t_m = re.search(r'TITLE:\s*(.*?)(?=\n\n|\nDESCRIPTION:|$)', content, re.DOTALL)
            d_m = re.search(r'DESCRIPTION:\s*(.*?)(?=\n\nPINNED COMMENT:|$)', content, re.DOTALL)
            if t_m:
                title = t_m.group(1).strip()
            if d_m:
                description = d_m.group(1).strip()
                extracted_tags = re.findall(r'#(\w+)', description)
                if extracted_tags:
                    tags = extracted_tags
        except Exception:
            pass

    # Strict YouTube Token Isolation:
    # Only legacy owner can fall back to root token.json if user token is missing.
    # Non-owner accounts MUST have their own token.json in their user directory.
    if os.path.exists(paths["token_file"]):
        token_to_use = paths["token_file"]
    elif is_legacy_owner(paths["user_id"], user.get("email")) and os.path.exists(TOKEN_FILE):
        token_to_use = TOKEN_FILE
    else:
        raise HTTPException(
            status_code=400,
            detail="YouTube channel not connected for this account. Please go to Channel Settings and connect your YouTube OAuth token (token.json) to upload."
        )

    try:
        if req.publish_at:
            from upload_scheduled import upload_scheduled_short
            yt_url = upload_scheduled_short(video_path, title, description, tags, req.publish_at, token_file=token_to_use)
        else:
            from uploader import upload_short
            yt_url = upload_short(video_path, title, description, tags, req.privacy_status, token_file=token_to_use)

        yt_id = yt_url.split("/")[-1].split("?")[0]
        status_label = "SCHEDULED" if req.publish_at else req.privacy_status.upper()
        save_user_video_mapping(paths["mappings_file"], req.video_id, yt_id, status_label, req.publish_at)

        try:
            from usage_tracker import record_youtube_upload
            record_youtube_upload(tracker_file=paths["usage_file"])
        except Exception:
            pass

        return {
            "success": True,
            "video_id": req.video_id,
            "url": yt_url,
            "yt_id": yt_id,
            "privacy": req.privacy_status,
            "scheduled": req.publish_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount React static files if built
if os.path.exists(DASHBOARD_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DASHBOARD_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_react_spa(full_path: str):
        file_path = os.path.join(DASHBOARD_DIST, full_path)
        if full_path and os.path.exists(file_path):
            return FileResponse(file_path)
        return FileResponse(
            os.path.join(DASHBOARD_DIST, "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )

if __name__ == "__main__":
    import uvicorn
    server_port = int(os.environ.get("PORT", "8050"))
    server_host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("server:app", host=server_host, port=server_port, app_dir=BASE_DIR, reload_dirs=[BASE_DIR], reload=True)
