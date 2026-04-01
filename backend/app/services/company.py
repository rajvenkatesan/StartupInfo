from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


async def get_company(db: AsyncSession, name: str) -> Company | None:
    result = await db.execute(select(Company).where(Company.company_name == name))
    return result.scalar_one_or_none()


async def list_companies(
    db: AsyncSession,
    status: str | None = None,
    company_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[Company]:
    q = select(Company)
    if status:
        q = q.where(Company.status == status)
    if company_type:
        q = q.where(Company.company_type == company_type)
    q = q.offset(offset).limit(limit).order_by(Company.company_name)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_company(db: AsyncSession, data: CompanyCreate) -> Company:
    company = Company(**data.model_dump())
    company.status = "ready"
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


async def update_company(db: AsyncSession, name: str, data: CompanyUpdate) -> Company | None:
    company = await get_company(db, name)
    if not company:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(company, field, value)
    await db.commit()
    await db.refresh(company)
    return company


async def upsert_company(db: AsyncSession, data: dict) -> Company:
    """Used by the discovery service to insert or update."""
    name = data.get("company_name", "").strip().lower()
    data["company_name"] = name
    existing = await get_company(db, name)
    if existing:
        for k, v in data.items():
            if v is not None:
                setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        return existing
    company = Company(**data)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


async def set_company_status(db: AsyncSession, name: str, status: str) -> None:
    company = await get_company(db, name)
    if company:
        company.status = status
        await db.commit()
