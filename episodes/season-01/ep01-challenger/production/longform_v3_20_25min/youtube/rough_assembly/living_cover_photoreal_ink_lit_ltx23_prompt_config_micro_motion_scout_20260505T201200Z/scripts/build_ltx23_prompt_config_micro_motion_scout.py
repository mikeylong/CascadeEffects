#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CREATED_UTC = "2026-05-05T20:12:00Z"
PACKET_ID = "living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z"
PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z"
)
REJECTED_LOOP_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z"
)
REJECTED_LOOP_MANIFEST = REJECTED_LOOP_ROOT / "motion_scout_manifest.json"
SOURCE_ART_PATH = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png"
)
EXPECTED_SOURCE_SHA256 = "52f94150037d5aa40633d34b29c137c59c5868e987bc5f8b7f80903f6bc2ac8a"
LTX_BIN = Path("/Users/mike/AI/ltx-2-mlx/.venv/bin/ltx-2-mlx")
LTX_RUNTIME_ROOT = Path("/Users/mike/AI/ltx-2-mlx")
MODEL_REPO = "dgrauet/ltx-2.3-mlx-q8"
TEXT_ENCODER_REPO = "mlx-community/gemma-3-12b-it-4bit"
WIDTH = 960
HEIGHT = 384
FULL_WIDTH = 1920
FULL_HEIGHT = 1080
FRAMES = 145
EXPECTED_RAW_FRAMES = 144
FPS = 24
STEPS = 8
LOOP_SECONDS = 12.0
PREVIEW_SECONDS = 36.0
CREW_CROP_BOX = (96, 696, 1056, 1080)
EDGE_FEATHER = 18
RAW_QA_FRAMES = [0, 36, 72, 108, 143]
LOOP_QA_FRAMES = [0, 72, 144, 216, 287]
SEAM_QA_FRAMES = [252, 264, 276, 284, 287, 0, 6, 12]
PREVIEW_SEAM_QA_FRAMES = [276, 287, 288, 300, 564, 575, 576, 588]


@dataclass(frozen=True)
class Candidate:
    id: str
    label: str
    seed: int
    cfg_scale: float
    stg_scale: float
    prompt_variant_id: str
    positive_motion_line: str


CANDIDATES = [
    Candidate(
        id="variant_a",
        label="A",
        seed=314159,
        cfg_scale=1.2,
        stg_scale=0.25,
        prompt_variant_id="almost_still_tiny_posture_settling_a",
        positive_motion_line="almost still; only tiny posture settling",
    ),
    Candidate(
        id="variant_b",
        label="B",
        seed=271828,
        cfg_scale=1.5,
        stg_scale=0.40,
        prompt_variant_id="subtle_detectable_independent_posture_settling_b",
        positive_motion_line="subtle detectable independent posture settling",
    ),
    Candidate(
        id="variant_c",
        label="C",
        seed=161803,
        cfg_scale=1.8,
        stg_scale=0.55,
        prompt_variant_id="upper_subtle_no_visible_action_c",
        positive_motion_line="upper subtle motion, still no visible action",
    ),
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_size(path: Path) -> int:
    return path.stat().st_size


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256(path), "bytes": bytes_size(path)}


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    if log_path:
        ensure_dir(log_path.parent)
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if log_path:
        log_path.write_text(
            "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
            encoding="utf-8",
        )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"command failed: {' '.join(command)}"
        raise RuntimeError(detail)
    return completed


def ffprobe(path: Path) -> dict[str, Any]:
    completed = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    return json.loads(completed.stdout)


def video_summary(path: Path) -> dict[str, Any]:
    data = ffprobe(path)
    streams = data.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    return {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": bytes_size(path),
        "duration_seconds": float(data.get("format", {}).get("duration") or 0),
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "codec_name": video_stream.get("codec_name"),
        "pix_fmt": video_stream.get("pix_fmt"),
        "avg_frame_rate": video_stream.get("avg_frame_rate"),
        "nb_frames": video_stream.get("nb_frames"),
        "has_audio": bool(audio_streams),
        "ffprobe": data,
    }


def safe_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for item in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(item).exists():
            return ImageFont.truetype(item, size)
    return ImageFont.load_default()


def build_crop_asset() -> Path:
    output = PACKET_ROOT / "assets" / "source_crop" / "variant_c_crew_zone_x96_y696_w960_h384.png"
    if output.exists():
        return output
    ensure_dir(output.parent)
    image = Image.open(SOURCE_ART_PATH).convert("RGB")
    crop = image.crop(CREW_CROP_BOX)
    crop.save(output)
    return output


def build_prompt(candidate: Candidate) -> str:
    return (
        "Photorealistic image-to-video for a Challenger living-cover crew crop. "
        "Use the provided crop as the exact visual source. The frame contains seven astronauts in blue flight suits, "
        "seen from behind, standing still on the launch pad and looking toward the shuttle. "
        f"Motion level: {candidate.positive_motion_line}. "
        "The seven astronauts stay planted, backs to viewer, arms down, feet fixed, looking toward the shuttle, with "
        "only tiny independent posture settling. Keep the image nearly static. Keep all movement local to the people. "
        "Keep the pad surface, rail, lighting, shadows, clothing identity, and crop composition stable. "
        "No walking. No stepping. No arm raising. No waving. No synchronized swaying. No turning toward camera. "
        "No faces. No readable text. No readable logos. No name patches. No lighting changes. No smoke. No fire. "
        "No shimmer. No atmosphere effects. No camera movement. No pad movement. No extra people. No missing people. "
        "No duplicated people. No launch event. No new objects. No scene effects."
    )


def ltx_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    env.setdefault("HF_HUB_CACHE", str(Path.home() / ".cache" / "huggingface" / "hub"))
    return env


def strip_audio_and_normalize(input_path: Path, output_path: Path, *, width: int, height: int, frames: int | None = None) -> None:
    ensure_dir(output_path.parent)
    filters = [f"fps={FPS}", f"scale={width}:{height}:flags=lanczos"]
    if frames is not None:
        filters.append(f"trim=end_frame={frames}")
        filters.append("setpts=PTS-STARTPTS")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            ",".join(filters),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_path.stem}.normalize.ffmpeg.log",
    )


def extract_all_frames(clip_path: Path, output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    ensure_dir(output_dir)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(clip_path),
            "-vf",
            f"fps={FPS}",
            "-start_number",
            "0",
            str(output_dir / "frame_%04d.png"),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_dir.parent.name}_{output_dir.name}_extract.ffmpeg.log",
    )
    return sorted(output_dir.glob("frame_*.png"))


def encode_frames(input_dir: Path, output_path: Path, *, width: int, height: int) -> None:
    ensure_dir(output_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(input_dir / "frame_%04d.png"),
            "-vf",
            f"scale={width}:{height}:flags=lanczos",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_path.stem}.encode.ffmpeg.log",
    )


