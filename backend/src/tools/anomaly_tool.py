"""Ferramenta de detecção de anomalias."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # pragma: no cover
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:  # pragma: no cover
    from sklearn.ensemble import IsolationForest
except ImportError:  # pragma: no cover
    IsolationForest = None  # type: ignore

try:  # pragma: no cover
    from langchain_core.tools import tool
except ImportError:  # pragma: no cover
    tool = None  # type: ignore

try:  # pragma: no cover
    import polars as pl
except ImportError:  # pragma: no cover
    pl = None  # type: ignore

try:  # pragma: no cover
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore


@dataclass
class AnomalyResult:
    contamination: float
    outlier_count: int
    impact_ratio: float


def _to_numpy(data: Any, columns: Optional[list[str]] = None):
    if pl is not None and isinstance(data, pl.DataFrame):
        df = data
        if columns is not None:
            df = df.select(columns)
        return df.to_numpy()
    if pd is not None and isinstance(data, pd.DataFrame):
        df = data
        if columns is not None:
            df = df[columns]
        return df.to_numpy()
    raise RuntimeError("Formato de dados não suportado para detecção de anomalias")


def detect_anomalies(data: Any, *, contamination: float = 0.05, columns: Optional[list[str]] = None) -> AnomalyResult:
    if IsolationForest is None or np is None:
        raise RuntimeError("scikit-learn e numpy são necessários para detecção de anomalias")

    matrix = _to_numpy(data, columns)
    if matrix.size == 0:
        raise ValueError("Dataset vazio ou colunas inválidas para detecção de anomalias")

    model = IsolationForest(contamination=contamination, random_state=42)
    predictions = model.fit_predict(matrix)
    outliers = predictions == -1
    outlier_count = int(outliers.sum())
    impact = outlier_count / len(predictions)
    return AnomalyResult(contamination=contamination, outlier_count=outlier_count, impact_ratio=impact)


if tool is not None:  # pragma: no cover

    @tool("detect_outliers")
    def detect_outliers_tool(dataset: Any, contamination: float = 0.05, columns: Optional[list[str]] = None) -> Dict[str, Any]:
        """Detecta outliers com Isolation Forest."""

        result = detect_anomalies(dataset, contamination=contamination, columns=columns)
        return {
            "contamination": result.contamination,
            "outlier_count": result.outlier_count,
            "impact_ratio": result.impact_ratio,
        }
