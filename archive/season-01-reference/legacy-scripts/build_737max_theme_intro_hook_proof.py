#!/usr/bin/env python3
"""Build a local 737 MAX proof with official Boeing aircraft hook plus theme-intro music."""

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


EPISODE_ID = "737-max"
SHORT_ID = "737_max_short_scoped_v1"
DISPLAY_NAME = "737 MAX"

EPISODE_SHORT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/shorts/737_max_short_scoped_v1")
LATEST_PUBLISH_DIR = EPISODE_SHORT_ROOT / "publish/youtube_20260518T173949Z"
CURRENT_YOUTUBE_SHORT = LATEST_PUBLISH_DIR / "737_max_mcas_familiar_airplane_youtube_short.mp4"
VOICE_WAV = EPISODE_SHORT_ROOT / "final/737_max_short_scoped_v1.wav"

PASS07_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/737-max/shorts/737_max_short_scoped_v1/"
    "motion_video_proof/pass_05_source_led_takeoff_continuity_repair/final_exports/"
    "737-max_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
    "20260429T_house_crt_visible_scanline_first8_pass07_y24"
)
PASS07_SEGMENTS_DIR = PASS07_ROOT / "work/segments"
OFFICIAL_AUDIT_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Shorts_First_Second_Hook_Retrofit/"
    "737max_official_clean_footage_audit_latest"
)
OFFICIAL_AUDIT_MANIFEST = OFFICIAL_AUDIT_ROOT / "official_clean_footage_audit_manifest.json"
OFFICIAL_TAIL_SOURCE = OFFICIAL_AUDIT_ROOT / "clips/bff_span_75_110_air_to_air_landing_exact_no_audio.mp4"
OFFICIAL_HOOK_SOURCE = OFFICIAL_TAIL_SOURCE

HOOK_SOURCE_START_SECONDS = 5.472133
HOOK_DURATION_SECONDS = 3.0
TAIL_SOURCE_START_SECONDS = 0.0
LAST_SHOT_PROOF_START_SECONDS = 63.466667
VOICE_LAST_AUDIBLE_SECONDS = 55.124172
OUTRO_START_SECONDS = 58.224172
FINAL_DURATION_SECONDS = 65.204172
BODY_SWAP_SEGMENT_06_INDEX = 5
BODY_SWAP_SEGMENT_07_INDEX = 6
SEGMENT_06_HEAD_FLASH_TRIM_SECONDS = 0.12
SIGNAL_INTERRUPT_SECONDS = 0.25


def configure_737(body_source: Path | None = None) -> None:
    builder.SHORT_ROOT = EPISODE_SHORT_ROOT
    builder.LATEST_PUBLISH_DIR = LATEST_PUBLISH_DIR
    builder.CURRENT_YOUTUBE_SHORT = CURRENT_YOUTUBE_SHORT
    builder.BODY_CAPTIONED_NO_AUDIO = body_source if body_source is not None else PASS07_ROOT / "work/motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
    builder.NO_CAPTION_PICTURE = OFFICIAL_HOOK_SOURCE
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
        "purpose": "apply one continuous CRT/analog texture over the assembled 737 MAX hook, body, and tail proof",
        "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
        "scanline_strength_variant_id": "max_visible_bars_y24_p8",
        "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
    }
    builder.SOURCE_MOTION_TAIL = {
        "path": OFFICIAL_TAIL_SOURCE,
        "start_seconds": TAIL_SOURCE_START_SECONDS,
        "description": "moving no-audio official Boeing first-flight air-to-air/landing source tail for the full theme outro",
        "house_crt_tail_texture": None,
        "signal_interruption": {
            "profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
            "duration_seconds": 0.25,
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "full_frame_static_replacement_used": False,
            "purpose": "brief analog interruption between the clean pass-07 body and official Boeing source tail motion",
        },
    }


def require_inputs() -> None:
    configure_737()
    for path in (
        CURRENT_YOUTUBE_SHORT,
        VOICE_WAV,
        builder.THEME_FULL,
        builder.THEME_LOOP_60,
        builder.THEME_OUTRO,
        OFFICIAL_AUDIT_MANIFEST,
        OFFICIAL_HOOK_SOURCE,
        OFFICIAL_TAIL_SOURCE,
        PASS07_SEGMENTS_DIR,
    ):
        if not Path(path).exists():
            raise FileNotFoundError(str(path))


