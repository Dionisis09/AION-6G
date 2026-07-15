import pytest

pytestmark = pytest.mark.skip(reason="Kubernetes integration tests require a kind cluster")


def test_kubernetes_worker_placeholder():
    assert True
