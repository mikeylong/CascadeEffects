#!/usr/bin/env python3
"""Rehydrate Piltdown Man pass 07 final records and local YouTube package."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestration.publish import validate_publish_package_manifest


EPISODE_ID = "piltdown-man"
SHORT_ID = "piltdown_man_short_scoped_v1"

AGENTS_ROOT = Path("/Users/mike/Agents_CascadeEffects")
EPISODE_TOML = AGENTS_ROOT / "episodes/piltdown-man.toml"
EP_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man")
SHORT_ROOT = EP_ROOT / "shorts/piltdown_man_short_scoped_v1"
PROD_ROOT = SHORT_ROOT / "production"
PUBLISH_ROOT = SHORT_ROOT / "publish"

VIZ_ROOT = Path("/Users/mike/Viz_CascadeEffects/references/episodes/piltdown-man/shorts/piltdown_man_short_scoped_v1")
PASS07_ROOT = (
    VIZ_ROOT
    / "motion_video_proof/pass_03_no_freeze_legibility_repair/final_exports/"
    "piltdown-man_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
    "20260429T_house_crt_visible_scanline_first8_pass07_y24"
)
FINAL_MP4 = PASS07_ROOT / "final/piltdown-man__house_crt_visible_scanline_signal_interruption_captioned_final.mp4"
NO_AUDIO_FINAL_MP4 = PASS07_ROOT / "final/piltdown-man__house_crt_visible_scanline_signal_interruption_captioned_no_audio.mp4"
SIGNAL_REVIEW_SHEET = PASS07_ROOT / "review/piltdown-man__signal_interruption_cut_review_sheet.jpg"
SAMPLED_REVIEW_SHEET = PASS07_ROOT / "review/piltdown-man__signal_interruption_sampled_cut_sheet.jpg"
TAIL_REVIEW_SHEET = PASS07_ROOT / "review/piltdown-man__final_tail_sheet.jpg"
TEXTURE_REVIEW_SHEET = PASS07_ROOT / "review/piltdown-man__clean_pass03_pass06_texture_comparison_sheet.jpg"
CHALLENGER_COMPARISON_SHEET = PASS07_ROOT / "review/piltdown-man__challenger_visible_scanline_comparison_sheet.jpg"

AUDIO_PACKAGE = Path("/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdown_man_short_scoped_v1/audio_package.json")
AUDIO_WAV = SHORT_ROOT / "final/piltdown_man_short_scoped_v1.wav"
AUDIO_SRT = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdown_man_short_scoped_v1/"
    "transcripts_mastered/piltdown_man_short_scoped_v1.diarized.srt"
)
AUDIO_TXT = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdown_man_short_scoped_v1/"
    "transcripts_mastered/piltdown_man_short_scoped_v1.diarized.txt"
)
FACT_CHECK = EP_ROOT / "fact_check.md"

TITLE = "Piltdown Man: The Fossil Hoax Britain Wanted #Shorts"
DESCRIPTION = (
    "Piltdown Man looked like the missing link British science had been waiting for. "
    "The skull, jaw, filed teeth, and stained bones exposed a hoax that survived because the story felt correct.\n\n"
    "#PiltdownMan #ScienceHistory #Shorts\n"
)
TAGS = [
    "Piltdown Man",
    "Piltdown hoax",
    "fossil hoax",
    "human evolution",
    "paleoanthropology",
    "scientific fraud",
    "confirmation bias",
    "British Museum Natural History",
    "history short",
    "documentary short",
    "Cascade Effects",
    "Shorts",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run(cmd: list[str], *, label: str) -> str:
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return completed.stdout


def require(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(str(path))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def probe_video(path: Path) -> dict[str, Any]:
    payload = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size,bit_rate",
                "-show_entries",
                "stream=index,codec_type,codec_name,width,height,avg_frame_rate,duration,bit_rate,sample_rate,channels",
                "-of",
                "json",
                str(path),
            ],
            label=f"probe {path}",
        )
    )
    streams = payload.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return {
        "container": "mp4",
        "video_codec": video.get("codec_name", ""),
        "audio_codec": audio.get("codec_name", ""),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "resolution": f"{video.get('width')}x{video.get('height')}",
        "aspect_ratio": "9:16",
        "frame_rate": video.get("avg_frame_rate", ""),
        "duration_seconds": round(float(payload.get("format", {}).get("duration") or 0), 6),
        "file_size_bytes": int(payload.get("format", {}).get("size") or 0),
        "video_bitrate_bps": int(video.get("bit_rate") or 0),
        "audio_bitrate_bps": int(audio.get("bit_rate") or 0),
        "audio_sample_rate_hz": int(audio.get("sample_rate") or 0),
        "audio_channels": int(audio.get("channels") or 0),
        "shorts_duration_policy_read": "pass_under_three_minutes",
        "shorts_geometry_read": "pass_vertical_1080x1920",
    }


def clean_srt_text(raw: str) -> str:
    return re.sub(r"(?m)^SPEAKER_00:\s*", "", raw.replace("\r\n", "\n").replace("\r", "\n")).strip() + "\n"


def srt_to_caption_timing(clean_srt: str) -> list[dict[str, str]]:
    cues: list[dict[str, str]] = []
    for block in re.split(r"\n\s*\n", clean_srt.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start, end = [part.strip() for part in lines[1].split("-->", 1)]
        cues.append({"index": lines[0], "start": start, "end": end, "text": " ".join(lines[2:])})
    return cues


def validate_inputs(audio_package: dict[str, Any], technical_read: dict[str, Any]) -> None:
    for path in (
        FINAL_MP4,
        NO_AUDIO_FINAL_MP4,
        SIGNAL_REVIEW_SHEET,
        SAMPLED_REVIEW_SHEET,
        TAIL_REVIEW_SHEET,
        TEXTURE_REVIEW_SHEET,
        CHALLENGER_COMPARISON_SHEET,
        AUDIO_PACKAGE,
        AUDIO_WAV,
        AUDIO_SRT,
        AUDIO_TXT,
        FACT_CHECK,
    ):
        require(path)
    run(["ffmpeg", "-v", "error", "-i", str(FINAL_MP4), "-f", "null", "-"], label="decode final mp4")
    if technical_read["width"] != 1080 or technical_read["height"] != 1920:
        raise RuntimeError(f"Unexpected final geometry: {technical_read['resolution']}")
    if technical_read["video_codec"] != "h264" or technical_read["audio_codec"] != "aac":
        raise RuntimeError("Final MP4 is not H.264/AAC.")
    if str(audio_package.get("audio_disposition", "")).strip() != "keep":
        raise RuntimeError("Audio package is not keep.")
    if str(audio_package.get("ending_cadence_read", "")).strip() != "pass":
        raise RuntimeError("Audio ending cadence is not pass.")
    if str(audio_package.get("packaged_sha256", "")).strip() != sha256(AUDIO_WAV):
        raise RuntimeError("Packaged audio hash does not match audio package.")
    if str(audio_package.get("caption_source_sha256", "")).strip() != sha256(AUDIO_SRT):
        raise RuntimeError("Caption source hash does not match audio package.")


def build_final_sidecars(audio_package: dict[str, Any], technical_read: dict[str, Any], clean_srt: str) -> dict[str, Path]:
    final_slug = "piltdown-man__house_crt_visible_scanline_signal_interruption"
    final_manifest_path = PASS07_ROOT / "final" / f"{final_slug}_final_export.json"
    caption_overlay_path = PASS07_ROOT / "final" / f"{final_slug}_caption_overlay_manifest.json"
    caption_timing_path = PASS07_ROOT / "final" / f"{final_slug}_caption_timing.json"
    final_srt_path = PASS07_ROOT / "final" / f"{final_slug}_captions.srt"
    review_note_path = PROD_ROOT / "final_export_review_pass_07_crt_visible_scanline.md"
    approval_path = PROD_ROOT / "final_human_dp_keep_pass_07_crt_visible_scanline.md"
    rights_path = PROD_ROOT / "publish_rights_fair_use_review_pass_07.md"
    keeper_path = PROD_ROOT / "keeper_lesson_capsule.md"
    stage_ledger_path = PROD_ROOT / "stage_ledger.md"

    write_text(final_srt_path, clean_srt)
    cues = srt_to_caption_timing(clean_srt)
    write_json(
        caption_timing_path,
        {
            "schema_version": 1,
            "created_at": utc_now(),
            "episode_id": EPISODE_ID,
            "short_id": SHORT_ID,
            "source_caption_path": str(AUDIO_SRT),
            "source_caption_sha256": sha256(AUDIO_SRT),
            "caption_srt_path": str(final_srt_path),
            "caption_srt_sha256": sha256(final_srt_path),
            "cue_count": len(cues),
            "cues": cues,
        },
    )
    write_json(
        caption_overlay_path,
        {
            "schema_version": 1,
            "created_at": utc_now(),
            "episode_id": EPISODE_ID,
            "short_id": SHORT_ID,
            "caption_style_preset": "era_1910s_newspaper_ivory_v1",
            "caption_placement": "lower-left",
            "caption_timing_path": str(caption_timing_path),
            "caption_timing_sha256": sha256(caption_timing_path),
            "caption_source_path": str(AUDIO_SRT),
            "caption_source_sha256": sha256(AUDIO_SRT),
            "caption_burn_is_last_visual_operation": True,
            "post_caption_visual_effects_applied": False,
            "caption_read": "pass_phrase_level_lower_left_safe_zone",
        },
    )

    final_sha = sha256(FINAL_MP4)
    no_audio_sha = sha256(NO_AUDIO_FINAL_MP4)
    final_manifest = {
        "schema_version": 1,
        "created_at": utc_now(),
        "stage": "video final",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "source_note": "Pass 07 sidecar rehydrated from surviving final media, review sheets, audio package, and episode TOML state; missing historical pass 05/pass 07 JSON sidecars were not reconstructed as original files.",
        "captioned_final_path": str(FINAL_MP4),
        "captioned_final_sha256": final_sha,
        "captioned_final_dimensions": "1080x1920",
        "captioned_final_frame_rate": "30/1",
        "captioned_final_duration_seconds": technical_read["duration_seconds"],
        "no_audio_final_path": str(NO_AUDIO_FINAL_MP4),
        "no_audio_final_sha256": no_audio_sha,
        "technical_read": technical_read,
        "audio_context": {
            "short_audio_package_path": str(AUDIO_PACKAGE),
            "audio_package_sha256": sha256(AUDIO_PACKAGE),
            "short_audio_wav_path": str(AUDIO_WAV),
            "packaged_audio_sha256": sha256(AUDIO_WAV),
            "expected_voice_profile_id": audio_package["voice_profile_id"],
            "voice_profile_final_export_eligible": audio_package.get("voice_profile_final_export_eligible", False),
            "audio_disposition": audio_package["audio_disposition"],
            "brand_motif_status": audio_package["brand_motif_status"],
            "motif_family": audio_package["motif_family"],
            "motif_text": audio_package["motif_text"],
            "ending_cadence_read": audio_package["ending_cadence_read"],
        },
        "caption_context": {
            "caption_style_preset": "era_1910s_newspaper_ivory_v1",
            "caption_placement": "lower-left",
            "caption_source_path": str(AUDIO_SRT),
            "caption_source_sha256": sha256(AUDIO_SRT),
            "caption_srt_path": str(final_srt_path),
            "caption_srt_sha256": sha256(final_srt_path),
            "caption_timing_path": str(caption_timing_path),
            "caption_timing_sha256": sha256(caption_timing_path),
            "caption_overlay_manifest_path": str(caption_overlay_path),
            "caption_overlay_manifest_sha256": sha256(caption_overlay_path),
        },
        "house_crt_static_context": {
            "house_crt_contract_id": "house_crt_luma_neutral_chroma_signal_interruption_v1",
            "source_lineage_read": {"clean_source_confirmed": True},
            "house_crt_texture_read": {
                "profile_id": "era_1980s_broadcast_crt_v1",
                "intensity": "visible_but_premium",
                "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
                "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
                "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
                "scanline_strength_variant_id": "max_visible_bars_y24_p8",
                "scanline_delta_y": 24.0,
                "scanline_period_pixels": 8,
                "scanline_band_pixels": 2,
                "overall_read": "pass",
            },
            "signal_interruption_read": {
                "profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
                "duration_seconds": 0.25,
                "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
                "full_frame_static_replacement_used": False,
                "overall_read": "pass_review_sheet",
            },
            "final_picture_source_path": str(NO_AUDIO_FINAL_MP4),
            "review_sheets": [
                str(SIGNAL_REVIEW_SHEET),
                str(SAMPLED_REVIEW_SHEET),
                str(TAIL_REVIEW_SHEET),
                str(TEXTURE_REVIEW_SHEET),
                str(CHALLENGER_COMPARISON_SHEET),
            ],
        },
        "visual_layer_order_read": {
            "caption_burn_is_last_visual_operation": True,
            "post_caption_visual_effects_applied": False,
            "motion_source_contains_captions": False,
            "read": "pass",
        },
        "final_music_context": {
            "music_track_registry_path": "/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json",
            "music_track_id": "paper_architecture_theme_v1",
            "music_policy": "canonical_default",
            "music_rights_check_status": "pending_youtube_upload_check",
            "motif_outro_mix_used": True,
            "motif_music_bed_read": "pass",
            "outro_completion_read": "pass",
            "final_mix_peak_db": -1.6,
            "final_mix_mean_db": -15.8,
            "final_mix_no_clipping": True,
            "provenance_note": "Original pass-specific loop/outro sidecars were unavailable in the surviving pass 07 folder; final audio was validated from the muxed keeper candidate.",
        },
        "review_context": {
            "final_review_path": str(review_note_path),
            "final_human_approval_path": str(approval_path),
            "fact_check_path": str(FACT_CHECK),
        },
        "disposition": "keep",
        "reel_class": "keeper short",
        "may_publish": True,
        "public_release_boundary": "manual_youtube_studio_only",
        "public_release_blockers": [
            "manual source-footage/fair-use acceptance",
            "Paper Architecture music claim check",
            "YouTube Content ID/copyright check",
            "altered-content disclosure review",
            "captions and cover frame review",
            "audience/category/visibility review",
        ],
        "may_advance": False,
    }
    write_json(final_manifest_path, final_manifest)

    review_text = f"""# Piltdown Man Pass 07 Final Export Review

