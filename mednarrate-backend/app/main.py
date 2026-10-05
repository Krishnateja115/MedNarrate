import asyncio
import logging
import os
import re
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import CorrelationIdMiddleware
from app.core.rate_limit import limiter
from app.exceptions import setup_exception_handlers
from app.services.model_registry import get_ner_pipeline
from app.services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


async def _prewarm_ner_model() -> None:
    """Warm the optional NER model without delaying authentication readiness."""
    try:
        logger.info("Pre-warming NER ML model in the background...")
        await asyncio.wait_for(
            asyncio.to_thread(get_ner_pipeline),
            timeout=settings.NER_PREWARM_TIMEOUT_SECONDS,
        )
        logger.info("NER model pre-warmed successfully.")
    except TimeoutError:
        logger.warning(
            "NER pre-warm timed out after %s seconds; continuing with on-demand loading.",
            settings.NER_PREWARM_TIMEOUT_SECONDS,
        )
    except asyncio.CancelledError:
        raise
    except Exception as error:
        logger.warning("Failed to pre-warm NER model in the background: %s", error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    # Loading model weights may contact an unavailable network. Authentication,
    # the admin portal, and health checks do not depend on it, so API readiness
    # must not wait for this optional work.
    prewarm_task = asyncio.create_task(_prewarm_ner_model())
    try:
        yield
    finally:
        prewarm_task.cancel()
        with suppress(asyncio.CancelledError):
            await prewarm_task
        stop_scheduler()


# In production (ENVIRONMENT != 'development'), disable /docs, /redoc, and /openapi.json
# to prevent API schema enumeration. In development they remain accessible.
_is_development = (settings.ENVIRONMENT or "").lower() == "development"
app = FastAPI(
    title="MedNarrate API",
    lifespan=lifespan,
    docs_url="/docs" if _is_development else None,
    redoc_url="/redoc" if _is_development else None,
    openapi_url="/openapi.json" if _is_development else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
setup_exception_handlers(app)

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SlowAPIMiddleware)

cors_origins = set(settings.CORS_ORIGINS)
if "*" in cors_origins:
    cors_origins.remove("*")
    if settings.ADMIN_APP_ORIGIN:
        cors_origins.add(settings.ADMIN_APP_ORIGIN)
    if (settings.ENVIRONMENT or "").lower() == "development":
        cors_origins.update(
            {
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://127.0.0.1:3002",
            }
        )


# Always allow Tauri desktop app origins
cors_origins.add("tauri://localhost")
cors_origins.add("http://tauri.localhost")

# Fallback: if cors_origins is completely empty because of removing "*", add a placeholder or localhost
# to satisfy allow_origins requirements when allow_credentials=True
if not cors_origins:
    cors_origins.add("http://localhost:3000")

# Only allow localhost/127.x regex in development. In production CORS is restricted
# to explicitly configured origins only.
_allow_origin_regex = (
    r"http://(localhost|127\.0\.0\.1)(:\d+)?"
    if _is_development
    else None
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(cors_origins),
    allow_origin_regex=_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.middleware("http")
async def resolve_client_ip(request: Request, call_next):
    """Resolve the real client IP.

    Only trust X-Forwarded-For when TRUSTED_PROXY=true is explicitly set in the
    deployment environment (e.g., behind an nginx or load-balancer that strips
    and re-adds the header).  Without that flag, we use request.client.host to
    prevent IP-spoofing via a crafted X-Forwarded-For header.

    DEPLOYMENT NOTE: Set TRUSTED_PROXY=true only when the server is running
    behind a trusted reverse-proxy that guarantees the X-Forwarded-For chain.
    """
    trusted_proxy = (os.environ.get("TRUSTED_PROXY", "").lower() == "true")
    if trusted_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            request.state.client_ip = forwarded.split(",")[0].strip()
        else:
            request.state.client_ip = request.client.host if request.client else None
    else:
        request.state.client_ip = request.client.host if request.client else None
    return await call_next(request)


@app.middleware("http")
async def prompt_injection_middleware(request: Request, call_next):
    # Basic check on POST/PUT requests. Auth endpoints carry credentials/tokens (random
    # base64 text), never LLM prompts, so they are excluded to avoid false positives.
    if request.method in ["POST", "PUT"] and not request.url.path.startswith(
        f"{settings.API_V1_STR}/auth/"
    ):
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            from fastapi.responses import JSONResponse

            limit = settings.MAX_JSON_BODY_BYTES
            declared = request.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > limit:
                return JSONResponse(
                    status_code=413, content={"detail": "Request body too large."}
                )

            # Bounded read: abort as soon as the cap is exceeded, even for
            # chunked bodies that declare no Content-Length. This runs before
            # authentication, so it must never buffer an unbounded payload.
            chunks: list[bytes] = []
            received = 0
            async for chunk in request.stream():
                received += len(chunk)
                if received > limit:
                    return JSONResponse(
                        status_code=413, content={"detail": "Request body too large."}
                    )
                chunks.append(chunk)
            body = b"".join(chunks)

            try:
                body_str = body.decode("utf-8").lower()

                # Robust Prompt Injection / Jailbreak Detection Regex
                injection_pattern = re.compile(
                    r"\b(ignore previous instructions|ignore all previous|system prompt|you are a helpful assistant|forget previous|override instructions|bypass|jailbreak|dan|do anything now)\b",
                    re.IGNORECASE,
                )

                if injection_pattern.search(body_str):
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Potential prompt injection detected."},
                    )
            except Exception:
                pass

            # Make the body available again for downstream consumers. Starlette's
            # BaseHTTPMiddleware replays a cached request body only when `_body` is
            # set (stream() does not set it), so set it explicitly.
            request._body = body
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = receive
    response = await call_next(request)
    return response


os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# StaticFiles for /uploads was removed for security reasons.
# Files are now served via the authenticated /api/v1/reports/{id}/download endpoint.
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
async def health():
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            schema_revision = (
                await session.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one_or_none()
        db_status = "up"
    except Exception as exc:
        logger.warning("Health database check failed: %s", type(exc).__name__)
        db_status = "down"
        schema_revision = None

    status = "ok" if db_status == "up" else "degraded"

    return {
        "service": "mednarrate",
        "status": status,
        "db": db_status,
        "database_backend": settings.DATABASE_URL.split(":", 1)[0],
        "schema_revision": schema_revision,
        "schema_expected": settings.EXPECTED_SCHEMA_REVISION,
        "version": os.environ.get("MEDNARRATE_VERSION", "1.0.0"),
        "commit": os.environ.get("MEDNARRATE_COMMIT", "unknown"),
    }
