"""Ferramenta de geração de gráficos."""

from __future__ import annotations

from typing import Any, Optional

try:  # pragma: no cover
    from langchain_core.tools import tool
except ImportError:  # pragma: no cover
    tool = None  # type: ignore

from src.pipelines import visualization


def build_histogram(dataset: Any, column: str, *, title: Optional[str] = None) -> str:
    fig = visualization.create_histogram(dataset, column, title=title)
    path = visualization.export_figure(fig, filename=f"hist_{column}")
    return str(path)


def build_scatter(dataset: Any, x: str, y: str, *, color: Optional[str] = None, title: Optional[str] = None) -> str:
    fig = visualization.create_scatter(dataset, x=x, y=y, color=color, title=title)
    path = visualization.export_figure(fig, filename=f"scatter_{x}_{y}")
    return str(path)


if tool is not None:  # pragma: no cover

    @tool("draw_histogram")
    def histogram_tool(dataset: Any, column: str, title: Optional[str] = None) -> str:
        """Gera histograma para uma coluna numérica."""

        return build_histogram(dataset, column, title=title)

    @tool("draw_scatter")
    def scatter_tool(dataset: Any, x: str, y: str, color: Optional[str] = None, title: Optional[str] = None) -> str:
        """Cria gráfico de dispersão entre X e Y com cor opcional."""

        return build_scatter(dataset, x, y, color=color, title=title)
