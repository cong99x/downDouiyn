#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
抖音下载器 - 统一增强版
支持视频、图文、用户主页、合集等多种内容的批量下载
"""

import asyncio
import json
import copy
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import argparse
import yaml

# 第三方库
try:
    import aiohttp
    import requests
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich import print as rprint
except ImportError as e:
    print(f"Please install necessary dependencies: pip install aiohttp requests rich pyyaml")
    sys.exit(1)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
from apiproxy.douyin import douyin_headers
from apiproxy.douyin.urls import Urls
from apiproxy.douyin.result import Result
from apiproxy.common.utils import Utils
from apiproxy.douyin.auth.cookie_manager import AutoCookieManager
from apiproxy.douyin.database import DataBase
from apiproxy.douyin.douyin import Douyin
from apiproxy.tiktok.tiktok import TikTok

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('downloader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rich console
console = Console()


class ContentType:
    """内容类型枚举"""
    VIDEO = "video"
    IMAGE = "image" 
    USER = "user"
    MIX = "mix"
    MUSIC = "music"
    LIVE = "live"

class Platform:
    """平台类型枚举"""
    DOUYIN = "douyin"
    TIKTOK = "tiktok"


class DownloadStats:
    """下载统计"""
    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = time.time()
    
    @property
    def success_rate(self):
        return (self.success / self.total * 100) if self.total > 0 else 0
    
    @property
    def elapsed_time(self):
        return time.time() - self.start_time
    
    def to_dict(self):
        return {
            'total': self.total,
            'success': self.success,
            'failed': self.failed,
            'skipped': self.skipped,
            'success_rate': f"{self.success_rate:.1f}%",
            'elapsed_time': f"{self.elapsed_time:.1f}s"
        }


class RateLimiter:
    """Rate Limiter"""
    def __init__(self, max_per_second: float = 2):
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_request = 0
    
    async def acquire(self):
        """Acquire permission"""
        current = time.time()
        time_since_last = current - self.last_request
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last)
        self.last_request = time.time()


class RetryManager:
    """Retry Manager"""
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute function and auto-retry"""
        last_error = None
        retry_delays = [1, 2, 5]
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        raise last_error


