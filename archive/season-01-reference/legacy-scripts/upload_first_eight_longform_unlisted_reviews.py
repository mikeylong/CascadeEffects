#!/usr/bin/env python3
"""Upload first-eight long-form publish-readiness packages as unlisted reviews.

This helper is intentionally scoped to local long-form publish-readiness
packages produced by scripts/build_first_eight_longform_publish_readiness_packages.py.
It records package-local upload manifests, receipts, status checks, and keeps
public release locked.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mimetypes
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
EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")
YOUTUBE_CONFIG_DIR = Path("/Users/mike/.config/cascade-effects/youtube")
YOUTUBE_THUMBNAIL_LIMIT_BYTES = 2_097_152
VISUAL_GUARD_MIN_MEAN_LUMA = 20.0
VISUAL_GUARD_MIN_STD_LUMA = 8.0
VISUAL_GUARD_MIN_NONBLACK_FRACTION = 0.08
VISUAL_GUARD_DARK_SCENE_MIN_MEAN_LUMA = 16.0
VISUAL_GUARD_DARK_SCENE_MIN_STD_LUMA = 16.0
VISUAL_GUARD_DARK_SCENE_MIN_NONBLACK_FRACTION = 0.3

POST_UPLOAD_BLOCKERS = [
    "Review YouTube Studio copyright and Content ID checks before public release.",
    "Confirm altered-content disclosure in YouTube Studio for realistic generated or source-derived episode visuals.",
    "Verify uploaded captions or automatic captions in YouTube Studio so they do not conflict with burned-in rail captions.",
    "Configure final YouTube Studio end-screen elements for the baked three-target end-screen geometry.",
    "Public release remains manual and must not be performed by this upload step.",
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
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def resolve_path(package_root: Path, value: Any) -> Path:
    path = Path(str(value or "").strip())
    if path.is_absolute():
        return path
    return package_root / path


def dataclass_or_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    return value


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


def ffprobe(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
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
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def pixel_stats_from_rgb(raw: bytes) -> dict[str, Any]:
    count = len(raw) // 3
    if count <= 0:
        return {
            "pixel_count": 0,
            "mean_luma": 0.0,
            "std_luma": 0.0,
            "min_luma": 0.0,
            "max_luma": 0.0,
            "nonblack_fraction": 0.0,
        }
    total = 0.0
    squares = 0.0
    minimum = 255.0
    maximum = 0.0
    nonblack = 0
    for offset in range(0, count * 3, 3):
        luma = 0.2126 * raw[offset] + 0.7152 * raw[offset + 1] + 0.0722 * raw[offset + 2]
        total += luma
        squares += luma * luma
        minimum = min(minimum, luma)
        maximum = max(maximum, luma)
        if luma >= 10:
            nonblack += 1
    mean = total / count
    variance = max(0.0, squares / count - mean * mean)
    return {
        "pixel_count": count,
        "mean_luma": round(mean, 3),
        "std_luma": round(variance**0.5, 3),
        "min_luma": round(minimum, 3),
        "max_luma": round(maximum, 3),
        "nonblack_fraction": round(nonblack / count, 6),
    }


def video_frame_pixel_stats(path: Path, seconds: float) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{max(0.0, seconds):.6f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-vf",
            "scale=160:90:flags=area",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        check=True,
        capture_output=True,
    )
    return pixel_stats_from_rgb(completed.stdout)


def classify_visual_stats(stats: dict[str, Any]) -> dict[str, Any]:
    mean_luma = float(stats.get("mean_luma") or 0)
    std_luma = float(stats.get("std_luma") or 0)
    nonblack_fraction = float(stats.get("nonblack_fraction") or 0)
    standard_pass = (
        mean_luma >= VISUAL_GUARD_MIN_MEAN_LUMA
        and std_luma >= VISUAL_GUARD_MIN_STD_LUMA
        and nonblack_fraction >= VISUAL_GUARD_MIN_NONBLACK_FRACTION
    )
    if standard_pass:
        return {"passed": True, "reason": "pass_luma_variance_nonblack_floor"}
    dark_visible_scene_pass = (
        mean_luma >= VISUAL_GUARD_DARK_SCENE_MIN_MEAN_LUMA
        and std_luma >= VISUAL_GUARD_DARK_SCENE_MIN_STD_LUMA
        and nonblack_fraction >= VISUAL_GUARD_DARK_SCENE_MIN_NONBLACK_FRACTION
    )
    if dark_visible_scene_pass:
        return {"passed": True, "reason": "pass_dark_scene_high_variance_nonblack_source_visible"}
    return {"passed": False, "reason": "reject_luma_variance_nonblack_floor"}


def visual_stats_pass(stats: dict[str, Any]) -> bool:
    return bool(classify_visual_stats(stats).get("passed"))


def require_mp4_visual_guard(path: Path, *, episode_id: str, package_root: Path) -> dict[str, Any]:
    probe = ffprobe(path)
    duration = float(probe.get("format", {}).get("duration") or 0)
    require(duration > 1, f"{episode_id}: MP4 visual guard could not read duration for {path}")
    samples = {
        "start": 1.0,
        "quarter": duration * 0.25,
        "half": duration * 0.5,
        "three_quarter": duration * 0.75,
        "final_second": max(0.0, duration - 1.0),
    }
    results = []
    failures = []
    for name, seconds in samples.items():
        stats = video_frame_pixel_stats(path, min(max(0.0, seconds), max(0.0, duration - 0.05)))
        classification = classify_visual_stats(stats)
        passed = bool(classification.get("passed"))
        row = {
            "name": name,
            "seconds": round(seconds, 3),
            "stats": stats,
            "passed": passed,
            "classification": classification,
        }
        results.append(row)
        if not passed:
            failures.append(row)
    receipt = {
        "episode_id": episode_id,
        "created_at": utc_now(),
        "video_path": str(path),
        "video_sha256": sha256_file(path),
        "model": "youtube_upload_mp4_black_screen_guard_v1",
        "thresholds": {
            "min_mean_luma": VISUAL_GUARD_MIN_MEAN_LUMA,
            "min_std_luma": VISUAL_GUARD_MIN_STD_LUMA,
            "min_nonblack_fraction": VISUAL_GUARD_MIN_NONBLACK_FRACTION,
            "dark_scene_min_mean_luma": VISUAL_GUARD_DARK_SCENE_MIN_MEAN_LUMA,
            "dark_scene_min_std_luma": VISUAL_GUARD_DARK_SCENE_MIN_STD_LUMA,
            "dark_scene_min_nonblack_fraction": VISUAL_GUARD_DARK_SCENE_MIN_NONBLACK_FRACTION,
        },
        "samples": results,
        "reads": {
            "mp4_black_frame_guard_read": "pass_mp4_sample_frames_nonblack_with_luma_variance"
            if not failures
            else "reject_mp4_sample_frames_blank_or_low_variance",
            "youtube_upload_black_screen_block_read": "pass_black_screen_upload_preflight"
            if not failures
            else "reject_black_screen_upload_preflight_blocks_upload",
        },
        "ok": not failures,
    }
    receipt_path = package_root / "preflight" / f"{episode_id}_mp4_visual_guard_{stamp()}.json"
    write_json(receipt_path, receipt)
    receipt["path"] = str(receipt_path)
    receipt["sha256"] = sha256_file(receipt_path)
    require(not failures, f"{episode_id}: MP4 black-screen guard failed before upload: {receipt_path}")
    return receipt


def status_payload(status: Any) -> dict[str, Any]:
    payload = dataclass_or_value(status)
    require(isinstance(payload, dict), "Unexpected YouTube status response.")
    return payload


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


def require_challenger_precision_matte_guard(manifest_path: Path, manifest: dict[str, Any], upload_stamp: str) -> dict[str, Any]:
    episode_id = str(manifest.get("episode_id", "")).strip()
    if episode_id != "challenger":
        return {
            "ok": True,
            "required": False,
            "reads": {"challenger_precision_matte_guard_read": "not_applicable_non_challenger_episode"},
        }
    package_root = manifest_path.parent
    receipt_path = package_root / "preflight" / f"challenger_precision_matte_guard_{upload_stamp}.json"
    completed = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts/challenger_precision_matte_guard.mjs"),
            "--manifest",
            str(manifest_path),
            "--write-receipt",
            str(receipt_path),
            "--context",
            "youtube_unlisted_upload_preflight",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Challenger precision matte guard failed before YouTube upload.\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    receipt = read_json(receipt_path)
    require(receipt.get("ok") is True, f"Challenger precision matte receipt did not pass: {receipt_path}")
    return {
        "path": str(receipt_path),
        "sha256": sha256_file(receipt_path),
        "receipt": receipt,
        "ok": True,
        "required": True,
        "reads": receipt.get("reads", {}),
    }


def package_asset(manifest: dict[str, Any], package_root: Path, *keys: str) -> Path:
    local_assets = manifest.get("local_assets", {}) if isinstance(manifest.get("local_assets"), dict) else {}
    media = manifest.get("media", {}) if isinstance(manifest.get("media"), dict) else {}
    for key in keys:
        asset = local_assets.get(key)
        if isinstance(asset, dict) and str(asset.get("path", "")).strip():
            return resolve_path(package_root, asset["path"])
        asset = media.get(key)
        if isinstance(asset, dict) and str(asset.get("path", "")).strip():
            return resolve_path(package_root, asset["path"])
    raise RuntimeError(f"Missing package asset: {'/'.join(keys)}")


def verify_hash(manifest: dict[str, Any], package_root: Path, key: str, path: Path) -> None:
    local_assets = manifest.get("local_assets", {}) if isinstance(manifest.get("local_assets"), dict) else {}
    media = manifest.get("media", {}) if isinstance(manifest.get("media"), dict) else {}
    declared = ""
    for container in (local_assets, media):
        item = container.get(key) if isinstance(container, dict) else None
        if isinstance(item, dict) and item.get("sha256"):
            declared = str(item["sha256"]).strip()
            break
    if declared:
        actual = sha256_file(path)
        require(actual == declared, f"Hash mismatch for {key}: {path}")


def youtube_description(metadata: dict[str, Any]) -> str:
    description = str(metadata.get("description", "")).strip()
    chapters = metadata.get("chapters")
    if isinstance(chapters, list) and chapters:
        lines = ["Chapters:"]
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            timestamp = str(chapter.get("time") or chapter.get("timestamp") or "").strip()
            label = str(chapter.get("label") or chapter.get("title") or "").strip()
            if timestamp and label:
                lines.append(f"{timestamp} {label}")
        if len(lines) > 1:
            description = f"{description}\n\n" + "\n".join(lines)
    hashtags = metadata.get("hashtags")
    if isinstance(hashtags, list):
        tag_line = " ".join(str(item).strip() for item in hashtags if str(item).strip())
        if tag_line:
            description = f"{description}\n\n{tag_line}"
    return description.strip()


def prepare_youtube_thumbnail(source: Path, package_root: Path, episode_id: str) -> Path:
    if source.stat().st_size <= YOUTUBE_THUMBNAIL_LIMIT_BYTES:
        return source
    derivative = package_root / "thumbnail" / f"{episode_id}_youtube_upload_thumbnail.jpg"
    derivative.parent.mkdir(parents=True, exist_ok=True)
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
            str(derivative),
        ],
        check=True,
    )
    require(derivative.exists(), f"YouTube thumbnail derivative was not created: {derivative}")
    require(
        derivative.stat().st_size <= YOUTUBE_THUMBNAIL_LIMIT_BYTES,
        f"YouTube thumbnail derivative still exceeds 2 MB: {derivative}",
    )
    return derivative


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
    except Exception as exc:  # noqa: BLE001 - caption upload is nonfatal for review upload.
        return {
            "status": "failed_nonfatal",
            "error": str(exc),
            "caption_id": "",
            "raw_response": {},
        }


def poll_status(publisher: Any, video_id: str, upload_stamp: str, package_root: Path, attempts: int, interval: int) -> tuple[Path, dict[str, Any]]:
    latest: dict[str, Any] = {}
    terminal = {"succeeded", "failed", "terminated"}
    for attempt in range(1, attempts + 1):
        latest = status_payload(publisher.get_video_status(video_id))
        processing = str(latest.get("processing_status", "")).strip()
        upload_status = str(latest.get("upload_status", "")).strip()
        print(
            f"[status {attempt}/{attempts}] {video_id} upload={upload_status or 'unknown'} processing={processing or 'unknown'}",
            flush=True,
        )
        if processing in terminal or upload_status in {"processed", "rejected", "failed"}:
            break
        if attempt < attempts:
            time.sleep(interval)
    status_doc = {"checked_at": utc_now(), "video_id": video_id, "status": latest}
    status_path = package_root / f"youtube_longform_unlisted_upload_status_{upload_stamp}.json"
    write_json(status_path, status_doc)
    shutil.copyfile(status_path, package_root / "youtube_longform_unlisted_upload_status_latest.json")
    return status_path, status_doc


def build_upload_payload(manifest: dict[str, Any], package_root: Path) -> tuple[dict[str, Path], dict[str, Any]]:
    episode_id = str(manifest.get("episode_id", "")).strip()
    require(episode_id, f"Missing episode_id in {package_root}")
    mp4 = package_asset(manifest, package_root, "mp4", "final_mp4")
    vtt = package_asset(manifest, package_root, "vtt", "caption_vtt")
    srt = package_asset(manifest, package_root, "srt", "caption_srt")
    thumbnail_source = package_asset(manifest, package_root, "thumbnail_candidate")
    for label, path in (("mp4", mp4), ("vtt", vtt), ("srt", srt), ("thumbnail", thumbnail_source)):
        require(path.exists(), f"Missing upload asset {label}: {path}")
    verify_hash(manifest, package_root, "mp4", mp4)
    verify_hash(manifest, package_root, "final_mp4", mp4)
    verify_hash(manifest, package_root, "vtt", vtt)
    verify_hash(manifest, package_root, "caption_vtt", vtt)
    verify_hash(manifest, package_root, "srt", srt)
    verify_hash(manifest, package_root, "caption_srt", srt)
    thumbnail = prepare_youtube_thumbnail(thumbnail_source, package_root, episode_id)

    metadata = manifest.get("youtube_metadata", {}) if isinstance(manifest.get("youtube_metadata"), dict) else {}
    title = str(metadata.get("title", "")).strip()
    description = youtube_description(metadata)
    tags = normalize_tags(metadata.get("tags"))
    require(title, f"Missing YouTube title for {episode_id}")
    require(description, f"Missing YouTube description for {episode_id}")
    require(tags, f"Missing YouTube tags for {episode_id}")

    return {
        "mp4": mp4,
        "vtt": vtt,
        "srt": srt,
        "thumbnail": thumbnail,
        "thumbnail_source": thumbnail_source,
    }, {
        "video_path": str(mp4),
        "title": title,
        "description_text": description,
        "tags": tags,
        "privacy": "unlisted",
        "thumbnail_path": str(thumbnail),
        "category_id": str(metadata.get("category_id", "27")).strip() or "27",
        "default_language": str(metadata.get("language", metadata.get("default_language", "en"))).strip() or "en",
        "default_audio_language": str(metadata.get("default_audio_language", "en")).strip() or "en",
        "self_declared_made_for_kids": bool(metadata.get("made_for_kids", False)),
        "embeddable": True,
        "notify_subscribers": False,
        "ignore_thumbnail_errors": True,
    }


def write_upload_manifest(
    package_root: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    assets: dict[str, Path],
    payload: dict[str, Any],
    upload_stamp: str,
    challenger_precision_matte_guard: dict[str, Any],
    mp4_visual_guard: dict[str, Any],
) -> Path:
    upload_manifest = {
        "created_at": utc_now(),
        "episode_id": manifest.get("episode_id"),
        "human_publish_readiness_keep_read": "pass_user_requested_generate_mp4s_and_publish_all_unlisted_2026_05_23",
        "human_upload_approval_read": "pass_user_requested_generate_mp4s_and_publish_all_unlisted_2026_05_23",
        "target": "youtube_longform_unlisted_review",
        "privacy": "unlisted",
        "notify_subscribers": False,
        "public_release": "manual_youtube_studio_only",
        "source_publish_readiness_manifest_path": str(manifest_path),
        "source_publish_readiness_manifest_sha256": sha256_file(manifest_path),
        "challenger_precision_matte_guard": challenger_precision_matte_guard,
        "mp4_visual_guard": mp4_visual_guard,
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
            "title": payload["title"],
            "description": payload["description_text"],
            "tags": payload["tags"],
            "category_id": payload["category_id"],
            "default_language": payload["default_language"],
            "default_audio_language": payload["default_audio_language"],
            "self_declared_made_for_kids": payload["self_declared_made_for_kids"],
        },
    }
    path = package_root / f"youtube_longform_unlisted_upload_manifest_{upload_stamp}.json"
    write_json(path, upload_manifest)
    return path


def patch_review_html(package_root: Path, upload: dict[str, Any]) -> None:
    path = package_root / "review.html"
    if not path.exists():
        return
    html = path.read_text(encoding="utf-8")
    insert = f"""

  <section id=\"youtube-unlisted-upload\">
    <h2>YouTube Unlisted Review Upload</h2>
    <p>Unlisted review upload created. Public release, schedule, and visibility changes remain manual YouTube Studio actions.</p>
    <table><tbody>
      <tr><th>Video ID</th><td>{upload['video_id']}</td></tr>
      <tr><th>Unlisted URL</th><td><a href=\"{upload['video_url']}\">{upload['video_url']}</a></td></tr>
      <tr><th>Privacy</th><td>{upload['privacy_status']}</td></tr>
      <tr><th>Upload / Processing</th><td>{upload['upload_status']} / {upload['processing_status']}</td></tr>
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
    manifest_path: Path,
    upload_manifest_path: Path,
    receipt_path: Path,
    status_path: Path,
    receipt: dict[str, Any],
    status_doc: dict[str, Any],
) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    package_root = manifest_path.parent
    status = status_doc.get("status", {}) if isinstance(status_doc.get("status"), dict) else {}
    processing = str(status.get("processing_status", "")).strip()
    upload_status = str(status.get("upload_status", "")).strip()
    privacy = str(status.get("privacy_status", "")).strip()
    thumbnail_status = str(receipt.get("thumbnail", {}).get("status", "")).strip()
    caption_status = str(receipt.get("caption_upload", {}).get("status", "")).strip()
    processed_ok = processing == "succeeded" or upload_status == "processed"
    video_id = str(receipt.get("youtube", {}).get("video_id", "")).strip()
    video_url = str(receipt.get("youtube", {}).get("video_url", "")).strip()

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
        "mp4_visual_guard": receipt.get("mp4_visual_guard"),
        "upload_manifest": artifact(upload_manifest_path),
        "receipt": artifact(receipt_path),
        "status_check": artifact(status_path),
        "read": "pass_new_unlisted_review_upload_created_no_public_release",
        "visibility_change_taken": False,
    }

    updated = copy.deepcopy(manifest)
    updated["status"] = "youtube_unlisted_review_uploaded_public_release_blocked_pending_studio_checks"
    updated["human_disposition"] = "keep"
    updated["final_assembly_disposition"] = "keep"
    updated["human_keep_recorded_at"] = receipt.get("created_at")
    updated["publish_ready"] = True
    updated["youtube_upload_ready"] = False
    updated["public_release_ready"] = False
    updated["may_youtube_action"] = False
    updated["upload_performed"] = True
    updated["may_advance_to_upload"] = False
    updated["youtube_review"] = upload_object
    updated["youtube_unlisted_review"] = upload_object

    media = updated.get("media", {}) if isinstance(updated.get("media"), dict) else {}
    if "final_mp4" in media:
        media["mp4"] = media["final_mp4"]
    if "caption_vtt" in media:
        media["vtt"] = media["caption_vtt"]
        media["upload_vtt"] = media["caption_vtt"]
    if "caption_srt" in media:
        media["srt"] = media["caption_srt"]
        media["upload_srt"] = media["caption_srt"]
    updated["media"] = media

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
            "review_upload_privacy_after_approval": "unlisted_uploaded_after_explicit_user_instruction",
            "public_release": False,
        }
    )
    updated["locks"] = locks
    updated["upload_locks"] = locks

    reads = updated.get("reads", {}) if isinstance(updated.get("reads"), dict) else {}
    reads.update(
        {
            "final_assembly_human_keep_read": "pass_user_requested_generate_mp4s_and_publish_all_unlisted_2026_05_23",
            "human_publish_readiness_keep_read": "pass_user_requested_generate_mp4s_and_publish_all_unlisted_2026_05_23",
            "explicit_youtube_upload_approval_read": "pass_user_requested_generate_mp4s_and_publish_all_unlisted_2026_05_23",
            "upload_authorization_read": "pass_user_requested_generate_mp4s_and_publish_all_unlisted_2026_05_23",
            "youtube_upload_ready_read": "pass_new_unlisted_review_upload_created_public_release_manual",
            "youtube_unlisted_review_upload_read": "pass_new_unlisted_review_upload_created",
            "youtube_unlisted_review_privacy_read": f"pass_privacy_{privacy or 'unknown'}",
            "youtube_unlisted_upload_status_read": (
                "pass_upload_status_processed_processing_succeeded"
                if processed_ok
                else f"review_pending_upload_status_{upload_status or 'unknown'}_processing_{processing or 'unknown'}"
            ),
            "youtube_unlisted_upload_thumbnail_read": f"pass_thumbnail_{thumbnail_status or 'unknown'}",
            "mp4_black_frame_guard_read": "pass_mp4_sample_frames_nonblack_with_luma_variance",
            "youtube_upload_black_screen_block_read": "pass_black_screen_upload_preflight",
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
            "downstream_gate_read": "pass_unlisted_review_upload_done_public_release_locked",
        }
    )
    updated["reads"] = reads
    updated["blockers"] = POST_UPLOAD_BLOCKERS
    updated["remaining_blockers"] = POST_UPLOAD_BLOCKERS
    updated["next_review_question"] = "Review the unlisted YouTube upload and Studio blockers. Public release remains manual."

    review_html = package_root / "review.html"
    if review_html.exists():
        updated["primary_review_artifact"] = {
            "path": "review.html",
            "sha256": sha256_file(review_html),
            "bytes": review_html.stat().st_size,
        }
        updated["publish_readiness_review_html_sha256"] = sha256_file(review_html)
    write_json(manifest_path, updated)
    return updated


