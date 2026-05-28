#!/usr/bin/env python3
"""Build a local Semmelweis proof with a source-led theme-intro hook."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any


BASE_SCRIPT = Path("/Users/mike/Agents_CascadeEffects/scripts/build_challenger_explosion_theme_intro_hook_proof.py")
spec = importlib.util.spec_from_file_location("theme_hook_builder", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to import {BASE_SCRIPT}")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


EPISODE_ID = "semmelweis"
SHORT_ID = "semmelweis_short_scoped_v1"
DISPLAY_NAME = "Semmelweis"

EPISODE_SHORT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/shorts/semmelweis_short_scoped_v1")
LATEST_PUBLISH_DIR = EPISODE_SHORT_ROOT / "publish/youtube_20260429T044416Z"
CURRENT_YOUTUBE_SHORT = LATEST_PUBLISH_DIR / "semmelweis_handwashing_evidence_youtube_short.mp4"
VOICE_WAV = EPISODE_SHORT_ROOT / "final/semmelweis_short_scoped_v1.wav"

SEMMELWEIS_VIZ_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/semmelweis/shorts/semmelweis_short_scoped_v1"
)
PASS01D_ROOT = SEMMELWEIS_VIZ_ROOT / "motion_video_proof/pass_01d_head_in_hands_ending"
PASS01D_SEGMENTS_DIR = PASS01D_ROOT / "segments_no_audio"
BODY_TARGET_REFERENCE = PASS01D_ROOT / "semmelweis_motion_video_proof_pass_01d_head_in_hands_ending_no_captions.mp4"

HOOK_SOURCE = (
    SEMMELWEIS_VIZ_ROOT
    / "visual_research/operating_room_childbirth_bnw_repair_pass_05/candidate_clips_no_audio/"
    "p05_03_delivery_room_team_no_audio.mp4"
)
PASS05_CANDIDATES_DIR = (
    SEMMELWEIS_VIZ_ROOT
    / "visual_research/operating_room_childbirth_bnw_repair_pass_05/candidate_clips_no_audio"
)
PASS04_CANDIDATES_DIR = (
    SEMMELWEIS_VIZ_ROOT
    / "visual_research/youtube_newsreel_doc_no_charts_letters_pass_04/candidate_clips_no_audio"
)
PASS04_LIGHTBOX_ALLOWLIST = {
    "A": PASS04_CANDIDATES_DIR / "p04_04_autopsy_room_source_no_audio.mp4",
    "B": PASS04_CANDIDATES_DIR / "p04_06_inserm_basin_disinfection_no_audio.mp4",
}
BLOCKED_HISTORICAL_ANACHRONISM_SOURCES = [
    PASS04_CANDIDATES_DIR / name
    for name in (
        "p04_01_pathe_hospital_front_no_audio.mp4",
        "p04_01_pathe_street_facade_no_audio.mp4",
        "p04_02_pathe_courtyard_gathering_no_audio.mp4",
        "p04_02_pathe_courtyard_people_no_audio.mp4",
        "p04_03_inserm_ward_depth_no_audio.mp4",
        "p04_03_pathe_faculty_room_table_no_audio.mp4",
        "p04_05_pathe_faculty_room_no_audio.mp4",
        "p04_05_pathe_memorial_flowers_no_audio.mp4",
        "p04_07_pathe_audience_pressure_no_audio.mp4",
        "p04_08_pathe_public_ceremony_no_audio.mp4",
        "p04_09_pathe_hospital_skyline_no_audio.mp4",
        "p04_09_pathe_skyline_consequence_no_audio.mp4",
        "semmelweis_no_charts_letters_review_reel_pass_04_no_audio.mp4",
    )
]
BODY_REPAIR_SOURCES = {
    "04": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_04_clinic_threshold_entry_no_audio.mp4",
        "repair_id": "segment_04_repeat_variance_repair",
        "reason": "replace repeat-prone split-clinic body slot with a distinct moving clinic-threshold entry angle",
        "read": "pass_review_required",
    },
    "05": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_06_ward_role_contrast_no_audio.mp4",
        "repair_id": "segment_05_repeat_variance_repair",
        "reason": "replace body slot 05 because the prior proof had an obvious 05-to-06 same-patient-bed repeat",
        "read": "pass_review_required",
    },
    "06": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_09_midwife_doctor_room_no_audio.mp4",
        "repair_id": "segment_06_historical_accuracy_repair",
        "reason": "replace the historically inaccurate pass-04 exterior/courtyard shot with an existing Semmelweis clinical interior motion clip",
        "read": "pass_review_required",
    },
    "07": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_11_childbed_action_non_graphic_no_audio.mp4",
        "repair_id": "segment_07_historical_accuracy_repair",
        "reason": "replace the historically inaccurate pass-04 street/facade shot with an existing Semmelweis clinical interior motion clip",
        "read": "pass_review_required",
    },
    "08": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_12_childbed_aftershock_no_audio.mp4",
        "repair_id": "segment_08_historical_accuracy_repair",
        "reason": "replace the historically inaccurate pass-04 memorial/exterior shot with an existing Semmelweis clinical interior motion clip",
        "read": "pass_review_required",
    },
    "10": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_10_midwife_doctor_exchange_no_audio.mp4",
        "repair_id": "segment_10_historical_accuracy_repair",
        "reason": "replace the historically inaccurate pass-04 skyline shot with an existing Semmelweis clinical interior motion clip",
        "read": "pass_review_required",
    },
    "12": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_07_bedside_exam_close_no_audio.mp4",
        "repair_id": "segment_12_historical_accuracy_repair",
        "reason": "replace the historically inaccurate pass-04 hospital-front shot with an existing Semmelweis clinical interior motion clip",
        "read": "pass_review_required",
    },
    "13": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_02_doctors_over_maternity_bed_no_audio.mp4",
        "repair_id": "segment_13_historical_accuracy_repair",
        "reason": "replace the historically inaccurate pass-04 courtyard shot with an existing Semmelweis clinical interior motion clip",
        "read": "pass_review_required",
    },
    "15": {
        "replacement_source": PASS05_CANDIDATES_DIR / "p05_05_low_bedside_shadow_no_audio.mp4",
        "repair_id": "segment_15_historical_accuracy_repair",
        "reason": "replace the pass-04 ward-depth shot from the restricted lightbox with an existing Semmelweis clinical interior motion clip",
        "read": "pass_review_required",
    },
}
TAIL_SOURCE = HOOK_SOURCE
PRE_CLOSING_INSERT_SOURCE = PASS05_CANDIDATES_DIR / "p05_08_doctor_bends_to_bed_no_audio.mp4"

HOOK_SOURCE_START_SECONDS = 0.0
HOOK_DURATION_SECONDS = 3.0
TAIL_SOURCE_START_SECONDS = HOOK_SOURCE_START_SECONDS
TAIL_SINGLE_PASS_DURATION_SECONDS = 2.4
PRE_CLOSING_INSERT_DURATION_SECONDS = 3.071542
TAIL_SEQUENCE_DURATION_SECONDS = PRE_CLOSING_INSERT_DURATION_SECONDS + TAIL_SINGLE_PASS_DURATION_SECONDS
SIGNAL_INTERRUPT_SECONDS = 0.25
VOICE_LAST_AUDIBLE_SECONDS = 57.353288
OUTRO_START_SECONDS = 58.866667
FINAL_DURATION_SECONDS = 65.838209

USER_REPORTED_REPEAT_RANGES = [
    {
        "range_id": "middle_bedside_repeat_run",
        "proof_start_seconds": 19.5,
        "proof_end_seconds": 30.8,
        "reported_problem": "20-30s clips are too similar and repetitive",
        "target_segment_ids": ["06", "07", "08"],
        "blocked_family_id": "bedside_doctor_over_patient",
    },
    {
        "range_id": "thirty_seven_second_bedside_repeat",
        "proof_start_seconds": 34.5,
        "proof_end_seconds": 39.5,
        "reported_problem": "37s clip matches the repetitive bedside family",
        "target_segment_ids": ["10"],
        "blocked_family_id": "bedside_doctor_over_patient",
    },
    {
        "range_id": "pre_tail_public_audience_reuse",
        "proof_start_seconds": 52.5,
        "proof_end_seconds": 66.8,
        "reported_problem": "clip shown at about 1 minute is reused before the ending",
        "target_segment_ids": ["15"],
        "blocked_family_id": "public_ceremony_audience",
    },
]

VISUAL_FAMILY_BY_FILENAME = {
    "01_edl_01_childbed_hook.mp4": "childbed_close_hook",
    "02_edl_02_bedside_pressure.mp4": "bedside_pressure",
    "03_edl_03_room_roles.mp4": "room_roles_wide",
    "04_edl_04_split_clinic_role_contrast.mp4": "split_clinic_role_contrast",
    "05_edl_05_delivery_team.mp4": "delivery_team",
    "06_edl_06_childbed_action.mp4": "bedside_doctor_over_patient",
    "07_edl_07_aftershock.mp4": "bedside_doctor_over_patient",
    "08_edl_08_bedside_transfer_long_crop.mp4": "bedside_doctor_over_patient",
    "09_edl_09_role_pressure_no_blip.mp4": "midwife_doctor_exchange",
    "10_edl_10_intervention_clean_source.mp4": "bedside_doctor_over_patient",
    "11_edl_11_ward_role_reset.mp4": "ward_role_reset",
    "12_edl_12_identity_exchange_continuation.mp4": "identity_exchange",
    "13_edl_13a_institutional_pressure_room.mp4": "institution_room",
    "14_edl_13b_childbed_consequence_no_repeat.mp4": "bedside_consequence",
    "15_edl_14_identity_bridge_part_one.mp4": "public_ceremony_audience",
    "16_edl_15_identity_bridge_part_two.mp4": "identity_bridge",
    "17_edl_16_signature_sem_head_in_hands.mp4": "signature_head_in_hands",
    "p05_02_doctors_over_maternity_bed_no_audio.mp4": "doctors_over_maternity_bed",
    "p05_03_delivery_room_team_no_audio.mp4": "delivery_room_team_opening",
    "p05_04_clinic_threshold_entry_no_audio.mp4": "clinic_threshold_entry",
    "p05_05_low_bedside_shadow_no_audio.mp4": "low_bedside_shadow",
    "p05_06_ward_role_contrast_no_audio.mp4": "ward_role_contrast",
    "p05_07_bedside_exam_close_no_audio.mp4": "bedside_exam_close",
    "p05_08_doctor_bends_to_bed_no_audio.mp4": "doctor_bends_to_bed",
    "p05_09_midwife_doctor_room_no_audio.mp4": "midwife_doctor_room",
    "p05_10_midwife_doctor_exchange_no_audio.mp4": "midwife_doctor_exchange",
    "p05_11_childbed_action_non_graphic_no_audio.mp4": "childbed_action_non_graphic",
    "p05_12_childbed_aftershock_no_audio.mp4": "childbed_aftershock",
    "p04_04_autopsy_room_source_no_audio.mp4": "allowed_autopsy_room",
    "p04_06_inserm_basin_disinfection_no_audio.mp4": "basin_disinfection",
    "p04_02_pathe_courtyard_gathering_no_audio.mp4": "courtyard_gathering",
    "p04_01_pathe_street_facade_no_audio.mp4": "institution_street_facade",
    "p04_05_pathe_memorial_flowers_no_audio.mp4": "memorial_flowers",
    "p04_09_pathe_hospital_skyline_no_audio.mp4": "hospital_skyline",
    "p04_01_pathe_hospital_front_no_audio.mp4": "hospital_front",
    "p04_02_pathe_courtyard_people_no_audio.mp4": "courtyard_people",
    "p04_03_inserm_ward_depth_no_audio.mp4": "ward_depth",
    "semmelweis_no_charts_letters_review_reel_pass_04_no_audio.mp4": "public_ceremony_audience",
}


def visual_family_id(path: Path | str) -> str:
    return VISUAL_FAMILY_BY_FILENAME.get(Path(path).name, "unknown")


def configure_semmelweis(
    body_source: Path | None = None,
    tail_source: Path | None = None,
    tail_start_seconds: float | None = None,
) -> None:
    builder.SHORT_ROOT = EPISODE_SHORT_ROOT
    builder.LATEST_PUBLISH_DIR = LATEST_PUBLISH_DIR
    builder.CURRENT_YOUTUBE_SHORT = CURRENT_YOUTUBE_SHORT
    builder.BODY_CAPTIONED_NO_AUDIO = (
        body_source if body_source is not None else PASS01D_ROOT / "semmelweis_motion_video_proof_pass_01d_visual_bed_no_audio.mp4"
    )
    builder.NO_CAPTION_PICTURE = HOOK_SOURCE
    builder.VOICE_WAV = VOICE_WAV
    builder.HOOK_SOURCE_START_SECONDS = HOOK_SOURCE_START_SECONDS
    builder.HOOK_DURATION_SECONDS = HOOK_DURATION_SECONDS
    builder.THEME_INTRO_SECONDS = 3.0
    builder.LOOP_START_SECONDS = 2.25
    builder.LOOP_CROSSFADE_SECONDS = 0.75
    builder.VOICE_DELAY_SECONDS = 3.0
    builder.VOICE_LAST_AUDIBLE_SECONDS = VOICE_LAST_AUDIBLE_SECONDS
    builder.OUTRO_START_SECONDS = OUTRO_START_SECONDS
    builder.FINAL_DURATION_SECONDS = FINAL_DURATION_SECONDS
    builder.HOOK_CRT_TEXTURE = None
    builder.FULL_PICTURE_CRT_TEXTURE = {
        "profile_id": "era_1980s_broadcast_crt_v1",
        "intensity": "visible_but_premium",
        "purpose": "apply one continuous CRT/analog texture over the assembled Semmelweis hook, body, and tail proof",
        "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
        "scanline_strength_variant_id": "max_visible_bars_y24_p8",
        "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
    }
    builder.SOURCE_MOTION_TAIL = {
        "path": tail_source if tail_source is not None else TAIL_SOURCE,
        "start_seconds": tail_start_seconds if tail_start_seconds is not None else TAIL_SOURCE_START_SECONDS,
        "description": "moving no-audio Semmelweis pre-closing clinical insert plus the opening delivery-room clip returned as the final full-theme-outro tail",
        "house_crt_tail_texture": None,
        "signal_interruption": {
            "profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
            "duration_seconds": SIGNAL_INTERRUPT_SECONDS,
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "full_frame_static_replacement_used": False,
            "purpose": "brief analog interruption between the clean pass-01d body and the pre-closing insert/final same-source outro tail sequence",
        },
    }


def require_inputs() -> None:
    configure_semmelweis()
    for path in (
        CURRENT_YOUTUBE_SHORT,
        VOICE_WAV,
        builder.THEME_FULL,
        builder.THEME_LOOP_60,
        builder.THEME_OUTRO,
        PASS01D_SEGMENTS_DIR,
        BODY_TARGET_REFERENCE,
        HOOK_SOURCE,
        TAIL_SOURCE,
        PRE_CLOSING_INSERT_SOURCE,
        builder.BODY_CAPTIONED_NO_AUDIO,
        *PASS04_LIGHTBOX_ALLOWLIST.values(),
        *BLOCKED_HISTORICAL_ANACHRONISM_SOURCES,
        *[Path(context["replacement_source"]) for context in BODY_REPAIR_SOURCES.values()],
    ):
        if not Path(path).exists():
            raise FileNotFoundError(str(path))


def mark_source_package_tighten(source_package: Path | None) -> dict[str, Any]:
    if source_package is None:
        return {
            "source_package_path": None,
            "manifest_updated": False,
            "review_note_updated": False,
            "read": "not_applicable",
        }
    reason = (
        "Current latest proof is marked tighten because the successor Semmelweis local review proof "
        "repairs body/tail visual issues while preserving the approved hook, audio, signal rhythm, "
        "full-picture CRT pass, deferred captions, and no-YouTube boundary."
    )
    context: dict[str, Any] = {
        "source_package_path": str(source_package),
        "reason": reason,
        "human_review_disposition": "tighten",
        "manifest_updated": False,
        "review_note_updated": False,
        "read": "pass",
    }
    manifest_path = source_package / "semmelweis_theme_intro_hook_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["human_review_disposition"] = "tighten"
        manifest["first_second_hook_read"] = "tighten"
        manifest["tighten_reason"] = reason
        manifest["repeat_clip_read"] = "tighten"
        manifest["still_frozen_clip_read"] = "tighten"
        manifest["reported_repeat_read"] = "tighten"
        manifest["tail_reuse_read"] = "tighten"
        manifest["tighten_successor_policy"] = "semmelweis_local_review_visual_tighten_only"
        builder.write_json(manifest_path, manifest)
        context["manifest_path"] = str(manifest_path)
        context["manifest_sha256"] = builder.sha256(manifest_path)
        context["manifest_updated"] = True
    else:
        context["read"] = "tighten_manifest_missing"

    note_path = source_package / "review_note.md"
    if note_path.exists():
        marker = "## Current Review Disposition"
        note = note_path.read_text(encoding="utf-8")
        if marker not in note:
            note += (
                "\n\n## Current Review Disposition\n\n"
                "- `human_review_disposition`: `tighten`\n"
                "- `first_second_hook_read`: `tighten`\n"
                f"- `tighten_reason`: {reason}\n"
            )
            builder.write_text(note_path, note)
        context["review_note_path"] = str(note_path)
        context["review_note_sha256"] = builder.sha256(note_path)
        context["review_note_updated"] = True
    return context


def pass01d_body_segments() -> list[Path]:
    segments = sorted(PASS01D_SEGMENTS_DIR.glob("*.mp4"))
    if len(segments) != 17:
        raise RuntimeError(f"Expected 17 Semmelweis pass-01d body segments, found {len(segments)}")
    expected_prefixes = [f"{index:02d}_" for index in range(1, 18)]
    actual_prefixes = [segment.name[:3] for segment in segments]
    if actual_prefixes != expected_prefixes:
        raise RuntimeError(f"Unexpected Semmelweis pass-01d segment order: {actual_prefixes}")
    return segments


def apply_tail_signal_interruption(source: Path, output: Path, boundary_id: str) -> dict[str, Any]:
    source_duration = builder.duration(source)
    if source_duration <= SIGNAL_INTERRUPT_SECONDS:
        raise RuntimeError(f"Source is too short for signal-interruption boundary {boundary_id}: {source}")
    signal_start = source_duration - SIGNAL_INTERRUPT_SECONDS
    output.parent.mkdir(parents=True, exist_ok=True)
    builder.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-filter_complex",
            (
                f"[0:v]trim=0:{signal_start:.6f},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "setsar=1,fps=30,format=yuv420p[main];"
                f"[0:v]trim=start={signal_start:.6f}:duration={SIGNAL_INTERRUPT_SECONDS:.6f},"
                "setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                f"setsar=1,fps=30,format=yuv420p,{builder.signal_interruption_filter_chain()},format=yuv420p[sig];"
                f"[main][sig]concat=n=2:v=1:a=0,trim=0:{source_duration:.6f},"
                "setpts=PTS-STARTPTS,format=yuv420p[v]"
            ),
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
            "30",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return {
        "boundary_id": boundary_id,
        "source_path": str(source),
        "source_sha256": builder.sha256(source),
        "prepared_path": str(output),
        "prepared_sha256": builder.sha256(output),
        "duration_seconds": round(builder.duration(output), 6),
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPT_SECONDS,
        "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
        "full_frame_static_replacement_used": False,
        "cloned_frame_padding_used": False,
        "read": "pass_review_required",
    }


def normalize_segment(
    source: Path,
    output: Path,
    target_duration_seconds: float | None = None,
    source_start_seconds: float = 0.0,
) -> dict[str, Any]:
    source_duration = builder.duration(source)
    target_duration = source_duration if target_duration_seconds is None else target_duration_seconds
    usable_source_duration = source_duration - source_start_seconds
    if source_duration <= 0 or target_duration <= 0 or usable_source_duration <= 0:
        raise RuntimeError(f"Invalid source/target duration for {source}: {source_duration} -> {target_duration}")
    retime_factor = target_duration / usable_source_duration if usable_source_duration + 0.001 < target_duration else 1.0
    retime_filter = f"setpts={retime_factor:.12f}*PTS," if retime_factor != 1.0 else ""
    output.parent.mkdir(parents=True, exist_ok=True)
    builder.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-an",
            "-vf",
            (
                f"trim=start={source_start_seconds:.6f}:duration={usable_source_duration:.6f},"
                f"setpts=PTS-STARTPTS,{retime_filter}"
                f"trim=0:{target_duration:.6f},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "setsar=1,fps=30,format=yuv420p"
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
            "30",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return {
        "source_path": str(source),
        "source_sha256": builder.sha256(source),
        "source_start_seconds": round(source_start_seconds, 6),
        "usable_source_duration_seconds": round(usable_source_duration, 6),
        "prepared_path": str(output),
        "prepared_sha256": builder.sha256(output),
        "duration_seconds": round(builder.duration(output), 6),
        "target_duration_seconds": round(target_duration, 6),
        "retime_factor": round(retime_factor, 9),
        "subtle_retime_used": retime_factor != 1.0,
        "normalization": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "cloned_frame_padding_used": False,
    }


def normalize_source_span(
    source: Path,
    output: Path,
    start_seconds: float,
    duration_seconds: float,
) -> dict[str, Any]:
    if duration_seconds <= 0:
        raise RuntimeError(f"Invalid source span duration for {source}: {duration_seconds}")
    output.parent.mkdir(parents=True, exist_ok=True)
    builder.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-an",
            "-vf",
            (
                f"trim=start={start_seconds:.6f}:duration={duration_seconds:.6f},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "setsar=1,fps=30,format=yuv420p"
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
            "30",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return {
        "source_path": str(source),
        "source_sha256": builder.sha256(source),
        "source_start_seconds": round(start_seconds, 6),
        "requested_duration_seconds": round(duration_seconds, 6),
        "prepared_path": str(output),
        "prepared_sha256": builder.sha256(output),
        "prepared_duration_seconds": round(builder.duration(output), 6),
        "normalization": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "cloned_frame_padding_used": False,
    }


def build_prepared_tail_sequence(
    insert_with_signal: Path,
    final_tail_clip: Path,
    output: Path,
    target_duration_seconds: float,
) -> dict[str, Any]:
    insert_duration = builder.duration(insert_with_signal)
    final_tail_duration = builder.duration(final_tail_clip)
    output.parent.mkdir(parents=True, exist_ok=True)
    builder.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(insert_with_signal),
            "-i",
            str(final_tail_clip),
            "-filter_complex",
            (
                f"[0:v]trim=0:{insert_duration:.6f},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "setsar=1,fps=30,format=yuv420p[v0];"
                f"[1:v]trim=0:{final_tail_duration:.6f},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "setsar=1,fps=30,format=yuv420p[v1];"
                f"[v0][v1]concat=n=2:v=1:a=0,trim=0:{target_duration_seconds:.6f},"
                "setpts=PTS-STARTPTS,format=yuv420p[v]"
            ),
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
            "30",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return {
        "prepared_tail_sequence_path": str(output),
        "prepared_tail_sequence_sha256": builder.sha256(output),
        "prepared_tail_sequence_duration_seconds": round(builder.duration(output), 6),
        "target_duration_seconds": round(target_duration_seconds, 6),
        "insert_with_signal_path": str(insert_with_signal),
        "insert_with_signal_sha256": builder.sha256(insert_with_signal),
        "insert_with_signal_duration_seconds": round(insert_duration, 6),
        "final_tail_clip_path": str(final_tail_clip),
        "final_tail_clip_sha256": builder.sha256(final_tail_clip),
        "final_tail_clip_duration_seconds": round(final_tail_duration, 6),
        "cloned_frame_padding_used": False,
        "looped_source_span_used": False,
        "read": "pass_review_required",
    }


def loop_source_span_to_duration(
    source: Path,
    output: Path,
    start_seconds: float,
    unit_duration_seconds: float,
    target_duration_seconds: float,
) -> dict[str, Any]:
    if unit_duration_seconds <= 0 or target_duration_seconds <= 0:
        raise RuntimeError(
            f"Invalid loop/target duration for {source}: {unit_duration_seconds} -> {target_duration_seconds}"
        )
    source_duration = builder.duration(source)
    if start_seconds + unit_duration_seconds > source_duration + 0.05:
        raise RuntimeError(
            f"Loop unit exceeds source duration for {source}: start {start_seconds:.3f}s + "
            f"unit {unit_duration_seconds:.3f}s > source {source_duration:.3f}s"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    unit_output = output.with_name(f"{output.stem}_loop_unit.mp4")
    unit_context = normalize_source_span(source, unit_output, start_seconds, unit_duration_seconds)
    builder.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-stream_loop",
            "-1",
            "-i",
            str(unit_output),
            "-t",
            f"{target_duration_seconds:.6f}",
            "-an",
            "-vf",
            (
                f"trim=0:{target_duration_seconds:.6f},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "setsar=1,fps=30,format=yuv420p"
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
            "30",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return {
        "source_path": str(source),
        "source_sha256": builder.sha256(source),
        "source_start_seconds": round(start_seconds, 6),
        "loop_unit_duration_seconds": round(unit_duration_seconds, 6),
        "target_duration_seconds": round(target_duration_seconds, 6),
        "prepared_path": str(output),
        "prepared_sha256": builder.sha256(output),
        "prepared_duration_seconds": round(builder.duration(output), 6),
        "loop_unit_path": str(unit_output),
        "loop_unit_sha256": builder.sha256(unit_output),
        "loop_unit_context": unit_context,
        "loop_count_estimate": round(target_duration_seconds / unit_duration_seconds, 6),
        "looped_source_span_used": True,
        "subtle_retime_used": False,
        "retime_factor": 1.0,
        "normalization": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "cloned_frame_padding_used": False,
        "source_tail_low_motion_span_avoided": True,
    }


def build_clean_body_from_segments(work: Path) -> dict[str, Any]:
    segments = pass01d_body_segments()
    prepared_segments: list[dict[str, Any]] = []
    body_signal_boundaries: list[dict[str, Any]] = []
    body_clip_motion_repairs: list[dict[str, Any]] = []

    for index, segment in enumerate(segments):
        segment_id = segment.name.split("_", 1)[0]
        next_segment = segments[index + 1] if index + 1 < len(segments) else None
        next_segment_id = next_segment.name.split("_", 1)[0] if next_segment else None
        source_for_signal = segment
        source_path = segment
        replacement_context = None
        if segment_id in BODY_REPAIR_SOURCES:
            repair = BODY_REPAIR_SOURCES[segment_id]
            replacement_source = Path(repair["replacement_source"])
            replacement_prepared_path = (
                work
                / "body_motion_repairs"
                / f"body_{segment_id}_replacement_{replacement_source.stem}_no_audio.mp4"
            )
            original_duration = builder.duration(segment)
            normalization_context = normalize_segment(
                replacement_source,
                replacement_prepared_path,
                target_duration_seconds=original_duration,
                source_start_seconds=float(repair.get("source_start_seconds", 0.0)),
            )
            source_for_signal = replacement_prepared_path
            source_path = replacement_source
            replacement_context = {
                "repair_id": repair["repair_id"],
                "segment_id": segment_id,
                "original_segment_path": str(segment),
                "original_segment_sha256": builder.sha256(segment),
                "original_segment_duration_seconds": round(original_duration, 6),
                "replacement_source_path": str(replacement_source),
                "replacement_source_sha256": builder.sha256(replacement_source),
                "replacement_source_start_seconds": normalization_context["source_start_seconds"],
                "usable_replacement_source_duration_seconds": normalization_context["usable_source_duration_seconds"],
                "prepared_replacement_path": str(replacement_prepared_path),
                "prepared_replacement_sha256": builder.sha256(replacement_prepared_path),
                "prepared_replacement_duration_seconds": round(builder.duration(replacement_prepared_path), 6),
                "visual_family_id": visual_family_id(replacement_source),
                "target_duration_seconds": normalization_context["target_duration_seconds"],
                "retime_factor": normalization_context["retime_factor"],
                "subtle_retime_used": normalization_context["subtle_retime_used"],
                "normalization": normalization_context["normalization"],
                "cloned_frame_padding_used": False,
                "reason": repair["reason"],
                "read": repair["read"],
            }
            body_clip_motion_repairs.append(replacement_context)
        signal_context = None
        if next_segment is not None:
            boundary_id = f"body_{segment_id}_to_{next_segment_id}"
            prepared_path = work / "body_signal_boundaries" / f"{boundary_id}_signal_replaced_no_audio.mp4"
            signal_context = apply_tail_signal_interruption(source_for_signal, prepared_path, boundary_id)
        else:
            prepared_path = work / "normalized_segments" / f"body_{segment_id}_normalized_no_audio.mp4"
            normalize_segment(source_for_signal, prepared_path)
        prepared_segments.append(
            {
                "segment_id": segment_id,
                "source_path": source_path,
                "original_segment_path": segment,
                "source_for_signal_path": source_for_signal,
                "prepared_path": prepared_path,
                "signal_context": signal_context,
                "incoming_segment_id": next_segment_id,
                "replacement_context": replacement_context,
            }
        )

    concat_path = work / "concat_semmelweis_pass01d_source_body_segments.txt"
    untrimmed_body_output = work / "semmelweis_pass01d_clean_body_from_source_segments_untrimmed_no_audio.mp4"
    body_output = work / "semmelweis_pass01d_clean_body_from_source_segments_no_audio.mp4"
    body_target_duration = builder.duration(BODY_TARGET_REFERENCE)
    builder.write_text(concat_path, "".join(f"file '{row['prepared_path']}'\n" for row in prepared_segments))
    builder.run(
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
            "-an",
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-movflags",
            "+faststart",
            str(untrimmed_body_output),
        ]
    )
    builder.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(untrimmed_body_output),
            "-an",
            "-vf",
            f"trim=0:{body_target_duration:.6f},setpts=PTS-STARTPTS,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-movflags",
            "+faststart",
            str(body_output),
        ]
    )

    segment_rows: list[dict[str, Any]] = []
    cursor = 0.0
    for row in prepared_segments:
        segment = Path(row["prepared_path"])
        raw_segment_duration = builder.duration(segment)
        remaining_duration = max(0.0, body_target_duration - cursor)
        if remaining_duration <= 0:
            break
        segment_duration = min(raw_segment_duration, remaining_duration)
        proof_start = builder.HOOK_DURATION_SECONDS + cursor
        proof_end = builder.HOOK_DURATION_SECONDS + cursor + segment_duration
        segment_rows.append(
            {
                "path": str(segment),
                "sha256": builder.sha256(segment),
                "source_path": str(row["source_path"]),
                "source_sha256": builder.sha256(Path(row["source_path"])),
                "visual_family_id": visual_family_id(row["source_path"]),
                "original_segment_path": str(row["original_segment_path"]),
                "original_segment_sha256": builder.sha256(Path(row["original_segment_path"])),
                "original_visual_family_id": visual_family_id(row["original_segment_path"]),
                "original_segment_id": row["segment_id"],
                "replacement_applied": row["replacement_context"] is not None,
                "replacement_context": row["replacement_context"],
                "duration_seconds": round(segment_duration, 6),
                "prepared_duration_seconds": round(raw_segment_duration, 6),
                "trimmed_by_body_target_seconds": round(raw_segment_duration - segment_duration, 6),
                "body_timeline_start_seconds": round(cursor, 6),
                "body_timeline_end_seconds": round(cursor + segment_duration, 6),
                "proof_timeline_start_seconds": round(proof_start, 6),
                "proof_timeline_end_seconds": round(proof_end, 6),
                "tail_signal_interruption_used": row["signal_context"] is not None,
            }
        )
        if row["signal_context"]:
            context = dict(row["signal_context"])
            context.update(
                {
                    "outgoing_segment_id": row["segment_id"],
                    "incoming_segment_id": row["incoming_segment_id"],
                    "proof_boundary_seconds": round(proof_end, 6),
                    "proof_signal_start_seconds": round(proof_end - SIGNAL_INTERRUPT_SECONDS, 6),
                    "proof_signal_center_seconds": round(proof_end - (SIGNAL_INTERRUPT_SECONDS / 2.0), 6),
                    "proof_signal_end_seconds": round(proof_end, 6),
                }
            )
            body_signal_boundaries.append(context)
        cursor += segment_duration

    return {
        "body_source_policy": "rebuilt_from_existing_pass01d_source_segments_with_signal_interruptions",
        "segment_count": len(segments),
        "segment_order_read": "pass_original_pass01d_order_preserved",
        "body_clip_motion_repairs": body_clip_motion_repairs,
        "body_clip_variance_repairs": body_clip_motion_repairs,
        "targeted_repair_clip_ids": sorted(BODY_REPAIR_SOURCES.keys()),
        "targeted_variance_repair_clip_ids": sorted(BODY_REPAIR_SOURCES.keys()),
        "only_targeted_body_clips_changed": True,
        "only_variance_and_freeze_repairs_changed": True,
        "body_segment_replacements_used": True,
        "body_signal_interruption_boundaries": body_signal_boundaries,
        "segments": segment_rows,
        "concat_list_path": str(concat_path),
        "untrimmed_clean_body_path": str(untrimmed_body_output),
        "untrimmed_clean_body_sha256": builder.sha256(untrimmed_body_output),
        "untrimmed_clean_body_duration_seconds": round(builder.duration(untrimmed_body_output), 6),
        "clean_body_path": str(body_output),
        "clean_body_sha256": builder.sha256(body_output),
        "clean_body_duration_seconds": round(builder.duration(body_output), 6),
        "body_target_reference_path": str(BODY_TARGET_REFERENCE),
        "body_target_reference_sha256": builder.sha256(BODY_TARGET_REFERENCE),
        "body_target_duration_seconds": round(body_target_duration, 6),
        "body_target_policy": "trim_rebuilt_segment_body_to_existing_pass01d_no_caption_proof_duration",
        "only_signal_interruptions_added": False,
        "body_clip_order_changed": False,
    }


def framehash_sample(
    video: Path,
    start_seconds: float,
    duration_seconds: float,
    output: Path,
    sample_rate_fps: int = 2,
) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start_seconds:.6f}",
            "-t",
            f"{duration_seconds:.6f}",
            "-i",
            str(video),
            "-an",
            "-vf",
            f"fps={sample_rate_fps},scale=180:320:force_original_aspect_ratio=increase,crop=180:320,format=yuv420p",
            "-f",
            "framemd5",
            str(output),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    hashes: list[str] = []
    for line in output.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        hashes.append(parts[-1])
    unique_hashes = sorted(set(hashes))
    return {
        "path": str(output),
        "sha256": builder.sha256(output),
        "start_seconds": round(start_seconds, 6),
        "duration_seconds": round(duration_seconds, 6),
        "sample_rate_fps": sample_rate_fps,
        "sample_count": len(hashes),
        "unique_hash_count": len(unique_hashes),
        "read": "pass" if len(unique_hashes) > 1 else "tighten",
    }


def visual_family_audit(body_context: dict[str, Any]) -> dict[str, Any]:
    segment_family_by_id = {
        segment["original_segment_id"]: segment["visual_family_id"]
        for segment in body_context["segments"]
    }
    reported_range_reads: list[dict[str, Any]] = []
    for reported_range in USER_REPORTED_REPEAT_RANGES:
        target_ids = reported_range["target_segment_ids"]
        blocked_family = reported_range["blocked_family_id"]
        observed = {
            segment_id: segment_family_by_id.get(segment_id, "missing")
            for segment_id in target_ids
        }
        blocked_hits = [
            segment_id for segment_id, family_id in observed.items()
            if family_id == blocked_family
        ]
        reported_range_reads.append(
            {
                **reported_range,
                "observed_visual_families": observed,
                "blocked_family_hits": blocked_hits,
                "read": "pass" if not blocked_hits else "tighten",
            }
        )

    public_audience_body_hits = [
        segment["original_segment_id"]
        for segment in body_context["segments"]
        if segment["visual_family_id"] == "public_ceremony_audience"
    ]
    bedside_repeat_targets = ["06", "07", "08", "10"]
    bedside_hits = [
        segment_id
        for segment_id in bedside_repeat_targets
        if segment_family_by_id.get(segment_id) == "bedside_doctor_over_patient"
    ]
    overall_read = (
        "pass"
        if all(row["read"] == "pass" for row in reported_range_reads)
        and not public_audience_body_hits
        and not bedside_hits
        else "tighten"
    )
    return {
        "reported_range_reads": reported_range_reads,
        "visual_family_by_segment_id": segment_family_by_id,
        "blocked_repeat_clusters": [
            {
                "cluster_id": "bedside_doctor_over_patient_middle_and_37s",
                "blocked_family_id": "bedside_doctor_over_patient",
                "segment_ids": bedside_repeat_targets,
                "blocked_hits": bedside_hits,
                "read": "pass" if not bedside_hits else "tighten",
            },
            {
                "cluster_id": "public_ceremony_audience_before_tail",
                "blocked_family_id": "public_ceremony_audience",
                "segment_ids": [segment["original_segment_id"] for segment in body_context["segments"]],
                "blocked_hits": public_audience_body_hits,
                "read": "pass" if not public_audience_body_hits else "tighten",
            },
        ],
        "reported_repeat_read": overall_read,
        "tail_reuse_read": "pass" if not public_audience_body_hits else "tighten",
    }


def historical_source_policy_context(body_context: dict[str, Any]) -> dict[str, Any]:
    allowlist_names = {path.name for path in PASS04_LIGHTBOX_ALLOWLIST.values()}
    blocked_names = {path.name for path in BLOCKED_HISTORICAL_ANACHRONISM_SOURCES}
    pass04_sources_used: list[dict[str, Any]] = []
    allowed_used: list[dict[str, Any]] = []
    blocked_hits: list[dict[str, Any]] = []

    for segment in body_context["segments"]:
        source = Path(segment["source_path"])
        if source.parent != PASS04_CANDIDATES_DIR and source.name not in allowlist_names and source.name not in blocked_names:
            continue
        row = {
            "segment_id": segment["original_segment_id"],
            "source_name": source.name,
            "source_path": str(source),
            "visual_family_id": segment["visual_family_id"],
        }
        pass04_sources_used.append(row)
        if source.name in allowlist_names:
            allowed_used.append(row)
        if source.name in blocked_names:
            blocked_hits.append(row)

    return {
        "scope": "body_replacement_sources_and_same_opening_tail",
        "rule": "from the pass-04 lightbox, only A/B are allowed; exterior, automobile, public-ceremony, skyline, facade, courtyard, memorial, and ward-depth lightbox shots are blocked",
        "pass04_lightbox_allowlist": {
            label: {
                "label": label,
                "source_path": str(path),
                "source_name": path.name,
                "sha256": builder.sha256(path),
                "use_policy": "allowed_but_not_required_due_low_motion_risk",
            }
            for label, path in PASS04_LIGHTBOX_ALLOWLIST.items()
        },
        "blocked_historical_anachronism_sources": [
            {
                "source_name": path.name,
                "blocked_reason": "non-allowlisted pass-04 lightbox source with exterior, automobile, public-ceremony, skyline, facade, courtyard, memorial, ward-depth, or modern-context risk",
            }
            for path in BLOCKED_HISTORICAL_ANACHRONISM_SOURCES
        ],
        "blocked_historical_anachronism_source_paths_withheld": True,
        "pass04_lightbox_sources_used": pass04_sources_used,
        "allowed_pass04_lightbox_sources_used": allowed_used,
        "blocked_historical_anachronism_hits": blocked_hits,
        "external_shots_removed": not blocked_hits,
        "automobiles_or_modern_context_read": "pass_review_required" if not blocked_hits else "tighten",
        "historical_period_read": "pass_review_required" if not blocked_hits else "tighten",
        "read": "pass" if not blocked_hits else "tighten",
    }


def main() -> None:
    require_inputs()
    stamp = builder.utc_stamp()
    latest_link = builder.OUTPUT_ROOT / "semmelweis_theme_intro_hook_latest"
    source_tighten_package = latest_link.resolve() if latest_link.exists() or latest_link.is_symlink() else None
    source_package_tighten_context = mark_source_package_tighten(source_tighten_package)
    root = builder.OUTPUT_ROOT / f"semmelweis_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    body_context = build_clean_body_from_segments(work)
    body_path = Path(body_context["clean_body_path"])
    prepared_tail_sequence_duration = (
        FINAL_DURATION_SECONDS
        - HOOK_DURATION_SECONDS
        - builder.duration(body_path)
    )
    if abs(prepared_tail_sequence_duration - TAIL_SEQUENCE_DURATION_SECONDS) > 0.05:
        raise RuntimeError(
            "Unexpected Semmelweis tail sequence duration: "
            f"{prepared_tail_sequence_duration:.6f}s vs expected {TAIL_SEQUENCE_DURATION_SECONDS:.6f}s"
        )
    pre_closing_insert_clean_path = work / "semmelweis_pre_closing_insert_doctor_bends_no_audio.mp4"
    pre_closing_insert_signal_path = work / "semmelweis_pre_closing_insert_doctor_bends_tail_signal_no_audio.mp4"
    final_tail_path = work / "semmelweis_opening_clip_return_final_tail_exact_no_audio.mp4"
    prepared_tail_path = work / "semmelweis_pre_closing_insert_plus_opening_clip_final_tail_no_audio.mp4"
    pre_closing_insert_context = normalize_source_span(
        PRE_CLOSING_INSERT_SOURCE,
        pre_closing_insert_clean_path,
        0.0,
        PRE_CLOSING_INSERT_DURATION_SECONDS,
    )
    pre_closing_insert_signal_context = apply_tail_signal_interruption(
        pre_closing_insert_clean_path,
        pre_closing_insert_signal_path,
        "pre_closing_insert_to_final_opening_clip_tail",
    )
    prepared_tail_context = normalize_source_span(
        TAIL_SOURCE,
        final_tail_path,
        TAIL_SOURCE_START_SECONDS,
        TAIL_SINGLE_PASS_DURATION_SECONDS,
    )
    prepared_tail_sequence_context = build_prepared_tail_sequence(
        pre_closing_insert_signal_path,
        final_tail_path,
        prepared_tail_path,
        prepared_tail_sequence_duration,
    )
    configure_semmelweis(body_path, prepared_tail_path, 0.0)

    hook_clip = work / "semmelweis_delivery_room_team_hook_no_audio_3s.mp4"
    hook_signal_clip = work / "semmelweis_delivery_room_team_hook_tail_signal_no_audio_3s.mp4"
    picture_bed = work / "picture_bed_semmelweis_hook_pass01d_body_tail_full_picture_crt_no_audio.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "semmelweis_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_semmelweis_theme_hook_first_10s.mp4"
    opening_strip = evidence / "opening_frame_strip.jpg"
    hook_source_strip = evidence / "hook_source_frame_strip.jpg"
    hook_body_signal_strip = evidence / "hook_body_signal_interruption_frame_strip.jpg"
    hook_body_seam_strip = evidence / "hook_body_seam_frame_strip.jpg"
    all_signal_boundaries_strip = evidence / "all_signal_interruption_boundaries_frame_strip.jpg"
    body_signal_boundaries_strip = evidence / "body_segment_signal_interruption_boundaries_frame_strip.jpg"
    body_variance_strip = evidence / "body_variance_contact_sheet_frame_strip.jpg"
    reported_middle_repeat_strip = evidence / "reported_repeat_20_30s_frame_strip.jpg"
    reported_37s_repeat_strip = evidence / "reported_repeat_37s_frame_strip.jpg"
    historical_accuracy_repair_strip = evidence / "historical_accuracy_repair_frame_strip.jpg"
    reported_tail_reuse_strip = evidence / "reported_tail_reuse_52_66s_frame_strip.jpg"
    opening_closing_same_clip_strip = evidence / "opening_closing_same_clip_frame_strip.jpg"
    pre_closing_insert_strip = evidence / "pre_closing_insert_frame_strip.jpg"
    insert_to_final_signal_strip = evidence / "insert_to_final_signal_interruption_frame_strip.jpg"
    final_same_opening_tail_strip = evidence / "final_same_opening_tail_frame_strip.jpg"
    signal_tail_outro_strip = evidence / "signal_tail_outro_handoff_frame_strip.jpg"
    tail_source_strip = evidence / "tail_source_frame_strip.jpg"
    repaired_body_motion_strip = evidence / "repaired_body_clip_motion_frame_strip.jpg"
    repaired_body_seams_strip = evidence / "repaired_body_clip_adjacent_seams_frame_strip.jpg"
    end_strip = evidence / "end_frame_strip.jpg"
    waveform = evidence / "first_10s_waveform.png"

    hook_context = builder.build_hook_clip(hook_clip)
    hook_signal_context = apply_tail_signal_interruption(hook_clip, hook_signal_clip, "hook_to_body_01")
    picture_bed_context = builder.build_picture_bed(hook_signal_clip, picture_bed)
    builder.build_audio_mix(audio_mix)
    builder.mux(picture_bed, audio_mix, proof)
    builder.extract_excerpt(builder.CURRENT_YOUTUBE_SHORT, 10.0, current_excerpt)
    builder.extract_excerpt(proof, 10.0, revised_excerpt)
    builder.build_comparison(current_excerpt, revised_excerpt, comparison)

    opening_frames = builder.build_frame_strip(
        proof,
        opening_strip,
        [0.0, 0.5, 1.0, 2.0, 2.75, 2.9, 3.0, 3.1],
    )
    hook_source_frames = builder.build_frame_strip(
        hook_clip,
        hook_source_strip,
        [0.0, 0.5, 1.0, 2.0, 2.8],
    )
    hook_body_signal_frames = builder.build_frame_strip(
        proof,
        hook_body_signal_strip,
        [2.60, 2.75, 2.875, 3.00, 3.10],
    )
    hook_body_seam_frames = builder.build_frame_strip(
        proof,
        hook_body_seam_strip,
        [2.70, 2.90, 3.00, 3.10, 3.30],
    )
    body_signal_boundary_times = [
        boundary["proof_signal_center_seconds"]
        for boundary in body_context["body_signal_interruption_boundaries"]
    ]
    signal_start_seconds = builder.HOOK_DURATION_SECONDS + picture_bed_context["body_duration_seconds"]
    tail_start_seconds = signal_start_seconds + picture_bed_context["signal_interruption_duration_seconds"]
    closing_tail_start_seconds = tail_start_seconds + PRE_CLOSING_INSERT_DURATION_SECONDS
    tail_signal_boundary = {
        "boundary_id": "body_17_to_tail",
        "outgoing_segment_id": "17",
        "incoming_segment_id": "pre_closing_insert",
        "proof_boundary_seconds": round(tail_start_seconds, 6),
        "proof_signal_start_seconds": round(signal_start_seconds, 6),
        "proof_signal_center_seconds": round(signal_start_seconds + (SIGNAL_INTERRUPT_SECONDS / 2.0), 6),
        "proof_signal_end_seconds": round(tail_start_seconds, 6),
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPT_SECONDS,
        "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
        "read": "pass_review_required",
    }
    insert_to_final_signal_boundary = {
        "boundary_id": "pre_closing_insert_to_final_opening_clip_tail",
        "outgoing_segment_id": "pre_closing_insert",
        "incoming_segment_id": "final_opening_clip_tail",
        "proof_boundary_seconds": round(closing_tail_start_seconds, 6),
        "proof_signal_start_seconds": round(closing_tail_start_seconds - SIGNAL_INTERRUPT_SECONDS, 6),
        "proof_signal_center_seconds": round(closing_tail_start_seconds - (SIGNAL_INTERRUPT_SECONDS / 2.0), 6),
        "proof_signal_end_seconds": round(closing_tail_start_seconds, 6),
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPT_SECONDS,
        "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
        "full_frame_static_replacement_used": False,
        "read": "pass_review_required",
    }
    signal_boundaries = [
        {
            **hook_signal_context,
            "outgoing_segment_id": "hook",
            "incoming_segment_id": "01",
            "proof_boundary_seconds": builder.HOOK_DURATION_SECONDS,
            "proof_signal_start_seconds": round(builder.HOOK_DURATION_SECONDS - SIGNAL_INTERRUPT_SECONDS, 6),
            "proof_signal_center_seconds": round(builder.HOOK_DURATION_SECONDS - (SIGNAL_INTERRUPT_SECONDS / 2.0), 6),
            "proof_signal_end_seconds": builder.HOOK_DURATION_SECONDS,
        },
        *body_context["body_signal_interruption_boundaries"],
        tail_signal_boundary,
        insert_to_final_signal_boundary,
    ]
    all_signal_boundary_frames = builder.build_frame_strip(
        proof,
        all_signal_boundaries_strip,
        [boundary["proof_signal_center_seconds"] for boundary in signal_boundaries],
    )
    body_signal_boundary_frames = builder.build_frame_strip(
        proof,
        body_signal_boundaries_strip,
        body_signal_boundary_times,
    )
    body_variance_times = [
        float(segment["proof_timeline_start_seconds"])
        + ((float(segment["proof_timeline_end_seconds"]) - float(segment["proof_timeline_start_seconds"])) / 2.0)
        for segment in body_context["segments"]
    ]
    body_variance_frames = builder.build_frame_strip(
        proof,
        body_variance_strip,
        [0.75, *body_variance_times, tail_start_seconds + 1.0, builder.FINAL_DURATION_SECONDS - 0.75],
    )
    reported_middle_repeat_frames = builder.build_frame_strip(
        proof,
        reported_middle_repeat_strip,
        [19.5, 20.0, 22.0, 24.0, 26.5, 29.0, 30.8],
    )
    reported_37s_repeat_frames = builder.build_frame_strip(
        proof,
        reported_37s_repeat_strip,
        [34.5, 36.0, 37.0, 38.25, 39.5],
    )
    historical_accuracy_repair_frames = builder.build_frame_strip(
        proof,
        historical_accuracy_repair_strip,
        [
            19.5,
            20.0,
            22.0,
            24.0,
            26.5,
            29.0,
            30.8,
            34.5,
            36.0,
            37.0,
            38.25,
            39.5,
            42.5,
            43.0,
            45.0,
            47.0,
            52.5,
            53.5,
            55.5,
        ],
    )
    reported_tail_reuse_frames = builder.build_frame_strip(
        proof,
        reported_tail_reuse_strip,
        [
            52.5,
            53.5,
            55.0,
            tail_start_seconds,
            tail_start_seconds + 1.0,
            closing_tail_start_seconds,
            closing_tail_start_seconds + 1.0,
            builder.FINAL_DURATION_SECONDS - 0.25,
        ],
    )
    opening_closing_same_clip_frames = builder.build_frame_strip(
        proof,
        opening_closing_same_clip_strip,
        [
            0.0,
            0.5,
            2.5,
            closing_tail_start_seconds,
            closing_tail_start_seconds + 0.5,
            builder.FINAL_DURATION_SECONDS - 1.0,
            builder.FINAL_DURATION_SECONDS - 0.25,
        ],
    )
    pre_closing_insert_frames = builder.build_frame_strip(
        proof,
        pre_closing_insert_strip,
        [
            tail_start_seconds,
            tail_start_seconds + 0.50,
            tail_start_seconds + 1.50,
            max(tail_start_seconds, closing_tail_start_seconds - 0.30),
        ],
    )
    insert_to_final_signal_frames = builder.build_frame_strip(
        proof,
        insert_to_final_signal_strip,
        [
            closing_tail_start_seconds - 0.35,
            closing_tail_start_seconds - 0.20,
            closing_tail_start_seconds - 0.10,
            closing_tail_start_seconds,
            closing_tail_start_seconds + 0.15,
            closing_tail_start_seconds + 0.35,
        ],
    )
    final_same_opening_tail_frames = builder.build_frame_strip(
        proof,
        final_same_opening_tail_strip,
        [
            closing_tail_start_seconds,
            closing_tail_start_seconds + 0.50,
            closing_tail_start_seconds + 1.50,
            builder.FINAL_DURATION_SECONDS - 0.25,
        ],
    )
    repaired_segments = [
        segment
        for segment in body_context["segments"]
        if segment.get("replacement_applied")
    ]
    repaired_body_times: list[float] = []
    repaired_body_seam_times: list[float] = []
    for segment in repaired_segments:
        start = float(segment["proof_timeline_start_seconds"])
        end = float(segment["proof_timeline_end_seconds"])
        repaired_body_times.extend(
            [
                max(0.0, start - 0.20),
                start,
                start + 0.75,
                start + ((end - start) / 2.0),
                max(start, end - 0.30),
                end,
                end + 0.20,
            ]
        )
        repaired_body_seam_times.extend(
            [
                max(0.0, start - 0.25),
                start,
                start + 0.25,
                max(start, end - 0.25),
                end,
                end + 0.25,
            ]
        )
    repaired_body_frames = builder.build_frame_strip(
        proof,
        repaired_body_motion_strip,
        sorted(set(round(value, 6) for value in repaired_body_times)),
    )
    repaired_body_seam_frames = builder.build_frame_strip(
        proof,
        repaired_body_seams_strip,
        sorted(set(round(value, 6) for value in repaired_body_seam_times)),
    )
    repaired_source_frames: dict[str, Any] = {}
    for repair in body_context["body_clip_motion_repairs"]:
        segment_id = repair["segment_id"]
        source = Path(repair["replacement_source_path"])
        source_duration = builder.duration(source)
        strip = evidence / "repaired_sources" / f"segment_{segment_id}_source_frame_strip.jpg"
        source_start = float(repair.get("replacement_source_start_seconds", 0.0))
        usable_duration = float(repair.get("usable_replacement_source_duration_seconds", source_duration - source_start))
        source_end = min(source_duration - 0.05, source_start + max(0.05, usable_duration) - 0.05)
        times = [
            source_start,
            min(source_end, source_start + 0.50),
            min(source_end, source_start + 1.00),
            min(source_end, source_start + (usable_duration / 2.0)),
            source_end,
        ]
        repaired_source_frames[segment_id] = {
            "source_path": str(source),
            "source_start_seconds": round(source_start, 6),
            "usable_source_duration_seconds": round(usable_duration, 6),
            "frame_strip_path": str(strip),
            "frames": builder.build_frame_strip(source, strip, sorted(set(round(value, 6) for value in times))),
            "frame_strip_sha256": builder.sha256(strip),
        }
    signal_tail_outro_frames = builder.build_frame_strip(
        proof,
        signal_tail_outro_strip,
        [
            signal_start_seconds - 0.50,
            signal_start_seconds - 0.20,
            signal_start_seconds,
            tail_start_seconds,
            tail_start_seconds + 0.50,
            closing_tail_start_seconds - 0.20,
            closing_tail_start_seconds,
            closing_tail_start_seconds + 0.50,
            builder.OUTRO_START_SECONDS,
            builder.FINAL_DURATION_SECONDS - 0.50,
        ],
    )
    tail_source_duration = builder.duration(TAIL_SOURCE)
    tail_source_unit_end = min(tail_source_duration - 0.05, TAIL_SOURCE_START_SECONDS + TAIL_SINGLE_PASS_DURATION_SECONDS - 0.05)
    tail_source_frame_times = [
        TAIL_SOURCE_START_SECONDS,
        min(tail_source_duration - 0.05, TAIL_SOURCE_START_SECONDS + 0.50),
        min(tail_source_duration - 0.05, TAIL_SOURCE_START_SECONDS + 1.00),
        min(tail_source_duration - 0.05, TAIL_SOURCE_START_SECONDS + 2.00),
        tail_source_unit_end,
    ]
    tail_source_frames = builder.build_frame_strip(
        TAIL_SOURCE,
        tail_source_strip,
        sorted(set(round(max(TAIL_SOURCE_START_SECONDS, value), 6) for value in tail_source_frame_times)),
    )
    tail_variance_repair = {
        "source_path": str(TAIL_SOURCE),
        "source_sha256": builder.sha256(TAIL_SOURCE),
        "source_start_seconds": TAIL_SOURCE_START_SECONDS,
        "duration_seconds": TAIL_SINGLE_PASS_DURATION_SECONDS,
        "prepared_tail_context": prepared_tail_context,
        "reason": "keep the final clip as one clean pass from the same delivery-room source clip used for the opening hook; the proof now inserts a separate clip before it so the full theme outro is not cut off",
        "normalization": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "cloned_frame_padding_used": False,
        "looped_source_span_used": False,
        "read": "pass_review_required",
    }
    pre_closing_insert = {
        "source_path": str(PRE_CLOSING_INSERT_SOURCE),
        "source_sha256": builder.sha256(PRE_CLOSING_INSERT_SOURCE),
        "source_start_seconds": 0.0,
        "duration_seconds": PRE_CLOSING_INSERT_DURATION_SECONDS,
        "proof_start_seconds": round(tail_start_seconds, 6),
        "proof_end_seconds": round(closing_tail_start_seconds, 6),
        "visual_family_id": visual_family_id(PRE_CLOSING_INSERT_SOURCE),
        "prepared_insert_context": pre_closing_insert_context,
        "prepared_insert_signal_context": pre_closing_insert_signal_context,
        "insert_to_final_signal_boundary": insert_to_final_signal_boundary,
        "reason": "unused pass-05 clinical/interior motion source inserted before the final same-opening delivery-room clip so the video covers the full theme outro",
        "normalization": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "cloned_frame_padding_used": False,
        "read": "pass_review_required",
    }
    end_frames = builder.build_frame_strip(
        proof,
        end_strip,
        [
            builder.FINAL_DURATION_SECONDS - 2.50,
            builder.FINAL_DURATION_SECONDS - 1.50,
            builder.FINAL_DURATION_SECONDS - 0.75,
            builder.FINAL_DURATION_SECONDS - 0.25,
        ],
    )
    builder.build_waveform(proof, waveform)
    freeze_evidence = builder.freeze_tail_evidence(proof)
    motion_evidence = {
        "hook_motion": framehash_sample(hook_clip, 0.0, builder.HOOK_DURATION_SECONDS, evidence / "hook_motion_framemd5.txt"),
        "hook_body_signal_interruption_motion": framehash_sample(
            proof,
            max(0.0, builder.HOOK_DURATION_SECONDS - SIGNAL_INTERRUPT_SECONDS),
            0.50,
            evidence / "hook_body_signal_interruption_motion_framemd5.txt",
            sample_rate_fps=12,
        ),
        "representative_body_signal_interruption_motion": framehash_sample(
            proof,
            max(0.0, body_signal_boundary_times[0] - 0.25),
            0.50,
            evidence / "representative_body_signal_interruption_motion_framemd5.txt",
            sample_rate_fps=12,
        ),
        "body_tail_signal_interruption_motion": framehash_sample(
            proof,
            signal_start_seconds,
            0.50,
            evidence / "body_tail_signal_interruption_motion_framemd5.txt",
            sample_rate_fps=12,
        ),
        "pre_closing_insert_motion": framehash_sample(
            proof,
            tail_start_seconds,
            PRE_CLOSING_INSERT_DURATION_SECONDS,
            evidence / "pre_closing_insert_motion_framemd5.txt",
        ),
        "insert_to_final_signal_interruption_motion": framehash_sample(
            proof,
            closing_tail_start_seconds - SIGNAL_INTERRUPT_SECONDS,
            0.50,
            evidence / "insert_to_final_signal_interruption_motion_framemd5.txt",
            sample_rate_fps=12,
        ),
        "tail_motion": framehash_sample(
            proof,
            closing_tail_start_seconds,
            TAIL_SINGLE_PASS_DURATION_SECONDS,
            evidence / "tail_motion_framemd5.txt",
        ),
        "tail_sequence_motion": framehash_sample(
            proof,
            tail_start_seconds,
            max(0.25, min(3.0, builder.FINAL_DURATION_SECONDS - tail_start_seconds)),
            evidence / "tail_sequence_motion_framemd5.txt",
        ),
    }
    repaired_motion_evidence: dict[str, Any] = {}
    for segment in repaired_segments:
        segment_id = segment["original_segment_id"]
        start = float(segment["proof_timeline_start_seconds"])
        duration = max(0.25, min(3.0, float(segment["proof_timeline_end_seconds"]) - start))
        repaired_motion_evidence[segment_id] = framehash_sample(
            proof,
            start,
            duration,
            evidence / f"body_segment_{segment_id}_repaired_motion_framemd5.txt",
            sample_rate_fps=4,
        )
    motion_evidence["body_clip_motion_repairs"] = repaired_motion_evidence

    signal_interruption_context = {
        "signal_interruptions_between_every_clip": True,
        "signal_interruption_boundary_count": len(signal_boundaries),
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPT_SECONDS,
        "signal_interruption_timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
        "signal_interruption_profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
        "signal_interruption_boundaries": signal_boundaries,
    }
    family_audit = visual_family_audit(body_context)
    historical_policy = historical_source_policy_context(body_context)

    manifest = {
        "schema_version": "1.0",
        "stage": "first-second hook review",
        "prototype_id": f"semmelweis_theme_intro_hook_{stamp}",
        "local_only_no_youtube_action": True,
        "no_youtube_action": True,
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "display_name": DISPLAY_NAME,
        "source_tighten_package_path": str(source_tighten_package) if source_tighten_package else None,
        "source_package_tighten_context": source_package_tighten_context,
        "current_latest_publish_mp4_path": str(builder.CURRENT_YOUTUBE_SHORT),
        "current_latest_publish_mp4_sha256": builder.sha256(builder.CURRENT_YOUTUBE_SHORT),
        "proof_path": str(proof),
        "proof_sha256": builder.sha256(proof),
        "comparison_path": str(comparison),
        "comparison_sha256": builder.sha256(comparison),
        "opening_frame_strip_path": str(opening_strip),
        "opening_frame_strip_sha256": builder.sha256(opening_strip),
        "hook_source_frame_strip_path": str(hook_source_strip),
        "hook_source_frame_strip_sha256": builder.sha256(hook_source_strip),
        "hook_body_signal_interruption_frame_strip_path": str(hook_body_signal_strip),
        "hook_body_signal_interruption_frame_strip_sha256": builder.sha256(hook_body_signal_strip),
        "hook_body_seam_frame_strip_path": str(hook_body_seam_strip),
        "hook_body_seam_frame_strip_sha256": builder.sha256(hook_body_seam_strip),
        "all_signal_interruption_boundaries_frame_strip_path": str(all_signal_boundaries_strip),
        "all_signal_interruption_boundaries_frame_strip_sha256": builder.sha256(all_signal_boundaries_strip),
        "body_segment_signal_interruption_boundaries_frame_strip_path": str(body_signal_boundaries_strip),
        "body_segment_signal_interruption_boundaries_frame_strip_sha256": builder.sha256(body_signal_boundaries_strip),
        "body_variance_contact_sheet_frame_strip_path": str(body_variance_strip),
        "body_variance_contact_sheet_frame_strip_sha256": builder.sha256(body_variance_strip),
        "reported_repeat_20_30s_frame_strip_path": str(reported_middle_repeat_strip),
        "reported_repeat_20_30s_frame_strip_sha256": builder.sha256(reported_middle_repeat_strip),
        "reported_repeat_37s_frame_strip_path": str(reported_37s_repeat_strip),
        "reported_repeat_37s_frame_strip_sha256": builder.sha256(reported_37s_repeat_strip),
        "historical_accuracy_repair_frame_strip_path": str(historical_accuracy_repair_strip),
        "historical_accuracy_repair_frame_strip_sha256": builder.sha256(historical_accuracy_repair_strip),
        "reported_tail_reuse_52_66s_frame_strip_path": str(reported_tail_reuse_strip),
        "reported_tail_reuse_52_66s_frame_strip_sha256": builder.sha256(reported_tail_reuse_strip),
        "opening_closing_same_clip_frame_strip_path": str(opening_closing_same_clip_strip),
        "opening_closing_same_clip_frame_strip_sha256": builder.sha256(opening_closing_same_clip_strip),
        "pre_closing_insert_frame_strip_path": str(pre_closing_insert_strip),
        "pre_closing_insert_frame_strip_sha256": builder.sha256(pre_closing_insert_strip),
        "insert_to_final_signal_interruption_frame_strip_path": str(insert_to_final_signal_strip),
        "insert_to_final_signal_interruption_frame_strip_sha256": builder.sha256(insert_to_final_signal_strip),
        "final_same_opening_tail_frame_strip_path": str(final_same_opening_tail_strip),
        "final_same_opening_tail_frame_strip_sha256": builder.sha256(final_same_opening_tail_strip),
        "repaired_body_clip_motion_frame_strip_path": str(repaired_body_motion_strip),
        "repaired_body_clip_motion_frame_strip_sha256": builder.sha256(repaired_body_motion_strip),
        "repaired_body_clip_adjacent_seams_frame_strip_path": str(repaired_body_seams_strip),
        "repaired_body_clip_adjacent_seams_frame_strip_sha256": builder.sha256(repaired_body_seams_strip),
        "repaired_source_frame_strips": repaired_source_frames,
        "signal_tail_outro_handoff_frame_strip_path": str(signal_tail_outro_strip),
        "signal_tail_outro_handoff_frame_strip_sha256": builder.sha256(signal_tail_outro_strip),
        "tail_source_frame_strip_path": str(tail_source_strip),
        "tail_source_frame_strip_sha256": builder.sha256(tail_source_strip),
        "end_frame_strip_path": str(end_strip),
        "end_frame_strip_sha256": builder.sha256(end_strip),
        "waveform_path": str(waveform),
        "waveform_sha256": builder.sha256(waveform),
        "visual_extension_mode": picture_bed_context["visual_extension_mode"],
        "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
        "source_motion_tail": picture_bed_context["source_motion_tail"],
        "signal_interruption": picture_bed_context["signal_interruption"],
        **signal_interruption_context,
        "full_picture_crt_texture": picture_bed_context["full_picture_crt_texture"],
        "full_picture_crt_scope": picture_bed_context["full_picture_crt_scope"],
        "segment_crt_passes_used": picture_bed_context["segment_crt_passes_used"],
        "tail_segment_crt_pass_used": picture_bed_context["tail_segment_crt_pass_used"],
        "caption_layer_policy": "local_review_no_final_caption_rebuild",
        "paper_architecture_visual_style_read": "pass_not_used",
        "opening_delivery_room_hook_read": "pass_review_required",
        "opening_subject_event_presence_read": "pass_review_required",
        "hook_body_signal_interruption_read": "pass_review_required",
        "body_segment_signal_interruption_read": "pass_review_required",
        "body_tail_signal_interruption_read": "pass_review_required",
        "insert_to_final_signal_interruption_read": "pass_review_required",
        "body_clip_motion_repairs": body_context["body_clip_motion_repairs"],
        "body_clip_historical_accuracy_repairs": [
            repair
            for repair in body_context["body_clip_motion_repairs"]
            if repair["segment_id"] in ["06", "07", "08", "10", "12", "13", "15"]
        ],
        "targeted_repair_clip_ids": body_context["targeted_repair_clip_ids"],
        "only_targeted_body_clips_changed": body_context["only_targeted_body_clips_changed"],
        "frozen_body_clip_repair_read": "pass_review_required",
        "tail_motion_read": motion_evidence["tail_motion"]["read"],
        "source_family_dedupe_policy": {
            "scope": "body_and_tail_review_proof",
            "rule": "no exact or obvious same-source-family repeats in the body; the opening delivery-room clip is allowed to return only as the ending tail",
            "known_repeat_clusters_tightened": [
                "05~06",
                "03/04",
                "09/12",
                "12/13/15",
                "20-30s/37s_bedside_doctor_over_patient",
                "pre_tail_public_audience_reuse",
                "tail_empty_room_hold",
            ],
            "hospital_bedside_exception": "allowed only when composition and action are clearly different; opening source family may recur only as the closing tail",
            "read": "pass_review_required",
        },
        "user_reported_repeat_ranges": USER_REPORTED_REPEAT_RANGES,
        "visual_family_id_by_segment_id": family_audit["visual_family_by_segment_id"],
        "blocked_repeat_clusters": family_audit["blocked_repeat_clusters"],
        "reported_repeat_repair_clip_ids": ["06", "07", "08", "10", "15"],
        "historical_accuracy_source_policy": historical_policy,
        "pass04_lightbox_allowlist": historical_policy["pass04_lightbox_allowlist"],
        "pass04_lightbox_sources_used": historical_policy["pass04_lightbox_sources_used"],
        "allowed_pass04_lightbox_sources_used": historical_policy["allowed_pass04_lightbox_sources_used"],
        "blocked_historical_anachronism_sources": historical_policy["blocked_historical_anachronism_sources"],
        "blocked_historical_anachronism_source_paths_withheld": historical_policy[
            "blocked_historical_anachronism_source_paths_withheld"
        ],
        "blocked_historical_anachronism_hits": historical_policy["blocked_historical_anachronism_hits"],
        "external_shots_removed": historical_policy["external_shots_removed"],
        "automobiles_or_modern_context_read": historical_policy["automobiles_or_modern_context_read"],
        "historical_period_read": historical_policy["historical_period_read"],
        "historical_accuracy_source_policy_read": historical_policy["read"],
        "reported_repeat_visual_family_audit": family_audit,
        "reported_repeat_read": family_audit["reported_repeat_read"],
        "tail_reuse_read": family_audit["tail_reuse_read"],
        "body_clip_variance_repairs": body_context["body_clip_variance_repairs"],
        "targeted_variance_repair_clip_ids": body_context["targeted_variance_repair_clip_ids"],
        "music_outro_completion_repair": {
            "problem": "prior local proof ended before the full theme outro completed",
            "previous_final_duration_seconds": 62.766667,
            "outro_start_seconds": OUTRO_START_SECONDS,
            "theme_outro_duration_seconds": round(builder.duration(builder.THEME_OUTRO), 6),
            "corrected_final_duration_seconds": FINAL_DURATION_SECONDS,
            "added_duration_seconds": PRE_CLOSING_INSERT_DURATION_SECONDS,
            "strategy": "insert one pass-05 clinical/interior motion clip immediately before the final same-opening delivery-room clip",
            "read": "pass_review_required",
        },
        "pre_closing_insert": pre_closing_insert,
        "insert_before_final_clip_read": "pass_review_required",
        "theme_outro_full_duration_preserved": True,
        "theme_outro_expected_end_seconds": round(OUTRO_START_SECONDS + builder.duration(builder.THEME_OUTRO), 6),
        "prepared_tail_sequence_context": prepared_tail_sequence_context,
        "tail_variance_repair": tail_variance_repair,
        "opening_closing_source_path_match": str(HOOK_SOURCE) == str(TAIL_SOURCE),
        "closing_returns_to_opening_clip": True,
        "closing_tail_source_path": str(TAIL_SOURCE),
        "closing_tail_source_start_seconds": TAIL_SOURCE_START_SECONDS,
        "closing_tail_start_seconds": round(closing_tail_start_seconds, 6),
        "closing_tail_duration_seconds": TAIL_SINGLE_PASS_DURATION_SECONDS,
        "closing_tail_retime_used": prepared_tail_context.get("subtle_retime_used", False),
        "closing_tail_retime_factor": prepared_tail_context.get("retime_factor", 1.0),
        "closing_tail_looped_source_span_used": prepared_tail_context.get("looped_source_span_used", False),
        "closing_tail_single_pass_duration_seconds": TAIL_SINGLE_PASS_DURATION_SECONDS,
        "extra_closing_clip_repeats_removed": True,
        "overall_duration_shortened_for_single_tail_pass": False,
        "overall_duration_extended_for_full_outro": True,
        "closing_ends_on_opening_clip_read": "pass_review_required",
        "repeat_clip_read": "pass_review_required",
        "no_repeat_clip_read": "pass_review_required",
        "still_frozen_clip_read": "pass_review_required",
        "only_variance_and_freeze_repairs_changed": body_context["only_variance_and_freeze_repairs_changed"],
        "full_picture_crt_continuity_read": "pass_review_required",
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "body_trimmed_for_tail_motion_seconds": picture_bed_context["body_trimmed_for_tail_motion_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "tail_start_seconds": round(tail_start_seconds, 6),
        "tail_sequence_duration_seconds": TAIL_SEQUENCE_DURATION_SECONDS,
        "pass01d_clean_body_context": body_context,
        "visual_strategy": {
            "hook_visual": "doctor-at-bedside delivery-room source clip opens the proof before narration",
            "hook_source_path": str(builder.NO_CAPTION_PICTURE),
            "hook_source_start_seconds": builder.HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": builder.HOOK_DURATION_SECONDS,
            "hook_selection_reason": "opens immediately on an episode-specific doctor/patient event instead of a dark architectural frame or the current first body shot",
            "body_after_hook": "existing pass-01d Semmelweis body order preserved, rebuilt from clean no-audio source segments",
            "body_source_path": str(builder.BODY_CAPTIONED_NO_AUDIO),
            "tail_visual": "one pass-05 clinical/interior insert leads into the same delivery-room source clip used for the opening hook, preserving the full theme outro without repeating the final clip",
            "pre_closing_insert_source_path": str(PRE_CLOSING_INSERT_SOURCE),
            "pre_closing_insert_duration_seconds": PRE_CLOSING_INSERT_DURATION_SECONDS,
            "tail_source_path": str(TAIL_SOURCE),
            "tail_source_start_seconds": TAIL_SOURCE_START_SECONDS,
            "closing_tail_start_seconds": round(closing_tail_start_seconds, 6),
            "opening_closing_source_path_match": str(HOOK_SOURCE) == str(TAIL_SOURCE),
            "full_picture_crt_scope": picture_bed_context["full_picture_crt_scope"],
            "segment_crt_passes_used": picture_bed_context["segment_crt_passes_used"],
            "caption_layer_policy": "local_review_no_final_caption_rebuild",
        },
        "music_strategy": {
            "full_theme_intro_path": str(builder.THEME_FULL),
            "full_theme_intro_sha256": builder.sha256(builder.THEME_FULL),
            "theme_intro_start_seconds": 0.0,
            "theme_intro_duration_seconds": builder.THEME_INTRO_SECONDS,
            "theme_intro_volume": builder.INTRO_VOLUME,
            "loop_path": str(builder.THEME_LOOP_60),
            "loop_sha256": builder.sha256(builder.THEME_LOOP_60),
            "loop_start_seconds": builder.LOOP_START_SECONDS,
            "loop_crossfade_seconds": builder.LOOP_CROSSFADE_SECONDS,
            "loop_volume_under_voice": builder.LOOP_VOLUME,
            "outro_path": str(builder.THEME_OUTRO),
            "outro_sha256": builder.sha256(builder.THEME_OUTRO),
            "outro_start_seconds": round(builder.OUTRO_START_SECONDS, 6),
            "outro_volume": builder.OUTRO_VOLUME,
            "limiter": "post-mix volume=0.62, alimiter=limit=0.62:level=false",
        },
        "voice_strategy": {
            "voice_wav_path": str(builder.VOICE_WAV),
            "voice_wav_sha256": builder.sha256(builder.VOICE_WAV),
            "voice_delay_seconds": builder.VOICE_DELAY_SECONDS,
            "voice_volume": builder.VOICE_VOLUME,
            "voice_last_audible_seconds_source": builder.VOICE_LAST_AUDIBLE_SECONDS,
        },
        "media_summary": builder.media_summary(proof),
        "audio_evidence": {
            "first_3s": builder.audio_metrics(proof, 3.0),
            "first_10s": builder.audio_metrics(proof, 10.0),
            "full_proof": builder.audio_metrics(proof, builder.FINAL_DURATION_SECONDS),
        },
        "motion_evidence": motion_evidence,
        "frame_samples": {
            "opening": opening_frames,
            "hook_source": hook_source_frames,
            "hook_body_signal_interruption": hook_body_signal_frames,
            "hook_body_seam": hook_body_seam_frames,
            "all_signal_interruption_boundaries": all_signal_boundary_frames,
            "body_segment_signal_interruption_boundaries": body_signal_boundary_frames,
            "body_variance_contact_sheet": body_variance_frames,
            "reported_repeat_20_30s": reported_middle_repeat_frames,
            "reported_repeat_37s": reported_37s_repeat_frames,
            "historical_accuracy_repair": historical_accuracy_repair_frames,
            "reported_tail_reuse_52_66s": reported_tail_reuse_frames,
            "opening_closing_same_clip": opening_closing_same_clip_frames,
            "pre_closing_insert": pre_closing_insert_frames,
            "insert_to_final_signal_interruption": insert_to_final_signal_frames,
            "final_same_opening_tail": final_same_opening_tail_frames,
            "repaired_body_clip_motion": repaired_body_frames,
            "repaired_body_clip_adjacent_seams": repaired_body_seam_frames,
            "repaired_source_clips": repaired_source_frames,
            "signal_tail_outro_handoff": signal_tail_outro_frames,
            "tail_source": tail_source_frames,
            "end": end_frames,
        },
        "review_request": "Judge whether the pre-closing pass-05 insert lets the video run through the full theme outro while preserving the historical-accuracy repairs, delivery-room hook, same-opening final clip, signal rhythm, CRT continuity, and local-only proof boundary.",
        "human_review_disposition": "keep|tighten|reject",
    }
    manifest_path = root / "semmelweis_theme_intro_hook_manifest.json"
    builder.write_json(manifest_path, manifest)

    note = f"""# Semmelweis Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `opening_frame_strip_path`: `{opening_strip}`
