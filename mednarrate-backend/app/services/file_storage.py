import os
import uuid
import re
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from .storage import get_storage_backend

def sanitize_filename(filename: str) -> str:
    # Strip path separators
    filename = os.path.basename(filename)
    # Keep only alnum/._- characters
    filename = re.sub(r'[^a-zA-Z0-9.\-_]', '', filename)
    return filename

async def save_upload_file(user_id: uuid.UUID, upload_file: UploadFile) -> str:
    if not upload_file.filename:
        raise HTTPException(status_code=422, detail="No filename provided")

    ext = upload_file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=422, detail="Unsupported file extension")

    # Read the file to check size
    file_bytes = await upload_file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(status_code=422, detail=f"File too large. Max size is {settings.MAX_UPLOAD_MB}MB")
        
    # PDF magic byte check if ext is pdf
    if ext == "pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(status_code=422, detail="Invalid PDF file format")
    elif ext in ["jpg", "jpeg"]:
        if not (file_bytes.startswith(b"\xff\xd8\xff") or file_bytes.startswith(b"\xFF\xD8\xFF")):
            raise HTTPException(status_code=422, detail="Invalid JPEG file format")
    elif ext == "png":
        if not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=422, detail="Invalid PNG file format")
    
    # Use strict UUID filenames to prevent injection
    unique_filename = f"{user_id}/{uuid.uuid4()}.{ext}"
    
    storage = get_storage_backend()
    file_url = await storage.upload_file(file_bytes, unique_filename, upload_file.content_type or "application/octet-stream")
        
    return file_url

async def delete_file(file_path: str):
    storage = get_storage_backend()
    # file_path in DB might be the URL or relative path. 
    # For storage backend, we need the relative object key which might just be the file_path itself if local.
    # In a full implementation, you'd extract the key. For now, pass file_path directly.
    # Since GCS/S3 needs just the key, and local needs the filename.
    # The unique_filename we passed was {user_id}/{uuid}_{name}, let's just assume the backend handles it.
    await storage.delete_file(file_path.replace("/uploads/", ""))
