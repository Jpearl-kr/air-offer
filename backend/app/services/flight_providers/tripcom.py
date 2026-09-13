"""Real Trip.com affiliate/partner integration — not wired up yet.

Requires Trip.com affiliate program approval and its search/deep-link API
contract. Once credentials are issued, implement `search()` and register
this class alongside the other providers in app/api/v1/search.py.
"""

from datetime import date

from app.services.flight_providers.base import FlightProvider, NormalizedFlight


class TripcomProvider(FlightProvider):
    name = "tripcom"
    provider_type = "ota"

    def __init__(self, affiliate_id: str) -> None:
        self.affiliate_id = affiliate_id

    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: date | None,
        adults: int,
        children: int,
    ) -> list[NormalizedFlight]:
        raise NotImplementedError("Trip.com affiliate API integration pending approval")
