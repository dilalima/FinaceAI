"""Dashboard endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.routes.dependencies import get_current_user
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DashboardSummary:
    """Return financial indicators for the authenticated user."""

    return build_dashboard(db, current_user.id)
