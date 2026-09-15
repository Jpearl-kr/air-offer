from datetime import datetime, timezone
from decimal import Decimal

from app.schemas.alert import AlertOut


def test_target_price_avoids_scientific_notation_from_asyncpg_decimal():
    """asyncpg can decode a scale-0 NUMERIC like 1200000 as Decimal('1.2E+6')."""
    alert = AlertOut(
        id=1,
        origin="ICN",
        destination="CEB",
        depart_date=None,
        target_price=Decimal("1.2E+6"),
        active=True,
        created_at=datetime.now(timezone.utc),
        triggered_at=None,
    )
    assert alert.target_price == Decimal("1200000.00")
    assert "E" not in str(alert.target_price)
