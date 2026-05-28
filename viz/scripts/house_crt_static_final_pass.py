#!/usr/bin/env python3
"""Rebuild active final Shorts with house CRT and Challenger signal cuts.

This pass intentionally starts from no-caption proof/provenance sources, applies
the motion-only treatment, then burns existing final-export ASS captions and
remuxes the prior approved final audio stream. Existing finals are read-only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import random
import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageStat


HOUSE_CRT_CONTRACT_ID = "house_crt_luma_neutral_chroma_signal_interruption_v1"
HOUSE_CRT_PROFILE_ID = "era_1980s_broadcast_crt_v1"
HOUSE_CRT_INTENSITY = "visible_but_premium"
HOUSE_CRT_TONE_POLICY = "luma_neutral_chroma_v1"
CALIBRATION_RECIPE_ID = "premium_broadcast_crt_luma_neutral_chroma_v1"
LEGACY_CALIBRATION_RECIPE_ID = CALIBRATION_RECIPE_ID
TEXTURE_RENDERER_SOURCE = "house_crt_static_final_pass.luma_neutral_chroma_filter_graph"
TEXTURE_CONSERVATIVE_CLEAN_SOURCE = "short_tool.historical_signal_conservative_clean"
VISIBLE_SCANLINE_TONE_POLICY = "luma_neutral_chroma_visible_scanline_v1"
VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID = "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1"
VISIBLE_SCANLINE_POLICY_ID = "luma_neutral_visible_scanline_modulation_v1"
VISIBLE_SCANLINE_RENDERER_SOURCE = "house_crt_static_final_pass.luma_neutral_chroma_visible_scanline_filter_graph"
VISIBLE_SCANLINE_CALIBRATION_PASS_ID = "house_crt_visible_scanline_calibration_pass_07a"
VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID = "house_crt_visible_scanline_strength_ladder_pass_07b"
VISIBLE_SCANLINE_HIGH_VISIBILITY_LADDER_PASS_ID = "house_crt_visible_scanline_high_visibility_ladder_pass_07c"
VISIBLE_SCANLINE_FULL_PASS_ID = "house_crt_clean_source_lineage_visible_scanline_first8_pass_07"
VISIBLE_SCANLINE_PERIOD_PIXELS = 4
VISIBLE_SCANLINE_BAND_PIXELS = 1
VISIBLE_SCANLINE_DELTA_RGB = 6.0
VISIBLE_SCANLINE_VISIBILITY_YAVG_MIN = 2.0
VISIBLE_SCANLINE_STRENGTH_VARIANTS = (
    {
        "scanline_strength_variant_id": "balanced_plus_y8",
        "scanline_delta_y": 8.0,
        "target_scanline_yavg_min": 17.0,
        "target_scanline_yavg_max": 19.0,
        "review_role": "likely_promotion_candidate",
    },
    {
        "scanline_strength_variant_id": "strong_crt_y10",
        "scanline_delta_y": 10.0,
        "target_scanline_yavg_min": 21.0,
        "target_scanline_yavg_max": 24.0,
        "review_role": "stronger_visible_reference",
    },
    {
        "scanline_strength_variant_id": "max_safe_y12",
        "scanline_delta_y": 12.0,
        "target_scanline_yavg_min": 25.0,
        "target_scanline_yavg_max": 29.0,
        "review_role": "diagnostic_unless_still_premium",
    },
)
VISIBLE_SCANLINE_HIGH_VISIBILITY_VARIANTS = (
    {
        "scanline_strength_variant_id": "visible_bars_y16_p8",
        "scanline_delta_y": 16.0,
        "scanline_period_pixels": 8,
        "scanline_band_pixels": 2,
        "target_scanline_yavg_min": 34.0,
        "target_scanline_yavg_max": 40.0,
        "review_role": "likely_promotion_candidate_for_readable_bars",
    },
    {
        "scanline_strength_variant_id": "assertive_bars_y20_p8",
        "scanline_delta_y": 20.0,
        "scanline_period_pixels": 8,
        "scanline_band_pixels": 2,
        "target_scanline_yavg_min": 42.0,
        "target_scanline_yavg_max": 50.0,
        "review_role": "strong_visible_reference",
    },
    {
        "scanline_strength_variant_id": "max_visible_bars_y24_p8",
        "scanline_delta_y": 24.0,
        "scanline_period_pixels": 8,
        "scanline_band_pixels": 2,
        "target_scanline_yavg_min": 50.0,
        "target_scanline_yavg_max": 60.0,
        "review_role": "diagnostic_unless_still_premium",
    },
)
VISIBLE_SCANLINE_SELECTED_STRENGTH_VARIANT_ID = "max_visible_bars_y24_p8"
LUMA_YAVG_TOLERANCE = 3.0
MAX_LUMA_CORRECTION_YAVG = 12.0
MONOCHROME_CHROMA_MAGNITUDE_MAX = 2.5
SIGNAL_INTERRUPTION_PROFILE_ID = "era_1980s_horizontal_signal_interruption_v2_randomized"
SIGNAL_INTERRUPTION_PROFILE_SOURCE = "era_1980s_horizontal_signal_interruption_v1"
SIGNAL_INTERRUPTION_STRENGTH = "medium_varied"
SIGNAL_INTERRUPTION_DURATION_SECONDS = 0.25
# Backward-compatible aliases for tests/importers while the script name is retained.
STATIC_PROFILE_ID = SIGNAL_INTERRUPTION_PROFILE_ID
STATIC_DURATION_SECONDS = SIGNAL_INTERRUPTION_DURATION_SECONDS
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
DRIFT_TOLERANCE_SECONDS = 0.25
CORRECTED_PASS_ID = "house_crt_clean_source_lineage_first8_pass_06"
SUPERSEDED_PASS_ID = "house_crt_luma_neutral_chroma_signal_interruption_first8_pass_05"
DEFAULT_EPISODE_TOML_DIR = Path("/Users/mike/Agents_CascadeEffects/episodes")
CHALLENGER_REFERENCE_VIDEO_PATH = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_scoped_v1/"
    "motion_video_proof/pass_05/challenger_short_scoped_v1_motion_video_proof_pass_05_audio_timed_20260425T143308Z.mp4"
)
CHALLENGER_TEXTURE_MANIFEST_PATH = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_scoped_v1/"
    "motion_contact_sheet/pass_11/historical_signal_texture/pass_01/"
    "historical_signal_texture_pass11_manifest_20260425T061836Z.json"
)
PASS03_SUMMARY_PATH = Path(
    "/Users/mike/Agents_CascadeEffects/"
    "20260429T_house_crt_challenger_contract_pass03__house_crt_challenger_contract_signal_interruption_active_final_summary.json"
)
PASS05_SUMMARY_PATH = Path(
    "/Users/mike/Agents_CascadeEffects/"
    "20260429T_house_crt_first8_contract_pass05__house_crt_luma_neutral_chroma_signal_interruption_first8_contract_summary.json"
)
PASS04_SCHEMA_VERSION = "house_crt_clean_source_lineage_first8_pass_v6"
PASS04_TEXTURE_SCHEMA_VERSION = "house_crt_clean_source_lineage_texture_manifest_v6"
PASS04_METRICS_SCHEMA_VERSION = "house_crt_luma_neutral_chroma_metrics_v1"
PASS04_SUMMARY_SCHEMA_VERSION = "house_crt_clean_source_lineage_first8_summary_v6"
PASS07A_SCHEMA_VERSION = "house_crt_visible_scanline_calibration_pass_v7a"
PASS07A_METRICS_SCHEMA_VERSION = "house_crt_visible_scanline_calibration_metrics_v1"
PASS07A_SUMMARY_SCHEMA_VERSION = "house_crt_visible_scanline_calibration_summary_v1"
PASS07B_SCHEMA_VERSION = "house_crt_visible_scanline_strength_ladder_pass_v7b"
PASS07B_METRICS_SCHEMA_VERSION = "house_crt_visible_scanline_strength_ladder_metrics_v1"
PASS07B_SUMMARY_SCHEMA_VERSION = "house_crt_visible_scanline_strength_ladder_summary_v1"
PASS07C_SCHEMA_VERSION = "house_crt_visible_scanline_high_visibility_ladder_pass_v7c"
PASS07C_METRICS_SCHEMA_VERSION = "house_crt_visible_scanline_high_visibility_ladder_metrics_v1"
PASS07C_SUMMARY_SCHEMA_VERSION = "house_crt_visible_scanline_high_visibility_ladder_summary_v1"
PASS07_SCHEMA_VERSION = "house_crt_clean_source_lineage_visible_scanline_first8_pass_v7"
PASS07_TEXTURE_SCHEMA_VERSION = "house_crt_visible_scanline_texture_manifest_v7"
PASS07_METRICS_SCHEMA_VERSION = "house_crt_visible_scanline_luma_chroma_scanline_metrics_v1"
PASS07_SUMMARY_SCHEMA_VERSION = "house_crt_clean_source_lineage_visible_scanline_first8_summary_v7"

ACTIVE_FINAL_MANIFESTS = {
    "hyatt": "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/shorts/hyatt_short_scoped_v1/motion_video_proof/pass_12_scene_led_challenger_matched_crt/final_exports/hyatt_pass13_outro_tail_source_motion_paper_architecture_motif_outro_mix/20260429T002052Z__final_export.json",
    "piltdown": "/Users/mike/Viz_CascadeEffects/references/episodes/piltdown-man/shorts/piltdown_man_short_scoped_v1/motion_video_proof/pass_03_no_freeze_legibility_repair/final_exports/piltdown_pass05_outro_level_consistency_repair_lower_left_paper_architecture_quiet_full_resolve/20260429T043951Z__final_export.json",
    "semmelweis": "/Users/mike/Viz_CascadeEffects/references/episodes/semmelweis/shorts/semmelweis_short_scoped_v1/motion_video_proof/pass_01d_head_in_hands_ending/final_exports/semmelweis_pass02_head_in_hands_ending_1940s_newsreel_ivory_lower_left_voice_only/20260429T000657Z__final_export.json",
    "tacoma": "/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_02_era_1940s_archival_film/final_exports/tacoma_pass07_no_freeze_outro_tail_repair/20260428T211116Z__final_export.json",
    "titanic": "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/titanic_short_scoped_v1/motion_video_proof/pass_01_ltx_hybrid/final_exports/pass_03_paper_architecture_motif_outro_mix/20260426T142402Z__titanic_pass03_paper_architecture_motif_outro_mix_final_export.json",
}

FIRST_EIGHT_TARGET_ORDER = (
    "challenger",
    "therac-25",
    "hyatt",
    "tacoma",
    "semmelweis",
    "piltdown",
    "titanic",
    "737-max",
)

VISIBLE_SCANLINE_CALIBRATION_TARGETS = ("challenger", "hyatt", "737-max")

FIRST_EIGHT_FINAL_MANIFESTS = {
    "challenger": "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_scoped_v1/final/challenger_short_scoped_v1_video_final_motif_outro_mix_20260425T191413Z_final_export.json",
    "therac-25": "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/motion_video_proof/pass_29_1980s_crt_visible_but_premium/final_exports/therac_pass03_1980s_crt_visible_but_premium_lower_left_paper_architecture/20260429T002616Z__final_export.json",
    "hyatt": ACTIVE_FINAL_MANIFESTS["hyatt"],
    "tacoma": ACTIVE_FINAL_MANIFESTS["tacoma"],
    "semmelweis": ACTIVE_FINAL_MANIFESTS["semmelweis"],
    "piltdown": ACTIVE_FINAL_MANIFESTS["piltdown"],
    "titanic": ACTIVE_FINAL_MANIFESTS["titanic"],
    "737-max": "/Users/mike/Viz_CascadeEffects/references/episodes/737-max/shorts/737_max_short_scoped_v1/motion_video_proof/pass_05_source_led_takeoff_continuity_repair/final_exports/737max_pass06_outro_tail_repair_contemporary_aviation_news_lower_left_paper_architecture/20260429T000602Z__final_export.json",
}

ALL_KNOWN_FINAL_MANIFESTS = {
    **ACTIVE_FINAL_MANIFESTS,
    **FIRST_EIGHT_FINAL_MANIFESTS,
}

SOURCE_PROOF_OVERRIDES = {
    "titanic": "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/titanic_short_scoped_v1/motion_video_proof/pass_01_ltx_hybrid/titanic_motion_video_proof_pass_01_ltx_hybrid__proof.json",
}

CLEAN_SOURCE_PROOF_OVERRIDES = {
    "challenger": "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_scoped_v1/motion_contact_sheet/pass_11/manifest.json",
    "hyatt": "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/shorts/hyatt_short_scoped_v1/motion_video_proof/pass_11_scene_led_no_freeze_44s/hyatt_scene_led_motion_video_proof_pass_11_manifest.json",
    "therac-25": "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/motion_video_proof/pass_28_final_tail_repair/therac25_motion_video_proof_pass_28_tail_repair__proof.json",
    "tacoma": "/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/tacoma_motion_video_proof_pass_01_source_led_20260426T064000Z__proof.json",
}


@dataclass
class Segment:
    index: int
    start: float
    end: float
    source_row_id: str
    signal_seed: int | None = None

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class CleanSourcePlan:
    original_source_proof_path: Path
    clean_source_proof_path: Path
    clean_proof_manifest: dict[str, Any]
    visual_source_path: Path | None
    segment_plan: list[tuple[Segment, Path, float, float]]
    source_lineage_read: dict[str, Any]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def run_json(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return json.loads(proc.stdout)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def contract_read() -> dict[str, Any]:
    return {
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
        "texture_tone_policy": HOUSE_CRT_TONE_POLICY,
        "calibration_recipe_id": CALIBRATION_RECIPE_ID,
        "legacy_calibration_recipe_id": LEGACY_CALIBRATION_RECIPE_ID,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "signal_interruption_profile_id": SIGNAL_INTERRUPTION_PROFILE_ID,
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPTION_DURATION_SECONDS,
        "texture_renderer_source": TEXTURE_RENDERER_SOURCE,
        "texture_conservative_clean_source": TEXTURE_CONSERVATIVE_CLEAN_SOURCE,
        "renderer_scope": "episode_agnostic_house_contract",
        "episode_specific_texture_branch_allowed": False,
        "waiver_required_for_override": True,
    }


def visible_scanline_contract_read() -> dict[str, Any]:
    read = contract_read()
    read.update(
        {
            "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY,
            "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
            "legacy_calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
            "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
            "signal_texture_strength": HOUSE_CRT_INTENSITY,
            "texture_renderer_source": VISIBLE_SCANLINE_RENDERER_SOURCE,
            "contract_status": "selected_for_first8_pass07_review",
            "full_first8_pass_id_after_review": VISIBLE_SCANLINE_FULL_PASS_ID,
            "strength_ladder_pass_id": VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID,
            "strength_ladder_variants": list(VISIBLE_SCANLINE_STRENGTH_VARIANTS),
            "high_visibility_ladder_pass_id": VISIBLE_SCANLINE_HIGH_VISIBILITY_LADDER_PASS_ID,
            "high_visibility_ladder_variants": list(VISIBLE_SCANLINE_HIGH_VISIBILITY_VARIANTS),
            "selected_scanline_strength_variant_id": VISIBLE_SCANLINE_SELECTED_STRENGTH_VARIANT_ID,
            "selected_scanline_strength_variant": selected_visible_scanline_variant(),
            "black_only_scanline_overlay_used": False,
            "zero_mean_horizontal_modulation": True,
        }
    )
    return read


def selected_visible_scanline_variant() -> dict[str, Any]:
    for spec in VISIBLE_SCANLINE_HIGH_VISIBILITY_VARIANTS:
        if spec["scanline_strength_variant_id"] == VISIBLE_SCANLINE_SELECTED_STRENGTH_VARIANT_ID:
            return dict(spec)
    raise RuntimeError(f"Missing selected scanline variant: {VISIBLE_SCANLINE_SELECTED_STRENGTH_VARIANT_ID}")


def scanline_contract_fields(spec: dict[str, Any] | None) -> dict[str, Any]:
    selected = spec or selected_visible_scanline_variant()
    return {
        "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
        "scanline_strength_variant_id": str(selected["scanline_strength_variant_id"]),
        "scanline_delta_y": float(selected["scanline_delta_y"]),
        "scanline_period_pixels": int(selected.get("scanline_period_pixels") or VISIBLE_SCANLINE_PERIOD_PIXELS),
        "scanline_band_pixels": int(selected.get("scanline_band_pixels") or VISIBLE_SCANLINE_BAND_PIXELS),
        "black_only_scanline_overlay_used": False,
        "zero_mean_horizontal_modulation": True,
        "chroma_planes_untouched_by_scanline_modulation": True,
    }


def visual_layer_order_read() -> dict[str, Any]:
    return {
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "visual_layer_sequence": [
            "approved_no_caption_motion_or_proof_source",
            "historical_signal_conservative_clean_normalization",
            "luma_neutral_house_crt_texture",
            "challenger_style_signal_interruption_at_eligible_outgoing_cut_tails",
            "final_duration_tail_visual_handling",
            "caption_burn_last_visual_layer",
            "audio_mux_stream_only_after_caption_burn",
        ],
        "motion_source_contains_captions": False,
        "texture_applied_before_captions": True,
        "signal_interruption_applied_before_captions": True,
        "tail_visual_handling_before_captions": True,
        "caption_burn_is_last_visual_operation": True,
        "post_caption_visual_effects_applied": False,
        "audio_mux_after_caption_burn_is_stream_only": True,
        "caption_layer_order_read": "captions_applied_after_house_crt_signal_interruption_motion_rebuild",
    }


def resolve_first_eight_final_manifests() -> list[tuple[str, Path]]:
    missing = [target for target in FIRST_EIGHT_TARGET_ORDER if target not in FIRST_EIGHT_FINAL_MANIFESTS]
    if missing:
        raise ValueError(f"First-eight final resolver is missing target(s): {', '.join(missing)}")
    return [(target, Path(FIRST_EIGHT_FINAL_MANIFESTS[target])) for target in FIRST_EIGHT_TARGET_ORDER]


def _flatten_mapping(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in payload.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            flat.update(_flatten_mapping(value, full_key))
        else:
            flat[full_key] = value
    return flat


def _candidate_pass_number(key: str) -> int:
    import re

    matches = re.findall(r"pass[_-]?(\d+)", key)
    return int(matches[-1]) if matches else -1


def _candidate_is_superseded(key: str, flat: dict[str, Any]) -> bool:
    pass_no = _candidate_pass_number(key)
    lowered_values: list[str] = []
    key_stem = key.removesuffix("_path").removesuffix(".path")
    for status_key, status_value in flat.items():
        if not isinstance(status_value, str):
            continue
        if key_stem in status_key or (pass_no >= 0 and f"pass_{pass_no:02d}" in status_key):
            lowered_values.append(status_value.lower())
    joined = " ".join(lowered_values)
    return any(word in joined for word in ("superseded", "diagnostic_only", "reject"))


def discover_current_final_manifests(toml_dir: Path = DEFAULT_EPISODE_TOML_DIR) -> list[tuple[str, Path]]:
    """Resolve future/current final manifests from episode TOML, independent of the first-eight list.

    First-eight production remains an explicit roster. Future Shorts can enter this
    contract by carrying a top-level or nested final_export_manifest_path that points
    at the current final-export manifest.
    """

    resolved: list[tuple[str, Path]] = []
    for toml_path in sorted(toml_dir.glob("*.toml")):
        with toml_path.open("rb") as handle:
            payload = tomllib.load(handle)
        episode_id = str(payload.get("id") or toml_path.stem)
        flat = _flatten_mapping(payload)
        direct = payload.get("final_export_manifest_path")
        if isinstance(direct, str) and direct and Path(direct).exists():
            resolved.append((episode_id, Path(direct)))
            continue
        candidates: list[tuple[int, str, Path]] = []
        for key, value in flat.items():
            if not isinstance(value, str) or not value.endswith(".json"):
                continue
            key_tail = key.rsplit(".", 1)[-1]
            if "final_export_manifest" not in key_tail or not key_tail.endswith("_path"):
                continue
            path = Path(value)
            if path.exists() and not _candidate_is_superseded(key_tail, flat):
                candidates.append((_candidate_pass_number(key_tail), key_tail, path))
        if candidates:
            _pass_no, _key, path = sorted(candidates, key=lambda item: (item[0], item[1]))[-1]
            resolved.append((episode_id, path))
    return resolved


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ffprobe(path: Path) -> dict[str, Any]:
    return run_json(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ]
    )


def duration(path: Path) -> float:
    info = ffprobe(path)
    return float(info.get("format", {}).get("duration") or 0.0)


def video_stream(path: Path) -> dict[str, Any]:
    for stream in ffprobe(path).get("streams", []):
        if stream.get("codec_type") == "video":
            return stream
    raise ValueError(f"No video stream found: {path}")


def stream_counts(path: Path) -> dict[str, int]:
    counts = {"video": 0, "audio": 0, "subtitle": 0}
    for stream in ffprobe(path).get("streams", []):
        typ = stream.get("codec_type")
        if typ in counts:
            counts[typ] += 1
    return counts


def ffmpeg_escape(path: Path) -> str:
    s = str(path)
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")


def shell_escape_for_concat(path: Path) -> str:
    return str(path).replace("'", "'\\''")


def find_final_path(final_manifest: dict[str, Any]) -> Path | None:
    for key in ("captioned_final_path", "final_video_path"):
        val = final_manifest.get(key) or final_manifest.get("outputs", {}).get(key)
        if val:
            return Path(val)
    return None


def find_caption_ass_path(final_manifest: dict[str, Any]) -> Path | None:
    val = final_manifest.get("caption_ass_path") or final_manifest.get("outputs", {}).get("caption_ass_path")
    return Path(val) if val else None


def resolve_source_proof(target: str, final_manifest: dict[str, Any]) -> Path | None:
    if target in SOURCE_PROOF_OVERRIDES:
        return Path(SOURCE_PROOF_OVERRIDES[target])
    val = final_manifest.get("source_proof_manifest_path") or final_manifest.get("outputs", {}).get("source_proof_manifest_path")
    if val:
        return Path(val)
    upstream = final_manifest.get("source_final_export_manifest_path") or final_manifest.get("outputs", {}).get("source_final_export_manifest_path")
    if upstream:
        upstream_manifest = load_json(Path(upstream))
        return resolve_source_proof(target, upstream_manifest)
    return None


def resolve_visual_source(proof_manifest: dict[str, Any], source_proof_path: Path) -> Path | None:
    for key in (
        "visual_bed_no_audio_path",
        "visual_noaudio_path",
        "video_only_path",
        "silent_video_path",
        "motion_only_video_path",
        "no_audio_video_path",
        "normalized_no_audio_path",
        "proof_video_path",
        "proof_path",
        "motion_video_path",
    ):
        val = proof_manifest.get(key) or proof_manifest.get("outputs", {}).get(key)
        if val:
            return Path(val)
    for candidate in sorted(source_proof_path.parent.glob("*video_only*.mp4")):
        if "caption" not in candidate.name.lower():
            return candidate
    for candidate in sorted(source_proof_path.parent.glob("*no_audio*.mp4")):
        if "caption" not in candidate.name.lower():
            return candidate
    for candidate in sorted(source_proof_path.parent.glob("*.mp4")):
        if "caption" not in candidate.name.lower():
            return candidate
    return None


def source_path_is_pretextured(path: Path | str | None) -> bool:
    if not path:
        return False
    lowered = str(path).lower()
    return (
        "/historical_signal_texture/" in lowered
        or lowered.endswith("/historical_signal_texture")
        or "/historical_signal/" in lowered
        or "__era_1980s_broadcast_crt_v1__" in lowered
        or "challenger_matched_crt" in lowered
        or "1980s_crt_visible_but_premium" in lowered
        or "era_1940s_archival_film" in lowered
    )


def source_manifest_pretextured_reasons(
    proof_manifest: dict[str, Any],
    source_proof_path: Path,
    selected_visual_source: Path | None = None,
) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []

    def add(field: str, value: Any, reason: str) -> None:
        reasons.append(
            {
                "source_proof_manifest_path": str(source_proof_path),
                "field": field,
                "value": str(value),
                "reason": reason,
            }
        )

    for key in ("historical_signal_texture_used", "historical_signal_texture_applied"):
        if proof_manifest.get(key) is True:
            add(key, True, f"{key}_true")
    if normalize_text_for_lineage(proof_manifest.get("historical_signal_texture_read")) == "pass":
        add("historical_signal_texture_read", "pass", "historical_signal_texture_read_pass")
    if proof_manifest.get("input_historical_signal_texture_manifest_path"):
        add(
            "input_historical_signal_texture_manifest_path",
            proof_manifest.get("input_historical_signal_texture_manifest_path"),
            "manifest_derives_from_historical_signal_texture_manifest",
        )
    if (
        normalize_text_for_lineage(proof_manifest.get("historical_signal_profile_id")) == HOUSE_CRT_PROFILE_ID
        and proof_manifest.get("signal_texture_strength")
        and proof_manifest.get("historical_signal_texture_applied") is not False
    ):
        add(
            "historical_signal_profile_id",
            proof_manifest.get("historical_signal_profile_id"),
            "manifest_records_historical_signal_texture_profile",
        )
    if (
        normalize_text_for_lineage(proof_manifest.get("signal_interruption_read")) == "pass"
        and normalize_text_for_lineage(proof_manifest.get("historical_signal_profile_id")) == HOUSE_CRT_PROFILE_ID
    ):
        add("signal_interruption_read", "pass", "manifest_records_challenger_pass05_signal_over_textured_source")
    texture_applied = proof_manifest.get("texture_applied_path") or proof_manifest.get("outputs", {}).get("texture_applied_path")
    if texture_applied:
        add("texture_applied_path", texture_applied, "manifest_records_texture_applied_path")
    for key in ("visual_noaudio_path", "visual_bed_no_audio_path", "video_only_path", "motion_only_video_path", "proof_video_path"):
        val = proof_manifest.get(key) or proof_manifest.get("outputs", {}).get(key)
        if val and source_path_is_pretextured(val):
            add(key, val, "manifest_visual_path_under_historical_signal_texture")
    if selected_visual_source is not None and source_path_is_pretextured(selected_visual_source):
        add("selected_visual_source_path", selected_visual_source, "selected_visual_source_under_historical_signal_texture")
    return reasons


def normalize_text_for_lineage(value: Any) -> str:
    return str(value or "").strip().lower()


def rejected_pretextured_paths(rejections: list[dict[str, str]]) -> list[str]:
    paths: set[str] = set()
    for item in rejections:
        value = item.get("value", "")
        if value.startswith("/"):
            paths.add(value)
        paths.add(item.get("source_proof_manifest_path", ""))
    return sorted(path for path in paths if path)


def selected_source_is_clean(path: Path | None, proof_manifest: dict[str, Any]) -> bool:
    if path is None or source_path_is_pretextured(path):
        return False
    texture_path = proof_manifest.get("texture_applied_path") or proof_manifest.get("outputs", {}).get("texture_applied_path")
    if texture_path and Path(str(texture_path)) == path:
        return False
    if proof_manifest.get("historical_signal_texture_used") is True:
        return False
    if proof_manifest.get("historical_signal_texture_applied") is True:
        return False
    return True


def first_existing_row_clip_path(row: dict[str, Any]) -> Path | None:
    for key in (
        "source_motion_clip_path",
        "output_path",
        "vertical_clip_path",
        "proof_segment_path",
        "segment_path",
        "clip_path",
        "normalized_clip_path",
        "motion_clip_path",
        "input_path",
        "source_clip_path",
        "source_path",
    ):
        val = row.get(key)
        if not val:
            continue
        path = Path(str(val))
        if path.exists():
            return path
    return None


def row_id(row: dict[str, Any], index: int) -> str:
    return str(
        row.get("beat_id")
        or row.get("shot_id")
        or row.get("row_id")
        or row.get("edl_id")
        or row.get("id")
        or f"segment_{index:02d}"
    )


def row_duration_seconds(row: dict[str, Any]) -> float | None:
    direct = coerce_float(
        row.get("duration_seconds")
        or row.get("duration")
        or row.get("actual_duration_seconds")
        or row.get("target_story_duration_seconds")
        or row.get("intended_duration_seconds")
        or row.get("rendered_segment_duration_seconds")
    )
    if direct is not None:
        return direct
    start, end = row_start_end(row)
    if start is not None and end is not None and end > start:
        return end - start
    span = row.get("source_span_seconds")
    if isinstance(span, dict):
        span_start = coerce_float(span.get("start"))
        span_end = coerce_float(span.get("end"))
        if span_start is not None and span_end is not None and span_end > span_start:
            return span_end - span_start
    return None


def resolve_row_clip_segment_sources(rows: list[dict[str, Any]]) -> list[tuple[Segment, Path, float, float]]:
    segment_sources: list[tuple[Segment, Path, float, float]] = []
    timeline_cursor = 0.0
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        source_path = first_existing_row_clip_path(row)
        if source_path is None or source_path_is_pretextured(source_path):
            continue
        source_duration = duration(source_path)
        intended_duration = row_duration_seconds(row)
        segment_duration = min(source_duration, intended_duration) if intended_duration else source_duration
        if segment_duration < 0.05:
            continue
        start, end = row_start_end(row)
        timeline_in = start if start is not None else timeline_cursor
        timeline_out = end if end is not None and end > timeline_in else timeline_in + segment_duration
        segment = Segment(
            index=len(segment_sources) + 1,
            start=0.0,
            end=segment_duration,
            source_row_id=row_id(row, index),
        )
        segment_sources.append((segment, source_path, timeline_in, timeline_out))
        timeline_cursor = timeline_out
    return segment_sources


def resolve_segment_source_rows(proof_manifest: dict[str, Any]) -> list[tuple[Segment, Path, float, float]]:
    rows = proof_manifest.get("segments")
    if not isinstance(rows, list) or not rows:
        return []
    return resolve_row_clip_segment_sources([row for row in rows if isinstance(row, dict)])


def coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def row_start_end(row: dict[str, Any]) -> tuple[float | None, float | None]:
    starts = (
        "timeline_in",
        "timeline_in_seconds",
        "timeline_start_seconds",
        "proof_start",
        "proof_start_seconds",
        "cue_start",
        "cue_start_seconds",
        "start",
        "start_seconds",
    )
    ends = (
        "timeline_out",
        "timeline_out_seconds",
        "timeline_end_seconds",
        "proof_end",
        "proof_end_seconds",
        "cue_end",
        "cue_end_seconds",
        "end",
        "end_seconds",
    )
    start = next((coerce_float(row.get(k)) for k in starts if coerce_float(row.get(k)) is not None), None)
    end = next((coerce_float(row.get(k)) for k in ends if coerce_float(row.get(k)) is not None), None)
    if start is None or end is None:
        dur = coerce_float(
            row.get("duration_seconds")
            or row.get("duration")
            or row.get("actual_duration_seconds")
            or row.get("target_story_duration_seconds")
            or row.get("intended_duration_seconds")
        )
        if start is not None and dur is not None:
            end = start + dur
    return start, end


def extract_rows(proof_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("beats", "story_shots", "edl_rows", "shot_timing_edl", "segments", "rows", "shots", "items"):
        rows = proof_manifest.get(key)
        if isinstance(rows, list) and rows:
            return rows
    edl_path = (
        proof_manifest.get("shot_timing_edl_path")
        or proof_manifest.get("shot_timing_edl_json_path")
        or proof_manifest.get("shot_timing_edl_manifest_path")
        or proof_manifest.get("outputs", {}).get("shot_timing_edl_path")
        or proof_manifest.get("outputs", {}).get("shot_timing_edl_json_path")
        or proof_manifest.get("outputs", {}).get("shot_timing_edl_manifest_path")
    )
    if edl_path:
        edl_path_obj = Path(edl_path)
        if edl_path_obj.suffix.lower() != ".json":
            return []
        edl = load_json(edl_path_obj)
        for key in ("rows", "beats", "story_shots", "edl_rows", "shot_timing_edl", "segments", "shots", "items"):
            rows = edl.get(key)
            if isinstance(rows, list) and rows:
                return rows
    return []


def normalize_segments(rows: list[dict[str, Any]], visual_duration: float) -> list[Segment]:
    segments: list[Segment] = []
    for index, row in enumerate(rows, start=1):
        start, end = row_start_end(row)
        if start is None or end is None or end <= start:
            continue
        start = max(0.0, start)
        end = min(visual_duration, end)
        if end - start < 0.05:
            continue
        row_id = str(row.get("beat_id") or row.get("shot_id") or row.get("row_id") or row.get("id") or f"segment_{index:02d}")
        segments.append(Segment(index=len(segments) + 1, start=start, end=end, source_row_id=row_id))
    return segments


def segment_plan_from_visual_source(
    rows: list[dict[str, Any]],
    visual_source: Path,
    visual_duration: float,
) -> list[tuple[Segment, Path, float, float]]:
    segments = normalize_segments(rows, visual_duration)
    return [(segment, visual_source, segment.start, segment.end) for segment in segments]


def _lineage_rejection_entry(
    source_proof_path: Path,
    proof_manifest: dict[str, Any],
    selected_visual_source: Path | None = None,
) -> list[dict[str, str]]:
    return source_manifest_pretextured_reasons(proof_manifest, source_proof_path, selected_visual_source)


def resolve_clean_source_plan(
    target: str,
    original_source_proof_path: Path,
    original_proof_manifest: dict[str, Any],
) -> CleanSourcePlan:
    rejected_sources = _lineage_rejection_entry(original_source_proof_path, original_proof_manifest)
    clean_source_path = original_source_proof_path
    clean_source_selection_reason = "original_source_proof_manifest_clean"
    if target in CLEAN_SOURCE_PROOF_OVERRIDES:
        clean_source_path = Path(CLEAN_SOURCE_PROOF_OVERRIDES[target])
        clean_source_selection_reason = "explicit_clean_predecessor_override"
    elif rejected_sources:
        upstream = (
            original_proof_manifest.get("source_proof_manifest_path")
            or original_proof_manifest.get("source_motion_manifest_path")
            or original_proof_manifest.get("input_motion_manifest_path")
            or original_proof_manifest.get("outputs", {}).get("source_proof_manifest_path")
        )
        if upstream and Path(str(upstream)).exists():
            clean_source_path = Path(str(upstream))
            clean_source_selection_reason = "source_proof_manifest_path_clean_predecessor"

    clean_manifest = load_json(clean_source_path)
    selected_visual_source = resolve_visual_source(clean_manifest, clean_source_path)
    clean_rejections = _lineage_rejection_entry(clean_source_path, clean_manifest, selected_visual_source)
    rows = extract_rows(clean_manifest)
    row_clip_plan = resolve_row_clip_segment_sources(rows)

    segment_plan: list[tuple[Segment, Path, float, float]] = []
    selected_source_mode = "unresolved"
    prefer_row_clip_plan = target == "challenger"
    if (
        not prefer_row_clip_plan
        and selected_visual_source is not None
        and selected_visual_source.exists()
        and selected_source_is_clean(
        selected_visual_source,
        clean_manifest,
        )
    ):
        visual_duration = duration(selected_visual_source)
        segment_plan = segment_plan_from_visual_source(rows, selected_visual_source, visual_duration)
        selected_source_mode = "single_clean_no_caption_visual_source"
    if len(segment_plan) < 2 and len(row_clip_plan) >= 2:
        segment_plan = row_clip_plan
        selected_source_mode = "ordered_clean_row_clip_sources"
        selected_visual_source = None
    if len(segment_plan) < 2 and len(resolve_segment_source_rows(clean_manifest)) >= 2:
        segment_plan = resolve_segment_source_rows(clean_manifest)
        selected_source_mode = "ordered_clean_manifest_segment_sources"
        selected_visual_source = None

    selected_paths = [str(path) for _segment, path, _timeline_in, _timeline_out in segment_plan]
    selected_rejections = [
        {
            "source_proof_manifest_path": str(clean_source_path),
            "field": "selected_segment_source_path",
            "value": path,
            "reason": "selected_segment_source_under_historical_signal_texture",
        }
        for path in selected_paths
        if source_path_is_pretextured(path)
    ]
    hard_clean_rejections = [
        item
        for item in clean_rejections
        if item["field"] in {"historical_signal_texture_used", "historical_signal_texture_applied"}
        or item.get("reason") == "selected_visual_source_under_historical_signal_texture"
    ]
    clean_source_confirmed = bool(segment_plan) and not selected_rejections and not hard_clean_rejections
    sidecar_rejections = [
        item
        for item in clean_rejections
        if item not in hard_clean_rejections
    ]
    source_lineage_read = {
        "schema_version": "house_crt_clean_source_lineage_read_v1",
        "clean_source_confirmed": clean_source_confirmed,
        "source_lineage_policy": "reject_pretextured_motion_sources_before_house_crt_contract",
        "selected_source_mode": selected_source_mode,
        "source_selection_reason": clean_source_selection_reason,
        "original_source_proof_manifest_path": str(original_source_proof_path),
        "clean_source_proof_manifest_path": str(clean_source_path),
        "selected_visual_source_path": str(selected_visual_source) if selected_visual_source else "",
        "selected_segment_source_paths": selected_paths,
        "selected_segment_source_count": len(selected_paths),
        "rejected_pretextured_source_paths": rejected_pretextured_paths(rejected_sources + selected_rejections),
        "rejected_upstream_manifest_reads": rejected_sources,
        "clean_source_sidecar_texture_fields_ignored": sidecar_rejections,
        "selected_source_rejections": selected_rejections,
        "clean_source_evidence": {
            "historical_signal_texture_used": clean_manifest.get("historical_signal_texture_used", False),
            "historical_signal_texture_applied": clean_manifest.get("historical_signal_texture_applied", False),
            "historical_signal_texture_read": clean_manifest.get("historical_signal_texture_read", ""),
            "row_count": len(rows),
            "segment_count": len(segment_plan),
            "selected_paths_under_historical_signal_texture": bool(selected_rejections),
        },
    }
    return CleanSourcePlan(
        original_source_proof_path=original_source_proof_path,
        clean_source_proof_path=clean_source_path,
        clean_proof_manifest=clean_manifest,
        visual_source_path=selected_visual_source,
        segment_plan=segment_plan,
        source_lineage_read=source_lineage_read,
    )


def historical_strength_scale(strength: str) -> float:
    return {
        "low": 0.45,
        "low_to_visible": 0.72,
        "low_to_medium": 0.82,
        "visible_but_premium": 1.0,
        "medium": 1.18,
    }[strength]


def historical_signal_conservative_clean_filter(width: int, height: int, fps: float) -> str:
    return (
        f"fps={fps:.6f},scale={width}:{height}:flags=lanczos,"
        "hqdn3d=0.8:0.6:2.0:1.5,"
        "unsharp=5:5:0.28:3:3:0.12,"
        "eq=contrast=1.015:saturation=1.01:brightness=0.002,"
        "setsar=1,format=yuv420p"
    )


def historical_signal_filter_graph(
    *,
    profile_id: str,
    strength: str,
    width: int,
    height: int,
    fps: float,
) -> str:
    return luma_neutral_chroma_filter_graph(
        profile_id=profile_id,
        strength=strength,
        width=width,
        height=height,
        fps=fps,
    )


def luma_neutral_chroma_filter_graph(
    *,
    profile_id: str,
    strength: str,
    width: int,
    height: int,
    fps: float,
) -> str:
    if profile_id != HOUSE_CRT_PROFILE_ID:
        raise ValueError(f"Unsupported house CRT profile: {profile_id}")
    scale = historical_strength_scale(strength)
    base = f"[0:v]fps={fps:.6f},scale={width}:{height}:flags=lanczos,setsar=1"
    luma_noise = max(0.5, 1.25 * scale)
    bloom = 0.006 + (0.004 * scale)
    return (
        f"{base},crop={max(2, width - 1)}:{max(2, height - 1)}:"
        "0.5+0.5*sin(n/17):0.5+0.5*cos(n/19),"
        f"scale={width}:{height}:flags=bicubic,"
        "chromashift=cbh=1:crh=-1,"
        f"eq=contrast={1.006 + (0.006 * scale):.3f}:brightness=0.000:"
        f"saturation={1.0 + (0.280 * scale):.3f}:gamma=1.000,"
        f"noise=c0s={luma_noise:.2f}:c0f=t+u,"
        "split[base][glow];"
        f"[glow]gblur=sigma={0.40 + (0.12 * scale):.2f},"
        "eq=brightness=0.000:saturation=1.015[glow2];"
        f"[base][glow2]blend=all_mode=screen:all_opacity={bloom:.3f},"
        "setsar=1,format=yuv420p[v]"
    )


def visible_scanline_modulation_filter(
    scale: float,
    scanline_delta_y: float | None = None,
    scanline_period_pixels: int | None = None,
    scanline_band_pixels: int | None = None,
) -> str:
    delta = VISIBLE_SCANLINE_DELTA_RGB * scale if scanline_delta_y is None else float(scanline_delta_y)
    period = int(scanline_period_pixels or VISIBLE_SCANLINE_PERIOD_PIXELS)
    band = max(1, min(int(scanline_band_pixels or VISIBLE_SCANLINE_BAND_PIXELS), max(1, period // 2)))
    light_start = period // 2
    dark_end = band - 1
    light_end = light_start + band - 1
    modulation = (
        f"if(between(mod(Y,{period}),0,{dark_end}),-{delta:.3f},"
        f"if(between(mod(Y,{period}),{light_start},{light_end}),{delta:.3f},0))"
    )
    return (
        "format=yuv444p,"
        f"geq=lum='min(max(lum(X,Y)+{modulation},0),255)':cb='cb(X,Y)':cr='cr(X,Y)'"
    )


def luma_neutral_chroma_visible_scanline_filter_graph(
    *,
    profile_id: str,
    strength: str,
    width: int,
    height: int,
    fps: float,
    scanline_delta_y: float | None = None,
    scanline_period_pixels: int | None = None,
    scanline_band_pixels: int | None = None,
) -> str:
    if profile_id != HOUSE_CRT_PROFILE_ID:
        raise ValueError(f"Unsupported house CRT profile: {profile_id}")
    scale = historical_strength_scale(strength)
    base = f"[0:v]fps={fps:.6f},scale={width}:{height}:flags=lanczos,setsar=1"
    luma_noise = max(0.5, 1.25 * scale)
    bloom = 0.006 + (0.004 * scale)
    scanline = visible_scanline_modulation_filter(
        scale,
        scanline_delta_y,
        scanline_period_pixels,
        scanline_band_pixels,
    )
    return (
        f"{base},crop={max(2, width - 1)}:{max(2, height - 1)}:"
        "0.5+0.5*sin(n/17):0.5+0.5*cos(n/19),"
        f"scale={width}:{height}:flags=bicubic,"
        "chromashift=cbh=1:crh=-1,"
        f"eq=contrast={1.006 + (0.006 * scale):.3f}:brightness=0.000:"
        f"saturation={1.0 + (0.280 * scale):.3f}:gamma=1.000,"
        f"noise=c0s={luma_noise:.2f}:c0f=t+u,"
        "split[base][glow];"
        f"[glow]gblur=sigma={0.40 + (0.12 * scale):.2f},"
        "eq=brightness=0.000:saturation=1.015[glow2];"
        f"[base][glow2]blend=all_mode=screen:all_opacity={bloom:.3f},"
        f"{scanline},setsar=1,format=yuv420p[v]"
    )


def luma_neutral_monochrome_filter_graph(
    *,
    profile_id: str,
    strength: str,
    width: int,
    height: int,
    fps: float,
) -> str:
    if profile_id != HOUSE_CRT_PROFILE_ID:
        raise ValueError(f"Unsupported house CRT profile: {profile_id}")
    scale = historical_strength_scale(strength)
    base = f"[0:v]fps={fps:.6f},scale={width}:{height}:flags=lanczos,setsar=1"
    luma_noise = max(0.5, 1.25 * scale)
    bloom = 0.004 + (0.003 * scale)
    return (
        f"{base},crop={max(2, width - 1)}:{max(2, height - 1)}:"
        "0.5+0.5*sin(n/17):0.5+0.5*cos(n/19),"
        f"scale={width}:{height}:flags=bicubic,"
        f"eq=contrast={1.006 + (0.006 * scale):.3f}:brightness=0.000:"
        "saturation=1.000:gamma=1.000,"
        f"noise=c0s={luma_noise:.2f}:c0f=t+u,"
        "split[base][glow];"
        f"[glow]gblur=sigma={0.36 + (0.10 * scale):.2f},"
        "eq=brightness=0.000:saturation=1.000[glow2];"
        f"[base][glow2]blend=all_mode=screen:all_opacity={bloom:.3f},"
        "setsar=1,format=yuv420p[v]"
    )


def luma_neutral_monochrome_visible_scanline_filter_graph(
    *,
    profile_id: str,
    strength: str,
    width: int,
    height: int,
    fps: float,
    scanline_delta_y: float | None = None,
    scanline_period_pixels: int | None = None,
    scanline_band_pixels: int | None = None,
) -> str:
    if profile_id != HOUSE_CRT_PROFILE_ID:
        raise ValueError(f"Unsupported house CRT profile: {profile_id}")
    scale = historical_strength_scale(strength)
    base = f"[0:v]fps={fps:.6f},scale={width}:{height}:flags=lanczos,setsar=1"
    luma_noise = max(0.5, 1.25 * scale)
    bloom = 0.004 + (0.003 * scale)
    scanline = visible_scanline_modulation_filter(
        scale,
        scanline_delta_y,
        scanline_period_pixels,
        scanline_band_pixels,
    )
    return (
        f"{base},crop={max(2, width - 1)}:{max(2, height - 1)}:"
        "0.5+0.5*sin(n/17):0.5+0.5*cos(n/19),"
        f"scale={width}:{height}:flags=bicubic,"
        f"eq=contrast={1.006 + (0.006 * scale):.3f}:brightness=0.000:"
        "saturation=1.000:gamma=1.000,"
        f"noise=c0s={luma_noise:.2f}:c0f=t+u,"
        "split[base][glow];"
        f"[glow]gblur=sigma={0.36 + (0.10 * scale):.2f},"
        "eq=brightness=0.000:saturation=1.000[glow2];"
        f"[base][glow2]blend=all_mode=screen:all_opacity={bloom:.3f},"
        f"{scanline},setsar=1,format=yuv420p[v]"
    )


def variant_config(seed: int, order: int) -> dict[str, Any]:
    rng = random.Random(seed + order * 104729)
    variants = [
        {
            "variant_id": "thin_tracking_tears",
            "emphasis": "full",
            "band_count": rng.randint(4, 7),
            "band_heights": [2, 3, 4, 5, 6],
            "dx_range": (10, 34),
            "snow_strength": rng.uniform(0.12, 0.20),
            "line_alpha": rng.randint(44, 78),
            "chroma_shift": rng.randint(1, 3),
            "dropout_count": rng.randint(0, 1),
        },
        {
            "variant_id": "bottom_tracking_roll",
            "emphasis": "lower",
            "band_count": rng.randint(3, 5),
            "band_heights": [4, 6, 8, 12, 18],
            "dx_range": (18, 46),
            "snow_strength": rng.uniform(0.08, 0.16),
            "line_alpha": rng.randint(36, 68),
            "chroma_shift": rng.randint(2, 4),
            "dropout_count": rng.randint(1, 2),
        },
        {
            "variant_id": "top_sync_flutter",
            "emphasis": "upper",
            "band_count": rng.randint(5, 8),
            "band_heights": [2, 3, 4, 6, 8],
            "dx_range": (8, 28),
            "snow_strength": rng.uniform(0.10, 0.18),
            "line_alpha": rng.randint(50, 86),
            "chroma_shift": rng.randint(1, 2),
            "dropout_count": rng.randint(0, 1),
        },
        {
            "variant_id": "chroma_skew_dropout",
            "emphasis": "middle",
            "band_count": rng.randint(2, 4),
            "band_heights": [8, 12, 16, 22],
            "dx_range": (22, 58),
            "snow_strength": rng.uniform(0.06, 0.14),
            "line_alpha": rng.randint(28, 58),
            "chroma_shift": rng.randint(3, 5),
            "dropout_count": rng.randint(1, 2),
        },
        {
            "variant_id": "sparse_luma_snap",
            "emphasis": "full",
            "band_count": rng.randint(2, 4),
            "band_heights": [2, 3, 4, 10],
            "dx_range": (6, 22),
            "snow_strength": rng.uniform(0.16, 0.25),
            "line_alpha": rng.randint(70, 106),
            "chroma_shift": rng.randint(1, 3),
            "dropout_count": rng.randint(0, 1),
        },
    ]
    config = variants[(order - 1) % len(variants)]
    config["seed"] = seed + order * 104729
    return config


def pick_y(rng: random.Random, h: int, emphasis: str) -> int:
    if emphasis == "upper":
        return rng.randrange(20, max(21, int(h * 0.35)))
    if emphasis == "middle":
        return rng.randrange(int(h * 0.25), int(h * 0.72))
    if emphasis == "lower":
        return rng.randrange(int(h * 0.55), h - 24)
    return rng.randrange(8, h - 24)


def apply_signal_frame(im: Image.Image, config: dict[str, Any], frame_index: int, total_frames: int) -> Image.Image:
    rng = random.Random(int(config["seed"]) + frame_index * 7919)
    progress = (frame_index + 1) / max(1, total_frames)
    out = im.convert("RGB")
    w, h = out.size

    attack = progress ** rng.choice([0.75, 0.9, 1.1, 1.35])
    r, g, b = out.split()
    chroma_shift = int(round(int(config["chroma_shift"]) * attack))
    if config["variant_id"] == "chroma_skew_dropout":
        chroma_shift += frame_index % 2
    r = ImageChops.offset(r, chroma_shift, 0)
    b = ImageChops.offset(b, -chroma_shift, 0)
    out = Image.merge("RGB", (r, g, b))
    out = ImageEnhance.Contrast(out).enhance(1.02 + 0.08 * attack)
    out = ImageEnhance.Brightness(out).enhance(1.0 + 0.035 * attack)

    draw = ImageDraw.Draw(out, "RGBA")
    band_count = max(1, int(round(int(config["band_count"]) * (0.65 + 0.55 * attack))))
    for _ in range(band_count):
        y = pick_y(rng, h, str(config["emphasis"]))
        band_h = rng.choice(config["band_heights"])
        dx_min, dx_max = config["dx_range"]
        dx_mag = rng.randrange(int(dx_min), int(dx_max) + 1)
        dx = dx_mag if rng.random() > 0.5 else -dx_mag
        band = out.crop((0, y, w, min(h, y + band_h)))
        band = ImageChops.offset(band, dx, 0)
        out.paste(band, (0, y))
        alpha = int(int(config["line_alpha"]) * attack * rng.uniform(0.55, 1.10))
        color = (245, 245, 245, alpha) if rng.random() > 0.42 else (2, 2, 2, alpha)
        draw.rectangle((0, y, w, min(h, y + max(2, band_h // 2))), fill=color)

    for _ in range(int(config["dropout_count"])):
        if rng.random() < 0.55 + 0.30 * attack:
            y = pick_y(rng, h, str(config["emphasis"]))
            dropout_h = rng.choice([3, 4, 5, 7])
            draw.rectangle((0, y, w, min(h, y + dropout_h)), fill=(255, 255, 255, int(82 * attack)))
            draw.rectangle(
                (0, min(h - 1, y + dropout_h + 2), w, min(h - 1, y + dropout_h + 5)),
                fill=(0, 0, 0, int(48 * attack)),
            )

    noise = Image.effect_noise((w, h), 48 + 34 * attack).convert("L")
    snow_strength = float(config["snow_strength"])
    alpha = Image.eval(noise, lambda px: max(0, min(52, int((px - 122) * snow_strength * attack))))
    snow = Image.new("RGB", (w, h), (236, 236, 232))
    return Image.composite(snow, out, alpha)


def render_signal_tail_segment(src: Path, out: Path, work_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    pattern = work_dir / "%06d.png"
    src_duration = duration(src)
    start = max(0.0, src_duration - SIGNAL_INTERRUPTION_DURATION_SECONDS)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.6f}",
            "-i",
            str(src),
            "-t",
            f"{SIGNAL_INTERRUPTION_DURATION_SECONDS:.6f}",
            "-vf",
            f"fps={TARGET_FPS},scale={TARGET_WIDTH}:{TARGET_HEIGHT}:flags=lanczos,setsar=1",
            "-start_number",
            "0",
            str(pattern),
        ]
    )
    frame_paths = sorted(work_dir.glob("*.png"))
    if not frame_paths:
        raise RuntimeError(f"No frames extracted from {src}")
    for idx, frame_path in enumerate(frame_paths):
        with Image.open(frame_path) as im:
            apply_signal_frame(im, config, idx, len(frame_paths)).save(frame_path)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            str(TARGET_FPS),
            "-i",
            str(pattern),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(TARGET_FPS),
            "-movflags",
            "+faststart",
            str(out),
        ]
    )
    return {
        "frame_count": len(frame_paths),
        "interruption_frame_count": len(frame_paths),
        "interruption_start_seconds": round(start, 3),
        "interruption_duration_seconds": round(len(frame_paths) / TARGET_FPS, 3),
        "variant_config": config,
    }


def render_source_segment(source: Path, segment: Segment, out_path: Path) -> Path:
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{segment.start:.6f}",
            "-i",
            str(source),
            "-t",
            f"{segment.duration:.6f}",
            "-vf",
            (
                f"fps={TARGET_FPS},scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
                "force_original_aspect_ratio=increase,crop="
                f"{TARGET_WIDTH}:{TARGET_HEIGHT},setsar=1,format=yuv420p"
            ),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-r",
            str(TARGET_FPS),
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
            str(out_path),
        ]
    )
    return out_path


def render_historical_signal_conservative_clean(src: Path, out_path: Path) -> Path:
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-vf",
            historical_signal_conservative_clean_filter(TARGET_WIDTH, TARGET_HEIGHT, float(TARGET_FPS)),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(TARGET_FPS),
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
            "-movflags",
            "+faststart",
            "-an",
            str(out_path),
        ]
    )
    return out_path


def signalstats_metrics(path: Path, frame_limit: int = 90) -> dict[str, Any]:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-vf",
            "signalstats,metadata=print:file=-",
            "-frames:v",
            str(frame_limit),
            "-f",
            "null",
            "-",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    values: dict[str, list[float]] = {"YAVG": [], "UAVG": [], "VAVG": [], "SATAVG": []}
    for line in (proc.stdout + "\n" + proc.stderr).splitlines():
        if "=" not in line:
            continue
        key, raw_value = line.rsplit("=", 1)
        short_key = key.rsplit(".", 1)[-1]
        if short_key not in values:
            continue
        try:
            values[short_key].append(float(raw_value))
        except ValueError:
            continue
    if not values["YAVG"]:
        raise RuntimeError(f"Unable to read signalstats metrics from {path}")

    def mean(key: str) -> float | None:
        vals = values[key]
        return sum(vals) / len(vals) if vals else None

    yavg = mean("YAVG")
    uavg = mean("UAVG")
    vavg = mean("VAVG")
    satavg = mean("SATAVG")
    uv_magnitude = None
    if uavg is not None and vavg is not None:
        uv_magnitude = math.hypot(uavg - 128.0, vavg - 128.0)
    chroma_magnitude = satavg if satavg is not None else uv_magnitude
    return {
        "path": str(path),
        "frame_limit": frame_limit,
        "sampled_frame_count": len(values["YAVG"]),
        "yavg": round(float(yavg or 0.0), 4),
        "uavg": round(float(uavg or 0.0), 4) if uavg is not None else None,
        "vavg": round(float(vavg or 0.0), 4) if vavg is not None else None,
        "satavg": round(float(satavg), 4) if satavg is not None else None,
        "uv_chroma_magnitude": round(float(uv_magnitude), 4) if uv_magnitude is not None else None,
        "chroma_magnitude": round(float(chroma_magnitude or 0.0), 4),
    }


def texture_metric_read(
    clean_metrics: dict[str, Any],
    textured_metrics: dict[str, Any],
    *,
    brightness_correction: float = 0.0,
    preliminary_luma_yavg_delta: float | None = None,
) -> dict[str, Any]:
    clean_yavg = float(clean_metrics["yavg"])
    textured_yavg = float(textured_metrics["yavg"])
    luma_delta = textured_yavg - clean_yavg
    clean_chroma = float(clean_metrics.get("chroma_magnitude") or 0.0)
    textured_chroma = float(textured_metrics.get("chroma_magnitude") or 0.0)
    chroma_delta = textured_chroma - clean_chroma
    source_chroma_class = "monochrome" if clean_chroma <= MONOCHROME_CHROMA_MAGNITUDE_MAX else "color"
    luma_read = "pass" if abs(luma_delta) <= LUMA_YAVG_TOLERANCE else "fail"
    if source_chroma_class == "monochrome":
        fake_color_limit = max(clean_chroma + 0.5, MONOCHROME_CHROMA_MAGNITUDE_MAX + 0.5)
        chroma_read = "pass" if textured_chroma <= fake_color_limit else "fail"
        chroma_policy = "do_not_introduce_fake_color"
    else:
        chroma_read = "pass" if chroma_delta >= -0.25 else "fail"
        chroma_policy = "increase_or_preserve_source_chroma"
    return {
        "clean_metrics": clean_metrics,
        "textured_metrics": textured_metrics,
        "luma_yavg_delta": round(luma_delta, 4),
        "preliminary_luma_yavg_delta": round(preliminary_luma_yavg_delta, 4)
        if preliminary_luma_yavg_delta is not None
        else None,
        "luma_yavg_tolerance": LUMA_YAVG_TOLERANCE,
        "luma_neutral_read": luma_read,
        "source_chroma_class": source_chroma_class,
        "source_chroma_magnitude": round(clean_chroma, 4),
        "textured_chroma_magnitude": round(textured_chroma, 4),
        "chroma_delta": round(chroma_delta, 4),
        "chroma_policy": chroma_policy,
        "chroma_read": chroma_read,
        "brightness_correction": round(brightness_correction, 6),
        "overall_read": "pass" if luma_read == "pass" and chroma_read == "pass" else "fail",
    }


def scanline_visibility_from_image(
    image: Image.Image,
    *,
    scanline_period_pixels: int | None = None,
    scanline_band_pixels: int | None = None,
    scanline_delta_y: float | None = None,
    scanline_strength_variant_id: str | None = None,
) -> dict[str, Any]:
    luma = image.convert("L")
    width, height = luma.size
    period = int(scanline_period_pixels or VISIBLE_SCANLINE_PERIOD_PIXELS)
    band = max(1, min(int(scanline_band_pixels or VISIBLE_SCANLINE_BAND_PIXELS), max(1, period // 2)))
    light_offset = period // 2
    if width <= 0 or height <= period:
        return {
            "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
            "scanline_strength_variant_id": scanline_strength_variant_id or "pass07a_y6_baseline",
            "row_pair_count": 0,
            "signed_light_minus_dark_yavg": 0.0,
            "abs_pair_delta_yavg": 0.0,
            "scanline_visibility_read": "fail",
        }
    row_means: list[float] = []
    for y in range(height):
        row = luma.crop((0, y, width, y + 1))
        row_means.append(float(ImageStat.Stat(row).mean[0]))
    signed_deltas: list[float] = []
    abs_deltas: list[float] = []
    max_y = height - light_offset - band + 1
    for y in range(0, max(0, max_y), period):
        dark_mean = sum(row_means[y : y + band]) / band
        light_mean = sum(row_means[y + light_offset : y + light_offset + band]) / band
        delta = light_mean - dark_mean
        signed_deltas.append(delta)
        abs_deltas.append(abs(delta))
    signed_mean = sum(signed_deltas) / len(signed_deltas) if signed_deltas else 0.0
    abs_mean = sum(abs_deltas) / len(abs_deltas) if abs_deltas else 0.0
    return {
        "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
        "scanline_strength_variant_id": scanline_strength_variant_id or "pass07a_y6_baseline",
        "scanline_period_pixels": period,
        "scanline_band_pixels": band,
        "scanline_delta_rgb": VISIBLE_SCANLINE_DELTA_RGB,
        "scanline_delta_y": float(scanline_delta_y if scanline_delta_y is not None else VISIBLE_SCANLINE_DELTA_RGB),
        "row_pair_count": len(signed_deltas),
        "signed_light_minus_dark_yavg": round(signed_mean, 4),
        "abs_pair_delta_yavg": round(abs_mean, 4),
        "scanline_visibility_yavg_min": VISIBLE_SCANLINE_VISIBILITY_YAVG_MIN,
        "scanline_visibility_read": "pass"
        if signed_mean >= VISIBLE_SCANLINE_VISIBILITY_YAVG_MIN
        else "fail",
    }


def scanline_metric_read(
    video_path: Path,
    frame_dir: Path | None = None,
    frame_limit: int = 5,
    *,
    scanline_delta_y: float | None = None,
    scanline_strength_variant_id: str | None = None,
    scanline_period_pixels: int | None = None,
    scanline_band_pixels: int | None = None,
) -> dict[str, Any]:
    if frame_dir is None:
        frame_dir = video_path.with_name(video_path.stem + "__scanline_metric_frames")
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    video_duration = duration(video_path)
    if video_duration <= 0:
        return {
            "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
            "scanline_strength_variant_id": scanline_strength_variant_id or "pass07a_y6_baseline",
            "scanline_delta_y": float(scanline_delta_y if scanline_delta_y is not None else VISIBLE_SCANLINE_DELTA_RGB),
            "scanline_period_pixels": int(scanline_period_pixels or VISIBLE_SCANLINE_PERIOD_PIXELS),
            "scanline_band_pixels": int(scanline_band_pixels or VISIBLE_SCANLINE_BAND_PIXELS),
            "video_path": str(video_path),
            "sampled_frame_count": 0,
            "scanline_visibility_read": "fail",
            "blocked_reason": "zero_duration_video",
        }
    sample_count = max(1, frame_limit)
    times = [
        max(0.01, min(video_duration - (1.0 / TARGET_FPS), video_duration * ((idx + 1) / (sample_count + 1))))
        for idx in range(sample_count)
    ]
    frames: list[Path] = []
    frame_reads: list[dict[str, Any]] = []
    for idx, seconds in enumerate(times, start=1):
        frame = frame_dir / f"scanline_metric_{idx:02d}_{seconds:.3f}.png"
        extract_review_frame(video_path, seconds, frame)
        frames.append(frame)
        with Image.open(frame) as im:
            frame_reads.append(
                scanline_visibility_from_image(
                    im,
                    scanline_delta_y=scanline_delta_y,
                    scanline_strength_variant_id=scanline_strength_variant_id,
                    scanline_period_pixels=scanline_period_pixels,
                    scanline_band_pixels=scanline_band_pixels,
                )
            )
    signed_values = [float(item.get("signed_light_minus_dark_yavg") or 0.0) for item in frame_reads]
    abs_values = [float(item.get("abs_pair_delta_yavg") or 0.0) for item in frame_reads]
    signed_mean = sum(signed_values) / len(signed_values) if signed_values else 0.0
    abs_mean = sum(abs_values) / len(abs_values) if abs_values else 0.0
    return {
        "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
        "scanline_strength_variant_id": scanline_strength_variant_id or "pass07a_y6_baseline",
        "video_path": str(video_path),
        "sampled_frame_count": len(frame_reads),
        "frame_paths": [str(path) for path in frames],
        "scanline_period_pixels": int(scanline_period_pixels or VISIBLE_SCANLINE_PERIOD_PIXELS),
        "scanline_band_pixels": int(scanline_band_pixels or VISIBLE_SCANLINE_BAND_PIXELS),
        "scanline_delta_rgb": VISIBLE_SCANLINE_DELTA_RGB,
        "scanline_delta_y": float(scanline_delta_y if scanline_delta_y is not None else VISIBLE_SCANLINE_DELTA_RGB),
        "mean_signed_light_minus_dark_yavg": round(signed_mean, 4),
        "mean_abs_pair_delta_yavg": round(abs_mean, 4),
        "scanline_visibility_yavg_min": VISIBLE_SCANLINE_VISIBILITY_YAVG_MIN,
        "scanline_visibility_read": "pass"
        if signed_mean >= VISIBLE_SCANLINE_VISIBILITY_YAVG_MIN
        else "fail",
        "frames": frame_reads,
    }


def source_chroma_class(metrics: dict[str, Any]) -> str:
    return "monochrome" if float(metrics.get("chroma_magnitude") or 0.0) <= MONOCHROME_CHROMA_MAGNITUDE_MAX else "color"


def render_luma_neutral_chroma_texture(
    src: Path,
    out_path: Path,
    *,
    visible_scanline: bool = False,
    scanline_delta_y: float | None = None,
    scanline_period_pixels: int | None = None,
    scanline_band_pixels: int | None = None,
    scanline_strength_variant_id: str | None = None,
    enforce_metric_gate: bool = True,
) -> dict[str, Any]:
    variant_suffix = f"_{scanline_strength_variant_id}" if scanline_strength_variant_id else ""
    texture_suffix = (
        f"__pre_luma_neutral_chroma_visible_scanline{variant_suffix}"
        if visible_scanline
        else "__pre_luma_neutral_chroma"
    )
    pre_path = out_path.with_name(out_path.stem + texture_suffix + ".mp4")
    clean_metrics = signalstats_metrics(src)
    if source_chroma_class(clean_metrics) == "monochrome":
        if visible_scanline:
            graph = luma_neutral_monochrome_visible_scanline_filter_graph(
                profile_id=HOUSE_CRT_PROFILE_ID,
                strength=HOUSE_CRT_INTENSITY,
                width=TARGET_WIDTH,
                height=TARGET_HEIGHT,
                fps=float(TARGET_FPS),
                scanline_delta_y=scanline_delta_y,
                scanline_period_pixels=scanline_period_pixels,
                scanline_band_pixels=scanline_band_pixels,
            )
        else:
            graph = luma_neutral_monochrome_filter_graph(
                profile_id=HOUSE_CRT_PROFILE_ID,
                strength=HOUSE_CRT_INTENSITY,
                width=TARGET_WIDTH,
                height=TARGET_HEIGHT,
                fps=float(TARGET_FPS),
            )
        renderer_variant = (
            "luma_neutral_monochrome_visible_scanline_no_chroma_shift"
            if visible_scanline
            else "luma_neutral_monochrome_no_chroma_shift"
        )
    else:
        if visible_scanline:
            graph = luma_neutral_chroma_visible_scanline_filter_graph(
                profile_id=HOUSE_CRT_PROFILE_ID,
                strength=HOUSE_CRT_INTENSITY,
                width=TARGET_WIDTH,
                height=TARGET_HEIGHT,
                fps=float(TARGET_FPS),
                scanline_delta_y=scanline_delta_y,
                scanline_period_pixels=scanline_period_pixels,
                scanline_band_pixels=scanline_band_pixels,
            )
        else:
            graph = luma_neutral_chroma_filter_graph(
                profile_id=HOUSE_CRT_PROFILE_ID,
                strength=HOUSE_CRT_INTENSITY,
                width=TARGET_WIDTH,
                height=TARGET_HEIGHT,
                fps=float(TARGET_FPS),
            )
        renderer_variant = (
            "luma_neutral_color_chroma_separation_visible_scanline"
            if visible_scanline
            else "luma_neutral_color_chroma_separation"
        )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(TARGET_FPS),
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
            "-movflags",
            "+faststart",
            "-an",
            str(pre_path),
        ]
    )
    pre_metrics = signalstats_metrics(pre_path)
    preliminary_delta = float(pre_metrics["yavg"]) - float(clean_metrics["yavg"])
    brightness_correction = 0.0

    def apply_brightness_correction(input_path: Path, output_path: Path, correction: float) -> None:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(input_path),
                "-vf",
                f"eq=brightness={correction:.6f},setsar=1,format=yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(TARGET_FPS),
                "-color_primaries",
                "bt709",
                "-color_trc",
                "bt709",
                "-colorspace",
                "bt709",
                "-movflags",
                "+faststart",
                "-an",
                str(output_path),
            ]
        )

    if abs(preliminary_delta) <= LUMA_YAVG_TOLERANCE:
        shutil.copy2(pre_path, out_path)
    else:
        if abs(preliminary_delta) > MAX_LUMA_CORRECTION_YAVG:
            raise RuntimeError(
                f"{src}: luma-neutral compensation would require {preliminary_delta:.3f} YAVG, "
                f"beyond visible correction limit {MAX_LUMA_CORRECTION_YAVG:.3f}."
            )
        brightness_correction = -preliminary_delta / 255.0
        apply_brightness_correction(pre_path, out_path, brightness_correction)
    final_metrics = signalstats_metrics(out_path)
    correction_passes = 1 if abs(preliminary_delta) > LUMA_YAVG_TOLERANCE else 0
    for correction_index in range(2):
        final_delta = float(final_metrics["yavg"]) - float(clean_metrics["yavg"])
        if abs(final_delta) <= LUMA_YAVG_TOLERANCE:
            break
        next_correction = -final_delta / 255.0
        if abs(brightness_correction + next_correction) > (MAX_LUMA_CORRECTION_YAVG / 255.0):
            break
        corrected_path = out_path.with_name(out_path.stem + f"__luma_correction_{correction_index + 2}.mp4")
        apply_brightness_correction(out_path, corrected_path, next_correction)
        corrected_path.replace(out_path)
        brightness_correction += next_correction
        correction_passes += 1
        final_metrics = signalstats_metrics(out_path)
    metric_read = texture_metric_read(
        clean_metrics,
        final_metrics,
        brightness_correction=brightness_correction,
        preliminary_luma_yavg_delta=preliminary_delta,
    )
    metric_read["luma_correction_passes"] = correction_passes
    metric_read["renderer_variant"] = renderer_variant
    metric_read["texture_tone_policy"] = VISIBLE_SCANLINE_TONE_POLICY if visible_scanline else HOUSE_CRT_TONE_POLICY
    metric_read["calibration_recipe_id"] = (
        VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID if visible_scanline else CALIBRATION_RECIPE_ID
    )
    metric_read["texture_renderer_source"] = VISIBLE_SCANLINE_RENDERER_SOURCE if visible_scanline else TEXTURE_RENDERER_SOURCE
    metric_read["pre_texture_path"] = str(pre_path)
    metric_read["texture_path"] = str(out_path)
    if visible_scanline:
        metric_read["scanline_policy_id"] = VISIBLE_SCANLINE_POLICY_ID
        metric_read["scanline_strength_variant_id"] = scanline_strength_variant_id or "pass07a_y6_baseline"
        metric_read["scanline_delta_y"] = float(
            scanline_delta_y if scanline_delta_y is not None else VISIBLE_SCANLINE_DELTA_RGB
        )
        metric_read["scanline_period_pixels"] = int(scanline_period_pixels or VISIBLE_SCANLINE_PERIOD_PIXELS)
        metric_read["scanline_band_pixels"] = int(scanline_band_pixels or VISIBLE_SCANLINE_BAND_PIXELS)
        metric_read["black_only_scanline_overlay_used"] = False
        metric_read["zero_mean_horizontal_modulation"] = True
        metric_read["scanline_metrics"] = scanline_metric_read(
            out_path,
            out_path.with_name(out_path.stem + "__scanline_metrics_frames"),
            scanline_delta_y=scanline_delta_y,
            scanline_period_pixels=scanline_period_pixels,
            scanline_band_pixels=scanline_band_pixels,
            scanline_strength_variant_id=scanline_strength_variant_id,
        )
    if enforce_metric_gate and metric_read["overall_read"] != "pass":
        raise RuntimeError(
            f"{out_path}: luma-neutral chroma gate failed "
            f"(luma={metric_read['luma_yavg_delta']}, chroma_read={metric_read['chroma_read']})."
        )
    return metric_read


def render_challenger_contract_texture(src: Path, out_path: Path) -> Path:
    render_luma_neutral_chroma_texture(src, out_path)
    return out_path


def render_segment(
    source: Path,
    segment: Segment,
    out_path: Path,
    apply_signal: bool,
    *,
    visible_scanline: bool = False,
    scanline_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    source_segment_path = out_path.with_name(out_path.stem + "__source_segment_no_audio.mp4")
    clean_path = out_path.with_name(out_path.stem + "__conservative_clean.mp4")
    base_suffix = "__luma_neutral_chroma_visible_scanline_crt_base.mp4" if visible_scanline else "__luma_neutral_chroma_crt_base.mp4"
    base_path = out_path.with_name(out_path.stem + base_suffix)
    render_source_segment(source, segment, source_segment_path)
    render_historical_signal_conservative_clean(source_segment_path, clean_path)
    scanline_fields = scanline_contract_fields(scanline_spec) if visible_scanline else {}
    texture_metrics = render_luma_neutral_chroma_texture(
        clean_path,
        base_path,
        visible_scanline=visible_scanline,
        scanline_delta_y=scanline_fields.get("scanline_delta_y") if visible_scanline else None,
        scanline_period_pixels=scanline_fields.get("scanline_period_pixels") if visible_scanline else None,
        scanline_band_pixels=scanline_fields.get("scanline_band_pixels") if visible_scanline else None,
        scanline_strength_variant_id=scanline_fields.get("scanline_strength_variant_id") if visible_scanline else None,
    )
    texture_tone_policy = VISIBLE_SCANLINE_TONE_POLICY if visible_scanline else HOUSE_CRT_TONE_POLICY
    calibration_recipe_id = VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID if visible_scanline else CALIBRATION_RECIPE_ID
    texture_renderer_source = VISIBLE_SCANLINE_RENDERER_SOURCE if visible_scanline else TEXTURE_RENDERER_SOURCE
    base_read = {
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "texture_source_segment_path": str(source_segment_path),
        "texture_conservative_clean_path": str(clean_path),
        "texture_applied_path": str(base_path),
        "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
        "texture_tone_policy": texture_tone_policy,
        "calibration_recipe_id": calibration_recipe_id,
        "legacy_calibration_recipe_id": calibration_recipe_id,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "texture_renderer_source": texture_renderer_source,
        "texture_conservative_clean_source": TEXTURE_CONSERVATIVE_CLEAN_SOURCE,
        **scanline_fields,
        "texture_metrics": texture_metrics,
        "luma_neutral_read": texture_metrics["luma_neutral_read"],
        "chroma_read": texture_metrics["chroma_read"],
    }
    if not apply_signal or segment.duration <= SIGNAL_INTERRUPTION_DURATION_SECONDS + 0.05:
        base_path.replace(out_path)
        no_signal_read = dict(base_read)
        no_signal_metrics = dict(texture_metrics)
        no_signal_metrics["texture_path"] = str(out_path)
        no_signal_read["texture_applied_path"] = str(out_path)
        no_signal_read["texture_metrics"] = no_signal_metrics
        return {
            "segment_path": str(out_path),
            **no_signal_read,
            "signal_interruption_applied": False,
            "signal_interruption_profile_id": "none",
            "signal_interruption_duration_seconds": 0.0,
            "signal_interruption_render_meta": {"variant_config": {"variant_id": "none"}},
        }

    keep_duration = segment.duration - SIGNAL_INTERRUPTION_DURATION_SECONDS
    keep_path = out_path.with_name(out_path.stem + "__crt_keep.mp4")
    signal_path = out_path.with_name(out_path.stem + "__signal_tail.mp4")
    config = variant_config(segment.signal_seed or 1, segment.index)
    signal_meta = render_signal_tail_segment(
        base_path,
        signal_path,
        out_path.with_name(out_path.stem + "__signal_frames"),
        config,
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(base_path),
            "-t",
            f"{keep_duration:.6f}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "18",
            str(keep_path),
        ]
    )
    concat_path = out_path.with_suffix(".concat.txt")
    concat_path.write_text(
        f"file '{shell_escape_for_concat(keep_path)}'\nfile '{shell_escape_for_concat(signal_path)}'\n"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(out_path),
        ]
    )
    return {
        "segment_path": str(out_path),
        **base_read,
        "signal_interruption_applied": True,
        "signal_interruption_seed": segment.signal_seed,
        "signal_interruption_profile_id": SIGNAL_INTERRUPTION_PROFILE_ID,
        "signal_interruption_profile_source": SIGNAL_INTERRUPTION_PROFILE_SOURCE,
        "signal_interruption_strength": SIGNAL_INTERRUPTION_STRENGTH,
        "signal_interruption_timing": "final_0.25s_before_outgoing_cut",
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPTION_DURATION_SECONDS,
        "signal_interruption_render_meta": signal_meta,
        "full_frame_static_replacement_used": False,
    }


def concat_videos(paths: list[Path], out_path: Path) -> None:
    concat_path = out_path.with_suffix(".concat.txt")
    concat_path.write_text("".join(f"file '{shell_escape_for_concat(p)}'\n" for p in paths))
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(out_path),
        ]
    )


def trim_clip(src: Path, out: Path, start: float, seconds: float) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{max(0.0, start):.6f}",
            "-i",
            str(src),
            "-t",
            f"{seconds:.6f}",
            "-vf",
            f"fps={TARGET_FPS},scale={TARGET_WIDTH}:{TARGET_HEIGHT}:flags=lanczos,setsar=1,format=yuv420p",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(TARGET_FPS),
            "-movflags",
            "+faststart",
            str(out),
        ]
    )


def render_tail_from_source(
    tail_source: Path,
    seconds: float,
    out_path: Path,
    *,
    visible_scanline: bool = False,
    scanline_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    source_tail = out_path.with_name(out_path.stem + "__source_tail_no_audio.mp4")
    clean_tail = out_path.with_name(out_path.stem + "__conservative_clean.mp4")
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(tail_source),
            "-t",
            f"{seconds:.6f}",
            "-vf",
            (
                f"fps={TARGET_FPS},scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
                "force_original_aspect_ratio=increase,crop="
                f"{TARGET_WIDTH}:{TARGET_HEIGHT},setsar=1,format=yuv420p"
            ),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-r",
            str(TARGET_FPS),
            str(source_tail),
        ]
    )
    render_historical_signal_conservative_clean(source_tail, clean_tail)
    scanline_fields = scanline_contract_fields(scanline_spec) if visible_scanline else {}
    texture_metrics = render_luma_neutral_chroma_texture(
        clean_tail,
        out_path,
        visible_scanline=visible_scanline,
        scanline_delta_y=scanline_fields.get("scanline_delta_y") if visible_scanline else None,
        scanline_period_pixels=scanline_fields.get("scanline_period_pixels") if visible_scanline else None,
        scanline_band_pixels=scanline_fields.get("scanline_band_pixels") if visible_scanline else None,
        scanline_strength_variant_id=scanline_fields.get("scanline_strength_variant_id") if visible_scanline else None,
    )
    return {
        "texture_source_segment_path": str(source_tail),
        "texture_conservative_clean_path": str(clean_tail),
        "texture_applied_path": str(out_path),
        **scanline_fields,
        "texture_metrics": texture_metrics,
    }


def render_freeze_tail(source: Path, seconds: float, out_path: Path) -> None:
    src_dur = duration(source)
    seek = max(0.0, src_dur - 0.04)
    frames = max(1, int(math.ceil(seconds * TARGET_FPS)))
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{seek:.6f}",
            "-i",
            str(source),
            "-vf",
            f"select='eq(n\\,0)',loop=loop={frames}:size=1:start=0,setpts=N/{TARGET_FPS}/TB,scale={TARGET_WIDTH}:{TARGET_HEIGHT},setsar=1,format=yuv420p",
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "18",
            str(out_path),
        ]
    )


def match_final_duration(
    motion_path: Path,
    final_manifest: dict[str, Any],
    old_final: Path,
    work_dir: Path,
    *,
    visible_scanline: bool = False,
    scanline_spec: dict[str, Any] | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    current_duration = duration(motion_path)
    desired_duration = duration(old_final)
    append_seconds = desired_duration - current_duration
    tail_reads: list[dict[str, Any]] = []
    if append_seconds <= DRIFT_TOLERANCE_SECONDS:
        return motion_path, tail_reads

    pieces = [motion_path]
    remaining = append_seconds
    tail_source_val = final_manifest.get("source_motion_tail_path") or final_manifest.get("outputs", {}).get("source_motion_tail_path")
    if tail_source_val and Path(tail_source_val).exists():
        tail_source = Path(tail_source_val)
        tail_seconds = min(duration(tail_source), remaining)
        if tail_seconds > 0.05:
            tail_path = work_dir / "tail__house_crt_no_audio.mp4"
            tail_texture_read = render_tail_from_source(
                tail_source,
                tail_seconds,
                tail_path,
                visible_scanline=visible_scanline,
                scanline_spec=scanline_spec,
            )
            texture_tone_policy = VISIBLE_SCANLINE_TONE_POLICY if visible_scanline else HOUSE_CRT_TONE_POLICY
            calibration_recipe_id = VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID if visible_scanline else CALIBRATION_RECIPE_ID
            texture_renderer_source = VISIBLE_SCANLINE_RENDERER_SOURCE if visible_scanline else TEXTURE_RENDERER_SOURCE
            pieces.append(tail_path)
            remaining -= tail_seconds
            tail_reads.append(
                {
                    "type": "source_motion_tail",
                    "source_path": str(tail_source),
                    "seconds": tail_seconds,
                    "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
                    "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
                    "texture_tone_policy": texture_tone_policy,
                    "calibration_recipe_id": calibration_recipe_id,
                    "legacy_calibration_recipe_id": calibration_recipe_id,
                    "signal_texture_strength": HOUSE_CRT_INTENSITY,
                    "texture_renderer_source": texture_renderer_source,
                    **tail_texture_read,
                }
            )
    if remaining > 0.05:
        freeze_path = work_dir / "tail__final_frame_hold_no_audio.mp4"
        render_freeze_tail(pieces[-1], remaining, freeze_path)
        pieces.append(freeze_path)
        tail_reads.append({"type": "final_frame_hold", "seconds": remaining})
    if len(pieces) == 1:
        return motion_path, tail_reads
    out_path = work_dir / "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
    concat_videos(pieces, out_path)
    return out_path, tail_reads


def burn_captions(motion_path: Path, ass_path: Path, out_path: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(motion_path),
            "-vf",
            f"ass={ffmpeg_escape(ass_path)}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "16",
            str(out_path),
        ]
    )


def remux_final_audio(captioned_video: Path, old_final: Path, out_path: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(captioned_video),
            "-i",
            str(old_final),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-shortest",
            "-movflags",
            "+faststart",
            str(out_path),
        ]
    )


def make_frame_sheet(video_path: Path, times: list[float], out_path: Path) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame_dir = out_path.with_suffix("")
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    for idx, t in enumerate(times[:12], start=1):
        frame = frame_dir / f"frame_{idx:02d}_{t:.3f}.png"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{max(0.0, t):.6f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-pix_fmt",
                "rgb24",
                str(frame),
            ]
        )
        frames.append(frame)
    try:
        from PIL import Image, ImageDraw

        thumb_w, thumb_h = 270, 480
        cols = 3
        rows = math.ceil(len(frames) / cols) or 1
        sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 36)), "white")
        draw = ImageDraw.Draw(sheet)
        for i, frame in enumerate(frames):
            img = Image.open(frame).convert("RGB")
            img.thumbnail((thumb_w, thumb_h))
            x = (i % cols) * thumb_w
            y = (i // cols) * (thumb_h + 36)
            sheet.paste(img, (x + (thumb_w - img.width) // 2, y))
            draw.text((x + 8, y + thumb_h + 8), f"{times[i]:.3f}s", fill=(0, 0, 0))
        sheet.save(out_path, quality=92)
        return {"sheet_path": str(out_path), "frame_paths": [str(p) for p in frames]}
    except Exception as exc:  # noqa: BLE001 - optional review artifact should not stop the video pass.
        return {"sheet_path": None, "frame_paths": [str(p) for p in frames], "sheet_error": str(exc)}


def extract_review_frame(video_path: Path, seconds: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    safe_seconds = max(0.0, min(seconds, max(0.0, duration(video_path) - (1.0 / TARGET_FPS))))
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{safe_seconds:.6f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-pix_fmt",
            "rgb24",
            str(out_path),
        ]
    )
    if not out_path.exists():
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-sseof",
                "-0.100000",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-pix_fmt",
                "rgb24",
                str(out_path),
            ]
        )
    if not out_path.exists():
        raise RuntimeError(f"Failed to extract review frame from {video_path} at {seconds:.3f}s")


def make_challenger_style_cut_review_sheet(
    reads: list[dict[str, Any]],
    out_path: Path,
    frame_dir: Path,
) -> dict[str, Any]:
    affected = [idx for idx, item in enumerate(reads[:-1]) if item.get("signal_interruption_applied")]
    if not affected:
        return {"sheet_path": None, "frame_paths": [], "affected_cut_count": 0}
    frame_dir.mkdir(parents=True, exist_ok=True)
    label_w = 520
    thumb_w = 180
    thumb_h = 320
    gap = 12
    cols = [("out -0.30s", "out", -0.300), ("glitch -0.12s", "out", -0.120), ("glitch -0.03s", "out", -0.030), ("next +0.08s", "in", 0.080)]
    row_h = thumb_h + 34
    sheet = Image.new("RGB", (label_w + len(cols) * thumb_w + (len(cols) + 1) * gap, 62 + len(affected) * row_h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "House CRT Signal Interruption - Challenger-style cut review", fill=(255, 255, 255))
    for c, (name, _, _) in enumerate(cols):
        draw.text((label_w + gap + c * (thumb_w + gap), 24), name, fill=(215, 215, 215))
    frame_paths: list[Path] = []
    for row_i, idx in enumerate(affected):
        outgoing = reads[idx]
        incoming = reads[idx + 1]
        y = 62 + row_i * row_h
        render_meta = outgoing.get("signal_interruption_render_meta") or {}
        variant = (render_meta.get("variant_config") or {}).get("variant_id", "unknown")
        label = (
            f"cut {float(outgoing['timeline_out']):.3f}s\n"
            f"{int(outgoing['segment_index']):02d} {outgoing['source_row_id']} ->\n"
            f"{int(incoming['segment_index']):02d} {incoming['source_row_id']}\n"
            f"{variant}"
        )
        for line_i, line in enumerate(label.splitlines()):
            draw.text((16, y + 8 + line_i * 18), line, fill=(235, 235, 235))
        for c, (_, side, offset) in enumerate(cols):
            src = Path(outgoing["segment_path"]) if side == "out" else Path(incoming["segment_path"])
            src_dur = duration(src)
            t = max(0.01, min(src_dur - (1.0 / TARGET_FPS), src_dur + offset)) if side == "out" else offset
            frame = frame_dir / f"cut_{int(outgoing['segment_index']):02d}_col_{c + 1}_{t:.3f}.png"
            extract_review_frame(src, t, frame)
            frame_paths.append(frame)
            with Image.open(frame) as im:
                thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (label_w + gap + c * (thumb_w + gap), y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {"sheet_path": str(out_path), "frame_paths": [str(p) for p in frame_paths], "affected_cut_count": len(affected)}


def make_challenger_style_cut_review_reel(
    reads: list[dict[str, Any]],
    out_path: Path,
    tmp_dir: Path,
) -> dict[str, Any]:
    affected = [idx for idx, item in enumerate(reads[:-1]) if item.get("signal_interruption_applied")]
    if not affected:
        return {"reel_path": None, "affected_cut_count": 0, "snippet_paths": []}
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    for idx in affected:
        outgoing = reads[idx]
        incoming = reads[idx + 1]
        out_dur = duration(Path(outgoing["segment_path"]))
        tail = tmp_dir / f"{int(outgoing['segment_index']):02d}_tail.mp4"
        head = tmp_dir / f"{int(incoming['segment_index']):02d}_head.mp4"
        snippet = tmp_dir / f"{int(outgoing['segment_index']):02d}_to_{int(incoming['segment_index']):02d}.mp4"
        trim_clip(Path(outgoing["segment_path"]), tail, max(0.0, out_dur - 0.650), 0.650)
        trim_clip(Path(incoming["segment_path"]), head, 0.0, 0.450)
        concat_videos([tail, head], snippet)
        pieces.append(snippet)
    concat_videos(pieces, out_path)
    return {"reel_path": str(out_path), "affected_cut_count": len(affected), "snippet_paths": [str(p) for p in pieces]}


def luma_chroma_metrics_summary(
    reads: list[dict[str, Any]],
    tail_reads: list[dict[str, Any]],
    *,
    visible_scanline: bool = False,
    scanline_spec: dict[str, Any] | None = None,
    metrics_schema_version: str = PASS04_METRICS_SCHEMA_VERSION,
) -> dict[str, Any]:
    metrics = [item["texture_metrics"] for item in reads if isinstance(item.get("texture_metrics"), dict)]
    tail_metrics = [item["texture_metrics"] for item in tail_reads if isinstance(item.get("texture_metrics"), dict)]
    all_metrics = metrics + tail_metrics
    color_metrics = [item for item in all_metrics if item.get("source_chroma_class") == "color"]
    monochrome_metrics = [item for item in all_metrics if item.get("source_chroma_class") == "monochrome"]
    luma_failures = [item for item in all_metrics if item.get("luma_neutral_read") != "pass"]
    chroma_failures = [item for item in all_metrics if item.get("chroma_read") != "pass"]
    scanline_reads = [item.get("scanline_metrics") or {} for item in all_metrics if item.get("scanline_metrics")]
    scanline_failures = [item for item in scanline_reads if item.get("scanline_visibility_read") != "pass"]
    scanline_values = [float(item.get("mean_signed_light_minus_dark_yavg") or 0.0) for item in scanline_reads]
    max_abs_luma_delta = max((abs(float(item.get("luma_yavg_delta") or 0.0)) for item in all_metrics), default=0.0)
    min_color_chroma_delta = min((float(item.get("chroma_delta") or 0.0) for item in color_metrics), default=0.0)
    max_monochrome_chroma_delta = max((float(item.get("chroma_delta") or 0.0) for item in monochrome_metrics), default=0.0)
    payload = {
        "schema_version": metrics_schema_version,
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY if visible_scanline else HOUSE_CRT_TONE_POLICY,
        "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID if visible_scanline else CALIBRATION_RECIPE_ID,
        "luma_yavg_tolerance": LUMA_YAVG_TOLERANCE,
        "monochrome_chroma_magnitude_max": MONOCHROME_CHROMA_MAGNITUDE_MAX,
        "segment_count": len(metrics),
        "tail_metric_count": len(tail_metrics),
        "luma_neutral_segment_count": sum(1 for item in metrics if item.get("luma_neutral_read") == "pass"),
        "luma_neutral_all_count": sum(1 for item in all_metrics if item.get("luma_neutral_read") == "pass"),
        "max_abs_luma_yavg_delta": round(max_abs_luma_delta, 4),
        "color_segment_count": len([item for item in metrics if item.get("source_chroma_class") == "color"]),
        "color_all_count": len(color_metrics),
        "chroma_preserved_or_increased_count": sum(
            1 for item in color_metrics if item.get("chroma_read") == "pass"
        ),
        "min_color_chroma_delta": round(min_color_chroma_delta, 4),
        "monochrome_segment_count": len([item for item in metrics if item.get("source_chroma_class") == "monochrome"]),
        "monochrome_all_count": len(monochrome_metrics),
        "fake_color_reject_count": sum(1 for item in monochrome_metrics if item.get("chroma_read") == "pass"),
        "max_monochrome_chroma_delta": round(max_monochrome_chroma_delta, 4),
        "luma_failure_count": len(luma_failures),
        "chroma_failure_count": len(chroma_failures),
        "overall_read": "pass"
        if all_metrics and not luma_failures and not chroma_failures and (not visible_scanline or not scanline_failures)
        else "fail",
    }
    if visible_scanline:
        payload.update(
            {
                **scanline_contract_fields(scanline_spec),
                "scanline_metric_count": len(scanline_reads),
                "scanline_visibility_pass_count": sum(
                    1 for item in scanline_reads if item.get("scanline_visibility_read") == "pass"
                ),
                "scanline_failure_count": len(scanline_failures),
                "mean_scanline_yavg": round(sum(scanline_values) / len(scanline_values), 4)
                if scanline_values
                else 0.0,
                "min_scanline_yavg": round(min(scanline_values), 4) if scanline_values else 0.0,
            }
        )
    return payload


def challenger_luma_neutral_reference(
    run_id: str,
    *,
    visible_scanline: bool = False,
    scanline_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not CHALLENGER_TEXTURE_MANIFEST_PATH.exists():
        return {
            "status": "blocked",
            "blocked_reason": "missing_challenger_texture_manifest",
            "manifest_path": str(CHALLENGER_TEXTURE_MANIFEST_PATH),
        }
    source_manifest = load_json(CHALLENGER_TEXTURE_MANIFEST_PATH)
    items = source_manifest.get("items") or []
    reference_root_name = "luma_neutral_chroma_visible_scanline_reference" if visible_scanline else "luma_neutral_chroma_reference"
    reference_root = CHALLENGER_TEXTURE_MANIFEST_PATH.parent / reference_root_name / run_id
    reference_root.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    reads: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda x: int(x.get("order") or 0)):
        clean_path = Path(str(item.get("conservative_clean_path") or ""))
        if not clean_path.exists():
            continue
        order = int(item.get("order") or (len(rendered) + 1))
        out_label = "luma_neutral_chroma_visible_scanline" if visible_scanline else "luma_neutral_chroma"
        out_path = reference_root / f"challenger_{order:02d}__{out_label}.mp4"
        if out_path.exists():
            metric_read = texture_metric_read(signalstats_metrics(clean_path), signalstats_metrics(out_path))
            metric_read["texture_path"] = str(out_path)
        else:
            scanline_fields = scanline_contract_fields(scanline_spec) if visible_scanline else {}
            metric_read = render_luma_neutral_chroma_texture(
                clean_path,
                out_path,
                visible_scanline=visible_scanline,
                scanline_delta_y=scanline_fields.get("scanline_delta_y") if visible_scanline else None,
                scanline_period_pixels=scanline_fields.get("scanline_period_pixels") if visible_scanline else None,
                scanline_band_pixels=scanline_fields.get("scanline_band_pixels") if visible_scanline else None,
                scanline_strength_variant_id=scanline_fields.get("scanline_strength_variant_id") if visible_scanline else None,
            )
        rendered.append(out_path)
        reads.append(
            {
                "order": order,
                "shot_id": item.get("shot_id", ""),
                "conservative_clean_path": str(clean_path),
                "texture_applied_path": str(out_path),
                "texture_metrics": metric_read,
            }
        )
    if not rendered:
        return {"status": "blocked", "blocked_reason": "no_usable_challenger_reference_clips"}
    video_name = (
        "challenger_luma_neutral_chroma_visible_scanline_reference_no_audio.mp4"
        if visible_scanline
        else "challenger_luma_neutral_chroma_reference_no_audio.mp4"
    )
    video_path = reference_root / video_name
    if not video_path.exists():
        concat_videos(rendered, video_path)
    metrics_summary = luma_chroma_metrics_summary(
        [
            {
                "texture_metrics": read["texture_metrics"],
            }
            for read in reads
        ],
        [],
        visible_scanline=visible_scanline,
        scanline_spec=scanline_spec,
        metrics_schema_version=PASS07_METRICS_SCHEMA_VERSION if visible_scanline else PASS04_METRICS_SCHEMA_VERSION,
    )
    manifest_name = (
        f"{run_id}__challenger_luma_neutral_chroma_visible_scanline_reference_manifest.json"
        if visible_scanline
        else f"{run_id}__challenger_luma_neutral_chroma_reference_manifest.json"
    )
    manifest_path = reference_root / manifest_name
    texture_tone_policy = VISIBLE_SCANLINE_TONE_POLICY if visible_scanline else HOUSE_CRT_TONE_POLICY
    calibration_recipe_id = VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID if visible_scanline else CALIBRATION_RECIPE_ID
    texture_renderer_source = VISIBLE_SCANLINE_RENDERER_SOURCE if visible_scanline else TEXTURE_RENDERER_SOURCE
    payload = {
        "schema_version": "challenger_luma_neutral_chroma_visible_scanline_reference_v1"
        if visible_scanline
        else "challenger_luma_neutral_chroma_reference_v1",
        "created_at": run_id,
        "status": "review_reference",
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "house_crt_contract_read": visible_scanline_contract_read() if visible_scanline else contract_read(),
        "visual_layer_order_read": {
            **visual_layer_order_read(),
            "caption_burn_is_last_visual_operation": "not_applicable_reference_no_captions",
        },
        "source_manifest_path": str(CHALLENGER_TEXTURE_MANIFEST_PATH),
        "reference_video_path": str(video_path),
        "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
        "texture_tone_policy": texture_tone_policy,
        "calibration_recipe_id": calibration_recipe_id,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "texture_renderer_source": texture_renderer_source,
        **(scanline_contract_fields(scanline_spec) if visible_scanline else {}),
        "metrics_summary": metrics_summary,
        "items": reads,
    }
    write_json(manifest_path, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload


def make_challenger_contract_comparison_sheet(
    video_path: Path,
    out_path: Path,
    frame_dir: Path,
    reference_video_path: Path,
) -> dict[str, Any]:
    if not reference_video_path.exists():
        return {
            "sheet_path": None,
            "frame_paths": [],
            "reference_video_path": str(reference_video_path),
            "sheet_error": "missing_challenger_luma_neutral_reference_video",
        }
    frame_dir.mkdir(parents=True, exist_ok=True)
    samples = [0.12, 0.28, 0.44, 0.60, 0.76]
    challenger_duration = duration(reference_video_path)
    target_duration = duration(video_path)
    frame_paths: list[Path] = []
    rows: list[tuple[Path, Path, str]] = []
    for idx, pct in enumerate(samples, start=1):
        challenger_time = max(0.01, min(challenger_duration - (1.0 / TARGET_FPS), challenger_duration * pct))
        target_time = max(0.01, min(target_duration - (1.0 / TARGET_FPS), target_duration * pct))
        challenger_frame = frame_dir / f"challenger_ref_{idx:02d}_{challenger_time:.3f}.png"
        target_frame = frame_dir / f"target_{idx:02d}_{target_time:.3f}.png"
        extract_review_frame(reference_video_path, challenger_time, challenger_frame)
        extract_review_frame(video_path, target_time, target_frame)
        frame_paths.extend([challenger_frame, target_frame])
        rows.append((challenger_frame, target_frame, f"{pct:.0%} timeline"))

    thumb_w, thumb_h = 270, 480
    label_h = 42
    sheet = Image.new("RGB", (thumb_w * 2 + 36, label_h + len(rows) * (thumb_h + 34)), (12, 12, 12))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), "Challenger luma-neutral ref", fill=(235, 235, 235))
    draw.text((thumb_w + 24, 12), "Current target contract", fill=(235, 235, 235))
    for row_i, (challenger_frame, target_frame, label) in enumerate(rows):
        y = label_h + row_i * (thumb_h + 34)
        with Image.open(challenger_frame) as im:
            sheet.paste(im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (12, y))
        with Image.open(target_frame) as im:
            sheet.paste(im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (thumb_w + 24, y))
        draw.text((12, y + thumb_h + 8), label, fill=(220, 220, 220))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "sheet_path": str(out_path),
        "frame_paths": [str(p) for p in frame_paths],
        "reference_video_path": str(reference_video_path),
        "comparison_policy": "normalized_timeline_challenger_luma_neutral_reference_vs_target_contract",
    }


def load_pass03_manifest(target: str) -> dict[str, Any] | None:
    if not PASS03_SUMMARY_PATH.exists():
        return None
    summary = load_json(PASS03_SUMMARY_PATH)
    for result in summary.get("results", []):
        if result.get("target") == target and result.get("manifest_path"):
            path = Path(result["manifest_path"])
            if path.exists():
                manifest = load_json(path)
                manifest["manifest_path"] = str(path)
                return manifest
    return None


def load_pass05_manifest(target: str) -> dict[str, Any] | None:
    if not PASS05_SUMMARY_PATH.exists():
        return None
    summary = load_json(PASS05_SUMMARY_PATH)
    for result in summary.get("results", []):
        if result.get("target") == target and result.get("manifest_path"):
            path = Path(result["manifest_path"])
            if path.exists():
                manifest = load_json(path)
                manifest["manifest_path"] = str(path)
                return manifest
    return None


def make_clean_texture_comparison_sheet(
    contract_reads: list[dict[str, Any]],
    pass03_manifest: dict[str, Any] | None,
    out_path: Path,
    frame_dir: Path,
) -> dict[str, Any]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    pass03_by_index = {
        int(item.get("segment_index")): item
        for item in (pass03_manifest or {}).get("segments", [])
        if item.get("segment_index") is not None
    }
    rows = contract_reads[:8]
    if not rows:
        return {"sheet_path": None, "frame_paths": [], "sheet_error": "no_contract_segments"}
    thumb_w, thumb_h = 210, 374
    label_w = 260
    gap = 10
    header_h = 54
    row_h = thumb_h + 48
    columns = ["clean source", "pass03 dark ref", "new contract"]
    sheet = Image.new(
        "RGB",
        (label_w + len(columns) * thumb_w + (len(columns) + 1) * gap, header_h + len(rows) * row_h),
        (12, 12, 12),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 16), "Clean vs texture comparison", fill=(245, 245, 245))
    for c, label in enumerate(columns):
        draw.text((label_w + gap + c * (thumb_w + gap), 18), label, fill=(225, 225, 225))
    frame_paths: list[Path] = []
    for row_i, read in enumerate(rows):
        seg_index = int(read["segment_index"])
        y = header_h + row_i * row_h
        metric = read.get("texture_metrics") or {}
        label_lines = [
            f"{seg_index:02d} {read.get('source_row_id', '')}",
            f"Y delta {float(metric.get('luma_yavg_delta') or 0.0):+.2f}",
            f"Chroma {float(metric.get('chroma_delta') or 0.0):+.2f}",
        ]
        for line_i, line in enumerate(label_lines):
            draw.text((16, y + 12 + line_i * 18), line, fill=(230, 230, 230))
        pass03_read = pass03_by_index.get(seg_index, {})
        sources = [
            Path(read["texture_conservative_clean_path"]),
            Path(str(pass03_read.get("texture_applied_path") or read["texture_applied_path"])),
            Path(read["texture_applied_path"]),
        ]
        for c, src in enumerate(sources):
            frame = frame_dir / f"segment_{seg_index:02d}_col_{c + 1}.png"
            extract_review_frame(src, max(0.01, min(0.45, duration(src) / 2)), frame)
            frame_paths.append(frame)
            with Image.open(frame) as im:
                thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (label_w + gap + c * (thumb_w + gap), y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "sheet_path": str(out_path),
        "frame_paths": [str(p) for p in frame_paths],
        "comparison_policy": "clean_source_vs_pass03_darkening_reference_vs_luma_neutral_contract",
        "pass03_manifest_path": pass03_manifest.get("manifest_path", "") if pass03_manifest else "",
    }


def make_clean_pass05_pass06_lineage_comparison_sheet(
    contract_reads: list[dict[str, Any]],
    pass05_manifest: dict[str, Any] | None,
    pass06_final: Path,
    out_path: Path,
    frame_dir: Path,
) -> dict[str, Any]:
    pass05_final_text = (pass05_manifest or {}).get("outputs", {}).get("captioned_final_path") or (
        pass05_manifest or {}
    ).get("captioned_final_path")
    pass05_final = Path(str(pass05_final_text)) if pass05_final_text else None
    if pass05_final is None or not pass05_final.exists():
        return {
            "sheet_path": None,
            "frame_paths": [],
            "sheet_error": "missing_pass05_diagnostic_final",
            "pass05_manifest_path": pass05_manifest.get("manifest_path", "") if pass05_manifest else "",
        }
    frame_dir.mkdir(parents=True, exist_ok=True)
    samples = [0.10, 0.25, 0.42, 0.60, 0.78]
    pass06_duration = duration(pass06_final)
    thumb_w, thumb_h = 210, 374
    label_w = 250
    gap = 10
    header_h = 54
    row_h = thumb_h + 44
    columns = ["clean source", "pass05 diagnostic", "pass06 clean-lineage"]
    sheet = Image.new(
        "RGB",
        (label_w + len(columns) * thumb_w + (len(columns) + 1) * gap, header_h + len(samples) * row_h),
        (12, 12, 12),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 16), "Clean source vs pass05 vs pass06", fill=(245, 245, 245))
    for c, label in enumerate(columns):
        draw.text((label_w + gap + c * (thumb_w + gap), 18), label, fill=(225, 225, 225))
    frame_paths: list[Path] = []
    for row_i, pct in enumerate(samples, start=1):
        absolute_time = max(0.01, min(pass06_duration - (1.0 / TARGET_FPS), pass06_duration * pct))
        clean_read = next(
            (
                read
                for read in contract_reads
                if float(read.get("timeline_in") or 0.0) <= absolute_time < float(read.get("timeline_out") or 0.0)
            ),
            contract_reads[min(row_i - 1, len(contract_reads) - 1)] if contract_reads else None,
        )
        if not clean_read:
            continue
        local_time = max(0.01, absolute_time - float(clean_read.get("timeline_in") or 0.0))
        y = header_h + (row_i - 1) * row_h
        label_lines = [
            f"{pct:.0%} timeline",
            f"{clean_read.get('source_row_id', '')}",
        ]
        for line_i, line in enumerate(label_lines):
            draw.text((16, y + 12 + line_i * 18), line, fill=(230, 230, 230))
        sources = [
            (Path(clean_read["texture_conservative_clean_path"]), local_time),
            (pass05_final, absolute_time),
            (pass06_final, absolute_time),
        ]
        for c, (src, seconds) in enumerate(sources):
            frame = frame_dir / f"row_{row_i:02d}_col_{c + 1}_{seconds:.3f}.png"
            extract_review_frame(src, seconds, frame)
            frame_paths.append(frame)
            with Image.open(frame) as im:
                thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (label_w + gap + c * (thumb_w + gap), y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "sheet_path": str(out_path),
        "frame_paths": [str(p) for p in frame_paths],
        "comparison_policy": "clean_source_vs_pass05_diagnostic_vs_pass06_clean_source_lineage",
        "pass05_manifest_path": pass05_manifest.get("manifest_path", "") if pass05_manifest else "",
        "pass05_captioned_final_path": str(pass05_final),
    }


def select_calibration_segments(
    segment_plan: list[tuple[Segment, Path, float, float]],
    max_samples: int = 3,
) -> list[tuple[Segment, Path, float, float]]:
    eligible = [item for item in segment_plan if item[0].duration >= 0.85]
    if not eligible:
        eligible = segment_plan[:]
    if len(eligible) <= max_samples:
        return eligible
    raw_indices = [0, len(eligible) // 2, len(eligible) - 1]
    chosen: list[int] = []
    for idx in raw_indices:
        if idx not in chosen:
            chosen.append(idx)
    cursor = 0
    while len(chosen) < max_samples and cursor < len(eligible):
        if cursor not in chosen:
            chosen.append(cursor)
        cursor += 1
    return [eligible[idx] for idx in sorted(chosen[:max_samples])]


def render_signal_sample_from_textured_segment(
    textured_path: Path,
    out_path: Path,
    work_dir: Path,
    seed: int,
    order: int,
) -> dict[str, Any]:
    sample_duration = duration(textured_path)
    if sample_duration <= SIGNAL_INTERRUPTION_DURATION_SECONDS + 0.05:
        shutil.copy2(textured_path, out_path)
        return {
            "signal_interruption_applied": False,
            "signal_interruption_duration_seconds": 0.0,
            "signal_interruption_render_meta": {"variant_config": {"variant_id": "none"}},
        }
    keep_duration = sample_duration - SIGNAL_INTERRUPTION_DURATION_SECONDS
    keep_path = work_dir / f"{out_path.stem}__keep.mp4"
    signal_path = work_dir / f"{out_path.stem}__signal_tail.mp4"
    config = variant_config(seed, order)
    signal_render_meta = render_signal_tail_segment(
        textured_path,
        signal_path,
        work_dir / f"{out_path.stem}__signal_frames",
        config,
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(textured_path),
            "-t",
            f"{keep_duration:.6f}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "18",
            str(keep_path),
        ]
    )
    concat_videos([keep_path, signal_path], out_path)
    return {
        "signal_interruption_applied": True,
        "signal_interruption_seed": seed,
        "signal_interruption_profile_id": SIGNAL_INTERRUPTION_PROFILE_ID,
        "signal_interruption_profile_source": SIGNAL_INTERRUPTION_PROFILE_SOURCE,
        "signal_interruption_strength": SIGNAL_INTERRUPTION_STRENGTH,
        "signal_interruption_timing": "final_0.25s_before_outgoing_cut",
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPTION_DURATION_SECONDS,
        "signal_interruption_render_meta": signal_render_meta,
        "full_frame_static_replacement_used": False,
    }


def make_visible_scanline_calibration_sheet(
    sample_reads: list[dict[str, Any]],
    out_path: Path,
    frame_dir: Path,
) -> dict[str, Any]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    rows = sample_reads[:3]
    if not rows:
        return {"sheet_path": None, "frame_paths": [], "sheet_error": "no_calibration_samples"}
    thumb_w, thumb_h = 210, 374
    label_w = 260
    gap = 10
    header_h = 58
    row_h = thumb_h + 52
    columns = ["clean source", "pass06", "pass07a visible lines"]
    sheet = Image.new(
        "RGB",
        (label_w + len(columns) * thumb_w + (len(columns) + 1) * gap, header_h + len(rows) * row_h),
        (12, 12, 12),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 16), "Visible scanline calibration", fill=(245, 245, 245))
    for c, label in enumerate(columns):
        draw.text((label_w + gap + c * (thumb_w + gap), 18), label, fill=(225, 225, 225))
    frame_paths: list[Path] = []
    for row_i, read in enumerate(rows):
        y = header_h + row_i * row_h
        sample_duration = float(read.get("sample_duration_seconds") or 0.0)
        frame_second = max(0.01, min(0.70, sample_duration / 2))
        metrics = read.get("pass07a_texture_metrics") or {}
        scanline_metrics = read.get("pass07a_scanline_metrics") or {}
        label_lines = [
            f"{int(read['sample_index']):02d} {read.get('source_row_id', '')}",
            f"Y delta {float(metrics.get('luma_yavg_delta') or 0.0):+.2f}",
            f"Line {float(scanline_metrics.get('mean_signed_light_minus_dark_yavg') or 0.0):+.2f}",
        ]
        for line_i, line in enumerate(label_lines):
            draw.text((16, y + 12 + line_i * 18), line, fill=(230, 230, 230))
        sources = [
            Path(read["conservative_clean_sample_path"]),
            Path(read["pass06_sample_path"]),
            Path(read["pass07a_sample_path"]),
        ]
        for c, src in enumerate(sources):
            frame = frame_dir / f"sample_{int(read['sample_index']):02d}_col_{c + 1}.png"
            extract_review_frame(src, frame_second, frame)
            frame_paths.append(frame)
            with Image.open(frame) as im:
                thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (label_w + gap + c * (thumb_w + gap), y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "sheet_path": str(out_path),
        "frame_paths": [str(path) for path in frame_paths],
        "comparison_policy": "clean_source_vs_pass06_luma_neutral_vs_pass07a_visible_scanline",
    }


def make_scanline_closeup_sheet(
    sample_reads: list[dict[str, Any]],
    out_path: Path,
    frame_dir: Path,
) -> dict[str, Any]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    rows = sample_reads[:3]
    if not rows:
        return {"sheet_path": None, "frame_paths": [], "sheet_error": "no_calibration_samples"}
    crop_w, crop_h = 360, 260
    thumb_w, thumb_h = 360, 260
    label_w = 210
    gap = 12
    header_h = 58
    row_h = thumb_h + 48
    columns = ["pass06 crop", "pass07a crop"]
    sheet = Image.new(
        "RGB",
        (label_w + len(columns) * thumb_w + (len(columns) + 1) * gap, header_h + len(rows) * row_h),
        (12, 12, 12),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 16), "Scanline close-up", fill=(245, 245, 245))
    for c, label in enumerate(columns):
        draw.text((label_w + gap + c * (thumb_w + gap), 18), label, fill=(225, 225, 225))
    frame_paths: list[Path] = []
    for row_i, read in enumerate(rows):
        y = header_h + row_i * row_h
        sample_duration = float(read.get("sample_duration_seconds") or 0.0)
        frame_second = max(0.01, min(0.70, sample_duration / 2))
        scanline_metrics = read.get("pass07a_scanline_metrics") or {}
        label_lines = [
            f"{int(read['sample_index']):02d}",
            f"Line {float(scanline_metrics.get('mean_signed_light_minus_dark_yavg') or 0.0):+.2f}",
        ]
        for line_i, line in enumerate(label_lines):
            draw.text((16, y + 12 + line_i * 18), line, fill=(230, 230, 230))
        for c, key in enumerate(("pass06_sample_path", "pass07a_sample_path")):
            source = Path(read[key])
            frame = frame_dir / f"sample_{int(read['sample_index']):02d}_{key}.png"
            extract_review_frame(source, frame_second, frame)
            frame_paths.append(frame)
            with Image.open(frame) as im:
                img = im.convert("RGB")
                left = max(0, (img.width - crop_w) // 2)
                top = max(0, int(img.height * 0.42) - crop_h // 2)
                crop = img.crop((left, top, min(img.width, left + crop_w), min(img.height, top + crop_h)))
                crop = crop.resize((thumb_w, thumb_h), Image.Resampling.NEAREST)
            sheet.paste(crop, (label_w + gap + c * (thumb_w + gap), y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=95)
    return {
        "sheet_path": str(out_path),
        "frame_paths": [str(path) for path in frame_paths],
        "comparison_policy": "center_crop_pass06_vs_pass07a_visible_scanline_nearest_neighbor",
    }


def summarize_visible_scanline_calibration(sample_reads: list[dict[str, Any]]) -> dict[str, Any]:
    luma_deltas = [
        abs(float((item.get("pass07a_texture_metrics") or {}).get("luma_yavg_delta") or 0.0))
        for item in sample_reads
    ]
    pass06_scanlines = [
        float((item.get("pass06_scanline_metrics") or {}).get("mean_signed_light_minus_dark_yavg") or 0.0)
        for item in sample_reads
    ]
    pass07a_scanlines = [
        float((item.get("pass07a_scanline_metrics") or {}).get("mean_signed_light_minus_dark_yavg") or 0.0)
        for item in sample_reads
    ]
    pass07a_metrics = [item.get("pass07a_texture_metrics") or {} for item in sample_reads]
    scanline_failures = [
        item for item in sample_reads if (item.get("pass07a_scanline_metrics") or {}).get("scanline_visibility_read") != "pass"
    ]
    metric_failures = [item for item in pass07a_metrics if item.get("overall_read") != "pass"]
    return {
        "schema_version": PASS07A_METRICS_SCHEMA_VERSION,
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY,
        "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
        "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "luma_yavg_tolerance": LUMA_YAVG_TOLERANCE,
        "scanline_visibility_yavg_min": VISIBLE_SCANLINE_VISIBILITY_YAVG_MIN,
        "sample_count": len(sample_reads),
        "max_abs_luma_yavg_delta": round(max(luma_deltas), 4) if luma_deltas else 0.0,
        "mean_pass06_scanline_yavg": round(sum(pass06_scanlines) / len(pass06_scanlines), 4)
        if pass06_scanlines
        else 0.0,
        "mean_pass07a_scanline_yavg": round(sum(pass07a_scanlines) / len(pass07a_scanlines), 4)
        if pass07a_scanlines
        else 0.0,
        "mean_scanline_gain_over_pass06_yavg": round(
            (sum(pass07a_scanlines) / len(pass07a_scanlines) if pass07a_scanlines else 0.0)
            - (sum(pass06_scanlines) / len(pass06_scanlines) if pass06_scanlines else 0.0),
            4,
        ),
        "scanline_failure_count": len(scanline_failures),
        "luma_chroma_failure_count": len(metric_failures),
        "overall_read": "pass" if sample_reads and not scanline_failures and not metric_failures else "fail",
    }


def build_visible_scanline_calibration_target(target: str, final_manifest_path: Path, run_id: str) -> dict[str, Any]:
    final_manifest = load_json(final_manifest_path)
    source_proof_path = resolve_source_proof(target, final_manifest)
    blocked_base = {
        "target": target,
        "source_final_export_manifest_path": str(final_manifest_path),
        "created_at": run_id,
        "disposition": "blocked",
        "pass_id": VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
    }
    if source_proof_path is None or not source_proof_path.exists():
        return {**blocked_base, "blocked_reason": "missing_source_proof_manifest_path"}

    proof_manifest = load_json(source_proof_path)
    clean_source_plan = resolve_clean_source_plan(target, source_proof_path, proof_manifest)
    if clean_source_plan.source_lineage_read.get("clean_source_confirmed") is not True:
        return {
            **blocked_base,
            "source_proof_manifest_path": str(source_proof_path),
            "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "blocked_reason": "clean_source_lineage_not_confirmed",
        }
    selected_segments = select_calibration_segments(clean_source_plan.segment_plan)
    if not selected_segments:
        return {
            **blocked_base,
            "source_proof_manifest_path": str(source_proof_path),
            "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "blocked_reason": "missing_usable_clean_story_segments",
        }

    slug = target_slug(final_manifest, target)
    proof_dir = clean_source_plan.clean_source_proof_path.parent
    output_root = proof_dir / "final_exports" / f"{slug}_{VISIBLE_SCANLINE_CALIBRATION_PASS_ID}" / run_id
    work_dir = output_root / "work"
    sample_dir = work_dir / "samples"
    review_dir = output_root / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / f"{run_id}__visible_scanline_calibration_manifest.json"
    if manifest_path.exists():
        existing_manifest = load_json(manifest_path)
        if existing_manifest.get("disposition") == "review_ready" and existing_manifest.get("pass_id") == VISIBLE_SCANLINE_CALIBRATION_PASS_ID:
            existing_manifest["manifest_path"] = str(manifest_path)
            return existing_manifest

    sample_reads: list[dict[str, Any]] = []
    pass07a_samples: list[Path] = []
    signal_samples: list[Path] = []
    rng = random.Random(f"{target}:{run_id}:{VISIBLE_SCANLINE_POLICY_ID}")
    for sample_index, (segment, segment_source, timeline_in, timeline_out) in enumerate(selected_segments, start=1):
        sample_seconds = min(2.0, max(0.10, segment.duration))
        sample_segment = Segment(
            index=sample_index,
            start=segment.start,
            end=min(segment.end, segment.start + sample_seconds),
            source_row_id=segment.source_row_id,
        )
        sample_root = sample_dir / f"{sample_index:02d}_{sample_segment.source_row_id}"
        sample_root.mkdir(parents=True, exist_ok=True)
        source_sample = sample_root / f"{sample_index:02d}__source_no_audio.mp4"
        clean_sample = sample_root / f"{sample_index:02d}__conservative_clean.mp4"
        pass06_sample = sample_root / f"{sample_index:02d}__pass06_luma_neutral_chroma.mp4"
        pass07a_sample = sample_root / f"{sample_index:02d}__pass07a_visible_scanline.mp4"
        signal_sample = sample_root / f"{sample_index:02d}__pass07a_visible_scanline_signal_tail.mp4"
        render_source_segment(segment_source, sample_segment, source_sample)
        render_historical_signal_conservative_clean(source_sample, clean_sample)
        pass06_metrics = render_luma_neutral_chroma_texture(clean_sample, pass06_sample)
        pass07a_metrics = render_luma_neutral_chroma_texture(clean_sample, pass07a_sample, visible_scanline=True)
        pass06_scanline = scanline_metric_read(pass06_sample, sample_root / "pass06_scanline_metric_frames")
        pass07a_scanline = pass07a_metrics.get("scanline_metrics") or scanline_metric_read(
            pass07a_sample,
            sample_root / "pass07a_scanline_metric_frames",
        )
        signal_meta = render_signal_sample_from_textured_segment(
            pass07a_sample,
            signal_sample,
            sample_root / "signal_tail_work",
            rng.randint(1000, 999999),
            sample_index,
        )
        pass07a_samples.append(pass07a_sample)
        signal_samples.append(signal_sample)
        sample_reads.append(
            {
                "sample_index": sample_index,
                "source_row_id": sample_segment.source_row_id,
                "segment_source_path": str(segment_source),
                "timeline_in": timeline_in,
                "timeline_out": timeline_out,
                "sample_source_start": sample_segment.start,
                "sample_source_end": sample_segment.end,
                "sample_duration_seconds": sample_segment.duration,
                "source_sample_path": str(source_sample),
                "conservative_clean_sample_path": str(clean_sample),
                "pass06_sample_path": str(pass06_sample),
                "pass07a_sample_path": str(pass07a_sample),
                "pass07a_signal_sample_path": str(signal_sample),
                "pass06_texture_metrics": pass06_metrics,
                "pass07a_texture_metrics": pass07a_metrics,
                "pass06_scanline_metrics": pass06_scanline,
                "pass07a_scanline_metrics": pass07a_scanline,
                "signal_interruption_sample_read": signal_meta,
            }
        )

    sample_reel = review_dir / f"{slug}__pass07a_visible_scanline_sample_reel_no_audio.mp4"
    signal_reel = review_dir / f"{slug}__pass07a_visible_scanline_signal_tail_sample_reel_no_audio.mp4"
    concat_videos(pass07a_samples, sample_reel)
    concat_videos(signal_samples, signal_reel)
    comparison_sheet = make_visible_scanline_calibration_sheet(
        sample_reads,
        review_dir / f"{slug}__clean_pass06_pass07a_visible_scanline_comparison_sheet.jpg",
        review_dir / f"{slug}__clean_pass06_pass07a_visible_scanline_comparison_frames",
    )
    closeup_sheet = make_scanline_closeup_sheet(
        sample_reads,
        review_dir / f"{slug}__pass06_pass07a_scanline_closeup_sheet.jpg",
        review_dir / f"{slug}__pass06_pass07a_scanline_closeup_frames",
    )
    metrics_read = summarize_visible_scanline_calibration(sample_reads)
    sample_streams = stream_counts(sample_reel)
    signal_streams = stream_counts(signal_reel)
    sample_video = video_stream(sample_reel)
    qa = {
        "sample_reel_geometry_9x16_read": "pass"
        if int(sample_video.get("width", 0)) == TARGET_WIDTH and int(sample_video.get("height", 0)) == TARGET_HEIGHT
        else "fail",
        "sample_reel_audio_stream_count": sample_streams["audio"],
        "sample_reel_audio_read": "pass" if sample_streams["audio"] == 0 else "fail",
        "signal_sample_reel_audio_stream_count": signal_streams["audio"],
        "signal_sample_reel_audio_read": "pass" if signal_streams["audio"] == 0 else "fail",
        "luma_scanline_metrics_read": metrics_read["overall_read"],
    }
    metrics_manifest_path = output_root / f"{run_id}__visible_scanline_metrics_manifest.json"
    manifest = {
        "schema_version": PASS07A_SCHEMA_VERSION,
        "target": target,
        "episode_slug": slug,
        "created_at": run_id,
        "disposition": "review_ready",
        "pass_id": VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
        "calibration_only": True,
        "full_first8_render_deferred_until_review": True,
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "house_crt_contract_read": visible_scanline_contract_read(),
        "supersedes_pass_id": CORRECTED_PASS_ID,
        "supersedes_status": "diagnostic_only_until_human_review",
        "source_final_export_manifest_path": str(final_manifest_path),
        "source_proof_manifest_path": str(source_proof_path),
        "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
        "source_lineage_read": clean_source_plan.source_lineage_read,
        "visual_layer_order_read": {
            **visual_layer_order_read(),
            "caption_burn_is_last_visual_operation": "not_applicable_calibration_no_captions",
            "post_caption_visual_effects_applied": False,
        },
        "house_crt_texture_read": {
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "profile_id": HOUSE_CRT_PROFILE_ID,
            "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
            "intensity": HOUSE_CRT_INTENSITY,
            "signal_texture_strength": HOUSE_CRT_INTENSITY,
            "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY,
            "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
            "legacy_calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
            "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
            "texture_renderer_source": VISIBLE_SCANLINE_RENDERER_SOURCE,
            "texture_conservative_clean_source": TEXTURE_CONSERVATIVE_CLEAN_SOURCE,
            "black_only_scanline_overlay_used": False,
            "zero_mean_horizontal_modulation": True,
            "caption_burn_is_last_visual_operation": "not_applicable_calibration_no_captions",
            "post_caption_visual_effects_applied": False,
            "clean_source_confirmed": True,
        },
        "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
        "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY,
        "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
        "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "texture_renderer_source": VISIBLE_SCANLINE_RENDERER_SOURCE,
        "luma_chroma_scanline_metrics_read": metrics_read,
        "signal_interruption_read": {
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "profile_id": SIGNAL_INTERRUPTION_PROFILE_ID,
            "profile_source": SIGNAL_INTERRUPTION_PROFILE_SOURCE,
            "strength": SIGNAL_INTERRUPTION_STRENGTH,
            "duration_seconds": SIGNAL_INTERRUPTION_DURATION_SECONDS,
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "render_policy": "mutate_existing_outgoing_frames_with_horizontal_tears_chroma_skew_luma_dropouts_restrained_snow",
            "full_frame_static_replacement_used": False,
            "calibration_signal_sample_reel_path": str(signal_reel),
        },
        "samples": sample_reads,
        "outputs": {
            "sample_reel_no_audio_path": str(sample_reel),
            "signal_tail_sample_reel_no_audio_path": str(signal_reel),
            "comparison_sheet": comparison_sheet,
            "scanline_closeup_sheet": closeup_sheet,
            "luma_chroma_scanline_metrics_manifest_path": str(metrics_manifest_path),
        },
        "qa": qa,
    }
    write_json(manifest_path, manifest)
    write_json(
        metrics_manifest_path,
        {
            **metrics_read,
            "target": target,
            "created_at": run_id,
            "pass_id": VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
            "samples": [
                {
                    "sample_index": item["sample_index"],
                    "source_row_id": item["source_row_id"],
                    "pass06_texture_metrics": item["pass06_texture_metrics"],
                    "pass07a_texture_metrics": item["pass07a_texture_metrics"],
                    "pass06_scanline_metrics": item["pass06_scanline_metrics"],
                    "pass07a_scanline_metrics": item["pass07a_scanline_metrics"],
                }
                for item in sample_reads
            ],
        },
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["luma_chroma_scanline_metrics_manifest_path"] = str(metrics_manifest_path)
    return manifest


def build_visible_scanline_calibration_set(run_id: str) -> tuple[Path, list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    for target in VISIBLE_SCANLINE_CALIBRATION_TARGETS:
        manifest_path = Path(FIRST_EIGHT_FINAL_MANIFESTS[target])
        print(f"[house-crt-visible-scanline-calibration] {target}: {manifest_path}", flush=True)
        try:
            results.append(build_visible_scanline_calibration_target(target, manifest_path, run_id))
        except subprocess.CalledProcessError as exc:
            results.append(
                {
                    "target": target,
                    "source_final_export_manifest_path": str(manifest_path),
                    "created_at": run_id,
                    "disposition": "blocked",
                    "pass_id": VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
                    "blocked_reason": "ffmpeg_or_probe_failed",
                    "command": exc.cmd,
                    "returncode": exc.returncode,
                }
            )
        except Exception as exc:  # noqa: BLE001 - keep the calibration batch inspectable.
            results.append(
                {
                    "target": target,
                    "source_final_export_manifest_path": str(manifest_path),
                    "created_at": run_id,
                    "disposition": "blocked",
                    "pass_id": VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
                    "blocked_reason": "render_or_validation_failed",
                    "error": str(exc),
                }
            )
    summary_path = Path.cwd() / f"{run_id}__house_crt_visible_scanline_calibration_pass_07a_summary.json"
    write_json(
        summary_path,
        {
            "schema_version": PASS07A_SUMMARY_SCHEMA_VERSION,
            "created_at": run_id,
            "pass_id": VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
            "target_set": "visible_scanline_calibration_set",
            "targets": list(VISIBLE_SCANLINE_CALIBRATION_TARGETS),
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "house_crt_contract_read": visible_scanline_contract_read(),
            "visual_layer_order_read": {
                **visual_layer_order_read(),
                "caption_burn_is_last_visual_operation": "not_applicable_calibration_no_captions",
            },
            "source_lineage_gate_read": {
                "required": True,
                "clean_source_confirmed_required": True,
                "pass06_preserved_as_diagnostic": True,
                "full_first8_render_deferred_until_review": True,
            },
            "results": results,
        },
    )
    return summary_path, results


def visible_scanline_strength_variant_ids(
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
) -> list[str]:
    return [str(item["scanline_strength_variant_id"]) for item in variants]


def summarize_ladder_entries(
    entries: list[dict[str, Any]],
    *,
    spec: dict[str, Any] | None,
    baseline_mean_scanline_yavg: float = 0.0,
) -> dict[str, Any]:
    luma_deltas = [abs(float((item.get("texture_metrics") or {}).get("luma_yavg_delta") or 0.0)) for item in entries]
    chroma_deltas = [float((item.get("texture_metrics") or {}).get("chroma_delta") or 0.0) for item in entries]
    scanline_values = [
        float((item.get("scanline_metrics") or {}).get("mean_signed_light_minus_dark_yavg") or 0.0)
        for item in entries
    ]
    metric_failures = [item for item in entries if (item.get("texture_metrics") or {}).get("overall_read") != "pass"]
    scanline_failures = [
        item for item in entries if (item.get("scanline_metrics") or {}).get("scanline_visibility_read") != "pass"
    ]
    mean_scanline = sum(scanline_values) / len(scanline_values) if scanline_values else 0.0
    target_min = float((spec or {}).get("target_scanline_yavg_min") or VISIBLE_SCANLINE_VISIBILITY_YAVG_MIN)
    target_max = float((spec or {}).get("target_scanline_yavg_max") or 999.0)
    target_read = "pass" if target_min <= mean_scanline <= target_max else "tighten"
    overall_read = "pass" if entries and not metric_failures and not scanline_failures else "fail"
    return {
        "scanline_strength_variant_id": (spec or {}).get("scanline_strength_variant_id", "pass07a_y6_baseline"),
        "scanline_delta_y": float((spec or {}).get("scanline_delta_y") or VISIBLE_SCANLINE_DELTA_RGB),
        "scanline_period_pixels": int((spec or {}).get("scanline_period_pixels") or VISIBLE_SCANLINE_PERIOD_PIXELS),
        "scanline_band_pixels": int((spec or {}).get("scanline_band_pixels") or VISIBLE_SCANLINE_BAND_PIXELS),
        "review_role": (spec or {}).get("review_role", "pass07a_baseline"),
        "target_scanline_yavg_min": target_min,
        "target_scanline_yavg_max": target_max,
        "sample_count": len(entries),
        "max_abs_luma_yavg_delta": round(max(luma_deltas), 4) if luma_deltas else 0.0,
        "min_chroma_delta": round(min(chroma_deltas), 4) if chroma_deltas else 0.0,
        "mean_scanline_yavg": round(mean_scanline, 4),
        "mean_scanline_gain_over_pass07a_yavg": round(mean_scanline - baseline_mean_scanline_yavg, 4),
        "target_scanline_read": target_read,
        "luma_chroma_failure_count": len(metric_failures),
        "scanline_failure_count": len(scanline_failures),
        "overall_read": overall_read,
    }


def make_scanline_strength_ladder_sheet(
    sample_reads: list[dict[str, Any]],
    out_path: Path,
    frame_dir: Path,
    *,
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
    title: str = "Visible scanline strength ladder",
) -> dict[str, Any]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    rows = sample_reads[:3]
    if not rows:
        return {"sheet_path": None, "frame_paths": [], "sheet_error": "no_ladder_samples"}
    variant_columns = [
        (str(spec["scanline_strength_variant_id"]).replace("_", " "), str(spec["scanline_strength_variant_id"]))
        for spec in variants
    ]
    columns = [
        ("clean", "conservative_clean_sample_path"),
        ("pass06", "pass06_sample_path"),
        ("pass07a", "pass07a_sample_path"),
    ] + variant_columns
    thumb_w, thumb_h = 160, 284
    label_w = 238
    gap = 8
    header_h = 58
    row_h = thumb_h + 54
    sheet = Image.new(
        "RGB",
        (label_w + len(columns) * thumb_w + (len(columns) + 1) * gap, header_h + len(rows) * row_h),
        (12, 12, 12),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 16), title, fill=(245, 245, 245))
    for c, (label, _key) in enumerate(columns):
        draw.text((label_w + gap + c * (thumb_w + gap), 18), label, fill=(225, 225, 225))
    frame_paths: list[Path] = []
    for row_i, read in enumerate(rows):
        y = header_h + row_i * row_h
        sample_duration = float(read.get("sample_duration_seconds") or 0.0)
        frame_second = max(0.01, min(0.70, sample_duration / 2))
        label_lines = [
            f"{int(read['sample_index']):02d} {read.get('source_row_id', '')}",
            f"07a {float((read.get('pass07a_scanline_metrics') or {}).get('mean_signed_light_minus_dark_yavg') or 0.0):+.1f}",
        ]
        for variant_id in visible_scanline_strength_variant_ids(variants):
            variant_read = (read.get("ladder_variants") or {}).get(variant_id) or {}
            scanline = variant_read.get("scanline_metrics") or {}
            label_lines.append(f"{variant_id.split('_')[0]} {float(scanline.get('mean_signed_light_minus_dark_yavg') or 0.0):+.1f}")
        for line_i, line in enumerate(label_lines[:6]):
            draw.text((16, y + 8 + line_i * 17), line, fill=(230, 230, 230))
        for c, (_label, key) in enumerate(columns):
            if key in visible_scanline_strength_variant_ids(variants):
                src = Path((read.get("ladder_variants") or {})[key]["sample_path"])
            else:
                src = Path(read[key])
            frame = frame_dir / f"sample_{int(read['sample_index']):02d}_col_{c + 1}.png"
            extract_review_frame(src, frame_second, frame)
            frame_paths.append(frame)
            with Image.open(frame) as im:
                thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (label_w + gap + c * (thumb_w + gap), y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "sheet_path": str(out_path),
        "frame_paths": [str(path) for path in frame_paths],
        "comparison_policy": "clean_vs_pass06_vs_pass07a_vs_visible_scanline_strength_variants",
        "variant_ids": visible_scanline_strength_variant_ids(variants),
    }


def make_scanline_strength_closeup_sheet(
    sample_reads: list[dict[str, Any]],
    out_path: Path,
    frame_dir: Path,
    *,
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
    title: str = "Scanline strength close-up",
) -> dict[str, Any]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    rows = sample_reads[:3]
    if not rows:
        return {"sheet_path": None, "frame_paths": [], "sheet_error": "no_ladder_samples"}
    columns = [
        ("pass07a", "pass07a_sample_path"),
    ] + [
        (str(spec["scanline_strength_variant_id"]).replace("_", " "), str(spec["scanline_strength_variant_id"]))
        for spec in variants
    ]
    crop_w, crop_h = 320, 230
    thumb_w, thumb_h = 240, 172
    label_w = 190
    gap = 10
    header_h = 58
    row_h = thumb_h + 46
    sheet = Image.new(
        "RGB",
        (label_w + len(columns) * thumb_w + (len(columns) + 1) * gap, header_h + len(rows) * row_h),
        (12, 12, 12),
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 16), title, fill=(245, 245, 245))
    for c, (label, _key) in enumerate(columns):
        draw.text((label_w + gap + c * (thumb_w + gap), 18), label, fill=(225, 225, 225))
    frame_paths: list[Path] = []
    for row_i, read in enumerate(rows):
        y = header_h + row_i * row_h
        sample_duration = float(read.get("sample_duration_seconds") or 0.0)
        frame_second = max(0.01, min(0.70, sample_duration / 2))
        draw.text((16, y + 10), f"{int(read['sample_index']):02d}", fill=(230, 230, 230))
        for c, (_label, key) in enumerate(columns):
            if key in visible_scanline_strength_variant_ids(variants):
                src = Path((read.get("ladder_variants") or {})[key]["sample_path"])
            else:
                src = Path(read[key])
            frame = frame_dir / f"sample_{int(read['sample_index']):02d}_{key}.png"
            extract_review_frame(src, frame_second, frame)
            frame_paths.append(frame)
            with Image.open(frame) as im:
                img = im.convert("RGB")
                left = max(0, (img.width - crop_w) // 2)
                top = max(0, int(img.height * 0.42) - crop_h // 2)
                crop = img.crop((left, top, min(img.width, left + crop_w), min(img.height, top + crop_h)))
                crop = crop.resize((thumb_w, thumb_h), Image.Resampling.NEAREST)
            sheet.paste(crop, (label_w + gap + c * (thumb_w + gap), y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=95)
    return {
        "sheet_path": str(out_path),
        "frame_paths": [str(path) for path in frame_paths],
        "comparison_policy": "nearest_neighbor_crop_pass07a_vs_scanline_strength_variants",
        "variant_ids": visible_scanline_strength_variant_ids(variants),
    }


def make_ladder_grid_clip(
    sample_read: dict[str, Any],
    out_path: Path,
    *,
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
) -> None:
    sources = [
        Path(sample_read["conservative_clean_sample_path"]),
        Path(sample_read["pass06_sample_path"]),
        Path(sample_read["pass07a_sample_path"]),
    ] + [
        Path((sample_read.get("ladder_variants") or {})[variant_id]["sample_path"])
        for variant_id in visible_scanline_strength_variant_ids(variants)
    ]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for source in sources:
        cmd.extend(["-i", str(source)])
    scale_filters = ";".join(
        f"[{idx}:v]scale=360:640,setpts=PTS-STARTPTS[v{idx}]" for idx in range(len(sources))
    )
    stack_inputs = "".join(f"[v{idx}]" for idx in range(len(sources)))
    layout = "0_0|360_0|720_0|0_640|360_640|720_640"
    filter_complex = (
        f"{scale_filters};"
        f"{stack_inputs}xstack=inputs={len(sources)}:layout={layout}[grid];"
        "[grid]pad=1080:1920:0:320:color=black,setsar=1,format=yuv420p[v]"
    )
    cmd.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(TARGET_FPS),
            "-movflags",
            "+faststart",
            str(out_path),
        ]
    )
    run(cmd)


def make_scanline_strength_ladder_reel(
    sample_reads: list[dict[str, Any]],
    out_path: Path,
    tmp_dir: Path,
    *,
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
) -> dict[str, Any]:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    grid_clips: list[Path] = []
    for read in sample_reads:
        clip = tmp_dir / f"sample_{int(read['sample_index']):02d}__ladder_grid.mp4"
        make_ladder_grid_clip(read, clip, variants=variants)
        grid_clips.append(clip)
    concat_videos(grid_clips, out_path)
    return {
        "reel_path": str(out_path),
        "grid_clip_paths": [str(path) for path in grid_clips],
        "layout": "2x3_grid_clean_pass06_pass07a_plus_three_scanline_variants",
        "variant_ids": visible_scanline_strength_variant_ids(variants),
    }


def summarize_scanline_strength_ladder(
    sample_reads: list[dict[str, Any]],
    *,
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
    metrics_schema_version: str = PASS07B_METRICS_SCHEMA_VERSION,
) -> dict[str, Any]:
    pass07a_entries = [
        {
            "texture_metrics": item.get("pass07a_texture_metrics"),
            "scanline_metrics": item.get("pass07a_scanline_metrics"),
        }
        for item in sample_reads
    ]
    pass07a_summary = summarize_ladder_entries(pass07a_entries, spec=None)
    baseline_mean = float(pass07a_summary.get("mean_scanline_yavg") or 0.0)
    variant_summaries: dict[str, Any] = {}
    for spec in variants:
        variant_id = str(spec["scanline_strength_variant_id"])
        entries = [
            {
                "texture_metrics": ((item.get("ladder_variants") or {}).get(variant_id) or {}).get("texture_metrics"),
                "scanline_metrics": ((item.get("ladder_variants") or {}).get(variant_id) or {}).get("scanline_metrics"),
            }
            for item in sample_reads
        ]
        variant_summaries[variant_id] = summarize_ladder_entries(entries, spec=spec, baseline_mean_scanline_yavg=baseline_mean)

    recommended = "manual_review_required"
    for spec in variants:
        if str(spec.get("review_role", "")).startswith("diagnostic"):
            continue
        variant_id = str(spec["scanline_strength_variant_id"])
        read = variant_summaries.get(variant_id) or {}
        if read.get("overall_read") == "pass" and read.get("target_scanline_read") == "pass":
            recommended = variant_id
            break
    failures = [
        variant_id
        for variant_id, read in variant_summaries.items()
        if read.get("overall_read") != "pass"
    ]
    return {
        "schema_version": metrics_schema_version,
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY,
        "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
        "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "luma_yavg_tolerance": LUMA_YAVG_TOLERANCE,
        "sample_count": len(sample_reads),
        "pass07a_baseline_read": pass07a_summary,
        "variant_reads": variant_summaries,
        "variant_ids": visible_scanline_strength_variant_ids(variants),
        "recommended_candidate": recommended,
        "failed_variant_ids": failures,
        "overall_read": "pass" if sample_reads and not failures else "tighten",
    }


def build_visible_scanline_strength_ladder_target(
    target: str,
    final_manifest_path: Path,
    run_id: str,
    *,
    pass_id: str = VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID,
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
    schema_version: str = PASS07B_SCHEMA_VERSION,
    metrics_schema_version: str = PASS07B_METRICS_SCHEMA_VERSION,
    manifest_stem: str = "visible_scanline_strength_ladder",
    output_label: str = "pass07b",
    supersedes_pass_id: str = VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
) -> dict[str, Any]:
    final_manifest = load_json(final_manifest_path)
    source_proof_path = resolve_source_proof(target, final_manifest)
    blocked_base = {
        "target": target,
        "source_final_export_manifest_path": str(final_manifest_path),
        "created_at": run_id,
        "disposition": "blocked",
        "pass_id": pass_id,
    }
    if source_proof_path is None or not source_proof_path.exists():
        return {**blocked_base, "blocked_reason": "missing_source_proof_manifest_path"}

    proof_manifest = load_json(source_proof_path)
    clean_source_plan = resolve_clean_source_plan(target, source_proof_path, proof_manifest)
    if clean_source_plan.source_lineage_read.get("clean_source_confirmed") is not True:
        return {
            **blocked_base,
            "source_proof_manifest_path": str(source_proof_path),
            "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "blocked_reason": "clean_source_lineage_not_confirmed",
        }
    selected_segments = select_calibration_segments(clean_source_plan.segment_plan)
    if not selected_segments:
        return {
            **blocked_base,
            "source_proof_manifest_path": str(source_proof_path),
            "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "blocked_reason": "missing_usable_clean_story_segments",
        }

    slug = target_slug(final_manifest, target)
    proof_dir = clean_source_plan.clean_source_proof_path.parent
    output_root = proof_dir / "final_exports" / f"{slug}_{pass_id}" / run_id
    work_dir = output_root / "work"
    sample_dir = work_dir / "samples"
    review_dir = output_root / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / f"{run_id}__{manifest_stem}_manifest.json"
    if manifest_path.exists():
        existing_manifest = load_json(manifest_path)
        if existing_manifest.get("disposition") == "review_ready" and existing_manifest.get("pass_id") == pass_id:
            existing_manifest["manifest_path"] = str(manifest_path)
            return existing_manifest

    sample_reads: list[dict[str, Any]] = []
    variant_samples: dict[str, list[Path]] = {variant_id: [] for variant_id in visible_scanline_strength_variant_ids(variants)}
    for sample_index, (segment, segment_source, timeline_in, timeline_out) in enumerate(selected_segments, start=1):
        sample_seconds = min(2.0, max(0.10, segment.duration))
        sample_segment = Segment(
            index=sample_index,
            start=segment.start,
            end=min(segment.end, segment.start + sample_seconds),
            source_row_id=segment.source_row_id,
        )
        sample_root = sample_dir / f"{sample_index:02d}_{sample_segment.source_row_id}"
        sample_root.mkdir(parents=True, exist_ok=True)
        source_sample = sample_root / f"{sample_index:02d}__source_no_audio.mp4"
        clean_sample = sample_root / f"{sample_index:02d}__conservative_clean.mp4"
        pass06_sample = sample_root / f"{sample_index:02d}__pass06_luma_neutral_chroma.mp4"
        pass07a_sample = sample_root / f"{sample_index:02d}__pass07a_visible_scanline_y6.mp4"
        render_source_segment(segment_source, sample_segment, source_sample)
        render_historical_signal_conservative_clean(source_sample, clean_sample)
        pass06_metrics = render_luma_neutral_chroma_texture(clean_sample, pass06_sample)
        pass07a_metrics = render_luma_neutral_chroma_texture(
            clean_sample,
            pass07a_sample,
            visible_scanline=True,
            scanline_delta_y=VISIBLE_SCANLINE_DELTA_RGB,
            scanline_strength_variant_id="pass07a_y6_baseline",
        )
        pass06_scanline = scanline_metric_read(pass06_sample, sample_root / "pass06_scanline_metric_frames")
        pass07a_scanline = pass07a_metrics.get("scanline_metrics") or scanline_metric_read(
            pass07a_sample,
            sample_root / "pass07a_scanline_metric_frames",
            scanline_delta_y=VISIBLE_SCANLINE_DELTA_RGB,
            scanline_strength_variant_id="pass07a_y6_baseline",
        )
        ladder_variants: dict[str, Any] = {}
        for spec in variants:
            variant_id = str(spec["scanline_strength_variant_id"])
            variant_delta = float(spec["scanline_delta_y"])
            variant_period = int(spec.get("scanline_period_pixels") or VISIBLE_SCANLINE_PERIOD_PIXELS)
            variant_band = int(spec.get("scanline_band_pixels") or VISIBLE_SCANLINE_BAND_PIXELS)
            variant_path = sample_root / f"{sample_index:02d}__{output_label}_{variant_id}.mp4"
            variant_metrics = render_luma_neutral_chroma_texture(
                clean_sample,
                variant_path,
                visible_scanline=True,
                scanline_delta_y=variant_delta,
                scanline_period_pixels=variant_period,
                scanline_band_pixels=variant_band,
                scanline_strength_variant_id=variant_id,
                enforce_metric_gate=False,
            )
            variant_scanline = variant_metrics.get("scanline_metrics") or scanline_metric_read(
                variant_path,
                sample_root / f"{variant_id}_scanline_metric_frames",
                scanline_delta_y=variant_delta,
                scanline_period_pixels=variant_period,
                scanline_band_pixels=variant_band,
                scanline_strength_variant_id=variant_id,
            )
            variant_samples[variant_id].append(variant_path)
            ladder_variants[variant_id] = {
                **spec,
                "sample_path": str(variant_path),
                "texture_metrics": variant_metrics,
                "scanline_metrics": variant_scanline,
            }
        sample_reads.append(
            {
                "sample_index": sample_index,
                "source_row_id": sample_segment.source_row_id,
                "segment_source_path": str(segment_source),
                "timeline_in": timeline_in,
                "timeline_out": timeline_out,
                "sample_source_start": sample_segment.start,
                "sample_source_end": sample_segment.end,
                "sample_duration_seconds": sample_segment.duration,
                "source_sample_path": str(source_sample),
                "conservative_clean_sample_path": str(clean_sample),
                "pass06_sample_path": str(pass06_sample),
                "pass07a_sample_path": str(pass07a_sample),
                "pass06_texture_metrics": pass06_metrics,
                "pass07a_texture_metrics": pass07a_metrics,
                "pass06_scanline_metrics": pass06_scanline,
                "pass07a_scanline_metrics": pass07a_scanline,
                "ladder_variants": ladder_variants,
            }
        )

    variant_reels: dict[str, str] = {}
    for variant_id, paths in variant_samples.items():
        reel_path = review_dir / f"{slug}__{output_label}_{variant_id}_sample_reel_no_audio.mp4"
        concat_videos(paths, reel_path)
        variant_reels[variant_id] = str(reel_path)
    ladder_reel = make_scanline_strength_ladder_reel(
        sample_reads,
        review_dir / f"{slug}__{output_label}_visible_scanline_strength_ladder_reel_no_audio.mp4",
        review_dir / f"{slug}__{output_label}_visible_scanline_strength_ladder_grid_clips",
        variants=variants,
    )
    comparison_sheet = make_scanline_strength_ladder_sheet(
        sample_reads,
        review_dir / f"{slug}__clean_pass06_pass07a_{output_label}_strength_ladder_sheet.jpg",
        review_dir / f"{slug}__clean_pass06_pass07a_{output_label}_strength_ladder_frames",
        variants=variants,
        title=f"{output_label} visible scanline strength ladder",
    )
    closeup_sheet = make_scanline_strength_closeup_sheet(
        sample_reads,
        review_dir / f"{slug}__pass07a_{output_label}_scanline_strength_closeup_sheet.jpg",
        review_dir / f"{slug}__pass07a_{output_label}_scanline_strength_closeup_frames",
        variants=variants,
        title=f"{output_label} scanline close-up",
    )
    metrics_read = summarize_scanline_strength_ladder(
        sample_reads,
        variants=variants,
        metrics_schema_version=metrics_schema_version,
    )

    qa_videos = {**variant_reels, "side_by_side_ladder_reel": ladder_reel["reel_path"]}
    video_reads: dict[str, Any] = {}
    for key, path_text in qa_videos.items():
        path = Path(path_text)
        streams = stream_counts(path)
        video = video_stream(path)
        video_reads[key] = {
            "path": str(path),
            "geometry_9x16_read": "pass"
            if int(video.get("width", 0)) == TARGET_WIDTH and int(video.get("height", 0)) == TARGET_HEIGHT
            else "fail",
            "audio_stream_count": streams["audio"],
            "audio_stream_read": "pass" if streams["audio"] == 0 else "fail",
            "subtitle_stream_count": streams["subtitle"],
            "subtitle_stream_read": "pass" if streams["subtitle"] == 0 else "fail",
        }
    qa = {
        "video_reads": video_reads,
        "all_reels_geometry_9x16_read": "pass"
        if all(item["geometry_9x16_read"] == "pass" for item in video_reads.values())
        else "fail",
        "all_reels_zero_audio_read": "pass"
        if all(item["audio_stream_count"] == 0 for item in video_reads.values())
        else "fail",
        "all_reels_zero_subtitle_read": "pass"
        if all(item["subtitle_stream_count"] == 0 for item in video_reads.values())
        else "fail",
        "luma_chroma_scanline_ladder_read": metrics_read["overall_read"],
    }
    metrics_manifest_path = output_root / f"{run_id}__{manifest_stem}_metrics_manifest.json"
    manifest = {
        "schema_version": schema_version,
        "target": target,
        "episode_slug": slug,
        "created_at": run_id,
        "disposition": "review_ready",
        "pass_id": pass_id,
        "calibration_only": True,
        "full_first8_render_deferred_until_review": True,
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "house_crt_contract_read": visible_scanline_contract_read(),
        "supersedes_pass_id": supersedes_pass_id,
        "supersedes_status": "diagnostic_only_until_human_review",
        "source_final_export_manifest_path": str(final_manifest_path),
        "source_proof_manifest_path": str(source_proof_path),
        "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
        "source_lineage_read": clean_source_plan.source_lineage_read,
        "visual_layer_order_read": {
            **visual_layer_order_read(),
            "caption_burn_is_last_visual_operation": "not_applicable_calibration_no_captions",
            "post_caption_visual_effects_applied": False,
        },
        "house_crt_texture_read": {
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "profile_id": HOUSE_CRT_PROFILE_ID,
            "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
            "intensity": HOUSE_CRT_INTENSITY,
            "signal_texture_strength": HOUSE_CRT_INTENSITY,
            "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY,
            "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
            "legacy_calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
            "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
            "texture_renderer_source": VISIBLE_SCANLINE_RENDERER_SOURCE,
            "texture_conservative_clean_source": TEXTURE_CONSERVATIVE_CLEAN_SOURCE,
            "scanline_strength_ladder_pass_id": pass_id,
            "scanline_strength_variants": list(variants),
            "black_only_scanline_overlay_used": False,
            "zero_mean_horizontal_modulation": True,
            "caption_burn_is_last_visual_operation": "not_applicable_calibration_no_captions",
            "post_caption_visual_effects_applied": False,
            "clean_source_confirmed": True,
        },
        "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
        "texture_tone_policy": VISIBLE_SCANLINE_TONE_POLICY,
        "calibration_recipe_id": VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID,
        "scanline_policy_id": VISIBLE_SCANLINE_POLICY_ID,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "texture_renderer_source": VISIBLE_SCANLINE_RENDERER_SOURCE,
        "luma_chroma_scanline_metrics_read": metrics_read,
        "signal_interruption_read": {
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "profile_id": SIGNAL_INTERRUPTION_PROFILE_ID,
            "duration_seconds": SIGNAL_INTERRUPTION_DURATION_SECONDS,
            "timing_policy": "unchanged_from_pass07a_not_rendered_in_line_strength_ladder",
            "full_frame_static_replacement_used": False,
        },
        "samples": sample_reads,
        "outputs": {
            "variant_sample_reels_no_audio": variant_reels,
            "side_by_side_ladder_reel_no_audio": ladder_reel,
            "comparison_sheet": comparison_sheet,
            "scanline_closeup_sheet": closeup_sheet,
            "luma_chroma_scanline_metrics_manifest_path": str(metrics_manifest_path),
        },
        "qa": qa,
    }
    write_json(manifest_path, manifest)
    write_json(
        metrics_manifest_path,
        {
            **metrics_read,
            "target": target,
            "created_at": run_id,
            "pass_id": pass_id,
            "samples": [
                {
                    "sample_index": item["sample_index"],
                    "source_row_id": item["source_row_id"],
                    "pass06_texture_metrics": item["pass06_texture_metrics"],
                    "pass07a_texture_metrics": item["pass07a_texture_metrics"],
                    "pass06_scanline_metrics": item["pass06_scanline_metrics"],
                    "pass07a_scanline_metrics": item["pass07a_scanline_metrics"],
                    "ladder_variants": item["ladder_variants"],
                }
                for item in sample_reads
            ],
        },
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["luma_chroma_scanline_metrics_manifest_path"] = str(metrics_manifest_path)
    return manifest


def build_visible_scanline_strength_ladder_set(
    run_id: str,
    *,
    pass_id: str = VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID,
    variants: tuple[dict[str, Any], ...] = VISIBLE_SCANLINE_STRENGTH_VARIANTS,
    schema_version: str = PASS07B_SCHEMA_VERSION,
    metrics_schema_version: str = PASS07B_METRICS_SCHEMA_VERSION,
    summary_schema_version: str = PASS07B_SUMMARY_SCHEMA_VERSION,
    manifest_stem: str = "visible_scanline_strength_ladder",
    output_label: str = "pass07b",
    target_set: str = "visible_scanline_strength_ladder_set",
    summary_filename_suffix: str = "house_crt_visible_scanline_strength_ladder_pass_07b_summary",
    supersedes_pass_id: str = VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
) -> tuple[Path, list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    for target in VISIBLE_SCANLINE_CALIBRATION_TARGETS:
        manifest_path = Path(FIRST_EIGHT_FINAL_MANIFESTS[target])
        print(f"[house-crt-visible-scanline-ladder:{output_label}] {target}: {manifest_path}", flush=True)
        try:
            results.append(
                build_visible_scanline_strength_ladder_target(
                    target,
                    manifest_path,
                    run_id,
                    pass_id=pass_id,
                    variants=variants,
                    schema_version=schema_version,
                    metrics_schema_version=metrics_schema_version,
                    manifest_stem=manifest_stem,
                    output_label=output_label,
                    supersedes_pass_id=supersedes_pass_id,
                )
            )
        except subprocess.CalledProcessError as exc:
            results.append(
                {
                    "target": target,
                    "source_final_export_manifest_path": str(manifest_path),
                    "created_at": run_id,
                    "disposition": "blocked",
                    "pass_id": pass_id,
                    "blocked_reason": "ffmpeg_or_probe_failed",
                    "command": exc.cmd,
                    "returncode": exc.returncode,
                }
            )
        except Exception as exc:  # noqa: BLE001 - keep the ladder batch inspectable.
            results.append(
                {
                    "target": target,
                    "source_final_export_manifest_path": str(manifest_path),
                    "created_at": run_id,
                    "disposition": "blocked",
                    "pass_id": pass_id,
                    "blocked_reason": "render_or_validation_failed",
                    "error": str(exc),
                }
            )
    summary_path = Path.cwd() / f"{run_id}__{summary_filename_suffix}.json"
    write_json(
        summary_path,
        {
            "schema_version": summary_schema_version,
            "created_at": run_id,
            "pass_id": pass_id,
            "target_set": target_set,
            "targets": list(VISIBLE_SCANLINE_CALIBRATION_TARGETS),
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "house_crt_contract_read": visible_scanline_contract_read(),
            "scanline_strength_variants": list(variants),
            "visual_layer_order_read": {
                **visual_layer_order_read(),
                "caption_burn_is_last_visual_operation": "not_applicable_calibration_no_captions",
            },
            "source_lineage_gate_read": {
                "required": True,
                "clean_source_confirmed_required": True,
                "pass07a_preserved_as_baseline": True,
                "full_first8_render_deferred_until_review": True,
            },
            "results": results,
        },
    )
    return summary_path, results


def build_visible_scanline_high_visibility_ladder_set(run_id: str) -> tuple[Path, list[dict[str, Any]]]:
    return build_visible_scanline_strength_ladder_set(
        run_id,
        pass_id=VISIBLE_SCANLINE_HIGH_VISIBILITY_LADDER_PASS_ID,
        variants=VISIBLE_SCANLINE_HIGH_VISIBILITY_VARIANTS,
        schema_version=PASS07C_SCHEMA_VERSION,
        metrics_schema_version=PASS07C_METRICS_SCHEMA_VERSION,
        summary_schema_version=PASS07C_SUMMARY_SCHEMA_VERSION,
        manifest_stem="visible_scanline_high_visibility_ladder",
        output_label="pass07c",
        target_set="visible_scanline_high_visibility_ladder_set",
        summary_filename_suffix="house_crt_visible_scanline_high_visibility_ladder_pass_07c_summary",
        supersedes_pass_id=VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID,
    )


def target_slug(final_manifest: dict[str, Any], fallback: str) -> str:
    for key in ("episode_id", "short_id", "target_id"):
        val = final_manifest.get(key)
        if isinstance(val, str) and val:
            return val.replace("/", "_").replace(" ", "_").lower()
    return fallback


def build_target(
    target: str,
    final_manifest_path: Path,
    run_id: str,
    challenger_reference: dict[str, Any] | None = None,
    *,
    pass_id: str = CORRECTED_PASS_ID,
    schema_version: str = PASS04_SCHEMA_VERSION,
    texture_schema_version: str = PASS04_TEXTURE_SCHEMA_VERSION,
    metrics_schema_version: str = PASS04_METRICS_SCHEMA_VERSION,
    visible_scanline: bool = False,
    scanline_spec: dict[str, Any] | None = None,
    output_suffix: str = "house_crt_signal_interruption",
    supersedes_pass_id: str = SUPERSEDED_PASS_ID,
) -> dict[str, Any]:
    final_manifest = load_json(final_manifest_path)
    old_final = find_final_path(final_manifest)
    ass_path = find_caption_ass_path(final_manifest)
    source_proof_path = resolve_source_proof(target, final_manifest)
    blocked_base = {
        "target": target,
        "source_final_export_manifest_path": str(final_manifest_path),
        "created_at": run_id,
        "disposition": "blocked",
        "pass_id": pass_id,
    }
    scanline_spec = scanline_spec or (selected_visible_scanline_variant() if visible_scanline else None)
    contract_payload = visible_scanline_contract_read() if visible_scanline else contract_read()
    texture_tone_policy = VISIBLE_SCANLINE_TONE_POLICY if visible_scanline else HOUSE_CRT_TONE_POLICY
    calibration_recipe_id = VISIBLE_SCANLINE_CALIBRATION_RECIPE_ID if visible_scanline else CALIBRATION_RECIPE_ID
    texture_renderer_source = VISIBLE_SCANLINE_RENDERER_SOURCE if visible_scanline else TEXTURE_RENDERER_SOURCE
    scanline_fields = scanline_contract_fields(scanline_spec) if visible_scanline else {}
    if old_final is None or not old_final.exists():
        return {**blocked_base, "blocked_reason": "missing_active_captioned_final_path"}
    if ass_path is None or not ass_path.exists():
        return {**blocked_base, "blocked_reason": "missing_caption_ass_path"}
    if source_proof_path is None or not source_proof_path.exists():
        return {**blocked_base, "blocked_reason": "missing_source_proof_manifest_path"}

    proof_manifest = load_json(source_proof_path)
    clean_source_plan = resolve_clean_source_plan(target, source_proof_path, proof_manifest)
    segment_plan = clean_source_plan.segment_plan
    segments = [item[0] for item in segment_plan]
    visual_source = clean_source_plan.visual_source_path
    if len(segment_plan) < 2:
        return {
            **blocked_base,
            "source_proof_manifest_path": str(source_proof_path),
            "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "visual_source_path": str(visual_source or ""),
            "blocked_reason": "missing_usable_clean_story_segments",
        }
    if clean_source_plan.source_lineage_read.get("clean_source_confirmed") is not True:
        return {
            **blocked_base,
            "source_proof_manifest_path": str(source_proof_path),
            "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "visual_source_path": str(visual_source or ""),
            "blocked_reason": "clean_source_lineage_not_confirmed",
        }

    rng = random.Random(f"{target}:{run_id}:{SIGNAL_INTERRUPTION_PROFILE_ID}")
    for segment in segments[:-1]:
        segment.signal_seed = rng.randint(1000, 999999)

    slug = target_slug(final_manifest, target)
    proof_dir = clean_source_plan.clean_source_proof_path.parent
    output_root = proof_dir / "final_exports" / f"{slug}_{pass_id}" / run_id
    work_dir = output_root / "work"
    segment_dir = work_dir / "segments"
    final_dir = output_root / "final"
    review_dir = output_root / "review"
    final_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / f"{run_id}__final_export.json"
    if manifest_path.exists():
        existing_manifest = load_json(manifest_path)
        if (
            existing_manifest.get("disposition") == "review_ready"
            and existing_manifest.get("house_crt_contract_id") == HOUSE_CRT_CONTRACT_ID
            and existing_manifest.get("pass_id") == pass_id
        ):
            existing_manifest["manifest_path"] = str(manifest_path)
            return existing_manifest

    rendered_segments: list[Path] = []
    signal_reads: list[dict[str, Any]] = []
    for segment, segment_source, timeline_in, timeline_out in segment_plan:
        segment_path = segment_dir / f"{segment.index:02d}_{segment.source_row_id}__{output_suffix}.mp4"
        read = render_segment(
            segment_source,
            segment,
            segment_path,
            apply_signal=segment.index < len(segments),
            visible_scanline=visible_scanline,
            scanline_spec=scanline_spec,
        )
        rendered_segments.append(segment_path)
        signal_reads.append(
            {
                "segment_index": segment.index,
                "source_row_id": segment.source_row_id,
                "timeline_in": timeline_in,
                "timeline_out": timeline_out,
                "segment_source_path": str(segment_source),
                "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
                "source_lineage_clean_source_confirmed": True,
                **read,
            }
        )

    motion_core = work_dir / f"{slug}__{output_suffix}_core_no_audio.mp4"
    concat_videos(rendered_segments, motion_core)
    motion_full, tail_reads = match_final_duration(
        motion_core,
        final_manifest,
        old_final,
        work_dir,
        visible_scanline=visible_scanline,
        scanline_spec=scanline_spec,
    )

    captioned_no_audio = final_dir / f"{slug}__{output_suffix}_captioned_no_audio.mp4"
    captioned_final = final_dir / f"{slug}__{output_suffix}_captioned_final.mp4"
    burn_captions(motion_full, ass_path, captioned_no_audio)
    remux_final_audio(captioned_no_audio, old_final, captioned_final)

    cut_times = [max(0.0, float(item["timeline_out"]) - SIGNAL_INTERRUPTION_DURATION_SECONDS / 2) for item in signal_reads[:-1]]
    sampled_cut_sheet = make_frame_sheet(captioned_final, cut_times, review_dir / f"{slug}__signal_interruption_sampled_cut_sheet.jpg")
    cut_sheet = make_challenger_style_cut_review_sheet(
        signal_reads,
        review_dir / f"{slug}__signal_interruption_cut_review_sheet.jpg",
        review_dir / f"{slug}__signal_interruption_cut_review_frames",
    )
    cut_reel = make_challenger_style_cut_review_reel(
        signal_reads,
        review_dir / f"{slug}__signal_interruption_cut_review_reel.mp4",
        review_dir / f"{slug}__signal_interruption_cut_review_reel_pieces",
    )
    challenger_reference = challenger_reference or challenger_luma_neutral_reference(
        run_id,
        visible_scanline=visible_scanline,
        scanline_spec=scanline_spec,
    )
    challenger_reference_video = Path(str(challenger_reference.get("reference_video_path") or CHALLENGER_REFERENCE_VIDEO_PATH))
    challenger_contract_comparison_sheet = make_challenger_contract_comparison_sheet(
        captioned_final,
        review_dir / f"{slug}__challenger_{'visible_scanline' if visible_scanline else 'luma_neutral'}_comparison_sheet.jpg",
        review_dir / f"{slug}__challenger_{'visible_scanline' if visible_scanline else 'luma_neutral'}_comparison_frames",
        challenger_reference_video,
    )
    pass03_manifest = load_pass03_manifest(target)
    clean_texture_comparison_sheet = make_clean_texture_comparison_sheet(
        signal_reads,
        pass03_manifest,
        review_dir / f"{slug}__clean_pass03_pass06_texture_comparison_sheet.jpg",
        review_dir / f"{slug}__clean_pass03_pass06_texture_comparison_frames",
    )
    pass05_manifest = load_pass05_manifest(target)
    clean_pass05_pass06_lineage_sheet = make_clean_pass05_pass06_lineage_comparison_sheet(
        signal_reads,
        pass05_manifest,
        captioned_final,
        review_dir / f"{slug}__clean_pass05_pass06_lineage_comparison_sheet.jpg",
        review_dir / f"{slug}__clean_pass05_pass06_lineage_comparison_frames",
    )
    tail_times = [max(0.0, duration(captioned_final) - t) for t in (4.0, 2.0, 0.5)]
    tail_sheet = make_frame_sheet(captioned_final, tail_times, review_dir / f"{slug}__final_tail_sheet.jpg")
    luma_chroma_metrics_read = luma_chroma_metrics_summary(
        signal_reads,
        tail_reads,
        visible_scanline=visible_scanline,
        scanline_spec=scanline_spec,
        metrics_schema_version=metrics_schema_version,
    )

    old_duration = duration(old_final)
    new_duration = duration(captioned_final)
    final_streams = stream_counts(captioned_final)
    motion_streams = stream_counts(motion_full)
    video = video_stream(captioned_final)
    qa = {
        "geometry_9x16_read": "pass" if int(video.get("width", 0)) == TARGET_WIDTH and int(video.get("height", 0)) == TARGET_HEIGHT else "fail",
        "duration_drift_seconds": new_duration - old_duration,
        "duration_drift_read": "pass" if abs(new_duration - old_duration) <= DRIFT_TOLERANCE_SECONDS else "fail",
        "final_audio_stream_count": final_streams["audio"],
        "final_audio_stream_read": "pass" if final_streams["audio"] == 1 else "fail",
        "motion_only_audio_stream_count": motion_streams["audio"],
        "motion_only_audio_read": "pass" if motion_streams["audio"] == 0 else "fail",
        "subtitle_stream_count": final_streams["subtitle"],
        "subtitle_stream_read": "pass" if final_streams["subtitle"] == 0 else "fail",
        "old_final_unchanged_sha256": sha256(old_final),
        "new_final_sha256": sha256(captioned_final),
        "old_final_path": str(old_final),
    }

    manifest = {
        "schema_version": schema_version,
        "target": target,
        "episode_slug": slug,
        "created_at": run_id,
        "disposition": "review_ready",
        "pass_id": pass_id,
        "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
        "house_crt_contract_read": contract_payload,
        "supersedes_pass_id": supersedes_pass_id,
        "diagnostic_supersedes_pass_ids": [
            "house_crt_static_active_final_pass_01",
            "house_crt_signal_interruption_active_final_pass_02",
            "house_crt_challenger_contract_signal_interruption_active_final_pass_03",
            "house_crt_luma_neutral_chroma_signal_interruption_active_final_pass_04",
            CORRECTED_PASS_ID,
            VISIBLE_SCANLINE_CALIBRATION_PASS_ID,
            VISIBLE_SCANLINE_STRENGTH_LADDER_PASS_ID,
            VISIBLE_SCANLINE_HIGH_VISIBILITY_LADDER_PASS_ID,
            SUPERSEDED_PASS_ID,
        ],
        "supersedes_reason": (
            "pass07 applies the reviewed strongest visible scanline contract from verified clean no-caption source lineage; "
            "prior passes remain diagnostic."
            if visible_scanline
            else "pass06 rebuilds from verified clean no-caption source lineage before applying the shared house CRT contract; pass05 remains diagnostic."
        ),
        "source_final_export_manifest_path": str(final_manifest_path),
        "source_proof_manifest_path": str(source_proof_path),
        "clean_source_proof_manifest_path": str(clean_source_plan.clean_source_proof_path),
        "visual_source_path": str(visual_source or ""),
        "source_lineage_read": clean_source_plan.source_lineage_read,
        "caption_ass_path": str(ass_path),
        "audio_source_final_path": str(old_final),
        "visual_layer_order_read": visual_layer_order_read(),
        "caption_layer_order_read": visual_layer_order_read()["caption_layer_order_read"],
        "post_caption_visual_effects_applied": False,
        "house_crt_texture_read": {
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "profile_id": HOUSE_CRT_PROFILE_ID,
            "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
            "intensity": HOUSE_CRT_INTENSITY,
            "signal_texture_strength": HOUSE_CRT_INTENSITY,
            "texture_tone_policy": texture_tone_policy,
            "calibration_recipe_id": calibration_recipe_id,
            "legacy_calibration_recipe_id": calibration_recipe_id,
            "texture_renderer_source": texture_renderer_source,
            "texture_conservative_clean_source": TEXTURE_CONSERVATIVE_CLEAN_SOURCE,
            **scanline_fields,
            "luma_yavg_tolerance": LUMA_YAVG_TOLERANCE,
            "monochrome_chroma_magnitude_max": MONOCHROME_CHROMA_MAGNITUDE_MAX,
            "scope": "story_motion_segments_and_rebuilt_tail_before_captions",
            "caption_burn_is_last_visual_operation": True,
            "post_caption_visual_effects_applied": False,
            "era_specific_texture_removed": True,
            "clean_source_confirmed": True,
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "challenger_luma_neutral_reference_video_path": str(challenger_reference_video),
            "challenger_luma_neutral_reference_manifest_path": str(challenger_reference.get("manifest_path", "")),
        },
        "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
        "texture_tone_policy": texture_tone_policy,
        "calibration_recipe_id": calibration_recipe_id,
        "legacy_calibration_recipe_id": calibration_recipe_id,
        "signal_texture_strength": HOUSE_CRT_INTENSITY,
        "texture_renderer_source": texture_renderer_source,
        **scanline_fields,
        "luma_chroma_metrics_read": luma_chroma_metrics_read,
        "signal_interruption_read": {
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "profile_id": SIGNAL_INTERRUPTION_PROFILE_ID,
            "profile_source": SIGNAL_INTERRUPTION_PROFILE_SOURCE,
            "strength": SIGNAL_INTERRUPTION_STRENGTH,
            "duration_seconds": SIGNAL_INTERRUPTION_DURATION_SECONDS,
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "render_policy": "mutate_existing_outgoing_frames_with_horizontal_tears_chroma_skew_luma_dropouts_restrained_snow",
            "full_frame_static_replacement_used": False,
            "eligible_cut_count": len(segments) - 1,
            "applied_cut_count": sum(1 for item in signal_reads if item.get("signal_interruption_applied")),
        },
        "randomized_static_transition_read": {
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "profile_id": SIGNAL_INTERRUPTION_PROFILE_ID,
            "duration_seconds": SIGNAL_INTERRUPTION_DURATION_SECONDS,
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "read": "superseded_label_use_signal_interruption_read",
        },
        "segments": signal_reads,
        "tail_reads": tail_reads,
        "outputs": {
            "motion_core_no_audio_path": str(motion_core),
            "motion_full_duration_no_audio_path": str(motion_full),
            "captioned_no_audio_path": str(captioned_no_audio),
            "captioned_final_path": str(captioned_final),
            "signal_interruption_cut_review_sheet": cut_sheet,
            "signal_interruption_sampled_cut_sheet": sampled_cut_sheet,
            "signal_interruption_cut_review_reel": cut_reel,
            "challenger_luma_neutral_comparison_sheet": challenger_contract_comparison_sheet,
            "clean_texture_comparison_sheet": clean_texture_comparison_sheet,
            "clean_pass05_pass06_lineage_comparison_sheet": clean_pass05_pass06_lineage_sheet,
            "final_tail_sheet": tail_sheet,
        },
        "publish_package_validation": {
            "status": "deferred_until_human_keep_review",
            "reason": "new pass is review_ready; existing packages are not superseded before keep",
        },
        "qa": qa,
    }
    texture_manifest_name = (
        f"{run_id}__texture_luma_neutral_chroma_visible_scanline_signal_interruption_manifest.json"
        if visible_scanline
        else f"{run_id}__texture_luma_neutral_chroma_signal_interruption_manifest.json"
    )
    metrics_manifest_name = (
        f"{run_id}__luma_chroma_scanline_metrics_manifest.json"
        if visible_scanline
        else f"{run_id}__luma_chroma_metrics_manifest.json"
    )
    texture_manifest_path = output_root / texture_manifest_name
    metrics_manifest_path = output_root / metrics_manifest_name
    manifest["outputs"]["texture_signal_interruption_manifest_path"] = str(texture_manifest_path)
    manifest["outputs"]["luma_chroma_metrics_manifest_path"] = str(metrics_manifest_path)
    manifest["luma_chroma_metrics_manifest_path"] = str(metrics_manifest_path)
    write_json(manifest_path, manifest)
    write_json(
        texture_manifest_path,
        {
            "schema_version": texture_schema_version,
            "target": target,
            "created_at": run_id,
            "pass_id": pass_id,
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "house_crt_contract_read": contract_payload,
            "visual_layer_order_read": manifest["visual_layer_order_read"],
            "supersedes_pass_id": supersedes_pass_id,
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
            "texture_tone_policy": texture_tone_policy,
            "calibration_recipe_id": calibration_recipe_id,
            "legacy_calibration_recipe_id": calibration_recipe_id,
            "signal_texture_strength": HOUSE_CRT_INTENSITY,
            "texture_renderer_source": texture_renderer_source,
            **scanline_fields,
            "house_crt_texture_read": manifest["house_crt_texture_read"],
            "luma_chroma_metrics_read": luma_chroma_metrics_read,
            "signal_interruption_read": manifest["signal_interruption_read"],
            "randomized_static_transition_read": manifest["randomized_static_transition_read"],
            "segments": signal_reads,
            "tail_reads": tail_reads,
        },
    )
    write_json(
        metrics_manifest_path,
        {
            **luma_chroma_metrics_read,
            "target": target,
            "created_at": run_id,
            "pass_id": pass_id,
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "source_lineage_read": clean_source_plan.source_lineage_read,
            "historical_signal_profile_id": HOUSE_CRT_PROFILE_ID,
            "texture_tone_policy": texture_tone_policy,
            "calibration_recipe_id": calibration_recipe_id,
            **scanline_fields,
            "segments": [
                {
                    "segment_index": item["segment_index"],
                    "source_row_id": item["source_row_id"],
                    "texture_metrics": item["texture_metrics"],
                }
                for item in signal_reads
            ],
            "tails": [
                {
                    "type": item.get("type"),
                    "seconds": item.get("seconds"),
                    "texture_metrics": item.get("texture_metrics"),
                }
                for item in tail_reads
                if item.get("texture_metrics")
            ],
        },
    )
    manifest["manifest_path"] = str(manifest_path)
    manifest["texture_static_manifest_path"] = str(texture_manifest_path)
    manifest["texture_signal_interruption_manifest_path"] = str(texture_manifest_path)
    manifest["luma_chroma_metrics_manifest_path"] = str(metrics_manifest_path)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active-final-set", action="store_true", help="Process TOML-active final set, excluding Challenger.")
    parser.add_argument("--first-eight-final-set", action="store_true", help="Process the eight first-slate final manifests through the global house CRT contract.")
    parser.add_argument(
        "--visible-scanline-first-eight-final-set",
        action="store_true",
        help="Process the first eight finals through pass07 with the selected visible CRT scanline strength.",
    )
    parser.add_argument(
        "--visible-scanline-final-gate",
        action="store_true",
        help="Use the selected visible CRT scanline final-gate contract for --current-final-set, --target, or --final-manifest.",
    )
    parser.add_argument(
        "--visible-scanline-calibration-set",
        action="store_true",
        help="Render pass07a calibration samples for Challenger, Hyatt, and 737 MAX before full first-eight promotion.",
    )
    parser.add_argument(
        "--visible-scanline-strength-ladder-set",
        action="store_true",
        help="Render pass07b visible scanline strength ladder samples for Challenger, Hyatt, and 737 MAX.",
    )
    parser.add_argument(
        "--visible-scanline-high-visibility-ladder-set",
        action="store_true",
        help="Render pass07c higher-visibility scanline bar ladder samples for Challenger, Hyatt, and 737 MAX.",
    )
    parser.add_argument("--current-final-set", action="store_true", help="Discover current final_export_manifest_path values from episode TOML for future Shorts.")
    parser.add_argument("--target", action="append", choices=sorted(ALL_KNOWN_FINAL_MANIFESTS), help="Process one known target.")
    parser.add_argument("--final-manifest", action="append", type=Path, help="Explicit final export manifest path.")
    parser.add_argument("--run-id", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.run_id is None:
        args.run_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    if args.visible_scanline_calibration_set:
        summary_path, results = build_visible_scanline_calibration_set(args.run_id)
        print(summary_path)
        blocked = [r for r in results if r.get("disposition") == "blocked"]
        return 2 if blocked else 0
    if args.visible_scanline_strength_ladder_set:
        summary_path, results = build_visible_scanline_strength_ladder_set(args.run_id)
        print(summary_path)
        blocked = [r for r in results if r.get("disposition") == "blocked"]
        return 2 if blocked else 0
    if args.visible_scanline_high_visibility_ladder_set:
        summary_path, results = build_visible_scanline_high_visibility_ladder_set(args.run_id)
        print(summary_path)
        blocked = [r for r in results if r.get("disposition") == "blocked"]
        return 2 if blocked else 0
    final_manifests: list[tuple[str, Path]] = []
    if args.active_final_set:
        final_manifests.extend((target, Path(path)) for target, path in ACTIVE_FINAL_MANIFESTS.items())
    if args.first_eight_final_set:
        final_manifests.extend(resolve_first_eight_final_manifests())
    if args.visible_scanline_first_eight_final_set:
        final_manifests.extend(resolve_first_eight_final_manifests())
    if args.current_final_set:
        final_manifests.extend(discover_current_final_manifests())
    for target in args.target or []:
        final_manifests.append((target, Path(ALL_KNOWN_FINAL_MANIFESTS[target])))
    for manifest in args.final_manifest or []:
        final_manifests.append((manifest.stem, manifest))
    if not final_manifests:
        raise SystemExit(
            "No targets supplied. Use --visible-scanline-calibration-set, "
            "--visible-scanline-strength-ladder-set, --visible-scanline-high-visibility-ladder-set, "
            "--visible-scanline-first-eight-final-set, --visible-scanline-final-gate, "
            "--first-eight-final-set, --current-final-set, --active-final-set, --target, or --final-manifest."
        )

    deduped: dict[str, Path] = {}
    for target, manifest_path in final_manifests:
        deduped[target] = manifest_path
    final_manifests = list(deduped.items())

    visible_scanline_final = bool(args.visible_scanline_first_eight_final_set or args.visible_scanline_final_gate)
    selected_scanline_spec = selected_visible_scanline_variant() if visible_scanline_final else None
    run_pass_id = VISIBLE_SCANLINE_FULL_PASS_ID if visible_scanline_final else CORRECTED_PASS_ID
    run_schema_version = PASS07_SCHEMA_VERSION if visible_scanline_final else PASS04_SCHEMA_VERSION
    run_texture_schema_version = PASS07_TEXTURE_SCHEMA_VERSION if visible_scanline_final else PASS04_TEXTURE_SCHEMA_VERSION
    run_metrics_schema_version = PASS07_METRICS_SCHEMA_VERSION if visible_scanline_final else PASS04_METRICS_SCHEMA_VERSION
    run_summary_schema_version = PASS07_SUMMARY_SCHEMA_VERSION if visible_scanline_final else PASS04_SUMMARY_SCHEMA_VERSION
    run_contract_read = visible_scanline_contract_read() if visible_scanline_final else contract_read()
    run_output_suffix = (
        "house_crt_visible_scanline_signal_interruption"
        if visible_scanline_final
        else "house_crt_signal_interruption"
    )
    challenger_reference = challenger_luma_neutral_reference(
        args.run_id,
        visible_scanline=visible_scanline_final,
        scanline_spec=selected_scanline_spec,
    )
    results = []
    for target, manifest_path in final_manifests:
        print(f"[house-crt-signal:{run_pass_id}] {target}: {manifest_path}", flush=True)
        try:
            results.append(
                build_target(
                    target,
                    manifest_path,
                    args.run_id,
                    challenger_reference=challenger_reference,
                    pass_id=run_pass_id,
                    schema_version=run_schema_version,
                    texture_schema_version=run_texture_schema_version,
                    metrics_schema_version=run_metrics_schema_version,
                    visible_scanline=visible_scanline_final,
                    scanline_spec=selected_scanline_spec,
                    output_suffix=run_output_suffix,
                    supersedes_pass_id=CORRECTED_PASS_ID if visible_scanline_final else SUPERSEDED_PASS_ID,
                )
            )
        except subprocess.CalledProcessError as exc:
            results.append(
                {
                    "target": target,
                    "source_final_export_manifest_path": str(manifest_path),
                    "created_at": args.run_id,
                    "disposition": "blocked",
                    "pass_id": run_pass_id,
                    "blocked_reason": "ffmpeg_or_probe_failed",
                    "command": exc.cmd,
                    "returncode": exc.returncode,
                }
            )
        except Exception as exc:  # noqa: BLE001 - block only the failing target and keep scoped run evidence.
            results.append(
                {
                    "target": target,
                    "source_final_export_manifest_path": str(manifest_path),
                    "created_at": args.run_id,
                    "disposition": "blocked",
                    "pass_id": run_pass_id,
                    "blocked_reason": "render_or_validation_failed",
                    "error": str(exc),
                }
            )
    summary_suffix = (
        "house_crt_clean_source_lineage_visible_scanline_first8_summary"
        if visible_scanline_final
        else "house_crt_clean_source_lineage_first8_summary"
    )
    summary_path = Path.cwd() / f"{args.run_id}__{summary_suffix}.json"
    target_set = (
        "first_eight_visible_scanline_final_set"
        if args.visible_scanline_first_eight_final_set
        else "first_eight_final_set"
        if args.first_eight_final_set
        else "current_final_set"
        if args.current_final_set
        else "active_final_set"
        if args.active_final_set
        else "explicit_targets"
    )
    write_json(
        summary_path,
        {
            "schema_version": run_summary_schema_version,
            "created_at": args.run_id,
            "pass_id": run_pass_id,
            "target_set": target_set,
            "expected_first_eight_targets": list(FIRST_EIGHT_TARGET_ORDER)
            if (args.first_eight_final_set or args.visible_scanline_first_eight_final_set)
            else [],
            "house_crt_contract_id": HOUSE_CRT_CONTRACT_ID,
            "house_crt_contract_read": run_contract_read,
            "selected_scanline_strength_variant": selected_scanline_spec or {},
            "visual_layer_order_read": visual_layer_order_read(),
            "source_lineage_gate_read": {
                "required": True,
                "clean_source_confirmed_required": True,
                "rejects": [
                    "historical_signal_texture_used_true",
                    "historical_signal_texture_applied_true",
                    "historical_signal_texture_read_pass_as_selected_source",
                    "selected_visual_or_segment_path_under_historical_signal_texture",
                ],
                "pass05_preserved_as_diagnostic": True,
                "pass06_preserved_as_diagnostic": visible_scanline_final,
                "superseded_diagnostic_pass_id": CORRECTED_PASS_ID if visible_scanline_final else SUPERSEDED_PASS_ID,
            },
            "challenger_reference": challenger_reference,
            "results": results,
        },
    )
    print(summary_path)
    blocked = [r for r in results if r.get("disposition") == "blocked"]
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
