from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT_DIR / "profiles"
RESULTS_DIR = ROOT_DIR / "results"
DEPLOYMENTS_DIR = ROOT_DIR / "deployments"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()

LOCAL_WORKER_HOST = os.getenv("LOCAL_WORKER_HOST", "127.0.0.1")
LOCAL_WORKER_PORT = int(os.getenv("LOCAL_WORKER_PORT", "8001"))
LOCAL_WORKER_URL = os.getenv("LOCAL_WORKER_URL", f"http://{LOCAL_WORKER_HOST}:{LOCAL_WORKER_PORT}")

KUBERNETES_WORKER_URL = os.getenv("KUBERNETES_WORKER_URL", "http://127.0.0.1:8002")
KUBERNETES_CLUSTER_NAME = os.getenv("KUBERNETES_CLUSTER_NAME", "aion-6g-cluster")
KUBERNETES_CONTEXT = os.getenv("KUBERNETES_CONTEXT", f"kind-{KUBERNETES_CLUSTER_NAME}")
KUBERNETES_NAMESPACE = os.getenv("KUBERNETES_NAMESPACE", "aion-6g")
KUBERNETES_DEPLOYMENT = os.getenv("KUBERNETES_DEPLOYMENT", "aion6g-worker")
KUBERNETES_CONTAINER = os.getenv("KUBERNETES_CONTAINER", "aion6g-worker")

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
