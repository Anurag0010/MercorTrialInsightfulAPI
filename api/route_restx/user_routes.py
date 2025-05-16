from flask_restx import Namespace, Resource, fields
from api.models.user import User
from database import db

api = Namespace('users', description='User operations')

user_model = api.model('User', {
    'id': fields.Integer(readOnly=True),
    'username': fields.String(required=True),
    'email': fields.String(required=False),
})

@api.route('/')
class UserList(Resource):
    @api.marshal_list_with(user_model)
    def get(self) -> list[User]:
        """Get all users"""
        return User.query.all()
