import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Azure PostgreSQL (Optional)
    POSTGRES_SERVER = os.getenv('POSTGRES_SERVER')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    
    # Azure Blob Storage
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
