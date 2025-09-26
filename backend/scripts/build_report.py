"""Gera um rascunho de relatório em Markdown."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

TEMPLATE = """# Agentes Autônomos – Relatório da Atividade Extra

_Data gerado em {generated_at}_

## 1. Framework escolhida
- LangChain / LangGraph
- Bibliotecas de apoio: Polars, Plotly, scikit-learn

## 2. Estrutura da solução
```
{tree}
```

## 3. Perguntas respondidas
{questions_block}

## 4. Conclusões principais
{conclusions_block}

## 5. Links úteis
- API: {api_url}
- Código fonte: {repo_url}

## 6. Apêndice
- Caminho do dataset analisado: {dataset_path}
- Estatísticas básicas: {stats_json}

> Converta este arquivo para PDF com `pandoc` ou Google Docs antes da entrega oficial.
"""


def render_tree(root: Path) -> str:
    items: List[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        items.append(str(relative))
    return "\n".join(items)


def build_report(
    dataset_path: Path,
    stats_json: str = "{}",
    questions_block: str = "- Pergunta 1: ...",
    conclusions_block: str = "- Insight 1: ...",
    api_url: str = "http://localhost:8080/docs",
    repo_url: str = "https://github.com/seu-usuario/i2a2-DesafioIndividual",
    output: Path | None = None,
) -> Path:
    root = Path.cwd()
    tree = render_tree(root / "src")
    output = output or Path("reports/Agentes Autônomos – Relatório da Atividade Extra.md")
    output.parent.mkdir(parents=True, exist_ok=True)

    content = TEMPLATE.format(
        generated_at=datetime.utcnow().isoformat(),
        tree=tree,
        questions_block=questions_block,
        conclusions_block=conclusions_block,
        api_url=api_url,
        repo_url=repo_url,
        dataset_path=dataset_path,
        stats_json=stats_json,
    )

    output.write_text(content, encoding="utf-8")
    return output


if __name__ == "__main__":
    path = build_report(Path("data/input/creditcard.csv"))
    print(f"Relatório gerado em {path}")
