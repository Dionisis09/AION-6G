from __future__ import annotations

from copy import deepcopy
from typing import Any


def build_emulated_network_profile(scenario: str) -> dict[str, Any]:
    profiles = {
        "baseline": {"additional_latency_ms": 0, "jitter_ms": 0, "packet_loss_percent": 0, "bandwidth_limit_mbps": 1000},
        "local-high-cpu": {"additional_latency_ms": 0, "jitter_ms": 0, "packet_loss_percent": 0, "bandwidth_limit_mbps": 1000},
        "kubernetes-high-latency": {"additional_latency_ms": 35, "jitter_ms": 2, "packet_loss_percent": 0.1, "bandwidth_limit_mbps": 100},
        "packet-loss-degradation": {"additional_latency_ms": 5, "jitter_ms": 1, "packet_loss_percent": 1.5, "bandwidth_limit_mbps": 80},
        "selected-target-failure": {"additional_latency_ms": 0, "jitter_ms": 0, "packet_loss_percent": 0, "bandwidth_limit_mbps": 1000},
        "no-eligible-target": {"additional_latency_ms": 15, "jitter_ms": 3, "packet_loss_percent": 2, "bandwidth_limit_mbps": 20},
    }
    if scenario not in profiles:
        raise ValueError(f"Unsupported scenario: {scenario}")
    return deepcopy(profiles[scenario])
