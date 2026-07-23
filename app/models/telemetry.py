from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


class Telemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str
    health: bool
    cpu_utilization_percent: float | None
    memory_utilization_percent: float | None
    http_latency_ms: float | None
    endpoint_ready: bool
    kubernetes_desired_replicas: int | None = None
    kubernetes_ready_replicas: int | None = None
    pod_restart_count: int | None = None
    cluster_name: str | None = None
    namespace: str | None = None
    deployment: str | None = None
    pod_name: str | None = None
    pod_uid: str | None = None
    container_name: str | None = None
    worker_endpoint: str | None = None
    timestamp: str
    telemetry_source: Literal["local", "kubernetes", "emulated", "mixed"]
    cpu_unavailable_reason: str | None = None
    network_data_type: Literal["MEASURED", "EMULATED", "CONTROLLED", "UNAVAILABLE"]
    metric_sources: dict[str, str] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)
