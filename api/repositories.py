from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User, Venue


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: int, username: str | None, locale: str = "uk") -> User:
        user = User(telegram_id=telegram_id, username=username, locale=locale)
        self._session.add(user)
        await self._session.flush()
        return user


class VenueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_venues(self) -> list[Venue]:
        result = await self._session.execute(select(Venue).order_by(Venue.id.asc()))
        return list(result.scalars().all())
