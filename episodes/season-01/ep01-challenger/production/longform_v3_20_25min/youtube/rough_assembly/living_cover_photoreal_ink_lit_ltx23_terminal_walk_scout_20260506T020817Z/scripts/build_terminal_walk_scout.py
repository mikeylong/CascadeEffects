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

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


CREATED_UTC = "2026-05-06T02:08:17Z"
PACKET_ID = "living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z"
PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_ltx23_terminal_walk_scout_20260506T020817Z"
)
CURRENT_CHROMA_SCOUT_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z"
)
CURRENT_CHROMA_SCOUT_MANIFEST = CURRENT_CHROMA_SCOUT_ROOT / "motion_scout_manifest.json"
SOURCE_ART_PATH = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png"
)
EXPECTED_SOURCE_SHA256 = "52f94150037d5aa40633d34b29c137c59c5868e987bc5f8b7f80903f6bc2ac8a"
PREVIOUS_NO_CREW_PLATE = CURRENT_CHROMA_SCOUT_ROOT / "assets/background_plate/variant_c_aligned_no_crew_plate.png"
PREVIOUS_NO_CREW_MASK = CURRENT_CHROMA_SCOUT_ROOT / "assets/background_plate/variant_c_no_crew_plate_mask.png"
PREVIOUS_CHROMA_SOURCE = CURRENT_CHROMA_SCOUT_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_green_screen_source.png"
PREVIOUS_ALPHA_REFERENCE = CURRENT_CHROMA_SCOUT_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_alpha_reference.png"
PREVIOUS_SOURCE_MASK = CURRENT_CHROMA_SCOUT_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_source_mask.png"
LTX_BIN = Path("/Users/mike/AI/ltx-2-mlx/.venv/bin/ltx-2-mlx")
LTX_RUNTIME_ROOT = Path("/Users/mike/AI/ltx-2-mlx")
MODEL_REPO = "dgrauet/ltx-2.3-mlx-q8"
TEXT_ENCODER_REPO = "mlx-community/gemma-3-12b-it-4bit"
FULL_WIDTH = 1920
FULL_HEIGHT = 1080
WIDTH = 960
HEIGHT = 384
FPS = 24
FRAMES_REQUESTED = 289
NORMALIZED_FRAMES = 288
STEPS = 8
WALK_SECONDS = 12.0
REVIEW_STILL_SECONDS = 2.0
REVIEW_SECONDS = 14.0
APPROVED_AUDIO_DURATION_SECONDS = 1289.131247
TERMINAL_WALK_START_SECONDS = 1277.131247
APPROVED_AUDIO_DURATION_DISPLAY = "00:21:29.131"
TERMINAL_WALK_START_DISPLAY = "00:21:17.131"
CREW_CROP_BOX = (96, 696, 1056, 1080)
RAW_QA_FRAMES = [0, 36, 72, 144, 216, 287]
WALK_QA_FRAMES = [0, 36, 72, 144, 216, 287]
TRANSITION_QA_FRAMES = [0, 24, 47, 48, 60, 84, 120, 180, 240, 335]


@dataclass(frozen=True)
class Candidate:
    id: str
    label: str
    seed: int
    cfg_scale: float
    stg_scale: float
    prompt_variant_id: str
    motion_line: str


CANDIDATES = [
    Candidate(
        id="variant_a",
        label="A",
        seed=404101,
        cfg_scale=1.15,
        stg_scale=0.20,
        prompt_variant_id="restrained_first_step_cue_a",
        motion_line=(
            "The group stands still for the first moment, then begins only a restrained first-step cue. "
            "Minimal travel away from camera, quiet posture, tiny stagger between people."
        ),
    ),
    Candidate(
        id="variant_b",
        label="B",
        seed=404203,
        cfg_scale=1.35,
        stg_scale=0.32,
        prompt_variant_id="clear_calm_asynchronous_walk_start_b",
        motion_line=(
            "Recommended middle path: seven astronauts begin a clear calm walk away from camera with staggered first steps, "
            "modest travel toward the unseen shuttle pad, natural low arm movement only."
        ),
    ),
    Candidate(
        id="variant_c",
        label="C",
        seed=404307,
        cfg_scale=1.55,
        stg_scale=0.45,
        prompt_variant_id="readable_restrained_terminal_walk_c",
        motion_line=(
            "More readable terminal action: the group begins walking away from camera toward the unseen shuttle pad, "
            "still restrained, no running, no theatrical gestures, arms remain low."
        ),
    ),
]


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