def pass07_source_segments() -> list[Path]:
    segments = sorted(PASS07_SEGMENTS_DIR.glob("*__source_segment_no_audio.mp4"))
    if len(segments) != 14:
        raise RuntimeError(f"Expected 14 pass-07 source body segments, found {len(segments)}")
    expected_prefixes = [f"{index:02d}_" for index in range(1, 15)]
    actual_prefixes = [segment.name[:3] for segment in segments]
    if actual_prefixes != expected_prefixes:
        raise RuntimeError(f"Unexpected pass-07 body segment order: {actual_prefixes}")
    return segments


def repair_segment_06_head_flash(source: Path, output: Path) -> dict[str, Any]:
    source_duration = builder.duration(source)
    repaired_motion_duration = source_duration - SEGMENT_06_HEAD_FLASH_TRIM_SECONDS
    if repaired_motion_duration <= 0:
        raise RuntimeError(f"Segment 06 is too short for head-flash trim: {source}")
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
                f"trim=start={SEGMENT_06_HEAD_FLASH_TRIM_SECONDS:.6f},setpts=PTS-STARTPTS,"
                f"setpts={source_duration / repaired_motion_duration:.12f}*PTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                "setsar=1,fps=30,"
                f"trim=0:{source_duration:.6f},setpts=PTS-STARTPTS,format=yuv420p"
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
        "repair_id": "segment_06_head_engine_flash_trim",
        "source_path": str(source),
        "source_sha256": builder.sha256(source),
        "repaired_path": str(output),
        "repaired_sha256": builder.sha256(output),
        "trimmed_head_seconds": SEGMENT_06_HEAD_FLASH_TRIM_SECONDS,
        "duration_seconds": round(builder.duration(output), 6),
        "duration_policy": "preserve_original_segment_duration_by_subtle_motion_retime",
        "cloned_frame_padding_used": False,
        "read": "pass_review_required",
    }


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


