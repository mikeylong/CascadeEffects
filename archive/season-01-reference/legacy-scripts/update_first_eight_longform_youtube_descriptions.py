#!/usr/bin/env python3
"""Update existing first-eight long-form YouTube descriptions from package metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")
YOUTUBE_CONFIG_DIR = Path("/Users/mike/.config/cascade-effects/youtube")

CURRENT_LONGFORM_VIDEO_IDS = {
    "hyatt-regency": "0HHham1eYsI",
    "tacoma-narrows": "KwwhWaH4PrI",
    "piltdown-man": "vu3hOJJAiAM",
    "titanic": "ikBaThpggE4",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON file must contain an object: {path}")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataclass_or_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def normalize_tags(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        return []
    output: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        text = str(tag).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def resolve_maybe_relative(base: Path, value: Any) -> Path:
    candidate = Path(str(value or "").strip())
    if candidate.is_absolute():
        return candidate
    return base / candidate


def require_contract_youtube_action(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    explicit_receipt_path: str,
    confirmed: bool,
    action: str,
) -> dict[str, Any]:
    require(confirmed, f"--confirm-contract-youtube-action is required before {action}")
    receipt_value = explicit_receipt_path or manifest.get("production_contract_action_receipt", {}).get("path", "")
    if not receipt_value:
        receipt_value = manifest.get("production_contract_receipt", {}).get("path", "")
    require(bool(str(receipt_value).strip()), f"Missing production contract receipt for {action}: {manifest_path}")
    receipt_path = resolve_maybe_relative(manifest_path.parent, receipt_value)
    require(receipt_path.is_file(), f"Production contract receipt does not exist: {receipt_path}")
    receipt = read_json(receipt_path)
    require(receipt.get("ok") is True, f"Production contract receipt is not passing: {receipt_path}")
    require(receipt.get("youtube_action_allowed") is True, f"Production contract receipt does not allow {action}: {receipt_path}")
    requested = str(receipt.get("youtube_action_requested", "")).strip()
    require(requested == action, f"Production contract receipt action mismatch: {requested or '(missing)'} != {action}")
    return {"path": str(receipt_path), "sha256": sha256_file(receipt_path), "receipt": receipt}


def youtube_description(metadata: dict[str, Any]) -> str:
    description = str(metadata.get("description", "")).strip()
    lines = ["Chapters:"]
    chapters = metadata.get("chapters")
    if isinstance(chapters, list):
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            timestamp = str(chapter.get("time") or chapter.get("timestamp") or "").strip()
            label = str(chapter.get("label") or chapter.get("title") or "").strip()
            if timestamp and label:
                lines.append(f"{timestamp} {label}")
    if len(lines) <= 1:
        raise RuntimeError("Metadata does not contain YouTube chapter lines.")
    description = f"{description}\n\n" + "\n".join(lines)
    hashtags = metadata.get("hashtags")
    if isinstance(hashtags, list):
        tag_line = " ".join(str(item).strip() for item in hashtags if str(item).strip())
        if tag_line:
            description = f"{description}\n\n{tag_line}"
    return description.strip()


def selected_package_manifests(summary_path: Path, only: set[str]) -> dict[str, Path]:
    summary = read_json(summary_path)
    packages = summary.get("packages")
    if not isinstance(packages, list):
        raise RuntimeError(f"Summary lacks packages list: {summary_path}")
    selected: dict[str, Path] = {}
    for item in packages:
        if not isinstance(item, dict):
            continue
        episode_id = str(item.get("episode_id", "")).strip()
        if only and episode_id not in only:
            continue
        manifest_path = Path(str(item.get("manifest_path", "")).strip())
        if episode_id and manifest_path.is_file():
            selected[episode_id] = manifest_path
    if not selected:
        raise RuntimeError("No package manifests selected.")
    return selected


def update_one(
    *,
    publisher: Any,
    episode_id: str,
    manifest_path: Path,
    video_id: str,
    run_stamp: str,
    dry_run: bool,
    production_contract_receipt: str,
    confirm_contract_youtube_action: bool,
) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    metadata = manifest.get("youtube_metadata", {}) if isinstance(manifest.get("youtube_metadata"), dict) else {}
    chapters = metadata.get("chapters")
    chapter_count = len(chapters) if isinstance(chapters, list) else 0
    if episode_id in CURRENT_LONGFORM_VIDEO_IDS and chapter_count < 4:
        raise RuntimeError(f"{episode_id} still has only {chapter_count} metadata chapters; refusing YouTube update.")
    description = youtube_description(metadata)
    payload = {
        "episode_id": episode_id,
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "manifest_path": str(manifest_path),
        "chapter_count": chapter_count,
        "description_text": description,
        "dry_run": dry_run,
    }
    if dry_run:
        return {"status": "dry_run_ready", **payload}
    contract_receipt = require_contract_youtube_action(
        manifest=manifest,
        manifest_path=manifest_path,
        explicit_receipt_path=production_contract_receipt,
        confirmed=confirm_contract_youtube_action,
        action="description_update",
    )
    result = publisher.update_video_snippet(
        video_id,
        title=str(metadata.get("title", "")).strip() or None,
        description=description,
        tags=normalize_tags(metadata.get("tags")),
    )
    result_payload = dataclass_or_value(result)
    receipt = {
        "receipt_type": "youtube_longform_description_update",
        "created_at": utc_now(),
        "episode_id": episode_id,
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "source_publish_readiness_manifest_path": str(manifest_path),
        "chapter_count": chapter_count,
        "read": "pass_youtube_description_updated_with_full_chapter_block",
        "public_release": "manual_youtube_studio_only",
        "production_contract_receipt": {
            "path": contract_receipt["path"],
            "sha256": contract_receipt["sha256"],
            "contract_id": contract_receipt["receipt"].get("contract_id"),
            "intent": contract_receipt["receipt"].get("intent"),
            "youtube_action_requested": contract_receipt["receipt"].get("youtube_action_requested"),
            "youtube_action_allowed": contract_receipt["receipt"].get("youtube_action_allowed"),
        },
        "youtube": result_payload,
    }
    receipt_path = manifest_path.parent / f"youtube_description_update_receipt_{run_stamp}.json"
    write_json(receipt_path, receipt)
    return {"status": "updated", "receipt_path": str(receipt_path), **payload}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(EPISODES_ROOT / "first_eight_longform_publish_readiness_packages_latest.json"))
    parser.add_argument("--config-dir", default=str(YOUTUBE_CONFIG_DIR))
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--production-contract-receipt", default="")
    parser.add_argument("--confirm-contract-youtube-action", action="store_true")
    args = parser.parse_args()

    only = {item.strip() for item in args.only if item.strip()}
    selected = selected_package_manifests(Path(args.summary), only)
    run_stamp = stamp()
    publisher = None
    channel: dict[str, Any] = {}
    if not args.dry_run:
        sys.path.insert(0, str(REPO_ROOT))
        from orchestration.publish import _verify_authenticated_channel, build_youtube_package_publisher

        publisher = build_youtube_package_publisher(config_dir=args.config_dir)
        channel = _verify_authenticated_channel(publisher)
        print(f"[youtube] authenticated channel: {channel.get('title')} ({channel.get('channel_id')})", flush=True)

    results: list[dict[str, Any]] = []
    for episode_id, manifest_path in selected.items():
        video_id = CURRENT_LONGFORM_VIDEO_IDS.get(episode_id, "")
        if not video_id:
            results.append({"episode_id": episode_id, "status": "skipped_no_current_video_id", "manifest_path": str(manifest_path)})
            continue
        print(f"[youtube] {episode_id}: updating description on {video_id}", flush=True)
        results.append(
            update_one(
                publisher=publisher,
                episode_id=episode_id,
                manifest_path=manifest_path,
                video_id=video_id,
                run_stamp=run_stamp,
                dry_run=args.dry_run,
                production_contract_receipt=args.production_contract_receipt,
                confirm_contract_youtube_action=args.confirm_contract_youtube_action,
            )
        )

    ok = all(item.get("status") in {"updated", "dry_run_ready", "skipped_no_current_video_id"} for item in results)
    aggregate = {
        "ok": ok,
        "created_at": utc_now(),
        "stamp": run_stamp,
        "summary_path": str(args.summary),
        "public_release": "manual_youtube_studio_only",
        "channel": channel,
        "results": results,
    }
    aggregate_path = EPISODES_ROOT / f"first_eight_longform_youtube_description_updates_{run_stamp}.json"
    write_json(aggregate_path, aggregate)
    write_json(EPISODES_ROOT / "first_eight_longform_youtube_description_updates_latest.json", aggregate)
    print(json.dumps({"aggregate_path": str(aggregate_path), **aggregate}, indent=2, sort_keys=True), flush=True)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
