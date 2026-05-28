from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json

ALLOWED_MODES = {"sketch", "final", "lock"}
ALLOWED_PRESETS = {"stillness_breathe", "vertical_glide"}
ALLOWED_SHORT_RENDER_AS = {"still", "motion"}
EXPECTED_ASPECT_MODE = "vertical_9x16"
EXPECTED_FINAL_SIZE = {"width": 1080, "height": 1920}
EXPECTED_CAPTION_SAFE_KEYS = ("top_ui", "subtitles")


def _require_keys(payload: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def _require_box(box: Any, label: str) -> None:
    if not isinstance(box, list) or len(box) != 4:
        raise ValueError(f"{label} must be a list of four normalized values.")
    floats = [float(value) for value in box]
    if any(value < 0.0 or value > 1.0 for value in floats):
        raise ValueError(f"{label} values must be between 0.0 and 1.0.")
    if floats[0] >= floats[2] or floats[1] >= floats[3]:
        raise ValueError(f"{label} must use increasing x/y coordinates.")


def _require_positive_number(value: Any, label: str) -> None:
    if float(value) <= 0.0:
        raise ValueError(f"{label} must be greater than zero.")


def _validate_caption_safe_zone(payload: dict[str, Any], label: str) -> None:
    _require_keys(payload, list(EXPECTED_CAPTION_SAFE_KEYS), label)
    for key in EXPECTED_CAPTION_SAFE_KEYS:
        _require_box(payload[key], f"{label}.{key}")


def _validate_contract_metrics(payload: dict[str, Any], label: str) -> None:
    _require_keys(
        payload,
        [
            "negative_space_ratio",
            "max_palette_count",
            "max_accent_colors",
            "surreal_breach_count",
            "lighting_style",
            "forbidden_elements",
            "evaluator_thresholds",
        ],
        label,
    )
    _require_keys(payload["negative_space_ratio"], ["min", "preferred"], f"{label}.negative_space_ratio")
    if float(payload["negative_space_ratio"]["min"]) < 0.6:
        raise ValueError(f"{label}.negative_space_ratio.min must be at least 0.6.")
    if int(payload["max_palette_count"]) > 4:
        raise ValueError(f"{label}.max_palette_count must not exceed 4.")
    if int(payload["max_accent_colors"]) != 1:
        raise ValueError(f"{label}.max_accent_colors must equal 1.")
    if int(payload["surreal_breach_count"]) != 1:
        raise ValueError(f"{label}.surreal_breach_count must equal 1.")
    if not isinstance(payload["forbidden_elements"], list) or not payload["forbidden_elements"]:
        raise ValueError(f"{label}.forbidden_elements must be a non-empty list.")
    _require_keys(
        payload["evaluator_thresholds"],
        ["asymmetry_ratio", "palette_discipline", "focal_clarity", "visual_noise", "overall_pass_threshold"],
        f"{label}.evaluator_thresholds",
    )


def _validate_historical_anchor(payload: dict[str, Any], label: str) -> None:
    _require_keys(payload, ["episode", "topic", "description"], label)


def _validate_surreal_breach(payload: dict[str, Any], label: str) -> None:
    _require_keys(payload, ["kind", "description"], label)


def scene_path_for_id(root: Path, scene_id: str) -> Path:
    return root / f"{scene_id}.json"


def load_profile(path: Path) -> dict[str, Any]:
    profile = read_json(path)
    _require_keys(
        profile,
        ["id", "palette", "prompts", "rules", "motion_presets", "negative_prompt_defaults", "contract_metrics", "caption_safe_defaults"],
        f"profile `{path.name}`",
    )
    _require_keys(profile["prompts"], ["global_base", "mode_overrides"], f"profile `{path.name}` prompts")
    for mode in ALLOWED_MODES:
        if mode not in profile["prompts"]["mode_overrides"]:
            raise ValueError(f"profile `{path.name}` prompts.mode_overrides must declare `{mode}`.")
    _require_keys(
        profile["rules"],
        ["subject_anchor", "reduction", "color_fields", "asymmetry", "selective_saturation", "textural_restraint", "implied_story"],
        f"profile `{path.name}` rules",
    )
    for preset in ALLOWED_PRESETS:
        if preset not in profile["motion_presets"]:
            raise ValueError(f"profile `{path.name}` motion_presets must declare `{preset}`.")
    if not isinstance(profile["negative_prompt_defaults"], list) or not profile["negative_prompt_defaults"]:
        raise ValueError(f"profile `{path.name}` negative_prompt_defaults must be a non-empty list.")
    _validate_contract_metrics(profile["contract_metrics"], f"profile `{path.name}` contract_metrics")
    _validate_caption_safe_zone(profile["caption_safe_defaults"], f"profile `{path.name}` caption_safe_defaults")
    return profile


def load_scene(path: Path) -> dict[str, Any]:
    scene = read_json(path)
    validate_scene_manifest(scene, path=path)
    return scene


def validate_scene_manifest(scene: dict[str, Any], *, path: Path | None = None) -> None:
    label = f"scene `{path.name}`" if path else "scene"
    _require_keys(
        scene,
        [
            "id",
            "aspect_mode",
            "final_size",
            "style_profile",
            "source_refs",
            "subject_anchor",
            "dominant_mass_strategy",
            "accent_strategy",
            "reflection_strategy",
            "prompt_overrides",
            "selected_seed",
            "motion_preset",
            "outputs",
            "beat_id",
            "historical_anchor",
            "surreal_breach",
            "caption_safe_zone",
            "target_duration_seconds",
        ],
        label,
    )
    if scene["aspect_mode"] != EXPECTED_ASPECT_MODE:
        raise ValueError(f"{label} must use aspect_mode `{EXPECTED_ASPECT_MODE}`.")
    if scene["final_size"] != EXPECTED_FINAL_SIZE:
        raise ValueError(f"{label} must use final_size `{EXPECTED_FINAL_SIZE}`.")
    if not isinstance(scene["source_refs"], list):
        raise ValueError(f"{label} source_refs must be a list.")
    for source_ref in scene["source_refs"]:
        _require_keys(source_ref, ["path", "role", "label"], f"{label} source_ref")
        source_path = Path(str(source_ref["path"])).expanduser()
        if not source_path.exists():
            raise ValueError(f"{label} source_ref path does not exist: {source_path}")
    _require_keys(scene["subject_anchor"], ["description", "placement", "scale", "archetype"], f"{label} subject_anchor")
    _require_keys(scene["dominant_mass_strategy"], ["description", "width_ratio"], f"{label} dominant_mass_strategy")
    _require_keys(scene["accent_strategy"], ["description", "placement", "size"], f"{label} accent_strategy")
    _require_keys(scene["reflection_strategy"], ["description", "literal_water", "horizon_y"], f"{label} reflection_strategy")
    if not isinstance(scene["prompt_overrides"], dict):
        raise ValueError(f"{label} prompt_overrides must be an object.")
    if "negative_prompt" in scene["prompt_overrides"]:
        raise ValueError(f"{label} cannot declare a negative_prompt override in this lab.")
    if not isinstance(scene["outputs"], dict):
        raise ValueError(f"{label} outputs must be an object.")
    if scene["motion_preset"] not in ALLOWED_PRESETS:
        raise ValueError(f"{label} has unsupported motion_preset `{scene['motion_preset']}`.")
    if not isinstance(scene["selected_seed"], int):
        raise ValueError(f"{label} selected_seed must be an integer.")
    if not str(scene["beat_id"]).strip():
        raise ValueError(f"{label} beat_id must be non-empty.")
    _validate_historical_anchor(scene["historical_anchor"], f"{label} historical_anchor")
    _validate_surreal_breach(scene["surreal_breach"], f"{label} surreal_breach")
    _validate_caption_safe_zone(scene["caption_safe_zone"], f"{label} caption_safe_zone")
    _require_positive_number(scene["target_duration_seconds"], f"{label} target_duration_seconds")


def load_short(path: Path, *, scenes_root: Path | None = None) -> dict[str, Any]:
    short_manifest = read_json(path)
    validate_short_manifest(short_manifest, path=path, scenes_root=scenes_root)
    return short_manifest


def validate_short_manifest(short_manifest: dict[str, Any], *, path: Path | None = None, scenes_root: Path | None = None) -> None:
    label = f"short `{path.name}`" if path else "short"
    _require_keys(short_manifest, ["id", "title", "audio_path", "transcript_path", "packaging_frame_id", "beats"], label)
    audio_path = Path(str(short_manifest["audio_path"])).expanduser()
    transcript_path = Path(str(short_manifest["transcript_path"])).expanduser()
    if not audio_path.exists():
        raise ValueError(f"{label} audio_path does not exist: {audio_path}")
    if not transcript_path.exists():
        raise ValueError(f"{label} transcript_path does not exist: {transcript_path}")
    if not isinstance(short_manifest["beats"], list) or not short_manifest["beats"]:
        raise ValueError(f"{label} beats must be a non-empty list.")
    prior_clip_end = -1.0
    seen_ids: set[str] = set()
    for index, beat in enumerate(short_manifest["beats"]):
        beat_label = f"{label} beat[{index}]"
        _require_keys(
            beat,
            [
                "id",
                "scene_id",
                "render_as",
                "clip_start_seconds",
                "clip_end_seconds",
                "cue_start_seconds",
                "cue_end_seconds",
                "narration_text",
            ],
            beat_label,
        )
        beat_id = str(beat["id"]).strip()
        if not beat_id:
            raise ValueError(f"{beat_label} id must be non-empty.")
        if beat_id in seen_ids:
            raise ValueError(f"{label} beat ids must be unique.")
        seen_ids.add(beat_id)
        if beat["render_as"] not in ALLOWED_SHORT_RENDER_AS:
            raise ValueError(f"{beat_label} render_as must be one of {sorted(ALLOWED_SHORT_RENDER_AS)}.")
        clip_start = float(beat["clip_start_seconds"])
        clip_end = float(beat["clip_end_seconds"])
        cue_start = float(beat["cue_start_seconds"])
        cue_end = float(beat["cue_end_seconds"])
        if clip_end <= clip_start:
            raise ValueError(f"{beat_label} clip_end_seconds must be greater than clip_start_seconds.")
        if cue_end <= cue_start:
            raise ValueError(f"{beat_label} cue_end_seconds must be greater than cue_start_seconds.")
        if clip_start < prior_clip_end:
            raise ValueError(f"{label} beats must be ordered by non-decreasing clip_start_seconds.")
        prior_clip_end = clip_end
        if not str(beat["narration_text"]).strip():
            raise ValueError(f"{beat_label} narration_text must be non-empty.")
        if scenes_root is not None:
            scene_path = scene_path_for_id(scenes_root, str(beat["scene_id"]))
            if not scene_path.exists():
                raise ValueError(f"{beat_label} scene_id does not exist: {scene_path}")
    if scenes_root is not None:
        packaging_scene_path = scene_path_for_id(scenes_root, str(short_manifest["packaging_frame_id"]))
        if not packaging_scene_path.exists():
            raise ValueError(f"{label} packaging_frame_id does not exist: {packaging_scene_path}")


def normalize_final_size(scene: dict[str, Any]) -> tuple[int, int]:
    final_size = scene.get("final_size") or {}
    return int(final_size.get("width", 1080)), int(final_size.get("height", 1920))
