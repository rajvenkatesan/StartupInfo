from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Investment(Base):
    __tablename__ = "investments"

    company_name: Mapped[str] = mapped_column(
        String(255), ForeignKey("companies.company_name", ondelete="CASCADE"), primary_key=True
    )
    investor_name: Mapped[str] = mapped_column(
        String(255), ForeignKey("investors.investor_name", ondelete="CASCADE"), primary_key=True
    )
    series_name: Mapped[str] = mapped_column(String(50), primary_key=True)

    amount_invested_usd: Mapped[int | None] = mapped_column(BigInteger, default=-1)
    # lead | participant | angel
    investor_role: Mapped[str | None] = mapped_column(String(30))
    additional_comments: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    company: Mapped["Company"] = relationship(back_populates="investments")  # noqa: F821
    investor: Mapped["Investor"] = relationship(back_populates="investments")  # noqa: F821
