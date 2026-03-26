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

from backend.controllers import download_bp, file_bp, auth_bp, init_download_service, init_file_service
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
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Load config from config.yml if it exists
    root_dir = Path(__file__).resolve().parent.parent
    config_path = root_dir / "config.yml"
    config_yaml = {}
    if config_path.exists():
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config_yaml = yaml.safe_load(f)
                logger.info("Loaded config from config.yml")
        except Exception as e:
            logger.error(f"Error loading config.yml: {e}")
    
    # Enable CORS for frontend communication
    # We apply CORS to all routes (/*) to ensure even error responses have proper headers
    CORS(app, resources={
        r"/*": {
            "origins": "*",  # Allow all origins for easier setup in VPS
            "methods": ["GET", "POST", "DELETE", "PUT", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"]
        }
    })
    
    # Path resolution logic - Ultra-stable for Docker/Local
    project_root = Path(__file__).resolve().parent.parent
    
    # Priority 1: Environment Variable
    raw_path = os.environ.get('DOWNLOAD_PATH') or config_yaml.get('path')
    
    if raw_path:
        download_path = Path(raw_path)
        if not download_path.is_absolute():
            download_path = project_root / download_path
    # Priority 2: Docker Environment Detection
    elif os.path.exists('/app/Downloaded') or os.environ.get('RENDER'):
        download_path = Path('/app/Downloaded')
    # Priority 3: Windows Default Local (C:\download tiktok)
    elif os.name == 'nt':
        download_path = Path("C:\\download tiktok")
    # Priority 4: Development Default
    else:
        download_path = project_root / "Downloaded"
        
    # Ensure the path is absolute and resolved (crucial for path matching)
    download_path = download_path.resolve()
    
    # CREATE FOLDER IF NOT EXISTS
    try:
        download_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Verified download directory: {download_path}")
    except Exception as e:
        logger.error(f"Could not create directory {download_path}: {e}")
    
    # Get cookie from environment or config file
    cookie = os.environ.get('DOUYIN_COOKIE') or config_yaml.get('cookies', '')
    
    # Initialize services with absolute path strings (resolved)
    download_service = DownloadService(download_path=str(download_path), cookie=cookie)
    file_service = FileService(download_path=str(download_path))
    
    logger.info(f"Services initialized with path: {download_path}")
    
    # Initialize controllers with services (Dependency Injection)
    init_download_service(download_service)
    init_file_service(file_service)
    
    # Register blueprints
    app.register_blueprint(download_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(auth_bp)
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Douyin Downloader API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'download': '/api/download',
                'files': '/api/files',
                'auth': '/api/auth'
            }
        })
    
    # Health check endpoint
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'download_path': str(download_path)
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
