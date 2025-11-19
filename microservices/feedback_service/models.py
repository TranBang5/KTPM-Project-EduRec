from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Feedback(db.Model):
    """Feedback model for feedback service"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Reference to auth service user_id
    feedback_type = db.Column(db.String(50), nullable=False)  # 'general', 'recommendation', 'interface', etc.
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5 star rating
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.id} from User {self.user_id}>'

