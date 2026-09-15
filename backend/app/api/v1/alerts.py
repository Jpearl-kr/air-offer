from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import PriceAlert, User
from app.schemas.alert import AlertCreateRequest, AlertOut
from app.services.user_lookup import get_or_create_user_by_email

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertOut, status_code=201)
async def create_alert(payload: AlertCreateRequest, db: AsyncSession = Depends(get_db)) -> AlertOut:
    user = await get_or_create_user_by_email(db, payload.email)

    alert = PriceAlert(
        user_id=user.id,
        origin=payload.origin.upper(),
        destination=payload.destination.upper(),
        depart_date=payload.depart_date,
        target_price=payload.target_price,
    )
    db.add(alert)
    await db.flush()
    await db.commit()
    return AlertOut.model_validate(alert)


@router.get("", response_model=list[AlertOut])
async def list_alerts(email: str = Query(...), db: AsyncSession = Depends(get_db)) -> list[AlertOut]:
    user = await db.scalar(select(User).where(User.email == email))
    if user is None:
        return []
    rows = (await db.execute(select(PriceAlert).where(PriceAlert.user_id == user.id))).scalars().all()
    return [AlertOut.model_validate(row) for row in rows]


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> None:
    alert = await db.get(PriceAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    await db.delete(alert)
    await db.commit()
