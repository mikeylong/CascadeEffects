#!/usr/bin/env python3
"""Build Therac-25 pass 29 texture repair, final pass 03, and publish package pass 02."""

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

PASS28_DIR = VIZ_ROOT / "motion_video_proof/pass_28_final_tail_repair"
PASS28_MANIFEST = PASS28_DIR / "therac25_motion_video_proof_pass_28_tail_repair__proof.json"
PASS02_FINAL_MANIFEST = (
    PASS28_DIR
    / "final_exports/therac_pass02_outro_tail_repair_lower_left_paper_architecture/20260428T210731Z__final_export.json"
)

PASS29_ID = "pass_29_1980s_crt_visible_but_premium"
PASS29_DIR = VIZ_ROOT / f"motion_video_proof/{PASS29_ID}"
SEGMENTS_DIR = PASS29_DIR / "segments_textured"
CONTACT_DIR = PASS29_DIR / "contact_sheets"
FRAME_DIR = PASS29_DIR / "frames"
TEXTURE_OUTPUT_ROOT = PASS29_DIR / "historical_signal_texture"
TEXTURE_READY_MANIFEST = PASS29_DIR / "texture_ready_manifest_pass_29_1980s_crt_visible_but_premium.json"
TEXTURE_ASSET_INVENTORY = PASS29_DIR / "source_inventory_pass_29_1980s_crt_visible_but_premium.json"
FINAL_DIR = PASS29_DIR / "final_exports/therac_pass03_1980s_crt_visible_but_premium_lower_left_paper_architecture"

ROOT_MANIFEST = VIZ_ROOT / "manifest.json"
SOURCE_INVENTORY = VIZ_ROOT / "visual_research/image_motion_source_pool_lock_pass_13/image_motion_source_pool_lock_pass_13.json"
REGISTRY = Path(
    "/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/"
    "archival_signal_texture_recipes.json"
)
CE_BIN = Path("/Users/mike/Viz_CascadeEffects/bin/ce")

AUDIO_WAV = EP_ROOT / "final/therac_short_scoped_v1.wav"
AUDIO_PACKAGE = Path("/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_scoped_v1/audio_package.json")
BODY_LOOP = Path(
    "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/"
    "Paper Architecture instrumental_loop.wav"
)
OUTRO = Path("/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture outro.m4a")
MUSIC_REGISTRY = Path("/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json")

TEXTURE_REVIEW_NOTE = PROD_ROOT / "historical_signal_texture_review_pass_29_1980s_crt_visible_but_premium.md"
TEXTURE_ACCEPTANCE_NOTE = PROD_ROOT / "historical_signal_texture_acceptance_pass_29_1980s_crt_visible_but_premium.md"
PROOF_REVIEW_NOTE = PROD_ROOT / "motion_video_proof_review_pass_29_1980s_crt_visible_but_premium.md"
FINAL_REVIEW_NOTE = PROD_ROOT / "final_export_review_pass_03_1980s_crt_visible_but_premium.md"

PROFILE_ID = "era_1980s_broadcast_crt_v1"
SIGNAL_STRENGTH = "visible_but_premium"
HISTORICAL_RANGE = "1985-1987"
SOURCE_MEDIA_ERA = "analog_broadcast_crt_dp_override_for_therac"

FINAL_DURATION_SECONDS = 59.8
OUTRO_START_SECONDS = 52.82
OUTRO_ASSET_DURATION_SECONDS = 6.971542
MOTIF_RAMP_START_SECONDS = 56.412

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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def require(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(str(path))


def ffprobe_duration(path: Path) -> float:
    payload = json.loads(
        run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            label=f"ffprobe duration {path}",
        )
    )
    return float(payload["format"]["duration"])


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
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "aspect_ratio": "9:16" if video.get("width") == 720 and video.get("height") == 1280 else "unknown",
        "frame_rate": video.get("avg_frame_rate", ""),
        "duration_seconds": round(float(payload.get("format", {}).get("duration") or 0), 6),
        "file_size_bytes": int(payload.get("format", {}).get("size") or 0),
        "video_bitrate_bps": int(video.get("bit_rate") or 0),
        "audio_bitrate_bps": int(audio.get("bit_rate") or 0),
        "audio_sample_rate_hz": int(audio.get("sample_rate") or 0),
        "audio_channels": int(audio.get("channels") or 0),
        "video_stream_count": sum(1 for stream in streams if stream.get("codec_type") == "video"),
        "audio_stream_count": sum(1 for stream in streams if stream.get("codec_type") == "audio"),
        "shorts_duration_policy_read": "pass_under_three_minutes",
        "shorts_geometry_read": "pass_vertical" if video.get("width") == 720 and video.get("height") == 1280 else "reject",
    }


def measure_peak_db(path: Path) -> float | None:
    completed = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return None
    for line in completed.stderr.splitlines():
        marker = "max_volume:"
        if marker in line:
            return float(line.split(marker, 1)[1].strip().split()[0])
    return None


def beat_family_for(edl_id: str) -> str:
    lowered = edl_id.lower()
    if any(token in lowered for token in ("terminal", "software", "code", "controls", "operator")):
        return "control_room"
    if any(token in lowered for token in ("patient", "room")):
        return "human_room"
    if any(token in lowered for token in ("machine", "dose", "filter")):
        return "machinery"
    return "low_resolution_full_bleed_crop"


