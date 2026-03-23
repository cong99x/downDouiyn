
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class ProgressService:
    """
    Simple singleton service to track download progress.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProgressService, cls).__new__(cls)
                cls._instance.progress = {} # { 'current': 0.0 }
        return cls._instance
    
    def update_progress(self, percentage: float):
        """Update the current progress percentage."""
        self.progress['current'] = round(percentage, 2)
        
    def get_progress(self) -> float:
        """Get the current progress percentage."""
        return self.progress.get('current', 0.0)
    
    def reset(self):
        """Reset progress to zero."""
        self.progress['current'] = 0.0
