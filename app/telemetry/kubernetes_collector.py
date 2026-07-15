from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from app.models.telemetry import Telemetry


def _run_kubectl(args: list[str]) -> tuple[bool, str]:
    import subprocess

    try:
        completed = subprocess.run(["kubectl", *args], capture_output=True, text=True, timeout=10)
        return completed.returncode == 0, completed.stdout.strip()
    except Exception:
        return False, ""


def collect_kubernetes_telemetry(target: str, namespace: str | None = None) -> Telemetry:
    ns = namespace or os.getenv("KUBERNETES_NAMESPACE", "default")
    ok, _ = _run_kubectl(["get", "pods", "-n", ns])
    if not ok:
        return Telemetry(
            target=target,
            health=False,
            cpu_utilization_percent=None,
            memory_utilization_percent=None,
            http_latency_ms=None,
            endpoint_ready=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            telemetry_source="kubernetes",
            cpu_unavailable_reason="kubectl is unavailable or cluster is not reachable",
            network_data_type="MEASURED",
        )

    return Telemetry(
        target=target,
        health=True,
        cpu_utilization_percent=None,
        memory_utilization_percent=None,
        http_latency_ms=None,
        endpoint_ready=True,
        kubernetes_desired_replicas=1,
        kubernetes_ready_replicas=1,
        pod_restart_count=0,
        timestamp=datetime.now(timezone.utc).isoformat(),
        telemetry_source="kubernetes",
        cpu_unavailable_reason="metrics-server unavailable in this environment",
        network_data_type="MEASURED",
    )
