"""Deterministic fake providers used until real partner API credentials are approved.

Both mock providers return the same flight schedule for a given
(origin, destination, depart_date) so they normalize into a single
flight_result with two competing provider_prices, exactly like real
meta-search + airline-official offers would.
"""

import hashlib
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from app.services.flight_providers.base import FlightProvider, NormalizedFlight

KST = timezone(timedelta(hours=9))


def _seed(origin: str, destination: str, depart_date: date) -> int:
    raw = f"{origin}-{destination}-{depart_date.isoformat()}"
    return int(hashlib.sha256(raw.encode()).hexdigest(), 16)


def _shared_itinerary(
    origin: str, destination: str, depart_date: date
) -> tuple[str, str, datetime, datetime]:
    seed = _seed(origin, destination, depart_date)
    airline_code = "KE"
    flight_number = f"KE{600 + seed % 300}"
    depart_at = datetime.combine(depart_date, time(hour=6 + seed % 12, minute=seed % 60), tzinfo=KST)
    arrive_at = depart_at + timedelta(hours=3, minutes=25 + seed % 90)
    return airline_code, flight_number, depart_at, arrive_at


class MockSkyscannerProvider(FlightProvider):
    """Stand-in for the real Skyscanner Live Prices API pending partner approval."""

    name = "skyscanner"
    provider_type = "meta_search"

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: date | None,
        adults: int,
        children: int,
    ) -> list[NormalizedFlight]:
        airline_code, flight_number, depart_at, arrive_at = _shared_itinerary(
            origin, destination, depart_date
        )
        seed = _seed(origin, destination, depart_date)
        base_price = Decimal(1_050_000 + seed % 150_000)
        return [
            NormalizedFlight(
                airline_code=airline_code,
                flight_number=flight_number,
                depart_at=depart_at,
                arrive_at=arrive_at,
                base_price=base_price,
                currency="KRW",
                deep_link=f"https://www.skyscanner.co.kr/transport/flights/{origin.lower()}/{destination.lower()}/",
            )
        ]


class MockOfficialProvider(FlightProvider):
    """Stand-in for an airline's official-site price feed (not yet automated)."""

    name = "ke_official"
    provider_type = "airline_official"

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: date | None,
        adults: int,
        children: int,
    ) -> list[NormalizedFlight]:
        airline_code, flight_number, depart_at, arrive_at = _shared_itinerary(
            origin, destination, depart_date
        )
        seed = _seed(origin, destination, depart_date)
        base_price = Decimal(1_120_000 + seed % 150_000)
        return [
            NormalizedFlight(
                airline_code=airline_code,
                flight_number=flight_number,
                depart_at=depart_at,
                arrive_at=arrive_at,
                base_price=base_price,
                currency="KRW",
                deep_link="https://www.koreanair.com/booking",
            )
        ]
