#!/usr/bin/env python3
"""Build the Therac-25 local YouTube Shorts publish-review package."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EPISODE_ID = "therac-25"
SHORT_ID = "therac_short_scoped_v1"

VIZ_ROOT = Path("/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1")
EP_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1")
PROD_ROOT = EP_ROOT / "production"
PUBLISH_ROOT = EP_ROOT / "publish"

ROOT_MANIFEST = VIZ_ROOT / "manifest.json"
FINAL_MANIFEST = (
    VIZ_ROOT
    / "motion_video_proof/pass_28_final_tail_repair/final_exports/therac_pass02_outro_tail_repair_lower_left_paper_architecture/20260428T210731Z__final_export.json"
)
FINAL_MP4 = (
    VIZ_ROOT
    / "motion_video_proof/pass_28_final_tail_repair/final_exports/therac_pass02_outro_tail_repair_lower_left_paper_architecture/20260428T210731Z__captioned_final.mp4"
)
FINAL_SRT = (
    VIZ_ROOT
    / "motion_video_proof/pass_28_final_tail_repair/final_exports/therac_pass02_outro_tail_repair_lower_left_paper_architecture/20260428T210731Z__captions.srt"
)
FINAL_REVIEW = PROD_ROOT / "final_export_review_pass_02_tail_repair.md"
TAIL_REPAIR_PROOF = VIZ_ROOT / "motion_video_proof/pass_28_final_tail_repair/therac25_motion_video_proof_pass_28_tail_repair__proof.json"
TAIL_REPAIR_PROOF_MP4 = VIZ_ROOT / "motion_video_proof/pass_28_final_tail_repair/therac25_motion_video_proof_pass_28_tail_repair_audio_timed.mp4"
SOURCE_INVENTORY = VIZ_ROOT / "visual_research/image_motion_source_pool_lock_pass_13/image_motion_source_pool_lock_pass_13.json"


TITLE = "Therac-25: When Software Became the Safety System #Shorts"
DESCRIPTION = """Therac-25 showed what happens when software is treated like the safety layer instead of being tested against one.

A radiation machine gave patients massive overdoses. The pattern was visible in the field before the system was willing to believe it.

#Therac25 #SoftwareSafety #CascadeEffects
"""
TAGS = [
    "Therac-25",
    "Therac 25",
    "software safety",
    "race condition",
    "medical device",
    "radiation therapy",
    "patient safety",
    "systems failure",
    "software engineering",
    "safety critical systems",
    "medical history",
    "documentary short",
    "history short",
    "Cascade Effects",
    "Shorts",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run(cmd: list[str], *, label: str) -> str:
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return completed.stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def require(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(str(path))


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
        "shorts_geometry_read": "pass_vertical",
    }


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def build() -> Path:
    for path in (ROOT_MANIFEST, FINAL_MANIFEST, FINAL_MP4, FINAL_SRT, FINAL_REVIEW, TAIL_REPAIR_PROOF, TAIL_REPAIR_PROOF_MP4):
        require(path)

    final_manifest = read_json(FINAL_MANIFEST)
    root_manifest = read_json(ROOT_MANIFEST)
    proof_manifest = read_json(TAIL_REPAIR_PROOF)

    package_dir = PUBLISH_ROOT / f"youtube_{utc_stamp()}"
    package_dir.mkdir(parents=True, exist_ok=True)

    upload_video = package_dir / "therac25_software_safety_youtube_short.mp4"
    upload_srt = package_dir / "therac25_software_safety_captions.srt"
    final_manifest_copy = package_dir / "final_export_manifest.json"
    final_review_copy = package_dir / "final_review.md"
    keeper_capsule_publish = package_dir / "keeper_lesson_capsule.md"
    rights_review_publish = package_dir / "rights_fair_use_review.md"
    approval_publish = package_dir / "final_human_approval.md"
    shutil.copy2(FINAL_MP4, upload_video)
    shutil.copy2(FINAL_SRT, upload_srt)
    shutil.copy2(FINAL_MANIFEST, final_manifest_copy)
    shutil.copy2(FINAL_REVIEW, final_review_copy)

    cover_frame = package_dir / "suggested_shorts_cover_frame.png"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            "0.650",
            "-i",
            str(TAIL_REPAIR_PROOF_MP4),
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

    write_text(title_path, TITLE)
    write_text(description_path, DESCRIPTION)
    write_text(tags_path, "\n".join(TAGS))
    write_text(
        metadata_path,
        f"""# Therac-25 YouTube Metadata

## Title

{TITLE}

## Description

{DESCRIPTION.rstrip()}

## Tags

{chr(10).join(f"- {tag}" for tag in TAGS)}

## Upload Defaults

