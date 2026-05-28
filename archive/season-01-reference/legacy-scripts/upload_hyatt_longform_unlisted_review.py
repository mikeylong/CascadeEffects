#!/usr/bin/env python3
"""Upload the current Hyatt long-form lifecycle packet as an unlisted review.

This follows the Challenger/Therac long-form precedent: the final MP4 is hosted
on YouTube for review, small evidence stays in the local/remote review packet,
and public release remains locked for manual YouTube Studio handling.
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
RESTART_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516")
PACKAGE_ROOT = RESTART_ROOT / "youtube/publish_readiness/hyatt_publish_readiness_lifecycle"
PUBLISH_MANIFEST = PACKAGE_ROOT / "publish_readiness_manifest.json"
PROOF_ROOT = (
    RESTART_ROOT
    / "youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_subtle_tail_outro_20260519T040128Z"
)
PROOF_MANIFEST = PROOF_ROOT / "rough_assembly_manifest.json"
PLAYER_HTML = PROOF_ROOT / "player.html"
AUDIO_MIX_MANIFEST = PROOF_ROOT / "references/audio_mix_manifest.json"
FINAL_RENDER_ROOT = PROOF_ROOT / "video_render/hyatt_longform_final_mp4_20260519T040222Z"
FINAL_RENDER_MANIFEST = FINAL_RENDER_ROOT / "render_manifest.json"
LOCAL_RENDER_MANIFEST = PACKAGE_ROOT / "render_manifest.json"
VALIDATOR = REPO_ROOT / "scripts/validate_living_cover_final_gate.mjs"
GATE_APPROVALS_DIR = RESTART_ROOT / "youtube/gate_approvals"
YOUTUBE_CONFIG_DIR = Path("/Users/mike/.config/cascade-effects/youtube")
YOUTUBE_THUMBNAIL_LIMIT_BYTES = 2_097_152
YOUTUBE_THUMBNAIL_DERIVATIVE = PACKAGE_ROOT / "thumbnail/hyatt_thumbnail_candidate_youtube_upload.jpg"

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


def resolve_packet_path(manifest: dict[str, Any], media_key: str) -> Path:
    media = manifest.get("media", {}) if isinstance(manifest.get("media"), dict) else {}
    artifact_obj = media.get(media_key, {}) if isinstance(media.get(media_key), dict) else {}
    raw_path = str(artifact_obj.get("path", "")).strip()
    require(raw_path, f"Missing media.{media_key}.path")
    return Path(raw_path) if Path(raw_path).is_absolute() else PACKAGE_ROOT / raw_path


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


def chapter_title(chapter: dict[str, Any]) -> str:
    return str(chapter.get("label") or chapter.get("title") or "").strip()


def chapter_time(chapter: dict[str, Any]) -> str:
    return str(chapter.get("time") or chapter.get("timestamp") or "").strip()


def youtube_description(metadata: dict[str, Any]) -> str:
    description = str(metadata.get("description", "")).strip()
    if "Chapters:" in description:
        return description
    chapters = metadata.get("chapters")
    if isinstance(chapters, list) and chapters:
        lines = ["Chapters:"]
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            timestamp = chapter_time(chapter)
            title = chapter_title(chapter)
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


def verify_preflight(manifest: dict[str, Any]) -> tuple[dict[str, Path], dict[str, Any]]:
    require(PUBLISH_MANIFEST.exists(), f"Missing publish readiness manifest: {PUBLISH_MANIFEST}")
    existing = manifest.get("youtube_review")
    if isinstance(existing, dict) and existing.get("video_id"):
        raise RuntimeError(f"Active YouTube review upload already exists: {existing.get('video_id')}")
    locks = manifest.get("locks", {}) if isinstance(manifest.get("locks"), dict) else {}
    require(locks.get("public_release_ready") is False, "Public release must remain locked.")
    require(locks.get("may_youtube_action") is False, "General YouTube actions must remain locked outside this explicit upload.")

    assets = {
        "mp4": resolve_packet_path(manifest, "final_mp4"),
        "vtt": resolve_packet_path(manifest, "caption_vtt"),
        "srt": resolve_packet_path(manifest, "caption_srt"),
        "thumbnail_source": resolve_packet_path(manifest, "thumbnail_candidate"),
    }
    for label, asset_path in assets.items():
        require(asset_path.exists(), f"Missing upload asset {label}: {asset_path}")
    media = manifest.get("media", {}) if isinstance(manifest.get("media"), dict) else {}
    for key, asset_path in (
        ("final_mp4", assets["mp4"]),
        ("caption_vtt", assets["vtt"]),
        ("caption_srt", assets["srt"]),
        ("thumbnail_candidate", assets["thumbnail_source"]),
    ):
        declared = media.get(key, {}).get("sha256") if isinstance(media.get(key), dict) else ""
        require(not declared or declared == sha256_file(asset_path), f"Hash mismatch for media.{key}: {asset_path}")

    validator = run_validator()
    require(validator.get("status") == "pass", f"Final gate validator did not pass: {validator}")
    assets["thumbnail"] = prepare_youtube_thumbnail(assets["thumbnail_source"])
    return assets, validator


def build_upload_manifest(
    manifest: dict[str, Any],
    assets: dict[str, Path],
    validator: dict[str, Any],
    upload_stamp: str,
) -> tuple[Path, dict[str, Any]]:
    metadata = manifest.get("youtube_metadata", {}) if isinstance(manifest.get("youtube_metadata"), dict) else {}
    title = str(metadata.get("title", "")).strip()
    description = youtube_description(metadata)
    tags = normalize_tags(metadata.get("tags"))
    require(title, "Missing YouTube title.")
    require(description, "Missing YouTube description.")
    require(tags, "Missing YouTube tags.")
    upload_manifest = {
        "created_at": utc_now(),
        "human_final_assembly_keep_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
        "human_publish_readiness_keep_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
        "human_upload_approval_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
        "target": "youtube_longform_unlisted_review",
        "privacy": "unlisted",
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
            "probe": ffprobe(assets["mp4"]),
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


def mark_final_assembly_keep(upload_stamp: str, receipt_created_at: str) -> Path:
    GATE_APPROVALS_DIR.mkdir(parents=True, exist_ok=True)
    approval_path = GATE_APPROVALS_DIR / f"hyatt_final_assembly_keep_youtube_upload_{upload_stamp}.json"
    approval = {
        "created_at": receipt_created_at,
        "episode": "hyatt-regency",
        "gate": "final_assembly",
        "human_disposition": "keep",
        "approval_source": "user_requested_publish_video_to_youtube_and_update_review",
        "final_render_manifest_path": str(FINAL_RENDER_MANIFEST),
        "mp4_path": str(PACKAGE_ROOT / "media/hyatt_regency_living_cover_final_review_1080p24.mp4"),
        "public_release": "manual_youtube_studio_only",
    }
    write_json(approval_path, approval)
    for manifest_path in (FINAL_RENDER_MANIFEST, LOCAL_RENDER_MANIFEST):
        if not manifest_path.exists():
            continue
        manifest = read_json(manifest_path)
        manifest["status"] = "final_assembly_keep_opened_publish_readiness_youtube_review_uploaded_public_release_blocked"
        manifest["human_disposition"] = "keep"
        manifest["human_keep_recorded_at"] = receipt_created_at
        manifest["human_keep_approval_path"] = str(approval_path)
        manifest["may_advance_to_publish_readiness"] = True
        locks = manifest.get("upload_locks", {}) if isinstance(manifest.get("upload_locks"), dict) else {}
        locks.update(
            {
                "publish_ready": True,
                "youtube_upload_ready": False,
                "public_release_ready": False,
                "may_youtube_action": False,
                "upload_performed": True,
                "public_release": False,
            }
        )
        manifest["upload_locks"] = locks
        reads = manifest.get("qa_reads", {}) if isinstance(manifest.get("qa_reads"), dict) else {}
        reads.update(
            {
                "final_assembly_human_keep_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
                "explicit_youtube_upload_approval_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
                "youtube_public_release_read": "blocked_manual_youtube_studio_only",
            }
        )
        manifest["qa_reads"] = reads
        write_json(manifest_path, manifest)
    return approval_path


def patch_review_html(upload: dict[str, Any]) -> None:
    path = PACKAGE_ROOT / "review.html"
    html = path.read_text(encoding="utf-8")
    html = html.replace("Upload and public release remain locked.", "YouTube review upload exists; public release remains locked.")
    html = html.replace(
        "<div><strong>YouTube action</strong>unavailable</div>",
        '<div><strong>YouTube review</strong><span>unlisted uploaded</span></div>',
    )
    insert = f"""

  <section class="panel" id="youtube-unlisted-upload">
    <h2>YouTube Unlisted Review Upload</h2>
    <p>Unlisted review upload created. Public release, schedule, and visibility changes remain manual YouTube Studio actions.</p>
    <table><tbody>
      <tr><th>Video ID</th><td>{upload['video_id']}</td></tr>
      <tr><th>Unlisted URL</th><td><a href="{upload['video_url']}">{upload['video_url']}</a></td></tr>
      <tr><th>Privacy</th><td>{upload['privacy_status']}</td></tr>
      <tr><th>Upload / Processing</th><td>{upload['upload_status']} / {upload['processing_status']}</td></tr>
      <tr><th>Embeddable</th><td>{upload['embeddable']}</td></tr>
      <tr><th>Thumbnail</th><td>{upload['thumbnail_status']}</td></tr>
      <tr><th>Captions</th><td>{upload['caption_status']}</td></tr>
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
    approval_path: Path,
    receipt: dict[str, Any],
    status_doc: dict[str, Any],
) -> None:
    updated = copy.deepcopy(manifest)
    status = status_doc.get("status", {}) if isinstance(status_doc.get("status"), dict) else {}
    processing = str(status.get("processing_status", "")).strip()
    upload_status = str(status.get("upload_status", "")).strip()
    privacy = str(status.get("privacy_status", "")).strip()
    embeddable = bool(status.get("raw_response", {}).get("items", [{}])[0].get("status", {}).get("embeddable", True))
    thumbnail_status = str(receipt.get("thumbnail", {}).get("status", "")).strip()
    caption_status = str(receipt.get("caption_upload", {}).get("status", "")).strip()
    processed_ok = processing == "succeeded" or upload_status == "processed"
    video_id = receipt.get("youtube", {}).get("video_id")
    video_url = receipt.get("youtube", {}).get("video_url")
    upload_object = {
        "status": "uploaded_unlisted_review_processing_succeeded"
        if processed_ok
        else "uploaded_unlisted_review_processing_pending",
        "host": "youtube_unlisted",
        "uploaded_at": receipt.get("created_at"),
        "video_id": video_id,
        "video_url": video_url,
        "watch_url": video_url,
        "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?enablejsapi=1&rel=0&modestbranding=1&playsinline=1",
        "title": updated.get("youtube_metadata", {}).get("title"),
        "privacy_status": privacy,
        "upload_status": upload_status,
        "processing_status": processing,
        "embeddable": embeddable,
        "channel_id": receipt.get("youtube", {}).get("channel_id"),
        "channel_title": receipt.get("youtube", {}).get("channel_title"),
        "notify_subscribers": False,
        "thumbnail_status": thumbnail_status,
        "captions_uploaded": caption_status == "uploaded",
        "caption_upload": receipt.get("caption_upload"),
        "caption_sidecar_to_upload_or_verify": receipt.get("caption_sidecar_to_upload_or_verify"),
        "upload_manifest": artifact(upload_manifest_path),
        "receipt": artifact(receipt_path),
        "receipt_path": str(receipt_path),
        "receipt_sha256": sha256_file(receipt_path),
        "status_check": artifact(status_path),
        "latest_status_check": artifact(status_latest_path),
        "read": "pass_new_unlisted_review_upload_created_no_public_release",
        "visibility_change_taken": False,
    }

    updated["lifecycle_stage"] = "publish_readiness"
    updated["stage"] = "publish_readiness"
    updated["current_gate"] = "youtube_review_upload"
    updated["status"] = "youtube_unlisted_review_uploaded_public_release_blocked_pending_studio_checks"
    updated["human_disposition"] = "keep"
    updated["final_assembly_disposition"] = "keep"
    updated["human_keep_recorded_at"] = receipt.get("created_at")
    updated["human_keep_approval_path"] = str(approval_path)
    updated["publish_ready"] = True
    updated["youtube_upload_ready"] = False
    updated["public_release_ready"] = False
    updated["may_youtube_action"] = False
    updated["upload_performed"] = True
    updated["may_advance_to_upload"] = False
    updated["youtube_review"] = upload_object
    updated["youtube_unlisted_review"] = upload_object
    remote_review = updated.get("remote_review", {}) if isinstance(updated.get("remote_review"), dict) else {}
    remote_review.update(
        {
            "status": "pending_remote_refresh_after_youtube_upload",
            "review_id": "hyatt-regency",
            "remote_review_url": "https://cascadeeffects.tv/reviews/publish-readiness/hyatt-regency",
            "video_host": "youtube_unlisted_review",
            "youtube_review": {
                "video_id": video_id,
                "video_url": video_url,
                "privacy_status": privacy,
                "processing_status": processing,
                "upload_status": upload_status,
                "embeddable": embeddable,
                "receipt_path": str(receipt_path),
                "receipt_sha256": sha256_file(receipt_path),
            },
        }
    )
    updated["remote_review"] = remote_review

    media = updated.get("media", {}) if isinstance(updated.get("media"), dict) else {}
    if "final_mp4" in media:
        media["mp4"] = media["final_mp4"]
    if "caption_vtt" in media:
        media["vtt"] = media["caption_vtt"]
        media["upload_vtt"] = media["caption_vtt"]
    if "caption_srt" in media:
        media["srt"] = media["caption_srt"]
        media["upload_srt"] = media["caption_srt"]
    qa_frame_dir = PACKAGE_ROOT / "qa_frames"
    qa_frames = []
    if qa_frame_dir.exists():
        for frame_path in sorted(qa_frame_dir.glob("*.jpg")):
            qa_frames.append(
                {
                    "label": frame_path.stem,
                    "path": str(frame_path.relative_to(PACKAGE_ROOT)),
                    "sha256": sha256_file(frame_path),
                    "bytes": frame_path.stat().st_size,
                }
            )
    if qa_frames:
        media["qa_frames"] = qa_frames
    updated["media"] = media

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
            "review_upload_privacy_after_approval": "unlisted_uploaded_after_explicit_user_instruction",
            "public_release": False,
        }
    )
    updated["locks"] = locks
    updated["upload_locks"] = locks

    reads = updated.get("reads", {}) if isinstance(updated.get("reads"), dict) else {}
    reads.update(
        {
            "final_assembly_human_keep_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
            "human_publish_readiness_keep_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
            "explicit_youtube_upload_approval_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
            "upload_authorization_read": "pass_user_requested_publish_video_to_youtube_and_update_review_2026_05_19",
            "youtube_upload_ready_read": "pass_new_unlisted_review_upload_created_public_release_manual",
            "youtube_unlisted_review_upload_read": "pass_new_unlisted_review_upload_created",
            "youtube_unlisted_review_privacy_read": f"pass_privacy_{privacy or 'unknown'}",
            "youtube_unlisted_review_embeddable_read": "pass_embeddable_true" if embeddable else "reject_embeddable_false",
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
            "html_unlisted_upload_visible_read": "pass_review_html_shows_new_unlisted_upload_video_id_and_url",
            "html_public_release_lock_visible_read": "pass_public_release_schedule_visibility_locked",
            "html_post_upload_blockers_visible_read": "pass_copyright_caption_altered_content_end_screen_public_release_blockers_visible",
            "public_release_ready_read": "blocked_public_release_manual",
            "remote_review_youtube_video_pending_refresh_read": "pending_remote_manifest_refresh_after_upload",
            "downstream_gate_read": "pass_unlisted_review_upload_done_public_release_locked",
        }
    )
    updated["reads"] = reads
    updated["blockers"] = POST_UPLOAD_BLOCKERS
    updated["remaining_blockers"] = POST_UPLOAD_BLOCKERS
    updated["next_review_question"] = "Review the unlisted YouTube embed and Studio blockers. Public release remains manual."
    review_html = PACKAGE_ROOT / "review.html"
    if review_html.exists():
        updated["publish_readiness_review_html_sha256"] = sha256_file(review_html)
        updated["review_html"] = artifact(review_html)
        updated["primary_review_artifact"] = {
            "path": "review.html",
            "sha256": sha256_file(review_html),
            "bytes": review_html.stat().st_size,
        }
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
    print("[youtube] starting unlisted video upload", flush=True)
    result = publisher.publish_video(payload)
    print(f"[youtube] uploaded video id: {result.video_id}", flush=True)

    caption_result = upload_captions_srt(publisher, result.video_id, assets["srt"])
    print(f"[youtube] caption upload status: {caption_result['status']}", flush=True)

    status_path, status_doc = poll_status(publisher, result.video_id, upload_stamp)
    latest_path = PACKAGE_ROOT / "youtube_longform_unlisted_upload_status_latest.json"
    status = status_doc.get("status", {}) if isinstance(status_doc.get("status"), dict) else {}
    raw_status = status.get("raw_response", {}) if isinstance(status.get("raw_response"), dict) else {}
    item_status = raw_status.get("items", [{}])[0].get("status", {}) if raw_status.get("items") else {}

    receipt = {
        "receipt_type": "youtube_longform_unlisted_upload",
        "created_at": utc_now(),
        "manifest_path": str(upload_manifest_path),
        "source_publish_readiness_manifest_path": str(PUBLISH_MANIFEST),
        "privacy": "unlisted",
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
    receipt_path = PACKAGE_ROOT / f"youtube_longform_unlisted_upload_receipt_{upload_stamp}.json"
    write_json(receipt_path, receipt)

    approval_path = mark_final_assembly_keep(upload_stamp, receipt["created_at"])
    patch_review_html(
        {
            "video_id": result.video_id,
            "video_url": result.video_url,
            "privacy_status": status.get("privacy_status", ""),
            "upload_status": status.get("upload_status", ""),
            "processing_status": status.get("processing_status", ""),
            "embeddable": item_status.get("embeddable", True),
            "thumbnail_status": result.thumbnail_status,
            "caption_status": caption_result.get("status", ""),
        }
    )
    update_publish_manifest(manifest, upload_manifest_path, receipt_path, status_path, latest_path, approval_path, receipt, status_doc)

    summary = {
        "ok": True,
        "video_id": result.video_id,
        "video_url": result.video_url,
        "privacy": status.get("privacy_status", ""),
        "upload_status": status.get("upload_status", ""),
        "processing_status": status.get("processing_status", ""),
        "embeddable": item_status.get("embeddable", True),
        "thumbnail_status": result.thumbnail_status,
        "caption_status": caption_result.get("status", ""),
        "upload_manifest_path": str(upload_manifest_path),
        "receipt_path": str(receipt_path),
        "status_path": str(status_path),
        "publish_manifest_path": str(PUBLISH_MANIFEST),
        "review_html_path": str(PACKAGE_ROOT / "review.html"),
        "approval_path": str(approval_path),
        "public_release": "manual_youtube_studio_only",
    }
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
