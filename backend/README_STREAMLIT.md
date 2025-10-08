# Streamlit deployment

Este README descreve como rodar a versão Streamlit do projeto criada em `frontend/app.py`.

## Como executar localmente

1. Crie um virtualenv e instale dependências:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Exporte variáveis de ambiente (exemplo):

```bash
export OPENAI_API_KEY="your_key"
export LLM_PROVIDER="openai"
export DEFAULT_MODEL="gpt-5-nano"
export GEMINI_API_KEY="your_gemini_key"
```

3. Execute o Streamlit app:

```bash
streamlit run frontend/app.py
```

## Deploy gratuito

- Recomendo usar Streamlit Community Cloud: faça push do repositório para o GitHub e configure o app apontando para `frontend/app.py`. Defina as variáveis de ambiente na UI do Streamlit Cloud.
- Alternativas: Render, Railway (planos gratuitos), Deta Space.

## Notas

- O app importa módulos do backend (`src/...`) então o repo precisa estar intacto.
- Se usar OpenAI, lembre-se dos custos (aplicações gratuitas têm limites).
- O app permite selecionar o provedor na barra lateral (OpenAI ou Gemini). Para Gemini, preencha `GEMINI_API_KEY` nas variáveis de ambiente ou diretamente na UI.
