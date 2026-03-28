from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import os
import logging
import asyncio

logger = logging.getLogger("agenticpr.database")

# ─── Database URL Configuration ─────────────────────────────────
# Production: Postgres (required for concurrent access, UNIQUE constraints, scaling)
# Development: SQLite fallback (set DEV_MODE=true to use SQLite)
#
# Examples:
#   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agenticpr_db
#   DATABASE_URL=sqlite+aiosqlite:///./database.db

DEV_MODE = os.getenv("DEV_MODE", "").lower() in ("true", "1", "yes")
PRODUCTION = os.getenv("PRODUCTION", "").lower() in ("true", "1", "yes")

# Default to Postgres in production, SQLite in dev
if DEV_MODE:
    _default_url = "sqlite+aiosqlite:///./database.db"
else:
    _default_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://prbot:prbot@localhost:5432/pr_bot_db"
    )

DATABASE_URL = os.getenv("DATABASE_URL", _default_url)

# Warn if using SQLite in production
if PRODUCTION and "sqlite" in DATABASE_URL:
    logger.warning("⚠ SQLite detected in production — this is NOT safe for concurrent access!")
    logger.warning("  Set DATABASE_URL to a Postgres connection string.")

engine = create_async_engine(DATABASE_URL, echo=False)


async def init_db():
    """Initialize database tables with retry logic."""
    retries = 5
    for i in range(retries):
        try:
            async with engine.begin() as conn:
                # This creates tables if they don't exist
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info(f"Database connected and initialized ({DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'local'})")
            return
        except Exception as e:
            if i == retries - 1:
                logger.error(f"Database connection failed after {retries} attempts: {e}")
                raise e
            logger.warning(f"Database connection failed ({e}). Retrying in 2s... ({i+1}/{retries})")
            await asyncio.sleep(2)


async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session