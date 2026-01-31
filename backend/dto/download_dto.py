#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Transfer Objects for API request/response validation.
Following SOLID principles - single responsibility for data validation.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class DownloadRequest:
    """DTO for download request validation."""
    url: str
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate download request.
        
        Returns:
            (is_valid, error_message)
        """
        if not self.url:
            return False, "URL is required"
        
        import re
        # Regex to find Douyin or TikTok URLs in text
        # Supports: 
        # - douyin.com, v.douyin.com, iesdouyin.com
        # - tiktok.com, www.tiktok.com, vm.tiktok.com, vt.tiktok.com, m.tiktok.com
        pattern = r'https?://(?:[a-zA-Z0-9-]+\.)?(?:douyin\.com|tiktok\.com|iesdouyin\.com)/[a-zA-Z0-9/_?=&%\-\.@]+'
        
        match = re.search(pattern, self.url)
        if match:
            # Update url with the extracted one
            self.url = match.group(0)
            return True, None
            
        return False, "Invalid URL format. Must be a Douyin or TikTok URL"


@dataclass
class DownloadResponse:
    """DTO for download response."""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'error': self.error
        }


@dataclass
class FileInfo:
    """DTO representing downloaded file metadata."""
    filename: str
    title: str
    author: str
    file_size: int
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    download_date: Optional[str] = None
    file_path: Optional[str] = None
    video_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'filename': self.filename,
            'title': self.title,
            'author': self.author,
            'file_size': self.file_size,
            'duration': self.duration,
            'thumbnail': self.thumbnail,
            'download_date': self.download_date,
            'file_path': self.file_path,
            'video_url': self.video_url
        }


@dataclass
class ApiResponse:
    """Generic API response wrapper."""
    status: str  # 'success' or 'error'
    data: Optional[dict] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {'status': self.status}
        if self.data is not None:
            result['data'] = self.data
        if self.message:
            result['message'] = self.message
        if self.errors:
            result['errors'] = self.errors
        return result
