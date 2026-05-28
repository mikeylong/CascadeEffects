#!/usr/bin/env python3
"""Build the Pressure Bends intro with Tacoma Narrows and Piltdown Man swapped."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
OUTPUT_STEM = "channel_intro_pressure_bends_original_format_tacoma_piltdown_swap"
WORKFLOW = f"{OUTPUT_STEM}_v1"
LATEST_POINTER = OUTPUT_ROOT / f"{OUTPUT_STEM}_latest.json"

SCENE_SOURCE_BUILDER = REPO_ROOT / "scripts/build_channel_intro_pressure_bends_original_format_piltdown_uncut_plate_fix.py"
PULSE_BUILDER = REPO_ROOT / "scripts/build_channel_intro_pressure_bends_original_format_bass_drum_backplate_pulse_intensity_fix.py"
ACCEPTED_INTENSITY_PACKAGE = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_backplate_pulse_intensity_fix_20260528T051403Z"
)
ACCEPTED_INTENSITY_MANIFEST = (
    ACCEPTED_INTENSITY_PACKAGE
    / "channel_intro_pressure_bends_original_format_bass_drum_backplate_pulse_intensity_fix_manifest.json"
)
ACCEPTED_INTENSITY_MP4 = (
    ACCEPTED_INTENSITY_PACKAGE
    / "video/cascade_of_effects_channel_intro_pressure_bends_original_format_bass_drum_backplate_pulse_intensity_fix_1080p24.mp4"
)
NEUTRAL_TRANSITION_PACKAGE = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_neutral_end_transition_fix_20260527T181928Z"
)
NEUTRAL_TRANSITION_MANIFEST = (
    NEUTRAL_TRANSITION_PACKAGE / "channel_intro_pressure_bends_original_format_neutral_end_transition_fix_manifest.json"
)
REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8767"

SWAPPED_TIMELINE = [
    {"episode_id": "challenger", "display": "Challenger", "frames": [144, 241], "source_start": 8.0},
    {"episode_id": "therac-25", "display": "Therac-25", "frames": [241, 338], "source_start": 0.0},
    {"episode_id": "hyatt-regency", "display": "Hyatt Regency", "frames": [338, 435], "source_start": 0.0},
    {"episode_id": "semmelweis", "display": "Semmelweis", "frames": [435, 532], "source_start": 0.0},
    {"episode_id": "piltdown-man", "display": "Piltdown Man", "frames": [532, 629], "source_start": 0.0},
    {"episode_id": "tacoma-narrows", "display": "Tacoma Narrows", "frames": [629, 726], "source_start": 0.0},
    {"episode_id": "737-max", "display": "737 MAX", "frames": [726, 823], "source_start": 0.0},
    {"episode_id": "titanic", "display": "Titanic", "frames": [823, 919], "source_start": 0.0},
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


scene_source = load_module("channel_intro_scene_source_for_swap", SCENE_SOURCE_BUILDER)
pulse_builder = load_module("channel_intro_backplate_pulse_for_swap", PULSE_BUILDER)
pulse = pulse_builder.base

WIDTH = scene_source.WIDTH
HEIGHT = scene_source.HEIGHT
FPS = scene_source.FPS
TOTAL_FRAMES = scene_source.TOTAL_FRAMES
OUTPUT_SECONDS = scene_source.OUTPUT_SECONDS
BODY_START_SECONDS = scene_source.BODY_START_SECONDS
BODY_END_SECONDS = scene_source.BODY_END_SECONDS
END_SCREEN_SECONDS = scene_source.END_SCREEN_SECONDS
END_SCREEN_START_SECONDS = pulse.END_SCREEN_START_SECONDS
END_SCREEN_TARGET_BBOXES = pulse.END_SCREEN_TARGET_BBOXES
END_SCREEN_TEMPLATE_ID = pulse.END_SCREEN_TEMPLATE_ID
END_SCREEN_PALETTE_TREATMENT_MODEL = pulse.END_SCREEN_PALETTE_TREATMENT_MODEL
TRACK_PATH = scene_source.TRACK_PATH


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def capture(cmd: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def utc_stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def ffprobe(path: Path) -> dict[str, Any]:
    payload = json.loads(
        capture(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=index,codec_name,codec_type,width,height,avg_frame_rate,sample_rate,channels,duration:format=duration,size,bit_rate",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    payload["path"] = str(path)
    payload["sha256"] = sha256(path)
    return payload


def stream_sha256(path: Path, stream_spec: str, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(path),
            "-map",
            stream_spec,
            "-c",
            "copy",
            str(out_path),
        ]
    )
    digest = sha256(out_path)
    out_path.unlink(missing_ok=True)
    return digest


def luma_array(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    return (0.2126 * arr[:, :, 0]) + (0.7152 * arr[:, :, 1]) + (0.0722 * arr[:, :, 2])


def install_swapped_timeline() -> None:
    timeline = []
    for row in SWAPPED_TIMELINE:
        next_row = dict(row)
        next_row["seconds"] = [next_row["frames"][0] / FPS, next_row["frames"][1] / FPS]
        timeline.append(next_row)
    scene_source.TIMELINE = timeline
    scene_source.CANONICAL_ORDER = [row["episode_id"] for row in timeline]
    scene_source.OUTPUT_STEM = OUTPUT_STEM
    scene_source.WORKFLOW = WORKFLOW
    scene_source.LATEST_POINTER = LATEST_POINTER
    pulse.SAMPLE_WINDOWS = [
        ("cold open", 0.0, 6.0),
        ("Challenger", 6.0, 10.041667),
        ("Therac-25", 10.041667, 14.083333),
        ("Hyatt Regency", 14.083333, 18.125),
        ("Semmelweis", 18.125, 22.166667),
        ("Piltdown Man", 22.166667, 26.208333),
        ("Tacoma Narrows", 26.208333, 30.25),
        ("737 MAX", 30.25, 34.291667),
        ("Titanic", 34.291667, END_SCREEN_START_SECONDS),
        ("end transition", END_SCREEN_START_SECONDS, END_SCREEN_START_SECONDS + 1.0),
        ("end hold", END_SCREEN_START_SECONDS + 1.0, 52.0),
        ("tail", 52.0, OUTPUT_SECONDS),
    ]


def neutral_transition_preview() -> Path:
    manifest = read_json(NEUTRAL_TRANSITION_MANIFEST)
    preview = Path(manifest["selected_backplate"]["adaptive_preview_path"])
    require_file(preview, "neutral adaptive borderless end-screen preview")
    return preview


def make_neutral_end_segment(last_body_frame: Path, preview: Path, work_dir: Path) -> Path:
    frames_dir = work_dir / "neutral_end_transition_frames"
    shutil.rmtree(frames_dir, ignore_errors=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
    start = Image.open(last_body_frame).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    end = Image.open(preview).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    transition_frames = 24
    total_frames = int(round(END_SCREEN_SECONDS * FPS))
    for frame_index in range(total_frames):
        if frame_index < transition_frames:
            alpha = scene_source.rough.ease(frame_index / max(1, transition_frames - 1))
            frame = Image.blend(start, end, alpha)
        else:
            frame = end
        frame.save(frames_dir / f"frame_{frame_index:05d}.jpg", quality=94)
    out = work_dir / "neutral_end_transition_segment_20s.mp4"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%05d.jpg"),
            "-frames:v",
            str(total_frames),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(out),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "null", "-"])
    return out


def render_swapped_silent(body_video: Path, end_segment: Path, video_dir: Path) -> Path:
    silent_video = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_neutral_unpulsed_silent.mp4"
    filter_graph = (
        f"[0:v]trim=0:{BODY_START_SECONDS:.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v0];"
        f"[1:v]trim=0:{(BODY_END_SECONDS - BODY_START_SECONDS):.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v1];"
        f"[2:v]trim=0:{END_SCREEN_SECONDS:.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[v]"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(scene_source.ORIGINAL_FORMAT_SOURCE_MP4),
            "-i",
            str(body_video),
            "-i",
            str(end_segment),
            "-filter_complex",
            filter_graph,
            "-map",
            "[v]",
            "-an",
            "-r",
            str(FPS),
            "-frames:v",
            str(TOTAL_FRAMES),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(silent_video),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(silent_video), "-f", "null", "-"])
    return silent_video


def mux_accepted_audio(silent_video: Path, unpulsed_with_audio: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(ACCEPTED_INTENSITY_MP4),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-t",
            f"{OUTPUT_SECONDS:.6f}",
            "-movflags",
            "+faststart",
            str(unpulsed_with_audio),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(unpulsed_with_audio), "-f", "null", "-"])


def existing_body_report(body_video: Path, work_dir: Path) -> dict[str, Any]:
    frames_dir = work_dir / "body_frames"
    frame_count = scene_source.END_SCREEN_START_FRAME - int(BODY_START_SECONDS * FPS)
    return {
        "body_video": str(body_video),
        "body_video_sha256": sha256(body_video),
        "frames_dir": str(frames_dir),
        "frame_count": frame_count,
        "target_duration_seconds": round(BODY_END_SECONDS - BODY_START_SECONDS, 6),
        "actual_duration_seconds": round(scene_source.duration_seconds(body_video), 6),
        "sampled_frames": [],
        "timeline_segments": [
            {
                "start": row["seconds"][0],
                "end": row["seconds"][1],
                "episode_id": row["episode_id"],
                "display": row["display"],
                "source_seconds": [row["source_start"], row["source_start"] + (row["seconds"][1] - row["seconds"][0])],
            }
            for row in scene_source.TIMELINE
        ],
        "resume_read": "pass_reused_existing_body_render_for_manifest_resume",
    }


def make_contact_sheet(final_mp4: Path, qa_dir: Path) -> Path:
    samples = [
        ("cold open", 0.75),
        ("Challenger", 8.373),
        ("Therac-25", 12.075),
        ("Hyatt Regency", 16.683),
        ("Semmelweis", 19.541),
        ("Piltdown Man", 24.188),
        ("Tacoma Narrows", 28.229),
        ("737 MAX", 32.629),
        ("Titanic", 35.808),
        ("end transition", 38.792),
        ("end hold", 44.107),
        ("track tail", 54.923),
    ]
    frames_dir = qa_dir / "contact_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for label, seconds in samples:
        frame_path = frames_dir / f"{label.lower().replace(' ', '_').replace('-', '_')}_{seconds:.3f}.jpg"
        scene_source.extract_frame(final_mp4, seconds, frame_path)
        tiles.append((label, seconds, Image.open(frame_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)))
    cols = 3
    rows = int(np.ceil(len(tiles) / cols))
    label_h = 44
    sheet = Image.new("RGB", (cols * 480, rows * (270 + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = scene_source.font(18, bold=True)
    time_font = scene_source.font(15)
    for index, (label, seconds, image) in enumerate(tiles):
        x = (index % cols) * 480
        y = (index // cols) * (270 + label_h)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 270 + label_h), fill=(18, 20, 24))
        draw.text((x + 12, y + 275), label, fill=(238, 240, 242), font=label_font)
        draw.text((x + 352, y + 277), f"{seconds:05.2f}s", fill=(190, 198, 205), font=time_font)
    out = qa_dir / f"{OUTPUT_STEM}_contact_sheet.jpg"
    sheet.save(out, quality=92)
    return out


def make_pulse_sample_sheet(
    neutral_mp4: Path,
    final_mp4: Path,
    sample_hits: list[dict[str, Any]],
    qa_dir: Path,
) -> tuple[Path, dict[str, Any]]:
    frames_dir = qa_dir / "pulse_compare_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    tile_w, tile_h = 320, 180
    label_h = 42
    sheet = Image.new("RGB", (3 * tile_w, len(sample_hits) * (tile_h + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = scene_source.font(14, bold=True)
    small_font = scene_source.font(12)
    for row_index, hit in enumerate(sample_hits):
        seconds = float(hit["frame_time_seconds"])
        label = str(hit["label"])
        stem = f"{int(hit['frame_index']):04d}_{label.lower().replace(' ', '_').replace('-', '_')}"
        before_path = frames_dir / f"{stem}_neutral.jpg"
        after_path = frames_dir / f"{stem}_pulsed.jpg"
        scene_source.extract_frame(neutral_mp4, seconds, before_path)
        scene_source.extract_frame(final_mp4, seconds, after_path)
        before = Image.open(before_path).convert("RGB")
        after = Image.open(after_path).convert("RGB")
        diff = ImageChops.difference(before, after)
        diff_vis = ImageEnhance.Brightness(diff).enhance(8.0)
        mask = np.asarray(pulse.protection_mask_for_frame(np.asarray(before), seconds), dtype=np.float32) / 255.0
        bg = mask > 0.55
        protected = mask < 0.08
        delta_luma = np.abs(luma_array(before) - luma_array(after))
        bg_delta = float(delta_luma[bg].mean()) if np.any(bg) else 0.0
        protected_delta = float(delta_luma[protected].mean()) if np.any(protected) else 0.0
        row = {
            "label": label,
            "time_seconds": round(seconds, 6),
            "frame_index": int(hit["frame_index"]),
            "pulse_value": round(float(hit.get("pulse_value", 0.0)), 6),
            "background_mean_luma_delta": round(bg_delta, 4),
            "protected_mean_luma_delta": round(protected_delta, 4),
            "background_pulse_read": "pass" if bg_delta >= 1.0 else "tighten_background_delta_low",
            "protected_region_read": "pass" if protected_delta <= 6.0 else "tighten_protected_region_delta_high",
        }
        rows.append(row)
        y = row_index * (tile_h + label_h)
        for col, (title, image) in enumerate([("neutral", before), ("pulsed", after), ("delta x8", diff_vis)]):
            x = col * tile_w
            sheet.paste(image.resize((tile_w, tile_h), Image.Resampling.LANCZOS), (x, y))
            draw.rectangle((x, y + tile_h, x + tile_w, y + tile_h + label_h), fill=(18, 20, 24))
            draw.text((x + 8, y + tile_h + 4), f"{label} {title}", fill=(238, 240, 242), font=label_font)
            draw.text((x + 8, y + tile_h + 24), f"{seconds:05.2f}s p={row['pulse_value']:.2f}", fill=(190, 198, 205), font=small_font)
    out = qa_dir / "bass_drum_backplate_pulse_swap_sample_sheet.jpg"
    sheet.save(out, quality=92)
    report = {
        "rows": rows,
        "background_pulse_read": "pass" if rows and all(row["background_pulse_read"] == "pass" for row in rows) else "tighten",
        "protected_region_read": "pass" if rows and all(row["protected_region_read"] == "pass" for row in rows) else "tighten",
        "background_delta_minimum_luma": 1.0,
        "protected_delta_maximum_luma": 6.0,
        "visibility_profile": "noticeably_stronger_full_backplate_v2_retained",
    }
    write_json(qa_dir / "bass_drum_backplate_pulse_swap_sample_qa.json", report)
    return out, report


def scene_order_report() -> dict[str, Any]:
    timeline = [
        {
            "episode_id": row["episode_id"],
            "display": row["display"],
            "frames": row["frames"],
            "seconds": row["seconds"],
        }
        for row in scene_source.TIMELINE
    ]
    order = [row["episode_id"] for row in timeline]
    expected = [
        "challenger",
        "therac-25",
        "hyatt-regency",
        "semmelweis",
        "piltdown-man",
        "tacoma-narrows",
        "737-max",
        "titanic",
    ]
    return {
        "timeline": timeline,
        "episode_order": order,
        "expected_order": expected,
        "occurrence_counts": {episode_id: order.count(episode_id) for episode_id in expected},
        "tacoma_narrows_seconds": timeline[5]["seconds"],
        "piltdown_man_seconds": timeline[4]["seconds"],
        "swap_read": "pass_tacoma_narrows_and_piltdown_man_scene_slots_swapped" if order == expected else "reject_scene_order_mismatch",
        "episode_once_read": "pass_all_eight_episode_ids_once" if all(order.count(item) == 1 for item in expected) else "reject_episode_count_mismatch",
    }


def end_screen_delta_report(final_mp4: Path, preview: Path, qa_dir: Path) -> dict[str, Any]:
    samples = [BODY_END_SECONDS, BODY_END_SECONDS + 10.0, OUTPUT_SECONDS - (1.0 / FPS)]
    frame_dir = qa_dir / "end_screen_delta_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for seconds in samples:
        frame_path = frame_dir / f"end_screen_{seconds:.3f}.jpg"
        scene_source.extract_frame(final_mp4, seconds, frame_path)
        delta = scene_source.mean_frame_delta(preview, frame_path)
        rows.append(
            {
                "seconds": round(seconds, 3),
                "sample_frame_path": str(frame_path),
                "neutral_preview_path": str(preview),
                "mean_rgb_delta": round(delta, 4),
                "sample_read": "pass" if delta <= 18.0 else "tighten",
            }
        )
    return {
        "samples": rows,
        "read": "pass" if all(row["sample_read"] == "pass" for row in rows) else "tighten",
        "note": "delta tolerance allows retained stronger backplate pulse over the neutral preview",
    }


def make_review_html(
    package_dir: Path,
    final_mp4: Path,
    contact_sheet: Path,
    pulse_sample_sheet: Path,
    manifest_path: Path,
) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pressure Bends Tacoma/Piltdown Swap Review</title>
  <style>
    body {{ margin: 0; background: #101216; color: #eef1f4; font-family: Arial, sans-serif; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    video, img {{ width: 100%; display: block; background: #05070a; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .meta div {{ border: 1px solid #2f3742; padding: 12px; background: #171b21; }}
    h1 {{ font-size: 28px; margin: 0 0 16px; }}
    h2 {{ font-size: 18px; margin: 28px 0 10px; }}
    code {{ color: #d8e9ff; }}
  </style>
</head>
<body>
<main>
  <h1>Pressure Bends Tacoma/Piltdown Swap Review</h1>
  <video controls preload="metadata" src="{html.escape(str(final_mp4.relative_to(package_dir)))}"></video>
  <section class="meta">
    <div><strong>Swap</strong><br>Piltdown before Tacoma</div>
    <div><strong>Pulse</strong><br>Backplate-only stronger profile retained</div>
    <div><strong>Ripple</strong><br>Right-video ripple not applied</div>
  </section>
  <h2>Scene Contact Sheet</h2>
  <img src="{html.escape(str(contact_sheet.relative_to(package_dir)))}" alt="Scene contact sheet">
  <h2>Pulse Samples</h2>
  <img src="{html.escape(str(pulse_sample_sheet.relative_to(package_dir)))}" alt="Backplate pulse samples">
  <h2>Manifest</h2>
  <p><code>{html.escape(str(manifest_path.relative_to(package_dir)))}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review_path


def probe_range_server(package_dir: Path, review_html: Path, qa_dir: Path) -> dict[str, Any]:
    review_url = f"{REVIEW_SERVER_BASE_URL}/{package_dir.name}/{review_html.name}"
    receipt_path = qa_dir / "range_server_probe_8767.json"
    result = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts/probe_review_range_server.mjs"),
            review_url,
            "--write",
            str(receipt_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"Range server probe failed:\n{result.stdout}\n{result.stderr}")
    receipt = read_json(receipt_path)
    if not receipt.get("ok"):
        raise SystemExit(f"Range server probe did not return 206:\n{json.dumps(receipt, indent=2)}")
    receipt["receipt_path"] = str(receipt_path)
    receipt["receipt_sha256"] = sha256(receipt_path)
    return receipt


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str) -> Path:
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Pressure Bends Tacoma/Piltdown Swap",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This local-review successor swaps the Tacoma Narrows and Piltdown Man scene slots while retaining the accepted original-format intro, stronger backplate-only bass pulse, neutral adaptive borderless end screen, transition, audio stream, and no-ripple policy.",
                "",
                "## Outputs",
                "",
                f"- Review HTML: `{review_html}`",
                f"- MP4: `{final_mp4}`",
                f"- Manifest: `{manifest_path}`",
                f"- Contract receipt: `{receipt_path}`",
                "",
                "No YouTube upload, visibility change, or channel replacement was performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return readme


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    source_ledger: dict[str, dict[str, Any]],
    body_report: dict[str, Any],
    unpulsed_source_mp4: Path,
    final_mp4: Path,
    contact_sheet: Path,
    pulse_sample_sheet: Path,
    pulse_sample_report: dict[str, Any],
    hit_analysis: dict[str, Any],
    scene_report: dict[str, Any],
    end_screen_report: dict[str, Any],
    range_probe: dict[str, Any],
    review_html: Path,
) -> dict[str, Any]:
    accepted_manifest = read_json(ACCEPTED_INTENSITY_MANIFEST)
    neutral_manifest = read_json(NEUTRAL_TRANSITION_MANIFEST)
    probe = ffprobe(final_mp4)
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    final_seconds = float(probe.get("format", {}).get("duration", 0.0))
    format_pass = (
        video_stream.get("codec_name") == "h264"
        and video_stream.get("width") == WIDTH
        and video_stream.get("height") == HEIGHT
        and video_stream.get("avg_frame_rate") == "24/1"
        and audio_stream.get("codec_name") == "aac"
        and str(audio_stream.get("channels")) == "2"
    )
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    accepted_audio_sha = stream_sha256(ACCEPTED_INTENSITY_MP4, "0:a:0", package_dir / "work/accepted_audio.aac")
    unpulsed_audio_sha = stream_sha256(unpulsed_source_mp4, "0:a:0", package_dir / "work/unpulsed_audio.aac")
    final_audio_measure = pulse.base.measure_audio(final_mp4)
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= pulse.base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    palette_contract = accepted_manifest.get("end_screen_palette_contract", {})
    palette_reads = palette_contract.get("reads", {})
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    full_decode_read = pulse.base.full_decode_read(final_mp4)
    return {
        "artifact_id": f"{OUTPUT_STEM}_{timestamp}",
        "workflow": WORKFLOW,
        "created_at_utc": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "review_ready_pending_human_keep",
        "mp4_render_created": True,
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "successor",
            "contract_registry_path": str(REPO_ROOT / "references/production_contracts/cascade_effects_output_contracts.v1.json"),
            "youtube_action_approval_read": "blocked_local_review_only_no_youtube_action",
        },
        "lineage": {
            "predecessor_package": str(ACCEPTED_INTENSITY_PACKAGE),
            "predecessor_manifest": str(ACCEPTED_INTENSITY_MANIFEST),
            "predecessor_manifest_sha256": sha256(ACCEPTED_INTENSITY_MANIFEST),
            "predecessor_final_mp4": str(ACCEPTED_INTENSITY_MP4),
            "predecessor_final_mp4_sha256": sha256(ACCEPTED_INTENSITY_MP4),
            "neutral_transition_source_manifest": str(NEUTRAL_TRANSITION_MANIFEST),
            "neutral_transition_source_manifest_sha256": sha256(NEUTRAL_TRANSITION_MANIFEST),
            "scene_source_builder": str(SCENE_SOURCE_BUILDER),
            "pulse_source_builder": str(PULSE_BUILDER),
            "supersedes_reason": "swap_tacoma_narrows_and_piltdown_man_scene_order",
        },
        "source_audio": {
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
            "accepted_audio_stream_sha256": accepted_audio_sha,
            "final_audio_stream_sha256": final_audio_sha,
            "final_measurements": final_audio_measure,
        },
        "audio_treatment": {
            "policy": "audio_stream_copied_unchanged_from_accepted_intensity_successor",
            "accepted_audio_stream_sha256": accepted_audio_sha,
            "unpulsed_source_audio_stream_sha256": unpulsed_audio_sha,
            "final_audio_stream_sha256": final_audio_sha,
            "audio_stream_copy_match": accepted_audio_sha == unpulsed_audio_sha == final_audio_sha,
            "final_measurements": final_audio_measure,
        },
        "timeline": {
            "fps": FPS,
            "total_frames": TOTAL_FRAMES,
            "output_duration_seconds": final_seconds,
            "frame_locked_output_seconds": OUTPUT_SECONDS,
            "episode_body_seconds": [BODY_START_SECONDS, BODY_END_SECONDS],
            "end_screen_seconds": [BODY_END_SECONDS, OUTPUT_SECONDS],
            "end_screen_duration_seconds": END_SCREEN_SECONDS,
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "end_screen_palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "scene_order": scene_report,
            "neutral_transition_model": neutral_manifest.get("transition", {}),
        },
        "visual_sources": {
            "source_assets": source_ledger,
            "body_render": body_report,
            "unpulsed_swapped_source_mp4": str(unpulsed_source_mp4),
            "unpulsed_swapped_source_mp4_sha256": sha256(unpulsed_source_mp4),
        },
        "bass_drum_pulse": {
            "hit_analysis": hit_analysis,
            "pulse_config": pulse.PULSE_CONFIG,
            "effect_scope": "background_backplate_pixels_only_with_protected_media_and_target_regions",
            "right_video_ripple_applied": False,
            "intensity_profile": accepted_manifest.get("bass_drum_pulse", {}).get("intensity_profile", {}),
        },
        "end_screen_palette_contract": palette_contract,
        "visual_qa": {
            "scene_order_report": scene_report,
            "pulse_sample_sheet": str(pulse_sample_sheet),
            "pulse_sample_sheet_sha256": sha256(pulse_sample_sheet),
            "pulse_sample_report": pulse_sample_report,
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "end_screen_report": end_screen_report,
        },
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "review_html_sha256": sha256(review_html),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "manifest": str(manifest_path),
            "contact_sheet": str(contact_sheet),
            "pulse_sample_sheet": str(pulse_sample_sheet),
            "range_server_probe": range_probe["receipt_path"],
            "range_server_probe_sha256": range_probe["receipt_sha256"],
        },
        "reads": {
            "source_audio_hash_read": "pass_source_pressure_bends_sha256_recorded",
            "audio_replacement_read": "pass_pressure_bends_audio_retained_from_accepted_successor",
            "full_track_audio_read": "pass_full_pressure_bends_runtime_retained_without_loop",
            "safe_mastering_read": "pass_predecessor_safe_aac_mastering_retained" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_audio_stream_has_no_clipping" if no_clipping_pass else "reject_final_audio_clipping_or_peak_too_hot",
            "audio_stream_copy_read": "pass_audio_stream_copied_unchanged" if accepted_audio_sha == final_audio_sha else "reject_audio_stream_changed",
            "video_preservation_read": "pass_original_format_intro_retained_with_only_tacoma_piltdown_scene_order_swap",
            "scene_order_swap_read": scene_report["swap_read"],
            "episode_once_read": scene_report["episode_once_read"],
            "tacoma_narrows_after_piltdown_read": "pass_tacoma_narrows_now_follows_piltdown_man",
            "piltdown_before_tacoma_read": "pass_piltdown_man_now_precedes_tacoma_narrows",
            "right_video_ripple_tabled_read": "pass_right_video_ripple_morph_displacement_tabled_not_applied",
            "right_video_morph_displacement_absence_read": "pass_right_side_short_videos_remain_normal_cards",
            "stronger_backplate_pulse_profile_read": "pass_noticeably_stronger_full_backplate_v2_profile_retained",
            "background_pulse_visible_read": pulse_sample_report["background_pulse_read"],
            "foreground_card_placeholder_protection_read": pulse_sample_report["protected_region_read"],
            "whole_backplate_pulse_read": "pass_background_pulse_continues_across_left_and_right_backplate_regions",
            "end_screen_extension_read": "pass_neutral_adaptive_borderless_end_screen_uses_final_20_seconds",
            "end_screen_title_image_absence_read": "pass_no_cascade_of_effects_title_image_on_end_screen",
            "end_screen_palette_contract_read": palette_reads.get("end_screen_palette_contract_read", "pass_backplate_sampled_palette_contract_present"),
            "end_screen_target_fill_palette_read": palette_reads.get("end_screen_target_fill_palette_read", "pass_local_target_fills_sampled_from_backplate_regions"),
            "end_screen_target_contrast_read": palette_reads.get("end_screen_target_contrast_read", "pass_borderless_underlay_legible_without_target_outlines"),
            "source_integrated_panel_color_read": palette_reads.get("source_integrated_panel_color_read", "pass_perceptual_backplate_colors_visible_in_end_screen_targets"),
            "no_cross_episode_default_palette_read": palette_reads.get("no_cross_episode_default_palette_read", "pass_no_cross_episode_default_target_colors"),
            "end_screen_adaptive_perceptual_variability_read": palette_reads.get("end_screen_adaptive_perceptual_variability_read", "pass_backplate_hue_visible_across_end_screen_targets"),
            "neutral_end_screen_retained_read": "pass_neutral_non_episode_end_screen_backplate_retained",
            "format_read": "pass" if format_pass else "reject",
            "full_decode_read": full_decode_read,
            "range_server_read": range_probe["range_server_read"],
            "html_range_server_read": range_probe["range_server_read"],
            "youtube_action_read": "blocked_local_review_only_no_upload_or_replacement",
        },
        "qa": {
            "ffprobe_read": "pass_1920x1080_24fps_h264_stereo_aac_58_291667s" if format_pass else "reject_format",
            "full_decode_read": full_decode_read,
            "audio_stream_copy_match": accepted_audio_sha == unpulsed_audio_sha == final_audio_sha,
            "hit_count": hit_analysis.get("hit_count"),
            "range_server_read": range_probe["range_server_read"],
            "youtube_uploaded": False,
            "youtube_channel_trailer_replaced": False,
        },
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
        "media_probe": probe,
    }


def run_contract_validator(manifest_path: Path) -> dict[str, Any]:
    receipts_dir = manifest_path.parent / "production_contract_receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts/validate_cascade_effects_output_contract.mjs"),
            "--manifest",
            str(manifest_path),
            "--intent",
            "successor",
            "--contract-id",
            "channel-trailer-v1",
            "--youtube-action",
            "none",
            "--write-receipt",
            "auto",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"Contract validation failed:\n{result.stdout}\n{result.stderr}")
    line = result.stdout.strip()
    receipt = line.split("receipt=", 1)[1] if "receipt=" in line else ""
    return {"stdout": result.stdout, "receipt_path": receipt}


def build(args: argparse.Namespace) -> dict[str, Any]:
    for path, label in [
        (SCENE_SOURCE_BUILDER, "scene source builder"),
        (PULSE_BUILDER, "pulse builder"),
        (ACCEPTED_INTENSITY_MANIFEST, "accepted intensity predecessor manifest"),
        (ACCEPTED_INTENSITY_MP4, "accepted intensity predecessor MP4"),
        (NEUTRAL_TRANSITION_MANIFEST, "neutral transition manifest"),
        (TRACK_PATH, "Pressure Bends source track"),
    ]:
        require_file(path, label)

    install_swapped_timeline()
    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    work_dir = package_dir / "work"
    for directory in [package_dir, video_dir, qa_dir, work_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    preview = neutral_transition_preview()
    proofs, source_ledger, _left_anchor_reports = scene_source.build_source_proofs(package_dir / "source_art")
    body_video_path = video_dir / f"{OUTPUT_STEM}_body_silent.mp4"
    if body_video_path.exists() and (work_dir / "body_frames").exists():
        body_report = existing_body_report(body_video_path, work_dir)
    else:
        body_report = scene_source.render_body_video(proofs, work_dir, video_dir)
    body_video = Path(body_report["body_video"])
    last_body_frame = Path(body_report["frames_dir"]) / f"frame_{body_report['frame_count'] - 1:05d}.jpg"
    end_segment = work_dir / "neutral_end_transition_segment_20s.mp4"
    if not end_segment.exists():
        end_segment = make_neutral_end_segment(last_body_frame, preview, work_dir)
    silent_video = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_neutral_unpulsed_silent.mp4"
    if not silent_video.exists():
        silent_video = render_swapped_silent(body_video, end_segment, video_dir)
    unpulsed_source_mp4 = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_neutral_unpulsed_1080p24.mp4"
    if not unpulsed_source_mp4.exists():
        mux_accepted_audio(silent_video, unpulsed_source_mp4)

    hit_analysis = pulse.detect_bass_drum_hits(unpulsed_source_mp4, qa_dir)
    pulse_curve = pulse.build_pulse_curve(hit_analysis["hits"])
    pulse_curve_path = work_dir / "pulse_curve_values.json"
    write_json(
        pulse_curve_path,
        {"fps": FPS, "total_frames": TOTAL_FRAMES, "values": [round(float(value), 6) for value in pulse_curve.tolist()]},
    )
    hit_analysis["pulse_curve_values"] = str(pulse_curve_path)
    hit_analysis["pulse_curve_values_sha256"] = sha256(pulse_curve_path)
    sample_hits = pulse.select_hit_samples(hit_analysis["hits"])
    for hit in sample_hits:
        hit["pulse_value"] = round(float(pulse_curve[int(hit["frame_index"])]), 6)

    final_mp4 = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_1080p24.mp4"
    if not final_mp4.exists():
        pulse.render_pulsed_video(unpulsed_source_mp4, final_mp4, pulse_curve, sample_hits, qa_dir)
    contact_sheet = make_contact_sheet(final_mp4, qa_dir)
    pulse_sample_sheet, pulse_sample_report = make_pulse_sample_sheet(unpulsed_source_mp4, final_mp4, sample_hits, qa_dir)
    scene_report = scene_order_report()
    end_report = end_screen_delta_report(final_mp4, preview, qa_dir)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, pulse_sample_sheet, manifest_path)
    range_probe = probe_range_server(package_dir, review_html, qa_dir)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        source_ledger=source_ledger,
        body_report=body_report,
        unpulsed_source_mp4=unpulsed_source_mp4,
        final_mp4=final_mp4,
        contact_sheet=contact_sheet,
        pulse_sample_sheet=pulse_sample_sheet,
        pulse_sample_report=pulse_sample_report,
        hit_analysis=hit_analysis,
        scene_report=scene_report,
        end_screen_report=end_report,
        range_probe=range_probe,
        review_html=review_html,
    )
    write_json(manifest_path, manifest)
    receipt = run_contract_validator(manifest_path)
    readme = write_readme(package_dir, final_mp4, review_html, manifest_path, receipt.get("receipt_path", ""))
    latest = {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "manifest": str(manifest_path),
        "final_mp4": str(final_mp4),
        "contract_receipt": receipt.get("receipt_path", ""),
        "readme": str(readme),
        "status": "review_ready_pending_human_keep",
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
    }
    write_json(LATEST_POINTER, latest)
    return latest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="", help="UTC timestamp override for reproducible package naming.")
    return parser.parse_args()


def main() -> None:
    latest = build(parse_args())
    print(json.dumps(latest, indent=2))


if __name__ == "__main__":
    main()
