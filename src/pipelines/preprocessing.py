"""Funções auxiliares de pré-processamento."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - import opcional
    import polars as pl
except ImportError:  # pragma: no cover
    pl = None  # type: ignore

try:  # pragma: no cover
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore


@dataclass
class PreparedData:
    """Carrega o dataframe normalizado e metainformações."""

    dataframe: Any
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]


NUMERIC_KINDS = {"i", "u", "f"}


def _ensure_dataframe(data: Any) -> Any:
    if pl is not None and isinstance(data, pl.LazyFrame):
        return data.collect()
    if pl is not None and isinstance(data, pl.DataFrame):
        return data
    if pd is not None and isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, list) and data and isinstance(data[0], dict):
        if pd is None:
            raise RuntimeError("Pandas necessário para converter lista de dicts em DataFrame")
        return pd.DataFrame(data)
    raise TypeError(f"Formato de dados não suportado: {type(data)!r}")


def prepare_dataframe(data: Any, *, dropna_threshold: float = 0.4) -> PreparedData:
    """Normaliza o dataset removendo colunas com excesso de valores nulos."""

    df = _ensure_dataframe(data)

    if pl is not None and isinstance(df, pl.DataFrame):
        na_ratio = df.null_count() / df.height if df.height else 0
        cols_to_keep = [col for col, ratio in zip(df.columns, na_ratio) if ratio <= dropna_threshold]
        df = df.select(cols_to_keep)
        numeric = [c for c, dt in zip(df.columns, df.dtypes) if getattr(dt, "is_numeric", lambda: False)()]
        datetime_cols = [c for c, dt in zip(df.columns, df.dtypes) if str(dt) in {"date", "datetime"}]
        categorical = [c for c in df.columns if c not in numeric and c not in datetime_cols]
        return PreparedData(df, numeric, categorical, datetime_cols)

    if pd is not None and isinstance(df, pd.DataFrame):
        na_ratio = df.isna().mean()
        cols_to_keep = [col for col in df.columns if na_ratio[col] <= dropna_threshold]
        df = df[cols_to_keep]
        numeric = df.select_dtypes(include=["number"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
        categorical = [c for c in df.columns if c not in numeric and c not in datetime_cols]
        return PreparedData(df, numeric, categorical, datetime_cols)

    raise RuntimeError("Não foi possível preparar o dataframe - dependências ausentes")
