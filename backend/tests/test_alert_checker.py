from datetime import date
from decimal import Decimal

from app.models import PriceAlert
from app.services.alert_checker import alert_matches


def make_alert(**overrides) -> PriceAlert:
    defaults = dict(
        id=1,
        user_id=None,
        origin="ICN",
        destination="CEB",
        depart_date=None,
        target_price=Decimal(1_000_000),
        active=True,
        triggered_at=None,
    )
    defaults.update(overrides)
    return PriceAlert(**defaults)


def test_matches_when_price_at_or_below_target():
    alert = make_alert(target_price=Decimal(1_000_000))
    assert alert_matches(alert, "ICN", "CEB", date(2026, 11, 17), Decimal(1_000_000))
    assert alert_matches(alert, "ICN", "CEB", date(2026, 11, 17), Decimal(900_000))
    assert not alert_matches(alert, "ICN", "CEB", date(2026, 11, 17), Decimal(1_000_001))


def test_ignores_inactive_alert():
    alert = make_alert(active=False)
    assert not alert_matches(alert, "ICN", "CEB", date(2026, 11, 17), Decimal(500_000))


def test_requires_matching_route():
    alert = make_alert(origin="ICN", destination="CEB")
    assert not alert_matches(alert, "ICN", "NRT", date(2026, 11, 17), Decimal(500_000))


def test_null_depart_date_matches_any_date():
    alert = make_alert(depart_date=None)
    assert alert_matches(alert, "ICN", "CEB", date(2026, 12, 25), Decimal(500_000))


def test_specific_depart_date_must_match():
    alert = make_alert(depart_date=date(2026, 11, 17))
    assert alert_matches(alert, "ICN", "CEB", date(2026, 11, 17), Decimal(500_000))
    assert not alert_matches(alert, "ICN", "CEB", date(2026, 12, 25), Decimal(500_000))
