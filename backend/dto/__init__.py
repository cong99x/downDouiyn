#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""DTO package for data transfer objects."""

from .download_dto import DownloadRequest, DownloadResponse, FileInfo, ApiResponse

__all__ = ['DownloadRequest', 'DownloadResponse', 'FileInfo', 'ApiResponse']
