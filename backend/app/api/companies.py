from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate, DiscoverResponse
from app.services import company as svc
from app.services.discovery.company import discover_company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
async def list_companies(
    status: str | None = None,
    company_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await svc.list_companies(db, status=status, company_type=company_type,
                                    offset=offset, limit=limit)


@router.get("/{name}", response_model=CompanyOut)
async def get_company(
    name: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    company = await svc.get_company(db, name.lower())
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data.company_name = data.company_name.strip().lower()
    if await svc.get_company(db, data.company_name):
        raise HTTPException(status_code=409, detail="Company already exists")
    return await svc.create_company(db, data)


@router.put("/{name}", response_model=CompanyOut)
async def update_company(
    name: str,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    updated = await svc.update_company(db, name.lower(), data)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found")
    return updated


@router.post("/{name}/discover", response_model=DiscoverResponse)
async def trigger_discover(
    name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    name = name.strip().lower()
    company = await svc.get_company(db, name)
    if not company:
        # Create stub so the client can poll status
        await svc.upsert_company(db, {"company_name": name, "status": "stub"})
    background_tasks.add_task(discover_company, db, name)
    return DiscoverResponse(
        message="Discovery started", company_name=name, status="discovering"
    )
