from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from orchestration.io import Context


SOURCE_TEXT_STATUSES = frozenset({"clear", "needs_cleanup", "cleaned", "blocked"})
SOURCE_CANDIDATE_ROLES = frozenset({"opening_subject", "opening_supporting", "act_reference"})
SOURCE_ORIGIN_POLICIES = frozenset({"any", "fresh_web_only"})
SOURCE_INVENTORY_SCHEMA_VERSION = 2


def _string(value: Any) -> str:
    return str(value or "").strip()


def _path_string(value: Any) -> str:
    return _string(value)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = _string(value).lower()
    return text in {"1", "true", "yes", "on"}


def _path_exists(raw: Any) -> bool:
    candidate = _path_string(raw)
    return bool(candidate and Path(candidate).expanduser().exists())


def _normalized_path_token(raw: Any) -> str:
    candidate = _path_string(raw)
    if not candidate:
        return ""
    try:
        return str(Path(candidate).expanduser().resolve(strict=False))
    except OSError:
        return str(Path(candidate).expanduser())


def default_source_inventory_path(visual_research: dict[str, Any]) -> str:
    explicit = _path_string(visual_research.get("source_inventory_path"))
    if explicit:
        return explicit
    act_breakdown_path = _path_string(visual_research.get("act_breakdown_path"))
    if not act_breakdown_path:
        return ""
    return str(Path(act_breakdown_path).expanduser().parent / "source_inventory.json")


def _normalize_text_status(raw_status: Any, *, approved_for_generation: bool) -> str:
    status = _string(raw_status)
    if status in SOURCE_TEXT_STATUSES:
        return status
    return "needs_cleanup" if approved_for_generation else "clear"


def _normalize_coverage_id(raw_coverage_id: Any, *, act_id: str, raw_candidate_role: Any) -> str:
    coverage_id = _string(raw_coverage_id)
    if coverage_id:
        return coverage_id
    role = _string(raw_candidate_role)
    if role in {"opening_subject", "opening_supporting"}:
        return "opening"
    return act_id


def _normalize_candidate_role(raw_candidate_role: Any, *, coverage_id: str) -> str:
    role = _string(raw_candidate_role)
    if coverage_id == "opening":
        return role if role in {"opening_subject", "opening_supporting"} else "opening_supporting"
    return role if role == "act_reference" else "act_reference"


def _normalize_source_entry(raw: Any, *, index: int) -> dict[str, Any]:
    entry = raw if isinstance(raw, dict) else {}
    source_id = _string(entry.get("source_id")) or f"source_{index:03d}"
    approved_for_generation = _bool(entry.get("approved_for_generation"))
    text_status = _normalize_text_status(entry.get("text_status"), approved_for_generation=approved_for_generation)
    act_id = _string(entry.get("act_id"))
    coverage_id = _normalize_coverage_id(entry.get("coverage_id"), act_id=act_id, raw_candidate_role=entry.get("candidate_role"))
    candidate_role = _normalize_candidate_role(entry.get("candidate_role"), coverage_id=coverage_id)
    normalized = {
        "source_id": source_id,
        "act_id": act_id,
        "coverage_id": coverage_id,
        "opening_slot_id": _string(entry.get("opening_slot_id")) if coverage_id == "opening" else "",
        "candidate_label": _string(entry.get("candidate_label")) or source_id,
        "candidate_role": candidate_role,
        "source_url": _string(entry.get("source_url")),
        "source_origin": _string(entry.get("source_origin")),
        "raw_asset_path": _path_string(entry.get("raw_asset_path")),
        "board_asset_path": _path_string(entry.get("board_asset_path")),
        "approved_for_generation": approved_for_generation,
        "text_status": text_status,
        "text_detection_manifest_path": _path_string(entry.get("text_detection_manifest_path")),
        "cleanup_manifest_path": _path_string(entry.get("cleanup_manifest_path")),
        "cleaned_asset_path": _path_string(entry.get("cleaned_asset_path")),
        "downstream_asset_path": _path_string(entry.get("downstream_asset_path")),
        "notes": _string(entry.get("notes")),
    }
    if normalized["text_status"] == "cleaned" and not normalized["cleaned_asset_path"]:
        normalized["text_status"] = "needs_cleanup"
    if normalized["text_status"] == "cleaned" and not normalized["downstream_asset_path"] and normalized["cleaned_asset_path"]:
        normalized["downstream_asset_path"] = normalized["cleaned_asset_path"]
    if normalized["text_status"] == "clear" and not normalized["downstream_asset_path"]:
        normalized["downstream_asset_path"] = normalized["raw_asset_path"]
    return normalized


