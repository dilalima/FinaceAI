"""Financial planning schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=14, decimal_places=2)
    target_date: date | None = None


class GoalRead(GoalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime


class BudgetCreate(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    limit_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class BudgetRead(BudgetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime


class BudgetAlert(BaseModel):
    category: str
    limit_amount: Decimal
    spent_amount: Decimal
    percentage: Decimal
    severity: str
