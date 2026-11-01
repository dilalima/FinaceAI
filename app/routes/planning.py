"""Goals, budgets and financial alerts."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.planning import Budget, Goal
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User
from app.routes.dependencies import get_current_user
from app.schemas.planning import BudgetAlert, BudgetCreate, BudgetRead, GoalCreate, GoalRead

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("/goals", response_model=GoalRead, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Goal:
    goal = Goal(user_id=current_user.id, **payload.model_dump())
    db.add(goal); db.commit(); db.refresh(goal)
    return goal


@router.get("/goals", response_model=list[GoalRead])
def list_goals(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Goal]:
    return list(db.scalars(select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.target_date)))


@router.post("/budgets", response_model=BudgetRead, status_code=201)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Budget:
    budget = Budget(user_id=current_user.id, **payload.model_dump())
    db.add(budget); db.commit(); db.refresh(budget)
    return budget


@router.get("/budgets", response_model=list[BudgetRead])
def list_budgets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Budget]:
    return list(db.scalars(select(Budget).where(Budget.user_id == current_user.id).order_by(Budget.year.desc(), Budget.month.desc())))


@router.get("/alerts", response_model=list[BudgetAlert])
def budget_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[BudgetAlert]:
    today = date.today()
    budgets = db.scalars(select(Budget).where(Budget.user_id == current_user.id, Budget.year == today.year, Budget.month == today.month)).all()
    alerts = []
    for budget in budgets:
        spent = db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.user_id == current_user.id, Transaction.category == budget.category, Transaction.type == TransactionType.EXPENSE, Transaction.status == TransactionStatus.PAID, func.extract("year", Transaction.transaction_date) == today.year, func.extract("month", Transaction.transaction_date) == today.month)) or Decimal("0.00")
        percentage = (spent / budget.limit_amount * 100) if budget.limit_amount else Decimal("0")
        if percentage >= 80:
            alerts.append(BudgetAlert(category=budget.category, limit_amount=budget.limit_amount, spent_amount=spent, percentage=percentage, severity="exceeded" if percentage >= 100 else "warning"))
    return alerts
