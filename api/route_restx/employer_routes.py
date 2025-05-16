from flask_restx import Namespace, Resource, fields, abort
from api.models.employer import Employer
from api.models.project import Project
from api.models.task import Task
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity

api = Namespace('employers', description='Employer operations')

# Base models
employer_model = api.model('Employer', {
    'id': fields.Integer(readOnly=True, description='Employer ID'),
    'company_name': fields.String(required=True, description='Company name'),
    'contact_name': fields.String(required=True, description='Contact person name'),
    'email': fields.String(required=True, description='Employer email'),
    'phone': fields.String(required=False, description='Contact phone number'),
    'active': fields.Boolean(description='Account status'),
    'profile_image_url': fields.String(description='Profile image URL'),
    'address': fields.String(description='Company address'),
    'website': fields.String(description='Company website')
})

employer_update_model = api.model('EmployerUpdate', {
    'company_name': fields.String(description='Company name'),
    'contact_name': fields.String(description='Contact person name'),
    'phone': fields.String(description='Contact phone number'),
    'profile_image_url': fields.String(description='Profile image URL'),
    'address': fields.String(description='Company address'),
    'website': fields.String(description='Company website'),
    'password': fields.String(description='New password')
})

# Project models
project_input_model = api.model('ProjectInput', {
    'name': fields.String(required=True, description='Project name'),
    'description': fields.String(description='Project description'),
    'hourly_rate': fields.Float(description='Hourly rate')
})

