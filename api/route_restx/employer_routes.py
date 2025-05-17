from flask_restx import Namespace, Resource, fields, abort
from api.models.employer import Employer
from api.models.project import Project
from api.models.task import Task
from api.models.time_log import TimeLog
from database import db
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from .auth_decorators import employer_required, admin_required
from datetime import datetime, timedelta

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
    'employee_count': fields.Integer(description='Number of assigned employees'),
    'task_count': fields.Integer(description='Number of tasks')
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
    claims = get_jwt()
    
    if not claims or 'role' not in claims or claims['role'] != 'employer':
        abort(403, 'This operation is only available to employers')
        
    employer = Employer.query.get(claims['id'])
    if not employer:
        abort(404, 'Employer account not found')
        
    return employer

@api.route('/profile')
class EmployerProfile(Resource):
    @jwt_required()
    @employer_required
    @api.marshal_with(employer_model)
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Not found')
    def get(self):
        """Get employer profile"""
        employer = get_authorized_employer()
        return employer
    
    @jwt_required()
    @employer_required
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
    @employer_required
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
                'employee_count': len(project.employees),
                'task_count': len(project.tasks)
            }
            result.append(project_data)
            
        return result
    
    @jwt_required()
    @employer_required
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
    @employer_required
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
    @employer_required
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
    @employer_required
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
    
@api.route('/employees')
class EmployerEmployees(Resource):
    @jwt_required()
    @employer_required
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    def get(self):
        claims = get_jwt()
        employer_id = claims['id']
        projects = Project.query.filter_by(employer_id=employer_id).all()  
        employees = []
        employee_ids = set()
        for project in projects:
            for employee in project.employees:
                if employee.id not in employee_ids:
                    employee_ids.add(employee.id)
                    tasks: list[Task] = Task.query.join(Task.employees).filter_by(id=employee.id).all()
                    total_seconds = sum(task.minutes_spent for task in tasks)
                    total_cost = sum((task.minutes_spent // 3600) * task.project.hourly_rate for task in tasks)
                    # make total seconds to pretty form of x hours and y minutes
                    employees.append({
                        'id': employee.id,
                        'name': employee.name,
                        'email': employee.email,
                        'username': employee.username,
                        'total_seconds': total_seconds,
                        'total_cost': float(total_cost),
                        'tasks': [{
                            'id': task.id,
                            'name': task.name,
                            'status': task.status,
                            'total_seconds': task.minutes_spent,
                            'project_id': task.project_id,
                            'project_name': task.project.name,
                            'project_hourly_rate': float(task.project.hourly_rate) if task.project.hourly_rate else None,
                        } for task in tasks]
                    })
        
        return employees

@api.route('/employees/<int:employee_id>/tasks/<task_id>')
class EmployerEmployees(Resource):
    @jwt_required()
    @employer_required
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    def delete(self, employee_id, task_id):
        claims = get_jwt()
        employer_id = claims['id']
        # Check if employer owns the task
        task = Task.query.filter_by(id=task_id).first()
        if task is None:
            abort(404, 'Task not found')
        if task.project.employer_id != employer_id:
            abort(403, 'You are not authorized to delete this task')
        # Check if employee is assigned to the task
        employee = task.employees.filter_by(id=employee_id).first()
        if employee is None:
            abort(404, 'Employee not assigned to this task')
        # Remove employee from task
        task.employees.remove(employee)
        db.session.commit()
        return {'message': 'Employee removed from task successfully'}, 200
    
@api.route('/summary')
class EmployerSummary(Resource):
    @jwt_required()
    @employer_required
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    def get(self):
        claims = get_jwt()
        employer_id = claims['id']
        
        # Fetching summary for this employer, How many projects, employees and tasks
        # Recent top 5 activities from timeLog from employees
        # Total cost of projects
        # Total time spent on projects
        projects = Project.query.filter_by(employer_id=employer_id).all()
        # join through projects to get all tasks under this employer
        project_ids = [project.id for project in projects]
        tasks = Task.query.filter(Task.project_id.in_(project_ids)).all()
        
        # employee count
        emp_ids = set()
        for task in tasks:
            for employee in task.employees:
                emp_ids.add(employee.id)
        
        employee_count = len(emp_ids)
                
        # recent activities
        recent_activities = TimeLog.query.filter(TimeLog.project_id.in_(project_ids)).order_by(TimeLog.start_time.desc()).limit(5).all()
        recent_activities = [
            {
                'id': activity.id,
                'employee_id': activity.employee_id,
                'task_id': activity.task_id,
                'project_id': activity.project_id,
                'start_time': activity.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': activity.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'duration': activity.duration
            }
            for activity in recent_activities
        ]
        
        # total cost of tasks
        total_cost = int(sum(task.project.hourly_rate * task.minutes_spent // 3600 for task in tasks))
        
        # total time spent on tasks
        total_time = int(sum(task.minutes_spent for task in tasks))
        
        # project wise time and money spent
        project_wise_time = {}
        project_wise_cost = {}
        for project in projects:
            project_wise_time[project.id] = int(sum(task.minutes_spent for task in project.tasks))
            project_wise_cost[project.id] = int(sum(task.project.hourly_rate * task.minutes_spent // 3600 for task in project.tasks))
        
        return {
            'projects_count': len(projects),
            'employees_count': employee_count,
            'tasks_count': len(tasks),
            'recent_activities': recent_activities,
            'total_cost': total_cost,
            'total_time': total_time,
            'project_wise_time': project_wise_time,
            'project_wise_cost': project_wise_cost
        }
        

@api.route('/day-summary')
class EmployerDaySummary(Resource):
    @jwt_required()
    @employer_required
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    def get(self):
        claims = get_jwt()
        employer_id = claims['id']
        
        start_time = (datetime.now() - timedelta(days=7)).date()
        end_time = datetime.now()
        
        # Fetching summary for this employer, How many projects, employees and tasks
        # Recent top 5 activities from timeLog from employees
        # Total cost of projects
        # Total time spent on projects
        projects = Project.query.filter_by(employer_id=employer_id).all()
        # join through projects to get all tasks under this employer
        project_ids = [project.id for project in projects]
                    
        # recent activities
        recent_activities = TimeLog.query.filter(TimeLog.project_id.in_(project_ids)).filter(TimeLog.start_time.between(start_time, end_time)).all()
        
        # day wise sum of duration of timelog object
        day_wise_duration = {}
        for activity in recent_activities:
            day = activity.start_time.strftime('%Y-%m-%d')
            if day not in day_wise_duration:
                day_wise_duration[day] = 0
            day_wise_duration[day] += activity.duration
                
        return day_wise_duration