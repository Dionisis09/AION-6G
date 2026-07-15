from app.models.telemetry import Telemetry


def test_telemetry_model_accepts_required_fields():
    telemetry = Telemetry(
        target="local-edge",
        health=True,
        cpu_utilization_percent=12.0,
        memory_utilization_percent=21.0,
        http_latency_ms=8.3,
        endpoint_ready=True,
        timestamp="2026-01-01T00:00:00Z",
        telemetry_source="local",
        network_data_type="MEASURED",
    )
    assert telemetry.target == "local-edge"
