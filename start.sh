#!/usr/bin/env bash
set -euo pipefail

# start.sh - convenience script to setup virtualenv and run the Streamlit app
# Usage:
#   ./start.sh setup  -> create venv and install dependencies
#   ./start.sh run    -> launch the Streamlit app (requires venv present)
#   ./start.sh        -> setup then run

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

REQ_FILE="$ROOT_DIR/backend/requirements.txt"
APP_ENTRY="$ROOT_DIR/backend/frontend/app.py"

function ensure_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "Criando virtualenv em $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
  fi
}

function setup() {
  ensure_venv
  echo "Atualizando pip..."
  "$PIP" install --upgrade pip setuptools wheel
  if [ -f "$REQ_FILE" ]; then
    echo "Instalando dependências de $REQ_FILE..."
    "$PIP" install -r "$REQ_FILE"
  else
    echo "Arquivo de requirements não encontrado: $REQ_FILE"
    exit 1
  fi
}

function run() {
  if [ ! -x "$PYTHON" ]; then
    echo "Virtualenv não encontrado. Rode '$0 setup' antes de iniciar." >&2
    exit 1
  fi

  export PYTHONPATH="$ROOT_DIR/backend"
  echo "Iniciando Streamlit (PYTHONPATH=$PYTHONPATH) ..."
  exec "$VENV_DIR/bin/streamlit" run "$APP_ENTRY"
}

case "${1-}" in
  setup)
    setup
    ;;
  run)
    run
    ;;
  "" )
    setup
    run
    ;;
  *)
    echo "Usage: $0 [setup|run]"
    exit 2
    ;;
esac
