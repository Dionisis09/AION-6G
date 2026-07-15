from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
TIMESTAMPED = re.compile(r"^\d{8}T\d{6}(?:\d{6})?-[0-9a-f]{16}\.json$")

changed = []
for path in RESULTS.glob("*.json"):
    if not TIMESTAMPED.match(path.name):
        continue
    payload = json.loads(path.read_text(encoding="utf-8"))
    execution = payload.get("execution") or {}
    if (
        payload.get("selected_target") == "kubernetes-edge"
        and payload.get("verification", {}).get("status") == "PASSED"
        and execution.get("execution_mode") != "KUBERNETES"
        and not execution.get("worker_endpoint")
        and not execution.get("pod_name")
    ):
        payload["legacy_original_claim"] = {
            "execution": copy.deepcopy(execution),
            "verification": copy.deepcopy(payload.get("verification")),
        }
        payload["historical_classification"] = "INVALID_LEGACY_LOCAL_EXECUTION_MISLABELLED_AS_KUBERNETES"
        execution.update({
            "status": "failed",
            "execution_mode": "SIMULATED",
            "reason": "legacy artifact lacked a live Kubernetes worker response and pod metadata",
            "worker_endpoint": None,
            "pod_name": None,
            "pod_uid": None,
            "cluster_name": None,
        })
        payload["execution"] = execution
        payload["execution_mode"] = "SIMULATED"
        payload["verification"] = {
            "status": "FAILED",
            "checks": ["invalid legacy Kubernetes claim reclassified during full validation"],
        }
        payload["verification_status"] = "FAILED"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        changed.append(path.name)

audit = {
    "classification": "HISTORICAL_EVIDENCE_AUDIT",
    "reclassified_count": len(changed),
    "reclassified_files": changed,
    "rule": "kubernetes-edge PASSED without KUBERNETES mode, worker endpoint, or pod metadata",
}
(RESULTS / "historical_artifact_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(json.dumps(audit, indent=2))
