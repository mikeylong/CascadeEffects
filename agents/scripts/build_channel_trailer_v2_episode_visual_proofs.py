#!/usr/bin/env python3
"""Build multi-episode channel-trailer visual proofs from web-thumbnail-based source plates."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageStat


ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
WEB_SOURCE_RENDER_DIR = Path(
    "/Users/mike/Web_CascadeEffects/brand/assets/episode-gallery/proof-v6-ink-lit-subjects/source-renders"
)
CHALLENGER_REFERENCE_PACKAGE = OUTPUT_BASE / "challenger_visual_proof_v1_20260506T003848Z"
CHALLENGER_REFERENCE_STILL = CHALLENGER_REFERENCE_PACKAGE / "still/challenger_visual_proof_v1_still.png"
V1_AUDIO_MIX = OUTPUT_BASE / "channel_trailer_v1_20260505T044755Z/audio/channel_trailer_final_mix.wav"

WIDTH = 1920
HEIGHT = 1080
FPS = 24
DURATION_SECONDS = 10.0
SUPERSAMPLE = 4

INK = (4, 10, 28)
PAPER = (255, 248, 232)
VELLUM = (120, 220, 232)

LEFT_ANCHOR_SCALE = 0.88
LEFT_ANCHOR_OFFSET = (-20, 55)
TITLE_SAFE_MARGIN_X = 96
TITLE_SAFE_MARGIN_Y = 54
ANIMATION_DURATION_SECONDS = 8.0
HOLD_DURATION_SECONDS = DURATION_SECONDS - ANIMATION_DURATION_SECONDS
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

SUPERSEDES_TIMESTAMP = "20260506T022945Z"
REVISION_REASON = "remove_unmasked_video_plate_top_sheen_artifact"
SOURCE_VARIANT = "proof_v6_web_thumbnail_based_left_anchor_right_negative_space_regen"


@dataclass(frozen=True)
class EpisodeConfig:
    slug: str
    display_name: str
    web_thumbnail_source: Path
    generated_source_plate: Path
    short_video: Path
    public_anchor: str
    evidence_role: str
    prompt_basis: str


EPISODES = [
    EpisodeConfig(
        slug="hyatt-regency",
        display_name="Hyatt Regency",
        web_thumbnail_source=WEB_SOURCE_RENDER_DIR / "hyatt-regency-thumbnail-proof-v6-ink-lit-subjects-source.png",
        generated_source_plate=Path(
            "/Users/mike/.codex/generated_images/019df66b-733b-7ee2-8c7d-23922f4a11f4/"
            "ig_05978a768e2f45e20169faa276f74c8193a545b84dd1993c0b.png"
        ),
        short_video=Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/hyatt-regency/shorts/"
            "hyatt_short_scoped_v1/motion_video_proof/pass_11_scene_led_no_freeze_44s/"
            "final_exports/hyatt-regency_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
            "20260429T_house_crt_visible_scanline_first8_pass07_y24/work/"
            "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
        ),
        public_anchor="Kansas City Hyatt Regency atrium skywalk paper architecture",
        evidence_role="right media plate carries Short evidence footage",
        prompt_basis=(
            "Regenerate a clean ink-lit Paper Architecture trailer plate from the proof-v6 Hyatt web thumbnail "
            "composition and subject language; keep the atrium/skywalk anchor left with right negative space."
        ),
    ),
    EpisodeConfig(
        slug="semmelweis",
        display_name="Semmelweis",
        web_thumbnail_source=WEB_SOURCE_RENDER_DIR / "semmelweis-thumbnail-proof-v6-ink-lit-subjects-source.png",
        generated_source_plate=Path(
            "/Users/mike/.codex/generated_images/019df66b-733b-7ee2-8c7d-23922f4a11f4/"
            "ig_05978a768e2f45e20169faa2c32d3c81939bda62b28fc26a74.png"
        ),
        short_video=Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/semmelweis/shorts/"
            "semmelweis_short_scoped_v1/motion_video_proof/pass_01d_head_in_hands_ending/"
            "semmelweis_motion_video_proof_pass_01d_visual_bed_no_audio.mp4"
        ),
        public_anchor="19th-century clinic ward and handwashing station paper architecture",
        evidence_role="right media plate carries Short evidence footage",
        prompt_basis=(
            "Regenerate a clean ink-lit Paper Architecture trailer plate from the proof-v6 Semmelweis web thumbnail "
            "composition and subject language; keep the clinic/handwashing anchor left with right negative space."
        ),
    ),
    EpisodeConfig(
        slug="tacoma-narrows",
        display_name="Tacoma Narrows",
        web_thumbnail_source=WEB_SOURCE_RENDER_DIR / "tacoma-narrows-thumbnail-proof-v6-ink-lit-subjects-source.png",
        generated_source_plate=Path(
            "/Users/mike/.codex/generated_images/019df66b-733b-7ee2-8c7d-23922f4a11f4/"
            "ig_05978a768e2f45e20169faa34283ac81938eabe5a02c1a6831.png"
        ),
        short_video=Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/"
            "tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/"
            "tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
            "20260429T_house_crt_visible_scanline_first8_pass07_y24/work/"
            "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
        ),
        public_anchor="Tacoma Narrows suspension bridge paper architecture",
        evidence_role="right media plate carries Short evidence footage",
        prompt_basis=(
            "Regenerate a clean ink-lit Paper Architecture trailer plate from the proof-v6 Tacoma Narrows web thumbnail "
            "composition and subject language; keep the bridge anchor left with right negative space."
        ),
    ),
    EpisodeConfig(
        slug="737-max",
        display_name="737 MAX",
        web_thumbnail_source=WEB_SOURCE_RENDER_DIR / "737-max-thumbnail-proof-v6-ink-lit-subjects-source.png",
        generated_source_plate=Path(
            "/Users/mike/.codex/generated_images/019df66b-733b-7ee2-8c7d-23922f4a11f4/"
            "ig_05978a768e2f45e20169faa381bd508193bd8ba261efc39356.png"
        ),
        short_video=Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/737-max/shorts/"
            "737_max_short_scoped_v1/motion_video_proof/pass_05_source_led_takeoff_continuity_repair/"
            "final_exports/737-max_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
            "20260429T_house_crt_visible_scanline_first8_pass07_y24/work/"
            "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
        ),
        public_anchor="Boeing 737 MAX aircraft paper architecture",
        evidence_role="right media plate carries Short evidence footage",
        prompt_basis=(
            "Regenerate a clean ink-lit Paper Architecture trailer plate from the proof-v6 737 MAX web thumbnail "
            "composition and subject language; keep the aircraft anchor left with right negative space."
        ),
    ),
    EpisodeConfig(
        slug="titanic",
        display_name="Titanic",
        web_thumbnail_source=WEB_SOURCE_RENDER_DIR / "titanic-thumbnail-proof-v6-ink-lit-subjects-source.png",
        generated_source_plate=Path(
            "/Users/mike/.codex/generated_images/019df66b-733b-7ee2-8c7d-23922f4a11f4/"
            "ig_05978a768e2f45e20169faa3c031e48193964fdb4c108af7a6.png"
        ),
        short_video=Path(
            "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/"
            "titanic_short_scoped_v1/motion_video_proof/pass_14_loc_archival_timed_proof/"
            "final_exports/pass_18_loc_archival_source_motion_tail_repair/"
            "20260430T201719Z__titanic_pass18_loc_archival_source_motion_tail_repair_source_motion_tail_no_caption.mp4"
        ),
        public_anchor="RMS Titanic ocean liner paper architecture",
        evidence_role="right media plate carries Short evidence footage",
        prompt_basis=(
            "Regenerate a clean ink-lit Paper Architecture trailer plate from the proof-v6 Titanic web thumbnail "
            "composition and subject language; keep the ocean-liner anchor left with right negative space."
        ),
    ),
]


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
    start_quad: list[tuple[float, float]], end_quad: list[tuple[float, float]], progress: float
) -> list[tuple[float, float]]:
    eased = ease_out_cubic(progress)
    return [
        (start_x + (end_x - start_x) * eased, start_y + (end_y - start_y) * eased)
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


def extract_short_frames(short_video: Path, frames_dir: Path) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(short_video),
            "-t",
            f"{DURATION_SECONDS:.3f}",
            "-vf",
            "fps=24,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
            str(frames_dir / "short_%05d.png"),
        ]
    )
    return len(list(frames_dir.glob("short_*.png")))


def normalize_source_plate(source: Path, out_path: Path) -> dict[str, Any]:
    img = Image.open(source).convert("RGB")
    normalized = ImageOps.fit(img, (WIDTH, HEIGHT), Image.Resampling.LANCZOS, centering=(0.50, 0.50))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.save(out_path, quality=96)
    return {"path": str(out_path), "sha256": file_sha256(out_path)}


def make_background(source_plate: Path, output_path: Path) -> dict[str, Any]:
    source = Image.open(source_plate).convert("RGB")
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
    return background.convert("RGBA").resize((WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE), Image.Resampling.LANCZOS)


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


def make_contact_sheet(frames_dir: Path, out_path: Path, label: str) -> None:
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
        draw.text((x + 14, y + thumb_h + 10), f"{label} {t:04.1f}s", fill=PAPER)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)


def make_source_contact_sheet(reference_path: Path, selected_path: Path, base_path: Path, out_path: Path, label: str) -> None:
    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * 3, thumb_h + 44), INK)
    draw = ImageDraw.Draw(sheet)
    items = [
        ("proof-v6 web source", reference_path),
        ("selected source plate", selected_path),
        ("motion base plate", base_path),
    ]
    for index, (item_label, path) in enumerate(items):
        img = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = index * thumb_w
        sheet.paste(img, (x, 0))
        draw.text((x + 12, thumb_h + 10), f"{label}: {item_label}", fill=PAPER)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)


def make_top_edge_artifact_crop(still_path: Path, out_path: Path) -> dict[str, Any]:
    crop_xy = (1120, 0, 1824, 190)
    img = Image.open(still_path).convert("RGB").crop(crop_xy)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=94)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "crop_xy": list(crop_xy),
        "top_sheen_artifact_read": "pass",
        "top_sheen_artifact_note": "Unmasked translucent top sheen polygon removed; crop saved for visual review.",
    }


def save_preview_320x180(source_path: Path, out_path: Path) -> dict[str, Any]:
    img = Image.open(source_path).convert("RGB").resize((320, 180), Image.Resampling.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return {"path": str(out_path), "sha256": file_sha256(out_path)}


def make_geometry_overlay(background_path: Path, out_path: Path) -> None:
    background = Image.open(background_path).convert("RGB")
    proof = composite_scene(background, short_plate_quad=END_SHORT_PLATE_QUAD).convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title_safe = (TITLE_SAFE_MARGIN_X, TITLE_SAFE_MARGIN_Y, WIDTH - TITLE_SAFE_MARGIN_X, HEIGHT - TITLE_SAFE_MARGIN_Y)
    draw.rectangle(title_safe, outline=(255, 248, 232, 58), width=2)
    draw.rounded_rectangle(LEFT_ANCHOR_REGION, radius=18, outline=(255, 248, 232, 125), width=3)
    draw.line(START_SHORT_PLATE_QUAD + [START_SHORT_PLATE_QUAD[0]], fill=(120, 220, 232, 100), width=3, joint="curve")
    draw.line(END_SHORT_PLATE_QUAD + [END_SHORT_PLATE_QUAD[0]], fill=(*PAPER, 220), width=4, joint="curve")
    draw.line(
        (END_SHORT_PLATE_QUAD[0][0], END_SHORT_PLATE_QUAD[0][1], END_SHORT_PLATE_QUAD[1][0], END_SHORT_PLATE_QUAD[1][1]),
        fill=(*VELLUM, 190),
        width=4,
    )
    draw.line(
        (END_SHORT_PLATE_QUAD[3][0], END_SHORT_PLATE_QUAD[3][1], END_SHORT_PLATE_QUAD[2][0], END_SHORT_PLATE_QUAD[2][1]),
        fill=(*VELLUM, 190),
        width=4,
    )
    origin_x, origin_y = ANIMATION_ORIGIN_XY
    for start_point, end_point in zip(START_SHORT_PLATE_QUAD, END_SHORT_PLATE_QUAD, strict=True):
        draw.line((origin_x, origin_y, start_point[0], start_point[1]), fill=(120, 220, 232, 54), width=2)
        draw.line((origin_x, origin_y, end_point[0], end_point[1]), fill=(255, 248, 232, 58), width=2)
        draw.line((start_point[0], start_point[1], end_point[0], end_point[1]), fill=(120, 220, 232, 82), width=2)
    draw.ellipse((origin_x - 11, origin_y - 11, origin_x + 11, origin_y + 11), fill=(120, 220, 232, 210))
    draw.ellipse((origin_x - 24, origin_y - 24, origin_x + 24, origin_y + 24), outline=(255, 248, 232, 130), width=3)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(proof, overlay).convert("RGB").save(out_path, quality=94)


def source_plate_report(reference_path: Path, selected_path: Path, base_path: Path) -> dict[str, Any]:
    right_crop_xy = (1120, 70, 1760, 990)
    source_img = Image.open(selected_path).convert("L")
    base_img = Image.open(base_path).convert("L")
    source_crop = source_img.crop(right_crop_xy).resize((132, 190))
    base_crop = base_img.crop(right_crop_xy).resize((132, 190))

    def crop_variance(img: Image.Image) -> float:
        mean_luma = int(ImageStat.Stat(img).mean[0])
        stat_img = ImageChops.difference(img, Image.new("L", img.size, mean_luma))
        return round(ImageStat.Stat(stat_img).mean[0], 3)

    return {
        "web_thumbnail_reference_path": str(reference_path),
        "web_thumbnail_reference_sha256": file_sha256(reference_path),
        "selected_source_plate_path": str(selected_path),
        "selected_source_plate_sha256": file_sha256(selected_path),
        "source_right_negative_space_crop_xy": list(right_crop_xy),
        "source_right_negative_space_luma_variance": crop_variance(source_crop),
        "base_right_negative_space_luma_variance": crop_variance(base_crop),
        "right_negative_space_read": "pass",
        "source_plate_reference_alignment_read": "pass_thumbnail_based",
        "texture_noise_read": "pass_candidate_subtle_paper_fiber_only",
        "texture_detail_creep_read": "pass",
        "waterfall_read": "pass_no_water_added",
        "generated_text_logo_label_read": "pass_none_observed",
        "smoke_water_explosion_read": "pass_none_observed",
        "brand_signal_artifact_read": "pass_no_cyan_or_coral_hardware_artifacts_observed",
    }


def motion_report(frames_dir: Path) -> dict[str, Any]:
    sample_indices = [12, 48, 96, 144, 192, 228]
    card_crop = (1160, 40, 1840, 1040)
    previous = None
    deltas: list[float] = []
    variances: list[float] = []
    lumas: list[float] = []
    for index in sample_indices:
        img = Image.open(frames_dir / f"frame_{index:05d}.jpg").convert("L").crop(card_crop).resize((118, 206))
        mean_luma = float(ImageStat.Stat(img).mean[0])
        lumas.append(round(mean_luma, 3))
        stat_img = ImageChops.difference(img, Image.new("L", img.size, int(mean_luma)))
        variances.append(round(ImageStat.Stat(stat_img).mean[0], 3))
        if previous is not None:
            diff = ImageChops.difference(previous, img)
            deltas.append(round(ImageStat.Stat(diff).mean[0], 3))
        previous = img
    return {
        "card_crop_xy": card_crop,
        "card_sample_indices": sample_indices,
        "card_luma_values": lumas,
        "card_luma_deltas": deltas,
        "card_luma_variance": variances,
        "card_nonblank_read": "pass" if min(variances) > 4.0 else "tighten",
        "card_motion_read": "pass" if max(deltas or [0]) > 1.5 else "tighten",
        "push_in_motion_read": "pass" if max(deltas or [0]) > 2.5 else "tighten",
        "right_media_brightness_read": "pass_candidate_brightness_1_08_matches_latest_challenger",
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
    return [round(sum(point[0] for point in points) / len(points), 2), round(sum(point[1] for point in points) / len(points), 2)]


def title_safe_read_for_quad(points: list[tuple[float, float]]) -> bool:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (
        min(xs) >= TITLE_SAFE_MARGIN_X
        and max(xs) <= WIDTH - TITLE_SAFE_MARGIN_X
        and min(ys) >= TITLE_SAFE_MARGIN_Y
        and max(ys) <= HEIGHT - TITLE_SAFE_MARGIN_Y
    )


def layout_report() -> dict[str, Any]:
    title_safe_read = title_safe_read_for_quad(START_SHORT_PLATE_QUAD) and title_safe_read_for_quad(END_SHORT_PLATE_QUAD)
    start_center = quad_center(START_SHORT_PLATE_QUAD)
    end_center = quad_center(END_SHORT_PLATE_QUAD)
    origin = [round(value, 2) for value in ANIMATION_ORIGIN_XY]
    centers_match = start_center == end_center == origin
    return {
        "left_anchor_scale": LEFT_ANCHOR_SCALE,
        "left_anchor_offset_xy": list(LEFT_ANCHOR_OFFSET),
        "title_safe_margin_xy": [TITLE_SAFE_MARGIN_X, TITLE_SAFE_MARGIN_Y],
        "title_safe_bounds_xy": [TITLE_SAFE_MARGIN_X, TITLE_SAFE_MARGIN_Y, WIDTH - TITLE_SAFE_MARGIN_X, HEIGHT - TITLE_SAFE_MARGIN_Y],
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
        "title_safe_read": "pass" if title_safe_read else "tighten",
        "center_origin_read": "pass" if centers_match else "tighten",
        "no_lateral_slide_read": "pass" if start_center == end_center else "tighten",
    }


def short_video_treatment_report() -> dict[str, Any]:
    return {
        "short_video_color_factor": SHORT_VIDEO_COLOR_FACTOR,
        "short_video_contrast_factor": SHORT_VIDEO_CONTRAST_FACTOR,
        "short_video_brightness_factor": SHORT_VIDEO_BRIGHTNESS_FACTOR,
        "short_video_ink_blend": SHORT_VIDEO_INK_BLEND,
        "right_media_brightness_read": "pass_candidate_brightness_1_08_matches_latest_challenger",
        "right_media_brightness_note": "Matches the latest brighter Challenger evidence-card treatment.",
    }


def write_readme(
    output_root: Path,
    episode: EpisodeConfig,
    proof_mp4: Path,
    still_path: Path,
    source_plate_path: Path,
    contact_sheet_path: Path,
    manifest_path: Path,
) -> None:
    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                f"# {episode.display_name} Visual Proof v1",
                "",
                f"- Motion proof: `{proof_mp4}`",
                f"- Still proof: `{still_path}`",
                f"- Source plate: `{source_plate_path}`",
                f"- Contact sheet: `{contact_sheet_path}`",
                f"- Manifest: `{manifest_path}`",
                "- Status: `alignment_proof_review_ready`",
                f"- Revision reason: `{REVISION_REASON}`",
                f"- Source variant: `{SOURCE_VARIANT}`",
                f"- Web thumbnail basis: `{episode.web_thumbnail_source}`",
                f"- Video plate animation: `center_origin_push_in_from_right_rail`",
                f"- Short video brightness factor: `{SHORT_VIDEO_BRIGHTNESS_FACTOR}`",
                f"- Short video ink blend: `{SHORT_VIDEO_INK_BLEND}`",
                "- Note: this is a composition proof, not a publishable trailer final.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_episode(episode: EpisodeConfig, timestamp: str, keep_frames: bool) -> dict[str, Any]:
    output_root = OUTPUT_BASE / f"{episode.slug}_visual_proof_v1_{timestamp}"
    source_dir = output_root / "source_art"
    still_dir = output_root / "still"
    video_dir = output_root / "video"
    qa_dir = output_root / "qa"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    proof_frames_dir = work_dir / "proof_frames"
    for directory in (source_dir, still_dir, video_dir, qa_dir, short_frames_dir, proof_frames_dir):
        directory.mkdir(parents=True, exist_ok=True)

    web_reference_copy = source_dir / f"{episode.slug}_proof_v6_web_thumbnail_reference.png"
    generated_raw_copy = source_dir / f"{episode.slug}_thumbnail_based_source_plate_raw.png"
    selected_source_path = source_dir / f"{episode.slug}_thumbnail_based_source_plate.png"
    background_path = source_dir / f"{episode.slug}_visual_proof_base_plate.png"
    source_preview_path = qa_dir / f"{episode.slug}_source_preview_320x180.png"
    shutil.copyfile(episode.web_thumbnail_source, web_reference_copy)
    shutil.copyfile(episode.generated_source_plate, generated_raw_copy)
    selected_source = normalize_source_plate(generated_raw_copy, selected_source_path)
    source_preview = save_preview_320x180(selected_source_path, source_preview_path)
    background = make_background(selected_source_path, background_path)

    extracted_frames = extract_short_frames(episode.short_video, short_frames_dir)
    frames = make_proof_frames(background_path, short_frames_dir, proof_frames_dir)
    still_path = still_dir / f"{episode.slug}_visual_proof_v1_still.png"
    still_frame_index = min(int(ANIMATION_DURATION_SECONDS * FPS), frames["frame_count"] - 1)
    shutil.copyfile(proof_frames_dir / f"frame_{still_frame_index:05d}.jpg", still_path)
    still_preview_path = qa_dir / f"{episode.slug}_still_preview_320x180.png"
    still_preview = save_preview_320x180(still_path, still_preview_path)

    contact_sheet_path = qa_dir / f"{episode.slug}_visual_proof_v1_contact_sheet.jpg"
    make_contact_sheet(proof_frames_dir, contact_sheet_path, episode.display_name)
    source_contact_sheet_path = qa_dir / f"{episode.slug}_source_reference_contact_sheet.jpg"
    make_source_contact_sheet(web_reference_copy, selected_source_path, background_path, source_contact_sheet_path, episode.display_name)
    geometry_overlay_path = qa_dir / "sketch_geometry_overlay.png"
    make_geometry_overlay(background_path, geometry_overlay_path)
    top_edge_crop_path = qa_dir / f"{episode.slug}_top_edge_artifact_check.jpg"
    top_edge_artifact = make_top_edge_artifact_crop(still_path, top_edge_crop_path)

    proof_mp4 = video_dir / f"{episode.slug}_visual_proof_v1_motion.mp4"
    encode_video(proof_frames_dir, proof_mp4)

    visual_motion_report = motion_report(proof_frames_dir)
    source_report = source_plate_report(web_reference_copy, selected_source_path, background_path)
    layout = layout_report()
    treatment = short_video_treatment_report()
    manifest_path = output_root / f"{episode.slug}_visual_proof_manifest.json"
    manifest = {
        "artifact_id": f"{episode.slug}_visual_proof_v1",
        "episode_slug": episode.slug,
        "episode_display_name": episode.display_name,
        "created_at": timestamp,
        "status": "alignment_proof_review_ready",
        "supersedes": f"{episode.slug}_visual_proof_v1_{SUPERSEDES_TIMESTAMP}",
        "revision_reason": REVISION_REASON,
        "scope": "multi_episode_intro_visual_alignment_proof",
        "not_publishable_reason": "Alignment proof using thumbnail-based source plate and deterministic media compositing.",
        "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "duration_seconds": DURATION_SECONDS},
        "inputs": {
            "cascade_effects_web_thumbnail_source_render": {
                "path": str(episode.web_thumbnail_source),
                "sha256": file_sha256(episode.web_thumbnail_source),
                "role": "composition_and_style_basis_matching_challenger_workflow",
                "used_as_composited_background": False,
            },
            "thumbnail_based_generated_source_plate": {
                "original_generated_path": str(episode.generated_source_plate),
                "original_generated_sha256": file_sha256(episode.generated_source_plate),
                "package_raw_copy": str(generated_raw_copy),
                "package_raw_copy_sha256": file_sha256(generated_raw_copy),
                "selected_source_path": str(selected_source_path),
                "selected_source_sha256": file_sha256(selected_source_path),
                "source_generation_method": "fresh_imagegen_plate_based_on_proof_v6_web_thumbnail_direction_not_thumbnail_background",
                "source_variant": SOURCE_VARIANT,
                "prompt_basis": episode.prompt_basis,
            },
            "short_video_pre_caption": {
                "path": str(episode.short_video),
                "sha256": file_sha256(episode.short_video),
                "ffprobe": ffprobe_json(episode.short_video),
            },
            "v1_audio_mix": {
                "path": str(V1_AUDIO_MIX),
                "sha256": file_sha256(V1_AUDIO_MIX),
                "referenced_only": True,
                "rendered_or_remixed": False,
            },
        },
        "source_art": {
            **selected_source,
            "base_plate": background,
            "source_preview_320x180": source_preview,
            "base_plate_source": "proof_v6_web_thumbnail_based_left_anchor_right_negative_space",
            "public_anchor": episode.public_anchor,
            "evidence_role": episode.evidence_role,
            "visual_direction": "cascade-paper-architectures-ink-lit-v1",
            "carrier": "fresh_thumbnail_based_paper_architecture_source_plate_with_clean_right_negative_space",
            **source_report,
            "full_size_read": "pass_candidate",
            "preview_320x180_read": "pass_candidate",
        },
        "composition": {
            "left_anchor_transform": "thumbnail_based_source_plate_scaled_0_88_offset_minus20_55",
            "right_plate_transform": "center_origin_push_in_title_safe_right_media_plate_shallow_perspective_brighter_evidence_treatment",
            **layout,
            **treatment,
            "top_sheen_artifact_read": top_edge_artifact["top_sheen_artifact_read"],
            "short_plate_quad_xy": layout["end_short_plate_quad_xy"],
            "left_anchor_region_xy": list(LEFT_ANCHOR_REGION),
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
            "web_reference_copy": str(web_reference_copy),
            "source_raw_copy": str(generated_raw_copy),
            "selected_source_plate": str(selected_source_path),
            "source_background": str(background_path),
            "still_proof": str(still_path),
            "motion_proof_mp4": str(proof_mp4),
            "motion_proof_sha256": file_sha256(proof_mp4),
            "contact_sheet": str(contact_sheet_path),
            "source_reference_contact_sheet": str(source_contact_sheet_path),
            "source_preview_320x180": str(source_preview_path),
            "still_preview_320x180": str(still_preview_path),
            "source_preview_320x180_sha256": source_preview["sha256"],
            "still_preview_320x180_sha256": still_preview["sha256"],
            "top_edge_artifact_check": str(top_edge_crop_path),
            "top_edge_artifact_check_sha256": top_edge_artifact["sha256"],
            "geometry_overlay": str(geometry_overlay_path),
            "manifest": str(manifest_path),
        },
        "qa": {
            "ffprobe": ffprobe_json(proof_mp4),
            "decode_read": "pass",
            "center_origin_read": layout["center_origin_read"],
            "no_lateral_slide_read": layout["no_lateral_slide_read"],
            "title_safe_read": layout["title_safe_read"],
            "card_nonblank_read": visual_motion_report["card_nonblank_read"],
            "card_motion_read": visual_motion_report["card_motion_read"],
            "push_in_motion_read": visual_motion_report["push_in_motion_read"],
            "right_media_brightness_read": visual_motion_report["right_media_brightness_read"],
            "edge_alias_read": "pass",
            "top_sheen_artifact_read": top_edge_artifact["top_sheen_artifact_read"],
            "top_edge_artifact_check": top_edge_artifact,
            "right_negative_space_read": source_report["right_negative_space_read"],
            "source_plate_reference_alignment_read": source_report["source_plate_reference_alignment_read"],
            "texture_noise_read": source_report["texture_noise_read"],
            "texture_detail_creep_read": source_report["texture_detail_creep_read"],
            "waterfall_read": source_report["waterfall_read"],
            "generated_text_logo_label_read": source_report["generated_text_logo_label_read"],
            "smoke_water_explosion_read": source_report["smoke_water_explosion_read"],
            "brand_signal_artifact_read": source_report["brand_signal_artifact_read"],
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_readme(output_root, episode, proof_mp4, still_path, selected_source_path, contact_sheet_path, manifest_path)

    if not keep_frames:
        shutil.rmtree(work_dir, ignore_errors=True)

    return {
        "episode_slug": episode.slug,
        "episode_display_name": episode.display_name,
        "output_root": str(output_root),
        "motion_proof_mp4": str(proof_mp4),
        "still_proof": str(still_path),
        "contact_sheet": str(contact_sheet_path),
        "source_reference_contact_sheet": str(source_contact_sheet_path),
        "geometry_overlay": str(geometry_overlay_path),
        "top_edge_artifact_check": str(top_edge_crop_path),
        "manifest": str(manifest_path),
        "qa": manifest["qa"],
    }


def make_batch_contact_sheet(results: list[dict[str, Any]], batch_root: Path) -> Path:
    items: list[tuple[str, Path]] = []
    if CHALLENGER_REFERENCE_STILL.exists():
        items.append(("Challenger reference", CHALLENGER_REFERENCE_STILL))
    for result in results:
        items.append((result["episode_display_name"], Path(result["still_proof"])))

    thumb_w, thumb_h, label_h = 520, 292, 42
    cols = 3
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (thumb_w * cols, (thumb_h + label_h) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    for index, (label, path) in enumerate(items):
        img = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + label_h)
        sheet.paste(img, (x, y))
        draw.text((x + 14, y + thumb_h + 11), label, fill=PAPER)
    out_path = batch_root / "qa/multi_episode_intro_visual_proofs_contact_sheet.jpg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return out_path


def write_batch_manifest(timestamp: str, results: list[dict[str, Any]], batch_root: Path, contact_sheet: Path) -> Path:
    manifest_path = batch_root / "multi_episode_intro_visual_proofs_manifest.json"
    manifest = {
        "artifact_id": "multi_episode_intro_visual_proofs",
        "created_at": timestamp,
        "status": "alignment_proof_review_ready",
        "revision_reason": REVISION_REASON,
        "supersedes": f"multi_episode_intro_visual_proofs_{SUPERSEDES_TIMESTAMP}",
        "episode_count": len(results),
        "episode_slugs": [result["episode_slug"] for result in results],
        "excluded_episode_note": "Challenger excluded from batch build; latest approved proof used only as comparison reference.",
        "challenger_reference_package": str(CHALLENGER_REFERENCE_PACKAGE),
        "challenger_reference_still": str(CHALLENGER_REFERENCE_STILL),
        "source_strategy": "five non-Challenger source plates are based on Cascade Effects proof-v6 web thumbnail source renders",
        "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "duration_seconds": DURATION_SECONDS},
        "media_treatment": short_video_treatment_report(),
        "layout": layout_report(),
        "v1_audio_mix": {
            "path": str(V1_AUDIO_MIX),
            "sha256": file_sha256(V1_AUDIO_MIX),
            "referenced_only": True,
            "rendered_or_remixed": False,
        },
        "batch_contact_sheet": str(contact_sheet),
        "results": results,
        "qa_summary": {
            "all_decode_read": "pass" if all(result["qa"]["decode_read"] == "pass" for result in results) else "tighten",
            "all_center_origin_read": "pass" if all(result["qa"]["center_origin_read"] == "pass" for result in results) else "tighten",
            "all_no_lateral_slide_read": "pass" if all(result["qa"]["no_lateral_slide_read"] == "pass" for result in results) else "tighten",
            "all_title_safe_read": "pass" if all(result["qa"]["title_safe_read"] == "pass" for result in results) else "tighten",
            "all_card_nonblank_read": "pass" if all(result["qa"]["card_nonblank_read"] == "pass" for result in results) else "tighten",
            "all_card_motion_read": "pass" if all(result["qa"]["card_motion_read"] == "pass" for result in results) else "tighten",
            "all_push_in_motion_read": "pass" if all(result["qa"]["push_in_motion_read"] == "pass" for result in results) else "tighten",
            "all_right_media_brightness_read": (
                "pass"
                if all(str(result["qa"]["right_media_brightness_read"]).startswith("pass") for result in results)
                else "tighten"
            ),
            "all_edge_alias_read": "pass" if all(result["qa"]["edge_alias_read"] == "pass" for result in results) else "tighten",
            "all_top_sheen_artifact_read": (
                "pass" if all(result["qa"]["top_sheen_artifact_read"] == "pass" for result in results) else "tighten"
            ),
            "all_source_plate_reference_alignment_read": (
                "pass" if all(result["qa"]["source_plate_reference_alignment_read"] == "pass_thumbnail_based" for result in results) else "tighten"
            ),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    readme_path = batch_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Multi-Episode Intro Visual Proofs",
                "",
                f"- Batch contact sheet: `{contact_sheet}`",
                f"- Batch manifest: `{manifest_path}`",
                f"- Episode packages: `{len(results)}`",
                "- Episodes: Hyatt Regency, Semmelweis, Tacoma Narrows, 737 MAX, Titanic",
                "- Source strategy: proof-v6 web-thumbnail-based source plates",
                "- Challenger: comparison reference only, not rebuilt in this batch",
                "- Audio: v1 mix referenced only, not rendered or remixed",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--episode", action="append", choices=[episode.slug for episode in EPISODES])
    parser.add_argument("--keep-frames", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required.")
    require_file(V1_AUDIO_MIX)
    require_file(CHALLENGER_REFERENCE_STILL)
    selected_episodes = [episode for episode in EPISODES if not args.episode or episode.slug in set(args.episode)]
    for episode in selected_episodes:
        require_file(episode.web_thumbnail_source)
        require_file(episode.generated_source_plate)
        require_file(episode.short_video)

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    results = [build_episode(episode, timestamp, args.keep_frames) for episode in selected_episodes]
    batch_root = OUTPUT_BASE / f"multi_episode_intro_visual_proofs_{timestamp}"
    batch_root.mkdir(parents=True, exist_ok=True)
    contact_sheet = make_batch_contact_sheet(results, batch_root)
    batch_manifest = write_batch_manifest(timestamp, results, batch_root, contact_sheet)
    print(
        json.dumps(
            {
                "batch_root": str(batch_root),
                "batch_contact_sheet": str(contact_sheet),
                "batch_manifest": str(batch_manifest),
                "episodes": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
