from flask_restx import Namespace, Resource, fields
from api.models.project import Project
from database import db

api = Namespace('projects', description='Project operations')

project_model = api.model('Project', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(required=True),
    'description': fields.String(required=False),
    'created_at': fields.String,
    'updated_at': fields.String,
})

@api.route('/')
class ProjectList(Resource):
    @api.marshal_list_with(project_model)
    def get(self) -> list[Project]:
        """Get all projects"""
        return Project.query.all()

    @api.expect(project_model)
    @api.marshal_with(project_model, code=201)
    def post(self) -> tuple[Project, int]:
        """Create a new project"""
        data = api.payload
        project = Project(name=data['name'], description=data.get('description'))
        db.session.add(project)
        db.session.commit()
        return project, 201
