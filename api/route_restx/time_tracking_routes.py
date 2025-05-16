import os
import uuid
from datetime import datetime
import mimetypes
from flask import current_app
from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage
from api.models.time_log import TimeLog
from api.models.task import Task
from database import db
from api.route_restx.auth_decorators import role_required, check_mac_address
from api.service.azure_blob import AzureBlobStorage

api = Namespace('timelogs', description='Time Log operations')

time_log_model = api.model('TimeLog', {
    'id': fields.Integer(readOnly=True),
    'employee_id': fields.Integer(required=True),
    'task_id': fields.Integer(required=True),
    'project_id': fields.Integer(required=True),
    'start_time': fields.String,
    'end_time': fields.String,
    'duration': fields.Float,
    'is_screenshot_permission_enabled': fields.Boolean,
    'ip_address': fields.String,
    'mac_address': fields.String,
    # Screenshot fields
    'file_path': fields.String(readOnly=True),
    'image_url': fields.String(readOnly=True),
    'captured_at': fields.DateTime(description='Timestamp when the screenshot was taken')
})

@api.route('/')
class TimeLogList(Resource):
    @api.marshal_list_with(time_log_model)
    @role_required(['admin'])
    def get(self) -> list[TimeLog]:
        """Get all time logs"""
        return TimeLog.query.all()

    upload_parser = reqparse.RequestParser()
    upload_parser.add_argument('employee_id', type=int, required=True, help='Employee ID')
    upload_parser.add_argument('task_id', type=int, required=True, help='Task ID')
    upload_parser.add_argument('project_id', type=int, required=True, help='Project ID')
    upload_parser.add_argument('start_time', type=str, required=True, help='Start time')
    upload_parser.add_argument('end_time', type=str, required=True, help='End time')
    upload_parser.add_argument('duration', type=float, required=True, help='Duration in seconds')
    upload_parser.add_argument('is_screenshot_permission_enabled', type=bool, required=False)
    upload_parser.add_argument('ip_address', type=str, required=False)
    upload_parser.add_argument('mac_address', type=str, required=False)
    upload_parser.add_argument('file', location='files', type=FileStorage, required=False, help='Screenshot image file')

    @api.expect(upload_parser)
    @role_required(['employee', 'employer'])
    @check_mac_address
    @api.marshal_with(time_log_model, code=201)
    def post(self) -> tuple[TimeLog, int]:
        """Create a new time log (optionally with screenshot upload)"""
        args = upload_parser.parse_args()
        file = args.get('file')
        file_path = None
        image_url = None
        captured_at = None
        if file:
            # Generate a GUID for the file ID
            file_id = str(uuid.uuid4())
            blob_name = file_id
            container_name = os.environ.get('SCREENSHOT_STORAGE_CONTAINER', 'screenshots')
            # Get Azure connection string from config/env
            azure_blob = AzureBlobStorage()
            file_data = file.read()
            content_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            image_url = azure_blob.upload_file(container_name, blob_name, file_data, content_type)
            file_path = blob_name
            captured_at = datetime.utcnow()
        time_log = TimeLog(
            employee_id=args['employee_id'],
            task_id=args['task_id'],
            project_id=args['project_id'],
            start_time=args.get('start_time'),
            end_time=args.get('end_time'),
            duration=args.get('duration'),
            is_screenshot_permission_enabled=args.get('is_screenshot_permission_enabled'),
            ip_address=args.get('ip_address'),
            mac_address=args.get('mac_address'),
            file_path=file_path,
            image_url=image_url,
            captured_at=captured_at
        )
        # Add the duration to minutes in task assigned to this user
        task = Task.query.get(args['task_id'])
        if task:
            task.minutes_spent += args['duration']
        db.session.add(time_log)
        db.session.commit()
        return time_log, 201

    @api.marshal_list_with(time_log_model)
    @role_required(['admin', 'employer'])
    def list(self, project_id: int, task_id: int, start_date: str, end_date: str, page: int, page_size: int) -> list[TimeLog]:
        """Get time logs for a project and task within a date range"""
        # Only max duration of 1 hr duration screenshots are allowed
        time_logs = TimeLog.query.filter_by(project_id=project_id, task_id=task_id).filter(TimeLog.start_time.between(start_date, end_date)).all()
        time_logs = time_logs[(page - 1) * page_size: page * page_size]
        return time_logs