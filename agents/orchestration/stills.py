from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from orchestration.domain import (
    PACKAGING_KIND_TO_FAMILY,
    derive_packaging_lane_status,
    derive_scene_lane_status,
    motion_items,
    normalize_kind,
    packaging_items,
    scene_items,
    utc_now_iso,
)
from orchestration.io import (
    Context,
    build_episode_reference_dir,
    build_packaging_output_path,
    build_scene_output_path,
    find_scene_archetype,
    write_episode_manifest,
)
from orchestration.motion import derive_motion_lane_status, parse_info_value, remove_file_like_path, run_checked_command
from orchestration.research_sources import display_asset_path, load_source_inventory


RETIRED_SCENE_STILL_WORKFLOW_MESSAGE = (
    "The Viz scene_still workflow family is retired. Use short-specific still lanes or promote an existing "
    "reference-local scene asset instead of rendering/finalizing via scene_still."
)


def resolve_scene_item(manifest: dict[str, Any], scene_item_id: str) -> dict[str, Any]:
    for item in scene_items(manifest):
        if str(item.get("id", "")) == scene_item_id:
            return item
    raise SystemExit(f"Unknown scene item id: {scene_item_id}")


def resolve_packaging_item(manifest: dict[str, Any], item_id: str) -> dict[str, Any]:
    for item in packaging_items(manifest):
        if str(item.get("id", "")) == item_id:
            return item
    raise SystemExit(f"Unknown packaging item id: {item_id}")


def _resolve_manifest_path(manifest: dict[str, Any]) -> Path:
    return Path(str(manifest["_manifest_path"]))


def _load_pipeline_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_visual_qc_passed(manifest: dict[str, Any], *, manifest_path: Path) -> None:
    stage_validations = manifest.get("stage_validations")
    if not isinstance(stage_validations, dict):
        raise SystemExit(f"Pipeline manifest is missing stage_validations: {manifest_path}")
    visual_qc = stage_validations.get("visual_qc")
    if not isinstance(visual_qc, dict):
        raise SystemExit(f"Pipeline manifest is missing visual_qc validation: {manifest_path}")
    if str(visual_qc.get("status", "")).strip() != "ok":
        raise SystemExit(
            f"Pipeline manifest visual_qc did not pass for promotion/review: {manifest_path}"
        )
    audit_manifest = str(visual_qc.get("audit_manifest", "")).strip()
    if not audit_manifest:
        raise SystemExit(f"Pipeline manifest visual_qc is missing audit_manifest: {manifest_path}")
    if not Path(audit_manifest).expanduser().exists():
        raise SystemExit(f"Pipeline manifest visual_qc audit manifest is missing: {audit_manifest}")


def _resolve_output_manifest_path(asset_path: Path, latest_render_path: str, latest_render_manifest_path: str) -> Path:
    if latest_render_path and latest_render_manifest_path:
        try:
            if asset_path.resolve() == Path(latest_render_path).expanduser().resolve():
                manifest_path = Path(latest_render_manifest_path).expanduser()
                if not manifest_path.exists():
                    raise SystemExit(f"Latest render manifest is missing: {manifest_path}")
                return manifest_path
        except FileNotFoundError:
            pass
    sibling_manifest_path = Path(f"{asset_path}.json")
    if not sibling_manifest_path.exists():
        raise SystemExit(f"Render manifest is missing for approved asset: {sibling_manifest_path}")
    return sibling_manifest_path


def _review_snapshot_asset_path(item: dict[str, Any]) -> Path:
    reference_dir_raw = str(item.get("reference_dir", "")).strip()
    if not reference_dir_raw:
        raise SystemExit(f"Still `{item.get('id', '')}` is missing reference_dir.")
    reference_dir = Path(reference_dir_raw).expanduser()
    if not reference_dir.is_absolute():
        raise SystemExit(f"Still `{item.get('id', '')}` reference_dir must be absolute: {reference_dir}")
    return reference_dir / "selects" / "review_approved.png"


