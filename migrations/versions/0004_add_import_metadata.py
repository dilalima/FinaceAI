"""add CSV import metadata

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("source", sa.String(length=30), nullable=False, server_default="manual"))
    op.add_column("transactions", sa.Column("import_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_transactions_import_hash", "transactions", ["import_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_import_hash", table_name="transactions")
    op.drop_column("transactions", "import_hash")
    op.drop_column("transactions", "source")
