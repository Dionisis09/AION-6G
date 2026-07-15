from unittest.mock import patch

from app.experiments.summary import build_experiment_summary
from app.models.telemetry import Telemetry
from app.orchestration.orchestrator import orchestrator


def telemetry(target: str, *, healthy: bool = True, kubernetes: bool = False, complete: bool = True) -> Telemetry:
    return Telemetry(
        target=target,
        health=healthy,
        cpu_utilization_percent=None if kubernetes else 10.0,
        memory_utilization_percent=None if kubernetes else 20.0,
        http_latency_ms=19.0 if kubernetes else 1.0,
        endpoint_ready=healthy,
        kubernetes_desired_replicas=1 if kubernetes else None,
        kubernetes_ready_replicas=1 if kubernetes else None,
        pod_restart_count=0 if kubernetes else None,
        cluster_name="aion-6g-cluster" if kubernetes else None,
        namespace="aion-6g" if kubernetes else None,
        deployment="aion6g-worker" if kubernetes else None,
        pod_name="aion6g-worker-abc" if kubernetes else None,
        pod_uid="uid-123" if kubernetes and complete else None,
        container_name="aion6g-worker" if kubernetes else None,
        worker_endpoint="http://127.0.0.1:8002" if kubernetes else "http://127.0.0.1:8001",
        timestamp="2026-07-15T00:00:00Z",
        telemetry_source="kubernetes" if kubernetes else "local",
        cpu_unavailable_reason="metrics unavailable" if kubernetes else None,
        network_data_type="MEASURED" if healthy else "UNAVAILABLE",
        metric_sources={"http_latency_ms": "MEASURED" if healthy else "UNAVAILABLE"},
    )


def worker_response(mode: str) -> dict:
    payload = {
        "status": "ok",
        "runtime_execution_mode": mode,
        "workload_type": "critical-control",
        "iterations": 200,
        "payload_size": 64,
        "checksum": "abc",
        "execution_latency_ms": 1.2,
        "start_timestamp": "2026-07-15T00:00:00Z",
        "end_timestamp": "2026-07-15T00:00:01Z",
    }
    if mode == "KUBERNETES":
        payload.update({
            "cluster_name": "aion-6g-cluster",
            "namespace": "aion-6g",
            "deployment": "aion6g-worker",
            "pod_name": "aion6g-worker-abc",
            "pod_uid": "uid-123",
            "container_name": "aion6g-worker",
        })
    return payload


def test_orchestrator_returns_result_payload(tmp_path):
    with patch("app.orchestration.orchestrator.collect_local_telemetry", return_value=telemetry("local-edge")), \
         patch("app.orchestration.orchestrator.collect_kubernetes_telemetry", return_value=telemetry("kubernetes-edge", kubernetes=True)), \
         patch("app.orchestration.orchestrator.execute_remote_workload", return_value=worker_response("LOCAL")), \
         patch.object(orchestrator, "results_dir", tmp_path):
        result = orchestrator.orchestrate("Deploy a critical-control workload with latency below 20 ms and CPU below 70%")
    assert result["selected_target"] == "local-edge"
    assert result["execution_mode"] == "LOCAL"
    assert result["verification"]["status"] == "PASSED"


def test_selected_target_failure_retries_once_without_fabrication(tmp_path):
    with patch("app.orchestration.orchestrator.collect_local_telemetry", return_value=telemetry("local-edge")), \
         patch("app.orchestration.orchestrator.collect_kubernetes_telemetry", return_value=telemetry("kubernetes-edge", kubernetes=True)), \
         patch("app.orchestration.orchestrator.execute_remote_workload", return_value=worker_response("KUBERNETES")) as remote, \
         patch.object(orchestrator, "results_dir", tmp_path):
        result = orchestrator.orchestrate(
            "Deploy a critical-control workload with latency below 20 ms and CPU below 70%",
            scenario="selected-target-failure",
        )
    assert remote.call_count == 1
    assert result["fallback"]["used"] is True
    assert result["fallback"]["retry_count"] == 1
    assert len(result["fallback"]["attempts"]) == 2
    assert result["execution"]["execution_mode"] == "KUBERNETES"
    assert result["verification"]["status"] == "PASSED"


