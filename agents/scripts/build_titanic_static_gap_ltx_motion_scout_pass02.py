#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


EPISODE_ID = "titanic"
SHORT_ID = "titanic_short_scoped_v1"
PASS_ID = "static_gap_ltx_motion_scout_pass_02"
OUTPUT_SLUG = "pass_02_static_gap_apple_distilled"

PRODUCTION_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1/production"
)
VIZ_SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/titanic_short_scoped_v1"
)
SOURCE_PROOF_MANIFEST = VIZ_SHORT_ROOT / (
    "stills_video_proof/pass_01_event_led_static/"
    "titanic_event_led_stills_video_proof_manifest_pass_01.json"
)
SOURCE_CONTACT_MANIFEST = VIZ_SHORT_ROOT / (
    "stills_contact_sheet/pass_03_event_led_shot_lock/"
    "titanic_event_led_shot_lock_manifest_pass_03.json"
)
SOURCE_MOTION_PROOF_MANIFEST = VIZ_SHORT_ROOT / (
    "motion_video_proof/pass_01_ltx_hybrid/"
    "titanic_motion_video_proof_pass_01_ltx_hybrid_manifest.json"
)
OUTPUT_ROOT = VIZ_SHORT_ROOT / "motion_contact_sheet" / OUTPUT_SLUG

DP_SCOPE_PATH = PRODUCTION_ROOT / "dp_motion_scope_decision_ltx_static_gap_pass_02.md"
RENDER_AUTH_PATH = PRODUCTION_ROOT / "render_authorization_check_ltx_static_gap_pass_02.md"
REQUEST_PATH = PRODUCTION_ROOT / "ltx_motion_scout_request_pass_02_static_gap_apple_distilled.md"
REVIEW_PATH = PRODUCTION_ROOT / "motion_contact_sheet_review_ltx_static_gap_pass_02.md"
HANDOFF_PATH = PRODUCTION_ROOT / "motion_contact_sheet_handoff_ltx_static_gap_pass_02.yaml"

VIZ_ROOT = Path("/Users/mike/Viz_CascadeEffects")
HANDOFF_STAGE = VIZ_ROOT / "scripts/handoff-stage.sh"
HANDOFF_I2V = VIZ_ROOT / "scripts/handoff-i2v.sh"

FPS = 24
FRAME_COUNT = 121
TARGET_SECONDS = 5.0
WIDTH = 576
HEIGHT = 1024

APPLE_PIPELINE = "apple-ltx23-q8-one-stage"
APPLE_MODEL_REPO = "dgrauet/ltx-2.3-mlx-q8"
APPLE_TEXT_ENCODER_REPO = "mlx-community/gemma-3-12b-it-4bit"
DISTILLED_PIPELINE = "distilled"
DISTILLED_MODEL_REPO = "mlx-community/LTX-2-distilled-bf16"

STATIC_GAP_SHOT_IDS = ["shot_03", "shot_04", "shot_07", "shot_08", "shot_09", "shot_10"]
CONTROL_KEEP_MOTION_SHOT_IDS = ["shot_00", "shot_01", "shot_02", "shot_05", "shot_06", "shot_11"]


@dataclass(frozen=True)
class ScoutShot:
    shot_id: str
    role: str
    seed: int
    motion_intent: str
    reject_if: str
    prompt: str


@dataclass(frozen=True)
class CandidateSpec:
    variant_id: str
    label: str
    motion_pipeline: str
    model_repo: str
    text_encoder_repo: str


