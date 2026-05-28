#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont


CREATED_UTC = "2026-05-06T17:35:17Z"
PACKET_ID = "living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z"
PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_ltx23_variable_duration_terminal_walk_scout_20260506T173517Z"
)
CURRENT_TERMINAL_SCOUT_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z"
)
CURRENT_TERMINAL_SCOUT_MANIFEST = CURRENT_TERMINAL_SCOUT_ROOT / "terminal_walk_manifest.json"
BASE_BUILDER_SCRIPT = CURRENT_TERMINAL_SCOUT_ROOT / "scripts/build_terminal_walk_scout.py"

SOURCE_ART_PATH = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png"
)
EXPECTED_SOURCE_SHA256 = "52f94150037d5aa40633d34b29c137c59c5868e987bc5f8b7f80903f6bc2ac8a"

PREVIOUS_NO_CREW_PLATE = CURRENT_TERMINAL_SCOUT_ROOT / "assets/background_plate/variant_c_aligned_no_crew_plate.png"
PREVIOUS_NO_CREW_MASK = CURRENT_TERMINAL_SCOUT_ROOT / "assets/background_plate/variant_c_no_crew_plate_mask.png"
PREVIOUS_CHROMA_SOURCE = CURRENT_TERMINAL_SCOUT_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_green_screen_source.png"
PREVIOUS_ALPHA_REFERENCE = CURRENT_TERMINAL_SCOUT_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_alpha_reference.png"
PREVIOUS_SOURCE_MASK = CURRENT_TERMINAL_SCOUT_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_source_mask.png"

LTX_BIN = Path("/Users/mike/AI/ltx-2-mlx/.venv/bin/ltx-2-mlx")
LTX_RUNTIME_ROOT = Path("/Users/mike/AI/ltx-2-mlx")
MODEL_REPO = "dgrauet/ltx-2.3-mlx-q8"
TEXT_ENCODER_REPO = "mlx-community/gemma-3-12b-it-4bit"

FPS = 24
FULL_WIDTH = 1920
FULL_HEIGHT = 1080
WIDTH = 960
HEIGHT = 384
CREW_CROP_BOX = (96, 696, 1056, 1080)
REVIEW_STILL_SECONDS = 2.0
APPROVED_AUDIO_DURATION_SECONDS = 1289.131247
APPROVED_AUDIO_DURATION_DISPLAY = "00:21:29.131"


spec = importlib.util.spec_from_file_location("terminal_base_builder", BASE_BUILDER_SCRIPT)
base_builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = base_builder
spec.loader.exec_module(base_builder)


@dataclass(frozen=True)
class PipelineLane:
    id: str
    label: str
    seed_offset: int
    cfg_scale: float
    stg_scale: float
    one_stage_steps: int | None = None
    stage1_steps: int | None = None
    stage2_steps: int | None = None
    flags: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class DurationCell:
    seconds: int
    frames: int


PIPELINE_LANES = [
    PipelineLane(
        id="one_stage_q8",
        label="One-stage q8",
        seed_offset=0,
        cfg_scale=1.35,
        stg_scale=0.30,
        one_stage_steps=8,
        note="Baseline one-stage q8 I2V, true duration, no stretching.",
    ),
    PipelineLane(
        id="two_stage_distilled_lora",
        label="Two-stage distilled-LoRA",
        seed_offset=1000,
        cfg_scale=2.4,
        stg_scale=0.70,
        stage1_steps=15,
        stage2_steps=3,
        flags=("--two-stage",),
        note="Two-stage q8 path with distilled-LoRA refinement; true duration, no stretching.",
    ),
]

DURATION_CELLS = [
    DurationCell(seconds=4, frames=97),
    DurationCell(seconds=6, frames=145),
    DurationCell(seconds=8, frames=193),
    DurationCell(seconds=12, frames=289),
]

QA_RATIOS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


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
    return json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]).stdout)


def video_summary(path: Path) -> dict[str, Any]:
    data = ffprobe(path)
    streams = data.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = [item for item in streams if item.get("codec_type") == "audio"]
    return {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "duration_seconds": float(data.get("format", {}).get("duration") or 0),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "codec_name": video.get("codec_name"),
        "pix_fmt": video.get("pix_fmt"),
        "avg_frame_rate": video.get("avg_frame_rate"),
        "nb_frames": video.get("nb_frames"),
        "has_audio": bool(audio),
        "ffprobe": data,
    }


def ltx_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    env.setdefault("HF_HUB_CACHE", str(Path.home() / ".cache" / "huggingface" / "hub"))
    return env


def safe_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for item in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(item).exists():
            return ImageFont.truetype(item, size)
    return ImageFont.load_default()


def frame_indices(total_frames: int) -> list[int]:
    return sorted({max(0, min(total_frames - 1, round((total_frames - 1) * ratio))) for ratio in QA_RATIOS})


