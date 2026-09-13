from datetime import date
from decimal import Decimal

from app.models import PromotionRule
from app.services.discount_rule_engine import (
    UserContext,
    best_combination,
    compute_discount_amount,
    is_rule_applicable,
)


def make_rule(**overrides) -> PromotionRule:
    defaults = dict(
        id=1,
        promotion_id=1,
        discount_type="fixed",
        discount_value=Decimal(10_000),
        max_discount=None,
        payment_method_id=None,
        new_member_required=False,
        app_only=False,
        minimum_amount=None,
        travel_start=None,
        travel_end=None,
        booking_start=None,
        booking_end=None,
        applicable_routes=None,
        coupon_code=None,
        stackable=True,
        stack_group=None,
    )
    defaults.update(overrides)
    return PromotionRule(**defaults)


def make_ctx(**overrides) -> UserContext:
    defaults = dict(
        payment_method_ids=set(),
        is_new_member=False,
        booking_date=date(2026, 9, 13),
        travel_date=date(2026, 11, 17),
        route_id=1,
        amount_hint=Decimal(1_000_000),
    )
    defaults.update(overrides)
    return UserContext(**defaults)


def test_new_member_rule_requires_new_member_flag():
    rule = make_rule(new_member_required=True)
    assert not is_rule_applicable(rule, make_ctx(is_new_member=False))
    assert is_rule_applicable(rule, make_ctx(is_new_member=True))


def test_payment_method_rule_requires_matching_method():
    rule = make_rule(payment_method_id=2)
    assert not is_rule_applicable(rule, make_ctx(payment_method_ids={1}))
    assert is_rule_applicable(rule, make_ctx(payment_method_ids={1, 2}))


def test_minimum_amount_rule():
    rule = make_rule(minimum_amount=Decimal(500_000))
    assert not is_rule_applicable(rule, make_ctx(amount_hint=Decimal(400_000)))
    assert is_rule_applicable(rule, make_ctx(amount_hint=Decimal(600_000)))


def test_percent_discount_capped_by_max_discount():
    rule = make_rule(discount_type="percent", discount_value=Decimal(5), max_discount=Decimal(30_000))
    # 5% of 1,150,000 = 57,500, capped at 30,000
    assert compute_discount_amount(rule, Decimal(1_150_000)) == Decimal(30_000)


def test_stack_group_keeps_only_the_larger_discount():
    cheap = make_rule(id=1, discount_value=Decimal(10_000), stack_group="payment")
    rich = make_rule(id=2, discount_value=Decimal(30_000), stack_group="payment")
    applied = best_combination([(cheap, "cheap"), (rich, "rich")], Decimal(1_000_000), make_ctx())
    assert len(applied) == 1
    assert applied[0].rule_id == 2


def test_max_discount_avoids_scientific_notation_from_asyncpg_decimal():
    """asyncpg can decode a scale-0 NUMERIC like 30000 as Decimal('3E+4'); the API must
    still render it as a normal fixed-point amount."""
    rule = make_rule(discount_type="percent", discount_value=Decimal(5), max_discount=Decimal("3E+4"))
    amount = compute_discount_amount(rule, Decimal(1_150_000))
    assert amount == Decimal("30000.00")
    assert "E" not in str(amount)


def test_worked_example_from_service_idea_doc():
    """docs/service-idea.md: 대한항공 공식 1,150,000 - 신규회원 50,000 - 현대카드 5%(최대 30,000) = 1,070,000"""
    new_member_rule = make_rule(
        id=1, discount_type="fixed", discount_value=Decimal(50_000), new_member_required=True
    )
    card_rule = make_rule(
        id=2,
        discount_type="percent",
        discount_value=Decimal(5),
        max_discount=Decimal(30_000),
        payment_method_id=10,
    )
    ctx = make_ctx(is_new_member=True, payment_method_ids={10}, amount_hint=Decimal(1_150_000))

    applied = best_combination(
        [(new_member_rule, "신규회원 쿠폰"), (card_rule, "현대카드 5%")], Decimal(1_150_000), ctx
    )
    total_discount = sum((a.amount for a in applied), Decimal(0))
    final_price = Decimal(1_150_000) - total_discount

    assert total_discount == Decimal(80_000)
    assert final_price == Decimal(1_070_000)
