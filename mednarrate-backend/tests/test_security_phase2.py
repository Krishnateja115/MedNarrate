import os
import pytest
from app.core.config import Settings
from app.core.logging_helpers import redact_secrets

def production_settings(**overrides):
    values = {
        "ENVIRONMENT": "production",
        "JWT_SECRET": "a_very_secure_test_secret_12345!@#",
        "DATABASE_URL": "postgresql://user:pass@localhost/db",
        "CORS_ORIGINS": ["https://app.mednarrate.test"],
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)

def test_production_rejects_missing_jwt_secret():
    # If JWT_SECRET is missing or empty in production
    settings = production_settings(JWT_SECRET="")
    with pytest.raises(ValueError, match="JWT_SECRET must be configured with a strong, non-default value"):
        settings.validate_production_security()

def test_production_rejects_placeholder_jwt_secret():
    settings = production_settings(JWT_SECRET="changeme")
    with pytest.raises(ValueError, match="JWT_SECRET must be configured with a strong, non-default value"):
        settings.validate_production_security()
        
    settings = production_settings(JWT_SECRET="please_change_this_secret_in_production")
    with pytest.raises(ValueError, match="JWT_SECRET must be configured with a strong, non-default value"):
        settings.validate_production_security()

def test_production_rejects_wildcard_cors():
    settings = production_settings(CORS_ORIGINS=["*"])
    with pytest.raises(ValueError, match="Wildcard CORS origins"):
        settings.validate_production_security()

def test_development_startup_remains_supported():
    # Development shouldn't fail with weak JWT
    settings = Settings(ENVIRONMENT="development", JWT_SECRET="changeme", DATABASE_URL="sqlite+aiosqlite:///./test.db")
    # Should not raise
    settings.validate_production_security()

def test_logs_redact_credential_values():
    log_msg = "Error connecting to postgresql+asyncpg://user123:mypassword@localhost:5432/mednarrate"
    redacted = redact_secrets(log_msg)
    assert "user123:mypassword" not in redacted
    assert "[REDACTED_CREDENTIALS]" in redacted
    
    log_msg2 = "Loaded GEMINI_API_KEY: AIzaSyDr2UxVnv_U85AbhhY8XSHSIavUW0DC-sY"
    redacted2 = redact_secrets(log_msg2)
    assert "AIzaSyDr2UxVnv_U85AbhhY8XSHSIavUW0DC-sY" not in redacted2
    assert "[REDACTED]" in redacted2

@pytest.mark.asyncio
async def test_admin_ai_config_never_returns_decrypted_api_key(client, token_headers):
    from app.main import app
    from app.core.admin_auth import AdminContext, get_admin_context
    import uuid
    from app.models.user import User

    async def override_get_admin_context():
        mock_user = User(id=uuid.uuid4())
        return AdminContext(user=mock_user, permissions=["ai_config:read", "ai_config:manage"])
    
    app.dependency_overrides[get_admin_context] = override_get_admin_context
    
    try:
        response = await client.get("/api/v1/admin/ai-config", headers=token_headers)
        assert response.status_code == 200
        data = response.json()
        assert "api_key_status" in data
        assert "is_set" in data["api_key_status"]
        response_text = response.text
        assert "your_gemini_api_key_here" not in response_text
        assert "valid_test_key_12345" not in response_text
        assert "api_key" not in data
    finally:
        app.dependency_overrides.clear()


def test_environment_templates_contain_placeholders_only():
    with open("../mednarrate-backend/.env.example", "r") as f:
        content = f.read()
    assert "your_gemini_api_key_here" in content
    assert "change-me-to-a-long-random-string" in content

def test_frontend_config_contains_no_server_secret():
    with open("../mednarrate-admin/next.config.ts", "r") as f:
        content = f.read()
    assert "JWT_SECRET" not in content
    assert "DATABASE_URL" not in content
