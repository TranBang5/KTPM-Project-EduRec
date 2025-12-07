from flask import Flask, request, jsonify
from datetime import datetime
from models import db, Feedback
import logging
import json
import os
import sys
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@feedback-db:3306/feedback_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for feedback service"""
    return jsonify({
        'service': 'feedback-service',
        'status': 'running',
        'description': 'Feedback Service for collecting and analyzing user feedback',
        'available_endpoints': {
            'health': '/health',
            'submit': '/feedback (POST)',
            'get_user_feedback': '/feedback/<user_id> (GET)',
            'update_feedback': '/feedback/<feedback_id> (PUT)',
            'analytics': '/feedback/analytics (GET)',
            'user_analytics': '/feedback/analytics/<user_id> (GET)',
            'reports': '/feedback/reports (GET)'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        with db.engine.connect() as conn:
            conn.execute(db.text("SELECT 1"))
        return jsonify({
            'status': 'healthy',
            'service': 'feedback-service'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'service': 'feedback-service', 'error': str(e)}), 503

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback from a user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['user_id', 'feedback_type', 'content', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Validate rating
        rating = data['rating']
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400

        # Create feedback entry
        feedback = Feedback(
            user_id=data['user_id'],
            feedback_type=data['feedback_type'],
            content=data['content'],
            rating=rating,
            status='pending'
        )

        db.session.add(feedback)
        db.session.commit()

        return jsonify({
            'success': True,
            'feedback_id': feedback.id,
            'message': 'Feedback submitted successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/<user_id>', methods=['GET'])
def get_user_feedback(user_id):
    """Get all feedback for a specific user"""
    try:
        user_feedbacks = Feedback.query.filter_by(user_id=user_id).order_by(Feedback.created_at.desc()).all()
        
        feedbacks_list = [{
            'id': fb.id,
            'user_id': fb.user_id,
            'feedback_type': fb.feedback_type,
            'content': fb.content,
            'rating': fb.rating,
            'status': fb.status,
            'created_at': fb.created_at.isoformat() if fb.created_at else None,
            'updated_at': fb.updated_at.isoformat() if fb.updated_at else None
        } for fb in user_feedbacks]

        return jsonify({
            'success': True,
            'feedbacks': feedbacks_list,
            'count': len(feedbacks_list)
        })

    except Exception as e:
        logger.error(f"Error getting user feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/<int:feedback_id>', methods=['PUT'])
def update_feedback_status(feedback_id):
    """Update feedback status (for admin use)"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'status is required'}), 400

        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return jsonify({'error': 'Feedback not found'}), 404

        valid_statuses = ['pending', 'reviewed', 'resolved']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Status must be one of: {valid_statuses}'}), 400

        feedback.status = data['status']
        db.session.commit()

        return jsonify({
            'success': True,
            'feedback': {
                'id': feedback.id,
                'user_id': feedback.user_id,
                'feedback_type': feedback.feedback_type,
                'content': feedback.content,
                'rating': feedback.rating,
                'status': feedback.status,
                'created_at': feedback.created_at.isoformat() if feedback.created_at else None,
                'updated_at': feedback.updated_at.isoformat() if feedback.updated_at else None
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating feedback status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/analytics', methods=['GET'])
def get_feedback_analytics():
    """Get overall feedback analytics"""
    try:
        # Calculate overall analytics
        total_feedback = Feedback.query.count()
        if total_feedback == 0:
            return jsonify({
                'success': True,
                'analytics': {
                    'total_feedback': 0,
                    'average_rating': 0.0,
                    'feedback_by_type': {},
                    'feedback_by_status': {},
                    'recent_feedback': []
                }
            })

        # Calculate average rating
        avg_rating = db.session.query(func.avg(Feedback.rating)).scalar()
        average_rating = round(float(avg_rating), 2) if avg_rating else 0.0

        # Group by type
        feedback_by_type = {}
        type_counts = db.session.query(Feedback.feedback_type, func.count(Feedback.id)).group_by(Feedback.feedback_type).all()
        for fb_type, count in type_counts:
            feedback_by_type[fb_type] = count

        # Group by status
        feedback_by_status = {}
        status_counts = db.session.query(Feedback.status, func.count(Feedback.id)).group_by(Feedback.status).all()
        for status, count in status_counts:
            feedback_by_status[status] = count

        # Get recent feedback (last 10)
        recent_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(10).all()
        recent_feedback = [{
            'id': fb.id,
            'user_id': fb.user_id,
            'feedback_type': fb.feedback_type,
            'content': fb.content[:100] + '...' if len(fb.content) > 100 else fb.content,
            'rating': fb.rating,
            'status': fb.status,
            'created_at': fb.created_at.isoformat() if fb.created_at else None
        } for fb in recent_feedbacks]

        analytics = {
            'total_feedback': total_feedback,
            'average_rating': average_rating,
            'feedback_by_type': feedback_by_type,
            'feedback_by_status': feedback_by_status,
            'recent_feedback': recent_feedback
        }

        return jsonify({
            'success': True,
            'analytics': analytics
        })

    except Exception as e:
        logger.error(f"Error getting feedback analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/analytics/<user_id>', methods=['GET'])
def get_user_feedback_analytics(user_id):
    """Get feedback analytics for a specific user"""
    try:
        user_feedbacks = Feedback.query.filter_by(user_id=user_id).all()
        
        if not user_feedbacks:
            return jsonify({
                'success': True,
                'analytics': {
                    'total_feedback': 0,
                    'average_rating': 0.0,
                    'feedback_by_type': {},
                    'last_feedback_date': None
                }
            })

        total_feedback = len(user_feedbacks)
        avg_rating = sum(fb.rating for fb in user_feedbacks) / total_feedback if total_feedbacks else 0.0
        
        feedback_by_type = {}
        for fb in user_feedbacks:
            fb_type = fb.feedback_type
            feedback_by_type[fb_type] = feedback_by_type.get(fb_type, 0) + 1

        last_feedback = max(user_feedbacks, key=lambda x: x.created_at if x.created_at else datetime.min)
        last_feedback_date = last_feedback.created_at.isoformat() if last_feedback.created_at else None

        analytics = {
            'total_feedback': total_feedback,
            'average_rating': round(avg_rating, 2),
            'feedback_by_type': feedback_by_type,
            'last_feedback_date': last_feedback_date
        }

        return jsonify({
            'success': True,
            'analytics': analytics
        })

    except Exception as e:
        logger.error(f"Error getting user feedback analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/reports', methods=['GET'])
def generate_feedback_report():
    """Generate a detailed feedback report"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        feedback_type = request.args.get('feedback_type')
        status = request.args.get('status')

        # Build query
        query = Feedback.query

        if start_date:
            query = query.filter(Feedback.created_at >= datetime.fromisoformat(start_date.replace('Z', '+00:00')))
        if end_date:
            query = query.filter(Feedback.created_at <= datetime.fromisoformat(end_date.replace('Z', '+00:00')))
        if feedback_type:
            query = query.filter(Feedback.feedback_type == feedback_type)
        if status:
            query = query.filter(Feedback.status == status)

        filtered_feedbacks = query.all()

        # Generate report
        feedbacks_list = [{
            'id': fb.id,
            'user_id': fb.user_id,
            'feedback_type': fb.feedback_type,
            'content': fb.content,
            'rating': fb.rating,
            'status': fb.status,
            'created_at': fb.created_at.isoformat() if fb.created_at else None,
            'updated_at': fb.updated_at.isoformat() if fb.updated_at else None
        } for fb in filtered_feedbacks]

        # Calculate summary
        total_feedback = len(filtered_feedbacks)
        avg_rating = sum(fb.rating for fb in filtered_feedbacks) / total_feedback if filtered_feedbacks else 0
        
        feedback_by_type = {}
        feedback_by_status = {}
        for fb in filtered_feedbacks:
            fb_type = fb.feedback_type
            fb_status = fb.status
            feedback_by_type[fb_type] = feedback_by_type.get(fb_type, 0) + 1
            feedback_by_status[fb_status] = feedback_by_status.get(fb_status, 0) + 1

        report = {
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'feedback_type': feedback_type,
                'status': status
            },
            'summary': {
                'total_feedback': total_feedback,
                'average_rating': round(avg_rating, 2),
                'feedback_by_type': feedback_by_type,
                'feedback_by_status': feedback_by_status
            },
            'feedbacks': feedbacks_list
        }

        return jsonify({
            'success': True,
            'report': report
        })

    except Exception as e:
        logger.error(f"Error generating feedback report: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        logger.info("Initializing Feedback Service...")
        with app.app_context():
            # Retry database connection and table creation
            max_retries = 5
            retry_delay = 2
            for attempt in range(max_retries):
                try:
                    # Test database connection
                    with db.engine.connect() as conn:
                        conn.execute(db.text("SELECT 1"))
                    logger.info(f"Database connection successful (attempt {attempt + 1})")
                    
                    # Create all tables
                    db.create_all()
                    logger.info("Database tables created/verified successfully")
                    break
                except Exception as db_error:
                    if attempt < max_retries - 1:
                        logger.warning(f"Database initialization attempt {attempt + 1} failed: {str(db_error)}")
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        import time
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Database initialization failed after {max_retries} attempts: {str(db_error)}")
                        logger.error("Service cannot start without database connection")
                        raise
        
        logger.info(f"Feedback Service starting on port 5003")
        logger.info(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")
        
        # Disable debug mode in Docker to prevent auto-restart
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(host='0.0.0.0', port=5003, debug=debug_mode)
    except Exception as e:
        logger.error(f"Failed to start Feedback Service: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