def _copy_asset_and_manifest(asset_path: Path, manifest_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_manifest_path = Path(f"{output_path}.json")
    if asset_path.resolve() != output_path.resolve():
        remove_file_like_path(output_path)
        shutil.copy2(asset_path, output_path)
    if manifest_path.resolve() != canonical_manifest_path.resolve():
        remove_file_like_path(canonical_manifest_path)
        shutil.copy2(manifest_path, canonical_manifest_path)
    return canonical_manifest_path


def _stamp_approved_proof(item: dict[str, Any], asset_path: Path, manifest_path: Path) -> tuple[Path, Path]:
    approved_proof_path = _review_snapshot_asset_path(item)
    approved_proof_manifest_path = _copy_asset_and_manifest(asset_path, manifest_path, approved_proof_path)
    item["approved_proof_path"] = str(approved_proof_path)
    item["approved_proof_manifest_path"] = str(approved_proof_manifest_path)
    return approved_proof_path, approved_proof_manifest_path


def _clear_review_fields(item: dict[str, Any]) -> None:
    item["reviewer"] = ""
    item["reviewed_at"] = ""
    item["review_notes"] = ""
    item["review_tags"] = []


def _clear_motion_review_fields(item: dict[str, Any]) -> None:
    item["motion_reviewer"] = ""
    item["motion_reviewed_at"] = ""
    item["motion_review_notes"] = ""
    item["motion_review_tags"] = []


def _reset_motion_review_status(item: dict[str, Any]) -> None:
    current = str(item.get("motion_review_status", "pending")).strip() or "pending"
    if current not in {"blocked", "not_planned"}:
        item["motion_review_status"] = "pending"
    _clear_motion_review_fields(item)


def _reopen_motion_asset_item(item: dict[str, Any]) -> None:
    item["status"] = "review" if str(item.get("latest_render_path", "")).strip() else "todo"
    item["review_outcome"] = ""
    item["reviewer"] = ""
    item["reviewed_at"] = ""
    item["review_notes"] = ""
    item["review_tags"] = []


def _reset_motion_assets_for_source(manifest: dict[str, Any], source_still_id: str) -> None:
    motion_section = manifest.setdefault("motion_assets", {})
    for motion_item in motion_section.get("items", []):
        if str(motion_item.get("source_still_id", "")).strip() != str(source_still_id).strip():
            continue
        if str(motion_item.get("status", "")).strip() == "not_needed":
            continue
        if (
            str(motion_item.get("latest_render_path", "")).strip()
            or str(motion_item.get("latest_render_manifest_path", "")).strip()
            or str(motion_item.get("status", "")).strip() in {"review", "done"}
        ):
            _reopen_motion_asset_item(motion_item)


def _render_viz_manifest(
    context: Context,
    *,
    command_name: str,
    family: str,
    preset: str,
    source_image: str = "",
    overrides: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    governance = context.viz_repo.find_text_governance(family, preset)
    if not governance:
        raise SystemExit(f"Missing text governance matrix entry for {family}/{preset}.")
    viz_ce = Path(context.channel["paths"]["viz_ce_path"])
    render_args = [
        str(viz_ce),
        "render",
        command_name,
        family,
        preset,
        "--selected-seed",
        str(governance.canonical_seed),
    ]
    if command_name == "finalize-still":
        if not source_image:
            raise SystemExit(f"{family}/{preset} finalize-still requires a source image.")
        render_args.extend(
            [
                "--source-image",
                source_image,
                "--source-text-repair",
                governance.source_text_repair_mode,
                "--typography",
                governance.typography_mode,
            ]
        )
    for key, value in sorted((overrides or {}).items()):
        render_args.extend(["--set", f"{key}={json.dumps(value)}"])
    render_output = run_checked_command(render_args, cwd=Path(context.channel["paths"]["viz_root"]))
    pipeline_manifest_path = Path(parse_info_value(render_output, "INFO  pipeline manifest ->")).expanduser()
    if not pipeline_manifest_path.exists():
        raise SystemExit(f"Pipeline manifest is missing: {pipeline_manifest_path}")
    pipeline_manifest = _load_pipeline_manifest(pipeline_manifest_path)
    _require_visual_qc_passed(pipeline_manifest, manifest_path=pipeline_manifest_path)
    final_outputs = pipeline_manifest.get("final_outputs")
    if not isinstance(final_outputs, list) or not final_outputs:
        raise SystemExit(f"{family}/{preset} pipeline did not record final_outputs.")
    final_output_path = Path(str(final_outputs[0])).expanduser()
    if not final_output_path.exists():
        raise SystemExit(f"Rendered final output is missing: {final_output_path}")
    return final_output_path, pipeline_manifest_path


def _join_render_descriptors(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return f"{', '.join(cleaned[:-1])}, and {cleaned[-1]}"


def _opening_scene_render_overrides(manifest: dict[str, Any], scene_item_id: str) -> dict[str, Any]:
    visual_research = manifest.get("visual_research", {})
    opening_sequence = visual_research.get("opening_sequence", {})
    opening_scene_id = str(opening_sequence.get("planned_scene_id", "")).strip()
    if not opening_scene_id or scene_item_id != opening_scene_id:
        return {}
    inventory_path_raw = str(visual_research.get("source_inventory_path", "")).strip()
    if not inventory_path_raw:
        raise SystemExit("Opening tableau render requires visual_research.source_inventory_path.")
    inventory = load_source_inventory(Path(inventory_path_raw).expanduser())
    inventory_errors = list(inventory.get("errors") or [])
    if inventory_errors:
        raise SystemExit(inventory_errors[0])

    slot_entries_by_id: dict[str, list[dict[str, Any]]] = {}
    for entry in inventory.get("sources", []):
        if str(entry.get("coverage_id", "")).strip() != "opening":
            continue
        slot_id = str(entry.get("opening_slot_id", "")).strip()
        if not slot_id:
            continue
        slot_entries_by_id.setdefault(slot_id, []).append(entry)

    ordered_slots: list[dict[str, Any]] = []
    subject_descriptor = ""
    subject_display_label = ""
    support_labels: list[str] = []
    support_descriptors: list[str] = []
    required_reads: list[str] = []
    for slot in opening_sequence.get("slots") or []:
        if not isinstance(slot, dict):
            continue
        slot_id = str(slot.get("slot_id", "")).strip()
        if not slot_id:
            continue
        slot_entries = slot_entries_by_id.get(slot_id, [])
        if not slot_entries:
            raise SystemExit(f"Opening tableau render is missing a source entry for slot `{slot_id}`.")
        selected_entry = next(
            (entry for entry in slot_entries if str(entry.get("board_asset_path", "")).strip()),
            slot_entries[0],
        )
        asset_path = display_asset_path(selected_entry)
        if not asset_path:
            raise SystemExit(f"Opening tableau slot `{slot_id}` is missing a display asset.")
        asset_file = Path(asset_path).expanduser()
        if not asset_file.exists():
            raise SystemExit(f"Opening tableau asset is missing for slot `{slot_id}`: {asset_file}")
        display_label = str(slot.get("display_label", "")).strip() or str(selected_entry.get("candidate_label", "")).strip() or slot_id
        descriptor = str(slot.get("visual_descriptor", "")).strip() or display_label
        role = str(slot.get("role", "")).strip() or "supporting_object"
        required_reads.append(display_label)
        if role == "subject_object":
            subject_descriptor = descriptor
            subject_display_label = display_label
        else:
            support_labels.append(display_label)
            support_descriptors.append(descriptor)
        ordered_slots.append(
            {
                "slot_id": slot_id,
                "display_label": display_label,
                "role": role,
                "visual_descriptor": descriptor,
                "asset_path": str(asset_file),
                "candidate_count": len(slot_entries),
                "source_url": str(selected_entry.get("source_url", "")).strip(),
                "candidate_label": str(selected_entry.get("candidate_label", "")).strip(),
            }
        )

    if not ordered_slots:
        raise SystemExit("Opening tableau render requires at least one ordered opening slot.")
    if not subject_descriptor:
        raise SystemExit("Opening tableau render requires one subject_object slot.")

    required_reads_text = _join_render_descriptors(required_reads)
    support_summary = _join_render_descriptors(support_labels)
    focus_transition = str(opening_sequence.get("focus_transition", "")).strip()
    payload = {
        "episode_id": str(manifest.get("id", "")).strip(),
        "time_period_label": str(opening_sequence.get("time_period_label", "")).strip(),
        "focus_transition": focus_transition,
        "subject_action": str(opening_sequence.get("subject_action", "")).strip(),
        "subject_slot_id": next(
            (str(slot.get("slot_id", "")).strip() for slot in opening_sequence.get("slots") or [] if str(slot.get("role", "")).strip() == "subject_object"),
            "",
        ),
        "subject_descriptor": subject_descriptor,
        "subject_display_label": subject_display_label,
        "required_reads": required_reads,
        "slots": ordered_slots,
    }
    return {
        "opening_payload": payload,
        "opening_anchor_fragment": f"central dominant subject isolated for the pull-in: {subject_descriptor}",
        "opening_support_summary": support_summary,
        "opening_required_reads": required_reads_text,
    }


def _require_opening_scene_approval_gate(manifest: dict[str, Any], scene_item_id: str) -> None:
    visual_research = manifest.get("visual_research", {})
    opening_sequence = visual_research.get("opening_sequence", {})
    if not bool(opening_sequence.get("block_downstream_until_approved", True)):
        return
    opening_scene_id = str(opening_sequence.get("planned_scene_id", "")).strip()
    if not opening_scene_id or scene_item_id == opening_scene_id:
        return
    try:
        opening_item = resolve_scene_item(manifest, opening_scene_id)
    except SystemExit:
        return
    if str(opening_item.get("review_status", "")).strip() == "approved":
        return
    raise SystemExit(
        f"Opening still `{opening_scene_id}` must be approved before rendering downstream still `{scene_item_id}`."
    )


def set_scene_archetype(context: Context, manifest: dict[str, Any], scene_item_id: str, archetype_id: str) -> tuple[Path, Path]:
    manifest_path = _resolve_manifest_path(manifest)
    item = resolve_scene_item(manifest, scene_item_id)
    archetype = find_scene_archetype(context, archetype_id)
    assert archetype is not None
    episode_id = str(manifest["id"])
    reference_dir = build_episode_reference_dir(context, episode_id, scene_item_id)
    item["archetype_id"] = archetype_id
    item["archetype_status"] = "resolved"
    item["preset"] = str(archetype["preset"])
    item["reference_dir"] = str(reference_dir)
    item["latest_render_path"] = ""
    item["latest_render_manifest_path"] = ""
    item["approved_proof_path"] = ""
    item["approved_proof_manifest_path"] = ""
    item["selected_asset"] = ""
    item["review_status"] = "pending"
    item["motion_review_status"] = "pending"
    _clear_review_fields(item)
    _clear_motion_review_fields(item)
    item["notes"] = str(archetype.get("notes", ""))
    item["output_path"] = str(build_scene_output_path(context, episode_id, item, scene_items(manifest)))
    for motion_item in manifest.get("motion_assets", {}).get("items", []):
        if str(motion_item.get("source_still_id", "")) != scene_item_id:
            continue
        if str(motion_item.get("latest_render_path", "")).strip() or str(motion_item.get("status", "")) == "done":
            continue
        motion_item["output_path"] = str(reference_dir / "selects" / "hero_video.mp4")
    manifest["scene_stills"]["status"] = derive_scene_lane_status(scene_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return reference_dir, Path(str(item["output_path"]))


def render_scene_still(context: Context, manifest: dict[str, Any], scene_item_id: str) -> tuple[Path, Path]:
    resolve_scene_item(manifest, scene_item_id)
    raise SystemExit(RETIRED_SCENE_STILL_WORKFLOW_MESSAGE)


def render_packaging_still(context: Context, manifest: dict[str, Any], item_id: str) -> tuple[Path, Path]:
    manifest_path = _resolve_manifest_path(manifest)
    item = resolve_packaging_item(manifest, item_id)
    preset = str(item.get("preset", "")).strip()
    if not preset:
        raise SystemExit(f"Packaging item `{item_id}` is missing a preset.")
    family = PACKAGING_KIND_TO_FAMILY[normalize_kind(str(item.get("kind", "")))]
    final_output_path, pipeline_manifest_path = _render_viz_manifest(
        context,
        command_name="review-proof",
        family=family,
        preset=preset,
    )
    item["latest_render_path"] = str(final_output_path)
    item["latest_render_manifest_path"] = str(pipeline_manifest_path)
    item["approved_proof_path"] = ""
    item["approved_proof_manifest_path"] = ""
    item["selected_asset"] = ""
    item["review_status"] = "pending"
    _clear_review_fields(item)
    manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return final_output_path, pipeline_manifest_path


def finalize_scene_still(context: Context, manifest: dict[str, Any], scene_item_id: str) -> tuple[Path, Path]:
    resolve_scene_item(manifest, scene_item_id)
    raise SystemExit(RETIRED_SCENE_STILL_WORKFLOW_MESSAGE)


def finalize_packaging_still(context: Context, manifest: dict[str, Any], item_id: str) -> tuple[Path, Path]:
    manifest_path = _resolve_manifest_path(manifest)
    item = resolve_packaging_item(manifest, item_id)
    if str(item.get("review_status", "")).strip() != "approved":
        raise SystemExit(f"Packaging item `{item_id}` must be approved before finalize-packaging.")
    preset = str(item.get("preset", "")).strip()
    if not preset:
        raise SystemExit(f"Packaging item `{item_id}` is missing a preset.")
    family = PACKAGING_KIND_TO_FAMILY[normalize_kind(str(item.get("kind", "")))]
    approved_proof_path = str(item.get("approved_proof_path", "")).strip()
    if not approved_proof_path:
        raise SystemExit(f"Packaging item `{item_id}` has no approved proof to finalize.")
    approved_proof_asset = Path(approved_proof_path).expanduser().resolve()
    if not approved_proof_asset.exists():
        raise SystemExit(f"Approved proof is missing: {approved_proof_asset}")
    final_output_path, pipeline_manifest_path = _render_viz_manifest(
        context,
        command_name="finalize-still",
        family=family,
        preset=preset,
        source_image=str(approved_proof_asset),
    )
    output_raw = str(item.get("output_path", "")).strip()
    if not output_raw:
        raise SystemExit(f"Packaging item `{item_id}` is missing output_path.")
    output_path = Path(output_raw).expanduser()
    canonical_manifest_path = _copy_asset_and_manifest(final_output_path, pipeline_manifest_path, output_path)
    item["selected_asset"] = str(output_path)
    manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return output_path, canonical_manifest_path


def promote_scene_still(
    context: Context,
    manifest: dict[str, Any],
    scene_item_id: str,
    asset: str,
    *,
    reviewer: str = "",
    review_notes: str = "",
) -> tuple[Path, Path]:
    manifest_path = _resolve_manifest_path(manifest)
    item = resolve_scene_item(manifest, scene_item_id)
    output_raw = str(item.get("output_path", "")).strip()
    if not output_raw:
        raise SystemExit(f"Scene item `{scene_item_id}` is missing output_path.")
    asset_path = Path(asset).expanduser().resolve()
    if not asset_path.exists():
        raise SystemExit(f"Approved still is missing: {asset_path}")
    proof_manifest_path = _resolve_output_manifest_path(
        asset_path,
        str(item.get("latest_render_path", "")).strip(),
        str(item.get("latest_render_manifest_path", "")).strip(),
    )
    _require_visual_qc_passed(_load_pipeline_manifest(proof_manifest_path), manifest_path=proof_manifest_path)
    output_path = Path(output_raw).expanduser()
    canonical_manifest_path = _copy_asset_and_manifest(asset_path, proof_manifest_path, output_path)
    if not str(item.get("approved_proof_path", "")).strip():
        _stamp_approved_proof(item, asset_path, proof_manifest_path)
    item["selected_asset"] = str(output_path)
    item["review_status"] = "approved"
    item["reviewer"] = str(reviewer).strip()
    item["reviewed_at"] = utc_now_iso() if str(reviewer).strip() else ""
    item["review_notes"] = str(review_notes).strip()
    item["review_tags"] = []
    manifest["scene_stills"]["status"] = derive_scene_lane_status(scene_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return output_path, canonical_manifest_path


def promote_packaging_still(
    context: Context,
    manifest: dict[str, Any],
    item_id: str,
    asset: str,
    *,
    reviewer: str = "",
    review_notes: str = "",
) -> tuple[Path, Path]:
    manifest_path = _resolve_manifest_path(manifest)
    item = resolve_packaging_item(manifest, item_id)
    output_raw = str(item.get("output_path", "")).strip()
    if not output_raw:
        raise SystemExit(f"Packaging item `{item_id}` is missing output_path.")
    asset_path = Path(asset).expanduser().resolve()
    if not asset_path.exists():
        raise SystemExit(f"Approved still is missing: {asset_path}")
    proof_manifest_path = _resolve_output_manifest_path(
        asset_path,
        str(item.get("latest_render_path", "")).strip(),
        str(item.get("latest_render_manifest_path", "")).strip(),
    )
    _require_visual_qc_passed(_load_pipeline_manifest(proof_manifest_path), manifest_path=proof_manifest_path)
    output_path = Path(output_raw).expanduser()
    canonical_manifest_path = _copy_asset_and_manifest(asset_path, proof_manifest_path, output_path)
    if not str(item.get("approved_proof_path", "")).strip():
        _stamp_approved_proof(item, asset_path, proof_manifest_path)
    item["selected_asset"] = str(output_path)
    item["review_status"] = "approved"
    item["reviewer"] = str(reviewer).strip()
    item["reviewed_at"] = utc_now_iso() if str(reviewer).strip() else ""
    item["review_notes"] = str(review_notes).strip()
    item["review_tags"] = []
    manifest["packaging_stills"]["status"] = derive_packaging_lane_status(packaging_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return output_path, canonical_manifest_path
