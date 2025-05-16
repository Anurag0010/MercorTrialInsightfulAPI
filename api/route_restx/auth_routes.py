from flask_restx import Namespace, Resource, fields, abort
from typing import Dict, Any, Optional, Tuple, Union
from api.models.employee import Employee
from api.models.employer import Employer
from api.models.admin import Admin
from database import db
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity
)
from datetime import timedelta
from constants import ACCESS_TOKEN_EXPIRY_MINUTES, REFRESH_TOKEN_EXPIRY_MINUTES, ALLOWED_ADMIN_EMAILS

api = Namespace('auth', description='Authentication operations')

# Input models
employee_login_model = api.model('EmployeeLogin', {
    'username': fields.String(required=True, description='Employee username'),
    'password': fields.String(required=True, description='Employee password'),
})

employee_register_model = api.model('EmployeeRegister', {
    'username': fields.String(required=True, description='Employee username'),
    'name': fields.String(required=True, description='Employee name'),
    'email': fields.String(required=True, description='Employee email'),
    'password': fields.String(required=True, description='Employee password'),
})

employer_login_model = api.model('EmployerLogin', {
    'email': fields.String(required=True, description='Employer email'),
    'password': fields.String(required=True, description='Employer password'),
})

employer_register_model = api.model('EmployerRegister', {
    'company_name': fields.String(required=True, description='Company name'),
    'contact_name': fields.String(required=True, description='Contact person name'),
    'email': fields.String(required=True, description='Employer email'),
    'phone': fields.String(required=False, description='Contact phone number'),
    'password': fields.String(required=True, description='Employer password'),
    'website': fields.String(required=False, description='Company website'),
    'address': fields.String(required=False, description='Company address'),
})

# Admin login model
admin_login_model = api.model('AdminLogin', {
    'email': fields.String(required=True, description='Admin email'),
    'password': fields.String(required=True, description='Admin password'),
})

# Output models
token_model = api.model('Token', {
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'user_type': fields.String(description='Type of user (employee, employer, or admin)'),
    'user_id': fields.Integer(description='User ID'),
})

# Routes for employee authentication
@api.route('/employee/register')
class EmployeeRegister(Resource):
    @api.expect(employee_register_model)
    @api.response(201, 'Employee successfully registered')
    @api.response(400, 'Validation error')
    @api.response(409, 'Username or email already exists')
    def post(self) -> Tuple[Dict[str, str], int]:
        """Register a new employee"""
        data: Dict[str, Any] = api.payload
        
        # Validate required fields
        if not data:
            abort(400, 'No input data provided')
            
        # Check if username already exists
        if Employee.query.filter_by(username=data['username']).first():
            abort(409, 'Username already exists')
            
        # Check if email already exists
        if Employee.query.filter_by(email=data['email']).first():
            abort(409, 'Email already registered')
            
        # Create new employee
        employee = Employee(
            username=data['username'],
            name=data['name'],
            email=data['email']
        )
        employee.set_password(data['password'])
        
        db.session.add(employee)
        db.session.commit()
        
        return {'message': 'Employee registered successfully'}, 201

@api.route('/employee/login')
class EmployeeLogin(Resource):
    @api.expect(employee_login_model)
    @api.response(200, 'Login successful', token_model)
    @api.response(400, 'Validation error')
    @api.response(401, 'Invalid credentials')
    def post(self) -> Tuple[Dict[str, Any], int]:
        """Login for employees"""
        data: Dict[str, Any] = api.payload
        
        if not data:
            abort(400, 'No input data provided')
            
        # Find employee by username
        employee: Optional[Employee] = Employee.query.filter_by(username=data['username']).first()
        if not employee or not employee.check_password(data['password']):
            abort(401, 'Invalid username or password')
            
        # Check if employee is active
        if not employee.active:
            abort(403, 'Your account is deactivated. Please contact admin.')
        
        # Generate tokens with identity containing role
        identity: Dict[str, Any] = {
            'id': employee.id,
            'role': 'employee',  # New field for role-based auth
            'username': employee.username
        }
        
        access_token: str = create_access_token(
            identity=identity,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
        )
        
        refresh_token: str = create_refresh_token(
            identity=identity,
            expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRY_MINUTES)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_type': 'employee',
            'user_id': employee.id
        }, 200

