"""Add company_url (required) and related_urls to companies

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-01
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add company_url — nullable first so existing rows are accepted,
    # then backfill from website, then enforce NOT NULL.
    op.add_column("companies", sa.Column("company_url", sa.Text, nullable=True))
    op.add_column("companies", sa.Column("related_urls", postgresql.ARRAY(sa.Text), nullable=True))

    # Backfill company_url from existing website column where available
    op.execute("UPDATE companies SET company_url = website WHERE website IS NOT NULL AND website != ''")
    op.execute("UPDATE companies SET company_url = '' WHERE company_url IS NULL")

    op.alter_column("companies", "company_url", nullable=False)


def downgrade() -> None:
    op.drop_column("companies", "related_urls")
    op.drop_column("companies", "company_url")
