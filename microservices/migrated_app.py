from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db, User, Course, Tutor, Material
import requests
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://user:password@db:3306/recommendation_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Microservices URLs
RECOMMENDATION_SERVICE_URL = os.getenv('RECOMMENDATION_SERVICE_URL', 'http://localhost:5001')
STUDY_PLAN_SERVICE_URL = os.getenv('STUDY_PLAN_SERVICE_URL', 'http://localhost:5002')
FEEDBACK_SERVICE_URL = os.getenv('FEEDBACK_SERVICE_URL', 'http://localhost:5003')

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def call_microservice(service_url, endpoint, method='GET', data=None, params=None):
    """Helper function to call microservices"""
    try:
        url = f"{service_url}{endpoint}"
        if method == 'GET':
            response = requests.get(url, params=params, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=30)
        
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Error calling microservice {service_url}{endpoint}: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        school = request.form.get('school')
        current_grade = request.form.get('current_grade')
        learning_goals = request.form.get('learning_goals')
        favorite_subjects = request.form.get('favorite_subjects')
        preferred_learning_method = request.form.get('preferred_learning_method')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            school=school,
            current_grade=current_grade,
            learning_goals=learning_goals,
            favorite_subjects=favorite_subjects,
            preferred_learning_method=preferred_learning_method
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('profile'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.school = request.form.get('school')
        current_user.current_grade = request.form.get('current_grade')
        current_user.favorite_subjects = request.form.get('favorite_subjects')
        current_user.learning_goals = request.form.get('learning_goals')
        current_user.preferred_learning_method = request.form.get('preferred_learning_method')
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user)

@app.route('/recommendations', methods=['GET', 'POST'])
@login_required
def recommendations():
    if not all([current_user.school, current_user.current_grade, current_user.favorite_subjects, current_user.learning_goals]):
        flash('Vui lòng hoàn thành hồ sơ của bạn trước khi xem đề xuất')
        return redirect(url_for('profile'))
    
    # Prepare user data for recommendation service
    user_data = {
        'school': current_user.school,
        'current_grade': current_user.current_grade,
        'learning_goals': current_user.learning_goals,
        'favorite_subjects': current_user.favorite_subjects,
        'preferred_learning_method': current_user.preferred_learning_method
    }
    
    try:
        # Call recommendation service
        response_data, status_code = call_microservice(
            RECOMMENDATION_SERVICE_URL, 
            '/recommendations/generate', 
            'POST', 
            user_data
        )
        
        if status_code != 200:
            flash(f'Lỗi khi tạo đề xuất: {response_data.get("error", "Unknown error")}')
            return redirect(url_for('profile'))
        
        # Get recommendations from response
        recommendations_data = response_data.get('recommendations', {})
        
        # Get active tab from request
        active_tab = request.args.get('tab', 'courses')
        
        # Get filter parameters
        filters = {
            'subject': request.args.get('subject', ''),
            'grade': request.args.get('grade', ''),
            'method': request.args.get('method', '')
        }
        
        # Get all items from database for display
        all_courses = Course.query.all()
        all_tutors = Tutor.query.all()
        all_materials = Material.query.all()
        
        # Process recommendations with database items
        recommendations = {'courses': [], 'tutors': [], 'materials': []}
        
        # Process courses
        for course_rec in recommendations_data.get('courses', []):
            course_id = course_rec['id'].replace('course_', '')
            course = next((c for c in all_courses if str(c.id) == course_id), None)
            if course and apply_filters(course, filters):
                course.score = course_rec['score']
                recommendations['courses'].append(course)
        
        # Process tutors
        for tutor_rec in recommendations_data.get('tutors', []):
            tutor_id = tutor_rec['id'].replace('tutor_', '')
            tutor = next((t for t in all_tutors if str(t.id) == tutor_id), None)
            if tutor and apply_filters(tutor, filters):
                tutor.score = tutor_rec['score']
                recommendations['tutors'].append(tutor)
        
        # Process materials
        for material_rec in recommendations_data.get('materials', []):
            material_id = material_rec['id'].replace('material_', '')
            material = next((m for m in all_materials if str(m.id) == material_id), None)
            if material and apply_filters(material, filters):
                material.score = material_rec['score']
                recommendations['materials'].append(material)
        
        # Get filter options
        all_subjects = set()
        all_grades = set()
        all_methods = set()
        
        for course in all_courses:
            all_subjects.add(course.subject)
            all_grades.add(course.grade_level)
            all_methods.add(course.teaching_method)
        
        for tutor in all_tutors:
            all_subjects.add(tutor.subject)
            all_grades.add(tutor.specialized_grade)
            all_methods.add(tutor.teaching_method)
        
        for material in all_materials:
            all_subjects.add(material.subject)
            all_grades.add(material.grade_level)
        
        if request.method == 'POST':
            return render_template('_recommendations.html', 
                                 recommendations=recommendations,
                                 active_tab=active_tab)
        
        return render_template('recommendations.html', 
                             recommendations=recommendations,
                             active_tab=active_tab,
                             all_subjects=sorted(all_subjects),
                             all_grades=sorted(all_grades),
                             all_methods=sorted(all_methods))
    
    except Exception as e:
        logger.error(f"Error in recommendations: {str(e)}")
        flash(f'Lỗi khi tạo đề xuất: {str(e)}')
        return redirect(url_for('profile'))

