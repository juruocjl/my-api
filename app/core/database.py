from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def ensure_sqlite_compatibility() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    async with engine.begin() as conn:
        info_rows = (await conn.execute(text("PRAGMA table_info(api_keys)"))).fetchall()
        columns = {row[1] for row in info_rows}

        if "balance" not in columns:
            await conn.execute(text("ALTER TABLE api_keys ADD COLUMN balance FLOAT DEFAULT 0"))
        if "currency" not in columns:
            await conn.execute(text("ALTER TABLE api_keys ADD COLUMN currency VARCHAR(16) DEFAULT 'CNY'"))
