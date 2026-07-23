from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


def build_experiment_summary(rows: list[dict[str, Any]], output_dir: Path | str | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir or Path(__file__).resolve().parent.parent.parent / "results")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "experiment_summary.csv"
    json_path = output_dir / "experiment_summary.json"
    stats_path = output_dir / "experiment_statistics.json"

    fieldnames = [
        "run_id",
        "timestamp",
        "policy",
        "service_profile",
        "scenario",
        "selected_target",
        "execution_mode",
        "execution_success",
        "sla_status",
        "fallback_used",
        "orchestration_time_ms",
        "local_http_latency_ms",
        "kubernetes_http_latency_ms",
        "local_cpu_percent",
        "kubernetes_cpu_percent",
        "local_memory_percent",
        "kubernetes_memory_percent",
        "jitter_ms",
        "packet_loss_percent",
        "bandwidth_mbps",
        "network_data_type",
        "rejection_reasons",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            row = dict(row)
            row.setdefault("run_id", f"run-{index:03d}")
            row.setdefault("timestamp", "")
            row.setdefault("execution_mode", "")
            row.setdefault("network_data_type", "EMULATED")
            row.setdefault("rejection_reasons", [])
            row["rejection_reasons"] = "|".join(row.get("rejection_reasons") or [])
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    json_payload = {"rows": len(rows), "results": rows}
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    stats_payload = {
        "rows": len(rows),
        "policies": sorted({row.get("policy", "") for row in rows}),
        "profiles": sorted({row.get("service_profile", "") for row in rows}),
        "scenarios": sorted({row.get("scenario", "") for row in rows}),
        "success_count": sum(1 for row in rows if row.get("execution_success") is True),
        "total": len(rows),
    }
    stats_path.write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")

    def _chart(values: list[tuple[str, int]], name: str) -> None:
        labels = [label for label, _ in values]
        heights = [count for _, count in values]
        fig, ax = plt.subplots()
        ax.bar(labels, heights)
        ax.set_title(name)
        fig.tight_layout()
        fig.savefig(output_dir / f"{name.lower().replace(' ', '_')}.png")
        plt.close(fig)

    policy_counts: dict[str, int] = {}
    for row in rows:
        policy_counts[row.get("policy", "unknown")] = policy_counts.get(row.get("policy", "unknown"), 0) + 1
    _chart(list(policy_counts.items()), "Runs by policy")
    target_counts: dict[str, int] = {}
    for row in rows:
        target = row.get("selected_target") or "none"
        target_counts[target] = target_counts.get(target, 0) + 1
    _chart(list(target_counts.items()), "Selected targets")
    return stats_payload
