from datetime import datetime
from app import db

# Association tables for many-to-many relationships
project_employee = db.Table('project_employee',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('employees.id'), primary_key=True)
)

task_employee = db.Table('task_employee',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('employees.id'), primary_key=True)
)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    profile_image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    projects = db.relationship('Project', secondary=project_employee, back_populates='employees')
    tasks = db.relationship('Task', secondary=task_employee, back_populates='employees')
    time_logs = db.relationship('TimeLog', back_populates='employee')
    screenshots = db.relationship('Screenshot', back_populates='employee')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'active': self.active,
            'profile_image_url': self.profile_image_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    employees = db.relationship('Employee', secondary=project_employee, back_populates='projects')
    tasks = db.relationship('Task', back_populates='project')
    time_logs = db.relationship('TimeLog', back_populates='project')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    project = db.relationship('Project', back_populates='tasks')
    employees = db.relationship('Employee', secondary=task_employee, back_populates='tasks')
    time_logs = db.relationship('TimeLog', back_populates='task')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class TimeLog(db.Model):
    __tablename__ = 'timelogs'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    employee = db.relationship('Employee', back_populates='time_logs')
    project = db.relationship('Project', back_populates='time_logs')
    task = db.relationship('Task', back_populates='time_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'project_id': self.project_id,
            'task_id': self.task_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class Screenshot(db.Model):
    __tablename__ = 'screenshots'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    taken_at = db.Column(db.DateTime, nullable=False)
    permission_flag = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    employee = db.relationship('Employee', back_populates='screenshots')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'image_url': self.image_url,
            'taken_at': self.taken_at.isoformat(),
            'permission_flag': self.permission_flag,
            'created_at': self.created_at.isoformat()
        }
