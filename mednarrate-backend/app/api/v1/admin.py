from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user

@router.get("/health")
async def admin_health(admin_user: User = Depends(require_admin)):
    return {"status": "ok", "message": "Admin services are running"}

@router.get("/kb-stats")
async def get_kb_stats(admin_user: User = Depends(require_admin)):
    # Mock KB stats for now
    return {
        "status": "ok",
        "total_documents": 5,
        "total_chunks": 42
    }
