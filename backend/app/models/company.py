from datetime import datetime, timezone

from sqlalchemy import ARRAY, BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    company_name: Mapped[str] = mapped_column(String(255), primary_key=True)
    # stub | discovering | ready | error
    status: Mapped[str] = mapped_column(String(20), default="stub", nullable=False)
    location: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    # public | private | acquired | defunct
    company_type: Mapped[str | None] = mapped_column(String(20))
    about: Mapped[str | None] = mapped_column(Text)
    vision: Mapped[str | None] = mapped_column(Text)
    mission: Mapped[str | None] = mapped_column(Text)
    founders: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    website: Mapped[str | None] = mapped_column(Text)
    company_url: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    related_urls: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    # enrichment fields populated by discovery
    founded_year: Mapped[int | None] = mapped_column(Integer)
    employee_count: Mapped[str | None] = mapped_column(String(50))
    headquarters: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    total_funding_usd: Mapped[int | None] = mapped_column(BigInteger)
    latest_series: Mapped[str | None] = mapped_column(String(30))
    products: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    extra: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    investments: Mapped[list["Investment"]] = relationship(  # noqa: F821
        back_populates="company", lazy="selectin"
    )
    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        back_populates="company", lazy="selectin"
    )
