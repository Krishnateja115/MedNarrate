import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Surface per-field Pydantic validation errors to the client so callers get
    # actionable messages (e.g. "report_date: invalid date format") instead of
    # a generic "Validation error" that masks our specific HTTPException details.
    # NEVER include raw "input" values in the response as they might contain secrets.
    errors = exc.errors()
    safe_errors = []
    if errors:
        for error in errors:
            loc = " → ".join(str(val) for val in error.get("loc", []) if val != "body")
            msg = error.get("msg", "Validation error")
            safe_errors.append({
                "field": loc,
                "message": msg,
                "type": error.get("type", "value_error"),
            })
        
        # Build a readable string from the first error for single-error responses
        first = safe_errors[0]
        loc = first.get("field", "")
        msg = first.get("message", "Validation error")
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "Validation error"
    
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "code": "validation_error", "errors": safe_errors}
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
    
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id", "unknown")
    logger.error(f"Unhandled exception on {request.method} {request.url.path} (request_id={request_id}): {type(exc).__name__}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please contact support if this persists.", 
            "code": "internal_server_error",
            "request_id": request_id
        }
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

