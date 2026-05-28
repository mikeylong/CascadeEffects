from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from orchestration.assembly import (
    ALLOWED_ASSEMBLY_RENDERERS,
    ALLOWED_ASSEMBLY_STRATEGIES,
    ALLOWED_AUDIO_TRANSITIONS,
    ALLOWED_VIDEO_TRANSITIONS,
    derive_act_spine,
)
from orchestration.io import (
    Context,
    audio_package_differs_from_manifest,
    audio_package_is_promotable,
    find_motion_archetype,
    list_episode_manifests,
    load_audio_package_metadata,
    materialize_episode_manifest,
    path_exists,
    path_or_none,
    table_status,
)
from orchestration.research_sources import (
    SOURCE_ORIGIN_POLICIES,
    display_asset_path,
    note_allows_duplicate_display,
)


@dataclass(frozen=True)
class LaneDefinition:
    name: str
    allowed_repo_keys: tuple[str, ...]


LANE_DEFINITIONS = (
    LaneDefinition("visual_research", ("episodes_root", "viz_root")),
    LaneDefinition("audio", ("episodes_root", "audio_root")),
    LaneDefinition("scene_stills", ("viz_root", "ai_root")),
    LaneDefinition("packaging_stills", ("viz_root", "ai_root")),
    LaneDefinition("motion_assets", ("viz_root", "ai_root")),
    LaneDefinition("assembly", ("episodes_root", "audio_root", "viz_root")),
    LaneDefinition("web", ("web_root",)),
    LaneDefinition("release", ("episodes_root", "audio_root", "viz_root", "web_root")),
    LaneDefinition("analytics", ("web_root",)),
)
LANE_STATUSES = {"todo", "in_progress", "review", "done", "blocked", "not_needed"}
RELEASE_LANE_STATUSES = LANE_STATUSES | {"manual_upload_ready"}
REVIEW_STATUSES = {"pending", "approved", "rejected", "blocked"}
AUDIO_REVIEW_STATUSES = {"pending", "approved", "rejected"}
AUDIO_FRESHNESS_OVERRIDES = {"", "waived"}
MOTION_REVIEW_STATUSES = {"not_planned", "pending", "approved_for_motion", "rejected", "blocked"}
MOTION_ITEM_STATUSES = {"todo", "in_progress", "review", "done", "blocked", "not_needed"}
MOTION_AUTHORING_MODES = {"legacy_i2v", "particle_workbench"}
SCENE_ARCHETYPE_STATUSES = {"resolved", "unresolved"}
VISUAL_RESEARCH_APPROVAL_STATUSES = {"pending", "approved", "rejected"}
OPENING_OBJECT_STRATEGIES = {"episode_specific_cluster", "generic_era_cluster"}
OPENING_OBJECT_SCOPES = {"generic_mass_market", "episode_specific"}
OPENING_SLOT_RENDERABILITIES = {"", "common_iconic"}
CANONICAL_OPENING_SCENE_ID = "opening_culture_cluster"
CANONICAL_OPENING_MOTION_ID = "opening_subject_pull_in"
PACKAGING_KIND_TO_FAMILY = {
    "thumbnail": "thumbnail_plate",
    "thumbnail_plate": "thumbnail_plate",
    "shorts_cover": "shorts_cover_plate",
    "shorts_cover_plate": "shorts_cover_plate",
}
ROLLING_HISTORY_WINDOW = 12
TREND_WINDOW_SIZE = 3
MIN_P50_SAMPLES = 3
MIN_P90_SAMPLES = 5
SLOWEST_IN_FLIGHT_LIMIT = 5
GENERIC_ERA_CONTEXT_TOKENS = (
    "room",
    "wide",
    "panorama",
    "interior",
    "exterior",
    "mission control",
    "control room",
    "firing room",
    "launch pad",
    "gantry",
    "tower",
    "facility",
    "operations",
    "site",
    "crowd",
    "people",
    "building",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalized_path_token(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return str(Path(raw).expanduser().resolve(strict=False))
    except OSError:
        return str(Path(raw).expanduser())


def _is_generated_episode_select_path(path_value: Any, episode_id: str) -> bool:
    token = _normalized_path_token(path_value)
    if not token:
        return False
    needle = f"/references/episodes/{str(episode_id).strip()}/"
    return needle in token and "/selects/" in token


def _looks_like_generic_era_context_imagery(*parts: Any) -> bool:
    haystack = " ".join(str(part or "").strip().lower() for part in parts if str(part or "").strip())
    if not haystack:
        return False
    return any(token in haystack for token in GENERIC_ERA_CONTEXT_TOKENS)


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


def _datetime_to_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _round_hours(delta_seconds: float) -> float:
    return round(delta_seconds / 3600, 2)


def _round_days(delta_seconds: float) -> float:
    return round(delta_seconds / 86400, 2)


def _duration_payload(start: datetime, end: datetime) -> dict[str, float] | None:
    delta_seconds = (end - start).total_seconds()
    if delta_seconds < 0:
        return None
    return {
        "hours": _round_hours(delta_seconds),
        "days": _round_days(delta_seconds),
    }


def _metric_payload(value: float | None, *, status: str, sample_count: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "sample_count": sample_count,
        "value": None,
    }
    if value is not None:
        payload["value"] = round(value, 2)
    return payload


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[midpoint])
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _percentile_nearest_rank(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile / 100) * len(ordered)))
    return float(ordered[rank - 1])


def _file_mtime_datetime(value: Any) -> datetime | None:
    path = path_or_none(value)
    if not path or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0)


def _build_review_log_index(context: Context, episode_id: str) -> dict[tuple[str, str], datetime]:
    path = context.root / "state" / "reviews" / f"{episode_id}.jsonl"
    if not path.exists():
        return {}
    latest: dict[tuple[str, str], datetime] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if str(payload.get("decision", "")).strip() != "approve":
            continue
        timestamp = _parse_iso8601(payload.get("timestamp"))
        if timestamp is None:
            continue
        key = (
            str(payload.get("gate_type", "")).strip(),
            str(payload.get("item_id", "")).strip(),
        )
        current = latest.get(key)
        if current is None or timestamp > current:
            latest[key] = timestamp
    return latest


def _milestone_payload(
    timestamp: datetime | None,
    *,
    source: str = "",
    confidence: str = "",
    derived_from: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "timestamp": _datetime_to_iso(timestamp) if timestamp else "",
        "source": source,
        "confidence": confidence,
    }
    if derived_from:
        payload["derived_from"] = sorted(set(item for item in derived_from if item))
    return payload


def _resolve_item_timestamp(
    *,
    explicit_value: Any,
    explicit_source: str,
    review_log_lookup: dict[tuple[str, str], datetime],
    review_log_key: tuple[str, str],
    fallback_path: Any,
    fallback_source: str,
) -> tuple[datetime | None, str, str]:
    explicit_timestamp = _parse_iso8601(explicit_value)
    if explicit_timestamp is not None:
        return explicit_timestamp, explicit_source, "explicit"
    logged_timestamp = review_log_lookup.get(review_log_key)
    if logged_timestamp is not None:
        return logged_timestamp, "review_log", "backfilled"
    fallback_timestamp = _file_mtime_datetime(fallback_path)
    if fallback_timestamp is not None:
        return fallback_timestamp, fallback_source, "backfilled"
    return None, "", ""


def _resolve_visual_package_done_at(
    manifest: dict[str, Any],
    *,
    review_log_lookup: dict[tuple[str, str], datetime],
) -> tuple[datetime | None, str, str, list[str]]:
    resolved: list[tuple[datetime, str, str]] = []
    for item in scene_items(manifest):
        if not bool(item.get("required", True)):
            continue
        if str(item.get("review_status", "")).strip() != "approved":
            return None, "", "", []
        timestamp, source, confidence = _resolve_item_timestamp(
            explicit_value=item.get("reviewed_at"),
            explicit_source="scene_stills.reviewed_at",
            review_log_lookup=review_log_lookup,
            review_log_key=("scene_still", str(item.get("id", "")).strip()),
            fallback_path=item.get("selected_asset") or item.get("output_path"),
            fallback_source="scene_still_asset_mtime",
        )
        if timestamp is None:
            return None, "", "", []
        resolved.append((timestamp, source, confidence))
    for item in packaging_items(manifest):
        if not bool(item.get("required", True)):
            continue
        if str(item.get("review_status", "")).strip() != "approved":
            return None, "", "", []
        timestamp, source, confidence = _resolve_item_timestamp(
            explicit_value=item.get("reviewed_at"),
            explicit_source="packaging_stills.reviewed_at",
            review_log_lookup=review_log_lookup,
            review_log_key=("packaging_still", str(item.get("id", "")).strip()),
            fallback_path=item.get("selected_asset") or item.get("output_path"),
            fallback_source="packaging_asset_mtime",
        )
        if timestamp is None:
            return None, "", "", []
        resolved.append((timestamp, source, confidence))
    motion_candidates = [item for item in motion_items(manifest) if str(item.get("status", "todo")).strip() != "not_needed"]
    for item in motion_candidates:
        if str(item.get("status", "")).strip() != "done":
            return None, "", "", []
        timestamp, source, confidence = _resolve_item_timestamp(
            explicit_value=item.get("reviewed_at"),
            explicit_source="motion_assets.reviewed_at",
            review_log_lookup=review_log_lookup,
            review_log_key=("motion_asset", str(item.get("id", "")).strip()),
            fallback_path=item.get("output_path"),
            fallback_source="motion_asset_mtime",
        )
        if timestamp is None:
            return None, "", "", []
        resolved.append((timestamp, source, confidence))
    if not resolved:
        return None, "", "", []
    latest_timestamp, _, _ = max(resolved, key=lambda item: item[0])
    derived_from = [source for _, source, _ in resolved]
    confidence = "explicit" if all(level == "explicit" for _, _, level in resolved) else "mixed"
    return latest_timestamp, "composite", confidence, derived_from


def _resolve_visual_research_done_at(
    manifest: dict[str, Any],
    *,
    review_log_lookup: dict[tuple[str, str], datetime],
) -> tuple[datetime | None, str, str]:
    visual_research = manifest.get("visual_research", {})
    vr_approval = visual_research.get("approval", {})
    resolved_at, source, confidence = _resolve_item_timestamp(
        explicit_value=vr_approval.get("reviewed_at"),
        explicit_source="visual_research.approval.reviewed_at",
        review_log_lookup=review_log_lookup,
        review_log_key=("visual_research", "visual_research"),
        fallback_path=visual_research.get("assembly_notes_path"),
        fallback_source="visual_research_doc_mtime",
    )
    if str(vr_approval.get("status", "")).strip() != "approved":
        return None, "", ""
    return resolved_at, source, confidence


def _resolve_audio_done_at(manifest: dict[str, Any]) -> tuple[datetime | None, str, str]:
    audio_done_at = None
    audio_source = ""
    audio_confidence = ""
    audio = manifest.get("audio", {})
    if str(audio.get("status", "")).strip() != "not_needed":
        master_mtime = _file_mtime_datetime(audio.get("master_path"))
        transcript_mtime = _file_mtime_datetime(audio.get("transcript_path"))
        if master_mtime and transcript_mtime:
            audio_done_at = max(master_mtime, transcript_mtime)
            audio_source = "audio_output_mtime"
            audio_confidence = "backfilled"
    return audio_done_at, audio_source, audio_confidence


def _resolve_latest_research_anchor(
    manifest: dict[str, Any],
    *,
    context: Context,
    review_log_lookup: dict[tuple[str, str], datetime],
) -> tuple[datetime | None, str]:
    episode_id = str(manifest.get("id", "")).strip()
    anchors: list[tuple[datetime, str]] = []
    visual_research_done_at, _, _ = _resolve_visual_research_done_at(
        manifest,
        review_log_lookup=review_log_lookup,
    )
    if visual_research_done_at is not None:
        anchors.append((visual_research_done_at, "visual_research"))
    episode_info = context.episodes_repo.get_episode_info(episode_id) if episode_id else None
    fact_check_path = episode_info.fact_check_path if episode_info else None
    fact_check_at = _file_mtime_datetime(fact_check_path)
    if fact_check_at is not None:
        anchors.append((fact_check_at, "fact_check"))
    if not anchors:
        return None, ""
    latest_at, source = max(anchors, key=lambda item: item[0])
    return latest_at, source


def _build_cycle_time(
    manifest: dict[str, Any],
    *,
    context: Context,
    next_action_lane: str,
) -> dict[str, Any]:
    episode_id = str(manifest.get("id", "")).strip()
    review_log_lookup = _build_review_log_index(context, episode_id)
    tracking = manifest.get("tracking", {})
    assembly = manifest.get("assembly", {})
    release = manifest.get("release", {})
    visual_research = manifest.get("visual_research", {})

    bootstrapped_source = str(tracking.get("_bootstrapped_at_source", "")).strip()
    bootstrapped_at = _parse_iso8601(tracking.get("bootstrapped_at"))
    visual_research_done_at, visual_research_source, visual_research_confidence = _resolve_visual_research_done_at(
        manifest,
        review_log_lookup=review_log_lookup,
    )
    audio_done_at, audio_source, audio_confidence = _resolve_audio_done_at(manifest)

    visual_package_done_at, visual_package_source, visual_package_confidence, visual_package_inputs = _resolve_visual_package_done_at(
        manifest,
        review_log_lookup=review_log_lookup,
    )

    assembly_done_at = _parse_iso8601(assembly.get("completed_at"))
    assembly_source = "assembly.completed_at" if assembly_done_at else ""
    assembly_confidence = "explicit" if assembly_done_at else ""
    if assembly_done_at is None and str(assembly.get("status", "")).strip() == "done":
        assembly_done_at = _file_mtime_datetime(assembly.get("master_video_path"))
        if assembly_done_at is not None:
            assembly_source = "assembly_master_video_mtime"
            assembly_confidence = "backfilled"

    posted_at = _parse_iso8601(release.get("published_at"))
    posted_source = "release.published_at" if posted_at else ""
    posted_confidence = "explicit" if posted_at else ""

    milestones = {
        "bootstrapped_at": _milestone_payload(
            bootstrapped_at,
            source=bootstrapped_source or "tracking.bootstrapped_at",
            confidence="explicit" if bootstrapped_source == "tracking.bootstrapped_at" else "backfilled" if bootstrapped_at else "",
        ),
        "visual_research_done_at": _milestone_payload(
            visual_research_done_at,
            source=visual_research_source,
            confidence=visual_research_confidence,
        ),
        "audio_done_at": _milestone_payload(
            audio_done_at,
            source=audio_source,
            confidence=audio_confidence,
        ),
        "visual_package_done_at": _milestone_payload(
            visual_package_done_at,
            source=visual_package_source,
            confidence=visual_package_confidence,
            derived_from=visual_package_inputs,
        ),
        "assembly_done_at": _milestone_payload(
            assembly_done_at,
            source=assembly_source,
            confidence=assembly_confidence,
        ),
        "posted_at": _milestone_payload(
            posted_at,
            source=posted_source,
            confidence=posted_confidence,
        ),
    }

    chronology_issues: list[dict[str, str]] = []

    def record_issue(message: str, lane: str) -> None:
        chronology_issues.append({"message": message, "lane": lane})

    if bootstrapped_at and posted_at and posted_at < bootstrapped_at:
        record_issue("posted_at is earlier than bootstrapped_at.", "release")
    if audio_done_at and assembly_done_at and assembly_done_at < audio_done_at:
        record_issue("assembly_done_at is earlier than audio_done_at.", "assembly")
    if visual_package_done_at and assembly_done_at and assembly_done_at < visual_package_done_at:
        record_issue("assembly_done_at is earlier than visual_package_done_at.", "assembly")
    if assembly_done_at and posted_at and posted_at < assembly_done_at:
        record_issue("posted_at is earlier than assembly_done_at.", "release")

    segment_pairs = {
        "bootstrap_to_visual_research": (bootstrapped_at, visual_research_done_at),
        "bootstrap_to_audio": (bootstrapped_at, audio_done_at),
        "bootstrap_to_visual_package": (bootstrapped_at, visual_package_done_at),
        "bootstrap_to_assembly": (bootstrapped_at, assembly_done_at),
        "bootstrap_to_posted": (bootstrapped_at, posted_at),
        "visual_research_to_audio": (visual_research_done_at, audio_done_at),
        "visual_research_to_visual_package": (visual_research_done_at, visual_package_done_at),
        "assembly_to_posted": (assembly_done_at, posted_at),
    }
    segments: dict[str, dict[str, float]] = {}
    for name, (start, end) in segment_pairs.items():
        if start is None or end is None:
            continue
        duration = _duration_payload(start, end)
        if duration is not None:
            segments[name] = duration

    now = datetime.now(timezone.utc).replace(microsecond=0)
    total_elapsed = _duration_payload(bootstrapped_at, posted_at) if bootstrapped_at and posted_at else None
    in_flight_age = _duration_payload(bootstrapped_at, now) if bootstrapped_at and posted_at is None else None
    valid_for_aggregates = bootstrapped_at is not None and (posted_at is None or posted_at >= bootstrapped_at) and not any(
        issue["lane"] == "assembly" and issue["message"].startswith("assembly_done_at is earlier")
        for issue in chronology_issues
    )

    return {
        "status": "complete" if posted_at else "in_progress" if bootstrapped_at else "unknown",
        "current_blocker_lane": next_action_lane if next_action_lane != "complete" else "",
        "milestones": milestones,
        "segment_durations": segments,
        "total_elapsed_hours": total_elapsed["hours"] if total_elapsed else None,
        "total_elapsed_days": total_elapsed["days"] if total_elapsed else None,
        "in_flight_age_hours": in_flight_age["hours"] if in_flight_age else None,
        "in_flight_age_days": in_flight_age["days"] if in_flight_age else None,
        "chronology_issues": chronology_issues,
        "valid_for_aggregates": valid_for_aggregates,
    }


