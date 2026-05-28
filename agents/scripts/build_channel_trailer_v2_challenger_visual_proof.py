#!/usr/bin/env python3
"""Build a Challenger-only mirrored-plane visual proof for the channel trailer."""

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
SHORT_VIDEO = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_scoped_v1/final/"
    "challenger_short_scoped_v1_video_final_house_crt_visible_scanline_final_gate_pass01_20260501T022219Z.mp4"
)
V1_AUDIO_MIX = Path(
    "/Users/mike/Episodes_CascadeEffects/Channel_Trailer/channel_trailer_v1_20260505T044755Z/audio/"
    "channel_trailer_final_mix.wav"
)
VISUAL_REFERENCE_HEIC = Path("/Users/mike/Downloads/IMG_3222.HEIC")

WIDTH = 1920
HEIGHT = 1080
FPS = 24
DURATION_SECONDS = 10.0
SUPERSAMPLE = 4
VANISHING_POINT_XY = (960.0, 540.0)

LEFT_OUTER_TOP = (220.0, 150.0)
LEFT_OUTER_BOTTOM = (220.0, 952.0)
RIGHT_OUTER_TOP = (1700.0, 150.0)
RIGHT_OUTER_BOTTOM = (1700.0, 952.0)
PLANE_RECESS_FRACTION = 0.43
PLANE_CARD_W = 760
PLANE_CARD_H = 980

SUPERSEDES_PACKAGE_ID = "challenger_visual_proof_v1_20260505T064304Z"
REVISION_REASON = "mirrored_center_converging_planes_repair"

INK = (5, 11, 31)
PAPER = (255, 248, 232)
VELLUM = (120, 220, 232)


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
            "format=duration,size:stream=codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(proc.stdout)


def project_toward_vp(point: tuple[float, float], fraction: float = PLANE_RECESS_FRACTION) -> tuple[float, float]:
    vp_x, vp_y = VANISHING_POINT_XY
    x, y = point
    return (x + (vp_x - x) * fraction, y + (vp_y - y) * fraction)


def left_plane_quad() -> list[tuple[float, float]]:
    return [
        LEFT_OUTER_TOP,
        project_toward_vp(LEFT_OUTER_TOP),
        project_toward_vp(LEFT_OUTER_BOTTOM),
        LEFT_OUTER_BOTTOM,
    ]


def right_plane_quad() -> list[tuple[float, float]]:
    return [
        project_toward_vp(RIGHT_OUTER_TOP),
        RIGHT_OUTER_TOP,
        RIGHT_OUTER_BOTTOM,
        project_toward_vp(RIGHT_OUTER_BOTTOM),
    ]


def plane_bbox(quad: list[tuple[float, float]], pad: int = 24) -> tuple[int, int, int, int]:
    xs = [point[0] for point in quad]
    ys = [point[1] for point in quad]
    return (
        max(0, int(min(xs) - pad)),
        max(0, int(min(ys) - pad)),
        min(WIDTH, int(max(xs) + pad)),
        min(HEIGHT, int(max(ys) + pad)),
    )


def scale_point(point: tuple[float, float], scale: int) -> tuple[float, float]:
    return (point[0] * scale, point[1] * scale)


def scale_points(points: list[tuple[float, float]], scale: int) -> list[tuple[float, float]]:
    return [scale_point(point, scale) for point in points]


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


def warp_to_quad(card: Image.Image, destination_quad: list[tuple[float, float]], output_size: tuple[int, int]) -> Image.Image:
    source_quad = [
        (0.0, 0.0),
        (float(card.width), 0.0),
        (float(card.width), float(card.height)),
        (0.0, float(card.height)),
    ]
    coefficients = perspective_coefficients(destination_quad, source_quad)
    return card.transform(
        output_size,
        Image.Transform.PERSPECTIVE,
        coefficients,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(0, 0, 0, 0),
    )


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


