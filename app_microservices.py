from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import requests
import os
import json
import logging
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# API Gateway URL - single entry point
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://localhost:5000')

# Helper function to get current user info from session
def get_current_user():
    """Get current user info from session (cached, no API call)"""
    if 'access_token' not in session:
        return None
    
    # Get user info from session (cached when logged in)
    user_data = session.get('user_data', {})
    user_id = session.get('user_id')
    
    if not user_id:
        return None
    
    # Create a simple object-like dict for template usage
    user = type('User', (), {
        'id': user_id,
        'full_name': user_data.get('full_name', 'User'),
        'email': user_data.get('email', ''),
        'is_authenticated': True,
        **user_data  # Include any other user data from session
    })()
    return user

# Context processor to inject current_user into all templates
@app.context_processor
def inject_current_user():
    """Make current_user available in all templates"""
    return dict(current_user=get_current_user())

# Helper function to call API Gateway
def call_api_gateway(endpoint, method='GET', data=None, params=None, headers=None):
    """Call API Gateway endpoint"""
    try:
        url = f"{API_GATEWAY_URL}{endpoint}"
        request_headers = headers or {}
        
        # Add session token if available
        if 'access_token' in session:
            request_headers['Authorization'] = f"Bearer {session['access_token']}"
        
        if method == 'GET':
            response = requests.get(url, params=params, headers=request_headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=request_headers, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=request_headers, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=request_headers, timeout=30)
        
        if response.status_code < 400:
            return response.json(), response.status_code
        else:
            error_data = response.json() if response.content else {'error': 'Unknown error'}
            return error_data, response.status_code
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error: API Gateway at {API_GATEWAY_URL} is not available")
        return {'error': 'Microservices are not available. Please ensure Docker Compose is running.'}, 503
    except Exception as e:
        logger.error(f"Error calling API Gateway {endpoint}: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/')
def index():
    if 'access_token' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for frontend"""
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append({
                'rule': rule.rule,
                'endpoint': rule.endpoint,
                'methods': list(rule.methods)
            })
    return jsonify({
        'status': 'healthy',
        'service': 'frontend',
        'registered_routes': routes
    }), 200

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = {
            'email': request.form['email'],
            'password': request.form['password'],
            'full_name': request.form['full_name'],
            'school': request.form.get('school'),
            'current_grade': request.form.get('current_grade'),
            'learning_goals': request.form.get('learning_goals'),
            'favorite_subjects': request.form.get('favorite_subjects'),
            'preferred_learning_method': request.form.get('preferred_learning_method')
        }
        
        response_data, status_code = call_api_gateway('/auth/register', 'POST', user_data)
        
        if status_code == 201:
            # Store tokens and user info in session
            user_info = response_data.get('user', {})
            session['access_token'] = response_data.get('access_token')
            session['refresh_token'] = response_data.get('refresh_token')
            session['user_id'] = user_info.get('id')
            # Cache user data for template usage
            session['user_data'] = {
                'id': user_info.get('id'),
                'full_name': user_info.get('full_name', user_data.get('full_name', 'User')),
                'email': user_info.get('email', user_data.get('email', ''))
            }
            flash('Registration successful!')
            return redirect(url_for('dashboard'))
        else:
            flash(response_data.get('error', 'Registration failed'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_data = {
            'email': request.form['email'],
            'password': request.form['password']
        }
        
        response_data, status_code = call_api_gateway('/auth/login', 'POST', login_data)
        
        if status_code == 200:
            # Store tokens and user info in session
            user_info = response_data.get('user', {})
            session['access_token'] = response_data.get('access_token')
            session['refresh_token'] = response_data.get('refresh_token')
            session['user_id'] = user_info.get('id')
            # Cache user data for template usage
            session['user_data'] = {
                'id': user_info.get('id'),
                'full_name': user_info.get('full_name', 'User'),
                'email': user_info.get('email', login_data.get('email', ''))
            }
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash(response_data.get('error', 'Invalid email or password'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'access_token' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        profile_data = {
            'school': request.form.get('school'),
            'current_grade': request.form.get('current_grade'),
            'favorite_subjects': request.form.get('favorite_subjects'),
            'learning_goals': request.form.get('learning_goals'),
            'preferred_learning_method': request.form.get('preferred_learning_method')
        }
        
        response_data, status_code = call_api_gateway(f'/profiles/{user_id}', 'PUT', profile_data)
        
        if status_code == 200:
            flash('Profile updated successfully')
        else:
            flash(response_data.get('error', 'Failed to update profile'))
    
    # Get current profile
    response_data, status_code = call_api_gateway(f'/profiles/{user_id}', 'GET')
    
    if status_code == 200:
        user = response_data
        # Update cached user data in session
        if 'user_data' in session:
            session['user_data'].update({
                'full_name': user.get('full_name', session['user_data'].get('full_name', 'User')),
                'email': user.get('email', session['user_data'].get('email', ''))
            })
        else:
            session['user_data'] = {
                'id': user_id,
                'full_name': user.get('full_name', 'User'),
                'email': user.get('email', '')
            }
    elif status_code == 404:
        # If profile not found, try to get from auth service directly
        logger.warning(f"Profile not found for user {user_id}, trying Auth Service...")
        auth_response, auth_status = call_api_gateway('/auth/profile', 'GET')
        if auth_status == 200:
            user = auth_response
            # Update session cache
            if 'user_data' in session:
                session['user_data'].update({
                    'full_name': user.get('full_name', session['user_data'].get('full_name', 'User')),
                    'email': user.get('email', session['user_data'].get('email', ''))
                })
            else:
                session['user_data'] = {
                    'id': user_id,
                    'full_name': user.get('full_name', 'User'),
                    'email': user.get('email', '')
                }
        else:
            flash('Failed to load profile. Please try again or complete your profile.')
            user = {}
    else:
        flash(f'Failed to load profile: {response_data.get("error", "Unknown error")}')
        user = {}
    
    return render_template('profile.html', user=user)

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    if 'access_token' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Get user profile first
    profile_response, profile_status = call_api_gateway(f'/profiles/{user_id}', 'GET')
    
    if profile_status != 200 or not all([
        profile_response.get('school'),
        profile_response.get('current_grade'),
        profile_response.get('favorite_subjects'),
        profile_response.get('learning_goals')
    ]):
        flash('Vui lòng hoàn thành hồ sơ của bạn trước khi xem đề xuất')
        return redirect(url_for('profile'))
    
    # Prepare user data for recommendation service
    user_data = {
        'school': profile_response.get('school'),
        'current_grade': profile_response.get('current_grade'),
        'learning_goals': profile_response.get('learning_goals'),
        'favorite_subjects': profile_response.get('favorite_subjects'),
        'preferred_learning_method': profile_response.get('preferred_learning_method')
    }
    
    try:
        # Call recommendation service through API Gateway
        response_data, status_code = call_api_gateway('/recommendations/generate', 'POST', user_data)
        
        if status_code != 200:
            flash(f'Lỗi khi tạo đề xuất: {response_data.get("error", "Unknown error")}')
            return redirect(url_for('profile'))
        
        # Process recommendations and fetch full item details from catalog service
        recommendations_data = response_data.get('recommendations', {})
        
        # Get active tab and filters
        active_tab = request.args.get('tab', 'courses')
        filters = {
            'subject': request.args.get('subject', ''),
            'grade': request.args.get('grade', ''),
            'method': request.args.get('method', '')
        }
        
        # Fetch full item details from catalog service
        recommendations = {
            'courses': [],
            'tutors': [],
            'materials': []
        }
        
        # Fetch course details
        course_ids = [item.get('id', '').replace('course_', '') for item in recommendations_data.get('courses', [])]
        for course_item in recommendations_data.get('courses', []):
            course_id = course_item.get('id', '').replace('course_', '')
            if course_id and course_id.isdigit():
                try:
                    catalog_response, catalog_status = call_api_gateway(f'/catalog/courses/{course_id}', 'GET')
                    if catalog_status == 200:
                        course_detail = catalog_response.copy()
                        course_detail['score'] = course_item.get('score', 0)
                        recommendations['courses'].append(course_detail)
                    else:
                        # If catalog service fails, use minimal info
                        recommendations['courses'].append({
                            'id': course_id,
                            'name': f"Course {course_id}",
                            'score': course_item.get('score', 0)
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch course {course_id}: {str(e)}")
                    recommendations['courses'].append({
                        'id': course_id,
                        'name': f"Course {course_id}",
                        'score': course_item.get('score', 0)
                    })
        
        # Fetch tutor details
        for tutor_item in recommendations_data.get('tutors', []):
            tutor_id = tutor_item.get('id', '').replace('tutor_', '')
            if tutor_id and tutor_id.isdigit():
                try:
                    catalog_response, catalog_status = call_api_gateway(f'/catalog/tutors/{tutor_id}', 'GET')
                    if catalog_status == 200:
                        tutor_detail = catalog_response.copy()
                        tutor_detail['score'] = tutor_item.get('score', 0)
                        recommendations['tutors'].append(tutor_detail)
                    else:
                        recommendations['tutors'].append({
                            'id': tutor_id,
                            'name': f"Tutor {tutor_id}",
                            'score': tutor_item.get('score', 0)
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch tutor {tutor_id}: {str(e)}")
                    recommendations['tutors'].append({
                        'id': tutor_id,
                        'name': f"Tutor {tutor_id}",
                        'score': tutor_item.get('score', 0)
                    })
        
        # Fetch material details
        for material_item in recommendations_data.get('materials', []):
            material_id = material_item.get('id', '').replace('material_', '')
            if material_id and material_id.isdigit():
                try:
                    catalog_response, catalog_status = call_api_gateway(f'/catalog/materials/{material_id}', 'GET')
                    if catalog_status == 200:
                        material_detail = catalog_response.copy()
                        material_detail['score'] = material_item.get('score', 0)
                        recommendations['materials'].append(material_detail)
                    else:
                        recommendations['materials'].append({
                            'id': material_id,
                            'name': f"Material {material_id}",
                            'score': material_item.get('score', 0)
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch material {material_id}: {str(e)}")
                    recommendations['materials'].append({
                        'id': material_id,
                        'name': f"Material {material_id}",
                        'score': material_item.get('score', 0)
                    })
        
        if request.method == 'POST':
            return render_template('_recommendations.html', 
                                 recommendations=recommendations,
                                 active_tab=active_tab)
        
        return render_template('recommendations.html', 
                             recommendations=recommendations,
                             active_tab=active_tab,
                             all_subjects=[],
                             all_grades=[],
                             all_methods=[])
    
    except Exception as e:
        logger.error(f"Error in recommendations: {str(e)}")
        flash(f'Lỗi khi tạo đề xuất: {str(e)}')
        return redirect(url_for('profile'))

@app.route('/study_plan', methods=['GET', 'POST'])
def study_plan():
    if 'access_token' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Get or create study plan
    logger.info(f"Loading study plan for user {user_id}")
    response_data, status_code = call_api_gateway(f'/study-plans/{user_id}', 'GET')
    
    if status_code == 404:
        # Create new study plan
        logger.info(f"Study plan not found for user {user_id}, creating new one")
        create_data = {'user_id': user_id}
        response_data, status_code = call_api_gateway('/study-plans', 'POST', create_data)
    
    if status_code not in [200, 201]:
        error_message = response_data.get('error', 'Unknown error')
        logger.error(f"Failed to load study plan for user {user_id}: {error_message} (status: {status_code})")
        flash(f'Lỗi khi tải kế hoạch học tập: {error_message}')
        return redirect(url_for('dashboard'))
    
    logger.info(f"Successfully loaded study plan for user {user_id}")
    
    study_plan_data = response_data.get('study_plan', {})
    study_plan_items = response_data.get('items', [])
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_item':
            item_data = {
                'user_id': user_id,
                'item_type': request.form.get('item_type'),
                'item_id': request.form.get('item_id'),
                'name': request.form.get('name'),
                'subject': request.form.get('subject'),
                'grade': request.form.get('grade'),
                'method': request.form.get('method'),
                'time_slots': request.form.get('time_slots')
            }
            
            response_data, status_code = call_api_gateway(f'/study-plans/{user_id}/items', 'POST', item_data)
            
            if status_code == 201:
                flash('Đã thêm vào kế hoạch học tập')
            else:
                flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
        
        elif action == 'add_course':
            # Update time_slot for an existing course item
            course_id = request.form.get('course_id')
            time_slot = request.form.get('time_slot')
            
            if not course_id or not time_slot:
                flash('Vui lòng chọn trung tâm và nhập thời gian')
            else:
                # Find the item by item_id
                item = next((item for item in study_plan_items if item.get('item_id') == course_id and item.get('item_type') == 'course'), None)
                if item:
                    # Update time_slots for the item
                    update_data = {'time_slots': time_slot}
                    response_data, status_code = call_api_gateway(f'/study-plans/{user_id}/items/{item["id"]}', 'PUT', update_data)
                    
                    if status_code == 200:
                        flash('Đã thêm vào thời khóa biểu')
                    else:
                        flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
                else:
                    flash('Không tìm thấy trung tâm trong kế hoạch học tập')
        
        elif action == 'add_tutor':
            # Update selected_time_slot for an existing tutor item
            tutor_id = request.form.get('tutor_id')
            selected_time_slot = request.form.get('selected_time_slot')
            
            if not tutor_id or not selected_time_slot:
                flash('Vui lòng chọn gia sư và thời gian')
            else:
                # Find the item by item_id
                item = next((item for item in study_plan_items if item.get('item_id') == tutor_id and item.get('item_type') == 'tutor'), None)
                if item:
                    # Update time_slots for the item
                    update_data = {'time_slots': selected_time_slot}
                    response_data, status_code = call_api_gateway(f'/study-plans/{user_id}/items/{item["id"]}', 'PUT', update_data)
                    
                    if status_code == 200:
                        flash('Đã thêm vào thời khóa biểu')
                    else:
                        flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
                else:
                    flash('Không tìm thấy gia sư trong kế hoạch học tập')
        
        elif action == 'add_material':
            # Update time_slots for an existing material item
            material_id = request.form.get('material_id')
            time_slots_json = request.form.get('time_slots')
            
            if not material_id or not time_slots_json:
                flash('Vui lòng chọn tài liệu và nhập thời gian')
            else:
                # Find the item by item_id
                item = next((item for item in study_plan_items if item.get('item_id') == material_id and item.get('item_type') == 'material'), None)
                if item:
                    # Update time_slots for the item
                    update_data = {'time_slots': time_slots_json}
                    response_data, status_code = call_api_gateway(f'/study-plans/{user_id}/items/{item["id"]}', 'PUT', update_data)
                    
                    if status_code == 200:
                        flash('Đã thêm vào thời khóa biểu')
                    else:
                        flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
                else:
                    flash('Không tìm thấy tài liệu trong kế hoạch học tập')
        
        elif action == 'remove_item':
            item_id = request.form.get('item_id')
            response_data, status_code = call_api_gateway(f'/study-plans/{user_id}/items/{item_id}', 'DELETE')
            
            if status_code == 200:
                flash('Đã xóa khỏi kế hoạch học tập')
            else:
                flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
        
        return redirect(url_for('study_plan'))
    
    # Get sorted schedule
    schedule_response, schedule_status = call_api_gateway(f'/study-plans/{user_id}/schedule', 'GET')
    sorted_items = schedule_response.get('schedule', []) if schedule_status == 200 else []
    
    return render_template('study_plan.html',
                         study_plan=study_plan_data,
                         study_plan_items=study_plan_items,
                         courses=[],
                         tutors=[],
                         materials=[],
                         sorted_items=sorted_items)

@app.route('/study_plan/add', methods=['POST'])
def add_to_study_plan():
    if 'access_token' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'}), 401
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID not found'}), 401
    
    try:
        # user_id is already in URL path, don't include it in data
        item_data = {
            'item_type': request.form.get('type'),
            'item_id': request.form.get('id'),
            'name': request.form.get('name'),
            'subject': request.form.get('subject') or '',
            'grade': request.form.get('grade') or '',
            'method': request.form.get('method') or '',
            'time_slots': request.form.get('schedule') or ''
        }
        
        logger.info(f"Adding item to study plan for user {user_id}: {item_data}")
        response_data, status_code = call_api_gateway(f'/study-plans/{user_id}/items', 'POST', item_data)
        
        if status_code == 201:
            logger.info(f"Successfully added item to study plan for user {user_id}")
            return jsonify({'success': True, 'message': 'Đã thêm vào kế hoạch học tập thành công'})
        else:
            error_message = response_data.get('error', 'Unknown error')
            logger.error(f"Failed to add item to study plan: {error_message} (status: {status_code})")
            return jsonify({'success': False, 'message': error_message}), status_code
    except Exception as e:
        logger.error(f"Error adding item to study plan: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi khi thêm vào kế hoạch: {str(e)}'}), 500

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'access_token' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    success = False
    if request.method == 'POST':
        feedback_data = {
            'user_id': user_id,
            'feedback_type': request.form.get('feedback_type'),
            'content': request.form.get('content'),
            'rating': int(request.form.get('rating'))
        }
        
        response_data, status_code = call_api_gateway('/feedback', 'POST', feedback_data)
        
        if status_code == 201:
            flash('Cảm ơn bạn đã gửi phản hồi!')
            success = True
        else:
            flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
    
    # Get user's previous feedback
    response_data, status_code = call_api_gateway(f'/feedback/{user_id}', 'GET')
    feedbacks = response_data.get('feedbacks', []) if status_code == 200 else []
    
    return render_template('feedback.html', success=success, feedbacks=feedbacks)

@app.route('/dashboard')
def dashboard():
    if 'access_token' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    
    # Get user's study plan items
    response_data, status_code = call_api_gateway(f'/study-plans/{user_id}', 'GET')
    study_plan_items = response_data.get('items', []) if status_code == 200 else []
    
    return render_template('dashboard.html', 
                         study_plan_items=study_plan_items,
                         recommendations={'courses': 0, 'tutors': 0, 'materials': 0})

if __name__ == '__main__':
    # Frontend app runs on port 8080, API Gateway runs on port 5000
    # Disable debug mode in Docker to prevent auto-restart issues
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', '8080'))
    
    logger.info("=" * 60)
    logger.info("Starting Flask Frontend Application")
    logger.info(f"API Gateway URL: {API_GATEWAY_URL}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            logger.info(f"  {rule.rule:40s} {list(rule.methods)}")
    logger.info("=" * 60)
    logger.info(f"Starting on http://0.0.0.0:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
