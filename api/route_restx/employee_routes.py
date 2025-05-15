from flask_restx import Namespace, Resource, fields
from api.models.employee import Employee
from database import db

api = Namespace('employees', description='Employee operations')

employee_model = api.model('Employee', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(required=True),
    'email': fields.String(required=False),
})

@api.route('/')
class EmployeeList(Resource):
    @api.marshal_list_with(employee_model)
    def get(self):
        """Get all employees"""
        return Employee.query.all()

    @api.expect(employee_model)
    @api.marshal_with(employee_model, code=201)
    def post(self):
        """Create a new employee"""
        data = api.payload
        employee = Employee(name=data['name'], email=data.get('email'))
        db.session.add(employee)
        db.session.commit()
        return employee, 201
