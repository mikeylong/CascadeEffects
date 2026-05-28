#!/usr/bin/env python3
"""Build a local Therac-25 proof with strongest clinical scene plus theme-intro music."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any


BASE_SCRIPT = Path("/Users/mike/Agents_CascadeEffects/scripts/build_challenger_explosion_theme_intro_hook_proof.py")
spec = importlib.util.spec_from_file_location("theme_hook_builder", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to import {BASE_SCRIPT}")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


VIZ_SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1"
)
PASS28_SEGMENTS_DIR = VIZ_SHORT_ROOT / "motion_video_proof/pass_28_final_tail_repair/segments"
P13_LOCKED_CLIPS_DIR = VIZ_SHORT_ROOT / "visual_research/image_motion_source_pool_lock_pass_13/locked_clips"
BODY_REPAIR_SOURCES = {
    "03_edl_03_impossible_repeat_hold": {
        "source_path": P13_LOCKED_CLIPS_DIR
        / "p13_p01__archival_patient_beam_alignment__WiJP4P9b1ow__tail_safe_no_audio.mp4",
        "source_asset_id": "P13_P01",
        "source_family": "existing_pass13_locked_motion_lineage",
        "source_offset_seconds": 0.0,
        "repair_mode": "existing_locked_motion_lineage_replacement",
    },
    "04_edl_04_controls_take_over_hold": {
        "source_path": P13_LOCKED_CLIPS_DIR
        / "p13_s01__archival_control_console_gauges__RJcbDmom4BQ__tail_safe_no_audio.mp4",
        "source_asset_id": "P13_S01",
        "source_family": "existing_pass13_locked_motion_lineage",
        "source_offset_seconds": 0.0,
        "repair_mode": "existing_locked_motion_lineage_replacement",
    },
}


def configure_therac() -> None:
    short_root = Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1")
    latest_publish = short_root / "publish/youtube_20260429T002638Z_pass02_1980s_texture"
    clean_motion_source = Path(
        "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/"
        "motion_video_proof/pass_28_final_tail_repair/"
        "therac25_motion_video_proof_pass_28_tail_repair_motion_only_no_audio.mp4"
    )
    builder.SHORT_ROOT = short_root
    builder.LATEST_PUBLISH_DIR = latest_publish
    builder.CURRENT_YOUTUBE_SHORT = latest_publish / "therac25_software_safety_youtube_short.mp4"
    builder.BODY_CAPTIONED_NO_AUDIO = clean_motion_source
    builder.NO_CAPTION_PICTURE = clean_motion_source
    builder.VOICE_WAV = short_root / "final/therac_short_scoped_v1.wav"
    builder.HOOK_SOURCE_START_SECONDS = 39.0
    builder.HOOK_DURATION_SECONDS = 3.0
    builder.THEME_INTRO_SECONDS = 3.0
    builder.LOOP_START_SECONDS = 2.25
    builder.LOOP_CROSSFADE_SECONDS = 0.75
    builder.VOICE_DELAY_SECONDS = 3.0
    builder.VOICE_LAST_AUDIBLE_SECONDS = 56.38
    builder.OUTRO_START_SECONDS = builder.VOICE_DELAY_SECONDS + builder.VOICE_LAST_AUDIBLE_SECONDS + 0.10
    builder.FINAL_DURATION_SECONDS = builder.OUTRO_START_SECONDS + 6.98
    builder.HOOK_CRT_TEXTURE = None
    builder.FULL_PICTURE_CRT_TEXTURE = {
        "profile_id": "era_1980s_broadcast_crt_v1",
        "intensity": "visible_but_premium",
        "purpose": "apply one continuous CRT/analog texture over the assembled Therac hook, body, and tail proof",
        "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
        "scanline_strength_variant_id": "max_visible_bars_y24_p8",
        "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
    }
    builder.SOURCE_MOTION_TAIL = {
        "path": Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/"
            "motion_video_proof/pass_28_final_tail_repair/source_tail_scout/"
            "wijp4p9b1ow_176_193_tail_scout_no_audio.mp4"
        ),
        "start_seconds": 8.10,
        "replace_body_after_seconds": builder.duration(builder.CURRENT_YOUTUBE_SHORT),
        "continuation_source_start_seconds": 8.10,
        "description": "moving no-audio Therac-25 patient/machine tail scout continuation source",
        "house_crt_tail_texture": None,
    }


def repair_key_for_segment(segment_path: Path) -> str | None:
    for repair_key in BODY_REPAIR_SOURCES:
        if segment_path.name.startswith(f"{repair_key}__"):
            return repair_key
    return None


def render_replacement_segment(source: Path, target_duration: float, output: Path, source_offset_seconds: float) -> None:
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
            "-vf",
            (
                f"trim=start={source_offset_seconds:.6f}:duration={target_duration:.6f},setpts=PTS-STARTPTS,"
                "scale=720:1280:force_original_aspect_ratio=increase,"
                "crop=720:1280,setsar=1,fps=30,format=yuv420p"
            ),
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


def build_repaired_body(work: Path) -> dict[str, Any]:
    segments = sorted(PASS28_SEGMENTS_DIR.glob("*.mp4"))
    if len(segments) != 17:
        raise RuntimeError(f"Expected 17 pass-28 body segments, found {len(segments)} in {PASS28_SEGMENTS_DIR}")

    repaired_segments_dir = work / "targeted_body_motion_repair_segments"
    repaired_body = work / "therac_targeted_motion_repaired_body_no_audio.mp4"
    concat_path = work / "concat_therac_targeted_motion_repaired_body.txt"
    body_clip_motion_repairs: list[dict[str, Any]] = []
    concat_segments: list[Path] = []
    body_cursor = 0.0

    for segment in segments:
        target_duration = builder.duration(segment)
        repair_key = repair_key_for_segment(segment)
        if repair_key:
            source_config = BODY_REPAIR_SOURCES[repair_key]
            source = Path(source_config["source_path"])
            source_offset_seconds = float(source_config["source_offset_seconds"])
            if not source.exists():
                raise FileNotFoundError(f"Repair source does not exist: {source}")
            if builder.duration(source) - source_offset_seconds + (1.0 / builder.FPS) < target_duration:
                raise RuntimeError(
                    f"Repair source {source} is shorter than target slot {segment}: "
                    f"{builder.duration(source) - source_offset_seconds:.3f}s < {target_duration:.3f}s"
                )
            repaired_segment = repaired_segments_dir / segment.name.replace("__proof_pass28", "__targeted_motion_repair")
            render_replacement_segment(source, target_duration, repaired_segment, source_offset_seconds)
            concat_segments.append(repaired_segment)
            body_clip_motion_repairs.append(
                {
                    "clip_id": repair_key,
                    "original_segment_path": str(segment),
                    "original_segment_sha256": builder.sha256(segment),
                    "replacement_source_path": str(source),
                    "replacement_source_sha256": builder.sha256(source),
                    "replacement_source_family": source_config["source_family"],
                    "source_asset_id": source_config["source_asset_id"],
                    "source_offset_seconds": source_offset_seconds,
                    "normalized_replacement_path": str(repaired_segment),
                    "normalized_replacement_sha256": builder.sha256(repaired_segment),
                    "target_slot_duration_seconds": round(target_duration, 6),
                    "body_timeline_start_seconds": round(body_cursor, 6),
                    "body_timeline_end_seconds": round(body_cursor + target_duration, 6),
                    "proof_timeline_start_seconds": round(builder.HOOK_DURATION_SECONDS + body_cursor, 6),
                    "proof_timeline_end_seconds": round(builder.HOOK_DURATION_SECONDS + body_cursor + target_duration, 6),
                    "repair_mode": source_config["repair_mode"],
                    "regression_repair_source_policy": "existing_motion_lineage_only",
                    "pass01_replacement_used": False,
                    "audio_removed": True,
                    "fps": 30,
                    "resolution": "720x1280",
                }
            )
        else:
            concat_segments.append(segment)
        body_cursor += target_duration

    builder.write_text(concat_path, "".join(f"file '{path}'\n" for path in concat_segments))
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
            str(repaired_body),
        ]
    )

    return {
        "repaired_body_path": repaired_body,
        "repaired_body_sha256": builder.sha256(repaired_body),
        "repaired_body_duration_seconds": round(builder.duration(repaired_body), 6),
        "source_segments_dir": str(PASS28_SEGMENTS_DIR),
        "concat_path": str(concat_path),
        "targeted_repair_clip_ids": list(BODY_REPAIR_SOURCES.keys()),
        "body_clip_motion_repairs": body_clip_motion_repairs,
        "only_targeted_body_clips_changed": True,
        "frozen_body_clip_repair_read": "pass_review_required",
        "regression_repair_source_policy": "existing_motion_lineage_only",
        "pass01_replacement_used": False,
    }


def main() -> None:
    configure_therac()
    stamp = builder.utc_stamp()
    root = builder.OUTPUT_ROOT / f"therac_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    hook_clip = work / "therac_clinical_hook_no_caption_3s.mp4"
    picture_bed = work / "picture_bed_clinical_scene_full_picture_crt_no_caption.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "therac_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_therac_theme_hook_first_10s.mp4"
    frame_strip = evidence / "opening_frame_strip.jpg"
    hook_body_seam_strip = evidence / "hook_body_seam_frame_strip.jpg"
    repaired_span_strip = evidence / "repaired_early_body_motion_span_frame_strip.jpg"
    repaired_seams_strip = evidence / "repaired_early_body_motion_seams_frame_strip.jpg"
    repair_source_03_strip = evidence / "repair_sources" / "03_impossible_repeat_existing_motion_lineage_strip.jpg"
    repair_source_04_strip = evidence / "repair_sources" / "04_controls_take_over_existing_motion_lineage_strip.jpg"
    outro_strip = evidence / "outro_frame_strip.jpg"
    tail_continuity_strip = evidence / "tail_continuity_frame_strip.jpg"
    tail_crt_strip = evidence / "tail_full_picture_crt_frame_strip.jpg"
    end_strip = evidence / "end_frame_strip.jpg"
    waveform = evidence / "first_10s_waveform.png"

    body_repair_context = build_repaired_body(work)
    builder.BODY_CAPTIONED_NO_AUDIO = body_repair_context["repaired_body_path"]
    builder.build_hook_clip(hook_clip)
    picture_bed_context = builder.build_picture_bed(hook_clip, picture_bed)
    builder.build_audio_mix(audio_mix)
    builder.mux(picture_bed, audio_mix, proof)
    builder.extract_excerpt(builder.CURRENT_YOUTUBE_SHORT, 10.0, current_excerpt)
    builder.extract_excerpt(proof, 10.0, revised_excerpt)
    builder.build_comparison(current_excerpt, revised_excerpt, comparison)
    opening_frames = builder.build_frame_strip(proof, frame_strip, [0.0, 0.5, 1.0, 2.0, 2.9, 3.0, 3.1, 4.0, 6.0, 10.0])
    hook_body_seam_frames = builder.build_frame_strip(
        proof,
        hook_body_seam_strip,
        [2.70, 2.90, 3.00, 3.10, 3.30],
    )
    repaired_span_frames = builder.build_frame_strip(
        proof,
        repaired_span_strip,
        [8.75, 9.25, 10.00, 11.25, 12.10, 12.75, 13.50, 14.50, 15.25],
    )
    repaired_seam_frames = builder.build_frame_strip(
        proof,
        repaired_seams_strip,
        [8.85, 9.05, 9.25, 11.90, 12.10, 12.30, 14.80, 15.00, 15.20],
    )
    repair_03 = body_repair_context["body_clip_motion_repairs"][0]
    repair_04 = body_repair_context["body_clip_motion_repairs"][1]
    repair_source_03_frames = builder.build_frame_strip(
        Path(repair_03["normalized_replacement_path"]),
        repair_source_03_strip,
        [0.0, repair_03["target_slot_duration_seconds"] / 2.0, repair_03["target_slot_duration_seconds"] - 0.20],
    )
    repair_source_04_frames = builder.build_frame_strip(
        Path(repair_04["normalized_replacement_path"]),
        repair_source_04_strip,
        [0.0, repair_04["target_slot_duration_seconds"] / 2.0, repair_04["target_slot_duration_seconds"] - 0.20],
    )
    outro_frames = builder.build_frame_strip(
        proof,
        outro_strip,
        [
            builder.OUTRO_START_SECONDS - 0.5,
            builder.OUTRO_START_SECONDS,
            builder.OUTRO_START_SECONDS + 1.5,
            builder.FINAL_DURATION_SECONDS - 0.5,
        ],
    )
    tail_start_seconds = builder.HOOK_DURATION_SECONDS + picture_bed_context["body_duration_seconds"]
    tail_continuity_frames = builder.build_frame_strip(
        proof,
        tail_continuity_strip,
        [
            tail_start_seconds - 1.30,
            tail_start_seconds - 0.80,
            tail_start_seconds - 0.30,
            tail_start_seconds,
            tail_start_seconds + 0.40,
            tail_start_seconds + 0.90,
            tail_start_seconds + 1.60,
            tail_start_seconds + 2.40,
            builder.FINAL_DURATION_SECONDS - 0.50,
        ],
    )
    tail_crt_frames = builder.build_frame_strip(
        proof,
        tail_crt_strip,
        [
            tail_start_seconds,
            tail_start_seconds + 0.25,
            tail_start_seconds + 0.50,
            tail_start_seconds + 0.90,
            tail_start_seconds + 1.40,
            tail_start_seconds + 2.00,
            tail_start_seconds + 2.70,
            builder.FINAL_DURATION_SECONDS - 0.50,
        ],
    )
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

    manifest = {
        "schema_version": "1.0",
        "stage": "first-second hook review",
        "prototype_id": f"therac_theme_intro_hook_{stamp}",
        "local_only_no_youtube_action": True,
        "episode_id": "therac-25",
        "short_id": "therac_short_scoped_v1",
        "current_latest_publish_mp4_path": str(builder.CURRENT_YOUTUBE_SHORT),
        "current_latest_publish_mp4_sha256": builder.sha256(builder.CURRENT_YOUTUBE_SHORT),
        "proof_path": str(proof),
        "proof_sha256": builder.sha256(proof),
        "comparison_path": str(comparison),
        "comparison_sha256": builder.sha256(comparison),
        "frame_strip_path": str(frame_strip),
        "frame_strip_sha256": builder.sha256(frame_strip),
        "hook_body_seam_frame_strip_path": str(hook_body_seam_strip),
        "hook_body_seam_frame_strip_sha256": builder.sha256(hook_body_seam_strip),
        "outro_frame_strip_path": str(outro_strip),
        "outro_frame_strip_sha256": builder.sha256(outro_strip),
        "tail_continuity_frame_strip_path": str(tail_continuity_strip),
        "tail_continuity_frame_strip_sha256": builder.sha256(tail_continuity_strip),
        "tail_crt_frame_strip_path": str(tail_crt_strip),
        "tail_crt_frame_strip_sha256": builder.sha256(tail_crt_strip),
        "end_frame_strip_path": str(end_strip),
        "end_frame_strip_sha256": builder.sha256(end_strip),
        "waveform_path": str(waveform),
        "waveform_sha256": builder.sha256(waveform),
        "clean_motion_source_path": str(builder.NO_CAPTION_PICTURE),
        "clean_motion_source_sha256": builder.sha256(builder.NO_CAPTION_PICTURE),
        "targeted_motion_repaired_body_path": str(body_repair_context["repaired_body_path"]),
        "targeted_motion_repaired_body_sha256": body_repair_context["repaired_body_sha256"],
        "targeted_motion_repaired_body_duration_seconds": body_repair_context["repaired_body_duration_seconds"],
        "body_clip_motion_repairs": body_repair_context["body_clip_motion_repairs"],
        "targeted_repair_clip_ids": body_repair_context["targeted_repair_clip_ids"],
        "only_targeted_body_clips_changed": body_repair_context["only_targeted_body_clips_changed"],
        "frozen_body_clip_repair_read": body_repair_context["frozen_body_clip_repair_read"],
        "regression_repair_source_policy": body_repair_context["regression_repair_source_policy"],
        "pass01_replacement_used": body_repair_context["pass01_replacement_used"],
        "repaired_span_frame_strip_path": str(repaired_span_strip),
        "repaired_span_frame_strip_sha256": builder.sha256(repaired_span_strip),
        "repaired_seams_frame_strip_path": str(repaired_seams_strip),
        "repaired_seams_frame_strip_sha256": builder.sha256(repaired_seams_strip),
        "repair_source_03_frame_strip_path": str(repair_source_03_strip),
        "repair_source_03_frame_strip_sha256": builder.sha256(repair_source_03_strip),
        "repair_source_04_frame_strip_path": str(repair_source_04_strip),
        "repair_source_04_frame_strip_sha256": builder.sha256(repair_source_04_strip),
        "visual_extension_mode": picture_bed_context["visual_extension_mode"],
        "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
        "source_motion_tail": picture_bed_context["source_motion_tail"],
        "full_picture_crt_texture": picture_bed_context["full_picture_crt_texture"],
        "full_picture_crt_scope": picture_bed_context["full_picture_crt_scope"],
        "segment_crt_passes_used": picture_bed_context["segment_crt_passes_used"],
        "tail_segment_crt_pass_used": picture_bed_context["tail_segment_crt_pass_used"],
        "caption_layer_policy": "local_review_no_final_caption_rebuild",
        "tail_repeat_read": "pass",
        "tail_continuation_source_start_seconds": 8.10,
        "source_motion_tail_continuity_read": "pass_review_required",
        "tail_crt_texture": picture_bed_context["source_motion_tail"]["house_crt_tail_texture"]
        if picture_bed_context["source_motion_tail"]
        else None,
        "tail_crt_overlay_read": "pass_review_required",
        "post_62s_texture_match_read": "pass_review_required",
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "body_trimmed_for_tail_motion_seconds": picture_bed_context["body_trimmed_for_tail_motion_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "visual_strategy": {
            "hook_visual": "no-caption Therac-25 clinical patient/machine scene moved to the front",
            "hook_source_path": str(builder.NO_CAPTION_PICTURE),
            "hook_source_start_seconds": builder.HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": builder.HOOK_DURATION_SECONDS,
            "body_after_hook": "clean no-caption Therac-25 motion source starts at original t=0 after hook",
            "body_source_path": str(builder.BODY_CAPTIONED_NO_AUDIO),
            "body_replaces_current_captioned_source_for_texture_review": True,
            "body_clip_motion_repairs": body_repair_context["body_clip_motion_repairs"],
            "targeted_repair_clip_ids": body_repair_context["targeted_repair_clip_ids"],
            "only_targeted_body_clips_changed": body_repair_context["only_targeted_body_clips_changed"],
            "frozen_body_clip_repair_read": body_repair_context["frozen_body_clip_repair_read"],
            "regression_repair_source_policy": body_repair_context["regression_repair_source_policy"],
            "pass01_replacement_used": body_repair_context["pass01_replacement_used"],
            "caption_layer_policy": "local_review_no_final_caption_rebuild",
            "visual_extension_mode": picture_bed_context["visual_extension_mode"],
            "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
            "source_motion_tail": picture_bed_context["source_motion_tail"],
            "full_picture_crt_texture": picture_bed_context["full_picture_crt_texture"],
            "full_picture_crt_scope": picture_bed_context["full_picture_crt_scope"],
            "segment_crt_passes_used": picture_bed_context["segment_crt_passes_used"],
            "tail_segment_crt_pass_used": picture_bed_context["tail_segment_crt_pass_used"],
            "tail_repeat_read": "pass",
            "tail_continuation_source_start_seconds": 8.10,
            "source_motion_tail_continuity_read": "pass_review_required",
            "tail_crt_texture": picture_bed_context["source_motion_tail"]["house_crt_tail_texture"]
            if picture_bed_context["source_motion_tail"]
            else None,
            "tail_crt_overlay_read": "pass_review_required",
            "post_62s_texture_match_read": "pass_review_required",
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
            "outro_start_seconds": round(builder.OUTRO_START_SECONDS, 3),
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
        "frame_samples": {
            "opening": opening_frames,
            "hook_body_seam": hook_body_seam_frames,
            "repaired_span": repaired_span_frames,
            "repaired_seams": repaired_seam_frames,
            "repair_source_03": repair_source_03_frames,
            "repair_source_04": repair_source_04_frames,
            "outro": outro_frames,
            "tail_continuity": tail_continuity_frames,
            "tail_crt": tail_crt_frames,
            "end": end_frames,
        },
        "review_request": "Judge whether the Therac-25 clinical scene plus full theme intro punch works better than the current opening, and whether the transition into the loop feels natural before voice starts.",
        "human_review_disposition": "keep|tighten|reject",
    }
    builder.write_json(root / "therac_theme_intro_hook_manifest.json", manifest)

    note = f"""# Therac-25 Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `frame_strip_path`: `{frame_strip}`
