import os
from azure.storage.blob import BlobServiceClient, ContentSettings

class AzureBlobStorage:
    def __init__(self):
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    def upload_file(self, container_name: str, blob_name: str, file_data: bytes, content_type: str = None) -> str:
        """
        Uploads a file to Azure Blob Storage.
        Args:
            container_name (str): The name of the blob container.
            blob_name (str): The name of the blob (filename in storage).
            file_data (bytes): The file data to upload.
            content_type (str): Optional MIME type.
        Returns:
            str: The URL of the uploaded blob.
        """
        container_client = self.blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
        blob_client = container_client.get_blob_client(blob_name)
        content_settings = ContentSettings(content_type=content_type) if content_type else None
        blob_client.upload_blob(file_data, overwrite=True, content_settings=content_settings)
        blob_url = blob_client.url
        return blob_url

    def delete_file(self, container_name: str, blob_name: str):
        """Deletes a file from Azure Blob Storage."""
        container_client = self.blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
