"""Initial schema — all tables + audit trigger

Revision ID: 0001
Revises:
Create Date: 2026-03-31
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    # ── companies ─────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("company_name", sa.String(255), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="stub"),
        sa.Column("location", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("company_type", sa.String(20)),
        sa.Column("about", sa.Text),
        sa.Column("vision", sa.Text),
        sa.Column("mission", sa.Text),
        sa.Column("founders", postgresql.ARRAY(sa.Text)),
        sa.Column("website", sa.Text),
        sa.Column("linkedin_url", sa.Text),
        sa.Column("extra", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ── investors ─────────────────────────────────────────────────────────────
    op.create_table(
        "investors",
        sa.Column("investor_name", sa.String(255), primary_key=True),
        sa.Column("description", sa.Text),
        sa.Column("investor_type", sa.String(30)),
        sa.Column("total_companies_invested", sa.Integer),
        sa.Column("total_amount_invested_usd", sa.BigInteger, server_default="-1"),
        sa.Column("location", sa.Text),
        sa.Column("website", sa.Text),
        sa.Column("extra", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ── investments ───────────────────────────────────────────────────────────
    op.create_table(
        "investments",
        sa.Column("company_name", sa.String(255),
                  sa.ForeignKey("companies.company_name", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("investor_name", sa.String(255),
                  sa.ForeignKey("investors.investor_name", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("series_name", sa.String(50), primary_key=True),
        sa.Column("amount_invested_usd", sa.BigInteger, server_default="-1"),
        sa.Column("investor_role", sa.String(30)),
        sa.Column("additional_comments", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ── jobs ──────────────────────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(255),
                  sa.ForeignKey("companies.company_name", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("location", sa.Text),
        sa.Column("job_type", sa.String(20)),
        sa.Column("url", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ── job_applications ──────────────────────────────────────────────────────
    op.create_table(
        "job_applications",
        sa.Column("application_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("jobs.job_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("applied_date", sa.Date),
        sa.Column("status", sa.String(20), nullable=False, server_default="wishlist"),
        sa.Column("notes", sa.Text),
        sa.Column("follow_up_date", sa.Date),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # ── audit_log ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("table_name", sa.String(100), nullable=False, index=True),
        sa.Column("record_pk", sa.Text, nullable=False),
        sa.Column("operation", sa.String(10), nullable=False),
        sa.Column("changed_by", sa.String(100), nullable=False, server_default="system"),
        sa.Column("old_values", postgresql.JSONB),
        sa.Column("new_values", postgresql.JSONB),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()"), index=True),
    )

    # ── updated_at trigger function ───────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for tbl in ["users", "companies", "investors", "investments", "jobs", "job_applications"]:
        op.execute(f"""
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)

    # ── audit trigger ─────────────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_fn()
        RETURNS TRIGGER AS $$
        DECLARE
            pk_val TEXT;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                pk_val := OLD::TEXT;
            ELSE
                pk_val := NEW::TEXT;
            END IF;

            INSERT INTO audit_log (log_id, table_name, record_pk, operation, old_values, new_values, occurred_at)
            VALUES (
                gen_random_uuid(),
                TG_TABLE_NAME,
                pk_val,
                TG_OP,
                CASE WHEN TG_OP IN ('UPDATE','DELETE') THEN to_jsonb(OLD) ELSE NULL END,
                CASE WHEN TG_OP IN ('INSERT','UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
                NOW()
            );
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)

    for tbl in ["users", "companies", "investors", "investments", "jobs", "job_applications"]:
        op.execute(f"""
            CREATE TRIGGER trg_{tbl}_audit
            AFTER INSERT OR UPDATE OR DELETE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();
        """)


def downgrade() -> None:
    for tbl in ["users", "companies", "investors", "investments", "jobs", "job_applications"]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_audit ON {tbl};")
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl};")

    op.execute("DROP FUNCTION IF EXISTS audit_trigger_fn();")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")

    for tbl in ["audit_log", "job_applications", "jobs", "investments", "investors", "companies", "users"]:
        op.drop_table(tbl)
