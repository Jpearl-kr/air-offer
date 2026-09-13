"""seed reference data

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    airports = sa.table(
        "airports",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("country", sa.String),
    )
    op.bulk_insert(
        airports,
        [
            {"code": "ICN", "name": "인천국제공항", "country": "KR"},
            {"code": "CEB", "name": "막탄세부국제공항", "country": "PH"},
        ],
    )

    airlines = sa.table(
        "airlines",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("official_site_url", sa.Text),
    )
    op.bulk_insert(
        airlines,
        [{"code": "KE", "name": "대한항공", "official_site_url": "https://www.koreanair.com"}],
    )

    providers = sa.table(
        "providers",
        sa.column("name", sa.String),
        sa.column("provider_type", sa.String),
        sa.column("affiliate_base_url", sa.Text),
    )
    op.bulk_insert(
        providers,
        [
            {"name": "skyscanner", "provider_type": "meta_search", "affiliate_base_url": None},
            {"name": "ke_official", "provider_type": "airline_official", "affiliate_base_url": None},
        ],
    )

    card_companies = sa.table("card_companies", sa.column("name", sa.String))
    op.bulk_insert(card_companies, [{"name": "현대카드"}])

    payment_methods = sa.table(
        "payment_methods",
        sa.column("type", sa.String),
        sa.column("name", sa.String),
        sa.column("card_company_id", sa.Integer),
    )
    # card_company_id 1 == 현대카드, the only row inserted above into an empty table
    op.bulk_insert(
        payment_methods,
        [
            {"type": "simple_pay", "name": "카카오페이", "card_company_id": None},
            {"type": "card", "name": "현대카드", "card_company_id": 1},
        ],
    )

    # promotions/promotion_rules are inserted with raw SQL so we can reference
    # the freshly-generated promotion id (promotion_id 1, since the table is
    # empty) without a round-trip; provider_id 2 == ke_official, payment_method_id
    # 2 == 현대카드, both from the bulk_insert ordering above.
    op.execute(
        """
        INSERT INTO promotions (airline_code, provider_id, title, status, confidence_score)
        VALUES ('KE', 2, '대한항공 공식 홈페이지 가을 프로모션', 'active', 80)
        """
    )
    op.execute(
        """
        INSERT INTO promotion_rules
            (promotion_id, discount_type, discount_value, max_discount, payment_method_id,
             new_member_required, app_only, stackable, stack_group)
        VALUES
            (1, 'fixed', 50000, NULL, NULL, true, false, true, NULL),
            (1, 'percent', 5, 30000, 2, false, false, true, NULL)
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM promotion_rules WHERE promotion_id = 1")
    op.execute("DELETE FROM promotions WHERE airline_code = 'KE'")
    op.execute("DELETE FROM payment_methods WHERE name IN ('카카오페이', '현대카드')")
    op.execute("DELETE FROM card_companies WHERE name = '현대카드'")
    op.execute("DELETE FROM providers WHERE name IN ('skyscanner', 'ke_official')")
    op.execute("DELETE FROM airlines WHERE code = 'KE'")
    op.execute("DELETE FROM airports WHERE code IN ('ICN', 'CEB')")
