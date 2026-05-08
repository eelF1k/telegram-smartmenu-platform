from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import BotSettings

settings = BotSettings()
DATABASE_URL = (
    "postgresql+asyncpg://smartmenu:smartmenu@localhost:5432/smartmenu"
    if not hasattr(settings, "database_url")
    else settings.database_url
)

engine: AsyncEngine = create_async_engine(DATABASE_URL, future=True, echo=False)
SessionFactory = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
