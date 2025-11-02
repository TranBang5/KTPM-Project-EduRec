from flask import Flask, request, jsonify, redirect, url_for
import requests
import logging
import os
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Service URLs
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5004')
RECOMMENDATION_SERVICE_URL = os.getenv('RECOMMENDATION_SERVICE_URL', 'http://localhost:5001')
STUDY_PLAN_SERVICE_URL = os.getenv('STUDY_PLAN_SERVICE_URL', 'http://localhost:5002')
FEEDBACK_SERVICE_URL = os.getenv('FEEDBACK_SERVICE_URL', 'http://localhost:5003')
CATALOG_SERVICE_URL = os.getenv('CATALOG_SERVICE_URL', 'http://localhost:5005')
PROFILE_SERVICE_URL = os.getenv('PROFILE_SERVICE_URL', 'http://localhost:5006')

# Service health status
service_health = {
    'auth': True,
    'recommendation': True,
    'study_plan': True,
    'feedback': True,
    'catalog': True,
    'profile': True
}

def check_service_health():
    """Check health of all services"""
    services = {
        'auth': AUTH_SERVICE_URL,
        'recommendation': RECOMMENDATION_SERVICE_URL,
        'study_plan': STUDY_PLAN_SERVICE_URL,
        'feedback': FEEDBACK_SERVICE_URL,
        'catalog': CATALOG_SERVICE_URL,
        'profile': PROFILE_SERVICE_URL
    }
    
    for service_name, url in services.items():
        try:
            logger.debug(f"Checking health of {service_name} at {url}")
            response = requests.get(f"{url}/health", timeout=5)
            service_health[service_name] = response.status_code == 200
            if service_health[service_name]:
                logger.info(f"{service_name} service is healthy (status: {response.status_code})")
            else:
                logger.warning(f"{service_name} service health check returned status {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Health check connection error for {service_name} at {url}: {str(e)}")
            service_health[service_name] = False
        except requests.exceptions.Timeout as e:
            logger.warning(f"Health check timeout for {service_name} at {url}: {str(e)}")
            service_health[service_name] = False
        except Exception as e:
            logger.error(f"Health check failed for {service_name} at {url}: {str(e)}")
            service_health[service_name] = False

def service_available(service_name, retry_check=False):
    """Check if a service is available"""
    if retry_check:
        # Re-check health if service was marked as unavailable
        if not service_health.get(service_name, False):
            services = {
                'auth': AUTH_SERVICE_URL,
                'recommendation': RECOMMENDATION_SERVICE_URL,
                'study_plan': STUDY_PLAN_SERVICE_URL,
                'feedback': FEEDBACK_SERVICE_URL,
                'catalog': CATALOG_SERVICE_URL,
                'profile': PROFILE_SERVICE_URL
            }
            url = services.get(service_name)
            if url:
                logger.info(f"Retrying health check for {service_name} at {url}")
                try:
                    response = requests.get(f"{url}/health", timeout=5)
                    service_health[service_name] = response.status_code == 200
                    if service_health[service_name]:
                        logger.info(f"{service_name} service is now available (status: {response.status_code})")
                    else:
                        logger.warning(f"{service_name} service health check returned status {response.status_code}")
                except requests.exceptions.Timeout as e:
                    logger.warning(f"Health check timeout for {service_name}: {str(e)}")
                    service_health[service_name] = False
                except requests.exceptions.ConnectionError as e:
                    logger.warning(f"Health check connection error for {service_name}: {str(e)}")
                    service_health[service_name] = False
                except Exception as e:
                    logger.warning(f"Health check retry failed for {service_name}: {str(e)}")
                    service_health[service_name] = False
    return service_health.get(service_name, False)

