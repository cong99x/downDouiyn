#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import requests
import json
import time
import copy
import logging
from apiproxy.tiktok import tiktok_headers
from apiproxy.tiktok.urls import TikTokUrls
from apiproxy.douyin.result import Result
from apiproxy.common import utils

logger = logging.getLogger('downloader')

class TikTokApi(object):
    def __init__(self):
        self.urls = TikTokUrls()
        self.result = Result()
        self.utils = utils
        self.timeout = 15
        self.headers = copy.deepcopy(tiktok_headers)
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def set_cookies(self, cookie_str):
        if cookie_str:
            self.headers['Cookie'] = cookie_str
            self.session.headers.update({'Cookie': cookie_str})

    def get_session_cookies(self):
        """Expose session cookies as dict"""
        return self.session.cookies.get_dict()

    def getShareLink(self, string):
        """Extract URL from string"""
        pattern = r'https?://[a-zA-Z0-9.\-/_?&%=#:@!+]+'
        matches = re.findall(pattern, string)
        return matches[0] if matches else None

    def getKey(self, url):
        """Extract id and type from TikTok URL"""
        key = None
        key_type = None

        try:
            # Handle short URLs (vt.tiktok.com, v.tiktok.com, tiktok.com/t/)
            # These always need redirection to find the actual video ID
            if any(domain in url for domain in ['vt.tiktok.com', 'v.tiktok.com', 'tiktok.com/t/']):
                logger.info(f"Short TikTok URL detected: {url}, following redirects...")
                r = self.session.get(url, allow_redirects=True, timeout=self.timeout, stream=True)
                url = r.url
                logger.info(f"Redirected to: {url}")

            # 1. Pattern for video: tiktok.com/@user/video/732891238123
            video_match = re.search(r'video/(\d+)', url)
            if video_match:
                key = video_match.group(1)
                key_type = "aweme"
                return key_type, key

            # 2. Pattern for mobile v/ format: tiktok.com/v/732891238123
            v_match = re.search(r'/v/(\d+)', url)
            if v_match:
                key = v_match.group(1)
                key_type = "aweme"
                return key_type, key

            # 3. Pattern for user: tiktok.com/@username
            user_match = re.search(r'@([a-zA-Z0-9._-]+)', url)
            if user_match:
                key = user_match.group(1)
                key_type = "user"
                return key_type, key

        except Exception as e:
            logger.error(f'TikTok link parsing failed: {e}')
        
        return key_type, key

    def getAwemeInfoApi(self, aweme_id):
        """Fetch video information from TikTok API"""
        if not aweme_id:
            return None, None

        # Method 1: Try SSR Fallback first as it is more reliable for web
        logger.info(f"Attempting TikTok SSR fallback for ID: {aweme_id}")
        ssr_data = self._try_ssr_fallback(aweme_id)
        if ssr_data:
            return ssr_data, {"method": "ssr"}

        # Method 2: Standard API
        start = time.time()
        while True:
            try:
                # TikTok Item Detail API usually requires signature (X-Bogus)
                params = {
                    'itemId': aweme_id,
                    'aid': '1988',
                    'device_platform': 'webapp',
                    'region': 'VN',
                    'priority_region': '',
                    'os': 'windows',
                    'referer': '',
                    'cookie_enabled': 'true',
                    'screen_width': '1920',
                    'screen_height': '1080',
                    'browser_language': 'en-US',
                    'browser_platform': 'Win32',
                    'browser_name': 'Mozilla',
                    'browser_version': '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'browser_online': 'true',
                }
                
                response = self.session.get(self.urls.ITEM_DETAIL, params=params, timeout=self.timeout)
                datadict = response.json()
                
                if datadict and datadict.get("statusCode") == 0:
                    break
                else:
                    logger.warning(f"TikTok API failed: {datadict.get('statusMsg', 'Unknown error')}")
            except Exception as e:
                if time.time() - start > self.timeout:
                    return None, None
                time.sleep(1)

        # Normalizing data to Result format
        self.result.clearDict(self.result.awemeDict)
        item = datadict.get("itemInfo", {}).get("itemStruct", {})
        
        if not item:
            return None, datadict

        # Basic mapping (TikTok API structure is different from Douyin)
        self.result.awemeDict["aweme_id"] = item.get("id")
        self.result.awemeDict["desc"] = item.get("desc")
        self.result.awemeDict["create_time"] = time.strftime("%Y-%m-%d %H.%M.%S", time.localtime(int(item.get("createTime", 0))))
        self.result.awemeDict["awemeType"] = 0 # Default to video
        
        # Mapping video addr
        video_url = item.get("video", {}).get("downloadAddr") or item.get("video", {}).get("playAddr")
        if video_url:
            self.result.awemeDict["video"]["play_addr"]["url_list"] = [video_url]
            
        # Mapping author
        author = item.get("author", {})
        self.result.awemeDict["author"]["nickname"] = author.get("nickname")
        self.result.awemeDict["author"]["unique_id"] = author.get("uniqueId")
        self.result.awemeDict["author"]["sec_uid"] = author.get("secUid")

        return self.result.awemeDict, datadict

    def _try_ssr_fallback(self, aweme_id: str) -> dict:
        """Extract data from TikTok SSR HTML"""
        try:
            url = f"https://www.tiktok.com/video/{aweme_id}"
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"TikTok SSR failed with status {response.status_code}")
                return {}
            
            html = response.text
            # Debug: save HTML to file
            with open("tiktok_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("Saved TikTok HTML to tiktok_debug.html for debugging")
            # Look for __UNIVERSAL_DATA_FOR_REHYDRATION__ or SIG_RENDER_DATA
            json_data = None
            
            # 1. Try __UNIVERSAL_DATA_FOR_REHYDRATION__
            match = re.search(r'id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html)
            if match:
                try:
                    data = json.loads(match.group(1))
                    # TikTok structure in Universal Data:
                    # __DEFAULT_SCOPE__ -> webapp.video-detail -> itemInfo -> itemStruct
                    video_detail = data.get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail", {})
                    if "itemInfo" in video_detail:
                        item = video_detail["itemInfo"].get("itemStruct", {})
                        if item:
                            return self._normalize_item(item)
                except:
                    pass

            # 2. Try Mobile Fallback
            logger.info(f"Attempting TikTok Mobile SSR fallback for ID: {aweme_id}")
            mobile_url = f"https://m.tiktok.com/v/{aweme_id}.html"
            headers = copy.deepcopy(self.session.headers)
            headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
            response = self.session.get(mobile_url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                html = response.text
                with open("tiktok_mobile_debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info("Saved TikTok Mobile HTML to tiktok_mobile_debug.html")
                
                # Broad search for SIG_RENDER_DATA or UNIVERSAL_DATA
                match = re.search(r'type="application/json">(.*?)</script>', html)
                if match:
                    try:
                        # Try to find all JSON-like scripts and look for itemStruct
                        scripts = re.findall(r'<script [^>]*type="application/json"[^>]*>(.*?)</script>', html)
                        for script_content in scripts:
                            try:
                                data = json.loads(script_content)
                                item = self.utils.find_key(data, "itemStruct")
                                if item:
                                    logger.info("Found itemStruct in a script tag!")
                                    return self._normalize_item(item)
                            except:
                                continue
                    except Exception as e:
                        logger.warning(f"Error parsing scripts: {e}")
                    
        except Exception as e:
            logger.warning(f"TikTok SSR fallback error: {e}")
        return {}

    def _normalize_item(self, item: dict) -> dict:
        """Convert TikTok itemStruct to Result format"""
        self.result.clearDict(self.result.awemeDict)
        
        self.result.awemeDict["aweme_id"] = item.get("id")
        self.result.awemeDict["desc"] = item.get("desc")
        self.result.awemeDict["create_time"] = time.strftime("%Y-%m-%d %H.%M.%S", time.localtime(int(item.get("createTime", 0))))
        self.result.awemeDict["awemeType"] = 1 if item.get('imagePost') else 0
        
        # Video
        video = item.get("video", {})
        play_url = video.get("playAddr") or video.get("downloadAddr")
        if play_url:
            self.result.awemeDict["video"]["play_addr"]["url_list"] = [play_url]
            
        # Author
        author = item.get("author", {})
        self.result.awemeDict["author"]["nickname"] = author.get("nickname")
        self.result.awemeDict["author"]["unique_id"] = author.get("uniqueId")
        self.result.awemeDict["author"]["sec_uid"] = author.get("secUid")
        self.result.awemeDict["author"]["avatar_thumb"]["url_list"] = [author.get("avatarThumb", "")]
        
        # Music
        music = item.get("music", {})
        music_url = music.get("playUrl")
        if music_url:
            self.result.awemeDict["music"]["play_url"]["url_list"] = [music_url]
        self.result.awemeDict["music"]["title"] = music.get("title")
        self.result.awemeDict["music"]["author"] = music.get("authorName")
        
        # Cover
        cover = video.get("cover")
        if cover:
            self.result.awemeDict["video"]["cover"]["url_list"] = [cover]
        dynamic_cover = video.get("dynamicCover")
        if dynamic_cover:
            self.result.awemeDict["video"]["dynamic_cover"]["url_list"] = [dynamic_cover]
            
        return self.result.awemeDict

    def getAwemeInfo(self, aweme_id: str) -> dict:
        """
        Get TikTok video information (wrapper for getAwemeInfoApi).
        
        Args:
            aweme_id: TikTok video ID
            
        Returns:
            Video data dictionary or None
        """
        video_data, _ = self.getAwemeInfoApi(aweme_id)
        return video_data
