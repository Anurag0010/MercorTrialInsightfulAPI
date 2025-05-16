import os
from flask import Flask
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine

# Create a global SQLAlchemy instance
db = SQLAlchemy()

def init_db(app: Flask) -> SQLAlchemy:
    """
    Initialize the database with the given Flask app.
    
    :param app: Flask application instance
    :return: Initialized SQLAlchemy instance
    """
    # Configure PostgreSQL connection
    server: Optional[str] = os.environ.get('POSTGRES_SERVER')
    database: Optional[str] = os.environ.get('POSTGRES_DB')
    username: Optional[str] = os.environ.get('POSTGRES_USER')
    password: Optional[str] = os.environ.get('POSTGRES_PASSWORD')
    schema: str = os.environ.get('POSTGRES_SCHEMA', 'mercor')
    
    if all([server, database, username, password]):
        # Use Azure PostgreSQL
        from urllib.parse import quote_plus
        encoded_password: str = quote_plus(password)  # URL encode the password
        # Set schema in connection options and search_path
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{encoded_password}@{server}/{database}?options=-c%20search_path={schema}'
        
        # Create schema if it doesn't exist
        from sqlalchemy import create_engine, text
        engine: Engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
            conn.commit()
    else:
        # Fallback to SQLite for development
        basedir: str = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "app.db")}'
    
    db.init_app(app)
    return db