def apply_filters(item, filters):
    """Apply filters to an item based on its type"""
    if filters['subject'] and item.subject != filters['subject']:
        return False
    if filters['grade'] and item.grade_level != filters['grade']:
        return False
    if filters['method'] and hasattr(item, 'teaching_method') and item.teaching_method != filters['method']:
        return False
    return True

@app.route('/study_plan', methods=['GET', 'POST'])
@login_required
def study_plan():
    try:
        # Get or create study plan
        response_data, status_code = call_microservice(
            STUDY_PLAN_SERVICE_URL,
            f'/study-plans/{current_user.id}',
            'GET'
        )
        
        if status_code == 404:
            # Create new study plan
            create_data = {'user_id': current_user.id}
            response_data, status_code = call_microservice(
                STUDY_PLAN_SERVICE_URL,
                '/study-plans',
                'POST',
                create_data
            )
        
        if status_code != 200:
            flash('Lỗi khi tải kế hoạch học tập')
            return redirect(url_for('dashboard'))
        
        study_plan_data = response_data.get('study_plan', {})
        study_plan_items = response_data.get('items', [])
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add_item':
                item_data = {
                    'user_id': current_user.id,
                    'item_type': request.form.get('item_type'),
                    'item_id': request.form.get('item_id'),
                    'name': request.form.get('name'),
                    'subject': request.form.get('subject'),
                    'grade': request.form.get('grade'),
                    'method': request.form.get('method'),
                    'time_slots': request.form.get('time_slots')
                }
                
                response_data, status_code = call_microservice(
                    STUDY_PLAN_SERVICE_URL,
                    f'/study-plans/{current_user.id}/items',
                    'POST',
                    item_data
                )
                
                if status_code == 201:
                    flash('Đã thêm vào kế hoạch học tập')
                else:
                    flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
            
            elif action == 'remove_item':
                item_id = request.form.get('item_id')
                response_data, status_code = call_microservice(
                    STUDY_PLAN_SERVICE_URL,
                    f'/study-plans/{current_user.id}/items/{item_id}',
                    'DELETE'
                )
                
                if status_code == 200:
                    flash('Đã xóa khỏi kế hoạch học tập')
                else:
                    flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
            
            return redirect(url_for('study_plan'))
        
        # Get all available items for selection
        courses = Course.query.all()
        tutors = Tutor.query.all()
        materials = Material.query.all()
        
        # Get sorted schedule
        schedule_response, schedule_status = call_microservice(
            STUDY_PLAN_SERVICE_URL,
            f'/study-plans/{current_user.id}/schedule',
            'GET'
        )
        
        sorted_items = schedule_response.get('schedule', []) if schedule_status == 200 else []
        
        return render_template('study_plan.html',
                             study_plan=study_plan_data,
                             study_plan_items=study_plan_items,
                             courses=courses,
                             tutors=tutors,
                             materials=materials,
                             sorted_items=sorted_items)
    
    except Exception as e:
        logger.error(f"Error in study_plan: {str(e)}")
        flash(f'Lỗi: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/study_plan/add', methods=['POST'])
@login_required
def add_to_study_plan():
    try:
        item_data = {
            'user_id': current_user.id,
            'item_type': request.form.get('type'),
            'item_id': request.form.get('id'),
            'name': request.form.get('name'),
            'subject': request.form.get('subject'),
            'grade': request.form.get('grade'),
            'method': request.form.get('method'),
            'time_slots': request.form.get('schedule')
        }
        
        response_data, status_code = call_microservice(
            STUDY_PLAN_SERVICE_URL,
            f'/study-plans/{current_user.id}/items',
            'POST',
            item_data
        )
        
        if status_code == 201:
            return jsonify({'success': True, 'message': 'Đã thêm vào kế hoạch học tập thành công'})
        else:
            return jsonify({'success': False, 'message': response_data.get('error', 'Unknown error')})
    
    except Exception as e:
        logger.error(f"Error adding to study plan: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    success = False
    
    if request.method == 'POST':
        feedback_data = {
            'user_id': current_user.id,
            'feedback_type': request.form.get('feedback_type'),
            'content': request.form.get('content'),
            'rating': int(request.form.get('rating'))
        }
        
        response_data, status_code = call_microservice(
            FEEDBACK_SERVICE_URL,
            '/feedback',
            'POST',
            feedback_data
        )
        
        if status_code == 201:
            success = True
            flash('Cảm ơn bạn đã gửi phản hồi!')
        else:
            flash(f'Lỗi: {response_data.get("error", "Unknown error")}')
    
    # Get user's previous feedback
    response_data, status_code = call_microservice(
        FEEDBACK_SERVICE_URL,
        f'/feedback/{current_user.id}',
        'GET'
    )
    
    feedbacks = response_data.get('feedbacks', []) if status_code == 200 else []
    
    return render_template('feedback.html', success=success, feedbacks=feedbacks)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's study plan items
    response_data, status_code = call_microservice(
        STUDY_PLAN_SERVICE_URL,
        f'/study-plans/{current_user.id}',
        'GET'
    )
    
    study_plan_items = response_data.get('items', []) if status_code == 200 else []
    
    # Get recommendations count
    recommendations = {
        'courses': Course.query.count(),
        'tutors': Tutor.query.count(),
        'materials': Material.query.count()
    }
    
    return render_template('dashboard.html', 
                         study_plan_items=study_plan_items,
                         recommendations=recommendations)

def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("Tables created successfully.")
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
