from datetime import datetime
from database import db

class Screenshot(db.Model):
    __tablename__ = 'screenshots'
    __table_args__ = {'schema': 'mercor'}
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)
    captured_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    employee_id = db.Column(db.Integer, db.ForeignKey('mercor.employees.id'), nullable=False)
    
    # Relationships
    employee = db.relationship('Employee', back_populates='screenshots')
