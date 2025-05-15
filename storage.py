from azure.storage.blob import BlobServiceClient
import os

class AzureStorage:
    def __init__(self, app=None):
        self.blob_service_client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize Azure Blob Storage with Flask app configuration."""
        connection_string = app.config.get('AZURE_STORAGE_CONNECTION_STRING')
        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        else:
            account_name = app.config.get('AZURE_STORAGE_ACCOUNT')
            account_key = app.config.get('AZURE_STORAGE_KEY')
            if account_name and account_key:
                conn_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
                self.blob_service_client = BlobServiceClient.from_connection_string(conn_str)

    def upload_file(self, container_name, blob_name, data):
        """Upload a file to Azure Blob Storage."""
        if not self.blob_service_client:
            raise Exception("Azure Storage not configured")
        
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(data, overwrite=True)
        return blob_client.url

    def download_file(self, container_name, blob_name):
        """Download a file from Azure Blob Storage."""
        if not self.blob_service_client:
            raise Exception("Azure Storage not configured")
        
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        return blob_client.download_blob().readall()

    def delete_file(self, container_name, blob_name):
        """Delete a file from Azure Blob Storage."""
        if not self.blob_service_client:
            raise Exception("Azure Storage not configured")
        
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
