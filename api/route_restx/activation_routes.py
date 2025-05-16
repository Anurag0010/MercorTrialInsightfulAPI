from flask_restx import Namespace, Resource, reqparse
from api.models.employee import Employee
from database import db
from passlib.hash import bcrypt
from datetime import datetime
from flask import request

activation_ns = Namespace('activation', description='Account Activation')

password_parser = reqparse.RequestParser()
password_parser.add_argument('password', type=str, required=True, help='New password')

@activation_ns.route('/activate/<string:token>')
class ActivateEmployee(Resource):
    def post(self, token):
        data = request.get_json(force=True)
        password = data.get('password', None)
        user_name = data.get('userName', None)
        if user_name is None:
            return {"message": "User name is required."}, 400
        if not password or len(password) < 6:
            return {"message": "Password is required and must be at least 6 characters."}, 400

        # check if user name is already taken
        if Employee.query.filter_by(username=user_name).first():
            return {"message": "User name already exists."}, 400
        
        employee = Employee.query.filter_by(activation_token=token, is_active=False).first()
        if not employee or not employee.activation_token_expiry or employee.activation_token_expiry < datetime.utcnow():
            return {"message": "Invalid or expired activation token."}, 400
        
        employee.password_hash = bcrypt.hash(password)
        employee.is_active = True
        employee.activation_token = None
        employee.activation_token_expiry = None
        db.session.commit()
        return {"message": "Account activated successfully."}, 200
