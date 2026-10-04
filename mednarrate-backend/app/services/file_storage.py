import os
import re
import uuid

from fastapi import HTTPException, UploadFile

from app.core.config import settings

from .storage import get_storage_backend


def sanitize_filename(filename: str) -> str:
    # Strip path separators & path traversal components
    filename = os.path.basename(filename).replace("\\", "/").split("/")[-1]
    # Keep only alnum/._- characters
    filename = re.sub(r"[^a-zA-Z0-9.\-_]", "", filename)
    return filename or "upload"


def _enforce_parser_budgets(ext: str, data: bytes) -> None:
    """Reject files whose *structure* would make OCR/extraction expensive.

    Raw byte size is not enough: a small PDF can declare thousands of pages and a
    small PNG can decode to gigapixels. Only headers/page trees are inspected
    here; pixel data is never decoded.
    """
    if ext == "pdf":
        try:
            import fitz  # PyMuPDF

            with fitz.open(stream=data, filetype="pdf") as doc:
                if doc.needs_pass or doc.is_encrypted:
                    raise HTTPException(
                        status_code=422, detail="Encrypted PDFs are not supported"
                    )
                if doc.page_count > settings.MAX_PDF_PAGES:
                    raise HTTPException(
                        status_code=422,
                        detail=f"PDF has too many pages (max {settings.MAX_PDF_PAGES})",
                    )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid PDF file format")
    else:
        try:
            import io

            from PIL import Image

            with Image.open(io.BytesIO(data)) as img:  # header-only, lazy decode
                width, height = img.size
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid image file")
        if width * height > settings.MAX_IMAGE_PIXELS:
            raise HTTPException(
                status_code=422,
                detail="Image dimensions too large",
            )


async def save_upload_file(user_id: uuid.UUID, upload_file: UploadFile) -> str:
    if not upload_file.filename:
        raise HTTPException(status_code=422, detail="No filename provided")

    safe_name = sanitize_filename(upload_file.filename)
    ext = safe_name.split(".")[-1].lower() if "." in safe_name else ""
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=422, detail="Unsupported file extension")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024

    # Read up to max_bytes + 1 to check if it exceeds the limit without loading the whole file into RAM
    file_bytes = await upload_file.read(max_bytes + 1024)
    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="Empty file payload")

    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=422,
            detail=f"File too large. Max size is {settings.MAX_UPLOAD_MB}MB",
        )
    # PDF magic byte check if ext is pdf
    if ext == "pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(status_code=422, detail="Invalid PDF file format")
    elif ext in ["jpg", "jpeg"]:
        if not (
            file_bytes.startswith(b"\xff\xd8\xff")
            or file_bytes.startswith(b"\xff\xd8\xff")
        ):
            raise HTTPException(status_code=422, detail="Invalid JPEG file format")
    elif ext == "png":
        if not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=422, detail="Invalid PNG file format")

    _enforce_parser_budgets(ext, file_bytes)

    # Use strict UUID filenames to prevent injection
    unique_filename = f"{user_id}/{uuid.uuid4()}.{ext}"

    storage = get_storage_backend()
    file_url = await storage.upload_file(
        file_bytes,
        unique_filename,
        upload_file.content_type or "application/octet-stream",
    )

    return file_url


async def delete_file(file_path: str):
    storage = get_storage_backend()
    # The object key is stored directly in file_path
    await storage.delete_file(file_path)
