from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from orchestration.domain import build_scene_lookup, motion_item_authoring_mode, motion_items, scene_items, utc_now_iso
from orchestration.io import Context, find_motion_archetype, find_scene_archetype, path_exists, write_episode_manifest
from orchestration.research_sources import preflight_motion_source_asset


def resolve_motion_item(manifest: dict[str, Any], motion_item_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    scenes = build_scene_lookup(scene_items(manifest))
    for item in motion_items(manifest):
        if str(item.get("id")) == motion_item_id:
            source_id = str(item.get("source_still_id", ""))
            source_still = scenes.get(source_id)
            if not source_still:
                raise SystemExit(f"Motion item `{motion_item_id}` references unknown scene still `{source_id}`.")
            return item, source_still
    raise SystemExit(f"Unknown motion item id: {motion_item_id}")


def derive_motion_lane_status(items: list[dict[str, Any]]) -> str:
    statuses = [str(item.get("status", "todo")) for item in items]
    if statuses and all(status in {"done", "not_needed"} for status in statuses):
        return "done"
    if any(status in {"review", "in_progress"} for status in statuses):
        return "review"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "todo" for status in statuses):
        return "todo"
    return "todo"


def remove_file_like_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def run_checked_command(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(args, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
    if result.returncode != 0:
        raise SystemExit(combined or f"Command failed with exit code {result.returncode}: {' '.join(args)}")
    return combined


def parse_info_value(output: str, prefix: str) -> str:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped.split(prefix, 1)[1].strip()
    raise SystemExit(f"Could not parse `{prefix}` from command output.")


def probe_video_duration_seconds(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
    )
    combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
    if result.returncode != 0:
        raise SystemExit(combined or f"ffprobe failed for {video_path}")
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise SystemExit(f"Could not parse ffprobe duration for {video_path}") from exc


def resolve_motion_duration_seconds(video_path: Path, video_manifest: dict[str, Any]) -> float:
    try:
        duration = float(video_manifest.get("duration_seconds", 0.0) or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    if duration > 0.0:
        return duration
    return probe_video_duration_seconds(video_path)


def validate_motion_duration(
    video_path: Path,
    video_manifest: dict[str, Any],
    *,
    min_duration_seconds: float,
    motion_item_id: str,
) -> float:
    duration_seconds = resolve_motion_duration_seconds(video_path, video_manifest)
    if min_duration_seconds > 0.0 and duration_seconds + 1e-6 < min_duration_seconds:
        raise SystemExit(
            f"Motion proof `{motion_item_id}` is too short: "
            f"{duration_seconds:.3f}s < required {min_duration_seconds:.3f}s."
        )
    return duration_seconds


def _append_behavior_to_prompt(prompt: str, behavior: str) -> str:
    base_prompt = str(prompt).strip()
    behavior_text = str(behavior).strip()
    if not behavior_text:
        return base_prompt
    if not base_prompt:
        return behavior_text
    if base_prompt[-1] not in ".!?":
        base_prompt = f"{base_prompt}."
    return f"{base_prompt} Approved action: {behavior_text}"


def resolve_motion_source_asset(source_still: dict[str, Any]) -> Path | None:
    approved_proof_path = str(source_still.get("approved_proof_path", "")).strip()
    if approved_proof_path:
        approved_proof = Path(approved_proof_path).expanduser()
        if approved_proof.exists():
            return approved_proof
    selected_asset = str(source_still.get("selected_asset", "")).strip()
    if selected_asset:
        selected = Path(selected_asset).expanduser()
        if selected.exists():
            return selected
    return None


def resolve_motion_contract(
    context: Context,
    episode_id: str,
    item: dict[str, Any],
    source_still: dict[str, Any],
) -> dict[str, Any]:
    if motion_item_authoring_mode(item) == "particle_workbench":
        return {
            "archetype_id": str(item.get("archetype_id", "")).strip(),
            "prompt": str(item.get("prompt", "")).strip(),
            "behavior": str(item.get("behavior", "")).strip(),
            "resolved_prompt": str(item.get("prompt", "")).strip(),
            "frames": int(item.get("frames") or 33),
            "width": int(item.get("width") or 640),
            "height": int(item.get("height") or 384),
            "pipeline": str(item.get("pipeline") or "particle_workbench"),
            "min_duration_seconds": float(item.get("min_duration_seconds", 0.0) or 0.0),
            "typography_intent_path": None,
        }
    archetype_id = str(item.get("archetype_id", "")).strip()
    if not archetype_id:
        scene_archetype_id = str(source_still.get("archetype_id", "")).strip()
        scene_archetype = find_scene_archetype(context, scene_archetype_id) if scene_archetype_id else None
        archetype_id = str(scene_archetype.get("default_motion_archetype_id", "")).strip() if scene_archetype else ""
    if not archetype_id:
        raise SystemExit(f"Motion item `{item.get('id', '')}` is missing archetype_id.")
    archetype = find_motion_archetype(context, archetype_id)
    certification = context.viz_repo.find_motion_certification(episode_id, str(item.get("id", "")))
    prompt = certification.prompt if certification else str(item.get("prompt") or archetype["prompt"])
    behavior = str(item.get("behavior", "")).strip()
    existing_min_duration_seconds = float(item.get("min_duration_seconds", 0.0) or 0.0)
    guardrail_min_duration_seconds = float(
        context.viz_repo.find_motion_guardrails(
            episode_id,
            str(item.get("id", "")),
            preset_id=certification.preset_id if certification else "",
        ).get("min_duration_seconds", 0.0)
        or 0.0
    )
    min_duration_seconds = max(existing_min_duration_seconds, guardrail_min_duration_seconds)
    return {
        "archetype_id": archetype_id,
        "prompt": prompt,
        "behavior": behavior,
        "resolved_prompt": _append_behavior_to_prompt(prompt, behavior),
        "frames": certification.frames if certification else int(item.get("frames") or archetype["frames"]),
        "width": certification.width if certification else int(item.get("width") or archetype["width"]),
        "height": certification.height if certification else int(item.get("height") or archetype["height"]),
        "pipeline": certification.pipeline if certification else str(item.get("pipeline") or archetype["pipeline"]),
        "min_duration_seconds": min_duration_seconds,
        "typography_intent_path": (
            certification.typography_intent_path
            if certification and certification.typography_intent_path
            else Path(str(archetype.get("handoff_typography_intent_path", "")).strip())
            if str(archetype.get("handoff_typography_intent_path", "")).strip()
            else None
        ),
    }


def motion_item_requires_alpha_export(manifest: dict[str, Any], motion_item_id: str) -> bool:
    for composition in manifest.get("assembly", {}).get("compositions", []):
        if not isinstance(composition, dict):
            continue
        for overlay in composition.get("overlays", []):
            if not isinstance(overlay, dict):
                continue
            if str(overlay.get("motion_asset_id", "")).strip() == motion_item_id:
                return True
    return False


def _ensure_motion_output_path_for_role(item: dict[str, Any], *, requires_alpha: bool) -> None:
    output_path = str(item.get("output_path", "")).strip()
    if not output_path:
        return
    path = Path(output_path).expanduser()
    if requires_alpha and path.suffix.lower() != ".mov":
        item["output_path"] = str(path.with_suffix(".mov"))
    elif not requires_alpha and path.suffix.lower() == ".mov":
        item["output_path"] = str(path.with_suffix(".mp4"))


def _persist_motion_render_result(
    manifest_path: Path,
    manifest: dict[str, Any],
    item: dict[str, Any],
    proof_video_path: Path,
    video_manifest_path: Path,
) -> None:
    item["latest_render_path"] = str(proof_video_path)
    item["latest_render_manifest_path"] = str(video_manifest_path)
    item["status"] = "review"
    item["review_outcome"] = ""
    item["reviewer"] = ""
    item["reviewed_at"] = ""
    item["review_notes"] = ""
    item["review_tags"] = []
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)


def render_legacy_motion_proof(context: Context, manifest: dict[str, Any], motion_item_id: str) -> tuple[Path, Path]:
    manifest_path = Path(str(manifest["_manifest_path"]))
    item, source_still = resolve_motion_item(manifest, motion_item_id)
    if str(item.get("status", "todo")) == "not_needed":
        raise SystemExit(f"Motion item `{motion_item_id}` is marked not_needed.")
    source_asset = resolve_motion_source_asset(source_still)
    if source_asset is None:
        raise SystemExit(f"Source still `{source_still.get('id', '')}` has no approved proof or selected asset to hand off.")
    if str(source_still.get("motion_review_status", "")) != "approved_for_motion":
        raise SystemExit(f"Source still `{source_still.get('id', '')}` is not approved for motion.")
    preflight_asset_path, _preflight_summary = preflight_motion_source_asset(
        context,
        motion_item_id=motion_item_id,
        source_still_id=str(source_still.get("id", "")),
        preset=str(source_still.get("preset", "")),
        selected_asset_path=source_asset,
    )
    contract = resolve_motion_contract(context, str(manifest["id"]), item, source_still)
    if not contract["behavior"]:
        raise SystemExit(f"Motion item `{motion_item_id}` is missing behavior.")
    viz_ce = Path(context.channel["paths"]["viz_ce_path"])
    stage_args = [
        str(viz_ce),
        "handoff-stage",
        str(preflight_asset_path),
        "--from",
        "comfy",
        "--prompt",
        contract["resolved_prompt"],
        "--next-step",
        "review",
        "--width",
        str(contract["width"]),
        "--height",
        str(contract["height"]),
    ]
    if contract["typography_intent_path"]:
        stage_args.extend(["--typography-intent", str(contract["typography_intent_path"])])
    stage_output = run_checked_command(stage_args, cwd=Path(context.channel["paths"]["viz_root"]))
    staged_path = parse_info_value(stage_output, "INFO  Staged asset:")
    video_args = [
        str(viz_ce),
        "handoff-i2v",
        staged_path,
        "--frames",
        str(contract["frames"]),
        "--width",
        str(contract["width"]),
        "--height",
        str(contract["height"]),
        "--pipeline",
        contract["pipeline"],
        "--typography",
        "auto",
    ]
    video_output = run_checked_command(video_args, cwd=Path(context.channel["paths"]["viz_root"]))
    video_manifest_path = Path(parse_info_value(video_output, "INFO  Handoff video manifest:"))
    video_manifest = json.loads(video_manifest_path.read_text(encoding="utf-8"))
    proof_video_path = Path(str(video_manifest["output_path"]))
    duration_seconds = validate_motion_duration(
        proof_video_path,
        video_manifest,
        min_duration_seconds=float(contract["min_duration_seconds"]),
        motion_item_id=motion_item_id,
    )
    item["archetype_id"] = contract["archetype_id"]
    item["prompt"] = contract["prompt"]
    item["behavior"] = contract["behavior"]
    item["frames"] = contract["frames"]
    item["width"] = contract["width"]
    item["height"] = contract["height"]
    item["pipeline"] = contract["pipeline"]
    item["min_duration_seconds"] = contract["min_duration_seconds"]
    _persist_motion_render_result(manifest_path, manifest, item, proof_video_path, video_manifest_path)
    return proof_video_path, video_manifest_path


def render_workbench_motion_proof(context: Context, manifest: dict[str, Any], motion_item_id: str) -> tuple[Path, Path]:
    manifest_path = Path(str(manifest["_manifest_path"]))
    item, source_still = resolve_motion_item(manifest, motion_item_id)
    if str(item.get("status", "todo")) == "not_needed":
        raise SystemExit(f"Motion item `{motion_item_id}` is marked not_needed.")
    source_asset = resolve_motion_source_asset(source_still)
    if source_asset is None:
        raise SystemExit(f"Source still `{source_still.get('id', '')}` has no approved proof or selected asset to hand off.")
    if str(source_still.get("motion_review_status", "")) != "approved_for_motion":
        raise SystemExit(f"Source still `{source_still.get('id', '')}` is not approved for motion.")
    workbench_project_path = str(item.get("workbench_project_path", "")).strip()
    if not workbench_project_path:
        raise SystemExit(f"Motion item `{motion_item_id}` is missing workbench_project_path.")
    if not path_exists(workbench_project_path):
        raise SystemExit(f"Workbench project is missing for `{motion_item_id}`: {workbench_project_path}")
    contract = resolve_motion_contract(context, str(manifest["id"]), item, source_still)
    if not contract["behavior"]:
        raise SystemExit(f"Motion item `{motion_item_id}` is missing behavior.")
    alpha_required = motion_item_requires_alpha_export(manifest, motion_item_id)
    _ensure_motion_output_path_for_role(item, requires_alpha=alpha_required)
    viz_ce = Path(context.channel["paths"]["viz_ce_path"])
    export_args = [
        str(viz_ce),
        "workbench",
        "export-shot",
        "--project",
        workbench_project_path,
        "--width",
        str(contract["width"]),
        "--height",
        str(contract["height"]),
        "--frames",
        str(contract["frames"]),
        "--min-duration-seconds",
        f"{float(contract['min_duration_seconds']):.3f}",
    ]
    if alpha_required:
        export_args.append("--alpha")
    export_output = run_checked_command(export_args, cwd=Path(context.channel["paths"]["viz_root"]))
    try:
        export_manifest = json.loads(export_output)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Workbench export returned invalid JSON: {export_output}") from exc
    if not isinstance(export_manifest, dict):
        raise SystemExit(f"Workbench export returned invalid payload for `{motion_item_id}`.")
    proof_video_path = Path(str(export_manifest.get("output_path", ""))).expanduser()
    video_manifest_path = Path(str(export_manifest.get("manifest_path", ""))).expanduser()
    if not proof_video_path.exists():
        raise SystemExit(f"Workbench proof video is missing: {proof_video_path}")
    if not video_manifest_path.exists():
        raise SystemExit(f"Workbench proof manifest is missing: {video_manifest_path}")
    duration_payload = json.loads(video_manifest_path.read_text(encoding="utf-8"))
    validate_motion_duration(
        proof_video_path,
        duration_payload,
        min_duration_seconds=float(contract["min_duration_seconds"]),
        motion_item_id=motion_item_id,
    )
    item["frames"] = contract["frames"]
    item["width"] = contract["width"]
    item["height"] = contract["height"]
    item["pipeline"] = contract["pipeline"]
    item["min_duration_seconds"] = contract["min_duration_seconds"]
    _persist_motion_render_result(manifest_path, manifest, item, proof_video_path, video_manifest_path)
    return proof_video_path, video_manifest_path


def render_motion_proof(context: Context, manifest: dict[str, Any], motion_item_id: str) -> tuple[Path, Path]:
    item, _source_still = resolve_motion_item(manifest, motion_item_id)
    if motion_item_authoring_mode(item) == "particle_workbench":
        return render_workbench_motion_proof(context, manifest, motion_item_id)
    return render_legacy_motion_proof(context, manifest, motion_item_id)


def promote_motion_proof(
    context: Context,
    manifest: dict[str, Any],
    motion_item_id: str,
    video: str,
    *,
    reviewer: str = "",
    review_notes: str = "",
) -> tuple[Path, Path]:
    manifest_path = Path(str(manifest["_manifest_path"]))
    item, _source_still = resolve_motion_item(manifest, motion_item_id)
    _ensure_motion_output_path_for_role(item, requires_alpha=motion_item_requires_alpha_export(manifest, motion_item_id))
    proof_video_path = Path(video).expanduser().resolve()
    if not proof_video_path.exists():
        raise SystemExit(f"Proof video is missing: {proof_video_path}")
    proof_manifest_path = Path(f"{proof_video_path}.json")
    if not proof_manifest_path.exists():
        raise SystemExit(f"Proof video manifest is missing: {proof_manifest_path}")
    contract = resolve_motion_contract(context, str(manifest["id"]), item, _source_still)
    proof_manifest = json.loads(proof_manifest_path.read_text(encoding="utf-8"))
    validate_motion_duration(
        proof_video_path,
        proof_manifest,
        min_duration_seconds=float(contract["min_duration_seconds"]),
        motion_item_id=motion_item_id,
    )
    output_raw = str(item.get("output_path", "")).strip()
    if not output_raw:
        raise SystemExit(f"Motion item `{motion_item_id}` is missing output_path.")
    output_path = Path(output_raw).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_manifest_path = Path(f"{output_path}.json")
    if proof_video_path.resolve() != output_path.resolve():
        remove_file_like_path(output_path)
        shutil.copy2(proof_video_path, output_path)
    if proof_manifest_path.resolve() != canonical_manifest_path.resolve():
        remove_file_like_path(canonical_manifest_path)
        shutil.copy2(proof_manifest_path, canonical_manifest_path)
    item["latest_render_path"] = str(proof_video_path)
    item["latest_render_manifest_path"] = str(proof_manifest_path)
    item["min_duration_seconds"] = contract["min_duration_seconds"]
    item["status"] = "done"
    item["review_outcome"] = "approved"
    item["reviewer"] = str(reviewer).strip()
    item["reviewed_at"] = utc_now_iso() if str(reviewer).strip() else ""
    item["review_notes"] = str(review_notes).strip()
    item["review_tags"] = []
    manifest["motion_assets"]["status"] = derive_motion_lane_status(motion_items(manifest))
    write_episode_manifest(manifest_path, manifest)
    return output_path, canonical_manifest_path
