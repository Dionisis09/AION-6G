from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone

import requests

from app.config import (
    KUBERNETES_CLUSTER_NAME,
    KUBERNETES_CONTAINER,
    KUBERNETES_CONTEXT,
    KUBERNETES_DEPLOYMENT,
    KUBERNETES_NAMESPACE,
    KUBERNETES_WORKER_URL,
)
from app.models.telemetry import Telemetry


def _run_kubectl(args: list[str]) -> tuple[bool, str, str]:
    try:
        completed = subprocess.run(
            ["kubectl", "--context", KUBERNETES_CONTEXT, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return completed.returncode == 0, completed.stdout.strip(), completed.stderr.strip()
    except Exception as exc:
        return False, "", str(exc)


def _unavailable(target: str, reason: str) -> Telemetry:
    return Telemetry(
        target=target,
        health=False,
        cpu_utilization_percent=None,
        memory_utilization_percent=None,
        http_latency_ms=None,
        endpoint_ready=False,
        timestamp=datetime.now(timezone.utc).isoformat(),
        telemetry_source="kubernetes",
        cpu_unavailable_reason=reason,
        network_data_type="UNAVAILABLE",
        cluster_name=KUBERNETES_CLUSTER_NAME,
        namespace=KUBERNETES_NAMESPACE,
        deployment=KUBERNETES_DEPLOYMENT,
        container_name=KUBERNETES_CONTAINER,
        worker_endpoint=KUBERNETES_WORKER_URL,
        metric_sources={
            "cpu_utilization_percent": "UNAVAILABLE",
            "memory_utilization_percent": "UNAVAILABLE",
            "http_latency_ms": "UNAVAILABLE",
        },
        details={"reason": reason},
    )


def collect_kubernetes_telemetry(target: str, namespace: str | None = None) -> Telemetry:
    ns = namespace or KUBERNETES_NAMESPACE
    ok, raw, error = _run_kubectl(["get", "deployment", KUBERNETES_DEPLOYMENT, "-n", ns, "-o", "json"])
    if not ok:
        return _unavailable(target, error or "expected kind cluster/deployment is not reachable")

    try:
        deployment = json.loads(raw)
    except json.JSONDecodeError:
        return _unavailable(target, "kubectl returned invalid deployment JSON")

    desired = int(deployment.get("spec", {}).get("replicas") or 0)
    ready = int(deployment.get("status", {}).get("readyReplicas") or 0)
    ok, raw, error = _run_kubectl([
        "get", "pods", "-n", ns, "-l", "app=aion6g-worker", "-o", "json"
    ])
    if not ok:
        return _unavailable(target, error or "worker pods are unavailable")
    pods = json.loads(raw).get("items", [])
    ready_pods = [
        pod for pod in pods
        if pod.get("status", {}).get("phase") == "Running"
        and all(item.get("ready") for item in pod.get("status", {}).get("containerStatuses", []))
    ]
    if desired < 1 or ready < desired or not ready_pods:
        return _unavailable(target, f"deployment is not ready: desired={desired}, ready={ready}")

    pod = ready_pods[0]
    statuses = pod.get("status", {}).get("containerStatuses", [])
    restart_count = sum(int(item.get("restartCount") or 0) for item in statuses)
    pod_name = pod.get("metadata", {}).get("name")
    pod_uid = pod.get("metadata", {}).get("uid")

    try:
        response = requests.get(f"{KUBERNETES_WORKER_URL.rstrip('/')}/health", timeout=2.0)
        latency = response.elapsed.total_seconds() * 1000.0
        endpoint_ready = response.status_code == 200
    except Exception as exc:
        return _unavailable(target, f"worker endpoint is unreachable: {exc}")

    cpu = memory = None
    metrics_reason = "metrics-server unavailable"
    metrics_ok, metrics_raw, metrics_error = _run_kubectl([
        "top", "pod", pod_name, "-n", ns, "--no-headers"
    ])
    if metrics_ok:
        metrics_reason = "kubectl top returned raw units; percentages are intentionally unavailable"
    elif metrics_error:
        metrics_reason = metrics_error

    return Telemetry(
        target=target,
        health=endpoint_ready,
        cpu_utilization_percent=cpu,
        memory_utilization_percent=memory,
        http_latency_ms=latency,
        endpoint_ready=endpoint_ready,
        kubernetes_desired_replicas=desired,
        kubernetes_ready_replicas=ready,
        pod_restart_count=restart_count,
        cluster_name=KUBERNETES_CLUSTER_NAME,
        namespace=ns,
        deployment=KUBERNETES_DEPLOYMENT,
        pod_name=pod_name,
        pod_uid=pod_uid,
        container_name=KUBERNETES_CONTAINER,
        worker_endpoint=KUBERNETES_WORKER_URL,
        timestamp=datetime.now(timezone.utc).isoformat(),
        telemetry_source="kubernetes",
        cpu_unavailable_reason=metrics_reason,
        network_data_type="MEASURED",
        metric_sources={
            "cpu_utilization_percent": "UNAVAILABLE",
            "memory_utilization_percent": "UNAVAILABLE",
            "http_latency_ms": "MEASURED",
        },
        details={"kubectl_top_raw": metrics_raw if metrics_ok else None},
    )
