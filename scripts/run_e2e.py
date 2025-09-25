"""Script simples para validar ingestão e uma pergunta."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.agents.csv_agent import AgentConfig, build_agent
from src.pipelines.ingestion import load_dataset


def run(path: Path, question: str) -> None:
    ctx = load_dataset(path, lazy=False)
    agent = build_agent(ctx, AgentConfig())
    answer = agent.invoke({"input": question})
    print(answer)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fluxo end-to-end do agente")
    parser.add_argument("csv", type=Path, help="Caminho do arquivo CSV")
    parser.add_argument("question", type=str, help="Pergunta a ser feita ao agente")
    args = parser.parse_args()
    run(args.csv, args.question)


if __name__ == "__main__":
    main()
