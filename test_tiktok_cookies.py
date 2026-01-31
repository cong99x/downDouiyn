#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test TikTok download with cookies to debug
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apiproxy.tiktok.tiktokapi import TikTokApi
from apiproxy.douyin.download import Download
from apiproxy.tiktok import tiktok_headers
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test TikTok download
tiktok = TikTokApi()
# Add some common browser headers to be sure
tiktok.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.tiktok.com/'
})
tiktok.session.headers.update(tiktok.headers)

aweme_id = "7600352599870557461"

print(f"Fetching TikTok video info for ID: {aweme_id}")
video_data = tiktok.getAwemeInfo(aweme_id)

if video_data:
    print(f"\n✅ Got video data!")
    
    # Get cookies from session
    cookies = tiktok.get_session_cookies()
    print(f"Session cookies: {cookies.keys()}")
    
    # Check video URL
    video_url = video_data.get('video', {}).get('play_addr', {}).get('url_list', [])
    if video_url:
        url = video_url[0]
        print(f"\n📹 Video URL: {url[:100]}...")
        
        # Test download with requests directly first
        print(f"\n🔽 Testing HEAD request with cookies...")
        
        # Prepare headers
        headers = tiktok_headers.copy()
        headers['User-Agent'] = tiktok.headers['User-Agent']
        
        try:
            r = requests.head(url, headers=headers, cookies=cookies, timeout=10)
            print(f"Status with cookies: {r.status_code}")
            
            if r.status_code == 403:
                 # Try WITHOUT Referer
                print("Trying without Referer...")
                headers.pop('referer', None)
                headers.pop('Referer', None)
                r = requests.head(url, headers=headers, cookies=cookies, timeout=10)
                print(f"Status without Referer + Cookies: {r.status_code}")
                
        except Exception as e:
            print(f"Error: {e}")

    else:
        print("\n❌ No video URL found!")
else:
    print("\n❌ Failed to get video data!")