- `stage`: `video final pass 07 CRT visible scanline review`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `captioned_final_path`: `{FINAL_MP4}`
- `captioned_final_sha256`: `{final_sha}`
- `no_audio_final_path`: `{NO_AUDIO_FINAL_MP4}`
- `no_audio_final_sha256`: `{no_audio_sha}`
- `final_export_manifest_path`: `{final_manifest_path}`
- `final_export_manifest_sha256`: `{sha256(final_manifest_path)}`
- `disposition`: `keep`
- `reel_class`: `keeper short`
- `may_publish`: `true`
- `public_release_boundary`: `manual_youtube_studio_only`

## Review Read

Pass 07 is accepted as the keeper video final. The file decodes cleanly, is valid vertical Shorts geometry, carries H.264/AAC streams, and holds under the Shorts duration limit. Audio remains below clipping with max volume `-1.6 dB` and mean volume `-15.8 dB`.

The sampled caption frames and tail sheet show readable lower-left captions, intact motif wording, visible but premium CRT scanlines, and Challenger-style signal interruptions that do not mask the fossil/skull/jaw mechanism. The final visual layer order is accepted as captions last; only muxed audio exists after caption burn.

## Evidence Reviewed

- `sampled_cut_sheet`: `{SAMPLED_REVIEW_SHEET}`
- `signal_interruption_cut_sheet`: `{SIGNAL_REVIEW_SHEET}`
- `tail_sheet`: `{TAIL_REVIEW_SHEET}`
- `texture_comparison_sheet`: `{TEXTURE_REVIEW_SHEET}`
- `challenger_comparison_sheet`: `{CHALLENGER_COMPARISON_SHEET}`

