import asyncio
import logging
import os
import re
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import CorrelationIdMiddleware
from app.exceptions import setup_exception_handlers
from app.services.model_registry import get_ner_pipeline
from app.services.scheduler import start_scheduler, stop_scheduler

limiter = Limiter(key_func=get_remote_address, enabled="pytest" not in sys.modules)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    try:
        logger.info("Pre-warming NER ML model...")
        await asyncio.to_thread(get_ner_pipeline)
        logger.info("NER model pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Failed to pre-warm NER model at startup: {e}")
    yield
    stop_scheduler()

app = FastAPI(title="MedNarrate API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
setup_exception_handlers(app)

app.add_middleware(CorrelationIdMiddleware)

is_wildcard = "*" in settings.CORS_ORIGINS
cors_origins = set(settings.CORS_ORIGINS)
if is_wildcard:
    cors_origins.remove("*")
    if settings.ADMIN_APP_ORIGIN:
        cors_origins.add(settings.ADMIN_APP_ORIGIN)

# Always allow Tauri desktop app origins
cors_origins.add("tauri://localhost")
cors_origins.add("http://tauri.localhost")

# Fallback: if cors_origins is completely empty because of removing "*", add a placeholder or localhost 
# to satisfy allow_origins requirements when allow_credentials=True
if not cors_origins:
    cors_origins.add("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.middleware("http")
async def prompt_injection_middleware(request: Request, call_next):
    # Basic check on POST/PUT requests
    if request.method in ["POST", "PUT"]:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.body()
                body_str = body.decode('utf-8').lower()
                
                # Robust Prompt Injection / Jailbreak Detection Regex
                injection_pattern = re.compile(
                    r"(ignore previous instructions|ignore all previous|system prompt|you are a helpful assistant|forget previous|override instructions|bypass|jailbreak|dan|do anything now)", 
                    re.IGNORECASE
                )
                
                if injection_pattern.search(body_str):
                    from fastapi.responses import JSONResponse
                    return JSONResponse(status_code=400, content={"detail": "Potential prompt injection detected."})
            except Exception:
                pass
            # need to make the body available again for downstream consumers
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
    response = await call_next(request)
    return response

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# StaticFiles for /uploads was removed for security reasons.
# Files are now served via the authenticated /api/v1/reports/{id}/download endpoint.
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {
        "service": "mednarrate",
        "status": "ok",
        "version": os.environ.get("MEDNARRATE_VERSION", "1.0.0"),
        "commit": os.environ.get("MEDNARRATE_COMMIT", "unknown")
    }