def handle_service_error(service_name, error):
    """Handle service errors gracefully"""
    logger.error(f"Error calling {service_name} service: {str(error)}")
    return jsonify({
        'error': f'{service_name.replace("_", " ").title()} service is currently unavailable',
        'service': service_name
    }), 503

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for API Gateway"""
    check_service_health()
    return jsonify({
        'service': 'api-gateway',
        'status': 'running',
        'description': 'API Gateway for Student Study Plan Recommendation System',
        'available_endpoints': {
            'health': '/health',
            'auth': '/auth/*',
            'recommendations': '/recommendations/*',
            'study_plans': '/study-plans/*',
            'feedback': '/feedback/*',
            'catalog': '/catalog/*',
            'profiles': '/profiles/*'
        },
        'services_status': service_health
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """API Gateway health check"""
    check_service_health()
    return jsonify({
        'status': 'healthy',
        'service': 'api-gateway',
        'services': service_health
    })

# Recommendation Service Routes
@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    """Route recommendations requests to recommendation service"""
    if not service_available('recommendation', retry_check=True):
        return handle_service_error('recommendation', 'Service unavailable')
    
    try:
        if request.method == 'GET':
            response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/recommendations", 
                                 params=request.args, timeout=30)
        else:  # POST
            response = requests.post(f"{RECOMMENDATION_SERVICE_URL}/recommendations", 
                                  json=request.get_json(), timeout=30)
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['recommendation'] = False
        logger.error(f"Connection error to recommendation service: {str(e)}")
        return handle_service_error('recommendation', e)
    except Exception as e:
        logger.error(f"Error calling recommendation service: {str(e)}")
        return handle_service_error('recommendation', e)

@app.route('/recommendations/generate', methods=['POST'])
def generate_recommendations():
    """Route recommendation generation to recommendation service"""
    if not service_available('recommendation', retry_check=True):
        return handle_service_error('recommendation', 'Service unavailable')
    
    try:
        response = requests.post(f"{RECOMMENDATION_SERVICE_URL}/recommendations/generate", 
                              json=request.get_json(), timeout=30)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['recommendation'] = False
        logger.error(f"Connection error to recommendation service: {str(e)}")
        return handle_service_error('recommendation', e)
    except Exception as e:
        logger.error(f"Error calling recommendation service: {str(e)}")
        return handle_service_error('recommendation', e)

@app.route('/recommendations/models', methods=['GET'])
def get_model_info():
    """Route model info requests to recommendation service"""
    if not service_available('recommendation', retry_check=True):
        return handle_service_error('recommendation', 'Service unavailable')
    
    try:
        response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/recommendations/models", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['recommendation'] = False
        logger.error(f"Connection error to recommendation service: {str(e)}")
        return handle_service_error('recommendation', e)
    except Exception as e:
        logger.error(f"Error calling recommendation service: {str(e)}")
        return handle_service_error('recommendation', e)

# Study Plan Service Routes
@app.route('/study-plans', methods=['POST'])
def create_study_plan():
    """Route study plan creation to study plan service"""
    if not service_available('study_plan', retry_check=True):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        response = requests.post(f"{STUDY_PLAN_SERVICE_URL}/study-plans", 
                              json=request.get_json(), timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['study_plan'] = False
        logger.error(f"Connection error to study plan service: {str(e)}")
        return handle_service_error('study_plan', e)
    except Exception as e:
        logger.error(f"Error calling study plan service: {str(e)}")
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>', methods=['GET'])
def get_study_plan(user_id):
    """Route study plan retrieval to study plan service"""
    if not service_available('study_plan', retry_check=True):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        response = requests.get(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['study_plan'] = False
        logger.error(f"Connection error to study plan service: {str(e)}")
        return handle_service_error('study_plan', e)
    except Exception as e:
        logger.error(f"Error calling study plan service: {str(e)}")
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>/items', methods=['POST'])
def add_study_plan_item(user_id):
    """Route study plan item addition to study plan service"""
    if not service_available('study_plan', retry_check=True):
        logger.error(f"Study plan service is unavailable. Current health status: {service_health.get('study_plan', False)}")
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        data = request.get_json() or {}
        # user_id is already in URL path, don't need it in data
        logger.info(f"Adding item to study plan for user {user_id}: {data}")
        response = requests.post(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/items", 
                              json=data, timeout=10)
        logger.info(f"Study plan service responded with status {response.status_code}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['study_plan'] = False
        logger.error(f"Connection error to study plan service at {STUDY_PLAN_SERVICE_URL}: {str(e)}")
        return handle_service_error('study_plan', e)
    except requests.exceptions.Timeout as e:
        service_health['study_plan'] = False
        logger.error(f"Timeout error to study plan service: {str(e)}")
        return handle_service_error('study_plan', e)
    except Exception as e:
        logger.error(f"Error calling study plan service: {str(e)}")
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>/items/<item_id>', methods=['PUT', 'DELETE'])
def manage_study_plan_item(user_id, item_id):
    """Route study plan item updates/deletions to study plan service"""
    if not service_available('study_plan', retry_check=True):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        if request.method == 'PUT':
            response = requests.put(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/items/{item_id}", 
                                 json=request.get_json(), timeout=10)
        else:  # DELETE
            response = requests.delete(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/items/{item_id}", 
                                    timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['study_plan'] = False
        logger.error(f"Connection error to study plan service: {str(e)}")
        return handle_service_error('study_plan', e)
    except Exception as e:
        logger.error(f"Error calling study plan service: {str(e)}")
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>/schedule', methods=['GET'])
def get_study_schedule(user_id):
    """Route study schedule requests to study plan service"""
    if not service_available('study_plan', retry_check=True):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        response = requests.get(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/schedule", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['study_plan'] = False
        logger.error(f"Connection error to study plan service: {str(e)}")
        return handle_service_error('study_plan', e)
    except Exception as e:
        logger.error(f"Error calling study plan service: {str(e)}")
        return handle_service_error('study_plan', e)

# Feedback Service Routes
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Route feedback submission to feedback service"""
    if not service_available('feedback', retry_check=True):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.post(f"{FEEDBACK_SERVICE_URL}/feedback", 
                              json=request.get_json(), timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['feedback'] = False
        logger.error(f"Connection error to feedback service: {str(e)}")
        return handle_service_error('feedback', e)
    except Exception as e:
        logger.error(f"Error calling feedback service: {str(e)}")
        return handle_service_error('feedback', e)

@app.route('/feedback/<user_id>', methods=['GET'])
def get_user_feedback(user_id):
    """Route user feedback retrieval to feedback service"""
    if not service_available('feedback', retry_check=True):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/{user_id}", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['feedback'] = False
        logger.error(f"Connection error to feedback service: {str(e)}")
        return handle_service_error('feedback', e)
    except Exception as e:
        logger.error(f"Error calling feedback service: {str(e)}")
        return handle_service_error('feedback', e)

@app.route('/feedback/<feedback_id>', methods=['PUT'])
def update_feedback_status(feedback_id):
    """Route feedback status updates to feedback service"""
    if not service_available('feedback', retry_check=True):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.put(f"{FEEDBACK_SERVICE_URL}/feedback/{feedback_id}", 
                             json=request.get_json(), timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['feedback'] = False
        logger.error(f"Connection error to feedback service: {str(e)}")
        return handle_service_error('feedback', e)
    except Exception as e:
        logger.error(f"Error calling feedback service: {str(e)}")
        return handle_service_error('feedback', e)

@app.route('/feedback/analytics', methods=['GET'])
def get_feedback_analytics():
    """Route feedback analytics to feedback service"""
    if not service_available('feedback', retry_check=True):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/analytics", 
                             params=request.args, timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['feedback'] = False
        logger.error(f"Connection error to feedback service: {str(e)}")
        return handle_service_error('feedback', e)
    except Exception as e:
        logger.error(f"Error calling feedback service: {str(e)}")
        return handle_service_error('feedback', e)

@app.route('/feedback/analytics/<user_id>', methods=['GET'])
def get_user_feedback_analytics(user_id):
    """Route user feedback analytics to feedback service"""
    if not service_available('feedback', retry_check=True):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/analytics/{user_id}", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['feedback'] = False
        logger.error(f"Connection error to feedback service: {str(e)}")
        return handle_service_error('feedback', e)
    except Exception as e:
        logger.error(f"Error calling feedback service: {str(e)}")
        return handle_service_error('feedback', e)

@app.route('/feedback/reports', methods=['GET'])
def generate_feedback_report():
    """Route feedback reports to feedback service"""
    if not service_available('feedback', retry_check=True):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/reports", 
                             params=request.args, timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['feedback'] = False
        logger.error(f"Connection error to feedback service: {str(e)}")
        return handle_service_error('feedback', e)
    except Exception as e:
        logger.error(f"Error calling feedback service: {str(e)}")
        return handle_service_error('feedback', e)

# Auth Service Routes
@app.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def auth_routes(path):
    """Route all auth requests to auth service"""
    # Retry health check if service was marked as unavailable
    if not service_available('auth', retry_check=True):
        return handle_service_error('auth', 'Service unavailable')
    
    try:
        url = f"{AUTH_SERVICE_URL}/auth/{path}"
        if request.method == 'GET':
            response = requests.get(url, params=request.args, timeout=10)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json(), timeout=10)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), timeout=10)
        else:  # DELETE
            response = requests.delete(url, timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        # Mark service as unavailable if connection fails
        service_health['auth'] = False
        logger.error(f"Connection error to auth service: {str(e)}")
        return handle_service_error('auth', e)
    except Exception as e:
        logger.error(f"Error calling auth service: {str(e)}")
        return handle_service_error('auth', e)

# Catalog Service Routes
@app.route('/catalog/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catalog_routes(path):
    """Route all catalog requests to catalog service"""
    if not service_available('catalog', retry_check=True):
        return handle_service_error('catalog', 'Service unavailable')
    
    try:
        url = f"{CATALOG_SERVICE_URL}/catalog/{path}"
        if request.method == 'GET':
            response = requests.get(url, params=request.args, headers=request.headers, timeout=10)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json(), headers=request.headers, timeout=10)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), headers=request.headers, timeout=10)
        else:  # DELETE
            response = requests.delete(url, headers=request.headers, timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        service_health['catalog'] = False
        logger.error(f"Connection error to catalog service: {str(e)}")
        return handle_service_error('catalog', e)
    except Exception as e:
        logger.error(f"Error calling catalog service: {str(e)}")
        return handle_service_error('catalog', e)

# Profile Service Routes
@app.route('/profiles/<int:user_id>', methods=['GET', 'PUT'])
def profile_get_update(user_id):
    """Route profile get/update requests to profile service"""
    # Retry health check if service was marked as unavailable
    if not service_available('profile', retry_check=True):
        return handle_service_error('profile', 'Service unavailable')
    
    try:
        if request.method == 'GET':
            response = requests.get(f"{PROFILE_SERVICE_URL}/profiles/{user_id}", 
                                 headers=request.headers, timeout=10)
        else:  # PUT
            response = requests.put(f"{PROFILE_SERVICE_URL}/profiles/{user_id}", 
                                  json=request.get_json(), headers=request.headers, timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        # Mark service as unavailable if connection fails
        service_health['profile'] = False
        logger.error(f"Connection error to profile service: {str(e)}")
        return handle_service_error('profile', e)
    except Exception as e:
        logger.error(f"Error calling profile service: {str(e)}")
        return handle_service_error('profile', e)

@app.route('/profiles/<int:user_id>/history', methods=['GET'])
def profile_history(user_id):
    """Route profile history requests to profile service"""
    # Retry health check if service was marked as unavailable
    if not service_available('profile', retry_check=True):
        return handle_service_error('profile', 'Service unavailable')
    
    try:
        response = requests.get(f"{PROFILE_SERVICE_URL}/profiles/{user_id}/history", 
                             headers=request.headers, timeout=10)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError as e:
        # Mark service as unavailable if connection fails
        service_health['profile'] = False
        logger.error(f"Connection error to profile service: {str(e)}")
        return handle_service_error('profile', e)
    except Exception as e:
        logger.error(f"Error calling profile service: {str(e)}")
        return handle_service_error('profile', e)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check service health on startup
    check_service_health()
    # Disable debug mode in Docker to prevent auto-restart
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
