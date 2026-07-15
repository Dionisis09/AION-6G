import os

import pytest
import requests


pytestmark = pytest.mark.docker


@pytest.mark.skipif(
    os.getenv("AION_RUN_DOCKER_TESTS") != "1",
    reason="set AION_RUN_DOCKER_TESTS=1 with Docker Compose project aion6g running",
)
def test_docker_worker_executes_bounded_workload():
    health = requests.get("http://127.0.0.1:8001/health", timeout=3)
    health.raise_for_status()
    assert health.json()["execution_mode"] == "DOCKER"
    response = requests.post(
        "http://127.0.0.1:8001/execute",
        json={"workload_type": "critical-control", "iterations": 50, "payload_size": 32},
        timeout=5,
    )
    response.raise_for_status()
    payload = response.json()
    assert payload["runtime_execution_mode"] == "DOCKER"
    assert payload["checksum"]
