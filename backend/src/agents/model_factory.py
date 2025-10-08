"""Fábrica de modelos de linguagem para o agente."""

from __future__ import annotations

import os
from typing import Any

from src.config import Settings, get_settings

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None  # type: ignore

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None  # type: ignore

SUPPORTED_PROVIDERS = {"openai", "gemini"}


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
    
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Provedor de LLM não suportado: {provider}. Use 'openai' ou 'gemini'.")

    model_name = model or settings.default_model
    temp = settings.model_temperature if temperature is None else temperature
    timeout = request_timeout or settings.model_request_timeout

    if provider == "openai":
        if ChatOpenAI is None:
            raise RuntimeError(
                "Dependência langchain-openai não encontrada. Execute `poetry install` ou `pip install langchain-openai`."
            )
        return ChatOpenAI(
            model=model_name,
            temperature=temp,
            timeout=timeout,
            model_kwargs={"top_p": 0.95} if temp > 0 else {}
        )

    if provider == "gemini":
        # Preferir o adapter oficial do Google Gemini
        if ChatGoogleGenerativeAI is not None:
            api_key = (
                settings.google_api_key 
                or settings.gemini_api_key 
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
            )
            if not api_key:
                raise RuntimeError(
                    "API key do Gemini não encontrada. Configure GOOGLE_API_KEY ou GEMINI_API_KEY no arquivo .env"
                )
            
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=temp,
                timeout=timeout,
                convert_system_message_to_human=True,  # Gemini não suporta system messages nativamente
            )
        
        # Fallback para ChatGooglePalm (versão antiga)
        try:
            from langchain_community.chat_models import ChatGooglePalm
            
            api_key = (
                settings.google_api_key 
                or settings.gemini_api_key 
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("GEMINI_API_KEY")
            )
            if not api_key:
                raise RuntimeError(
                    "API key do Gemini não encontrada. Configure GOOGLE_API_KEY ou GEMINI_API_KEY no arquivo .env"
                )
                
            return ChatGooglePalm(
                model=model_name,
                google_api_key=api_key,
                temperature=temp,
                timeout=timeout,
            )
        except ImportError:
            raise RuntimeError(
                "Nenhum adapter Gemini encontrado. Instale com: pip install langchain-google-genai"
            )

    raise RuntimeError(f"Provedor '{provider}' não implementado no factory de modelos")
