import hashlib
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FlightResult, Provider, ProviderPrice
from app.services.flight_providers.base import NormalizedFlight


def compute_itinerary_hash(
    airline_code: str, flight_number: str, depart_at: datetime, arrive_at: datetime
) -> str:
    raw = f"{airline_code}|{flight_number}|{depart_at.isoformat()}|{arrive_at.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def persist_provider_offers(
    db: AsyncSession, search_id: UUID, provider_name: str, flights: list[NormalizedFlight]
) -> None:
    """Match each offer to an existing flight_result (by itinerary hash) or create one, then
    record the provider's price. Does not commit — caller controls the transaction boundary."""
    provider = await db.scalar(select(Provider).where(Provider.name == provider_name))
    if provider is None:
        raise ValueError(f"Unknown provider '{provider_name}' — seed a row in providers first")

    for flight in flights:
        itinerary_hash = compute_itinerary_hash(
            flight.airline_code, flight.flight_number, flight.depart_at, flight.arrive_at
        )

        flight_result = await db.scalar(
            select(FlightResult).where(
                FlightResult.search_id == search_id,
                FlightResult.itinerary_hash == itinerary_hash,
            )
        )
        if flight_result is None:
            flight_result = FlightResult(
                search_id=search_id,
                airline_code=flight.airline_code,
                flight_number=flight.flight_number,
                depart_at=flight.depart_at,
                arrive_at=flight.arrive_at,
                itinerary_hash=itinerary_hash,
            )
            db.add(flight_result)
            await db.flush()

        db.add(
            ProviderPrice(
                flight_result_id=flight_result.id,
                provider_id=provider.id,
                base_price=flight.base_price,
                currency=flight.currency,
                deep_link=flight.deep_link,
            )
        )
