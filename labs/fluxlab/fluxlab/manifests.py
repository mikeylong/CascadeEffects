from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json, write_json

ALLOWED_SCENE_IDS = {
    "challenger_a",
    "challenger_b",
    "therac25_a",
    "therac25_b",
    "boeing737max_a",
    "boeing737max_b",
}
STAGES = {"lookdev", "refine"}
STAGE_DEFAULTS = {
    "lookdev": {"width": 864, "height": 1536, "batch_size": 4},
    "refine": {"width": 1024, "height": 1792, "batch_size": 1},
}


def _require_keys(payload: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def load_prompt_canon(path: Path) -> dict[str, Any]:
    canon = read_json(path)
    _require_keys(canon, ["shared_positive_style_prompt", "shared_negative_prompt", "subjects"], "prompt canon")
    return canon


def validate_scene(scene: dict[str, Any], *, path: Path | None = None) -> None:
    label = f"scene `{path.name}`" if path else "scene"
    _require_keys(
        scene,
        [
            "id",
            "incident",
            "variant",
            "stage_defaults",
            "positive_style_prompt",
            "subject_prompt",
            "negative_prompt",
            "selected_seed",
            "outputs",
        ],
        label,
    )
    if scene["id"] not in ALLOWED_SCENE_IDS:
        raise ValueError(f"{label} has unsupported id `{scene['id']}`.")
    if scene["variant"] not in {"a", "b"}:
        raise ValueError(f"{label} variant must be `a` or `b`.")
    if not isinstance(scene["outputs"], dict):
        raise ValueError(f"{label} outputs must be an object.")
    seed = scene["selected_seed"]
    if seed is not None and not isinstance(seed, int):
        raise ValueError(f"{label} selected_seed must be an integer or null.")
    stage_defaults = scene["stage_defaults"]
    if not isinstance(stage_defaults, dict):
        raise ValueError(f"{label} stage_defaults must be an object.")
    for stage, expected in STAGE_DEFAULTS.items():
        if stage_defaults.get(stage) != expected:
            raise ValueError(f"{label} stage_defaults.{stage} must equal {expected}.")


def load_scene(path: Path) -> dict[str, Any]:
    scene = read_json(path)
    validate_scene(scene, path=path)
    return scene


def save_scene(path: Path, scene: dict[str, Any]) -> None:
    validate_scene(scene, path=path)
    write_json(path, scene)


def scene_path(root: Path, scene_id: str) -> Path:
    if scene_id not in ALLOWED_SCENE_IDS:
        raise ValueError(f"Unsupported scene id `{scene_id}`.")
    return root / f"{scene_id}.json"
