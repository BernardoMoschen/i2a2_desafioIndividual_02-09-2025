# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml README.md ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

COPY src ./src
COPY scripts ./scripts

RUN addgroup --system agent && adduser --system --ingroup agent agent
USER agent

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
