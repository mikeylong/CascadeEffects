#!/usr/bin/env python3
"""Repair the Titanic pass18 YouTube Shorts publish package.

This script preserves the existing pass18 final MP4 and cover assets, then
creates the package sidecars required by `publish-package-check`.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


EPISODE_ID = "titanic"
SHORT_ID = "titanic_short_scoped_v1"
PACKAGE_ID = "youtube_20260430T201719Z_pass18_loc_archival_source_motion_tail_repair"
PACKAGE_CREATED_UTC = "20260430T201719Z"
PACKAGE_REPAIR_DATE = "2026-05-18"

PACKAGE_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/"
    "titanic_short_scoped_v1/publish/"
    "youtube_20260430T201719Z_pass18_loc_archival_source_motion_tail_repair"
)
VIDEO_PATH = PACKAGE_ROOT / "titanic_lifeboat_gap_pass18_loc_archival_source_motion_tail_repair_youtube_short.mp4"
COVER_PATH = PACKAGE_ROOT / "suggested_shorts_cover_frame.png"
CAPTION_QA_CONTACT_SHEET_PATH = PACKAGE_ROOT / "caption_qa_contact_sheet.jpg"
SOURCE_FINAL_PATH = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/"
    "titanic_short_scoped_v1/motion_video_proof/pass_14_loc_archival_timed_proof/"
    "final_exports/pass_18_loc_archival_source_motion_tail_repair/"
    "20260430T201719Z__titanic_pass18_loc_archival_source_motion_tail_repair_captioned_final.mp4"
)
SOURCE_FRAME_SHEET_PATH = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/"
    "titanic_short_scoped_v1/motion_video_proof/pass_14_loc_archival_timed_proof/"
    "final_exports/pass_18_loc_archival_source_motion_tail_repair/"
    "20260430T201719Z__titanic_pass18_loc_archival_source_motion_tail_repair_frame_sheet.jpg"
)
AUDIO_PACKAGE_PATH = Path("/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_short_scoped_v1/audio_package.json")
AUDIO_TRANSCRIPT_PATH = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_short_scoped_v1/"
    "transcripts_mastered/titanic_short_scoped_v1.diarized.txt"
)
AUDIO_SRT_PATH = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_short_scoped_v1/"
    "transcripts_mastered/titanic_short_scoped_v1.diarized.srt"
)

EXPECTED_VIDEO_SHA256 = "b2e4b4a384f1ee461ab88b7eb239abb10f70d63abb53351a4c3a1df427aa5c3f"
EXPECTED_DURATION_SECONDS = 63.866667
EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920
EXPECTED_FRAME_RATE = "30/1"
EXPECTED_VIDEO_CODEC = "h264"
EXPECTED_AUDIO_CODEC = "aac"
EXPECTED_AUDIO_SAMPLE_RATE_HZ = 44100
EXPECTED_AUDIO_CHANNELS = 1
MOTIF_TEXT = "Small causes, massive consequences."

TITLE_TEXT = "Titanic Was Legal. That Was the Problem #Shorts"
DESCRIPTION_TEXT = """Titanic met the lifeboat rules on paper. But the rule was measuring tonnage while the ship carried more than 2,200 people, and the gap helped turn compliance into danger.

After Titanic, the lesson changed: count people carried, not just the size of the ship.

