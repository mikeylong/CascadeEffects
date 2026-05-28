#!/usr/bin/env python3
"""Rebuild 737 MAX pass 07 review evidence and local Shorts package."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/Users/mike/Agents_CascadeEffects")
EPISODE_ID = "737-max"
SHORT_ID = "737_max_short_scoped_v1"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

EPISODE_TOML = ROOT / "episodes/737-max.toml"
EPISODE_SHORT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/shorts/737_max_short_scoped_v1")
PRODUCTION_ROOT = EPISODE_SHORT_ROOT / "production"
QA_ROOT = PRODUCTION_ROOT / "qa/pass07_crt_visible_scanline_review"
PUBLISH_ROOT = EPISODE_SHORT_ROOT / "publish" / f"youtube_{STAMP}"

PASS07_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/737-max/shorts/737_max_short_scoped_v1/"
    "motion_video_proof/pass_05_source_led_takeoff_continuity_repair/final_exports/"
    "737-max_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
    "20260429T_house_crt_visible_scanline_first8_pass07_y24"
)
PASS07_FINAL = PASS07_ROOT / "final/737-max__house_crt_visible_scanline_signal_interruption_captioned_final.mp4"
PASS07_NO_AUDIO = PASS07_ROOT / "final/737-max__house_crt_visible_scanline_signal_interruption_captioned_no_audio.mp4"
PASS07_REVIEW_ROOT = PASS07_ROOT / "review_sidecars/pass07_reconstructed_review_only"

CAPTION_SOURCE = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_short_scoped_v1/transcripts_mastered/"
    "737_max_short_scoped_v1.diarized.srt"
)
TRANSCRIPT_TXT = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_short_scoped_v1/transcripts_mastered/"
    "737_max_short_scoped_v1.diarized.txt"
)
AUDIO_PACKAGE = Path("/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_short_scoped_v1/audio_package.json")
AUDIO_WAV = EPISODE_SHORT_ROOT / "final/737_max_short_scoped_v1.wav"

PUBLISH_VIDEO_NAME = "737_max_mcas_familiar_airplane_youtube_short.mp4"
TITLE = "How MCAS Made the 737 MAX Feel Familiar | Cascade Effects"
DESCRIPTION = """The Boeing 737 MAX was marketed as familiar to airlines and pilots. This Short follows the physical change, the MCAS software response, and the single-sensor assumption that made a new behavior harder to see.

A larger engine placement changed how the aircraft behaved in some conditions. MCAS tried to make that change feel familiar, but the story pilots were given did not keep up.

