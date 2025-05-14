from flask import Blueprint, request, jsonify
from models import Project, Employee, db

project_bp = Blueprint('project', __name__)

@project_bp.route('/projects', methods=['GET'])
def list_projects():
    projects = Project.query.all()
    return jsonify([p.to_dict() for p in projects])

@project_bp.route('/projects', methods=['POST'])
def create_project():
    data = request.json
    project = Project(
        name=data['name'],
        description=data.get('description')
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201

@project_bp.route('/projects/<int:project_id>', methods=['PATCH'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.json
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    db.session.commit()
    return jsonify(project.to_dict())

@project_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return '', 204
