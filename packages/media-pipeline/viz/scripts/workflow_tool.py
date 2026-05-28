#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import difflib
import json
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from guardrail_policy import load_guardrail_policy, prompt_guardrails_for
from midjourney_package_tool import (
    MidjourneyPackageError,
    grid_runtime_filename,
    load_midjourney_package_adapter,
    load_midjourney_package_shot,
    normalize_negative_terms as normalize_midjourney_negative_terms,
)
from subject_reference_plate import build_status_for_output
from typography_contract import TypographyContractError, normalize_typography_intent


TOKEN_RE = re.compile(r"{{\s*([^{}]+?)\s*}}")
REQUIRED_SPEC_FIELDS = {
    "family",
    "preset",
    "base_fragment",
    "params",
    "nodes",
    "links",
    "output",
}
REQUIRED_OUTPUT_FIELDS = {"intent", "generated_filename", "sync_filename"}
LEGACY_REQUIRED_PARAM_FIELDS = {
    "positive_prompt",
    "negative_prompt",
    "width",
    "height",
    "batch_size",
    "seed",
    "selected_seed",
    "seed_mode",
    "variant_count",
    "steps",
    "guidance",
    "cfg",
    "sampler_name",
    "scheduler",
    "denoise",
    "refine_denoise",
    "upscale_factor",
    "filename_prefix",
    "note_text",
    "output_intent",
    "stage",
    "reference_board_dir",
    "safe_zone",
    "signal_anchor",
    "source_image",
    "full_unet_name",
    "full_vae_name",
    "full_text_encoder_primary",
    "full_text_encoder_secondary",
    "full_weight_dtype",
    "upscale_model_name",
    "upscale_method",
}
ACTIVE_STYLE_PARAM_FIELDS = {
    "style_profile",
    "temperature",
    "palette_policy",
    "accent_palette",
    "human_presence",
    "safe_zone_intent",
    "post_work",
}
ACTIVE_REQUIRED_PARAM_FIELDS = LEGACY_REQUIRED_PARAM_FIELDS | ACTIVE_STYLE_PARAM_FIELDS
FAMILY_REQUIRED_PARAM_FIELDS = {
    "shorts_scene_plate": {"beat_id", "historical_anchor", "surreal_breach", "caption_safe_zone"},
}
ACTIVE_FAMILY_RULES = {
    "shorts_scene_plate": {"kind": "exact", "ratio": 9 / 16},
    "thumbnail_plate": {"kind": "exact", "ratio": 16 / 9},
    "shorts_cover_plate": {"kind": "exact", "ratio": 9 / 16},
    "evidence_card_plate": {"kind": "exact", "ratio": 1080 / 1350},
}
RETIRED_FAMILIES: set[str] = {"scene_still"}
STYLE_PROFILE_REQUIRED_FIELDS = {"name", "defaults", "prompts"}
STYLE_PROFILE_OPTIONAL_LIST_FIELDS = {"negative_prompt_defaults"}
STYLE_PROFILE_OPTIONAL_OBJECT_FIELDS = {
    "contract_metrics",
    "caption_safe_defaults",
    "subject_reference_defaults",
    "plate_seed_defaults",
    "source_package",
}
MIDJOURNEY_PACKAGE_GRID_REFERENCE_MODE = "midjourney_package_grid"
MIDJOURNEY_STEER_TARGET_PROMPT_MAP = {
    "single_severe_warning_object": "one off-center severe institutional warning object, compressed into a monolithic signal with only faint shuttle-stack cues",
    "cold_pipe_winter_signal": "one cold-risk infrastructure signal dominated by icicle-heavy pipe detail and winter haze, with tower structure reduced to incidental background support",
    "accurate_shuttle_documentary": "faithful NASA Space Shuttle documentary rendering with accurate orbiter, external tank, twin solid rocket boosters, and exhaust behavior tied to the aft propulsion geometry",
}
ACTIVE_PROMPT_BANLIST = {
    "readable text": "readable-text dependence",
    "readable memo": "memo-centric clue",
    "readable label": "label-led clue",
    "readable labels": "label-led clue",
    "readable paperwork": "paperwork-led clue",
    "documentary realism": "documentary-realism dependency",
    "archival realism": "documentary-realism dependency",
    "documentary framing": "documentary-realism dependency",
    "archival proof": "faux-archival-proof cue",
    "photographic realism": "believable-realism dependency",
    "photojournalism": "documentary-photo cue",
    "hero astronaut": "astronaut-hero framing",
    "heroic astronaut": "astronaut-hero framing",
    "courtroom hearing": "courtroom shorthand",
    "courtroom drama": "courtroom shorthand",
    "fireball spectacle": "explosion-spectacle cue",
    "explosion poster": "explosion-poster cue",
    "one dominant clue": "legacy single-clue framing",
    "single dominant": "legacy single-clue framing",
    "single emblematic": "legacy single-clue framing",
    "at most two supporting elements": "legacy support-cap framing",
    "blank display glass": "legacy realism-adjacent cue",
    "institutional materials": "legacy realism-adjacent cue",
    "raw hardware only": "legacy raw-hardware framing",
    "unmarked surfaces": "legacy blank-surface framing",
}
PACKAGING_FAMILIES = {"thumbnail_plate", "shorts_cover_plate"}
ACTIVE_TEXT_SIGNAGE_BANLIST = {
    "readable text": "text-bearing active-image cue",
    "printed text": "text-bearing active-image cue",
    "words": "text-bearing active-image cue",
    "letters": "text-bearing active-image cue",
    "numbers": "text-bearing active-image cue",
    "digits": "text-bearing active-image cue",
    "label": "label-led active-image cue",
    "labels": "label-led active-image cue",
    "warning label": "label-led active-image cue",
    "warning labels": "label-led active-image cue",
    "serial plate": "plate-led active-image cue",
    "serial plates": "plate-led active-image cue",
    "serial tag": "tag-led active-image cue",
    "serial tags": "tag-led active-image cue",
    "placard": "placard-led active-image cue",
    "placards": "placard-led active-image cue",
    "sticker": "sticker-led active-image cue",
    "stickers": "sticker-led active-image cue",
    "decal": "decal-led active-image cue",
    "decals": "decal-led active-image cue",
    "engraved plate": "engraved-plate active-image cue",
    "engraved plates": "engraved-plate active-image cue",
    "warning plate": "warning-plate active-image cue",
    "warning plates": "warning-plate active-image cue",
    "warning sign": "warning-sign active-image cue",
    "warning signs": "warning-sign active-image cue",
    "icon plate": "icon-plate active-image cue",
    "icon plates": "icon-plate active-image cue",
    "symbol plate": "symbol-plate active-image cue",
    "symbol plates": "symbol-plate active-image cue",
    "readable ui": "ui-led active-image cue",
    "ui readout": "ui-led active-image cue",
    "ui readouts": "ui-led active-image cue",
    "readable display": "display-led active-image cue",
    "display readout": "display-led active-image cue",
    "display readouts": "display-led active-image cue",
}
SCENE_STILL_STRIPE_BANLIST = {
    "schematic overlay": "line-amplification cue",
    "circuit traces": "line-amplification cue",
    "halftone": "line-amplification cue",
    "photocopy grain": "line-amplification cue",
    "scan line": "scan-line cue",
    "scan lines": "scan-line cue",
    "scan-line": "scan-line cue",
    "scan-lines": "scan-line cue",
    "scanline": "scan-line cue",
    "scanlines": "scan-line cue",
    "horizontal banding": "banding cue",
}
ACTIVE_REQUIRED_NEGATIVE_PHRASES = (
    "no text",
    "no words",
    "no letters",
    "no numbers",
    "no digits",
    "no stickers",
    "no decals",
    "no placards",
    "no serial tags",
    "no serial plates",
    "no engraved plates",
    "no warning signs",
    "no warning plates",
    "no stamped markings",
    "no screen digits",
    "no icon plates",
    "no symbol plates",
    "no interface readouts",
    "no readable ui",
)
COLLAGE_REQUIRED_MARKERS = (
    "editorial collage",
    "torn paper",
    "ripped seam",
    "soft collage seam",
    "paper fiber",
    "abstract wiring silhouette",
    "soft tonal breakup",
    "poster montage",
    "fragmented historical imagery",
)
SCENE_STILL_REQUIRED_FINAL_FRAGMENT = "image_resize_base"
ACTIVE_FAMILY_PROMPT_REQUIREMENTS = {
    "shorts_scene_plate": ("anchor fragment", "layered support fragments", "historical anchor", "surreal breach"),
    "thumbnail_plate": ("anchor fragment", "layered support fragments", "poster montage"),
    "shorts_cover_plate": ("anchor fragment", "layered support fragments", "poster montage"),
    "evidence_card_plate": ("anchor fragment", "layered support fragments"),
}
MINIMAL_SURREAL_REQUIRED_PROMPT_PHRASES = (
    "negative space occupies at least 60% of the frame",
    "off-center focal mass",
    "one dominant field color",
    "one saturated accent element",
    "exactly one surreal breach",
    "soft diffuse lighting",
    "no text, logo, or ui artifacts",
)
MINIMAL_SURREAL_REFERENCE_PLATE_PROMPT_PHRASE = (
    "preserve the reference plate's dominant subject count, silhouette, and placement bias"
)
MINIMAL_SURREAL_ALLOWED_TEMPERATURES = {"restrained", "tense", "bold"}
SUBJECT_REFERENCE_REQUIRED_STAGES = {"draft_txt2img", "refine_img2img"}
SUBJECT_REFERENCE_ALLOWED_CROPS = {"none", "center"}
MINIMAL_SURREAL_PORTRAIT_FAMILIES = {"shorts_scene_plate", "shorts_cover_plate"}
PLATE_SEED_REQUIRED_STAGES = {"draft_txt2img"}
PIPELINE_STRATEGY_REQUIRED_FIELDS = {
    "seed_policy",
    "draft_candidate_count",
    "hero_model",
    "hero_refine_denoise",
    "semantic_qc_profile",
}
PIPELINE_STRATEGY_ALLOWED_SEED_POLICIES = {"fixed", "search"}
PROMPT_FRAGMENT_REQUIRED_FIELDS = {"anchor_fragment", "support_fragments"}
PROMPT_FRAGMENT_OPTIONAL_FIELDS = {
    "directives",
    "draft_directives",
    "refine_directives",
    "final_directives",
}
PROMPT_SUPPORT_LIMITS = {
    "shorts_scene_plate": 2,
    "thumbnail_plate": 3,
    "shorts_cover_plate": 3,
}
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".tif", ".tiff", ".bmp"}
STAGE_ORDER = {
    "draft_txt2img": 0,
    "refine_img2img": 1,
    "repair_source_text": 2,
    "final_upscale": 3,
}
UPSTREAM_STAGE = {
    "draft_txt2img": None,
    "refine_img2img": "draft_txt2img",
    "repair_source_text": "refine_img2img",
    "final_upscale": "refine_img2img",
}
NON_API_NODE_TYPES = {"Note"}
REPAIR_POLICY_REQUIRED_FIELDS = {
    "enabled",
    "application_stage",
    "surface_scope",
    "llm_backend",
    "llm_model",
    "allow_repaired_text_outside_typography_zones",
    "ambiguous_environmental_fallback_action",
    "max_regions",
    "ocr_confidence_floor",
    "rewrite_confidence_floor",
    "erase_confidence_floor",
    "context_terms",
    "forbidden_surface_types",
}
REPAIR_POST_FINAL_CLEANUP_DEFAULTS = {
    "enabled": False,
    "mode": "erase_only",
    "max_regions": 8,
}
REPAIR_ALLOWED_APPLICATION_STAGES = {"post_refine"}
REPAIR_ALLOWED_SURFACE_SCOPES = {"environmental_only"}
REPAIR_ALLOWED_BACKENDS = {"ollama"}
FINAL_UPSCALE_REQUIRED_BASE_FRAGMENTS = {
    "shorts_scene_plate": SCENE_STILL_REQUIRED_FINAL_FRAGMENT,
}
FULL_FLUX_DRAFT_FRAGMENTS = {
    "flux_full_txt2img_base",
    "minimal_surreal_flux_reference_txt2img_base",
    "minimal_surreal_flux_reference_seeded_draft_base",
    "minimal_surreal_flux_reference_fullframe_draft_base",
    "minimal_surreal_flux_midjourney_grid_draft_base",
}
PLATE_SEEDED_DRAFT_FRAGMENTS = {"minimal_surreal_flux_reference_seeded_draft_base"}
FULL_FRAME_COMPOSITION_FRAGMENTS = {
    "minimal_surreal_flux_reference_fullframe_draft_base",
    "minimal_surreal_flux_reference_fullframe_refine_base",
}
MIDJOURNEY_PACKAGE_GRID_FRAGMENTS = {
    "minimal_surreal_flux_midjourney_grid_draft_base",
    "minimal_surreal_flux_midjourney_grid_refine_base",
}
MAX_SPATIAL_EXCLUSION_BOXES = 4
CHECKPOINT_LOADER_TYPES = {"CheckpointLoaderSimple"}


class WorkflowError(Exception):
    pass


def phrase_matches_text(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase.lower())}(?![a-z0-9])", text.lower()) is not None


