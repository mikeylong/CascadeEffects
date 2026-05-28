from __future__ import annotations

import copy
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestration.guardrails import infer_reject_tags, normalize_review_tags

from inbox_app.agents_bridge import (
    Context,
    build_scene_lookup,
    derive_episode_state,
    derive_packaging_lane_status,
    derive_scene_lane_status,
    list_episode_manifests,
    load_episode_manifest,
    materialize_episode_manifest,
    motion_items,
    path_exists,
    packaging_items,
    scene_items,
    utc_now_iso,
    write_episode_manifest,
    write_state_file,
    derive_motion_lane_status,
    promote_motion_proof,
    resolve_packaging_item,
    resolve_scene_item,
)


GATE_TYPES = {"visual_research", "audio", "scene_still", "motion_source", "packaging_still", "motion_asset"}
GROUP_KEYS = ("visual_research", "audio", "scene_stills", "packaging_stills", "motion_assets")
BLOCKED_VISUAL_RESEARCH_APPROVE_TOOLTIP = "blocked until visual research is approved"
BLOCKED_MOTION_SOURCE_REASON = "Blocked until the scene still review is approved."
LANE_LABELS = {
    "todo": "Not started",
    "in_progress": "In progress",
    "review": "Awaiting review",
    "done": "Done",
    "blocked": "Blocked",
    "not_needed": "Not needed",
    "archived": "Archived",
}
DECISION_LABELS = {
    "pending": "Pending",
    "approved": "Approved",
    "rejected": "Rejected",
    "approved_for_motion": "Approved for motion",
    "unapproved": "Approval removed",
    "recorded": "Recorded",
}
AUDIO_FRESHNESS_LABELS = {
    "current": "Current",
    "provisional": "Provisional",
    "stale": "Stale",
    "pending": "Pending",
    "not_ready": "Not ready",
}
AUDIO_PACKAGE_SYNC_LABELS = {
    "current": "Current",
    "out_of_sync": "Needs promotion",
    "unknown": "Unknown",
}


def _episode_guardrails(manifest: dict[str, Any]) -> dict[str, Any]:
    guardrails = manifest.get("visual_research", {}).get("guardrails", {})
    return copy.deepcopy(guardrails if isinstance(guardrails, dict) else {})


def _reject_tag_options(context: Context, gate_type: str) -> list[dict[str, str]]:
    if gate_type == "audio":
        return []
    return copy.deepcopy(context.viz_repo.reject_tag_options(gate_type))


def _normalize_action_tags(context: Context, gate_type: str, tags: list[str] | tuple[str, ...] | None) -> list[str]:
    if gate_type == "audio":
        return []
    allowed = set(context.viz_repo.allowed_reject_tags(gate_type))
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in tags or []:
        tag = str(raw_tag).strip()
        if not tag or tag in seen:
            continue
        if allowed and tag not in allowed:
            raise SystemExit(f"Reject tag `{tag}` is not allowed for gate `{gate_type}`.")
        seen.add(tag)
        normalized.append(tag)
    return normalized


def _thread_actions(
    *,
    approve: bool = False,
    reject: bool = False,
    unapprove: bool = False,
    unreject: bool = False,
) -> dict[str, bool]:
    return {
        "approve": bool(approve),
        "reject": bool(reject),
        "unapprove": bool(unapprove),
        "unreject": bool(unreject),
    }


def _blocked_thread_actions(*, approve: str | None = None) -> dict[str, str]:
    blocked_actions: dict[str, str] = {}
    if approve:
        blocked_actions["approve"] = str(approve)
    return blocked_actions


def _lane_status_for(state: dict[str, Any], lane: str, fallback: str = "") -> str:
    lane_state = state.get("lanes", {}).get(str(lane).strip(), {})
    return str(lane_state.get("status", fallback)).strip() or str(fallback).strip()


def _lane_label(status: str) -> str:
    normalized = str(status).strip()
    return LANE_LABELS.get(normalized, normalized.replace("_", " ").title())


def _decision_label(status: str) -> str:
    normalized = str(status).strip()
    return DECISION_LABELS.get(normalized, normalized.replace("_", " ").title())


def _freshness_label(status: str) -> str:
    normalized = str(status).strip()
    if not normalized:
        return ""
    return AUDIO_FRESHNESS_LABELS.get(normalized, normalized.replace("_", " ").title())


def _package_sync_label(status: str) -> str:
    normalized = str(status).strip()
    if not normalized:
        return ""
    return AUDIO_PACKAGE_SYNC_LABELS.get(normalized, normalized.replace("_", " ").title())


def _thread_status_fields(
    *,
    lane_status: str,
    decision_status: str,
    freshness_status: str = "",
    package_sync_status: str = "",
) -> dict[str, str]:
    normalized_lane = str(lane_status).strip()
    normalized_decision = str(decision_status).strip()
    normalized_freshness = str(freshness_status).strip()
    normalized_package_sync = str(package_sync_status).strip()
    return {
        "status": normalized_decision,
        "lane_status": normalized_lane,
        "lane_label": _lane_label(normalized_lane),
        "decision_status": normalized_decision,
        "decision_label": _decision_label(normalized_decision),
        "freshness_status": normalized_freshness,
        "freshness_label": _freshness_label(normalized_freshness),
        "package_sync_status": normalized_package_sync,
        "package_sync_label": _package_sync_label(normalized_package_sync),
    }


def default_reviewer_name(reviewer: str | None = None) -> str:
    value = str(reviewer or "").strip()
    if value:
        return value
    fallback = os.environ.get("USER", "").strip()
    return fallback or "reviewer"


def load_review_manifest(context: Context, episode_id: str) -> dict[str, Any]:
    manifest_path = context.root / "episodes" / f"{episode_id}.toml"
    if not manifest_path.exists():
        raise SystemExit(f"Unknown episode id: {episode_id}")
    return materialize_episode_manifest(context, load_episode_manifest(manifest_path))


def allowed_asset_roots(context: Context) -> list[Path]:
    roots: list[Path] = []
    for key, value in context.channel.get("paths", {}).items():
        if not key.endswith("_root"):
            continue
        root = Path(str(value)).expanduser().resolve()
        roots.append(root)
    return roots


def ensure_allowed_asset_path(context: Context, raw_path: str | Path) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise SystemExit("Asset preview path must be absolute.")
    resolved = path.resolve()
    for root in allowed_asset_roots(context):
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    raise SystemExit(f"Asset preview path is outside configured roots: {resolved}")


def review_log_path(context: Context, episode_id: str) -> Path:
    review_dir = context.root / "state" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    return review_dir / f"{episode_id}.jsonl"


def append_review_log(context: Context, episode_id: str, event: dict[str, Any]) -> Path:
    path = review_log_path(context, episode_id)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return path


def _history_gate_label(gate_type: str) -> str:
    if gate_type == "visual_research":
        return "Visual research"
    if gate_type == "audio":
        return "Audio"
    if gate_type == "scene_still":
        return "Scene still"
    if gate_type == "motion_source":
        return "Motion source"
    if gate_type == "packaging_still":
        return "Packaging still"
    if gate_type == "motion_asset":
        return "Motion asset"
    return gate_type.replace("_", " ")


def _history_item_label(event: dict[str, Any]) -> str:
    gate_type = str(event.get("gate_type", "")).strip()
    if gate_type == "visual_research":
        return "Visual research coverage"
    if gate_type == "audio":
        return "Final audio"
    for candidate in (event.get("after"), event.get("before")):
        if not isinstance(candidate, dict):
            continue
        purpose = str(candidate.get("purpose", "")).strip()
        if purpose:
            return purpose
        item_id = str(candidate.get("id", "")).strip()
        if item_id:
            return item_id
    item_id = str(event.get("item_id", "")).strip()
    if item_id and item_id != "visual_research":
        return item_id
    return _history_gate_label(gate_type)


def _serialize_review_history_event(event: dict[str, Any]) -> dict[str, Any]:
    episode_id = str(event.get("episode_id", "")).strip()
    gate_type = str(event.get("gate_type", "")).strip()
    item_id = str(event.get("item_id", "")).strip()
    decision = str(event.get("decision", "")).strip()
    proof_path = str(event.get("proof_path", "")).strip()
    if decision == "approve":
        status = "approved"
    elif decision == "reject":
        status = "rejected"
    elif decision == "unapprove":
        status = "unapproved"
    elif decision == "unreject":
        status = "review" if gate_type == "motion_asset" else "pending"
    else:
        status = decision
    tags = normalize_review_tags(event.get("tags"))
    if decision == "reject":
        tags = infer_reject_tags(episode_id, gate_type, item_id, current_tags=tags)
    return {
        "timestamp": str(event.get("timestamp", "")).strip(),
        "reviewer": str(event.get("reviewer", "")).strip(),
        "episode_id": episode_id,
        "lane": str(event.get("lane", "")).strip(),
        "gate_type": gate_type,
        "gate_label": _history_gate_label(gate_type),
        "item_id": item_id,
        "item_label": _history_item_label(event),
        "message_id": message_id_for(episode_id, gate_type, item_id),
        "decision": decision,
        "status": status,
        "decision_status": status,
        "decision_label": _decision_label(status),
        "notes": str(event.get("notes", "")).strip(),
        "tags": tags,
        "proof_path": proof_path,
        "proof_exists": path_exists(proof_path),
        "preview_type": _preview_type(proof_path) if proof_path else "file",
    }


def load_review_history(context: Context, episode_id: str) -> list[dict[str, Any]]:
    path = review_log_path(context, episode_id)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        events.append(_serialize_review_history_event(event))
    return events


def _preview_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return "image"
    if suffix in {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}:
        return "audio"
    if suffix in {".mp4", ".mov", ".m4v", ".webm"}:
        return "video"
    return "file"


def _visual_research_proof_path(visual_research: dict[str, Any]) -> str:
    for key in ("contact_sheet_path", "act_breakdown_path"):
        path = str(visual_research.get(key, "")).strip()
        if path:
            return path
    return ""


def _lane_issues(state: dict[str, Any], lane: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "errors": [issue for issue in state.get("errors", []) if issue.get("lane") == lane],
        "pending": [issue for issue in state.get("pending", []) if issue.get("lane") == lane],
    }


def _item_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        gate_type = str(item["gate_type"])
        counts[gate_type] = counts.get(gate_type, 0) + 1
    return counts


def message_id_for(episode_id: str, gate_type: str, item_id: str) -> str:
    return f"{episode_id}:{gate_type}:{item_id}"


def parse_message_id(message_id: str) -> tuple[str, str, str]:
    parts = str(message_id).split(":", 2)
    if len(parts) != 3 or not all(parts):
        raise SystemExit(f"Unknown message id: {message_id}")
    return parts[0], parts[1], parts[2]


def _history_group_key(episode_id: str, gate_type: str, item_id: str) -> tuple[str, str, str]:
    return str(episode_id), str(gate_type), str(item_id)


