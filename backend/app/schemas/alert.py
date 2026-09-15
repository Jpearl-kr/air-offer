from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class AlertCreateRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    depart_date: date | None = None
    target_price: Decimal
    email: EmailStr


class AlertOut(BaseModel):
    id: int
    origin: str
    destination: str
    depart_date: date | None
    target_price: Decimal
    active: bool
    created_at: datetime
    triggered_at: datetime | None

    model_config = {"from_attributes": True}

    @field_validator("target_price", mode="before")
    @classmethod
    def _normalize_money(cls, value: Decimal) -> Decimal:
        # asyncpg can decode a scale-0 NUMERIC like 1200000 as Decimal('1.2E+6');
        # quantizing forces fixed-point formatting in the API response.
        return Decimal(value).quantize(Decimal("0.01"))
