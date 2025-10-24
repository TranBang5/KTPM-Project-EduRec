from flask import request, jsonify, g
from .jwt_utils import verify_jwt_token
from models.database import User

def jwt_required(f):
    """Decorator to require JWT authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            if not payload or payload.get('type') != 'access':
                return jsonify({'error': 'Invalid token'}), 401
            
            # Store user info in g object
            g.user_id = payload['user_id']
            g.user = User.query.get(payload['user_id'])
            if not g.user:
                return jsonify({'error': 'User not found'}), 404
                
        except Exception as e:
            return jsonify({'error': 'Invalid token format'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_jwt(f):
    """Decorator for optional JWT authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                payload = verify_jwt_token(token)
                if payload and payload.get('type') == 'access':
                    g.user_id = payload['user_id']
                    g.user = User.query.get(payload['user_id'])
            except:
                pass
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get current user from g object"""
    return getattr(g, 'user', None)

def get_current_user_id():
    """Get current user ID from g object"""
    return getattr(g, 'user_id', None)

def is_jwt_authenticated():
    """Check if user is authenticated via JWT"""
    return getattr(g, 'user', None) is not None
