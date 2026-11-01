"""User persistence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    """Find a user by normalized email."""

    return db.scalar(select(User).where(User.email == email.lower()))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Find a user by primary key."""

    return db.get(User, user_id)


def create_user(
    db: Session, *, email: str, full_name: str, hashed_password: str
) -> User:
    """Persist a new user."""

    user = User(
        email=email.lower(),
        full_name=full_name.strip(),
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
