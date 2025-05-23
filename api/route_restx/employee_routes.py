from flask_restx import Namespace, Resource, fields, abort
from api.models.employee import Employee
from database import db
from flask_jwt_extended import jwt_required, get_jwt
from api.route_restx.auth_decorators import role_required, employee_required, employer_required, check_mac_address
from api.models.project import Project
from api.models.task import Task
from api.models.employee import task_employee

api = Namespace('employees', description='Employee operations')

# Enhanced employee model with all fields from Employee class
employee_model = api.model('Employee', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(required=True, description='Employee name'),
    'email': fields.String(required=True, description='Employee email'),
    'role': fields.String(required=False, description='Employee role'),
    'username': fields.String(required=False, description='Employee username'),
})

# Project summary model for nested responses
project_summary_model = api.model('ProjectSummary', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(description='Project name'),
    'description': fields.String(description='Project description'),
    'task_count': fields.Integer(description='Number of tasks in the project')
})

projectAssignment_model = api.model('ProjectAssignment', {
    'project_id': fields.Integer(required=True, description='Project ID to assign'),
})

taskAssignment_model = api.model('TaskAssignment', {
    'task_id': fields.Integer(required=True, description='Task ID to assign'),
    'employee_id': fields.Integer(required=True, description='Employee ID to assign to')
})

# Task summary model for nested responses
task_summary_model = api.model('TaskSummary', {
    'id': fields.Integer(readOnly=True),
    'title': fields.String(description='Task title'),
    'status': fields.String(description='Task status'),
    'hourly_rate': fields.Float(description='Hourly rate for the task'),
    'total_hours': fields.Float(description='Total hours logged for the task'),
    'total_cost': fields.Float(description='Total cost for the task'), 
    'project_id': fields.Integer(description='Project ID associated with the task')
})

# Detailed employee model with relationships
detailed_employee_model = api.inherit('DetailedEmployee', employee_model, {
    'projects': fields.List(fields.Nested(project_summary_model), description='Projects assigned to employee'),
    'tasks': fields.List(fields.Nested(task_summary_model), description='Tasks assigned to employee')
})

