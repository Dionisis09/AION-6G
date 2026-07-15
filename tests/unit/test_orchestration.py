from app.models.intent import ServiceIntent
from app.orchestration.eligibility import evaluate_eligibility
from app.orchestration.placement import score_candidate, select_target
from app.orchestration.verifier import verify_sla
from app.telemetry.emulation import build_emulated_network_profile
from app.models.telemetry import Telemetry


def test_evaluate_eligibility_rejects_high_cpu():
    intent = ServiceIntent.model_validate({
        "service_type": "critical-control",
        "max_latency_ms": 20,
        "max_jitter_ms": 2,
        "max_packet_loss_percent": 0.1,
        "max_cpu_percent": 70,
        "priority": "reliability",
    })
    telemetry = Telemetry(
        target="local-edge",
        health=True,
        cpu_utilization_percent=80,
        memory_utilization_percent=40,
        http_latency_ms=10,
        endpoint_ready=True,
        timestamp="now",
        telemetry_source="local",
        network_data_type="MEASURED",
    )
    eligible, reasons = evaluate_eligibility(intent, telemetry)
    assert not eligible
    assert any("CPU" in reason for reason in reasons)


def test_score_candidate_is_deterministic():
    intent = ServiceIntent.model_validate({
        "service_type": "critical-control",
        "max_latency_ms": 20,
        "max_jitter_ms": 2,
        "max_packet_loss_percent": 0.1,
        "max_cpu_percent": 70,
        "priority": "reliability",
    })
    telemetry = Telemetry(
        target="local-edge",
        health=True,
        cpu_utilization_percent=40,
        memory_utilization_percent=30,
        http_latency_ms=8,
        endpoint_ready=True,
        timestamp="now",
        telemetry_source="local",
        network_data_type="MEASURED",
    )
    assert score_candidate(intent, telemetry) == 0.83


def test_select_target_returns_none_without_eligible_candidates():
    intent = ServiceIntent.model_validate({
        "service_type": "critical-control",
        "max_latency_ms": 20,
        "max_jitter_ms": 2,
        "max_packet_loss_percent": 0.1,
        "max_cpu_percent": 20,
        "priority": "reliability",
    })
    telemetry = Telemetry(
        target="local-edge",
        health=True,
        cpu_utilization_percent=80,
        memory_utilization_percent=40,
        http_latency_ms=10,
        endpoint_ready=True,
        timestamp="now",
        telemetry_source="local",
        network_data_type="MEASURED",
    )
    target, ranked = select_target(intent, [("local-edge", telemetry)])
    assert target is None
    assert ranked[0]["eligible"] is False


def test_verify_sla_passes_with_constraints_met():
    intent = ServiceIntent.model_validate({
        "service_type": "critical-control",
        "max_latency_ms": 20,
        "max_jitter_ms": 2,
        "max_packet_loss_percent": 0.1,
        "max_cpu_percent": 70,
        "priority": "reliability",
    })
    result = verify_sla(intent, {"checksum": "abc"}, {"http_latency_ms": 10, "cpu_utilization_percent": 10}, {"packet_loss_percent": 0.05})
    assert result["status"] == "PASSED"


def test_verify_sla_fails_on_packet_loss():
    intent = ServiceIntent.model_validate({
        "service_type": "critical-control",
        "max_latency_ms": 20,
        "max_jitter_ms": 2,
        "max_packet_loss_percent": 0.1,
        "max_cpu_percent": 70,
        "priority": "reliability",
    })
    result = verify_sla(intent, {"checksum": "abc"}, {"http_latency_ms": 10, "cpu_utilization_percent": 10}, {"packet_loss_percent": 0.5})
    assert result["status"] == "FAILED"


def test_emulation_profile_contains_expected_keys():
    profile = build_emulated_network_profile("baseline")
    assert profile["additional_latency_ms"] == 0
    assert profile["packet_loss_percent"] == 0
