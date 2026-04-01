from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CompanyBase(BaseModel):
    company_name: str
    company_url: str
    location: str | None = None
    description: str | None = None
    company_type: str | None = None
    about: str | None = None
    vision: str | None = None
    mission: str | None = None
    founders: list[str] | None = None
    website: str | None = None
    related_urls: list[str] | None = None
    linkedin_url: str | None = None
    # enrichment fields
    founded_year: int | None = None
    employee_count: str | None = None
    headquarters: str | None = None
    industry: str | None = None
    total_funding_usd: int | None = None
    latest_series: str | None = None
    products: list[str] | None = None
    extra: dict[str, Any] | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    company_url: str | None = None
    location: str | None = None
    description: str | None = None
    company_type: str | None = None
    about: str | None = None
    vision: str | None = None
    mission: str | None = None
    founders: list[str] | None = None
    website: str | None = None
    related_urls: list[str] | None = None
    linkedin_url: str | None = None
    # enrichment fields
    founded_year: int | None = None
    employee_count: str | None = None
    headquarters: str | None = None
    industry: str | None = None
    total_funding_usd: int | None = None
    latest_series: str | None = None
    products: list[str] | None = None
    extra: dict[str, Any] | None = None


class CompanyOut(CompanyBase):
    model_config = {"from_attributes": True}

    status: str
    created_at: datetime
    updated_at: datetime


class DiscoverResponse(BaseModel):
    message: str
    company_name: str
    status: str