SCOUT_SHOTS = [
    ScoutShot(
        shot_id="shot_03",
        role="Carpathia lifeboat regulation table beat",
        seed=850301,
        motion_intent="gentle water bob, tiny fog drift, film weave; boats and people locked",
        reject_if="added boats, changed people count, face/body drift, changed rail or lifeboat geometry",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the Carpathia rescue lifeboat "
            "photograph composition fixed, preserving the ship rail, lifeboat positions, people "
            "count, faces, postures, ropes, and monochrome period texture. Add only gentle water "
            "bob, tiny fog drift, faint film weave, and an almost locked camera. No new people, "
            "no face changes, no body motion, no added boats, no evacuation action, no text, no logos."
        ),
    ),
    ScoutShot(
        shot_id="shot_04",
        role="Carpathia lifeboats and collapsibles beat",
        seed=850401,
        motion_intent="subtle water motion and film texture; all people, boats, and ship details fixed",
        reject_if="new people, new boats, identity drift, boat reshaping, or hidden text/logo leakage",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the lifeboat rescue photograph "
            "composition fixed, preserving boat count, people count, seated and standing postures, "
            "ship-side geometry, ropes, and archival monochrome texture. Add only slight water "
            "movement, faint haze, restrained film weave, and a nearly imperceptible camera creep. "
            "No new people, no face/body drift, no added boats, no boat reshaping, no text, no logos."
        ),
    ),
    ScoutShot(
        shot_id="shot_07",
        role="underfilled lifeboat close beat",
        seed=850701,
        motion_intent="low-amplitude water bob only; human identities and boat geometry locked",
        reject_if="face/body drift, posture changes, changed occupancy, oar drift, or boat deformation",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the close lifeboat survivor photograph "
            "locked, preserving the exact people count, faces, seated postures, oars, boat rim, waterline, "
            "and period texture. Add only a tiny water bob and faint film weave already implied by the "
            "still. No new people, no facial changes, no posture changes, no oar motion, no boat reshaping, "
            "no added boats, no text, no logos."
        ),
    ),
    ScoutShot(
        shot_id="shot_08",
        role="investigation aftermath survivor crowd beat",
        seed=850801,
        motion_intent="restrained parallax and film weave; crowd identity and room/ship context locked",
        reject_if="crowd count changes, face drift, body motion, new props, text, logos, or modern AI sheen",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the Carpathia survivor aftermath photograph "
            "composition fixed, preserving crowd count, faces, body positions, clothing silhouettes, ship or "
            "deck context, and monochrome archival texture. Add only restrained parallax, tiny haze, and "
            "subtle film weave from a locked documentary camera. No new people, no face/body drift, no "
            "restaging, no new props, no text, no logos, no modern color."
        ),
    ),
    ScoutShot(
        shot_id="shot_09",
        role="lifeboat at sea rule-correction beat",
        seed=850901,
        motion_intent="subtle sea shimmer and lifeboat bob; occupants and boat count locked",
        reject_if="new boats, changed person count, body drift, oar/boat deformation, or invented rescue action",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the lifeboat-at-sea photograph fixed, "
            "preserving the exact lifeboat silhouette, people count, seated postures, oars, horizon, and "
            "archival monochrome texture. Add only subtle sea shimmer, a small lifeboat bob, and faint film "
            "weave. No new boats, no new people, no face/body changes, no oar movement, no rescue action, "
            "no text, no logos."
        ),
    ),
    ScoutShot(
        shot_id="shot_10",
        role="SOLAS survivor aftermath beat",
        seed=851001,
        motion_intent="tiny atmospheric drift and parallax; crowd and source identity locked",
        reject_if="face/body drift, changed crowd count, new signage, text/logo leakage, or modernized texture",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the survivor aftermath photograph composition "
            "fixed, preserving people count, faces, postures, clothing, ship/deck context, and period texture. "
            "Add only tiny atmospheric drift, subtle film weave, and restrained parallax from a locked camera. "
            "No new people, no face changes, no body motion, no new signs, no text, no logos, no modern color."
        ),
    ),
]