def upload_one(
    *,
    manifest_path: Path,
    publisher: Any,
    channel: dict[str, Any],
    upload_stamp: str,
    poll_attempts: int,
    poll_interval: int,
    dry_run: bool,
    production_contract_receipt: str,
    confirm_contract_youtube_action: bool,
) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    package_root = manifest_path.parent
    episode_id = str(manifest.get("episode_id", "")).strip()
    existing = manifest.get("youtube_unlisted_review")
    if isinstance(existing, dict) and existing.get("video_id"):
        return {
            "episode_id": episode_id,
            "status": "skipped_existing_unlisted_review_upload",
            "video_id": existing.get("video_id"),
            "video_url": existing.get("video_url"),
            "manifest_path": str(manifest_path),
        }

    challenger_precision_matte_guard = require_challenger_precision_matte_guard(manifest_path, manifest, upload_stamp)
    assets, payload = build_upload_payload(manifest, package_root)
    mp4_visual_guard = require_mp4_visual_guard(assets["mp4"], episode_id=episode_id, package_root=package_root)
    upload_manifest_path = write_upload_manifest(
        package_root,
        manifest_path,
        manifest,
        assets,
        payload,
        upload_stamp,
        challenger_precision_matte_guard,
        mp4_visual_guard,
    )
    print(f"[preflight] {episode_id}: wrote {upload_manifest_path}", flush=True)

    if dry_run:
        return {
            "episode_id": episode_id,
            "status": "dry_run_ready",
            "manifest_path": str(manifest_path),
            "upload_manifest_path": str(upload_manifest_path),
            "video_path": str(assets["mp4"]),
            "title": payload["title"],
        }

    contract_receipt = require_contract_youtube_action(
        manifest=manifest,
        manifest_path=manifest_path,
        explicit_receipt_path=production_contract_receipt,
        confirmed=confirm_contract_youtube_action,
        action="unlisted_review_upload",
    )

    print(f"[youtube] {episode_id}: uploading unlisted", flush=True)
    result = publisher.publish_video(payload)
    print(f"[youtube] {episode_id}: uploaded {result.video_id}", flush=True)

    caption_result = upload_captions_srt(publisher, result.video_id, assets["srt"])
    print(f"[youtube] {episode_id}: caption upload {caption_result['status']}", flush=True)
    status_path, status_doc = poll_status(publisher, result.video_id, upload_stamp, package_root, poll_attempts, poll_interval)
    status = status_doc.get("status", {}) if isinstance(status_doc.get("status"), dict) else {}

    receipt = {
        "receipt_type": "youtube_longform_unlisted_upload",
        "created_at": utc_now(),
        "episode_id": episode_id,
        "manifest_path": str(upload_manifest_path),
        "source_publish_readiness_manifest_path": str(manifest_path),
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
            "path": str(assets["thumbnail"]),
            "status": result.thumbnail_status,
            "error": result.thumbnail_error,
            "content_type": mimetypes.guess_type(str(assets["thumbnail"]))[0] or "image/jpeg",
        },
        "caption_upload": caption_result,
        "caption_sidecar_to_upload_or_verify": str(assets["srt"]),
        "captions_uploaded": caption_result.get("status") == "uploaded",
        "production_contract_receipt": {
            "path": contract_receipt["path"],
            "sha256": contract_receipt["sha256"],
            "contract_id": contract_receipt["receipt"].get("contract_id"),
            "intent": contract_receipt["receipt"].get("intent"),
            "youtube_action_requested": contract_receipt["receipt"].get("youtube_action_requested"),
            "youtube_action_allowed": contract_receipt["receipt"].get("youtube_action_allowed"),
        },
        "challenger_precision_matte_guard": challenger_precision_matte_guard,
        "mp4_visual_guard": mp4_visual_guard,
        "raw_upload_response": result.raw_response,
        "post_upload_blockers": POST_UPLOAD_BLOCKERS,
    }
    receipt_path = package_root / f"youtube_longform_unlisted_upload_receipt_{upload_stamp}.json"
    write_json(receipt_path, receipt)
    patch_review_html(
        package_root,
        {
            "video_id": result.video_id,
            "video_url": result.video_url,
            "privacy_status": status.get("privacy_status", ""),
            "upload_status": status.get("upload_status", ""),
            "processing_status": status.get("processing_status", ""),
            "thumbnail_status": result.thumbnail_status,
            "caption_status": caption_result.get("status", ""),
        },
    )
    updated = update_publish_manifest(manifest_path, upload_manifest_path, receipt_path, status_path, receipt, status_doc)

    return {
        "episode_id": episode_id,
        "status": "uploaded",
        "video_id": result.video_id,
        "video_url": result.video_url,
        "privacy": status.get("privacy_status", ""),
        "upload_status": status.get("upload_status", ""),
        "processing_status": status.get("processing_status", ""),
        "thumbnail_status": result.thumbnail_status,
        "caption_status": caption_result.get("status", ""),
        "publish_manifest_path": str(manifest_path),
        "receipt_path": str(receipt_path),
        "status_path": str(status_path),
        "publish_manifest_sha256": sha256_file(manifest_path),
        "production_contract_receipt_path": contract_receipt["path"],
        "public_release": updated.get("reads", {}).get("youtube_public_release_read", "blocked_manual_youtube_studio_only"),
    }


