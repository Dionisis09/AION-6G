from __future__ import annotations

import platform
import time
from datetime import datetime, timezone

import psutil
import requests

from app.models.telemetry import Telemetry


def collect_local_telemetry(target: str) -> Telemetry:
    cpu = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory().percent
    try:
        response = requests.get(f"http://127.0.0.1:8001/health", timeout=1.5)
        latency = response.elapsed.total_seconds() * 1000
        endpoint_ready = response.status_code == 200
    except Exception:
        latency = None
        endpoint_ready = False

    return Telemetry(
        target=target,
        health=True,
        cpu_utilization_percent=float(cpu),
        memory_utilization_percent=float(memory),
        http_latency_ms=latency,
        endpoint_ready=endpoint_ready,
        timestamp=datetime.now(timezone.utc).isoformat(),
        telemetry_source="local",
        network_data_type="MEASURED",
    )
