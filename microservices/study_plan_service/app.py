from flask import Flask, request, jsonify
from datetime import datetime
import json
import re
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory storage for study plans (in production, use a database)
study_plans = {}
study_plan_items = {}

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for study plan service"""
    return jsonify({
        'service': 'study-plan-service',
        'status': 'running',
        'description': 'Study Plan Service for managing student study plans',
        'available_endpoints': {
            'health': '/health',
            'create_plan': '/study-plans (POST)',
            'get_plan': '/study-plans/<user_id> (GET)',
            'add_item': '/study-plans/<user_id>/items (POST)',
            'update_item': '/study-plans/<user_id>/items/<item_id> (PUT)',
            'delete_item': '/study-plans/<user_id>/items/<item_id> (DELETE)',
            'get_schedule': '/study-plans/<user_id>/schedule (GET)'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'study-plan-service'
    })

@app.route('/study-plans', methods=['POST'])
def create_study_plan():
    """Create a new study plan for a user"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'user_id is required'}), 400

        # Convert user_id to int for consistency
        try:
            user_id = int(data['user_id'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id'}), 400
        
        # Check if user already has a study plan
        if user_id in study_plans:
            return jsonify({'error': 'Study plan already exists for this user'}), 409

        # Create new study plan
        study_plan = {
            'id': f"sp_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        study_plans[user_id] = study_plan
        study_plan_items[user_id] = []

        return jsonify({
            'success': True,
            'study_plan': study_plan
        }), 201

    except Exception as e:
        logger.error(f"Error creating study plan: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/study-plans/<user_id>', methods=['GET'])
def get_study_plan(user_id):
    """Get study plan for a user"""
    try:
        # Convert user_id from string to int to match add_study_plan_item
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id'}), 400
        
        if user_id not in study_plans:
            return jsonify({'error': 'Study plan not found'}), 404

        study_plan = study_plans[user_id]
        items = study_plan_items.get(user_id, [])

        return jsonify({
            'success': True,
            'study_plan': study_plan,
            'items': items
        })

    except Exception as e:
        logger.error(f"Error getting study plan: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/study-plans/<user_id>/items', methods=['POST'])
def add_study_plan_item(user_id):
    """Add an item to study plan"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Use user_id from URL path, not from data
        # Convert user_id from string to int if needed
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id'}), 400

        required_fields = ['item_type', 'item_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Auto-create study plan if it doesn't exist
        if user_id not in study_plans:
            logger.info(f"Auto-creating study plan for user {user_id}")
            study_plan = {
                'id': f"sp_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            study_plans[user_id] = study_plan
            study_plan_items[user_id] = []

        # Check if item already exists
        existing_item = next(
            (item for item in study_plan_items[user_id] 
             if item['item_type'] == data['item_type'] and item['item_id'] == data['item_id']),
            None
        )
        
        if existing_item:
            return jsonify({'error': 'Item already exists in study plan'}), 409

        # Create new study plan item
        item = {
            'id': f"item_{len(study_plan_items[user_id]) + 1}",
            'user_id': user_id,
            'item_type': data['item_type'],
            'item_id': data['item_id'],
            'name': data['name'],
            'subject': data.get('subject', ''),
            'grade': data.get('grade', ''),
            'method': data.get('method', ''),
            'time_slots': data.get('time_slots', ''),
            'created_at': datetime.now().isoformat()
        }

        study_plan_items[user_id].append(item)
        
        # Update study plan timestamp
        study_plans[user_id]['updated_at'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'item': item
        }), 201

    except Exception as e:
        logger.error(f"Error adding study plan item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/study-plans/<user_id>/items/<item_id>', methods=['PUT'])
def update_study_plan_item(user_id, item_id):
    """Update a study plan item"""
    try:
        # Convert user_id from string to int
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        if user_id not in study_plans:
            return jsonify({'error': 'Study plan not found'}), 404

        # Find the item
        item = next(
            (item for item in study_plan_items[user_id] if item['id'] == item_id),
            None
        )
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Update item fields
        for field in ['name', 'subject', 'grade', 'method', 'time_slots']:
            if field in data:
                item[field] = data[field]

        item['updated_at'] = datetime.now().isoformat()
        
        # Update study plan timestamp
        study_plans[user_id]['updated_at'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'item': item
        })

    except Exception as e:
        logger.error(f"Error updating study plan item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/study-plans/<user_id>/items/<item_id>', methods=['DELETE'])
def delete_study_plan_item(user_id, item_id):
    """Delete a study plan item"""
    try:
        # Convert user_id from string to int
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id'}), 400
        
        if user_id not in study_plans:
            return jsonify({'error': 'Study plan not found'}), 404

        # Find and remove the item
        items = study_plan_items[user_id]
        item = next((item for item in items if item['id'] == item_id), None)
        
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        items.remove(item)
        
        # Update study plan timestamp
        study_plans[user_id]['updated_at'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': 'Item deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting study plan item: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/study-plans/<user_id>/schedule', methods=['GET'])
def get_study_schedule(user_id):
    """Get sorted study schedule for a user"""
    try:
        # Convert user_id from string to int
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid user_id'}), 400
        
        if user_id not in study_plans:
            return jsonify({'error': 'Study plan not found'}), 404

        items = study_plan_items.get(user_id, [])
        
        # Sort items by time
        sorted_items = sort_items_by_time(items)

        return jsonify({
            'success': True,
            'schedule': sorted_items
        })

    except Exception as e:
        logger.error(f"Error getting study schedule: {str(e)}")
        return jsonify({'error': str(e)}), 500

def parse_time_slot(time_slot):
    """Parse time slot string into start time (minutes), end time (minutes), and day (integer)."""
    try:
        day_map = {
            'thứ 2': 2, 'thứ hai': 2, '2': 2,
            'thứ 3': 3, 'thứ ba': 3, '3': 3,
            'thứ 4': 4, 'thứ tư': 4, '4': 4,
            'thứ 5': 5, 'thứ năm': 5, '5': 5,
            'thứ 6': 6, 'thứ sáu': 6, '6': 6,
            'thứ 7': 7, 'thứ bảy': 7, '7': 7
        }

        if not time_slot or not time_slot.strip():
            return None, None, None

        time_parts = time_slot.lower().split('thứ')
        if len(time_parts) < 2:
            return None, None, None
            
        time_part = time_parts[0].strip()
        day_part = time_parts[1].strip()
        
        day = day_map.get(f'thứ {day_part}')
        if not day and day_part.isdigit():
            day = int(day_part)
            if day < 2 or day > 7:
                return None, None, None
        if not day:
            return None, None, None

        if '-' in time_part:
            start, end = time_part.split('-')
            start_minutes = time_to_minutes(start.strip())
            end_minutes = time_to_minutes(end.strip())
        else:
            start_minutes = time_to_minutes(time_part.strip())
            end_minutes = start_minutes + 60
            
        return start_minutes, end_minutes, day
    except Exception as e:
        logger.error(f"Error parsing time slot: {e}")
        return None, None, None

def time_to_minutes(time_str):
    """Convert time string (e.g., '7h45' or '7:45') to minutes since midnight."""
    time_str = time_str.replace('h', ':').strip()
    if ':' not in time_str:
        time_str = f"{time_str}:00"
        
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except Exception as e:
        logger.error(f"Error converting time to minutes: {e}")
        return 0

def sort_items_by_time(items):
    """Sort all items by day and precise start time."""
    sorted_items = []
    day_names = {2: "Hai", 3: "Ba", 4: "Tư", 5: "Năm", 6: "Sáu", 7: "Bảy"}

    for item in items:
        if item.get('time_slots'):
            try:
                time_slots_raw = item['time_slots']
                
                # Handle different formats: JSON array, string array, or single string
                if isinstance(time_slots_raw, str):
                    # Try to parse as JSON array first
                    try:
                        time_slots = json.loads(time_slots_raw)
                        if not isinstance(time_slots, list):
                            # If not a list, treat as single string
                            time_slots = [time_slots_raw]
                    except (json.JSONDecodeError, ValueError):
                        # If not JSON, treat as single string or check if it's a valid time slot
                        if time_slots_raw.strip():
                            time_slots = [time_slots_raw]
                        else:
                            time_slots = []
                elif isinstance(time_slots_raw, list):
                    time_slots = time_slots_raw
                else:
                    time_slots = []
                
                # Process each time slot
                for slot in time_slots:
                    if not slot or not isinstance(slot, str):
                        continue
                    
                    start, end, day = parse_time_slot(slot.strip())
                    if start is not None:
                        sorted_items.append({
                            'item': item,
                            'start': start,
                            'end': end,
                            'day': day,
                            'day_name': day_names.get(day, ""),
                            'time_slot': slot.strip(),
                            'type': item.get('item_type', '')
                        })
            except Exception as e:
                logger.error(f"Error parsing time slots for item {item.get('id', 'unknown')}: {e}")
                continue

    return sorted(sorted_items, key=lambda x: (x['day'], x['start']))

if __name__ == '__main__':
    try:
        logger.info("Initializing Study Plan Service...")
        logger.info(f"Study Plan Service starting on port 5002")
        
        # Disable debug mode in Docker to prevent auto-restart
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(host='0.0.0.0', port=5002, debug=debug_mode)
    except Exception as e:
        logger.error(f"Failed to start Study Plan Service: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