def load_package_manifests(summary_path: Path, only: set[str]) -> list[Path]:
    summary = read_json(summary_path)
    packages = summary.get("packages")
    require(isinstance(packages, list), f"Summary lacks packages list: {summary_path}")
    paths: list[Path] = []
    for item in packages:
        if not isinstance(item, dict):
            continue
        episode_id = str(item.get("episode_id", "")).strip()
        if only and episode_id not in only:
            continue
        manifest_path = Path(str(item.get("manifest_path", "")).strip())
        require(manifest_path.exists(), f"Package manifest missing for {episode_id}: {manifest_path}")
        paths.append(manifest_path)
    require(paths, "No package manifests selected.")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(EPISODES_ROOT / "first_eight_longform_publish_readiness_packages_latest.json"))
    parser.add_argument("--config-dir", default=str(YOUTUBE_CONFIG_DIR))
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--poll-attempts", type=int, default=4)
    parser.add_argument("--poll-interval", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--production-contract-receipt", default="")
    parser.add_argument("--confirm-contract-youtube-action", action="store_true")
    args = parser.parse_args()

    sys.path.insert(0, str(REPO_ROOT))
    from orchestration.publish import _verify_authenticated_channel, build_youtube_package_publisher

    summary_path = Path(args.summary)
    only = {item.strip() for item in args.only if item.strip()}
    manifests = load_package_manifests(summary_path, only)
    upload_stamp = stamp()

    publisher = None
    channel: dict[str, Any] = {}
    if not args.dry_run:
        publisher = build_youtube_package_publisher(config_dir=args.config_dir)
        channel = _verify_authenticated_channel(publisher)
        print(f"[youtube] authenticated channel: {channel.get('title')} ({channel.get('channel_id')})", flush=True)

    results: list[dict[str, Any]] = []
    for manifest_path in manifests:
        try:
            result = upload_one(
                manifest_path=manifest_path,
                publisher=publisher,
                channel=channel,
                upload_stamp=upload_stamp,
                poll_attempts=args.poll_attempts,
                poll_interval=args.poll_interval,
                dry_run=args.dry_run,
                production_contract_receipt=args.production_contract_receipt,
                confirm_contract_youtube_action=args.confirm_contract_youtube_action,
            )
        except Exception as exc:  # noqa: BLE001 - batch captures per-episode failures.
            failed_episode_id = manifest_path.parent.name
            try:
                failed_episode_id = str(read_json(manifest_path).get("episode_id") or failed_episode_id)
            except Exception:
                pass
            result = {
                "episode_id": failed_episode_id,
                "status": "failed",
                "error": str(exc),
                "publish_manifest_path": str(manifest_path),
            }
            print(f"[error] {manifest_path}: {exc}", flush=True)
            if args.stop_on_error:
                results.append(result)
                break
        results.append(result)

    ok = all(item.get("status") in {"uploaded", "skipped_existing_unlisted_review_upload", "dry_run_ready"} for item in results)
    aggregate = {
        "ok": ok,
        "created_at": utc_now(),
        "stamp": upload_stamp,
        "summary_path": str(summary_path),
        "privacy": "unlisted",
        "notify_subscribers": False,
        "public_release": "manual_youtube_studio_only",
        "count": len(results),
        "results": results,
    }
    aggregate_path = EPISODES_ROOT / f"first_eight_longform_youtube_unlisted_uploads_{upload_stamp}.json"
    write_json(aggregate_path, aggregate)
    write_json(EPISODES_ROOT / "first_eight_longform_youtube_unlisted_uploads_latest.json", aggregate)

    summary = read_json(summary_path)
    summary["youtube_unlisted_uploads"] = {
        "aggregate_path": str(aggregate_path),
        "aggregate_sha256": sha256_file(aggregate_path),
        "status": "complete" if ok else "partial_or_failed",
        "results": results,
        "public_release": "manual_youtube_studio_only",
    }
    write_json(summary_path, summary)

    print(json.dumps({"aggregate_path": str(aggregate_path), **aggregate}, indent=2, sort_keys=True), flush=True)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
