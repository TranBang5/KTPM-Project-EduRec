from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Course(db.Model):
    """Course model for catalog service"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade_level = db.Column(db.String(20), nullable=False)
    schedule = db.Column(db.String(100))
    address = db.Column(db.String(200))
    teaching_method = db.Column(db.String(20))  # online/offline
    cost = db.Column(db.Float)
    teaching_time = db.Column(db.String(100))  # Thời gian giảng dạy
    location = db.Column(db.String(200))  # Địa điểm
    
    def __repr__(self):
        return f'<Course {self.name}>'

class Tutor(db.Model):
    """Tutor model for catalog service"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    schedule = db.Column(db.String(100))
    specialized_grade = db.Column(db.String(20))
    teaching_experience = db.Column(db.Integer)  # years
    teaching_method = db.Column(db.String(20))  # online/offline
    teaching_time = db.Column(db.String(200))  # Thời gian giảng dạy
    experience = db.Column(db.Integer)  # Kinh nghiệm
    
    def __repr__(self):
        return f'<Tutor {self.name}>'

class Material(db.Model):
    """Material model for catalog service"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade_level = db.Column(db.String(20))
    material_type = db.Column(db.String(20))  # paper/digital
    description = db.Column(db.Text)  # Mô tả
    
    def __repr__(self):
        return f'<Material {self.name}>'

