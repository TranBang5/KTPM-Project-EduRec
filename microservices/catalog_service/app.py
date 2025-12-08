from flask import Flask, request, jsonify
from models import db, Course, Tutor, Material
import os
import sys
import re
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@catalog-db:3306/catalog_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database connection pooling for better performance
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 20,  # Increased for high load
    'pool_recycle': 3600,  # Recycle connections after 1 hour
    'pool_pre_ping': True,  # Verify connections before using
    'max_overflow': 40,  # Increased for burst traffic
    'pool_timeout': 30,  # Timeout for getting connection from pool
    'connect_args': {
        'connect_timeout': 10,
        'read_timeout': 20,
        'write_timeout': 20
    },
    'execution_options': {
        'isolation_level': 'READ COMMITTED'  # Reduce lock contention
    }
}

# Auth service URL for token verification
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5004')

# Initialize database
db.init_app(app)

# Ensure database sessions are properly cleaned up after each request
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Clean up database session after each request"""
    db.session.remove()

def verify_token_with_auth_service(token):
    """Verify JWT token with auth service with retry logic"""
    max_retries = 2
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/auth/verify-token",
                json={'token': token},
                timeout=20  # Increased timeout to handle slow auth service
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code >= 500:
                # Server error, retry
                if attempt < max_retries - 1:
                    logger.warning(f"Auth service returned {response.status_code}, retrying...")
                    import time
                    time.sleep(retry_delay)
                    continue
            return None
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                logger.warning(f"Token verification timeout (attempt {attempt + 1}), retrying...")
                import time
                time.sleep(retry_delay)
                continue
            logger.error(f"Token verification timeout after {max_retries} attempts: {str(e)}")
            return None
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Auth service connection error (attempt {attempt + 1}), retrying...")
                import time
                time.sleep(retry_delay)
                continue
            logger.error(f"Auth service connection error after {max_retries} attempts: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
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
        
        # Store user info in request context
        request.current_user_id = payload.get('user_id')
        return f(*args, **kwargs)
    
    return decorated_function

def validate_course_data(data):
    """Validate course data"""
    errors = []
    
    if not data.get('name'):
        errors.append('Tên khóa học là bắt buộc')
    elif len(data['name']) < 3:
        errors.append('Tên khóa học phải có ít nhất 3 ký tự')
    
    if not data.get('subject'):
        errors.append('Môn học là bắt buộc')
    
    if not data.get('grade_level'):
        errors.append('Khối lớp là bắt buộc')
    
    if data.get('cost') is not None:
        if not isinstance(data['cost'], (int, float)) or data['cost'] < 0:
            errors.append('Giá tiền phải là số dương')
    
    return errors

def validate_tutor_data(data):
    """Validate tutor data"""
    errors = []
    
    if not data.get('name'):
        errors.append('Tên gia sư là bắt buộc')
    elif len(data['name']) < 2:
        errors.append('Tên gia sư phải có ít nhất 2 ký tự')
    
    if not data.get('subject'):
        errors.append('Môn học là bắt buộc')
    
    if not data.get('specialized_grade'):
        errors.append('Khối lớp là bắt buộc')
    
    return errors

def validate_material_data(data):
    """Validate material data"""
    errors = []
    
    if not data.get('name'):
        errors.append('Tên tài liệu là bắt buộc')
    elif len(data['name']) < 3:
        errors.append('Tên tài liệu phải có ít nhất 3 ký tự')
    
    if not data.get('subject'):
        errors.append('Môn học là bắt buộc')
    
    if not data.get('grade_level'):
        errors.append('Khối lớp là bắt buộc')
    
    return errors

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for catalog service"""
    return jsonify({
        'service': 'catalog-service',
        'status': 'running',
        'description': 'Catalog Service for managing courses, tutors, and materials',
        'available_endpoints': {
            'health': '/health',
            'courses': '/catalog/courses (GET, POST)',
            'course_detail': '/catalog/courses/<id> (GET, PUT, DELETE)',
            'tutors': '/catalog/tutors (GET)',
            'tutor_detail': '/catalog/tutors/<id> (GET)',
            'materials': '/catalog/materials (GET)',
            'material_detail': '/catalog/materials/<id> (GET)',
            'search': '/catalog/search (GET)'
        },
        'features': ['course_management', 'tutor_management', 'material_management']
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'catalog-service',
        'features': ['course_management', 'tutor_management', 'material_management']
    }), 200

