from flask import jsonify, request, current_app
from api.models.employee import Employee
from api.models.employer import Employer
from api.models.project import Project
from api.models.task import Task
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from database import db
from datetime import timedelta
from . import employer_bp

@employer_bp.route('/employers/register', methods=['POST'])
def register_employer():
    """Register a new employer"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Validate required fields
        required_fields = ['company_name', 'contact_name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if email already exists
        if Employer.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email is already registered'}), 409
            
        # Create new employer
        employer = Employer(
            company_name=data['company_name'],
            contact_name=data['contact_name'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address'),
            website=data.get('website'),
            active=True
        )
        employer.set_password(data['password'])
        
        db.session.add(employer)
        db.session.commit()
        
        return jsonify({
            'message': 'Employer registered successfully',
            'employer': employer.to_dict()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f'Error registering employer: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/login', methods=['POST'])
def login_employer():
    """Log in an employer"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
            
        # Find employer by email
        employer = Employer.query.filter_by(email=data['email']).first()
        if not employer or not employer.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
            
        # Check if employer is active
        if not employer.active:
            return jsonify({'error': 'Account is deactivated'}), 403
            
        # Generate tokens
        access_token = create_access_token(
            identity={
                'id': employer.id,
                'role': 'employer',
                'email': employer.email
            },
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity={
                'id': employer.id,
                'role': 'employer',
                'email': employer.email
            }
        )
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'employer': employer.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error during employer login: {str(e)}')
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_employer_token():
    """Refresh the access token for an employer"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        access_token = create_access_token(
            identity=identity,
            expires_delta=timedelta(hours=1)
        )
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error refreshing token: {str(e)}')
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/profile', methods=['GET'])
@jwt_required()
def get_employer_profile():
    """Get employer profile"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        return jsonify(employer.to_dict()), 200
        
    except Exception as e:
        current_app.logger.error(f'Error getting employer profile: {str(e)}')
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/profile', methods=['PUT'])
@jwt_required()
def update_employer_profile():
    """Update employer profile"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Update fields
        if 'company_name' in data:
            employer.company_name = data['company_name']
        if 'contact_name' in data:
            employer.contact_name = data['contact_name']
        if 'phone' in data:
            employer.phone = data['phone']
        if 'address' in data:
            employer.address = data['address']
        if 'website' in data:
            employer.website = data['website']
        if 'profile_image_url' in data:
            employer.profile_image_url = data['profile_image_url']
        if 'password' in data:
            employer.set_password(data['password'])
            
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'employer': employer.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error updating employer profile: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Project Management Routes
@employer_bp.route('/employers/employees', methods=['GET'])
@jwt_required()
def get_employer_employees():
    """Get all employees working on any project of the logged-in employer"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401

        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404

        # Get all projects for this employer
        projects = Project.query.filter_by(employer_id=employer.id).all()
        project_ids = [p.id for p in projects]

        # Get all employees assigned to any of these projects (using association table)
        employees = Employee.query.join(Employee.projects).filter(Project.id.in_(project_ids)).distinct().all()

        return jsonify([emp.to_dict() for emp in employees]), 200
    except Exception as e:
        current_app.logger.error(f'Error getting employer employees: {str(e)}')
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects', methods=['GET'])
@jwt_required()
def get_employer_projects():
    """Get all projects for the employer"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        projects = Project.query.filter_by(employer_id=employer.id).all()
        
        return jsonify([{
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'employee_count': len(project.employees),
            'task_count': len(project.tasks)
        } for project in projects]), 200
        
    except Exception as e:
        current_app.logger.error(f'Error getting employer projects: {str(e)}')
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project for the employer"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        if 'name' not in data:
            return jsonify({'error': 'Project name is required'}), 400
            
        project = Project(
            name=data['name'],
            description=data.get('description'),
            hourly_rate=data.get('hourly_rate'),
            employer_id=employer.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f'Error creating project: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project_detail(project_id):
    """Get details of a specific project"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
            
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'employees': [{
                'id': employee.id,
                'name': employee.name,
                'email': employee.email
            } for employee in project.employees],
            'tasks': [{
                'id': task.id,
                'name': task.name,
                'status': task.status
            } for task in project.tasks]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error getting project details: {str(e)}')
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update a project"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Update fields
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'hourly_rate' in data:
            project.hourly_rate = data['hourly_rate']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Project updated successfully',
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error updating project: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete a project"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
            
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error deleting project: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Task Management Routes
@employer_bp.route('/employers/projects/<int:project_id>/tasks', methods=['GET'])
@jwt_required()
def get_project_tasks(project_id):
    """Get all tasks for a project"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
            
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        return jsonify([{
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'status': task.status,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        } for task in tasks]), 200
        
    except Exception as e:
        current_app.logger.error(f'Error getting project tasks: {str(e)}')
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects/<int:project_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(project_id):
    """Create a new task for a project"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        if 'name' not in data:
            return jsonify({'error': 'Task name is required'}), 400
            
        task = Task(
            name=data['name'],
            description=data.get('description'),
            status=data.get('status', 'pending'),
            project_id=project_id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        current_app.logger.error(f'Error creating task: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects/<int:project_id>/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(project_id, task_id):
    """Update a task"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
            
        task = Task.query.filter_by(id=task_id, project_id=project_id).first()
        if not task:
            return jsonify({'error': 'Task not found or access denied'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Update fields
        if 'name' in data:
            task.name = data['name']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error updating task: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employer_bp.route('/employers/projects/<int:project_id>/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(project_id, task_id):
    """Delete a task"""
    try:
        identity = get_jwt_identity()
        if not identity or 'role' not in identity or identity['role'] != 'employer':
            return jsonify({'error': 'Invalid token or not an employer'}), 401
            
        employer = Employer.query.get(identity['id'])
        if not employer:
            return jsonify({'error': 'Employer not found'}), 404
            
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
            
        task = Task.query.filter_by(id=task_id, project_id=project_id).first()
        if not task:
            return jsonify({'error': 'Task not found or access denied'}), 404
            
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Task deleted successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error deleting task: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500