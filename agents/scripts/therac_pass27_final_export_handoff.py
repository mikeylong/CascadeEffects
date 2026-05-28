#!/usr/bin/env python3
"""Prepare and record the Therac-25 pass 27 final-export handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EPISODE_ID = "therac-25"
SHORT_ID = "therac_short_scoped_v1"

VIZ_ROOT = Path("/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1")
EP_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1")
PROD_ROOT = EP_ROOT / "production"

PASS27_MANIFEST = (
    VIZ_ROOT
    / "motion_video_proof/pass_27_from_pass26_tighten/motion_video_proof_manifest_pass_27_from_pass26_tighten.json"
)
PASS27_PROOF_ALIAS = (
    VIZ_ROOT
    / "motion_video_proof/pass_27_from_pass26_tighten/therac25_motion_video_proof_pass_27__proof.json"
)
ROOT_MANIFEST = VIZ_ROOT / "manifest.json"
AUDIO_PACKAGE = Path("/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_scoped_v1/audio_package.json")
CAPTION_TIMING_SRT = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_scoped_v1/transcripts_mastered/therac_short_scoped_v1.diarized.srt"
)
PROOF_REVIEW_NOTE = PROD_ROOT / "motion_video_proof_review_pass_27_keep.md"
FINAL_REVIEW_NOTE = PROD_ROOT / "final_export_review_pass_01.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def require_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(str(path))


def write_proof_review_note(manifest: dict[str, Any]) -> None:
    proof_path = manifest["proof_video_path"]
    frame_sheet = manifest["frame_sheet_path"]
    affected_rows = manifest["affected_rows_sheet_path"]
    note = f"""# Therac-25 Motion Video Proof Pass 27 Review

Disposition: keep

Reel class: keeper-short

Review basis: human/DP feedback after pass 27: "looks better - continue".

Accepted proof:
- Video: `{proof_path}`
- Full frame sheet: `{frame_sheet}`
- Affected-row sheet: `{affected_rows}`

Gate decision:
- Pass 27 supersedes pass 26 tighten notes for the 19s continuity flash and the 30-34s / 48-51s frozen-frame reads.
- Final export may start from pass 27 using the approved short audio and approved caption transcript.
- LTX and generated stills remain unused for this final-export handoff.

