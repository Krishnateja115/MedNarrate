"""Classify expected document rejection separately from processing faults."""

from sqlalchemy import select

from app.models.report import ProcessingStatus
from app.models.report_analysis import ReportAnalysis


REJECTED_REPORT_CATEGORIES = ("NOT_MEDICAL_REPORT",)


def rejected_report_ids():
    """Return report IDs rejected by the medical-document gate."""
    return select(ReportAnalysis.report_id).where(
        ReportAnalysis.failure_category.in_(REJECTED_REPORT_CATEGORIES)
    )


def public_report_status(status: ProcessingStatus, failure_category: str | None) -> str:
    """Expose a rejected document as a distinct outcome without a schema change."""
    if status == ProcessingStatus.failed and failure_category in REJECTED_REPORT_CATEGORIES:
        return "rejected"
    return status.value