def make_pingpong_frames(raw_frame_paths: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    ensure_dir(output_dir)
    usable = raw_frame_paths[:EXPECTED_RAW_FRAMES]
    if len(usable) != EXPECTED_RAW_FRAMES:
        raise RuntimeError(f"Expected {EXPECTED_RAW_FRAMES} raw frames, got {len(usable)}")
    sequence = usable + list(reversed(usable))
    output_paths: list[Path] = []
    for index, frame_path in enumerate(sequence):
        output = output_dir / f"frame_{index:04d}.png"
        shutil.copyfile(frame_path, output)
        output_paths.append(output)
    return output_paths


def make_composite_frames(loop_crop_paths: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    ensure_dir(output_dir)
    base = Image.open(SOURCE_ART_PATH).convert("RGB")
    x1, y1, x2, y2 = CREW_CROP_BOX
    mask = Image.new("L", (WIDTH, HEIGHT), 255)
    edge = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(edge)
    inset = EDGE_FEATHER
    draw.rectangle((inset, inset, WIDTH - inset, HEIGHT - inset), fill=255)
    feathered = edge.filter(ImageFilter.GaussianBlur(radius=EDGE_FEATHER / 2))
    mask = Image.composite(mask, feathered, feathered)
    output_paths: list[Path] = []
    for index, frame_path in enumerate(loop_crop_paths):
        frame = base.copy()
        crop = Image.open(frame_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        frame.paste(crop, (x1, y1), mask)
        output = output_dir / f"frame_{index:04d}.png"
        frame.save(output)
        output_paths.append(output)
    return output_paths


def make_three_loop_preview(loop_path: Path, output_path: Path, *, width: int, height: int) -> None:
    ensure_dir(output_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "2",
            "-i",
            str(loop_path),
            "-t",
            str(PREVIEW_SECONDS),
            "-vf",
            f"fps={FPS},scale={width}:{height}:flags=lanczos",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_path.stem}.ffmpeg.log",
    )


def extract_frame_from_sequence(sequence: list[Path], frame_index: int, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    shutil.copyfile(sequence[frame_index], output_path)


def extract_frame(clip_path: Path, frame_index: int, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(clip_path),
            "-vf",
            f"select=eq(n\\,{frame_index})",
            "-frames:v",
            "1",
            str(output_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_path.stem}.ffmpeg.log",
    )


def make_contact_sheet(
    *,
    rows: list[tuple[str, list[Path]]],
    output_path: Path,
    title: str,
    thumb_w: int,
    thumb_h: int,
) -> None:
    ensure_dir(output_path.parent)
    columns = max(len(paths) for _, paths in rows)
    gutter = 10
    top_h = 54
    label_h = 38
    sheet_w = gutter + columns * (thumb_w + gutter)
    sheet_h = top_h + len(rows) * (label_h + thumb_h + gutter) + gutter
    canvas = Image.new("RGB", (sheet_w, sheet_h), (8, 14, 25))
    draw = ImageDraw.Draw(canvas)
    draw.text((gutter, 14), title, fill=(247, 235, 214), font=safe_font(23))
    for row_index, (label, frame_paths) in enumerate(rows):
        row_y = top_h + row_index * (label_h + thumb_h + gutter)
        draw.text((gutter, row_y + 7), label, fill=(247, 235, 214), font=safe_font(15))
        for col, frame_path in enumerate(frame_paths):
            image = Image.open(frame_path).convert("RGB")
            image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb_w, thumb_h), (4, 10, 19))
            tile.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
            x = gutter + col * (thumb_w + gutter)
            y = row_y + label_h
            canvas.paste(tile, (x, y))
    canvas.save(output_path, quality=92)


def update_rejected_loop_successor() -> None:
    manifest = read_json(REJECTED_LOOP_MANIFEST)
    manifest["ltx_prompt_config_micro_motion_successor"] = {
        "packet_path": str(PACKET_ROOT),
        "manifest_path": str(PACKET_ROOT / "motion_scout_manifest.json"),
        "review_packet_path": str(PACKET_ROOT / "review" / "motion_scout_review_packet.md"),
        "created_utc": CREATED_UTC,
        "human_disposition": "defer",
        "note": "Rejected loop packet remains rejected; this successor is a fresh LTX prompt/config scout, not a revived rejected candidate.",
    }
    for flag in [
        "may_select_loop_candidate_after_human_keep",
        "may_create_full_runtime_html_proof",
        "may_create_full_runtime_mp4_render",
        "may_advance_to_final_assembly",
        "may_advance_to_shorts_work",
        "may_advance_to_publish_readiness",
        "may_youtube_action",
    ]:
        manifest[flag] = False
    manifest["next_review_question"] = "Rejected packet remains closed. Review the new LTX prompt/config micro-motion scout separately."
    write_json(REJECTED_LOOP_MANIFEST, manifest)

    readme_path = REJECTED_LOOP_ROOT / "README.md"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
        if "## LTX Prompt/Config Successor" not in text:
            text += (
                "\n## LTX Prompt/Config Successor\n\n"
                "This rejected packet remains rejected. The successor is a fresh Apple LTX prompt/config scout, not a revival of any rejected candidate.\n\n"
                f"Successor packet: `{PACKET_ROOT}`\n"
            )
            readme_path.write_text(text, encoding="utf-8")
    review_path = REJECTED_LOOP_ROOT / "review" / "motion_scout_review_packet.md"
    if review_path.exists():
        text = review_path.read_text(encoding="utf-8")
        if "## LTX Prompt/Config Successor" not in text:
            text += (
                "\n## LTX Prompt/Config Successor\n\n"
                "This rejected packet remains rejected. The successor is a fresh Apple LTX prompt/config scout, not a revival of any rejected candidate.\n\n"
                f"Successor packet: `{PACKET_ROOT}`\n"
            )
            review_path.write_text(text, encoding="utf-8")


def render_candidate(candidate: Candidate, crop_path: Path) -> dict[str, Any]:
    prompt_text = build_prompt(candidate)
    prompt_path = PACKET_ROOT / "prompts" / f"{candidate.id}_prompt.txt"
    write_text(prompt_path, prompt_text + "\n")

    ltx_output = PACKET_ROOT / "work" / "ltx_raw_with_possible_audio" / f"{candidate.id}_ltx_seed{candidate.seed}_raw_with_possible_audio.mp4"
    raw_crop_path = PACKET_ROOT / "clips" / "raw_crop" / f"{candidate.id}_ltx_seed{candidate.seed}_raw_crop.mp4"
    if not ltx_output.exists():
        command = [
            str(LTX_BIN),
            "generate",
            "--prompt",
            prompt_text,
            "--output",
            str(ltx_output),
            "--model",
            MODEL_REPO,
            "--gemma",
            TEXT_ENCODER_REPO,
            "--seed",
            str(candidate.seed),
            "--height",
            str(HEIGHT),
            "--width",
            str(WIDTH),
            "--frames",
            str(FRAMES),
            "--image",
            str(crop_path),
            "--steps",
            str(STEPS),
            "--cfg-scale",
            str(candidate.cfg_scale),
            "--stg-scale",
            str(candidate.stg_scale),
        ]
        run(command, cwd=LTX_RUNTIME_ROOT, env=ltx_env(), log_path=PACKET_ROOT / "logs" / f"{candidate.id}_ltx23_generate.log")
    strip_audio_and_normalize(ltx_output, raw_crop_path, width=WIDTH, height=HEIGHT, frames=EXPECTED_RAW_FRAMES)
    ltx_output.unlink(missing_ok=True)

    raw_frames = extract_all_frames(raw_crop_path, PACKET_ROOT / "work" / "raw_crop_frames" / candidate.id)
    loop_crop_frames = make_pingpong_frames(raw_frames, PACKET_ROOT / "work" / "loop_crop_frames" / candidate.id)
    loop_full_frames = make_composite_frames(loop_crop_frames, PACKET_ROOT / "work" / "loop_full_frame_frames" / candidate.id)

    loop_crop_path = PACKET_ROOT / "clips" / "loop_crop" / f"{candidate.id}_ltx_prompt_config_crop_loop_12s.mp4"
    loop_full_path = PACKET_ROOT / "clips" / "loop_composited_full_frame" / f"{candidate.id}_ltx_prompt_config_full_frame_loop_12s.mp4"
    preview_full_path = PACKET_ROOT / "clips" / "loop_preview_3x" / f"{candidate.id}_ltx_prompt_config_full_frame_3x_preview.mp4"
    encode_frames(PACKET_ROOT / "work" / "loop_crop_frames" / candidate.id, loop_crop_path, width=WIDTH, height=HEIGHT)
    encode_frames(PACKET_ROOT / "work" / "loop_full_frame_frames" / candidate.id, loop_full_path, width=FULL_WIDTH, height=FULL_HEIGHT)
    make_three_loop_preview(loop_full_path, preview_full_path, width=FULL_WIDTH, height=FULL_HEIGHT)

    qa: dict[str, list[Path]] = {
        "raw_crop": [],
        "loop_full_frame": [],
        "crew_crop": [],
        "loop_seam": [],
        "preview_3loop_seam": [],
    }
    for frame_index in RAW_QA_FRAMES:
        output = PACKET_ROOT / "qa" / "frames" / "raw_crop" / candidate.id / f"{candidate.id}_raw_crop_{frame_index:03d}.png"
        extract_frame(raw_crop_path, frame_index, output)
        qa["raw_crop"].append(output)
    for frame_index in LOOP_QA_FRAMES:
        output = PACKET_ROOT / "qa" / "frames" / "loop_full_frame" / candidate.id / f"{candidate.id}_loop_full_{frame_index:03d}.png"
        extract_frame_from_sequence(loop_full_frames, frame_index, output)
        qa["loop_full_frame"].append(output)
        crop_output = PACKET_ROOT / "qa" / "frames" / "crew_crop" / candidate.id / f"{candidate.id}_crew_crop_{frame_index:03d}.png"
        ensure_dir(crop_output.parent)
        Image.open(output).convert("RGB").crop(CREW_CROP_BOX).save(crop_output)
        qa["crew_crop"].append(crop_output)
    for index, frame_index in enumerate(SEAM_QA_FRAMES):
        output = PACKET_ROOT / "qa" / "frames" / "loop_seam" / candidate.id / f"{candidate.id}_seam_{index:02d}_frame_{frame_index:03d}.png"
        crop_output = PACKET_ROOT / "qa" / "frames" / "loop_seam_crop" / candidate.id / f"{candidate.id}_seam_crop_{index:02d}_frame_{frame_index:03d}.png"
        extract_frame_from_sequence(loop_full_frames, frame_index, output)
        ensure_dir(crop_output.parent)
        Image.open(output).convert("RGB").crop(CREW_CROP_BOX).save(crop_output)
        qa["loop_seam"].append(crop_output)
    for frame_index in PREVIEW_SEAM_QA_FRAMES:
        output = PACKET_ROOT / "qa" / "frames" / "preview_3loop_seam" / candidate.id / f"{candidate.id}_preview_{frame_index:03d}.png"
        crop_output = PACKET_ROOT / "qa" / "frames" / "preview_3loop_seam_crop" / candidate.id / f"{candidate.id}_preview_crop_{frame_index:03d}.png"
        extract_frame(preview_full_path, frame_index, output)
        ensure_dir(crop_output.parent)
        Image.open(output).convert("RGB").crop(CREW_CROP_BOX).save(crop_output)
        qa["preview_3loop_seam"].append(crop_output)

    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "seed": candidate.seed,
        "prompt_variant_id": candidate.prompt_variant_id,
        "cfg_scale": candidate.cfg_scale,
        "stg_scale": candidate.stg_scale,
        "steps": STEPS,
        "frames_requested": FRAMES,
        "prompt_text": prompt_text,
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256(prompt_path),
        "source_crop_path": str(crop_path),
        "source_crop_sha256": sha256(crop_path),
        "ltx_invocation": {
            "runtime": str(LTX_BIN),
            "model": MODEL_REPO,
            "gemma": TEXT_ENCODER_REPO,
            "width": WIDTH,
            "height": HEIGHT,
            "frames": FRAMES,
            "steps": STEPS,
            "cfg_scale": candidate.cfg_scale,
            "stg_scale": candidate.stg_scale,
            "enhance_prompt": False,
            "pipeline": "one_stage",
        },
        "raw_crop_clip": video_summary(raw_crop_path),
        "loop_crop_clip": video_summary(loop_crop_path),
        "loop_composited_full_frame_clip": video_summary(loop_full_path),
        "preview_3loop_clip": video_summary(preview_full_path),
        "qa_frames": {key: [artifact(path) for path in paths] for key, paths in qa.items()},
        "disposition": "defer",
        "selected_for_full_runtime_html_proof": False,
        "selected_for_full_runtime_html_proof_status": "pending_human_review",
    }
    write_json(PACKET_ROOT / "candidates" / f"{candidate.id}.json", payload)
    return payload


