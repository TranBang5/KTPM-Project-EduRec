"""Cache utility functions for catalog service"""
import hashlib
import json
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

def make_cache_key(*args, **kwargs):
    """Create a cache key from request parameters"""
    # Get query parameters
    params = dict(request.args)
    # Sort params for consistent keys
    params_str = json.dumps(params, sort_keys=True)
    # Create hash for long keys
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    return f"catalog:{':'.join(str(arg) for arg in args)}:{params_hash}"

def invalidate_catalog_cache(cache_type=None, item_id=None):
    """Invalidate cache entries for catalog operations"""
    try:
        if cache_type == 'courses':
            if item_id:
                key = f"catalog:courses:{item_id}"
                if use_sharding:
                    sharded_cache.delete(key)
                else:
                    cache.delete(key)
        elif cache_type == 'tutors':
            if item_id:
                key = f"catalog:tutors:{item_id}"
                if use_sharding:
                    sharded_cache.delete(key)
                else:
                    cache.delete(key)
        elif cache_type == 'materials':
            if item_id:
                key = f"catalog:materials:{item_id}"
                if use_sharding:
                    sharded_cache.delete(key)
                else:
                    cache.delete(key)
        elif cache_type == 'search':
            # Search cache will expire naturally with TTL
            pass
    except Exception as e:
        logger.error(f"Cache invalidation error: {str(e)}")

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

def cached_list(timeout=300):
    """Decorator for caching list endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # Create cache key from query parameters
            params = dict(request.args)
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            cache_key = f"catalog:{f.__name__}:{params_hash}"
            
            # Try to get from cache
            if use_sharding:
                cached = sharded_cache.get(cache_key)
                if cached:
                    return _deserialize_response(cached)
            else:
                cached = cache.get(cache_key)
                if cached:
                    return cached
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache successful responses
            if result[1] == 200:
                if use_sharding:
                    sharded_cache.set(cache_key, _serialize_response(result), timeout=timeout)
                else:
                    cache.set(cache_key, result, timeout=timeout)
            
            return result
        return decorated_function
    return decorator

def get_cache_value(key: str):
    """Get value from cache (works with both sharded and non-sharded)"""
    if use_sharding:
        cached = sharded_cache.get(key)
        if cached:
            return _deserialize_response(cached)
    else:
        return cache.get(key)
    return None

def set_cache_value(key: str, value, timeout: int = 300):
    """Set value in cache (works with both sharded and non-sharded)"""
    if use_sharding:
        sharded_cache.set(key, _serialize_response(value), timeout=timeout)
    else:
        cache.set(key, value, timeout=timeout)

def cached_detail(timeout=900):
    """Decorator for caching detail endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get item_id from kwargs
            item_id = kwargs.get('course_id') or kwargs.get('tutor_id') or kwargs.get('material_id')
            if not item_id:
                return f(*args, **kwargs)
            
            cache_key = f"catalog:{f.__name__}:{item_id}"
            
            # Try to get from cache
            if use_sharding:
                cached = sharded_cache.get(cache_key)
                if cached:
                    return _deserialize_response(cached)
            else:
                cached = cache.get(cache_key)
                if cached:
                    return cached
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache successful responses
            if result[1] == 200:
                if use_sharding:
                    sharded_cache.set(cache_key, _serialize_response(result), timeout=timeout)
                else:
                    cache.set(cache_key, result, timeout=timeout)
            
            return result
        return decorated_function
    return decorator

