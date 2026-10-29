import os
import sys
import re
import json
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service(token_file: str = None):
    target_token = token_file if token_file is not None else TOKEN_FILE
    if not os.path.exists(target_token):
        raise FileNotFoundError(f"Missing YouTube OAuth credentials ({target_token}). Please connect your channel.")
    
    creds = Credentials.from_authorized_user_file(target_token, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            creds.refresh(Request())
            with open(target_token, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
        else:
            raise RuntimeError("Credentials invalid and cannot refresh. Re-authenticate.")
            
    return build("youtube", "v3", credentials=creds)


def upload_short(video_path: str, title: str, description: str, tags: list, privacy_status: str = "public", token_file: str = None):
    youtube = get_authenticated_service(token_file)
    
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "27",  # 27 = Education (High CPM & view retention)
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True
        }
    }
    
    print(f"\n==========================================")
    print(f"Uploading: {os.path.basename(video_path)}")
    print(f"Title: {title}")
    print(f"Privacy: {privacy_status.upper()}")
    print(f"Tags count: {len(tags)}")
    print(f"==========================================")
    
    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024 * 2,  # 2MB chunks for resumable upload
        resumable=True,
        mimetype="video/mp4"
    )
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
        notifySubscribers=True
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"\n>>> LIVE: {video_url} <<<\n")
    return video_url


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload YouTube Short")
    parser.add_argument("--video", required=True)
    parser.add_argument("--meta")
    parser.add_argument("--privacy", default="public")
    args = parser.parse_args()
    
    title = "Dark Psychology Short #shorts"
    description = "Subscribe to @ShadowMind for daily psychology breakdowns."
    tags = ["dark psychology", "psychology facts", "shorts"]
    
    if args.meta and os.path.exists(args.meta):
        content = open(args.meta, encoding="utf-8").read()
        t_m = re.search(r"TITLE:\n(.*?)\n\n", content, re.DOTALL)
        d_m = re.search(r"DESCRIPTION:\n(.*?)\n\nPINNED COMMENT:", content, re.DOTALL)
        if t_m: title = t_m.group(1).strip()
        if d_m: description = d_m.group(1).strip()
        
    upload_short(args.video, title, description, tags, privacy_status=args.privacy)
