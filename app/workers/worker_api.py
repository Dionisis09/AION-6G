from __future__ import annotations

import os

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
    return {"status": "ok", "execution_mode": os.getenv("AION_EXECUTION_MODE", "LOCAL")}


@app.post("/execute")
def execute(payload: WorkloadRequest) -> dict:
    result = execute_workload(payload.workload_type, iterations=payload.iterations, payload_size=payload.payload_size)
    return {
        "status": "ok",
        "runtime_execution_mode": os.getenv("AION_EXECUTION_MODE", "LOCAL"),
        "cluster_name": os.getenv("AION_CLUSTER_NAME"),
        "namespace": os.getenv("AION_NAMESPACE"),
        "deployment": os.getenv("AION_DEPLOYMENT"),
        "pod_name": os.getenv("AION_POD_NAME"),
        "pod_uid": os.getenv("AION_POD_UID"),
        "container_name": os.getenv("AION_CONTAINER_NAME"),
        **result,
    }
