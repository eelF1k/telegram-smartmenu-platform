from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class Reservation:
    reservation_id: int
    user_id: int
    venue: str
    datetime_text: str
    status: str
    created_at: str


@dataclass
class OrderRecord:
    order_id: int
    user_id: int
    total: int
    status: str
    created_at: str


class AdminStore:
    def __init__(self) -> None:
        self._reservations: list[Reservation] = []
        self._orders: list[OrderRecord] = []
        self._next_reservation_id = 1
        self._next_order_id = 1

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=UTC).isoformat()

    def create_reservation(self, user_id: int, venue: str, datetime_text: str) -> Reservation:
        reservation = Reservation(
            reservation_id=self._next_reservation_id,
            user_id=user_id,
            venue=venue,
            datetime_text=datetime_text,
            status="pending",
            created_at=self._now(),
        )
        self._next_reservation_id += 1
        self._reservations.append(reservation)
        return reservation

    def list_reservations(self) -> list[Reservation]:
        return self._reservations

    def update_reservation_status(self, reservation_id: int, status: str) -> Reservation | None:
        for reservation in self._reservations:
            if reservation.reservation_id == reservation_id:
                reservation.status = status
                return reservation
        return None

    def create_order(self, user_id: int, total: int) -> OrderRecord:
        order = OrderRecord(
            order_id=self._next_order_id,
            user_id=user_id,
            total=total,
            status="created",
            created_at=self._now(),
        )
        self._next_order_id += 1
        self._orders.append(order)
        return order

    def list_orders(self) -> list[OrderRecord]:
        return self._orders

    def update_order_status(self, order_id: int, status: str) -> OrderRecord | None:
        for order in self._orders:
            if order.order_id == order_id:
                order.status = status
                return order
        return None


admin_store = AdminStore()