@api.route('/')
class EmployeeList(Resource):
    @api.marshal_list_with(employee_model)
    @role_required(['admin', 'employer'])  # Only admins and employers can view all employees
    def get(self) -> list[dict]:
        """Get all employees (Admin and Employer only)"""
        employees = Employee.query.all()
        # Include project and task counts
        result: list[dict] = []
        for e in employees:
            employee_data = {
                'id': e.id,
                'name': e.name,
                'email': e.email,
                'project_count': len(e.projects),
                'task_count': len(e.tasks)
            }
            result.append(employee_data)
        return result

    @api.expect(employee_model)
    @api.marshal_with(employee_model, code=201)
    @api.response(400, 'Validation Error')
    @role_required('admin')  # Only admins can create employees through this endpoint
    def post(self) -> tuple[Employee, int]:
        """Create a new employee (Admin only)"""
        data = api.payload
        
        # Validate required fields
        if not data or 'name' not in data or 'email' not in data:
            abort(400, 'Name and email are required')
        
        # Check if email already exists
        if Employee.query.filter_by(email=data['email']).first():
            abort(400, 'Email already registered')
        
        employee = Employee(
            name=data['name'],
            email=data['email'],
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return employee, 201

@api.route('/<int:employee_id>')
@api.param('employee_id', 'The employee identifier')
@api.response(404, 'Employee not found')
class EmployeeResource(Resource):
    @api.marshal_with(detailed_employee_model)
    @jwt_required()  # Any authenticated user can access, but we'll check permissions inside
    def get(self, employee_id):
        """Get a specific employee by ID"""
        employee : Employee = Employee.query.get_or_404(employee_id)
        
        # Get the identity of the current user
        identity = get_jwt()
        
        # If it's not an admin or employer, make sure the employee is only accessing their own record
        if identity.get('role', identity.get('type')) == 'employee' and identity['id'] != employee_id:
            abort(403, 'You can only access your own employee record')
        
        return {
            'id': employee.id,
            'name': employee.name,
            'email': employee.email,
            'role': employee.role,
            'projects': [{
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'task_count': len(p.tasks)
            } for p in employee.projects],
            'tasks': [{
                'id': t.id,
                'title': t.name,
                'status': t.status,
                'hourly_rate': t.project.hourly_rate,
                'total_hours': t.minutes_spent / 60,
                'project_id': t.project.id,
                'total_cost': (t.minutes_spent / 60) * t.project.hourly_rate
            } for t in employee.tasks]
        }

    @api.expect(employee_model)
    @api.marshal_with(employee_model)
    @api.response(400, 'Validation Error')
    @role_required(['admin', 'employee'])  # Only admin or the employee themselves
    def put(self, employee_id: int) -> Employee:
        """Update an employee (full update)"""
        # Check if employee is updating their own record
        identity = get_jwt()
        if identity.get('role', identity.get('type')) == 'employee' and identity['id'] != employee_id:
            abort(403, 'You can only update your own details')
            
        return self._update_employee(employee_id)
    
    @api.expect(employee_model)
    @api.marshal_with(employee_model)
    @api.response(400, 'Validation Error')
    @role_required(['admin', 'employee'])  # Only admin or the employee themselves
    def patch(self, employee_id: int) -> Employee:
        """Update an employee (partial update)"""
        # Check if employee is updating their own record
        identity = get_jwt()
        if identity.get('role', identity.get('type')) == 'employee' and identity['id'] != employee_id:
            abort(403, 'You can only update your own details.')
            
        return self._update_employee(employee_id)
    
    def _update_employee(self, employee_id: int) -> Employee:
        """Helper method for put and patch operations"""
        employee = Employee.query.get_or_404(employee_id)
        data = api.payload
        
        if data.get('name'):
            employee.name = data['name']
        if data.get('email'):
            # Check if new email already exists for another employee
            existing = Employee.query.filter_by(email=data['email']).first()
            if existing and existing.id != employee_id:
                abort(400, 'Email already registered')
            employee.email = data['email']
        if 'role' in data:
            # Only allow admin to change roles
            identity = get_jwt()
            if identity.get('role', identity.get('type')) != 'admin':
                abort(403, 'Only administrators can change roles')
            employee.role = data['role']
        
        db.session.commit()
        
        return employee
        
    @api.response(204, 'Employee successfully deleted')
    @role_required('admin')  # Only admins can delete employees
    def delete(self, employee_id: int) -> tuple[str, int]:
        """Delete an employee (Admin only)"""
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        return '', 204


@api.route('/<int:employee_id>/projects')
@api.param('employee_id', 'The employee identifier')
@api.response(404, 'Employee not found')
class EmployeeProjects(Resource):
    @api.marshal_list_with(project_summary_model)
    @jwt_required()  # Any authenticated user can access, but we'll check permissions inside
    def get(self, employee_id):
        """Get all projects for an employee"""
        employee = Employee.query.get_or_404(employee_id)
        
        # Get the identity of the current user
        identity = get_jwt()
        
        # If it's an employee, make sure they are only accessing their own projects
        if identity.get('role', identity.get('type')) == 'employee' and identity['id'] != employee_id:
            abort(403, 'You can only access your own projects')
        
        return [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'task_count': len(p.tasks)
        } for p in employee.projects]

    # New endpoint to assign a project to an employee
    @api.doc(description='Assign a project to an employee')
    @api.response(201, 'Project successfully assigned')
    @api.response(400, 'Validation Error')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @role_required(['admin', 'employer'])
    def post(self, employee_id):
        """Assign a project to an employee (Admin or the employee themselves)"""
        # Check permissions        
        project_id = api.payload['project_id'] 
        
        # Find the employee
        employee = Employee.query.get_or_404(employee_id)
        
        # Get the project ID from the request
        if not api.payload or 'project_id' not in api.payload:
            abort(400, 'Project ID is required')
        
        project_id = api.payload['project_id']
        
        # Import needed models
        from api.models.project import Project
        from api.models.task import Task
        
        # Find the project
        project = Project.query.get_or_404(project_id)
        
        # Check if the employee is already assigned to this project
        if project in employee.projects:
            return {'message': f'Employee already assigned to project {project.name}'}, 200
        
        try:
            # Assign the project to the employee
            employee.projects.append(project)
            
            # Assign all tasks from this project to the employee as well
            tasks = Task.query.filter_by(project_id=project_id).all()
            for task in tasks:
                if task not in employee.tasks:
                    employee.tasks.append(task)
            
            db.session.commit()
            
            return {
                'message': f'Project {project.name} successfully assigned to {employee.name}',
                'tasks_assigned': len(tasks)
            }, 201
        except Exception as e:
            db.session.rollback()
            abort(500, f'Failed to assign project: {str(e)}')

    @api.doc(description='Unassign a project from an employee')
    @api.response(204, 'Project successfully unassigned')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @role_required(['admin', 'employer'])
    def delete(self, employee_id):
        """Unassign a project from an employee (Admin or Employer only)"""
        project_id = None
        if api.payload and 'project_id' in api.payload:
            project_id = api.payload['project_id']
        elif hasattr(api, 'args') and 'project_id' in api.args:
            project_id = api.args['project_id']
        if not project_id:
            abort(400, 'Project ID is required to unassign')
        from api.models.project import Project
        employee = Employee.query.get_or_404(employee_id)
        project = Project.query.get_or_404(project_id)
        # Only allow if the current user is the employer who owns this project or admin
        identity = get_jwt()
        if identity.get('role', identity.get('type')) == 'employer' and project.employer_id != identity['id']:
            abort(403, 'You do not have permission to unassign this project')
        if project not in employee.projects:
            abort(404, 'Employee is not assigned to this project')
        try:
            employee.projects.remove(project)
            # Optionally, also remove all tasks from this project from the employee
            employee.tasks = [t for t in employee.tasks if t.project_id != project_id]
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            abort(500, f'Failed to unassign project: {str(e)}')


