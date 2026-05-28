#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


EPISODE_ID = "titanic"
SHORT_ID = "titanic_short_scoped_v1"
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
OUTPUT_ROOT = VIZ_SHORT_ROOT / "motion_contact_sheet/pass_01_ltx_scout"
REQUEST_PATH = PRODUCTION_ROOT / "ltx_motion_scout_request_pass_01.md"
REVIEW_PATH = PRODUCTION_ROOT / "motion_contact_sheet_review_ltx_scout_pass_01.md"
HANDOFF_PATH = PRODUCTION_ROOT / "motion_contact_sheet_handoff_ltx_scout_pass_01.yaml"
VIZ_ROOT = Path("/Users/mike/Viz_CascadeEffects")
HANDOFF_STAGE = VIZ_ROOT / "scripts/handoff-stage.sh"
HANDOFF_I2V = VIZ_ROOT / "scripts/handoff-i2v.sh"

FPS = 24
FRAME_COUNT = 121
TARGET_SECONDS = 5.0
WIDTH = 576
HEIGHT = 1024
PIPELINE = "apple-ltx23-q8-one-stage"
MODEL_REPO = "dgrauet/ltx-2.3-mlx-q8"
TEXT_ENCODER_REPO = "mlx-community/gemma-3-12b-it-4bit"


@dataclass(frozen=True)
class ScoutShot:
    shot_id: str
    role: str
    seed: int
    motion_intent: str
    reject_if: str
    prompt: str


