"""Checks whether a newly-computed best price should trigger a user's price alert.

`alert_matches` is pure (no DB) so it's cheap to unit test; the async wrapper
does the DB fetch + mutation and is called from the comparisons endpoint right
after a search's offers are priced.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PriceAlert


def alert_matches(
    alert: PriceAlert, origin: str, destination: str, depart_date: date, best_final_price: Decimal
) -> bool:
    if not alert.active:
        return False
    if alert.origin != origin or alert.destination != destination:
        return False
    if alert.depart_date is not None and alert.depart_date != depart_date:
        return False
    return best_final_price <= alert.target_price


async def check_and_trigger_alerts(
    db: AsyncSession, origin: str, destination: str, depart_date: date, best_final_price: Decimal
) -> list[PriceAlert]:
    """Marks matching active alerts as triggered. Does not commit — caller controls
    the transaction boundary."""
    candidates = (
        await db.execute(
            select(PriceAlert).where(
                PriceAlert.origin == origin,
                PriceAlert.destination == destination,
                PriceAlert.active.is_(True),
            )
        )
    ).scalars().all()

    triggered = [
        alert
        for alert in candidates
        if alert_matches(alert, origin, destination, depart_date, best_final_price)
    ]
    now = datetime.now(timezone.utc)
    for alert in triggered:
        alert.active = False
        alert.triggered_at = now
    return triggered
