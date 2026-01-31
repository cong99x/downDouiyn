
import re

def validate(url):
    print(f"Testing URL: {url}")
    # Updated pattern with . and @ support
    pattern = r'https?://(?:[a-zA-Z0-9-]+\.)?(?:douyin\.com|tiktok\.com|iesdouyin\.com)/[a-zA-Z0-9/_?=&%\-\.@]+'
    match = re.search(pattern, url)
    if match:
        print("✅ Match found:", match.group(0))
        return True
    else:
        print("❌ No match found")
        return False

url = "https://www.tiktok.com/@hh04102001/video/7599156423603375378?is_from_webapp=1&sender_device=pc"
validate(url)
