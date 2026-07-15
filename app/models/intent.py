from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator

Priority = Literal["reliability", "latency", "scalability"]


class ServiceIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_type: str = Field(..., min_length=1)
    max_latency_ms: float = Field(..., gt=0)
    max_jitter_ms: float | None = Field(default=None, ge=0)
    max_packet_loss_percent: float | None = Field(default=None, ge=0)
    min_bandwidth_mbps: float | None = Field(default=None, ge=0)
    max_cpu_percent: float | None = Field(default=None, gt=0)
    max_memory_percent: float | None = Field(default=None, gt=0)
    priority: Priority = Field(...)
    fallback_allowed: bool = True

    @field_validator("service_type")
    @classmethod
    def validate_service_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"critical-control", "immersive-xr", "massive-iot"}
        if normalized not in allowed:
            raise ValueError("service_type must be one of: critical-control, immersive-xr, massive-iot")
        return normalized

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"reliability", "latency", "scalability"}:
            raise ValueError("priority must be one of: reliability, latency, scalability")
        return normalized

    @field_validator("max_packet_loss_percent")
    @classmethod
    def validate_packet_loss(cls, value: float | None) -> float | None:
        if value is not None and value > 100:
            raise ValueError("max_packet_loss_percent cannot exceed 100")
        return value

    @field_validator("max_cpu_percent", "max_memory_percent")
    @classmethod
    def validate_percentage(cls, value: float | None) -> float | None:
        if value is not None and value > 100:
            raise ValueError("percentage values cannot exceed 100")
        return value
