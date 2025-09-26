"""Fábrica de modelos de linguagem para o agente."""

from __future__ import annotations

from typing import Any

from src.config import Settings, get_settings

try:  # pragma: no cover
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    ChatOpenAI = None  # type: ignore

try:  # pragma: no cover
    from langchain_community.chat_models import ChatOllama
except ImportError:  # pragma: no cover
    ChatOllama = None  # type: ignore

SUPPORTED_PROVIDERS = {"openai", "ollama"}


def _ensure_provider_available(provider: str) -> None:
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Provedor de LLM não suportado: {provider}")
    if provider == "openai" and ChatOpenAI is None:
        raise RuntimeError(
            "Dependência langchain-openai não encontrada. Execute `poetry install` ou defina LLM_PROVIDER=ollama."
        )
    if provider == "ollama" and ChatOllama is None:
        raise RuntimeError(
            "Dependência langchain-community[ollama] não encontrada. Execute `poetry install` para habilitar o provedor."  # noqa: E501
        )


def create_chat_model(
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    request_timeout: float | None = None,
    settings: Settings | None = None,
) -> Any:
    """Instancia o modelo de linguagem de acordo com as configurações."""

    settings = settings or get_settings()
    provider = (provider or settings.llm_provider).lower()
    _ensure_provider_available(provider)

    model_name = model or settings.default_model
    temp = settings.model_temperature if temperature is None else temperature
    timeout = request_timeout or settings.model_request_timeout

    if provider == "openai":
        return ChatOpenAI(model=model_name, temperature=temp, timeout=timeout)

    base_url = settings.ollama_base_url or "http://localhost:11434"
    ollama_model = model or settings.ollama_model
    return ChatOllama(model=ollama_model, temperature=temp, base_url=base_url, timeout=timeout)
