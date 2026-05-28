#!/usr/bin/env python3
"""Upload the kept Therac-25 long-form publish-readiness package privately.

This is intentionally narrow: it uses the existing YouTube adapter, writes the
same audit artifacts as the Challenger long-form precedent, and never performs
public visibility changes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
PACKAGE_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/"
    "publish_readiness/therac25_publish_readiness_actual_outro_prelap_20260518T182800Z"
)
PUBLISH_MANIFEST = PACKAGE_ROOT / "publish_readiness_manifest.json"
PROOF_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/"
    "rough_assembly/therac_living_cover_challenger_music_html_rough_proof_20260517T073904Z"
)
PROOF_MANIFEST = PROOF_ROOT / "rough_assembly_manifest.json"
PLAYER_HTML = PROOF_ROOT / "player.html"
AUDIO_MIX_MANIFEST = (
    PROOF_ROOT
    / "audio_repairs/actual_outro_prelap_20260518T182800Z/actual_outro_prelap_audio_mix_manifest.json"
)
FINAL_RENDER_MANIFEST = (
    PROOF_ROOT
    / "video_render/therac25_final_mp4_actual_outro_prelap_20260518T182800Z/render_manifest.json"
)
VALIDATOR = REPO_ROOT / "scripts/validate_living_cover_final_gate.mjs"
YOUTUBE_CONFIG_DIR = Path("/Users/mike/.config/cascade-effects/youtube")
YOUTUBE_THUMBNAIL_LIMIT_BYTES = 2_097_152
YOUTUBE_THUMBNAIL_DERIVATIVE = PACKAGE_ROOT / "assets/thumbnail/therac25_thumbnail_candidate_youtube_upload.jpg"


POST_UPLOAD_BLOCKERS = [
    "Review YouTube Studio copyright and Content ID checks before public release.",
    "Confirm altered-content disclosure in YouTube Studio for realistic generated or source-derived episode visuals.",
    "Verify uploaded captions or automatic captions in YouTube Studio so they do not conflict with burned-in rail captions.",
    "Configure final YouTube Studio end-screen elements for the baked titleless three-target end-screen geometry.",
    "Public visibility change remains manual and must not be performed by this upload step.",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON file must contain an object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dataclass_or_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def run_validator() -> dict[str, Any]:
    return run_json(
        [
            "node",
            str(VALIDATOR),
            "--proof-manifest",
            str(PROOF_MANIFEST),
            "--player",
            str(PLAYER_HTML),
            "--audio-mix",
            str(AUDIO_MIX_MANIFEST),
            "--final-manifest",
            str(FINAL_RENDER_MANIFEST),
            "--publish-readiness",
            str(PUBLISH_MANIFEST),
        ]
    )


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


def prepare_youtube_thumbnail(source: Path) -> Path:
    """Create a YouTube API-safe thumbnail derivative when the source is >2 MB."""
    if source.stat().st_size <= YOUTUBE_THUMBNAIL_LIMIT_BYTES:
        return source
    YOUTUBE_THUMBNAIL_DERIVATIVE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vf",
            "scale=1280:720",
            "-q:v",
            "3",
            str(YOUTUBE_THUMBNAIL_DERIVATIVE),
        ],
        check=True,
    )
    require(YOUTUBE_THUMBNAIL_DERIVATIVE.exists(), "YouTube thumbnail derivative was not created.")
    require(
        YOUTUBE_THUMBNAIL_DERIVATIVE.stat().st_size <= YOUTUBE_THUMBNAIL_LIMIT_BYTES,
        "YouTube thumbnail derivative is still larger than the 2 MB API limit.",
    )
    return YOUTUBE_THUMBNAIL_DERIVATIVE


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def normalize_tags(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        return []
    seen: set[str] = set()
    output: list[str] = []
    for tag in tags:
        text = str(tag).strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output


def upload_captions_srt(publisher: Any, video_id: str, caption_path: Path) -> dict[str, Any]:
    """Best-effort captions.insert call using the local force-ssl OAuth scope."""
    token = publisher.refresh_access_token()
    boundary = f"cascadeeffects-{stamp()}"
    metadata = {
        "snippet": {
            "videoId": video_id,
            "language": "en",
            "name": "English",
            "isDraft": False,
        }
    }
    caption_bytes = caption_path.read_bytes()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
            json.dumps(metadata).encode("utf-8"),
            b"\r\n",
            f"--{boundary}\r\n".encode("utf-8"),
            b"Content-Type: application/x-subrip\r\n\r\n",
            caption_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    params = urllib.parse.urlencode({"part": "snippet", "uploadType": "multipart"})
    request = urllib.request.Request(
        f"https://www.googleapis.com/upload/youtube/v3/captions?{params}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
            "Content-Length": str(len(body)),
            "User-Agent": "CascadeEffectsPublish/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8", errors="replace")
        payload = json.loads(raw) if raw else {}
        return {
            "status": "uploaded",
            "caption_id": str(payload.get("id", "")).strip(),
            "raw_response": payload,
        }
    except Exception as exc:  # noqa: BLE001 - nonfatal evidence capture
        return {
            "status": "failed_nonfatal",
            "error": str(exc),
            "caption_id": "",
            "raw_response": {},
        }


def verify_preflight(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    require(PUBLISH_MANIFEST.exists(), f"Missing publish readiness manifest: {PUBLISH_MANIFEST}")
    require(str(manifest.get("human_disposition", "")).strip() == "keep", "Publish readiness is not human-kept.")
    require(
        str(manifest.get("status", "")).strip()
        in {
            "publish_readiness_keep_pending_explicit_upload_authorization",
            "private_review_uploaded_public_release_blocked_pending_studio_checks",
        },
        f"Unexpected publish readiness status: {manifest.get('status')}",
    )
    locks = manifest.get("locks", {}) if isinstance(manifest.get("locks"), dict) else {}
    require(locks.get("publish_ready") is True, "Publish-ready lock is not true.")
    require(locks.get("public_release_ready") is False, "Public-release lock must remain false.")
    require(locks.get("may_youtube_action") is False, "may_youtube_action must be false before private-upload helper runs.")
    require(locks.get("public_visibility_change_enabled") is False, "Public visibility controls must remain disabled.")
    existing = manifest.get("youtube_private_review_upload")
    if isinstance(existing, dict) and existing.get("video_id") and not existing.get("superseded_do_not_publish"):
        raise RuntimeError(f"Active private review upload already exists: {existing.get('video_id')}")

    media = manifest.get("media", {}) if isinstance(manifest.get("media"), dict) else {}
    mp4 = Path(media.get("mp4", {}).get("path", ""))
    vtt = Path(media.get("vtt", {}).get("path", ""))
    srt = Path(media.get("srt", {}).get("path", ""))
    thumbnail = Path(media.get("thumbnail_candidate", {}).get("path", ""))
    for label, path in (("mp4", mp4), ("vtt", vtt), ("srt", srt), ("thumbnail", thumbnail)):
        require(path.exists(), f"Missing upload asset {label}: {path}")
    for key, path in (("mp4", mp4), ("vtt", vtt), ("srt", srt), ("thumbnail_candidate", thumbnail)):
        declared = media.get(key, {}).get("sha256")
        require(not declared or declared == sha256_file(path), f"Hash mismatch for {key}: {path}")

    validator = run_validator()
    require(validator.get("status") == "pass", f"Final gate validator did not pass: {validator}")
    upload_thumbnail = prepare_youtube_thumbnail(thumbnail)
    return {
        "mp4": mp4,
        "vtt": vtt,
        "srt": srt,
        "thumbnail": upload_thumbnail,
        "thumbnail_source": thumbnail,
    }, validator


def build_upload_manifest(
    manifest: dict[str, Any],
    assets: dict[str, Path],
    validator: dict[str, Any],
    upload_stamp: str,
) -> tuple[Path, dict[str, Any]]:
    copy_payload = manifest.get("metadata", {}).get("copy", {})
    require(isinstance(copy_payload, dict), "Missing metadata.copy block.")
    title = str(copy_payload.get("recommended_title", "")).strip()
    description = str(copy_payload.get("description", "")).strip()
    tags = normalize_tags(copy_payload.get("tags"))
    require(title, "Missing YouTube title.")
    require(description, "Missing YouTube description.")
    require(tags, "Missing YouTube tags.")
    probe = ffprobe(assets["mp4"])
    upload_manifest = {
        "created_at": utc_now(),
        "human_upload_approval_read": "pass_user_authorized_private_youtube_upload_for_therac25_2026_05_18",
        "target": "youtube_longform_private_review",
        "privacy": "private",
        "notify_subscribers": False,
        "public_release": "manual_youtube_studio_only",
        "source_publish_readiness_manifest_path": str(PUBLISH_MANIFEST),
        "source_publish_readiness_manifest_sha256": sha256_file(PUBLISH_MANIFEST),
        "final_gate_validator": validator,
        "known_post_upload_blockers": POST_UPLOAD_BLOCKERS,
        "upload_assets": {
            "video_path": str(assets["mp4"]),
            "video_sha256": sha256_file(assets["mp4"]),
            "caption_vtt_path": str(assets["vtt"]),
            "caption_vtt_sha256": sha256_file(assets["vtt"]),
            "caption_srt_path": str(assets["srt"]),
            "caption_srt_sha256": sha256_file(assets["srt"]),
            "thumbnail_path": str(assets["thumbnail"]),
            "thumbnail_sha256": sha256_file(assets["thumbnail"]),
            "thumbnail_source_path": str(assets["thumbnail_source"]),
            "thumbnail_source_sha256": sha256_file(assets["thumbnail_source"]),
            "probe": probe,
        },
        "youtube_metadata": {
            "title": title,
            "description": description,
            "tags": tags,
            "category_id": "27",
            "default_language": "en",
            "default_audio_language": "en",
            "self_declared_made_for_kids": False,
        },
    }
    path = PACKAGE_ROOT / f"youtube_longform_private_upload_manifest_{upload_stamp}.json"
    write_json(path, upload_manifest)
    return path, upload_manifest


def status_payload(status: Any) -> dict[str, Any]:
    payload = dataclass_or_value(status)
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected status response.")
    return payload


def poll_status(publisher: Any, video_id: str, upload_stamp: str) -> tuple[Path, dict[str, Any]]:
    latest: dict[str, Any] = {}
    terminal = {"succeeded", "failed", "terminated"}
    for attempt in range(1, 21):
        latest = status_payload(publisher.get_video_status(video_id))
        processing = str(latest.get("processing_status", "")).strip()
        upload_status = str(latest.get("upload_status", "")).strip()
        print(
            f"[status {attempt}/20] upload={upload_status or 'unknown'} processing={processing or 'unknown'}",
            flush=True,
        )
        if processing in terminal or upload_status in {"processed", "rejected", "failed"}:
            break
        time.sleep(30)
    status_doc = {"checked_at": utc_now(), "video_id": video_id, "status": latest}
    status_path = PACKAGE_ROOT / f"youtube_longform_private_upload_status_{upload_stamp}.json"
    write_json(status_path, status_doc)
    latest_path = PACKAGE_ROOT / "youtube_longform_private_upload_status_latest.json"
    shutil.copyfile(status_path, latest_path)
    return status_path, status_doc


def patch_review_html(upload: dict[str, Any]) -> None:
    path = PACKAGE_ROOT / "review.html"
    html = path.read_text(encoding="utf-8")
    html = html.replace(
        '<div><strong>YouTube Upload</strong><span class="lock">Needs Auth</span></div>',
        '<div><strong>YouTube Upload</strong><span>Private Uploaded</span></div>',
    )
    html = html.replace(
        "Publish-readiness is marked keep. The kept video stream, captions, metadata, thumbnail candidate, and upload locks are preserved.",
        "Publish-readiness is marked keep and a private YouTube review upload has been created. The kept video stream, captions, metadata, thumbnail candidate, and public-release locks are preserved.",
    )
    html = html.replace(
        "<tr><th>youtube_upload_ready_read</th><td>blocked_pending_publish_readiness_human_keep_and_upload_authorization</td></tr>",
        "<tr><th>youtube_upload_ready_read</th><td>pass_private_review_upload_created_public_release_manual</td></tr>",
    )
    insert = f"""

  <section class="panel" id="youtube-private-upload">
    <h2>YouTube Private Review Upload</h2>
    <p>Private review upload created. Public release, schedule, and visibility changes remain manual YouTube Studio actions.</p>
    <table><tbody>
      <tr><th>Video ID</th><td>{upload['video_id']}</td></tr>
      <tr><th>Private URL</th><td><a href="{upload['video_url']}">{upload['video_url']}</a></td></tr>
      <tr><th>Privacy</th><td>{upload['privacy_status']}</td></tr>
      <tr><th>Upload / Processing</th><td>{upload['upload_status']} / {upload['processing_status']}</td></tr>
      <tr><th>Thumbnail</th><td>{upload['thumbnail_status']}</td></tr>
      <tr><th>Captions</th><td>{upload['caption_status']}</td></tr>
      <tr><th>Public Release</th><td>manual_youtube_studio_only</td></tr>
    </tbody></table>
    <p>Studio checks still required: copyright/Content ID, altered-content disclosure, caption verification, and end-screen element placement.</p>
  </section>
