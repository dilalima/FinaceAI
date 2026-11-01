"""Financial assistant endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.provider import get_assistant_provider
from app.database.session import get_db
from app.models.user import User
from app.routes.dependencies import get_current_user
from app.schemas.assistant import AssistantAnswer, AssistantQuestion
from app.services.dashboard import build_dashboard

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantAnswer)
def chat(
    payload: AssistantQuestion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistantAnswer:
    """Answer a financial question using the current user's dashboard data."""

    dashboard = build_dashboard(db, current_user.id)
    try:
        provider = get_assistant_provider()
        answer = provider.answer(payload.question, dashboard.model_dump_json())
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assistente indisponível: configure OPENAI_API_KEY no arquivo .env",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível consultar o provedor do assistente",
        ) from exc
    return AssistantAnswer(answer=answer)
