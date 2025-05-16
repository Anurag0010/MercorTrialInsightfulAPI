from datetime import datetime
from typing import Dict, Any, Optional, List
from database import db
from passlib.hash import bcrypt

class Employer(db.Model):
    __tablename__ = 'employers'
    __table_args__ = (
        db.Index('idx_employer_email', 'email', unique=True),
        db.Index('idx_employer_company_name', 'company_name'),
        db.Index('idx_employer_active', 'active'),
        {'schema': 'mercor'}
    )
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    active = db.Column(db.Boolean, default=True)
    profile_image_url = db.Column(db.String(255))
    address = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', back_populates='employer')

    def set_password(self, password: str) -> None:
        """Set password hash for employer"""
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash"""
        return bcrypt.verify(password, self.password_hash)

    def to_dict(self) -> Dict[str, Any]:
        """Convert employer object to dictionary"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'email': self.email,
            'phone': self.phone,
            'active': self.active,
            'profile_image_url': self.profile_image_url,
            'address': self.address,
            'website': self.website,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }