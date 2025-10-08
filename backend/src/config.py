"""Configurações centralizadas do agente."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

# Tentar carregar .env de múltiplos locais possíveis
try:
    from dotenv import load_dotenv
    
    # Procurar .env em vários locais possíveis
    possible_env_paths = [
        Path(".env"),  # diretório atual
        Path("backend/.env"),  # se executado da raiz do projeto
        Path(__file__).parent.parent.parent / ".env",  # relativo a este arquivo
    ]
    
    for env_path in possible_env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break
except ImportError:
    pass


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente ou `.env`."""

    project_name: str = Field(default="i2a2-autonomous-agent")
    data_dir: Path = Field(default=Path("data"))
    cache_dir: Path = Field(default=Path("data/cache"))
    reports_dir: Path = Field(default=Path("reports"))

    duckdb_path: Path = Field(default=Path("data/cache/agent.duckdb"))

    # Provedores externos
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    # Google/Gemini API key
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # Configurações de LLM
    llm_provider: str = Field(default="gemini", env="LLM_PROVIDER")
    default_model: str = Field(default="gemini-2.5-flash-lite", env="DEFAULT_MODEL")
    # Supported providers: openai, gemini
    model_temperature: float = Field(default=0.0, env="MODEL_TEMPERATURE")
    model_request_timeout: float = Field(default=120.0, env="MODEL_REQUEST_TIMEOUT")

    langchain_tracing_v2: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")
    langchain_project: Optional[str] = Field(default=None, env="LANGCHAIN_PROJECT")

    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna instância singleton das configurações."""

    return Settings()
