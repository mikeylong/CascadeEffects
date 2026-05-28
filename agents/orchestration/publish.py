from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestration.adapters import BuzzsproutPublisher, YouTubePublisher
from orchestration.domain import derive_episode_state
from orchestration.io import (
    Context,
    default_publish_notes_path,
    materialize_episode_manifest,
    path_exists,
    utc_now_iso,
    write_episode_manifest,
)

PUBLISH_TARGETS = ("youtube", "podcast")
PUBLISH_PACKAGE_TARGETS = {"youtube_shorts"}
YOUTUBE_SHORTS_MAX_DURATION_SECONDS = 180.0
YOUTUBE_PRIVACY_VALUES = {"public", "private", "unlisted"}
YOUTUBE_VIDEO_TITLE_BANNED_SUFFIX = "| Cascade Effects"
YOUTUBE_ENV_VARS = (
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REFRESH_TOKEN",
    "YOUTUBE_CHANNEL_ID",
)
YOUTUBE_PACKAGE_ENV_VARS = (
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REFRESH_TOKEN",
)
YOUTUBE_LOCAL_CONFIG_DIR = Path("/Users/mike/.config/cascade-effects/youtube")
SCRIPT_LOCKED_CAPTION_MODEL = "script_locked_canonical_text_timing_from_asr_v1"
SCRIPT_LOCKED_TEXT_POLICIES = {"script_locked", "script_locked_canonical_text_only"}
ASR_TIMING_POLICIES = {"asr_timing_only", "asr_whisperx_timing_only", "whisperx_timing_only"}
BLOCKED_CAPTION_WORD_SOURCE_MARKERS = (
    ".diarized",
    "whisperx",
    "raw_asr",
    "asr_transcript",
    "transcripts_mastered",
    "transcripts_final",
)
BUZZSPROUT_ENV_VARS = (
    "BUZZSPROUT_API_TOKEN",
    "BUZZSPROUT_PODCAST_ID",
)


class PublishValidationError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_package_path(manifest_path: Path, value: Any) -> Path:
    path = Path(str(value or "").strip()).expanduser()
    if path.is_absolute():
        return path
    return manifest_path.parent / path


