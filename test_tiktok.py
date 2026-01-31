import sys
import os
import asyncio

# Add relevant paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from downloader import UnifiedDownloader, Platform, ContentType

async def test_tiktok_support():
    downloader = UnifiedDownloader()
    
    # 1. Test Platform Detection
    tiktok_urls = [
        "https://www.tiktok.com/@khaby.lame/video/732891238123",
        "https://vt.tiktok.com/ZS2A1B2C/",
        "https://www.tiktok.com/@tiktok"
    ]
    
    douyin_urls = [
        "https://www.douyin.com/video/123456789",
        "https://v.douyin.com/i89Wvptv/"
    ]
    
    print("Checking Platform Detection...")
    for url in tiktok_urls:
        platform = downloader.detect_platform(url)
        print(f"URL: {url} -> {platform}")
        assert platform == Platform.TIKTOK
        
    for url in douyin_urls:
        platform = downloader.detect_platform(url)
        print(f"URL: {url} -> {platform}")
        assert platform == Platform.DOUYIN
    
    # 2. Test Content Type Detection
    print("\nChecking Content Type Detection...")
    assert downloader.detect_content_type(tiktok_urls[0]) == ContentType.VIDEO
    assert downloader.detect_content_type(tiktok_urls[2]) == ContentType.USER
    print("Content Type detection passed!")

    # 3. Test TikTok ID Extraction
    print("\nChecking TikTok ID Extraction...")
    from apiproxy.tiktok.tiktok import TikTok
    tk = TikTok()
    
    type1, id1 = tk.getKey(tiktok_urls[0])
    print(f"Video URL: {tiktok_urls[0]} -> {type1}, {id1}")
    assert type1 == "aweme"
    assert id1 == "732891238123"
    
    type2, id2 = tk.getKey(tiktok_urls[2])
    print(f"User URL: {tiktok_urls[2]} -> {type2}, {id2}")
    assert type2 == "user"
    assert id2 == "tiktok"
    
    print("\nAll internal logic tests passed!")

if __name__ == "__main__":
    asyncio.run(test_tiktok_support())
