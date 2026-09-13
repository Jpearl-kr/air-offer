import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import FlightResult, FlightSearch
from app.schemas.search import SearchCreateRequest, SearchCreateResponse, SearchStatusResponse
from app.services.flight_providers.base import FlightProvider
from app.services.flight_providers.mock import MockOfficialProvider, MockSkyscannerProvider
from app.services.price_normalizer import persist_provider_offers

router = APIRouter(prefix="/search", tags=["search"])

# Swap these for the real SkyscannerProvider/TripcomProvider once partner
# credentials are approved (see app/services/flight_providers/skyscanner.py).
PROVIDERS: list[FlightProvider] = [MockSkyscannerProvider(), MockOfficialProvider()]


@router.post("", response_model=SearchCreateResponse, status_code=202)
async def create_search(
    payload: SearchCreateRequest, db: AsyncSession = Depends(get_db)
) -> SearchCreateResponse:
    search = FlightSearch(
        origin=payload.origin.upper(),
        destination=payload.destination.upper(),
        depart_date=payload.depart_date,
        return_date=payload.return_date,
        adults=payload.adults,
        children=payload.children,
    )
    db.add(search)
    await db.flush()

    provider_results = await asyncio.gather(
        *(
            provider.search(
                search.origin,
                search.destination,
                search.depart_date,
                search.return_date,
                search.adults,
                search.children,
            )
            for provider in PROVIDERS
        )
    )

    for provider, flights in zip(PROVIDERS, provider_results):
        await persist_provider_offers(db, search.id, provider.name, flights)

    await db.commit()
    return SearchCreateResponse(search_id=search.id)


@router.get("/{search_id}/status", response_model=SearchStatusResponse)
async def get_search_status(search_id: UUID, db: AsyncSession = Depends(get_db)) -> SearchStatusResponse:
    search = await db.get(FlightSearch, search_id)
    if search is None:
        raise HTTPException(status_code=404, detail="search not found")

    result_count = await db.scalar(
        select(func.count()).select_from(FlightResult).where(FlightResult.search_id == search_id)
    )
    return SearchStatusResponse(status="ready" if result_count else "pending")
