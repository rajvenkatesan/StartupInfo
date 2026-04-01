from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investor import Investor
from app.models.investment import Investment
from app.schemas.investor import InvestorCreate, InvestorUpdate
from app.schemas.investment import InvestmentCreate, InvestmentUpdate


# ── Investor CRUD ─────────────────────────────────────────────────────────────

async def get_investor(db: AsyncSession, name: str) -> Investor | None:
    result = await db.execute(select(Investor).where(Investor.investor_name == name))
    return result.scalar_one_or_none()


async def list_investors(
    db: AsyncSession, offset: int = 0, limit: int = 50
) -> list[Investor]:
    result = await db.execute(
        select(Investor).offset(offset).limit(limit).order_by(Investor.investor_name)
    )
    return list(result.scalars().all())


async def create_investor(db: AsyncSession, data: InvestorCreate) -> Investor:
    investor = Investor(**data.model_dump())
    db.add(investor)
    await db.commit()
    await db.refresh(investor)
    return investor


async def update_investor(db: AsyncSession, name: str, data: InvestorUpdate) -> Investor | None:
    investor = await get_investor(db, name)
    if not investor:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(investor, field, value)
    await db.commit()
    await db.refresh(investor)
    return investor


async def upsert_investor(db: AsyncSession, data: dict) -> Investor:
    name = data.get("investor_name", "").strip()
    existing = await get_investor(db, name)
    if existing:
        for k, v in data.items():
            if v is not None:
                setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        return existing
    investor = Investor(**data)
    db.add(investor)
    await db.commit()
    await db.refresh(investor)
    return investor


# ── Investment CRUD ───────────────────────────────────────────────────────────

async def get_investment(
    db: AsyncSession, company: str, investor: str, series: str
) -> Investment | None:
    result = await db.execute(
        select(Investment).where(
            Investment.company_name == company,
            Investment.investor_name == investor,
            Investment.series_name == series,
        )
    )
    return result.scalar_one_or_none()


async def list_investments_for_company(
    db: AsyncSession, company_name: str
) -> list[Investment]:
    result = await db.execute(
        select(Investment).where(Investment.company_name == company_name)
    )
    return list(result.scalars().all())


async def upsert_investment(db: AsyncSession, data: InvestmentCreate) -> Investment:
    existing = await get_investment(
        db, data.company_name, data.investor_name, data.series_name
    )
    if existing:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return existing
    investment = Investment(**data.model_dump())
    db.add(investment)
    await db.commit()
    await db.refresh(investment)
    return investment


async def update_investment(
    db: AsyncSession, company: str, investor: str, series: str, data: InvestmentUpdate
) -> Investment | None:
    inv = await get_investment(db, company, investor, series)
    if not inv:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(inv, field, value)
    await db.commit()
    await db.refresh(inv)
    return inv
