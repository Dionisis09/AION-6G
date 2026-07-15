from app.orchestration.executor import execute_workload
from app.workloads.common import WorkloadError


def test_execute_critical_control_returns_checksum():
    result = execute_workload("critical-control", iterations=120, payload_size=32)
    assert result["workload_type"] == "critical-control"
    assert result["checksum"]


def test_execute_immersive_xr_returns_checksum():
    result = execute_workload("immersive-xr", iterations=80, payload_size=64)
    assert result["workload_type"] == "immersive-xr"
    assert result["checksum"]


def test_execute_massive_iot_returns_checksum():
    result = execute_workload("massive-iot", iterations=160, payload_size=16)
    assert result["workload_type"] == "massive-iot"
    assert result["checksum"]


def test_invalid_workload_type_raise_error():
    try:
        execute_workload("unknown", iterations=10, payload_size=8)
    except ValueError:
        return
    raise AssertionError("Expected ValueError")
