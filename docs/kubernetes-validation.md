# Kubernetes Validation

Status: **VERIFIED**

- Cluster: `aion-6g-cluster`
- Context: `kind-aion-6g-cluster`
- Namespace: `aion-6g`
- Deployment/Service: `aion6g-worker`
- Service type: ClusterIP with localhost port-forwarding only
- Pod execution returned `KUBERNETES`, checksum, pod name, pod UID, container name, ready replicas, and restart count.
- Integration suite: 1 passed, 37 deselected.
- `kubectl top` returned `Metrics API not available`; Kubernetes CPU/RAM are therefore `UNAVAILABLE`.

Evidence: `results/kubernetes_validation.json`, `results/kubernetes_edge_success.json`
