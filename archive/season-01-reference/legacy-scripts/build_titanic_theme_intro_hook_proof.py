#!/usr/bin/env python3
"""Build a local Titanic proof with a source-led theme-intro hook."""

from __future__ import annotations

import importlib.util
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


EPISODE_ID = "titanic"
SHORT_ID = "titanic_short_scoped_v1"
DISPLAY_NAME = "Titanic"

EPISODE_SHORT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1")
LATEST_PUBLISH_DIR = (
    EPISODE_SHORT_ROOT / "publish/youtube_20260430T201719Z_pass18_loc_archival_source_motion_tail_repair"
)
CURRENT_YOUTUBE_SHORT = (
    LATEST_PUBLISH_DIR / "titanic_lifeboat_gap_pass18_loc_archival_source_motion_tail_repair_youtube_short.mp4"
)
VOICE_WAV = EPISODE_SHORT_ROOT / "final/titanic_short_scoped_v1.wav"

TITANIC_VIZ_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/titanic_short_scoped_v1"
)
PASS14_ROOT = TITANIC_VIZ_ROOT / "motion_video_proof/pass_14_loc_archival_timed_proof"
PASS14_CLIPS_DIR = PASS14_ROOT / "clips"

CLIP_45_SOURCE = (
    PASS14_CLIPS_DIR / "11_loc_p14_11_survivor_press_correction__loc_08_survivor_group.mp4"
)
BODY_SEGMENT_11_REPLACEMENT_SOURCE = (
    TITANIC_VIZ_ROOT
    / "motion_contact_sheet/pass_13_loc_archival_vertical_feedback_repair/candidates/normalized/"
    "loc_04_cabin_decks__loc-direct-source-vertical-crop__no_audio.mp4"
)
HOOK_SOURCE = CLIP_45_SOURCE
TAIL_SOURCE = CLIP_45_SOURCE
BODY_REPLACEMENT_SOURCES = {
    "11": {
        "replacement_source": BODY_SEGMENT_11_REPLACEMENT_SOURCE,
        "reason": "45s survivor-group clip is repurposed as opening and closing bookend; replace the body occurrence to avoid a distracting repeat",
        "read": "pass_review_required",
    }
}

HOOK_SOURCE_START_SECONDS = 1.60
HOOK_DURATION_SECONDS = 3.0
TAIL_SOURCE_START_SECONDS = 0.75
SIGNAL_INTERRUPT_SECONDS = 0.25

# Keep the existing pass18 outro placement relationship and shift it by the new 3s hook.
VOICE_LAST_AUDIBLE_SECONDS = 59.350
OUTRO_START_SECONDS = 59.895125
FINAL_DURATION_SECONDS = 66.866667


def configure_titanic(body_source: Path | None = None) -> None:
    builder.SHORT_ROOT = EPISODE_SHORT_ROOT
    builder.LATEST_PUBLISH_DIR = LATEST_PUBLISH_DIR
    builder.CURRENT_YOUTUBE_SHORT = CURRENT_YOUTUBE_SHORT
    builder.BODY_CAPTIONED_NO_AUDIO = (
        body_source if body_source is not None else PASS14_ROOT / "titanic_loc_archival_timed_motion_video_proof_pass_14_silent.mp4"
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
        "purpose": "apply one continuous CRT/analog texture over the assembled Titanic hook, body, and tail proof",
        "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
        "scanline_strength_variant_id": "max_visible_bars_y24_p8",
        "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
    }
    builder.SOURCE_MOTION_TAIL = {
        "path": TAIL_SOURCE,
        "start_seconds": TAIL_SOURCE_START_SECONDS,
        "description": "moving no-audio LOC survivor-group source tail returning to the 45s clip used as the opening hook",
        "house_crt_tail_texture": None,
        "signal_interruption": {
            "profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
            "duration_seconds": SIGNAL_INTERRUPT_SECONDS,
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "full_frame_static_replacement_used": False,
            "purpose": "brief analog interruption between the LOC archival body and returning survivor-group tail",
        },
    }


