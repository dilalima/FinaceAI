"""Accounts, transactions and transfer schemas."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(StrEnum):
    """Supported transaction directions."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(StrEnum):
    """Transaction status values."""

    PENDING = "pending"
    PAID = "paid"
    RECEIVED = "received"


class AccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    institution: str | None = Field(default=None, max_length=120)
    account_type: str = Field(default="bank", min_length=2, max_length=40)
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)


class AccountRead(AccountCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TransactionCreate(BaseModel):
    account_id: int
    description: str = Field(min_length=2, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    type: TransactionType
    category: str = Field(min_length=2, max_length=80)
    transaction_date: date
    due_date: date | None = None
    payment_method: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    status: TransactionStatus = TransactionStatus.PENDING


class TransactionRead(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    source: str


class TransferCreate(BaseModel):
    source_account_id: int
    destination_account_id: int
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    transfer_date: date
    description: str | None = Field(default=None, max_length=255)


class TransferRead(TransferCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
