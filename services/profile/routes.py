from flask import request, jsonify, current_app
from models.database import db, User
from . import profile_bp

@profile_bp.route('/', methods=['GET'])
def get_profile():
    """Get user profile via API"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Import JWT functions from auth service
    from services.auth.jwt_utils import verify_jwt_token
    
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    user = User.query.get(payload['user_id'])
    if not user:
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
        'created_at': user.created_at.isoformat()
    }), 200

@profile_bp.route('/', methods=['PUT'])
def update_profile():
    """Update user profile via API"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Import JWT functions from auth service
    from services.auth.jwt_utils import verify_jwt_token
    
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    user = User.query.get(payload['user_id'])
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
        return jsonify({'error': 'Failed to update profile'}), 500

@profile_bp.route('/avatar', methods=['POST'])
def upload_avatar():
    """Upload user avatar"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Import JWT functions from auth service
    from services.auth.jwt_utils import verify_jwt_token
    
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if 'avatar' not in request.files:
        return jsonify({'error': 'No avatar file provided'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Simple file validation
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        # In a real app, you'd save the file and store the path
        # For now, we'll just return success
        return jsonify({
            'message': 'Avatar uploaded successfully',
            'avatar_url': f'/static/avatars/user_{user.id}.jpg'
        }), 200
    else:
        return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, GIF allowed'}), 400

@profile_bp.route('/health', methods=['GET'])
def health_check():
    """Profile Service health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'profile-service',
        'features': ['profile_management', 'avatar']
    }), 200