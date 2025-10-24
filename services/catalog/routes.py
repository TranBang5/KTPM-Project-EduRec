from flask import request, jsonify, current_app
from models.database import db, Course, Tutor, Material
from . import catalog_bp
from services.auth.jwt_utils import verify_jwt_token
import re

def validate_course_data(data):
    """Validate course data"""
    errors = []
    
    if not data.get('ten_khoa_hoc'):
        errors.append('Tên khóa học là bắt buộc')
    elif len(data['ten_khoa_hoc']) < 3:
        errors.append('Tên khóa học phải có ít nhất 3 ký tự')
    
    if not data.get('mon_hoc'):
        errors.append('Môn học là bắt buộc')
    
    if not data.get('khoi_lop'):
        errors.append('Khối lớp là bắt buộc')
    elif not isinstance(data['khoi_lop'], (int, list)):
        errors.append('Khối lớp phải là số hoặc danh sách số')
    
    if data.get('gia_tien') is not None:
        if not isinstance(data['gia_tien'], (int, float)) or data['gia_tien'] < 0:
            errors.append('Giá tiền phải là số dương')
    
    return errors

def validate_tutor_data(data):
    """Validate tutor data"""
    errors = []
    
    if not data.get('ten_gia_su'):
        errors.append('Tên gia sư là bắt buộc')
    elif len(data['ten_gia_su']) < 2:
        errors.append('Tên gia sư phải có ít nhất 2 ký tự')
    
    if not data.get('mon_hoc'):
        errors.append('Môn học là bắt buộc')
    
    if not data.get('khoi_lop'):
        errors.append('Khối lớp là bắt buộc')
    
    if data.get('so_dien_thoai'):
        phone_pattern = r'^[0-9+\-\s()]+$'
        if not re.match(phone_pattern, data['so_dien_thoai']):
            errors.append('Số điện thoại không hợp lệ')
    
    return errors

def validate_material_data(data):
    """Validate material data"""
    errors = []
    
    if not data.get('ten_tai_lieu'):
        errors.append('Tên tài liệu là bắt buộc')
    elif len(data['ten_tai_lieu']) < 3:
        errors.append('Tên tài liệu phải có ít nhất 3 ký tự')
    
    if not data.get('mon_hoc'):
        errors.append('Môn học là bắt buộc')
    
    if not data.get('khoi_lop'):
        errors.append('Khối lớp là bắt buộc')
    
    if not data.get('loai_tai_lieu'):
        errors.append('Loại tài liệu là bắt buộc')
    
    return errors

def apply_filters(query, model, filters):
    """Apply filters to query"""
    if filters.get('mon_hoc'):
        query = query.filter(model.mon_hoc.like(f'%{filters["mon_hoc"]}%'))
    
    if filters.get('khoi_lop'):
        if isinstance(filters['khoi_lop'], list):
            query = query.filter(model.khoi_lop.in_(filters['khoi_lop']))
        else:
            query = query.filter(model.khoi_lop == filters['khoi_lop'])
    
    if filters.get('search'):
        search_term = f'%{filters["search"]}%'
        if model == Course:
            query = query.filter(Course.ten_khoa_hoc.like(search_term))
        elif model == Tutor:
            query = query.filter(Tutor.ten_gia_su.like(search_term))
        elif model == Material:
            query = query.filter(Material.ten_tai_lieu.like(search_term))
    
    return query

