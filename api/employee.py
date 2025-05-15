from flask import Blueprint, request, jsonify
from flask import current_app
from database import db
from api.models import Employee

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/employees', methods=['GET'])
def list_employees():
    employees = Employee.query.all()
    return jsonify([e.to_dict() for e in employees])

@employee_bp.route('/employees', methods=['POST'])
def create_employee():
    data = request.json
    employee = Employee(
        name=data['name'],
        email=data['email'],
        active=data.get('active', True),
        profile_image_url=data.get('profile_image_url')
    )
    try:
        db.session.add(employee)
        db.session.commit()
        return jsonify(employee.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@employee_bp.route('/employees/<int:employee_id>', methods=['PATCH'])
def update_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    data = request.json
    employee.name = data.get('name', employee.name)
    employee.email = data.get('email', employee.email)
    employee.active = data.get('active', employee.active)
    db.session.commit()
    return jsonify(employee.to_dict())

@employee_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
def deactivate_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employee.active = False
    db.session.commit()
    return '', 204
