import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Determine if we're in a test environment
is_test = "pytest" in sys.modules
pool_class = NullPool if is_test else None

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine_kwargs = {
    "echo": settings.ENVIRONMENT == "development",
    "pool_pre_ping": True,
}

if not is_sqlite and not is_test:
    # QueuePool tuning; NullPool (used under pytest) rejects these arguments.
    engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        }
    )

if pool_class:
    engine_kwargs["poolclass"] = pool_class

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def init_db():
    """Verify the migrated schema and ensure useful starter help content exists.

    Metadata-driven table creation is available only when explicitly enabled
    for a disposable local database. Normal startup fails fast when migrations
    are missing or the database is at the wrong revision.
    """
    import app.models  # noqa: F401 – ensures all models are registered
    from app.services.help_center_seed import seed_help_center_if_empty

    async with engine.begin() as conn:
        if settings.AUTO_CREATE_SCHEMA:
            await conn.run_sync(Base.metadata.create_all)
        else:
            try:
                revision = (
                    await conn.execute(text("SELECT version_num FROM alembic_version"))
                ).scalar_one_or_none()
            except Exception as exc:
                raise RuntimeError(
                    "Database migrations are not available; run 'alembic upgrade head' "
                    "before starting MedNarrate."
                ) from exc
            if revision != settings.EXPECTED_SCHEMA_REVISION:
                raise RuntimeError(
                    "Database schema revision mismatch: "
                    f"expected {settings.EXPECTED_SCHEMA_REVISION}, got {revision!r}. "
                    "Run 'alembic upgrade head' before starting MedNarrate."
                )

    async with AsyncSessionLocal() as session:
        await seed_help_center_if_empty(session)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_schema_revision() -> str | None:
    """Return the Alembic revision without exposing connection details."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT version_num FROM alembic_version"))
        return result.scalar_one_or_none()
