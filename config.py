import os
from typing import Optional, Union, ClassVar
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

class Config:
    # Flask
    SECRET_KEY: ClassVar[str] = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Azure Blob Storage Configuration
    AZURE_STORAGE_ACCOUNT_NAME: ClassVar[Optional[str]] = os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_CONTAINER_NAME: ClassVar[Optional[str]] = os.environ.get('AZURE_STORAGE_CONTAINER_NAME')
    AZURE_STORAGE_CONNECTION_STRING: ClassVar[Optional[str]] = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    
    # Azure Blob Service Client
    @classmethod
    def get_blob_service_client(cls) -> Optional[BlobServiceClient]:
        try:
            return BlobServiceClient.from_connection_string(cls.AZURE_STORAGE_CONNECTION_STRING)
        except Exception as e:
            print(f"Error creating Blob Service Client: {e}")
            return None
    
    # PostgreSQL Configuration
    POSTGRES_SERVER: ClassVar[Optional[str]] = os.environ.get('POSTGRES_SERVER')
    POSTGRES_DB: ClassVar[Optional[str]] = os.environ.get('POSTGRES_DB')
    POSTGRES_USER: ClassVar[Optional[str]] = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD: ClassVar[Optional[str]] = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_SCHEMA: ClassVar[str] = os.environ.get('POSTGRES_SCHEMA', 'mercor')

    # Database URI
    if all([POSTGRES_SERVER, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
        # Azure PostgreSQL connection string with schema
        from urllib.parse import quote_plus
        password = quote_plus(POSTGRES_PASSWORD)
        SQLALCHEMY_DATABASE_URI: ClassVar[str] = f'postgresql://{POSTGRES_USER}:{password}@{POSTGRES_SERVER}/{POSTGRES_DB}?options=-c%20search_path={POSTGRES_SCHEMA}'
    else:
        # Fallback to SQLite for development
        basedir: str = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI: ClassVar[str] = f'sqlite:///{os.path.join(basedir, "app.db")}'
    
    AZURE_STORAGE_ACCOUNT: ClassVar[Optional[str]] = os.getenv('AZURE_STORAGE_ACCOUNT')
    AZURE_STORAGE_KEY: ClassVar[Optional[str]] = os.getenv('AZURE_STORAGE_KEY')
    AZURE_CONTAINER_NAME: ClassVar[Optional[str]] = os.getenv('AZURE_CONTAINER_NAME')
    
    @staticmethod
    def get_blob_service_client() -> Optional[BlobServiceClient]:
        if not Config.AZURE_STORAGE_ACCOUNT or not Config.AZURE_STORAGE_KEY:
            return None
        
        connect_str: str = f"DefaultEndpointsProtocol=https;AccountName={Config.AZURE_STORAGE_ACCOUNT};AccountKey={Config.AZURE_STORAGE_KEY};EndpointSuffix=core.windows.net"
        return BlobServiceClient.from_connection_string(connect_str)
    
    @classmethod
    def is_production(cls) -> bool:
        return cls.POSTGRES_SERVER is not None