def safe_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for item in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(item).exists():
            return ImageFont.truetype(item, size)
    return ImageFont.load_default()


def ltx_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    env.setdefault("HF_HUB_CACHE", str(Path.home() / ".cache" / "huggingface" / "hub"))
    return env


def update_current_chroma_scout() -> None:
    manifest = read_json(CURRENT_CHROMA_SCOUT_MANIFEST)
    manifest["human_disposition"] = "tighten"
    manifest["status"] = "tighten_terminal_walk_successor_required"
    manifest["tighten_record"] = {
        "recorded_utc": CREATED_UTC,
        "reviewer_note": (
            "A/B/C chroma-key micro-motion candidates are clean but read too still. "
            "Change motion concept from continuous living loop to a terminal narrative action: static crew until the final 12 seconds, then seven astronauts begin walking toward the shuttle pad."
        ),
        "required_successor": "ltx23_terminal_walk_scout",
    }
    reads = manifest.setdefault("motion_scout_reads", {})
    reads["motion_detectability_read"] = "tighten_too_still_for_review"
    reads["crew_loop_read"] = "tighten_loop_concept_replaced_by_terminal_walk"
    reads["long_runtime_carrier_read"] = "tighten_static_then_terminal_walk_required"
    reads["terminal_walk_successor_read"] = "pass_successor_packet_created"
    manifest["terminal_walk_successor"] = {
        "packet_path": str(PACKET_ROOT),
        "manifest_path": str(PACKET_ROOT / "terminal_walk_manifest.json"),
        "review_packet_path": str(PACKET_ROOT / "review" / "terminal_walk_review_packet.md"),
        "created_utc": CREATED_UTC,
        "human_disposition": "defer",
    }
    for flag in [
        "may_select_chroma_key_candidate_after_human_keep",
        "may_create_full_runtime_html_proof",
        "may_create_full_runtime_mp4_render",
        "may_advance_to_final_assembly",
        "may_advance_to_shorts_work",
        "may_advance_to_publish_readiness",
        "may_youtube_action",
    ]:
        manifest[flag] = False
    manifest["next_review_question"] = "Current micro-motion scout is tighten. Review the terminal-walk successor packet."
    write_json(CURRENT_CHROMA_SCOUT_MANIFEST, manifest)

    append = (
        "\n## Terminal-Walk Successor\n\n"
        "Human disposition: `tighten`.\n\n"
        "Reason: the chroma-key A/B/C micro-motion candidates are clean but read too still. "
        "The successor changes the concept to a one-time final-12-second walk toward the shuttle pad.\n\n"
        f"Successor packet: `{PACKET_ROOT}`\n"
    )
    for md_path in [CURRENT_CHROMA_SCOUT_ROOT / "README.md", CURRENT_CHROMA_SCOUT_ROOT / "review" / "motion_scout_review_packet.md"]:
        if md_path.exists():
            text = md_path.read_text(encoding="utf-8")
            if "## Terminal-Walk Successor" not in text:
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
    static_keyed, _ = key_chroma_frame(Image.open(copied["chroma_source"]["path"]))
    base = Image.open(copied["no_crew_plate"]["path"]).convert("RGB").convert("RGBA")
    base.alpha_composite(static_keyed, dest=(CREW_CROP_BOX[0], CREW_CROP_BOX[1]))
    static_preview = assets / "static_prewalk_full_frame.png"
    base.convert("RGB").save(static_preview)
    copied["static_prewalk_full_frame"] = artifact(static_preview)
    return copied


