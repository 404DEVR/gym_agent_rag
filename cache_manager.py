import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional

class ResponseCache:
    def __init__(self, cache_dir="cache", cache_duration_hours=24):
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_key(self, message: str) -> str:
        """Generate a cache key from the message"""
        # Normalize the message for better cache hits
        normalized = message.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> str:
        """Get the cache file path"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get_cached_response(self, message: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        cache_key = self._get_cache_key(message)
        cache_file = self._get_cache_file(cache_key)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > self.cache_duration:
                # Remove expired cache
                os.remove(cache_file)
                return None
            
            return cache_data['response']
        
        except (json.JSONDecodeError, KeyError, ValueError):
            # Remove corrupted cache file
            if os.path.exists(cache_file):
                os.remove(cache_file)
            return None
    
    def cache_response(self, message: str, response: str):
        """Cache a response"""
        cache_key = self._get_cache_key(message)
        cache_file = self._get_cache_file(cache_key)
        
        cache_data = {
            'message': message,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to cache response: {e}")
    
    def clear_cache(self):
        """Clear all cached responses"""
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                os.remove(os.path.join(self.cache_dir, filename))