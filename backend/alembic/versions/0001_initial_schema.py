"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "airports",
        sa.Column("code", sa.String(3), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
    )

    op.create_table(
        "airlines",
        sa.Column("code", sa.String(2), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("official_site_url", sa.Text(), nullable=True),
    )

    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("origin", sa.String(3), sa.ForeignKey("airports.code"), nullable=False),
        sa.Column("destination", sa.String(3), sa.ForeignKey("airports.code"), nullable=False),
        sa.UniqueConstraint("origin", "destination"),
    )

    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("provider_type", sa.String(20), nullable=False),
        sa.Column("affiliate_base_url", sa.Text(), nullable=True),
    )

    op.create_table(
        "flight_searches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("origin", sa.String(3), nullable=False),
        sa.Column("destination", sa.String(3), nullable=False),
        sa.Column("depart_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("adults", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("children", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "flight_results",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "search_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("flight_searches.id", ondelete="CASCADE"),
        ),
        sa.Column("airline_code", sa.String(2), sa.ForeignKey("airlines.code"), nullable=True),
        sa.Column("flight_number", sa.String(10), nullable=True),
        sa.Column("depart_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrive_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("itinerary_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_flight_results_search", "flight_results", ["search_id"])
    op.create_index("idx_flight_results_itinerary", "flight_results", ["itinerary_hash"])

    op.create_table(
        "provider_prices",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "flight_result_id",
            sa.BigInteger(),
            sa.ForeignKey("flight_results.id", ondelete="CASCADE"),
        ),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("base_price", sa.Numeric(12, 0), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KRW"),
        sa.Column("deep_link", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_provider_prices_result", "provider_prices", ["flight_result_id"])

    op.create_table(
        "card_companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
    )

    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("card_company_id", sa.Integer(), sa.ForeignKey("card_companies.id"), nullable=True),
    )

    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("airline_code", sa.String(2), sa.ForeignKey("airlines.code"), nullable=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_method", sa.String(20), nullable=True),
        sa.Column("confidence_score", sa.SmallInteger(), server_default="50"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "promotion_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "promotion_id",
            sa.Integer(),
            sa.ForeignKey("promotions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("discount_type", sa.String(10), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_discount", sa.Numeric(12, 0), nullable=True),
        sa.Column("payment_method_id", sa.Integer(), sa.ForeignKey("payment_methods.id"), nullable=True),
        sa.Column("new_member_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("app_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("minimum_amount", sa.Numeric(12, 0), nullable=True),
        sa.Column("travel_start", sa.Date(), nullable=True),
        sa.Column("travel_end", sa.Date(), nullable=True),
        sa.Column("booking_start", sa.Date(), nullable=True),
        sa.Column("booking_end", sa.Date(), nullable=True),
        sa.Column("applicable_routes", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("coupon_code", sa.String(50), nullable=True),
        sa.Column("stackable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stack_group", sa.String(50), nullable=True),
    )
    op.create_index("idx_promo_rules_promotion", "promotion_rules", ["promotion_id"])

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_payment_preferences",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "payment_method_id",
            sa.Integer(),
            sa.ForeignKey("payment_methods.id"),
            primary_key=True,
        ),
    )

    op.create_table(
        "price_comparisons",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "search_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("flight_searches.id"), nullable=True
        ),
        sa.Column(
            "flight_result_id", sa.BigInteger(), sa.ForeignKey("flight_results.id"), nullable=True
        ),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=True),
        sa.Column("base_price", sa.Numeric(12, 0), nullable=False),
        sa.Column(
            "applied_promotion_ids",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("final_price", sa.Numeric(12, 0), nullable=False),
        sa.Column("is_best", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "clicks",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "price_comparison_id",
            sa.BigInteger(),
            sa.ForeignKey("price_comparisons.id"),
            nullable=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("click_id", sa.BigInteger(), sa.ForeignKey("clicks.id"), nullable=True),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=True),
        sa.Column("commission_amount", sa.Numeric(12, 0), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
    )

    op.create_table(
        "price_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("origin", sa.String(3), nullable=False),
        sa.Column("destination", sa.String(3), nullable=False),
        sa.Column("depart_date", sa.Date(), nullable=True),
        sa.Column("target_price", sa.Numeric(12, 0), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("price_alerts")
    op.drop_table("bookings")
    op.drop_table("clicks")
    op.drop_table("price_comparisons")
    op.drop_table("user_payment_preferences")
    op.drop_table("users")
    op.drop_index("idx_promo_rules_promotion", table_name="promotion_rules")
    op.drop_table("promotion_rules")
    op.drop_table("promotions")
    op.drop_table("payment_methods")
    op.drop_table("card_companies")
    op.drop_index("idx_provider_prices_result", table_name="provider_prices")
    op.drop_table("provider_prices")
    op.drop_index("idx_flight_results_itinerary", table_name="flight_results")
    op.drop_index("idx_flight_results_search", table_name="flight_results")
    op.drop_table("flight_results")
    op.drop_table("flight_searches")
    op.drop_table("providers")
    op.drop_table("routes")
    op.drop_table("airlines")
    op.drop_table("airports")
