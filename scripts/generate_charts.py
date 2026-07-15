from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent.parent / "results"
files = sorted(base.glob("*.json"))
if not files:
    raise SystemExit("No result files available")

records = [json.loads(path.read_text(encoding="utf-8")) for path in files]
fig, ax = plt.subplots()
ax.plot(range(len(records)), [item.get("orchestration_time_ms", 0) for item in records])
ax.set_xlabel("Result")
ax.set_ylabel("Orchestration time (ms)")
fig.tight_layout()
fig.savefig(base / "orchestration_times.png")
plt.close(fig)
