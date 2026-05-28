#!/usr/bin/env python3
"""Build a stronger-visibility variant of the Pressure Bends bass-drum pulse intro."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
BASE_BUILDER = REPO_ROOT / "scripts/build_channel_intro_pressure_bends_original_format_bass_drum_pulse_fix.py"
REVIEW_PREDECESSOR_PACKAGE = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_pulse_fix_20260527T185050Z"
)
REVIEW_PREDECESSOR_MANIFEST = (
    REVIEW_PREDECESSOR_PACKAGE / "channel_intro_pressure_bends_original_format_bass_drum_pulse_fix_manifest.json"
)


def load_base():
    spec = importlib.util.spec_from_file_location("channel_intro_bass_drum_pulse_base", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load base builder: {BASE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["channel_intro_bass_drum_pulse_base"] = module
    spec.loader.exec_module(module)
    return module


base = load_base()

base.WORKFLOW = "channel_intro_pressure_bends_original_format_bass_drum_pulse_visibility_fix_v1"
base.OUTPUT_STEM = "channel_intro_pressure_bends_original_format_bass_drum_pulse_visibility_fix"
base.LATEST_POINTER = base.OUTPUT_ROOT / f"{base.OUTPUT_STEM}_latest.json"
base.PULSE_CONFIG = {
    **base.PULSE_CONFIG,
    "visibility_profile": "stronger_review_v1",
    "visibility_multiplier_from_prior": 2.0,
    "brightness_lift": 0.11,
    "wash_mix": 0.165,
    "contrast_lift": 0.035,
    "background_mask_blur_px": 12,
}

_base_build_manifest = base.build_manifest


def build_manifest(*, pulse_sample_report: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    manifest = _base_build_manifest(pulse_sample_report=pulse_sample_report, **kwargs)
    manifest["lineage"]["review_predecessor_package"] = str(REVIEW_PREDECESSOR_PACKAGE)
    manifest["lineage"]["review_predecessor_manifest"] = str(REVIEW_PREDECESSOR_MANIFEST)
    manifest["lineage"]["review_predecessor_manifest_sha256"] = (
        base.sha256(REVIEW_PREDECESSOR_MANIFEST) if REVIEW_PREDECESSOR_MANIFEST.exists() else ""
    )
    manifest["lineage"]["visual_render_source_package"] = str(base.PREDECESSOR_PACKAGE)
    manifest["lineage"]["supersedes_reason"] = "bass_drum_background_pulse_visibility_too_subtle"
    manifest["bass_drum_pulse"]["visibility_profile"] = {
        "profile_id": "stronger_review_v1",
        "brightness_lift": base.PULSE_CONFIG["brightness_lift"],
        "wash_mix": base.PULSE_CONFIG["wash_mix"],
        "contrast_lift": base.PULSE_CONFIG["contrast_lift"],
        "background_mask_blur_px": base.PULSE_CONFIG["background_mask_blur_px"],
        "timing_change_read": "pass_no_timing_or_hit_map_model_change",
    }
    manifest["reads"]["pulse_visibility_increase_read"] = "pass_pulse_visual_treatment_strength_increased_without_timing_change"
    manifest["reads"]["pulse_timing_unchanged_read"] = "pass_same_low_band_hit_detector_and_frame_lock_model"
    manifest["visual_qa"]["pulse_sample_report"]["visibility_profile"] = "stronger_review_v1"
    manifest["visual_qa"]["pulse_sample_report"]["prior_background_delta_mean_reference"] = "about_2_4_to_2_8_luma"
    return manifest


base.build_manifest = build_manifest


if __name__ == "__main__":
    base.main()
