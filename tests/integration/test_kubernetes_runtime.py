import os

import pytest

from app.orchestration.orchestrator import orchestrator


pytestmark = pytest.mark.kubernetes


@pytest.mark.skipif(
    os.getenv("AION_RUN_KUBERNETES_TESTS") != "1",
    reason="set AION_RUN_KUBERNETES_TESTS=1 with aion-6g-cluster and port-forward running",
)
def test_real_kubernetes_worker_execution():
    result = orchestrator.orchestrate(
        "Deploy a massive-iot workload with latency below 100 ms and CPU below 80%",
        policy="always-kubernetes",
        fallback_allowed=False,
    )
    assert result["execution_mode"] == "KUBERNETES"
    assert result["execution"]["cluster_name"] == "aion-6g-cluster"
    assert result["execution"]["namespace"] == "aion-6g"
    assert result["execution"]["pod_uid"]
    assert result["execution"]["checksum"]
    assert result["verification_status"] == "PASSED"