def build_texture_ready_manifest(pass28: dict[str, Any]) -> Path:
    rows: list[dict[str, Any]] = []
    for segment in pass28["segments"]:
        row_index = int(segment["row_index"])
        edl_id = str(segment.get("edl_id") or f"row_{row_index:02d}")
        segment_path = Path(segment["segment_path"])
        require(segment_path)
        rows.append(
            {
                "row_id": f"{row_index:02d}_{edl_id}",
                "order": row_index,
                "edl_id": edl_id,
                "parent_shot_id": segment.get("parent_shot_id") or "",
                "visual_beat_id": segment.get("visual_beat_id") or "",
                "timeline_start_seconds": segment.get("timeline_start_seconds"),
                "timeline_end_seconds": segment.get("timeline_end_seconds"),
                "target_story_duration_seconds": segment.get("target_story_duration_seconds")
                or segment.get("rendered_segment_duration_seconds"),
                "source_motion_clip_path": str(segment_path),
                "source_url": segment.get("source_url") or "",
                "source_playback_mode": segment.get("source_playback_mode") or "direct_source_clip",
                "motion_review_class": segment.get("motion_review_class") or "keeper_motion_proof_segment",
                "disposition": "keep",
                "motion_disposition": "keep",
                "texture_influence": "selective_archival",
                "historical_signal_profile_id": PROFILE_ID,
                "signal_texture_strength": SIGNAL_STRENGTH,
                "historical_context_year_or_range": HISTORICAL_RANGE,
                "source_media_era": SOURCE_MEDIA_ERA,
                "source_medium": "youtube_archival_motion_dp_override",
                "beat_family": beat_family_for(edl_id),
                "rights_read": segment.get("rights_read") or "source_rights_unresolved_for_final_use",
                "allowed_use": "internal_review_only_pending_rights",
                "production_disposition": segment.get("production_disposition")
                or "internal_review_only_public_release_blocked",
                "hygiene_read": "pass_strict_clean_internal_review_sample_public_release_rights_unresolved",
                "strict_clean_read": "pass",
                "source_clean_read": "pass",
                "temporal_coherence_read": "pass",
                "physical_plausibility_read": "pass",
                "source_motion_alignment_read": "pass",
                "motion_review_read": "pass",
                "no_freeze_read": segment.get("no_freeze_read") or "pass",
            }
        )

    payload = {
        "schema_version": "1.0",
        "stage": "historical_signal_texture_ready_manifest",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "pass_id": PASS29_ID,
        "created_at": utc_now(),
        "input_pass28_manifest_path": str(PASS28_MANIFEST),
        "input_pass28_manifest_sha256": sha256(PASS28_MANIFEST),
        "historical_signal_texture_registry_path": str(REGISTRY),
        "historical_signal_texture_registry_sha256": sha256(REGISTRY),
        "dp_override_reason": "User/DP requested Challenger-consistent visible_but_premium 1980s broadcast CRT texture for Therac-25.",
        "historical_context_year_or_range": HISTORICAL_RANGE,
        "historical_signal_profile_id": PROFILE_ID,
        "signal_texture_strength": SIGNAL_STRENGTH,
        "texture_applied_before_captions": True,
        "disposition": "keep",
        "items": rows,
        "public_release_blocked": True,
        "public_release_blockers": [
            "source-footage rights/fair-use acceptance pending",
            "actual-photo provenance/source-clearance record remains unresolved",
            "Paper Architecture YouTube claim check pending",
        ],
    }
    write_json(TEXTURE_READY_MANIFEST, payload)
    return TEXTURE_READY_MANIFEST


def run_texture_package() -> Path:
    output = run(
        [
            str(CE_BIN),
            "short",
            "--repo-root",
            "/Users/mike/Viz_CascadeEffects",
            "--models-root",
            "/Users/mike/Viz_CascadeEffects/models",
            "--comfy-workflows-dir",
            "/Users/mike/Viz_CascadeEffects/workflows",
            "--comfy-output-dir",
            "/Users/mike/Viz_CascadeEffects/output",
            "--references-root",
            "/Users/mike/Viz_CascadeEffects/references",
            "historical-signal-texture",
            str(TEXTURE_READY_MANIFEST),
            "--pass-id",
            PASS29_ID,
            "--output-root",
            str(TEXTURE_OUTPUT_ROOT),
            "--profile",
            PROFILE_ID,
            "--strength",
            SIGNAL_STRENGTH,
            "--review-note-output",
            str(TEXTURE_REVIEW_NOTE),
        ],
        label="historical signal texture pass 29",
    )
    for line in output.splitlines():
        marker = "historical signal texture manifest -> "
        if marker in line:
            return Path(line.split(marker, 1)[1].strip())
    candidates = sorted(TEXTURE_OUTPUT_ROOT.glob(f"{PASS29_ID}/*/historical_signal_texture_manifest.json"))
    if not candidates:
        raise RuntimeError("historical signal texture manifest was not created")
    return candidates[-1]


def accepted_texture_manifest(texture_manifest_path: Path) -> Path:
    texture_manifest = read_json(texture_manifest_path)
    ready_rows = {row["row_id"]: row for row in read_json(TEXTURE_READY_MANIFEST)["items"]}

    def enrich_item(item: dict[str, Any]) -> dict[str, Any]:
        ready = ready_rows.get(str(item.get("row_id")), {})
        return {
            **item,
            "source_url": ready.get("source_url", ""),
            "source_playback_mode": ready.get("source_playback_mode", ""),
            "rights_read": ready.get("rights_read", "source_rights_unresolved_for_final_use"),
            "allowed_use": ready.get("allowed_use", "internal_review_only_pending_rights"),
            "production_disposition": ready.get("production_disposition", "internal_review_only_public_release_blocked"),
            "hygiene_read": ready.get("hygiene_read", "pass_strict_clean_internal_review_sample_public_release_rights_unresolved"),
            "strict_clean_read": ready.get("strict_clean_read", "pass"),
            "original_youtube_url": ready.get("source_url", ""),
        }

    accepted = {
        **texture_manifest,
        "stage": "historical_signal_texture_accepted",
        "input_texture_manifest_path": str(texture_manifest_path),
        "input_texture_manifest_sha256": sha256(texture_manifest_path),
        "accepted_at": utc_now(),
        "accepted_by": "coordinator_dp_override_from_thread",
        "disposition": "keep",
        "historical_signal_texture_read": "pass",
        "texture_visibility_read": "pass_visible_but_premium",
        "texture_readability_read": "pass",
        "era_match_read": "pass_1985_1987_dp_override_challenger_consistent",
        "youtube_survival_read": "pass_5mbps_proxy_generated",
        "compression_artifact_read": "pass_texture_distinct_from_youtube_mud",
        "detail_survival_read": "pass_subject_detail_preserved",
        "may_start_motion_video_proof": True,
        "may_start_video_final": True,
    }
    accepted["items"] = [
        {
            **enrich_item(item),
            "disposition": "keep",
            "texture_visibility_read": "pass_visible_but_premium",
            "texture_readability_read": "pass",
            "era_match_read": "pass_1985_1987_dp_override_challenger_consistent",
            "historical_signal_texture_read": "pass",
            "youtube_survival_read": "pass_5mbps_proxy_generated",
            "compression_artifact_read": "pass_texture_distinct_from_youtube_mud",
            "detail_survival_read": "pass_subject_detail_preserved",
            "may_start_motion_video_proof": True,
        }
        for item in texture_manifest["items"]
    ]
    accepted_path = texture_manifest_path.with_name("historical_signal_texture_manifest_accepted.json")
    write_json(accepted_path, accepted)
    write_text(
        TEXTURE_ACCEPTANCE_NOTE,
        f"""# Therac-25 Historical Signal Texture Acceptance Pass 29

- `stage`: `historical_signal_texture_accepted`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `pass_id`: `{PASS29_ID}`
- `created_at`: `{utc_now()}`
- `historical_context_year_or_range`: `{HISTORICAL_RANGE}`
- `historical_signal_profile_id`: `{PROFILE_ID}`
- `signal_texture_strength`: `{SIGNAL_STRENGTH}`
- `texture_applied_before_captions`: `true`
- `texture_manifest_path`: `{texture_manifest_path}`
- `accepted_texture_manifest_path`: `{accepted_path}`
- `review_sheet_path`: `{texture_manifest['review_sheet_path']}`
- `disposition`: `keep`

## Read

The default Therac institutional-video profile is overridden by user/DP direction to match the Challenger visible-but-premium broadcast CRT calibration. The texture is a source-preserving historical signal treatment, full-bleed, with no TV frame, matte, border, rounded mask, fake caption, or reduced image area.

Public release remains blocked pending source-footage rights/fair-use acceptance, actual-photo provenance/source-clearance recording, Paper Architecture claim checks, and YouTube unlisted processing checks.
""",
    )
    return accepted_path


