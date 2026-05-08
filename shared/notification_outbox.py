from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class OutboxRecord:
    dedupe_key: str
    channel: str
    payload: dict
    delivered: bool
    created_at: str


class InMemoryNotificationOutbox:
    def __init__(self) -> None:
        self._records: dict[str, OutboxRecord] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=UTC).isoformat()

    def reset(self) -> None:
        self._records = {}

    def exists(self, dedupe_key: str) -> bool:
        return dedupe_key in self._records

    def save(self, dedupe_key: str, channel: str, payload: dict, delivered: bool) -> OutboxRecord:
        record = OutboxRecord(
            dedupe_key=dedupe_key,
            channel=channel,
            payload=payload,
            delivered=delivered,
            created_at=self._now(),
        )
        self._records[dedupe_key] = record
        return record

    def list_records(self) -> list[OutboxRecord]:
        return list(self._records.values())


notification_outbox = InMemoryNotificationOutbox()