- `hook_source_frame_strip_path`: `{hook_source_strip}`
- `hook_body_signal_interruption_frame_strip_path`: `{hook_body_signal_strip}`
- `hook_body_seam_frame_strip_path`: `{hook_body_seam_strip}`
- `all_signal_interruption_boundaries_frame_strip_path`: `{all_signal_boundaries_strip}`
- `body_segment_signal_interruption_boundaries_frame_strip_path`: `{body_signal_boundaries_strip}`
- `body_variance_contact_sheet_frame_strip_path`: `{body_variance_strip}`
- `reported_repeat_20_30s_frame_strip_path`: `{reported_middle_repeat_strip}`
- `reported_repeat_37s_frame_strip_path`: `{reported_37s_repeat_strip}`
- `historical_accuracy_repair_frame_strip_path`: `{historical_accuracy_repair_strip}`
- `reported_tail_reuse_52_66s_frame_strip_path`: `{reported_tail_reuse_strip}`
- `opening_closing_same_clip_frame_strip_path`: `{opening_closing_same_clip_strip}`
- `pre_closing_insert_frame_strip_path`: `{pre_closing_insert_strip}`
- `insert_to_final_signal_interruption_frame_strip_path`: `{insert_to_final_signal_strip}`
- `final_same_opening_tail_frame_strip_path`: `{final_same_opening_tail_strip}`
- `repaired_body_clip_motion_frame_strip_path`: `{repaired_body_motion_strip}`
- `repaired_body_clip_adjacent_seams_frame_strip_path`: `{repaired_body_seams_strip}`
- `signal_tail_outro_handoff_frame_strip_path`: `{signal_tail_outro_strip}`
- `tail_source_frame_strip_path`: `{tail_source_strip}`
- `end_frame_strip_path`: `{end_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{builder.HOOK_DURATION_SECONDS:.1f}s` opens on the delivery-room doctor/patient source clip, starting at source `{builder.HOOK_SOURCE_START_SECONDS:.2f}s`.
- The full theme song starts from `0.00`, then crossfades into the registered loop from `{builder.LOOP_START_SECONDS:.2f}s` to `{builder.LOOP_START_SECONDS + builder.LOOP_CROSSFADE_SECONDS:.2f}s`; the outro starts at `{builder.OUTRO_START_SECONDS:.2f}s` and the proof now runs through the full outro.
- The approved Semmelweis voice starts after the hook at `{builder.VOICE_DELAY_SECONDS:.2f}s`; final captions remain deferred.
- The pass-01d body is rebuilt from the existing clean no-audio source segments, preserving segment order.
- Body slots `04`, `05`, `06`, `07`, `08`, `10`, `12`, `13`, and `15` are replaced with existing Semmelweis motion-lineage clips because the previous proof repeated the same visual families.
- The historical-accuracy repair blocks all non-allowlisted pass-04 lightbox shots; only A (`p04_04_autopsy_room_source_no_audio.mp4`) and B (`p04_06_inserm_basin_disinfection_no_audio.mp4`) remain allowlisted, and neither is forced into this proof.
- Body slots `06`, `07`, `08`, `10`, `12`, `13`, and `15` now use pass-05 clinical/interior motion-lineage clips instead of exterior, facade, courtyard, memorial, skyline, public-ceremony, ward-depth, or other modern-context pass-04 shots.
- The user-reported `20-30s` and `37s` bedside repeat cluster is blocked from using `bedside_doctor_over_patient`.
- The user-reported pre-tail audience repeat is blocked from using `public_ceremony_audience` before the tail.
- Each replacement is normalized to the original slot duration, no audio, full-bleed `1080x1920 @ 30fps`; cloned-frame padding is not used.
- The existing `{SIGNAL_INTERRUPT_SECONDS:.2f}s` analog signal interruption appears at every clip boundary by replacing the outgoing clip tail, not adding runtime.
- Signal boundaries are applied at hook -> segment `01`, all body segment boundaries, and segment `17` -> tail.
- One continuous full-picture CRT pass is applied after hook/body/tail assembly.
- A new pass-05 clinical/interior insert (`{PRE_CLOSING_INSERT_SOURCE.name}`) runs for `{PRE_CLOSING_INSERT_DURATION_SECONDS:.6f}s` immediately before the final clip so the video no longer cuts off the theme outro.
- The insert has its own `{SIGNAL_INTERRUPT_SECONDS:.2f}s` signal-interruption tail before the final clip.
- The ending still returns to the same delivery-room source clip that opens the proof, prepared from source `{TAIL_SOURCE_START_SECONDS:.2f}s` as one clean `{TAIL_SINGLE_PASS_DURATION_SECONDS:.2f}s` moving pass; no looping or repeated tail span is used.
- `opening_closing_source_path_match`: `{str(HOOK_SOURCE) == str(TAIL_SOURCE)}`
- `closing_tail_looped_source_span_used`: `{prepared_tail_context.get("looped_source_span_used", False)}`
- `extra_closing_clip_repeats_removed`: `true`
- `final_duration_seconds`: `{builder.FINAL_DURATION_SECONDS:.6f}`
- `theme_outro_expected_end_seconds`: `{OUTRO_START_SECONDS + builder.duration(builder.THEME_OUTRO):.6f}`
- `closing_tail_start_seconds`: `{closing_tail_start_seconds:.6f}`
- `closing_ends_on_opening_clip_read`: `pass_review_required`
- `signal_interruption_boundary_count`: `{len(signal_boundaries)}`
- `targeted_repair_clip_ids`: `{body_context["targeted_repair_clip_ids"]}`
- `targeted_variance_repair_clip_ids`: `{body_context["targeted_variance_repair_clip_ids"]}`
- `reported_repeat_repair_clip_ids`: `["06", "07", "08", "10", "15"]`
- `pass04_lightbox_sources_used`: `{historical_policy["pass04_lightbox_sources_used"]}`
- `external_shots_removed`: `{historical_policy["external_shots_removed"]}`
- `automobiles_or_modern_context_read`: `{historical_policy["automobiles_or_modern_context_read"]}`
- `historical_period_read`: `{historical_policy["historical_period_read"]}`
- `reported_repeat_read`: `{family_audit["reported_repeat_read"]}`
- `tail_reuse_read`: `{family_audit["tail_reuse_read"]}`
- `repeat_clip_read`: `pass_review_required`
- `still_frozen_clip_read`: `pass_review_required`
- `tail_motion_read`: `{motion_evidence["tail_motion"]["read"]}`
- `pre_closing_insert_motion_read`: `{motion_evidence["pre_closing_insert_motion"]["read"]}`
- `theme_outro_full_duration_preserved`: `true`
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`

## Review Read

Mark this `keep`, `tighten`, or `reject`.

- `keep`: the repaired body slots and tail no longer read as repeated or still/frozen, and the hook, signal rhythm, CRT, audio, and source-motion tail still hold.
- `tighten`: the targeted repairs help, but one repaired slot, adjacent seam, repeat cluster, tail span, signal density, or audio balance needs adjustment.
- `reject`: this is less effective than the previous Semmelweis opening.
"""
    builder.write_text(root / "review_note.md", note)

    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