@api.route('/<int:employee_id>/tasks')
@api.param('employee_id', 'The employee identifier')
@api.response(404, 'Employee not found')
class EmployeeTasks(Resource):
    @api.marshal_list_with(task_summary_model)
    @jwt_required()
    def get(self, employee_id):
        """Get all tasks for an employee"""
        employee = Employee.query.get_or_404(employee_id)
        
        # Get the identity of the current user
        identity = get_jwt()
        
        # If it's an employee, make sure they are only accessing their own tasks
        if identity.get('role', identity.get('type')) == 'employee' and identity['id'] != employee_id:
            abort(403, 'You can only access your own tasks')
        
        return [{
            'id': t.id,
            'title': t.name,
            'status': t.status,
            'hourly_rate': t.project.hourly_rate if t.project else None,
            'total_hours': t.minutes_spent / 60 if t.minutes_spent else 0,
            'project_id': t.project_id,
            'total_cost': (t.minutes_spent / 60) * t.project.hourly_rate if t.minutes_spent and t.project else 0
        } for t in employee.tasks]

    # New endpoint to assign a task to an employee
    @api.doc(description='Assign a task to an employee')
    @api.expect(taskAssignment_model)
    @api.marshal_with(taskAssignment_model)
    @api.response(201, 'Task successfully assigned')
    @api.response(400, 'Validation Error')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @role_required(['admin', 'employer'])
    def post(self, employee_id):
        """Assign a task to an employee (Admin or the employee themselves)"""                
        # Find the employee
        employee = Employee.query.get_or_404(employee_id)
        
        # Get the task ID from the request
        if not api.payload or 'task_id' not in api.payload:
            abort(400, 'Task ID is required')
        
        task_id = api.payload['task_id']
        
        # Import needed models
        from api.models.task import Task
        
        # Find the task
        task = Task.query.get_or_404(task_id)
        
        # Check if the employee is already assigned to this task
        if task in employee.tasks:
            return {'message': f'Employee already assigned to task {task.name}'}, 200
        
        # Check if the employee is assigned to the project of this task
        if task.project not in employee.projects:
            employee.projects.append(task.project)
        
        try:
            # Assign the task to the employee
            employee.tasks.append(task)
            db.session.commit()
            
            return {
                'message': f'Task {task.name} successfully assigned to {employee.name}',
                'project': task.project.name
            }, 201
        except Exception as e:
            db.session.rollback()
            abort(500, f'Failed to assign task: {str(e)}')

    @api.doc(description='Unassign a task from an employee')
    @api.response(204, 'Task successfully unassigned')
    @api.response(403, 'Forbidden')
    @api.response(404, 'Not Found')
    @role_required(['admin', 'employer'])
    def delete(self, employee_id):
        """Unassign a task from an employee (Admin or Employer only)"""
        task_id = None
        if api.payload and 'task_id' in api.payload:
            task_id = api.payload['task_id']
        elif hasattr(api, 'args') and 'task_id' in api.args:
            task_id = api.args['task_id']
        if not task_id:
            abort(400, 'Task ID is required to unassign')
        from api.models.task import Task
        employee = Employee.query.get_or_404(employee_id)
        task = Task.query.get_or_404(task_id)
        # Only allow if the current user is the employer who owns this task's project or admin
        identity = get_jwt()
        if identity.get('role', identity.get('type')) == 'employer' and task.project.employer_id != identity['id']:
            abort(403, 'You do not have permission to unassign this task')
        if task not in employee.tasks:
            abort(404, 'Employee is not assigned to this task')
        try:
            employee.tasks.remove(task)
            db.session.commit()
            return '', 204
        except Exception as e:
            db.session.rollback()
            abort(500, f'Failed to unassign task: {str(e)}')