def lane_order(context: Context) -> list[str]:
    configured = list(context.channel.get("defaults", {}).get("lane_order", []))
    expected = [lane.name for lane in LANE_DEFINITIONS]
    if configured and configured != expected:
        raise SystemExit("config/channel.toml defaults.lane_order does not match the lane registry.")
    return configured or expected


def scene_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest.get("scene_stills", {}).get("items", []))


def packaging_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest.get("packaging_stills", {}).get("items", []))


def motion_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest.get("motion_assets", {}).get("items", []))


def motion_item_authoring_mode(item: dict[str, Any]) -> str:
    return str(item.get("authoring_mode", "legacy_i2v")).strip() or "legacy_i2v"


def build_scene_lookup(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in items if "id" in item}


def _format_missing_act_ids(act_ids: tuple[str, ...] | list[str]) -> str:
    return ", ".join(str(item) for item in act_ids if str(item).strip())


def add_issue(bucket: list[dict[str, Any]], message: str, *, lane: str | None = None, path: str | None = None) -> None:
    issue = {"message": message}
    if lane:
        issue["lane"] = lane
    if path:
        issue["path"] = path
    bucket.append(issue)


def normalize_kind(kind: str) -> str:
    normalized = str(kind).strip().lower()
    if normalized not in PACKAGING_KIND_TO_FAMILY:
        raise ValueError(f"Unsupported packaging kind: {kind}")
    return normalized


def _lane_index(name: str) -> int:
    return [lane.name for lane in LANE_DEFINITIONS].index(name)


def _lane_is_complete(status: str) -> bool:
    return status in {"done", "not_needed"}


def _item_has_latest_render(item: dict[str, Any]) -> bool:
    return bool(str(item.get("latest_render_path", "")).strip())


def _item_has_approved_proof(item: dict[str, Any]) -> bool:
    approved_proof = item.get("approved_proof_path")
    return bool(approved_proof and str(item.get("review_status", "")) == "approved" and path_exists(approved_proof))


def _item_is_selected_and_approved(item: dict[str, Any]) -> bool:
    selected_asset = item.get("selected_asset")
    return bool(selected_asset and str(item.get("review_status", "")) == "approved" and path_exists(selected_asset))


def _item_is_approved_but_unfinished(item: dict[str, Any]) -> bool:
    return _item_has_approved_proof(item) and not _item_is_selected_and_approved(item)


def _motion_source_asset_path(item: dict[str, Any]) -> str:
    approved_proof_path = str(item.get("approved_proof_path", "")).strip()
    if approved_proof_path and path_exists(approved_proof_path):
        return approved_proof_path
    selected_asset = str(item.get("selected_asset", "")).strip()
    if selected_asset and path_exists(selected_asset):
        return selected_asset
    return ""


def _item_is_approved_for_motion(item: dict[str, Any]) -> bool:
    return str(item.get("motion_review_status", "")).strip() == "approved_for_motion" and bool(
        _motion_source_asset_path(item)
    )


def derive_scene_lane_status(items: list[dict[str, Any]]) -> str:
    if any(str(item.get("archetype_status", "resolved" if item.get("preset") else "unresolved")) == "unresolved" for item in items):
        return "blocked"
    required_items = [item for item in items if bool(item.get("required", True))]
    if required_items and all(_item_is_selected_and_approved(item) for item in required_items):
        return "done"
    if any(_item_has_latest_render(item) and not _item_has_approved_proof(item) and not _item_is_selected_and_approved(item) for item in items):
        return "review"
    if any(_item_is_approved_but_unfinished(item) for item in items):
        return "in_progress"
    if any(_item_has_latest_render(item) and not _item_is_selected_and_approved(item) for item in items):
        return "review"
    if any(str(item.get("review_status", "pending")) == "blocked" for item in required_items):
        return "blocked"
    return "todo"


def derive_packaging_lane_status(items: list[dict[str, Any]]) -> str:
    required_items = [item for item in items if bool(item.get("required", True))]
    if required_items and all(_item_is_selected_and_approved(item) for item in required_items):
        return "done"
    if any(_item_has_latest_render(item) and not _item_has_approved_proof(item) and not _item_is_selected_and_approved(item) for item in items):
        return "review"
    if any(_item_is_approved_but_unfinished(item) for item in items):
        return "in_progress"
    if any(_item_has_latest_render(item) and not _item_is_selected_and_approved(item) for item in items):
        return "review"
    if any(str(item.get("review_status", "pending")) == "blocked" for item in required_items):
        return "blocked"
    return "todo"


def lane_is_eligible(lanes: dict[str, dict[str, Any]], lane: str) -> bool:
    if lane == "visual_research":
        return True
    if lane in {"audio", "scene_stills", "packaging_stills"}:
        return _lane_is_complete(str(lanes["visual_research"]["status"]))
    if lane == "motion_assets":
        return lanes["scene_stills"]["status"] in {"review", "in_progress", "done"}
    if lane == "assembly":
        return (
            lanes["audio"]["status"] == "done"
            and lanes["scene_stills"].get("required_complete")
            and lanes["packaging_stills"].get("required_complete")
            and lanes["motion_assets"].get("ready_for_assembly")
            and lanes["assembly"].get("coverage_complete", True)
        )
    if lane == "web":
        return _lane_is_complete(str(lanes["assembly"]["status"]))
    if lane == "release":
        return _lane_is_complete(str(lanes["assembly"]["status"])) and _lane_is_complete(str(lanes["web"]["status"]))
    if lane == "analytics":
        return _lane_is_complete(str(lanes["release"]["status"]))
    return False


def lane_is_active(lanes: dict[str, dict[str, Any]], lane: str) -> bool:
    return str(lanes[lane]["status"]) in {"in_progress", "review", "done"}


def _build_cycle_time_summary(
    completed_entries: list[dict[str, Any]],
    in_flight_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    recent_completed = completed_entries[:ROLLING_HISTORY_WINDOW]
    recent_cycle_days = [float(entry["cycle_days"]) for entry in recent_completed]
    p50_value = _median(recent_cycle_days) if len(recent_cycle_days) >= MIN_P50_SAMPLES else None
    p90_value = _percentile_nearest_rank(recent_cycle_days, 90) if len(recent_cycle_days) >= MIN_P90_SAMPLES else None
    trend_payload: dict[str, Any] = {
        "status": "insufficient_sample",
        "window_size": TREND_WINDOW_SIZE,
        "recent_p50_cycle_days": None,
        "previous_p50_cycle_days": None,
        "delta_days": None,
        "direction": "unknown",
    }
    if len(recent_cycle_days) >= TREND_WINDOW_SIZE * 2:
        recent_p50 = _median(recent_cycle_days[:TREND_WINDOW_SIZE])
        previous_p50 = _median(recent_cycle_days[TREND_WINDOW_SIZE : TREND_WINDOW_SIZE * 2])
        delta_days = round(float(recent_p50) - float(previous_p50), 2) if recent_p50 is not None and previous_p50 is not None else None
        direction = "flat"
        if delta_days is not None and delta_days < 0:
            direction = "faster"
        elif delta_days is not None and delta_days > 0:
            direction = "slower"
        trend_payload = {
            "status": "ok",
            "window_size": TREND_WINDOW_SIZE,
            "recent_p50_cycle_days": round(float(recent_p50), 2) if recent_p50 is not None else None,
            "previous_p50_cycle_days": round(float(previous_p50), 2) if previous_p50 is not None else None,
            "delta_days": delta_days,
            "direction": direction,
        }

    slowest_in_flight = sorted(in_flight_entries, key=lambda entry: float(entry["age_days"]), reverse=True)[:SLOWEST_IN_FLIGHT_LIMIT]
    slowest_payload: list[dict[str, Any]] = []
    for entry in slowest_in_flight:
        remaining_days = None
        eta_at_p50 = ""
        if p50_value is not None:
            remaining_days = round(max(float(p50_value) - float(entry["age_days"]), 0.0), 2)
            if remaining_days > 0:
                eta_at_p50 = _datetime_to_iso(datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=remaining_days))
        slowest_payload.append(
            {
                "episode_id": entry["episode_id"],
                "title": entry["title"],
                "age_days": round(float(entry["age_days"]), 2),
                "age_hours": round(float(entry["age_hours"]), 2),
                "current_blocker_lane": entry["current_blocker_lane"],
                "estimated_remaining_days_p50": remaining_days,
                "eta_at_p50": eta_at_p50,
            }
        )

    return {
        "completed_sample_count": len(completed_entries),
        "in_flight_count": len(in_flight_entries),
        "rolling_window_size": min(len(completed_entries), ROLLING_HISTORY_WINDOW),
        "minimum_samples": {"p50": MIN_P50_SAMPLES, "p90": MIN_P90_SAMPLES},
        "p50_cycle_days": _metric_payload(p50_value, status="ok" if p50_value is not None else "insufficient_sample", sample_count=len(recent_cycle_days)),
        "p90_cycle_days": _metric_payload(p90_value, status="ok" if p90_value is not None else "insufficient_sample", sample_count=len(recent_cycle_days)),
        "trend": trend_payload,
        "slowest_in_flight": slowest_payload,
    }


def _build_throughput_summary(posted_entries: list[dict[str, Any]]) -> dict[str, Any]:
    recent_posted = posted_entries[:ROLLING_HISTORY_WINDOW]
    recent_posted_dates = [entry["posted_at"] for entry in recent_posted if isinstance(entry.get("posted_at"), datetime)]
    if len(recent_posted_dates) >= MIN_P90_SAMPLES:
        ordered_dates = sorted(recent_posted_dates)
        span_seconds = (ordered_dates[-1] - ordered_dates[0]).total_seconds()
        if span_seconds > 0:
            episodes_per_week = ((len(ordered_dates) - 1) / span_seconds) * 7 * 24 * 3600
            gaps_days = [
                _round_days((current - previous).total_seconds())
                for previous, current in zip(ordered_dates, ordered_dates[1:], strict=False)
            ]
            median_gap = _median(gaps_days)
            return {
                "posted_sample_count": len(posted_entries),
                "rolling_window_size": min(len(posted_entries), ROLLING_HISTORY_WINDOW),
                "episodes_per_week": _metric_payload(episodes_per_week, status="ok", sample_count=len(ordered_dates)),
                "median_days_between_posts": _metric_payload(median_gap, status="ok", sample_count=len(gaps_days)),
                "latest_posted_at": _datetime_to_iso(max(ordered_dates)),
            }
    return {
        "posted_sample_count": len(posted_entries),
        "rolling_window_size": min(len(posted_entries), ROLLING_HISTORY_WINDOW),
        "episodes_per_week": _metric_payload(None, status="insufficient_sample", sample_count=len(recent_posted_dates)),
        "median_days_between_posts": _metric_payload(None, status="insufficient_sample", sample_count=max(0, len(recent_posted_dates) - 1)),
        "latest_posted_at": _datetime_to_iso(max(recent_posted_dates)) if recent_posted_dates else "",
    }


def _build_slate_forecast(
    *,
    context: Context,
    posted_count: int,
    throughput_summary: dict[str, Any],
) -> dict[str, Any]:
    target_episode_count = int(context.channel.get("defaults", {}).get("slate_target_episode_count", 186) or 186)
    remaining_count = max(0, target_episode_count - posted_count)
    episodes_per_week_metric = throughput_summary["episodes_per_week"]
    episodes_per_week = episodes_per_week_metric.get("value")
    if remaining_count == 0:
        return {
            "status": "complete",
            "basis": "rolling_post_throughput",
            "target_episode_count": target_episode_count,
            "posted_count": posted_count,
            "remaining_count": remaining_count,
            "episodes_per_week": episodes_per_week,
            "weeks_remaining": 0.0,
            "finish_eta": throughput_summary.get("latest_posted_at", ""),
        }
    if episodes_per_week_metric.get("status") != "ok" or not episodes_per_week:
        return {
            "status": "insufficient_sample",
            "basis": "rolling_post_throughput",
            "target_episode_count": target_episode_count,
            "posted_count": posted_count,
            "remaining_count": remaining_count,
            "episodes_per_week": None,
            "weeks_remaining": None,
            "finish_eta": "",
        }
    weeks_remaining = round(remaining_count / float(episodes_per_week), 2)
    finish_eta = _datetime_to_iso(datetime.now(timezone.utc).replace(microsecond=0) + timedelta(weeks=weeks_remaining))
    return {
        "status": "forecasted",
        "basis": "rolling_post_throughput",
        "target_episode_count": target_episode_count,
        "posted_count": posted_count,
        "remaining_count": remaining_count,
        "episodes_per_week": round(float(episodes_per_week), 2),
        "weeks_remaining": weeks_remaining,
        "finish_eta": finish_eta,
    }


def build_production_report(context: Context) -> dict[str, Any]:
    manifests = list_episode_manifests(context)
    states = [derive_episode_state(manifest, context) for manifest in manifests]
    board_counts: dict[str, int] = {}
    lane_status_counts: dict[str, dict[str, int]] = {lane: {} for lane in lane_order(context)}
    unresolved_scene_archetypes: list[dict[str, str]] = []
    packaging_demand: dict[str, dict[str, Any]] = {}
    scene_stills_coverage: dict[str, Any] = {
        "required_pending_render_count": 0,
        "required_pending_review_count": 0,
        "required_pending_finish_count": 0,
        "episodes_pending_render": [],
        "episodes_pending_review": [],
        "episodes_pending_finish": [],
    }
    packaging_stills_coverage: dict[str, Any] = {
        "required_pending_render_count": 0,
        "required_pending_review_count": 0,
        "required_pending_finish_count": 0,
        "episodes_pending_render": [],
        "episodes_pending_review": [],
        "episodes_pending_finish": [],
    }
    motion_ready_episodes: list[str] = []
    motion_demand: dict[str, Any] = {"required_pending_count": 0, "episodes": []}
    motion_blocked_on_source_still_approval: dict[str, Any] = {"required_pending_count": 0, "episodes": []}
    motion_proof_review_coverage: dict[str, Any] = {
        "items_with_latest_render": 0,
        "items_in_review": 0,
        "items_done": 0,
        "episodes_with_latest_render": [],
    }
    completed_cycle_entries: list[dict[str, Any]] = []
    in_flight_cycle_entries: list[dict[str, Any]] = []
    posted_entries: list[dict[str, Any]] = []
    posted_count = 0

    for manifest, state in zip(manifests, states, strict=True):
        board_counts[state["board_category"]] = board_counts.get(state["board_category"], 0) + 1
        for lane in lane_order(context):
            status = state["lanes"][lane]["status"]
            lane_status_counts[lane][status] = lane_status_counts[lane].get(status, 0) + 1
        if any(_item_is_approved_for_motion(item) for item in scene_items(manifest)):
            motion_ready_episodes.append(str(manifest["id"]))
        for item in scene_items(manifest):
            archetype_status = str(item.get("archetype_status", "resolved" if item.get("preset") else "unresolved"))
            if archetype_status == "unresolved":
                unresolved_scene_archetypes.append({"episode_id": str(manifest["id"]), "item_id": str(item.get("id", ""))})
                continue
            if not bool(item.get("required", True)):
                continue
            if _item_is_selected_and_approved(item):
                continue
            if _item_is_approved_but_unfinished(item):
                scene_stills_coverage["required_pending_finish_count"] += 1
                scene_stills_coverage["episodes_pending_finish"].append(str(manifest["id"]))
            elif _item_has_latest_render(item):
                scene_stills_coverage["required_pending_review_count"] += 1
                scene_stills_coverage["episodes_pending_review"].append(str(manifest["id"]))
            else:
                scene_stills_coverage["required_pending_render_count"] += 1
                scene_stills_coverage["episodes_pending_render"].append(str(manifest["id"]))
        for item in packaging_items(manifest):
            if not bool(item.get("required", True)):
                continue
            kind = normalize_kind(str(item.get("kind", "")))
            is_complete = _item_is_selected_and_approved(item)
            if is_complete:
                continue
            bucket = packaging_demand.setdefault(kind, {"required_pending_count": 0, "episodes": []})
            bucket["required_pending_count"] += 1
            bucket["episodes"].append(str(manifest["id"]))
            if _item_is_approved_but_unfinished(item):
                packaging_stills_coverage["required_pending_finish_count"] += 1
                packaging_stills_coverage["episodes_pending_finish"].append(str(manifest["id"]))
            elif _item_has_latest_render(item):
                packaging_stills_coverage["required_pending_review_count"] += 1
                packaging_stills_coverage["episodes_pending_review"].append(str(manifest["id"]))
            else:
                packaging_stills_coverage["required_pending_render_count"] += 1
                packaging_stills_coverage["episodes_pending_render"].append(str(manifest["id"]))
        has_latest_render = False
        motion_blocked_for_episode = False
        for item in motion_items(manifest):
            item_status = str(item.get("status", "todo"))
            latest_render_path = str(item.get("latest_render_path", "")).strip()
            latest_render_manifest_path = str(item.get("latest_render_manifest_path", "")).strip()
            if item_status not in {"done", "not_needed"}:
                motion_demand["required_pending_count"] += 1
                motion_demand["episodes"].append(str(manifest["id"]))
                source_still = build_scene_lookup(scene_items(manifest)).get(str(item.get("source_still_id", "")))
                if source_still and not _item_is_approved_for_motion(source_still):
                    motion_blocked_for_episode = True
            if latest_render_path:
                motion_proof_review_coverage["items_with_latest_render"] += 1
                has_latest_render = True
            if item_status == "review":
                motion_proof_review_coverage["items_in_review"] += 1
            if item_status == "done":
                motion_proof_review_coverage["items_done"] += 1
            if latest_render_manifest_path and not latest_render_path:
                has_latest_render = True
        if has_latest_render:
            motion_proof_review_coverage["episodes_with_latest_render"].append(str(manifest["id"]))
        if motion_blocked_for_episode:
            motion_blocked_on_source_still_approval["required_pending_count"] += 1
            motion_blocked_on_source_still_approval["episodes"].append(str(manifest["id"]))

        cycle_time = state.get("cycle_time", {})
        milestones = cycle_time.get("milestones", {})
        posted_timestamp = _parse_iso8601(milestones.get("posted_at", {}).get("timestamp"))
        if posted_timestamp is not None:
            posted_count += 1
        if cycle_time.get("valid_for_aggregates"):
            total_elapsed_days = cycle_time.get("total_elapsed_days")
            if posted_timestamp is not None and total_elapsed_days is not None:
                completed_cycle_entries.append(
                    {
                        "episode_id": str(state["episode_id"]),
                        "title": str(state.get("title", "")),
                        "cycle_days": float(total_elapsed_days),
                        "posted_at": posted_timestamp,
                    }
                )
                posted_entries.append(
                    {
                        "episode_id": str(state["episode_id"]),
                        "posted_at": posted_timestamp,
                    }
                )
            elif cycle_time.get("in_flight_age_days") is not None:
                in_flight_cycle_entries.append(
                    {
                        "episode_id": str(state["episode_id"]),
                        "title": str(state.get("title", "")),
                        "age_days": float(cycle_time["in_flight_age_days"]),
                        "age_hours": float(cycle_time["in_flight_age_hours"]),
                        "current_blocker_lane": str(cycle_time.get("current_blocker_lane", "")),
                    }
                )

    completed_cycle_entries.sort(key=lambda entry: entry["posted_at"], reverse=True)
    posted_entries.sort(key=lambda entry: entry["posted_at"], reverse=True)
    cycle_time_summary = _build_cycle_time_summary(completed_cycle_entries, in_flight_cycle_entries)
    throughput_summary = _build_throughput_summary(posted_entries)
    slate_forecast = _build_slate_forecast(
        context=context,
        posted_count=posted_count,
        throughput_summary=throughput_summary,
    )

    return {
        "generated_at": utc_now_iso(),
        "episode_count": len(manifests),
        "board_counts": board_counts,
        "lane_status_counts": lane_status_counts,
        "unresolved_scene_archetypes": unresolved_scene_archetypes,
        "packaging_demand": packaging_demand,
        "scene_stills_coverage": {
            **scene_stills_coverage,
            "episodes_pending_render": sorted(set(scene_stills_coverage["episodes_pending_render"])),
            "episodes_pending_review": sorted(set(scene_stills_coverage["episodes_pending_review"])),
            "episodes_pending_finish": sorted(set(scene_stills_coverage["episodes_pending_finish"])),
        },
        "packaging_stills_coverage": {
            **packaging_stills_coverage,
            "episodes_pending_render": sorted(set(packaging_stills_coverage["episodes_pending_render"])),
            "episodes_pending_review": sorted(set(packaging_stills_coverage["episodes_pending_review"])),
            "episodes_pending_finish": sorted(set(packaging_stills_coverage["episodes_pending_finish"])),
        },
        "motion_ready_episodes": sorted(motion_ready_episodes),
        "motion_ready_count": len(motion_ready_episodes),
        "motion_demand": {
            "required_pending_count": motion_demand["required_pending_count"],
            "episodes": sorted(set(motion_demand["episodes"])),
        },
        "motion_blocked_on_source_still_approval": {
            "required_pending_count": motion_blocked_on_source_still_approval["required_pending_count"],
            "episodes": sorted(set(motion_blocked_on_source_still_approval["episodes"])),
        },
        "motion_proof_review_coverage": {
            **motion_proof_review_coverage,
            "episodes_with_latest_render": sorted(set(motion_proof_review_coverage["episodes_with_latest_render"])),
        },
        "cycle_time_summary": cycle_time_summary,
        "throughput_summary": throughput_summary,
        "slate_forecast": slate_forecast,
    }