@dataclass
class BuildResult:
    spec_path: Path
    family: str
    preset: str
    base_preset: str
    stage: str
    generated_workflow_path: Path
    generated_prompt_path: Path
    generated_manifest_path: Path
    sync_target_path: Path
    workflow: dict[str, Any]
    prompt: dict[str, Any]
    manifest: dict[str, Any]
    warnings: list[str]
    params: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bin/ce workflow")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--models-root", required=True)
    parser.add_argument("--comfy-workflows-dir", required=True)
    parser.add_argument("--comfy-output-dir", required=True)
    parser.add_argument("--references-root", required=True)
    parser.add_argument("--comfy-clip-vision-model", default="")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("family", nargs="?", default="all")
    validate_parser.add_argument("preset", nargs="?")

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("family")
    build_parser.add_argument("preset", nargs="?")
    build_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for a build target.",
    )

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("family")
    sync_parser.add_argument("preset", nargs="?")
    sync_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for a build target before syncing.",
    )

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("family")
    diff_parser.add_argument("preset", nargs="?")
    diff_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for a build target before diffing.",
    )

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("family")
    compare_parser.add_argument("preset", nargs="?")
    compare_parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override allowed params for a compare target.",
    )

    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def parse_override_values(raw_items: list[str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for raw in raw_items:
        if "=" not in raw:
            raise WorkflowError(f"Invalid override {raw!r}; expected KEY=VALUE.")
        key, raw_value = raw.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise WorkflowError(f"Invalid override {raw!r}; missing key.")
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        overrides[key] = value
    return overrides


def deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = copy.deepcopy(base)
        for key, value in override.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged
    return copy.deepcopy(override)


def unique_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    items: list[str] = []
    for raw in value:
        text = str(raw).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        items.append(text)
    return items


def unique_phrase_list(*values: Any) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        raw_items: list[str]
        if isinstance(value, str):
            raw_items = [item.strip() for item in value.split(",")]
        else:
            raw_items = unique_string_list(value)
        for raw in raw_items:
            text = str(raw).strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            items.append(text)
    return items


def merge_prompt_phrases(*values: Any) -> str:
    return ", ".join(unique_phrase_list(*values))


def path_text_for_manifest(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve())).replace(os.sep, "/")
    except ValueError:
        return str(path.resolve())


def style_uses_minimal_surreal_contract(style: dict[str, Any]) -> bool:
    contract_metrics = style.get("contract_metrics")
    caption_safe_defaults = style.get("caption_safe_defaults")
    return isinstance(contract_metrics, dict) and bool(contract_metrics) and isinstance(
        caption_safe_defaults, dict
    )


def style_uses_subject_reference_conditioning(style: dict[str, Any]) -> bool:
    subject_reference_defaults = style.get("subject_reference_defaults")
    return (
        style_uses_minimal_surreal_contract(style)
        and isinstance(subject_reference_defaults, dict)
        and bool(subject_reference_defaults.get("enabled"))
    )


def style_uses_plate_seed_defaults(style: dict[str, Any]) -> bool:
    plate_seed_defaults = style.get("plate_seed_defaults")
    return (
        style_uses_subject_reference_conditioning(style)
        and isinstance(plate_seed_defaults, dict)
        and bool(plate_seed_defaults.get("enabled"))
    )


def minimal_surreal_plate_seed_active(
    *,
    spec: dict[str, Any],
    style: dict[str, Any],
    params: dict[str, Any],
) -> bool:
    return (
        style_uses_plate_seed_defaults(style)
        and str(spec.get("family", "")).strip() in MINIMAL_SURREAL_PORTRAIT_FAMILIES
        and str(params.get("stage", "")).strip() in PLATE_SEED_REQUIRED_STAGES
        and str(spec.get("base_fragment", "")).strip() in PLATE_SEEDED_DRAFT_FRAGMENTS
    )


def minimal_surreal_full_frame_composition_active(
    *,
    spec: dict[str, Any],
    style: dict[str, Any],
    params: dict[str, Any],
) -> bool:
    return (
        style_uses_subject_reference_conditioning(style)
        and str(spec.get("family", "")).strip() in MINIMAL_SURREAL_PORTRAIT_FAMILIES
        and str(params.get("stage", "")).strip() in SUBJECT_REFERENCE_REQUIRED_STAGES
        and str(spec.get("base_fragment", "")).strip() in FULL_FRAME_COMPOSITION_FRAGMENTS
    )


def midjourney_package_grid_reference_mode(params: dict[str, Any]) -> bool:
    return str(params.get("reference_mode", "")).strip() == MIDJOURNEY_PACKAGE_GRID_REFERENCE_MODE


def minimal_surreal_midjourney_package_grid_active(
    *,
    spec: dict[str, Any],
    style: dict[str, Any],
    params: dict[str, Any],
) -> bool:
    return (
        style_uses_subject_reference_conditioning(style)
        and str(spec.get("family", "")).strip() in MINIMAL_SURREAL_PORTRAIT_FAMILIES
        and str(params.get("stage", "")).strip() in SUBJECT_REFERENCE_REQUIRED_STAGES
        and midjourney_package_grid_reference_mode(params)
        and str(spec.get("base_fragment", "")).strip() in MIDJOURNEY_PACKAGE_GRID_FRAGMENTS
    )


def validate_normalized_box(path: Path, label: str, value: Any) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise WorkflowError(f"{path}: {label} must be a list of four normalized coordinates.")
    try:
        x1, y1, x2, y2 = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{path}: {label} must contain only numeric coordinates.") from exc
    coordinates = (x1, y1, x2, y2)
    if any(item < 0.0 or item > 1.0 for item in coordinates):
        raise WorkflowError(f"{path}: {label} coordinates must stay within 0.0-1.0.")
    if x2 <= x1 or y2 <= y1:
        raise WorkflowError(f"{path}: {label} must define a positive-area box.")
    return coordinates


def normalized_box_to_pixel_rect(
    box: list[float] | tuple[float, float, float, float],
    *,
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = [float(item) for item in box]
    left = max(0, min(width - 1, int(round(x1 * width))))
    top = max(0, min(height - 1, int(round(y1 * height))))
    right = max(left + 1, min(width, int(round(x2 * width))))
    bottom = max(top + 1, min(height, int(round(y2 * height))))
    return left, top, right - left, bottom - top


def validate_caption_safe_payload(path: Path, label: str, value: Any) -> dict[str, list[float]]:
    if not isinstance(value, dict):
        raise WorkflowError(f"{path}: {label} must be an object.")
    required = {"top_ui", "subtitles"}
    missing = required - set(value)
    if missing:
        raise WorkflowError(f"{path}: {label} missing fields: {', '.join(sorted(missing))}")
    normalized = {
        "top_ui": list(validate_normalized_box(path, f"{label}.top_ui", value["top_ui"])),
        "subtitles": list(validate_normalized_box(path, f"{label}.subtitles", value["subtitles"])),
    }
    return normalized


def validate_subject_reference_defaults(path: Path, label: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkflowError(f"{path}: {label} must be an object.")
    required = {
        "enabled",
        "clip_vision_model_env",
        "draft_strength",
        "refine_strength",
        "noise_augmentation",
        "crop",
    }
    missing = required - set(value)
    if missing:
        raise WorkflowError(f"{path}: {label} missing fields: {', '.join(sorted(missing))}")
    normalized = dict(value)
    normalized["enabled"] = bool(value["enabled"])
    env_name = str(value["clip_vision_model_env"]).strip()
    if not env_name:
        raise WorkflowError(f"{path}: {label}.clip_vision_model_env must be non-empty.")
    normalized["clip_vision_model_env"] = env_name
    for field in ("draft_strength", "refine_strength", "noise_augmentation"):
        try:
            normalized[field] = float(value[field])
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{path}: {label}.{field} must be numeric.") from exc
    if normalized["draft_strength"] <= 0.0:
        raise WorkflowError(f"{path}: {label}.draft_strength must be > 0.")
    if normalized["refine_strength"] <= 0.0:
        raise WorkflowError(f"{path}: {label}.refine_strength must be > 0.")
    if normalized["noise_augmentation"] < 0.0 or normalized["noise_augmentation"] > 1.0:
        raise WorkflowError(f"{path}: {label}.noise_augmentation must stay within 0.0-1.0.")
    crop = str(value["crop"]).strip().lower()
    if crop not in SUBJECT_REFERENCE_ALLOWED_CROPS:
        raise WorkflowError(
            f"{path}: {label}.crop must be one of {', '.join(sorted(SUBJECT_REFERENCE_ALLOWED_CROPS))}."
        )
    normalized["crop"] = crop
    return normalized


def validate_plate_seed_defaults(path: Path, label: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkflowError(f"{path}: {label} must be an object.")
    required = {"enabled", "draft_denoise"}
    missing = required - set(value)
    if missing:
        raise WorkflowError(f"{path}: {label} missing fields: {', '.join(sorted(missing))}")
    normalized = dict(value)
    normalized["enabled"] = bool(value["enabled"])
    try:
        normalized["draft_denoise"] = float(value["draft_denoise"])
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{path}: {label}.draft_denoise must be numeric.") from exc
    if normalized["draft_denoise"] <= 0.0 or normalized["draft_denoise"] > 1.0:
        raise WorkflowError(f"{path}: {label}.draft_denoise must stay within 0.0-1.0.")
    return normalized


def format_caption_safe_zone(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    parts: list[str] = []
    for key in ("top_ui", "subtitles"):
        raw_box = value.get(key)
        if not isinstance(raw_box, list) or len(raw_box) != 4:
            continue
        rounded = ", ".join(f"{float(item):.2f}" for item in raw_box)
        parts.append(f"{key}=[{rounded}]")
    return "; ".join(parts)


def resolve_context_path(context: dict[str, Any], expression: str) -> Any:
    current: Any = context
    for segment in expression.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise WorkflowError(f"Unknown template expression: {expression}")
        current = current[segment]
    return current


def render_template(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        matches = list(TOKEN_RE.finditer(value))
        if not matches:
            return value
        if len(matches) == 1 and matches[0].span() == (0, len(value)):
            return resolve_context_path(context, matches[0].group(1).strip())

        rendered = value
        for match in matches:
            replacement = resolve_context_path(context, match.group(1).strip())
            rendered = rendered.replace(match.group(0), str(replacement))
        return rendered
    if isinstance(value, list):
        return [render_template(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render_template(item, context) for key, item in value.items()}
    return value


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class WorkflowCompiler:
    def __init__(
        self,
        repo_root: Path,
        models_root: Path,
        comfy_workflows_dir: Path,
        comfy_output_dir: Path,
        references_root: Path,
        comfy_clip_vision_model: str = "",
    ) -> None:
        self.repo_root = repo_root
        self.models_root = models_root
        self.comfy_workflows_dir = comfy_workflows_dir
        self.comfy_output_dir = comfy_output_dir
        self.references_root = references_root
        self.comfy_clip_vision_model = str(comfy_clip_vision_model).strip()
        self.workflows_root = repo_root / "workflows"
        self.fragments_dir = self.workflows_root / "fragments"
        self.specs_dir = self.workflows_root / "specs"
        self.style_profiles_dir = self.workflows_root / "style_profiles"
        self.typography_dir = self.workflows_root / "typography"
        self.source_text_repair_dir = self.workflows_root / "source_text_repair"
        self.generated_dir = self.workflows_root / "generated"
        self.reports_dir = self.generated_dir / "reports"
        self._typography_cache: dict[tuple[str, str], tuple[Path, dict[str, Any]] | None] = {}
        self._repair_policy_cache: dict[tuple[str, str], tuple[Path, dict[str, Any]] | None] = {}

    @staticmethod
    def is_active_family(family: str) -> bool:
        return family in ACTIVE_FAMILY_RULES

    @staticmethod
    def is_retired_family(family: str) -> bool:
        return family in RETIRED_FAMILIES

    @staticmethod
    def nodes_require_checkpoint_loader(nodes: Any) -> bool:
        return any(isinstance(node, dict) and node.get("type") in CHECKPOINT_LOADER_TYPES for node in nodes)

    def all_spec_paths(self) -> list[Path]:
        return sorted(
            self.specs_dir.glob("*/*.json"),
            key=lambda path: (path.parent.name, STAGE_ORDER.get(path.stem.split("__")[-1], 999), path.stem),
        )

    def list_specs(self, active_only: bool = True) -> list[Path]:
        specs = self.all_spec_paths()
        if active_only:
            specs = [path for path in specs if self.is_active_family(path.parent.name)]
        return specs

    def load_spec(self, path: Path) -> dict[str, Any]:
        spec = read_json(path)
        self.validate_spec_shape(spec, path)
        return spec

    def validate_spec_shape(self, spec: dict[str, Any], path: Path) -> None:
        missing = REQUIRED_SPEC_FIELDS - set(spec)
        if missing:
            raise WorkflowError(f"{path}: missing top-level fields: {', '.join(sorted(missing))}")

        if not isinstance(spec["params"], dict):
            raise WorkflowError(f"{path}: params must be an object.")
        required_params = (
            ACTIVE_REQUIRED_PARAM_FIELDS
            if self.is_active_family(str(spec["family"]))
            else LEGACY_REQUIRED_PARAM_FIELDS
        )
        missing_params = required_params - set(spec["params"])
        if missing_params:
            raise WorkflowError(f"{path}: missing params: {', '.join(sorted(missing_params))}")
        family_required_params = FAMILY_REQUIRED_PARAM_FIELDS.get(str(spec["family"]), set())
        missing_family_params = family_required_params - set(spec["params"])
        if missing_family_params:
            raise WorkflowError(
                f"{path}: missing {spec['family']} params: {', '.join(sorted(missing_family_params))}"
            )

        if not isinstance(spec["nodes"], list):
            raise WorkflowError(f"{path}: nodes must be a list.")
        if not isinstance(spec["links"], list):
            raise WorkflowError(f"{path}: links must be a list.")

        if not isinstance(spec["output"], dict):
            raise WorkflowError(f"{path}: output must be an object.")
        missing_output = REQUIRED_OUTPUT_FIELDS - set(spec["output"])
        if missing_output:
            raise WorkflowError(f"{path}: missing output fields: {', '.join(sorted(missing_output))}")

        family_dir = path.parent.name
        preset_name = path.stem
        if spec["family"] != family_dir:
            raise WorkflowError(f"{path}: family must match directory name {family_dir!r}.")
        if spec["preset"] != preset_name:
            raise WorkflowError(f"{path}: preset must match file stem {preset_name!r}.")

        if self.is_active_family(spec["family"]):
            if str(spec["params"]["safe_zone"]).strip().lower() == "none":
                raise WorkflowError(f"{path}: active workflows must declare a non-'none' safe_zone.")
            if "caption_safe_zone" in spec["params"]:
                validate_caption_safe_payload(path, "params.caption_safe_zone", spec["params"]["caption_safe_zone"])

        pipeline_strategy = spec.get("pipeline_strategy")
        if pipeline_strategy is not None:
            self.validate_pipeline_strategy(path, pipeline_strategy)

        prompt_fragments = spec.get("prompt_fragments")
        if prompt_fragments is not None:
            self.validate_prompt_fragments(path, str(spec["family"]), prompt_fragments)

    def validate_pipeline_strategy(self, path: Path, pipeline_strategy: Any) -> None:
        if not isinstance(pipeline_strategy, dict):
            raise WorkflowError(f"{path}: pipeline_strategy must be an object when present.")
        missing = PIPELINE_STRATEGY_REQUIRED_FIELDS - set(pipeline_strategy)
        if missing:
            raise WorkflowError(
                f"{path}: pipeline_strategy missing fields: {', '.join(sorted(missing))}"
            )
        seed_policy = str(pipeline_strategy.get("seed_policy", "")).strip()
        if seed_policy not in PIPELINE_STRATEGY_ALLOWED_SEED_POLICIES:
            raise WorkflowError(
                f"{path}: pipeline_strategy.seed_policy must be one of "
                f"{sorted(PIPELINE_STRATEGY_ALLOWED_SEED_POLICIES)}."
            )
        try:
            draft_candidate_count = int(pipeline_strategy.get("draft_candidate_count", 0))
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{path}: pipeline_strategy.draft_candidate_count must be an integer.") from exc
        if draft_candidate_count < 1:
            raise WorkflowError(f"{path}: pipeline_strategy.draft_candidate_count must be >= 1.")
        hero_model = str(pipeline_strategy.get("hero_model", "")).strip()
        if not hero_model:
            raise WorkflowError(f"{path}: pipeline_strategy.hero_model must be non-empty.")
        try:
            hero_refine_denoise = float(pipeline_strategy.get("hero_refine_denoise", 0.0))
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{path}: pipeline_strategy.hero_refine_denoise must be numeric.") from exc
        if hero_refine_denoise < 0.0:
            raise WorkflowError(f"{path}: pipeline_strategy.hero_refine_denoise must be >= 0.")
        semantic_qc_profile = str(pipeline_strategy.get("semantic_qc_profile", "")).strip()
        if not semantic_qc_profile:
            raise WorkflowError(f"{path}: pipeline_strategy.semantic_qc_profile must be non-empty.")

    def validate_prompt_fragments(self, path: Path, family: str, prompt_fragments: Any) -> None:
        if not isinstance(prompt_fragments, dict):
            raise WorkflowError(f"{path}: prompt_fragments must be an object when present.")
        missing = PROMPT_FRAGMENT_REQUIRED_FIELDS - set(prompt_fragments)
        if missing:
            raise WorkflowError(
                f"{path}: prompt_fragments missing fields: {', '.join(sorted(missing))}"
            )
        anchor_fragment = str(prompt_fragments.get("anchor_fragment", "")).strip()
        if not anchor_fragment:
            raise WorkflowError(f"{path}: prompt_fragments.anchor_fragment must be non-empty.")
        if not isinstance(prompt_fragments.get("support_fragments"), list):
            raise WorkflowError(f"{path}: prompt_fragments.support_fragments must be a list.")
        support_fragments = unique_string_list(prompt_fragments.get("support_fragments"))
        if not support_fragments:
            raise WorkflowError(f"{path}: prompt_fragments.support_fragments must contain at least one item.")
        support_limit = PROMPT_SUPPORT_LIMITS.get(family)
        if support_limit is not None and len(support_fragments) > support_limit:
            raise WorkflowError(
                f"{path}: {family} prompt_fragments.support_fragments is capped at {support_limit} items."
            )
        for field in PROMPT_FRAGMENT_OPTIONAL_FIELDS:
            value = prompt_fragments.get(field, [])
            if value is not None and not isinstance(value, list):
                raise WorkflowError(f"{path}: prompt_fragments.{field} must be a list when present.")

    def normalize_pipeline_strategy(self, spec: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        raw = spec.get("pipeline_strategy")
        if isinstance(raw, dict):
            return {
                "seed_policy": str(raw["seed_policy"]).strip(),
                "draft_candidate_count": int(raw["draft_candidate_count"]),
                "hero_model": str(raw["hero_model"]).strip(),
                "hero_refine_denoise": float(raw["hero_refine_denoise"]),
                "semantic_qc_profile": str(raw["semantic_qc_profile"]).strip(),
            }
        return {
            "seed_policy": str(params.get("seed_mode", "fixed")).strip() or "fixed",
            "draft_candidate_count": max(1, int(params.get("variant_count", 1) or 1)),
            "hero_model": str(params.get("full_unet_name", "") or params.get("checkpoint", "")).strip().rsplit(".", 1)[0],
            "hero_refine_denoise": float(params.get("refine_denoise", 0.0) or 0.0),
            "semantic_qc_profile": "",
        }

    def compose_positive_prompt(
        self,
        *,
        family: str,
        stage: str,
        style: dict[str, Any],
        params: dict[str, Any],
        prompt_fragments: dict[str, Any],
    ) -> str:
        prompts = style.get("prompts", {})
        anchor_fragment = str(prompt_fragments["anchor_fragment"]).strip()
        support_fragments = unique_string_list(prompt_fragments.get("support_fragments"))
        directives = unique_string_list(prompt_fragments.get("directives"))
        stage_directives = unique_string_list(prompt_fragments.get(f"{stage.split('_', 1)[0]}_directives"))
        pieces: list[str] = []
        minimal_surreal_mode = style_uses_minimal_surreal_contract(style)
        minimal_surreal_prompt_phrases = MINIMAL_SURREAL_REQUIRED_PROMPT_PHRASES
        subject_reference_present = bool(str(params.get("subject_reference_image", "")).strip())
        subject_reference_path_hint = str(params.get("subject_reference_image", "")).strip().replace("\\", "/")
        caption_safe_zone = format_caption_safe_zone(params.get("caption_safe_zone"))
        historical_anchor = str(params.get("historical_anchor", "")).strip()
        surreal_breach = str(params.get("surreal_breach", "")).strip()
        minimal_surreal_contract = ", ".join(minimal_surreal_prompt_phrases)

        if stage == "draft_txt2img":
            pieces.append(str(prompts.get("global_base", "")).strip())
            if minimal_surreal_mode:
                if family == "shorts_scene_plate":
                    pieces.append(
                        "portrait beat plate for vertical shorts, mobile-legible silhouette, "
                        "primary subject kept outside the subtitle and top-ui keep-out bands"
                    )
                elif family in PACKAGING_FAMILIES:
                    pieces.append(
                        "portrait packaging plate, high small-size clarity, one dominant anchor object "
                        "placed off-center, quiet header-safe field"
                    )
            else:
                if family == "shorts_scene_plate":
                    pieces.append(str(prompts.get("shorts_scene_base", prompts.get("scene_base", ""))).strip())
                elif family in PACKAGING_FAMILIES:
                    pieces.append(str(prompts.get("packaging_base", "")).strip())
                    pieces.append(
                        str(
                            prompts.get("thumbnail_base" if family == "thumbnail_plate" else "shorts_base", "")
                        ).strip()
                    )
                    pieces.append("recognizable anchor object")
            pieces.append(f"anchor fragment: {anchor_fragment}")
            limited_support_fragments = (
                support_fragments[: (1 if family in PACKAGING_FAMILIES else 2)]
                if minimal_surreal_mode
                else support_fragments
            )
            pieces.append(f"layered support fragments: {', '.join(limited_support_fragments)}")
            if historical_anchor:
                pieces.append(f"historical anchor: {historical_anchor}")
            if surreal_breach:
                pieces.append(f"surreal breach: {surreal_breach}")
            if subject_reference_present:
                pieces.append("preserve recognizable silhouette and major geometry of the reference subject")
                pieces.append("stylize surface and atmosphere rather than identity")
                if "subject_reference_plates/generated/" in subject_reference_path_hint:
                    pieces.append(MINIMAL_SURREAL_REFERENCE_PLATE_PROMPT_PHRASE)
            if minimal_surreal_mode:
                pieces.append(minimal_surreal_contract)
            if caption_safe_zone:
                pieces.append(f"caption-safe keep-out zones {caption_safe_zone}")
            if minimal_surreal_mode:
                compact_directives = unique_phrase_list(directives, stage_directives)[:6]
                pieces.extend(compact_directives)
                pieces.append(f"accent palette {params['accent_palette']}")
                if family == "shorts_scene_plate":
                    pieces.append(f"safe-zone intent {params['safe_zone_intent']}")
            else:
                pieces.extend(directives)
                pieces.extend(stage_directives)
                pieces.append(f"accent palette {params['accent_palette']}")
                pieces.append(f"safe-zone intent {params['safe_zone_intent']}")
        elif stage == "refine_img2img":
            pieces.append(str(prompts.get("global_base", "")).strip())
            if family == "shorts_scene_plate":
                pieces.append(str(prompts.get("shorts_scene_base", prompts.get("scene_base", ""))).strip())
            elif family in PACKAGING_FAMILIES:
                pieces.append(str(prompts.get("packaging_base", "")).strip())
                pieces.append(
                    str(
                        prompts.get("thumbnail_base" if family == "thumbnail_plate" else "shorts_base", "")
                    ).strip()
                )
                pieces.append("recognizable anchor object")
            pieces.append(str(prompts.get("refine_base", "")).strip())
            pieces.append(f"preserve the anchor fragment: {anchor_fragment}")
            pieces.append(f"preserve the layered support fragments: {', '.join(support_fragments)}")
            if historical_anchor:
                pieces.append(f"preserve the historical anchor: {historical_anchor}")
            if surreal_breach:
                pieces.append(f"preserve exactly one surreal breach: {surreal_breach}")
            if subject_reference_present:
                pieces.append("preserve recognizable silhouette and major geometry of the reference subject")
                pieces.append("stylize surface and atmosphere rather than identity")
                if "subject_reference_plates/generated/" in subject_reference_path_hint:
                    pieces.append(MINIMAL_SURREAL_REFERENCE_PLATE_PROMPT_PHRASE)
            if minimal_surreal_mode:
                pieces.extend(minimal_surreal_prompt_phrases)
            if caption_safe_zone:
                pieces.append(f"caption-safe keep-out zones {caption_safe_zone}")
            pieces.extend(directives)
            pieces.extend(stage_directives)
            pieces.append(f"accent palette {params['accent_palette']}")
        elif stage == "final_upscale":
            pieces.append(str(prompts.get("final_base", "")).strip())
            if family in PACKAGING_FAMILIES:
                pieces.append("recognizable anchor object")
            pieces.append(f"preserve the anchor fragment: {anchor_fragment}")
            pieces.append(f"preserve the layered support fragments: {', '.join(support_fragments)}")
            if historical_anchor:
                pieces.append(f"preserve the historical anchor: {historical_anchor}")
            if surreal_breach:
                pieces.append(f"preserve exactly one surreal breach: {surreal_breach}")
            if subject_reference_present:
                pieces.append("preserve recognizable silhouette and major geometry of the reference subject")
                pieces.append("stylize surface and atmosphere rather than identity")
                if "subject_reference_plates/generated/" in subject_reference_path_hint:
                    pieces.append(MINIMAL_SURREAL_REFERENCE_PLATE_PROMPT_PHRASE)
            if minimal_surreal_mode:
                pieces.extend(minimal_surreal_prompt_phrases)
            if caption_safe_zone:
                pieces.append(f"caption-safe keep-out zones {caption_safe_zone}")
            pieces.extend(directives)
            pieces.extend(stage_directives)
            pieces.append(f"accent palette {params['accent_palette']}")
        else:
            return str(params["positive_prompt"]).strip()

        return ", ".join(part for part in pieces if part)

    def compose_midjourney_package_prompt(
        self,
        *,
        shot: Any,
        params: dict[str, Any],
        adapter: Any | None = None,
    ) -> str:
        pieces = [str(shot.prompt_text).strip()]
        caption_safe_zone = format_caption_safe_zone(params.get("caption_safe_zone"))
        if caption_safe_zone:
            pieces.append(f"caption-safe keep-out zones {caption_safe_zone}")
        pieces.append("recognizable anchor object")
        pieces.extend(MINIMAL_SURREAL_REQUIRED_PROMPT_PHRASES)
        pieces.append(
            "ordered reference grid is guidance only, not visible collage panels, tiled reference windows, or pasted source fragments"
        )
        if adapter is not None:
            pieces.extend(item for item in adapter.prompt_adapter_append if str(item).strip())
            steer_target = MIDJOURNEY_STEER_TARGET_PROMPT_MAP.get(str(adapter.steer_target).strip(), "")
            if steer_target:
                pieces.append(steer_target)
            if adapter.steer_keep_traits:
                pieces.append(f"prefer {', '.join(str(item).strip() for item in adapter.steer_keep_traits if str(item).strip())}")
            if adapter.steer_avoid_traits:
                pieces.append(f"avoid {', '.join(str(item).strip() for item in adapter.steer_avoid_traits if str(item).strip())}")
        return ", ".join(part for part in pieces if part)

    def load_style_profile(self, name: str) -> dict[str, Any]:
        path = self.style_profiles_dir / f"{name}.json"
        if not path.exists():
            raise WorkflowError(f"Missing style profile: {path}")
        style = read_json(path)
        missing = STYLE_PROFILE_REQUIRED_FIELDS - set(style)
        if missing:
            raise WorkflowError(f"{path}: missing style-profile fields: {', '.join(sorted(missing))}")
        if style["name"] != name:
            raise WorkflowError(f"{path}: style profile name must match file stem {name!r}.")
        if not isinstance(style["defaults"], dict) or not isinstance(style["prompts"], dict):
            raise WorkflowError(f"{path}: style profile defaults/prompts must be objects.")
        for field in STYLE_PROFILE_OPTIONAL_LIST_FIELDS:
            if field in style and not isinstance(style[field], list):
                raise WorkflowError(f"{path}: style profile field {field!r} must be a list when present.")
        for field in STYLE_PROFILE_OPTIONAL_OBJECT_FIELDS:
            if field in style and not isinstance(style[field], dict):
                raise WorkflowError(f"{path}: style profile field {field!r} must be an object when present.")
        if "caption_safe_defaults" in style:
            style["caption_safe_defaults"] = validate_caption_safe_payload(
                path,
                "caption_safe_defaults",
                style["caption_safe_defaults"],
            )
        if "subject_reference_defaults" in style:
            style["subject_reference_defaults"] = validate_subject_reference_defaults(
                path,
                "subject_reference_defaults",
                style["subject_reference_defaults"],
            )
        if "plate_seed_defaults" in style:
            style["plate_seed_defaults"] = validate_plate_seed_defaults(
                path,
                "plate_seed_defaults",
                style["plate_seed_defaults"],
            )
        return style

    def apply_subject_reference_defaults(self, style: dict[str, Any], params: dict[str, Any]) -> None:
        if not style_uses_subject_reference_conditioning(style):
            return
        stage = str(params.get("stage", "")).strip()
        if stage not in SUBJECT_REFERENCE_REQUIRED_STAGES:
            return
        defaults = style["subject_reference_defaults"]
        params.setdefault("subject_reference_runtime_image", str(params.get("subject_reference_image", "")).strip())
        params.setdefault("subject_reference_runtime_mask", "")
        params.setdefault("subject_reference_crop", defaults["crop"])
        params.setdefault("subject_reference_noise_augmentation", defaults["noise_augmentation"])
        params.setdefault(
            "subject_reference_strength",
            defaults["draft_strength"] if stage == "draft_txt2img" else defaults["refine_strength"],
        )
        env_name = str(defaults["clip_vision_model_env"]).strip()
        params.setdefault(
            "subject_reference_clip_vision_model",
            self.comfy_clip_vision_model or os.environ.get(env_name, "").strip(),
        )

    def resolve_midjourney_package_shot(self, params: dict[str, Any]) -> Any:
        raw_path = str(params.get("midjourney_package_path", "")).strip()
        if not raw_path:
            raise WorkflowError("midjourney_package_path must be non-empty for reference_mode=midjourney_package_grid.")
        shot_id = str(params.get("midjourney_shot_id", "")).strip()
        if not shot_id:
            raise WorkflowError("midjourney_shot_id must be non-empty for reference_mode=midjourney_package_grid.")
        try:
            return load_midjourney_package_shot(raw_path, shot_id=shot_id, repo_root=self.repo_root)
        except MidjourneyPackageError as exc:
            raise WorkflowError(str(exc)) from exc

    def resolve_midjourney_package_adapter(
        self,
        params: dict[str, Any],
        *,
        shot: Any | None = None,
    ) -> Any | None:
        raw_path = str(params.get("midjourney_adapter_path", "")).strip()
        if not raw_path:
            return None
        resolved_shot = shot if shot is not None else self.resolve_midjourney_package_shot(params)
        try:
            return load_midjourney_package_adapter(raw_path, shot=resolved_shot, repo_root=self.repo_root)
        except MidjourneyPackageError as exc:
            raise WorkflowError(str(exc)) from exc

    def default_midjourney_grid_runtime_image(self, family: str, base_preset: str, shot_id: str) -> str:
        return (
            f"cascadeeffects/midjourney_package_grids/{family}/{base_preset}/{grid_runtime_filename(shot_id=shot_id)}"
        )

    def apply_midjourney_package_defaults(
        self,
        spec: dict[str, Any],
        style: dict[str, Any],
        params: dict[str, Any],
    ) -> None:
        if not minimal_surreal_midjourney_package_grid_active(spec=spec, style=style, params=params):
            return
        shot = self.resolve_midjourney_package_shot(params)
        adapter = self.resolve_midjourney_package_adapter(params, shot=shot)
        base_preset = self.base_preset_name(str(spec["preset"]), str(params.get("stage", "")))
        params["midjourney_package_id"] = shot.package_id
        params["midjourney_package_manifest_path"] = path_text_for_manifest(
            shot.package_manifest_path,
            repo_root=self.repo_root,
        )
        params["midjourney_prompt_doc_path"] = shot.prompt_doc_path
        params["midjourney_references_manifest_path"] = shot.references_manifest_path
        params["midjourney_package_prompt_text"] = shot.prompt_text
        params["midjourney_package_negative_terms"] = normalize_midjourney_negative_terms(list(shot.negative_terms))
        params["midjourney_reference_files"] = list(shot.reference_files)
        if adapter is not None:
            params["midjourney_adapter_manifest_path"] = path_text_for_manifest(
                adapter.adapter_path,
                repo_root=self.repo_root,
            )
            params["midjourney_adapter_prompt_append"] = list(adapter.prompt_adapter_append)
            params["midjourney_adapter_negative_terms"] = list(adapter.negative_adapter_terms)
            params["midjourney_adapter_grid_layout_template"] = adapter.grid_layout_template
            params["midjourney_adapter_included_reference_indices"] = list(adapter.included_reference_indices)
            params["midjourney_adapter_reference_crops"] = {
                str(index): list(crop) for index, crop in sorted(adapter.reference_crops.items())
            }
            params["midjourney_adapter_draft_visual_softpass"] = {
                "enabled": bool(adapter.draft_visual_softpass.get("enabled", False)),
                "allowed_visual_failures": list(adapter.draft_visual_softpass.get("allowed_visual_failures", [])),
            }
            params["midjourney_adapter_steer_target"] = adapter.steer_target
            params["midjourney_adapter_steer_keep_traits"] = list(adapter.steer_keep_traits)
            params["midjourney_adapter_steer_avoid_traits"] = list(adapter.steer_avoid_traits)
            params["midjourney_adapter_ranking_bias_tags"] = list(adapter.ranking_bias_tags)
        runtime_grid_path = self.default_midjourney_grid_runtime_image(
            str(spec["family"]),
            base_preset,
            shot.shot_id,
        )
        params["subject_reference_image"] = runtime_grid_path
        params["subject_reference_runtime_image"] = runtime_grid_path
        params["subject_reference_runtime_mask"] = ""

    def apply_plate_seed_defaults(
        self,
        spec: dict[str, Any],
        style: dict[str, Any],
        params: dict[str, Any],
    ) -> None:
        if not minimal_surreal_plate_seed_active(spec=spec, style=style, params=params):
            return
        defaults = style["plate_seed_defaults"]
        params.setdefault("draft_plate_seed_denoise", defaults["draft_denoise"])

    def apply_subject_reference_plate_controls(
        self,
        spec: dict[str, Any],
        style: dict[str, Any],
        params: dict[str, Any],
    ) -> None:
        raw_subject_reference = str(params.get("subject_reference_image", "")).strip()
        existing_runtime_image = str(params.get("subject_reference_runtime_image", "")).strip()
        existing_runtime_mask = str(params.get("subject_reference_runtime_mask", "")).strip()
        runtime_image_uses_default = not existing_runtime_image or existing_runtime_image == raw_subject_reference
        params["palette_lock_active"] = False
        params["palette_lock_accent_box"] = []
        params["spatial_mask_active"] = False
        params["spatial_mask_allow_box"] = []
        params["spatial_mask_exclusion_boxes"] = []
        params["composition_control_active"] = False
        params["composition_control_mode"] = ""
        params["subject_reference_preview_path"] = str(params.get("subject_reference_image", "")).strip()
        params["subject_reference_vision_ref_path"] = ""
        params["subject_reference_layout_mask_path"] = ""
        params["subject_reference_seed_rgba_path"] = ""
        params["subject_reference_soft_mask_path"] = ""
        params["subject_reference_runtime_image"] = (
            existing_runtime_image or str(params.get("subject_reference_image", "")).strip()
        )
        params["subject_reference_runtime_mask"] = existing_runtime_mask

        if minimal_surreal_midjourney_package_grid_active(spec=spec, style=style, params=params):
            return
        if not style_uses_subject_reference_conditioning(style):
            return
        stage = str(params.get("stage", "")).strip()
        if stage not in SUBJECT_REFERENCE_REQUIRED_STAGES:
            return
        if not raw_subject_reference:
            return
        source_path = self.resolve_subject_reference_path(raw_subject_reference)
        if not source_path.exists():
            return
        plate_status = build_status_for_output(source_path)
        if plate_status is None or not plate_status.get("ready"):
            return
        build_manifest_path = Path(str(plate_status["build_manifest_path"])).expanduser().resolve()
        if not build_manifest_path.exists():
            return
        build_manifest = read_json(build_manifest_path)
        accent_box = build_manifest.get("accent_box") or []
        allow_box = build_manifest.get("generation_allow_box") or []
        exclusion_boxes = build_manifest.get("generation_exclusion_boxes") or []
        vision_ref_path = str(build_manifest.get("vision_ref_path", "")).strip()
        layout_mask_path = str(build_manifest.get("layout_mask_path", "")).strip()
        seed_rgba_path = str(build_manifest.get("seed_rgba_path", "")).strip()
        soft_mask_path = str(build_manifest.get("soft_mask_path", "")).strip()

        params["palette_lock_active"] = bool(accent_box)
        params["palette_lock_accent_box"] = copy.deepcopy(accent_box)
        params["spatial_mask_allow_box"] = copy.deepcopy(allow_box)
        params["spatial_mask_exclusion_boxes"] = copy.deepcopy(exclusion_boxes)
        params["spatial_mask_active"] = bool(allow_box or exclusion_boxes)
        params["subject_reference_preview_path"] = str(build_manifest.get("preview_path", raw_subject_reference)).strip()
        params["subject_reference_vision_ref_path"] = vision_ref_path
        params["subject_reference_layout_mask_path"] = layout_mask_path
        params["subject_reference_seed_rgba_path"] = seed_rgba_path
        params["subject_reference_soft_mask_path"] = soft_mask_path
        if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=params):
            params["composition_control_active"] = True
            params["composition_control_mode"] = "hidden_control_full_frame"
            if vision_ref_path and runtime_image_uses_default:
                params["subject_reference_runtime_image"] = vision_ref_path
            if layout_mask_path and not existing_runtime_mask:
                params["subject_reference_runtime_mask"] = layout_mask_path
        if (
            minimal_surreal_plate_seed_active(spec=spec, style=style, params=params)
            and seed_rgba_path
            and runtime_image_uses_default
        ):
            params["subject_reference_runtime_image"] = seed_rgba_path

    def load_fragment(self, name: str) -> dict[str, Any]:
        path = self.fragments_dir / f"{name}.json"
        if not path.exists():
            raise WorkflowError(f"Missing fragment: {path}")
        fragment = read_json(path)
        for required in ("name", "nodes", "links"):
            if required not in fragment:
                raise WorkflowError(f"{path}: missing fragment field {required!r}")
        return fragment

    def typography_sidecar_path(self, family: str, base_preset: str) -> Path:
        return self.typography_dir / family / f"{base_preset}.json"

    def repair_policy_path(self, family: str, base_preset: str) -> Path:
        return self.source_text_repair_dir / family / f"{base_preset}.json"

    def load_typography_sidecar(
        self,
        family: str,
        base_preset: str,
        *,
        required: bool = False,
    ) -> tuple[Path, dict[str, Any]] | None:
        cache_key = (family, base_preset)
        if cache_key in self._typography_cache:
            cached = self._typography_cache[cache_key]
            if cached is None and required:
                raise WorkflowError(
                    f"Missing controlled typography sidecar for {family}/{base_preset}: "
                    f"{self.typography_sidecar_path(family, base_preset)}"
                )
            return cached

        path = self.typography_sidecar_path(family, base_preset)
        if not path.exists():
            self._typography_cache[cache_key] = None
            if required:
                raise WorkflowError(f"Missing controlled typography sidecar for {family}/{base_preset}: {path}")
            return None

        data = read_json(path)
        self.validate_typography_sidecar(path, data, family, base_preset)
        loaded = (
            path,
            normalize_typography_intent(
                data,
                expected_family=family,
                expected_preset=base_preset,
                active_family_check=self.is_active_family,
                path=path,
            ),
        )
        self._typography_cache[cache_key] = loaded
        return loaded

    def load_repair_policy(
        self,
        family: str,
        base_preset: str,
        *,
        required: bool = False,
    ) -> tuple[Path, dict[str, Any]] | None:
        cache_key = (family, base_preset)
        if cache_key in self._repair_policy_cache:
            cached = self._repair_policy_cache[cache_key]
            if cached is None and required:
                raise WorkflowError(
                    f"Missing source-text repair policy for {family}/{base_preset}: "
                    f"{self.repair_policy_path(family, base_preset)}"
                )
            return cached

        path = self.repair_policy_path(family, base_preset)
        if not path.exists():
            self._repair_policy_cache[cache_key] = None
            if required:
                raise WorkflowError(f"Missing source-text repair policy for {family}/{base_preset}: {path}")
            return None

        data = read_json(path)
        loaded = (path, self.validate_repair_policy_sidecar(path, data, family, base_preset))
        self._repair_policy_cache[cache_key] = loaded
        return loaded

    def validate_typography_sidecar(
        self,
        path: Path,
        data: dict[str, Any],
        family: str,
        base_preset: str,
    ) -> None:
        try:
            normalize = normalize_typography_intent(
                data,
                expected_family=family,
                expected_preset=base_preset,
                active_family_check=self.is_active_family,
                path=path,
            )
            _ = normalize
        except TypographyContractError as exc:
            raise WorkflowError(str(exc)) from exc

    def validate_repair_policy_sidecar(
        self,
        path: Path,
        data: dict[str, Any],
        family: str,
        base_preset: str,
    ) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise WorkflowError(f"{path}: repair policy must be an object.")
        missing = REPAIR_POLICY_REQUIRED_FIELDS - set(data)
        if missing:
            raise WorkflowError(f"{path}: missing repair-policy fields: {', '.join(sorted(missing))}")
        if data.get("family") != family:
            raise WorkflowError(f"{path}: family must match {family!r}.")
        if data.get("preset") != base_preset:
            raise WorkflowError(f"{path}: preset must match {base_preset!r}.")
        application_stage = str(data["application_stage"])
        if application_stage not in REPAIR_ALLOWED_APPLICATION_STAGES:
            raise WorkflowError(
                f"{path}: unsupported application_stage {application_stage!r}; "
                f"expected one of {sorted(REPAIR_ALLOWED_APPLICATION_STAGES)}."
            )
        surface_scope = str(data["surface_scope"])
        if surface_scope not in REPAIR_ALLOWED_SURFACE_SCOPES:
            raise WorkflowError(
                f"{path}: unsupported surface_scope {surface_scope!r}; "
                f"expected one of {sorted(REPAIR_ALLOWED_SURFACE_SCOPES)}."
            )
        llm_backend = str(data["llm_backend"])
        if llm_backend not in REPAIR_ALLOWED_BACKENDS:
            raise WorkflowError(
                f"{path}: unsupported llm_backend {llm_backend!r}; expected one of {sorted(REPAIR_ALLOWED_BACKENDS)}."
            )
        if not isinstance(data["llm_model"], str) or not data["llm_model"].strip():
            raise WorkflowError(f"{path}: llm_model must be a non-empty string.")
        if not isinstance(data["enabled"], bool):
            raise WorkflowError(f"{path}: enabled must be a boolean.")
        if not isinstance(data["allow_repaired_text_outside_typography_zones"], bool):
            raise WorkflowError(f"{path}: allow_repaired_text_outside_typography_zones must be a boolean.")
        ambiguous_fallback_action = str(data["ambiguous_environmental_fallback_action"])
        if ambiguous_fallback_action not in {"ignore", "erase"}:
            raise WorkflowError(
                f"{path}: ambiguous_environmental_fallback_action must be 'ignore' or 'erase'."
            )
        try:
            max_regions = int(data["max_regions"])
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{path}: max_regions must be an integer.") from exc
        if max_regions < 1:
            raise WorkflowError(f"{path}: max_regions must be >= 1.")
        numeric_fields = (
            "ocr_confidence_floor",
            "rewrite_confidence_floor",
            "erase_confidence_floor",
        )
        normalized = dict(data)
        normalized["max_regions"] = max_regions
        for field in numeric_fields:
            try:
                value = float(data[field])
            except (TypeError, ValueError) as exc:
                raise WorkflowError(f"{path}: {field} must be numeric.") from exc
            if value < 0.0:
                raise WorkflowError(f"{path}: {field} must be >= 0.")
            normalized[field] = value
        if not isinstance(data["context_terms"], list) or not all(
            isinstance(item, str) and item.strip() for item in data["context_terms"]
        ):
            raise WorkflowError(f"{path}: context_terms must be a list of non-empty strings.")
        if not isinstance(data["forbidden_surface_types"], list) or not all(
            isinstance(item, str) and item.strip() for item in data["forbidden_surface_types"]
        ):
            raise WorkflowError(f"{path}: forbidden_surface_types must be a list of non-empty strings.")
        cleanup = data.get("post_final_cleanup")
        if cleanup is None:
            normalized_cleanup = dict(REPAIR_POST_FINAL_CLEANUP_DEFAULTS)
        elif isinstance(cleanup, dict):
            normalized_cleanup = dict(REPAIR_POST_FINAL_CLEANUP_DEFAULTS)
            normalized_cleanup.update(cleanup)
        else:
            raise WorkflowError(f"{path}: post_final_cleanup must be an object when present.")
        if not isinstance(normalized_cleanup["enabled"], bool):
            raise WorkflowError(f"{path}: post_final_cleanup.enabled must be a boolean.")
        cleanup_mode = str(normalized_cleanup["mode"])
        if cleanup_mode != "erase_only":
            raise WorkflowError(f"{path}: post_final_cleanup.mode must be 'erase_only'.")
        try:
            cleanup_max_regions = int(normalized_cleanup["max_regions"])
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{path}: post_final_cleanup.max_regions must be an integer.") from exc
        if cleanup_max_regions < 1:
            raise WorkflowError(f"{path}: post_final_cleanup.max_regions must be >= 1.")
        normalized["context_terms"] = [str(item).strip() for item in data["context_terms"]]
        normalized["forbidden_surface_types"] = [str(item).strip() for item in data["forbidden_surface_types"]]
        normalized["ambiguous_environmental_fallback_action"] = ambiguous_fallback_action
        normalized["post_final_cleanup"] = {
            "enabled": bool(normalized_cleanup["enabled"]),
            "mode": cleanup_mode,
            "max_regions": cleanup_max_regions,
        }
        return normalized

    def select_specs(self, family: str, preset: str | None = None) -> list[Path]:
        specs = self.list_specs(active_only=True)
        if family == "all":
            selected = specs
        else:
            if self.is_retired_family(family):
                raise WorkflowError(f"{family} is retired from the active workflow surface.")
            selected = [path for path in specs if path.parent.name == family]
        if preset is not None:
            selected = [path for path in selected if path.stem == preset]
        if not selected:
            target = family if preset is None else f"{family}/{preset}"
            raise WorkflowError(f"No workflow specs found for {target}.")
        return selected

    def retired_sync_targets(self) -> list[Path]:
        targets: list[Path] = []
        for path in self.all_spec_paths():
            if not self.is_retired_family(path.parent.name):
                continue
            spec = read_json(path)
            sync_name = spec.get("output", {}).get("sync_filename")
            if sync_name:
                targets.append(self.comfy_workflows_dir / sync_name)
        return sorted(targets)

    def stage_spec_name(self, base_preset: str, stage: str) -> str:
        return f"{base_preset}__{stage}"

    def base_preset_name(self, preset: str, stage: str) -> str:
        suffix = f"__{stage}"
        if preset.endswith(suffix):
            return preset[: -len(suffix)]
        return preset

    def resolve_stage_spec_path(self, family: str, base_preset: str, stage: str) -> Path:
        spec_name = self.stage_spec_name(base_preset, stage)
        candidates = self.select_specs(family, spec_name)
        if len(candidates) != 1:
            raise WorkflowError(f"Expected exactly one workflow spec for {family}/{spec_name}.")
        return candidates[0]

    def list_workflows(self) -> None:
        rows = []
        for path in self.list_specs():
            spec = self.load_spec(path)
            rows.append(
                (
                    spec["family"],
                    spec["preset"],
                    spec["params"]["stage"],
                    spec["base_fragment"],
                    spec["output"]["generated_filename"],
                    spec["output"]["sync_filename"],
                )
            )
        for family, preset, stage, fragment, generated, sync_name in rows:
            print(
                f"{family:<20} {preset:<44} stage={stage:<16} fragment={fragment:<24} sync={sync_name}"
            )

    def build_many(
        self,
        spec_paths: list[Path],
        write_generated: bool,
        overrides: dict[str, Any] | None = None,
    ) -> list[BuildResult]:
        results: list[BuildResult] = []
        generated_names: set[str] = set()
        sync_names: set[str] = set()

        for path in spec_paths:
            result = self.build_one(path, write_generated=write_generated, overrides=overrides or {})
            generated_name = result.generated_workflow_path.name
            sync_name = result.sync_target_path.name
            if generated_name in generated_names:
                raise WorkflowError(f"Duplicate generated filename detected: {generated_name}")
            if sync_name in sync_names:
                raise WorkflowError(f"Duplicate sync filename detected: {sync_name}")
            generated_names.add(generated_name)
            sync_names.add(sync_name)
            results.append(result)
        return results

    def build_one(
        self,
        spec_path: Path,
        write_generated: bool,
        overrides: dict[str, Any],
    ) -> BuildResult:
        spec = self.load_spec(spec_path)
        fragment = self.load_fragment(spec["base_fragment"])

        params = copy.deepcopy(spec["params"])
        style = {"name": "", "defaults": {}, "prompts": {}}
        if self.is_active_family(spec["family"]):
            style = self.load_style_profile(str(params["style_profile"]))
        allowed_override_keys = set(params.keys())
        allowed_override_keys.update(style.get("defaults", {}).keys())
        if style_uses_subject_reference_conditioning(style):
            allowed_override_keys.update(
                {
                    "subject_reference_runtime_image",
                    "subject_reference_runtime_mask",
                    "subject_reference_crop",
                    "subject_reference_noise_augmentation",
                    "subject_reference_strength",
                    "subject_reference_clip_vision_model",
                }
            )
        if style_uses_plate_seed_defaults(style):
            allowed_override_keys.add("draft_plate_seed_denoise")
        for key, value in overrides.items():
            if key not in allowed_override_keys:
                raise WorkflowError(
                    f"{spec_path}: override {key!r} is not allowed for family {spec['family']}."
                )
            params[key] = value
        if self.is_active_family(spec["family"]):
            for key, value in style["defaults"].items():
                params.setdefault(key, copy.deepcopy(value))
            self.apply_subject_reference_defaults(style, params)
            self.apply_midjourney_package_defaults(spec, style, params)
            self.apply_plate_seed_defaults(spec, style, params)
            self.apply_subject_reference_plate_controls(spec, style, params)

        nodes_by_key: dict[str, dict[str, Any]] = {}
        ordered_keys: list[str] = []
        for node in fragment["nodes"]:
            key = node.get("key")
            if not key:
                raise WorkflowError(f"{spec_path}: fragment node missing key.")
            if key in nodes_by_key:
                raise WorkflowError(f"{spec_path}: duplicate fragment node key {key!r}.")
            nodes_by_key[key] = copy.deepcopy(node)
            ordered_keys.append(key)

        for override in spec["nodes"]:
            key = override.get("key")
            if not key:
                raise WorkflowError(f"{spec_path}: node override missing key.")
            if key in nodes_by_key:
                nodes_by_key[key] = deep_merge(nodes_by_key[key], override)
            else:
                required_new_fields = {"key", "type", "inputs", "outputs"}
                missing_new_fields = required_new_fields - set(override)
                if missing_new_fields:
                    raise WorkflowError(
                        f"{spec_path}: new node {key!r} is missing fields: {', '.join(sorted(missing_new_fields))}"
                    )
                nodes_by_key[key] = copy.deepcopy(override)
                ordered_keys.append(key)

        if self.nodes_require_checkpoint_loader(nodes_by_key.values()):
            checkpoint_name = str(params.get("checkpoint", "")).strip()
            if not checkpoint_name:
                raise WorkflowError(f"{spec_path}: checkpoint-loader workflow is missing params.checkpoint.")
            checkpoint_path = self.models_root / "checkpoints" / checkpoint_name
            if not checkpoint_path.exists():
                raise WorkflowError(
                    f"{spec_path}: checkpoint {checkpoint_name!r} was not found in {checkpoint_path.parent}."
                )

        all_links = copy.deepcopy(fragment["links"]) + copy.deepcopy(spec["links"])
        context = {
            "family": spec["family"],
            "preset": spec["preset"],
            "params": params,
            "output": spec["output"],
            "style": style,
        }

        resolved_params = render_template(params, context)
        midjourney_package_mode = (
            self.is_active_family(spec["family"])
            and minimal_surreal_midjourney_package_grid_active(spec=spec, style=style, params=resolved_params)
        )
        midjourney_package_shot = (
            self.resolve_midjourney_package_shot(resolved_params) if midjourney_package_mode else None
        )
        midjourney_package_adapter = (
            self.resolve_midjourney_package_adapter(resolved_params, shot=midjourney_package_shot)
            if midjourney_package_shot is not None
            else None
        )
        pipeline_strategy = self.normalize_pipeline_strategy(spec, resolved_params)
        prompt_fragments = spec.get("prompt_fragments")
        if prompt_fragments is not None and self.is_active_family(spec["family"]) and not midjourney_package_mode:
            rendered_prompt_fragments = render_template(copy.deepcopy(prompt_fragments), context)
            resolved_params["positive_prompt"] = self.compose_positive_prompt(
                family=str(spec["family"]),
                stage=str(resolved_params["stage"]),
                style=style,
                params=resolved_params,
                prompt_fragments=rendered_prompt_fragments,
            )
        elif midjourney_package_shot is not None:
            resolved_params["positive_prompt"] = self.compose_midjourney_package_prompt(
                shot=midjourney_package_shot,
                params=resolved_params,
                adapter=midjourney_package_adapter,
            )
        if self.is_active_family(spec["family"]):
            resolved_params["negative_prompt"] = merge_prompt_phrases(
                style.get("negative_prompt_defaults", []),
                (
                    normalize_midjourney_negative_terms(list(midjourney_package_shot.negative_terms))
                    if midjourney_package_shot is not None
                    else []
                ),
                (
                    list(midjourney_package_adapter.negative_adapter_terms)
                    if midjourney_package_adapter is not None
                    else []
                ),
                resolved_params.get("negative_prompt", ""),
            )
        context["params"] = resolved_params
        resolved_nodes = [render_template(nodes_by_key[key], context) for key in ordered_keys]
        resolved_links = render_template(all_links, context)

        self.validate_active_semantics(spec_path, spec, style, resolved_params)

        warnings = self.dimension_warnings(
            spec["family"], int(resolved_params["width"]), int(resolved_params["height"])
        )
        dependency_report = self.dependency_report(spec, style, resolved_params)
        warnings.extend(dependency_report["warnings"])
        base_preset = self.base_preset_name(spec["preset"], str(resolved_params["stage"]))
        typography_sidecar = self.load_typography_sidecar(spec["family"], base_preset, required=False)
        repair_policy = self.load_repair_policy(spec["family"], base_preset, required=False)
        workflow = self.compile_native_workflow(spec, fragment, resolved_nodes, resolved_links)
        prompt = self.compile_api_prompt(spec, resolved_nodes, resolved_links)

        generated_workflow_path = self.generated_dir / spec["family"] / spec["output"]["generated_filename"]
        generated_prompt_path = (
            self.generated_dir
            / spec["family"]
            / spec["output"]["generated_filename"].replace(".workflow.json", ".prompt.json")
        )
        generated_manifest_path = (
            self.generated_dir
            / spec["family"]
            / spec["output"]["generated_filename"].replace(".workflow.json", ".manifest.json")
        )
        sync_target_path = self.comfy_workflows_dir / spec["output"]["sync_filename"]
        stage_requirements = self.stage_requirements(spec, style, resolved_params, dependency_report)
        if (
            str(resolved_params["stage"]) == "final_upscale"
            and repair_policy is not None
            and bool(repair_policy[1]["enabled"])
        ):
            stage_requirements["upstream_stage"] = "repair_source_text"

        manifest = {
            "family": spec["family"],
            "preset": spec["preset"],
            "base_preset": base_preset,
            "stage": resolved_params["stage"],
            "source_spec": str(spec_path.relative_to(self.repo_root)),
            "base_fragment": spec["base_fragment"],
            "style_profile_path": (
                str((self.style_profiles_dir / f"{resolved_params['style_profile']}.json").relative_to(self.repo_root))
                if self.is_active_family(spec["family"])
                else ""
            ),
            "generated_at": utc_now_iso(),
            "generated_workflow": str(generated_workflow_path.relative_to(self.repo_root)),
            "generated_prompt": str(generated_prompt_path.relative_to(self.repo_root)),
            "sync_target": str(sync_target_path),
            "artifacts": {
                "workflow": str(generated_workflow_path.relative_to(self.repo_root)),
                "prompt": str(generated_prompt_path.relative_to(self.repo_root)),
                "manifest": str(generated_manifest_path.relative_to(self.repo_root)),
                "sync_target": str(sync_target_path),
            },
            "checkpoint": resolved_params.get("checkpoint", ""),
            "dimensions": {"width": int(resolved_params["width"]), "height": int(resolved_params["height"])},
            "output_intent": spec["output"]["intent"],
            "filename_prefix": resolved_params["filename_prefix"],
            "prompt": resolved_params["positive_prompt"],
            "negative_prompt": resolved_params["negative_prompt"],
            "seed": resolved_params["seed"],
            "selected_seed": resolved_params["selected_seed"],
            "variant_count": resolved_params["variant_count"],
            "reference_board_dir": resolved_params["reference_board_dir"],
            "safe_zone": resolved_params["safe_zone"],
            "safe_zone_intent": resolved_params.get("safe_zone_intent", ""),
            "signal_anchor": resolved_params["signal_anchor"],
            "beat_id": resolved_params.get("beat_id", ""),
            "historical_anchor": resolved_params.get("historical_anchor", ""),
            "surreal_breach": resolved_params.get("surreal_breach", ""),
            "caption_safe_zone": resolved_params.get("caption_safe_zone", {}),
            "source_image": resolved_params["source_image"],
            "refine_denoise": resolved_params["refine_denoise"],
            "upscale_factor": resolved_params["upscale_factor"],
            "guidance": resolved_params["guidance"],
            "cfg": resolved_params["cfg"],
            "steps": resolved_params["steps"],
            "scheduler": resolved_params["scheduler"],
            "sampler_name": resolved_params["sampler_name"],
            "denoise": resolved_params["denoise"],
            "style_profile": resolved_params.get("style_profile", ""),
            "temperature": resolved_params.get("temperature", ""),
            "palette_policy": resolved_params.get("palette_policy", ""),
            "accent_palette": resolved_params.get("accent_palette", ""),
            "human_presence": resolved_params.get("human_presence", ""),
            "post_work": resolved_params.get("post_work", ""),
            "style_contract": {
                "negative_prompt_defaults": unique_string_list(style.get("negative_prompt_defaults", [])),
                "contract_metrics": copy.deepcopy(style.get("contract_metrics", {})),
                "caption_safe_defaults": copy.deepcopy(style.get("caption_safe_defaults", {})),
                "subject_reference_defaults": copy.deepcopy(style.get("subject_reference_defaults", {})),
                "plate_seed_defaults": copy.deepcopy(style.get("plate_seed_defaults", {})),
                "source_package": copy.deepcopy(style.get("source_package", {})),
            },
            "subject_reference": {
                "source_path": resolved_params.get("subject_reference_image", ""),
                "preview_path": resolved_params.get("subject_reference_preview_path", ""),
                "vision_ref_path": resolved_params.get("subject_reference_vision_ref_path", ""),
                "layout_mask_path": resolved_params.get("subject_reference_layout_mask_path", ""),
                "seed_rgba_path": resolved_params.get("subject_reference_seed_rgba_path", ""),
                "soft_mask_path": resolved_params.get("subject_reference_soft_mask_path", ""),
                "runtime_image": resolved_params.get("subject_reference_runtime_image", ""),
                "runtime_mask": resolved_params.get("subject_reference_runtime_mask", ""),
                "clip_vision_model": resolved_params.get("subject_reference_clip_vision_model", ""),
                "strength": resolved_params.get("subject_reference_strength"),
                "noise_augmentation": resolved_params.get("subject_reference_noise_augmentation"),
                "crop": resolved_params.get("subject_reference_crop", ""),
            },
            "plate_seed": {
                "active": minimal_surreal_plate_seed_active(spec=spec, style=style, params=resolved_params),
                "source_path": (
                    resolved_params.get("subject_reference_seed_rgba_path", "")
                    if minimal_surreal_plate_seed_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "preview_path": (
                    resolved_params.get("subject_reference_preview_path", "")
                    if minimal_surreal_plate_seed_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "soft_mask_path": (
                    resolved_params.get("subject_reference_soft_mask_path", "")
                    if minimal_surreal_plate_seed_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "runtime_image": (
                    resolved_params.get("subject_reference_runtime_image", "")
                    if minimal_surreal_plate_seed_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "staged_input_path": "",
                "draft_denoise": (
                    resolved_params.get("draft_plate_seed_denoise")
                    if minimal_surreal_plate_seed_active(spec=spec, style=style, params=resolved_params)
                    else None
                ),
            },
            "composition_control": {
                "active": minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=resolved_params),
                "mode": (
                    resolved_params.get("composition_control_mode", "")
                    if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "preview_path": (
                    resolved_params.get("subject_reference_preview_path", "")
                    if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "vision_ref_path": (
                    resolved_params.get("subject_reference_vision_ref_path", "")
                    if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "layout_mask_path": (
                    resolved_params.get("subject_reference_layout_mask_path", "")
                    if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "runtime_image": (
                    resolved_params.get("subject_reference_runtime_image", "")
                    if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "runtime_mask": (
                    resolved_params.get("subject_reference_runtime_mask", "")
                    if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=resolved_params)
                    else ""
                ),
                "staged_input_path": "",
                "staged_mask_input_path": "",
                "leakage_check_enabled": minimal_surreal_full_frame_composition_active(
                    spec=spec,
                    style=style,
                    params=resolved_params,
                ),
            },
            "midjourney_package": {
                "active": midjourney_package_shot is not None,
                "package_manifest_path": (
                    resolved_params.get("midjourney_package_manifest_path", "")
                    if midjourney_package_shot is not None
                    else ""
                ),
                "package_id": (
                    resolved_params.get("midjourney_package_id", "")
                    if midjourney_package_shot is not None
                    else ""
                ),
                "shot_id": (
                    str(params.get("midjourney_shot_id", "")).strip()
                    if midjourney_package_shot is not None
                    else ""
                ),
                "reference_files": (
                    copy.deepcopy(resolved_params.get("midjourney_reference_files", []))
                    if midjourney_package_shot is not None
                    else []
                ),
                "reference_grid_path": (
                    resolved_params.get("subject_reference_runtime_image", "")
                    if midjourney_package_shot is not None
                    else ""
                ),
                "prompt_doc_path": (
                    resolved_params.get("midjourney_prompt_doc_path", "")
                    if midjourney_package_shot is not None
                    else ""
                ),
                "references_manifest_path": (
                    resolved_params.get("midjourney_references_manifest_path", "")
                    if midjourney_package_shot is not None
                    else ""
                ),
                "prompt_text": (
                    resolved_params.get("midjourney_package_prompt_text", "")
                    if midjourney_package_shot is not None
                    else ""
                ),
                "negative_terms": (
                    copy.deepcopy(resolved_params.get("midjourney_package_negative_terms", []))
                    if midjourney_package_shot is not None
                    else []
                ),
                "adapter": (
                    {
                        "active": True,
                        "adapter_manifest_path": resolved_params.get("midjourney_adapter_manifest_path", ""),
                        "grid_layout_template": resolved_params.get("midjourney_adapter_grid_layout_template", ""),
                        "included_reference_indices": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_included_reference_indices", [])
                        ),
                        "reference_crops": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_reference_crops", {})
                        ),
                        "prompt_adapter_append": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_prompt_append", [])
                        ),
                        "negative_adapter_terms": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_negative_terms", [])
                        ),
                        "draft_visual_softpass": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_draft_visual_softpass", {})
                        ),
                        "steer_target": resolved_params.get("midjourney_adapter_steer_target", ""),
                        "steer_keep_traits": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_steer_keep_traits", [])
                        ),
                        "steer_avoid_traits": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_steer_avoid_traits", [])
                        ),
                        "ranking_bias_tags": copy.deepcopy(
                            resolved_params.get("midjourney_adapter_ranking_bias_tags", [])
                        ),
                    }
                    if midjourney_package_adapter is not None
                    else {"active": False}
                ),
            },
            "palette_lock": {
                "active": bool(resolved_params.get("palette_lock_active")),
                "accent_box": copy.deepcopy(resolved_params.get("palette_lock_accent_box", [])),
            },
            "spatial_mask": {
                "active": bool(resolved_params.get("spatial_mask_active")),
                "allow_box": copy.deepcopy(resolved_params.get("spatial_mask_allow_box", [])),
                "exclusion_boxes": copy.deepcopy(resolved_params.get("spatial_mask_exclusion_boxes", [])),
            },
            "full_model": {
                "unet": resolved_params["full_unet_name"],
                "vae": resolved_params["full_vae_name"],
                "text_encoder_primary": resolved_params["full_text_encoder_primary"],
                "text_encoder_secondary": resolved_params["full_text_encoder_secondary"],
                "weight_dtype": resolved_params["full_weight_dtype"],
            },
            "upscale_model": {
                "name": resolved_params["upscale_model_name"],
                "post_scale_factor": resolved_params["upscale_factor"],
                "post_scale_method": resolved_params["upscale_method"],
            },
            "typography": {
                "enabled": bool(typography_sidecar[1]["enabled"]) if typography_sidecar else False,
                "mode": str(typography_sidecar[1]["mode"]) if typography_sidecar else "",
                "artifact_type": str(typography_sidecar[1]["artifact_type"]) if typography_sidecar else "",
                "application_phase": str(typography_sidecar[1]["application_phase"]) if typography_sidecar else "",
                "apply_stage": (
                    str(typography_sidecar[1]["source"].get("legacy_apply_stage", ""))
                    if typography_sidecar
                    else ""
                ),
                "zone_count": len(typography_sidecar[1]["zones"]) if typography_sidecar else 0,
                "config_path": (
                    str(typography_sidecar[0].relative_to(self.repo_root)) if typography_sidecar else ""
                ),
            },
            "source_text_repair": {
                "enabled": bool(repair_policy[1]["enabled"]) if repair_policy else False,
                "application_stage": str(repair_policy[1]["application_stage"]) if repair_policy else "",
                "surface_scope": str(repair_policy[1]["surface_scope"]) if repair_policy else "",
                "llm_backend": str(repair_policy[1]["llm_backend"]) if repair_policy else "",
                "llm_model": str(repair_policy[1]["llm_model"]) if repair_policy else "",
                "allow_repaired_text_outside_typography_zones": (
                    bool(repair_policy[1]["allow_repaired_text_outside_typography_zones"])
                    if repair_policy
                    else False
                ),
                "ambiguous_environmental_fallback_action": (
                    str(repair_policy[1]["ambiguous_environmental_fallback_action"])
                    if repair_policy
                    else ""
                ),
                "post_final_cleanup": (
                    dict(repair_policy[1]["post_final_cleanup"])
                    if repair_policy
                    else dict(REPAIR_POST_FINAL_CLEANUP_DEFAULTS)
                ),
                "max_regions": int(repair_policy[1]["max_regions"]) if repair_policy else 0,
                "config_path": str(repair_policy[0].relative_to(self.repo_root)) if repair_policy else "",
            },
            "pipeline_strategy": pipeline_strategy,
            "prompt_fragments": (
                render_template(copy.deepcopy(prompt_fragments), context)
                if prompt_fragments is not None
                else {}
            ),
            "stage_requirements": stage_requirements,
            "dependency_report": dependency_report,
            "warnings": warnings,
        }

        if write_generated:
            write_json(generated_workflow_path, workflow)
            write_json(generated_prompt_path, prompt)
            write_json(generated_manifest_path, manifest)

        return BuildResult(
            spec_path=spec_path,
            family=spec["family"],
            preset=spec["preset"],
            base_preset=base_preset,
            stage=resolved_params["stage"],
            generated_workflow_path=generated_workflow_path,
            generated_prompt_path=generated_prompt_path,
            generated_manifest_path=generated_manifest_path,
            sync_target_path=sync_target_path,
            workflow=workflow,
            prompt=prompt,
            manifest=manifest,
            warnings=warnings,
            params=resolved_params,
        )

    def dependency_report(
        self,
        spec: dict[str, Any],
        style: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        warnings: list[str] = []
        assets: list[dict[str, Any]] = []

        def add_asset(kind: str, path: Path | None, required: bool, note: str = "") -> None:
            exists = bool(path and path.exists())
            assets.append(
                {
                    "kind": kind,
                    "path": str(path) if path is not None else "",
                    "required": required,
                    "present": exists,
                    "note": note,
                }
            )
            if required and not exists:
                warnings.append(f"Missing required asset for runtime: {kind} -> {path}")
            elif not required and path is not None and not exists:
                warnings.append(f"Optional quality asset missing: {kind} -> {path}")

        fragment = self.load_fragment(str(spec["base_fragment"]))
        nodes_by_key = {str(node.get("key", "")): copy.deepcopy(node) for node in fragment["nodes"]}
        for override in spec["nodes"]:
            key = str(override.get("key", ""))
            if key in nodes_by_key:
                nodes_by_key[key] = deep_merge(nodes_by_key[key], override)
            elif key:
                nodes_by_key[key] = copy.deepcopy(override)
        if self.nodes_require_checkpoint_loader(nodes_by_key.values()):
            checkpoint_name = str(params.get("checkpoint", "")).strip()
            checkpoint_path = self.models_root / "checkpoints" / checkpoint_name if checkpoint_name else None
            add_asset("checkpoint", checkpoint_path, required=True)

        reference_board_dir = self.resolve_reference_board_dir(params["reference_board_dir"])
        reference_root = reference_board_dir.parent if reference_board_dir.name == "board" else reference_board_dir
        docs_dir = reference_root / "docs"
        textures_dir = reference_root / "textures"
        board_files = self.list_files(reference_board_dir, IMAGE_SUFFIXES)
        docs_files = self.list_files(docs_dir)
        texture_files = self.list_files(textures_dir, IMAGE_SUFFIXES)

        add_asset("reference_board_dir", reference_board_dir, required=False, note="Curated episode board")
        add_asset("reference_docs_dir", docs_dir, required=False, note="Supporting documents")
        add_asset("reference_textures_dir", textures_dir, required=False, note="Material and texture references")

        if reference_board_dir.exists() and len(board_files) < 6:
            warnings.append(
                f"Reference board {reference_board_dir} only has {len(board_files)} file(s); target 6-12 references."
            )

        stage = str(params["stage"])
        base_fragment = str(spec.get("base_fragment", "")).strip()
        full_flux_runtime = stage == "refine_img2img" or (
            stage == "draft_txt2img" and base_fragment in FULL_FLUX_DRAFT_FRAGMENTS
        )
        if stage in {"refine_img2img", "repair_source_text", "final_upscale"}:
            source_image_path = self.resolve_output_reference(params["source_image"])
            add_asset("source_image", source_image_path, required=False, note="Source image for downstream stage")
        if style_uses_subject_reference_conditioning(style) and stage in SUBJECT_REFERENCE_REQUIRED_STAGES:
            if minimal_surreal_midjourney_package_grid_active(spec=spec, style=style, params=params):
                package_shot = self.resolve_midjourney_package_shot(params)
                package_manifest_path = package_shot.package_manifest_path
                add_asset(
                    "midjourney_package_manifest",
                    package_manifest_path,
                    required=True,
                    note="MidJourney source package manifest",
                )
                adapter = self.resolve_midjourney_package_adapter(params, shot=package_shot)
                if adapter is not None:
                    add_asset(
                        "midjourney_adapter_manifest",
                        adapter.adapter_path,
                        required=True,
                        note="MidJourney package adapter manifest",
                    )
            else:
                raw_subject_reference = str(params.get("subject_reference_image", "")).strip()
                subject_reference_path = (
                    self.resolve_subject_reference_path(raw_subject_reference) if raw_subject_reference else None
                )
                add_asset(
                    "subject_reference_image",
                    subject_reference_path,
                    required=True,
                    note="Hero subject reference image",
                )
            clip_vision_model_name = str(params.get("subject_reference_clip_vision_model", "")).strip()
            clip_vision_model_path = (
                self.models_root / "clip_vision" / clip_vision_model_name
                if clip_vision_model_name
                else None
            )
            add_asset(
                "clip_vision_model",
                clip_vision_model_path,
                required=True,
                note="CLIP vision model for subject reference conditioning",
            )
            if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=params):
                layout_mask_path = str(params.get("subject_reference_layout_mask_path", "")).strip()
                add_asset(
                    "subject_reference_layout_mask",
                    self.resolve_subject_reference_path(layout_mask_path) if layout_mask_path else None,
                    required=True,
                    note="Full-canvas layout mask for hidden composition control",
                )

        if full_flux_runtime:
            add_asset(
                "full_flux_unet",
                self.models_root / "diffusion_models" / str(params["full_unet_name"]),
                required=True,
                note="Full FLUX diffusion model",
            )
            add_asset(
                "full_flux_vae",
                self.models_root / "vae" / str(params["full_vae_name"]),
                required=True,
                note="Full FLUX VAE",
            )
            add_asset(
                "full_flux_text_encoder_primary",
                self.models_root / "text_encoders" / str(params["full_text_encoder_primary"]),
                required=True,
                note="Primary FLUX text encoder",
            )
            add_asset(
                "full_flux_text_encoder_secondary",
                self.models_root / "text_encoders" / str(params["full_text_encoder_secondary"]),
                required=True,
                note="Secondary FLUX text encoder",
            )

        if stage == "final_upscale":
            add_asset(
                "upscale_model",
                self.models_root / "upscale_models" / str(params["upscale_model_name"]),
                required=False,
                note="Canonical final-deliverable upscaler",
            )

        return {
            "reference": {
                "board_dir": str(reference_board_dir),
                "board_files": len(board_files),
                "docs_files": len(docs_files),
                "texture_files": len(texture_files),
            },
            "assets": assets,
            "warnings": warnings,
        }

    def stage_requirements(
        self,
        spec: dict[str, Any],
        style: dict[str, Any],
        params: dict[str, Any],
        dependency_report: dict[str, Any],
    ) -> dict[str, Any]:
        stage = str(params["stage"])
        base_fragment = str(spec.get("base_fragment", "")).strip()
        full_flux_runtime = stage == "refine_img2img" or (
            stage == "draft_txt2img" and base_fragment in FULL_FLUX_DRAFT_FRAGMENTS
        )
        runtime_required_kinds = ["checkpoint"]
        if stage in {"refine_img2img", "repair_source_text", "final_upscale"}:
            runtime_required_kinds.append("source_image")
        if full_flux_runtime:
            runtime_required_kinds.extend(
                [
                    "full_flux_unet",
                    "full_flux_vae",
                    "full_flux_text_encoder_primary",
                    "full_flux_text_encoder_secondary",
                ]
            )
        if style_uses_subject_reference_conditioning(style) and stage in SUBJECT_REFERENCE_REQUIRED_STAGES:
            runtime_required_kinds.append("clip_vision_model")
            if minimal_surreal_midjourney_package_grid_active(spec=spec, style=style, params=params):
                runtime_required_kinds.append("midjourney_package_manifest")
                if str(params.get("midjourney_adapter_path", "")).strip():
                    runtime_required_kinds.append("midjourney_adapter_manifest")
            else:
                runtime_required_kinds.append("subject_reference_image")
            if minimal_surreal_full_frame_composition_active(spec=spec, style=style, params=params):
                runtime_required_kinds.append("subject_reference_layout_mask")
        if stage == "final_upscale":
            runtime_required_kinds.append("upscale_model")

        return {
            "allow_batch": stage == "draft_txt2img",
            "runtime_required_asset_kinds": runtime_required_kinds,
            "requires_source_image": stage in {"refine_img2img", "repair_source_text", "final_upscale"},
            "upstream_stage": UPSTREAM_STAGE.get(stage),
            "missing_runtime_assets": [
                asset["kind"]
                for asset in dependency_report["assets"]
                if asset["kind"] in runtime_required_kinds and not asset["present"]
            ],
        }

    def resolve_reference_board_dir(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path
        return self.repo_root / path

    def resolve_reference_notes_path(self, raw_board_path: str) -> Path:
        reference_board_dir = self.resolve_reference_board_dir(raw_board_path)
        reference_root = reference_board_dir.parent if reference_board_dir.name == "board" else reference_board_dir
        return reference_root / "notes.md"

    def resolve_subject_reference_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path.resolve()
        return (self.repo_root / path).resolve()

    def resolve_output_reference(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path
        return self.comfy_output_dir / path

    @staticmethod
    def list_files(path: Path, suffixes: set[str] | None = None) -> list[Path]:
        if not path.exists():
            return []
        files = [child for child in path.iterdir() if child.is_file()]
        if suffixes is None:
            return sorted(files)
        return sorted(child for child in files if child.suffix.lower() in suffixes)

    def validate_active_semantics(
        self,
        spec_path: Path,
        spec: dict[str, Any],
        style: dict[str, Any],
        params: dict[str, Any],
    ) -> None:
        if not self.is_active_family(spec["family"]):
            return

        prompt = str(params["positive_prompt"]).strip()
        prompt_lower = prompt.lower()
        raw_prompt_source = str(spec.get("params", {}).get("positive_prompt", "")).strip()
        midjourney_package_mode = minimal_surreal_midjourney_package_grid_active(
            spec=spec,
            style=style,
            params=params,
        )
        if spec.get("prompt_fragments") is not None and not midjourney_package_mode:
            raw_prompt_source = (
                raw_prompt_source
                + " "
                + json.dumps(spec.get("prompt_fragments"), ensure_ascii=True, sort_keys=True)
            ).strip()
        raw_prompt_lower = raw_prompt_source.lower()
        negative_lower = str(params["negative_prompt"]).strip().lower()
        minimal_surreal_mode = style_uses_minimal_surreal_contract(style)
        subject_reference_mode = style_uses_subject_reference_conditioning(style)
        plate_seed_mode = minimal_surreal_plate_seed_active(spec=spec, style=style, params=params)
        prompt_guardrails = prompt_guardrails_for(
            load_guardrail_policy(self.repo_root),
            str(spec["family"]),
            str(spec["preset"]),
        )
        prompt_fragments = spec.get("prompt_fragments")
        if isinstance(prompt_fragments, dict):
            support_limit = PROMPT_SUPPORT_LIMITS.get(str(spec["family"]))
            support_fragments = unique_string_list(prompt_fragments.get("support_fragments"))
            if support_limit is not None and len(support_fragments) > support_limit:
                raise WorkflowError(
                    f"{spec_path}: {spec['family']} prompt_fragments.support_fragments is capped at "
                    f"{support_limit} items."
                )

        for phrase, reason in ACTIVE_PROMPT_BANLIST.items():
            if phrase in prompt_lower:
                raise WorkflowError(
                    f"{spec_path}: active workflow contains banned {reason} phrase {phrase!r}."
                )
        for phrase, reason in prompt_guardrails["banned_phrases"].items():
            if phrase.lower() in prompt_lower:
                raise WorkflowError(
                    f"{spec_path}: active workflow contains banned {reason} phrase {phrase!r}."
                )

        if not negative_lower:
            raise WorkflowError(
                f"{spec_path}: active workflows require a non-empty negative_prompt with zero-letter clauses."
            )
        missing_negative_phrases = [
            phrase for phrase in ACTIVE_REQUIRED_NEGATIVE_PHRASES if phrase not in negative_lower
        ]
        if missing_negative_phrases:
            missing_text = ", ".join(repr(phrase) for phrase in missing_negative_phrases[:5])
            raise WorkflowError(
                f"{spec_path}: active negative_prompt is missing required zero-letter phrases: "
                f"{missing_text}."
            )
        for phrase, reason in ACTIVE_TEXT_SIGNAGE_BANLIST.items():
            if phrase_matches_text(prompt_lower, phrase):
                raise WorkflowError(
                    f"{spec_path}: active workflow contains banned {reason} phrase {phrase!r}."
                )
        for phrase, reason in prompt_guardrails["raw_prompt_banned_phrases"].items():
            if phrase.lower() in raw_prompt_lower:
                raise WorkflowError(
                    f"{spec_path}: active workflow contains banned {reason} phrase {phrase!r}."
                )
        required_fragment = FINAL_UPSCALE_REQUIRED_BASE_FRAGMENTS.get(str(spec["family"]))
        if required_fragment and str(params.get("stage", "")).strip() == "final_upscale":
            if str(spec.get("base_fragment", "")).strip() != required_fragment:
                raise WorkflowError(
                    f"{spec_path}: {spec['family']} final_upscale must use "
                    f"{required_fragment!r}, not {spec.get('base_fragment')!r}."
                )

        if not minimal_surreal_mode:
            collage_hits = [marker for marker in COLLAGE_REQUIRED_MARKERS if marker in prompt_lower]
            if len(collage_hits) < 3:
                raise WorkflowError(
                    f"{spec_path}: active workflow prompt must declare at least three collage markers; "
                    f"found {len(collage_hits)}."
                )
        else:
            missing_minimal_surreal = [
                phrase
                for phrase in MINIMAL_SURREAL_REQUIRED_PROMPT_PHRASES
                if phrase not in prompt_lower
            ]
            if missing_minimal_surreal:
                missing_text = ", ".join(repr(phrase) for phrase in missing_minimal_surreal)
                raise WorkflowError(
                    f"{spec_path}: minimal-surreal prompt is missing required contract phrase(s): "
                    f"{missing_text}."
                )

        if str(params["style_profile"]) != str(style["name"]):
            raise WorkflowError(
                f"{spec_path}: params.style_profile {params['style_profile']!r} must match style profile "
                f"{style['name']!r}."
            )

        required_phrases = list(ACTIVE_FAMILY_PROMPT_REQUIREMENTS.get(spec["family"], ()))
        for phrase in prompt_guardrails["required_phrases"]:
            if phrase not in required_phrases:
                required_phrases.append(phrase)
        if minimal_surreal_mode:
            required_phrases = [phrase for phrase in required_phrases if phrase != "poster montage"]
        if midjourney_package_mode:
            required_phrases = [
                phrase
                for phrase in required_phrases
                if phrase not in {"anchor fragment", "layered support fragments", "historical anchor", "surreal breach"}
            ]
        missing_required_phrases = [phrase for phrase in required_phrases if phrase not in prompt_lower]
        if missing_required_phrases:
            missing_text = ", ".join(repr(phrase) for phrase in missing_required_phrases)
            raise WorkflowError(
                f"{spec_path}: active workflow prompt is missing required framing phrase(s): "
                f"{missing_text}."
            )

        if str(params["safe_zone"]).strip().lower() == "none":
            raise WorkflowError(f"{spec_path}: active workflows must preserve a non-'none' safe_zone.")
        if not str(params["safe_zone_intent"]).strip():
            raise WorkflowError(f"{spec_path}: safe_zone_intent must be non-empty for active workflows.")
        if str(params["human_presence"]).strip().lower() not in {"none", "traces-only", "operators-allowed"}:
            raise WorkflowError(
                f"{spec_path}: human_presence must be one of none, traces-only, operators-allowed."
            )
        if str(params["temperature"]).strip().lower() not in MINIMAL_SURREAL_ALLOWED_TEMPERATURES:
            raise WorkflowError(f"{spec_path}: temperature must be one of restrained, tense, bold.")
        if minimal_surreal_mode:
            if "caption_safe_defaults" not in style:
                raise WorkflowError(f"{spec_path}: minimal-surreal style profile is missing caption_safe_defaults.")
            if "subject_reference_defaults" not in style:
                raise WorkflowError(
                    f"{spec_path}: minimal-surreal style profile is missing subject_reference_defaults."
                )
            if str(spec["family"]) in MINIMAL_SURREAL_PORTRAIT_FAMILIES and "plate_seed_defaults" not in style:
                raise WorkflowError(
                    f"{spec_path}: minimal-surreal style profile is missing plate_seed_defaults."
                )
            validate_caption_safe_payload(
                spec_path,
                "style.caption_safe_defaults",
                style["caption_safe_defaults"],
            )
            validate_caption_safe_payload(
                spec_path,
                "params.caption_safe_zone",
                params.get("caption_safe_zone"),
            )
            if spec["family"] == "shorts_scene_plate":
                if not str(params.get("beat_id", "")).strip():
                    raise WorkflowError(f"{spec_path}: shorts_scene_plate presets must declare beat_id.")
                if not str(params.get("historical_anchor", "")).strip():
                    raise WorkflowError(f"{spec_path}: shorts_scene_plate presets must declare historical_anchor.")
                if not str(params.get("surreal_breach", "")).strip():
                    raise WorkflowError(f"{spec_path}: shorts_scene_plate presets must declare surreal_breach.")
        if subject_reference_mode and str(params.get("stage", "")).strip() in SUBJECT_REFERENCE_REQUIRED_STAGES:
            normalized_subject_reference = str(params.get("subject_reference_image", "")).strip().replace("\\", "/")
            if midjourney_package_mode:
                if not str(params.get("midjourney_package_path", "")).strip():
                    raise WorkflowError(
                        f"{spec_path}: reference_mode=midjourney_package_grid requires midjourney_package_path."
                    )
                if not str(params.get("midjourney_shot_id", "")).strip():
                    raise WorkflowError(
                        f"{spec_path}: reference_mode=midjourney_package_grid requires midjourney_shot_id."
                    )
                if str(params.get("midjourney_adapter_path", "")).strip():
                    package_shot = self.resolve_midjourney_package_shot(params)
                    self.resolve_midjourney_package_adapter(params, shot=package_shot)
            else:
                raw_subject_reference = str(params.get("subject_reference_image", "")).strip()
                if not raw_subject_reference:
                    raise WorkflowError(
                        f"{spec_path}: minimal-surreal {params['stage']} presets must declare subject_reference_image."
                    )
                if "/selects/" in normalized_subject_reference or normalized_subject_reference.startswith("selects/"):
                    raise WorkflowError(
                        f"{spec_path}: minimal-surreal subject references must point at generated documentary "
                        "subject_reference_plates, not stylized selects."
                    )
            try:
                subject_strength = float(params.get("subject_reference_strength", 0.0))
            except (TypeError, ValueError) as exc:
                raise WorkflowError(f"{spec_path}: subject_reference_strength must be numeric.") from exc
            if subject_strength <= 0.0:
                raise WorkflowError(f"{spec_path}: subject_reference_strength must be > 0.")
            try:
                subject_noise = float(params.get("subject_reference_noise_augmentation", -1.0))
            except (TypeError, ValueError) as exc:
                raise WorkflowError(
                    f"{spec_path}: subject_reference_noise_augmentation must be numeric."
                ) from exc
            if subject_noise < 0.0 or subject_noise > 1.0:
                raise WorkflowError(
                    f"{spec_path}: subject_reference_noise_augmentation must stay within 0.0-1.0."
                )
            subject_crop = str(params.get("subject_reference_crop", "")).strip().lower()
            if subject_crop not in SUBJECT_REFERENCE_ALLOWED_CROPS:
                raise WorkflowError(
                    f"{spec_path}: subject_reference_crop must be one of "
                    f"{', '.join(sorted(SUBJECT_REFERENCE_ALLOWED_CROPS))}."
                )
            if not midjourney_package_mode:
                if "preserve recognizable silhouette and major geometry of the reference subject" not in prompt_lower:
                    raise WorkflowError(
                        f"{spec_path}: minimal-surreal subject-reference prompting must preserve recognizable silhouette."
                    )
                if "stylize surface and atmosphere rather than identity" not in prompt_lower:
                    raise WorkflowError(
                        f"{spec_path}: minimal-surreal subject-reference prompting must preserve identity over surface."
                    )
            if not midjourney_package_mode and "subject_reference_plates/generated/" in normalized_subject_reference:
                if MINIMAL_SURREAL_REFERENCE_PLATE_PROMPT_PHRASE not in prompt_lower:
                    raise WorkflowError(
                        f"{spec_path}: minimal-surreal documentary plate prompting must preserve dominant subject "
                        "count and placement bias."
                    )
        if plate_seed_mode:
            try:
                draft_plate_seed_denoise = float(params.get("draft_plate_seed_denoise", 0.0))
            except (TypeError, ValueError) as exc:
                raise WorkflowError(f"{spec_path}: draft_plate_seed_denoise must be numeric.") from exc
            if draft_plate_seed_denoise <= 0.0 or draft_plate_seed_denoise > 1.0:
                raise WorkflowError(f"{spec_path}: draft_plate_seed_denoise must stay within 0.0-1.0.")

        if spec["family"] in PACKAGING_FAMILIES:
            if str(params["human_presence"]).strip().lower() != "traces-only":
                raise WorkflowError(
                    f"{spec_path}: packaging workflows are locked to traces-only human presence."
                )
            if not str(params.get("signal_anchor", "")).strip():
                raise WorkflowError(f"{spec_path}: packaging workflows must declare a non-empty signal_anchor.")
            reference_board_dir = self.resolve_reference_board_dir(params["reference_board_dir"])
            board_files = self.list_files(reference_board_dir, IMAGE_SUFFIXES)
            if len(board_files) < 6:
                raise WorkflowError(
                    f"{spec_path}: packaging workflows require 6-12 curated board references before rendering; "
                    f"found {len(board_files)} in {reference_board_dir}."
                )

    def compile_native_workflow(
        self,
        spec: dict[str, Any],
        fragment: dict[str, Any],
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
    ) -> dict[str, Any]:
        node_id_map: dict[str, int] = {}
        compiled_nodes: list[dict[str, Any]] = []
        outputs_meta: dict[str, dict[str, tuple[int, int, str]]] = {}
        inputs_meta: dict[str, dict[str, tuple[int, str]]] = {}

        for index, node in enumerate(nodes, start=1):
            key = node["key"]
            node_id = index
            node_id_map[key] = node_id

            compiled_inputs: list[dict[str, Any]] = []
            input_name_map: dict[str, tuple[int, str]] = {}
            for input_index, input_def in enumerate(node.get("inputs", [])):
                compiled_input = copy.deepcopy(input_def)
                compiled_input.pop("source", None)
                compiled_input["link"] = None
                compiled_inputs.append(compiled_input)
                input_name_map[input_def["name"]] = (input_index, input_def.get("type", ""))
            inputs_meta[key] = input_name_map

            compiled_outputs: list[dict[str, Any]] = []
            output_name_map: dict[str, tuple[int, int, str]] = {}
            for output_index, output_def in enumerate(node.get("outputs", [])):
                compiled_output = copy.deepcopy(output_def)
                slot_index = int(compiled_output.get("slot_index", output_index))
                compiled_output["slot_index"] = slot_index
                compiled_output["links"] = []
                compiled_outputs.append(compiled_output)
                output_name_map[output_def["name"]] = (
                    output_index,
                    slot_index,
                    output_def.get("type", ""),
                )
            outputs_meta[key] = output_name_map

            widget_names = node.get("widget_names", [])
            widgets = node.get("widgets", {})
            widgets_values = [
                self.normalize_widget_value(node["type"], name, widgets[name]) for name in widget_names
            ]

            compiled_node = {
                "id": node_id,
                "type": node["type"],
                "pos": node.get("pos", [0, 0]),
                "size": node.get("size", [315, 80]),
                "flags": node.get("flags", {}),
                "order": node.get("order", index - 1),
                "mode": node.get("mode", 0),
                "inputs": compiled_inputs,
                "outputs": compiled_outputs,
                "properties": node.get("properties", {}),
                "widgets_values": widgets_values,
            }
            if node.get("title"):
                compiled_node["title"] = node["title"]
            if node.get("color") is not None:
                compiled_node["color"] = node["color"]
            if node.get("bgcolor") is not None:
                compiled_node["bgcolor"] = node["bgcolor"]
            compiled_nodes.append(compiled_node)

        compiled_links: list[list[Any]] = []
        for link_id, link in enumerate(links, start=1):
            source_key, source_output = self.parse_endpoint(link["from"])
            target_key, target_input = self.parse_endpoint(link["to"])

            if source_key not in outputs_meta:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: link references unknown source node {source_key!r}."
                )
            if target_key not in inputs_meta:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: link references unknown target node {target_key!r}."
                )
            if source_output not in outputs_meta[source_key]:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: link references unknown output {link['from']!r}."
                )
            if target_input not in inputs_meta[target_key]:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: link references unknown input {link['to']!r}."
                )

            source_output_index, source_slot_index, source_type = outputs_meta[source_key][source_output]
            target_input_index, target_type = inputs_meta[target_key][target_input]

            expected_link_type = link.get("type", source_type)
            if source_type and expected_link_type != source_type:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: link {link['from']} -> {link['to']} "
                    f"declares type {expected_link_type!r} but source output type is {source_type!r}."
                )
            if source_type and target_type and source_type != target_type:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: type mismatch for link {link['from']} -> {link['to']} "
                    f"({source_type!r} vs {target_type!r})."
                )

            compiled_nodes[node_id_map[source_key] - 1]["outputs"][source_output_index]["links"].append(link_id)
            compiled_nodes[node_id_map[target_key] - 1]["inputs"][target_input_index]["link"] = link_id
            compiled_links.append(
                [
                    link_id,
                    node_id_map[source_key],
                    source_slot_index,
                    node_id_map[target_key],
                    target_input_index,
                    expected_link_type or target_type,
                ]
            )

        workflow_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"ce-workflow:{spec['family']}:{spec['preset']}"))
        meta = fragment.get("meta", {})
        return {
            "id": workflow_id,
            "revision": meta.get("revision", 0),
            "last_node_id": len(compiled_nodes),
            "last_link_id": len(compiled_links),
            "nodes": compiled_nodes,
            "links": compiled_links,
            "groups": meta.get("groups", []),
            "config": meta.get("config", {}),
            "extra": meta.get("extra", {}),
            "version": meta.get("version", 0.4),
        }

    def compile_api_prompt(
        self,
        spec: dict[str, Any],
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
    ) -> dict[str, Any]:
        node_id_map: dict[str, str] = {}
        outputs_meta: dict[str, dict[str, int]] = {}
        prompt: dict[str, Any] = {}

        executable_nodes = [node for node in nodes if node["type"] not in NON_API_NODE_TYPES]
        for index, node in enumerate(executable_nodes, start=1):
            key = node["key"]
            node_id = str(index)
            node_id_map[key] = node_id

            prompt_inputs: dict[str, Any] = {}
            widgets = node.get("widgets", {})
            for input_def in node.get("inputs", []):
                input_name = input_def["name"]
                widget_name = input_def.get("widget", {}).get("name", input_name)
                if widget_name in widgets:
                    prompt_inputs[input_name] = self.normalize_widget_value(
                        node["type"],
                        widget_name,
                        copy.deepcopy(widgets[widget_name]),
                    )

            outputs_meta[key] = {
                output_def["name"]: int(output_def.get("slot_index", output_index))
                for output_index, output_def in enumerate(node.get("outputs", []))
            }
            prompt[node_id] = {
                "inputs": prompt_inputs,
                "class_type": node["type"],
                "_meta": {
                    "title": node.get("title", node["type"]),
                },
            }

        for link in links:
            source_key, source_output = self.parse_endpoint(link["from"])
            target_key, target_input = self.parse_endpoint(link["to"])

            if source_key not in node_id_map:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: API prompt link references "
                    f"non-executable source node {source_key!r}."
                )
            if target_key not in node_id_map:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: API prompt link references "
                    f"non-executable target node {target_key!r}."
                )
            if source_output not in outputs_meta[source_key]:
                raise WorkflowError(
                    f"{spec['family']}/{spec['preset']}: API prompt link references unknown output {link['from']!r}."
                )

            prompt[node_id_map[target_key]]["inputs"][target_input] = [
                node_id_map[source_key],
                outputs_meta[source_key][source_output],
            ]

        return prompt

    def matching_output_files(self, filename_prefix: str) -> list[Path]:
        prefix_path = self.comfy_output_dir / filename_prefix
        parent = prefix_path.parent
        stem = prefix_path.name
        if not parent.exists():
            return []
        return sorted(
            [path for path in parent.glob(f"{stem}_*.*") if path.is_file()],
            key=lambda path: path.stat().st_mtime,
        )

    def build_compare_report(
        self,
        target_name: str,
        results: list[BuildResult],
    ) -> Path:
        report_items = []
        for result in results:
            outputs = self.matching_output_files(result.params["filename_prefix"])
            latest_output = outputs[-1] if outputs else None
            missing_assets = [
                asset for asset in result.manifest["dependency_report"]["assets"] if not asset["present"]
            ]
            report_items.append(
                {
                    "family": result.family,
                    "preset": result.preset,
                    "base_preset": result.base_preset,
                    "stage": result.stage,
                    "manifest_path": str(result.generated_manifest_path),
                    "prompt_path": str(result.generated_prompt_path),
                    "sync_target_path": str(result.sync_target_path),
                    "filename_prefix": result.params["filename_prefix"],
                    "output_count": len(outputs),
                    "latest_output": str(latest_output) if latest_output else "",
                    "latest_output_mtime": (
                        datetime.fromtimestamp(latest_output.stat().st_mtime, tz=timezone.utc)
                        .replace(microsecond=0)
                        .isoformat()
                        .replace("+00:00", "Z")
                        if latest_output
                        else ""
                    ),
                    "seed": result.params["seed"],
                    "selected_seed": result.params["selected_seed"],
                    "variant_count": result.params["variant_count"],
                    "reference_board_dir": result.params["reference_board_dir"],
                    "style_profile": result.params.get("style_profile", ""),
                    "temperature": result.params.get("temperature", ""),
                    "palette_policy": result.params.get("palette_policy", ""),
                    "accent_palette": result.params.get("accent_palette", ""),
                    "human_presence": result.params.get("human_presence", ""),
                    "safe_zone_intent": result.params.get("safe_zone_intent", ""),
                    "source_image": result.params["source_image"],
                    "refine_denoise": result.params["refine_denoise"],
                    "upscale_factor": result.params["upscale_factor"],
                    "warnings": result.warnings,
                    "missing_assets": missing_assets,
                }
            )

        report_path = self.reports_dir / f"{target_name}.compare.json"
        write_json(
            report_path,
            {
                "generated_at": utc_now_iso(),
                "target": target_name,
                "items": report_items,
            },
        )
        return report_path

    @staticmethod
    def parse_endpoint(endpoint: str) -> tuple[str, str]:
        if "." not in endpoint:
            raise WorkflowError(f"Invalid link endpoint {endpoint!r}; expected node.port")
        node_key, port_name = endpoint.split(".", 1)
        return node_key, port_name

    @staticmethod
    def normalize_widget_value(node_type: str, widget_name: str, value: Any) -> Any:
        if widget_name != "image" or not isinstance(value, str):
            return value
        if value.endswith("[output]") or value.endswith("[input]") or value.endswith("[temp]"):
            return value
        if node_type == "LoadImageOutput":
            return f"{value} [output]"
        if node_type == "LoadImage":
            return f"{value} [input]"
        return value

    @staticmethod
    def dimension_warnings(family: str, width: int, height: int) -> list[str]:
        warnings: list[str] = []
        rule = ACTIVE_FAMILY_RULES.get(family)
        if not rule:
            return warnings
        if width <= 0 or height <= 0:
            warnings.append("Dimensions must be positive integers.")
            return warnings

        ratio = width / height
        if rule["kind"] == "landscape" and width <= height:
            warnings.append(f"{family} expects a landscape canvas; got {width}x{height}.")
        if rule["kind"] == "exact" and rule["ratio"] is not None:
            expected = rule["ratio"]
            if abs(ratio - expected) > 0.02:
                warnings.append(
                    f"{family} expects aspect ratio {expected:.4f}; got {width}x{height} ({ratio:.4f})."
                )
        return warnings


