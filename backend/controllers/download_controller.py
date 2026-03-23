#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download Controller - HTTP request handler for download endpoints.
Single Responsibility: Handle HTTP requests and delegate to service layer.
"""

import logging
from flask import Blueprint, request, jsonify, Response
import time
import json

from backend.services import DownloadService, ProgressService
from backend.dto import DownloadRequest, ApiResponse

logger = logging.getLogger(__name__)

# Create blueprint
download_bp = Blueprint('download', __name__, url_prefix='/api/download')

# Initialize services
download_service = None
progress_service = ProgressService()


def init_download_service(service: DownloadService):
    """Initialize the download service instance."""
    global download_service
    download_service = service


@download_bp.route('/progress', methods=['GET'])
def get_progress():
    """
    SSE endpoint to stream download progress.
    """
    def generate():
        last_progress = -1
        while True:
            current_progress = progress_service.get_progress()
            # Only send update if progress changed
            if current_progress != last_progress:
                yield f"data: {json.dumps({'progress': current_progress})}\n\n"
                last_progress = current_progress
                
            if current_progress >= 100:
                # Keep it at 100 for a bit then break or wait for next reset
                time.sleep(2)
                # We don't break here to keep the connection alive if needed, 
                # but frontend will usually close after success
            
            time.sleep(0.5) # Poll internal state every 500ms

    return Response(generate(), mimetype='text/event-stream')


@download_bp.route('', methods=['POST'])
def download_video():
    """
    Download video endpoint.
    
    Request Body:
        {
            "url": "https://v.douyin.com/xxxxx/"
        }
    
    Response:
        {
            "status": "success",
            "message": "Video downloaded successfully",
            "data": {
                "title": "Video title",
                "author": "Author name",
                "filename": "video.mp4",
                "file_path": "/path/to/video.mp4",
                "thumbnail": "thumbnail_url"
            }
        }
    """
    try:
        # Validate request
        if not request.is_json:
            response = ApiResponse(
                status='error',
                message='Content-Type must be application/json',
                errors=['Invalid content type']
            )
            return jsonify(response.to_dict()), 400
        
        data = request.get_json()
        
        # Validate URL
        if 'url' not in data:
            response = ApiResponse(
                status='error',
                message='URL is required',
                errors=['Missing required field: url']
            )
            return jsonify(response.to_dict()), 400
        
        # Create DTO and validate
        download_req = DownloadRequest(url=data['url'])
        is_valid, error_msg = download_req.validate()
        
        if not is_valid:
            response = ApiResponse(
                status='error',
                message='Invalid request',
                errors=[error_msg]
            )
            return jsonify(response.to_dict()), 400
        
        # Call service
        logger.info(f"Download request received for URL: {download_req.url}")
        result = download_service.download_video(download_req.url)
        
        if result['success']:
            response = ApiResponse(
                status='success',
                message=result['message'],
                data=result['data']
            )
            return jsonify(response.to_dict()), 200
        else:
            response = ApiResponse(
                status='error',
                message=result['message'],
                errors=[result['message']]
            )
            return jsonify(response.to_dict()), 400
            
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}", exc_info=True)
        response = ApiResponse(
            status='error',
            message='Internal server error',
            errors=[str(e)]
        )
        return jsonify(response.to_dict()), 500


@download_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'success',
        'message': 'Download service is running'
    }), 200
