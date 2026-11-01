import uuid

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.user import User


client = TestClient(app)


def create_test_user() -> tuple[str, dict[str, str]]:
    email = f"security-{uuid.uuid4().hex}@example.com"
    client.post(
        "/auth/register",
        json={"email": email, "full_name": "Security Test", "password": "SenhaTeste123!"},
    )
    token = client.post(
        "/auth/login", json={"email": email, "password": "SenhaTeste123!"}
    ).json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


def delete_test_users(*emails: str) -> None:
    db = SessionLocal()
    for email in emails:
        user = db.query(User).filter(User.email == email).one_or_none()
        if user:
            db.delete(user)
    db.commit()
    db.close()


def test_user_cannot_see_another_users_accounts() -> None:
    first_email, first_headers = create_test_user()
    second_email, second_headers = create_test_user()
    try:
        created = client.post(
            "/finance/accounts",
            headers=first_headers,
            json={"name": "Conta privada", "account_type": "bank", "initial_balance": "10.00"},
        )
        assert created.status_code == 201
        assert client.get("/finance/accounts", headers=second_headers).json() == []
    finally:
        delete_test_users(first_email, second_email)


def test_invalid_token_is_rejected() -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401


def test_negative_transaction_amount_is_rejected() -> None:
    email, headers = create_test_user()
    try:
        account = client.post(
            "/finance/accounts",
            headers=headers,
            json={"name": "Conta valida", "account_type": "bank", "initial_balance": "0.00"},
        ).json()
        response = client.post(
            "/finance/transactions",
            headers=headers,
            json={
                "account_id": account["id"],
                "description": "Valor inválido",
                "amount": "-1.00",
                "type": "expense",
                "category": "Teste",
                "transaction_date": "2026-11-01",
                "status": "paid",
            },
        )
        assert response.status_code == 422
    finally:
        delete_test_users(email)