def print_result_summary(prefix: str, result: BuildResult) -> None:
    warning_suffix = ""
    if result.warnings:
        warning_suffix = f" warnings={len(result.warnings)}"
    print(
        f"{prefix} {result.family}/{result.preset} "
        f"stage={result.stage} -> {result.generated_workflow_path.relative_to(result.spec_path.parents[3])}"
        f"{warning_suffix}"
    )
    for warning in result.warnings:
        print(f"WARN  {result.family}/{result.preset}: {warning}")


def command_validate(compiler: WorkflowCompiler, args: argparse.Namespace) -> int:
    spec_paths = compiler.select_specs(args.family, args.preset)
    results = compiler.build_many(spec_paths, write_generated=False)
    for result in results:
        print_result_summary("OK   ", result)
    print(f"Validated {len(results)} workflow spec(s).")
    return 0


def command_build(compiler: WorkflowCompiler, args: argparse.Namespace) -> int:
    overrides = parse_override_values(args.overrides)
    spec_paths = compiler.select_specs(args.family, args.preset)
    results = compiler.build_many(spec_paths, write_generated=True, overrides=overrides)
    for result in results:
        print_result_summary("BUILT", result)
        print(f"INFO  prompt -> {result.generated_prompt_path}")
        print(f"INFO  manifest -> {result.generated_manifest_path}")
    print(f"Built {len(results)} workflow artifact(s).")
    return 0