def build_clean_body_from_segments(work: Path) -> dict[str, Any]:
    original_segments = pass07_source_segments()
    segments = list(original_segments)
    segment_06_original = original_segments[BODY_SWAP_SEGMENT_06_INDEX]
    segment_06_repaired = work / "segment_06_high_aoa_pitch_behavior_head_flash_repaired_no_audio.mp4"
    segment_06_flash_repair = repair_segment_06_head_flash(segment_06_original, segment_06_repaired)
    segment_06 = segment_06_repaired
    segment_07 = original_segments[BODY_SWAP_SEGMENT_07_INDEX]
    segments[BODY_SWAP_SEGMENT_06_INDEX], segments[BODY_SWAP_SEGMENT_07_INDEX] = segment_07, segment_06
    prepared_segments: list[dict[str, Any]] = []
    body_signal_boundaries: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        segment_id = "06" if segment == segment_06 else segment.name.split("_", 1)[0]
        next_segment = segments[index + 1] if index + 1 < len(segments) else None
        next_segment_id = None
        prepared_path = segment
        signal_context = None
        if next_segment is not None:
            next_segment_id = "06" if next_segment == segment_06 else next_segment.name.split("_", 1)[0]
            boundary_id = f"body_{segment_id}_to_{next_segment_id}"
            prepared_path = work / "body_signal_boundaries" / f"{boundary_id}_signal_replaced_no_audio.mp4"
            signal_context = apply_tail_signal_interruption(segment, prepared_path, boundary_id)
        prepared_segments.append(
            {
                "segment_id": segment_id,
                "source_path": segment,
                "prepared_path": prepared_path,
                "signal_context": signal_context,
                "incoming_segment_id": next_segment_id,
            }
        )

    concat_path = work / "concat_737max_pass07_source_body_segments.txt"
    body_output = work / "737max_pass07_clean_body_from_source_segments_no_audio.mp4"

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
                "original_segment_id": row["segment_id"],
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
    segment_07_duration = builder.duration(segment_07)
    segment_06_duration = builder.duration(segment_06)
    segment_07_body_start = sum(builder.duration(segment) for segment in original_segments[:BODY_SWAP_SEGMENT_06_INDEX])
    segment_06_body_start = segment_07_body_start + segment_07_duration
    body_clip_order_repairs = [
        {
            "repair_id": "swap_cockpit_takeoff_segments_06_07",
            "reason": "place the more advanced land-out-the-window takeoff cockpit view before the earlier cockpit view",
            "segments_swapped": [
                {
                    "original_segment_id": "06",
                    "original_path": str(segment_06_original),
                    "path": str(segment_06),
                    "duration_seconds": round(segment_06_duration, 6),
                    "original_proof_start_seconds": 23.566667,
                    "new_proof_start_seconds": round(builder.HOOK_DURATION_SECONDS + segment_06_body_start, 6),
                    "head_flash_repair_id": segment_06_flash_repair["repair_id"],
                },
                {
                    "original_segment_id": "07",
                    "path": str(segment_07),
                    "duration_seconds": round(segment_07_duration, 6),
                    "original_proof_start_seconds": 28.166667,
                    "new_proof_start_seconds": round(builder.HOOK_DURATION_SECONDS + segment_07_body_start, 6),
                },
            ],
            "duration_policy": "preserve_source_segment_durations",
        }
    ]
    return {
        "body_source_policy": "rebuilt_from_existing_pass07_source_segment_no_audio_clips_with_targeted_06_07_order_swap",
        "segment_count": len(segments),
        "segment_order_read": "pass_with_targeted_06_07_swap",
        "body_clip_order_repairs": body_clip_order_repairs,
        "body_clip_flash_repairs": [segment_06_flash_repair],
        "body_signal_interruption_boundaries": body_signal_boundaries,
        "only_body_segments_06_07_swapped": True,
        "only_segment_06_head_flash_trimmed": True,
        "segments": segment_rows,
        "concat_list_path": str(concat_path),
        "clean_body_path": str(body_output),
        "clean_body_sha256": builder.sha256(body_output),
        "clean_body_duration_seconds": round(builder.duration(body_output), 6),
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
    root = builder.OUTPUT_ROOT / f"737max_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    body_context = build_clean_body_from_segments(work)
    body_path = Path(body_context["clean_body_path"])
    configure_737(body_path)

    hook_clip = work / "737max_official_boeing_last_air_to_air_shot_hook_no_audio_3s.mp4"
    hook_signal_clip = work / "737max_official_boeing_last_air_to_air_shot_hook_tail_signal_no_audio_3s.mp4"
    picture_bed = work / "picture_bed_official_boeing_hook_pass07_body_tail_full_picture_crt_no_audio.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "737max_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_737max_theme_hook_first_10s.mp4"
    opening_strip = evidence / "opening_frame_strip.jpg"
    hook_source_strip = evidence / "hook_source_frame_strip.jpg"
    hook_body_signal_strip = evidence / "hook_body_signal_interruption_frame_strip.jpg"
    hook_body_seam_strip = evidence / "hook_body_seam_frame_strip.jpg"
    all_signal_boundaries_strip = evidence / "all_signal_interruption_boundaries_frame_strip.jpg"
    body_signal_boundaries_strip = evidence / "body_segment_signal_interruption_boundaries_frame_strip.jpg"
    cockpit_takeoff_order_strip = evidence / "cockpit_takeoff_order_swap_frame_strip.jpg"
    engine_flash_repair_strip = evidence / "cockpit_takeoff_engine_flash_repair_frame_strip.jpg"
    signal_tail_outro_strip = evidence / "signal_tail_outro_handoff_frame_strip.jpg"
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
        [0.0, 0.5, 1.0, 2.0, 2.9, 3.0, 3.1],
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
    cockpit_takeoff_order_frames = builder.build_frame_strip(
        proof,
        cockpit_takeoff_order_strip,
        [22.50, 23.566667, 24.50, 26.50, 27.933334, 28.50, 29.50],
    )
    engine_flash_repair_frames = builder.build_frame_strip(
        proof,
        engine_flash_repair_strip,
        [27.70, 27.90, 27.933334, 28.03, 28.20, 28.50, 28.80],
    )
    signal_start_seconds = builder.HOOK_DURATION_SECONDS + picture_bed_context["body_duration_seconds"]
    tail_start_seconds = signal_start_seconds + picture_bed_context["signal_interruption_duration_seconds"]
    tail_signal_boundary = {
        "boundary_id": "body_14_to_tail",
        "outgoing_segment_id": "14",
        "incoming_segment_id": "official_tail",
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
    signal_tail_outro_frames = builder.build_frame_strip(
        proof,
        signal_tail_outro_strip,
        [
            signal_start_seconds - 0.50,
            signal_start_seconds - 0.20,
            signal_start_seconds,
            tail_start_seconds,
            builder.OUTRO_START_SECONDS,
            tail_start_seconds + 0.50,
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
    hook_motion = framehash_sample(hook_clip, 0.0, builder.HOOK_DURATION_SECONDS, evidence / "hook_motion_framemd5.txt")
    hook_signal_motion = framehash_sample(
        proof,
        max(0.0, builder.HOOK_DURATION_SECONDS - SIGNAL_INTERRUPT_SECONDS),
        0.50,
        evidence / "hook_body_signal_interruption_motion_framemd5.txt",
        sample_rate_fps=12,
    )
    tail_motion = framehash_sample(
        proof,
        tail_start_seconds,
        max(0.25, min(3.0, builder.FINAL_DURATION_SECONDS - tail_start_seconds)),
        evidence / "tail_motion_framemd5.txt",
    )
    cockpit_takeoff_order_motion = framehash_sample(
        proof,
        23.566667,
        8.966667,
        evidence / "cockpit_takeoff_order_motion_framemd5.txt",
    )
    engine_flash_repair_motion = framehash_sample(
        proof,
        27.933334,
        1.25,
        evidence / "cockpit_takeoff_engine_flash_repair_motion_framemd5.txt",
    )
    representative_body_signal_motion = framehash_sample(
        proof,
        max(0.0, body_signal_boundary_times[0] - 0.25),
        0.50,
        evidence / "representative_body_signal_interruption_motion_framemd5.txt",
        sample_rate_fps=12,
    )
    body_tail_signal_motion = framehash_sample(
        proof,
        signal_start_seconds,
        0.50,
        evidence / "body_tail_signal_interruption_motion_framemd5.txt",
        sample_rate_fps=12,
    )
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
        "prototype_id": f"737max_theme_intro_hook_{stamp}",
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
        "all_signal_interruption_boundaries_frame_strip_path": str(all_signal_boundaries_strip),
        "all_signal_interruption_boundaries_frame_strip_sha256": builder.sha256(all_signal_boundaries_strip),
        "body_segment_signal_interruption_boundaries_frame_strip_path": str(body_signal_boundaries_strip),
        "body_segment_signal_interruption_boundaries_frame_strip_sha256": builder.sha256(body_signal_boundaries_strip),
        "cockpit_takeoff_order_frame_strip_path": str(cockpit_takeoff_order_strip),
        "cockpit_takeoff_order_frame_strip_sha256": builder.sha256(cockpit_takeoff_order_strip),
        "cockpit_takeoff_engine_flash_repair_frame_strip_path": str(engine_flash_repair_strip),
        "cockpit_takeoff_engine_flash_repair_frame_strip_sha256": builder.sha256(engine_flash_repair_strip),
        "signal_tail_outro_handoff_frame_strip_path": str(signal_tail_outro_strip),
        "signal_tail_outro_handoff_frame_strip_sha256": builder.sha256(signal_tail_outro_strip),
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
        "opening_official_aircraft_hook_read": "pass_review_required",
        "opening_last_shot_hook_read": "pass_review_required",
        "opening_uses_final_tail_shot_read": "pass_review_required",
        "engine_heavy_hook_removed_read": "pass_review_required",
        "hook_body_no_repeat_read": "pass_review_required",
        "hook_body_signal_interruption_read": "pass_review_required",
        "body_clip_order_repairs": body_context["body_clip_order_repairs"],
        "body_clip_flash_repairs": body_context["body_clip_flash_repairs"],
        "cockpit_takeoff_order_read": "pass_review_required",
        "cockpit_engine_flash_repair_read": "pass_review_required",
        "body_segment_signal_interruption_read": "pass_review_required",
        "body_tail_signal_interruption_read": "pass_review_required",
        "only_body_segments_06_07_swapped": True,
        "only_segment_06_head_flash_trimmed": True,
        "tail_motion_read": "pass_review_required",
        "full_picture_crt_continuity_read": "pass_review_required",
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "body_trimmed_for_tail_motion_seconds": picture_bed_context["body_trimmed_for_tail_motion_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "tail_start_seconds": round(tail_start_seconds, 6),
        "pass07_clean_body_context": body_context,
        "official_source_audit": {
            "audit_package_path": str(OFFICIAL_AUDIT_ROOT),
            "audit_manifest_path": str(OFFICIAL_AUDIT_MANIFEST),
            "audit_manifest_sha256": builder.sha256(OFFICIAL_AUDIT_MANIFEST),
            "hook_candidate_id": "bff_span_75_110_air_to_air_landing",
            "tail_candidate_id": "bff_span_75_110_air_to_air_landing",
            "stock_fallback_used": False,
            "trip_report_sources_used": False,
            "official_clean_spans_keep_count": 2,
            "last_shot_source_mapping": {
                "detected_proof_start_seconds": LAST_SHOT_PROOF_START_SECONDS,
                "mapped_tail_source_start_seconds": HOOK_SOURCE_START_SECONDS,
                "mapping_basis": "scene change detected in latest proof at proof 63.466667s; latest proof tail begins at 58.0s",
            },
        },
        "visual_strategy": {
            "hook_visual": "official Boeing first-flight final air-to-air tail shot moved to the front",
            "hook_source_path": str(builder.NO_CAPTION_PICTURE),
            "hook_source_start_seconds": builder.HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": builder.HOOK_DURATION_SECONDS,
            "body_after_hook": "existing pass-07 737 MAX source-segment body starts at original shot 01 after hook, with only segments 06 and 07 swapped",
            "body_source_path": str(builder.BODY_CAPTIONED_NO_AUDIO),
            "tail_visual": "official Boeing first-flight air-to-air/landing source span for moving outro tail",
            "tail_source_path": str(OFFICIAL_TAIL_SOURCE),
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
        "motion_evidence": {
            "hook_motion": hook_motion,
            "hook_body_signal_interruption_motion": hook_signal_motion,
            "cockpit_takeoff_order_motion": cockpit_takeoff_order_motion,
            "cockpit_takeoff_engine_flash_repair_motion": engine_flash_repair_motion,
            "representative_body_signal_interruption_motion": representative_body_signal_motion,
            "body_tail_signal_interruption_motion": body_tail_signal_motion,
            "tail_motion": tail_motion,
        },
        "frame_samples": {
            "opening": opening_frames,
            "hook_source": hook_source_frames,
            "hook_body_signal_interruption": hook_body_signal_frames,
            "hook_body_seam": hook_body_seam_frames,
            "all_signal_interruption_boundaries": all_signal_boundary_frames,
            "body_segment_signal_interruption_boundaries": body_signal_boundary_frames,
            "cockpit_takeoff_order": cockpit_takeoff_order_frames,
            "cockpit_takeoff_engine_flash_repair": engine_flash_repair_frames,
            "signal_tail_outro_handoff": signal_tail_outro_frames,
            "end": end_frames,
        },
        "review_request": "Judge whether opening with the final air-to-air aircraft shot plus full theme intro punch improves scroll-stop, whether the swapped cockpit takeoff clips now progress correctly, and whether the brief engine flash at the segment 07 to 06 handoff is gone.",
        "human_review_disposition": "keep|tighten|reject",
    }
    manifest_path = root / "737max_theme_intro_hook_manifest.json"
    builder.write_json(manifest_path, manifest)

    note = f"""# 737 MAX Official-Source Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `opening_frame_strip_path`: `{opening_strip}`
- `hook_source_frame_strip_path`: `{hook_source_strip}`
- `hook_body_signal_interruption_frame_strip_path`: `{hook_body_signal_strip}`
- `hook_body_seam_frame_strip_path`: `{hook_body_seam_strip}`
- `all_signal_interruption_boundaries_frame_strip_path`: `{all_signal_boundaries_strip}`
- `body_segment_signal_interruption_boundaries_frame_strip_path`: `{body_signal_boundaries_strip}`
- `cockpit_takeoff_order_frame_strip_path`: `{cockpit_takeoff_order_strip}`
- `cockpit_takeoff_engine_flash_repair_frame_strip_path`: `{engine_flash_repair_strip}`
- `signal_tail_outro_handoff_frame_strip_path`: `{signal_tail_outro_strip}`
- `end_frame_strip_path`: `{end_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{builder.HOOK_DURATION_SECONDS:.1f}s` is the clean official Boeing first-flight air-to-air shot that appears near proof `{LAST_SHOT_PROOF_START_SECONDS:.2f}s` in the prior proof, starting at source `{builder.HOOK_SOURCE_START_SECONDS:.6f}s`.
- The full theme song starts from `0.00` so the opening punch lands immediately.
- The theme intro crossfades into the registered loop from `{builder.LOOP_START_SECONDS:.2f}s` to `{builder.LOOP_START_SECONDS + builder.LOOP_CROSSFADE_SECONDS:.2f}s`.
- The approved 737 MAX voice starts after the hook at `{builder.VOICE_DELAY_SECONDS:.2f}s`.
- The body is rebuilt from the existing pass-07 `source_segment_no_audio` clips, preserving the existing order except for the targeted `06`/`07` swap.
- Body segments `06` and `07` are swapped so the land-out-the-window takeoff cockpit view starts around proof `23.57s`, and the earlier cockpit angle starts around proof `27.93s`.
- The brief engine flash at the head of segment `06` is trimmed by `{SEGMENT_06_HEAD_FLASH_TRIM_SECONDS:.2f}s`; the remaining segment motion is subtly retimed to preserve the original body duration.
- The existing `{SIGNAL_INTERRUPT_SECONDS:.2f}s` analog signal interruption now appears at every clip boundary by replacing the outgoing clip tail, not adding runtime.
- Signal boundaries are applied at hook -> segment `01`, all body segment boundaries, and segment `14` -> tail.
- One continuous full-picture CRT pass is applied after hook/body/tail assembly.
- A `{picture_bed_context["signal_interruption_duration_seconds"]:.2f}s` signal interruption hands off to moving official Boeing air-to-air/landing source tail footage.
- The engine-closeup-heavy hook/tail sources from the prior proof are not used.
- The source span choices come from `{OFFICIAL_AUDIT_MANIFEST}`.
- The ending tail remains unchanged and still starts at source `{TAIL_SOURCE_START_SECONDS:.2f}s`.
- Final caption rebuilding remains deferred; this package is for local hook, timing, and texture review only.

## Review Read

- `opening_official_aircraft_hook_read`: `pass_review_required`
- `opening_last_shot_hook_read`: `pass_review_required`
- `opening_uses_final_tail_shot_read`: `pass_review_required`
- `engine_heavy_hook_removed_read`: `pass_review_required`
- `hook_body_no_repeat_read`: `pass_review_required`
- `hook_body_signal_interruption_read`: `pass_review_required`
- `cockpit_takeoff_order_read`: `pass_review_required`
- `cockpit_engine_flash_repair_read`: `pass_review_required`
- `body_segment_signal_interruption_read`: `pass_review_required`
- `body_tail_signal_interruption_read`: `pass_review_required`
- `signal_interruption_boundary_count`: `{len(signal_boundaries)}`
- `only_body_segments_06_07_swapped`: `true`
- `only_segment_06_head_flash_trimmed`: `true`
- `tail_motion_read`: `{tail_motion["read"]}`
- `full_picture_crt_continuity_read`: `pass_review_required`
- `cloned_frame_padding_used`: `{str(picture_bed_context["cloned_frame_padding_used"]).lower()}`
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`

Mark this `keep`, `tighten`, or `reject`.
"""
    builder.write_text(root / "review_note.md", note)

    latest_link = builder.OUTPUT_ROOT / "737max_theme_intro_hook_latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
