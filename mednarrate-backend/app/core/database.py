import sys

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

if not is_sqlite:
    engine_kwargs.update(
        {
            "pool_size": 5 if not is_test else 0,
            "max_overflow": 10 if not is_test else 0,
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
    """Create development tables and ensure useful starter help content exists."""
    import app.models  # noqa: F401 – ensures all models are registered
    from app.services.help_center_seed import seed_help_center_if_empty

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_help_center_if_empty(session)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
