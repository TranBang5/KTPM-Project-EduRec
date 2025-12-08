from flask import Flask, request, jsonify
import tensorflow as tf
import pandas as pd
import numpy as np
import os
import json
import sys
import threading

# Add parent directory to path to import models
sys.path.append('/app')

try:
    from models.recommender import RecommendationModel, load_and_preprocess_data
    import logging
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure models directory is mounted correctly")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Disable debug mode in production
app.config['DEBUG'] = False

# Model configuration
WEIGHTS_DIR = os.getenv('WEIGHTS_DIR', '/app/checkpoints')
BRUTEFORCE_DATA_PATH = os.getenv('BRUTEFORCE_DATA_PATH', '/app/bruteforce_data.npz')

# Global model variable and lock for thread-safe loading
model = None
model_lock = threading.Lock()
model_loading = False

def initialize_model():
    """Initialize the recommendation model"""
    global model
    try:
        logger.info("Loading preprocessed data...")
        data = load_and_preprocess_data()
        logger.info("Data loaded successfully")

        logger.info("Initializing recommendation model...")
        model = RecommendationModel(
            student_features=data['student_data'],
            course_features=data['course_data'],
            tutor_features=data['tutor_data'],
            material_features=data['material_data'],
            student_course_train=data['student_course_train'],
            student_tutor_train=data['student_tutor_train'],
            student_material_train=data['student_material_train'],
            subject_vocab=data['subject_vocab'],
            grade_vocab=data['grade_vocab'],
            material_type_vocab=data['material_type_vocab'],
            teaching_time_vocab=data['teaching_time_vocab'],
            bruteforce_data_path=BRUTEFORCE_DATA_PATH
        )
        logger.info("Model initialized successfully")

        # Load model weights
        checkpoint = tf.train.Checkpoint(model=model)
        latest_checkpoint = tf.train.latest_checkpoint(WEIGHTS_DIR)
        if latest_checkpoint:
            checkpoint.restore(latest_checkpoint)
            logger.info(f"Model weights loaded from {latest_checkpoint}")
        else:
            logger.warning(f"No checkpoint found in {WEIGHTS_DIR}")

        # Load BruteForce data if available
        if os.path.exists(BRUTEFORCE_DATA_PATH):
            model.load_bruteforce_data(BRUTEFORCE_DATA_PATH)
            logger.info("BruteForce data loaded successfully")
        else:
            logger.warning("BruteForce data not found, will be created on first request")

    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@app.route('/', methods=['GET'])
def index():
    """Root endpoint for recommendation service"""
    return jsonify({
        'service': 'recommendation-service',
        'status': 'running',
        'description': 'Recommendation Service for generating study plan recommendations',
        'available_endpoints': {
            'health': '/health',
            'generate': '/recommendations/generate (POST)',
            'model_info': '/recommendations/models (GET)'
        },
        'model_loaded': model is not None
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'recommendation-service',
        'model_loaded': model is not None
    })

def ensure_model_loaded():
    """Ensure model is loaded, load it if not (thread-safe)"""
    global model, model_loading
    
    # Fast path: model already loaded
    if model is not None:
        return
    
    # Acquire lock to prevent concurrent initialization
    with model_lock:
        # Double-check after acquiring lock
        if model is not None:
            return
        
        # Check if another thread is already loading
        if model_loading:
            logger.warning("Model is being loaded by another thread, waiting...")
            # Wait for model to be loaded (with timeout)
            import time
            max_wait = 300  # 5 minutes max wait
            wait_time = 0
            while model_loading and wait_time < max_wait:
                time.sleep(1)
                wait_time += 1
                if model is not None:
                    logger.info("Model loaded by another thread")
                    return
            
            if model is None:
                raise Exception("Model loading timeout or failed")
            return
        
        # Mark as loading
        model_loading = True
        try:
            logger.info("Model not loaded, initializing now...")
            initialize_model()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model on demand: {str(e)}")
            raise
        finally:
            model_loading = False

