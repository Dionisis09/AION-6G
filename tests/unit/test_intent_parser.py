import pytest

from app.intent.deterministic_parser import parse_intent
from app.models.intent import ServiceIntent


def test_parse_critical_control_intent():
    result = parse_intent("Deploy a critical control workload with latency below 20 ms and CPU below 70 percent")
    assert result.service_type == "critical-control"
    assert result.max_latency_ms == 20
    assert result.max_cpu_percent == 70


def test_parse_immersive_xr_intent():
    result = parse_intent("Run immersive XR with latency below 15 ms and bandwidth above 50 mbps")
    assert result.service_type == "immersive-xr"
    assert result.max_latency_ms == 15
    assert result.min_bandwidth_mbps == 50


def test_parse_massive_iot_intent():
    result = parse_intent("Process massive IoT traffic with packet loss under 2 percent")
    assert result.service_type == "massive-iot"
    assert result.max_packet_loss_percent == 2


def test_parse_reliability_priority():
    result = parse_intent("Prioritize reliability for this workload")
    assert result.priority == "reliability"


def test_parse_low_latency_priority():
    result = parse_intent("Prioritize low latency")
    assert result.priority == "latency"


def test_parse_jitter_and_packet_loss():
    result = parse_intent("Jitter below 2 ms and packet loss under 0.1 percent")
    assert result.max_jitter_ms == 2
    assert result.max_packet_loss_percent == 0.1


@pytest.mark.parametrize(
    "text",
    [
        "Deploy a critical control workload with latency below 20 ms and CPU below 70 percent",
        "Run immersive XR with latency below 15 ms and bandwidth above 50 mbps",
        "Process massive IoT traffic with packet loss under 2 percent",
    ],
)
def test_parsing_examples_are_valid(text):
    result = parse_intent(text)
    assert isinstance(result, ServiceIntent)


def test_invalid_intent_rejected_for_negative_latency():
    with pytest.raises(ValueError):
        parse_intent("Latency below -5 ms")


def test_invalid_intent_rejected_for_non_numeric_cpu():
    with pytest.raises(ValueError):
        parse_intent("CPU below ten percent")


def test_invalid_intent_rejected_for_conflicting_priority():
    with pytest.raises(ValueError):
        parse_intent("Prioritize reliability and scalability")
