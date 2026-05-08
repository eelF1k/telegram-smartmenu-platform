import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select

from api.db import SessionFactory
from api.models import NotificationOutbox


@dataclass
class OutboxRecord:
    dedupe_key: str
    channel: str
    payload: dict
    delivered: bool
    created_at: str


class AsyncOutboxStoreProtocol(Protocol):
    async def exists(self, dedupe_key: str) -> bool: ...

    async def save(
        self,
        dedupe_key: str,
        channel: str,
        payload: dict,
        delivered: bool,
    ) -> OutboxRecord: ...

    async def list_records(self) -> list[OutboxRecord]: ...


class InMemoryOutboxStore:
    def __init__(self) -> None:
        self._records: dict[str, OutboxRecord] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=UTC).isoformat()

    def reset(self) -> None:
        self._records = {}

    async def exists(self, dedupe_key: str) -> bool:
        return dedupe_key in self._records

    async def save(
        self,
        dedupe_key: str,
        channel: str,
        payload: dict,
        delivered: bool,
    ) -> OutboxRecord:
        record = OutboxRecord(
            dedupe_key=dedupe_key,
            channel=channel,
            payload=payload,
            delivered=delivered,
            created_at=self._now(),
        )
        self._records[dedupe_key] = record
        return record

    async def list_records(self) -> list[OutboxRecord]:
        return list(self._records.values())


class SqlAlchemyOutboxStore:
    async def exists(self, dedupe_key: str) -> bool:
        async with SessionFactory() as session:
            stmt = select(NotificationOutbox.id).where(NotificationOutbox.dedupe_key == dedupe_key)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def save(
        self,
        dedupe_key: str,
        channel: str,
        payload: dict,
        delivered: bool,
    ) -> OutboxRecord:
        async with SessionFactory() as session:
            model = NotificationOutbox(
                dedupe_key=dedupe_key,
                channel=channel,
                payload_json=json.dumps(payload),
                delivered=1 if delivered else 0,
            )
            session.add(model)
            await session.commit()
            return OutboxRecord(
                dedupe_key=dedupe_key,
                channel=channel,
                payload=payload,
                delivered=delivered,
                created_at=datetime.now(tz=UTC).isoformat(),
            )

    async def list_records(self) -> list[OutboxRecord]:
        async with SessionFactory() as session:
            stmt = select(NotificationOutbox).order_by(NotificationOutbox.id.desc()).limit(100)
            result = await session.execute(stmt)
            records: list[OutboxRecord] = []
            for row in result.scalars().all():
                records.append(
                    OutboxRecord(
                        dedupe_key=row.dedupe_key,
                        channel=row.channel,
                        payload=json.loads(row.payload_json),
                        delivered=bool(row.delivered),
                        created_at=row.created_at.isoformat(),
                    )
                )
            return records


class FallbackOutboxStore:
    def __init__(self, primary: AsyncOutboxStoreProtocol, fallback: InMemoryOutboxStore) -> None:
        self._primary = primary
        self._fallback = fallback

    def reset(self) -> None:
        self._fallback.reset()

    async def exists(self, dedupe_key: str) -> bool:
        try:
            return await self._primary.exists(dedupe_key)
        except Exception:
            return await self._fallback.exists(dedupe_key)

    async def save(
        self,
        dedupe_key: str,
        channel: str,
        payload: dict,
        delivered: bool,
    ) -> OutboxRecord:
        try:
            return await self._primary.save(dedupe_key, channel, payload, delivered)
        except Exception:
            return await self._fallback.save(dedupe_key, channel, payload, delivered)

    async def list_records(self) -> list[OutboxRecord]:
        try:
            records = await self._primary.list_records()
            if records:
                return records
        except Exception:
            pass
        return await self._fallback.list_records()


outbox_store = FallbackOutboxStore(primary=SqlAlchemyOutboxStore(), fallback=InMemoryOutboxStore())