SCOUT_SHOTS = [
    ScoutShot(
        shot_id="shot_00",
        role="ship hook",
        seed=840001,
        motion_intent="faint funnel smoke, gentle sea shimmer, slow camera creep",
        reject_if="ship geometry, mast, funnel, hull, rigging, or period-photo identity warps",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the RMS Titanic photograph "
            "composition, hull shape, mast and rigging, deck line, funnels, and black-and-white "
            "period texture fixed. Add only faint funnel smoke drift, gentle sea shimmer, and an "
            "almost imperceptible slow camera creep. No new boats, no people changes, no text, "
            "no logos, no modern color, no dramatic sinking action."
        ),
    ),
    ScoutShot(
        shot_id="shot_01",
        role="iceberg/ocean",
        seed=840101,
        motion_intent="fog drift, water shimmer, restrained slow push",
        reject_if="iceberg shape changes, collision action appears, or new ship/object appears",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the iceberg and ocean photograph "
            "composition fixed, preserving the original iceberg silhouette, horizon, waterline, "
            "and monochrome archival texture. Add only slight fog drift, subtle water shimmer, "
            "and a restrained slow push. No ship collision, no cracking iceberg, no new vessels, "
            "no text, no logos, no modern color."
        ),
    ),
    ScoutShot(
        shot_id="shot_02",
        role="ship mass",
        seed=840201,
        motion_intent="smoke, water, restrained parallax",
        reject_if="ship scale, funnel count, rigging, or dock geometry changes",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the Titanic harbor photograph "
            "composition, ship scale, funnel count, rigging, dock geometry, and period texture "
            "fixed. Add only restrained smoke drift, small water movement, and barely visible "
            "parallax from a locked documentary camera. No new ships, no new people, no text, "
            "no logos, no sinking or collision action."
        ),
    ),
    ScoutShot(
        shot_id="shot_05",
        role="lifeboat gap",
        seed=840501,
        motion_intent="subtle water bob, locked people and boat",
        reject_if="people count, body posture, faces, boat count, or boat geometry changes",
        prompt=(
            "Source-preserving documentary image-to-video. Keep the lifeboat photograph "
            "composition fixed, preserving the exact boat position, people count, seated "
            "postures, faces, oars, and sea horizon. Add only slight water bob and tiny camera "
            "drift already implied by the still. No new people, no face changes, no body motion, "
            "no boat reshaping, no added boats, no text, no logos."
        ),
    ),
    ScoutShot(
        shot_id="shot_06",
        role="sinking illustration",
        seed=840601,
        motion_intent="tiny smoke/water/film drift only",
        reject_if="new catastrophe action, changed ship angle, added people, or added boats appear",
        prompt=(
            "Source-preserving documentary image-to-video. Keep this period sinking illustration "
            "as representational artwork, preserving the original ship angle, water shape, sky, "
            "smoke, and illustration texture. Add only tiny smoke drift, slight water shimmer, "
            "and subtle film weave. No new sinking stage, no plunging motion, no explosion, no "
            "new people, no new boats, no text, no logos."
        ),
    ),
    ScoutShot(
        shot_id="shot_11",
        role="final motif",
        seed=841101,
        motion_intent="restrained illustration motion with stable tail hold",
        reject_if="tail image no longer holds stable or invents new disaster action",
        prompt=(
            "Source-preserving documentary image-to-video for a final held motif. Keep the period "
            "sinking illustration composition stable, preserving the original ship angle, water, "
            "sky, smoke, and printed-art texture. Add only very slow smoke drift, faint water "
            "movement, and subtle film weave while maintaining a stable end hold. No new action, "
            "no new people, no new boats, no text, no logos, no modernized look."
        ),
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


def sha256_file(path: Path) -> str:
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


def stage_still(shot: ScoutShot, still_path: Path, prompt: str, stage_cache_path: Path) -> tuple[Path, Path]:
    cache: dict[str, Any] = read_json(stage_cache_path) if stage_cache_path.exists() else {}
    cached = cache.get(shot.shot_id)
    if isinstance(cached, dict):
        staged = Path(cached.get("staged_path", ""))
        manifest = Path(cached.get("manifest_path", ""))
        if staged.exists() and manifest.exists():
            return staged, manifest

    completed = subprocess.run(
        [
            str(HANDOFF_STAGE),
            str(still_path),
            "--from",
            "comfy",
            "--prompt",
            prompt,
            "--width",
            str(WIDTH),
            "--height",
            str(HEIGHT),
            "--next-step",
            "titanic_ltx_motion_scout_pass_01",
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
        raise RuntimeError(f"Could not parse handoff-stage output for {shot.shot_id}")

    cache[shot.shot_id] = {
        "staged_path": str(staged_path),
        "manifest_path": str(manifest_path),
    }
    write_json(stage_cache_path, cache)
    return staged_path, manifest_path


def make_contact_sheet(records: list[dict[str, Any]], contact_sheet_path: Path) -> None:
    source_w, source_h = 128, 228
    frame_w, frame_h = 132, 235
    label_w = 280
    gap = 8
    margin = 24
    row_h = 286
    frame_count = 10
    width = margin * 2 + label_w + source_w + gap + frame_count * (frame_w + gap)
    height = margin * 2 + 88 + len(records) * row_h
    canvas = Image.new("RGB", (width, height), (12, 12, 12))
    draw = ImageDraw.Draw(canvas)
    title_font = font(28)
    label_font = font(20)
    small_font = font(15)
    draw.text((margin, margin), "Titanic LTX Motion Scout Pass 01", fill=(245, 245, 245), font=title_font)
    draw.text(
        (margin, margin + 38),
        "2fps frame audit from six still-driven I2V handles; no archival motion import; no generated stills",
        fill=(190, 190, 190),
        font=small_font,
    )
    y = margin + 88
    for record in records:
        shot_id = record["beat_id"]
        draw.rectangle((margin, y, width - margin, y + row_h - 10), fill=(24, 24, 24))
        x = margin + 14
        draw.text((x, y + 16), shot_id, fill=(245, 245, 245), font=label_font)
        draw.text((x, y + 44), record.get("source_role", ""), fill=(210, 210, 210), font=small_font)
        draw.text((x, y + 70), record.get("render_status", ""), fill=(190, 190, 190), font=small_font)
        draw.text((x, y + 94), f"seed {record.get('seed', '')}", fill=(170, 170, 170), font=small_font)
        draw.text((x, y + 118), "reject if:", fill=(210, 210, 210), font=small_font)
        reject_text = record.get("reject_if", "")
        wrapped = [reject_text[i : i + 34] for i in range(0, len(reject_text), 34)]
        for index, line in enumerate(wrapped[:4]):
            draw.text((x, y + 140 + index * 18), line, fill=(170, 170, 170), font=small_font)
        x = margin + label_w
        source = Image.open(record["source_still_path"]).convert("RGB")
        source_thumb = ImageOps.contain(source, (source_w, source_h))
        source_canvas = Image.new("RGB", (source_w, source_h), (0, 0, 0))
        source_canvas.paste(source_thumb, ((source_w - source_thumb.width) // 2, (source_h - source_thumb.height) // 2))
        canvas.paste(source_canvas, (x, y + 36))
        draw.text((x, y + 12), "source", fill=(190, 190, 190), font=small_font)
        x += source_w + gap
        frames = [Path(path) for path in record.get("frame_audit_paths", [])][:frame_count]
        for frame_path in frames:
            frame = Image.open(frame_path).convert("RGB")
            canvas.paste(frame, (x, y + 36))
            x += frame_w + gap
        while len(frames) < frame_count:
            draw.rectangle((x, y + 36, x + frame_w - 1, y + 36 + frame_h - 1), outline=(80, 80, 80))
            x += frame_w + gap
            frames.append(Path(""))
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
    concat_path = output_path.parent / "preview_concat_pass_01.txt"
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
        "-c",
        "copy",
        str(output_path),
    ]
    if subprocess.run(command, capture_output=True, text=True, check=False).returncode == 0:
        return output_path
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
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return output_path if completed.returncode == 0 and output_path.exists() else None


def write_request(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Titanic LTX Motion Scout Request Pass 01",
        "",
        "## Gate",
        "",
        "- `stage`: `motion contact sheet scout`",
        f"- `episode_id`: `{EPISODE_ID}`",
        f"- `short_id`: `{SHORT_ID}`",
        "- `motion_strategy`: `still_driven_i2v`",
        "- `motion_scope`: `ltx_motion_scout_pass_01_named_shots_only`",
        "- `archival_motion_in_scope`: `false`",
        "- `source_derived_reanimation_used`: `false`",
        "- `generated_stills_used`: `false`",
        f"- `pipeline`: `{PIPELINE}`",
        f"- `model_repo`: `{MODEL_REPO}`",
        f"- `text_encoder_repo`: `{TEXT_ENCODER_REPO}`",
        f"- `frame_count`: `{FRAME_COUNT}`",
        f"- `fps`: `{FPS}`",
        f"- `target_duration_seconds`: `{TARGET_SECONDS:.1f}`",
        "- `audio_policy`: `visual-only; strip any backend audio before review`",
        "- `final_export_blocked`: `true`",
        "",
        "## Scout Rows",
        "",
        "| shot_id | source_still_path | role | seed | motion_intent | reject_if |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| `{shot_id}` | `{source}` | `{role}` | `{seed}` | {intent} | {reject_if} |".format(
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
            "- Allow only low-amplitude smoke, water, fog, parallax, camera creep, or film-weave motion.",
            "- Reject invented sinking action, evacuation action, people, boats, faces, text, logos, or modernized HD/AI texture.",
            "- Human survivor/crowd shots remain deferred until this scout proves stable.",
        ]
    )
    write_text(REQUEST_PATH, "\n".join(lines))


def write_review(manifest_path: Path, contact_sheet_path: Path, preview_reel_path: Path | None, records: list[dict[str, Any]]) -> None:
    completed = [record for record in records if record.get("render_status") == "completed"]
    failed = [record for record in records if record.get("render_status") != "completed"]
    audio_failures = [record for record in completed if record.get("audio_stream_read") != "pass: no audio stream"]
    duration_failures = [
        record for record in completed if float(record.get("duration_seconds", 0.0)) < TARGET_SECONDS - 0.15
    ]
    qa_state = "ready_for_human_review" if len(completed) == len(records) and not audio_failures and not duration_failures else "partial"
    lines = [
        "# Titanic LTX Motion Scout Contact Sheet Pass 01",
        "",
        "## Review Gate",
        "",
        "- `stage`: `motion contact sheet`",
        f"- `episode_id`: `{EPISODE_ID}`",
        f"- `short_id`: `{SHORT_ID}`",
        "- `pass_id`: `ltx_motion_scout_pass_01`",
        f"- `created_at`: `{utc_now()}`",
        f"- `motion_contact_sheet_manifest_path`: `{manifest_path}`",
        f"- `motion_contact_sheet_path`: `{contact_sheet_path}`",
        f"- `motion_contact_sheet_reel_path`: `{preview_reel_path if preview_reel_path else 'none'}`",
        f"- `candidate_count`: `{len(records)}`",
        f"- `completed_candidate_count`: `{len(completed)}`",
        f"- `render_completion_status`: `{qa_state}`",
        "- `motion_strategy`: `still_driven_i2v`",
        "- `archival_motion_in_scope`: `false`",
        "- `source_derived_reanimation_used`: `false`",
        "- `generated_stills_used`: `false`",
        "- `audio_stream_policy`: `visual-only; normalized clips must be no-audio`",
        "- `dense_frame_sampling`: `2fps frame audit extracted for each completed handle`",
        "- `disposition`: `diagnostic only pending human review`",
        "- `may_start_motion_video_proof`: `false`",
        "- `may_start_final_export`: `false`",
        "",
        "## Candidate QA",
        "",
        "| shot_id | status | duration | audio | frame_audit_count | review_focus |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for record in records:
        lines.append(
            "| `{shot}` | `{status}` | `{duration:.3f}` | `{audio}` | `{frames}` | {focus} |".format(
                shot=record["beat_id"],
                status=record.get("render_status", ""),
                duration=float(record.get("duration_seconds", 0.0)),
                audio=record.get("audio_stream_read", ""),
                frames=len(record.get("frame_audit_paths", [])),
                focus=record.get("reject_if", ""),
            )
        )
    lines.extend(
        [
            "",
            "## Reject Conditions",
            "",
            "- Reject ship or iceberg geometry drift, modernized AI sheen, or source-defying disaster motion.",
            "- Reject human face/body drift, added people, added boats, or changed lifeboat/person counts.",
            "- Reject hidden text, logo, caption, watermark, lower-third, or document-surface leakage.",
            "- Promote only after actual MP4 review, not manifest-only review.",
            "",
            "## Handoff",
            "",
            "- `next_action`: human/DP review of the LTX scout contact sheet and preview reel.",
            "- `advance_rule`: if at least 4 of 6 handles pass visual QA, create `shot_timing_edl`; otherwise keep the static stills proof or use only winning handles.",
        ]
    )
    if failed:
        lines.extend(["", "## Render Failures", ""])
        for record in failed:
            lines.append(f"- `{record['beat_id']}`: `{record.get('failure_reason', 'unknown failure')}`")
    write_text(REVIEW_PATH, "\n".join(lines))


def write_handoff(manifest_path: Path, contact_sheet_path: Path, preview_reel_path: Path | None, records: list[dict[str, Any]]) -> None:
    completed_count = sum(1 for record in records if record.get("render_status") == "completed")
    lines = [
        "stage: motion_contact_sheet_ltx_scout_pass_01_handoff",
        f"episode_id: {EPISODE_ID}",
        f"short_id: {SHORT_ID}",
        "gate_id: ltx_motion_scout_pass_01",
        f"created_at: {utc_now()}",
        "disposition: diagnostic only",
        f"candidate_count: {len(records)}",
        f"completed_candidate_count: {completed_count}",
        "motion_strategy: still_driven_i2v",
        "archival_motion_in_scope: false",
        "source_derived_reanimation_used: false",
        "generated_stills_used: false",
        "may_start_shot_timing_edl: false until human review keeps at least 4 of 6",
        "may_start_motion_video_proof: false",
        "may_start_final_export: false",
        f"motion_contact_sheet_manifest_path: {manifest_path}",
        f"motion_contact_sheet_path: {contact_sheet_path}",
        f"motion_contact_sheet_reel_path: {preview_reel_path if preview_reel_path else ''}",
        f"gate_review_path: {REVIEW_PATH}",
        "next_action: Review the Titanic LTX scout contact sheet and preview reel; choose keep/tighten/reject per shot.",
    ]
    write_text(HANDOFF_PATH, "\n".join(lines))


def load_rows() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    proof = read_json(SOURCE_PROOF_MANIFEST)
    contact = read_json(SOURCE_CONTACT_MANIFEST)
    proof_by_id = {item["shot_id"]: item for item in proof["shots"]}
    contact_by_id = {item["shot_id"]: item for item in contact["shots"]}
    rows = []
    for scout in SCOUT_SHOTS:
        proof_item = proof_by_id[scout.shot_id]
        contact_item = contact_by_id[scout.shot_id]
        source_still = Path(proof_item["image"])
        if source_still != Path(contact_item["clean_candidate_path"]):
            raise RuntimeError(f"{scout.shot_id}: proof image and contact clean candidate differ")
        if not source_still.exists():
            raise RuntimeError(f"{scout.shot_id}: missing source still {source_still}")
        rows.append(
            {
                "shot_id": scout.shot_id,
                "source_still_path": str(source_still),
                "source_still_sha256": sha256_file(source_still),
                "role": scout.role,
                "seed": scout.seed,
                "motion_intent": scout.motion_intent,
                "reject_if": scout.reject_if,
                "prompt": scout.prompt,
            }
        )
    return rows, proof_by_id, contact_by_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Titanic LTX scout pass 01.")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--max-renders", type=int, default=0, help="0 renders all missing candidates")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows, proof_by_id, contact_by_id = load_rows()
    write_request(rows)

    stage_cache_path = OUTPUT_ROOT / "stage_cache.json"
    records: list[dict[str, Any]] = []
    rendered = 0
    for row in rows:
        shot_id = row["shot_id"]
        raw_path = OUTPUT_ROOT / "candidates/raw" / f"{shot_id}__{PIPELINE}__seed{row['seed']}.mp4"
        normalized_path = OUTPUT_ROOT / "candidates/normalized" / f"{shot_id}__{PIPELINE}__seed{row['seed']}__no_audio.mp4"
        frame_dir = OUTPUT_ROOT / "frame_audits" / shot_id
        logs_dir = OUTPUT_ROOT / "logs"
        contact_item = contact_by_id[shot_id]
        proof_item = proof_by_id[shot_id]
        record = {
            "beat_id": shot_id,
            "visual_beat_id": contact_item.get("label", ""),
            "source_role": row["role"],
            "source_still_path": row["source_still_path"],
            "source_still_variant_role": "primary",
            "source_still_sha256": row["source_still_sha256"],
            "source_anchor_id": contact_item.get("candidate", ""),
            "source_family": contact_item.get("family", proof_item.get("family", "")),
            "carrier_mode": "sourced",
            "motion_pipeline": PIPELINE,
            "model_repo": MODEL_REPO,
            "text_encoder_repo": TEXT_ENCODER_REPO,
            "seed": row["seed"],
            "prompt_variant_id": "titanic_low_amplitude_source_lock",
            "prompt_text": row["prompt"],
            "raw_clip_path": str(raw_path),
            "normalized_clip_path": str(normalized_path),
            "requested_duration_seconds": max(TARGET_SECONDS, float(proof_item["duration"])),
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
        }
        should_render = not args.skip_render and (args.max_renders <= 0 or rendered < args.max_renders)
        try:
            staged_path, stage_manifest_path = stage_still(
                SCOUT_SHOTS[[shot.shot_id for shot in SCOUT_SHOTS].index(shot_id)],
                Path(row["source_still_path"]),
                row["prompt"],
                stage_cache_path,
            )
            record["staged_path"] = str(staged_path)
            record["stage_manifest_path"] = str(stage_manifest_path)
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
                    PIPELINE,
                    "--model-repo",
                    MODEL_REPO,
                    "--text-encoder-repo",
                    TEXT_ENCODER_REPO,
                    "--typography",
                    "off",
                    "--output",
                    str(raw_path),
                ]
                status = run_logged(command, logs_dir / f"{shot_id}__ltx_render.log", cwd=VIZ_ROOT)
                if status == 0 and raw_path.exists():
                    rendered += 1
                else:
                    record["render_status"] = "failed"
                    record["failure_reason"] = f"handoff-i2v exited {status}; see {logs_dir / (shot_id + '__ltx_render.log')}"
            if raw_path.exists():
                ok = normalize_no_audio(raw_path, normalized_path, logs_dir / f"{shot_id}__normalize_no_audio.log")
                if ok:
                    frames = extract_audit_frames(
                        normalized_path,
                        frame_dir,
                        logs_dir / f"{shot_id}__frame_audit.log",
                    )
                    record["frame_audit_paths"] = [str(path) for path in frames]
                    record["duration_seconds"] = ffprobe_duration(normalized_path)
                    record["audio_stream_read"] = "reject: audio stream present" if has_audio_stream(normalized_path) else "pass: no audio stream"
                    record["normalized_sha256"] = sha256_file(normalized_path)
                    record["raw_sha256"] = sha256_file(raw_path)
                    record["render_status"] = "completed"
                else:
                    record["render_status"] = "failed"
                    record["failure_reason"] = "normalization failed"
            elif "render_status" not in record:
                record["render_status"] = "pending"
                record["duration_seconds"] = 0.0
                record["audio_stream_read"] = "not checked"
                record["frame_audit_paths"] = []
        except Exception as exc:
            record["render_status"] = "failed"
            record["failure_reason"] = str(exc)
            record["duration_seconds"] = 0.0
            record["audio_stream_read"] = "not checked"
            record["frame_audit_paths"] = []
        records.append(record)

    manifest_path = OUTPUT_ROOT / "titanic_ltx_motion_scout_manifest_pass_01.json"
    contact_sheet_path = OUTPUT_ROOT / "titanic_ltx_motion_scout_contact_sheet_pass_01.png"
    preview_reel_path = build_preview_reel(
        records,
        OUTPUT_ROOT / "titanic_ltx_motion_scout_preview_reel_pass_01.mp4",
    )
    make_contact_sheet(records, contact_sheet_path)
    payload = {
        "stage": "motion_contact_sheet",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "pass_id": "ltx_motion_scout_pass_01",
        "created_at": utc_now(),
        "input_stills_video_proof_manifest_path": str(SOURCE_PROOF_MANIFEST),
        "input_contact_sheet_manifest_path": str(SOURCE_CONTACT_MANIFEST),
        "request_path": str(REQUEST_PATH),
        "motion_strategy": "still_driven_i2v",
        "archival_motion_in_scope": False,
        "source_derived_reanimation_used": False,
        "generated_stills_used": False,
        "pipeline": PIPELINE,
        "model_repo": MODEL_REPO,
        "text_encoder_repo": TEXT_ENCODER_REPO,
        "fps": FPS,
        "frames": FRAME_COUNT,
        "target_duration_seconds": TARGET_SECONDS,
        "contact_sheet_path": str(contact_sheet_path),
        "contact_sheet_sha256": sha256_file(contact_sheet_path),
        "preview_reel_path": str(preview_reel_path) if preview_reel_path else "",
        "preview_reel_sha256": sha256_file(preview_reel_path) if preview_reel_path else "",
        "raw_clips_root": str(OUTPUT_ROOT / "candidates/raw"),
        "normalized_clips_root": str(OUTPUT_ROOT / "candidates/normalized"),
        "frame_audits_root": str(OUTPUT_ROOT / "frame_audits"),
        "motion_candidates": records,
        "render_completion_status": "complete"
        if all(record.get("render_status") == "completed" for record in records)
        else "partial",
        "disposition": "diagnostic only pending human review",
        "may_start_shot_timing_edl": False,
        "may_start_motion_video_proof": False,
        "may_start_final_export": False,
    }
    write_json(manifest_path, payload)
    write_review(manifest_path, contact_sheet_path, preview_reel_path, records)
    write_handoff(manifest_path, contact_sheet_path, preview_reel_path, records)
    print(f"INFO  Request: {REQUEST_PATH}")
    print(f"INFO  Manifest: {manifest_path}")
    print(f"INFO  Contact sheet: {contact_sheet_path}")
    print(f"INFO  Preview reel: {preview_reel_path if preview_reel_path else 'none'}")
    print(
        "INFO  Completed candidates: "
        f"{sum(1 for record in records if record.get('render_status') == 'completed')}/{len(records)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