def format_production_report(report: dict[str, Any], context: Context | None = None) -> str:
    ordered_lanes = lane_order(context) if context else [lane.name for lane in LANE_DEFINITIONS]
    lines = [f"episodes: {report['episode_count']}", "", "board counts:"]
    for category, count in sorted(report["board_counts"].items()):
        lines.append(f"  - {category}: {count}")
    lines.append("")
    lines.append("lane status counts:")
    for lane in ordered_lanes:
        counts = report["lane_status_counts"].get(lane, {})
        if counts:
            lines.append(f"  - {lane}: {', '.join(f'{status}={count}' for status, count in sorted(counts.items()))}")
    lines.append("")
    lines.append(f"unresolved scene archetypes: {len(report['unresolved_scene_archetypes'])}")
    for item in report["unresolved_scene_archetypes"]:
        lines.append(f"  - {item['episode_id']}: {item['item_id']}")
    lines.append("")
    lines.append("scene still coverage:")
    scene_coverage = report["scene_stills_coverage"]
    lines.append(
        f"  - pending_render: {scene_coverage['required_pending_render_count']} across {', '.join(scene_coverage['episodes_pending_render']) or 'none'}"
    )
    lines.append(
        f"  - pending_review: {scene_coverage['required_pending_review_count']} across {', '.join(scene_coverage['episodes_pending_review']) or 'none'}"
    )
    lines.append(
        f"  - pending_finish: {scene_coverage['required_pending_finish_count']} across {', '.join(scene_coverage['episodes_pending_finish']) or 'none'}"
    )
    lines.append("")
    lines.append("packaging demand:")
    if report["packaging_demand"]:
        for kind, data in sorted(report["packaging_demand"].items()):
            lines.append(f"  - {kind}: {data['required_pending_count']} pending across {', '.join(sorted(set(data['episodes'])))}")
    else:
        lines.append("  - none")
    lines.append("")
    lines.append("packaging still coverage:")
    packaging_coverage = report["packaging_stills_coverage"]
    lines.append(
        f"  - pending_render: {packaging_coverage['required_pending_render_count']} across {', '.join(packaging_coverage['episodes_pending_render']) or 'none'}"
    )
    lines.append(
        f"  - pending_review: {packaging_coverage['required_pending_review_count']} across {', '.join(packaging_coverage['episodes_pending_review']) or 'none'}"
    )
    lines.append(
        f"  - pending_finish: {packaging_coverage['required_pending_finish_count']} across {', '.join(packaging_coverage['episodes_pending_finish']) or 'none'}"
    )
    lines.append("")
    lines.append(f"motion ready episodes: {report['motion_ready_count']}")
    for episode_id in report["motion_ready_episodes"]:
        lines.append(f"  - {episode_id}")
    lines.append("")
    lines.append(
        f"motion demand: {report['motion_demand']['required_pending_count']} pending across {', '.join(report['motion_demand']['episodes']) or 'none'}"
    )
    lines.append(
        "motion blocked on still approval: "
        f"{report['motion_blocked_on_source_still_approval']['required_pending_count']} across "
        f"{', '.join(report['motion_blocked_on_source_still_approval']['episodes']) or 'none'}"
    )
    lines.append("motion proof/review coverage:")
    coverage = report["motion_proof_review_coverage"]
    lines.append(f"  - items_with_latest_render: {coverage['items_with_latest_render']}")
    lines.append(f"  - items_in_review: {coverage['items_in_review']}")
    lines.append(f"  - items_done: {coverage['items_done']}")
    lines.append(
        f"  - episodes_with_latest_render: {', '.join(coverage['episodes_with_latest_render']) if coverage['episodes_with_latest_render'] else 'none'}"
    )
    lines.append("")
    lines.append("cycle time:")
    cycle = report["cycle_time_summary"]
    p50_metric = cycle["p50_cycle_days"]
    p90_metric = cycle["p90_cycle_days"]
    lines.append(f"  - completed_samples: {cycle['completed_sample_count']}")
    lines.append(f"  - in_flight: {cycle['in_flight_count']}")
    lines.append(
        f"  - p50_days: {p50_metric['value'] if p50_metric['status'] == 'ok' else p50_metric['status']}"
    )
    lines.append(
        f"  - p90_days: {p90_metric['value'] if p90_metric['status'] == 'ok' else p90_metric['status']}"
    )
    trend = cycle["trend"]
    if trend["status"] == "ok":
        lines.append(
            "  - trend: "
            f"recent_p50={trend['recent_p50_cycle_days']} previous_p50={trend['previous_p50_cycle_days']} "
            f"delta_days={trend['delta_days']} direction={trend['direction']}"
        )
    else:
        lines.append(f"  - trend: {trend['status']}")
    lines.append("  - slowest_in_flight:")
    if cycle["slowest_in_flight"]:
        for entry in cycle["slowest_in_flight"]:
            remaining = (
                f" remaining_p50_days={entry['estimated_remaining_days_p50']}"
                if entry["estimated_remaining_days_p50"] is not None
                else ""
            )
            eta = f" eta_p50={entry['eta_at_p50']}" if entry["eta_at_p50"] else ""
            lines.append(
                f"    - {entry['episode_id']}: age_days={entry['age_days']} blocker={entry['current_blocker_lane'] or 'unknown'}{remaining}{eta}"
            )
    else:
        lines.append("    - none")
    lines.append("")
    lines.append("throughput:")
    throughput = report["throughput_summary"]
    epw_metric = throughput["episodes_per_week"]
    gap_metric = throughput["median_days_between_posts"]
    lines.append(f"  - posted_samples: {throughput['posted_sample_count']}")
    lines.append(
        f"  - episodes_per_week: {epw_metric['value'] if epw_metric['status'] == 'ok' else epw_metric['status']}"
    )
    lines.append(
        f"  - median_days_between_posts: {gap_metric['value'] if gap_metric['status'] == 'ok' else gap_metric['status']}"
    )
    lines.append(f"  - latest_posted_at: {throughput['latest_posted_at'] or 'none'}")
    lines.append("")
    lines.append("slate forecast:")
    forecast = report["slate_forecast"]
    lines.append(
        f"  - target={forecast['target_episode_count']} posted={forecast['posted_count']} remaining={forecast['remaining_count']}"
    )
    if forecast["status"] == "forecasted":
        lines.append(
            f"  - eta={forecast['finish_eta']} weeks_remaining={forecast['weeks_remaining']} episodes_per_week={forecast['episodes_per_week']}"
        )
    elif forecast["status"] == "complete":
        lines.append(f"  - eta={forecast['finish_eta'] or 'complete'}")
    else:
        lines.append(f"  - eta={forecast['status']}")
    if context:
        lines.append("")
        lines.append("web visibility:")
        for episode_id in sorted(context.web_repo.entry_ids()):
            entry = context.web_repo.get_launch_entry(episode_id)
            if entry:
                lines.append(
                    f"  - {episode_id}: archive_entry=yes homepage_visible={'yes' if entry.homepage_visible else 'no'}"
                )
    return "\n".join(lines)


