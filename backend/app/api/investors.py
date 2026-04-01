from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.investor import InvestorCreate, InvestorOut, InvestorUpdate
from app.schemas.investment import InvestmentOut
from app.services import investor as svc

router = APIRouter(prefix="/investors", tags=["investors"])


@router.get("", response_model=list[InvestorOut])
async def list_investors(
    offset: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await svc.list_investors(db, offset=offset, limit=limit)


@router.get("/{name}", response_model=InvestorOut)
async def get_investor(
    name: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    investor = await svc.get_investor(db, name)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return investor


@router.post("", response_model=InvestorOut, status_code=status.HTTP_201_CREATED)
async def create_investor(
    data: InvestorCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if await svc.get_investor(db, data.investor_name):
        raise HTTPException(status_code=409, detail="Investor already exists")
    return await svc.create_investor(db, data)


@router.put("/{name}", response_model=InvestorOut)
async def update_investor(
    name: str,
    data: InvestorUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    updated = await svc.update_investor(db, name, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Investor not found")
    return updated
