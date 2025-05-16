from datetime import datetime, timedelta
import uuid
from database import db
from typing import Dict, Any, Optional


class ActivationToken(db.Model):
    """Model to store activation tokens for employee registration"""
    __tablename__ = 'activation_tokens'
    __table_args__ = (
        db.Index('idx_activation_token', 'token', unique=True),
        db.Index('idx_activation_email', 'email', unique=True),
        {'schema': 'mercor'}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    employee_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    @staticmethod
    def generate_token(email: str, employee_id: int, expiry_hours: int = 48) -> str:
        """
        Generate a unique token for account activation
        
        Args:
            email: The email address of the employee
            employee_id: The ID of the employee
            expiry_hours: Number of hours the token is valid for (default: 48)
            
        Returns:
            The generated token string
        """
        # Delete any existing tokens for this email
        ActivationToken.query.filter_by(email=email).delete()
        
        # Generate a new token
        token = str(uuid.uuid4())
        
        # Calculate expiry date
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        # Create and save the activation token
        activation_token = ActivationToken(
            token=token,
            email=email,
            employee_id=employee_id,
            expires_at=expires_at
        )
        
        db.session.add(activation_token)
        db.session.commit()
        
        return token
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a token and return associated data if valid
        
        Args:
            token: The token string to validate
            
        Returns:
            A dictionary with token data if valid, None otherwise
        """
        activation_token = ActivationToken.query.filter_by(token=token, used=False).first()
        
        if not activation_token:
            return None
            
        if activation_token.expires_at < datetime.utcnow():
            return None
            
        return {
            'id': activation_token.id,
            'email': activation_token.email,
            'project_id': activation_token.project_id,
            'created_at': activation_token.created_at,
            'expires_at': activation_token.expires_at
        }
    
    @staticmethod
    def mark_used(token: str) -> bool:
        """
        Mark a token as used
        
        Args:
            token: The token string to mark as used
            
        Returns:
            True if token was found and marked, False otherwise
        """
        activation_token = ActivationToken.query.filter_by(token=token, used=False).first()
        
        if not activation_token:
            return False
            
        activation_token.used = True
        db.session.commit()
        
        return True