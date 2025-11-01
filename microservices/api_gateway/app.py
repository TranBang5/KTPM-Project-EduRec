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
RECOMMENDATION_SERVICE_URL = os.getenv('RECOMMENDATION_SERVICE_URL', 'http://localhost:5001')
STUDY_PLAN_SERVICE_URL = os.getenv('STUDY_PLAN_SERVICE_URL', 'http://localhost:5002')
FEEDBACK_SERVICE_URL = os.getenv('FEEDBACK_SERVICE_URL', 'http://localhost:5003')

# Service health status
service_health = {
    'recommendation': True,
    'study_plan': True,
    'feedback': True
}

def check_service_health():
    """Check health of all services"""
    services = {
        'recommendation': RECOMMENDATION_SERVICE_URL,
        'study_plan': STUDY_PLAN_SERVICE_URL,
        'feedback': FEEDBACK_SERVICE_URL
    }
    
    for service_name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            service_health[service_name] = response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {str(e)}")
            service_health[service_name] = False

def service_available(service_name):
    """Check if a service is available"""
    return service_health.get(service_name, False)

def handle_service_error(service_name, error):
    """Handle service errors gracefully"""
    logger.error(f"Error calling {service_name} service: {str(error)}")
    return jsonify({
        'error': f'{service_name.replace("_", " ").title()} service is currently unavailable',
        'service': service_name
    }), 503

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
    if not service_available('recommendation'):
        return handle_service_error('recommendation', 'Service unavailable')
    
    try:
        if request.method == 'GET':
            response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/recommendations", 
                                 params=request.args, timeout=30)
        else:  # POST
            response = requests.post(f"{RECOMMENDATION_SERVICE_URL}/recommendations", 
                                  json=request.get_json(), timeout=30)
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('recommendation', e)

@app.route('/recommendations/generate', methods=['POST'])
def generate_recommendations():
    """Route recommendation generation to recommendation service"""
    if not service_available('recommendation'):
        return handle_service_error('recommendation', 'Service unavailable')
    
    try:
        response = requests.post(f"{RECOMMENDATION_SERVICE_URL}/recommendations/generate", 
                              json=request.get_json(), timeout=30)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('recommendation', e)

@app.route('/recommendations/models', methods=['GET'])
def get_model_info():
    """Route model info requests to recommendation service"""
    if not service_available('recommendation'):
        return handle_service_error('recommendation', 'Service unavailable')
    
    try:
        response = requests.get(f"{RECOMMENDATION_SERVICE_URL}/recommendations/models", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('recommendation', e)

# Study Plan Service Routes
@app.route('/study-plans', methods=['POST'])
def create_study_plan():
    """Route study plan creation to study plan service"""
    if not service_available('study_plan'):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        response = requests.post(f"{STUDY_PLAN_SERVICE_URL}/study-plans", 
                              json=request.get_json(), timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>', methods=['GET'])
def get_study_plan(user_id):
    """Route study plan retrieval to study plan service"""
    if not service_available('study_plan'):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        response = requests.get(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>/items', methods=['POST'])
def add_study_plan_item(user_id):
    """Route study plan item addition to study plan service"""
    if not service_available('study_plan'):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        data = request.get_json() or {}
        data['user_id'] = user_id
        response = requests.post(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/items", 
                              json=data, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>/items/<item_id>', methods=['PUT', 'DELETE'])
def manage_study_plan_item(user_id, item_id):
    """Route study plan item updates/deletions to study plan service"""
    if not service_available('study_plan'):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        if request.method == 'PUT':
            response = requests.put(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/items/{item_id}", 
                                 json=request.get_json(), timeout=10)
        else:  # DELETE
            response = requests.delete(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/items/{item_id}", 
                                    timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('study_plan', e)

@app.route('/study-plans/<user_id>/schedule', methods=['GET'])
def get_study_schedule(user_id):
    """Route study schedule requests to study plan service"""
    if not service_available('study_plan'):
        return handle_service_error('study_plan', 'Service unavailable')
    
    try:
        response = requests.get(f"{STUDY_PLAN_SERVICE_URL}/study-plans/{user_id}/schedule", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('study_plan', e)

# Feedback Service Routes
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Route feedback submission to feedback service"""
    if not service_available('feedback'):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.post(f"{FEEDBACK_SERVICE_URL}/feedback", 
                              json=request.get_json(), timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('feedback', e)

@app.route('/feedback/<user_id>', methods=['GET'])
def get_user_feedback(user_id):
    """Route user feedback retrieval to feedback service"""
    if not service_available('feedback'):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/{user_id}", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('feedback', e)

@app.route('/feedback/<feedback_id>', methods=['PUT'])
def update_feedback_status(feedback_id):
    """Route feedback status updates to feedback service"""
    if not service_available('feedback'):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.put(f"{FEEDBACK_SERVICE_URL}/feedback/{feedback_id}", 
                             json=request.get_json(), timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('feedback', e)

@app.route('/feedback/analytics', methods=['GET'])
def get_feedback_analytics():
    """Route feedback analytics to feedback service"""
    if not service_available('feedback'):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/analytics", 
                             params=request.args, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('feedback', e)

@app.route('/feedback/analytics/<user_id>', methods=['GET'])
def get_user_feedback_analytics(user_id):
    """Route user feedback analytics to feedback service"""
    if not service_available('feedback'):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/analytics/{user_id}", 
                             timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('feedback', e)

@app.route('/feedback/reports', methods=['GET'])
def generate_feedback_report():
    """Route feedback reports to feedback service"""
    if not service_available('feedback'):
        return handle_service_error('feedback', 'Service unavailable')
    
    try:
        response = requests.get(f"{FEEDBACK_SERVICE_URL}/feedback/reports", 
                             params=request.args, timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return handle_service_error('feedback', e)

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
    app.run(host='0.0.0.0', port=5000, debug=True)
