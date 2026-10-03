from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.config import settings
from app.services.llm_orchestrator import (
    extract_structured_json,
    generate_primary_reasoning,
    translate_text_indic,
    verify_medical_facts,
)

pytestmark = pytest.mark.asyncio


@patch("app.services.llm_orchestrator.generate")
async def test_generate_primary_reasoning(mock_generate):
    mock_generate.return_value = "Test summary"
    result = await generate_primary_reasoning("test prompt")
    assert result == "Test summary"
    mock_generate.assert_called_once()


@patch("httpx.AsyncClient.post")
async def test_verify_medical_facts_valid(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "The text is [VALID]."}
    mock_post.return_value = mock_resp

    settings.MEDICAL_VERIFIER_PROVIDER = "ollama"
    result = await verify_medical_facts("some medical text")
    assert result["is_valid"] is True
    assert result["verification_status"] == "verified"
    assert result["correction"] is None


@patch("httpx.AsyncClient.post")
async def test_verify_medical_facts_invalid(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "[INVALID] Dosage is dangerously high."}
    mock_post.return_value = mock_resp

    settings.MEDICAL_VERIFIER_PROVIDER = "ollama"
    result = await verify_medical_facts("some bad medical text")
    assert result["is_valid"] is False
    assert result["verification_status"] == "invalid"
    assert "[INVALID]" in result["correction"]


@patch("httpx.AsyncClient.post")
async def test_extract_structured_json_ollama(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": '{"key": "value"}'}
    mock_post.return_value = mock_resp

    settings.STRUCTURED_MODEL_PROVIDER = "ollama"
    result = await extract_structured_json("extract this")
    assert result == '{"key": "value"}'


@patch("app.services.llm_orchestrator.generate_primary_reasoning")
async def test_extract_structured_json_fallback(mock_generate):
    mock_generate.return_value = '{"fallback": "yes"}'
    settings.STRUCTURED_MODEL_PROVIDER = (
        "gemini"  # not ollama, so it falls back to primary
    )

    result = await extract_structured_json("extract this")
    assert result == '{"fallback": "yes"}'
    mock_generate.assert_called_once()


@patch("httpx.AsyncClient.post")
async def test_translate_text_indic_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"translated_text": "अनुवादित"}
    mock_post.return_value = mock_resp

    settings.TRANSLATION_MODEL_URL = "http://fake-translation"
    result = await translate_text_indic("hello", "hi")
    assert result == "अनुवादित"


@patch("httpx.AsyncClient.post")
async def test_translate_text_indic_failure_raises_not_silent_english(mock_post):
    """A failed translation must raise; it must never return the English source as if translated."""
    from app.exceptions import TranslationServiceError

    mock_post.side_effect = httpx.ConnectError("Connection refused")

    settings.TRANSLATION_MODEL_URL = "http://fake-translation"
    with pytest.raises(TranslationServiceError):
        await translate_text_indic("hello", "hi")


async def test_translate_text_indic_unconfigured_raises():
    from app.exceptions import TranslationServiceError

    settings.TRANSLATION_MODEL_URL = None
    with pytest.raises(TranslationServiceError):
        await translate_text_indic("hello", "hi")


async def test_translate_text_indic_english_target_passthrough():
    assert await translate_text_indic("hello", "en") == "hello"


@patch("httpx.AsyncClient.post")
async def test_translate_text_indic_wrong_script_rejected(mock_post):
    """Service returning Latin text for a Hindi request is a failure, not a success."""
    from app.exceptions import TranslationServiceError

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"translated_text": "hello"}
    mock_post.return_value = mock_resp
    settings.TRANSLATION_MODEL_URL = "http://fake-translation"
    with pytest.raises(TranslationServiceError):
        await translate_text_indic("hello", "hi")


# --- Verifier fail-closed behaviour -----------------------------------------

def _assert_unverified(result, status):
    assert result["is_valid"] is None
    assert result["verification_status"] == status
    assert result["is_valid"] is not True


@patch("httpx.AsyncClient.post")
async def test_verifier_timeout_is_not_verified(mock_post):
    mock_post.side_effect = httpx.ReadTimeout("slow")
    settings.MEDICAL_VERIFIER_PROVIDER = "ollama"
    _assert_unverified(await verify_medical_facts("text"), "verifier_unavailable")


@patch("httpx.AsyncClient.post")
async def test_verifier_exception_is_not_verified(mock_post):
    mock_post.side_effect = RuntimeError("boom")
    settings.MEDICAL_VERIFIER_PROVIDER = "ollama"
    _assert_unverified(await verify_medical_facts("text"), "verifier_unavailable")


@patch("httpx.AsyncClient.post")
async def test_verifier_http_error_is_not_verified(mock_post):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock()
    )
    mock_post.return_value = mock_resp
    settings.MEDICAL_VERIFIER_PROVIDER = "ollama"
    _assert_unverified(await verify_medical_facts("text"), "verifier_unavailable")


@pytest.mark.parametrize("body", ["", "Looks fine to me", "valid", "VALIDATED"])
@patch("httpx.AsyncClient.post")
async def test_verifier_malformed_output_is_not_verified(mock_post, body):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": body}
    mock_post.return_value = mock_resp
    settings.MEDICAL_VERIFIER_PROVIDER = "ollama"
    _assert_unverified(await verify_medical_facts("text"), "malformed_response")


async def test_verifier_non_ollama_provider_is_unverified():
    settings.MEDICAL_VERIFIER_PROVIDER = "gemini"
    try:
        _assert_unverified(await verify_medical_facts("text"), "verifier_unavailable")
    finally:
        settings.MEDICAL_VERIFIER_PROVIDER = "ollama"


@patch("httpx.AsyncClient.post")
async def test_verifier_valid_and_invalid_both_present_is_invalid(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"response": "[VALID] ... actually [INVALID] dose wrong"}
    mock_post.return_value = mock_resp
    settings.MEDICAL_VERIFIER_PROVIDER = "ollama"
    result = await verify_medical_facts("text")
    assert result["is_valid"] is False
    assert result["verification_status"] == "invalid"
