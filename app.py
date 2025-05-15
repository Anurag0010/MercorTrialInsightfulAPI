from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from database import db, init_db
from storage import AzureStorage
from api.routes import blueprints
from flask_restx import Api
import sys

# RESTx imports
from api.route_restx.user_routes import api as user_ns
from api.route_restx.project_routes import api as project_ns
from api.route_restx.employee_routes import api as employee_ns
from api.route_restx.task_routes import api as task_ns
from api.route_restx.time_tracking_routes import api as timelog_ns
from api.route_restx.screenshot_routes import api as screenshot_ns


from api.routes import blueprints
import os

# Load environment variables
load_dotenv()

def create_app_with_restx():
    # Initialize Flask app
    app = Flask(__name__)

    # Configure app
    app.config.from_object(Config)
    app.config['PROPAGATE_EXCEPTIONS'] = True  # This will propagate exceptions to see them in responses

    # Initialize extensions
    CORS(app)
    init_db(app)
    migrate = Migrate(app, db)

    # Initialize Flask-RESTx API (Swagger UI at /api/docs)
    restx_api = Api(app, version='1.0', title='RESTx API', doc='/api/docs')
    restx_api.add_namespace(user_ns, path='/api/users')
    restx_api.add_namespace(project_ns, path='/api/projects')
    restx_api.add_namespace(employee_ns, path='/api/employees')
    restx_api.add_namespace(task_ns, path='/api/tasks')
    restx_api.add_namespace(timelog_ns, path='/api/timelogs')
    restx_api.add_namespace(screenshot_ns, path='/api/screenshots')

    # Initialize Azure Storage
    storage = AzureStorage(app)

    # Add error handlers
    @app.errorhandler(Exception)
    def handle_error(error):
        code = 500
        if hasattr(error, 'code'):
            code = error.code
        return {'message': str(error), 'error': type(error).__name__}, code

    return app

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'

    # app.config.from_object(Config)
    # CORS(app)
    # init_db(app)
    # migrate = Migrate(app, db)
    # storage = AzureStorage(app)

    # Register all blueprints (traditional routes)
    from api.routes import blueprints
    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint)

    # Add error handlers
    @app.errorhandler(Exception)
    def handle_error(error):
        code = 500
        if hasattr(error, 'code'):
            code = error.code
        return {'message': str(error), 'error': type(error).__name__}, code

    return app

# Create the app instance
app = create_app_with_restx()

# app = Flask(__name__)

# @app.route('/ping', methods=['GET'])
# def ping():
#     return {"message": "pong"}, 200



if __name__ == '__main__':
    for rule in app.url_map.iter_rules():
        print(rule)
    app.run(debug=True)
