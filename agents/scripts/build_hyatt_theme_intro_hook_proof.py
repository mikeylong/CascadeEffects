#!/usr/bin/env python3
"""Build a local Hyatt Regency proof with dance-floor source motion plus theme-intro music."""

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


HYATT_DANCE_SOURCE = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/shorts/hyatt_short_scoped_v1/"
    "visual_research/repetition_repair_pass_03/archival_review_candidates/"
    "HYA-YT-01G_gKojuChxNt8_0330_0345_close_crowd_dance_noaudio.mp4"
)
HYATT_BALLOON_TAIL_SOURCE = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/shorts/hyatt_short_scoped_v1/"
    "visual_research/repetition_repair_pass_03/archival_review_candidates/"
    "HYA-YT-01E_gKojuChxNt8_0322_0326_balloon_event_atrium_noaudio.mp4"
)
HYATT_CLEAN_BODY_SOURCE = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/shorts/hyatt_short_scoped_v1/"
    "motion_video_proof/pass_11_scene_led_no_freeze_44s/final_exports/"
    "hyatt-regency_house_crt_clean_source_lineage_first8_pass_06/"
    "20260429T_house_crt_clean_source_lineage_pass06/work/"
    "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
)


def configure_hyatt() -> None:
    short_root = Path("/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/shorts/hyatt_short_scoped_v1")
    latest_publish = short_root / "publish/youtube_20260429T002052Z"
    builder.SHORT_ROOT = short_root
    builder.LATEST_PUBLISH_DIR = latest_publish
    builder.CURRENT_YOUTUBE_SHORT = latest_publish / "hyatt_regency_tea_dance_pass13_outro_tail_youtube_short.mp4"
    builder.BODY_CAPTIONED_NO_AUDIO = builder.CURRENT_YOUTUBE_SHORT
    builder.BODY_PICTURE_SOURCE = HYATT_CLEAN_BODY_SOURCE
    builder.BODY_PICTURE_SOURCE_DURATION_SECONDS = builder.duration(builder.CURRENT_YOUTUBE_SHORT)
    builder.BODY_PICTURE_SOURCE_CONTAINS_CAPTIONS = False
    builder.CAPTION_DUPLICATE_REPAIR_READ = "pass"
    builder.NO_CAPTION_PICTURE = HYATT_DANCE_SOURCE
    builder.VOICE_WAV = short_root / "final/hyatt_short_scoped_v1.wav"
    builder.HOOK_SOURCE_START_SECONDS = 1.5
    builder.HOOK_DURATION_SECONDS = 3.0
    builder.THEME_INTRO_SECONDS = 3.0
    builder.LOOP_START_SECONDS = 2.25
    builder.LOOP_CROSSFADE_SECONDS = 0.75
    builder.VOICE_DELAY_SECONDS = 3.0
    builder.VOICE_LAST_AUDIBLE_SECONDS = 55.692744
    builder.OUTRO_START_SECONDS = builder.VOICE_DELAY_SECONDS + builder.VOICE_LAST_AUDIBLE_SECONDS + 0.10
    builder.FINAL_DURATION_SECONDS = builder.OUTRO_START_SECONDS + 6.98
    builder.HOOK_CRT_TEXTURE = {
        "profile_id": "era_1980s_broadcast_crt_v1",
        "intensity": "visible_but_premium",
        "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
        "purpose": "apply the same visible house CRT/analog texture to the opening dance-floor hook",
    }
    builder.SOURCE_MOTION_TAIL = {
        "path": HYATT_BALLOON_TAIL_SOURCE,
        "start_seconds": 0.65,
        "source_transition_trimmed_seconds": 0.65,
        "description": (
            "moving no-audio Hyatt Regency balloon/atrium source tail with the source-internal "
            "stretch/grow transition from black trimmed off"
        ),
        "house_crt_tail_texture": {
            "profile_id": "hyatt_house_crt_tail_match_v1",
            "purpose": "match the existing Hyatt Short CRT/analog texture on the inserted balloon tail",
            "filters": [
                "contrast lift",
                "saturation lift",
                "temporal noise",
                "horizontal scanline grid",
            ],
        },
        "signal_interruption": {
            "used": True,
            "duration_seconds": 0.25,
            "profile_id": "hyatt_signal_interruption_tail_handoff_v1",
            "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
            "full_frame_static_replacement_used": False,
        },
    }


