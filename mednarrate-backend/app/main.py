from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.database import init_db
from app.exceptions import setup_exception_handlers
from app.api.v1 import router as api_v1_router
import os

import sys
limiter = Limiter(key_func=get_remote_address, enabled="pytest" not in sys.modules)

from app.services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title="MedNarrate API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
                forbidden = ["ignore previous instructions", "system prompt", "you are a helpful assistant"]
                if any(x in body_str for x in forbidden):
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

app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}
