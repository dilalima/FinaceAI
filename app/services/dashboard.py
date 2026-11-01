"""Dashboard calculations based on persisted financial data."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.transfer import Transfer
from app.schemas.dashboard import (
    AccountBalance,
    CategoryTotal,
    DashboardSummary,
    MonthlyTotal,
)

ZERO = Decimal("0.00")


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """Return the inclusive start and exclusive end of a calendar month."""

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def sum_transactions(
    db: Session,
    user_id: int,
    transaction_type: TransactionType,
    start: date,
    end: date,
) -> Decimal:
    """Sum settled transactions of one type for a user and period."""

    settled_status = (
        TransactionStatus.RECEIVED
        if transaction_type == TransactionType.INCOME
        else TransactionStatus.PAID
    )
    value = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == transaction_type,
            Transaction.status == settled_status,
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
        )
    )
    return value or ZERO


def account_balance(db: Session, user_id: int, account: Account) -> Decimal:
    """Calculate an account balance from settled transactions and transfers."""

    income = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.account_id == account.id,
            Transaction.type == TransactionType.INCOME,
            Transaction.status == TransactionStatus.RECEIVED,
        )
    ) or ZERO
    expenses = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.account_id == account.id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.status == TransactionStatus.PAID,
        )
    ) or ZERO
    incoming = db.scalar(
        select(func.coalesce(func.sum(Transfer.amount), 0)).where(
            Transfer.user_id == user_id,
            Transfer.destination_account_id == account.id,
        )
    ) or ZERO
    outgoing = db.scalar(
        select(func.coalesce(func.sum(Transfer.amount), 0)).where(
            Transfer.user_id == user_id,
            Transfer.source_account_id == account.id,
        )
    ) or ZERO
    return account.initial_balance + income - expenses + incoming - outgoing


def build_dashboard(db: Session, user_id: int, today: date | None = None) -> DashboardSummary:
    """Build a dashboard summary from the authenticated user's records."""

    current = today or date.today()
    start, end = month_bounds(current.year, current.month)
    monthly_income = sum_transactions(db, user_id, TransactionType.INCOME, start, end)
    monthly_expenses = sum_transactions(db, user_id, TransactionType.EXPENSE, start, end)

    accounts = list(
        db.scalars(select(Account).where(Account.user_id == user_id).order_by(Account.id))
    )
    account_balances = [
        AccountBalance(
            account_id=account.id,
            account_name=account.name,
            balance=account_balance(db, user_id, account),
        )
        for account in accounts
    ]

    category_rows = db.execute(
        select(Transaction.category, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.status == TransactionStatus.PAID,
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    ).all()
    expenses_by_category = [
        CategoryTotal(category=category, total=total) for category, total in category_rows
    ]
    pending_transactions = db.scalar(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == user_id,
            Transaction.status == TransactionStatus.PENDING,
        )
    ) or 0

    evolution: list[MonthlyTotal] = []
    year, month = current.year, current.month
    for _ in range(6):
        period_start, period_end = month_bounds(year, month)
        income = sum_transactions(db, user_id, TransactionType.INCOME, period_start, period_end)
        expenses = sum_transactions(db, user_id, TransactionType.EXPENSE, period_start, period_end)
        evolution.append(
            MonthlyTotal(
                month=period_start,
                income=income,
                expenses=expenses,
                savings=income - expenses,
            )
        )
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    evolution.reverse()

    return DashboardSummary(
        month=start,
        total_balance=sum((item.balance for item in account_balances), ZERO),
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_savings=monthly_income - monthly_expenses,
        pending_transactions=int(pending_transactions),
        top_expense_category=expenses_by_category[0].category if expenses_by_category else None,
        top_expense_category_total=(expenses_by_category[0].total if expenses_by_category else ZERO),
        accounts=account_balances,
        expenses_by_category=expenses_by_category,
        monthly_evolution=evolution,
    )
