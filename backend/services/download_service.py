#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download Service - Business logic layer for video download operations.
Single Responsibility: Handle all download-related business logic.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict

# Add parent directory to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apiproxy.douyin.douyin import Douyin
from apiproxy.douyin.download import Download
from apiproxy.douyin import douyin_headers
from apiproxy.tiktok.tiktokapi import TikTokApi
from apiproxy.tiktok import tiktok_headers
from apiproxy.tiktok import tiktok_headers
from apiproxy.common import utils
from utils.s3_uploader import S3Uploader
from backend.services.progress_service import ProgressService
import yaml

logger = logging.getLogger(__name__)


class DownloadService:
    """
    Service class for handling video download operations.
    Encapsulates business logic and integrates with existing Douyin/Download classes.
    """
    
    def __init__(self, download_path: str = None, cookie: str = None):
        """
        Initialize download service.
        
        Args:
            download_path: Path to save downloaded files
            cookie: Optional cookie string for authentication
        """
        if download_path:
            self.download_path = Path(download_path).resolve()
        else:
            self.download_path = (Path(os.getcwd()) / "Downloaded").resolve()
            
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Progress Service
        self.progress_service = ProgressService()
        
        # Initialize Douyin API client
        self.douyin = Douyin(database=True)
        
        # Initialize TikTok API client
        self.tiktok = TikTokApi()
        
        # Set cookie if provided
        if cookie:
            douyin_headers["Cookie"] = cookie
            self.douyin.set_cookies(cookie)
        
        # Initialize Download manager (for Douyin)
        self.downloader = Download(
            thread=5,
            music=True,
            cover=True,
            avatar=True,
            resjson=True,
            folderstyle=True,
            progress_callback=self.progress_service.update_progress
        )
        
        # Initialize TikTok Download manager with TikTok headers
        self.tiktok_headers_copy = tiktok_headers.copy()
        self.tiktok_downloader = Download(
            thread=5,
            music=True,
            cover=True,
            avatar=True,
            resjson=True,
            folderstyle=True,
            custom_headers=self.tiktok_headers_copy,
            progress_callback=self.progress_service.update_progress
        )
        
        
        # Initialize S3 Uploader
        self.s3_uploader = self._init_s3_uploader()
        
        logger.info(f"DownloadService initialized with path: {self.download_path}")

    def _init_s3_uploader(self):
        """Initialize S3 uploader from config file"""
        try:
            # Look for config in project root relative to this file
            # services/backend/root -> 3 levels up
            root_dir = Path(__file__).resolve().parent.parent.parent
            config_path = root_dir / "config.yml"
            
            if not config_path.exists():
                config_path = root_dir / "config.example.yml"
                
            logger.info(f"Loading config from: {config_path}")
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    aws_config = config.get('aws', {})
                    if aws_config.get('enabled'):
                        logger.info("S3 Uploader enabled in config")
                        return S3Uploader(
                            access_key_id=aws_config.get('access_key_id'),
                            secret_access_key=aws_config.get('secret_access_key'),
                            region=aws_config.get('region'),
                            bucket_name=aws_config.get('bucket_name'),
                            prefix=aws_config.get('prefix', ''),
                            endpoint_url=aws_config.get('endpoint_url')
                        )
                    else:
                        logger.info("S3 Uploader disabled in config")
            return None
        except Exception as e:
            logger.error(f"Failed to init S3 uploader: {e}")
            return None
    
    def download_video(self, url: str) -> Dict:
        """
        Download video from given URL.
        """
        try:
            self.progress_service.reset()
            logger.info(f"Starting download for URL: {url}")
            
            # Detect if it's a TikTok URL
            is_tiktok = 'tiktok.com' in url.lower() or 'vt.tiktok.com' in url.lower()
            
            if is_tiktok:
                logger.info("Detected TikTok URL, using TikTok API")
                # Get key type and ID from TikTok URL
                key_type, key = self.tiktok.getKey(url)
                logger.info(f"TikTok Key type: {key_type}, Key: {key}")
                
                if key_type == "aweme":
                    return self._download_tiktok_video(key)
                else:
                    return {
                        'success': False,
                        'message': f'Unsupported TikTok URL type: {key_type}. Please use a direct video link.',
                        'data': None
                    }
            else:
                # Douyin URL handling
                logger.info("Detected Douyin URL, using Douyin API")
                share_link = self.douyin.getShareLink(url)
                logger.info(f"Resolved share link: {share_link}")
                
                # Get key type and ID
                key_type, key = self.douyin.getKey(share_link)
                logger.info(f"Key type: {key_type}, Key: {key}")
                
                # Handle different content types
                if key_type == "aweme":
                    return self._download_single_video(key)
                elif key_type == "user":
                    return {
                        'success': False,
                        'message': 'User homepage URLs are not supported. Please use a direct video link.',
                        'data': None
                    }
                elif key_type == "mix":
                    return {
                        'success': False,
                        'message': 'Collection URLs are not supported. Please use a direct video link.',
                        'data': None
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Unsupported URL type: {key_type}',
                        'data': None
                    }
                
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Download failed: {str(e)}',
                'data': None
            }
    
    def _download_single_video(self, aweme_id: str) -> Dict:
        """
        Download a single video by aweme ID.
        
        Args:
            aweme_id: Video ID
            
        Returns:
            Download result dictionary
        """
        try:
            # Get video information
            logger.info(f"Fetching video info for aweme_id: {aweme_id}")
            video_data = self.douyin.getAwemeInfo(aweme_id)
            
            if not video_data:
                return {
                    'success': False,
                    'message': 'Failed to fetch video information. The video may be private or unavailable.',
                    'data': None
                }
            
            # Check prevent_download flag
            prevent_download = video_data.get('prevent_download', False)
            author_prevent_download = video_data.get('author', {}).get('prevent_download', False)
            
            if prevent_download or author_prevent_download:
                author_name = video_data.get('author', {}).get('nickname', 'Unknown')
                video_desc = video_data.get('desc', 'No title')
                
                logger.warning(f"Video has prevent_download enabled: {aweme_id}")
                return {
                    'success': False,
                    'message': '⚠️ Tác giả đã bật chế độ ngăn tải xuống cho video này. Không thể tải video không watermark.',
                    'data': {
                        'title': video_desc,
                        'author': author_name,
                        'aweme_id': aweme_id,
                        'prevent_download': True,
                        'reason': 'Author has enabled download protection'
                    }
                }
            
            # Create save path
            aweme_path = self.download_path / "aweme"
            aweme_path.mkdir(parents=True, exist_ok=True)
            
            # Download the video
            logger.info(f"Downloading video to: {aweme_path}")
            self.downloader.userDownload(awemeList=[video_data], savePath=str(aweme_path))
            
            # Extract metadata
            author_name = video_data.get('author', {}).get('nickname', 'Unknown')
            video_desc = video_data.get('desc', 'No title')
            
            # Clean filename
            clean_desc = utils.replaceStr(video_desc[:50])  # Limit title length
            
            # Find the downloaded file
            video_filename = self._find_downloaded_file(aweme_path, aweme_id)
            

            
            # S3 Upload
            if self.s3_uploader and self.s3_uploader.enabled and video_filename:
                self._upload_to_s3(aweme_path, video_filename)

            return {
                'success': True,
                'message': 'Video downloaded successfully',
                'data': {
                    'title': video_desc,
                    'author': author_name,
                    'aweme_id': aweme_id,
                    'filename': video_filename,
                    'file_path': str((aweme_path / video_filename).relative_to(self.download_path)) if video_filename else None,
                    'thumbnail': video_data.get('video', {}).get('cover', {}).get('url_list', [None])[0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in _download_single_video: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Download failed: {str(e)}',
                'data': None
            }
    
    def _download_tiktok_video(self, aweme_id: str) -> Dict:
        """
        Download a single TikTok video by aweme ID.
        
        Args:
            aweme_id: TikTok video ID
            
        Returns:
            Download result dictionary
        """
        try:
            # Get video information from TikTok
            logger.info(f"Fetching TikTok video info for aweme_id: {aweme_id}")
            video_data = self.tiktok.getAwemeInfo(aweme_id)
            
            if not video_data:
                return {
                    'success': False,
                    'message': 'Failed to fetch TikTok video information. The video may be private or unavailable.',
                    'data': None
                }
            
            # Check prevent_download flag for TikTok
            prevent_download = video_data.get('prevent_download', False)
            author_prevent_download = video_data.get('author', {}).get('prevent_download', False)
            
            if prevent_download or author_prevent_download:
                author_name = video_data.get('author', {}).get('nickname', 'Unknown')
                video_desc = video_data.get('desc', 'No title')
                
                logger.warning(f"TikTok video has prevent_download enabled: {aweme_id}")
                return {
                    'success': False,
                    'message': '⚠️ The author has enabled download protection for this TikTok video. Cannot download without watermark.',
                    'data': {
                        'title': video_desc,
                        'author': author_name,
                        'aweme_id': aweme_id,
                        'prevent_download': True,
                        'reason': 'Author has enabled download protection'
                    }
                }
            
            # Create save path
            aweme_path = self.download_path / "aweme"
            aweme_path.mkdir(parents=True, exist_ok=True)

            # Get session cookies and update headers
            cookies_dict = self.tiktok.get_session_cookies()
            if cookies_dict:
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
                self.tiktok_downloader.custom_headers["Cookie"] = cookie_str
                logger.info("Updated TikTok downloader with session cookies")
            
            # Download the video
            logger.info(f"Downloading TikTok video to: {aweme_path}")
            self.tiktok_downloader.userDownload(awemeList=[video_data], savePath=str(aweme_path))
            
            # Extract metadata
            author_name = video_data.get('author', {}).get('nickname', 'Unknown')
            video_desc = video_data.get('desc', 'No title')
            
            # Find the downloaded file
            video_filename = self._find_downloaded_file(aweme_path, aweme_id)
            


            # S3 Upload
            if self.s3_uploader and self.s3_uploader.enabled and video_filename:
                self._upload_to_s3(aweme_path, video_filename)
                
            return {
                'success': True,
                'message': 'TikTok video downloaded successfully',
                'data': {
                    'title': video_desc,
                    'author': author_name,
                    'aweme_id': aweme_id,
                    'filename': video_filename,
                    'file_path': str((aweme_path / video_filename).relative_to(self.download_path)) if video_filename else None,
                    'thumbnail': video_data.get('video', {}).get('cover', {}).get('url_list', [None])[0]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in _download_tiktok_video: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'TikTok download failed: {str(e)}',
                'data': None
            }
    
    def _find_downloaded_file(self, directory: Path, aweme_id: str) -> Optional[str]:
        """
        Find the downloaded video file in the directory.
        
        Args:
            directory: Directory to search
            aweme_id: Video ID to match
            
        Returns:
            Filename if found, None otherwise
        """
        try:
            # Look for video files (mp4)
            for file in directory.glob("*.mp4"):
                if aweme_id in file.name:
                    return file.name
            
            # If not found, return the most recent mp4 file
            mp4_files = list(directory.glob("*.mp4"))
            if mp4_files:
                latest_file = max(mp4_files, key=lambda f: f.stat().st_mtime)
                return latest_file.name
                
        except Exception as e:
            logger.error(f"Error finding downloaded file: {str(e)}")
        
        return None
    
        douyin_headers["Cookie"] = cookie
        self.douyin.set_cookies(cookie)
        logger.info("Cookie updated")

    def _upload_to_s3(self, directory: Path, video_filename: str):
        """Upload video and related files to S3, preserving folder structure"""
        try:
            # Upload video
            video_uploaded = False
            video_path = directory / video_filename
            
            if video_path.exists():
                # Use relative path as object name to maintain structure in S3
                # e.g. 'aweme/video_id.mp4'
                rel_path = str(video_path.relative_to(self.download_path)).replace('\\', '/')
                logger.info(f"Uploading video to S3 with key: {rel_path}")
                video_uploaded = self.s3_uploader.upload_file(str(video_path), object_name=rel_path)
            
            # Find and upload related files (cover, music, json)
            stem = Path(video_filename).stem
            for file in directory.glob(f"*{stem}*"):
                if file.name == video_filename:
                    continue
                
                # Also use relative path for related files
                rel_file_path = str(file.relative_to(self.download_path)).replace('\\', '/')
                logger.info(f"Uploading related file to S3 with key: {rel_file_path}")
                if self.s3_uploader.upload_file(str(file), object_name=rel_file_path):
                    # Remove related file after upload
                    try:
                        os.remove(file)
                        logger.info(f"Deleted local file: {file.name}")
                    except Exception as ex:
                        logger.warning(f"Failed to delete local file {file.name}: {ex}")

            # Remove video file after upload
            if video_path.exists() and video_uploaded:
                try:
                    os.remove(video_path)
                    logger.info(f"Deleted local video: {video_filename}")
                except Exception as ex:
                    logger.warning(f"Failed to delete local video {video_filename}: {ex}")
                
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