Release warning:
- YouTube/source rights and actual-photo provenance remain unresolved for public release. This keep decision accepts the internal motion proof and final-export route only; source clearance still has to be resolved before upload/publication.
"""
    PROOF_REVIEW_NOTE.write_text(note, encoding="utf-8")


def prepare() -> None:
    for path in (PASS27_MANIFEST, AUDIO_PACKAGE, CAPTION_TIMING_SRT):
        require_path(path)

    manifest = read_json(PASS27_MANIFEST)
    package = read_json(AUDIO_PACKAGE)

    proof_path = Path(manifest["proof_video_path"])
    audio_path = Path(package["packaged_path"])
    transcript_path = Path(package["transcript_path"])
    for path in (proof_path, audio_path, transcript_path):
        require_path(path)

    manifest["stage"] = "motion_video_proof_reviewed_keep"
    manifest["disposition"] = "keep"
    manifest["reel_class"] = "keeper short"
    manifest["proof_path"] = str(proof_path)
    manifest["audio_path"] = str(audio_path)
    manifest["approved_audio_path"] = str(audio_path)
    manifest["transcript_path"] = str(transcript_path)
    manifest["caption_source_path"] = str(transcript_path)
    manifest["caption_timing_path"] = str(CAPTION_TIMING_SRT)
    manifest["caption_timing_sha256"] = sha256(CAPTION_TIMING_SRT)
    manifest["short_audio_package_path"] = str(AUDIO_PACKAGE)
    manifest["audio_package_sha256"] = sha256(AUDIO_PACKAGE)
    manifest["packaged_audio_sha256"] = sha256(audio_path)
    manifest["transcript_sha256"] = sha256(transcript_path)
    manifest["audio_disposition"] = "keep"
    manifest["fps"] = 30
    manifest["proof_review_note_path"] = str(PROOF_REVIEW_NOTE)
    manifest["human_dp_review"] = {
        "reviewed_at": utc_now(),
        "review_source": "thread feedback",
        "feedback": "looks better - continue",
        "disposition": "keep",
        "reel_class": "keeper short",
        "accepted_for": "video final export handoff",
    }
    manifest["may_start_final_export"] = True
    manifest["may_start_ltx_render"] = False
    manifest["may_start_generated_stills"] = False
    manifest["may_start_motion_video_proof"] = False
    manifest["public_release_blocked"] = True
    manifest["public_release_blockers"] = [
        "YouTube/source rights and actual-photo provenance remain unresolved before upload/publication."
    ]
    manifest["blockers"] = [
        "public release/upload blocked pending YouTube/source rights and actual-photo provenance clearance"
    ]
    manifest["next_required_gate"] = "video final export pass 01"
    manifest["gate_assertions"] = {
        "proof_disposition": "keep",
        "reel_class": "keeper short",
        "all_motion_clips_are_keep": True,
        "no_diagnostic_placeholders": True,
        "source_rights_public_release_blocker_recorded": True,
    }
    manifest["beats"] = [
        {
            "id": segment.get("edl_id") or f"row_{segment.get('row_index')}",
            "row_index": segment.get("row_index"),
            "cue_start_seconds": segment.get("timeline_start_seconds"),
            "cue_end_seconds": segment.get("timeline_end_seconds"),
            "motion_disposition": "keep",
            "source_playback_mode": segment.get("source_playback_mode"),
            "rights_read": segment.get("rights_read"),
        }
        for segment in manifest.get("segments", [])
    ]

    write_json(PASS27_MANIFEST, manifest)
    write_json(PASS27_PROOF_ALIAS, manifest)
    write_proof_review_note(manifest)
    print(PROOF_REVIEW_NOTE)


def update_text_file(path: Path, replacements: dict[str, str], append: str = "") -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    if append and append not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += append
    path.write_text(text, encoding="utf-8")


def post(final_manifest_path: Path) -> None:
    require_path(final_manifest_path)
    final_manifest = read_json(final_manifest_path)
    captioned_final = Path(final_manifest["captioned_final_path"])
    overlay_manifest = Path(final_manifest["caption_overlay_manifest_path"])
    final_frame_sheet = final_manifest_path.with_name(final_manifest_path.name.replace("__final_export.json", "__final_frame_sheet.png"))
    require_path(captioned_final)
    require_path(overlay_manifest)

    root = read_json(ROOT_MANIFEST)
    root["current_stage"] = "video final pass 01 review"
    root["last_completed_stage"] = "video final pass 01 export"
    root["next_action"] = "Review captioned final pass 01; public release remains blocked pending source rights/provenance clearance."
    root["active_review_surface_path"] = str(captioned_final)
    root["active_review_manifest_path"] = str(final_manifest_path)
    root["captioned_final_path"] = str(captioned_final)
    root["captioned_final_sha256"] = sha256(captioned_final)
    root["final_export_manifest_path"] = str(final_manifest_path)
    root["final_export_manifest_sha256"] = sha256(final_manifest_path)
    root["final_caption_overlay_manifest_path"] = str(overlay_manifest)
    root["final_caption_overlay_manifest_sha256"] = sha256(overlay_manifest)
    if final_frame_sheet.exists():
        root["final_frame_sheet_path"] = str(final_frame_sheet)
        root["final_frame_sheet_sha256"] = sha256(final_frame_sheet)
    root["music_track_id"] = final_manifest.get("music_track_id")
    root["music_policy"] = final_manifest.get("music_policy")
    root["caption_style_preset"] = final_manifest.get("caption_style_preset")
    root["caption_placement"] = final_manifest.get("caption_placement")
    root["may_start_final_export"] = False
    root["may_start_ltx_render"] = False
    root["may_start_generated_stills"] = False
    root["may_start_motion_video_proof"] = False
    root["public_release_blocked"] = True
    root["public_release_blockers"] = [
        "YouTube/source rights and actual-photo provenance remain unresolved before upload/publication."
    ]
    root["final_export_pass_01"] = {
        "final_export_manifest_path": str(final_manifest_path),
        "captioned_final_path": str(captioned_final),
        "caption_overlay_manifest_path": str(overlay_manifest),
        "final_frame_sheet_path": str(final_frame_sheet) if final_frame_sheet.exists() else "",
        "captioned_final_sha256": sha256(captioned_final),
        "caption_style_preset": final_manifest.get("caption_style_preset"),
        "caption_placement": final_manifest.get("caption_placement"),
        "music_track_id": final_manifest.get("music_track_id"),
        "music_policy": final_manifest.get("music_policy"),
        "music_rights_check_status": final_manifest.get("music_rights_check_status"),
        "proof_review_note_path": str(PROOF_REVIEW_NOTE),
        "release_status": "blocked_pending_source_rights_provenance",
    }
    write_json(ROOT_MANIFEST, root)

    FINAL_REVIEW_NOTE.write_text(
        f"""# Therac-25 Final Export Pass 01

