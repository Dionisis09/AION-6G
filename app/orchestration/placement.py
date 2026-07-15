from __future__ import annotations

from app.models.intent import ServiceIntent
from app.models.telemetry import Telemetry
from app.orchestration.eligibility import evaluate_eligibility


def score_candidate(intent: ServiceIntent, telemetry: Telemetry) -> float:
    if telemetry.http_latency_ms is None:
        latency_component = 0.0
    else:
        latency_component = max(0.0, 1.0 - (telemetry.http_latency_ms / (intent.max_latency_ms * 2)))

    cpu_component = 1.0
    if telemetry.cpu_utilization_percent is not None and intent.max_cpu_percent is not None:
        cpu_component = max(0.0, 1.0 - (telemetry.cpu_utilization_percent / intent.max_cpu_percent))

    memory_component = 1.0
    if telemetry.memory_utilization_percent is not None and intent.max_memory_percent is not None:
        memory_component = max(0.0, 1.0 - (telemetry.memory_utilization_percent / intent.max_memory_percent))

    reliability_component = 1.0 if telemetry.health else 0.0
    readiness_component = 1.0 if telemetry.endpoint_ready else 0.0

    if intent.priority == "reliability":
        priority_component = 1.0
    elif intent.priority == "latency":
        priority_component = 0.9
    else:
        priority_component = 0.8

    return round((latency_component * 0.3) + (cpu_component * 0.2) + (memory_component * 0.2) + (reliability_component * 0.15) + (readiness_component * 0.15) + (priority_component * 0.0), 2)


def select_target(intent: ServiceIntent, candidates: list[tuple[str, Telemetry]]) -> tuple[str | None, list[dict[str, object]]]:
    ranked: list[dict[str, object]] = []
    for target, telemetry in candidates:
        eligible, reasons = evaluate_eligibility(intent, telemetry)
        score = score_candidate(intent, telemetry) if eligible else None
        ranked.append({
            "target": target,
            "telemetry": telemetry.model_dump(),
            "eligible": eligible,
            "rejection_reasons": reasons,
            "score": score,
        })

    eligible = [item for item in ranked if item["eligible"]]
    if not eligible:
        return None, ranked

    best = sorted(eligible, key=lambda item: item["score"], reverse=True)[0]
    return best["target"], ranked
