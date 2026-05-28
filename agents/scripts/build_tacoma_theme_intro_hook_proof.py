#!/usr/bin/env python3
"""Build a local Tacoma Narrows proof with roadway-twist source motion plus theme-intro music."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


BASE_SCRIPT = Path("/Users/mike/Agents_CascadeEffects/scripts/build_challenger_explosion_theme_intro_hook_proof.py")
spec = importlib.util.spec_from_file_location("theme_hook_builder", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to import {BASE_SCRIPT}")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


TACOMA_PASS07_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/"
    "tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/"
    "tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
    "20260429T_house_crt_visible_scanline_first8_pass07_y24"
)
TACOMA_HOOK_SOURCE = (
    TACOMA_PASS07_ROOT
    / "work/segments/08_shot_08_roadway_twist__house_crt_visible_scanline_signal_interruption.mp4"
)
TACOMA_BODY_SOURCE = TACOMA_PASS07_ROOT / "work/motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
TACOMA_TAIL_SOURCE = (
    TACOMA_PASS07_ROOT
    / "work/segments/07_shot_07_torsion_flexible_deck__house_crt_visible_scanline_signal_interruption.mp4"
)


def configure_tacoma() -> None:
    short_root = Path("/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts/tacoma_short_scoped_v1")
    latest_publish = short_root / "publish/youtube_20260428T232642Z"
    builder.SHORT_ROOT = short_root
    builder.LATEST_PUBLISH_DIR = latest_publish
    builder.CURRENT_YOUTUBE_SHORT = latest_publish / "tacoma_galloping_gertie_pass07_no_freeze_youtube_short.mp4"
    builder.BODY_CAPTIONED_NO_AUDIO = TACOMA_BODY_SOURCE
    builder.NO_CAPTION_PICTURE = TACOMA_HOOK_SOURCE
    builder.VOICE_WAV = short_root / "final/tacoma_short_scoped_v1.wav"
    builder.HOOK_SOURCE_START_SECONDS = 0.0
    builder.HOOK_DURATION_SECONDS = 3.0
    builder.THEME_INTRO_SECONDS = 3.0
    builder.LOOP_START_SECONDS = 2.25
    builder.LOOP_CROSSFADE_SECONDS = 0.75
    builder.VOICE_DELAY_SECONDS = 3.0
    builder.VOICE_LAST_AUDIBLE_SECONDS = 58.456576
    builder.OUTRO_START_SECONDS = builder.VOICE_DELAY_SECONDS + builder.VOICE_LAST_AUDIBLE_SECONDS + 0.10
    builder.FINAL_DURATION_SECONDS = builder.OUTRO_START_SECONDS + 6.98
    builder.HOOK_CRT_TEXTURE = None
    builder.FULL_PICTURE_CRT_TEXTURE = None
    builder.SOURCE_MOTION_TAIL = {
        "path": TACOMA_TAIL_SOURCE,
        "start_seconds": 0.0,
        "description": "moving no-audio Tacoma Narrows bridge torsion source tail for the full theme outro",
        "house_crt_tail_texture": None,
    }


def main() -> None:
    configure_tacoma()
    stamp = builder.utc_stamp()
    root = builder.OUTPUT_ROOT / f"tacoma_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    hook_clip = work / "tacoma_roadway_twist_hook_existing_crt_no_audio_3s.mp4"
    picture_bed = work / "picture_bed_roadway_twist_then_pass07_existing_crt_no_audio.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "tacoma_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_tacoma_theme_hook_first_10s.mp4"
    opening_strip = evidence / "opening_frame_strip.jpg"
    hook_source_strip = evidence / "hook_source_frame_strip.jpg"
    hook_body_seam_strip = evidence / "hook_body_seam_frame_strip.jpg"
    tail_continuity_strip = evidence / "tail_continuity_frame_strip.jpg"
    end_strip = evidence / "end_frame_strip.jpg"
    waveform = evidence / "first_10s_waveform.png"

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
        [0.0, 0.5, 1.0, 2.0, 2.9, 3.0, 3.1, 4.0, 6.0, 10.0],
    )
    hook_source_frames = builder.build_frame_strip(
        hook_clip,
        hook_source_strip,
        [0.0, 1.0, 2.0, 2.8],
    )
    hook_body_seam_frames = builder.build_frame_strip(
        proof,
        hook_body_seam_strip,
        [2.70, 2.90, 3.00, 3.10, 3.30],
    )
    tail_start_seconds = builder.HOOK_DURATION_SECONDS + picture_bed_context["body_duration_seconds"]
    tail_continuity_frames = builder.build_frame_strip(
        proof,
        tail_continuity_strip,
        [
            builder.OUTRO_START_SECONDS - 0.50,
            builder.OUTRO_START_SECONDS,
            tail_start_seconds - 0.50,
            tail_start_seconds,
            tail_start_seconds + 0.50,
            tail_start_seconds + 1.25,
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
        "prototype_id": f"tacoma_theme_intro_hook_{stamp}",
        "local_only_no_youtube_action": True,
        "episode_id": "tacoma-narrows",
        "short_id": "tacoma_short_scoped_v1",
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
        "hook_body_seam_frame_strip_path": str(hook_body_seam_strip),
        "hook_body_seam_frame_strip_sha256": builder.sha256(hook_body_seam_strip),
        "tail_continuity_frame_strip_path": str(tail_continuity_strip),
        "tail_continuity_frame_strip_sha256": builder.sha256(tail_continuity_strip),
        "end_frame_strip_path": str(end_strip),
        "end_frame_strip_sha256": builder.sha256(end_strip),
        "waveform_path": str(waveform),
        "waveform_sha256": builder.sha256(waveform),
        "visual_extension_mode": picture_bed_context["visual_extension_mode"],
        "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
        "source_motion_tail": picture_bed_context["source_motion_tail"],
        "caption_layer_policy": "local_review_no_final_caption_rebuild",
        "existing_crt_texture_source": "tacoma_pass07_house_crt_visible_scanline_signal_interruption",
        "additional_crt_pass_used": False,
        "hook_crt_texture": hook_context["hook_crt_texture"],
        "opening_roadway_twist_hook_read": "pass_review_required",
        "opening_texture_match_read": "pass_review_required",
        "hook_body_seam_read": "pass_review_required",
        "tail_motion_read": "pass_review_required",
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "visual_strategy": {
            "hook_visual": "Tacoma Narrows roadway twist source motion moved to the front",
            "hook_source_path": str(builder.NO_CAPTION_PICTURE),
            "hook_source_start_seconds": builder.HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": builder.HOOK_DURATION_SECONDS,
            "body_after_hook": "approved pass-07 Tacoma no-audio motion bed starts at original t=0 after hook",
            "body_source_path": str(builder.BODY_CAPTIONED_NO_AUDIO),
            "tail_source_path": str(TACOMA_TAIL_SOURCE),
            "existing_crt_texture_source": "tacoma_pass07_house_crt_visible_scanline_signal_interruption",
            "additional_crt_pass_used": False,
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
            "hook_body_seam": hook_body_seam_frames,
            "tail_continuity": tail_continuity_frames,
            "end": end_frames,
        },
        "review_request": "Judge whether Tacoma roadway-twist motion plus full theme intro punch improves scroll-stop, and whether the transition into the loop feels natural before voice starts.",
        "human_review_disposition": "keep|tighten|reject",
    }
    builder.write_json(root / "tacoma_theme_intro_hook_manifest.json", manifest)

    note = f"""# Tacoma Narrows Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `opening_frame_strip_path`: `{opening_strip}`
