from flask import jsonify, request
from api.models.task import Task
from database import db
from . import task_bp

@task_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """Get all tasks"""
    tasks = Task.query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'project_id': t.project_id,
        'assigned_employees': len(t.employees)
    } for t in tasks])

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    if not data or 'title' not in data or 'project_id' not in data:
        return jsonify({'error': 'Title and project_id are required'}), 400
    
    task = Task(
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'pending'),
        project_id=data['project_id']
    )
    
    # Add assigned employees if provided
    if 'employee_ids' in data:
        from api.models.employee import Employee
        for emp_id in data['employee_ids']:
            employee = Employee.query.get(emp_id)
            if employee:
                task.employees.append(employee)
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'project_id': task.project_id,
        'assigned_employees': [{
            'id': e.id,
            'name': e.name
        } for e in task.employees]
    }), 201

@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID"""
    task = Task.query.get_or_404(task_id)
    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'project_id': task.project_id,
        'project': {
            'id': task.project.id,
            'name': task.project.name
        },
        'assigned_employees': [{
            'id': e.id,
            'name': e.name,
            'email': e.email
        } for e in task.employees],
        'time_logs': [{
            'id': tl.id,
            'start_time': tl.start_time.isoformat(),
            'end_time': tl.end_time.isoformat() if tl.end_time else None,
            'duration': tl.duration
        } for tl in task.time_logs]
    })

@task_bp.route('/tasks/<int:task_id>', methods=['PUT', 'PATCH'])
def update_task(task_id):
    """Update a task"""
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    if data.get('title'):
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if data.get('status'):
        task.status = data['status']
    if data.get('project_id'):
        task.project_id = data['project_id']
    
    # Update assigned employees if provided
    if 'employee_ids' in data:
        from api.models.employee import Employee
        task.employees = []  # Clear existing assignments
        for emp_id in data['employee_ids']:
            employee = Employee.query.get(emp_id)
            if employee:
                task.employees.append(employee)
    
    db.session.commit()
    
    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'project_id': task.project_id,
        'assigned_employees': [{
            'id': e.id,
            'name': e.name
        } for e in task.employees]
    })

@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204

@task_bp.route('/tasks/<int:task_id>/employees', methods=['POST'])
def assign_employee_to_task(task_id):
    """Assign an employee to a task"""
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    if not data or 'employee_id' not in data:
        return jsonify({'error': 'Employee ID is required'}), 400
    
    from api.models.employee import Employee
    employee = Employee.query.get_or_404(data['employee_id'])
    
    if employee not in task.employees:
        task.employees.append(employee)
        db.session.commit()
    
    return jsonify({
        'message': 'Employee assigned to task successfully',
        'employee': {
            'id': employee.id,
            'name': employee.name,
            'email': employee.email
        }
    })
