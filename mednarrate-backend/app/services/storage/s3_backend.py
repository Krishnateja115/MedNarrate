import os
import asyncio
from fastapi import HTTPException
from app.core.config import settings
from .base import StorageBackend

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class S3Backend(StorageBackend):
    """AWS S3 storage backend."""
    
    def __init__(self):
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 package is not installed.")
            
        self.bucket_name = settings.AWS_S3_BUCKET
        if not self.bucket_name:
            raise RuntimeError("AWS_S3_BUCKET is required for S3Backend.")
            
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize S3 client: {str(e)}")

    async def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        try:
            def _upload():
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=file_bytes,
                    ContentType=content_type
                )
            await asyncio.to_thread(_upload)
            
            # Assuming public for this implementation or returning the public URL structure.
            return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

    async def download_file(self, filename: str) -> bytes:
        try:
            def _download():
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=filename)
                return response['Body'].read()
            return await asyncio.to_thread(_download)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="File not found in S3.")
            raise HTTPException(status_code=500, detail=f"Failed to download from S3: {str(e)}")

    async def delete_file(self, filename: str) -> bool:
        try:
            def _delete():
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
            await asyncio.to_thread(_delete)
            return True
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete from S3: {str(e)}")

    async def file_exists(self, filename: str) -> bool:
        try:
            def _exists():
                self.s3_client.head_object(Bucket=self.bucket_name, Key=filename)
            await asyncio.to_thread(_exists)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            raise HTTPException(status_code=500, detail=f"Failed to check file in S3: {str(e)}")
