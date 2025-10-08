"""Abstrações de memória para o agente.

Este módulo expõe um MemoryManager que suporta modos:
- ephemeral: apenas memória em RAM com limites (deque)
- summarize: comprime histórico antigo em um resumo quando ultrapassa thresholds
- guarded persistent: opcionalmente persiste embeddings em FAISS quando explicitamente ativado

Também mantém compatibilidade com a API existente: `build_memory(namespace)` retorna
um AgentMemory(chat, vector) onde `chat` é um LangChain ConversationBufferMemory (para compatibilidade)
e `vector` é a instância de MemoryManager (ou None se inválido).
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

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

logger = logging.getLogger(__name__)


@dataclass
class AgentMemory:
    chat: Any
    vector: Optional[Any]


class MemoryManager:
    """Memory manager with ephemeral, summarize and guarded persistent modes.

    This is intentionally lightweight: summarization uses a local heuristic by default
    (concatenate and take representative sentences) to avoid extra dependencies.
    """

    def __init__(
        self,
        namespace: str,
        mode: str = "ephemeral",
        max_items: int = 200,
        summary_threshold: int = 100,
        cache_dir: Optional[str] = None,
    ) -> None:
        self.namespace = namespace
        self.mode = mode
        self.max_items = max_items
        self.summary_threshold = summary_threshold
        self.cache_dir = cache_dir or get_settings().cache_dir

        # in-memory deque of messages (each message is dict with role/content/meta/timestamp)
        self._deque: deque = deque()
        self._summaries: List[Dict[str, Any]] = []

        # persistence
        self._persist_enabled = False
        self._vector_store = None
        self._embeddings = None

        # initialize guarded persistence only when explicitly enabled

    # Basic message model: {'role':..., 'content':..., 'meta':...}
    def add(self, message: Dict[str, Any]) -> None:
        msg = dict(message)
        msg.setdefault("meta", {})
        msg["meta"]["ts"] = time.time()
        self._deque.append(msg)

        # enforce max_items
        if len(self._deque) > self.max_items:
            if self.mode == "summarize":
                try:
                    self._summarize_older()
                except Exception as exc:
                    logger.warning("Summarization failed: %s", exc)
                    # fallback: drop oldest
                    self._deque.popleft()
            else:
                self._deque.popleft()

        # if persistence enabled, index text into vector store
        if self._persist_enabled and self._vector_store is not None and self._embeddings is not None:
            try:
                text = self._as_text(msg)
                # use a minimal metadata
                meta = {"role": msg.get("role"), "ts": msg["meta"].get("ts")}
                # FAISS wrapper via LangChain vectorstores typically has add_texts
                if hasattr(self._vector_store, "add_texts"):
                    self._vector_store.add_texts([text], metadatas=[meta])
                else:
                    # best-effort: if vector_store has from_texts, recreate
                    pass
            except Exception as exc:
                logger.warning("Failed to index message to vector store: %s", exc)

    def retrieve(self, query: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        # If persistence enabled and query provided, use vector similarity
        if self._persist_enabled and self._vector_store is not None and query:
            try:
                if hasattr(self._vector_store, "similarity_search"):
                    docs = self._vector_store.similarity_search(query, k=k)
                    # docs may be LangChain Documents; map to dict
                    results = []
                    for d in docs:
                        results.append({"role": "memory", "content": getattr(d, "page_content", str(d)), "meta": {}})
                    return results
            except Exception as exc:
                logger.warning("Vector retrieve failed: %s", exc)

        # fallback: return recent messages + summaries (most recent first)
        out: List[Dict[str, Any]] = []
        # include summaries first
        for s in self._summaries[-3:]:
            out.append(s)
        # then most recent messages
        for m in list(self._deque)[-k:]:
            out.append(m)
        return out

    def clear(self) -> None:
        self._deque.clear()
        self._summaries.clear()
        # clear persistent store if enabled
        if self._persist_enabled and self._vector_store is not None:
            try:
                # attempt to delete local files for FAISS store
                base = Path(self.cache_dir) / f"faiss_{self.namespace}"
                if base.exists():
                    for p in base.iterdir():
                        try:
                            p.unlink()
                        except Exception:
                            pass
                    try:
                        base.rmdir()
                    except Exception:
                        pass
            except Exception as exc:
                logger.warning("Failed to clear persistent store: %s", exc)

    def persist(self, enable: bool) -> bool:
        """Enable/disable persistent vector memory. Returns True if persistence enabled."""
        if enable:
            # safety: do not initialize on Streamlit Cloud
            if os.environ.get("STREAMLIT_CLOUD") in {"1", "true", "True"}:
                logger.info("Running on Streamlit Cloud; persistent memory disabled by policy.")
                return False

            if FAISS is None or OpenAIEmbeddings is None:
                logger.warning("FAISS or OpenAIEmbeddings not available; cannot enable persistence.")
                return False

            settings = get_settings()
            api_key = (settings.openai_api_key or "").strip()
            if not api_key:
                logger.info("OPENAI_API_KEY not configured; cannot enable persistent memory.")
                return False

            try:
                embeddings = OpenAIEmbeddings(openai_api_key=api_key)
            except Exception as exc:
                logger.warning("Failed to initialize embeddings client: %s", exc)
                return False

            base_path = Path(self.cache_dir)
            base_path.mkdir(parents=True, exist_ok=True)
            store_path = base_path / f"faiss_{self.namespace}"

            try:
                if store_path.exists():
                    vs = FAISS.load_local(str(store_path), embeddings, allow_dangerous_deserialization=True)
                else:
                    vs = FAISS.from_texts([], embeddings)
                    vs.save_local(str(store_path))
            except Exception as exc:
                logger.warning("Failed to init FAISS store: %s", exc)
                return False

            self._vector_store = vs
            self._embeddings = embeddings
            self._persist_enabled = True
            return True

        else:
            # disable persistence
            self._persist_enabled = False
            self._vector_store = None
            self._embeddings = None
            return True

    def summarize_older(self) -> str:
        return self._summarize_older()

    def _summarize_older(self) -> str:
        # naive local summarization: take first sentence from each of the oldest N messages
        n = min(len(self._deque) // 2, self.summary_threshold)
        if n <= 0:
            return ""
        oldest = [self._deque.popleft() for _ in range(n)]
        # extract sentences heuristically
        sentences: List[str] = []
        for m in oldest:
            txt = self._as_text(m)
            parts = [p.strip() for p in txt.split(".") if p.strip()]
            if parts:
                sentences.append(parts[0])
        summary_text = "; ".join(sentences)[:1000]
        summary_entry = {"role": "system", "content": f"SUMMARY: {summary_text}", "meta": {"summarized_count": len(oldest)}}
        self._summaries.append(summary_entry)
        return summary_text

    def _as_text(self, msg: Dict[str, Any]) -> str:
        if isinstance(msg.get("content"), str):
            return msg["content"]
        try:
            return str(msg.get("content"))
        except Exception:
            return ""


def build_memory(namespace: str) -> AgentMemory:
    """Builds conversation memory and a MemoryManager (vector) instance.

    Returns an AgentMemory where `chat` is a ConversationBufferMemory for LangChain
    compatibility and `vector` is the MemoryManager instance (or None).
    """
    if ConversationBufferMemory is None:
        raise RuntimeError("LangChain não está instalado. Execute `poetry install`.")

    chat_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # create MemoryManager (vector) in ephemeral mode by default
    mem_mgr = MemoryManager(namespace=namespace, mode="ephemeral", max_items=200, summary_threshold=100)

    # For backward compatibility: if FAISS+OpenAIEmbeddings available and env allows, we keep vector store None until persist()
    return AgentMemory(chat=chat_memory, vector=mem_mgr)

