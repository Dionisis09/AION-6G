from __future__ import annotations

from app.workloads.common import run_bounded_workload


def execute_critical_control(iterations: int = 200, payload_size: int = 64) -> dict:
    return run_bounded_workload("critical-control", iterations=iterations, payload_size=payload_size)
