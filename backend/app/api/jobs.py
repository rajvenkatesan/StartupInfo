import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate, JobOut, JobUpdate
from app.services.discovery.jobs import discover_jobs

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(
    company: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    active_only: bool = True,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Job)
    if company:
        q = q.where(Job.company_name == company.lower())
    if location:
        q = q.where(Job.location.ilike(f"%{location}%"))
    if job_type:
        q = q.where(Job.job_type == job_type)
    if active_only:
        q = q.where(Job.is_active.is_(True))
    q = q.offset(offset).limit(limit).order_by(Job.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("/companies/{name}/jobs/discover", status_code=202)
async def trigger_job_discovery(
    name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    background_tasks.add_task(discover_jobs, db, name.lower())
    return {"message": "Job discovery started", "company_name": name.lower()}


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    job = Job(**data.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.put("/jobs/{job_id}", response_model=JobOut)
async def update_job(
    job_id: uuid.UUID,
    data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(job, field, value)
    await db.commit()
    await db.refresh(job)
    return job
