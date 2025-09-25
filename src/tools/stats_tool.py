"""Ferramenta de estatísticas descritivas para o agente."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # pragma: no cover - dependência opcional
    import polars as pl
except ImportError:  # pragma: no cover
    pl = None  # type: ignore

try:  # pragma: no cover
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore

try:  # pragma: no cover
    from langchain_core.tools import tool
except ImportError:  # pragma: no cover
    tool = None  # type: ignore


@dataclass
class StatsResult:
    summary: Dict[str, Any]
    message: str


def _to_dataframe(data: Any) -> Any:
    if pl is not None and isinstance(data, pl.DataFrame):
        return data
    if pd is not None and isinstance(data, pd.DataFrame):
        return data
    if pl is not None and isinstance(data, pl.LazyFrame):
        return data.collect()
    if pd is not None and isinstance(data, list):
        return pd.DataFrame(data)
    raise RuntimeError("Formato de dados não suportado para estatísticas")


def compute_basic_stats(data: Any) -> StatsResult:
    df = _to_dataframe(data)

    if pl is not None and isinstance(df, pl.DataFrame):
        summary = df.describe().to_pandas().set_index("describe").to_dict()
    elif pd is not None and isinstance(df, pd.DataFrame):
        summary = df.describe(include="all", datetime_is_numeric=True).fillna(0).to_dict()
    else:
        raise RuntimeError("Não foi possível calcular estatísticas - instale pandas ou polars")

    message = (
        "Estatísticas calculadas. Foco em média, desvio padrão e quartis para colunas numéricas. "
        "Colunas categóricas listam frequência e cardinalidade quando disponível."
    )
    return StatsResult(summary=summary, message=message)


if tool is not None:  # pragma: no cover - registra para LangChain se disponível

    @tool("describe_dataset")
    def describe_dataset_tool(dataset: Any) -> Dict[str, Any]:
        """Retorna resumo estatístico completo do dataset atual."""

        result = compute_basic_stats(dataset)
        return {"summary": result.summary, "message": result.message}
