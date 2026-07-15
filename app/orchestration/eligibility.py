from __future__ import annotations

from app.models.telemetry import Telemetry
from app.models.intent import ServiceIntent


def evaluate_eligibility(intent: ServiceIntent, telemetry: Telemetry) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not telemetry.health:
        reasons.append("Target is unhealthy")
    if telemetry.cpu_utilization_percent is not None and intent.max_cpu_percent is not None and telemetry.cpu_utilization_percent > intent.max_cpu_percent:
        reasons.append("CPU utilization exceeds the requested maximum")
    if telemetry.memory_utilization_percent is not None and intent.max_memory_percent is not None and telemetry.memory_utilization_percent > intent.max_memory_percent:
        reasons.append("Memory utilization exceeds the requested maximum")
    if telemetry.http_latency_ms is not None and intent.max_latency_ms is not None and telemetry.http_latency_ms > intent.max_latency_ms:
        reasons.append("Measured HTTP latency exceeds the requested maximum")
    if telemetry.endpoint_ready is False:
        reasons.append("Execution endpoint is not ready")
    return len(reasons) == 0, reasons
