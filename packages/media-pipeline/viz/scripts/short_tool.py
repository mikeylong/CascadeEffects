#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_tool import WorkflowCompiler, WorkflowError, write_json

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:  # pragma: no cover - Pillow is expected in the repo env
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageOps = None


SHORT_MANIFEST_REQUIRED_FIELDS = {
    "short_id",
    "title",
    "audio_path",
    "transcript_path",
    "short_audio_package_path",
    "expected_voice_profile_id",
    "audio_package_sha256",
    "audio_disposition",
    "caption_source_path",
    "transcript_sha256",
    "fps",
    "packaging_frame_id",
    "beats",
}
BEAT_REQUIRED_FIELDS = {
    "id",
    "preset_id",
    "cue_start_seconds",
    "cue_end_seconds",
    "target_duration_seconds",
    "motion_prompt",
    "motion_pipeline",
}
BEAT_OPTIONAL_FLOAT_FIELDS = {
    "motion_head_trim_seconds",
    "motion_handle_seconds",
}
REQUIRED_STAGES = ("draft_txt2img", "refine_img2img", "final_upscale")
SHORTS_OUTPUT_DIRNAME = "shorts"
EXPERIMENTS_DIRNAME = "experiments"
DEFAULT_I2V_WIDTH = 576
DEFAULT_I2V_HEIGHT = 1024
DEFAULT_RENDER_QUALITY = "standard"
DELIVERY_MODES = {"strict", "advisory"}
CLIP_MODES = {"animated", "still_holds"}
DEFAULT_I2V_TYPOGRAPHY = "off"
APPLE_LTX23_ONE_STAGE_PIPELINE = "apple-ltx23-q8-one-stage"
PIPELINE_MANIFEST_SUFFIX = "__pipeline.run.json"
FINALIZE_STILL_MANIFEST_SUFFIX = "__finalize_still.run.json"
PROOF_AUDIO_DRIFT_TOLERANCE = 0.25
SHORT_ASPECT_RATIO = 9.0 / 16.0
SHORT_ASPECT_TOLERANCE = 0.03
SCRIPT_LOCKED_CAPTION_MODEL = "script_locked_canonical_text_timing_from_asr_v1"
SCRIPT_LOCKED_TEXT_POLICY = "script_locked_canonical_text_only"
ASR_TIMING_POLICY = "asr_whisperx_timing_only"
BLOCKED_CAPTION_WORD_SOURCE_MARKERS = (
    ".diarized",
    "whisperx",
    "raw_asr",
    "asr_transcript",
    "transcripts_mastered",
    "transcripts_final",
)


def caption_word_source_looks_blocked(path: Path) -> bool:
    token = str(path).lower()
    if "script_locked" in token or "locked_script" in token or "canonical_script" in token:
        return False
    return any(marker in token for marker in BLOCKED_CAPTION_WORD_SOURCE_MARKERS)


def pass_read(value: Any) -> bool:
    normalized = normalize_text(value)
    if normalized.startswith("pass_review") or normalized.startswith("pass_pending"):
        return False
    return normalized == "pass" or normalized.startswith("pass_") or normalized.startswith("pass ")
OVERLAY_SCOPES = {"whole_short"}
OVERLAY_APPLY_STAGES = {"post_picture_master_pre_mux"}
OVERLAY_PRESET_DEFAULT_STRENGTHS = {
    "prismatic_glass_soft_v1": 0.16,
    "prismatic_glass_v1": 0.22,
    "prismatic_glass_glitch_v1": 0.28,
}
DEFAULT_CAPTION_STYLE_PRESET = "minimal_surreal_editorial_v1"
ACTIVE_SHORT_PROFILE_ID = "youtube_shorts_mike_challenger_match_v1"
DEFAULT_MUSIC_TRACK_REGISTRY_PATH = Path(
    "/Users/mike/CascadeEffects/packages/production-registry/shorts/music_track_registry.json"
)
DEFAULT_MUSIC_TRACK_ID = "paper_architecture_theme_v1"
MUSIC_POLICIES = ("canonical_default", "waived", "alternate_approved")
DEFAULT_MUSIC_RIGHTS_CHECK_STATUS = "pending_youtube_upload_check"
MOTIF_OUTRO_DEFAULT_TEXT = "Small causes, massive consequences."
HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH = Path(
    "/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json"
)
HISTORICAL_SIGNAL_PROFILE_IDS = (
    "era_1940s_archival_film_v1",
    "era_1980s_broadcast_crt_v1",
    "era_1980s_institutional_video_v1",
    "era_1990s_news_v1",
    "era_2000s_digital_news_v1",
    "era_2010s_mobile_news_v1",
)
HISTORICAL_SIGNAL_STRENGTHS = (
    "low",
    "low_to_visible",
    "low_to_medium",
    "visible_but_premium",
    "medium",
)
HOUSE_CRT_FINAL_CONTRACT_ID = "house_crt_luma_neutral_chroma_signal_interruption_v1"
HOUSE_CRT_FINAL_PROFILE_ID = "era_1980s_broadcast_crt_v1"
HOUSE_CRT_FINAL_INTENSITY = "visible_but_premium"
HOUSE_CRT_FINAL_TONE_POLICY = "luma_neutral_chroma_visible_scanline_v1"
HOUSE_CRT_FINAL_CALIBRATION_RECIPE_ID = "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1"
HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID = HOUSE_CRT_FINAL_CALIBRATION_RECIPE_ID
HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE = (
    "house_crt_static_final_pass.luma_neutral_chroma_visible_scanline_filter_graph"
)
HOUSE_CRT_FINAL_SCANLINE_POLICY_ID = "luma_neutral_visible_scanline_modulation_v1"
HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID = "max_visible_bars_y24_p8"
HOUSE_CRT_FINAL_SCANLINE_DELTA_Y = 24.0
HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS = 8
HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS = 2
HOUSE_CRT_FINAL_CALIBRATION_ONLY_PASS_IDS = {
    "house_crt_visible_scanline_calibration_pass_07a",
    "house_crt_visible_scanline_strength_ladder_pass_07b",
    "house_crt_visible_scanline_high_visibility_ladder_pass_07c",
}
HOUSE_CRT_STATIC_PROFILE_ID = "era_1980s_horizontal_signal_interruption_v2_randomized"
HOUSE_CRT_STATIC_DURATION_SECONDS = 0.25
CAPTION_STYLE_PRESETS = {
    DEFAULT_CAPTION_STYLE_PRESET: {
        "font_name": "Arial",
        "font_size": 82,
        # ASS colors are AABBGGRR. This is minimal-surreal accent amber (#FFD54A).
        "font_color": "&H004AD5FF",
        "outline_color": "&HAA0E1116",
        "back_color": "&H00000000",
        "bold": -1,
        "border_style": 1,
        "outline": 4,
        "shadow": 2,
        "alignment": 2,
        "margin_l": 110,
        "margin_r": 110,
        "margin_v": 340,
        "max_line_chars": 26,
        "max_lines": 2,
        "max_text_width_px": 860,
        "target_segment_min_seconds": 1.2,
        "target_segment_max_seconds": 2.4,
        "placement": "centered mobile-safe lower third",
        "animation": "restrained",
        "must_not_cover": ["mechanism", "faces", "key anomaly", "crucial motion"],
    },
    "contemporary_aviation_news_v1": {
        "font_name": "Helvetica Neue",
        "font_size": 70,
        # Cool off-white (#E8F1F8) for 2010s mobile/news documentary captions.
        "font_color": "&H00F8F1E8",
        "outline_color": "&HAA261810",
        "back_color": "&H00000000",
        "bold": -1,
        "border_style": 1,
        "outline": 3,
        "shadow": 1,
        "alignment": 2,
        "margin_l": 110,
        "margin_r": 110,
        "margin_v": 340,
        "max_line_chars": 24,
        "max_lines": 2,
        "max_text_width_px": 860,
        "target_segment_min_seconds": 1.2,
        "target_segment_max_seconds": 2.4,
        "placement": "centered mobile-safe lower third",
        "animation": "restrained",
        "period_reference": "2010s aviation/news explainer captioning: neutral modern sans, not retro CRT, newsreel, or amber brand-title treatment",
        "must_not_cover": ["cockpit instruments", "aircraft motion", "engine detail", "faces", "key anomaly"],
    },
    "era_1940s_newsreel_ivory_v1": {
        "font_name": "Futura Condensed ExtraBold",
        "font_size": 78,
        # Warm ivory (#F2E8C8) with condensed Futura for 1940s archival/newsreel captioning.
        "font_color": "&H00C8E8F2",
        "outline_color": "&HAA1A211F",
        "back_color": "&H00000000",
        "bold": -1,
        "border_style": 1,
        "outline": 4,
        "shadow": 2,
        "alignment": 2,
        "margin_l": 110,
        "margin_r": 110,
        "margin_v": 350,
        "max_line_chars": 24,
        "max_lines": 2,
        "max_text_width_px": 860,
        "target_segment_min_seconds": 1.2,
        "target_segment_max_seconds": 2.4,
        "placement": "centered mobile-safe lower third",
        "animation": "restrained",
        "must_not_cover": ["mechanism", "faces", "key anomaly", "crucial motion"],
    },
    "era_1910s_newspaper_ivory_v1": {
        "font_name": "Baskerville",
        "font_size": 80,
        # Warm ivory (#F3E7C4) for 1910s newspaper/steamship-era captioning.
        "font_color": "&H00C4E7F3",
        "outline_color": "&HAA1D242A",
        "back_color": "&H00000000",
        "bold": -1,
        "border_style": 1,
        "outline": 4,
        "shadow": 2,
        "alignment": 2,
        "margin_l": 110,
        "margin_r": 110,
        "margin_v": 350,
        "max_line_chars": 23,
        "max_lines": 2,
        "max_text_width_px": 860,
        "target_segment_min_seconds": 1.2,
        "target_segment_max_seconds": 2.4,
        "placement": "centered mobile-safe lower third",
        "animation": "restrained",
        "period_reference": "1910s newspaper and steamship-era serif captioning, not 1940s newsreel or silent-film title cards",
        "must_not_cover": ["mechanism", "faces", "key anomaly", "crucial motion"],
    },
    "early_1980s_broadcast_cg_v1": {
        "font_name": "Andale Mono",
        "font_size": 76,
        # Pale phosphor/cyan-white (#DDF4FF) with a deep broadcast-blue edge.
        "font_color": "&H00FFF4DD",
        "outline_color": "&HAA4D1007",
        "back_color": "&H00000000",
        "bold": -1,
        "border_style": 1,
        "outline": 3,
        "shadow": 3,
        "alignment": 2,
        "margin_l": 110,
        "margin_r": 110,
        "margin_v": 350,
        "max_line_chars": 22,
        "max_lines": 2,
        "max_text_width_px": 820,
        "target_segment_min_seconds": 1.2,
        "target_segment_max_seconds": 2.4,
        "placement": "centered mobile-safe lower third",
        "animation": "restrained",
        "period_reference": "early-1980s broadcast character generator, not late-1980s desktop UI",
        "must_not_cover": ["mechanism", "faces", "key anomaly", "crucial motion"],
    },
    "documentary_lower_third_v1": {
        "font_name": "Arial",
        "font_size": 72,
        "font_color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&H99000000",
        "bold": -1,
        "border_style": 3,
        "outline": 3,
        "shadow": 0,
        "alignment": 2,
        "margin_l": 110,
        "margin_r": 110,
        "margin_v": 360,
        "max_line_chars": 28,
        "max_lines": 2,
        "max_text_width_px": 860,
        "target_segment_min_seconds": 1.2,
        "target_segment_max_seconds": 2.4,
        "placement": "centered mobile-safe lower third",
        "animation": "restrained",
        "must_not_cover": ["mechanism", "faces", "key anomaly", "crucial motion"],
    }
}
CAPTION_PLACEMENT_OVERRIDES = {
    "lower-center": {},
    "lower-left": {
        "alignment": 1,
        "margin_l": 80,
        "margin_r": 420,
        "margin_v": 360,
        "max_line_chars": 22,
        "placement": "mobile-safe lower-left third",
    },
}
BEAT_SHEET_COLUMNS = 3
BEAT_SHEET_TILE_WIDTH = 320
BEAT_SHEET_TILE_HEIGHT = 568
BEAT_SHEET_LABEL_HEIGHT = 112
BEAT_SHEET_MARGIN = 24
BEAT_SHEET_GUTTER = 18
BEAT_SHEET_HEADER_HEIGHT = 96
HEADLESS_PATHS_ENV_FIELDS = (
    "CE_COMFY_MAIN_PY",
    "CE_COMFY_PYTHON",
    "CE_COMFY_CLIP_VISION_MODEL",
    "CE_COMFY_HEADLESS_HOST",
    "CE_COMFY_HEADLESS_PORT",
)
MLX_VIDEO_PATHS_ENV_FIELDS = ("CE_MLX_VIDEO_DIR",)
MIDJOURNEY_DEFAULT_SUFFIX = "--v 7 --ar 9:16 --raw --s 75"
MIDJOURNEY_NEGATIVE_TERMS = ["text", "watermark", "logo", "crowd", "poster", "explosion"]
MIDJOURNEY_REFERENCE_MODE = "manual_upload_local_files_with_provenance"
MIDJOURNEY_SURFACE_TYPE = "short_beats"
MIDJOURNEY_REFERENCE_SELECTIONS = {
    "challenger": {
        "cover": ["opening_02", "act2_01", "act3_01", "act4_02"],
        "beats": {
            "beat_01": ["act3_06", "act3_07", "act3_08"],
            "beat_02": ["act2_01", "act2_05", "act2_06", "act2_02"],
            "beat_03": ["act3_01", "act3_02", "act3_03", "act3_04"],
            "beat_04": ["act4_01", "act4_02", "act4_03", "act4_04"],
            "beat_05": ["act4_02", "act4_04", "act4_06", "act4_07"],
            "beat_06": ["act2_03", "act2_04", "act2_08", "act1_05"],
            "beat_07": ["act2_01", "act3_01", "act4_02", "act2_08"],
        },
        "short_overrides": {
            "challenger_short_minimal_surreal_v3_trimmed": {
                "beats": {
                    "beat_01": ["act3_06", "act3_07", "act3_08", "act3_01"],
                    "beat_02": ["act2_01", "act2_05", "act2_06", "act2_02"],
                    "beat_03": ["act3_01", "act3_02", "act3_03", "act3_04"],
                    "beat_04": ["act4_01", "act4_02", "act4_04", "act4_06"],
                    "beat_05": ["act2_03", "act2_08", "act3_01", "act4_02"],
                },
            }
        },
    }
}


def add_build_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--delivery-mode",
        choices=sorted(DELIVERY_MODES),
        default="strict",
        help="strict requires QC-clean still pipelines; advisory keeps the best available still outputs and records QC failures as metadata.",
    )
    parser.add_argument(
        "--quality-profile",
        choices=["fast", "standard", "hero"],
        default=DEFAULT_RENDER_QUALITY,
        help="Render quality profile to use when building missing still pipelines.",
    )
    parser.add_argument(
        "--clip-mode",
        choices=sorted(CLIP_MODES),
        default="animated",
        help="animated renders motion clips through handoff-i2v; still_holds builds freeze-frame clips directly from stills.",
    )
    parser.add_argument(
        "--overlay-preset",
        choices=sorted(OVERLAY_PRESET_DEFAULT_STRENGTHS),
        help="Optional picture-master overlay preset override for this build.",
    )
    parser.add_argument(
        "--overlay-strength",
        type=float,
        help="Optional overlay strength override for this build (0.0-1.0).",
    )
    parser.add_argument(
        "--overlay-disable",
        action="store_true",
        help="Disable manifest overlay configuration for this build.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bin/ce short")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--models-root", required=True)
    parser.add_argument("--comfy-workflows-dir", required=True)
    parser.add_argument("--comfy-output-dir", required=True)
    parser.add_argument("--references-root", required=True)

    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("short_id")
    add_build_options(build_parser)
    build_manifest_parser = subparsers.add_parser("build-manifest")
    build_manifest_parser.add_argument("manifest_path", help="Absolute path to an active or quarantined short manifest.")
    add_build_options(build_manifest_parser)
    overlay_parser = subparsers.add_parser("overlay")
    overlay_parser.add_argument("target", help="Absolute path to a proof manifest or build directory.")
    overlay_parser.add_argument(
        "--preset",
        choices=sorted(OVERLAY_PRESET_DEFAULT_STRENGTHS),
        required=True,
        help="Overlay preset to apply to the existing picture master.",
    )
    overlay_parser.add_argument(
        "--strength",
        type=float,
        help="Optional overlay strength override (0.0-1.0). Defaults to the preset default.",
    )
    overlay_parser.add_argument(
        "--output-tag",
        help="Optional stable tag for the overlay variant. Defaults to a tag derived from preset and strength.",
    )
    historical_signal_parser = subparsers.add_parser("historical-signal-texture")
    historical_signal_parser.add_argument(
        "motion_manifest_path",
        help="Absolute path to the motion contact sheet, shot timing EDL, or motion manifest to texture.",
    )
    historical_signal_parser.add_argument(
        "--pass-id",
        required=True,
        help="Stable pass id for the historical signal texture package.",
    )
    historical_signal_parser.add_argument(
        "--review-note-output",
        required=True,
        help="Absolute path for the pending human/DP review note markdown artifact.",
    )
    historical_signal_parser.add_argument(
        "--output-root",
        help="Optional absolute output root. Defaults beside the input manifest under historical_signal_texture/.",
    )
    historical_signal_parser.add_argument(
        "--profile",
        choices=HISTORICAL_SIGNAL_PROFILE_IDS,
        help="Optional registry profile id. Required when eligible rows do not carry historical_signal_profile_id.",
    )
    historical_signal_parser.add_argument(
        "--strength",
        choices=HISTORICAL_SIGNAL_STRENGTHS,
        help="Optional strength override. Defaults to row strength, then registry profile default.",
    )
    beat_sheet_parser = subparsers.add_parser("beat-sheet")
    beat_sheet_parser.add_argument("target", help="Absolute path to a proof manifest or build directory.")
    beat_sheet_parser.add_argument(
        "--output",
        help="Optional absolute path for the beat sheet PNG. Defaults beside the proof manifest.",
    )
    final_export_parser = subparsers.add_parser("final-export")
    final_export_parser.add_argument("target", help="Absolute path to a proof manifest or build directory.")
    final_export_parser.add_argument(
        "--proof-review-note",
        required=True,
        help="Absolute path to the approved motion video proof review note.",
    )
    final_export_parser.add_argument(
        "--proof-disposition",
        choices=["keep", "tighten", "diagnostic-only", "reject"],
        required=True,
        help="Coordinator-approved motion proof disposition; must be keep.",
    )
    final_export_parser.add_argument(
        "--reel-class",
        choices=["keeper-short", "mixed-review-short"],
        required=True,
        help="Coordinator-approved reel class; must be keeper-short.",
    )
    final_export_parser.add_argument(
        "--all-motion-clips-keep",
        action="store_true",
        required=True,
        help="Required assertion that every motion clip included in the proof is keep.",
    )
    final_export_parser.add_argument(
        "--no-diagnostic-placeholders",
        action="store_true",
        required=True,
        help="Required assertion that no diagnostic placeholders remain in the final source proof.",
    )
    final_export_parser.add_argument(
        "--caption-style",
        choices=sorted(CAPTION_STYLE_PRESETS),
        default=DEFAULT_CAPTION_STYLE_PRESET,
        help="Caption style preset to burn into the final export.",
    )
    final_export_parser.add_argument(
        "--caption-placement",
        choices=sorted(CAPTION_PLACEMENT_OVERRIDES),
        default="lower-center",
        help="Optional placement override for proofs where the default caption position covers the mechanism.",
    )
    final_export_parser.add_argument(
        "--caption-source",
        help="Optional absolute script-locked caption text source path. Raw ASR/WhisperX/diarized transcripts are blocked as caption words.",
    )
    final_export_parser.add_argument(
        "--caption-timing",
        help="Optional absolute SRT, VTT, or JSON timing path. ASR/WhisperX text in this file is timing evidence only.",
    )
    final_export_parser.add_argument(
        "--manual-timing-adjustments",
        help="Optional absolute JSON file documenting manual caption timing adjustments.",
    )
    final_export_parser.add_argument(
        "--output-tag",
        help="Optional stable tag for the final export directory. Defaults to the caption style preset.",
    )
    final_export_parser.add_argument(
        "--music-policy",
        choices=MUSIC_POLICIES,
        default="canonical_default",
        help="Final music policy. Active Shorts default to the canonical Paper Architecture track.",
    )
    final_export_parser.add_argument(
        "--music-track-registry",
        default=str(DEFAULT_MUSIC_TRACK_REGISTRY_PATH),
        help="Absolute path to the Shorts music track registry.",
    )
    final_export_parser.add_argument(
        "--music-track-id",
        default=DEFAULT_MUSIC_TRACK_ID,
        help="Registry track id to use for canonical or alternate-approved final music.",
    )
    final_export_parser.add_argument(
        "--music-waiver-reason",
        default="",
        help="Required when --music-policy waived.",
    )
    final_export_parser.add_argument(
        "--music-rights-check-status",
        default=DEFAULT_MUSIC_RIGHTS_CHECK_STATUS,
        help="Rights/Content ID status to record in the final export manifest.",
    )
    final_export_parser.add_argument(
        "--source-motion-tail-path",
        help="Optional absolute no-audio 9:16 motion tail to use instead of cloned-frame visual padding.",
    )
    final_export_parser.add_argument(
        "--source-motion-tail-source-clip-id",
        default="",
        help="Approved source clip id for --source-motion-tail-path.",
    )
    final_export_parser.add_argument(
        "--source-motion-tail-source-path",
        default="",
        help="Absolute approved source path used to create --source-motion-tail-path.",
    )
    final_export_parser.add_argument(
        "--source-motion-tail-span-in",
        type=float,
        help="Local source in-point used to create --source-motion-tail-path.",
    )
    final_export_parser.add_argument(
        "--source-motion-tail-span-out",
        type=float,
        help="Local source out-point used to create --source-motion-tail-path.",
    )
    final_export_parser.add_argument(
        "--source-motion-tail-residual-hold-max",
        type=float,
        default=0.15,
        help="Maximum cloned-frame residual allowed after a supplied motion tail.",
    )
    final_export_parser.add_argument(
        "--house-crt-static-manifest",
        "--house-crt-final-gate-manifest",
        dest="house_crt_static_manifest",
        help=(
            "Absolute house CRT + Challenger-style signal-interruption final-gate manifest. "
            "Active Shorts require this unless "
            "--house-crt-static-waiver-reason is supplied."
        ),
    )
    final_export_parser.add_argument(
        "--house-crt-static-waiver-reason",
        default="",
        help="Explicit coordinator waiver reason when the active house CRT + signal-interruption final gate is not applied.",
    )
    export_midjourney_parser = subparsers.add_parser("export-midjourney")
    export_midjourney_parser.add_argument("short_id")
    return parser.parse_args()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_absolute_path(raw: str, *, label: str) -> Path:
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        raise WorkflowError(f"{label} must be an absolute path, got {raw!r}.")
    resolved = path.resolve()
    if not resolved.exists():
        raise WorkflowError(f"{label} was not found: {resolved}")
    return resolved


def ensure_command(name: str) -> None:
    if shutil.which(name):
        return
    raise WorkflowError(f"Required command is not available: {name}")


def duration_to_frames(duration_seconds: float, fps: int) -> int:
    if duration_seconds <= 0:
        raise WorkflowError(f"target_duration_seconds must be > 0, got {duration_seconds!r}.")
    if fps <= 0:
        raise WorkflowError(f"fps must be > 0, got {fps!r}.")
    return max(1, int(round(float(duration_seconds) * float(fps))))


def optional_nonnegative_float(raw: Any, *, label: str) -> float:
    if raw is None:
        return 0.0
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{label} must be a number.") from exc
    if value < 0:
        raise WorkflowError(f"{label} must be >= 0, got {value!r}.")
    return value


def coerce_motion_frames(frames: int, motion_pipeline: str) -> int:
    if motion_pipeline != APPLE_LTX23_ONE_STAGE_PIPELINE:
        return frames
    if frames <= 0:
        raise WorkflowError(f"frames must be > 0 before coercion, got {frames!r}.")
    lower = max(1, frames - ((frames - 1) % 8))
    if lower == frames:
        return frames
    upper = lower + 8
    lower_distance = abs(frames - lower)
    upper_distance = abs(upper - frames)
    return upper if upper_distance <= lower_distance else lower


def split_preset_id(raw: str, *, label: str) -> tuple[str, str]:
    family, separator, preset = str(raw).partition("/")
    if not separator or not family.strip() or not preset.strip():
        raise WorkflowError(f"{label} must use family/preset form, got {raw!r}.")
    return family.strip(), preset.strip()


