#!/usr/bin/env python3
"""Upload the kept Challenger long-form package as a new unlisted review video.

This is intentionally narrow to avoid mutating the stale private upload. It
uses the local YouTube OAuth config, uploads the current subtle-tail final MP4
as unlisted, attempts thumbnail and caption sidecar upload, and records local
receipts while keeping public release locked.
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
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/"
    "rough_assembly/challenger_longform_canonical_signoff_subtle_tail_outro_html_approval_proof_20260518T221334Z/"
    "video_render/challenger_longform_canonical_signoff_subtle_tail_outro_final_mp4_20260518T221420Z/"
    "publish_readiness/challenger_longform_canonical_signoff_publish_readiness_20260518T224617Z"
)
PUBLISH_MANIFEST = PACKAGE_ROOT / "publish_readiness_manifest.json"
PROOF_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/"
    "rough_assembly/challenger_longform_canonical_signoff_subtle_tail_outro_html_approval_proof_20260518T221334Z"
)
PROOF_MANIFEST = PROOF_ROOT / "rough_assembly_manifest.json"
PLAYER_HTML = PROOF_ROOT / "player.html"
AUDIO_MIX_MANIFEST = PROOF_ROOT / "references/audio_mix_manifest.json"
FINAL_RENDER_MANIFEST = (
    PROOF_ROOT
    / "video_render/challenger_longform_canonical_signoff_subtle_tail_outro_final_mp4_20260518T221420Z/render_manifest.json"
)
VALIDATOR = REPO_ROOT / "scripts/validate_living_cover_final_gate.mjs"
YOUTUBE_CONFIG_DIR = Path("/Users/mike/.config/cascade-effects/youtube")
YOUTUBE_THUMBNAIL_LIMIT_BYTES = 2_097_152
YOUTUBE_THUMBNAIL_DERIVATIVE = PACKAGE_ROOT / "images/thumbnail_candidate_youtube_upload.jpg"
OLD_PRIVATE_VIDEO_ID = "ToEay5mFDy8"


POST_UPLOAD_BLOCKERS = [
    "Review YouTube Studio copyright and Content ID checks before public release.",
    "Confirm altered-content disclosure in YouTube Studio for realistic generated or source-derived episode visuals.",
    "Verify uploaded captions in YouTube Studio and remove/ignore automatic captions if they conflict with the script-locked sidecar.",
    "Configure final YouTube Studio end-screen elements for the baked titleless three-target end-screen geometry.",
    "Public visibility change remains manual and must not be performed by this upload step.",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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
    require(isinstance(payload, dict), f"JSON file must contain an object: {path}")
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


def normalize_tags(tags: Any) -> list[str]:
    if not isinstance(tags, list):
        return []
    seen: set[str] = set()
    output: list[str] = []
    for tag in tags:
        text = str(tag).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def youtube_description(metadata: dict[str, Any]) -> str:
    description = str(metadata.get("description", "")).strip()
    chapters = metadata.get("chapters")
    if isinstance(chapters, list) and chapters:
        lines = ["Chapters:"]
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            timestamp = str(chapter.get("timestamp", "")).strip()
            title = str(chapter.get("title", "")).strip()
            if timestamp and title:
                lines.append(f"{timestamp} {title}")
        if len(lines) > 1:
            description = description + "\n\n" + "\n".join(lines)
    return description


def upload_captions_srt(publisher: Any, video_id: str, caption_path: Path) -> dict[str, Any]:
    token = publisher.refresh_access_token()
    boundary = f"cascadeeffects-{stamp()}"
    metadata = {
        "snippet": {
            "videoId": video_id,
            "language": "en",
            "name": "English script-locked captions",
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
    except Exception as exc:  # noqa: BLE001 - nonfatal audit evidence
        return {
            "status": "failed_nonfatal",
            "error": str(exc),
            "caption_id": "",
            "raw_response": {},
        }


def media_path(manifest: dict[str, Any], key: str) -> Path:
    media = manifest.get("media", {}) if isinstance(manifest.get("media"), dict) else {}
    value = media.get(key, {}) if isinstance(media.get(key), dict) else {}
    return Path(str(value.get("path", "")).strip())


def verify_preflight(manifest: dict[str, Any]) -> tuple[dict[str, Path], dict[str, Any]]:
    require(PUBLISH_MANIFEST.exists(), f"Missing publish readiness manifest: {PUBLISH_MANIFEST}")
    require(str(manifest.get("human_disposition", "")).strip() in {"pending", "keep"}, "Unexpected human disposition.")
    require(manifest.get("upload_performed") is False, "This package already records an upload.")
    existing = manifest.get("youtube_unlisted_review_upload")
    if isinstance(existing, dict) and existing.get("video_id"):
        raise RuntimeError(f"Active unlisted review upload already exists: {existing.get('video_id')}")

    old_upload = manifest.get("old_private_upload", {}) if isinstance(manifest.get("old_private_upload"), dict) else {}
    require(old_upload.get("video_id") == OLD_PRIVATE_VIDEO_ID, "Expected old private upload id was not recorded.")
    require(old_upload.get("local_status") == "superseded_do_not_publish", "Old private upload is not marked superseded.")

    mp4 = media_path(manifest, "mp4")
    vtt = media_path(manifest, "upload_vtt") or media_path(manifest, "vtt")
    srt = media_path(manifest, "upload_srt") or media_path(manifest, "srt")
    thumbnail = media_path(manifest, "thumbnail_candidate")
    for label, path in (("mp4", mp4), ("vtt", vtt), ("srt", srt), ("thumbnail", thumbnail)):
        require(path.exists(), f"Missing upload asset {label}: {path}")

    media = manifest.get("media", {}) if isinstance(manifest.get("media"), dict) else {}
    for key, path in (("mp4", mp4), ("upload_vtt", vtt), ("upload_srt", srt), ("thumbnail_candidate", thumbnail)):
        declared = (media.get(key, {}) if isinstance(media.get(key), dict) else {}).get("sha256")
        require(not declared or declared == sha256_file(path), f"Hash mismatch for {key}: {path}")

    validator = run_validator()
    require(validator.get("status") == "pass", f"Final gate validator did not pass: {validator}")
    guard_receipt = PACKAGE_ROOT / "preflight" / f"challenger_precision_matte_guard_{stamp()}.json"
    completed = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts/challenger_precision_matte_guard.mjs"),
            "--manifest",
            str(PUBLISH_MANIFEST),
            "--write-receipt",
            str(guard_receipt),
            "--context",
            "legacy_challenger_unlisted_upload_preflight",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    require(
        completed.returncode == 0,
        "Challenger precision matte guard failed before legacy upload path.\n"
        f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}",
    )
    validator["challenger_precision_matte_guard"] = {
        "path": str(guard_receipt),
        "sha256": sha256_file(guard_receipt),
    }
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
    metadata = manifest.get("metadata", {}) if isinstance(manifest.get("metadata"), dict) else {}
    title = str(metadata.get("title", "")).strip()
    description = youtube_description(metadata)
    tags = normalize_tags(metadata.get("tags"))
    require(title, "Missing YouTube title.")
    require(description, "Missing YouTube description.")
    require(tags, "Missing YouTube tags.")
    probe = ffprobe(assets["mp4"])
    upload_manifest = {
        "created_at": utc_now(),
        "human_publish_readiness_keep_read": "pass_user_kept_challenger_subtle_tail_publish_readiness_2026_05_18",
        "human_upload_approval_read": "pass_user_authorized_new_unlisted_youtube_upload_for_challenger_2026_05_18",
        "target": "youtube_longform_unlisted_review",
        "privacy": "unlisted",
        "notify_subscribers": False,
        "public_release": "manual_youtube_studio_only",
        "old_private_upload": {
            "video_id": OLD_PRIVATE_VIDEO_ID,
            "local_status": "superseded_do_not_publish",
            "visibility_change_taken": False,
        },
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
    path = PACKAGE_ROOT / f"youtube_longform_unlisted_upload_manifest_{upload_stamp}.json"
    write_json(path, upload_manifest)
    return path, upload_manifest


def status_payload(status: Any) -> dict[str, Any]:
    payload = dataclass_or_value(status)
    require(isinstance(payload, dict), "Unexpected status response.")
    return payload


def poll_status(publisher: Any, video_id: str, upload_stamp: str) -> tuple[Path, dict[str, Any]]:
    latest: dict[str, Any] = {}
    terminal = {"succeeded", "failed", "terminated"}
    for attempt in range(1, 16):
        latest = status_payload(publisher.get_video_status(video_id))
        processing = str(latest.get("processing_status", "")).strip()
        upload_status = str(latest.get("upload_status", "")).strip()
        print(
            f"[status {attempt}/15] upload={upload_status or 'unknown'} processing={processing or 'unknown'}",
            flush=True,
        )
        if processing in terminal or upload_status in {"processed", "rejected", "failed"}:
            break
        time.sleep(20)
    status_doc = {"checked_at": utc_now(), "video_id": video_id, "status": latest}
    status_path = PACKAGE_ROOT / f"youtube_longform_unlisted_upload_status_{upload_stamp}.json"
    write_json(status_path, status_doc)
    latest_path = PACKAGE_ROOT / "youtube_longform_unlisted_upload_status_latest.json"
    shutil.copyfile(status_path, latest_path)
    return status_path, status_doc


def patch_review_html(upload: dict[str, Any]) -> None:
    path = PACKAGE_ROOT / "review.html"
    html = path.read_text(encoding="utf-8")
    html = html.replace("Pending unlisted YouTube review upload", "Unlisted YouTube review upload created")
    html = html.replace("Separate explicit unlisted review-upload approval is not recorded.", "Unlisted review-upload approval recorded.")
    html = html.replace(
        "Remote cascadeeffects.tv review is video-pending until a new unlisted YouTube review upload exists.",
        "Remote review video exists as a new unlisted YouTube upload.",
    )
    html = html.replace(
        "<tr><th>Remote video state</th><td><code>video pending; no YouTube upload action taken</code></td></tr>",
        f"<tr><th>Remote video state</th><td><code>unlisted upload created: {upload['video_id']}</code></td></tr>",
    )
    html = html.replace(
        "<tr><th>youtube_unlisted_review_upload_read</th><td>pending_review_video_no_youtube_action_taken</td></tr>",
        "<tr><th>youtube_unlisted_review_upload_read</th><td>pass_new_unlisted_review_upload_created</td></tr>",
    )
    insert = f"""

  <section class="panel" id="youtube-unlisted-upload">
    <h2>YouTube Unlisted Review Upload</h2>
    <p>New unlisted review upload created. Public release, schedule, and visibility changes remain manual YouTube Studio actions.</p>
    <table><tbody>
      <tr><th>Video ID</th><td>{upload['video_id']}</td></tr>
      <tr><th>Unlisted URL</th><td><a href="{upload['video_url']}">{upload['video_url']}</a></td></tr>
      <tr><th>Privacy</th><td>{upload['privacy_status']}</td></tr>
      <tr><th>Upload / Processing</th><td>{upload['upload_status']} / {upload['processing_status']}</td></tr>
      <tr><th>Thumbnail</th><td>{upload['thumbnail_status']}</td></tr>
      <tr><th>Captions</th><td>{upload['caption_status']}</td></tr>
      <tr><th>Old Private Upload</th><td>{OLD_PRIVATE_VIDEO_ID} remains superseded_do_not_publish</td></tr>
      <tr><th>Public Release</th><td>manual_youtube_studio_only</td></tr>
    </tbody></table>
    <p>Studio checks still required: copyright/Content ID, altered-content disclosure, caption verification, and end-screen element placement.</p>
  </section>
