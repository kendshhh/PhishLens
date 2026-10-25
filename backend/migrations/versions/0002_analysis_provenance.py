"""Add analysis mode and provenance to saved analyses.

Revision ID: 0002_analysis_provenance
Revises: 0001_initial_schema
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_analysis_provenance"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "analyzed_emails",
        sa.Column("analysis_mode", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "analyzed_emails",
        sa.Column("analysis_provenance", postgresql.JSONB(), nullable=True),
    )
    op.create_check_constraint(
        "ck_analyzed_emails_analysis_mode",
        "analyzed_emails",
        "analysis_mode IS NULL OR analysis_mode IN ('mock', 'real', 'unknown')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_analyzed_emails_analysis_mode",
        "analyzed_emails",
        type_="check",
    )
    op.drop_column("analyzed_emails", "analysis_provenance")
    op.drop_column("analyzed_emails", "analysis_mode")
