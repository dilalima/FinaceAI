"""Financial report calculations and exports."""

from calendar import monthrange
from datetime import date
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionStatus, TransactionType

ZERO = Decimal("0.00")


def bounds(start: date, end: date) -> tuple[date, date]:
    """Return an inclusive start and exclusive end range."""

    return start, end


def report_data(db: Session, user_id: int, start: date, end: date) -> dict:
    """Calculate report totals and category details for one period."""

    income = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.INCOME,
            Transaction.status == TransactionStatus.RECEIVED,
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
        )
    ) or ZERO
    expenses = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.status == TransactionStatus.PAID,
            Transaction.transaction_date >= start,
            Transaction.transaction_date < end,
        )
    ) or ZERO
    categories = db.execute(
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
    return {
        "start": start,
        "end": end,
        "income": income,
        "expenses": expenses,
        "savings": income - expenses,
        "categories": [{"category": name, "total": total} for name, total in categories],
    }


def annual_months(db: Session, user_id: int, year: int) -> list[dict]:
    """Build monthly totals for a year."""

    result = []
    for month in range(1, 13):
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        data = report_data(db, user_id, start, end)
        result.append({"month": start, "income": data["income"], "expenses": data["expenses"], "savings": data["savings"]})
    return result


def export_xlsx(data: dict, title: str) -> BytesIO:
    """Create an Excel workbook from a report."""

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Relatório"
    sheet.append([title])
    sheet.append(["Período", data["start"].isoformat(), data["end"].isoformat()])
    sheet.append([])
    sheet.append(["Indicador", "Valor"])
    sheet.append(["Receitas", float(data["income"])])
    sheet.append(["Despesas", float(data["expenses"])])
    sheet.append(["Economia", float(data["savings"])])
    sheet.append([])
    sheet.append(["Categoria", "Total"])
    for item in data["categories"]:
        sheet.append([item["category"], float(item["total"])])
    sheet.column_dimensions["A"].width = 28
    sheet.column_dimensions["B"].width = 18
    for row in sheet.iter_rows(min_row=5, min_col=2, max_col=2):
        row[0].number_format = 'R$ #,##0.00'
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def export_pdf(data: dict, title: str) -> BytesIO:
    """Create a simple PDF report."""

    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 0.4 * cm)]
    story.append(Paragraph(f"Período: {data['start']} a {data['end']}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))
    rows = [["Indicador", "Valor"], ["Receitas", f"R$ {data['income']:,.2f}"], ["Despesas", f"R$ {data['expenses']:,.2f}"], ["Economia", f"R$ {data['savings']:,.2f}"]]
    rows.extend([[item["category"], f"R$ {item['total']:,.2f}"] for item in data["categories"]])
    table = Table(rows, colWidths=[10 * cm, 6 * cm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2367e8")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .3, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 8)]))
    story.append(table)
    document.build(story)
    output.seek(0)
    return output