# COURSE ENDPOINTS
@app.route('/catalog/courses', methods=['GET'])
@require_auth
def get_courses():
    """Get courses with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50)
        
        # Get filters
        filters = {
            'subject': request.args.get('subject'),
            'grade_level': request.args.get('grade_level'),
            'search': request.args.get('search')
        }
        
        # Build query with error handling
        try:
            query = Course.query
            
            if filters['subject']:
                query = query.filter(Course.subject.like(f"%{filters['subject']}%"))
            if filters['grade_level']:
                query = query.filter(Course.grade_level.like(f"%{filters['grade_level']}%"))
            if filters['search']:
                query = query.filter(Course.name.like(f"%{filters['search']}%"))
            
            # Get total count with timeout handling
            try:
                total = query.count()
            except Exception as count_error:
                logger.error(f"Error counting courses: {str(count_error)}")
                total = 0
            
            # Apply pagination with error handling
            try:
                courses = query.paginate(page=page, per_page=per_page, error_out=False)
            except Exception as pagination_error:
                logger.error(f"Error paginating courses: {str(pagination_error)}")
                return jsonify({'error': 'Failed to retrieve courses'}), 500
            
            return jsonify({
                'courses': [{
                    'id': course.id,
                    'name': course.name,
                    'subject': course.subject,
                    'grade_level': course.grade_level,
                    'cost': course.cost,
                    'teaching_method': course.teaching_method,
                    'teaching_time': course.teaching_time,
                    'location': course.location
                } for course in courses.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': courses.pages,
                    'has_next': courses.has_next,
                    'has_prev': courses.has_prev
                }
            }), 200
        except Exception as query_error:
            logger.error(f"Database query error: {str(query_error)}")
            return jsonify({'error': 'Failed to retrieve courses'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_courses: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/catalog/courses/<int:course_id>', methods=['GET'])
@require_auth
def get_course(course_id):
    """Get specific course by ID"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    return jsonify({
        'id': course.id,
        'name': course.name,
        'subject': course.subject,
        'grade_level': course.grade_level,
        'cost': course.cost,
        'teaching_method': course.teaching_method,
        'teaching_time': course.teaching_time,
        'location': course.location
    }), 200

