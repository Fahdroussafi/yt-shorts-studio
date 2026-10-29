import requests
import re
import random
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_stock_video_clip(query: str, dest_path: str):
    """Fetch a free real MP4 video clip by keyword from Mixkit/Coverr."""
    query_clean = query.strip().lower().replace(" ", "-")
    urls_to_try = [
        f"https://mixkit.co/free-stock-video/{query_clean}/",
        f"https://coverr.co/s?q={query.strip().lower().replace(' ', '+')}"
    ]
    
    mp4_links = []
    for u in urls_to_try:
        try:
            r = requests.get(u, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                # Find direct 720p or 1080p mp4 links
                found = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-720\.mp4', r.text)
                if not found:
                    found = re.findall(r'https://[^"\']+\.mp4', r.text)
                if found:
                    mp4_links.extend(found)
                    break
        except Exception as e:
            print(f"Fetch query error: {e}")
            
    if not mp4_links:
        # Fallback to general technology
        r = requests.get("https://mixkit.co/free-stock-video/technology/", headers=HEADERS, timeout=10)
        mp4_links = re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-720\.mp4', r.text)
        
    if mp4_links:
        selected_url = random.choice(mp4_links[:5])
        print(f"Downloading real stock video for '{query}': {selected_url}")
        r = requests.get(selected_url, headers=HEADERS, stream=True, timeout=25)
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*64):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded clip: {dest_path} ({round(os.path.getsize(dest_path)/(1024*1024), 2)} MB)")
        return True
    return False

if __name__ == "__main__":
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(_base, "test_robot.mp4")
    res = fetch_stock_video_clip("robot", out)
    print("Success:", res)
