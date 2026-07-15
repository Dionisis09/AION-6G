from __future__ import annotations

from app.workloads.common import run_bounded_workload


def execute_massive_iot(iterations: int = 400, payload_size: int = 32) -> dict:
    return run_bounded_workload("massive-iot", iterations=iterations, payload_size=payload_size)
