from unittest.mock import Mock, patch

from app.telemetry.kubernetes_collector import _run_kubectl, collect_kubernetes_telemetry


def worker_health_response(mode: str = "KUBERNETES") -> Mock:
    response = Mock()
    response.status_code = 200
    response.elapsed.total_seconds.return_value = 0.005
    response.json.return_value = {"status": "ok", "execution_mode": mode}
    return response


def test_kubectl_uses_current_context_when_no_override_is_configured():
    completed = Mock(returncode=0, stdout="{}", stderr="")
    with patch(
        "app.telemetry.kubernetes_collector.KUBERNETES_CONTEXT",
        "",
    ), patch(
        "app.telemetry.kubernetes_collector.subprocess.run",
        return_value=completed,
    ) as run:
        ok, _, _ = _run_kubectl(["get", "nodes"])

    assert ok is True
    assert run.call_args.args[0] == ["kubectl", "get", "nodes"]


def test_kubectl_uses_explicit_context_override_when_configured():
    completed = Mock(returncode=0, stdout="{}", stderr="")
    with patch(
        "app.telemetry.kubernetes_collector.KUBERNETES_CONTEXT",
        "test-context",
    ), patch(
        "app.telemetry.kubernetes_collector.subprocess.run",
        return_value=completed,
    ) as run:
        ok, _, _ = _run_kubectl(["get", "nodes"])

    assert ok is True
    assert run.call_args.args[0] == [
        "kubectl",
        "--context",
        "test-context",
        "get",
        "nodes",
    ]


def test_endpoint_only_telemetry_is_truthful_when_kubectl_is_unavailable():
    with patch(
        "app.telemetry.kubernetes_collector._run_kubectl",
        return_value=(False, "", "kubectl executable not found"),
    ), patch(
        "app.telemetry.kubernetes_collector.requests.get",
        return_value=worker_health_response(),
    ):
        telemetry = collect_kubernetes_telemetry("kubernetes-edge")

    assert telemetry.health is True
    assert telemetry.endpoint_ready is True
    assert telemetry.http_latency_ms == 5.0
    assert telemetry.pod_name is None
    assert telemetry.pod_uid is None
    assert telemetry.kubernetes_ready_replicas is None
    assert telemetry.metric_sources["kubernetes_resource_metadata"] == "UNAVAILABLE"
    assert telemetry.details["collection_mode"] == "worker-endpoint-only"


def test_endpoint_only_telemetry_rejects_non_kubernetes_worker_identity():
    with patch(
        "app.telemetry.kubernetes_collector._run_kubectl",
        return_value=(False, "", "kubectl executable not found"),
    ), patch(
        "app.telemetry.kubernetes_collector.requests.get",
        return_value=worker_health_response("LOCAL"),
    ):
        telemetry = collect_kubernetes_telemetry("kubernetes-edge")

    assert telemetry.health is False
    assert telemetry.endpoint_ready is False
    assert telemetry.network_data_type == "UNAVAILABLE"
