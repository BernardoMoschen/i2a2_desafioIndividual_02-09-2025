"""Utility helpers for pipelines (conversion and safe sampling).

Provides a helper to convert Polars/Pandas/list-of-dicts into a pandas.DataFrame
suitable for visualization and modelling. Sampling is optional and disabled by
default (the full dataset is returned unless the caller requests a sample).
"""
from __future__ import annotations

from typing import Any, Optional

try:
    import polars as pl
except Exception:  # pragma: no cover - optional
    pl = None  # type: ignore

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional
    pd = None  # type: ignore


def to_pandas_for_viz(data: Any, *, sample_n: Optional[int] = None, random_state: int = 42) -> "pd.DataFrame":
    """Return a pandas.DataFrame for visualization.

    Args:
        data: a polars.DataFrame/LazyFrame, pandas.DataFrame or list-of-dicts.
        sample_n: optional number of rows to sample. If None (default), the
            full dataset is returned. If the dataset has <= sample_n rows the
            full dataset is returned as well.
        random_state: seed for reproducible sampling.

    Raises:
        RuntimeError: when pandas is not available or the input format is
            unsupported.
    """
    if pd is None:
        raise RuntimeError("Pandas não está instalado")

    # Polars path
    if pl is not None and isinstance(data, pl.DataFrame):
        df = data.to_pandas()
    elif pl is not None and hasattr(pl, "LazyFrame") and isinstance(data, pl.LazyFrame):
        # collect lazy frame
        df = data.collect().to_pandas()
    elif pd is not None and isinstance(data, pd.DataFrame):
        df = data
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        df = pd.DataFrame(data)
    else:
        # last resort: if it's an empty list or unknown structure try to coerce
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            raise RuntimeError("Formato de dados não suportado para conversão em pandas")

    # If sampling requested and dataset larger than sample_n, apply sampling.
    if sample_n is not None:
        try:
            nrows = len(df)
        except Exception:
            nrows = getattr(df, "shape", (0, 0))[0]
        if nrows > sample_n:
            df = df.sample(n=sample_n, random_state=random_state)

    # reset index for a clean dataframe for Plotly/ML codepaths
    df = df.reset_index(drop=True)
    return df
