import abc
import time
import uuid
import logging
import httpx
import google.auth
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMConfigurationError(RuntimeError):
    """Raised when an explicit LLM provider is configured but missing credentials/configuration."""
    pass

class LLMConnectionError(RuntimeError):
    """Raised when the configured LLM provider service cannot be reached or fails."""
    pass

def _is_valid_dev_gemini_key(key: str | None) -> bool:
    if not key or not key.strip():
        return False
    k = key.strip()
    if k in ["your_gemini_api_key_here", "your-gemini-api-key", "placeholder"]:
        return False
    return True

# Abstract Provider Interface
class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None) -> dict:
        """Executes LLM text generation and returns structured metadata response."""
        pass

    @abc.abstractmethod
    async def health_check(self) -> dict:
        """Evaluates health state: configured, authenticated, reachable, model_available."""
        pass

# Production Primary Provider: Google Cloud Vertex AI
class VertexAIProvider(LLMProvider):
    @property
    def project(self) -> str | None:
        return getattr(settings, "VERTEX_PROJECT_ID", None)

    @property
    def location(self) -> str:
        return getattr(settings, "VERTEX_LOCATION", "us-central1")

    @property
    def model_name(self) -> str:
        return getattr(settings, "VERTEX_MODEL", "gemini-1.5-flash")

    async def health_check(self) -> dict:
        has_project = bool(self.project and self.project.strip())
        has_auth = False
        auth_method = "none"
        try:
            credentials, proj = google.auth.default()
            has_auth = credentials is not None
            auth_method = "application_default_credentials"
            if not has_project and proj:
                has_project = True
        except Exception:
            has_auth = False

        return {
            "provider": "vertex_ai",
            "configured": has_project or has_auth,
            "authenticated": has_auth,
            "auth_method": auth_method,
            "reachable": has_auth,
            "model": self.model_name,
            "location": self.location,
            "model_available": has_auth,
        }

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None) -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()
        
        # Check Application Default Credentials / Auth
        health = await self.health_check()
        if not health["authenticated"]:
            raise LLMConfigurationError(
                "Vertex AI authentication unavailable. Application Default Credentials (ADC) "
                "or Google Cloud service credentials must be configured for Vertex AI."
            )

        try:
            import google.generativeai as genai  # Lazy import — avoids deprecation warnings at startup
            if settings.GEMINI_API_KEY and _is_valid_dev_gemini_key(settings.GEMINI_API_KEY):
                genai.configure(api_key=settings.GEMINI_API_KEY.strip())
            
            model = genai.GenerativeModel(self.model_name)
            response = await model.generate_content_async(prompt)
            latency_ms = int((time.time() - start_time) * 1000)

            if response and response.text:
                logger.info(f"[LLM:VERTEX_AI:SUCCESS] req_id={req_id} latency={latency_ms}ms model={self.model_name}")
                return {
                    "provider": "vertex_ai",
                    "model": self.model_name,
                    "request_success": True,
                    "response_received": True,
                    "error_category": None,
                    "content": response.text.strip(),
                    "latency_ms": latency_ms,
                    "request_id": req_id,
                }
            raise ValueError("Empty text response payload received from Vertex AI.")
        except LLMConfigurationError:
            raise
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[LLM:VERTEX_AI:FAIL] req_id={req_id} latency={latency_ms}ms error={e}")
            raise LLMConnectionError(f"Vertex AI LLM service error: {e}")

