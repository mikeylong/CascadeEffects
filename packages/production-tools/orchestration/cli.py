from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from orchestration.assembly import assemble_episode_cut
from orchestration.contact_sheet import render_contact_sheet_pdf
from orchestration.domain import (
    build_production_report,
    derive_episode_state,
    format_production_report,
    format_state_summary,
    lane_order,
    print_board,
    render_brief,
)
from orchestration.io import (
    ROOT_DIR,
    Context,
    build_bootstrap_manifest,
    build_context,
    load_episode_manifest,
    promote_audio_package,
    resolve_episode_directories,
    resolve_target_manifests,
    utc_now_iso,
    write_episode_manifest,
    write_bootstrap_manifest,
    write_state_file,
)
from orchestration.inception_review import publish_inception_review_packet, write_inception_review_packet
from orchestration.motion import promote_motion_proof, render_motion_proof
from orchestration.publish import (
    publish_package_delete,
    publish_package_status,
    publish_package_update_title,
    publish_package_upload,
    scaffold_publish_notes,
    validate_publish_package_manifest,
)
from orchestration.research_sources import process_research_source_inventory
from orchestration.review import build_review_episode_detail
from orchestration.shorts_audio import (
    run_shorts_audio_audit,
    sync_shorts_audio_lane,
    write_historical_proof_annotations,
)
from orchestration.source_control import run_source_control_media_audit
from orchestration.source_control import install_source_media_pre_commit_hooks
from orchestration.stills import (
    finalize_packaging_still,
    finalize_scene_still,
    promote_packaging_still,
    promote_scene_still,
    render_packaging_still,
    render_scene_still,
    set_scene_archetype,
)