def make_contact_sheets(candidate_payloads: list[dict[str, Any]]) -> dict[str, Path]:
    rows: dict[str, list[tuple[str, list[Path]]]] = {
        "raw_crop": [],
        "loop_full_frame": [],
        "crew_crop": [],
        "loop_seam": [],
        "preview_3loop_seam": [],
    }
    for item in candidate_payloads:
        label = f"{item['label']} cfg {item['cfg_scale']} stg {item['stg_scale']} - {item['prompt_variant_id']}"
        for key in rows:
            rows[key].append((label, [Path(frame["path"]) for frame in item["qa_frames"][key]]))

    contact_dir = PACKET_ROOT / "qa" / "contact_sheets"
    outputs = {
        "raw_crop": contact_dir / "ltx23_prompt_config_raw_crop_contact_sheet.jpg",
        "loop_full_frame": contact_dir / "ltx23_prompt_config_composited_full_frame_contact_sheet.jpg",
        "crew_crop": contact_dir / "ltx23_prompt_config_crew_crop_contact_sheet.jpg",
        "loop_seam": contact_dir / "ltx23_prompt_config_loop_seam_contact_sheet.jpg",
        "preview_3loop_seam": contact_dir / "ltx23_prompt_config_3loop_seam_contact_sheet.jpg",
    }
    make_contact_sheet(rows=rows["raw_crop"], output_path=outputs["raw_crop"], title="LTX 2.3 Prompt/Config Scout - Raw Crew Crop", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["loop_full_frame"], output_path=outputs["loop_full_frame"], title="LTX 2.3 Prompt/Config Scout - Composited Full Frame", thumb_w=256, thumb_h=144)
    make_contact_sheet(rows=rows["crew_crop"], output_path=outputs["crew_crop"], title="LTX 2.3 Prompt/Config Scout - Crew Crop", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["loop_seam"], output_path=outputs["loop_seam"], title="LTX 2.3 Prompt/Config Scout - End/Start Seam Crop", thumb_w=205, thumb_h=82)
    make_contact_sheet(rows=rows["preview_3loop_seam"], output_path=outputs["preview_3loop_seam"], title="LTX 2.3 Prompt/Config Scout - 3x Preview Seam Crop", thumb_w=205, thumb_h=82)
    return outputs


