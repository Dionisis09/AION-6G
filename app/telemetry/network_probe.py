from __future__ import annotations

import time
from typing import Any

import requests


def measure_http_latency(url: str) -> float | None:
    try:
        start = time.perf_counter()
        response = requests.get(url, timeout=2.0)
        if response.status_code >= 400:
            return None
        return (time.perf_counter() - start) * 1000.0
    except Exception:
        return None
