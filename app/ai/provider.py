"""Financial assistant providers."""

from abc import ABC, abstractmethod

from openai import OpenAI

from app.core.config import get_settings


class AssistantProvider(ABC):
    """Interface that allows the model provider to be replaced."""

    @abstractmethod
    def answer(self, question: str, financial_context: str) -> str:
        """Answer a question using only the supplied financial context."""


class OpenAIAssistantProvider(AssistantProvider):
    """OpenAI Responses API implementation."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def answer(self, question: str, financial_context: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "developer",
                    "content": (
                        "Você é o assistente financeiro do FinanceAI. Use somente os dados "
                        "fornecidos no contexto. Nunca invente valores, movimentações ou saldos. "
                        "Diferencie fatos, estimativas e recomendações. Se os dados não forem "
                        "suficientes, diga isso claramente. Não execute pagamentos ou transferências. "
                        "Responda em português do Brasil, de forma objetiva."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Contexto financeiro real:\n{financial_context}\n\nPergunta: {question}",
                },
            ],
        )
        return response.output_text


def get_assistant_provider() -> AssistantProvider:
    """Return the configured provider."""

    return OpenAIAssistantProvider()
