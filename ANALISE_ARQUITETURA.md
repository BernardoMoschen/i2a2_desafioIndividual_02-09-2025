# Análise do Código — Framework e Estrutura da Solução

## 1. Framework escolhida

### Framework principal

A solução utiliza o **LangChain** como framework central para construção do agente conversacional/autônomo e orquestração de chamadas a ferramentas. A integração com provedores de LLM é feita via adaptadores específicos (ex.: OpenAI, Gemini).

Principais dependências relacionadas a agentes:

- `langchain` (core)
- `langchain-openai` (integração OpenAI)
- `langchain-google-genai` (integração Gemini)
- `langchain-community` / `langgraph` (quando presente, para orquestração adicional)

### Bibliotecas de apoio

- Processamento de dados: `polars` (preferencial) e `pandas` (fallback)
- NumPy: `numpy`
- Visualização: `plotly`, `matplotlib`, `seaborn`
- ML / estatística: `scikit-learn`, `pyod` (detecção de anomalias)
- Infra: `streamlit` (UI), `fastapi` (API REST), `duckdb` (cache/persistência)

---

## 2. Como a solução foi estruturada

A solução está organizada em camadas claras e modulares, o que facilita manutenção e extensão.

```
┌─────────────────────────────────────────────────────┐
│           INTERFACES DE USUÁRIO                     │
├─────────────────────────────────────────────────────┤
│  • Streamlit (`frontend/app.py`)                    │
│  • CLI (`src/cli.py`)                               │
│  • FastAPI REST (`src/api/main.py`)                 │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│              CAMADA DE AGENTES                      │
├─────────────────────────────────────────────────────┤
│  `src/agents/csv_agent.py`                          │
│  • `build_agent()` - cria o agente LangChain         │
│  • `build_tools()` - registra ferramentas            │
│  • `AgentConfig` - configuração do agente           │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│           FERRAMENTAS DO AGENTE (Tools)             │
├─────────────────────────────────────────────────────┤
│  1. `info_colunas`          - Descobre colunas      │
│  2. `descrever_dataset`     - Estatísticas básicas  │
│  3. `histograma`            - Gráfico de distribuição│
│  4. `dispersao`             - Scatter plot          │
│  5. `anomalias`             - Detecta outliers      │
│  6. `importancia_features`  - Feature importance    │
│  7. `executar_codigo_python`- Código Python arbitrário│
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│         CAMADA DE FERRAMENTAS ESPECIALIZADAS        │
├─────────────────────────────────────────────────────┤
│  `src/tools/`                                       │
│  • `stats_tool.py`  - Estatísticas descritivas      │
│  • `chart_tool.py`  - Geração de gráficos (Plotly)  │
│  • `feature_tool.py` - Importância de features      │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│            CAMADA DE PIPELINES                      │
├─────────────────────────────────────────────────────┤
│  `src/pipelines/`                                   │
│  • `ingestion.py`      - Carrega CSV com Polars/Pandas│
│  • `visualization.py`  - Cria/exporta figuras (Plotly)|
│  • `utils.py`          - Helpers e conversões       │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│       CONFIGURAÇÃO E PERSISTÊNCIA                   │
├─────────────────────────────────────────────────────┤
│  • `src/config.py`     - Pydantic Settings + dotenv  │
│  • `DuckDB`            - Cache de análises           │
│  • `/tmp/i2a2_reports/`- Armazena gráficos (HTML/PNG)│
└─────────────────────────────────────────────────────┘
```

### Fluxo de execução (exemplo)

1. Usuário carrega CSV via Streamlit (`frontend/app.py`).
2. Pipeline de ingestão (`src/pipelines/ingestion.py`) detecta delimitador e usa Polars (ou Pandas) para carregar os dados.
3. `build_agent()` cria um agente LangChain com ferramentas especializadas.
4. Usuário faz uma pergunta (ex.: "crie um gráfico de dispersão das primeiras 3 colunas").
5. Agente chama `info_colunas()` → decide usar `dispersao()`.
6. `chart_tool.build_scatter()` cria a figura (Plotly) e `visualization.export_figure()` salva em `/tmp/i2a2_reports/`.
7. A ferramenta retorna uma mensagem contendo a linha `**📊 Arquivo:** /tmp/i2a2_reports/arquivo.html`.
8. O frontend (`frontend/app.py`) detecta esse padrão por regex e renderiza o HTML via `st.components.v1.html()`.

---

## Componentes principais (resumo)

- `src/agents/csv_agent.py` — construção do agente, prompt do sistema, ferramentas como `StructuredTool` com schemas Pydantic.
- `src/tools/*.py` — implementações das ferramentas de análise e visualização (`stats_tool`, `chart_tool`, `anomaly_tool`, etc.).
- `src/pipelines/*.py` — ingestão e utilitários para conversão entre Polars/Pandas e preparação para visualização.
- `frontend/app.py` — interface Streamlit com detection/renderer de saídas do agente (textos, blocos de código, gráficos em `/tmp/i2a2_reports`).
- `src/config.py` — configuração via Pydantic Settings e `dotenv`.

---

## Características arquiteturais

- **Modularidade:** Camadas separadas (UI, agentes, tools, pipelines) permitem extensão e testes isolados.
- **Flexibilidade:** Suporte a múltiplos LLMs (OpenAI/Gemini), Polars/Pandas, ferramentas padrão + execução de código Python arbitrário.
- **Observabilidade:** Logs, modo verbose e possibilidades de debug (captura de caminhos, mensagens de erro detalhadas).
- **Persistência:** Exportação de gráficos para `/tmp/i2a2_reports/` e cache via DuckDB.

---

## Interfaces e execução

### Streamlit (UI)

Executa a interface de chat e visualização:

```bash
streamlit run frontend/app.py
```

### CLI

Exemplo de uso via CLI:

```bash
python -m src.cli ask data/input/creditcard.csv "Quais colunas têm maior correlação com fraude?" --provider gemini
```

### API (FastAPI)

Exemplo de execução:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8080
```

---

## Resumo técnico (tabela)

|                Aspecto | Tecnologia / Observação                            |
| ---------------------: | :------------------------------------------------- |
|   Framework de agentes | LangChain (+ adaptações para tool-calling)         |
|        LLMs suportados | OpenAI, Gemini                                     |
| Processamento de dados | Polars (preferencial), Pandas (fallback)           |
|           Visualização | Plotly, Matplotlib, Seaborn                        |
|         ML / Anomalias | scikit-learn, PyOD                                 |
|                     UI | Streamlit                                          |
|                    API | FastAPI                                            |
|                    CLI | Typer + Rich                                       |
|           Persistência | DuckDB, sistema de arquivos (`/tmp/i2a2_reports/`) |
|           Configuração | Pydantic Settings + dotenv                         |
