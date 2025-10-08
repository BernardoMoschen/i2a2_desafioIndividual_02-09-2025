"""Pipeline de geração de gráficos com Plotly."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from src.config import get_settings
from src.pipelines.utils import to_pandas_for_viz

try:  # pragma: no cover - dependência opcional
    import plotly.express as px
except ImportError:  # pragma: no cover
    px = None  # type: ignore

try:  # pragma: no cover
    import polars as pl
except ImportError:  # pragma: no cover
    pl = None  # type: ignore

try:  # pragma: no cover
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore


class VisualizationError(RuntimeError):
    """Erro específico do módulo de visualização."""


def _ensure_plotly():
    if px is None:
        raise VisualizationError("Plotly não está instalado. Execute `poetry install`.")


def _ensure_dataframe(data: Any, *, sample_n: Optional[int] = None) -> Any:
    # Use the central helper which supports polars/pandas/list-of-dicts and optional sampling.
    return to_pandas_for_viz(data, sample_n=sample_n)


def create_histogram(data: Any, column: str, *, title: Optional[str] = None, sample_n: Optional[int] = None) -> Any:
    _ensure_plotly()
    df = _ensure_dataframe(data, sample_n=sample_n)
    fig = px.histogram(df, x=column, title=title or f"Distribuição de {column}")
    return fig


def create_scatter(data: Any, x: str, y: str, color: Optional[str] = None, *, title: Optional[str] = None, sample_n: Optional[int] = None) -> Any:
    _ensure_plotly()
    df = _ensure_dataframe(data, sample_n=sample_n)
    fig = px.scatter(df, x=x, y=y, color=color, title=title or f"Dispersão {x} x {y}")
    return fig


def create_correlation_heatmap(data: Any, *, method: str = "pearson", title: Optional[str] = None, sample_n: Optional[int] = None) -> Any:
    _ensure_plotly()
    df = _ensure_dataframe(data, sample_n=sample_n)
    numeric = df.select_dtypes(include=["number"]) if hasattr(df, "select_dtypes") else df
    corr = numeric.corr(method=method)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu", origin="lower", title=title or f"Matriz de correlação ({method})")
    return fig


def export_figure(fig: Any, *, filename: str) -> Path:
    _ensure_plotly()
    settings = get_settings()
    # Use a temporary directory for cloud-friendly exports (Streamlit Cloud doesn't guarantee filesystem persistence)
    import tempfile

    temp_dir = Path(tempfile.gettempdir()) / "i2a2_reports"
    temp_dir.mkdir(parents=True, exist_ok=True)

    path = temp_dir / filename
    # write image if kaleido/wheels available, otherwise just write html
    try:
        fig.write_image(path.with_suffix(".png"))
    except Exception:
        pass
    try:
        fig.write_html(path.with_suffix(".html"))
        return path.with_suffix(".html")
    except Exception:
        # Last resort: return path to PNG if available
        return path.with_suffix(".png")
