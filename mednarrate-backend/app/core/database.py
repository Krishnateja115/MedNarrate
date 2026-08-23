from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import sys
from sqlalchemy.pool import NullPool

# Determine if we're in a test environment
is_test = "pytest" in sys.modules
pool_class = NullPool if is_test else None

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine_kwargs = {
    "echo": settings.ENVIRONMENT == "development",
    "pool_pre_ping": True,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 5 if not is_test else 0,
        "max_overflow": 10 if not is_test else 0,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

if pool_class:
    engine_kwargs["poolclass"] = pool_class

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def init_db():
    """Create all tables if they don't exist (dev mode)."""
    import app.models  # noqa: F401 – ensures all models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
