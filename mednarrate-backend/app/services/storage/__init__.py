from app.core.config import settings
from .base import StorageBackend
from .local_backend import LocalStorageBackend
from .gcs_backend import GCSBackend
from .s3_backend import S3Backend

def get_storage_backend() -> StorageBackend:
    """
    Factory function that returns the active storage backend based on configuration.
    """
    backend_type = settings.STORAGE_BACKEND.lower()
    
    if backend_type == "gcs":
        return GCSBackend()
    elif backend_type == "s3":
        return S3Backend()
    else:
        # Default to local storage
        return LocalStorageBackend()
