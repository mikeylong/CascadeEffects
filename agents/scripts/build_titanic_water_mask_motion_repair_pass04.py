#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


EPISODE_ID = "titanic"
SHORT_ID = "titanic_short_scoped_v1"
PASS_ID = "water_mask_motion_repair_pass_04"
OUTPUT_SLUG = "pass_04_water_mask_motion_repair"

PRODUCTION_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1/production"
)
VIZ_SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/titanic_short_scoped_v1"
)
OUTPUT_ROOT = VIZ_SHORT_ROOT / "motion_contact_sheet" / OUTPUT_SLUG

WIDTH = 576
HEIGHT = 1024
FPS = 24
FRAME_COUNT = 121
TARGET_SECONDS = 5.0

SHOT_SPECS = [
    {
        "shot_id": "shot_07",
        "role": "underfilled lifeboat close beat",
        "source_still_path": VIZ_SHORT_ROOT
        / "stills_contact_sheet/pass_03_event_led_shot_lock/clean_candidates/shot_07_event_06_lifeboat_survivors_close.png",
        "motion_intent": "water-only shimmer around the locked lifeboat; people, boat rim, oars, and faces remain frozen",
        "reject_if": "any person, oar, boat rim, or face moves; mask edge halos; water motion calls attention to itself",
        "amplitude_x": 3.0,
        "amplitude_y": 1.0,
        "speed": 1.15,
    },
    {
        "shot_id": "shot_10",
        "role": "SOLAS consequence beat - replacement ship/lifeboat source",
        "source_still_path": VIZ_SHORT_ROOT
        / "motion_contact_sheet/pass_03_apple_subject_motion_shot10_repair/source_stills/shot_10_event_01_ship_lifeboat_repair_from_rms_titanic_3.png",
        "motion_intent": "water-only lower-third shimmer under a locked Titanic ship profile",
        "reject_if": "ship hull, portholes, lifeboats, rigging, or funnels move; water edge halos; modern synthetic shimmer",
        "amplitude_x": 2.4,
        "amplitude_y": 0.7,
        "speed": 0.95,
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


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


def ffprobe(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate:format=duration",
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
    return json.loads(completed.stdout)


def prepare_source(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if image.size == (WIDTH, HEIGHT):
        return image
    return ImageOps.fit(image, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def water_mask(shot_id: str) -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    if shot_id == "shot_10":
        draw.polygon([(0, 718), (WIDTH, 700), (WIDTH, HEIGHT), (0, HEIGHT)], fill=255)
        return mask.filter(ImageFilter.GaussianBlur(16))

    if shot_id == "shot_07":
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=255)
        keep_boat_and_people = [
            (118, 330),
            (215, 220),
            (340, 230),
            (430, 355),
            (560, 495),
            (560, 865),
            (470, 1018),
            (185, 950),
            (68, 760),
            (62, 520),
        ]
        draw.polygon(keep_boat_and_people, fill=0)
        draw.rectangle((0, HEIGHT - 20, WIDTH, HEIGHT), fill=0)
        return mask.filter(ImageFilter.GaussianBlur(13))

    raise ValueError(f"unsupported shot_id {shot_id}")


def animate_water(base: Image.Image, mask: Image.Image, *, frame_index: int, spec: dict[str, Any]) -> Image.Image:
    arr = np.asarray(base).astype(np.float32)
    h, w = arr.shape[:2]
    phase = (frame_index / FRAME_COUNT) * math.tau * float(spec["speed"])
    warped = np.empty_like(arr)
    for y in range(h):
        src_y = int(round(y + float(spec["amplitude_y"]) * math.sin(phase * 1.3 + y / 41.0)))
        src_y = max(0, min(h - 1, src_y))
        shift = int(round(float(spec["amplitude_x"]) * math.sin(phase + y / 23.0)))
        warped[y] = np.roll(arr[src_y], shift, axis=0)

    yy, xx = np.mgrid[0:h, 0:w]
    shimmer = 1.0 + 0.020 * np.sin(phase * 2.0 + yy / 15.0 + 0.35 * np.sin(xx / 43.0))
    warped = np.clip(warped * shimmer[..., None], 0, 255)

    alpha = np.asarray(mask).astype(np.float32) / 255.0
    blended = arr * (1.0 - alpha[..., None]) + warped * alpha[..., None]
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), "RGB")


def render_clip(spec: dict[str, Any]) -> dict[str, Any]:
    shot_id = str(spec["shot_id"])
    source_path = Path(spec["source_still_path"])
    clip_dir = OUTPUT_ROOT / "clips" / shot_id
    frames_dir = OUTPUT_ROOT / "frames" / shot_id
    audit_dir = OUTPUT_ROOT / "frame_audits" / shot_id
    logs_dir = OUTPUT_ROOT / "logs"
    raw_path = clip_dir / f"{shot_id}__water_mask_motion_pass_04.mp4"
    normalized_path = clip_dir / f"{shot_id}__water_mask_motion_pass_04__no_audio.mp4"
    mask_path = OUTPUT_ROOT / "masks" / f"{shot_id}__water_mask.png"

    base = prepare_source(source_path)
    mask = water_mask(shot_id)
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    mask.save(mask_path)
    frames_dir.mkdir(parents=True, exist_ok=True)
    existing_frames = sorted(frames_dir.glob("frame_*.png"))
    if len(existing_frames) != FRAME_COUNT:
        for frame in existing_frames:
            frame.unlink()
        for index in range(FRAME_COUNT):
            frame = animate_water(base, mask, frame_index=index, spec=spec)
            frame.save(frames_dir / f"frame_{index + 1:04d}.png")

    clip_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-an",
        "-movflags",
        "+faststart",
        str(raw_path),
    ]
    with (logs_dir / f"{shot_id}__encode.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, text=True, check=False)

    normalize_cmd = [
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
    with (logs_dir / f"{shot_id}__normalize_no_audio.log").open("w", encoding="utf-8") as log:
        subprocess.run(normalize_cmd, stdout=log, stderr=subprocess.STDOUT, text=True, check=False)

    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_indices = [1, 25, 49, 73, 97, 121]
    for audit_index in audit_indices:
        frame = Image.open(frames_dir / f"frame_{audit_index:04d}.png").convert("RGB")
        frame.resize((160, 284), Image.Resampling.LANCZOS).save(audit_dir / f"frame_{audit_index:03d}.png")

    info = ffprobe(normalized_path)
    streams = info.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    duration = float(info.get("format", {}).get("duration", 0.0) or 0.0)
    video = video_streams[0] if video_streams else {}
    return {
        "beat_id": shot_id,
        "shot_id": shot_id,
        "candidate_id": f"{shot_id}__water_mask_motion_pass_04",
        "variant_id": "water_mask_motion",
        "variant_label": "deterministic water-mask motion pass 04",
        "source_role": spec["role"],
        "source_still_path": str(source_path),
        "source_still_sha256": sha256_file(source_path),
        "source_still_variant_role": "primary",
        "source_render_size": [WIDTH, HEIGHT],
        "water_mask_path": str(mask_path),
        "water_mask_sha256": sha256_file(mask_path),
        "motion_pipeline": "deterministic_water_mask_motion_v1",
        "motion_strategy": "source_still_water_region_only",
        "ltx_used": False,
        "motion_intent": spec["motion_intent"],
        "reject_if": spec["reject_if"],
        "prompt_variant_id": "titanic_water_only_subject_lock",
        "prompt_text": "Freeze all non-water source content. Animate only the approved water mask with low-amplitude archival shimmer; no new objects, no subject motion, no text.",
        "raw_clip_path": str(raw_path),
        "normalized_clip_path": str(normalized_path),
        "frame_audit_dir": str(audit_dir),
        "frame_audit_paths": [str(path) for path in sorted(audit_dir.glob("frame_*.png"))],
        "target_duration_seconds": TARGET_SECONDS,
        "duration_seconds": duration,
        "fps": FPS,
        "frames": FRAME_COUNT,
        "width": WIDTH,
        "height": HEIGHT,
        "video_info": video,
        "audio_stream_read": "pass: no audio stream" if not audio_streams else "reject: audio stream present",
        "dimension_read": "pass" if (video.get("width"), video.get("height")) == (WIDTH, HEIGHT) else "reject",
        "fps_read": "pass" if video.get("r_frame_rate") == "24/1" else "reject",
        "duration_read": "pass" if duration >= TARGET_SECONDS - 0.05 else "reject",
        "normalized_sha256": sha256_file(normalized_path),
        "raw_sha256": sha256_file(raw_path),
        "archival_motion_in_scope": False,
        "source_derived_reanimation_used": False,
        "generated_stills_used": False,
        "source_still_water_mask_motion_used": True,
        "disposition": "diagnostic only",
        "selected_for_motion_proof": False,
        "selected_for_motion_proof_status": "blocked_pending_human_dp_review",
        "render_status": "completed",
    }


def make_contact_sheet(records: list[dict[str, Any]], output_path: Path) -> None:
    frame_w, frame_h = 136, 242
    source_w, source_h = 136, 242
    margin = 24
    gap = 12
    row_h = 330
    label_w = 270
    canvas_w = margin * 2 + label_w + source_w + gap + 6 * (frame_w + gap)
    canvas_h = margin * 2 + 76 + row_h * len(records)
    canvas = Image.new("RGB", (canvas_w, canvas_h), (14, 14, 14))
    draw = ImageDraw.Draw(canvas)
    title_font = font(28)
    label_font = font(18)
    small_font = font(14)
    draw.text((margin, margin), "Titanic Water-Mask Motion Repair Pass 04", fill=(245, 245, 245), font=title_font)
    draw.text(
        (margin, margin + 38),
        "Shot 07 and shot 10; water-only deterministic motion; subjects and ship geometry locked",
        fill=(190, 190, 190),
        font=small_font,
    )
    y = margin + 76
    for record in records:
        draw.rectangle((margin, y, canvas_w - margin, y + row_h - 10), fill=(24, 24, 24))
        x = margin + 12
        draw.text((x, y + 14), record["shot_id"], fill=(245, 245, 245), font=label_font)
        draw.text((x, y + 42), "water-only repair", fill=(210, 210, 210), font=small_font)
        wrapped = [record["reject_if"][i : i + 34] for i in range(0, len(record["reject_if"]), 34)]
        for index, line in enumerate(wrapped[:6]):
            draw.text((x, y + 70 + index * 17), line, fill=(170, 170, 170), font=small_font)

        x = margin + label_w
        source = prepare_source(Path(record["source_still_path"]))
        source_thumb = ImageOps.contain(source, (source_w, source_h))
        source_canvas = Image.new("RGB", (source_w, source_h), (0, 0, 0))
        source_canvas.paste(source_thumb, ((source_w - source_thumb.width) // 2, (source_h - source_thumb.height) // 2))
        canvas.paste(source_canvas, (x, y + 54))
        draw.text((x, y + 24), "source", fill=(190, 190, 190), font=small_font)
        x += source_w + gap
        for frame_path in record["frame_audit_paths"][:6]:
            frame = Image.open(frame_path).convert("RGB")
            frame_thumb = ImageOps.contain(frame, (frame_w, frame_h))
            frame_canvas = Image.new("RGB", (frame_w, frame_h), (0, 0, 0))
            frame_canvas.paste(frame_thumb, ((frame_w - frame_thumb.width) // 2, (frame_h - frame_thumb.height) // 2))
            canvas.paste(frame_canvas, (x, y + 54))
            x += frame_w + gap
        y += row_h
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def build_preview_reel(records: list[dict[str, Any]], output_path: Path) -> Path:
    concat_path = output_path.parent / "preview_concat_pass_04.txt"
    write_text(
        concat_path,
        "\n".join(f"file '{record['normalized_clip_path']}'" for record in records),
    )
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
    subprocess.run(command, capture_output=True, text=True, check=False)
    return output_path


def write_supporting_docs(manifest_path: Path, contact_sheet_path: Path, preview_reel_path: Path, records: list[dict[str, Any]]) -> None:
    review_path = PRODUCTION_ROOT / "motion_contact_sheet_review_water_mask_motion_pass_04.md"
    handoff_path = PRODUCTION_ROOT / "motion_contact_sheet_handoff_water_mask_motion_pass_04.yaml"
    request_path = PRODUCTION_ROOT / "water_mask_motion_repair_request_pass_04.md"

    rows = "\n".join(
        "| `{shot}` | `{source}` | `{mask}` | {intent} | {reject} |".format(
            shot=record["shot_id"],
            source=record["source_still_path"],
            mask=record["water_mask_path"],
            intent=record["motion_intent"],
            reject=record["reject_if"],
        )
        for record in records
    )
    write_text(
        request_path,
        f"""# Titanic Water-Mask Motion Repair Request Pass 04

## Gate

- `stage`: `motion contact sheet diagnostic`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `pass_id`: `{PASS_ID}`
- `created_at`: `{utc_now()}`
- `motion_strategy`: `source_still_water_region_only`
- `ltx_used`: `false`
- `archival_motion_in_scope`: `false`
- `source_derived_reanimation_used`: `false`
- `generated_stills_used`: `false`
- `current_pass03_final_remains_active`: `true`
- `may_start_motion_video_proof`: `false`
- `may_start_final_export`: `false`

## Rows

| shot_id | source_still_path | water_mask_path | motion_intent | reject_if |
| --- | --- | --- | --- | --- |
{rows}
""",
    )

    qa_rows = "\n".join(
        "| `{shot}` | `{duration:.3f}` | `{audio}` | `{dimensions}` | `{fps}` | `{sha}` |".format(
            shot=record["shot_id"],
            duration=float(record["duration_seconds"]),
            audio=record["audio_stream_read"],
            dimensions=record["dimension_read"],
            fps=record["fps_read"],
            sha=record["normalized_sha256"],
        )
        for record in records
    )
    write_text(
        review_path,
        f"""# Titanic Water-Mask Motion Contact Sheet Pass 04

## Review Gate

- `stage`: `motion contact sheet`
- `episode_id`: `{EPISODE_ID}`
- `short_id`: `{SHORT_ID}`
- `pass_id`: `{PASS_ID}`
- `created_at`: `{utc_now()}`
- `motion_contact_sheet_manifest_path`: `{manifest_path}`
- `motion_contact_sheet_path`: `{contact_sheet_path}`
- `motion_contact_sheet_preview_reel_path`: `{preview_reel_path}`
- `candidate_count`: `{len(records)}`
- `completed_candidate_count`: `{len(records)}`
- `motion_strategy`: `source_still_water_region_only`
- `ltx_used`: `false`
- `disposition`: `diagnostic only pending human/DP MP4 review`
- `current_pass03_final_status`: `remains active keeper`
- `may_start_motion_video_proof`: `false`
- `may_start_final_export`: `false`

## Candidate QA

| shot_id | duration | audio | dimensions | fps | normalized_sha256 |
| --- | ---: | --- | --- | --- | --- |
{qa_rows}

## Human Review Checks

- Reject if `shot_07` moves faces, bodies, oars, or boat rim.
- Reject if `shot_10` moves the hull, portholes, lifeboats, rigging, or funnels.
- Reject if the mask boundary is visible or the water reads modern/synthetic.
""",
    )

    write_text(
        handoff_path,
        "\n".join(
            [
                "stage: motion_contact_sheet_water_mask_motion_pass_04_handoff",
                f"episode_id: {EPISODE_ID}",
                f"short_id: {SHORT_ID}",
                f"gate_id: {PASS_ID}",
                f"created_at: {utc_now()}",
                "disposition: diagnostic only",
                "motion_strategy: source_still_water_region_only",
                "ltx_used: false",
                "archival_motion_in_scope: false",
                "source_derived_reanimation_used: false",
                "generated_stills_used: false",
                "current_pass03_final_remains_active: true",
                "may_start_motion_video_proof: false",
                "may_start_final_export: false",
                f"motion_contact_sheet_manifest_path: {manifest_path}",
                f"motion_contact_sheet_path: {contact_sheet_path}",
                f"motion_contact_sheet_preview_reel_path: {preview_reel_path}",
                f"gate_review_path: {review_path}",
                "next_action: Human/DP review of water-only motion for shot_07 and shot_10; decide whether to use as deterministic repair or run LTX water-first rerenders.",
            ]
        ),
    )


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    records = [render_clip(spec) for spec in SHOT_SPECS]
    contact_sheet_path = OUTPUT_ROOT / "titanic_water_mask_motion_repair_contact_sheet_pass_04.png"
    preview_reel_path = OUTPUT_ROOT / "titanic_water_mask_motion_repair_preview_reel_pass_04.mp4"
    manifest_path = OUTPUT_ROOT / "titanic_water_mask_motion_repair_manifest_pass_04.json"
    make_contact_sheet(records, contact_sheet_path)
    build_preview_reel(records, preview_reel_path)
    payload = {
        "stage": "motion_contact_sheet",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "pass_id": PASS_ID,
        "created_at": utc_now(),
        "motion_strategy": "source_still_water_region_only",
        "ltx_used": False,
        "archival_motion_in_scope": False,
        "source_derived_reanimation_used": False,
        "generated_stills_used": False,
        "source_still_water_mask_motion_used": True,
        "current_pass03_final_remains_active": True,
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "frames": FRAME_COUNT,
        "target_duration_seconds": TARGET_SECONDS,
        "motion_candidates": records,
        "candidate_count": len(records),
        "completed_candidate_count": len(records),
        "contact_sheet_path": str(contact_sheet_path),
        "contact_sheet_sha256": sha256_file(contact_sheet_path),
        "preview_reel_path": str(preview_reel_path),
        "preview_reel_sha256": sha256_file(preview_reel_path),
        "disposition": "diagnostic only pending human/DP MP4 review",
        "may_start_motion_video_proof": False,
        "may_start_final_export": False,
    }
    write_json(manifest_path, payload)
    write_supporting_docs(manifest_path, contact_sheet_path, preview_reel_path, records)
    print(f"INFO  Manifest: {manifest_path}")
    print(f"INFO  Contact sheet: {contact_sheet_path}")
    print(f"INFO  Preview reel: {preview_reel_path}")
    print(f"INFO  Completed candidates: {len(records)}/{len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