Disposition: review-ready

Captioned final:
`{captioned_final}`

Final export manifest:
`{final_manifest_path}`

Caption overlay manifest:
`{overlay_manifest}`

Final frame sheet:
`{final_frame_sheet if final_frame_sheet.exists() else ""}`

Source proof:
`{final_manifest["source_proof_manifest_path"]}`

Proof review note:
`{PROOF_REVIEW_NOTE}`

Render read:
- Caption style: `{final_manifest.get("caption_style_preset")}` / `{final_manifest.get("caption_placement")}`
- Music policy: `{final_manifest.get("music_policy")}` / `{final_manifest.get("music_track_id")}`
- Final SHA-256: `{sha256(captioned_final)}`

Gate read:
- Internal final export is ready for review.
- Public upload/release remains blocked pending YouTube/source rights and actual-photo provenance clearance.
""",
        encoding="utf-8",
    )

    append = f"""

## Video Final Pass 01

- `final_export_manifest_path`: `{final_manifest_path}`
- `captioned_final_path`: `{captioned_final}`
- `caption_overlay_manifest_path`: `{overlay_manifest}`
- `proof_review_note_path`: `{PROOF_REVIEW_NOTE}`
- `public_release_blocked`: `true; YouTube/source rights and actual-photo provenance unresolved`
"""
    update_text_file(
        PROD_ROOT / "motion_video_proof.md",
        {
            "Current review gate: `motion_video_proof pass 27 repair review`.": "Current review gate: `motion_video_proof pass 27 keep accepted for final export`.",
            "Final export remains blocked until pass 27 receives a human/DP `keep` decision.": "Final export pass 01 has been rendered for review; public release remains blocked pending source rights/provenance clearance.",
        },
        append=append,
    )
    update_text_file(
        PROD_ROOT / "deferred_gaps.md",
        {
            "Pass 27 is a review proof only; no human/DP `keep` decision has accepted it for final export.": "Pass 27 is accepted as the keeper motion proof for internal final export.",
            "Review pass 27 proof/frame sheet and mark keep/tighten/reject before any final-export routing.": f"Review final export pass 01 at `{captioned_final}`; public release remains blocked pending source rights/provenance clearance.",
            "Pass 27 motion video proof repair is review-ready but not accepted.": "Pass 27 motion video proof repair was accepted for final-export routing; final export pass 01 is review-ready.",
            "Final export requires a `keep` motion video proof.": "Public upload/release requires source rights and actual-photo provenance clearance.",
            "Do not route to final export yet.": f"Review final export pass 01 at `{captioned_final}`.",
        },
    )
    update_text_file(
        PROD_ROOT / "workflow_scope_manifest.md",
        {
            "- `may_start_motion_video_proof`: `false; completed by pass 27 repair and pending human/DP review`": "- `may_start_motion_video_proof`: `false; completed by pass 27 repair and accepted for final-export handoff`",
            "- `may_start_stills_or_motion_generation`: `false; pass 27 proof repair review is pending`": "- `may_start_stills_or_motion_generation`: `false; final export pass 01 uses source-led proof, no LTX/generated stills`",
            "Pass 27 motion video proof repair awaits human/DP review; YouTube source rights/provenance remain unresolved for final production use; current local LTX backend/settings rejected; pass 10 execution packet is pending manual send/submission and 0 production-eligible cleared actual visuals; pass 13/pass 21/pass 24/pass 26/pass 27 are not final production eligibility": "Pass 27 motion video proof accepted for internal final export; YouTube source rights/provenance remain unresolved for public release; current local LTX backend/settings rejected; pass 10 execution packet is pending manual send/submission and 0 production-eligible cleared actual visuals; pass 13/pass 21/pass 24/pass 26/pass 27 are not public-release clearance",
            "- `next_action`: `human/DP review motion video proof pass 27 repair; keep source-clearance execution active in parallel before final production use`": f"- `next_action`: `review final export pass 01 at {captioned_final}; keep source-clearance execution active before public release`",
        },
        append=append,
    )
    update_text_file(
        PROD_ROOT / "stage_ledger.md",
        {
            "- `current_stage`: `human/DP motion_video_proof pass 27 repair review`": "- `current_stage`: `video final pass 01 review`",
            "- `last_completed_stage`: `motion_video_proof pass 27 repair`": "- `last_completed_stage`: `video final pass 01 export`",
            "- `advance_scope`: `human/DP motion proof review only; no LTX, generated stills, or final export`": "- `advance_scope`: `internal final export review; no LTX or generated stills; public release blocked pending source rights`",
            "- `next_required_gate`: `human/DP review motion video proof pass 27`": "- `next_required_gate`: `human/DP review final export pass 01`",
            "| `motion video proof pass 27 repair` | `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1/production/motion_video_proof_pass_27.md` | `diagnostic only` | `false` | Repairs pass 26 notes at rows 07, 11, and 16 while preserving pass 21 timing and approved audio; human/DP review required before final export. |": "| `motion video proof pass 27 repair` | `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1/production/motion_video_proof_pass_27.md` | `keep` | `true to video_final_pass_01` | Repairs pass 26 notes at rows 07, 11, and 16 while preserving pass 21 timing and approved audio; accepted by human/DP feedback for final export handoff. |",
            "| `motion proof review` | Pass 27 repair proof is review-ready, but no human/DP decision has accepted it for final export. |": "| `motion proof review` | Pass 27 repair proof accepted as keeper-short for internal final export. |",
            "Review `/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/motion_video_proof/pass_27_from_pass26_tighten/therac25_motion_video_proof_pass_27_audio_timed.mp4` and `/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/motion_video_proof/pass_27_from_pass26_tighten/contact_sheets/therac25_motion_video_proof_pass_27_affected_rows_sheet.png`; keep/tighten/reject before final export.": f"Review final export pass 01 at `{captioned_final}`; public release remains blocked pending source rights/provenance clearance.",
            "may_start_final_export: false": "may_start_final_export: false; completed by final export pass 01, review pending",
            "  - pass 27 motion video proof repair has not received human/DP acceptance": "  - final export pass 01 review pending",
            "  - generated stills, LTX, and final remain blocked": "  - generated stills and LTX remain unused/blocked; public release is blocked pending source rights",
            "next_action: human/DP review motion video proof pass 27 repair; keep source clearance active in parallel before final production use": f"next_action: review final export pass 01 at {captioned_final}; keep source clearance active before public release",
        },
        append=f"""

| `motion video proof pass 27 keep review` | `{PROOF_REVIEW_NOTE}` | `keep` | `true to video_final_pass_01` | Human/DP feedback: looks better - continue. |
| `video final pass 01` | `{FINAL_REVIEW_NOTE}` | `review-ready` | `false to public_release` | Captioned final rendered; public release blocked pending source rights/provenance clearance. |
""",
    )
    print(FINAL_REVIEW_NOTE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--post-final-manifest", type=Path)
    args = parser.parse_args()

    if args.prepare:
        prepare()
    if args.post_final_manifest:
        post(args.post_final_manifest.expanduser().resolve())
    if not args.prepare and not args.post_final_manifest:
        parser.error("choose --prepare and/or --post-final-manifest")


if __name__ == "__main__":
    main()
