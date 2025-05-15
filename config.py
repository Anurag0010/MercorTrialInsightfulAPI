import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Azure Blob Storage Configuration
    AZURE_STORAGE_ACCOUNT_NAME = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_CONTAINER_NAME = os.environ.get('AZURE_STORAGE_CONTAINER_NAME')
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    
    # Azure Blob Service Client
    @classmethod
    def get_blob_service_client(cls):
        try:
            return BlobServiceClient.from_connection_string(cls.AZURE_STORAGE_CONNECTION_STRING)
        except Exception as e:
            print(f"Error creating Blob Service Client: {e}")
            return None
    
    # PostgreSQL Configuration
    POSTGRES_SERVER = os.environ.get('POSTGRES_SERVER')
    POSTGRES_DB = os.environ.get('POSTGRES_DB')
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_SCHEMA = os.environ.get('POSTGRES_SCHEMA', 'mercor')

    if all([POSTGRES_SERVER, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
        # Azure PostgreSQL connection string with schema
        from urllib.parse import quote_plus
        password = quote_plus(POSTGRES_PASSWORD)
        SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{password}@{POSTGRES_SERVER}/{POSTGRES_DB}?options=-c%20search_path={POSTGRES_SCHEMA}'
    else:
        # Fallback to SQLite for development
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "app.db")}'
    
    AZURE_STORAGE_ACCOUNT = os.getenv('AZURE_STORAGE_ACCOUNT')
    AZURE_STORAGE_KEY = os.getenv('AZURE_STORAGE_KEY')
    AZURE_CONTAINER_NAME = os.getenv('AZURE_CONTAINER_NAME')
    
    @staticmethod
    def get_blob_service_client():
        if not Config.AZURE_STORAGE_ACCOUNT or not Config.AZURE_STORAGE_KEY:
            return None
        
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={Config.AZURE_STORAGE_ACCOUNT};AccountKey={Config.AZURE_STORAGE_KEY};EndpointSuffix=core.windows.net"
        return BlobServiceClient.from_connection_string(connect_str)
    
    @classmethod
    def is_production(cls):
        return cls.POSTGRES_SERVER is not None
