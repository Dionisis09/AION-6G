from app.models.intent import ServiceIntent
from app.orchestration.orchestrator import orchestrator


def test_orchestrator_returns_result_payload():
    result = orchestrator.orchestrate("Deploy a critical-control workload with latency below 20 ms and CPU below 70%", policy="adaptive", scenario="baseline", fallback_allowed=True)
    assert result["selected_target"] in {"local-edge", "kubernetes-edge"}
    assert "verification" in result
    assert "fallback" in result
