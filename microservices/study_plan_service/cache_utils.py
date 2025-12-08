"""Cache utility functions for study plan service"""
import pickle
from functools import wraps
from flask import request, jsonify
from flask_caching import Cache
from sharding import create_sharded_cache
import os
import logging

logger = logging.getLogger(__name__)

# Initialize sharded cache if REDIS_SHARDS is set, otherwise use single cache
use_sharding = os.getenv('REDIS_SHARDS') is not None

if use_sharding:
    sharded_cache = create_sharded_cache()
    cache = None  # Not used when sharding
else:
    cache = Cache()  # Single cache instance
    sharded_cache = None

def _serialize_response(response):
    """Serialize Flask response tuple to bytes for caching"""
    if isinstance(response, tuple) and len(response) == 2:
        # (jsonify_object, status_code)
        json_data, status_code = response
        # Convert to dict if it's a Response object
        if hasattr(json_data, 'get_json'):
            data = json_data.get_json()
        else:
            data = json_data
        return pickle.dumps((data, status_code))
    return pickle.dumps(response)

def _deserialize_response(cached_bytes):
    """Deserialize cached bytes back to Flask response"""
    if cached_bytes:
        try:
            data, status_code = pickle.loads(cached_bytes)
            return jsonify(data), status_code
        except Exception as e:
            logger.error(f"Error deserializing cache: {str(e)}")
            return None
    return None

def invalidate_user_cache(user_id):
    """Invalidate all cache entries for a specific user"""
    try:
        keys = [
            f"studyplan:{user_id}",
            f"studyplan:{user_id}:items",
            f"studyplan:{user_id}:schedule"
        ]
        
        if use_sharding:
            sharded_cache.delete_many(keys)
        else:
            for key in keys:
                cache.delete(key)
    except Exception as e:
        logger.error(f"Cache invalidation error: {str(e)}")

def cached_user_data(timeout=120):
    """Decorator for caching user-specific data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user_id from args or kwargs
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            
            if not user_id:
                return f(*args, **kwargs)
            
            # Determine cache key based on endpoint
            endpoint_name = f.__name__
            if 'schedule' in endpoint_name:
                cache_key = f"studyplan:{user_id}:schedule"
            elif 'items' in endpoint_name or 'item' in endpoint_name:
                cache_key = f"studyplan:{user_id}:items"
            else:
                cache_key = f"studyplan:{user_id}"
            
            # Try to get from cache
            if use_sharding:
                cached = sharded_cache.get(cache_key)
                if cached:
                    return _deserialize_response(cached)
            else:
                cached = cache.get(cache_key)
                if cached:
                    return cached
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            
            # Only cache successful GET responses
            if request.method == 'GET' and result[1] == 200:
                if use_sharding:
                    sharded_cache.set(cache_key, _serialize_response(result), timeout=timeout)
                else:
                    cache.set(cache_key, result, timeout=timeout)
            
            return result
        return decorated_function
    return decorator

