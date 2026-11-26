"""Add privacy-safe shared AI request quota buckets."""

import sqlalchemy as sa
from alembic import op

revision = "0005_ai_request_quota"
down_revision = "0004_neon_auth_subject"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_request_quota_buckets",
        sa.Column("scope", sa.String(length=24), nullable=False),
        sa.Column("subject_hash", sa.String(length=64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column(
            "cost_upper_bound_usd",
            sa.Numeric(precision=20, scale=12),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint(
            "scope",
            "subject_hash",
            "window_start",
            name="pk_ai_request_quota_buckets",
        ),
        sa.CheckConstraint(
            "scope IN ('ip_minute', 'ip_day', 'user_day', 'daily_spend')",
            name="ck_ai_request_quota_scope",
        ),
        sa.CheckConstraint("request_count > 0", name="ck_ai_request_quota_count"),
        sa.CheckConstraint(
            "cost_upper_bound_usd >= 0",
            name="ck_ai_request_quota_cost",
        ),
    )
    op.create_index(
        "ix_ai_request_quota_window_start",
        "ai_request_quota_buckets",
        ["window_start"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ai_request_quota_window_start",
        table_name="ai_request_quota_buckets",
    )
    op.drop_table("ai_request_quota_buckets")
