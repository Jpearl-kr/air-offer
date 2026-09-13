from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PromotionRule(Base):
    __tablename__ = "promotion_rules"
    __table_args__ = (Index("idx_promo_rules_promotion", "promotion_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(Integer, ForeignKey("promotions.id", ondelete="CASCADE"))
    discount_type: Mapped[str] = mapped_column(String(10), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 0))
    payment_method_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("payment_methods.id"))
    new_member_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    app_only: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    minimum_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 0))
    travel_start: Mapped[date | None] = mapped_column(Date)
    travel_end: Mapped[date | None] = mapped_column(Date)
    booking_start: Mapped[date | None] = mapped_column(Date)
    booking_end: Mapped[date | None] = mapped_column(Date)
    applicable_routes: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    coupon_code: Mapped[str | None] = mapped_column(String(50))
    stackable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    stack_group: Mapped[str | None] = mapped_column(String(50))
