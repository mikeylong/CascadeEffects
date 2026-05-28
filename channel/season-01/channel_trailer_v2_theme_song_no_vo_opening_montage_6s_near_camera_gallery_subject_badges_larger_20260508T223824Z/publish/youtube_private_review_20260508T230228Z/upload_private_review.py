#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/Users/mike/Agents_CascadeEffects")

from orchestration.publish import build_youtube_package_publisher


ROOT = Path(__file__).resolve().parent
PAYLOAD_PATH = ROOT / "youtube_private_upload_payload.json"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    if payload.get("privacy") != "private":
        raise SystemExit("This helper only supports private review uploads.")

    youtube = build_youtube_package_publisher()
    channel = youtube.get_authenticated_channel()
    result = youtube.publish_video(payload)
    status = youtube.get_video_status(result.video_id)
    receipt = {
        "receipt_type": "youtube_channel_trailer_private_upload",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "payload_path": str(PAYLOAD_PATH),
        "package_dir": str(ROOT),
        "privacy": "private",
        "youtube": {
            "video_id": result.video_id,
            "video_url": result.video_url,
            "channel_id": channel.get("channel_id", ""),
            "channel_title": channel.get("title", ""),
            "published_at": result.published_at,
            "status": {
                "privacy_status": status.privacy_status,
                "upload_status": status.upload_status,
                "processing_status": status.processing_status,
                "channel_id": status.channel_id,
                "title": status.title,
            },
        },
        "thumbnail": {
            "path": payload.get("thumbnail_path", ""),
            "status": result.thumbnail_status,
            "error": result.thumbnail_error,
        },
        "post_upload_blockers": [
            "Review YouTube Studio copyright and Content ID checks before public release.",
            "Confirm altered-content disclosure in YouTube Studio.",
            "Confirm audience, category, title, description, tags, thumbnail, end screen, and visibility.",
            "Set as channel trailer in YouTube Studio if this private review is approved.",
            "Public release remains manual in YouTube Studio.",
        ],
    }
    receipt_path = ROOT / f"youtube_channel_trailer_private_upload_receipt_{utc_stamp()}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(receipt_path)
    print(result.video_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