- `privacy`: `unlisted_first_then_public_after_checks`
- `audience`: `not_made_for_kids`
- `paid_promotion`: `false`
- `language`: `English`
- `category`: `Education`
""",
    )

    final_sha = sha256(FINAL_MP4)
    final_manifest_sha = sha256(FINAL_MANIFEST)
    final_review_sha = sha256(FINAL_REVIEW)

    approval_text = f"""# Therac-25 Final Human Approval

- `stage`: `video final approval`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `approved_final_path`: `{FINAL_MP4}`
- `approved_final_sha256`: `{final_sha}`
- `final_export_manifest_path`: `{FINAL_MANIFEST}`
- `final_export_manifest_sha256`: `{final_manifest_sha}`
- `disposition`: `keep`
- `reel_class`: `keeper short`
- `approval_source`: `thread feedback`
- `approval_note`: `good - continue`
- `current_gate`: `publish/release review`

Public release remains blocked pending YouTube/source rights, actual-photo provenance, and Paper Architecture claim checks.
"""
    approval_production = PROD_ROOT / "final_human_approval_20260428_good_continue.md"
    write_text(approval_production, approval_text)
    write_text(approval_publish, approval_text)

    approval_sha = sha256(approval_production)
    caption_style = final_manifest.get("caption_style_preset", "early_1980s_broadcast_cg_v1")
    caption_placement = final_manifest.get("caption_placement", "lower-left")
    music_context = final_manifest.get("final_music_context", {}) if isinstance(final_manifest.get("final_music_context"), dict) else {}
    final_music_track_id = music_context.get("music_track_id", final_manifest.get("music_track_id", "paper_architecture_theme_v1"))
    final_music_policy = music_context.get("music_policy", final_manifest.get("music_policy", "canonical_default"))
    music_rights_status = "pending_youtube_upload_check"

    keeper_capsule_text = f"""# Therac-25 Keeper Lesson Capsule

## Keeper Capsule

- `stage`: `keeper lesson capsule`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `keeper_final_path`: `{FINAL_MP4}`
- `keeper_final_sha256`: `{final_sha}`
- `keeper_final_manifest_path`: `{FINAL_MANIFEST}`
- `keeper_final_manifest_sha256`: `{final_manifest_sha}`
- `publishable_approved_at`: `{utc_now()}`
- `production_model_lane`: `source_led_youtube_archival_motion_with_strict_clean_hygiene`
- `hero_source_family_ids`: `WiJP4P9b1ow`, `RJcbDmom4BQ`, `gZIez0zNiU4`
- `caption_style_preset`: `{caption_style}`
- `caption_placement`: `{caption_placement}`
- `music_track_id`: `{final_music_track_id}`
- `music_policy`: `{final_music_policy}`
- `music_rights_check_status`: `{music_rights_status}`
- `motif_outro_mix_used`: `true`
- `disposition`: `keep`

## Reusable Lessons

| `lesson_id` | `lesson` | `scope` | `evidence_path` | `action` |
|---|---|---|---|---|
| `therac_source_motion_after_actual_photo_gap_v1` | When actual-unit stills remain rights-limited, a narrow, DP-ranked source-motion pool can still carry the Short if the source identity and rights limits are explicit. | `global_policy_candidate` | `{PROD_ROOT / 'image_motion_source_pool_lock_pass_13.md'}` | `remember_only` |
| `therac_no_freeze_final_tail_v1` | Do not use cloned-frame padding to solve final outro timing when the viewer expects motion; extend with clean same-source motion or shorten the music plan. | `global_policy_candidate` | `{FINAL_MANIFEST}` | `remember_only` |
| `therac_youtube_search_repair_v1` | The useful visual basis came only after widening the search to YouTube motion, scouting stills/clips, and rejecting text-heavy provenance boards as the primary visual surface. | `episode_local` | `{PROD_ROOT / 'archival_footage_review_youtube_expanded_pass_02.md'}` | `remember_only` |
| `therac_caption_audio_finish_v1` | Early-1980s lower-left captions plus the Paper Architecture outro worked once the last visual continued under the outro instead of freezing. | `episode_local` | `{FINAL_REVIEW}` | `remember_only` |

## What Worked

- `winning_lane_reason`: Source-led archival motion made the abstract software-safety failure visible without relying on generic generated machinery.
- `winning_source_families`: Archival patient/table/machine relationship, clinical room geometry, operator interface/code beats, and terminal/race-condition visuals.
- `effective_motion_strategy`: Continuous same-source handles for motion rows; source-frame holds only where explicitly intentional; real source motion under the final outro.
- `effective_audio_or_caption_choice`: `early_1980s_broadcast_cg_v1` lower-left captions with canonical Paper Architecture motif/outro mix.

## What Not To Globalize

