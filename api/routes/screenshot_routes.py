from flask import jsonify, request
from api.models.screenshot import Screenshot
from api.models.time_log import TimeLog
from database import db
from storage import AzureStorage
from datetime import datetime
from . import screenshot_bp

@screenshot_bp.route('/screenshots', methods=['GET'])
def list_screenshots():
    """Get all screenshots"""
    screenshots = Screenshot.query.all()
    return jsonify([{
        'id': s.id,
        'time_entry_id': s.time_entry_id,
        'image_url': s.image_url,
        'timestamp': s.timestamp.isoformat()
    } for s in screenshots])

@screenshot_bp.route('/screenshots', methods=['POST'])
def create_screenshot():
    """Create a new screenshot"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    data = request.form
    if 'time_entry_id' not in data:
        return jsonify({'error': 'Time entry ID is required'}), 400
    
    # Verify time entry exists
    time_entry = TimeLog.query.get_or_404(data['time_entry_id'])
    
    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Initialize Azure Storage
        storage = AzureStorage()
        
        # Generate unique filename
        timestamp = datetime.utcnow()
        filename = f"screenshots/{time_entry.id}/{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        
        # Upload to Azure Blob Storage
        image_url = storage.upload_file('screenshots', filename, image_file.read())
        
        # Create screenshot record
        screenshot = Screenshot(
            time_entry_id=time_entry.id,
            image_url=image_url,
            timestamp=timestamp
        )
        
        db.session.add(screenshot)
        db.session.commit()
        
        return jsonify({
            'id': screenshot.id,
            'time_entry_id': screenshot.time_entry_id,
            'image_url': screenshot.image_url,
            'timestamp': screenshot.timestamp.isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@screenshot_bp.route('/screenshots/<int:screenshot_id>', methods=['GET'])
def get_screenshot(screenshot_id):
    """Get a specific screenshot by ID"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    return jsonify({
        'id': screenshot.id,
        'time_entry': {
            'id': screenshot.time_entry.id,
            'task': {
                'id': screenshot.time_entry.task.id,
                'title': screenshot.time_entry.task.title
            },
            'employee': {
                'id': screenshot.time_entry.employee.id,
                'name': screenshot.time_entry.employee.name
            }
        },
        'image_url': screenshot.image_url,
        'timestamp': screenshot.timestamp.isoformat()
    })

@screenshot_bp.route('/screenshots/<int:screenshot_id>', methods=['DELETE'])
def delete_screenshot(screenshot_id):
    """Delete a screenshot"""
    screenshot = Screenshot.query.get_or_404(screenshot_id)
    
    try:
        # Initialize Azure Storage
        storage = AzureStorage()
        
        # Delete from Azure Blob Storage
        # Extract blob name from URL
        blob_name = screenshot.image_url.split('/')[-1]
        storage.delete_file('screenshots', blob_name)
        
        # Delete from database
        db.session.delete(screenshot)
        db.session.commit()
        
        return '', 204
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@screenshot_bp.route('/time-entries/<int:time_entry_id>/screenshots', methods=['GET'])
def get_time_entry_screenshots(time_entry_id):
    """Get all screenshots for a time entry"""
    TimeLog.query.get_or_404(time_entry_id)  # Verify time entry exists
    screenshots = Screenshot.query.filter_by(time_entry_id=time_entry_id).all()
    
    return jsonify([{
        'id': s.id,
        'image_url': s.image_url,
        'timestamp': s.timestamp.isoformat()
    } for s in screenshots])
