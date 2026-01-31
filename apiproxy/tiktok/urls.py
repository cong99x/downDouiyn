#!/usr/bin/env python
# -*- coding: utf-8 -*-

class TikTokUrls(object):
    def __init__(self):
        # TikTok Base API
        self.BASE_URL = 'https://www.tiktok.com'
        self.API_BASE = 'https://www.tiktok.com/api'
        
        # User details
        self.USER_DETAIL = f'{self.API_BASE}/user/detail/'
        
        # User post list
        self.USER_POST = f'{self.API_BASE}/post/item_list/'
        
        # Video detail (requires item_id)
        self.ITEM_DETAIL = f'{self.API_BASE}/item/detail/'
        
        # Search (if needed)
        self.SEARCH_ITEM = f'{self.API_BASE}/search/item/full/'
        
        # Short URL redirect resolver (usually handled by requests)
        self.SHORT_URL_BASE = 'https://vt.tiktok.com/'