def build_manifest(candidate_payloads: list[dict[str, Any]], crop_path: Path, contact_sheets: dict[str, Path]) -> dict[str, Any]:
    no_forbidden_sidecars = not any(
        path.suffix.lower() in {".wav", ".mp3", ".srt", ".vtt", ".html", ".mov"}
        for path in PACKET_ROOT.rglob("*")
        if path.is_file()
    )
    all_no_audio = all(
        not item["raw_crop_clip"]["has_audio"]
        and not item["loop_crop_clip"]["has_audio"]
        and not item["loop_composited_full_frame_clip"]["has_audio"]
        and not item["preview_3loop_clip"]["has_audio"]
        for item in candidate_payloads
    )
    loop_duration_ok = all(
        11.9 <= float(item["loop_composited_full_frame_clip"]["duration_seconds"]) <= 12.1
        for item in candidate_payloads
    )
    preview_duration_ok = all(
        35.8 <= float(item["preview_3loop_clip"]["duration_seconds"]) <= 36.2
        for item in candidate_payloads
    )
    return {
        "packet_id": PACKET_ID,
        "gate": "rough_assembly_ltx_prompt_config_micro_motion_scout_gate",
        "status": "review_ready_pending_human_ltx_prompt_config_micro_motion_keep",
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
        "created_from_disposition": "fresh_scout_after_rejected_smooth_loop_ltx_packet",
        "rejected_loop_packet_path": str(REJECTED_LOOP_ROOT),
        "rejected_loop_manifest_path": str(REJECTED_LOOP_MANIFEST),
        "review_only": True,
        "ltx_prompt_config_scout_only": True,
        "full_runtime_html_proof_created": False,
        "full_runtime_mp4_created": False,
        "final_assembly_created": False,
        "profileId": "cascade-ink-lit-photoreal-v1",
        "source_visual": {
            "carrier": "kept_variant_c_full_frame_source_art",
            "source_art_path": str(SOURCE_ART_PATH),
            "source_art_sha256": sha256(SOURCE_ART_PATH),
            "expected_source_art_sha256": EXPECTED_SOURCE_SHA256,
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "source_art_dimensions": {"width": FULL_WIDTH, "height": FULL_HEIGHT, "aspect_ratio": "16:9"},
            "crew_crop_box": {"x": CREW_CROP_BOX[0], "y": CREW_CROP_BOX[1], "width": WIDTH, "height": HEIGHT},
            "crew_crop_path": str(crop_path),
            "crew_crop_sha256": sha256(crop_path),
        },
        "ltx_runtime": {
            "runtime": str(LTX_BIN),
            "runtime_root": str(LTX_RUNTIME_ROOT),
            "model": MODEL_REPO,
            "gemma": TEXT_ENCODER_REPO,
            "pipeline": "one_stage",
            "enhance_prompt": False,
            "width": WIDTH,
            "height": HEIGHT,
            "frames": FRAMES,
            "steps": STEPS,
            "runtime_path_read": "pass" if LTX_BIN.exists() else "reject_missing_runtime",
        },
        "loop_contract": {
            "raw_half_cycle_seconds": 6.0,
            "raw_half_cycle_frames_after_normalization": EXPECTED_RAW_FRAMES,
            "loop_method": "forward_reverse_ping_pong",
            "loop_seconds": LOOP_SECONDS,
            "loop_frames": 288,
            "preview_seconds": PREVIEW_SECONDS,
            "preview_frames": 864,
            "motion_target": "subtle_non_synchronized_posture_settling_only_no_noise_or_effects",
            "composite_policy": "ltx_generated_crop_composited_into_static_kept_variant_c_full_frame_for_context",
        },
        "candidates": candidate_payloads,
        "contact_sheets": {key: artifact(path) for key, path in contact_sheets.items()},
        "motion_scout_reads": {
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "ltx_runtime_read": "pass" if LTX_BIN.exists() else "reject_missing_runtime",
            "candidate_count_read": "pass_three_candidates" if len(candidate_payloads) == 3 else "reject_missing_candidates",
            "raw_crop_audio_read": "pass_no_audio" if all_no_audio else "reject_audio_present",
            "loop_duration_read": "pass_12s" if loop_duration_ok else "tighten_duration_not_12s",
            "preview_3loop_duration_read": "pass_36s" if preview_duration_ok else "tighten_duration_not_36s",
            "contact_sheet_read": "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet",
            "forbidden_media_copy_read": "pass_no_audio_caption_transcript_html_mov_sidecars" if no_forbidden_sidecars else "reject_forbidden_sidecar_found",
            "full_runtime_html_proof_read": "pass_not_created",
            "full_runtime_mp4_read": "pass_not_created",
            "final_assembly_read": "pass_not_created",
            "ltx_prompt_config_read": "defer_pending_human_review",
            "crew_loop_read": "defer_pending_human_review",
            "loop_seam_read": "defer_pending_human_review",
            "motion_subtlety_read": "defer_pending_human_review",
            "motion_detectability_read": "defer_pending_human_review",
            "non_synchronized_motion_read": "defer_pending_human_review",
            "no_noise_effects_read": "defer_pending_human_review",
            "crew_count_read": "defer_pending_human_review",
            "background_stability_read": "defer_pending_human_review",
            "uncanny_motion_read": "defer_pending_human_review",
            "long_runtime_carrier_read": "defer_pending_human_review",
        },
        "may_select_ltx_prompt_config_candidate_after_human_keep": False,
        "may_create_full_runtime_html_proof": False,
        "may_create_full_runtime_mp4_render": False,
        "may_advance_to_final_assembly": False,
        "may_advance_to_shorts_work": False,
        "may_advance_to_publish_readiness": False,
        "may_youtube_action": False,
        "next_review_question": "Review A/B/C and reply with exactly one response: keep A, keep B, keep C, tighten, or reject.",
    }


