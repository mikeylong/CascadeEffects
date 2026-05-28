#!/usr/bin/env python3
"""Build a local Piltdown Man proof with skull-face hook plus theme-intro music."""

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


PILTDOWN_VIZ_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/piltdown-man/shorts/"
    "piltdown_man_short_scoped_v1"
)
PILTDOWN_PASS03_ROOT = PILTDOWN_VIZ_ROOT / "motion_video_proof/pass_03_no_freeze_legibility_repair"
PILTDOWN_PASS03_SEGMENTS_DIR = PILTDOWN_PASS03_ROOT / "shot_clips_no_audio"
PILTDOWN_HOOK_SOURCE = (
    PILTDOWN_VIZ_ROOT
    / "visual_research/youtube_archival_review_pass_01/candidates/clips/"
    "pil-arc-11__skull_hands_museum__yt_pil_03_banijay_greatest_hoaxes.no_audio.mp4"
)
PILTDOWN_BODY_SOURCE = (
    PILTDOWN_PASS03_ROOT / "piltdown_motion_video_proof_pass_03_no_freeze_legibility_video_only.mp4"
)
PILTDOWN_TAIL_SOURCE = PILTDOWN_HOOK_SOURCE
PILTDOWN_BODY_REPAIR_SOURCE = (
    PILTDOWN_VIZ_ROOT
    / "visual_research/archival_expanded_9x16_pass_02/vertical_clips/"
    "09__pil-arc-09__expert_holding_skull__9x16_review.mp4"
)
BODY_REPAIR_SEGMENT_PREFIX = "15__shot_11_skull_jaw_reveal__pil-arc-06-clean"
HOOK_SOURCE_START_SECONDS = 11.0
TAIL_SOURCE_START_SECONDS = 9.20


def configure_piltdown() -> None:
    short_root = Path("/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts/piltdown_man_short_scoped_v1")
    latest_publish = short_root / "publish/youtube_20260518T174506Z_pass07_visible_scanline"
    builder.SHORT_ROOT = short_root
    builder.LATEST_PUBLISH_DIR = latest_publish
    builder.CURRENT_YOUTUBE_SHORT = latest_publish / "piltdown_man_fossil_hoax_youtube_short.mp4"
    builder.BODY_CAPTIONED_NO_AUDIO = PILTDOWN_BODY_SOURCE
    builder.NO_CAPTION_PICTURE = PILTDOWN_HOOK_SOURCE
    builder.VOICE_WAV = short_root / "final/piltdown_man_short_scoped_v1.wav"
    builder.HOOK_SOURCE_START_SECONDS = HOOK_SOURCE_START_SECONDS
    builder.HOOK_DURATION_SECONDS = 3.0
    builder.THEME_INTRO_SECONDS = 3.0
    builder.LOOP_START_SECONDS = 2.25
    builder.LOOP_CROSSFADE_SECONDS = 0.75
    builder.VOICE_DELAY_SECONDS = 3.0
    builder.VOICE_LAST_AUDIBLE_SECONDS = 57.970544
    builder.OUTRO_START_SECONDS = 61.070544
    builder.FINAL_DURATION_SECONDS = 68.050544
    builder.HOOK_CRT_TEXTURE = None
    builder.FULL_PICTURE_CRT_TEXTURE = {
        "profile_id": "era_1980s_broadcast_crt_v1",
        "intensity": "visible_but_premium",
        "purpose": "apply one continuous CRT/analog texture over the assembled Piltdown hook, body, and tail proof",
        "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
        "scanline_strength_variant_id": "max_visible_bars_y24_p8",
        "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
    }
    builder.SOURCE_MOTION_TAIL = {
        "path": PILTDOWN_TAIL_SOURCE,
        "start_seconds": TAIL_SOURCE_START_SECONDS,
        "description": "moving no-audio Piltdown skull/hands source tail returning to the opening source clip",
        "house_crt_tail_texture": None,
        "signal_interruption": {
            "profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
            "duration_seconds": 0.25,
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "full_frame_static_replacement_used": False,
            "purpose": "brief analog interruption between the repaired body and same-source skull/hands tail motion",
        },
    }