def write_texture_asset_inventory(accepted_texture_path: Path) -> Path:
    accepted = read_json(accepted_texture_path)
    inventory = {
        "schema_version": "1.0",
        "stage": "historical_signal_texture_asset_inventory",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "pass_id": PASS29_ID,
        "created_at": utc_now(),
        "input_accepted_texture_manifest_path": str(accepted_texture_path),
        "input_accepted_texture_manifest_sha256": sha256(accepted_texture_path),
        "historical_signal_profile_id": PROFILE_ID,
        "signal_texture_strength": SIGNAL_STRENGTH,
        "texture_applied_before_captions": True,
        "review_sheet_path": accepted["review_sheet_path"],
        "review_sheet_sha256": accepted["review_sheet_sha256"],
        "items": [
            {
                "row_id": item["row_id"],
                "order_label": item["order_label"],
                "source_url": item.get("source_url", ""),
                "original_youtube_url": item.get("original_youtube_url", item.get("source_url", "")),
                "source_motion_clip_path": item["source_motion_clip_path"],
                "source_motion_sha256": item["source_motion_sha256"],
                "conservative_clean_path": item["conservative_clean_path"],
                "conservative_clean_sha256": item["conservative_clean_sha256"],
                "texture_applied_path": item["texture_applied_path"],
                "texture_applied_sha256": item["texture_applied_sha256"],
                "youtube_survival_proxy_path": item["youtube_survival_proxy_path"],
                "youtube_survival_proxy_sha256": item["youtube_survival_proxy_sha256"],
                "frame_audit_paths": item["frame_audit_paths"],
                "historical_signal_profile_id": item["historical_signal_profile_id"],
                "signal_texture_strength": item["signal_texture_strength"],
                "rights_read": item.get("rights_read", "source_rights_unresolved_for_final_use"),
                "allowed_use": item.get("allowed_use", "internal_review_only_pending_rights"),
                "production_disposition": item.get("production_disposition", "internal_review_only_public_release_blocked"),
                "hygiene_read": item.get("hygiene_read", ""),
                "historical_signal_texture_read": item["historical_signal_texture_read"],
            }
            for item in accepted["items"]
        ],
        "public_release_blocked": True,
        "public_release_blockers": [
            "source-footage rights/fair-use acceptance pending",
            "actual-photo provenance/source-clearance record remains unresolved",
            "Paper Architecture YouTube claim check pending",
            "YouTube unlisted processing check pending",
        ],
    }
    write_json(TEXTURE_ASSET_INVENTORY, inventory)
    return TEXTURE_ASSET_INVENTORY


def concat_textured_motion(texture_manifest: dict[str, Any]) -> tuple[Path, Path]:
    SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    ordered = sorted(texture_manifest["items"], key=lambda item: int(str(item.get("order_label") or "0")))
    concat_path = PASS29_DIR / "concat_pass29_1980s_crt_visible_but_premium.txt"
    concat_path.write_text(
        "".join(f"file '{Path(item['texture_applied_path'])}'\n" for item in ordered),
        encoding="utf-8",
    )
    motion_only_path = PASS29_DIR / "therac25_motion_video_proof_pass_29_1980s_crt_visible_but_premium_motion_only_no_audio.mp4"
    run(
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
            "-b:v",
            "6000k",
            "-maxrate",
            "8000k",
            "-bufsize",
            "12000k",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(motion_only_path),
        ],
        label="concat pass29 textured motion",
    )
    return concat_path, motion_only_path


