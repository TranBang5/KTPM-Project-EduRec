"""Sharding utility for catalog service cache"""
import hashlib
import os
from typing import List, Optional
from redis import Redis
from flask_caching import Cache
import logging

logger = logging.getLogger(__name__)

class ShardedCache:
    """Sharded cache manager for distributing cache across multiple Redis instances"""
    
    def __init__(self, shard_urls: List[str], shard_count: int):
        """
        Initialize sharded cache
        
        Args:
            shard_urls: List of Redis URLs for each shard
            shard_count: Number of shards
        """
        self.shard_count = shard_count
        self.shards: List[Cache] = []
        self.redis_clients: List[Redis] = []
        
        # Initialize cache instances for each shard
        for i, url in enumerate(shard_urls):
            try:
                # Parse Redis URL
                # Format: redis://host:port/db
                from urllib.parse import urlparse
                parsed = urlparse(url)
                host = parsed.hostname or 'localhost'
                port = int(parsed.port or 6379)
                db = int(parsed.path.lstrip('/') or 0)
                
                # Create Redis client
                redis_client = Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=False,  # Keep binary for compatibility
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                self.redis_clients.append(redis_client)
                
                # Create Flask-Caching instance
                cache = Cache()
                self.shards.append(cache)
                
                logger.info(f"Initialized Redis shard {i}: {host}:{port}/{db}")
            except Exception as e:
                logger.error(f"Failed to initialize shard {i} ({url}): {str(e)}")
                raise
    
    def _get_shard_index(self, key: str) -> int:
        """
        Determine which shard to use for a given key
        
        Args:
            key: Cache key
            
        Returns:
            Shard index (0 to shard_count-1)
        """
        # Use consistent hashing (MD5 hash modulo shard_count)
        hash_value = int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)
        return hash_value % self.shard_count
    
    def _get_shard(self, key: str) -> Cache:
        """Get the cache instance for a given key"""
        shard_index = self._get_shard_index(key)
        return self.shards[shard_index]
    
    def _get_redis_client(self, key: str) -> Redis:
        """Get the Redis client for a given key"""
        shard_index = self._get_shard_index(key)
        return self.redis_clients[shard_index]
    
    def get(self, key: str) -> Optional[bytes]:
        """Get value from cache"""
        try:
            redis_client = self._get_redis_client(key)
            value = redis_client.get(key)
            return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: bytes, timeout: int = 300):
        """Set value in cache"""
        try:
            redis_client = self._get_redis_client(key)
            redis_client.setex(key, timeout, value)
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            redis_client = self._get_redis_client(key)
            redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
    
    def delete_many(self, keys: List[str]):
        """Delete multiple keys from cache"""
        # Group keys by shard
        shard_keys = {}
        for key in keys:
            shard_index = self._get_shard_index(key)
            if shard_index not in shard_keys:
                shard_keys[shard_index] = []
            shard_keys[shard_index].append(key)
        
        # Delete from each shard
        for shard_index, keys_list in shard_keys.items():
            try:
                redis_client = self.redis_clients[shard_index]
                if keys_list:
                    redis_client.delete(*keys_list)
            except Exception as e:
                logger.error(f"Error deleting keys from shard {shard_index}: {str(e)}")
    
    def clear(self):
        """Clear all caches (all shards)"""
        for i, redis_client in enumerate(self.redis_clients):
            try:
                redis_client.flushdb()
                logger.info(f"Cleared shard {i}")
            except Exception as e:
                logger.error(f"Error clearing shard {i}: {str(e)}")
    
    def get_stats(self) -> dict:
        """Get statistics from all shards"""
        stats = {
            'shard_count': self.shard_count,
            'shards': []
        }
        
        for i, redis_client in enumerate(self.redis_clients):
            try:
                info = redis_client.info()
                stats['shards'].append({
                    'index': i,
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'keyspace': info.get('db0', {}).get('keys', 0) if 'db0' in str(info) else 0
                })
            except Exception as e:
                stats['shards'].append({
                    'index': i,
                    'error': str(e)
                })
        
        return stats


def create_sharded_cache() -> ShardedCache:
    """Factory function to create sharded cache from environment variables"""
    shard_urls_str = os.getenv('REDIS_SHARDS', 'redis://localhost:6379/0')
    shard_count = int(os.getenv('REDIS_SHARD_COUNT', '1'))
    
    shard_urls = [url.strip() for url in shard_urls_str.split(',')]
    
    if len(shard_urls) != shard_count:
        logger.warning(f"Shard count mismatch: {len(shard_urls)} URLs but {shard_count} expected")
    
    return ShardedCache(shard_urls, shard_count)




















