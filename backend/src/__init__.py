"""Pacote raiz para o agente autônomo de análise de CSVs."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("i2a2-autonomous-agent")
except PackageNotFoundError:  # pragma: no cover - durante desenvolvimento local
    __version__ = "0.0.0"
