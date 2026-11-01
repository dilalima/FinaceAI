"""Monthly, annual and export report endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.reports.service import annual_months, export_pdf, export_xlsx, report_data
from app.routes.dependencies import get_current_user
from app.schemas.reports import AnnualReport, FinancialReport

router = APIRouter(prefix="/reports", tags=["reports"])


def monthly_range(year: int | None, month: int | None) -> tuple[date, date]:
    today = date.today()
    selected_year, selected_month = year or today.year, month or today.month
    start = date(selected_year, selected_month, 1)
    end = date(selected_year + 1, 1, 1) if selected_month == 12 else date(selected_year, selected_month + 1, 1)
    return start, end


@router.get("/monthly", response_model=FinancialReport)
def monthly_report(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    start, end = monthly_range(year, month)
    return report_data(db, current_user.id, start, end)


@router.get("/annual", response_model=AnnualReport)
def annual_report(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    selected_year = year or date.today().year
    data = report_data(db, current_user.id, date(selected_year, 1, 1), date(selected_year + 1, 1, 1))
    return {**data, "year": selected_year, "months": annual_months(db, current_user.id, selected_year)}


def report_download(db: Session, user_id: int, fmt: str, year: int | None, month: int | None) -> StreamingResponse:
    start, end = monthly_range(year, month)
    data = report_data(db, user_id, start, end)
    title = "FinanceAI - Relatório mensal"
    if fmt == "xlsx":
        output = export_xlsx(data, title)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=financeai-relatorio.xlsx"})
    output = export_pdf(data, title)
    return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=financeai-relatorio.pdf"})


@router.get("/export.xlsx")
def export_excel(
    year: int | None = Query(default=None, ge=2000, le=2100), month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    return report_download(db, current_user.id, "xlsx", year, month)


@router.get("/export.pdf")
def export_pdf_report(
    year: int | None = Query(default=None, ge=2000, le=2100), month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    return report_download(db, current_user.id, "pdf", year, month)
