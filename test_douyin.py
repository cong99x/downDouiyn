
import asyncio
import argparse
from downloader import UnifiedDownloader

async def test_download(url):
    print(f"Testing download for URL: {url}")
    # Initialize downloader with cookies if available
    downloader = UnifiedDownloader(
        cookies='auto',
        save_path='downloads'
    )
    
    # Initialize
    await downloader._initialize_cookies_and_headers()
    
    # Start download
    success = await downloader.download(url)
    if success:
        print("\n[SUCCESS] Download completed!")
    else:
        print("\n[FAILED] Download failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://v.douyin.com/aGG719PwM5M/")
    args = parser.parse_args()
    
    asyncio.run(test_download(args.url))