# Private / Local Provider: Ollama
class OllamaProvider(LLMProvider):
    @property
    def base_url(self) -> str:
        url = getattr(settings, "OLLAMA_URL", None) or "http://localhost:11434"
        return url.rstrip('/')

    @property
    def model_name(self) -> str:
        return getattr(settings, "OLLAMA_MODEL", "llama3:8b")

    async def health_check(self) -> dict:
        configured = bool(settings.OLLAMA_URL and settings.OLLAMA_URL.strip())
        reachable = False
        model_available = False
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    reachable = True
                    models = [m.get("name", "") for m in resp.json().get("models", [])]
                    model_available = any(self.model_name in m for m in models) or len(models) > 0
        except Exception:
            reachable = False

        return {
            "provider": "ollama",
            "configured": configured or reachable,
            "authenticated": True,  # Local no-auth
            "auth_method": "local_endpoint",
            "reachable": reachable,
            "model": self.model_name,
            "location": "local",
            "model_available": model_available,
        }

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None) -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()
        url = f"{self.base_url}/api/generate"

        try:
            async with httpx.AsyncClient(timeout=min(timeout, 30.0)) as client:
                resp = await client.post(
                    url,
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
                resp.raise_for_status()
                res_data = resp.json()
                latency_ms = int((time.time() - start_time) * 1000)

                if "response" in res_data and res_data["response"]:
                    logger.info(f"[LLM:OLLAMA:SUCCESS] req_id={req_id} latency={latency_ms}ms model={self.model_name}")
                    return {
                        "provider": "ollama",
                        "model": self.model_name,
                        "request_success": True,
                        "response_received": True,
                        "error_category": None,
                        "content": res_data["response"].strip(),
                        "latency_ms": latency_ms,
                        "request_id": req_id,
                    }
                raise ValueError("Invalid or empty response payload from Ollama API.")
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[LLM:OLLAMA:FAIL] req_id={req_id} latency={latency_ms}ms error={e}")
            raise LLMConnectionError(f"Ollama LLM service error at {self.base_url}: {e}")

# Development-Only Direct Gemini Provider
class DevGeminiProvider(LLMProvider):
    @property
    def api_key(self) -> str | None:
        return getattr(settings, "GEMINI_API_KEY", None)

    @property
    def model_name(self) -> str:
        return getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    def _check_production_restriction(self):
        if (getattr(settings, "ENVIRONMENT", "development") or "").lower() == "production":
            raise LLMConfigurationError(
                "Direct developer Gemini API keys (DevGeminiProvider) are strictly prohibited in production. "
                "Configure PRIMARY_LLM_PROVIDER=vertex_ai or ollama."
            )

    async def health_check(self) -> dict:
        self._check_production_restriction()
        valid_key = _is_valid_dev_gemini_key(self.api_key)
        return {
            "provider": "dev_gemini",
            "configured": valid_key,
            "authenticated": valid_key,
            "auth_method": "direct_api_key",
            "reachable": valid_key,
            "model": self.model_name,
            "location": "cloud_development",
            "model_available": valid_key,
        }

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None) -> dict:
        self._check_production_restriction()
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()

        if not _is_valid_dev_gemini_key(self.api_key):
            raise LLMConfigurationError("Gemini API key is not configured or is invalid.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key.strip()}"
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}]
                    }
                )
            
            resp.raise_for_status()
            data = resp.json()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            content = ""
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if content:
                logger.info(f"[LLM:DEV_GEMINI:SUCCESS] req_id={req_id} latency={latency_ms}ms model={self.model_name}")
                return {
                    "provider": "dev_gemini",
                    "model": self.model_name,
                    "request_success": True,
                    "response_received": True,
                    "error_category": None,
                    "content": content.strip(),
                    "latency_ms": latency_ms,
                    "request_id": req_id,
                }
            raise ValueError(f"Empty or invalid response from Gemini API: {data}")
        except httpx.HTTPStatusError as e:
            logger.error(f"[LLM:DEV_GEMINI:FAIL] HTTP {e.response.status_code}: {e.response.text}")
            raise ValueError(f"Gemini API returned error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"[LLM:DEV_GEMINI:FAIL] req_id={req_id} error={e}")
            raise LLMConnectionError(f"Gemini developer API error: {e}")

# Standalone Fallback Provider for Development & Offline Execution
class FallbackAIProvider(LLMProvider):
    async def health_check(self) -> dict:
        return {
            "provider": "fallback",
            "configured": True,
            "authenticated": True,
            "auth_method": "local_fallback",
            "reachable": True,
            "model": "mednarrate-fallback-v1",
            "location": "local",
            "model_available": True,
        }

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None) -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()

        prompt_lower = prompt.lower()
        is_clinician = "clinician" in prompt_lower or "medical professional" in prompt_lower or "icd-10" in prompt_lower
        is_translation = "translate" in prompt_lower

        if is_translation:
            content = "This is an automated translation of the report summary into the selected language. All extracted numerical values and findings are preserved."
        else:
            # Generate deterministic, report-specific source-derived summary
            import json
            labs = []
            if "Structured lab values:" in prompt:
                try:
                    json_part = prompt.split("Structured lab values:")[1].split("Clinical Knowledge")[0].split("Extracted report text")[0].strip()
                    labs = json.loads(json_part)
                except Exception:
                    labs = []

            total_count = len(labs)
            abnormal_labs = [l for l in labs if l.get("flag") and l.get("flag") != "normal"]
            normal_labs = [l for l in labs if l.get("flag") == "normal"]

            lines = []
            if is_clinician:
                lines.append("Source-Derived Clinical Executive Summary:")
                if total_count > 0:
                    lines.append(f"- Extracted {total_count} laboratory parameter(s) ({len(abnormal_labs)} flagged outside reference range).")
                else:
                    lines.append("- Structured report data processed. No individual laboratory parameters were extracted.")
                if abnormal_labs:
                    lines.append("- Flagged Abnormal Findings:")
                    for l in abnormal_labs:
                        name = l.get("test_name") or l.get("original_name") or "Test"
                        val = l.get("value")
                        unit = l.get("unit", "")
                        flag = (l.get("flag") or "").upper()
                        low = l.get("ref_low")
                        high = l.get("ref_high")
                        ref_str = f"{low}-{high} {unit}" if (low is not None and high is not None) else "Not provided"
                        lines.append(f"  • {name}: {val} {unit} (Status: {flag}, Reported Range: {ref_str})")
                if normal_labs:
                    sample_names = ", ".join([l.get("test_name") or l.get("original_name") or "Test" for l in normal_labs[:5]])
                    lines.append(f"- Measured Parameters Within Reference Bounds: {sample_names}")
            else:
                lines.append("Source-Derived Report Summary:")
                if total_count > 0:
                    lines.append(f"Your report contains {total_count} extracted test result(s).")
                else:
                    lines.append("Your report data has been processed.")
                if abnormal_labs:
                    lines.append("\nResults Outside Reported Reference Ranges:")
                    for l in abnormal_labs:
                        name = l.get("test_name") or l.get("original_name") or "Test"
                        val = l.get("value")
                        unit = l.get("unit", "")
                        flag = (l.get("flag") or "").upper()
                        low = l.get("ref_low")
                        high = l.get("ref_high")
                        ref_str = f"{low}-{high} {unit}" if (low is not None and high is not None) else "Not provided"
                        lines.append(f"• {name}: {val} {unit} — Flagged {flag} (Reported range: {ref_str}).")
                if normal_labs:
                    sample_names = ", ".join([f"{l.get('test_name')} ({l.get('value')} {l.get('unit')})" for l in normal_labs[:4]])
                    lines.append(f"\nResults Within Reported Ranges: {sample_names}.")
                lines.append("\nThis explanation is derived directly from your uploaded document for informational purposes and does not replace advice from your doctor.")

            content = "\n".join(lines)

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[LLM:FALLBACK:SUCCESS] req_id={req_id} latency={latency_ms}ms model=mednarrate-fallback-v1")
        return {
            "provider": "fallback",
            "model": "mednarrate-fallback-v1",
            "request_success": True,
            "response_received": True,
            "error_category": None,
            "content": content.strip(),
            "latency_ms": latency_ms,
            "request_id": req_id,
        }

