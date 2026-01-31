#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Douyin Cookie Extraction Assistant (Manual Version)
No Playwright required, manually obtain via browser developer tools
"""

import json
import yaml
import os
import sys
from datetime import datetime
from typing import Dict

def print_instructions():
    """Print detailed instructions for obtaining Cookies"""
    print("\n" + "="*60)
    print("Douyin Cookie Extraction Tutorial")
    print("="*60)
    print("\n📝 Steps:\n")
    print("1. Open a browser (Chrome/Edge recommended)")
    print("2. Visit Douyin web version: https://www.douyin.com")
    print("3. Log into your account (QR Code/Phone/Third-party login)")
    print("4. After successful login, press F12 to open developer tools")
    print("5. Switch to the Network tab")
    print("6. Refresh the page (F5)")
    print("7. Find any request for douyin.com in the request list")
    print("8. Click the request and find Request Headers on the right")
    print("9. Find the Cookie field and copy the entire Cookie value")
    print("\n" + "="*60)
    
    print("\n⚠️ Important Tips:")
    print("• Cookies contain your login info, do not share with others")
    print("• Cookies usually last 7-30 days; obtain new ones if they expire")
    print("• Recommended to update Cookies regularly for download success")
    print("\n" + "="*60)

def parse_cookie_string(cookie_str: str) -> Dict[str, str]:
    """Parse Cookie string into a dictionary"""
    cookies = {}
    
    # Clean input
    cookie_str = cookie_str.strip()
    if cookie_str.startswith('"') and cookie_str.endswith('"'):
        cookie_str = cookie_str[1:-1]
    
    # Split Cookies
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    
    return cookies

def validate_cookies(cookies: Dict[str, str]) -> bool:
    """Validate if Cookies contain necessary fields"""
    # Necessary Cookie fields
    required_fields = ['ttwid']  # ttwid is the bare minimum
    important_fields = ['sessionid', 'sessionid_ss', 'passport_csrf_token', 'msToken']
    
    # Check necessary fields
    missing_required = []
    for field in required_fields:
        if field not in cookies:
            missing_required.append(field)
    
    if missing_required:
        print(f"\n❌ Missing required Cookie fields: {', '.join(missing_required)}")
        return False
    
    # Check important fields
    missing_important = []
    for field in important_fields:
        if field not in cookies:
            missing_important.append(field)
    
    if missing_important:
        print(f"\n⚠️ Missing some important Cookie fields: {', '.join(missing_important)}")
        print("This might affect some features, but you can try using it")
    
    return True

def save_cookies(cookies: Dict[str, str], config_path: str = "config_simple.yml"):
    """Save Cookies to configuration file"""
    # Read existing configuration
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    # Update Cookie configuration
    config['cookies'] = cookies
    
    # Save configuration
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Cookies saved to {config_path}")
    
    # Simultaneously save full Cookie string
    cookie_string = '; '.join([f'{k}={v}' for k, v in cookies.items()])
    with open('cookies.txt', 'w', encoding='utf-8') as f:
        f.write(cookie_string)
    print(f"✅ Full Cookie string saved to cookies.txt")
    
    # Save a timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'cookies_backup_{timestamp}.json'
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump({
            'cookies': cookies,
            'cookie_string': cookie_string,
            'timestamp': timestamp,
            'note': 'Douyin Cookie Backup'
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ Cookie backup saved to {backup_file}")

def load_existing_cookies(config_path: str = "config_simple.yml") -> Dict[str, str]:
    """Load existing Cookies"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('cookies', {})
    return {}

def main():
    """Main function"""
    print("\n🍪 Douyin Cookie Configuration Assistant")
    print("-" * 40)
    
    # Show options
    print("\nPlease select an operation:")
    print("1. Obtain new Cookies")
    print("2. View current Cookies")
    print("3. Validate Cookie effectiveness")
    print("4. Show tutorial")
    
    choice = input("\nPlease enter an option (1-4): ").strip()
    
    if choice == '1':
        # Obtain new Cookies
        print_instructions()
        
        print("\nPlease paste the Cookie content you copied:")
        print("(Tip: Press Enter to confirm after pasting)")
        print("-" * 40)
        
        # Support multi-line input
        lines = []
        while True:
            line = input()
            if line:
                lines.append(line)
            else:
                break
        
        cookie_str = ' '.join(lines)
        
        if not cookie_str:
            print("\n❌ No Cookie entered")
            return
        
        # Parse Cookie
        cookies = parse_cookie_string(cookie_str)
        
        if not cookies:
            print("\n❌ Cookie parsing failed, please check the format")
            return
        
        print(f"\n✅ Successfully parsed {len(cookies)} Cookie fields")
        
        # Show important Cookies
        print("\n📋 Extracted key Cookies:")
        important_fields = ['sessionid', 'sessionid_ss', 'ttwid', 'passport_csrf_token', 'msToken']
        for field in important_fields:
            if field in cookies:
                value = cookies[field]
                display_value = f"{value[:20]}..." if len(value) > 20 else value
                print(f"  • {field}: {display_value}")
        
        # Validate Cookies
        if validate_cookies(cookies):
            # Ask whether to save
            save_choice = input("\nSave Cookies to configuration file? (y/n): ").strip().lower()
            if save_choice == 'y':
                save_cookies(cookies)
                print("\n🎉 Configuration complete! You can now run the downloader:")
                print("python3 downloader.py -c config_simple.yml")
            else:
                print("\nSave cancelled")
        
    elif choice == '2':
        # View current Cookies
        cookies = load_existing_cookies()
        if cookies:
            print("\n📋 Currently configured Cookies:")
            for key, value in cookies.items():
                display_value = f"{value[:30]}..." if len(value) > 30 else value
                print(f"  • {key}: {display_value}")
        else:
            print("\n❌ No configured Cookies found")
    
    elif choice == '3':
        # Validate Cookies
        cookies = load_existing_cookies()
        if cookies:
            print("\n🔍 Validating Cookies...")
            if validate_cookies(cookies):
                print("✅ Cookie format is correct")
                print("\nNote: This only validates the format. Effectiveness requires testing the download function.")
        else:
            print("\n❌ No configured Cookies found")
    
    elif choice == '4':
        # Show tutorial
        print_instructions()
    
    else:
        print("\n❌ Invalid option")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exited")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()