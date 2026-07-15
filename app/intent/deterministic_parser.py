from __future__ import annotations

import re
from typing import Any

from app.models.intent import ServiceIntent


_PROFILE_DEFAULTS = {
    "critical-control": {
        "service_type": "critical-control",
        "max_latency_ms": 20,
        "max_jitter_ms": 2,
        "max_packet_loss_percent": 0.1,
        "max_cpu_percent": 70,
        "priority": "reliability",
    },
    "immersive-xr": {
        "service_type": "immersive-xr",
        "max_latency_ms": 15,
        "max_jitter_ms": 4,
        "max_packet_loss_percent": 0.5,
        "min_bandwidth_mbps": 50,
        "max_cpu_percent": 75,
        "priority": "latency",
    },
    "massive-iot": {
        "service_type": "massive-iot",
        "max_latency_ms": 100,
        "max_packet_loss_percent": 2,
        "max_cpu_percent": 80,
        "priority": "scalability",
    },
}


def parse_intent(text: str) -> ServiceIntent:
    normalized = text.lower().strip()
    if not normalized:
        raise ValueError("Request text cannot be empty")

    profile = None
    for name in _PROFILE_DEFAULTS:
        if name in normalized or name.replace("-", " ") in normalized:
            profile = name
            break

    values: dict[str, Any] = {
        "service_type": profile or "critical-control",
        "max_latency_ms": 1000,
        "priority": "reliability",
        "fallback_allowed": True,
    }

    if profile is None:
        if "immersive" in normalized or "xr" in normalized:
            values["service_type"] = "immersive-xr"
        elif "massive" in normalized or "iot" in normalized:
            values["service_type"] = "massive-iot"
        else:
            values["service_type"] = "critical-control"

    if "critical" in normalized or "control" in normalized:
        values["service_type"] = "critical-control"
    if "immersive" in normalized or "xr" in normalized:
        values["service_type"] = "immersive-xr"
    if "massive" in normalized or "iot" in normalized:
        values["service_type"] = "massive-iot"

    if profile is None:
        for name, defaults in _PROFILE_DEFAULTS.items():
            if values["service_type"] == name:
                profile = name
                break

    defaults = _PROFILE_DEFAULTS.get(values["service_type"], {})
    values.update(defaults)

    latency_match = re.search(r"latency\s+(?:below|under|less than|less|up to|max\s*of)?\s*(\d+(?:\.\d+)?)", normalized)
    if latency_match:
        values["max_latency_ms"] = float(latency_match.group(1))

    jitter_match = re.search(r"jitter\s+(?:below|under|less than|less|up to|max\s*of)?\s*(\d+(?:\.\d+)?)", normalized)
    if jitter_match:
        values["max_jitter_ms"] = float(jitter_match.group(1))

    packet_loss_match = re.search(r"packet\s+loss\s+(?:below|under|less than|less|up to|max\s*of)?\s*(\d+(?:\.\d+)?)", normalized)
    if packet_loss_match:
        values["max_packet_loss_percent"] = float(packet_loss_match.group(1))

    bandwidth_match = re.search(r"bandwidth\s+(?:above|over|greater than|at least|min(?:imum)?\s*)?\s*(\d+(?:\.\d+)?)", normalized)
    if bandwidth_match:
        values["min_bandwidth_mbps"] = float(bandwidth_match.group(1))

    cpu_match = re.search(r"cpu\s+(?:below|under|less than|less|up to|max\s*of)?\s*(\d+(?:\.\d+)?)", normalized)
    if cpu_match:
        values["max_cpu_percent"] = float(cpu_match.group(1))

    memory_match = re.search(r"memory\s+(?:below|under|less than|less|up to|max\s*of)?\s*(\d+(?:\.\d+)?)", normalized)
    if memory_match:
        values["max_memory_percent"] = float(memory_match.group(1))

    if "reliability" in normalized:
        values["priority"] = "reliability"
    elif "latency" in normalized:
        values["priority"] = "latency"
    elif "scalability" in normalized:
        values["priority"] = "scalability"

    if "reliability" in normalized and "scalability" in normalized:
        raise ValueError("Conflicting priorities requested")

    if "latency" in normalized and "scalability" in normalized:
        raise ValueError("Conflicting priorities requested")

    if "latency" in normalized and "reliability" in normalized:
        raise ValueError("Conflicting priorities requested")

    if not re.search(r"\d", normalized) and not any(keyword in normalized for keyword in ("prioritize", "priority", "profile", "service")):
        raise ValueError("At least one numeric requirement is required")

    if "below -" in normalized or "under -" in normalized or "less than -" in normalized:
        raise ValueError("Negative numeric values are not allowed")

    if re.search(r"cpu\s+(?:below|under|less than|less|up to|max\s*of)\s+([a-zA-Z]+)", normalized):
        raise ValueError("CPU target must be numeric")

    return ServiceIntent.model_validate(values)
