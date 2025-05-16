from datetime import datetime
from typing import Dict, Any, Optional, List
from database import db
from .base import project_employee, task_employee
from passlib.hash import bcrypt

from datetime import datetime, timedelta

class Employee(db.Model):
    __tablename__ = 'employees'
    __table_args__ = (
        db.Index('idx_employee_email', 'email', unique=True),
        db.Index('idx_employee_name', 'name'),
        db.Index('idx_employee_active', 'active'),
        db.Index('idx_employee_username', 'username', unique=True),
        {'schema': 'mercor'}
    )
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), nullable=True)
    password_hash: Optional[str] = db.Column(db.String(128), nullable=True)
    name: str = db.Column(db.String(80), nullable=False)
    email: str = db.Column(db.String(120), unique=True, nullable=False)
    active: bool = db.Column(db.Boolean, default=True)
    profile_image_url: Optional[str] = db.Column(db.String(255))
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Activation fields
    activation_token = db.Column(db.String(64), nullable=True, unique=True)
    activation_token_expiry = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False)

    # Device tracking
    latest_mac_address = db.Column(db.String(32), nullable=True)  # Store latest MAC address used for login
    
    # Relationships
    projects = db.relationship('Project', secondary=project_employee, back_populates='employees')
    tasks = db.relationship('Task', secondary=task_employee, back_populates='employees')
    time_logs = db.relationship('TimeLog', back_populates='employee')
    screenshots = db.relationship('Screenshot', back_populates='employee')

    def set_password(self, password: str) -> None:
        """Set password hash for employee"""
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash"""
        if self.password_hash:
            return bcrypt.verify(password, self.password_hash)
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert employee object to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'active': self.active,
            'profile_image_url': self.profile_image_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
