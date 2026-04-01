from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.investment import InvestmentCreate, InvestmentOut, InvestmentUpdate
from app.services import investor as svc

router = APIRouter(tags=["investments"])


@router.get("/companies/{name}/investments", response_model=list[InvestmentOut])
async def list_investments(
    name: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await svc.list_investments_for_company(db, name.lower())


@router.post("/investments", response_model=InvestmentOut, status_code=201)
async def upsert_investment(
    data: InvestmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await svc.upsert_investment(db, data)


@router.put(
    "/investments/{company}/{investor}/{series}",
    response_model=InvestmentOut,
)
async def update_investment(
    company: str,
    investor: str,
    series: str,
    data: InvestmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    updated = await svc.update_investment(db, company.lower(), investor, series, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Investment not found")
    return updated
