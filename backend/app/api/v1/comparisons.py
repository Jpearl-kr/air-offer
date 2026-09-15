from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    FlightResult,
    FlightSearch,
    PaymentMethod,
    PriceComparison,
    Promotion,
    PromotionRule,
    Provider,
    ProviderPrice,
)
from app.schemas.comparison import AppliedPromotionOut, ComparisonResponse, FlightResultOut, OfferOut
from app.services.alert_checker import check_and_trigger_alerts
from app.services.discount_rule_engine import UserContext, best_combination
from app.services.route_lookup import get_or_create_route_id

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


def _money(value: Decimal) -> Decimal:
    """Normalizes to fixed-point cents. asyncpg can decode a scale-0 NUMERIC like
    30000 as Decimal('3E+4'); quantizing prevents scientific notation in API output."""
    return value.quantize(Decimal("0.01"))


async def _applicable_rules(
    db: AsyncSession, provider_id: int, airline_code: str | None
) -> list[tuple[PromotionRule, str]]:
    stmt = (
        select(PromotionRule, Promotion.title)
        .join(Promotion, PromotionRule.promotion_id == Promotion.id)
        .where(Promotion.status == "active", Promotion.provider_id == provider_id)
    )
    if airline_code is not None:
        stmt = stmt.where((Promotion.airline_code.is_(None)) | (Promotion.airline_code == airline_code))
    rows = (await db.execute(stmt)).all()
    return [(rule, title) for rule, title in rows]


@router.get("/{search_id}", response_model=ComparisonResponse)
async def get_comparisons(
    search_id: UUID,
    payment_methods: str = Query(default="", description="comma-separated payment method names"),
    new_member: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> ComparisonResponse:
    search = await db.get(FlightSearch, search_id)
    if search is None:
        raise HTTPException(status_code=404, detail="search not found")

    requested_names = [name.strip() for name in payment_methods.split(",") if name.strip()]
    payment_method_ids: set[int] = set()
    if requested_names:
        rows = (
            await db.execute(select(PaymentMethod).where(PaymentMethod.name.in_(requested_names)))
        ).scalars()
        payment_method_ids = {pm.id for pm in rows}

    route_id = await get_or_create_route_id(db, search.origin, search.destination)

    flight_results = (
        (await db.execute(select(FlightResult).where(FlightResult.search_id == search_id)))
        .scalars()
        .all()
    )

    results_out: list[FlightResultOut] = []
    triggered_alert_ids: list[int] = []

    for flight_result in flight_results:
        provider_prices = (
            (
                await db.execute(
                    select(ProviderPrice).where(ProviderPrice.flight_result_id == flight_result.id)
                )
            )
            .scalars()
            .all()
        )
        if not provider_prices:
            continue

        market_lowest = min(_money(pp.base_price) for pp in provider_prices)

        offers: list[OfferOut] = []
        comparisons: list[PriceComparison] = []
        for provider_price in provider_prices:
            base_price = _money(provider_price.base_price)
            provider = await db.get(Provider, provider_price.provider_id)
            rules = await _applicable_rules(db, provider_price.provider_id, flight_result.airline_code)

            ctx = UserContext(
                payment_method_ids=payment_method_ids,
                is_new_member=new_member,
                booking_date=date.today(),
                travel_date=search.depart_date,
                route_id=route_id,
                amount_hint=base_price,
            )
            applied = best_combination(rules, base_price, ctx)
            discount_total: Decimal = sum((a.amount for a in applied), Decimal(0))
            final_price = _money(base_price - discount_total)

            comparison = PriceComparison(
                search_id=search_id,
                flight_result_id=flight_result.id,
                provider_id=provider_price.provider_id,
                base_price=base_price,
                applied_promotion_ids=[a.rule_id for a in applied],
                final_price=final_price,
                is_best=False,
            )
            db.add(comparison)
            await db.flush()
            comparisons.append(comparison)

            offers.append(
                OfferOut(
                    provider=provider.name,
                    base_price=base_price,
                    final_price=final_price,
                    applied_promotions=[
                        AppliedPromotionOut(id=a.rule_id, title=a.promotion_title, discount=-a.amount)
                        for a in applied
                    ],
                    deep_link=provider_price.deep_link,
                    price_comparison_id=comparison.id,
                )
            )

        best_offer = min(offers, key=lambda o: o.final_price)
        for offer, comparison in zip(offers, comparisons):
            comparison.is_best = offer is best_offer

        results_out.append(
            FlightResultOut(
                flight_result_id=flight_result.id,
                airline=flight_result.airline_code,
                flight_number=flight_result.flight_number,
                depart_at=flight_result.depart_at,
                arrive_at=flight_result.arrive_at,
                offers=offers,
                best_offer_provider=best_offer.provider,
                savings_vs_market_lowest=_money(market_lowest - best_offer.final_price),
            )
        )

        triggered = await check_and_trigger_alerts(
            db, search.origin, search.destination, search.depart_date, best_offer.final_price
        )
        triggered_alert_ids.extend(alert.id for alert in triggered)

    await db.commit()

    return ComparisonResponse(
        search_id=search_id,
        origin=search.origin,
        destination=search.destination,
        results=results_out,
        triggered_alert_ids=triggered_alert_ids,
    )
