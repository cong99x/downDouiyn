#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import List, Optional
from pathlib import Path
# import asyncio  # 暂时注释掉
# import aiohttp  # 暂时注释掉
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from apiproxy.douyin import douyin_headers
from apiproxy.common import utils

logger = logging.getLogger("douyin_downloader")
console = Console()

class Download(object):
    def __init__(self, thread=5, music=True, cover=True, avatar=True, resjson=True, folderstyle=True, custom_headers=None, progress_callback=None):
        self.thread = thread
        self.music = music
        self.cover = cover
        self.avatar = avatar
        self.resjson = resjson
        self.folderstyle = folderstyle
        self.custom_headers = custom_headers  # Support for TikTok headers
        self.progress_callback = progress_callback
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            transient=True  # 添加这个参数，进度条完成后自动消失
        )
        self.retry_times = 3
        self.chunk_size = 8192
        self.timeout = 30

    def _download_media(self, url: str, path: Path, desc: str) -> bool:
        """通用下载方法，处理所有类型的媒体下载"""
        if path.exists():
            self.console.print(f"[cyan]⏭️  跳过已存在: {desc}[/]")
            return True
            
        # 使用新的断点续传下载方法替换原有的下载逻辑
        return self.download_with_resume(url, path, desc)

    def _get_first_url(self, url_list: list) -> str:
        """安全地获取URL列表中的第一个URL"""
        if isinstance(url_list, list) and len(url_list) > 0:
            return url_list[0]
        return None

    def _download_media_files(self, aweme: dict, path: Path, name: str, desc: str) -> None:
        """下载所有媒体文件"""
        try:
            # 下载视频或图集
            if aweme["awemeType"] == 0:  # 视频
                video_path = path / f"{name}_video.mp4"
                
                # Lấy URL video
                url_list = aweme.get("video", {}).get("play_addr", {}).get("url_list", [])
                video_url = self._get_first_url(url_list)
                
                if video_url:
                    # Kiểm tra xem URL có phải là playwm (có watermark) không
                    if 'playwm' in video_url:
                        logger.info(f"🔄 Phát hiện URL có watermark, đang chuyển đổi...")
                        # Chuyển đổi sang URL không watermark
                        video_url = self._convert_to_no_watermark_url(video_url, aweme)
                        logger.info(f"✅ Đã chuyển đổi sang URL không watermark")
                    
                    if not self._download_media(video_url, video_path, f"[视频]{desc}"):
                        raise Exception("视频下载失败")
                else:
                    logger.warning(f"视频URL为空: {desc}")

            elif aweme["awemeType"] == 1:  # 图集
                for i, image in enumerate(aweme.get("images", [])):
                    url_list = image.get("url_list", [])
                    if url := self._get_first_url(url_list):
                        image_path = path / f"{name}_image_{i}.jpeg"
                        if not self._download_media(url, image_path, f"[图集{i+1}]{desc}"):
                            raise Exception(f"图片{i+1}下载失败")
                    else:
                        logger.warning(f"图片{i+1} URL为空: {desc}")

            # 下载音乐
            if self.music:
                url_list = aweme.get("music", {}).get("play_url", {}).get("url_list", [])
                if url := self._get_first_url(url_list):
                    music_name = utils.replaceStr(aweme["music"]["title"])
                    music_path = path / f"{name}_music_{music_name}.mp3"
                    if not self._download_media(url, music_path, f"[音乐]{desc}"):
                        self.console.print(f"[yellow]⚠️  音乐下载失败: {desc}[/]")

            # 下载封面
            if self.cover and aweme["awemeType"] == 0:
                url_list = aweme.get("video", {}).get("cover", {}).get("url_list", [])
                if url := self._get_first_url(url_list):
                    cover_path = path / f"{name}_cover.jpeg"
                    if not self._download_media(url, cover_path, f"[封面]{desc}"):
                        self.console.print(f"[yellow]⚠️  封面下载失败: {desc}[/]")

            # 下载头像
            if self.avatar:
                url_list = aweme.get("author", {}).get("avatar", {}).get("url_list", [])
                if url := self._get_first_url(url_list):
                    avatar_path = path / f"{name}_avatar.jpeg"
                    if not self._download_media(url, avatar_path, f"[头像]{desc}"):
                        self.console.print(f"[yellow]⚠️  头像下载失败: {desc}[/]")

        except Exception as e:
            raise Exception(f"下载失败: {str(e)}")
    
    def _convert_to_no_watermark_url(self, watermark_url: str, aweme: dict) -> str:
        """
        Chuyển đổi URL có watermark thành URL không watermark
        
        Args:
            watermark_url: URL có watermark (playwm)
            aweme: Dữ liệu video để lấy thông tin bổ sung
            
        Returns:
            URL không watermark
        """
        try:
            # Lấy video_id từ URL
            import re
            from urllib.parse import urlparse, parse_qs
            
            # Parse URL
            parsed = urlparse(watermark_url)
            params = parse_qs(parsed.query)
            
            video_id = params.get('video_id', [None])[0]
            ratio = params.get('ratio', ['720p'])[0]
            
            if not video_id:
                # Thử lấy từ aweme data
                video_id = aweme.get("video", {}).get("play_addr", {}).get("uri", "")
            
            if video_id:
                # Tạo URL không watermark
                # Phương pháp 1: Thay playwm bằng play
                no_wm_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={video_id}&ratio={ratio}&line=0"
                
                logger.info(f"🔄 Chuyển đổi URL:")
                logger.info(f"   Từ: {watermark_url[:80]}...")
                logger.info(f"   Sang: {no_wm_url[:80]}...")
                
                return no_wm_url
            else:
                logger.warning("⚠️ Không tìm thấy video_id, sử dụng URL gốc")
                return watermark_url
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi chuyển đổi URL: {str(e)}")
            return watermark_url


    def awemeDownload(self, awemeDict: dict, savePath: Path) -> None:
        """下载单个作品的所有内容"""
        if not awemeDict:
            logger.warning("无效的作品数据")
            return
            
        try:
            # 创建保存目录
            save_path = Path(savePath)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 构建文件名
            file_name = f"{awemeDict['create_time']}_{utils.replaceStr(awemeDict['desc'])}"
            aweme_path = save_path / file_name if self.folderstyle else save_path
            aweme_path.mkdir(exist_ok=True)
            
            # 保存JSON数据
            if self.resjson:
                self._save_json(aweme_path / f"{file_name}_result.json", awemeDict)
                
            # 下载媒体文件
            desc = file_name[:30]
            self._download_media_files(awemeDict, aweme_path, file_name, desc)
                
        except Exception as e:
            logger.error(f"处理作品时出错: {str(e)}")

    def _save_json(self, path: Path, data: dict) -> None:
        """保存JSON数据"""
        try:
            with open(path, "w", encoding='utf-8') as f:
                json.dump(data, ensure_ascii=False, indent=2, fp=f)
        except Exception as e:
            logger.error(f"保存JSON失败: {path}, 错误: {str(e)}")

    def userDownload(self, awemeList: List[dict], savePath: Path):
        if not awemeList:
            self.console.print("[yellow]⚠️  没有找到可下载的内容[/]")
            return

        save_path = Path(savePath)
        save_path.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        total_count = len(awemeList)
        success_count = 0
        
        # 显示下载信息面板
        self.console.print(Panel(
            Text.assemble(
                ("下载配置\n", "bold cyan"),
                (f"总数: {total_count} 个作品\n", "cyan"),
                (f"线程: {self.thread}\n", "cyan"),
                (f"保存路径: {save_path}\n", "cyan"),
            ),
            title="抖音下载器",
            border_style="cyan"
        ))

        with self.progress:
            download_task = self.progress.add_task(
                "[cyan]📥 批量下载进度", 
                total=total_count
            )
            
            for aweme in awemeList:
                try:
                    self.awemeDownload(awemeDict=aweme, savePath=save_path)
                    success_count += 1
                    self.progress.update(download_task, advance=1)
                except Exception as e:
                    self.console.print(f"[red]❌ 下载失败: {str(e)}[/]")

        # 显示下载完成统计
        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.console.print(Panel(
            Text.assemble(
                ("下载完成\n", "bold green"),
                (f"成功: {success_count}/{total_count}\n", "green"),
                (f"用时: {minutes}分{seconds}秒\n", "green"),
                (f"保存位置: {save_path}\n", "green"),
            ),
            title="下载统计",
            border_style="green"
        ))

    def download_with_resume(self, url: str, filepath: Path, desc: str) -> bool:
        """支持断点续传的下载方法"""
        file_size = filepath.stat().st_size if filepath.exists() else 0
        headers = {'Range': f'bytes={file_size}-'} if file_size > 0 else {}

        for attempt in range(self.retry_times):
            try:
                # Use custom headers if provided (for TikTok), otherwise use douyin_headers
                base_headers = self.custom_headers if self.custom_headers else douyin_headers
                response = requests.get(url, headers={**base_headers, **headers},
                                     stream=True, timeout=self.timeout)

                if response.status_code not in (200, 206):
                    raise Exception(f"HTTP {response.status_code}")

                total_size = int(response.headers.get('content-length', 0)) + file_size
                mode = 'ab' if file_size > 0 else 'wb'

                with self.progress:
                    task = self.progress.add_task(f"[cyan]⬇️  {desc}", total=total_size)
                    self.progress.update(task, completed=file_size)  # 更新断点续传的进度

                    with open(filepath, mode) as f:
                        try:
                            downloaded = file_size
                            for chunk in response.iter_content(chunk_size=self.chunk_size):
                                if chunk:
                                    size = f.write(chunk)
                                    downloaded += size
                                    self.progress.update(task, advance=size)
                                    if self.progress_callback:
                                        percentage = (downloaded / total_size) * 100
                                        self.progress_callback(percentage)
                        except (requests.exceptions.ConnectionError,
                               requests.exceptions.ChunkedEncodingError,
                               Exception) as chunk_error:
                            # 网络中断，记录当前文件大小，下次从这里继续
                            current_size = filepath.stat().st_size if filepath.exists() else 0
                            logger.warning(f"下载中断，已下载 {current_size} 字节: {str(chunk_error)}")
                            raise chunk_error

                return True

            except Exception as e:
                # 计算重试等待时间（指数退避）
                wait_time = min(2 ** attempt, 10)  # 最多等待10秒
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.retry_times}): {str(e)}")

                if attempt == self.retry_times - 1:
                    self.console.print(f"[red]❌ 下载失败: {desc}\n   {str(e)}[/]")
                    return False
                else:
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    # 重新计算文件大小，准备断点续传
                    file_size = filepath.stat().st_size if filepath.exists() else 0
                    headers = {'Range': f'bytes={file_size}-'} if file_size > 0 else {}

        return False


class DownloadManager:
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def download_with_resume(self, url, filepath, callback=None):
        # 检查是否存在部分下载的文件
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        
        headers = {'Range': f'bytes={file_size}-'}
        
        response = requests.get(url, headers=headers, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        mode = 'ab' if file_size > 0 else 'wb'
        
        with open(filepath, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    if callback:
                        callback(len(chunk))


if __name__ == "__main__":
    pass