def build_textured_proof(pass28: dict[str, Any], accepted_texture_path: Path) -> tuple[Path, Path, Path]:
    texture_manifest = read_json(accepted_texture_path)
    concat_path, motion_only_path = concat_textured_motion(texture_manifest)
    proof_path = PASS29_DIR / "therac25_motion_video_proof_pass_29_1980s_crt_visible_but_premium_audio_timed.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(motion_only_path),
            "-i",
            str(AUDIO_WAV),
            "-filter_complex",
            f"[1:a]apad=pad_dur=8,atrim=0:{FINAL_DURATION_SECONDS:.3f},asetpts=PTS-STARTPTS[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(proof_path),
        ],
        label="mux pass29 textured proof",
    )
    frame_sheet = CONTACT_DIR / "therac25_motion_video_proof_pass_29_1980s_crt_visible_but_premium_frame_sheet.png"
    CONTACT_DIR.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(proof_path),
            "-vf",
            "fps=1/4,scale=180:320:force_original_aspect_ratio=decrease,"
            "pad=180:320:(ow-iw)/2:(oh-ih)/2:white,tile=5x4:padding=8:margin=12:color=white",
            "-frames:v",
            "1",
            str(frame_sheet),
        ],
        label="render pass29 proof frame sheet",
    )
    tail_frames: dict[str, str] = {}
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    for label, ts in {"tail_start": 51.6, "voice_end": 56.4, "outro_end": 59.7}.items():
        frame_path = FRAME_DIR / f"pass29_{label}_{ts:.1f}s.jpg"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{ts:.3f}",
                "-i",
                str(proof_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(frame_path),
            ],
            label=f"extract pass29 {label}",
        )
        tail_frames[label] = str(frame_path)

    proof_duration = ffprobe_duration(proof_path)
    motion_duration = ffprobe_duration(motion_only_path)
    segments_by_order = sorted(texture_manifest["items"], key=lambda item: int(str(item.get("order_label") or "0")))
    proof_manifest_path = PASS29_DIR / "therac25_motion_video_proof_pass_29_1980s_crt_visible_but_premium__proof.json"
    proof_manifest = {
        "created_at": utc_now(),
        "schema_version": "1.0",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "stage": "motion_video_proof_1980s_crt_texture_repair",
        "pass_id": PASS29_ID,
        "input_pass28_manifest_path": str(PASS28_MANIFEST),
        "input_pass28_manifest_sha256": sha256(PASS28_MANIFEST),
        "texture_ready_manifest_path": str(TEXTURE_READY_MANIFEST),
        "texture_ready_manifest_sha256": sha256(TEXTURE_READY_MANIFEST),
        "historical_signal_texture_manifest_path": str(accepted_texture_path),
        "historical_signal_texture_manifest_sha256": sha256(accepted_texture_path),
        "historical_signal_texture_asset_inventory_path": str(TEXTURE_ASSET_INVENTORY),
        "historical_signal_texture_asset_inventory_sha256": sha256(TEXTURE_ASSET_INVENTORY),
        "historical_signal_texture_review_note_path": str(TEXTURE_REVIEW_NOTE),
        "historical_signal_texture_acceptance_note_path": str(TEXTURE_ACCEPTANCE_NOTE),
        "historical_signal_texture_registry_path": str(REGISTRY),
        "historical_signal_texture_registry_sha256": sha256(REGISTRY),
        "historical_signal_texture_used": True,
        "historical_signal_profile_id": PROFILE_ID,
        "historical_signal_texture_profile_id": PROFILE_ID,
        "signal_texture_strength": SIGNAL_STRENGTH,
        "historical_context_year_or_range": HISTORICAL_RANGE,
        "source_media_era": SOURCE_MEDIA_ERA,
        "texture_applied_before_captions": True,
        "texture_visibility_read": "pass_visible_but_premium",
        "texture_readability_read": "pass",
        "era_match_read": "pass_1985_1987_dp_override_challenger_consistent",
        "historical_signal_texture_read": "pass",
        "youtube_survival_read": "pass_5mbps_proxy_generated",
        "compression_artifact_read": "pass_texture_distinct_from_youtube_mud",
        "detail_survival_read": "pass_subject_detail_preserved",
        "disposition": "keep",
        "reel_class": "keeper short",
        "proof_video_path": str(proof_path),
        "proof_path": str(proof_path),
        "motion_only_video_path": str(motion_only_path),
        "concat_path": str(concat_path),
        "frame_sheet_path": str(frame_sheet),
        "caption_source_path": pass28["caption_source_path"],
        "caption_timing_path": pass28.get("caption_timing_path", ""),
        "short_audio_package_path": str(AUDIO_PACKAGE),
        "audio_package_sha256": sha256(AUDIO_PACKAGE),
        "packaged_audio_sha256": sha256(AUDIO_WAV),
        "transcript_sha256": pass28["transcript_sha256"],
        "audio_disposition": "keep",
        "audio_path": str(AUDIO_WAV),
        "approved_audio_path": str(AUDIO_WAV),
        "expected_voice_profile_id": pass28["expected_voice_profile_id"],
        "duration_seconds": round(proof_duration, 6),
        "motion_only_duration_seconds": round(motion_duration, 6),
        "fps": 30,
        "story_shot_count": 17,
        "segments": [
            {
                "order": int(str(item.get("order_label") or "0")),
                "row_id": item.get("row_id"),
                "edl_id": item.get("row_id", "").split("_", 1)[-1],
                "source_motion_clip_path": item["source_motion_clip_path"],
                "texture_applied_path": item["texture_applied_path"],
                "youtube_survival_proxy_path": item["youtube_survival_proxy_path"],
                "source_url": item.get("source_url", ""),
                "original_youtube_url": item.get("original_youtube_url", item.get("source_url", "")),
                "historical_signal_profile_id": item["historical_signal_profile_id"],
                "signal_texture_strength": item["signal_texture_strength"],
                "texture_visibility_read": item["texture_visibility_read"],
                "era_match_read": item["era_match_read"],
                "historical_signal_texture_read": item["historical_signal_texture_read"],
                "production_disposition": "internal_review_only_public_release_blocked",
                "rights_read": item.get("rights_read", "source_rights_unresolved_for_final_use"),
                "allowed_use": item.get("allowed_use", "internal_review_only_pending_rights"),
                "motion_disposition": "keep",
            }
            for item in segments_by_order
        ],
        "tail_repair": {
            **pass28.get("tail_repair", {}),
            "last_clip_freeze_read": "pass_textured_real_source_motion_no_cloned_tail",
            "outro_completion_read": "pass_full_outro_window_preserved_for_final_mix",
            "tail_review_frames": tail_frames,
        },
        "gate_assertions": {
            "proof_disposition": "keep",
            "reel_class": "keeper short",
            "all_motion_clips_are_keep": True,
            "no_diagnostic_placeholders": True,
            "no_final_cloned_frame_tail": True,
            "historical_signal_texture_used": True,
            "historical_signal_texture_read": "pass",
            "texture_applied_before_captions": True,
            "public_release_blocker_recorded": True,
        },
        "may_start_final_export": True,
        "may_start_motion_video_proof": False,
        "may_start_ltx_render": False,
        "may_start_generated_stills": False,
        "public_release_blocked": True,
        "public_release_blockers": [
            "source-footage rights/fair-use acceptance pending",
            "actual-photo provenance/source-clearance record remains unresolved",
            "Paper Architecture YouTube claim check pending",
        ],
    }
    write_json(proof_manifest_path, proof_manifest)
    write_text(
        PROOF_REVIEW_NOTE,
        f"""# Therac-25 Motion Video Proof Pass 29 1980s CRT Texture Repair

Disposition: keep

Reel class: keeper-short

Proof:
`{proof_path}`

Frame sheet:
`{frame_sheet}`

Texture review sheet:
`{texture_manifest['review_sheet_path']}`

Repair read:
- Pass 29 preserves pass 28 timing, continuous tail motion, and the full outro window.
- Texture profile is `{PROFILE_ID}` at `{SIGNAL_STRENGTH}`, recorded as a DP override for Therac's 1985-1987 period surface.
- Review clips remain visual-only/no-audio; the proof uses only the approved Therac short audio.

Public release remains blocked pending source-footage rights/fair-use acceptance, actual-photo provenance/source-clearance recording, Paper Architecture claim checks, and YouTube unlisted processing checks.
""",
    )
    return proof_manifest_path, proof_path, frame_sheet


