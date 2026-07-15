from __future__ import annotations

from app.workloads.common import run_bounded_workload


def execute_immersive_xr(iterations: int = 180, payload_size: int = 96) -> dict:
    return run_bounded_workload("immersive-xr", iterations=iterations, payload_size=payload_size)
