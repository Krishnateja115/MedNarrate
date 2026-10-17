"""Read-only view of how well MedNarrate's models perform, for the app."""

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.ml.model_report import build_report
from app.models.user import User

router = APIRouter()


@router.get("/model-performance")
async def model_performance(current_user: User = Depends(get_current_user)):
    """Every model, its measured scores (or "not evaluated"), and worked XAI examples."""
    report = build_report()
    # Server details are for administrators only.
    report.pop("environment", None)
    report.pop("how_to_refresh", None)
    return report
