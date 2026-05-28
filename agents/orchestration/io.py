from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tomllib

from orchestration.adapters import AudioRepo, EpisodesRepo, VizRepo, WebRepo
from orchestration.adapters.episodes import EpisodeDirectoryInfo, compact_slug
from orchestration.guardrails import (
    derive_latest_reject_tags,
    derive_visual_research_guardrails,
    infer_reject_tags,
    normalize_review_tags,
)
from orchestration.research_sources import default_source_inventory_path, load_source_inventory

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_WORDS_PER_MINUTE = 150
ACT_HEADING_RE = re.compile(r"^##\s+Act\s+(?P<number>\d+)\s*[-:]\s*(?P<title>.+?)\s*$", re.IGNORECASE)
ACT_TITLE_RE = re.compile(r"^Act\s+\d+\s*[-:]\s*", re.IGNORECASE)
DIARIZED_LINE_RE = re.compile(
    r"^\[(?P<start>\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*[–-]\s*(?P<end>\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]\s*"
    r"(?:(?P<speaker>[^:]+):\s*)?(?P<text>.+?)\s*$"
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Context:
    root: Path
    channel: dict[str, Any]
    web_entry_ids: set[str]
    asset_archetypes: dict[str, Any]
    episodes_repo: EpisodesRepo
    audio_repo: AudioRepo
    viz_repo: VizRepo
    web_repo: WebRepo


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def build_context(root: Path = ROOT_DIR) -> Context:
    channel = load_toml(root / "config" / "channel.toml")
    asset_archetypes = load_toml(root / "config" / "asset_archetypes.toml")
    episodes_repo = EpisodesRepo(Path(channel["paths"]["episodes_root"]))
    audio_repo = AudioRepo(Path(channel["paths"]["audio_root"]))
    viz_repo = VizRepo(Path(channel["paths"]["viz_root"]))
    web_repo = WebRepo(Path(channel["paths"]["web_root"]) / "lib" / "site-facts.ts")
    return Context(
        root=root,
        channel=channel,
        web_entry_ids=web_repo.entry_ids(),
        asset_archetypes=asset_archetypes,
        episodes_repo=episodes_repo,
        audio_repo=audio_repo,
        viz_repo=viz_repo,
        web_repo=web_repo,
    )


def path_or_none(value: Any) -> Path | None:
    if not value:
        return None
    return Path(str(value))


def path_exists(value: Any) -> bool:
    path = path_or_none(value)
    return bool(path and path.exists())


def build_motion_output_path(context: Context, episode_id: str, item_id: str) -> Path:
    return build_episode_reference_dir(context, episode_id, item_id) / "selects" / "hero_video.mp4"


def build_motion_workbench_project_path(context: Context, episode_id: str, item_id: str) -> Path:
    return build_episode_reference_dir(context, episode_id, item_id) / "workbench" / "project.json"


def build_episode_reference_dir(context: Context, episode_id: str, item_id: str) -> Path:
    return Path(context.channel["paths"]["viz_root"]) / "references" / "episodes" / episode_id / item_id


def _first_required_item_id(items: list[dict[str, Any]]) -> str | None:
    for item in items:
        if bool(item.get("required", True)):
            item_id = str(item.get("id", "")).strip()
            if item_id:
                return item_id
    return None


def build_scene_output_path(context: Context, episode_id: str, item: dict[str, Any], items: list[dict[str, Any]]) -> Path:
    reference_dir = build_episode_reference_dir(context, episode_id, str(item["id"]))
    primary_item_id = _first_required_item_id(items)
    filename = "hero_still.png" if str(item.get("id", "")) == primary_item_id else f"{item['id']}.png"
    return reference_dir / "selects" / filename


def build_packaging_output_path(
    context: Context,
    episode_id: str,
    item: dict[str, Any],
    items: list[dict[str, Any]],
) -> Path:
    reference_dir = build_episode_reference_dir(context, episode_id, str(item["id"]))
    primary_item_id = None
    item_kind = str(item.get("kind", "")).strip()
    for candidate in items:
        if str(candidate.get("kind", "")).strip() == item_kind and bool(candidate.get("required", True)):
            primary_item_id = str(candidate.get("id", "")).strip()
            break
    filename = "hero_plate.png" if str(item.get("id", "")) == primary_item_id else f"{item['id']}.png"
    return reference_dir / "selects" / filename


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _coerce_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _estimate_script_runtime_seconds(script_path: Path) -> int:
    text = script_path.read_text(encoding="utf-8")
    cleaned = re.sub(r"\[[^\]]+\]", " ", text)
    words = re.findall(r"[A-Za-z0-9']+", cleaned)
    if not words:
        return 0
    return max(1, math.ceil((len(words) / SCRIPT_WORDS_PER_MINUTE) * 60))


def _parse_timestamp_seconds(value: str) -> float:
    parts = str(value).strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid HH:MM:SS timestamp: {value}")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return (hours * 3600) + (minutes * 60) + seconds


def _normalize_cue_text(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _opening_sequence_declared(opening_sequence: dict[str, Any] | Any) -> bool:
    if not isinstance(opening_sequence, dict):
        return False
    return bool(
        str(opening_sequence.get("planned_scene_id", "")).strip()
        or str(opening_sequence.get("planned_motion_id", "")).strip()
    )


def _normalize_opening_min_duration_seconds(value: Any, *, opener_declared: bool) -> float:
    normalized = max(0.0, _coerce_float(value, 0.0))
    if opener_declared:
        return max(5.0, normalized)
    return normalized


def _normalize_opening_block_downstream_until_approved(value: Any, *, opener_declared: bool) -> bool:
    if isinstance(value, bool):
        return value if opener_declared else False
    token = str(value or "").strip().lower()
    if token in {"true", "1", "yes", "on"}:
        return opener_declared
    if token in {"false", "0", "no", "off"}:
        return False
    return bool(opener_declared)


def _join_sentence_fragments(*parts: Any) -> str:
    fragments: list[str] = []
    for raw in parts:
        text = str(raw or "").strip()
        if not text:
            continue
        if text[-1] not in ".!?":
            text = f"{text}."
        fragments.append(text)
    return " ".join(fragments).strip()


def _distribute_runtime(total_seconds: int, act_count: int) -> list[int]:
    if act_count <= 0:
        return []
    base = total_seconds // act_count
    remainder = total_seconds % act_count
    values: list[int] = []
    for index in range(act_count):
        values.append(base + (1 if index < remainder else 0))
    return values


def required_motion_sequences_for_duration(estimated_seconds: int) -> int:
    if estimated_seconds < 150:
        return 1
    if estimated_seconds <= 300:
        return 2
    return 3


def _extract_label_value(lines: list[str], prefix: str) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith(prefix.lower()):
            return stripped.split(":", 1)[1].strip() if ":" in stripped else ""
    return ""


def _parse_act_breakdown(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    sections: list[tuple[re.Match[str], list[str]]] = []
    current_match: re.Match[str] | None = None
    current_lines: list[str] = []
    for line in lines:
        match = ACT_HEADING_RE.match(line.strip())
        if match:
            if current_match:
                sections.append((current_match, current_lines))
            current_match = match
            current_lines = []
            continue
        if current_match:
            current_lines.append(line)
    if current_match:
        sections.append((current_match, current_lines))

    acts: list[dict[str, Any]] = []
    for match, section_lines in sections:
        act_number = int(match.group("number"))
        title = match.group("title").strip()
        acts.append(
            {
                "id": f"act{act_number}",
                "title": ACT_TITLE_RE.sub("", title).strip(),
                "visual_thesis": _extract_label_value(section_lines, "- Visual thesis"),
                "dominant_signal": _extract_label_value(section_lines, "- Dominant signal"),
            }
        )
    return acts


def _default_reference_board_path(visual_research: dict[str, Any], act_id: str) -> str:
    act_breakdown_path = path_or_none(visual_research.get("act_breakdown_path"))
    if not act_breakdown_path:
        return ""
    return str(act_breakdown_path.parent / "boards" / act_id)


def _default_visual_research_approval(raw: Any) -> dict[str, Any]:
    approval = raw if isinstance(raw, dict) else {}
    return {
        "status": str(approval.get("status", "pending")).strip() or "pending",
        "reviewer": str(approval.get("reviewer", "")).strip(),
        "reviewed_at": str(approval.get("reviewed_at", "")).strip(),
        "notes": str(approval.get("notes", "")).strip(),
        "tags": normalize_review_tags(approval.get("tags")),
    }


def _default_audio_review(raw: Any) -> dict[str, Any]:
    review = raw if isinstance(raw, dict) else {}
    return {
        "status": str(review.get("status", "pending")).strip() or "pending",
        "reviewer": str(review.get("reviewer", "")).strip(),
        "reviewed_at": str(review.get("reviewed_at", "")).strip(),
        "notes": str(review.get("notes", "")).strip(),
        "freshness_override": str(review.get("freshness_override", "")).strip(),
    }


def default_publish_notes_path(context: Context, manifest: dict[str, Any]) -> Path:
    episode_id = str(manifest.get("id", "")).strip()
    episode_info = context.episodes_repo.get_episode_info(episode_id) if episode_id else None
    if episode_info is not None:
        return episode_info.directory / "publish_notes.md"
    script_path = path_or_none(manifest.get("script", {}).get("path"))
    if script_path is not None:
        return script_path.parent / "publish_notes.md"
    fallback_root = Path(str(context.channel["paths"]["episodes_root"]))
    return fallback_root / f"{episode_id or 'episode'}_publish_notes.md"


def _default_youtube_release_section(
    raw: Any,
    *,
    title: str,
    description_path: str,
    scheduled_for: str,
    published_at: str,
    thumbnail_item_id: str = "",
) -> dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    return {
        "status": str(payload.get("status", "todo")).strip() or "todo",
        "title": str(payload.get("title", title)).strip() or title,
        "description_path": str(payload.get("description_path", description_path)).strip() or description_path,
        "tags": _normalize_string_list(payload.get("tags")),
        "privacy": str(payload.get("privacy", "public")).strip() or "public",
        "thumbnail_item_id": str(payload.get("thumbnail_item_id", thumbnail_item_id)).strip() or thumbnail_item_id,
        "video_id": str(payload.get("video_id", "")).strip(),
        "video_url": str(payload.get("video_url", "")).strip(),
        "scheduled_for": str(payload.get("scheduled_for", scheduled_for)).strip() or scheduled_for,
        "published_at": str(payload.get("published_at", published_at)).strip() or published_at,
        "error": str(payload.get("error", "")).strip(),
    }


def _default_podcast_release_section(
    raw: Any,
    *,
    title: str,
    description_path: str,
    scheduled_for: str,
    published_at: str,
    audio_path: str,
) -> dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    return {
        "status": str(payload.get("status", "todo")).strip() or "todo",
        "title": str(payload.get("title", title)).strip() or title,
        "description_path": str(payload.get("description_path", description_path)).strip() or description_path,
        "audio_path": str(payload.get("audio_path", audio_path)).strip() or audio_path,
        "external_id": str(payload.get("external_id", "")).strip(),
        "episode_url": str(payload.get("episode_url", "")).strip(),
        "scheduled_for": str(payload.get("scheduled_for", scheduled_for)).strip() or scheduled_for,
        "published_at": str(payload.get("published_at", published_at)).strip() or published_at,
        "error": str(payload.get("error", "")).strip(),
    }


def audio_package_metadata_path(pipeline_dir: Any) -> Path | None:
    path = path_or_none(pipeline_dir)
    if not path:
        return None
    return path / "audio_package.json"


def _normalize_audio_package_metadata(raw: Any, *, metadata_path: Path | None = None) -> dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    return {
        "metadata_path": str(metadata_path) if metadata_path else "",
        "provider": str(payload.get("provider", "")).strip(),
        "voice": str(payload.get("voice", "")).strip(),
        "model": str(payload.get("model", "")).strip(),
        "voice_profile_id": str(payload.get("voice_profile_id", "")).strip(),
        "disposition": str(payload.get("disposition", "")).strip(),
        "audio_disposition": str(payload.get("audio_disposition", payload.get("disposition", ""))).strip(),
        "voice_profile_settings": copy.deepcopy(payload.get("voice_profile_settings", {}))
        if isinstance(payload.get("voice_profile_settings", {}), dict)
        else {},
        "effective_manifest_path": str(payload.get("effective_manifest_path", "")).strip(),
        "packaged_path": str(payload.get("packaged_path", "")).strip(),
        "packaged_sha256": str(payload.get("packaged_sha256", "")).strip(),
        "packaged_at": str(payload.get("packaged_at", "")).strip(),
        "transcript_path": str(payload.get("transcript_path", "")).strip(),
        "transcript_sha256": str(payload.get("transcript_sha256", "")).strip(),
        "qa_completed_at": str(payload.get("qa_completed_at", "")).strip(),
    }


def load_audio_package_metadata(pipeline_dir: Any) -> dict[str, Any]:
    metadata_path = audio_package_metadata_path(pipeline_dir)
    if not metadata_path or not metadata_path.exists():
        return _normalize_audio_package_metadata({}, metadata_path=metadata_path)
    try:
        loaded = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _normalize_audio_package_metadata({}, metadata_path=metadata_path)
    return _normalize_audio_package_metadata(loaded, metadata_path=metadata_path)


def audio_package_is_promotable(metadata: dict[str, Any]) -> bool:
    packaged_path = str(metadata.get("packaged_path", "")).strip()
    transcript_path = str(metadata.get("transcript_path", "")).strip()
    return bool(
        packaged_path
        and transcript_path
        and str(metadata.get("qa_completed_at", "")).strip()
        and path_exists(packaged_path)
        and path_exists(transcript_path)
    )


def _normalized_path_token(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    path = Path(raw).expanduser()
    try:
        return str(path.resolve(strict=False))
    except OSError:
        return str(path)


def audio_package_differs_from_manifest(audio: dict[str, Any], metadata: dict[str, Any]) -> bool:
    packaged_path = str(metadata.get("packaged_path", "")).strip()
    transcript_path = str(metadata.get("transcript_path", "")).strip()
    if not packaged_path or not transcript_path:
        return False
    current_master = str(audio.get("master_path", "")).strip()
    current_transcript = str(audio.get("transcript_path", "")).strip()
    return _normalized_path_token(current_master) != _normalized_path_token(packaged_path) or _normalized_path_token(
        current_transcript
    ) != _normalized_path_token(transcript_path)


def clear_audio_review_fields(audio: dict[str, Any], *, status: str = "pending") -> None:
    review = _default_audio_review(audio.get("review"))
    review["status"] = status
    review["reviewer"] = ""
    review["reviewed_at"] = ""
    review["notes"] = ""
    audio["review"] = review


def reset_downstream_after_audio_revocation(manifest: dict[str, Any]) -> None:
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
    for target_name in ("youtube", "podcast"):
        target = release.get(target_name)
        if not isinstance(target, dict):
            continue
        target["status"] = "todo"
        for key in ("video_id", "video_url", "external_id", "episode_url", "scheduled_for", "published_at", "error"):
            if key in target:
                target[key] = ""
    analytics = manifest.setdefault("analytics", {})
    analytics["status"] = "todo"


def promote_audio_package(manifest: dict[str, Any]) -> dict[str, Any]:
    audio = manifest.setdefault("audio", {})
    metadata = load_audio_package_metadata(audio.get("pipeline_dir"))
    metadata_path = str(metadata.get("metadata_path", "")).strip()
    if not metadata_path:
        raise SystemExit("Audio package metadata is missing. Run merge and qa before promotion.")
    if not path_exists(metadata_path):
        raise SystemExit(f"Audio package metadata is missing: {metadata_path}")
    if not audio_package_is_promotable(metadata):
        raise SystemExit("Audio package metadata is incomplete. Run merge and qa before promotion.")

    packaged_path = str(metadata.get("packaged_path", "")).strip()
    transcript_path = str(metadata.get("transcript_path", "")).strip()
    review = _default_audio_review(audio.get("review"))
    changed = audio_package_differs_from_manifest(audio, metadata)
    was_approved = str(review.get("status", "")).strip() == "approved" or str(audio.get("status", "")).strip() == "done"

    audio["master_path"] = packaged_path
    audio["transcript_path"] = transcript_path

    if changed:
        clear_audio_review_fields(audio, status="pending")
        audio["status"] = "review"
        if was_approved:
            reset_downstream_after_audio_revocation(manifest)
    elif str(audio.get("status", "")).strip() not in {"review", "done", "not_needed"}:
        audio["status"] = "done" if str(review.get("status", "")).strip() == "approved" else "review"

    return {
        "metadata": metadata,
        "changed": changed,
        "reset_downstream": changed and was_approved,
        "packaged_path": packaged_path,
        "transcript_path": transcript_path,
    }


def _default_visual_research_opening_sequence(raw: Any) -> dict[str, Any]:
    opening = raw if isinstance(raw, dict) else {}
    opener_declared = bool(
        str(opening.get("planned_scene_id", "")).strip() or str(opening.get("planned_motion_id", "")).strip()
    )
    return {
        "object_strategy": _normalize_visual_research_opening_object_strategy(opening.get("object_strategy")),
        "time_period_label": str(opening.get("time_period_label", "")).strip(),
        "supporting_objects": _normalize_string_list(opening.get("supporting_objects")),
        "subject_object": str(opening.get("subject_object", "")).strip(),
        "focus_transition": str(opening.get("focus_transition", "")).strip(),
        "subject_action": str(opening.get("subject_action", "")).strip(),
        "act_id": str(opening.get("act_id", "")).strip(),
        "planned_scene_id": str(opening.get("planned_scene_id", "")).strip(),
        "planned_motion_id": str(opening.get("planned_motion_id", "")).strip(),
        "audio_end_cue_text": str(opening.get("audio_end_cue_text", "")).strip(),
        "min_duration_seconds": _normalize_opening_min_duration_seconds(
            opening.get("min_duration_seconds"),
            opener_declared=opener_declared,
        ),
        "block_downstream_until_approved": _normalize_opening_block_downstream_until_approved(
            opening.get("block_downstream_until_approved"),
            opener_declared=opener_declared,
        ),
        "slots": _normalize_visual_research_opening_slots(opening.get("slots")),
    }


def _normalize_visual_research_opening_slot_role(raw_role: Any) -> str:
    role = str(raw_role or "").strip()
    return role if role in {"supporting_object", "subject_object"} else "supporting_object"


def _normalize_visual_research_opening_object_strategy(raw_strategy: Any) -> str:
    strategy = str(raw_strategy or "").strip()
    return strategy if strategy in {"episode_specific_cluster", "generic_era_cluster"} else "episode_specific_cluster"


def _normalize_visual_research_opening_slot_object_scope(raw_scope: Any) -> str:
    scope = str(raw_scope or "").strip()
    return scope if scope in {"generic_mass_market", "episode_specific"} else "episode_specific"


def _normalize_visual_research_opening_slot_renderability(raw_renderability: Any, *, object_scope: str) -> str:
    renderability = str(raw_renderability or "").strip()
    if renderability == "common_iconic":
        return renderability
    return "common_iconic" if object_scope == "generic_mass_market" else ""


def _default_visual_research_opening_slot_id(raw_slot_id: Any, display_label: str, index: int) -> str:
    candidate = re.sub(r"[^a-z0-9]+", "_", str(raw_slot_id or "").strip().lower()).strip("_")
    if not candidate and display_label:
        candidate = re.sub(r"[^a-z0-9]+", "_", display_label.lower()).strip("_")
    candidate = re.sub(r"_+", "_", candidate)
    return candidate or f"opening_slot_{index}"


def _normalize_visual_research_opening_slots(raw: Any) -> list[dict[str, str]]:
    raw_slots = raw if isinstance(raw, list) else []
    normalized: list[dict[str, str]] = []
    seen_slot_ids: set[str] = set()
    for index, raw_slot in enumerate(raw_slots, start=1):
        slot = raw_slot if isinstance(raw_slot, dict) else {}
        display_label = str(slot.get("display_label", "")).strip() or str(slot.get("label", "")).strip()
        role = _normalize_visual_research_opening_slot_role(slot.get("role"))
        object_scope = _normalize_visual_research_opening_slot_object_scope(slot.get("object_scope"))
        renderability = _normalize_visual_research_opening_slot_renderability(slot.get("renderability"), object_scope=object_scope)
        visual_descriptor = str(slot.get("visual_descriptor", "")).strip()
        slot_id = _default_visual_research_opening_slot_id(slot.get("slot_id"), display_label, index)
        suffix = 2
        base_slot_id = slot_id
        while slot_id in seen_slot_ids:
            slot_id = f"{base_slot_id}_{suffix}"
            suffix += 1
        seen_slot_ids.add(slot_id)
        normalized.append(
            {
                "slot_id": slot_id,
                "display_label": display_label or slot_id.replace("_", " "),
                "role": role,
                "object_scope": object_scope,
                "renderability": renderability,
                "visual_descriptor": visual_descriptor,
            }
        )
    return normalized


def _default_contact_sheet_path(visual_research: dict[str, Any]) -> str:
    explicit = str(visual_research.get("contact_sheet_path", "")).strip()
    if explicit:
        return explicit
    act_breakdown_path = path_or_none(visual_research.get("act_breakdown_path"))
    if act_breakdown_path:
        return str(act_breakdown_path.parent / "contact_sheet.pdf")
    return ""


def _resolve_opening_sequence_timing(manifest: dict[str, Any]) -> dict[str, Any]:
    visual_research = manifest.get("visual_research", {})
    opening_sequence = visual_research.get("opening_sequence", {})
    opener_declared = _opening_sequence_declared(opening_sequence)
    min_duration_seconds = _normalize_opening_min_duration_seconds(
        opening_sequence.get("min_duration_seconds"),
        opener_declared=opener_declared,
    )
    cue_text = str(opening_sequence.get("audio_end_cue_text", "")).strip()
    transcript_path = path_or_none(manifest.get("audio", {}).get("transcript_path"))
    result: dict[str, Any] = {
        "declared": opener_declared,
        "cue_text": cue_text,
        "transcript_path": str(transcript_path) if transcript_path else "",
        "transcript_exists": bool(transcript_path and transcript_path.exists()),
        "opening_audio_start_seconds": 0.0,
        "opening_audio_end_seconds": 0.0,
        "opening_cue_duration_seconds": 0.0,
        "opening_min_duration_seconds": min_duration_seconds,
        "opening_duration_seconds": 0.0,
        "opening_duration_source": "transcript_cue",
        "opening_duration_resolved": False,
        "opening_duration_extended": False,
        "matched_text": "",
        "resolution_reason": "",
    }
    if not opener_declared:
        return result
    if not cue_text:
        result["resolution_reason"] = "missing_cue_text"
        return result
    if transcript_path is None or not transcript_path.exists():
        result["resolution_reason"] = "missing_transcript"
        return result
    cue_token = _normalize_cue_text(cue_text)
    if not cue_token:
        result["resolution_reason"] = "missing_cue_text"
        return result
    for raw_line in transcript_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = DIARIZED_LINE_RE.match(line)
        if not match:
            continue
        transcript_text = match.group("text").strip()
        transcript_token = _normalize_cue_text(transcript_text)
        if transcript_token != cue_token and cue_token not in transcript_token:
            continue
        cue_end_seconds = round(_parse_timestamp_seconds(match.group("end")), 3)
        duration_seconds = round(max(cue_end_seconds, min_duration_seconds), 3)
        result.update(
            {
                "opening_audio_end_seconds": cue_end_seconds,
                "opening_cue_duration_seconds": cue_end_seconds,
                "opening_duration_seconds": duration_seconds,
                "opening_duration_resolved": True,
                "opening_duration_extended": duration_seconds > cue_end_seconds + 1e-6,
                "matched_text": transcript_text,
                "resolution_reason": "matched",
            }
        )
        return result
    result["resolution_reason"] = "cue_not_found"
    return result


def _load_visual_research_source_inventory(visual_research: dict[str, Any]) -> dict[str, Any]:
    inventory_path = default_source_inventory_path(visual_research)
    if not inventory_path:
        return {
            "schema_version": 2,
            "inventory_path": "",
            "sources": [],
            "errors": [],
            "summary": {
                "source_total": 0,
                "approved_source_total": 0,
                "clear_source_total": 0,
                "cleaned_source_total": 0,
                "ready_source_total": 0,
                "ready_source_ids": [],
                "unresolved_source_ids": [],
                "blocked_source_ids": [],
                "missing_downstream_source_ids": [],
                "missing_display_source_ids": [],
                "duplicate_display_source_ids": [],
                "opening_candidate_total": 0,
                "opening_subject_candidate_total": 0,
                "opening_supporting_candidate_total": 0,
                "opening_slot_candidate_totals": {},
                "act_candidate_totals": {},
                "ready_for_generation": True,
            },
        }
    return load_source_inventory(Path(inventory_path))


def _normalize_visual_research_acts(visual_research: dict[str, Any]) -> list[dict[str, Any]]:
    raw_acts = list(visual_research.get("acts") or [])
    act_breakdown_path = path_or_none(visual_research.get("act_breakdown_path"))
    if not raw_acts and act_breakdown_path and act_breakdown_path.exists():
        raw_acts = _parse_act_breakdown(act_breakdown_path)
    runtimes = _distribute_runtime(_coerce_int(visual_research.get("estimated_runtime_seconds")), len(raw_acts))
    normalized_acts: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_acts, start=1):
        act = raw if isinstance(raw, dict) else {}
        act_id = str(act.get("id", "")).strip() or f"act{index}"
        estimated_seconds = _coerce_int(act.get("estimated_seconds"), runtimes[index - 1] if index - 1 < len(runtimes) else 0)
        normalized_acts.append(
            {
                "id": act_id,
                "title": str(act.get("title", "")).strip() or act_id,
                "estimated_seconds": estimated_seconds,
                "beat_count": max(0, _coerce_int(act.get("beat_count"), 0)),
                "visual_thesis": str(act.get("visual_thesis", "")).strip(),
                "dominant_signal": str(act.get("dominant_signal", "")).strip(),
                "reference_board_path": str(act.get("reference_board_path", "")).strip()
                or _default_reference_board_path(visual_research, act_id),
                "required_motion_sequences": required_motion_sequences_for_duration(estimated_seconds),
                "planned_scene_ids": _normalize_string_list(act.get("planned_scene_ids")),
                "planned_motion_ids": _normalize_string_list(act.get("planned_motion_ids")),
                "exception_reason": str(act.get("exception_reason", "")).strip(),
            }
        )
    return normalized_acts


def _copy_with_updates(item: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(item)
    payload.update(updates)
    return payload


def _longest_shared_prefix_score(left: str, right: str) -> int:
    left_parts = [part for part in left.split("_") if part]
    right_parts = [part for part in right.split("_") if part]
    score = 0
    for left_part, right_part in zip(left_parts, right_parts, strict=False):
        if left_part != right_part:
            break
        score += 1
    return score


def _choose_motion_source_scene_id(motion_id: str, scene_ids: list[str]) -> str:
    if not scene_ids:
        return ""
    ranked = sorted(scene_ids, key=lambda scene_id: (_longest_shared_prefix_score(motion_id, scene_id), -len(scene_id)), reverse=True)
    return ranked[0]


def _materialize_visual_research(manifest: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(manifest)
    visual_research = copy.deepcopy(payload.get("visual_research", {}))
    script_path = path_or_none(payload.get("script", {}).get("path"))
    current_sha = ""
    current_runtime = 0
    if script_path and script_path.exists():
        current_sha = _sha256_path(script_path)
        current_runtime = _estimate_script_runtime_seconds(script_path)
        visual_research["script_source_path"] = str(script_path)
        visual_research["estimated_runtime_seconds"] = current_runtime
    stored_sha = str(visual_research.get("script_sha256", "")).strip()
    approval = _default_visual_research_approval(visual_research.get("approval"))
    opening_sequence = _default_visual_research_opening_sequence(visual_research.get("opening_sequence"))
    visual_research["source_origin_policy"] = str(visual_research.get("source_origin_policy", "any")).strip() or "any"
    script_sha_mismatch = bool(stored_sha and current_sha and stored_sha != current_sha)
    if current_sha:
        if script_sha_mismatch and approval["status"] == "approved":
            approval["status"] = "pending"
            approval["reviewer"] = ""
            approval["reviewed_at"] = ""
            approval["tags"] = []
            if str(visual_research.get("status", "")).strip() == "done":
                visual_research["status"] = "review"
        visual_research["script_sha256"] = current_sha
    approval["tags"] = (
        infer_reject_tags(
            str(payload.get("id", "")),
            "visual_research",
            "visual_research",
            current_tags=approval.get("tags"),
        )
        if approval.get("status") == "rejected"
        else []
    )
    visual_research["contact_sheet_path"] = _default_contact_sheet_path(visual_research)
    visual_research["source_inventory_path"] = default_source_inventory_path(visual_research)
    visual_research["approval"] = approval
    visual_research["opening_sequence"] = opening_sequence
    visual_research["_script_sha_mismatch"] = script_sha_mismatch
    source_inventory = _load_visual_research_source_inventory(visual_research)
    visual_research["_source_inventory"] = source_inventory
    acts = _normalize_visual_research_acts(visual_research)
    visual_research["acts"] = acts
    visual_research["act_count"] = len(acts)
    visual_research["beat_count_total"] = sum(int(act["beat_count"]) for act in acts)
    visual_research["required_motion_total"] = sum(int(act["required_motion_sequences"]) for act in acts)
    visual_research["planned_motion_total"] = sum(len(act["planned_motion_ids"]) for act in acts)
    latest_reject_tags = derive_latest_reject_tags(payload)
    visual_research["guardrails"] = derive_visual_research_guardrails(
        str(payload.get("id", "")),
        opening_sequence,
        acts,
        visual_research.get("guardrails"),
        latest_reject_tags,
        source_inventory.get("summary"),
    )
    payload["visual_research"] = visual_research
    return payload


def _materialize_item_review_metadata(manifest: dict[str, Any]) -> None:
    episode_id = str(manifest.get("id", "")).strip()
    for item in manifest.get("scene_stills", {}).get("items", []):
        item.setdefault("approved_proof_path", "")
        item.setdefault("approved_proof_manifest_path", "")
        item.setdefault("reviewer", "")
        item.setdefault("reviewed_at", "")
        item.setdefault("review_notes", "")
        item["review_tags"] = (
            infer_reject_tags(
                episode_id,
                "scene_still",
                str(item.get("id", "")).strip(),
                current_tags=item.get("review_tags"),
            )
            if str(item.get("review_status", "")).strip() == "rejected"
            else []
        )
        item.setdefault("motion_reviewer", "")
        item.setdefault("motion_reviewed_at", "")
        item.setdefault("motion_review_notes", "")
        item["motion_review_tags"] = (
            infer_reject_tags(
                episode_id,
                "motion_source",
                str(item.get("id", "")).strip(),
                current_tags=item.get("motion_review_tags"),
            )
            if str(item.get("motion_review_status", "")).strip() == "rejected"
            else []
        )
    for item in manifest.get("packaging_stills", {}).get("items", []):
        item.setdefault("approved_proof_path", "")
        item.setdefault("approved_proof_manifest_path", "")
        item.setdefault("reviewer", "")
        item.setdefault("reviewed_at", "")
        item.setdefault("review_notes", "")
        item["review_tags"] = (
            infer_reject_tags(
                episode_id,
                "packaging_still",
                str(item.get("id", "")).strip(),
                current_tags=item.get("review_tags"),
            )
            if str(item.get("review_status", "")).strip() == "rejected"
            else []
        )
    for item in manifest.get("motion_assets", {}).get("items", []):
        item.setdefault("behavior", "")
        item.setdefault("review_outcome", "")
        item.setdefault("reviewer", "")
        item.setdefault("reviewed_at", "")
        item.setdefault("review_notes", "")
        item.setdefault("authoring_mode", "legacy_i2v")
        item.setdefault("workbench_project_path", "")
        item["review_tags"] = (
            infer_reject_tags(
                episode_id,
                "motion_asset",
                str(item.get("id", "")).strip(),
                current_tags=item.get("review_tags"),
            )
            if str(item.get("review_outcome", "")).strip() == "rejected"
            else []
        )
        item.setdefault("min_duration_seconds", 0.0)


def _materialize_visual_research_guardrails(manifest: dict[str, Any]) -> None:
    visual_research = manifest.get("visual_research", {})
    opening_sequence = visual_research.get("opening_sequence", {})
    source_inventory = visual_research.get("_source_inventory", {})
    visual_research["guardrails"] = derive_visual_research_guardrails(
        str(manifest.get("id", "")),
        opening_sequence if isinstance(opening_sequence, dict) else {},
        list(visual_research.get("acts") or []),
        visual_research.get("guardrails"),
        derive_latest_reject_tags(manifest),
        source_inventory.get("summary") if isinstance(source_inventory, dict) else None,
    )


def _materialize_audio_section(manifest: dict[str, Any]) -> None:
    audio = copy.deepcopy(manifest.get("audio", {}))
    status = str(audio.get("status", "todo")).strip() or "todo"
    review = _default_audio_review(audio.get("review"))
    audio["pipeline_dir"] = str(audio.get("pipeline_dir", "")).strip()
    audio["master_path"] = str(audio.get("master_path", "")).strip()
    audio["transcript_path"] = str(audio.get("transcript_path", "")).strip()
    master_ready = path_exists(audio["master_path"])
    transcript_ready = path_exists(audio["transcript_path"])
    ready_for_review = master_ready and transcript_ready
    if status == "not_needed":
        resolved_status = "not_needed"
    elif ready_for_review:
        resolved_status = "done" if review["status"] == "approved" else "review"
    elif status in {"review", "done"}:
        resolved_status = "todo"
    else:
        resolved_status = status
    audio["status"] = resolved_status
    audio["review"] = review
    manifest["audio"] = audio


def _materialize_opening_timing(manifest: dict[str, Any]) -> None:
    visual_research = manifest.get("visual_research", {})
    visual_research["_opening_timing"] = _resolve_opening_sequence_timing(manifest)
    manifest["visual_research"] = visual_research


def _default_thumbnail_item_id(manifest: dict[str, Any]) -> str:
    for item in manifest.get("packaging_stills", {}).get("items", []):
        if str(item.get("kind", "")).strip() != "thumbnail":
            continue
        if not bool(item.get("required", True)):
            continue
        item_id = str(item.get("id", "")).strip()
        if item_id:
            return item_id
    return ""


def _materialize_release_section(context: Context, manifest: dict[str, Any]) -> None:
    release = copy.deepcopy(manifest.get("release", {}))
    notes_path = str(release.get("notes_path", "")).strip() or str(default_publish_notes_path(context, manifest))
    scheduled_for = str(release.get("scheduled_for", "")).strip()
    published_at = str(release.get("published_at", "")).strip()
    release["status"] = str(release.get("status", "todo")).strip() or "todo"
    release["scheduled_for"] = scheduled_for
    release["published_at"] = published_at
    release["notes"] = str(release.get("notes", "")).strip()
    release["notes_path"] = notes_path
    release["youtube"] = _default_youtube_release_section(
        release.get("youtube"),
        title=str(manifest.get("title", "")).strip(),
        description_path=notes_path,
        scheduled_for=scheduled_for,
        published_at=published_at,
        thumbnail_item_id=_default_thumbnail_item_id(manifest),
    )
    release["podcast"] = _default_podcast_release_section(
        release.get("podcast"),
        title=str(manifest.get("title", "")).strip(),
        description_path=notes_path,
        scheduled_for=scheduled_for,
        published_at=published_at,
        audio_path=str(manifest.get("audio", {}).get("master_path", "")).strip(),
    )
    manifest["release"] = release


def _materialize_motion_contract_metadata(context: Context, manifest: dict[str, Any]) -> None:
    episode_id = str(manifest.get("id", "")).strip()
    for item in manifest.get("motion_assets", {}).get("items", []):
        motion_item_id = str(item.get("id", "")).strip()
        item["authoring_mode"] = str(item.get("authoring_mode", "legacy_i2v")).strip() or "legacy_i2v"
        if motion_item_id and not str(item.get("workbench_project_path", "")).strip():
            item["workbench_project_path"] = str(build_motion_workbench_project_path(context, episode_id, motion_item_id))
        if not motion_item_id:
            item.setdefault("min_duration_seconds", 0.0)
            continue
        certification = context.viz_repo.find_motion_certification(episode_id, motion_item_id)
        preset_id = certification.preset_id if certification else ""
        existing_min_duration = _coerce_float(item.get("min_duration_seconds"), 0.0)
        guardrail_min_duration = _coerce_float(
            context.viz_repo.find_motion_guardrails(
                episode_id,
                motion_item_id,
                preset_id=preset_id,
            ).get("min_duration_seconds", 0.0),
            0.0,
        )
        item["min_duration_seconds"] = max(existing_min_duration, guardrail_min_duration)


def _materialize_tracking_section(manifest: dict[str, Any]) -> None:
    tracking = copy.deepcopy(manifest.get("tracking", {}))
    bootstrapped_at = str(tracking.get("bootstrapped_at", "")).strip()
    existing_source = str(tracking.get("_bootstrapped_at_source", "")).strip()
    if bootstrapped_at:
        tracking["bootstrapped_at"] = bootstrapped_at
        tracking["_bootstrapped_at_source"] = existing_source or "tracking.bootstrapped_at"
    else:
        manifest_path = path_or_none(manifest.get("_manifest_path"))
        if manifest_path and manifest_path.exists():
            tracking["bootstrapped_at"] = file_mtime_iso(manifest_path)
            tracking["_bootstrapped_at_source"] = "manifest_mtime"
        else:
            tracking["bootstrapped_at"] = ""
            tracking["_bootstrapped_at_source"] = "missing"
    manifest["tracking"] = tracking


def _materialize_assembly_section(manifest: dict[str, Any]) -> None:
    assembly = copy.deepcopy(manifest.get("assembly", {}))
    assembly.setdefault("status", "todo")
    assembly.setdefault("owner", "agent")
    assembly.setdefault("renderer", "ffmpeg")
    assembly.setdefault("strategy", "act_spine")
    assembly.setdefault("notes", "")
    assembly.setdefault("master_video_path", "")
    assembly.setdefault("completed_at", "")
    raw_transitions = assembly.get("transitions", [])
    normalized_transitions: list[dict[str, Any]] = []
    if isinstance(raw_transitions, list):
        for item in raw_transitions:
            if isinstance(item, dict):
                try:
                    duration_seconds = float(str(item.get("duration_seconds", "0") or "0").strip() or "0")
                except ValueError:
                    duration_seconds = 0.0
                normalized_transitions.append(
                    {
                        "from_act": str(item.get("from_act", "")).strip(),
                        "to_act": str(item.get("to_act", "")).strip(),
                        "video": str(item.get("video", "cut")).strip() or "cut",
                        "audio": str(item.get("audio", "cut")).strip() or "cut",
                        "duration_seconds": duration_seconds,
                    }
                )
    assembly["transitions"] = normalized_transitions
    raw_compositions = assembly.get("compositions", [])
    normalized_compositions: list[dict[str, Any]] = []
    if isinstance(raw_compositions, list):
        for item in raw_compositions:
            if not isinstance(item, dict):
                continue
            raw_overlays = item.get("overlays", [])
            normalized_overlays: list[dict[str, Any]] = []
            if isinstance(raw_overlays, list):
                for overlay in raw_overlays:
                    if not isinstance(overlay, dict):
                        continue
                    normalized_overlays.append(
                        {
                            "motion_asset_id": str(overlay.get("motion_asset_id", "")).strip(),
                            "start_seconds": _coerce_float(overlay.get("start_seconds", 0.0), 0.0),
                            "duration_seconds": _coerce_float(overlay.get("duration_seconds", 0.0), 0.0),
                            "x": None if overlay.get("x") in {None, ""} else _coerce_float(overlay.get("x", 0.0), 0.0),
                            "y": None if overlay.get("y") in {None, ""} else _coerce_float(overlay.get("y", 0.0), 0.0),
                            "scale": _coerce_float(overlay.get("scale", 1.0), 1.0),
                            "opacity": _coerce_float(overlay.get("opacity", 1.0), 1.0),
                            "blend_mode": str(overlay.get("blend_mode", "normal")).strip() or "normal",
                            "hold_last_frame": bool(overlay.get("hold_last_frame", False)),
                        }
                    )
            normalized_compositions.append(
                {
                    "act_id": str(item.get("act_id", "")).strip(),
                    "base_asset_id": str(item.get("base_asset_id", "")).strip(),
                    "overlays": normalized_overlays,
                }
            )
    assembly["compositions"] = normalized_compositions
    manifest["assembly"] = assembly


def _motion_item_is_overlay_target(manifest: dict[str, Any], motion_item_id: str) -> bool:
    for composition in manifest.get("assembly", {}).get("compositions", []):
        if not isinstance(composition, dict):
            continue
        for overlay in composition.get("overlays", []):
            if not isinstance(overlay, dict):
                continue
            if str(overlay.get("motion_asset_id", "")).strip() == motion_item_id:
                return True
    return False


def _materialize_overlay_motion_output_paths(context: Context, manifest: dict[str, Any]) -> None:
    episode_id = str(manifest.get("id", "")).strip()
    if not episode_id:
        return
    for item in manifest.get("motion_assets", {}).get("items", []):
        motion_item_id = str(item.get("id", "")).strip()
        if not motion_item_id or not _motion_item_is_overlay_target(manifest, motion_item_id):
            continue
        if str(item.get("authoring_mode", "")).strip() != "particle_workbench":
            continue
        output_path = str(item.get("output_path", "")).strip()
        if not output_path:
            item["output_path"] = str(build_motion_output_path(context, episode_id, motion_item_id).with_suffix(".mov"))
            continue
        current_path = Path(output_path).expanduser()
        if current_path.suffix.lower() == ".mov":
            continue
        if str(item.get("status", "")).strip() == "done" and str(item.get("latest_render_path", "")).strip():
            continue
        item["output_path"] = str(current_path.with_suffix(".mov"))


def _seed_scene_items_from_visual_research(context: Context, manifest: dict[str, Any]) -> None:
    visual_research = manifest.get("visual_research", {})
    approval = visual_research.get("approval", {})
    if str(approval.get("status", "")).strip() != "approved":
        return
    acts = list(visual_research.get("acts") or [])
    opening_sequence = visual_research.get("opening_sequence", {})
    opening_scene_id = str(opening_sequence.get("planned_scene_id", "")).strip()
    opening_motion_id = str(opening_sequence.get("planned_motion_id", "")).strip()
    opening_scene_archetype = find_scene_archetype(context, "opening_culture_cluster") if opening_scene_id else None
    expected_specs: list[dict[str, Any]] = []
    motion_source_candidates: set[str] = set()
    if opening_scene_id:
        expected_specs.append(
            {
                "id": opening_scene_id,
                "act": "opening",
                "purpose": (
                    "Pre-act opening tableau of time-period culture objects hovering together while the focal subject "
                    "is prepared for isolation before act 1 begins."
                ),
                "archetype_status": "resolved",
                "archetype_id": "opening_culture_cluster",
                "preset": str(opening_scene_archetype.get("preset", "")).strip() if opening_scene_archetype else "",
                "notes": "Seeded from visual_research opening_sequence as the shared pre-act opener.",
                "motion_review_status": "pending" if opening_motion_id else "not_planned",
            }
        )
        if opening_motion_id:
            motion_source_candidates.add(opening_scene_id)
    for act in acts:
        planned_scene_ids = _normalize_string_list(act.get("planned_scene_ids"))
        if planned_scene_ids:
            for scene_id in planned_scene_ids:
                expected_specs.append(
                    {
                        "id": scene_id,
                        "act": str(act.get("id", "")).strip() or "tbd",
                        "purpose": f"Planned scene still for {str(act.get('title', scene_id)).strip()}.",
                        "archetype_status": "unresolved",
                        "archetype_id": "",
                        "preset": "",
                        "notes": f"Seeded from visual_research act `{str(act.get('id', '')).strip() or 'unknown'}`.",
                        "motion_review_status": "",
                    }
                )
        for motion_id in _normalize_string_list(act.get("planned_motion_ids")):
            source_scene_id = _choose_motion_source_scene_id(motion_id, planned_scene_ids)
            if source_scene_id:
                motion_source_candidates.add(source_scene_id)
    if not expected_specs:
        return

    episode_id = str(manifest["id"])
    existing_items = list(manifest.get("scene_stills", {}).get("items", []))
    existing_by_id = {str(item.get("id", "")): copy.deepcopy(item) for item in existing_items if str(item.get("id", "")).strip()}
    expected_items: list[dict[str, Any]] = []
    for spec in expected_specs:
        scene_id = str(spec["id"]).strip()
        existing = existing_by_id.pop(scene_id, None)
        default_review_status = "blocked"
        default_motion_review_status = str(spec.get("motion_review_status", "")).strip() or (
            "pending" if scene_id in motion_source_candidates else "not_planned"
        )
        if existing is None:
            expected_items.append(
                {
                    "id": scene_id,
                    "act": str(spec.get("act", "")).strip() or "tbd",
                    "purpose": str(spec.get("purpose", "")).strip() or f"Planned scene still for {scene_id}.",
                    "preset": str(spec.get("preset", "")).strip(),
                    "reference_dir": "",
                    "output_path": "",
                    "latest_render_path": "",
                    "latest_render_manifest_path": "",
                    "approved_proof_path": "",
                    "approved_proof_manifest_path": "",
                    "selected_asset": "",
                    "required": True,
                    "review_status": default_review_status,
                    "motion_review_status": default_motion_review_status,
                    "reviewer": "",
                    "reviewed_at": "",
                    "review_notes": "",
                    "review_tags": [],
                    "motion_reviewer": "",
                    "motion_reviewed_at": "",
                    "motion_review_notes": "",
                    "motion_review_tags": [],
                    "archetype_status": str(spec.get("archetype_status", "")).strip() or "unresolved",
                    "archetype_id": str(spec.get("archetype_id", "")).strip(),
                    "notes": str(spec.get("notes", "")).strip(),
                }
            )
            continue
        if not existing.get("act"):
            existing["act"] = str(spec.get("act", "")).strip() or existing.get("act", "tbd")
        if not existing.get("purpose"):
            existing["purpose"] = str(spec.get("purpose", "")).strip() or f"Planned scene still for {scene_id}."
        if not existing.get("preset") and str(spec.get("preset", "")).strip():
            existing["preset"] = str(spec.get("preset", "")).strip()
        if not existing.get("motion_review_status"):
            existing["motion_review_status"] = default_motion_review_status
        if not str(existing.get("archetype_status", "")).strip():
            existing["archetype_status"] = str(spec.get("archetype_status", "")).strip() or "unresolved"
        if not str(existing.get("archetype_id", "")).strip() and str(spec.get("archetype_id", "")).strip():
            existing["archetype_id"] = str(spec.get("archetype_id", "")).strip()
        if not str(existing.get("notes", "")).strip() and str(spec.get("notes", "")).strip():
            existing["notes"] = str(spec.get("notes", "")).strip()
        expected_items.append(existing)
    for item in expected_items:
        if not str(item.get("reference_dir", "")).strip():
            item["reference_dir"] = str(build_episode_reference_dir(context, episode_id, str(item["id"])))
    for item in expected_items:
        if not str(item.get("output_path", "")).strip():
            item["output_path"] = str(build_scene_output_path(context, episode_id, item, expected_items))
    extras = list(existing_by_id.values())
    manifest.setdefault("scene_stills", {})["items"] = expected_items + extras


def _seed_motion_items_from_visual_research(context: Context, manifest: dict[str, Any]) -> None:
    visual_research = manifest.get("visual_research", {})
    approval = visual_research.get("approval", {})
    if str(approval.get("status", "")).strip() != "approved":
        return
    acts = list(visual_research.get("acts") or [])
    opening_sequence = visual_research.get("opening_sequence", {})
    opening_scene_id = str(opening_sequence.get("planned_scene_id", "")).strip()
    opening_motion_id = str(opening_sequence.get("planned_motion_id", "")).strip()
    opening_motion_archetype = find_motion_archetype(context, "opening_subject_pull_in") if opening_motion_id else None
    opener_min_duration_seconds = _normalize_opening_min_duration_seconds(
        opening_sequence.get("min_duration_seconds"),
        opener_declared=bool(opening_scene_id or opening_motion_id),
    )
    expected_specs: list[dict[str, Any]] = []
    if opening_scene_id and opening_motion_id:
        expected_specs.append(
            {
                "id": opening_motion_id,
                "source_still_id": opening_scene_id,
                "archetype_id": "opening_subject_pull_in",
                "behavior": _join_sentence_fragments(
                    opening_sequence.get("focus_transition", ""),
                    opening_sequence.get("subject_action", ""),
                ),
                "frames": int(opening_motion_archetype.get("frames", 33)) if opening_motion_archetype else 33,
                "width": int(opening_motion_archetype.get("width", 640)) if opening_motion_archetype else 640,
                "height": int(opening_motion_archetype.get("height", 384)) if opening_motion_archetype else 384,
                "pipeline": str(opening_motion_archetype.get("pipeline", "distilled")) if opening_motion_archetype else "distilled",
                "min_duration_seconds": opener_min_duration_seconds,
                "notes": "Seeded from visual_research opening_sequence as the shared pre-act opener.",
            }
        )
    for act in acts:
        planned_scene_ids = _normalize_string_list(act.get("planned_scene_ids"))
        for motion_id in _normalize_string_list(act.get("planned_motion_ids")):
            source_scene_id = _choose_motion_source_scene_id(motion_id, planned_scene_ids)
            if source_scene_id:
                expected_specs.append(
                    {
                        "id": motion_id,
                        "source_still_id": source_scene_id,
                        "archetype_id": "",
                        "behavior": "",
                        "frames": 33,
                        "width": 640,
                        "height": 384,
                        "pipeline": "distilled",
                        "min_duration_seconds": _coerce_float(
                            context.viz_repo.find_motion_guardrails(str(manifest["id"]), motion_id).get("min_duration_seconds", 0.0),
                            0.0,
                        ),
                        "notes": f"Seeded from visual_research source still `{source_scene_id}`.",
                    }
                )
    if not expected_specs:
        return

    episode_id = str(manifest["id"])
    existing_items = list(manifest.get("motion_assets", {}).get("items", []))
    existing_by_id = {str(item.get("id", "")): copy.deepcopy(item) for item in existing_items if str(item.get("id", "")).strip()}
    expected_items: list[dict[str, Any]] = []
    for spec in expected_specs:
        motion_id = str(spec["id"]).strip()
        source_scene_id = str(spec["source_still_id"]).strip()
        existing = existing_by_id.pop(motion_id, None)
        if existing is None:
            expected_items.append(
                {
                    "id": motion_id,
                    "source_still_id": source_scene_id,
                    "archetype_id": str(spec.get("archetype_id", "")).strip(),
                    "prompt": "",
                    "behavior": str(spec.get("behavior", "")).strip(),
                    "frames": int(spec.get("frames", 33) or 33),
                    "width": int(spec.get("width", 640) or 640),
                    "height": int(spec.get("height", 384) or 384),
                    "pipeline": str(spec.get("pipeline", "distilled") or "distilled"),
                    "authoring_mode": "legacy_i2v",
                    "workbench_project_path": str(build_motion_workbench_project_path(context, episode_id, motion_id)),
                    "output_path": str(build_motion_output_path(context, episode_id, motion_id)),
                    "latest_render_path": "",
                    "latest_render_manifest_path": "",
                    "status": "todo",
                    "review_outcome": "",
                    "reviewer": "",
                    "reviewed_at": "",
                    "review_notes": "",
                    "review_tags": [],
                    "min_duration_seconds": _coerce_float(spec.get("min_duration_seconds"), 0.0),
                    "notes": str(spec.get("notes", "")).strip(),
                }
            )
            continue
        if not str(existing.get("source_still_id", "")).strip():
            existing["source_still_id"] = source_scene_id
        if not str(existing.get("archetype_id", "")).strip() and str(spec.get("archetype_id", "")).strip():
            existing["archetype_id"] = str(spec.get("archetype_id", "")).strip()
        if not str(existing.get("behavior", "")).strip() and str(spec.get("behavior", "")).strip():
            existing["behavior"] = str(spec.get("behavior", "")).strip()
        if not str(existing.get("output_path", "")).strip():
            existing["output_path"] = str(build_motion_output_path(context, episode_id, motion_id))
        if not str(existing.get("authoring_mode", "")).strip():
            existing["authoring_mode"] = "legacy_i2v"
        if not str(existing.get("workbench_project_path", "")).strip():
            existing["workbench_project_path"] = str(build_motion_workbench_project_path(context, episode_id, motion_id))
        if not existing.get("frames"):
            existing["frames"] = int(spec.get("frames", 33) or 33)
        if not existing.get("width"):
            existing["width"] = int(spec.get("width", 640) or 640)
        if not existing.get("height"):
            existing["height"] = int(spec.get("height", 384) or 384)
        if not str(existing.get("pipeline", "")).strip():
            existing["pipeline"] = str(spec.get("pipeline", "distilled") or "distilled")
        existing["min_duration_seconds"] = max(
            _coerce_float(existing.get("min_duration_seconds"), 0.0),
            _coerce_float(spec.get("min_duration_seconds"), 0.0),
        )
        if not str(existing.get("notes", "")).strip() and str(spec.get("notes", "")).strip():
            existing["notes"] = str(spec.get("notes", "")).strip()
        expected_items.append(existing)
    extras = list(existing_by_id.values())
    manifest.setdefault("motion_assets", {})["items"] = expected_items + extras


def materialize_episode_manifest(context: Context, manifest: dict[str, Any]) -> dict[str, Any]:
    payload = _materialize_visual_research(manifest)
    _materialize_tracking_section(payload)
    _materialize_audio_section(payload)
    _materialize_opening_timing(payload)
    _materialize_release_section(context, payload)
    _materialize_item_review_metadata(payload)
    _materialize_motion_contract_metadata(context, payload)
    _materialize_visual_research_guardrails(payload)
    _materialize_assembly_section(payload)
    _seed_scene_items_from_visual_research(context, payload)
    _seed_motion_items_from_visual_research(context, payload)
    _materialize_overlay_motion_output_paths(context, payload)
    _materialize_tracking_section(payload)
    _materialize_release_section(context, payload)
    _materialize_item_review_metadata(payload)
    _materialize_motion_contract_metadata(context, payload)
    _materialize_visual_research_guardrails(payload)
    _materialize_assembly_section(payload)
    return payload


def table_status(manifest: dict[str, Any], name: str, default: str = "todo") -> str:
    table = manifest.get(name, {})
    return str(table.get("status", default))


def list_episode_manifest_paths(context: Context) -> list[Path]:
    return sorted((context.root / "episodes").glob("*.toml"))


def load_episode_manifest(path: Path) -> dict[str, Any]:
    manifest = load_toml(path)
    manifest["_manifest_path"] = str(path)
    return manifest


def list_episode_manifests(context: Context) -> list[dict[str, Any]]:
    return [materialize_episode_manifest(context, load_episode_manifest(path)) for path in list_episode_manifest_paths(context)]


def resolve_episode_directories(context: Context, episode: str | None, select_all: bool) -> list[Path]:
    return context.episodes_repo.resolve_episode_directories(episode, select_all)


def find_scene_archetype(context: Context, archetype_id: str | None) -> dict[str, Any] | None:
    if not archetype_id:
        return None
    scene_archetypes = context.asset_archetypes.get("scene_archetypes", {})
    archetype = scene_archetypes.get(archetype_id)
    if not archetype:
        raise SystemExit(f"Unknown scene archetype: {archetype_id}")
    return archetype


def find_motion_archetype(context: Context, archetype_id: str | None) -> dict[str, Any] | None:
    if not archetype_id:
        return None
    motion_archetypes = context.asset_archetypes.get("motion_archetypes", {})
    archetype = motion_archetypes.get(archetype_id)
    if not archetype:
        raise SystemExit(f"Unknown motion archetype: {archetype_id}")
    return archetype


def _format_pillar_label(pillar: str) -> str:
    return pillar.replace("-", " ").replace("_", " ").title()


def _derive_visual_research_status(info: EpisodeDirectoryInfo) -> str:
    return "review" if all(path.exists() for path in info.visual_research_paths.values()) else "todo"


def _build_bootstrap_scene_item(
    context: Context,
    scene_archetype_id: str | None,
    title: str,
    episode_id: str,
) -> tuple[dict[str, Any], str]:
    archetype = find_scene_archetype(context, scene_archetype_id)
    if not archetype:
        return (
            {
                "id": "primary_scene_hero",
                "act": "tbd",
                "purpose": f"Primary scene still for {title}; scene archetype remains unresolved.",
                "preset": "",
                "reference_dir": "",
                "output_path": "",
                "latest_render_path": "",
                "latest_render_manifest_path": "",
                "approved_proof_path": "",
                "approved_proof_manifest_path": "",
                "selected_asset": "",
                "required": True,
                "review_status": "blocked",
                "motion_review_status": "blocked",
                "reviewer": "",
                "reviewed_at": "",
                "review_notes": "",
                "review_tags": [],
                "motion_reviewer": "",
                "motion_reviewed_at": "",
                "motion_review_notes": "",
                "motion_review_tags": [],
                "archetype_status": "unresolved",
                "archetype_id": "",
                "notes": "Scene archetype unresolved.",
            },
            "blocked",
        )
    item = {
        "id": "primary_scene_hero",
        "act": "tbd",
        "purpose": f"Primary scene still for {title}.",
        "preset": str(archetype["preset"]),
        "reference_dir": "",
        "output_path": "",
        "latest_render_path": "",
        "latest_render_manifest_path": "",
        "approved_proof_path": "",
        "approved_proof_manifest_path": "",
        "selected_asset": "",
        "required": True,
        "review_status": "pending",
        "motion_review_status": "pending",
        "reviewer": "",
        "reviewed_at": "",
        "review_notes": "",
        "review_tags": [],
        "motion_reviewer": "",
        "motion_reviewed_at": "",
        "motion_review_notes": "",
        "motion_review_tags": [],
        "archetype_status": "resolved",
        "archetype_id": scene_archetype_id,
        "notes": str(archetype.get("notes", "")),
    }
    item["reference_dir"] = str(build_episode_reference_dir(context, episode_id, item["id"]))
    item["output_path"] = str(build_scene_output_path(context, episode_id, item, [item]))
    return (item, "todo")


def _build_bootstrap_packaging_items(context: Context, episode_id: str) -> list[dict[str, Any]]:
    defaults = context.asset_archetypes.get("defaults", {})
    items = [
        {
            "id": "primary_thumbnail",
            "kind": "thumbnail",
            "purpose": "Primary episode thumbnail.",
            "preset": str(defaults["thumbnail_preset"]),
            "reference_dir": "",
            "output_path": "",
            "latest_render_path": "",
            "latest_render_manifest_path": "",
            "approved_proof_path": "",
            "approved_proof_manifest_path": "",
            "selected_asset": "",
            "required": True,
            "review_status": "pending",
            "reviewer": "",
            "reviewed_at": "",
            "review_notes": "",
            "review_tags": [],
        },
        {
            "id": "primary_shorts_cover",
            "kind": "shorts_cover",
            "purpose": "Primary shorts cover.",
            "preset": str(defaults["shorts_preset"]),
            "reference_dir": "",
            "output_path": "",
            "latest_render_path": "",
            "latest_render_manifest_path": "",
            "approved_proof_path": "",
            "approved_proof_manifest_path": "",
            "selected_asset": "",
            "required": True,
            "review_status": "pending",
            "reviewer": "",
            "reviewed_at": "",
            "review_notes": "",
            "review_tags": [],
        },
    ]
    for item in items:
        item["reference_dir"] = str(build_episode_reference_dir(context, episode_id, item["id"]))
        item["output_path"] = str(build_packaging_output_path(context, episode_id, item, items))
    return items


def _build_bootstrap_motion_item(
    context: Context,
    scene_item: dict[str, Any],
    scene_archetype_id: str | None,
    episode_id: str,
) -> dict[str, Any]:
    scene_archetype = find_scene_archetype(context, scene_archetype_id)
    motion_archetype_id = str(scene_archetype.get("default_motion_archetype_id", "")).strip() if scene_archetype else ""
    motion_archetype = find_motion_archetype(context, motion_archetype_id) if motion_archetype_id else None
    reference_dir = str(scene_item.get("reference_dir", "")).strip()
    output_path = (
        str(Path(reference_dir) / "selects" / "hero_video.mp4")
        if reference_dir
        else str(Path(context.channel["paths"]["ai_root"]) / "outputs" / "mlx-video" / f"{episode_id}_proof.mp4")
    )
    certification = context.viz_repo.find_motion_certification(episode_id, "primary_scene_motion")
    return {
        "id": "primary_scene_motion",
        "source_still_id": scene_item["id"],
        "archetype_id": motion_archetype_id,
        "prompt": certification.prompt if certification else str(motion_archetype.get("prompt", "")) if motion_archetype else "",
        "behavior": "",
        "frames": certification.frames if certification else int(motion_archetype.get("frames", 33)) if motion_archetype else 33,
        "width": certification.width if certification else int(motion_archetype.get("width", 640)) if motion_archetype else 640,
        "height": certification.height if certification else int(motion_archetype.get("height", 384)) if motion_archetype else 384,
        "pipeline": certification.pipeline if certification else str(motion_archetype.get("pipeline", "distilled")) if motion_archetype else "distilled",
        "authoring_mode": "legacy_i2v",
        "workbench_project_path": str(build_motion_workbench_project_path(context, episode_id, "primary_scene_motion")),
        "output_path": output_path,
        "latest_render_path": "",
        "latest_render_manifest_path": "",
        "status": "todo",
        "review_outcome": "",
        "reviewer": "",
        "reviewed_at": "",
        "review_notes": "",
        "review_tags": [],
        "min_duration_seconds": (
            float(certification.min_duration_seconds)
            if certification
            else float(context.viz_repo.find_motion_guardrails(episode_id, "primary_scene_motion").get("min_duration_seconds", 0.0) or 0.0)
        ),
    }


def build_bootstrap_manifest(
    context: Context,
    episode_dir: Path,
    *,
    scene_archetype_id: str | None,
    pillar: str,
) -> dict[str, Any]:
    info = context.episodes_repo.parse_episode_directory(episode_dir)
    defaults = context.asset_archetypes.get("defaults", {})
    web_entry = context.web_repo.get_launch_entry(info.episode_id)
    resolved_pillar = context.web_repo.infer_pillar_id(web_entry.label) if web_entry else pillar
    resolved_pillar = resolved_pillar or pillar
    resolved_title = web_entry.title if web_entry else info.title
    resolved_label = web_entry.label if web_entry else f"{_format_pillar_label(resolved_pillar)} · Launch Episode {info.number:02d}"
    resolved_summary = web_entry.summary if web_entry else ""
    scene_item, scene_lane_status = _build_bootstrap_scene_item(context, scene_archetype_id, resolved_title, info.episode_id)
    packaging_items = _build_bootstrap_packaging_items(context, info.episode_id)
    motion_item = _build_bootstrap_motion_item(context, scene_item, scene_archetype_id, info.episode_id)
    audio_pipeline = f"ep{info.number}_{compact_slug(info.episode_id)}_production"
    pipeline_dir = context.audio_repo.pipeline_dir(audio_pipeline)
    web_notes = (
        f"Launch entry exists in site-facts.ts ({'homepage visible' if web_entry.homepage_visible else 'homepage hidden'})."
        if web_entry
        else "Web entry has not been prepared yet."
    )
    manifest = {
        "id": info.episode_id,
        "title": resolved_title,
        "pillar": resolved_pillar,
        "priority": info.number,
        "label": resolved_label,
        "summary": resolved_summary,
        "release_window": f"launch-episode-{info.number:02d}",
        "aliases": {
            "episode_folder": info.folder_name,
            "audio_pipeline": audio_pipeline,
            "scene_preset": scene_item["preset"],
            "thumbnail_preset": defaults["thumbnail_preset"],
            "shorts_preset": defaults["shorts_preset"],
            "web_entry_id": web_entry.id if web_entry else info.episode_id,
        },
        "tracking": {
            "bootstrapped_at": utc_now_iso(),
        },
        "script": {
            "path": str(info.script_path),
            "status": "locked",
        },
        "visual_research": {
            "status": _derive_visual_research_status(info),
            **{key: str(value) for key, value in info.visual_research_paths.items()},
        },
        "audio": {
            "status": "todo",
            "pipeline_dir": str(pipeline_dir),
            "master_path": str(info.canonical_final_audio_path),
            "transcript_path": "",
            "review": {
                "status": "pending",
                "reviewer": "",
                "reviewed_at": "",
                "notes": "",
            },
        },
        "scene_stills": {
            "status": scene_lane_status,
            "items": [scene_item],
        },
        "packaging_stills": {
            "status": "todo",
            "items": packaging_items,
        },
        "motion_assets": {
            "status": "todo",
            "items": [motion_item],
        },
        "assembly": {
            "status": "todo",
            "owner": "agent",
            "renderer": "ffmpeg",
            "strategy": "act_spine",
            "notes": "Blocked until final audio and approved visual package exist.",
            "master_video_path": "",
            "completed_at": "",
            "transitions": [],
        },
        "web": {
            "status": "todo",
            "entry_id": web_entry.id if web_entry else info.episode_id,
            "notes": web_notes,
        },
        "release": {
            "status": "todo",
            "scheduled_for": "",
            "published_at": "",
            "notes": "Publish timing has not been set.",
            "notes_path": str(info.directory / "publish_notes.md"),
            "youtube": {
                "status": "todo",
                "title": resolved_title,
                "description_path": str(info.directory / "publish_notes.md"),
                "tags": [],
                "privacy": "public",
                "thumbnail_item_id": "primary_thumbnail",
                "video_id": "",
                "video_url": "",
                "scheduled_for": "",
                "published_at": "",
                "error": "",
            },
            "podcast": {
                "status": "todo",
                "title": resolved_title,
                "description_path": str(info.directory / "publish_notes.md"),
                "audio_path": str(info.canonical_final_audio_path),
                "external_id": "",
                "episode_url": "",
                "scheduled_for": "",
                "published_at": "",
                "error": "",
            },
        },
        "analytics": {
            "status": "todo",
            "notes": "Open after publish date exists.",
        },
    }
    return materialize_episode_manifest(context, manifest)


def toml_literal(value: Any) -> str:
    if isinstance(value, dict):
        items: list[str] = []
        for key, item_value in value.items():
            key_text = str(key)
            key_literal = key_text if re.match(r"^[A-Za-z0-9_-]+$", key_text) else toml_literal(key_text)
            items.append(f"{key_literal} = {toml_literal(item_value)}")
        return "{ " + ", ".join(items) + " }"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(toml_literal(item) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    if "\n" in text:
        if "'''" not in text:
            return "'''" + text + "'''"
        escaped_multiline = text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        return '"""' + escaped_multiline + '"""'
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def ordered_keys(mapping: dict[str, Any], preferred: tuple[str, ...]) -> list[str]:
    keys = [key for key in preferred if key in mapping]
    keys.extend(key for key in mapping.keys() if key not in keys)
    return keys


def render_episode_manifest(manifest: dict[str, Any]) -> str:
    lines: list[str] = []

    def add_kv(key: str, value: Any) -> None:
        lines.append(f"{key} = {toml_literal(value)}")

    for key in ("id", "title", "pillar", "priority", "label", "summary", "release_window"):
        add_kv(key, manifest[key])
    lines.append("")
    lines.append("[aliases]")
    for key in ordered_keys(
        manifest["aliases"],
        ("episode_folder", "audio_pipeline", "scene_preset", "thumbnail_preset", "shorts_preset", "web_entry_id"),
    ):
        add_kv(key, manifest["aliases"][key])
    lines.append("")
    lines.append("[tracking]")
    tracking = manifest.get("tracking", {})
    tracking_scalars = {
        key: value
        for key, value in tracking.items()
        if not str(key).startswith("_")
    }
    for key in ordered_keys(tracking_scalars, ("bootstrapped_at",)):
        add_kv(key, tracking_scalars[key])
    lines.append("")
    lines.append("[script]")
    for key in ordered_keys(manifest["script"], ("path", "status")):
        add_kv(key, manifest["script"][key])
    lines.append("")
    lines.append("[visual_research]")
    visual_research = manifest["visual_research"]
    visual_research_scalars = {
        key: value
        for key, value in visual_research.items()
        if key not in {"approval", "opening_sequence", "acts", "guardrails"} and not str(key).startswith("_")
    }
    for key in ordered_keys(
        visual_research_scalars,
        (
            "status",
            "script_source_path",
            "script_sha256",
            "estimated_runtime_seconds",
            "act_count",
            "beat_count_total",
            "required_motion_total",
            "planned_motion_total",
            "contact_sheet_path",
            "source_inventory_path",
            "source_origin_policy",
            "act_breakdown_path",
            "reference_notes_path",
            "sources_path",
            "assembly_notes_path",
        ),
    ):
        add_kv(key, visual_research_scalars[key])
    approval = visual_research.get("approval", {})
    lines.append("")
    lines.append("[visual_research.approval]")
    for key in ordered_keys(approval, ("status", "reviewer", "reviewed_at", "notes", "tags")):
        add_kv(key, approval[key])
    guardrails = visual_research.get("guardrails", {})
    lines.append("")
    lines.append("[visual_research.guardrails]")
    for key in ordered_keys(
        guardrails,
        (
            "signal_object",
            "banned_motifs",
            "latest_reject_tags",
            "opening_candidate_min",
            "opening_candidate_target",
            "subject_candidate_min",
            "act_candidate_min",
            "source_total",
            "approved_source_total",
            "clear_source_total",
            "cleaned_source_total",
            "ready_source_total",
            "opening_candidate_total",
            "opening_subject_candidate_total",
            "opening_supporting_candidate_total",
            "opening_subject_slot_id",
            "opening_slot_candidate_totals",
            "missing_opening_slot_ids",
            "act_candidate_totals",
            "underfilled_coverage_ids",
            "ready_for_generation",
            "unresolved_source_ids",
            "blocked_source_ids",
            "missing_downstream_source_ids",
            "opening_slot_source_ids_missing_assignment",
            "opening_slot_source_ids_invalid_assignment",
            "opening_slot_role_mismatch_source_ids",
        ),
    ):
        add_kv(key, guardrails[key])
    opening_sequence = visual_research.get("opening_sequence", {})
    lines.append("")
    lines.append("[visual_research.opening_sequence]")
    opening_sequence_scalars = {
        key: value
        for key, value in opening_sequence.items()
        if key != "slots"
    }
    for key in ordered_keys(
        opening_sequence_scalars,
        (
            "object_strategy",
            "time_period_label",
            "supporting_objects",
            "subject_object",
            "focus_transition",
            "subject_action",
            "act_id",
            "planned_scene_id",
            "planned_motion_id",
            "audio_end_cue_text",
            "min_duration_seconds",
            "block_downstream_until_approved",
        ),
    ):
        add_kv(key, opening_sequence_scalars[key])
    for slot in opening_sequence.get("slots", []):
        lines.append("")
        lines.append("[[visual_research.opening_sequence.slots]]")
        for key in ordered_keys(slot, ("slot_id", "display_label", "role", "object_scope", "renderability", "visual_descriptor")):
            add_kv(key, slot[key])
    for act in visual_research.get("acts", []):
        lines.append("")
        lines.append("[[visual_research.acts]]")
        for key in ordered_keys(
            act,
            (
                "id",
                "title",
                "estimated_seconds",
                "beat_count",
                "visual_thesis",
                "dominant_signal",
                "reference_board_path",
                "required_motion_sequences",
                "planned_scene_ids",
                "planned_motion_ids",
                "exception_reason",
            ),
        ):
            add_kv(key, act[key])
    lines.append("")
    lines.append("[audio]")
    audio = manifest["audio"]
    audio_scalars = {
        key: value
        for key, value in audio.items()
        if key != "review"
    }
    for key in ordered_keys(audio_scalars, ("status", "pipeline_dir", "master_path", "transcript_path")):
        add_kv(key, audio_scalars[key])
    lines.append("")
    lines.append("[audio.review]")
    for key in ordered_keys(audio.get("review", {}), ("status", "reviewer", "reviewed_at", "notes", "freshness_override")):
        add_kv(key, audio["review"][key])
    lines.append("")
    lines.append("[scene_stills]")
    add_kv("status", manifest["scene_stills"]["status"])
    for item in manifest["scene_stills"]["items"]:
        lines.append("")
        lines.append("[[scene_stills.items]]")
        for key in ordered_keys(
            item,
            (
                "id",
                "act",
                "purpose",
                "preset",
                "reference_dir",
                "output_path",
                "latest_render_path",
                "latest_render_manifest_path",
                "approved_proof_path",
                "approved_proof_manifest_path",
                "selected_asset",
                "required",
                "review_status",
                "motion_review_status",
                "reviewer",
                "reviewed_at",
                "review_notes",
                "review_tags",
                "motion_reviewer",
                "motion_reviewed_at",
                "motion_review_notes",
                "motion_review_tags",
                "archetype_status",
                "archetype_id",
                "notes",
            ),
        ):
            add_kv(key, item.get(key, ""))
    lines.append("")
    lines.append("[packaging_stills]")
    add_kv("status", manifest["packaging_stills"]["status"])
    for item in manifest["packaging_stills"]["items"]:
        lines.append("")
        lines.append("[[packaging_stills.items]]")
        for key in ordered_keys(
            item,
            (
                "id",
                "kind",
                "purpose",
                "preset",
                "reference_dir",
                "output_path",
                "latest_render_path",
                "latest_render_manifest_path",
                "approved_proof_path",
                "approved_proof_manifest_path",
                "selected_asset",
                "required",
                "review_status",
                "reviewer",
                "reviewed_at",
                "review_notes",
                "review_tags",
            ),
        ):
            add_kv(key, item.get(key, ""))
    lines.append("")
    lines.append("[motion_assets]")
    add_kv("status", manifest["motion_assets"]["status"])
    for item in manifest["motion_assets"]["items"]:
        lines.append("")
        lines.append("[[motion_assets.items]]")
        for key in ordered_keys(
            item,
            (
                "id",
                "source_still_id",
                "archetype_id",
                "prompt",
                "behavior",
                "frames",
                "width",
                "height",
                "pipeline",
                "authoring_mode",
                "workbench_project_path",
                "output_path",
                "latest_render_path",
                "latest_render_manifest_path",
                "status",
                "review_outcome",
                "reviewer",
                "reviewed_at",
                "review_notes",
                "review_tags",
                "min_duration_seconds",
                "notes",
            ),
        ):
            add_kv(key, item.get(key, ""))
    lines.append("")
    lines.append("[assembly]")
    assembly = manifest["assembly"]
    assembly_scalars = {key: value for key, value in assembly.items() if key not in {"transitions", "compositions"}}
    for key in ordered_keys(
        assembly_scalars,
        ("status", "owner", "renderer", "strategy", "notes", "master_video_path", "completed_at"),
    ):
        add_kv(key, assembly_scalars[key])
    for transition in assembly.get("transitions", []):
        lines.append("")
        lines.append("[[assembly.transitions]]")
        for key in ordered_keys(
            transition,
            ("from_act", "to_act", "video", "audio", "duration_seconds"),
        ):
            add_kv(key, transition.get(key, ""))
    for composition in assembly.get("compositions", []):
        lines.append("")
        lines.append("[[assembly.compositions]]")
        for key in ordered_keys(composition, ("act_id", "base_asset_id")):
            if key == "overlays":
                continue
            add_kv(key, composition.get(key, ""))
        for overlay in composition.get("overlays", []):
            lines.append("")
            lines.append("[[assembly.compositions.overlays]]")
            for key in ordered_keys(
                overlay,
                ("motion_asset_id", "start_seconds", "duration_seconds", "x", "y", "scale", "opacity", "blend_mode", "hold_last_frame"),
            ):
                if overlay.get(key) is None:
                    continue
                add_kv(key, overlay.get(key, ""))
    lines.append("")
    lines.append("[web]")
    for key in ordered_keys(manifest["web"], tuple(manifest["web"].keys())):
        add_kv(key, manifest["web"][key])
    lines.append("")
    lines.append("[release]")
    release = manifest["release"]
    release_scalars = {
        key: value
        for key, value in release.items()
        if key not in {"youtube", "podcast"}
    }
    for key in ordered_keys(release_scalars, ("status", "scheduled_for", "published_at", "notes", "notes_path")):
        add_kv(key, release_scalars[key])
    lines.append("")
    lines.append("[release.youtube]")
    for key in ordered_keys(
        release.get("youtube", {}),
        ("status", "title", "description_path", "tags", "privacy", "thumbnail_item_id", "video_id", "video_url", "scheduled_for", "published_at", "error"),
    ):
        add_kv(key, release["youtube"][key])
    lines.append("")
    lines.append("[release.podcast]")
    for key in ordered_keys(
        release.get("podcast", {}),
        ("status", "title", "description_path", "audio_path", "external_id", "episode_url", "scheduled_for", "published_at", "error"),
    ):
        add_kv(key, release["podcast"][key])
    lines.append("")
    lines.append("[analytics]")
    for key in ordered_keys(manifest["analytics"], tuple(manifest["analytics"].keys())):
        add_kv(key, manifest["analytics"][key])
    lines.append("")
    return "\n".join(lines)


def write_bootstrap_manifest(context: Context, manifest: dict[str, Any]) -> Path:
    path = context.root / "episodes" / f"{manifest['id']}.toml"
    path.write_text(render_episode_manifest(manifest), encoding="utf-8")
    return path


def write_episode_manifest(path: Path, manifest: dict[str, Any]) -> None:
    payload = copy.deepcopy(manifest)
    payload.pop("_manifest_path", None)
    path.write_text(render_episode_manifest(payload), encoding="utf-8")


def write_state_file(context: Context, manifest: dict[str, Any], state: dict[str, Any]) -> Path:
    state_dir = context.root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{manifest['id']}.json"
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state_path


def resolve_target_manifests(context: Context, episode_id: str | None, select_all: bool) -> list[dict[str, Any]]:
    manifests = list_episode_manifests(context)
    if select_all:
        return manifests
    if not episode_id:
        raise SystemExit("Episode id or --all is required.")
    for manifest in manifests:
        if manifest.get("id") == episode_id:
            return [manifest]
    raise SystemExit(f"Unknown episode id: {episode_id}")
