"""Testes para o módulo de ingestão."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.pipelines.ingestion import DatasetContext, load_dataset


def test_load_dataset_creates_metadata(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["col_a", "col_b"])
        writer.writerow([1, 2])
        writer.writerow([3, 4])

    ctx = load_dataset(path, lazy=False)
    assert isinstance(ctx, DatasetContext)
    assert ctx.metadata.num_rows == 2
    assert ctx.metadata.num_columns == 2
    assert set(ctx.metadata.columns) == {"col_a", "col_b"}


def test_load_dataset_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        load_dataset(missing)
