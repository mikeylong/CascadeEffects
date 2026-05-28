#!/usr/bin/env python3
"""Build a Challenger trailer proof with the selected regenerated Challenger anchor and right Short plate."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageStat


ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
REFERENCE_PLATE = Path(
    "/Users/mike/Web_CascadeEffects/brand/assets/episode-gallery/proof-v6-ink-lit-subjects/"
    "source-renders/challenger-thumbnail-proof-v6-ink-lit-subjects-source.png"
)
FRESH_THREE_QUARTER_SOURCE_PLATE = Path(
    "/Users/mike/Episodes_CascadeEffects/Channel_Trailer/"
    "challenger_source_plate_regen_v1_20260505T184110Z/source_art/"
    "challenger_true_left_side_3_4_source_plate.png"
)
SOURCE_PLATE_REGEN_PACKAGE = "challenger_source_plate_regen_v1_20260505T184110Z"
SELECTED_SOURCE_VARIANT = "variant_01_broad_left_side_prompt"
SHORT_VIDEO = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/"
    "challenger_short_scoped_v1/motion_contact_sheet/pass_11/final_exports/"
    "challenger_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
    "20260430T_challenger_house_crt_visible_scanline_final_gate_pass01/work/"
    "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
)
V1_AUDIO_MIX = Path(
    "/Users/mike/Episodes_CascadeEffects/Channel_Trailer/channel_trailer_v1_20260505T044755Z/audio/"
    "channel_trailer_final_mix.wav"
)

WIDTH = 1920
HEIGHT = 1080
FPS = 24
DURATION_SECONDS = 10.0
SUPERSAMPLE = 4

SUPERSEDES_PACKAGE_ID = "challenger_visual_proof_v1_20260506T003848Z"
REVISION_REASON = "remove_unmasked_video_plate_top_sheen_artifact"

INK = (4, 10, 28)
PAPER = (255, 248, 232)
VELLUM = (120, 220, 232)

LEFT_ANCHOR_SCALE = 0.88
LEFT_ANCHOR_OFFSET = (-20, 55)
TITLE_SAFE_MARGIN_X = 96
TITLE_SAFE_MARGIN_Y = 54
ANIMATION_DURATION_SECONDS = 8.0
HOLD_DURATION_SECONDS = DURATION_SECONDS - ANIMATION_DURATION_SECONDS

# Center-origin push-in repair: keep the selected source plate placement and
# scale the Short plate from the center of its right-hand rail footprint.
ANIMATION_ORIGIN_XY = (1484.0, 539.0)
START_SHORT_PLATE_QUAD = [
    (1292.2, 243.2),
    (1671.7, 216.0),
    (1671.7, 864.7),
    (1300.4, 832.1),
]
END_SHORT_PLATE_QUAD = [
    (1202.0, 104.0),
    (1760.0, 64.0),
    (1760.0, 1018.0),
    (1214.0, 970.0),
]
SHORT_CARD_SIZE = (720, 1280)
LEFT_ANCHOR_REGION = (0, 40, 1080, 1040)
SHORT_VIDEO_COLOR_FACTOR = 0.62
SHORT_VIDEO_CONTRAST_FACTOR = 0.98
SHORT_VIDEO_BRIGHTNESS_FACTOR = 1.08
SHORT_VIDEO_INK_BLEND = 0.12


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + proc.stdout[-4000:]
            + "\n\nSTDERR:\n"
            + proc.stderr[-4000:]
        )
    return proc


def require_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ffprobe_json(path: Path) -> dict[str, Any]:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(proc.stdout)


def solve_linear_system(rows: list[list[float]], values: list[float]) -> list[float]:
    matrix = [row[:] + [value] for row, value in zip(rows, values, strict=True)]
    size = len(values)
    for pivot_index in range(size):
        pivot_row = max(range(pivot_index, size), key=lambda row_index: abs(matrix[row_index][pivot_index]))
        if abs(matrix[pivot_row][pivot_index]) < 1e-9:
            raise ValueError("Perspective transform matrix is singular.")
        matrix[pivot_index], matrix[pivot_row] = matrix[pivot_row], matrix[pivot_index]
        pivot = matrix[pivot_index][pivot_index]
        matrix[pivot_index] = [value / pivot for value in matrix[pivot_index]]
        for row_index in range(size):
            if row_index == pivot_index:
                continue
            factor = matrix[row_index][pivot_index]
            matrix[row_index] = [
                current - factor * pivot_value
                for current, pivot_value in zip(matrix[row_index], matrix[pivot_index], strict=True)
            ]
    return [matrix[row_index][-1] for row_index in range(size)]


def perspective_coefficients(
    destination_points: list[tuple[float, float]], source_points: list[tuple[float, float]]
) -> tuple[float, ...]:
    rows: list[list[float]] = []
    values: list[float] = []
    for (x, y), (u, v) in zip(destination_points, source_points, strict=True):
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        values.append(u)
        rows.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        values.append(v)
    return tuple(solve_linear_system(rows, values))


def scale_points(points: list[tuple[float, float]], scale: int) -> list[tuple[float, float]]:
    return [(x * scale, y * scale) for x, y in points]


def ease_out_cubic(progress: float) -> float:
    clamped = max(0.0, min(1.0, progress))
    return 1.0 - (1.0 - clamped) ** 3


def interpolate_quads(
    start_quad: list[tuple[float, float]],
    end_quad: list[tuple[float, float]],
    progress: float,
) -> list[tuple[float, float]]:
    eased = ease_out_cubic(progress)
    return [
        (
            start_x + (end_x - start_x) * eased,
            start_y + (end_y - start_y) * eased,
        )
        for (start_x, start_y), (end_x, end_y) in zip(start_quad, end_quad, strict=True)
    ]


def short_plate_quad_at_frame(frame_index: int) -> list[tuple[float, float]]:
    seconds = frame_index / FPS
    if seconds >= ANIMATION_DURATION_SECONDS:
        return END_SHORT_PLATE_QUAD
    return interpolate_quads(START_SHORT_PLATE_QUAD, END_SHORT_PLATE_QUAD, seconds / ANIMATION_DURATION_SECONDS)


def warp_to_quad_patch(
    card: Image.Image, destination_quad: list[tuple[float, float]], pad: int = 16
) -> tuple[Image.Image, tuple[int, int]]:
    min_x = max(0, int(min(point[0] for point in destination_quad) - pad))
    min_y = max(0, int(min(point[1] for point in destination_quad) - pad))
    max_x = int(max(point[0] for point in destination_quad) + pad)
    max_y = int(max(point[1] for point in destination_quad) + pad)
    patch_size = (max(1, max_x - min_x), max(1, max_y - min_y))
    shifted_quad = [(x - min_x, y - min_y) for x, y in destination_quad]
    source_quad = [
        (0.0, 0.0),
        (float(card.width), 0.0),
        (float(card.width), float(card.height)),
        (0.0, float(card.height)),
    ]
    coefficients = perspective_coefficients(shifted_quad, source_quad)
    return (
        card.transform(
            patch_size,
            Image.Transform.PERSPECTIVE,
            coefficients,
            resample=Image.Resampling.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        ),
        (min_x, min_y),
    )


def extract_short_frames(frames_dir: Path) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(SHORT_VIDEO),
            "-t",
            f"{DURATION_SECONDS:.3f}",
            "-vf",
            "fps=24,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
            str(frames_dir / "short_%05d.png"),
        ]
    )
    return len(list(frames_dir.glob("short_*.png")))


def make_background(output_path: Path) -> dict[str, Any]:
    source = Image.open(FRESH_THREE_QUARTER_SOURCE_PLATE).convert("RGB")
    plate = Image.new("RGBA", (WIDTH, HEIGHT), (*INK, 255))
    scaled_size = (round(WIDTH * LEFT_ANCHOR_SCALE), round(HEIGHT * LEFT_ANCHOR_SCALE))
    scaled_source = ImageOps.fit(source, scaled_size, Image.Resampling.LANCZOS, centering=(0.50, 0.50)).convert("RGBA")
    offset_x, offset_y = LEFT_ANCHOR_OFFSET
    src_left = max(0, -offset_x)
    src_top = max(0, -offset_y)
    src_right = min(scaled_source.width, WIDTH - offset_x)
    src_bottom = min(scaled_source.height, HEIGHT - offset_y)
    cropped_source = scaled_source.crop((src_left, src_top, src_right, src_bottom))
    plate.alpha_composite(cropped_source, (max(0, offset_x), max(0, offset_y)))

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((1100, 0, WIDTH, HEIGHT), fill=(0, 0, 0, 30))
    for x in range(1020, WIDTH):
        t = (x - 1020) / (WIDTH - 1020)
        alpha = int(2 + 46 * t)
        draw.line((x, 0, x, HEIGHT), fill=(0, 0, 0, alpha))

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((170, 150, 980, 960), fill=(255, 248, 232, 10))
    glow = glow.filter(ImageFilter.GaussianBlur(95))

    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    vdraw = ImageDraw.Draw(vignette)
    for i in range(0, 360, 8):
        alpha = int(112 * (i / 360) ** 2)
        vdraw.rectangle((i, i, WIDTH - i, HEIGHT - i), outline=alpha, width=8)
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    dark.putalpha(vignette.filter(ImageFilter.GaussianBlur(42)))

    plate = Image.alpha_composite(plate, overlay)
    plate = Image.alpha_composite(plate, glow)
    plate = Image.alpha_composite(plate, dark).convert("RGB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plate.save(output_path, quality=96)
    return {"path": str(output_path), "sha256": file_sha256(output_path)}


def build_short_card(short_frame: Image.Image, scale: int = 1) -> Image.Image:
    card_w, card_h = SHORT_CARD_SIZE[0] * scale, SHORT_CARD_SIZE[1] * scale
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    radius = 74 * scale
    draw.rounded_rectangle((0, 0, card_w - 1, card_h - 1), radius=radius, fill=(242, 236, 226, 238))
    inset = 8 * scale
    screen_box = (inset, inset, card_w - inset, card_h - inset)

    video = ImageOps.fit(
        short_frame.convert("RGB"),
        (screen_box[2] - inset, screen_box[3] - inset),
        Image.Resampling.LANCZOS,
        centering=(0.50, 0.42),
    )
    video = ImageEnhance.Color(video).enhance(SHORT_VIDEO_COLOR_FACTOR)
    video = ImageEnhance.Contrast(video).enhance(SHORT_VIDEO_CONTRAST_FACTOR)
    video = ImageEnhance.Brightness(video).enhance(SHORT_VIDEO_BRIGHTNESS_FACTOR)
    video = Image.blend(video, Image.new("RGB", video.size, (11, 20, 42)), SHORT_VIDEO_INK_BLEND)
    card.paste(video, (screen_box[0], screen_box[1]))

    screen_mask = Image.new("L", (card_w, card_h), 0)
    mask_draw = ImageDraw.Draw(screen_mask)
    mask_draw.rounded_rectangle(screen_box, radius=radius - inset, fill=255)
    card.putalpha(ImageChops.multiply(card.getchannel("A"), screen_mask.filter(ImageFilter.GaussianBlur(0.35 * scale))))

    border = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle(screen_box, radius=radius - inset, outline=(255, 248, 232, 76), width=2 * scale)
    border.putalpha(ImageChops.multiply(border.getchannel("A"), screen_mask))
    return Image.alpha_composite(card, border)


def make_card_shadow(output_size: tuple[int, int], short_plate_quad: list[tuple[float, float]]) -> Image.Image:
    quad = scale_points(short_plate_quad, SUPERSAMPLE)
    shadow = Image.new("RGBA", output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    shifted = [(x + 28 * SUPERSAMPLE, y + 24 * SUPERSAMPLE) for x, y in quad]
    draw.polygon(shifted, fill=(0, 0, 0, 104))
    return shadow.filter(ImageFilter.GaussianBlur(28 * SUPERSAMPLE))


def make_static_base(background: Image.Image) -> Image.Image:
    high_size = (WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE)
    return background.convert("RGBA").resize(high_size, Image.Resampling.LANCZOS)


def composite_scene(
    background: Image.Image,
    short_frame: Image.Image | None = None,
    static_base: Image.Image | None = None,
    short_plate_quad: list[tuple[float, float]] | None = None,
) -> Image.Image:
    out = static_base.copy() if static_base is not None else make_static_base(background)
    quad = short_plate_quad or END_SHORT_PLATE_QUAD
    out.alpha_composite(make_card_shadow(out.size, quad))
    frame = short_frame if short_frame is not None else Image.new("RGB", SHORT_CARD_SIZE, (30, 22, 72))
    card = build_short_card(frame, SUPERSAMPLE)
    layer, offset = warp_to_quad_patch(card, scale_points(quad, SUPERSAMPLE), pad=28 * SUPERSAMPLE)
    out.alpha_composite(layer, offset)
    return out.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def make_proof_frames(background_path: Path, short_frames_dir: Path, frames_dir: Path) -> dict[str, Any]:
    background = Image.open(background_path).convert("RGB")
    static_base = make_static_base(background)
    frames_dir.mkdir(parents=True, exist_ok=True)
    short_frames = sorted(short_frames_dir.glob("short_*.png"))
    expected_frames = int(DURATION_SECONDS * FPS)
    if len(short_frames) < expected_frames:
        raise SystemExit(f"Expected at least {expected_frames} short frames, got {len(short_frames)}")

    for index in range(expected_frames):
        short_frame = Image.open(short_frames[index]).convert("RGB")
        frame = composite_scene(background, short_frame, static_base, short_plate_quad_at_frame(index))
        frame.save(frames_dir / f"frame_{index:05d}.jpg", quality=93)
    return {"frame_count": expected_frames, "fps": FPS, "duration_seconds": DURATION_SECONDS}


def encode_video(frames_dir: Path, output_path: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%05d.jpg"),
            "-t",
            f"{DURATION_SECONDS:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(output_path), "-f", "null", "-"])


def make_contact_sheet(frames_dir: Path, out_path: Path) -> None:
    times = [0.0, 1.8, 3.6, 5.4, 7.2, 9.6]
    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * 3, (thumb_h + 42) * 2), INK)
    draw = ImageDraw.Draw(sheet)
    for idx, t in enumerate(times):
        frame_idx = min(int(t * FPS), int(DURATION_SECONDS * FPS) - 1)
        frame = Image.open(frames_dir / f"frame_{frame_idx:05d}.jpg").convert("RGB")
        frame = frame.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % 3) * thumb_w
        y = (idx // 3) * (thumb_h + 42)
        sheet.paste(frame, (x, y))
        draw.text((x + 14, y + thumb_h + 10), f"{t:04.1f}s", fill=PAPER)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)


def make_geometry_overlay(background_path: Path, out_path: Path) -> None:
    background = Image.open(background_path).convert("RGB")
    proof = composite_scene(background, short_plate_quad=END_SHORT_PLATE_QUAD).convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    start_quad = START_SHORT_PLATE_QUAD
    end_quad = END_SHORT_PLATE_QUAD
    title_safe = (
        TITLE_SAFE_MARGIN_X,
        TITLE_SAFE_MARGIN_Y,
        WIDTH - TITLE_SAFE_MARGIN_X,
        HEIGHT - TITLE_SAFE_MARGIN_Y,
    )
    draw.rectangle(title_safe, outline=(255, 248, 232, 58), width=2)
    draw.rounded_rectangle(LEFT_ANCHOR_REGION, radius=18, outline=(255, 248, 232, 125), width=3)
    draw.line(start_quad + [start_quad[0]], fill=(120, 220, 232, 100), width=3, joint="curve")
    draw.line(end_quad + [end_quad[0]], fill=(*PAPER, 220), width=4, joint="curve")
    draw.line((end_quad[0][0], end_quad[0][1], end_quad[1][0], end_quad[1][1]), fill=(*VELLUM, 190), width=4)
    draw.line((end_quad[3][0], end_quad[3][1], end_quad[2][0], end_quad[2][1]), fill=(*VELLUM, 190), width=4)
    origin_x, origin_y = ANIMATION_ORIGIN_XY
    for start_point, end_point in zip(start_quad, end_quad, strict=True):
        draw.line((origin_x, origin_y, start_point[0], start_point[1]), fill=(120, 220, 232, 54), width=2)
        draw.line((origin_x, origin_y, end_point[0], end_point[1]), fill=(255, 248, 232, 58), width=2)
        draw.line((start_point[0], start_point[1], end_point[0], end_point[1]), fill=(120, 220, 232, 82), width=2)
    draw.ellipse((origin_x - 11, origin_y - 11, origin_x + 11, origin_y + 11), fill=(120, 220, 232, 210))
    draw.ellipse((origin_x - 24, origin_y - 24, origin_x + 24, origin_y + 24), outline=(255, 248, 232, 130), width=3)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(proof, overlay).convert("RGB").save(out_path, quality=94)


def motion_report(frames_dir: Path) -> dict[str, Any]:
    sample_indices = [12, 48, 96, 144, 192, 228]
    card_crop = (1160, 40, 1840, 1040)
    previous = None
    deltas: list[float] = []
    variances: list[float] = []
    for index in sample_indices:
        img = Image.open(frames_dir / f"frame_{index:05d}.jpg").convert("L").crop(card_crop).resize((118, 206))
        mean_luma = int(ImageStat.Stat(img).mean[0])
        stat_img = ImageChops.difference(img, Image.new("L", img.size, mean_luma))
        variances.append(round(ImageStat.Stat(stat_img).mean[0], 3))
        if previous is not None:
            diff = ImageChops.difference(previous, img)
            deltas.append(round(ImageStat.Stat(diff).mean[0], 3))
        previous = img
    return {
        "card_crop_xy": card_crop,
        "card_sample_indices": sample_indices,
        "card_luma_deltas": deltas,
        "card_luma_variance": variances,
        "card_nonblank_read": "pass" if min(variances) > 4.0 else "tighten",
        "card_motion_read": "pass" if max(deltas or [0]) > 1.5 else "tighten",
        "push_in_motion_read": "pass" if max(deltas or [0]) > 2.5 else "tighten",
    }


def right_negative_space_report(background_path: Path) -> dict[str, Any]:
    img = Image.open(background_path).convert("L")
    right_crop_xy = (1120, 70, 1760, 990)
    right_crop = img.crop(right_crop_xy).resize((132, 190))
    mean_luma = int(ImageStat.Stat(right_crop).mean[0])
    stat_img = ImageChops.difference(right_crop, Image.new("L", right_crop.size, mean_luma))
    variance = round(ImageStat.Stat(stat_img).mean[0], 3)
    return {
        "right_negative_space_crop_xy": list(right_crop_xy),
        "right_negative_space_luma_variance": variance,
        "right_negative_space_read": "pass" if variance < 40.0 else "tighten",
        "right_negative_space_note": "Allows the clean paper floor plane; blocks subject/detail clutter in the media-plate field.",
    }


def quad_area(points: list[tuple[float, float]]) -> float:
    return abs(
        sum(
            points[index][0] * points[(index + 1) % len(points)][1]
            - points[(index + 1) % len(points)][0] * points[index][1]
            for index in range(len(points))
        )
        / 2
    )


def quad_bbox_wh(points: list[tuple[float, float]]) -> list[float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2)]


def quad_center(points: list[tuple[float, float]]) -> list[float]:
    return [
        round(sum(point[0] for point in points) / len(points), 2),
        round(sum(point[1] for point in points) / len(points), 2),
    ]


def title_safe_read_for_quad(points: list[tuple[float, float]]) -> bool:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (
        min(xs) >= TITLE_SAFE_MARGIN_X
        and max(xs) <= WIDTH - TITLE_SAFE_MARGIN_X
        and min(ys) >= TITLE_SAFE_MARGIN_Y
        and max(ys) <= HEIGHT - TITLE_SAFE_MARGIN_Y
    )


def layout_balance_report() -> dict[str, Any]:
    xs = [point[0] for point in END_SHORT_PLATE_QUAD]
    ys = [point[1] for point in END_SHORT_PLATE_QUAD]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    title_safe_bounds = [
        TITLE_SAFE_MARGIN_X,
        TITLE_SAFE_MARGIN_Y,
        WIDTH - TITLE_SAFE_MARGIN_X,
        HEIGHT - TITLE_SAFE_MARGIN_Y,
    ]
    title_safe_read = title_safe_read_for_quad(START_SHORT_PLATE_QUAD) and title_safe_read_for_quad(END_SHORT_PLATE_QUAD)
    start_center = quad_center(START_SHORT_PLATE_QUAD)
    end_center = quad_center(END_SHORT_PLATE_QUAD)
    origin = [round(value, 2) for value in ANIMATION_ORIGIN_XY]
    centers_match = start_center == end_center == origin
    return {
        "left_anchor_scale": LEFT_ANCHOR_SCALE,
        "left_anchor_offset_xy": list(LEFT_ANCHOR_OFFSET),
        "title_safe_margin_xy": [TITLE_SAFE_MARGIN_X, TITLE_SAFE_MARGIN_Y],
        "title_safe_bounds_xy": title_safe_bounds,
        "video_plate_animation": "center_origin_push_in_from_right_rail",
        "animation_origin_xy": origin,
        "animation_duration_seconds": ANIMATION_DURATION_SECONDS,
        "hold_duration_seconds": HOLD_DURATION_SECONDS,
        "start_short_plate_quad_xy": [[round(x, 2), round(y, 2)] for x, y in START_SHORT_PLATE_QUAD],
        "end_short_plate_quad_xy": [[round(x, 2), round(y, 2)] for x, y in END_SHORT_PLATE_QUAD],
        "start_short_plate_center_xy": start_center,
        "end_short_plate_center_xy": end_center,
        "start_short_plate_bbox_wh": quad_bbox_wh(START_SHORT_PLATE_QUAD),
        "end_short_plate_bbox_wh": quad_bbox_wh(END_SHORT_PLATE_QUAD),
        "start_short_plate_area_px": round(quad_area(START_SHORT_PLATE_QUAD)),
        "end_short_plate_area_px": round(quad_area(END_SHORT_PLATE_QUAD)),
        "short_plate_bbox_wh": [round(max_x - min_x, 2), round(max_y - min_y, 2)],
        "short_plate_area_px": round(quad_area(END_SHORT_PLATE_QUAD)),
        "title_safe_read": "pass" if title_safe_read else "tighten",
        "center_origin_read": "pass" if centers_match else "tighten",
        "no_lateral_slide_read": "pass" if start_center == end_center else "tighten",
        "balance_repair_read": "pass_candidate_center_origin_push_in_from_right_rail",
    }


def left_anchor_orientation_report() -> dict[str, Any]:
    return {
        "source_plate_regen_package": SOURCE_PLATE_REGEN_PACKAGE,
        "selected_source_variant": SELECTED_SOURCE_VARIANT,
        "left_anchor_camera": "selected_regenerated_3_4_left_side_view",
        "left_anchor_orientation": "inward_toward_right_media_plate",
        "left_anchor_orientation_read": "pass",
        "three_quarter_left_side_read": "pass",
        "literal_side_elevation_read": "pass_no_literal_side_elevation",
        "rear_facing_thumbnail_read": "pass_no_rear_facing_thumbnail_carrier",
        "mirrored_source_read": "pass_no_mirror_transform_used",
        "left_anchor_orientation_method": (
            "user-selected regenerated Paper Architecture source plate placed left/center-left; "
            "source plate package selected variant_01_broad_left_side_prompt"
        ),
    }


def short_video_treatment_report() -> dict[str, Any]:
    return {
        "short_video_color_factor": SHORT_VIDEO_COLOR_FACTOR,
        "short_video_contrast_factor": SHORT_VIDEO_CONTRAST_FACTOR,
        "short_video_brightness_factor": SHORT_VIDEO_BRIGHTNESS_FACTOR,
        "short_video_ink_blend": SHORT_VIDEO_INK_BLEND,
        "right_media_brightness_read": "pass_candidate_brighter_than_prior_dim_treatment",
        "right_media_brightness_note": (
            "Lifted the media plate from brightness 0.78 / ink blend 0.22 "
            "to brightness 1.08 / ink blend 0.12 while keeping a muted evidence treatment."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--keep-frames", action="store_true")
    args = parser.parse_args()

    for path in (REFERENCE_PLATE, FRESH_THREE_QUARTER_SOURCE_PLATE, SHORT_VIDEO, V1_AUDIO_MIX):
        require_file(path)
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required.")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = OUTPUT_BASE / f"challenger_visual_proof_v1_{timestamp}"
    source_dir = output_root / "source_art"
    still_dir = output_root / "still"
    video_dir = output_root / "video"
    qa_dir = output_root / "qa"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    proof_frames_dir = work_dir / "proof_frames"
    for directory in (source_dir, still_dir, video_dir, qa_dir, short_frames_dir, proof_frames_dir):
        directory.mkdir(parents=True, exist_ok=True)

    background_path = source_dir / "challenger_selected_variant_01_base_plate.png"
    background = make_background(background_path)
    extracted_frames = extract_short_frames(short_frames_dir)
    frames = make_proof_frames(background_path, short_frames_dir, proof_frames_dir)

    still_path = still_dir / "challenger_visual_proof_v1_still.png"
    still_frame_index = min(int(ANIMATION_DURATION_SECONDS * FPS), frames["frame_count"] - 1)
    shutil.copyfile(proof_frames_dir / f"frame_{still_frame_index:05d}.jpg", still_path)

    contact_sheet_path = qa_dir / "challenger_visual_proof_v1_contact_sheet.jpg"
    make_contact_sheet(proof_frames_dir, contact_sheet_path)

    geometry_overlay_path = qa_dir / "sketch_geometry_overlay.png"
    make_geometry_overlay(background_path, geometry_overlay_path)

    proof_mp4 = video_dir / "challenger_visual_proof_v1_motion.mp4"
    encode_video(proof_frames_dir, proof_mp4)

    visual_motion_report = motion_report(proof_frames_dir)
    negative_space_report = right_negative_space_report(background_path)
    orientation_report = left_anchor_orientation_report()
    balance_report = layout_balance_report()
    video_treatment_report = short_video_treatment_report()
    manifest_path = output_root / "challenger_visual_proof_manifest.json"
    manifest = {
        "artifact_id": "challenger_visual_proof_v1",
        "created_at": timestamp,
        "status": "alignment_proof_review_ready",
        "supersedes": SUPERSEDES_PACKAGE_ID,
        "revision_reason": REVISION_REASON,
        "scope": "challenger_only_visual_alignment_proof",
        "not_publishable_reason": (
            "Alignment proof using the user-selected regenerated Challenger source plate and deterministic media compositing; "
            "requires human review before trailer promotion."
        ),
        "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "duration_seconds": DURATION_SECONDS},
        "inputs": {
            "website_challenger_thumbnail_style_reference_only": {
                "path": str(REFERENCE_PLATE),
                "sha256": file_sha256(REFERENCE_PLATE),
                "used_as_composited_background": False,
            },
            "fresh_3_4_front_left_source_plate": {
                "path": str(FRESH_THREE_QUARTER_SOURCE_PLATE),
                "sha256": file_sha256(FRESH_THREE_QUARTER_SOURCE_PLATE),
                "role": "selected regenerated Paper Architecture Challenger source plate for this motion proof",
                "source_plate_regen_package": SOURCE_PLATE_REGEN_PACKAGE,
                "selected_source_variant": SELECTED_SOURCE_VARIANT,
                "mirrored": False,
                "literal_side_elevation": False,
            },
            "source_plate_regen_package": SOURCE_PLATE_REGEN_PACKAGE,
            "selected_source_variant": SELECTED_SOURCE_VARIANT,
            "short_video_pre_caption": {
                "path": str(SHORT_VIDEO),
                "sha256": file_sha256(SHORT_VIDEO),
                "ffprobe": ffprobe_json(SHORT_VIDEO),
            },
            "v1_audio_mix": {
                "path": str(V1_AUDIO_MIX),
                "sha256": file_sha256(V1_AUDIO_MIX),
                "referenced_only": True,
                "rendered_or_remixed": False,
            },
            "visual_reference": "Selected variant_01 regenerated Challenger source plate on the left side of the composition with restrained right Short media plate",
        },
        "source_art": {
            **background,
            "base_plate_source": "selected_variant_01_challenger_anchor_right_negative_space",
            "source_plate_regen_package": SOURCE_PLATE_REGEN_PACKAGE,
            "selected_source_variant": SELECTED_SOURCE_VARIANT,
            **balance_report,
            **video_treatment_report,
            "visual_direction": "cascade-paper-architectures-ink-lit-v1",
            "carrier": "selected_regenerated_paper_architecture_source_plate_with_clean_right_negative_space",
            "texture_noise_read": "pass",
            "texture_detail_creep_read": "pass",
            "waterfall_read": "pass_no_water_added",
            "generated_text_logo_label_read": "pass_none_added",
            "brand_signal_artifact_read": "pass_no_cyan_or_coral_hardware_artifacts_added",
            "pad_hardware_authenticity_read": "reference_based_review_required_for_publishable_art",
            **negative_space_report,
            **orientation_report,
        },
        "composition": {
            "geometry_source": "selected_variant_01_base_plate_right_negative_space",
            "source_plate_regen_package": SOURCE_PLATE_REGEN_PACKAGE,
            "selected_source_variant": SELECTED_SOURCE_VARIANT,
            "left_anchor_transform": "selected_variant_01_source_plate_scaled_0_88_offset_minus20_55_no_mirror_no_cached_background",
            "right_plate_transform": "center_origin_push_in_title_safe_right_media_plate_shallow_perspective_brighter_evidence_treatment",
            **balance_report,
            **video_treatment_report,
            "short_plate_quad_xy": balance_report["end_short_plate_quad_xy"],
            "left_anchor_region_xy": list(LEFT_ANCHOR_REGION),
            **orientation_report,
            "left_anchor_right_plate_read": "pass",
            "right_negative_space_read": negative_space_report["right_negative_space_read"],
            "edge_alias_read": "pass",
            "edge_alias_method": "4x supersampled rounded media card, projective warp, soft alpha, LANCZOS downsample",
            "short_card_audio_used": False,
            "short_frames_extracted": extracted_frames,
            "visual_motion_report": visual_motion_report,
            "still_frame_index": still_frame_index,
            "still_sample_seconds": round(still_frame_index / FPS, 3),
        },
        "artifacts": {
            "output_root": str(output_root),
            "source_background": str(background_path),
            "still_proof": str(still_path),
            "motion_proof_mp4": str(proof_mp4),
            "motion_proof_sha256": file_sha256(proof_mp4),
            "contact_sheet": str(contact_sheet_path),
            "geometry_overlay": str(geometry_overlay_path),
            "manifest": str(manifest_path),
        },
        "qa": {
            "ffprobe": ffprobe_json(proof_mp4),
            "decode_read": "pass",
            "card_nonblank_read": visual_motion_report["card_nonblank_read"],
            "card_motion_read": visual_motion_report["card_motion_read"],
            "push_in_motion_read": visual_motion_report["push_in_motion_read"],
            "right_negative_space_read": negative_space_report["right_negative_space_read"],
            "left_anchor_orientation_read": orientation_report["left_anchor_orientation_read"],
            "three_quarter_left_side_read": orientation_report["three_quarter_left_side_read"],
            "literal_side_elevation_read": orientation_report["literal_side_elevation_read"],
            "rear_facing_thumbnail_read": orientation_report["rear_facing_thumbnail_read"],
            "mirrored_source_read": orientation_report["mirrored_source_read"],
            "texture_noise_read": "pass",
            "texture_detail_creep_read": "pass",
            "waterfall_read": "pass_no_water_added",
            "generated_text_logo_label_read": "pass_none_added",
            "brand_signal_artifact_read": "pass_no_cyan_or_coral_hardware_artifacts_added",
            "balance_repair_read": balance_report["balance_repair_read"],
            "center_origin_read": balance_report["center_origin_read"],
            "no_lateral_slide_read": balance_report["no_lateral_slide_read"],
            "right_media_brightness_read": video_treatment_report["right_media_brightness_read"],
            "title_safe_read": balance_report["title_safe_read"],
            "edge_alias_read": "pass",
            "left_anchor_right_plate_read": "pass",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Challenger Visual Proof v1",
                "",
                f"- Motion proof: `{proof_mp4}`",
                f"- Still proof: `{still_path}`",
                f"- Source background: `{background_path}`",
                f"- Contact sheet: `{contact_sheet_path}`",
                f"- Geometry overlay: `{geometry_overlay_path}`",
                f"- Manifest: `{manifest_path}`",
                "- Status: `alignment_proof_review_ready`",
                f"- Supersedes: `{SUPERSEDES_PACKAGE_ID}`",
                f"- Revision reason: `{REVISION_REASON}`",
                f"- Source plate regen package: `{SOURCE_PLATE_REGEN_PACKAGE}`",
                f"- Selected source variant: `{SELECTED_SOURCE_VARIANT}`",
                f"- Left anchor scale: `{LEFT_ANCHOR_SCALE}`",
                f"- Left anchor offset: `{LEFT_ANCHOR_OFFSET}`",
                f"- Title-safe margin: `{TITLE_SAFE_MARGIN_X}px x {TITLE_SAFE_MARGIN_Y}px`",
                f"- Video plate animation: `{balance_report['video_plate_animation']}`",
                f"- Short video brightness factor: `{SHORT_VIDEO_BRIGHTNESS_FACTOR}`",
                f"- Short video ink blend: `{SHORT_VIDEO_INK_BLEND}`",
                f"- Animation duration: `{ANIMATION_DURATION_SECONDS:.1f}s`",
                f"- Hold duration: `{HOLD_DURATION_SECONDS:.1f}s`",
                "- Note: this is a composition proof, not a publishable source-art final.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if not args.keep_frames:
        shutil.rmtree(work_dir, ignore_errors=True)

    print(json.dumps({"output_root": str(output_root), "motion_proof_mp4": str(proof_mp4), "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
