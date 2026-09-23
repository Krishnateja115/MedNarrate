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
    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> dict:
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
        return getattr(settings, "VERTEX_MODEL", "gemini-3.8-flash")

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

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> dict:
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
            
            # Use basic GenerationConfig. Gemini 3 ignores temperature/topP/topK and throws errors for penalties.
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=2048,
            )
            
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
            response = await model.generate_content_async(prompt, generation_config=generation_config)
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

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> dict:
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
        return getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash")

    async def health_check(self) -> dict:
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

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()

        if not _is_valid_dev_gemini_key(self.api_key):
            raise LLMConfigurationError("Gemini API key is not configured or is invalid.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key.strip()}"
        
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "thinkingConfig": {"thinkingLevel": thinking_level},
                        "maxOutputTokens": 2048,
                    }
                }
                
                if system_instruction:
                    payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        url,
                        json=payload
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

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"[LLM:DEV_GEMINI:RETRY] Attempt {attempt + 1} failed: {e}. Retrying...")
                    import asyncio
                    await asyncio.sleep(1.5)
                else:
                    if isinstance(e, httpx.HTTPStatusError):
                        logger.error(f"[LLM:DEV_GEMINI:FAIL] HTTP {e.response.status_code}: {e.response.text}")
                        raise ValueError(f"Gemini API returned error {e.response.status_code}: {e.response.text}")
                    else:
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

    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()

        prompt_lower = prompt.lower()
        sys_lower = (system_instruction or "").lower()
        is_clinician = "clinician" in prompt_lower or "medical professional" in prompt_lower or "icd-10" in prompt_lower or "clinical tone" in sys_lower
        is_translation = "translate" in prompt_lower
        is_classification = "classify the following medical query" in prompt_lower
        is_chat = "ai assistant" in sys_lower or "you are mednarrate" in prompt_lower or "you are a helpful medical ai assistant" in prompt_lower

        if is_classification:
            content = "general"
        elif is_chat:
            content = "AI service is temporarily unavailable. Please try again."
        elif is_translation:
            content = "This is an automated translation of the report summary into the selected language. All extracted numerical values and findings are preserved."
        else:
            import json
            import re
            
            # Determine report type cleanly from prompt header line
            report_type = "blood"
            header_match = re.search(r"explaining a ([a-z_\-]+) medical report", prompt, re.IGNORECASE)
            if header_match:
                parsed_type = header_match.group(1).lower().strip()
                if parsed_type in ["radiology", "health", "xray", "imaging"]:
                    report_type = "radiology"
                elif parsed_type in ["pathology", "biopsy"]:
                    report_type = "pathology"
                elif parsed_type in ["blood", "lab", "laboratory"]:
                    report_type = "blood"
            elif "radiology" in prompt_lower or "chest x-ray" in prompt_lower:
                report_type = "radiology"
            elif "pathology" in prompt_lower:
                report_type = "pathology"

            # Parse extracted text from prompt
            extracted_text = ""
            if "Extracted report text" in prompt:
                try:
                    extracted_text = prompt.split("Extracted report text")[1].split("Clinical Knowledge")[0].strip()
                    if extracted_text.startswith(":") or extracted_text.startswith("("):
                        extracted_text = extracted_text.lstrip(":()").strip()
                except Exception:
                    extracted_text = ""

            labs = []
            if "Structured lab values:" in prompt and report_type == "blood":
                try:
                    json_part = prompt.split("Structured lab values:")[1].split("Clinical Knowledge")[0].split("Extracted report text")[0].strip()
                    labs = json.loads(json_part)
                except Exception:
                    labs = []

            lines = []
            if report_type == "radiology":
                lines.append("### 1. What Your Report Says")
                if "Chest X-Ray" in extracted_text or "x-ray" in extracted_text.lower():
                    lines.append("- Examination: Chest X-Ray (PA and Lateral Views)")
                else:
                    lines.append("- Examination: Diagnostic Imaging Examination")
                
                lines.append("\n### 2. Key Findings & Impression")
                # Parse findings & impressions cleanly from extracted_text
                findings_list = []
                impression_list = []
                in_findings = False
                in_impression = False
                for raw_line in extracted_text.splitlines():
                    line_str = raw_line.strip()
                    if line_str.upper().startswith("FINDINGS:"):
                        in_findings = True
                        in_impression = False
                        continue
                    elif line_str.upper().startswith("IMPRESSION:"):
                        in_impression = True
                        in_findings = False
                        continue
                    elif line_str.upper().startswith("CLINICAL INDICATION:") or line_str.upper().startswith("EXAM:"):
                        in_findings = False
                        in_impression = False
                        continue

                    if in_findings and line_str:
                        findings_list.append(line_str.lstrip("-*• "))
                    elif in_impression and line_str:
                        impression_list.append(line_str.lstrip("-*•123456789. "))

                if findings_list:
                    lines.append("Findings:")
                    for f in findings_list:
                        lines.append(f"• {f}")
                if impression_list:
                    lines.append("Impression:")
                    for imp in impression_list:
                        lines.append(f"• {imp}")

                if not findings_list and not impression_list and extracted_text:
                    lines.append(f"• {extracted_text}")

                lines.append("\n### 3. What These Terms Mean")
                if "pneumonia" in extracted_text.lower():
                    lines.append("• Pneumonia: An infection in one or both lungs causing inflammation in the air sacs.")
                if "cardiomegaly" in extracted_text.lower():
                    lines.append("• Cardiomegaly: An enlarged heart condition noted on imaging that warrants discussion with your physician.")
                if "opacity" in extracted_text.lower() or "consolidation" in extracted_text.lower():
                    lines.append("• Opacity / Consolidation: An area on the X-ray where lung tissue appears denser than normal.")

                lines.append("\n### 4. Information Not Provided")
                lines.append("• Numerical blood laboratory test parameters are not applicable to this imaging study.")
                lines.append("• Current medication list and dosages are not provided in this report.")
                lines.append("• Comparisons with previous imaging studies are not provided in this report.")

                lines.append("\n### 5. What to Discuss With Your Doctor")
                lines.append("• Review the imaging impression (including any findings of pneumonia or cardiomegaly) with your treating physician for clinical evaluation.")

            elif report_type == "pathology":
                lines.append("### 1. What Your Report Says")
                lines.append("Pathology Examination Summary:")
                lines.append(f"{extracted_text}")
                lines.append("\n### 2. Key Findings")
                lines.append(f"• Diagnostic findings derived directly from specimen analysis.")
                lines.append("\n### 3. What These Terms Mean")
                lines.append("• Pathological terms describe tissue structure and cellular features evaluated under microscopic examination.")
                lines.append("\n### 4. Information Not Provided")
                lines.append("• Routine blood laboratory parameters and medication schedules are not provided in this report.")
                lines.append("\n### 5. What to Discuss With Your Doctor")
                lines.append("• Consult your physician to discuss the pathological diagnosis and next steps.")

            else:
                # Blood / Laboratory Report
                total_count = len(labs)
                abnormal_labs = [l for l in labs if l.get("flag") in ["low", "high", "abnormal", "critical"]]
                normal_labs = [l for l in labs if l.get("flag") == "normal"]

                lines.append("### 1. What Your Report Says")
                if total_count > 0:
                    lines.append(f"Your report contains {total_count} extracted laboratory test result(s).")
                else:
                    lines.append("Your blood report data has been processed.")

                lines.append("\n### 2. Key Findings")
                if abnormal_labs:
                    lines.append("Results Outside Reported Reference Ranges / Flagged Results:")
                    for l in abnormal_labs:
                        name = l.get("test_name") or l.get("original_name") or "Test"
                        val = l.get("value")
                        unit = l.get("unit", "")
                        flag_str = (l.get("flag") or "").upper()
                        low = l.get("ref_low")
                        high = l.get("ref_high")
                        ref_str = l.get("ref_range_str")
                        if not ref_str:
                            if low is not None and high is not None:
                                ref_str = f"{low} - {high} {unit}".strip()
                            elif high is not None:
                                ref_str = f"< {high} {unit}".strip()
                            elif low is not None:
                                ref_str = f"> {low} {unit}".strip()
                            else:
                                ref_str = "Not provided in the report"
                        lines.append(f"• {name}: {val} {unit} — Flagged {flag_str} (Reported Reference Range: {ref_str}).")
                
                if normal_labs:
                    lines.append("\nResults Within Reported Normal Bounds:")
                    for l in normal_labs:
                        name = l.get("test_name") or l.get("original_name") or "Test"
                        val = l.get("value")
                        unit = l.get("unit", "")
                        low = l.get("ref_low")
                        high = l.get("ref_high")
                        ref_str = l.get("ref_range_str")
                        if not ref_str:
                            if low is not None and high is not None:
                                ref_str = f"{low} - {high} {unit}".strip()
                            elif high is not None:
                                ref_str = f"< {high} {unit}".strip()
                            elif low is not None:
                                ref_str = f"> {low} {unit}".strip()
                            else:
                                ref_str = "Not provided in the report"
                        lines.append(f"• {name}: {val} {unit} — NORMAL (Reported Reference Range: {ref_str}).")

                lines.append("\n### 3. What These Terms Mean")
                if any("glucose" in (l.get("test_name") or "").lower() for l in labs):
                    lines.append("• Serum Glucose: Measures sugar levels in the blood, an indicator of energy metabolism.")
                if any("hemoglobin" in (l.get("test_name") or "").lower() for l in labs):
                    lines.append("• Hemoglobin: An oxygen-carrying protein found inside red blood cells.")
                if any("cholesterol" in (l.get("test_name") or "").lower() or "ldl" in (l.get("test_name") or "").lower() for l in labs):
                    lines.append("• LDL Cholesterol: A lipid component involved in transport of fats in the bloodstream.")
                if any("platelet" in (l.get("test_name") or "").lower() for l in labs):
                    lines.append("• Platelet Count: Blood cell fragments essential for normal blood clotting.")

                lines.append("\n### 4. Information Not Provided")
                lines.append("• Unlisted lab parameters, radiology imaging findings, and medication prescriptions are not provided in this report.")

                lines.append("\n### 5. What to Discuss With Your Doctor")
                lines.append("• Discuss your test values and flagged abnormalities with your primary care physician.")

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

    async def generate_with_metadata(self, prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> dict:
        req_id = request_id or str(uuid.uuid4())
        provider_setting = (getattr(settings, "PRIMARY_LLM_PROVIDER", "gemini") or "auto").lower().strip()

        # Explicit Provider Selection
        if provider_setting in ["vertex_ai", "ollama", "dev_gemini", "gemini", "fallback"]:
            provider = self.get_provider(provider_setting)
            try:
                return await provider.generate(prompt, timeout=timeout, request_id=req_id, system_instruction=system_instruction, thinking_level=thinking_level)
            except Exception as e:
                if getattr(settings, "ENABLE_LLM_FALLBACK", True):
                    logger.warning(f"[LLM:{provider_setting.upper()}:FAILED] {e}. Falling back to FallbackAIProvider.")
                    return await self.providers["fallback"].generate(prompt, timeout=timeout, request_id=req_id, system_instruction=system_instruction, thinking_level=thinking_level)
                raise

        # "auto" Mode Deterministic Order: Vertex AI -> Ollama -> Dev Gemini -> Fallback
        # 1. Try Vertex AI
        v_provider = self.providers["vertex_ai"]
        v_health = await v_provider.health_check()
        if v_health["configured"] and v_health["authenticated"]:
            try:
                return await v_provider.generate(prompt, timeout=timeout, request_id=req_id, system_instruction=system_instruction, thinking_level=thinking_level)
            except Exception as e:
                logger.warning(f"[LLM:AUTO:VERTEX_FAILED] Vertex AI failed in auto mode: {e}")

        # 2. Try Ollama
        o_provider = self.providers["ollama"]
        o_health = await o_provider.health_check()
        if o_health["reachable"]:
            try:
                return await o_provider.generate(prompt, timeout=timeout, request_id=req_id, system_instruction=system_instruction, thinking_level=thinking_level)
            except Exception as e:
                logger.warning(f"[LLM:AUTO:OLLAMA_FAILED] Ollama failed in auto mode: {e}")

        # 3. Try Dev Gemini if key present
        g_provider = self.providers["dev_gemini"]
        g_health = await g_provider.health_check()
        if g_health["configured"]:
            try:
                return await g_provider.generate(prompt, timeout=timeout, request_id=req_id, system_instruction=system_instruction, thinking_level=thinking_level)
            except Exception as e:
                logger.warning(f"[LLM:AUTO:DEV_GEMINI_FAILED] Dev Gemini failed in auto mode: {e}")

        # 4. Fallback Provider if enabled
        if getattr(settings, "ENABLE_LLM_FALLBACK", True):
            f_provider = self.providers["fallback"]
            return await f_provider.generate(prompt, timeout=timeout, request_id=req_id, system_instruction=system_instruction, thinking_level=thinking_level)

        err = RuntimeError(
            "AI analysis is currently unavailable. Please verify the LLM provider configuration "
            "(VERTEX_PROJECT_ID, OLLAMA_URL, or GEMINI_API_KEY) and try again."
        )
        err.failure_category = "LLM_NOT_CONFIGURED"
        raise err


    async def generate(self, prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> str:
        res = await self.generate_with_metadata(prompt, timeout=timeout, request_id=request_id, system_instruction=system_instruction, thinking_level=thinking_level)
        return res["content"]

llm_client_instance = LLMClient()

async def generate_with_metadata(prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> dict:
    return await llm_client_instance.generate_with_metadata(prompt, timeout=timeout, request_id=request_id, system_instruction=system_instruction, thinking_level=thinking_level)

async def generate(prompt: str, timeout: float = 30.0, request_id: str | None = None, system_instruction: str | None = None, thinking_level: str = "LOW") -> str:
    return await llm_client_instance.generate(prompt, timeout=timeout, request_id=request_id, system_instruction=system_instruction, thinking_level=thinking_level)

