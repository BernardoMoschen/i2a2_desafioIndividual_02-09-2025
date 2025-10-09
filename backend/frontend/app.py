"""Streamlit interface optimized for AI-driven data analysis."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

import streamlit as st

# Ensure backend/ is on sys.path so imports like `from src.agents...` work when
# Streamlit Cloud runs the app (the cloud runner doesn't set PYTHONPATH).
backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# Carregar .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=False)

from src.agents.csv_agent import AgentConfig, build_agent
from src.config import get_settings
from src.pipelines.ingestion import DatasetContext, load_dataset

try:
    from src.tools.feature_tool import compute_feature_importances
except Exception:
    compute_feature_importances = None

try:
    from src.tools.correlation_tool import compute_correlations
except Exception:
    compute_correlations = None


@st.cache_resource(show_spinner=False)
def _get_settings():
    return get_settings()


def _ensure_dataset(upload) -> Optional[DatasetContext]:
    """Carrega o dataset enviado pelo usuário."""
    if upload is None:
        return None
    
    settings = _get_settings()
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    target_path = data_dir / upload.name
    target_path.write_bytes(upload.getvalue())
    
    return load_dataset(target_path, lazy=False)


def _build_agent(dataset: DatasetContext, provider: str, model: str, api_key: str) -> None:
    """Inicializa o agente de IA."""
    # Configurar chave de API
    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
    elif provider == "gemini":
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
    
    settings = _get_settings()
    config = AgentConfig(
        model=model,
        temperature=0.0,
        max_steps=8,
        use_memory=True,
        provider=provider,
        request_timeout=settings.model_request_timeout,
    )
    
    st.session_state.agent = build_agent(dataset, config)
    st.session_state.dataset = dataset
    st.session_state.messages = []


def _render_message(content: Any):
    """Render chat messages with support for charts and code blocks."""
    if isinstance(content, dict):
        # Preferred: render human-readable output if provided
        if "output" in content:
            st.markdown(content["output"])
            return

        # Fallbacks: some tools return structured metadata with paths (plot_path, plot, report_path)
        path_keys = ["plot_path", "plot", "report_path", "report", "file"]
        found_paths = []
        for k in path_keys:
            if k in content and content[k]:
                try:
                    p = str(content[k])
                    found_paths.append(p)
                except Exception:
                    pass

        if found_paths:
            output_lines = []
            if "message" in content:
                output_lines.append(str(content["message"]))
            for p in found_paths:
                output_lines.append(f"\n**📊 Arquivo:** {p}")
            st.markdown("\n".join(output_lines))
            return

        st.json(content)
    elif isinstance(content, str):
        # Detectar padrões de arquivo
        file_patterns = [
            r"(/tmp/i2a2_reports/[^\s'\"`,]+)",  # Adicionar , e ` na lista de exclusão
            r"\*\*📊 Arquivo:\*\*\s*([^\s`]+)",  # Adicionar ` na lista de exclusão
        ]
        
        paths = []
        seen = set()  # Para evitar duplicatas
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    if isinstance(match, str) and match.strip():
                        # Limpar caracteres extras como `, ', ", etc.
                        cleaned = match.strip().rstrip('`\'",')
                        if cleaned not in seen:
                            paths.append(cleaned)
                            seen.add(cleaned)
        
        # Detectar e processar blocos de código Python
        # Padrão: ```python\n...\n``` ou ```\n...\n```
        code_block_pattern = r"```(?:python)?\s*\n(.*?)\n```"
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
        
        if code_blocks:
            # Dividir o conteúdo em partes: texto e código
            parts = re.split(code_block_pattern, content, flags=re.DOTALL)
            
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Parte de texto (não-código)
                    if part.strip():
                        st.markdown(part)
                else:
                    # Parte de código
                    st.code(part, language='python')
        else:
            # Sem code blocks, renderizar normalmente
            st.markdown(content)
        
        # Renderizar gráficos encontrados
        if paths:
            st.markdown("---")
            st.markdown("### 📊 Gráficos Gerados:")
            
            # Debug: mostrar quantos caminhos foram detectados
            # st.caption(f"🔍 Debug: {len(paths)} arquivo(s) detectado(s)")
            
            for path_str in paths:
                # Debug: mostrar o caminho detectado
                # st.caption(f"🔍 Debug: Procurando arquivo em: `{path_str}`")
                
                p = Path(path_str)
                # st.caption(f"   - Existe? {p.exists()}")
                # st.caption(f"   - Sufixo: {p.suffix}")
                
                if p.exists():
                    if p.suffix == ".html":
                        try:
                            st.markdown(f"**{p.name}**")
                            html = p.read_text(encoding="utf-8")
                            st.components.v1.html(html, height=500, scrolling=True)
                            with open(p, "rb") as f:
                                st.download_button(
                                    f"📥 Baixar {p.name}",
                                    f.read(),
                                    file_name=p.name,
                                    key=f"download_{p.stem}_{hash(path_str)}"
                                )
                            st.markdown("---")
                        except Exception as e:
                            st.error(f"Erro ao renderizar {p.name}: {e}")
                    elif p.suffix == ".png":
                        st.markdown(f"**{p.name}**")
                        st.image(str(p), use_column_width=True)
                        with open(p, "rb") as f:
                            st.download_button(
                                f"📥 Baixar {p.name}",
                                f.read(),
                                file_name=p.name,
                                key=f"download_{p.stem}_{hash(path_str)}"
                            )
                        st.markdown("---")
                else:
                    # Mostrar caminho completo para debug
                    st.warning(f"⚠️ Arquivo não encontrado: `{path_str}`")
    else:
        st.write(content)


def main() -> None:
    """Interface principal otimizada para o usuário final."""
    
    # Configuração da página
    st.set_page_config(
        page_title="Análise de Dados com IA",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS customizado
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<p class="main-header">🤖 AI Data Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Upload your data and chat with a specialized AI assistant</p>', unsafe_allow_html=True)
    
    # Sidebar - Settings
    with st.sidebar:
        st.header("⚙️ Settings")

        settings = _get_settings()

        # AI Provider
        st.subheader("AI Provider")
        provider_options = {
            "OpenAI (GPT)": "openai",
            "Google Gemini": "gemini"
        }
        provider_label = st.selectbox(
            "Choose provider:",
            options=list(provider_options.keys()),
            index=0 if settings.llm_provider == "openai" else 1
        )
        provider = provider_options[provider_label]

        # Model
        if provider == "openai":
            model_options = ["gpt-4o-mini", "gpt-4o"]
            default_model = settings.default_model if settings.default_model in model_options else "gpt-4o-mini"
        else:
            model_options = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
            default_model = settings.default_model if settings.default_model in model_options else "gemini-1.5-flash"

        model = st.selectbox("Model:", options=model_options, index=model_options.index(default_model) if default_model in model_options else 0)

        # API Key
        st.subheader("API Key")

        if provider == "openai":
            api_key = st.text_input(
                "OpenAI API Key:",
                value=os.environ.get("OPENAI_API_KEY", ""),
                type="password",
                help="Get it at https://platform.openai.com/api-keys"
            )
        else:
            api_key = st.text_input(
                "Google AI API Key:",
                value=os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", "")),
                type="password",
                help="Get it at https://aistudio.google.com/apikey"
            )

        st.markdown("---")

        # Status
        if st.session_state.get("agent"):
            st.success("✅ Agent active")
            if st.session_state.get("dataset"):
                ds = st.session_state.dataset
                st.info(f"📊 {ds.metadata.num_rows:,} rows × {ds.metadata.num_columns} columns")
        else:
            st.warning("⏳ Waiting for initialization")

        st.markdown("---")

        # How to use
        with st.expander("❓ How to use"):
            st.markdown("""
            1. Configure the API Key above
            2. Upload your CSV file
            3. Click "🚀 Initialize"
            4. Ask questions about the data
            
            **Examples:**
            - "What are the main statistics?"
            - "Show correlations"
            - "Create a histogram of [column]"
            - "Detect outliers"
            """)

        # Debug - list generated report files
        with st.expander("🐞 Debug: generated reports (temp)"):
            try:
                import tempfile
                from pathlib import Path
                temp_dir = Path(tempfile.gettempdir()) / "i2a2_reports"
                files = []
                if temp_dir.exists():
                    for p in sorted(temp_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                        try:
                            files.append({
                                "name": p.name,
                                "path": str(p.absolute()),
                                "size_kb": f"{p.stat().st_size/1024:.1f}",
                                "mtime": p.stat().st_mtime,
                                "suffix": p.suffix,
                            })
                        except Exception:
                            pass

                if not files:
                    st.write("No report files found in temp directory.")
                else:
                    for f in files[:50]:
                        st.write(f"- {f['name']} — {f['size_kb']} KB — {f['suffix']}")
                        if f['suffix'] == '.html':
                            try:
                                text = Path(f['path']).read_text(encoding='utf-8')
                                st.code(text[:1000])
                            except Exception as e:
                                st.write(f"Could not read {f['name']}: {e}")
            except Exception as e:
                st.write(f"Debug error: {e}")
    
    # Inicializar session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dataset" not in st.session_state:
        st.session_state.dataset = None
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    # Upload de arquivo
    st.subheader("📁 Carregar Dataset")
    
    col_upload, col_button = st.columns([3, 1])
    
    with col_upload:
        uploaded_file = st.file_uploader(
            "Selecione um arquivo CSV",
            type=["csv"],
            help="Formatos: CSV com separadores vírgula, ponto-vírgula ou tab",
            label_visibility="collapsed"
        )
    
    with col_button:
        if uploaded_file:
            if st.button("🚀 Inicializar", type="primary", use_container_width=True):
                if not api_key:
                    st.error("❌ Configure a API Key na barra lateral")
                else:
                    with st.spinner("Inicializando..."):
                        try:
                            dataset = _ensure_dataset(uploaded_file)
                            if dataset:
                                _build_agent(dataset, provider, model, api_key)
                                st.success("✅ Pronto!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao carregar dataset")
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
    
    # Preview dos dados
    if st.session_state.get("dataset"):
        dataset = st.session_state.dataset
        
        with st.expander("📊 Informações do Dataset", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Linhas", f"{dataset.metadata.num_rows:,}")
            with col2:
                st.metric("Colunas", dataset.metadata.num_columns)
            with col3:
                st.metric("Tamanho", f"{dataset.metadata.size_in_bytes / 1024:.1f} KB")
            with col4:
                if st.button("🔄 Resetar"):
                    st.session_state.clear()
                    st.rerun()
            
            st.write("**Colunas:**", ", ".join(dataset.metadata.columns))
            
            # Preview dos dados
            try:
                data = dataset.data
                if hasattr(data, "head"):
                    st.dataframe(data.head(20), use_container_width=True)
            except Exception as e:
                st.warning(f"Preview não disponível: {e}")
    
    st.markdown("---")
    
    # Chat com o agente
    if st.session_state.get("agent"):
        st.subheader("💬 Converse com o Assistente")
        
        # Exibir mensagens anteriores
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                _render_message(message["content"])
        
        # Input do usuário
        if prompt := st.chat_input("Faça uma pergunta sobre os dados..."):
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Gerar resposta
            with st.chat_message("assistant"):
                with st.spinner("Analisando..."):
                    try:
                        agent = st.session_state.agent
                        response = agent.invoke({"input": prompt})
                        
                        # Extrair output
                        if isinstance(response, dict):
                            if "output" in response:
                                output = response["output"]
                            elif "result" in response:
                                output = response["result"]
                            else:
                                output = response
                        else:
                            output = response
                        
                        _render_message(output)
                        st.session_state.messages.append({"role": "assistant", "content": output})
                        
                    except Exception as e:
                        error_msg = f"❌ Erro: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    elif st.session_state.get("dataset"):
        st.info("ℹ️ Dataset carregado. Clique em **🚀 Inicializar** para ativar o assistente.")
    
    else:
        # Guia inicial para usuários novos
        st.markdown("### 🎯 O que você pode fazer:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📊 Análise Exploratória")
            st.markdown("""
            - Estatísticas descritivas
            - Visualizações automáticas
            - Identificação de padrões
            - Detecção de anomalias
            """)
        
        with col2:
            st.markdown("#### 🔍 Insights com IA")
            st.markdown("""
            - Correlações entre variáveis
            - Importância de features
            - Recomendações de análise
            - Interpretação de resultados
            """)
        
        with col3:
            st.markdown("#### 📈 Visualizações")
            st.markdown("""
            - Histogramas interativos
            - Gráficos de dispersão
            - Heatmaps de correlação
            - Exportação de gráficos
            """)
        
        st.markdown("---")
        st.info("👆 **Começar:** Carregue um CSV acima e configure a API Key na barra lateral")


if __name__ == "__main__":
    main()
