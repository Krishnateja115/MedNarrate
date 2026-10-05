import os

# We will use python regex to replace the content of llm_client.py
# specifically replacing GroqProvider and DeepSeekProvider with new ones.

import re

file_path = r"C:\Users\manas\Downloads\MedNarrate-main\mednarrate-backend\app\services\llm_client.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I will write out the full new code for the providers and replace lines from GroqProvider to the end of DeepSeekProvider.
# Also update the LLMClient initialization.

NEW_PROVIDERS = """
class OpenAIProvider(LLMProvider):
    def get_api_key(self) -> str | None:
        return getattr(settings, "OPENAI_API_KEY", None)

    def get_model_name(self) -> str:
        return getattr(settings, "OPENAI_TRANSLATION_MODEL", "gpt-6.1-sol")

    async def health_check(self, config: dict | None = None) -> dict:
        api_key = self.get_api_key()
        valid = bool(api_key and api_key.strip())
        return {
            "provider": "openai",
            "configured": valid,
            "authenticated": valid,
            "auth_method": "direct_api_key",
            "reachable": valid,
            "model": self.get_model_name(),
            "location": "cloud",
            "model_available": valid,
        }

    async def generate(
        self,
        prompt: str,
        timeout: float = 30.0,
        request_id: str | None = None,
        system_instruction: str | None = None,
        thinking_level: str = "LOW",
        config: dict | None = None,
    ) -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()
        api_key = self.get_api_key()
        if not api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is missing")

        model_name = self.get_model_name()
        
        messages = []
        if system_instruction:
            messages.append({"role": "developer", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
        }
        if _translation_request.get():
            payload["response_format"] = {"type": "json_object"}
            # "gpt-6.1-sol" is a reasoning model, require reasoning_effort
            payload["reasoning_effort"] = "low"
            # OpenAI requires max_completion_tokens for o1/o3/gpt-6.1 reasoning models
            payload["max_completion_tokens"] = min(settings.TRANSLATION_MAX_OUTPUT_TOKENS, 4000)
        else:
            payload["max_completion_tokens"] = 2048
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key.strip()}"}
                )
                resp.raise_for_status()
                data = resp.json()
                latency_ms = int((time.time() - start_time) * 1000)
                content = data["choices"][0]["message"]["content"]
                logger.info(f"[LLM:OPENAI:SUCCESS] req_id={req_id} latency={latency_ms}ms model={model_name}")
                return {
                    "provider": "openai",
                    "model": model_name,
                    "request_success": True,
                    "response_received": True,
                    "error_category": None,
                    "content": content.strip(),
                    "latency_ms": latency_ms,
                    "request_id": req_id,
                }
        except httpx.HTTPStatusError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[LLM:OPENAI:FAIL] req_id={req_id} status={e.response.status_code}")
            err = LLMConnectionError(f"OpenAI API error: {e}")
            setattr(err, "status_code", e.response.status_code)
            raise err
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[LLM:OPENAI:FAIL] req_id={req_id} latency={latency_ms}ms error={e}")
            raise LLMConnectionError(f"OpenAI API error: {e}")


class AnthropicProvider(LLMProvider):
    def get_api_key(self) -> str | None:
        return getattr(settings, "ANTHROPIC_API_KEY", None)

    def get_model_name(self) -> str:
        return getattr(settings, "ANTHROPIC_TRANSLATION_MODEL", "claude-sonnet-5-5")

    async def health_check(self, config: dict | None = None) -> dict:
        api_key = self.get_api_key()
        valid = bool(api_key and api_key.strip())
        return {
            "provider": "anthropic",
            "configured": valid,
            "authenticated": valid,
            "auth_method": "direct_api_key",
            "reachable": valid,
            "model": self.get_model_name(),
            "location": "cloud",
            "model_available": valid,
        }

    async def generate(
        self,
        prompt: str,
        timeout: float = 30.0,
        request_id: str | None = None,
        system_instruction: str | None = None,
        thinking_level: str = "LOW",
        config: dict | None = None,
    ) -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()
        api_key = self.get_api_key()
        if not api_key:
            raise LLMConfigurationError("ANTHROPIC_API_KEY is missing")

        model_name = self.get_model_name()
        
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": min(settings.TRANSLATION_MAX_OUTPUT_TOKENS, 4000) if _translation_request.get() else 2048,
        }
        if system_instruction:
            payload["system"] = system_instruction

        if _translation_request.get():
            # Anthropic enforces JSON via tools
            payload["tools"] = [{
                "name": "generate_translation",
                "description": "Output the final translation in structured JSON format.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "translation": {"type": "string", "description": "JSON string of the translation"}
                    },
                    "required": ["translation"]
                }
            }]
            payload["tool_choice"] = {"type": "tool", "name": "generate_translation"}
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=payload,
                    headers={
                        "x-api-key": api_key.strip(),
                        "anthropic-version": "2023-06-01",
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                latency_ms = int((time.time() - start_time) * 1000)
                
                content = ""
                if _translation_request.get():
                    for item in data.get("content", []):
                        if item.get("type") == "tool_use" and item.get("name") == "generate_translation":
                            content = item.get("input", {}).get("translation", "")
                            break
                    if not content:
                        raise ValueError("Anthropic did not use the requested tool to output JSON.")
                else:
                    content = "".join(item["text"] for item in data.get("content", []) if item.get("type") == "text")
                
                logger.info(f"[LLM:ANTHROPIC:SUCCESS] req_id={req_id} latency={latency_ms}ms model={model_name}")
                return {
                    "provider": "anthropic",
                    "model": model_name,
                    "request_success": True,
                    "response_received": True,
                    "error_category": None,
                    "content": content.strip(),
                    "latency_ms": latency_ms,
                    "request_id": req_id,
                }
        except httpx.HTTPStatusError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[LLM:ANTHROPIC:FAIL] req_id={req_id} status={e.response.status_code}")
            err = LLMConnectionError(f"Anthropic API error: {e}")
            setattr(err, "status_code", e.response.status_code)
            raise err
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[LLM:ANTHROPIC:FAIL] req_id={req_id} latency={latency_ms}ms error={e}")
            raise LLMConnectionError(f"Anthropic API error: {e}")

class MistralProvider(LLMProvider):
    def get_api_key(self) -> str | None:
        return getattr(settings, "MISTRAL_API_KEY", None)

    def get_model_name(self) -> str:
        return getattr(settings, "MISTRAL_TRANSLATION_MODEL", "mistral-large-2512")

    async def health_check(self, config: dict | None = None) -> dict:
        api_key = self.get_api_key()
        valid = bool(api_key and api_key.strip())
        return {
            "provider": "mistral",
            "configured": valid,
            "authenticated": valid,
            "auth_method": "direct_api_key",
            "reachable": valid,
            "model": self.get_model_name(),
            "location": "cloud",
            "model_available": valid,
        }

    async def generate(
        self,
        prompt: str,
        timeout: float = 30.0,
        request_id: str | None = None,
        system_instruction: str | None = None,
        thinking_level: str = "LOW",
        config: dict | None = None,
    ) -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()
        api_key = self.get_api_key()
        if not api_key:
            raise LLMConfigurationError("MISTRAL_API_KEY is missing")

        model_name = self.get_model_name()
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": min(settings.TRANSLATION_MAX_OUTPUT_TOKENS, 4000) if _translation_request.get() else 2048,
        }
        if _translation_request.get():
            payload["response_format"] = {"type": "json_object"}
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key.strip()}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                latency_ms = int((time.time() - start_time) * 1000)
                content = data["choices"][0]["message"]["content"]
                logger.info(f"[LLM:MISTRAL:SUCCESS] req_id={req_id} latency={latency_ms}ms model={model_name}")
                return {
                    "provider": "mistral",
                    "model": model_name,
                    "request_success": True,
                    "response_received": True,
                    "error_category": None,
                    "content": content.strip(),
                    "latency_ms": latency_ms,
                    "request_id": req_id,
                }
        except httpx.HTTPStatusError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[LLM:MISTRAL:FAIL] req_id={req_id} status={e.response.status_code}")
            err = LLMConnectionError(f"Mistral API error: {e}")
            setattr(err, "status_code", e.response.status_code)
            raise err
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[LLM:MISTRAL:FAIL] req_id={req_id} latency={latency_ms}ms error={e}")
            raise LLMConnectionError(f"Mistral API error: {e}")
"""

