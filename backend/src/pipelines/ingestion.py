"""Funções de ingestão de CSVs com validações básicas."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from src.config import get_settings

try:  # pragma: no cover - import opcional
    import polars as pl
except ImportError:  # pragma: no cover - ambiente sem polars
    pl = None  # type: ignore

try:  # pragma: no cover - import opcional
    import pandas as pd
except ImportError:  # pragma: no cover - ambiente sem pandas
    pd = None  # type: ignore


@dataclass
class DatasetMetadata:
    """Informações resumidas sobre o dataset carregado."""

    path: Path
    num_rows: int
    num_columns: int
    columns: Iterable[str]
    delimiter: str
    size_in_bytes: int


@dataclass
class DatasetContext:
    """Representa o dataset carregado e suas metainformações."""

    data: Any
    metadata: DatasetMetadata


def _detect_delimiter(sample: str) -> str:
    sniffer = csv.Sniffer()
    dialect = sniffer.sniff(sample)
    return dialect.delimiter


def _read_sample(path: Path, sample_size: int = 8192) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.read(sample_size)


def load_dataset(path: Path, *, lazy: bool = True) -> DatasetContext:
    """Carrega um arquivo CSV utilizando a melhor engine disponível.

    Args:
        path: caminho do arquivo CSV.
        lazy: se `True`, tenta utilizar leitura preguiçosa (lazy) quando suportado.
    """

    if not path.exists():
        raise FileNotFoundError(path)

    settings = get_settings()
    data_dir = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    sample = _read_sample(path)
    delimiter = _detect_delimiter(sample)

    if pl is not None:
        if lazy:
            data = pl.scan_csv(path, separator=delimiter, ignore_errors=True)
        else:
            data = pl.read_csv(path, separator=delimiter, ignore_errors=True)
        num_rows = data.collect().height if lazy else data.height
        num_columns = len(data.columns)
        columns = data.columns

    elif pd is not None:
        data = pd.read_csv(path, sep=delimiter, encoding_errors="ignore")
        num_rows, num_columns = data.shape
        columns = list(data.columns)

    else:  # fallback minimalista
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            rows = list(reader)
        data = rows
        num_rows = len(rows)
        num_columns = len(rows[0]) if rows else 0
        columns = list(rows[0].keys()) if rows else []

    metadata = DatasetMetadata(
        path=path.resolve(),
        num_rows=num_rows,
        num_columns=num_columns,
        columns=columns,
        delimiter=delimiter,
        size_in_bytes=path.stat().st_size,
    )

    return DatasetContext(data=data, metadata=metadata)
