import hashlib
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Union
from app import cache
import pickle
import os

class CacheManager:
    """Advanced cache management with TTL and invalidation strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_ttl = 300  # 5 minutes
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a consistent cache key
        
        Args:
            prefix: Key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Generated cache key
        """
        try:
            # Create a string representation of arguments
            key_parts = [str(arg) for arg in args]
            
            # Add sorted keyword arguments
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                key_parts.extend([f"{k}={v}" for k, v in sorted_kwargs])
            
            # Create hash of the key parts for consistency
            key_string = f"{prefix}:{':'.join(key_parts)}"
            
            # Use SHA256 hash for long keys to avoid length limits
            if len(key_string) > 200:
                key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]
                return f"{prefix}:{key_hash}"
            
            return key_string.replace(' ', '_').replace('/', '_')
            
        except Exception as e:
            self.logger.error(f"Error generating cache key: {str(e)}")
            return f"{prefix}:fallback_{int(time.time())}"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successfully cached
        """
        try:
            ttl = ttl or self.default_ttl
            
            # Wrap value with metadata
            cache_entry = {
                'value': value,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': ttl,
                'expires_at': (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()
            }
            
            cache.set(key, cache_entry, timeout=ttl)
            self.cache_stats['sets'] += 1
            
            self.logger.debug(f"Cached {key} with TTL {ttl}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            cache_entry = cache.get(key)
            
            if cache_entry is None:
                self.cache_stats['misses'] += 1
                return default
            
            # Check if it's a new format with metadata
            if isinstance(cache_entry, dict) and 'value' in cache_entry:
                self.cache_stats['hits'] += 1
                return cache_entry['value']
            else:
                # Old format or direct value
                self.cache_stats['hits'] += 1
                return cache_entry
                
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {str(e)}")
            self.cache_stats['misses'] += 1
            return default
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            cache.delete(key)
            self.cache_stats['deletes'] += 1
            self.logger.debug(f"Deleted cache key {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def get_or_set(self, key: str, callback, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """
        Get from cache or set using callback if not found
        
        Args:
            key: Cache key
            callback: Function to call if cache miss
            ttl: Time to live in seconds
            *args: Arguments for callback
            **kwargs: Keyword arguments for callback
            
        Returns:
            Cached or computed value
        """
        try:
            # Try to get from cache first
            value = self.get(key)
            
            if value is not None:
                return value
            
            # Cache miss - compute value
            self.logger.debug(f"Cache miss for {key}, computing value")
            
            try:
                value = callback(*args, **kwargs)
                
                # Cache the computed value
                if value is not None:
                    self.set(key, value, ttl)
                
                return value
                
            except Exception as e:
                self.logger.error(f"Error in cache callback for {key}: {str(e)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in get_or_set for {key}: {str(e)}")
            return None
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear cache keys matching a pattern (simplified implementation)
        
        Args:
            pattern: Pattern to match (basic wildcard support)
            
        Returns:
            Number of keys cleared
        """
        try:
            # This is a simplified implementation
            # In production, you might want to use Redis SCAN or similar
            cleared_count = 0
            
            # For Flask-Cache with simple backend, we can't easily iterate
            # So we'll log the intent and return 0
            self.logger.info(f"Clear pattern requested: {pattern}")
            
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing pattern {pattern}: {str(e)}")
            return 0
    
    def clear_symbol_cache(self, symbol: str) -> int:
        """
        Clear all cache entries for a specific symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Number of keys cleared
        """
        try:
            # Clear common symbol-related cache keys
            symbol_keys = [
                f"predict:{symbol}",
                f"compare:{symbol}",
                f"oracle:{symbol}",
                f"options:{symbol}",
                f"chart_data:{symbol}",
                f"strategies:{symbol}",
                f"sentiment:{symbol}",
                f"stock_data:{symbol}",
                f"real_time_price:{symbol}"
            ]
            
            cleared_count = 0
            for key in symbol_keys:
                if self.delete(key):
                    cleared_count += 1
            
            self.logger.info(f"Cleared {cleared_count} cache entries for symbol {symbol}")
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing symbol cache for {symbol}: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache performance statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'sets': self.cache_stats['sets'],
                'deletes': self.cache_stats['deletes'],
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def warm_cache(self, symbols: list) -> Dict:
        """
        Warm cache for a list of symbols
        
        Args:
            symbols: List of stock symbols to warm cache for
            
        Returns:
            Dictionary with warming results
        """
        try:
            from server.ml.data_fetcher import DataFetcher
            
            data_fetcher = DataFetcher()
            warmed_count = 0
            failed_count = 0
            
            self.logger.info(f"Starting cache warm-up for {len(symbols)} symbols")
            
            for symbol in symbols:
                try:
                    # Warm up basic stock data
                    stock_data_key = self.generate_cache_key('stock_data', symbol, period='1y')
                    stock_data = data_fetcher.get_stock_data(symbol, period='1y')
                    
                    if stock_data is not None and not stock_data.empty:
                        self.set(stock_data_key, stock_data, ttl=1800)  # 30 minutes
                        warmed_count += 1
                    else:
                        failed_count += 1
                    
                    # Add small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"Error warming cache for {symbol}: {str(e)}")
                    failed_count += 1
                    continue
            
            result = {
                'symbols_processed': len(symbols),
                'successful': warmed_count,
                'failed': failed_count,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(f"Cache warm-up completed: {warmed_count} successful, {failed_count} failed")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in cache warm-up: {str(e)}")
            return {
                'error': str(e),
                'symbols_processed': 0,
                'successful': 0,
                'failed': len(symbols) if symbols else 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def set_with_tags(self, key: str, value: Any, tags: list, ttl: Optional[int] = None) -> bool:
        """
        Set a cache value with tags for easier invalidation
        
        Args:
            key: Cache key
            value: Value to cache
            tags: List of tags to associate with this key
            ttl: Time to live in seconds
            
        Returns:
            True if successfully cached
        """
        try:
            ttl = ttl or self.default_ttl
            
            # Store the value with tags
            cache_entry = {
                'value': value,
                'tags': tags,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': ttl
            }
            
            # Set the main cache entry
            cache.set(key, cache_entry, timeout=ttl)
            
            # Update tag indexes
            for tag in tags:
                tag_key = f"tag:{tag}"
                tagged_keys = self.get(tag_key, [])
                
                if key not in tagged_keys:
                    tagged_keys.append(key)
                    # Use longer TTL for tag indexes
                    self.set(tag_key, tagged_keys, ttl=ttl*2)
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache with tags {key}: {str(e)}")
            return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache entries with a specific tag
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            Number of keys invalidated
        """
        try:
            tag_key = f"tag:{tag}"
            tagged_keys = self.get(tag_key, [])
            
            invalidated_count = 0
            
            for key in tagged_keys:
                if self.delete(key):
                    invalidated_count += 1
            
            # Clear the tag index
            self.delete(tag_key)
            
            self.logger.info(f"Invalidated {invalidated_count} keys with tag '{tag}'")
            return invalidated_count
            
        except Exception as e:
            self.logger.error(f"Error invalidating by tag {tag}: {str(e)}")
            return 0

# Global cache manager instance
cache_manager = CacheManager()