- `hook_source_frame_strip_path`: `{hook_source_strip}`
- `hook_body_seam_frame_strip_path`: `{hook_body_seam_strip}`
- `tail_continuity_frame_strip_path`: `{tail_continuity_strip}`
- `end_frame_strip_path`: `{end_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{builder.HOOK_DURATION_SECONDS:.1f}s` is existing pass-07 Tacoma roadway-twist motion.
- The full theme song starts from `0.00` so the opening punch lands immediately.
- The theme intro crossfades into the registered loop from `{builder.LOOP_START_SECONDS:.2f}s` to `{builder.LOOP_START_SECONDS + builder.LOOP_CROSSFADE_SECONDS:.2f}s`.
- The approved Tacoma Narrows voice starts after the hook at `{builder.VOICE_DELAY_SECONDS:.2f}s`.
- The loop continues under the body, then fades into the theme outro at `{builder.OUTRO_START_SECONDS:.2f}s`.
- Visuals use existing pass-07 CRT/signal-interruption treatment; no additional CRT pass is stacked on top.
- Any needed full-outro visual extension uses moving bridge-torsion source footage, not cloned-frame padding.
- Final caption rebuilding remains deferred; this package is for local hook, timing, and texture review only.
- `opening_roadway_twist_hook_read`: `pass_review_required`
- `opening_texture_match_read`: `pass_review_required`
- `hook_body_seam_read`: `pass_review_required`
- `tail_motion_read`: `pass_review_required`
- `cloned_frame_padding_used`: `{str(picture_bed_context["cloned_frame_padding_used"]).lower()}`
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`

## Review Read

Mark this `keep`, `tighten`, or `reject`.

- `keep`: roadway-twist motion plus theme punch improves scroll-stop and the loop handoff feels natural.
- `tighten`: the idea works, but the hook span, music level, seam, or outro tail needs adjustment.
- `reject`: it feels too loud, tonally wrong, or less effective than the current opening.
"""
    builder.write_text(root / "review_note.md", note)

    latest_link = builder.OUTPUT_ROOT / "tacoma_theme_intro_hook_latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
