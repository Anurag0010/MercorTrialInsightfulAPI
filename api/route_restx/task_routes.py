from flask_restx import Namespace, Resource, fields
from api.models.task import Task
from database import db
from flask_jwt_extended import jwt_required, get_jwt

api = Namespace('tasks', description='Task operations')

time_log_model = api.model('TimeLogSummary', {
    'id': fields.Integer(readOnly=True),
    'employee_id': fields.Integer(),
    'employee_name': fields.String(attribute=lambda x: x.employee.name if x.employee else None),
    'start_time': fields.DateTime(),
    'end_time': fields.DateTime(),
    'duration': fields.Integer(),  # in seconds
    'notes': fields.String()
})

# Detailed task model
detailed_task_model = api.model('DetailedTask', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(required=True),
    'description': fields.String(),
    'status': fields.String(),
    'project_id': fields.Integer(),
    'project_name': fields.String(attribute=lambda x: x.project.name if x.project else None),
    'project_hourly_rate': fields.Float(attribute=lambda x: float(x.project.hourly_rate) if x.project and x.project.hourly_rate else None),
    'created_at': fields.DateTime(),
    'updated_at': fields.DateTime(),
    'minutes_spent': fields.Integer(),
    'assignees': fields.List(fields.Nested(api.model('AssigneeSummary', {
        'id': fields.Integer(),
        'name': fields.String(),
        'email': fields.String()
    })), attribute=lambda x: [{'id': e.id, 'name': e.name, 'email': e.email} for e in x.employees]),
    'time_logs': fields.List(fields.Nested(time_log_model))
})

task_model = api.model('Task', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(required=True),
    'description': fields.String(required=False),
    'status': fields.String(required=False),
})

detailed_task_model 

@api.route('/')
class TaskList(Resource):
    @api.marshal_list_with(task_model)
    def get(self) -> list[Task]:
        """Get all tasks"""
        return Task.query.all()

    @api.expect(task_model)
    @api.marshal_with(task_model, code=201)
    def post(self) -> tuple[Task, int]:
        """Create a new task"""
        data = api.payload
        task = Task(name=data['name'], description=data.get('description'), status=data.get('status'))
        db.session.add(task)
        db.session.commit()
        return task, 201


@api.route('/')
class TaskList(Resource):
    @api.marshal_list_with(task_model)
    def get(self) -> list[Task]:
        """Get all tasks"""
        return Task.query.all()

    @api.expect(task_model)
    @api.marshal_with(task_model, code=201)
    def post(self) -> tuple[Task, int]:
        """Create a new task"""
        data = api.payload
        task = Task(name=data['name'], description=data.get('description'), status=data.get('status'))
        db.session.add(task)
        db.session.commit()
        return task, 201

@api.route('/<int:task_id>')
@api.param('task_id', 'The task identifier')
@api.response(404, 'Task not found')
class TaskDetail(Resource):
    @jwt_required()
    @api.marshal_with(detailed_task_model)
    def get(self, task_id):
        """Get task details including time entries"""
        # Get the identity of the current user
        claims = get_jwt()
        user_role = claims.get('role')
        user_id = claims.get('id')

        task = Task.query.get_or_404(task_id)

        # Check permissions
        if user_role == 'employee':
            # Employees can only view tasks assigned to them
            if not any(e.id == user_id for e in task.employees):
                api.abort(403, 'You do not have permission to view this task')
        elif user_role == 'employer':
            # Employers can only view tasks from their projects
            if task.project.employer_id != user_id:
                api.abort(403, 'You do not have permission to view this task')

        return task