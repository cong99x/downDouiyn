#!/usr/bin/env python
# -*- coding: utf-8 -*-

import apiproxy

tiktok_headers = {
    'User-Agent': apiproxy.ua,
    'referer': 'https://www.tiktok.com/',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin'
}
