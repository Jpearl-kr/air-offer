from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AppliedPromotionOut(BaseModel):
    id: int
    title: str
    discount: Decimal


class OfferOut(BaseModel):
    provider: str
    base_price: Decimal
    final_price: Decimal
    applied_promotions: list[AppliedPromotionOut]
    deep_link: str
    price_comparison_id: int


class FlightResultOut(BaseModel):
    flight_result_id: int
    airline: str | None
    flight_number: str | None
    depart_at: datetime | None
    arrive_at: datetime | None
    offers: list[OfferOut]
    best_offer_provider: str
    savings_vs_market_lowest: Decimal


class ComparisonResponse(BaseModel):
    search_id: UUID
    origin: str
    destination: str
    results: list[FlightResultOut]
    triggered_alert_ids: list[int] = []