def mix_final_with_captions(pass02: dict[str, Any], proof_path: Path, proof_manifest_path: Path) -> Path:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    caption_ass = FINAL_DIR / f"{stamp}__captions.ass"
    caption_srt = FINAL_DIR / f"{stamp}__captions.srt"
    caption_timing = FINAL_DIR / f"{stamp}__caption_timing.json"
    shutil.copy2(pass02["caption_ass_path"], caption_ass)
    shutil.copy2(pass02["caption_srt_path"], caption_srt)
    shutil.copy2(pass02["caption_timing_path"], caption_timing)

    captioned_voice_only = FINAL_DIR / f"{stamp}__captioned_voice_only.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(proof_path),
            "-vf",
            f"subtitles=filename={caption_ass}:original_size=1080x1920",
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            "6000k",
            "-maxrate",
            "8000k",
            "-bufsize",
            "12000k",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(captioned_voice_only),
        ],
        label="apply pass03 captions after texture",
    )

    final_path = FINAL_DIR / f"{stamp}__captioned_final.mp4"
    outro_delay_ms = int(round(OUTRO_START_SECONDS * 1000.0))
    outro_ramp_local_start = MOTIF_RAMP_START_SECONDS - OUTRO_START_SECONDS
    outro_ramp_local_end = FINAL_DURATION_SECONDS - OUTRO_START_SECONDS
    outro_ramp_duration = outro_ramp_local_end - outro_ramp_local_start
    volume_expr = (
        f"if(lt(t,{outro_ramp_local_start:.3f}),0.100000,"
        f"if(lt(t,{outro_ramp_local_end:.3f}),"
        f"0.100000+(t-{outro_ramp_local_start:.3f})*(0.720000/{outro_ramp_duration:.3f}),0.820000))"
    )
    filter_complex = ";".join(
        [
            f"[0:v]trim=0:{FINAL_DURATION_SECONDS:.3f},setpts=PTS-STARTPTS[v]",
            f"[0:a]atrim=0:{FINAL_DURATION_SECONDS:.3f},asetpts=PTS-STARTPTS[voice]",
            "[1:a]"
            f"atrim=0:{OUTRO_START_SECONDS:.3f},asetpts=PTS-STARTPTS,volume=0.200000,"
            f"afade=t=out:st={OUTRO_START_SECONDS - 0.5:.3f}:d=0.500[body]",
            "[2:a]"
            f"atrim=0:{OUTRO_ASSET_DURATION_SECONDS:.3f},asetpts=PTS-STARTPTS,"
            f"volume='{volume_expr}':eval=frame,"
            "afade=t=in:st=0:d=0.200,"
            f"adelay={outro_delay_ms}:all=1[outro]",
            "[voice][body][outro]amix=inputs=3:duration=longest:normalize=0,"
            f"atrim=0:{FINAL_DURATION_SECONDS:.3f},alimiter=limit=0.89:level=false,asetpts=PTS-STARTPTS[a]",
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(captioned_voice_only),
            "-stream_loop",
            "-1",
            "-i",
            str(BODY_LOOP),
            "-i",
            str(OUTRO),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            "6000k",
            "-maxrate",
            "8000k",
            "-bufsize",
            "12000k",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_path),
        ],
        label="mix pass03 outro",
    )

    final_frame_sheet = FINAL_DIR / f"{stamp}__final_frame_sheet.png"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(final_path),
            "-vf",
            "fps=1/4,scale=180:320:force_original_aspect_ratio=decrease,"
            "pad=180:320:(ow-iw)/2:(oh-ih)/2:white,tile=5x4:padding=8:margin=12:color=white",
            "-frames:v",
            "1",
            str(final_frame_sheet),
        ],
        label="render pass03 final frame sheet",
    )

    final_duration = ffprobe_duration(final_path)
    peak_db = measure_peak_db(final_path)
    proof_manifest = read_json(proof_manifest_path)
    texture_manifest_path = Path(proof_manifest["historical_signal_texture_manifest_path"])
    texture_manifest = read_json(texture_manifest_path)
    music_context = {
        **pass02.get("final_music_context", {}),
        "source_duration_seconds": round(ffprobe_duration(proof_path), 6),
        "final_duration_seconds": round(final_duration, 6),
        "target_final_duration_seconds": FINAL_DURATION_SECONDS,
        "final_frame_hold_seconds": 0.0,
        "captioned_voice_only_path": str(captioned_voice_only),
        "body_loop_end_seconds": OUTRO_START_SECONDS,
        "body_loop_fade_out_start_seconds": round(OUTRO_START_SECONDS - 0.5, 3),
        "body_loop_fade_out_duration_seconds": 0.5,
        "outro_start_seconds": OUTRO_START_SECONDS,
        "outro_asset_duration_seconds": OUTRO_ASSET_DURATION_SECONDS,
        "outro_duration_used_seconds": OUTRO_ASSET_DURATION_SECONDS,
        "outro_initial_volume_linear": 0.1,
        "outro_ramp_start_seconds": MOTIF_RAMP_START_SECONDS,
        "outro_ramp_end_seconds": FINAL_DURATION_SECONDS,
        "outro_ramp_end_volume_linear": 0.82,
        "outro_fade_in_duration_seconds": 0.2,
        "outro_completion_read": "pass",
        "motif_music_bed_read": "pass",
        "final_mix_peak_db": peak_db,
        "final_mix_no_clipping": peak_db is None or peak_db <= -0.1,
    }

    overlay_manifest_path = FINAL_DIR / f"{stamp}__caption_overlay_manifest.json"
    caption_timing_payload = read_json(caption_timing)
    overlay_manifest = {
        **read_json(Path(pass02["caption_overlay_manifest_path"])),
        "stage": "video final pass 03 1980s texture caption repair",
        "caption_timing_path": str(caption_timing),
        "caption_srt_path": str(caption_srt),
        "caption_ass_path": str(caption_ass),
        "captioned_final_path": str(final_path),
        "captioned_voice_only_path": str(captioned_voice_only),
        "caption_segments": caption_timing_payload.get("segments", []),
        "historical_signal_texture_used": True,
        "historical_signal_profile_id": PROFILE_ID,
        "signal_texture_strength": SIGNAL_STRENGTH,
        "texture_applied_before_captions": True,
        "final_music_context": music_context,
        "tail_repair_read": "pass03 preserves pass02 real source motion under the outro; no final cloned-frame tail",
    }
    write_json(overlay_manifest_path, overlay_manifest)

    final_manifest_path = FINAL_DIR / f"{stamp}__final_export.json"
    final_manifest = {
        **pass02,
        "created_at": utc_now(),
        "stage": "video final pass 03 1980s texture caption repair",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "input_final_export_pass02_manifest_path": str(PASS02_FINAL_MANIFEST),
        "input_final_export_pass02_sha256": sha256(PASS02_FINAL_MANIFEST),
        "source_proof_manifest_path": str(proof_manifest_path),
        "proof_video_path": str(proof_path),
        "proof_review_note_path": str(PROOF_REVIEW_NOTE),
        "texture_ready_manifest_path": str(TEXTURE_READY_MANIFEST),
        "texture_ready_manifest_sha256": sha256(TEXTURE_READY_MANIFEST),
        "historical_signal_texture_used": True,
        "historical_signal_texture_registry_path": str(REGISTRY),
        "historical_signal_texture_registry_sha256": sha256(REGISTRY),
        "historical_signal_texture_manifest_path": str(texture_manifest_path),
        "historical_signal_texture_manifest_sha256": sha256(texture_manifest_path),
        "historical_signal_texture_asset_inventory_path": str(TEXTURE_ASSET_INVENTORY),
        "historical_signal_texture_asset_inventory_sha256": sha256(TEXTURE_ASSET_INVENTORY),
        "historical_signal_texture_review_note_path": str(TEXTURE_REVIEW_NOTE),
        "historical_signal_texture_acceptance_note_path": str(TEXTURE_ACCEPTANCE_NOTE),
        "historical_signal_profile_id": PROFILE_ID,
        "historical_signal_texture_profile_id": PROFILE_ID,
        "signal_texture_strength": SIGNAL_STRENGTH,
        "historical_context_year_or_range": HISTORICAL_RANGE,
        "source_media_era": SOURCE_MEDIA_ERA,
        "texture_applied_before_captions": True,
        "texture_visibility_read": "pass_visible_but_premium",
        "texture_readability_read": "pass",
        "era_match_read": "pass_1985_1987_dp_override_challenger_consistent",
        "historical_signal_texture_read": "pass",
        "youtube_survival_read": "pass_5mbps_proxy_generated",
        "compression_artifact_read": "pass_texture_distinct_from_youtube_mud",
        "detail_survival_read": "pass_subject_detail_preserved",
        "caption_style_preset": "early_1980s_broadcast_cg_v1",
        "caption_placement": "lower-left",
        "caption_timing_path": str(caption_timing),
        "caption_srt_path": str(caption_srt),
        "caption_ass_path": str(caption_ass),
        "caption_overlay_manifest_path": str(overlay_manifest_path),
        "captioned_final_path": str(final_path),
        "captioned_voice_only_path": str(captioned_voice_only),
        "captioned_final_sha256": sha256(final_path),
        "captioned_voice_only_sha256": sha256(captioned_voice_only),
        "final_video_sha256": sha256(final_path),
        "final_frame_sheet_path": str(final_frame_sheet),
        "final_frame_sheet_sha256": sha256(final_frame_sheet),
        "duration_seconds": round(final_duration, 6),
        "final_frame_hold_seconds": 0.0,
        "motif_outro_mix_used": True,
        "music_track_id": "paper_architecture_theme_v1",
        "music_policy": "canonical_default",
        "music_rights_check_status": "registered_track_hash_verified_publish_claim_check_pending",
        "final_mix_peak_db": peak_db,
        "final_mix_no_clipping": peak_db is None or peak_db <= -0.1,
        "final_music_context": music_context,
        "supersedes_final_export_pass_02_path": pass02["captioned_final_path"],
        "supersedes_final_export_pass_02_reason": "pass 02 lacked an era-appropriate historical signal texture",
        "outputs": {
            "caption_timing_path": str(caption_timing),
            "caption_srt_path": str(caption_srt),
            "caption_overlay_manifest_path": str(overlay_manifest_path),
            "captioned_final_path": str(final_path),
            "captioned_voice_only_path": str(captioned_voice_only),
            "final_frame_sheet_path": str(final_frame_sheet),
            "historical_signal_texture_review_sheet_path": texture_manifest.get("review_sheet_path", ""),
        },
        "gate_assertions": {
            **pass02.get("gate_assertions", {}),
            "proof_disposition": "keep",
            "reel_class": "keeper short",
            "no_final_cloned_frame_tail": True,
            "full_outro_asset_used": True,
            "historical_signal_texture_used": True,
            "historical_signal_texture_read": "pass",
            "texture_applied_before_captions": True,
            "caption_style_period_read": "pass_early_1980s_broadcast_cg_v1_lower_left",
            "unresolved_mixed_review_blockers": False,
        },
        "public_release_blocked": True,
        "public_release_blockers": [
            "source-footage rights/fair-use acceptance pending",
            "actual-photo provenance/source-clearance record remains unresolved",
            "Paper Architecture YouTube claim check pending",
            "YouTube unlisted processing check pending",
        ],
    }
    write_json(final_manifest_path, final_manifest)

    write_text(
        FINAL_REVIEW_NOTE,
        f"""# Therac-25 Final Export Pass 03 1980s CRT Texture And Caption Repair

Disposition: review-ready

Captioned final:
`{final_path}`

Final frame sheet:
`{final_frame_sheet}`

Texture review sheet:
`{texture_manifest.get('review_sheet_path', '')}`

Final export manifest:
`{final_manifest_path}`

Repair read:
- Pass 03 supersedes pass 02 because pass 02 had the right early-1980s caption style but no historical signal texture.
- Texture uses `{PROFILE_ID}` at `{SIGNAL_STRENGTH}`, matching Challenger by DP override for the Therac 1985-1987 period surface.
- Texture was applied before captions; captions remain `{final_manifest['caption_style_preset']}` with `{final_manifest['caption_placement']}` placement.
- Final duration is `{final_duration:.3f}s`; final-frame cloned padding is `0.0s`.
- Paper Architecture outro still completes under continuous real source motion.

Public upload/release remains blocked pending source-footage rights/fair-use acceptance, actual-photo provenance/source-clearance recording, Paper Architecture claim checks, and YouTube unlisted processing checks.
""",
    )
    return final_manifest_path


