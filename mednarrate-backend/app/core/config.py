from pydantic_settings import BaseSettings
from pydantic import model_validator

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str | None = None
    SECRET_KEY: str | None = None
    SENTRY_DSN: str | None = None
    SENDGRID_API_KEY: str | None = None
    SENDGRID_FROM_EMAIL: str = "noreply@mednarrate.com"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MedNarrate"
    ENVIRONMENT: str = "development"
    FIREBASE_SERVICE_ACCOUNT_JSON: str | None = None
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 25
    CORS_ORIGINS: list[str] = ["*"]
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_URL: str | None = None
    
    # Storage Configuration
    STORAGE_BACKEND: str = "local"
    STORAGE_BUCKET_NAME: str | None = None
    GCS_PROJECT_ID: str | None = None
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_S3_BUCKET: str | None = None
    AWS_REGION: str = "us-east-1"

    @model_validator(mode="before")
    @classmethod
    def setup_jwt_secret(cls, values: dict):
        if not values.get("JWT_SECRET") and values.get("SECRET_KEY"):
            values["JWT_SECRET"] = values["SECRET_KEY"]
        elif values.get("JWT_SECRET") and not values.get("SECRET_KEY"):
            values["SECRET_KEY"] = values["JWT_SECRET"]
        return values

    class Config:
        env_file = ".env"

settings = Settings()
