#!/usr/bin/env python3
"""Upload a kept channel intro/trailer package as an unlisted YouTube review.

This lane intentionally does not replace the channel trailer, publish publicly,
schedule visibility, or mutate YouTube Studio channel customization. It only
creates a new unlisted review upload after the channel-trailer contract says the
`unlisted_review_upload` action is allowed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
YOUTUBE_CONFIG_DIR = Path("/Users/mike/.config/cascade-effects/youtube")
ACTION = "unlisted_review_upload"

DEFAULT_MANIFEST = Path(
    "/Users/mike/Episodes_CascadeEffects/Channel_Trailer/"
    "channel_intro_pressure_bends_original_format_tacoma_piltdown_swap_latest.json"
)

POST_UPLOAD_BLOCKERS = [
    "Review YouTube Studio copyright and Content ID checks before public release.",
    "Configure the uploaded video as the channel trailer manually in YouTube Studio only after review.",
    "Public, scheduled, or channel-trailer replacement actions are not part of this lane.",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), f"JSON file must contain an object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def dataclass_or_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def resolve_manifest(path: Path) -> Path:
    payload = read_json(path)
    if "manifest" in payload and Path(str(payload["manifest"])).is_file():
        return Path(str(payload["manifest"]))
    if "manifest_path" in payload and Path(str(payload["manifest_path"])).is_file():
        return Path(str(payload["manifest_path"]))
    return path


def resolve_path(base: Path, value: Any) -> Path:
    candidate = Path(str(value or "").strip())
    if candidate.is_absolute():
        return candidate
    return base / candidate


def final_mp4_path(manifest: dict[str, Any], manifest_path: Path) -> Path:
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
    media_probe = manifest.get("media_probe") if isinstance(manifest.get("media_probe"), dict) else {}
    for value in (outputs.get("final_mp4"), media_probe.get("path")):
        if value:
            path = resolve_path(manifest_path.parent, value)
            if path.is_file():
                return path
    raise RuntimeError(f"Could not resolve final MP4 from {manifest_path}")


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def ffprobe(path: Path) -> dict[str, Any]:
    return run_json(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate",
            "-show_entries",
            "stream=index,codec_type,codec_name,width,height,avg_frame_rate,duration,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )


def require_media_shape(mp4: Path) -> dict[str, Any]:
    probe = ffprobe(mp4)
    streams = probe.get("streams") if isinstance(probe.get("streams"), list) else []
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    require(video.get("codec_name") == "h264", "Channel intro/trailer upload requires H.264 video.")
    require(video.get("width") == 1920 and video.get("height") == 1080, "Channel intro/trailer upload requires 1920x1080 video.")
    require(video.get("avg_frame_rate") in {"24/1", "24000/1000"}, "Channel intro/trailer upload requires 24fps video.")
    require(audio.get("codec_name") == "aac", "Channel intro/trailer upload requires AAC audio.")
    require(int(audio.get("channels") or 0) == 2, "Channel intro/trailer upload requires stereo audio.")
    return probe


def contract_action_receipt(manifest: dict[str, Any], manifest_path: Path, explicit_receipt: str) -> dict[str, Any]:
    receipt_value = explicit_receipt
    if not receipt_value:
        action_receipt = manifest.get("production_contract_action_receipt")
        if isinstance(action_receipt, dict):
            receipt_value = str(action_receipt.get("path") or "").strip()
    if not receipt_value:
        action_receipt = manifest.get("production_contract_receipt")
        if isinstance(action_receipt, dict):
            receipt_value = str(action_receipt.get("path") or "").strip()
    require(bool(receipt_value), f"Missing production contract action receipt for {ACTION}: {manifest_path}")
    receipt_path = resolve_path(manifest_path.parent, receipt_value)
    require(receipt_path.is_file(), f"Production contract action receipt does not exist: {receipt_path}")
    receipt = read_json(receipt_path)
    require(receipt.get("ok") is True, f"Production contract action receipt is not passing: {receipt_path}")
    require(receipt.get("youtube_action_requested") == ACTION, f"Receipt action is not {ACTION}: {receipt_path}")
    require(receipt.get("youtube_action_allowed") is True, f"Receipt does not allow {ACTION}: {receipt_path}")
    return {"path": str(receipt_path), "sha256": sha256_file(receipt_path), "receipt": receipt}


def build_upload_payload(manifest: dict[str, Any], manifest_path: Path, mp4: Path, args: argparse.Namespace) -> dict[str, Any]:
    metadata = manifest.get("youtube_upload_metadata") if isinstance(manifest.get("youtube_upload_metadata"), dict) else {}
    artifact_id = str(manifest.get("artifact_id") or manifest_path.parent.name).strip()
    title = str(args.title or metadata.get("title") or "Cascade of Effects Channel Intro - Unlisted Review").strip()
    review_html = str((manifest.get("outputs") or {}).get("review_html") or "").strip()
    description = str(args.description or metadata.get("description") or "").strip()
    if not description:
        description = "\n".join(
            [
                "Unlisted review upload for a Cascade of Effects channel intro/trailer candidate.",
                f"Source package: {artifact_id}",
                f"Local review HTML: {review_html or '(not recorded)'}",
                "Channel trailer replacement and public visibility remain manual YouTube Studio actions.",
            ]
        )
    tags = metadata.get("tags") if isinstance(metadata.get("tags"), list) else []
    if not tags:
        tags = ["Cascade of Effects", "channel intro", "channel trailer", "review"]
    return {
        "video_path": str(mp4),
        "title": title,
        "description_text": description,
        "tags": [str(tag) for tag in tags],
        "privacy": "unlisted",
        "category_id": str(metadata.get("category_id") or "27"),
        "default_language": str(metadata.get("default_language") or "en"),
        "default_audio_language": str(metadata.get("default_audio_language") or "en"),
        "self_declared_made_for_kids": False,
        "notify_subscribers": False,
        "ignore_thumbnail_errors": True,
    }


def write_preflight(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    mp4: Path,
    media_probe: dict[str, Any],
    receipt: dict[str, Any],
    payload: dict[str, Any],
    upload_stamp: str,
    dry_run: bool,
) -> Path:
    preflight = {
        "receipt_type": "channel_trailer_unlisted_review_upload_preflight",
        "created_at": utc_now(),
        "dry_run": dry_run,
        "action": ACTION,
        "source_manifest": artifact(manifest_path),
        "source_mp4": artifact(mp4),
        "production_contract_action_receipt": {"path": receipt["path"], "sha256": receipt["sha256"]},
        "media_probe": media_probe,
        "youtube_payload_preview": {
            "title": payload["title"],
            "privacy": payload["privacy"],
            "category_id": payload["category_id"],
            "notify_subscribers": payload["notify_subscribers"],
        },
        "reads": {
            "contract_youtube_action_read": "pass_contract_allows_unlisted_review_upload",
            "format_read": "pass_1920x1080_24fps_h264_stereo_aac",
            "channel_trailer_replacement_read": "pass_not_performed_manual_youtube_studio_only",
            "public_visibility_read": "pass_not_performed_manual_youtube_studio_only",
        },
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
        "source_artifact_id": manifest.get("artifact_id"),
    }
    path = manifest_path.parent / "qa" / f"channel_trailer_unlisted_review_upload_preflight_{upload_stamp}.json"
    write_json(path, preflight)
    shutil.copyfile(path, manifest_path.parent / "qa" / "channel_trailer_unlisted_review_upload_preflight_latest.json")
    return path


def update_manifest_after_upload(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    upload_receipt_path: Path,
    result: Any,
    channel: dict[str, Any],
    status: dict[str, Any],
) -> None:
    updated = dict(manifest)
    upload = {
        "action": ACTION,
        "video_id": result.video_id,
        "video_url": result.video_url,
        "privacy": "unlisted",
        "channel_id": channel.get("channel_id"),
        "channel_title": channel.get("title"),
        "published_at": result.published_at,
        "status": status,
        "receipt_path": str(upload_receipt_path),
        "receipt_sha256": sha256_file(upload_receipt_path),
    }
    updated["youtube_unlisted_review"] = upload
    updated["youtube_uploaded"] = True
    updated["youtube_channel_trailer_replaced"] = False
    qa = updated.get("qa") if isinstance(updated.get("qa"), dict) else {}
    qa["youtube_uploaded"] = True
    qa["youtube_channel_trailer_replaced"] = False
    qa["youtube_unlisted_review_upload_read"] = "pass_new_unlisted_review_upload_created"
    updated["qa"] = qa
    reads = updated.get("reads") if isinstance(updated.get("reads"), dict) else {}
    reads["youtube_action_read"] = "pass_unlisted_review_upload_created_channel_replacement_manual_only"
    reads["youtube_unlisted_review_upload_read"] = "pass_new_unlisted_review_upload_created"
    reads["youtube_channel_trailer_replacement_read"] = "pass_not_performed_manual_youtube_studio_only"
    updated["reads"] = reads
    updated["youtube_action_lane"] = dict(updated.get("youtube_action_lane") or {})
    updated["youtube_action_lane"]["action_performed"] = True
    write_json(manifest_path, updated)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--config-dir", default=str(YOUTUBE_CONFIG_DIR))
    parser.add_argument("--production-contract-receipt", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-contract-youtube-action", action="store_true")
    parser.add_argument("--poll-status", action="store_true")
    args = parser.parse_args()

    manifest_path = resolve_manifest(Path(args.manifest))
    manifest = read_json(manifest_path)
    mp4 = final_mp4_path(manifest, manifest_path)
    media_probe = require_media_shape(mp4)
    receipt = contract_action_receipt(manifest, manifest_path, args.production_contract_receipt)
    payload = build_upload_payload(manifest, manifest_path, mp4, args)
    upload_stamp = stamp()
    preflight_path = write_preflight(
        manifest_path=manifest_path,
        manifest=manifest,
        mp4=mp4,
        media_probe=media_probe,
        receipt=receipt,
        payload=payload,
        upload_stamp=upload_stamp,
        dry_run=args.dry_run,
    )
    print(f"[preflight] wrote {preflight_path}", flush=True)

    if args.dry_run:
        print("[dry-run] ready for contract-gated unlisted review upload; no YouTube action performed", flush=True)
        return

    require(args.confirm_contract_youtube_action, "--confirm-contract-youtube-action is required before upload")
    sys.path.insert(0, str(REPO_ROOT))
    from orchestration.publish import _verify_authenticated_channel, build_youtube_package_publisher

    publisher = build_youtube_package_publisher(config_dir=args.config_dir)
    channel = _verify_authenticated_channel(publisher)
    print(f"[youtube] authenticated channel: {channel.get('title')} ({channel.get('channel_id')})", flush=True)
    print("[youtube] uploading channel intro/trailer as unlisted review", flush=True)
    result = publisher.publish_video(payload)
    print(f"[youtube] uploaded {result.video_id}", flush=True)
    status = {}
    if args.poll_status:
        status = dataclass_or_value(publisher.get_video_status(result.video_id))

    upload_receipt = {
        "receipt_type": "youtube_channel_trailer_unlisted_review_upload",
        "created_at": utc_now(),
        "action": ACTION,
        "source_manifest": artifact(manifest_path),
        "source_mp4": artifact(mp4),
        "production_contract_action_receipt": {"path": receipt["path"], "sha256": receipt["sha256"]},
        "youtube": {
            "video_id": result.video_id,
            "video_url": result.video_url,
            "channel_id": channel.get("channel_id"),
            "channel_title": channel.get("title"),
            "published_at": result.published_at,
            "status": status,
        },
        "privacy": "unlisted",
        "public_release": "manual_youtube_studio_only",
        "channel_trailer_replacement": "manual_youtube_studio_only",
        "post_upload_blockers": POST_UPLOAD_BLOCKERS,
        "reads": {
            "youtube_unlisted_review_upload_read": "pass_new_unlisted_review_upload_created",
            "youtube_unlisted_review_privacy_read": "pass_privacy_unlisted",
            "youtube_channel_trailer_replacement_read": "pass_not_performed_manual_youtube_studio_only",
            "youtube_public_release_read": "pass_not_performed_manual_youtube_studio_only",
        },
    }
    upload_receipt_path = manifest_path.parent / "qa" / f"youtube_channel_trailer_unlisted_upload_receipt_{upload_stamp}.json"
    write_json(upload_receipt_path, upload_receipt)
    shutil.copyfile(upload_receipt_path, manifest_path.parent / "qa" / "youtube_channel_trailer_unlisted_upload_receipt_latest.json")
    update_manifest_after_upload(
        manifest_path=manifest_path,
        manifest=manifest,
        upload_receipt_path=upload_receipt_path,
        result=result,
        channel=channel,
        status=status,
    )
    print(f"[receipt] wrote {upload_receipt_path}", flush=True)


if __name__ == "__main__":
    main()
