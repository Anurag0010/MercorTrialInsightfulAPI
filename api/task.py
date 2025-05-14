from flask import Blueprint, request, jsonify
from models import Task, Project, Employee, db

task_bp = Blueprint('task', __name__)

@task_bp.route('/tasks', methods=['GET'])
def list_tasks():
    tasks = Task.query.all()
    return jsonify([t.to_dict() for t in tasks])

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    task = Task(
        name=data['name'],
        project_id=data['project_id']
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@task_bp.route('/tasks/<int:task_id>', methods=['PATCH'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.json
    task.name = data.get('name', task.name)
    db.session.commit()
    return jsonify(task.to_dict())

@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204
