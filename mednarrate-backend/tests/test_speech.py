"""Voice input: backend speech-to-text (Groq Whisper) behind a feature flag."""

import httpx
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.services import provider_health as ph
from app.services import speech_service
from app.services.provider_health import provider_health
from app.services.speech_service import SpeechError

M4A = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00" + b"\x01" * 64
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32


@pytest.fixture
def voice_on(monkeypatch):
    monkeypatch.setattr(settings, "VOICE_INPUT_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test_key_123456", raising=False)


def _client_for(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _ok(text="my head hurts", **extra):
    body = {"text": text, "duration": 3.2, "segments": [{"no_speech_prob": 0.01, "avg_logprob": -0.2}]}
    body.update(extra)
    return httpx.Response(200, json=body)


# ---------- format detection ----------

@pytest.mark.parametrize(
    "data,ext",
    [
        (M4A, "m4a"),
        (WAV, "wav"),
        (b"OggS" + b"\x00" * 20, "ogg"),
        (b"\x1aE\xdf\xa3" + b"\x00" * 20, "webm"),
        (b"fLaC" + b"\x00" * 20, "flac"),
        (b"ID3\x03" + b"\x00" * 20, "mp3"),
        (b"\xff\xfb\x90\x00" + b"\x00" * 20, "mp3"),
    ],
)
def test_sniff_audio_detects_container(data, ext):
    assert speech_service.sniff_audio(data)[0] == ext


def test_sniff_audio_rejects_other_files():
    with pytest.raises(SpeechError) as exc:
        speech_service.sniff_audio(b"%PDF-1.7 not audio at all")
    assert exc.value.status_code == 415


@pytest.mark.parametrize("raw,expected", [("hi", "hi"), ("ta-IN", "ta"), ("MR", "mr"), ("fr", None), ("", None), (None, None)])
def test_normalise_language(raw, expected):
    assert speech_service.normalise_language(raw) == expected


# ---------- service ----------

@pytest.mark.asyncio
async def test_disabled_by_default():
    with pytest.raises(SpeechError) as exc:
        await speech_service.transcribe(M4A, "en")
    assert exc.value.status_code == 404 and exc.value.reason == "disabled"


@pytest.mark.asyncio
async def test_enabled_needs_key(monkeypatch):
    monkeypatch.setattr(settings, "VOICE_INPUT_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "GROQ_API_KEY", None, raising=False)
    assert speech_service.is_enabled() is False


@pytest.mark.asyncio
async def test_transcribe_sends_language_model_and_file(voice_on):
    seen = {}

    def handler(request: httpx.Request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = request.content
        return _ok("मुझे सिरदर्द है")

    async with _client_for(handler) as c:
        result = await speech_service.transcribe(M4A, "hi-IN", client=c)
    assert result.text == "मुझे सिरदर्द है"
    assert result.model == "whisper-large-v3"
    assert seen["auth"] == "Bearer gsk_test_key_123456"
    body = seen["body"]
    assert b'name="language"' in body and b"\r\n\r\nhi\r\n" in body
    assert b'name="model"' in body and b"whisper-large-v3" in body
    assert b"voice.m4a" in body and b"audio/mp4" in body


@pytest.mark.asyncio
async def test_no_language_lets_whisper_detect(voice_on):
    seen = {}

    def handler(request):
        seen["body"] = request.content
        return _ok()

    async with _client_for(handler) as c:
        await speech_service.transcribe(WAV, None, client=c)
    assert b'name="language"' not in seen["body"]


@pytest.mark.asyncio
async def test_falls_back_to_second_model_on_rate_limit(voice_on):
    calls = []

    def handler(request):
        model = b"whisper-large-v3-turbo" in request.content
        calls.append("turbo" if model else "large")
        if not model:
            return httpx.Response(429, json={"error": {"message": "Rate limit reached"}})
        return _ok("hello doctor")

    async with _client_for(handler) as c:
        result = await speech_service.transcribe(M4A, "en", client=c)
    assert calls == ["large", "turbo"]
    assert result.text == "hello doctor" and result.model == "whisper-large-v3-turbo"
    # The limited model rests; the next clip goes straight to turbo.
    assert not provider_health.is_available("speech:whisper-large-v3")

    async with _client_for(handler) as c:
        await speech_service.transcribe(M4A, "en", client=c)
    assert calls == ["large", "turbo", "turbo"]


@pytest.mark.asyncio
async def test_all_models_limited_gives_friendly_error(voice_on):
    def handler(request):
        return httpx.Response(429, json={"error": {"message": "Rate limit reached"}})

    async with _client_for(handler) as c:
        with pytest.raises(SpeechError) as exc:
            await speech_service.transcribe(M4A, "en", client=c)
    assert exc.value.status_code == 503 and exc.value.reason == ph.QUOTA
    assert "gsk_" not in exc.value.message


@pytest.mark.asyncio
async def test_bad_key_stops_after_first_model(voice_on):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(401, json={"error": {"message": "Invalid API Key"}})

    async with _client_for(handler) as c:
        with pytest.raises(SpeechError) as exc:
            await speech_service.transcribe(M4A, "en", client=c)
    assert len(calls) == 1
    assert exc.value.reason == ph.AUTH


@pytest.mark.asyncio
async def test_unreadable_clip_does_not_bench_the_model(voice_on):
    def handler(request):
        return httpx.Response(400, json={"error": {"message": "could not process file"}})

    async with _client_for(handler) as c:
        with pytest.raises(SpeechError) as exc:
            await speech_service.transcribe(M4A, "en", client=c)
    assert exc.value.status_code == 422
    assert provider_health.is_available("speech:whisper-large-v3")


@pytest.mark.asyncio
async def test_network_failure_is_reported_as_unreachable(voice_on):
    def handler(request):
        raise httpx.ConnectError("no route to host")

    async with _client_for(handler) as c:
        with pytest.raises(SpeechError) as exc:
            await speech_service.transcribe(M4A, "en", client=c)
    assert exc.value.reason == ph.NETWORK


@pytest.mark.asyncio
async def test_silence_returns_no_speech(voice_on):
    def handler(request):
        return httpx.Response(200, json={"text": "", "duration": 2.0, "segments": []})

    async with _client_for(handler) as c:
        result = await speech_service.transcribe(M4A, "en", client=c)
    assert result.no_speech is True and result.text == ""


@pytest.mark.asyncio
async def test_whisper_hallucination_on_noise_is_dropped(voice_on):
    def handler(request):
        return httpx.Response(
            200,
            json={"text": "Thank you.", "duration": 3.0,
                  "segments": [{"no_speech_prob": 0.8, "avg_logprob": -1.4}]},
        )

    async with _client_for(handler) as c:
        result = await speech_service.transcribe(M4A, "en", client=c)
    assert result.no_speech is True


@pytest.mark.asyncio
async def test_real_thank_you_with_confident_speech_is_kept(voice_on):
    def handler(request):
        return httpx.Response(
            200,
            json={"text": "Thank you.", "duration": 1.0,
                  "segments": [{"no_speech_prob": 0.02, "avg_logprob": -0.1}]},
        )

    async with _client_for(handler) as c:
        result = await speech_service.transcribe(M4A, "en", client=c)
    assert result.text == "Thank you." and not result.no_speech


# ---------- HTTP API ----------

@pytest.mark.asyncio
async def test_status_reports_disabled(client: AsyncClient, token_headers):
    resp = await client.get("/api/v1/speech/status", headers=token_headers)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
    assert resp.json()["languages"] == []


@pytest.mark.asyncio
async def test_status_reports_enabled(client: AsyncClient, token_headers, voice_on):
    body = (await client.get("/api/v1/speech/status", headers=token_headers)).json()
    assert body["enabled"] is True
    assert set(body["languages"]) == {"en", "hi", "ta", "te", "kn", "ml", "bn", "mr"}
    assert body["max_seconds"] == 120


@pytest.mark.asyncio
async def test_endpoints_require_login(client: AsyncClient, voice_on):
    assert (await client.get("/api/v1/speech/status")).status_code == 401
    resp = await client.post("/api/v1/speech/transcribe", files={"file": ("a.m4a", M4A, "audio/mp4")})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_transcribe_404_when_disabled(client: AsyncClient, token_headers):
    resp = await client.post(
        "/api/v1/speech/transcribe", headers=token_headers,
        files={"file": ("a.m4a", M4A, "audio/mp4")},
    )
    assert resp.status_code == 404
    assert resp.json()["reason"] == "disabled"


@pytest.mark.asyncio
async def test_transcribe_returns_text(client: AsyncClient, token_headers, voice_on, monkeypatch):
    async def fake(http, model, data, ext, ctype, language):
        assert ext == "m4a" and language == "ta"
        return {"text": "எனக்கு தலைவலி", "duration": 2.5,
                "segments": [{"no_speech_prob": 0.01, "avg_logprob": -0.3}]}

    monkeypatch.setattr(speech_service, "_call_groq", fake)
    resp = await client.post(
        "/api/v1/speech/transcribe", headers=token_headers,
        files={"file": ("whatever.bin", M4A, "application/octet-stream")},
        data={"language": "ta"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"text": "எனக்கு தலைவலி", "no_speech": False, "language": "ta", "duration_seconds": 2.5}


@pytest.mark.asyncio
async def test_transcribe_rejects_non_audio(client: AsyncClient, token_headers, voice_on):
    resp = await client.post(
        "/api/v1/speech/transcribe", headers=token_headers,
        files={"file": ("a.m4a", b"%PDF-1.7 hello", "audio/mp4")},
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_transcribe_rejects_oversized(client: AsyncClient, token_headers, voice_on, monkeypatch):
    monkeypatch.setattr(settings, "SPEECH_MAX_BYTES", 1000, raising=False)
    resp = await client.post(
        "/api/v1/speech/transcribe", headers=token_headers,
        files={"file": ("a.m4a", M4A + b"\x00" * 5000, "audio/mp4")},
    )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_transcribe_rejects_empty(client: AsyncClient, token_headers, voice_on):
    resp = await client.post(
        "/api/v1/speech/transcribe", headers=token_headers,
        files={"file": ("a.m4a", b"", "audio/mp4")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_provider_outage_is_503_with_code(client: AsyncClient, token_headers, voice_on, monkeypatch):
    async def fake(*a, **k):
        raise speech_service._ProviderFailure("x", 429, "Rate limit")

    monkeypatch.setattr(speech_service, "_call_groq", fake)
    resp = await client.post(
        "/api/v1/speech/transcribe", headers=token_headers,
        files={"file": ("a.m4a", M4A, "audio/mp4")},
    )
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "speech_unavailable" and body["reason"] == ph.QUOTA
    assert "Rate limit" not in body["detail"]


@pytest.mark.asyncio
async def test_transcript_is_not_logged(client: AsyncClient, token_headers, voice_on, monkeypatch, caplog):
    async def fake(*a, **k):
        return {"text": "secret symptom words", "duration": 2.0,
                "segments": [{"no_speech_prob": 0.0, "avg_logprob": -0.1}]}

    monkeypatch.setattr(speech_service, "_call_groq", fake)
    with caplog.at_level("DEBUG"):
        await client.post(
            "/api/v1/speech/transcribe", headers=token_headers,
            files={"file": ("a.m4a", M4A, "audio/mp4")},
        )
    assert "secret symptom words" not in caplog.text
