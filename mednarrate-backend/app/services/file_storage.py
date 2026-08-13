import os
import uuid
import re
from fastapi import UploadFile, HTTPException
from app.core.config import settings

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
    
    safe_filename = sanitize_filename(upload_file.filename)
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)
        
    return file_path

def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
