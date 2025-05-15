from flask import jsonify, request, current_app
from api.models.project import Project
from database import db
from . import project_bp

@project_bp.route('/projects', methods=['GET'])
def list_projects():
    """Get all projects"""
    try:
        current_app.logger.info('Attempting to list all projects')
        projects = Project.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'created_at': p.created_at.isoformat(),
            'updated_at': p.updated_at.isoformat(),
            'employee_count': len(p.employees),
            'task_count': len(p.tasks)
        } for p in projects])
    except Exception as e:
        current_app.logger.error(f'Error listing projects: {str(e)}')
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
        
        project = Project(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat()
        }), 201
    except Exception as e:
        current_app.logger.error(f'Error creating project: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@project_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project by ID"""
    project = Project.query.get_or_404(project_id)
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at.isoformat(),
        'updated_at': project.updated_at.isoformat(),
        'employees': [{
            'id': e.id,
            'name': e.name,
            'email': e.email
        } for e in project.employees],
        'tasks': [{
            'id': t.id,
            'title': t.title,
            'status': t.status
        } for t in project.tasks]
    })

@project_bp.route('/projects/<int:project_id>', methods=['PUT', 'PATCH'])
def update_project(project_id):
    """Update a project"""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    if data.get('name'):
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at.isoformat(),
        'updated_at': project.updated_at.isoformat()
    })

@project_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return '', 204

@project_bp.route('/projects/<int:project_id>/employees', methods=['POST'])
def add_employee_to_project(project_id):
    """Add an employee to a project"""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    if not data or 'employee_id' not in data:
        return jsonify({'error': 'Employee ID is required'}), 400
    
    from api.models.employee import Employee
    employee = Employee.query.get_or_404(data['employee_id'])
    
    if employee not in project.employees:
        project.employees.append(employee)
        db.session.commit()
    
    return jsonify({
        'message': 'Employee added to project successfully',
        'employee': {
            'id': employee.id,
            'name': employee.name,
            'email': employee.email
        }
    })
