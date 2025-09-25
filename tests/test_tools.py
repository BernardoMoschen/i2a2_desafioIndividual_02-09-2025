"""Testes básicos das ferramentas."""

from __future__ import annotations

from typing import Any

import pytest

pd = pytest.importorskip("pandas")

from src.tools.stats_tool import compute_basic_stats


def test_compute_basic_stats_with_pandas() -> None:
    df = pd.DataFrame({"value": [1, 2, 3, 4]})
    result = compute_basic_stats(df)
    assert "value" in result.summary
    stats = result.summary["value"]
    assert pytest.approx(stats.get("mean", 0), 0.1) == 2.5
