from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProviderPrice(Base):
    __tablename__ = "provider_prices"
    __table_args__ = (Index("idx_provider_prices_result", "flight_result_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    flight_result_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("flight_results.id", ondelete="CASCADE")
    )
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("providers.id"))
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 0), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="KRW")
    deep_link: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
