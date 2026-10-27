"""Add per-demo-user idempotency keys for saved analysis creation.

Revision ID: 0003_saved_analysis_idempotency
Revises: 0002_analysis_provenance
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_saved_analysis_idempotency"
down_revision = "0002_analysis_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analyzed_emails",
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_analyzed_emails_user_idempotency_key",
        "analyzed_emails",
        ["user_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_analyzed_emails_user_idempotency_key",
        "analyzed_emails",
        type_="unique",
    )
    op.drop_column("analyzed_emails", "idempotency_key")