def display_asset_path(entry: dict[str, Any]) -> str:
    board_asset_path = _path_string(entry.get("board_asset_path"))
    if board_asset_path:
        return board_asset_path
    return _path_string(entry.get("raw_asset_path"))


def note_allows_duplicate_display(entry: dict[str, Any]) -> bool:
    notes = _string(entry.get("notes")).lower()
    return "allow_duplicate_display" in notes


def summarize_source_inventory(sources: list[dict[str, Any]]) -> dict[str, Any]:
    approved_sources = [entry for entry in sources if entry["approved_for_generation"]]
    clear_source_ids: list[str] = []
    cleaned_source_ids: list[str] = []
    unresolved_source_ids: list[str] = []
    blocked_source_ids: list[str] = []
    missing_downstream_source_ids: list[str] = []
    missing_display_source_ids: list[str] = []
    duplicate_display_source_ids: list[str] = []
    act_candidate_totals: dict[str, int] = {}
    opening_candidate_total = 0
    opening_subject_candidate_total = 0
    opening_supporting_candidate_total = 0
    opening_slot_candidate_totals: dict[str, int] = {}
    display_asset_to_source_ids: dict[str, list[str]] = {}

    for entry in sources:
        coverage_id = _string(entry.get("coverage_id"))
        candidate_role = _string(entry.get("candidate_role"))
        if coverage_id == "opening":
            opening_candidate_total += 1
            opening_slot_id = _string(entry.get("opening_slot_id"))
            if opening_slot_id:
                opening_slot_candidate_totals[opening_slot_id] = int(opening_slot_candidate_totals.get(opening_slot_id, 0)) + 1
            if candidate_role == "opening_subject":
                opening_subject_candidate_total += 1
            elif candidate_role == "opening_supporting":
                opening_supporting_candidate_total += 1
            continue
        if coverage_id:
            act_candidate_totals[coverage_id] = int(act_candidate_totals.get(coverage_id, 0)) + 1
        display_path = display_asset_path(entry)
        if not display_path or not _path_exists(display_path):
            missing_display_source_ids.append(entry["source_id"])
        else:
            key = _normalized_path_token(display_path)
            display_asset_to_source_ids.setdefault(key, []).append(entry["source_id"])

    for entry in approved_sources:
        source_id = entry["source_id"]
        text_status = _string(entry.get("text_status"))
        downstream_asset_path = _path_string(entry.get("downstream_asset_path"))
        if text_status == "clear":
            clear_source_ids.append(source_id)
        elif text_status == "cleaned":
            cleaned_source_ids.append(source_id)
        if text_status == "blocked":
            blocked_source_ids.append(source_id)
        if text_status in {"clear", "cleaned"} and not downstream_asset_path:
            missing_downstream_source_ids.append(source_id)
        if text_status not in {"clear", "cleaned"} or not downstream_asset_path:
            unresolved_source_ids.append(source_id)

    ready_source_ids = [source_id for source_id in clear_source_ids + cleaned_source_ids if source_id not in missing_downstream_source_ids]
    for source_ids in display_asset_to_source_ids.values():
        if len(source_ids) < 2:
            continue
        duplicate_display_source_ids.extend(source_ids)
    return {
        "source_total": len(sources),
        "approved_source_total": len(approved_sources),
        "clear_source_total": len(clear_source_ids),
        "cleaned_source_total": len(cleaned_source_ids),
        "ready_source_total": len(ready_source_ids),
        "ready_source_ids": ready_source_ids,
        "unresolved_source_ids": unresolved_source_ids,
        "blocked_source_ids": blocked_source_ids,
        "missing_downstream_source_ids": missing_downstream_source_ids,
        "missing_display_source_ids": missing_display_source_ids,
        "duplicate_display_source_ids": duplicate_display_source_ids,
        "opening_candidate_total": opening_candidate_total,
        "opening_subject_candidate_total": opening_subject_candidate_total,
        "opening_supporting_candidate_total": opening_supporting_candidate_total,
        "opening_slot_candidate_totals": opening_slot_candidate_totals,
        "act_candidate_totals": act_candidate_totals,
        "ready_for_generation": not unresolved_source_ids,
    }


