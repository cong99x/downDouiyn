"""
Test download video với URL conversion
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.download_service import DownloadService
import yaml

def test_download():
    """Test download video"""
    
    # Load cookies
    config_path = Path("config.yml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    cookie_string = config.get('cookies', '')
    
    # Initialize download service
    download_service = DownloadService(
        download_path="./Downloaded_Test",
        cookie=cookie_string
    )
    
    # Test URL
    test_url = "https://v.douyin.com/wIQhS93IyEk/"
    
    print("\n" + "="*60)
    print("🎬 TEST DOWNLOAD VIDEO KHÔNG WATERMARK")
    print("="*60)
    print(f"\n📹 URL: {test_url}")
    print("\n⏳ Đang download...\n")
    
    # Download
    result = download_service.download_video(test_url)
    
    print("\n" + "="*60)
    print("📊 KẾT QUẢ")
    print("="*60)
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"\n📝 Thông tin video:")
        data = result['data']
        print(f"   • Tiêu đề: {data['title']}")
        print(f"   • Tác giả: {data['author']}")
        print(f"   • File: {data['filename']}")
        print(f"   • Đường dẫn: {data['file_path']}")
        print(f"\n💡 Hãy kiểm tra video đã tải về xem còn watermark không!")
        print(f"📂 Mở thư mục: {Path(data['file_path']).parent}")
    else:
        print(f"❌ {result['message']}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    test_download()