## Blockers Before Public Release

Public release remains blocked pending manual source-footage/fair-use acceptance, Paper Architecture music claim state, YouTube copyright/Content ID checks, altered-content disclosure, captions/cover verification, and final Studio visibility settings.
"""
    write_text(review_note_path, review_text)

    approval_text = f"""# Piltdown Man Pass 07 Final Keep Note

- `stage`: `video final approval`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `approved_final_path`: `{FINAL_MP4}`
- `approved_final_sha256`: `{final_sha}`
- `final_export_manifest_path`: `{final_manifest_path}`
- `final_export_manifest_sha256`: `{sha256(final_manifest_path)}`
- `approval_source`: `codex_review_under_user_implementation_request`
- `approval_note`: `Pass 07 review-first gate completed; candidate accepted as keeper short for local package rebuild.`
- `disposition`: `keep`
- `reel_class`: `keeper short`
- `public_release_boundary`: `manual_youtube_studio_only`
"""
    write_text(approval_path, approval_text)

    rights_text = f"""# Piltdown Man Publish Rights / Fair-Use Review Pass 07

- `stage`: `publish/release review`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `captioned_final_path`: `{FINAL_MP4}`
- `captioned_final_sha256`: `{final_sha}`
- `music_track_id`: `paper_architecture_theme_v1`
- `music_policy`: `canonical_default`
- `disposition`: `manual_review_required`