def seconds_to_display(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    whole = millis // 1000
    ms = millis % 1000
    minutes = whole // 60
    sec = whole % 60
    return f"{minutes:02d}:{sec:02d}.{ms:03d}"


def update_current_terminal_scout() -> None:
    manifest = read_json(CURRENT_TERMINAL_SCOUT_MANIFEST)
    manifest["human_disposition"] = "tighten"
    manifest["status"] = "tighten_variable_duration_successor_required"
    manifest["tighten_record"] = {
        "recorded_utc": CREATED_UTC,
        "reviewer_note": (
            "Variant A was directionally best, but the crew squats/crouches before stepping and the stretched 12s walk is too slow to read as natural. "
            "The fixed 12s terminal-walk constraint is no longer binding; successor must test true-duration 4s, 6s, 8s, and 12s generations plus pipeline lanes."
        ),
        "best_prior_variant": "A_directional_only_not_keep",
        "required_successor": "ltx23_variable_duration_terminal_walk_scout",
    }
    reads = manifest.setdefault("terminal_walk_reads", {})
    reads["terminal_walk_read"] = "tighten_directional_only"
    reads["squat_crouch_read"] = "tighten_squat_before_step"
    reads["walk_speed_read"] = "tighten_too_slow_due_stretched_12s_prefix"
    reads["duration_fit_read"] = "tighten_fixed_12s_constraint_released"
    reads["natural_gait_read"] = "tighten_not_natural_enough"
    reads["variable_duration_successor_read"] = "pass_successor_packet_created"
    manifest["variable_duration_successor"] = {
        "packet_path": str(PACKET_ROOT),
        "manifest_path": str(PACKET_ROOT / "variable_duration_terminal_walk_manifest.json"),
        "review_packet_path": str(PACKET_ROOT / "review" / "variable_duration_terminal_walk_review_packet.md"),
        "created_utc": CREATED_UTC,
        "human_disposition": "defer",
    }
    manifest["terminal_walk_contract"]["presented_iteration_note"] = (
        manifest["terminal_walk_contract"].get("presented_iteration_note", "")
        + " Superseded by variable-duration true-generation scout; stretched 12s prefixes are not advancement sources."
    )
    for flag in [
        "may_select_terminal_walk_candidate_after_human_keep",
        "may_create_full_runtime_html_proof",
        "may_create_full_runtime_mp4_render",
        "may_advance_to_final_assembly",
        "may_advance_to_shorts_work",
        "may_advance_to_publish_readiness",
        "may_youtube_action",
    ]:
        manifest[flag] = False
    manifest["next_review_question"] = "Current 12s terminal-walk scout is tighten. Review the variable-duration successor packet."
    write_json(CURRENT_TERMINAL_SCOUT_MANIFEST, manifest)

    append = (
        "\n## Variable-Duration Terminal Walk Successor\n\n"
        "Human disposition: `tighten`.\n\n"
        "Reason: Variant A was directionally best, but the crew squats/crouches before stepping and the stretched 12s walk is too slow. "
        "The successor drops the fixed 12s requirement and tests true-duration 4s, 6s, 8s, and 12s generations across one-stage and two-stage LTX lanes.\n\n"
        f"Successor packet: `{PACKET_ROOT}`\n"
    )
    for md_path in [CURRENT_TERMINAL_SCOUT_ROOT / "README.md", CURRENT_TERMINAL_SCOUT_ROOT / "review" / "terminal_walk_review_packet.md"]:
        if md_path.exists():
            text = md_path.read_text(encoding="utf-8")
            if "## Variable-Duration Terminal Walk Successor" not in text:
                md_path.write_text(text + append, encoding="utf-8")


def copy_inputs() -> dict[str, Any]:
    assets = PACKET_ROOT / "assets"
    background_dir = assets / "background_plate"
    crew_dir = assets / "crew_chroma_source"
    ensure_dir(background_dir)
    ensure_dir(crew_dir)
    mapping = {
        "no_crew_plate": (PREVIOUS_NO_CREW_PLATE, background_dir / "variant_c_aligned_no_crew_plate.png"),
        "no_crew_mask": (PREVIOUS_NO_CREW_MASK, background_dir / "variant_c_no_crew_plate_mask.png"),
        "chroma_source": (PREVIOUS_CHROMA_SOURCE, crew_dir / "variant_c_seven_astronauts_green_screen_source.png"),
        "alpha_reference": (PREVIOUS_ALPHA_REFERENCE, crew_dir / "variant_c_seven_astronauts_alpha_reference.png"),
        "source_mask": (PREVIOUS_SOURCE_MASK, crew_dir / "variant_c_seven_astronauts_source_mask.png"),
    }
    copied: dict[str, Any] = {}
    for key, (src, dst) in mapping.items():
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copyfile(src, dst)
        copied[key] = artifact(dst)
    static_keyed, _ = base_builder.key_chroma_frame(Image.open(copied["chroma_source"]["path"]))
    base = Image.open(copied["no_crew_plate"]["path"]).convert("RGB").convert("RGBA")
    base.alpha_composite(static_keyed, dest=(CREW_CROP_BOX[0], CREW_CROP_BOX[1]))
    static_preview = assets / "static_prewalk_full_frame.png"
    base.convert("RGB").save(static_preview)
    copied["static_prewalk_full_frame"] = artifact(static_preview)
    return copied


def build_prompt(lane: PipelineLane, duration: DurationCell) -> str:
    return (
        "Image-to-video of a green-screen crew layer only. The input image shows exactly seven astronauts in blue flight suits, "
        "seen from behind on a pure flat chroma green background. Preserve exactly seven people. Preserve their back-view orientation. "
        f"Over {duration.seconds} seconds, they begin upright natural first steps away from camera toward an unseen shuttle pad. "
        "Use calm natural walking cadence, not slow motion. Start from the standing pose and step forward without dipping. "
        "The seven people should move with slight staggered timing; each person has an independent stride. "
        "Keep arms low with only small natural walking arm movement. Keep heads and torsos upright. "
        "Keep bodies facing away from camera. Keep feet and legs believable. Keep the background pure chroma green and blank. "
        "No camera movement. No time stretching. No squat. No crouch. No knee dip. No bobbing. No slow motion. "
        "No marching. No synchronized stride. No waving. No saluting. No pointing. No raised hands. No running. "
        "No jumping. No dancing. No turning around. No faces. No readable logos. No name patches. No text. "
        "No extra people. No missing people. No duplicated people. No smoke. No fire. No launch. No sparks. "
        "No atmosphere effects. No pad background. No floor detail. No props. "
        f"Pipeline intent: {lane.note}"
    )


def strip_audio_and_normalize(input_path: Path, output_path: Path, *, width: int, height: int, frames: int) -> None:
    ensure_dir(output_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vf",
            f"fps={FPS},scale={width}:{height}:flags=lanczos,trim=end_frame={frames},setpts=PTS-STARTPTS",
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


def copy_sequence_frame(sequence: list[Path], frame_index: int, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    shutil.copyfile(sequence[frame_index], output_path)


def make_transition_review_frames(static_full_frame: Path, walk_full_frames: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    ensure_dir(output_dir)
    static = Image.open(static_full_frame).convert("RGB")
    output: list[Path] = []
    still_frames = int(REVIEW_STILL_SECONDS * FPS)
    total = still_frames + len(walk_full_frames)
    for index in range(total):
        if index < still_frames:
            img = static
        else:
            img = Image.open(walk_full_frames[index - still_frames]).convert("RGB")
        path = output_dir / f"frame_{index:04d}.png"
        img.save(path)
        output.append(path)
    return output


def motion_delta_score(frame_paths: list[Path]) -> float:
    if len(frame_paths) < 2:
        return 0.0
    first = Image.open(frame_paths[0]).convert("L")
    scores: list[float] = []
    for path in frame_paths[1:]:
        current = Image.open(path).convert("L")
        arr = np.array(ImageChops.difference(first, current), dtype=np.float32)
        scores.append(float(arr.mean()))
    return round(max(scores), 4) if scores else 0.0


def upper_body_raise_probe(crew_crop_paths: list[Path]) -> dict[str, Any]:
    counts: list[int] = []
    for path in crew_crop_paths:
        img = Image.open(path).convert("RGB")
        arr = np.array(img)
        zone = arr[35:180, :, :]
        blue = (zone[:, :, 2] > zone[:, :, 1] + 14) & (zone[:, :, 2] > zone[:, :, 0] + 20) & (zone[:, :, 2] > 55)
        counts.append(int(blue.sum()))
    baseline = counts[0] if counts else 0
    max_delta = max([abs(value - baseline) for value in counts], default=0)
    return {
        "upper_body_blue_pixel_counts": counts,
        "max_delta_from_first": max_delta,
        "machine_flag": "review_possible_raise_or_gesture" if max_delta > 9000 else "no_large_upper_body_raise_detected",
    }


def crouch_probe(matte_paths: list[Path]) -> dict[str, Any]:
    tops: list[int] = []
    centers: list[float] = []
    for path in matte_paths:
        arr = np.array(Image.open(path).convert("L"))
        ys, _ = np.where(arr > 16)
        if len(ys) == 0:
            tops.append(HEIGHT)
            centers.append(float(HEIGHT))
            continue
        tops.append(int(ys.min()))
        centers.append(float(ys.mean()))
    top_drop = max(tops) - tops[0] if tops else 0
    center_drop = max(centers) - centers[0] if centers else 0.0
    return {
        "silhouette_top_y": tops,
        "silhouette_center_y": [round(value, 3) for value in centers],
        "max_top_drop_pixels": int(top_drop),
        "max_center_drop_pixels": round(center_drop, 3),
        "machine_flag": "review_possible_squat_or_crouch" if top_drop > 9 or center_drop > 8 else "no_large_crouch_detected",
    }


def terminal_start_for_duration(duration_seconds: float) -> dict[str, Any]:
    start = APPROVED_AUDIO_DURATION_SECONDS - duration_seconds
    return {
        "terminal_walk_duration_seconds": duration_seconds,
        "terminal_walk_start_seconds": round(start, 6),
        "terminal_walk_start_display": seconds_to_display(start),
        "approved_audio_duration_seconds": APPROVED_AUDIO_DURATION_SECONDS,
        "approved_audio_duration_display": APPROVED_AUDIO_DURATION_DISPLAY,
    }


def ltx_command(lane: PipelineLane, duration: DurationCell, prompt: str, output_path: Path, seed: int, chroma_source: Path) -> list[str]:
    command = [
        str(LTX_BIN),
        "generate",
        "--prompt",
        prompt,
        "--output",
        str(output_path),
        "--model",
        MODEL_REPO,
        "--gemma",
        TEXT_ENCODER_REPO,
        "--seed",
        str(seed),
        "--height",
        str(HEIGHT),
        "--width",
        str(WIDTH),
        "--frames",
        str(duration.frames),
        "--image",
        str(chroma_source),
        "--cfg-scale",
        str(lane.cfg_scale),
        "--stg-scale",
        str(lane.stg_scale),
    ]
    if lane.id == "one_stage_q8":
        command.extend(["--steps", str(lane.one_stage_steps)])
    else:
        command.extend(lane.flags)
        command.extend(["--stage1-steps", str(lane.stage1_steps), "--stage2-steps", str(lane.stage2_steps)])
    return command


def render_cell(lane: PipelineLane, duration: DurationCell, chroma_source: Path, no_crew_plate: Path, static_full_frame: Path, cell_index: int) -> dict[str, Any]:
    cell_id = f"{lane.id}_{duration.seconds}s"
    seed = 510000 + lane.seed_offset + duration.seconds * 17
    prompt = build_prompt(lane, duration)
    prompt_path = PACKET_ROOT / "prompts" / f"{cell_id}_prompt.txt"
    write_text(prompt_path, prompt + "\n")

    ltx_temp = PACKET_ROOT / "work" / "ltx_raw_with_possible_audio" / f"{cell_id}_seed{seed}_with_possible_audio.mp4"
    raw_chroma = PACKET_ROOT / "clips" / "raw_chroma_crew" / f"{cell_id}_seed{seed}_raw_chroma_{duration.seconds}s.mp4"
    command = ltx_command(lane, duration, prompt, ltx_temp, seed, chroma_source)
    ensure_dir(ltx_temp.parent)
    run(command, cwd=LTX_RUNTIME_ROOT, env=ltx_env(), log_path=PACKET_ROOT / "logs" / f"{cell_id}_ltx23_generate.log")
    strip_audio_and_normalize(ltx_temp, raw_chroma, width=WIDTH, height=HEIGHT, frames=duration.frames)
    ltx_temp.unlink(missing_ok=True)

    raw_frames = extract_all_frames(raw_chroma, PACKET_ROOT / "work" / "raw_chroma_frames" / cell_id)
    keyed_dirs = base_builder.key_and_composite_frames(
        raw_frames,
        no_crew_plate,
        PACKET_ROOT / "work" / "keyed_frames" / cell_id,
        PACKET_ROOT / "work" / "matte_frames" / cell_id,
        PACKET_ROOT / "work" / "full_frame_frames" / cell_id,
        PACKET_ROOT / "work" / "crew_crop_frames" / cell_id,
    )

    keyed_clip = PACKET_ROOT / "clips" / "keyed_alpha_preview" / f"{cell_id}_keyed_alpha_preview_{duration.seconds}s.mp4"
    composited_clip = PACKET_ROOT / "clips" / "composited_full_frame" / f"{cell_id}_composited_full_frame_{duration.seconds}s.mp4"
    transition_dir = PACKET_ROOT / "work" / "transition_review_frames" / cell_id
    transition_frames = make_transition_review_frames(static_full_frame, keyed_dirs["full"], transition_dir)
    transition_clip = PACKET_ROOT / "clips" / "transition_review" / f"{cell_id}_static_then_terminal_walk_review_{duration.seconds + 2}s.mp4"
    encode_frames(PACKET_ROOT / "work" / "keyed_frames" / cell_id, keyed_clip, width=WIDTH, height=HEIGHT)
    encode_frames(PACKET_ROOT / "work" / "full_frame_frames" / cell_id, composited_clip, width=FULL_WIDTH, height=FULL_HEIGHT)
    encode_frames(transition_dir, transition_clip, width=FULL_WIDTH, height=FULL_HEIGHT)

    qa_indices = frame_indices(len(raw_frames))
    transition_indices = [0, 24, 47, 48] + [48 + idx for idx in qa_indices]
    transition_indices = sorted({idx for idx in transition_indices if 0 <= idx < len(transition_frames)})
    qa: dict[str, list[Path]] = {
        "raw_chroma_crew": [],
        "matte": [],
        "composited_full_frame": [],
        "crew_crop": [],
        "still_to_walk_transition": [],
    }
    for frame_index in qa_indices:
        raw_out = PACKET_ROOT / "qa" / "frames" / "raw_chroma_crew" / cell_id / f"{cell_id}_raw_{frame_index:03d}.png"
        matte_out = PACKET_ROOT / "qa" / "frames" / "matte" / cell_id / f"{cell_id}_matte_{frame_index:03d}.png"
        full_out = PACKET_ROOT / "qa" / "frames" / "composited_full_frame" / cell_id / f"{cell_id}_full_{frame_index:03d}.png"
        crop_out = PACKET_ROOT / "qa" / "frames" / "crew_crop" / cell_id / f"{cell_id}_crew_crop_{frame_index:03d}.png"
        copy_sequence_frame(raw_frames, frame_index, raw_out)
        copy_sequence_frame(keyed_dirs["matte"], frame_index, matte_out)
        copy_sequence_frame(keyed_dirs["full"], frame_index, full_out)
        copy_sequence_frame(keyed_dirs["crew_crop"], frame_index, crop_out)
        qa["raw_chroma_crew"].append(raw_out)
        qa["matte"].append(matte_out)
        qa["composited_full_frame"].append(full_out)
        qa["crew_crop"].append(crop_out)
    for frame_index in transition_indices:
        transition_out = PACKET_ROOT / "qa" / "frames" / "still_to_walk_transition" / cell_id / f"{cell_id}_transition_{frame_index:03d}.png"
        copy_sequence_frame(transition_frames, frame_index, transition_out)
        qa["still_to_walk_transition"].append(transition_out)

    probes = {
        "crew_crop_motion_delta_score": motion_delta_score(qa["crew_crop"]),
        "upper_body_raise_probe": upper_body_raise_probe(qa["crew_crop"]),
        "squat_crouch_probe": crouch_probe(qa["matte"]),
        "note": "Machine probes are coarse screening only; human review is authoritative.",
    }
    payload = {
        "cell_id": cell_id,
        "matrix_index": cell_index,
        "pipeline_lane": lane.id,
        "pipeline_label": lane.label,
        "pipeline_note": lane.note,
        "duration_seconds": duration.seconds,
        "frames_requested": duration.frames,
        "frames_after_normalization": duration.frames,
        "fps": FPS,
        "seed": seed,
        "cfg_scale": lane.cfg_scale,
        "stg_scale": lane.stg_scale,
        "one_stage_steps": lane.one_stage_steps,
        "stage1_steps": lane.stage1_steps,
        "stage2_steps": lane.stage2_steps,
        "true_duration_no_time_stretch": True,
        "terminal_timing": terminal_start_for_duration(duration.seconds),
        "prompt_text": prompt,
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256(prompt_path),
        "ltx_invocation": {
            "runtime": str(LTX_BIN),
            "model": MODEL_REPO,
            "gemma": TEXT_ENCODER_REPO,
            "width": WIDTH,
            "height": HEIGHT,
            "frames": duration.frames,
            "enhance_prompt": False,
            "command": command,
            "pipeline": lane.id,
        },
        "raw_chroma_crew_clip": video_summary(raw_chroma),
        "keyed_alpha_preview_clip": video_summary(keyed_clip),
        "composited_full_frame_clip": video_summary(composited_clip),
        "transition_review_clip": video_summary(transition_clip),
        "qa_frames": {key: [artifact(path) for path in paths] for key, paths in qa.items()},
        "machine_motion_probe": probes,
        "diagnostic_disposition": "defer_pending_review_selection",
        "selected_for_presented_abc": False,
        "presented_label": None,
    }
    write_json(PACKET_ROOT / "diagnostics" / f"{cell_id}.json", payload)
    return payload


def objective_score(cell: dict[str, Any]) -> float:
    motion = float(cell["machine_motion_probe"]["crew_crop_motion_delta_score"])
    upper = cell["machine_motion_probe"]["upper_body_raise_probe"]["max_delta_from_first"]
    top_drop = cell["machine_motion_probe"]["squat_crouch_probe"]["max_top_drop_pixels"]
    center_drop = float(cell["machine_motion_probe"]["squat_crouch_probe"]["max_center_drop_pixels"])
    duration = float(cell["duration_seconds"])
    score = 100.0
    score += min(motion, 35.0) * 1.2
    score -= max(0.0, motion - 42.0) * 2.0
    score -= max(0.0, top_drop - 7.0) * 3.0
    score -= max(0.0, center_drop - 6.0) * 2.5
    score -= max(0.0, upper - 7500.0) / 650.0
    if duration in {4.0, 6.0, 8.0}:
        score += 6.0
    if cell["pipeline_lane"] == "two_stage_distilled_lora":
        score += 2.5
    return round(score, 4)


def select_presented_candidates(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(cells, key=lambda item: objective_score(item), reverse=True)
    selected: list[dict[str, Any]] = []
    seen_durations: set[int] = set()
    for item in ranked:
        if len(selected) >= 3:
            break
        if item["duration_seconds"] in seen_durations and len(cells) - len(selected) >= 2:
            continue
        selected.append(item)
        seen_durations.add(item["duration_seconds"])
    for item in ranked:
        if len(selected) >= 3:
            break
        if item not in selected:
            selected.append(item)
    labels = ["A", "B", "C"]
    for label, item in zip(labels, selected):
        item["selected_for_presented_abc"] = True
        item["presented_label"] = label
        item["diagnostic_disposition"] = "presented_for_human_review"
        item["selection_reason"] = (
            f"Selected by objective pre-screen from {item['pipeline_label']} {item['duration_seconds']}s: "
            f"score {objective_score(item)}, motion delta {item['machine_motion_probe']['crew_crop_motion_delta_score']}, "
            f"crouch flag {item['machine_motion_probe']['squat_crouch_probe']['machine_flag']}, "
            f"upper-body flag {item['machine_motion_probe']['upper_body_raise_probe']['machine_flag']}."
        )
    return selected


def make_contact_sheet(*, rows: list[tuple[str, list[Path]]], output_path: Path, title: str, thumb_w: int, thumb_h: int) -> None:
    ensure_dir(output_path.parent)
    columns = max(len(paths) for _, paths in rows)
    gutter = 10
    top_h = 60
    label_h = 42
    sheet_w = gutter + columns * (thumb_w + gutter)
    sheet_h = top_h + len(rows) * (label_h + thumb_h + gutter) + gutter
    canvas = Image.new("RGB", (sheet_w, sheet_h), (7, 12, 22))
    draw = ImageDraw.Draw(canvas)
    draw.text((gutter, 16), title, fill=(247, 235, 214), font=safe_font(22))
    for row_index, (label, frame_paths) in enumerate(rows):
        row_y = top_h + row_index * (label_h + thumb_h + gutter)
        draw.text((gutter, row_y + 8), label[:120], fill=(247, 235, 214), font=safe_font(14))
        for col, frame_path in enumerate(frame_paths):
            image = Image.open(frame_path).convert("RGB")
            image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb_w, thumb_h), (4, 10, 19))
            tile.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
            x = gutter + col * (thumb_w + gutter)
            y = row_y + label_h
            canvas.paste(tile, (x, y))
    canvas.save(output_path, quality=92)


def make_contact_sheets(cells: list[dict[str, Any]], selected: list[dict[str, Any]], input_payload: dict[str, Any]) -> dict[str, Path]:
    contact_dir = PACKET_ROOT / "qa" / "contact_sheets"
    rows_full: list[tuple[str, list[Path]]] = []
    rows_crop: list[tuple[str, list[Path]]] = []
    rows_matte: list[tuple[str, list[Path]]] = []
    rows_transition: list[tuple[str, list[Path]]] = []
    rows_rejected: list[tuple[str, list[Path]]] = []
    selected_ids = {item["cell_id"] for item in selected}
    for item in cells:
        label = (
            f"{item['cell_id']} | score {objective_score(item)} | "
            f"terminal {item['terminal_timing']['terminal_walk_start_display']}"
        )
        rows_full.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["composited_full_frame"]]))
        rows_crop.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["crew_crop"]]))
        rows_matte.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["matte"]]))
        rows_transition.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["still_to_walk_transition"]]))
        if item["cell_id"] not in selected_ids:
            rows_rejected.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["crew_crop"]]))

    source_contact = contact_dir / "variable_duration_plate_and_source_contact_sheet.jpg"
    make_contact_sheet(
        rows=[
            ("Static no-crew plate", [Path(input_payload["no_crew_plate"]["path"])]),
            ("Static pre-walk composite", [Path(input_payload["static_prewalk_full_frame"]["path"])]),
            ("Crew chroma source", [Path(input_payload["chroma_source"]["path"])]),
        ],
        output_path=source_contact,
        title="Variable-Duration Terminal Walk - Plate and Source",
        thumb_w=426,
        thumb_h=240,
    )
    selected_rows = []
    for item in selected:
        selected_rows.append(
            (
                f"{item['presented_label']} = {item['cell_id']} | terminal {item['terminal_timing']['terminal_walk_start_display']}",
                [Path(frame["path"]) for frame in item["qa_frames"]["composited_full_frame"]],
            )
        )

    outputs = {
        "plate_and_source": source_contact,
        "duration_pipeline_matrix_full_frame": contact_dir / "variable_duration_pipeline_matrix_full_frame_contact_sheet.jpg",
        "duration_pipeline_matrix_crew_crop": contact_dir / "variable_duration_pipeline_matrix_crew_crop_contact_sheet.jpg",
        "alpha_matte_qa": contact_dir / "variable_duration_alpha_matte_contact_sheet.jpg",
        "still_to_walk_transition": contact_dir / "variable_duration_still_to_walk_transition_contact_sheet.jpg",
        "presented_abc": contact_dir / "variable_duration_presented_abc_contact_sheet.jpg",
        "rejected_diagnostic_cells": contact_dir / "variable_duration_rejected_diagnostic_cells_contact_sheet.jpg",
    }
    make_contact_sheet(rows=rows_full, output_path=outputs["duration_pipeline_matrix_full_frame"], title="Variable-Duration Terminal Walk - Full Frame Matrix", thumb_w=210, thumb_h=118)
    make_contact_sheet(rows=rows_crop, output_path=outputs["duration_pipeline_matrix_crew_crop"], title="Variable-Duration Terminal Walk - Crew Crop Matrix", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows_matte, output_path=outputs["alpha_matte_qa"], title="Variable-Duration Terminal Walk - Alpha Matte QA", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows_transition, output_path=outputs["still_to_walk_transition"], title="Variable-Duration Terminal Walk - Still-to-Walk Transition", thumb_w=184, thumb_h=103)
    make_contact_sheet(rows=selected_rows, output_path=outputs["presented_abc"], title="Variable-Duration Terminal Walk - Presented A/B/C", thumb_w=256, thumb_h=144)
    make_contact_sheet(rows=rows_rejected or selected_rows, output_path=outputs["rejected_diagnostic_cells"], title="Variable-Duration Terminal Walk - Non-Presented Diagnostic Cells", thumb_w=256, thumb_h=102)
    return outputs


