from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    click_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("clicks.id"))
    provider_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("providers.id"))
    commission_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 0))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