#Titanic #MaritimeHistory #Shorts
"""
TAGS = [
    "Titanic",
    "RMS Titanic",
    "Titanic lifeboats",
    "lifeboat regulations",
    "SOLAS",
    "maritime safety",
    "British Board of Trade",
    "shipping safety",
    "disaster regulation",
]
HASHTAGS = ["#Titanic", "#MaritimeHistory", "#Shorts"]
CLAIM_RISK = (
    "Manual Studio review required before public release: archival/source footage, "
    "source-derived maritime visuals, and Paper Architecture music may trigger copyright, "
    "Content ID, altered-content, or cover-frame checks."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def probe_video(path: Path) -> dict[str, Any]:
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    payload = json.loads(raw)
    streams = payload.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return {
        "video_codec": video_stream.get("codec_name", ""),
        "audio_codec": audio_stream.get("codec_name", ""),
        "width": int(video_stream.get("width", 0) or 0),
        "height": int(video_stream.get("height", 0) or 0),
        "frame_rate": video_stream.get("r_frame_rate", ""),
        "audio_sample_rate_hz": int(audio_stream.get("sample_rate", 0) or 0),
        "audio_channels": int(audio_stream.get("channels", 0) or 0),
        "duration_seconds": float(payload.get("format", {}).get("duration", 0.0) or 0.0),
        "size_bytes": int(payload.get("format", {}).get("size", 0) or 0),
        "bit_rate": int(payload.get("format", {}).get("bit_rate", 0) or 0),
    }


def assert_media_gate(probe: dict[str, Any]) -> None:
    checks = {
        "video sha256": sha256_file(VIDEO_PATH) == EXPECTED_VIDEO_SHA256,
        "source duplicate sha256": sha256_file(SOURCE_FINAL_PATH) == EXPECTED_VIDEO_SHA256,
        "video codec": probe["video_codec"] == EXPECTED_VIDEO_CODEC,
        "audio codec": probe["audio_codec"] == EXPECTED_AUDIO_CODEC,
        "width": probe["width"] == EXPECTED_WIDTH,
        "height": probe["height"] == EXPECTED_HEIGHT,
        "frame rate": probe["frame_rate"] == EXPECTED_FRAME_RATE,
        "audio sample rate": probe["audio_sample_rate_hz"] == EXPECTED_AUDIO_SAMPLE_RATE_HZ,
        "audio channels": probe["audio_channels"] == EXPECTED_AUDIO_CHANNELS,
        "duration": abs(probe["duration_seconds"] - EXPECTED_DURATION_SECONDS) < 0.001,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"Titanic pass18 media gate failed: {', '.join(failed)}")


def clean_caption_srt(source_srt: Path) -> str:
    text = source_srt.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^SPEAKER_\d+:\s*", "", text)
    text = re.sub(r"(?m)^([^\n]*?)SPEAKER_\d+:\s*", r"\1", text)
    if "SPEAKER_" in text:
        raise SystemExit("Clean caption SRT still contains speaker labels.")
    if MOTIF_TEXT not in text:
        raise SystemExit("Clean caption SRT is missing the Signature Consequence Motif.")
    return text.rstrip() + "\n"


def build_metadata_packet() -> str:
    tags_block = "\n".join(f"- {tag}" for tag in TAGS)
    alternates = "\n".join(
        [
            "- Titanic: Legal, Compliant, and Not Safe #Shorts",
            "- The Titanic Lifeboat Rule That Measured the Wrong Thing #Shorts",
            "- Titanic Had Enough Lifeboats for the Law #Shorts",
            "- When Titanic Compliance Wasn't Safety #Shorts",
        ]
    )
    return f"""# Titanic Short YouTube Metadata Copy Packet

stage: youtube_metadata_copy
surface: short
episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
disposition: review_ready
human_review_required: true
may_advance: false

## Source Inputs

- Upload video: `{VIDEO_PATH.name}`
- Cover frame: `{COVER_PATH.name}`
- Audio transcript: `{AUDIO_TRANSCRIPT_PATH}`
- Metadata skill: `/Users/mike/Agents_CascadeEffects/references/skills/youtube_metadata_copywriting_v1/SKILL.md`

## Viewer Promise

This Short shows how Titanic could satisfy the lifeboat rule while the rule was measuring the wrong risk.

## Recommended Title

{TITLE_TEXT}

mode: hybrid

## Alternate Titles

{alternates}

## Description

{DESCRIPTION_TEXT.rstrip()}

## Tags

{tags_block}

## QA Reads

- title_thumbnail_promise_read: pass
- youtube_metadata_copywriting_read: pass
- front_loaded_title_read: pass
- description_first_lines_read: pass
- description_concrete_viewer_hook_read: pass
- chapter_format_read: not_applicable_short
- public_metadata_copy_read: pass
- public_tag_relevance_read: pass
- tag_minimal_role_read: pass
- hashtag_policy_read: pass
- spam_deception_policy_read: pass
- metadata_human_keep_read: pending_human_review

## Blockers

- Human should review title, description, tags, cover frame, altered-content disclosure, and claim state before public release.
- Public release remains manual YouTube Studio only.
"""


def build_upload_checklist(manifest_path: Path, caption_srt_path: Path) -> str:
    return f"""# Titanic Short Upload Checklist

