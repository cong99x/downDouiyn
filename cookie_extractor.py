#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Douyin Cookie Auto-Extractor
Uses Playwright to automatically log in and extract Cookies
"""

import asyncio
import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Optional
import time

try:
    from playwright.async_api import async_playwright, Browser, Page
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich import print as rprint
except ImportError:
    print("Please install necessary dependencies: pip install playwright rich pyyaml")
    print("And run: playwright install chromium")
    sys.exit(1)

console = Console()


class CookieExtractor:
    """Cookie Extractor"""
    
    def __init__(self, config_path: str = "config_simple.yml"):
        self.config_path = config_path
        self.cookies = {}
        
    async def extract_cookies(self, headless: bool = False) -> Dict:
        """Extract Cookies
        
        Args:
            headless: Whether to run in headless mode
        """
        console.print(Panel.fit(
            "[bold cyan]Douyin Cookie Auto-Extractor[/bold cyan]\n"
            "[dim]The browser will open automatically. Please complete the login in the browser.[/dim]",
            border_style="cyan"
        ))
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # Create context (emulate a real browser)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Add initialization script (hide automation features)
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Create page
            page = await context.new_page()
            
            try:
                # Visit Douyin login page
                console.print("\n[cyan]Opening Douyin login page...[/cyan]")
                await page.goto('https://www.douyin.com', wait_until='domcontentloaded', timeout=60000)
                
                # Wait for user to log in
                console.print("\n[yellow]Please complete the login in the browser[/yellow]")
                console.print("[dim]Login methods:[/dim]")
                console.print("  1. QR Code login (Recommended)")
                console.print("  2. Phone number login")
                console.print("  3. Third-party account login")
                
                # Wait for login success signs
                logged_in = await self._wait_for_login(page)
                
                if logged_in:
                    console.print("\n[green]✅ Login successful! Extracting Cookies...[/green]")
                    
                    # Extract Cookies
                    cookies = await context.cookies()
                    
                    # Convert to dictionary format
                    cookie_dict = {}
                    cookie_string = ""
                    
                    for cookie in cookies:
                        cookie_dict[cookie['name']] = cookie['value']
                        cookie_string += f"{cookie['name']}={cookie['value']}; "
                    
                    self.cookies = cookie_dict
                    
                    # Display important Cookies
                    console.print("\n[cyan]Extracted key Cookies:[/cyan]")
                    important_cookies = ['sessionid', 'sessionid_ss', 'ttwid', 'passport_csrf_token', 'msToken']
                    for name in important_cookies:
                        if name in cookie_dict:
                            value = cookie_dict[name]
                            console.print(f"  • {name}: {value[:20]}..." if len(value) > 20 else f"  • {name}: {value}")
                    
                    # Save Cookies
                    if Confirm.ask("\nSave Cookies to configuration file?"):
                        self._save_cookies(cookie_dict)
                        console.print("[green]✅ Cookies saved to configuration file[/green]")
                    
                    # Save full Cookie string to file
                    with open('cookies.txt', 'w', encoding='utf-8') as f:
                        f.write(cookie_string.strip())
                    console.print("[green]✅ Full Cookies saved to cookies.txt[/green]")
                    
                    return cookie_dict
                else:
                    console.print("\n[red]❌ Login timeout or failed[/red]")
                    return {}
                    
            except Exception as e:
                console.print(f"\n[red]❌ Failed to extract Cookies: {e}[/red]")
                return {}
            finally:
                await browser.close()
    
    async def _wait_for_login(self, page: Page, timeout: int = 300) -> bool:
        """Wait for user to log in
        
        Args:
            page: Page object
            timeout: Timeout period (seconds)
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if logged in (multiple ways)
            try:
                # Type 1: Check for user avatar
                avatar = await page.query_selector('div[class*="avatar"]')
                if avatar:
                    await asyncio.sleep(2)  # Wait for Cookies to fully load
                    return True
                
                # Type 2: Check if URL contains user ID
                current_url = page.url
                if '/user/' in current_url:
                    await asyncio.sleep(2)
                    return True
                
                # Type 3: Check for specific post-login elements
                user_menu = await page.query_selector('[class*="user-info"]')
                if user_menu:
                    await asyncio.sleep(2)
                    return True
                
            except:
                pass
            
            await asyncio.sleep(2)
            
            # Show waiting progress
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            console.print(f"\r[dim]Waiting for login... ({remaining}s remaining)[/dim]", end="")
        
        return False
    
    def _save_cookies(self, cookies: Dict):
        """Save Cookies to configuration file"""
        # Read existing configuration
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # Update Cookie configuration
        config['cookies'] = cookies
        
        # Save configuration
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    async def quick_extract(self) -> Dict:
        """Quick extraction (use an already logged-in browser session)"""
        console.print("\n[cyan]Attempting to extract Cookies from an open browser...[/cyan]")
        console.print("[dim]Please make sure you are logged into Douyin in the browser[/dim]")
        
        # Here we could use CDP to connect to an already open browser
        # Requires browser to be launched in debug mode
        console.print("\n[yellow]Please follow these steps:[/yellow]")
        console.print("1. Close all Chrome browsers")
        console.print("2. Launch Chrome in debug mode:")
        console.print("   Windows: chrome.exe --remote-debugging-port=9222")
        console.print("   Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        console.print("3. Log into Douyin in the opened browser")
        console.print("4. Press Enter to continue...")
        
        input()
        
        try:
            async with async_playwright() as p:
                # Connect to an already open browser
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                contexts = browser.contexts
                
                if contexts:
                    context = contexts[0]
                    pages = context.pages
                    
                    # Look for Douyin page
                    douyin_page = None
                    for page in pages:
                        if 'douyin.com' in page.url:
                            douyin_page = page
                            break
                    
                    if douyin_page:
                        # Extract Cookies
                        cookies = await context.cookies()
                        cookie_dict = {}
                        
                        for cookie in cookies:
                            if 'douyin.com' in cookie.get('domain', ''):
                                cookie_dict[cookie['name']] = cookie['value']
                        
                        if cookie_dict:
                            console.print("[green]✅ Successfully extracted Cookies![/green]")
                            self._save_cookies(cookie_dict)
                            return cookie_dict
                        else:
                            console.print("[red]Douyin Cookies not found[/red]")
                    else:
                        console.print("[red]Douyin page not found, please visit douyin.com first[/red]")
                else:
                    console.print("[red]Browser context not found[/red]")
                    
        except Exception as e:
            console.print(f"[red]Failed to connect to browser: {e}[/red]")
            console.print("[yellow]Please ensure the browser is launched in debug mode[/yellow]")
        
        return {}


async def main():
    """Main function"""
    extractor = CookieExtractor()
    
    console.print("\n[cyan]Please select extraction method:[/cyan]")
    console.print("1. Auto login extraction (Recommended)")
    console.print("2. Extract from an already logged-in browser")
    console.print("3. Manually enter Cookies")
    
    choice = Prompt.ask("Please selection", choices=["1", "2", "3"], default="1")
    
    if choice == "1":
        # Auto login extraction
        headless = not Confirm.ask("Show browser interface?", default=True)
        cookies = await extractor.extract_cookies(headless=headless)
        
    elif choice == "2":
        # Extract from an already logged-in browser
        cookies = await extractor.quick_extract()
        
    else:
        # Manual entry
        console.print("\n[cyan]Please enter Cookie string:[/cyan]")
        console.print("[dim]Format: name1=value1; name2=value2; ...[/dim]")
        cookie_string = Prompt.ask("Cookie")
        
        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookies[key] = value
        
        if cookies:
            extractor._save_cookies(cookies)
            console.print("[green]✅ Cookies saved[/green]")
    
    if cookies:
        console.print("\n[green]✅ Cookie extraction complete![/green]")
        console.print("[dim]You can now run the downloader:[/dim]")
        console.print("python3 downloader.py -c config_simple.yml")
    else:
        console.print("\n[red]❌ Failed to extract Cookies[/red]")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Program exception: {e}[/red]")
