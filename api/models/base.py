from database import db
from datetime import datetime

# Association tables for many-to-many relationships
project_employee = db.Table('project_employee',
    db.Column('project_id', db.Integer, db.ForeignKey('mercor.projects.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('mercor.employees.id'), primary_key=True),
    schema='mercor'
)

task_employee = db.Table('task_employee',
    db.Column('task_id', db.Integer, db.ForeignKey('mercor.tasks.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('mercor.employees.id'), primary_key=True),
    schema='mercor'
)
