# Docker Validation

Status: **VERIFIED**

- Compose project: `aion6g`
- Containers: `aion6g-app`, `aion6g-local-worker`
- Health, readiness, profiles, telemetry, and bounded workload endpoints returned successfully.
- The worker reported `DOCKER`, produced a checksum, and reproduced the same checksum after a controlled container restart.
- Integration suite: 1 passed, 37 deselected.

Evidence: `results/docker_validation.json`
