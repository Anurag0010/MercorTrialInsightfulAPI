from datetime import datetime
from database import db

class TimeLog(db.Model):
    __tablename__ = 'time_logs'
    __table_args__ = {'schema': 'mercor'}
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in seconds
    
    # Foreign Keys
    employee_id = db.Column(db.Integer, db.ForeignKey('mercor.employees.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('mercor.projects.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('mercor.tasks.id'), nullable=False)
    
    # Relationships
    employee = db.relationship('Employee', back_populates='time_logs')
    project = db.relationship('Project', back_populates='time_logs')
    task = db.relationship('Task', back_populates='time_logs')
