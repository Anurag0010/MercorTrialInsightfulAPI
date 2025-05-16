from flask_restx import Namespace, Resource, fields, abort
from api.models.employee import Employee
from database import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.route_restx.auth_decorators import role_required, employee_required, employer_required

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
                'role': e.role,
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
            role=data.get('role')
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
        identity = get_jwt_identity()
        
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
        identity = get_jwt_identity()
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
        identity = get_jwt_identity()
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
            identity = get_jwt_identity()
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
        identity = get_jwt_identity()
        
        # If it's an employee, make sure they are only accessing their own projects
        if identity.get('role', identity.get('type')) == 'employee' and identity['id'] != employee_id:
            abort(403, 'You can only access your own projects')
        
        return [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'task_count': len(p.tasks)
        } for p in employee.projects]

# Example endpoints demonstrating role-based access control
@api.route('/admin-only')
class AdminOnlyEndpoint(Resource):
    @api.doc(description='This endpoint can only be accessed by admin users')
    @role_required('admin')
    def get(self):
        """Admin only endpoint"""
        return {'message': 'You have admin access'}

@api.route('/employee-only')
class EmployeeOnlyEndpoint(Resource):
    @api.doc(description='This endpoint can only be accessed by employee users')
    @employee_required
    def get(self):
        """Employee only endpoint"""
        identity = get_jwt_identity()
        return {'message': f'Hello employee #{identity["id"]}, you have employee access'}

@api.route('/employer-only')
class EmployerOnlyEndpoint(Resource):
    @api.doc(description='This endpoint can only be accessed by employer users')
    @employer_required
    def get(self):
        """Employer only endpoint"""
        identity = get_jwt_identity()
        return {'message': f'Hello employer #{identity["id"]}, you have employer access'}

@api.route('/multi-role')
class MultiRoleEndpoint(Resource):
    @api.doc(description='This endpoint can be accessed by both employees and employers')
    @role_required(['employee', 'employer'])
    def get(self):
        """Multi-role endpoint (employees and employers)"""
        identity = get_jwt_identity()
        user_type = identity.get('role', identity.get('type'))
        return {'message': f'Hello {user_type} #{identity["id"]}, you have access to this endpoint'}