def normalize_source_inventory(raw: Any, *, inventory_path: Path | None) -> dict[str, Any]:
    payload = raw if isinstance(raw, dict) else {}
    raw_sources = payload.get("sources", [])
    errors: list[str] = []
    if raw_sources is None:
        raw_sources = []
    if not isinstance(raw_sources, list):
        errors.append("Source inventory `sources` must be a list.")
        raw_sources = []

    seen_source_ids: set[str] = set()
    sources: list[dict[str, Any]] = []
    for index, raw_entry in enumerate(raw_sources, start=1):
        entry = _normalize_source_entry(raw_entry, index=index)
        if entry["source_id"] in seen_source_ids:
            errors.append(f"Duplicate source_id `{entry['source_id']}` in source inventory.")
            continue
        seen_source_ids.add(entry["source_id"])
        sources.append(entry)

    return {
        "schema_version": int(payload.get("schema_version", SOURCE_INVENTORY_SCHEMA_VERSION) or SOURCE_INVENTORY_SCHEMA_VERSION),
        "inventory_path": str(inventory_path) if inventory_path is not None else "",
        "sources": sources,
        "errors": errors,
        "summary": summarize_source_inventory(sources),
    }


def load_source_inventory(path: Path) -> dict[str, Any]:
    resolved = Path(path).expanduser()
    if not resolved.exists():
        inventory = normalize_source_inventory({"schema_version": SOURCE_INVENTORY_SCHEMA_VERSION, "sources": []}, inventory_path=resolved)
        inventory["errors"] = [f"Source inventory is missing: {resolved}"]
        return inventory
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        inventory = normalize_source_inventory({"schema_version": SOURCE_INVENTORY_SCHEMA_VERSION, "sources": []}, inventory_path=resolved)
        inventory["errors"] = [f"Source inventory is not valid JSON: {resolved}: {exc}"]
        return inventory
    return normalize_source_inventory(raw, inventory_path=resolved)


