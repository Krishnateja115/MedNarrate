from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """Abstract base class for all storage backends (local, gcs, s3)."""
    
    @abstractmethod
    async def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """
        Uploads a file to the storage backend.
        
        Args:
            file_bytes: The raw bytes of the file.
            filename: The target filename.
            content_type: The MIME type of the file.
            
        Returns:
            The public or accessible URL/path of the uploaded file.
        """
        pass

    @abstractmethod
    async def download_file(self, filename: str) -> bytes:
        """
        Downloads a file from the storage backend.
        
        Args:
            filename: The name of the file to download.
            
        Returns:
            The raw bytes of the file.
        """
        pass

    @abstractmethod
    async def delete_file(self, filename: str) -> bool:
        """
        Deletes a file from the storage backend.
        
        Args:
            filename: The name of the file to delete.
            
        Returns:
            True if deleted successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def file_exists(self, filename: str) -> bool:
        """
        Checks if a file exists in the storage backend.
        
        Args:
            filename: The name of the file to check.
            
        Returns:
            True if it exists, False otherwise.
        """
        pass
