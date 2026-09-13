"""Real Skyscanner Flights Live Prices integration — not wired up yet.

Requires an approved Partner API key (create/poll flow, plus a separate
itinerary refresh call for final-price accuracy). Once credentials are
issued, implement `search()` and swap `MockSkyscannerProvider` for this
class in app/api/v1/search.py.
"""

from datetime import date

from app.services.flight_providers.base import FlightProvider, NormalizedFlight


class SkyscannerProvider(FlightProvider):
    name = "skyscanner"
    provider_type = "meta_search"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: date | None,
        adults: int,
        children: int,
    ) -> list[NormalizedFlight]:
        raise NotImplementedError(
            "Skyscanner Partner API integration pending credential approval"
        )