def write_source_inventory(path: Path, inventory: dict[str, Any]) -> None:
    resolved = Path(path).expanduser()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": int(inventory.get("schema_version", SOURCE_INVENTORY_SCHEMA_VERSION) or SOURCE_INVENTORY_SCHEMA_VERSION),
        "sources": [
            {
                "source_id": _string(entry.get("source_id")),
                "act_id": _string(entry.get("act_id")),
                "coverage_id": _string(entry.get("coverage_id")),
                "opening_slot_id": _string(entry.get("opening_slot_id"))
                if _normalize_coverage_id(entry.get("coverage_id"), act_id=_string(entry.get("act_id")), raw_candidate_role=entry.get("candidate_role")) == "opening"
                else "",
                "candidate_label": _string(entry.get("candidate_label")),
                "candidate_role": _normalize_candidate_role(
                    entry.get("candidate_role"),
                    coverage_id=_normalize_coverage_id(entry.get("coverage_id"), act_id=_string(entry.get("act_id")), raw_candidate_role=entry.get("candidate_role")),
                ),
                "source_url": _string(entry.get("source_url")),
                "source_origin": _string(entry.get("source_origin")),
                "raw_asset_path": _path_string(entry.get("raw_asset_path")),
                "board_asset_path": _path_string(entry.get("board_asset_path")),
                "approved_for_generation": _bool(entry.get("approved_for_generation")),
                "text_status": _normalize_text_status(entry.get("text_status"), approved_for_generation=_bool(entry.get("approved_for_generation"))),
                "text_detection_manifest_path": _path_string(entry.get("text_detection_manifest_path")),
                "cleanup_manifest_path": _path_string(entry.get("cleanup_manifest_path")),
                "cleaned_asset_path": _path_string(entry.get("cleaned_asset_path")),
                "downstream_asset_path": _path_string(entry.get("downstream_asset_path")),
                "notes": _string(entry.get("notes")),
            }
            for entry in inventory.get("sources", [])
        ],
    }
    resolved.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def shared_research_processed_dir(inventory_path: Path) -> Path:
    return Path(inventory_path).expanduser().parent / "processed"


