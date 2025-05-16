from datetime import datetime
from typing import Dict, Any, Optional
from database import db
from passlib.hash import bcrypt

class Admin(db.Model):
    """Admin model for system administrators"""
    __tablename__ = 'admins'
    __table_args__ = (
        db.Index('idx_admin_email', 'email', unique=True),
        {'schema': 'mercor'}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<Admin {self.email}>'
    
    def set_password(self, password: str) -> None:
        """Set the password hash for the admin"""
        self.password_hash = bcrypt.hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash"""
        return bcrypt.verify(password, self.password_hash)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert admin object to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }