from __future__ import annotations

from app.models.intent import ServiceIntent


def verify_sla(intent: ServiceIntent, execution: dict, telemetry: dict, network_profile: dict) -> dict:
    checks = []
    status = "PASSED"

    if execution.get("checksum"):
        checks.append("workload checksum produced")

    if intent.max_latency_ms is not None and telemetry.get("http_latency_ms") is not None and telemetry["http_latency_ms"] > intent.max_latency_ms:
        status = "FAILED"
        checks.append("latency constraint violated")

    if intent.max_cpu_percent is not None and telemetry.get("cpu_utilization_percent") is not None and telemetry["cpu_utilization_percent"] > intent.max_cpu_percent:
        status = "FAILED"
        checks.append("cpu constraint violated")

    if intent.max_packet_loss_percent is not None and network_profile.get("packet_loss_percent") is not None and network_profile["packet_loss_percent"] > intent.max_packet_loss_percent:
        status = "FAILED"
        checks.append("packet loss constraint violated")

    if status == "PASSED":
        checks.append("mandatory constraints satisfied")

    return {"status": status, "checks": checks}
