#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File Controller - HTTP request handler for file management endpoints.
Single Responsibility: Handle HTTP requests for file operations.
"""

import logging
import mimetypes
from flask import Blueprint, request, jsonify, send_file
from pathlib import Path

from backend.services import FileService
from backend.dto import ApiResponse

logger = logging.getLogger(__name__)

# Create blueprint
file_bp = Blueprint('files', __name__, url_prefix='/api/files')

# Initialize service (will be configured by app)
file_service = None


def init_file_service(service: FileService):
    """Initialize the file service instance."""
    global file_service
    file_service = service


@file_bp.route('', methods=['GET'])
def list_files():
    """
    List all downloaded files.
    
    Response:
        {
            "status": "success",
            "data": {
                "files": [
                    {
                        "filename": "video.mp4",
                        "title": "Video title",
                        "author": "Author name",
                        "file_size": 12345678,
                        "file_size_mb": 11.77,
                        "download_date": "2026-01-30T22:00:00",
                        "thumbnail": "path/to/thumbnail.jpg"
                    }
                ],
                "count": 1
            }
        }
    """
    try:
        files = file_service.list_downloaded_files()
        
        response = ApiResponse(
            status='success',
            data={
                'files': files,
                'count': len(files)
            }
        )
        return jsonify(response.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        response = ApiResponse(
            status='error',
            message='Failed to list files',
            errors=[str(e)]
        )
        return jsonify(response.to_dict()), 500


@file_bp.route('/<path:filename>', methods=['GET'])
def get_file_info(filename: str):
    """
    Get information about a specific file.
    
    Args:
        filename: Name of the file
    
    Response:
        {
            "status": "success",
            "data": {
                "filename": "video.mp4",
                "title": "Video title",
                ...
            }
        }
    """
    try:
        file_info = file_service.get_file_info(filename)
        
        if file_info:
            response = ApiResponse(
                status='success',
                data=file_info
            )
            return jsonify(response.to_dict()), 200
        else:
            response = ApiResponse(
                status='error',
                message='File not found',
                errors=[f'File not found: {filename}']
            )
            return jsonify(response.to_dict()), 404
            
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}", exc_info=True)
        response = ApiResponse(
            status='error',
            message='Failed to get file information',
            errors=[str(e)]
        )
        return jsonify(response.to_dict()), 500


@file_bp.route('/<path:filename>', methods=['DELETE'])
def delete_file(filename: str):
    """
    Delete a file.
    
    Args:
        filename: Name of the file to delete
    
    Response:
        {
            "status": "success",
            "message": "File deleted successfully"
        }
    """
    try:
        success = file_service.delete_file(filename)
        
        if success:
            response = ApiResponse(
                status='success',
                message='File deleted successfully'
            )
            return jsonify(response.to_dict()), 200
        else:
            response = ApiResponse(
                status='error',
                message='Failed to delete file',
                errors=['File not found or deletion failed']
            )
            return jsonify(response.to_dict()), 404
            
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        response = ApiResponse(
            status='error',
            message='Failed to delete file',
            errors=[str(e)]
        )
        return jsonify(response.to_dict()), 500


@file_bp.route('/stream', methods=['GET'])
def stream_file():
    """Stream a video file for preview."""
    path_param = request.args.get('path')
    logger.info(f"Stream request for path: {path_param}")
    
    try:
        if not path_param:
            return jsonify({'status': 'error', 'message': 'No file path provided'}), 400
            
        file_path = file_service.get_file_path(path_param)
        logger.info(f"Resolved physical path: {file_path}")
        
        if file_path and file_path.exists() and file_path.is_file():
            # Use absolute path as string
            abs_path = str(file_path.absolute())
            mime_type, _ = mimetypes.guess_type(abs_path)
            mime_type = mime_type or 'application/octet-stream'
            
            logger.info(f"Serving file: {abs_path} with mimetype: {mime_type}")
            return send_file(
                abs_path,
                mimetype=mime_type,
                as_attachment=False,
                conditional=True
            )
        
        logger.warning(f"File not found: {path_param}")
        return jsonify({'status': 'error', 'message': f'File not found: {path_param}'}), 404
    except Exception as e:
        import traceback
        logger.error(f"Error streaming file {path_param}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500


@file_bp.route('/download', methods=['GET'])
def download_file():
    """Download a video file."""
    path_param = request.args.get('path')
    logger.info(f"Download request for path: {path_param}")
    
    try:
        if not path_param:
            return jsonify({'status': 'error', 'message': 'No file path provided'}), 400
            
        file_path = file_service.get_file_path(path_param)
        logger.info(f"Resolved physical path: {file_path}")
        
        if file_path and file_path.exists() and file_path.is_file():
            abs_path = str(file_path.absolute())
            logger.info(f"Downloading file: {abs_path}")
            
            # Use application/octet-stream to FORCE download on iOS Safari
            # If we use video/mp4, iOS often tries to play it instead of downloading
            return send_file(
                abs_path,
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name=file_path.name,
                conditional=True
            )
        
        # If not found locally, try to get S3 URL if possible
        if file_service.s3_uploader and file_service.s3_uploader.enabled:
            # Assume path_param might be the S3 key
            s3_url = file_service.s3_uploader.get_presigned_url(path_param)
            if s3_url:
                logger.info(f"Redirecting download to S3: {s3_url}")
                from flask import redirect
                return redirect(s3_url)
        
        logger.warning(f"File not found for download: {path_param}")
        return jsonify({'status': 'error', 'message': f'File not found: {path_param}'}), 404
    except Exception as e:
        import traceback
        logger.error(f"Error downloading file {path_param}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500


@file_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'success',
        'message': 'File service is running'
    }), 200