def build_readme(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- {item['label']}: seed `{item['seed']}`, cfg `{item['cfg_scale']}`, stg `{item['stg_scale']}`, `{item['prompt_variant_id']}`"
        for item in manifest["candidates"]
    )
    return f"""# Challenger Living Cover LTX 2.3 Prompt/Config Micro-Motion Scout

Packet: `{PACKET_ID}`
Status: `{manifest['status']}`
Human disposition: `defer`

This packet is a fresh Apple LTX 2.3 prompt/config scout after the rejected smooth-loop scout. It keeps LTX as the motion generator, isolates generation to the crew crop, removes atmosphere/effects language, and builds a loop with a forward/reverse ping-pong.

## Candidates

{rows}

## Review Surfaces

- Raw crop contact sheet: `{manifest['contact_sheets']['raw_crop']['path']}`
- Composited full-frame contact sheet: `{manifest['contact_sheets']['loop_full_frame']['path']}`
- Crew crop contact sheet: `{manifest['contact_sheets']['crew_crop']['path']}`
- Loop seam contact sheet: `{manifest['contact_sheets']['loop_seam']['path']}`
- 3-loop seam contact sheet: `{manifest['contact_sheets']['preview_3loop_seam']['path']}`
- Composited loops: `clips/loop_composited_full_frame/`
- 3-loop previews: `clips/loop_preview_3x/`

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.
"""


