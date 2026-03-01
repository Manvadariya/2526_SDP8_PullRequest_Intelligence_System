from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import os

# Default: SQLite (always works, no Docker needed)
# To use Postgres: set DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/pr_bot_db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

engine = create_async_engine(DATABASE_URL, echo=False)

import asyncio

async def init_db():
    retries = 5
    for i in range(retries):
        try:
            async with engine.begin() as conn:
                # This creates the tables if they don't exist
                await conn.run_sync(SQLModel.metadata.create_all)
            print("  [Database] Connected and initialized.")
            return
        except Exception as e:
            if i == retries - 1:
                print(f"❌ [Database] Failed to connect after {retries} attempts: {e}")
                raise e
            print(f"⚠️ [Database] Connection failed ({e}). Retrying in 2s... ({i+1}/{retries})")
            await asyncio.sleep(2)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session