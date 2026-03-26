#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File Service - Business logic layer for file management operations.
Single Responsibility: Handle all file-related operations.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from utils.s3_uploader import S3Uploader
import yaml

logger = logging.getLogger(__name__)


class FileService:
    """
    Service class for managing downloaded files.
    Handles file listing, metadata extraction, and file operations.
    """
    
    def __init__(self, download_path: str = None):
        """
        Initialize file service.
        
        Args:
            download_path: Path where downloaded files are stored
        """
        self.download_path = Path(download_path).resolve() if download_path else Path(os.getcwd()).resolve() / "Downloaded"
        self.s3_uploader = self._init_s3_uploader()
        logger.info(f"FileService initialized with path: {self.download_path}")

    def _init_s3_uploader(self):
        """Initialize S3 uploader from config file"""
        try:
            # Look for config in project root relative to this file
            root_dir = Path(__file__).resolve().parent.parent.parent
            config_path = root_dir / "config.yml"
            
            if not config_path.exists():
                config_path = root_dir / "config.example.yml"
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    aws_config = config.get('aws', {})
                    if aws_config.get('enabled'):
                        return S3Uploader(
                            access_key_id=aws_config.get('access_key_id'),
                            secret_access_key=aws_config.get('secret_access_key'),
                            region=aws_config.get('region'),
                            bucket_name=aws_config.get('bucket_name'),
                            prefix=aws_config.get('prefix', ''),
                            endpoint_url=aws_config.get('endpoint_url')
                        )
            return None
        except Exception as e:
            logger.error(f"Failed to init S3 uploader: {e}")
            return None
    
    def list_downloaded_files(self) -> List[Dict]:
        """
        List all downloaded video files with metadata.
        
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            
            if self.s3_uploader and self.s3_uploader.enabled:
                # List from S3
                logger.info("Listing files from S3...")
                s3_files = self.s3_uploader.list_files()
                for obj in s3_files:
                    key = obj['Key']
                    if key.endswith('.mp4'):
                        files.append(self._s3_object_to_file_info(obj))
            else:
                # List from local
                if not self.download_path.exists():
                    logger.warning(f"Download path does not exist: {self.download_path}")
                    return files
                
                # Scan all subdirectories for video files
                for video_file in self.download_path.rglob("*.mp4"):
                    file_info = self._extract_file_info(video_file)
                    if file_info:
                        files.append(file_info)
            
            # Sort by download date (newest first)
            files.sort(key=lambda x: x.get('download_date', ''), reverse=True)
            
            logger.info(f"Found {len(files)} video files")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}", exc_info=True)
            return []

    def _s3_object_to_file_info(self, obj: Dict) -> Dict:
        """Convert S3 object to FileInfo dict"""
        key = obj['Key']
        filename = key.split('/')[-1]
        
        # Try to extract title/author from path if structure is Author/Title/file.mp4
        # or Author/Title_ID/file.mp4
        parts = key.split('/')
        author = "Unknown"
        title = filename
        
        if len(parts) >= 3:
            author = parts[-2] # Assuming folder structure
            # Or parts[-3] if deeper. 
            # Let's rely on simple heuristic for now.
        
        return {
            'filename': filename,
            'title': title, # We don't have rich metadata in S3 list, using filename
            'author': author,
            'file_size': obj['Size'],
            'file_size_mb': round(obj['Size'] / (1024 * 1024), 2),
            'download_date': obj['LastModified'].isoformat(),
            'download_date_formatted': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
            'file_path': key, # Use Key as path
            'full_path': key, # Use Key as full path
            'thumbnail': None, # S3 thumbnail would need another call
            'duration': None,
            'aweme_id': ''
        }
    
    def _extract_file_info(self, video_path: Path) -> Optional[Dict]:
        """
        Extract metadata for a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with file metadata or None if extraction fails
        """
        try:
            # Get basic file info
            stat = video_path.stat()
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to find associated JSON file
            json_path = video_path.with_suffix('.json')
            metadata = {}
            
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read JSON metadata for {video_path.name}: {str(e)}")
            
            # Extract information
            title = metadata.get('desc', video_path.stem)
            author = metadata.get('author', {}).get('nickname', 'Unknown')
            
            # Try to find thumbnail
            thumbnail_path = None
            cover_file = video_path.with_name(video_path.stem + '_cover.jpg')
            if cover_file.exists():
                thumbnail_path = str(cover_file.relative_to(self.download_path))
            
            return {
                'filename': video_path.name,
                'title': title,
                'author': author,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'download_date': modified_time.isoformat(),
                'download_date_formatted': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                'file_path': str(video_path.relative_to(self.download_path)),
                'full_path': str(video_path),
                'thumbnail': thumbnail_path,
                'duration': metadata.get('video', {}).get('duration'),
                'aweme_id': metadata.get('aweme_id', '')
            }
            
        except Exception as e:
            logger.error(f"Error extracting file info for {video_path}: {str(e)}")
            return None
    
    def get_file_info(self, filename: str) -> Optional[Dict]:
        """
        Get detailed information for a specific file.
        
        Args:
            filename: Name of the file or relative path
            
        Returns:
            File information dictionary or None if not found
        """
        try:
            # Search for the file
            for video_file in self.download_path.rglob(filename):
                if video_file.is_file():
                    return self._extract_file_info(video_file)
            
            logger.warning(f"File not found: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}", exc_info=True)
            return None
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a video file and its associated files (JSON, cover, etc.).
        
        Args:
            filename: Name of the file or relative path from download_path
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # First, try as a direct relative path (more precise)
            video_path = self.download_path / filename
            
            # If not found directly, try to search (fallback)
            if not video_path.exists() or not video_path.is_file():
                logger.info(f"File not found at direct path {video_path}, searching...")
                video_path = None
                # Use a safer search that doesn't treat filename as a glob pattern if it contains []
                for file in self.download_path.rglob("*"):
                    if file.is_file() and (file.name == filename or str(file.relative_to(self.download_path)) == filename):
                        video_path = file
                        break
            
            if not video_path:
                logger.warning(f"File not found for deletion: {filename}")
                return False
            
            # Delete associated files
            base_name = video_path.stem
            parent_dir = video_path.parent
            
            deleted_files = []
            
            # Delete video file
            if video_path.exists():
                video_path.unlink()
                deleted_files.append(str(video_path.name))
            
            # Also try to delete files in S3 if enabled
            if self.s3_uploader and self.s3_uploader.enabled:
                try:
                    # Logic for S3 deletion if needed, for now just local
                    pass
                except Exception as s3_err:
                    logger.warning(f"Failed to delete from S3: {s3_err}")
            
            # Find and delete associated metadata files in the same directory
            # We look for files starting with the same stem and having common extensions
            for suffix in ['.json', '_cover.jpg', '_music.mp3', '.mp3', '.jpg']:
                assoc_file = parent_dir / f"{base_name}{suffix}"
                if assoc_file.exists():
                    assoc_file.unlink()
                    deleted_files.append(assoc_file.name)
            
            logger.info(f"Deleted files: {', '.join(deleted_files)}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}", exc_info=True)
            return False
    
    def get_file_path(self, filename: str) -> Optional[Path]:
        """
        Get absolute path to a file, with security checks.
        Args:
            filename: Name of the file or relative path (e.g. 'aweme/vid.mp4')
        Returns:
            Absolute Path object or None if not found
        """
        try:
            logger.debug(f"get_file_path called with: {filename}")
            
            # 1. Try as a relative path from download_path
            path = (self.download_path / filename).resolve()
            
            if path.exists() and path.is_file():
                # Security check: ensure the file is inside the download_path
                # is_relative_to requires Python 3.9+, otherwise use simple check
                try:
                    path.relative_to(self.download_path)
                    return path
                except ValueError:
                    logger.warning(f"Security: Blocked access to path outside download folder: {path}")
                    return None
            
            # 2. Try as a pure filename (search for it if direct path fails)
            logger.info(f"File not found at direct path {path}, searching recursively...")
            just_filename = os.path.basename(filename)
            for video_file in self.download_path.rglob("*"):
                if video_file.is_file() and video_file.name == just_filename:
                    return video_file.resolve()
                    
            logger.warning(f"File not found anywhere in {self.download_path}: {filename}")
            return None
        except Exception as e:
            logger.error(f"Error getting file path for {filename}: {str(e)}")
            return None