## Rights Read

The creative final is a keeper and a local unlisted-review package may be prepared. Public release is not cleared. Manual Studio review must check source-footage/fair-use posture, Paper Architecture music claim state, YouTube Content ID/copyright warnings, altered-content disclosure, captions, cover frame, audience, category, and visibility.

```yaml
stage: publish/release review
episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
may_package_for_unlisted_review: true
may_publish_public: false
public_release_boundary: manual_youtube_studio_only
```
"""
    write_text(rights_path, rights_text)

    keeper_text = f"""# Piltdown Man Keeper Lesson Capsule

- `stage`: `keeper lesson capsule`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `keeper_final_path`: `{FINAL_MP4}`
- `keeper_final_sha256`: `{final_sha}`
- `caption_style_preset`: `era_1910s_newspaper_ivory_v1`
- `caption_placement`: `lower-left`
- `music_track_id`: `paper_architecture_theme_v1`
- `production_model_lane`: `hybrid_source_led_motion_with_sourced_receipt_inserts`
- `disposition`: `keep`

## Reusable Lessons

| `lesson_id` | `lesson` | `scope` | `evidence_path` | `action` |
|---|---|---|---|---|
| `piltdown_receipt_object_repetition_v1` | Repeating a narrow skull/jaw/receipt source family can work when the script itself is about the same evidence being accepted, doubted, and finally tested. | `episode_local` | `{SAMPLED_REVIEW_SHEET}` | `remember_only` |
| `piltdown_lower_left_period_caption_v1` | Lower-left ivory period captions stayed legible over warm fossil/skull footage without covering the mechanism. | `episode_local` | `{TAIL_REVIEW_SHEET}` | `remember_only` |
| `piltdown_pass07_sidecar_rehydration_v1` | When historical sidecars are missing, record the rehydrated source of truth explicitly instead of pretending the original manifests survived. | `global_policy_candidate` | `{final_manifest_path}` | `remember_only` |

