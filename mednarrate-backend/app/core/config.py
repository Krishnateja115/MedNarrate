from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MedNarrate"
    ENVIRONMENT: str = "development"
    # Centralized API rate limiting (see app/core/rate_limit.py). Disable only in tests.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_SENSITIVE: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "30/minute"
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = None
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
    PRIMARY_LLM_PROVIDER: str = "gemini"
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
    TRANSLATION_MAX_OUTPUT_TOKENS: int = 16384
    TRANSLATION_TIMEOUT_SECONDS: float = 270.0  # Includes up to 75s of 503-retry backoff

    # Translation Fallback Orchestrator Models
    TRANSLATION_PROVIDER_ORDER: str = "gemini,groq_gpt,groq_qwen,deepseek,existing"
    GROQ_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    GROQ_GPT_TRANSLATION_MODEL: str = "openai/gpt-oss-120b"
    GROQ_QWEN_TRANSLATION_MODEL: str = "qwen/qwen3.8-27b"
    DEEPSEEK_TRANSLATION_MODEL: str = "deepseek-flash"

    ENABLE_LLM_FALLBACK: bool = True

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

    # Development-Only Gemini Provider
    GEMINI_API_KEY: str | None = None
    EMBEDDING_PROVIDER: str | None = None  # defaults to PRIMARY_LLM_PROVIDER
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Privacy & Data Governance Boundary
    LLM_SEND_MODE: str = "deidentified"  # "deidentified" (default) or "full"

    # Token & Cost Guardrails
    MAX_INPUT_TOKENS: int = 8192
    MAX_OUTPUT_TOKENS: int = 2048
    LLM_TIMEOUT_SECONDS: float = 60.0
    MAX_RAG_CHUNKS: int = 3
    MAX_RETRIES: int = 2
    # Startup must remain responsive when model weights are not already cached.
    NER_PREWARM_TIMEOUT_SECONDS: float = 10.0

    # Schema creation is intentionally opt-in. Deployments must apply Alembic
    # migrations before starting the API instead of silently creating a partial
    # schema with SQLAlchemy metadata.
    AUTO_CREATE_SCHEMA: bool = False
    EXPECTED_SCHEMA_REVISION: str = "110ba6a7df09"

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
