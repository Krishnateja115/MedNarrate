"""Voice input: turn a short recording into text for the chat box.

Optional feature, off unless ``VOICE_INPUT_ENABLED=true`` and a ``GROQ_API_KEY``
is set. The app asks ``GET /speech/status`` first and only shows the microphone
when it answers ``enabled: true``. Audio is processed in memory and discarded;
neither it nor the transcript is stored or logged.
"""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.maintenance import check_maintenance
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.models.user import User
from app.services import speech_service
from app.services.speech_service import SUPPORTED_LANGUAGES, SpeechError

router = APIRouter()

_CHUNK = 256 * 1024


def _error(exc: SpeechError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": "speech_unavailable", "reason": exc.reason},
    )


@router.get("/status")
async def speech_status(current_user: User = Depends(get_current_user)):
    enabled = speech_service.is_enabled()
    return {
        "enabled": enabled,
        "languages": list(SUPPORTED_LANGUAGES) if enabled else [],
        "max_seconds": int(settings.SPEECH_MAX_SECONDS),
        "max_bytes": int(settings.SPEECH_MAX_BYTES),
    }


@router.post("/transcribe")
@limiter.limit(settings.SPEECH_RATE_LIMIT)
async def transcribe_speech(
    request: Request,
    file: UploadFile = File(...),
    language: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    maintenance=Depends(check_maintenance("chat")),
):
    if not speech_service.is_enabled():
        return _error(SpeechError("Voice input is not enabled.", status_code=404, reason="disabled"))

    limit = int(settings.SPEECH_MAX_BYTES)
    data = bytearray()
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > limit:
            return _error(
                SpeechError(
                    "That recording is too long. Please keep it shorter.",
                    status_code=413,
                    reason="too_large",
                )
            )

    try:
        result = await speech_service.transcribe(bytes(data), language)
    except SpeechError as exc:
        return _error(exc)
    finally:
        del data

    return {
        "text": result.text,
        "no_speech": result.no_speech,
        "language": result.language,
        "duration_seconds": result.duration_seconds,
    }