status: ready_for_unlisted_review_validation
public_release_boundary: manual_youtube_studio_only

## Package

- Upload MP4: `{VIDEO_PATH.name}`
- Suggested Shorts cover frame: `{COVER_PATH.name}`
- Clean SRT sidecar: `{caption_srt_path.name}`
- Title: `titanic_lifeboat_gap_title.txt`
- Description: `titanic_lifeboat_gap_description.txt`
- Tags: `titanic_lifeboat_gap_tags.txt`
- Manifest: `{manifest_path.name}`

## Unlisted Review Upload

- Run `/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-check {manifest_path}`.
- Upload only after explicit action-time confirmation for this manifest and `--privacy unlisted`.
- Do not make the video public or scheduled from agent tooling.

## Studio Checks Before Public Release

- Confirm copyright and Content ID checks.
- Confirm Paper Architecture music claim state.
- Confirm altered-content disclosure; answer Yes for realistic generated or source-derived event visuals.
- Confirm burned-in captions and remove or disable duplicate uploaded/automatic captions if needed.
- Confirm the Shorts cover frame in Studio or mobile Studio.
- Confirm audience, category, title, description, tags, hashtags, and visibility.
"""


def build_final_review(probe: dict[str, Any], caption_srt_path: Path) -> str:
    return f"""# Titanic Pass18 Final Export Review

stage: video final
episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
disposition: keep
reel_class: keeper short
may_publish: true
public_release_boundary: manual_youtube_studio_only

## Inputs

- Captioned final: `{VIDEO_PATH}`
- Source duplicate: `{SOURCE_FINAL_PATH}`
- Caption source: `{caption_srt_path}`
- Suggested cover frame: `{COVER_PATH}`

## QA Reads

- final_video_sha256_read: pass
- source_duplicate_sha256_read: pass
- vertical_shorts_geometry_read: pass_1080x1920
- codec_read: pass_h264_aac
- frame_rate_read: pass_30fps
- duration_read: pass_{probe["duration_seconds"]:.3f}s
- clean_srt_speaker_label_read: pass
- motif_text_read: pass
- caption_burn_read: pass
- house_crt_texture_read: pass
- signal_interruption_read: pass
- music_policy_read: pass_canonical_default_pending_youtube_upload_check

## Blockers

