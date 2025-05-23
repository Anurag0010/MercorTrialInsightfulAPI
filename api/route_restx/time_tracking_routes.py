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
from flask_jwt_extended import get_jwt

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

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('task_id', type=int, required=True, help='Task ID')
upload_parser.add_argument('project_id', type=int, required=True, help='Project ID')
upload_parser.add_argument('start_time', type=float, required=True, help='Start time as UNIX timestamp (seconds)')
upload_parser.add_argument('end_time', type=float, required=True, help='End time as UNIX timestamp (seconds)')
upload_parser.add_argument('duration', type=float, required=True, help='Duration in seconds')
upload_parser.add_argument('is_screenshot_permission_enabled', type=bool, required=False)
upload_parser.add_argument('ip_address', type=str, required=False)
upload_parser.add_argument('mac_address', type=str, required=False)
upload_parser.add_argument('file', location='files', type=FileStorage, required=False, help='Screenshot image file')

@api.route('/')
class TimeLogList(Resource):
    @api.expect(upload_parser)
    @role_required(['employee', 'employer'])
    @check_mac_address
    @api.marshal_with(time_log_model, code=201)
    def post(self) -> tuple[TimeLog, int]:
        """Create a new time log (optionally with screenshot upload)"""
        claims = get_jwt()
        employee_id = claims.get('id')
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
            
        # Convert UNIX timestamps to datetime
        start_time_dt = datetime.utcfromtimestamp(args.get('start_time')) if args.get('start_time') else None
        end_time_dt = datetime.utcfromtimestamp(args.get('end_time')) if args.get('end_time') else None
        time_log = TimeLog(
            employee_id=employee_id,
            task_id=args['task_id'],
            project_id=args['project_id'],
            start_time=start_time_dt,
            end_time=end_time_dt,
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
    def get(self) -> list[TimeLog]:
        """Get time logs for a project and task within a date range"""
        from flask import request
        project_id = request.args.get('project_id', type=int)
        task_id = request.args.get('task_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)
        
        time_logs = TimeLog.query.filter_by(project_id=project_id, task_id=task_id).filter(TimeLog.start_time.between(start_date, end_date)).all()
        time_logs = time_logs[(page - 1) * page_size: page * page_size]
        time_logs = [{
            'id': time_log.id,
            'employee_id': time_log.employee_id,
            'task_id': time_log.task_id,
            'project_id': time_log.project_id,
            'start_time': time_log.start_time,
            'end_time': time_log.end_time,
            'duration': time_log.duration,
            'is_screenshot_permission_enabled': time_log.is_screenshot_permission_enabled,
            'ip_address': time_log.ip_address,
            'mac_address': time_log.mac_address,
            'file_path': time_log.file_path,
            'image_url': time_log.image_url,
            'captured_at': time_log.captured_at
        } for time_log in time_logs]
        time_logs = sorted(time_logs, key=lambda x: x['start_time'], reverse=True) 
        return time_logs