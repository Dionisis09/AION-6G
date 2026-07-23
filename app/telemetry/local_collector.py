from __future__ import annotations

from datetime import datetime, timezone

import psutil
import requests

from app.config import LOCAL_WORKER_URL
from app.models.telemetry import Telemetry


def collect_local_telemetry(target: str) -> Telemetry:
    cpu = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory().percent
    try:
        response = requests.get(f"{LOCAL_WORKER_URL.rstrip('/')}/health", timeout=1.5)
        latency = response.elapsed.total_seconds() * 1000
        endpoint_ready = response.status_code == 200
    except Exception:
        latency = None
        endpoint_ready = False

    return Telemetry(
        target=target,
        health=endpoint_ready,
        cpu_utilization_percent=float(cpu),
        memory_utilization_percent=float(memory),
        http_latency_ms=latency,
        endpoint_ready=endpoint_ready,
        timestamp=datetime.now(timezone.utc).isoformat(),
        telemetry_source="local",
        network_data_type="MEASURED",
        worker_endpoint=LOCAL_WORKER_URL,
        metric_sources={
            "cpu_utilization_percent": "MEASURED",
            "memory_utilization_percent": "MEASURED",
            "http_latency_ms": "MEASURED" if latency is not None else "UNAVAILABLE",
        },
    )
