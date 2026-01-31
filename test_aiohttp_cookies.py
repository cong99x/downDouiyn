
import aiohttp
import asyncio
import json

async def test_aiohttp_cookies():
    # URL from our earlier success
    url = "https://v16-webapp-prime.tiktok.com/video/tos/alisg/tos-alisg-pve-0037c001/o4l5gefWGMYILdiifTIff9QRTKAIqcaA8RNQHA/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C&cv=1&br=2856&bt=1428&cs=0&ds=6&ft=-Csk_m7nPD12NMSiAd-Uxt4VhY9e3wv25UcAp&mime_type=video_mp4&qs=0&rc=NDQ6PDs2NWY6O2k3ODNkZUBpM2k1PHk5cnl5NzMzODczNEAuX2EyM2MwXi0xY2ExX2JgYSNrYWEyMmRzbDFhLS1kMS1zcw%3D%3D&btag=e00090000&expire=1769874880&l=2026012923525313E08C1B0801C9266596&ply_type=2&policy=2&signature=e67958424e1a3075bb605d2ae2d72d9f&tk=tt_chain_token"
    
    # We need real cookies from a request
    import requests
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': 'https://www.tiktok.com/'
    })
    s.get("https://www.tiktok.com/@hanoiangi/video/7568858748001750279")
    cookies = s.cookies.get_dict()
    print(f"Got {len(cookies)} cookies")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': 'https://www.tiktok.com/'
    }
    
    async with aiohttp.ClientSession(cookies=cookies) as session:
        print("Testing aiohttp with cookies...")
        async with session.get(url, headers=headers) as resp:
            print(f"  Status: {resp.status}")
            if resp.status == 200:
                data = await resp.read()
                print(f"  Success! Read {len(data[:1024])} bytes")
            else:
                print(f"  Failed. Headers sent: {resp.request_info.headers}")

if __name__ == "__main__":
    asyncio.run(test_aiohttp_cookies())
