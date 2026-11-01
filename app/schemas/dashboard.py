"""Dashboard response schemas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AccountBalance(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    account_name: str
    balance: Decimal


class CategoryTotal(BaseModel):
    category: str
    total: Decimal


class MonthlyTotal(BaseModel):
    month: date
    income: Decimal
    expenses: Decimal
    savings: Decimal


class DashboardSummary(BaseModel):
    month: date
    total_balance: Decimal
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_savings: Decimal
    pending_transactions: int
    top_expense_category: str | None
    top_expense_category_total: Decimal
    accounts: list[AccountBalance]
    expenses_by_category: list[CategoryTotal]
    monthly_evolution: list[MonthlyTotal]
