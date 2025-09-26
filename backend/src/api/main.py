"""API FastAPI para interação com o agente."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.agents.csv_agent import AgentConfig, build_agent
from src.config import Settings, get_settings
from src.pipelines.ingestion import DatasetContext, load_dataset

app = FastAPI(title="Agente Autônomo CSV")

_DATASETS: Dict[str, DatasetContext] = {}


def get_settings_dependency() -> Settings:
    return get_settings()


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings_dependency),
) -> Dict[str, str]:
    dataset_id = uuid.uuid4().hex
    output_path = Path(settings.data_dir) / file.filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    output_path.write_bytes(content)

    dataset = load_dataset(output_path, lazy=False)
    _DATASETS[dataset_id] = dataset

    return {"dataset_id": dataset_id, "rows": str(dataset.metadata.num_rows)}


@app.post("/ask")
async def ask_question(
    dataset_id: str,
    question: str,
    settings: Settings = Depends(get_settings_dependency),
) -> JSONResponse:
    dataset = _DATASETS.get(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset não encontrado")

    try:
        agent = build_agent(dataset, AgentConfig.from_settings())
    except RuntimeError as exc:  # dependências ausentes
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    response = agent.invoke({"input": question})
    return JSONResponse(content={"answer": response})


@app.get("/datasets")
def list_datasets() -> Dict[str, Dict[str, str]]:
    return {
        dataset_id: {
            "path": str(ctx.metadata.path),
            "rows": str(ctx.metadata.num_rows),
            "columns": str(ctx.metadata.num_columns),
        }
        for dataset_id, ctx in _DATASETS.items()
    }
