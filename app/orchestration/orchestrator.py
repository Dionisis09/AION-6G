from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import RESULTS_DIR
from app.intent.deterministic_parser import parse_intent
from app.models.intent import ServiceIntent
from app.orchestration.executor import execute_workload
from app.orchestration.eligibility import evaluate_eligibility
from app.orchestration.placement import score_candidate, select_target
from app.orchestration.verifier import verify_sla
from app.telemetry.emulation import build_emulated_network_profile
from app.telemetry.kubernetes_collector import collect_kubernetes_telemetry
from app.telemetry.local_collector import collect_local_telemetry
from app.telemetry.network_probe import measure_http_latency


class Orchestrator:
    def __init__(self) -> None:
        self.results_dir = RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def orchestrate(self, request: str, policy: str = "adaptive", scenario: str = "baseline", fallback_allowed: bool = True) -> dict[str, Any]:
        started = time.perf_counter()
        intent = parse_intent(request)
        network_profile = build_emulated_network_profile(scenario)

        local_telemetry = collect_local_telemetry("local-edge")
        k8s_telemetry = collect_kubernetes_telemetry("kubernetes-edge")

        if local_telemetry.http_latency_ms is None:
            local_telemetry.http_latency_ms = 0.0
        if k8s_telemetry.http_latency_ms is None:
            k8s_telemetry.http_latency_ms = 0.0

        candidates = [("local-edge", local_telemetry), ("kubernetes-edge", k8s_telemetry)]
        selected_target = None
        ranked = []
        if policy == "always-local":
            selected_target = "local-edge"
            ranked = [{"target": "local-edge", "telemetry": local_telemetry.model_dump(), "eligible": True, "rejection_reasons": [], "score": 1.0}]
        elif policy == "always-kubernetes":
            selected_target = "kubernetes-edge"
            ranked = [{"target": "kubernetes-edge", "telemetry": k8s_telemetry.model_dump(), "eligible": True, "rejection_reasons": [], "score": 1.0}]
        else:
            selected_target, ranked = select_target(intent, candidates)

        if selected_target is None:
            fallback_target = ranked[0]["target"] if ranked else "local-edge"
            selected_target = fallback_target
            execution = {"status": "skipped", "reason": "No eligible target"}
            verification = {"status": "FAILED", "checks": ["no eligible target"]}
            fallback = {"used": False, "reason": None}
            result = self._package_result(intent, ranked, selected_target, execution, verification, fallback, network_profile, started)
            self._write_result(result)
            return result

        selected_telemetry = dict(local_telemetry.model_dump()) if selected_target == "local-edge" else dict(k8s_telemetry.model_dump())
        execution = execute_workload(intent.service_type)
        verification = verify_sla(intent, execution, selected_telemetry, network_profile)

        fallback = {"used": False, "reason": None}
        if fallback_allowed and verification["status"] != "PASSED" and selected_target == "local-edge":
            fallback = {"used": True, "reason": "primary target failed verification"}
            selected_target = "kubernetes-edge"
            execution = execute_workload(intent.service_type)
            verification = verify_sla(intent, execution, dict(k8s_telemetry.model_dump()), network_profile)

        result = self._package_result(intent, ranked, selected_target, execution, verification, fallback, network_profile, started)
        self._write_result(result)
        return result

    def _package_result(self, intent: ServiceIntent, ranked: list[dict[str, Any]], selected_target: str | None, execution: dict[str, Any], verification: dict[str, Any], fallback: dict[str, Any], network_profile: dict[str, Any], started: float) -> dict[str, Any]:
        evidence_id = hashlib.sha256(json.dumps({"intent": intent.model_dump(), "execution": execution, "verification": verification}, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        return {
            "intent": intent.model_dump(),
            "candidates": ranked,
            "selected_target": selected_target,
            "execution": execution,
            "verification": verification,
            "fallback": fallback,
            "orchestration_time_ms": int((time.perf_counter() - started) * 1000),
            "evidence_id": evidence_id,
            "network_data_type": "EMULATED",
        }

    def _write_result(self, result: dict[str, Any]) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        path = self.results_dir / f"{ts}-{result['evidence_id']}.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")


orchestrator = Orchestrator()