def build_prompt(candidate: Candidate) -> str:
    return (
        "Image-to-video of a green-screen crew layer only. The input image shows exactly seven astronauts in blue flight suits, "
        "seen from behind on a pure flat chroma green background. Preserve exactly seven people and preserve their back-view identities. "
        f"Action: {candidate.motion_line} "
        "They are walking away from camera toward an unseen shuttle pad, moving gently upstage within the frame. "
        "The first frames should match the input standing pose, then the walk begins. "
        "Keep the group calm and solemn. Keep feet and legs believable. Keep arms low; only small natural walking arm motion is allowed. "
        "Stride timing must be staggered and human, not synchronized marching. Keep all bodies facing away from camera. "
        "Keep the background pure chroma green and blank. No camera movement. "
        "No waving. No saluting. No pointing. No raised hands. No running. No jumping. No dancing. No synchronized marching. "
        "No turning around. No faces. No readable logos. No name patches. No text. No extra people. No missing people. No duplicated people. "
        "No smoke. No fire. No launch. No sparks. No atmosphere effects. No pad background. No floor detail. No props."
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


def key_chroma_frame(frame: Image.Image) -> tuple[Image.Image, Image.Image]:
    rgb = frame.convert("RGB")
    arr = np.array(rgb).astype(np.float32)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    green_distance = g - np.maximum(r, b)
    is_key = (g > 34) & (green_distance > 8) & (r < 150) & (b < 165)
    alpha = np.where(is_key, 0, 255).astype(np.uint8)
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.MedianFilter(size=5))
    alpha_img = alpha_img.filter(ImageFilter.MinFilter(size=3)).filter(ImageFilter.GaussianBlur(radius=0.65))
    alpha_img = Image.eval(alpha_img, lambda px: 0 if px < 128 else px)
    rgba = rgb.convert("RGBA")
    rgba.putalpha(alpha_img)
    rgba_arr = np.array(rgba).astype(np.float32)
    alpha_float = np.array(alpha_img).astype(np.float32) / 255.0
    edge_weight = np.clip(1.0 - np.abs(alpha_float - 0.55) * 2.0, 0.0, 1.0)
    target_green = np.maximum(rgba_arr[:, :, 0], rgba_arr[:, :, 2]) * 0.84
    spill_weight = np.clip((1.0 - alpha_float) + edge_weight, 0.0, 1.0)
    rgba_arr[:, :, 1] = rgba_arr[:, :, 1] * (1.0 - spill_weight) + target_green * spill_weight
    keyed = Image.fromarray(np.clip(rgba_arr, 0, 255).astype(np.uint8), "RGBA")
    return keyed, alpha_img


def key_and_composite_frames(raw_paths: list[Path], no_crew_plate: Path, keyed_dir: Path, matte_dir: Path, full_dir: Path, crop_dir: Path) -> dict[str, list[Path]]:
    for path in [keyed_dir, matte_dir, full_dir, crop_dir]:
        if path.exists():
            shutil.rmtree(path)
        ensure_dir(path)
    base = Image.open(no_crew_plate).convert("RGB")
    output: dict[str, list[Path]] = {"keyed": [], "matte": [], "full": [], "crew_crop": []}
    for index, frame_path in enumerate(raw_paths):
        keyed, matte = key_chroma_frame(Image.open(frame_path))
        keyed_path = keyed_dir / f"frame_{index:04d}.png"
        matte_path = matte_dir / f"frame_{index:04d}.png"
        full_path = full_dir / f"frame_{index:04d}.png"
        crop_path = crop_dir / f"frame_{index:04d}.png"
        keyed.save(keyed_path)
        matte.save(matte_path)
        composite = base.copy().convert("RGBA")
        composite.alpha_composite(keyed, dest=(CREW_CROP_BOX[0], CREW_CROP_BOX[1]))
        full_rgb = composite.convert("RGB")
        full_rgb.save(full_path)
        full_rgb.crop(CREW_CROP_BOX).save(crop_path)
        output["keyed"].append(keyed_path)
        output["matte"].append(matte_path)
        output["full"].append(full_path)
        output["crew_crop"].append(crop_path)
    return output


