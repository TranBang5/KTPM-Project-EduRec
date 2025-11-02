from flask import Flask, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db, User
from datetime import datetime, timedelta
import jwt
import secrets
import string
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://user:password@db:3306/recommendation_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize database
db.init_app(app)

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

def generate_jwt_token(user_id, token_type='access'):
    """Generate JWT token"""
    if token_type == 'access':
        expires = datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
    else:  # refresh
        expires = datetime.utcnow() + app.config['JWT_REFRESH_TOKEN_EXPIRES']
    
    payload = {
        'user_id': user_id,
        'type': token_type,
        'exp': expires,
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_reset_token():
    """Generate secure reset token"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def send_reset_email(email, reset_token):
    """Send password reset email"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured, skipping email send")
            return True  # Return True for development
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "Password Reset Request"
        
        reset_url = f"http://localhost:5000/auth/reset-password?token={reset_token}"
        body = f"""
        You have requested to reset your password.
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        If you didn't request this, please ignore this email.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, email, text)
        server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for auth service"""
    return jsonify({
        'service': 'auth-service',
        'status': 'running',
        'description': 'Authentication Service for user registration, login, and JWT token management',
        'available_endpoints': {
            'health': '/health',
            'register': '/auth/register (POST)',
            'login': '/auth/login (POST)',
            'refresh': '/auth/refresh (POST)',
            'forgot_password': '/auth/forgot-password (POST)',
            'reset_password': '/auth/reset-password (POST)',
            'verify_token': '/auth/verify-token (POST)',
            'profile': '/auth/profile (GET, PUT)'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'auth-service'}), 200

@app.route('/auth/register', methods=['POST'])
def register():
    """User registration"""
    data = request.get_json()
    
    required_fields = ['email', 'password', 'full_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new user
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(
        email=data['email'],
        full_name=data['full_name'],
        password_hash=hashed_password,
        school=data.get('school'),
        current_grade=data.get('current_grade'),
        learning_goals=data.get('learning_goals'),
        favorite_subjects=data.get('favorite_subjects'),
        preferred_learning_method=data.get('preferred_learning_method')
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT tokens
        access_token = generate_jwt_token(new_user.id, 'access')
        refresh_token = generate_jwt_token(new_user.id, 'refresh')
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'full_name': new_user.full_name
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Generate JWT tokens
    access_token = generate_jwt_token(user.id, 'access')
    refresh_token = generate_jwt_token(user.id, 'refresh')
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name
        }
    }), 200

@app.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token is required'}), 400
    
    # Verify refresh token
    payload = verify_jwt_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        return jsonify({'error': 'Invalid refresh token'}), 401
    
    # Generate new access token
    new_access_token = generate_jwt_token(payload['user_id'], 'access')
    
    return jsonify({
        'access_token': new_access_token
    }), 200

@app.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal if email exists or not
        return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
    
    # Generate reset token
    reset_token = generate_reset_token()
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    # Send email
    if send_reset_email(email, reset_token):
        return jsonify({'message': 'Password reset email sent'}), 200
    else:
        return jsonify({'error': 'Failed to send reset email'}), 500

@app.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expires < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    # Update password
    user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200

@app.route('/auth/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token is required'}), 400
    
    payload = verify_jwt_token(token)
    if not payload:
        return jsonify({'error': 'Invalid token'}), 401
    
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    return jsonify({
        'valid': True,
        'user_id': payload['user_id'],
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name
        }
    }), 200

@app.route('/auth/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
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
        'learning_goals': user.learning_goals,
        'favorite_subjects': user.favorite_subjects,
        'preferred_learning_method': user.preferred_learning_method,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }), 200

@app.route('/auth/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
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
    if 'learning_goals' in data:
        user.learning_goals = data['learning_goals']
    if 'favorite_subjects' in data:
        user.favorite_subjects = data['favorite_subjects']
    if 'preferred_learning_method' in data:
        user.preferred_learning_method = data['preferred_learning_method']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

if __name__ == '__main__':
    try:
        logger.info("Initializing Auth Service...")
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created/verified successfully")
            except Exception as db_error:
                logger.warning(f"Database initialization warning: {str(db_error)}")
                logger.info("Service will continue to start. Database connection will be established on first request.")
        
        logger.info(f"Auth Service starting on port 5004")
        logger.info(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")
        
        # Disable debug mode in Docker to prevent auto-restart
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(host='0.0.0.0', port=5004, debug=debug_mode)
    except Exception as e:
        logger.error(f"Failed to start Auth Service: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
