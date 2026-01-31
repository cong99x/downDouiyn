
import requests
import re
import json

def test_full_flow():
    url = "https://www.tiktok.com/@hanoiangi/video/7568858748001750279"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': 'https://www.tiktok.com/'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    print("Fetching page...")
    resp = session.get(url, timeout=15)
    print(f"Page status: {resp.status_code}")
    
    html = resp.text
    scripts = re.findall(r'<script [^>]*type="application/json"[^>]*>(.*?)</script>', html)
    print(f"Found {len(scripts)} scripts")
    
    video_url = None
    for script in scripts:
        if "itemStruct" in script:
            data = json.loads(script)
            # Try to find playAddr
            def find_play_addr(obj):
                if isinstance(obj, dict):
                    if "playAddr" in obj: return obj["playAddr"]
                    for v in obj.values():
                        res = find_play_addr(v)
                        if res: return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = find_play_addr(item)
                        if res: return res
                return None
            
            video_url = find_play_addr(data)
            if video_url:
                print("Found video URL!")
                break
    
    if video_url:
        print(f"Video URL: {video_url[:100]}...")
        print("Downloading video...")
        # Use the same session and same headers
        resp_vid = session.get(video_url, stream=True, timeout=15)
        print(f"Download status: {resp_vid.status_code}")
        if resp_vid.status_code == 200:
            print("Success! Downloaded 1024 bytes...")
            chunk = next(resp_vid.iter_content(chunk_size=1024))
            print(f"Received {len(chunk)} bytes")
        else:
            print(f"Failed with {resp_vid.status_code}")
            print(f"Headers sent: {resp_vid.request.headers}")
    else:
        print("Could not find video URL in page.")

if __name__ == "__main__":
    test_full_flow()
