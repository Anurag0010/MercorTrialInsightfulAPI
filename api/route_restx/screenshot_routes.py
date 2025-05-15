from flask_restx import Namespace, Resource, fields
from api.models.screenshot import Screenshot
from database import db

api = Namespace('screenshots', description='Screenshot operations')

screenshot_model = api.model('Screenshot', {
    'id': fields.Integer(readOnly=True),
    'employee_id': fields.Integer(required=True),
    'image_url': fields.String(required=True),
    'timestamp': fields.String,
})

@api.route('/')
class ScreenshotList(Resource):
    @api.marshal_list_with(screenshot_model)
    def get(self):
        """Get all screenshots"""
        return Screenshot.query.all()

    @api.expect(screenshot_model)
    @api.marshal_with(screenshot_model, code=201)
    def post(self):
        """Create a new screenshot"""
        data = api.payload
        screenshot = Screenshot(
            employee_id=data['employee_id'],
            image_url=data['image_url'],
            timestamp=data.get('timestamp')
        )
        db.session.add(screenshot)
        db.session.commit()
        return screenshot, 201
