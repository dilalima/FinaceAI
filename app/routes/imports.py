"""Manual CSV import endpoints."""

import csv
import hashlib
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.account import Account
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.models.user import User
from app.routes.dependencies import get_current_user
from app.schemas.imports import ImportErrorItem, ImportResult

router = APIRouter(prefix="/imports", tags=["imports"])
REQUIRED_COLUMNS = {"date", "description", "amount", "type", "category", "account_id"}


def parse_amount(value: str) -> Decimal:
    """Parse common Brazilian or international decimal formats."""

    normalized = value.strip().replace("R$", "").replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    else:
        normalized = normalized.replace(",", ".")
    amount = Decimal(normalized)
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    return amount.quantize(Decimal("0.01"))


@router.post("/transactions.csv", response_model=ImportResult)
async def import_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportResult:
    """Import transactions from CSV without duplicating existing rows."""

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Envie um arquivo CSV")
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        columns = set(reader.fieldnames or [])
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="O CSV deve estar em UTF-8") from exc
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise HTTPException(status_code=400, detail=f"Colunas ausentes: {', '.join(sorted(missing))}")

    imported = 0
    duplicates = 0
    errors: list[ImportErrorItem] = []
    for row_number, row in enumerate(reader, start=2):
        try:
            account_id = int(row["account_id"] or "0")
            account = db.scalar(select(Account).where(Account.id == account_id, Account.user_id == current_user.id))
            if account is None:
                raise ValueError("account_id does not belong to the authenticated user")
            transaction_type = TransactionType(row["type"].strip().lower())
            transaction_date = date.fromisoformat(row["date"].strip())
            amount = parse_amount(row["amount"])
            status_value = row.get("status", "pending").strip().lower() or "pending"
            transaction_status = TransactionStatus(status_value)
            key = "|".join([str(current_user.id), str(account_id), row["description"].strip(), str(amount), transaction_type.value, row["category"].strip(), transaction_date.isoformat()])
            import_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
            existing = db.scalar(select(Transaction.id).where(Transaction.user_id == current_user.id, Transaction.import_hash == import_hash))
            if existing is not None:
                duplicates += 1
                continue
            db.add(Transaction(user_id=current_user.id, account_id=account_id, description=row["description"].strip(), amount=amount, type=transaction_type, category=row["category"].strip(), transaction_date=transaction_date, due_date=date.fromisoformat(row["due_date"]) if row.get("due_date") else None, status=transaction_status, source="csv", import_hash=import_hash))
            imported += 1
        except (ValueError, InvalidOperation, KeyError) as exc:
            errors.append(ImportErrorItem(row=row_number, error=str(exc)))
    db.commit()
    return ImportResult(imported=imported, skipped_duplicates=duplicates, errors=errors)
