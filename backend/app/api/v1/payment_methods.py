from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import PaymentMethod
from app.schemas.payment_method import PaymentMethodOut

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.get("", response_model=list[PaymentMethodOut])
async def list_payment_methods(db: AsyncSession = Depends(get_db)) -> list[PaymentMethodOut]:
    rows = (await db.execute(select(PaymentMethod))).scalars().all()
    return [PaymentMethodOut(id=row.id, type=row.type, name=row.name) for row in rows]