@app.route('/recommendations/generate', methods=['POST'])
def generate_recommendations():
    """Generate recommendations for a user"""
    try:
        # Load model if not already loaded (lazy loading)
        try:
            ensure_model_loaded()
        except Exception as e:
            logger.error(f"Model loading error: {str(e)}")
            return jsonify({'error': 'Model not available'}), 503
        
        if model is None:
            return jsonify({'error': 'Model not initialized'}), 503

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract user features with defaults
        user_features = {
            'truong_hoc_hien_tai': str(data.get('school', '')).strip().lower() or 'unknown',
            'khoi_lop_hien_tai': str(data.get('current_grade', '')).strip().lower() or 'unknown',
            'muc_tieu_hoc': str(data.get('learning_goals', '')).strip().lower() or 'unknown',
            'mon_hoc_yeu_thich': str(data.get('favorite_subjects', '')).strip().lower() or 'unknown',
            'phuong_phap_hoc_yeu_thich': str(data.get('preferred_learning_method', '')).strip().lower() or 'unknown'
        }

        # Convert to model input format with error handling
        try:
            user_data = {k: tf.convert_to_tensor([v.encode('utf-8')], dtype=tf.string) for k, v in user_features.items()}
            user_dataset = tf.data.Dataset.from_tensor_slices(user_data).batch(1)
        except Exception as e:
            logger.error(f"Error preparing model input: {str(e)}")
            return jsonify({'error': 'Invalid input data'}), 400

        # Get recommendations with error handling
        try:
            recommendations_result = None
            for batch in user_dataset:
                student_embeddings = model.student_model(batch)
                if model.bruteforce is None:
                    logger.error("Bruteforce model not loaded")
                    return jsonify({'error': 'Recommendation model not ready'}), 503
                scores, top_k_ids = model.bruteforce(student_embeddings)
                scores = scores.numpy()[0]
                top_k_ids = top_k_ids.numpy().astype(str)[0]
                recommendations_result = (scores, top_k_ids)
                break
            
            if recommendations_result is None:
                return jsonify({'error': 'Failed to generate recommendations'}), 500
            
            scores, top_k_ids = recommendations_result
        except Exception as e:
            logger.error(f"Error during model inference: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Failed to generate recommendations'}), 500

        # Process recommendations
        recommendations = {'courses': [], 'tutors': [], 'materials': []}
        item_scores = {}
        
        try:
            for id_, score in zip(top_k_ids, scores):
                item_scores[str(id_)] = float(score)
        except Exception as e:
            logger.error(f"Error processing recommendation scores: {str(e)}")
            return jsonify({'error': 'Failed to process recommendations'}), 500

        # Categorize recommendations
        for item_id, score in item_scores.items():
            if item_id.startswith('course_'):
                recommendations['courses'].append({
                    'id': item_id,
                    'score': score
                })
            elif item_id.startswith('tutor_'):
                recommendations['tutors'].append({
                    'id': item_id,
                    'score': score
                })
            elif item_id.startswith('material_'):
                recommendations['materials'].append({
                    'id': item_id,
                    'score': score
                })

        # Sort by score
        for category in recommendations:
            recommendations[category].sort(key=lambda x: x['score'], reverse=True)

        return jsonify({
            'success': True,
            'recommendations': recommendations
        })

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/recommendations/models', methods=['GET'])
def get_model_info():
    """Get information about the loaded model"""
    try:
        # Load model if not already loaded (lazy loading)
        ensure_model_loaded()
        
        if model is None:
            return jsonify({'error': 'Model not initialized'}), 500

        return jsonify({
            'success': True,
            'model_info': {
                'subject_vocab_size': len(model.subject_vocab),
                'grade_vocab_size': len(model.grade_vocab),
                'material_type_vocab_size': len(model.material_type_vocab),
                'teaching_time_vocab_size': len(model.teaching_time_vocab),
                'bruteforce_loaded': model.bruteforce is not None
            }
        })

    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check if model should be loaded at startup
    LOAD_MODEL_ON_STARTUP = os.getenv('LOAD_MODEL_ON_STARTUP', 'true').lower() == 'true'
    
    if LOAD_MODEL_ON_STARTUP:
        try:
            logger.info("Loading model at startup (LOAD_MODEL_ON_STARTUP=true)...")
            initialize_model()
            logger.info("Model loaded successfully at startup")
        except Exception as e:
            logger.error(f"Failed to load model at startup: {str(e)}")
            logger.warning("Service will start without model. Model will be loaded on first request.")
    else:
        logger.info("Skipping model loading at startup (LOAD_MODEL_ON_STARTUP=false)")
        logger.info("Model will be loaded on first request")
    
    # Disable debug mode in Docker to prevent auto-restart
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
