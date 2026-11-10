"""Add Neon Auth subject mapping to users."""

import sqlalchemy as sa
from alembic import op

revision = "0004_neon_auth_subject"
down_revision = "0003_saved_analysis_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("neon_auth_subject", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_users_neon_auth_subject",
        "users",
        ["neon_auth_subject"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_users_neon_auth_subject", "users", type_="unique")
    op.drop_column("users", "neon_auth_subject")
