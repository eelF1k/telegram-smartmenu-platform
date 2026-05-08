from dataclasses import dataclass


def parse_start_referral(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip()
    if payload.startswith("ref") and len(payload) > 3:
        return payload
    return None


@dataclass
class ReferralStats:
    invited_by: int
    invitee_count: int


class ReferralService:
    def __init__(self) -> None:
        self._invitee_to_referrer: dict[int, int] = {}
        self._referrer_to_invitees: dict[int, set[int]] = {}

    def register_referral(self, invitee_id: int, payload: str) -> bool:
        if invitee_id in self._invitee_to_referrer:
            return False
        try:
            referrer_id = int(payload.removeprefix("ref"))
        except ValueError:
            return False
        if referrer_id == invitee_id:
            return False
        self._invitee_to_referrer[invitee_id] = referrer_id
        self._referrer_to_invitees.setdefault(referrer_id, set()).add(invitee_id)
        return True

    def stats(self, referrer_id: int) -> ReferralStats:
        invitees = self._referrer_to_invitees.get(referrer_id, set())
        return ReferralStats(invited_by=referrer_id, invitee_count=len(invitees))