CANDIDATE_SPECS = [
    CandidateSpec(
        variant_id="apple",
        label="Apple LTX 2.3 q8 one-stage",
        motion_pipeline=APPLE_PIPELINE,
        model_repo=APPLE_MODEL_REPO,
        text_encoder_repo=APPLE_TEXT_ENCODER_REPO,
    ),
    CandidateSpec(
        variant_id="distilled",
        label="LTX 2 distilled bf16",
        motion_pipeline=DISTILLED_PIPELINE,
        model_repo=DISTILLED_MODEL_REPO,
        text_encoder_repo="",
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def run_logged(command: list[str], log_path: Path, *, cwd: Path | None = None) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("$ " + " ".join(command) + "\n\n")
        log_file.flush()
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return completed.returncode


def ffprobe_duration(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return 0.0
    try:
        return float(completed.stdout.strip())
    except ValueError:
        return 0.0


def ffprobe_video_info(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,codec_name",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return {}
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {}
    streams = data.get("streams") or []
    return streams[0] if streams else {}


def has_audio_stream(path: Path) -> bool:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0 and bool(completed.stdout.strip())


def normalize_no_audio(raw_path: Path, normalized_path: Path, log_path: Path) -> bool:
    if normalized_path.exists():
        return True
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(raw_path),
        "-map",
        "0:v:0",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-an",
        "-movflags",
        "+faststart",
        str(normalized_path),
    ]
    return run_logged(command, log_path) == 0 and normalized_path.exists()


def extract_audit_frames(video_path: Path, output_dir: Path, log_path: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(output_dir.glob("frame_*.png"))
    if len(existing) >= 8:
        return existing
    for path in existing:
        path.unlink()
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        "fps=2,scale=160:284:force_original_aspect_ratio=decrease,pad=160:284:(ow-iw)/2:(oh-ih)/2:black",
        str(output_dir / "frame_%03d.png"),
    ]
    if run_logged(command, log_path) != 0:
        return []
    return sorted(output_dir.glob("frame_*.png"))


def validate_source_manifests() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    proof = read_json(SOURCE_PROOF_MANIFEST)
    contact = read_json(SOURCE_CONTACT_MANIFEST)
    motion_proof = read_json(SOURCE_MOTION_PROOF_MANIFEST)
    proof_by_id = {item["shot_id"]: item for item in proof["shots"]}
    contact_by_id = {item["shot_id"]: item for item in contact["shots"]}
    motion_by_id = {item["shot_id"]: item for item in motion_proof["story_shots"]}

    rows: list[dict[str, Any]] = []
    for scout in SCOUT_SHOTS:
        proof_item = proof_by_id[scout.shot_id]
        contact_item = contact_by_id[scout.shot_id]
        motion_item = motion_by_id[scout.shot_id]
        source_still = Path(proof_item["image"])
        clean_candidate = Path(contact_item["clean_candidate_path"])
        if source_still != clean_candidate:
            raise RuntimeError(f"{scout.shot_id}: proof image and clean candidate differ")
        if not source_still.exists():
            raise RuntimeError(f"{scout.shot_id}: missing source still {source_still}")
        source_sha = sha256_file(source_still)
        expected_sha = str(contact_item.get("clean_candidate_sha256", ""))
        if expected_sha and source_sha != expected_sha:
            raise RuntimeError(f"{scout.shot_id}: clean candidate hash mismatch")
        if motion_item.get("source_kind") != "direct_source_still_hold":
            raise RuntimeError(f"{scout.shot_id}: expected current proof to use direct_source_still_hold")
        rows.append(
            {
                "shot_id": scout.shot_id,
                "source_still_path": str(source_still),
                "source_still_sha256": source_sha,
                "role": scout.role,
                "seed": scout.seed,
                "motion_intent": scout.motion_intent,
                "reject_if": scout.reject_if,
                "prompt": scout.prompt,
                "proof_duration_seconds": float(proof_item["duration"]),
                "proof_start": float(motion_item["proof_start"]),
                "proof_end": float(motion_item["proof_end"]),
                "phrase": proof_item.get("phrase", ""),
                "family": proof_item.get("family", contact_item.get("family", "")),
                "source_anchor_id": contact_item.get("candidate", ""),
                "carrier_mode": contact_item.get("carrier_mode", "sourced"),
                "hygiene_read": contact_item.get("hygiene_read", ""),
                "motion_proof_static_clip_path": motion_item.get("clip_path", ""),
                "motion_proof_static_clip_sha256": motion_item.get("clip_sha256", ""),
            }
        )
    return rows, contact_by_id, motion_proof


def stage_still(row: dict[str, Any], stage_cache_path: Path) -> tuple[Path, Path]:
    cache: dict[str, Any] = read_json(stage_cache_path) if stage_cache_path.exists() else {}
    shot_id = row["shot_id"]
    cached = cache.get(shot_id)
    if isinstance(cached, dict):
        staged = Path(cached.get("staged_path", ""))
        manifest = Path(cached.get("manifest_path", ""))
        if staged.exists() and manifest.exists():
            return staged, manifest

    completed = subprocess.run(
        [
            str(HANDOFF_STAGE),
            row["source_still_path"],
            "--from",
            "comfy",
            "--prompt",
            row["prompt"],
            "--width",
            str(WIDTH),
            "--height",
            str(HEIGHT),
            "--next-step",
            "titanic_static_gap_ltx_motion_scout_pass_02",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip())

    staged_path = None
    manifest_path = None
    for line in completed.stdout.splitlines():
        if line.startswith("INFO  Staged asset: "):
            staged_path = Path(line.split(": ", 1)[1].strip())
        elif line.startswith("INFO  Manifest: "):
            manifest_path = Path(line.split(": ", 1)[1].strip())
    if staged_path is None or manifest_path is None:
        raise RuntimeError(f"Could not parse handoff-stage output for {shot_id}")

    cache[shot_id] = {
        "staged_path": str(staged_path),
        "manifest_path": str(manifest_path),
    }
    write_json(stage_cache_path, cache)
    return staged_path, manifest_path


def candidate_slug(row: dict[str, Any], spec: CandidateSpec) -> str:
    return f"{row['shot_id']}__{spec.motion_pipeline}__seed{row['seed']}"


def render_candidate(
    *,
    row: dict[str, Any],
    spec: CandidateSpec,
    stage_cache_path: Path,
    rendered_count: int,
    max_renders: int,
    skip_render: bool,
) -> tuple[dict[str, Any], bool]:
    slug = candidate_slug(row, spec)
    logs_dir = OUTPUT_ROOT / "logs"
    raw_path = OUTPUT_ROOT / "candidates" / "raw" / f"{slug}.mp4"
    normalized_path = OUTPUT_ROOT / "candidates" / "normalized" / f"{slug}__no_audio.mp4"
    frame_dir = OUTPUT_ROOT / "frame_audits" / slug
    record: dict[str, Any] = {
        "beat_id": row["shot_id"],
        "shot_id": row["shot_id"],
        "candidate_id": slug,
        "variant_id": spec.variant_id,
        "variant_label": spec.label,
        "source_role": row["role"],
        "source_still_path": row["source_still_path"],
        "source_still_sha256": row["source_still_sha256"],
        "source_anchor_id": row["source_anchor_id"],
        "source_family": row["family"],
        "carrier_mode": row["carrier_mode"],
        "hygiene_read": row["hygiene_read"],
        "motion_pipeline": spec.motion_pipeline,
        "model_repo": spec.model_repo,
        "text_encoder_repo": spec.text_encoder_repo,
        "seed": row["seed"],
        "prompt_variant_id": "titanic_static_gap_low_amplitude_source_lock",
        "prompt_text": row["prompt"],
        "raw_clip_path": str(raw_path),
        "normalized_clip_path": str(normalized_path),
        "frame_audit_dir": str(frame_dir),
        "requested_duration_seconds": max(TARGET_SECONDS, float(row["proof_duration_seconds"])),
        "target_duration_seconds": TARGET_SECONDS,
        "frames": FRAME_COUNT,
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "motion_strategy": "still_driven_i2v",
        "motion_intent": row["motion_intent"],
        "reject_if": row["reject_if"],
        "source_derived_reanimation_used": False,
        "archival_motion_in_scope": False,
        "generated_stills_used": False,
        "disposition": "diagnostic only",
        "selected_for_motion_proof": False,
        "selected_for_motion_proof_status": "pending_human_review",
        "phrase": row["phrase"],
        "proof_start": row["proof_start"],
        "proof_end": row["proof_end"],
    }
    did_render = False
    try:
        staged_path, stage_manifest_path = stage_still(row, stage_cache_path)
        record["staged_path"] = str(staged_path)
        record["stage_manifest_path"] = str(stage_manifest_path)
        should_render = not skip_render and (max_renders <= 0 or rendered_count < max_renders)
        if should_render and not raw_path.exists():
            command = [
                str(HANDOFF_I2V),
                str(staged_path),
                "--prompt",
                row["prompt"],
                "--frames",
                str(FRAME_COUNT),
                "--width",
                str(WIDTH),
                "--height",
                str(HEIGHT),
                "--seed",
                str(row["seed"]),
                "--pipeline",
                spec.motion_pipeline,
                "--model-repo",
                spec.model_repo,
                "--typography",
                "off",
                "--output",
                str(raw_path),
            ]
            if spec.text_encoder_repo:
                command.extend(["--text-encoder-repo", spec.text_encoder_repo])
            status = run_logged(command, logs_dir / f"{slug}__render.log", cwd=VIZ_ROOT)
            if status == 0 and raw_path.exists():
                did_render = True
            else:
                record["render_status"] = "failed"
                record["failure_reason"] = f"handoff-i2v exited {status}; see {logs_dir / (slug + '__render.log')}"
        if raw_path.exists():
            ok = normalize_no_audio(raw_path, normalized_path, logs_dir / f"{slug}__normalize_no_audio.log")
            if ok:
                frames = extract_audit_frames(
                    normalized_path,
                    frame_dir,
                    logs_dir / f"{slug}__frame_audit.log",
                )
                duration = ffprobe_duration(normalized_path)
                video_info = ffprobe_video_info(normalized_path)
                handoff_manifest_path = Path(str(raw_path) + ".json")
                handoff_manifest = read_json(handoff_manifest_path) if handoff_manifest_path.exists() else {}
                pipeline_ok = handoff_manifest.get("pipeline") == spec.motion_pipeline
                model_ok = handoff_manifest.get("model_repo") == spec.model_repo
                dimensions_ok = int(video_info.get("width", 0)) == WIDTH and int(video_info.get("height", 0)) == HEIGHT
                duration_ok = duration >= TARGET_SECONDS - 0.15
                no_audio = not has_audio_stream(normalized_path)
                record.update(
                    {
                        "frame_audit_paths": [str(path) for path in frames],
                        "duration_seconds": duration,
                        "video_info": video_info,
                        "audio_stream_read": "pass: no audio stream" if no_audio else "reject: audio stream present",
                        "dimension_read": "pass" if dimensions_ok else "reject",
                        "duration_read": "pass" if duration_ok else "reject",
                        "metadata_pipeline_read": "pass" if pipeline_ok else "reject",
                        "metadata_model_repo_read": "pass" if model_ok else "reject",
                        "handoff_video_manifest_path": str(handoff_manifest_path) if handoff_manifest_path.exists() else "",
                        "normalized_sha256": sha256_file(normalized_path),
                        "raw_sha256": sha256_file(raw_path),
                        "render_status": "completed"
                        if all([frames, duration_ok, no_audio, dimensions_ok, pipeline_ok, model_ok])
                        else "failed",
                    }
                )
                if record["render_status"] != "completed":
                    record["failure_reason"] = "one or more validation reads failed"
            else:
                record["render_status"] = "failed"
                record["failure_reason"] = "normalization failed"
        elif "render_status" not in record:
            record["render_status"] = "pending"
            record["duration_seconds"] = 0.0
            record["audio_stream_read"] = "not checked"
            record["dimension_read"] = "not checked"
            record["duration_read"] = "not checked"
            record["metadata_pipeline_read"] = "not checked"
            record["metadata_model_repo_read"] = "not checked"
            record["frame_audit_paths"] = []
    except Exception as exc:
        record["render_status"] = "failed"
        record["failure_reason"] = str(exc)
        record["duration_seconds"] = 0.0
        record["audio_stream_read"] = "not checked"
        record["dimension_read"] = "not checked"
        record["duration_read"] = "not checked"
        record["metadata_pipeline_read"] = "not checked"
        record["metadata_model_repo_read"] = "not checked"
        record["frame_audit_paths"] = []
    return record, did_render


def make_contact_sheet(rows: list[dict[str, Any]], records: list[dict[str, Any]], contact_sheet_path: Path) -> None:
    by_shot: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        by_shot.setdefault(record["shot_id"], {})[record["variant_id"]] = record

    source_w, source_h = 128, 228
    frame_w, frame_h = 120, 213
    label_w = 310
    gap = 8
    margin = 24
    row_h = 326
    frames_per_variant = 6
    width = margin * 2 + label_w + source_w + gap + (frames_per_variant * (frame_w + gap) * 2) + 60
    height = margin * 2 + 92 + len(rows) * row_h
    canvas = Image.new("RGB", (width, height), (12, 12, 12))
    draw = ImageDraw.Draw(canvas)
    title_font = font(28)
    label_font = font(19)
    small_font = font(14)
    draw.text((margin, margin), "Titanic Static-Gap Motion Scout Pass 02", fill=(245, 245, 245), font=title_font)
    draw.text(
        (margin, margin + 38),
        "Reference still plus Apple LTX and distilled 2fps frame samples; diagnostic only; no archival motion import",
        fill=(190, 190, 190),
        font=small_font,
    )
    y = margin + 92
    for row in rows:
        draw.rectangle((margin, y, width - margin, y + row_h - 10), fill=(24, 24, 24))
        x = margin + 14
        draw.text((x, y + 16), row["shot_id"], fill=(245, 245, 245), font=label_font)
        draw.text((x, y + 43), row["role"], fill=(210, 210, 210), font=small_font)
        draw.text((x, y + 66), f"seed {row['seed']}", fill=(185, 185, 185), font=small_font)
        draw.text((x, y + 89), row["family"], fill=(170, 170, 170), font=small_font)
        draw.text((x, y + 116), "Reject if:", fill=(210, 210, 210), font=small_font)
        reject_text = row["reject_if"]
        wrapped = [reject_text[i : i + 38] for i in range(0, len(reject_text), 38)]
        for index, line in enumerate(wrapped[:5]):
            draw.text((x, y + 138 + index * 17), line, fill=(170, 170, 170), font=small_font)

        x = margin + label_w
        source = Image.open(row["source_still_path"]).convert("RGB")
        source_thumb = ImageOps.contain(source, (source_w, source_h))
        source_canvas = Image.new("RGB", (source_w, source_h), (0, 0, 0))
        source_canvas.paste(source_thumb, ((source_w - source_thumb.width) // 2, (source_h - source_thumb.height) // 2))
        draw.text((x, y + 12), "source", fill=(190, 190, 190), font=small_font)
        canvas.paste(source_canvas, (x, y + 40))
        x += source_w + gap + 20

        for variant_id, label in (("apple", "Apple LTX"), ("distilled", "distilled")):
            record = by_shot.get(row["shot_id"], {}).get(variant_id)
            status = record.get("render_status", "missing") if record else "missing"
            draw.text((x, y + 12), f"{label}: {status}", fill=(220, 220, 220), font=small_font)
            frames = [Path(path) for path in (record or {}).get("frame_audit_paths", [])][:frames_per_variant]
            fx = x
            for frame_path in frames:
                frame = Image.open(frame_path).convert("RGB")
                frame_thumb = ImageOps.contain(frame, (frame_w, frame_h))
                frame_canvas = Image.new("RGB", (frame_w, frame_h), (0, 0, 0))
                frame_canvas.paste(frame_thumb, ((frame_w - frame_thumb.width) // 2, (frame_h - frame_thumb.height) // 2))
                canvas.paste(frame_canvas, (fx, y + 40))
                fx += frame_w + gap
            for _ in range(frames_per_variant - len(frames)):
                draw.rectangle((fx, y + 40, fx + frame_w - 1, y + 40 + frame_h - 1), outline=(90, 90, 90))
                fx += frame_w + gap
            x += frames_per_variant * (frame_w + gap) + 20
        y += row_h

    contact_sheet_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(contact_sheet_path)


def build_preview_reel(records: list[dict[str, Any]], output_path: Path) -> Path | None:
    completed_paths = [
        Path(record["normalized_clip_path"])
        for record in records
        if record.get("render_status") == "completed" and Path(record["normalized_clip_path"]).exists()
    ]
    if not completed_paths:
        return None
    concat_path = output_path.parent / "preview_concat_pass_02.txt"
    write_text(concat_path, "\n".join(f"file '{path}'" for path in completed_paths))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-an",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return output_path if completed.returncode == 0 and output_path.exists() else None


def write_supporting_docs(rows: list[dict[str, Any]]) -> None:
    shot_list = ", ".join(f"`{row['shot_id']}`" for row in rows)
    write_text(
        DP_SCOPE_PATH,
        "\n".join(
            [
                "# Titanic Static-Gap LTX Motion Scope Pass 02",
                "",
                "## Gate",
                "",
                "- `stage`: `DP motion scope decision`",
                f"- `episode_id`: `{EPISODE_ID}`",
                f"- `short_id`: `{SHORT_ID}`",
                f"- `pass_id`: `{PASS_ID}`",
                f"- `created_at`: `{utc_now()}`",
                "- `disposition`: `diagnostic only`",
                "- `motion_strategy`: `still_driven_i2v`",
                "- `scope`: `six current direct-source-still holds only`",
                f"- `authorized_shots`: {shot_list}",
                f"- `control_keep_motion_shots`: {', '.join(f'`{shot}`' for shot in CONTROL_KEEP_MOTION_SHOT_IDS)}",
                "- `archival_motion_in_scope`: `false`",
                "- `source_derived_reanimation_used`: `false`",
                "- `generated_stills_used`: `false`",
                "- `final_export_blocked`: `true`",
                "",
                "## DP Direction",
                "",
                "- Keep the current pass03 final as the active keeper.",
                "- Render Apple and distilled diagnostic handles from the approved pass03 clean sourced stills only.",
                "- Preserve source identity, human count, boat count, ship/rail geometry, and period texture.",
                "- Allow only water bob, faint fog, film weave, restrained parallax, or slow camera creep.",
                "- Reject invented rescue action, sinking action, new people, new boats, face/body drift, hidden text, logos, or modern AI sheen.",
                "",
                "## Advancement",
                "",
                "- `may_start_motion_video_proof`: `false until human/DP review keeps winners`",
                "- `advance_rule`: `at least 5 of 6 static shots need a keep candidate before an all-motion proof plan`",
            ]
        ),
    )

    lines = [
        "# Titanic Static-Gap LTX Render Authorization Pass 02",
        "",
        "## Gate",
        "",
        "- `stage`: `render authorization check`",
        f"- `episode_id`: `{EPISODE_ID}`",
        f"- `short_id`: `{SHORT_ID}`",
        f"- `pass_id`: `{PASS_ID}`",
        f"- `created_at`: `{utc_now()}`",
        "- `render_authorization_read`: `pass for diagnostic motion scout only`",
        "- `disposition`: `diagnostic only`",
        "- `motion_strategy`: `still_driven_i2v`",
        "- `candidate_matrix`: `Apple LTX 2.3 q8 one-stage plus LTX 2 distilled bf16`",
        "- `archival_motion_in_scope`: `false`",
        "- `source_derived_reanimation_used`: `false`",
        "- `generated_stills_used`: `false`",
        "- `final_export_blocked`: `true`",
        "",
        "## Authorized Rows",
        "",
        "| shot_id | source_still_sha256 | role | seed |",
        "| --- | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(f"| `{row['shot_id']}` | `{row['source_still_sha256']}` | {row['role']} | `{row['seed']}` |")
    lines.extend(
        [
            "",
            "## Backend Matrix",
            "",
            f"- `apple_pipeline`: `{APPLE_PIPELINE}`",
            f"- `apple_model_repo`: `{APPLE_MODEL_REPO}`",
            f"- `apple_text_encoder_repo`: `{APPLE_TEXT_ENCODER_REPO}`",
            f"- `distilled_pipeline`: `{DISTILLED_PIPELINE}`",
            f"- `distilled_model_repo`: `{DISTILLED_MODEL_REPO}`",
            f"- `frames`: `{FRAME_COUNT}`",
            f"- `fps`: `{FPS}`",
            f"- `width`: `{WIDTH}`",
            f"- `height`: `{HEIGHT}`",
        ]
    )
    write_text(RENDER_AUTH_PATH, "\n".join(lines))


def write_request(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Titanic Static-Gap LTX Motion Scout Request Pass 02",
        "",
        "## Gate",
        "",
        "- `stage`: `motion contact sheet scout`",
        f"- `episode_id`: `{EPISODE_ID}`",
        f"- `short_id`: `{SHORT_ID}`",
        f"- `pass_id`: `{PASS_ID}`",
        "- `motion_strategy`: `still_driven_i2v`",
        "- `motion_scope`: `pass_02_static_gap_apple_distilled`",
        "- `archival_motion_in_scope`: `false`",
        "- `source_derived_reanimation_used`: `false`",
        "- `generated_stills_used`: `false`",
        f"- `apple_pipeline`: `{APPLE_PIPELINE}`",
        f"- `apple_model_repo`: `{APPLE_MODEL_REPO}`",
        f"- `apple_text_encoder_repo`: `{APPLE_TEXT_ENCODER_REPO}`",
        f"- `distilled_pipeline`: `{DISTILLED_PIPELINE}`",
        f"- `distilled_model_repo`: `{DISTILLED_MODEL_REPO}`",
        f"- `frame_count`: `{FRAME_COUNT}`",
        f"- `fps`: `{FPS}`",
        f"- `target_duration_seconds`: `{TARGET_SECONDS:.1f}`",
        "- `audio_policy`: `visual-only; strip any backend audio before review`",
        "- `final_export_blocked`: `true`",
        "",
        "## Scout Rows",
        "",
        "| shot_id | source_still_path | role | seed | variants | motion_intent | reject_if |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| `{shot_id}` | `{source}` | {role} | `{seed}` | `apple`, `distilled` | {intent} | {reject_if} |".format(
                shot_id=row["shot_id"],
                source=row["source_still_path"],
                role=row["role"],
                seed=row["seed"],
                intent=row["motion_intent"],
                reject_if=row["reject_if"],
            )
        )
    lines.extend(
        [
            "",
            "## Motion Controls",
            "",
            "- Keep the approved still composition and source identity primary.",
            "- Allow only low-amplitude water, fog, parallax, camera creep, or film-weave motion.",
            "- Reject invented sinking action, rescue action, evacuation action, people, boats, faces, text, logos, or modernized HD/AI texture.",
            "- Promote no candidate from manifest-only review; actual MP4 review and dense frame sampling are required.",
        ]
    )
    write_text(REQUEST_PATH, "\n".join(lines))


def write_review(manifest_path: Path, contact_sheet_path: Path, preview_reel_path: Path | None, records: list[dict[str, Any]]) -> None:
    completed = [record for record in records if record.get("render_status") == "completed"]
    failed = [record for record in records if record.get("render_status") != "completed"]
    complete_shots = {
        record["shot_id"]
        for record in records
        if record.get("render_status") == "completed"
    }
    qa_state = "ready_for_human_review" if len(completed) == len(records) else "partial"
    lines = [
        "# Titanic Static-Gap LTX Motion Contact Sheet Pass 02",
        "",
        "## Review Gate",
        "",
        "- `stage`: `motion contact sheet`",
        f"- `episode_id`: `{EPISODE_ID}`",
        f"- `short_id`: `{SHORT_ID}`",
        f"- `pass_id`: `{PASS_ID}`",
        f"- `created_at`: `{utc_now()}`",
        f"- `motion_contact_sheet_manifest_path`: `{manifest_path}`",
        f"- `motion_contact_sheet_path`: `{contact_sheet_path}`",
        f"- `motion_contact_sheet_reel_path`: `{preview_reel_path if preview_reel_path else 'none'}`",
        f"- `candidate_count`: `{len(records)}`",
        f"- `completed_candidate_count`: `{len(completed)}`",
        f"- `static_gap_shots_with_at_least_one_completed_candidate`: `{len(complete_shots)}`",
        f"- `render_completion_status`: `{qa_state}`",
        "- `motion_strategy`: `still_driven_i2v`",
        "- `archival_motion_in_scope`: `false`",
        "- `source_derived_reanimation_used`: `false`",
        "- `generated_stills_used`: `false`",
        "- `audio_stream_policy`: `visual-only; normalized clips must be no-audio`",
        "- `dense_frame_sampling`: `2fps frame audit extracted for each completed handle`",
        "- `disposition`: `diagnostic only pending human review`",
        "- `current_pass03_final_status`: `remains active keeper`",
        "- `may_start_motion_video_proof`: `false`",
        "- `may_start_final_export`: `false`",
        "",
        "## Candidate QA",
        "",
        "| shot_id | variant | status | duration | audio | dimensions | metadata | frame_audit_count | review_focus |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: | --- |",
    ]
    for record in records:
        metadata = f"{record.get('metadata_pipeline_read', '')}/{record.get('metadata_model_repo_read', '')}"
        dimensions = record.get("dimension_read", "")
        lines.append(
            "| `{shot}` | `{variant}` | `{status}` | `{duration:.3f}` | `{audio}` | `{dimensions}` | `{metadata}` | `{frames}` | {focus} |".format(
                shot=record["shot_id"],
                variant=record["variant_id"],
                status=record.get("render_status", ""),
                duration=float(record.get("duration_seconds", 0.0)),
                audio=record.get("audio_stream_read", ""),
                dimensions=dimensions,
                metadata=metadata,
                frames=len(record.get("frame_audit_paths", [])),
                focus=record.get("reject_if", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Reject Conditions",
            "",
            "- Reject human face/body drift, added people, added boats, changed people/boat counts, or restaged rescue action.",
            "- Reject source geometry drift around ship rails, lifeboats, oars, ropes, horizons, or crowd/ship context.",
            "- Reject hidden text, logos, watermarks, lower-thirds, caption-like artifacts, document leakage, or modern AI sheen.",
            "- Reject motion that creates new sinking, collision, evacuation, or rescue events not present in the sourced still.",
            "",
            "## Handoff",
            "",
            "- `next_action`: human/DP review of the Apple-versus-distilled contact sheet and preview reel.",
            "- `advance_rule`: if at least 5 of 6 static shots have a keep candidate, create `shot_timing_edl_pass_02_all_motion`; otherwise keep pass03 active and use only any winning diagnostic clips in a later partial hybrid proof if useful.",
        ]
    )
    if failed:
        lines.extend(["", "## Render Failures", ""])
        for record in failed:
            lines.append(f"- `{record['candidate_id']}`: `{record.get('failure_reason', 'unknown failure')}`")
    write_text(REVIEW_PATH, "\n".join(lines))


def write_handoff(manifest_path: Path, contact_sheet_path: Path, preview_reel_path: Path | None, records: list[dict[str, Any]]) -> None:
    completed_count = sum(1 for record in records if record.get("render_status") == "completed")
    completed_shots = sorted({record["shot_id"] for record in records if record.get("render_status") == "completed"})
    lines = [
        "stage: motion_contact_sheet_ltx_static_gap_pass_02_handoff",
        f"episode_id: {EPISODE_ID}",
        f"short_id: {SHORT_ID}",
        f"gate_id: {PASS_ID}",
        f"created_at: {utc_now()}",
        "disposition: diagnostic only",
        f"candidate_count: {len(records)}",
        f"completed_candidate_count: {completed_count}",
        f"static_gap_shots_with_completed_candidate: {len(completed_shots)}",
        "motion_strategy: still_driven_i2v",
        "archival_motion_in_scope: false",
        "source_derived_reanimation_used: false",
        "generated_stills_used: false",
        "current_pass03_final_remains_active: true",
        "may_start_shot_timing_edl_pass_02_all_motion: false until human review keeps at least 5 of 6 static-gap shots",
        "may_start_motion_video_proof: false",
        "may_start_final_export: false",
        f"motion_contact_sheet_manifest_path: {manifest_path}",
        f"motion_contact_sheet_path: {contact_sheet_path}",
        f"motion_contact_sheet_reel_path: {preview_reel_path if preview_reel_path else ''}",
        f"gate_review_path: {REVIEW_PATH}",
        "next_action: Review the Titanic pass02 Apple-versus-distilled static-gap contact sheet and preview reel; choose keep/tighten/reject per shot.",
    ]
    write_text(HANDOFF_PATH, "\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Titanic static-gap LTX motion scout pass 02.")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--max-renders", type=int, default=0, help="0 renders all missing candidates")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows, _contact_by_id, source_motion_proof = validate_source_manifests()
    write_supporting_docs(rows)
    write_request(rows)

    stage_cache_path = OUTPUT_ROOT / "stage_cache.json"
    records: list[dict[str, Any]] = []
    rendered = 0
    for row in rows:
        for spec in CANDIDATE_SPECS:
            record, did_render = render_candidate(
                row=row,
                spec=spec,
                stage_cache_path=stage_cache_path,
                rendered_count=rendered,
                max_renders=args.max_renders,
                skip_render=args.skip_render,
            )
            if did_render:
                rendered += 1
            records.append(record)

    manifest_path = OUTPUT_ROOT / "titanic_static_gap_ltx_motion_scout_manifest_pass_02.json"
    contact_sheet_path = OUTPUT_ROOT / "titanic_static_gap_ltx_motion_scout_contact_sheet_pass_02.png"
    preview_reel_path = build_preview_reel(
        records,
        OUTPUT_ROOT / "titanic_static_gap_ltx_motion_scout_preview_reel_pass_02.mp4",
    )
    make_contact_sheet(rows, records, contact_sheet_path)
    completed_count = sum(1 for record in records if record.get("render_status") == "completed")
    completed_shot_count = len({record["shot_id"] for record in records if record.get("render_status") == "completed"})
    payload = {
        "stage": "motion_contact_sheet",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "pass_id": PASS_ID,
        "created_at": utc_now(),
        "input_stills_video_proof_manifest_path": str(SOURCE_PROOF_MANIFEST),
        "input_contact_sheet_manifest_path": str(SOURCE_CONTACT_MANIFEST),
        "input_motion_video_proof_manifest_path": str(SOURCE_MOTION_PROOF_MANIFEST),
        "dp_scope_decision_path": str(DP_SCOPE_PATH),
        "render_authorization_path": str(RENDER_AUTH_PATH),
        "request_path": str(REQUEST_PATH),
        "review_path": str(REVIEW_PATH),
        "handoff_path": str(HANDOFF_PATH),
        "current_pass03_final_remains_active": True,
        "source_motion_proof_path": source_motion_proof.get("proof_video_path", ""),
        "source_motion_proof_sha256": source_motion_proof.get("proof_video_sha256", ""),
        "static_gap_shot_ids": STATIC_GAP_SHOT_IDS,
        "control_keep_motion_shot_ids": CONTROL_KEEP_MOTION_SHOT_IDS,
        "motion_strategy": "still_driven_i2v",
        "archival_motion_in_scope": False,
        "source_derived_reanimation_used": False,
        "generated_stills_used": False,
        "candidate_matrix": [
            {
                "variant_id": spec.variant_id,
                "label": spec.label,
                "motion_pipeline": spec.motion_pipeline,
                "model_repo": spec.model_repo,
                "text_encoder_repo": spec.text_encoder_repo,
            }
            for spec in CANDIDATE_SPECS
        ],
        "fps": FPS,
        "frames": FRAME_COUNT,
        "target_duration_seconds": TARGET_SECONDS,
        "width": WIDTH,
        "height": HEIGHT,
        "contact_sheet_path": str(contact_sheet_path),
        "contact_sheet_sha256": sha256_file(contact_sheet_path),
        "preview_reel_path": str(preview_reel_path) if preview_reel_path else "",
        "preview_reel_sha256": sha256_file(preview_reel_path) if preview_reel_path else "",
        "raw_clips_root": str(OUTPUT_ROOT / "candidates/raw"),
        "normalized_clips_root": str(OUTPUT_ROOT / "candidates/normalized"),
        "frame_audits_root": str(OUTPUT_ROOT / "frame_audits"),
        "motion_candidates": records,
        "candidate_count": len(records),
        "completed_candidate_count": completed_count,
        "static_gap_shots_with_at_least_one_completed_candidate": completed_shot_count,
        "render_completion_status": "complete" if completed_count == len(records) else "partial",
        "disposition": "diagnostic only pending human review",
        "may_start_shot_timing_edl_pass_02_all_motion": False,
        "may_start_motion_video_proof": False,
        "may_start_final_export": False,
    }
    write_json(manifest_path, payload)
    write_review(manifest_path, contact_sheet_path, preview_reel_path, records)
    write_handoff(manifest_path, contact_sheet_path, preview_reel_path, records)
    print(f"INFO  DP scope: {DP_SCOPE_PATH}")
    print(f"INFO  Render authorization: {RENDER_AUTH_PATH}")
    print(f"INFO  Request: {REQUEST_PATH}")
    print(f"INFO  Manifest: {manifest_path}")
    print(f"INFO  Contact sheet: {contact_sheet_path}")
    print(f"INFO  Preview reel: {preview_reel_path if preview_reel_path else 'none'}")
    print(f"INFO  Completed candidates: {completed_count}/{len(records)}")
    print(f"INFO  Static-gap shots with candidates: {completed_shot_count}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
