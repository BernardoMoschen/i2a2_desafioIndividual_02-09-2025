"""Adapter that wraps an AgentExecutor and provides a streaming interface.

If the underlying model/agent does not support streaming, a fallback
generator will synchronously call the agent and yield the text in chunks.
"""
from __future__ import annotations

from typing import Any, Generator, Iterable


class AgentAdapter:
    def __init__(self, executor: Any):
        self._executor = executor

    def invoke(self, payload: Any) -> Any:
        # preserve existing sync interface
        if hasattr(self._executor, "invoke"):
            return self._executor.invoke(payload)
        if hasattr(self._executor, "run"):
            return self._executor.run(payload)
        # last resort: try calling as callable
        return self._executor(payload)

    def invoke_stream(self, payload: Any, chunk_size: int = 200) -> Iterable[str]:
        """Yield chunks of the response text.

        If the underlying executor exposes a streaming API, prefer that.
        Otherwise call the sync invoke and yield chunks of text.
        """
        # Try to detect streaming-capable model (LangChain chat models often have 'stream' kw)
        # We intentionally keep this generic: if executor has 'invoke_stream' use it.
        if hasattr(self._executor, "invoke_stream"):
            try:
                for chunk in self._executor.invoke_stream(payload):
                    yield chunk
                return
            except Exception:
                # Fall back to sync path
                pass

        # Sync fallback: call invoke and chunk the text
        result = self.invoke(payload)
        # If the agent returns a dict-like structured answer, try to extract text
        text = None
        if isinstance(result, str):
            text = result
        elif isinstance(result, dict):
            # common keys: 'output', 'text', 'result', 'final_answer'
            for k in ("output", "text", "result", "final_answer", "Final Answer"):
                if k in result and isinstance(result[k], str):
                    text = result[k]
                    break
            # fallback to stringifying
            if text is None:
                text = str(result)
        else:
            text = str(result)

        # Yield in chunks
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