def command_sync(compiler: WorkflowCompiler, args: argparse.Namespace) -> int:
    overrides = parse_override_values(args.overrides)
    spec_paths = compiler.select_specs(args.family, args.preset)
    results = compiler.build_many(spec_paths, write_generated=True, overrides=overrides)
    compiler.comfy_workflows_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        shutil.copyfile(result.generated_workflow_path, result.sync_target_path)
        print_result_summary("SYNC ", result)
        print(f"INFO  sync -> {result.sync_target_path}")
    if args.family == "all":
        for retired_target in compiler.retired_sync_targets():
            if retired_target.exists():
                retired_target.unlink()
                print(f"INFO  retired workflow removed -> {retired_target}")
    print(f"Synced {len(results)} workflow artifact(s).")
    return 0


def command_diff(compiler: WorkflowCompiler, args: argparse.Namespace) -> int:
    overrides = parse_override_values(args.overrides)
    spec_paths = compiler.select_specs(args.family, args.preset)
    results = compiler.build_many(spec_paths, write_generated=False, overrides=overrides)

    has_diff = False
    for result in results:
        generated_text = json.dumps(result.workflow, indent=2) + "\n"
        if not result.sync_target_path.exists():
            has_diff = True
            print(f"DIFF {result.family}/{result.preset}: missing sync target {result.sync_target_path}")
            continue

        live_text = result.sync_target_path.read_text(encoding="utf-8")
        if generated_text == live_text:
            print(f"OK   {result.family}/{result.preset}: in sync")
            continue

        has_diff = True
        print(f"DIFF {result.family}/{result.preset}:")
        diff_lines = difflib.unified_diff(
            live_text.splitlines(),
            generated_text.splitlines(),
            fromfile=str(result.sync_target_path),
            tofile=str(result.generated_workflow_path),
            lineterm="",
        )
        for line in diff_lines:
            print(line)
    return 1 if has_diff else 0