# Routes for employer authentication
@api.route('/employer/register')
class EmployerRegister(Resource):
    @api.expect(employer_register_model)
    @api.response(201, 'Employer successfully registered')
    @api.response(400, 'Validation error')
    @api.response(409, 'Email already exists')
    def post(self) -> Tuple[Dict[str, str], int]:
        """Register a new employer"""
        data: Dict[str, Any] = api.payload
        
        # Validate required fields
        if not data:
            abort(400, 'No input data provided')
            
        # Check if email already exists
        if Employer.query.filter_by(email=data['email']).first():
            abort(409, 'Email already registered')
            
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
        
        return {'message': 'Employer registered successfully'}, 201

@api.route('/employer/login')
class EmployerLogin(Resource):
    @api.expect(employer_login_model)
    @api.response(200, 'Login successful', token_model)
    @api.response(400, 'Validation error')
    @api.response(401, 'Invalid credentials')
    def post(self) -> Tuple[Dict[str, Any], int]:
        """Login for employers"""
        data: Dict[str, Any] = api.payload
        
        if not data:
            abort(400, 'No input data provided')
            
        # Find employer by email
        employer: Optional[Employer] = Employer.query.filter_by(email=data['email']).first()
        if not employer or not employer.check_password(data['password']):
            abort(401, 'Invalid email or password')
            
        # Check if employer is active
        if not employer.active:
            abort(403, 'Your account is deactivated. Please contact admin.')
        
        # Generate tokens with identity containing role
        identity: Dict[str, Any] = {
            'id': employer.id,
            'role': 'employer',  # New field for role-based auth
            'email': employer.email
        }
        
        access_token: str = create_access_token(
            identity=identity,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
        )
        
        refresh_token: str = create_refresh_token(
            identity=identity,
            expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRY_MINUTES)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_type': 'employer',
            'user_id': employer.id
        }, 200

# Routes for admin authentication
@api.route('/admin/login')
class AdminLogin(Resource):
    @api.expect(admin_login_model)
    @api.response(200, 'Login successful', token_model)
    @api.response(400, 'Validation error')
    @api.response(401, 'Invalid credentials')
    @api.response(403, 'Email not in allowed list')
    def post(self) -> Tuple[Dict[str, Any], int]:
        """Login for administrators"""
        data: Dict[str, Any] = api.payload
        
        if not data:
            abort(400, 'No input data provided')
        
        # Check if email is in the allowed list
        if data['email'] not in ALLOWED_ADMIN_EMAILS:
            abort(403, 'Email not authorized for admin access')
            
        # Find admin by email
        admin: Optional[Admin] = Admin.query.filter_by(email=data['email']).first()
        if not admin or not admin.check_password(data['password']):
            abort(401, 'Invalid email or password')
        
        # Generate tokens with identity containing role
        identity: Dict[str, Any] = {
            'id': admin.id,
            'type': 'admin',  # For backward compatibility 
            'role': 'admin',  # Admin role for role-based auth
            'email': admin.email
        }
        
        access_token: str = create_access_token(
            identity=identity,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
        )
        
        refresh_token: str = create_refresh_token(
            identity=identity,
            expires_delta=timedelta(minutes=REFRESH_TOKEN_EXPIRY_MINUTES)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_type': 'admin',
            'user_id': admin.id
        }, 200

# Shared token refresh endpoint
@api.route('/refresh')
class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    @api.response(200, 'Token refreshed successfully', token_model)
    @api.response(401, 'Invalid refresh token')
    def post(self) -> Tuple[Dict[str, Any], int]:
        """Refresh access token"""
        identity: Dict[str, Any] = get_jwt_identity()
        
        if not identity or ('role' not in identity):
            abort(401, 'Invalid token')
            
        access_token: str = create_access_token(
            identity=identity,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
        )
        
        return {
            'access_token': access_token,
            'user_type': identity.get('role', identity.get('type', 'unknown')),
            'user_id': identity['id']
        }, 200