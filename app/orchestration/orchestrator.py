from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

from app.config import RESULTS_DIR
from app.intent.deterministic_parser import parse_intent
from app.models.intent import ServiceIntent
from app.models.telemetry import Telemetry
from app.orchestration.eligibility import evaluate_eligibility
from app.orchestration.executor import execute_remote_workload
from app.orchestration.placement import score_candidate, select_target
from app.orchestration.verifier import verify_sla
from app.telemetry.emulation import build_emulated_network_profile
from app.telemetry.kubernetes_collector import collect_kubernetes_telemetry
from app.telemetry.local_collector import collect_local_telemetry


class Orchestrator:
    def __init__(self) -> None:
        self.results_dir = RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _build_failed_execution(
        self,
        intent: ServiceIntent,
        target: str | None,
        telemetry: dict[str, Any],
        reason: str,
        mode: str = "UNAVAILABLE",
    ) -> dict[str, Any]:
        return {
            "status": "failed",
            "reason": reason,
            "workload_type": intent.service_type,
            "iterations": 200,
            "payload_size": 64,
            "checksum": None,
            "execution_latency_ms": None,
            "execution_mode": mode,
            "target": target,
            "worker_endpoint": telemetry.get("worker_endpoint"),
            "telemetry_source": telemetry.get("telemetry_source"),
            "network_data_type": telemetry.get("network_data_type", "UNAVAILABLE"),
            "start_timestamp": None,
            "end_timestamp": None,
        }

    def _execute_target(self, intent: ServiceIntent, target: str, telemetry: dict[str, Any]) -> dict[str, Any]:
        if not telemetry.get("health") or not telemetry.get("endpoint_ready"):
            return self._build_failed_execution(
                intent, target, telemetry, f"{target} is unavailable: endpoint or runtime is not ready"
            )

        endpoint = telemetry.get("worker_endpoint")
        if not endpoint:
            return self._build_failed_execution(intent, target, telemetry, "worker endpoint is missing")

        expected_mode = "KUBERNETES" if target == "kubernetes-edge" else "LOCAL"
        try:
            execution = execute_remote_workload(endpoint, intent.service_type)
        except Exception as exc:
            return self._build_failed_execution(
                intent, target, telemetry, f"worker request failed: {exc}", mode=expected_mode
            )

        runtime_mode = execution.pop("runtime_execution_mode", None)
        if target == "kubernetes-edge" and runtime_mode != "KUBERNETES":
            return self._build_failed_execution(
                intent,
                target,
                telemetry,
                f"worker runtime identity mismatch: expected KUBERNETES, received {runtime_mode!r}",
            )
        if target == "local-edge" and runtime_mode not in {"LOCAL", "DOCKER"}:
            return self._build_failed_execution(
                intent,
                target,
                telemetry,
                f"worker runtime identity mismatch: expected LOCAL or DOCKER, received {runtime_mode!r}",
            )

        execution.update({
            "execution_mode": runtime_mode,
            "target": target,
            "worker_endpoint": endpoint,
            "telemetry_source": telemetry.get("telemetry_source"),
            "network_data_type": telemetry.get("network_data_type"),
        })
        if target == "kubernetes-edge":
            for field in (
                "cluster_name", "namespace", "deployment", "pod_name", "pod_uid",
                "container_name", "kubernetes_desired_replicas", "kubernetes_ready_replicas",
                "pod_restart_count",
            ):
                worker_value = execution.get(field)
                telemetry_value = telemetry.get(field)
                if worker_value is not None and telemetry_value is not None and worker_value != telemetry_value:
                    return self._build_failed_execution(
                        intent, target, telemetry, f"Kubernetes metadata mismatch for {field}"
                    )
                execution[field] = telemetry_value if telemetry_value is not None else worker_value
            execution["ready_replicas"] = telemetry.get("kubernetes_ready_replicas")
            execution["restart_count"] = telemetry.get("pod_restart_count")
        return execution

    def _build_verification(
        self,
        intent: ServiceIntent,
        execution: dict[str, Any],
        telemetry: dict[str, Any],
        network_profile: dict[str, Any],
    ) -> dict[str, Any]:
        if execution.get("execution_mode") in {"UNAVAILABLE", "SIMULATED"}:
            return {"status": "FAILED", "checks": [execution.get("reason", "real execution unavailable")]}
        return verify_sla(intent, execution, telemetry, network_profile)

    def _apply_scenario(
        self,
        scenario: str,
        local: Telemetry,
        kubernetes: Telemetry,
    ) -> tuple[Telemetry, Telemetry, list[dict[str, Any]]]:
        local = local.model_copy(deep=True)
        kubernetes = kubernetes.model_copy(deep=True)
        overrides: list[dict[str, Any]] = []
        if scenario == "local-high-cpu":
            local.cpu_utilization_percent = 99.0
            local.metric_sources["cpu_utilization_percent"] = "CONTROLLED"
            local.network_data_type = "CONTROLLED"
            overrides.append({"target": "local-edge", "metric": "cpu_utilization_percent", "value": 99.0, "source": "CONTROLLED"})
        elif scenario == "kubernetes-high-latency" and kubernetes.http_latency_ms is not None:
            kubernetes.http_latency_ms += 35.0
            kubernetes.metric_sources["http_latency_ms"] = "EMULATED"
            overrides.append({"target": "kubernetes-edge", "metric": "http_latency_ms", "added_value": 35.0, "source": "EMULATED"})
        elif scenario == "no-eligible-target":
            for item in (local, kubernetes):
                item.health = False
                item.endpoint_ready = False
                item.network_data_type = "CONTROLLED"
            overrides.append({"targets": ["local-edge", "kubernetes-edge"], "metric": "availability", "value": False, "source": "CONTROLLED"})
        return local, kubernetes, overrides

    @staticmethod
    def _rank_forced(intent: ServiceIntent, target: str, telemetry: Telemetry) -> list[dict[str, Any]]:
        eligible, reasons = evaluate_eligibility(intent, telemetry)
        return [{
            "target": target,
            "telemetry": telemetry.model_dump(),
            "eligible": eligible,
            "rejection_reasons": reasons,
            "score": score_candidate(intent, telemetry) if eligible else None,
        }]

    def orchestrate(
        self,
        request: str,
        policy: str = "adaptive",
        scenario: str = "baseline",
        fallback_allowed: bool = True,
    ) -> dict[str, Any]:
        if policy not in {"always-local", "always-kubernetes", "adaptive"}:
            raise ValueError(f"Unsupported policy: {policy}")
        started = time.perf_counter()
        intent = parse_intent(request)
        network_profile = build_emulated_network_profile(scenario)
        local, kubernetes, overrides = self._apply_scenario(
            scenario,
            collect_local_telemetry("local-edge"),
            collect_kubernetes_telemetry("kubernetes-edge"),
        )
        candidates = [("local-edge", local), ("kubernetes-edge", kubernetes)]

        if policy == "always-local":
            selected_target = "local-edge"
            ranked = self._rank_forced(intent, selected_target, local)
        elif policy == "always-kubernetes":
            selected_target = "kubernetes-edge"
            ranked = self._rank_forced(intent, selected_target, kubernetes)
        else:
            selected_target, ranked = select_target(intent, candidates)

        if selected_target is None:
            execution = self._build_failed_execution(intent, None, {}, "No eligible target")
            verification = {"status": "FAILED", "checks": ["no eligible target"]}
            fallback = {"used": False, "retry_count": 0, "reason": None, "attempts": []}
            result = self._package_result(
                request, policy, scenario, intent, ranked, None, execution, verification,
                fallback, network_profile, overrides, started,
            )
            self._write_result(result)
            return result

        telemetry_by_target = {
            "local-edge": local.model_dump(),
            "kubernetes-edge": kubernetes.model_dump(),
        }
        selected_telemetry = telemetry_by_target[selected_target]
        controlled_failure = scenario == "selected-target-failure" and selected_target == "local-edge"
        if controlled_failure:
            overrides.append({
                "target": "local-edge",
                "metric": "execution_availability",
                "value": False,
                "source": "CONTROLLED",
            })
            execution = self._build_failed_execution(
                intent, "local-edge", selected_telemetry, "controlled local execution failure", mode="LOCAL"
            )
            execution["failure_source"] = "CONTROLLED"
            verification = {"status": "FAILED", "checks": ["controlled local execution failure"]}
        else:
            execution = self._execute_target(intent, selected_target, selected_telemetry)
            verification = self._build_verification(intent, execution, selected_telemetry, network_profile)
        fallback = {"used": False, "retry_count": 0, "reason": None, "attempts": []}

        should_fallback = (
            fallback_allowed
            and selected_target == "local-edge"
            and verification.get("status") != "PASSED"
        )
        if should_fallback:
            primary_attempt = {
                "target": selected_target,
                "execution": execution,
                "verification": verification,
            }
            fallback = {
                "used": True,
                "retry_count": 1,
                "reason": "primary target failed verification",
                "attempts": [primary_attempt],
            }
            selected_target = "kubernetes-edge"
            selected_telemetry = telemetry_by_target[selected_target]
            execution = self._execute_target(intent, selected_target, selected_telemetry)
            verification = self._build_verification(intent, execution, selected_telemetry, network_profile)
            fallback["attempts"].append({
                "target": selected_target,
                "execution": execution,
                "verification": verification,
            })
            if verification.get("status") != "PASSED":
                fallback["reason"] = "primary target failed; fallback target did not complete successfully"

        result = self._package_result(
            request, policy, scenario, intent, ranked, selected_target, execution, verification,
            fallback, network_profile, overrides, started,
        )
        self._write_result(result)
        return result

    def _package_result(
        self,
        request: str,
        policy: str,
        scenario: str,
        intent: ServiceIntent,
        ranked: list[dict[str, Any]],
        selected_target: str | None,
        execution: dict[str, Any],
        verification: dict[str, Any],
        fallback: dict[str, Any],
        network_profile: dict[str, Any],
        overrides: list[dict[str, Any]],
        started: float,
    ) -> dict[str, Any]:
        evidence_id = hashlib.sha256(json.dumps({
            "request": request,
            "intent": intent.model_dump(),
            "execution": execution,
            "verification": verification,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        return {
            "original_request": request,
            "policy": policy,
            "scenario": scenario,
            "intent": intent.model_dump(),
            "candidates": ranked,
            "selected_target": selected_target,
            "execution_mode": execution.get("execution_mode", "UNAVAILABLE"),
            "worker_endpoint": execution.get("worker_endpoint"),
            "telemetry_source": execution.get("telemetry_source"),
            "network_data_type": "EMULATED",
            "network_profile": network_profile,
            "scenario_overrides": overrides,
            "execution": execution,
            "verification": verification,
            "verification_status": verification.get("status"),
            "fallback": fallback,
            "orchestration_time_ms": round((time.perf_counter() - started) * 1000.0, 3),
            "evidence_id": evidence_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _write_result(self, result: dict[str, Any]) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        path = self.results_dir / f"{ts}-{result['evidence_id']}.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")


orchestrator = Orchestrator()
