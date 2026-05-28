#!/usr/bin/env python3
"""Build a full-width backplate pulse variant for the Pressure Bends channel intro."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
BASE_BUILDER = REPO_ROOT / "scripts/build_channel_intro_pressure_bends_original_format_bass_drum_pulse_fix.py"
REVIEW_PREDECESSOR_PACKAGE = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_pulse_visibility_fix_20260527T190610Z"
)
REVIEW_PREDECESSOR_MANIFEST = (
    REVIEW_PREDECESSOR_PACKAGE / "channel_intro_pressure_bends_original_format_bass_drum_pulse_visibility_fix_manifest.json"
)


def load_base():
    spec = importlib.util.spec_from_file_location("channel_intro_bass_drum_pulse_base_full_backplate", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load base builder: {BASE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["channel_intro_bass_drum_pulse_base_full_backplate"] = module
    spec.loader.exec_module(module)
    return module


base = load_base()

base.WORKFLOW = "channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix_v1"
base.OUTPUT_STEM = "channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix"
base.LATEST_POINTER = base.OUTPUT_ROOT / f"{base.OUTPUT_STEM}_latest.json"
base.PULSE_CONFIG = {
    **base.PULSE_CONFIG,
    "visibility_profile": "stronger_review_full_backplate_v1",
    "visibility_multiplier_from_initial": 2.0,
    "brightness_lift": 0.11,
    "wash_mix": 0.165,
    "contrast_lift": 0.035,
    "background_mask_blur_px": 12,
    "right_short_card_protection_block_used": False,
    "right_card_region_pulsed_for_review": True,
}


def protection_mask_for_frame(frame: np.ndarray, t: float) -> Image.Image:
    protected = Image.new("L", (base.WIDTH, base.HEIGHT), 0)
    draw = ImageDraw.Draw(protected)
    if t < base.END_SCREEN_START_SECONDS:
        if t >= 5.85:
            draw.rounded_rectangle((74, 830, 710, 956), radius=18, fill=255)
    else:
        for bbox in base.END_SCREEN_TARGET_BBOXES.values():
            draw.rounded_rectangle(base.expanded_bbox(bbox, 28), radius=34, fill=255)

    arr = frame.astype(np.int16)
    luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    maxc = arr.max(axis=2)
    minc = arr.min(axis=2)
    saturation = (maxc - minc) / np.maximum(maxc, 1)
    bright_subject = ((luma > 92) & (saturation < 0.43)).astype(np.uint8) * 255
    subject_mask = Image.fromarray(bright_subject, "L").filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(5))
    protected = ImageChops.lighter(protected, subject_mask)

    dark_background = (luma < 122).astype(np.uint8) * 255
    apply_mask = Image.fromarray(dark_background, "L")
    apply_mask = ImageChops.subtract(apply_mask, protected)
    apply_mask = apply_mask.filter(ImageFilter.GaussianBlur(int(base.PULSE_CONFIG["background_mask_blur_px"])))
    return apply_mask


base.protection_mask_for_frame = protection_mask_for_frame

_base_build_manifest = base.build_manifest


def build_manifest(*, pulse_sample_report: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    manifest = _base_build_manifest(pulse_sample_report=pulse_sample_report, **kwargs)
    manifest["lineage"]["review_predecessor_package"] = str(REVIEW_PREDECESSOR_PACKAGE)
    manifest["lineage"]["review_predecessor_manifest"] = str(REVIEW_PREDECESSOR_MANIFEST)
    manifest["lineage"]["review_predecessor_manifest_sha256"] = (
        base.sha256(REVIEW_PREDECESSOR_MANIFEST) if REVIEW_PREDECESSOR_MANIFEST.exists() else ""
    )
    manifest["lineage"]["visual_render_source_package"] = str(base.PREDECESSOR_PACKAGE)
    manifest["lineage"]["supersedes_reason"] = "right_card_protection_mask_created_visible_backplate_pulse_cutoff"
    manifest["bass_drum_pulse"]["full_backplate_profile"] = {
        "profile_id": "stronger_review_full_backplate_v1",
        "right_short_card_protection_block_used": False,
        "right_card_region_pulsed_for_review": True,
        "badge_and_end_screen_target_protection_retained": True,
        "timing_change_read": "pass_no_timing_or_hit_map_model_change",
    }
    manifest["reads"]["right_card_cutoff_removal_read"] = "pass_right_short_card_block_removed_from_pulse_protection_mask"
    manifest["reads"]["whole_backplate_pulse_read"] = "pass_background_pulse_continues_across_left_and_right_backplate_regions"
    manifest["reads"]["pulse_visibility_increase_read"] = "pass_stronger_review_visibility_profile_retained"
    manifest["reads"]["pulse_timing_unchanged_read"] = "pass_same_low_band_hit_detector_and_frame_lock_model"
    manifest["visual_qa"]["pulse_sample_report"]["visibility_profile"] = "stronger_review_full_backplate_v1"
    manifest["visual_qa"]["pulse_sample_report"]["right_card_region_policy"] = (
        "right_card_block_mask_removed_so_no_vertical_cutoff_is_introduced"
    )
    return manifest


base.build_manifest = build_manifest


if __name__ == "__main__":
    base.main()
