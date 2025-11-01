from flask import Flask, request, jsonify
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory storage for feedback (in production, use a database)
feedbacks = {}
feedback_analytics = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'feedback-service'
    })

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
        feedback_id = f"fb_{len(feedbacks) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        feedback = {
            'id': feedback_id,
            'user_id': data['user_id'],
            'feedback_type': data['feedback_type'],
            'content': data['content'],
            'rating': rating,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'  # pending, reviewed, resolved
        }

        # Store feedback
        feedbacks[feedback_id] = feedback

        # Update analytics
        user_id = data['user_id']
        if user_id not in feedback_analytics:
            feedback_analytics[user_id] = {
                'total_feedback': 0,
                'average_rating': 0.0,
                'feedback_by_type': {},
                'last_feedback_date': None
            }

        analytics = feedback_analytics[user_id]
        analytics['total_feedback'] += 1
        
        # Update average rating
        total_rating = analytics['average_rating'] * (analytics['total_feedback'] - 1) + rating
        analytics['average_rating'] = total_rating / analytics['total_feedback']
        
        # Update feedback by type
        feedback_type = data['feedback_type']
        analytics['feedback_by_type'][feedback_type] = analytics['feedback_by_type'].get(feedback_type, 0) + 1
        
        analytics['last_feedback_date'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'feedback_id': feedback_id,
            'message': 'Feedback submitted successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/<user_id>', methods=['GET'])
def get_user_feedback(user_id):
    """Get all feedback for a specific user"""
    try:
        user_feedbacks = [fb for fb in feedbacks.values() if fb['user_id'] == user_id]
        
        # Sort by creation date (newest first)
        user_feedbacks.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({
            'success': True,
            'feedbacks': user_feedbacks,
            'count': len(user_feedbacks)
        })

    except Exception as e:
        logger.error(f"Error getting user feedback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/<feedback_id>', methods=['PUT'])
def update_feedback_status(feedback_id):
    """Update feedback status (for admin use)"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'status is required'}), 400

        if feedback_id not in feedbacks:
            return jsonify({'error': 'Feedback not found'}), 404

        valid_statuses = ['pending', 'reviewed', 'resolved']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Status must be one of: {valid_statuses}'}), 400

        feedbacks[feedback_id]['status'] = data['status']
        feedbacks[feedback_id]['updated_at'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'feedback': feedbacks[feedback_id]
        })

    except Exception as e:
        logger.error(f"Error updating feedback status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback/analytics', methods=['GET'])
def get_feedback_analytics():
    """Get overall feedback analytics"""
    try:
        # Calculate overall analytics
        total_feedback = len(feedbacks)
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
        total_rating = sum(fb['rating'] for fb in feedbacks.values())
        average_rating = total_rating / total_feedback

        # Group by type
        feedback_by_type = {}
        for fb in feedbacks.values():
            fb_type = fb['feedback_type']
            feedback_by_type[fb_type] = feedback_by_type.get(fb_type, 0) + 1

        # Group by status
        feedback_by_status = {}
        for fb in feedbacks.values():
            status = fb['status']
            feedback_by_status[status] = feedback_by_status.get(status, 0) + 1

        # Get recent feedback (last 10)
        recent_feedback = sorted(
            list(feedbacks.values()),
            key=lambda x: x['created_at'],
            reverse=True
        )[:10]

        analytics = {
            'total_feedback': total_feedback,
            'average_rating': round(average_rating, 2),
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
        if user_id not in feedback_analytics:
            return jsonify({
                'success': True,
                'analytics': {
                    'total_feedback': 0,
                    'average_rating': 0.0,
                    'feedback_by_type': {},
                    'last_feedback_date': None
                }
            })

        return jsonify({
            'success': True,
            'analytics': feedback_analytics[user_id]
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

        # Filter feedbacks
        filtered_feedbacks = list(feedbacks.values())

        if start_date:
            filtered_feedbacks = [
                fb for fb in filtered_feedbacks 
                if fb['created_at'] >= start_date
            ]

        if end_date:
            filtered_feedbacks = [
                fb for fb in filtered_feedbacks 
                if fb['created_at'] <= end_date
            ]

        if feedback_type:
            filtered_feedbacks = [
                fb for fb in filtered_feedbacks 
                if fb['feedback_type'] == feedback_type
            ]

        if status:
            filtered_feedbacks = [
                fb for fb in filtered_feedbacks 
                if fb['status'] == status
            ]

        # Generate report
        report = {
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'feedback_type': feedback_type,
                'status': status
            },
            'summary': {
                'total_feedback': len(filtered_feedbacks),
                'average_rating': round(
                    sum(fb['rating'] for fb in filtered_feedbacks) / len(filtered_feedbacks), 2
                ) if filtered_feedbacks else 0,
                'feedback_by_type': {},
                'feedback_by_status': {}
            },
            'feedbacks': filtered_feedbacks
        }

        # Calculate breakdowns
        for fb in filtered_feedbacks:
            fb_type = fb['feedback_type']
            fb_status = fb['status']
            
            report['summary']['feedback_by_type'][fb_type] = \
                report['summary']['feedback_by_type'].get(fb_type, 0) + 1
            report['summary']['feedback_by_status'][fb_status] = \
                report['summary']['feedback_by_status'].get(fb_status, 0) + 1

        return jsonify({
            'success': True,
            'report': report
        })

    except Exception as e:
        logger.error(f"Error generating feedback report: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