"""
    if 'id="youtube-private-upload"' not in html:
        html = html.replace("</main>", insert + "\n</main>")
    path.write_text(html, encoding="utf-8")


def update_publish_manifest(
    manifest: dict[str, Any],
    upload_manifest_path: Path,
    receipt_path: Path,
    status_path: Path,
    status_latest_path: Path,
    receipt: dict[str, Any],
    status_doc: dict[str, Any],
) -> None:
    updated = copy.deepcopy(manifest)
    status = status_doc.get("status", {}) if isinstance(status_doc.get("status"), dict) else {}
    processing = str(status.get("processing_status", "")).strip()
    upload_status = str(status.get("upload_status", "")).strip()
    privacy = str(status.get("privacy_status", "")).strip()
    thumbnail_status = str(receipt.get("thumbnail", {}).get("status", "")).strip()
    caption_status = str(receipt.get("caption_upload", {}).get("status", "")).strip()
    processed_ok = processing == "succeeded" or upload_status == "processed"
    upload_object = {
        "status": "uploaded_private_review_processing_succeeded"
        if processed_ok
        else "uploaded_private_review_processing_pending",
        "uploaded_at": receipt.get("created_at"),
        "video_id": receipt.get("youtube", {}).get("video_id"),
        "video_url": receipt.get("youtube", {}).get("video_url"),
        "privacy_status": privacy,
        "upload_status": upload_status,
        "processing_status": processing,
        "channel_id": receipt.get("youtube", {}).get("channel_id"),
        "channel_title": receipt.get("youtube", {}).get("channel_title"),
        "notify_subscribers": False,
        "thumbnail_status": thumbnail_status,
        "captions_uploaded": caption_status == "uploaded",
        "caption_upload": receipt.get("caption_upload"),
        "caption_sidecar_to_upload_or_verify": receipt.get("caption_sidecar_to_upload_or_verify"),
        "upload_manifest": artifact(upload_manifest_path),
        "receipt": artifact(receipt_path),
        "status_check": artifact(status_path),
        "latest_status_check": artifact(status_latest_path),
        "read": "pass_private_review_upload_created_no_public_release",
        "visibility_change_taken": False,
        "superseded_do_not_publish": False,
    }
    updated["status"] = "private_review_uploaded_public_release_blocked_pending_studio_checks"
    updated["youtube_private_review_upload"] = upload_object
    updated["publish_ready"] = True
    updated["youtube_upload_ready"] = False
    updated["public_release_ready"] = False
    updated["may_youtube_action"] = False
    updated["upload_performed"] = True
    locks = updated.get("locks", {}) if isinstance(updated.get("locks"), dict) else {}
    locks.update(
        {
            "publish_ready": True,
            "youtube_upload_ready": False,
            "public_release_ready": False,
            "may_youtube_action": False,
            "upload_performed": True,
            "upload_action_enabled_in_review_html": False,
            "public_visibility_change_enabled": False,
        }
    )
    updated["locks"] = locks
    reads = updated.get("reads", {}) if isinstance(updated.get("reads"), dict) else {}
    reads.update(
        {
            "upload_authorization_read": "pass_user_authorized_private_youtube_upload_for_therac25_2026_05_18",
            "youtube_upload_ready_read": "pass_private_review_upload_created_public_release_manual",
            "youtube_private_upload_read": "pass_private_review_upload_created",
            "youtube_private_upload_status_read": (
                "pass_upload_status_processed_processing_succeeded"
                if processed_ok
                else f"review_pending_upload_status_{upload_status or 'unknown'}_processing_{processing or 'unknown'}"
            ),
            "youtube_private_upload_privacy_read": f"pass_privacy_{privacy or 'unknown'}",
            "youtube_private_upload_thumbnail_read": f"pass_thumbnail_{thumbnail_status or 'unknown'}",
            "youtube_caption_sidecar_upload_read": (
                "pass_caption_sidecar_uploaded"
                if caption_status == "uploaded"
                else "pending_manual_upload_or_studio_verification_captions_uploaded_false"
            ),
            "youtube_public_release_read": "blocked_manual_youtube_studio_only",
            "youtube_end_screen_studio_elements_read": "pending_youtube_studio_end_screen_element_configuration",
            "html_private_upload_visible_read": "pass_review_html_shows_private_upload_video_id_and_url",
            "html_public_release_lock_visible_read": "pass_public_release_schedule_visibility_locked",
            "html_post_upload_blockers_visible_read": "pass_copyright_caption_altered_content_end_screen_public_release_blockers_visible",
            "youtube_private_upload_processing_read": (
                "pass_processing_succeeded" if processed_ok else f"review_pending_processing_{processing or 'unknown'}"
            ),
            "public_release_ready_read": "blocked_public_release_manual",
        }
    )
    updated["reads"] = reads
    updated["remaining_blockers"] = POST_UPLOAD_BLOCKERS
    write_json(PUBLISH_MANIFEST, updated)


def main() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from orchestration.publish import build_youtube_package_publisher, _verify_authenticated_channel

    upload_stamp = stamp()
    manifest = read_json(PUBLISH_MANIFEST)
    assets, validator = verify_preflight(manifest)
    upload_manifest_path, upload_manifest = build_upload_manifest(manifest, assets, validator, upload_stamp)
    print(f"[preflight] wrote upload manifest: {upload_manifest_path}", flush=True)

    publisher = build_youtube_package_publisher(config_dir=YOUTUBE_CONFIG_DIR)
    channel = _verify_authenticated_channel(publisher)
    print(f"[youtube] authenticated channel: {channel.get('title')} ({channel.get('channel_id')})", flush=True)

    metadata = upload_manifest["youtube_metadata"]
    payload = {
        "video_path": upload_manifest["upload_assets"]["video_path"],
        "title": metadata["title"],
        "description_text": metadata["description"],
        "tags": metadata["tags"],
        "privacy": "private",
        "thumbnail_path": upload_manifest["upload_assets"]["thumbnail_path"],
        "category_id": metadata["category_id"],
        "default_language": metadata["default_language"],
        "default_audio_language": metadata["default_audio_language"],
        "self_declared_made_for_kids": metadata["self_declared_made_for_kids"],
        "notify_subscribers": False,
        "ignore_thumbnail_errors": True,
    }
    print("[youtube] starting private video upload", flush=True)
    result = publisher.publish_video(payload)
    print(f"[youtube] uploaded video id: {result.video_id}", flush=True)

    caption_result = upload_captions_srt(publisher, result.video_id, assets["srt"])
    print(f"[youtube] caption upload status: {caption_result['status']}", flush=True)

    status_path, status_doc = poll_status(publisher, result.video_id, upload_stamp)
    latest_path = PACKAGE_ROOT / "youtube_longform_private_upload_status_latest.json"
    status = status_doc.get("status", {}) if isinstance(status_doc.get("status"), dict) else {}

    receipt = {
        "receipt_type": "youtube_longform_private_upload",
        "created_at": utc_now(),
        "manifest_path": str(upload_manifest_path),
        "source_publish_readiness_manifest_path": str(PUBLISH_MANIFEST),
        "privacy": "private",
        "notify_subscribers": False,
        "public_release": "manual_youtube_studio_only",
        "youtube": {
            "video_id": result.video_id,
            "video_url": result.video_url,
            "channel_id": channel.get("channel_id"),
            "channel_title": channel.get("title"),
            "published_at": result.published_at,
            "status": status,
        },
        "thumbnail": {
            "path": upload_manifest["upload_assets"]["thumbnail_path"],
            "status": result.thumbnail_status,
            "error": result.thumbnail_error,
        },
        "caption_upload": caption_result,
        "caption_sidecar_to_upload_or_verify": upload_manifest["upload_assets"]["caption_srt_path"],
        "captions_uploaded": caption_result.get("status") == "uploaded",
        "raw_upload_response": result.raw_response,
        "post_upload_blockers": POST_UPLOAD_BLOCKERS,
    }
    receipt_path = PACKAGE_ROOT / f"youtube_longform_private_upload_receipt_{upload_stamp}.json"
    write_json(receipt_path, receipt)

    patch_review_html(
        {
            "video_id": result.video_id,
            "video_url": result.video_url,
            "privacy_status": status.get("privacy_status", ""),
            "upload_status": status.get("upload_status", ""),
            "processing_status": status.get("processing_status", ""),
            "thumbnail_status": result.thumbnail_status,
            "caption_status": caption_result.get("status", ""),
        }
    )
    update_publish_manifest(manifest, upload_manifest_path, receipt_path, status_path, latest_path, receipt, status_doc)

    summary = {
        "ok": True,
        "video_id": result.video_id,
        "video_url": result.video_url,
        "privacy": status.get("privacy_status", ""),
        "upload_status": status.get("upload_status", ""),
        "processing_status": status.get("processing_status", ""),
        "thumbnail_status": result.thumbnail_status,
        "caption_status": caption_result.get("status", ""),
        "upload_manifest_path": str(upload_manifest_path),
        "receipt_path": str(receipt_path),
        "status_path": str(status_path),
        "publish_manifest_path": str(PUBLISH_MANIFEST),
        "review_html_path": str(PACKAGE_ROOT / "review.html"),
        "public_release": "manual_youtube_studio_only",
    }
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
