"""
Cookie Validator for Douyin
Kiểm tra tính hợp lệ của cookie Douyin bằng cách thử gọi API
"""

import asyncio
import yaml
import httpx
from pathlib import Path


class CookieValidator:
    """Service để validate cookie Douyin"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = Path(config_path)
        self.cookies = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    
    def load_cookies_from_config(self) -> bool:
        """Load cookies từ file config.yml"""
        try:
            if not self.config_path.exists():
                print(f"❌ File config không tồn tại: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            cookie_string = config.get('cookies', '')
            if not cookie_string:
                print("❌ Không tìm thấy cookies trong config.yml")
                return False
            
            # Parse cookie string thành dictionary
            self.cookies = self._parse_cookie_string(cookie_string)
            
            print(f"✅ Đã load {len(self.cookies)} cookies từ config.yml")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi load cookies: {str(e)}")
            return False
    
    def _parse_cookie_string(self, cookie_string: str) -> dict:
        """Parse cookie string thành dictionary"""
        cookies = {}
        # Loại bỏ khoảng trắng và xuống dòng
        cookie_string = cookie_string.replace('\n', '').replace('  ', '')
        
        # Split bởi dấu ;
        for item in cookie_string.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        return cookies
    
    async def validate_cookie(self) -> dict:
        """
        Validate cookie bằng cách thử gọi API Douyin
        Returns: dict với status và message
        """
        if not self.cookies:
            return {
                'valid': False,
                'message': 'Chưa load cookies',
                'details': None
            }
        
        # Kiểm tra các cookie quan trọng
        important_cookies = ['sessionid', 'sid_guard', 'uid_tt', 'ttwid']
        missing_cookies = [c for c in important_cookies if c not in self.cookies]
        
        if missing_cookies:
            return {
                'valid': False,
                'message': f'Thiếu các cookie quan trọng: {", ".join(missing_cookies)}',
                'details': {
                    'missing_cookies': missing_cookies,
                    'total_cookies': len(self.cookies)
                }
            }
        
        # Test cookie bằng cách gọi API user info
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # API để lấy thông tin user
                url = "https://www.douyin.com/aweme/v1/web/im/user/info/"
                
                response = await client.get(
                    url,
                    headers=self.headers,
                    cookies=self.cookies,
                    follow_redirects=True
                )
                
                print(f"\n📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Kiểm tra response có hợp lệ không
                        if 'status_code' in data:
                            if data['status_code'] == 0:
                                return {
                                    'valid': True,
                                    'message': '✅ Cookie hợp lệ! Đã đăng nhập thành công',
                                    'details': {
                                        'status_code': data['status_code'],
                                        'user_info': data.get('data', {}),
                                        'total_cookies': len(self.cookies),
                                        'important_cookies_present': important_cookies
                                    }
                                }
                            else:
                                return {
                                    'valid': False,
                                    'message': f'❌ Cookie không hợp lệ hoặc đã hết hạn (status_code: {data["status_code"]})',
                                    'details': data
                                }
                        else:
                            # Thử API khác - check follow list
                            return await self._validate_with_follow_api()
                            
                    except Exception as e:
                        print(f"⚠️ Không parse được JSON: {str(e)}")
                        return await self._validate_with_follow_api()
                
                elif response.status_code == 302 or response.status_code == 301:
                    return {
                        'valid': False,
                        'message': '❌ Cookie đã hết hạn hoặc không hợp lệ (bị redirect)',
                        'details': {
                            'status_code': response.status_code,
                            'redirect_url': response.headers.get('Location', 'N/A')
                        }
                    }
                else:
                    return {
                        'valid': False,
                        'message': f'❌ Lỗi khi gọi API (HTTP {response.status_code})',
                        'details': {
                            'status_code': response.status_code,
                            'response_text': response.text[:500]
                        }
                    }
                    
        except Exception as e:
            return {
                'valid': False,
                'message': f'❌ Lỗi khi validate cookie: {str(e)}',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            }
    
    async def _validate_with_follow_api(self) -> dict:
        """Validate bằng API follow list (backup method)"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # API lấy danh sách following
                url = "https://www.douyin.com/aweme/v1/web/im/following/list/"
                params = {
                    'cursor': 0,
                    'count': 10
                }
                
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers,
                    cookies=self.cookies,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status_code') == 0:
                        return {
                            'valid': True,
                            'message': '✅ Cookie hợp lệ! (Verified via follow API)',
                            'details': {
                                'status_code': data['status_code'],
                                'total_cookies': len(self.cookies)
                            }
                        }
                
                return {
                    'valid': False,
                    'message': '❌ Cookie không hợp lệ hoặc đã hết hạn',
                    'details': {
                        'status_code': response.status_code
                    }
                }
                
        except Exception as e:
            return {
                'valid': False,
                'message': f'❌ Lỗi khi validate: {str(e)}',
                'details': {'error': str(e)}
            }
    
    def print_cookie_info(self):
        """In thông tin về cookies"""
        if not self.cookies:
            print("❌ Chưa load cookies")
            return
        
        print("\n" + "="*60)
        print("📋 THÔNG TIN COOKIES")
        print("="*60)
        print(f"Tổng số cookies: {len(self.cookies)}")
        print("\n🔑 Các cookies quan trọng:")
        
        important_cookies = {
            'sessionid': 'Session ID (quan trọng nhất)',
            'sid_guard': 'Session Guard',
            'uid_tt': 'User ID TikTok',
            'ttwid': 'TikTok Web ID',
            'passport_csrf_token': 'CSRF Token',
            'odin_tt': 'Odin Token',
            '__ac_signature': 'AC Signature'
        }
        
        for key, description in important_cookies.items():
            if key in self.cookies:
                value = self.cookies[key]
                # Chỉ hiển thị 20 ký tự đầu để bảo mật
                display_value = value[:20] + '...' if len(value) > 20 else value
                print(f"  ✅ {key}: {display_value}")
                print(f"     └─ {description}")
            else:
                print(f"  ❌ {key}: THIẾU")
                print(f"     └─ {description}")
        
        print("="*60 + "\n")


