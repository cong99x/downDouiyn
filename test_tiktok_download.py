#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test TikTok download directly to debug the issue
"""

import sys
import os
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
aweme_id = "7600352599870557461"

print(f"Fetching TikTok video info for ID: {aweme_id}")
video_data = tiktok.getAwemeInfo(aweme_id)

if video_data:
    print(f"\n✅ Got video data!")
    print(f"Title: {video_data.get('desc', 'N/A')}")
    print(f"Author: {video_data.get('author', {}).get('nickname', 'N/A')}")
    print(f"awemeType: {video_data.get('awemeType')}")
    
    # Check video URL
    video_url = video_data.get('video', {}).get('play_addr', {}).get('url_list', [])
    if video_url:
        print(f"\n📹 Video URL: {video_url[0][:100]}...")
        
        # Test download
        print(f"\n🔽 Testing download with TikTok headers...")
        downloader = Download(
            thread=1,
            music=True,
            cover=True,
            avatar=True,
            resjson=True,
            folderstyle=True,
            custom_headers=tiktok_headers
        )
        
        save_path = Path("./test_download")
        save_path.mkdir(exist_ok=True)
        
        try:
            downloader.awemeDownload(awemeDict=video_data, savePath=save_path)
            print("\n✅ Download completed! Check ./test_download folder")
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
    else:
        print("\n❌ No video URL found!")
else:
    print("\n❌ Failed to get video data!")
