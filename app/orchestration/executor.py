from __future__ import annotations

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
