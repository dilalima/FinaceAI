"""create planning tables and transaction due date

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("due_date", sa.Date(), nullable=True))
    op.create_index("ix_transactions_due_date", "transactions", ["due_date"], unique=False)
    for table, columns in (
        ("goals", [("name", sa.String(120), False), ("target_amount", sa.Numeric(14, 2), False), ("current_amount", sa.Numeric(14, 2), False), ("target_date", sa.Date(), True)]),
        ("budgets", [("category", sa.String(80), False), ("year", sa.Integer(), False), ("month", sa.Integer(), False), ("limit_amount", sa.Numeric(14, 2), False)]),
    ):
        table_columns = [sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("user_id", sa.Integer(), nullable=False)]
        table_columns.extend(sa.Column(name, type_, nullable=nullable, server_default="0.00" if name == "current_amount" else None) for name, type_, nullable in columns)
        table_columns.extend([sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id")])
        op.create_table(table, *table_columns)
        op.create_index(f"ix_{table}_user_id", table, ["user_id"], unique=False)
    op.create_index("ix_budgets_category", "budgets", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_budgets_category", table_name="budgets")
    op.drop_table("budgets")
    op.drop_table("goals")
    op.drop_index("ix_transactions_due_date", table_name="transactions")
    op.drop_column("transactions", "due_date")