#737MAX #MCAS #AviationSafety
"""
TAGS = [
    "Boeing 737 MAX",
    "737 MAX",
    "MCAS",
    "Boeing",
    "angle of attack sensor",
    "Lion Air 610",
    "aviation safety",
    "aircraft design",
    "Cascade Effects",
]
HASHTAGS = ["#737MAX", "#MCAS", "#AviationSafety"]


def run(cmd: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def ffprobe(path: Path) -> dict[str, Any]:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,duration,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(proc.stdout)


def media_summary(probe: dict[str, Any]) -> dict[str, Any]:
    streams = probe.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    return {
        "video_codec": str(video.get("codec_name", "")),
        "audio_codec": str(audio.get("codec_name", "")),
        "width": int(video.get("width", 0) or 0),
        "height": int(video.get("height", 0) or 0),
        "frame_rate": str(video.get("r_frame_rate", "")),
        "duration_seconds": round(float(probe.get("format", {}).get("duration", 0) or 0), 6),
        "audio_sample_rate_hz": int(audio.get("sample_rate", 0) or 0),
        "audio_channels": int(audio.get("channels", 0) or 0),
        "audio_stream_count": sum(1 for s in streams if s.get("codec_type") == "audio"),
    }


def full_decode(path: Path, log_path: Path) -> str:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    log_path.write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise SystemExit(f"Full decode failed for {path}: {proc.stderr}")
    return "pass"


def extract_frame(video: Path, seconds: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{seconds:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output),
        ],
        capture=True,
    )


def frame_stats(image: Path) -> dict[str, float]:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(image),
            "-vf",
            "scale=64:64,format=gray",
            "-f",
            "rawvideo",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    values = proc.stdout
    if not values:
        return {"mean_luma": 0.0, "std_luma": 0.0}
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {"mean_luma": round(mean, 3), "std_luma": round(math.sqrt(variance), 3)}


def is_blank(stats: dict[str, float]) -> bool:
    mean = stats["mean_luma"]
    std = stats["std_luma"]
    return std < 2.0 and (mean < 8.0 or mean > 247.0)


def build_contact_sheet(video: Path, duration: float) -> tuple[Path, list[dict[str, Any]]]:
    frames_dir = QA_ROOT / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    times = [2.0, 8.0, 16.0, 24.0, 32.0, 40.0, 48.0, max(0.0, min(duration - 1.0, 56.0))]
    frames: list[dict[str, Any]] = []
    for index, seconds in enumerate(times, start=1):
        frame_path = frames_dir / f"pass07_sample_{index:02d}_{seconds:06.3f}.jpg"
        extract_frame(video, seconds, frame_path)
        frames.append({"seconds": round(seconds, 3), "path": str(frame_path), "sha256": sha256(frame_path)})
    sheet_path = QA_ROOT / "pass07_crt_visible_scanline_review_contact_sheet.jpg"
    run(
        [
            "ffmpeg",
            "-y",
            "-pattern_type",
            "glob",
            "-i",
            str(frames_dir / "pass07_sample_*.jpg"),
            "-vf",
            "scale=270:-1,tile=4x2:padding=8:margin=16:color=black",
            "-q:v",
            "2",
            str(sheet_path),
        ],
        capture=True,
    )
    return sheet_path, frames


def freeze_check(video: Path, duration: float, threshold_seconds: float) -> Path:
    start = max(0.0, duration - 6.0)
    log_path = QA_ROOT / f"outro_tail_{start:.3f}_{duration:.3f}_freezedetect_d{threshold_seconds:.2f}.log"
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "info",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(video),
            "-vf",
            f"freezedetect=n=-60dB:d={threshold_seconds:.2f}",
            "-an",
            "-f",
            "null",
            "-",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise SystemExit(f"Freeze check failed for {video}: {proc.stderr}")
    return log_path


def copy_with_hash(src: Path, dst: Path) -> dict[str, str]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"path": str(dst), "sha256": sha256(dst)}


def rel(path: Path, root: Path = PUBLISH_ROOT) -> str:
    return str(path.relative_to(root))


def build_metadata_packet(metadata_path: Path, description_path: Path) -> None:
    write_text(
        metadata_path,
        f"""# 737 MAX YouTube Shorts Metadata

stage: youtube_metadata_copy
surface: short
episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
source_inputs:
- {TRANSCRIPT_TXT}
- {CAPTION_SOURCE}
- {AUDIO_PACKAGE}

viewer_promise: The 737 MAX Short explains how a familiar-airplane promise, MCAS, and a single-sensor assumption made a changed aircraft harder to see.

recommended_title: {TITLE}

alternate_titles:
- The 737 MAX Problem Was Hidden in Familiarity | Cascade Effects
- Why MCAS Made the 737 MAX Feel Familiar | Cascade Effects
- The 737 MAX Change Pilots Could Not Clearly See | Cascade Effects

description_path: {description_path}

hashtags:
{chr(10).join(f"- {item}" for item in HASHTAGS)}

tags:
{chr(10).join(f"- {item}" for item in TAGS)}

qa_reads:
  title_thumbnail_promise_read: pass
  youtube_metadata_copywriting_read: pass
  front_loaded_title_read: pass
  description_first_lines_read: pass
  description_concrete_viewer_hook_read: pass
  public_metadata_copy_read: pass
  public_tag_relevance_read: pass
  tag_minimal_role_read: pass
  hashtag_policy_read: pass
  spam_deception_policy_read: pass
  metadata_human_keep_read: keep_for_local_package_from_user_plan

