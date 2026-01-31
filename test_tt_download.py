
import requests
import json

def test_tiktok_download():
    # URL from the script_4.json we extracted earlier
    url = "https://v16-webapp-prime.tiktok.com/video/tos/alisg/tos-alisg-pve-0037c001/o4l5gefWGMYILdiifTIff9QRTKAIqcaA8RNQHA/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C&cv=1&br=2856&bt=1428&cs=0&ds=6&ft=-Csk_m7nPD12NMSiAd-Uxt4VhY9e3wv25UcAp&mime_type=video_mp4&qs=0&rc=NDQ6PDs2NWY6O2k3ODNkZUBpM2k1PHk5cnl5NzMzODczNEAuX2EyM2MwXi0xY2ExX2JgYSNrYWEyMmRzbDFhLS1kMS1zcw%3D%3D&btag=e00090000&expire=1769874880&l=2026012923525313E08C1B0801C9266596&ply_type=2&policy=2&signature=e67958424e1a3075bb605d2ae2d72d9f&tk=tt_chain_token"
    
    headers_list = [
        {
            "name": "Minimal",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
        },
        {
            "name": "TikTok Referer",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Referer": "https://www.tiktok.com/"
            }
        },
         {
            "name": "Full TikTok Headers",
            "headers": {
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                'referer': 'https://www.tiktok.com/',
                'range': 'bytes=0-',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'video',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'same-site'
            }
        }
    ]
    
    for h in headers_list:
        print(f"Testing {h['name']}...")
        try:
            resp = requests.head(url, headers=h['headers'], timeout=10)
            print(f"  Result: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  Success!")
                # Download a tiny bit to be sure
                resp2 = requests.get(url, headers=h['headers'], stream=True, timeout=10)
                chunk = next(resp2.iter_content(chunk_size=1024))
                print(f"  Data received: {len(chunk)} bytes")
                break
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_tiktok_download()
