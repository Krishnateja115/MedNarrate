from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .reports import router as reports_router
from .analysis import router as analysis_router
from .chat import router as chat_router
from .password_reset import router as password_reset_router
from .notifications import router as notifications_router
from .health import router as health_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(reports_router, prefix="/reports", tags=["reports"])
router.include_router(analysis_router, prefix="/reports", tags=["analysis"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
router.include_router(password_reset_router, prefix="/auth", tags=["password-reset"])
router.include_router(health_router, prefix="/health", tags=["health"])
