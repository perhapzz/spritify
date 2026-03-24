"""
Storage Service - Handles file storage (local or Azure Blob)
"""
import os
from typing import Optional
from azure.storage.blob import BlobServiceClient
from app.config import settings


class StorageService:
    def __init__(self):
        self.use_azure = (
            settings.azure_storage_connection_string is not None
            and not settings.use_local_storage
        )

        if self.use_azure:
            self.blob_service = BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
        else:
            self.blob_service = None

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        container: str = "uploads",
    ) -> str:
        """Upload a file and return its URL/path"""
        if self.use_azure:
            return await self._upload_to_azure(file_content, filename, container)
        else:
            return await self._save_locally(file_content, filename, container)

    async def _upload_to_azure(
        self,
        file_content: bytes,
        filename: str,
        container: str,
    ) -> str:
        """Upload to Azure Blob Storage"""
        container_name = (
            settings.azure_storage_container_uploads
            if container == "uploads"
            else settings.azure_storage_container_outputs
        )

        blob_client = self.blob_service.get_blob_client(
            container=container_name,
            blob=filename
        )
        blob_client.upload_blob(file_content, overwrite=True)

        return blob_client.url

    async def _save_locally(
        self,
        file_content: bytes,
        filename: str,
        container: str,
    ) -> str:
        """Save to local filesystem"""
        directory = f"static/{container}"
        os.makedirs(directory, exist_ok=True)

        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(file_content)

        return f"/static/{container}/{filename}"

    async def get_file_url(self, filename: str, container: str = "outputs") -> str:
        """Get the URL for a file"""
        if self.use_azure:
            container_name = (
                settings.azure_storage_container_uploads
                if container == "uploads"
                else settings.azure_storage_container_outputs
            )
            blob_client = self.blob_service.get_blob_client(
                container=container_name,
                blob=filename
            )
            return blob_client.url
        else:
            return f"/static/{container}/{filename}"

    async def delete_file(self, filename: str, container: str) -> bool:
        """Delete a file"""
        if self.use_azure:
            container_name = (
                settings.azure_storage_container_uploads
                if container == "uploads"
                else settings.azure_storage_container_outputs
            )
            blob_client = self.blob_service.get_blob_client(
                container=container_name,
                blob=filename
            )
            blob_client.delete_blob()
            return True
        else:
            filepath = f"static/{container}/{filename}"
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
