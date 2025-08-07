import json
import os
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

class CacheManager:
    """Enhanced cache management with persistence and intelligent invalidation"""
    
    def __init__(self, cache_dir='cache', default_ttl=300):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.memory_cache = {}
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize cache metadata
        self.metadata_file = os.path.join(cache_dir, 'cache_metadata.json')
        self.metadata = self._load_metadata()
        
        # Clean expired cache on startup
        self._cleanup_expired_cache()
    
    def _load_metadata(self):
        """Load cache metadata"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading cache metadata: {str(e)}")
        
        return {}
    
    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving cache metadata: {str(e)}")
    
    def _generate_cache_key(self, key: str) -> str:
        """Generate consistent cache key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Get cache file path"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with TTL"""
        try:
            cache_key = self._generate_cache_key(key)
            ttl = ttl or self.default_ttl
            
            cache_data = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl,
                'original_key': key
            }
            
            # Store in memory cache
            self.memory_cache[cache_key] = cache_data
            
            # Store in file cache
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            # Update metadata
            self.metadata[cache_key] = {
                'key': key,
                'timestamp': cache_data['timestamp'],
                'ttl': ttl,
                'file_path': cache_file
            }
            self._save_metadata()
            
            return True
            
        except Exception as e:
            logging.error(f"Error setting cache for key {key}: {str(e)}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Get cache value"""
        try:
            cache_key = self._generate_cache_key(key)
            
            # Try memory cache first
            if cache_key in self.memory_cache:
                cache_data = self.memory_cache[cache_key]
                if self._is_cache_valid(cache_data):
                    return cache_data['value']
                else:
                    # Remove expired cache
                    del self.memory_cache[cache_key]
            
            # Try file cache
            cache_file = self._get_cache_file_path(cache_key)
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                if self._is_cache_valid(cache_data):
                    # Load back into memory cache
                    self.memory_cache[cache_key] = cache_data
                    return cache_data['value']
                else:
                    # Remove expired file cache
                    os.remove(cache_file)
                    if cache_key in self.metadata:
                        del self.metadata[cache_key]
                        self._save_metadata()
            
            return default
            
        except Exception as e:
            logging.error(f"Error getting cache for key {key}: {str(e)}")
            return default
    
    def _is_cache_valid(self, cache_data: dict) -> bool:
        """Check if cache data is still valid"""
        try:
            timestamp = cache_data.get('timestamp', 0)
            ttl = cache_data.get('ttl', self.default_ttl)
            
            return (time.time() - timestamp) < ttl
            
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        try:
            cache_key = self._generate_cache_key(key)
            
            # Remove from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            # Remove from file cache
            cache_file = self._get_cache_file_path(cache_key)
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            # Remove from metadata
            if cache_key in self.metadata:
                del self.metadata[cache_key]
                self._save_metadata()
            
            return True
            
        except Exception as e:
            logging.error(f"Error deleting cache for key {key}: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache entries"""
        try:
            # Clear memory cache
            self.memory_cache.clear()
            
            # Clear file cache
            for cache_key in list(self.metadata.keys()):
                cache_file = self._get_cache_file_path(cache_key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            
            # Clear metadata
            self.metadata.clear()
            self._save_metadata()
            
            return True
            
        except Exception as e:
            logging.error(f"Error clearing all cache: {str(e)}")
            return False
    
    def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            expired_keys = []
            current_time = time.time()
            
            for cache_key, metadata in self.metadata.items():
                timestamp = metadata.get('timestamp', 0)
                ttl = metadata.get('ttl', self.default_ttl)
                
                if (current_time - timestamp) >= ttl:
                    expired_keys.append(cache_key)
            
            # Remove expired entries
            for cache_key in expired_keys:
                cache_file = self._get_cache_file_path(cache_key)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                
                if cache_key in self.metadata:
                    del self.metadata[cache_key]
                
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
            
            if expired_keys:
                self._save_metadata()
                logging.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        except Exception as e:
            logging.error(f"Error cleaning up expired cache: {str(e)}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        try:
            current_time = time.time()
            
            total_entries = len(self.metadata)
            memory_entries = len(self.memory_cache)
            
            # Calculate expired entries
            expired_count = 0
            cache_sizes = []
            
            for cache_key, metadata in self.metadata.items():
                timestamp = metadata.get('timestamp', 0)
                ttl = metadata.get('ttl', self.default_ttl)
                
                if (current_time - timestamp) >= ttl:
                    expired_count += 1
                
                # Get file size
                cache_file = metadata.get('file_path')
                if cache_file and os.path.exists(cache_file):
                    cache_sizes.append(os.path.getsize(cache_file))
            
            total_size = sum(cache_sizes)
            avg_size = total_size / len(cache_sizes) if cache_sizes else 0
            
            return {
                'total_entries': total_entries,
                'memory_entries': memory_entries,
                'expired_entries': expired_count,
                'active_entries': total_entries - expired_count,
                'total_size_bytes': total_size,
                'average_entry_size_bytes': avg_size,
                'cache_directory': self.cache_dir,
                'default_ttl_seconds': self.default_ttl
            }
            
        except Exception as e:
            logging.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        try:
            invalidated_count = 0
            
            for cache_key, metadata in list(self.metadata.items()):
                original_key = metadata.get('key', '')
                
                if pattern in original_key:
                    cache_file = self._get_cache_file_path(cache_key)
                    
                    # Remove from memory
                    if cache_key in self.memory_cache:
                        del self.memory_cache[cache_key]
                    
                    # Remove file
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                    
                    # Remove metadata
                    del self.metadata[cache_key]
                    invalidated_count += 1
            
            if invalidated_count > 0:
                self._save_metadata()
                logging.info(f"Invalidated {invalidated_count} cache entries matching pattern: {pattern}")
            
            return invalidated_count
            
        except Exception as e:
            logging.error(f"Error invalidating cache pattern {pattern}: {str(e)}")
            return 0
    
    def warmup_cache(self, key_value_pairs: list) -> int:
        """Warm up cache with multiple key-value pairs"""
        try:
            success_count = 0
            
            for key, value, ttl in key_value_pairs:
                if self.set(key, value, ttl):
                    success_count += 1
            
            logging.info(f"Cache warmup completed: {success_count}/{len(key_value_pairs)} entries loaded")
            return success_count
            
        except Exception as e:
            logging.error(f"Error warming up cache: {str(e)}")
            return 0
    
    def get_cache_keys(self, pattern: str = None) -> list:
        """Get all cache keys, optionally filtered by pattern"""
        try:
            keys = []
            
            for cache_key, metadata in self.metadata.items():
                original_key = metadata.get('key', '')
                
                if pattern is None or pattern in original_key:
                    keys.append(original_key)
            
            return sorted(keys)
            
        except Exception as e:
            logging.error(f"Error getting cache keys: {str(e)}")
            return []
    
    def export_cache(self, export_file: str) -> bool:
        """Export cache to file"""
        try:
            export_data = {
                'metadata': self.metadata,
                'export_timestamp': datetime.now().isoformat(),
                'cache_version': '1.0'
            }
            
            # Include cache data
            cache_entries = {}
            for cache_key, metadata in self.metadata.items():
                cache_file = self._get_cache_file_path(cache_key)
                if os.path.exists(cache_file):
                    with open(cache_file, 'r') as f:
                        cache_entries[cache_key] = json.load(f)
            
            export_data['cache_entries'] = cache_entries
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logging.info(f"Cache exported to {export_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting cache: {str(e)}")
            return False
    
    def import_cache(self, import_file: str) -> bool:
        """Import cache from file"""
        try:
            with open(import_file, 'r') as f:
                import_data = json.load(f)
            
            cache_entries = import_data.get('cache_entries', {})
            imported_count = 0
            
            for cache_key, cache_data in cache_entries.items():
                # Validate cache data
                if self._is_cache_valid(cache_data):
                    original_key = cache_data.get('original_key', cache_key)
                    value = cache_data.get('value')
                    ttl = cache_data.get('ttl', self.default_ttl)
                    
                    if self.set(original_key, value, ttl):
                        imported_count += 1
            
            logging.info(f"Cache import completed: {imported_count} entries imported")
            return True
            
        except Exception as e:
            logging.error(f"Error importing cache: {str(e)}")
            return False
