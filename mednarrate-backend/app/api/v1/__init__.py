from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .reports import router as reports_router
from .analysis import router as analysis_router
from .chat import router as chat_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(reports_router, prefix="/reports", tags=["reports"])
router.include_router(analysis_router, prefix="/reports", tags=["analysis"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
