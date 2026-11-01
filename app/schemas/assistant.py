"""Assistant API schemas."""

from pydantic import BaseModel, Field


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=2, max_length=2000)


class AssistantAnswer(BaseModel):
    answer: str
    based_on: str = "dados financeiros reais do usuário"