def derive_episode_state(manifest: dict[str, Any], context: Context) -> dict[str, Any]:
    manifest = materialize_episode_manifest(context, manifest)
    errors: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    lanes: dict[str, dict[str, Any]] = {}

    episode_id = str(manifest.get("id", "")).strip()
    review_log_lookup = _build_review_log_index(context, episode_id) if episode_id else {}
    if not episode_id:
        add_issue(errors, "Manifest is missing id.")

    for lane in lane_order(context):
        status = table_status(manifest, lane)
        allowed_statuses = RELEASE_LANE_STATUSES if lane == "release" else LANE_STATUSES
        if status not in allowed_statuses:
            add_issue(errors, f"Lane `{lane}` has invalid status `{status}`.", lane=lane)
        lanes[lane] = {"status": status}

    script = manifest.get("script", {})
    script_path = path_or_none(script.get("path"))
    script_locked = script.get("status") == "locked"
    episode_info = context.episodes_repo.get_episode_info(episode_id) if episode_id else None
    expected_fact_check_path = (
        episode_info.directory / "fact_check.md"
        if episode_info is not None
        else script_path.parent / "fact_check.md"
        if script_path is not None
        else None
    )
    if not script_path or not script_path.exists():
        add_issue(errors, "Locked script path is missing.", lane="script", path=str(script_path) if script_path else None)
    if not script_locked:
        add_issue(errors, "Script status must be `locked` before orchestration starts.", lane="script")

    visual_research = manifest.get("visual_research", {})
    vr_approval = visual_research.get("approval", {})
    opening_sequence = visual_research.get("opening_sequence", {})
    vr_guardrails = visual_research.get("guardrails", {})
    vr_approval_status = str(vr_approval.get("status", "pending")).strip() or "pending"
    vr_script_sha_mismatch = bool(visual_research.get("_script_sha_mismatch"))
    vr_required = {
        "fact_check_path": expected_fact_check_path,
        "contact_sheet_path": visual_research.get("contact_sheet_path"),
        "source_inventory_path": visual_research.get("source_inventory_path"),
        "act_breakdown_path": visual_research.get("act_breakdown_path"),
        "reference_notes_path": visual_research.get("reference_notes_path"),
        "sources_path": visual_research.get("sources_path"),
        "assembly_notes_path": visual_research.get("assembly_notes_path"),
    }
    vr_status = lanes["visual_research"]["status"]
    vr_gate_required = vr_status in {"review", "done"}
    vr_docs_complete = True

    def add_visual_research_issue(message: str, *, path: str | None = None, blocking: bool = False) -> None:
        if blocking:
            add_issue(errors, message, lane="visual_research", path=path)
            return
        if vr_status != "todo":
            add_issue(pending, message, lane="visual_research", path=path)

    if vr_approval_status not in VISUAL_RESEARCH_APPROVAL_STATUSES:
        add_issue(
            errors,
            f"Visual research approval has invalid status `{vr_approval_status}`.",
            lane="visual_research",
        )
    for field, value in vr_required.items():
        exists = path_exists(value)
        vr_docs_complete = vr_docs_complete and exists
        if not exists:
            add_visual_research_issue(
                f"Visual research file `{field}` is missing.",
                path=str(value),
                blocking=vr_gate_required,
            )

    vr_acts = list(visual_research.get("acts") or [])
    vr_structured_complete = True
    vr_scene_coverage_complete = True
    vr_motion_coverage_complete = True
    if not vr_acts:
        vr_structured_complete = False
        add_visual_research_issue(
            "Visual research must map the locked script into structured per-act coverage.",
            blocking=vr_gate_required,
        )
    for act in vr_acts:
        act_id = str(act.get("id", "")).strip() or "unknown"
        title = str(act.get("title", "")).strip()
        visual_thesis = str(act.get("visual_thesis", "")).strip()
        dominant_signal = str(act.get("dominant_signal", "")).strip()
        reference_board_path = str(act.get("reference_board_path", "")).strip()
        beat_count = max(0, int(act.get("beat_count", 0)))
        estimated_seconds = max(0, int(act.get("estimated_seconds", 0)))
        planned_scene_ids = [str(item).strip() for item in act.get("planned_scene_ids", []) if str(item).strip()]
        planned_motion_ids = [str(item).strip() for item in act.get("planned_motion_ids", []) if str(item).strip()]
        required_motion_sequences = max(0, int(act.get("required_motion_sequences", 0)))
        exception_reason = str(act.get("exception_reason", "")).strip()
        if not title:
            vr_structured_complete = False
            add_visual_research_issue(
                f"Visual research act `{act_id}` is missing a title.",
                blocking=vr_gate_required,
            )
        if not visual_thesis:
            vr_structured_complete = False
            add_visual_research_issue(
                f"Visual research act `{act_id}` is missing `visual_thesis`.",
                blocking=vr_gate_required,
            )
        if not dominant_signal:
            vr_structured_complete = False
            add_visual_research_issue(
                f"Visual research act `{act_id}` is missing `dominant_signal`.",
                blocking=vr_gate_required,
            )
        if not reference_board_path:
            vr_structured_complete = False
            add_visual_research_issue(
                f"Visual research act `{act_id}` is missing `reference_board_path`.",
                blocking=vr_gate_required,
            )
        if estimated_seconds <= 0:
            vr_structured_complete = False
            add_visual_research_issue(
                f"Visual research act `{act_id}` is missing a valid `estimated_seconds` value.",
                blocking=vr_gate_required,
            )
        if len(planned_scene_ids) < beat_count:
            vr_scene_coverage_complete = False
            add_visual_research_issue(
                f"Visual research act `{act_id}` has {len(planned_scene_ids)} planned scene ids for beat_count={beat_count}.",
                blocking=vr_gate_required,
            )
        if len(planned_motion_ids) < required_motion_sequences and not exception_reason:
            vr_motion_coverage_complete = False
            add_visual_research_issue(
                f"Visual research act `{act_id}` needs {required_motion_sequences} planned motion sequences for {estimated_seconds}s or an exception_reason.",
                blocking=vr_gate_required,
            )
    opening_object_strategy = str(opening_sequence.get("object_strategy", "")).strip() or "episode_specific_cluster"
    opening_time_period_label = str(opening_sequence.get("time_period_label", "")).strip()
    opening_supporting_objects = [str(item).strip() for item in opening_sequence.get("supporting_objects", []) if str(item).strip()]
    opening_subject_object = str(opening_sequence.get("subject_object", "")).strip()
    opening_focus_transition = str(opening_sequence.get("focus_transition", "")).strip()
    opening_subject_action = str(opening_sequence.get("subject_action", "")).strip()
    opening_act_id = str(opening_sequence.get("act_id", "")).strip()
    opening_planned_scene_id = str(opening_sequence.get("planned_scene_id", "")).strip()
    opening_planned_motion_id = str(opening_sequence.get("planned_motion_id", "")).strip()
    opening_audio_end_cue_text = str(opening_sequence.get("audio_end_cue_text", "")).strip()
    opening_min_duration_seconds = float(opening_sequence.get("min_duration_seconds", 0.0) or 0.0)
    opening_timing = visual_research.get("_opening_timing", {}) if isinstance(visual_research.get("_opening_timing", {}), dict) else {}
    opening_declared = bool(opening_planned_scene_id or opening_planned_motion_id)
    opening_slots = [
        {
            "slot_id": str(slot.get("slot_id", "")).strip(),
            "display_label": str(slot.get("display_label", "")).strip(),
            "role": str(slot.get("role", "")).strip(),
            "object_scope": str(slot.get("object_scope", "")).strip(),
            "renderability": str(slot.get("renderability", "")).strip(),
            "visual_descriptor": str(slot.get("visual_descriptor", "")).strip(),
        }
        for slot in opening_sequence.get("slots", [])
        if isinstance(slot, dict)
    ]
    opening_required_fields = {
        "time_period_label": opening_time_period_label,
        "supporting_objects": opening_supporting_objects,
        "subject_object": opening_subject_object,
        "focus_transition": opening_focus_transition,
        "subject_action": opening_subject_action,
        "act_id": opening_act_id,
        "planned_scene_id": opening_planned_scene_id,
        "planned_motion_id": opening_planned_motion_id,
    }
    if opening_declared:
        opening_required_fields["audio_end_cue_text"] = opening_audio_end_cue_text
    vr_opening_sequence_complete = True
    if opening_object_strategy not in OPENING_OBJECT_STRATEGIES:
        vr_structured_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            f"Visual research opening_sequence has unsupported object_strategy `{opening_object_strategy}`.",
            blocking=vr_gate_required,
        )
    for field_name, field_value in opening_required_fields.items():
        is_missing = len(field_value) == 0 if isinstance(field_value, list) else not field_value
        if not is_missing:
            continue
        vr_structured_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            f"Visual research opening_sequence is missing `{field_name}`.",
            blocking=vr_gate_required,
        )
    if opening_declared and opening_planned_scene_id != CANONICAL_OPENING_SCENE_ID:
        vr_structured_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            f"Visual research opening_sequence planned_scene_id `{opening_planned_scene_id}` must be `{CANONICAL_OPENING_SCENE_ID}`.",
            blocking=vr_gate_required,
        )
    if opening_declared and opening_planned_motion_id != CANONICAL_OPENING_MOTION_ID:
        vr_structured_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            f"Visual research opening_sequence planned_motion_id `{opening_planned_motion_id}` must be `{CANONICAL_OPENING_MOTION_ID}`.",
            blocking=vr_gate_required,
        )
    opening_slot_contract_enabled = bool(opening_slots)
    opening_slot_lookup: dict[str, dict[str, str]] = {}
    opening_subject_slot_ids: list[str] = []
    supporting_slot_count = 0
    generic_mass_market_supporting_slot_ids: list[str] = []
    if opening_slot_contract_enabled:
        for slot_index, slot in enumerate(opening_slots, start=1):
            slot_id = slot["slot_id"]
            display_label = slot["display_label"]
            slot_role = slot["role"]
            object_scope = slot["object_scope"]
            renderability = slot["renderability"]
            visual_descriptor = slot["visual_descriptor"]
            if not slot_id:
                vr_structured_complete = False
                vr_opening_sequence_complete = False
                add_visual_research_issue(
                    f"Visual research opening_sequence slot {slot_index} is missing `slot_id`.",
                    blocking=vr_gate_required,
                )
                continue
            if slot_id in opening_slot_lookup:
                vr_structured_complete = False
                vr_opening_sequence_complete = False
                add_visual_research_issue(
                    f"Visual research opening_sequence has duplicate slot_id `{slot_id}`.",
                    blocking=vr_gate_required,
                )
                continue
            if not display_label:
                vr_structured_complete = False
                vr_opening_sequence_complete = False
                add_visual_research_issue(
                    f"Visual research opening_sequence slot `{slot_id}` is missing `display_label`.",
                    blocking=vr_gate_required,
                )
            if slot_role not in {"supporting_object", "subject_object"}:
                vr_structured_complete = False
                vr_opening_sequence_complete = False
                add_visual_research_issue(
                    f"Visual research opening_sequence slot `{slot_id}` has invalid role `{slot_role}`.",
                    blocking=vr_gate_required,
                )
                continue
            if object_scope not in OPENING_OBJECT_SCOPES:
                vr_structured_complete = False
                vr_opening_sequence_complete = False
                add_visual_research_issue(
                    f"Visual research opening_sequence slot `{slot_id}` has invalid object_scope `{object_scope}`.",
                    blocking=vr_gate_required,
                )
            if renderability not in OPENING_SLOT_RENDERABILITIES:
                vr_structured_complete = False
                vr_opening_sequence_complete = False
                add_visual_research_issue(
                    f"Visual research opening_sequence slot `{slot_id}` has invalid renderability `{renderability}`.",
                    blocking=vr_gate_required,
                )
            opening_slot_lookup[slot_id] = slot
            if slot_role == "subject_object":
                opening_subject_slot_ids.append(slot_id)
                if slot_index != len(opening_slots):
                    vr_structured_complete = False
                    vr_opening_sequence_complete = False
                    add_visual_research_issue(
                        "Visual research opening_sequence subject_object slot must be the final opening slot.",
                        blocking=vr_gate_required,
                    )
            else:
                supporting_slot_count += 1
                if opening_subject_slot_ids:
                    vr_structured_complete = False
                    vr_opening_sequence_complete = False
                    add_visual_research_issue(
                        "Visual research opening_sequence cannot place supporting_object slots after the subject_object slot.",
                        blocking=vr_gate_required,
                    )
                if object_scope == "generic_mass_market":
                    generic_mass_market_supporting_slot_ids.append(slot_id)
                if opening_object_strategy == "generic_era_cluster":
                    if object_scope != "generic_mass_market":
                        vr_structured_complete = False
                        vr_opening_sequence_complete = False
                        add_visual_research_issue(
                            f"Generic-era opening supporting slot `{slot_id}` must use object_scope=`generic_mass_market`.",
                            blocking=vr_gate_required,
                        )
                    if renderability != "common_iconic":
                        vr_structured_complete = False
                        vr_opening_sequence_complete = False
                        add_visual_research_issue(
                            f"Generic-era opening supporting slot `{slot_id}` must use renderability=`common_iconic`.",
                            blocking=vr_gate_required,
                        )
                    if not visual_descriptor:
                        vr_structured_complete = False
                        vr_opening_sequence_complete = False
                        add_visual_research_issue(
                            f"Generic-era opening supporting slot `{slot_id}` is missing `visual_descriptor`.",
                            blocking=vr_gate_required,
                        )
        if supporting_slot_count != len(opening_supporting_objects):
            vr_structured_complete = False
            vr_opening_sequence_complete = False
            add_visual_research_issue(
                "Visual research opening_sequence slots must include one supporting_object slot per named supporting object.",
                blocking=vr_gate_required,
            )
        if len(opening_subject_slot_ids) != 1:
            vr_structured_complete = False
            vr_opening_sequence_complete = False
            add_visual_research_issue(
                "Visual research opening_sequence must include exactly one subject_object slot.",
                blocking=vr_gate_required,
            )
        if opening_object_strategy == "generic_era_cluster":
            if len(generic_mass_market_supporting_slot_ids) < 4:
                vr_structured_complete = False
                vr_opening_sequence_complete = False
                add_visual_research_issue(
                    "Generic-era opening_sequence needs at least 4 generic_mass_market supporting_object slots before the subject_object slot.",
                    blocking=vr_gate_required,
                )
            if opening_subject_slot_ids:
                subject_slot = opening_slot_lookup.get(opening_subject_slot_ids[0], {})
                if str(subject_slot.get("renderability", "")).strip() != "common_iconic":
                    vr_structured_complete = False
                    vr_opening_sequence_complete = False
                    add_visual_research_issue(
                        "Generic-era opening_sequence subject_object slot must use renderability=`common_iconic`.",
                        blocking=vr_gate_required,
                    )
                if not str(subject_slot.get("visual_descriptor", "")).strip():
                    vr_structured_complete = False
                    vr_opening_sequence_complete = False
                    add_visual_research_issue(
                        "Generic-era opening_sequence subject_object slot is missing `visual_descriptor`.",
                        blocking=vr_gate_required,
                    )
    opening_act = next((act for act in vr_acts if str(act.get("id", "")).strip() == opening_act_id), None)
    opening_delivery_contract_enforced = vr_approval_status == "approved"
    if opening_act_id and opening_act is None:
        vr_structured_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            f"Visual research opening_sequence references unknown act `{opening_act_id}`.",
            blocking=vr_gate_required,
        )
    scene_lookup = build_scene_lookup(scene_items(manifest))
    if opening_delivery_contract_enforced and opening_planned_scene_id and opening_planned_scene_id not in scene_lookup:
        vr_scene_coverage_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            f"Visual research opening_sequence planned_scene_id `{opening_planned_scene_id}` does not resolve to a scene item.",
            blocking=vr_gate_required,
        )
    motion_lookup = {
        str(item.get("id", "")).strip(): item
        for item in motion_items(manifest)
        if str(item.get("id", "")).strip()
    }
    if opening_delivery_contract_enforced and opening_planned_motion_id:
        motion_item = motion_lookup.get(opening_planned_motion_id)
        if motion_item is None:
            vr_motion_coverage_complete = False
            vr_opening_sequence_complete = False
            add_visual_research_issue(
                f"Visual research opening_sequence planned_motion_id `{opening_planned_motion_id}` does not resolve to a motion item.",
                blocking=vr_gate_required,
            )
        elif not str(motion_item.get("behavior", "")).strip():
            vr_motion_coverage_complete = False
            vr_opening_sequence_complete = False
            add_visual_research_issue(
                f"Visual research opening_sequence motion item `{opening_planned_motion_id}` is missing `behavior`.",
                blocking=vr_gate_required,
            )
        elif opening_planned_scene_id and str(motion_item.get("source_still_id", "")).strip() != opening_planned_scene_id:
            vr_motion_coverage_complete = False
            vr_opening_sequence_complete = False
            add_visual_research_issue(
                f"Visual research opening_sequence motion item `{opening_planned_motion_id}` must source still `{opening_planned_scene_id}`.",
                blocking=vr_gate_required,
            )
    if opening_declared and opening_min_duration_seconds < 5.0:
        vr_structured_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            "Visual research opening_sequence min_duration_seconds must be at least 5.0 seconds.",
            blocking=vr_gate_required,
        )
    opening_duration_resolved = bool(opening_timing.get("opening_duration_resolved"))
    opening_transcript_exists = bool(opening_timing.get("transcript_exists"))
    if opening_declared and opening_transcript_exists and not opening_duration_resolved:
        vr_structured_complete = False
        vr_opening_sequence_complete = False
        add_visual_research_issue(
            f"Visual research opening_sequence audio_end_cue_text `{opening_audio_end_cue_text or 'unset'}` does not resolve in the QA transcript.",
            path=str(opening_timing.get("transcript_path", "")).strip() or None,
            blocking=vr_gate_required,
        )
    vr_coverage_complete = vr_scene_coverage_complete and vr_motion_coverage_complete
    vr_approval_complete = vr_approval_status == "approved" and not vr_script_sha_mismatch
    lanes["visual_research"]["docs_complete"] = vr_docs_complete
    lanes["visual_research"]["structured_complete"] = vr_structured_complete
    lanes["visual_research"]["coverage_complete"] = vr_coverage_complete
    lanes["visual_research"]["opening_sequence_complete"] = vr_opening_sequence_complete
    lanes["visual_research"]["approval_status"] = vr_approval_status
    lanes["visual_research"]["approval_complete"] = vr_approval_complete
    lanes["visual_research"]["script_sha_mismatch"] = vr_script_sha_mismatch
    lanes["visual_research"]["opening_audio_start_seconds"] = float(opening_timing.get("opening_audio_start_seconds", 0.0) or 0.0)
    lanes["visual_research"]["opening_audio_end_seconds"] = float(opening_timing.get("opening_audio_end_seconds", 0.0) or 0.0)
    lanes["visual_research"]["opening_cue_duration_seconds"] = float(opening_timing.get("opening_cue_duration_seconds", 0.0) or 0.0)
    lanes["visual_research"]["opening_min_duration_seconds"] = float(opening_timing.get("opening_min_duration_seconds", opening_min_duration_seconds) or 0.0)
    lanes["visual_research"]["opening_duration_seconds"] = float(opening_timing.get("opening_duration_seconds", 0.0) or 0.0)
    lanes["visual_research"]["opening_duration_source"] = str(opening_timing.get("opening_duration_source", "")).strip()
    lanes["visual_research"]["opening_duration_resolved"] = opening_duration_resolved
    lanes["visual_research"]["opening_duration_extended"] = bool(opening_timing.get("opening_duration_extended"))
    lanes["visual_research"]["opening_duration_resolution_reason"] = str(opening_timing.get("resolution_reason", "")).strip()
    lanes["visual_research"]["act_count"] = int(visual_research.get("act_count", len(vr_acts)) or 0)
    lanes["visual_research"]["beat_count_total"] = int(visual_research.get("beat_count_total", 0) or 0)
    lanes["visual_research"]["required_motion_total"] = int(visual_research.get("required_motion_total", 0) or 0)
    lanes["visual_research"]["planned_motion_total"] = int(visual_research.get("planned_motion_total", 0) or 0)
    latest_reject_tags = [
        str(tag).strip()
        for tag in vr_guardrails.get("latest_reject_tags", [])
        if str(tag).strip()
    ]
    source_inventory = visual_research.get("_source_inventory", {})
    source_inventory_sources = list(source_inventory.get("sources", [])) if isinstance(source_inventory, dict) else []
    source_inventory_summary = source_inventory.get("summary", {}) if isinstance(source_inventory, dict) else {}
    source_inventory_errors = [
        str(error).strip()
        for error in (source_inventory.get("errors", []) if isinstance(source_inventory, dict) else [])
        if str(error).strip()
    ]
    unresolved_source_ids = [
        str(source_id).strip()
        for source_id in source_inventory_summary.get("unresolved_source_ids", [])
        if str(source_id).strip()
    ]
    blocked_source_ids = [
        str(source_id).strip()
        for source_id in source_inventory_summary.get("blocked_source_ids", [])
        if str(source_id).strip()
    ]
    missing_downstream_source_ids = [
        str(source_id).strip()
        for source_id in source_inventory_summary.get("missing_downstream_source_ids", [])
        if str(source_id).strip()
    ]
    source_origin_policy = str(visual_research.get("source_origin_policy", "any")).strip() or "any"
    fresh_web_missing_source_url_ids: list[str] = []
    fresh_web_missing_raw_asset_ids: list[str] = []
    fresh_web_invalid_origin_ids: list[str] = []
    fresh_web_generated_select_ids: list[str] = []
    fresh_web_missing_display_asset_ids: list[str] = []
    fresh_web_duplicate_display_source_ids: list[str] = []
    if source_origin_policy not in SOURCE_ORIGIN_POLICIES:
        source_inventory_errors.append(f"Unsupported visual research source_origin_policy `{source_origin_policy}`.")
        source_origin_policy = "any"
    if source_origin_policy == "fresh_web_only":
        display_path_to_source_ids: dict[str, list[str]] = {}
        entry_by_source_id: dict[str, dict[str, Any]] = {}
        for entry in source_inventory_sources:
            source_id = str(entry.get("source_id", "")).strip()
            if not source_id:
                continue
            entry_by_source_id[source_id] = entry
            if not str(entry.get("source_url", "")).strip():
                fresh_web_missing_source_url_ids.append(source_id)
            raw_asset_path = str(entry.get("raw_asset_path", "")).strip()
            if not raw_asset_path or not path_exists(raw_asset_path):
                fresh_web_missing_raw_asset_ids.append(source_id)
            if str(entry.get("source_origin", "")).strip() != "web_fresh":
                fresh_web_invalid_origin_ids.append(source_id)
            display_path = display_asset_path(entry)
            if not display_path or not path_exists(display_path):
                fresh_web_missing_display_asset_ids.append(source_id)
                continue
            if _is_generated_episode_select_path(display_path, episode_id) or _is_generated_episode_select_path(raw_asset_path, episode_id):
                fresh_web_generated_select_ids.append(source_id)
            token = _normalized_path_token(display_path)
            if token:
                display_path_to_source_ids.setdefault(token, []).append(source_id)
        for source_ids in display_path_to_source_ids.values():
            if len(source_ids) < 2:
                continue
            if all(note_allows_duplicate_display(entry_by_source_id[source_id]) for source_id in source_ids):
                continue
            fresh_web_duplicate_display_source_ids.extend(source_ids)
    opening_candidate_min = int(vr_guardrails.get("opening_candidate_min", 0) or 0)
    opening_candidate_target = int(vr_guardrails.get("opening_candidate_target", 0) or 0)
    subject_candidate_min = int(vr_guardrails.get("subject_candidate_min", 0) or 0)
    act_candidate_min = int(vr_guardrails.get("act_candidate_min", 0) or 0)
    opening_candidate_total = int(vr_guardrails.get("opening_candidate_total", source_inventory_summary.get("opening_candidate_total", 0)) or 0)
    opening_subject_candidate_total = int(
        vr_guardrails.get("opening_subject_candidate_total", source_inventory_summary.get("opening_subject_candidate_total", 0)) or 0
    )
    opening_supporting_candidate_total = int(
        vr_guardrails.get("opening_supporting_candidate_total", source_inventory_summary.get("opening_supporting_candidate_total", 0)) or 0
    )
    raw_opening_slot_candidate_totals = vr_guardrails.get(
        "opening_slot_candidate_totals",
        source_inventory_summary.get("opening_slot_candidate_totals", {}),
    )
    opening_slot_candidate_totals = {
        str(slot_id).strip(): int(total or 0)
        for slot_id, total in (raw_opening_slot_candidate_totals.items() if isinstance(raw_opening_slot_candidate_totals, dict) else [])
        if str(slot_id).strip()
    }
    opening_subject_slot_id = str(vr_guardrails.get("opening_subject_slot_id", "")).strip() or (
        opening_subject_slot_ids[0] if len(opening_subject_slot_ids) == 1 else ""
    )
    missing_opening_slot_ids = [
        str(slot_id).strip()
        for slot_id in vr_guardrails.get("missing_opening_slot_ids", [])
        if str(slot_id).strip()
    ]
    raw_act_candidate_totals = vr_guardrails.get("act_candidate_totals", {})
    act_candidate_totals = {
        str(act_id).strip(): int(total or 0)
        for act_id, total in (raw_act_candidate_totals.items() if isinstance(raw_act_candidate_totals, dict) else [])
        if str(act_id).strip()
    }
    underfilled_coverage_ids = [
        str(coverage_id).strip()
        for coverage_id in vr_guardrails.get("underfilled_coverage_ids", [])
        if str(coverage_id).strip()
    ]
    opening_slot_source_ids_missing_assignment: list[str] = []
    opening_slot_source_ids_invalid_assignment: list[str] = []
    opening_slot_role_mismatch_source_ids: list[str] = []
    generic_era_context_source_ids: list[str] = []
    if opening_slot_contract_enabled:
        for entry in source_inventory_sources:
            if str(entry.get("coverage_id", "")).strip() != "opening":
                continue
            source_id = str(entry.get("source_id", "")).strip()
            opening_slot_id = str(entry.get("opening_slot_id", "")).strip()
            if not opening_slot_id:
                opening_slot_source_ids_missing_assignment.append(source_id)
                continue
            slot = opening_slot_lookup.get(opening_slot_id)
            if slot is None:
                opening_slot_source_ids_invalid_assignment.append(source_id)
                continue
            expected_candidate_role = "opening_subject" if slot["role"] == "subject_object" else "opening_supporting"
            candidate_role = str(entry.get("candidate_role", "")).strip()
            if candidate_role != expected_candidate_role:
                opening_slot_role_mismatch_source_ids.append(source_id)
            if (
                opening_object_strategy == "generic_era_cluster"
                and str(slot.get("object_scope", "")).strip() == "generic_mass_market"
                and _looks_like_generic_era_context_imagery(
                    entry.get("candidate_label"),
                    entry.get("notes"),
                    entry.get("source_url"),
                )
            ):
                generic_era_context_source_ids.append(source_id)
    option_range_complete = not underfilled_coverage_ids
    source_policy_complete = not (
        fresh_web_missing_source_url_ids
        or fresh_web_missing_raw_asset_ids
        or fresh_web_invalid_origin_ids
        or fresh_web_generated_select_ids
        or fresh_web_missing_display_asset_ids
        or fresh_web_duplicate_display_source_ids
    )
    opening_slot_assignment_complete = not (
        opening_slot_source_ids_missing_assignment
        or opening_slot_source_ids_invalid_assignment
        or opening_slot_role_mismatch_source_ids
        or generic_era_context_source_ids
    )
    source_inventory_complete = (
        not source_inventory_errors
        and not unresolved_source_ids
        and option_range_complete
        and source_policy_complete
        and opening_slot_assignment_complete
    )
    lanes["visual_research"]["guardrails"] = {
        "signal_object": str(vr_guardrails.get("signal_object", "")).strip(),
        "banned_motifs": [
            str(item).strip()
            for item in vr_guardrails.get("banned_motifs", [])
            if str(item).strip()
        ],
        "opening_object_strategy": opening_object_strategy,
        "latest_reject_tags": latest_reject_tags,
        "machine_enforced_reject_tags": [
            tag for tag in latest_reject_tags if context.viz_repo.reject_tag_mode(tag) == "machine_enforced"
        ],
        "review_only_reject_tags": [
            tag for tag in latest_reject_tags if context.viz_repo.reject_tag_mode(tag) != "machine_enforced"
        ],
        "source_total": int(source_inventory_summary.get("source_total", 0) or 0),
        "approved_source_total": int(source_inventory_summary.get("approved_source_total", 0) or 0),
        "clear_source_total": int(source_inventory_summary.get("clear_source_total", 0) or 0),
        "cleaned_source_total": int(source_inventory_summary.get("cleaned_source_total", 0) or 0),
        "ready_source_total": int(source_inventory_summary.get("ready_source_total", 0) or 0),
        "opening_candidate_min": opening_candidate_min,
        "opening_candidate_target": opening_candidate_target,
        "subject_candidate_min": subject_candidate_min,
        "act_candidate_min": act_candidate_min,
        "opening_candidate_total": opening_candidate_total,
        "opening_subject_candidate_total": opening_subject_candidate_total,
        "opening_supporting_candidate_total": opening_supporting_candidate_total,
        "opening_subject_slot_id": opening_subject_slot_id,
        "opening_slot_candidate_totals": opening_slot_candidate_totals,
        "missing_opening_slot_ids": missing_opening_slot_ids,
        "act_candidate_totals": act_candidate_totals,
        "underfilled_coverage_ids": underfilled_coverage_ids,
        "ready_for_generation": bool(source_inventory_summary.get("ready_for_generation", False)),
        "unresolved_source_ids": unresolved_source_ids,
        "blocked_source_ids": blocked_source_ids,
        "missing_downstream_source_ids": missing_downstream_source_ids,
        "opening_slot_source_ids_missing_assignment": opening_slot_source_ids_missing_assignment,
        "opening_slot_source_ids_invalid_assignment": opening_slot_source_ids_invalid_assignment,
        "opening_slot_role_mismatch_source_ids": opening_slot_role_mismatch_source_ids,
        "generic_era_context_source_ids": generic_era_context_source_ids,
        "source_origin_policy": source_origin_policy,
        "fresh_web_missing_source_url_ids": fresh_web_missing_source_url_ids,
        "fresh_web_missing_raw_asset_ids": fresh_web_missing_raw_asset_ids,
        "fresh_web_invalid_origin_ids": fresh_web_invalid_origin_ids,
        "fresh_web_generated_select_ids": fresh_web_generated_select_ids,
        "fresh_web_missing_display_asset_ids": fresh_web_missing_display_asset_ids,
        "fresh_web_duplicate_display_source_ids": fresh_web_duplicate_display_source_ids,
        "source_inventory_errors": source_inventory_errors,
    }
    lanes["visual_research"]["source_inventory_complete"] = source_inventory_complete
    lanes["visual_research"]["option_range_complete"] = option_range_complete
    lanes["visual_research"]["source_origin_policy"] = source_origin_policy
    lanes["visual_research"]["source_policy_complete"] = source_policy_complete
    lanes["visual_research"]["opening_slot_contract_enabled"] = opening_slot_contract_enabled
    lanes["visual_research"]["opening_slot_assignment_complete"] = opening_slot_assignment_complete
    lanes["visual_research"]["opening_object_strategy"] = opening_object_strategy
    if source_inventory_errors:
        for error_message in source_inventory_errors:
            add_visual_research_issue(error_message, path=str(visual_research.get("source_inventory_path") or ""), blocking=vr_gate_required)
    if unresolved_source_ids:
        unresolved_label = ", ".join(unresolved_source_ids)
        add_visual_research_issue(
            f"Approved visual research sources still require text cleanup or downstream selection: {unresolved_label}.",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if opening_slot_source_ids_missing_assignment:
        add_visual_research_issue(
            "Opening tableau candidates are missing opening_slot_id assignments: "
            + ", ".join(opening_slot_source_ids_missing_assignment)
            + ".",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if opening_slot_source_ids_invalid_assignment:
        add_visual_research_issue(
            "Opening tableau candidates reference unknown opening slots: "
            + ", ".join(opening_slot_source_ids_invalid_assignment)
            + ".",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if opening_slot_role_mismatch_source_ids:
        add_visual_research_issue(
            "Opening tableau candidates must use candidate roles that match their opening slot role: "
            + ", ".join(opening_slot_role_mismatch_source_ids)
            + ".",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if generic_era_context_source_ids:
        add_visual_research_issue(
            "Generic-era opening slots must use isolated mass-market object references, not room/context imagery: "
            + ", ".join(generic_era_context_source_ids)
            + ".",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if source_origin_policy == "fresh_web_only":
        if fresh_web_missing_source_url_ids:
            add_visual_research_issue(
                "Fresh-web research candidates are missing source_url entries: " + ", ".join(fresh_web_missing_source_url_ids) + ".",
                path=str(visual_research.get("source_inventory_path") or ""),
                blocking=vr_gate_required,
            )
        if fresh_web_missing_raw_asset_ids:
            add_visual_research_issue(
                "Fresh-web research candidates are missing local raw_asset_path downloads: " + ", ".join(fresh_web_missing_raw_asset_ids) + ".",
                path=str(visual_research.get("source_inventory_path") or ""),
                blocking=vr_gate_required,
            )
        if fresh_web_invalid_origin_ids:
            add_visual_research_issue(
                "Fresh-web research candidates must use source_origin=`web_fresh`: " + ", ".join(fresh_web_invalid_origin_ids) + ".",
                path=str(visual_research.get("source_inventory_path") or ""),
                blocking=vr_gate_required,
            )
        if fresh_web_generated_select_ids:
            add_visual_research_issue(
                "Fresh-web research candidates cannot reuse prior generated selects: " + ", ".join(fresh_web_generated_select_ids) + ".",
                path=str(visual_research.get("source_inventory_path") or ""),
                blocking=vr_gate_required,
            )
        if fresh_web_missing_display_asset_ids:
            add_visual_research_issue(
                "Fresh-web research candidates must all render with real images; missing display assets for: "
                + ", ".join(fresh_web_missing_display_asset_ids)
                + ".",
                path=str(visual_research.get("source_inventory_path") or ""),
                blocking=vr_gate_required,
            )
        if fresh_web_duplicate_display_source_ids:
            add_visual_research_issue(
                "Fresh-web contact-sheet candidates must use unique displayed images unless notes explicitly allow duplicates: "
                + ", ".join(fresh_web_duplicate_display_source_ids)
                + ".",
                path=str(visual_research.get("source_inventory_path") or ""),
                blocking=vr_gate_required,
            )
    if opening_candidate_total < opening_candidate_min:
        add_visual_research_issue(
            f"Visual research opening tableau needs at least {opening_candidate_min} candidates; found {opening_candidate_total}.",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if opening_subject_candidate_total < subject_candidate_min:
        add_visual_research_issue(
            f"Visual research opening tableau needs at least {subject_candidate_min} subject candidates; found {opening_subject_candidate_total}.",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if missing_opening_slot_ids:
        opening_slot_display_lookup = {
            slot["slot_id"]: slot["display_label"] or slot["slot_id"]
            for slot in opening_slots
            if slot["slot_id"]
        }
        missing_slot_labels = [
            opening_slot_display_lookup.get(slot_id, slot_id)
            for slot_id in missing_opening_slot_ids
        ]
        add_visual_research_issue(
            "Visual research opening tableau needs at least one candidate for every named opening slot; missing: "
            + ", ".join(missing_slot_labels)
            + ".",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    if opening_subject_slot_id and int(opening_slot_candidate_totals.get(opening_subject_slot_id, 0) or 0) < subject_candidate_min:
        subject_slot_label = next(
            (
                slot["display_label"]
                for slot in opening_slots
                if slot["slot_id"] == opening_subject_slot_id
            ),
            opening_subject_slot_id,
        )
        add_visual_research_issue(
            f"Visual research opening subject slot `{subject_slot_label}` needs at least {subject_candidate_min} candidates; found {int(opening_slot_candidate_totals.get(opening_subject_slot_id, 0) or 0)}.",
            path=str(visual_research.get("source_inventory_path") or ""),
            blocking=vr_gate_required,
        )
    for act in vr_acts:
        act_id = str(act.get("id", "")).strip()
        if not act_id:
            continue
        candidate_total = int(act_candidate_totals.get(act_id, 0) or 0)
        if candidate_total < act_candidate_min:
            add_visual_research_issue(
                f"Visual research act `{act_id}` needs at least {act_candidate_min} source candidates; found {candidate_total}.",
                path=str(visual_research.get("source_inventory_path") or ""),
                blocking=vr_gate_required,
            )
    if vr_status == "done" and not (vr_docs_complete and vr_structured_complete and vr_coverage_complete and vr_approval_complete and source_inventory_complete):
        vr_status = "review"
        lanes["visual_research"]["status"] = vr_status
    if vr_script_sha_mismatch:
        add_issue(
            errors,
            "Locked script changed after visual research approval; refresh coverage and re-approve visual research.",
            lane="visual_research",
            path=str(visual_research.get("script_source_path") or script_path or ""),
        )
    elif vr_status in {"review", "done"} and vr_approval_status != "approved":
        add_issue(
            errors,
            f"Visual research approval is `{vr_approval_status}` and must be `approved` before downstream work can continue.",
            lane="visual_research",
        )

    audio = manifest.get("audio", {})
    audio_status = lanes["audio"]["status"]
    audio_eligible = lane_is_eligible(lanes, "audio")
    pipeline_dir = audio.get("pipeline_dir")
    master_path = audio.get("master_path")
    transcript_path = audio.get("transcript_path")
    master_exists = path_exists(master_path)
    transcript_exists = path_exists(transcript_path)
    audio_package = load_audio_package_metadata(pipeline_dir)
    package_promotable = audio_package_is_promotable(audio_package)
    package_sync_status = "unknown"
    if package_promotable:
        package_sync_status = "out_of_sync" if audio_package_differs_from_manifest(audio, audio_package) else "current"
    audio_review = audio.get("review", {})
    audio_review_status = str(audio_review.get("status", "pending")).strip() or "pending"
    audio_freshness_override = str(audio_review.get("freshness_override", "")).strip()
    if audio_review_status not in AUDIO_REVIEW_STATUSES:
        add_issue(
            errors,
            f"Audio review has invalid status `{audio_review_status}`.",
            lane="audio",
        )
    if audio_freshness_override not in AUDIO_FRESHNESS_OVERRIDES:
        add_issue(
            errors,
            f"Audio review freshness_override has invalid value `{audio_freshness_override}`.",
            lane="audio",
        )
    audio_done_at, _, _ = _resolve_audio_done_at(manifest)
    latest_research_anchor_at, latest_research_anchor_source = _resolve_latest_research_anchor(
        manifest,
        context=context,
        review_log_lookup=review_log_lookup,
    )
    lanes["audio"]["freshness"] = "not_ready"
    lanes["audio"]["done_at"] = _datetime_to_iso(audio_done_at) if audio_done_at else ""
    lanes["audio"]["research_anchor"] = latest_research_anchor_source
    lanes["audio"]["research_anchor_at"] = _datetime_to_iso(latest_research_anchor_at) if latest_research_anchor_at else ""
    lanes["audio"]["review_status"] = audio_review_status
    lanes["audio"]["freshness_override"] = audio_freshness_override
    lanes["audio"]["freshness_override_applied"] = False
    lanes["audio"]["review_ready"] = bool(master_exists and transcript_exists)
    lanes["audio"]["review_actionable"] = False
    lanes["audio"]["review_blocked_reason"] = ""
    lanes["audio"]["package_sync_status"] = package_sync_status
    lanes["audio"]["package_metadata_path"] = str(audio_package.get("metadata_path", "")).strip()
    lanes["audio"]["package_path"] = str(audio_package.get("packaged_path", "")).strip()
    lanes["audio"]["package_transcript_path"] = str(audio_package.get("transcript_path", "")).strip()
    lanes["audio"]["package_provider"] = str(audio_package.get("provider", "")).strip()
    lanes["audio"]["package_voice"] = str(audio_package.get("voice", "")).strip()
    lanes["audio"]["package_model"] = str(audio_package.get("model", "")).strip()
    lanes["audio"]["package_voice_profile_id"] = str(audio_package.get("voice_profile_id", "")).strip()
    lanes["audio"]["package_audio_disposition"] = str(audio_package.get("audio_disposition", "")).strip()
    lanes["audio"]["package_source_manifest_path"] = str(audio_package.get("effective_manifest_path", "")).strip()
    lanes["audio"]["package_qa_completed_at"] = str(audio_package.get("qa_completed_at", "")).strip()
    if audio_done_at and latest_research_anchor_at and audio_done_at < latest_research_anchor_at:
        lanes["audio"]["freshness"] = "stale"
        lanes["audio"]["review_blocked_reason"] = "Audio master predates the latest fact-check or approved visual research and must be rerendered before review."
    elif audio_done_at and latest_research_anchor_at is None:
        lanes["audio"]["freshness"] = "provisional"
        lanes["audio"]["review_blocked_reason"] = "Audio review is blocked until fact-checking or approved visual research confirms the current script."
    elif audio_done_at:
        lanes["audio"]["freshness"] = "current"
    if (
        lanes["audio"]["freshness"] == "stale"
        and audio_review_status == "approved"
        and audio_freshness_override == "waived"
    ):
        lanes["audio"]["freshness"] = "current"
        lanes["audio"]["freshness_override_applied"] = True
        lanes["audio"]["review_blocked_reason"] = ""
    if package_sync_status == "out_of_sync":
        lanes["audio"]["review_blocked_reason"] = (
            "Audio review is blocked until the latest packaged audio and QA transcript are promoted to the manifest-backed review asset."
        )
    if audio_status == "done":
        if audio_review_status != "approved":
            add_issue(
                errors,
                f"Audio review is `{audio_review_status}` and must be `approved` before the audio lane can be done.",
                lane="audio",
            )
        if not path_exists(pipeline_dir):
            add_issue(errors, "Audio pipeline directory is missing.", lane="audio", path=str(pipeline_dir))
        if not master_exists:
            add_issue(errors, "Final audio master is missing.", lane="audio", path=str(master_path))
        if not transcript_exists:
            add_issue(errors, "Audio QA transcript is missing.", lane="audio", path=str(transcript_path))
        if package_sync_status == "out_of_sync":
            add_issue(
                pending,
                f"Latest packaged audio is newer than the manifest-backed review asset; run `ce-orchestrate promote-audio {manifest['id']}` before further audio decisions.",
                lane="audio",
                path=str(audio_package.get("metadata_path") or audio_package.get("packaged_path") or master_path),
            )
        if lanes["audio"]["freshness"] == "stale":
            issue_bucket = errors if audio_eligible else pending
            add_issue(
                issue_bucket,
                "Audio master predates the latest fact-check or approved visual research and should be rerendered against the current locked script.",
                lane="audio",
                path=str(master_path) if master_path else None,
            )
        elif lanes["audio"]["freshness"] == "provisional":
            add_issue(
                pending,
                "Audio master exists, but there is no fact-check or approved visual research yet; treat it as provisional until research confirms the script.",
                lane="audio",
                path=str(master_path) if master_path else None,
            )
    elif audio_eligible and audio_status != "not_needed":
        if lanes["audio"]["freshness"] == "not_ready":
            lanes["audio"]["freshness"] = "pending"
        if pipeline_dir and not path_exists(pipeline_dir):
            add_issue(pending, "Audio pipeline directory is not ready yet.", lane="audio", path=str(pipeline_dir))
        if master_path and not master_exists:
            add_issue(pending, "Final audio master has not been rendered yet.", lane="audio", path=str(master_path))
        if transcript_path and not transcript_exists:
            add_issue(pending, "Audio QA transcript has not been generated yet.", lane="audio", path=str(transcript_path))
        if package_sync_status == "out_of_sync":
            add_issue(
                pending,
                f"Latest packaged audio is ready; run `ce-orchestrate promote-audio {manifest['id']}` before review.",
                lane="audio",
                path=str(audio_package.get("metadata_path") or audio_package.get("packaged_path") or master_path),
            )
        if master_exists and transcript_exists:
            if lanes["audio"]["freshness"] == "stale":
                issue_bucket = errors if audio_eligible else pending
                add_issue(
                    issue_bucket,
                    "Audio master predates the latest fact-check or approved visual research and should be rerendered against the current locked script.",
                    lane="audio",
                    path=str(master_path) if master_path else None,
                )
            elif lanes["audio"]["freshness"] == "provisional":
                add_issue(
                    pending,
                    "Audio master exists, but there is no fact-check or approved visual research yet; treat it as provisional until research confirms the script.",
                    lane="audio",
                    path=str(master_path) if master_path else None,
                )
            elif audio_review_status == "rejected":
                add_issue(
                    pending,
                    "Final audio review is rejected; address reviewer notes and resubmit the package for approval.",
                    lane="audio",
                    path=str(master_path),
                )
            elif package_sync_status == "out_of_sync":
                pass
            else:
                add_issue(
                    pending,
                    "Final audio is ready for human review.",
                    lane="audio",
                    path=str(master_path),
                )
            lanes["audio"]["review_actionable"] = (
                lanes["audio"]["freshness"] == "current" and package_sync_status != "out_of_sync"
            )
        elif master_exists and not transcript_exists:
            lanes["audio"]["review_blocked_reason"] = "Audio review is blocked until the QA transcript exists."
        elif not master_exists:
            lanes["audio"]["review_blocked_reason"] = "Audio review is blocked until the final master WAV exists."
    elif audio_status != "not_needed" and master_exists and transcript_exists:
        if lanes["audio"]["freshness"] == "stale":
            add_issue(
                pending,
                "Audio master predates the latest fact-check or approved visual research and should be rerendered against the current locked script.",
                lane="audio",
                path=str(master_path) if master_path else None,
            )
        elif lanes["audio"]["freshness"] == "provisional":
            add_issue(
                pending,
                "Audio master exists, but there is no fact-check or approved visual research yet; treat it as provisional until research confirms the script.",
                lane="audio",
                path=str(master_path) if master_path else None,
            )
    if lanes["audio"]["freshness"] in {"stale", "provisional"} or package_sync_status == "out_of_sync":
        lanes["audio"]["review_actionable"] = False

    scene_status = lanes["scene_stills"]["status"]
    scene_eligible = _lane_is_complete(str(lanes["visual_research"]["status"]))
    scene_data = scene_items(manifest)
    scene_lookup = build_scene_lookup(scene_data)
    required_scene_complete = True
    unresolved_scene_archetypes: list[dict[str, str]] = []
    approved_sources: list[str] = []
    for item in scene_data:
        item_id = str(item.get("id", ""))
        preset = str(item.get("preset", ""))
        archetype_status = str(item.get("archetype_status", "resolved" if preset else "unresolved"))
        archetype_id = str(item.get("archetype_id", ""))
        reference_dir = item.get("reference_dir")
        output_path = item.get("output_path")
        latest_render_path = item.get("latest_render_path")
        latest_render_manifest_path = item.get("latest_render_manifest_path")
        approved_proof_path = item.get("approved_proof_path")
        approved_proof_manifest_path = item.get("approved_proof_manifest_path")
        selected_asset = item.get("selected_asset")
        required = bool(item.get("required", True))
        review_status = str(item.get("review_status", "pending"))
        motion_review_status = str(item.get("motion_review_status", "not_planned"))
        motion_review_notes = str(item.get("motion_review_notes", "")).strip()
        if not item_id:
            add_issue(errors, "Scene still item is missing id.", lane="scene_stills")
            continue
        if archetype_status not in SCENE_ARCHETYPE_STATUSES:
            add_issue(errors, f"Scene still `{item_id}` has invalid archetype status `{archetype_status}`.", lane="scene_stills")
            continue
        if review_status not in REVIEW_STATUSES:
            add_issue(errors, f"Scene still `{item_id}` has invalid review status `{review_status}`.", lane="scene_stills")
        if motion_review_status not in MOTION_REVIEW_STATUSES:
            add_issue(errors, f"Scene still `{item_id}` has invalid motion review status `{motion_review_status}`.", lane="scene_stills")
        if motion_review_status == "approved_for_motion" and not motion_review_notes:
            add_issue(
                errors,
                f"Scene still `{item_id}` is approved_for_motion but missing motion_review_notes describing the approved behavior.",
                lane="scene_stills",
            )
        if archetype_status == "unresolved":
            unresolved_scene_archetypes.append({"item_id": item_id, "archetype_id": archetype_id})
            if lane_is_active(lanes, "scene_stills"):
                add_issue(errors, f"Scene still `{item_id}` cannot advance while its archetype is unresolved.", lane="scene_stills")
            elif scene_eligible:
                add_issue(pending, f"Scene still `{item_id}` still needs a resolved scene archetype.", lane="scene_stills")
        else:
            if not preset:
                add_issue(errors, f"Scene still `{item_id}` is missing preset metadata.", lane="scene_stills")
            if not reference_dir:
                add_issue(errors, f"Scene still `{item_id}` is missing reference_dir.", lane="scene_stills")
            if not output_path:
                add_issue(errors, f"Scene still `{item_id}` is missing output_path.", lane="scene_stills")
        if latest_render_path and not path_exists(latest_render_path):
            add_issue(errors, f"Scene still `{item_id}` latest render is missing.", lane="scene_stills", path=str(latest_render_path))
        if latest_render_manifest_path and not path_exists(latest_render_manifest_path):
            add_issue(errors, f"Scene still `{item_id}` latest render manifest is missing.", lane="scene_stills", path=str(latest_render_manifest_path))
        if bool(latest_render_path) != bool(latest_render_manifest_path):
            add_issue(errors, f"Scene still `{item_id}` latest render metadata is incomplete.", lane="scene_stills")
        if approved_proof_path and not path_exists(approved_proof_path):
            add_issue(errors, f"Scene still `{item_id}` approved proof is missing.", lane="scene_stills", path=str(approved_proof_path))
        if approved_proof_manifest_path and not path_exists(approved_proof_manifest_path):
            add_issue(
                errors,
                f"Scene still `{item_id}` approved proof manifest is missing.",
                lane="scene_stills",
                path=str(approved_proof_manifest_path),
            )
        if bool(approved_proof_path) != bool(approved_proof_manifest_path):
            add_issue(errors, f"Scene still `{item_id}` approved proof metadata is incomplete.", lane="scene_stills")
        if selected_asset and not path_exists(selected_asset):
            add_issue(errors, f"Scene still `{item_id}` selected asset is missing.", lane="scene_stills", path=str(selected_asset))
        if _motion_source_asset_path(item) and review_status == "approved":
            approved_sources.append(item_id)
        if required:
            is_complete = bool(selected_asset and review_status == "approved" and path_exists(selected_asset))
            required_scene_complete = required_scene_complete and is_complete
            if scene_status == "done" and not is_complete:
                add_issue(errors, f"Required scene still `{item_id}` is not approved with a selected asset.", lane="scene_stills")
            elif scene_eligible and scene_status != "done" and not is_complete:
                if _item_is_approved_but_unfinished(item):
                    add_issue(pending, f"Required scene still `{item_id}` still needs finalize.", lane="scene_stills")
                elif latest_render_path and path_exists(latest_render_path):
                    add_issue(pending, f"Required scene still `{item_id}` still needs review.", lane="scene_stills")
                elif archetype_status == "resolved":
                    add_issue(pending, f"Required scene still `{item_id}` still needs a render.", lane="scene_stills")
    lanes["scene_stills"]["required_complete"] = required_scene_complete
    lanes["scene_stills"]["unresolved_archetype_count"] = len(unresolved_scene_archetypes)

    packaging_status = lanes["packaging_stills"]["status"]
    packaging_eligible = _lane_is_complete(str(lanes["visual_research"]["status"]))
    packaging_data = packaging_items(manifest)
    required_packaging_complete = True
    for item in packaging_data:
        item_id = str(item.get("id", ""))
        kind = str(item.get("kind", ""))
        preset = str(item.get("preset", ""))
        reference_dir = item.get("reference_dir")
        output_path = item.get("output_path")
        latest_render_path = item.get("latest_render_path")
        latest_render_manifest_path = item.get("latest_render_manifest_path")
        approved_proof_path = item.get("approved_proof_path")
        approved_proof_manifest_path = item.get("approved_proof_manifest_path")
        selected_asset = item.get("selected_asset")
        required = bool(item.get("required", True))
        review_status = str(item.get("review_status", "pending"))
        if not item_id:
            add_issue(errors, "Packaging item is missing id.", lane="packaging_stills")
            continue
        if review_status not in REVIEW_STATUSES:
            add_issue(errors, f"Packaging item `{item_id}` has invalid review status `{review_status}`.", lane="packaging_stills")
            continue
        try:
            family = PACKAGING_KIND_TO_FAMILY[normalize_kind(kind)]
        except ValueError as exc:
            add_issue(errors, str(exc), lane="packaging_stills")
            continue
        if not preset or not context.viz_repo.spec_exists(family, preset):
            add_issue(errors, f"Packaging item `{item_id}` preset `{preset}` is missing from Viz specs.", lane="packaging_stills")
        if not reference_dir:
            add_issue(errors, f"Packaging item `{item_id}` is missing reference_dir.", lane="packaging_stills")
        if not output_path:
            add_issue(errors, f"Packaging item `{item_id}` is missing output_path.", lane="packaging_stills")
        if latest_render_path and not path_exists(latest_render_path):
            add_issue(errors, f"Packaging item `{item_id}` latest render is missing.", lane="packaging_stills", path=str(latest_render_path))
        if latest_render_manifest_path and not path_exists(latest_render_manifest_path):
            add_issue(errors, f"Packaging item `{item_id}` latest render manifest is missing.", lane="packaging_stills", path=str(latest_render_manifest_path))
        if bool(latest_render_path) != bool(latest_render_manifest_path):
            add_issue(errors, f"Packaging item `{item_id}` latest render metadata is incomplete.", lane="packaging_stills")
        if approved_proof_path and not path_exists(approved_proof_path):
            add_issue(errors, f"Packaging item `{item_id}` approved proof is missing.", lane="packaging_stills", path=str(approved_proof_path))
        if approved_proof_manifest_path and not path_exists(approved_proof_manifest_path):
            add_issue(
                errors,
                f"Packaging item `{item_id}` approved proof manifest is missing.",
                lane="packaging_stills",
                path=str(approved_proof_manifest_path),
            )
        if bool(approved_proof_path) != bool(approved_proof_manifest_path):
            add_issue(errors, f"Packaging item `{item_id}` approved proof metadata is incomplete.", lane="packaging_stills")
        if selected_asset and not path_exists(selected_asset):
            add_issue(errors, f"Packaging item `{item_id}` selected asset is missing.", lane="packaging_stills", path=str(selected_asset))
        if required:
            is_complete = bool(selected_asset and review_status == "approved" and path_exists(selected_asset))
            required_packaging_complete = required_packaging_complete and is_complete
            if packaging_status == "done" and not is_complete:
                add_issue(errors, f"Required packaging item `{item_id}` is not approved with a selected asset.", lane="packaging_stills")
            elif packaging_eligible and packaging_status != "done" and not is_complete:
                if _item_is_approved_but_unfinished(item):
                    add_issue(pending, f"Required packaging item `{item_id}` still needs finalize.", lane="packaging_stills")
                elif latest_render_path and path_exists(latest_render_path):
                    add_issue(pending, f"Required packaging item `{item_id}` still needs review.", lane="packaging_stills")
                else:
                    add_issue(pending, f"Required packaging item `{item_id}` still needs a render.", lane="packaging_stills")
    lanes["packaging_stills"]["required_complete"] = required_packaging_complete

    motion_status = lanes["motion_assets"]["status"]
    motion_eligible = bool(
        approved_sources
        and any(_item_is_approved_for_motion(scene_lookup[item_id]) for item_id in approved_sources)
    )
    motion_data = motion_items(manifest)
    motion_complete = True
    planned_motion_ids = {
        str(motion_id).strip()
        for act in vr_acts
        for motion_id in act.get("planned_motion_ids", [])
        if str(motion_id).strip()
    }
    opening_planned_motion_id = str(opening_sequence.get("planned_motion_id", "")).strip()
    for item in motion_data:
        item_id = str(item.get("id", ""))
        item_status = str(item.get("status", "todo"))
        authoring_mode = motion_item_authoring_mode(item)
        archetype_id = str(item.get("archetype_id", "")).strip()
        behavior = str(item.get("behavior", "")).strip()
        source_still_id = str(item.get("source_still_id", ""))
        workbench_project_path = str(item.get("workbench_project_path", "")).strip()
        output_path = item.get("output_path")
        latest_render_path = item.get("latest_render_path")
        latest_render_manifest_path = item.get("latest_render_manifest_path")
        if item_status not in MOTION_ITEM_STATUSES:
            add_issue(errors, f"Motion item `{item_id}` has invalid status `{item_status}`.", lane="motion_assets")
        if authoring_mode not in MOTION_AUTHORING_MODES:
            add_issue(errors, f"Motion item `{item_id}` has invalid authoring_mode `{authoring_mode}`.", lane="motion_assets")
            motion_complete = False
        if authoring_mode == "particle_workbench":
            if not workbench_project_path:
                add_issue(errors, f"Motion item `{item_id}` is missing workbench_project_path.", lane="motion_assets")
                motion_complete = False
            elif not path_exists(workbench_project_path):
                add_issue(errors, f"Motion item `{item_id}` workbench project is missing.", lane="motion_assets", path=workbench_project_path)
                motion_complete = False
        if archetype_id:
            find_motion_archetype(context, archetype_id)
        source_still = scene_lookup.get(source_still_id)
        if not source_still:
            add_issue(errors, f"Motion item `{item_id}` references unknown scene still `{source_still_id}`.", lane="motion_assets")
            motion_complete = False
            continue
        source_asset = _motion_source_asset_path(source_still)
        motion_review_status = source_still.get("motion_review_status")
        behavior_required = item_status in {"in_progress", "review", "done"} or (
            vr_status != "todo" and (item_id in planned_motion_ids or item_id == opening_planned_motion_id)
        )
        if behavior_required and not behavior and item_status != "not_needed":
            add_issue(errors, f"Motion item `{item_id}` is missing `behavior`.", lane="motion_assets")
            motion_complete = False
        if item_status in {"in_progress", "review", "done"}:
            if not source_asset:
                add_issue(
                    errors,
                    f"Motion item `{item_id}` source still `{source_still_id}` has no approved proof or selected asset.",
                    lane="motion_assets",
                )
            if motion_review_status != "approved_for_motion":
                add_issue(errors, f"Motion item `{item_id}` source still `{source_still_id}` is not approved for motion.", lane="motion_assets")
        if latest_render_path and not path_exists(latest_render_path):
            add_issue(errors, f"Motion item `{item_id}` latest render is missing.", lane="motion_assets", path=str(latest_render_path))
        if latest_render_manifest_path and not path_exists(latest_render_manifest_path):
            add_issue(errors, f"Motion item `{item_id}` latest render manifest is missing.", lane="motion_assets", path=str(latest_render_manifest_path))
        if item_status == "review" and (not latest_render_path or not latest_render_manifest_path):
            add_issue(pending, f"Motion item `{item_id}` is in review but is missing latest render metadata.", lane="motion_assets")
        if item_status == "done":
            if not path_exists(output_path):
                add_issue(errors, f"Motion item `{item_id}` output is missing.", lane="motion_assets", path=str(output_path))
        elif item_status not in {"not_needed"}:
            motion_complete = False
            if motion_eligible and output_path and not path_exists(output_path):
                add_issue(pending, f"Motion item `{item_id}` output is not rendered yet.", lane="motion_assets", path=str(output_path))
    if motion_status == "done" and not motion_complete:
        add_issue(errors, "Motion assets lane is marked done but not every motion item is complete.", lane="motion_assets")
    lanes["motion_assets"]["all_items_complete"] = motion_complete
    lanes["motion_assets"]["ready_for_assembly"] = motion_complete or motion_status == "not_needed"

    assembly = manifest.get("assembly", {})
    assembly_status = lanes["assembly"]["status"]
    master_video_path = str(assembly.get("master_video_path", "")).strip()
    assembly_plan = derive_act_spine(context, manifest)
    opening_duration_ready = (not opening_declared) or lanes["visual_research"].get("opening_duration_resolved", False)
    assembly_config_valid = True
    act_ids = [str(act.get("id", "")).strip() for act in manifest.get("visual_research", {}).get("acts", []) if str(act.get("id", "")).strip()]
    transition_pairs: set[tuple[str, str]] = set()
    if assembly_plan.renderer not in ALLOWED_ASSEMBLY_RENDERERS:
        add_issue(errors, f"Assembly renderer `{assembly_plan.renderer}` is unsupported.", lane="assembly")
        assembly_config_valid = False
    if assembly_plan.strategy not in ALLOWED_ASSEMBLY_STRATEGIES:
        add_issue(errors, f"Assembly strategy `{assembly_plan.strategy}` is unsupported.", lane="assembly")
        assembly_config_valid = False
    for transition in assembly_plan.transitions:
        boundary = (transition.from_act, transition.to_act)
        if not transition.from_act or not transition.to_act:
            add_issue(errors, "Assembly transition entries require both from_act and to_act.", lane="assembly")
            assembly_config_valid = False
            continue
        if transition.from_act not in act_ids or transition.to_act not in act_ids:
            add_issue(
                errors,
                f"Assembly transition `{transition.from_act}` -> `{transition.to_act}` references an unknown act.",
                lane="assembly",
            )
            assembly_config_valid = False
        if boundary in transition_pairs:
            add_issue(errors, f"Assembly transition `{transition.from_act}` -> `{transition.to_act}` is duplicated.", lane="assembly")
            assembly_config_valid = False
        transition_pairs.add(boundary)
        if transition.video not in ALLOWED_VIDEO_TRANSITIONS:
            add_issue(errors, f"Assembly transition `{transition.from_act}` -> `{transition.to_act}` has invalid video mode `{transition.video}`.", lane="assembly")
            assembly_config_valid = False
        if transition.audio not in ALLOWED_AUDIO_TRANSITIONS:
            add_issue(errors, f"Assembly transition `{transition.from_act}` -> `{transition.to_act}` has invalid audio mode `{transition.audio}`.", lane="assembly")
            assembly_config_valid = False
        if transition.video == "xfade" and transition.duration_seconds <= 0:
            add_issue(errors, f"Assembly transition `{transition.from_act}` -> `{transition.to_act}` needs duration_seconds > 0 for xfade.", lane="assembly")
            assembly_config_valid = False
        if transition.audio == "acrossfade" and transition.duration_seconds <= 0:
            add_issue(errors, f"Assembly transition `{transition.from_act}` -> `{transition.to_act}` needs duration_seconds > 0 for acrossfade.", lane="assembly")
            assembly_config_valid = False
    assembly_coverage_complete = assembly_config_valid and bool(assembly_plan.acts) and not assembly_plan.missing_act_ids
    assembly_input_ready = (
        lanes["audio"]["status"] == "done"
        and lanes["scene_stills"].get("required_complete")
        and lanes["packaging_stills"].get("required_complete")
        and lanes["motion_assets"].get("ready_for_assembly")
        and opening_duration_ready
    )
    ready_for_assembly = assembly_input_ready and assembly_coverage_complete
    lanes["assembly"]["renderer"] = assembly_plan.renderer
    lanes["assembly"]["strategy"] = assembly_plan.strategy
    lanes["assembly"]["output_path"] = str(assembly_plan.output_path)
    lanes["assembly"]["input_ready"] = assembly_input_ready
    lanes["assembly"]["opening_duration_resolved"] = bool(lanes["visual_research"].get("opening_duration_resolved", False))
    lanes["assembly"]["opening_duration_seconds"] = float(lanes["visual_research"].get("opening_duration_seconds", 0.0) or 0.0)
    lanes["assembly"]["coverage_complete"] = assembly_coverage_complete
    lanes["assembly"]["missing_act_ids"] = list(assembly_plan.missing_act_ids)
    lanes["assembly"]["ready_for_render"] = ready_for_assembly
    if assembly_plan.missing_act_ids and assembly_input_ready:
        add_issue(
            errors,
            "Assembly requires approved scene or motion coverage for every act. Missing: "
            + _format_missing_act_ids(assembly_plan.missing_act_ids),
            lane="assembly",
        )
    if opening_declared and lanes["audio"]["status"] == "done" and not opening_duration_ready:
        add_issue(
            errors,
            f"Opening tableau duration is unresolved; audio_end_cue_text `{opening_audio_end_cue_text or 'unset'}` must match the QA transcript before assembly.",
            lane="assembly",
            path=str(opening_timing.get("transcript_path", "")).strip() or None,
        )
    if assembly_status == "done":
        if not master_video_path:
            add_issue(errors, "Assembly lane is done but master_video_path is empty.", lane="assembly")
        elif not path_exists(master_video_path):
            add_issue(errors, "Assembly master video is missing.", lane="assembly", path=master_video_path)

    web = manifest.get("web", {})
    web_status = lanes["web"]["status"]
    web_entry_id = str(web.get("entry_id") or manifest.get("aliases", {}).get("web_entry_id", ""))
    web_entry = context.web_repo.get_launch_entry(web_entry_id) if web_entry_id else None
    if web_status not in {"todo", "not_needed"}:
        if not web_entry_id:
            add_issue(errors, "Web entry id is missing.", lane="web")
        elif not web_entry:
            add_issue(errors, f"Web entry id `{web_entry_id}` is not present in site-facts.ts.", lane="web")
        elif web_status != "done":
            add_issue(pending, f"Web entry `{web_entry_id}` exists but lane is not marked done.", lane="web")

    if lane_is_active(lanes, "scene_stills") and lanes["visual_research"]["status"] != "done":
        add_issue(errors, "Scene stills require visual research to be done first.", lane="scene_stills")
    if lane_is_active(lanes, "packaging_stills") and lanes["visual_research"]["status"] != "done":
        add_issue(errors, "Packaging stills require visual research to be done first.", lane="packaging_stills")
    if lane_is_active(lanes, "motion_assets"):
        approved_motion_sources = [item["id"] for item in scene_data if _item_is_approved_for_motion(item)]
        if not approved_motion_sources:
            add_issue(errors, "Motion assets require at least one still approved for motion.", lane="motion_assets")

    if assembly_status in {"in_progress", "review", "done"} and not ready_for_assembly:
        add_issue(errors, "Assembly requires final audio, required scene stills, required packaging stills, and motion completeness.", lane="assembly")
    elif lane_is_eligible(lanes, "assembly") and assembly_status != "done" and ready_for_assembly:
        add_issue(pending, "Assembly can start now.", lane="assembly")

    release = manifest.get("release", {})
    release_status = lanes["release"]["status"]
    scheduled_for = str(release.get("scheduled_for", "")).strip()
    published_at = str(release.get("published_at", "")).strip()
    release_notes_path = str(release.get("notes_path", "")).strip()
    release_notes_exists = path_exists(release_notes_path)
    release_youtube = release.get("youtube", {})
    release_podcast = release.get("podcast", {})
    lanes["release"]["notes_path"] = release_notes_path
    lanes["release"]["notes_exists"] = release_notes_exists
    lanes["release"]["youtube_status"] = str(release_youtube.get("status", "todo")).strip() or "todo"
    lanes["release"]["youtube_video_id"] = str(release_youtube.get("video_id", "")).strip()
    lanes["release"]["youtube_video_url"] = str(release_youtube.get("video_url", "")).strip()
    lanes["release"]["podcast_status"] = str(release_podcast.get("status", "todo")).strip() or "todo"
    lanes["release"]["podcast_external_id"] = str(release_podcast.get("external_id", "")).strip()
    lanes["release"]["podcast_episode_url"] = str(release_podcast.get("episode_url", "")).strip()
    if release_status in {"in_progress", "review", "done"} and (
        lanes["assembly"]["status"] != "done" or lanes["web"]["status"] != "done"
    ):
        add_issue(errors, "Release requires assembly and web to be done.", lane="release")
    elif lane_is_eligible(lanes, "release") and not release_notes_exists:
        add_issue(pending, "Release publish notes are required before publish preparation can run.", lane="release", path=release_notes_path)
    elif lane_is_eligible(lanes, "release") and release_status != "done" and lanes["assembly"]["status"] == "done" and lanes["web"]["status"] == "done":
        add_issue(pending, "Release is the next lane after assembly and web.", lane="release")

    analytics_status = lanes["analytics"]["status"]
    if analytics_status in {"in_progress", "review", "done"} and not published_at:
        add_issue(errors, "Analytics cannot start until publish date is recorded.", lane="analytics")
    elif lane_is_eligible(lanes, "analytics") and analytics_status != "done" and published_at:
        add_issue(pending, "Analytics can start now that publish date is recorded.", lane="analytics")

    board_category = determine_board_category(lanes, scheduled_for=scheduled_for, published_at=published_at)
    next_action = determine_next_action(lanes, errors, ready_for_assembly, published_at)
    cycle_time = _build_cycle_time(manifest, context=context, next_action_lane=next_action["lane"])
    for issue in cycle_time["chronology_issues"]:
        add_issue(errors, str(issue["message"]), lane=str(issue["lane"]))
    next_action = determine_next_action(lanes, errors, ready_for_assembly, published_at)
    cycle_time["current_blocker_lane"] = next_action["lane"] if next_action["lane"] != "complete" else ""
    return {
        "episode_id": episode_id,
        "title": manifest.get("title"),
        "board_category": board_category,
        "generated_at": utc_now_iso(),
        "manifest_path": manifest.get("_manifest_path"),
        "lanes": lanes,
        "errors": errors,
        "pending": pending,
        "next_action": next_action,
        "cycle_time": cycle_time,
        "web_entry_id": web_entry_id,
        "unresolved_scene_archetypes": unresolved_scene_archetypes,
    }


def determine_board_category(lanes: dict[str, dict[str, Any]], *, scheduled_for: str, published_at: str) -> str:
    if published_at and lanes["analytics"]["status"] == "done":
        return "post_release"
    if published_at:
        return "published"
    if scheduled_for:
        return "scheduled"
    if lanes["assembly"]["status"] == "done" and lanes["web"]["status"] == "done":
        return "release_ready"
    if lanes["assembly"].get("ready_for_render"):
        return "ready_for_assembly"
    if any(lanes[lane.name]["status"] != "todo" for lane in LANE_DEFINITIONS):
        return "in_production"
    return "backlog"


def determine_next_action(
    lanes: dict[str, dict[str, Any]],
    errors: list[dict[str, Any]],
    ready_for_assembly: bool,
    published_at: str,
) -> dict[str, str]:
    if errors:
        first = errors[0]
        return {"lane": str(first.get("lane", "validation")), "reason": first["message"]}
    if lanes["visual_research"]["status"] != "done":
        if not lanes["visual_research"].get("docs_complete"):
            return {"lane": "visual_research", "reason": "Complete `fact_check.md` and the six visual research deliverables beside the locked script, including contact_sheet.pdf and source_inventory.json."}
        if not lanes["visual_research"].get("structured_complete"):
            return {"lane": "visual_research", "reason": "Translate the locked script into per-act visual research coverage."}
        if not lanes["visual_research"].get("source_inventory_complete"):
            if not lanes["visual_research"].get("option_range_complete", True):
                return {"lane": "visual_research", "reason": "Expand the opening tableau and per-act option board before continuing."}
            if not lanes["visual_research"].get("source_policy_complete", True):
                return {"lane": "visual_research", "reason": "Replace generated selects, empty slots, and stale provenance with fresh web-researched candidate images."}
            return {"lane": "visual_research", "reason": "Process approved research sources until every downstream image is text-clear or has a cleaned derivative."}
        if not lanes["visual_research"].get("coverage_complete"):
            return {"lane": "visual_research", "reason": "Add enough per-act still and motion planning, or approved exceptions, before continuing."}
        if not lanes["visual_research"].get("approval_complete"):
            return {"lane": "visual_research", "reason": "Approve the visual research coverage before downstream lanes continue."}
        return {"lane": "visual_research", "reason": "Move the approved visual research package to done."}
    if lanes["scene_stills"]["status"] != "done":
        if lanes["scene_stills"].get("unresolved_archetype_count"):
            return {"lane": "scene_stills", "reason": "Resolve the scene archetype before producing the required scene stills."}
        if lanes["scene_stills"]["status"] == "in_progress":
            return {"lane": "scene_stills", "reason": "Finalize the approved scene stills before assembly can continue."}
        return {"lane": "scene_stills", "reason": "Approve the required scene still proofs."}
    if lanes["packaging_stills"]["status"] != "done":
        if lanes["packaging_stills"]["status"] == "in_progress":
            return {"lane": "packaging_stills", "reason": "Finalize the approved thumbnail and shorts cover assets."}
        return {"lane": "packaging_stills", "reason": "Approve the required thumbnail and shorts cover proofs."}
    if lanes["audio"].get("package_sync_status") == "out_of_sync":
        return {"lane": "audio", "reason": "Promote the latest packaged audio and QA transcript before continuing review."}
    if lanes["audio"]["status"] != "done":
        if lanes["audio"].get("review_actionable"):
            if lanes["audio"].get("review_status") == "rejected":
                return {"lane": "audio", "reason": "Address the reviewer notes and re-approve the final audio package."}
            return {"lane": "audio", "reason": "Approve the final audio package."}
        return {
            "lane": "audio",
            "reason": "Run validate -> cost -> render -> guard -> merge -> qa, then promote-audio for the episode audio package.",
        }
    if lanes["motion_assets"]["status"] not in {"done", "not_needed"}:
        return {"lane": "motion_assets", "reason": "Render motion only from stills approved for motion."}
    if ready_for_assembly and lanes["assembly"]["status"] != "done":
        return {"lane": "assembly", "reason": "Assemble the episode cut from approved audio and visuals."}
    if lanes["web"]["status"] != "done":
        return {"lane": "web", "reason": "Finish the web launch metadata and site entry."}
    if lanes["release"]["status"] != "done":
        return {"lane": "release", "reason": "Prepare a local publish package, run publish-package-check, then upload an unlisted review draft with publish-package-upload."}
    if published_at and lanes["analytics"]["status"] != "done":
        return {"lane": "analytics", "reason": "Capture post-release analytics and notes."}
    return {"lane": "complete", "reason": "No blocking orchestration work remains."}


def format_state_summary(state: dict[str, Any]) -> str:
    lines = [f"{state['episode_id']}: {state['board_category']}", f"  next: {state['next_action']['lane']} - {state['next_action']['reason']}"]
    if state["errors"]:
        lines.append("  errors:")
        for issue in state["errors"]:
            lines.append(f"    - {issue['message']}")
    if state["pending"]:
        lines.append("  pending:")
        for issue in state["pending"]:
            lines.append(f"    - {issue['message']}")
    return "\n".join(lines)


def print_board(context: Context) -> int:
    manifests = list_episode_manifests(context)
    states = [derive_episode_state(manifest, context) for manifest in manifests]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for state in states:
        grouped.setdefault(state["board_category"], []).append(state)
    order = context.channel.get("defaults", {}).get("board_categories", [])
    lines: list[str] = []
    for category in order:
        entries = grouped.get(category, [])
        if entries:
            lines.append(f"{category}:")
            for entry in entries:
                status = entry["lanes"][entry["next_action"]["lane"]]["status"] if entry["next_action"]["lane"] in entry["lanes"] else "n/a"
                lines.append(f"  - {entry['episode_id']}: next={entry['next_action']['lane']} status={status}")
    if not lines:
        lines.append("No episodes found.")
    print("\n".join(lines))
    return 0


def allowed_repos_for_lane(context: Context, lane: str) -> list[str]:
    path_map = context.channel["paths"]
    for definition in LANE_DEFINITIONS:
        if definition.name == lane:
            return [path_map[key] for key in definition.allowed_repo_keys]
    return []


def render_brief(context: Context, manifest: dict[str, Any], lane: str) -> str:
    manifest = materialize_episode_manifest(context, manifest)
    title = manifest["title"]
    episode_info = context.episodes_repo.get_episode_info(str(manifest["id"]))
    fact_check_target = (
        episode_info.directory / "fact_check.md"
        if episode_info is not None
        else path_or_none(manifest.get("script", {}).get("path")).parent / "fact_check.md"
        if path_or_none(manifest.get("script", {}).get("path")) is not None
        else None
    )
    lines = [f"# {manifest['id']} {lane} brief", "", f"Goal: move `{title}` through `{lane}`.", "", "Allowed repos:"]
    for repo in allowed_repos_for_lane(context, lane):
        lines.append(f"- {repo}")
    lines.append("")

    if lane == "visual_research":
        research = manifest["visual_research"]
        approval = research.get("approval", {})
        opening = research.get("opening_sequence", {})
        guardrails = research.get("guardrails", {})
        act_candidate_totals = guardrails.get("act_candidate_totals", {}) if isinstance(guardrails.get("act_candidate_totals", {}), dict) else {}
        opening_slots = [slot for slot in opening.get("slots", []) if isinstance(slot, dict) and str(slot.get("slot_id", "")).strip()]
        opening_slot_candidate_totals = (
            guardrails.get("opening_slot_candidate_totals", {})
            if isinstance(guardrails.get("opening_slot_candidate_totals", {}), dict)
            else {}
        )
        opening_timing = research.get("_opening_timing", {}) if isinstance(research.get("_opening_timing", {}), dict) else {}
        opening_supporting = ", ".join(str(item).strip() for item in opening.get("supporting_objects", []) if str(item).strip()) or "unset"
        lines.extend(
            [
                "Inputs:",
                f"- Locked script: {manifest['script']['path']}",
                f"- Script source: {research.get('script_source_path', manifest['script']['path'])}",
                f"- Script sha256: {research.get('script_sha256', '') or 'unset'}",
                f"- Estimated runtime (seconds): {research.get('estimated_runtime_seconds', 0)}",
                f"- Act count: {research.get('act_count', 0)}",
                f"- Motion plan: planned={research.get('planned_motion_total', 0)} required={research.get('required_motion_total', 0)}",
                f"- Approval status: {approval.get('status', 'pending')}",
                f"- Opening object strategy: {opening.get('object_strategy', 'episode_specific_cluster') or 'episode_specific_cluster'}",
                f"- Opening period label: {opening.get('time_period_label', '') or 'unset'}",
                f"- Opening supporting objects: {opening_supporting}",
                f"- Opening subject object: {opening.get('subject_object', '') or 'unset'}",
                f"- Opening focus transition: {opening.get('focus_transition', '') or 'unset'}",
                f"- Opening subject action: {opening.get('subject_action', '') or 'unset'}",
                f"- Opening act/scene/motion: {opening.get('act_id', '') or 'unset'} / {opening.get('planned_scene_id', '') or 'unset'} / {opening.get('planned_motion_id', '') or 'unset'}",
                f"- Opening cue text: {opening.get('audio_end_cue_text', '') or 'unset'}",
                (
                    "- Opening duration: "
                    f"cue={float(opening_timing.get('opening_cue_duration_seconds', 0.0) or 0.0):.3f}s "
                    f"min={float(opening_timing.get('opening_min_duration_seconds', opening.get('min_duration_seconds', 0.0)) or 0.0):.3f}s "
                    f"resolved={('yes' if opening_timing.get('opening_duration_resolved') else 'no')} "
                    f"final={float(opening_timing.get('opening_duration_seconds', 0.0) or 0.0):.3f}s "
                    f"extended={('yes' if opening_timing.get('opening_duration_extended') else 'no')}"
                ),
                (
                    "- Opening slots: "
                    + (
                        "; ".join(
                            f"{slot.get('slot_id', '') or 'unset'}:{slot.get('display_label', '') or 'unset'}"
                            f" ({slot.get('role', '') or 'unset'})"
                            f" scope={slot.get('object_scope', '') or 'unset'}"
                            f" renderability={slot.get('renderability', '') or 'unset'}"
                            f" descriptor={slot.get('visual_descriptor', '') or 'unset'}"
                            f" [{int(opening_slot_candidate_totals.get(str(slot.get('slot_id', '')).strip(), 0) or 0)}]"
                            for slot in opening_slots
                        )
                        if opening_slots
                        else "legacy flat opening bucket"
                    )
                ),
                (
                    "- Opening option coverage: "
                    f"total={guardrails.get('opening_candidate_total', 0)}/{guardrails.get('opening_candidate_min', 0)} "
                    f"subject={guardrails.get('opening_subject_candidate_total', 0)}/{guardrails.get('subject_candidate_min', 0)} "
                    f"target={guardrails.get('opening_candidate_target', 0)}"
                ),
                f"- Fact-check target: {fact_check_target or 'unset'}",
                f"- Contact sheet target: {research.get('contact_sheet_path', '') or 'unset'}",
                f"- Source inventory target: {research.get('source_inventory_path', '') or 'unset'}",
                f"- Source origin policy: {research.get('source_origin_policy', 'any') or 'any'}",
                f"- Act breakdown target: {research['act_breakdown_path']}",
                f"- Reference notes target: {research['reference_notes_path']}",
                f"- Sources target: {research['sources_path']}",
                f"- Assembly notes target: {research['assembly_notes_path']}",
            ]
        )
        if episode_info and episode_info.fact_check_path:
            lines.append(f"- Fact-check status: present ({episode_info.fact_check_path})")
        else:
            lines.append("- Fact-check status: missing")
            if manifest.get("audio", {}).get("status") == "done":
                lines.append("- Existing audio should be treated as provisional until research confirms the script.")
        if research.get("acts"):
            lines.append("- Per-act coverage:")
            for act in research["acts"]:
                option_total = int(act_candidate_totals.get(str(act["id"]), 0) or 0)
                lines.append(
                    f"  - {act['id']}: options={option_total}/{guardrails.get('act_candidate_min', 0)} beats={act.get('beat_count', 0)} scenes={len(act.get('planned_scene_ids', []))} motions={len(act.get('planned_motion_ids', []))}/{act.get('required_motion_sequences', 0)} exception={'yes' if act.get('exception_reason') else 'no'}"
                )
        lines.extend(
            [
                "",
                "Definition of done:",
                "- `fact_check.md` and the six visual research files exist beside the script, including contact_sheet.pdf and source_inventory.json.",
                "- The contact sheet reads as an option board: 6 to 8 opening-period objects, at least 2 subject candidates, and at least 8 candidates per act.",
                "- When opening slots are defined, page 1 groups candidates by slot order so the named period objects lead into the focal subject object.",
                "- Generic-era opening strategies use common iconic mass-market objects before the final subject slot, with visual descriptors that are easy for the renderer to recognize.",
                "- The opening sequence specifies the period tableau, focal subject object, focus transition, subject action, the cue text that ends the opener, and the scene/motion ids that deliver it.",
                "- The opener duration resolves from the QA transcript cue and never drops below the 5.0s house floor.",
                "- Approved research sources are either text-clear or have a cleaned derivative recorded as downstream_asset_path in source_inventory.json.",
                "- Every act has structured coverage with beat-aware planned scene ids and enough planned motion ids or an explicit exception_reason.",
                "- visual_research.approval.status=approved and the stored script fingerprint still matches the locked script.",
            ]
        )
    elif lane == "audio":
        audio = manifest["audio"]
        review = audio.get("review", {})
        lines.extend(
            [
                "Inputs:",
                f"- Locked script: {manifest['script']['path']}",
                f"- Pipeline dir: {audio['pipeline_dir']}",
                f"- Guard dir: {context.audio_repo.guard_dir(audio['pipeline_dir']) if audio.get('pipeline_dir') else 'unset'}",
                f"- Mastering dir: {context.audio_repo.mastering_dir(audio['pipeline_dir']) if audio.get('pipeline_dir') else 'unset'}",
                f"- Canonical packaged final target: {episode_info.canonical_final_audio_path if episode_info else audio['master_path']}",
                f"- QA transcript target: {audio.get('transcript_path') or context.audio_repo.transcript_output_dir}",
                f"- Audio package metadata: {context.audio_repo.package_metadata_path(audio['pipeline_dir']) if audio.get('pipeline_dir') else 'unset'}",
                f"- Human review status: {review.get('status', 'pending')}",
                "- Freshness rule: rerun audio if fact-check or approved visual research lands after the current master.",
                "- Package sync rule: promote the latest packaged WAV and QA transcript before review when the pipeline sidecar is ahead of the manifest.",
                "",
                "Delegated workflow:",
                f"- {manifest.get('aliases', {}).get('audio_pipeline', 'episode_audio')}: {' -> '.join(context.audio_repo.FLOW_STEPS)}",
                "",
                "Definition of done:",
                "- The canonical packaged final WAV exists in the episode `final/` directory.",
                "- The QA transcript exists for the packaged final.",
                "- The packaged WAV and QA transcript have been promoted into the episode manifest.",
                "- A human reviewer has approved the final audio package.",
            ]
        )
    elif lane == "scene_stills":
        opening = manifest["visual_research"].get("opening_sequence", {})
        opening_timing = manifest["visual_research"].get("_opening_timing", {})
        opening_slots = [slot for slot in opening.get("slots", []) if isinstance(slot, dict)]
        lines.append("Inputs:")
        for item in scene_items(manifest):
            governance = context.viz_repo.find_text_governance("scene_still", str(item.get("preset", "")))
            suffix = f" governance={governance.governance_class}" if governance else ""
            lines.append(
                f"- {item['id']}: preset={item['preset']} output={item.get('output_path', 'unset')} latest={item.get('latest_render_path', 'none') or 'none'} selected={item.get('selected_asset', 'none')}{suffix}"
            )
        lines.extend(
            [
                f"- Opening sequence still target: {opening.get('planned_scene_id', '') or 'unset'} action={opening.get('subject_action', '') or 'unset'}",
                (
                    f"- Opening sequence duration target: {float(opening_timing.get('opening_duration_seconds', 0.0) or 0.0):.3f}s "
                    f"(cue={float(opening_timing.get('opening_cue_duration_seconds', 0.0) or 0.0):.3f}s "
                    f"min={float(opening_timing.get('opening_min_duration_seconds', opening.get('min_duration_seconds', 0.0)) or 0.0):.3f}s)"
                ),
            ]
        )
        if opening_slots:
            lines.append("- Opening tableau review checklist:")
            for slot in opening_slots:
                role = str(slot.get("role", "")).strip() or "supporting_object"
                display_label = str(slot.get("display_label", "")).strip() or str(slot.get("slot_id", "")).strip() or "unset"
                lines.append(f"  - visible read: {display_label} ({role})")
            lines.extend(
                [
                    "  - Challenger must be the largest and most central read.",
                    "  - No buildings, interiors, clocks, monitor walls, tiled panel grids, or readable text.",
                    "  - The composition must preserve a clean pull-in path from the surrounding objects into Challenger.",
                ]
            )
        lines.extend(
            [
                "",
                "Definition of done:",
                "- Every required scene still has a selected asset and review_status=approved.",
                "- Only stills with motion_review_status=approved_for_motion may feed motion.",
                "- Any still approved_for_motion records the approved subject-action behavior in motion_review_notes.",
            ]
        )
    elif lane == "packaging_stills":
        lines.append("Inputs:")
        for item in packaging_items(manifest):
            family = PACKAGING_KIND_TO_FAMILY.get(str(item.get("kind", "")), "")
            governance = context.viz_repo.find_text_governance(family, str(item.get("preset", ""))) if family else None
            suffix = f" governance={governance.governance_class}" if governance else ""
            lines.append(
                f"- {item['id']}: kind={item['kind']} preset={item['preset']} output={item.get('output_path', 'unset')} latest={item.get('latest_render_path', 'none') or 'none'} selected={item.get('selected_asset', 'none')}{suffix}"
            )
        lines.extend(["", "Definition of done:", "- Required thumbnail and shorts cover assets have selected approved outputs."])
    elif lane == "motion_assets":
        opening = manifest["visual_research"].get("opening_sequence", {})
        opening_timing = manifest["visual_research"].get("_opening_timing", {})
        approved_source_ids = {item["id"] for item in scene_items(manifest) if _item_is_approved_for_motion(item)}
        assembly_plan = derive_act_spine(context, manifest)
        overlay_motion_ids = {
            overlay.motion_asset_id
            for composition in assembly_plan.compositions
            for overlay in composition.overlays
        }
        base_asset_ids = {composition.base_asset_id for composition in assembly_plan.compositions}
        lines.append("Inputs:")
        lines.append(
            f"- Opening sequence motion target: {opening.get('planned_motion_id', '') or 'unset'} action={opening.get('subject_action', '') or 'unset'}"
        )
        lines.append(
            f"- Opening sequence duration target: {float(opening_timing.get('opening_duration_seconds', 0.0) or 0.0):.3f}s "
            f"(cue={float(opening_timing.get('opening_cue_duration_seconds', 0.0) or 0.0):.3f}s min={float(opening_timing.get('opening_min_duration_seconds', opening.get('min_duration_seconds', 0.0)) or 0.0):.3f}s)"
        )
        for item in motion_items(manifest):
            if item["source_still_id"] not in approved_source_ids:
                continue
            certification = context.viz_repo.find_motion_certification(str(manifest["id"]), str(item["id"]))
            certification_suffix = (
                f" certification=yes typography_metadata_expected={'yes' if certification.expected_typography_metadata else 'no'}"
                if certification
                else " certification=no"
            )
            authoring_mode = motion_item_authoring_mode(item)
            workbench_suffix = (
                f" project={item.get('workbench_project_path', '') or 'unset'}"
                if authoring_mode == "particle_workbench"
                else ""
            )
            composition_role = " role=overlay_fx" if item["id"] in overlay_motion_ids else " role=base_clip" if item["id"] in base_asset_ids else ""
            lines.append(
                f"- {item['id']}: mode={authoring_mode} archetype={item.get('archetype_id', '') or 'unset'} source={item['source_still_id']} behavior={item.get('behavior', '') or 'unset'} frames={item['frames']} pipeline={item['pipeline']} output={item['output_path']} latest={item.get('latest_render_path', 'none') or 'none'}{workbench_suffix}{certification_suffix}{composition_role}"
            )
        if not approved_source_ids:
            lines.append("- No stills are approved for motion yet.")
        lines.extend(
            [
                "",
                "Compositing-first prompt contract:",
                "- Base clip prompt: Create a restrained documentary-style base shot for later compositing. Keep camera motion minimal and stable. Preserve clear negative space for overlay elements. Do not add extra particles, smoke, captions, lens effects, or foreground clutter.",
                "- FX overlay prompt: Render only the plume or event element as an isolated overlay for compositing, with transparent background and no environment. Keep the motion bold, clean, and readable against alpha.",
                "- Global negatives: no text, subtitles, UI, baked-in background, full-frame fog wash, camera whip, dramatic reframing, edge-to-edge debris field, or independent environmental storytelling.",
                "",
                "Definition of done:",
                "- Each motion item uses a still approved_for_motion.",
                "- Each planned motion item carries a non-empty behavior describing the approved focus-and-action beat.",
                "- Workbench-authored motion items keep a valid workbench_project_path.",
                "- Completed motion items write their output files to the expected path.",
                "- Certification-matrix expectations are satisfied when a matching entry exists.",
            ]
        )
    elif lane == "assembly":
        assembly_plan = derive_act_spine(context, manifest)
        opening_timing = manifest["visual_research"].get("_opening_timing", {})
        lines.extend(
            [
                "Inputs:",
                f"- Audio master: {manifest['audio']['master_path']}",
                f"- Assembly notes: {manifest['visual_research']['assembly_notes_path']}",
                f"- Renderer: {manifest['assembly'].get('renderer', 'ffmpeg')}",
                f"- Strategy: {manifest['assembly'].get('strategy', 'act_spine')}",
                f"- Opening sequence scene/motion: {manifest['visual_research'].get('opening_sequence', {}).get('planned_scene_id', '') or 'unset'} / {manifest['visual_research'].get('opening_sequence', {}).get('planned_motion_id', '') or 'unset'}",
                f"- Opening duration target: {float(opening_timing.get('opening_duration_seconds', 0.0) or 0.0):.3f}s",
                f"- Final output target: {assembly_plan.output_path}",
                f"- Missing act coverage: {_format_missing_act_ids(assembly_plan.missing_act_ids) or 'none'}",
            ]
        )
        if assembly_plan.transitions:
            lines.append("- Declared act-boundary transitions:")
            for transition in assembly_plan.transitions:
                lines.append(
                    f"  - {transition.from_act} -> {transition.to_act}: video={transition.video} audio={transition.audio} duration={transition.duration_seconds}"
                )
        if assembly_plan.compositions:
            lines.append("- Declared Base + FX compositions:")
            for composition in assembly_plan.compositions:
                lines.append(
                    f"  - {composition.act_id} / {composition.base_asset_id}: overlays={len(composition.overlays)}"
                )
                for overlay in composition.overlays:
                    lines.append(
                        f"    - overlay={overlay.motion_asset_id} start={overlay.start_seconds:.3f}s duration={overlay.duration_seconds:.3f}s scale={overlay.scale:.3f} opacity={overlay.opacity:.3f} blend={overlay.blend_mode}"
                    )
        lines.extend(
            [
                "",
                "Definition of done:",
                "- Every act has approved scene or motion coverage in the act spine.",
                "- The final MP4 exists at assembly.master_video_path.",
                "- The assembly lane can be marked done by the agent-run ffmpeg pipeline.",
            ]
        )
    elif lane == "web":
        entry_id = str(manifest["web"]["entry_id"])
        entry = context.web_repo.get_launch_entry(entry_id)
        lines.extend(
            [
                "Inputs:",
                f"- Web entry id: {entry_id}",
                f"- Launch archive entry exists: {'yes' if entry else 'no'}",
                f"- Homepage visible now: {'yes' if entry and entry.homepage_visible else 'no'}",
                "",
                "Definition of done:",
                "- The launch archive entry exists in site-facts.ts.",
                "- Homepage visibility is treated separately and only flips on when the Web repo marks the episode as recorded.",
            ]
        )
    elif lane == "release":
        lines.extend(
            [
                "Inputs:",
                f"- Scheduled for: {manifest['release'].get('scheduled_for', '') or 'unset'}",
                f"- Publish notes: {manifest['release'].get('notes_path', '') or 'unset'}",
                f"- YouTube status: {manifest['release'].get('youtube', {}).get('status', 'todo')}",
                f"- Podcast status: {manifest['release'].get('podcast', {}).get('status', 'todo')}",
                "",
                "Definition of done:",
                "- A local publish package manifest exists for the target platform.",
                "- `publish-package-check <manifest_path>` passes for that package.",
                "- Private review upload ids/URLs and receipt paths are recorded; public release remains manual.",
            ]
        )
    elif lane == "analytics":
        lines.extend(["Inputs:", f"- Published at: {manifest['release'].get('published_at', '') or 'unset'}", "", "Definition of done:", "- Post-release notes and analytics are recorded."])
    else:
        raise SystemExit(f"Unsupported lane brief: {lane}")
    return "\n".join(lines)
