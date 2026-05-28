from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def list_scene_paths(root: Path) -> list[Path]:
    return sorted(root.glob("*.json"))


def list_short_paths(root: Path) -> list[Path]:
    return sorted(root.glob("*.json"))


def timestamp_slug() -> str:
    from datetime import datetime, timezone

    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