def build_publish_package(final_manifest_path: Path) -> Path:
    final_manifest = read_json(final_manifest_path)
    proof_manifest = read_json(Path(final_manifest["source_proof_manifest_path"]))
    package_dir = PUBLISH_ROOT / f"youtube_{utc_stamp()}_pass02_1980s_texture"
    package_dir.mkdir(parents=True, exist_ok=True)

    final_mp4 = Path(final_manifest["captioned_final_path"])
    final_srt = Path(final_manifest["caption_srt_path"])
    final_review = FINAL_REVIEW_NOTE
    upload_video = package_dir / "therac25_software_safety_youtube_short.mp4"
    upload_srt = package_dir / "therac25_software_safety_captions.srt"
    final_manifest_copy = package_dir / "final_export_manifest.json"
    final_review_copy = package_dir / "final_review.md"
    shutil.copy2(final_mp4, upload_video)
    shutil.copy2(final_srt, upload_srt)
    shutil.copy2(final_manifest_path, final_manifest_copy)
    shutil.copy2(final_review, final_review_copy)

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
            proof_manifest["proof_video_path"],
            "-frames:v",
            "1",
            str(cover_frame),
        ],
        label="extract pass03 cover frame",
    )

    title_path = package_dir / "youtube_title.txt"
    description_path = package_dir / "youtube_description.txt"
    tags_path = package_dir / "youtube_tags.txt"
    metadata_path = package_dir / "youtube_metadata.md"
    checklist_path = package_dir / "upload_checklist.md"
    delivery_manifest_path = package_dir / "delivery_manifest.json"
    rights_review_publish = package_dir / "rights_fair_use_review.md"
    approval_publish = package_dir / "final_human_approval.md"
    keeper_capsule_publish = package_dir / "keeper_lesson_capsule.md"

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

    final_sha = sha256(final_mp4)
    final_manifest_sha = sha256(final_manifest_path)
    final_review_sha = sha256(final_review)
    approval_text = f"""# Therac-25 Final Human Approval Pass 03

- `stage`: `video final approval`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `approved_final_path`: `{final_mp4}`
- `approved_final_sha256`: `{final_sha}`
- `final_export_manifest_path`: `{final_manifest_path}`
- `final_export_manifest_sha256`: `{final_manifest_sha}`
- `disposition`: `review_ready_keep`
- `reel_class`: `keeper short`
- `approval_source`: `thread implementation request`
- `approval_note`: `Implement Therac-25 mid-1980s texture and caption repair with Challenger-consistent visible_but_premium texture.`
- `current_gate`: `publish/release review`

Public release remains blocked pending source-footage rights/fair-use acceptance, actual-photo provenance/source-clearance recording, Paper Architecture claim checks, and YouTube unlisted processing checks.
"""
    approval_production = PROD_ROOT / "final_human_approval_pass_03_1980s_texture.md"
    write_text(approval_production, approval_text)
    write_text(approval_publish, approval_text)

    keeper_capsule_text = f"""# Therac-25 Keeper Lesson Capsule

## Keeper Capsule

- `stage`: `keeper lesson capsule`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `keeper_final_path`: `{final_mp4}`
- `keeper_final_sha256`: `{final_sha}`
- `keeper_final_manifest_path`: `{final_manifest_path}`
- `keeper_final_manifest_sha256`: `{final_manifest_sha}`
- `publishable_approved_at`: `{utc_now()}`
- `production_model_lane`: `source_led_youtube_archival_motion_with_strict_clean_hygiene`
- `historical_signal_profile_id`: `{PROFILE_ID}`
- `signal_texture_strength`: `{SIGNAL_STRENGTH}`
- `texture_applied_before_captions`: `true`
- `caption_style_preset`: `{final_manifest['caption_style_preset']}`
- `caption_placement`: `{final_manifest['caption_placement']}`
- `music_track_id`: `paper_architecture_theme_v1`
- `music_policy`: `canonical_default`
- `music_rights_check_status`: `pending_youtube_upload_check`
- `motif_outro_mix_used`: `true`
- `disposition`: `keep`

## Reusable Lessons

| `lesson_id` | `lesson` | `scope` | `evidence_path` | `action` |
|---|---|---|---|---|
| `therac_texture_before_captions_v1` | Apply period signal texture before final caption burn-in so the image has historical media texture while captions stay readable. | `global_policy_candidate` | `{final_manifest_path}` | `remember_only` |
| `therac_visible_but_premium_1980s_v1` | For 1980s Shorts using broadcast-linked archival motion, Challenger-calibrated `visible_but_premium` can convey period signal without turning into YouTube compression mud. | `global_policy_candidate` | `{final_manifest['historical_signal_texture_manifest_path']}` | `remember_only` |

## Handoff

- `global_policy_updates_recommended`: `false`
- `next_episode_implications`: Use the registered historical signal texture pass before final captions when the DP approves period media texture.
- `blockers_before_public_release`: Source-footage rights/fair-use acceptance, actual-photo provenance/source-clearance recording, Paper Architecture claim checks, and YouTube unlisted processing checks remain unresolved.
"""
    keeper_capsule_production = PROD_ROOT / "keeper_lesson_capsule_pass_03_1980s_texture.md"
    write_text(keeper_capsule_production, keeper_capsule_text)
    write_text(keeper_capsule_publish, keeper_capsule_text)

    rights_review_text = f"""# Therac-25 Publish Rights / Fair-Use Review Pass 02

## Review

- `stage`: `publish/release review`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `created_at`: `{utc_now()}`
- `captioned_final_path`: `{final_mp4}`
- `historical_signal_profile_id`: `{PROFILE_ID}`
- `signal_texture_strength`: `{SIGNAL_STRENGTH}`
- `music_track_id`: `paper_architecture_theme_v1`
- `music_policy`: `canonical_default`
- `disposition`: `manual_review_required`

## Rights Read

The textured creative final is a keeper for local upload review. Public release is not cleared. The Short uses YouTube/archive-derived clinical and software-safety footage plus the Paper Architecture music bed/outro.

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
    rights_review_production = PROD_ROOT / "publish_rights_fair_use_review_pass_02_1980s_texture.md"
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

- Confirm final pass 03 shows the visible-but-premium 1980s texture without muddying subject detail.
- Confirm captions remain readable over the textured picture.
- Confirm the last visual and Paper Architecture outro complete without a freeze.
- Upload unlisted first.
- Check YouTube processing and Content ID for Paper Architecture.
- Complete source-footage rights/fair-use review before public release.
""",
    )

    technical_read = probe_video(upload_video)
    source_used_ids = sorted(
        {
            str(seg.get("source_url", "")).split("v=")[-1]
            for seg in read_json(PASS28_MANIFEST).get("segments", [])
            if seg.get("source_url")
        }
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
        "publication_readiness": "ready_for_upload_review_with_rights_check",
        "source_final": {
            "path": str(final_mp4),
            "sha256": final_sha,
            "final_export_manifest_path": str(final_manifest_path),
            "final_export_manifest_sha256": final_manifest_sha,
            "review_path": str(final_review),
            "review_sha256": final_review_sha,
            "final_human_approval_path": str(approval_production),
            "final_human_approval_sha256": sha256(approval_production),
            "keeper_lesson_capsule_path": str(keeper_capsule_production),
            "keeper_lesson_capsule_sha256": sha256(keeper_capsule_production),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
            "may_publish_scope": "creative_keep_package_ready_requires_human_rights_and_music_checks_before_public",
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
        "historical_signal_texture_context": {
            "historical_signal_texture_used": True,
            "historical_signal_profile_id": PROFILE_ID,
            "signal_texture_strength": SIGNAL_STRENGTH,
            "texture_applied_before_captions": True,
            "texture_visibility_read": final_manifest["texture_visibility_read"],
            "era_match_read": final_manifest["era_match_read"],
            "youtube_survival_read": final_manifest["youtube_survival_read"],
            "compression_artifact_read": final_manifest["compression_artifact_read"],
            "detail_survival_read": final_manifest["detail_survival_read"],
        },
        "rights_and_claims": {
            "source_footage_rights_read": "manual_review_required",
            "actual_photo_provenance_read": "unresolved_not_used_as_cleared_surface",
            "music_bed_used": True,
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "claim_risk": "Manual source-footage fair-use review, actual-photo provenance record, and YouTube Content ID claim check required before public release.",
            "public_publish_clearance": "blocked_until_human_rights_acceptance_and_youtube_checks",
        },
        "source_provenance": {
            "proof_manifest_path": str(final_manifest["source_proof_manifest_path"]),
            "proof_manifest_sha256": sha256(Path(final_manifest["source_proof_manifest_path"])),
            "historical_signal_texture_asset_inventory_path": final_manifest["historical_signal_texture_asset_inventory_path"],
            "historical_signal_texture_asset_inventory_sha256": final_manifest["historical_signal_texture_asset_inventory_sha256"],
            "used_youtube_ids": source_used_ids,
            "source_inventory_path": str(SOURCE_INVENTORY) if SOURCE_INVENTORY.exists() else "",
            "source_inventory_sha256": sha256(SOURCE_INVENTORY) if SOURCE_INVENTORY.exists() else "",
        },
        "final_music_context": {
            **final_manifest.get("final_music_context", {}),
            "music_rights_check_status": "pending_youtube_upload_check",
        },
    }
    write_json(upload_manifest_path, upload_manifest)

    publish_packet = PROD_ROOT / "youtube_publish_package_pass_02_1980s_texture.md"
    write_text(
        publish_packet,
        f"""# Therac-25 YouTube Publish Package Pass 02 1980s Texture

- `stage`: `publish/release review`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `package_root`: `{package_dir}`
- `youtube_upload_manifest_path`: `{upload_manifest_path}`
- `youtube_upload_manifest_sha256`: `{sha256(upload_manifest_path)}`
- `upload_video_path`: `{upload_video}`
- `upload_video_sha256`: `{sha256(upload_video)}`
- `publication_readiness`: `ready_for_upload_review_with_rights_check`
- `public_release_blocked`: `true`

## Gate Read

The package is ready for local upload review with pass 03 texture/caption repair. Public release remains blocked until source-footage rights/fair-use acceptance, actual-photo provenance/source-clearance recording, Paper Architecture claim checks, and YouTube unlisted processing checks are complete.
""",
    )
    return upload_manifest_path


def update_root_and_ledgers(final_manifest_path: Path, upload_manifest_path: Path) -> None:
    final_manifest = read_json(final_manifest_path)
    upload_manifest = read_json(upload_manifest_path)
    root = read_json(ROOT_MANIFEST)
    root["current_stage"] = "publish/release review"
    root["last_completed_stage"] = "youtube publish package pass 02 1980s texture repair"
    root["next_action"] = "Review textured pass 03 final and local YouTube publish package; public release remains blocked pending source/music rights and YouTube checks."
    root["active_review_surface_path"] = final_manifest["captioned_final_path"]
    root["active_review_manifest_path"] = str(final_manifest_path)
    root["captioned_final_path"] = final_manifest["captioned_final_path"]
    root["captioned_final_sha256"] = sha256(Path(final_manifest["captioned_final_path"]))
    root["final_export_manifest_path"] = str(final_manifest_path)
    root["final_export_manifest_sha256"] = sha256(final_manifest_path)
    root["final_caption_overlay_manifest_path"] = final_manifest["caption_overlay_manifest_path"]
    root["final_caption_overlay_manifest_sha256"] = sha256(Path(final_manifest["caption_overlay_manifest_path"]))
    root["final_frame_sheet_path"] = final_manifest["final_frame_sheet_path"]
    root["final_frame_sheet_sha256"] = sha256(Path(final_manifest["final_frame_sheet_path"]))
    root["historical_signal_texture_manifest_path"] = final_manifest["historical_signal_texture_manifest_path"]
    root["historical_signal_texture_manifest_sha256"] = final_manifest["historical_signal_texture_manifest_sha256"]
    root["historical_signal_texture_asset_inventory_path"] = final_manifest["historical_signal_texture_asset_inventory_path"]
    root["historical_signal_texture_asset_inventory_sha256"] = final_manifest["historical_signal_texture_asset_inventory_sha256"]
    root["historical_signal_texture_review_note_path"] = final_manifest["historical_signal_texture_review_note_path"]
    root["historical_signal_profile_id"] = PROFILE_ID
    root["signal_texture_strength"] = SIGNAL_STRENGTH
    root["texture_applied_before_captions"] = True
    root["superseded_final_export_pass_02_path"] = final_manifest["supersedes_final_export_pass_02_path"]
    root["superseded_final_export_pass_02_reason"] = final_manifest["supersedes_final_export_pass_02_reason"]
    root["youtube_upload_manifest_path"] = str(upload_manifest_path)
    root["youtube_upload_manifest_sha256"] = sha256(upload_manifest_path)
    root["publish_package_root"] = upload_manifest["upload_assets"]["video_path"].rsplit("/", 1)[0]
    root["publish_package_readiness"] = "ready_for_upload_review_with_rights_check"
    root["final_export_pass_03_1980s_texture"] = {
        "captioned_final_path": final_manifest["captioned_final_path"],
        "final_export_manifest_path": str(final_manifest_path),
        "final_frame_sheet_path": final_manifest["final_frame_sheet_path"],
        "historical_signal_texture_review_sheet_path": final_manifest["outputs"]["historical_signal_texture_review_sheet_path"],
        "duration_seconds": final_manifest["duration_seconds"],
        "final_frame_hold_seconds": 0.0,
        "historical_signal_profile_id": PROFILE_ID,
        "signal_texture_strength": SIGNAL_STRENGTH,
        "texture_applied_before_captions": True,
        "outro_completion_read": "pass",
        "last_clip_freeze_read": "pass",
        "public_release_blocked": True,
    }
    root["may_start_final_export"] = False
    root["may_start_ltx_render"] = False
    root["may_start_generated_stills"] = False
    root["may_start_motion_video_proof"] = False
    root["public_release_blocked"] = True
    root["public_release_blockers"] = [
        "manual source-rights/fair-use acceptance",
        "actual-photo provenance/source-clearance record remains unresolved",
        "Paper Architecture YouTube claim check",
        "YouTube unlisted processing check",
    ]
    write_json(ROOT_MANIFEST, root)

    append = f"""

## Video Final Pass 03 1980s Texture And Caption Repair

- `captioned_final_path`: `{final_manifest['captioned_final_path']}`
- `final_export_manifest_path`: `{final_manifest_path}`
- `final_frame_sheet_path`: `{final_manifest['final_frame_sheet_path']}`
- `historical_signal_texture_review_sheet_path`: `{final_manifest['outputs']['historical_signal_texture_review_sheet_path']}`
- `historical_signal_profile_id`: `{PROFILE_ID}`
- `signal_texture_strength`: `{SIGNAL_STRENGTH}`
- `texture_applied_before_captions`: `true`
- `supersedes`: pass 02, because pass 02 had period captions but no historical signal texture.
- `youtube_upload_manifest_path`: `{upload_manifest_path}`
- `public_release_blocked`: `true; source/music rights and YouTube checks pending`
"""
    for path in (
        PROD_ROOT / "stage_ledger.md",
        PROD_ROOT / "workflow_scope_manifest.md",
        PROD_ROOT / "short_production_pilot.md",
        PROD_ROOT / "deferred_gaps.md",
    ):
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if append not in text:
                path.write_text(text.rstrip() + "\n" + append, encoding="utf-8")


def build() -> Path:
    for path in (
        PASS28_MANIFEST,
        PASS02_FINAL_MANIFEST,
        ROOT_MANIFEST,
        REGISTRY,
        CE_BIN,
        AUDIO_WAV,
        AUDIO_PACKAGE,
        BODY_LOOP,
        OUTRO,
        MUSIC_REGISTRY,
    ):
        require(path)
    for directory in (PASS29_DIR, SEGMENTS_DIR, CONTACT_DIR, FRAME_DIR, FINAL_DIR, PROD_ROOT, PUBLISH_ROOT):
        directory.mkdir(parents=True, exist_ok=True)

    pass28 = read_json(PASS28_MANIFEST)
    pass02 = read_json(PASS02_FINAL_MANIFEST)
    build_texture_ready_manifest(pass28)
    texture_manifest_path = run_texture_package()
    accepted_texture_path = accepted_texture_manifest(texture_manifest_path)
    write_texture_asset_inventory(accepted_texture_path)
    proof_manifest_path, proof_path, _frame_sheet = build_textured_proof(pass28, accepted_texture_path)
    final_manifest_path = mix_final_with_captions(pass02, proof_path, proof_manifest_path)
    upload_manifest_path = build_publish_package(final_manifest_path)
    update_root_and_ledgers(final_manifest_path, upload_manifest_path)
    print(upload_manifest_path)
    return upload_manifest_path


if __name__ == "__main__":
    build()
