import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FlightResult(Base):
    __tablename__ = "flight_results"
    __table_args__ = (
        Index("idx_flight_results_search", "search_id"),
        Index("idx_flight_results_itinerary", "itinerary_hash"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flight_searches.id", ondelete="CASCADE")
    )
    airline_code: Mapped[str | None] = mapped_column(String(2), ForeignKey("airlines.code"))
    flight_number: Mapped[str | None] = mapped_column(String(10))
    depart_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    arrive_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    itinerary_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