class UnifiedDownloader:
    """Unified Downloader"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.config = self._load_config(config_path)
        self.urls_helper = Urls()
        self.result_helper = Result()
        self.utils = Utils()
        
        # Core Platform Clients
        self.douyin = Douyin()
        self.tiktok = TikTok()
        
        # 组件初始化
        self.stats = DownloadStats()
        self.rate_limiter = RateLimiter(max_per_second=2)
        self.retry_manager = RetryManager(max_retries=self.config.get('retry_times', 3))
        
        # Cookie与请求头（延迟初始化，支持自动获取）
        self.cookies = self.config.get('cookies') if 'cookies' in self.config else self.config.get('cookie')
        self.auto_cookie = bool(self.config.get('auto_cookie')) or (isinstance(self.config.get('cookie'), str) and self.config.get('cookie') == 'auto') or (isinstance(self.config.get('cookies'), str) and self.config.get('cookies') == 'auto')
        self.headers = {**douyin_headers}
        # 避免服务端使用brotli导致aiohttp无法解压（未安装brotli库时会出现空响应）
        self.headers['accept-encoding'] = 'gzip, deflate'
        # 增量下载与数据库
        self.increase_cfg: Dict[str, Any] = self.config.get('increase', {}) or {}
        self.enable_database: bool = bool(self.config.get('database', True))
        self.db: Optional[DataBase] = DataBase() if self.enable_database else None
        
        # S3 Uploader
        from utils.s3_uploader import S3Uploader
        self.s3_uploader = S3Uploader(self.config)
        
        # 保存路径
        self.save_path = Path(self.config.get('path', './Downloaded'))
        self.save_path.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        if not os.path.exists(config_path):
            # 兼容配置文件命名：优先 config.yml，其次 config_simple.yml
            alt_path = 'config_simple.yml'
            if os.path.exists(alt_path):
                config_path = alt_path
            else:
                # Return empty config, let command line args decide
                return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Simplify config compatibility: links/link, output_dir/path, cookie/cookies
        if 'links' in config and 'link' not in config:
            config['link'] = config['links']
        if 'output_dir' in config and 'path' not in config:
            config['path'] = config['output_dir']
        if 'cookie' in config and 'cookies' not in config:
            config['cookies'] = config['cookie']
        if isinstance(config.get('cookies'), str) and config.get('cookies') == 'auto':
            config['auto_cookie'] = True
        
        # Allow no link (passed via command line)
        # If both are missing, a prompt will appear at runtime
        
        return config
    
    def _build_cookie_string(self) -> str:
        """构建Cookie字符串"""
        if isinstance(self.cookies, str):
            return self.cookies
        elif isinstance(self.cookies, dict):
            return '; '.join([f'{k}={v}' for k, v in self.cookies.items()])
        elif isinstance(self.cookies, list):
            # 支持来自AutoCookieManager的cookies列表
            try:
                kv = {c.get('name'): c.get('value') for c in self.cookies if c.get('name') and c.get('value')}
                return '; '.join([f'{k}={v}' for k, v in kv.items()])
            except Exception:
                return ''
        return ''

    async def _initialize_cookies_and_headers(self):
        """初始化Cookie与请求头（支持自动获取）"""
        # 若配置为字符串 'auto'，视为未提供，触发自动获取
        if isinstance(self.cookies, str) and self.cookies.strip().lower() == 'auto':
            self.cookies = None
        
        # 若已显式提供cookies，则直接使用
        cookie_str = self._build_cookie_string()
        if cookie_str:
            self.headers['Cookie'] = cookie_str
            # 同时设置到全局 douyin_headers，确保所有 API 请求都能使用
            from apiproxy.douyin import douyin_headers
            douyin_headers['Cookie'] = cookie_str
            return
        
        # 自动获取Cookie
        if self.auto_cookie:
            try:
                console.print("[cyan]🔐 Automatically acquiring Cookie...[/cyan]")
                async with AutoCookieManager(cookie_file='cookies.pkl', headless=False) as cm:
                    cookies_list = await cm.get_cookies()
                    if cookies_list:
                        self.cookies = cookies_list
                        cookie_str = self._build_cookie_string()
                        if cookie_str:
                            self.headers['Cookie'] = cookie_str
                            # Set to global douyin_headers as well, ensure all API requests can use it
                            from apiproxy.douyin import douyin_headers
                            douyin_headers['Cookie'] = cookie_str
                            console.print("[green]✅ Cookie acquired successfully[/green]")
                            return
                console.print("[yellow]⚠️ Automatic Cookie acquisition failed or empty, continuing in no-Cookie mode[/yellow]")
            except Exception as e:
                logger.warning(f"Failed to automatically acquire Cookie: {e}")
                console.print("[yellow]⚠️ Automatic Cookie acquisition failed, continuing in no-Cookie mode[/yellow]")
        
        # If Cookie acquisition fails, don't set it, use default headers
    
    def _clean_urls(self, urls: List[str]) -> List[str]:
        """清理 URL 列表，处理分享文本被碎片化的情况"""
        if not urls:
            return []
        
        # 尝试从所有片段中提取真正的 URL
        # 如果是命令行 -u 传入的，碎片会被空格分开在 urls 列表中
        combined_text = " ".join(urls)
        extracted = self.utils.extract_urls(combined_text)
        
        if extracted:
            logger.info(f"从输入中提取到 {len(extracted)} 个有效 URL")
            return list(dict.fromkeys(extracted))  # 去重
        
        # 如果没有提取到 http/https，则返回原列表（或者是空，取决于是否有必要保留碎片）
        # 这里的策略是只保留看起来像 URL 的片段
        cleaned = []
        for u in urls:
            u = u.strip()
            if u.startswith('http') or '.douyin.com' in u:
                cleaned.append(u)
        
        return cleaned

    def detect_platform(self, url: str) -> Platform:
        """检测 URL 所属平台"""
        if 'tiktok.com' in url:
            return Platform.TIKTOK
        return Platform.DOUYIN

    def detect_content_type(self, url: str) -> ContentType:
        """检测URL内容类型"""
        # TikTok patterns
        if 'tiktok.com' in url:
            if '/video/' in url or '/photo/' in url:
                return ContentType.VIDEO
            elif '@' in url:
                return ContentType.USER
            return ContentType.VIDEO

        # Douyin patterns
        if '/user/' in url:
            return ContentType.USER
        elif '/video/' in url or 'v.douyin.com' in url:
            return ContentType.VIDEO
        elif '/note/' in url:
            return ContentType.IMAGE
        elif '/collection/' in url or '/mix/' in url:
            return ContentType.MIX
        elif '/music/' in url:
            return ContentType.MUSIC
        elif 'live.douyin.com' in url:
            return ContentType.LIVE
        else:
            return ContentType.VIDEO  # 默认当作视频
    
    async def resolve_short_url(self, url: str) -> str:
        """解析短链接"""
        if 'v.douyin.com' in url:
            try:
                # 使用同步请求获取重定向
                response = requests.get(url, headers=self.headers, allow_redirects=True, timeout=10)
                final_url = response.url
                logger.info(f"解析短链接: {url} -> {final_url}")
                return final_url
            except Exception as e:
                logger.warning(f"解析短链接失败: {e}")
        return url
    
    def extract_id_from_url(self, url: str, content_type: ContentType = None) -> Optional[str]:
        """从URL提取ID
        
        Args:
            url: 要解析的URL
            content_type: 内容类型（可选，用于指导提取）
        """
        # 如果已知是用户页面，直接提取用户ID
        if content_type == ContentType.USER or '/user/' in url:
            user_patterns = [
                r'/user/([\w-]+)',
                r'sec_uid=([\w-]+)'
            ]
            
            for pattern in user_patterns:
                match = re.search(pattern, url)
                if match:
                    user_id = match.group(1)
                    logger.info(f"提取到用户ID: {user_id}")
                    return user_id
        
        # 视频ID模式（优先）
        video_patterns = [
            r'/video/(\d+)',
            r'/note/(\d+)',
            r'modal_id=(\d+)',
            r'aweme_id=(\d+)',
            r'item_id=(\d+)'
        ]
        
        for pattern in video_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(f"提取到视频ID: {video_id}")
                return video_id
        
        # 其他模式
        other_patterns = [
            r'/collection/(\d+)',
            r'/music/(\d+)'
        ]
        
        for pattern in other_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 尝试从URL中提取数字ID
        number_match = re.search(r'(\d{15,20})', url)
        if number_match:
            video_id = number_match.group(1)
            logger.info(f"从URL提取到数字ID: {video_id}")
            return video_id
        
        logger.error(f"无法从URL提取ID: {url}")
        return None

    def _get_aweme_id_from_info(self, info: Dict) -> Optional[str]:
        """从 aweme 信息中提取 aweme_id"""
        try:
            if 'aweme_id' in info:
                return str(info.get('aweme_id'))
            # aweme_detail 结构
            return str(info.get('aweme', {}).get('aweme_id') or info.get('aweme_id'))
        except Exception:
            return None

    def _get_sec_uid_from_info(self, info: Dict) -> Optional[str]:
        """从 aweme 信息中提取作者 sec_uid"""
        try:
            return info.get('author', {}).get('sec_uid')
        except Exception:
            return None

    def _should_skip_increment(self, context: str, info: Dict, mix_id: Optional[str] = None, music_id: Optional[str] = None, sec_uid: Optional[str] = None) -> bool:
        """根据增量配置与数据库记录判断是否跳过下载"""
        if not self.db:
            return False
        aweme_id = self._get_aweme_id_from_info(info)
        if not aweme_id:
            return False

        try:
            if context == 'post' and self.increase_cfg.get('post', False):
                sec = sec_uid or self._get_sec_uid_from_info(info) or ''
                return bool(self.db.get_user_post(sec, int(aweme_id)) if aweme_id.isdigit() else None)
            if context == 'like' and self.increase_cfg.get('like', False):
                sec = sec_uid or self._get_sec_uid_from_info(info) or ''
                return bool(self.db.get_user_like(sec, int(aweme_id)) if aweme_id.isdigit() else None)
            if context == 'mix' and self.increase_cfg.get('mix', False):
                sec = sec_uid or self._get_sec_uid_from_info(info) or ''
                mid = mix_id or ''
                return bool(self.db.get_mix(sec, mid, int(aweme_id)) if aweme_id.isdigit() else None)
            if context == 'music' and self.increase_cfg.get('music', False):
                mid = music_id or ''
                return bool(self.db.get_music(mid, int(aweme_id)) if aweme_id.isdigit() else None)
        except Exception:
            return False
        return False

    def _record_increment(self, context: str, info: Dict, mix_id: Optional[str] = None, music_id: Optional[str] = None, sec_uid: Optional[str] = None):
        """下载成功后写入数据库记录"""
        if not self.db:
            return
        aweme_id = self._get_aweme_id_from_info(info)
        if not aweme_id or not aweme_id.isdigit():
            return
        try:
            if context == 'post':
                sec = sec_uid or self._get_sec_uid_from_info(info) or ''
                self.db.insert_user_post(sec, int(aweme_id), info)
            elif context == 'like':
                sec = sec_uid or self._get_sec_uid_from_info(info) or ''
                self.db.insert_user_like(sec, int(aweme_id), info)
            elif context == 'mix':
                sec = sec_uid or self._get_sec_uid_from_info(info) or ''
                mid = mix_id or ''
                self.db.insert_mix(sec, mid, int(aweme_id), info)
            elif context == 'music':
                mid = music_id or ''
                self.db.insert_music(mid, int(aweme_id), info)
        except Exception:
            pass
    
    async def download_single_video(self, url: str, progress=None, client=None) -> bool:
        """下载单个视频/图文"""
        try:
            # 解析短链接
            url = await self.resolve_short_url(url)
            
            # 提取ID
            video_id = self.extract_id_from_url(url, ContentType.VIDEO)
            if not video_id:
                logger.error(f"无法从URL提取ID: {url}")
                return False
            
            # 如果没有提取到视频ID，尝试作为视频ID直接使用
            if not video_id and '/user/' not in url:
                # 可能短链接直接包含了视频ID
                video_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                logger.info(f"尝试从短链接路径提取ID: {video_id}")
            
            if not video_id:
                logger.error(f"无法从URL提取视频ID: {url}")
                return False
            
            # 限速
            await self.rate_limiter.acquire()
            
            # 获取视频信息
            if progress:
                progress.update(task_id=progress.task_ids[-1], description="Acquiring video info...")
            
            video_info = await self.retry_manager.execute_with_retry(
                self._fetch_video_info, video_id, client=client
            )
            
            if not video_info:
                logger.error(f"无法获取视频信息: {video_id}")
                self.stats.failed += 1
                return False
            
            # 下载视频文件
            if progress:
                progress.update(task_id=progress.task_ids[-1], description="Downloading video file...")
            
            success = await self._download_media_files(video_info, progress)
            
            if success:
                self.stats.success += 1
                logger.info(f"✅ 下载成功: {url}")
            else:
                self.stats.failed += 1
                logger.error(f"❌ 下载失败: {url}")
            
            return success
            
        except Exception as e:
            logger.error(f"下载视频异常 {url}: {e}")
            self.stats.failed += 1
            return False
        finally:
            self.stats.total += 1
    
    async def _fetch_video_info(self, video_id: str, client=None) -> Optional[Dict]:
        """获取视频信息"""
        try:
            # If client is provided (pre-initialized TikTok or Douyin), use it
            if client:
                # Ensure cookies are set to the client
                cookie_str = self._build_cookie_string()
                if cookie_str and hasattr(client, 'set_cookies'):
                    client.set_cookies(cookie_str)
                
                # Check if getAwemeInfo is async or sync
                import asyncio
                import inspect
                if asyncio.iscoroutinefunction(client.getAwemeInfo) or inspect.iscoroutinefunction(client.getAwemeInfo):
                    result = await client.getAwemeInfo(video_id)
                else:
                    result = client.getAwemeInfo(video_id)
                    
                if result:
                    logger.info(f"API Client ({type(client).__name__}) 成功获取视频信息")
                    return result
            
            # Default fallback to existing Douyin logic
            from apiproxy.douyin.douyin import Douyin
            dy = client if isinstance(client, Douyin) else Douyin(database=False)
            
            # 设置我们的 cookies 到 douyin_headers
            if hasattr(self, 'cookies') and self.cookies:
                cookie_str = self._build_cookie_string()
                if cookie_str:
                    from apiproxy.douyin import douyin_headers
                    douyin_headers['Cookie'] = cookie_str
                    logger.info(f"设置 Cookie 到 Douyin 类: {cookie_str[:100]}...")
            
            try:
                # 使用现有的成功实现
                result = await dy.getAwemeInfo(video_id)
                if result:
                    logger.info(f"Douyin 类成功获取视频信息: {result.get('desc', '')[:30]}")
                    return result
                else:
                    logger.error("Douyin 类返回空结果")
                    
            except Exception as e:
                logger.error(f"Douyin 类获取视频信息失败: {e}")
                
        except Exception as e:
            logger.error(f"导入或使用 Douyin 类失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 如果 Douyin 类失败，尝试备用接口（iesdouyin，无需X-Bogus）
        try:
            fallback_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"
            logger.info(f"尝试备用接口获取视频信息: {fallback_url}")
            
            # 设置更通用的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.douyin.com/',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(fallback_url, headers=headers, timeout=15) as response:
                    logger.info(f"备用接口响应状态: {response.status}")
                    if response.status != 200:
                        logger.error(f"备用接口请求失败，状态码: {response.status}")
                        return None
                    
                    text = await response.text()
                    logger.info(f"备用接口响应内容长度: {len(text)}")
                    
                    if not text:
                        logger.error("备用接口响应为空")
                        return None
                    
                    try:
                        data = json.loads(text)
                        logger.info(f"备用接口返回数据: {data}")
                        
                        item_list = (data or {}).get('item_list') or []
                        if item_list:
                            aweme_detail = item_list[0]
                            logger.info("备用接口成功获取视频信息")
                            return aweme_detail
                        else:
                            logger.error("备用接口返回的数据中没有 item_list")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"备用接口JSON解析失败: {e}")
                        logger.error(f"原始响应内容: {text}")
                        return None
                        
        except Exception as e:
            logger.error(f"备用接口获取视频信息失败: {e}")
        
        return None
    
    def _build_detail_params(self, aweme_id: str) -> str:
        """构建详情API参数"""
        # 使用与现有 douyinapi.py 相同的参数格式
        params = [
            f'aweme_id={aweme_id}',
            'device_platform=webapp',
            'aid=6383'
        ]
        return '&'.join(params)
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        if not filename:
            return ""
        # 替换 Windows 不允许的字符: \ / : * ? " < > |
        # 使用正则替换为下划线
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
        # 去重下划线
        filename = re.sub(r'_+', '_', filename)
        # 去除首尾空格和点 (Windows 不允许文件夹以点或空格结尾)
        filename = filename.strip(' .')
        return filename

    async def _download_media_files(self, video_info: Dict, progress=None) -> bool:
        """下载媒体文件"""
        try:
            # 判断类型
            is_image = bool(video_info.get('images'))
            
            # 构建保存路径
            author_name = self._sanitize_filename(video_info.get('author', {}).get('nickname', 'unknown'))
            desc = self._sanitize_filename(video_info.get('desc', '')[:50])
            # 兼容 create_time 为时间戳或格式化字符串
            raw_create_time = video_info.get('create_time')
            dt_obj = None
            if isinstance(raw_create_time, (int, float)):
                dt_obj = datetime.fromtimestamp(raw_create_time)
            elif isinstance(raw_create_time, str) and raw_create_time:
                for fmt in ('%Y-%m-%d %H.%M.%S', '%Y-%m-%d_%H-%M-%S', '%Y-%m-%d %H:%M:%S'):
                    try:
                        dt_obj = datetime.strptime(raw_create_time, fmt)
                        break
                    except Exception:
                        pass
            if dt_obj is None:
                dt_obj = datetime.fromtimestamp(time.time())
            create_time = dt_obj.strftime('%Y-%m-%d_%H-%M-%S')
            
            folder_name = f"{create_time}_{desc}" if desc else create_time
            # Ensure folder_name is also sanitized (it should be since desc is)
            folder_name = self._sanitize_filename(folder_name)
            
            save_dir = self.save_path / author_name / folder_name
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 决定下载用的 headers 和 cookies
            download_headers = copy.deepcopy(self.headers)
            download_cookies = None
            
            # 简单判断是否为 TikTok
            is_tiktok = False
            
            success = True
            
            if is_image:
                # 下载图文（无水印）
                images = video_info.get('images', [])
                for i, img in enumerate(images):
                    img_url = self._get_best_quality_url(img.get('url_list', []))
                    if img_url:
                        if 'tiktok' in img_url: is_tiktok = True
                        if is_tiktok:
                            from apiproxy.tiktok import tiktok_headers
                            download_headers = {**tiktok_headers}
                            download_cookies = self.tiktok.api.get_session_cookies()
                        
                        file_path = save_dir / f"image_{i+1}.jpg"
                        if await self._download_file(img_url, file_path, headers=download_headers, cookies=download_cookies):
                            logger.info(f"下载图片 {i+1}/{len(images)}: {file_path.name}")
                            # S3 Upload
                            if self.s3_uploader.enabled:
                                try:
                                    rel_path = file_path.relative_to(self.save_path).as_posix()
                                    self.s3_uploader.upload_file(str(file_path), object_name=rel_path)
                                except Exception:
                                    self.s3_uploader.upload_file(str(file_path))
                        else:
                            success = False
            else:
                # 下载视频（无水印）
                video_url = self._get_no_watermark_url(video_info)
                if video_url:
                    if 'tiktok' in video_url: is_tiktok = True
                    if is_tiktok:
                        from apiproxy.tiktok import tiktok_headers
                        download_headers = {**tiktok_headers}
                        download_cookies = self.tiktok.api.get_session_cookies()
                    
                    file_path = save_dir / f"{folder_name}.mp4"
                    download_func = self._download_file_sync if is_tiktok else self._download_file
                    if await download_func(video_url, file_path, headers=download_headers, cookies=download_cookies):
                        logger.info(f"下载视频: {file_path.name}")
                        # S3 Upload
                        if self.s3_uploader.enabled:
                            try:
                                rel_path = file_path.relative_to(self.save_path).as_posix()
                                self.s3_uploader.upload_file(str(file_path), object_name=rel_path)
                            except Exception:
                                self.s3_uploader.upload_file(str(file_path))
                    else:
                        success = False
                
                # 下载音频
                if self.config.get('music', True):
                    music_url = self._get_music_url(video_info)
                    if music_url:
                        # Re-check for music url platform
                        file_path = save_dir / f"{folder_name}_music.mp3"
                        # Use same headers/cookies as video for simplicity
                        if is_tiktok:
                            await self._download_file_sync(music_url, file_path, headers=download_headers, cookies=download_cookies)
                        else:
                            await self._download_file(music_url, file_path, headers=download_headers, cookies=download_cookies)
                        
                        # S3 Upload (optional for music)
                        if self.s3_uploader.enabled and os.path.exists(file_path):
                            try:
                                rel_path = file_path.relative_to(self.save_path).as_posix()
                                self.s3_uploader.upload_file(str(file_path), object_name=rel_path)
                            except Exception:
                                self.s3_uploader.upload_file(str(file_path))
            
            # 下载封面
            if self.config.get('cover', True):
                cover_url = self._get_cover_url(video_info)
                if cover_url:
                    file_path = save_dir / f"{folder_name}_cover.jpg"
                    if is_tiktok:
                        await self._download_file_sync(cover_url, file_path, headers=download_headers, cookies=download_cookies)
                    else:
                        await self._download_file(cover_url, file_path)
                    
                    # S3 Upload (optional for cover)
                    if self.s3_uploader.enabled and os.path.exists(file_path):
                        try:
                            rel_path = file_path.relative_to(self.save_path).as_posix()
                            self.s3_uploader.upload_file(str(file_path), object_name=rel_path)
                        except Exception:
                            self.s3_uploader.upload_file(str(file_path))
            
            # 保存JSON数据
            if self.config.get('json', True):
                json_path = save_dir / f"{folder_name}_data.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(video_info, f, ensure_ascii=False, indent=2)
                
                # S3 Upload (optional for json)
                if self.s3_uploader.enabled:
                    try:
                        rel_path = json_path.relative_to(self.save_path).as_posix()
                        self.s3_uploader.upload_file(str(json_path), object_name=rel_path)
                    except Exception:
                        self.s3_uploader.upload_file(str(json_path))
            
            return success
            
        except Exception as e:
            logger.error(f"下载媒体文件失败: {e}")
            return False
    
    def _get_no_watermark_url(self, video_info: Dict) -> Optional[str]:
        """获取无水印视频URL"""
        try:
            # 优先使用play_addr_h264
            play_addr = video_info.get('video', {}).get('play_addr_h264') or \
                       video_info.get('video', {}).get('play_addr')
            
            if play_addr:
                url_list = play_addr.get('url_list', [])
                if url_list:
                    # 替换URL以获取无水印版本
                    url = url_list[0]
                    url = url.replace('playwm', 'play')
                    url = url.replace('720p', '1080p')
                    return url
            
            # 备用：download_addr
            download_addr = video_info.get('video', {}).get('download_addr')
            if download_addr:
                url_list = download_addr.get('url_list', [])
                if url_list:
                    return url_list[0]
                    
        except Exception as e:
            logger.error(f"获取无水印URL失败: {e}")
        
        return None
    
    def _get_best_quality_url(self, url_list: List[str]) -> Optional[str]:
        """获取最高质量的URL"""
        if not url_list:
            return None
        
        # 优先选择包含特定关键词的URL
        for keyword in ['1080', 'origin', 'high']:
            for url in url_list:
                if keyword in url:
                    return url
        
        # 返回第一个
        return url_list[0]
    
    def _get_music_url(self, video_info: Dict) -> Optional[str]:
        """获取音乐URL"""
        try:
            music = video_info.get('music', {})
            play_url = music.get('play_url', {})
            url_list = play_url.get('url_list', [])
            return url_list[0] if url_list else None
        except:
            return None
    
    def _get_cover_url(self, video_info: Dict) -> Optional[str]:
        """获取封面URL"""
        try:
            cover = video_info.get('video', {}).get('cover', {})
            url_list = cover.get('url_list', [])
            return self._get_best_quality_url(url_list)
        except:
            return None
    
    async def _download_file(self, url: str, save_path: Path, headers: Dict = None, cookies: Dict = None) -> bool:
        """下载文件"""
        try:
            if save_path.exists():
                logger.info(f"文件已存在，跳过: {save_path.name}")
                return True
            
            final_headers = headers if headers is not None else self.headers
            
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.get(url, headers=final_headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        return True
                    else:
                        logger.error(f"下载失败，状态码: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"下载文件失败 {url}: {e}")
            return False

    async def _download_file_sync(self, url: str, save_path: Path, headers: Dict = None, cookies: Dict = None) -> bool:
        """同步下载文件 (用于 TikTok 等对 aiohttp 敏感的平台)"""
        return await asyncio.to_thread(self._do_download_file_sync, url, save_path, headers, cookies)

    def _do_download_file_sync(self, url: str, save_path: Path, headers: Dict = None, cookies: Dict = None) -> bool:
        try:
            if save_path.exists():
                return True
            
            final_headers = headers if headers is not None else self.headers
            
            with requests.Session() as s:
                if cookies:
                    s.cookies.update(cookies)
                
                with s.get(url, headers=final_headers, stream=True, timeout=30) as r:
                    if r.status_code == 200:
                        with open(save_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        return True
                    else:
                        logger.error(f"同步下载失败，状态码: {r.status_code}")
                        return False
        except Exception as e:
            logger.error(f"同步下载异常 {url}: {e}")
            return False
    
    async def download_user_page(self, url: str, client=None) -> bool:
        """下载用户主页内容"""
        try:
            # 提取用户ID
            user_id = self.extract_id_from_url(url, ContentType.USER)
            if not user_id:
                logger.error(f"无法从URL提取用户ID: {url}")
                return False
            
            console.print(f"\n[cyan]Acquiring work list for user {user_id}...[/cyan]")
            
            # 根据配置下载不同类型的内容
            mode = self.config.get('mode', ['post'])
            if isinstance(mode, str):
                mode = [mode]
            
            # 增加总任务数统计
            total_posts = 0
            if 'post' in mode:
                total_posts += self.config.get('number', {}).get('post', 0) or 1
            if 'like' in mode:
                total_posts += self.config.get('number', {}).get('like', 0) or 1
            if 'mix' in mode:
                total_posts += self.config.get('number', {}).get('allmix', 0) or 1
            
            self.stats.total += total_posts
            
            for m in mode:
                if m == 'post':
                    await self._download_user_posts(user_id)
                elif m == 'like':
                    await self._download_user_likes(user_id)
                elif m == 'mix':
                    await self._download_user_mixes(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"下载用户主页失败: {e}")
            return False
    
    async def _download_user_posts(self, user_id: str):
        """Download user published works"""
        max_count = self.config.get('number', {}).get('post', 0)
        await self.download_user_works(user_id, mode="post", max_count=max_count)

    async def download_user_works(self, user_id: str, mode: str = "post", max_count: int = 0):
        """Download user works"""
        console.print(f"[cyan]🚀 Starting download for user: {user_id} (Mode: {mode})[/cyan]")
        
        try:
            # Fetch work list
            aweme_list = self.api.getUserInfo(user_id, mode=mode, number=max_count)
            if not aweme_list:
                console.print("[yellow]No works found or failed to fetch[/yellow]")
                return
            
            console.print(f"[green]Found {len(aweme_list)} candidate works[/green]")
            
            downloaded = 0
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                # Download works
                for aweme in aweme_list:
                    if max_count > 0 and downloaded >= max_count:
                        console.print(f"[yellow]Reached download limit: {max_count}[/yellow]")
                        return
                    
                    # Time filter
                    if not self._check_time_filter(aweme):
                        continue
                    
                    # Create download task
                    task_id = progress.add_task(
                        f"Downloading work {downloaded + 1}", 
                        total=100
                    )
                    
                    # Incremental check
                    if self._should_skip_increment('post', aweme, sec_uid=user_id):
                        continue
                    
                    # Download
                    success = await self._download_media_files(aweme, progress, task_id)
                    
                    if success:
                        downloaded += 1
                        self.stats.success += 1  # Increment success count
                        progress.update(task_id, completed=100)
                        self._record_increment('post', aweme, sec_uid=user_id)
                    else:
                        self.stats.failed += 1  # Increment failure count
                        progress.update(task_id, description="[red]Download failed[/red]")
        except Exception as e:
            logger.error(f"Download user works error: {str(e)}")
            console.print(f"[red]❌ Error: {str(e)}[/red]")
        
        console.print(f"[green]✅ User works download complete, {downloaded} items downloaded in total[/green]")
    
    async def _fetch_user_posts(self, user_id: str, cursor: int = 0) -> Optional[Dict]:
        """获取用户作品列表"""
        try:
            # 直接使用 Douyin 类的 getUserInfo 方法，就像 DouYinCommand.py 那样
            from apiproxy.douyin.douyin import Douyin
            
            # 创建 Douyin 实例
            dy = Douyin(database=False)
            
            # 获取用户作品列表
            result = dy.getUserInfo(
                user_id, 
                "post", 
                35, 
                0,  # 不限制数量
                False,  # 不启用增量
                "",  # start_time
                ""   # end_time
            )
            
            if result:
                logger.info(f"Douyin 类成功获取用户作品列表，共 {len(result)} 个作品")
                # 转换为期望的格式
                return {
                    'status_code': 0,
                    'aweme_list': result,
                    'max_cursor': cursor,
                    'has_more': False
                }
            else:
                logger.error("Douyin 类返回空结果")
                return None
                
        except Exception as e:
            logger.error(f"获取用户作品列表失败: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    async def _download_user_likes(self, user_id: str):
        """下载用户喜欢的作品"""
        max_count = 0
        try:
            max_count = int(self.config.get('number', {}).get('like', 0))
        except Exception:
            max_count = 0
        cursor = 0
        downloaded = 0

        console.print(f"\n[green]Starting download of user's liked works...[/green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:

            while True:
                # 限速
                await self.rate_limiter.acquire()

                # 获取喜欢列表
                likes_data = await self._fetch_user_likes(user_id, cursor)
                if not likes_data:
                    break

                aweme_list = likes_data.get('aweme_list', [])
                if not aweme_list:
                    break

                # 下载作品
                for aweme in aweme_list:
                    if max_count > 0 and downloaded >= max_count:
                        console.print(f"[yellow]已达到下载数量限制: {max_count}[/yellow]")
                        return

                    if not self._check_time_filter(aweme):
                        continue

                    task_id = progress.add_task(
                        f"Downloading like {downloaded + 1}",
                        total=100
                    )

                    # 增量判断
                    if self._should_skip_increment('like', aweme, sec_uid=user_id):
                        continue

                    success = await self._download_media_files(aweme, progress)

                    if success:
                        downloaded += 1
                        progress.update(task_id, completed=100)
                        self._record_increment('like', aweme, sec_uid=user_id)
                    else:
                        progress.update(task_id, description="[red]下载失败[/red]")

                # 翻页
                if not likes_data.get('has_more'):
                    break
                cursor = likes_data.get('max_cursor', 0)

        console.print(f"[green]✅ Liked works download complete, {downloaded} items downloaded in total[/green]")

    async def _fetch_user_likes(self, user_id: str, cursor: int = 0) -> Optional[Dict]:
        """获取用户喜欢的作品列表"""
        try:
            params_list = [
                f'sec_user_id={user_id}',
                f'max_cursor={cursor}',
                'count=35',
                'aid=6383',
                'device_platform=webapp',
                'channel=channel_pc_web',
                'pc_client_type=1',
                'version_code=170400',
                'version_name=17.4.0',
                'cookie_enabled=true',
                'screen_width=1920',
                'screen_height=1080',
                'browser_language=zh-CN',
                'browser_platform=MacIntel',
                'browser_name=Chrome',
                'browser_version=122.0.0.0',
                'browser_online=true'
            ]
            params = '&'.join(params_list)

            api_url = self.urls_helper.USER_FAVORITE_A

            try:
                xbogus = self.utils.getXbogus(params)
                full_url = f"{api_url}{params}&X-Bogus={xbogus}"
            except Exception as e:
                logger.warning(f"获取X-Bogus失败: {e}, 尝试不带X-Bogus")
                full_url = f"{api_url}{params}"

            logger.info(f"请求用户喜欢列表: {full_url[:100]}...")

            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"请求失败，状态码: {response.status}")
                        return None

                    text = await response.text()
                    if not text:
                        logger.error("响应内容为空")
                        return None

                    data = json.loads(text)
                    if data.get('status_code') == 0:
                        return data
                    else:
                        logger.error(f"API返回错误: {data.get('status_msg', '未知错误')}")
                        return None
        except Exception as e:
            logger.error(f"获取用户喜欢列表失败: {e}")
        return None

    async def _download_user_mixes(self, user_id: str):
        """下载用户的所有合集（按配置可限制数量）"""
        max_allmix = 0
        try:
            # 兼容旧键名 allmix 或 mix
            number_cfg = self.config.get('number', {}) or {}
            max_allmix = int(number_cfg.get('allmix', number_cfg.get('mix', 0)) or 0)
        except Exception:
            max_allmix = 0

        cursor = 0
        fetched = 0

        console.print(f"\n[green]Starting to acquire user's collection list...[/green]")
        while True:
            await self.rate_limiter.acquire()
            mix_list_data = await self._fetch_user_mix_list(user_id, cursor)
            if not mix_list_data:
                break

            mix_infos = mix_list_data.get('mix_infos') or []
            if not mix_infos:
                break

            for mix in mix_infos:
                if max_allmix > 0 and fetched >= max_allmix:
                    console.print(f"[yellow]已达到合集数量限制: {max_allmix}[/yellow]")
                    return
                mix_id = mix.get('mix_id')
                mix_name = mix.get('mix_name', '')
                console.print(f"[cyan]Downloading collection[/cyan]: {mix_name} ({mix_id})")
                await self._download_mix_by_id(mix_id)
                fetched += 1

            if not mix_list_data.get('has_more'):
                break
            cursor = mix_list_data.get('cursor', 0)

        console.print(f"[green]✅ User collections download complete, {fetched} items processed in total[/green]")

    async def _fetch_user_mix_list(self, user_id: str, cursor: int = 0) -> Optional[Dict]:
        """获取用户合集列表"""
        try:
            params_list = [
                f'sec_user_id={user_id}',
                f'cursor={cursor}',
                'count=35',
                'aid=6383',
                'device_platform=webapp',
                'channel=channel_pc_web',
                'pc_client_type=1',
                'version_code=170400',
                'version_name=17.4.0',
                'cookie_enabled=true',
                'screen_width=1920',
                'screen_height=1080',
                'browser_language=zh-CN',
                'browser_platform=MacIntel',
                'browser_name=Chrome',
                'browser_version=122.0.0.0',
                'browser_online=true'
            ]
            params = '&'.join(params_list)

            api_url = self.urls_helper.USER_MIX_LIST
            try:
                xbogus = self.utils.getXbogus(params)
                full_url = f"{api_url}{params}&X-Bogus={xbogus}"
            except Exception as e:
                logger.warning(f"获取X-Bogus失败: {e}, 尝试不带X-Bogus")
                full_url = f"{api_url}{params}"

            logger.info(f"请求用户合集列表: {full_url[:100]}...")
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"请求失败，状态码: {response.status}")
                        return None
                    text = await response.text()
                    if not text:
                        logger.error("响应内容为空")
                        return None
                    data = json.loads(text)
                    if data.get('status_code') == 0:
                        return data
                    else:
                        logger.error(f"API返回错误: {data.get('status_msg', '未知错误')}")
                        return None
        except Exception as e:
            logger.error(f"获取用户合集列表失败: {e}")
        return None

    async def download_mix(self, url: str) -> bool:
        """根据合集链接下载合集内所有作品"""
        try:
            mix_id = None
            for pattern in [r'/collection/(\d+)', r'/mix/detail/(\d+)']:
                m = re.search(pattern, url)
                if m:
                    mix_id = m.group(1)
                    break
            if not mix_id:
                logger.error(f"无法从合集链接提取ID: {url}")
                return False
            await self._download_mix_by_id(mix_id)
            return True
        except Exception as e:
            logger.error(f"下载合集失败: {e}")
            return False

    async def _download_mix_by_id(self, mix_id: str):
        """按合集ID下载全部作品"""
        cursor = 0
        downloaded = 0

        console.print(f"\n[green]Starting to download collection {mix_id} ...[/green]")

        while True:
            await self.rate_limiter.acquire()
            data = await self._fetch_mix_awemes(mix_id, cursor)
            if not data:
                break

            aweme_list = data.get('aweme_list') or []
            if not aweme_list:
                break

            for aweme in aweme_list:
                success = await self._download_media_files(aweme)
                if success:
                    downloaded += 1

            if not data.get('has_more'):
                break
            cursor = data.get('cursor', 0)

        console.print(f"[green]✅ Collection download complete, {downloaded} items downloaded in total[/green]")

    async def _fetch_mix_awemes(self, mix_id: str, cursor: int = 0) -> Optional[Dict]:
        """获取合集下作品列表"""
        try:
            params_list = [
                f'mix_id={mix_id}',
                f'cursor={cursor}',
                'count=35',
                'aid=6383',
                'device_platform=webapp',
                'channel=channel_pc_web',
                'pc_client_type=1',
                'version_code=170400',
                'version_name=17.4.0',
                'cookie_enabled=true',
                'screen_width=1920',
                'screen_height=1080',
                'browser_language=zh-CN',
                'browser_platform=MacIntel',
                'browser_name=Chrome',
                'browser_version=122.0.0.0',
                'browser_online=true'
            ]
            params = '&'.join(params_list)

            api_url = self.urls_helper.USER_MIX
            try:
                xbogus = self.utils.getXbogus(params)
                full_url = f"{api_url}{params}&X-Bogus={xbogus}"
            except Exception as e:
                logger.warning(f"获取X-Bogus失败: {e}, 尝试不带X-Bogus")
                full_url = f"{api_url}{params}"

            logger.info(f"请求合集作品列表: {full_url[:100]}...")
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"请求失败，状态码: {response.status}")
                        return None
                    text = await response.text()
                    if not text:
                        logger.error("响应内容为空")
                        return None
                    data = json.loads(text)
                    # USER_MIX 返回没有统一的 status_code，这里直接返回
                    return data
        except Exception as e:
            logger.error(f"获取合集作品失败: {e}")
        return None

    async def download_music(self, url: str) -> bool:
        """根据音乐页链接下载音乐下的所有作品（支持增量）"""
        try:
            # 提取 music_id
            music_id = None
            m = re.search(r'/music/(\d+)', url)
            if m:
                music_id = m.group(1)
            if not music_id:
                logger.error(f"无法从音乐链接提取ID: {url}")
                return False

            cursor = 0
            downloaded = 0
            limit_num = 0
            try:
                limit_num = int((self.config.get('number', {}) or {}).get('music', 0))
            except Exception:
                limit_num = 0

            console.print(f"\n[green]Starting to download works under music {music_id}...[/green]")

            while True:
                await self.rate_limiter.acquire()
                data = await self._fetch_music_awemes(music_id, cursor)
                if not data:
                    break
                aweme_list = data.get('aweme_list') or []
                if not aweme_list:
                    break

                for aweme in aweme_list:
                    if limit_num > 0 and downloaded >= limit_num:
                        console.print(f"[yellow]已达到音乐下载数量限制: {limit_num}[/yellow]")
                        return True
                    if self._should_skip_increment('music', aweme, music_id=music_id):
                        continue
                    success = await self._download_media_files(aweme)
                    if success:
                        downloaded += 1
                        self._record_increment('music', aweme, music_id=music_id)

                if not data.get('has_more'):
                    break
                cursor = data.get('cursor', 0)

            console.print(f"[green]✅ Music works download complete, {downloaded} items downloaded in total[/green]")
            return True
        except Exception as e:
            logger.error(f"下载音乐页失败: {e}")
            return False

    async def _fetch_music_awemes(self, music_id: str, cursor: int = 0) -> Optional[Dict]:
        """获取音乐下作品列表"""
        try:
            params_list = [
                f'music_id={music_id}',
                f'cursor={cursor}',
                'count=35',
                'aid=6383',
                'device_platform=webapp',
                'channel=channel_pc_web',
                'pc_client_type=1',
                'version_code=170400',
                'version_name=17.4.0',
                'cookie_enabled=true',
                'screen_width=1920',
                'screen_height=1080',
                'browser_language=zh-CN',
                'browser_platform=MacIntel',
                'browser_name=Chrome',
                'browser_version=122.0.0.0',
                'browser_online=true'
            ]
            params = '&'.join(params_list)

            api_url = self.urls_helper.MUSIC
            try:
                xbogus = self.utils.getXbogus(params)
                full_url = f"{api_url}{params}&X-Bogus={xbogus}"
            except Exception as e:
                logger.warning(f"获取X-Bogus失败: {e}, 尝试不带X-Bogus")
                full_url = f"{api_url}{params}"

            logger.info(f"请求音乐作品列表: {full_url[:100]}...")
            async with aiohttp.ClientSession() as session:
                async with session.get(full_url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"请求失败，状态码: {response.status}")
                        return None
                    text = await response.text()
                    if not text:
                        logger.error("响应内容为空")
                        return None
                    data = json.loads(text)
                    return data
        except Exception as e:
            logger.error(f"获取音乐作品失败: {e}")
        return None
    
    def _check_time_filter(self, aweme: Dict) -> bool:
        """检查时间过滤"""
        start_time = self.config.get('start_time')
        end_time = self.config.get('end_time')
        
        if not start_time and not end_time:
            return True
        
        raw_create_time = aweme.get('create_time')
        if not raw_create_time:
            return True
        
        create_date = None
        if isinstance(raw_create_time, (int, float)):
            try:
                create_date = datetime.fromtimestamp(raw_create_time)
            except Exception:
                create_date = None
        elif isinstance(raw_create_time, str):
            for fmt in ('%Y-%m-%d %H.%M.%S', '%Y-%m-%d_%H-%M-%S', '%Y-%m-%d %H:%M:%S'):
                try:
                    create_date = datetime.strptime(raw_create_time, fmt)
                    break
                except Exception:
                    pass
        
        if create_date is None:
            return True
        
        if start_time:
            start_date = datetime.strptime(start_time, '%Y-%m-%d')
            if create_date < start_date:
                return False
        
        if end_time:
            end_date = datetime.strptime(end_time, '%Y-%m-%d')
            if create_date > end_date:
                return False
        
        return True
    
    async def run(self):
        """Run downloader"""
        # Show startup info
        console.print(Panel.fit(
            "[bold cyan]Douyin Downloader v3.0 - Unified Enhanced Version[/bold cyan]\n"
            "[dim]Supports batch download of videos, galleries, user homepages, and collections[/dim]",
            border_style="cyan"
        ))
        
        # Initialize Cookie and headers
        await self._initialize_cookies_and_headers()
        
        # Get URL list
        urls = self.config.get('link', [])
        # Compatibility: single string
        if isinstance(urls, str):
            urls = [urls]
        
        # Clean URLs (handle share text fragments)
        urls = self._clean_urls(urls)
        
        if not urls:
            console.print("[red]No download links found![/red]")
            return
        
        # Analyze URL type
        console.print(f"\n[cyan]📊 Link Analysis[/cyan]")
        url_types = {}
        for url in urls:
            content_type = self.detect_content_type(url)
            url_types[url] = content_type
            console.print(f"  • {content_type.upper()}: {url[:50]}...")
        
        # Start download
        console.print(f"\n[green]⏳ Starting download of {len(urls)} links...[/green]\n")
        
        for i, url in enumerate(urls, 1):
            platform = self.detect_platform(url)
            content_type = url_types[url]
            console.print(f"[{i}/{len(urls)}] Processing [[bold cyan]{platform.upper()}[/bold cyan]] {content_type.upper()}: {url}")
            
            # Use appropriate API client
            client = self.tiktok if platform == Platform.TIKTOK else self.douyin
            
            # Single video/image
            if content_type == ContentType.VIDEO or content_type == ContentType.IMAGE:
                # Need to specialize download_single_video to use client
                await self.download_single_video(url, client=client)
            # User page
            elif content_type == ContentType.USER:
                await self.download_user_page(url, client=client)
                # If config contains like or mix, process them too
                modes = self.config.get('mode', ['post'])
                if 'like' in modes:
                    user_id = self.extract_id_from_url(url, ContentType.USER)
                    if user_id:
                        await self._download_user_likes(user_id)
                if 'mix' in modes:
                    user_id = self.extract_id_from_url(url, ContentType.USER)
                    if user_id:
                        await self._download_user_mixes(user_id)
            elif content_type == ContentType.MIX:
                await self.download_mix(url)
            elif content_type == ContentType.MUSIC:
                await self.download_music(url)
            else:
                console.print(f"[yellow]Unsupported content type: {content_type}[/yellow]")
            
            # Show progress
            console.print(f"Progress: {i}/{len(urls)} | Success: {self.stats.success} | Failed: {self.stats.failed}")
            console.print("-" * 60)
        
        # Show stats
        self._show_stats()
    
    def _show_stats(self):
        """Show download statistics"""
        console.print("\n" + "=" * 60)
        
        # Create stats table
        table = Table(title="📊 Download Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Item", style="cyan", width=12)
        table.add_column("Value", style="green")
        
        stats = self.stats.to_dict()
        table.add_row("Total Tasks", str(stats['total']))
        table.add_row("Success", str(stats['success']))
        table.add_row("Failed", str(stats['failed']))
        table.add_row("Skipped", str(stats['skipped']))
        table.add_row("Success Rate", stats['success_rate'])
        table.add_row("Time Elapsed", stats['elapsed_time'])
        
        console.print(table)
        console.print("\n[bold green]✅ Download task complete![/bold green]")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='抖音下载器 - 统一增强版',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yml',
        help='Configuration file path (default: config.yml, auto-compatible with config_simple.yml)'
    )
    
    parser.add_argument(
        '-u', '--url',
        nargs='+',
        help='Directly specify URLs to download'
    )
    parser.add_argument(
        '-p', '--path',
        default=None,
        help='Save path (overrides configuration file)'
    )
    parser.add_argument(
        '--auto-cookie',
        action='store_true',
        help='Automatically acquire Cookie (requires Playwright)'
    )
    parser.add_argument(
        '--cookie',
        help='Manually specify Cookie string, e.g., "msToken=xxx; ttwid=yyy"'
    )
    parser.add_argument(
        'positional_urls',
        nargs='*',
        help='Directly specify URLs to download (positional arguments supported)'
    )
    
    args = parser.parse_args()
    
    # 组合配置来源：优先命令行 (合并 -u 和 随后的位置参数)
    input_urls = (args.url or []) + args.positional_urls
    
    temp_config = {}
    if input_urls:
        temp_config['link'] = input_urls
    
    # 覆盖保存路径
    if args.path:
        temp_config['path'] = args.path
    
    # Cookie配置
    if args.auto_cookie:
        temp_config['auto_cookie'] = True
        temp_config['cookies'] = 'auto'
    if args.cookie:
        temp_config['cookies'] = args.cookie
        temp_config['auto_cookie'] = False
    
    # 如果存在临时配置，则生成一个临时文件供现有构造函数使用
    if temp_config:
        # 合并文件配置（如存在）
        file_config = {}
        if os.path.exists(args.config):
            try:
                with open(args.config, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
            except Exception:
                file_config = {}
        
        # 兼容简化键名
        if 'links' in file_config and 'link' not in file_config:
            file_config['link'] = file_config['links']
        if 'output_dir' in file_config and 'path' not in file_config:
            file_config['path'] = file_config['output_dir']
        if 'cookie' in file_config and 'cookies' not in file_config:
            file_config['cookies'] = file_config['cookie']
        
        merged = {**(file_config or {}), **temp_config}
        with open('temp_config.yml', 'w', encoding='utf-8') as f:
            yaml.dump(merged, f, allow_unicode=True)
        config_path = 'temp_config.yml'
    else:
        config_path = args.config
    
    # Run downloader
    try:
        downloader = UnifiedDownloader(config_path)
        asyncio.run(downloader.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ User interrupted download[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Program exception: {e}[/red]")
        logger.exception("Program exception")
    finally:
        # Clean up temporary config
        if input_urls and os.path.exists('temp_config.yml'):
            os.remove('temp_config.yml')


if __name__ == '__main__':
    main()