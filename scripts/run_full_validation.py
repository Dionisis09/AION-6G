from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS = PROJECT_ROOT / "results"
RESULTS.mkdir(exist_ok=True)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.orchestration.orchestrator import orchestrator
from app.telemetry.kubernetes_collector import collect_kubernetes_telemetry
from app.telemetry.local_collector import collect_local_telemetry


REQUESTS = {
    "critical-control": "Deploy a critical-control workload with latency below 100 ms and CPU below 70%",
    "immersive-xr": "Deploy an immersive-xr workload with latency below 100 ms and bandwidth above 50 Mbps and CPU below 75%",
    "massive-iot": "Deploy a massive-iot workload with latency below 100 ms and packet loss below 2% and CPU below 80%",
}


def save(name: str, payload: dict) -> dict:
    (RESULTS / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def run(name: str, request: str, policy: str, scenario: str = "baseline", fallback_allowed: bool = True) -> dict:
    return save(name, orchestrator.orchestrate(
        request,
        policy=policy,
        scenario=scenario,
        fallback_allowed=fallback_allowed,
    ))


def docker_validation() -> dict:
    checks = {}
    for path in ("health", "ready", "api/v1/profiles", "api/v1/telemetry"):
        response = requests.get(f"http://127.0.0.1:8000/{path}", timeout=10)
        checks[path] = {"status_code": response.status_code, "ok": response.ok}
    body = {"workload_type": "critical-control", "iterations": 100, "payload_size": 64}
    response = requests.post("http://127.0.0.1:8001/execute", json=body, timeout=10)
    response.raise_for_status()
    workload_before_restart = response.json()
    restart = subprocess.run(
        ["docker", "compose", "-p", "aion6g", "restart", "aion6g-local-worker"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    worker_recovered = False
    deadline = time.monotonic() + 30
    while restart.returncode == 0 and time.monotonic() < deadline:
        try:
            worker_recovered = requests.get("http://127.0.0.1:8001/health", timeout=2).ok
        except requests.RequestException:
            worker_recovered = False
        if worker_recovered:
            break
        time.sleep(0.5)

    workload_after_restart: dict = {}
    if worker_recovered:
        response = requests.post("http://127.0.0.1:8001/execute", json=body, timeout=10)
        response.raise_for_status()
        workload_after_restart = response.json()
    ps = subprocess.run(
        ["docker", "compose", "-p", "aion6g", "ps", "--format", "json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    checksum_before = workload_before_restart.get("checksum")
    checksum_after = workload_after_restart.get("checksum")
    verified = (
        all(item["ok"] for item in checks.values())
        and restart.returncode == 0
        and worker_recovered
        and bool(checksum_before)
        and checksum_before == checksum_after
        and workload_before_restart.get("runtime_execution_mode") == "DOCKER"
        and workload_after_restart.get("runtime_execution_mode") == "DOCKER"
        and ps.returncode == 0
    )
    return save("docker_validation.json", {
        "status": "VERIFIED" if verified else "PARTIAL",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "compose_project": "aion6g",
        "checks": checks,
        "workload_before_restart": workload_before_restart,
        "worker_restart": {
            "return_code": restart.returncode,
            "stdout": restart.stdout,
            "stderr": restart.stderr,
            "recovered": worker_recovered,
        },
        "workload_after_restart": workload_after_restart,
        "checksum_consistent_after_restart": checksum_before == checksum_after and bool(checksum_before),
        "compose_ps": ps.stdout,
    })


def kubernetes_validation() -> dict:
    telemetry = collect_kubernetes_telemetry("kubernetes-edge").model_dump()
    verified = bool(telemetry.get("health") and telemetry.get("pod_uid") and telemetry.get("kubernetes_ready_replicas") == 1)
    return save("kubernetes_validation.json", {
        "status": "VERIFIED" if verified else "BLOCKED",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "cluster_name": "aion-6g-cluster",
        "namespace": "aion-6g",
        "telemetry": telemetry,
        "metrics_status": "MEASURED" if telemetry.get("cpu_utilization_percent") is not None else "UNAVAILABLE",
    })


def main() -> None:
    docker_validation()
    kubernetes_validation()

    run("kubernetes_edge_success.json", REQUESTS["critical-control"], "always-kubernetes", fallback_allowed=False)
    run("policy_always_local.json", REQUESTS["massive-iot"], "always-local", fallback_allowed=False)
    run("policy_always_kubernetes.json", REQUESTS["massive-iot"], "always-kubernetes", fallback_allowed=False)
    run("policy_adaptive.json", REQUESTS["massive-iot"], "adaptive")
    run("adaptive_selects_local.json", REQUESTS["massive-iot"], "adaptive")
    run("adaptive_selects_kubernetes.json", REQUESTS["massive-iot"], "adaptive", "local-high-cpu")
    run("fallback_real_success.json", REQUESTS["massive-iot"], "adaptive", "selected-target-failure")

    run("profile_critical_control.json", REQUESTS["critical-control"], "always-kubernetes", fallback_allowed=False)
    run("profile_immersive_xr.json", REQUESTS["immersive-xr"], "always-kubernetes", fallback_allowed=False)
    run("profile_massive_iot.json", REQUESTS["massive-iot"], "always-local", fallback_allowed=False)

    scenario_policies = {
        "baseline": "always-local",
        "local-high-cpu": "adaptive",
        "kubernetes-high-latency": "always-local",
        "packet-loss-degradation": "always-local",
        "selected-target-failure": "adaptive",
        "no-eligible-target": "adaptive",
    }
    for scenario, policy in scenario_policies.items():
        run(f"scenario_{scenario.replace('-', '_')}.json", REQUESTS["massive-iot"], policy, scenario)

    print(json.dumps({"artifacts_created": 19, "results_dir": str(RESULTS)}, indent=2))


if __name__ == "__main__":
    if "--fallback-failure" in sys.argv:
        run("fallback_real_failure.json", REQUESTS["massive-iot"], "adaptive", "selected-target-failure")
    else:
        main()
