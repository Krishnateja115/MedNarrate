from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

import sys
from sqlalchemy.pool import NullPool

# SQLite needs check_same_thread=False; PostgreSQL doesn't need connect_args
_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

_poolclass = NullPool if "pytest" in sys.modules else None

engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args=_connect_args, poolclass=_poolclass)
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
