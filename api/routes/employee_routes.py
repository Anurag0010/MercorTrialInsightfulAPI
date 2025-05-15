from flask import jsonify, request
from api.models.employee import Employee
from database import db
from . import employee_bp

@employee_bp.route('/employees', methods=['GET'])
def list_employees():
    """Get all employees"""
    employees = Employee.query.all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'email': e.email,
        'project_count': len(e.projects),
        'task_count': len(e.tasks)
    } for e in employees])

@employee_bp.route('/employees', methods=['POST'])
def create_employee():
    """Create a new employee"""
    data = request.json
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({'error': 'Name and email are required'}), 400
    
    # Check if email already exists
    if Employee.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    employee = Employee(
        name=data['name'],
        email=data['email'],
        role=data.get('role')
    )
    
    db.session.add(employee)
    db.session.commit()
    
    return jsonify({
        'id': employee.id,
        'name': employee.name,
        'email': employee.email,
        'role': employee.role
    }), 201

@employee_bp.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get a specific employee by ID"""
    employee = Employee.query.get_or_404(employee_id)
    return jsonify({
        'id': employee.id,
        'name': employee.name,
        'email': employee.email,
        'role': employee.role,
        'projects': [{
            'id': p.id,
            'name': p.name
        } for p in employee.projects],
        'tasks': [{
            'id': t.id,
            'title': t.title,
            'status': t.status
        } for t in employee.tasks]
    })

@employee_bp.route('/employees/<int:employee_id>', methods=['PUT', 'PATCH'])
def update_employee(employee_id):
    """Update an employee"""
    employee = Employee.query.get_or_404(employee_id)
    data = request.json
    
    if data.get('name'):
        employee.name = data['name']
    if data.get('email'):
        # Check if new email already exists for another employee
        existing = Employee.query.filter_by(email=data['email']).first()
        if existing and existing.id != employee_id:
            return jsonify({'error': 'Email already registered'}), 400
        employee.email = data['email']
    if 'role' in data:
        employee.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'id': employee.id,
        'name': employee.name,
        'email': employee.email,
        'role': employee.role
    })

@employee_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete an employee"""
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return '', 204

@employee_bp.route('/employees/<int:employee_id>/projects', methods=['GET'])
def get_employee_projects(employee_id):
    """Get all projects for an employee"""
    employee = Employee.query.get_or_404(employee_id)
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'task_count': len(p.tasks)
    } for p in employee.projects])
