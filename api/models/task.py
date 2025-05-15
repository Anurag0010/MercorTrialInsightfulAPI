from datetime import datetime
from database import db
from .base import task_employee

class Task(db.Model):
    __tablename__ = 'tasks'
    __table_args__ = {'schema': 'mercor'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    project_id = db.Column(db.Integer, db.ForeignKey('mercor.projects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', back_populates='tasks')
    employees = db.relationship('Employee', secondary=task_employee, back_populates='tasks')
    time_logs = db.relationship('TimeLog', back_populates='task')
