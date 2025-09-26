"""Interface de linha de comando para o agente."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from src.agents.csv_agent import AgentConfig, build_agent
from src.config import get_settings
from src.pipelines.ingestion import load_dataset

app = typer.Typer(help="Ferramentas CLI para o agente de análise de CSV")


def _print_json(payload):
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@app.command()
def ingest(path: Path) -> None:
    """Carrega um CSV e exibe metadados básicos."""

    ctx = load_dataset(path, lazy=False)
    _print_json(
        {
            "path": str(ctx.metadata.path),
            "rows": ctx.metadata.num_rows,
            "columns": ctx.metadata.num_columns,
            "delimiter": ctx.metadata.delimiter,
        }
    )


@app.command()
def ask(
    path: Path,
    question: str,
    model: Optional[str] = typer.Option(None, help="Modelo a ser utilizado"),
    provider: Optional[str] = typer.Option(None, help="Provedor do LLM (openai ou ollama)"),
) -> None:
    """Faz uma pergunta ao agente usando um CSV local."""

    ctx = load_dataset(path, lazy=False)
    settings = get_settings()
    config = AgentConfig.from_settings()
    if model:
        config.model = model
    if provider:
        provider = provider.lower()
        config.provider = provider
        if not model:
            config.model = settings.ollama_model if provider.lower() == "ollama" else settings.default_model

    try:
        agent = build_agent(ctx, config)
    except RuntimeError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    answer = agent.invoke({"input": question})
    _print_json(answer)


@app.command()
def report(path: Path, output: Optional[Path] = None) -> None:
    """Gera relatório provisório com estatísticas e insights do CSV."""

    ctx = load_dataset(path, lazy=False)
    stats = ctx.metadata
    output = output or Path("reports") / "quick_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "dataset": stats.path.name,
        "rows": stats.num_rows,
        "columns": stats.num_columns,
        "notes": [
            "Execute scripts/build_report.py para o relatório oficial.",
            "Utilize a CLI 'ask' para coletar respostas das quatro perguntas obrigatórias.",
        ],
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.secho(f"Relatório rápido salvo em {output}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