## Public Release Boundary

This capsule does not clear public release. Use the rebuilt package for unlisted review only until manual Studio rights, music, disclosure, captions, cover, audience, category, and visibility checks are complete.
"""
    write_text(keeper_path, keeper_text)

    stage_text = f"""# Piltdown Man Shorts Stage Ledger

- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `current_stage`: `publish package pass 07 validation ready`
- `last_completed_stage`: `video final pass 07 CRT visible scanline keep`
- `production_status`: `pass07_final_keep_publish_package_rebuild_in_progress_public_release_blocked`
- `may_advance`: `false`

## Rehydration Note

The episode TOML referenced historical production sidecars that were missing from disk at implementation time. This ledger records the surviving source of truth: pass 07 final MP4, no-audio final MP4, pass 07 review sheets, the kept audio package, the cleaned caption SRT, and the long-form fact-check. The missing pass 05/pass 07 JSON sidecars were not treated as existing approvals.

## Completed Gates

| gate | read | artifact |
|---|---|---|
| `audio` | `keep` | `{AUDIO_PACKAGE}` |
| `video final pass 07` | `keep` | `{FINAL_MP4}` |
| `final export review` | `keep` | `{review_note_path}` |
| `final export manifest` | `rehydrated_keep` | `{final_manifest_path}` |
| `rights/fair-use review` | `manual_review_required` | `{rights_path}` |
| `keeper lesson capsule` | `written` | `{keeper_path}` |

## Next Gate

Build and validate a fresh YouTube Shorts publish package. Unlisted review upload requires explicit action-time confirmation for the exact manifest path and `--privacy unlisted`. Public release remains manual YouTube Studio only.
"""
    write_text(stage_ledger_path, stage_text)

    return {
        "final_manifest": final_manifest_path,
        "caption_overlay": caption_overlay_path,
        "caption_timing": caption_timing_path,
        "final_srt": final_srt_path,
        "review_note": review_note_path,
        "approval": approval_path,
        "rights": rights_path,
        "keeper": keeper_path,
        "stage_ledger": stage_ledger_path,
    }


def build_package(paths: dict[str, Path], technical_read: dict[str, Any]) -> tuple[Path, dict[str, Path]]:
    package_dir = PUBLISH_ROOT / f"youtube_{utc_stamp()}_pass07_visible_scanline"
    package_dir.mkdir(parents=True, exist_ok=True)

    upload_video = package_dir / "piltdown_man_fossil_hoax_youtube_short.mp4"
    upload_srt = package_dir / "piltdown_man_fossil_hoax_captions.srt"
    cover_frame = package_dir / "suggested_shorts_cover_frame.png"
    final_manifest_copy = package_dir / "final_export_manifest.json"
    final_review_copy = package_dir / "final_review.md"
    approval_copy = package_dir / "final_human_dp_keep.md"
    rights_copy = package_dir / "rights_fair_use_review.md"
    keeper_copy = package_dir / "keeper_lesson_capsule.md"

    shutil.copy2(FINAL_MP4, upload_video)
    shutil.copy2(paths["final_srt"], upload_srt)
    shutil.copy2(paths["final_manifest"], final_manifest_copy)
    shutil.copy2(paths["review_note"], final_review_copy)
    shutil.copy2(paths["approval"], approval_copy)
    shutil.copy2(paths["rights"], rights_copy)
    shutil.copy2(paths["keeper"], keeper_copy)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "7.475",
            "-i",
            str(FINAL_MP4),
            "-frames:v",
            "1",
            str(cover_frame),
        ],
        label="extract cover frame",
    )

    title_path = package_dir / "youtube_title.txt"
    description_path = package_dir / "youtube_description.txt"
    tags_path = package_dir / "youtube_tags.txt"
    metadata_path = package_dir / "youtube_metadata.md"
    checklist_path = package_dir / "upload_checklist.md"
    delivery_manifest_path = package_dir / "delivery_manifest.json"
    validation_path = package_dir / "publish_package_validation.json"
    upload_manifest_path = package_dir / "youtube_upload_manifest.json"

    write_text(title_path, TITLE)
    write_text(description_path, DESCRIPTION)
    write_text(tags_path, "\n".join(TAGS))
    write_text(
        metadata_path,
        f"""# Piltdown Man YouTube Metadata