def build_presented_candidate_payloads(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for item in selected:
        candidate = {
            "label": item["presented_label"],
            "source_cell_id": item["cell_id"],
            "pipeline_lane": item["pipeline_lane"],
            "pipeline_label": item["pipeline_label"],
            "duration_seconds": item["duration_seconds"],
            "frames": item["frames_after_normalization"],
            "seed": item["seed"],
            "terminal_walk_start_seconds": item["terminal_timing"]["terminal_walk_start_seconds"],
            "terminal_walk_start_display": item["terminal_timing"]["terminal_walk_start_display"],
            "selection_reason": item.get("selection_reason"),
            "raw_chroma_crew_clip": item["raw_chroma_crew_clip"],
            "keyed_alpha_preview_clip": item["keyed_alpha_preview_clip"],
            "composited_full_frame_clip": item["composited_full_frame_clip"],
            "transition_review_clip": item["transition_review_clip"],
            "machine_motion_probe": item["machine_motion_probe"],
            "selected_for_full_runtime_html_proof": False,
            "selected_for_full_runtime_html_proof_status": "pending_human_review",
            "human_disposition": "defer",
        }
        write_json(PACKET_ROOT / "candidates" / f"variant_{item['presented_label'].lower()}.json", candidate)
        payloads.append(candidate)
    return payloads


def build_manifest(input_payload: dict[str, Any], cells: list[dict[str, Any]], selected: list[dict[str, Any]], presented: list[dict[str, Any]], contact_sheets: dict[str, Path]) -> dict[str, Any]:
    forbidden_sidecars = [
        str(path)
        for path in PACKET_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".wav", ".mp3", ".srt", ".vtt", ".html", ".mov"}
    ]
    all_clips = []
    for item in cells:
        all_clips.extend([item["raw_chroma_crew_clip"], item["keyed_alpha_preview_clip"], item["composited_full_frame_clip"], item["transition_review_clip"]])
    all_no_audio = all(not clip["has_audio"] for clip in all_clips)
    duration_ok = all(abs(item["composited_full_frame_clip"]["duration_seconds"] - item["duration_seconds"]) < 0.08 for item in cells)
    matrix_ids = {f"{lane.id}_{duration.seconds}s" for lane in PIPELINE_LANES for duration in DURATION_CELLS}
    actual_ids = {item["cell_id"] for item in cells}
    return {
        "packet_id": PACKET_ID,
        "gate": "rough_assembly_ltx_variable_duration_terminal_walk_scout_gate",
        "status": "review_ready_pending_human_variable_duration_terminal_walk_keep",
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
        "created_from_disposition": "tighten_after_fixed_12s_terminal_walk_scout_squat_and_slow_gait",
        "tightened_source_packet_path": str(CURRENT_TERMINAL_SCOUT_ROOT),
        "tightened_source_manifest_path": str(CURRENT_TERMINAL_SCOUT_MANIFEST),
        "review_only": True,
        "ltx_variable_duration_terminal_walk_scout_only": True,
        "full_runtime_html_proof_created": False,
        "full_runtime_mp4_created": False,
        "final_assembly_created": False,
        "profileId": "cascade-ink-lit-photoreal-v1",
        "source_visual": {
            "carrier": "kept_variant_c_source_art_split_into_static_no_crew_plate_plus_keyed_terminal_walk_crew_layer",
            "source_art_path": str(SOURCE_ART_PATH),
            "source_art_sha256": sha256(SOURCE_ART_PATH),
            "expected_source_art_sha256": EXPECTED_SOURCE_SHA256,
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "source_art_dimensions": {"width": FULL_WIDTH, "height": FULL_HEIGHT, "aspect_ratio": "16:9"},
            "crew_crop_box": {"x": CREW_CROP_BOX[0], "y": CREW_CROP_BOX[1], "width": WIDTH, "height": HEIGHT},
            "reused_chroma_key_inputs": input_payload,
        },
        "ltx_runtime": {
            "runtime": str(LTX_BIN),
            "runtime_root": str(LTX_RUNTIME_ROOT),
            "model": MODEL_REPO,
            "gemma": TEXT_ENCODER_REPO,
            "enhance_prompt": False,
            "width": WIDTH,
            "height": HEIGHT,
            "runtime_path_read": "pass" if LTX_BIN.exists() else "reject_missing_runtime",
        },
        "diagnostic_matrix_contract": {
            "durations_seconds": [duration.seconds for duration in DURATION_CELLS],
            "frames_at_24fps": {str(duration.seconds): duration.frames for duration in DURATION_CELLS},
            "pipeline_lanes": [lane.id for lane in PIPELINE_LANES],
            "expected_cell_ids": sorted(matrix_ids),
            "actual_cell_ids": sorted(actual_ids),
            "all_cells_generated": matrix_ids == actual_ids,
            "no_time_stretch_policy": "Every diagnostic cell is generated at true duration. No prefix stretching or retiming is used.",
        },
        "future_full_runtime_policy": {
            "approved_audio_duration_seconds": APPROVED_AUDIO_DURATION_SECONDS,
            "approved_audio_duration_display": APPROVED_AUDIO_DURATION_DISPLAY,
            "terminal_start_rule": "selected_terminal_walk_start = approved_audio_duration - selected_candidate_duration",
            "pre_walk_state": "static keyed seven-astronaut layer over no-crew plate",
            "terminal_walk_state": "selected LTX-generated green-screen crew layer composited once over static no-crew plate",
            "right_rail_policy": "existing staged right rail remains preserved and unchanged in any future HTML proof",
        },
        "diagnostic_cells": cells,
        "presented_candidates": presented,
        "contact_sheets": {key: artifact(path) for key, path in contact_sheets.items()},
        "variable_duration_reads": {
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "ltx_runtime_read": "pass" if LTX_BIN.exists() else "reject_missing_runtime",
            "duration_matrix_read": "pass_4s_6s_8s_12s" if {item["duration_seconds"] for item in cells} == {4, 6, 8, 12} else "reject_missing_duration",
            "pipeline_matrix_read": "pass_one_stage_and_two_stage" if {item["pipeline_lane"] for item in cells} == {lane.id for lane in PIPELINE_LANES} else "reject_missing_pipeline_lane",
            "true_duration_no_stretch_read": "pass" if all(item["true_duration_no_time_stretch"] for item in cells) else "reject_time_stretched",
            "raw_chroma_audio_read": "pass_no_audio" if all_no_audio else "reject_audio_present",
            "clip_duration_read": "pass_true_duration" if duration_ok else "tighten_duration_mismatch",
            "contact_sheet_read": "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet",
            "forbidden_media_copy_read": "pass_no_audio_caption_transcript_html_mov_sidecars" if not forbidden_sidecars else "reject_forbidden_sidecar_found",
            "full_runtime_html_proof_read": "pass_not_created",
            "full_runtime_mp4_read": "pass_not_created",
            "final_assembly_read": "pass_not_created",
            "duration_fit_read": "defer_pending_human_review",
            "natural_gait_read": "defer_pending_human_review",
            "squat_crouch_read": "defer_pending_human_review",
            "walk_speed_read": "defer_pending_human_review",
            "two_stage_distilled_read": "defer_pending_human_review",
            "crew_count_read": "defer_pending_human_review",
            "hand_waving_read": "defer_pending_human_review",
            "non_synchronized_stride_read": "defer_pending_human_review",
            "matte_edge_read": "defer_pending_human_review",
            "background_stability_read": "defer_pending_human_review",
            "right_rail_safe_space_read": "defer_pending_human_review",
            "long_runtime_terminal_carrier_read": "defer_pending_human_review",
        },
        "forbidden_sidecars_found": forbidden_sidecars,
        "may_select_variable_duration_terminal_walk_candidate_after_human_keep": False,
        "may_create_full_runtime_html_proof": False,
        "may_create_full_runtime_mp4_render": False,
        "may_advance_to_final_assembly": False,
        "may_advance_to_shorts_work": False,
        "may_advance_to_publish_readiness": False,
        "may_youtube_action": False,
        "next_review_question": "Review A/B/C and reply with exactly one response: keep A, keep B, keep C, tighten, or reject.",
    }