- `hook_body_seam_frame_strip_path`: `{hook_body_seam_strip}`
- `repaired_span_frame_strip_path`: `{repaired_span_strip}`
- `repaired_seams_frame_strip_path`: `{repaired_seams_strip}`
- `repair_source_03_frame_strip_path`: `{repair_source_03_strip}`
- `repair_source_04_frame_strip_path`: `{repair_source_04_strip}`
- `tail_continuity_frame_strip_path`: `{tail_continuity_strip}`
- `tail_crt_frame_strip_path`: `{tail_crt_strip}`
- `end_frame_strip_path`: `{end_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{builder.HOOK_DURATION_SECONDS:.1f}s` is a no-caption clinical Therac-25 patient/machine scene.
- The full theme song starts from `0.00` so the opening punch lands immediately.
- The theme intro crossfades into the registered loop from `{builder.LOOP_START_SECONDS:.2f}s` to `{builder.LOOP_START_SECONDS + builder.LOOP_CROSSFADE_SECONDS:.2f}s`.
- The approved Therac-25 voice starts after the hook at `{builder.VOICE_DELAY_SECONDS:.2f}s`.
- The loop continues under the body, then fades into the theme outro at `{builder.OUTRO_START_SECONDS:.2f}s`.
- The previous cloned-frame tail padding has been replaced with source motion tail footage.
- The tail scout now starts at `8.10s` so the end continues instead of replaying the same patient/machine shot from the beginning.
- The picture bed is rebuilt from clean no-caption motion sources, then one full-picture CRT/analog pass is applied across hook, body, and tail.
- Only the two frozen early body clip slots are replaced with existing Therac motion-lineage clips: `03_edl_03_impossible_repeat_hold` and `04_edl_04_controls_take_over_hold`.
- Segment-specific CRT passes are disabled for this Therac proof so the scanline/noise pattern stays continuous through the `1:02` tail handoff.
- Final caption rebuilding remains deferred; this package is for local texture and timing review only.
- `only_targeted_body_clips_changed`: `{str(body_repair_context["only_targeted_body_clips_changed"]).lower()}`
- `frozen_body_clip_repair_read`: `{body_repair_context["frozen_body_clip_repair_read"]}`
- `regression_repair_source_policy`: `{body_repair_context["regression_repair_source_policy"]}`
- `pass01_replacement_used`: `{str(body_repair_context["pass01_replacement_used"]).lower()}`
- `full_picture_crt_scope`: `{picture_bed_context["full_picture_crt_scope"]}`
- `segment_crt_passes_used`: `{str(picture_bed_context["segment_crt_passes_used"]).lower()}`
- `caption_layer_policy`: `local_review_no_final_caption_rebuild`
- `tail_repeat_read`: `pass`
- `source_motion_tail_continuity_read`: `pass_review_required`
- `tail_crt_overlay_read`: `pass_review_required`
- `post_62s_texture_match_read`: `pass_review_required`
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`

## Review Read

Mark this `keep`, `tighten`, or `reject`.

- `keep`: clinical scene plus theme punch clearly improves scroll-stop and the loop handoff feels natural.
- `tighten`: the idea works, but the hook scene, music level, loop handoff, or outro timing needs adjustment.
- `reject`: it feels too loud, too front-loaded, tonally wrong, or less effective than the current opening.
"""
    builder.write_text(root / "review_note.md", note)

    latest_link = builder.OUTPUT_ROOT / "therac_theme_intro_hook_latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
