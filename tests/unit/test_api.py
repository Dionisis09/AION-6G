from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_ready_endpoint():
    response = client.get('/ready')
    assert response.status_code == 200
    assert response.json()['status'] == 'ready'


def test_profiles_endpoint():
    response = client.get('/api/v1/profiles')
    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_parse_intent_endpoint():
    response = client.post('/api/v1/parse-intent', json={'request': 'Deploy a critical control workload with latency below 20 ms'})
    assert response.status_code == 200
    assert response.json()['service_type'] == 'critical-control'


def test_orchestrate_endpoint():
    response = client.post('/api/v1/orchestrate', json={'request': 'Deploy a critical-control workload with latency below 20 ms and CPU below 70%', 'policy': 'adaptive', 'scenario': 'baseline'})
    assert response.status_code == 200
    assert 'selected_target' in response.json()
