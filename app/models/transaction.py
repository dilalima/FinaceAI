"""Income and expense transaction model."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TransactionType(StrEnum):
    """Supported transaction directions."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(StrEnum):
    """Lifecycle status for a transaction."""

    PENDING = "pending"
    PAID = "paid"
    RECEIVED = "received"


class Transaction(Base):
    """A user income or expense."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, values_callable=lambda enum_type: [item.value for item in enum_type])
    )
    category: Mapped[str] = mapped_column(String(80), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    import_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    payment_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(
            TransactionStatus,
            values_callable=lambda enum_type: [item.value for item in enum_type],
        ),
        default=TransactionStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="transactions")
    account = relationship("Account")