def _run_viz_json_command(args: list[str], *, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(args, capture_output=True, text=True, cwd=str(cwd))
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        combined = "\n".join(part for part in (stdout, stderr) if part).strip()
        raise SystemExit(combined or f"Command failed with exit code {completed.returncode}: {' '.join(args)}")
    if not stdout:
        raise SystemExit(f"Command returned no JSON output: {' '.join(args)}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Command returned invalid JSON: {' '.join(args)}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"Command returned non-object JSON: {' '.join(args)}")
    return payload


def process_source_artifact_with_viz(
    context: Context,
    *,
    artifact_path: Path,
    output_path: Path,
    debug_dir: Path,
    policy_path: Path | None,
) -> dict[str, Any]:
    viz_ce = Path(context.channel["paths"]["viz_ce_path"]).expanduser()
    args = [
        str(viz_ce),
        "typography",
        "process-research-source",
        "--artifact",
        str(artifact_path),
        "--output",
        str(output_path),
        "--debug-dir",
        str(debug_dir),
    ]
    if policy_path is not None:
        args.extend(["--policy", str(policy_path)])
    return _run_viz_json_command(args, cwd=Path(context.channel["paths"]["viz_root"]).expanduser())


def _research_source_input_path(entry: dict[str, Any]) -> Path | None:
    raw_asset_path = _path_string(entry.get("raw_asset_path"))
    if raw_asset_path:
        return Path(raw_asset_path).expanduser()
    board_asset_path = _path_string(entry.get("board_asset_path"))
    if board_asset_path:
        return Path(board_asset_path).expanduser()
    return None


def process_research_source_inventory(context: Context, manifest: dict[str, Any]) -> dict[str, Any]:
    visual_research = manifest.get("visual_research", {})
    inventory_path_raw = _path_string(visual_research.get("source_inventory_path"))
    if not inventory_path_raw:
        raise SystemExit("Visual research is missing source_inventory_path.")
    inventory_path = Path(inventory_path_raw).expanduser()
    inventory = load_source_inventory(inventory_path)
    if inventory.get("errors") and any("not valid JSON" in error for error in inventory["errors"]):
        raise SystemExit(inventory["errors"][0])

    policy_path = context.viz_repo.shared_research_source_repair_policy_path()
    processed_dir = shared_research_processed_dir(inventory_path)
    updated_sources: list[dict[str, Any]] = []
    source_errors: list[str] = []

    for entry in inventory.get("sources", []):
        updated = dict(entry)
        if not _bool(entry.get("approved_for_generation")):
            updated_sources.append(updated)
            continue

        input_path = _research_source_input_path(entry)
        if input_path is None or not input_path.exists():
            updated["text_status"] = "blocked"
            updated["text_detection_manifest_path"] = ""
            updated["cleanup_manifest_path"] = ""
            updated["cleaned_asset_path"] = ""
            updated["downstream_asset_path"] = ""
            source_errors.append(f"{updated['source_id']}: approved source asset is missing.")
            updated_sources.append(updated)
            continue

        source_dir = processed_dir / updated["source_id"]
        output_path = source_dir / f"{input_path.stem}__cleaned{input_path.suffix}"
        debug_dir = source_dir / "debug"
        summary = process_source_artifact_with_viz(
            context,
            artifact_path=input_path,
            output_path=output_path,
            debug_dir=debug_dir,
            policy_path=policy_path,
        )
        status = _string(summary.get("status")) or "blocked"
        updated["text_status"] = status if status in SOURCE_TEXT_STATUSES else "blocked"
        updated["text_detection_manifest_path"] = _path_string(summary.get("text_detection_manifest_path"))
        updated["cleanup_manifest_path"] = _path_string(summary.get("cleanup_manifest_path"))
        updated["cleaned_asset_path"] = (
            _path_string(summary.get("output_artifact"))
            if _string(summary.get("status")) in {"cleaned", "blocked"}
            else ""
        )
        if status == "clear":
            updated["downstream_asset_path"] = str(input_path)
            updated["cleaned_asset_path"] = ""
        elif status == "cleaned":
            updated["downstream_asset_path"] = _path_string(summary.get("output_artifact"))
        else:
            updated["downstream_asset_path"] = ""
            reason = _string(summary.get("blocked_reason"))
            if reason:
                source_errors.append(f"{updated['source_id']}: {reason}")
        updated_sources.append(updated)

    updated_inventory = normalize_source_inventory(
        {
            "schema_version": inventory.get("schema_version", SOURCE_INVENTORY_SCHEMA_VERSION),
            "sources": updated_sources,
        },
        inventory_path=inventory_path,
    )
    if source_errors:
        updated_inventory["errors"] = list(updated_inventory.get("errors", [])) + source_errors
    write_source_inventory(inventory_path, updated_inventory)
    return updated_inventory


def preflight_motion_source_asset(
    context: Context,
    *,
    motion_item_id: str,
    source_still_id: str,
    preset: str,
    selected_asset_path: Path,
) -> tuple[Path, dict[str, Any]]:
    policy_path = context.viz_repo.repair_policy_path("scene_still", preset)
    temp_root = Path(tempfile.mkdtemp(prefix=f"ce-motion-source-{motion_item_id}-"))
    output_path = temp_root / selected_asset_path.name
    debug_dir = temp_root / "debug"
    summary = process_source_artifact_with_viz(
        context,
        artifact_path=selected_asset_path,
        output_path=output_path,
        debug_dir=debug_dir,
        policy_path=policy_path,
    )
    status = _string(summary.get("status"))
    if status == "clear":
        return selected_asset_path, summary
    if status == "cleaned":
        cleaned_path = Path(_path_string(summary.get("output_artifact"))).expanduser()
        if not cleaned_path.exists():
            raise SystemExit(f"Motion source preflight did not produce the cleaned asset for `{source_still_id}`.")
        return cleaned_path, summary
    reason = _string(summary.get("blocked_reason")) or "Residual readable text remains after cleanup."
    raise SystemExit(
        f"Motion source `{source_still_id}` cannot render `{motion_item_id}` because text_artifacts remain after preflight cleanup. {reason}"
    )


__all__ = [
    "SOURCE_ORIGIN_POLICIES",
    "SOURCE_INVENTORY_SCHEMA_VERSION",
    "SOURCE_TEXT_STATUSES",
    "default_source_inventory_path",
    "display_asset_path",
    "load_source_inventory",
    "note_allows_duplicate_display",
    "normalize_source_inventory",
    "preflight_motion_source_asset",
    "process_research_source_inventory",
    "process_source_artifact_with_viz",
    "shared_research_processed_dir",
    "summarize_source_inventory",
    "write_source_inventory",
]
