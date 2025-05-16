from datetime import datetime
from typing import List, Optional, Dict, Any
from database import db
from .base import project_employee

class Project(db.Model):
    __tablename__ = 'projects'
    __table_args__ = (
        db.Index('idx_project_name', 'name'),
        db.Index('idx_project_created_at', 'created_at'),
        {'schema': 'mercor'}
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # Adding hourly rate
    employer_id = db.Column(db.Integer, db.ForeignKey('mercor.employers.id'), nullable=True)  # Link to employer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employer = db.relationship('Employer', back_populates='projects')  # Relationship to employer
    employees = db.relationship('Employee', secondary=project_employee, back_populates='projects')
    tasks = db.relationship('Task', back_populates='project')
    time_logs = db.relationship('TimeLog', back_populates='project')
    screenshots = db.relationship('Screenshot', back_populates='project')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'employer_id': self.employer_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
