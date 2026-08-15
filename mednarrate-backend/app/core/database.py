from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

import sys
from sqlalchemy.pool import NullPool
import os

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required for production.")

_poolclass = NullPool if "pytest" in sys.modules else None

if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=_connect_args, poolclass=_poolclass)
else:
    if _poolclass is NullPool:
        engine = create_async_engine(
            settings.DATABASE_URL, 
            echo=False, 
            poolclass=_poolclass
        )
    else:
        engine = create_async_engine(
            settings.DATABASE_URL, 
            echo=False, 
            poolclass=_poolclass,
            pool_size=10, 
            max_overflow=20, 
            pool_timeout=30
        )

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def init_db():
    """Create all tables if they don't exist (dev/SQLite mode)."""
    import app.models  # noqa: F401 – ensures all models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