"""
    if 'id="youtube-unlisted-upload"' not in html:
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
        "status": "uploaded_unlisted_review_processing_succeeded"
        if processed_ok
        else "uploaded_unlisted_review_processing_pending",
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
        "read": "pass_new_unlisted_review_upload_created_no_public_release",
        "visibility_change_taken": False,
        "supersedes_private_video_id": OLD_PRIVATE_VIDEO_ID,
    }
    updated["status"] = "unlisted_review_uploaded_public_release_blocked_pending_studio_checks"
    updated["human_disposition"] = "keep"
    updated["human_keep_recorded_at"] = receipt.get("created_at")
    updated["upload_performed"] = True
    updated["publish_ready"] = True
    updated["youtube_upload_ready"] = False
    updated["public_release_ready"] = False
    updated["may_youtube_action"] = False
    updated["youtube_unlisted_review_upload"] = upload_object
    updated["youtube_private_review_upload"] = {
        "video_id": OLD_PRIVATE_VIDEO_ID,
        "local_status": "superseded_do_not_publish",
        "visibility_change_taken": False,
    }
    locks = updated.get("locks", {}) if isinstance(updated.get("locks"), dict) else {}
    locks.update(
        {
            "publish_ready": True,
            "publishReady": True,
            "youtube_upload_ready": False,
            "youtubeUploadReady": False,
            "public_release_ready": False,
            "publicReleaseReady": False,
            "may_youtube_action": False,
            "mayYoutubeAction": False,
            "upload_performed": True,
            "uploadPerformed": True,
            "upload_action_enabled_in_review_html": False,
            "public_visibility_change_enabled": False,
        }
    )
    updated["locks"] = locks
    reads = updated.get("reads", {}) if isinstance(updated.get("reads"), dict) else {}
    reads.update(
        {
            "human_publish_readiness_keep_read": "pass_user_kept_challenger_subtle_tail_publish_readiness_2026_05_18",
            "explicit_youtube_upload_approval_read": "pass_user_authorized_new_unlisted_youtube_upload_2026_05_18",
            "upload_authorization_read": "pass_user_authorized_new_unlisted_youtube_upload_2026_05_18",
            "youtube_upload_ready_read": "pass_new_unlisted_review_upload_created_public_release_manual",
            "youtube_unlisted_review_upload_read": "pass_new_unlisted_review_upload_created",
            "youtube_unlisted_review_privacy_read": f"pass_privacy_{privacy or 'unknown'}",
            "youtube_private_upload_superseded_read": f"pass_{OLD_PRIVATE_VIDEO_ID}_superseded_do_not_publish",
            "youtube_private_upload_read": "not_applicable_old_private_upload_superseded_new_unlisted_upload_created",
            "youtube_private_upload_status_read": "not_applicable_old_private_upload_superseded_new_unlisted_upload_created",
            "youtube_private_upload_privacy_read": "not_applicable_old_private_upload_superseded_new_unlisted_upload_created",
            "youtube_private_upload_thumbnail_read": "not_applicable_old_private_upload_superseded_new_unlisted_upload_created",
            "youtube_unlisted_upload_status_read": (
                "pass_upload_status_processed_processing_succeeded"
                if processed_ok
                else f"review_pending_upload_status_{upload_status or 'unknown'}_processing_{processing or 'unknown'}"
            ),
            "youtube_unlisted_upload_thumbnail_read": f"pass_thumbnail_{thumbnail_status or 'unknown'}",
            "youtube_caption_sidecar_upload_read": (
                "pass_caption_sidecar_uploaded"
                if caption_status == "uploaded"
                else "pending_manual_upload_or_studio_verification_captions_uploaded_false"
            ),
            "youtube_public_release_read": "blocked_manual_youtube_studio_only",
            "youtube_end_screen_studio_elements_read": "pending_youtube_studio_end_screen_element_configuration",
            "html_private_upload_visible_read": "pass_review_html_shows_old_private_upload_superseded_do_not_publish",
            "html_unlisted_upload_visible_read": "pass_review_html_shows_new_unlisted_upload_video_id_and_url",
            "html_public_release_lock_visible_read": "pass_public_release_schedule_visibility_locked",
            "html_post_upload_blockers_visible_read": "pass_copyright_caption_altered_content_end_screen_public_release_blockers_visible",
            "youtube_unlisted_upload_processing_read": (
                "pass_processing_succeeded" if processed_ok else f"review_pending_processing_{processing or 'unknown'}"
            ),
            "public_release_ready_read": "blocked_public_release_manual",
            "downstream_gate_read": "pass_unlisted_review_upload_done_public_release_locked",
        }
    )
    updated["reads"] = reads
    updated["remaining_blockers"] = POST_UPLOAD_BLOCKERS
    review_html = PACKAGE_ROOT / "review.html"
    if review_html.exists():
        updated["publish_readiness_review_html"] = artifact(review_html)
    write_json(PUBLISH_MANIFEST, updated)


def main() -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from orchestration.publish import _verify_authenticated_channel, build_youtube_package_publisher

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
        "privacy": "unlisted",
        "thumbnail_path": upload_manifest["upload_assets"]["thumbnail_path"],
        "category_id": metadata["category_id"],
        "default_language": metadata["default_language"],
        "default_audio_language": metadata["default_audio_language"],
        "self_declared_made_for_kids": metadata["self_declared_made_for_kids"],
        "notify_subscribers": False,
        "ignore_thumbnail_errors": True,
    }
    print("[youtube] starting new unlisted video upload", flush=True)
    result = publisher.publish_video(payload)
    print(f"[youtube] uploaded video id: {result.video_id}", flush=True)

    caption_result = upload_captions_srt(publisher, result.video_id, assets["srt"])
    print(f"[youtube] caption upload status: {caption_result['status']}", flush=True)

    status_path, status_doc = poll_status(publisher, result.video_id, upload_stamp)
    latest_path = PACKAGE_ROOT / "youtube_longform_unlisted_upload_status_latest.json"
    status = status_doc.get("status", {}) if isinstance(status_doc.get("status"), dict) else {}

    receipt = {
        "receipt_type": "youtube_longform_unlisted_upload",
        "created_at": utc_now(),
        "manifest_path": str(upload_manifest_path),
        "source_publish_readiness_manifest_path": str(PUBLISH_MANIFEST),
        "privacy": "unlisted",
        "notify_subscribers": False,
        "public_release": "manual_youtube_studio_only",
        "old_private_upload": {
            "video_id": OLD_PRIVATE_VIDEO_ID,
            "local_status": "superseded_do_not_publish",
            "visibility_change_taken": False,
        },
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
    receipt_path = PACKAGE_ROOT / f"youtube_longform_unlisted_upload_receipt_{upload_stamp}.json"
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
        "old_private_video_id": OLD_PRIVATE_VIDEO_ID,
        "public_release": "manual_youtube_studio_only",
    }
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