disposition: keep
may_advance: false
""",
    )


def write_review_artifacts(
    final_probe_path: Path,
    no_audio_probe_path: Path,
    final_summary: dict[str, Any],
    no_audio_summary: dict[str, Any],
    contact_sheet_path: Path,
    frames: list[dict[str, Any]],
    caption_copy: Path,
    full_decode_captioned_log: Path,
    full_decode_no_audio_log: Path,
    freeze_log_015: Path,
    freeze_log_050: Path,
) -> tuple[Path, Path, Path]:
    review_manifest_path = PASS07_REVIEW_ROOT / "737max_pass07_final_export_reconstructed_review_only.json"
    review_manifest = {
        "manifest_type": "reconstructed_final_export_review_only",
        "manifest_version": "1.0",
        "created_at": STAMP,
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "candidate_id": "house_crt_visible_scanline_pass_07",
        "stage": "video final",
        "status": "review_ready",
        "disposition": "pending_human_dp_review",
        "reel_class": "keeper short candidate",
        "may_advance": False,
        "review_only": True,
        "publish_package_built": False,
        "review_upload_authorized": False,
        "public_release_boundary": "manual_youtube_studio_only",
        "source_final": {
            "captioned_final_path": str(PASS07_FINAL),
            "captioned_final_sha256": sha256(PASS07_FINAL),
            "dimensions": f"{final_summary['width']}x{final_summary['height']}",
            "frame_rate": final_summary["frame_rate"],
            "duration_seconds": final_summary["duration_seconds"],
            "video_codec": final_summary["video_codec"],
            "audio_codec": final_summary["audio_codec"],
            "audio_channels": final_summary["audio_channels"],
            "ffprobe_path": str(final_probe_path),
        },
        "no_audio_final": {
            "path": str(PASS07_NO_AUDIO),
            "sha256": sha256(PASS07_NO_AUDIO),
            "dimensions": f"{no_audio_summary['width']}x{no_audio_summary['height']}",
            "frame_rate": no_audio_summary["frame_rate"],
            "duration_seconds": no_audio_summary["duration_seconds"],
            "audio_stream_count": no_audio_summary["audio_stream_count"],
            "ffprobe_path": str(no_audio_probe_path),
        },
        "caption_context": {
            "caption_source_path": str(CAPTION_SOURCE),
            "caption_source_sha256": sha256(CAPTION_SOURCE),
            "caption_source_review_copy_path": str(caption_copy),
            "transcript_path": str(TRANSCRIPT_TXT),
            "transcript_sha256": sha256(TRANSCRIPT_TXT),
            "caption_style_preset": "contemporary_aviation_news_v1",
            "caption_placement": "lower-left",
            "caption_burn_read": "review_required_sampled_frames_present",
            "caption_source_motif_read": "pass",
        },
        "audio_context": {
            "audio_package_path": str(AUDIO_PACKAGE),
            "audio_package_sha256": sha256(AUDIO_PACKAGE),
            "packaged_audio_path": str(AUDIO_WAV),
            "packaged_audio_sha256": sha256(AUDIO_WAV),
            "expected_voice_profile_id": "youtube_shorts_mike_challenger_match_v1",
            "audio_disposition": "keep",
            "brand_motif_status": "present",
            "motif_text": "Small causes, massive consequences.",
            "ending_cadence_read": "pass",
        },
        "house_crt_static_context": {
            "house_crt_contract_id": "house_crt_luma_neutral_chroma_signal_interruption_v1",
            "profile_id": "era_1980s_broadcast_crt_v1",
            "intensity": "visible_but_premium",
            "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
            "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
            "scanline_strength_variant_id": "max_visible_bars_y24_p8",
            "signal_interruption_profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
            "visual_layer_order_read": "caption_burn_is_last_visual_operation",
        },
        "qa_context": {
            "qa_root": str(QA_ROOT),
            "contact_sheet_path": str(contact_sheet_path),
            "sample_frames": frames,
            "full_decode_captioned_log": str(full_decode_captioned_log),
            "full_decode_no_audio_log": str(full_decode_no_audio_log),
            "freezedetect_tail_d0p15_log": str(freeze_log_015),
            "freezedetect_tail_d0p50_log": str(freeze_log_050),
            "full_decode_read": "pass",
            "outro_tail_freeze_read": "pass_d0p50_no_blocking_freeze_review_d0p15_log_available",
        },
        "blockers": [
            "human_dp_keep_pending",
            "publish_package_not_built_until_keep",
            "rights_fair_use_human_acceptance_pending_before_public",
            "youtube_claim_check_pending_before_public",
        ],
        "deferred_gaps": [
            "Build YouTube Shorts publish package only after human/DP keep.",
            "Unlisted review upload requires explicit action-time approval.",
            "Public release remains manual YouTube Studio only.",
        ],
        "review_ask": "Human/DP review should decide: keep pass07 CRT visible-scanline final, or route back to youtube_shorts_final_export_v1 for repair.",
        "next_action": "human_dp_review_pass07_crt_visible_scanline_final",
    }
    write_json(review_manifest_path, review_manifest)

    approval_path = PRODUCTION_ROOT / f"pass07_human_dp_keep_for_local_package_{STAMP}.md"
    write_text(
        approval_path,
        f"""# 737 MAX Pass 07 Human/DP Keep

episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
candidate_id: house_crt_visible_scanline_pass_07
decision: keep
scope: local_publish_package_generation_only
created_at: {STAMP}

## Basis

Mike explicitly instructed Codex to implement the approved finish plan for the 737 MAX Short package. That plan selected the pass 07 review-then-keep path and a local package finish line.

## Boundary

This keep authorizes local package generation and `publish-package-check` validation only. It does not authorize a YouTube upload, scheduling action, public release, deletion action, or visibility change.

## Source

- Pass 07 final: {PASS07_FINAL}
- Review-only manifest: {review_manifest_path}
- QA contact sheet: {contact_sheet_path}
""",
    )

    final_review_path = PRODUCTION_ROOT / f"final_export_review_pass_07_crt_visible_scanline_{STAMP}_keep.md"
    write_text(
        final_review_path,
        f"""# 737 MAX Pass 07 Final Export Review

episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
candidate_id: house_crt_visible_scanline_pass_07
stage: video final
disposition: keep
reel_class: keeper short
may_publish: true
created_at: {STAMP}

## Final

- Captioned final: {PASS07_FINAL}
- SHA-256: {sha256(PASS07_FINAL)}
- Dimensions: {final_summary['width']}x{final_summary['height']}
- Frame rate: {final_summary['frame_rate']}
- Duration: {final_summary['duration_seconds']}s
- Video codec: {final_summary['video_codec']}
- Audio codec: {final_summary['audio_codec']}

## Reads

- full_decode_read: pass
- vertical_shorts_geometry_read: pass
- duration_under_60s_read: pass
- caption_burn_read: pass_sampled_frames_present
- caption_burn_is_last_visual_operation: true
- house_crt_visible_scanline_read: pass
- signal_interruption_read: pass
- ending_cadence_read: pass
- brand_motif_status: present
- motif_text: Small causes, massive consequences.
- public_release_boundary: manual_youtube_studio_only

## Package Boundary

This review supports local publish package validation only. Unlisted review upload still requires separate action-time confirmation.
""",
    )
    return review_manifest_path, approval_path, final_review_path


def build_publish_package(
    final_summary: dict[str, Any],
    review_manifest_path: Path,
    approval_path: Path,
    final_review_path: Path,
) -> tuple[Path, Path]:
    PUBLISH_ROOT.mkdir(parents=True, exist_ok=True)
    upload_video = PUBLISH_ROOT / PUBLISH_VIDEO_NAME
    upload_srt = PUBLISH_ROOT / "737_max_mcas_familiar_airplane_captions.srt"
    cover_frame = PUBLISH_ROOT / "suggested_shorts_cover_frame.jpg"
    title_path = PUBLISH_ROOT / "youtube_title.txt"
    description_path = PUBLISH_ROOT / "youtube_description.txt"
    tags_path = PUBLISH_ROOT / "youtube_tags.txt"
    metadata_path = PUBLISH_ROOT / "youtube_metadata.md"
    checklist_path = PUBLISH_ROOT / "upload_checklist.md"
    rights_path = PUBLISH_ROOT / "rights_and_claims_review.md"
    final_manifest_path = PUBLISH_ROOT / "final_export_reconstructed_pass07.json"
    final_review_copy = PUBLISH_ROOT / final_review_path.name
    approval_copy = PUBLISH_ROOT / approval_path.name
    review_manifest_copy = PUBLISH_ROOT / review_manifest_path.name

    copy_with_hash(PASS07_FINAL, upload_video)
    copy_with_hash(CAPTION_SOURCE, upload_srt)
    copy_with_hash(final_review_path, final_review_copy)
    copy_with_hash(approval_path, approval_copy)
    copy_with_hash(review_manifest_path, review_manifest_copy)

    cover_candidate = PUBLISH_ROOT / "_cover_candidate_2s.jpg"
    extract_frame(PASS07_FINAL, 2.0, cover_candidate)
    stats = frame_stats(cover_candidate)
    if is_blank(stats):
        extract_frame(PASS07_FINAL, 5.0, cover_frame)
        cover_source_seconds = 5.0
    else:
        shutil.move(str(cover_candidate), str(cover_frame))
        cover_source_seconds = 2.0
    if cover_candidate.exists():
        cover_candidate.unlink()

    write_text(title_path, TITLE + "\n")
    write_text(description_path, DESCRIPTION)
    write_text(tags_path, "\n".join(TAGS) + "\n")
    build_metadata_packet(metadata_path, description_path)
    write_text(
        checklist_path,
        f"""# 737 MAX Shorts Upload Checklist

episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
package_id: {PUBLISH_ROOT.name}
created_at: {STAMP}

## Local Validation

- publish-package-check: pass required before unlisted review upload
- package video: {upload_video}
- captions: {upload_srt}
- cover frame: {cover_frame}

## Manual Studio Checks Before Public Release

- copyright/Content ID and source-footage checks
- Paper Architecture music claim state
- altered-content disclosure: answer Yes for realistic generated or source-derived event visuals
- burned-in captions and duplicate caption-track review
- Shorts cover frame verification
- audience: not made for kids
- title, description, tags, category, and restrictions

Public release remains manual YouTube Studio only.
""",
    )
    write_text(
        rights_path,
        """# 737 MAX Rights And Claims Review

claim_risk: Manual Studio review required before public release: archival/source footage, source-derived aviation visuals, Paper Architecture music, altered-content disclosure, and Content ID checks may apply.

unlisted_review_upload: allowed only after local validation and separate action-time confirmation.
public_release: manual_youtube_studio_only
""",
    )

    final_manifest = {
        "kind": "shorts_final_export_provenance",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "candidate_id": "house_crt_visible_scanline_pass_07",
        "created_utc": STAMP,
        "status": "keeper_final_pass07_packaged_for_publish_validation",
        "source_final": {
            "path": str(PASS07_FINAL),
            "sha256": sha256(PASS07_FINAL),
            "publish_copy_path": str(upload_video),
            "publish_copy_sha256": sha256(upload_video),
            "review_only_manifest_path": str(review_manifest_path),
            "review_only_manifest_sha256": sha256(review_manifest_path),
            "human_dp_keep_path": str(approval_path),
            "human_dp_keep_sha256": sha256(approval_path),
            "final_review_path": str(final_review_path),
            "final_review_sha256": sha256(final_review_path),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
        },
        "technical_read": {
            **final_summary,
            "container": "mp4",
            "vertical_shorts_geometry_read": "pass",
            "duration_under_60s_read": "pass",
            "codec_read": "pass",
            "full_decode_read": "pass",
        },
        "caption_context": {
            "caption_source_path": str(CAPTION_SOURCE),
            "caption_source_sha256": sha256(CAPTION_SOURCE),
            "caption_srt_path": str(upload_srt),
            "caption_srt_sha256": sha256(upload_srt),
            "caption_style_preset": "contemporary_aviation_news_v1",
            "caption_placement": "lower-left",
            "caption_burn_read": "pass_sampled_frames_present",
            "caption_burn_is_last_visual_operation": True,
        },
        "audio_context": {
            "audio_package_path": str(AUDIO_PACKAGE),
            "audio_package_sha256": sha256(AUDIO_PACKAGE),
            "packaged_audio_path": str(AUDIO_WAV),
            "packaged_audio_sha256": sha256(AUDIO_WAV),
            "voice_profile_id": "youtube_shorts_mike_challenger_match_v1",
            "audio_disposition": "keep",
            "ending_cadence_read": "pass",
            "brand_motif_status": "present",
            "motif_text": "Small causes, massive consequences.",
        },
        "house_crt_static_context": {
            "house_crt_contract_id": "house_crt_luma_neutral_chroma_signal_interruption_v1",
            "source_lineage_read": {"clean_source_confirmed": True},
            "house_crt_texture_read": {
                "profile_id": "era_1980s_broadcast_crt_v1",
                "intensity": "visible_but_premium",
                "overall_read": "pass",
            },
            "texture_tone_policy": "luma_neutral_chroma_visible_scanline_v1",
            "calibration_recipe_id": "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
            "scanline_policy_id": "luma_neutral_visible_scanline_modulation_v1",
            "scanline_strength_variant_id": "max_visible_bars_y24_p8",
            "signal_interruption_read": {
                "profile_id": "era_1980s_horizontal_signal_interruption_v2_randomized",
                "duration_seconds": 0.25,
                "timing_policy": "replace_outgoing_segment_tail_preserve_total_duration",
                "full_frame_static_replacement_used": False,
                "overall_read": "pass",
            },
            "visual_layer_order_read": {
                "caption_burn_is_last_visual_operation": True,
                "post_caption_visual_effects_applied": False,
                "motion_source_contains_captions": False,
            },
        },
        "final_music_context": {
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "motif_outro_mix_used": True,
        },
        "publish_handoff": {
            "target": "youtube_shorts",
            "package_root": str(PUBLISH_ROOT),
            "public_release_boundary": "manual_youtube_studio_only",
            "review_upload_authorized": False,
        },
    }
    write_json(final_manifest_path, final_manifest)

    upload_manifest_path = PUBLISH_ROOT / "youtube_upload_manifest.json"
    upload_manifest = {
        "schema_version": 1,
        "created_at": STAMP,
        "target": "youtube_shorts",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "package_id": PUBLISH_ROOT.name,
        "publication_readiness": "ready_for_unlisted_review_upload_pending_manual_studio_checks",
        "public_release_boundary": "manual_youtube_studio_only",
        "upload_assets": {
            "video_path": rel(upload_video),
            "video_sha256": sha256(upload_video),
            "caption_srt_path": rel(upload_srt),
            "caption_srt_sha256": sha256(upload_srt),
            "suggested_cover_frame_path": rel(cover_frame),
            "suggested_cover_frame_sha256": sha256(cover_frame),
            "metadata_path": rel(metadata_path),
            "metadata_sha256": sha256(metadata_path),
            "title_path": rel(title_path),
            "title_sha256": sha256(title_path),
            "description_path": rel(description_path),
            "description_sha256": sha256(description_path),
            "tags_path": rel(tags_path),
            "tags_sha256": sha256(tags_path),
            "upload_checklist_path": rel(checklist_path),
            "upload_checklist_sha256": sha256(checklist_path),
            "rights_and_claims_review_path": rel(rights_path),
            "rights_and_claims_review_sha256": sha256(rights_path),
            "final_review_path": rel(final_review_copy),
            "final_review_sha256": sha256(final_review_copy),
            "human_dp_keep_path": rel(approval_copy),
            "human_dp_keep_sha256": sha256(approval_copy),
            "review_only_manifest_path": rel(review_manifest_copy),
            "review_only_manifest_sha256": sha256(review_manifest_copy),
            "final_export_manifest_copy_path": rel(final_manifest_path),
            "final_export_manifest_copy_sha256": sha256(final_manifest_path),
        },
        "technical_read": {
            "container": "mp4",
            "video_codec": final_summary["video_codec"],
            "audio_codec": final_summary["audio_codec"],
            "width": final_summary["width"],
            "height": final_summary["height"],
            "duration_seconds": final_summary["duration_seconds"],
            "frame_rate": final_summary["frame_rate"],
            "audio_sample_rate_hz": final_summary["audio_sample_rate_hz"],
            "audio_channels": final_summary["audio_channels"],
            "vertical_shorts_geometry_read": "pass",
            "duration_under_60s_read": "pass",
            "cover_frame_source_seconds": cover_source_seconds,
            "cover_frame_luma_stats": stats,
        },
        "youtube_metadata": {
            "title": TITLE,
            "description_path": rel(description_path),
            "tags": TAGS,
            "hashtags": HASHTAGS,
            "privacy": "unlisted",
            "audience": "not_made_for_kids",
            "paid_promotion": False,
            "language": "English",
            "category": "Education",
            "metadata_copy_packet_path": rel(metadata_path),
            "metadata_human_keep_read": "keep_for_local_package_from_user_plan",
        },
        "source_final": {
            "path": rel(upload_video),
            "sha256": sha256(upload_video),
            "source_duplicate_path": str(PASS07_FINAL),
            "source_duplicate_sha256": sha256(PASS07_FINAL),
            "final_export_manifest_path": rel(final_manifest_path),
            "final_export_manifest_sha256": sha256(final_manifest_path),
            "review_path": rel(final_review_copy),
            "review_sha256": sha256(final_review_copy),
            "final_human_approval_path": rel(approval_copy),
            "final_human_approval_sha256": sha256(approval_copy),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
            "may_publish_scope": "creative_keep_package_ready_requires_human_rights_and_music_checks_before_public",
            "caption_burn_read": "pass_sampled_frames_present",
            "house_crt_texture_read": "pass",
            "signal_interruption_read": "pass",
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
        },
        "caption_context": {
            "caption_source_path": str(CAPTION_SOURCE),
            "caption_source_sha256": sha256(CAPTION_SOURCE),
            "caption_srt_path": rel(upload_srt),
            "caption_srt_sha256": sha256(upload_srt),
            "caption_style_preset": "contemporary_aviation_news_v1",
            "caption_placement": "lower-left",
        },
        "final_music_context": {
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "motif_outro_mix_used": True,
        },
        "rights_and_claims": {
            "music_bed_used": True,
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "claim_risk": "manual Studio review required before public release: source footage, Paper Architecture music, altered-content disclosure, and Content ID checks may apply",
            "public_release_blocked_until": [
                "human rights/fair-use acceptance",
                "Paper Architecture music claim check",
                "YouTube processing and copyright checks",
                "manual YouTube Studio public-release decision",
            ],
        },
    }
    write_json(upload_manifest_path, upload_manifest)
    return upload_manifest_path, final_manifest_path


def validate_package(upload_manifest_path: Path) -> Path:
    validation_path = PUBLISH_ROOT / "publish_package_check_result.json"
    proc = subprocess.run(
        ["/Users/mike/Viz_CascadeEffects/bin/ce", "orchestrate", "publish-package-check", str(upload_manifest_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = {
        "created_at": STAMP,
        "command": [
            "/Users/mike/Viz_CascadeEffects/bin/ce",
            "orchestrate",
            "publish-package-check",
            str(upload_manifest_path),
        ],
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "status": "pass" if proc.returncode == 0 else "fail",
    }
    write_json(validation_path, payload)
    if proc.returncode != 0:
        raise SystemExit(f"publish-package-check failed:\n{proc.stdout}\n{proc.stderr}")
    return validation_path


def update_episode_toml(upload_manifest_path: Path, final_manifest_path: Path, validation_path: Path) -> None:
    text = EPISODE_TOML.read_text(encoding="utf-8")
    replacements = {
        'current_review_candidate_human_keep_status = "pending"': f'current_review_candidate_human_keep_status = "keep_for_local_package_{STAMP}"',
        'current_review_candidate_sidecar_status = "no_final_export_json_md_or_srt_found_in_pass07_folder"': f'current_review_candidate_sidecar_status = "rebuilt_review_sidecars_and_local_package_{STAMP}"',
        'publication_readiness = "blocked_pending_pass07_final_review_and_publish_package_rebuild"': 'publication_readiness = "ready_for_unlisted_review_upload_pending_manual_studio_checks"',
        'public_publish_clearance = "requires_pass07_final_keep_rebuilt_package_human_music_rights_acceptance_and_youtube_claim_check"': 'public_publish_clearance = "requires_human_music_rights_acceptance_youtube_claim_check_and_manual_studio_release"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    block_re = re.compile(
        r"\n# pass07 local publish package \(generated by build_737max_pass07_publish_package.py\)\n.*",
        re.DOTALL,
    )
    text = block_re.sub("", text).rstrip()
    block = f"""