def copy_sequence_frame(sequence: list[Path], frame_index: int, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    shutil.copyfile(sequence[frame_index], output_path)


def make_transition_review_frames(static_full_frame: Path, walk_full_frames: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    ensure_dir(output_dir)
    static = Image.open(static_full_frame).convert("RGB")
    output: list[Path] = []
    for index in range(int(REVIEW_SECONDS * FPS)):
        if index < int(REVIEW_STILL_SECONDS * FPS):
            img = static
        else:
            walk_index = min(index - int(REVIEW_STILL_SECONDS * FPS), len(walk_full_frames) - 1)
            img = Image.open(walk_full_frames[walk_index]).convert("RGB")
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


def hand_raise_probe(crew_crop_paths: list[Path]) -> dict[str, Any]:
    top_bands: list[int] = []
    for path in crew_crop_paths:
        img = Image.open(path).convert("RGB")
        arr = np.array(img)
        zone = arr[55:180, :, :]
        blue = (zone[:, :, 2] > zone[:, :, 1] + 14) & (zone[:, :, 2] > zone[:, :, 0] + 20) & (zone[:, :, 2] > 55)
        top_bands.append(int(blue.sum()))
    baseline = top_bands[0] if top_bands else 0
    max_delta = max([abs(value - baseline) for value in top_bands], default=0)
    return {
        "upper_body_blue_pixel_counts": top_bands,
        "max_delta_from_first": max_delta,
        "machine_flag": "review" if max_delta > 9000 else "no_large_upper_body_raise_detected",
    }


def render_candidate(candidate: Candidate, chroma_source: Path, no_crew_plate: Path, static_full_frame: Path) -> dict[str, Any]:
    prompt = build_prompt(candidate)
    prompt_path = PACKET_ROOT / "prompts" / f"{candidate.id}_terminal_walk_prompt.txt"
    write_text(prompt_path, prompt + "\n")
    ltx_temp = PACKET_ROOT / "work" / "ltx_raw_with_possible_audio" / f"{candidate.id}_seed{candidate.seed}_terminal_walk_with_possible_audio.mp4"
    raw_chroma = PACKET_ROOT / "clips" / "raw_chroma_crew" / f"{candidate.id}_seed{candidate.seed}_terminal_walk_raw_chroma_12s.mp4"
    command = [
        str(LTX_BIN),
        "generate",
        "--prompt",
        prompt,
        "--output",
        str(ltx_temp),
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
        str(FRAMES_REQUESTED),
        "--image",
        str(chroma_source),
        "--steps",
        str(STEPS),
        "--cfg-scale",
        str(candidate.cfg_scale),
        "--stg-scale",
        str(candidate.stg_scale),
    ]
    ensure_dir(ltx_temp.parent)
    run(command, cwd=LTX_RUNTIME_ROOT, env=ltx_env(), log_path=PACKET_ROOT / "logs" / f"{candidate.id}_ltx23_generate.log")
    strip_audio_and_normalize(ltx_temp, raw_chroma, width=WIDTH, height=HEIGHT, frames=NORMALIZED_FRAMES)
    ltx_temp.unlink(missing_ok=True)

    raw_frames = extract_all_frames(raw_chroma, PACKET_ROOT / "work" / "raw_chroma_frames" / candidate.id)
    keyed_dirs = key_and_composite_frames(
        raw_frames,
        no_crew_plate,
        PACKET_ROOT / "work" / "keyed_frames" / candidate.id,
        PACKET_ROOT / "work" / "matte_frames" / candidate.id,
        PACKET_ROOT / "work" / "full_frame_frames" / candidate.id,
        PACKET_ROOT / "work" / "crew_crop_frames" / candidate.id,
    )
    keyed_clip = PACKET_ROOT / "clips" / "keyed_alpha_preview" / f"{candidate.id}_terminal_walk_keyed_alpha_preview_12s.mp4"
    composited_clip = PACKET_ROOT / "clips" / "composited_full_frame" / f"{candidate.id}_terminal_walk_composited_full_frame_12s.mp4"
    transition_dir = PACKET_ROOT / "work" / "transition_review_frames" / candidate.id
    transition_frames = make_transition_review_frames(static_full_frame, keyed_dirs["full"], transition_dir)
    transition_clip = PACKET_ROOT / "clips" / "transition_review" / f"{candidate.id}_static_then_terminal_walk_review_14s.mp4"
    encode_frames(PACKET_ROOT / "work" / "keyed_frames" / candidate.id, keyed_clip, width=WIDTH, height=HEIGHT)
    encode_frames(PACKET_ROOT / "work" / "full_frame_frames" / candidate.id, composited_clip, width=FULL_WIDTH, height=FULL_HEIGHT)
    encode_frames(transition_dir, transition_clip, width=FULL_WIDTH, height=FULL_HEIGHT)

    qa: dict[str, list[Path]] = {
        "raw_chroma_crew": [],
        "matte": [],
        "composited_full_frame": [],
        "crew_crop": [],
        "still_to_walk_transition": [],
    }
    for frame_index in RAW_QA_FRAMES:
        raw_out = PACKET_ROOT / "qa" / "frames" / "raw_chroma_crew" / candidate.id / f"{candidate.id}_raw_{frame_index:03d}.png"
        copy_sequence_frame(raw_frames, frame_index, raw_out)
        qa["raw_chroma_crew"].append(raw_out)
    for frame_index in WALK_QA_FRAMES:
        matte_out = PACKET_ROOT / "qa" / "frames" / "matte" / candidate.id / f"{candidate.id}_matte_{frame_index:03d}.png"
        full_out = PACKET_ROOT / "qa" / "frames" / "composited_full_frame" / candidate.id / f"{candidate.id}_full_{frame_index:03d}.png"
        crop_out = PACKET_ROOT / "qa" / "frames" / "crew_crop" / candidate.id / f"{candidate.id}_crew_crop_{frame_index:03d}.png"
        copy_sequence_frame(keyed_dirs["matte"], frame_index, matte_out)
        copy_sequence_frame(keyed_dirs["full"], frame_index, full_out)
        copy_sequence_frame(keyed_dirs["crew_crop"], frame_index, crop_out)
        qa["matte"].append(matte_out)
        qa["composited_full_frame"].append(full_out)
        qa["crew_crop"].append(crop_out)
    for frame_index in TRANSITION_QA_FRAMES:
        transition_out = PACKET_ROOT / "qa" / "frames" / "still_to_walk_transition" / candidate.id / f"{candidate.id}_transition_{frame_index:03d}.png"
        copy_sequence_frame(transition_frames, frame_index, transition_out)
        qa["still_to_walk_transition"].append(transition_out)

    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "seed": candidate.seed,
        "prompt_variant_id": candidate.prompt_variant_id,
        "cfg_scale": candidate.cfg_scale,
        "stg_scale": candidate.stg_scale,
        "steps": STEPS,
        "frames_requested": FRAMES_REQUESTED,
        "frames_after_normalization": NORMALIZED_FRAMES,
        "terminal_walk_duration_seconds": WALK_SECONDS,
        "review_transition_duration_seconds": REVIEW_SECONDS,
        "prompt_text": prompt,
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256(prompt_path),
        "ltx_invocation": {
            "runtime": str(LTX_BIN),
            "model": MODEL_REPO,
            "gemma": TEXT_ENCODER_REPO,
            "width": WIDTH,
            "height": HEIGHT,
            "frames": FRAMES_REQUESTED,
            "steps": STEPS,
            "cfg_scale": candidate.cfg_scale,
            "stg_scale": candidate.stg_scale,
            "enhance_prompt": False,
            "pipeline": "one_stage",
        },
        "raw_chroma_crew_clip": video_summary(raw_chroma),
        "keyed_alpha_preview_clip": video_summary(keyed_clip),
        "composited_full_frame_clip": video_summary(composited_clip),
        "transition_review_clip": video_summary(transition_clip),
        "qa_frames": {key: [artifact(path) for path in paths] for key, paths in qa.items()},
        "machine_motion_probe": {
            "crew_crop_motion_delta_score": motion_delta_score(qa["crew_crop"]),
            "hand_raise_probe": hand_raise_probe(qa["crew_crop"]),
            "note": "Machine probes are coarse screening only; human review is authoritative for walking authenticity, crew count, hand waving, and synchronized stride.",
        },
        "disposition": "defer",
        "selected_for_full_runtime_html_proof": False,
        "selected_for_full_runtime_html_proof_status": "pending_human_review",
    }
    write_json(PACKET_ROOT / "candidates" / f"{candidate.id}.json", payload)
    return payload


def make_contact_sheet(*, rows: list[tuple[str, list[Path]]], output_path: Path, title: str, thumb_w: int, thumb_h: int) -> None:
    ensure_dir(output_path.parent)
    columns = max(len(paths) for _, paths in rows)
    gutter = 10
    top_h = 54
    label_h = 38
    sheet_w = gutter + columns * (thumb_w + gutter)
    sheet_h = top_h + len(rows) * (label_h + thumb_h + gutter) + gutter
    canvas = Image.new("RGB", (sheet_w, sheet_h), (7, 12, 22))
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


def make_contact_sheets(candidate_payloads: list[dict[str, Any]], input_payload: dict[str, Any]) -> dict[str, Path]:
    contact_dir = PACKET_ROOT / "qa" / "contact_sheets"
    rows: dict[str, list[tuple[str, list[Path]]]] = {
        "raw_chroma_crew": [],
        "matte": [],
        "composited_full_frame": [],
        "crew_crop": [],
        "still_to_walk_transition": [],
    }
    for item in candidate_payloads:
        label = f"{item['label']} cfg {item['cfg_scale']} stg {item['stg_scale']} - {item['prompt_variant_id']}"
        for key in rows:
            rows[key].append((label, [Path(frame["path"]) for frame in item["qa_frames"][key]]))
    source_contact = contact_dir / "terminal_walk_plate_and_source_contact_sheet.jpg"
    make_contact_sheet(
        rows=[
            ("Static no-crew plate", [Path(input_payload["no_crew_plate"]["path"])]),
            ("Static pre-walk composite", [Path(input_payload["static_prewalk_full_frame"]["path"])]),
            ("Crew chroma source", [Path(input_payload["chroma_source"]["path"])]),
        ],
        output_path=source_contact,
        title="Terminal Walk Scout - Plate and Source",
        thumb_w=426,
        thumb_h=240,
    )
    outputs = {
        "plate_and_source": source_contact,
        "raw_chroma_crew": contact_dir / "terminal_walk_raw_chroma_crew_contact_sheet.jpg",
        "matte": contact_dir / "terminal_walk_alpha_matte_contact_sheet.jpg",
        "composited_full_frame": contact_dir / "terminal_walk_composited_full_frame_contact_sheet.jpg",
        "crew_crop": contact_dir / "terminal_walk_crew_crop_contact_sheet.jpg",
        "still_to_walk_transition": contact_dir / "terminal_walk_still_to_walk_transition_contact_sheet.jpg",
    }
    make_contact_sheet(rows=rows["raw_chroma_crew"], output_path=outputs["raw_chroma_crew"], title="Terminal Walk Scout - Raw Chroma Motion States", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["matte"], output_path=outputs["matte"], title="Terminal Walk Scout - Alpha Matte QA", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["composited_full_frame"], output_path=outputs["composited_full_frame"], title="Terminal Walk Scout - Composited Full Frame", thumb_w=256, thumb_h=144)
    make_contact_sheet(rows=rows["crew_crop"], output_path=outputs["crew_crop"], title="Terminal Walk Scout - Crew Crop Motion States", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["still_to_walk_transition"], output_path=outputs["still_to_walk_transition"], title="Terminal Walk Scout - Still-to-Walk Transition", thumb_w=205, thumb_h=115)
    return outputs


def build_manifest(input_payload: dict[str, Any], candidate_payloads: list[dict[str, Any]], contact_sheets: dict[str, Path]) -> dict[str, Any]:
    forbidden_sidecars = [
        str(path)
        for path in PACKET_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".wav", ".mp3", ".srt", ".vtt", ".html", ".mov"}
    ]
    all_no_audio = all(
        not item["raw_chroma_crew_clip"]["has_audio"]
        and not item["keyed_alpha_preview_clip"]["has_audio"]
        and not item["composited_full_frame_clip"]["has_audio"]
        and not item["transition_review_clip"]["has_audio"]
        for item in candidate_payloads
    )
    walk_duration_ok = all(11.9 <= item["composited_full_frame_clip"]["duration_seconds"] <= 12.1 for item in candidate_payloads)
    review_duration_ok = all(13.9 <= item["transition_review_clip"]["duration_seconds"] <= 14.1 for item in candidate_payloads)
    return {
        "packet_id": PACKET_ID,
        "gate": "rough_assembly_ltx_terminal_walk_scout_gate",
        "status": "review_ready_pending_human_terminal_walk_keep",
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
        "created_from_disposition": "tighten_after_chroma_key_micro_motion_too_still",
        "tightened_source_packet_path": str(CURRENT_CHROMA_SCOUT_ROOT),
        "tightened_source_manifest_path": str(CURRENT_CHROMA_SCOUT_MANIFEST),
        "review_only": True,
        "ltx_terminal_walk_scout_only": True,
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
            "pipeline": "one_stage",
            "enhance_prompt": False,
            "width": WIDTH,
            "height": HEIGHT,
            "frames_requested": FRAMES_REQUESTED,
            "frames_after_normalization": NORMALIZED_FRAMES,
            "steps": STEPS,
            "runtime_path_read": "pass" if LTX_BIN.exists() else "reject_missing_runtime",
        },
        "terminal_walk_contract": {
            "approved_audio_duration_seconds": APPROVED_AUDIO_DURATION_SECONDS,
            "approved_audio_duration_display": APPROVED_AUDIO_DURATION_DISPLAY,
            "terminal_walk_start_seconds": TERMINAL_WALK_START_SECONDS,
            "terminal_walk_start_display": TERMINAL_WALK_START_DISPLAY,
            "terminal_walk_duration_seconds": WALK_SECONDS,
            "pre_walk_state": "static keyed seven-astronaut layer over no-crew plate",
            "terminal_walk_state": "selected 12s LTX-generated green-screen crew layer composited once over static no-crew plate",
            "future_full_runtime_policy": "static crew until 00:21:17.131, then selected terminal-walk carrier once through 00:21:29.131",
            "right_rail_policy": "existing staged right rail remains preserved and unchanged in any future HTML proof",
        },
        "candidates": candidate_payloads,
        "contact_sheets": {key: artifact(path) for key, path in contact_sheets.items()},
        "terminal_walk_reads": {
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "ltx_runtime_read": "pass" if LTX_BIN.exists() else "reject_missing_runtime",
            "candidate_count_read": "pass_three_candidates" if len(candidate_payloads) == 3 else "reject_missing_candidates",
            "raw_chroma_audio_read": "pass_no_audio" if all_no_audio else "reject_audio_present",
            "terminal_walk_duration_read": "pass_12s" if walk_duration_ok else "tighten_duration_not_12s",
            "transition_review_duration_read": "pass_14s" if review_duration_ok else "tighten_duration_not_14s",
            "contact_sheet_read": "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet",
            "forbidden_media_copy_read": "pass_no_audio_caption_transcript_html_mov_sidecars" if not forbidden_sidecars else "reject_forbidden_sidecar_found",
            "full_runtime_html_proof_read": "pass_not_created",
            "full_runtime_mp4_read": "pass_not_created",
            "final_assembly_read": "pass_not_created",
            "terminal_walk_read": "defer_pending_human_review",
            "walk_start_timing_read": "defer_pending_human_review",
            "still_to_walk_pop_read": "defer_pending_human_review",
            "crew_count_read": "defer_pending_human_review",
            "walking_motion_authenticity_read": "defer_pending_human_review",
            "non_synchronized_stride_read": "defer_pending_human_review",
            "hand_waving_read": "defer_pending_human_review",
            "identity_logo_text_read": "defer_pending_human_review",
            "matte_edge_read": "defer_pending_human_review",
            "background_stability_read": "defer_pending_human_review",
            "right_rail_safe_space_read": "defer_pending_human_review",
            "long_runtime_terminal_carrier_read": "defer_pending_human_review",
        },
        "forbidden_sidecars_found": forbidden_sidecars,
        "may_select_terminal_walk_candidate_after_human_keep": False,
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
        f"- {item['label']}: seed `{item['seed']}`, cfg `{item['cfg_scale']}`, stg `{item['stg_scale']}`, `{item['prompt_variant_id']}`"
        for item in manifest["candidates"]
    )
    return f"""# Challenger Living Cover LTX 2.3 Terminal Walk Scout

Packet: `{PACKET_ID}`
Status: `{manifest['status']}`
Human disposition: `defer`

This packet records the prior chroma-key micro-motion scout as `tighten` because A/B/C read too still. The new review artifact tests a terminal narrative action: the crew is static until the final 12 seconds of the episode, then all seven astronauts begin walking away from camera toward the shuttle pad.

## Candidates

{candidate_rows}

## Timing Contract

- Full approved audio: `{APPROVED_AUDIO_DURATION_DISPLAY}` / `{APPROVED_AUDIO_DURATION_SECONDS}s`
- Terminal walk start: `{TERMINAL_WALK_START_DISPLAY}` / `{TERMINAL_WALK_START_SECONDS}s`
- Terminal walk duration: `12s`
- Future full-runtime proof: static crew until the walk start, then play the selected terminal-walk carrier once.

## Review Surfaces

- Plate/source contact sheet: `{manifest['contact_sheets']['plate_and_source']['path']}`
- Raw chroma contact sheet: `{manifest['contact_sheets']['raw_chroma_crew']['path']}`
- Alpha matte contact sheet: `{manifest['contact_sheets']['matte']['path']}`
- Composited full-frame contact sheet: `{manifest['contact_sheets']['composited_full_frame']['path']}`
- Crew crop contact sheet: `{manifest['contact_sheets']['crew_crop']['path']}`
- Still-to-walk transition contact sheet: `{manifest['contact_sheets']['still_to_walk_transition']['path']}`
- Composited walk clips: `clips/composited_full_frame/`
- Static-then-walk review clips: `clips/transition_review/`

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.
"""


