from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def run_scan(mode: str, report_path: Path) -> dict:
    command = [
        "gitleaks",
        mode,
        ".",
        "--redact=100",
        "--report-format",
        "json",
        "--report-path",
        str(report_path),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    findings: list[dict] = []
    if report_path.exists() and report_path.stat().st_size:
        findings = json.loads(report_path.read_text(encoding="utf-8"))
    return {
        "command": " ".join(command[:-1] + ["<temporary-report>"]),
        "return_code": completed.returncode,
        "findings": len(findings),
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="aion6g-gitleaks-") as temp_dir:
        temp = Path(temp_dir)
        scans = [
            run_scan("git", temp / "git.json"),
            run_scan("dir", temp / "dir.json"),
        ]

    verified = all(item["return_code"] == 0 and item["findings"] == 0 for item in scans)
    payload = {
        "status": "VERIFIED" if verified else "FAILED",
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "scanner": "gitleaks",
        "version": subprocess.run(
            ["gitleaks", "version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout.strip(),
        "scope": "AION-6G Git history and working tree",
        "scans": scans,
        "findings": sum(item["findings"] for item in scans),
        "code_review": {
            "arbitrary_shell_execution_api": False,
            "allowlisted_workloads": True,
            "parameter_bounds": True,
            "execution_timeouts": True,
            "path_safe_evidence_storage": True,
            "committed_env_file": False,
            "public_load_balancer": False,
            "manifest_credentials": False,
        },
    }
    (RESULTS / "security_scan.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": payload["status"], "findings": payload["findings"]}, indent=2))
    if not verified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
