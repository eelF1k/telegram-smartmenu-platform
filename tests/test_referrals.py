from bot.referrals import ReferralService, parse_start_referral


def test_parse_start_referral() -> None:
    assert parse_start_referral("/start ref123") == "ref123"
    assert parse_start_referral("/start") is None
    assert parse_start_referral("/start hello") is None


def test_referral_register_once() -> None:
    service = ReferralService()
    first = service.register_referral(invitee_id=200, payload="ref100")
    second = service.register_referral(invitee_id=200, payload="ref100")
    assert first is True
    assert second is False
    assert service.stats(100).invitee_count == 1
