from __future__ import annotations

import hashlib
import time
from typing import Any


class WorkloadError(Exception):
    pass


def run_bounded_workload(workload_type: str, iterations: int = 200, payload_size: int = 64) -> dict[str, Any]:
    if workload_type not in {"critical-control", "immersive-xr", "massive-iot"}:
        raise WorkloadError("Workload type is not allowed")
    if iterations <= 0 or iterations > 10000:
        raise WorkloadError("iterations must be between 1 and 10000")
    if payload_size <= 0 or payload_size > 4096:
        raise WorkloadError("payload_size must be between 1 and 4096")

    start = time.perf_counter()
    checksum = hashlib.sha256()
    for index in range(iterations):
        checksum.update(f"{workload_type}:{index}:{payload_size}".encode("utf-8"))
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return {
        "workload_type": workload_type,
        "iterations": iterations,
        "payload_size": payload_size,
        "checksum": checksum.hexdigest(),
        "execution_latency_ms": round(elapsed_ms, 2),
    }
