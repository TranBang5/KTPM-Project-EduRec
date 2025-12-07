from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class StudyPlan(db.Model):
    """Study Plan model for study plan service"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Reference to auth service user_id
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('StudyPlanItem', backref='study_plan', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudyPlan {self.id} for User {self.user_id}>'

class StudyPlanItem(db.Model):
    """Study Plan Item model"""
    id = db.Column(db.Integer, primary_key=True)
    study_plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Denormalized for easier querying
    item_type = db.Column(db.String(20), nullable=False)  # 'course', 'tutor', or 'material'
    item_id = db.Column(db.String(100), nullable=False)  # ID from catalog service
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    method = db.Column(db.String(20))  # Optional, for courses and tutors
    time_slots = db.Column(db.Text)  # JSON string of time slots
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyPlanItem {self.id} - {self.item_type}>'