def build_review(manifest: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        "| {label} | `{seed}` | `{cfg}` | `{stg}` | `{walk}` | `{review}` |".format(
            label=item["label"],
            seed=item["seed"],
            cfg=item["cfg_scale"],
            stg=item["stg_scale"],
            walk=item["composited_full_frame_clip"]["path"],
            review=item["transition_review_clip"]["path"],
        )
        for item in manifest["candidates"]
    )
    read_rows = "\n".join(f"| `{key}` | `{value}` |" for key, value in manifest["terminal_walk_reads"].items())
    return f"""# Challenger Living Cover Terminal Walk Scout Review

Packet: `{PACKET_ID}`
Gate: `rough_assembly_ltx_terminal_walk_scout_gate`
Human disposition: `defer`

## What Changed

- The chroma-key micro-motion scout is recorded as `tighten`.
- The new motion concept is not a loop: static crew until `00:21:17.131`, then a one-time 12s walk toward the shuttle pad.
- LTX runs only on the green-screen crew layer; the shuttle, pad, sky, and right-rail safe area remain static from the no-crew plate.
- Candidate clips are review-only motion-scout artifacts, not full-runtime rough/final renders.

## Candidates

| Candidate | Seed | CFG | STG | 12s Walk Composite | 14s Static-Then-Walk Review |
|---|---:|---:|---:|---|---|
{candidate_rows}

## Contact Sheets

- Plate/source: `{manifest['contact_sheets']['plate_and_source']['path']}`
- Raw chroma crew: `{manifest['contact_sheets']['raw_chroma_crew']['path']}`
- Alpha matte QA: `{manifest['contact_sheets']['matte']['path']}`
- Composited full frame: `{manifest['contact_sheets']['composited_full_frame']['path']}`
- Crew crop: `{manifest['contact_sheets']['crew_crop']['path']}`
- Still-to-walk transition: `{manifest['contact_sheets']['still_to_walk_transition']['path']}`

## Reads

| Read | Result |
|---|---:|
{read_rows}

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof with static crew until the final 12 seconds, then the selected terminal-walk carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.
"""


def main() -> None:
    for subdir in [
        "assets/background_plate",
        "assets/crew_chroma_source",
        "prompts",
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
    update_current_chroma_scout()
    input_payload = copy_inputs()
    chroma_source = Path(input_payload["chroma_source"]["path"])
    no_crew_plate = Path(input_payload["no_crew_plate"]["path"])
    static_full_frame = Path(input_payload["static_prewalk_full_frame"]["path"])
    candidate_payloads = [render_candidate(candidate, chroma_source, no_crew_plate, static_full_frame) for candidate in CANDIDATES]
    contact_sheets = make_contact_sheets(candidate_payloads, input_payload)
    manifest = build_manifest(input_payload, candidate_payloads, contact_sheets)
    manifest_path = PACKET_ROOT / "terminal_walk_manifest.json"
    readme_path = PACKET_ROOT / "README.md"
    review_path = PACKET_ROOT / "review" / "terminal_walk_review_packet.md"
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
