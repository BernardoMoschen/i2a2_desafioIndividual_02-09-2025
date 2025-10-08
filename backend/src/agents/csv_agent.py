"""Construção do agente especializado em CSV."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Callable, Dict, List, Optional

from src.agents.model_factory import create_chat_model
from src.config import get_settings
from src.memory.store import build_memory
from src.pipelines.ingestion import DatasetContext
from src.tools import anomaly_tool, chart_tool, stats_tool
try:
    from src.tools import feature_tool
except Exception:  # pragma: no cover - optional
    feature_tool = None  # type: ignore

try:  # pragma: no cover
    from langchain.agents import (
        AgentExecutor,
        create_react_agent,
        create_tool_calling_agent,
    )
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
    from langchain_core.tools import Tool, StructuredTool
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover
    AgentExecutor = None  # type: ignore
    create_react_agent = None  # type: ignore
    create_tool_calling_agent = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore
    MessagesPlaceholder = None  # type: ignore
    PromptTemplate = None  # type: ignore
    Tool = None  # type: ignore
    StructuredTool = None  # type: ignore
    BaseModel = None  # type: ignore
    Field = None  # type: ignore

if AgentExecutor is None:  # pragma: no cover - typing fallback
    AgentExecutor = Any  # type: ignore
if create_react_agent is None:  # pragma: no cover - typing fallback
    create_react_agent = Any  # type: ignore
if Tool is None:  # pragma: no cover - typing fallback
    Tool = Any  # type: ignore
if MessagesPlaceholder is None:  # pragma: no cover - typing fallback
    MessagesPlaceholder = Any  # type: ignore


@dataclass
class AgentConfig:
    model: str = "gpt-5-nano"
    temperature: float = 0.0
    max_steps: int = 8
    use_memory: bool = True
    provider: str = "openai"
    request_timeout: float = 120.0

    @classmethod
    def from_settings(cls):
        settings = get_settings()
        model = settings.default_model
        return cls(
            model=model,
            temperature=settings.model_temperature,
            max_steps=8,
            use_memory=True,
            provider=settings.llm_provider.lower(),
            request_timeout=settings.model_request_timeout,
        )


PROMPT_TEMPLATE = dedent(
    """
    Você é um analista de dados experiente. Analise o dataset disponível respondendo em português, citando
    as etapas executadas e mencionando os gráficos gerados quando aplicável. Seja transparente sobre
    limitações, utilize sempre as ferramentas apropriadas antes de responder e finalize com um resumo
    em bullet points.

        Você tem acesso às seguintes ferramentas: (as ferramentas disponíveis serão fornecidas pelo sistema e devem ser usadas quando apropriado)

    Use o seguinte formato:

    Thought: você deve sempre pensar sobre o que fazer
    Action: a ação a tomar, deve ser uma das ferramentas fornecidas pelo sistema
    Action Input: a entrada para a ação
    Observation: o resultado da ação

    ... (este Thought/Action/Action Input/Observation pode se repetir N vezes)

    Thought: agora sei a resposta final
    Final Answer: a resposta final para a pergunta de entrada original
    """
).strip()


def _require_dependencies():
    if any(
        dep is None
        for dep in (
            AgentExecutor,
            create_react_agent,
            create_tool_calling_agent,
            ChatPromptTemplate,
            MessagesPlaceholder,
            Tool,
        )
    ):
        raise RuntimeError(
            "Dependências do LangChain/LangGraph não encontradas. Execute `poetry install` antes de usar o agente."
        )


def _tool(name: str, description: str, func: Callable[..., Any]) -> Any:
    _require_dependencies()
    return Tool.from_function(name=name, description=description, func=func)


def build_tools(dataset: DatasetContext) -> List[Any]:
    """Constrói ferramentas com validação de colunas."""
    
    # Obter informações das colunas do dataset
    data = dataset.data
    all_columns = list(dataset.metadata.columns)
    
    # Tentar identificar colunas numéricas
    numeric_columns = []
    try:
        if hasattr(data, 'select_dtypes'):  # pandas
            numeric_columns = data.select_dtypes(include=['number']).columns.tolist()
        elif hasattr(data, 'schema'):  # polars
            import polars as pl
            numeric_types = [pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float32, pl.Float64]
            numeric_columns = [col for col, dtype in data.schema.items() if dtype in numeric_types]
        else:
            numeric_columns = all_columns  # fallback
    except Exception:
        numeric_columns = all_columns  # fallback
    
    def get_columns_info(_: Any = None) -> str:
        """SEMPRE use esta ferramenta PRIMEIRO para descobrir quais colunas existem no dataset."""
        info = f"""