def test_kubernetes_unreachable_is_unavailable_and_never_passes(tmp_path):
    unavailable = telemetry("kubernetes-edge", healthy=False, kubernetes=True)
    with patch("app.orchestration.orchestrator.collect_local_telemetry", return_value=telemetry("local-edge")), \
         patch("app.orchestration.orchestrator.collect_kubernetes_telemetry", return_value=unavailable), \
         patch("app.orchestration.orchestrator.execute_remote_workload") as remote, \
         patch.object(orchestrator, "results_dir", tmp_path):
        result = orchestrator.orchestrate("Deploy a critical-control workload with latency below 20 ms", policy="always-kubernetes", fallback_allowed=False)
    remote.assert_not_called()
    assert result["execution_mode"] == "UNAVAILABLE"
    assert result["verification_status"] == "FAILED"
    assert result["execution"]["execution_latency_ms"] is None


def test_kubernetes_cannot_execute_through_local_runtime(tmp_path):
    with patch("app.orchestration.orchestrator.collect_local_telemetry", return_value=telemetry("local-edge")), \
         patch("app.orchestration.orchestrator.collect_kubernetes_telemetry", return_value=telemetry("kubernetes-edge", kubernetes=True)), \
         patch("app.orchestration.orchestrator.execute_remote_workload", return_value=worker_response("LOCAL")), \
         patch.object(orchestrator, "results_dir", tmp_path):
        result = orchestrator.orchestrate("Deploy a critical-control workload with latency below 20 ms", policy="always-kubernetes", fallback_allowed=False)
    assert result["execution_mode"] == "UNAVAILABLE"
    assert result["verification_status"] == "FAILED"


def test_real_kubernetes_requires_complete_pod_metadata(tmp_path):
    incomplete = telemetry("kubernetes-edge", kubernetes=True, complete=False)
    response = worker_response("KUBERNETES")
    response["pod_uid"] = None
    with patch("app.orchestration.orchestrator.collect_local_telemetry", return_value=telemetry("local-edge")), \
         patch("app.orchestration.orchestrator.collect_kubernetes_telemetry", return_value=incomplete), \
         patch("app.orchestration.orchestrator.execute_remote_workload", return_value=response), \
         patch.object(orchestrator, "results_dir", tmp_path):
        result = orchestrator.orchestrate("Deploy a critical-control workload with latency below 20 ms", policy="always-kubernetes", fallback_allowed=False)
    assert result["execution_mode"] == "KUBERNETES"
    assert result["verification_status"] == "FAILED"
    assert any("pod_uid" in check for check in result["verification"]["checks"])


def test_simulated_execution_is_never_labelled_kubernetes(tmp_path):
    unavailable = telemetry("kubernetes-edge", healthy=False, kubernetes=True)
    with patch("app.orchestration.orchestrator.collect_local_telemetry", return_value=telemetry("local-edge")), \
         patch("app.orchestration.orchestrator.collect_kubernetes_telemetry", return_value=unavailable), \
         patch.object(orchestrator, "results_dir", tmp_path):
        result = orchestrator.orchestrate("Deploy a critical-control workload with latency below 20 ms", policy="always-kubernetes", fallback_allowed=False)
    assert result["execution_mode"] != "KUBERNETES"
    assert result["execution_mode"] == "UNAVAILABLE"


def test_build_experiment_summary_writes_outputs(tmp_path):
    rows = [{
        "policy": "adaptive", "service_profile": "critical-control", "scenario": "baseline",
        "selected_target": "local-edge", "execution_mode": "LOCAL", "execution_success": True,
        "sla_status": "PASSED", "fallback_used": False, "orchestration_time_ms": 100,
        "local_http_latency_ms": 1.3, "local_cpu_percent": 20.0, "local_memory_percent": 30.0,
        "jitter_ms": 0, "packet_loss_percent": 0, "bandwidth_mbps": 1000,
        "network_data_type": "EMULATED", "rejection_reasons": [],
    }]
    summary = build_experiment_summary(rows, tmp_path)
    assert (tmp_path / "experiment_summary.csv").exists()
    assert (tmp_path / "experiment_summary.json").exists()
    assert (tmp_path / "experiment_statistics.json").exists()
    assert summary["rows"] == 1
