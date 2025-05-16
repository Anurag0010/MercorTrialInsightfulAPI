from datetime import datetime
from typing import Optional
from database import db

class TimeLog(db.Model):
    """
    Unified model for time tracking and screenshot logging.
    Stores time log data and (optionally) screenshot metadata and file info for each time log entry.
    """
    __tablename__ = 'time_logs'
    __table_args__ = (
        db.Index('idx_time_logs_employee_id', 'employee_id'),
        db.Index('idx_time_logs_project_id', 'project_id'),
        db.Index('idx_time_logs_task_id', 'task_id'),
        db.Index('idx_time_logs_start_time', 'start_time'),
        db.Index('idx_time_logs_end_time', 'end_time'),
        db.Index('idx_time_logs_screenshot_permission', 'is_screenshot_permission_enabled'),
        db.Index('idx_time_logs_captured_at', 'captured_at'),
        {'schema': 'mercor'}
    )
    id: int = db.Column(db.Integer, primary_key=True)
    start_time: datetime = db.Column(db.DateTime, nullable=False)
    end_time: datetime = db.Column(db.DateTime, nullable=False)
    duration: int = db.Column(db.Integer, nullable=False)  # in seconds

    # Screenshot fields (optional)
    file_path: str = db.Column(db.String(255), nullable=True)
    image_url: str = db.Column(db.String(512), nullable=True)
    captured_at: datetime = db.Column(db.DateTime, nullable=True)

    # Tracking permissions and network info
    is_screenshot_permission_enabled: bool = db.Column(db.Boolean, default=True, nullable=False)
    ip_address: str = db.Column(db.String(45), nullable=True)
    mac_address: str = db.Column(db.String(17), nullable=True)

    # Foreign Keys
    employee_id: int = db.Column(db.Integer, db.ForeignKey('mercor.employees.id'), nullable=False)
    project_id: int = db.Column(db.Integer, db.ForeignKey('mercor.projects.id'), nullable=False)
    task_id: int = db.Column(db.Integer, db.ForeignKey('mercor.tasks.id'), nullable=False)

    # Relationships
    employee = db.relationship('Employee', back_populates='time_logs')
    project = db.relationship('Project', back_populates='time_logs')
    task = db.relationship('Task', back_populates='time_logs')
