"""Shared health tracking ("circuit breaker") for LLM providers.

Why this exists
---------------
Without it, every chat message, report summary and translation chunk blindly
retried every provider, even one whose key was invalid, whose model name did
not exist, or whose quota was already exhausted. That wastes the remaining
free-tier allowance on the *other* providers (extra retries, extra chunks),
makes every request slow, and ends in the generic "AI service is temporarily
unavailable" message with no hint why.

A provider that fails for a *persistent* reason (auth, quota, unknown model,
not configured) is skipped for a cool-down period instead of being retried on
every request. Transient failures (timeouts, 5xx) get a short cool-down.
State is per process; it is deliberately tiny and dependency free.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from typing import Any

# Failure kinds ------------------------------------------------------------
QUOTA = "quota_or_rate_limit"
AUTH = "invalid_or_unauthorised_key"
MODEL = "model_not_found_or_bad_request"
NOT_CONFIGURED = "not_configured"
TRANSIENT = "temporary_outage_or_timeout"
NETWORK = "network_unreachable"
SAFETY = "safety_block"
UNKNOWN = "unknown_error"

# Seconds a provider is skipped after a failure of that kind.
_COOLDOWN_SECONDS = {
    QUOTA: 90.0,
    AUTH: 1800.0,
    MODEL: 900.0,
    NOT_CONFIGURED: 300.0,
    TRANSIENT: 20.0,
    NETWORK: 20.0,
    UNKNOWN: 30.0,
    SAFETY: 0.0,  # a safety block is about the prompt, not the provider
}
# Quota messages that say the *daily* allowance is gone back off for longer.
_DAILY_QUOTA_COOLDOWN = 1800.0
_DAILY_HINT = re.compile(
    r"per\s*day|daily|insufficient_quota|exceeded your current quota|billing",
    re.IGNORECASE,
)

_HINTS = {
    QUOTA: "Quota or rate limit reached. Wait for the allowance to reset, add billing, or use another provider.",
    AUTH: "The API key was rejected. Check the key value and that it is enabled for this API.",
    MODEL: "The model name was not accepted. Check the *_MODEL / *_TRANSLATION_MODEL setting for this provider.",
    NOT_CONFIGURED: "No usable credentials for this provider in this environment.",
    TRANSIENT: "The provider timed out or is temporarily unavailable.",
    NETWORK: "The server could not open a connection to the provider (no internet, DNS, proxy or TLS problem). Check outbound HTTPS from wherever the API runs, including inside Docker.",
    SAFETY: "The provider blocked this content.",
    UNKNOWN: "Unexpected error; see the server log for details.",
}


def hint_for(kind: str) -> str:
    return _HINTS.get(kind, _HINTS[UNKNOWN])


def http_error_detail(response: Any, limit: int = 240) -> str:
    """Short, key-free description of an HTTP error body from a provider."""
    try:
        data = response.json()
        if isinstance(data, dict):
            err = data.get("error", data)
            if isinstance(err, dict):
                text = err.get("message") or err.get("status") or str(err)
            else:
                text = str(err)
        else:
            text = str(data)
    except Exception:
        text = getattr(response, "text", "") or ""
    text = re.sub(r"(AIza[0-9A-Za-z_\-]{10,}|sk-[0-9A-Za-z_\-]{10,}|Bearer\s+\S+)", "[redacted]", text)
    return " ".join(text.split())[:limit]


_TIMEOUT_NAMES = {"ReadTimeout", "WriteTimeout", "PoolTimeout", "ConnectTimeout", "TimeoutException", "TimeoutError", "CancelledError"}
_NETWORK_NAMES = {
    "ConnectError", "NetworkError", "ReadError", "WriteError", "CloseError", "ProxyError",
    "RemoteProtocolError", "ConnectionError", "ConnectionResetError", "ConnectionRefusedError",
    "gaierror", "SSLError", "SSLCertVerificationError", "CertificateError", "UnsupportedProtocol",
}


def _exception_chain(exc: BaseException):
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def describe_error(exc: BaseException, limit: int = 200) -> str:
    """Key-free one-line description: exception types in the chain plus the message."""
    names = [type(e).__name__ for e in _exception_chain(exc)]
    text = " ".join(str(exc).split())
    text = re.sub(r"(AIza[0-9A-Za-z_\-]{10,}|AQ\.[0-9A-Za-z_\-]{10,}|sk-[0-9A-Za-z_\-]{10,}|Bearer\s+\S+)", "[redacted]", text)
    detail = getattr(exc, "error_detail", "")
    out = " < ".join(dict.fromkeys(names))
    if text:
        out += f": {text}"
    if detail:
        out += f" ({detail})"
    return out[:limit]


def classify_error(exc: BaseException) -> tuple[str, float]:
    """Return (kind, cooldown_seconds) for an exception raised by a provider."""
    if getattr(exc, "is_safety_block", False):
        return SAFETY, _COOLDOWN_SECONDS[SAFETY]

    status = getattr(exc, "status_code", None)
    if status is None:
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None)
    detail = f"{exc} {getattr(exc, 'error_detail', '')}"
    low = detail.lower()
    name = type(exc).__name__
    if status is None:
        # Some wrappers keep the status only in the message ("... 403 Forbidden").
        found = re.search(r"\b(401|403|404|429|500|502|503|504)\b", detail)
        if found:
            status = int(found.group(1))

    chain_names = {type(e).__name__ for e in _exception_chain(exc)}
    if status is None and "CERTIFICATE_VERIFY_FAILED" in detail:
        return NETWORK, _COOLDOWN_SECONDS[NETWORK]

    if name == "LLMConfigurationError":
        # Missing / placeholder credentials or a refused environment - never a
        # rejected-key response from the provider.
        return NOT_CONFIGURED, _COOLDOWN_SECONDS[NOT_CONFIGURED]

    if status == 429 or "resource_exhausted" in low or "rate limit" in low or "quota" in low:
        daily = bool(_DAILY_HINT.search(detail))
        return QUOTA, _DAILY_QUOTA_COOLDOWN if daily else _COOLDOWN_SECONDS[QUOTA]
    if status in (401, 403) or "api key" in low and ("invalid" in low or "missing" in low or "not valid" in low):
        return AUTH, _COOLDOWN_SECONDS[AUTH]
    if status in (400, 404, 422):
        return MODEL, _COOLDOWN_SECONDS[MODEL]
    if name == "LLMConfigurationError" or "not configured" in low or "is missing" in low:
        return NOT_CONFIGURED, _COOLDOWN_SECONDS[NOT_CONFIGURED]
    if status is None and chain_names & _TIMEOUT_NAMES:
        return TRANSIENT, _COOLDOWN_SECONDS[TRANSIENT]
    if status is None and chain_names & _NETWORK_NAMES:
        return NETWORK, _COOLDOWN_SECONDS[NETWORK]
    if status in (500, 502, 503, 504) or isinstance(exc, (TimeoutError,)) or "timeout" in low or "timed out" in low or "overloaded" in low or "connection" in low or "connect" in low and "fail" in low:
        return TRANSIENT, _COOLDOWN_SECONDS[TRANSIENT]
    return UNKNOWN, _COOLDOWN_SECONDS[UNKNOWN]


@dataclass
class _State:
    until: float = 0.0
    kind: str = ""
    failures: int = 0
    last_error: str = ""


class ProviderHealth:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[str, _State] = {}

    @staticmethod
    def _key(name: str) -> str:
        n = (name or "").lower().strip()
        return "gemini" if n in {"dev_gemini", "gemini"} else n

    @staticmethod
    def classify(exc: BaseException) -> str:
        return classify_error(exc)[0]

    def is_available(self, name: str) -> bool:
        with self._lock:
            st = self._state.get(self._key(name))
            return st is None or time.monotonic() >= st.until

    def seconds_until_retry(self, name: str) -> float:
        with self._lock:
            st = self._state.get(self._key(name))
            return 0.0 if st is None else max(0.0, st.until - time.monotonic())

    def last_kind(self, name: str) -> str:
        """Failure kind that put ``name`` on cool-down ("" when healthy)."""
        with self._lock:
            st = self._state.get(self._key(name))
            return st.kind if st else ""

    def record_success(self, name: str) -> None:
        with self._lock:
            self._state.pop(self._key(name), None)

    def record_failure(self, name: str, exc: BaseException) -> str:
        kind, cooldown = classify_error(exc)
        if cooldown <= 0:
            return kind
        with self._lock:
            st = self._state.setdefault(self._key(name), _State())
            st.failures += 1
            st.kind = kind
            st.last_error = describe_error(exc)
            # Repeated failures of the same kind back off progressively (max 4x).
            st.until = time.monotonic() + cooldown * min(4, st.failures)
        return kind

    def reset(self, name: str | None = None) -> None:
        with self._lock:
            if name is None:
                self._state.clear()
            else:
                self._state.pop(self._key(name), None)

    def snapshot(self) -> dict[str, dict]:
        now = time.monotonic()
        with self._lock:
            return {
                name: {
                    "kind": st.kind,
                    "failures": st.failures,
                    "retry_in_seconds": round(max(0.0, st.until - now), 1),
                    "last_error": st.last_error,
                }
                for name, st in self._state.items()
            }


provider_health = ProviderHealth()
