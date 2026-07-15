from pathlib import Path

import yaml


def test_profiles_are_loadable():
    base = Path(__file__).resolve().parents[1] / ".." / "profiles"
    for path in base.glob("*.yaml"):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        assert data["service_type"]
        assert data["defaults"]
