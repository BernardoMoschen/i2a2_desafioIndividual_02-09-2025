# Agente Autônomo para Análise de CSVs

Este projeto implementa um agente inteligente baseado em LangChain/LangGraph capaz de ingerir arquivos CSV, executar análises exploratórias, detectar anomalias, gerar visualizações e sintetizar conclusões automaticamente. A solução foi desenhada para funcionar de forma independente, com memória e capacidade de responder a perguntas em linguagem natural.

## ✨ Principais Recursos

- **Ingestão inteligente de CSVs** com detecção automática de esquema, tratamento de valores ausentes e normalização.
- **Ferramentas analíticas especializadas** (estatísticas descritivas, correlações, detecção de outliers, gráficos interativos).
- **Agente multimodal** orquestrado com LangGraph, com memória curta e longa para reutilização de insights.
- **API REST e CLI** para interação humana ou integração com outras aplicações.
- **Containerização completa** via Docker e scripts de automação.
- **Relatório automatizado** para consolidar respostas e evidências exigidas pela atividade.

## 📂 Estrutura do Projeto

```
src/
  agents/            # Definições de agentes LangChain/LangGraph
  api/               # FastAPI (HTTP endpoints)
  memory/            # Estratégias de memória e persistência
  pipelines/         # Ingestão, pré-processamento e gráficos
  tools/             # Ferramentas analíticas expostas ao agente
  cli.py             # Interface de linha de comando (Typer)

scripts/             # Automação (bootstrap, e2e, geração de relatório)
data/                # Arquivos CSV de entrada e cache (ignored)
reports/             # Saída de relatórios PDF/HTML
```

## 🚀 Como começar

### 1. Preparar ambiente local (Poetry)

```bash
pip install --upgrade pip
pip install poetry
poetry install
cp .env.example .env
# preencha as chaves necessárias no arquivo .env
# LLM_PROVIDER=openai utiliza a API da OpenAI (requer OPENAI_API_KEY)
# LLM_PROVIDER=ollama usa um modelo local servido via Ollama
poetry run python scripts/bootstrap.sh
```

### 2. Executar a API

```bash
poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Utilizar a CLI

```bash
poetry run python -m src.cli ingest data/input/creditcard.csv
poetry run python -m src.cli ask data/input/creditcard.csv "Quais colunas apresentam maior correlação com fraude?"
# Para forçar o uso do Ollama local:
poetry run python -m src.cli ask data/input/creditcard.csv "Há outliers relevantes?" --provider ollama
poetry run python -m src.cli report
```

## 🐳 Docker Compose

1. No diretório raiz do repositório, construa e suba somente o backend:

```bash
docker compose up backend --build
```

2. Para rodar em segundo plano:

```bash
docker compose up backend --build -d
```

3. Quando terminar os testes, finalize os containers:

```bash
docker compose down
```

> A API ficará acessível em `http://localhost:8080/docs`.

> **Dica:** ao utilizar Docker + Ollama local, defina `OLLAMA_BASE_URL=http://host.docker.internal:11434` para permitir que o container se conecte ao serviço hospedado na máquina.

## 🧪 Testes e Qualidade

```bash
poetry run pytest
poetry run ruff check src
poetry run mypy src
```

## 📄 Relatório da Atividade

- O relatório final `Agentes Autônomos – Relatório da Atividade Extra.pdf` é gerado pelo script `scripts/build_report.py`, compilando perguntas, respostas, gráficos e conclusões.

## 🔒 Boas Práticas

- Nunca comitar chaves de API (`.env` está no `.gitignore`).
- Utilize LangSmith para monitorar custos e qualidade (`LANGCHAIN_TRACING_V2=true`).
- Execute análises com datasets diversos para validar generalização.

## ✅ Checklist de Entrega

- [ ] Código final versionado.
- [ ] Docker build + compose testados.
- [ ] Relatório PDF atualizado em `reports/`.
- [ ] Link público do agente (deploy) inserido no relatório.
- [ ] E-mail de envio conforme instruções.

---

Para detalhes adicionais sobre requisitos e arquitetura, consulte `atividadeObrigatoria_02-09-25.md`.
