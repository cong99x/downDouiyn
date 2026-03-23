"""
Test script để kiểm tra URL video từ Douyin API
Kiểm tra xem có URL không watermark không
"""

import asyncio
import yaml
from pathlib import Path
from apiproxy.douyin.douyin import Douyin
from apiproxy.douyin import douyin_headers
import json


def test_video_url():
    """Test lấy URL video"""
    
    # Load cookies từ config
    config_path = Path("config.yml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    cookie_string = config.get('cookies', '')
    
    # Set cookie vào headers
    douyin_headers["Cookie"] = cookie_string
    
    # Initialize Douyin API
    douyin = Douyin(database=True)
    douyin.set_cookies(cookie_string)
    
    # Test với một video URL (bạn cần thay đổi URL này)
    test_url = input("Nhập URL video Douyin để test: ").strip()
    
    if not test_url:
        print("❌ Vui lòng nhập URL")
        return
    
    print(f"\n🔍 Đang phân tích URL: {test_url}")
    
    # Get share link
    share_link = douyin.getShareLink(test_url)
    print(f"✅ Share link: {share_link}")
    
    # Get key
    key_type, key = douyin.getKey(share_link)
    print(f"✅ Key type: {key_type}, Key: {key}")
    
    if key_type == "aweme":
        # Get video info
        print(f"\n📥 Đang lấy thông tin video...")
        video_data = douyin.getAwemeInfo(key)
        
        if video_data:
            print(f"\n✅ Đã lấy được thông tin video!")
            
            # Lưu toàn bộ data vào file để phân tích
            with open("video_data_analysis.json", "w", encoding='utf-8') as f:
                json.dump(video_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Đã lưu toàn bộ data vào video_data_analysis.json")
            
            # Phân tích các URL có sẵn
            print("\n" + "="*60)
            print("📊 PHÂN TÍCH CÁC URL VIDEO")
            print("="*60)
            
            video_info = video_data.get('video', {})
            
            # 1. play_addr (URL thường có watermark)
            play_addr = video_info.get('play_addr', {})
            if play_addr:
                print("\n1️⃣ play_addr (thường có watermark):")
                print(f"   URI: {play_addr.get('uri', 'N/A')}")
                url_list = play_addr.get('url_list', [])
                if url_list:
                    print(f"   URL: {url_list[0][:100]}...")
            
            # 2. download_addr (URL không watermark - nếu có)
            download_addr = video_info.get('download_addr', {})
            if download_addr:
                print("\n2️⃣ download_addr (không watermark):")
                print(f"   URI: {download_addr.get('uri', 'N/A')}")
                url_list = download_addr.get('url_list', [])
                if url_list:
                    print(f"   URL: {url_list[0][:100]}...")
            else:
                print("\n2️⃣ download_addr: ❌ KHÔNG TÌM THẤY")
            
            # 3. download_suffix_logo_addr (URL có logo nhỏ)
            download_suffix = video_info.get('download_suffix_logo_addr', {})
            if download_suffix:
                print("\n3️⃣ download_suffix_logo_addr (logo nhỏ):")
                print(f"   URI: {download_suffix.get('uri', 'N/A')}")
                url_list = download_suffix.get('url_list', [])
                if url_list:
                    print(f"   URL: {url_list[0][:100]}...")
            
            # 4. bit_rate (các chất lượng khác nhau)
            bit_rate = video_info.get('bit_rate', [])
            if bit_rate:
                print(f"\n4️⃣ bit_rate (có {len(bit_rate)} chất lượng):")
                for idx, br in enumerate(bit_rate):
                    quality = br.get('gear_name', 'unknown')
                    bit_rate_val = br.get('bit_rate', 0)
                    play_addr_br = br.get('play_addr', {})
                    url_list_br = play_addr_br.get('url_list', [])
                    print(f"   [{idx}] {quality} ({bit_rate_val} bps)")
                    if url_list_br:
                        print(f"       URL: {url_list_br[0][:100]}...")
            
            # Kiểm tra xem có prevent_download không
            prevent_download = video_data.get('prevent_download', False)
            print(f"\n⚠️ prevent_download: {prevent_download}")
            
            # Kiểm tra author settings
            author = video_data.get('author', {})
            author_prevent = author.get('prevent_download', False)
            print(f"⚠️ author prevent_download: {author_prevent}")
            
            print("\n" + "="*60)
            print("💡 KẾT LUẬN:")
            print("="*60)
            
            if download_addr:
                print("✅ Video này CÓ URL không watermark (download_addr)")
                print("   → Cần sửa code để sử dụng download_addr thay vì play_addr")
            else:
                print("❌ Video này KHÔNG CÓ download_addr")
                if prevent_download or author_prevent:
                    print("   → Tác giả đã BẬT chế độ ngăn download")
                    print("   → Không thể tải video không watermark")
                else:
                    print("   → Có thể do cấu trúc API khác")
                    print("   → Cần kiểm tra file video_data_analysis.json để tìm URL khác")
            
            print("\n📄 Xem chi tiết trong file: video_data_analysis.json")
        else:
            print("❌ Không lấy được thông tin video")
    else:
        print(f"❌ URL type không hợp lệ: {key_type}")


if __name__ == "__main__":
    test_video_url()

