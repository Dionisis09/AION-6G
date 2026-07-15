from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.orchestration.executor import execute_workload

app = FastAPI(title="AION-6G Worker")


class WorkloadRequest(BaseModel):
    workload_type: str = Field(...)
    iterations: int = Field(default=100, ge=1, le=1000)
    payload_size: int = Field(default=64, ge=1, le=4096)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/execute")
def execute(payload: WorkloadRequest) -> dict:
    result = execute_workload(payload.workload_type, iterations=payload.iterations, payload_size=payload.payload_size)
    return {"status": "ok", **result}