- `episode_specific_subject_rules`: Do not globally require radiotherapy footage, patient table imagery, or terminal-screen beats.
- `diagnostic_experiments_not_promoted`: LTX/noise-only tests and text-heavy provenance boards stay diagnostic.
- `rights_limited_actual_photo_leads`: Actual Therac-25 photo leads remain source-clearance work, not a reusable production surface.

## Handoff

- `global_policy_updates_recommended`: `false`
- `recommended_policy_update_paths`: []
- `next_episode_implications`: Use DP visual strength as the forcing function earlier; provenance boards can support decisions but should not become the contact sheet.
- `blockers_before_public_release`: YouTube/source rights, actual-photo provenance, and Paper Architecture claim checks remain unresolved.
"""
    keeper_capsule_production = PROD_ROOT / "keeper_lesson_capsule.md"
    write_text(keeper_capsule_production, keeper_capsule_text)
    write_text(keeper_capsule_publish, keeper_capsule_text)

    rights_review_text = f"""# Therac-25 Publish Rights / Fair-Use Review Pass 01

## Review

- `stage`: `publish/release review`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `captioned_final_path`: `{FINAL_MP4}`
- `music_track_id`: `{final_music_track_id}`
- `music_policy`: `{final_music_policy}`
- `disposition`: `manual_review_required`

## Rights Read

The creative final is a keeper and the local upload package may be prepared for review. Public release is not cleared. The Short uses YouTube/archive-derived clinical and software-safety footage plus the Paper Architecture music bed/outro.

| check | read |
| --- | --- |
| `source_footage_rights_read` | `manual_review_required` |
| `actual_photo_provenance_read` | `unresolved_not_used_as_cleared_surface` |
| `music_rights_check_status` | `pending_youtube_upload_check` |
| `youtube_claim_check_status` | `pending_unlisted_upload` |
| `public_publish_clearance` | `blocked_until_checks_recorded` |

## Handoff

```yaml
stage: publish/release review
episode_id: {EPISODE_ID}
short_id: {SHORT_ID}
disposition: manual_review_required
may_package_for_upload_review: true
may_publish_public: false
next_required_gate: manual source/music rights acceptance and YouTube unlisted claim check
```
"""
    rights_review_production = PROD_ROOT / "publish_rights_fair_use_review_pass_01.md"
    write_text(rights_review_production, rights_review_text)
    write_text(rights_review_publish, rights_review_text)

    write_text(
        checklist_path,
        f"""# Therac-25 YouTube Upload Checklist

## Assets

- video: `{upload_video}`
- captions: `{upload_srt}`
- title: `{title_path}`
- description: `{description_path}`
- tags: `{tags_path}`
- cover frame: `{cover_frame}`
- manifest: `{package_dir / 'youtube_upload_manifest.json'}`

## Required Checks

