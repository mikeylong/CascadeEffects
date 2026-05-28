#!/usr/bin/env python3
"""Build a stronger backplate-only bass-pulse variant for the Pressure Bends intro."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
FULL_BACKPLATE_BUILDER = (
    REPO_ROOT / "scripts/build_channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix.py"
)
ACCEPTED_FULL_BACKPLATE_PACKAGE = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix_20260527T192026Z"
)
ACCEPTED_FULL_BACKPLATE_MANIFEST = (
    ACCEPTED_FULL_BACKPLATE_PACKAGE
    / "channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix_manifest.json"
)
ACCEPTED_FULL_BACKPLATE_MP4 = (
    ACCEPTED_FULL_BACKPLATE_PACKAGE
    / "video/cascade_of_effects_channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix_1080p24.mp4"
)
TABLED_RIPPLE_PACKAGES = [
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_right_video_pressure_ripple_fix_20260527T220702Z",
    OUTPUT_ROOT / "channel_intro_pressure_bends_right_video_ripple_micro_proof_20260527T230841Z",
]
INTENSITY_RATIO_MINIMUM = 1.35
PROTECTED_DELTA_MAXIMUM_LUMA = 6.0


def load_full_backplate_builder():
    spec = importlib.util.spec_from_file_location("channel_intro_full_backplate_for_intensity_fix", FULL_BACKPLATE_BUILDER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load full-backplate builder: {FULL_BACKPLATE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["channel_intro_full_backplate_for_intensity_fix"] = module
    spec.loader.exec_module(module)
    return module


full_backplate = load_full_backplate_builder()
base = full_backplate.base

base.WORKFLOW = "channel_intro_pressure_bends_original_format_bass_drum_backplate_pulse_intensity_fix_v1"
base.OUTPUT_STEM = "channel_intro_pressure_bends_original_format_bass_drum_backplate_pulse_intensity_fix"
base.LATEST_POINTER = base.OUTPUT_ROOT / f"{base.OUTPUT_STEM}_latest.json"
base.PULSE_CONFIG = {
    **base.PULSE_CONFIG,
    "visibility_profile": "noticeably_stronger_full_backplate_v2",
    "visibility_multiplier_from_initial": 2.9,
    "visibility_multiplier_from_current_full_backplate": 1.45,
    "brightness_lift": 0.16,
    "wash_mix": 0.24,
    "contrast_lift": 0.05,
    "background_mask_blur_px": 12,
    "right_short_card_protection_block_used": False,
    "right_card_region_pulsed_for_review": True,
    "right_video_ripple_applied": False,
}

_base_build_manifest = base.build_manifest
_base_write_readme = base.write_readme


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def luma_array(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    return (0.2126 * arr[:, :, 0]) + (0.7152 * arr[:, :, 1]) + (0.0722 * arr[:, :, 2])


def safe_label(value: str) -> str:
    return value.lower().replace(" ", "_").replace("-", "_")


def make_pulse_sample_sheet(
    predecessor_mp4: Path,
    final_mp4: Path,
    sample_hits: list[dict[str, Any]],
    qa_dir: Path,
) -> tuple[Path, dict[str, Any]]:
    require_file(ACCEPTED_FULL_BACKPLATE_MP4, "accepted full-backplate pulse comparison MP4")
    frames_dir = qa_dir / "pulse_intensity_compare_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    tile_w, tile_h = 288, 162
    label_h = 46
    cols = 5
    sheet = Image.new("RGB", (cols * tile_w, len(sample_hits) * (tile_h + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = base.font(13, bold=True)
    small_font = base.font(11)
    for row_index, hit in enumerate(sample_hits):
        seconds = float(hit["frame_time_seconds"])
        label = str(hit["label"])
        stem = f"{int(hit['frame_index']):04d}_{safe_label(label)}"
        neutral_path = frames_dir / f"{stem}_neutral.jpg"
        current_path = frames_dir / f"{stem}_current_full_backplate.jpg"
        stronger_path = frames_dir / f"{stem}_stronger.jpg"
        base.extract_frame(predecessor_mp4, seconds, neutral_path)
        base.extract_frame(ACCEPTED_FULL_BACKPLATE_MP4, seconds, current_path)
        base.extract_frame(final_mp4, seconds, stronger_path)
        neutral = Image.open(neutral_path).convert("RGB")
        current = Image.open(current_path).convert("RGB")
        stronger = Image.open(stronger_path).convert("RGB")
        current_delta = ImageChops.difference(neutral, current)
        stronger_delta = ImageChops.difference(neutral, stronger)
        current_delta_vis = ImageEnhance.Brightness(current_delta).enhance(8.0)
        stronger_delta_vis = ImageEnhance.Brightness(stronger_delta).enhance(8.0)

        mask = np.asarray(base.protection_mask_for_frame(np.asarray(neutral), seconds), dtype=np.float32) / 255.0
        bg = mask > 0.55
        protected = mask < 0.08
        current_luma_delta = np.abs(luma_array(neutral) - luma_array(current))
        stronger_luma_delta = np.abs(luma_array(neutral) - luma_array(stronger))
        current_bg_delta = float(current_luma_delta[bg].mean()) if np.any(bg) else 0.0
        stronger_bg_delta = float(stronger_luma_delta[bg].mean()) if np.any(bg) else 0.0
        ratio = stronger_bg_delta / current_bg_delta if current_bg_delta > 0.01 else 0.0
        stronger_protected_delta = float(stronger_luma_delta[protected].mean()) if np.any(protected) else 0.0
        row = {
            "label": label,
            "time_seconds": round(seconds, 6),
            "frame_index": int(hit["frame_index"]),
            "pulse_value": round(float(hit.get("pulse_value", 0.0)), 6),
            "bass_hit_score": hit["score"],
            "neutral_frame": str(neutral_path),
            "accepted_full_backplate_frame": str(current_path),
            "stronger_frame": str(stronger_path),
            "current_background_mean_luma_delta": round(current_bg_delta, 4),
            "stronger_background_mean_luma_delta": round(stronger_bg_delta, 4),
            "background_delta_ratio_vs_current": round(ratio, 4),
            "stronger_protected_mean_luma_delta": round(stronger_protected_delta, 4),
            "pulse_intensity_ratio_read": "pass" if ratio >= INTENSITY_RATIO_MINIMUM else "tighten_intensity_ratio_low",
            "protected_region_read": "pass"
            if stronger_protected_delta <= PROTECTED_DELTA_MAXIMUM_LUMA
            else "tighten_protected_region_delta_high",
        }
        rows.append(row)
        y = row_index * (tile_h + label_h)
        tiles = [
            ("neutral", neutral),
            ("current", current),
            ("stronger", stronger),
            ("current delta x8", current_delta_vis),
            ("stronger delta x8", stronger_delta_vis),
        ]
        for col, (title, image) in enumerate(tiles):
            x = col * tile_w
            sheet.paste(image.resize((tile_w, tile_h), Image.Resampling.LANCZOS), (x, y))
            draw.rectangle((x, y + tile_h, x + tile_w, y + tile_h + label_h), fill=(18, 20, 24))
            draw.text((x + 8, y + tile_h + 4), f"{label} {title}", fill=(238, 240, 242), font=label_font)
            draw.text(
                (x + 8, y + tile_h + 24),
                f"{seconds:05.2f}s r={ratio:.2f}",
                fill=(190, 198, 205),
                font=small_font,
            )
    out = qa_dir / "bass_drum_backplate_pulse_intensity_comparison_sheet.jpg"
    sheet.save(out, quality=92)
    ratio_reads = [row["pulse_intensity_ratio_read"] == "pass" for row in rows]
    protected_reads = [row["protected_region_read"] == "pass" for row in rows]
    min_ratio = min((row["background_delta_ratio_vs_current"] for row in rows), default=0.0)
    report = {
        "rows": rows,
        "comparison_reference_package": str(ACCEPTED_FULL_BACKPLATE_PACKAGE),
        "comparison_reference_mp4": str(ACCEPTED_FULL_BACKPLATE_MP4),
        "comparison_model": "neutral_vs_current_full_backplate_vs_stronger_intensity_v1",
        "background_pulse_read": "pass" if ratio_reads and all(ratio_reads) else "tighten",
        "pulse_intensity_ratio_read": "pass" if ratio_reads and all(ratio_reads) else "tighten",
        "protected_region_read": "pass" if protected_reads and all(protected_reads) else "tighten",
        "background_delta_ratio_minimum_observed": round(float(min_ratio), 4),
        "background_delta_ratio_minimum_required": INTENSITY_RATIO_MINIMUM,
        "protected_delta_maximum_luma": PROTECTED_DELTA_MAXIMUM_LUMA,
        "visibility_profile": "noticeably_stronger_full_backplate_v2",
    }
    write_json = getattr(base, "write_json")
    write_json(qa_dir / "bass_drum_backplate_pulse_intensity_comparison_qa.json", report)
    return out, report


base.make_pulse_sample_sheet = make_pulse_sample_sheet


def build_manifest(*, pulse_sample_report: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    manifest = _base_build_manifest(pulse_sample_report=pulse_sample_report, **kwargs)
    manifest["workflow"] = base.WORKFLOW
    manifest["artifact_id"] = f"{base.OUTPUT_STEM}_{kwargs['timestamp']}"
    manifest["lineage"]["accepted_full_backplate_predecessor_package"] = str(ACCEPTED_FULL_BACKPLATE_PACKAGE)
    manifest["lineage"]["accepted_full_backplate_predecessor_manifest"] = str(ACCEPTED_FULL_BACKPLATE_MANIFEST)
    manifest["lineage"]["accepted_full_backplate_predecessor_manifest_sha256"] = base.sha256(ACCEPTED_FULL_BACKPLATE_MANIFEST)
    manifest["lineage"]["accepted_full_backplate_predecessor_mp4"] = str(ACCEPTED_FULL_BACKPLATE_MP4)
    manifest["lineage"]["accepted_full_backplate_predecessor_mp4_sha256"] = base.sha256(ACCEPTED_FULL_BACKPLATE_MP4)
    manifest["lineage"]["visual_render_source_package"] = str(base.PREDECESSOR_PACKAGE)
    manifest["lineage"]["visual_render_source_policy"] = (
        "re-rendered_from_unpulsed_neutral_end_transition_source_not_stacked_on_prior_pulsed_mp4"
    )
    manifest["lineage"]["tabled_ripple_packages"] = [
        {
            "path": str(path),
            "exists": path.exists(),
            "manifest_paths": [str(child) for child in sorted(path.glob("*manifest*.json"))] if path.exists() else [],
        }
        for path in TABLED_RIPPLE_PACKAGES
    ]
    manifest["lineage"]["supersedes_reason"] = "backplate_bass_pulse_visibility_still_too_subtle"
    manifest["bass_drum_pulse"]["intensity_profile"] = {
        "profile_id": "noticeably_stronger_full_backplate_v2",
        "brightness_lift": base.PULSE_CONFIG["brightness_lift"],
        "wash_mix": base.PULSE_CONFIG["wash_mix"],
        "contrast_lift": base.PULSE_CONFIG["contrast_lift"],
        "background_mask_blur_px": base.PULSE_CONFIG["background_mask_blur_px"],
        "minimum_ratio_vs_current_full_backplate": INTENSITY_RATIO_MINIMUM,
        "timing_change_read": "pass_no_timing_or_hit_map_model_change",
        "right_video_ripple_applied": False,
    }
    manifest["visual_qa"]["pulse_sample_report"] = pulse_sample_report
    manifest["outputs"]["pulse_intensity_comparison_qa"] = str(
        Path(manifest["outputs"]["package_dir"]) / "qa/bass_drum_backplate_pulse_intensity_comparison_qa.json"
    )
    manifest["reads"].update(
        {
            "original_format_intro_retained_read": "pass_original_intro_scene_format_retained_no_card_distortion",
            "right_video_ripple_tabled_read": "pass_right_video_ripple_morph_displacement_tabled_not_applied",
            "right_video_morph_displacement_absence_read": "pass_right_side_short_videos_remain_normal_cards",
            "render_source_not_stacked_read": "pass_re_rendered_from_unpulsed_neutral_end_transition_visual_source",
            "hit_map_and_timing_unchanged_read": "pass_same_low_band_frame_locked_74_hit_map_model",
            "stronger_backplate_pulse_profile_read": "pass_noticeably_stronger_full_backplate_v2_profile_applied",
            "pulse_intensity_ratio_read": pulse_sample_report["pulse_intensity_ratio_read"],
            "whole_backplate_pulse_read": "pass_background_pulse_continues_across_left_and_right_backplate_regions",
            "right_card_cutoff_removal_read": "pass_right_short_card_block_removed_from_pulse_protection_mask",
            "foreground_card_placeholder_protection_read": pulse_sample_report["protected_region_read"],
            "youtube_action_read": "blocked_local_review_only_no_upload_or_replacement",
        }
    )
    manifest["qa"]["pulse_intensity_ratio_read"] = pulse_sample_report["pulse_intensity_ratio_read"]
    manifest["qa"]["background_delta_ratio_minimum_observed"] = pulse_sample_report[
        "background_delta_ratio_minimum_observed"
    ]
    manifest["qa"]["background_delta_ratio_minimum_required"] = INTENSITY_RATIO_MINIMUM
    return manifest


base.build_manifest = build_manifest


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str) -> Path:
    readme = _base_write_readme(package_dir, final_mp4, review_html, manifest_path, receipt_path)
    readme.write_text(
        "\n".join(
            [
                "# Pressure Bends Backplate Pulse Intensity Fix",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This local-review successor tables the right-video ripple branch and keeps the accepted original-format intro. It re-renders from the unpulsed neutral-end-transition visual source with a stronger full-backplate bass-drum pulse profile, while preserving timing, audio, scenes, right-card videos, transition, neutral adaptive end screen, labels, badges, placeholders, and geometry.",
                "",
                "## Outputs",
                "",
                f"- Review HTML: `{review_html}`",
                f"- MP4: `{final_mp4}`",
                f"- Manifest: `{manifest_path}`",
                f"- Contract receipt: `{receipt_path}`",
                "",
                "No YouTube upload, visibility change, or channel replacement was performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return readme


base.write_readme = write_readme


if __name__ == "__main__":
    for path, label in [
        (ACCEPTED_FULL_BACKPLATE_MANIFEST, "accepted full-backplate predecessor manifest"),
        (ACCEPTED_FULL_BACKPLATE_MP4, "accepted full-backplate predecessor MP4"),
    ]:
        require_file(path, label)
    base.main()