def build_readme(manifest: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        f"- {item['label']}: `{item['source_cell_id']}`, {item['duration_seconds']}s, {item['pipeline_label']}, "
        f"seed `{item['seed']}`, terminal start `{item['terminal_walk_start_display']}`"
        for item in manifest["presented_candidates"]
    )
    return f"""# Challenger Living Cover Variable-Duration Terminal Walk Scout

Packet: `{PACKET_ID}`
Status: `{manifest['status']}`
Human disposition: `defer`

This packet records the fixed-12s terminal-walk scout as `tighten`. Variant A was the best prior direction, but the pre-step squat/crouch and slow stretched gait block keep. This successor tests true-duration LTX generations at `4s`, `6s`, `8s`, and `12s` across one-stage q8 and two-stage distilled-LoRA lanes.

## Presented A/B/C

{candidate_rows}

## Diagnostic Matrix

- Durations: `4s`, `6s`, `8s`, `12s`
- Pipelines: `one_stage_q8`, `two_stage_distilled_lora`
- No clip is stretched or retimed to meet a target duration.
- Future full-runtime walk start is computed as `00:21:29.131 - selected_candidate_duration`.

## Review Surfaces

- Presented A/B/C contact sheet: `{manifest['contact_sheets']['presented_abc']['path']}`
- Full-frame matrix: `{manifest['contact_sheets']['duration_pipeline_matrix_full_frame']['path']}`
- Crew-crop matrix: `{manifest['contact_sheets']['duration_pipeline_matrix_crew_crop']['path']}`
- Alpha/matte QA: `{manifest['contact_sheets']['alpha_matte_qa']['path']}`
- Still-to-walk transition: `{manifest['contact_sheets']['still_to_walk_transition']['path']}`
- Non-presented diagnostics: `{manifest['contact_sheets']['rejected_diagnostic_cells']['path']}`

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.
"""


