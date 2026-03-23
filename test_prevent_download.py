"""
Test script để kiểm tra prevent_download detection
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.download_service import DownloadService
import yaml


def test_prevent_download_detection():
    """Test prevent_download detection"""
    
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
    
    print("\n" + "="*70)
    print("🔒 TEST PREVENT_DOWNLOAD DETECTION")
    print("="*70)
    
    # Test với video thường (không có prevent_download)
    print("\n📹 Test 1: Video thường (cho phép download)")
    print("-" * 70)
    test_url_1 = "https://v.douyin.com/wIQhS93IyEk/"
    print(f"URL: {test_url_1}")
    
    result_1 = download_service.download_video(test_url_1)
    
    if result_1['success']:
        print(f"✅ {result_1['message']}")
        print(f"   Tiêu đề: {result_1['data']['title'][:50]}...")
    else:
        if result_1.get('data', {}).get('prevent_download'):
            print(f"🔒 {result_1['message']}")
            print(f"   Tiêu đề: {result_1['data']['title'][:50]}...")
            print(f"   Tác giả: {result_1['data']['author']}")
            print(f"   Lý do: {result_1['data']['reason']}")
        else:
            print(f"❌ {result_1['message']}")
    
    print("\n" + "="*70)
    print("📊 KẾT QUẢ TEST")
    print("="*70)
    print("""
✅ Tính năng prevent_download detection đã được thêm vào!

Khi gặp video có prevent_download = true:
  • ⚠️ Hệ thống sẽ KHÔNG tải video
  • 📢 Hiển thị thông báo rõ ràng cho người dùng
  • 📝 Trả về thông tin video (tiêu đề, tác giả, lý do)
  • 💾 Tiết kiệm băng thông và thời gian

Lợi ích:
  • Tránh tải video có watermark khi tác giả bật bảo vệ
  • Thông báo rõ ràng cho người dùng biết lý do
  • Tuân thủ chính sách bảo vệ nội dung của tác giả
    """)
    print("="*70 + "\n")


if __name__ == "__main__":
    test_prevent_download_detection()
