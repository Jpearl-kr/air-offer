from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Click, PriceComparison, Provider, ProviderPrice
from app.schemas.click import ClickCreateRequest, ClickCreateResponse
from app.services.affiliate import build_redirect_url

router = APIRouter(prefix="/clicks", tags=["clicks"])


@router.post("", response_model=ClickCreateResponse, status_code=201)
async def create_click(
    payload: ClickCreateRequest, db: AsyncSession = Depends(get_db)
) -> ClickCreateResponse:
    comparison = await db.get(PriceComparison, payload.price_comparison_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail="price comparison not found")

    provider_price = await db.scalar(
        select(ProviderPrice)
        .where(
            ProviderPrice.flight_result_id == comparison.flight_result_id,
            ProviderPrice.provider_id == comparison.provider_id,
        )
        .order_by(ProviderPrice.fetched_at.desc())
    )
    if provider_price is None:
        raise HTTPException(status_code=404, detail="underlying offer not found")

    provider = await db.get(Provider, comparison.provider_id)

    click = Click(price_comparison_id=comparison.id, user_id=None)
    db.add(click)
    await db.flush()

    redirect_url = build_redirect_url(provider, provider_price.deep_link, click.id)

    await db.commit()
    return ClickCreateResponse(redirect_url=redirect_url)