def build_review(manifest: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        "| {label} | `{seed}` | `{cfg}` | `{stg}` | `{loop}` | `{preview}` |".format(
            label=item["label"],
            seed=item["seed"],
            cfg=item["cfg_scale"],
            stg=item["stg_scale"],
            loop=item["loop_composited_full_frame_clip"]["path"],
            preview=item["preview_3loop_clip"]["path"],
        )
        for item in manifest["candidates"]
    )
    read_rows = "\n".join(f"| `{key}` | `{value}` |" for key, value in manifest["motion_scout_reads"].items())
    return f"""# Challenger Living Cover LTX 2.3 Prompt/Config Micro-Motion Scout Review

Packet: `{PACKET_ID}`
Gate: `rough_assembly_ltx_prompt_config_micro_motion_scout_gate`
Human disposition: `defer`

## What Changed

- The rejected smooth-loop packet remains rejected.
- This is a fresh LTX prompt/config scout, not in-place deformation or sprite animation.
- LTX runs only on the crew crop; the review full-frame clips composite that generated crop into static kept Variant C context.
- The loop is built from a 6s generated half-cycle plus reverse playback.

## Candidates

| Candidate | Seed | CFG | STG | 12s Composited Loop | 36s 3-Loop Preview |
|---|---:|---:|---:|---|---|
{candidate_rows}

## Contact Sheets

- Raw crop: `{manifest['contact_sheets']['raw_crop']['path']}`
- Composited full frame: `{manifest['contact_sheets']['loop_full_frame']['path']}`
- Crew crop: `{manifest['contact_sheets']['crew_crop']['path']}`
- Loop seam: `{manifest['contact_sheets']['loop_seam']['path']}`
- 3-loop seam: `{manifest['contact_sheets']['preview_3loop_seam']['path']}`

## Reads

| Read | Result |
|---|---:|
{read_rows}

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected LTX prompt/config carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.
"""


