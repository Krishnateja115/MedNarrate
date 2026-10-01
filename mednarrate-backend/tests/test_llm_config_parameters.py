from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from app.services.llm_client import DevGeminiProvider, OllamaProvider, VertexAIProvider
from app.core.config import settings

@pytest.mark.asyncio
async def test_dev_gemini_config_parameters(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "valid_dev_key_999")

    provider = DevGeminiProvider()
    config = {"temperature": 0.5, "max_tokens": 1234}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "Mocked Response"}]}}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        await provider.generate("Test prompt", config=config)

        # Verify that the correct parameters were passed to the API
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        json_payload = call_kwargs.get("json")
        gen_config = json_payload.get("generationConfig", {})

        assert gen_config.get("temperature") == 0.5
        assert gen_config.get("maxOutputTokens") == 1234

@pytest.mark.asyncio
async def test_ollama_config_parameters(monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_URL", "http://localhost:11434")
    provider = OllamaProvider()
    config = {"temperature": 0.7, "max_tokens": 4096}

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"response": "Mocked"})
        mock_post.return_value = mock_response

        await provider.generate("Test prompt", config=config)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        json_payload = call_kwargs.get("json")
        options = json_payload.get("options", {})

        assert options.get("temperature") == 0.7
        assert options.get("num_predict") == 4096
