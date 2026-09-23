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
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = None
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 25
    # SECURITY: ["*"] is acceptable for local development only.
    # For production, set this to an explicit list of allowed origins, e.g.:
    #   CORS_ORIGINS=["https://app.mednarrate.com"]
    # or via environment: CORS_ORIGINS='["https://app.mednarrate.com"]'
    CORS_ORIGINS: list[str] = ["*"]

    # LLM Provider Architecture Configuration
    PRIMARY_LLM_PROVIDER: str = "gemini" 
    PRIMARY_LLM_MODEL: str = "gemini-3.8-flash"
    
    MEDICAL_VERIFIER_PROVIDER: str = "ollama"
    MEDICAL_VERIFIER_MODEL: str = "medgemma-1.5:4b"
    
    STRUCTURED_MODEL_PROVIDER: str = "ollama"
    STRUCTURED_MODEL_MODEL: str = "qwen3:14b"
    
    TRANSLATION_MODEL_PROVIDER: str = "indictrans2"
    TRANSLATION_MODEL_URL: str | None = "http://localhost:8001/translate" # Placeholder for local IndicTrans2 service

    ENABLE_LLM_FALLBACK: bool = True
    
    # Vertex AI (Primary Production Provider - Fallback for Gemini)
    VERTEX_PROJECT_ID: str | None = None
    VERTEX_LOCATION: str = "us-central1"
    VERTEX_MODEL: str = "gemini-1.5-flash"
    VERTEX_TIMEOUT_SECONDS: float = 30.0

    # Ollama (Secondary Private/Local Provider)
    OLLAMA_URL: str | None = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:8b" # Default fallback, should use specific models instead

    # Development-Only Gemini Provider
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Privacy & Data Governance Boundary
    LLM_SEND_MODE: str = "deidentified"  # "deidentified" (default) or "full"

    # Token & Cost Guardrails
    MAX_INPUT_TOKENS: int = 8192
    MAX_OUTPUT_TOKENS: int = 2048
    LLM_TIMEOUT_SECONDS: float = 60.0
    MAX_RAG_CHUNKS: int = 3
    MAX_RETRIES: int = 2

    # Backward compatibility property aliases
    @property
    def GEMINI_MODEL_NAME(self) -> str:
        return self.GEMINI_MODEL

    def validate_production_security(self):
        """Enforces that loose CORS boundaries are blocked in production."""
        if (self.ENVIRONMENT or "").lower() == "production":
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Wildcard CORS origins ('*') are prohibited in production environments. "
                    "Please configure CORS_ORIGINS to an explicit list of allowed origins."
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

