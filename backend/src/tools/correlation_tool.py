"""Ferramenta de correlação: calcula matrizes e exporta heatmap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore

try:
    from langchain_core.tools import tool
except ImportError:  # pragma: no cover
    tool = None  # type: ignore

from src.pipelines.visualization import create_correlation_heatmap, export_figure
from src.pipelines.utils import to_pandas_for_viz


@dataclass
class CorrelationResult:
    matrix: Dict[str, Dict[str, float]]
    top_pairs: List[Tuple[str, str, float]]
    plot_path: Optional[str]


def _ensure_dataframe(data: Any) -> "pd.DataFrame":
    if pd is None:
        raise RuntimeError("Pandas não está instalado")
    if isinstance(data, pd.DataFrame):
        return data
    # try to coerce list of dicts
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return pd.DataFrame(data)
    raise RuntimeError("Formato de dados não suportado para correlação")


def compute_correlations(data: Any, method: str = "pearson", top_k: int = 10, sample_n: Optional[int] = None) -> CorrelationResult:
    # Convert data to pandas with optional sampling. By default sample_n=None -> full dataset.
    df = to_pandas_for_viz(data, sample_n=sample_n)
    # select numeric columns only
    numeric = df.select_dtypes(include=["number"]).copy()
    if numeric.shape[1] == 0:
        raise ValueError("Nenhuma coluna numérica disponível para correlação")

    if method not in {"pearson", "spearman"}:
        raise ValueError("Método deve ser 'pearson' ou 'spearman'")

    corr = numeric.corr(method=method)
    matrix = corr.fillna(0).to_dict()

    # top pairs by absolute correlation (exclude self-correlations)
    pairs: List[Tuple[str, str, float]] = []
    cols = corr.columns.tolist()
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if j <= i:
                continue
            val = float(corr.iloc[i, j])
            pairs.append((a, b, val))
    pairs_sorted = sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    top_pairs = pairs_sorted[:top_k]

    # generate heatmap
    try:
        fig = create_correlation_heatmap(numeric, method=method)
        plot_path = export_figure(fig, filename=f"corr_{method}")
    except Exception:
        plot_path = None

    return CorrelationResult(matrix=matrix, top_pairs=top_pairs, plot_path=str(plot_path) if plot_path else None)


if tool is not None:  # pragma: no cover

    @tool("correlation")
    def correlation_tool(dataset: Any, method: str = "pearson", top_k: int = 10) -> Dict[str, Any]:
        """Computa matriz de correlação e gera heatmap."""

        result = compute_correlations(dataset, method=method, top_k=top_k)
        return {
            "matrix": result.matrix,
            "top_pairs": [list(t) for t in result.top_pairs],
            "plot": result.plot_path,
        }
