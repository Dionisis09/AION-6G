# Kubernetes Validation

Status: **VERIFIED**

- Cluster: `aion-6g-cluster`
- Context: current `kubectl` context at validation time
- Namespace: `aion-6g`
- Deployment/Service: `aion6g-worker`
- Service type: ClusterIP. Host-side validation uses a localhost-only port-forward.
- Dockerized API validation uses `scripts/port_forward_kubernetes.ps1 -ForDocker`, which emits a security warning and creates a temporary host-reachable listener.
- Pod execution returned `KUBERNETES`, checksum, pod name, pod UID, container name, ready replicas, and restart count.
- Host-to-Kubernetes integration: 1 passed.
- Dockerized API-to-Kubernetes regression: 1 passed.
- `kubectl top` returned `Metrics API not available`; Kubernetes CPU/RAM are therefore `UNAVAILABLE`.

Evidence: `results/kubernetes_validation.json`, `results/kubernetes_edge_success.json`
