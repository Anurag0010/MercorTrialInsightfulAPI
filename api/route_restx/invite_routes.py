from flask_restx import Namespace, Resource, reqparse
from api.models.employee import Employee
from api.models.project import Project
from database import db
import uuid
from datetime import datetime, timedelta

invite_ns = Namespace('invite', description='Employee Invitation')

invite_parser = reqparse.RequestParser()
invite_parser.add_argument('email', type=str, required=True, help='Employee email')
invite_parser.add_argument('name', type=str, required=True, help='Employee name')

@invite_ns.route('/projects/<int:project_id>/invite-employee')
class ProjectInviteEmployee(Resource):
    @invite_ns.expect(invite_parser)
    def post(self, project_id):
        args = invite_parser.parse_args()
        email = args['email'].strip().lower()
        name = args['name'].strip()
        project = Project.query.get_or_404(project_id)

        # Check if employee exists
        employee = Employee.query.filter_by(email=email).first()
        if employee:
            # Add employee to project if not already
            if employee not in project.employees:
                project.employees.append(employee)
                db.session.commit()
            return {"message": "Employee already registered and added to project."}, 200

        # Create pending employee with activation token and expiry
        token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(hours=24)
        new_employee = Employee(
            name=name,
            email=email,
            is_active=False,
            activation_token=token,
            activation_token_expiry=expiry
        )
        db.session.add(new_employee)
        project.employees.append(new_employee)
        db.session.commit()

        # TODO: Send activation email with link: f"<frontend_url>/activate/{token}"
        return {"message": "Invitation sent. Activation email will be sent.", "activation_token": token, "expires_at": expiry.isoformat()}, 201