def build_review(manifest: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        "| {label} | `{cell}` | `{dur}s` | `{pipeline}` | `{start}` | `{clip}` | `{review}` |".format(
            label=item["label"],
            cell=item["source_cell_id"],
            dur=item["duration_seconds"],
            pipeline=item["pipeline_lane"],
            start=item["terminal_walk_start_display"],
            clip=item["composited_full_frame_clip"]["path"],
            review=item["transition_review_clip"]["path"],
        )
        for item in manifest["presented_candidates"]
    )
    read_rows = "\n".join(f"| `{key}` | `{value}` |" for key, value in manifest["variable_duration_reads"].items())
    return f"""# Challenger Living Cover Variable-Duration Terminal Walk Scout Review

Packet: `{PACKET_ID}`
Gate: `rough_assembly_ltx_variable_duration_terminal_walk_scout_gate`
Human disposition: `defer`

## What Changed

- Current 12s terminal-walk scout is recorded as `tighten`.
- The fixed 12s ending rule is released; each candidate carries its own duration and computed full-episode terminal start time.
- LTX still runs only on the green-screen seven-astronaut crew layer. The shuttle, pad, sky, and right-rail safe area remain static from the no-crew plate.
- The diagnostic matrix tests `4s`, `6s`, `8s`, and `12s` true-duration generations across one-stage q8 and two-stage distilled-LoRA lanes.

## Presented Candidates

| Candidate | Source Cell | Duration | Pipeline | Future Terminal Start | Walk Composite | Static-Then-Walk Review |
|---|---|---:|---|---:|---|---|
{candidate_rows}

## Contact Sheets

- Presented A/B/C: `{manifest['contact_sheets']['presented_abc']['path']}`
- Full-frame matrix: `{manifest['contact_sheets']['duration_pipeline_matrix_full_frame']['path']}`
- Crew-crop matrix: `{manifest['contact_sheets']['duration_pipeline_matrix_crew_crop']['path']}`
- Alpha matte QA: `{manifest['contact_sheets']['alpha_matte_qa']['path']}`
- Still-to-walk transition: `{manifest['contact_sheets']['still_to_walk_transition']['path']}`
- Non-presented diagnostics: `{manifest['contact_sheets']['rejected_diagnostic_cells']['path']}`

## Reads

| Read | Result |
|---|---:|
{read_rows}

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof with static crew until that candidate's computed terminal start time, then the selected terminal-walk carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.
"""


