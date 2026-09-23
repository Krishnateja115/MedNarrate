from fastapi import APIRouter, Depends
from typing import List

from app.core.admin_auth import AdminContext, require_permission
from app.services.scheduler import get_all_jobs

router = APIRouter()

@router.get("")
async def get_background_jobs(
    admin_ctx: AdminContext = Depends(require_permission("jobs.view"))
):
    # Fetch operational jobs scheduled in APScheduler
    jobs = get_all_jobs()
    
    return {
        "status": "ok",
        "jobs": jobs
    }
