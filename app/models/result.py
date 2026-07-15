from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class OrchestrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    intent: dict[str, Any]
    candidates: list[dict[str, Any]]
    selected_target: str | None
    execution: dict[str, Any]
    verification: dict[str, Any]
    fallback: dict[str, Any]
    orchestration_time_ms: int
    evidence_id: str
    network_data_type: str
