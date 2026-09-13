import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    price_comparison_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("price_comparisons.id")
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