def main() -> None:
    for subdir in [
        "assets/source_crop",
        "prompts",
        "candidates",
        "clips/raw_crop",
        "clips/loop_crop",
        "clips/loop_composited_full_frame",
        "clips/loop_preview_3x",
        "qa/frames",
        "qa/contact_sheets",
        "logs",
        "review",
        "scripts",
        "work",
        "work/ltx_raw_with_possible_audio",
    ]:
        ensure_dir(PACKET_ROOT / subdir)
    if not SOURCE_ART_PATH.exists():
        raise FileNotFoundError(SOURCE_ART_PATH)
    if sha256(SOURCE_ART_PATH) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Kept Variant C source-art hash mismatch")
    if not LTX_BIN.exists():
        raise FileNotFoundError(LTX_BIN)

    update_rejected_loop_successor()
    crop_path = build_crop_asset()
    candidate_payloads = [render_candidate(candidate, crop_path) for candidate in CANDIDATES]
    contact_sheets = make_contact_sheets(candidate_payloads)

    manifest = build_manifest(candidate_payloads, crop_path, contact_sheets)
    manifest_path = PACKET_ROOT / "motion_scout_manifest.json"
    readme_path = PACKET_ROOT / "README.md"
    review_path = PACKET_ROOT / "review" / "motion_scout_review_packet.md"
    write_json(manifest_path, manifest)
    write_text(readme_path, build_readme(manifest))
    write_text(review_path, build_review(manifest))
    manifest["artifacts"] = {
        "manifest": artifact(manifest_path),
        "readme": artifact(readme_path),
        "review_packet": artifact(review_path),
        "builder_script": artifact(Path(__file__)),
        **{key: artifact(path) for key, path in contact_sheets.items()},
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"packet_root": str(PACKET_ROOT), "manifest_path": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
