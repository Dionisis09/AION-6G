import os
import time

import pytest
import requests


pytestmark = [pytest.mark.docker, pytest.mark.kubernetes]


@pytest.mark.skipif(
    os.getenv("AION_RUN_DOCKER_KUBERNETES_TESTS") != "1",
    reason="set AION_RUN_DOCKER_KUBERNETES_TESTS=1 with Compose and Docker-reachable Kubernetes port-forward running",
)
def test_dockerized_api_executes_on_real_kubernetes_worker():
    deadline = time.monotonic() + 30
    while True:
        try:
            ready = requests.get("http://127.0.0.1:8000/ready", timeout=2)
            if ready.status_code == 200:
                break
        except requests.RequestException:
            pass
        if time.monotonic() >= deadline:
            pytest.fail("Dockerized AION-6G API did not become ready within 30 seconds")
        time.sleep(0.5)

    response = requests.post(
        "http://127.0.0.1:8000/api/v1/orchestrate",
        json={
            "request": "Deploy a massive-iot workload with latency below 100 ms and CPU below 80%",
            "policy": "always-kubernetes",
            "scenario": "baseline",
            "fallback_allowed": False,
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()

    assert payload["selected_target"] == "kubernetes-edge"
    assert payload["execution_mode"] == "KUBERNETES"
    assert payload["execution"]["pod_uid"]
    assert payload["execution"]["checksum"]
    assert payload["verification_status"] == "PASSED"
