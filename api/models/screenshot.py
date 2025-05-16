from datetime import datetime
from typing import Optional
from database import db

# DEPRECATED: Screenshot model is now merged into TimeLog. This file is retained for migration reference only.
# class Screenshot(db.Model):
    __tablename__ = 'screenshots'
    __table_args__ = (
        db.Index('idx_screenshot_employee', 'employee_id'),
        db.Index('idx_screenshot_project', 'project_id'),
        db.Index('idx_screenshot_task', 'task_id'),
        db.Index('idx_screenshot_captured_at', 'captured_at'),
        # Composite indexes for common query patterns
        db.Index('idx_screenshot_employee_date', 'employee_id', 'captured_at'),
        db.Index('idx_screenshot_project_date', 'project_id', 'captured_at'),
        {'schema': 'mercor'}
    )
    id: int = db.Column(db.Integer, primary_key=True)
    file_path: str = db.Column(db.String(255), nullable=False)
    image_url: str = db.Column(db.String(512), nullable=True)  # Adding URL field for access
    captured_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    employee_id: int = db.Column(db.Integer, db.ForeignKey('mercor.employees.id'), nullable=False)
    project_id: int = db.Column(db.Integer, db.ForeignKey('mercor.projects.id'), nullable=False)
    task_id: int = db.Column(db.Integer, db.ForeignKey('mercor.tasks.id'), nullable=False)
    
    # Relationships
    employee = db.relationship('Employee', back_populates='screenshots')
    project = db.relationship('Project', back_populates='screenshots')
    task = db.relationship('Task', back_populates='screenshots')