def main() -> None:
    for subdir in [
        "assets/background_plate",
        "assets/crew_chroma_source",
        "prompts",
        "diagnostics",
        "candidates",
        "clips/raw_chroma_crew",
        "clips/keyed_alpha_preview",
        "clips/composited_full_frame",
        "clips/transition_review",
        "qa/frames",
        "qa/contact_sheets",
        "logs",
        "review",
        "work/ltx_raw_with_possible_audio",
    ]:
        ensure_dir(PACKET_ROOT / subdir)
    if not SOURCE_ART_PATH.exists():
        raise FileNotFoundError(SOURCE_ART_PATH)
    if sha256(SOURCE_ART_PATH) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Kept Variant C source-art hash mismatch")
    if not LTX_BIN.exists():
        raise FileNotFoundError(LTX_BIN)
    update_current_terminal_scout()
    input_payload = copy_inputs()
    chroma_source = Path(input_payload["chroma_source"]["path"])
    no_crew_plate = Path(input_payload["no_crew_plate"]["path"])
    static_full_frame = Path(input_payload["static_prewalk_full_frame"]["path"])

    cells: list[dict[str, Any]] = []
    cell_index = 0
    for lane in PIPELINE_LANES:
        for duration in DURATION_CELLS:
            cell_index += 1
            cells.append(render_cell(lane, duration, chroma_source, no_crew_plate, static_full_frame, cell_index))

    selected = select_presented_candidates(cells)
    for cell in cells:
        write_json(PACKET_ROOT / "diagnostics" / f"{cell['cell_id']}.json", cell)
    presented = build_presented_candidate_payloads(selected)
    contact_sheets = make_contact_sheets(cells, selected, input_payload)
    manifest = build_manifest(input_payload, cells, selected, presented, contact_sheets)
    manifest_path = PACKET_ROOT / "variable_duration_terminal_walk_manifest.json"
    readme_path = PACKET_ROOT / "README.md"
    review_path = PACKET_ROOT / "review" / "variable_duration_terminal_walk_review_packet.md"
    write_json(manifest_path, manifest)
    write_text(readme_path, build_readme(manifest))
    write_text(review_path, build_review(manifest))
    manifest["artifacts"] = {
        "manifest": {
            "path": str(manifest_path),
            "sha256": None,
            "bytes": None,
            "hash_note": "Self-referential manifest hash intentionally omitted; validate externally with shasum.",
        },
        "readme": artifact(readme_path),
        "review_packet": artifact(review_path),
        "builder_script": artifact(Path(__file__)),
        **{key: artifact(path) for key, path in contact_sheets.items()},
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"packet_root": str(PACKET_ROOT), "manifest_path": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
