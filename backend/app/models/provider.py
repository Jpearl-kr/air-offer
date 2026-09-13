from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    provider_type: Mapped[str] = mapped_column(String(20), nullable=False)
    affiliate_base_url: Mapped[str | None] = mapped_column(Text)