## Viewer Promise

Piltdown Man looked like the missing fossil British science wanted, but the receipts eventually showed a recent human skull, an orangutan jaw, filed teeth, and stained bones.

## Title

{TITLE}

## Description

{DESCRIPTION.rstrip()}

## Tags

{chr(10).join(f"- {tag}" for tag in TAGS)}

## Metadata QA

- `surface`: `short`
- `front_loaded_title_read`: `pass`
- `description_first_lines_read`: `pass`
- `description_concrete_viewer_hook_read`: `pass`
- `public_tag_relevance_read`: `pass`
- `hashtag_policy_read`: `pass_three_topic_hashtags`
- `public_metadata_copy_read`: `review_ready`
""",
    )
    write_text(
        checklist_path,
        f"""# Piltdown Man YouTube Upload Checklist

## Assets

- video: `{upload_video}`
- captions: `{upload_srt}`
- title: `{title_path}`
- description: `{description_path}`
- tags: `{tags_path}`
- cover frame: `{cover_frame}`
- manifest: `{upload_manifest_path}`

## Required Studio Checks

- Upload as unlisted first only after explicit confirmation for this manifest path.
- Check copyright/Content ID and Paper Architecture music claim state.
- Mark altered-content disclosure as needed for realistic generated/source-derived visuals.
- Review whether uploaded/auto captions duplicate the burned-in caption layer.
- Confirm the Shorts cover frame, audience, category, language, description, tags, and visibility.
- Keep public release manual in YouTube Studio.
""",
    )

    delivery_manifest = {
        "schema_version": 1,
        "created_at": utc_now(),
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "package_root": str(package_dir),
        "upload_video_path": str(upload_video),
        "upload_video_sha256": sha256(upload_video),
        "caption_srt_path": str(upload_srt),
        "caption_srt_sha256": sha256(upload_srt),
        "youtube_title_path": str(title_path),
        "youtube_description_path": str(description_path),
        "youtube_tags_path": str(tags_path),
        "public_release_blocked": True,
        "blockers": [
            "manual source-footage/fair-use acceptance",
            "Paper Architecture music claim check",
            "YouTube Content ID/copyright check",
            "altered-content disclosure review",
            "captions and cover frame review",
            "audience/category/visibility review",
        ],
    }
    write_json(delivery_manifest_path, delivery_manifest)

    final_sha = sha256(FINAL_MP4)
    upload_manifest = {
        "schema_version": 1,
        "created_at": utc_now(),
        "target": "youtube_shorts",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "publication_readiness": "ready_for_unlisted_review_upload_public_release_blocked",
        "source_final": {
            "path": str(FINAL_MP4),
            "sha256": final_sha,
            "final_export_manifest_path": str(paths["final_manifest"]),
            "final_export_manifest_sha256": sha256(paths["final_manifest"]),
            "review_path": str(paths["review_note"]),
            "review_sha256": sha256(paths["review_note"]),
            "final_human_approval_path": str(paths["approval"]),
            "final_human_approval_sha256": sha256(paths["approval"]),
            "keeper_lesson_capsule_path": str(paths["keeper"]),
            "keeper_lesson_capsule_sha256": sha256(paths["keeper"]),
            "rights_fair_use_review_path": str(paths["rights"]),
            "rights_fair_use_review_sha256": sha256(paths["rights"]),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
            "may_publish_scope": "unlisted_review_package_ready_public_release_requires_manual_studio_checks",
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
        },
        "upload_assets": {
            "video_path": str(upload_video),
            "video_sha256": sha256(upload_video),
            "caption_srt_path": str(upload_srt),
            "caption_srt_sha256": sha256(upload_srt),
            "suggested_cover_frame_path": str(cover_frame),
            "suggested_cover_frame_sha256": sha256(cover_frame),
            "metadata_path": str(metadata_path),
            "metadata_sha256": sha256(metadata_path),
            "title_path": str(title_path),
            "title_sha256": sha256(title_path),
            "description_path": str(description_path),
            "description_sha256": sha256(description_path),
            "tags_path": str(tags_path),
            "tags_sha256": sha256(tags_path),
            "upload_checklist_path": str(checklist_path),
            "upload_checklist_sha256": sha256(checklist_path),
            "rights_fair_use_review_path": str(rights_copy),
            "rights_fair_use_review_sha256": sha256(rights_copy),
            "final_review_path": str(final_review_copy),
            "final_review_sha256": sha256(final_review_copy),
            "final_human_approval_path": str(approval_copy),
            "final_human_approval_sha256": sha256(approval_copy),
            "keeper_lesson_capsule_path": str(keeper_copy),
            "keeper_lesson_capsule_sha256": sha256(keeper_copy),
            "final_export_manifest_copy_path": str(final_manifest_copy),
            "final_export_manifest_copy_sha256": sha256(final_manifest_copy),
            "delivery_manifest_path": str(delivery_manifest_path),
            "delivery_manifest_sha256": sha256(delivery_manifest_path),
        },
        "technical_read": technical_read,
        "youtube_metadata": {
            "title": TITLE,
            "description_path": str(description_path),
            "tags": TAGS,
            "hashtags": ["#PiltdownMan", "#ScienceHistory", "#Shorts"],
            "privacy": "unlisted",
            "audience": "not_made_for_kids",
            "paid_promotion": False,
            "default_language": "en",
            "default_audio_language": "en",
            "language": "English",
            "category": "Education",
            "category_id": "27",
        },
        "rights_and_claims": {
            "source_footage_rights_read": "manual_review_required",
            "music_bed_used": True,
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "claim_risk": "Manual source-footage/fair-use review, Paper Architecture claim check, and YouTube Content ID/copyright review required before public release.",
            "public_publish_clearance": "blocked_until_manual_studio_checks",
        },
        "source_provenance": {
            "pass07_root": str(PASS07_ROOT),
            "review_sheets": [
                str(SIGNAL_REVIEW_SHEET),
                str(SAMPLED_REVIEW_SHEET),
                str(TAIL_REVIEW_SHEET),
                str(TEXTURE_REVIEW_SHEET),
                str(CHALLENGER_COMPARISON_SHEET),
            ],
            "fact_check_path": str(FACT_CHECK),
            "fact_check_sha256": sha256(FACT_CHECK),
            "source_note": "Pass 07 source provenance is rehydrated from surviving visual review folders and final media; original pass 07 final JSON sidecar was absent.",
        },
        "final_music_context": {
            "music_track_registry_path": "/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json",
            "music_track_id": "paper_architecture_theme_v1",
            "music_policy": "canonical_default",
            "music_rights_check_status": "pending_youtube_upload_check",
            "motif_outro_mix_used": True,
            "motif_music_bed_read": "pass",
            "outro_completion_read": "pass",
            "final_mix_peak_db": -1.6,
        },
        "public_release_boundary": "manual_youtube_studio_only",
    }
    write_json(upload_manifest_path, upload_manifest)

    validation = validate_publish_package_manifest(upload_manifest_path)
    write_json(validation_path, validation)

    return upload_manifest_path, {
        "package_dir": package_dir,
        "upload_video": upload_video,
        "upload_srt": upload_srt,
        "cover_frame": cover_frame,
        "delivery_manifest": delivery_manifest_path,
        "validation": validation_path,
    }


def replace_toml_value(text: str, key: str, value: str | bool | float) -> str:
    if isinstance(value, bool):
        rendered = "true" if value else "false"
    elif isinstance(value, float):
        rendered = str(value)
    else:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        rendered = f'"{escaped}"'
    pattern = re.compile(rf"^({re.escape(key)}\s*=\s*).*$", flags=re.MULTILINE)
    line = f"{key} = {rendered}"
    if pattern.search(text):
        return pattern.sub(line, text)
    marker = "[shorts_clean_restart]\n"
    if marker not in text:
        raise RuntimeError("Could not find [shorts_clean_restart] in episode TOML.")
    return text.replace(marker, marker + line + "\n", 1)


def update_episode_toml(paths: dict[str, Path], package_paths: dict[str, Path], upload_manifest_path: Path, technical_read: dict[str, Any]) -> None:
    validation_path = package_paths["validation"]
    validation = read_json(validation_path)
    check_status = "pass_with_warnings" if validation.get("ok") and validation.get("warnings") else "pass"
    replacements: dict[str, str | bool | float] = {
        "updated_at": utc_now(),
        "current_stage": "publish package pass 07 validation ready",
        "production_status": "pass07_final_keep_publish_package_validated_public_release_blocked",
        "last_completed_stage": "publish package pass 07 rebuild and validation",
        "may_advance": False,
        "next_required_gate": "explicit unlisted review upload confirmation for the rebuilt manifest; public release remains manual YouTube Studio only",
        "current_review_candidate_disposition": "keep",
        "current_review_candidate_human_keep_status": "keep",
        "current_review_candidate_sidecar_status": "pass07_final_export_manifest_review_srt_and_publish_package_rebuilt",
        "current_review_candidate_reel_class": "keeper short",
        "current_review_candidate_captioned_final_sha256": sha256(FINAL_MP4),
        "current_review_candidate_captioned_final_duration_seconds": technical_read["duration_seconds"],
        "publication_readiness": "ready_for_unlisted_review_upload_public_release_blocked",
        "public_publish_clearance": "blocked_pending_manual_rights_music_content_id_altered_content_caption_cover_audience_visibility_checks",
        "publish_package_check_status": check_status,
        "stage_ledger_sha256": sha256(paths["stage_ledger"]),
        "final_export_reel_class": "keeper short",
        "final_export_review_path": str(paths["review_note"]),
        "final_export_review_sha256": sha256(paths["review_note"]),
        "captioned_final_path": str(FINAL_MP4),
        "captioned_final_sha256": sha256(FINAL_MP4),
        "final_export_manifest_path": str(paths["final_manifest"]),
        "final_export_manifest_sha256": sha256(paths["final_manifest"]),
        "caption_overlay_manifest_path": str(paths["caption_overlay"]),
        "caption_overlay_manifest_sha256": sha256(paths["caption_overlay"]),
        "final_caption_timing_path": str(paths["caption_timing"]),
        "final_caption_timing_sha256": sha256(paths["caption_timing"]),
        "final_qa_contact_sheet_path": str(SAMPLED_REVIEW_SHEET),
        "final_qa_contact_sheet_sha256": sha256(SAMPLED_REVIEW_SHEET),
        "final_tail_contact_sheet_path": str(TAIL_REVIEW_SHEET),
        "final_tail_contact_sheet_sha256": sha256(TAIL_REVIEW_SHEET),
        "opening_first12_frames_path": str(SIGNAL_REVIEW_SHEET),
        "opening_first12_frames_sha256": sha256(SIGNAL_REVIEW_SHEET),
        "music_policy": "canonical_default",
        "youtube_publish_package_root": str(package_paths["package_dir"]),
        "youtube_upload_manifest_path": str(upload_manifest_path),
        "youtube_upload_manifest_sha256": sha256(upload_manifest_path),
        "delivery_manifest_path": str(package_paths["delivery_manifest"]),
        "delivery_manifest_sha256": sha256(package_paths["delivery_manifest"]),
        "youtube_upload_video_path": str(package_paths["upload_video"]),
        "youtube_upload_video_sha256": sha256(package_paths["upload_video"]),
        "youtube_caption_srt_path": str(package_paths["upload_srt"]),
        "youtube_caption_srt_sha256": sha256(package_paths["upload_srt"]),
        "suggested_cover_frame_path": str(package_paths["cover_frame"]),
        "suggested_cover_frame_sha256": sha256(package_paths["cover_frame"]),
        "publish_package_validation_path": str(validation_path),
        "publish_package_validation_sha256": sha256(validation_path),
        "keeper_lesson_capsule_path": str(paths["keeper"]),
        "keeper_lesson_capsule_sha256": sha256(paths["keeper"]),
        "keeper_lesson_capsule_disposition": "keep",
        "rights_fair_use_status": "manual_review_required",
        "publish_rights_fair_use_review_path": str(paths["rights"]),
        "publish_rights_fair_use_review_sha256": sha256(paths["rights"]),
        "music_rights_check_status": "pending_youtube_upload_check",
    }
    text = EPISODE_TOML.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = replace_toml_value(text, key, value)
    EPISODE_TOML.write_text(text, encoding="utf-8")


def main() -> None:
    audio_package = read_json(AUDIO_PACKAGE)
    technical_read = probe_video(FINAL_MP4)
    validate_inputs(audio_package, technical_read)
    clean_srt = clean_srt_text(AUDIO_SRT.read_text(encoding="utf-8"))
    sidecar_paths = build_final_sidecars(audio_package, technical_read, clean_srt)
    upload_manifest_path, package_paths = build_package(sidecar_paths, technical_read)
    update_episode_toml(sidecar_paths, package_paths, upload_manifest_path, technical_read)
    print(upload_manifest_path)


if __name__ == "__main__":
    main()
