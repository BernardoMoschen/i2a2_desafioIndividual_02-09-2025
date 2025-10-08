#!/usr/bin/env bash
set -euo pipefail

if [ ! -f ".env" ]; then
  echo "Copiando .env.example para .env"
  cp .env.example .env
fi

mkdir -p data/input data/cache reports logs

echo "Ambiente inicializado. Execute 'poetry install' para instalar as dependências."
