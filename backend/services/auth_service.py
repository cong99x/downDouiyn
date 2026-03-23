import os
import yaml
import logging
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

class AuthService:
    """
    Service to handle Douyin authentication via manual cookie input.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AuthService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pass

    def update_cookie(self, cookie_str: str) -> dict:
        """
        Update cookie in config.yml with user-provided cookie string.
        
        Args:
            cookie_str: Cookie string from browser
            
        Returns:
            dict with status and message
        """
        try:
            if not cookie_str or not cookie_str.strip():
                return {
                    'status': 'error',
                    'message': 'Cookie string cannot be empty'
                }
            
            # Validate cookie format (basic check)
            if ';' not in cookie_str and '=' not in cookie_str:
                return {
                    'status': 'error',
                    'message': 'Invalid cookie format. Expected format: name1=value1; name2=value2'
                }
            
            root_dir = Path(__file__).resolve().parent.parent.parent
            config_path = root_dir / "config.yml"
            
            if not config_path.exists():
                return {
                    'status': 'error',
                    'message': 'config.yml not found'
                }
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            config['cookies'] = cookie_str.strip()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, allow_unicode=True)
            
            logger.info("Successfully updated config.yml with new cookies")
            return {
                'status': 'success',
                'message': 'Cookie updated successfully'
            }
        except Exception as e:
            logger.error(f"Failed to update config.yml: {e}")
            return {
                'status': 'error',
                'message': f'Failed to update cookie: {str(e)}'
            }
    
    def get_current_cookie(self) -> dict:
        """
        Get current cookie from config.yml
        
        Returns:
            dict with status and cookie data
        """
        try:
            root_dir = Path(__file__).resolve().parent.parent.parent
            config_path = root_dir / "config.yml"
            
            if not config_path.exists():
                return {
                    'status': 'error',
                    'message': 'config.yml not found'
                }
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            cookie = config.get('cookies', '')
            # Mask the cookie for security (show only first and last 20 chars)
            if len(cookie) > 40:
                masked_cookie = f"{cookie[:20]}...{cookie[-20:]}"
            else:
                masked_cookie = cookie[:10] + '...' if len(cookie) > 10 else cookie
            
            return {
                'status': 'success',
                'data': {
                    'cookie_preview': masked_cookie,
                    'has_cookie': bool(cookie)
                }
            }
        except Exception as e:
            logger.error(f"Failed to read config.yml: {e}")
            return {
                'status': 'error',
                'message': f'Failed to read cookie: {str(e)}'
            }
