import pytest
import os
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.orphan_file import OrphanFile
from app.services.orphan_cleanup import retry_pending_orphan_files
from app.services.file_storage import save_upload_file

@pytest.mark.asyncio
async def test_retry_pending_orphan_files(db_session: AsyncSession):
    # Setup test file
    test_user_id = str(uuid.uuid4())
    test_filename = "test_orphan.pdf"
    file_path = f"/uploads/{test_user_id}/{test_filename}"
    
    # Actually create the physical file so we can delete it
    base_dir = os.getenv("STORAGE_ROOT", "storage")
    full_dir = os.path.join(base_dir, test_user_id)
    os.makedirs(full_dir, exist_ok=True)
    full_path = os.path.join(full_dir, test_filename)
    with open(full_path, "w") as f:
        f.write("test content")

    # 1. Create a pending orphan for the real file
    o1 = OrphanFile(file_path=file_path, status="pending")
    
    # 2. Create a pending orphan for a non-existent file
    o2 = OrphanFile(file_path="/uploads/non_existent/file.pdf", status="pending")
    
    # 3. Create a pending orphan for an invalid path
    o3 = OrphanFile(file_path="/etc/passwd", status="pending")
    
    db_session.add_all([o1, o2, o3])
    await db_session.commit()
    
    # Run cleanup with mocked delete_file
    from unittest.mock import patch
    
    async def mock_delete_file(fp):
        if fp == "/etc/passwd":
            raise PermissionError("Access denied")
        if fp == "/uploads/non_existent/file.pdf":
            raise FileNotFoundError("Not found")
        # For the valid file, it succeeds
        return None

    with patch("app.services.orphan_cleanup.delete_file", side_effect=mock_delete_file):
        count = await retry_pending_orphan_files(db_session)
        
    assert count == 3
    
    # Verify o1 (successful delete)
    await db_session.refresh(o1)
    assert o1.status == "resolved"
    assert o1.retry_count == 1
    assert o1.last_attempt_at is not None
    
    # Verify o2 (file not found, should be resolved)
    await db_session.refresh(o2)
    assert o2.status == "resolved"
    assert o2.retry_count == 1
    
    # Verify o3 (invalid path, failed)
    await db_session.refresh(o3)
    assert o3.status == "failed"
    assert o3.retry_count == 1
    assert o3.last_error_code == "invalid_path"

    # 4. Verify resolved/failed records not retried
    with patch("app.services.orphan_cleanup.delete_file", side_effect=mock_delete_file):
        count2 = await retry_pending_orphan_files(db_session)
    assert count2 == 0
