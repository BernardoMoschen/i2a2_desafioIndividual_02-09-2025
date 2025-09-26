"""Pipeline de geração de gráficos com Plotly."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from src.config import get_settings

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


def _ensure_dataframe(data: Any) -> Any:
    if pl is not None and isinstance(data, pl.DataFrame):
        return data.to_pandas()
    if pd is not None and isinstance(data, pd.DataFrame):
        return data
    raise VisualizationError("Formato de dados não suportado para visualização")


def create_histogram(data: Any, column: str, *, title: Optional[str] = None) -> Any:
    _ensure_plotly()
    df = _ensure_dataframe(data)
    fig = px.histogram(df, x=column, title=title or f"Distribuição de {column}")
    return fig


def create_scatter(data: Any, x: str, y: str, color: Optional[str] = None, *, title: Optional[str] = None) -> Any:
    _ensure_plotly()
    df = _ensure_dataframe(data)
    fig = px.scatter(df, x=x, y=y, color=color, title=title or f"Dispersão {x} x {y}")
    return fig


def export_figure(fig: Any, *, filename: str) -> Path:
    _ensure_plotly()
    settings = get_settings()
    output_dir = settings.reports_dir / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    path = output_dir / filename
    fig.write_image(path.with_suffix(".png"))
    fig.write_html(path.with_suffix(".html"))
    return path.with_suffix(".html")
