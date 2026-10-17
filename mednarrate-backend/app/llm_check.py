"""Check every configured LLM provider and say exactly why one fails.

    docker compose -p mednarrate-audit exec backend python -m app.llm_check
    (or, outside Docker)  python -m app.llm_check

Sends one tiny prompt to each provider that has credentials and prints a table:
working / failing, which model was used, and the real reason (invalid key,
quota exhausted, model name rejected, timeout...). API keys are never printed.
"""

from __future__ import annotations

import asyncio
import time

from app.core.config import settings
from app.services.llm_client import (
    LLMConfigurationError,
    OPENAI_COMPATIBLE,
    _gemini_key_blocked_by_environment,
    llm_client_instance,
)
from app.services.provider_health import classify_error, hint_for

PROMPT = "Reply with the single word: OK"


def _model_for(name: str) -> str:
    return {
        "vertex_ai": getattr(settings, "VERTEX_MODEL", ""),
        "gemini": getattr(settings, "GEMINI_MODEL", ""),
        "openai": getattr(settings, "OPENAI_TRANSLATION_MODEL", ""),
        "anthropic": getattr(settings, "ANTHROPIC_TRANSLATION_MODEL", ""),
        "mistral": getattr(settings, "MISTRAL_TRANSLATION_MODEL", ""),
        "ollama": getattr(settings, "OLLAMA_MODEL", ""),
        **{n: getattr(settings, m, "") for n, (_u, _k, m) in OPENAI_COMPATIBLE.items()},
    }.get(name, "")


def _credentials_present(name: str) -> tuple[bool, str]:
    if name == "vertex_ai":
        ok = bool(getattr(settings, "VERTEX_PROJECT_ID", None))
        return ok, "" if ok else "VERTEX_PROJECT_ID not set"
    if name == "gemini":
        key = getattr(settings, "GEMINI_API_KEY", None)
        if not (key and str(key).strip()):
            return False, "GEMINI_API_KEY not set"
        if _gemini_key_blocked_by_environment():
            return False, (
                "key present, but direct Gemini keys are refused when ENVIRONMENT=production "
                "(set ENVIRONMENT=development, or ALLOW_GEMINI_API_KEY_IN_PRODUCTION=true after "
                "reading the privacy note in .env.example)"
            )
        return True, ""
    if name in {"openai", "anthropic", "mistral"}:
        key = getattr(settings, f"{name.upper()}_API_KEY", None)
        ok = bool(key and str(key).strip())
        return ok, "" if ok else f"{name.upper()}_API_KEY not set"
    if name in OPENAI_COMPATIBLE:
        key_setting = OPENAI_COMPATIBLE[name][1]
        ok = bool(getattr(settings, key_setting, None))
        return ok, "" if ok else f"{key_setting} not set"
    if name == "ollama":
        return bool(getattr(settings, "OLLAMA_URL", None)), ""
    return False, "unknown provider"


async def _probe(name: str) -> dict:
    ok, why = _credentials_present(name)
    row = {"provider": name, "model": _model_for(name), "status": "skipped", "detail": why, "latency": ""}
    if not ok:
        return row
    started = time.monotonic()
    try:
        provider = llm_client_instance.get_provider(name)
        res = await asyncio.wait_for(
            provider.generate(PROMPT, timeout=25.0, thinking_level="LOW", config={"max_tokens": 32}),
            timeout=30.0,
        )
        row.update(
            status="WORKING",
            model=res.get("model") or row["model"],
            detail=(res.get("content") or "")[:40].replace("\n", " "),
            latency=f"{time.monotonic() - started:.1f}s",
        )
    except LLMConfigurationError as exc:
        row.update(status="NOT USABLE", detail=str(exc)[:160])
    except Exception as exc:  # noqa: BLE001 - diagnostics must never crash
        kind, _ = classify_error(exc)
        row.update(
            status="FAILING",
            detail=f"{kind}: {hint_for(kind)} [{str(getattr(exc, 'error_detail', '') or exc)[:160]}]",
            latency=f"{time.monotonic() - started:.1f}s",
        )
    return row


async def main() -> int:
    print(f"ENVIRONMENT={settings.ENVIRONMENT}  PRIMARY_LLM_PROVIDER={settings.PRIMARY_LLM_PROVIDER}  "
          f"ENABLE_LLM_FALLBACK={settings.ENABLE_LLM_FALLBACK}\n")
    names = ["vertex_ai", "gemini", "openai", "anthropic", "mistral", *OPENAI_COMPATIBLE, "ollama"]
    rows = await asyncio.gather(*[_probe(n) for n in names])
    for r in rows:
        print(f"{r['provider']:<10} {r['status']:<11} model={r['model'] or '-':<26} {r['latency']:<6} {r['detail']}")
    working = [r["provider"] for r in rows if r["status"] == "WORKING"]
    chain = llm_client_instance._build_chain(
        settings.PRIMARY_LLM_PROVIDER, "none" if not settings.ENABLE_LLM_FALLBACK else "ollama",
        bool(settings.ENABLE_LLM_FALLBACK),
    )
    print("\nChat / summaries will try, in order:", " -> ".join(chain + ["built-in template"]))
    print("Working providers:", ", ".join(working) if working else "NONE - AI chat and translation will not work")
    if not working:
        print("Fix the lines marked FAILING / NOT USABLE above, then run this again.")
    return 0 if working else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
