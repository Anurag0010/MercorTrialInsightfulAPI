from flask import Blueprint, request, jsonify
from models import Screenshot, db
from datetime import datetime

screenshot_bp = Blueprint('screenshot', __name__)

@screenshot_bp.route('/screenshots', methods=['GET'])
def list_screenshots():
    screenshots = Screenshot.query.all()
    return jsonify([s.to_dict() for s in screenshots])

@screenshot_bp.route('/screenshots', methods=['POST'])
def upload_screenshot():
    data = request.form
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400
    # Placeholder for Azure Blob upload logic
    # image_url = upload_to_blob(file)
    image_url = 'https://example.com/your_blob_url.jpg'
    screenshot = Screenshot(
        employee_id=data['employee_id'],
        image_url=image_url,
        taken_at=datetime.fromisoformat(data['taken_at']),
        permission_flag=data.get('permission_flag', True)
    )
    db.session.add(screenshot)
    db.session.commit()
    return jsonify(screenshot.to_dict()), 201
