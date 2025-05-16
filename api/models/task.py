from datetime import datetime
from typing import List
from database import db
from .base import task_employee

class Task(db.Model):
    __tablename__ = 'tasks'
    __table_args__ = (
        db.Index('idx_task_project_id', 'project_id'),
        db.Index('idx_task_status', 'status'),
        db.Index('idx_task_name', 'name'),
        db.Index('idx_task_created_at', 'created_at'),
        {'schema': 'mercor'}
    )
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(120), nullable=False)
    description: str = db.Column(db.Text)
    status: str = db.Column(db.String(20), default='pending')
    project_id: int = db.Column(db.Integer, db.ForeignKey('mercor.projects.id'), nullable=False)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    minutes_spent = db.Column(db.Integer, default=0)  # Total minutes spent on the task
    
    # Relationships
    project = db.relationship('Project', back_populates='tasks')
    employees = db.relationship('Employee', secondary=task_employee, back_populates='tasks')
    time_logs  = db.relationship('TimeLog', back_populates='task')
