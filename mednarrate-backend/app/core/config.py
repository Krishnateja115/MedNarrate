from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MedNarrate"
    ENVIRONMENT: str = "development"
    # Log every SQL statement with its parameters. Very noisy and prints data; leave off unless debugging.
    DB_ECHO: bool = False
    # Centralized API rate limiting (see app/core/rate_limit.py). Disable only in tests.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_SENSITIVE: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "30/minute"
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = None
    # Mobile medicine alerts are scheduled in the user's local timezone.
    # Server-side UTC reminders are opt-in for development only.
    SERVER_MEDICATION_PUSH_ENABLED: bool = False
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 25
    # Parser complexity budgets enforced at the upload boundary.
    MAX_PDF_PAGES: int = 60
    MAX_IMAGE_PIXELS: int = 40_000_000
    # Cap for JSON request bodies inspected by the prompt-injection middleware.
    MAX_JSON_BODY_BYTES: int = 2 * 1024 * 1024
    # SECURITY: ["*"] is acceptable for local development only.
    # For production, set this to an explicit list of allowed origins, e.g.:
    #   CORS_ORIGINS=["https://app.mednarrate.com"]
    # or via environment: CORS_ORIGINS='["https://app.mednarrate.com"]'
    CORS_ORIGINS: list[str] = ["*"]
    ADMIN_APP_ORIGIN: str = "http://localhost:3001"

    # LLM Provider Architecture Configuration
    # Vertex AI is the production-safe default. Local development can opt into
    # dev_gemini explicitly through .env without changing application code.
    PRIMARY_LLM_PROVIDER: str = "vertex_ai"
    PRIMARY_LLM_MODEL: str = "gemini-3.8-flash"

    MEDICAL_VERIFIER_PROVIDER: str = "ollama"
    MEDICAL_VERIFIER_MODEL: str = "medgemma-1.5:4b"

    STRUCTURED_MODEL_PROVIDER: str = "ollama"
    STRUCTURED_MODEL_MODEL: str = "qwen3:14b"

    TRANSLATION_MODEL_PROVIDER: str = "indictrans2"
    TRANSLATION_MODEL_URL: str | None = (
        "http://localhost:8001/translate"  # Placeholder for local IndicTrans2 service
    )

    # Structured translations include the report body and all UI labels.
    TRANSLATION_PROVIDER_ORDER: str = "vertex_ai,gemini,openai,mistral"
    TRANSLATION_MAX_OUTPUT_TOKENS: int = 16384
    # Translation requests must fail promptly when an upstream provider is
    # unavailable; the mobile client should never remain in a loading state.
    TRANSLATION_TIMEOUT_SECONDS: float = 45.0
    # Whole-request budget for one translation. Must stay below the mobile
    # app's receive timeout (240 s) and any reverse-proxy timeout.
    # Extra Gemini models to try (same key, separate quota) after the main one. Empty by default:
    # model names are retired often and a retired one only costs a failed call per translation.
    GEMINI_FALLBACK_MODELS: str = ""
    TRANSLATION_DEADLINE_SECONDS: float = 150.0
    # Report chunks translated in parallel (kept small to respect free-tier rate limits).
    TRANSLATION_CONCURRENCY: int = 3
    # Upper bound for one chat answer (all providers together); the app waits 90 s.
    CHAT_TIMEOUT_SECONDS: float = 75.0
    # Direct GEMINI_API_KEY use is refused when ENVIRONMENT=production unless this is true.
    ALLOW_GEMINI_API_KEY_IN_PRODUCTION: bool = False

    # Translation Fallback Orchestrator Models
    OPENAI_API_KEY: str | None = None
    # Extra OpenAI-compatible providers (all have a free tier; see .env.example).
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    # Second Groq model (same key, own daily limit) used as a separate fail-over entry.
    GROQ_QWEN_MODEL: str = "qwen/qwen3.8-27b"
    CEREBRAS_API_KEY: str | None = None
    CEREBRAS_MODEL: str = "llama-3.3-70b"
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "openrouter/free"
    GITHUB_MODELS_TOKEN: str | None = None
    GITHUB_MODELS_MODEL: str = "openai/gpt-4o-mini"
    # Voice input (speech-to-text for the chat box). Off by default; the app
    # hides the microphone unless this is true and GROQ_API_KEY is set.
    VOICE_INPUT_ENABLED: bool = False
    SPEECH_MODELS: str = "whisper-large-v3,whisper-large-v3-turbo"
    SPEECH_MAX_BYTES: int = 10 * 1024 * 1024
    SPEECH_MAX_SECONDS: int = 120
    SPEECH_TIMEOUT_SECONDS: float = 30.0
    SPEECH_RATE_LIMIT: str = "20/minute"
    OPENAI_TRANSLATION_MODEL: str = "gpt-6.1-sol"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_TRANSLATION_MODEL: str = "claude-sonnet-5-5"
    GEMINI_API_KEY: str | None = None
    GEMINI_TRANSLATION_MODEL: str = "gemini-3.8-flash"
    MISTRAL_API_KEY: str | None = None
    MISTRAL_TRANSLATION_MODEL: str = "mistral-large-2512"
    LOCAL_TRANSLATION_MODEL: str = "Qwen/Qwen2.5-1.5B-Instruct"
    LOCAL_TRANSLATION_TIMEOUT_SECONDS: float = 30.0

    ENABLE_LLM_FALLBACK: bool = True
    # Comma-separated provider order tried after the primary/fallback, e.g.
    # "gemini,openai,mistral,anthropic". Empty = vertex_ai,gemini,openai,anthropic,mistral
    # (only providers that actually have credentials are used).
    LLM_PROVIDER_CHAIN: str = ""

    # Vertex AI (Primary Production Provider - Fallback for Gemini)
    VERTEX_PROJECT_ID: str | None = None
    VERTEX_LOCATION: str = "us-central1"
    VERTEX_MODEL: str = "gemini-3.8-flash"
    VERTEX_TIMEOUT_SECONDS: float = 30.0

    # Ollama (Secondary Private/Local Provider)
    OLLAMA_URL: str | None = "http://localhost:11434"
    OLLAMA_MODEL: str = (
        "llama3:8b"  # Default fallback, should use specific models instead
    )

    # Development-Only Gemini Provider (GEMINI_API_KEY is declared above)
    EMBEDDING_PROVIDER: str | None = None  # defaults to PRIMARY_LLM_PROVIDER
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Privacy & Data Governance Boundary
    LLM_SEND_MODE: str = "deidentified"  # "deidentified" (default) or "full"

    # Token & Cost Guardrails
    MAX_INPUT_TOKENS: int = 8192
    MAX_OUTPUT_TOKENS: int = 2048
    LLM_TIMEOUT_SECONDS: float = 60.0
    # A provider that is not the last one in the chain may only hold a request
    # for this long before the next provider is tried (0 disables the cap).
    LLM_PROVIDER_TIMEOUT_SECONDS: float = 25.0
    # Gemini 3 "thinking" depth for report summaries (LOW is much faster than HIGH).
    ANALYSIS_THINKING_LEVEL: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"
    # Timing log: one JSON line per timed request/analysis in logs/timing.jsonl.
    TIMING_LOG_ENABLED: bool = True
    TIMING_SLOW_REQUEST_MS: int = 3000
    MAX_RAG_CHUNKS: int = 3
    MAX_RETRIES: int = 2
    # Startup must remain responsive when model weights are not already cached.
    NER_PREWARM_TIMEOUT_SECONDS: float = 10.0
    # "worker" persists processing jobs in PostgreSQL for a separate worker.
    # In-process FastAPI background tasks are suitable for development only.
    ANALYSIS_EXECUTION_MODE: Literal["background", "worker"] = "background"

    # Schema creation is intentionally opt-in. Deployments must apply Alembic
    # migrations before starting the API instead of silently creating a partial
    # schema with SQLAlchemy metadata.
    AUTO_CREATE_SCHEMA: bool = False
    EXPECTED_SCHEMA_REVISION: str = "110ba6a7df09"

    # Transactional e-mail (password reset). "log" only logs in development.
    EMAIL_PROVIDER: str = "log"  # "sendgrid" | "smtp" | "log"
    EMAIL_FROM: str = "no-reply@mednarrate.app"
    EMAIL_FROM_NAME: str = "MedNarrate"
    EMAIL_TIMEOUT_SECONDS: float = 10.0
    SENDGRID_API_KEY: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # Field-encryption keys (MFA secrets, stored AI keys). When unset the key is
    # derived from JWT_SECRET (legacy behaviour). Set ENCRYPTION_KEY to a
    # Fernet key to decouple it from JWT rotation; keep the old key in
    # ENCRYPTION_KEY_PREVIOUS (comma separated) while rotating.
    ENCRYPTION_KEY: str | None = None
    ENCRYPTION_KEY_PREVIOUS: str | None = None

    # Backward compatibility property aliases
    @property
    def GEMINI_MODEL_NAME(self) -> str:
        return self.GEMINI_MODEL

    def validate_production_security(self):
        """Enforces that loose CORS boundaries and default secrets are blocked in production."""
        if (self.ENVIRONMENT or "").lower() == "production":
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Wildcard CORS origins ('*') are prohibited in production environments. "
                    "Please configure CORS_ORIGINS to an explicit list of allowed origins."
                )
            jwt = self.JWT_SECRET or ""
            jwt_lower = jwt.lower().strip()
            unsafe_substrings = ["changeme", "secret", "default", "test", "mednarrate", "your-", "placeholder", "please_change"]
            if not jwt or len(jwt) < 16 or any(s in jwt_lower for s in unsafe_substrings):
                raise ValueError("JWT_SECRET must be configured with a strong, non-default value for production.")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("SQLite databases are not supported in production. Please configure a PostgreSQL DATABASE_URL.")
            if self.ANALYSIS_EXECUTION_MODE != "worker":
                raise ValueError(
                    "Production report analysis requires ANALYSIS_EXECUTION_MODE=worker."
                )
            if self.SERVER_MEDICATION_PUSH_ENABLED:
                raise ValueError(
                    "Server medication push requires per-user timezone scheduling; "
                    "use the mobile local-alert path in production."
                )

    # Storage Configuration
    STORAGE_BACKEND: str = "local"
    STORAGE_BUCKET_NAME: str | None = None
    GCS_PROJECT_ID: str | None = None
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_S3_BUCKET: str | None = None
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
settings.validate_production_security()
