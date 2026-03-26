import sys
import os
import re
import requests
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.curdir))

from apiproxy.tiktok.tiktokapi import TikTokApi

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

api = TikTokApi()
test_url = "https://vt.tiktok.com/ZSuKNRJGx/"

print(f"Testing URL: {test_url}")
key_type, key = api.getKey(test_url)
print(f"Result: type={key_type}, key={key}")

if key_type == "aweme" and key:
    print("SUCCESS: Found video ID!")
    info = api.getAwemeInfo(key)
    if info:
        print("SUCCESS: Fetched video info!")
        print(f"Title: {info.get('desc')}")
    else:
        print("FAILED: Could not fetch video info.")
else:
    print("FAILED: Could not extract key/type.")