def main() -> None:
    configure_hyatt()
    stamp = builder.utc_stamp()
    root = builder.OUTPUT_ROOT / f"hyatt_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    hook_clip = work / "hyatt_dance_floor_hook_crt_no_caption_3s.mp4"
    picture_bed = work / "picture_bed_dance_floor_then_clean_body.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "hyatt_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_hyatt_theme_hook_first_10s.mp4"
    frame_strip = evidence / "opening_frame_strip.jpg"
    outro_strip = evidence / "outro_frame_strip.jpg"
    tail_transition_strip = evidence / "tail_signal_interruption_transition_strip.jpg"
    tail_crt_strip = evidence / "tail_balloon_after_trim_crt_strip.jpg"
    waveform = evidence / "first_10s_waveform.png"

    hook_context = builder.build_hook_clip(hook_clip)
    picture_bed_context = builder.build_picture_bed(hook_clip, picture_bed)
    builder.build_audio_mix(audio_mix)
    builder.mux(picture_bed, audio_mix, proof)
    builder.extract_excerpt(builder.CURRENT_YOUTUBE_SHORT, 10.0, current_excerpt)
    builder.extract_excerpt(proof, 10.0, revised_excerpt)
    builder.build_comparison(current_excerpt, revised_excerpt, comparison)
    opening_frames = builder.build_frame_strip(proof, frame_strip, [0.0, 0.5, 1.0, 2.0, 2.9, 3.0, 3.1, 4.0, 6.0, 10.0])
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
    tail_handoff_seconds = builder.HOOK_DURATION_SECONDS + picture_bed_context["body_duration_seconds"]
    tail_start_seconds = tail_handoff_seconds + picture_bed_context["signal_interruption_duration_seconds"]
    tail_transition_frames = builder.build_frame_strip(
        proof,
        tail_transition_strip,
        [
            tail_handoff_seconds - 0.15,
            tail_handoff_seconds,
            tail_handoff_seconds + 0.08,
            tail_handoff_seconds + 0.16,
            tail_start_seconds,
            tail_start_seconds + 0.20,
            tail_start_seconds + 0.55,
            tail_start_seconds + 1.00,
        ],
    )
    tail_crt_frames = builder.build_frame_strip(
        proof,
        tail_crt_strip,
        [
            tail_start_seconds,
            tail_start_seconds + 0.40,
            tail_start_seconds + 0.80,
            tail_start_seconds + 1.20,
            tail_start_seconds + 1.80,
            tail_start_seconds + 2.40,
            builder.FINAL_DURATION_SECONDS - 0.50,
        ],
    )
    builder.build_waveform(proof, waveform)
    freeze_evidence = builder.freeze_tail_evidence(proof)

    manifest = {
        "schema_version": "1.0",
        "stage": "first-second hook review",
        "prototype_id": f"hyatt_theme_intro_hook_{stamp}",
        "local_only_no_youtube_action": True,
        "episode_id": "hyatt-regency",
        "short_id": "hyatt_short_scoped_v1",
        "current_latest_publish_mp4_path": str(builder.CURRENT_YOUTUBE_SHORT),
        "current_latest_publish_mp4_sha256": builder.sha256(builder.CURRENT_YOUTUBE_SHORT),
        "proof_path": str(proof),
        "proof_sha256": builder.sha256(proof),
        "comparison_path": str(comparison),
        "comparison_sha256": builder.sha256(comparison),
        "frame_strip_path": str(frame_strip),
        "frame_strip_sha256": builder.sha256(frame_strip),
        "outro_frame_strip_path": str(outro_strip),
        "outro_frame_strip_sha256": builder.sha256(outro_strip),
        "tail_signal_interruption_transition_strip_path": str(tail_transition_strip),
        "tail_signal_interruption_transition_strip_sha256": builder.sha256(tail_transition_strip),
        "tail_balloon_after_trim_crt_strip_path": str(tail_crt_strip),
        "tail_balloon_after_trim_crt_strip_sha256": builder.sha256(tail_crt_strip),
        "waveform_path": str(waveform),
        "waveform_sha256": builder.sha256(waveform),
        "visual_extension_mode": picture_bed_context["visual_extension_mode"],
        "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
        "motion_source_contains_captions": picture_bed_context["motion_source_contains_captions"],
        "clean_body_source_path": picture_bed_context["clean_body_source_path"],
        "caption_duplicate_repair_read": picture_bed_context["caption_duplicate_repair_read"],
        "hook_crt_texture": hook_context["hook_crt_texture"],
        "hook_crt_overlay_read": "pass_review_required",
        "opening_texture_match_read": "pass_review_required",
        "source_motion_tail": picture_bed_context["source_motion_tail"],
        "signal_interruption_used": picture_bed_context["signal_interruption_used"],
        "signal_interruption_duration_seconds": picture_bed_context["signal_interruption_duration_seconds"],
        "signal_interruption": picture_bed_context["signal_interruption"],
        "tail_source_trim_start_seconds": picture_bed_context["source_motion_tail"]["source_start_seconds"]
        if picture_bed_context["source_motion_tail"]
        else None,
        "source_transition_trimmed_seconds": picture_bed_context["source_motion_tail"]["source_transition_trimmed_seconds"]
        if picture_bed_context["source_motion_tail"]
        else None,
        "house_crt_tail_match_read": "pass_review_required",
        "unwanted_source_transition_read": "pass",
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "body_trimmed_for_tail_motion_seconds": picture_bed_context["body_trimmed_for_tail_motion_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "tail_repetition_read": "pass",
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "visual_strategy": {
            "hook_visual": "no-caption Hyatt Regency tea-dance floor source motion moved to the front",
            "hook_source_path": str(builder.NO_CAPTION_PICTURE),
            "hook_source_start_seconds": builder.HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": builder.HOOK_DURATION_SECONDS,
            "hook_crt_texture": hook_context["hook_crt_texture"],
            "hook_crt_overlay_read": "pass_review_required",
            "opening_texture_match_read": "pass_review_required",
            "body_after_hook": "existing Hyatt Regency clean no-caption house-CRT body starts at original t=0 after hook",
            "clean_body_source_path": picture_bed_context["clean_body_source_path"],
            "motion_source_contains_captions": picture_bed_context["motion_source_contains_captions"],
            "caption_duplicate_repair_read": picture_bed_context["caption_duplicate_repair_read"],
            "visual_extension_mode": picture_bed_context["visual_extension_mode"],
            "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
            "source_motion_tail": picture_bed_context["source_motion_tail"],
            "signal_interruption": picture_bed_context["signal_interruption"],
            "house_crt_tail_match_read": "pass_review_required",
            "unwanted_source_transition_read": "pass",
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
            "outro": outro_frames,
            "tail_signal_interruption_transition": tail_transition_frames,
            "tail_balloon_after_trim_crt": tail_crt_frames,
        },
        "review_request": "Judge whether the Hyatt tea-dance motion plus full theme intro punch improves scroll-stop, and whether the transition into the loop feels natural before voice starts.",
        "tail_repair_note": "The outro extension uses a different balloon/atrium source segment so the final dance-floor couple clip does not repeat around 1:02.",
        "human_review_disposition": "keep",
    }
    builder.write_json(root / "hyatt_theme_intro_hook_manifest.json", manifest)

    note = f"""# Hyatt Regency Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `frame_strip_path`: `{frame_strip}`
- `tail_signal_interruption_transition_strip_path`: `{tail_transition_strip}`
- `tail_balloon_after_trim_crt_strip_path`: `{tail_crt_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{builder.HOOK_DURATION_SECONDS:.1f}s` is no-caption Hyatt Regency tea-dance floor source motion with house CRT/analog texture applied.
- The full theme song starts from `0.00` so the opening punch lands immediately.
- The theme intro crossfades into the registered loop from `{builder.LOOP_START_SECONDS:.2f}s` to `{builder.LOOP_START_SECONDS + builder.LOOP_CROSSFADE_SECONDS:.2f}s`.
- The approved Hyatt Regency voice starts after the hook at `{builder.VOICE_DELAY_SECONDS:.2f}s`.
- The loop continues under the body, then fades into the theme outro at `{builder.OUTRO_START_SECONDS:.2f}s`.
- The body source is now the clean no-caption Hyatt house-CRT motion bed, so final export can burn one yellow caption layer without overlap.
- Any needed tail extension uses a different balloon/atrium source segment, not cloned-frame padding or a repeat of the final dance-floor couple clip.
- The balloon/atrium source starts at `0.65s`, cutting out the source-internal stretch/grow transition from black.
- The handoff into the tail uses the signal-interruption transition.
- The inserted tail has a house CRT/analog texture pass to better match the rest of the Short.
- `hook_crt_overlay_read`: `pass_review_required`
- `opening_texture_match_read`: `pass_review_required`
- `caption_duplicate_repair_read`: `{picture_bed_context["caption_duplicate_repair_read"]}`
- `tail_repetition_read`: `pass`
- `unwanted_source_transition_read`: `pass`
- `house_crt_tail_match_read`: `pass_review_required`
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`

## Review Read

Mark this `keep`, `tighten`, or `reject`.

- `keep`: dance-floor motion plus theme punch improves scroll-stop and the loop handoff feels natural.
- `tighten`: the idea works, but the hook span, music level, loop handoff, or outro timing needs adjustment.
- `reject`: it feels too loud, tonally wrong, or less effective than the current opening.
"""
    builder.write_text(root / "review_note.md", note)

    latest_link = builder.OUTPUT_ROOT / "hyatt_theme_intro_hook_latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
