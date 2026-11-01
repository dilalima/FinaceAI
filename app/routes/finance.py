"""Accounts, transactions and transfer endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.transfer import Transfer
from app.models.user import User
from app.routes.dependencies import get_current_user
from app.schemas.finance import (
    AccountCreate,
    AccountRead,
    TransactionCreate,
    TransactionRead,
    TransferCreate,
    TransferRead,
)

router = APIRouter(prefix="/finance", tags=["finance"])


def owned_account(db: Session, user_id: int, account_id: int) -> Account:
    """Get an account belonging to the authenticated user."""

    account = db.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Account:
    account = Account(user_id=current_user.id, **payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts", response_model=list[AccountRead])
def list_accounts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Account]:
    return list(
        db.scalars(select(Account).where(Account.user_id == current_user.id).order_by(Account.id))
    )


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    owned_account(db, current_user.id, payload.account_id)
    transaction = Transaction(user_id=current_user.id, **payload.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/transactions", response_model=list[TransactionRead])
def list_transactions(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Transaction]:
    return list(
        db.scalars(
            select(Transaction)
            .where(Transaction.user_id == current_user.id)
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        )
    )


@router.post("/transfers", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Transfer:
    if payload.source_account_id == payload.destination_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination accounts must be different",
        )
    owned_account(db, current_user.id, payload.source_account_id)
    owned_account(db, current_user.id, payload.destination_account_id)
    transfer = Transfer(user_id=current_user.id, **payload.model_dump())
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


@router.get("/transfers", response_model=list[TransferRead])
def list_transfers(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Transfer]:
    return list(
        db.scalars(
            select(Transfer)
            .where(Transfer.user_id == current_user.id)
            .order_by(Transfer.transfer_date.desc(), Transfer.id.desc())
        )
    )
