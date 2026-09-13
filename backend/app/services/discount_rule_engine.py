"""Pure discount calculation logic — no DB access, so it's cheap to unit test.

Callers fetch the applicable PromotionRule rows (joined with their Promotion
title) themselves and pass them in here.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models import PromotionRule


@dataclass
class UserContext:
    payment_method_ids: set[int]
    is_new_member: bool
    booking_date: date
    travel_date: date
    route_id: int | None
    amount_hint: Decimal


@dataclass
class AppliedDiscount:
    rule_id: int
    promotion_title: str
    amount: Decimal
    stack_group: str | None


def is_rule_applicable(rule: PromotionRule, ctx: UserContext) -> bool:
    if rule.payment_method_id is not None and rule.payment_method_id not in ctx.payment_method_ids:
        return False
    if rule.new_member_required and not ctx.is_new_member:
        return False
    if rule.minimum_amount is not None and ctx.amount_hint < rule.minimum_amount:
        return False
    if rule.travel_start is not None and not (rule.travel_start <= ctx.travel_date <= rule.travel_end):
        return False
    if rule.booking_start is not None and not (rule.booking_start <= ctx.booking_date <= rule.booking_end):
        return False
    if rule.applicable_routes and (ctx.route_id is None or ctx.route_id not in rule.applicable_routes):
        return False
    return True


def compute_discount_amount(rule: PromotionRule, base_price: Decimal) -> Decimal:
    if rule.discount_type == "percent":
        amount = base_price * Decimal(rule.discount_value) / Decimal(100)
    else:
        amount = Decimal(rule.discount_value)
    if rule.max_discount is not None:
        amount = min(amount, rule.max_discount)
    return amount


def best_combination(
    rules_with_titles: list[tuple[PromotionRule, str]],
    base_price: Decimal,
    ctx: UserContext,
) -> list[AppliedDiscount]:
    """Applies every stackable rule, but keeps only the single largest discount
    within each stack_group (mutually-exclusive discounts like '카카오페이 10%')."""
    applicable = [(rule, title) for rule, title in rules_with_titles if is_rule_applicable(rule, ctx)]

    standalone: list[tuple[PromotionRule, str]] = []
    grouped: dict[str, list[tuple[PromotionRule, str]]] = defaultdict(list)
    for rule, title in applicable:
        if rule.stack_group:
            grouped[rule.stack_group].append((rule, title))
        else:
            standalone.append((rule, title))

    chosen: list[AppliedDiscount] = []
    for rule, title in standalone:
        chosen.append(AppliedDiscount(rule.id, title, compute_discount_amount(rule, base_price), None))
    for group, group_rules in grouped.items():
        best_rule, best_title = max(group_rules, key=lambda pair: compute_discount_amount(pair[0], base_price))
        chosen.append(
            AppliedDiscount(best_rule.id, best_title, compute_discount_amount(best_rule, base_price), group)
        )
    return chosen
