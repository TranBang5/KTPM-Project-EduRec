from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication service"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Student profile
    school = db.Column(db.String(200))
    current_grade = db.Column(db.String(50))
    favorite_subjects = db.Column(db.String(500))
    learning_goals = db.Column(db.String(200))
    preferred_learning_method = db.Column(db.String(200))
    
    # Password reset
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)
    
    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.email}>'

