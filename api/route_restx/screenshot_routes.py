from flask_restx import Namespace, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage
from flask import request, current_app
from api.models.screenshot import Screenshot
from database import db
import os
from datetime import datetime
from constants import SCREENSHOT_STORAGE_CONTAINER
import uuid

api = Namespace('screenshots', description='Screenshot operations')

screenshot_model = api.model('Screenshot', {
    'id': fields.Integer(readOnly=True),
    'employee_id': fields.Integer(required=True),
    'project_id': fields.Integer(required=True),
    'task_id': fields.Integer(required=True),
    'file_path': fields.String(readOnly=True),
    'image_url': fields.String(readOnly=True),
    'captured_at': fields.DateTime(description='Timestamp when the screenshot was taken')
})

# File upload parser
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='Screenshot image file')
upload_parser.add_argument('employee_id', type=int, required=True, help='Employee ID')
upload_parser.add_argument('project_id', type=int, required=True, help='Project ID')
upload_parser.add_argument('task_id', type=int, required=True, help='Task ID')

@api.route('/')
class ScreenshotList(Resource):
    @api.marshal_list_with(screenshot_model)
    def get(self) -> list[Screenshot]:
        """Get all screenshots"""
        return Screenshot.query.all()

    @api.expect(upload_parser)
    @api.marshal_with(screenshot_model, code=201)
    def post(self) -> tuple[Screenshot, int]:
        """Upload a new screenshot (with UUID as file name and blob key)"""
        args = upload_parser.parse_args()
        file = args['file']
        
        # Generate a UUID for the screenshot file name
        screenshot_uuid = str(uuid.uuid4())
        container_name = 'screenshot'  # As per user requirement
        blob_name = screenshot_uuid
        
        try:
            # Get blob storage from app context
            azure_storage = current_app.extensions.get('azure_storage')
            if not azure_storage:
                api.abort(500, "Azure Storage not configured")
            
            # Upload the file to Azure Blob Storage
            file_data = file.read()
            image_url = azure_storage.upload_file(container_name, blob_name, file_data)
            
            # Create a new screenshot record in the database
            screenshot = Screenshot(
                employee_id=args['employee_id'],
                project_id=args['project_id'],
                task_id=args['task_id'],
                file_path=blob_name,
                image_url=image_url,
                captured_at=datetime.utcnow()
            )
            db.session.add(screenshot)
            db.session.commit()
            return screenshot, 201
        except Exception as e:
            db.session.rollback()
            api.abort(500, f"Failed to upload screenshot: {str(e)}")


@api.route('/<int:id>')
@api.param('id', 'The screenshot identifier')
@api.response(404, 'Screenshot not found')
class ScreenshotResource(Resource):
    @api.marshal_with(screenshot_model)
    def get(self, id: int) -> Screenshot:
        """Get a screenshot by ID"""
        screenshot = Screenshot.query.get_or_404(id)
        return screenshot

    @api.response(204, 'Screenshot deleted')
    def delete(self, id: int) -> tuple[str, int]:
        """Delete a screenshot"""
        screenshot = Screenshot.query.get_or_404(id)
        
        # Delete from Azure Blob Storage first
        try:
            azure_storage = current_app.extensions.get('azure_storage')
            if azure_storage and screenshot.file_path:
                # Extract container and blob name from file_path
                container_name = 'screenshots'
                blob_name = screenshot.id
                
                # Delete the blob
                azure_storage.delete_file(container_name, blob_name)
        except Exception as e:
            api.abort(500, f"Failed to delete screenshot from storage: {str(e)}")
        
        # Delete from database
        db.session.delete(screenshot)
        db.session.commit()
        
        return '', 204