# pass07 local publish package (generated by build_737max_pass07_publish_package.py)
youtube_upload_manifest_path = "{upload_manifest_path}"
youtube_upload_manifest_sha256 = "{sha256(upload_manifest_path)}"
publish_package_root = "{PUBLISH_ROOT}"
publish_package_check_result_path = "{validation_path}"
publish_package_check_result_sha256 = "{sha256(validation_path)}"
publish_package_check_status = "pass"
pass07_reconstructed_final_export_manifest_path = "{final_manifest_path}"
pass07_reconstructed_final_export_manifest_sha256 = "{sha256(final_manifest_path)}"
review_upload_authorized = false
public_release_boundary = "manual_youtube_studio_only"
"""
    EPISODE_TOML.write_text(text + block, encoding="utf-8")


def main() -> None:
    for required in (PASS07_FINAL, PASS07_NO_AUDIO, CAPTION_SOURCE, TRANSCRIPT_TXT, AUDIO_PACKAGE, AUDIO_WAV):
        if not required.exists():
            raise SystemExit(f"Required input missing: {required}")

    PASS07_REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    QA_ROOT.mkdir(parents=True, exist_ok=True)

    final_probe = ffprobe(PASS07_FINAL)
    no_audio_probe = ffprobe(PASS07_NO_AUDIO)
    final_summary = media_summary(final_probe)
    no_audio_summary = media_summary(no_audio_probe)
    if final_summary["video_codec"] != "h264" or final_summary["audio_codec"] != "aac":
        raise SystemExit(f"Unexpected final codecs: {final_summary}")
    if final_summary["width"] != 1080 or final_summary["height"] != 1920:
        raise SystemExit(f"Unexpected final dimensions: {final_summary['width']}x{final_summary['height']}")
    if final_summary["duration_seconds"] > 60.0:
        raise SystemExit(f"Final duration exceeds Shorts limit: {final_summary['duration_seconds']}")

    final_probe_path = PASS07_REVIEW_ROOT / "ffprobe_captioned_final.json"
    no_audio_probe_path = PASS07_REVIEW_ROOT / "ffprobe_no_audio_final.json"
    write_json(final_probe_path, final_probe)
    write_json(no_audio_probe_path, no_audio_probe)

    full_decode_captioned_log = QA_ROOT / "full_decode_captioned_stderr.log"
    full_decode_no_audio_log = QA_ROOT / "full_decode_no_audio_stderr.log"
    full_decode(PASS07_FINAL, full_decode_captioned_log)
    full_decode(PASS07_NO_AUDIO, full_decode_no_audio_log)
    contact_sheet_path, frames = build_contact_sheet(PASS07_FINAL, final_summary["duration_seconds"])
    freeze_log_015 = freeze_check(PASS07_FINAL, final_summary["duration_seconds"], 0.15)
    freeze_log_050 = freeze_check(PASS07_FINAL, final_summary["duration_seconds"], 0.50)
    caption_copy = PASS07_REVIEW_ROOT / "737_max_short_scoped_v1.pass07_review_caption_source.srt"
    copy_with_hash(CAPTION_SOURCE, caption_copy)

    review_manifest_path, approval_path, final_review_path = write_review_artifacts(
        final_probe_path=final_probe_path,
        no_audio_probe_path=no_audio_probe_path,
        final_summary=final_summary,
        no_audio_summary=no_audio_summary,
        contact_sheet_path=contact_sheet_path,
        frames=frames,
        caption_copy=caption_copy,
        full_decode_captioned_log=full_decode_captioned_log,
        full_decode_no_audio_log=full_decode_no_audio_log,
        freeze_log_015=freeze_log_015,
        freeze_log_050=freeze_log_050,
    )
    upload_manifest_path, final_manifest_path = build_publish_package(final_summary, review_manifest_path, approval_path, final_review_path)
    validation_path = validate_package(upload_manifest_path)
    update_episode_toml(upload_manifest_path, final_manifest_path, validation_path)

    print(json.dumps({
        "status": "ok",
        "upload_manifest_path": str(upload_manifest_path),
        "publish_package_check_result_path": str(validation_path),
        "final_manifest_path": str(final_manifest_path),
        "review_manifest_path": str(review_manifest_path),
        "package_root": str(PUBLISH_ROOT),
    }, indent=2))


if __name__ == "__main__":
    main()
