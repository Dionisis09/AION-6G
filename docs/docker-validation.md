# Docker Validation

Status: **VERIFIED**

- Compose project: `aion6g`
- Containers: `aion6g-app`, `aion6g-local-worker`
- Health, readiness, profiles, telemetry, and bounded workload endpoints returned successfully.
- The worker reported `DOCKER`, produced a checksum, and reproduced the same checksum after a controlled container restart.
- Docker worker integration: 1 passed.
- The Dockerized API-to-Kubernetes regression also passed when the explicit Docker-reachable port-forward was active.

Evidence: `results/docker_validation.json`
