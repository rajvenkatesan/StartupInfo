import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    company_name: str
    applied_date: date | None = None
    status: str = "wishlist"
    notes: str | None = None
    follow_up_date: date | None = None


class ApplicationUpdate(BaseModel):
    applied_date: date | None = None
    status: str | None = None
    notes: str | None = None
    follow_up_date: date | None = None


class ApplicationOut(BaseModel):
    model_config = {"from_attributes": True}

    application_id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    company_name: str
    applied_date: date | None
    status: str
    notes: str | None
    follow_up_date: date | None
    created_at: datetime
    updated_at: datetime