def require_inputs() -> None:
    configure_titanic()
    for path in (
        CURRENT_YOUTUBE_SHORT,
        VOICE_WAV,
        builder.THEME_FULL,
        builder.THEME_LOOP_60,
        builder.THEME_OUTRO,
        PASS14_CLIPS_DIR,
        HOOK_SOURCE,
        TAIL_SOURCE,
        BODY_SEGMENT_11_REPLACEMENT_SOURCE,
        builder.BODY_CAPTIONED_NO_AUDIO,
    ):
        if not Path(path).exists():
            raise FileNotFoundError(str(path))


def pass14_body_segments() -> list[Path]:
    segments = sorted(PASS14_CLIPS_DIR.glob("*.mp4"))
    if len(segments) != 15:
        raise RuntimeError(f"Expected 15 Titanic pass14 body segments, found {len(segments)}")
    expected_prefixes = [f"{index:02d}_" for index in range(1, 16)]
    actual_prefixes = [segment.name[:3] for segment in segments]
    if actual_prefixes != expected_prefixes:
        raise RuntimeError(f"Unexpected Titanic pass14 segment order: {actual_prefixes}")
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


def normalize_segment(source: Path, output: Path, target_duration_seconds: float | None = None) -> dict[str, Any]:
    source_duration = builder.duration(source)
    target_duration = source_duration if target_duration_seconds is None else target_duration_seconds
    if source_duration + 0.001 < target_duration:
        raise RuntimeError(
            f"Replacement source is too short for requested duration: {source} "
            f"source={source_duration:.6f}s target={target_duration:.6f}s"
        )
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
        "prepared_path": str(output),
        "prepared_sha256": builder.sha256(output),
        "duration_seconds": round(builder.duration(output), 6),
        "target_duration_seconds": round(target_duration, 6),
        "normalization": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "cloned_frame_padding_used": False,
    }


