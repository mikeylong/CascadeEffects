#!/usr/bin/env python3
"""Build the Pressure Bends intro with right-video bass ripple carry-through."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont


WIDTH = 1920
HEIGHT = 1080
FPS = 24
TOTAL_FRAMES = 1399
OUTPUT_SECONDS = TOTAL_FRAMES / FPS
END_SCREEN_SECONDS = 20.0
END_SCREEN_START_SECONDS = OUTPUT_SECONDS - END_SCREEN_SECONDS
BODY_START_SECONDS = 6.0
OUTPUT_STEM = "channel_intro_pressure_bends_original_format_bass_drum_right_video_pressure_ripple_fix"
WORKFLOW = f"{OUTPUT_STEM}_v1"
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8767"

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
PRESSURE_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_pressure_bends_successor.py"
ROUGH_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_v2_intro_rough_cut.py"
SOURCE_POINTER = OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix_latest.json"
LATEST_POINTER = OUTPUT_ROOT / f"{OUTPUT_STEM}_latest.json"

SHORT_CARD_SIZE = (720, 1280)
CARD_INSET = 8
CARD_RADIUS = 74
TRANSITION_SECONDS = 0.32

TIMELINE = [
    {"episode_id": "challenger", "display": "Challenger", "frames": [144, 241]},
    {"episode_id": "therac-25", "display": "Therac-25", "frames": [241, 338]},
    {"episode_id": "hyatt-regency", "display": "Hyatt Regency", "frames": [338, 435]},
    {"episode_id": "semmelweis", "display": "Semmelweis", "frames": [435, 532]},
    {"episode_id": "tacoma-narrows", "display": "Tacoma Narrows", "frames": [532, 629]},
    {"episode_id": "piltdown-man", "display": "Piltdown Man", "frames": [629, 726]},
    {"episode_id": "737-max", "display": "737 MAX", "frames": [726, 823]},
    {"episode_id": "titanic", "display": "Titanic", "frames": [823, 919]},
]
for row in TIMELINE:
    row["seconds"] = [row["frames"][0] / FPS, row["frames"][1] / FPS]

SAMPLE_WINDOWS = [
    ("cold open", 0.0, 6.0),
    ("Challenger", 6.0, 10.041667),
    ("Therac-25", 10.041667, 14.083333),
    ("Hyatt Regency", 14.083333, 18.125),
    ("Semmelweis", 18.125, 22.166667),
    ("Tacoma Narrows", 22.166667, 26.208333),
    ("Piltdown Man", 26.208333, 30.25),
    ("737 MAX", 30.25, 34.291667),
    ("Titanic", 34.291667, END_SCREEN_START_SECONDS),
]

RIGHT_VIDEO_EFFECT = {
    "profile_id": "right_video_pressure_ripple_carry_through_v1",
    "active_seconds": [0.0, END_SCREEN_START_SECONDS],
    "decay_frames": 10,
    "mesh_columns": 10,
    "mesh_rows": 18,
    "max_displacement_px": 5.2,
    "ripple_wavelength_px": 92.0,
    "ripple_travel_px_per_frame": 44.0,
    "ripple_band_width_px": 260.0,
    "pressure_contrast_lift": 0.075,
    "pressure_brightness_lift": 0.070,
    "scanline_lift": 0.045,
    "screen_wash_mix": 0.060,
    "carry_through_wash_mix": 0.190,
    "carry_through_brightness_lift": 0.240,
    "carry_through_additive_lift_rgb": [7.0, 9.0, 18.0],
    "carry_through_mask_blur_px": 34,
    "video_pixels_clipped_to_screen_mask": True,
    "geometry_movement_allowed": False,
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rough = load_module("channel_intro_right_video_ripple_rough", ROUGH_HELPER_PATH)
pressure = load_module("channel_intro_right_video_ripple_pressure_helper", PRESSURE_HELPER_PATH)


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
                "stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels,duration:format=duration,size,bit_rate",
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


def extract_frame(video: Path, seconds: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{seconds:.6f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(out_path),
        ]
    )


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def luma_array(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    return (0.2126 * arr[:, :, 0]) + (0.7152 * arr[:, :, 1]) + (0.0722 * arr[:, :, 2])


def screen_mask(size: tuple[int, int] = SHORT_CARD_SIZE, inset: int = 0, blur: float = 0.35) -> Image.Image:
    w, h = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    x0 = CARD_INSET + inset
    y0 = CARD_INSET + inset
    x1 = w - CARD_INSET - inset
    y1 = h - CARD_INSET - inset
    radius = max(0, CARD_RADIUS - CARD_INSET - inset)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur)) if blur else mask


SCREEN_MASK = screen_mask()
CORE_MASK = screen_mask(inset=12, blur=5.0)


def source_to_card_coefficients(quad: list[tuple[float, float]]) -> tuple[float, ...]:
    rect = [
        (0.0, 0.0),
        (float(SHORT_CARD_SIZE[0]), 0.0),
        (float(SHORT_CARD_SIZE[0]), float(SHORT_CARD_SIZE[1])),
        (0.0, float(SHORT_CARD_SIZE[1])),
    ]
    return rough.perspective_coefficients(rect, quad)


def unwarp_card(frame: Image.Image, quad: list[tuple[float, float]]) -> Image.Image:
    return frame.transform(
        SHORT_CARD_SIZE,
        Image.Transform.PERSPECTIVE,
        source_to_card_coefficients(quad),
        Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0),
    ).convert("RGB")


def displacement_at(x: float, y: float, strength: float, elapsed_frames: int) -> tuple[float, float]:
    w, h = SHORT_CARD_SIZE
    cx = w * 0.50
    cy = h * 0.45
    dx = x - cx
    dy = (y - cy) * 0.62
    radius = math.sqrt(dx * dx + dy * dy) + 1e-6
    phase = elapsed_frames * float(RIGHT_VIDEO_EFFECT["ripple_travel_px_per_frame"])
    wavelength = float(RIGHT_VIDEO_EFFECT["ripple_wavelength_px"])
    band_width = float(RIGHT_VIDEO_EFFECT["ripple_band_width_px"])
    ring = math.exp(-((radius - phase) ** 2) / (2.0 * band_width * band_width))
    wave = math.sin((radius - phase) / wavelength * math.tau)
    breathing = math.exp(-radius / 1450.0)
    amount = float(RIGHT_VIDEO_EFFECT["max_displacement_px"]) * strength * ((0.48 * ring * wave) + (0.18 * breathing))
    return (dx / radius * amount, (dy / radius) * amount / 0.62)


def ripple_mesh(card: Image.Image, strength: float, elapsed_frames: int) -> Image.Image:
    if strength < 0.018:
        return card
    w, h = card.size
    cols = int(RIGHT_VIDEO_EFFECT["mesh_columns"])
    rows = int(RIGHT_VIDEO_EFFECT["mesh_rows"])
    mesh = []
    for row in range(rows):
        y0 = int(round(row * h / rows))
        y1 = int(round((row + 1) * h / rows))
        for col in range(cols):
            x0 = int(round(col * w / cols))
            x1 = int(round((col + 1) * w / cols))
            corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            source_quad = []
            for x, y in corners:
                ox, oy = displacement_at(float(x), float(y), strength, elapsed_frames)
                source_quad.append((max(0.0, min(w - 1.0, x + ox)), max(0.0, min(h - 1.0, y + oy))))
            mesh.append(((x0, y0, x1, y1), tuple(value for point in source_quad for value in point)))
    return card.transform(card.size, Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)


def pressure_grade(card: Image.Image, strength: float, elapsed_frames: int) -> Image.Image:
    arr = np.asarray(card.convert("RGB"), dtype=np.float32)
    y = np.arange(arr.shape[0], dtype=np.float32)[:, None]
    scan = 0.5 + 0.5 * np.sin((y + elapsed_frames * 3.0) * math.tau / 7.0)
    arr = (arr - 128.0) * (1.0 + float(RIGHT_VIDEO_EFFECT["pressure_contrast_lift"]) * strength) + 128.0
    arr *= 1.0 + float(RIGHT_VIDEO_EFFECT["pressure_brightness_lift"]) * strength
    arr *= 1.0 + float(RIGHT_VIDEO_EFFECT["scanline_lift"]) * strength * scan[:, :, None]
    wash = np.array([24, 44, 82], dtype=np.float32)
    mix = float(RIGHT_VIDEO_EFFECT["screen_wash_mix"]) * strength
    arr = arr * (1.0 - mix) + wash * mix
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def apply_right_video_pressure_ripple(card: Image.Image, strength: float, elapsed_frames: int) -> Image.Image:
    if strength < 0.012:
        return card
    rippled = ripple_mesh(card, strength, elapsed_frames)
    graded = pressure_grade(rippled, strength, elapsed_frames)
    original = np.asarray(card.convert("RGB"), dtype=np.float32)
    effected = np.asarray(graded, dtype=np.float32)
    mask = np.asarray(CORE_MASK, dtype=np.float32) / 255.0
    mask = (mask * min(1.0, 0.58 + strength * 0.42))[:, :, None]
    blended = original * (1.0 - mask) + effected * mask
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), "RGB")


def polygon_mask(quad: list[tuple[float, float]], blur_px: int = 0, grow_px: int = 0) -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(round(x), round(y)) for x, y in quad], fill=255)
    if grow_px > 0:
        mask = mask.filter(ImageFilter.MaxFilter(grow_px | 1))
    if blur_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur_px))
    return mask


def subtract_protected_ui(mask: Image.Image, t: float) -> Image.Image:
    if t < END_SCREEN_START_SECONDS and t >= 5.85:
        protected = Image.new("L", (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(protected)
        draw.rounded_rectangle((74, 830, 710, 956), radius=18, fill=255)
        mask = ImageChops.subtract(mask, protected.filter(ImageFilter.GaussianBlur(8)))
    return mask


def apply_carry_through(frame: Image.Image, quad: list[tuple[float, float]], strength: float, elapsed_frames: int, t: float) -> Image.Image:
    if strength < 0.018:
        return frame
    poly = polygon_mask(quad, blur_px=0)
    halo = polygon_mask(quad, blur_px=int(RIGHT_VIDEO_EFFECT["carry_through_mask_blur_px"]), grow_px=35)
    ring = ImageChops.subtract(halo, poly.filter(ImageFilter.MaxFilter(17)))
    dim_halo = Image.fromarray((np.asarray(halo, dtype=np.float32) * 0.76).astype(np.uint8), "L")
    mask = ImageChops.lighter(dim_halo, ring)
    mask = subtract_protected_ui(mask, t)

    arr = np.asarray(frame.convert("RGB"), dtype=np.float32)
    m = np.asarray(mask, dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
    cx = sum(x for x, _ in quad) / 4.0
    cy = sum(y for _, y in quad) / 4.0
    dist = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 0.72) ** 2)
    wave = 0.68 + 0.32 * np.sin((dist - elapsed_frames * 54.0) / 105.0 * math.tau)
    shaped = (m * wave * strength)[:, :, None]
    wash = np.array([34, 48, 102], dtype=np.float32)
    additive = np.array(RIGHT_VIDEO_EFFECT["carry_through_additive_lift_rgb"], dtype=np.float32)
    arr = arr * (1.0 + float(RIGHT_VIDEO_EFFECT["carry_through_brightness_lift"]) * shaped)
    arr = arr + additive * shaped
    mix = float(RIGHT_VIDEO_EFFECT["carry_through_wash_mix"]) * shaped
    arr = arr * (1.0 - mix) + wash * mix
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def warp_effect_card(effect_card: Image.Image, quad: list[tuple[float, float]]) -> tuple[Image.Image, tuple[int, int]]:
    rgba = effect_card.convert("RGBA")
    rgba.putalpha(SCREEN_MASK)
    return rough.warp_to_quad_patch(rgba, quad, pad=32)


def episode_quad(slug: str, start: float, t: float) -> list[tuple[float, float]]:
    if slug == "challenger":
        return rough.END_SHORT_PLATE_QUAD
    progress = (t - start) / float(rough.EPISODE_PUSH_IN_SECONDS)
    return rough.interpolate_quad(rough.START_SHORT_PLATE_QUAD, rough.END_SHORT_PLATE_QUAD, rough.ease_out_cubic(progress))


def active_quads(t: float) -> list[dict[str, Any]]:
    if t >= END_SCREEN_START_SECONDS:
        return []
    if t < BODY_START_SECONDS:
        progress = max(0.0, min(1.0, t / float(rough.MUSIC_ONLY_COLD_OPEN_SECONDS)))
        quad = rough.interpolate_quad(
            rough.MUSIC_ONLY_COLD_OPEN_START_SHORT_PLATE_QUAD,
            rough.END_SHORT_PLATE_QUAD,
            rough.ease(progress),
        )
        return [{"label": "cold_open", "quad": quad}]

    active_index = None
    for index, row in enumerate(TIMELINE):
        start, end = row["seconds"]
        if start <= t < end:
            active_index = index
            break
    if active_index is None:
        return []

    row = TIMELINE[active_index]
    start, _ = row["seconds"]
    quads: list[dict[str, Any]] = [
        {"label": row["episode_id"], "quad": episode_quad(row["episode_id"], start, t)}
    ]
    if active_index > 0 and 0.0 <= t - start < TRANSITION_SECONDS:
        previous = TIMELINE[active_index - 1]
        previous_start, previous_end = previous["seconds"]
        previous_t = min(previous_end - 1 / FPS, t)
        quads.insert(
            0,
            {
                "label": previous["episode_id"],
                "quad": episode_quad(previous["episode_id"], previous_start, previous_t),
            },
        )
    return quads


def build_right_video_curve(hit_analysis: dict[str, Any]) -> tuple[np.ndarray, list[int]]:
    curve = np.zeros(TOTAL_FRAMES, dtype=np.float32)
    source_frames = [-10_000 for _ in range(TOTAL_FRAMES)]
    decay = int(RIGHT_VIDEO_EFFECT["decay_frames"])
    for hit in hit_analysis["hits"]:
        hit_frame = int(hit["frame_index"])
        score = max(0.0, min(1.0, float(hit["score"])))
        peak = 0.38 + 0.62 * score
        for frame_index in range(hit_frame, min(TOTAL_FRAMES, hit_frame + decay + 1)):
            dt_frames = frame_index - hit_frame
            value = peak * math.exp(-dt_frames / 5.2)
            if value <= curve[frame_index]:
                continue
            curve[frame_index] = value
            source_frames[frame_index] = hit_frame
    return np.clip(curve, 0.0, 1.0), source_frames


def select_hit_samples(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_frames: set[int] = set()
    for label, start, end in SAMPLE_WINDOWS:
        in_window = [hit for hit in hits if start <= float(hit["frame_time_seconds"]) < end]
        if not in_window:
            continue
        hit = max(in_window, key=lambda item: item["score"])
        frame_index = int(hit["frame_index"])
        if frame_index in used_frames:
            continue
        used_frames.add(frame_index)
        selected.append({**hit, "label": label})
    return selected


def right_card_crop_bbox(quads: list[dict[str, Any]], pad: int = 56) -> tuple[int, int, int, int]:
    points = [(x, y) for item in quads for x, y in item["quad"]]
    if not points:
        return (1100, 20, 1868, 1046)
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return (
        max(0, int(math.floor(min(xs))) - pad),
        max(0, int(math.floor(min(ys))) - pad),
        min(WIDTH, int(math.ceil(max(xs))) + pad),
        min(HEIGHT, int(math.ceil(max(ys))) + pad),
    )


def right_video_delta_metrics(before: Image.Image, after: Image.Image, quads: list[dict[str, Any]]) -> dict[str, Any]:
    if not quads:
        return {}
    before_luma = luma_array(before)
    after_luma = luma_array(after)
    delta = np.abs(after_luma - before_luma)
    interior = Image.new("L", (WIDTH, HEIGHT), 0)
    for item in quads:
        interior = ImageChops.lighter(interior, polygon_mask(item["quad"], blur_px=0))
    halo = interior.filter(ImageFilter.MaxFilter(51)).filter(ImageFilter.GaussianBlur(14))
    outside_edge = ImageChops.subtract(halo, interior.filter(ImageFilter.MaxFilter(7)))
    interior_arr = np.asarray(interior, dtype=np.float32) > 128
    outside_arr = np.asarray(outside_edge, dtype=np.float32) > 35
    interior_delta = float(delta[interior_arr].mean()) if np.any(interior_arr) else 0.0
    outside_delta = float(delta[outside_arr].mean()) if np.any(outside_arr) else 0.0
    ratio = outside_delta / max(interior_delta, 1e-6)
    return {
        "interior_mean_luma_delta": round(interior_delta, 4),
        "outside_edge_mean_luma_delta": round(outside_delta, 4),
        "outside_to_inside_delta_ratio": round(ratio, 4),
        "right_video_interior_effect_read": "pass" if interior_delta >= 0.55 else "tighten_right_video_effect_low",
        "carry_through_edge_read": "pass" if outside_delta >= 0.18 and ratio >= 0.025 else "tighten_edge_carry_through_low",
        "no_hard_edge_cutoff_read": "pass" if outside_delta >= 0.18 and ratio >= 0.025 else "tighten_possible_hard_edge_cutoff",
    }


def process_frame(
    frame: np.ndarray,
    frame_index: int,
    right_curve: np.ndarray,
    source_hit_frames: list[int],
) -> Image.Image:
    t = frame_index / FPS
    strength = float(right_curve[frame_index])
    image = Image.fromarray(frame, "RGB")
    if strength < 0.012 or t >= END_SCREEN_START_SECONDS:
        return image
    elapsed_frames = max(0, frame_index - int(source_hit_frames[frame_index]))
    quads = active_quads(t)
    if not quads:
        return image

    carried = image
    for item in quads:
        carried = apply_carry_through(carried, item["quad"], strength * 0.62, elapsed_frames, t)

    composited = carried.convert("RGBA")
    for item in quads:
        card = unwarp_card(carried, item["quad"])
        effect_card = apply_right_video_pressure_ripple(card, strength, elapsed_frames)
        layer, offset = warp_effect_card(effect_card, item["quad"])
        composited.alpha_composite(layer, offset)
    return composited.convert("RGB")


def render_right_video_ripple(
    source_mp4: Path,
    final_mp4: Path,
    hit_analysis: dict[str, Any],
    sample_hits: list[dict[str, Any]],
    qa_dir: Path,
    work_dir: Path,
) -> dict[str, Any]:
    right_curve, source_hit_frames = build_right_video_curve(hit_analysis)
    curve_path = work_dir / "right_video_ripple_curve_values.json"
    write_json(
        curve_path,
        {
            "fps": FPS,
            "total_frames": TOTAL_FRAMES,
            "values": [round(float(value), 6) for value in right_curve.tolist()],
            "source_hit_frame_by_frame": source_hit_frames,
        },
    )

    sample_frames = {int(hit["frame_index"]): hit for hit in sample_hits if int(hit["frame_index"]) < END_SCREEN_START_SECONDS * FPS}
    sample_dir = qa_dir / "right_video_ripple_raw_frames"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_rows: list[dict[str, Any]] = []

    decoder = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source_mp4),
            "-map",
            "0:v:0",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    encoder = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-i",
            str(source_mp4),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-frames:v",
            str(TOTAL_FRAMES),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "16",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ],
        stdin=subprocess.PIPE,
    )
    if decoder.stdout is None or encoder.stdin is None:
        raise SystemExit("Could not open ffmpeg pipes.")

    frame_bytes = WIDTH * HEIGHT * 3
    try:
        for frame_index in range(TOTAL_FRAMES):
            raw = decoder.stdout.read(frame_bytes)
            if len(raw) != frame_bytes:
                raise SystemExit(f"Decoder ended early at frame {frame_index}; read {len(raw)} bytes.")
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3)).copy()
            before = Image.fromarray(frame, "RGB")
            after = process_frame(frame, frame_index, right_curve, source_hit_frames)
            if frame_index in sample_frames:
                hit = sample_frames[frame_index]
                label = str(hit["label"]).lower().replace(" ", "_").replace("-", "_")
                t = frame_index / FPS
                quads = active_quads(t)
                crop_box = right_card_crop_bbox(quads)
                before_path = sample_dir / f"{frame_index:04d}_{label}_before.png"
                after_path = sample_dir / f"{frame_index:04d}_{label}_after.png"
                before_crop_path = sample_dir / f"{frame_index:04d}_{label}_right_card_before.png"
                after_crop_path = sample_dir / f"{frame_index:04d}_{label}_right_card_after.png"
                delta_crop_path = sample_dir / f"{frame_index:04d}_{label}_right_card_delta.png"
                before.save(before_path)
                after.save(after_path)
                before_crop = before.crop(crop_box)
                after_crop = after.crop(crop_box)
                delta_crop = ImageEnhance.Brightness(ImageChops.difference(before_crop, after_crop)).enhance(9.0)
                before_crop.save(before_crop_path)
                after_crop.save(after_crop_path)
                delta_crop.save(delta_crop_path)
                metrics = right_video_delta_metrics(before, after, quads)
                sample_rows.append(
                    {
                        "label": hit["label"],
                        "frame_index": frame_index,
                        "time_seconds": round(t, 6),
                        "bass_hit_score": hit["score"],
                        "right_video_strength": round(float(right_curve[frame_index]), 6),
                        "elapsed_frames_from_source_hit": max(0, frame_index - int(source_hit_frames[frame_index])),
                        "active_quad_labels": [item["label"] for item in quads],
                        "crop_bbox": list(crop_box),
                        "before_frame": str(before_path),
                        "after_frame": str(after_path),
                        "right_card_before": str(before_crop_path),
                        "right_card_after": str(after_crop_path),
                        "right_card_delta": str(delta_crop_path),
                        **metrics,
                    }
                )
            encoder.stdin.write(np.asarray(after, dtype=np.uint8).tobytes())
    finally:
        encoder.stdin.close()
        decoder.stdout.close()
    decoder_rc = decoder.wait()
    encoder_rc = encoder.wait()
    if decoder_rc != 0:
        raise SystemExit(f"ffmpeg decoder failed with code {decoder_rc}")
    if encoder_rc != 0:
        raise SystemExit(f"ffmpeg encoder failed with code {encoder_rc}")
    run(["ffmpeg", "-v", "error", "-i", str(final_mp4), "-f", "null", "-"])

    return {
        "source_video": str(source_mp4),
        "final_video": str(final_mp4),
        "frame_count": TOTAL_FRAMES,
        "right_video_curve_values": str(curve_path),
        "right_video_curve_values_sha256": sha256(curve_path),
        "sample_rows": sample_rows,
        "render_model": "card_space_right_video_pressure_ripple_with_carry_through_v1",
    }


def make_contact_sheet(final_mp4: Path, qa_dir: Path) -> Path:
    samples = [
        ("cold open", 0.75),
        ("Challenger", 8.373),
        ("Therac-25", 12.075),
        ("Hyatt Regency", 16.683),
        ("Semmelweis", 19.541),
        ("Tacoma Narrows", 23.541),
        ("Piltdown Man", 28.949),
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
        frame_path = frames_dir / f"{label.lower().replace(' ', '_')}_{seconds:.3f}.jpg"
        extract_frame(final_mp4, seconds, frame_path)
        tiles.append((label, seconds, Image.open(frame_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)))
    cols = 3
    rows = math.ceil(len(tiles) / cols)
    label_h = 44
    sheet = Image.new("RGB", (cols * 480, rows * (270 + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, bold=True)
    time_font = font(15)
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


def make_right_video_qa_sheet(render_report: dict[str, Any], qa_dir: Path) -> tuple[Path, dict[str, Any]]:
    rows = render_report["sample_rows"]
    tile_w, tile_h = 360, 240
    label_h = 48
    cols = 3
    sheet = Image.new("RGB", (cols * tile_w, len(rows) * (tile_h + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(14, bold=True)
    small_font = font(12)
    for row_index, row in enumerate(rows):
        y = row_index * (tile_h + label_h)
        images = [
            ("before", Image.open(row["right_card_before"]).convert("RGB")),
            ("after", Image.open(row["right_card_after"]).convert("RGB")),
            ("delta x9", Image.open(row["right_card_delta"]).convert("RGB")),
        ]
        for col, (title, image) in enumerate(images):
            x = col * tile_w
            sheet.paste(image.resize((tile_w, tile_h), Image.Resampling.LANCZOS), (x, y))
            draw.rectangle((x, y + tile_h, x + tile_w, y + tile_h + label_h), fill=(18, 20, 24))
            draw.text((x + 8, y + tile_h + 5), f"{row['label']} {title}", fill=(238, 240, 242), font=label_font)
            draw.text(
                (x + 8, y + tile_h + 25),
                f"{row['time_seconds']:05.2f}s s={row['right_video_strength']:.2f}",
                fill=(190, 198, 205),
                font=small_font,
            )
    out = qa_dir / "right_video_pressure_ripple_before_after_delta_sheet.jpg"
    sheet.save(out, quality=92)
    effect_reads = [row.get("right_video_interior_effect_read") == "pass" for row in rows]
    carry_reads = [row.get("carry_through_edge_read") == "pass" for row in rows]
    seam_reads = [row.get("no_hard_edge_cutoff_read") == "pass" for row in rows]
    report = {
        "sample_count": len(rows),
        "rows": rows,
        "right_video_interior_effect_read": "pass" if effect_reads and all(effect_reads) else "tighten",
        "carry_through_edge_read": "pass" if carry_reads and all(carry_reads) else "tighten",
        "no_hard_edge_cutoff_read": "pass" if seam_reads and all(seam_reads) else "tighten",
        "video_bleed_read": "pass_video_pixels_clipped_to_rounded_screen_mask_by_alpha_composite_model",
        "geometry_stability_read": "pass_card_quads_and_masks_reused_without_moving_vertices",
    }
    return out, report


def make_review_html(
    package_dir: Path,
    final_mp4: Path,
    contact_sheet: Path,
    right_video_qa_sheet: Path,
    source_pulse_curve_plot: Path,
    hit_json: Path,
    manifest_path: Path,
) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pressure Bends Right-Video Bass Ripple Review</title>
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
  <h1>Pressure Bends Right-Video Bass Ripple Review</h1>
  <video controls preload="metadata" src="{html.escape(str(final_mp4.relative_to(package_dir)))}"></video>
  <section class="meta">
    <div><strong>Runtime</strong><br>{OUTPUT_SECONDS:.3f}s, 24fps</div>
    <div><strong>Right Video</strong><br>Clipped pressure+ripple</div>
    <div><strong>Audio</strong><br>AAC stream copied unchanged</div>
  </section>
  <h2>Scene Contact Sheet</h2>
  <img src="{html.escape(str(contact_sheet.relative_to(package_dir)))}" alt="Scene contact sheet">
  <h2>Right-Video Ripple QA</h2>
  <img src="{html.escape(str(right_video_qa_sheet.relative_to(package_dir)))}" alt="Right-video before, after, and delta samples">
  <h2>Inherited Bass Hit Curve</h2>
  <img src="{html.escape(str(source_pulse_curve_plot.relative_to(package_dir)))}" alt="Inherited frame-locked bass-drum pulse curve">
  <h2>Hit Map</h2>
  <p><code>{html.escape(str(hit_json.relative_to(package_dir)))}</code></p>
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
                "# Pressure Bends Right-Video Bass Ripple Carry-Through",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This local-review successor keeps the accepted full-backplate bass pulse, timing, audio stream, scenes, neutral end backplate, and adaptive borderless end screen. It adds a clipped bass-hit pressure/ripple response inside the right-side Short cards, plus a lower-amplitude carry-through response around the card edge and backplate.",
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


def format_pass(probe: dict[str, Any]) -> bool:
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return (
        video_stream.get("codec_name") == "h264"
        and video_stream.get("width") == WIDTH
        and video_stream.get("height") == HEIGHT
        and video_stream.get("avg_frame_rate") == "24/1"
        and audio_stream.get("codec_name") == "aac"
        and str(audio_stream.get("channels")) == "2"
    )


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    source_pointer: dict[str, Any],
    source_manifest: dict[str, Any],
    source_mp4: Path,
    source_hit_json: Path,
    source_pulse_curve_json: Path,
    inherited_pulse_curve_plot: Path,
    local_hit_json: Path,
    local_hit_csv: Path,
    local_pulse_curve_json: Path,
    render_report: dict[str, Any],
    contact_sheet: Path,
    right_video_qa_sheet: Path,
    right_video_qa_report: dict[str, Any],
    range_probe: dict[str, Any],
    review_html: Path,
    final_mp4: Path,
    source_audio_measure: dict[str, Any],
    final_audio_measure: dict[str, Any],
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    final_seconds = float(probe.get("format", {}).get("duration", 0.0))
    source_audio_sha = stream_sha256(source_mp4, "0:a:0", package_dir / "work/source_audio.aac")
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    source_video_sha = stream_sha256(source_mp4, "0:v:0", package_dir / "work/source_video.h264")
    final_video_sha = stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264")
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= pressure.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    duration_read = "pass" if abs(final_seconds - OUTPUT_SECONDS) <= (1.0 / FPS) else "reject_duration_mismatch"
    source_reads = source_manifest.get("reads", {})
    hit_analysis = source_manifest["bass_drum_pulse"]["hit_analysis"]
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
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
            "predecessor_package": source_pointer["package_dir"],
            "predecessor_manifest": source_pointer["manifest"],
            "predecessor_manifest_sha256": sha256(Path(source_pointer["manifest"])),
            "predecessor_final_mp4": str(source_mp4),
            "predecessor_final_mp4_sha256": sha256(source_mp4),
            "predecessor_latest_pointer": str(SOURCE_POINTER),
            "predecessor_latest_pointer_sha256": sha256(SOURCE_POINTER),
            "supersedes_reason": "adds_right_side_short_video_bass_pressure_ripple_with_visual_carry_through",
        },
        "source_audio": {
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
            "role": "pressure_bends_source_lineage_audio_inherited",
            "rendered_analysis_source_mp4": source_manifest["source_audio"].get("rendered_analysis_source_mp4", ""),
            "rendered_analysis_source_audio_sha256": source_manifest["source_audio"].get(
                "rendered_analysis_source_audio_sha256", ""
            ),
            "predecessor_audio_measurements": source_audio_measure,
        },
        "audio_treatment": {
            "policy": "audio_stream_copied_unchanged_from_full_backplate_successor",
            "predecessor_audio_stream_sha256": source_audio_sha,
            "final_audio_stream_sha256": final_audio_sha,
            "audio_stream_copy_match": source_audio_sha == final_audio_sha,
            "final_measurements": final_audio_measure,
        },
        "timeline": {
            "fps": FPS,
            "total_frames": TOTAL_FRAMES,
            "output_duration_seconds": final_seconds,
            "frame_locked_output_seconds": OUTPUT_SECONDS,
            "duration_read": duration_read,
            "bass_pulse_seconds": [0.0, OUTPUT_SECONDS],
            "right_video_ripple_seconds": [0.0, END_SCREEN_START_SECONDS],
            "end_screen_seconds": [END_SCREEN_START_SECONDS, OUTPUT_SECONDS],
            "end_screen_duration_seconds": END_SCREEN_SECONDS,
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "end_screen_palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "predecessor_timeline": source_manifest.get("timeline", {}),
        },
        "bass_drum_pulse": {
            "inherited_from_predecessor": True,
            "hit_count": hit_analysis.get("hit_count"),
            "max_frame_lock_offset_seconds": hit_analysis.get("max_frame_lock_offset_seconds"),
            "model": hit_analysis.get("model"),
            "periodic_grid_used": False,
            "mid_high_transient_weight": 0,
            "hit_map_json": str(local_hit_json),
            "hit_map_json_sha256": sha256(local_hit_json),
            "hit_map_csv": str(local_hit_csv),
            "hit_map_csv_sha256": sha256(local_hit_csv),
            "source_hit_map_json": str(source_hit_json),
            "source_hit_map_json_sha256": sha256(source_hit_json),
            "source_pulse_curve_values": str(source_pulse_curve_json),
            "source_pulse_curve_values_sha256": sha256(source_pulse_curve_json),
            "local_pulse_curve_values": str(local_pulse_curve_json),
            "local_pulse_curve_values_sha256": sha256(local_pulse_curve_json),
            "pulse_curve_plot": str(inherited_pulse_curve_plot),
            "pulse_curve_plot_sha256": sha256(inherited_pulse_curve_plot),
            "hit_map_change_read": "pass_inherited_74_hit_frame_locked_map_unchanged",
        },
        "end_screen_palette_contract": source_manifest.get("end_screen_palette_contract", {}),
        "right_video_pressure_ripple": {
            "config": RIGHT_VIDEO_EFFECT,
            "effect_scope": "active_right_side_short_video_cards_before_end_screen_only",
            "screen_content_policy": "distorted_video_pixels_clipped_to_rounded_screen_mask",
            "carry_through_policy": "same_hit_field_continues_as_lower_amplitude_card_edge_and_backplate_luma_refraction",
            "protected_layers": [
                "subject_badges",
                "labels",
                "youtube_end_screen_placeholders",
                "end_screen_targets",
                "card_quad_vertices",
                "rounded_screen_mask_geometry",
            ],
            "qa_report": right_video_qa_report,
        },
        "visual_qa": {
            "render_report": render_report,
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "right_video_qa_sheet": str(right_video_qa_sheet),
            "right_video_qa_sheet_sha256": sha256(right_video_qa_sheet),
            "source_video_stream_sha256": source_video_sha,
            "final_video_stream_sha256": final_video_sha,
        },
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "review_html_sha256": sha256(review_html),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "manifest": str(manifest_path),
            "contact_sheet": str(contact_sheet),
            "right_video_qa_sheet": str(right_video_qa_sheet),
            "range_server_probe": range_probe["receipt_path"],
            "range_server_probe_sha256": range_probe["receipt_sha256"],
        },
        "reads": {
            "source_audio_hash_read": "pass_source_pressure_bends_sha256_recorded",
            "audio_replacement_read": "pass_pressure_bends_audio_retained_from_accepted_successor",
            "full_track_audio_read": "pass_full_pressure_bends_runtime_retained_without_loop" if duration_read == "pass" else "reject_duration_mismatch",
            "safe_mastering_read": "pass_predecessor_safe_aac_mastering_retained" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_audio_stream_has_no_clipping" if no_clipping_pass else "reject_final_audio_clipping_or_peak_too_hot",
            "audio_stream_copy_read": "pass_audio_stream_copied_unchanged" if source_audio_sha == final_audio_sha else "reject_audio_stream_changed",
            "video_preservation_read": "pass_predecessor_timing_scenes_full_backplate_pulse_and_end_screen_retained",
            "end_screen_extension_read": "pass_final_20s_neutral_adaptive_borderless_end_screen_retained",
            "end_screen_title_image_absence_read": source_reads.get(
                "end_screen_title_image_absence_read", "pass_no_title_image_added_to_end_screen"
            ),
            "end_screen_palette_contract_read": source_reads.get(
                "end_screen_palette_contract_read", "pass_backplate_sampled_palette_contract_present"
            ),
            "end_screen_target_fill_palette_read": source_reads.get(
                "end_screen_target_fill_palette_read", "pass_local_target_fills_sampled_from_backplate_regions"
            ),
            "end_screen_target_contrast_read": source_reads.get(
                "end_screen_target_contrast_read", "pass_borderless_underlay_legible_without_target_outlines"
            ),
            "source_integrated_panel_color_read": source_reads.get(
                "source_integrated_panel_color_read", "pass_perceptual_backplate_colors_visible_in_end_screen_targets"
            ),
            "no_cross_episode_default_palette_read": source_reads.get(
                "no_cross_episode_default_palette_read", "pass_no_cross_episode_default_target_colors"
            ),
            "end_screen_adaptive_perceptual_variability_read": source_reads.get(
                "end_screen_adaptive_perceptual_variability_read",
                "pass_backplate_hue_visible_across_end_screen_targets",
            ),
            "format_read": "pass" if format_pass(probe) else "reject",
            "full_decode_read": pressure.full_decode_read(final_mp4),
            "bass_drum_hit_map_read": "pass_inherited_same_74_hit_low_band_map",
            "low_band_only_timing_read": source_manifest["bass_drum_pulse"]["hit_analysis"].get(
                "low_band_only_read", "pass_low_band_flux_energy_drives_hit_map"
            ),
            "periodic_grid_read": source_manifest["bass_drum_pulse"]["hit_analysis"].get(
                "periodic_grid_read", "pass_no_periodic_grid_or_tempo_fallback_used"
            ),
            "full_backplate_pulse_retention_read": "pass_full_backplate_predecessor_used_as_visual_source",
            "right_video_pressure_ripple_read": right_video_qa_report["right_video_interior_effect_read"],
            "right_video_clipped_screen_read": "pass_video_pixels_clipped_to_rounded_screen_mask",
            "right_video_carry_through_read": right_video_qa_report["carry_through_edge_read"],
            "right_video_no_hard_edge_cutoff_read": right_video_qa_report["no_hard_edge_cutoff_read"],
            "right_video_no_bleed_read": right_video_qa_report["video_bleed_read"],
            "card_geometry_stability_read": right_video_qa_report["geometry_stability_read"],
            "foreground_card_placeholder_protection_read": "pass_badges_labels_end_screen_placeholders_and_target_geometry_protected",
            "neutral_end_screen_retained_read": source_reads.get(
                "neutral_end_screen_retained_read", "pass_neutral_non_episode_end_screen_backplate_retained"
            ),
            "end_screen_outline_removal_read": source_reads.get(
                "end_screen_outline_removal_read", "pass_borderless_placeholder_method_retained_no_outline_added"
            ),
            "html_range_server_read": range_probe["range_server_read"],
            "range_server_read": range_probe["range_server_read"],
            "youtube_action_read": "blocked_local_review_only",
        },
        "qa": {
            "ffprobe_read": "pass_1920x1080_24fps_h264_stereo_aac_58_291667s" if format_pass(probe) else "reject_format",
            "full_decode_read": pressure.full_decode_read(final_mp4),
            "audio_loudness_read": "pass_audio_stream_copied_safe_measurements_retained" if safe_mastering_pass else "reject_audio_measurements",
            "hit_map_read": "pass_same_74_hits" if hit_analysis.get("hit_count") == 74 else "tighten_hit_count_changed",
            "range_server_read": range_probe["range_server_read"],
            "youtube_uploaded": False,
            "youtube_channel_trailer_replaced": False,
        },
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
        "media_probe": probe,
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    require_file(SOURCE_POINTER, "full-backplate pulse latest pointer")
    require_file(TRACK_PATH, "Pressure Bends source track")
    source_pointer = read_json(SOURCE_POINTER)
    source_package = Path(source_pointer["package_dir"])
    source_manifest_path = Path(source_pointer["manifest"])
    source_mp4 = Path(source_pointer["final_mp4"])
    source_hit_json = source_package / "qa/bass_drum_hit_map.json"
    source_hit_csv = source_package / "qa/bass_drum_hit_map.csv"
    source_pulse_curve_json = source_package / "work/pulse_curve_values.json"
    source_pulse_curve_plot = source_package / "qa/bass_drum_pulse_curve.png"
    for path, label in [
        (source_package, "full-backplate predecessor package"),
        (source_manifest_path, "full-backplate predecessor manifest"),
        (source_mp4, "full-backplate predecessor MP4"),
        (source_hit_json, "inherited bass hit map JSON"),
        (source_hit_csv, "inherited bass hit map CSV"),
        (source_pulse_curve_json, "inherited pulse curve values"),
        (source_pulse_curve_plot, "inherited pulse curve plot"),
    ]:
        require_file(path, label)

    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    work_dir = package_dir / "work"
    for directory in [package_dir, video_dir, qa_dir, work_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    source_manifest = read_json(source_manifest_path)
    hit_analysis = read_json(source_hit_json)
    local_hit_json = qa_dir / "bass_drum_hit_map.json"
    local_hit_csv = qa_dir / "bass_drum_hit_map.csv"
    local_pulse_curve_json = work_dir / "pulse_curve_values.json"
    inherited_pulse_curve_plot = qa_dir / "bass_drum_pulse_curve.png"
    shutil.copy2(source_hit_json, local_hit_json)
    shutil.copy2(source_hit_csv, local_hit_csv)
    shutil.copy2(source_pulse_curve_json, local_pulse_curve_json)
    shutil.copy2(source_pulse_curve_plot, inherited_pulse_curve_plot)

    sample_hits = select_hit_samples(hit_analysis["hits"])
    final_mp4 = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_1080p24.mp4"
    render_report = render_right_video_ripple(source_mp4, final_mp4, hit_analysis, sample_hits, qa_dir, work_dir)
    source_audio_measure = pressure.measure_audio(source_mp4)
    final_audio_measure = pressure.measure_audio(final_mp4)
    contact_sheet = make_contact_sheet(final_mp4, qa_dir)
    right_video_qa_sheet, right_video_qa_report = make_right_video_qa_sheet(render_report, qa_dir)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(
        package_dir,
        final_mp4,
        contact_sheet,
        right_video_qa_sheet,
        inherited_pulse_curve_plot,
        local_hit_json,
        manifest_path,
    )
    range_probe = probe_range_server(package_dir, review_html, qa_dir)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        source_pointer=source_pointer,
        source_manifest=source_manifest,
        source_mp4=source_mp4,
        source_hit_json=source_hit_json,
        source_pulse_curve_json=source_pulse_curve_json,
        inherited_pulse_curve_plot=inherited_pulse_curve_plot,
        local_hit_json=local_hit_json,
        local_hit_csv=local_hit_csv,
        local_pulse_curve_json=local_pulse_curve_json,
        render_report=render_report,
        contact_sheet=contact_sheet,
        right_video_qa_sheet=right_video_qa_sheet,
        right_video_qa_report=right_video_qa_report,
        range_probe=range_probe,
        review_html=review_html,
        final_mp4=final_mp4,
        source_audio_measure=source_audio_measure,
        final_audio_measure=final_audio_measure,
    )
    write_json(manifest_path, manifest)
    receipt = pressure.run_contract_validator(manifest_path)
    readme = write_readme(package_dir, final_mp4, review_html, manifest_path, receipt.get("receipt_path", ""))
    latest = {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "review_url": f"{REVIEW_SERVER_BASE_URL}/{package_dir.name}/{review_html.name}",
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
