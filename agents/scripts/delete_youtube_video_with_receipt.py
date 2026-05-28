#!/usr/bin/env python3
"""Delete a YouTube video and write a local receipt."""

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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def dataclass_or_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


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


def require_contract_youtube_action(*, receipt_path_value: str, confirmed: bool, action: str) -> dict[str, Any]:
    require(confirmed, f"--confirm-contract-youtube-action is required before {action}")
    require(bool(str(receipt_path_value).strip()), f"--production-contract-receipt is required before {action}")
    receipt_path = Path(receipt_path_value).expanduser().resolve()
    require(receipt_path.is_file(), f"Production contract receipt does not exist: {receipt_path}")
    receipt = read_json(receipt_path)
    require(receipt.get("ok") is True, f"Production contract receipt is not passing: {receipt_path}")
    require(receipt.get("youtube_action_allowed") is True, f"Production contract receipt does not allow {action}: {receipt_path}")
    requested = str(receipt.get("youtube_action_requested", "")).strip()
    require(requested == action, f"Production contract receipt action mismatch: {requested or '(missing)'} != {action}")
    return {"path": str(receipt_path), "sha256": sha256_file(receipt_path), "receipt": receipt}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--replacement-video-id", default="")
    parser.add_argument("--replacement-video-url", default="")
    parser.add_argument("--config-dir", default=str(YOUTUBE_CONFIG_DIR))
    parser.add_argument("--receipt-dir", default=str(EPISODES_ROOT / "youtube_deletion_receipts"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--production-contract-receipt", default="")
    parser.add_argument("--confirm-contract-youtube-action", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(REPO_ROOT))
    from orchestration.publish import _verify_authenticated_channel, build_youtube_package_publisher

    publisher = build_youtube_package_publisher(config_dir=args.config_dir)
    channel = _verify_authenticated_channel(publisher)
    video_id = str(args.video_id).strip()
    if not video_id:
        raise RuntimeError("--video-id is required")
    status_before = dataclass_or_value(publisher.get_video_status(video_id))
    delete_result: dict[str, Any] | None = None
    contract_receipt: dict[str, Any] | None = None
    if not args.dry_run:
        contract_receipt = require_contract_youtube_action(
            receipt_path_value=args.production_contract_receipt,
            confirmed=args.confirm_contract_youtube_action,
            action="delete_defective_unlisted_upload",
        )
        delete_result = dataclass_or_value(publisher.delete_video(video_id))
    receipt = {
        "receipt_type": "youtube_video_delete",
        "created_at": utc_now(),
        "episode_id": args.episode_id,
        "video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "reason": args.reason,
        "replacement_video_id": args.replacement_video_id,
        "replacement_video_url": args.replacement_video_url,
        "channel": channel,
        "status_before_delete": status_before,
        "delete_result": delete_result,
        "dry_run": args.dry_run,
        "public_release": "manual_youtube_studio_only",
        "read": "pass_defective_unlisted_upload_deleted_after_replacement_verified" if not args.dry_run else "dry_run_no_delete",
    }
    if contract_receipt:
        receipt["production_contract_receipt"] = {
            "path": contract_receipt["path"],
            "sha256": contract_receipt["sha256"],
            "contract_id": contract_receipt["receipt"].get("contract_id"),
            "intent": contract_receipt["receipt"].get("intent"),
            "youtube_action_requested": contract_receipt["receipt"].get("youtube_action_requested"),
            "youtube_action_allowed": contract_receipt["receipt"].get("youtube_action_allowed"),
        }
    receipt_path = Path(args.receipt_dir) / f"{args.episode_id}_youtube_delete_{video_id}_{stamp()}.json"
    write_json(receipt_path, receipt)
    print(json.dumps({"receipt_path": str(receipt_path), **receipt}, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
