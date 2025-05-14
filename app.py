from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
import os
# Import and register blueprints
from api.employee import employee_bp
from api.project import project_bp
from api.task import task_bp
from api.time_tracking import time_tracking_bp
from api.screenshot import screenshot_bp

# Load environment variables
load_dotenv()

# Create global db object
db = SQLAlchemy()

def create_app():
    # Initialize Flask app
    app = Flask(__name__)

    # Configure app
    app.config.from_object(Config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(employee_bp, url_prefix='/api')
    app.register_blueprint(project_bp, url_prefix='/api')
    app.register_blueprint(task_bp, url_prefix='/api')
    app.register_blueprint(time_tracking_bp, url_prefix='/api')
    app.register_blueprint(screenshot_bp, url_prefix='/api')

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