@app.route('/catalog/courses', methods=['POST'])
@require_auth
def create_course():
    """Create new course"""
    data = request.get_json()
    
    errors = validate_course_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        course = Course(
            name=data['name'],
            subject=data['subject'],
            grade_level=data['grade_level'],
            cost=data.get('cost'),
            teaching_method=data.get('teaching_method'),
            teaching_time=data.get('teaching_time'),
            location=data.get('location')
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Course created successfully',
            'course': {
                'id': course.id,
                'name': course.name,
                'subject': course.subject,
                'grade_level': course.grade_level
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating course: {str(e)}")
        return jsonify({'error': 'Failed to create course'}), 500

@app.route('/catalog/courses/<int:course_id>', methods=['PUT'])
@require_auth
def update_course(course_id):
    """Update course"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    data = request.get_json()
    errors = validate_course_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        course.name = data['name']
        course.subject = data['subject']
        course.grade_level = data['grade_level']
        course.cost = data.get('cost')
        course.teaching_method = data.get('teaching_method')
        course.teaching_time = data.get('teaching_time')
        course.location = data.get('location')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Course updated successfully',
            'course': {
                'id': course.id,
                'name': course.name,
                'subject': course.subject,
                'grade_level': course.grade_level
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating course: {str(e)}")
        return jsonify({'error': 'Failed to update course'}), 500

@app.route('/catalog/courses/<int:course_id>', methods=['DELETE'])
@require_auth
def delete_course(course_id):
    """Delete course"""
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    try:
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': 'Course deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting course: {str(e)}")
        return jsonify({'error': 'Failed to delete course'}), 500

# TUTOR ENDPOINTS
@app.route('/catalog/tutors', methods=['GET'])
@require_auth
def get_tutors():
    """Get tutors with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50)
        
        filters = {
            'subject': request.args.get('subject'),
            'grade': request.args.get('grade'),
            'search': request.args.get('search')
        }
        
        try:
            query = Tutor.query
            
            if filters['subject']:
                query = query.filter(Tutor.subject.like(f"%{filters['subject']}%"))
            if filters['grade']:
                query = query.filter(Tutor.specialized_grade.like(f"%{filters['grade']}%"))
            if filters['search']:
                query = query.filter(Tutor.name.like(f"%{filters['search']}%"))
            
            try:
                total = query.count()
            except Exception as count_error:
                logger.error(f"Error counting tutors: {str(count_error)}")
                total = 0
            
            tutors = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return jsonify({
                'tutors': [{
                    'id': tutor.id,
                    'name': tutor.name,
                    'subject': tutor.subject,
                    'specialized_grade': tutor.specialized_grade,
                    'teaching_method': tutor.teaching_method,
                    'teaching_time': tutor.teaching_time,
                    'experience': tutor.experience
                } for tutor in tutors.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': tutors.pages,
                    'has_next': tutors.has_next,
                    'has_prev': tutors.has_prev
                }
            }), 200
        except Exception as query_error:
            logger.error(f"Database query error: {str(query_error)}")
            return jsonify({'error': 'Failed to retrieve tutors'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_tutors: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/catalog/tutors/<int:tutor_id>', methods=['GET'])
@require_auth
def get_tutor(tutor_id):
    """Get specific tutor by ID"""
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({'error': 'Tutor not found'}), 404
    
    return jsonify({
        'id': tutor.id,
        'name': tutor.name,
        'subject': tutor.subject,
        'specialized_grade': tutor.specialized_grade,
        'teaching_method': tutor.teaching_method,
        'teaching_time': tutor.teaching_time,
        'experience': tutor.experience
    }), 200

# Similar endpoints for tutors and materials (POST, PUT, DELETE) - abbreviated for space
# MATERIAL ENDPOINTS
@app.route('/catalog/materials', methods=['GET'])
@require_auth
def get_materials():
    """Get materials with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50)
        
        filters = {
            'subject': request.args.get('subject'),
            'grade_level': request.args.get('grade_level'),
            'material_type': request.args.get('material_type'),
            'search': request.args.get('search')
        }
        
        try:
            query = Material.query
            
            if filters['subject']:
                query = query.filter(Material.subject.like(f"%{filters['subject']}%"))
            if filters['grade_level']:
                query = query.filter(Material.grade_level.like(f"%{filters['grade_level']}%"))
            if filters['material_type']:
                query = query.filter(Material.material_type.like(f"%{filters['material_type']}%"))
            if filters['search']:
                query = query.filter(Material.name.like(f"%{filters['search']}%"))
            
            try:
                total = query.count()
            except Exception as count_error:
                logger.error(f"Error counting materials: {str(count_error)}")
                total = 0
            
            materials = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return jsonify({
                'materials': [{
                    'id': material.id,
                    'name': material.name,
                    'subject': material.subject,
                    'grade_level': material.grade_level,
                    'material_type': material.material_type,
                    'description': material.description
                } for material in materials.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': materials.pages,
                    'has_next': materials.has_next,
                    'has_prev': materials.has_prev
                }
            }), 200
        except Exception as query_error:
            logger.error(f"Database query error: {str(query_error)}")
            return jsonify({'error': 'Failed to retrieve materials'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_materials: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/catalog/materials/<int:material_id>', methods=['GET'])
@require_auth
def get_material(material_id):
    """Get specific material by ID"""
    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    return jsonify({
        'id': material.id,
        'name': material.name,
        'subject': material.subject,
        'grade_level': material.grade_level,
        'material_type': material.material_type,
        'description': material.description
    }), 200

@app.route('/catalog/search', methods=['GET'])
@require_auth
def search_all():
    """Search across courses, tutors, and materials"""
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({'error': 'Search term is required'}), 400
    
    courses = Course.query.filter(Course.name.like(f"%{search_term}%")).limit(10).all()
    tutors = Tutor.query.filter(Tutor.name.like(f"%{search_term}%")).limit(10).all()
    materials = Material.query.filter(Material.name.like(f"%{search_term}%")).limit(10).all()
    
    return jsonify({
        'courses': [{'id': c.id, 'name': c.name, 'subject': c.subject} for c in courses],
        'tutors': [{'id': t.id, 'name': t.name, 'subject': t.subject} for t in tutors],
        'materials': [{'id': m.id, 'name': m.name, 'subject': m.subject} for m in materials]
    }), 200

if __name__ == '__main__':
    try:
        logger.info("Initializing Catalog Service...")
        with app.app_context():
            try:
                db.create_all()
                logger.info("Database tables created/verified successfully")
            except Exception as db_error:
                logger.warning(f"Database initialization warning: {str(db_error)}")
                logger.info("Service will continue to start. Database connection will be established on first request.")
        
        logger.info(f"Catalog Service starting on port 5005")
        logger.info(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")
        logger.info(f"Auth Service URL: {AUTH_SERVICE_URL}")
        
        # Disable debug mode in Docker to prevent auto-restart
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(host='0.0.0.0', port=5005, debug=debug_mode)
    except Exception as e:
        logger.error(f"Failed to start Catalog Service: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
