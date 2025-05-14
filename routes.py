from flask import Blueprint, request, jsonify
from app import db
# Removed import as User model is not found
from utils.blob_storage import upload_to_blob, get_blob_url

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Example route for user profile with image upload
@api_bp.route('/profile', methods=['POST'])
def create_profile():
    try:
        data = request.form.to_dict()
        image = request.files.get('image')
        
        # Create user profile
        user = User(
            username=data.get('username'),
            email=data.get('email')
        )
        
        # Upload image if provided
        if image:
            image_url = upload_to_blob(image)
            user.profile_image_url = image_url
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "message": "Profile created successfully",
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
