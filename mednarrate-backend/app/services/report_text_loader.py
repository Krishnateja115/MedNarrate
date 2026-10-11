"""Load report bytes for extraction regardless of storage backend."""

import asyncio
import os
import tempfile

from app.core.config import settings
from app.services.storage import get_storage_backend
from app.services.text_extraction import extract_text_from_file


async def extract_report_text(file_path: str, file_type: str) -> str:
    """Extract a local report or stage a cloud object in a private temp file."""
    if settings.STORAGE_BACKEND == "local":
        return await asyncio.to_thread(extract_text_from_file, file_path, file_type)

    payload = await get_storage_backend().download_file(file_path)
    suffix = ".pdf" if file_type.lower() == "pdf" else ".png"
    with tempfile.TemporaryDirectory(prefix="mednarrate-report-") as temp_dir:
        staged_path = os.path.join(temp_dir, "report" + suffix)
        with open(staged_path, "wb") as staged_file:
            staged_file.write(payload)
        return await asyncio.to_thread(
            extract_text_from_file, staged_path, file_type
        )
