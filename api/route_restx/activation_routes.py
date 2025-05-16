from flask_restx import Namespace, Resource, reqparse
from api.models.employee import Employee
from database import db
from passlib.hash import bcrypt
from datetime import datetime

activation_ns = Namespace('activation', description='Account Activation')

password_parser = reqparse.RequestParser()
password_parser.add_argument('password', type=str, required=True, help='New password')

@activation_ns.route('/activate/<string:token>')
class ActivateEmployee(Resource):
    @activation_ns.expect(password_parser)
    def post(self, token):
        args = password_parser.parse_args()
        employee = Employee.query.filter_by(activation_token=token, is_active=False).first()
        if not employee or not employee.activation_token_expiry or employee.activation_token_expiry < datetime.utcnow():
            return {"message": "Invalid or expired activation token."}, 400

        # Set password and activate account
        employee.password_hash = bcrypt.hash(args['password'])
        employee.is_active = True
        employee.activation_token = None
        employee.activation_token_expiry = None
        db.session.commit()
        return {"message": "Account activated successfully."}, 200