def _probe_video(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
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
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    duration = payload.get("format", {}).get("duration") or video.get("duration") or audio.get("duration") or 0
    return {
        "video_codec": str(video.get("codec_name", "")).strip(),
        "audio_codec": str(audio.get("codec_name", "")).strip(),
        "width": int(video.get("width", 0) or 0),
        "height": int(video.get("height", 0) or 0),
        "duration_seconds": float(duration or 0),
        "frame_rate": str(video.get("avg_frame_rate", "")).strip(),
        "audio_sample_rate_hz": int(audio.get("sample_rate", 0) or 0),
        "audio_channels": int(audio.get("channels", 0) or 0),
    }


def _path_fields(payload: dict[str, Any]) -> list[str]:
    return sorted(key for key, value in payload.items() if key.endswith("_path") and str(value or "").strip())


def _validate_path_exists(
    *,
    manifest_path: Path,
    payload: dict[str, Any],
    field: str,
    issues: list[str],
    resolved_paths: dict[str, str],
) -> Path | None:
    value = str(payload.get(field, "")).strip()
    if not value:
        issues.append(f"Missing required path field `{field}`.")
        return None
    path = _resolve_package_path(manifest_path, value)
    resolved_paths[field] = str(path)
    if not path.exists():
        issues.append(f"Path for `{field}` does not exist: {path}")
        return None
    return path


def _validate_sha_fields(
    *,
    manifest_path: Path,
    payload: dict[str, Any],
    object_name: str,
    issues: list[str],
) -> None:
    for field, expected_value in sorted(payload.items()):
        if not field.endswith("_sha256") and field != "sha256":
            continue
        expected = str(expected_value or "").strip()
        if not expected:
            issues.append(f"`{object_name}.{field}` is empty.")
            continue
        path_field = "path" if field == "sha256" else field.removesuffix("_sha256") + "_path"
        path_value = str(payload.get(path_field, "")).strip()
        if not path_value:
            issues.append(f"`{object_name}.{field}` has no matching `{path_field}`.")
            continue
        path = _resolve_package_path(manifest_path, path_value)
        if not path.exists():
            continue
        actual = _sha256_file(path)
        if actual != expected:
            issues.append(f"`{object_name}.{field}` mismatch for {path}: expected {expected}, got {actual}.")


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _read_passes(value: Any) -> bool:
    text = str(value or "").strip().lower().replace("-", "_")
    if text.startswith(("pass_review", "pass_pending", "pending")):
        return False
    return text == "pass" or text.startswith("pass_") or text.startswith("pass ")


def _caption_word_source_looks_blocked(path_value: Any) -> bool:
    token = str(path_value or "").strip().lower()
    if "script_locked" in token or "locked_script" in token or "canonical_script" in token:
        return False
    return any(marker in token for marker in BLOCKED_CAPTION_WORD_SOURCE_MARKERS)


def _validate_shorts_caption_policy(
    *,
    manifest_path: Path,
    payload: dict[str, Any],
    issues: list[str],
    resolved_paths: dict[str, str],
) -> None:
    if str(payload.get("target", "")).strip() != "youtube_shorts":
        return
    caption_context = payload.get("caption_context", {})
    if not isinstance(caption_context, dict) or not caption_context:
        issues.append("YouTube Shorts publish packages must include `caption_context`.")
        return
    source_final = payload.get("source_final", {}) if isinstance(payload.get("source_final"), dict) else {}
    model = _first_nonempty(caption_context.get("caption_model"), source_final.get("caption_model"))
    if model != SCRIPT_LOCKED_CAPTION_MODEL:
        issues.append(
            "`caption_context.caption_model` must be "
            f"`{SCRIPT_LOCKED_CAPTION_MODEL}` for Shorts publish packages."
        )
    text_policy = _first_nonempty(
        caption_context.get("caption_text_source_policy"),
        source_final.get("caption_text_source_policy"),
    )
    if text_policy not in SCRIPT_LOCKED_TEXT_POLICIES:
        issues.append("`caption_context.caption_text_source_policy` must prove script-locked caption words.")
    timing_policy = _first_nonempty(
        caption_context.get("caption_timing_source_policy"),
        source_final.get("caption_timing_source_policy"),
    )
    if timing_policy not in ASR_TIMING_POLICIES and "timing" not in timing_policy:
        issues.append("`caption_context.caption_timing_source_policy` must identify ASR/WhisperX as timing-only evidence.")

    text_path_value = _first_nonempty(
        caption_context.get("caption_text_source_path"),
        caption_context.get("caption_source_path"),
        source_final.get("caption_text_source_path"),
        source_final.get("caption_source_path"),
    )
    if not text_path_value:
        issues.append("Missing `caption_context.caption_text_source_path`.")
    elif _caption_word_source_looks_blocked(text_path_value):
        issues.append(
            "`caption_context.caption_text_source_path` points to ASR/WhisperX/diarized text; "
            "caption words must come from a locked script or script-locked caption output."
        )
    else:
        text_path = _resolve_package_path(manifest_path, text_path_value)
        resolved_paths["caption_text_source_path"] = str(text_path)
        if not text_path.exists():
            issues.append(f"Path for `caption_context.caption_text_source_path` does not exist: {text_path}")

    timing_path_value = _first_nonempty(
        caption_context.get("caption_timing_source_path"),
        source_final.get("caption_timing_source_path"),
    )
    if not timing_path_value:
        issues.append("Missing `caption_context.caption_timing_source_path`.")
    else:
        timing_path = _resolve_package_path(manifest_path, timing_path_value)
        resolved_paths["caption_timing_source_path"] = str(timing_path)
        if not timing_path.exists():
            issues.append(f"Path for `caption_context.caption_timing_source_path` does not exist: {timing_path}")

    for read_key in (
        "caption_text_matches_script_read",
        "caption_asr_text_not_used_read",
        "caption_alignment_coverage_read",
    ):
        read_value = _first_nonempty(caption_context.get(read_key), source_final.get(read_key))
        if not _read_passes(read_value):
            issues.append(f"`caption_context.{read_key}` must be pass, got `{read_value or 'missing'}`.")

    same_source_read = _first_nonempty(
        caption_context.get("burned_in_and_sidecar_same_script_locked_source_read"),
        source_final.get("burned_in_and_sidecar_same_script_locked_source_read"),
    )
    if not _read_passes(same_source_read):
        issues.append(
            "`caption_context.burned_in_and_sidecar_same_script_locked_source_read` must be pass."
        )


def _validate_music_policy(payload: dict[str, Any], issues: list[str], warnings: list[str]) -> None:
    source_final = payload.get("source_final", {}) if isinstance(payload.get("source_final"), dict) else {}
    rights_and_claims = payload.get("rights_and_claims", {}) if isinstance(payload.get("rights_and_claims"), dict) else {}
    final_music_context = payload.get("final_music_context", {}) if isinstance(payload.get("final_music_context"), dict) else {}
    music_bed_used = rights_and_claims.get("music_bed_used")
    music_policy = _first_nonempty(
        final_music_context.get("music_policy"),
        source_final.get("music_policy"),
        rights_and_claims.get("music_policy"),
    )
    music_track_id = _first_nonempty(
        final_music_context.get("music_track_id"),
        source_final.get("music_track_id"),
        rights_and_claims.get("music_track_id"),
    )
    waiver_reason = _first_nonempty(
        final_music_context.get("music_waiver_reason"),
        source_final.get("music_waiver_reason"),
        rights_and_claims.get("music_waiver_reason"),
    )
    rights_status = _first_nonempty(
        final_music_context.get("music_rights_check_status"),
        source_final.get("music_rights_check_status"),
        rights_and_claims.get("music_rights_check_status"),
    )

    if music_bed_used is False or music_policy == "waived":
        if music_policy != "waived":
            issues.append("Packages without music must record `music_policy: waived`.")
        if not waiver_reason:
            issues.append("Packages with `music_policy: waived` must include a non-empty `music_waiver_reason`.")
        return

    if music_bed_used is not True:
        issues.append("Active YouTube Shorts packages must record `rights_and_claims.music_bed_used: true` or `music_policy: waived`.")
        return

    if not music_policy:
        warnings.append("Music-complete package is missing `music_policy`; treat as legacy music-complete metadata.")
    elif music_policy not in {"canonical_default", "alternate_approved"}:
        issues.append(f"Unsupported music policy for a music-complete package: `{music_policy}`.")
    if not music_track_id:
        warnings.append("Music-complete package is missing `music_track_id`; future packages should record the registry track id.")
    if not rights_status:
        warnings.append("Music-complete package is missing `music_rights_check_status`; confirm rights/Content ID status manually.")
    if rights_status and rights_status not in {"cleared", "pending_youtube_upload_check", "claim_warning", "manual_review_required"}:
        warnings.append(f"Unrecognized music rights/check status: {rights_status}")


def validate_publish_package_manifest(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path).expanduser()
    issues: list[str] = []
    warnings: list[str] = []
    resolved_paths: dict[str, str] = {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"ok": False, "manifest_path": str(path), "target": "", "issues": [f"Publish package manifest is missing: {path}"], "warnings": []}
    except json.JSONDecodeError as exc:
        return {"ok": False, "manifest_path": str(path), "target": "", "issues": [f"Publish package manifest JSON is invalid: {exc}"], "warnings": []}

    required_fields = ("target", "publication_readiness", "upload_assets", "technical_read", "youtube_metadata", "source_final")
    for field in required_fields:
        if field not in payload:
            issues.append(f"Missing required field `{field}`.")
    target = str(payload.get("target", "")).strip()
    if target not in PUBLISH_PACKAGE_TARGETS:
        issues.append(f"Unsupported publish package target `{target or 'unset'}`.")

    upload_assets = payload.get("upload_assets", {}) if isinstance(payload.get("upload_assets"), dict) else {}
    source_final = payload.get("source_final", {}) if isinstance(payload.get("source_final"), dict) else {}
    youtube_metadata = payload.get("youtube_metadata", {}) if isinstance(payload.get("youtube_metadata"), dict) else {}
    rights_and_claims = payload.get("rights_and_claims", {}) if isinstance(payload.get("rights_and_claims"), dict) else {}
    technical_read = payload.get("technical_read", {}) if isinstance(payload.get("technical_read"), dict) else {}

    if not str(payload.get("publication_readiness", "")).strip().startswith("ready"):
        issues.append("`publication_readiness` must start with `ready` for upload validation.")
    if str(source_final.get("disposition", "")).strip() != "keep":
        issues.append("`source_final.disposition` must be `keep`.")
    if str(source_final.get("reel_class", "")).strip() != "keeper short":
        issues.append("`source_final.reel_class` must be `keeper short`.")
    if source_final.get("may_publish") is not True:
        issues.append("`source_final.may_publish` must be true.")

    checked_upload_path_fields = set()
    for field in ("video_path", "title_path", "description_path", "tags_path"):
        _validate_path_exists(manifest_path=path, payload=upload_assets, field=field, issues=issues, resolved_paths=resolved_paths)
        checked_upload_path_fields.add(field)
    for field in ("caption_srt_path", "suggested_cover_frame_path", "metadata_path", "upload_checklist_path"):
        if str(upload_assets.get(field, "")).strip():
            _validate_path_exists(manifest_path=path, payload=upload_assets, field=field, issues=issues, resolved_paths=resolved_paths)
            checked_upload_path_fields.add(field)
    for field in _path_fields(upload_assets):
        if field not in checked_upload_path_fields:
            _validate_path_exists(manifest_path=path, payload=upload_assets, field=field, issues=issues, resolved_paths=resolved_paths)
    _validate_path_exists(manifest_path=path, payload=source_final, field="path", issues=issues, resolved_paths=resolved_paths)
    for field in _path_fields(source_final):
        _validate_path_exists(manifest_path=path, payload=source_final, field=field, issues=issues, resolved_paths=resolved_paths)
    if str(youtube_metadata.get("description_path", "")).strip():
        _validate_path_exists(manifest_path=path, payload=youtube_metadata, field="description_path", issues=issues, resolved_paths=resolved_paths)

    for field in ("title_path", "description_path", "tags_path"):
        value = str(upload_assets.get(field, "")).strip()
        if value:
            text_path = _resolve_package_path(path, value)
            if text_path.exists() and not text_path.read_text(encoding="utf-8").strip():
                issues.append(f"`{field}` file is empty: {text_path}")

    _validate_sha_fields(manifest_path=path, payload=upload_assets, object_name="upload_assets", issues=issues)
    _validate_sha_fields(manifest_path=path, payload=source_final, object_name="source_final", issues=issues)
    _validate_shorts_caption_policy(
        manifest_path=path,
        payload=payload,
        issues=issues,
        resolved_paths=resolved_paths,
    )
    _validate_music_policy(payload, issues, warnings)

    video_path: Path | None = None
    if str(upload_assets.get("video_path", "")).strip():
        candidate = _resolve_package_path(path, upload_assets["video_path"])
        if candidate.exists():
            video_path = candidate
    probe: dict[str, Any] = {}
    if video_path is not None:
        try:
            probe = _probe_video(video_path)
            if probe.get("video_codec") != "h264":
                issues.append(f"Video codec must be h264, got `{probe.get('video_codec') or 'unset'}`.")
            if probe.get("audio_codec") != "aac":
                issues.append(f"Audio codec must be aac, got `{probe.get('audio_codec') or 'unset'}`.")
            if int(probe.get("height", 0) or 0) <= int(probe.get("width", 0) or 0):
                issues.append(f"Video must be vertical for YouTube Shorts, got {probe.get('width')}x{probe.get('height')}.")
            if float(probe.get("duration_seconds", 0) or 0) > YOUTUBE_SHORTS_MAX_DURATION_SECONDS:
                issues.append(
                    f"Video duration must be at most {YOUTUBE_SHORTS_MAX_DURATION_SECONDS:.0f}s for YouTube Shorts, got {probe.get('duration_seconds'):.3f}s."
                )
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as exc:
            issues.append(f"Could not probe video with ffprobe: {exc}")

    declared_container = str(technical_read.get("container", "")).strip()
    if declared_container and declared_container != "mp4":
        issues.append(f"`technical_read.container` must be `mp4`, got `{declared_container}`.")
    if str(rights_and_claims.get("claim_risk", "")).strip():
        warnings.append(str(rights_and_claims["claim_risk"]).strip())

    return {
        "ok": not issues,
        "manifest_path": str(path),
        "target": target,
        "issues": issues,
        "warnings": warnings,
        "resolved_paths": resolved_paths,
        "probe": probe,
    }


def _parse_iso8601(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_target(target: str) -> str:
    normalized = str(target or "all").strip().lower() or "all"
    if normalized == "all":
        return normalized
    if normalized not in PUBLISH_TARGETS:
        raise PublishValidationError(f"Unknown publish target: {target}")
    return normalized


def _selected_targets(target: str) -> list[str]:
    normalized = _normalize_target(target)
    return list(PUBLISH_TARGETS) if normalized == "all" else [normalized]


def _markdown_to_plain_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"^\s{0,3}#{1,6}\s*", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", normalized)
    normalized = re.sub(r"[*_`]+", "", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _default_tags(manifest: dict[str, Any]) -> list[str]:
    candidates = [
        "Cascade Effects",
        str(manifest.get("title", "")).strip(),
        str(manifest.get("pillar", "")).strip().replace("-", " ").title(),
        str(manifest.get("id", "")).strip(),
        "documentary",
        "history",
    ]
    tags: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = candidate.strip()
        if not value or value.lower() in seen:
            continue
        seen.add(value.lower())
        tags.append(value)
    return tags


def _publish_state_path(context: Context, episode_id: str) -> Path:
    return context.root / "state" / "publish" / f"{episode_id}.json"


def load_publish_state(context: Context, episode_id: str) -> dict[str, Any]:
    path = _publish_state_path(context, episode_id)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_publish_state(context: Context, episode_id: str, payload: dict[str, Any]) -> Path:
    path = _publish_state_path(context, episode_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _youtube_thumbnail_path(manifest: dict[str, Any]) -> str:
    target = manifest.get("release", {}).get("youtube", {})
    thumbnail_item_id = str(target.get("thumbnail_item_id", "")).strip()
    packaging_items = list(manifest.get("packaging_stills", {}).get("items", []))
    item = None
    if thumbnail_item_id:
        item = next((candidate for candidate in packaging_items if str(candidate.get("id", "")).strip() == thumbnail_item_id), None)
    if item is None:
        item = next(
            (
                candidate
                for candidate in packaging_items
                if str(candidate.get("kind", "")).strip() == "thumbnail" and bool(candidate.get("required", True))
            ),
            None,
        )
    if item is None:
        return ""
    for field in ("selected_asset", "output_path"):
        candidate = str(item.get(field, "")).strip()
        if candidate:
            return candidate
    return ""


def _notes_payload(path: Path) -> tuple[str, str]:
    if not path.exists():
        return ("", "")
    text = path.read_text(encoding="utf-8")
    plain = _markdown_to_plain_text(text)
    return (plain, _sha256_text(text))


def _packaging_item(manifest: dict[str, Any], item_id: str) -> dict[str, Any] | None:
    normalized = str(item_id).strip()
    if not normalized:
        return None
    for item in manifest.get("packaging_stills", {}).get("items", []):
        if str(item.get("id", "")).strip() == normalized:
            return item
    return None


def build_publish_bundle(context: Context, manifest: dict[str, Any], *, target: str = "all") -> dict[str, Any]:
    materialized = materialize_episode_manifest(context, manifest)
    release = materialized.get("release", {})
    notes_path = Path(str(release.get("notes_path", "")).strip() or str(default_publish_notes_path(context, materialized)))
    notes_text, notes_sha256 = _notes_payload(notes_path)
    requested_targets = _selected_targets(target)
    state = derive_episode_state(materialized, context)
    bundle: dict[str, Any] = {
        "episode_id": str(materialized.get("id", "")).strip(),
        "title": str(materialized.get("title", "")).strip(),
        "summary": str(materialized.get("summary", "")).strip(),
        "label": str(materialized.get("label", "")).strip(),
        "requested_target": _normalize_target(target),
        "publish_notes_path": str(notes_path),
        "publish_notes_exists": notes_path.exists(),
        "publish_notes_text": notes_text,
        "publish_notes_sha256": notes_sha256,
        "release_scheduled_for": str(release.get("scheduled_for", "")).strip(),
        "state": state,
        "targets": {},
        "manifest": materialized,
    }

    if "youtube" in requested_targets:
        youtube = release.get("youtube", {})
        description_path = Path(str(youtube.get("description_path", "")).strip() or str(notes_path))
        description_text, description_sha256 = _notes_payload(description_path)
        target_payload = {
            "status": str(youtube.get("status", "todo")).strip() or "todo",
            "title": str(youtube.get("title", bundle["title"])).strip() or bundle["title"],
            "description_path": str(description_path),
            "description_exists": description_path.exists(),
            "description_text": description_text,
            "description_sha256": description_sha256,
            "tags": list(youtube.get("tags") or _default_tags(materialized)),
            "privacy": str(youtube.get("privacy", "public")).strip() or "public",
            "thumbnail_item_id": str(youtube.get("thumbnail_item_id", "")).strip(),
            "thumbnail_path": _youtube_thumbnail_path(materialized),
            "video_path": str(materialized.get("assembly", {}).get("master_video_path", "")).strip(),
            "scheduled_for": str(youtube.get("scheduled_for", bundle["release_scheduled_for"])).strip() or bundle["release_scheduled_for"],
            "published_at": str(youtube.get("published_at", "")).strip(),
            "video_id": str(youtube.get("video_id", "")).strip(),
            "video_url": str(youtube.get("video_url", "")).strip(),
            "error": str(youtube.get("error", "")).strip(),
        }
        idempotency_source = json.dumps(
            {
                "episode_id": bundle["episode_id"],
                "target": "youtube",
                "video_path": target_payload["video_path"],
                "thumbnail_path": target_payload["thumbnail_path"],
                "title": target_payload["title"],
                "description_sha256": target_payload["description_sha256"],
                "scheduled_for": target_payload["scheduled_for"],
            },
            sort_keys=True,
        )
        target_payload["idempotency_key"] = _sha256_text(idempotency_source)
        bundle["targets"]["youtube"] = target_payload

    if "podcast" in requested_targets:
        podcast = release.get("podcast", {})
        description_path = Path(str(podcast.get("description_path", "")).strip() or str(notes_path))
        description_text, description_sha256 = _notes_payload(description_path)
        target_payload = {
            "status": str(podcast.get("status", "todo")).strip() or "todo",
            "title": str(podcast.get("title", bundle["title"])).strip() or bundle["title"],
            "description_path": str(description_path),
            "description_exists": description_path.exists(),
            "description_text": description_text,
            "description_sha256": description_sha256,
            "audio_path": str(podcast.get("audio_path", materialized.get("audio", {}).get("master_path", ""))).strip(),
            "scheduled_for": str(podcast.get("scheduled_for", bundle["release_scheduled_for"])).strip() or bundle["release_scheduled_for"],
            "published_at": str(podcast.get("published_at", "")).strip(),
            "external_id": str(podcast.get("external_id", "")).strip(),
            "episode_url": str(podcast.get("episode_url", "")).strip(),
            "error": str(podcast.get("error", "")).strip(),
            "artist": "Cascade Effects",
            "summary": bundle["summary"],
            "tags": _default_tags(materialized),
            "tags_csv": ", ".join(_default_tags(materialized)),
        }
        idempotency_source = json.dumps(
            {
                "episode_id": bundle["episode_id"],
                "target": "podcast",
                "audio_path": target_payload["audio_path"],
                "title": target_payload["title"],
                "description_sha256": target_payload["description_sha256"],
                "scheduled_for": target_payload["scheduled_for"],
            },
            sort_keys=True,
        )
        target_payload["idempotency_key"] = _sha256_text(idempotency_source)
        bundle["targets"]["podcast"] = target_payload

    return bundle


def validate_publish_bundle(context: Context, manifest: dict[str, Any], *, target: str = "all") -> dict[str, Any]:
    bundle = build_publish_bundle(context, manifest, target=target)
    state = bundle["state"]
    issues: list[str] = []
    scheduled_for = str(bundle.get("release_scheduled_for", "")).strip()
    if scheduled_for and _parse_iso8601(scheduled_for) is None:
        issues.append("release.scheduled_for must be a valid ISO 8601 timestamp.")
    if not bundle["publish_notes_exists"]:
        issues.append(f"Release publish notes are missing: {bundle['publish_notes_path']}")
    elif not str(bundle.get("publish_notes_text", "")).strip():
        issues.append(f"Release publish notes are empty: {bundle['publish_notes_path']}")
    for target_name in _selected_targets(target):
        payload = bundle["targets"][target_name]
        target_scheduled_for = str(payload.get("scheduled_for", "")).strip()
        if target_scheduled_for and _parse_iso8601(target_scheduled_for) is None:
            issues.append(f"{target_name} scheduled_for must be a valid ISO 8601 timestamp.")
        if not payload["description_exists"]:
            issues.append(f"{target_name} description file is missing: {payload['description_path']}")
        elif not str(payload.get("description_text", "")).strip():
            issues.append(f"{target_name} description file is empty: {payload['description_path']}")
        if target_name == "youtube":
            try:
                _reject_banned_youtube_video_title_suffix(str(payload.get("title", "")))
            except PublishValidationError as exc:
                issues.append(str(exc))
            if state["lanes"]["assembly"]["status"] != "done":
                issues.append("YouTube publish requires assembly to be done.")
            if state["lanes"]["web"]["status"] != "done":
                issues.append("YouTube publish requires the web lane to be done.")
            thumbnail_item = _packaging_item(bundle["manifest"], payload.get("thumbnail_item_id", ""))
            if thumbnail_item is None:
                issues.append("YouTube publish requires a resolved release.youtube.thumbnail_item_id packaging item.")
            elif str(thumbnail_item.get("review_status", "")).strip() != "approved":
                issues.append("YouTube publish requires an approved thumbnail asset.")
            if not path_exists(payload.get("video_path")):
                issues.append(f"YouTube master video is missing: {payload['video_path'] or 'unset'}")
            if not path_exists(payload.get("thumbnail_path")):
                issues.append(f"YouTube thumbnail asset is missing: {payload['thumbnail_path'] or 'unset'}")
            privacy = str(payload.get("privacy", "")).strip()
            if privacy not in YOUTUBE_PRIVACY_VALUES:
                issues.append(f"YouTube privacy must be one of {', '.join(sorted(YOUTUBE_PRIVACY_VALUES))}.")
            if (
                target_scheduled_for
                and _parse_iso8601(target_scheduled_for)
                and _parse_iso8601(target_scheduled_for) > datetime.now(timezone.utc).replace(microsecond=0)
                and privacy != "public"
            ):
                issues.append("Scheduled YouTube publishing currently requires release.youtube.privacy = \"public\".")
        elif target_name == "podcast":
            if state["lanes"]["audio"]["status"] != "done":
                issues.append("Podcast publish requires the audio lane to be done.")
            if state["lanes"]["web"]["status"] != "done":
                issues.append("Podcast publish requires the web lane to be done.")
            if str(state["lanes"]["audio"].get("freshness", "")).strip() != "current":
                issues.append("Podcast publish requires the approved audio package to be current.")
            if str(state["lanes"]["audio"].get("package_sync_status", "")).strip() != "current":
                issues.append("Podcast publish requires the promoted audio package to match the latest packaged WAV and QA transcript.")
            if not path_exists(payload.get("audio_path")):
                issues.append(f"Podcast audio asset is missing: {payload['audio_path'] or 'unset'}")
    return {"ok": not issues, "issues": issues, "bundle": bundle}


def _missing_env_vars(required: tuple[str, ...], env: dict[str, str] | None = None) -> list[str]:
    environment = env or os.environ
    return [name for name in required if not str(environment.get(name, "")).strip()]


def build_youtube_publisher_from_env(env: dict[str, str] | None = None) -> YouTubePublisher:
    environment = env or os.environ
    missing = _missing_env_vars(YOUTUBE_ENV_VARS, environment)
    if missing:
        raise PublishValidationError("Missing YouTube credentials: " + ", ".join(missing))
    return YouTubePublisher(
        client_id=str(environment["YOUTUBE_CLIENT_ID"]).strip(),
        client_secret=str(environment["YOUTUBE_CLIENT_SECRET"]).strip(),
        refresh_token=str(environment["YOUTUBE_REFRESH_TOKEN"]).strip(),
        channel_id=str(environment["YOUTUBE_CHANNEL_ID"]).strip(),
    )


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PublishValidationError(f"Missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PublishValidationError(f"Invalid JSON file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PublishValidationError(f"JSON file must contain an object: {path}")
    return payload


def _oauth_client_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("installed", "web"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return payload


def _local_youtube_channel_id(config_dir: Path) -> str:
    for path in (config_dir / "channel_id.txt", config_dir / "channel.txt"):
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    channel_json = config_dir / "channel.json"
    if channel_json.exists():
        payload = _load_json_file(channel_json)
        return str(payload.get("channel_id", payload.get("id", ""))).strip()
    return ""


def build_youtube_package_publisher(
    *,
    env: dict[str, str] | None = None,
    config_dir: str | Path | None = None,
) -> YouTubePublisher:
    environment = env or os.environ
    if not _missing_env_vars(YOUTUBE_PACKAGE_ENV_VARS, environment):
        return YouTubePublisher(
            client_id=str(environment["YOUTUBE_CLIENT_ID"]).strip(),
            client_secret=str(environment["YOUTUBE_CLIENT_SECRET"]).strip(),
            refresh_token=str(environment["YOUTUBE_REFRESH_TOKEN"]).strip(),
            channel_id=str(environment.get("YOUTUBE_CHANNEL_ID", "")).strip(),
        )

    local_dir = Path(config_dir or YOUTUBE_LOCAL_CONFIG_DIR).expanduser()
    client_payload = _oauth_client_payload(_load_json_file(local_dir / "oauth_client_secret.json"))
    token_payload = _load_json_file(local_dir / "access_token.json")
    client_id = str(client_payload.get("client_id", "")).strip()
    client_secret = str(client_payload.get("client_secret", "")).strip()
    refresh_token = str(token_payload.get("refresh_token", "")).strip()
    missing = [
        name
        for name, value in (
            ("client_id", client_id),
            ("client_secret", client_secret),
            ("refresh_token", refresh_token),
        )
        if not value
    ]
    if missing:
        raise PublishValidationError(f"Local YouTube OAuth config is missing: {', '.join(missing)}")
    return YouTubePublisher(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        channel_id=str(environment.get("YOUTUBE_CHANNEL_ID", "")).strip() or _local_youtube_channel_id(local_dir),
    )


def _read_package_manifest(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path).expanduser()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PublishValidationError(f"Publish package manifest is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PublishValidationError(f"Publish package manifest JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise PublishValidationError("Publish package manifest must contain a JSON object.")
    return payload


def _read_manifest_text(manifest_path: Path, value: Any) -> str:
    path = _resolve_package_path(manifest_path, value)
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise PublishValidationError(f"Declared metadata file is missing: {path}") from exc


def _read_youtube_tags(manifest_path: Path, upload_assets: dict[str, Any], youtube_metadata: dict[str, Any]) -> list[str]:
    raw_tags = youtube_metadata.get("tags")
    if isinstance(raw_tags, list):
        candidates = [str(value).strip() for value in raw_tags]
    elif str(raw_tags or "").strip():
        candidates = [part.strip() for part in re.split(r"[\n,]+", str(raw_tags))]
    elif str(upload_assets.get("tags_path", "")).strip():
        candidates = [part.strip() for part in re.split(r"[\n,]+", _read_manifest_text(manifest_path, upload_assets["tags_path"]))]
    else:
        candidates = []
    tags: list[str] = []
    seen: set[str] = set()
    for tag in candidates:
        if not tag or tag.lower() in seen:
            continue
        tags.append(tag)
        seen.add(tag.lower())
    return tags


def build_youtube_shorts_publish_payload(manifest_path: str | Path, *, privacy: str = "unlisted") -> dict[str, Any]:
    manifest_file = Path(manifest_path).expanduser()
    package = _read_package_manifest(manifest_file)
    target = str(package.get("target", "")).strip()
    if target != "youtube_shorts":
        raise PublishValidationError(f"Unsupported publish package target `{target or 'unset'}`.")
    requested_privacy = str(privacy or "").strip() or "unlisted"
    if requested_privacy != "unlisted":
        raise PublishValidationError("Package upload v1 supports unlisted review uploads only; use --privacy unlisted.")

    upload_assets = package.get("upload_assets", {}) if isinstance(package.get("upload_assets"), dict) else {}
    youtube_metadata = package.get("youtube_metadata", {}) if isinstance(package.get("youtube_metadata"), dict) else {}
    video_path = _resolve_package_path(manifest_file, upload_assets.get("video_path", ""))
    title = _first_nonempty(
        youtube_metadata.get("title"),
        _read_manifest_text(manifest_file, upload_assets["title_path"]) if str(upload_assets.get("title_path", "")).strip() else "",
    )
    description_text = _first_nonempty(
        youtube_metadata.get("description"),
        youtube_metadata.get("description_text"),
        _read_manifest_text(manifest_file, youtube_metadata["description_path"]) if str(youtube_metadata.get("description_path", "")).strip() else "",
        _read_manifest_text(manifest_file, upload_assets["description_path"]) if str(upload_assets.get("description_path", "")).strip() else "",
    )
    if not title:
        raise PublishValidationError("YouTube Shorts publish payload is missing a title.")
    _reject_banned_youtube_video_title_suffix(title)
    if not description_text:
        raise PublishValidationError("YouTube Shorts publish payload is missing a description.")
    category_id = str(youtube_metadata.get("category_id", youtube_metadata.get("categoryId", "27"))).strip() or "27"
    audience = str(youtube_metadata.get("audience", "")).strip().lower()
    return {
        "manifest_path": str(manifest_file),
        "video_path": str(video_path),
        "title": title,
        "description_text": description_text,
        "tags": _read_youtube_tags(manifest_file, upload_assets, youtube_metadata),
        "privacy": "unlisted",
        "scheduled_for": "",
        "thumbnail_path": str(_resolve_package_path(manifest_file, upload_assets.get("suggested_cover_frame_path", "")))
        if str(upload_assets.get("suggested_cover_frame_path", "")).strip()
        else "",
        "category_id": category_id,
        "default_language": str(youtube_metadata.get("default_language", "en")).strip() or "en",
        "default_audio_language": str(youtube_metadata.get("default_audio_language", "en")).strip() or "en",
        "self_declared_made_for_kids": audience in {"made_for_kids", "kids", "true", "yes"},
        "embeddable": True,
        "notify_subscribers": False,
        "ignore_thumbnail_errors": True,
        "caption_srt_path": str(_resolve_package_path(manifest_file, upload_assets.get("caption_srt_path", "")))
        if str(upload_assets.get("caption_srt_path", "")).strip()
        else "",
    }


def _receipt_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _get_mapping_or_attr(value: Any, key: str, default: Any = "") -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _video_status_payload(status: Any) -> dict[str, Any]:
    return {
        "video_id": str(_get_mapping_or_attr(status, "video_id", "")).strip(),
        "exists": bool(_get_mapping_or_attr(status, "exists", False)),
        "video_url": str(_get_mapping_or_attr(status, "video_url", "")).strip(),
        "channel_id": str(_get_mapping_or_attr(status, "channel_id", "")).strip(),
        "channel_title": str(_get_mapping_or_attr(status, "channel_title", "")).strip(),
        "title": str(_get_mapping_or_attr(status, "title", "")).strip(),
        "privacy_status": str(_get_mapping_or_attr(status, "privacy_status", "")).strip(),
        "upload_status": str(_get_mapping_or_attr(status, "upload_status", "")).strip(),
        "processing_status": str(_get_mapping_or_attr(status, "processing_status", "")).strip(),
        "published_at": str(_get_mapping_or_attr(status, "published_at", "")).strip(),
        "embeddable": bool(_get_mapping_or_attr(status, "embeddable", False)),
        "raw_response": _get_mapping_or_attr(status, "raw_response", {}),
    }


def _post_upload_blockers(validation: dict[str, Any]) -> list[str]:
    blockers = [
        "Review YouTube Studio copyright and Content ID checks before public release.",
        "Confirm altered-content disclosure in YouTube Studio; answer Yes for realistic generated or source-derived event visuals.",
        "Review or remove uploaded/automatic captions if they duplicate burned-in captions.",
        "Verify the Shorts cover frame in Studio or mobile Studio; API thumbnail setting can fail or be ignored.",
        "Public visibility change remains manual and must not be performed by package upload v1.",
    ]
    for warning in validation.get("warnings", []):
        text = str(warning).strip()
        if text and text not in blockers:
            blockers.append(text)
    return blockers


def _write_json_receipt(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _channel_id(channel: dict[str, Any]) -> str:
    return str(channel.get("channel_id", channel.get("id", ""))).strip()


def _reject_banned_youtube_video_title_suffix(title: str) -> None:
    if YOUTUBE_VIDEO_TITLE_BANNED_SUFFIX in str(title or ""):
        raise PublishValidationError("YouTube video titles must not append `| Cascade Effects`.")


def _verify_authenticated_channel(publisher: Any) -> dict[str, Any]:
    channel = publisher.get_authenticated_channel()
    if not isinstance(channel, dict):
        raise PublishValidationError("YouTube channel verification returned an unexpected response.")
    authenticated_channel_id = _channel_id(channel)
    expected_channel_id = str(getattr(publisher, "channel_id", "")).strip()
    if expected_channel_id and authenticated_channel_id != expected_channel_id:
        raise PublishValidationError(
            f"YouTube credentials are authenticated for `{authenticated_channel_id}`, expected `{expected_channel_id}`."
        )
    return channel


def publish_package_upload(
    manifest_path: str | Path,
    *,
    privacy: str = "unlisted",
    publisher: Any | None = None,
    env: dict[str, str] | None = None,
    config_dir: str | Path | None = None,
) -> dict[str, Any]:
    validation = validate_publish_package_manifest(manifest_path)
    if not validation["ok"]:
        raise PublishValidationError("\n".join(validation["issues"]))
    payload = build_youtube_shorts_publish_payload(manifest_path, privacy=privacy)
    youtube = publisher or build_youtube_package_publisher(env=env, config_dir=config_dir)
    channel = _verify_authenticated_channel(youtube)
    result = youtube.publish_video(payload)
    status = youtube.get_video_status(result.video_id)
    status_payload = _video_status_payload(status)
    manifest_file = Path(manifest_path).expanduser()
    receipt_path = manifest_file.parent / f"youtube_review_upload_receipt_{_receipt_timestamp()}.json"
    receipt = {
        "receipt_type": "youtube_review_upload",
        "created_at": utc_now_iso(),
        "manifest_path": str(manifest_file),
        "package_dir": str(manifest_file.parent),
        "privacy": "unlisted",
        "youtube": {
            "video_id": result.video_id,
            "video_url": result.video_url,
            "channel_id": _channel_id(channel),
            "channel_title": str(channel.get("title", channel.get("channel_title", ""))).strip(),
            "published_at": result.published_at,
            "status": status_payload,
        },
        "thumbnail": {
            "path": str(payload.get("thumbnail_path", "")).strip(),
            "status": result.thumbnail_status,
            "error": result.thumbnail_error,
        },
        "validation": {
            "warnings": validation.get("warnings", []),
            "probe": validation.get("probe", {}),
        },
        "post_upload_blockers": _post_upload_blockers(validation),
        "captions_uploaded": False,
        "public_release": "manual_youtube_studio_only",
    }
    _write_json_receipt(receipt_path, receipt)
    return {
        "ok": True,
        "manifest_path": str(manifest_file),
        "receipt_path": str(receipt_path),
        "video_id": result.video_id,
        "video_url": result.video_url,
        "channel_id": _channel_id(channel),
        "privacy": "unlisted",
        "processing_status": status_payload.get("processing_status", ""),
        "upload_status": status_payload.get("upload_status", ""),
        "thumbnail_status": result.thumbnail_status,
        "warnings": validation.get("warnings", []),
        "post_upload_blockers": receipt["post_upload_blockers"],
    }


def _video_id_from_reference(reference: str | Path) -> tuple[str, Path | None]:
    raw = str(reference or "").strip()
    if not raw:
        raise PublishValidationError("A receipt path, YouTube URL, or video id is required.")
    path = Path(raw).expanduser()
    if path.exists():
        payload = _load_json_file(path)
        youtube = payload.get("youtube", {}) if isinstance(payload.get("youtube"), dict) else {}
        youtube_unlisted = payload.get("youtube_unlisted_review_upload", {}) if isinstance(payload.get("youtube_unlisted_review_upload"), dict) else {}
        youtube_private = payload.get("youtube_private_review_upload", {}) if isinstance(payload.get("youtube_private_review_upload"), dict) else {}
        video_id = _first_nonempty(
            youtube.get("video_id"),
            youtube_unlisted.get("video_id"),
            youtube_private.get("video_id"),
            payload.get("video_id"),
            payload.get("deleted_video_id"),
        )
        if not video_id:
            raise PublishValidationError(f"Receipt does not contain a video id: {path}")
        return video_id, path
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{6,})", raw)
    if match:
        return match.group(1), None
    return raw, None


def publish_package_update_title(
    receipt_or_video_id: str | Path,
    *,
    title: str,
    publisher: Any | None = None,
    env: dict[str, str] | None = None,
    config_dir: str | Path | None = None,
) -> dict[str, Any]:
    new_title = str(title or "").strip()
    if not new_title:
        raise PublishValidationError("YouTube title update requires a non-empty title.")
    _reject_banned_youtube_video_title_suffix(new_title)
    video_id, receipt_path = _video_id_from_reference(receipt_or_video_id)
    youtube = publisher or build_youtube_package_publisher(env=env, config_dir=config_dir)
    channel = _verify_authenticated_channel(youtube)
    expected_channel_id = _channel_id(channel)
    before_status = _video_status_payload(youtube.get_video_status(video_id))
    if not before_status["exists"]:
        raise PublishValidationError(f"Video `{video_id}` was not found.")
    if expected_channel_id and before_status["channel_id"] and before_status["channel_id"] != expected_channel_id:
        raise PublishValidationError(f"Video `{video_id}` belongs to channel `{before_status['channel_id']}`, not `{expected_channel_id}`.")
    result = youtube.update_video_title(video_id, new_title)
    after_status = _video_status_payload(youtube.get_video_status(video_id))
    if after_status["exists"] and expected_channel_id and after_status["channel_id"] and after_status["channel_id"] != expected_channel_id:
        raise PublishValidationError(f"Updated video `{video_id}` belongs to channel `{after_status['channel_id']}`, not `{expected_channel_id}`.")
    if after_status["title"] != new_title:
        raise PublishValidationError(f"YouTube title update did not stick for `{video_id}`; saw `{after_status['title']}`.")
    receipt_dir = receipt_path.parent if receipt_path else Path.cwd()
    title_receipt_path = receipt_dir / f"youtube_title_update_receipt_{_receipt_timestamp()}.json"
    receipt = {
        "receipt_type": "youtube_title_update",
        "created_at": utc_now_iso(),
        "source_reference": str(receipt_path) if receipt_path else str(receipt_or_video_id),
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "channel_id": expected_channel_id,
        "channel_title": str(channel.get("title", channel.get("channel_title", ""))).strip(),
        "old_title": before_status["title"],
        "new_title": new_title,
        "privacy_preserved": before_status["privacy_status"] == after_status["privacy_status"],
        "public_release": "manual_youtube_studio_only",
        "verification": {
            "before": before_status,
            "after": after_status,
        },
        "raw_update_response": _get_mapping_or_attr(result, "raw_response", {}),
        "updated_at": str(_get_mapping_or_attr(result, "updated_at", "")).strip(),
    }
    _write_json_receipt(title_receipt_path, receipt)
    return {
        "ok": True,
        "video_id": video_id,
        "video_url": receipt["video_url"],
        "receipt_path": str(title_receipt_path),
        "old_title": before_status["title"],
        "new_title": new_title,
        "channel_id": expected_channel_id,
        "privacy_status": after_status["privacy_status"],
        "upload_status": after_status["upload_status"],
        "processing_status": after_status["processing_status"],
        "privacy_preserved": receipt["privacy_preserved"],
    }


def publish_package_status(
    receipt_or_video_id: str | Path,
    *,
    publisher: Any | None = None,
    env: dict[str, str] | None = None,
    config_dir: str | Path | None = None,
) -> dict[str, Any]:
    video_id, receipt_path = _video_id_from_reference(receipt_or_video_id)
    youtube = publisher or build_youtube_package_publisher(env=env, config_dir=config_dir)
    channel = _verify_authenticated_channel(youtube)
    status = _video_status_payload(youtube.get_video_status(video_id))
    expected_channel_id = _channel_id(channel)
    if status["exists"] and expected_channel_id and status["channel_id"] and status["channel_id"] != expected_channel_id:
        raise PublishValidationError(f"Video `{video_id}` belongs to channel `{status['channel_id']}`, not `{expected_channel_id}`.")
    return {
        "ok": True,
        "video_id": video_id,
        "receipt_path": str(receipt_path) if receipt_path else "",
        "channel_id": expected_channel_id,
        "status": status,
    }


def publish_package_delete(
    receipt_or_video_id: str | Path,
    *,
    confirm_video_id: str,
    publisher: Any | None = None,
    env: dict[str, str] | None = None,
    config_dir: str | Path | None = None,
) -> dict[str, Any]:
    video_id, receipt_path = _video_id_from_reference(receipt_or_video_id)
    confirmation = str(confirm_video_id or "").strip()
    if confirmation != video_id:
        raise PublishValidationError(f"Delete confirmation must exactly match `{video_id}`.")
    youtube = publisher or build_youtube_package_publisher(env=env, config_dir=config_dir)
    channel = _verify_authenticated_channel(youtube)
    before_status = _video_status_payload(youtube.get_video_status(video_id))
    if before_status["exists"] and _channel_id(channel) and before_status["channel_id"] and before_status["channel_id"] != _channel_id(channel):
        raise PublishValidationError(f"Video `{video_id}` belongs to channel `{before_status['channel_id']}`, not `{_channel_id(channel)}`.")
    delete_result = youtube.delete_video(video_id)
    after_status = _video_status_payload(youtube.get_video_status(video_id))
    receipt_dir = receipt_path.parent if receipt_path else Path.cwd()
    delete_receipt_path = receipt_dir / f"youtube_delete_receipt_{_receipt_timestamp()}.json"
    receipt = {
        "receipt_type": "youtube_delete",
        "created_at": utc_now_iso(),
        "confirmation_text": confirmation,
        "deleted_video_id": video_id,
        "channel_id": _channel_id(channel),
        "source_receipt_path": str(receipt_path) if receipt_path else "",
        "local_package_paths_retained": True,
        "delete_result": {
            "deleted_at": str(_get_mapping_or_attr(delete_result, "deleted_at", "")).strip(),
            "raw_response": _get_mapping_or_attr(delete_result, "raw_response", {}),
        },
        "verification": {
            "exists_before_delete": before_status["exists"],
            "exists_after_delete": after_status["exists"],
            "before": before_status,
            "after": after_status,
        },
    }
    _write_json_receipt(delete_receipt_path, receipt)
    return {
        "ok": True,
        "video_id": video_id,
        "receipt_path": str(delete_receipt_path),
        "deleted": not after_status["exists"],
        "verification": receipt["verification"],
    }


def build_buzzsprout_publisher_from_env(env: dict[str, str] | None = None) -> BuzzsproutPublisher:
    environment = env or os.environ
    missing = _missing_env_vars(BUZZSPROUT_ENV_VARS, environment)
    if missing:
        raise PublishValidationError("Missing Buzzsprout credentials: " + ", ".join(missing))
    return BuzzsproutPublisher(
        api_token=str(environment["BUZZSPROUT_API_TOKEN"]).strip(),
        podcast_id=str(environment["BUZZSPROUT_PODCAST_ID"]).strip(),
    )


def validate_publish_credentials(
    *,
    target: str = "all",
    youtube_publisher: YouTubePublisher | None = None,
    buzzsprout_publisher: BuzzsproutPublisher | None = None,
) -> dict[str, Any]:
    validations: dict[str, Any] = {}
    for target_name in _selected_targets(target):
        if target_name == "youtube":
            publisher = youtube_publisher or build_youtube_publisher_from_env()
            validations["youtube"] = publisher.validate_credentials()
        elif target_name == "podcast":
            publisher = buzzsprout_publisher or build_buzzsprout_publisher_from_env()
            validations["podcast"] = publisher.validate_credentials()
    return validations


def _state_payload_for_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "episode_id": bundle["episode_id"],
        "prepared_at": utc_now_iso(),
        "requested_target": bundle["requested_target"],
        "publish_notes_path": bundle["publish_notes_path"],
        "publish_notes_exists": bundle["publish_notes_exists"],
        "publish_notes_sha256": bundle["publish_notes_sha256"],
        "release_scheduled_for": bundle["release_scheduled_for"],
        "targets": copy.deepcopy(bundle["targets"]),
    }


def prepare_publish(context: Context, manifest: dict[str, Any], *, target: str = "all") -> dict[str, Any]:
    validation = validate_publish_bundle(context, manifest, target=target)
    if validation["issues"]:
        raise PublishValidationError("\n".join(validation["issues"]))
    bundle = validation["bundle"]
    episode_id = bundle["episode_id"]
    publish_state = load_publish_state(context, episode_id)
    prepared_state = _state_payload_for_bundle(bundle)
    for key, value in prepared_state.items():
        if key == "targets":
            continue
        publish_state[key] = value
    publish_targets = publish_state.setdefault("targets", {})
    for target_name, target_payload in prepared_state["targets"].items():
        existing = publish_targets.setdefault(target_name, {})
        existing.update(target_payload)
    state_path = write_publish_state(context, episode_id, publish_state)
    return {
        "bundle": bundle,
        "manifest": bundle["manifest"],
        "publish_state": publish_state,
        "state_path": str(state_path),
    }


def build_publish_status(context: Context, manifest: dict[str, Any]) -> dict[str, Any]:
    materialized = materialize_episode_manifest(context, manifest)
    episode_id = str(materialized.get("id", "")).strip()
    state_path = _publish_state_path(context, episode_id)
    return {
        "episode_id": episode_id,
        "release": materialized.get("release", {}),
        "publish_state_path": str(state_path),
        "publish_state_exists": state_path.exists(),
        "publish_state": load_publish_state(context, episode_id),
    }


def _update_release_completion(manifest: dict[str, Any]) -> None:
    release = manifest.setdefault("release", {})
    youtube = release.setdefault("youtube", {})
    podcast = release.setdefault("podcast", {})
    youtube_status = str(youtube.get("status", "todo")).strip() or "todo"
    podcast_status = str(podcast.get("status", "todo")).strip() or "todo"
    successful_statuses = {"scheduled", "published"}
    if youtube_status == "published" and podcast_status == "published":
        timestamps = [
            value
            for value in (str(youtube.get("published_at", "")).strip(), str(podcast.get("published_at", "")).strip())
            if value
        ]
        release["published_at"] = max(timestamps) if timestamps else utc_now_iso()
    else:
        release["published_at"] = ""
    if youtube_status in successful_statuses and podcast_status in successful_statuses:
        release["status"] = "done"
    elif any(status in successful_statuses.union({"failed"}) for status in (youtube_status, podcast_status)):
        release["status"] = "in_progress"
    else:
        release["status"] = "todo"


def publish_episode(
    context: Context,
    manifest: dict[str, Any],
    *,
    target: str = "all",
    dry_run: bool = False,
    youtube_publisher: YouTubePublisher | None = None,
    buzzsprout_publisher: BuzzsproutPublisher | None = None,
) -> dict[str, Any]:
    prepared = prepare_publish(context, manifest, target=target)
    bundle = prepared["bundle"]
    materialized = prepared["manifest"]
    publish_state = prepared["publish_state"]
    validations: dict[str, Any] = {}
    if not dry_run:
        validations = validate_publish_credentials(
            target=target,
            youtube_publisher=youtube_publisher,
            buzzsprout_publisher=buzzsprout_publisher,
        )
    results: dict[str, Any] = {}
    if dry_run:
        return {
            "episode_id": bundle["episode_id"],
            "dry_run": True,
            "results": results,
            "validations": validations,
            "state_path": prepared["state_path"],
            "bundle": _state_payload_for_bundle(bundle),
        }

    release = materialized.setdefault("release", {})
    publish_state.setdefault("targets", {})
    for target_name in _selected_targets(target):
        payload = bundle["targets"][target_name]
        target_state = release.setdefault(target_name, {})
        state_target = publish_state["targets"].setdefault(target_name, copy.deepcopy(payload))
        result_payload: dict[str, Any]
        if target_name == "youtube":
            if str(target_state.get("status", "")).strip() in {"scheduled", "published"} and str(target_state.get("video_id", "")).strip():
                result_payload = {
                    "status": str(target_state.get("status", "")).strip(),
                    "skipped": True,
                    "video_id": str(target_state.get("video_id", "")).strip(),
                    "video_url": str(target_state.get("video_url", "")).strip(),
                }
            else:
                publisher = youtube_publisher or build_youtube_publisher_from_env()
                try:
                    result = publisher.publish_video(payload)
                    target_state["status"] = "scheduled" if result.scheduled_for else "published"
                    target_state["video_id"] = result.video_id
                    target_state["video_url"] = result.video_url
                    target_state["scheduled_for"] = result.scheduled_for
                    target_state["published_at"] = result.published_at
                    target_state["error"] = ""
                    result_payload = {
                        "status": target_state["status"],
                        "video_id": result.video_id,
                        "video_url": result.video_url,
                        "scheduled_for": result.scheduled_for,
                        "published_at": result.published_at,
                    }
                except Exception as exc:
                    target_state["status"] = "failed"
                    target_state["error"] = str(exc)
                    result_payload = {"status": "failed", "error": str(exc)}
        else:
            if str(target_state.get("status", "")).strip() in {"scheduled", "published"} and str(target_state.get("external_id", "")).strip():
                result_payload = {
                    "status": str(target_state.get("status", "")).strip(),
                    "skipped": True,
                    "external_id": str(target_state.get("external_id", "")).strip(),
                    "episode_url": str(target_state.get("episode_url", "")).strip(),
                }
            else:
                publisher = buzzsprout_publisher or build_buzzsprout_publisher_from_env()
                try:
                    result = publisher.publish_episode(payload)
                    target_state["status"] = "scheduled" if result.scheduled_for else "published"
                    target_state["external_id"] = result.external_id
                    target_state["episode_url"] = result.episode_url
                    target_state["scheduled_for"] = result.scheduled_for
                    target_state["published_at"] = result.published_at
                    target_state["error"] = ""
                    result_payload = {
                        "status": target_state["status"],
                        "external_id": result.external_id,
                        "episode_url": result.episode_url,
                        "scheduled_for": result.scheduled_for,
                        "published_at": result.published_at,
                    }
                except Exception as exc:
                    target_state["status"] = "failed"
                    target_state["error"] = str(exc)
                    result_payload = {"status": "failed", "error": str(exc)}
        state_target["status"] = str(target_state.get("status", payload.get("status", "todo"))).strip() or "todo"
        state_target["scheduled_for"] = str(target_state.get("scheduled_for", payload.get("scheduled_for", ""))).strip()
        state_target["published_at"] = str(target_state.get("published_at", payload.get("published_at", ""))).strip()
        state_target["error"] = str(target_state.get("error", "")).strip()
        if target_name == "youtube":
            state_target["video_id"] = str(target_state.get("video_id", "")).strip()
            state_target["video_url"] = str(target_state.get("video_url", "")).strip()
        else:
            state_target["external_id"] = str(target_state.get("external_id", "")).strip()
            state_target["episode_url"] = str(target_state.get("episode_url", "")).strip()
        results[target_name] = result_payload

    _update_release_completion(materialized)
    manifest_path = Path(str(materialized["_manifest_path"]))
    write_episode_manifest(manifest_path, materialized)
    prepared_state = _state_payload_for_bundle(bundle)
    for key, value in prepared_state.items():
        if key == "targets":
            continue
        publish_state[key] = value
    publish_state["last_attempt_at"] = utc_now_iso()
    publish_state["last_validations"] = validations
    publish_state.setdefault("results", {}).update(results)
    state_path = write_publish_state(context, bundle["episode_id"], publish_state)
    return {
        "episode_id": bundle["episode_id"],
        "dry_run": False,
        "results": results,
        "validations": validations,
        "manifest_path": str(manifest_path),
        "state_path": str(state_path),
    }


def scaffold_publish_notes(context: Context, manifest: dict[str, Any]) -> Path:
    materialized = materialize_episode_manifest(context, manifest)
    notes_path = Path(str(materialized.get("release", {}).get("notes_path", "")).strip() or str(default_publish_notes_path(context, materialized)))
    if notes_path.exists():
        return notes_path
    title = str(materialized.get("title", "")).strip()
    summary = str(materialized.get("summary", "")).strip()
    template = "\n".join(
        [
            f"# {title}",
            "",
            "## Summary",
            summary or "TODO: add the one-paragraph episode summary used for public distribution.",
            "",
            "## Description",
            "TODO: add the long-form YouTube and podcast description.",
            "",
            "## Sources",
            "TODO: add source links or notes that should appear in the public description.",
            "",
        ]
    )
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(template, encoding="utf-8")
    return notes_path
