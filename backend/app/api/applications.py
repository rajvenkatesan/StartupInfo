import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job_application import JobApplication
from app.models.user import User
from app.schemas.job_application import ApplicationCreate, ApplicationOut, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    app_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(JobApplication).where(JobApplication.user_id == current_user.user_id)
    if app_status:
        q = q.where(JobApplication.status == app_status)
    q = q.order_by(JobApplication.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = JobApplication(**data.model_dump(), user_id=current_user.user_id)
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


@router.put("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: uuid.UUID,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(JobApplication).where(
            JobApplication.application_id == application_id,
            JobApplication.user_id == current_user.user_id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(app, field, value)
    await db.commit()
    await db.refresh(app)
    return app
