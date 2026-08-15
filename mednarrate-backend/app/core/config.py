from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 25
    CORS_ORIGINS: list[str] = ["*"]
    GEMINI_API_KEY: str | None = None
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

    class Config:
        env_file = ".env"

settings = Settings()
