# Final Validation

Classification: **VALIDATED EXPERIMENTAL PROTOTYPE**

Latest live revalidation: **2026-07-18T19:31:10.165433+00:00** on the local Windows, Docker Desktop and isolated kind environment.

## Test Results

- Complete suite: 42 passed.
- Standard suite: 39 passed, 3 runtime tests deselected.
- Docker worker integration: 1 passed.
- Host-to-Kubernetes integration: 1 passed.
- Dockerized API-to-Kubernetes regression: 1 passed.

## Capability Matrix

- **local FastAPI - VERIFIED**: /health and /ready returned 200 Evidence: `results/docker_validation.json`. Limitation: None
- **local-edge worker - VERIFIED**: The dedicated Compose worker returned DOCKER identity and a checksum; a directly launched host worker returns LOCAL Evidence: `results/policy_always_local.json`. Limitation: None
- **Docker runtime - VERIFIED**: DOCKER worker passed and recovered after restart with a consistent checksum Evidence: `results/docker_validation.json`. Limitation: None
- **kind cluster - VERIFIED**: The isolated aion-6g-cluster is available Evidence: `results/kubernetes_validation.json`. Limitation: None
- **Kubernetes worker - VERIFIED**: 1/1 ready pod, zero restarts at validation Evidence: `results/kubernetes_validation.json`. Limitation: None
- **kubernetes-edge workload - VERIFIED**: Real pod returned runtime identity, checksum, and pod UID Evidence: `results/kubernetes_edge_success.json`. Limitation: None
- **Docker API-to-Kubernetes path - VERIFIED**: The Compose API reached the real worker pod and verified pod UID plus checksum Evidence: `results/kubernetes_edge_success.json`. Limitation: Requires scripts/port_forward_kubernetes.ps1 -ForDocker on a trusted development machine
- **always-local - VERIFIED**: local-edge execution PASSED (DOCKER mode in the Compose validation) Evidence: `results/policy_always_local.json`. Limitation: None
- **always-kubernetes - VERIFIED**: KUBERNETES execution PASSED Evidence: `results/policy_always_kubernetes.json`. Limitation: None
- **adaptive - VERIFIED**: Deterministic scoring evaluated both targets Evidence: `results/policy_adaptive.json`. Limitation: None
- **adaptive local selection - VERIFIED**: Healthy baseline selected LOCAL and PASSED Evidence: `results/adaptive_selects_local.json`. Limitation: None
- **adaptive Kubernetes selection - VERIFIED**: CONTROLLED local high CPU selected Kubernetes and PASSED Evidence: `results/adaptive_selects_kubernetes.json`. Limitation: None
- **real fallback - VERIFIED**: One controlled local failure, one retry, real pod success Evidence: `results/fallback_real_success.json`. Limitation: None
- **three profiles - VERIFIED**: All three profiles PASSED across local-edge and Kubernetes targets Evidence: `results/profile_critical_control.json`. Limitation: None
- **six scenarios - FUNCTIONAL**: Five successful flows and expected no-eligible failure Evidence: `results/scenario_no_eligible_target.json`. Limitation: None
- **experiment runner - VERIFIED**: 60 rows, 56 PASSED, failures retained Evidence: `results/experiment_summary.csv`. Limitation: None
- **CPU telemetry - PARTIAL**: Local CPU MEASURED; Kubernetes CPU UNAVAILABLE Evidence: `results/kubernetes_validation.json`. Limitation: metrics-server Metrics API unavailable
- **RAM telemetry - PARTIAL**: Local RAM MEASURED; Kubernetes RAM UNAVAILABLE Evidence: `results/kubernetes_validation.json`. Limitation: metrics-server Metrics API unavailable
- **HTTP latency - VERIFIED**: Local and Kubernetes endpoint latency MEASURED Evidence: `results/experiment_summary.csv`. Limitation: None
- **jitter - EMULATED**: Explicitly classified EMULATED Evidence: `results/scenario_kubernetes_high_latency.json`. Limitation: No packet-level measurement tool
- **packet loss - EMULATED**: Explicitly classified EMULATED Evidence: `results/scenario_packet_loss_degradation.json`. Limitation: No packet-level measurement tool
- **bandwidth - EMULATED**: Explicitly classified EMULATED Evidence: `results/scenario_baseline.json`. Limitation: No throughput measurement tool
- **security scan - VERIFIED**: 0 findings Evidence: `results/security_scan.json`. Limitation: None

## Limitations

- Kubernetes CPU/RAM percentages are unavailable because metrics-server is not installed.
- Jitter, packet loss, and bandwidth are emulated rather than radio/network measurements.
- Four of 60 experiment rows failed SLA checks and remain labelled as failures.
- This is an experimental Cloud-Edge testbed, not production telecom infrastructure.
- Detailed JSON/CSV evidence under results is generated locally and ignored by Git.
