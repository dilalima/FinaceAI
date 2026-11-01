"""Report response schemas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ReportCategory(BaseModel):
    category: str
    total: Decimal


class FinancialReport(BaseModel):
    start: date
    end: date
    income: Decimal
    expenses: Decimal
    savings: Decimal
    categories: list[ReportCategory]


class AnnualMonth(BaseModel):
    month: date
    income: Decimal
    expenses: Decimal
    savings: Decimal


class AnnualReport(FinancialReport):
    year: int
    months: list[AnnualMonth]
