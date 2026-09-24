import asyncio
import os

from fastapi import HTTPException

from app.core.config import settings

from .base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Local disk storage backend for development."""

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_file(
        self, file_bytes: bytes, filename: str, content_type: str
    ) -> str:
        filepath = os.path.join(self.upload_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        try:

            def _write():
                with open(filepath, "wb") as f:
                    written = f.write(file_bytes)
                if written != len(file_bytes):
                    raise IOError(
                        f"Incomplete write: expected {len(file_bytes)} bytes, wrote {written} bytes"
                    )
                actual_size = os.path.getsize(filepath)
                if actual_size != len(file_bytes):
                    raise IOError(
                        f"Disk file size mismatch: expected {len(file_bytes)} bytes, got {actual_size} bytes"
                    )

            await asyncio.to_thread(_write)
            # Returning a relative URL path suitable for local serving
            # Normalize to forward slashes for URL safety
            normalized_filename = filename.replace("\\", "/")
            return f"/uploads/{normalized_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save file locally: {str(e)}"
            )

    async def download_file(self, filename: str) -> bytes:
        filepath = os.path.join(self.upload_dir, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found.")
        try:

            def _read():
                with open(filepath, "rb") as f:
                    return f.read()

            return await asyncio.to_thread(_read)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read file locally: {str(e)}"
            )

    async def delete_file(self, filename: str) -> bool:
        filepath = os.path.join(self.upload_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to delete file locally: {str(e)}"
                )
        return False

    async def file_exists(self, filename: str) -> bool:
        filepath = os.path.join(self.upload_dir, filename)
        return os.path.exists(filepath)