# Replace GroqProvider and DeepSeekProvider
pattern = r"class GroqProvider\(LLMProvider\):.*?# Standalone Fallback Provider for Development & Offline Execution"
new_content = re.sub(pattern, NEW_PROVIDERS + "\n# Standalone Fallback Provider for Development & Offline Execution", content, flags=re.DOTALL)

# Update Client Dispatcher
dispatcher_pattern = r"""    def __init__\(self\):
        self\.providers = \{
            "vertex_ai": VertexAIProvider\(\),
            "ollama": OllamaProvider\(\),
            "dev_gemini": DevGeminiProvider\(\),
            "fallback": FallbackAIProvider\(\),
            "groq_gpt": GroqProvider\("gpt"\),
            "groq_qwen": GroqProvider\("qwen"\),
            "deepseek": DeepSeekProvider\(\),
        \}"""

new_dispatcher = """    def __init__(self):
        self.providers = {
            "vertex_ai": VertexAIProvider(),
            "ollama": OllamaProvider(),
            "dev_gemini": DevGeminiProvider(),
            "fallback": FallbackAIProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "mistral": MistralProvider(),
            # Aliasing gemini to DevGeminiProvider
            "gemini": DevGeminiProvider(),
        }"""

new_content = new_content.replace(dispatcher_pattern, new_dispatcher)

get_provider_pattern = r"""        if name in \["gemini", "dev_gemini"\]:
            return self\.providers\["dev_gemini"\]
        elif name == "ollama":
            return self\.providers\["ollama"\]
        elif name == "vertex_ai":
            return self\.providers\["vertex_ai"\]
        elif name == "fallback":
            return self\.providers\["fallback"\]
        elif name in \["groq_gpt", "groq_qwen", "deepseek"\]:
            return self\.providers\[name\]"""

new_get_provider = """        if name in ["gemini", "dev_gemini"]:
            return self.providers["dev_gemini"]
        elif name == "ollama":
            return self.providers["ollama"]
        elif name == "vertex_ai":
            return self.providers["vertex_ai"]
        elif name == "fallback":
            return self.providers["fallback"]
        elif name in ["openai", "anthropic", "mistral"]:
            return self.providers[name]"""

new_content = new_content.replace(get_provider_pattern, new_get_provider)

# Update status code propagation in DevGeminiProvider
dev_gemini_catch_pattern = r"""                        logger.error\(f"\[LLM:DEV_GEMINI:FAIL\] req_id={req_id} error_type={type\(e\)\.__name__}"\)
                        raise LLMConnectionError\("Gemini developer API request failed."\) from e"""

dev_gemini_catch_new = """                        logger.error(f"[LLM:DEV_GEMINI:FAIL] req_id={req_id} error_type={type(e).__name__}")
                        err = LLMConnectionError("Gemini developer API request failed.")
                        if is_http_error:
                            setattr(err, "status_code", status_code)
                        raise err from e"""
new_content = new_content.replace(dev_gemini_catch_pattern, dev_gemini_catch_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated llm_client.py")
