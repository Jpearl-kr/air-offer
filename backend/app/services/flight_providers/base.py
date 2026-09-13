from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass
class NormalizedFlight:
    airline_code: str
    flight_number: str
    depart_at: datetime
    arrive_at: datetime
    base_price: Decimal
    currency: str
    deep_link: str


class FlightProvider(ABC):
    """Common interface every price source (meta-search, OTA, airline official site) implements."""

    name: str
    provider_type: str  # 'meta_search' | 'ota' | 'airline_official'

    @abstractmethod
    async def search(
        self,
        origin: str,
        destination: str,
        depart_date: date,
        return_date: date | None,
        adults: int,
        children: int,
    ) -> list[NormalizedFlight]:
        ...
