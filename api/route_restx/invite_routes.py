from flask_restx import Namespace, Resource
from api.models.employee import Employee
from database import db
import uuid
from datetime import datetime, timedelta
from flask import request
from api.service.email.email_service import EmailService
import os

invite_ns = Namespace('invite', description='Employee Invitation')

@invite_ns.route('/invite-employee')
class ProjectInviteEmployee(Resource):
    def post(self):
        data = request.get_json(force=True)
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()

        # Check if employee exists
        employee = Employee.query.filter_by(email=email).first()
        if employee and employee.is_active:
            return {"message": "Employee already registered. You can assign tasks and projects."}, 200

        # Create pending employee with activation token and expiry
        token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(hours=24)
        
        if not employee:
            new_employee = Employee(
                name=name,
                email=email,
                is_active=False,
                activation_token=token,
                activation_token_expiry=expiry
            )
            db.session.add(new_employee)
        else:
            employee.activation_token = token
            employee.activation_token_expiry = expiry
        db.session.commit()

        email_service = EmailService()  
        email_service.send_activation_email(email, f"{os.getenv('BASE_APP_DOMAIN_URL')}/activate/{token}")
        # TODO: Send activation email with link: f"<frontend_url>/activate/{token}"
        return {"message": "Invitation sent. Activation email will be sent.", "activation_token": token, "expires_at": expiry.isoformat()}, 201
