import os
from flask_sqlalchemy import SQLAlchemy

# Create a global SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """
    Initialize the database with the given Flask app.
    
    :param app: Flask application instance
    :return: Initialized SQLAlchemy instance
    """
    # Configure PostgreSQL connection
    server = os.environ.get('POSTGRES_SERVER')
    database = os.environ.get('POSTGRES_DB')
    username = os.environ.get('POSTGRES_USER')
    password = os.environ.get('POSTGRES_PASSWORD')
    schema = os.environ.get('POSTGRES_SCHEMA', 'mercor')
    
    if all([server, database, username, password]):
        # Use Azure PostgreSQL
        from urllib.parse import quote_plus
        password = quote_plus(password)  # URL encode the password
        # Set schema in connection options and search_path
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@{server}/{database}?options=-c%20search_path={schema}'
        
        # Create schema if it doesn't exist
        from sqlalchemy import create_engine, text
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
            conn.commit()
    else:
        # Fallback to SQLite for development
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "app.db")}'
    
    db.init_app(app)
    return db
