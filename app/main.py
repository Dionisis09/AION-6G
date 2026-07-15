from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from app.config import ROOT_DIR
from app.intent.deterministic_parser import parse_intent
from app.models.intent import ServiceIntent
from app.orchestration.orchestrator import orchestrator

app = FastAPI(title="AION-6G", version="0.1.0")


class IntentRequest(BaseModel):
    request: str = Field(..., min_length=1)
    policy: str = Field(default="adaptive")
    scenario: str = Field(default="baseline")
    fallback_allowed: bool = True


class ExperimentRequest(BaseModel):
    policies: list[str] = Field(default_factory=lambda: ["always-local", "always-kubernetes", "adaptive"])
    scenarios: list[str] = Field(default_factory=lambda: ["baseline", "local-high-cpu", "kubernetes-high-latency"])
    runs_per_scenario: int = Field(default=3, ge=1, le=20)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    return {"status": "ready"}


@app.get("/api/v1/profiles")
def profiles() -> list[dict[str, Any]]:
    return [
        {
            "name": "critical-control",
            "description": "Reliability-sensitive control workload",
            "defaults": {
                "max_latency_ms": 20,
                "max_jitter_ms": 2,
                "max_packet_loss_percent": 0.1,
                "max_cpu_percent": 70,
                "priority": "reliability",
            },
        },
        {
            "name": "immersive-xr",
            "description": "Latency-sensitive interactive workload",
            "defaults": {
                "max_latency_ms": 15,
                "max_jitter_ms": 4,
                "max_packet_loss_percent": 0.5,
                "min_bandwidth_mbps": 50,
                "max_cpu_percent": 75,
                "priority": "latency",
            },
        },
        {
            "name": "massive-iot",
            "description": "Batch processing of many lightweight device messages",
            "defaults": {
                "max_latency_ms": 100,
                "max_packet_loss_percent": 2,
                "max_cpu_percent": 80,
                "priority": "scalability",
            },
        },
    ]


@app.get("/api/v1/targets")
def targets() -> list[dict[str, Any]]:
    return [
        {"name": "local-edge", "description": "Local worker target"},
        {"name": "kubernetes-edge", "description": "Kubernetes worker target"},
    ]


@app.get("/api/v1/telemetry")
def telemetry() -> list[dict[str, Any]]:
    return [{"target": "local-edge", "status": "ok"}, {"target": "kubernetes-edge", "status": "ok"}]


@app.post("/api/v1/parse-intent")
def parse_intent_endpoint(payload: IntentRequest) -> dict[str, Any]:
    intent = parse_intent(payload.request)
    return intent.model_dump()


@app.post("/api/v1/orchestrate")
def orchestrate(payload: IntentRequest) -> dict[str, Any]:
    return orchestrator.orchestrate(payload.request, policy=payload.policy, scenario=payload.scenario, fallback_allowed=payload.fallback_allowed)


@app.post("/api/v1/run-experiment")
def run_experiment(payload: ExperimentRequest) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for policy in payload.policies:
        for scenario in payload.scenarios:
            for _ in range(payload.runs_per_scenario):
                result = orchestrator.orchestrate("Deploy a critical-control workload with latency below 20 ms and CPU below 70%", policy=policy, scenario=scenario)
                results.append(result)
    return {"count": len(results), "results": results}


@app.get("/api/v1/results")
def results() -> list[dict[str, Any]]:
    paths = sorted(Path(ROOT_DIR / "results").glob("*.json"))
    items = []
    for path in paths:
        items.append(json.loads(path.read_text(encoding="utf-8")))
    return items


@app.get("/api/v1/results/{result_id}")
def result_detail(result_id: str) -> dict[str, Any]:
    for path in Path(ROOT_DIR / "results").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("evidence_id") == result_id:
            return payload
    raise HTTPException(status_code=404, detail="Result not found")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    html_path = ROOT_DIR / "app" / "web" / "templates" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"), status_code=200)