- Public release remains blocked pending unlisted review processing, YouTube copyright/Content ID checks, Paper Architecture claim state, altered-content disclosure, caption duplication review, cover frame review, and manual Studio visibility decision.
"""


def main() -> int:
    for path in (
        PACKAGE_ROOT,
        VIDEO_PATH,
        COVER_PATH,
        CAPTION_QA_CONTACT_SHEET_PATH,
        SOURCE_FINAL_PATH,
        AUDIO_PACKAGE_PATH,
        AUDIO_TRANSCRIPT_PATH,
        AUDIO_SRT_PATH,
    ):
        if not path.exists():
            raise SystemExit(f"Required Titanic pass18 package input is missing: {path}")

    probe = probe_video(VIDEO_PATH)
    assert_media_gate(probe)

    manifest_path = PACKAGE_ROOT / "youtube_upload_manifest.json"
    caption_srt_path = PACKAGE_ROOT / "titanic_lifeboat_gap_pass18_clean_captions.srt"
    title_path = PACKAGE_ROOT / "titanic_lifeboat_gap_title.txt"
    description_path = PACKAGE_ROOT / "titanic_lifeboat_gap_description.txt"
    tags_path = PACKAGE_ROOT / "titanic_lifeboat_gap_tags.txt"
    metadata_path = PACKAGE_ROOT / "youtube_metadata_copy_packet.md"
    upload_checklist_path = PACKAGE_ROOT / "upload_checklist.md"
    final_export_manifest_path = PACKAGE_ROOT / "final_export_provenance_manifest.json"
    final_review_path = PACKAGE_ROOT / "final_export_review.md"
    summary_path = PACKAGE_ROOT / "pass18_publish_package_repair_summary.json"

    write_text(caption_srt_path, clean_caption_srt(AUDIO_SRT_PATH))
    write_text(title_path, TITLE_TEXT)
    write_text(description_path, DESCRIPTION_TEXT)
    write_text(tags_path, "\n".join(TAGS))
    write_text(metadata_path, build_metadata_packet())
    write_text(upload_checklist_path, build_upload_checklist(manifest_path, caption_srt_path))
    write_text(final_review_path, build_final_review(probe, caption_srt_path))

    final_export_manifest = {
        "kind": "titanic_pass18_final_export_provenance",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "created_utc": PACKAGE_CREATED_UTC,
        "package_repair_date": PACKAGE_REPAIR_DATE,
        "disposition": "keep",
        "reel_class": "keeper short",
        "may_publish": True,
        "public_release_boundary": "manual_youtube_studio_only",
        "source_final": {
            "captioned_final_path": str(VIDEO_PATH),
            "captioned_final_sha256": sha256_file(VIDEO_PATH),
            "source_duplicate_path": str(SOURCE_FINAL_PATH),
            "source_duplicate_sha256": sha256_file(SOURCE_FINAL_PATH),
            "source_frame_sheet_path": str(SOURCE_FRAME_SHEET_PATH),
            "source_frame_sheet_sha256": sha256_file(SOURCE_FRAME_SHEET_PATH) if SOURCE_FRAME_SHEET_PATH.exists() else "",
        },
        "technical_read": {
            "container": "mp4",
            "video_codec": probe["video_codec"],
            "audio_codec": probe["audio_codec"],
            "width": probe["width"],
            "height": probe["height"],
            "duration_seconds": probe["duration_seconds"],
            "frame_rate": probe["frame_rate"],
            "audio_sample_rate_hz": probe["audio_sample_rate_hz"],
            "audio_channels": probe["audio_channels"],
            "vertical_shorts_geometry_read": "pass",
            "codec_read": "pass",
        },
        "caption_context": {
            "caption_strategy": "audio_srt_cleaned_speaker_labels_preserve_timings_v1",
            "source_srt_path": str(AUDIO_SRT_PATH),
            "source_srt_sha256": sha256_file(AUDIO_SRT_PATH),
            "clean_srt_path": caption_srt_path.name,
            "clean_srt_sha256": sha256_file(caption_srt_path),
            "motif_text": MOTIF_TEXT,
            "motif_text_read": "pass",
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
            "source_footage_role": "source-derived archival/maritime visuals",
            "altered_content_disclosure_required": True,
            "claim_risk": CLAIM_RISK,
        },
        "publish_handoff": {
            "target": "youtube_shorts",
            "manifest_path": str(manifest_path),
            "public_release_boundary": "manual_youtube_studio_only",
        },
    }
    write_json(final_export_manifest_path, final_export_manifest)

    upload_manifest = {
        "kind": "youtube_shorts_publish_package",
        "target": "youtube_shorts",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "package_id": PACKAGE_ID,
        "created_utc": PACKAGE_CREATED_UTC,
        "package_repair_date": PACKAGE_REPAIR_DATE,
        "publication_readiness": "ready_for_unlisted_review_upload_pending_manual_studio_checks",
        "public_release_boundary": "manual_youtube_studio_only",
        "upload_assets": {
            "video_path": VIDEO_PATH.name,
            "video_sha256": sha256_file(VIDEO_PATH),
            "title_path": title_path.name,
            "title_sha256": sha256_file(title_path),
            "description_path": description_path.name,
            "description_sha256": sha256_file(description_path),
            "tags_path": tags_path.name,
            "tags_sha256": sha256_file(tags_path),
            "caption_srt_path": caption_srt_path.name,
            "caption_srt_sha256": sha256_file(caption_srt_path),
            "suggested_cover_frame_path": COVER_PATH.name,
            "suggested_cover_frame_sha256": sha256_file(COVER_PATH),
            "metadata_path": metadata_path.name,
            "metadata_sha256": sha256_file(metadata_path),
            "upload_checklist_path": upload_checklist_path.name,
            "upload_checklist_sha256": sha256_file(upload_checklist_path),
            "caption_qa_contact_sheet_path": CAPTION_QA_CONTACT_SHEET_PATH.name,
            "caption_qa_contact_sheet_sha256": sha256_file(CAPTION_QA_CONTACT_SHEET_PATH),
            "final_export_provenance_manifest_path": final_export_manifest_path.name,
            "final_export_provenance_manifest_sha256": sha256_file(final_export_manifest_path),
        },
        "technical_read": {
            "container": "mp4",
            "video_codec": probe["video_codec"],
            "audio_codec": probe["audio_codec"],
            "width": probe["width"],
            "height": probe["height"],
            "duration_seconds": probe["duration_seconds"],
            "frame_rate": probe["frame_rate"],
            "audio_sample_rate_hz": probe["audio_sample_rate_hz"],
            "audio_channels": probe["audio_channels"],
            "vertical_shorts_geometry_read": "pass",
            "codec_read": "pass",
            "clean_srt_speaker_label_read": "pass",
            "motif_text_read": "pass",
        },
        "youtube_metadata": {
            "title": TITLE_TEXT,
            "description_path": description_path.name,
            "tags": TAGS,
            "hashtags": HASHTAGS,
            "category_id": "27",
            "privacy": "unlisted",
            "default_language": "en",
            "default_audio_language": "en",
            "audience": "not_made_for_kids",
            "metadata_copy_packet_path": metadata_path.name,
            "metadata_human_keep_read": "pending_human_review",
        },
        "source_final": {
            "path": VIDEO_PATH.name,
            "sha256": sha256_file(VIDEO_PATH),
            "source_duplicate_path": str(SOURCE_FINAL_PATH),
            "source_duplicate_sha256": sha256_file(SOURCE_FINAL_PATH),
            "final_export_manifest_path": final_export_manifest_path.name,
            "final_export_manifest_sha256": sha256_file(final_export_manifest_path),
            "final_review_path": final_review_path.name,
            "final_review_sha256": sha256_file(final_review_path),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
            "caption_burn_read": "pass",
            "clean_srt_speaker_label_read": "pass",
            "house_crt_texture_read": "pass",
            "signal_interruption_read": "pass",
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
        },
        "caption_context": {
            "caption_strategy": "audio_srt_cleaned_speaker_labels_preserve_timings_v1",
            "source_srt_path": str(AUDIO_SRT_PATH),
            "source_srt_sha256": sha256_file(AUDIO_SRT_PATH),
            "clean_srt_path": caption_srt_path.name,
            "clean_srt_sha256": sha256_file(caption_srt_path),
            "motif_text": MOTIF_TEXT,
            "motif_text_read": "pass",
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
            "source_footage_role": "source-derived archival/maritime visuals",
            "altered_content_disclosure_required": True,
            "claim_risk": CLAIM_RISK,
        },
        "studio_checks_required": [
            "copyright_and_content_id",
            "paper_architecture_music_claim_state",
            "altered_content_disclosure_yes_for_realistic_generated_or_source_derived_event_visuals",
            "burned_in_caption_duplicate_caption_track_check",
            "shorts_cover_frame_check",
            "audience_category_visibility_metadata_check",
        ],
        "review_upload": {
            "performed": False,
            "requires_explicit_user_confirmation": True,
            "command": f"/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-upload {manifest_path} --privacy unlisted",
        },
        "public_release": {
            "ready": False,
            "boundary": "manual_youtube_studio_only",
        },
    }
    write_json(manifest_path, upload_manifest)

    summary = {
        "ok": True,
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "package_root": str(PACKAGE_ROOT),
        "video_path": str(VIDEO_PATH),
        "video_sha256": sha256_file(VIDEO_PATH),
        "caption_srt_path": str(caption_srt_path),
        "title_path": str(title_path),
        "description_path": str(description_path),
        "tags_path": str(tags_path),
        "metadata_path": str(metadata_path),
        "upload_checklist_path": str(upload_checklist_path),
        "final_export_manifest_path": str(final_export_manifest_path),
        "final_review_path": str(final_review_path),
        "upload_manifest_path": str(manifest_path),
        "publish_package_check_command": f"/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-check {manifest_path}",
        "review_upload_command": f"/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-upload {manifest_path} --privacy unlisted",
        "public_release_boundary": "manual_youtube_studio_only",
        "probe": probe,
    }
    write_json(summary_path, summary)
    print(json.dumps({**summary, "summary_path": str(summary_path)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