def _parse_timestamp(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _timestamp_order_value(value: str) -> float:
    stamp = _parse_timestamp(value)
    if stamp is None:
        return 0.0
    return stamp.astimezone(timezone.utc).timestamp()


def _path_updated_at(path_value: str) -> str:
    raw = str(path_value or "").strip()
    if not raw:
        return ""
    path = Path(raw).expanduser()
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _pick_latest_timestamp(values: list[str]) -> str:
    latest = ""
    latest_value = 0.0
    for candidate in values:
        order_value = _timestamp_order_value(candidate)
        if order_value >= latest_value:
            latest_value = order_value
            latest = candidate
    return latest


def _resolve_thread_updated_at(
    *,
    manifest_path: str,
    unread: bool,
    current_timestamps: list[str],
    history_entries: list[dict[str, Any]],
) -> str:
    current_latest = _pick_latest_timestamp(current_timestamps)
    history_latest = _pick_latest_timestamp([str(entry.get("timestamp", "")).strip() for entry in history_entries])
    manifest_latest = _path_updated_at(manifest_path)
    if unread:
        return current_latest or manifest_latest or history_latest
    return _pick_latest_timestamp([current_latest, history_latest, manifest_latest])


def _has_text_fields(*values: Any) -> bool:
    return any(str(value or "").strip() for value in values)


def _visual_research_done(manifest: dict[str, Any]) -> bool:
    return str(manifest.get("visual_research", {}).get("status", "")).strip() == "done"


def _visual_research_can_unreject(manifest: dict[str, Any]) -> bool:
    visual_research = manifest.get("visual_research", {})
    approval = visual_research.get("approval", {})
    return (
        str(visual_research.get("status", "")).strip() == "review"
        and str(approval.get("status", "")).strip() == "rejected"
    )


def _audio_can_unreject(manifest: dict[str, Any]) -> bool:
    audio = manifest.get("audio", {})
    review = audio.get("review", {})
    return (
        str(audio.get("status", "")).strip() == "review"
        and str(review.get("status", "")).strip() == "rejected"
    )


def _audio_can_unapprove(manifest: dict[str, Any]) -> bool:
    audio = manifest.get("audio", {})
    review = audio.get("review", {})
    return (
        str(audio.get("status", "")).strip() == "done"
        and str(review.get("status", "")).strip() == "approved"
        and path_exists(audio.get("master_path"))
        and path_exists(audio.get("transcript_path"))
    )


def _scene_reviewable(item: dict[str, Any]) -> bool:
    proof_path = _best_available_path(item.get("latest_render_path", ""))
    review_status = _effective_still_review_status(item)
    return bool(proof_path) and review_status in {"pending", "rejected"}


def _scene_can_unreject(item: dict[str, Any]) -> bool:
    return str(item.get("review_status", "")).strip() == "rejected" and bool(_best_available_path(item.get("latest_render_path", "")))


def _scene_can_unapprove(item: dict[str, Any]) -> bool:
    return _effective_still_review_status(item) == "approved" and bool(_approved_still_path(item))


def _motion_source_prerequisites(item: dict[str, Any]) -> bool:
    return _effective_still_review_status(item) == "approved" and bool(_approved_still_path(item))


def _motion_source_reviewable(item: dict[str, Any]) -> bool:
    motion_status = str(item.get("motion_review_status", "pending")).strip() or "pending"
    return _motion_source_prerequisites(item) and motion_status in {"pending", "rejected"}


def _motion_source_can_unreject(item: dict[str, Any]) -> bool:
    return str(item.get("motion_review_status", "")).strip() == "rejected"


def _motion_source_can_unapprove(item: dict[str, Any]) -> bool:
    return _effective_motion_review_status(item) == "approved_for_motion" and _motion_source_prerequisites(item)


def _best_available_path(*candidates: Any) -> str:
    normalized = [str(candidate).strip() for candidate in candidates if str(candidate).strip()]
    for candidate in normalized:
        if path_exists(candidate):
            return candidate
    return ""


def _approved_proof_path(item: dict[str, Any]) -> str:
    path = str(item.get("approved_proof_path", "")).strip()
    return path if path and path_exists(path) else ""


def _approved_still_path(item: dict[str, Any]) -> str:
    return _approved_proof_path(item) or _best_available_path(item.get("selected_asset", ""))


def _effective_still_review_status(item: dict[str, Any]) -> str:
    review_status = str(item.get("review_status", "pending")).strip() or "pending"
    if review_status == "approved" and not _approved_still_path(item):
        return "pending"
    return review_status


def _effective_motion_review_status(item: dict[str, Any]) -> str:
    motion_status = str(item.get("motion_review_status", "pending")).strip() or "pending"
    if motion_status == "approved_for_motion" and not _motion_source_prerequisites(item):
        return "pending"
    return motion_status


def _approved_still_manifest_path(item: dict[str, Any]) -> str:
    approved_proof_manifest = str(item.get("approved_proof_manifest_path", "")).strip()
    if approved_proof_manifest and path_exists(approved_proof_manifest):
        return approved_proof_manifest
    selected_asset = str(item.get("selected_asset", "")).strip()
    if selected_asset:
        selected_manifest = _selected_asset_manifest_path(selected_asset)
        if path_exists(selected_manifest):
            return selected_manifest
    return ""


def _still_thread_lane_status(item: dict[str, Any], fallback_lane_status: str) -> str:
    if _scene_can_unapprove(item) and not str(item.get("selected_asset", "")).strip():
        return "in_progress"
    return fallback_lane_status


def _motion_source_blocked_reason(item: dict[str, Any]) -> str:
    if _motion_source_prerequisites(item):
        return ""
    return BLOCKED_MOTION_SOURCE_REASON


def _motion_asset_prerequisites(manifest: dict[str, Any], item: dict[str, Any]) -> bool:
    source_still = build_scene_lookup(scene_items(manifest)).get(str(item.get("source_still_id", "")).strip())
    if source_still is None:
        return False
    return _motion_source_can_unapprove(source_still) and bool(_approved_still_path(source_still))


def _motion_asset_reviewable(item: dict[str, Any]) -> bool:
    return str(item.get("status", "todo")).strip() == "review"


def _motion_asset_can_unapprove(item: dict[str, Any]) -> bool:
    status = str(item.get("status", "todo")).strip()
    review_outcome = str(item.get("review_outcome", "")).strip()
    return status == "done" and review_outcome in {"", "approved"}


def _motion_asset_can_unreject(item: dict[str, Any]) -> bool:
    return str(item.get("review_outcome", "")).strip() == "rejected"


def _history_item_label_for_thread(
    gate_type: str,
    item_id: str,
    label: str,
    current_paths: dict[str, str],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    entry = history_entries[0] if history_entries else None
    preview_path = ""
    preview_type = "file"
    proof_path = ""
    proof_exists = False
    if entry:
        proof_path = str(entry.get("proof_path", "")).strip()
    if not proof_path:
        for candidate in (
            current_paths.get("preview_path", ""),
            current_paths.get("selected_asset", ""),
            current_paths.get("proof_path", ""),
        ):
            if str(candidate).strip():
                proof_path = str(candidate).strip()
                break
    if proof_path:
        preview_path = proof_path
        preview_type = _preview_type(proof_path)
        proof_exists = path_exists(proof_path)
    return {
        "gate_type": gate_type,
        "gate_label": _history_gate_label(gate_type),
        "item_id": item_id,
        "item_label": label,
        "proof_path": proof_path,
        "preview_path": preview_path,
        "preview_type": preview_type,
        "proof_exists": proof_exists,
    }


def _serialize_visual_research_thread(
    context: Context,
    manifest: dict[str, Any],
    state: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    visual_research = manifest.get("visual_research", {})
    lane_state = state.get("lanes", {}).get("visual_research", {})
    visual_status = str(visual_research.get("status", "")).strip()
    approval = visual_research.get("approval", {})
    actionable = visual_status == "review"
    unread = actionable and str(approval.get("status", "pending")).strip() not in {"approved", "rejected"}
    include = actionable or visual_status == "done" or _has_text_fields(
        approval.get("reviewer", ""),
        approval.get("reviewed_at", ""),
        approval.get("notes", ""),
    ) or bool(history_entries)
    if not include:
        return None
    docs: list[dict[str, Any]] = []
    for key, label in (
        ("contact_sheet_path", "Contact sheet"),
        ("source_inventory_path", "Source inventory"),
        ("act_breakdown_path", "Act breakdown"),
        ("reference_notes_path", "Reference notes"),
        ("sources_path", "Sources"),
        ("assembly_notes_path", "Assembly notes"),
    ):
        path = str(visual_research.get(key, "")).strip()
        docs.append(
            {
                "label": label,
                "path": path,
                "exists": path_exists(path),
                "preview_type": _preview_type(path) if path else "markdown",
            }
        )
    preview_path = _visual_research_proof_path(visual_research) or next((doc["path"] for doc in docs if doc["path"]), "")
    episode_id = str(manifest["id"])
    item_id = "visual_research"
    decision_status = str(approval.get("status", "pending")).strip() or "pending"
    lane_status = _lane_status_for(state, "visual_research", visual_status)
    source_guardrails = lane_state.get("guardrails", {}) if isinstance(lane_state, dict) else {}
    source_inventory_complete = bool(lane_state.get("source_inventory_complete", True))
    approve_blocked_reason = ""
    if actionable and not source_inventory_complete:
        unresolved = [
            str(source_id).strip()
            for source_id in source_guardrails.get("unresolved_source_ids", [])
            if str(source_id).strip()
        ]
        unresolved_label = f": {', '.join(unresolved)}" if unresolved else ""
        approve_blocked_reason = (
            "blocked until approved research sources are text-clear or cleaned" + unresolved_label
        )
    updated_at = _resolve_thread_updated_at(
        manifest_path=str(manifest.get("_manifest_path", "")),
        unread=unread,
        current_timestamps=[str(approval.get("reviewed_at", "")).strip()],
        history_entries=history_entries,
    )
    actions = _thread_actions(
        approve=actionable and not approve_blocked_reason,
        reject=actionable,
        unapprove=str(approval.get("status", "")).strip() == "approved" and visual_status == "done",
        unreject=_visual_research_can_unreject(manifest),
    )
    blocked_actions = _blocked_thread_actions(approve=approve_blocked_reason) if approve_blocked_reason else {}
    return {
        "message_id": message_id_for(episode_id, "visual_research", item_id),
        "episode_id": episode_id,
        "episode_title": str(manifest.get("title", "")),
        "gate_type": "visual_research",
        "gate_label": _history_gate_label("visual_research"),
        "lane": "visual_research",
        "item_id": item_id,
        "label": "Visual research coverage",
        "unread": unread,
        "read": not unread,
        "actionable": actionable,
        "actions": actions,
        "blocked_actions": blocked_actions,
        "updated_at": updated_at,
        "preview_type": _preview_type(preview_path) if preview_path else "markdown",
        "preview_path": preview_path,
        "proof_path": preview_path,
        "reviewer": str(approval.get("reviewer", "")).strip(),
        "reviewed_at": str(approval.get("reviewed_at", "")).strip(),
        "review_notes": str(approval.get("notes", "")).strip(),
        "review_tags": normalize_review_tags(approval.get("tags")),
        "reject_tag_options": _reject_tag_options(context, "visual_research"),
        "episode_guardrails": _episode_guardrails(manifest),
        "docs": docs,
        "acts": copy.deepcopy(list(visual_research.get("acts") or [])),
        "metrics": {
            "act_count": int(visual_research.get("act_count", 0) or 0),
            "beat_count_total": int(visual_research.get("beat_count_total", 0) or 0),
            "required_motion_total": int(visual_research.get("required_motion_total", 0) or 0),
            "planned_motion_total": int(visual_research.get("planned_motion_total", 0) or 0),
            "approved_source_total": int(source_guardrails.get("approved_source_total", 0) or 0),
            "clear_source_total": int(source_guardrails.get("clear_source_total", 0) or 0),
            "cleaned_source_total": int(source_guardrails.get("cleaned_source_total", 0) or 0),
            "ready_source_total": int(source_guardrails.get("ready_source_total", 0) or 0),
        },
        "source_inventory": {
            "complete": source_inventory_complete,
            "unresolved_source_ids": [
                str(source_id).strip()
                for source_id in source_guardrails.get("unresolved_source_ids", [])
                if str(source_id).strip()
            ],
            "blocked_source_ids": [
                str(source_id).strip()
                for source_id in source_guardrails.get("blocked_source_ids", [])
                if str(source_id).strip()
            ],
        },
        "issues": _lane_issues(state, "visual_research"),
        "history": copy.deepcopy(history_entries),
        "history_count": len(history_entries),
        **_thread_status_fields(
            lane_status=lane_status,
            decision_status=decision_status,
        ),
    }


def _serialize_audio_review_thread(
    context: Context,
    manifest: dict[str, Any],
    state: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    audio = manifest.get("audio", {})
    lane_state = state.get("lanes", {}).get("audio", {})
    review = audio.get("review", {})
    audio_status = str(audio.get("status", "")).strip()
    review_status = str(review.get("status", "pending")).strip() or "pending"
    lane_status = _lane_status_for(state, "audio", audio_status)
    freshness_status = str(lane_state.get("freshness", "")).strip()
    package_sync_status = str(lane_state.get("package_sync_status", "")).strip()
    proof_path = str(audio.get("master_path", "")).strip()
    transcript_path = str(audio.get("transcript_path", "")).strip()
    review_ready = bool(lane_state.get("review_ready"))
    blocked_reason = str(lane_state.get("review_blocked_reason", "")).strip()
    reviewable = review_ready and audio_status == "review" and not blocked_reason
    actionable = reviewable
    unread = reviewable and review_status == "pending"
    include = (
        audio_status in {"review", "done"}
        or _has_text_fields(review.get("reviewer", ""), review.get("reviewed_at", ""), review.get("notes", ""))
        or bool(history_entries)
    )
    if not include:
        return None
    updated_at = _resolve_thread_updated_at(
        manifest_path=str(manifest.get("_manifest_path", "")),
        unread=unread,
        current_timestamps=[str(review.get("reviewed_at", "")).strip()],
        history_entries=history_entries,
    )
    actions = _thread_actions(
        approve=reviewable,
        reject=reviewable,
        unapprove=_audio_can_unapprove(manifest),
        unreject=_audio_can_unreject(manifest) and not blocked_reason,
    )
    docs: list[dict[str, Any]] = []
    if transcript_path:
        docs.append(
            {
                "label": "QA transcript",
                "path": transcript_path,
                "exists": path_exists(transcript_path),
                "preview_type": _preview_type(transcript_path),
            }
        )
    return {
        "message_id": message_id_for(str(manifest["id"]), "audio", "audio"),
        "episode_id": str(manifest["id"]),
        "episode_title": str(manifest.get("title", "")),
        "gate_type": "audio",
        "gate_label": _history_gate_label("audio"),
        "lane": "audio",
        "item_id": "audio",
        "label": "Final audio",
        "unread": unread,
        "read": not unread,
        "actionable": actionable,
        "actions": actions,
        "updated_at": updated_at,
        "preview_type": _preview_type(proof_path or ".wav"),
        "preview_path": proof_path,
        "proof_path": proof_path,
        "reviewer": str(review.get("reviewer", "")).strip(),
        "reviewed_at": str(review.get("reviewed_at", "")).strip(),
        "review_notes": str(review.get("notes", "")).strip(),
        "review_tags": [],
        "reject_tag_options": [],
        "episode_guardrails": _episode_guardrails(manifest),
        "docs": docs,
        "issues": _lane_issues(state, "audio"),
        **(
            {"blocked_reason": blocked_reason}
            if blocked_reason and (audio_status == "review" or package_sync_status == "out_of_sync")
            else {}
        ),
        "audio_provider": str(lane_state.get("package_provider", "")).strip(),
        "audio_voice": str(lane_state.get("package_voice", "")).strip(),
        "audio_model": str(lane_state.get("package_model", "")).strip(),
        "audio_source_manifest_path": str(lane_state.get("package_source_manifest_path", "")).strip(),
        "audio_package_metadata_path": str(lane_state.get("package_metadata_path", "")).strip(),
        "history": copy.deepcopy(history_entries),
        "history_count": len(history_entries),
        **_thread_status_fields(
            lane_status=lane_status,
            decision_status=review_status,
            freshness_status=freshness_status,
            package_sync_status=package_sync_status,
        ),
    }


def _serialize_scene_review_item(
    context: Context,
    manifest: dict[str, Any],
    state: dict[str, Any],
    item: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    proof_path = _best_available_path(item.get("latest_render_path", ""))
    approved_proof_path = _approved_proof_path(item)
    selected_asset = _best_available_path(item.get("selected_asset", ""))
    review_status = _effective_still_review_status(item)
    reviewable = _scene_reviewable(item)
    actionable = reviewable
    unread = reviewable and review_status == "pending"
    include = bool(proof_path) or bool(selected_asset) or _has_text_fields(
        item.get("reviewer", ""),
        item.get("reviewed_at", ""),
        item.get("review_notes", ""),
    ) or bool(history_entries)
    if not include:
        return None
    label = str(item.get("purpose", "")).strip() or str(item.get("id", "")).strip()
    history_proof_path = str(history_entries[0].get("proof_path", "")).strip() if history_entries else ""
    preview_path = _best_available_path(approved_proof_path, selected_asset, proof_path, history_proof_path)
    thread_proof_path = approved_proof_path if review_status == "approved" and approved_proof_path else _best_available_path(proof_path, selected_asset, history_proof_path)
    updated_at = _resolve_thread_updated_at(
        manifest_path=str(manifest.get("_manifest_path", "")),
        unread=unread,
        current_timestamps=[str(item.get("reviewed_at", "")).strip()],
        history_entries=history_entries,
    )
    actions = _thread_actions(
        approve=reviewable and _visual_research_done(manifest),
        reject=reviewable,
        unapprove=_scene_can_unapprove(item),
        unreject=_scene_can_unreject(item),
    )
    blocked_actions = _blocked_thread_actions(
        approve=BLOCKED_VISUAL_RESEARCH_APPROVE_TOOLTIP if reviewable and not _visual_research_done(manifest) else None,
    )
    lane_status = _still_thread_lane_status(
        item,
        _lane_status_for(state, "scene_stills", str(manifest.get("scene_stills", {}).get("status", "")).strip()),
    )
    return {
        "message_id": message_id_for(str(manifest["id"]), "scene_still", str(item.get("id", "")).strip()),
        "episode_id": str(manifest["id"]),
        "episode_title": str(manifest.get("title", "")),
        "gate_type": "scene_still",
        "gate_label": _history_gate_label("scene_still"),
        "lane": "scene_stills",
        "item_id": str(item.get("id", "")).strip(),
        "label": label,
        "unread": unread,
        "read": not unread,
        "actionable": actionable,
        "actions": actions,
        "updated_at": updated_at,
        "preview_type": _preview_type(preview_path or ".png"),
        "preview_path": preview_path,
        "proof_path": thread_proof_path,
        "proof_manifest_path": _approved_still_manifest_path(item) if review_status == "approved" else (
            str(item.get("latest_render_manifest_path", "")).strip()
            if path_exists(item.get("latest_render_manifest_path", ""))
            else ""
        ),
        "approved_proof_path": approved_proof_path,
        "approved_proof_manifest_path": str(item.get("approved_proof_manifest_path", "")).strip(),
        "selected_asset": selected_asset,
        "required": bool(item.get("required", True)),
        "reviewer": str(item.get("reviewer", "")).strip(),
        "reviewed_at": str(item.get("reviewed_at", "")).strip(),
        "review_notes": str(item.get("review_notes", "")).strip(),
        "review_tags": normalize_review_tags(item.get("review_tags")),
        "reject_tag_options": _reject_tag_options(context, "scene_still"),
        "episode_guardrails": _episode_guardrails(manifest),
        **({"blocked_actions": blocked_actions} if blocked_actions else {}),
        "history": copy.deepcopy(history_entries),
        "history_count": len(history_entries),
        **_thread_status_fields(
            lane_status=lane_status,
            decision_status=review_status,
        ),
    }


def _serialize_motion_source_review_item(
    context: Context,
    manifest: dict[str, Any],
    state: dict[str, Any],
    item: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    approved_proof_path = _approved_proof_path(item)
    selected_asset = _best_available_path(item.get("selected_asset", ""))
    latest_render_path = _best_available_path(item.get("latest_render_path", ""))
    motion_status = _effective_motion_review_status(item)
    still_approved = _motion_source_prerequisites(item)
    blocked_reason = _motion_source_blocked_reason(item)
    history_proof_path = str(history_entries[0].get("proof_path", "")).strip() if history_entries else ""
    preview_path = _best_available_path(approved_proof_path, selected_asset, latest_render_path, history_proof_path)
    reviewable = still_approved and motion_status in {"pending", "rejected"}
    actionable = reviewable
    unread = reviewable and motion_status == "pending"
    include = (
        bool(approved_proof_path or selected_asset)
        or motion_status in {"pending", "rejected", "approved_for_motion"}
    ) and (
        still_approved
        or motion_status in {"pending", "rejected", "approved_for_motion"}
        or _has_text_fields(item.get("motion_reviewer", ""), item.get("motion_reviewed_at", ""), item.get("motion_review_notes", ""))
        or bool(history_entries)
    )
    if not include:
        return None
    label = str(item.get("purpose", "")).strip() or str(item.get("id", "")).strip()
    updated_at = _resolve_thread_updated_at(
        manifest_path=str(manifest.get("_manifest_path", "")),
        unread=unread,
        current_timestamps=[str(item.get("motion_reviewed_at", "")).strip()],
        history_entries=history_entries,
    )
    actions = (
        _thread_actions()
        if blocked_reason
        else _thread_actions(
            approve=reviewable,
            reject=reviewable,
            unapprove=_motion_source_can_unapprove(item),
            unreject=_motion_source_can_unreject(item),
        )
    )
    lane_status = _still_thread_lane_status(
        item,
        _lane_status_for(state, "scene_stills", str(manifest.get("scene_stills", {}).get("status", "")).strip()),
    )
    return {
        "message_id": message_id_for(str(manifest["id"]), "motion_source", str(item.get("id", "")).strip()),
        "episode_id": str(manifest["id"]),
        "episode_title": str(manifest.get("title", "")),
        "gate_type": "motion_source",
        "gate_label": _history_gate_label("motion_source"),
        "lane": "scene_stills",
        "item_id": str(item.get("id", "")).strip(),
        "label": label,
        "unread": unread,
        "read": not unread,
        "actionable": actionable,
        "actions": actions,
        "updated_at": updated_at,
        "preview_type": _preview_type(preview_path or ".png"),
        "preview_path": preview_path,
        "proof_path": preview_path,
        "approved_proof_path": approved_proof_path,
        "selected_asset": selected_asset,
        "reviewer": str(item.get("motion_reviewer", "")).strip(),
        "reviewed_at": str(item.get("motion_reviewed_at", "")).strip(),
        "review_notes": str(item.get("motion_review_notes", "")).strip(),
        "review_tags": normalize_review_tags(item.get("motion_review_tags")),
        "reject_tag_options": _reject_tag_options(context, "motion_source"),
        "episode_guardrails": _episode_guardrails(manifest),
        **({"blocked_reason": blocked_reason} if blocked_reason else {}),
        "history": copy.deepcopy(history_entries),
        "history_count": len(history_entries),
        **_thread_status_fields(
            lane_status=lane_status,
            decision_status=motion_status if motion_status else "pending",
        ),
    }


def _serialize_packaging_review_item(
    context: Context,
    manifest: dict[str, Any],
    state: dict[str, Any],
    item: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    proof_path = _best_available_path(item.get("latest_render_path", ""))
    approved_proof_path = _approved_proof_path(item)
    selected_asset = _best_available_path(item.get("selected_asset", ""))
    review_status = _effective_still_review_status(item)
    reviewable = _scene_reviewable(item)
    actionable = reviewable
    unread = reviewable and review_status == "pending"
    include = bool(proof_path) or bool(selected_asset) or _has_text_fields(
        item.get("reviewer", ""),
        item.get("reviewed_at", ""),
        item.get("review_notes", ""),
    ) or bool(history_entries)
    if not include:
        return None
    label = str(item.get("purpose", "")).strip() or str(item.get("id", "")).strip()
    history_proof_path = str(history_entries[0].get("proof_path", "")).strip() if history_entries else ""
    preview_path = _best_available_path(approved_proof_path, selected_asset, proof_path, history_proof_path)
    thread_proof_path = approved_proof_path if review_status == "approved" and approved_proof_path else _best_available_path(proof_path, selected_asset, history_proof_path)
    updated_at = _resolve_thread_updated_at(
        manifest_path=str(manifest.get("_manifest_path", "")),
        unread=unread,
        current_timestamps=[str(item.get("reviewed_at", "")).strip()],
        history_entries=history_entries,
    )
    actions = _thread_actions(
        approve=reviewable and _visual_research_done(manifest),
        reject=reviewable,
        unapprove=_scene_can_unapprove(item),
        unreject=_scene_can_unreject(item),
    )
    blocked_actions = _blocked_thread_actions(
        approve=BLOCKED_VISUAL_RESEARCH_APPROVE_TOOLTIP if reviewable and not _visual_research_done(manifest) else None,
    )
    lane_status = _still_thread_lane_status(
        item,
        _lane_status_for(state, "packaging_stills", str(manifest.get("packaging_stills", {}).get("status", "")).strip()),
    )
    return {
        "message_id": message_id_for(str(manifest["id"]), "packaging_still", str(item.get("id", "")).strip()),
        "episode_id": str(manifest["id"]),
        "episode_title": str(manifest.get("title", "")),
        "gate_type": "packaging_still",
        "gate_label": _history_gate_label("packaging_still"),
        "lane": "packaging_stills",
        "item_id": str(item.get("id", "")).strip(),
        "label": label,
        "unread": unread,
        "read": not unread,
        "actionable": actionable,
        "actions": actions,
        "updated_at": updated_at,
        "preview_type": _preview_type(preview_path or ".png"),
        "preview_path": preview_path,
        "proof_path": thread_proof_path,
        "proof_manifest_path": _approved_still_manifest_path(item) if review_status == "approved" else (
            str(item.get("latest_render_manifest_path", "")).strip()
            if path_exists(item.get("latest_render_manifest_path", ""))
            else ""
        ),
        "approved_proof_path": approved_proof_path,
        "approved_proof_manifest_path": str(item.get("approved_proof_manifest_path", "")).strip(),
        "selected_asset": selected_asset,
        "required": bool(item.get("required", True)),
        "reviewer": str(item.get("reviewer", "")).strip(),
        "reviewed_at": str(item.get("reviewed_at", "")).strip(),
        "review_notes": str(item.get("review_notes", "")).strip(),
        "review_tags": normalize_review_tags(item.get("review_tags")),
        "reject_tag_options": _reject_tag_options(context, "packaging_still"),
        "episode_guardrails": _episode_guardrails(manifest),
        **({"blocked_actions": blocked_actions} if blocked_actions else {}),
        "history": copy.deepcopy(history_entries),
        "history_count": len(history_entries),
        **_thread_status_fields(
            lane_status=lane_status,
            decision_status=review_status,
        ),
    }


def _serialize_motion_review_item(
    context: Context,
    manifest: dict[str, Any],
    state: dict[str, Any],
    item: dict[str, Any],
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    latest_render_path = str(item.get("latest_render_path", "")).strip()
    output_path = str(item.get("output_path", "")).strip()
    review_outcome = str(item.get("review_outcome", "")).strip()
    decision_status = review_outcome or "pending"
    reviewable = _motion_asset_reviewable(item)
    actionable = reviewable
    unread = reviewable
    include = bool(latest_render_path) or review_outcome in {"approved", "rejected"} or _has_text_fields(
        item.get("reviewer", ""),
        item.get("reviewed_at", ""),
        item.get("review_notes", ""),
    ) or bool(history_entries)
    if not include:
        return None
    preview_path = output_path if review_outcome == "approved" and path_exists(output_path) else latest_render_path or output_path
    updated_at = _resolve_thread_updated_at(
        manifest_path=str(manifest.get("_manifest_path", "")),
        unread=unread,
        current_timestamps=[str(item.get("reviewed_at", "")).strip()],
        history_entries=history_entries,
    )
    actions = _thread_actions(
        approve=reviewable and bool(latest_render_path) and _motion_asset_prerequisites(manifest, item),
        reject=reviewable and bool(latest_render_path),
        unapprove=_motion_asset_can_unapprove(item),
        unreject=_motion_asset_can_unreject(item),
    )
    lane_status = _lane_status_for(state, "motion_assets", str(manifest.get("motion_assets", {}).get("status", "")).strip())
    return {
        "message_id": message_id_for(str(manifest["id"]), "motion_asset", str(item.get("id", "")).strip()),
        "episode_id": str(manifest["id"]),
        "episode_title": str(manifest.get("title", "")),
        "gate_type": "motion_asset",
        "gate_label": _history_gate_label("motion_asset"),
        "lane": "motion_assets",
        "item_id": str(item.get("id", "")).strip(),
        "label": str(item.get("id", "")).strip(),
        "unread": unread,
        "read": not unread,
        "actionable": actionable,
        "actions": actions,
        "updated_at": updated_at,
        "preview_type": _preview_type(preview_path or ".mp4"),
        "preview_path": preview_path,
        "proof_path": latest_render_path,
        "proof_manifest_path": str(item.get("latest_render_manifest_path", "")).strip(),
        "output_path": output_path,
        "review_outcome": review_outcome,
        "reviewer": str(item.get("reviewer", "")).strip(),
        "reviewed_at": str(item.get("reviewed_at", "")).strip(),
        "review_notes": str(item.get("review_notes", "")).strip(),
        "review_tags": normalize_review_tags(item.get("review_tags")),
        "reject_tag_options": _reject_tag_options(context, "motion_asset"),
        "episode_guardrails": _episode_guardrails(manifest),
        "history": copy.deepcopy(history_entries),
        "history_count": len(history_entries),
        **_thread_status_fields(
            lane_status=lane_status,
            decision_status=decision_status,
        ),
    }


def _group_review_history(events: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for event in events:
        key = _history_group_key(
            str(event.get("episode_id", "")).strip(),
            str(event.get("gate_type", "")).strip(),
            str(event.get("item_id", "")).strip(),
        )
        grouped.setdefault(key, []).append(copy.deepcopy(event))
    return grouped


def _history_only_thread(
    context: Context,
    manifest: dict[str, Any],
    gate_type: str,
    item_id: str,
    history_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not history_entries:
        return None
    latest = history_entries[0]
    preview = _history_item_label_for_thread(
        gate_type,
        item_id,
        str(latest.get("item_label", "")).strip() or item_id,
        {},
        history_entries,
    )
    updated_at = _pick_latest_timestamp([str(entry.get("timestamp", "")).strip() for entry in history_entries]) or _path_updated_at(
        str(manifest.get("_manifest_path", ""))
    )
    return {
        "message_id": message_id_for(str(manifest["id"]), gate_type, item_id),
        "episode_id": str(manifest["id"]),
        "episode_title": str(manifest.get("title", "")),
        "gate_type": gate_type,
        "gate_label": _history_gate_label(gate_type),
        "lane": str(latest.get("lane", "")).strip(),
        "item_id": item_id,
        "label": str(latest.get("item_label", "")).strip() or item_id,
        "unread": False,
        "read": True,
        "actionable": False,
        "actions": _thread_actions(),
        "updated_at": updated_at,
        "preview_type": str(preview.get("preview_type", "file")).strip(),
        "preview_path": str(preview.get("preview_path", "")).strip(),
        "proof_path": str(preview.get("proof_path", "")).strip(),
        "proof_manifest_path": "",
        "selected_asset": "",
        "reviewer": str(latest.get("reviewer", "")).strip(),
        "reviewed_at": str(latest.get("timestamp", "")).strip(),
        "review_notes": str(latest.get("notes", "")).strip(),
        "review_tags": normalize_review_tags(latest.get("tags")),
        "reject_tag_options": _reject_tag_options(context, gate_type),
        "episode_guardrails": _episode_guardrails(manifest),
        "history": copy.deepcopy(history_entries),
        "history_count": len(history_entries),
        **_thread_status_fields(
            lane_status="archived",
            decision_status=str(latest.get("status", "")).strip() or "recorded",
        ),
    }


def _thread_summary(thread: dict[str, Any]) -> dict[str, Any]:
    return {
        "message_id": str(thread["message_id"]),
        "episode_id": str(thread["episode_id"]),
        "episode_title": str(thread.get("episode_title", "")),
        "gate_type": str(thread["gate_type"]),
        "gate_label": str(thread.get("gate_label", "")),
        "item_id": str(thread["item_id"]),
        "label": str(thread["label"]),
        "status": str(thread.get("status", "")),
        "lane_status": str(thread.get("lane_status", "")),
        "lane_label": str(thread.get("lane_label", "")),
        "decision_status": str(thread.get("decision_status", "")),
        "decision_label": str(thread.get("decision_label", "")),
        "freshness_status": str(thread.get("freshness_status", "")),
        "freshness_label": str(thread.get("freshness_label", "")),
        "package_sync_status": str(thread.get("package_sync_status", "")),
        "package_sync_label": str(thread.get("package_sync_label", "")),
        "audio_provider": str(thread.get("audio_provider", "")),
        "audio_voice": str(thread.get("audio_voice", "")),
        "audio_model": str(thread.get("audio_model", "")),
        "unread": bool(thread.get("unread", False)),
        "read": bool(thread.get("read", True)),
        "updated_at": str(thread.get("updated_at", "")),
    }


def _build_review_threads(
    context: Context,
    manifest: dict[str, Any],
    state: dict[str, Any],
    history_entries: list[dict[str, Any]],
    *,
    hide_blocked_pending_motion_sources: bool = False,
) -> list[dict[str, Any]]:
    threads: list[dict[str, Any]] = []
    history_by_key = _group_review_history(history_entries)
    episode_id = str(manifest["id"])
    seen_keys: set[tuple[str, str, str]] = set()
    visual_key = _history_group_key(episode_id, "visual_research", "visual_research")
    visual_thread = _serialize_visual_research_thread(context, manifest, state, history_by_key.get(visual_key, []))
    if visual_thread:
        threads.append(visual_thread)
        seen_keys.add(visual_key)
    audio_key = _history_group_key(episode_id, "audio", "audio")
    audio_thread = _serialize_audio_review_thread(context, manifest, state, history_by_key.get(audio_key, []))
    if audio_thread:
        threads.append(audio_thread)
        seen_keys.add(audio_key)
    for item in scene_items(manifest):
        scene_key = _history_group_key(episode_id, "scene_still", str(item.get("id", "")).strip())
        scene_thread = _serialize_scene_review_item(context, manifest, state, item, history_by_key.get(scene_key, []))
        if scene_thread:
            threads.append(scene_thread)
            seen_keys.add(scene_key)
        motion_source_key = _history_group_key(episode_id, "motion_source", str(item.get("id", "")).strip())
        motion_source_thread = _serialize_motion_source_review_item(context, manifest, state, item, history_by_key.get(motion_source_key, []))
        if (
            motion_source_thread
            and not (
                hide_blocked_pending_motion_sources
                and str(motion_source_thread.get("blocked_reason", "")).strip()
                and str(motion_source_thread.get("decision_status", "")).strip() == "pending"
            )
        ):
            threads.append(motion_source_thread)
            seen_keys.add(motion_source_key)
    for item in packaging_items(manifest):
        packaging_key = _history_group_key(episode_id, "packaging_still", str(item.get("id", "")).strip())
        packaging_thread = _serialize_packaging_review_item(context, manifest, state, item, history_by_key.get(packaging_key, []))
        if packaging_thread:
            threads.append(packaging_thread)
            seen_keys.add(packaging_key)
    for item in motion_items(manifest):
        motion_key = _history_group_key(episode_id, "motion_asset", str(item.get("id", "")).strip())
        motion_thread = _serialize_motion_review_item(context, manifest, state, item, history_by_key.get(motion_key, []))
        if motion_thread:
            threads.append(motion_thread)
            seen_keys.add(motion_key)
    for key, grouped_history in history_by_key.items():
        if key in seen_keys:
            continue
        history_thread = _history_only_thread(context, manifest, key[1], key[2], grouped_history)
        if history_thread:
            threads.append(history_thread)
    threads.sort(
        key=lambda thread: (
            0 if bool(thread.get("unread", False)) else 1,
            -_timestamp_order_value(str(thread.get("updated_at", ""))),
            str(thread.get("episode_id", "")),
            str(thread.get("gate_type", "")),
            str(thread.get("item_id", "")),
        )
    )
    return threads


def _group_review_items(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups = {key: [] for key in GROUP_KEYS}
    for item in items:
        groups[str(item["lane"])].append(item)
    return groups


def build_review_episode_detail(context: Context, episode_id: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    state = derive_episode_state(manifest, context)
    history = load_review_history(context, episode_id)
    items = _build_review_threads(context, manifest, state, history)
    return {
        "generated_at": utc_now_iso(),
        "episode_id": str(manifest["id"]),
        "title": str(manifest.get("title", "")),
        "manifest_path": str(manifest.get("_manifest_path", "")),
        "board_category": state.get("board_category"),
        "next_action": state.get("next_action"),
        "state": state,
        "groups": _group_review_items(items),
        "items": items,
        "counts": _item_counts(items),
        "history": history,
        "history_count": len(history),
    }


def build_review_message_detail(context: Context, message_id: str) -> dict[str, Any]:
    episode_id, gate_type, item_id = parse_message_id(message_id)
    manifest = load_review_manifest(context, episode_id)
    state = derive_episode_state(manifest, context)
    history = load_review_history(context, episode_id)
    threads = _build_review_threads(context, manifest, state, history)
    thread = next((candidate for candidate in threads if str(candidate.get("message_id", "")) == message_id), None)
    if thread is None:
        raise SystemExit(f"Unknown message id: {message_id}")
    return {
        "generated_at": utc_now_iso(),
        "message": thread,
        "message_id": message_id,
    }


def build_review_inbox(context: Context) -> dict[str, Any]:
    all_items: list[dict[str, Any]] = []
    for manifest in list_episode_manifests(context):
        state = derive_episode_state(manifest, context)
        history = load_review_history(context, str(manifest["id"]))
        items = _build_review_threads(
            context,
            manifest,
            state,
            history,
            hide_blocked_pending_motion_sources=True,
        )
        if not items:
            continue
        all_items.extend(items)
    all_items.sort(
        key=lambda thread: (
            0 if bool(thread.get("unread", False)) else 1,
            -_timestamp_order_value(str(thread.get("updated_at", ""))),
            str(thread.get("episode_id", "")),
            str(thread.get("gate_type", "")),
            str(thread.get("item_id", "")),
        )
    )
    unread_items = [item for item in all_items if bool(item.get("unread", False))]
    default_message_id = str((unread_items or all_items or [{}])[0].get("message_id", "")).strip()
    return {
        "generated_at": utc_now_iso(),
        "episode_count": len({str(item.get("episode_id", "")) for item in all_items}),
        "total_items": len(all_items),
        "unread_count": len(unread_items),
        "default_message_id": default_message_id,
        "gate_counts": _item_counts(all_items),
        "messages": [_thread_summary(item) for item in all_items],
    }


def format_review_inbox(inbox: dict[str, Any]) -> str:
    lines = [f"messages: {inbox['total_items']} unread={inbox.get('unread_count', 0)} episodes={inbox['episode_count']}"]
    if not inbox["messages"]:
        lines.append("none")
        return "\n".join(lines)
    for item in inbox["messages"]:
        lines.append(
            f"{item['message_id']}: unread={str(bool(item.get('unread', False))).lower()} status={item['status']} updated={item.get('updated_at') or 'none'}"
        )
    return "\n".join(lines)


def _require_reject_inputs(decision: str, notes: str, tags: list[str], *, require_tags: bool = False) -> None:
    if decision != "reject":
        return
    if not notes.strip():
        raise SystemExit("Reject notes are required.")
    if require_tags and not tags:
        raise SystemExit("Reject tags are required.")


def _clear_review_fields(item: dict[str, Any]) -> None:
    item["reviewer"] = ""
    item["reviewed_at"] = ""
    item["review_notes"] = ""
    item["review_tags"] = []


def _stamp_review_fields(item: dict[str, Any], reviewer: str, notes: str, *, tags: list[str] | None = None) -> None:
    item["reviewer"] = reviewer
    item["reviewed_at"] = utc_now_iso()
    item["review_notes"] = notes.strip()
    item["review_tags"] = normalize_review_tags(tags)


def _clear_motion_review_fields(item: dict[str, Any]) -> None:
    item["motion_reviewer"] = ""
    item["motion_reviewed_at"] = ""
    item["motion_review_notes"] = ""
    item["motion_review_tags"] = []


def _stamp_motion_review_fields(item: dict[str, Any], reviewer: str, notes: str, *, tags: list[str] | None = None) -> None:
    item["motion_reviewer"] = reviewer
    item["motion_reviewed_at"] = utc_now_iso()
    item["motion_review_notes"] = notes.strip()
    item["motion_review_tags"] = normalize_review_tags(tags)


def _audio_review_payload(audio: dict[str, Any]) -> dict[str, Any]:
    review = audio.get("review")
    if not isinstance(review, dict):
        review = {}
        audio["review"] = review
    review.setdefault("status", "pending")
    review.setdefault("reviewer", "")
    review.setdefault("reviewed_at", "")
    review.setdefault("notes", "")
    return review


def _clear_audio_review_fields(audio: dict[str, Any], *, status: str = "pending") -> None:
    review = _audio_review_payload(audio)
    review["status"] = status
    review["reviewer"] = ""
    review["reviewed_at"] = ""
    review["notes"] = ""


def _stamp_audio_review_fields(audio: dict[str, Any], reviewer: str, notes: str, *, status: str) -> None:
    review = _audio_review_payload(audio)
    review["status"] = status
    review["reviewer"] = reviewer
    review["reviewed_at"] = utc_now_iso()
    review["notes"] = notes.strip()


def _reset_downstream_after_audio_revocation(manifest: dict[str, Any]) -> None:
    assembly = manifest.setdefault("assembly", {})
    assembly["status"] = "todo"
    assembly["master_video_path"] = ""
    assembly["completed_at"] = ""
    web = manifest.setdefault("web", {})
    web["status"] = "todo"
    release = manifest.setdefault("release", {})
    release["status"] = "todo"
    release["scheduled_for"] = ""
    release["published_at"] = ""
    analytics = manifest.setdefault("analytics", {})
    analytics["status"] = "todo"


def _selected_asset_manifest_path(selected_asset: str) -> str:
    return f"{selected_asset}.json"


def _approved_snapshot_asset_path(item: dict[str, Any]) -> Path:
    reference_dir_raw = str(item.get("reference_dir", "")).strip()
    if not reference_dir_raw:
        raise SystemExit(f"{item.get('id', '')} is missing reference_dir.")
    reference_dir = Path(reference_dir_raw).expanduser()
    if not reference_dir.is_absolute():
        raise SystemExit(f"{item.get('id', '')} reference_dir must be absolute: {reference_dir}")
    return reference_dir / "selects" / "review_approved.png"


def _capture_approved_proof(item: dict[str, Any], *, gate_label: str) -> str:
    item_id = str(item.get("id", "")).strip()
    latest_render_path = str(item.get("latest_render_path", "")).strip()
    latest_render_manifest_path = str(item.get("latest_render_manifest_path", "")).strip()
    if not latest_render_path or not path_exists(latest_render_path):
        raise SystemExit(f"{gate_label} `{item_id}` is missing latest_render_path for approval.")
    if not latest_render_manifest_path or not path_exists(latest_render_manifest_path):
        raise SystemExit(f"{gate_label} `{item_id}` latest render manifest is missing: {latest_render_manifest_path}")
    source_asset = Path(latest_render_path).expanduser().resolve()
    source_manifest = Path(latest_render_manifest_path).expanduser().resolve()
    approved_asset = _approved_snapshot_asset_path(item)
    approved_asset.parent.mkdir(parents=True, exist_ok=True)
    approved_manifest = Path(f"{approved_asset}.json")
    if source_asset.resolve() != approved_asset.resolve():
        if approved_asset.exists():
            approved_asset.unlink()
        shutil.copy2(source_asset, approved_asset)
    if source_manifest.resolve() != approved_manifest.resolve():
        if approved_manifest.exists():
            approved_manifest.unlink()
        shutil.copy2(source_manifest, approved_manifest)
    item["approved_proof_path"] = str(approved_asset)
    item["approved_proof_manifest_path"] = str(approved_manifest)
    return str(approved_asset)


def _reopen_approved_still(item: dict[str, Any], *, gate_label: str) -> str:
    item_id = str(item.get("id", "")).strip()
    approved_path = _approved_proof_path(item)
    approved_manifest_path = str(item.get("approved_proof_manifest_path", "")).strip()
    if approved_path and approved_manifest_path and path_exists(approved_manifest_path):
        item["latest_render_path"] = approved_path
        item["latest_render_manifest_path"] = approved_manifest_path
    else:
        selected_asset = str(item.get("selected_asset", "")).strip()
        if not selected_asset or not path_exists(selected_asset):
            raise SystemExit(f"{gate_label} `{item_id}` must have an approved proof or selected asset before it can be unapproved.")
        selected_manifest_path = _selected_asset_manifest_path(selected_asset)
        if not path_exists(selected_manifest_path):
            raise SystemExit(f"{gate_label} `{item_id}` selected asset manifest is missing: {selected_manifest_path}")
        item["latest_render_path"] = selected_asset
        item["latest_render_manifest_path"] = selected_manifest_path
    item["approved_proof_path"] = ""
    item["approved_proof_manifest_path"] = ""
    item["selected_asset"] = ""
    return str(item.get("latest_render_path", "")).strip()


def _reset_motion_review_status(item: dict[str, Any]) -> None:
    current = str(item.get("motion_review_status", "pending")).strip() or "pending"
    if current not in {"blocked", "not_planned"}:
        item["motion_review_status"] = "pending"
    _clear_motion_review_fields(item)


def _reopen_motion_asset_item(item: dict[str, Any]) -> None:
    item["status"] = "review"
    item["review_outcome"] = ""
    _clear_review_fields(item)


def _reset_motion_assets_for_source(manifest: dict[str, Any], source_still_id: str) -> None:
    for motion_item in motion_items(manifest):
        if str(motion_item.get("source_still_id", "")).strip() != str(source_still_id):
            continue
        if _motion_asset_can_unapprove(motion_item):
            _reopen_motion_asset_item(motion_item)


def _unapprove_scene_item(item: dict[str, Any], *, gate_label: str) -> str:
    proof_path = _reopen_approved_still(item, gate_label=gate_label)
    item["review_status"] = "pending"
    _clear_review_fields(item)
    _reset_motion_review_status(item)
    return proof_path


def _finalize_review_write(
    context: Context,
    manifest: dict[str, Any],
    *,
    episode_id: str,
    gate_type: str,
    lane: str,
    item_id: str,
    decision: str,
    reviewer: str,
    notes: str,
    tags: list[str],
    before: dict[str, Any],
    after: dict[str, Any],
    proof_path: str,
) -> dict[str, Any]:
    updated_manifest = load_review_manifest(context, episode_id)
    updated_state = derive_episode_state(updated_manifest, context)
    state_path = write_state_file(context, updated_manifest, updated_state)
    log_path = append_review_log(
        context,
        episode_id,
        {
            "timestamp": utc_now_iso(),
            "reviewer": reviewer,
            "episode_id": episode_id,
            "lane": lane,
            "gate_type": gate_type,
            "item_id": item_id,
            "decision": decision,
            "notes": notes.strip(),
            "tags": normalize_review_tags(tags),
            "before": before,
            "after": after,
            "proof_path": proof_path,
        },
    )
    detail = build_review_episode_detail(context, episode_id)
    return {
        "generated_at": utc_now_iso(),
        "episode_id": episode_id,
        "gate_type": gate_type,
        "item_id": item_id,
        "decision": decision,
        "reviewer": reviewer,
        "notes": notes.strip(),
        "tags": normalize_review_tags(tags),
        "manifest_path": str(updated_manifest.get("_manifest_path", "")),
        "state_path": str(state_path),
        "log_path": str(log_path),
        "state": updated_state,
        "detail": detail,
    }


def approve_visual_research(context: Context, episode_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    state = derive_episode_state(manifest, context)
    lane_state = state["lanes"]["visual_research"]
    if str(manifest.get("visual_research", {}).get("status", "")).strip() != "review":
        raise SystemExit("Visual research is not currently in review.")
    if not lane_state.get("docs_complete"):
        raise SystemExit("Visual research cannot be approved until the six visual research deliverables exist, including contact_sheet.pdf and source_inventory.json.")
    if not lane_state.get("structured_complete"):
        raise SystemExit("Visual research cannot be approved until every act has structured coverage.")
    if not lane_state.get("source_inventory_complete"):
        unresolved = lane_state.get("guardrails", {}).get("unresolved_source_ids", [])
        unresolved_ids = ", ".join(str(source_id).strip() for source_id in unresolved if str(source_id).strip())
        suffix = f" Unresolved sources: {unresolved_ids}." if unresolved_ids else ""
        raise SystemExit(
            "Visual research cannot be approved until approved research sources are text-clear or cleaned in source_inventory.json."
            + suffix
        )
    if not lane_state.get("coverage_complete"):
        raise SystemExit("Visual research cannot be approved until scene and motion coverage is complete.")
    if lane_state.get("script_sha_mismatch"):
        raise SystemExit("Visual research cannot be approved while the locked script fingerprint is stale.")
    visual_research = manifest["visual_research"]
    approval = visual_research.setdefault("approval", {})
    before = {
        "status": str(visual_research.get("status", "")).strip(),
        "approval": copy.deepcopy(approval),
    }
    approval["status"] = "approved"
    approval["reviewer"] = reviewer
    approval["reviewed_at"] = utc_now_iso()
    approval["notes"] = notes.strip()
    approval["tags"] = []
    visual_research["status"] = "done"
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="visual_research",
        lane="visual_research",
        item_id="visual_research",
        decision="approve",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after={
            "status": str(visual_research.get("status", "")).strip(),
            "approval": copy.deepcopy(approval),
        },
        proof_path=_visual_research_proof_path(visual_research),
    )


def reject_visual_research(context: Context, episode_id: str, reviewer: str, notes: str, tags: list[str]) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    visual_research = manifest.get("visual_research", {})
    if str(visual_research.get("status", "")).strip() != "review":
        raise SystemExit("Visual research is not currently in review.")
    approval = visual_research.setdefault("approval", {})
    before = {
        "status": str(visual_research.get("status", "")).strip(),
        "approval": copy.deepcopy(approval),
    }
    approval["status"] = "rejected"
    approval["reviewer"] = reviewer
    approval["reviewed_at"] = utc_now_iso()
    approval["notes"] = notes.strip()
    approval["tags"] = normalize_review_tags(tags)
    visual_research["status"] = "review"
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="visual_research",
        lane="visual_research",
        item_id="visual_research",
        decision="reject",
        reviewer=reviewer,
        notes=notes,
        tags=tags,
        before=before,
        after={
            "status": str(visual_research.get("status", "")).strip(),
            "approval": copy.deepcopy(approval),
        },
        proof_path=_visual_research_proof_path(visual_research),
    )


def unreject_visual_research(context: Context, episode_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    visual_research = manifest.get("visual_research", {})
    approval = visual_research.setdefault("approval", {})
    if not _visual_research_can_unreject(manifest):
        raise SystemExit("Visual research is not currently rejected.")
    before = {
        "status": str(visual_research.get("status", "")).strip(),
        "approval": copy.deepcopy(approval),
    }
    approval["status"] = "pending"
    approval["reviewer"] = ""
    approval["reviewed_at"] = ""
    approval["notes"] = ""
    approval["tags"] = []
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="visual_research",
        lane="visual_research",
        item_id="visual_research",
        decision="unreject",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after={
            "status": str(visual_research.get("status", "")).strip(),
            "approval": copy.deepcopy(approval),
        },
        proof_path=_visual_research_proof_path(visual_research),
    )


def unapprove_visual_research(context: Context, episode_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    visual_research = manifest.get("visual_research", {})
    approval = visual_research.setdefault("approval", {})
    if str(approval.get("status", "")).strip() != "approved" or str(visual_research.get("status", "")).strip() != "done":
        raise SystemExit("Visual research is not currently approved.")
    before = {
        "status": str(visual_research.get("status", "")).strip(),
        "approval": copy.deepcopy(approval),
    }
    approval["status"] = "pending"
    approval["reviewer"] = ""
    approval["reviewed_at"] = ""
    approval["notes"] = ""
    approval["tags"] = []
    visual_research["status"] = "review"
    for item in scene_items(manifest):
        if _scene_can_unapprove(item):
            _unapprove_scene_item(item, gate_label="Scene still")
            _reset_motion_assets_for_source(manifest, str(item.get("id", "")).strip())
        elif _motion_source_can_unapprove(item):
            _reset_motion_review_status(item)
            _reset_motion_assets_for_source(manifest, str(item.get("id", "")).strip())
    manifest["scene_stills"]["status"] = derive_scene_lane_status(scene_items(manifest))
    for item in packaging_items(manifest):
        if _scene_can_unapprove(item):
            _unapprove_scene_item(item, gate_label="Packaging still")
    manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
    for motion_item in motion_items(manifest):
        if _motion_asset_can_unapprove(motion_item):
            _reopen_motion_asset_item(motion_item)
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="visual_research",
        lane="visual_research",
        item_id="visual_research",
        decision="unapprove",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after={
            "status": str(visual_research.get("status", "")).strip(),
            "approval": copy.deepcopy(approval),
        },
        proof_path=_visual_research_proof_path(visual_research),
    )


def approve_audio(context: Context, episode_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    state = derive_episode_state(manifest, context)
    audio = manifest.get("audio", {})
    review = _audio_review_payload(audio)
    if str(audio.get("status", "")).strip() != "review":
        raise SystemExit("Audio is not currently in review.")
    if not path_exists(audio.get("master_path")):
        raise SystemExit("Audio cannot be approved until the final master WAV exists.")
    if not path_exists(audio.get("transcript_path")):
        raise SystemExit("Audio cannot be approved until the QA transcript exists.")
    if str(state.get("lanes", {}).get("audio", {}).get("package_sync_status", "")).strip() == "out_of_sync":
        raise SystemExit(
            str(state.get("lanes", {}).get("audio", {}).get("review_blocked_reason", "")).strip()
            or "Audio review is blocked until the latest packaged WAV and QA transcript are promoted."
        )
    if str(state.get("lanes", {}).get("audio", {}).get("freshness", "")).strip() != "current":
        raise SystemExit(
            str(state.get("lanes", {}).get("audio", {}).get("review_blocked_reason", "")).strip()
            or "Audio review is blocked until the package is current."
        )
    before = {
        "status": str(audio.get("status", "")).strip(),
        "review": copy.deepcopy(review),
    }
    _stamp_audio_review_fields(audio, reviewer, notes, status="approved")
    audio["status"] = "done"
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="audio",
        lane="audio",
        item_id="audio",
        decision="approve",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after={
            "status": str(audio.get("status", "")).strip(),
            "review": copy.deepcopy(_audio_review_payload(audio)),
        },
        proof_path=str(audio.get("master_path", "")).strip(),
    )


def reject_audio(context: Context, episode_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    state = derive_episode_state(manifest, context)
    audio = manifest.get("audio", {})
    review = _audio_review_payload(audio)
    if str(audio.get("status", "")).strip() != "review":
        raise SystemExit("Audio is not currently in review.")
    if not path_exists(audio.get("master_path")):
        raise SystemExit("Audio cannot be rejected until the final master WAV exists.")
    if not path_exists(audio.get("transcript_path")):
        raise SystemExit("Audio cannot be rejected until the QA transcript exists.")
    if str(state.get("lanes", {}).get("audio", {}).get("package_sync_status", "")).strip() == "out_of_sync":
        raise SystemExit(
            str(state.get("lanes", {}).get("audio", {}).get("review_blocked_reason", "")).strip()
            or "Audio review is blocked until the latest packaged WAV and QA transcript are promoted."
        )
    if str(state.get("lanes", {}).get("audio", {}).get("freshness", "")).strip() != "current":
        raise SystemExit(
            str(state.get("lanes", {}).get("audio", {}).get("review_blocked_reason", "")).strip()
            or "Audio review is blocked until the package is current."
        )
    before = {
        "status": str(audio.get("status", "")).strip(),
        "review": copy.deepcopy(review),
    }
    _stamp_audio_review_fields(audio, reviewer, notes, status="rejected")
    audio["status"] = "review"
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="audio",
        lane="audio",
        item_id="audio",
        decision="reject",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after={
            "status": str(audio.get("status", "")).strip(),
            "review": copy.deepcopy(_audio_review_payload(audio)),
        },
        proof_path=str(audio.get("master_path", "")).strip(),
    )


def unreject_audio(context: Context, episode_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    audio = manifest.get("audio", {})
    review = _audio_review_payload(audio)
    if not _audio_can_unreject(manifest):
        raise SystemExit("Audio is not currently rejected.")
    before = {
        "status": str(audio.get("status", "")).strip(),
        "review": copy.deepcopy(review),
    }
    _clear_audio_review_fields(audio, status="pending")
    audio["status"] = "review"
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="audio",
        lane="audio",
        item_id="audio",
        decision="unreject",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after={
            "status": str(audio.get("status", "")).strip(),
            "review": copy.deepcopy(_audio_review_payload(audio)),
        },
        proof_path=str(audio.get("master_path", "")).strip(),
    )


def unapprove_audio(context: Context, episode_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    audio = manifest.get("audio", {})
    review = _audio_review_payload(audio)
    if not _audio_can_unapprove(manifest):
        raise SystemExit("Audio is not currently approved.")
    before = {
        "status": str(audio.get("status", "")).strip(),
        "review": copy.deepcopy(review),
        "assembly": copy.deepcopy(manifest.get("assembly", {})),
        "web": copy.deepcopy(manifest.get("web", {})),
        "release": copy.deepcopy(manifest.get("release", {})),
        "analytics": copy.deepcopy(manifest.get("analytics", {})),
    }
    _clear_audio_review_fields(audio, status="pending")
    audio["status"] = "review"
    _reset_downstream_after_audio_revocation(manifest)
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="audio",
        lane="audio",
        item_id="audio",
        decision="unapprove",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after={
            "status": str(audio.get("status", "")).strip(),
            "review": copy.deepcopy(_audio_review_payload(audio)),
            "assembly": copy.deepcopy(manifest.get("assembly", {})),
            "web": copy.deepcopy(manifest.get("web", {})),
            "release": copy.deepcopy(manifest.get("release", {})),
            "analytics": copy.deepcopy(manifest.get("analytics", {})),
        },
        proof_path=str(audio.get("master_path", "")).strip(),
    )


def approve_motion_source(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_scene_item(manifest, item_id)
    source_path = _approved_still_path(item)
    if str(item.get("review_status", "")).strip() != "approved" or not source_path:
        raise SystemExit(f"Scene still `{item_id}` must be approved with an approved proof before motion approval.")
    before = copy.deepcopy(item)
    item["motion_review_status"] = "approved_for_motion"
    _stamp_motion_review_fields(item, reviewer, notes, tags=[])
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="motion_source",
        lane="scene_stills",
        item_id=item_id,
        decision="approve",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=source_path,
    )


def reject_motion_source(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str, tags: list[str]) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_scene_item(manifest, item_id)
    source_path = _approved_still_path(item)
    if str(item.get("review_status", "")).strip() != "approved" or not source_path:
        raise SystemExit(f"Scene still `{item_id}` must be approved with an approved proof before motion rejection.")
    before = copy.deepcopy(item)
    item["motion_review_status"] = "rejected"
    _stamp_motion_review_fields(item, reviewer, notes, tags=tags)
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="motion_source",
        lane="scene_stills",
        item_id=item_id,
        decision="reject",
        reviewer=reviewer,
        notes=notes,
        tags=tags,
        before=before,
        after=copy.deepcopy(item),
        proof_path=source_path,
    )


def unreject_motion_source(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_scene_item(manifest, item_id)
    if not _motion_source_can_unreject(item):
        raise SystemExit(f"Scene still `{item_id}` is not currently rejected for motion.")
    before = copy.deepcopy(item)
    item["motion_review_status"] = "pending"
    _clear_motion_review_fields(item)
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="motion_source",
        lane="scene_stills",
        item_id=item_id,
        decision="unreject",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=_approved_still_path(item),
    )


def unapprove_motion_source(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_scene_item(manifest, item_id)
    if not _motion_source_can_unapprove(item):
        raise SystemExit(f"Scene still `{item_id}` is not currently approved for motion.")
    before = copy.deepcopy(item)
    _reset_motion_review_status(item)
    _reset_motion_assets_for_source(manifest, item_id)
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="motion_source",
        lane="scene_stills",
        item_id=item_id,
        decision="unapprove",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=_approved_still_path(item),
    )


def reject_scene_still(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str, tags: list[str]) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_scene_item(manifest, item_id)
    if not str(item.get("latest_render_path", "")).strip():
        raise SystemExit(f"Scene still `{item_id}` has no proof to reject.")
    before = copy.deepcopy(item)
    item["review_status"] = "rejected"
    _stamp_review_fields(item, reviewer, notes, tags=tags)
    manifest["scene_stills"]["status"] = derive_scene_lane_status(scene_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="scene_still",
        lane="scene_stills",
        item_id=item_id,
        decision="reject",
        reviewer=reviewer,
        notes=notes,
        tags=tags,
        before=before,
        after=copy.deepcopy(item),
        proof_path=str(item.get("latest_render_path", "")).strip(),
    )


def unreject_scene_still(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_scene_item(manifest, item_id)
    if not _scene_can_unreject(item):
        raise SystemExit(f"Scene still `{item_id}` is not currently rejected.")
    before = copy.deepcopy(item)
    item["review_status"] = "pending"
    _clear_review_fields(item)
    manifest["scene_stills"]["status"] = derive_scene_lane_status(scene_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="scene_still",
        lane="scene_stills",
        item_id=item_id,
        decision="unreject",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=str(item.get("latest_render_path", "")).strip(),
    )


def unapprove_scene_still(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_scene_item(manifest, item_id)
    if not _scene_can_unapprove(item):
        raise SystemExit(f"Scene still `{item_id}` is not currently approved.")
    before = copy.deepcopy(item)
    proof_path = _unapprove_scene_item(item, gate_label="Scene still")
    _reset_motion_assets_for_source(manifest, item_id)
    manifest["scene_stills"]["status"] = derive_scene_lane_status(scene_items(manifest))
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="scene_still",
        lane="scene_stills",
        item_id=item_id,
        decision="unapprove",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=proof_path,
    )


def reject_packaging_still(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str, tags: list[str]) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_packaging_item(manifest, item_id)
    if not str(item.get("latest_render_path", "")).strip():
        raise SystemExit(f"Packaging still `{item_id}` has no proof to reject.")
    before = copy.deepcopy(item)
    item["review_status"] = "rejected"
    _stamp_review_fields(item, reviewer, notes, tags=tags)
    manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="packaging_still",
        lane="packaging_stills",
        item_id=item_id,
        decision="reject",
        reviewer=reviewer,
        notes=notes,
        tags=tags,
        before=before,
        after=copy.deepcopy(item),
        proof_path=str(item.get("latest_render_path", "")).strip(),
    )


def unreject_packaging_still(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_packaging_item(manifest, item_id)
    if not _scene_can_unreject(item):
        raise SystemExit(f"Packaging still `{item_id}` is not currently rejected.")
    before = copy.deepcopy(item)
    item["review_status"] = "pending"
    _clear_review_fields(item)
    manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="packaging_still",
        lane="packaging_stills",
        item_id=item_id,
        decision="unreject",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=str(item.get("latest_render_path", "")).strip(),
    )


def unapprove_packaging_still(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    item = resolve_packaging_item(manifest, item_id)
    if not _scene_can_unapprove(item):
        raise SystemExit(f"Packaging still `{item_id}` is not currently approved.")
    before = copy.deepcopy(item)
    proof_path = _unapprove_scene_item(item, gate_label="Packaging still")
    manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="packaging_still",
        lane="packaging_stills",
        item_id=item_id,
        decision="unapprove",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=proof_path,
    )


def reject_motion_asset(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str, tags: list[str]) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    lookup = {str(item.get("id", "")): item for item in motion_items(manifest)}
    item = lookup.get(item_id)
    if item is None:
        raise SystemExit(f"Unknown motion item id: {item_id}")
    if str(item.get("status", "")).strip() != "review":
        raise SystemExit(f"Motion asset `{item_id}` is not in review.")
    before = copy.deepcopy(item)
    item["status"] = "todo"
    item["review_outcome"] = "rejected"
    _stamp_review_fields(item, reviewer, notes, tags=tags)
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="motion_asset",
        lane="motion_assets",
        item_id=item_id,
        decision="reject",
        reviewer=reviewer,
        notes=notes,
        tags=tags,
        before=before,
        after=copy.deepcopy(item),
        proof_path=str(item.get("latest_render_path", "")).strip(),
    )


def unreject_motion_asset(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    lookup = {str(item.get("id", "")): item for item in motion_items(manifest)}
    item = lookup.get(item_id)
    if item is None:
        raise SystemExit(f"Unknown motion item id: {item_id}")
    if not _motion_asset_can_unreject(item):
        raise SystemExit(f"Motion asset `{item_id}` is not currently rejected.")
    before = copy.deepcopy(item)
    _reopen_motion_asset_item(item)
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="motion_asset",
        lane="motion_assets",
        item_id=item_id,
        decision="unreject",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=str(item.get("latest_render_path", "")).strip(),
    )


def unapprove_motion_asset(context: Context, episode_id: str, item_id: str, reviewer: str, notes: str) -> dict[str, Any]:
    manifest = load_review_manifest(context, episode_id)
    manifest_path = Path(str(manifest["_manifest_path"]))
    lookup = {str(item.get("id", "")): item for item in motion_items(manifest)}
    item = lookup.get(item_id)
    if item is None:
        raise SystemExit(f"Unknown motion item id: {item_id}")
    if not _motion_asset_can_unapprove(item):
        raise SystemExit(f"Motion asset `{item_id}` is not currently approved.")
    before = copy.deepcopy(item)
    _reopen_motion_asset_item(item)
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return _finalize_review_write(
        context,
        manifest,
        episode_id=episode_id,
        gate_type="motion_asset",
        lane="motion_assets",
        item_id=item_id,
        decision="unapprove",
        reviewer=reviewer,
        notes=notes,
        tags=[],
        before=before,
        after=copy.deepcopy(item),
        proof_path=str(item.get("latest_render_path", "")).strip(),
    )


def perform_review_action(
    context: Context,
    *,
    episode_id: str,
    gate_type: str,
    decision: str,
    item_id: str | None = None,
    reviewer: str | None = None,
    notes: str = "",
    tags: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    gate_type = str(gate_type).strip()
    decision = str(decision).strip().lower()
    reviewer_name = default_reviewer_name(reviewer)
    if gate_type not in GATE_TYPES:
        raise SystemExit(f"Unknown gate type: {gate_type}")
    if decision not in {"approve", "reject", "unapprove", "unreject"}:
        raise SystemExit(f"Unknown decision: {decision}")
    normalized_tags = _normalize_action_tags(context, gate_type, list(tags))
    _require_reject_inputs(decision, notes, normalized_tags)
    if gate_type == "visual_research":
        if item_id:
            raise SystemExit("visual_research does not take an item_id.")
        if decision == "approve":
            return approve_visual_research(context, episode_id, reviewer_name, notes)
        if decision == "reject":
            return reject_visual_research(context, episode_id, reviewer_name, notes, normalized_tags)
        if decision == "unreject":
            return unreject_visual_research(context, episode_id, reviewer_name, notes)
        return unapprove_visual_research(context, episode_id, reviewer_name, notes)
    if gate_type == "audio":
        if item_id and item_id != "audio":
            raise SystemExit("audio does not take a custom item_id.")
        if decision == "approve":
            return approve_audio(context, episode_id, reviewer_name, notes)
        if decision == "reject":
            return reject_audio(context, episode_id, reviewer_name, notes)
        if decision == "unreject":
            return unreject_audio(context, episode_id, reviewer_name, notes)
        return unapprove_audio(context, episode_id, reviewer_name, notes)
    if not item_id:
        raise SystemExit(f"{gate_type} requires an item_id.")
    if gate_type == "scene_still":
        manifest = load_review_manifest(context, episode_id)
        item = resolve_scene_item(manifest, item_id)
        if decision == "unapprove":
            return unapprove_scene_still(context, episode_id, item_id, reviewer_name, notes)
        if decision == "unreject":
            return unreject_scene_still(context, episode_id, item_id, reviewer_name, notes)
        if not str(item.get("latest_render_path", "")).strip():
            raise SystemExit(f"Scene still `{item_id}` has no proof render to review.")
        if decision == "approve":
            if not _visual_research_done(manifest):
                raise SystemExit("Scene stills cannot be approved until visual research is approved.")
            before = copy.deepcopy(item)
            _capture_approved_proof(item, gate_label="Scene still")
            item["selected_asset"] = ""
            item["review_status"] = "approved"
            _stamp_review_fields(item, reviewer_name, notes, tags=[])
            manifest["scene_stills"]["status"] = derive_scene_lane_status(scene_items(manifest))
            write_episode_manifest(Path(str(manifest["_manifest_path"])), manifest)
            return _finalize_review_write(
                context,
                manifest,
                episode_id=episode_id,
                gate_type="scene_still",
                lane="scene_stills",
                item_id=item_id,
                decision="approve",
                reviewer=reviewer_name,
                notes=notes,
                tags=[],
                before=before,
                after=copy.deepcopy(resolve_scene_item(manifest, item_id)),
                proof_path=str(item.get("approved_proof_path", "")).strip(),
            )
        return reject_scene_still(context, episode_id, item_id, reviewer_name, notes, normalized_tags)
    if gate_type == "motion_source":
        if decision == "approve":
            return approve_motion_source(context, episode_id, item_id, reviewer_name, notes)
        if decision == "reject":
            return reject_motion_source(context, episode_id, item_id, reviewer_name, notes, normalized_tags)
        if decision == "unreject":
            return unreject_motion_source(context, episode_id, item_id, reviewer_name, notes)
        return unapprove_motion_source(context, episode_id, item_id, reviewer_name, notes)
    if gate_type == "packaging_still":
        manifest = load_review_manifest(context, episode_id)
        item = resolve_packaging_item(manifest, item_id)
        if decision == "unapprove":
            return unapprove_packaging_still(context, episode_id, item_id, reviewer_name, notes)
        if decision == "unreject":
            return unreject_packaging_still(context, episode_id, item_id, reviewer_name, notes)
        if not str(item.get("latest_render_path", "")).strip():
            raise SystemExit(f"Packaging still `{item_id}` has no proof render to review.")
        if decision == "approve":
            if not _visual_research_done(manifest):
                raise SystemExit("Packaging stills cannot be approved until visual research is approved.")
            before = copy.deepcopy(item)
            _capture_approved_proof(item, gate_label="Packaging still")
            item["selected_asset"] = ""
            item["review_status"] = "approved"
            _stamp_review_fields(item, reviewer_name, notes, tags=[])
            manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
            write_episode_manifest(Path(str(manifest["_manifest_path"])), manifest)
            return _finalize_review_write(
                context,
                manifest,
                episode_id=episode_id,
                gate_type="packaging_still",
                lane="packaging_stills",
                item_id=item_id,
                decision="approve",
                reviewer=reviewer_name,
                notes=notes,
                tags=[],
                before=before,
                after=copy.deepcopy(resolve_packaging_item(manifest, item_id)),
                proof_path=str(item.get("approved_proof_path", "")).strip(),
            )
        return reject_packaging_still(context, episode_id, item_id, reviewer_name, notes, normalized_tags)
    manifest = load_review_manifest(context, episode_id)
    lookup = {str(item.get("id", "")): item for item in motion_items(manifest)}
    item = lookup.get(item_id)
    if item is None:
        raise SystemExit(f"Unknown motion item id: {item_id}")
    if decision == "unapprove":
        return unapprove_motion_asset(context, episode_id, item_id, reviewer_name, notes)
    if decision == "unreject":
        return unreject_motion_asset(context, episode_id, item_id, reviewer_name, notes)
    if str(item.get("status", "")).strip() != "review":
        raise SystemExit(f"Motion asset `{item_id}` is not in review.")
    if decision == "approve":
        proof_path = str(item.get("latest_render_path", "")).strip()
        if not proof_path:
            raise SystemExit(f"Motion asset `{item_id}` has no proof render to approve.")
        if not _motion_asset_prerequisites(manifest, item):
            raise SystemExit(f"Motion asset `{item_id}` cannot be approved until its source still is approved for motion.")
        before = copy.deepcopy(item)
        promote_motion_proof(
            context,
            manifest,
            item_id,
            proof_path,
            reviewer=reviewer_name,
            review_notes=notes,
        )
        return _finalize_review_write(
            context,
            manifest,
            episode_id=episode_id,
            gate_type="motion_asset",
            lane="motion_assets",
            item_id=item_id,
            decision="approve",
            reviewer=reviewer_name,
            notes=notes,
            tags=[],
            before=before,
            after=copy.deepcopy({candidate["id"]: candidate for candidate in motion_items(manifest)}[item_id]),
            proof_path=proof_path,
        )
    return reject_motion_asset(context, episode_id, item_id, reviewer_name, notes, normalized_tags)


__all__ = [
    "GATE_TYPES",
    "allowed_asset_roots",
    "append_review_log",
    "approve_audio",
    "approve_motion_source",
    "approve_visual_research",
    "build_review_episode_detail",
    "build_review_inbox",
    "build_review_message_detail",
    "default_reviewer_name",
    "ensure_allowed_asset_path",
    "format_review_inbox",
    "load_review_history",
    "load_review_manifest",
    "message_id_for",
    "parse_message_id",
    "perform_review_action",
    "reject_audio",
    "reject_motion_asset",
    "reject_motion_source",
    "reject_packaging_still",
    "reject_scene_still",
    "reject_visual_research",
    "review_log_path",
    "unapprove_audio",
    "unapprove_motion_asset",
    "unapprove_motion_source",
    "unapprove_packaging_still",
    "unapprove_scene_still",
    "unapprove_visual_research",
    "unreject_audio",
    "unreject_motion_asset",
    "unreject_motion_source",
    "unreject_packaging_still",
    "unreject_scene_still",
    "unreject_visual_research",
]
