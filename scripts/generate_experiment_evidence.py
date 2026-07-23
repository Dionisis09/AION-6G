import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.experiments.summary import build_experiment_summary
from app.orchestration.orchestrator import orchestrator

rows = []
profiles = [
    ("critical-control", "Deploy a critical-control workload with latency below 20 ms and CPU below 70%"),
    ("immersive-xr", "Deploy an immersive-xr workload with latency below 30 ms and bandwidth above 50 Mbps and CPU below 75%"),
    ("massive-iot", "Deploy a massive-iot workload with latency below 100 ms and packet loss below 2% and CPU below 80%"),
]
for policy in ["always-local", "always-kubernetes", "adaptive"]:
    for index in range(20):
        profile_name, request = profiles[index % len(profiles)]
        scenario = "baseline"
        result = orchestrator.orchestrate(
            request,
            policy=policy,
            scenario=scenario,
            fallback_allowed=policy == "adaptive",
        )
        execution = result.get("execution", {})
        candidates = result.get("candidates", [])
        local_telemetry = next((candidate.get("telemetry", {}) for candidate in candidates if candidate.get("target") == "local-edge"), {})
        k8s_telemetry = next((candidate.get("telemetry", {}) for candidate in candidates if candidate.get("target") == "kubernetes-edge"), {})
        rows.append({
            "run_id": f"{policy}-{index + 1:02d}",
            "timestamp": result.get("created_at") or "",
            "policy": policy,
            "service_profile": profile_name,
            "scenario": scenario,
            "selected_target": result.get("selected_target"),
            "execution_mode": execution.get("execution_mode", "UNAVAILABLE"),
            "execution_success": result.get("verification", {}).get("status") == "PASSED",
            "sla_status": result.get("verification", {}).get("status"),
            "fallback_used": bool(result.get("fallback", {}).get("used")),
            "orchestration_time_ms": result.get("orchestration_time_ms"),
            "local_http_latency_ms": local_telemetry.get("http_latency_ms"),
            "kubernetes_http_latency_ms": k8s_telemetry.get("http_latency_ms"),
            "local_cpu_percent": local_telemetry.get("cpu_utilization_percent"),
            "kubernetes_cpu_percent": k8s_telemetry.get("cpu_utilization_percent"),
            "local_memory_percent": local_telemetry.get("memory_utilization_percent"),
            "kubernetes_memory_percent": k8s_telemetry.get("memory_utilization_percent"),
            "jitter_ms": result.get("network_profile", {}).get("jitter_ms"),
            "packet_loss_percent": result.get("network_profile", {}).get("packet_loss_percent"),
            "bandwidth_mbps": result.get("network_profile", {}).get("bandwidth_limit_mbps"),
            "network_data_type": result.get("network_data_type", "EMULATED"),
            "rejection_reasons": [reason for candidate in result.get("candidates", []) for reason in candidate.get("rejection_reasons", [])],
        })

out = PROJECT_ROOT / "results"
out.mkdir(exist_ok=True)
summary = build_experiment_summary(rows, out)
(out / "experiment_summary.json").write_text(json.dumps({"rows": len(rows), "results": rows}, indent=2), encoding="utf-8")
(out / "experiment_statistics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({"rows": len(rows), "summary": summary}, indent=2))
