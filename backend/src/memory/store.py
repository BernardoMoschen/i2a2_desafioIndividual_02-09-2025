"""Abstrações de memória para o agente."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.config import get_settings

try:  # pragma: no cover
    from langchain.memory import ConversationBufferMemory
except ImportError:  # pragma: no cover
    ConversationBufferMemory = None  # type: ignore

try:  # pragma: no cover
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import OpenAIEmbeddings
except ImportError:  # pragma: no cover
    FAISS = None  # type: ignore
    OpenAIEmbeddings = None  # type: ignore


@dataclass
class AgentMemory:
    chat: Any
    vector: Optional[Any]


def build_memory(namespace: str) -> AgentMemory:
    """Cria memórias necessárias para o agente com fallback seguro."""

    if ConversationBufferMemory is None:
        raise RuntimeError("LangChain não está instalado. Execute `poetry install`.")

    chat_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    vector_store = None
    if FAISS is not None and OpenAIEmbeddings is not None:
        settings = get_settings()
        base_path = Path(settings.cache_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        store_path = base_path / f"faiss_{namespace}"
        embeddings = OpenAIEmbeddings()
        if store_path.exists():
            vector_store = FAISS.load_local(
                str(store_path),
                embeddings,
                allow_dangerous_deserialization=True,
            )
        else:
            vector_store = FAISS.from_texts([], embeddings)
            vector_store.save_local(str(store_path))

    return AgentMemory(chat=chat_memory, vector=vector_store)
