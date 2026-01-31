#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from apiproxy.tiktok.tiktokapi import TikTokApi

logger = logging.getLogger('downloader')

class TikTok(object):
    def __init__(self):
        self.api = TikTokApi()
        
    def set_cookies(self, cookie_str: str):
        self.api.set_cookies(cookie_str)

    def getShareLink(self, string: str) -> str:
        return self.api.getShareLink(string)

    def getKey(self, url: str):
        return self.api.getKey(url)

    def getAwemeInfo(self, aweme_id: str) -> dict:
        """Get information for a single TikTok video"""
        logger.info(f'[ TikTok ]: Requesting item ID = {aweme_id}')
        aweme_data, _ = self.api.getAwemeInfoApi(aweme_id)
        if not aweme_data:
            logger.warning(f'[ TikTok ]: Failed to get info for {aweme_id}')
            # Fallback strategy could go here
            return {}
        return aweme_data

    def getUserInfo(self, sec_uid_or_username: str, mode="post", count=35):
        """Get user post list (Stub for now)"""
        logger.info(f'[ TikTok ]: Requesting user {sec_uid_or_username} posts')
        # TikTok user scraping is more complex and often requires headers/signatures
        # We start with single video support and expand
        return []

    # Helper for converting formats if needed
    def _convert_data(self, raw_data):
        return raw_data
