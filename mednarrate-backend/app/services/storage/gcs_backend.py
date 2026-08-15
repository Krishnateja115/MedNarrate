import os
import asyncio
from fastapi import HTTPException
from app.core.config import settings
from .base import StorageBackend

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class GCSBackend(StorageBackend):
    """Google Cloud Storage backend."""
    
    def __init__(self):
        if not GCS_AVAILABLE:
            raise RuntimeError("google-cloud-storage package is not installed.")
        
        self.bucket_name = settings.STORAGE_BUCKET_NAME
        self.project_id = settings.GCS_PROJECT_ID
        
        if not self.bucket_name:
            raise RuntimeError("STORAGE_BUCKET_NAME is required for GCSBackend.")
            
        try:
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GCS client: {str(e)}")

    async def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        blob = self.bucket.blob(filename)
        try:
            # Run the synchronous upload in a thread pool
            def _upload():
                blob.upload_from_string(file_bytes, content_type=content_type)
            await asyncio.to_thread(_upload)
            
            # If the bucket isn't public, you'd generate a signed URL here.
            # Assuming public for this implementation or returning the public URL structure.
            return f"https://storage.googleapis.com/{self.bucket_name}/{filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to GCS: {str(e)}")

    async def download_file(self, filename: str) -> bytes:
        blob = self.bucket.blob(filename)
        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found in GCS.")
        try:
            def _download():
                return blob.download_as_bytes()
            return await asyncio.to_thread(_download)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download from GCS: {str(e)}")

    async def delete_file(self, filename: str) -> bool:
        blob = self.bucket.blob(filename)
        if blob.exists():
            try:
                def _delete():
                    blob.delete()
                await asyncio.to_thread(_delete)
                return True
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete from GCS: {str(e)}")
        return False

    async def file_exists(self, filename: str) -> bool:
        blob = self.bucket.blob(filename)
        def _exists():
            return blob.exists()
        return await asyncio.to_thread(_exists)
