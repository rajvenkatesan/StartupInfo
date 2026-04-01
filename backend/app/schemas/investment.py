from datetime import datetime

from pydantic import BaseModel


class InvestmentBase(BaseModel):
    company_name: str
    investor_name: str
    series_name: str
    amount_invested_usd: int | None = -1
    investor_role: str | None = None
    additional_comments: str | None = None


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    amount_invested_usd: int | None = None
    investor_role: str | None = None
    additional_comments: str | None = None


class InvestmentOut(InvestmentBase):
    model_config = {"from_attributes": True}

    created_at: datetime
    updated_at: datetime
