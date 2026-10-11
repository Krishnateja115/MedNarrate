import uuid

from app.analysis_worker import advisory_key
from app.core.config import Settings


def test_advisory_key_is_stable_signed_bigint() -> None:
    report_id = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    assert advisory_key(report_id) == -1
    assert advisory_key(report_id) == advisory_key(report_id)


def test_production_requires_separate_analysis_worker() -> None:
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost/mednarrate",
        JWT_SECRET="8vWqY9N6uD5pA2hJ7rL4sK3tM1zX0bC8",
        CORS_ORIGINS=["https://app.example.com"],
        ANALYSIS_EXECUTION_MODE="background",
    )
    try:
        settings.validate_production_security()
    except ValueError as error:
        assert "ANALYSIS_EXECUTION_MODE=worker" in str(error)
    else:
        raise AssertionError("Production accepted in-process background analysis")
