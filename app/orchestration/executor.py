from __future__ import annotations

from datetime import datetime, timezone

import requests

from app.workloads.critical_control import execute_critical_control
from app.workloads.immersive_xr import execute_immersive_xr
from app.workloads.massive_iot import execute_massive_iot


def execute_workload(service_type: str, iterations: int = 200, payload_size: int = 64) -> dict:
    if service_type == "critical-control":
        return execute_critical_control(iterations=iterations, payload_size=payload_size)
    if service_type == "immersive-xr":
        return execute_immersive_xr(iterations=iterations, payload_size=payload_size)
    if service_type == "massive-iot":
        return execute_massive_iot(iterations=iterations, payload_size=payload_size)
    raise ValueError("Unsupported service type")


def execute_remote_workload(
    endpoint: str,
    service_type: str,
    iterations: int = 200,
    payload_size: int = 64,
    timeout_seconds: float = 10.0,
) -> dict:
    started = datetime.now(timezone.utc)
    response = requests.post(
        f"{endpoint.rstrip('/')}/execute",
        json={
            "workload_type": service_type,
            "iterations": iterations,
            "payload_size": payload_size,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    ended = datetime.now(timezone.utc)
    payload["start_timestamp"] = started.isoformat()
    payload["end_timestamp"] = ended.isoformat()
    return payload
