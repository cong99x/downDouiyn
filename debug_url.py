import requests
from apiproxy.tiktok import tiktok_headers

url = "https://v16-webapp-prime.tiktok.com/video/tos/alisg/tos-alisg-pve-0037c001/o06S0WBtRAe2gjHkAQLg84oGXeeYTJ8IDIC55I/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C&cv=1&br=1840&bt=920&cs=0&ds=6&ft=-Csk_m7nPD12NyAg1d-UxDJ5GY6e3wv25DcAp&mime_type=video_mp4&qs=0&rc=NTs8OmY0ZTRnZjszPDtoOkBpM2Z0ZXc5cmR4ODMzODczNEAwYy1fNi8xX2ExXl9jNWAvYSM1Z25rMmRzLXBhLS1kMTFzcw%3D%3D&btag=e00090000&expire=1769960224&l=20260130233544166AC36049D46E873CFC&ply_type=2&policy=2&signature=3741073814ee6a04ea372b7ac138e684&tk=tt_chain_token"

strategies = [
    ("Original Headers", tiktok_headers),
    ("No Referer", {k:v for k,v in tiktok_headers.items() if k.lower() != 'referer'}),
    ("Empty Headers", {}),
    ("Only User-Agent", {'User-Agent': tiktok_headers['User-Agent']}),
    ("Browser Chrome Windows", {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.tiktok.com/'
    })
]

print(f"Testing URL: {url[:50]}...")
for name, headers in strategies:
    try:
        r = requests.head(url, headers=headers, timeout=10)
        print(f"Strategy: {name:<25} | Status: {r.status_code}")
    except Exception as e:
        print(f"Strategy: {name:<25} | Error: {e}")
