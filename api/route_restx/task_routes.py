from flask_restx import Namespace, Resource, fields
from api.models.task import Task
from database import db

api = Namespace('tasks', description='Task operations')

task_model = api.model('Task', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(required=True),
    'description': fields.String(required=False),
    'status': fields.String(required=False),
})

@api.route('/')
class TaskList(Resource):
    @api.marshal_list_with(task_model)
    def get(self):
        """Get all tasks"""
        return Task.query.all()

    @api.expect(task_model)
    @api.marshal_with(task_model, code=201)
    def post(self):
        """Create a new task"""
        data = api.payload
        task = Task(name=data['name'], description=data.get('description'), status=data.get('status'))
        db.session.add(task)
        db.session.commit()
        return task, 201