async def main():
    """Main function"""
    print("\n" + "="*60)
    print("🔍 DOUYIN COOKIE VALIDATOR")
    print("="*60 + "\n")
    
    validator = CookieValidator()
    
    # Load cookies từ config
    print("📂 Đang load cookies từ config.yml...")
    if not validator.load_cookies_from_config():
        return
    
    # In thông tin cookies
    validator.print_cookie_info()
    
    # Validate cookies
    print("🔄 Đang kiểm tra tính hợp lệ của cookies...")
    print("⏳ Vui lòng đợi...\n")
    
    result = await validator.validate_cookie()
    
    # In kết quả
    print("\n" + "="*60)
    print("📊 KẾT QUẢ KIỂM TRA")
    print("="*60)
    print(f"\nTrạng thái: {result['message']}")
    
    if result['details']:
        print("\n📝 Chi tiết:")
        for key, value in result['details'].items():
            if key == 'user_info' and isinstance(value, dict):
                print(f"  • {key}:")
                for k, v in value.items():
                    print(f"    - {k}: {v}")
            else:
                print(f"  • {key}: {value}")
    
    print("="*60 + "\n")
    
    if result['valid']:
        print("🎉 Cookie của bạn đang hoạt động tốt!")
        print("✅ Bạn có thể sử dụng ứng dụng để download video Douyin")
    else:
        print("⚠️ Cookie không hợp lệ hoặc đã hết hạn")
        print("💡 Hướng dẫn:")
        print("   1. Đăng nhập lại vào Douyin trên trình duyệt")
        print("   2. Lấy cookie mới từ DevTools (F12 > Application > Cookies)")
        print("   3. Copy toàn bộ cookies và paste vào config.yml")


if __name__ == "__main__":
    asyncio.run(main())
