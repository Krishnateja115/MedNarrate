"""Speech-to-text for the chat box ("press the mic, speak, get text").

The phone records a short clip and uploads it; this module sends it to Whisper
on Groq and returns the transcript. The Groq key stays on the server. Nothing is
stored: the audio lives in memory for the length of one request and neither the
audio nor the transcript is ever logged.

Everything here is optional. With ``VOICE_INPUT_ENABLED=false`` (the default) the
endpoints report "disabled" and the app does not show a microphone.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.services import provider_health as ph
from app.services.provider_health import describe_error, http_error_detail, provider_health

logger = logging.getLogger(__name__)

GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Languages the app supports for translation; Whisper uses the same ISO codes.
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
}

# Short phrases Whisper tends to invent when it hears silence or noise.
_SILENCE_HALLUCINATIONS = {
    "thank you",
    "thanks",
    "thank you for watching",
    "thanks for watching",
    "you",
    "bye",
    "okay",
    "subtitles by the amaraorg community",
}

_USER_MESSAGES = {
    ph.QUOTA: "Voice input is busy right now. Please try again in a minute, or type your message.",
    ph.AUTH: "Voice input is not set up correctly on the server.",
    ph.MODEL: "Voice input is not set up correctly on the server.",
    ph.NOT_CONFIGURED: "Voice input is not set up on the server yet.",
    ph.TRANSIENT: "Voice input took too long. Please try again.",
    ph.NETWORK: "The server could not reach the voice service. Please try again.",
    ph.UNKNOWN: "Voice input is temporarily unavailable. You can still type your message.",
}


class SpeechError(Exception):
    """A failure with a message that is safe to show the user."""

    def __init__(self, message: str, *, status_code: int, reason: str) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.reason = reason


@dataclass
class Transcript:
    text: str
    language: str | None
    duration_seconds: float | None
    model: str
    no_speech: bool = False


def is_enabled() -> bool:
    return bool(
        getattr(settings, "VOICE_INPUT_ENABLED", False)
        and str(getattr(settings, "GROQ_API_KEY", "") or "").strip()
    )


def models() -> list[str]:
    configured = str(getattr(settings, "SPEECH_MODELS", "") or "")
    return [m.strip() for m in configured.split(",") if m.strip()] or [
        "whisper-large-v3",
        "whisper-large-v3-turbo",
    ]


def normalise_language(language: str | None) -> str | None:
    """Two-letter code the app supports, or None (let Whisper detect it)."""
    code = (language or "").strip().lower().replace("_", "-").split("-")[0]
    return code if code in SUPPORTED_LANGUAGES else None


def sniff_audio(data: bytes) -> tuple[str, str]:
    """(file extension, content type) from the first bytes, or raise SpeechError."""
    head = data[:16]
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return "m4a", "audio/mp4"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav", "audio/wav"
    if head[:4] == b"OggS":
        return "ogg", "audio/ogg"
    if head[:4] == b"\x1aE\xdf\xa3":
        return "webm", "audio/webm"
    if head[:4] == b"fLaC":
        return "flac", "audio/flac"
    if head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
        return "mp3", "audio/mpeg"
    raise SpeechError(
        "That audio format is not supported.", status_code=415, reason="unsupported_audio"
    )


def _looks_like_silence(text: str, segments: list[dict[str, Any]]) -> bool:
    cleaned = re.sub(r"[^\w\s]", "", text).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return True
    if segments:
        no_speech = [s.get("no_speech_prob") for s in segments if isinstance(s.get("no_speech_prob"), (int, float))]
        logprobs = [s.get("avg_logprob") for s in segments if isinstance(s.get("avg_logprob"), (int, float))]
        if no_speech and min(no_speech) > 0.6 and (not logprobs or max(logprobs) < -0.8):
            return True
    return cleaned in _SILENCE_HALLUCINATIONS and len(cleaned) < 30 and bool(segments) and all(
        isinstance(s.get("no_speech_prob"), (int, float)) and s["no_speech_prob"] > 0.3 for s in segments
    )


class _ProviderFailure(Exception):
    def __init__(self, message: str, status_code: int | None = None, detail: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_detail = detail


async def _call_groq(
    client: httpx.AsyncClient,
    model: str,
    data: bytes,
    extension: str,
    content_type: str,
    language: str | None,
) -> dict[str, Any]:
    form = {"model": model, "response_format": "verbose_json", "temperature": "0"}
    if language:
        form["language"] = language
    try:
        resp = await client.post(
            GROQ_TRANSCRIPTION_URL,
            headers={"Authorization": f"Bearer {str(settings.GROQ_API_KEY).strip()}"},
            data=form,
            files={"file": (f"voice.{extension}", data, content_type)},
        )
    except httpx.HTTPError as exc:
        raise _ProviderFailure("Groq request failed") from exc
    if resp.status_code >= 400:
        raise _ProviderFailure(
            f"Groq HTTP {resp.status_code}", resp.status_code, http_error_detail(resp)
        )
    try:
        payload = resp.json()
    except ValueError as exc:
        raise _ProviderFailure("Groq returned a non-JSON answer") from exc
    if not isinstance(payload, dict):
        raise _ProviderFailure("Groq returned an unexpected answer")
    return payload


async def transcribe(
    data: bytes,
    language: str | None = None,
    *,
    client: httpx.AsyncClient | None = None,
) -> Transcript:
    """Transcribe one short clip. Raises :class:`SpeechError` on failure."""
    if not is_enabled():
        raise SpeechError("Voice input is not enabled.", status_code=404, reason="disabled")
    if not data:
        raise SpeechError("The recording is empty.", status_code=400, reason="empty_audio")
    extension, content_type = sniff_audio(data)
    code = normalise_language(language)

    timeout = float(getattr(settings, "SPEECH_TIMEOUT_SECONDS", 30.0))
    owns_client = client is None
    http = client or httpx.AsyncClient(timeout=timeout)
    kinds: list[str] = []
    try:
        for model in models():
            health_name = f"speech:{model}"
            if not provider_health.is_available(health_name):
                kinds.append(provider_health.last_kind(health_name) or ph.UNKNOWN)
                continue
            try:
                payload = await _call_groq(http, model, data, extension, content_type, code)
            except _ProviderFailure as exc:
                if exc.status_code in (400, 413, 415, 422):
                    # The clip itself was refused (corrupt, too long, wrong format).
                    # That says nothing about the model, so it is not put on cool-down.
                    logger.warning("Speech clip rejected: %s", describe_error(exc, 160))
                    raise SpeechError(
                        "That recording could not be read. Please try again.",
                        status_code=422,
                        reason="unreadable_audio",
                    ) from exc
                kind = provider_health.record_failure(health_name, exc)
                kinds.append(kind)
                logger.warning(
                    "Speech model %s failed: kind=%s %s", model, kind, describe_error(exc, 160)
                )
                if kind in (ph.AUTH, ph.NOT_CONFIGURED):
                    break  # the same key is used for every model
                continue
            provider_health.record_success(health_name)
            text = str(payload.get("text") or "").strip()
            segments = [s for s in (payload.get("segments") or []) if isinstance(s, dict)]
            duration = payload.get("duration")
            if _looks_like_silence(text, segments):
                return Transcript("", code, _as_float(duration), model, no_speech=True)
            return Transcript(text, code, _as_float(duration), model)
    finally:
        if owns_client:
            await http.aclose()

    reason = _pick_reason(kinds)
    message = _USER_MESSAGES.get(reason, _USER_MESSAGES[ph.UNKNOWN])
    raise SpeechError(message, status_code=503, reason=reason)


def _as_float(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


_REASON_ORDER = [ph.AUTH, ph.QUOTA, ph.MODEL, ph.NETWORK, ph.TRANSIENT, ph.NOT_CONFIGURED, ph.UNKNOWN]


def _pick_reason(kinds: list[str]) -> str:
    for reason in _REASON_ORDER:
        if reason in kinds:
            return reason
    return ph.UNKNOWN
