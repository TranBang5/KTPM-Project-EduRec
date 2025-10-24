import jwt
from datetime import datetime, timedelta
from flask import current_app

def generate_jwt_token(user_id, token_type='access'):
    """Generate JWT token"""
    if token_type == 'access':
        expires = datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    else:  # refresh
        expires = datetime.utcnow() + current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
    
    payload = {
        'user_id': user_id,
        'type': token_type,
        'exp': expires,
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
