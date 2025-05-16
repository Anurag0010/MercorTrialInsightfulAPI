from flask_restx import Namespace, Resource, fields
from api.models.time_log import TimeLog
from database import db

api = Namespace('timelogs', description='Time Log operations')

time_log_model = api.model('TimeLog', {
    'id': fields.Integer(readOnly=True),
    'employee_id': fields.Integer(required=True),
    'task_id': fields.Integer(required=True),
    'project_id': fields.Integer(required=True),
    'start_time': fields.String,
    'end_time': fields.String,
    'duration': fields.Float,
})

@api.route('/')
class TimeLogList(Resource):
    @api.marshal_list_with(time_log_model)
    def get(self) -> list[TimeLog]:
        """Get all time logs"""
        return TimeLog.query.all()

    @api.expect(time_log_model)
    @api.marshal_with(time_log_model, code=201)
    def post(self) -> tuple[TimeLog, int]:
        """Create a new time log"""
        data = api.payload
        time_log = TimeLog(
            employee_id=data['employee_id'],
            task_id=data['task_id'],
            project_id=data['project_id'],
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            duration=data.get('duration')
        )
        db.session.add(time_log)
        db.session.commit()
        return time_log, 201
