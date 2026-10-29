import os
import sys
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service(token_file: str = None):
    target_token = token_file if token_file is not None else TOKEN_FILE
    if not os.path.exists(target_token):
        raise FileNotFoundError(f"Missing YouTube OAuth credentials ({target_token}). Please connect your channel.")
    creds = Credentials.from_authorized_user_file(target_token, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(target_token, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload_scheduled_short(video_path: str, title: str, description: str, tags: list, publish_at_iso: str, token_file: str = None):
    youtube = get_authenticated_service(token_file)
    
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "27",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_iso,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True
        }
    }
    
    print(f"\n==========================================")
    print(f"Uploading & Scheduling: {os.path.basename(video_path)}")
    print(f"Title: {title}")
    print(f"Scheduled Public Release: {publish_at_iso}")
    print(f"==========================================")
    
    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024 * 2,
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
    print(f">>> SCHEDULED SUCCESSFULLY: {video_url} <<<")
    return video_url


SCHEDULE_QUEUE = [
    {
        "id": "short_04",
        "video": os.path.join(BASE_DIR, "videos", "short_04", "short_04.mp4"),
        "title": "Why a Crowd of 100 People Will Watch You Die #shorts #psychology",
        "publish_at": "2026-10-26T18:00:00.000Z",  # Monday 6:00 PM UTC
        "description": (
            "The Bystander Effect is one of the most terrifying cognitive flaws in human nature. Here is how it works and the one phrase to break it.\n\n"
            "Subscribe to @ShadowMind for daily behavioral psychology.\n\n"
            "#darkpsychology #bystandereffect #psychologyfacts #humanbehavior #survival #shorts #stoicism"
        ),
        "tags": [
            "dark psychology", "bystander effect", "psychology facts", "human behavior",
            "survival hacks", "crowd psychology", "manipulation tactics", "shorts", "stoicism"
        ]
    },
    {
        "id": "short_05",
        "video": os.path.join(BASE_DIR, "videos", "short_05", "short_05.mp4"),
        "title": "The Terrifying 65% Obedience Experiment #shorts #history",
        "publish_at": "2026-10-27T18:00:00.000Z",  # Tuesday 6:00 PM UTC
        "description": (
            "The Milgram Experiment proved that ordinary humans can be pushed to do the unthinkable through authority alone.\n\n"
            "Subscribe to @ShadowMind for daily dark psychology and historical experiments.\n\n"
            "#darkpsychology #milgramexperiment #historyfacts #psychologyexperiments #humanbehavior #shorts #mystery"
        ),
        "tags": [
            "milgram experiment", "dark psychology", "history facts", "psychology experiments",
            "human obedience", "authority bias", "shock experiment", "shorts", "mystery"
        ]
    },
    {
        "id": "short_06",
        "video": os.path.join(BASE_DIR, "videos", "short_06", "short_06.mp4"),
        "title": "The Monster Study: The Forbidden Orphan Experiment #shorts #darkhistory",
        "publish_at": "2026-10-28T18:00:00.000Z",  # Wednesday 6:00 PM UTC
        "description": (
            "In 1939, researchers conducted The Monster Study on 22 orphans. The results were so disturbing they were buried for decades.\n\n"
            "Subscribe to @ShadowMind for daily dark history and human psychology.\n\n"
            "#darkpsychology #darkhistory #monsterstudy #psychologyexperiments #creepyhistory #shorts #mindset"
        ),
        "tags": [
            "monster study", "dark history", "psychology experiments", "unethical experiments",
            "dark psychology", "creepy history", "stutter experiment", "shorts"
        ]
    }
]


def main():
    print("=== SCHEDULING SHORTS 4, 5, AND 6 ON YOUTUBE ===")
    results = []
    for item in SCHEDULE_QUEUE:
        if not os.path.exists(item["video"]):
            print(f"Error: Missing file {item['video']}")
            continue
        url = upload_scheduled_short(
            video_path=item["video"],
            title=item["title"],
            description=item["description"],
            tags=item["tags"],
            publish_at_iso=item["publish_at"]
        )
        results.append((item["id"], item["title"], item["publish_at"], url))
        print("Pausing 3s before next upload...")
        time.sleep(3)
        
    print("\n" + "="*60)
    print("ALL 3 SHORTS UPLOADED & SCHEDULED IN YOUTUBE STUDIO:")
    for v_id, title, pub, url in results:
        print(f"[{v_id}] {title}\n  -> Drops: {pub} | URL: {url}\n")
    print("="*60)


if __name__ == "__main__":
    main()