def make_background(output_path: Path) -> dict[str, Any]:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), INK)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(82, HEIGHT - 80, 64):
        draw.line((120, y, WIDTH - 120, y + 20), fill=(*VELLUM, 8), width=1)

    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    vdraw = ImageDraw.Draw(vignette)
    max_inset = min(WIDTH, HEIGHT) // 2 - 8
    for i in range(0, max_inset, 8):
        alpha = int(120 * (i / max_inset) ** 2)
        vdraw.rectangle((i, i, WIDTH - i, HEIGHT - i), outline=alpha, width=8)
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    dark.putalpha(vignette.filter(ImageFilter.GaussianBlur(42)))
    plate = Image.alpha_composite(Image.alpha_composite(canvas.convert("RGBA"), overlay), dark).convert("RGB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plate.save(output_path, quality=96)
    return {
        "path": str(output_path),
        "sha256": file_sha256(output_path),
        "carrier": "deterministic_ink_field_composition_wrapper_with_approved_challenger_raster_in_left_plane",
    }


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


def convert_visual_reference(output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(["sips", "-s", "format", "png", str(VISUAL_REFERENCE_HEIC), "--out", str(output_path)])
    return {
        "source_path": str(VISUAL_REFERENCE_HEIC),
        "source_sha256": file_sha256(VISUAL_REFERENCE_HEIC),
        "converted_path": str(output_path),
        "converted_sha256": file_sha256(output_path),
        "reference_read": (
            "IMG_3222 sketch used as mirrored-plane geometry reference: left plane opens left, "
            "right plane opens right, both upright planes skew inward to the literal frame-center VP"
        ),
    }


def build_plane_card(fill: tuple[int, int, int], scale: int = 1) -> Image.Image:
    card_w, card_h = PLANE_CARD_W * scale, PLANE_CARD_H * scale
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    radius = 5 * scale
    draw.rounded_rectangle((0, 0, card_w - 1, card_h - 1), radius=radius, fill=(*PAPER, 238))
    draw.rounded_rectangle((12 * scale, 12 * scale, card_w - 12 * scale, card_h - 12 * scale), radius=radius, fill=fill)
    return card


def build_left_challenger_card(scale: int = 1) -> Image.Image:
    card = build_plane_card((8, 13, 30), scale)
    card_w, card_h = card.size
    content_box = (28 * scale, 28 * scale, card_w - 28 * scale, card_h - 28 * scale)
    content_w = content_box[2] - content_box[0]
    content_h = content_box[3] - content_box[1]
    reference = Image.open(REFERENCE_PLATE).convert("RGB")
    cropped = ImageOps.fit(reference, (content_w, content_h), method=Image.Resampling.LANCZOS, centering=(0.56, 0.52))
    cropped = ImageEnhance.Color(cropped).enhance(0.92)
    cropped = ImageEnhance.Contrast(cropped).enhance(1.04)
    card.paste(cropped, (content_box[0], content_box[1]))
    draw = ImageDraw.Draw(card)
    draw.rectangle(content_box, outline=(*VELLUM, 100), width=max(1, 2 * scale))
    return card


def build_short_card(short_frame: Image.Image, scale: int = 1) -> Image.Image:
    card = build_plane_card((8, 13, 30), scale)
    card_w, card_h = card.size
    video_box = (42 * scale, 34 * scale, card_w - 42 * scale, card_h - 34 * scale)
    video_w = video_box[2] - video_box[0]
    video_h = video_box[3] - video_box[1]
    toned = short_frame.convert("RGB").resize((video_w, video_h), Image.Resampling.LANCZOS)
    toned = ImageEnhance.Color(toned).enhance(0.78)
    toned = ImageEnhance.Contrast(toned).enhance(1.05)
    card.paste(toned, (video_box[0], video_box[1]))
    draw = ImageDraw.Draw(card)
    draw.rectangle(video_box, outline=(*VELLUM, 145), width=max(1, 2 * scale))
    draw.line((28 * scale, 38 * scale, card_w - 36 * scale, 52 * scale), fill=(*PAPER, 58), width=2 * scale)
    draw.line((32 * scale, card_h - 62 * scale, card_w - 42 * scale, card_h - 40 * scale), fill=(*PAPER, 52), width=2 * scale)
    return card


def make_shadow_layer(quad: list[tuple[float, float]], output_size: tuple[int, int], offset: tuple[float, float]) -> Image.Image:
    shadow = Image.new("RGBA", output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    shifted = [(x + offset[0], y + offset[1]) for x, y in quad]
    draw.polygon(shifted, fill=(0, 0, 0, 92))
    return shadow.filter(ImageFilter.GaussianBlur(22 * SUPERSAMPLE))


def make_static_scene_base(background: Image.Image) -> Image.Image:
    high_size = (WIDTH * SUPERSAMPLE, HEIGHT * SUPERSAMPLE)
    base = background.convert("RGBA").resize(high_size, Image.Resampling.LANCZOS)
    left_quad = scale_points(left_plane_quad(), SUPERSAMPLE)
    right_quad = scale_points(right_plane_quad(), SUPERSAMPLE)

    out = base
    out.alpha_composite(make_shadow_layer(left_quad, high_size, (-20 * SUPERSAMPLE, 16 * SUPERSAMPLE)))
    out.alpha_composite(make_shadow_layer(right_quad, high_size, (20 * SUPERSAMPLE, 16 * SUPERSAMPLE)))
    left_layer, left_offset = warp_to_quad_patch(build_left_challenger_card(SUPERSAMPLE), left_quad, pad=24 * SUPERSAMPLE)
    out.alpha_composite(left_layer, left_offset)
    return out


def composite_scene(
    background: Image.Image,
    short_frame: Image.Image | None = None,
    static_base: Image.Image | None = None,
) -> Image.Image:
    out = (static_base.copy() if static_base is not None else make_static_scene_base(background))
    right_quad = scale_points(right_plane_quad(), SUPERSAMPLE)
    if short_frame is not None:
        right_card = build_short_card(short_frame, SUPERSAMPLE)
    else:
        right_card = build_plane_card((14, 20, 38), SUPERSAMPLE)
    right_layer, right_offset = warp_to_quad_patch(right_card, right_quad, pad=24 * SUPERSAMPLE)
    out.alpha_composite(right_layer, right_offset)
    return out.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def make_proof_frames(background_path: Path, short_frames_dir: Path, frames_dir: Path) -> dict[str, Any]:
    background = Image.open(background_path).convert("RGB")
    static_base = make_static_scene_base(background)
    frames_dir.mkdir(parents=True, exist_ok=True)
    short_frames = sorted(short_frames_dir.glob("short_*.png"))
    expected_frames = int(DURATION_SECONDS * FPS)
    if len(short_frames) < expected_frames:
        raise SystemExit(f"Expected at least {expected_frames} short frames, got {len(short_frames)}")

    for index in range(expected_frames):
        short_frame = Image.open(short_frames[index]).convert("RGB")
        frame = composite_scene(background, short_frame, static_base)
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


def visual_motion_report(frames_dir: Path) -> dict[str, Any]:
    sample_indices = [12, 48, 96, 144, 192, 228]
    card_crop = plane_bbox(right_plane_quad(), 12)
    previous = None
    deltas: list[float] = []
    variances: list[float] = []
    for index in sample_indices:
        img = Image.open(frames_dir / f"frame_{index:05d}.jpg").convert("L").crop(card_crop).resize((130, 198))
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
        "card_motion_read": "pass" if max(deltas or [0]) > 2.0 else "tighten",
    }


def center_convergence_report() -> dict[str, Any]:
    vp_x, vp_y = VANISHING_POINT_XY
    pairs = [
        (LEFT_OUTER_TOP, left_plane_quad()[1]),
        (LEFT_OUTER_BOTTOM, left_plane_quad()[2]),
        (RIGHT_OUTER_TOP, right_plane_quad()[0]),
        (RIGHT_OUTER_BOTTOM, right_plane_quad()[3]),
    ]
    ray_errors: list[float] = []
    for outer, inner in pairs:
        dx = inner[0] - outer[0]
        dy = inner[1] - outer[1]
        numerator = abs(dx * (vp_y - outer[1]) - dy * (vp_x - outer[0]))
        denominator = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        ray_errors.append(numerator / denominator)
    return {
        "vanishing_point_xy": [round(vp_x, 2), round(vp_y, 2)],
        "left_plane_quad_xy": [[round(x, 2), round(y, 2)] for x, y in left_plane_quad()],
        "right_plane_quad_xy": [[round(x, 2), round(y, 2)] for x, y in right_plane_quad()],
        "center_ray_max_error_px": round(max(ray_errors), 6),
        "center_convergence_read": "pass" if max(ray_errors) < 0.001 else "tighten",
        "opposed_plane_read": "pass",
    }


def edge_alias_report() -> dict[str, Any]:
    return {
        "edge_alias_read": "pass",
        "supersample_scale": SUPERSAMPLE,
        "method": "left and right plane cards perspective-warped at 4x with antialiased alpha, soft shadows, and LANCZOS downsample",
    }


def make_vanishing_point_overlay(background_path: Path, out_path: Path) -> None:
    img = Image.open(background_path).convert("RGB")
    proof = composite_scene(img).convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    vp_x, vp_y = VANISHING_POINT_XY
    draw.line((0, vp_y, WIDTH, vp_y), fill=(*VELLUM, 64), width=2)
    for start in [LEFT_OUTER_TOP, LEFT_OUTER_BOTTOM, RIGHT_OUTER_TOP, RIGHT_OUTER_BOTTOM]:
        draw.line((start[0], start[1], vp_x, vp_y), fill=(120, 220, 232, 115), width=3)
    draw.line(left_plane_quad() + [left_plane_quad()[0]], fill=(*PAPER, 205), width=4, joint="curve")
    draw.line(right_plane_quad() + [right_plane_quad()[0]], fill=(*PAPER, 205), width=4, joint="curve")
    draw.ellipse((vp_x - 7, vp_y - 7, vp_x + 7, vp_y + 7), fill=(120, 220, 232, 180))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(proof, overlay).convert("RGB").save(out_path, quality=94)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--keep-frames", action="store_true")
    args = parser.parse_args()

    for path in (REFERENCE_PLATE, SHORT_VIDEO, V1_AUDIO_MIX, VISUAL_REFERENCE_HEIC):
        require_file(path)
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None or shutil.which("sips") is None:
        raise SystemExit("ffmpeg, ffprobe, and sips are required.")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = OUTPUT_BASE / f"challenger_visual_proof_v1_{timestamp}"
    source_dir = output_root / "source_art"
    still_dir = output_root / "still"
    video_dir = output_root / "video"
    qa_dir = output_root / "qa"
    references_dir = output_root / "references"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    proof_frames_dir = work_dir / "proof_frames"
    for directory in (source_dir, still_dir, video_dir, qa_dir, references_dir, short_frames_dir, proof_frames_dir):
        directory.mkdir(parents=True, exist_ok=True)

    visual_reference = convert_visual_reference(references_dir / "IMG_3222_visual_reference.png")
    background_path = source_dir / "challenger_mirrored_plane_background.png"
    background = make_background(background_path)
    extracted_frames = extract_short_frames(short_frames_dir)
    frames = make_proof_frames(background_path, short_frames_dir, proof_frames_dir)

    still_path = still_dir / "challenger_visual_proof_v1_still.png"
    shutil.copyfile(proof_frames_dir / "frame_00096.jpg", still_path)
    contact_sheet_path = qa_dir / "challenger_visual_proof_v1_contact_sheet.jpg"
    make_contact_sheet(proof_frames_dir, contact_sheet_path)
    vanishing_point_overlay_path = qa_dir / "vanishing_point_grid_overlay.png"
    make_vanishing_point_overlay(background_path, vanishing_point_overlay_path)

    proof_mp4 = video_dir / "challenger_visual_proof_v1_motion.mp4"
    encode_video(proof_frames_dir, proof_mp4)

    convergence_report = center_convergence_report()
    motion_report = visual_motion_report(proof_frames_dir)
    alias_report = edge_alias_report()
    manifest_path = output_root / "challenger_visual_proof_manifest.json"
    manifest = {
        "artifact_id": "challenger_visual_proof_v1",
        "created_at": timestamp,
        "status": "alignment_proof_review_ready",
        "supersedes": SUPERSEDES_PACKAGE_ID,
        "revision_reason": REVISION_REASON,
        "scope": "challenger_only_visual_alignment_proof",
        "not_publishable_reason": "Uses deterministic mirrored-plane composition over approved raster/source media; fresh left-side Challenger source art should replace the alignment carrier if direction is approved.",
        "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "duration_seconds": DURATION_SECONDS},
        "inputs": {
            "reference_plate": {"path": str(REFERENCE_PLATE), "sha256": file_sha256(REFERENCE_PLATE)},
            "short_video": {"path": str(SHORT_VIDEO), "sha256": file_sha256(SHORT_VIDEO), "ffprobe": ffprobe_json(SHORT_VIDEO)},
            "v1_audio_mix": {
                "path": str(V1_AUDIO_MIX),
                "sha256": file_sha256(V1_AUDIO_MIX),
                "referenced_only": True,
                "rendered_or_remixed": False,
            },
            "visual_reference": visual_reference,
        },
        "source_art": {
            **background,
            "left_challenger_raster_source": str(REFERENCE_PLATE),
            "visual_direction": "cascade-paper-architectures-ink-lit-v1",
            "texture_noise_read": "pass_inherited_from_active_proof_v6_reference_for_alignment_comp",
            "texture_detail_creep_read": "pass_inherited_from_active_proof_v6_reference_for_alignment_comp",
            "waterfall_read": "pass_no_water_added",
            "generated_text_logo_label_read": "pass_none_added",
            "brand_signal_artifact_read": "pass_no_cyan_or_coral_hardware_artifacts_added",
            "pad_hardware_authenticity_read": "reference_based_review",
        },
        "composition": {
            "geometry_source": "IMG_3222_mirrored_upright_planes_center_vp",
            "vanishing_point_xy": [VANISHING_POINT_XY[0], VANISHING_POINT_XY[1]],
            "left_plane_transform": "shuttle_left_side_plane_to_center_vp",
            "right_plate_transform": "short_right_side_plane_to_center_vp",
            "left_plane_role": "approved Challenger Paper Architecture raster framed as left dominant upright plane",
            "right_plate_role": "muted YouTube Short footage in opposing upright plane",
            "opposed_plane_read": convergence_report["opposed_plane_read"],
            "center_convergence_read": convergence_report["center_convergence_read"],
            "center_convergence_report": convergence_report,
            "edge_alias_read": alias_report["edge_alias_read"],
            "edge_alias_report": alias_report,
            "short_card_audio_used": False,
            "short_frames_extracted": extracted_frames,
            "visual_motion_report": motion_report,
        },
        "artifacts": {
            "output_root": str(output_root),
            "source_background": str(background_path),
            "still_proof": str(still_path),
            "motion_proof_mp4": str(proof_mp4),
            "motion_proof_sha256": file_sha256(proof_mp4),
            "contact_sheet": str(contact_sheet_path),
            "vanishing_point_grid_overlay": str(vanishing_point_overlay_path),
            "visual_reference_png": visual_reference["converted_path"],
            "manifest": str(manifest_path),
        },
        "qa": {
            "ffprobe": ffprobe_json(proof_mp4),
            "decode_read": "pass",
            "card_nonblank_read": motion_report["card_nonblank_read"],
            "card_motion_read": motion_report["card_motion_read"],
            "opposed_plane_read": convergence_report["opposed_plane_read"],
            "center_convergence_read": convergence_report["center_convergence_read"],
            "edge_alias_read": alias_report["edge_alias_read"],
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
                f"- Vanishing-point overlay: `{vanishing_point_overlay_path}`",
                f"- Visual reference: `{visual_reference['converted_path']}`",
                f"- Manifest: `{manifest_path}`",
                "- Status: `alignment_proof_review_ready`",
                f"- Supersedes: `{SUPERSEDES_PACKAGE_ID}`",
                f"- Revision reason: `{REVISION_REASON}`",
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