def command_compare(compiler: WorkflowCompiler, args: argparse.Namespace) -> int:
    overrides = parse_override_values(args.overrides)
    spec_paths = compiler.select_specs(args.family, args.preset)
    results = compiler.build_many(spec_paths, write_generated=True, overrides=overrides)

    if args.family == "all":
        target_name = "all"
    elif args.preset:
        target_name = f"{args.family}__{args.preset}"
    else:
        target_name = args.family

    report_path = compiler.build_compare_report(target_name, results)
    for result in results:
        outputs = compiler.matching_output_files(result.params["filename_prefix"])
        latest_output = outputs[-1] if outputs else None
        missing_assets = sum(
            1 for asset in result.manifest["dependency_report"]["assets"] if not asset["present"]
        )
        latest_text = str(latest_output) if latest_output else "none"
        print(
            f"COMPARE {result.family}/{result.preset} stage={result.stage} "
            f"outputs={len(outputs)} latest={latest_text} missing_assets={missing_assets}"
        )
    print(f"INFO  compare report -> {report_path}")
    return 0


def main() -> int:
    args = parse_args()
    compiler = WorkflowCompiler(
        repo_root=Path(args.repo_root),
        models_root=Path(args.models_root),
        comfy_workflows_dir=Path(args.comfy_workflows_dir),
        comfy_output_dir=Path(args.comfy_output_dir),
        references_root=Path(args.references_root),
        comfy_clip_vision_model=str(args.comfy_clip_vision_model).strip(),
    )

    try:
        if args.command == "list":
            compiler.list_workflows()
            return 0
        if args.command == "validate":
            return command_validate(compiler, args)
        if args.command == "build":
            return command_build(compiler, args)
        if args.command == "sync":
            return command_sync(compiler, args)
        if args.command == "diff":
            return command_diff(compiler, args)
        if args.command == "compare":
            return command_compare(compiler, args)
        raise WorkflowError(f"Unknown command {args.command!r}")
    except WorkflowError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