def build_clean_body_from_segments(work: Path) -> dict[str, Any]:
    segments = pass14_body_segments()
    prepared_segments: list[dict[str, Any]] = []
    body_signal_boundaries: list[dict[str, Any]] = []
    body_clip_repeat_repairs: list[dict[str, Any]] = []

    for index, segment in enumerate(segments):
        segment_id = segment.name.split("_", 1)[0]
        next_segment = segments[index + 1] if index + 1 < len(segments) else None
        next_segment_id = next_segment.name.split("_", 1)[0] if next_segment else None
        source_for_signal = segment
        source_path = segment
        replacement_context = None

        if segment_id in BODY_REPLACEMENT_SOURCES:
            repair = BODY_REPLACEMENT_SOURCES[segment_id]
            replacement_source = Path(repair["replacement_source"])
            replacement_prepared_path = (
                work
                / "body_replacements"
                / f"body_{segment_id}_replacement_{replacement_source.stem}_no_audio.mp4"
            )
            original_duration = builder.duration(segment)
            normalization_context = normalize_segment(
                replacement_source,
                replacement_prepared_path,
                target_duration_seconds=original_duration,
            )
            source_for_signal = replacement_prepared_path
            source_path = replacement_source
            replacement_context = {
                "segment_id": segment_id,
                "original_segment_path": str(segment),
                "original_segment_sha256": builder.sha256(segment),
                "original_segment_duration_seconds": round(original_duration, 6),
                "replacement_source_path": str(replacement_source),
                "replacement_source_sha256": builder.sha256(replacement_source),
                "prepared_replacement_path": str(replacement_prepared_path),
                "prepared_replacement_sha256": builder.sha256(replacement_prepared_path),
                "prepared_replacement_duration_seconds": round(builder.duration(replacement_prepared_path), 6),
                "normalization": normalization_context["normalization"],
                "reason": repair["reason"],
                "read": repair["read"],
            }
            body_clip_repeat_repairs.append(replacement_context)

        prepared_path = segment
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

    concat_path = work / "concat_titanic_pass14_source_body_segments.txt"
    body_output = work / "titanic_pass14_clean_body_from_source_segments_no_audio.mp4"
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
            str(body_output),
        ]
    )

    segment_rows: list[dict[str, Any]] = []
    cursor = 0.0
    for row in prepared_segments:
        segment = Path(row["prepared_path"])
        segment_duration = builder.duration(segment)
        proof_start = builder.HOOK_DURATION_SECONDS + cursor
        proof_end = builder.HOOK_DURATION_SECONDS + cursor + segment_duration
        segment_rows.append(
            {
                "path": str(segment),
                "sha256": builder.sha256(segment),
                "source_path": str(row["source_path"]),
                "source_sha256": builder.sha256(Path(row["source_path"])),
                "original_segment_path": str(row["original_segment_path"]),
                "original_segment_sha256": builder.sha256(Path(row["original_segment_path"])),
                "original_segment_id": row["segment_id"],
                "replacement_applied": row["replacement_context"] is not None,
                "replacement_context": row["replacement_context"],
                "duration_seconds": round(segment_duration, 6),
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
        "body_source_policy": "rebuilt_from_existing_pass14_loc_archival_source_segments_with_segment_11_repeat_replacement_and_signal_interruptions",
        "segment_count": len(segments),
        "segment_order_read": "pass_original_pass14_order_preserved",
        "body_signal_interruption_boundaries": body_signal_boundaries,
        "body_clip_repeat_repairs": body_clip_repeat_repairs,
        "segments": segment_rows,
        "concat_list_path": str(concat_path),
        "clean_body_path": str(body_output),
        "clean_body_sha256": builder.sha256(body_output),
        "clean_body_duration_seconds": round(builder.duration(body_output), 6),
        "only_signal_interruptions_added": False,
        "body_clip_45_replaced": True,
        "only_body_segment_11_changed": True,
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


def main() -> None:
    require_inputs()
    stamp = builder.utc_stamp()
    root = builder.OUTPUT_ROOT / f"titanic_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    body_context = build_clean_body_from_segments(work)
    body_path = Path(body_context["clean_body_path"])
    configure_titanic(body_path)

    hook_clip = work / "titanic_45s_survivor_group_hook_no_audio_3s.mp4"
    hook_signal_clip = work / "titanic_45s_survivor_group_hook_tail_signal_no_audio_3s.mp4"
    picture_bed = work / "picture_bed_titanic_hook_pass14_body_tail_full_picture_crt_no_audio.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "titanic_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_titanic_theme_hook_first_10s.mp4"
    opening_strip = evidence / "opening_frame_strip.jpg"
    hook_source_strip = evidence / "hook_source_frame_strip.jpg"
    hook_body_signal_strip = evidence / "hook_body_signal_interruption_frame_strip.jpg"
    hook_body_seam_strip = evidence / "hook_body_seam_frame_strip.jpg"
    body_replacement_source_strip = evidence / "body_segment_11_replacement_source_frame_strip.jpg"
    body_clip_45_replacement_strip = evidence / "body_clip_45_replacement_frame_strip.jpg"
    all_signal_boundaries_strip = evidence / "all_signal_interruption_boundaries_frame_strip.jpg"
    body_signal_boundaries_strip = evidence / "body_segment_signal_interruption_boundaries_frame_strip.jpg"
    signal_tail_outro_strip = evidence / "signal_tail_outro_handoff_frame_strip.jpg"
    opening_closing_bookend_strip = evidence / "opening_closing_45s_clip_bookend_frame_strip.jpg"
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
    replaced_body_segment = next(
        segment
        for segment in body_context["segments"]
        if segment["original_segment_id"] == "11"
    )
    replacement_start_seconds = replaced_body_segment["proof_timeline_start_seconds"]
    replacement_end_seconds = replaced_body_segment["proof_timeline_end_seconds"]
    signal_start_seconds = builder.HOOK_DURATION_SECONDS + picture_bed_context["body_duration_seconds"]
    tail_start_seconds = signal_start_seconds + picture_bed_context["signal_interruption_duration_seconds"]
    tail_signal_boundary = {
        "boundary_id": "body_15_to_tail",
        "outgoing_segment_id": "15",
        "incoming_segment_id": "source_motion_tail",
        "proof_boundary_seconds": round(tail_start_seconds, 6),
        "proof_signal_start_seconds": round(signal_start_seconds, 6),
        "proof_signal_center_seconds": round(signal_start_seconds + (SIGNAL_INTERRUPT_SECONDS / 2.0), 6),
        "proof_signal_end_seconds": round(tail_start_seconds, 6),
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPT_SECONDS,
        "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
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
    body_replacement_source_frames = builder.build_frame_strip(
        BODY_SEGMENT_11_REPLACEMENT_SOURCE,
        body_replacement_source_strip,
        [0.0, 0.75, 1.5, 2.5, 3.5, 4.5],
    )
    body_clip_45_replacement_frames = builder.build_frame_strip(
        proof,
        body_clip_45_replacement_strip,
        [
            max(0.0, replacement_start_seconds - 0.25),
            replacement_start_seconds,
            replacement_start_seconds + 0.75,
            replacement_start_seconds + 2.00,
            replacement_end_seconds - 0.25,
            replacement_end_seconds,
            replacement_end_seconds + 0.25,
        ],
    )
    signal_tail_outro_frames = builder.build_frame_strip(
        proof,
        signal_tail_outro_strip,
        [
            builder.OUTRO_START_SECONDS - 0.50,
            builder.OUTRO_START_SECONDS,
            signal_start_seconds - 0.20,
            signal_start_seconds,
            tail_start_seconds,
            tail_start_seconds + 0.50,
            builder.FINAL_DURATION_SECONDS - 0.50,
        ],
    )
    opening_closing_bookend_frames = builder.build_frame_strip(
        proof,
        opening_closing_bookend_strip,
        [
            0.0,
            1.0,
            2.75,
            tail_start_seconds,
            tail_start_seconds + 1.0,
            builder.FINAL_DURATION_SECONDS - 1.0,
            builder.FINAL_DURATION_SECONDS - 0.25,
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
        "body_clip_45_replacement_motion": framehash_sample(
            proof,
            replacement_start_seconds,
            min(3.0, replacement_end_seconds - replacement_start_seconds),
            evidence / "body_clip_45_replacement_motion_framemd5.txt",
        ),
        "body_tail_signal_interruption_motion": framehash_sample(
            proof,
            signal_start_seconds,
            0.50,
            evidence / "body_tail_signal_interruption_motion_framemd5.txt",
            sample_rate_fps=12,
        ),
        "tail_motion": framehash_sample(
            proof,
            tail_start_seconds,
            max(0.25, min(3.0, builder.FINAL_DURATION_SECONDS - tail_start_seconds)),
            evidence / "tail_motion_framemd5.txt",
        ),
    }

    signal_interruption_context = {
        "signal_interruptions_between_every_clip": True,
        "signal_interruption_boundary_count": len(signal_boundaries),
        "signal_interruption_duration_seconds": SIGNAL_INTERRUPT_SECONDS,
        "signal_interruption_timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
        "signal_interruption_profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
        "signal_interruption_boundaries": signal_boundaries,
    }

    manifest = {
        "schema_version": "1.0",
        "stage": "first-second hook review",
        "prototype_id": f"titanic_theme_intro_hook_{stamp}",
        "local_only_no_youtube_action": True,
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "display_name": DISPLAY_NAME,
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
        "body_segment_11_replacement_source_frame_strip_path": str(body_replacement_source_strip),
        "body_segment_11_replacement_source_frame_strip_sha256": builder.sha256(body_replacement_source_strip),
        "body_clip_45_replacement_frame_strip_path": str(body_clip_45_replacement_strip),
        "body_clip_45_replacement_frame_strip_sha256": builder.sha256(body_clip_45_replacement_strip),
        "all_signal_interruption_boundaries_frame_strip_path": str(all_signal_boundaries_strip),
        "all_signal_interruption_boundaries_frame_strip_sha256": builder.sha256(all_signal_boundaries_strip),
        "body_segment_signal_interruption_boundaries_frame_strip_path": str(body_signal_boundaries_strip),
        "body_segment_signal_interruption_boundaries_frame_strip_sha256": builder.sha256(body_signal_boundaries_strip),
        "signal_tail_outro_handoff_frame_strip_path": str(signal_tail_outro_strip),
        "signal_tail_outro_handoff_frame_strip_sha256": builder.sha256(signal_tail_outro_strip),
        "opening_closing_45s_clip_bookend_frame_strip_path": str(opening_closing_bookend_strip),
        "opening_closing_45s_clip_bookend_frame_strip_sha256": builder.sha256(opening_closing_bookend_strip),
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
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "body_trimmed_for_tail_motion_seconds": picture_bed_context["body_trimmed_for_tail_motion_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "tail_start_seconds": round(tail_start_seconds, 6),
        "opening_crowded_deck_hook_read": "pass_review_required",
        "opening_closing_source_path_match": str(HOOK_SOURCE.resolve()) == str(TAIL_SOURCE.resolve()),
        "clip_45_repurposed_to_opening_and_tail": True,
        "clip_45_original_body_proof_span_seconds": {
            "start": 43.499999,
            "end": 48.533332,
        },
        "closing_returns_to_45s_clip": True,
        "closing_tail_source_start_seconds": TAIL_SOURCE_START_SECONDS,
        "closing_tail_source_duration_seconds": picture_bed_context["source_motion_tail"]["duration_seconds"],
        "opening_hook_source_cut_trimmed_seconds": HOOK_SOURCE_START_SECONDS,
        "opening_hook_source_native_cut_avoided": True,
        "opening_hook_first_frame_read": "pass_review_required",
        "opening_hook_internal_source_cut_read": "pass_review_required",
        "body_clip_45_replaced": True,
        "body_clip_repeat_repair": body_context["body_clip_repeat_repairs"][0],
        "body_repeat_repair_source_path": str(BODY_SEGMENT_11_REPLACEMENT_SOURCE),
        "distracting_repeat_read": "pass_review_required",
        "opening_closing_clip_match_read": "pass_review_required",
        "only_body_segment_11_changed": True,
        "opening_subject_event_presence_read": "pass_review_required",
        "hook_body_no_immediate_repeat_read": "pass_review_required",
        "hook_body_signal_interruption_read": "pass_review_required",
        "body_segment_signal_interruption_read": "pass_review_required",
        "body_tail_signal_interruption_read": "pass_review_required",
        "tail_motion_read": motion_evidence["tail_motion"]["read"],
        "full_picture_crt_continuity_read": "pass_review_required",
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "pass14_clean_body_context": body_context,
        "visual_strategy": {
            "hook_visual": "LOC archival survivor-group clip from proof 45s opens the proof before narration",
            "hook_source_path": str(HOOK_SOURCE),
            "hook_source_start_seconds": builder.HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": builder.HOOK_DURATION_SECONDS,
            "hook_selection_reason": "user-selected proof 45s clip becomes the opening bookend; source start is trimmed to 1.60s to avoid the preceding source-native stair/crowd cut",
            "body_after_hook": "existing pass14 LOC archival body order preserved except segment 11 is replaced to avoid repeating the opening/closing survivor-group clip",
            "body_source_path": str(builder.BODY_CAPTIONED_NO_AUDIO),
            "body_clip_45_replacement_source_path": str(BODY_SEGMENT_11_REPLACEMENT_SOURCE),
            "tail_visual": "same LOC survivor-group source returns for the theme outro tail",
            "tail_source_path": str(TAIL_SOURCE),
            "tail_source_start_seconds": TAIL_SOURCE_START_SECONDS,
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
            "outro_timing_policy": "preserve_pass18_outro_relationship_shifted_by_3s_hook",
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
            "body_segment_11_replacement_source": body_replacement_source_frames,
            "body_clip_45_replacement": body_clip_45_replacement_frames,
            "all_signal_interruption_boundaries": all_signal_boundary_frames,
            "body_segment_signal_interruption_boundaries": body_signal_boundary_frames,
            "signal_tail_outro_handoff": signal_tail_outro_frames,
            "opening_closing_45s_clip_bookend": opening_closing_bookend_frames,
            "end": end_frames,
        },
        "review_request": "Judge whether the proof 45s survivor-group clip works as the opening and closing bookend, whether replacing its body occurrence avoids distracting repeats, and whether signal rhythm, CRT continuity, and moving tail still hold.",
        "human_review_disposition": "keep|tighten|reject",
    }
    builder.write_json(root / "titanic_theme_intro_hook_manifest.json", manifest)

    note = f"""# Titanic Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `opening_frame_strip_path`: `{opening_strip}`
- `hook_source_frame_strip_path`: `{hook_source_strip}`
- `hook_body_signal_interruption_frame_strip_path`: `{hook_body_signal_strip}`
- `hook_body_seam_frame_strip_path`: `{hook_body_seam_strip}`
- `body_segment_11_replacement_source_frame_strip_path`: `{body_replacement_source_strip}`
- `body_clip_45_replacement_frame_strip_path`: `{body_clip_45_replacement_strip}`
- `all_signal_interruption_boundaries_frame_strip_path`: `{all_signal_boundaries_strip}`
- `body_segment_signal_interruption_boundaries_frame_strip_path`: `{body_signal_boundaries_strip}`
- `signal_tail_outro_handoff_frame_strip_path`: `{signal_tail_outro_strip}`
- `opening_closing_45s_clip_bookend_frame_strip_path`: `{opening_closing_bookend_strip}`
- `end_frame_strip_path`: `{end_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{builder.HOOK_DURATION_SECONDS:.1f}s` opens on the survivor-group clip that previously appeared around proof `45s`, starting at source `{HOOK_SOURCE_START_SECONDS:.2f}s` to avoid the preceding source-native stair/crowd cut.
- The ending tail returns to the same survivor-group source clip from `{TAIL_SOURCE_START_SECONDS:.2f}s`, trimmed to the computed tail gap.
- The full theme song starts from `0.00`, then crossfades into the registered loop from `{builder.LOOP_START_SECONDS:.2f}s` to `{builder.LOOP_START_SECONDS + builder.LOOP_CROSSFADE_SECONDS:.2f}s`.
- The approved Titanic voice starts at `{builder.VOICE_DELAY_SECONDS:.2f}s`; final captions remain deferred.
- The pass14 LOC body order is preserved except segment `11` is replaced with the cabin/deck source clip so the proof does not repeat the opening/closing survivor-group clip in the body.
- The existing `{SIGNAL_INTERRUPT_SECONDS:.2f}s` analog signal interruption appears at every clip boundary by replacing the outgoing clip tail, not adding runtime.
- Signal boundaries are applied at hook -> segment `01`, all body segment boundaries, and segment `15` -> tail.
- One continuous full-picture CRT pass is applied after hook/body/tail assembly.
- The moving source tail uses the same survivor-group LOC clip as the opening; cloned-frame padding is not used.
- `signal_interruption_boundary_count`: `{len(signal_boundaries)}`
- `body_clip_45_replaced`: `true`
- `tail_motion_read`: `{motion_evidence["tail_motion"]["read"]}`
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`

## Review Read

Mark this `keep`, `tighten`, or `reject`.

- `keep`: the 45s survivor-group clip works as both opener and closer, the body replacement removes the distracting repeat, and signal/CRT/tail behavior still works.
- `tighten`: the direction works, but the bookend span, replacement clip, interruption density, tail span, or audio balance needs adjustment.
- `reject`: it is less effective than the current Titanic opening.
"""
    builder.write_text(root / "review_note.md", note)

    latest_link = builder.OUTPUT_ROOT / "titanic_theme_intro_hook_latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
