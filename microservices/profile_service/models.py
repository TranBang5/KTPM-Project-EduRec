from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserProfile(db.Model):
    """User Profile model for profile service"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)  # Reference to auth service user_id
    email = db.Column(db.String(120))
    full_name = db.Column(db.String(100))
    school = db.Column(db.String(200))
    current_grade = db.Column(db.String(50))
    favorite_subjects = db.Column(db.String(500))
    learning_goals = db.Column(db.String(200))
    preferred_learning_method = db.Column(db.String(200))
    avatar_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfile {self.user_id}>'

