"""Construção do agente especializado em CSV."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from src.agents.model_factory import create_chat_model
from src.config import get_settings
from src.memory.store import build_memory
from src.pipelines.ingestion import DatasetContext
from src.tools import anomaly_tool, chart_tool, stats_tool

try:  # pragma: no cover
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.tools import Tool
except ImportError:  # pragma: no cover
    AgentExecutor = None  # type: ignore
    create_tool_calling_agent = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore
    Tool = None  # type: ignore

if AgentExecutor is None:  # pragma: no cover - typing fallback
    AgentExecutor = Any  # type: ignore
if Tool is None:  # pragma: no cover - typing fallback
    Tool = Any  # type: ignore


@dataclass
class AgentConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_steps: int = 8
    use_memory: bool = True
    provider: str = "openai"
    request_timeout: float = 120.0

    @classmethod
    def from_settings(cls):
        settings = get_settings()
        model = (
            settings.default_model
            if settings.llm_provider.lower() != "ollama"
            else settings.ollama_model
        )
        return cls(
            model=model,
            temperature=settings.model_temperature,
            max_steps=8,
            use_memory=True,
            provider=settings.llm_provider.lower(),
            request_timeout=settings.model_request_timeout,
        )


PROMPT_TEMPLATE = """
Você é um analista de dados experiente. Analise o dataset disponível respondendo em português, citando
as etapas executadas e mencionando os gráficos gerados quando aplicável. Seja transparente sobre
limitacoes, utilize sempre as ferramentas apropriadas antes de responder e finalize com um resumo
em bullet points.
"""


def _require_dependencies():
    if any(dep is None for dep in (AgentExecutor, create_tool_calling_agent, ChatPromptTemplate, Tool)):
        raise RuntimeError(
            "Dependências do LangChain/LangGraph não encontradas. Execute `poetry install` antes de usar o agente."
        )


def _tool(name: str, description: str, func: Callable[..., Any]) -> Any:
    _require_dependencies()
    return Tool.from_function(name=name, description=description, func=func)


def build_tools(dataset: DatasetContext) -> List[Any]:
    def describe() -> Dict[str, Any]:
        result = stats_tool.compute_basic_stats(dataset.data)
        return {"summary": result.summary, "message": result.message}

    def histogram(column: str) -> str:
        return chart_tool.build_histogram(dataset.data, column)

    def scatter(x: str, y: str, color: str | None = None) -> str:
        return chart_tool.build_scatter(dataset.data, x=x, y=y, color=color)

    def anomalies(contamination: float = 0.05) -> Dict[str, Any]:
        result = anomaly_tool.detect_anomalies(dataset.data, contamination=contamination)
        return {
            "contamination": result.contamination,
            "outlier_count": result.outlier_count,
            "impact_ratio": result.impact_ratio,
        }

    return [
        _tool("descrever_dataset", "Resumo estatístico completo do dataset atual.", describe),
        _tool(
            "histograma",
            "Gera histograma para uma coluna numérica. Informe o nome da coluna.",
            histogram,
        ),
        _tool(
            "dispersao",
            "Cria gráfico de dispersão entre duas colunas numéricas.",
            scatter,
        ),
        _tool(
            "anomalias",
            "Detecta outliers usando Isolation Forest e retorna impacto percentual.",
            anomalies,
        ),
    ]


def build_agent(dataset: DatasetContext, config: AgentConfig | None = None) -> Any:
    _require_dependencies()
    if config is None:
        config = AgentConfig.from_settings()

    llm = create_chat_model(
        provider=config.provider.lower(),
        model=config.model,
        temperature=config.temperature,
        request_timeout=config.request_timeout,
    )
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    tools = build_tools(dataset)
    agent = create_tool_calling_agent(llm, tools, prompt)

    memory = None
    if config.use_memory:
        memory = build_memory(dataset.metadata.path.stem)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=config.max_steps,
        memory=memory.chat if memory else None,
    )

    return executor
