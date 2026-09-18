from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Surface per-field Pydantic validation errors to the client so callers get
    # actionable messages (e.g. "report_date: invalid date format") instead of
    # a generic "Validation error" that masks our specific HTTPException details.
    errors = exc.errors()
    if errors:
        # Build a readable string from the first error for single-error responses
        first = errors[0]
        loc = " → ".join(str(l) for l in first.get("loc", []) if l != "body")
        msg = first.get("msg", "Validation error")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "Validation error"
    from fastapi.encoders import jsonable_encoder
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "code": "validation_error", "errors": jsonable_encoder(errors)}
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    # Don't catch HTTPExceptions — FastAPI handles those itself with the correct
    # status code and detail. Only catch genuinely unexpected errors here.
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None) or {},
        )
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_server_error"}
    )

async def integrity_exception_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Database integrity error, possibly a duplicate entry", "code": "integrity_error"}
    )

def setup_exception_handlers(app):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)