def require_inputs() -> None:
    for path in (
        builder.CURRENT_YOUTUBE_SHORT,
        builder.VOICE_WAV,
        builder.THEME_FULL,
        builder.THEME_LOOP_60,
        builder.THEME_OUTRO,
        PILTDOWN_HOOK_SOURCE,
        PILTDOWN_BODY_SOURCE,
        PILTDOWN_TAIL_SOURCE,
        PILTDOWN_BODY_REPAIR_SOURCE,
    ):
        if not Path(path).exists():
            raise FileNotFoundError(str(path))
    if not PILTDOWN_PASS03_SEGMENTS_DIR.exists():
        raise FileNotFoundError(str(PILTDOWN_PASS03_SEGMENTS_DIR))


def framehash_sample(video: Path, start_seconds: float, duration_seconds: float, output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
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
            "fps=2,scale=180:320:force_original_aspect_ratio=increase,crop=180:320,format=yuv420p",
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
        if parts:
            hashes.append(parts[-1])
    unique_hashes = sorted(set(hashes))
    return {
        "path": str(output),
        "sha256": builder.sha256(output),
        "start_seconds": round(start_seconds, 6),
        "duration_seconds": round(duration_seconds, 6),
        "sample_rate_fps": 2,
        "sample_count": len(hashes),
        "unique_hash_count": len(unique_hashes),
        "read": "pass" if len(unique_hashes) > 1 else "tighten",
        "ffmpeg_stdout": proc.stdout.strip(),
    }


def render_full_bleed_segment(source: Path, output: Path, duration_seconds: float) -> None:
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
                f"trim=0:{duration_seconds:.6f},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,setsar=1,fps=30,format=yuv420p"
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
    segments = sorted(PILTDOWN_PASS03_SEGMENTS_DIR.glob("*.mp4"))
    if len(segments) != 21:
        raise RuntimeError(f"Expected 21 Piltdown pass-03 segments, found {len(segments)}")

    repaired_segments_dir = work / "full_bleed_body_repair_segments"
    concat_path = work / "concat_piltdown_full_bleed_body_repair.txt"
    repaired_body = work / "piltdown_full_bleed_body_repaired_no_audio.mp4"
    concat_segments: list[Path] = []
    body_full_bleed_repairs: list[dict[str, Any]] = []
    body_cursor = 0.0

    for segment in segments:
        target_duration = builder.duration(segment)
        if segment.name.startswith(BODY_REPAIR_SEGMENT_PREFIX):
            repaired_segment = repaired_segments_dir / segment.name.replace("__pil-arc-06-clean", "__full_bleed_repair")
            render_full_bleed_segment(PILTDOWN_BODY_REPAIR_SOURCE, repaired_segment, target_duration)
            concat_segments.append(repaired_segment)
            body_full_bleed_repairs.append(
                {
                    "clip_id": BODY_REPAIR_SEGMENT_PREFIX,
                    "original_segment_path": str(segment),
                    "original_segment_sha256": builder.sha256(segment),
                    "replacement_source_path": str(PILTDOWN_BODY_REPAIR_SOURCE),
                    "replacement_source_sha256": builder.sha256(PILTDOWN_BODY_REPAIR_SOURCE),
                    "normalized_replacement_path": str(repaired_segment),
                    "normalized_replacement_sha256": builder.sha256(repaired_segment),
                    "target_slot_duration_seconds": round(target_duration, 6),
                    "body_timeline_start_seconds": round(body_cursor, 6),
                    "body_timeline_end_seconds": round(body_cursor + target_duration, 6),
                    "proof_timeline_start_seconds": round(builder.HOOK_DURATION_SECONDS + body_cursor, 6),
                    "proof_timeline_end_seconds": round(
                        builder.HOOK_DURATION_SECONDS + body_cursor + target_duration,
                        6,
                    ),
                    "full_bleed_normalization": (
                        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
                    ),
                    "repair_reason": "remove_internal_matte_full_bleed_offender",
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
    if len(body_full_bleed_repairs) != 1:
        raise RuntimeError(f"Expected exactly one full-bleed body repair, found {len(body_full_bleed_repairs)}")
    return {
        "repaired_body_path": str(repaired_body),
        "repaired_body_sha256": builder.sha256(repaired_body),
        "repaired_body_duration_seconds": round(builder.duration(repaired_body), 6),
        "source_segments_dir": str(PILTDOWN_PASS03_SEGMENTS_DIR),
        "concat_path": str(concat_path),
        "body_full_bleed_repairs": body_full_bleed_repairs,
        "only_full_bleed_offenders_changed": True,
        "full_bleed_audit_read": "pass_review_required",
    }


def main() -> None:
    configure_piltdown()
    require_inputs()
    stamp = builder.utc_stamp()
    root = builder.OUTPUT_ROOT / f"piltdown_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    hook_clip = work / "piltdown_skull_face_full_bleed_hook_clean_no_audio_3s.mp4"
    picture_bed = work / "picture_bed_skull_face_full_picture_crt_no_caption.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "piltdown_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_piltdown_theme_hook_first_10s.mp4"
    opening_strip = evidence / "opening_frame_strip.jpg"
    hook_source_strip = evidence / "hook_source" / "hook_source_frame_strip.jpg"
    hook_crop_letterbox_strip = evidence / "hook_crop_letterbox" / "hook_crop_letterbox_frame_strip.jpg"
    hook_body_seam_strip = evidence / "hook_body_seam_frame_strip.jpg"
    repaired_body_strip = evidence / "repaired_body_full_bleed_frame_strip.jpg"
    signal_tail_outro_strip = evidence / "signal_tail_outro_handoff_frame_strip.jpg"
    tail_start_end_strip = evidence / "tail_start_end_same_source_frame_strip.jpg"
    end_strip = evidence / "end_frame_strip.jpg"
    waveform = evidence / "first_10s_waveform.png"

    body_repair_context = build_repaired_body(work)
    builder.BODY_CAPTIONED_NO_AUDIO = Path(body_repair_context["repaired_body_path"])
    hook_context = builder.build_hook_clip(hook_clip)
    picture_bed_context = builder.build_picture_bed(hook_clip, picture_bed)
    builder.build_audio_mix(audio_mix)
    builder.mux(picture_bed, audio_mix, proof)
    builder.extract_excerpt(builder.CURRENT_YOUTUBE_SHORT, 10.0, current_excerpt)
    builder.extract_excerpt(proof, 10.0, revised_excerpt)
    builder.build_comparison(current_excerpt, revised_excerpt, comparison)

    opening_frames = builder.build_frame_strip(
        proof,
        opening_strip,
        [0.0, 0.25, 0.5, 1.0, 2.0, 2.9, 3.0, 3.1, 4.0, 6.0, 10.0],
    )
    hook_source_frames = builder.build_frame_strip(
        builder.NO_CAPTION_PICTURE,
        hook_source_strip,
        [11.0, 11.25, 11.5, 12.0, 13.0, 13.9],
    )
    hook_crop_letterbox_frames = builder.build_frame_strip(
        proof,
        hook_crop_letterbox_strip,
        [0.0, 0.25, 0.5, 1.0, 2.0, 2.9],
    )
    hook_body_seam_frames = builder.build_frame_strip(
        proof,
        hook_body_seam_strip,
        [2.70, 2.90, 3.00, 3.10, 3.30],
    )
    repaired_body_repair = body_repair_context["body_full_bleed_repairs"][0]
    repaired_start = repaired_body_repair["proof_timeline_start_seconds"]
    repaired_end = repaired_body_repair["proof_timeline_end_seconds"]
    repaired_body_frames = builder.build_frame_strip(
        proof,
        repaired_body_strip,
        [44.0, repaired_start, repaired_start + 0.50, repaired_start + 1.50, repaired_end - 0.10, 48.5],
    )
    tail_start_seconds = (
        builder.HOOK_DURATION_SECONDS
        + picture_bed_context["body_duration_seconds"]
        + picture_bed_context["signal_interruption_duration_seconds"]
    )
    signal_start_seconds = builder.HOOK_DURATION_SECONDS + picture_bed_context["body_duration_seconds"]
    signal_tail_outro_frames = builder.build_frame_strip(
        proof,
        signal_tail_outro_strip,
        [
            builder.OUTRO_START_SECONDS - 0.50,
            builder.OUTRO_START_SECONDS,
            signal_start_seconds - 0.10,
            signal_start_seconds,
            tail_start_seconds,
            tail_start_seconds + 0.50,
            builder.FINAL_DURATION_SECONDS - 0.50,
        ],
    )
    tail_start_end_frames = builder.build_frame_strip(
        proof,
        tail_start_end_strip,
        [
            tail_start_seconds,
            tail_start_seconds + 0.50,
            tail_start_seconds + 2.0,
            builder.FINAL_DURATION_SECONDS - 1.50,
            builder.FINAL_DURATION_SECONDS - 0.75,
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
        "hook": framehash_sample(proof, 0.0, builder.HOOK_DURATION_SECONDS, evidence / "hook_motion_framemd5.txt"),
        "repaired_body_full_bleed_segment": framehash_sample(
            proof,
            repaired_start,
            min(3.0, max(0.25, repaired_end - repaired_start)),
            evidence / "repaired_body_full_bleed_motion_framemd5.txt",
        ),
        "tail": framehash_sample(
            proof,
            tail_start_seconds,
            min(3.0, max(0.25, builder.FINAL_DURATION_SECONDS - tail_start_seconds)),
            evidence / "tail_motion_framemd5.txt",
        ),
    }

    manifest = {
        "schema_version": "1.0",
        "stage": "first-second hook review",
        "prototype_id": f"piltdown_theme_intro_hook_{stamp}",
        "local_only_no_youtube_action": True,
        "episode_id": "piltdown-man",
        "short_id": "piltdown_man_short_scoped_v1",
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
        "hook_crop_letterbox_frame_strip_path": str(hook_crop_letterbox_strip),
        "hook_crop_letterbox_frame_strip_sha256": builder.sha256(hook_crop_letterbox_strip),
        "hook_body_seam_frame_strip_path": str(hook_body_seam_strip),
        "hook_body_seam_frame_strip_sha256": builder.sha256(hook_body_seam_strip),
        "repaired_body_full_bleed_frame_strip_path": str(repaired_body_strip),
        "repaired_body_full_bleed_frame_strip_sha256": builder.sha256(repaired_body_strip),
        "signal_tail_outro_handoff_frame_strip_path": str(signal_tail_outro_strip),
        "signal_tail_outro_handoff_frame_strip_sha256": builder.sha256(signal_tail_outro_strip),
        "tail_start_end_same_source_frame_strip_path": str(tail_start_end_strip),
        "tail_start_end_same_source_frame_strip_sha256": builder.sha256(tail_start_end_strip),
        "end_frame_strip_path": str(end_strip),
        "end_frame_strip_sha256": builder.sha256(end_strip),
        "waveform_path": str(waveform),
        "waveform_sha256": builder.sha256(waveform),
        "visual_extension_mode": picture_bed_context["visual_extension_mode"],
        "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
        "source_motion_tail": picture_bed_context["source_motion_tail"],
        "signal_interruption": picture_bed_context["signal_interruption"],
        "full_picture_crt_texture": picture_bed_context["full_picture_crt_texture"],
        "full_picture_crt_scope": picture_bed_context["full_picture_crt_scope"],
        "segment_crt_passes_used": picture_bed_context["segment_crt_passes_used"],
        "caption_layer_policy": "local_review_no_final_caption_rebuild",
        "paper_architecture_visual_style_read": "pass_not_used",
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "body_trimmed_for_tail_motion_seconds": picture_bed_context["body_trimmed_for_tail_motion_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "tail_start_seconds": round(tail_start_seconds, 6),
        "signal_start_seconds": round(signal_start_seconds, 6),
        "opening_closing_source_path_match": str(PILTDOWN_HOOK_SOURCE) == str(PILTDOWN_TAIL_SOURCE),
        "closing_returns_to_opening_clip": True,
        "closing_tail_source_start_seconds": TAIL_SOURCE_START_SECONDS,
        "closing_ends_on_skull_face_read": "pass_review_required",
        "body_full_bleed_repairs": body_repair_context["body_full_bleed_repairs"],
        "full_bleed_audit_read": body_repair_context["full_bleed_audit_read"],
        "only_full_bleed_offenders_changed": body_repair_context["only_full_bleed_offenders_changed"],
        "repaired_body_context": body_repair_context,
        "opening_skull_jaw_hook_read": "superseded_by_skull_face_full_bleed_repair",
        "opening_skull_face_visible_read": "pass_review_required",
        "opening_full_bleed_read": "pass_review_required",
        "hook_internal_letterbox_read": "pass_review_required",
        "hook_repair_reason": "skull_face_full_bleed_opening",
        "opening_texture_match_read": "pass_review_required",
        "hook_body_seam_read": "pass_review_required",
        "tail_motion_read": motion_evidence["tail"]["read"],
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "motion_evidence": motion_evidence,
        "visual_strategy": {
            "hook_visual": "Piltdown skull face full-bleed source motion moved to the front",
            "hook_source_path": str(PILTDOWN_HOOK_SOURCE),
            "hook_source_start_seconds": builder.HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": builder.HOOK_DURATION_SECONDS,
            "opening_closing_source_path_match": str(PILTDOWN_HOOK_SOURCE) == str(PILTDOWN_TAIL_SOURCE),
            "hook_full_bleed_normalization": (
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
            ),
            "hook_letterbox_policy": "no_pad_no_pillarbox_no_blur_matte_no_letterbox",
            "body_after_hook": "pass-03 body rebuilt from segments with only the internal-matte offender repaired",
            "body_source_path": body_repair_context["repaired_body_path"],
            "original_body_source_path": str(PILTDOWN_BODY_SOURCE),
            "body_full_bleed_repairs": body_repair_context["body_full_bleed_repairs"],
            "tail_source_path": str(PILTDOWN_TAIL_SOURCE),
            "tail_source_start_seconds": TAIL_SOURCE_START_SECONDS,
            "source_motion_tail": picture_bed_context["source_motion_tail"],
            "full_picture_crt_scope": picture_bed_context["full_picture_crt_scope"],
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
            "hook_source": hook_source_frames,
            "hook_crop_letterbox": hook_crop_letterbox_frames,
            "hook_body_seam": hook_body_seam_frames,
            "repaired_body_full_bleed": repaired_body_frames,
            "signal_tail_outro": signal_tail_outro_frames,
            "tail_start_end_same_source": tail_start_end_frames,
            "end": end_frames,
        },
        "review_request": "Judge whether the skull-face full-bleed opening plus full theme intro punch improves scroll-stop, whether the repaired body segment removes the old internal matte, and whether returning to the same skull/hands source at the end feels right.",
        "human_review_disposition": "keep|tighten|reject",
    }
    builder.write_json(root / "piltdown_theme_intro_hook_manifest.json", manifest)

    note = f"""# Piltdown Man Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `opening_frame_strip_path`: `{opening_strip}`
- `hook_source_frame_strip_path`: `{hook_source_strip}`
- `hook_crop_letterbox_frame_strip_path`: `{hook_crop_letterbox_strip}`
- `hook_body_seam_frame_strip_path`: `{hook_body_seam_strip}`
- `repaired_body_full_bleed_frame_strip_path`: `{repaired_body_strip}`
- `signal_tail_outro_handoff_frame_strip_path`: `{signal_tail_outro_strip}`
- `tail_start_end_same_source_frame_strip_path`: `{tail_start_end_strip}`
- `end_frame_strip_path`: `{end_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{builder.HOOK_DURATION_SECONDS:.1f}s` is the Piltdown skull-face source clip, starting at source `{builder.HOOK_SOURCE_START_SECONDS:.2f}s`.
- The hook is normalized full-bleed with `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`; no pad, pillarbox, blur-matte, or letterbox treatment is used.
- The ending tail returns to the same skull/hands source clip, starting at source `{TAIL_SOURCE_START_SECONDS:.2f}s`.
- The full theme song starts from `0.00` so the opening punch lands immediately.
- The theme intro crossfades into the registered loop from `{builder.LOOP_START_SECONDS:.2f}s` to `{builder.LOOP_START_SECONDS + builder.LOOP_CROSSFADE_SECONDS:.2f}s`.
- The approved Piltdown voice starts at `{builder.VOICE_DELAY_SECONDS:.2f}s`.
- A single full-picture CRT pass is applied after hook/body/tail assembly.
- The pass-03 body was rebuilt from shot clips with only the old internal-matte skull/jaw reveal slot replaced by a full-bleed existing motion clip.
- The body-to-tail handoff uses a `{picture_bed_context["signal_interruption_duration_seconds"]:.2f}s` signal interruption.
- The outro tail uses source motion from the same skull/hands source family as the opening; cloned-frame padding is not used.
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`
- `tail_motion_read`: `{motion_evidence["tail"]["read"]}`

## Review Read

Mark this `keep`, `tighten`, or `reject`.

- `keep`: skull-face full-bleed opening plus theme punch clearly improves scroll-stop, the repaired body clip removes the old matte, and the ending return feels intentional.
- `tighten`: the idea works, but the hook span, repaired body slot, music level, CRT strength, signal handoff, or ending source span needs adjustment.
- `reject`: it feels cheap, confusing, too loud, or less effective than the current opening.
"""
    builder.write_text(root / "review_note.md", note)

    latest_link = builder.OUTPUT_ROOT / "piltdown_theme_intro_hook_latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
