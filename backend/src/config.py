"""Configurações centralizadas do agente."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente ou `.env`."""

    project_name: str = Field(default="i2a2-autonomous-agent")
    data_dir: Path = Field(default=Path("data"))
    cache_dir: Path = Field(default=Path("data/cache"))
    reports_dir: Path = Field(default=Path("reports"))

    duckdb_path: Path = Field(default=Path("data/cache/agent.duckdb"))

    # Provedores externos
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")

    # Configurações de LLM
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    default_model: str = Field(default="gpt-4o-mini", env="DEFAULT_MODEL")
    ollama_model: str = Field(default="mistral", env="OLLAMA_MODEL")
    ollama_base_url: Optional[str] = Field(default=None, env="OLLAMA_BASE_URL")
    model_temperature: float = Field(default=0.0, env="MODEL_TEMPERATURE")
    model_request_timeout: float = Field(default=120.0, env="MODEL_REQUEST_TIMEOUT")

    langchain_tracing_v2: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")
    langchain_project: Optional[str] = Field(default=None, env="LANGCHAIN_PROJECT")

    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna instância singleton das configurações."""

    return Settings()
