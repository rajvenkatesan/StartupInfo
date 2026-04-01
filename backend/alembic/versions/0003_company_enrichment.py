"""Add enrichment columns to companies (founded_year, employee_count, headquarters,
industry, total_funding_usd, latest_series, products)

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-01
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("founded_year",    sa.Integer,                       nullable=True))
    op.add_column("companies", sa.Column("employee_count",  sa.String(50),                    nullable=True))
    op.add_column("companies", sa.Column("headquarters",    sa.Text,                          nullable=True))
    op.add_column("companies", sa.Column("industry",        sa.Text,                          nullable=True))
    op.add_column("companies", sa.Column("total_funding_usd", sa.BigInteger,                  nullable=True))
    op.add_column("companies", sa.Column("latest_series",   sa.String(30),                    nullable=True))
    op.add_column("companies", sa.Column("products",        postgresql.ARRAY(sa.Text),        nullable=True))


def downgrade() -> None:
    for col in ("products", "latest_series", "total_funding_usd",
                "industry", "headquarters", "employee_count", "founded_year"):
        op.drop_column("companies", col)
