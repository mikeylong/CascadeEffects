from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def inbox_config_path(inbox_root: Path = ROOT_DIR) -> Path:
    return inbox_root / "config" / "inbox.toml"


def load_inbox_config(inbox_root: Path = ROOT_DIR) -> dict[str, Any]:
    path = inbox_config_path(inbox_root)
    if not path.exists():
        raise SystemExit(f"Missing Inbox config: {path}")
    with path.open("rb") as handle:
        loaded = tomllib.load(handle)
    if not isinstance(loaded, dict):
        raise SystemExit(f"Invalid Inbox config: {path}")
    return loaded


def resolve_production_tools_root(inbox_root: Path = ROOT_DIR) -> Path:
    config = load_inbox_config(inbox_root)
    raw = str(config.get("production_tools_root") or config.get("agents_root", "")).strip()
    if not raw:
        raise SystemExit(f"{inbox_config_path(inbox_root)} is missing `production_tools_root`.")
    tools_root = Path(raw).expanduser().resolve()
    if not tools_root.exists():
        raise SystemExit(f"Configured production_tools_root does not exist: {tools_root}")
    return tools_root


def resolve_agents_root(inbox_root: Path = ROOT_DIR) -> Path:
    return resolve_production_tools_root(inbox_root)


def ensure_agents_on_path(inbox_root: Path = ROOT_DIR) -> Path:
    agents_root = resolve_production_tools_root(inbox_root)
    rendered = str(agents_root)
    if rendered not in sys.path:
        sys.path.insert(0, rendered)
    return agents_root


AGENTS_ROOT = ensure_agents_on_path()


from orchestration.domain import (  # noqa: E402
    build_scene_lookup,
    derive_episode_state,
    derive_packaging_lane_status,
    derive_scene_lane_status,
    motion_items,
    packaging_items,
    scene_items,
    utc_now_iso,
)
from orchestration.io import (  # noqa: E402
    Context,
    build_context as _build_context,
    list_episode_manifests,
    load_episode_manifest,
    materialize_episode_manifest,
    path_exists,
    write_episode_manifest,
    write_state_file,
)
from orchestration.motion import derive_motion_lane_status, promote_motion_proof  # noqa: E402
from orchestration.stills import (  # noqa: E402
    promote_packaging_still,
    promote_scene_still,
    resolve_packaging_item,
    resolve_scene_item,
)


def build_agents_context(agents_root: Path | None = None) -> Context:
    root = Path(agents_root).expanduser().resolve() if agents_root else AGENTS_ROOT
    return _build_context(root=root)


build_context = build_agents_context


__all__ = [
    "AGENTS_ROOT",
    "Context",
    "build_agents_context",
    "build_context",
    "build_scene_lookup",
    "derive_episode_state",
    "derive_motion_lane_status",
    "derive_packaging_lane_status",
    "derive_scene_lane_status",
    "ensure_agents_on_path",
    "inbox_config_path",
    "list_episode_manifests",
    "load_episode_manifest",
    "load_inbox_config",
    "materialize_episode_manifest",
    "motion_items",
    "packaging_items",
    "path_exists",
    "promote_motion_proof",
    "promote_packaging_still",
    "promote_scene_still",
    "resolve_agents_root",
    "resolve_production_tools_root",
    "resolve_packaging_item",
    "resolve_scene_item",
    "scene_items",
    "utc_now_iso",
    "write_episode_manifest",
    "write_state_file",
]
