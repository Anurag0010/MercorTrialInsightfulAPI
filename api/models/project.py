from datetime import datetime
from database import db
from .base import project_employee

class Project(db.Model):
    __tablename__ = 'projects'
    __table_args__ = {'schema': 'mercor'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employees = db.relationship('Employee', secondary=project_employee, back_populates='projects')
    tasks = db.relationship('Task', back_populates='project')
    time_logs = db.relationship('TimeLog', back_populates='project')
