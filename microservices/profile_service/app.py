from flask import Flask, request, jsonify
from models.database import db, User
import os
import sys
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://user:password@db:3306/recommendation_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Auth service URL for token verification
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5004')

# Initialize database
db.init_app(app)

def verify_token_with_auth_service(token):
    """Verify JWT token with auth service"""
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/verify-token",
            json={'token': token},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header missing'}), 401
        
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = verify_token_with_auth_service(token)
        
        if not payload or not payload.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        request.current_user_id = payload.get('user_id')
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for profile service"""
    return jsonify({
        'service': 'profile-service',
        'status': 'running',
        'description': 'Profile Service for managing user profiles',
        'available_endpoints': {
            'health': '/health',
            'get_profile': '/profiles/<user_id> (GET)',
            'update_profile': '/profiles/<user_id> (PUT)',
            'profile_history': '/profiles/<user_id>/history (GET)'
        },
        'features': ['profile_management', 'avatar']
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'profile-service',
        'features': ['profile_management', 'avatar']
    }), 200

@app.route('/profiles/<int:user_id>', methods=['GET'])
@require_auth
def get_profile(user_id):
    """Get user profile"""
    # Verify user can only access their own profile
    if request.current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = User.query.get(user_id)
        
        # If user not found in Profile Service database, try to get from Auth Service
        if not user:
            logger.warning(f"User {user_id} not found in Profile Service database, trying Auth Service...")
            try:
                # Get auth header from request
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    # Call Auth Service to get profile
                    auth_response = requests.get(
                        f"{AUTH_SERVICE_URL}/auth/profile",
                        headers={'Authorization': auth_header},
                        timeout=5
                    )
                    if auth_response.status_code == 200:
                        auth_user_data = auth_response.json()
                        logger.info(f"Retrieved user {user_id} from Auth Service")
                        return jsonify(auth_user_data), 200
                    else:
                        logger.error(f"Auth Service returned status {auth_response.status_code}")
                else:
                    logger.error("No Authorization header found")
            except Exception as e:
                logger.error(f"Error fetching from Auth Service: {str(e)}")
            
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'school': user.school,
            'current_grade': user.current_grade,
            'favorite_subjects': user.favorite_subjects,
            'learning_goals': user.learning_goals,
            'preferred_learning_method': user.preferred_learning_method,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }), 200
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        # Fallback: try Auth Service
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                auth_response = requests.get(
                    f"{AUTH_SERVICE_URL}/auth/profile",
                    headers={'Authorization': auth_header},
                    timeout=5
                )
                if auth_response.status_code == 200:
                    logger.info(f"Fallback: Retrieved user {user_id} from Auth Service")
                    return jsonify(auth_response.json()), 200
        except Exception as fallback_error:
            logger.error(f"Fallback to Auth Service also failed: {str(fallback_error)}")
        
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@app.route('/profiles/<int:user_id>', methods=['PUT'])
@require_auth
def update_profile(user_id):
    """Update user profile"""
    # Verify user can only update their own profile
    if request.current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'school' in data:
        user.school = data['school']
    if 'current_grade' in data:
        user.current_grade = data['current_grade']
    if 'favorite_subjects' in data:
        user.favorite_subjects = data['favorite_subjects']
    if 'learning_goals' in data:
        user.learning_goals = data['learning_goals']
    if 'preferred_learning_method' in data:
        user.preferred_learning_method = data['preferred_learning_method']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'school': user.school,
                'current_grade': user.current_grade,
                'favorite_subjects': user.favorite_subjects,
                'learning_goals': user.learning_goals,
                'preferred_learning_method': user.preferred_learning_method
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@app.route('/profiles/<int:user_id>/history', methods=['GET'])
@require_auth
def get_profile_history(user_id):
    """Get profile change history"""
    if request.current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # In a real implementation, this would query a profile_history table
    # For now, return empty array
    return jsonify({
        'user_id': user_id,
        'history': []
    }), 200

if __name__ == '__main__':
    try:
        logger.info("Initializing Profile Service...")
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created/verified successfully")
            except Exception as db_error:
                logger.warning(f"Database initialization warning: {str(db_error)}")
                logger.info("Service will continue to start. Database connection will be established on first request.")
        
        logger.info(f"Profile Service starting on port 5006")
        logger.info(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")
        logger.info(f"Auth Service URL: {AUTH_SERVICE_URL}")
        
        # Disable debug mode in Docker to prevent auto-restart
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(host='0.0.0.0', port=5006, debug=debug_mode)
    except Exception as e:
        logger.error(f"Failed to start Profile Service: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
