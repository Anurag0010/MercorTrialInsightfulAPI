from flask import Blueprint

# Create blueprints for each route module
project_bp = Blueprint('project', __name__)
employee_bp = Blueprint('employee', __name__)
task_bp = Blueprint('task', __name__)
time_tracking_bp = Blueprint('time_tracking', __name__)
screenshot_bp = Blueprint('screenshot', __name__)

# Import routes to register them with blueprints
from . import project_routes
from . import employee_routes
from . import task_routes
from . import time_tracking_routes
from . import screenshot_routes
from .auth_routes import auth_bp

# List of all blueprints to register with the app
blueprints = [
    (project_bp, '/api'),
    (employee_bp, '/api'),
    (task_bp, '/api'),
    (time_tracking_bp, '/api'),
    (screenshot_bp, '/api'),
    (auth_bp, '/api')
]
