#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import requests
import json
import time
import copy
# from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Tuple, Optional
from requests.exceptions import RequestException
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console

from apiproxy.douyin import douyin_headers
from apiproxy.douyin.urls import Urls
from apiproxy.douyin.result import Result
from apiproxy.douyin.database import DataBase
from apiproxy.common import utils
import sys
import os
# Add project root to system path to ensure utils module can be imported correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.logger import logger

# Create global console instance
console = Console()

class Douyin(object):

    def __init__(self, database=False):
        self.urls = Urls()
        self.result = Result()
        self.database = database
        if database:
            self.db = DataBase()
        self.timeout = 10
        self.console = Console()
        self.headers = douyin_headers

    def set_cookies(self, cookie_str):
        """Set cookies to be used in requests"""
        if cookie_str:
            self.headers['Cookie'] = cookie_str
            # Also update global douyin_headers for compatibility with other modules
            from apiproxy.douyin import douyin_headers
            douyin_headers['Cookie'] = cookie_str

    # 从分享链接中提取网址
    def getShareLink(self, string):
        # 查找匹配正则表达式的字符串
        try:
            # More robust regex to find http/https URLs
            match = re.search(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)', string)
            if match:
                return match.group(1)
            else:
                return string  # Return original string if no URL found, maybe it is a raw URL
        except Exception:
            return string

    # 得到 作品id 或者 用户id
    # 传入 url 支持 https://www.iesdouyin.com 与 https://v.douyin.com
    def getKey(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """获取资源标识
        Args:
            url: 抖音分享链接或网页URL
        Returns:
            (资源类型, 资源ID)
        """
        key = None
        key_type = None

        try:
            r = requests.get(url=url, headers=douyin_headers)
        except Exception as e:
            print('[  Error  ]: Input link is incorrect!\r')
            return key_type, key

        # 抖音把图集更新为note
        # 作品 第一步解析出来的链接是share/video/{aweme_id}
        # https://www.iesdouyin.com/share/video/7037827546599263488/?region=CN&mid=6939809470193126152&u_code=j8a5173b&did=MS4wLjABAAAA1DICF9-A9M_CiGqAJZdsnig5TInVeIyPdc2QQdGrq58xUgD2w6BqCHovtqdIDs2i&iid=MS4wLjABAAAAomGWi4n2T0H9Ab9x96cUZoJXaILk4qXOJlJMZFiK6b_aJbuHkjN_f0mBzfy91DX1&with_sec_did=1&titleType=title&schema_type=37&from_ssr=1&utm_source=copy&utm_campaign=client_share&utm_medium=android&app=aweme
        # 用户 第一步解析出来的链接是share/user/{sec_uid}
        # https://www.iesdouyin.com/share/user/MS4wLjABAAAA06y3Ctu8QmuefqvUSU7vr0c_ZQnCqB0eaglgkelLTek?did=MS4wLjABAAAA1DICF9-A9M_CiGqAJZdsnig5TInVeIyPdc2QQdGrq58xUgD2w6BqCHovtqdIDs2i&iid=MS4wLjABAAAAomGWi4n2T0H9Ab9x96cUZoJXaILk4qXOJlJMZFiK6b_aJbuHkjN_f0mBzfy91DX1&with_sec_did=1&sec_uid=MS4wLjABAAAA06y3Ctu8QmuefqvUSU7vr0c_ZQnCqB0eaglgkelLTek&from_ssr=1&u_code=j8a5173b&timestamp=1674540164&ecom_share_track_params=%7B%22is_ec_shopping%22%3A%221%22%2C%22secuid%22%3A%22MS4wLjABAAAA-jD2lukp--I21BF8VQsmYUqJDbj3FmU-kGQTHl2y1Cw%22%2C%22enter_from%22%3A%22others_homepage%22%2C%22share_previous_page%22%3A%22others_homepage%22%7D&utm_source=copy&utm_campaign=client_share&utm_medium=android&app=aweme
        # 合集
        # https://www.douyin.com/collection/7093490319085307918
        urlstr = str(r.request.path_url)

        if "/user/" in urlstr:
            # 获取用户 sec_uid
            if '?' in r.request.path_url:
                for one in re.finditer(r'user\/([\d\D]*)([?])', str(r.request.path_url)):
                    key = one.group(1)
            else:
                for one in re.finditer(r'user\/([\d\D]*)', str(r.request.path_url)):
                    key = one.group(1)
            key_type = "user"
        elif "/video/" in urlstr:
            # 获取作品 aweme_id
            key = re.findall('video/(\d+)?', urlstr)[0]
            key_type = "aweme"
        elif "/note/" in urlstr:
            # 获取note aweme_id
            key = re.findall('note/(\d+)?', urlstr)[0]
            key_type = "aweme"
        elif "/mix/detail/" in urlstr:
            # 获取合集 id
            key = re.findall('/mix/detail/(\d+)?', urlstr)[0]
            key_type = "mix"
        elif "/collection/" in urlstr:
            # 获取合集 id
            key = re.findall('/collection/(\d+)?', urlstr)[0]
            key_type = "mix"
        elif "/music/" in urlstr:
            # 获取原声 id
            key = re.findall('music/(\d+)?', urlstr)[0]
            key_type = "music"
        elif "/webcast/reflow/" in urlstr:
            key1 = re.findall('reflow/(\d+)?', urlstr)[0]
            url = self.urls.LIVE2 + utils.getXbogus(
                f'live_id=1&room_id={key1}&app_id=1128')
            res = requests.get(url, headers=douyin_headers)
            resjson = json.loads(res.text)
            key = resjson['data']['room']['owner']['web_rid']
            key_type = "live"
        elif "live.douyin.com" in r.url:
            key = r.url.replace('https://live.douyin.com/', '')
            key_type = "live"

        if key is None or key_type is None:
            print('[  Error  ]: Input link is incorrect! Failed to get ID\r')
            return key_type, key

        return key_type, key

    # 暂时注释掉装饰器
    # @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def getAwemeInfo(self, aweme_id: str) -> dict:
        """获取作品信息（带重试机制）

        由于抖音单个视频接口经常返回空响应，这里实现一个备用方案：
        1. 首先尝试原有的单个视频接口
        2. 如果失败，尝试通过搜索接口获取视频信息
        3. 如果还是失败，返回空字典
        """
        retries = 3
        for attempt in range(retries):
            try:
                logger.info(f'[  Info  ]: Requesting work ID = {aweme_id}')
                if aweme_id is None:
                    return {}

                # 方法0: 确保有 ttwid
                if 'ttwid' not in douyin_headers.get('Cookie', ''):
                    self._ensure_ttwid()

                # 方法1: 尝试原有的单个视频接口
                result = self._try_detail_api(aweme_id)
                if result:
                    return result

                # Method 2: If single video API fails, try alternative method
                logger.warning("Single video API failed, trying alternative method...")
                result = self._try_alternative_method(aweme_id)
                if result:
                    return result

                # Method 3: SSR Fallback
                logger.warning("Alternative method failed, trying SSR fallback...")
                result = self._try_ssr_fallback(aweme_id)
                if result:
                    return result

                logger.warning(f"All methods failed, attempt {attempt+1}/{retries}")
                time.sleep(2 ** attempt)

            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{retries}): {str(e)}")
                time.sleep(2 ** attempt)

        logger.error(f"Unable to fetch info for video {aweme_id}")
        return {}

    def _try_detail_api(self, aweme_id: str) -> dict:
        """尝试使用原有的单个视频接口"""
        try:
            start = time.time()
            while True:
                try:
                    # 单作品接口返回 'aweme_detail'
                    # 主页作品接口返回 'aweme_list'->['aweme_detail']
                    # 更新API参数以适应最新接口要求
                    detail_params = f'aweme_id={aweme_id}&device_platform=webapp&aid=6383&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac&os_version=10.15.7&cpu_core_num=8&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50&update_version_code=170400'
                    jx_url = self.urls.POST_DETAIL + utils.getXbogus(detail_params)

                    response = requests.get(url=jx_url, headers=douyin_headers, timeout=10)

                    # Check if response is empty
                    if len(response.text) == 0:
                        logger.warning("Single video API returned empty response")
                        return {}

                    datadict = json.loads(response.text)

                    # Add debug info
                    logger.info(f"Single video API response status: {datadict.get('status_code') if datadict else 'None'}")
                    if datadict and datadict.get("status_code") != 0:
                        logger.warning(f"Single video API error: {datadict.get('status_msg', '未知错误')}")
                        return {}

                    if datadict is not None and datadict.get("status_code") == 0:
                        # Check for aweme_detail field
                        if "aweme_detail" not in datadict:
                            logger.error(f"Response missing aweme_detail field, available fields: {list(datadict.keys())}")
                            return {}
                        break
                except Exception as e:
                    end = time.time()
                    if end - start > self.timeout:
                        logger.warning(f"Repeat request to this interface for {self.timeout}s, still no data retrieved")
                        return {}

            # 清空self.awemeDict
            self.result.clearDict(self.result.awemeDict)

            # Default to video
            awemeType = 0
            try:
                # datadict['aweme_detail']["images"] not None means photo collection
                if datadict['aweme_detail']["images"] is not None:
                    awemeType = 1
            except Exception as e:
                logger.warning("images not found in interface")

            # Convert to our own format
            self.result.dataConvert(awemeType, self.result.awemeDict, datadict['aweme_detail'])

            return self.result.awemeDict

        except Exception as e:
            logger.warning(f"Single video API exception: {str(e)}")
            return {}

    def _ensure_ttwid(self):
        """确保 headers 中包含 ttwid"""
        try:
            url = 'https://www.douyin.com/'
            res = requests.get(url, headers=douyin_headers, timeout=10)
            ttwid = res.cookies.get('ttwid')
            if ttwid:
                logger.info(f"成功获取 ttwid: {ttwid}")
                current_cookie = douyin_headers.get('Cookie', '')
                if 'ttwid=' not in current_cookie:
                    douyin_headers['Cookie'] = (current_cookie + f'; ttwid={ttwid}').strip('; ')
        except Exception as e:
            logger.warning(f"获取 ttwid 失败: {e}")

    def _convert_aweme_data(self, item_detail: dict) -> dict:
        """统一数据转换方法"""
        self.result.clearDict(self.result.awemeDict)
        awemeType = 1 if item_detail.get('images') else 0
        self.result.dataConvert(awemeType, self.result.awemeDict, item_detail)
        return self.result.awemeDict

    def _try_ssr_fallback(self, aweme_id: str) -> dict:
        """从视频页面 HTML 中提取 SSR 数据作为最终兜底"""
        logger.info(f"正在尝试 SSR 兜底方案 (aweme_id: {aweme_id})...")
        
        # 尝试的 URL 列表：桌面端视频页、移动端分享页
        urls = [
            f"https://www.douyin.com/video/{aweme_id}",
            f"https://m.douyin.com/share/video/{aweme_id}"
        ]
        
        headers_list = [
            douyin_headers,
            {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
        ]

        for url, headers in zip(urls, headers_list):
            try:
                logger.info(f"正在请求 SSR 页面: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    logger.warning(f"SSR 请求页面失败 ({url}), 状态码: {response.status_code}")
                    continue
                
                html = response.text
                data = None
                
                # 寻找 RENDER_DATA (PC端常见)
                match = re.search(r'<script id="RENDER_DATA" type="application/json">(.*?)</script>', html)
                if match:
                    json_str = requests.utils.unquote(match.group(1))
                    data = json.loads(json_str)
                    logger.info("找到 RENDER_DATA")
                
                # 寻找 _ROUTER_DATA (移动端分享页常见)
                if not data:
                    match = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?});', html)
                    if not match:
                        # 尝试不带分号的版本
                        match = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?})<', html)
                    
                    if match:
                        data = json.loads(match.group(1))
                        logger.info("找到 _ROUTER_DATA")

                if data:
                    # 遍历查找 aweme_detail 或 item_list
                    def find_aweme(obj):
                        if isinstance(obj, dict):
                            # 情况1: 直接包含 aweme_detail
                            if 'aweme_detail' in obj and obj['aweme_detail']:
                                return obj['aweme_detail']
                            if 'awemeDetail' in obj and obj['awemeDetail']:
                                return obj['awemeDetail']
                            
                            # 情况2: 移动端常见的 item_list
                            if 'item_list' in obj and isinstance(obj['item_list'], list) and len(obj['item_list']) > 0:
                                return obj['item_list'][0]
                            
                            for v in obj.values():
                                res = find_aweme(v)
                                if res: return res
                        elif isinstance(obj, list):
                            for item in obj:
                                res = find_aweme(item)
                                if res: return res
                        return None
                    
                    aweme_detail = find_aweme(data)
                    if aweme_detail:
                        logger.info("SSR 兜底方案成功获取作品详情")
                        return self._convert_aweme_data(aweme_detail)
                
                logger.warning(f"页面 {url} 未找到有效 SSR 数据")
            except Exception as e:
                logger.warning(f"SSR 请求 {url} 失败: {e}")
        
        return {}

    def _try_alternative_method(self, aweme_id: str) -> dict:
        """备用方案：通过 iesdouyin API 获取视频信息"""
        logger.info("正在尝试备用方案 (iesdouyin API)...")
        try:
            url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={aweme_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.douyin.com/'
            }
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                item_list = data.get('item_list')
                if item_list:
                    item = item_list[0]
                    logger.info("备用方案成功获取信息")
                    return self._convert_aweme_data(item)
        except Exception as e:
            logger.warning(f"备用方案执行异常: {e}")
        
        return {}

    # 传入 url 支持 https://www.iesdouyin.com 与 https://v.douyin.com
    # mode : post | like 模式选择 like为用户点赞 post为用户发布
    def getUserInfo(self, sec_uid, mode="post", count=35, number=0, increase=False, start_time="", end_time=""):
        """Get user information
        Args:
            sec_uid: User ID
            mode: Mode (post: publish/like: like)
            count: Number per page
            number: Limit download quantity (0 means no limit)
            increase: Whether incremental update
            start_time: Start time, format: YYYY-MM-DD
            end_time: End time, format: YYYY-MM-DD
        """
        if sec_uid is None:
            return None

        # 处理时间范围
        if end_time == "now":
            end_time = time.strftime("%Y-%m-%d")
        
        if not start_time:
            start_time = "1970-01-01"
        if not end_time:
            end_time = "2099-12-31"

        self.console.print(f"[cyan]🕒 Time Range: {start_time} to {end_time}[/]")
        
        max_cursor = 0
        awemeList = []
        total_fetched = 0
        filtered_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=True
        ) as progress:
            fetch_task = progress.add_task(
                f"[cyan]📥 Fetching {mode} work list...", 
                total=None  # Total unknown, use infinite progress bar
            )
            
            while True:
                try:
                    # Construct request URL - add more required parameters
                    base_params = f'sec_user_id={sec_uid}&count={count}&max_cursor={max_cursor}&device_platform=webapp&aid=6383&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac&os_version=10.15.7&cpu_core_num=8&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50'

                    if mode == "post":
                        url = self.urls.USER_POST + utils.getXbogus(base_params)
                    elif mode == "like":
                        # 尝试备用like接口
                        try:
                            url = self.urls.USER_FAVORITE_A + utils.getXbogus(base_params)
                        except:
                            # 如果主接口失败，尝试备用接口
                            url = self.urls.USER_FAVORITE_B + utils.getXbogus(base_params)
                    else:
                        self.console.print("[red]❌ Mode selection error, only supports post, like[/red]")
                        return None

                    # 发送请求
                    res = requests.get(url=url, headers=douyin_headers, timeout=10)

                    # 检查HTTP状态码
                    if res.status_code != 200:
                        self.console.print(f"[red]❌ HTTP request failed: {res.status_code}[/]")
                        break

                    try:
                        datadict = json.loads(res.text)
                    except json.JSONDecodeError as e:
                        self.console.print(f"[red]❌ JSON parsing failed: {str(e)}[/]")
                        self.console.print(f"[yellow]🔍 Response content: {res.text[:500]}...[/]")
                        self.console.print(f"[yellow]🔍 Request URL: {url}[/]")
                        self.console.print(f"[yellow]🔍 Mode: {mode}[/]")

                        # Check if it's empty response or permission issue
                        if not res.text.strip():
                            self.console.print(f"[yellow]💡 Tip: {mode} mode might need special permissions or the user's {mode} list is not public[/]")
                        elif "登录" in res.text or "login" in res.text.lower():
                            self.console.print(f"[yellow]💡 Tip: {mode} mode requires login status[/]")
                        elif "权限" in res.text or "permission" in res.text.lower():
                            self.console.print(f"[yellow]💡 Tip: {mode} mode insufficient permissions[/]")
                        break
                    
                    # Handle return data
                    if not datadict or datadict.get("status_code") != 0:
                        self.console.print(f"[red]❌ API request failed: {datadict.get('status_msg', 'Unknown Error')}[/]")
                        # Print detailed response info for debugging
                        self.console.print(f"[yellow]🔍 Response status code: {datadict.get('status_code') if datadict else 'None'}[/]")
                        self.console.print(f"[yellow]🔍 Response content: {str(datadict)[:200]}...[/]")
                        break

                    # Check if aweme_list field exists
                    if "aweme_list" not in datadict:
                        self.console.print(f"[red]❌ Response missing aweme_list field[/red]")
                        self.console.print(f"[yellow]🔍 Available fields: {list(datadict.keys())}[/yellow]")
                        break

                    current_count = len(datadict["aweme_list"])
                    total_fetched += current_count
                    
                    # Update progress display
                    progress.update(
                        fetch_task, 
                        description=f"[cyan]📥 Fetched: {total_fetched} works"
                    )

                    # 在处理作品时添加时间过滤
                    for aweme in datadict["aweme_list"]:
                        create_time = time.strftime(
                            "%Y-%m-%d", 
                            time.localtime(int(aweme.get("create_time", 0)))
                        )
                        
                        # 时间过滤
                        if not (start_time <= create_time <= end_time):
                            filtered_count += 1
                            continue

                        # 数量限制检查
                        if number > 0 and len(awemeList) >= number:
                            self.console.print(f"[green]✅ Reached limit: {number}[/]")
                            return awemeList
                            
                        # Incremental update check
                        if self.database:
                            if mode == "post":
                                if self.db.get_user_post(sec_uid=sec_uid, aweme_id=aweme['aweme_id']):
                                    if increase and aweme['is_top'] == 0:
                                        self.console.print("[green]✅ Incremental update complete[/]")
                                        return awemeList
                                else:
                                    self.db.insert_user_post(sec_uid=sec_uid, aweme_id=aweme['aweme_id'], data=aweme)
                            elif mode == "like":
                                if self.db.get_user_like(sec_uid=sec_uid, aweme_id=aweme['aweme_id']):
                                    if increase and aweme['is_top'] == 0:
                                        self.console.print("[green]✅ Incremental update complete[/]")
                                        return awemeList
                            else:
                                self.console.print("[red]❌ Mode selection error, only supports post, like[/]")
                                return None

                        # 转换数据格式
                        aweme_data = self._convert_aweme_data(aweme)
                        if aweme_data:
                            awemeList.append(aweme_data)

                    # 检查是否还有更多数据
                    if not datadict["has_more"]:
                        self.console.print(f"[green]✅ Fetched all works: {total_fetched}[/]")
                        break
                    
                    # Update cursor
                    max_cursor = datadict["max_cursor"]
                    
                except Exception as e:
                    self.console.print(f"[red]❌ Error fetching work list: {str(e)}[/]")
                    break

        return awemeList

    def _convert_aweme_data(self, aweme):
        """Convert work data format"""
        try:
            self.result.clearDict(self.result.awemeDict)
            aweme_type = 1 if aweme.get("images") else 0
            self.result.dataConvert(aweme_type, self.result.awemeDict, aweme)
            return copy.deepcopy(self.result.awemeDict)
        except Exception as e:
            logger.error(f"Data conversion error: {str(e)}")
            return None

    def getLiveInfo(self, web_rid: str):
        print('[  Info  ]: Requesting live room ID = %s\r\n' % web_rid)

        start = time.time()  # Start time
        while True:
            # Interface unstable, sometimes server doesn't return data, need to re-fetch
            try:
                live_params = f'aid=6383&device_platform=web&web_rid={web_rid}&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac&os_version=10.15.7&cpu_core_num=8&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50'
                live_api = self.urls.LIVE + utils.getXbogus(live_params)

                response = requests.get(live_api, headers=douyin_headers)
                live_json = json.loads(response.text)
                if live_json != {} and live_json['status_code'] == 0:
                    break
            except Exception as e:
                end = time.time()  # End time
                if end - start > self.timeout:
                    print("[  Info  ]: Repeat request to this interface for " + str(self.timeout) + "s, still no data retrieved")
                    return {}

        # Clear dict
        self.result.clearDict(self.result.liveDict)

        # Type
        self.result.liveDict["awemeType"] = 2
        # Live status
        self.result.liveDict["status"] = live_json['data']['data'][0]['status']

        if self.result.liveDict["status"] == 4:
            print('[   📺   ]: Current live stream has ended, exiting')
            return self.result.liveDict

        # 直播标题
        self.result.liveDict["title"] = live_json['data']['data'][0]['title']

        # 直播cover
        self.result.liveDict["cover"] = live_json['data']['data'][0]['cover']['url_list'][0]

        # 头像
        self.result.liveDict["avatar"] = live_json['data']['data'][0]['owner']['avatar_thumb']['url_list'][0].replace(
            "100x100", "1080x1080")

        # 观看人数
        self.result.liveDict["user_count"] = live_json['data']['data'][0]['user_count_str']

        # 昵称
        self.result.liveDict["nickname"] = live_json['data']['data'][0]['owner']['nickname']

        # sec_uid
        self.result.liveDict["sec_uid"] = live_json['data']['data'][0]['owner']['sec_uid']

        # 直播间观看状态
        self.result.liveDict["display_long"] = live_json['data']['data'][0]['room_view_stats']['display_long']

        # 推流
        self.result.liveDict["flv_pull_url"] = live_json['data']['data'][0]['stream_url']['flv_pull_url']

        try:
            # Partition
            self.result.liveDict["partition"] = live_json['data']['partition_road_map']['partition']['title']
            self.result.liveDict["sub_partition"] = \
                live_json['data']['partition_road_map']['sub_partition']['partition']['title']
        except Exception as e:
            self.result.liveDict["partition"] = 'None'
            self.result.liveDict["sub_partition"] = 'None'

        info = '[   💻   ]: Live Room: %s  Current: %s  Host: %s Partition: %s-%s\r' % (
            self.result.liveDict["title"], self.result.liveDict["display_long"], self.result.liveDict["nickname"],
            self.result.liveDict["partition"], self.result.liveDict["sub_partition"])
        print(info)

        flv = []
        print('[   🎦   ]: Live Stream Clarity')
        for i, f in enumerate(self.result.liveDict["flv_pull_url"].keys()):
            print('[   %s   ]: %s' % (i, f))
            flv.append(f)

        rate = int(input('[   🎬   ] Enter number to select stream clarity: '))

        self.result.liveDict["flv_pull_url0"] = self.result.liveDict["flv_pull_url"][flv[rate]]

        # Display clarity list
        print('[   %s   ]:%s' % (flv[rate], self.result.liveDict["flv_pull_url"][flv[rate]]))
        print('[   📺   ]: Copy link to download using a download tool')
        return self.result.liveDict

    def getMixInfo(self, mix_id, count=35, number=0, increase=False, sec_uid="", start_time="", end_time=""):
        """Get collection information"""
        if mix_id is None:
            return None

        # 处理时间范围
        if end_time == "now":
            end_time = time.strftime("%Y-%m-%d")
        
        if not start_time:
            start_time = "1970-01-01"
        if not end_time:
            end_time = "2099-12-31"

        self.console.print(f"[cyan]🕒 Time Range: {start_time} to {end_time}[/]")

        cursor = 0
        awemeList = []
        total_fetched = 0
        filtered_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=True
        ) as progress:
            fetch_task = progress.add_task(
                "[cyan]📥 Fetching collection works...",
                total=None
            )

            while True:  # Outer loop
                try:
                    mix_params = f'mix_id={mix_id}&cursor={cursor}&count={count}&device_platform=webapp&aid=6383&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac&os_version=10.15.7&cpu_core_num=8&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50'
                    url = self.urls.USER_MIX + utils.getXbogus(mix_params)

                    res = requests.get(url=url, headers=douyin_headers, timeout=10)

                    # 检查HTTP状态码
                    if res.status_code != 200:
                        self.console.print(f"[red]❌ Collection HTTP request failed: {res.status_code}[/]")
                        break

                    try:
                        datadict = json.loads(res.text)
                    except json.JSONDecodeError as e:
                        self.console.print(f"[red]❌ Collection JSON parsing failed: {str(e)}[/]")
                        self.console.print(f"[yellow]🔍 Response content: {res.text[:500]}...[/]")
                        break

                    if not datadict:
                        self.console.print("[red]❌ Failed to get collection data[/]")
                        break

                    if datadict.get("status_code") != 0:
                        self.console.print(f"[red]❌ Collection API request failed: {datadict.get('status_msg', 'Unknown Error')}[/]")
                        break

                    if "aweme_list" not in datadict:
                        self.console.print(f"[red]❌ Collection response missing aweme_list field[/]")
                        self.console.print(f"[yellow]🔍 Available fields: {list(datadict.keys())}[/]")
                        break

                    for aweme in datadict["aweme_list"]:
                        create_time = time.strftime(
                            "%Y-%m-%d",
                            time.localtime(int(aweme.get("create_time", 0)))
                        )

                        # 时间过滤
                        if not (start_time <= create_time <= end_time):
                            filtered_count += 1
                            continue

                        # 数量限制检查
                        if number > 0 and len(awemeList) >= number:
                            return awemeList  # 使用return替代break

                        # 增量更新检查
                        if self.database:
                            if self.db.get_mix(sec_uid=sec_uid, mix_id=mix_id, aweme_id=aweme['aweme_id']):
                                if increase and aweme['is_top'] == 0:
                                    return awemeList  # 使用return替代break
                            else:
                                self.db.insert_mix(sec_uid=sec_uid, mix_id=mix_id, aweme_id=aweme['aweme_id'], data=aweme)

                        # 转换数据
                        aweme_data = self._convert_aweme_data(aweme)
                        if aweme_data:
                            awemeList.append(aweme_data)

                    # Check if there's more data
                    if not datadict.get("has_more"):
                        self.console.print(f"[green]✅ Fetched all works[/green]")
                        break

                    # Update cursor
                    cursor = datadict.get("cursor", 0)
                    total_fetched += len(datadict["aweme_list"])
                    progress.update(fetch_task, description=f"[cyan]📥 Fetched: {total_fetched} works")

                except Exception as e:
                    self.console.print(f"[red]❌ Error fetching work list: {str(e)}[/red]")
                    # Add more detailed error info
                    if 'datadict' in locals():
                        self.console.print(f"[yellow]🔍 Last response: {str(datadict)[:300]}...[/yellow]")
                    break

        if filtered_count > 0:
            self.console.print(f"[yellow]⚠️  Filtered {filtered_count} works not in time range[/yellow]")

        return awemeList

    def getUserAllMixInfo(self, sec_uid, count=35, number=0):
        print('[  Info  ]: Requesting user ID = %s\r\n' % sec_uid)
        if sec_uid is None:
            return None
        if number <= 0:
            numflag = False
        else:
            numflag = True

        cursor = 0
        mixIdNameDict = {}

        print("[  Info  ]: Fetching all collection ID data under homepage, please wait...\r")
        print("[  Info  ]: Multiple requests will be made, waiting time may be long...\r\n")
        times = 0
        while True:
            times = times + 1
            print("[  Info  ]: Requesting [Collection List] attempt " + str(times) + "...\r")

            start = time.time()  # Start time
            while True:
                # Interface unstable, sometimes server doesn't return data, need to re-fetch
                try:
                    mix_list_params = f'sec_user_id={sec_uid}&count={count}&cursor={cursor}&device_platform=webapp&aid=6383&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac&os_version=10.15.7&cpu_core_num=8&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50'
                    url = self.urls.USER_MIX_LIST + utils.getXbogus(mix_list_params)

                    res = requests.get(url=url, headers=douyin_headers, timeout=10)

                    # Check HTTP status code
                    if res.status_code != 200:
                        self.console.print(f"[red]❌ Collection list HTTP request failed: {res.status_code}[/red]")
                        break

                    try:
                        # Try direct parsing, if failed check for compressed format
                        try:
                            datadict = json.loads(res.text)
                        except json.JSONDecodeError:
                            # Maybe compressed response, try manual decompression
                            content_encoding = res.headers.get('content-encoding', '').lower()
                            if content_encoding == 'gzip':
                                import gzip
                                content = gzip.decompress(res.content).decode('utf-8')
                                datadict = json.loads(content)
                            elif content_encoding == 'br':
                                try:
                                    import brotli
                                    content = brotli.decompress(res.content).decode('utf-8')
                                    datadict = json.loads(content)
                                except ImportError:
                                    self.console.print("[red]❌ Need to install brotli library: pip install brotli[/red]")
                                    raise
                            else:
                                raise  # Reraise original exception
                    except json.JSONDecodeError as e:
                        self.console.print(f"[red]❌ Collection list JSON parsing failed: {str(e)}[/red]")
                        self.console.print(f"[yellow]🔍 Response content: {res.text[:500]}...[/yellow]")
                        self.console.print(f"[yellow]🔍 Response headers: {dict(res.headers)}[/yellow]")
                        break

                    # Check response structure
                    if not datadict:
                        self.console.print("[red]❌ Failed to get collection list data[/]")
                        break

                    if datadict.get("status_code") != 0:
                        self.console.print(f"[red]❌ Collection list API request failed: {datadict.get('status_msg', 'Unknown Error')}[/]")
                        break

                    if "mix_infos" not in datadict:
                        self.console.print(f"[red]❌ Response missing mix_infos field[/]")
                        self.console.print(f"[yellow]🔍 Available fields: {list(datadict.keys())}[/]")
                        break

                    print('[  Info  ]: This request returned ' + str(len(datadict["mix_infos"])) + ' data records\r')

                    if datadict is not None and datadict["status_code"] == 0:
                        break
                except Exception as e:
                    end = time.time()  # End time
                    if end - start > self.timeout:
                        print("[  Info  ]: Repeat request to this interface for " + str(self.timeout) + "s, still no data retrieved")
                        return mixIdNameDict

            # Check if datadict was successfully acquired
            if 'datadict' not in locals() or not datadict:
                print("[  Info  ]: Failed to obtain valid collection list data")
                return mixIdNameDict


            for mix in datadict["mix_infos"]:
                mixIdNameDict[mix["mix_id"]] = mix["mix_name"]
                if numflag:
                    number -= 1
                    if number == 0:
                        break
            if numflag and number == 0:
                print("\r\n[  Info  ]: Collection list with specified quantity fetched...\r\n")
                break

            # Update max_cursor
            cursor = datadict["cursor"]

            # Exit conditions
            if datadict["has_more"] == 0 or datadict["has_more"] == False:
                print("[  Info  ]: All collection ID data under [Collection List] fetched...\r\n")
                break
            else:
                print("\r\n[  Info  ]: [Collection List] attempt " + str(times) + " successful...\r\n")

        return mixIdNameDict

    def getMusicInfo(self, music_id: str, count=35, number=0, increase=False):
        print('[  Info  ]: Requesting music collection ID = %s\r\n' % music_id)
        if music_id is None:
            return None
        if number <= 0:
            numflag = False
        else:
            numflag = True

        cursor = 0
        awemeList = []
        increaseflag = False
        numberis0 = False

        print("[  Info  ]: Fetching all work data under music collection, please wait...\r")
        print("[  Info  ]: Multiple requests will be made, waiting time may be long...\r\n")
        times = 0
        while True:
            times = times + 1
            print("[  Info  ]: Requesting [Music Collection] attempt " + str(times) + "...\r")

            start = time.time()  # Start time
            while True:
                # Interface unstable, sometimes server doesn't return data, need to re-fetch
                try:
                    music_params = f'music_id={music_id}&cursor={cursor}&count={count}&device_platform=webapp&aid=6383&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac&os_version=10.15.7&cpu_core_num=8&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50'
                    url = self.urls.MUSIC + utils.getXbogus(music_params)

                    res = requests.get(url=url, headers=douyin_headers, timeout=10)

                    # Check HTTP status code
                    if res.status_code != 200:
                        self.console.print(f"[red]❌ Music HTTP request failed: {res.status_code}[/red]")
                        break

                    try:
                        datadict = json.loads(res.text)
                    except json.JSONDecodeError as e:
                        self.console.print(f"[red]❌ Music JSON parsing failed: {str(e)}[/red]")
                        self.console.print(f"[yellow]🔍 Response content: {res.text[:500]}...[/yellow]")
                        break

                    if not datadict:
                        self.console.print("[red]❌ Failed to get music data[/red]")
                        break

                    if datadict.get("status_code") != 0:
                        self.console.print(f"[red]❌ Music API request failed: {datadict.get('status_msg', 'Unknown Error')}[/]")
                        break

                    if "aweme_list" not in datadict:
                        self.console.print(f"[red]❌ Music response missing aweme_list field[/]")
                        self.console.print(f"[yellow]🔍 Available fields: {list(datadict.keys())}[/]")
                        break

                    print('[  Info  ]: This request returned ' + str(len(datadict["aweme_list"])) + ' data records\r')

                    if datadict is not None and datadict["status_code"] == 0:
                        break
                except Exception as e:
                    end = time.time()  # End time
                    if end - start > self.timeout:
                        print("[  Info  ]: Repeat request to this interface for " + str(self.timeout) + "s, still no data retrieved")
                        return awemeList


            for aweme in datadict["aweme_list"]:
                if self.database:
                    # 退出条件
                    if increase is False and numflag and numberis0:
                        break
                    if increase and numflag and numberis0 and increaseflag:
                        break
                    # 增量更新, 找到非置顶的最新的作品发布时间
                    if self.db.get_music(music_id=music_id, aweme_id=aweme['aweme_id']) is not None:
                        if increase and aweme['is_top'] == 0:
                            increaseflag = True
                    else:
                        self.db.insert_music(music_id=music_id, aweme_id=aweme['aweme_id'], data=aweme)

                    # 退出条件
                    if increase and numflag is False and increaseflag:
                        break
                    if increase and numflag and numberis0 and increaseflag:
                        break
                else:
                    if numflag and numberis0:
                        break

                if numflag:
                    number -= 1
                    if number == 0:
                        numberis0 = True

                # 清空self.awemeDict
                self.result.clearDict(self.result.awemeDict)

                # 默认为视频
                awemeType = 0
                try:
                    if aweme["images"] is not None:
                        awemeType = 1
                except Exception as e:
                    print("[  Warning  ]: images not found in interface\r")

                # 转换成我们自己的格式
                self.result.dataConvert(awemeType, self.result.awemeDict, aweme)

                if self.result.awemeDict is not None and self.result.awemeDict != {}:
                    awemeList.append(copy.deepcopy(self.result.awemeDict))

            if self.database:
                if increase and numflag is False and increaseflag:
                    print("\r\n[  Info  ]: [Music Collection] incremental update data fetched...\r\n")
                    break
                elif increase is False and numflag and numberis0:
                    print("\r\n[  Info  ]: [Music Collection] specified quantity of works fetched...\r\n")
                    break
                elif increase and numflag and numberis0 and increaseflag:
                    print("\r\n[  Info  ]: [Music Collection] specified quantity and incremental update data fetched...\r\n")
                    break
            else:
                if numflag and numberis0:
                    print("\r\n[  Info  ]: [Music Collection] specified quantity of works fetched...\r\n")
                    break

            # Update cursor
            cursor = datadict["cursor"]

            # Exit conditions
            if datadict["has_more"] == 0 or datadict["has_more"] == False:
                print("\r\n[  Info  ]: [Music Collection] all work data fetched...\r\n")
                break
            else:
                print("\r\n[  Info  ]: [Music Collection] attempt " + str(times) + " successful...\r\n")

        return awemeList

    def getUserDetailInfo(self, sec_uid):
        if sec_uid is None:
            return None

        datadict = {}
        start = time.time()  # Start time
        while True:
            # Interface unstable, sometimes server doesn't return data, need to re-fetch
            try:
                user_detail_params = f'sec_user_id={sec_uid}&device_platform=webapp&aid=6383&channel=channel_pc_web&pc_client_type=1&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1920&screen_height=1080&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Chrome&browser_version=122.0.0.0&browser_online=true&engine_name=Blink&engine_version=122.0.0.0&os_name=Mac&os_version=10.15.7&cpu_core_num=8&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50'
                url = self.urls.USER_DETAIL + utils.getXbogus(user_detail_params)

                res = requests.get(url=url, headers=douyin_headers)
                datadict = json.loads(res.text)

                if datadict is not None and datadict["status_code"] == 0:
                    return datadict
            except Exception as e:
                end = time.time()  # 结束时间
                if end - start > self.timeout:
                    print("[  Info  ]: Repeat request to this interface for " + str(self.timeout) + "s, still no data retrieved")
                    return datadict


if __name__ == "__main__":
    pass