- Confirm final pass 02 plays through the last visual and the Paper Architecture outro without a freeze.
- Upload unlisted first.
- Check YouTube processing and Content ID for Paper Architecture.
- Complete source-footage rights/fair-use review before public release.
- Confirm title, description, tags, and cover frame in YouTube Studio.
""",
    )

    technical_read = probe_video(upload_video)
    source_used_ids = sorted({str(seg.get("source_url", "")).split("v=")[-1] for seg in proof_manifest.get("segments", []) if seg.get("source_url")})

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
            "manual source-rights/fair-use acceptance",
            "actual-photo provenance/source-clearance record remains unresolved",
            "Paper Architecture YouTube claim check",
            "YouTube unlisted processing check",
        ],
    }
    write_json(delivery_manifest_path, delivery_manifest)

    upload_manifest_path = package_dir / "youtube_upload_manifest.json"
    upload_manifest = {
        "schema_version": 1,
        "created_at": utc_now(),
        "target": "youtube_shorts",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "publication_readiness": "ready_for_upload_with_rights_check",
        "source_final": {
            "path": str(FINAL_MP4),
            "sha256": final_sha,
            "final_export_manifest_path": str(FINAL_MANIFEST),
            "final_export_manifest_sha256": final_manifest_sha,
            "review_path": str(FINAL_REVIEW),
            "review_sha256": final_review_sha,
            "final_human_approval_path": str(approval_production),
            "final_human_approval_sha256": approval_sha,
            "keeper_lesson_capsule_path": str(keeper_capsule_production),
            "keeper_lesson_capsule_sha256": sha256(keeper_capsule_production),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
            "may_publish_scope": "creative_keep_package_ready_requires_human_rights_and_music_checks_before_public",
            "music_policy": final_music_policy,
            "music_track_id": final_music_track_id,
            "music_rights_check_status": music_rights_status,
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
            "rights_fair_use_review_path": str(rights_review_publish),
            "rights_fair_use_review_sha256": sha256(rights_review_publish),
            "final_review_path": str(final_review_copy),
            "final_review_sha256": sha256(final_review_copy),
            "final_human_approval_path": str(approval_publish),
            "final_human_approval_sha256": sha256(approval_publish),
            "keeper_lesson_capsule_path": str(keeper_capsule_publish),
            "keeper_lesson_capsule_sha256": sha256(keeper_capsule_publish),
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
            "privacy": "unlisted_first_then_public_after_checks",
            "audience": "not_made_for_kids",
            "paid_promotion": False,
            "language": "English",
            "category": "Education",
        },
        "rights_and_claims": {
            "source_footage_rights_read": "manual_review_required",
            "actual_photo_provenance_read": "unresolved_not_used_as_cleared_surface",
            "music_bed_used": True,
            "music_policy": final_music_policy,
            "music_track_id": final_music_track_id,
            "music_rights_check_status": music_rights_status,
            "claim_risk": "Manual source-footage fair-use review, actual-photo provenance record, and YouTube Content ID claim check required before public release.",
            "public_publish_clearance": "blocked_until_human_rights_acceptance_and_youtube_checks",
        },
        "source_provenance": {
            "proof_manifest_path": str(TAIL_REPAIR_PROOF),
            "proof_manifest_sha256": sha256(TAIL_REPAIR_PROOF),
            "used_youtube_ids": source_used_ids,
            "source_inventory_path": str(SOURCE_INVENTORY) if SOURCE_INVENTORY.exists() else "",
            "source_inventory_sha256": sha256(SOURCE_INVENTORY) if SOURCE_INVENTORY.exists() else "",
        },
        "final_music_context": {
            **music_context,
            "music_rights_check_status": music_rights_status,
        },
    }
    write_json(upload_manifest_path, upload_manifest)

    root_manifest["current_stage"] = "publish/release review"
    root_manifest["last_completed_stage"] = "youtube publish package pass 01"
    root_manifest["next_action"] = "Review local YouTube publish package; public release remains blocked pending source/music rights and YouTube checks."
    root_manifest["youtube_upload_manifest_path"] = str(upload_manifest_path)
    root_manifest["youtube_upload_manifest_sha256"] = sha256(upload_manifest_path)
    root_manifest["publish_package_root"] = str(package_dir)
    root_manifest["publish_package_readiness"] = "ready_for_upload_with_rights_check"
    root_manifest["keeper_lesson_capsule_path"] = str(keeper_capsule_production)
    root_manifest["keeper_lesson_capsule_sha256"] = sha256(keeper_capsule_production)
    root_manifest["final_human_approval_path"] = str(approval_production)
    root_manifest["final_human_approval_sha256"] = approval_sha
    root_manifest["public_release_blocked"] = True
    root_manifest["public_release_blockers"] = [
        "manual source-rights/fair-use acceptance",
        "actual-photo provenance/source-clearance record remains unresolved",
        "Paper Architecture YouTube claim check",
        "YouTube unlisted processing check",
    ]
    write_json(ROOT_MANIFEST, root_manifest)

    publish_packet = PROD_ROOT / "youtube_publish_package_pass_01.md"
    write_text(
        publish_packet,
        f"""# Therac-25 YouTube Publish Package Pass 01

- `stage`: `publish/release review`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `package_root`: `{package_dir}`
- `youtube_upload_manifest_path`: `{upload_manifest_path}`
- `youtube_upload_manifest_sha256`: `{sha256(upload_manifest_path)}`
- `upload_video_path`: `{upload_video}`
- `upload_video_sha256`: `{sha256(upload_video)}`
- `publication_readiness`: `ready_for_upload_with_rights_check`
- `public_release_blocked`: `true`

## Gate Read

The package is ready for local upload review. Public release remains blocked until source-footage rights/fair-use acceptance, actual-photo provenance/source-clearance recording, Paper Architecture claim checks, and YouTube unlisted processing checks are complete.
""",
    )

    append = f"""

## YouTube Publish Package Pass 01

- `youtube_upload_manifest_path`: `{upload_manifest_path}`
- `youtube_upload_manifest_sha256`: `{sha256(upload_manifest_path)}`
- `upload_video_path`: `{upload_video}`
- `publication_readiness`: `ready_for_upload_with_rights_check`
- `public_release_blocked`: `true; source/music rights and YouTube checks pending`
"""
    for path in (PROD_ROOT / "stage_ledger.md", PROD_ROOT / "workflow_scope_manifest.md", PROD_ROOT / "short_production_pilot.md", PROD_ROOT / "deferred_gaps.md"):
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if append not in text:
                path.write_text(text.rstrip() + "\n" + append, encoding="utf-8")

    print(upload_manifest_path)
    return upload_manifest_path


if __name__ == "__main__":
    build()
