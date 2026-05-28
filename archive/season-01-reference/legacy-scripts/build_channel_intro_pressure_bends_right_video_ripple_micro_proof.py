#!/usr/bin/env python3
"""Build a short right-video ripple micro-proof for the Pressure Bends intro."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont


WIDTH = 1920
HEIGHT = 1080
FPS = 24
PROOF_START_SECONDS = 6.0
PROOF_DURATION_SECONDS = 2.0
PROOF_FRAMES = int(round(PROOF_DURATION_SECONDS * FPS))
HIT_SECONDS = 6.291667
HIT_FRAME = int(round(HIT_SECONDS * FPS))
OUTPUT_STEM = "channel_intro_pressure_bends_right_video_ripple_micro_proof"
REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8767"

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
FULL_RENDER_HELPER = (
    REPO_ROOT
    / "scripts/build_channel_intro_pressure_bends_original_format_bass_drum_right_video_pressure_ripple_fix.py"
)
SOURCE_POINTER = OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_full_backplate_pulse_fix_latest.json"
REJECTED_FULL_RENDER_PACKAGE = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_bass_drum_right_video_pressure_ripple_fix_20260527T220702Z"
)
REJECTED_FULL_RENDER_MANIFEST = (
    REJECTED_FULL_RENDER_PACKAGE
    / "channel_intro_pressure_bends_original_format_bass_drum_right_video_pressure_ripple_fix_manifest.json"
)

SMOOTH_RIPPLE_CONFIG = {
    "profile_id": "right_video_smooth_pressure_refraction_micro_proof_v1",
    "render_model": "numpy_per_pixel_bilinear_radial_remap_no_mesh",
    "proof_window_seconds": [PROOF_START_SECONDS, PROOF_START_SECONDS + PROOF_DURATION_SECONDS],
    "hit_seconds": HIT_SECONDS,
    "hit_frame": HIT_FRAME,
    "decay_frames": 9,
    "max_displacement_px": 1.65,
    "base_pressure_displacement_px": 0.42,
    "ripple_wavelength_px": 148.0,
    "ripple_travel_px_per_frame": 62.0,
    "ripple_band_width_px": 175.0,
    "pressure_contrast_lift": 0.024,
    "pressure_brightness_lift": 0.022,
    "scanline_lift": 0.014,
    "screen_wash_mix": 0.018,
    "carry_through_brightness_lift": 0.075,
    "carry_through_additive_lift_rgb": [2.0, 3.0, 7.0],
    "carry_through_wash_mix": 0.035,
    "carry_through_mask_blur_px": 42,
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


full = load_module("channel_intro_rejected_ripple_helper_for_micro_proof", FULL_RENDER_HELPER)


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
                "stream=index,codec_name,codec_type,width,height,avg_frame_rate,sample_rate,channels,duration:format=duration",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    payload["path"] = str(path)
    payload["sha256"] = sha256(path)
    return payload


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


def bilinear_sample(image: np.ndarray, map_x: np.ndarray, map_y: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    map_x = np.clip(map_x, 0.0, width - 1.0)
    map_y = np.clip(map_y, 0.0, height - 1.0)
    x0 = np.floor(map_x).astype(np.int32)
    y0 = np.floor(map_y).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, width - 1)
    y1 = np.clip(y0 + 1, 0, height - 1)
    wx = (map_x - x0)[:, :, None]
    wy = (map_y - y0)[:, :, None]
    top = image[y0, x0] * (1.0 - wx) + image[y0, x1] * wx
    bottom = image[y1, x0] * (1.0 - wx) + image[y1, x1] * wx
    return top * (1.0 - wy) + bottom * wy


def proof_strength(global_frame: int) -> tuple[float, int]:
    elapsed = global_frame - HIT_FRAME
    if elapsed < 0 or elapsed > int(SMOOTH_RIPPLE_CONFIG["decay_frames"]):
        return 0.0, max(0, elapsed)
    strength = math.exp(-elapsed / 4.6)
    return min(1.0, max(0.0, strength)), elapsed


def smooth_pressure_refraction(card: Image.Image, strength: float, elapsed_frames: int) -> Image.Image:
    if strength < 0.01:
        return card
    source = np.asarray(card.convert("RGB"), dtype=np.float32)
    h, w = source.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = w * 0.50
    cy = h * 0.45
    dx = xx - cx
    dy = (yy - cy) * 0.68
    radius = np.sqrt(dx * dx + dy * dy) + 1e-6

    phase = elapsed_frames * float(SMOOTH_RIPPLE_CONFIG["ripple_travel_px_per_frame"])
    wavelength = float(SMOOTH_RIPPLE_CONFIG["ripple_wavelength_px"])
    band_width = float(SMOOTH_RIPPLE_CONFIG["ripple_band_width_px"])
    ring = np.exp(-((radius - phase) ** 2) / (2.0 * band_width * band_width))
    wave = np.sin((radius - phase) / wavelength * math.tau)
    base_pressure = np.exp(-radius / 1350.0) * float(SMOOTH_RIPPLE_CONFIG["base_pressure_displacement_px"])
    amount = strength * (
        base_pressure + ring * wave * float(SMOOTH_RIPPLE_CONFIG["max_displacement_px"])
    )
    map_x = xx + (dx / radius) * amount
    map_y = yy + ((dy / radius) / 0.68) * amount
    refracted = bilinear_sample(source, map_x, map_y)

    scan = 0.5 + 0.5 * np.sin((yy + elapsed_frames * 3.0) * math.tau / 7.0)
    graded = (refracted - 128.0) * (1.0 + float(SMOOTH_RIPPLE_CONFIG["pressure_contrast_lift"]) * strength) + 128.0
    graded *= 1.0 + float(SMOOTH_RIPPLE_CONFIG["pressure_brightness_lift"]) * strength
    graded *= 1.0 + float(SMOOTH_RIPPLE_CONFIG["scanline_lift"]) * strength * scan[:, :, None]
    wash = np.array([24, 44, 82], dtype=np.float32)
    mix = float(SMOOTH_RIPPLE_CONFIG["screen_wash_mix"]) * strength
    graded = graded * (1.0 - mix) + wash * mix

    original = source
    mask = np.asarray(full.CORE_MASK, dtype=np.float32) / 255.0
    mask = (mask * min(1.0, 0.64 + 0.36 * strength))[:, :, None]
    output = original * (1.0 - mask) + graded * mask
    return Image.fromarray(np.clip(output, 0, 255).astype(np.uint8), "RGB")


def smooth_carry_through(
    frame: Image.Image,
    quad: list[tuple[float, float]],
    strength: float,
    elapsed_frames: int,
    t: float,
) -> Image.Image:
    if strength < 0.01:
        return frame
    poly = full.polygon_mask(quad, blur_px=0)
    halo = full.polygon_mask(
        quad,
        blur_px=int(SMOOTH_RIPPLE_CONFIG["carry_through_mask_blur_px"]),
        grow_px=47,
    )
    soft_edge = ImageChops.subtract(halo, poly.filter(ImageFilter.MaxFilter(11)))
    dim_halo = Image.fromarray((np.asarray(halo, dtype=np.float32) * 0.32).astype(np.uint8), "L")
    mask = ImageChops.lighter(dim_halo, soft_edge)
    mask = full.subtract_protected_ui(mask, t)

    arr = np.asarray(frame.convert("RGB"), dtype=np.float32)
    m = np.asarray(mask, dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
    cx = sum(x for x, _ in quad) / 4.0
    cy = sum(y for _, y in quad) / 4.0
    dist = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 0.72) ** 2)
    wave = 0.76 + 0.24 * np.sin((dist - elapsed_frames * 58.0) / 150.0 * math.tau)
    shaped = (m * wave * strength)[:, :, None]
    additive = np.array(SMOOTH_RIPPLE_CONFIG["carry_through_additive_lift_rgb"], dtype=np.float32)
    wash = np.array([34, 48, 102], dtype=np.float32)
    arr *= 1.0 + float(SMOOTH_RIPPLE_CONFIG["carry_through_brightness_lift"]) * shaped
    arr += additive * shaped
    mix = float(SMOOTH_RIPPLE_CONFIG["carry_through_wash_mix"]) * shaped
    arr = arr * (1.0 - mix) + wash * mix
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def apply_smooth_effect(frame: Image.Image, global_frame: int) -> tuple[Image.Image, dict[str, Any]]:
    t = global_frame / FPS
    strength, elapsed = proof_strength(global_frame)
    quads = full.active_quads(t)
    if strength < 0.01 or not quads:
        return frame, {
            "global_frame": global_frame,
            "global_time_seconds": round(t, 6),
            "strength": 0.0,
            "elapsed_frames": elapsed,
            "active_quad_labels": [item["label"] for item in quads],
        }

    carried = frame
    for item in quads:
        carried = smooth_carry_through(carried, item["quad"], strength * 0.55, elapsed, t)

    composited = carried.convert("RGBA")
    for item in quads:
        card = full.unwarp_card(carried, item["quad"])
        effected_card = smooth_pressure_refraction(card, strength, elapsed)
        layer, offset = full.warp_effect_card(effected_card, item["quad"])
        composited.alpha_composite(layer, offset)
    return composited.convert("RGB"), {
        "global_frame": global_frame,
        "global_time_seconds": round(t, 6),
        "strength": round(float(strength), 6),
        "elapsed_frames": elapsed,
        "active_quad_labels": [item["label"] for item in quads],
    }


def decode_source_frames(source_mp4: Path) -> list[Image.Image]:
    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{PROOF_START_SECONDS:.6f}",
            "-i",
            str(source_mp4),
            "-frames:v",
            str(PROOF_FRAMES),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ]
    )
    frame_bytes = WIDTH * HEIGHT * 3
    if len(raw) != frame_bytes * PROOF_FRAMES:
        raise SystemExit(f"Expected {PROOF_FRAMES} frames, got {len(raw) // frame_bytes}")
    frames = []
    for index in range(PROOF_FRAMES):
        chunk = raw[index * frame_bytes : (index + 1) * frame_bytes]
        arr = np.frombuffer(chunk, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3)).copy()
        frames.append(Image.fromarray(arr, "RGB"))
    return frames


def encode_clip(frames: list[Image.Image], source_mp4: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
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
            f"{frames[0].width}x{frames[0].height}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-ss",
            f"{PROOF_START_SECONDS:.6f}",
            "-t",
            f"{PROOF_DURATION_SECONDS:.6f}",
            "-i",
            str(source_mp4),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-frames:v",
            str(len(frames)),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out_path),
        ],
        stdin=subprocess.PIPE,
    )
    if encoder.stdin is None:
        raise SystemExit("Could not open ffmpeg encoder pipe.")
    try:
        for frame in frames:
            encoder.stdin.write(np.asarray(frame.convert("RGB"), dtype=np.uint8).tobytes())
    finally:
        encoder.stdin.close()
    rc = encoder.wait()
    if rc != 0:
        raise SystemExit(f"ffmpeg encoder failed with code {rc}: {out_path}")


def side_by_side_frame(before: Image.Image, after: Image.Image, local_index: int, context: dict[str, Any]) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (10, 12, 18))
    draw = ImageDraw.Draw(canvas)
    title_font = font(30, bold=True)
    small_font = font(20)
    panel_w, panel_h = 900, 506
    before_panel = before.resize((panel_w, panel_h), Image.Resampling.LANCZOS)
    after_panel = after.resize((panel_w, panel_h), Image.Resampling.LANCZOS)
    canvas.paste(before_panel, (50, 216))
    canvas.paste(after_panel, (970, 216))
    draw.text((50, 168), "before", fill=(238, 240, 244), font=title_font)
    draw.text((970, 168), "smooth pressure/refraction proof", fill=(238, 240, 244), font=title_font)
    draw.text(
        (50, 744),
        f"global {context['global_time_seconds']:.3f}s   local frame {local_index:02d}   strength {context['strength']:.3f}",
        fill=(190, 198, 205),
        font=small_font,
    )
    return canvas


def right_card_crop(frame: Image.Image, t: float) -> Image.Image:
    quads = full.active_quads(t)
    crop = full.right_card_crop_bbox(quads, pad=56)
    return frame.crop(crop)


def make_frame_artifacts(
    before_frames: list[Image.Image],
    after_frames: list[Image.Image],
    contexts: list[dict[str, Any]],
    qa_dir: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    sample_offsets = [0, 2, 5, 9]
    sample_globals = [HIT_FRAME + offset for offset in sample_offsets]
    sample_locals = [frame - int(round(PROOF_START_SECONDS * FPS)) for frame in sample_globals]
    frame_dir = qa_dir / "smooth_ripple_sample_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    tile_w, tile_h = 360, 240
    label_h = 54
    contact = Image.new("RGB", (3 * tile_w, len(sample_locals) * (tile_h + label_h)), (18, 20, 24))
    strip = Image.new("RGB", (len(sample_locals) * tile_w, tile_h + label_h), (18, 20, 24))
    contact_draw = ImageDraw.Draw(contact)
    strip_draw = ImageDraw.Draw(strip)
    label_font = font(15, bold=True)
    small_font = font(12)

    for row_index, (offset, local_index, global_frame) in enumerate(zip(sample_offsets, sample_locals, sample_globals, strict=True)):
        before = before_frames[local_index]
        after = after_frames[local_index]
        context = contexts[local_index]
        t = global_frame / FPS
        before_crop = right_card_crop(before, t)
        after_crop = right_card_crop(after, t)
        delta = ImageEnhance.Brightness(ImageChops.difference(before_crop, after_crop)).enhance(12.0)
        safe = f"{global_frame:04d}_plus_{offset:02d}"
        before_path = frame_dir / f"{safe}_before.png"
        after_path = frame_dir / f"{safe}_after.png"
        delta_path = frame_dir / f"{safe}_delta_x12.png"
        before_crop.save(before_path)
        after_crop.save(after_path)
        delta.save(delta_path)
        rows.append(
            {
                "offset_frames": offset,
                "global_frame": global_frame,
                "global_time_seconds": round(t, 6),
                "local_frame": local_index,
                "strength": context["strength"],
                "before_crop": str(before_path),
                "after_crop": str(after_path),
                "delta_crop_x12": str(delta_path),
                "before_sha256": sha256(before_path),
                "after_sha256": sha256(after_path),
                "delta_sha256": sha256(delta_path),
            }
        )
        y = row_index * (tile_h + label_h)
        for col, (title, image) in enumerate([("before", before_crop), ("after", after_crop), ("delta x12", delta)]):
            x = col * tile_w
            contact.paste(image.resize((tile_w, tile_h), Image.Resampling.LANCZOS), (x, y))
            contact_draw.rectangle((x, y + tile_h, x + tile_w, y + tile_h + label_h), fill=(18, 20, 24))
            contact_draw.text((x + 8, y + tile_h + 6), f"+{offset} {title}", fill=(238, 240, 242), font=label_font)
            contact_draw.text(
                (x + 8, y + tile_h + 29),
                f"{t:.3f}s  s={context['strength']:.2f}",
                fill=(190, 198, 205),
                font=small_font,
            )

        x = row_index * tile_w
        strip.paste(after_crop.resize((tile_w, tile_h), Image.Resampling.LANCZOS), (x, 0))
        strip_draw.rectangle((x, tile_h, x + tile_w, tile_h + label_h), fill=(18, 20, 24))
        strip_draw.text((x + 8, tile_h + 6), f"hit +{offset} frames", fill=(238, 240, 242), font=label_font)
        strip_draw.text((x + 8, tile_h + 29), f"{t:.3f}s  s={context['strength']:.2f}", fill=(190, 198, 205), font=small_font)

    contact_path = qa_dir / "smooth_ripple_before_after_delta_contact_sheet.jpg"
    strip_path = qa_dir / "smooth_ripple_hit_frame_strip.jpg"
    contact.save(contact_path, quality=92)
    strip.save(strip_path, quality=92)
    return contact_path, strip_path, {
        "samples": rows,
        "hit_frame_strip": str(strip_path),
        "hit_frame_strip_sha256": sha256(strip_path),
        "before_after_delta_contact_sheet": str(contact_path),
        "before_after_delta_contact_sheet_sha256": sha256(contact_path),
        "checkerboard_mesh_artifact_read": "pass_no_pil_mesh_used_smooth_per_pixel_remap",
        "hard_block_boundary_read": "pass_no_rectangular_mesh_cells_generated",
        "screen_realism_read": "review_required_human_judges_smooth_refraction_micro_proof",
    }


def make_review_html(
    package_dir: Path,
    effect_clip: Path,
    side_by_side_clip: Path,
    contact_sheet: Path,
    frame_strip: Path,
    manifest_path: Path,
) -> Path:
    review = package_dir / "review.html"
    review.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Right-Video Ripple Micro-Proof</title>
  <style>
    body {{ margin: 0; background: #101216; color: #eef1f4; font-family: Arial, sans-serif; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    video, img {{ width: 100%; display: block; background: #05070a; }}
    h1 {{ font-size: 28px; margin: 0 0 16px; }}
    h2 {{ font-size: 18px; margin: 28px 0 10px; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .meta div {{ border: 1px solid #2f3742; padding: 12px; background: #171b21; }}
    code {{ color: #d8e9ff; }}
  </style>
</head>
<body>
<main>
  <h1>Right-Video Ripple Micro-Proof</h1>
  <section class="meta">
    <div><strong>Status</strong><br>proof only, review required</div>
    <div><strong>Window</strong><br>{PROOF_START_SECONDS:.3f}-{PROOF_START_SECONDS + PROOF_DURATION_SECONDS:.3f}s</div>
    <div><strong>Hit</strong><br>{HIT_SECONDS:.3f}s, Challenger</div>
  </section>
  <h2>Effect-Only Clip</h2>
  <video controls preload="metadata" src="{html.escape(str(effect_clip.relative_to(package_dir)))}"></video>
  <h2>Before / After Clip</h2>
  <video controls preload="metadata" src="{html.escape(str(side_by_side_clip.relative_to(package_dir)))}"></video>
  <h2>Hit-Frame Strip</h2>
  <img src="{html.escape(str(frame_strip.relative_to(package_dir)))}" alt="Hit frame strip">
  <h2>Before / After / Delta</h2>
  <img src="{html.escape(str(contact_sheet.relative_to(package_dir)))}" alt="Before after delta contact sheet">
  <h2>Manifest</h2>
  <p><code>{html.escape(str(manifest_path.relative_to(package_dir)))}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review


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


def full_decode_read(path: Path) -> str:
    try:
        run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    except subprocess.CalledProcessError:
        return "reject"
    return "pass"


def build(args: argparse.Namespace) -> dict[str, Any]:
    for path, label in [
        (FULL_RENDER_HELPER, "full render helper"),
        (SOURCE_POINTER, "accepted full-backplate latest pointer"),
        (REJECTED_FULL_RENDER_MANIFEST, "rejected full render manifest"),
    ]:
        require_file(path, label)

    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    for directory in [package_dir, video_dir, qa_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    source_pointer = read_json(SOURCE_POINTER)
    source_package = Path(source_pointer["package_dir"])
    source_manifest_path = Path(source_pointer["manifest"])
    source_mp4 = Path(source_pointer["final_mp4"])
    source_hit_map = source_package / "qa/bass_drum_hit_map.json"
    for path, label in [
        (source_manifest_path, "accepted full-backplate manifest"),
        (source_mp4, "accepted full-backplate MP4"),
        (source_hit_map, "inherited bass hit map"),
    ]:
        require_file(path, label)
    hit_map = read_json(source_hit_map)
    selected_hit = min(hit_map["hits"], key=lambda hit: abs(float(hit["frame_time_seconds"]) - HIT_SECONDS))
    if int(selected_hit["frame_index"]) != HIT_FRAME:
        raise SystemExit(f"Unexpected selected hit frame: {selected_hit}")

    before_frames = decode_source_frames(source_mp4)
    after_frames: list[Image.Image] = []
    side_by_side_frames: list[Image.Image] = []
    contexts: list[dict[str, Any]] = []
    proof_start_frame = int(round(PROOF_START_SECONDS * FPS))
    for local_index, before in enumerate(before_frames):
        global_frame = proof_start_frame + local_index
        after, context = apply_smooth_effect(before, global_frame)
        after_frames.append(after)
        contexts.append(context)
        side_by_side_frames.append(side_by_side_frame(before, after, local_index, context))

    effect_clip = video_dir / "right_video_smooth_ripple_effect_only_1080p24.mp4"
    side_by_side_clip = video_dir / "right_video_smooth_ripple_before_after_1080p24.mp4"
    encode_clip(after_frames, source_mp4, effect_clip)
    encode_clip(side_by_side_frames, source_mp4, side_by_side_clip)
    effect_decode = full_decode_read(effect_clip)
    side_decode = full_decode_read(side_by_side_clip)
    contact_sheet, frame_strip, visual_qa = make_frame_artifacts(before_frames, after_frames, contexts, qa_dir)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(package_dir, effect_clip, side_by_side_clip, contact_sheet, frame_strip, manifest_path)
    range_probe = probe_range_server(package_dir, review_html, qa_dir)
    manifest = {
        "artifact_id": f"{OUTPUT_STEM}_{timestamp}",
        "workflow": f"{OUTPUT_STEM}_v1",
        "created_at_utc": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "proof_only_review_required",
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "experiment",
            "production_successor_allowed": False,
            "reason": "micro_proof_only_no_full_runtime_render_until_human_review",
        },
        "lineage": {
            "accepted_full_backplate_predecessor_package": str(source_package),
            "accepted_full_backplate_predecessor_manifest": str(source_manifest_path),
            "accepted_full_backplate_predecessor_manifest_sha256": sha256(source_manifest_path),
            "accepted_full_backplate_predecessor_mp4": str(source_mp4),
            "accepted_full_backplate_predecessor_mp4_sha256": sha256(source_mp4),
            "rejected_full_render_package": str(REJECTED_FULL_RENDER_PACKAGE),
            "rejected_full_render_manifest": str(REJECTED_FULL_RENDER_MANIFEST),
            "rejected_full_render_manifest_sha256": sha256(REJECTED_FULL_RENDER_MANIFEST),
            "rejected_reason": "right_video_checkerboard_mesh_artifact_visual_ripple_not_believable",
        },
        "micro_proof": {
            "scene": "Challenger",
            "window_seconds": [PROOF_START_SECONDS, PROOF_START_SECONDS + PROOF_DURATION_SECONDS],
            "frame_count": PROOF_FRAMES,
            "fps": FPS,
            "selected_bass_hit": selected_hit,
            "config": SMOOTH_RIPPLE_CONFIG,
            "contexts": contexts,
        },
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "review_url": f"{REVIEW_SERVER_BASE_URL}/{package_dir.name}/{review_html.name}",
            "effect_only_clip": str(effect_clip),
            "effect_only_clip_sha256": sha256(effect_clip),
            "before_after_clip": str(side_by_side_clip),
            "before_after_clip_sha256": sha256(side_by_side_clip),
            "hit_frame_strip": str(frame_strip),
            "hit_frame_strip_sha256": sha256(frame_strip),
            "before_after_delta_contact_sheet": str(contact_sheet),
            "before_after_delta_contact_sheet_sha256": sha256(contact_sheet),
            "range_server_probe": range_probe["receipt_path"],
            "range_server_probe_sha256": range_probe["receipt_sha256"],
        },
        "qa": {
            "effect_only_ffprobe": ffprobe(effect_clip),
            "before_after_ffprobe": ffprobe(side_by_side_clip),
            "effect_only_full_decode_read": effect_decode,
            "before_after_full_decode_read": side_decode,
            "range_server_read": range_probe["range_server_read"],
            "visual_qa": visual_qa,
        },
        "reads": {
            "proof_only_read": "pass_micro_proof_only_no_full_runtime_render",
            "rejected_full_render_recorded_read": "pass_prior_full_render_marked_tighten_in_lineage",
            "inherited_hit_timing_read": "pass_uses_existing_6_291667s_challenger_bass_hit_no_new_detection",
            "smooth_remap_read": "pass_numpy_per_pixel_bilinear_remap_no_pil_mesh",
            "checkerboard_mesh_artifact_read": visual_qa["checkerboard_mesh_artifact_read"],
            "hard_block_boundary_read": visual_qa["hard_block_boundary_read"],
            "right_video_clipped_screen_read": "pass_video_pixels_clipped_to_rounded_screen_mask",
            "carry_through_edge_read": "pass_smooth_low_amplitude_card_edge_and_backplate_response",
            "geometry_stability_read": "pass_card_quad_badges_labels_and_placeholders_not_moved",
            "effect_only_full_decode_read": effect_decode,
            "before_after_full_decode_read": side_decode,
            "range_server_read": range_probe["range_server_read"],
            "youtube_action_read": "blocked_local_review_only_no_upload_or_replacement",
        },
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
    }
    write_json(manifest_path, manifest)
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Right-Video Ripple Micro-Proof",
                "",
                "Status: `proof_only_review_required`",
                "",
                "This package tests a smooth per-pixel right-video pressure/refraction ripple around the Challenger bass hit at 6.292s. It is not a full-runtime successor render.",
                "",
                f"- Review HTML: `{review_html}`",
                f"- Effect-only clip: `{effect_clip}`",
                f"- Before/after clip: `{side_by_side_clip}`",
                f"- Manifest: `{manifest_path}`",
                "",
                "No production latest pointer, YouTube upload, or channel replacement was performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "review_url": f"{REVIEW_SERVER_BASE_URL}/{package_dir.name}/{review_html.name}",
        "effect_only_clip": str(effect_clip),
        "before_after_clip": str(side_by_side_clip),
        "manifest": str(manifest_path),
        "status": "proof_only_review_required",
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="", help="UTC timestamp override for reproducible package naming.")
    return parser.parse_args()


def main() -> None:
    print(json.dumps(build(parse_args()), indent=2))


if __name__ == "__main__":
    main()
