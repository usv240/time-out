"""Seed deterministic vendor caches and synthetic encounter data."""

from __future__ import annotations

import json

from before.app.integrations import seed_all_caches
from before.app.service import BeforeService


def main() -> None:
    caches = seed_all_caches()
    encounters = BeforeService().seed()
    print(json.dumps({"cache_files": caches, "encounters": [row["id"] for row in encounters]}, indent=2))


if __name__ == "__main__":
    main()