📊 **Informações do Dataset:**

**Total de colunas:** {len(all_columns)}
**Total de linhas:** {dataset.metadata.num_rows}

**Todas as colunas:**
{', '.join(all_columns)}

**Colunas numéricas (para gráficos):**
{', '.join(numeric_columns) if numeric_columns else 'Nenhuma identificada'}

**Primeiras 3 colunas:**
{', '.join(all_columns[:3])}

💡 **Dica:** Use os nomes EXATOS das colunas ao criar gráficos.
        """.strip()
        return info

    def describe(_: Any = None) -> str:
        """Retorna resumo estatístico do dataset."""
        result = stats_tool.compute_basic_stats(dataset.data)
        return f"{result.message}\n\nResumo: {result.summary}"

    def histogram(column: str) -> str:
        """Gera histograma para uma coluna."""
        # Validar se a coluna existe
        if column not in all_columns:
            return f"❌ Erro: Coluna '{column}' não encontrada. Colunas disponíveis: {', '.join(all_columns)}"
        
        try:
            path = chart_tool.build_histogram(dataset.data, column)
            from pathlib import Path
            path_obj = Path(path)
            if not path_obj.exists():
                return f"❌ Erro: Gráfico gerado mas arquivo não encontrado em {path}"
            
            abs_path = str(path_obj.absolute())
            return f"✅ Histograma criado com sucesso para a coluna '{column}'!\n\n**📊 Arquivo:** {abs_path}"
        except Exception as e:
            import traceback
            return f"❌ Erro ao criar histograma: {str(e)}\n\nDetalhes: {traceback.format_exc()}"

    def scatter(x: str, y: str, color: Optional[str] = None) -> str:
        """Cria gráfico de dispersão entre duas colunas."""
        # Validar colunas
        if x not in all_columns:
            return f"❌ Erro: Coluna X '{x}' não encontrada. Colunas disponíveis: {', '.join(all_columns)}"
        if y not in all_columns:
            return f"❌ Erro: Coluna Y '{y}' não encontrada. Colunas disponíveis: {', '.join(all_columns)}"
        if color and color not in all_columns:
            return f"❌ Erro: Coluna de cor '{color}' não encontrada. Colunas disponíveis: {', '.join(all_columns)}"
        
        try:
            path = chart_tool.build_scatter(dataset.data, x=x, y=y, color=color)
            # Garantir que o caminho seja absoluto e exista
            from pathlib import Path
            path_obj = Path(path)
            if not path_obj.exists():
                return f"❌ Erro: Gráfico gerado mas arquivo não encontrado em {path}"
            
            # Retornar mensagem com caminho absoluto para o Streamlit detectar
            abs_path = str(path_obj.absolute())
            return f"✅ Gráfico de dispersão criado com sucesso!\n\n**Colunas:** {x} (eixo X) vs {y} (eixo Y)" + (f" colorido por {color}" if color else "") + f"\n\n**📊 Arquivo:** {abs_path}"
        except Exception as e:
            import traceback
            return f"❌ Erro ao criar gráfico: {str(e)}\n\nDetalhes: {traceback.format_exc()}"

    def anomalies(contamination: float = 0.05) -> Dict[str, Any]:
        """Detecta outliers usando Isolation Forest."""
        result = anomaly_tool.detect_anomalies(dataset.data, contamination=contamination)
        return {
            "contamination": result.contamination,
            "outlier_count": result.outlier_count,
            "impact_ratio": result.impact_ratio,
            "message": f"Detectados {result.outlier_count} outliers ({result.impact_ratio:.2%} dos dados)"
        }
    
    def feature_importance(target_column: str, method: str = "rf") -> Dict[str, Any]:
        """Calcula importância das features para uma coluna alvo."""
        # Validar coluna alvo
        if target_column not in all_columns:
            return {
                "error": f"Coluna alvo '{target_column}' não encontrada. Colunas disponíveis: {', '.join(all_columns)}"
            }
        
        if feature_tool is None:
            return {"error": "feature_tool não disponível"}
        try:
            result = feature_tool.compute_feature_importances(
                dataset.data,
                target_column=target_column,
                method=method,
                task="auto",
                top_k=10
            )
            return {
                "importances": result.importances,
                "message": result.message,
                "plot_path": result.plot_path
            }
        except Exception as e:
            return {"error": str(e)}
    
    def execute_python_code(code: str) -> str:
        """
        Executa código Python arbitrário para análises customizadas.
        Use quando as ferramentas padrão não forem suficientes.
        
        O código tem acesso a:
        - df: DataFrame pandas com os dados (sempre disponível)
        - pl: Polars (se original for polars)
        - pd: Pandas
        - np: NumPy
        - plt: Matplotlib
        - sns: Seaborn
        - px: Plotly Express
        
        Retorna: String com output ou caminho do gráfico gerado.
        """
        import sys
        from io import StringIO
        from pathlib import Path
        import tempfile
        
        try:
            # Preparar ambiente de execução
            import pandas as pd
            import numpy as np
            
            # Converter dados para pandas se necessário
            if hasattr(data, 'to_pandas'):  # polars
                df = data.to_pandas()
                exec_globals = {'df': df, 'pd': pd, 'np': np, 'pl': data}
            else:
                df = data
                exec_globals = {'df': df, 'pd': pd, 'np': np}
            
            # Importações opcionais
            try:
                import matplotlib.pyplot as plt
                import seaborn as sns
                exec_globals['plt'] = plt
                exec_globals['sns'] = sns
            except ImportError:
                pass
            
            try:
                import plotly.express as px
                import plotly.graph_objects as go
                exec_globals['px'] = px
                exec_globals['go'] = go
            except ImportError:
                pass
            
            # Adicionar funções auxiliares
            temp_dir = Path(tempfile.gettempdir()) / "i2a2_reports"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            def save_plot(filename: str, fig=None):
                """Salva gráfico e retorna caminho absoluto."""
                path = temp_dir / filename
                if fig is None:
                    # Matplotlib
                    plt.savefig(path.with_suffix('.png'), bbox_inches='tight', dpi=150)
                    plt.close()
                    return str(path.with_suffix('.png'))
                else:
                    # Plotly
                    try:
                        fig.write_html(path.with_suffix('.html'))
                        return str(path.with_suffix('.html'))
                    except:
                        fig.write_image(path.with_suffix('.png'))
                        return str(path.with_suffix('.png'))
            
            exec_globals['save_plot'] = save_plot
            
            # Capturar stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            # Executar código
            exec(code, exec_globals)
            
            # Restaurar stdout
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            
            # Verificar se há gráficos salvos recentemente
            import time
            recent_files = sorted(temp_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
            if recent_files and (recent_files[0].stat().st_mtime > (time.time() - 10)):
                latest_plot = str(recent_files[0].absolute())
                if output:
                    return f"{output.strip()}\n\n**📊 Arquivo:** {latest_plot}"
                else:
                    return f"✅ Código executado com sucesso!\n\n**📊 Arquivo:** {latest_plot}"
            
            if output:
                return f"✅ Código executado com sucesso!\n\n```\n{output.strip()}\n```"
            else:
                return "✅ Código executado com sucesso! (sem output)"
                
        except Exception as e:
            import traceback
            return f"❌ Erro na execução:\n\n```python\n{code}\n```\n\n**Erro:** {str(e)}\n\n**Traceback:**\n```\n{traceback.format_exc()}\n```"

    # Criar schemas Pydantic para ferramentas com múltiplos argumentos
    if BaseModel is not None:
        class ScatterInput(BaseModel):
            x: str = Field(description="Nome da coluna para o eixo X")
            y: str = Field(description="Nome da coluna para o eixo Y")
            color: Optional[str] = Field(default=None, description="Nome da coluna para colorir os pontos (opcional)")
        
        class HistogramInput(BaseModel):
            column: str = Field(description="Nome da coluna para criar o histograma")
        
        class AnomaliesInput(BaseModel):
            contamination: float = Field(default=0.05, description="Proporção esperada de outliers (padrão 0.05 = 5%)")
        
        class FeatureImportanceInput(BaseModel):
            target_column: str = Field(description="Nome da coluna alvo para calcular importância")
            method: str = Field(default="rf", description="Método de cálculo: 'rf' (Random Forest) ou 'mutual_info'")
        
        class PythonCodeInput(BaseModel):
            code: str = Field(description="Código Python para executar. Tem acesso a: df (DataFrame), pd, np, plt, sns, px, save_plot(filename)")
        
        # Schema vazio para ferramentas sem argumentos
        class EmptyInput(BaseModel):
            pass

    tools = []
    
    # Todas as ferramentas agora usam StructuredTool para compatibilidade total
    if StructuredTool is not None and BaseModel is not None:
        tools.append(
            StructuredTool(
                name="info_colunas",
                description="🔍 SEMPRE use esta ferramenta PRIMEIRO para descobrir quais colunas existem no dataset antes de criar qualquer gráfico ou análise. Retorna lista completa de colunas com nomes exatos.",
                func=get_columns_info,
                args_schema=EmptyInput
            )
        )
        
        tools.append(
            StructuredTool(
                name="descrever_dataset",
                description="📊 Retorna resumo estatístico completo do dataset (média, mediana, desvio padrão, etc). Não requer parâmetros.",
                func=describe,
                args_schema=EmptyInput
            )
        )
        
        tools.append(
            StructuredTool(
                name="histograma",
                description="📈 Gera histograma para UMA coluna numérica. Parâmetro obrigatório: column (nome EXATO da coluna). Use info_colunas PRIMEIRO.",
                func=histogram,
                args_schema=HistogramInput
            )
        )
        
        tools.append(
            StructuredTool(
                name="dispersao",
                description="📉 Cria gráfico de dispersão entre DUAS colunas numéricas. Parâmetros obrigatórios: x (coluna eixo X), y (coluna eixo Y). Opcional: color (coluna para colorir). Use info_colunas PRIMEIRO.",
                func=scatter,
                args_schema=ScatterInput
            )
        )
        
        tools.append(
            StructuredTool(
                name="anomalias",
                description="🔴 Detecta outliers/anomalias usando Isolation Forest. Parâmetro opcional: contamination (proporção esperada de outliers, padrão 0.05 = 5%).",
                func=anomalies,
                args_schema=AnomaliesInput
            )
        )
        
        tools.append(
            StructuredTool(
                name="importancia_features",
                description="⭐ Calcula importância das features para prever uma coluna alvo. Parâmetros: target_column (coluna alvo), method (opcional: 'rf' ou 'mutual_info'). Use info_colunas PRIMEIRO.",
                func=feature_importance,
                args_schema=FeatureImportanceInput
            )
        )
        
        tools.append(
            StructuredTool(
                name="executar_codigo_python",
                description="🐍 **FERRAMENTA PODEROSA**: Executa código Python arbitrário quando as ferramentas padrão não são suficientes. Use para análises customizadas, gráficos personalizados, estatísticas avançadas, transformações de dados, etc. O código tem acesso a: df (DataFrame pandas), pd, np, plt, sns, px, save_plot(). Retorna output ou caminho do gráfico gerado.",
                func=execute_python_code,
                args_schema=PythonCodeInput
            )
        )
    else:
        # Fallback para Tool.from_function se StructuredTool não estiver disponível
        tools.extend([
            Tool.from_function(name="info_colunas", description="Informações das colunas", func=get_columns_info),
            Tool.from_function(name="descrever_dataset", description="Resumo estatístico", func=describe),
            Tool.from_function(name="histograma", description="Gera histograma. Parâmetro: column", func=histogram),
            Tool.from_function(name="dispersao", description="Gráfico de dispersão. Parâmetros: x, y, color (opcional)", func=scatter),
            Tool.from_function(name="anomalias", description="Detecta outliers. Parâmetro: contamination", func=anomalies),
            Tool.from_function(name="importancia_features", description="Importância de features. Parâmetros: target_column, method", func=feature_importance),
        ])
    
    return tools


def build_agent(dataset: DatasetContext, config: AgentConfig | None = None) -> Any:
    """Constrói um agente LangChain otimizado para OpenAI ou Gemini."""
    _require_dependencies()
    if config is None:
        config = AgentConfig.from_settings()

    provider = config.provider.lower()
    llm = create_chat_model(
        provider=provider,
        model=config.model,
        temperature=config.temperature,
        request_timeout=config.request_timeout,
    )
    tools = build_tools(dataset)

    # Preparar descrições das ferramentas
    tool_names = ", ".join([t.name for t in tools])
    tool_lines = []
    for t in tools:
        desc = getattr(t, "description", "")
        name = getattr(t, "name", str(t))
        tool_lines.append(f"- {name}: {desc}")
    tools_descriptions = "\n".join(tool_lines)

    # Configurar memória se habilitado
    memory = build_memory(dataset.metadata.path.stem) if config.use_memory else None

    # Instruções do sistema
    system_instructions = (
        "Você é um analista de dados experiente e versátil. Analise o dataset disponível respondendo em português, "
        "citando as etapas executadas e mencionando os gráficos gerados quando aplicável.\n\n"
        "🎯 **FILOSOFIA DE TRABALHO:**\n"
        "- Você tem ferramentas especializadas (histograma, dispersao, etc.) para tarefas comuns\n"
        "- Você também tem a ferramenta **executar_codigo_python** para análises customizadas\n"
        "- **Seja criativo!** Se uma pergunta não pode ser respondida com as ferramentas padrão, "
        "use executar_codigo_python para criar sua própria solução\n"
        "- Pense como um cientista de dados: escreva código Python para explorar, transformar, visualizar e analisar dados\n\n"
        "⚠️ **REGRAS IMPORTANTES:**\n"
        "1. SEMPRE use 'info_colunas' PRIMEIRO para descobrir nomes das colunas\n"
        "2. Use ferramentas padrão para tarefas simples (histograma, dispersao, etc.)\n"
        "3. Use 'executar_codigo_python' para:\n"
        "   - Gráficos personalizados (boxplot, violin, heatmap, 3D, etc.)\n"
        "   - Análises estatísticas avançadas (testes, correlações, regressões)\n"
        "   - Transformações de dados (filtros, agregações, pivots)\n"
        "   - Qualquer coisa que não seja coberta pelas ferramentas padrão\n"
        "4. 🚨 **CRÍTICO**: Quando uma ferramenta retornar '**📊 Arquivo:**', COPIE essa linha EXATAMENTE na sua resposta final!\n"
        "   Isso é necessário para que os gráficos apareçam na interface do usuário.\n\n"
        "📚 **AMBIENTE DE EXECUÇÃO PYTHON:**\n"
        "Quando usar executar_codigo_python, você tem acesso a:\n"
        "- `df`: DataFrame pandas com os dados\n"
        "- `pd`: Pandas\n"
        "- `np`: NumPy\n"
        "- `plt`: Matplotlib (use plt.savefig ou save_plot)\n"
        "- `sns`: Seaborn\n"
        "- `px`: Plotly Express\n"
        "- `save_plot(filename, fig)`: Salva gráfico e retorna caminho\n\n"
        "💡 **EXEMPLO DE USO:**\n"
        "Criar boxplot customizado:\n"
        "import matplotlib.pyplot as plt\n"
        "plt.figure(figsize=(12, 6))\n"
        "df.boxplot(column=['V1', 'V2', 'V3'])\n"
        "plt.title('Distribuição das Features')\n"
        "caminho = save_plot('boxplot_features')\n"
        "print('Gráfico salvo em:', caminho)\n\n"
        "Fluxo recomendado:\n"
        "1. 🔍 info_colunas → descobrir nomes exatos das colunas\n"
        "2. 🤔 Avaliar: ferramenta padrão OU código Python customizado?\n"
        "3. 🚀 Executar análise escolhida\n"
        "4. 📝 Explicar resultados e incluir TODOS os caminhos '**📊 Arquivo:**' retornados pelas ferramentas\n"
        "5. 📊 Finalizar com resumo em bullet points\n\n"
        f"Ferramentas disponíveis:\n{tools_descriptions}"
    )

    # Tentar usar tool-calling agent (padrão para OpenAI e Gemini moderno)
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instructions),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        
        agent_runnable = create_tool_calling_agent(llm, tools, prompt)
        
    except Exception:
        # Fallback para ReAct agent (Gemini antigo sem tool calling)
        prompt = PromptTemplate(
            template=(
                f"{system_instructions}\n\n"
                "Use o seguinte formato:\n\n"
                "Question: a pergunta de entrada\n"
                "Thought: reflita sobre o que fazer\n"
                "Action: escolha uma ferramenta\n"
                "Action Input: entrada para a ferramenta\n"
                "Observation: resultado da ação\n"
                "... (repita Thought/Action/Input/Observation conforme necessário)\n"
                "Thought: agora sei a resposta\n"
                "Final Answer: resposta final em português\n\n"
                "Ferramentas: {{tools}}\n\n"
                "Question: {{input}}\n"
                "Thought:{{agent_scratchpad}}"
            ),
            input_variables=["input", "agent_scratchpad", "tools"],
        )
        
        agent_runnable = create_react_agent(llm, tools, prompt)

    # Criar executor
    executor = AgentExecutor(
        agent=agent_runnable,
        tools=tools,
        verbose=True,
        max_iterations=config.max_steps,
        memory=memory.chat if memory else None,
        handle_parsing_errors=True,  # Lidar com erros de parsing graciosamente
        return_intermediate_steps=False,  # Não retornar passos intermediários por padrão
    )

    # Retornar com adapter se disponível
    try:
        from src.agents.agent_adapter import AgentAdapter
        return AgentAdapter(executor)
    except Exception:
        return executor
