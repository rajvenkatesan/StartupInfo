from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Investor(Base):
    __tablename__ = "investors"

    investor_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text)
    # individual | vc_firm | corporate | angel | accelerator
    investor_type: Mapped[str | None] = mapped_column(String(30))
    total_companies_invested: Mapped[int | None] = mapped_column(Integer)
    total_amount_invested_usd: Mapped[int | None] = mapped_column(BigInteger, default=-1)
    location: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    extra: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    investments: Mapped[list["Investment"]] = relationship(  # noqa: F821
        back_populates="investor", lazy="selectin"
    )