# COURSE ENDPOINTS
@catalog_bp.route('/courses', methods=['GET'])
def get_courses():
    """Get courses with filtering and pagination"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 50)  # Limit max items per page
    
    # Get filters
    filters = {
        'mon_hoc': request.args.get('mon_hoc'),
        'khoi_lop': request.args.get('khoi_lop', type=int),
        'search': request.args.get('search')
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    # Build query
    query = Course.query
    query = apply_filters(query, Course, filters)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    courses = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'courses': [{
            'id': course.id,
            'ten_khoa_hoc': course.ten_khoa_hoc,
            'mon_hoc': course.mon_hoc,
            'khoi_lop': course.khoi_lop,
            'gia_tien': course.gia_tien,
            'trung_tam': course.trung_tam,
            'phuong_phap_hoc': course.phuong_phap_hoc
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

@catalog_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get specific course by ID"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    return jsonify({
        'id': course.id,
        'ten_khoa_hoc': course.ten_khoa_hoc,
        'mon_hoc': course.mon_hoc,
        'khoi_lop': course.khoi_lop,
        'gia_tien': course.gia_tien,
        'trung_tam': course.trung_tam,
        'phuong_phap_hoc': course.phuong_phap_hoc
    }), 200

@catalog_bp.route('/courses', methods=['POST'])
def create_course():
    """Create new course"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    
    # Validate data
    errors = validate_course_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        course = Course(
            ten_khoa_hoc=data['ten_khoa_hoc'],
            mon_hoc=data['mon_hoc'],
            khoi_lop=data['khoi_lop'],
            gia_tien=data.get('gia_tien'),
            trung_tam=data.get('trung_tam'),
            phuong_phap_hoc=data.get('phuong_phap_hoc')
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Course created successfully',
            'course': {
                'id': course.id,
                'ten_khoa_hoc': course.ten_khoa_hoc,
                'mon_hoc': course.mon_hoc,
                'khoi_lop': course.khoi_lop,
                'gia_tien': course.gia_tien,
                'trung_tam': course.trung_tam,
                'phuong_phap_hoc': course.phuong_phap_hoc
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create course'}), 500

@catalog_bp.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """Update course"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    data = request.get_json()
    
    # Validate data
    errors = validate_course_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        course.ten_khoa_hoc = data['ten_khoa_hoc']
        course.mon_hoc = data['mon_hoc']
        course.khoi_lop = data['khoi_lop']
        course.gia_tien = data.get('gia_tien')
        course.trung_tam = data.get('trung_tam')
        course.phuong_phap_hoc = data.get('phuong_phap_hoc')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Course updated successfully',
            'course': {
                'id': course.id,
                'ten_khoa_hoc': course.ten_khoa_hoc,
                'mon_hoc': course.mon_hoc,
                'khoi_lop': course.khoi_lop,
                'gia_tien': course.gia_tien,
                'trung_tam': course.trung_tam,
                'phuong_phap_hoc': course.phuong_phap_hoc
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update course'}), 500

@catalog_bp.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Delete course"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    try:
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({'message': 'Course deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete course'}), 500

# TUTOR ENDPOINTS
@catalog_bp.route('/tutors', methods=['GET'])
def get_tutors():
    """Get tutors with filtering and pagination"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 50)  # Limit max items per page
    
    # Get filters
    filters = {
        'mon_hoc': request.args.get('mon_hoc'),
        'khoi_lop': request.args.get('khoi_lop'),
        'search': request.args.get('search')
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    # Build query
    query = Tutor.query
    query = apply_filters(query, Tutor, filters)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    tutors = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'tutors': [{
            'id': tutor.id,
            'ten_gia_su': tutor.ten_gia_su,
            'mon_hoc': tutor.mon_hoc,
            'khoi_lop': tutor.khoi_lop,
            'so_dien_thoai': tutor.so_dien_thoai,
            'thoi_gian_day_hoc': tutor.thoi_gian_day_hoc
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

@catalog_bp.route('/tutors/<int:tutor_id>', methods=['GET'])
def get_tutor(tutor_id):
    """Get specific tutor by ID"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({'error': 'Tutor not found'}), 404
    
    return jsonify({
        'id': tutor.id,
        'ten_gia_su': tutor.ten_gia_su,
        'mon_hoc': tutor.mon_hoc,
        'khoi_lop': tutor.khoi_lop,
        'so_dien_thoai': tutor.so_dien_thoai,
        'thoi_gian_day_hoc': tutor.thoi_gian_day_hoc
    }), 200

@catalog_bp.route('/tutors', methods=['POST'])
def create_tutor():
    """Create new tutor"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    
    # Validate data
    errors = validate_tutor_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        tutor = Tutor(
            ten_gia_su=data['ten_gia_su'],
            mon_hoc=data['mon_hoc'],
            khoi_lop=data['khoi_lop'],
            so_dien_thoai=data.get('so_dien_thoai'),
            thoi_gian_day_hoc=data.get('thoi_gian_day_hoc')
        )
        
        db.session.add(tutor)
        db.session.commit()
        
        return jsonify({
            'message': 'Tutor created successfully',
            'tutor': {
                'id': tutor.id,
                'ten_gia_su': tutor.ten_gia_su,
                'mon_hoc': tutor.mon_hoc,
                'khoi_lop': tutor.khoi_lop,
                'so_dien_thoai': tutor.so_dien_thoai,
                'thoi_gian_day_hoc': tutor.thoi_gian_day_hoc
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create tutor'}), 500

@catalog_bp.route('/tutors/<int:tutor_id>', methods=['PUT'])
def update_tutor(tutor_id):
    """Update tutor"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({'error': 'Tutor not found'}), 404
    
    data = request.get_json()
    
    # Validate data
    errors = validate_tutor_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        tutor.ten_gia_su = data['ten_gia_su']
        tutor.mon_hoc = data['mon_hoc']
        tutor.khoi_lop = data['khoi_lop']
        tutor.so_dien_thoai = data.get('so_dien_thoai')
        tutor.thoi_gian_day_hoc = data.get('thoi_gian_day_hoc')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tutor updated successfully',
            'tutor': {
                'id': tutor.id,
                'ten_gia_su': tutor.ten_gia_su,
                'mon_hoc': tutor.mon_hoc,
                'khoi_lop': tutor.khoi_lop,
                'so_dien_thoai': tutor.so_dien_thoai,
                'thoi_gian_day_hoc': tutor.thoi_gian_day_hoc
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update tutor'}), 500

@catalog_bp.route('/tutors/<int:tutor_id>', methods=['DELETE'])
def delete_tutor(tutor_id):
    """Delete tutor"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    tutor = Tutor.query.get(tutor_id)
    if not tutor:
        return jsonify({'error': 'Tutor not found'}), 404
    
    try:
        db.session.delete(tutor)
        db.session.commit()
        
        return jsonify({'message': 'Tutor deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete tutor'}), 500

# MATERIAL ENDPOINTS
@catalog_bp.route('/materials', methods=['GET'])
def get_materials():
    """Get materials with filtering and pagination"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 50)  # Limit max items per page
    
    # Get filters
    filters = {
        'mon_hoc': request.args.get('mon_hoc'),
        'khoi_lop': request.args.get('khoi_lop'),
        'loai_tai_lieu': request.args.get('loai_tai_lieu'),
        'search': request.args.get('search')
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    # Build query
    query = Material.query
    query = apply_filters(query, Material, filters)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    materials = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    return jsonify({
        'materials': [{
            'id': material.id,
            'ten_tai_lieu': material.ten_tai_lieu,
            'mon_hoc': material.mon_hoc,
            'khoi_lop': material.khoi_lop,
            'loai_tai_lieu': material.loai_tai_lieu
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

@catalog_bp.route('/materials/<int:material_id>', methods=['GET'])
def get_material(material_id):
    """Get specific material by ID"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    return jsonify({
        'id': material.id,
        'ten_tai_lieu': material.ten_tai_lieu,
        'mon_hoc': material.mon_hoc,
        'khoi_lop': material.khoi_lop,
        'loai_tai_lieu': material.loai_tai_lieu
    }), 200

@catalog_bp.route('/materials', methods=['POST'])
def create_material():
    """Create new material"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    
    # Validate data
    errors = validate_material_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        material = Material(
            ten_tai_lieu=data['ten_tai_lieu'],
            mon_hoc=data['mon_hoc'],
            khoi_lop=data['khoi_lop'],
            loai_tai_lieu=data['loai_tai_lieu']
        )
        
        db.session.add(material)
        db.session.commit()
        
        return jsonify({
            'message': 'Material created successfully',
            'material': {
                'id': material.id,
                'ten_tai_lieu': material.ten_tai_lieu,
                'mon_hoc': material.mon_hoc,
                'khoi_lop': material.khoi_lop,
                'loai_tai_lieu': material.loai_tai_lieu
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create material'}), 500

@catalog_bp.route('/materials/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    """Update material"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    data = request.get_json()
    
    # Validate data
    errors = validate_material_data(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    try:
        material.ten_tai_lieu = data['ten_tai_lieu']
        material.mon_hoc = data['mon_hoc']
        material.khoi_lop = data['khoi_lop']
        material.loai_tai_lieu = data['loai_tai_lieu']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Material updated successfully',
            'material': {
                'id': material.id,
                'ten_tai_lieu': material.ten_tai_lieu,
                'mon_hoc': material.mon_hoc,
                'khoi_lop': material.khoi_lop,
                'loai_tai_lieu': material.loai_tai_lieu
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update material'}), 500

@catalog_bp.route('/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    """Delete material"""
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Authorization header missing'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    if not payload or payload.get('type') != 'access':
        return jsonify({'error': 'Invalid token'}), 401
    
    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    try:
        db.session.delete(material)
        db.session.commit()
        
        return jsonify({'message': 'Material deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete material'}), 500

# HEALTH CHECK
@catalog_bp.route('/health', methods=['GET'])
def health_check():
    """Catalog Service health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'catalog-service',
        'features': ['course_management', 'tutor_management', 'material_management', 'filtering', 'pagination', 'validation']
    }), 200
