#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Flask Application - Main entry point for the backend API server.
Configures Flask app, CORS, logging, and registers blueprints.
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.controllers import download_bp, file_bp, init_download_service, init_file_service
from backend.services import DownloadService, FileService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """
    Application factory pattern.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config['JSON_AS_ASCII'] = False  # Support UTF-8 characters
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
    
    # Apply custom configuration
    if config:
        app.config.update(config)
    
    # Enable CORS for frontend communication
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Get download path from environment or use default
    download_path = os.environ.get('DOWNLOAD_PATH', 
                                   os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Downloaded'))
    
    # Get cookie from environment or config file
    cookie = os.environ.get('DOUYIN_COOKIE', '')
    
    # Initialize services
    download_service = DownloadService(download_path=download_path, cookie=cookie)
    file_service = FileService(download_path=download_path)
    
    # Initialize controllers with services (Dependency Injection)
    init_download_service(download_service)
    init_file_service(file_service)
    
    # Register blueprints
    app.register_blueprint(download_bp)
    app.register_blueprint(file_bp)
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Douyin Downloader API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'download': '/api/download',
                'files': '/api/files'
            }
        })
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'download_path': download_path
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Endpoint not found',
            'errors': [str(error)]
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'errors': [str(error)]
        }), 500
    
    logger.info("Flask application created successfully")
    logger.info(f"Download path: {download_path}")
    
    return app


if __name__ == '__main__':
    # Create and run the application
    app = create_app()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info("API Documentation:")
    logger.info("  POST /api/download - Download a video")
    logger.info("  GET  /api/files - List downloaded files")
    logger.info("  GET  /api/files/<filename> - Get file info")
    logger.info("  DELETE /api/files/<filename> - Delete a file")
    logger.info("  GET  /api/files/<filename>/stream - Stream video file")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )
