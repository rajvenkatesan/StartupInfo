from datetime import datetime
from typing import Any

from pydantic import BaseModel


class InvestorBase(BaseModel):
    investor_name: str
    description: str | None = None
    investor_type: str | None = None
    total_companies_invested: int | None = None
    total_amount_invested_usd: int | None = -1
    location: str | None = None
    website: str | None = None
    extra: dict[str, Any] | None = None


class InvestorCreate(InvestorBase):
    pass


class InvestorUpdate(BaseModel):
    description: str | None = None
    investor_type: str | None = None
    total_companies_invested: int | None = None
    total_amount_invested_usd: int | None = None
    location: str | None = None
    website: str | None = None
    extra: dict[str, Any] | None = None


class InvestorOut(InvestorBase):
    model_config = {"from_attributes": True}

    created_at: datetime
    updated_at: datetime