@api.route('/projects')
class EmployeeProjects(Resource):
    # Get projects and tasks for an employee when employee calls this endpoint
    @api.doc(description='Get projects and tasks for an employee')
    @role_required(['employee'])
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    @api.response(404, 'Project not found')
    def get(self):
        """Get projects and tasks for an employee"""
        claims = get_jwt()
        employee_id = claims['id']
        projects = Project.query.filter_by(employer_id=employee_id).all()
        return {
            'projects': [{
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
            } for project in projects]
        }



@api.route('/tasks')
class EmployeeTasks(Resource):
    # Get projects and tasks for an employee when employee calls this endpoint
    @api.doc(description='Get projects and tasks for an employee')
    @role_required(['employee'])
    @api.response(200, 'Success')
    @api.response(403, 'Not authorized')
    def get(self):
        """Get projects and tasks for an employee"""
        claims = get_jwt()
        employee_id = claims['id']
        
        tasks: list[Task] = Task.query.join(Task.employees).filter_by(id=employee_id).all()
        full_tasks = []
        for task in tasks:
            full_tasks.append({
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'project_id': task.project_id,
                'project_name': task.project.name,
                'project_hourly_rate': float(task.project.hourly_rate) if task.project.hourly_rate else None,
                'project_employee_count': len(task.project.employees),
                'task_spent_time_in_minutes': task.minutes_spent,
                'task_spent_time_in_minutes_real': task.minutes_spent / 60,
                'task_spent_time_in_hours': task.minutes_spent / 60,
            })
        return full_tasks


        @api.doc(description='This endpoint can be accessed by both employees and employers')
        @role_required(['employee', 'employer'])
        def get(self):
            """Multi-role endpoint (employees and employers)"""
            identity = get_jwt()
            user_type = identity.get('role', identity.get('type'))
            return {'message': f'Hello {user_type} #{identity["id"]}, you have access to this endpoint'}