project_model = api.inherit('Project', project_input_model, {
    'id': fields.Integer(readOnly=True, description='Project ID'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp'),
    'employee_count': fields.Integer(description='Number of assigned employees')
})

project_detail_model = api.inherit('ProjectDetail', project_model, {
    'employees': fields.List(fields.Nested(api.model('EmployeeSummary', {
        'id': fields.Integer(description='Employee ID'),
        'name': fields.String(description='Employee name'),
        'email': fields.String(description='Employee email')
    })), description='Assigned employees'),
    'tasks': fields.List(fields.Nested(api.model('TaskSummary', {
        'id': fields.Integer(description='Task ID'),
        'name': fields.String(description='Task name'),
        'status': fields.String(description='Task status')
    })), description='Project tasks')
})

# Task models
task_input_model = api.model('TaskInput', {
    'name': fields.String(required=True, description='Task name'),
    'description': fields.String(description='Task description'),
    'status': fields.String(description='Task status', enum=['pending', 'in_progress', 'completed', 'on_hold'])
})

task_model = api.inherit('Task', task_input_model, {
    'id': fields.Integer(readOnly=True, description='Task ID'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

# Helper function to check if the authenticated user is an employer
def get_authorized_employer():
    identity = get_jwt_identity()
    
    if not identity or 'type' not in identity or identity['type'] != 'employer':
        abort(403, 'This operation is only available to employers')
        
    employer = Employer.query.get(identity['id'])
    if not employer:
        abort(404, 'Employer account not found')
        
    return employer

@api.route('/profile')
class EmployerProfile(Resource):
    @jwt_required()
    @api.marshal_with(employer_model)
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Not found')
    def get(self):
        """Get employer profile"""
        employer = get_authorized_employer()
        return employer
    
    @jwt_required()
    @api.expect(employer_update_model)
    @api.marshal_with(employer_model)
    @api.response(200, 'Profile updated')
    @api.response(400, 'Validation error')
    @api.response(403, 'Not authorized')
    def put(self):
        """Update employer profile"""
        employer = get_authorized_employer()
        data = api.payload
        
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
        if 'password' in data and data['password']:
            employer.set_password(data['password'])
        
        db.session.commit()
        return employer

@api.route('/projects')
class EmployerProjects(Resource):
    @jwt_required()
    @api.marshal_list_with(project_model)
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    def get(self):
        """Get all projects for the employer"""
        employer = get_authorized_employer()
        projects = Project.query.filter_by(employer_id=employer.id).all()
        
        result = []
        for project in projects:
            project_data = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
                'created_at': project.created_at,
                'updated_at': project.updated_at,
                'employee_count': len(project.employees)
            }
            result.append(project_data)
            
        return result
    
    @jwt_required()
    @api.expect(project_input_model)
    @api.marshal_with(project_model, code=201)
    @api.response(201, 'Project created')
    @api.response(400, 'Validation error')
    @api.response(403, 'Not authorized')
    def post(self):
        """Create a new project"""
        employer = get_authorized_employer()
        data = api.payload
        
        if not data or 'name' not in data:
            abort(400, 'Project name is required')
        
        project = Project(
            name=data['name'],
            description=data.get('description'),
            hourly_rate=data.get('hourly_rate'),
            employer_id=employer.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
            'created_at': project.created_at,
            'updated_at': project.updated_at,
            'employee_count': 0
        }, 201

@api.route('/projects/<int:project_id>')
@api.param('project_id', 'The project identifier')
class EmployerProjectDetail(Resource):
    @jwt_required()
    @api.marshal_with(project_detail_model)
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Project not found')
    def get(self, project_id):
        """Get details of a specific project"""
        employer = get_authorized_employer()
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        
        if not project:
            abort(404, 'Project not found or access denied')
        
        return {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
            'created_at': project.created_at,
            'updated_at': project.updated_at,
            'employee_count': len(project.employees),
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
        }
    
    @jwt_required()
    @api.expect(project_input_model)
    @api.marshal_with(project_model)
    @api.response(200, 'Project updated')
    @api.response(400, 'Validation error')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Project not found')
    def put(self, project_id):
        """Update a project"""
        employer = get_authorized_employer()
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        
        if not project:
            abort(404, 'Project not found or access denied')
        
        data = api.payload
        
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'hourly_rate' in data:
            project.hourly_rate = data['hourly_rate']
        
        db.session.commit()
        
        return {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None,
            'created_at': project.created_at,
            'updated_at': project.updated_at,
            'employee_count': len(project.employees)
        }
    
    @jwt_required()
    @api.response(204, 'Project deleted')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Project not found')
    def delete(self, project_id):
        """Delete a project"""
        employer = get_authorized_employer()
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        
        if not project:
            abort(404, 'Project not found or access denied')
        
        db.session.delete(project)
        db.session.commit()
        
        return '', 204

@api.route('/projects/<int:project_id>/tasks')
@api.param('project_id', 'The project identifier')
class ProjectTasks(Resource):
    @jwt_required()
    @api.marshal_list_with(task_model)
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Project not found')
    def get(self, project_id):
        """Get all tasks for a project"""
        employer = get_authorized_employer()
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        
        if not project:
            abort(404, 'Project not found or access denied')
        
        tasks = Task.query.filter_by(project_id=project_id).all()
        return tasks
    
    @jwt_required()
    @api.expect(task_input_model)
    @api.marshal_with(task_model, code=201)
    @api.response(201, 'Task created')
    @api.response(400, 'Validation error')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Project not found')
    def post(self, project_id):
        """Create a new task for a project"""
        employer = get_authorized_employer()
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        
        if not project:
            abort(404, 'Project not found or access denied')
        
        data = api.payload
        
        if not data or 'name' not in data:
            abort(400, 'Task name is required')
        
        task = Task(
            name=data['name'],
            description=data.get('description'),
            status=data.get('status', 'pending'),
            project_id=project_id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return task, 201

@api.route('/projects/<int:project_id>/tasks/<int:task_id>')
@api.param('project_id', 'The project identifier')
@api.param('task_id', 'The task identifier')
class ProjectTaskDetail(Resource):
    @jwt_required()
    @api.expect(task_input_model)
    @api.marshal_with(task_model)
    @api.response(200, 'Task updated')
    @api.response(400, 'Validation error')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Task not found or access denied')
    def put(self, project_id, task_id):
        """Update a task"""
        employer = get_authorized_employer()
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        
        if not project:
            abort(404, 'Project not found or access denied')
        
        task = Task.query.filter_by(id=task_id, project_id=project_id).first()
        
        if not task:
            abort(404, 'Task not found or access denied')
        
        data = api.payload
        
        if 'name' in data:
            task.name = data['name']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        
        db.session.commit()
        return task
    
    @jwt_required()
    @api.response(204, 'Task deleted')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Task not found or access denied')
    def delete(self, project_id, task_id):
        """Delete a task"""
        employer = get_authorized_employer()
        project = Project.query.filter_by(id=project_id, employer_id=employer.id).first()
        
        if not project:
            abort(404, 'Project not found or access denied')
        
        task = Task.query.filter_by(id=task_id, project_id=project_id).first()
        
        if not task:
            abort(404, 'Task not found or access denied')
        
        db.session.delete(task)
        db.session.commit()
        
        return '', 204