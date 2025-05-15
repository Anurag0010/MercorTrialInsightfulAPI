from flask import jsonify, request
from api.models.time_log import TimeLog
from api.models.task import Task
from api.models.employee import Employee
from database import db
from datetime import datetime
from . import time_tracking_bp

@time_tracking_bp.route('/time-entries', methods=['GET'])
def list_time_entries():
    """Get all time entries"""
    time_entries = TimeLog.query.all()
    return jsonify([{
        'id': te.id,
        'task_id': te.task_id,
        'employee_id': te.employee_id,
        'start_time': te.start_time.isoformat(),
        'end_time': te.end_time.isoformat() if te.end_time else None,
        'duration': te.duration,
        'notes': te.notes
    } for te in time_entries])

@time_tracking_bp.route('/time-entries', methods=['POST'])
def create_time_entry():
    """Create a new time entry"""
    data = request.json
    if not data or 'task_id' not in data or 'employee_id' not in data or 'start_time' not in data:
        return jsonify({'error': 'Task ID, employee ID, and start time are required'}), 400
    
    # Validate task and employee exist
    task = Task.query.get_or_404(data['task_id'])
    employee = Employee.query.get_or_404(data['employee_id'])
    
    # Parse start time
    try:
        start_time = datetime.fromisoformat(data['start_time'])
    except ValueError:
        return jsonify({'error': 'Invalid start time format'}), 400
    
    # Parse end time if provided
    end_time = None
    if data.get('end_time'):
        try:
            end_time = datetime.fromisoformat(data['end_time'])
            if end_time <= start_time:
                return jsonify({'error': 'End time must be after start time'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid end time format'}), 400
    
    time_entry = TimeLog(
        task_id=data['task_id'],
        employee_id=data['employee_id'],
        start_time=start_time,
        end_time=end_time,
        notes=data.get('notes', '')
    )
    
    # Calculate duration if end time is provided
    if end_time:
        time_entry.duration = int((end_time - start_time).total_seconds())
    
    db.session.add(time_entry)
    db.session.commit()
    
    return jsonify({
        'id': time_entry.id,
        'task_id': time_entry.task_id,
        'employee_id': time_entry.employee_id,
        'start_time': time_entry.start_time.isoformat(),
        'end_time': time_entry.end_time.isoformat() if time_entry.end_time else None,
        'duration': time_entry.duration,
        'notes': time_entry.notes
    }), 201

@time_tracking_bp.route('/time-entries/<int:entry_id>', methods=['GET'])
def get_time_entry(entry_id):
    """Get a specific time entry by ID"""
    time_entry = TimeLog.query.get_or_404(entry_id)
    return jsonify({
        'id': time_entry.id,
        'task': {
            'id': time_entry.task.id,
            'title': time_entry.task.title,
            'project': {
                'id': time_entry.task.project.id,
                'name': time_entry.task.project.name
            }
        },
        'employee': {
            'id': time_entry.employee.id,
            'name': time_entry.employee.name
        },
        'start_time': time_entry.start_time.isoformat(),
        'end_time': time_entry.end_time.isoformat() if time_entry.end_time else None,
        'duration': time_entry.duration,
        'notes': time_entry.notes
    })

@time_tracking_bp.route('/time-entries/<int:entry_id>/stop', methods=['POST'])
def stop_time_entry(entry_id):
    """Stop a time entry by setting its end time"""
    time_entry = TimeLog.query.get_or_404(entry_id)
    
    if time_entry.end_time:
        return jsonify({'error': 'Time entry already stopped'}), 400
    
    time_entry.end_time = datetime.utcnow()
    time_entry.duration = int((time_entry.end_time - time_entry.start_time).total_seconds())
    
    db.session.commit()
    
    return jsonify({
        'id': time_entry.id,
        'task_id': time_entry.task_id,
        'employee_id': time_entry.employee_id,
        'start_time': time_entry.start_time.isoformat(),
        'end_time': time_entry.end_time.isoformat(),
        'duration': time_entry.duration,
        'notes': time_entry.notes
    })

@time_tracking_bp.route('/time-entries/<int:entry_id>', methods=['DELETE'])
def delete_time_entry(entry_id):
    """Delete a time entry"""
    time_entry = TimeLog.query.get_or_404(entry_id)
    db.session.delete(time_entry)
    db.session.commit()
    return '', 204

@time_tracking_bp.route('/employees/<int:employee_id>/time-entries', methods=['GET'])
def get_employee_time_entries(employee_id):
    """Get all time entries for an employee"""
    Employee.query.get_or_404(employee_id)  # Verify employee exists
    time_entries = TimeLog.query.filter_by(employee_id=employee_id).all()
    
    return jsonify([{
        'id': te.id,
        'task': {
            'id': te.task.id,
            'title': te.task.title
        },
        'start_time': te.start_time.isoformat(),
        'end_time': te.end_time.isoformat() if te.end_time else None,
        'duration': te.duration,
        'notes': te.notes
    } for te in time_entries])
