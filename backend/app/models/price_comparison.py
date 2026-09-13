import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PriceComparison(Base):
    __tablename__ = "price_comparisons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    search_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("flight_searches.id"))
    flight_result_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("flight_results.id"))
    provider_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("providers.id"))
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 0), nullable=False)
    applied_promotion_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, server_default="{}"
    )
    final_price: Mapped[Decimal] = mapped_column(Numeric(12, 0), nullable=False)
    is_best: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