def ffprobe_duration(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise WorkflowError(completed.stderr.strip() or completed.stdout.strip() or f"ffprobe failed for {path}")
    try:
        return float(completed.stdout.strip())
    except ValueError as exc:
        raise WorkflowError(f"ffprobe returned an invalid duration for {path}: {completed.stdout!r}") from exc


def ffprobe_dimensions(path: Path) -> tuple[int, int]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise WorkflowError(completed.stderr.strip() or completed.stdout.strip() or f"ffprobe failed for {path}")
    raw = completed.stdout.strip()
    try:
        width_text, height_text = raw.split("x", 1)
        return int(width_text), int(height_text)
    except ValueError as exc:
        raise WorkflowError(f"ffprobe returned invalid dimensions for {path}: {raw!r}") from exc


def ffprobe_video_info(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,width,height,avg_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise WorkflowError(completed.stderr.strip() or completed.stdout.strip() or f"ffprobe failed for {path}")
    try:
        payload = json.loads(completed.stdout)
        video = next(stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video")
    except (json.JSONDecodeError, StopIteration) as exc:
        raise WorkflowError(f"ffprobe did not find a video stream for {path}.") from exc
    fps_raw = str(video.get("avg_frame_rate") or "0/1")
    fps = 0.0
    if "/" in fps_raw:
        numerator, denominator = fps_raw.split("/", 1)
        try:
            fps = float(numerator) / float(denominator)
        except (TypeError, ValueError, ZeroDivisionError):
            fps = 0.0
    else:
        try:
            fps = float(fps_raw)
        except ValueError:
            fps = 0.0
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration_seconds": float(payload.get("format", {}).get("duration", 0.0)),
        "fps": fps or 24.0,
        "audio_stream_count": sum(1 for stream in payload.get("streams", []) if stream.get("codec_type") == "audio"),
    }


def extract_video_frame(video_path: Path, output_path: Path, *, seconds: float) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{max(0.0, seconds):.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip() or f"ffmpeg frame extraction failed for {video_path}"
        raise WorkflowError(details)
    if not output_path.exists():
        raise WorkflowError(f"Frame extraction did not create {output_path}")
    return output_path


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines or [""]


def slugify_tag(raw: str) -> str:
    tag = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(raw).strip())
    tag = re.sub(r"_+", "_", tag).strip("_.-")
    return tag or "final"


def parse_caption_timestamp(raw: str) -> float:
    text = str(raw).strip().replace(",", ".")
    parts = text.split(":")
    if len(parts) == 3:
        hours_text, minutes_text, seconds_text = parts
    elif len(parts) == 2:
        hours_text = "0"
        minutes_text, seconds_text = parts
    else:
        raise WorkflowError(f"Invalid caption timestamp: {raw!r}")
    try:
        return (int(hours_text) * 3600.0) + (int(minutes_text) * 60.0) + float(seconds_text)
    except ValueError as exc:
        raise WorkflowError(f"Invalid caption timestamp: {raw!r}") from exc


def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(float(seconds) * 1000.0)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_ass_timestamp(seconds: float) -> str:
    total_cs = max(0, int(round(float(seconds) * 100.0)))
    hours, remainder = divmod(total_cs, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def normalize_caption_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(raw))
    text = text.replace("\ufeff", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(?:SPEAKER_\d+|[A-Z][A-Z0-9 _.-]{1,32}):\s+", "", text)
    return text


def validate_caption_segments(segments: list[dict[str, Any]], *, label: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        try:
            start_seconds = float(segment["start_seconds"])
            end_seconds = float(segment["end_seconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise WorkflowError(f"{label}: segment {index + 1} must include numeric start_seconds and end_seconds.") from exc
        text = normalize_caption_text(str(segment.get("text", "")))
        if not text:
            continue
        if end_seconds <= start_seconds:
            raise WorkflowError(f"{label}: segment {index + 1} end_seconds must be greater than start_seconds.")
        normalized.append(
            {
                "segment_id": str(segment.get("segment_id") or f"caption_{len(normalized) + 1:03d}"),
                "start_seconds": round(start_seconds, 3),
                "end_seconds": round(end_seconds, 3),
                "text": text,
                "emphasis_words": list(segment.get("emphasis_words", []))
                if isinstance(segment.get("emphasis_words", []), list)
                else [],
                "placement_override": str(segment.get("placement_override", "")),
                "timing_adjustment_note": str(segment.get("timing_adjustment_note", "")),
            }
        )
    if not normalized:
        raise WorkflowError(f"{label}: no usable caption segments found.")
    return normalized


def parse_srt_or_vtt_caption_segments(path: Path) -> list[dict[str, Any]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        if not current and line.upper().startswith("WEBVTT"):
            continue
        current.append(line)
    if current:
        blocks.append(current)

    segments: list[dict[str, Any]] = []
    for block in blocks:
        timing_index = next((index for index, line in enumerate(block) if "-->" in line), None)
        if timing_index is None:
            continue
        timing_line = block[timing_index]
        start_raw, end_raw = timing_line.split("-->", 1)
        end_raw = end_raw.strip().split(" ", 1)[0]
        caption_lines = block[timing_index + 1 :]
        text = normalize_caption_text(" ".join(caption_lines))
        if not text:
            continue
        segments.append(
            {
                "segment_id": f"caption_{len(segments) + 1:03d}",
                "start_seconds": parse_caption_timestamp(start_raw),
                "end_seconds": parse_caption_timestamp(end_raw),
                "text": text,
            }
        )
    return validate_caption_segments(segments, label=str(path))


def parse_json_caption_segments(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    if isinstance(payload, list):
        raw_segments = payload
    elif isinstance(payload, dict):
        raw_segments = payload.get("segments") or payload.get("caption_segments") or []
    else:
        raw_segments = []
    if not isinstance(raw_segments, list):
        raise WorkflowError(f"{path}: caption timing JSON must contain a list of segments.")
    return validate_caption_segments(raw_segments, label=str(path))


def parse_caption_timing_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_json_caption_segments(path)
    if suffix in {".srt", ".vtt"}:
        return parse_srt_or_vtt_caption_segments(path)
    raise WorkflowError(f"Unsupported caption timing format for {path}; expected .srt, .vtt, or .json.")


def split_transcript_into_phrases(text: str, *, max_words: int = 8, max_chars: int = 54) -> list[str]:
    normalized = normalize_caption_text(text)
    if not normalized:
        return []
    phrases: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", normalized):
        words = sentence.split()
        current: list[str] = []
        for word in words:
            candidate = current + [word]
            candidate_text = " ".join(candidate)
            if current and (len(candidate) > max_words or len(candidate_text) > max_chars):
                phrases.append(" ".join(current))
                current = [word]
                continue
            current = candidate
        if current:
            phrases.append(" ".join(current))
    return phrases


def distribute_counts(total_items: int, weights: list[float]) -> list[int]:
    if total_items <= 0 or not weights:
        return []
    positive_weights = [max(0.0, float(weight)) for weight in weights]
    total_weight = sum(positive_weights)
    if total_weight <= 0:
        positive_weights = [1.0 for _ in weights]
        total_weight = float(len(weights))
    raw_counts = [(weight / total_weight) * total_items for weight in positive_weights]
    counts = [int(value) for value in raw_counts]
    for index, value in sorted(
        enumerate(raw_counts),
        key=lambda item: item[1] - int(item[1]),
        reverse=True,
    )[: max(0, total_items - sum(counts))]:
        counts[index] += 1
    while sum(counts) > total_items:
        for index in sorted(range(len(counts)), key=lambda item: counts[item], reverse=True):
            if counts[index] > 0:
                counts[index] -= 1
                break
    return counts


def fallback_caption_segments_from_transcript(
    transcript_path: Path,
    proof_manifest: dict[str, Any],
    *,
    proof_duration_seconds: float,
) -> list[dict[str, Any]]:
    phrases = split_transcript_into_phrases(transcript_path.read_text(encoding="utf-8-sig"))
    if not phrases:
        raise WorkflowError(f"{transcript_path}: transcript did not contain usable caption text.")

    beats = proof_manifest.get("beats", [])
    beat_spans: list[tuple[float, float]] = []
    if isinstance(beats, list):
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            try:
                start = float(beat.get("cue_start_seconds", 0.0))
                end = float(beat.get("cue_end_seconds", start))
            except (TypeError, ValueError):
                continue
            if end > start:
                beat_spans.append((start, end))
    if not beat_spans:
        beat_spans = [(0.0, max(0.1, float(proof_duration_seconds)))]

    counts = distribute_counts(len(phrases), [end - start for start, end in beat_spans])
    segments: list[dict[str, Any]] = []
    phrase_index = 0
    for (span_start, span_end), count in zip(beat_spans, counts):
        if count <= 0:
            continue
        span_duration = max(0.1, span_end - span_start)
        slot_duration = span_duration / float(count)
        for local_index in range(count):
            if phrase_index >= len(phrases):
                break
            start = span_start + (slot_duration * local_index)
            end = span_start + (slot_duration * (local_index + 1))
            segments.append(
                {
                    "segment_id": f"caption_{len(segments) + 1:03d}",
                    "start_seconds": round(start, 3),
                    "end_seconds": round(min(end, proof_duration_seconds), 3),
                    "text": phrases[phrase_index],
                }
            )
            phrase_index += 1
    while phrase_index < len(phrases):
        start = (proof_duration_seconds / float(len(phrases))) * phrase_index
        end = (proof_duration_seconds / float(len(phrases))) * (phrase_index + 1)
        segments.append(
            {
                "segment_id": f"caption_{len(segments) + 1:03d}",
                "start_seconds": round(start, 3),
                "end_seconds": round(end, 3),
                "text": phrases[phrase_index],
            }
        )
        phrase_index += 1
    return validate_caption_segments(segments, label=str(transcript_path))


def split_caption_segments_for_style(
    segments: list[dict[str, Any]],
    style: dict[str, Any],
) -> list[dict[str, Any]]:
    refined: list[dict[str, Any]] = []
    max_chars = int(style["max_line_chars"]) * int(style["max_lines"])
    for segment in segments:
        start = float(segment["start_seconds"])
        end = float(segment["end_seconds"])
        duration = max(0.1, end - start)
        phrases = split_transcript_into_phrases(
            str(segment["text"]),
            max_words=7,
            max_chars=max_chars,
        )
        if len(phrases) <= 1:
            refined.append(
                {
                    **segment,
                    "segment_id": f"caption_{len(refined) + 1:03d}",
                    "text": normalize_caption_text(str(segment["text"])),
                    "start_seconds": round(start, 3),
                    "end_seconds": round(end, 3),
                }
            )
            continue
        slot_duration = duration / float(len(phrases))
        for phrase_index, phrase in enumerate(phrases):
            refined.append(
                {
                    **segment,
                    "segment_id": f"caption_{len(refined) + 1:03d}",
                    "start_seconds": round(start + (slot_duration * phrase_index), 3),
                    "end_seconds": round(start + (slot_duration * (phrase_index + 1)), 3),
                    "text": phrase,
                    "timing_adjustment_note": str(segment.get("timing_adjustment_note", ""))
                    or "split from longer timed caption for phrase-level Shorts overlay",
                }
            )
    return validate_caption_segments(refined, label="caption style segmentation")


def wrap_caption_for_ass(text: str, style: dict[str, Any]) -> str:
    lines = wrap_text(text, int(style["max_line_chars"]))
    max_lines = int(style["max_lines"])
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [" ".join(lines[max_lines - 1 :])]
    escaped = []
    for line in lines:
        escaped.append(line.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}"))
    return r"\N".join(escaped)


def write_srt_file(path: Path, segments: list[dict[str, Any]]) -> Path:
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        lines.extend(
            [
                str(index),
                f"{format_srt_timestamp(segment['start_seconds'])} --> {format_srt_timestamp(segment['end_seconds'])}",
                str(segment["text"]),
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path.resolve()


def write_ass_file(path: Path, segments: list[dict[str, Any]], style: dict[str, Any]) -> Path:
    style_name = "DocumentaryLowerThird"
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        (
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
            "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
        ),
        (
            f"Style: {style_name},{style['font_name']},{style['font_size']},{style['font_color']},"
            f"&H000000FF,{style['outline_color']},{style['back_color']},{style['bold']},0,0,0,"
            f"100,100,0,0,{style['border_style']},{style['outline']},{style['shadow']},"
            f"{style['alignment']},{style['margin_l']},{style['margin_r']},{style['margin_v']},1"
        ),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for segment in segments:
        text = wrap_caption_for_ass(str(segment["text"]), style)
        lines.append(
            "Dialogue: 0,"
            f"{format_ass_timestamp(segment['start_seconds'])},"
            f"{format_ass_timestamp(segment['end_seconds'])},"
            f"{style_name},,0,0,0,,{text}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.resolve()


def caption_style_with_placement(caption_style: str, caption_placement: str) -> dict[str, Any]:
    if caption_style not in CAPTION_STYLE_PRESETS:
        raise WorkflowError(f"Unsupported caption style preset: {caption_style!r}")
    if caption_placement not in CAPTION_PLACEMENT_OVERRIDES:
        raise WorkflowError(f"Unsupported caption placement override: {caption_placement!r}")
    style = dict(CAPTION_STYLE_PRESETS[caption_style])
    style.update(CAPTION_PLACEMENT_OVERRIDES[caption_placement])
    if caption_style == DEFAULT_CAPTION_STYLE_PRESET and caption_placement == "lower-left":
        style["max_line_chars"] = 20
    if caption_style == "era_1910s_newspaper_ivory_v1" and caption_placement == "lower-left":
        style["max_line_chars"] = 20
    if caption_style == "early_1980s_broadcast_cg_v1" and caption_placement == "lower-left":
        style["max_line_chars"] = 20
        style["margin_v"] = 340
    if caption_style == "contemporary_aviation_news_v1" and caption_placement == "lower-left":
        style["max_line_chars"] = 22
        style["margin_v"] = 330
    style["placement_override"] = caption_placement
    return style


def ffmpeg_filter_quoted_path(path: Path) -> str:
    escaped = str(path).replace("\\", "\\\\").replace("'", r"\'")
    return f"'{escaped}'"


def assert_short_aspect_ratio(width: int, height: int, *, label: str) -> None:
    if width <= 0 or height <= 0:
        raise WorkflowError(f"{label} has invalid dimensions: {width}x{height}")
    ratio = float(width) / float(height)
    if abs(ratio - SHORT_ASPECT_RATIO) > SHORT_ASPECT_TOLERANCE:
        raise WorkflowError(
            f"{label} must be portrait 9:16 within tolerance; got {width}x{height}."
        )


def image_dimensions(path: Path) -> tuple[int, int]:
    if Image is None:
        raise WorkflowError("Pillow is required to inspect still-image dimensions.")
    with Image.open(path) as image:
        return int(image.width), int(image.height)


def resolve_optional_absolute_path(raw: Any, *, label: str) -> Path | None:
    value = str(raw or "").strip()
    if not value:
        return None
    return resolve_absolute_path(value, label=label)


def extract_info_path(stdout: str, prefix: str) -> Path:
    for line in stdout.splitlines():
        if line.startswith(prefix):
            return Path(line[len(prefix) :].strip()).expanduser().resolve()
    raise WorkflowError(f"Command output did not include {prefix!r}.")


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_disposition(value: Any) -> str:
    return normalize_text(value).replace("-", " ").lower()


def normalize_caption_match_text(value: Any) -> str:
    text = normalize_caption_text(str(value or "")).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def seconds_field(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def find_motif_caption_span(
    caption_segments: list[dict[str, Any]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not caption_segments:
        raise WorkflowError("Cannot resolve motif timing without caption segments.")
    motif_text = (
        normalize_text(payload.get("motif_text"))
        or normalize_text(payload.get("locked_motif_text"))
        or MOTIF_OUTRO_DEFAULT_TEXT
    )
    normalized_motif = normalize_caption_match_text(motif_text)
    matches: list[dict[str, Any]] = []
    if normalized_motif:
        for segment in caption_segments:
            normalized_segment = normalize_caption_match_text(segment.get("text"))
            if normalized_segment and (
                normalized_segment == normalized_motif
                or normalized_motif in normalized_segment
                or normalized_segment in normalized_motif
            ):
                matches.append(segment)
    selected = matches[-1] if matches else caption_segments[-1]
    return {
        "motif_text": motif_text,
        "segment_id": selected.get("segment_id", ""),
        "start_seconds": seconds_field(selected.get("start_seconds")),
        "end_seconds": seconds_field(selected.get("end_seconds")),
        "source": "caption_exact_match" if matches else "last_caption_segment_fallback",
    }


OUTRO_COMPLETION_TOLERANCE_SECONDS = 0.05


def compute_motif_outro_mix_timing(
    *,
    source_duration: float,
    motif_start: float,
    motif_end: float,
    outro_asset_duration: float,
    mix_profile: dict[str, Any],
) -> dict[str, Any]:
    final_hold_min = seconds_field(mix_profile.get("final_frame_hold_seconds_min"), default=0.5)
    final_hold_max = max(
        final_hold_min,
        seconds_field(mix_profile.get("final_frame_hold_seconds_max"), default=0.75),
    )
    base_final_hold_seconds = min(max(0.75, final_hold_min), final_hold_max)
    outro_pre_motif_lead_seconds = seconds_field(
        mix_profile.get("outro_pre_motif_lead_seconds"),
        default=0.25,
    )
    desired_outro_start = max(0.0, motif_start - outro_pre_motif_lead_seconds)
    completion_policy = normalize_text(mix_profile.get("outro_completion_policy")) or "fit_within_final_hold"
    max_extended_final_hold_seconds = max(
        base_final_hold_seconds,
        seconds_field(
            mix_profile.get("max_extended_final_frame_hold_seconds"),
            default=base_final_hold_seconds,
        ),
    )
    required_final_hold_for_outro = max(
        base_final_hold_seconds,
        desired_outro_start + outro_asset_duration - source_duration,
    )

    final_frame_hold_seconds = base_final_hold_seconds
    if completion_policy == "extend_final_to_complete_outro":
        if required_final_hold_for_outro > max_extended_final_hold_seconds + OUTRO_COMPLETION_TOLERANCE_SECONDS:
            raise WorkflowError(
                "Registered music outro cannot complete within the allowed final-frame hold: "
                f"requires {required_final_hold_for_outro:.3f}s, policy max is "
                f"{max_extended_final_hold_seconds:.3f}s."
            )
        final_frame_hold_seconds = required_final_hold_for_outro
        outro_start = desired_outro_start
    elif completion_policy == "fit_within_final_hold":
        final_duration_for_fit = source_duration + final_frame_hold_seconds
        latest_outro_start_for_completion = max(0.0, final_duration_for_fit - outro_asset_duration)
        outro_start = max(desired_outro_start, latest_outro_start_for_completion)
    else:
        raise WorkflowError(f"Unsupported music outro_completion_policy: {completion_policy!r}.")

    final_duration = source_duration + final_frame_hold_seconds
    available_outro_duration = max(0.0, final_duration - outro_start)
    outro_duration_to_use = max(0.001, min(outro_asset_duration, available_outro_duration))
    outro_cutoff_seconds = max(0.0, outro_asset_duration - available_outro_duration)
    outro_completion_read = "pass" if outro_cutoff_seconds <= OUTRO_COMPLETION_TOLERANCE_SECONDS else "tighten"
    if completion_policy == "extend_final_to_complete_outro" and outro_completion_read != "pass":
        raise WorkflowError(
            "Registered music outro still cuts off after applying final-frame hold: "
            f"{outro_cutoff_seconds:.3f}s missing."
        )

    outro_ramp_start_local = max(0.0, motif_end - outro_start)
    outro_ramp_end_local = max(outro_ramp_start_local + 0.001, final_duration - outro_start)
    return {
        "outro_completion_policy": completion_policy,
        "base_final_frame_hold_seconds": base_final_hold_seconds,
        "max_extended_final_frame_hold_seconds": max_extended_final_hold_seconds,
        "required_final_frame_hold_for_outro_seconds": required_final_hold_for_outro,
        "final_frame_hold_seconds": final_frame_hold_seconds,
        "final_duration_seconds": final_duration,
        "outro_pre_motif_lead_seconds": outro_pre_motif_lead_seconds,
        "desired_outro_start_seconds": desired_outro_start,
        "outro_start_seconds": outro_start,
        "outro_duration_used_seconds": outro_duration_to_use,
        "outro_cutoff_seconds": outro_cutoff_seconds,
        "outro_completion_tolerance_seconds": OUTRO_COMPLETION_TOLERANCE_SECONDS,
        "outro_completion_read": outro_completion_read,
        "outro_ramp_start_local_seconds": outro_ramp_start_local,
        "outro_ramp_end_local_seconds": outro_ramp_end_local,
    }


def parse_final_mix_peak_db(stderr: str) -> float:
    match = re.search(r"max_volume:\s*([-+]?\d+(?:\.\d+)?)\s*dB", stderr)
    if not match:
        raise WorkflowError("Could not parse final mix peak dB from ffmpeg volumedetect output.")
    return float(match.group(1))


def effective_audio_job_settings(package_payload: dict[str, Any]) -> dict[str, Any]:
    effective_manifest_text = normalize_text(package_payload.get("effective_manifest_path"))
    if not effective_manifest_text:
        return {}
    effective_path = Path(effective_manifest_text).expanduser()
    if not effective_path.exists() or effective_path.is_dir():
        return {}
    for raw_line in effective_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
        except json.JSONDecodeError:
            return {}
        if not isinstance(job, dict):
            return {}
        voice_settings = job.get("elevenlabs_voice_settings")
        if not isinstance(voice_settings, dict):
            voice_settings = job.get("voice_settings") if isinstance(job.get("voice_settings"), dict) else {}
        speed = job.get("speed")
        if speed is None and isinstance(voice_settings, dict):
            speed = voice_settings.get("speed")
        return {
            "model": normalize_text(job.get("elevenlabs_model_id")),
            "speed": speed,
            "voice_settings": voice_settings if isinstance(voice_settings, dict) else {},
        }
    return {}


def as_sentence(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."


def validate_overlay_strength(value: Any, *, label: str) -> float:
    try:
        strength = float(value)
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{label} must be a number between 0.0 and 1.0.") from exc
    if strength < 0.0 or strength > 1.0:
        raise WorkflowError(f"{label} must be between 0.0 and 1.0, got {strength!r}.")
    return round(strength, 4)


def normalize_overlay_config(raw: Any, *, label: str) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise WorkflowError(f"{label} must be an object when provided.")
    enabled = bool(raw.get("enabled", False))
    preset = normalize_text(raw.get("preset", ""))
    scope = normalize_text(raw.get("scope", "whole_short")) or "whole_short"
    apply_stage = normalize_text(raw.get("apply_stage", "post_picture_master_pre_mux")) or "post_picture_master_pre_mux"
    strength_raw = raw.get("strength", OVERLAY_PRESET_DEFAULT_STRENGTHS.get(preset or "prismatic_glass_v1", 0.22))
    strength = validate_overlay_strength(strength_raw, label=f"{label}.strength")
    if scope not in OVERLAY_SCOPES:
        raise WorkflowError(f"{label}.scope must be one of {sorted(OVERLAY_SCOPES)}, got {scope!r}.")
    if apply_stage not in OVERLAY_APPLY_STAGES:
        raise WorkflowError(
            f"{label}.apply_stage must be one of {sorted(OVERLAY_APPLY_STAGES)}, got {apply_stage!r}."
        )
    if enabled:
        if preset not in OVERLAY_PRESET_DEFAULT_STRENGTHS:
            raise WorkflowError(
                f"{label}.preset must be one of {sorted(OVERLAY_PRESET_DEFAULT_STRENGTHS)}, got {preset!r}."
            )
    elif preset and preset not in OVERLAY_PRESET_DEFAULT_STRENGTHS:
        raise WorkflowError(
            f"{label}.preset must be one of {sorted(OVERLAY_PRESET_DEFAULT_STRENGTHS)}, got {preset!r}."
        )
    return {
        "enabled": enabled,
        "preset": preset,
        "scope": scope,
        "apply_stage": apply_stage,
        "strength": strength,
    }


def build_overlay_config_override(
    *,
    preset: str | None,
    strength: float | None,
    disable: bool,
) -> dict[str, Any] | None:
    if disable:
        return {"enabled": False}
    if preset is None and strength is None:
        return None
    config: dict[str, Any] = {"enabled": True}
    if preset is not None:
        config["preset"] = preset
    if strength is not None:
        config["strength"] = strength
    return config


def merge_overlay_config(
    base: dict[str, Any] | None,
    override: dict[str, Any] | None,
    *,
    label: str,
) -> dict[str, Any] | None:
    if override is None:
        return base if base and base.get("enabled") else None
    if override.get("enabled") is False:
        return None
    merged: dict[str, Any] = {
        "enabled": True,
        "scope": "whole_short",
        "apply_stage": "post_picture_master_pre_mux",
    }
    if base:
        merged.update(base)
    merged.update(override)
    merged["enabled"] = True
    if not normalize_text(merged.get("preset", "")):
        raise WorkflowError(f"{label}: overlay preset must be provided when enabling overlay.")
    if "strength" not in merged or merged["strength"] is None:
        merged["strength"] = OVERLAY_PRESET_DEFAULT_STRENGTHS[str(merged["preset"])]
    normalized = normalize_overlay_config(merged, label=label)
    return normalized if normalized and normalized.get("enabled") else None


def overlay_variant_tag(overlay_config: dict[str, Any], *, explicit_tag: str | None = None) -> str:
    if explicit_tag:
        return normalize_text(explicit_tag).replace(" ", "_")
    preset = str(overlay_config["preset"]).strip()
    strength_percent = int(round(float(overlay_config["strength"]) * 100.0))
    return f"{preset}__s{strength_percent:02d}"


def relative_path_text(path: Path, *, start: Path) -> str:
    return str(path.resolve().relative_to(start.resolve()))


class ShortBuilder:
    def __init__(
        self,
        *,
        repo_root: Path,
        models_root: Path,
        comfy_workflows_dir: Path,
        comfy_output_dir: Path,
        references_root: Path,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.models_root = models_root.resolve()
        self.comfy_workflows_dir = comfy_workflows_dir.resolve()
        self.comfy_output_dir = comfy_output_dir.resolve()
        self.references_root = references_root.resolve()
        self.compiler = WorkflowCompiler(
            repo_root=self.repo_root,
            models_root=self.models_root,
            comfy_workflows_dir=self.comfy_workflows_dir,
            comfy_output_dir=self.comfy_output_dir,
            references_root=self.references_root,
        )
        self.render_script = self.repo_root / "scripts" / "render.sh"
        self.handoff_stage_script = self.repo_root / "scripts" / "handoff-stage.sh"
        self.handoff_i2v_script = self.repo_root / "scripts" / "handoff-i2v.sh"
        self.manifests_root = self.repo_root / "references" / "episodes"
        self.shorts_generated_root = self.compiler.generated_dir / SHORTS_OUTPUT_DIRNAME
        self.paths_env_path = self.repo_root / "config" / "paths.env"
        self.voice_profiles_path = (
            self.repo_root.parent
            / "Audio_CascadeEffects"
            / "references"
            / "voice_profiles"
            / "youtube_shorts_voice_profiles.json"
        )

    def load_short_voice_profiles(self) -> dict[str, dict[str, Any]]:
        if not self.voice_profiles_path.exists():
            raise WorkflowError(f"Shorts voice profile registry is missing: {self.voice_profiles_path}")
        payload = read_json(self.voice_profiles_path)
        profiles = payload.get("profiles", {})
        if not isinstance(profiles, dict) or not profiles:
            raise WorkflowError(f"{self.voice_profiles_path}: expected non-empty profiles object.")
        return {str(profile_id): profile for profile_id, profile in profiles.items() if isinstance(profile, dict)}

    def validate_audio_provenance(
        self,
        path: Path,
        payload: dict[str, Any],
        *,
        require_final_export_eligible: bool,
    ) -> dict[str, Any]:
        package_path = resolve_absolute_path(
            str(payload.get("short_audio_package_path", "")),
            label=f"{path}: short_audio_package_path",
        )
        package_payload = read_json(package_path)
        package_sha = file_sha256(package_path)
        expected_package_sha = normalize_text(payload.get("audio_package_sha256"))
        if not expected_package_sha:
            raise WorkflowError(f"{path}: audio_package_sha256 is required.")
        if package_sha != expected_package_sha:
            raise WorkflowError(f"{path}: audio_package_sha256 mismatch for {package_path}.")

        audio_path = resolve_absolute_path(payload.get("audio_path", ""), label=f"{path}: audio_path")
        packaged_path = resolve_absolute_path(package_payload.get("packaged_path", ""), label=f"{package_path}: packaged_path")
        if audio_path != packaged_path:
            raise WorkflowError(f"{path}: audio_path must match audio_package packaged_path {packaged_path}.")
        packaged_audio_sha = file_sha256(packaged_path)
        expected_packaged_sha = normalize_text(package_payload.get("packaged_sha256"))
        if expected_packaged_sha and packaged_audio_sha != expected_packaged_sha:
            raise WorkflowError(f"{package_path}: packaged_sha256 does not match {packaged_path}.")
        manifest_packaged_sha = normalize_text(payload.get("packaged_audio_sha256"))
        if manifest_packaged_sha and packaged_audio_sha != manifest_packaged_sha:
            raise WorkflowError(f"{path}: packaged_audio_sha256 mismatch for {packaged_path}.")

        package_transcript_path = resolve_absolute_path(
            package_payload.get("transcript_path", ""),
            label=f"{package_path}: transcript_path",
        )
        transcript_sha = file_sha256(package_transcript_path)
        expected_transcript_sha = normalize_text(package_payload.get("transcript_sha256"))
        if expected_transcript_sha and transcript_sha != expected_transcript_sha:
            raise WorkflowError(f"{package_path}: transcript_sha256 does not match {package_transcript_path}.")
        manifest_transcript_sha = normalize_text(payload.get("transcript_sha256"))
        if not manifest_transcript_sha:
            raise WorkflowError(f"{path}: transcript_sha256 is required.")
        if transcript_sha != manifest_transcript_sha:
            raise WorkflowError(f"{path}: transcript_sha256 mismatch for {package_transcript_path}.")

        expected_profile_id = normalize_text(payload.get("expected_voice_profile_id"))
        if not expected_profile_id:
            raise WorkflowError(f"{path}: expected_voice_profile_id is required.")
        profiles = self.load_short_voice_profiles()
        profile = profiles.get(expected_profile_id)
        if profile is None:
            raise WorkflowError(f"{path}: unknown expected_voice_profile_id {expected_profile_id!r}.")
        for field in ("provider", "voice", "model"):
            actual = normalize_text(package_payload.get(field))
            expected = normalize_text(profile.get(field))
            if actual != expected:
                raise WorkflowError(
                    f"{path}: audio package {field} {actual!r} does not match profile "
                    f"{expected_profile_id} {expected!r}."
                )

        disposition = normalize_disposition(payload.get("audio_disposition"))
        if not disposition:
            raise WorkflowError(f"{path}: audio_disposition is required.")
        package_disposition = normalize_disposition(package_payload.get("disposition")) or disposition
        if package_disposition != disposition:
            raise WorkflowError(f"{path}: audio_disposition {disposition!r} does not match package disposition {package_disposition!r}.")
        if require_final_export_eligible:
            if disposition != "keep":
                raise WorkflowError(f"{path}: final export requires keep audio, got {disposition!r}.")
            if not bool(profile.get("final_export_eligible", False)):
                raise WorkflowError(f"{path}: profile {expected_profile_id!r} is not final-export eligible.")
        elif EXPERIMENTS_DIRNAME not in path.parts:
            if disposition != "keep":
                raise WorkflowError(f"{path}: active short manifests require keep audio; move diagnostic/comparison manifests under shorts/experiments.")
            if not bool(profile.get("final_export_eligible", False)):
                raise WorkflowError(f"{path}: active short manifests require a final-export-eligible voice profile.")

        job_settings = effective_audio_job_settings(package_payload)
        expected_speed = profile.get("render_settings", {}).get("speed") if isinstance(profile.get("render_settings"), dict) else None
        actual_speed = job_settings.get("speed")
        if expected_speed is not None and actual_speed is not None and abs(float(actual_speed) - float(expected_speed)) > 0.001:
            raise WorkflowError(f"{path}: recorded audio speed {actual_speed!r} does not match profile speed {expected_speed!r}.")

        return {
            "short_audio_package_path": package_path,
            "expected_voice_profile_id": expected_profile_id,
            "audio_package_sha256": package_sha,
            "packaged_audio_sha256": packaged_audio_sha,
            "audio_disposition": disposition,
            "caption_source_path": package_transcript_path,
            "audio_package_transcript_path": package_transcript_path,
            "transcript_sha256": transcript_sha,
            "provider": normalize_text(package_payload.get("provider")),
            "voice": normalize_text(package_payload.get("voice")),
            "model": normalize_text(package_payload.get("model")),
            "profile_final_export_eligible": bool(profile.get("final_export_eligible", False)),
            "recorded_speed": actual_speed,
            "profile_speed": expected_speed,
        }

    def resolve_stage_spec_path(self, family: str, preset: str, stage: str = "draft_txt2img") -> Path:
        path = self.repo_root / "workflows" / "specs" / family / f"{preset}__{stage}.json"
        if not path.exists():
            raise WorkflowError(f"Stage spec was not found: {path}")
        return path

    def load_stage_spec(self, family: str, preset: str, stage: str = "draft_txt2img") -> dict[str, Any]:
        return read_json(self.resolve_stage_spec_path(family, preset, stage))

    def load_style_profile(self, style_id: str) -> dict[str, Any]:
        path = self.repo_root / "workflows" / "style_profiles" / f"{style_id}.json"
        if not path.exists():
            raise WorkflowError(f"Style profile was not found: {path}")
        return read_json(path)

    def discover_visual_research_dir(self, seed_path: Path) -> Path:
        resolved = seed_path.expanduser().resolve()
        for parent in [resolved.parent, *resolved.parents]:
            candidate = parent / "visual_research"
            if (candidate / "source_inventory.json").exists() and (candidate / "sources.md").exists():
                return candidate
        raise WorkflowError(f"Could not locate visual_research beside {resolved}")

    def load_source_inventory(self, visual_research_dir: Path) -> dict[str, dict[str, Any]]:
        payload = read_json(visual_research_dir / "source_inventory.json")
        items = payload.get("sources")
        if not isinstance(items, list):
            raise WorkflowError(f"{visual_research_dir / 'source_inventory.json'}: expected top-level 'sources' list.")
        inventory: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            source_id = normalize_text(item.get("source_id"))
            if source_id:
                inventory[source_id] = item
        return inventory

    def selection_for_shot(
        self,
        episode_id: str,
        shot_id: str,
        *,
        short_id: str | None = None,
        is_cover: bool = False,
    ) -> list[str]:
        episode_map = MIDJOURNEY_REFERENCE_SELECTIONS.get(episode_id)
        if episode_map is None:
            raise WorkflowError(f"No Midjourney reference selection map is defined for episode {episode_id!r}.")
        cover_selection = list(episode_map["cover"])
        beat_map = dict(episode_map["beats"])
        short_overrides = episode_map.get("short_overrides", {})
        if short_id:
            override_map = short_overrides.get(short_id, {})
            if "cover" in override_map:
                cover_selection = list(override_map["cover"])
            beat_map.update(override_map.get("beats", {}))
        if is_cover:
            return cover_selection
        if shot_id not in beat_map:
            raise WorkflowError(f"No Midjourney reference selection is defined for shot {shot_id!r}.")
        return list(beat_map[shot_id])

    def copy_reference_files(
        self,
        *,
        reference_ids: list[str],
        source_inventory: dict[str, dict[str, Any]],
        destination_dir: Path,
        package_root: Path,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        destination_dir.mkdir(parents=True, exist_ok=True)
        copied_paths: list[str] = []
        provenance: list[dict[str, Any]] = []
        for index, source_id in enumerate(reference_ids, start=1):
            source_entry = source_inventory.get(source_id)
            if source_entry is None:
                raise WorkflowError(f"Missing source inventory entry for {source_id!r}.")
            source_origin = normalize_text(source_entry.get("source_origin"))
            if not source_origin.startswith("web"):
                raise WorkflowError(f"{source_id!r} is not a web-origin research asset: {source_origin!r}")
            raw_asset_path = resolve_absolute_path(source_entry.get("raw_asset_path", ""), label=f"{source_id}.raw_asset_path")
            suffix = raw_asset_path.suffix or ".jpg"
            destination_path = destination_dir / f"{index:02d}__{source_id}{suffix.lower()}"
            shutil.copy2(raw_asset_path, destination_path)
            copied_paths.append(relative_path_text(destination_path, start=package_root))
            provenance.append(
                {
                    "source_id": source_id,
                    "candidate_label": normalize_text(source_entry.get("candidate_label")),
                    "source_url": normalize_text(source_entry.get("source_url")),
                    "source_origin": source_origin,
                    "original_local_path": str(raw_asset_path),
                    "copied_package_path": relative_path_text(destination_path, start=package_root),
                    "notes": normalize_text(source_entry.get("notes")),
                }
            )
        return copied_paths, provenance

    def compose_midjourney_prompt(
        self,
        *,
        spec: dict[str, Any],
        prompt_subject: str,
    ) -> str:
        params = spec.get("params", {})
        prompt_fragments = spec.get("prompt_fragments", {})
        historical_anchor = normalize_text(params.get("historical_anchor")) or normalize_text(prompt_subject)
        anchor_fragment = normalize_text(prompt_fragments.get("anchor_fragment")) or normalize_text(params.get("signal_anchor"))
        palette = normalize_text(params.get("accent_palette"))
        surreal_breach = normalize_text(params.get("surreal_breach"))
        if not surreal_breach:
            support_fragments = prompt_fragments.get("support_fragments")
            if isinstance(support_fragments, list) and support_fragments:
                surreal_breach = normalize_text(support_fragments[0])
        safe_zone_intent = normalize_text(params.get("safe_zone_intent")).lower()
        placement = "off-center"
        if "left third" in safe_zone_intent:
            placement = "left-third"
        elif "right third" in safe_zone_intent:
            placement = "right-third"
        composition = f"{placement} composition, one dominant subject, large empty field, vertical 9:16 frame"
        pieces = [
            as_sentence(historical_anchor),
            as_sentence(anchor_fragment),
            as_sentence(composition),
            as_sentence(f"Palette limited to {palette}" if palette else ""),
            as_sentence(surreal_breach),
            "Stillness, soft diffuse light, quiet suspended atmosphere.",
        ]
        return " ".join(piece for piece in pieces if piece)

    def manual_upload_instructions(self, reference_files: list[str]) -> str:
        ordered_refs = ", ".join(reference_files)
        exclusions = ", ".join(MIDJOURNEY_NEGATIVE_TERMS)
        return (
            "Upload the reference files in the listed order, attach them first in Midjourney, then append the text "
            f"prompt and `{MIDJOURNEY_DEFAULT_SUFFIX}`. Add `--no {exclusions}` after the suffix if the generation "
            "starts drifting into text, poster framing, or spectacle."
        )

    def write_prompt_doc(
        self,
        *,
        prompt_path: Path,
        prompt_text: str,
        parameter_suffix: str,
        reference_files: list[str],
    ) -> None:
        exclusions = ", ".join(MIDJOURNEY_NEGATIVE_TERMS)
        lines = [
            "Midjourney reference upload order:",
            *[f"{index}. {path}" for index, path in enumerate(reference_files, start=1)],
            "",
            "Text prompt:",
            prompt_text,
            "",
            "Parameter suffix:",
            parameter_suffix,
            "",
            "Curated --no terms:",
            exclusions,
            "",
            "How to run:",
            self.manual_upload_instructions(reference_files),
            "",
        ]
        prompt_path.write_text("\n".join(lines), encoding="utf-8")

    def shot_entry_for_export(
        self,
        *,
        package_root: Path,
        shot_id: str,
        prompt_subject: str,
        preset_id: str,
        cue_start_seconds: float | None,
        cue_end_seconds: float | None,
        source_inventory: dict[str, dict[str, Any]],
        reference_ids: list[str],
        is_cover: bool = False,
    ) -> dict[str, Any]:
        family, preset = split_preset_id(preset_id, label=f"{shot_id}.preset_id")
        spec = self.load_stage_spec(family, preset, stage="draft_txt2img")
        prompt_text = self.compose_midjourney_prompt(spec=spec, prompt_subject=prompt_subject)
        shot_dir = package_root / ("cover" if is_cover else f"beats/{shot_id}")
        references_dir = shot_dir / "references"
        reference_files, provenance = self.copy_reference_files(
            reference_ids=reference_ids,
            source_inventory=source_inventory,
            destination_dir=references_dir,
            package_root=package_root,
        )
        references_json_path = shot_dir / "references.json"
        prompt_path = shot_dir / "prompt.txt"
        references_json_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(references_json_path, {"references": provenance})
        self.write_prompt_doc(
            prompt_path=prompt_path,
            prompt_text=prompt_text,
            parameter_suffix=MIDJOURNEY_DEFAULT_SUFFIX,
            reference_files=reference_files,
        )
        return {
            "shot_id": shot_id,
            "preset_id": preset_id,
            "cue_start_seconds": cue_start_seconds,
            "cue_end_seconds": cue_end_seconds,
            "prompt_text": prompt_text,
            "parameter_suffix": MIDJOURNEY_DEFAULT_SUFFIX,
            "negative_terms": list(MIDJOURNEY_NEGATIVE_TERMS),
            "reference_files": reference_files,
            "reference_provenance": provenance,
            "manual_upload_instructions": self.manual_upload_instructions(reference_files),
            "prompt_doc_path": relative_path_text(prompt_path, start=package_root),
            "references_manifest_path": relative_path_text(references_json_path, start=package_root),
        }

    def write_shot_list(
        self,
        *,
        package_root: Path,
        title: str,
        cover_entry: dict[str, Any],
        shot_entries: list[dict[str, Any]],
        source_documents: dict[str, str],
    ) -> Path:
        path = package_root / "shot_list.md"
        lines = [
            f"# {title} Midjourney Package",
            "",
            "## Defaults",
            f"- Parameter suffix: `{MIDJOURNEY_DEFAULT_SUFFIX}`",
            f"- Reference mode: `{MIDJOURNEY_REFERENCE_MODE}`",
            f"- Curated `--no`: `{', '.join(MIDJOURNEY_NEGATIVE_TERMS)}`",
            "",
            "## Source documents",
            f"- Short manifest: `{source_documents['short_manifest_path']}`",
            f"- Style profile: `{source_documents['style_profile_path']}`",
            f"- Source inventory: `{source_documents['source_inventory_path']}`",
            f"- Research notes: `{source_documents['sources_markdown_path']}`",
            "",
            "## Cover",
            f"- Preset: `{cover_entry['preset_id']}`",
            f"- Prompt: {cover_entry['prompt_text']}",
            f"- References: {', '.join(cover_entry['reference_files'])}",
            "",
            "## Shots",
        ]
        for shot in shot_entries:
            lines.extend(
                [
                    f"### {shot['shot_id']}",
                    f"- Preset: `{shot['preset_id']}`",
                    f"- Cue: {shot['cue_start_seconds']:.3f}s -> {shot['cue_end_seconds']:.3f}s",
                    f"- Prompt: {shot['prompt_text']}",
                    f"- References: {', '.join(shot['reference_files'])}",
                    "",
                ]
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def resolve_short_manifest_path(self, short_id: str) -> Path:
        candidates: list[Path] = []
        for path in sorted(self.manifests_root.glob("*/shorts/*.json")):
            try:
                payload = read_json(path)
            except json.JSONDecodeError:
                continue
            if str(payload.get("short_id", "")).strip() == short_id or path.stem == short_id:
                candidates.append(path)
        if not candidates:
            experimental_candidates: list[Path] = []
            for path in sorted(self.manifests_root.glob(f"*/shorts/{EXPERIMENTS_DIRNAME}/*.json")):
                try:
                    payload = read_json(path)
                except json.JSONDecodeError:
                    continue
                if str(payload.get("short_id", "")).strip() == short_id or path.stem == short_id:
                    experimental_candidates.append(path)
            if experimental_candidates:
                joined = ", ".join(str(path) for path in experimental_candidates)
                raise WorkflowError(
                    f"Short manifest {short_id!r} is quarantined under {EXPERIMENTS_DIRNAME}/. "
                    f"Use `bin/ce short build-manifest <absolute_manifest_path>` instead: {joined}"
                )
            raise WorkflowError(f"No short manifest found for {short_id!r}.")
        if len(candidates) != 1:
            joined = ", ".join(str(path) for path in candidates)
            raise WorkflowError(f"Expected exactly one short manifest for {short_id!r}, found: {joined}")
        return candidates[0]

    def resolve_build_manifest_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            raise WorkflowError(f"build-manifest requires an absolute manifest path, got {raw_path!r}.")
        resolved = path.resolve()
        if not resolved.exists():
            raise WorkflowError(f"Short manifest was not found: {resolved}")
        if resolved.suffix != ".json":
            raise WorkflowError(f"Short manifest path must point to a .json file: {resolved}")
        return resolved

    def validate_short_manifest(self, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
        missing = SHORT_MANIFEST_REQUIRED_FIELDS - set(payload)
        if missing:
            raise WorkflowError(f"{path}: missing short-manifest fields: {', '.join(sorted(missing))}")
        if str(payload.get("short_id", "")).strip() != path.stem:
            raise WorkflowError(f"{path}: short_id must match file stem {path.stem!r}.")

        audio_path = resolve_absolute_path(payload["audio_path"], label=f"{path}: audio_path")
        transcript_path = resolve_absolute_path(payload["transcript_path"], label=f"{path}: transcript_path")
        audio_provenance = self.validate_audio_provenance(
            path,
            payload,
            require_final_export_eligible=False,
        )
        try:
            fps = int(payload["fps"])
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{path}: fps must be an integer.") from exc
        if fps <= 0:
            raise WorkflowError(f"{path}: fps must be > 0.")

        packaging_family, packaging_preset = split_preset_id(
            payload["packaging_frame_id"],
            label=f"{path}: packaging_frame_id",
        )
        for stage in REQUIRED_STAGES:
            self.compiler.load_spec(self.compiler.resolve_stage_spec_path(packaging_family, packaging_preset, stage))
        packaging_frame_still_override_path = resolve_optional_absolute_path(
            payload.get("packaging_frame_still_override_path"),
            label=f"{path}: packaging_frame_still_override_path",
        )
        if packaging_frame_still_override_path is not None:
            width, height = image_dimensions(packaging_frame_still_override_path)
            assert_short_aspect_ratio(
                width,
                height,
                label=f"{path}: packaging_frame_still_override_path {packaging_frame_still_override_path}",
            )
        overlay_config = normalize_overlay_config(
            payload.get("overlay_config"),
            label=f"{path}: overlay_config",
        )

        beats = payload.get("beats")
        if not isinstance(beats, list) or not beats:
            raise WorkflowError(f"{path}: beats must be a non-empty list.")

        normalized_beats: list[dict[str, Any]] = []
        previous_cue_start = -1.0
        previous_cue_end = -1.0
        for index, beat in enumerate(beats):
            if not isinstance(beat, dict):
                raise WorkflowError(f"{path}: beats[{index}] must be an object.")
            missing_beat_fields = BEAT_REQUIRED_FIELDS - set(beat)
            if missing_beat_fields:
                raise WorkflowError(
                    f"{path}: beats[{index}] missing fields: {', '.join(sorted(missing_beat_fields))}"
                )
            beat_family, beat_preset = split_preset_id(
                beat["preset_id"],
                label=f"{path}: beats[{index}].preset_id",
            )
            for stage in REQUIRED_STAGES:
                self.compiler.load_spec(self.compiler.resolve_stage_spec_path(beat_family, beat_preset, stage))
            cue_start = float(beat["cue_start_seconds"])
            cue_end = float(beat["cue_end_seconds"])
            target_duration = float(beat["target_duration_seconds"])
            if cue_start < 0.0:
                raise WorkflowError(f"{path}: beats[{index}].cue_start_seconds must be >= 0.")
            if cue_end <= cue_start:
                raise WorkflowError(f"{path}: beats[{index}].cue_end_seconds must be > cue_start_seconds.")
            if target_duration <= 0.0:
                raise WorkflowError(f"{path}: beats[{index}].target_duration_seconds must be > 0.")
            if cue_start < previous_cue_start or cue_end < previous_cue_end:
                raise WorkflowError(f"{path}: beats must be ordered by cue_start_seconds/cue_end_seconds.")
            previous_cue_start = cue_start
            previous_cue_end = cue_end
            motion_prompt = str(beat["motion_prompt"]).strip()
            motion_pipeline = str(beat["motion_pipeline"]).strip()
            if not motion_prompt:
                raise WorkflowError(f"{path}: beats[{index}].motion_prompt must be non-empty.")
            if not motion_pipeline:
                raise WorkflowError(f"{path}: beats[{index}].motion_pipeline must be non-empty.")
            motion_head_trim_seconds = optional_nonnegative_float(
                beat.get("motion_head_trim_seconds"),
                label=f"{path}: beats[{index}].motion_head_trim_seconds",
            )
            motion_handle_seconds = optional_nonnegative_float(
                beat.get("motion_handle_seconds", motion_head_trim_seconds),
                label=f"{path}: beats[{index}].motion_handle_seconds",
            )
            still_override_path = resolve_optional_absolute_path(
                beat.get("still_override_path"),
                label=f"{path}: beats[{index}].still_override_path",
            )
            raw_clip_override_path = resolve_optional_absolute_path(
                beat.get("raw_clip_override_path"),
                label=f"{path}: beats[{index}].raw_clip_override_path",
            )
            if still_override_path is not None:
                width, height = image_dimensions(still_override_path)
                assert_short_aspect_ratio(
                    width,
                    height,
                    label=f"{path}: beats[{index}].still_override_path {still_override_path}",
                )
            if raw_clip_override_path is not None:
                width, height = ffprobe_dimensions(raw_clip_override_path)
                assert_short_aspect_ratio(
                    width,
                    height,
                    label=f"{path}: beats[{index}].raw_clip_override_path {raw_clip_override_path}",
                )
            render_duration = target_duration + motion_handle_seconds
            requested_frames = duration_to_frames(render_duration, fps)
            normalized_beats.append(
                {
                    "id": str(beat["id"]).strip(),
                    "family": beat_family,
                    "preset": beat_preset,
                    "preset_id": f"{beat_family}/{beat_preset}",
                    "cue_start_seconds": cue_start,
                    "cue_end_seconds": cue_end,
                    "target_duration_seconds": target_duration,
                    "motion_prompt": motion_prompt,
                    "motion_pipeline": motion_pipeline,
                    "motion_head_trim_seconds": motion_head_trim_seconds,
                    "motion_handle_seconds": motion_handle_seconds,
                    "requested_frames": requested_frames,
                    "frames": coerce_motion_frames(requested_frames, motion_pipeline),
                    "still_override_path": still_override_path,
                    "raw_clip_override_path": raw_clip_override_path,
                }
            )

        audio_duration = ffprobe_duration(audio_path)
        total_target_duration = sum(float(beat["target_duration_seconds"]) for beat in normalized_beats)
        if abs(total_target_duration - audio_duration) > PROOF_AUDIO_DRIFT_TOLERANCE:
            raise WorkflowError(
                f"{path}: total target duration {total_target_duration:.3f}s does not match audio duration "
                f"{audio_duration:.3f}s within tolerance {PROOF_AUDIO_DRIFT_TOLERANCE:.3f}s."
            )

        return {
            "short_id": str(payload["short_id"]).strip(),
            "episode_id": str(payload.get("episode_id", "")).strip(),
            "title": str(payload["title"]).strip(),
            "audio_path": audio_path,
            "audio_duration_seconds": audio_duration,
            "transcript_path": transcript_path,
            "short_audio_package_path": audio_provenance["short_audio_package_path"],
            "expected_voice_profile_id": audio_provenance["expected_voice_profile_id"],
            "audio_package_sha256": audio_provenance["audio_package_sha256"],
            "packaged_audio_sha256": audio_provenance["packaged_audio_sha256"],
            "audio_disposition": audio_provenance["audio_disposition"],
            "caption_source_path": audio_provenance["caption_source_path"],
            "transcript_sha256": audio_provenance["transcript_sha256"],
            "audio_provenance": {
                "provider": audio_provenance["provider"],
                "voice": audio_provenance["voice"],
                "model": audio_provenance["model"],
                "profile_final_export_eligible": audio_provenance["profile_final_export_eligible"],
                "recorded_speed": audio_provenance["recorded_speed"],
                "profile_speed": audio_provenance["profile_speed"],
            },
            "fps": fps,
            "packaging_frame_id": f"{packaging_family}/{packaging_preset}",
            "packaging_family": packaging_family,
            "packaging_preset": packaging_preset,
            "packaging_frame_still_override_path": packaging_frame_still_override_path,
            "overlay_config": overlay_config,
            "beats": normalized_beats,
        }

    def latest_pipeline_manifest(
        self,
        family: str,
        preset: str,
        *,
        accepted_statuses: set[str] | None = None,
    ) -> Path | None:
        run_dir = self.compiler.generated_dir / "runs" / family / preset
        if not run_dir.exists():
            return None
        statuses = accepted_statuses or {"success"}
        candidates = sorted(
            list(run_dir.glob(f"*{PIPELINE_MANIFEST_SUFFIX}"))
            + list(run_dir.glob(f"*{FINALIZE_STILL_MANIFEST_SUFFIX}"))
        )
        for path in reversed(candidates):
            try:
                payload = read_json(path)
            except json.JSONDecodeError:
                continue
            if str(payload.get("status", "")).strip() not in statuses:
                continue
            outputs = [Path(item).expanduser().resolve() for item in payload.get("final_outputs", [])]
            if not outputs:
                outputs = [Path(item).expanduser().resolve() for item in payload.get("base_final_outputs", [])]
            if outputs and all(candidate.exists() for candidate in outputs):
                return path
        return None

    def run_command(self, command: list[str], *, label: str) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            details = stderr or stdout or f"{label} failed with exit code {completed.returncode}"
            raise WorkflowError(details)
        return completed

    def draw_sheet_text(
        self,
        draw: Any,
        *,
        xy: tuple[int, int],
        text: str,
        font: Any,
        fill: tuple[int, int, int],
        max_chars: int,
        line_height: int,
        max_lines: int,
    ) -> int:
        x, y = xy
        for line in wrap_text(text, max_chars)[:max_lines]:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height
        return y

    def render_beat_sheet(self, proof_manifest_path: Path, *, output_path: Path | None = None) -> Path:
        if Image is None or ImageDraw is None or ImageFont is None or ImageOps is None:
            raise WorkflowError("Pillow is required to render beat sheets.")
        ensure_command("ffmpeg")
        ensure_command("ffprobe")

        proof_manifest_path = self.resolve_existing_proof_manifest(proof_manifest_path)
        payload = read_json(proof_manifest_path)
        beats = payload.get("beats", [])
        if not isinstance(beats, list) or not beats:
            raise WorkflowError(f"{proof_manifest_path}: no beats found for beat sheet rendering.")

        build_dir = proof_manifest_path.parent
        build_stamp = build_dir.name
        output_path = output_path or (build_dir / f"{build_stamp}__beat_sheet.png")
        frame_dir = build_dir / "beat_sheet_frames"
        frame_dir.mkdir(parents=True, exist_ok=True)

        columns = BEAT_SHEET_COLUMNS
        rows = (len(beats) + columns - 1) // columns
        tile_w = BEAT_SHEET_TILE_WIDTH
        tile_h = BEAT_SHEET_TILE_HEIGHT
        label_h = BEAT_SHEET_LABEL_HEIGHT
        margin = BEAT_SHEET_MARGIN
        gutter = BEAT_SHEET_GUTTER
        header_h = BEAT_SHEET_HEADER_HEIGHT
        canvas_w = (margin * 2) + (columns * tile_w) + ((columns - 1) * gutter)
        canvas_h = header_h + (margin * 2) + (rows * (tile_h + label_h)) + ((rows - 1) * gutter)

        sheet = Image.new("RGB", (canvas_w, canvas_h), (16, 16, 16))
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default()
        title = str(payload.get("title") or payload.get("short_id") or proof_manifest_path.stem)
        draw.text((margin, 18), title, font=font, fill=(245, 245, 245))
        draw.text(
            (margin, 42),
            f"{build_stamp} | {payload.get('clip_mode', '')} | {len(beats)} beats",
            font=font,
            fill=(185, 185, 185),
        )
        draw.text((margin, 64), str(payload.get("proof_path", "")), font=font, fill=(135, 135, 135))

        try:
            resampling = Image.Resampling.LANCZOS
        except AttributeError:  # pragma: no cover - older Pillow compatibility
            resampling = Image.LANCZOS

        for index, beat in enumerate(beats):
            beat_id = str(beat.get("id", f"beat_{index + 1:02d}"))
            video_path = resolve_absolute_path(
                str(beat.get("normalized_clip_path", "")),
                label=f"{proof_manifest_path}: beats[{index}].normalized_clip_path",
            )
            duration = ffprobe_duration(video_path)
            frame_path = extract_video_frame(
                video_path,
                frame_dir / f"{index + 1:02d}__{beat_id}.jpg",
                seconds=max(0.0, duration * 0.5),
            )
            col = index % columns
            row = index // columns
            x = margin + (col * (tile_w + gutter))
            y = header_h + margin + (row * (tile_h + label_h + gutter))

            with Image.open(frame_path) as frame:
                thumb = ImageOps.fit(frame.convert("RGB"), (tile_w, tile_h), method=resampling)
            sheet.paste(thumb, (x, y))
            draw.rectangle(
                [x, y + tile_h, x + tile_w, y + tile_h + label_h],
                fill=(28, 28, 28),
            )
            label_y = y + tile_h + 10
            draw.text((x + 10, label_y), beat_id, font=font, fill=(255, 255, 255))
            label_y += 18
            pipeline = str(beat.get("motion_pipeline", ""))
            source_mode = str(beat.get("raw_clip_source_mode", ""))
            frames = beat.get("frames", "")
            requested = beat.get("requested_frames", frames)
            duration_text = f"{float(beat.get('target_duration_seconds', 0.0)):.3f}s"
            label_y = self.draw_sheet_text(
                draw,
                xy=(x + 10, label_y),
                text=f"{pipeline} | {source_mode}",
                font=font,
                fill=(205, 205, 205),
                max_chars=42,
                line_height=16,
                max_lines=2,
            )
            draw.text(
                (x + 10, label_y + 2),
                f"{duration_text} | frames {requested}->{frames}",
                font=font,
                fill=(165, 165, 165),
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output_path)
        return output_path.resolve()

    def resolve_existing_proof_manifest(self, target: Path) -> Path:
        candidate = target.expanduser().resolve()
        if candidate.is_file():
            if candidate.name.endswith("__proof.json"):
                return candidate
            raise WorkflowError(f"Expected a proof manifest path ending with '__proof.json', got {candidate}.")
        if not candidate.is_dir():
            raise WorkflowError(f"Overlay target was not found: {candidate}")
        manifests = sorted(candidate.glob("*__proof.json"))
        if len(manifests) != 1:
            raise WorkflowError(f"Expected exactly one proof manifest in {candidate}, found {len(manifests)}.")
        return manifests[0]

    def overlay_filter_graph(self, overlay_config: dict[str, Any]) -> str:
        preset = str(overlay_config["preset"])
        strength = float(overlay_config["strength"])
        if preset == "prismatic_glass_soft_v1":
            alpha = 0.10 + (strength * 0.18)
            blur = 2.0 + (strength * 10.0)
            saturation = 1.04 + (strength * 0.55)
            brightness = 0.004 + (strength * 0.035)
            rh = max(1, int(round(2 + (strength * 6))))
            bh = -rh
            rv = max(0, int(round(strength * 4)))
            bv = -rv
            return (
                "[0:v]split=2[base][fxsrc];"
                f"[fxsrc]tmix=frames=3:weights='1 2 1',gblur=sigma={blur:.2f},"
                f"rgbashift=rh={rh}:gh=0:bh={bh}:rv={rv}:gv=0:bv={bv},"
                f"eq=saturation={saturation:.3f}:brightness={brightness:.3f}:gamma=1.012,"
                f"colorchannelmixer=aa={alpha:.3f}[glass];"
                "[base][glass]overlay=shortest=1:format=auto,format=yuv420p[outv]"
            )
        if preset == "prismatic_glass_v1":
            alpha = 0.12 + (strength * 0.22)
            blur = 3.5 + (strength * 12.0)
            saturation = 1.10 + (strength * 0.70)
            brightness = 0.008 + (strength * 0.045)
            rh = max(1, int(round(3 + (strength * 8))))
            bh = -rh
            rv = max(1, int(round(1 + (strength * 5))))
            bv = -rv
            return (
                "[0:v]split=2[base][fxsrc];"
                f"[fxsrc]tmix=frames=4:weights='1 2 2 1',gblur=sigma={blur:.2f},"
                f"rgbashift=rh={rh}:gh=0:bh={bh}:rv={rv}:gv=0:bv={bv},"
                f"eq=saturation={saturation:.3f}:brightness={brightness:.3f}:gamma=1.025,"
                f"colorchannelmixer=aa={alpha:.3f}[glass];"
                "[base][glass]overlay=shortest=1:format=auto,format=yuv420p[outv]"
            )
        if preset == "prismatic_glass_glitch_v1":
            alpha = 0.14 + (strength * 0.24)
            jitter_alpha = 0.03 + (strength * 0.08)
            blur = 2.0 + (strength * 8.5)
            saturation = 1.14 + (strength * 0.90)
            brightness = 0.010 + (strength * 0.055)
            rh = max(2, int(round(4 + (strength * 10))))
            bh = -rh
            rv = max(1, int(round(2 + (strength * 5))))
            bv = -rv
            jitter_x = max(1, int(round(2 + (strength * 10))))
            return (
                "[0:v]split=3[base][fxsrc][jittersrc];"
                f"[fxsrc]tmix=frames=3:weights='1 3 1',gblur=sigma={blur:.2f},"
                f"rgbashift=rh={rh}:gh=0:bh={bh}:rv={rv}:gv=0:bv={bv},"
                f"eq=saturation={saturation:.3f}:brightness={brightness:.3f}:gamma=1.035,"
                f"colorchannelmixer=aa={alpha:.3f}[glass];"
                f"[jittersrc]crop=iw-{jitter_x}:ih:{jitter_x}:0,pad=iw:ih:0:0:black,"
                f"rgbashift=rh={max(1, rh // 2)}:gh=0:bh={-max(1, rh // 2)}:rv=0:gv=0:bv=0,"
                f"colorchannelmixer=aa={jitter_alpha:.3f}[jitter];"
                "[base][glass]overlay=shortest=1:format=auto[tmp];"
                "[tmp][jitter]overlay=shortest=1:format=auto,format=yuv420p[outv]"
            )
        raise WorkflowError(f"Unsupported overlay preset: {preset!r}")

    def apply_overlay_to_picture_master(
        self,
        picture_path: Path,
        *,
        overlay_config: dict[str, Any],
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(picture_path),
                "-filter_complex",
                self.overlay_filter_graph(overlay_config),
                "-map",
                "[outv]",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-b:v",
                "6000k",
                "-maxrate",
                "8000k",
                "-bufsize",
                "12000k",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ],
            label=f"apply overlay {overlay_config['preset']}",
        )
        if not output_path.exists():
            raise WorkflowError(f"Overlay picture master was not created: {output_path}")
        width, height = ffprobe_dimensions(output_path)
        assert_short_aspect_ratio(width, height, label=f"Overlay picture master {output_path}")
        return output_path.resolve()

    def overlay_existing_build(
        self,
        target: Path,
        *,
        overlay_config: dict[str, Any],
        output_tag: str | None = None,
    ) -> Path:
        proof_manifest_path = self.resolve_existing_proof_manifest(target)
        payload = read_json(proof_manifest_path)
        build_dir = proof_manifest_path.parent
        source_picture_path = resolve_absolute_path(
            payload.get("clean_picture_master_path") or payload.get("picture_master_path") or "",
            label=f"{proof_manifest_path}: picture_master_path",
        )
        audio_path = resolve_absolute_path(payload.get("audio_path", ""), label=f"{proof_manifest_path}: audio_path")
        try:
            fps = int(payload["fps"])
        except (KeyError, TypeError, ValueError) as exc:
            raise WorkflowError(f"{proof_manifest_path}: fps must be present in the proof manifest.") from exc
        build_stamp = build_dir.name
        tag = overlay_variant_tag(overlay_config, explicit_tag=output_tag)
        variant_dir = build_dir / "overlay_variants" / tag
        variant_dir.mkdir(parents=True, exist_ok=True)
        overlay_picture_path = self.apply_overlay_to_picture_master(
            source_picture_path,
            overlay_config=overlay_config,
            output_path=variant_dir / f"{build_stamp}__{tag}__picture_master.mp4",
        )
        proof_path = self.mux_proof(
            overlay_picture_path,
            audio_path=audio_path,
            fps=fps,
            output_path=variant_dir / f"{build_stamp}__{tag}__proof.mp4",
        )
        manifest_path = variant_dir / f"{build_stamp}__{tag}__overlay.json"
        write_json(
            manifest_path,
            {
                "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "invocation": "short overlay",
                "source_proof_manifest": str(proof_manifest_path),
                "source_picture_master_path": str(source_picture_path),
                "source_audio_path": str(audio_path),
                "clip_mode": str(payload.get("clip_mode", "")),
                "overlay_config": overlay_config,
                "output_tag": tag,
                "overlay_picture_master_path": str(overlay_picture_path),
                "proof_path": str(proof_path),
            },
        )
        print(f"INFO  overlay manifest -> {manifest_path}")
        print(f"INFO  overlay proof -> {proof_path}")
        return manifest_path

    def apply_caption_overlay(
        self,
        proof_path: Path,
        *,
        caption_ass_path: Path,
        output_path: Path,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(proof_path),
                "-vf",
                f"subtitles=filename={ffmpeg_filter_quoted_path(caption_ass_path)}:original_size=1080x1920",
                "-map",
                "0:v:0",
                "-map",
                "0:a?",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-b:v",
                "6000k",
                "-maxrate",
                "8000k",
                "-bufsize",
                "12000k",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            label="apply final captions",
        )
        if not output_path.exists():
            raise WorkflowError(f"Captioned final was not created: {output_path}")
        width, height = ffprobe_dimensions(output_path)
        assert_short_aspect_ratio(width, height, label=f"Captioned final {output_path}")
        return output_path.resolve()

    def load_music_track_context(
        self,
        *,
        music_policy: str,
        music_track_registry: Path,
        music_track_id: str,
        music_waiver_reason: str,
        music_rights_check_status: str,
    ) -> dict[str, Any]:
        policy = normalize_text(music_policy)
        if policy not in MUSIC_POLICIES:
            raise WorkflowError(f"Unsupported music policy: {music_policy!r}.")
        rights_status = normalize_text(music_rights_check_status) or DEFAULT_MUSIC_RIGHTS_CHECK_STATUS
        registry_path = resolve_absolute_path(str(music_track_registry), label="--music-track-registry")
        registry = read_json(registry_path)
        registry_sha256 = file_sha256(registry_path)

        if policy == "waived":
            waiver_reason = normalize_text(music_waiver_reason)
            if not waiver_reason:
                raise WorkflowError("--music-waiver-reason is required when --music-policy waived.")
            return {
                "music_policy": policy,
                "music_track_registry_path": str(registry_path),
                "music_track_registry_sha256": registry_sha256,
                "music_track_id": "",
                "music_track_name": "",
                "music_waiver_reason": waiver_reason,
                "music_rights_check_status": rights_status,
                "motif_outro_mix_used": False,
                "body_loop_path": "",
                "body_loop_sha256": "",
                "outro_path": "",
                "outro_sha256": "",
                "body_loop": {},
                "outro": {},
                "mix_profile": {},
                "rights_and_claims": {},
            }

        default_track_id = normalize_text(registry.get("default_active_shorts_music_track_id")) or DEFAULT_MUSIC_TRACK_ID
        requested_track_id = normalize_text(music_track_id) or default_track_id
        if policy == "canonical_default" and requested_track_id != default_track_id:
            raise WorkflowError(
                f"--music-policy canonical_default requires registry default track {default_track_id!r}; "
                f"got {requested_track_id!r}."
            )
        tracks = registry.get("tracks", {})
        if not isinstance(tracks, dict) or requested_track_id not in tracks:
            raise WorkflowError(f"{registry_path}: music track id {requested_track_id!r} is not registered.")
        track = tracks[requested_track_id]
        if not isinstance(track, dict):
            raise WorkflowError(f"{registry_path}: music track {requested_track_id!r} must be an object.")
        if policy == "alternate_approved" and requested_track_id == default_track_id:
            raise WorkflowError("--music-policy alternate_approved requires a non-default registered music track.")

        body_loop = track.get("body_loop", {}) if isinstance(track.get("body_loop"), dict) else {}
        outro = track.get("outro", {}) if isinstance(track.get("outro"), dict) else {}
        mix_profile = track.get("mix_profile", {}) if isinstance(track.get("mix_profile"), dict) else {}
        body_loop_path = resolve_absolute_path(str(body_loop.get("path", "")), label=f"{registry_path}: body_loop.path")
        outro_path = resolve_absolute_path(str(outro.get("path", "")), label=f"{registry_path}: outro.path")
        body_loop_sha256 = file_sha256(body_loop_path)
        outro_sha256 = file_sha256(outro_path)
        expected_loop_sha = normalize_text(body_loop.get("sha256"))
        expected_outro_sha = normalize_text(outro.get("sha256"))
        if expected_loop_sha and body_loop_sha256 != expected_loop_sha:
            raise WorkflowError(f"{body_loop_path}: sha256 mismatch for registered body loop.")
        if expected_outro_sha and outro_sha256 != expected_outro_sha:
            raise WorkflowError(f"{outro_path}: sha256 mismatch for registered outro.")

        return {
            "music_policy": policy,
            "music_track_registry_path": str(registry_path),
            "music_track_registry_sha256": registry_sha256,
            "music_track_id": requested_track_id,
            "music_track_name": normalize_text(track.get("name")),
            "music_waiver_reason": "",
            "music_rights_check_status": rights_status,
            "motif_outro_mix_used": True,
            "body_loop_path": str(body_loop_path),
            "body_loop_sha256": body_loop_sha256,
            "outro_path": str(outro_path),
            "outro_sha256": outro_sha256,
            "body_loop": body_loop,
            "outro": outro,
            "mix_profile": mix_profile,
            "rights_and_claims": track.get("rights_and_claims", {})
            if isinstance(track.get("rights_and_claims"), dict)
            else {},
        }

    def measure_audio_peak_db(self, media_path: Path) -> float:
        completed = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-i",
                str(media_path),
                "-map",
                "0:a:0",
                "-af",
                "volumedetect",
                "-f",
                "null",
                "-",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise WorkflowError(completed.stderr.strip() or completed.stdout.strip() or f"volumedetect failed for {media_path}")
        return parse_final_mix_peak_db(completed.stderr)

    def source_motion_tail_context(
        self,
        *,
        tail_path: Path | None,
        source_clip_id: str = "",
        source_path: Path | None = None,
        source_span_in: float | None = None,
        source_span_out: float | None = None,
        residual_hold_max_seconds: float = 0.15,
    ) -> dict[str, Any] | None:
        if tail_path is None:
            return None
        resolved_tail_path = resolve_absolute_path(str(tail_path), label="--source-motion-tail-path")
        probe = ffprobe_video_info(resolved_tail_path)
        assert_short_aspect_ratio(
            int(probe["width"]),
            int(probe["height"]),
            label=f"Source motion tail {resolved_tail_path}",
        )
        if int(probe["audio_stream_count"]) != 0:
            raise WorkflowError(f"{resolved_tail_path}: source motion tails must have no audio streams.")

        resolved_source_path = ""
        if source_path is not None and normalize_text(source_path):
            resolved_source_path = str(resolve_absolute_path(str(source_path), label="--source-motion-tail-source-path"))
        return {
            "visual_extension_mode": "source_motion_tail",
            "source_motion_tail_path": str(resolved_tail_path),
            "source_motion_tail_sha256": file_sha256(resolved_tail_path),
            "source_motion_tail_source_clip_id": normalize_text(source_clip_id),
            "source_motion_tail_source_path": resolved_source_path,
            "source_motion_tail_source_span_in": source_span_in,
            "source_motion_tail_source_span_out": source_span_out,
            "source_motion_tail_duration_seconds": round(float(probe["duration_seconds"]), 6),
            "source_motion_tail_width": int(probe["width"]),
            "source_motion_tail_height": int(probe["height"]),
            "source_motion_tail_fps": float(probe["fps"]),
            "source_motion_tail_audio_stream_count": int(probe["audio_stream_count"]),
            "source_motion_tail_residual_hold_max_seconds": max(0.0, float(residual_hold_max_seconds)),
        }

    def apply_music_mix(
        self,
        captioned_voice_only_path: Path,
        *,
        output_path: Path,
        caption_segments: list[dict[str, Any]],
        source_payload: dict[str, Any],
        music_context: dict[str, Any],
        source_motion_tail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        body_loop_path = Path(str(music_context["body_loop_path"])).expanduser().resolve()
        outro_path = Path(str(music_context["outro_path"])).expanduser().resolve()
        source_duration = ffprobe_duration(captioned_voice_only_path)
        source_video_info = ffprobe_video_info(captioned_voice_only_path)
        source_width = int(source_video_info["width"])
        source_height = int(source_video_info["height"])
        source_fps = float(source_video_info["fps"])
        outro_asset_duration = ffprobe_duration(outro_path)
        motif_span = find_motif_caption_span(caption_segments, source_payload)
        motif_start = min(max(0.0, float(motif_span["start_seconds"])), source_duration)
        motif_end = min(max(motif_start, float(motif_span["end_seconds"])), source_duration)

        body_loop = music_context.get("body_loop", {})
        outro = music_context.get("outro", {})
        mix_profile = music_context.get("mix_profile", {})
        body_volume = seconds_field(
            mix_profile.get("body_loop_volume_linear"),
            default=seconds_field(body_loop.get("default_volume_linear"), default=0.2),
        )
        outro_initial_volume = seconds_field(
            mix_profile.get("outro_initial_volume_linear"),
            default=seconds_field(outro.get("default_initial_volume_linear"), default=0.1),
        )
        outro_ramp_end_volume = seconds_field(
            mix_profile.get("outro_ramp_end_volume_linear"),
            default=seconds_field(outro.get("default_ramp_end_volume_linear"), default=0.82),
        )
        body_loop_end = max(0.001, min(motif_start, source_duration))
        body_fade_duration = min(
            seconds_field(body_loop.get("default_fade_out_duration_seconds"), default=0.5),
            body_loop_end,
        )
        body_fade_start = max(0.0, body_loop_end - body_fade_duration)
        mix_timing = compute_motif_outro_mix_timing(
            source_duration=source_duration,
            motif_start=motif_start,
            motif_end=motif_end,
            outro_asset_duration=outro_asset_duration,
            mix_profile=mix_profile,
        )
        final_frame_hold_seconds = float(mix_timing["final_frame_hold_seconds"])
        final_duration = float(mix_timing["final_duration_seconds"])
        outro_start = float(mix_timing["outro_start_seconds"])
        outro_duration_to_use = float(mix_timing["outro_duration_used_seconds"])
        outro_delay_ms = int(round(outro_start * 1000.0))
        outro_ramp_start_local = float(mix_timing["outro_ramp_start_local_seconds"])
        outro_ramp_end_local = float(mix_timing["outro_ramp_end_local_seconds"])
        outro_ramp_duration = max(0.001, outro_ramp_end_local - outro_ramp_start_local)
        outro_fade_in_duration = min(
            seconds_field(outro.get("default_fade_in_duration_seconds"), default=0.2),
            outro_duration_to_use,
        )
        visual_extension_mode = "cloned_final_frame"
        source_motion_tail_used_seconds = None
        source_motion_tail_residual_hold_seconds = None
        tail_video_input: Path | None = None
        video_filter: str
        if source_motion_tail is not None:
            visual_extension_mode = "source_motion_tail"
            tail_video_input = Path(str(source_motion_tail["source_motion_tail_path"])).expanduser().resolve()
            tail_duration = float(source_motion_tail["source_motion_tail_duration_seconds"])
            residual_hold_max = float(source_motion_tail["source_motion_tail_residual_hold_max_seconds"])
            source_motion_tail_used_seconds = min(final_frame_hold_seconds, tail_duration)
            source_motion_tail_residual_hold_seconds = max(0.0, final_frame_hold_seconds - tail_duration)
            if source_motion_tail_residual_hold_seconds > residual_hold_max + 1e-6:
                raise WorkflowError(
                    "Source motion tail is too short for the required visual extension: "
                    f"needs {final_frame_hold_seconds:.3f}s, tail has {tail_duration:.3f}s, "
                    f"residual hold {source_motion_tail_residual_hold_seconds:.3f}s exceeds "
                    f"{residual_hold_max:.3f}s."
                )
            tail_filter = (
                f"[3:v]trim=0:{source_motion_tail_used_seconds:.3f},"
                f"setpts=PTS-STARTPTS,fps={source_fps:.6f},scale={source_width}:{source_height}:flags=lanczos,setsar=1,format=yuv420p"
            )
            if source_motion_tail_residual_hold_seconds > 0:
                tail_filter += f",tpad=stop_mode=clone:stop_duration={source_motion_tail_residual_hold_seconds:.3f}"
            video_filter = (
                f"[0:v]trim=0:{source_duration:.3f},setpts=PTS-STARTPTS,"
                f"fps={source_fps:.6f},scale={source_width}:{source_height}:flags=lanczos,"
                "setsar=1,format=yuv420p[mainv];"
                f"{tail_filter}[tailv];"
                "[mainv][tailv]concat=n=2:v=1:a=0,setpts=PTS-STARTPTS[v]"
            )
        else:
            video_filter = f"[0:v]tpad=stop_mode=clone:stop_duration={final_frame_hold_seconds:.3f},setpts=PTS-STARTPTS[v]"
        limiter = normalize_text(mix_profile.get("limiter")) or "alimiter=limit=0.89:level=false"
        limiter = limiter.replace("alimiter ", "alimiter=").replace(" ", ":")
        volume_expr = (
            f"if(lt(t,{outro_ramp_start_local:.3f}),{outro_initial_volume:.6f},"
            f"if(lt(t,{outro_ramp_end_local:.3f}),"
            f"{outro_initial_volume:.6f}+(t-{outro_ramp_start_local:.3f})*"
            f"({outro_ramp_end_volume - outro_initial_volume:.6f}/{outro_ramp_duration:.3f}),"
            f"{outro_ramp_end_volume:.6f}))"
        )
        filter_complex = ";".join(
            [
                video_filter,
                f"[0:a]apad=pad_dur={final_frame_hold_seconds:.3f},atrim=0:{final_duration:.3f},asetpts=PTS-STARTPTS[voice]",
                (
                    f"[1:a]atrim=0:{body_loop_end:.3f},asetpts=PTS-STARTPTS,volume={body_volume:.6f},"
                    f"afade=t=out:st={body_fade_start:.3f}:d={body_fade_duration:.3f}[body]"
                ),
                (
                    f"[2:a]atrim=0:{outro_duration_to_use:.3f},asetpts=PTS-STARTPTS,"
                    f"volume='{volume_expr}':eval=frame,"
                    f"afade=t=in:st=0:d={outro_fade_in_duration:.3f},"
                    f"adelay={outro_delay_ms}:all=1[outro]"
                ),
                (
                    f"[voice][body][outro]amix=inputs=3:duration=longest:normalize=0,"
                    f"atrim=0:{final_duration:.3f},{limiter},asetpts=PTS-STARTPTS[a]"
                ),
            ]
        )
        command = [
                "ffmpeg",
                "-y",
                "-i",
                str(captioned_voice_only_path),
                "-stream_loop",
                "-1",
                "-i",
                str(body_loop_path),
                "-i",
                str(outro_path),
        ]
        if tail_video_input is not None:
            command.extend(["-i", str(tail_video_input)])
        command.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-b:v",
                "6000k",
                "-maxrate",
                "8000k",
                "-bufsize",
                "12000k",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
        )
        self.run_command(
            command,
            label="apply final music mix",
        )
        if not output_path.exists():
            raise WorkflowError(f"Music final was not created: {output_path}")
        width, height = ffprobe_dimensions(output_path)
        assert_short_aspect_ratio(width, height, label=f"Music final {output_path}")
        output_duration = ffprobe_duration(output_path)
        peak_db = self.measure_audio_peak_db(output_path)
        return {
            "captioned_voice_only_path": str(captioned_voice_only_path),
            "source_duration_seconds": round(source_duration, 6),
            "final_duration_seconds": round(output_duration, 6),
            "target_final_duration_seconds": round(final_duration, 6),
            "visual_extension_mode": visual_extension_mode,
            "final_frame_hold_seconds": round(final_frame_hold_seconds, 3),
            "base_final_frame_hold_seconds": round(float(mix_timing["base_final_frame_hold_seconds"]), 3),
            "max_extended_final_frame_hold_seconds": round(
                float(mix_timing["max_extended_final_frame_hold_seconds"]),
                3,
            ),
            "required_final_frame_hold_for_outro_seconds": round(
                float(mix_timing["required_final_frame_hold_for_outro_seconds"]),
                3,
            ),
            "motif_span": motif_span,
            "body_loop_start_seconds": 0.0,
            "body_loop_end_seconds": round(body_loop_end, 3),
            "body_loop_volume_linear": body_volume,
            "body_loop_fade_out_start_seconds": round(body_fade_start, 3),
            "body_loop_fade_out_duration_seconds": round(body_fade_duration, 3),
            "outro_completion_policy": mix_timing["outro_completion_policy"],
            "outro_pre_motif_lead_seconds": round(float(mix_timing["outro_pre_motif_lead_seconds"]), 3),
            "desired_outro_start_seconds": round(float(mix_timing["desired_outro_start_seconds"]), 3),
            "outro_start_seconds": round(outro_start, 3),
            "outro_asset_duration_seconds": round(outro_asset_duration, 6),
            "outro_duration_used_seconds": round(outro_duration_to_use, 3),
            "outro_cutoff_seconds": round(float(mix_timing["outro_cutoff_seconds"]), 3),
            "outro_completion_tolerance_seconds": round(
                float(mix_timing["outro_completion_tolerance_seconds"]),
                3,
            ),
            "outro_initial_volume_linear": outro_initial_volume,
            "outro_ramp_start_seconds": round(motif_end, 3),
            "outro_ramp_end_seconds": round(final_duration, 3),
            "outro_ramp_end_volume_linear": outro_ramp_end_volume,
            "outro_fade_in_duration_seconds": round(outro_fade_in_duration, 3),
            "limiter": limiter,
            "motif_music_bed_read": "pass",
            "outro_completion_read": mix_timing["outro_completion_read"],
            "final_mix_peak_db": peak_db,
            "final_mix_no_clipping": peak_db <= -0.1,
            "source_motion_tail_path": source_motion_tail["source_motion_tail_path"] if source_motion_tail else "",
            "source_motion_tail_sha256": source_motion_tail["source_motion_tail_sha256"] if source_motion_tail else "",
            "source_motion_tail_source_clip_id": source_motion_tail["source_motion_tail_source_clip_id"]
            if source_motion_tail
            else "",
            "source_motion_tail_source_path": source_motion_tail["source_motion_tail_source_path"]
            if source_motion_tail
            else "",
            "source_motion_tail_source_span_in": source_motion_tail["source_motion_tail_source_span_in"]
            if source_motion_tail
            else None,
            "source_motion_tail_source_span_out": source_motion_tail["source_motion_tail_source_span_out"]
            if source_motion_tail
            else None,
            "source_motion_tail_duration_seconds": source_motion_tail["source_motion_tail_duration_seconds"]
            if source_motion_tail
            else None,
            "source_motion_tail_used_seconds": round(source_motion_tail_used_seconds, 3)
            if source_motion_tail_used_seconds is not None
            else None,
            "source_motion_tail_residual_hold_seconds": round(source_motion_tail_residual_hold_seconds, 3)
            if source_motion_tail_residual_hold_seconds is not None
            else None,
            "source_motion_tail_residual_hold_max_seconds": source_motion_tail[
                "source_motion_tail_residual_hold_max_seconds"
            ]
            if source_motion_tail
            else None,
            "source_motion_tail_audio_stream_count": source_motion_tail["source_motion_tail_audio_stream_count"]
            if source_motion_tail
            else None,
        }

    def final_export_historical_signal_context(
        self,
        proof_manifest_path: Path,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        profile_id = normalize_text(payload.get("historical_signal_profile_id"))
        texture_used = bool(payload.get("historical_signal_texture_used")) or bool(profile_id)
        if not texture_used:
            return {}
        required_reads = (
            "texture_visibility_read",
            "house_crt_texture_read",
            "historical_signal_texture_read",
            "youtube_survival_read",
            "compression_artifact_read",
            "detail_survival_read",
        )
        accepted_reads: dict[str, str] = {}
        for key in required_reads:
            value = normalize_text(payload.get(key))
            if key == "house_crt_texture_read" and not value:
                value = normalize_text(payload.get("era_match_read"))
            if not value:
                raise WorkflowError(f"{proof_manifest_path}: {key} is required when historical signal texture is used.")
            accepted = value == "pass" or value.startswith("pass ") or value.startswith("accepted")
            if not accepted:
                raise WorkflowError(
                    f"{proof_manifest_path}: {key} must be pass or explicitly accepted, got {payload.get(key)!r}."
                )
            accepted_reads[key] = value
        return {
            "historical_signal_texture_used": True,
            "historical_context_year_or_range": normalize_text(payload.get("historical_context_year_or_range")),
            "source_media_era": normalize_text(payload.get("source_media_era")),
            "historical_signal_profile_id": profile_id,
            "historical_signal_texture_registry_path": normalize_text(
                payload.get("historical_signal_texture_registry_path")
            ),
            "historical_signal_texture_registry_sha256": normalize_text(
                payload.get("historical_signal_texture_registry_sha256")
            ),
            "signal_texture_strength": normalize_text(payload.get("signal_texture_strength")),
            "texture_source_lane": normalize_text(payload.get("texture_source_lane")),
            "texture_application_scope": normalize_text(payload.get("texture_application_scope")),
            "texture_applied_path": normalize_text(payload.get("texture_applied_path")),
            "texture_applied_sha256": normalize_text(payload.get("texture_applied_sha256")),
            "youtube_survival_proxy_path": normalize_text(payload.get("youtube_survival_proxy_path")),
            "youtube_survival_proxy_sha256": normalize_text(payload.get("youtube_survival_proxy_sha256")),
            "randomized_static_transition_read": normalize_text(
                payload.get("randomized_static_transition_read")
            )
            or "not_applicable",
            **accepted_reads,
        }

    def final_export_house_crt_static_context(
        self,
        proof_manifest_path: Path,
        house_crt_static_manifest: Path | None,
        waiver_reason: str = "",
    ) -> dict[str, Any]:
        waiver_reason = normalize_text(waiver_reason)
        if house_crt_static_manifest is None:
            if not waiver_reason:
                raise WorkflowError(
                    "Final export requires --house-crt-static-manifest or an explicit "
                    "--house-crt-static-waiver-reason."
                )
            return {
                "required": True,
                "status": "waived",
                "waiver_reason": waiver_reason,
                "house_crt_contract_id": HOUSE_CRT_FINAL_CONTRACT_ID,
                "house_crt_texture_read": "waived",
                "signal_interruption_read": "waived",
                "randomized_static_transition_read": "waived",
            }

        manifest_path = resolve_absolute_path(
            str(house_crt_static_manifest),
            label="--house-crt-static-manifest",
        )
        payload = read_json(manifest_path)
        pass_id = normalize_text(payload.get("pass_id"))
        if bool(payload.get("calibration_only")) or pass_id in HOUSE_CRT_FINAL_CALIBRATION_ONLY_PASS_IDS:
            raise WorkflowError(
                f"{manifest_path}: calibration-only house CRT manifests cannot be used as final-gate inputs."
            )
        source_proof = normalize_text(payload.get("source_proof_manifest_path"))
        if source_proof and Path(source_proof).expanduser().resolve() != proof_manifest_path.resolve():
            raise WorkflowError(
                f"{manifest_path}: source_proof_manifest_path does not match final-export target {proof_manifest_path}."
            )

        house_read = payload.get("house_crt_texture_read")
        if not isinstance(house_read, dict):
            raise WorkflowError(f"{manifest_path}: house_crt_texture_read object is required.")
        contract_read = payload.get("house_crt_contract_read")
        contract_id = normalize_text(
            house_read.get("house_crt_contract_id")
            or payload.get("house_crt_contract_id")
            or (contract_read.get("house_crt_contract_id") if isinstance(contract_read, dict) else "")
        )
        if contract_id != HOUSE_CRT_FINAL_CONTRACT_ID:
            raise WorkflowError(
                f"{manifest_path}: house_crt_contract_id must be "
                f"{HOUSE_CRT_FINAL_CONTRACT_ID}, got {contract_id!r}."
            )
        profile_id = normalize_text(house_read.get("profile_id"))
        intensity = normalize_text(house_read.get("intensity"))
        if profile_id != HOUSE_CRT_FINAL_PROFILE_ID:
            raise WorkflowError(
                f"{manifest_path}: house CRT profile must be {HOUSE_CRT_FINAL_PROFILE_ID}, got {profile_id!r}."
            )
        if intensity != HOUSE_CRT_FINAL_INTENSITY:
            raise WorkflowError(
                f"{manifest_path}: house CRT intensity must be {HOUSE_CRT_FINAL_INTENSITY}, got {intensity!r}."
            )
        tone_policy = normalize_text(
            house_read.get("texture_tone_policy") or payload.get("texture_tone_policy")
        )
        if tone_policy != HOUSE_CRT_FINAL_TONE_POLICY:
            raise WorkflowError(
                f"{manifest_path}: house CRT texture_tone_policy must be "
                f"{HOUSE_CRT_FINAL_TONE_POLICY}, got {tone_policy!r}."
            )
        calibration_recipe_id = normalize_text(
            house_read.get("calibration_recipe_id") or payload.get("calibration_recipe_id")
        )
        if calibration_recipe_id != HOUSE_CRT_FINAL_CALIBRATION_RECIPE_ID:
            raise WorkflowError(
                f"{manifest_path}: house CRT calibration_recipe_id must be "
                f"{HOUSE_CRT_FINAL_CALIBRATION_RECIPE_ID}, got {calibration_recipe_id!r}."
            )
        legacy_recipe_id = normalize_text(
            house_read.get("legacy_calibration_recipe_id") or payload.get("legacy_calibration_recipe_id")
        )
        if legacy_recipe_id != HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID:
            raise WorkflowError(
                f"{manifest_path}: house CRT legacy_calibration_recipe_id must be "
                f"{HOUSE_CRT_FINAL_LEGACY_CALIBRATION_RECIPE_ID}, got {legacy_recipe_id!r}."
            )
        texture_renderer_source = normalize_text(
            house_read.get("texture_renderer_source") or payload.get("texture_renderer_source")
        )
        if texture_renderer_source != HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE:
            raise WorkflowError(
                f"{manifest_path}: house CRT texture_renderer_source must be "
                f"{HOUSE_CRT_FINAL_TEXTURE_RENDERER_SOURCE}, got {texture_renderer_source!r}."
            )
        scanline_policy_id = normalize_text(
            house_read.get("scanline_policy_id") or payload.get("scanline_policy_id")
        )
        if scanline_policy_id != HOUSE_CRT_FINAL_SCANLINE_POLICY_ID:
            raise WorkflowError(
                f"{manifest_path}: house CRT scanline_policy_id must be "
                f"{HOUSE_CRT_FINAL_SCANLINE_POLICY_ID}, got {scanline_policy_id!r}."
            )
        scanline_variant_id = normalize_text(
            house_read.get("scanline_strength_variant_id") or payload.get("scanline_strength_variant_id")
        )
        if scanline_variant_id != HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID:
            raise WorkflowError(
                f"{manifest_path}: house CRT scanline_strength_variant_id must be "
                f"{HOUSE_CRT_FINAL_SCANLINE_STRENGTH_VARIANT_ID}, got {scanline_variant_id!r}."
            )
        try:
            scanline_delta_y = float(house_read.get("scanline_delta_y") or payload.get("scanline_delta_y"))
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{manifest_path}: house CRT scanline_delta_y is invalid.") from exc
        if abs(scanline_delta_y - HOUSE_CRT_FINAL_SCANLINE_DELTA_Y) > 0.001:
            raise WorkflowError(
                f"{manifest_path}: house CRT scanline_delta_y must be "
                f"{HOUSE_CRT_FINAL_SCANLINE_DELTA_Y}, got {scanline_delta_y!r}."
            )
        try:
            scanline_period_pixels = int(
                house_read.get("scanline_period_pixels") or payload.get("scanline_period_pixels")
            )
            scanline_band_pixels = int(house_read.get("scanline_band_pixels") or payload.get("scanline_band_pixels"))
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{manifest_path}: house CRT scanline period/band fields are invalid.") from exc
        if scanline_period_pixels != HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS:
            raise WorkflowError(
                f"{manifest_path}: house CRT scanline_period_pixels must be "
                f"{HOUSE_CRT_FINAL_SCANLINE_PERIOD_PIXELS}, got {scanline_period_pixels!r}."
            )
        if scanline_band_pixels != HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS:
            raise WorkflowError(
                f"{manifest_path}: house CRT scanline_band_pixels must be "
                f"{HOUSE_CRT_FINAL_SCANLINE_BAND_PIXELS}, got {scanline_band_pixels!r}."
            )
        luma_chroma_read = payload.get("luma_chroma_metrics_read")
        if not isinstance(luma_chroma_read, dict) or normalize_text(luma_chroma_read.get("overall_read")) != "pass":
            raise WorkflowError(f"{manifest_path}: luma_chroma_metrics_read.overall_read must be pass.")
        source_lineage_read = payload.get("source_lineage_read") or house_read.get("source_lineage_read")
        if not isinstance(source_lineage_read, dict):
            raise WorkflowError(f"{manifest_path}: source_lineage_read object is required.")
        if source_lineage_read.get("clean_source_confirmed") is not True:
            raise WorkflowError(f"{manifest_path}: source_lineage_read.clean_source_confirmed must be true.")
        if source_lineage_read.get("selected_source_rejections"):
            raise WorkflowError(f"{manifest_path}: selected source lineage still contains pre-textured source paths.")
        if source_lineage_read.get("selected_paths_under_historical_signal_texture"):
            raise WorkflowError(f"{manifest_path}: selected source paths must not be under historical_signal_texture.")

        visual_layer_read = payload.get("visual_layer_order_read")
        if not isinstance(visual_layer_read, dict):
            raise WorkflowError(f"{manifest_path}: visual_layer_order_read object is required.")
        if visual_layer_read.get("caption_burn_is_last_visual_operation") is not True:
            raise WorkflowError(f"{manifest_path}: captions must be the last visual operation.")
        if visual_layer_read.get("post_caption_visual_effects_applied") is not False:
            raise WorkflowError(f"{manifest_path}: post-caption visual effects are not allowed.")
        if visual_layer_read.get("motion_source_contains_captions") is not False:
            raise WorkflowError(f"{manifest_path}: house CRT motion source must be no-caption picture.")
        if visual_layer_read.get("texture_applied_before_captions") is not True:
            raise WorkflowError(f"{manifest_path}: house CRT texture must be applied before captions.")
        if visual_layer_read.get("signal_interruption_applied_before_captions") is not True:
            raise WorkflowError(f"{manifest_path}: signal interruption must be applied before captions.")
        layer_sequence = visual_layer_read.get("visual_layer_sequence")
        if not isinstance(layer_sequence, list) or "caption_burn_last_visual_layer" not in layer_sequence:
            raise WorkflowError(f"{manifest_path}: visual_layer_sequence must record caption_burn_last_visual_layer.")

        signal_read = payload.get("signal_interruption_read")
        if not isinstance(signal_read, dict):
            raise WorkflowError(
                f"{manifest_path}: Challenger-style signal_interruption_read object is required; "
                "generic randomized_static_transition_read manifests are not valid for this gate."
            )
        signal_profile_id = normalize_text(signal_read.get("profile_id"))
        if signal_profile_id != HOUSE_CRT_STATIC_PROFILE_ID:
            raise WorkflowError(
                f"{manifest_path}: Challenger-style signal interruption profile must be "
                f"{HOUSE_CRT_STATIC_PROFILE_ID}, got {signal_profile_id!r}."
            )
        try:
            signal_duration = float(signal_read.get("duration_seconds"))
        except (TypeError, ValueError) as exc:
            raise WorkflowError(f"{manifest_path}: signal interruption duration_seconds is invalid.") from exc
        if abs(signal_duration - HOUSE_CRT_STATIC_DURATION_SECONDS) > 0.001:
            raise WorkflowError(
                f"{manifest_path}: signal interruption duration must be {HOUSE_CRT_STATIC_DURATION_SECONDS}, "
                f"got {signal_duration!r}."
            )
        timing_policy = normalize_text(signal_read.get("timing_policy"))
        if timing_policy and timing_policy != "replace_outgoing_segment_tail_preserve_total_duration":
            raise WorkflowError(f"{manifest_path}: unsupported signal interruption timing_policy {timing_policy!r}.")
        if bool(signal_read.get("full_frame_static_replacement_used")):
            raise WorkflowError(
                f"{manifest_path}: full_frame_static_replacement_used must be false for Challenger-style "
                "signal interruption."
            )
        eligible_cut_count = int(signal_read.get("eligible_cut_count") or 0)
        applied_cut_count = int(signal_read.get("applied_cut_count") or 0)
        if eligible_cut_count > 0 and applied_cut_count != eligible_cut_count:
            raise WorkflowError(
                f"{manifest_path}: signal interruption applied_cut_count {applied_cut_count} "
                f"does not match eligible_cut_count {eligible_cut_count}."
            )

        outputs = payload.get("outputs", {})
        if not isinstance(outputs, dict):
            outputs = {}
        motion_path_text = (
            outputs.get("motion_full_duration_no_audio_path")
            or outputs.get("motion_core_no_audio_path")
            or payload.get("motion_full_duration_no_audio_path")
            or payload.get("motion_core_no_audio_path")
        )
        if not motion_path_text:
            raise WorkflowError(f"{manifest_path}: motion no-audio output path is required.")
        motion_path = resolve_absolute_path(str(motion_path_text), label=f"{manifest_path}: motion no-audio output")
        motion_probe = ffprobe_video_info(motion_path)
        assert_short_aspect_ratio(
            int(motion_probe["width"]),
            int(motion_probe["height"]),
            label=f"House CRT/static motion bed {motion_path}",
        )
        if int(motion_probe["audio_stream_count"]) != 0:
            raise WorkflowError(f"{motion_path}: house CRT final-gate motion bed must have no audio streams.")

        return {
            "required": True,
            "status": "applied",
            "manifest_path": str(manifest_path),
            "house_crt_contract_id": contract_id,
            "house_crt_contract_read": contract_read if isinstance(contract_read, dict) else {},
            "motion_full_duration_no_audio_path": str(motion_path),
            "house_crt_texture_read": house_read,
            "scanline_policy_id": scanline_policy_id,
            "scanline_strength_variant_id": scanline_variant_id,
            "scanline_delta_y": scanline_delta_y,
            "scanline_period_pixels": scanline_period_pixels,
            "scanline_band_pixels": scanline_band_pixels,
            "source_lineage_read": source_lineage_read,
            "luma_chroma_metrics_read": luma_chroma_read,
            "visual_layer_order_read": visual_layer_read,
            "signal_interruption_read": signal_read,
            "randomized_static_transition_read": payload.get("randomized_static_transition_read", "superseded"),
            "eligible_cut_count": eligible_cut_count,
            "applied_cut_count": applied_cut_count,
            "caption_layer_order_read": "captions_applied_after_house_crt_signal_interruption_motion_rebuild",
            "audio_layer_order_read": "audio_muxed_after_captioned_motion_rebuild",
        }

    def final_export_existing_build(
        self,
        target: Path,
        *,
        proof_review_note: Path,
        proof_disposition: str,
        reel_class: str,
        all_motion_clips_keep: bool,
        no_diagnostic_placeholders: bool,
        caption_style: str = DEFAULT_CAPTION_STYLE_PRESET,
        caption_placement: str = "lower-center",
        caption_source: Path | None = None,
        caption_timing: Path | None = None,
        manual_timing_adjustments: Path | None = None,
        output_tag: str | None = None,
        music_policy: str = "canonical_default",
        music_track_registry: Path = DEFAULT_MUSIC_TRACK_REGISTRY_PATH,
        music_track_id: str = DEFAULT_MUSIC_TRACK_ID,
        music_waiver_reason: str = "",
        music_rights_check_status: str = DEFAULT_MUSIC_RIGHTS_CHECK_STATUS,
        source_motion_tail_path: Path | None = None,
        source_motion_tail_source_clip_id: str = "",
        source_motion_tail_source_path: Path | None = None,
        source_motion_tail_span_in: float | None = None,
        source_motion_tail_span_out: float | None = None,
        source_motion_tail_residual_hold_max: float = 0.15,
        house_crt_static_manifest: Path | None = None,
        house_crt_static_waiver_reason: str = "",
    ) -> Path:
        ensure_command("ffmpeg")
        ensure_command("ffprobe")
        resolved_caption_style = caption_style_with_placement(caption_style, caption_placement)
        if proof_disposition != "keep":
            raise WorkflowError("Final export requires --proof-disposition keep.")
        if reel_class != "keeper-short":
            raise WorkflowError("Final export requires --reel-class keeper-short.")
        if not all_motion_clips_keep:
            raise WorkflowError("Final export requires --all-motion-clips-keep.")
        if not no_diagnostic_placeholders:
            raise WorkflowError("Final export requires --no-diagnostic-placeholders.")

        proof_manifest_path = self.resolve_existing_proof_manifest(target)
        payload = read_json(proof_manifest_path)
        historical_signal_context = self.final_export_historical_signal_context(proof_manifest_path, payload)
        house_crt_static_context = self.final_export_house_crt_static_context(
            proof_manifest_path,
            house_crt_static_manifest,
            house_crt_static_waiver_reason,
        )
        audio_provenance = self.validate_audio_provenance(
            proof_manifest_path,
            payload,
            require_final_export_eligible=True,
        )
        manifest_disposition = normalize_text(payload.get("disposition", "")).replace("-", " ")
        if manifest_disposition and manifest_disposition != "keep":
            raise WorkflowError(f"{proof_manifest_path}: proof manifest disposition is not keep: {manifest_disposition!r}.")
        manifest_reel_class = normalize_text(payload.get("reel_class", "")).replace("-", " ")
        if manifest_reel_class and manifest_reel_class != "keeper short":
            raise WorkflowError(f"{proof_manifest_path}: proof manifest reel_class is not keeper short: {manifest_reel_class!r}.")
        for index, beat in enumerate(payload.get("beats", [])):
            if not isinstance(beat, dict):
                continue
            for field in ("motion_disposition", "clip_disposition", "disposition"):
                value = normalize_text(beat.get(field, "")).replace("-", " ")
                if value and value != "keep":
                    raise WorkflowError(
                        f"{proof_manifest_path}: beats[{index}].{field} is not keep: {value!r}."
                    )

        review_note_path = resolve_absolute_path(str(proof_review_note), label="--proof-review-note")
        proof_path = resolve_absolute_path(payload.get("proof_path", ""), label=f"{proof_manifest_path}: proof_path")
        final_picture_source_path = (
            Path(str(house_crt_static_context["motion_full_duration_no_audio_path"]))
            if house_crt_static_context.get("status") == "applied"
            else proof_path
        )
        audio_path = resolve_absolute_path(payload.get("audio_path", ""), label=f"{proof_manifest_path}: audio_path")
        source_path = caption_source
        if source_path is None:
            source_path = Path(
                str(
                    payload.get("caption_text_source_path")
                    or payload.get("caption_source_path")
                    or payload.get("transcript_path", "")
                )
            ).expanduser()
        caption_source_path = resolve_absolute_path(str(source_path), label="caption source")
        if caption_word_source_looks_blocked(caption_source_path):
            raise WorkflowError(
                f"{caption_source_path}: caption source is raw ASR/WhisperX/diarized transcript text. "
                "Use a locked script or script-locked caption output for caption words; ASR may be timing only."
            )
        caption_timing_path = (
            resolve_absolute_path(str(caption_timing), label="--caption-timing")
            if caption_timing is not None
            else None
        )
        manual_timing_adjustments_path = (
            resolve_absolute_path(str(manual_timing_adjustments), label="--manual-timing-adjustments")
            if manual_timing_adjustments is not None
            else None
        )
        if manual_timing_adjustments_path is not None and manual_timing_adjustments_path.suffix.lower() != ".json":
            raise WorkflowError("--manual-timing-adjustments must point to a JSON file.")
        music_context = self.load_music_track_context(
            music_policy=music_policy,
            music_track_registry=music_track_registry,
            music_track_id=music_track_id,
            music_waiver_reason=music_waiver_reason,
            music_rights_check_status=music_rights_check_status,
        )
        source_motion_tail = self.source_motion_tail_context(
            tail_path=source_motion_tail_path,
            source_clip_id=source_motion_tail_source_clip_id,
            source_path=source_motion_tail_source_path,
            source_span_in=source_motion_tail_span_in,
            source_span_out=source_motion_tail_span_out,
            residual_hold_max_seconds=source_motion_tail_residual_hold_max,
        )
        if source_motion_tail is not None and not music_context["motif_outro_mix_used"]:
            raise WorkflowError("--source-motion-tail-path requires an active motif/outro music mix.")

        width, height = ffprobe_dimensions(final_picture_source_path)
        assert_short_aspect_ratio(width, height, label=f"Final picture source {final_picture_source_path}")
        proof_duration_seconds = ffprobe_duration(final_picture_source_path)

        caption_source_mode = "qa_transcript_fallback"
        if caption_timing_path is not None:
            caption_segments = parse_caption_timing_file(caption_timing_path)
            caption_source_mode = "supplied_caption_timing"
        elif caption_source_path.suffix.lower() in {".srt", ".vtt"}:
            caption_segments = parse_caption_timing_file(caption_source_path)
            caption_source_mode = "timed_caption_source"
        elif caption_source_path.suffix.lower() == ".json":
            try:
                caption_segments = parse_caption_timing_file(caption_source_path)
                caption_source_mode = "timed_caption_source"
            except WorkflowError:
                caption_segments = fallback_caption_segments_from_transcript(
                    caption_source_path,
                    payload,
                    proof_duration_seconds=proof_duration_seconds,
                )
        else:
            caption_segments = fallback_caption_segments_from_transcript(
                caption_source_path,
                payload,
                proof_duration_seconds=proof_duration_seconds,
            )
        caption_segments = split_caption_segments_for_style(caption_segments, resolved_caption_style)
        raw_timing_source = payload.get("caption_timing_source_path") or (
            str(caption_timing_path) if caption_timing_path is not None else str(caption_source_path)
        )
        caption_timing_source_path = resolve_absolute_path(
            str(raw_timing_source),
            label=f"{proof_manifest_path}: caption_timing_source_path",
        )
        caption_policy_context = {
            "caption_model": SCRIPT_LOCKED_CAPTION_MODEL,
            "caption_text_source_policy": SCRIPT_LOCKED_TEXT_POLICY,
            "caption_timing_source_policy": normalize_text(payload.get("caption_timing_source_policy"))
            or ASR_TIMING_POLICY,
            "caption_text_source_path": str(caption_source_path),
            "caption_text_source_sha256": file_sha256(caption_source_path),
            "caption_timing_source_path": str(caption_timing_source_path),
            "caption_timing_source_sha256": file_sha256(caption_timing_source_path),
            "caption_text_matches_script_read": payload.get("caption_text_matches_script_read", "pass_review_required"),
            "caption_asr_text_not_used_read": payload.get("caption_asr_text_not_used_read", "pass"),
            "caption_alignment_coverage_read": payload.get("caption_alignment_coverage_read", "pass_review_required"),
            "publish_ready_blocked_if_caption_text_not_script_locked": True,
        }
        for read_key in (
            "caption_text_matches_script_read",
            "caption_asr_text_not_used_read",
            "caption_alignment_coverage_read",
        ):
            if not pass_read(caption_policy_context[read_key]):
                raise WorkflowError(
                    f"{proof_manifest_path}: {read_key} must be pass before final export; "
                    f"got {caption_policy_context[read_key]!r}."
                )

        export_stamp = utc_stamp()
        tag = slugify_tag(output_tag or caption_style)
        export_dir = proof_manifest_path.parent / "final_exports" / tag
        export_dir.mkdir(parents=True, exist_ok=True)
        caption_timing_output_path = export_dir / f"{export_stamp}__caption_timing.json"
        caption_srt_path = export_dir / f"{export_stamp}__captions.srt"
        caption_ass_path = export_dir / f"{export_stamp}__captions.ass"
        caption_overlay_manifest_path = export_dir / f"{export_stamp}__caption_overlay_manifest.json"
        captioned_final_path = export_dir / f"{export_stamp}__captioned_final.mp4"
        captioned_voice_only_path = (
            export_dir / f"{export_stamp}__captioned_voice_only.mp4"
            if music_context["motif_outro_mix_used"]
            else captioned_final_path
        )
        final_export_manifest_path = export_dir / f"{export_stamp}__final_export.json"

        timing_payload = {
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "caption_source_path": str(caption_source_path),
            "caption_source_mode": caption_source_mode,
            **caption_policy_context,
            "caption_style_preset": caption_style,
            "segments": caption_segments,
        }
        write_json(caption_timing_output_path, timing_payload)
        write_srt_file(caption_srt_path, caption_segments)
        write_ass_file(caption_ass_path, caption_segments, resolved_caption_style)
        captioned_voice_only_path = self.apply_caption_overlay(
            final_picture_source_path,
            caption_ass_path=caption_ass_path,
            output_path=captioned_voice_only_path,
        )
        if music_context["motif_outro_mix_used"]:
            music_mix = self.apply_music_mix(
                captioned_voice_only_path,
                output_path=captioned_final_path,
                caption_segments=caption_segments,
                source_payload=payload,
                music_context=music_context,
                source_motion_tail=source_motion_tail,
            )
        else:
            captioned_final_path = captioned_voice_only_path
            music_mix = {
                "captioned_voice_only_path": str(captioned_voice_only_path),
                "source_duration_seconds": round(ffprobe_duration(captioned_final_path), 6),
                "final_duration_seconds": round(ffprobe_duration(captioned_final_path), 6),
                "target_final_duration_seconds": round(ffprobe_duration(captioned_final_path), 6),
                "visual_extension_mode": "none",
                "final_frame_hold_seconds": 0.0,
                "base_final_frame_hold_seconds": 0.0,
                "max_extended_final_frame_hold_seconds": 0.0,
                "required_final_frame_hold_for_outro_seconds": 0.0,
                "motif_span": {},
                "body_loop_start_seconds": None,
                "body_loop_end_seconds": None,
                "body_loop_volume_linear": None,
                "body_loop_fade_out_start_seconds": None,
                "body_loop_fade_out_duration_seconds": None,
                "outro_completion_policy": "waived",
                "outro_pre_motif_lead_seconds": None,
                "desired_outro_start_seconds": None,
                "outro_start_seconds": None,
                "outro_asset_duration_seconds": None,
                "outro_duration_used_seconds": None,
                "outro_cutoff_seconds": None,
                "outro_completion_tolerance_seconds": OUTRO_COMPLETION_TOLERANCE_SECONDS,
                "outro_initial_volume_linear": None,
                "outro_ramp_start_seconds": None,
                "outro_ramp_end_seconds": None,
                "outro_ramp_end_volume_linear": None,
                "outro_fade_in_duration_seconds": None,
                "limiter": "",
                "motif_music_bed_read": "waived",
                "outro_completion_read": "waived",
                "final_mix_peak_db": None,
                "final_mix_no_clipping": None,
                "source_motion_tail_path": "",
                "source_motion_tail_sha256": "",
                "source_motion_tail_source_clip_id": "",
                "source_motion_tail_source_path": "",
                "source_motion_tail_source_span_in": None,
                "source_motion_tail_source_span_out": None,
                "source_motion_tail_duration_seconds": None,
                "source_motion_tail_used_seconds": None,
                "source_motion_tail_residual_hold_seconds": None,
                "source_motion_tail_residual_hold_max_seconds": None,
                "source_motion_tail_audio_stream_count": None,
            }
        final_music_context = {
            "music_track_registry_path": music_context["music_track_registry_path"],
            "music_track_registry_sha256": music_context["music_track_registry_sha256"],
            "music_track_id": music_context["music_track_id"],
            "music_track_name": music_context["music_track_name"],
            "music_policy": music_context["music_policy"],
            "music_waiver_reason": music_context["music_waiver_reason"],
            "music_rights_check_status": music_context["music_rights_check_status"],
            "motif_outro_mix_used": music_context["motif_outro_mix_used"],
            "body_loop_path": music_context["body_loop_path"],
            "body_loop_sha256": music_context["body_loop_sha256"],
            "outro_path": music_context["outro_path"],
            "outro_sha256": music_context["outro_sha256"],
            **music_mix,
        }

        overlay_manifest = {
            "episode_id": payload.get("episode_id", ""),
            "short_id": payload.get("short_id", ""),
            "stage": "video final",
            "short_audio_package_path": str(audio_provenance["short_audio_package_path"]),
            "expected_voice_profile_id": audio_provenance["expected_voice_profile_id"],
            "audio_disposition": audio_provenance["audio_disposition"],
            "caption_source_path": str(caption_source_path),
            **caption_policy_context,
            "transcript_sha256": audio_provenance["transcript_sha256"],
            "caption_style_preset": caption_style,
            "caption_timing_path": str(caption_timing_output_path),
            "caption_srt_path": str(caption_srt_path),
            "caption_ass_path": str(caption_ass_path),
            "captioned_final_path": str(captioned_final_path),
            "captioned_voice_only_path": str(captioned_voice_only_path),
            "manual_timing_adjustments_path": str(manual_timing_adjustments_path or ""),
            "historical_signal_context": historical_signal_context,
            "house_crt_static_context": house_crt_static_context,
            "final_music_context": final_music_context,
            "style_defaults": resolved_caption_style,
            "caption_segments": caption_segments,
            "qa": {
                "caption_legibility_checked": False,
                "caption_safe_zone_checked": False,
                "mechanism_not_occluded": False,
                "generated_visual_text_leakage_reviewed_separately": False,
            },
        }
        write_json(caption_overlay_manifest_path, overlay_manifest)

        final_manifest = {
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "invocation": "short final-export",
            "stage": "video final",
            "episode_id": payload.get("episode_id", ""),
            "short_id": payload.get("short_id", ""),
            "source_proof_manifest_path": str(proof_manifest_path),
            "proof_video_path": str(proof_path),
            "final_picture_source_path": str(final_picture_source_path),
            "house_crt_static_context": house_crt_static_context,
            "house_crt_static_manifest_path": house_crt_static_context.get("manifest_path", ""),
            "house_crt_static_status": house_crt_static_context.get("status", ""),
            "house_crt_static_waiver_reason": house_crt_static_context.get("waiver_reason", ""),
            "proof_review_note_path": str(review_note_path),
            "approved_short_audio_wav_path": str(audio_path),
            "short_audio_package_path": str(audio_provenance["short_audio_package_path"]),
            "expected_voice_profile_id": audio_provenance["expected_voice_profile_id"],
            "audio_package_sha256": audio_provenance["audio_package_sha256"],
            "packaged_audio_sha256": audio_provenance["packaged_audio_sha256"],
            "audio_disposition": audio_provenance["audio_disposition"],
            "caption_source_path": str(caption_source_path),
            **caption_policy_context,
            "transcript_sha256": audio_provenance["transcript_sha256"],
            "audio_provenance": {
                "provider": audio_provenance["provider"],
                "voice": audio_provenance["voice"],
                "model": audio_provenance["model"],
                "profile_final_export_eligible": audio_provenance["profile_final_export_eligible"],
                "recorded_speed": audio_provenance["recorded_speed"],
                "profile_speed": audio_provenance["profile_speed"],
            },
            "caption_source_mode": caption_source_mode,
            "caption_policy_context": caption_policy_context,
            "caption_style_preset": caption_style,
            "caption_placement": caption_placement,
            "caption_timing_path": str(caption_timing_output_path),
            "caption_srt_path": str(caption_srt_path),
            "caption_ass_path": str(caption_ass_path),
            "caption_overlay_manifest_path": str(caption_overlay_manifest_path),
            "captioned_final_path": str(captioned_final_path),
            "captioned_voice_only_path": str(captioned_voice_only_path),
            "captioned_final_sha256": file_sha256(captioned_final_path),
            "captioned_voice_only_sha256": file_sha256(captioned_voice_only_path),
            "final_video_sha256": file_sha256(captioned_final_path),
            "caption_srt_sha256": file_sha256(caption_srt_path),
            "manual_timing_adjustments_path": str(manual_timing_adjustments_path or ""),
            "manual_timing_adjustments_recorded": manual_timing_adjustments_path is not None,
            "historical_signal_context": historical_signal_context,
            "historical_signal_texture_used": bool(historical_signal_context),
            "historical_context_year_or_range": historical_signal_context.get("historical_context_year_or_range", ""),
            "source_media_era": historical_signal_context.get("source_media_era", ""),
            "historical_signal_profile_id": historical_signal_context.get("historical_signal_profile_id", ""),
            "historical_signal_texture_registry_path": historical_signal_context.get(
                "historical_signal_texture_registry_path", ""
            ),
            "historical_signal_texture_registry_sha256": historical_signal_context.get(
                "historical_signal_texture_registry_sha256", ""
            ),
            "signal_texture_strength": historical_signal_context.get("signal_texture_strength", ""),
            "texture_source_lane": historical_signal_context.get("texture_source_lane", ""),
            "texture_application_scope": historical_signal_context.get("texture_application_scope", ""),
            "texture_applied_path": historical_signal_context.get("texture_applied_path", ""),
            "texture_applied_sha256": historical_signal_context.get("texture_applied_sha256", ""),
            "youtube_survival_proxy_path": historical_signal_context.get("youtube_survival_proxy_path", ""),
            "youtube_survival_proxy_sha256": historical_signal_context.get("youtube_survival_proxy_sha256", ""),
            "texture_visibility_read": historical_signal_context.get("texture_visibility_read", ""),
            "house_crt_texture_read": historical_signal_context.get("house_crt_texture_read", ""),
            "randomized_static_transition_read": historical_signal_context.get(
                "randomized_static_transition_read", ""
            ),
            "historical_signal_texture_read": historical_signal_context.get("historical_signal_texture_read", ""),
            "youtube_survival_read": historical_signal_context.get("youtube_survival_read", ""),
            "compression_artifact_read": historical_signal_context.get("compression_artifact_read", ""),
            "detail_survival_read": historical_signal_context.get("detail_survival_read", ""),
            "final_music_context": final_music_context,
            "music_track_registry_path": final_music_context["music_track_registry_path"],
            "music_track_registry_sha256": final_music_context["music_track_registry_sha256"],
            "music_track_id": final_music_context["music_track_id"],
            "music_track_name": final_music_context["music_track_name"],
            "music_policy": final_music_context["music_policy"],
            "music_waiver_reason": final_music_context["music_waiver_reason"],
            "music_rights_check_status": final_music_context["music_rights_check_status"],
            "motif_outro_mix_used": final_music_context["motif_outro_mix_used"],
            "body_loop_path": final_music_context["body_loop_path"],
            "body_loop_sha256": final_music_context["body_loop_sha256"],
            "outro_path": final_music_context["outro_path"],
            "outro_sha256": final_music_context["outro_sha256"],
            "visual_extension_mode": final_music_context["visual_extension_mode"],
            "final_frame_hold_seconds": final_music_context["final_frame_hold_seconds"],
            "outro_completion_policy": final_music_context["outro_completion_policy"],
            "outro_start_seconds": final_music_context["outro_start_seconds"],
            "outro_asset_duration_seconds": final_music_context["outro_asset_duration_seconds"],
            "outro_duration_used_seconds": final_music_context["outro_duration_used_seconds"],
            "outro_cutoff_seconds": final_music_context["outro_cutoff_seconds"],
            "source_motion_tail_path": final_music_context["source_motion_tail_path"],
            "source_motion_tail_sha256": final_music_context["source_motion_tail_sha256"],
            "source_motion_tail_source_clip_id": final_music_context["source_motion_tail_source_clip_id"],
            "source_motion_tail_source_path": final_music_context["source_motion_tail_source_path"],
            "source_motion_tail_source_span_in": final_music_context["source_motion_tail_source_span_in"],
            "source_motion_tail_source_span_out": final_music_context["source_motion_tail_source_span_out"],
            "source_motion_tail_used_seconds": final_music_context["source_motion_tail_used_seconds"],
            "source_motion_tail_residual_hold_seconds": final_music_context[
                "source_motion_tail_residual_hold_seconds"
            ],
            "motif_music_bed_read": final_music_context["motif_music_bed_read"],
            "outro_completion_read": final_music_context["outro_completion_read"],
            "final_mix_peak_db": final_music_context["final_mix_peak_db"],
            "final_mix_no_clipping": final_music_context["final_mix_no_clipping"],
            "gate_assertions": {
                "proof_disposition": "keep",
                "reel_class": "keeper short",
                "all_motion_clips_are_keep": all_motion_clips_keep,
                "no_diagnostic_placeholders": no_diagnostic_placeholders,
                "proof_review_exists": True,
                "audio_exists": True,
                "transcript_exists": True,
                "audio_package_exists": True,
                "audio_package_provenance_checked": True,
                "audio_disposition": "keep",
                "voice_profile_final_export_eligible": True,
                "caption_preset_selected": True,
                "caption_text_source_script_locked": not caption_word_source_looks_blocked(caption_source_path),
                "caption_text_matches_script": pass_read(caption_policy_context["caption_text_matches_script_read"]),
                "caption_asr_text_not_used": pass_read(caption_policy_context["caption_asr_text_not_used_read"]),
                "historical_signal_texture_provenance_checked": not historical_signal_context
                or all(
                    bool(historical_signal_context.get(key))
                    for key in (
                        "historical_signal_profile_id",
                        "signal_texture_strength",
                        "texture_applied_path",
                        "youtube_survival_proxy_path",
                    )
                ),
                "house_crt_static_final_gate_checked": house_crt_static_context.get("status") == "applied",
                "house_crt_static_final_gate_waived": house_crt_static_context.get("status") == "waived",
                "music_policy_resolved": True,
                "music_waiver_reason_recorded": music_context["music_policy"] != "waived"
                or bool(music_context["music_waiver_reason"]),
                "music_track_hashes_verified": not music_context["motif_outro_mix_used"]
                or (
                    bool(music_context["body_loop_sha256"])
                    and bool(music_context["outro_sha256"])
                ),
                "unresolved_mixed_review_blockers": False,
            },
            "outputs": {
                "caption_timing_path": str(caption_timing_output_path),
                "caption_srt_path": str(caption_srt_path),
                "caption_overlay_manifest_path": str(caption_overlay_manifest_path),
                "captioned_final_path": str(captioned_final_path),
                "captioned_voice_only_path": str(captioned_voice_only_path),
            },
        }
        write_json(final_export_manifest_path, final_manifest)
        print(f"INFO  caption timing -> {caption_timing_output_path}")
        print(f"INFO  caption overlay manifest -> {caption_overlay_manifest_path}")
        print(f"INFO  captioned final -> {captioned_final_path}")
        print(f"INFO  final export manifest -> {final_export_manifest_path}")
        return final_export_manifest_path.resolve()

    def load_paths_config(self) -> dict[str, str]:
        if not self.paths_env_path.exists():
            raise WorkflowError(f"Missing paths config: {self.paths_env_path}")
        values: dict[str, str] = {}
        for raw_line in self.paths_env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, raw_value = line.split("=", 1)
            value = raw_value.strip()
            if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
                value = value[1:-1]
            values[key.strip()] = value
        return values

    def load_headless_config(self) -> dict[str, str]:
        values = self.load_paths_config()
        missing = [field for field in HEADLESS_PATHS_ENV_FIELDS if not str(values.get(field, "")).strip()]
        if missing:
            raise WorkflowError(
                f"{self.paths_env_path}: missing required headless fields: {', '.join(sorted(missing))}"
            )
        return values

    def resolve_mlx_generated_shorts_root(self) -> Path:
        values = self.load_paths_config()
        missing = [field for field in MLX_VIDEO_PATHS_ENV_FIELDS if not str(values.get(field, "")).strip()]
        if missing:
            raise WorkflowError(
                f"{self.paths_env_path}: missing required MLX video fields: {', '.join(sorted(missing))}"
            )
        mlx_video_dir = Path(str(values["CE_MLX_VIDEO_DIR"])).expanduser().resolve()
        return mlx_video_dir / "workflows" / "generated" / SHORTS_OUTPUT_DIRNAME

    def fetch_headless_system_stats(self, server_url: str) -> dict[str, Any]:
        request = urllib.request.Request(f"{server_url}/system_stats", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.URLError as exc:
            raise WorkflowError(f"Headless Comfy server not reachable at {server_url}/system_stats: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"Headless Comfy server returned invalid JSON from {server_url}/system_stats.") from exc

    def preflight_headless_runtime(self) -> dict[str, str]:
        config = self.load_headless_config()
        comfy_main_py = resolve_absolute_path(
            config["CE_COMFY_MAIN_PY"],
            label=f"{self.paths_env_path}: CE_COMFY_MAIN_PY",
        )
        comfy_python = resolve_absolute_path(
            config["CE_COMFY_PYTHON"],
            label=f"{self.paths_env_path}: CE_COMFY_PYTHON",
        )
        clip_vision_model = str(config["CE_COMFY_CLIP_VISION_MODEL"]).strip()
        clip_vision_model_path = self.models_root / "clip_vision" / clip_vision_model
        if not clip_vision_model_path.exists():
            raise WorkflowError(
                f"{self.paths_env_path}: CE_COMFY_CLIP_VISION_MODEL was not found: {clip_vision_model_path}"
            )
        host = str(config["CE_COMFY_HEADLESS_HOST"]).strip()
        port = str(config["CE_COMFY_HEADLESS_PORT"]).strip()
        if not host:
            raise WorkflowError(f"{self.paths_env_path}: CE_COMFY_HEADLESS_HOST must be non-empty.")
        try:
            port_value = int(port)
        except ValueError as exc:
            raise WorkflowError(f"{self.paths_env_path}: CE_COMFY_HEADLESS_PORT must be an integer.") from exc
        if port_value <= 0:
            raise WorkflowError(f"{self.paths_env_path}: CE_COMFY_HEADLESS_PORT must be > 0.")
        server_url = f"http://{host}:{port_value}"
        self.run_command(
            [str(self.render_script), "server", "start"],
            label="start headless Comfy server",
        )
        self.fetch_headless_system_stats(server_url)
        return {
            "server_url": server_url,
            "comfy_main_py": str(comfy_main_py),
            "comfy_python": str(comfy_python),
            "clip_vision_model": clip_vision_model,
            "clip_vision_model_path": str(clip_vision_model_path.resolve()),
        }

    def ensure_pipeline_output(
        self,
        family: str,
        preset: str,
        *,
        quality_profile: str = DEFAULT_RENDER_QUALITY,
        delivery_mode: str = "strict",
    ) -> tuple[Path, dict[str, Any], Path]:
        accepted_statuses = {"success", "advisory_success"} if delivery_mode == "advisory" else {"success"}
        existing = self.latest_pipeline_manifest(
            family,
            preset,
            accepted_statuses=accepted_statuses,
        )
        if existing is None:
            completed = self.run_command(
                [
                    str(self.render_script),
                    "pipeline",
                    family,
                    preset,
                    "--typography",
                    "off",
                    "--source-text-repair",
                    "off",
                    "--quality-profile",
                    quality_profile,
                    "--delivery-mode",
                    delivery_mode,
                ],
                label=f"render pipeline {family}/{preset}",
            )
            try:
                existing = extract_info_path(completed.stdout, "INFO  pipeline manifest -> ")
            except WorkflowError:
                existing = self.latest_pipeline_manifest(
                    family,
                    preset,
                    accepted_statuses=accepted_statuses,
                )
            if existing is None:
                raise WorkflowError(
                    f"Could not locate an accepted pipeline manifest for {family}/{preset} "
                    f"with delivery_mode={delivery_mode!r}."
                )
        payload = read_json(existing)
        outputs = [Path(item).expanduser().resolve() for item in payload.get("final_outputs", [])]
        if not outputs:
            outputs = [Path(item).expanduser().resolve() for item in payload.get("base_final_outputs", [])]
        if not outputs:
            raise WorkflowError(f"{existing}: final_outputs is empty.")
        selected_output = outputs[-1]
        if not selected_output.exists():
            raise WorkflowError(f"{existing}: selected final output was not found: {selected_output}")
        width, height = image_dimensions(selected_output)
        assert_short_aspect_ratio(width, height, label=f"Still source {selected_output}")
        return existing, payload, selected_output

    def stage_still(
        self,
        still_path: Path,
        *,
        motion_prompt: str,
    ) -> tuple[Path, Path]:
        completed = self.run_command(
            [
                str(self.handoff_stage_script),
                str(still_path),
                "--from",
                "comfy",
                "--prompt",
                motion_prompt,
                "--width",
                str(DEFAULT_I2V_WIDTH),
                "--height",
                str(DEFAULT_I2V_HEIGHT),
            ],
            label=f"handoff-stage {still_path}",
        )
        staged_path = extract_info_path(completed.stdout, "INFO  Staged asset: ")
        manifest_path = extract_info_path(completed.stdout, "INFO  Manifest: ")
        return staged_path, manifest_path

    def render_motion_clip(
        self,
        staged_path: Path,
        *,
        motion_prompt: str,
        frames: int,
        motion_pipeline: str,
        output_path: Path,
    ) -> tuple[Path, Path]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_command(
            [
                str(self.handoff_i2v_script),
                str(staged_path),
                "--prompt",
                motion_prompt,
                "--frames",
                str(frames),
                "--width",
                str(DEFAULT_I2V_WIDTH),
                "--height",
                str(DEFAULT_I2V_HEIGHT),
                "--pipeline",
                motion_pipeline,
                "--typography",
                DEFAULT_I2V_TYPOGRAPHY,
                "--output",
                str(output_path),
            ],
            label=f"handoff-i2v {staged_path.name}",
        )
        return self.ensure_motion_clip_artifacts(
            output_path=output_path,
            staged_path=staged_path,
            motion_prompt=motion_prompt,
            frames=frames,
            motion_pipeline=motion_pipeline,
        )

    def import_raw_clip_override(
        self,
        source_path: Path,
        *,
        motion_prompt: str,
        frames: int,
        motion_pipeline: str,
        output_path: Path,
    ) -> tuple[Path, Path]:
        canonical_source = source_path.expanduser().resolve()
        canonical_output = output_path.expanduser().resolve()
        canonical_output.parent.mkdir(parents=True, exist_ok=True)
        if canonical_source != canonical_output:
            shutil.copy2(canonical_source, canonical_output)
        return self.ensure_motion_clip_artifacts(
            output_path=canonical_output,
            staged_path=None,
            motion_prompt=motion_prompt,
            frames=frames,
            motion_pipeline=motion_pipeline,
        )

    def render_still_hold_clip(
        self,
        still_path: Path,
        *,
        duration_seconds: float,
        fps: int,
        frames: int,
        output_path: Path,
    ) -> tuple[Path, Path]:
        canonical_output = output_path.expanduser().resolve()
        canonical_output.parent.mkdir(parents=True, exist_ok=True)
        scale_filter = (
            f"scale={DEFAULT_I2V_WIDTH}:{DEFAULT_I2V_HEIGHT}:flags=lanczos:"
            "force_original_aspect_ratio=decrease,"
            f"pad={DEFAULT_I2V_WIDTH}:{DEFAULT_I2V_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,"
            "setsar=1"
        )
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(still_path),
                "-vf",
                scale_filter,
                "-r",
                str(fps),
                "-t",
                f"{duration_seconds:.6f}",
                "-an",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                str(canonical_output),
            ],
            label=f"render still-hold clip {still_path.name}",
        )
        if not canonical_output.exists():
            raise WorkflowError(f"Still-hold clip was not created: {canonical_output}")
        width, height = ffprobe_dimensions(canonical_output)
        assert_short_aspect_ratio(width, height, label=f"Still-hold clip {canonical_output}")
        manifest_path = self.write_motion_clip_manifest(
            canonical_output,
            staged_path=None,
            motion_prompt="still_hold",
            frames=frames,
            motion_pipeline="still_holds",
        )
        return canonical_output, manifest_path

    def motion_recovery_candidate(self, output_path: Path) -> Path | None:
        canonical_output = output_path.expanduser().resolve()
        canonical_generated_root = self.shorts_generated_root.expanduser().resolve()
        try:
            relative = canonical_output.relative_to(canonical_generated_root)
        except ValueError:
            return None
        parts = relative.parts
        if len(parts) < 4:
            return None
        short_id, build_stamp = parts[0], parts[1]
        return (
            self.resolve_mlx_generated_shorts_root()
            / short_id
            / build_stamp
            / "motion_proofs"
            / "raw"
            / canonical_output.name
        )

    def write_motion_clip_manifest(
        self,
        output_path: Path,
        *,
        staged_path: Path | None,
        motion_prompt: str,
        frames: int,
        motion_pipeline: str,
        recovered_from_path: Path | None = None,
    ) -> Path:
        manifest_path = Path(f"{output_path}.json").resolve()
        payload = {
            "id": f"recovered-{utc_stamp()}",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_staged_path": str(staged_path.resolve()) if staged_path is not None else "",
            "input_base_image_path": str(staged_path.resolve()) if staged_path is not None else "",
            "input_image_path": str(staged_path.resolve()) if staged_path is not None else "",
            "prompt": motion_prompt,
            "seed": "",
            "frames": int(frames),
            "width": DEFAULT_I2V_WIDTH,
            "height": DEFAULT_I2V_HEIGHT,
            "pipeline": motion_pipeline,
            "model_repo": "",
            "resolved_model_path": "",
            "text_encoder_repo": "",
            "output_path": str(output_path.resolve()),
            "duration_seconds": round(ffprobe_duration(output_path), 6),
            "typography_mode": DEFAULT_I2V_TYPOGRAPHY,
            "typography_intent_path": "",
            "typography_run_manifest": "",
            "typography_validation": {},
            "recovered_from_path": str(recovered_from_path.resolve()) if recovered_from_path is not None else "",
        }
        write_json(manifest_path, payload)
        return manifest_path

    def ensure_motion_clip_artifacts(
        self,
        *,
        output_path: Path,
        staged_path: Path | None,
        motion_prompt: str,
        frames: int,
        motion_pipeline: str,
    ) -> tuple[Path, Path]:
        canonical_output = output_path.expanduser().resolve()
        manifest_path = Path(f"{canonical_output}.json").resolve()
        if not canonical_output.exists():
            recovery_candidate = self.motion_recovery_candidate(canonical_output)
            if recovery_candidate is not None and recovery_candidate.exists():
                canonical_output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(recovery_candidate, canonical_output)
                manifest_path = self.write_motion_clip_manifest(
                    canonical_output,
                    staged_path=staged_path,
                    motion_prompt=motion_prompt,
                    frames=frames,
                    motion_pipeline=motion_pipeline,
                    recovered_from_path=recovery_candidate,
                )
            else:
                raise WorkflowError(f"Expected motion clip was not created: {canonical_output}")
        elif not manifest_path.exists():
            manifest_path = self.write_motion_clip_manifest(
                canonical_output,
                staged_path=staged_path,
                motion_prompt=motion_prompt,
                frames=frames,
                motion_pipeline=motion_pipeline,
            )
        width, height = ffprobe_dimensions(canonical_output)
        assert_short_aspect_ratio(width, height, label=f"Motion clip {canonical_output}")
        return canonical_output, manifest_path

    def normalize_clip(
        self,
        raw_clip_path: Path,
        *,
        output_path: Path,
        duration_seconds: float,
        fps: int,
        start_seconds: float = 0.0,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        actual_duration = ffprobe_duration(raw_clip_path)
        filter_parts = []
        available_duration = max(0.0, actual_duration - start_seconds)
        if available_duration + 1e-6 < duration_seconds:
            filter_parts.append(f"tpad=stop_mode=clone:stop_duration={duration_seconds - available_duration:.6f}")
        if start_seconds > 0:
            filter_parts.append(f"trim=start={start_seconds:.6f}:duration={duration_seconds:.6f}")
        else:
            filter_parts.append(f"trim=duration={duration_seconds:.6f}")
        filter_parts.append("setpts=PTS-STARTPTS")
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_clip_path),
                "-vf",
                ",".join(filter_parts),
                "-r",
                str(fps),
                "-an",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                str(output_path),
            ],
            label=f"normalize clip {raw_clip_path.name}",
        )
        if not output_path.exists():
            raise WorkflowError(f"Normalized clip was not created: {output_path}")
        width, height = ffprobe_dimensions(output_path)
        assert_short_aspect_ratio(width, height, label=f"Normalized clip {output_path}")
        return output_path.resolve()

    def concat_picture_segments(
        self,
        clips: list[Path],
        *,
        concat_list_path: Path,
        output_path: Path,
    ) -> Path:
        if not clips:
            raise WorkflowError("No normalized clips were provided for concatenation.")
        concat_list_path.parent.mkdir(parents=True, exist_ok=True)
        concat_list_path.write_text(
            "".join(f"file '{clip.as_posix()}'\n" for clip in clips),
            encoding="utf-8",
        )
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_path),
                "-an",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                str(output_path),
            ],
            label="concat picture segments",
        )
        if not output_path.exists():
            raise WorkflowError(f"Picture master was not created: {output_path}")
        width, height = ffprobe_dimensions(output_path)
        assert_short_aspect_ratio(width, height, label=f"Picture master {output_path}")
        return output_path.resolve()

    def mux_proof(
        self,
        picture_path: Path,
        *,
        audio_path: Path,
        fps: int,
        output_path: Path,
    ) -> Path:
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(picture_path),
                "-i",
                str(audio_path),
                "-vf",
                "scale=1080:1920:flags=lanczos",
                "-r",
                str(fps),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(output_path),
            ],
            label="mux proof video",
        )
        if not output_path.exists():
            raise WorkflowError(f"Proof video was not created: {output_path}")
        width, height = ffprobe_dimensions(output_path)
        assert_short_aspect_ratio(width, height, label=f"Proof video {output_path}")
        return output_path.resolve()

    def build(
        self,
        short_id: str,
        *,
        delivery_mode: str = "strict",
        quality_profile: str = DEFAULT_RENDER_QUALITY,
        clip_mode: str = "animated",
        overlay_config_override: dict[str, Any] | None = None,
    ) -> Path:
        manifest_path = self.resolve_short_manifest_path(short_id)
        return self.build_manifest(
            manifest_path,
            delivery_mode=delivery_mode,
            quality_profile=quality_profile,
            clip_mode=clip_mode,
            overlay_config_override=overlay_config_override,
        )

    def build_manifest(
        self,
        manifest_path: Path,
        *,
        delivery_mode: str = "strict",
        quality_profile: str = DEFAULT_RENDER_QUALITY,
        clip_mode: str = "animated",
        overlay_config_override: dict[str, Any] | None = None,
    ) -> Path:
        ensure_command("ffmpeg")
        ensure_command("ffprobe")
        if clip_mode not in CLIP_MODES:
            raise WorkflowError(f"Unsupported clip_mode: {clip_mode!r}")

        payload = self.validate_short_manifest(manifest_path, read_json(manifest_path))
        short_id = str(payload["short_id"])
        overlay_config = merge_overlay_config(
            payload.get("overlay_config"),
            overlay_config_override,
            label=f"{manifest_path}: overlay_config",
        )
        headless_runtime = self.preflight_headless_runtime()

        build_stamp = utc_stamp()
        build_dir = self.shorts_generated_root / short_id / build_stamp
        raw_clips_dir = build_dir / "clips" / "raw"
        normalized_clips_dir = build_dir / "clips" / "normalized"
        raw_clips_dir.mkdir(parents=True, exist_ok=True)
        normalized_clips_dir.mkdir(parents=True, exist_ok=True)

        packaging_frame_override_path = payload.get("packaging_frame_still_override_path")
        if packaging_frame_override_path is not None:
            packaging_manifest_path = Path()
            packaging_pipeline = {
                "status": "override",
                "delivery_advisory_used": False,
            }
            packaging_frame_path = Path(packaging_frame_override_path).expanduser().resolve()
        else:
            packaging_manifest_path, packaging_pipeline, packaging_frame_path = self.ensure_pipeline_output(
                payload["packaging_family"],
                payload["packaging_preset"],
                quality_profile=quality_profile,
                delivery_mode=delivery_mode,
            )

        beat_entries: list[dict[str, Any]] = []
        normalized_clips: list[Path] = []
        for beat in payload["beats"]:
            still_override_path = beat.get("still_override_path")
            raw_clip_override_path = beat.get("raw_clip_override_path")
            still_pipeline_manifest_path: Path | None = None
            still_pipeline_manifest: dict[str, Any] = {}
            still_path: Path | None = None
            still_source_mode = "none"
            if still_override_path is not None:
                still_path = Path(still_override_path).expanduser().resolve()
                still_source_mode = "override"
            elif raw_clip_override_path is None or clip_mode == "still_holds":
                (
                    still_pipeline_manifest_path,
                    still_pipeline_manifest,
                    still_path,
                ) = self.ensure_pipeline_output(
                    beat["family"],
                    beat["preset"],
                    quality_profile=quality_profile,
                    delivery_mode=delivery_mode,
                )
                still_source_mode = "pipeline"

            staged_path: Path | None = None
            stage_manifest_path: Path | None = None
            raw_clip_source_mode = "rendered"
            if clip_mode == "still_holds":
                if still_path is None:
                    raise WorkflowError(
                        f"Beat {beat['id']} requires a portrait still source when clip_mode=still_holds."
                    )
                raw_clip_source_mode = "still_hold"
                raw_clip_path, raw_clip_manifest_path = self.render_still_hold_clip(
                    still_path,
                    duration_seconds=float(beat["target_duration_seconds"]),
                    fps=int(payload["fps"]),
                    frames=beat["frames"],
                    output_path=raw_clips_dir / f"{beat['id']}__raw.mp4",
                )
            elif raw_clip_override_path is not None:
                raw_clip_source_mode = "override"
                raw_clip_path, raw_clip_manifest_path = self.import_raw_clip_override(
                    Path(raw_clip_override_path).expanduser().resolve(),
                    motion_prompt=beat["motion_prompt"],
                    frames=beat["frames"],
                    motion_pipeline=beat["motion_pipeline"],
                    output_path=raw_clips_dir / f"{beat['id']}__raw.mp4",
                )
            else:
                if still_path is None:
                    raise WorkflowError(f"Beat {beat['id']} did not resolve to a still source.")
                staged_path, stage_manifest_path = self.stage_still(
                    still_path,
                    motion_prompt=beat["motion_prompt"],
                )
                raw_clip_path, raw_clip_manifest_path = self.render_motion_clip(
                    staged_path,
                    motion_prompt=beat["motion_prompt"],
                    frames=beat["frames"],
                    motion_pipeline=beat["motion_pipeline"],
                    output_path=raw_clips_dir / f"{beat['id']}__raw.mp4",
                )
            normalized_clip_path = self.normalize_clip(
                raw_clip_path,
                output_path=normalized_clips_dir / f"{beat['id']}__normalized.mp4",
                duration_seconds=float(beat["target_duration_seconds"]),
                fps=int(payload["fps"]),
                start_seconds=float(beat.get("motion_head_trim_seconds", 0.0)),
            )
            normalized_clips.append(normalized_clip_path)
            beat_entries.append(
                {
                    "id": beat["id"],
                    "preset_id": beat["preset_id"],
                    "cue_start_seconds": beat["cue_start_seconds"],
                    "cue_end_seconds": beat["cue_end_seconds"],
                    "target_duration_seconds": beat["target_duration_seconds"],
                    "requested_frames": beat.get("requested_frames", beat["frames"]),
                    "frames": beat["frames"],
                    "motion_prompt": beat["motion_prompt"],
                    "motion_pipeline": beat["motion_pipeline"],
                    "motion_head_trim_seconds": beat.get("motion_head_trim_seconds", 0.0),
                    "motion_handle_seconds": beat.get("motion_handle_seconds", 0.0),
                    "still_source_mode": still_source_mode,
                    "still_pipeline_manifest": str(still_pipeline_manifest_path or ""),
                    "still_pipeline_status": str(still_pipeline_manifest.get("status", "")),
                    "still_delivery_advisory_used": bool(
                        still_pipeline_manifest.get("delivery_advisory_used", False)
                    ),
                    "still_override_path": str(still_override_path or ""),
                    "still_path": str(still_path or ""),
                    "stage_manifest_path": str(stage_manifest_path or ""),
                    "staged_path": str(staged_path or ""),
                    "raw_clip_source_mode": raw_clip_source_mode,
                    "raw_clip_override_path": str(raw_clip_override_path or ""),
                    "raw_clip_path": str(raw_clip_path),
                    "raw_clip_manifest_path": str(raw_clip_manifest_path),
                    "normalized_clip_path": str(normalized_clip_path),
                }
            )

        concat_list_path = build_dir / "concat_inputs.txt"
        clean_picture_path = self.concat_picture_segments(
            normalized_clips,
            concat_list_path=concat_list_path,
            output_path=build_dir / f"{build_stamp}__picture_master.mp4",
        )
        overlay_picture_path: Path | None = None
        final_picture_path = clean_picture_path
        if overlay_config is not None:
            overlay_picture_path = self.apply_overlay_to_picture_master(
                clean_picture_path,
                overlay_config=overlay_config,
                output_path=build_dir / f"{build_stamp}__overlay_picture_master.mp4",
            )
            final_picture_path = overlay_picture_path
        proof_path = self.mux_proof(
            final_picture_path,
            audio_path=payload["audio_path"],
            fps=int(payload["fps"]),
            output_path=build_dir / f"{build_stamp}__proof.mp4",
        )

        proof_manifest_path = build_dir / f"{build_stamp}__proof.json"
        build_manifest = {
            "short_id": payload["short_id"],
            "title": payload["title"],
            "episode_id": payload["episode_id"],
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "delivery_mode": delivery_mode,
            "clip_mode": clip_mode,
            "render_quality_profile": quality_profile,
            "source_manifest": str(manifest_path),
            "audio_path": str(payload["audio_path"]),
            "audio_duration_seconds": round(float(payload["audio_duration_seconds"]), 6),
            "transcript_path": str(payload["transcript_path"]),
            "short_audio_package_path": str(payload.get("short_audio_package_path", "")),
            "expected_voice_profile_id": payload.get("expected_voice_profile_id", ""),
            "audio_package_sha256": payload.get("audio_package_sha256", ""),
            "packaged_audio_sha256": payload.get("packaged_audio_sha256", ""),
            "audio_disposition": payload.get("audio_disposition", ""),
            "caption_source_path": str(payload.get("caption_source_path", "")),
            "transcript_sha256": payload.get("transcript_sha256", ""),
            "audio_provenance": payload.get("audio_provenance", {}),
            "fps": int(payload["fps"]),
            "overlay_enabled": overlay_config is not None,
            "overlay_config": overlay_config or {},
            "headless_comfy": headless_runtime,
            "packaging_frame_id": payload["packaging_frame_id"],
            "packaging_frame_pipeline_manifest": str(packaging_manifest_path),
            "packaging_frame_status": str(packaging_pipeline.get("status", "")),
            "packaging_frame_delivery_advisory_used": bool(
                packaging_pipeline.get("delivery_advisory_used", False)
            ),
            "packaging_frame_still_override_path": str(packaging_frame_override_path or ""),
            "packaging_frame_path": str(packaging_frame_path),
            "clean_picture_master_path": str(clean_picture_path),
            "overlay_picture_master_path": str(overlay_picture_path or ""),
            "picture_master_path": str(final_picture_path),
            "proof_path": str(proof_path),
            "beats": beat_entries,
        }
        write_json(proof_manifest_path, build_manifest)
        beat_sheet_path = self.render_beat_sheet(proof_manifest_path)
        build_manifest["beat_sheet_path"] = str(beat_sheet_path)
        write_json(proof_manifest_path, build_manifest)
        print(f"INFO  short manifest -> {proof_manifest_path}")
        print(f"INFO  proof video -> {proof_path}")
        print(f"INFO  beat sheet -> {beat_sheet_path}")
        return proof_manifest_path

    def load_historical_signal_profiles(self) -> dict[str, dict[str, Any]]:
        if not HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH.exists():
            raise WorkflowError(
                f"Historical signal texture registry is missing: {HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH}"
            )
        payload = read_json(HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH)
        profiles = payload.get("profiles", [])
        if not isinstance(profiles, list) or not profiles:
            raise WorkflowError(f"{HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH}: expected non-empty profiles list.")
        indexed: dict[str, dict[str, Any]] = {}
        for profile in profiles:
            if not isinstance(profile, dict):
                continue
            profile_id = normalize_text(profile.get("historical_signal_profile_id"))
            if profile_id:
                indexed[profile_id] = profile
        return indexed

    def historical_signal_payload_defaults(self, payload: dict[str, Any]) -> dict[str, Any]:
        defaults: dict[str, Any] = {}
        for key in (
            "texture_influence",
            "historical_context_year_or_range",
            "source_media_era",
            "historical_signal_profile_id",
            "signal_texture_strength",
            "disposition",
            "human_review_disposition",
            "review_disposition",
            "hygiene_read",
            "strict_clean_read",
            "strict_clean_repair_read",
            "temporal_coherence_read",
            "physical_plausibility_read",
            "source_motion_alignment_read",
            "archival_fidelity_read",
            "motion_review_read",
            "source_clean_read",
        ):
            value = payload.get(key)
            if value not in (None, ""):
                defaults[key] = value
        if "texture_influence" not in defaults and (
            normalize_text(payload.get("historical_signal_profile_id"))
            or normalize_text(payload.get("visual_noaudio_path"))
            or normalize_text(payload.get("texture_applied_path"))
        ):
            defaults["texture_influence"] = "house_crt"
        return defaults

    def motion_manifest_rows(self, manifest_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("items", "rows", "shot_timing_edl"):
            rows = payload.get(key)
            if isinstance(rows, list):
                defaults = self.historical_signal_payload_defaults(payload)
                return [{**defaults, **dict(row)} for row in rows if isinstance(row, dict)]
        visual_noaudio_path = normalize_text(payload.get("visual_noaudio_path"))
        if visual_noaudio_path:
            defaults = self.historical_signal_payload_defaults(payload)
            return [
                {
                    **defaults,
                    "row_id": normalize_text(payload.get("proof_id")) or "proof_visual_noaudio",
                    "shot_id": normalize_text(payload.get("proof_id")) or "proof_visual_noaudio",
                    "visual_noaudio_path": visual_noaudio_path,
                    "disposition": payload.get("disposition") or defaults.get("disposition") or "keep",
                }
            ]
        shots = payload.get("shots")
        if isinstance(shots, list):
            defaults = self.historical_signal_payload_defaults(payload)
            if defaults:
                return [{**defaults, **dict(row)} for row in shots if isinstance(row, dict)]
        raise WorkflowError(f"{manifest_path}: expected one of items, rows, or shot_timing_edl.")

    def historical_signal_row_source_path(self, manifest_path: Path, row: dict[str, Any], index: int) -> Path:
        for key in (
            "visual_noaudio_path",
            "normalized_no_audio_path",
            "normalized_clip_path",
            "vertical_clip_path",
            "source_motion_clip_path",
            "source_clip_path",
            "source_path",
            "output_path",
            "motion_clip_path",
            "clean_motion_path",
        ):
            value = normalize_text(row.get(key))
            if value:
                return resolve_absolute_path(value, label=f"{manifest_path}: rows[{index}].{key}")
        raise WorkflowError(f"{manifest_path}: rows[{index}] is eligible for texture but has no source clip path.")

    def historical_signal_row_id(self, row: dict[str, Any], index: int) -> str:
        for key in ("row_id", "edl_id", "case_id", "shot_id", "id"):
            value = normalize_text(row.get(key))
            if value:
                return value
        return f"row_{index + 1:02d}"

    def historical_signal_keep_like(self, row: dict[str, Any]) -> bool:
        for key in ("disposition", "motion_disposition", "review_disposition", "human_review_disposition"):
            value = normalize_disposition(row.get(key))
            if not value:
                continue
            if value == "keep" or value.startswith("keep ") or value.startswith("resolved keep"):
                return True
            if " keep" in value and "reject" not in value and "tighten" not in value:
                return True
        return False

    def historical_signal_failed_source_read(self, row: dict[str, Any]) -> str | None:
        checked_fields = (
            "hygiene_read",
            "strict_clean_read",
            "strict_clean_repair_read",
            "temporal_coherence_read",
            "physical_plausibility_read",
            "source_motion_alignment_read",
            "archival_fidelity_read",
            "motion_review_read",
            "source_clean_read",
        )
        for key in checked_fields:
            value = normalize_disposition(row.get(key))
            if not value:
                continue
            if value in {"pass", "not applicable", "none"} or value.startswith("pass "):
                continue
            if "pass" in value and "reject" not in value and "tighten" not in value and "fail" not in value:
                continue
            return f"{key}={row.get(key)!r}"
        return None

    def normalize_historical_signal_rows(
        self,
        manifest_path: Path,
        payload: dict[str, Any],
        *,
        profile_override: str | None,
        strength_override: str | None,
        profiles: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        eligible: list[dict[str, Any]] = []
        rows = self.motion_manifest_rows(manifest_path, payload)
        registry_policy = read_json(HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH).get("global_policy", {})
        default_house_profile_id = normalize_text(registry_policy.get("default_house_profile_id"))
        for index, row in enumerate(rows):
            texture_influence = normalize_text(row.get("texture_influence"))
            if texture_influence not in {"house_crt", "selective_archival"}:
                continue
            if not self.historical_signal_keep_like(row):
                continue
            failed_read = self.historical_signal_failed_source_read(row)
            if failed_read:
                raise WorkflowError(
                    f"{manifest_path}: rows[{index}] cannot enter historical_signal_texture because {failed_read}."
                )
            row_profile = normalize_text(row.get("historical_signal_profile_id"))
            if row_profile and row_profile not in profiles:
                raise WorkflowError(f"{manifest_path}: unsupported historical signal profile {row_profile!r}.")
            if profile_override and row_profile and row_profile != profile_override:
                raise WorkflowError(
                    f"{manifest_path}: rows[{index}] profile {row_profile!r} conflicts with --profile {profile_override!r}."
                )
            profile_id = profile_override or default_house_profile_id or row_profile
            if not profile_id:
                raise WorkflowError(f"{manifest_path}: rows[{index}] requires historical_signal_profile_id or --profile.")
            if profile_id not in profiles:
                raise WorkflowError(f"{manifest_path}: unsupported historical signal profile {profile_id!r}.")
            profile = profiles[profile_id]
            if normalize_text(profile.get("production_status")).startswith("legacy_reference_inactive"):
                raise WorkflowError(
                    f"{manifest_path}: historical signal profile {profile_id!r} is inactive; use the house CRT profile."
                )
            strength = strength_override or normalize_text(row.get("signal_texture_strength"))
            if not strength or strength == "none":
                strength = normalize_text(profile.get("default_strength")) or "visible_but_premium"
            if strength not in HISTORICAL_SIGNAL_STRENGTHS:
                raise WorkflowError(f"{manifest_path}: unsupported signal texture strength {strength!r}.")
            source_path = self.historical_signal_row_source_path(manifest_path, row, index)
            source_probe = ffprobe_video_info(source_path)
            assert_short_aspect_ratio(
                int(source_probe["width"]),
                int(source_probe["height"]),
                label=f"historical_signal_texture source {source_path}",
            )
            if int(source_probe["audio_stream_count"]) != 0:
                raise WorkflowError(f"{source_path}: historical_signal_texture sources must be no-audio.")
            normalized = {
                **row,
                "row_index": index,
                "row_id": self.historical_signal_row_id(row, index),
                "source_motion_clip_path": str(source_path),
                "source_motion_sha256": file_sha256(source_path),
                "source_motion_probe": source_probe,
                "historical_signal_profile_id": profile_id,
                "profile": profile,
                "signal_texture_strength": strength,
            }
            eligible.append(normalized)
        if not eligible:
            raise WorkflowError(f"{manifest_path}: no keep rows with texture_influence house_crt were found.")
        return eligible

    def historical_strength_scale(self, strength: str) -> float:
        return {
            "low": 0.45,
            "low_to_visible": 0.72,
            "low_to_medium": 0.82,
            "visible_but_premium": 1.0,
            "medium": 1.18,
        }[strength]

    def historical_signal_conservative_clean(self, source: Path, output: Path, *, probe: dict[str, Any]) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        width = int(probe["width"])
        height = int(probe["height"])
        fps = float(probe["fps"])
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-vf",
                (
                    f"fps={fps:.6f},scale={width}:{height}:flags=lanczos,"
                    "hqdn3d=0.8:0.6:2.0:1.5,"
                    "unsharp=5:5:0.28:3:3:0.12,"
                    "eq=contrast=1.015:saturation=1.01:brightness=0.002,"
                    "setsar=1,format=yuv420p"
                ),
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                f"{fps:.6f}",
                "-color_primaries",
                "bt709",
                "-color_trc",
                "bt709",
                "-colorspace",
                "bt709",
                "-movflags",
                "+faststart",
                "-an",
                str(output),
            ],
            label="historical signal conservative clean",
        )
        return output.resolve()

    def historical_signal_filter_graph(
        self,
        *,
        profile_id: str,
        strength: str,
        width: int,
        height: int,
        fps: float,
    ) -> str:
        scale = self.historical_strength_scale(strength)
        base = f"[0:v]fps={fps:.6f},scale={width}:{height}:flags=lanczos,setsar=1"
        if profile_id == "era_1980s_broadcast_crt_v1":
            noise = max(1.0, 2.0 * scale)
            scan_alpha = max(3, int(round(8 * scale)))
            bloom = 0.020 + (0.012 * scale)
            return (
                f"{base},crop={max(2, width - 1)}:{max(2, height - 1)}:"
                "0.5+0.7*sin(n/17):0.5+0.7*cos(n/19),"
                f"scale={width}:{height}:flags=bicubic,"
                "chromashift=cbh=1:crh=-1,"
                f"eq=contrast={1.015 + (0.010 * scale):.3f}:brightness=0.002:"
                f"saturation={1.0 - (0.040 * scale):.3f}:gamma=1.005,"
                f"noise=alls={noise:.2f}:allf=t+u,"
                "split[base][glow];"
                f"[glow]gblur=sigma={0.65 + (0.25 * scale):.2f},"
                "eq=brightness=0.006:saturation=0.90[glow2];"
                f"[base][glow2]blend=all_mode=screen:all_opacity={bloom:.3f}[glowed];"
                f"color=c=black:s={width}x{height}:r={fps:.6f},format=rgba,"
                f"geq=r='0':g='0':b='0':a='if(eq(mod(Y,4),0),{scan_alpha},0)'[scan];"
                "[glowed][scan]overlay=shortest=1:format=auto,setsar=1,format=yuv420p[v]"
            )
        if profile_id == "era_1940s_archival_film_v1":
            return (
                f"{base},crop={max(2, width - 2)}:{max(2, height - 2)}:"
                "1+0.55*sin(n/23):1+0.45*cos(n/29),"
                f"scale={width}:{height}:flags=bicubic,"
                f"eq=contrast={1.045 + (0.030 * scale):.3f}:brightness=0.001:"
                f"saturation={0.78 - (0.08 * min(scale, 1.2)):.3f},"
                f"noise=alls={1.6 + (1.5 * scale):.2f}:allf=t+u,"
                "unsharp=3:3:0.10:3:3:0.04,setsar=1,format=yuv420p[v]"
            )
        if profile_id == "era_1980s_institutional_video_v1":
            return (
                f"{base},gblur=sigma={0.10 + (0.18 * scale):.2f},"
                f"chromashift=cbh={1 if scale >= 0.7 else 0}:crh=0,"
                f"eq=contrast={1.005 + (0.010 * scale):.3f}:saturation={0.94 - (0.03 * scale):.3f},"
                f"noise=alls={0.7 + (0.9 * scale):.2f}:allf=t+u,setsar=1,format=yuv420p[v]"
            )
        if profile_id == "era_1990s_news_v1":
            return (
                f"{base},chromashift=cbh=1:crh=0,"
                f"eq=contrast={1.010 + (0.012 * scale):.3f}:saturation={0.96 - (0.02 * scale):.3f},"
                f"noise=alls={0.8 + (0.9 * scale):.2f}:allf=t+u,setsar=1,format=yuv420p[v]"
            )
        if profile_id == "era_2000s_digital_news_v1":
            return (
                f"{base},hqdn3d=0.4:0.4:1.0:1.0,"
                f"eq=contrast={1.005 + (0.008 * scale):.3f}:saturation={0.98 - (0.015 * scale):.3f},"
                "unsharp=3:3:0.08:3:3:0.03,setsar=1,format=yuv420p[v]"
            )
        if profile_id == "era_2010s_mobile_news_v1":
            return (
                f"{base},hqdn3d=0.25:0.25:0.7:0.7,"
                f"eq=contrast={1.002 + (0.006 * scale):.3f}:saturation={0.99 - (0.010 * scale):.3f},"
                "setsar=1,format=yuv420p[v]"
            )
        raise WorkflowError(f"Unsupported historical signal profile: {profile_id!r}")

    def apply_historical_signal_texture(
        self,
        source: Path,
        output: Path,
        *,
        profile_id: str,
        strength: str,
        probe: dict[str, Any],
    ) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        width = int(probe["width"])
        height = int(probe["height"])
        fps = float(probe["fps"])
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-filter_complex",
                self.historical_signal_filter_graph(
                    profile_id=profile_id,
                    strength=strength,
                    width=width,
                    height=height,
                    fps=fps,
                ),
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
                f"{fps:.6f}",
                "-color_primaries",
                "bt709",
                "-color_trc",
                "bt709",
                "-colorspace",
                "bt709",
                "-movflags",
                "+faststart",
                "-an",
                str(output),
            ],
            label=f"historical signal texture {profile_id}",
        )
        return output.resolve()

    def make_youtube_survival_proxy(self, source: Path, output: Path, *, fps: float) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        self.run_command(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-c:v",
                "libx264",
                "-profile:v",
                "high",
                "-b:v",
                "5M",
                "-maxrate",
                "5M",
                "-bufsize",
                "10M",
                "-pix_fmt",
                "yuv420p",
                "-r",
                f"{fps:.6f}",
                "-color_primaries",
                "bt709",
                "-color_trc",
                "bt709",
                "-colorspace",
                "bt709",
                "-movflags",
                "+faststart",
                "-an",
                str(output),
            ],
            label="historical signal youtube survival proxy",
        )
        return output.resolve()

    def extract_historical_signal_review_frames(
        self,
        *,
        item_dir: Path,
        row_id: str,
        source_path: Path,
        texture_path: Path,
        proxy_path: Path,
        duration_seconds: float,
    ) -> dict[str, dict[str, str]]:
        frame_times = {
            "start": 0.05,
            "mid": max(0.05, duration_seconds / 2.0),
            "end": max(0.05, duration_seconds - 0.08),
        }
        frames: dict[str, dict[str, str]] = {}
        for variant, path in {
            "baseline": source_path,
            "signal": texture_path,
            "youtube_proxy": proxy_path,
        }.items():
            frames[variant] = {}
            for frame_name, seconds in frame_times.items():
                out = item_dir / f"{row_id}__{variant}__{frame_name}.jpg"
                frames[variant][frame_name] = str(extract_video_frame(path, out, seconds=seconds))
        return frames

    def render_historical_signal_review_sheet(
        self,
        items: list[dict[str, Any]],
        output_path: Path,
    ) -> Path:
        if Image is None or ImageDraw is None or ImageFont is None:
            raise WorkflowError("Pillow is required to render historical signal review sheets.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            resampling = Image.Resampling.LANCZOS
        except AttributeError:  # pragma: no cover - older Pillow compatibility
            resampling = Image.LANCZOS
        font = ImageFont.load_default()
        label_w = 360
        thumb_w = 150
        thumb_h = 267
        gap = 12
        header_h = 58
        row_h = thumb_h + 52
        columns = (("baseline", "baseline"), ("signal", "texture_applied"), ("5mbps", "youtube_proxy"))
        canvas_w = label_w + len(columns) * (thumb_w + gap) + gap
        canvas_h = header_h + max(1, len(items)) * row_h
        sheet = Image.new("RGB", (canvas_w, canvas_h), (10, 10, 10))
        draw = ImageDraw.Draw(sheet)
        draw.text((16, 18), "Historical signal texture review - baseline / signal / 5Mbps", fill=(245, 245, 245), font=font)
        for idx, (label, _key) in enumerate(columns):
            draw.text((label_w + gap + idx * (thumb_w + gap), 36), label, fill=(205, 205, 205), font=font)
        for row_index, item in enumerate(items):
            y = header_h + row_index * row_h
            label = "\n".join(
                [
                    f"{item['order_label']} {item['row_id']}",
                    str(item.get("shot_id") or item.get("visual_beat_id") or ""),
                    str(item["historical_signal_profile_id"]),
                    str(item["signal_texture_strength"]),
                ]
            )
            self.draw_sheet_text(
                draw,
                xy=(16, y + 8),
                text=label,
                font=font,
                fill=(235, 235, 235),
                max_chars=42,
                line_height=16,
                max_lines=5,
            )
            for idx, (_label, key) in enumerate(columns):
                frame_path = Path(item["frame_audit_paths"][key]["mid"])
                with Image.open(frame_path) as frame:
                    thumb = frame.convert("RGB").resize((thumb_w, thumb_h), resampling)
                x = label_w + gap + idx * (thumb_w + gap)
                sheet.paste(thumb, (x, y + 8))
        sheet.save(output_path)
        return output_path.resolve()

    def write_historical_signal_review_note(
        self,
        path: Path,
        manifest: dict[str, Any],
    ) -> Path:
        if not path.is_absolute():
            raise WorkflowError(f"--review-note-output must be an absolute path, got {path}.")
        if path.suffix.lower() != ".md":
            raise WorkflowError(f"--review-note-output must be a markdown file, got {path}.")
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Historical Signal Texture Review",
            "",
            f"- `stage`: `historical_signal_texture`",
            f"- `episode_id`: `{manifest.get('episode_id', '')}`",
            f"- `short_id`: `{manifest.get('short_id', '')}`",
            f"- `pass_id`: `{manifest['pass_id']}`",
            f"- `created_at`: `{manifest['created_at']}`",
            f"- `disposition`: `{manifest['disposition']}`",
            f"- `historical_signal_texture_read`: `{manifest['historical_signal_texture_read']}`",
            f"- `texture_visibility_read`: `{manifest['texture_visibility_read']}`",
            f"- `texture_readability_read`: `{manifest['texture_readability_read']}`",
            f"- `may_start_motion_video_proof`: `{str(manifest['may_start_motion_video_proof']).lower()}`",
            f"- `manifest_path`: `{manifest['manifest_path']}`",
            f"- `review_sheet_path`: `{manifest['review_sheet_path']}`",
            f"- `candidate_count`: `{manifest['candidate_count']}`",
            "",
            "## Review Required",
            "",
            "Human/DP review must confirm texture visibility, house CRT consistency, YouTube survivability, compression artifacts, and subject/detail survival before any textured clip can enter a keeper motion proof. Randomized TV static/noise is reviewed separately when a proof assembly inserts inter-clip static transitions.",
            "",
            "## Candidates",
            "",
            "| row | profile | strength | textured clip | YouTube proxy |",
            "| --- | --- | --- | --- | --- |",
        ]
        for item in manifest["items"]:
            lines.append(
                f"| `{item['row_id']}` | `{item['historical_signal_profile_id']}` | "
                f"`{item['signal_texture_strength']}` | `{item['texture_applied_path']}` | "
                f"`{item['youtube_survival_proxy_path']}` |"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path.resolve()

    def historical_signal_texture(
        self,
        motion_manifest_path: Path,
        *,
        pass_id: str,
        review_note_output: Path,
        output_root: Path | None = None,
        profile: str | None = None,
        strength: str | None = None,
    ) -> Path:
        ensure_command("ffmpeg")
        ensure_command("ffprobe")
        manifest_path = resolve_absolute_path(str(motion_manifest_path), label="motion_manifest_path")
        review_note_target = review_note_output.expanduser()
        if not review_note_target.is_absolute():
            raise WorkflowError(f"--review-note-output must be an absolute path, got {review_note_output}.")
        if review_note_target.suffix.lower() != ".md":
            raise WorkflowError(f"--review-note-output must be a markdown file, got {review_note_output}.")
        review_note_target = review_note_target.resolve()
        pass_tag = re.sub(r"[^A-Za-z0-9_.-]+", "_", normalize_text(pass_id)).strip("_")
        if not pass_tag:
            raise WorkflowError("--pass-id must contain at least one filename-safe character.")
        if output_root is not None:
            if not output_root.is_absolute():
                raise WorkflowError(f"--output-root must be an absolute path, got {output_root}.")
            package_root = output_root.expanduser().resolve()
        else:
            package_root = manifest_path.parent / "historical_signal_texture"
        run_id = utc_stamp()
        run_root = package_root / pass_tag / run_id
        conservative_dir = run_root / "conservative_clean"
        signal_dir = run_root / "historical_signal"
        proxy_dir = run_root / "youtube_proxy_5mbps"
        frames_dir = run_root / "review_frames"
        sheets_dir = run_root / "review_sheets"
        for directory in (conservative_dir, signal_dir, proxy_dir, frames_dir, sheets_dir):
            directory.mkdir(parents=True, exist_ok=True)

        payload = read_json(manifest_path)
        profiles = self.load_historical_signal_profiles()
        rows = self.normalize_historical_signal_rows(
            manifest_path,
            payload,
            profile_override=profile,
            strength_override=strength,
            profiles=profiles,
        )
        items: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            source_path = Path(row["source_motion_clip_path"])
            source_probe = dict(row["source_motion_probe"])
            width = int(source_probe["width"])
            height = int(source_probe["height"])
            fps = float(source_probe["fps"])
            row_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(row["row_id"])).strip("_") or f"row_{index + 1:02d}"
            order_label = f"{index + 1:02d}"
            if "order" in row:
                order_label = f"{int(row['order']):02d}" if str(row["order"]).isdigit() else str(row["order"])
            profile_id = str(row["historical_signal_profile_id"])
            signal_strength = str(row["signal_texture_strength"])
            stem = f"{order_label}_{row_id}"
            clean_path = self.historical_signal_conservative_clean(
                source_path,
                conservative_dir / f"{stem}__conservative_clean__no_audio.mp4",
                probe=source_probe,
            )
            clean_probe = ffprobe_video_info(clean_path)
            texture_path = self.apply_historical_signal_texture(
                clean_path,
                signal_dir / f"{stem}__{profile_id}__{signal_strength}__no_audio.mp4",
                profile_id=profile_id,
                strength=signal_strength,
                probe=clean_probe,
            )
            texture_probe = ffprobe_video_info(texture_path)
            proxy_path = self.make_youtube_survival_proxy(
                texture_path,
                proxy_dir / f"{stem}__{profile_id}__youtube_5mbps_proxy__no_audio.mp4",
                fps=fps,
            )
            proxy_probe = ffprobe_video_info(proxy_path)
            for label, probe in (("conservative_clean", clean_probe), ("texture_applied", texture_probe), ("youtube_proxy", proxy_probe)):
                assert_short_aspect_ratio(int(probe["width"]), int(probe["height"]), label=f"{label} {stem}")
                if int(probe["audio_stream_count"]) != 0:
                    raise WorkflowError(f"{label} output for {stem} unexpectedly has audio.")
            item_frame_dir = frames_dir / stem
            frame_paths = self.extract_historical_signal_review_frames(
                item_dir=item_frame_dir,
                row_id=row_id,
                source_path=source_path,
                texture_path=texture_path,
                proxy_path=proxy_path,
                duration_seconds=float(texture_probe["duration_seconds"]),
            )
            items.append(
                {
                    "row_index": row["row_index"],
                    "row_id": row["row_id"],
                    "order_label": order_label,
                    "shot_id": row.get("shot_id", ""),
                    "visual_beat_id": row.get("visual_beat_id") or row.get("beat_id") or "",
                    "texture_influence": "house_crt",
                    "historical_context_year_or_range": row.get("historical_context_year_or_range")
                    or row["profile"].get("historical_context_year_or_range", ""),
                    "source_media_era": row.get("source_media_era") or row["profile"].get("source_media_era", ""),
                    "historical_signal_profile_id": profile_id,
                    "signal_texture_strength": signal_strength,
                    "texture_source_lane": row["profile"].get("source_lane", "conservative_clean"),
                    "texture_application_scope": "house_crt_story_clips",
                    "inter_clip_static_policy": "randomized_tv_static_between_story_clips",
                    "source_motion_clip_path": str(source_path),
                    "source_motion_sha256": row["source_motion_sha256"],
                    "source_motion_probe": source_probe,
                    "conservative_clean_path": str(clean_path),
                    "conservative_clean_sha256": file_sha256(clean_path),
                    "conservative_clean_probe": clean_probe,
                    "texture_applied_path": str(texture_path),
                    "texture_applied_sha256": file_sha256(texture_path),
                    "texture_applied_probe": texture_probe,
                    "youtube_survival_proxy_path": str(proxy_path),
                    "youtube_survival_proxy_sha256": file_sha256(proxy_path),
                    "youtube_proxy_probe": proxy_probe,
                    "frame_audit_paths": {
                        "baseline": frame_paths["baseline"],
                        "texture_applied": frame_paths["signal"],
                        "youtube_proxy": frame_paths["youtube_proxy"],
                    },
                    "full_bleed": True,
                    "machine_checks_read": "pass",
                    "audio_stream_read": "pass",
                    "geometry_read": "pass",
                    "source_clean_read": row.get("source_clean_read")
                    or row.get("strict_clean_read")
                    or row.get("hygiene_read")
                    or "not_recorded_no_failed_reads",
                    "texture_visibility_read": "pending_human_review",
                    "texture_readability_read": "pending_human_review",
                    "house_crt_texture_read": "pending_human_review",
                    "randomized_static_transition_read": "not_applicable",
                    "historical_signal_texture_read": "pending_human_review",
                    "youtube_survival_read": "pending_human_review",
                    "compression_artifact_read": "pending_human_review",
                    "detail_survival_read": "pending_human_review",
                    "texture_failure_mode": "none",
                    "disposition": "tighten",
                    "may_start_motion_video_proof": False,
                }
            )

        review_sheet_path = self.render_historical_signal_review_sheet(
            items,
            sheets_dir / "historical_signal_texture_review_sheet.png",
        )
        manifest_path_out = run_root / "historical_signal_texture_manifest.json"
        manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "stage": "historical_signal_texture",
            "episode_id": payload.get("episode_id", ""),
            "short_id": payload.get("short_id", ""),
            "pass_id": pass_tag,
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "input_motion_manifest_path": str(manifest_path),
            "input_motion_manifest_sha256": file_sha256(manifest_path),
            "historical_signal_texture_registry_path": str(HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH),
            "historical_signal_texture_registry_sha256": file_sha256(HISTORICAL_SIGNAL_TEXTURE_REGISTRY_PATH),
            "output_root": str(run_root),
            "manifest_path": str(manifest_path_out),
            "review_note_path": str(review_note_target),
            "review_sheet_path": str(review_sheet_path),
            "review_sheet_sha256": file_sha256(review_sheet_path),
            "candidate_count": len(items),
            "completed_candidate_count": len(items),
            "items": items,
            "disposition": "tighten",
            "reel_class": "texture review package",
            "machine_checks_read": "pass",
            "historical_signal_texture_read": "pending_human_review",
            "texture_visibility_read": "pending_human_review",
            "texture_readability_read": "pending_human_review",
            "house_crt_texture_read": "pending_human_review",
            "randomized_static_transition_read": "not_applicable",
            "youtube_survival_read": "pending_human_review",
            "compression_artifact_read": "pending_human_review",
            "detail_survival_read": "pending_human_review",
            "may_start_motion_video_proof": False,
            "may_start_video_final": False,
            "blockers": [
                "human/DP review required before textured clips can enter motion video proof",
                "proof assembly and final export intentionally not performed by this v1 runner",
            ],
        }
        review_note_path = self.write_historical_signal_review_note(review_note_target, manifest)
        manifest["review_note_path"] = str(review_note_path)
        manifest["review_note_sha256"] = file_sha256(review_note_path)
        write_json(manifest_path_out, manifest)
        print(f"INFO  historical signal texture manifest -> {manifest_path_out}")
        print(f"INFO  historical signal texture review note -> {review_note_path}")
        print(f"INFO  historical signal texture review sheet -> {review_sheet_path}")
        return manifest_path_out.resolve()

    def export_midjourney(self, short_id: str) -> Path:
        manifest_path = self.resolve_short_manifest_path(short_id)
        payload = self.validate_short_manifest(manifest_path, read_json(manifest_path))
        if not payload["episode_id"]:
            raise WorkflowError(f"{manifest_path}: episode_id is required for Midjourney export.")

        visual_research_dir = self.discover_visual_research_dir(payload["audio_path"])
        sources_markdown_path = visual_research_dir / "sources.md"
        if not sources_markdown_path.exists():
            raise WorkflowError(f"Research sources markdown was not found: {sources_markdown_path}")
        source_inventory = self.load_source_inventory(visual_research_dir)

        cover_spec = self.load_stage_spec(payload["packaging_family"], payload["packaging_preset"], stage="draft_txt2img")
        style_id = normalize_text(cover_spec.get("params", {}).get("style_profile"))
        if not style_id:
            raise WorkflowError(f"{self.resolve_stage_spec_path(payload['packaging_family'], payload['packaging_preset'])}: style_profile is required.")
        style_profile_path = self.repo_root / "workflows" / "style_profiles" / f"{style_id}.json"
        self.load_style_profile(style_id)

        package_root = manifest_path.parent / "midjourney" / short_id
        if package_root.exists():
            shutil.rmtree(package_root)
        package_root.mkdir(parents=True, exist_ok=True)

        cover_entry = self.shot_entry_for_export(
            package_root=package_root,
            shot_id="cover",
            prompt_subject="Challenger compressed into one institutional warning signal",
            preset_id=payload["packaging_frame_id"],
            cue_start_seconds=None,
            cue_end_seconds=None,
            source_inventory=source_inventory,
            reference_ids=self.selection_for_shot(
                payload["episode_id"],
                "cover",
                short_id=payload["short_id"],
                is_cover=True,
            ),
            is_cover=True,
        )

        shot_entries: list[dict[str, Any]] = []
        for beat in payload["beats"]:
            shot_entries.append(
                self.shot_entry_for_export(
                    package_root=package_root,
                    shot_id=beat["id"],
                    prompt_subject=beat["preset"].replace("_", " "),
                    preset_id=beat["preset_id"],
                    cue_start_seconds=float(beat["cue_start_seconds"]),
                    cue_end_seconds=float(beat["cue_end_seconds"]),
                    source_inventory=source_inventory,
                    reference_ids=self.selection_for_shot(
                        payload["episode_id"],
                        beat["id"],
                        short_id=payload["short_id"],
                    ),
                )
            )

        source_documents = {
            "short_manifest_path": str(manifest_path),
            "style_profile_path": str(style_profile_path),
            "source_inventory_path": str(visual_research_dir / "source_inventory.json"),
            "sources_markdown_path": str(sources_markdown_path),
        }
        shot_list_path = self.write_shot_list(
            package_root=package_root,
            title=payload["title"],
            cover_entry=cover_entry,
            shot_entries=shot_entries,
            source_documents=source_documents,
        )
        package_manifest_path = package_root / "package.manifest.json"
        package_manifest = {
            "package_id": f"{short_id}__midjourney_v1",
            "style_id": style_id,
            "surface_type": MIDJOURNEY_SURFACE_TYPE,
            "reference_mode": MIDJOURNEY_REFERENCE_MODE,
            "source_documents": source_documents,
            "midjourney_defaults": {
                "parameter_suffix": MIDJOURNEY_DEFAULT_SUFFIX,
                "negative_terms": list(MIDJOURNEY_NEGATIVE_TERMS),
                "manual_upload_workflow": True,
            },
            "cover": cover_entry,
            "shots": shot_entries,
            "shot_list_path": relative_path_text(shot_list_path, start=package_root),
        }
        write_json(package_manifest_path, package_manifest)
        print(f"INFO  Midjourney package manifest -> {package_manifest_path}")
        return package_manifest_path


def main() -> int:
    args = parse_args()
    builder = ShortBuilder(
        repo_root=Path(args.repo_root),
        models_root=Path(args.models_root),
        comfy_workflows_dir=Path(args.comfy_workflows_dir),
        comfy_output_dir=Path(args.comfy_output_dir),
        references_root=Path(args.references_root),
    )
    if args.command == "build":
        builder.build(
            args.short_id,
            delivery_mode=args.delivery_mode,
            quality_profile=args.quality_profile,
            clip_mode=args.clip_mode,
            overlay_config_override=build_overlay_config_override(
                preset=args.overlay_preset,
                strength=args.overlay_strength,
                disable=args.overlay_disable,
            ),
        )
        return 0
    if args.command == "build-manifest":
        builder.build_manifest(
            builder.resolve_build_manifest_path(args.manifest_path),
            delivery_mode=args.delivery_mode,
            quality_profile=args.quality_profile,
            clip_mode=args.clip_mode,
            overlay_config_override=build_overlay_config_override(
                preset=args.overlay_preset,
                strength=args.overlay_strength,
                disable=args.overlay_disable,
            ),
        )
        return 0
    if args.command == "historical-signal-texture":
        output_root = Path(args.output_root).expanduser() if args.output_root else None
        if output_root is not None and not output_root.is_absolute():
            raise WorkflowError(f"--output-root must be an absolute path, got {args.output_root!r}.")
        builder.historical_signal_texture(
            Path(args.motion_manifest_path).expanduser(),
            pass_id=args.pass_id,
            review_note_output=Path(args.review_note_output).expanduser(),
            output_root=output_root.resolve() if output_root else None,
            profile=args.profile,
            strength=args.strength,
        )
        return 0
    if args.command == "beat-sheet":
        output_path = None
        if args.output:
            output_path = Path(args.output).expanduser()
            if not output_path.is_absolute():
                raise WorkflowError(f"--output must be an absolute path, got {args.output!r}.")
            output_path = output_path.resolve()
        beat_sheet_path = builder.render_beat_sheet(Path(args.target), output_path=output_path)
        proof_manifest_path = builder.resolve_existing_proof_manifest(Path(args.target))
        payload = read_json(proof_manifest_path)
        payload["beat_sheet_path"] = str(beat_sheet_path)
        write_json(proof_manifest_path, payload)
        print(f"INFO  beat sheet -> {beat_sheet_path}")
        return 0
    if args.command == "final-export":
        builder.final_export_existing_build(
            Path(args.target),
            proof_review_note=Path(args.proof_review_note).expanduser(),
            proof_disposition=args.proof_disposition,
            reel_class=args.reel_class,
            all_motion_clips_keep=args.all_motion_clips_keep,
            no_diagnostic_placeholders=args.no_diagnostic_placeholders,
            caption_style=args.caption_style,
            caption_placement=args.caption_placement,
            caption_source=Path(args.caption_source).expanduser() if args.caption_source else None,
            caption_timing=Path(args.caption_timing).expanduser() if args.caption_timing else None,
            manual_timing_adjustments=Path(args.manual_timing_adjustments).expanduser()
            if args.manual_timing_adjustments
            else None,
            output_tag=args.output_tag,
            music_policy=args.music_policy,
            music_track_registry=Path(args.music_track_registry).expanduser(),
            music_track_id=args.music_track_id,
            music_waiver_reason=args.music_waiver_reason,
            music_rights_check_status=args.music_rights_check_status,
            source_motion_tail_path=Path(args.source_motion_tail_path).expanduser()
            if args.source_motion_tail_path
            else None,
            source_motion_tail_source_clip_id=args.source_motion_tail_source_clip_id,
            source_motion_tail_source_path=Path(args.source_motion_tail_source_path).expanduser()
            if args.source_motion_tail_source_path
            else None,
            source_motion_tail_span_in=args.source_motion_tail_span_in,
            source_motion_tail_span_out=args.source_motion_tail_span_out,
            source_motion_tail_residual_hold_max=args.source_motion_tail_residual_hold_max,
            house_crt_static_manifest=Path(args.house_crt_static_manifest).expanduser()
            if args.house_crt_static_manifest
            else None,
            house_crt_static_waiver_reason=args.house_crt_static_waiver_reason,
        )
        return 0
    if args.command == "export-midjourney":
        builder.export_midjourney(args.short_id)
        return 0
    raise WorkflowError(f"Unsupported short command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
