from __future__ import annotations

import html
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from orchestration.io import Context, utc_now_iso


REMOTE_REVIEW_SITE_URL = "https://cascadeeffects.tv"


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def inception_review_packet_root(context: Context, manifest: dict[str, Any]) -> Path:
    episode_id = str(manifest.get("id", "")).strip()
    episode_info = context.episodes_repo.get_episode_info(episode_id) if episode_id else None
    if episode_info is not None:
        episode_dir = episode_info.directory
    else:
        episode_folder = str(manifest.get("aliases", {}).get("episode_folder", episode_id)).strip() or episode_id
        episode_dir = Path(str(context.channel["paths"]["episodes_root"])) / episode_folder
    return episode_dir / "production" / "long_form_video_v1" / "youtube" / "publish_readiness" / episode_id


def _review_html(manifest: dict[str, Any], review_manifest: dict[str, Any]) -> str:
    title = html.escape(str(manifest.get("title", review_manifest["episode_title"])))
    summary = html.escape(str(manifest.get("summary", "")))
    remote_url = html.escape(str(review_manifest["remote_review"]["remote_review_url"]))
    next_question = html.escape(str(review_manifest["next_review_question"]))
    status = html.escape(str(review_manifest["status"]))
    blockers = "\n".join(f"<li>{html.escape(str(item))}</li>" for item in review_manifest["remaining_blockers"])
    locks = review_manifest["locks"]
    lock_rows = "\n".join(
        f"<tr><th>{html.escape(key)}</th><td>{'false' if value is False else html.escape(str(value))}</td></tr>"
        for key, value in locks.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="robots" content="noindex,nofollow">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} Production Review</title>
  <style>
    :root {{ color-scheme: dark; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; background: #0b1023; color: #fff8e8; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 6vw, 4rem); line-height: 1; text-transform: uppercase; }}
    h2 {{ margin: 0 0 12px; font-size: 1.2rem; }}
    p {{ color: rgba(255, 248, 232, 0.72); line-height: 1.5; }}
    a {{ color: #78dce8; }}
    section {{ margin-top: 18px; padding: 18px; border: 1px solid rgba(255, 248, 232, 0.14); border-radius: 8px; background: rgba(18, 25, 48, 0.9); }}
    .eyebrow {{ margin: 0 0 8px; color: #78dce8; font: 700 0.76rem ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; }}
    .pending {{ min-height: 180px; display: grid; align-content: center; background: linear-gradient(135deg, rgba(120, 220, 232, 0.12), rgba(243, 191, 116, 0.08)), rgba(4, 7, 17, 0.82); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px; border-top: 1px solid rgba(255, 248, 232, 0.12); text-align: left; vertical-align: top; }}
    th {{ color: rgba(255, 248, 232, 0.58); font: 700 0.75rem ui-monospace, SFMono-Regular, Menlo, monospace; }}
  </style>
</head>
<body>
  <main>
    <p class="eyebrow">Episode Inception Review</p>
    <h1>{title}</h1>
    <p>{summary}</p>
    <section class="pending">
      <h2>Review Video Not Attached</h2>
      <p>This local review packet was created at episode inception. The production page starts as a lifecycle review hub; an unlisted YouTube embed is added only after a real review upload exists.</p>
    </section>
    <section>
      <h2>Review Links</h2>
      <p><strong>Status:</strong> {status}</p>
      <p><strong>Production URL:</strong> <a href="{remote_url}">{remote_url}</a></p>
      <p><strong>Next review question:</strong> {next_question}</p>
    </section>
    <section>
      <h2>Locks</h2>
      <table>{lock_rows}</table>
    </section>
    <section>
      <h2>Current Blockers</h2>
      <ul>{blockers}</ul>
    </section>
  </main>
</body>
</html>
"""


def write_inception_review_packet(context: Context, manifest: dict[str, Any]) -> dict[str, Any]:
    episode_id = str(manifest.get("id", "")).strip()
    if not episode_id:
        raise ValueError("Episode manifest is missing id.")

    packet_root = inception_review_packet_root(context, manifest)
    packet_root.mkdir(parents=True, exist_ok=True)
    review_html_path = packet_root / "review.html"
    remote_review_url = f"{REMOTE_REVIEW_SITE_URL}/reviews/publish-readiness/{episode_id}"
    local_review_url = review_html_path.resolve().as_uri()
    now = utc_now_iso()
    review_manifest: dict[str, Any] = {
        "schema_version": 1,
        "lifecycle_stage": "inception",
        "packet_id": episode_id,
        "review_id": episode_id,
        "episode_id": episode_id,
        "episode_title": str(manifest.get("title", episode_id)).strip() or episode_id,
        "created_utc": now,
        "source_packet_path": str(packet_root),
        "status": "inception_review_initialized",
        "human_disposition": "defer",
        "next_review_question": "Review episode inception state, blockers, and next production action.",
        "local_review_url": local_review_url,
        "publish_readiness_review_html_path": str(review_html_path),
        "publish_readiness_canonical_review_url": local_review_url,
        "remote_review": {
            "status": "not_published",
            "review_id": episode_id,
            "remote_review_url": remote_review_url,
            "route": "/reviews/publish-readiness/[reviewId]",
            "site_visibility": "unlisted_noindex",
            "storage_policy": "normalized_manifest_and_small_evidence_assets_only",
            "large_video_upload_allowed": False,
            "video_host": "youtube_unlisted_when_review_video_exists",
            "publish_command": (
                "cd /Users/mike/CascadeEffects/apps/web && "
                f"npm run reviews:publish -- --packet {packet_root} --mode inception --review-id {episode_id}"
            ),
        },
        "youtube_review": {
            "host": "youtube_unlisted",
            "status": "not_uploaded",
            "video_id": "",
            "watch_url": "",
            "embed_url": "",
            "privacy_status": "",
            "processing_status": "pending_review_video",
            "embeddable": None,
            "receipt_path": "",
            "receipt_sha256": "",
            "access_note": "No YouTube review video exists yet; no video is uploaded at episode inception.",
        },
        "metadata": {
            "title": str(manifest.get("title", episode_id)).strip() or episode_id,
            "description": str(manifest.get("summary", "")).strip(),
            "chapters": [],
            "tags": [],
            "hashtags": [],
            "visibility": "unlisted_review_only_when_video_exists",
        },
        "locks": {
            "publish_ready": False,
            "youtube_upload_ready": False,
            "public_release_ready": False,
            "may_youtube_action": False,
            "upload_performed": False,
            "upload_action_enabled_in_review_html": False,
        },
        "expected_artifacts": [
            "final_mp4_after_final_assembly_keep",
            "upload_vtt_or_srt_sidecar",
            "thumbnail_candidate",
            "qa_frames",
            "transition_samples",
            "youtube_metadata_packet",
            "unlisted_youtube_review_receipt",
        ],
        "remaining_blockers": [
            "Episode package gate is not kept.",
            "Visual system, rough assembly, final assembly, and publish readiness are not complete.",
            "No unlisted YouTube review video exists yet.",
            "Public release remains manual and locked.",
        ],
        "reads": {
            "review_inception_packet_read": "pass_local_packet_created_at_bootstrap",
            "remote_review_manifest_read": "pending_remote_review_publish",
            "remote_review_large_video_upload_block_read": "pass_no_video_uploaded_at_inception",
            "youtube_unlisted_review_upload_read": "pending_review_video",
            "youtube_unlisted_review_privacy_read": "pending_review_video",
            "html_upload_lock_read": "pass_no_upload_publish_schedule_or_visibility_controls",
        },
    }
    review_html_path.write_text(_review_html(manifest, review_manifest), encoding="utf-8")
    review_manifest["primary_review_artifact"] = {
        "path": "review.html",
        "sha256": _sha256_path(review_html_path),
        "bytes": review_html_path.stat().st_size,
    }
    manifest_path = packet_root / "publish_readiness_manifest.json"
    manifest_path.write_text(json.dumps(review_manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "packet_root": str(packet_root),
        "manifest_path": str(manifest_path),
        "review_html_path": str(review_html_path),
        "local_review_url": local_review_url,
        "remote_review_url": remote_review_url,
    }


def publish_inception_review_packet(context: Context, packet_root: str | Path, *, review_id: str) -> dict[str, Any]:
    if not os.environ.get("BLOB_READ_WRITE_TOKEN"):
        raise RuntimeError("BLOB_READ_WRITE_TOKEN is required to publish the inception review manifest to Vercel Blob.")

    web_root = Path(str(context.channel["paths"]["web_root"]))
    command = [
        "npm",
        "run",
        "reviews:publish",
        "--",
        "--packet",
        str(packet_root),
        "--mode",
        "inception",
        "--review-id",
        review_id,
    ]
    completed = subprocess.run(command, cwd=web_root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise RuntimeError(detail)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse remote review publish output: {completed.stdout.strip()}") from exc
