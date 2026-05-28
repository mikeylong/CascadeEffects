#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


CREATED_UTC = "2026-05-05T23:05:12Z"
PACKET_ID = "living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z"
PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_ltx23_chroma_key_crew_motion_scout_20260505T230512Z"
)
CURRENT_SCOUT_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_ltx23_prompt_config_micro_motion_scout_20260505T201200Z"
)
CURRENT_SCOUT_MANIFEST = CURRENT_SCOUT_ROOT / "motion_scout_manifest.json"
SOURCE_ART_PATH = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png"
)
EXPECTED_SOURCE_SHA256 = "52f94150037d5aa40633d34b29c137c59c5868e987bc5f8b7f80903f6bc2ac8a"
IMAGEGEN_NO_CREW_REFERENCE = Path(
    "/Users/mike/.codex/generated_images/019df4b0-7ec4-7a22-a583-b3d9ec843bc5/"
    "ig_0aff70366a45d29f0169fa776f732c819797ef999974dd7ce6.png"
)
IMAGEGEN_CREW_CHROMA_REFERENCE = Path(
    "/Users/mike/.codex/generated_images/019df4b0-7ec4-7a22-a583-b3d9ec843bc5/"
    "ig_0aff70366a45d29f0169fa7ae250e88197901e7ee47c8320b4.png"
)
LTX_BIN = Path("/Users/mike/AI/ltx-2-mlx/.venv/bin/ltx-2-mlx")
LTX_RUNTIME_ROOT = Path("/Users/mike/AI/ltx-2-mlx")
MODEL_REPO = "dgrauet/ltx-2.3-mlx-q8"
TEXT_ENCODER_REPO = "mlx-community/gemma-3-12b-it-4bit"
FULL_WIDTH = 1920
FULL_HEIGHT = 1080
WIDTH = 960
HEIGHT = 384
FPS = 24
FRAMES = 145
EXPECTED_RAW_FRAMES = 144
STEPS = 8
LOOP_SECONDS = 12.0
PREVIEW_SECONDS = 36.0
CREW_CROP_BOX = (96, 696, 1056, 1080)
KEY_COLOR = (0, 255, 0)
RAW_QA_FRAMES = [0, 36, 72, 108, 143]
LOOP_QA_FRAMES = [0, 72, 144, 216, 287]
SEAM_QA_FRAMES = [252, 264, 276, 284, 287, 0, 6, 12]
PREVIEW_SEAM_QA_FRAMES = [276, 287, 288, 300, 564, 575, 576, 588]
PEOPLE = [
    (143, 90, 88, 242),
    (238, 88, 92, 244),
    (348, 86, 94, 246),
    (449, 89, 88, 242),
    (622, 86, 86, 244),
    (717, 90, 86, 240),
    (827, 88, 88, 242),
]


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
        seed=112358,
        cfg_scale=0.85,
        stg_scale=0.08,
        prompt_variant_id="barely_detectable_planted_posture_settling_a",
        motion_line="barely detectable independent posture settling, nearly still",
    ),
    Candidate(
        id="variant_b",
        label="B",
        seed=223606,
        cfg_scale=1.00,
        stg_scale=0.14,
        prompt_variant_id="minimal_lifelike_independent_stance_settle_b",
        motion_line="minimal lifelike independent weight settling, tiny shoulder and head set",
    ),
    Candidate(
        id="variant_c",
        label="C",
        seed=314269,
        cfg_scale=1.15,
        stg_scale=0.20,
        prompt_variant_id="upper_subtle_planted_head_shoulder_settle_c",
        motion_line="upper subtle planted stance settling, slight independent head and shoulder settling",
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
        "bytes": path.stat().st_size,
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


def ltx_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    env.setdefault("HF_HUB_CACHE", str(Path.home() / ".cache" / "huggingface" / "hub"))
    return env


def update_current_scout() -> None:
    manifest = read_json(CURRENT_SCOUT_MANIFEST)
    manifest["human_disposition"] = "tighten"
    manifest["status"] = "tighten_chroma_key_successor_required"
    manifest["tighten_record"] = {
        "recorded_utc": CREATED_UTC,
        "reviewer_note": (
            "Crop-isolated LTX lets the model re-solve pad/background pixels and causes gesture-scale artifacts. "
            "Contact sheets show hand/arm drift, background distortion inside the crew crop, and motion that is too animated for the Living Cover carrier."
        ),
        "required_successor": "chroma_key_crew_motion_scout",
    }
    reads = manifest.setdefault("motion_scout_reads", {})
    for key in [
        "crew_loop_read",
        "motion_subtlety_read",
        "non_synchronized_motion_read",
        "no_noise_effects_read",
        "uncanny_motion_read",
    ]:
        reads[key] = "tighten"
    reads["background_stability_read"] = "tighten_crop_background_re_solve_artifacts"
    reads["hand_waving_read"] = "tighten_hand_gesture_drift_observed"
    manifest["chroma_key_successor"] = {
        "packet_path": str(PACKET_ROOT),
        "manifest_path": str(PACKET_ROOT / "motion_scout_manifest.json"),
        "review_packet_path": str(PACKET_ROOT / "review" / "motion_scout_review_packet.md"),
        "created_utc": CREATED_UTC,
        "human_disposition": "defer",
    }
    for flag in [
        "may_select_ltx_prompt_config_candidate_after_human_keep",
        "may_create_full_runtime_html_proof",
        "may_create_full_runtime_mp4_render",
        "may_advance_to_final_assembly",
        "may_advance_to_shorts_work",
        "may_advance_to_publish_readiness",
        "may_youtube_action",
    ]:
        manifest[flag] = False
    manifest["next_review_question"] = "Current crop-isolated scout is tighten. Review the chroma-key successor packet."
    write_json(CURRENT_SCOUT_MANIFEST, manifest)

    append = (
        "\n## Chroma-Key Successor\n\n"
        "Human disposition: `tighten`.\n\n"
        "Reason: the crop-isolated LTX approach lets the model re-solve launch-pad/background pixels and creates gesture-scale artifacts, including hand/arm drift. "
        "The successor separates the static shuttle plate from a keyed crew-only LTX motion layer.\n\n"
        f"Successor packet: `{PACKET_ROOT}`\n"
    )
    for md_path in [CURRENT_SCOUT_ROOT / "README.md", CURRENT_SCOUT_ROOT / "review" / "motion_scout_review_packet.md"]:
        if md_path.exists():
            text = md_path.read_text(encoding="utf-8")
            if "## Chroma-Key Successor" not in text:
                md_path.write_text(text + append, encoding="utf-8")


def build_crew_masks() -> tuple[Image.Image, Image.Image]:
    crop_mask = Image.new("L", (WIDTH, HEIGHT), 0)
    full_mask = Image.new("L", (FULL_WIDTH, FULL_HEIGHT), 0)
    crop_draw = ImageDraw.Draw(crop_mask)
    full_draw = ImageDraw.Draw(full_mask)

    # Approximate back-view human silhouettes from the kept Variant C composition.
    for cx, top, width, height in PEOPLE:
        shoulder_y = top + 58
        hip_y = top + 148
        bottom_y = top + height
        # Head / hair.
        crop_draw.ellipse((cx - 18, top, cx + 18, top + 44), fill=255)
        # Neck and torso.
        crop_draw.rounded_rectangle((cx - 30, top + 38, cx + 30, hip_y), radius=12, fill=255)
        # Arms.
        crop_draw.polygon([(cx - 34, shoulder_y), (cx - 50, hip_y - 5), (cx - 38, hip_y + 8), (cx - 21, shoulder_y + 14)], fill=255)
        crop_draw.polygon([(cx + 34, shoulder_y), (cx + 50, hip_y - 5), (cx + 38, hip_y + 8), (cx + 21, shoulder_y + 14)], fill=255)
        # Legs.
        crop_draw.polygon([(cx - 30, hip_y - 4), (cx - 6, hip_y - 3), (cx - 7, bottom_y - 10), (cx - 25, bottom_y - 7), (cx - 36, hip_y + 38)], fill=255)
        crop_draw.polygon([(cx + 6, hip_y - 3), (cx + 30, hip_y - 4), (cx + 36, hip_y + 38), (cx + 25, bottom_y - 7), (cx + 7, bottom_y - 10)], fill=255)
        # Shoes.
        crop_draw.rounded_rectangle((cx - 35, bottom_y - 13, cx - 3, bottom_y + 3), radius=5, fill=255)
        crop_draw.rounded_rectangle((cx + 3, bottom_y - 13, cx + 35, bottom_y + 3), radius=5, fill=255)

    crop_mask = crop_mask.filter(ImageFilter.GaussianBlur(radius=2))
    crop_mask = Image.eval(crop_mask, lambda px: 255 if px > 18 else 0).filter(ImageFilter.GaussianBlur(radius=0.8))
    full_mask.paste(crop_mask, (CREW_CROP_BOX[0], CREW_CROP_BOX[1]))
    return crop_mask, full_mask


def build_no_crew_plate(full_mask: Image.Image) -> dict[str, Any]:
    source = Image.open(SOURCE_ART_PATH).convert("RGB")
    removal = Image.new("L", (FULL_WIDTH, FULL_HEIGHT), 0)
    removal.paste(full_mask, (0, 0))
    draw = ImageDraw.Draw(removal)
    for cx, top, width, height in PEOPLE:
        full_cx = CREW_CROP_BOX[0] + cx
        full_top = CREW_CROP_BOX[1] + top
        full_bottom = CREW_CROP_BOX[1] + top + height
        draw.rounded_rectangle(
            (full_cx - 70, full_top - 12, full_cx + 70, full_bottom + 60),
            radius=34,
            fill=255,
        )
        draw.ellipse((full_cx - 88, full_bottom - 8, full_cx + 88, full_bottom + 72), fill=255)
    mask = removal.filter(ImageFilter.MaxFilter(39)).filter(ImageFilter.GaussianBlur(radius=14))
    hard_mask = Image.eval(mask, lambda px: 255 if px > 20 else 0)
    if IMAGEGEN_NO_CREW_REFERENCE.exists():
        fill_source = ImageOps.fit(
            Image.open(IMAGEGEN_NO_CREW_REFERENCE).convert("RGB"),
            (FULL_WIDTH, FULL_HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        method = "aligned_variant_c_plate_with_generated_no_crew_reference_fill_under_crew_mask"
    else:
        src = np.array(source).astype(np.float32)
        masked = np.array(hard_mask) > 0
        filled = src.copy()
        for y in range(FULL_HEIGHT):
            row_mask = masked[y]
            if not row_mask.any():
                continue
            good = np.where(~row_mask)[0]
            if good.size < 2:
                continue
            bad = np.where(row_mask)[0]
            for channel in range(3):
                filled[y, bad, channel] = np.interp(bad, good, src[y, good, channel])
        fill_source = Image.fromarray(np.clip(filled, 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(radius=3))
        method = "aligned_local_no_crew_plate_from_kept_variant_c_with_manual_silhouette_mask_and_row_fill"
    plate = Image.composite(fill_source, source, mask)
    output = PACKET_ROOT / "assets" / "background_plate" / "variant_c_aligned_no_crew_plate.png"
    mask_path = PACKET_ROOT / "assets" / "background_plate" / "variant_c_no_crew_plate_mask.png"
    ensure_dir(output.parent)
    plate.save(output)
    hard_mask.save(mask_path)

    reference_payload: dict[str, Any] = {}
    if IMAGEGEN_NO_CREW_REFERENCE.exists():
        reference_dest = PACKET_ROOT / "assets" / "background_plate" / "imagegen_no_crew_reference_not_composite_base.png"
        shutil.copyfile(IMAGEGEN_NO_CREW_REFERENCE, reference_dest)
        reference_payload = {
            "imagegen_reference": artifact(reference_dest),
            "note": "Generated no-crew reference is used only inside the masked crew-removal area so the final plate preserves Variant C camera geometry.",
        }
    return {
        "plate": artifact(output),
        "mask": artifact(mask_path),
        **reference_payload,
        "method": method,
    }


def build_chroma_source(crop_mask: Image.Image) -> dict[str, Any]:
    if IMAGEGEN_CREW_CHROMA_REFERENCE.exists():
        chroma = ImageOps.fit(
            Image.open(IMAGEGEN_CREW_CHROMA_REFERENCE).convert("RGB"),
            (WIDTH, HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        arr = np.array(chroma).astype(np.int16)
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]
        is_key = (g > 120) & (g > r + 38) & (g > b + 38) & (r < 120) & (b < 130)
        alpha_mask = Image.fromarray(np.where(is_key, 0, 255).astype(np.uint8), "L")
        alpha_mask = alpha_mask.filter(ImageFilter.MedianFilter(size=5)).filter(ImageFilter.GaussianBlur(radius=0.7))
        alpha = chroma.convert("RGBA")
        alpha.putalpha(alpha_mask)
        source_reference_dest = PACKET_ROOT / "assets" / "crew_chroma_source" / "imagegen_seven_astronauts_green_screen_reference.png"
        chroma_path = PACKET_ROOT / "assets" / "crew_chroma_source" / "variant_c_seven_astronauts_green_screen_source.png"
        alpha_path = PACKET_ROOT / "assets" / "crew_chroma_source" / "variant_c_seven_astronauts_alpha_reference.png"
        mask_path = PACKET_ROOT / "assets" / "crew_chroma_source" / "variant_c_seven_astronauts_source_mask.png"
        ensure_dir(chroma_path.parent)
        shutil.copyfile(IMAGEGEN_CREW_CHROMA_REFERENCE, source_reference_dest)
        chroma.save(chroma_path)
        alpha.save(alpha_path)
        alpha_mask.save(mask_path)
        return {
            "chroma_source": artifact(chroma_path),
            "alpha_reference": artifact(alpha_path),
            "source_mask": artifact(mask_path),
            "imagegen_reference": artifact(source_reference_dest),
            "key_color": "#00ff00",
            "method": "generated_clean_green_screen_seven_astronaut_plate_fit_to_variant_c_crew_zone",
        }

    source = Image.open(SOURCE_ART_PATH).convert("RGB")
    crop = source.crop(CREW_CROP_BOX)
    green = Image.new("RGB", (WIDTH, HEIGHT), KEY_COLOR)
    silhouette = crop_mask.filter(ImageFilter.MaxFilter(3))
    head_mask = Image.new("L", (WIDTH, HEIGHT), 0)
    shoe_mask = Image.new("L", (WIDTH, HEIGHT), 0)
    detail_draw = ImageDraw.Draw(head_mask)
    shoe_draw = ImageDraw.Draw(shoe_mask)
    for cx, top, width, height in PEOPLE:
        hip_y = top + 148
        bottom_y = top + height
        detail_draw.ellipse((cx - 22, top - 2, cx + 22, top + 48), fill=255)
        shoe_draw.rounded_rectangle((cx - 38, bottom_y - 16, cx - 1, bottom_y + 6), radius=5, fill=255)
        shoe_draw.rounded_rectangle((cx + 1, bottom_y - 16, cx + 38, bottom_y + 6), radius=5, fill=255)
        # Keep lower torso/leg details close to blue-suit pixels but do not admit background rail lines.
        detail_draw.rounded_rectangle((cx - 22, hip_y - 18, cx + 22, bottom_y - 20), radius=10, fill=128)
    arr = np.array(crop).astype(np.int16)
    yy = np.arange(HEIGHT)[:, None]
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    brightness = (r + g + b) / 3.0
    sil = np.array(silhouette) > 8
    heads = np.array(head_mask) > 120
    legs_detail = np.array(head_mask) > 0
    shoes = np.array(shoe_mask) > 0
    blue_suit = (b > r + 16) & (b > g + 5) & (b > 45) & (g < 145)
    head_hair_skin = heads & (brightness < 165) & ~((r > 105) & (g > 92) & (b > 80) & (np.abs(r - g) < 34))
    dark_shoes = shoes & (brightness < 125)
    dark_leg_detail = legs_detail & (brightness < 86) & (b > r + 6)
    crew_pixels = sil & (blue_suit | head_hair_skin | dark_shoes | dark_leg_detail)
    crew_mask = Image.fromarray(np.where(crew_pixels, 255, 0).astype(np.uint8), "L")
    crew_mask = crew_mask.filter(ImageFilter.MaxFilter(9))
    crew_mask = ImageChops.multiply(crew_mask, silhouette)
    crew_mask = crew_mask.filter(ImageFilter.GaussianBlur(radius=0.8))
    chroma = Image.composite(crop, green, crew_mask)
    alpha = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    alpha.paste(crop, (0, 0), crew_mask)

    chroma_path = PACKET_ROOT / "assets" / "crew_chroma_source" / "variant_c_seven_astronauts_green_screen_source.png"
    alpha_path = PACKET_ROOT / "assets" / "crew_chroma_source" / "variant_c_seven_astronauts_alpha_reference.png"
    mask_path = PACKET_ROOT / "assets" / "crew_chroma_source" / "variant_c_seven_astronauts_source_mask.png"
    ensure_dir(chroma_path.parent)
    chroma.save(chroma_path)
    alpha.save(alpha_path)
    crew_mask.save(mask_path)
    return {
        "chroma_source": artifact(chroma_path),
        "alpha_reference": artifact(alpha_path),
        "source_mask": artifact(mask_path),
        "key_color": "#00ff00",
        "method": "source_preserving_chroma_plate_from_kept_variant_c_manual_seven_person_mask",
    }


def build_prompt(candidate: Candidate) -> str:
    return (
        "Image-to-video of a green-screen crew plate only. The frame contains exactly seven astronauts in blue flight suits, "
        "seen from behind, standing on a perfectly flat pure chroma green background. "
        "The astronauts are planted with feet fixed, arms down at their sides, backs to camera, looking away toward an unseen shuttle. "
        f"Motion level: {candidate.motion_line}. "
        "Only tiny unsynchronized posture settling is allowed: subtle independent weight balance, small cloth settling, and very slight head or shoulder set. "
        "Keep every astronaut in the same place. Keep the pure green background flat and clean. "
        "No walking. No stepping. No hand waving. No arm lifting. No raised hands. No pointing. No saluting. "
        "No synchronized motion. No swaying as a group. No turning toward camera. No faces. No text. No logos. No name patches. "
        "No smoke. No fire. No atmosphere. No shimmer. No pad background. No floor. No shadows on the green screen. "
        "No extra people. No missing people. No duplicated people. No new props. No scene change. No camera movement."
    )


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
    edge = alpha_float
    edge_weight = np.clip(1.0 - np.abs(edge - 0.55) * 2.0, 0.0, 1.0)
    target_green = np.maximum(rgba_arr[:, :, 0], rgba_arr[:, :, 2]) * 0.84
    spill_weight = np.clip((1.0 - alpha_float) + edge_weight, 0.0, 1.0)
    rgba_arr[:, :, 1] = rgba_arr[:, :, 1] * (1.0 - spill_weight) + target_green * spill_weight
    keyed = Image.fromarray(np.clip(rgba_arr, 0, 255).astype(np.uint8), "RGBA")
    return keyed, alpha_img


def key_and_composite_frames(loop_chroma_paths: list[Path], no_crew_plate: Path, keyed_dir: Path, matte_dir: Path, full_dir: Path, crop_dir: Path) -> dict[str, list[Path]]:
    for path in [keyed_dir, matte_dir, full_dir, crop_dir]:
        if path.exists():
            shutil.rmtree(path)
        ensure_dir(path)
    base = Image.open(no_crew_plate).convert("RGB")
    output: dict[str, list[Path]] = {"keyed": [], "matte": [], "full": [], "crew_crop": []}
    x1, y1, _, _ = CREW_CROP_BOX
    for index, frame_path in enumerate(loop_chroma_paths):
        keyed, matte = key_chroma_frame(Image.open(frame_path))
        keyed_path = keyed_dir / f"frame_{index:04d}.png"
        matte_path = matte_dir / f"frame_{index:04d}.png"
        full_path = full_dir / f"frame_{index:04d}.png"
        crop_path = crop_dir / f"frame_{index:04d}.png"
        keyed.save(keyed_path)
        matte.save(matte_path)
        composite = base.copy().convert("RGBA")
        composite.alpha_composite(keyed, dest=(x1, y1))
        full_rgb = composite.convert("RGB")
        full_rgb.save(full_path)
        full_rgb.crop(CREW_CROP_BOX).save(crop_path)
        output["keyed"].append(keyed_path)
        output["matte"].append(matte_path)
        output["full"].append(full_path)
        output["crew_crop"].append(crop_path)
    return output


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


def copy_sequence_frame(sequence: list[Path], frame_index: int, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    shutil.copyfile(sequence[frame_index], output_path)


def motion_delta_score(frame_paths: list[Path]) -> float:
    if len(frame_paths) < 2:
        return 0.0
    first = Image.open(frame_paths[0]).convert("L")
    scores: list[float] = []
    for path in frame_paths[1:]:
        current = Image.open(path).convert("L")
        diff = ImageChops.difference(first, current)
        arr = np.array(diff, dtype=np.float32)
        scores.append(float(arr.mean()))
    return round(max(scores), 4) if scores else 0.0


def hand_raise_probe(crew_crop_paths: list[Path]) -> dict[str, Any]:
    # Broad machine heuristic only. Human review remains authoritative.
    top_bands = []
    for path in crew_crop_paths:
        img = Image.open(path).convert("RGB")
        arr = np.array(img)
        # Count blue-suit pixels in upper body zone where raised arms usually appear.
        zone = arr[70:170, :, :]
        blue = (zone[:, :, 2] > zone[:, :, 1] + 14) & (zone[:, :, 2] > zone[:, :, 0] + 20) & (zone[:, :, 2] > 55)
        top_bands.append(int(blue.sum()))
    baseline = top_bands[0] if top_bands else 0
    max_delta = max([abs(value - baseline) for value in top_bands], default=0)
    return {
        "upper_body_blue_pixel_counts": top_bands,
        "max_delta_from_first": max_delta,
        "machine_flag": "review" if max_delta > 7000 else "no_large_upper_body_change_detected",
    }


def render_candidate(candidate: Candidate, chroma_source_path: Path, no_crew_plate_path: Path) -> dict[str, Any]:
    prompt = build_prompt(candidate)
    prompt_path = PACKET_ROOT / "prompts" / "iteration_01" / f"{candidate.id}_prompt.txt"
    write_text(prompt_path, prompt + "\n")

    ltx_temp = PACKET_ROOT / "work" / "ltx_raw_with_possible_audio" / f"{candidate.id}_seed{candidate.seed}_raw_chroma_with_possible_audio.mp4"
    raw_chroma = PACKET_ROOT / "clips" / "raw_chroma_crew" / f"{candidate.id}_seed{candidate.seed}_raw_chroma_crew.mp4"
    if not ltx_temp.exists() and not raw_chroma.exists():
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
            str(FRAMES),
            "--image",
            str(chroma_source_path),
            "--steps",
            str(STEPS),
            "--cfg-scale",
            str(candidate.cfg_scale),
            "--stg-scale",
            str(candidate.stg_scale),
        ]
        run(command, cwd=LTX_RUNTIME_ROOT, env=ltx_env(), log_path=PACKET_ROOT / "logs" / f"{candidate.id}_ltx23_generate.log")
    if not raw_chroma.exists():
        strip_audio_and_normalize(ltx_temp, raw_chroma, width=WIDTH, height=HEIGHT, frames=EXPECTED_RAW_FRAMES)
    ltx_temp.unlink(missing_ok=True)

    raw_frames = extract_all_frames(raw_chroma, PACKET_ROOT / "work" / "raw_chroma_frames" / candidate.id)
    loop_chroma_frames = make_pingpong_frames(raw_frames, PACKET_ROOT / "work" / "loop_chroma_frames" / candidate.id)
    keyed_dirs = key_and_composite_frames(
        loop_chroma_frames,
        no_crew_plate_path,
        PACKET_ROOT / "work" / "loop_keyed_frames" / candidate.id,
        PACKET_ROOT / "work" / "loop_matte_frames" / candidate.id,
        PACKET_ROOT / "work" / "loop_full_frame_frames" / candidate.id,
        PACKET_ROOT / "work" / "loop_crew_crop_frames" / candidate.id,
    )

    loop_chroma = PACKET_ROOT / "clips" / "loop_chroma_crew" / f"{candidate.id}_chroma_key_crew_loop_12s.mp4"
    loop_keyed = PACKET_ROOT / "clips" / "loop_keyed_alpha_preview" / f"{candidate.id}_keyed_alpha_preview_loop_12s.mp4"
    loop_composite = PACKET_ROOT / "clips" / "loop_composited_full_frame" / f"{candidate.id}_chroma_key_composited_full_frame_loop_12s.mp4"
    preview = PACKET_ROOT / "clips" / "loop_preview_3x" / f"{candidate.id}_chroma_key_composited_full_frame_3x_preview.mp4"
    encode_frames(PACKET_ROOT / "work" / "loop_chroma_frames" / candidate.id, loop_chroma, width=WIDTH, height=HEIGHT)
    encode_frames(PACKET_ROOT / "work" / "loop_keyed_frames" / candidate.id, loop_keyed, width=WIDTH, height=HEIGHT)
    encode_frames(PACKET_ROOT / "work" / "loop_full_frame_frames" / candidate.id, loop_composite, width=FULL_WIDTH, height=FULL_HEIGHT)
    make_three_loop_preview(loop_composite, preview, width=FULL_WIDTH, height=FULL_HEIGHT)

    qa: dict[str, list[Path]] = {
        "raw_chroma_crew": [],
        "matte": [],
        "composited_full_frame": [],
        "crew_crop": [],
        "loop_seam": [],
        "preview_3loop_seam": [],
    }
    for frame_index in RAW_QA_FRAMES:
        output = PACKET_ROOT / "qa" / "frames" / "raw_chroma_crew" / candidate.id / f"{candidate.id}_raw_chroma_{frame_index:03d}.png"
        extract_frame(raw_chroma, frame_index, output)
        qa["raw_chroma_crew"].append(output)
    for frame_index in LOOP_QA_FRAMES:
        matte_out = PACKET_ROOT / "qa" / "frames" / "matte" / candidate.id / f"{candidate.id}_matte_{frame_index:03d}.png"
        full_out = PACKET_ROOT / "qa" / "frames" / "composited_full_frame" / candidate.id / f"{candidate.id}_full_{frame_index:03d}.png"
        crew_out = PACKET_ROOT / "qa" / "frames" / "crew_crop" / candidate.id / f"{candidate.id}_crew_crop_{frame_index:03d}.png"
        copy_sequence_frame(keyed_dirs["matte"], frame_index, matte_out)
        copy_sequence_frame(keyed_dirs["full"], frame_index, full_out)
        copy_sequence_frame(keyed_dirs["crew_crop"], frame_index, crew_out)
        qa["matte"].append(matte_out)
        qa["composited_full_frame"].append(full_out)
        qa["crew_crop"].append(crew_out)
    for index, frame_index in enumerate(SEAM_QA_FRAMES):
        output = PACKET_ROOT / "qa" / "frames" / "loop_seam" / candidate.id / f"{candidate.id}_seam_{index:02d}_frame_{frame_index:03d}.png"
        copy_sequence_frame(keyed_dirs["crew_crop"], frame_index, output)
        qa["loop_seam"].append(output)
    for frame_index in PREVIEW_SEAM_QA_FRAMES:
        output = PACKET_ROOT / "qa" / "frames" / "preview_3loop_seam" / candidate.id / f"{candidate.id}_preview_{frame_index:03d}.png"
        full_tmp = PACKET_ROOT / "work" / "preview_extract" / candidate.id / f"{candidate.id}_preview_full_{frame_index:03d}.png"
        extract_frame(preview, frame_index, full_tmp)
        ensure_dir(output.parent)
        Image.open(full_tmp).convert("RGB").crop(CREW_CROP_BOX).save(output)
        qa["preview_3loop_seam"].append(output)

    probe = hand_raise_probe(qa["crew_crop"])
    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "iteration": "iteration_01",
        "seed": candidate.seed,
        "prompt_variant_id": candidate.prompt_variant_id,
        "cfg_scale": candidate.cfg_scale,
        "stg_scale": candidate.stg_scale,
        "steps": STEPS,
        "frames_requested": FRAMES,
        "prompt_text": prompt,
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256(prompt_path),
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
        "raw_chroma_crew_clip": video_summary(raw_chroma),
        "loop_chroma_crew_clip": video_summary(loop_chroma),
        "loop_keyed_alpha_preview_clip": video_summary(loop_keyed),
        "loop_composited_full_frame_clip": video_summary(loop_composite),
        "preview_3loop_clip": video_summary(preview),
        "qa_frames": {key: [artifact(path) for path in paths] for key, paths in qa.items()},
        "machine_motion_probe": {
            "crew_crop_motion_delta_score": motion_delta_score(qa["crew_crop"]),
            "hand_raise_probe": probe,
            "note": "Machine probes are coarse screening only; human review is authoritative for hand waving, synchronized motion, subtlety, and uncanny motion.",
        },
        "disposition": "defer",
        "selected_for_full_runtime_html_proof": False,
        "selected_for_full_runtime_html_proof_status": "pending_human_review",
    }
    write_json(PACKET_ROOT / "candidates" / f"{candidate.id}.json", payload)
    return payload


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


def build_no_crew_contact_sheet(no_crew_payload: dict[str, Any], chroma_payload: dict[str, Any]) -> Path:
    output = PACKET_ROOT / "qa" / "contact_sheets" / "chroma_key_no_crew_plate_and_source_contact_sheet.jpg"
    rows = [
        ("Aligned no-crew plate", [Path(no_crew_payload["plate"]["path"])]),
        ("Crew chroma source", [Path(chroma_payload["chroma_source"]["path"])]),
    ]
    if "imagegen_reference" in no_crew_payload:
        rows.append(("Generated no-crew reference, not composite base", [Path(no_crew_payload["imagegen_reference"]["path"])]))
    make_contact_sheet(rows=rows, output_path=output, title="Chroma-Key Scout - Plate and Source", thumb_w=426, thumb_h=240)
    return output


def make_contact_sheets(candidate_payloads: list[dict[str, Any]], no_crew_payload: dict[str, Any], chroma_payload: dict[str, Any]) -> dict[str, Path]:
    contact_dir = PACKET_ROOT / "qa" / "contact_sheets"
    rows: dict[str, list[tuple[str, list[Path]]]] = {
        "raw_chroma_crew": [],
        "matte": [],
        "composited_full_frame": [],
        "crew_crop": [],
        "loop_seam": [],
        "preview_3loop_seam": [],
    }
    for item in candidate_payloads:
        label = f"{item['label']} cfg {item['cfg_scale']} stg {item['stg_scale']} - {item['prompt_variant_id']}"
        for key in rows:
            rows[key].append((label, [Path(frame["path"]) for frame in item["qa_frames"][key]]))
    outputs = {
        "no_crew_plate_and_source": build_no_crew_contact_sheet(no_crew_payload, chroma_payload),
        "raw_chroma_crew": contact_dir / "chroma_key_raw_chroma_crew_contact_sheet.jpg",
        "matte": contact_dir / "chroma_key_alpha_matte_contact_sheet.jpg",
        "composited_full_frame": contact_dir / "chroma_key_composited_full_frame_contact_sheet.jpg",
        "crew_crop": contact_dir / "chroma_key_crew_crop_contact_sheet.jpg",
        "loop_seam": contact_dir / "chroma_key_loop_seam_contact_sheet.jpg",
        "preview_3loop_seam": contact_dir / "chroma_key_3loop_seam_contact_sheet.jpg",
    }
    make_contact_sheet(rows=rows["raw_chroma_crew"], output_path=outputs["raw_chroma_crew"], title="Chroma-Key Scout - Raw Green-Screen Crew", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["matte"], output_path=outputs["matte"], title="Chroma-Key Scout - Alpha Matte QA", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["composited_full_frame"], output_path=outputs["composited_full_frame"], title="Chroma-Key Scout - Composited Full Frame", thumb_w=256, thumb_h=144)
    make_contact_sheet(rows=rows["crew_crop"], output_path=outputs["crew_crop"], title="Chroma-Key Scout - Crew Crop Motion States", thumb_w=256, thumb_h=102)
    make_contact_sheet(rows=rows["loop_seam"], output_path=outputs["loop_seam"], title="Chroma-Key Scout - End/Start Seam Crop", thumb_w=205, thumb_h=82)
    make_contact_sheet(rows=rows["preview_3loop_seam"], output_path=outputs["preview_3loop_seam"], title="Chroma-Key Scout - 3x Preview Seam Crop", thumb_w=205, thumb_h=82)
    return outputs


def build_manifest(
    *,
    no_crew_payload: dict[str, Any],
    chroma_payload: dict[str, Any],
    candidate_payloads: list[dict[str, Any]],
    contact_sheets: dict[str, Path],
) -> dict[str, Any]:
    forbidden_sidecars = [
        str(path)
        for path in PACKET_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".wav", ".mp3", ".srt", ".vtt", ".html", ".mov"}
    ]
    all_no_audio = all(
        not item["raw_chroma_crew_clip"]["has_audio"]
        and not item["loop_chroma_crew_clip"]["has_audio"]
        and not item["loop_keyed_alpha_preview_clip"]["has_audio"]
        and not item["loop_composited_full_frame_clip"]["has_audio"]
        and not item["preview_3loop_clip"]["has_audio"]
        for item in candidate_payloads
    )
    loop_duration_ok = all(11.9 <= float(item["loop_composited_full_frame_clip"]["duration_seconds"]) <= 12.1 for item in candidate_payloads)
    preview_duration_ok = all(35.8 <= float(item["preview_3loop_clip"]["duration_seconds"]) <= 36.2 for item in candidate_payloads)
    return {
        "packet_id": PACKET_ID,
        "gate": "rough_assembly_ltx_chroma_key_crew_motion_scout_gate",
        "status": "review_ready_pending_human_chroma_key_crew_motion_keep",
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
        "created_from_disposition": "tighten_after_crop_isolated_ltx_prompt_config_micro_motion_scout",
        "tightened_source_packet_path": str(CURRENT_SCOUT_ROOT),
        "tightened_source_manifest_path": str(CURRENT_SCOUT_MANIFEST),
        "review_only": True,
        "ltx_chroma_key_scout_only": True,
        "full_runtime_html_proof_created": False,
        "full_runtime_mp4_created": False,
        "final_assembly_created": False,
        "profileId": "cascade-ink-lit-photoreal-v1",
        "source_visual": {
            "carrier": "kept_variant_c_source_art_split_into_static_no_crew_plate_plus_keyed_crew_layer",
            "source_art_path": str(SOURCE_ART_PATH),
            "source_art_sha256": sha256(SOURCE_ART_PATH),
            "expected_source_art_sha256": EXPECTED_SOURCE_SHA256,
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "source_art_dimensions": {"width": FULL_WIDTH, "height": FULL_HEIGHT, "aspect_ratio": "16:9"},
            "crew_crop_box": {"x": CREW_CROP_BOX[0], "y": CREW_CROP_BOX[1], "width": WIDTH, "height": HEIGHT},
            "no_crew_plate": no_crew_payload,
            "crew_chroma_source": chroma_payload,
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
            "motion_target": "minimal_unsynchronized_lifelike_planted_crew_motion_no_hand_waving_no_noise",
            "composite_policy": "ltx_generated_chroma_crew_keyed_and_composited_over_static_aligned_no_crew_plate",
            "internal_iteration_cap": 3,
            "iterations_attempted": 1,
            "presented_iteration": "iteration_01",
        },
        "candidates": candidate_payloads,
        "contact_sheets": {key: artifact(path) for key, path in contact_sheets.items()},
        "motion_scout_reads": {
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "ltx_runtime_read": "pass" if LTX_BIN.exists() else "reject_missing_runtime",
            "candidate_count_read": "pass_three_candidates" if len(candidate_payloads) == 3 else "reject_missing_candidates",
            "raw_chroma_audio_read": "pass_no_audio" if all_no_audio else "reject_audio_present",
            "loop_duration_read": "pass_12s" if loop_duration_ok else "tighten_duration_not_12s",
            "preview_3loop_duration_read": "pass_36s" if preview_duration_ok else "tighten_duration_not_36s",
            "contact_sheet_read": "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet",
            "forbidden_media_copy_read": "pass_no_audio_caption_transcript_html_mov_sidecars" if not forbidden_sidecars else "reject_forbidden_sidecar_found",
            "full_runtime_html_proof_read": "pass_not_created",
            "full_runtime_mp4_read": "pass_not_created",
            "final_assembly_read": "pass_not_created",
            "chroma_key_read": "defer_pending_human_review",
            "no_crew_plate_read": "defer_pending_human_review",
            "crew_loop_read": "defer_pending_human_review",
            "loop_seam_read": "defer_pending_human_review",
            "hand_waving_read": "defer_pending_human_review",
            "non_synchronized_motion_read": "defer_pending_human_review",
            "motion_subtlety_read": "defer_pending_human_review",
            "motion_detectability_read": "defer_pending_human_review",
            "crew_count_read": "defer_pending_human_review",
            "matte_edge_read": "defer_pending_human_review",
            "background_stability_read": "defer_pending_human_review",
            "identity_logo_text_read": "defer_pending_human_review",
            "uncanny_motion_read": "defer_pending_human_review",
            "right_rail_safe_space_read": "defer_pending_human_review",
            "long_runtime_carrier_read": "defer_pending_human_review",
        },
        "forbidden_sidecars_found": forbidden_sidecars,
        "may_select_chroma_key_candidate_after_human_keep": False,
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
    return f"""# Challenger Living Cover LTX 2.3 Chroma-Key Crew Motion Scout

Packet: `{PACKET_ID}`
Status: `{manifest['status']}`
Human disposition: `defer`

This packet records the prior crop-isolated LTX scout as `tighten` and tests a split-layer approach: static aligned no-crew shuttle plate plus a green-screen LTX crew-only motion layer.

## Candidates

{candidate_rows}

## Review Surfaces

- Plate/source contact sheet: `{manifest['contact_sheets']['no_crew_plate_and_source']['path']}`
- Raw chroma crew contact sheet: `{manifest['contact_sheets']['raw_chroma_crew']['path']}`
- Alpha matte contact sheet: `{manifest['contact_sheets']['matte']['path']}`
- Composited full-frame contact sheet: `{manifest['contact_sheets']['composited_full_frame']['path']}`
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
    return f"""# Challenger Living Cover LTX 2.3 Chroma-Key Crew Motion Scout Review

Packet: `{PACKET_ID}`
Gate: `rough_assembly_ltx_chroma_key_crew_motion_scout_gate`
Human disposition: `defer`

## What Changed

- The crop-isolated LTX prompt/config scout is recorded as `tighten`.
- The shuttle/pad scene is now a static aligned no-crew plate.
- LTX runs only on a green-screen crew layer, then the crew is keyed and composited over the plate.
- The loop is built from a 6s generated half-cycle plus reverse playback.

## Candidates

| Candidate | Seed | CFG | STG | 12s Composited Loop | 36s 3-Loop Preview |
|---|---:|---:|---:|---|---|
{candidate_rows}

## Contact Sheets

- Plate/source: `{manifest['contact_sheets']['no_crew_plate_and_source']['path']}`
- Raw chroma crew: `{manifest['contact_sheets']['raw_chroma_crew']['path']}`
- Alpha matte QA: `{manifest['contact_sheets']['matte']['path']}`
- Composited full frame: `{manifest['contact_sheets']['composited_full_frame']['path']}`
- Crew crop: `{manifest['contact_sheets']['crew_crop']['path']}`
- Loop seam: `{manifest['contact_sheets']['loop_seam']['path']}`
- 3-loop seam: `{manifest['contact_sheets']['preview_3loop_seam']['path']}`

## Reads

| Read | Result |
|---|---:|
{read_rows}

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected chroma-key crew carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.
"""


def main() -> None:
    for subdir in [
        "assets/background_plate",
        "assets/crew_chroma_source",
        "prompts/iteration_01",
        "candidates",
        "clips/raw_chroma_crew",
        "clips/loop_chroma_crew",
        "clips/loop_keyed_alpha_preview",
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

    update_current_scout()
    crop_mask, full_mask = build_crew_masks()
    no_crew_payload = build_no_crew_plate(full_mask)
    chroma_payload = build_chroma_source(crop_mask)
    chroma_source_path = Path(chroma_payload["chroma_source"]["path"])
    no_crew_plate_path = Path(no_crew_payload["plate"]["path"])
    candidate_payloads = [render_candidate(candidate, chroma_source_path, no_crew_plate_path) for candidate in CANDIDATES]
    contact_sheets = make_contact_sheets(candidate_payloads, no_crew_payload, chroma_payload)

    manifest = build_manifest(
        no_crew_payload=no_crew_payload,
        chroma_payload=chroma_payload,
        candidate_payloads=candidate_payloads,
        contact_sheets=contact_sheets,
    )
    manifest_path = PACKET_ROOT / "motion_scout_manifest.json"
    readme_path = PACKET_ROOT / "README.md"
    review_path = PACKET_ROOT / "review" / "motion_scout_review_packet.md"
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
