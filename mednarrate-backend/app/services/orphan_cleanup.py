import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.orphan_file import OrphanFile
from app.services.file_storage import delete_file

async def retry_pending_orphan_files(db: AsyncSession, limit: int = 100):
    stmt = select(OrphanFile).where(OrphanFile.status == "pending").limit(limit)
    result = await db.execute(stmt)
    orphans = result.scalars().all()
    
    for orphan in orphans:
        orphan.retry_count += 1
        orphan.last_attempt_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        if ".." in orphan.file_path or orphan.file_path.startswith("/"):
            orphan.status = "failed"
            orphan.last_error_code = "invalid_path"
            continue
            
        try:
            await delete_file(orphan.file_path)
            orphan.status = "resolved"
            orphan.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            orphan.last_error_code = None
        except PermissionError:
            orphan.status = "failed"
            orphan.last_error_code = "permission_error"
        except FileNotFoundError:
            orphan.status = "resolved"
            orphan.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            orphan.last_error_code = None
        except Exception:
            orphan.status = "failed"
            orphan.last_error_code = "unknown"
            
    await db.commit()
    return len(orphans)