def command_doctor(context: Context, _args: argparse.Namespace) -> int:
    failures: list[str] = []
    print("doctor:")
    if sys.version_info < (3, 11):
        failures.append("python3.11+ is required.")
    else:
        print(f"  OK python {sys.version.split()[0]}")
    for key, value in context.channel["paths"].items():
        path = Path(value)
        if path.exists():
            print(f"  OK {key}: {path}")
        else:
            failures.append(f"{key} is missing: {path}")
    helper_path = Path(context.channel["paths"]["orchestrate_helper"])
    if helper_path.exists() and os.access(helper_path, os.X_OK):
        print(f"  OK internal helper: {helper_path}")
    else:
        failures.append(f"Internal helper is missing or not executable: {helper_path}")
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"  OK ffmpeg: {ffmpeg_path}")
    else:
        failures.append("ffmpeg is not installed or not on PATH.")
    if context.web_entry_ids:
        print(f"  OK web launch entries discovered: {', '.join(sorted(context.web_entry_ids))}")
    else:
        failures.append("No web entry ids found in site-facts.ts.")
    print(f"  OK motion certification entries: {len(context.viz_repo.motion_certifications())}")
    print(f"  OK text governance entries: {len(context.viz_repo.text_governance())}")
    if failures:
        print("  FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    return 0


def command_bootstrap(context: Context, args: argparse.Namespace) -> int:
    pillar = args.pillar or str(context.asset_archetypes.get("defaults", {}).get("pillar", "design-failures"))
    episode_dirs = resolve_episode_directories(context, args.episode, args.all)
    exit_code = 0
    for episode_dir in episode_dirs:
        manifest = build_bootstrap_manifest(
            context,
            episode_dir,
            scene_archetype_id=args.scene_archetype,
            pillar=pillar,
        )
        manifest_path = context.root / "episodes" / f"{manifest['id']}.toml"
        if manifest_path.exists():
            print(f"skipped {manifest['id']} -> {manifest_path} (already exists)")
            continue
        path = write_bootstrap_manifest(context, manifest)
        notes_path = scaffold_publish_notes(context, manifest)
        review_packet = write_inception_review_packet(context, manifest)
        state = derive_episode_state(load_episode_manifest(path), context)
        print(f"bootstrapped {manifest['id']} -> {path}")
        print(f"publish notes scaffold -> {notes_path}")
        print(f"inception review packet -> {review_packet['manifest_path']}")
        print(f"local inception review -> {review_packet['local_review_url']}")
        print(f"production inception review -> {review_packet['remote_review_url']}")
        if getattr(args, "skip_remote_review", False):
            print("remote inception review publish skipped by --skip-remote-review")
        else:
            try:
                receipt = publish_inception_review_packet(context, review_packet["packet_root"], review_id=str(manifest["id"]))
                print(f"remote inception review manifest -> {receipt.get('manifestBlobUrl', '')}")
            except RuntimeError as exc:
                print(f"remote inception review publish failed: {exc}")
                exit_code = 1
        print(format_state_summary(state))
        if state["errors"]:
            exit_code = 1
    return exit_code


def command_board(context: Context, _args: argparse.Namespace) -> int:
    return print_board(context)


def command_show(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    state = derive_episode_state(manifest, context)
    review_detail = build_review_episode_detail(context, args.episode_id)
    print(json.dumps({"manifest": manifest, "state": state, "review": review_detail}, indent=2, sort_keys=True))
    return 0


def command_sync(context: Context, args: argparse.Namespace) -> int:
    manifests = resolve_target_manifests(context, args.episode_id, args.all)
    exit_code = 0
    for manifest in manifests:
        state = derive_episode_state(manifest, context)
        state_path = write_state_file(context, manifest, state)
        print(f"synced {manifest['id']} -> {state_path}")
        if state["errors"]:
            exit_code = 1
            print(format_state_summary(state))
    return exit_code


def command_validate(context: Context, args: argparse.Namespace) -> int:
    manifests = resolve_target_manifests(context, args.episode_id, args.all)
    exit_code = 0
    for manifest in manifests:
        state = derive_episode_state(manifest, context)
        print(format_state_summary(state))
        if state["errors"]:
            exit_code = 1
    return exit_code


def command_next(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    state = derive_episode_state(manifest, context)
    print(json.dumps(state["next_action"], indent=2, sort_keys=True))
    return 1 if state["errors"] else 0


def command_report(context: Context, args: argparse.Namespace) -> int:
    report = build_production_report(context)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_production_report(report, context))
    return 0


def command_publish_check(context: Context, args: argparse.Namespace) -> int:
    payload = _deprecated_publish_payload(getattr(args, "command", "publish-check"))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1


def command_publish_prepare(context: Context, args: argparse.Namespace) -> int:
    payload = _deprecated_publish_payload(getattr(args, "command", "publish-prepare"))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1


def command_publish(context: Context, args: argparse.Namespace) -> int:
    payload = _deprecated_publish_payload(getattr(args, "command", "publish"))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1


def command_publish_status(context: Context, args: argparse.Namespace) -> int:
    payload = _deprecated_publish_payload(getattr(args, "command", "publish-status"))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1


def _deprecated_publish_payload(command: str) -> dict[str, Any]:
    return {
        "ok": False,
        "deprecated": True,
        "command": command,
        "message": (
            "Episode-level publish automation is deprecated because Shorts publishing is now package-based. "
            "Use `ce orchestrate publish-package-check <manifest_path>`, then the package upload/status commands for unlisted review uploads."
        ),
        "replacement": "publish-package-check <manifest_path>",
    }


def command_publish_package_check(context: Context, args: argparse.Namespace) -> int:
    result = validate_publish_package_manifest(args.manifest_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


def _print_publish_package_error(command: str, exc: Exception) -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "command": command,
                "error": str(exc),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1


def command_publish_package_upload(context: Context, args: argparse.Namespace) -> int:
    try:
        result = publish_package_upload(args.manifest_path, privacy=args.privacy)
    except Exception as exc:
        return _print_publish_package_error("publish-package-upload", exc)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_publish_package_status(context: Context, args: argparse.Namespace) -> int:
    try:
        result = publish_package_status(args.receipt_or_video_id)
    except Exception as exc:
        return _print_publish_package_error("publish-package-status", exc)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_publish_package_update_title(context: Context, args: argparse.Namespace) -> int:
    try:
        result = publish_package_update_title(args.receipt_or_video_id, title=args.title)
    except Exception as exc:
        return _print_publish_package_error("publish-package-update-title", exc)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_publish_package_delete(context: Context, args: argparse.Namespace) -> int:
    try:
        result = publish_package_delete(
            args.receipt_or_video_id,
            confirm_video_id=args.confirm_video_id,
        )
    except Exception as exc:
        return _print_publish_package_error("publish-package-delete", exc)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_render_motion(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    proof_video_path, video_manifest_path = render_motion_proof(context, manifest, args.motion_item_id)
    print(f"rendered motion proof -> {proof_video_path}")
    print(f"motion manifest -> {video_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_process_research_sources(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    inventory = process_research_source_inventory(context, manifest)
    write_episode_manifest(Path(str(manifest["_manifest_path"])), manifest)
    payload = {
        "episode_id": str(manifest.get("id", "")).strip(),
        "source_inventory_path": str(manifest.get("visual_research", {}).get("source_inventory_path", "")).strip(),
        "summary": inventory.get("summary", {}),
        "errors": inventory.get("errors", []),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    summary = inventory.get("summary", {})
    unresolved_source_ids = summary.get("unresolved_source_ids", []) if isinstance(summary, dict) else []
    return 1 if unresolved_source_ids else 0


def command_render_contact_sheet(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    contact_sheet_path_raw = str(manifest.get("visual_research", {}).get("contact_sheet_path", "")).strip()
    if not contact_sheet_path_raw:
        raise SystemExit("Visual research is missing contact_sheet_path.")
    contact_sheet_path = Path(contact_sheet_path_raw)
    output_path = render_contact_sheet_pdf(manifest, contact_sheet_path)
    state = derive_episode_state(manifest, context)
    state_path = write_state_file(context, manifest, state)
    print(f"rendered contact sheet -> {output_path}")
    print(f"synced state -> {state_path}")
    return 0 if not state["errors"] else 1


def command_promote_motion(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    output_path, canonical_manifest_path = promote_motion_proof(context, manifest, args.motion_item_id, args.video)
    print(f"promoted motion -> {output_path}")
    print(f"promoted motion manifest -> {canonical_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_assemble(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    state = derive_episode_state(manifest, context)
    if state["errors"]:
        messages = "\n".join(f"- {issue['message']}" for issue in state["errors"])
        raise SystemExit(f"Assembly is blocked:\n{messages}")
    assembly_lane = state["lanes"]["assembly"]
    if not assembly_lane.get("ready_for_render"):
        missing = assembly_lane.get("missing_act_ids") or []
        if missing:
            raise SystemExit(
                "Assembly requires approved scene or motion coverage for every act. Missing: " + ", ".join(missing)
            )
        raise SystemExit("Assembly is not ready yet.")
    output_path = assemble_episode_cut(context, manifest)
    assembly = manifest.setdefault("assembly", {})
    assembly["status"] = "done"
    assembly["owner"] = "agent"
    assembly["renderer"] = "ffmpeg"
    assembly["strategy"] = "act_spine"
    assembly["master_video_path"] = str(output_path)
    assembly["completed_at"] = utc_now_iso()
    write_episode_manifest(Path(str(manifest["_manifest_path"])), manifest)
    print(f"assembled episode -> {output_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_brief(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    if args.lane not in lane_order(context):
        raise SystemExit(f"Unknown lane: {args.lane}")
    print(render_brief(context, manifest, args.lane))
    return 0


def command_set_scene_archetype(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    reference_dir, output_path = set_scene_archetype(context, manifest, args.scene_item_id, args.archetype_id)
    print(f"scene archetype set -> {args.scene_item_id} ({args.archetype_id})")
    print(f"reference dir -> {reference_dir}")
    print(f"scene output path -> {output_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_render_scene(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    latest_render_path, pipeline_manifest_path = render_scene_still(context, manifest, args.scene_item_id)
    print(f"rendered scene review proof -> {latest_render_path}")
    print(f"scene review manifest -> {pipeline_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_finalize_scene(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    output_path, canonical_manifest_path = finalize_scene_still(context, manifest, args.scene_item_id)
    print(f"finalized scene still -> {output_path}")
    print(f"finalized scene manifest -> {canonical_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_promote_scene(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    output_path, canonical_manifest_path = promote_scene_still(context, manifest, args.scene_item_id, args.asset)
    print(f"promoted scene still -> {output_path}")
    print(f"promoted scene manifest -> {canonical_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_render_packaging(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    latest_render_path, pipeline_manifest_path = render_packaging_still(context, manifest, args.item_id)
    print(f"rendered packaging review proof -> {latest_render_path}")
    print(f"packaging review manifest -> {pipeline_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_finalize_packaging(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    output_path, canonical_manifest_path = finalize_packaging_still(context, manifest, args.item_id)
    print(f"finalized packaging still -> {output_path}")
    print(f"finalized packaging manifest -> {canonical_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_promote_packaging(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    output_path, canonical_manifest_path = promote_packaging_still(context, manifest, args.item_id, args.asset)
    print(f"promoted packaging still -> {output_path}")
    print(f"promoted packaging manifest -> {canonical_manifest_path}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    return 0


def command_promote_audio(context: Context, args: argparse.Namespace) -> int:
    manifest = resolve_target_manifests(context, args.episode_id, False)[0]
    result = promote_audio_package(manifest)
    write_episode_manifest(Path(str(manifest["_manifest_path"])), manifest)
    state = derive_episode_state(manifest, context)
    state_path = write_state_file(context, manifest, state)
    print(f"promoted audio package -> {result['packaged_path']}")
    print(f"promoted QA transcript -> {result['transcript_path']}")
    print(f"audio package metadata -> {result['metadata'].get('metadata_path', '')}")
    print(f"updated episode manifest -> {manifest['_manifest_path']}")
    print(f"synced state -> {state_path}")
    if result["changed"]:
        print("audio review reset -> pending")
    if result["reset_downstream"]:
        print("downstream lanes reopened after promoted audio replaced an approved package")
    return 0


def command_review_inbox(context: Context, args: argparse.Namespace) -> int:
    command = ["review-inbox"]
    if args.json:
        command.append("--json")
    return _run_inbox_cli(command)


def command_review_action(context: Context, args: argparse.Namespace) -> int:
    command = ["review-action", args.episode_id, args.gate_type]
    if args.item_id:
        command.append(args.item_id)
    command.extend(["--decision", args.decision])
    if args.reviewer:
        command.extend(["--reviewer", args.reviewer])
    if args.notes:
        command.extend(["--notes", args.notes])
    for tag in args.tag or []:
        command.extend(["--tag", tag])
    return _run_inbox_cli(command)


def command_review_server(context: Context, args: argparse.Namespace) -> int:
    return _run_inbox_cli(["review-server", "--host", args.host, "--port", str(args.port)])


def command_shorts_audio_audit(context: Context, args: argparse.Namespace) -> int:
    report = run_shorts_audio_audit(
        context,
        output_path=Path(args.output) if args.output else None,
        use_historical_annotations=not args.no_historical_annotations,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"shorts audio audit -> {report['report_path']}")
        print(f"errors: {report['error_count']}  warnings: {report['warning_count']}")
        for issue in report["errors"][:12]:
            print(f"ERROR {issue['code']}: {issue['message']} ({issue.get('path', '')})")
        if report["error_count"] > 12:
            print(f"... {report['error_count'] - 12} more errors in report")
    return 0 if report["ok"] else 1


def command_shorts_audio_annotate_historical_proofs(context: Context, args: argparse.Namespace) -> int:
    result = write_historical_proof_annotations(context, output_path=Path(args.output) if args.output else None)
    print(f"historical proof annotations -> {result['annotation_path']}")
    print(f"annotations: {result['annotation_count']}  unresolved: {result['unresolved_count']}")
    return 0 if result["unresolved_count"] == 0 else 1


def command_shorts_audio_sync_lane(context: Context, args: argparse.Namespace) -> int:
    result = sync_shorts_audio_lane(context, args.lane, update_manifests=not args.no_update_manifests)
    print(f"synced Shorts audio lane -> {result['lane_id']}")
    print(f"short id -> {result['short_id']}")
    print(f"audio package -> {result['short_audio_package_path']}")
    print(f"registry -> {result['registry_path']}")
    print(f"active manifests updated -> {result['updated_manifest_count']}")
    if result["missing_manifest_count"]:
        print(f"active manifests missing -> {result['missing_manifest_count']}")
    return 0


def command_source_media_audit(context: Context, args: argparse.Namespace) -> int:
    report = run_source_control_media_audit(
        context,
        output_path=Path(args.output) if args.output else None,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"source media audit -> {report['report_path']}")
        print(f"errors: {report['error_count']}")
        for issue in report["errors"][:12]:
            print(f"ERROR {issue['code']}: {issue['message']} ({issue.get('path', '')})")
        if report["error_count"] > 12:
            print(f"... {report['error_count'] - 12} more errors in report")
    return 0 if report["ok"] else 1


def command_source_media_install_hooks(context: Context, args: argparse.Namespace) -> int:
    result = install_source_media_pre_commit_hooks(context)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"source media pre-commit hooks installed -> {result['installed_count']}")
        for repo in result["repositories"]:
            if repo.get("installed"):
                print(f"installed {repo['name']} -> {repo['hook_path']}")
                if repo.get("previous_hook_preserved"):
                    print(f"preserved previous {repo['name']} hook -> {repo['previous_hook_path']}")
            else:
                print(f"skipped {repo['name']} -> {repo.get('skipped_reason', 'unknown')}")
    return 0


def inbox_helper_path() -> Path:
    return ROOT_DIR.parent / "Inbox_CascadeEffects" / "bin" / "ce-inbox"


def _run_inbox_cli(command: list[str]) -> int:
    helper = inbox_helper_path()
    if not helper.exists():
        raise SystemExit(f"Inbox helper is missing: {helper}")
    if not os.access(helper, os.X_OK):
        raise SystemExit(f"Inbox helper is not executable: {helper}")
    completed = subprocess.run([str(helper), *command], check=False)
    return int(completed.returncode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ce-orchestrate")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor")
    subparsers.add_parser("board")
    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_target = bootstrap_parser.add_mutually_exclusive_group(required=True)
    bootstrap_target.add_argument("--episode")
    bootstrap_target.add_argument("--all", action="store_true", dest="all")
    bootstrap_parser.add_argument("--scene-archetype")
    bootstrap_parser.add_argument("--pillar")
    bootstrap_parser.add_argument("--skip-remote-review", action="store_true")
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--json", action="store_true")

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("episode_id")

    for name in ("sync", "validate"):
        command = subparsers.add_parser(name)
        command.add_argument("episode_id", nargs="?")
        command.add_argument("--all", action="store_true", dest="all")

    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("episode_id")

    brief_parser = subparsers.add_parser("brief")
    brief_parser.add_argument("episode_id")
    brief_parser.add_argument("lane")

    publish_check_parser = subparsers.add_parser("publish-check")
    publish_check_parser.add_argument("episode_id")

    publish_prepare_parser = subparsers.add_parser("publish-prepare")
    publish_prepare_parser.add_argument("episode_id")

    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("episode_id")
    publish_parser.add_argument("--target", choices=("youtube", "podcast", "all"), default="all")
    publish_parser.add_argument("--dry-run", action="store_true")

    publish_status_parser = subparsers.add_parser("publish-status")
    publish_status_parser.add_argument("episode_id")

    publish_package_check_parser = subparsers.add_parser("publish-package-check")
    publish_package_check_parser.add_argument("manifest_path")

    publish_package_upload_parser = subparsers.add_parser("publish-package-upload")
    publish_package_upload_parser.add_argument("manifest_path")
    publish_package_upload_parser.add_argument("--privacy", default="unlisted", choices=("private", "unlisted", "public"))

    publish_package_status_parser = subparsers.add_parser("publish-package-status")
    publish_package_status_parser.add_argument("receipt_or_video_id")

    publish_package_update_title_parser = subparsers.add_parser("publish-package-update-title")
    publish_package_update_title_parser.add_argument("receipt_or_video_id")
    publish_package_update_title_parser.add_argument("--title", required=True)

    publish_package_delete_parser = subparsers.add_parser("publish-package-delete")
    publish_package_delete_parser.add_argument("receipt_or_video_id")
    publish_package_delete_parser.add_argument("--confirm-video-id", required=True)

    render_motion_parser = subparsers.add_parser("render-motion")
    render_motion_parser.add_argument("episode_id")
    render_motion_parser.add_argument("motion_item_id")

    render_contact_sheet_parser = subparsers.add_parser("render-contact-sheet")
    render_contact_sheet_parser.add_argument("episode_id")

    process_research_sources_parser = subparsers.add_parser("process-research-sources")
    process_research_sources_parser.add_argument("episode_id")

    promote_motion_parser = subparsers.add_parser("promote-motion")
    promote_motion_parser.add_argument("episode_id")
    promote_motion_parser.add_argument("motion_item_id")
    promote_motion_parser.add_argument("--video", required=True)

    promote_audio_parser = subparsers.add_parser("promote-audio")
    promote_audio_parser.add_argument("episode_id")

    shorts_audio_audit_parser = subparsers.add_parser("shorts-audio-audit")
    shorts_audio_audit_parser.add_argument("--json", action="store_true")
    shorts_audio_audit_parser.add_argument("--output")
    shorts_audio_audit_parser.add_argument("--no-historical-annotations", action="store_true")

    shorts_audio_annotations_parser = subparsers.add_parser("shorts-audio-annotate-historical-proofs")
    shorts_audio_annotations_parser.add_argument("--output")

    shorts_audio_sync_parser = subparsers.add_parser("shorts-audio-sync-lane")
    shorts_audio_sync_parser.add_argument("lane")
    shorts_audio_sync_parser.add_argument("--no-update-manifests", action="store_true")

    source_media_audit_parser = subparsers.add_parser("source-media-audit")
    source_media_audit_parser.add_argument("--json", action="store_true")
    source_media_audit_parser.add_argument("--output")

    source_media_install_hooks_parser = subparsers.add_parser("source-media-install-hooks")
    source_media_install_hooks_parser.add_argument("--json", action="store_true")

    assemble_parser = subparsers.add_parser("assemble")
    assemble_parser.add_argument("episode_id")

    set_scene_archetype_parser = subparsers.add_parser("set-scene-archetype")
    set_scene_archetype_parser.add_argument("episode_id")
    set_scene_archetype_parser.add_argument("scene_item_id")
    set_scene_archetype_parser.add_argument("archetype_id")

    render_scene_parser = subparsers.add_parser("render-scene")
    render_scene_parser.add_argument("episode_id")
    render_scene_parser.add_argument("scene_item_id")

    finalize_scene_parser = subparsers.add_parser("finalize-scene")
    finalize_scene_parser.add_argument("episode_id")
    finalize_scene_parser.add_argument("scene_item_id")

    promote_scene_parser = subparsers.add_parser("promote-scene")
    promote_scene_parser.add_argument("episode_id")
    promote_scene_parser.add_argument("scene_item_id")
    promote_scene_parser.add_argument("--asset", required=True)

    render_packaging_parser = subparsers.add_parser("render-packaging")
    render_packaging_parser.add_argument("episode_id")
    render_packaging_parser.add_argument("item_id")

    finalize_packaging_parser = subparsers.add_parser("finalize-packaging")
    finalize_packaging_parser.add_argument("episode_id")
    finalize_packaging_parser.add_argument("item_id")

    promote_packaging_parser = subparsers.add_parser("promote-packaging")
    promote_packaging_parser.add_argument("episode_id")
    promote_packaging_parser.add_argument("item_id")
    promote_packaging_parser.add_argument("--asset", required=True)

    review_inbox_parser = subparsers.add_parser("review-inbox")
    review_inbox_parser.add_argument("--json", action="store_true")

    review_action_parser = subparsers.add_parser("review-action")
    review_action_parser.add_argument("episode_id")
    review_action_parser.add_argument("gate_type")
    review_action_parser.add_argument("item_id", nargs="?")
    review_action_parser.add_argument("--decision", required=True, choices=("approve", "reject"))
    review_action_parser.add_argument("--reviewer")
    review_action_parser.add_argument("--notes")
    review_action_parser.add_argument("--tag", action="append", default=[])

    review_server_parser = subparsers.add_parser("review-server")
    review_server_parser.add_argument("--host", default="127.0.0.1")
    review_server_parser.add_argument("--port", default=8765, type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    context = build_context()
    command_map = {
        "doctor": command_doctor,
        "board": command_board,
        "bootstrap": command_bootstrap,
        "report": command_report,
        "show": command_show,
        "sync": command_sync,
        "validate": command_validate,
        "next": command_next,
        "brief": command_brief,
        "publish-check": command_publish_check,
        "publish-prepare": command_publish_prepare,
        "publish": command_publish,
        "publish-status": command_publish_status,
        "publish-package-check": command_publish_package_check,
        "publish-package-upload": command_publish_package_upload,
        "publish-package-status": command_publish_package_status,
        "publish-package-update-title": command_publish_package_update_title,
        "publish-package-delete": command_publish_package_delete,
        "set-scene-archetype": command_set_scene_archetype,
        "render-scene": command_render_scene,
        "finalize-scene": command_finalize_scene,
        "promote-scene": command_promote_scene,
        "render-packaging": command_render_packaging,
        "finalize-packaging": command_finalize_packaging,
        "promote-packaging": command_promote_packaging,
        "render-motion": command_render_motion,
        "render-contact-sheet": command_render_contact_sheet,
        "process-research-sources": command_process_research_sources,
        "promote-motion": command_promote_motion,
        "promote-audio": command_promote_audio,
        "shorts-audio-audit": command_shorts_audio_audit,
        "shorts-audio-annotate-historical-proofs": command_shorts_audio_annotate_historical_proofs,
        "shorts-audio-sync-lane": command_shorts_audio_sync_lane,
        "source-media-audit": command_source_media_audit,
        "source-media-install-hooks": command_source_media_install_hooks,
        "assemble": command_assemble,
        "review-inbox": command_review_inbox,
        "review-action": command_review_action,
        "review-server": command_review_server,
    }
    return command_map[args.command](context, args)


__all__ = [
    "ROOT_DIR",
    "Context",
    "build_bootstrap_manifest",
    "build_context",
    "build_production_report",
    "build_parser",
    "command_assemble",
    "command_render_contact_sheet",
    "command_promote_audio",
    "command_publish_package_check",
    "command_publish_package_upload",
    "command_publish_package_status",
    "command_publish_package_delete",
    "command_shorts_audio_audit",
    "command_shorts_audio_annotate_historical_proofs",
    "command_shorts_audio_sync_lane",
    "command_source_media_audit",
    "command_source_media_install_hooks",
    "derive_episode_state",
    "format_production_report",
    "format_state_summary",
    "load_episode_manifest",
    "main",
    "print_board",
    "render_brief",
]


if __name__ == "__main__":
    raise SystemExit(main())