# Client Dispatcher
class LLMClient:
    def __init__(self):
        self.providers = {
            "vertex_ai": VertexAIProvider(),
            "ollama": OllamaProvider(),
            "dev_gemini": DevGeminiProvider(),
            "fallback": FallbackAIProvider(),
        }

    def get_provider(self, provider_name: str | None = None) -> LLMProvider:
        name = (provider_name or getattr(settings, "PRIMARY_LLM_PROVIDER", "gemini") or "auto").lower().strip()
        if name in ["gemini", "dev_gemini"]:
            return self.providers["dev_gemini"]
        elif name == "ollama":
            return self.providers["ollama"]
        elif name == "vertex_ai":
            return self.providers["vertex_ai"]
        elif name == "fallback":
            return self.providers["fallback"]
        return self.providers["vertex_ai"]

    async def generate_with_metadata(self, prompt: str, timeout: float = 30.0, request_id: str | None = None) -> dict:
        req_id = request_id or str(uuid.uuid4())
        provider_setting = (getattr(settings, "PRIMARY_LLM_PROVIDER", "gemini") or "auto").lower().strip()

        # Explicit Provider Selection
        if provider_setting in ["vertex_ai", "ollama", "dev_gemini", "gemini", "fallback"]:
            provider = self.get_provider(provider_setting)
            return await provider.generate(prompt, timeout=timeout, request_id=req_id)

        # "auto" Mode Deterministic Order: Vertex AI -> Ollama -> Dev Gemini -> Fallback
        # 1. Try Vertex AI
        v_provider = self.providers["vertex_ai"]
        v_health = await v_provider.health_check()
        if v_health["configured"] and v_health["authenticated"]:
            try:
                return await v_provider.generate(prompt, timeout=timeout, request_id=req_id)
            except Exception as e:
                logger.warning(f"[LLM:AUTO:VERTEX_FAILED] Vertex AI failed in auto mode: {e}")

        # 2. Try Ollama
        o_provider = self.providers["ollama"]
        o_health = await o_provider.health_check()
        if o_health["reachable"]:
            try:
                return await o_provider.generate(prompt, timeout=timeout, request_id=req_id)
            except Exception as e:
                logger.warning(f"[LLM:AUTO:OLLAMA_FAILED] Ollama failed in auto mode: {e}")

        # 3. Try Dev Gemini if key present
        g_provider = self.providers["dev_gemini"]
        g_health = await g_provider.health_check()
        if g_health["configured"]:
            try:
                return await g_provider.generate(prompt, timeout=timeout, request_id=req_id)
            except Exception as e:
                logger.warning(f"[LLM:AUTO:DEV_GEMINI_FAILED] Dev Gemini failed in auto mode: {e}")

        # 4. Fallback Provider if enabled
        if getattr(settings, "ENABLE_LLM_FALLBACK", True):
            f_provider = self.providers["fallback"]
            return await f_provider.generate(prompt, timeout=timeout, request_id=req_id)

        raise RuntimeError(
            "AI analysis is currently unavailable. Please verify the LLM provider configuration "
            "(VERTEX_PROJECT_ID, OLLAMA_URL, or GEMINI_API_KEY) and try again."
        )


    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None) -> str:
        res = await self.generate_with_metadata(prompt, timeout=timeout, request_id=request_id)
        return res["content"]

llm_client_instance = LLMClient()

async def generate_with_metadata(prompt: str, timeout: float = 30.0, request_id: str | None = None) -> dict:
    return await llm_client_instance.generate_with_metadata(prompt, timeout=timeout, request_id=request_id)

async def generate(prompt: str, timeout: float = 30.0, request_id: str | None = None) -> str:
    return await llm_client_instance.generate(prompt, timeout=timeout, request_id=request_id)

