import uuid
from datetime import datetime

from pydantic import BaseModel


class JobBase(BaseModel):
    company_name: str
    title: str
    location: str | None = None
    job_type: str | None = None
    url: str | None = None
    description: str | None = None
    source: str = "manual"


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: str | None = None
    location: str | None = None
    job_type: str | None = None
    url: str | None = None
    description: str | None = None
    is_active: bool | None = None


class JobOut(JobBase):
    model_config = {"from_attributes": True}

    job_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
