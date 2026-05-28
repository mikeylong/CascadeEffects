#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import difflib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from guardrail_policy import load_guardrail_policy, semantic_qc_profile_for
from typography_contract import TypographyContractError, load_typography_intent
from workflow_tool import WorkflowError

FONT_SEARCH_DIRS = (
    Path("/System/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
    Path("/Library/Fonts"),
)
SUPPORTED_TARGETS = {"still", "handoff_asset", "image_sequence", "video"}
TARGET_COMPATIBILITY = {
    "still": {"artifact_type": "still", "application_phase": "post_upscale", "adapter": "raster_still"},
    "handoff_asset": {
        "artifact_type": "handoff_asset",
        "application_phase": "post_handoff",
        "adapter": "raster_handoff_asset",
    },
}
TESSERACT_BIN = "tesseract"
NORMALIZE_TEXT_RE = re.compile(r"[^A-Z0-9:./-]+")
RESAMPLING_BICUBIC = Image.Resampling.BICUBIC
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
REPAIR_ALLOWED_ACTIONS = {"ignore", "erase", "rewrite"}
REPAIR_ALLOWED_SURFACE_TYPES = {
    "environmental_sign",
    "environmental_label",
    "bulkhead_mark",
    "wall_mark",
    "room_sign",
    "clock_strip",
    "console_header",
    "display_header",
    "display_surface",
}
REPAIR_DEFAULT_FONT = "Arial Bold.ttf"
REPAIR_DEFAULT_LIGHT = "#F4EEE3"
REPAIR_DEFAULT_DARK = "#24303A"
REPAIR_POST_FINAL_CLEANUP_DEFAULTS = {
    "enabled": False,
    "mode": "erase_only",
    "max_regions": 8,
    "max_rounds": 2,
}
VISUAL_QC_MAX_WIDTH = 512
VISUAL_QC_MIN_DIM = 64
VISUAL_QC_ROW_DIFF_FLOOR = 6.0
VISUAL_QC_SCORE_THRESHOLD = 2.0
SEMANTIC_IMAGE_MAX_DIM = 768


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="scripts/typography_tool.py")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--models-root", required=True)
    parser.add_argument("--comfy-workflows-dir", required=True)
    parser.add_argument("--comfy-output-dir", required=True)
    parser.add_argument("--references-root", required=True)

    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--target", required=True, choices=sorted(SUPPORTED_TARGETS))
    apply_parser.add_argument("--artifact", required=True, help="Absolute path to the base artifact.")
    apply_parser.add_argument("--intent", required=True, help="Absolute path to the typography intent manifest.")
    apply_parser.add_argument("--output", help="Optional output path for the typography-composited artifact.")
    apply_parser.add_argument("--repair-manifest", help="Optional repair manifest to allow approved repaired text.")
    apply_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug crops.")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--target", required=True, choices=sorted(SUPPORTED_TARGETS))
    validate_parser.add_argument("--artifact", required=True, help="Absolute path to the artifact to validate.")
    validate_parser.add_argument("--intent", required=True, help="Absolute path to the typography intent manifest.")
    validate_parser.add_argument("--repair-manifest", help="Optional repair manifest to allow approved repaired text.")
    validate_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug crops.")

    audit_parser = subparsers.add_parser("audit-zero-letter")
    audit_parser.add_argument("--artifact", required=True, help="Absolute path to the artifact to audit.")
    audit_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug artifacts.")

    source_audit_parser = subparsers.add_parser("audit-source-text")
    source_audit_parser.add_argument("--artifact", required=True, help="Absolute path to the base artifact to audit.")
    source_audit_parser.add_argument("--intent", required=True, help="Absolute path to the typography intent manifest.")
    source_audit_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug artifacts.")

    repair_parser = subparsers.add_parser("repair-source-text")
    repair_parser.add_argument("--artifact", required=True, help="Absolute path to the base artifact to repair.")
    repair_parser.add_argument("--policy", required=True, help="Absolute path to the source-text repair policy.")
    repair_parser.add_argument("--output", help="Optional output path for the repaired artifact.")
    repair_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug artifacts.")

    repaired_audit_parser = subparsers.add_parser("audit-repaired-text")
    repaired_audit_parser.add_argument("--artifact", required=True, help="Absolute path to the artifact to audit.")
    repaired_audit_parser.add_argument("--repair-manifest", required=True, help="Absolute path to the repair run manifest.")
    repaired_audit_parser.add_argument("--intent", required=True, help="Absolute path to the typography intent manifest.")
    repaired_audit_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug artifacts.")

    cleanup_parser = subparsers.add_parser("cleanup-final-text")
    cleanup_parser.add_argument("--artifact", required=True, help="Absolute path to the final artifact to clean.")
    cleanup_parser.add_argument("--intent", help="Optional absolute path to the typography intent manifest.")
    cleanup_parser.add_argument("--policy", required=True, help="Absolute path to the source-text repair policy.")
    cleanup_parser.add_argument("--repair-manifest", help="Optional repair manifest for approved rewritten regions.")
    cleanup_parser.add_argument("--output", help="Optional output path for the cleaned artifact.")
    cleanup_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug artifacts.")

    process_research_parser = subparsers.add_parser("process-research-source")
    process_research_parser.add_argument("--artifact", required=True, help="Absolute path to the research asset to process.")
    process_research_parser.add_argument("--policy", help="Optional absolute path to the source-text repair policy.")
    process_research_parser.add_argument("--output", help="Optional output path for a cleaned artifact.")
    process_research_parser.add_argument("--debug-dir", help="Optional directory for OCR/debug artifacts.")

    visual_qc_parser = subparsers.add_parser("audit-visual-qc")
    visual_qc_parser.add_argument("--artifact", required=True, help="Absolute path to the artifact to audit.")
    visual_qc_parser.add_argument("--debug-dir", help="Optional directory for visual QC debug artifacts.")
    visual_qc_parser.add_argument("--ban-scanlines", action="store_true")
    visual_qc_parser.add_argument("--family", help="Workflow family for semantic QC profile resolution.")
    visual_qc_parser.add_argument("--preset", help="Workflow preset for semantic QC profile resolution.")
    visual_qc_parser.add_argument("--semantic-profile", help="Semantic QC profile name from generation_guardrails.")
    visual_qc_parser.add_argument(
        "--contract-config-json",
        help="Optional JSON payload for style-specific visual contract evaluation.",
    )
    visual_qc_parser.add_argument(
        "--semantic-stage",
        choices=["candidate", "final"],
        default="final",
        help="Semantic QC pass type.",
    )

    return parser.parse_args()


def normalize_text(value: str) -> str:
    collapsed = NORMALIZE_TEXT_RE.sub("", value.upper())
    return collapsed.strip()


def parse_hex_color(raw: str, opacity: float) -> tuple[int, int, int, int]:
    value = raw.strip().lstrip("#")
    if len(value) == 6:
        red = int(value[0:2], 16)
        green = int(value[2:4], 16)
        blue = int(value[4:6], 16)
        alpha = 255
    elif len(value) == 8:
        red = int(value[0:2], 16)
        green = int(value[2:4], 16)
        blue = int(value[4:6], 16)
        alpha = int(value[6:8], 16)
    else:
        raise WorkflowError(f"Unsupported typography color {raw!r}.")
    scaled_alpha = max(0, min(255, int(round(alpha * opacity))))
    return red, green, blue, scaled_alpha


def default_output_path(artifact_path: Path) -> Path:
    return artifact_path.with_name(f"{artifact_path.stem}__typography{artifact_path.suffix}")


def default_repair_output_path(artifact_path: Path) -> Path:
    return artifact_path.with_name(f"{artifact_path.stem}__repair{artifact_path.suffix}")


def default_cleanup_output_path(artifact_path: Path) -> Path:
    return artifact_path.with_name(f"{artifact_path.stem}__cleanup{artifact_path.suffix}")


def default_zero_letter_audit_manifest_path(artifact_path: Path) -> Path:
    return artifact_path.with_name(f"{artifact_path.stem}__zero_letter_audit.json")


def resolve_absolute_path(raw: str, *, label: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise WorkflowError(f"{label} must be an absolute path, got {raw!r}.")
    return path.resolve()


def quad_to_pixels(quad_norm: list[list[float]], width: int, height: int) -> list[tuple[float, float]]:
    return [(float(point[0]) * width, float(point[1]) * height) for point in quad_norm]


def quad_bounds(quad_pixels: list[tuple[float, float]], padding: int = 0) -> tuple[int, int, int, int]:
    xs = [point[0] for point in quad_pixels]
    ys = [point[1] for point in quad_pixels]
    left = int(math.floor(min(xs))) - padding
    top = int(math.floor(min(ys))) - padding
    right = int(math.ceil(max(xs))) + padding
    bottom = int(math.ceil(max(ys))) + padding
    return left, top, right, bottom


def quad_estimated_size(quad_pixels: list[tuple[float, float]]) -> tuple[int, int]:
    top_width = math.dist(quad_pixels[0], quad_pixels[1])
    bottom_width = math.dist(quad_pixels[2], quad_pixels[3])
    left_height = math.dist(quad_pixels[0], quad_pixels[3])
    right_height = math.dist(quad_pixels[1], quad_pixels[2])
    width = max(1, int(math.ceil((top_width + bottom_width) / 2.0)))
    height = max(1, int(math.ceil((left_height + right_height) / 2.0)))
    return width, height


@lru_cache(maxsize=64)
def resolve_font_path(raw_font_family: str) -> Path:
    candidate = Path(raw_font_family).expanduser()
    if candidate.is_absolute() and candidate.exists():
        return candidate

    for directory in FONT_SEARCH_DIRS:
        direct = directory / raw_font_family
        if direct.exists():
            return direct

    target_lower = raw_font_family.lower()
    for directory in FONT_SEARCH_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.name.lower() == target_lower:
                return path
    raise WorkflowError(f"Could not resolve typography font {raw_font_family!r}.")


def tracked_text_width(font: ImageFont.FreeTypeFont, text: str, tracking: float) -> int:
    width = 0.0
    for index, char in enumerate(text):
        width += float(font.getlength(char))
        if index < len(text) - 1:
            width += float(tracking)
    return max(1, int(math.ceil(width)))


def build_text_alpha(
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: float,
    line_spacing_px: float,
) -> Image.Image:
    lines = text.splitlines() or [text]
    sample_bbox = font.getbbox("Ag")
    glyph_height = max(1, int(math.ceil(sample_bbox[3] - sample_bbox[1])))
    padding = max(6, int(math.ceil(font.size * 0.35)))
    width = max(
        tracked_text_width(font, line, tracking) if line else 1
        for line in lines
    ) + (padding * 2)
    line_spacing = max(0, int(math.ceil(line_spacing_px)))
    height = (glyph_height * len(lines)) + (line_spacing * max(0, len(lines) - 1)) + (padding * 2)

    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    y_cursor = float(padding)
    for line in lines:
        x_cursor = float(padding)
        baseline_y = y_cursor - float(sample_bbox[1])
        for index, char in enumerate(line):
            draw.text((x_cursor, baseline_y), char, font=font, fill=255)
            x_cursor += float(font.getlength(char))
            if index < len(line) - 1:
                x_cursor += float(tracking)
        y_cursor += glyph_height + line_spacing
    return mask


def apply_noise(patch: Image.Image, noise_strength: float) -> Image.Image:
    if noise_strength <= 0.0:
        return patch
    noise_span = max(1, int(round(255 * noise_strength)))
    data = numpy.array(patch).astype(numpy.int16)
    mask = data[:, :, 3] > 0
    if not numpy.any(mask):
        return patch
    noise = numpy.random.randint(-noise_span, noise_span + 1, size=data[:, :, :3].shape)
    data[:, :, :3] = numpy.clip(data[:, :, :3] + (noise * mask[:, :, None]), 0, 255)
    return Image.fromarray(data.astype(numpy.uint8), mode="RGBA")


def build_text_patch(zone: dict[str, Any]) -> Image.Image:
    font_path = resolve_font_path(str(zone["font_family"]))
    font = ImageFont.truetype(str(font_path), int(zone["font_size_px"]))
    tracking = float(zone["tracking"])
    line_spacing_px = float(zone.get("line_spacing_px", max(4.0, font.size * 0.22)))
    opacity = float(zone["opacity"])
    blur_px = float(zone["blur_px"])
    glow_px = float(zone["glow_px"])
    noise_strength = float(zone["noise_strength"])
    text_mask = build_text_alpha(str(zone["text"]), font, tracking, line_spacing_px)

    if blur_px > 0.0:
        text_mask = text_mask.filter(ImageFilter.GaussianBlur(radius=blur_px))

    red, green, blue, alpha = parse_hex_color(str(zone["color"]), opacity)
    scaled_main_alpha = text_mask.point(lambda value: max(0, min(255, int((value / 255.0) * alpha))))
    main_patch = Image.new("RGBA", text_mask.size, (red, green, blue, 0))
    main_patch.putalpha(scaled_main_alpha)
    main_patch = apply_noise(main_patch, noise_strength)

    if glow_px > 0.0:
        glow_alpha = text_mask.filter(ImageFilter.GaussianBlur(radius=glow_px))
        glow_alpha = glow_alpha.point(lambda value: max(0, min(255, int(value * opacity * 0.55))))
        glow_patch = Image.new("RGBA", text_mask.size, (red, green, blue, 0))
        glow_patch.putalpha(glow_alpha)
        return Image.alpha_composite(glow_patch, main_patch)
    return main_patch


def resize_patch(patch: Image.Image, size: tuple[int, int]) -> Image.Image:
    width = max(1, int(round(size[0])))
    height = max(1, int(round(size[1])))
    return patch.resize((width, height), resample=RESAMPLING_BICUBIC)


def align_offset(container: int, content: int, align: str) -> int:
    if align == "start":
        return 0
    if align == "end":
        return max(0, container - content)
    return max(0, (container - content) // 2)


def apply_shadow_to_patch(patch: Image.Image, shadow: dict[str, Any]) -> Image.Image:
    if not shadow["enabled"] or shadow["opacity"] <= 0.0:
        return patch
    shadow_alpha = patch.getchannel("A")
    if shadow["blur_px"] > 0.0:
        shadow_alpha = shadow_alpha.filter(ImageFilter.GaussianBlur(radius=float(shadow["blur_px"])))
    red, green, blue, alpha = parse_hex_color(str(shadow["color"]), float(shadow["opacity"]))
    scaled_alpha = shadow_alpha.point(lambda value: max(0, min(255, int((value / 255.0) * alpha))))
    shadow_patch = Image.new("RGBA", patch.size, (red, green, blue, 0))
    shadow_patch.putalpha(scaled_alpha)

    offset_x = int(round(float(shadow["offset_x"])))
    offset_y = int(round(float(shadow["offset_y"])))
    canvas = Image.new("RGBA", patch.size, (0, 0, 0, 0))
    canvas.alpha_composite(shadow_patch, dest=(offset_x, offset_y))
    canvas.alpha_composite(patch, dest=(0, 0))
    return canvas


def place_patch_on_canvas(
    patch: Image.Image,
    *,
    canvas_size: tuple[int, int],
    fit_mode: str,
    padding_px: float,
    align_x: str,
    align_y: str,
    shadow: dict[str, Any],
) -> Image.Image:
    canvas_width, canvas_height = canvas_size
    padding = int(round(padding_px))
    inner_width = max(1, canvas_width - (padding * 2))
    inner_height = max(1, canvas_height - (padding * 2))

    if fit_mode == "stretch":
        placed_patch = resize_patch(patch, (inner_width, inner_height))
    elif fit_mode == "contain":
        scale = min(inner_width / patch.width, inner_height / patch.height)
        placed_patch = resize_patch(patch, (patch.width * scale, patch.height * scale))
    else:
        raise WorkflowError(f"Unsupported typography fit_mode {fit_mode!r}.")

    placed_patch = apply_shadow_to_patch(placed_patch, shadow)
    x_offset = padding + align_offset(inner_width, placed_patch.width, align_x)
    y_offset = padding + align_offset(inner_height, placed_patch.height, align_y)

    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas.alpha_composite(placed_patch, dest=(x_offset, y_offset))
    return canvas


def perspective_coefficients(
    destination_quad: list[tuple[float, float]],
    source_quad: list[tuple[float, float]],
) -> list[float]:
    matrix: list[list[float]] = []
    target: list[float] = []
    for (dx, dy), (sx, sy) in zip(destination_quad, source_quad):
        matrix.append([dx, dy, 1.0, 0.0, 0.0, 0.0, -sx * dx, -sx * dy])
        matrix.append([0.0, 0.0, 0.0, dx, dy, 1.0, -sy * dx, -sy * dy])
        target.extend([sx, sy])
    coefficients = numpy.linalg.solve(numpy.array(matrix, dtype=numpy.float64), numpy.array(target))
    return coefficients.tolist()


def warp_patch_to_quad(
    patch: Image.Image,
    base_size: tuple[int, int],
    quad_pixels: list[tuple[float, float]],
) -> Image.Image:
    source_quad = [
        (0.0, 0.0),
        (float(patch.width), 0.0),
        (float(patch.width), float(patch.height)),
        (0.0, float(patch.height)),
    ]
    coefficients = perspective_coefficients(quad_pixels, source_quad)
    return patch.transform(
        base_size,
        Image.Transform.PERSPECTIVE,
        coefficients,
        resample=RESAMPLING_BICUBIC,
    )


def polygon_mask(base_size: tuple[int, int], quad_pixels: list[tuple[float, float]], blur_radius: float) -> Image.Image:
    mask = Image.new("L", base_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(quad_pixels, fill=255)
    if blur_radius > 0.0:
        return mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return mask


def resolve_neutralize_mode(zone: dict[str, Any]) -> str:
    mode = str(zone["neutralize_mode"])
    if mode == "auto":
        return "soft_blur"
    return mode


def resolve_underlay_kind(zone: dict[str, Any]) -> str:
    underlay_kind = str(zone["underlay_kind"])
    if underlay_kind == "auto":
        return "clock_strip" if str(zone.get("kind", "")) == "wall_clock_strip" else "none"
    return underlay_kind


def neutralize_zone(base_image: Image.Image, zone: dict[str, Any], quad_pixels: list[tuple[float, float]]) -> Image.Image:
    mode = resolve_neutralize_mode(zone)
    if mode == "none":
        return base_image
    if mode != "soft_blur":
        raise WorkflowError(f"Unsupported typography neutralize_mode {mode!r}.")
    mask = polygon_mask(base_image.size, quad_pixels, blur_radius=2.0)
    softened = base_image.filter(ImageFilter.GaussianBlur(radius=5.0))
    mask = mask.point(lambda value: max(0, min(255, int(value * 0.72))))
    return Image.composite(softened, base_image, mask)


def add_zone_underlay(base_image: Image.Image, zone: dict[str, Any], quad_pixels: list[tuple[float, float]]) -> Image.Image:
    underlay_kind = resolve_underlay_kind(zone)
    if underlay_kind == "none":
        return base_image
    if underlay_kind != "clock_strip":
        raise WorkflowError(f"Unsupported typography underlay_kind {underlay_kind!r}.")
    underlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(underlay)
    draw.polygon(quad_pixels, fill=(70, 36, 18, 210))
    return Image.alpha_composite(base_image, underlay)


def blend_overlay(base_image: Image.Image, overlay: Image.Image, blend_mode: str) -> Image.Image:
    if blend_mode == "normal":
        return Image.alpha_composite(base_image, overlay)

    base_rgb = base_image.convert("RGB")
    overlay_rgb = overlay.convert("RGB")
    overlay_alpha = overlay.getchannel("A")

    if blend_mode == "screen":
        blended_rgb = ImageChops.screen(base_rgb, overlay_rgb)
    elif blend_mode == "add":
        blended_rgb = ImageChops.add(base_rgb, overlay_rgb, scale=1.0, offset=0)
    elif blend_mode == "multiply":
        blended_rgb = ImageChops.multiply(base_rgb, overlay_rgb)
    else:
        raise WorkflowError(f"Unsupported typography blend_mode {blend_mode!r}.")

    composited_rgb = Image.composite(blended_rgb, base_rgb, overlay_alpha)
    result = composited_rgb.convert("RGBA")
    result.putalpha(base_image.getchannel("A"))
    return result


def run_tesseract(
    image: Image.Image,
    *,
    psm: int,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="ce-ocr-") as temp_dir:
        input_path = Path(temp_dir) / "ocr-input.png"
        image.save(input_path)
        cmd = [TESSERACT_BIN, str(input_path), "stdout", "-l", "eng", "--psm", str(psm)]
        if extra_args:
            cmd.extend(extra_args)
        return subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "LC_ALL": "C"},
        )


def crop_zone(image: Image.Image, zone: dict[str, Any], quad_pixels: list[tuple[float, float]]) -> Image.Image:
    padding = 4 if str(zone.get("kind", "")) == "wall_clock_strip" else 14
    left, top, right, bottom = quad_bounds(quad_pixels, padding=padding)
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)
    return image.crop((left, top, right, bottom))


def zone_ocr_result(image: Image.Image, zone: dict[str, Any], quad_pixels: list[tuple[float, float]]) -> dict[str, Any]:
    crop = crop_zone(image, zone, quad_pixels)
    expected_text = str(zone["text"])
    whitelist = "".join(sorted({char for char in expected_text if not char.isspace()}))
    crop = crop.resize((max(1, crop.width * 4), max(1, crop.height * 4)), resample=RESAMPLING_BICUBIC)
    grayscale = ImageOps.grayscale(crop)
    autocontrast = ImageOps.autocontrast(grayscale)
    thresholded = autocontrast.point(lambda value: 255 if value >= 140 else 0)
    extra_args = ["-c", "preserve_interword_spaces=1"]
    if whitelist:
        extra_args.extend(["-c", f"tessedit_char_whitelist={whitelist}"])
    candidates: list[str] = []
    for candidate_image in (crop, autocontrast, thresholded):
        for psm in (8, 7):
            completed = run_tesseract(candidate_image, psm=psm, extra_args=extra_args)
            if completed.returncode != 0:
                raise WorkflowError(
                    f"Tesseract failed while validating zone {zone['id']!r}: {completed.stderr.strip()}"
                )
            candidates.append(completed.stdout.strip())
    expected_normalized = normalize_text(expected_text)
    observed_text = max(
        candidates,
        key=lambda candidate: difflib.SequenceMatcher(
            a=expected_normalized,
            b=normalize_text(candidate),
        ).ratio(),
    )
    return {
        "zone_id": zone["id"],
        "expected_text": expected_text,
        "rendered_text": expected_text,
        "observed_text": observed_text,
        "expected_normalized": expected_normalized,
        "observed_normalized": normalize_text(observed_text),
        "rendered_exact": True,
        "ocr_match": expected_normalized == normalize_text(observed_text),
    }


def bbox_intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def detect_unapproved_text(
    image: Image.Image,
    approved_bounds: list[tuple[int, int, int, int]],
) -> list[dict[str, Any]]:
    completed = run_tesseract(image, psm=11, extra_args=["tsv"])
    if completed.returncode != 0:
        raise WorkflowError(f"Tesseract failed while checking text leaks: {completed.stderr.strip()}")

    leaks: list[dict[str, Any]] = []
    reader = csv.DictReader(
        completed.stdout.splitlines(),
        delimiter="\t",
        quoting=csv.QUOTE_NONE,
    )
    for row in reader:
        token = (row.get("text") or "").strip()
        normalized = normalize_text(token)
        if not normalized:
            continue
        try:
            confidence = float(row.get("conf") or "-1")
            left = int(row.get("left") or "0")
            top = int(row.get("top") or "0")
            width = int(row.get("width") or "0")
            height = int(row.get("height") or "0")
        except ValueError:
            continue
        if confidence < 60.0 or width < 8 or height < 8:
            continue
        alnum = re.sub(r"[^A-Z0-9]", "", normalized)
        if len(alnum) < 2:
            continue
        if len(alnum) <= 2 and alnum.isalpha():
            aspect_ratio = width / max(1, height)
            if aspect_ratio < 1.1:
                continue
        if len(alnum) == 2 and len(set(alnum)) == 1 and width < (height * 3):
            continue
        bounds = (left, top, left + width, top + height)
        if any(bbox_intersects(bounds, approved) for approved in approved_bounds):
            continue
        leaks.append(
            {
                "text": token,
                "normalized": normalized,
                "confidence": confidence,
                "bounds": {"left": left, "top": top, "width": width, "height": height},
            }
        )
    return leaks


def expand_bounds(bounds: tuple[int, int, int, int], padding: int) -> tuple[int, int, int, int]:
    return bounds[0] - padding, bounds[1] - padding, bounds[2] + padding, bounds[3] + padding


def clamp_bounds(
    bounds: tuple[int, int, int, int],
    image_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    width, height = image_size
    left = max(0, min(width, bounds[0]))
    top = max(0, min(height, bounds[1]))
    right = max(left, min(width, bounds[2]))
    bottom = max(top, min(height, bounds[3]))
    return left, top, right, bottom


def merge_bounds(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])


def quad_norm_from_bounds(
    bounds: tuple[int, int, int, int],
    image_size: tuple[int, int],
) -> list[list[float]]:
    width, height = image_size
    left, top, right, bottom = bounds
    return [
        [left / width, top / height],
        [right / width, top / height],
        [right / width, bottom / height],
        [left / width, bottom / height],
    ]


def extract_candidate_tokens(
    image: Image.Image,
    *,
    confidence_floor: float,
) -> list[dict[str, Any]]:
    completed = run_tesseract(image, psm=11, extra_args=["tsv"])
    if completed.returncode != 0:
        raise WorkflowError(f"Tesseract failed while detecting source text: {completed.stderr.strip()}")

    tokens: list[dict[str, Any]] = []
    reader = csv.DictReader(
        completed.stdout.splitlines(),
        delimiter="\t",
        quoting=csv.QUOTE_NONE,
    )
    for row in reader:
        token = (row.get("text") or "").strip()
        normalized = normalize_text(token)
        if not normalized:
            continue
        try:
            confidence = float(row.get("conf") or "-1")
            left = int(row.get("left") or "0")
            top = int(row.get("top") or "0")
            width = int(row.get("width") or "0")
            height = int(row.get("height") or "0")
        except ValueError:
            continue
        if confidence < confidence_floor or width < 8 or height < 8:
            continue
        if len(re.sub(r"[^A-Z0-9]", "", normalized)) < 2:
            continue
        tokens.append(
            {
                "text": token,
                "normalized": normalized,
                "confidence": confidence,
                "bounds": (left, top, left + width, top + height),
            }
        )
    return tokens


def merge_candidate_regions(
    tokens: list[dict[str, Any]],
    *,
    image_size: tuple[int, int],
    max_regions: int,
) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    for token in sorted(tokens, key=lambda item: (item["bounds"][1], item["bounds"][0])):
        token_bounds = token["bounds"]
        merged = False
        for region in regions:
            if bbox_intersects(expand_bounds(region["bounds"], 18), expand_bounds(token_bounds, 18)):
                region["bounds"] = merge_bounds(region["bounds"], token_bounds)
                region["tokens"].append(token)
                merged = True
                break
        if not merged:
            regions.append({"bounds": token_bounds, "tokens": [token]})

    changed = True
    while changed:
        changed = False
        merged_regions: list[dict[str, Any]] = []
        for region in regions:
            matched = False
            for existing in merged_regions:
                if bbox_intersects(expand_bounds(existing["bounds"], 24), expand_bounds(region["bounds"], 24)):
                    existing["bounds"] = merge_bounds(existing["bounds"], region["bounds"])
                    existing["tokens"].extend(region["tokens"])
                    matched = True
                    changed = True
                    break
            if not matched:
                merged_regions.append(region)
        regions = merged_regions

    normalized_regions: list[dict[str, Any]] = []
    for index, region in enumerate(sorted(regions, key=lambda item: (item["bounds"][1], item["bounds"][0]))[:max_regions], 1):
        bounds = clamp_bounds(expand_bounds(region["bounds"], 8), image_size)
        ordered_tokens = sorted(region["tokens"], key=lambda item: (item["bounds"][1], item["bounds"][0]))
        text = " ".join(token["text"] for token in ordered_tokens)
        confidence = sum(float(token["confidence"]) for token in ordered_tokens) / max(1, len(ordered_tokens))
        normalized_regions.append(
            {
                "region_id": f"region_{index:02d}",
                "detected_text": text.strip(),
                "normalized_text": normalize_text(text),
                "ocr_confidence": round(confidence, 2),
                "bounds": {
                    "left": int(bounds[0]),
                    "top": int(bounds[1]),
                    "width": int(bounds[2] - bounds[0]),
                    "height": int(bounds[3] - bounds[1]),
                },
                "quad_norm": quad_norm_from_bounds(bounds, image_size),
                "tokens": [
                    {
                        "text": token["text"],
                        "normalized": token["normalized"],
                        "confidence": token["confidence"],
                        "bounds": {
                            "left": int(token["bounds"][0]),
                            "top": int(token["bounds"][1]),
                            "width": int(token["bounds"][2] - token["bounds"][0]),
                            "height": int(token["bounds"][3] - token["bounds"][1]),
                        },
                    }
                    for token in ordered_tokens
                ],
            }
        )
    return normalized_regions


def merge_leak_regions(
    leaks: list[dict[str, Any]],
    *,
    image_size: tuple[int, int],
    max_regions: int,
) -> list[dict[str, Any]]:
    tokens = [
        {
            "text": str(leak["text"]),
            "normalized": str(leak["normalized"]),
            "confidence": float(leak["confidence"]),
            "bounds": (
                int(leak["bounds"]["left"]),
                int(leak["bounds"]["top"]),
                int(leak["bounds"]["left"]) + int(leak["bounds"]["width"]),
                int(leak["bounds"]["top"]) + int(leak["bounds"]["height"]),
            ),
        }
        for leak in leaks
    ]
    return merge_candidate_regions(tokens, image_size=image_size, max_regions=max_regions)


def load_repair_policy(path: Path) -> dict[str, Any]:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Repair policy is not valid JSON: {path}") from exc
    required = {
        "enabled",
        "application_stage",
        "surface_scope",
        "llm_backend",
        "llm_model",
        "allow_repaired_text_outside_typography_zones",
        "ambiguous_environmental_fallback_action",
        "max_regions",
        "ocr_confidence_floor",
        "rewrite_confidence_floor",
        "erase_confidence_floor",
        "context_terms",
        "forbidden_surface_types",
    }
    missing = required - set(policy)
    if missing:
        raise WorkflowError(f"{path}: missing repair-policy fields: {', '.join(sorted(missing))}")
    if str(policy["application_stage"]) != "post_refine":
        raise WorkflowError(f"{path}: repair policy application_stage must be 'post_refine'.")
    if str(policy["surface_scope"]) != "environmental_only":
        raise WorkflowError(f"{path}: repair policy surface_scope must be 'environmental_only'.")
    if str(policy["llm_backend"]) != "ollama":
        raise WorkflowError(f"{path}: repair policy llm_backend must be 'ollama'.")
    normalized = dict(policy)
    normalized["enabled"] = bool(policy["enabled"])
    normalized["allow_repaired_text_outside_typography_zones"] = bool(
        policy["allow_repaired_text_outside_typography_zones"]
    )
    normalized["ambiguous_environmental_fallback_action"] = str(
        policy["ambiguous_environmental_fallback_action"]
    ).strip().lower()
    if normalized["ambiguous_environmental_fallback_action"] not in {"ignore", "erase"}:
        raise WorkflowError(
            f"{path}: ambiguous_environmental_fallback_action must be 'ignore' or 'erase'."
        )
    normalized["max_regions"] = int(policy["max_regions"])
    normalized["ocr_confidence_floor"] = float(policy["ocr_confidence_floor"])
    normalized["rewrite_confidence_floor"] = float(policy["rewrite_confidence_floor"])
    normalized["erase_confidence_floor"] = float(policy["erase_confidence_floor"])
    normalized["context_terms"] = [str(item).strip() for item in policy["context_terms"]]
    normalized["forbidden_surface_types"] = [str(item).strip() for item in policy["forbidden_surface_types"]]
    cleanup = policy.get("post_final_cleanup")
    if cleanup is None:
        cleanup = dict(REPAIR_POST_FINAL_CLEANUP_DEFAULTS)
    if not isinstance(cleanup, dict):
        raise WorkflowError(f"{path}: post_final_cleanup must be an object when present.")
    if not isinstance(cleanup.get("enabled", REPAIR_POST_FINAL_CLEANUP_DEFAULTS["enabled"]), bool):
        raise WorkflowError(f"{path}: post_final_cleanup.enabled must be a boolean.")
    cleanup_mode = str(cleanup.get("mode", REPAIR_POST_FINAL_CLEANUP_DEFAULTS["mode"])).strip().lower()
    if cleanup_mode != "erase_only":
        raise WorkflowError(f"{path}: post_final_cleanup.mode must be 'erase_only'.")
    try:
        cleanup_max_regions = int(cleanup.get("max_regions", REPAIR_POST_FINAL_CLEANUP_DEFAULTS["max_regions"]))
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{path}: post_final_cleanup.max_regions must be an integer.") from exc
    if cleanup_max_regions < 1:
        raise WorkflowError(f"{path}: post_final_cleanup.max_regions must be >= 1.")
    try:
        cleanup_max_rounds = int(cleanup.get("max_rounds", REPAIR_POST_FINAL_CLEANUP_DEFAULTS["max_rounds"]))
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{path}: post_final_cleanup.max_rounds must be an integer.") from exc
    if cleanup_max_rounds < 1:
        raise WorkflowError(f"{path}: post_final_cleanup.max_rounds must be >= 1.")
    normalized["post_final_cleanup"] = {
        "enabled": bool(cleanup.get("enabled", REPAIR_POST_FINAL_CLEANUP_DEFAULTS["enabled"])),
        "mode": cleanup_mode,
        "max_regions": cleanup_max_regions,
        "max_rounds": cleanup_max_rounds,
    }
    return normalized


def load_repair_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Repair manifest is not valid JSON: {path}") from exc
    if not isinstance(manifest, dict):
        raise WorkflowError(f"Repair manifest must be an object: {path}")
    return manifest


def ollama_api_base() -> str:
    raw = OLLAMA_HOST.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw.rstrip("/")
    return f"http://{raw.rstrip('/')}"


def ensure_ollama_runtime(model: str) -> None:
    if not shutil.which("ollama"):
        raise WorkflowError("Source-text repair requires ollama, but it is not installed or not on PATH.")
    completed = subprocess.run(
        ["ollama", "show", model],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "LC_ALL": "C"},
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise WorkflowError(
            f"Source-text repair requires Ollama model {model!r}, but it is not available: {stderr}"
        )


def extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    salvage_text = text[start:] if start != -1 else text

    def extract_string_field(name: str) -> str:
        match = re.search(rf'"{re.escape(name)}"\s*:\s*"([^"\n\r]*)', salvage_text)
        if not match:
            return ""
        return match.group(1).strip()

    def extract_numeric_field(name: str) -> float | str | None:
        match = re.search(rf'"{re.escape(name)}"\s*:\s*("?)([-+]?\d+(?:\.\d+)?)\1', salvage_text)
        if not match:
            return None
        try:
            return float(match.group(2))
        except ValueError:
            return match.group(2)

    salvaged: dict[str, Any] = {}
    action = extract_string_field("action")
    if action:
        salvaged["action"] = action
    surface_type = extract_string_field("surface_type")
    if surface_type:
        salvaged["surface_type"] = surface_type
    corrected_text = extract_string_field("corrected_text")
    if corrected_text:
        salvaged["corrected_text"] = corrected_text
    reason = extract_string_field("reason")
    if reason:
        salvaged["reason"] = reason
    confidence = extract_numeric_field("confidence")
    if confidence is not None:
        salvaged["confidence"] = confidence

    if salvaged.get("action"):
        salvaged.setdefault("surface_type", "")
        salvaged.setdefault("confidence", 0.0)
        salvaged.setdefault("corrected_text", "")
        salvaged.setdefault("reason", "Recovered from partial Ollama JSON response.")
        return salvaged

    if start == -1 or end == -1 or end <= start:
        raise WorkflowError(f"Ollama response did not contain JSON: {raw_text}")
    raise WorkflowError(f"Ollama returned invalid JSON: {raw_text}")


def classify_region_with_ollama(
    *,
    crop_path: Path,
    region: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    prompt = (
        "Classify this cropped text region from a historical collage still. "
        "Return one JSON object with keys action, surface_type, confidence, corrected_text, reason. "
        "Confidence must be a number from 0.0 to 1.0, not a word. "
        "Allowed actions: ignore, erase, rewrite. "
        "Rewrite is only allowed for environmental room-integrated surfaces such as wall marks, room signs, "
        "clock strips, console headers, and large non-interactive display headers. "
        "Badges, paperwork, tiny labels, dense UI, instrument readouts, and serial plates must never be rewritten. "
        f"Context terms: {', '.join(policy['context_terms'])}. "
        f"Forbidden surface types: {', '.join(policy['forbidden_surface_types'])}. "
        f"OCR guess: {region['detected_text']!r}. "
        "If the text is readable enough to require cleanup but too ambiguous to rewrite confidently, prefer action=erase. "
        "If the text is not reliable or the crop is too ambiguous to act on, return action=ignore."
    )
    payload = {
        "model": str(policy["llm_model"]),
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "images": [base64.b64encode(crop_path.read_bytes()).decode("ascii")],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{ollama_api_base()}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise WorkflowError(f"Failed to reach Ollama at {ollama_api_base()}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError("Ollama returned invalid JSON from /api/generate.") from exc
    raw_response = str(body.get("response", "")).strip()
    parsed = extract_json_object(raw_response)
    return prompt, {"raw_response": raw_response, "parsed": parsed}


def normalize_semantic_issue_tags(value: Any, *, allowed_tags: list[str]) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    normalized: list[str] = []
    allowed = {tag.strip(): tag.strip() for tag in allowed_tags if tag.strip()}
    for raw in value:
        tag = str(raw).strip()
        if not tag or tag not in allowed or tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
    return normalized


def semantic_anchor_grade(value: Any) -> str:
    grade = str(value).strip().lower()
    if grade in {"clear", "partial", "missing"}:
        return grade
    if grade in {"yes", "recognized", "recognizable"}:
        return "clear"
    if grade in {"somewhat", "uncertain"}:
        return "partial"
    return "missing"


def semantic_numeric_score(value: Any) -> float:
    try:
        return max(0.0, min(10.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def evaluate_semantic_qc_response(
    parsed: dict[str, Any],
    profile: dict[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    anchor_grade = semantic_anchor_grade(parsed.get("anchor_recognition"))
    composition_score = semantic_numeric_score(parsed.get("composition_score"))
    clarity_score = semantic_numeric_score(parsed.get("clarity_score"))
    issues = normalize_semantic_issue_tags(
        parsed.get("issues"),
        allowed_tags=list(profile.get("allowed_issue_tags", [])),
    )
    if anchor_grade == "missing" and "unrecognizable_anchor" in profile.get("allowed_issue_tags", []):
        if "unrecognizable_anchor" not in issues:
            issues.append("unrecognizable_anchor")

    weights = dict(profile.get("weights", {}))
    ranking_score = (
        (composition_score * float(weights.get("composition", 0.65)))
        + (clarity_score * float(weights.get("clarity", 0.35)))
    )
    if anchor_grade == "clear":
        ranking_score += float(weights.get("anchor_bonus_clear", 2.0))
    elif anchor_grade == "partial":
        ranking_score += float(weights.get("anchor_bonus_partial", 0.5))
    else:
        ranking_score -= float(weights.get("anchor_penalty_missing", 3.0))
    ranking_score -= len(issues) * float(weights.get("issue_penalty", 1.5))

    hard_fail_tags = [tag for tag in issues if tag in set(profile.get("hard_fail_tags", []))]
    failures = [f"semantic hard fail: {tag}" for tag in hard_fail_tags]
    minimum_composition_score = float(profile.get("minimum_composition_score", 0.0) or 0.0)
    minimum_rank_score = float(profile.get("minimum_rank_score", 0.0) or 0.0)
    if composition_score < minimum_composition_score:
        failures.append(
            f"semantic composition score {composition_score:.2f} below threshold {minimum_composition_score:.2f}"
        )
    if ranking_score < minimum_rank_score:
        failures.append(f"semantic ranking score {ranking_score:.2f} below threshold {minimum_rank_score:.2f}")

    warnings: list[str] = []
    if not failures and anchor_grade == "partial":
        warnings.append("semantic anchor recognition is only partial")
    notes = str(parsed.get("notes", "")).strip()
    return {
        "status": "failed" if failures else "ok",
        "stage": stage,
        "profile": str(profile.get("name", "")).strip(),
        "anchor_recognition": anchor_grade,
        "composition_score": round(composition_score, 4),
        "clarity_score": round(clarity_score, 4),
        "ranking_score": round(float(ranking_score), 4),
        "minimum_rank_score": minimum_rank_score,
        "minimum_composition_score": minimum_composition_score,
        "issues": issues,
        "hard_fail_tags": hard_fail_tags,
        "warnings": warnings,
        "failures": failures,
        "notes": notes,
    }


def classify_artifact_semantics_with_ollama(
    *,
    artifact_path: Path,
    profile: dict[str, Any],
    family: str,
    preset: str,
    stage: str,
) -> tuple[str, dict[str, Any]]:
    prompt = (
        "You are grading a generated editorial-collage still for semantic quality control. "
        "Return one JSON object with keys anchor_recognition, composition_score, clarity_score, issues, notes. "
        "anchor_recognition must be one of clear, partial, missing. "
        "composition_score and clarity_score must be numbers from 0 to 10. "
        f"Family: {family}. Preset: {preset}. Semantic stage: {stage}. "
        f"Profile brief: {profile.get('brief', '')}. "
        f"Stage focus: {profile.get('stage_focus', {}).get(stage, '')}. "
        "Allowed issues are exactly: "
        f"{', '.join(profile.get('allowed_issue_tags', []))}. "
        "Use issues when the image drifts semantically, not for minor technical defects. "
        "Judge whether the intended anchor is clear, whether the collage composition stays readable, "
        "and whether the image drifts into the forbidden failure modes."
    )
    payload = {
        "model": str(profile["model"]),
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "images": [base64.b64encode(artifact_path.read_bytes()).decode("ascii")],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{ollama_api_base()}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise WorkflowError(f"Failed to reach Ollama at {ollama_api_base()}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError("Ollama returned invalid JSON from /api/generate.") from exc
    raw_response = str(body.get("response", "")).strip()
    parsed = extract_json_object(raw_response)
    return prompt, {"raw_response": raw_response, "parsed": parsed}


def audit_semantic_qc_artifact(
    artifact_path: Path,
    *,
    profile: dict[str, Any],
    family: str,
    preset: str,
    stage: str,
    debug_dir: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    ensure_ollama_runtime(str(profile["model"]))
    prompt, ollama_response = classify_artifact_semantics_with_ollama(
        artifact_path=artifact_path,
        profile=profile,
        family=family,
        preset=preset,
        stage=stage,
    )
    summary = evaluate_semantic_qc_response(
        dict(ollama_response["parsed"]),
        profile,
        stage=stage,
    )
    debug_artifacts: list[str] = []
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = debug_dir / "semantic_qc_prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        response_path = debug_dir / "semantic_qc_response.json"
        response_payload = {
            "parsed": ollama_response["parsed"],
            "raw_response": ollama_response["raw_response"],
            "summary": summary,
        }
        response_path.write_text(json.dumps(response_payload, indent=2), encoding="utf-8")
        debug_artifacts.extend([str(prompt_path), str(response_path)])
    return summary, debug_artifacts


def normalize_llm_confidence(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))

    text = str(value).strip().lower()
    if not text:
        return 0.0

    label_map = {
        "very_high": 0.95,
        "high": 0.85,
        "medium": 0.6,
        "low": 0.35,
        "very_low": 0.15,
    }
    normalized_label = text.replace(" ", "_").replace("-", "_")
    if normalized_label in label_map:
        return label_map[normalized_label]

    if text.endswith("%"):
        text = text[:-1].strip()
        try:
            return max(0.0, min(1.0, float(text) / 100.0))
        except ValueError:
            return 0.0

    try:
        numeric = float(text)
    except ValueError:
        return 0.0
    if numeric > 1.0:
        numeric /= 100.0
    return max(0.0, min(1.0, numeric))


def region_is_plausibly_environmental(region: dict[str, Any]) -> bool:
    bounds = region["bounds"]
    width = int(bounds["width"])
    height = int(bounds["height"])
    area = width * height
    tokens = list(region.get("tokens", []))
    if not tokens:
        return False
    if width < 40 or height < 20 or area < 1200:
        return False
    if len(tokens) > 4:
        return False
    average_token_height = sum(int(token["bounds"]["height"]) for token in tokens) / max(1, len(tokens))
    if average_token_height < 12:
        return False
    return True


def fallback_erase_for_ambiguous_environment(
    *,
    region: dict[str, Any],
    policy: dict[str, Any],
    action: str,
    surface_type: str,
    confidence: float,
    corrected_text: str,
    reason: str,
    forbidden: set[str],
) -> dict[str, Any] | None:
    fallback_action = str(policy.get("ambiguous_environmental_fallback_action", "ignore")).strip().lower()
    if fallback_action != "erase":
        return None
    if surface_type in forbidden:
        return None
    if not region_is_plausibly_environmental(region):
        return None

    rewrite_unusable = action == "rewrite" and (
        surface_type not in REPAIR_ALLOWED_SURFACE_TYPES
        or confidence < float(policy["rewrite_confidence_floor"])
        or not corrected_text
    )
    llm_declined = action == "ignore" or not surface_type
    if not (rewrite_unusable or llm_declined):
        return None

    fallback_confidence = max(confidence, min(1.0, float(region["ocr_confidence"]) / 100.0))
    return {
        "action": "erase",
        "surface_type": surface_type or "environmental_ambiguous",
        "confidence": fallback_confidence,
        "corrected_text": "",
        "reason": reason or "Ambiguous readable environmental text defaults to erase.",
    }


def choose_repair_text_color(crop: Image.Image) -> str:
    grayscale = ImageOps.grayscale(crop)
    resized = grayscale.resize((1, 1))
    luminance = int(resized.getpixel((0, 0)))
    return REPAIR_DEFAULT_LIGHT if luminance < 120 else REPAIR_DEFAULT_DARK


def soft_inpaint_rectangle(
    image: Image.Image,
    bounds: tuple[int, int, int, int],
) -> tuple[Image.Image, Image.Image]:
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(bounds, radius=max(6, min(bounds[2] - bounds[0], bounds[3] - bounds[1]) // 6), fill=255)
    soft_mask = mask.filter(ImageFilter.GaussianBlur(radius=6.0))

    crop = image.crop(bounds).resize((1, 1))
    average = crop.convert("RGB").getpixel((0, 0))
    fill = Image.new("RGBA", image.size, average + (0,))
    fill_draw = ImageDraw.Draw(fill)
    fill_draw.rounded_rectangle(bounds, radius=max(6, min(bounds[2] - bounds[0], bounds[3] - bounds[1]) // 6), fill=average + (220,))
    blurred = image.filter(ImageFilter.GaussianBlur(radius=12.0))
    base = Image.composite(fill, image, soft_mask.point(lambda value: int(value * 0.75)))
    repaired = Image.composite(blurred, base, soft_mask)
    return repaired, soft_mask


def synthesize_repair_zone(
    image: Image.Image,
    region: dict[str, Any],
    corrected_text: str,
) -> dict[str, Any]:
    bounds = region["bounds"]
    left = int(bounds["left"])
    top = int(bounds["top"])
    width = int(bounds["width"])
    height = int(bounds["height"])
    right = left + width
    bottom = top + height
    crop = image.crop((left, top, right, bottom))
    color = choose_repair_text_color(crop)
    font_size = max(14, int(height * 0.62))
    return {
        "id": str(region["region_id"]),
        "kind": "repair_region",
        "text": corrected_text,
        "quad_norm": region["quad_norm"],
        "font_family": REPAIR_DEFAULT_FONT,
        "font_size_px": font_size,
        "tracking": 1.0 if len(corrected_text) <= 6 else 0.0,
        "color": color,
        "opacity": 0.92,
        "blend_mode": "normal",
        "blur_px": 0.2,
        "glow_px": 0.0,
        "noise_strength": 0.01,
        "fit_mode": "contain",
        "padding_px": 2.0,
        "align_x": "center",
        "align_y": "center",
        "neutralize_mode": "none",
        "underlay_kind": "none",
        "shadow": {
            "enabled": False,
            "color": "#000000",
            "opacity": 0.0,
            "blur_px": 0.0,
            "offset_x": 0.0,
            "offset_y": 0.0,
        },
        "debug_emit_crop": False,
    }


def apply_repair_redraw(
    image: Image.Image,
    region: dict[str, Any],
    corrected_text: str,
) -> tuple[Image.Image, dict[str, Any]]:
    zone = synthesize_repair_zone(image, region, corrected_text)
    quad_pixels = quad_to_pixels(zone["quad_norm"], image.width, image.height)
    zone_size = quad_estimated_size(quad_pixels)
    text_patch = build_text_patch(zone)
    zone_canvas = place_patch_on_canvas(
        text_patch,
        canvas_size=zone_size,
        fit_mode=str(zone["fit_mode"]),
        padding_px=float(zone["padding_px"]),
        align_x=str(zone["align_x"]),
        align_y=str(zone["align_y"]),
        shadow=zone["shadow"],
    )
    warped_patch = warp_patch_to_quad(zone_canvas, image.size, quad_pixels)
    repaired = blend_overlay(image, warped_patch, str(zone["blend_mode"]))
    return repaired, {
        "text": corrected_text,
        "quad_norm": zone["quad_norm"],
        "font_family": zone["font_family"],
        "font_size_px": zone["font_size_px"],
        "color": zone["color"],
        "blend_mode": zone["blend_mode"],
    }


def choose_repair_action(
    *,
    region: dict[str, Any],
    policy: dict[str, Any],
    llm_result: dict[str, Any] | None,
) -> dict[str, Any]:
    if region["ocr_confidence"] < float(policy["ocr_confidence_floor"]):
        return {
            "action": "ignore",
            "surface_type": "unreliable",
            "confidence": 0.0,
            "corrected_text": "",
            "reason": f"OCR confidence {region['ocr_confidence']} below floor {policy['ocr_confidence_floor']}",
        }

    parsed = dict(llm_result or {})
    action = str(parsed.get("action", "ignore")).strip().lower()
    if action not in REPAIR_ALLOWED_ACTIONS:
        action = "ignore"
    surface_type = str(parsed.get("surface_type", "")).strip().lower().replace(" ", "_")
    confidence = normalize_llm_confidence(parsed.get("confidence", 0.0))
    corrected_text = str(parsed.get("corrected_text", "") or "").strip()
    reason = str(parsed.get("reason", "") or "").strip()
    forbidden = {item.strip().lower().replace(" ", "_") for item in policy["forbidden_surface_types"]}
    environmental = surface_type in REPAIR_ALLOWED_SURFACE_TYPES
    ambiguous_fallback = fallback_erase_for_ambiguous_environment(
        region=region,
        policy=policy,
        action=action,
        surface_type=surface_type,
        confidence=confidence,
        corrected_text=corrected_text,
        reason=reason,
        forbidden=forbidden,
    )

    if action == "rewrite":
        if surface_type in forbidden or not environmental:
            if ambiguous_fallback is not None:
                return ambiguous_fallback
            if confidence >= float(policy["erase_confidence_floor"]):
                return {
                    "action": "erase",
                    "surface_type": surface_type or "unknown",
                    "confidence": confidence,
                    "corrected_text": "",
                    "reason": reason or "Rewrite disallowed on non-environmental surface.",
                }
            return {
                "action": "ignore",
                "surface_type": surface_type or "unknown",
                "confidence": confidence,
                "corrected_text": "",
                "reason": reason or "Rewrite disallowed and erase confidence too low.",
            }
        if confidence < float(policy["rewrite_confidence_floor"]) or not corrected_text:
            if ambiguous_fallback is not None:
                return ambiguous_fallback
            if confidence >= float(policy["erase_confidence_floor"]):
                return {
                    "action": "erase",
                    "surface_type": surface_type or "unknown",
                    "confidence": confidence,
                    "corrected_text": "",
                    "reason": reason or "Rewrite confidence too low; erasing instead.",
                }
            return {
                "action": "ignore",
                "surface_type": surface_type or "unknown",
                "confidence": confidence,
                "corrected_text": "",
                "reason": reason or "Rewrite confidence too low.",
            }
        return {
            "action": "rewrite",
            "surface_type": surface_type or "unknown",
            "confidence": confidence,
            "corrected_text": corrected_text,
            "reason": reason,
        }

    if action == "erase":
        if confidence < float(policy["erase_confidence_floor"]):
            return {
                "action": "ignore",
                "surface_type": surface_type or "unknown",
                "confidence": confidence,
                "corrected_text": "",
                "reason": reason or "Erase confidence too low.",
            }
        return {
            "action": "erase",
            "surface_type": surface_type or "unknown",
            "confidence": confidence,
            "corrected_text": "",
            "reason": reason,
        }

    if ambiguous_fallback is not None:
        return ambiguous_fallback

    return {
        "action": "ignore",
        "surface_type": surface_type or "unknown",
        "confidence": confidence,
        "corrected_text": "",
        "reason": reason or "Model chose ignore.",
    }


def internal_residual_repair_validation(
    image: Image.Image,
    repaired_regions: list[dict[str, Any]],
    *,
    debug_dir: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    approved_bounds: list[tuple[int, int, int, int]] = []
    for region in repaired_regions:
        quad_pixels = quad_to_pixels(region["quad_norm"], image.width, image.height)
        approved_bounds.append(quad_bounds(quad_pixels, padding=8))
    leaks = detect_unapproved_text(image, approved_bounds)
    failures: list[str] = []
    if leaks:
        leak_list = ", ".join(repr(item["text"]) for item in leaks[:5])
        failures.append(f"unapproved text outside repaired regions: {leak_list}")
    validation = {
        "policy": {"repair_region_ocr": "warn", "unapproved_text": "fail"},
        "zone_results": [],
        "unapproved_text": leaks,
        "warnings": [],
        "failures": failures,
        "status": "failed" if failures else "ok",
    }
    debug_artifacts = emit_text_audit_debug_artifacts(
        image,
        leaks,
        approved_bounds=approved_bounds,
        debug_dir=debug_dir,
    )
    return validation, debug_artifacts


def emit_zone_debug_artifacts(
    image: Image.Image,
    zone: dict[str, Any],
    quad_pixels: list[tuple[float, float]],
    *,
    debug_dir: Path | None,
) -> list[str]:
    if debug_dir is None:
        return []
    crop = crop_zone(image, zone, quad_pixels)
    crop = crop.resize((max(1, crop.width * 4), max(1, crop.height * 4)), resample=RESAMPLING_BICUBIC)
    grayscale = ImageOps.grayscale(crop)
    autocontrast = ImageOps.autocontrast(grayscale)
    thresholded = autocontrast.point(lambda value: 255 if value >= 140 else 0)

    zone_dir = debug_dir / zone["id"]
    zone_dir.mkdir(parents=True, exist_ok=True)
    crop_path = zone_dir / "crop.png"
    autocontrast_path = zone_dir / "autocontrast.png"
    threshold_path = zone_dir / "threshold.png"
    crop.save(crop_path)
    autocontrast.save(autocontrast_path)
    thresholded.save(threshold_path)
    return [str(crop_path), str(autocontrast_path), str(threshold_path)]


def collect_approved_bounds(image: Image.Image, intent: dict[str, Any]) -> list[tuple[int, int, int, int]]:
    approved_bounds: list[tuple[int, int, int, int]] = []
    for zone in intent["zones"]:
        quad_pixels = quad_to_pixels(zone["quad_norm"], image.width, image.height)
        approved_bounds.append(quad_bounds(quad_pixels, padding=12))
    return approved_bounds


def iter_rewrite_regions(repair_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    regions = repair_manifest.get("regions")
    if isinstance(regions, list):
        return [region for region in regions if isinstance(region, dict) and str(region.get("action", "")) == "rewrite"]
    rewrite_regions = repair_manifest.get("rewrite_regions")
    if isinstance(rewrite_regions, list):
        return [region for region in rewrite_regions if isinstance(region, dict)]
    return []


def repair_region_to_zone(region: dict[str, Any]) -> dict[str, Any]:
    corrected_text = str(region.get("corrected_text") or region.get("redraw", {}).get("text") or "").strip()
    return {
        "id": str(region.get("region_id", "repair_region")),
        "kind": "repair_region",
        "text": corrected_text,
        "quad_norm": region["quad_norm"],
    }


def collect_repair_bounds(image: Image.Image, repair_manifest: dict[str, Any]) -> list[tuple[int, int, int, int]]:
    approved_bounds: list[tuple[int, int, int, int]] = []
    for region in iter_rewrite_regions(repair_manifest):
        quad_pixels = quad_to_pixels(region["quad_norm"], image.width, image.height)
        approved_bounds.append(quad_bounds(quad_pixels, padding=10))
    return approved_bounds


def repair_region_ocr_results(
    image: Image.Image,
    repair_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for region in iter_rewrite_regions(repair_manifest):
        zone = repair_region_to_zone(region)
        if not zone["text"]:
            continue
        quad_pixels = quad_to_pixels(zone["quad_norm"], image.width, image.height)
        results.append(zone_ocr_result(image, zone, quad_pixels))
    return results


def evaluate_validation(intent: dict[str, Any], zone_results: list[dict[str, Any]], leaks: list[dict[str, Any]]) -> dict[str, Any]:
    warnings: list[str] = []
    failures: list[str] = []

    zone_policy = str(intent["validation_policy"]["zone_ocr"])
    if zone_policy != "off":
        mismatches = [result for result in zone_results if not result["ocr_match"]]
        for mismatch in mismatches:
            message = (
                f"zone {mismatch['zone_id']!r} OCR mismatch: expected {mismatch['expected_text']!r}, "
                f"observed {mismatch['observed_text']!r}"
            )
            if zone_policy == "fail":
                failures.append(message)
            else:
                warnings.append(message)

    leak_policy = str(intent["validation_policy"]["unapproved_text"])
    if leak_policy != "off" and leaks:
        leak_list = ", ".join(repr(item["text"]) for item in leaks[:5])
        message = f"unapproved text outside zones: {leak_list}"
        if leak_policy == "fail":
            failures.append(message)
        else:
            warnings.append(message)

    status = "failed" if failures else "warning" if warnings else "ok"
    return {
        "policy": intent["validation_policy"],
        "zone_results": zone_results,
        "unapproved_text": leaks,
        "warnings": warnings,
        "failures": failures,
        "status": status,
    }


def evaluate_validation_with_repair(
    intent: dict[str, Any],
    zone_results: list[dict[str, Any]],
    repair_zone_results: list[dict[str, Any]],
    leaks: list[dict[str, Any]],
) -> dict[str, Any]:
    validation = evaluate_validation(intent, zone_results, leaks)
    warnings = list(validation["warnings"])
    failures = list(validation["failures"])
    for result in repair_zone_results:
        if not result["ocr_match"]:
            warnings.append(
                f"repaired region {result['zone_id']!r} OCR mismatch: expected {result['expected_text']!r}, "
                f"observed {result['observed_text']!r}"
            )
    status = "failed" if failures else "warning" if warnings else "ok"
    validation["repair_region_results"] = repair_zone_results
    validation["warnings"] = warnings
    validation["failures"] = failures
    validation["status"] = status
    return validation


def emit_text_audit_debug_artifacts(
    image: Image.Image,
    leaks: list[dict[str, Any]],
    *,
    approved_bounds: list[tuple[int, int, int, int]],
    debug_dir: Path | None,
) -> list[str]:
    if debug_dir is None:
        return []
    debug_dir.mkdir(parents=True, exist_ok=True)

    source_path = debug_dir / "artifact.png"
    image.save(source_path)

    overlay = image.convert("RGBA").copy()
    draw = ImageDraw.Draw(overlay)
    for left, top, right, bottom in approved_bounds:
        draw.rectangle((left, top, right, bottom), outline=(80, 200, 120, 255), width=3)
    for leak in leaks:
        bounds = leak["bounds"]
        left = int(bounds["left"])
        top = int(bounds["top"])
        right = left + int(bounds["width"])
        bottom = top + int(bounds["height"])
        draw.rectangle((left, top, right, bottom), outline=(255, 64, 64, 255), width=4)
    overlay_path = debug_dir / "artifact__unapproved_text.png"
    overlay.save(overlay_path)

    leaks_path = debug_dir / "unapproved_text.json"
    leaks_path.write_text(json.dumps(leaks, indent=2), encoding="utf-8")
    return [str(source_path), str(overlay_path), str(leaks_path)]


def audit_zero_letter_artifact(
    image: Image.Image,
    *,
    debug_dir: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    leaks = detect_unapproved_text(image, [])
    failures: list[str] = []
    if leaks:
        leak_list = ", ".join(repr(item["text"]) for item in leaks[:5])
        failures.append(f"unapproved text detected: {leak_list}")
    validation = {
        "policy": {"zone_ocr": "off", "unapproved_text": "fail"},
        "zone_results": [],
        "unapproved_text": leaks,
        "warnings": [],
        "failures": failures,
        "status": "failed" if failures else "ok",
    }
    debug_artifacts = emit_text_audit_debug_artifacts(
        image,
        leaks,
        approved_bounds=[],
        debug_dir=debug_dir,
    )
    return validation, debug_artifacts


def audit_source_text_artifact(
    image: Image.Image,
    intent: dict[str, Any],
    *,
    debug_dir: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    approved_bounds = collect_approved_bounds(image, intent)
    leaks = detect_unapproved_text(image, approved_bounds)
    failures: list[str] = []
    if leaks:
        leak_list = ", ".join(repr(item["text"]) for item in leaks[:5])
        failures.append(f"unapproved text outside approved refinement zones: {leak_list}")
    validation = {
        "policy": {"zone_ocr": "off", "unapproved_text": "fail"},
        "zone_results": [],
        "unapproved_text": leaks,
        "warnings": [],
        "failures": failures,
        "status": "failed" if failures else "ok",
    }
    debug_artifacts = emit_text_audit_debug_artifacts(
        image,
        leaks,
        approved_bounds=approved_bounds,
        debug_dir=debug_dir,
    )
    return validation, debug_artifacts


def audit_repaired_text_artifact(
    image: Image.Image,
    repair_manifest: dict[str, Any],
    intent: dict[str, Any],
    *,
    debug_dir: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    approved_bounds = collect_approved_bounds(image, intent) + collect_repair_bounds(image, repair_manifest)
    leaks = detect_unapproved_text(image, approved_bounds)
    repair_zone_results = repair_region_ocr_results(image, repair_manifest)
    warnings: list[str] = []
    failures: list[str] = []
    for result in repair_zone_results:
        if not result["ocr_match"]:
            warnings.append(
                f"repaired region {result['zone_id']!r} OCR mismatch: expected {result['expected_text']!r}, "
                f"observed {result['observed_text']!r}"
            )
    if leaks:
        leak_list = ", ".join(repr(item["text"]) for item in leaks[:5])
        failures.append(f"unapproved text outside typography zones and approved repair regions: {leak_list}")
    validation = {
        "policy": {
            "zone_ocr": "off",
            "repair_region_ocr": "warn",
            "unapproved_text": "fail",
        },
        "zone_results": [],
        "repair_region_results": repair_zone_results,
        "unapproved_text": leaks,
        "warnings": warnings,
        "failures": failures,
        "status": "failed" if failures else "warning" if warnings else "ok",
    }
    debug_artifacts = emit_text_audit_debug_artifacts(
        image,
        leaks,
        approved_bounds=approved_bounds,
        debug_dir=debug_dir,
    )
    return validation, debug_artifacts


def build_visual_qc_profile_image(
    row_diff: numpy.ndarray,
    *,
    threshold: float,
    flagged_rows: numpy.ndarray,
) -> Image.Image:
    width = max(256, min(512, int(row_diff.shape[0])))
    height = 160
    canvas = Image.new("RGBA", (width, height), (248, 248, 244, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width - 1, height - 1), outline=(44, 52, 60, 255), width=1)
    if row_diff.size == 0:
        return canvas

    max_value = max(float(row_diff.max()), threshold, 1.0)
    usable_height = height - 24
    threshold_y = 8 + int((1.0 - min(1.0, threshold / max_value)) * usable_height)
    draw.line((0, threshold_y, width - 1, threshold_y), fill=(214, 84, 61, 255), width=2)

    if row_diff.size == 1:
        scaled_points = [(width // 2, threshold_y)]
    else:
        scaled_points: list[tuple[int, int]] = []
        for index, value in enumerate(row_diff.tolist()):
            x = int(round(index * (width - 1) / max(1, row_diff.size - 1)))
            y = 8 + int((1.0 - min(1.0, float(value) / max_value)) * usable_height)
            scaled_points.append((x, y))
    if len(scaled_points) > 1:
        draw.line(scaled_points, fill=(35, 91, 196, 255), width=2)
    else:
        draw.ellipse(
            (
                scaled_points[0][0] - 2,
                scaled_points[0][1] - 2,
                scaled_points[0][0] + 2,
                scaled_points[0][1] + 2,
            ),
            fill=(35, 91, 196, 255),
        )

    flagged_indices = numpy.nonzero(flagged_rows)[0].tolist()
    for index in flagged_indices:
        x = int(round(index * (width - 1) / max(1, row_diff.size - 1)))
        draw.line((x, 8, x, height - 8), fill=(214, 84, 61, 70), width=1)

    return canvas


def rgb_to_gray_array(image_array: numpy.ndarray) -> numpy.ndarray:
    return 0.299 * image_array[:, :, 0] + 0.587 * image_array[:, :, 1] + 0.114 * image_array[:, :, 2]


def normalize_rgb_image(image: Image.Image) -> numpy.ndarray:
    return numpy.asarray(image.convert("RGB"), dtype=numpy.float32) / 255.0


def compute_edge_saliency(gray: numpy.ndarray) -> numpy.ndarray:
    gx = numpy.zeros_like(gray)
    gy = numpy.zeros_like(gray)
    gx[:, 1:] = numpy.abs(gray[:, 1:] - gray[:, :-1])
    gy[1:, :] = numpy.abs(gray[1:, :] - gray[:-1, :])
    return gx + gy


def quantize_palette(img: numpy.ndarray, bins: int = 6) -> tuple[numpy.ndarray, numpy.ndarray]:
    arr = numpy.clip((img * bins).astype(int), 0, bins - 1)
    flat = arr.reshape(-1, 3)
    unique, counts = numpy.unique(flat, axis=0, return_counts=True)
    proportions = counts / counts.sum()
    return unique, proportions


def score_asymmetry_ratio(gray: numpy.ndarray, saliency: numpy.ndarray) -> float:
    height, width = gray.shape
    left_saliency = float(saliency[:, : width // 2].sum())
    right_saliency = float(saliency[:, width // 2 :].sum())
    total_saliency = left_saliency + right_saliency + 1e-8
    side_balance = abs(left_saliency - right_saliency) / total_saliency

    center_band = saliency[:, int(width * 0.35) : int(width * 0.65)]
    center_mass = float(center_band.sum()) / max(float(saliency.sum()), 1e-8)

    score = (side_balance * 0.75) + (max(0.0, 1.0 - center_mass) * 0.25)
    return max(0.0, min(1.0, score))


def score_palette_discipline(img: numpy.ndarray) -> tuple[float, int]:
    _unique, proportions = quantize_palette(img, bins=6)
    meaningful = proportions[proportions > 0.03]
    count_score = 1.0 if 2 <= len(meaningful) <= 4 else max(0.2, 1.0 - 0.15 * abs(len(meaningful) - 3))

    saturation = img.max(axis=2) - img.min(axis=2)
    saturated_ratio = float((saturation > 0.45).mean())
    if 0.005 <= saturated_ratio <= 0.15:
        accent_score = 1.0
    elif saturated_ratio < 0.005:
        accent_score = 0.45
    else:
        accent_score = max(0.2, 1.0 - saturated_ratio * 3.0)

    accent_mask = saturation > 0.45
    accent_clusters = count_hue_clusters(img, accent_mask)
    if accent_clusters > 1:
        accent_score = min(accent_score, 0.45)

    score = float((count_score * 0.55) + (accent_score * 0.45))
    return max(0.0, min(1.0, score)), accent_clusters


def score_focal_clarity(img: numpy.ndarray) -> float:
    gray = rgb_to_gray_array(img)
    saliency = compute_edge_saliency(gray)
    threshold = float(numpy.quantile(saliency, 0.98))
    hotspots = saliency > threshold
    hotspot_density = float(hotspots.mean())

    if hotspot_density < 0.002:
        return 0.35
    if hotspot_density <= 0.02:
        return 0.95
    if hotspot_density <= 0.05:
        return 0.75
    return max(0.2, 1.0 - hotspot_density * 8.0)


def score_visual_noise_metric(img: numpy.ndarray) -> float:
    gray = rgb_to_gray_array(img)
    lap = numpy.zeros_like(gray)
    lap[1:-1, 1:-1] = (
        -4 * gray[1:-1, 1:-1]
        + gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
    )
    variance = float(numpy.var(lap))

    if variance <= 0.002:
        return 1.0
    if variance <= 0.008:
        return 0.85
    if variance <= 0.02:
        return 0.65
    return max(0.1, 1.0 - variance * 15.0)


def compute_symmetry_score(gray: numpy.ndarray) -> float:
    height, width = gray.shape
    half = width // 2
    if half < 4:
        return 0.0
    left = gray[:, :half]
    right = gray[:, width - half :]
    mirrored = numpy.fliplr(right)
    difference = float(numpy.mean(numpy.abs(left - mirrored)))
    return max(0.0, min(1.0, 1.0 - (difference / 0.35)))


def downsample_mask(mask: numpy.ndarray, max_dim: int = 128) -> numpy.ndarray:
    image = Image.fromarray((mask.astype(numpy.uint8) * 255), mode="L")
    width, height = image.size
    scale = min(1.0, max_dim / max(width, height))
    if scale < 1.0:
        image = image.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.Resampling.NEAREST)
    return numpy.asarray(image, dtype=numpy.uint8) > 0


def count_connected_components(mask: numpy.ndarray, *, min_pixels: int = 20) -> int:
    reduced = downsample_mask(mask)
    height, width = reduced.shape
    visited = numpy.zeros_like(reduced, dtype=bool)
    components = 0
    for row in range(height):
        for column in range(width):
            if not reduced[row, column] or visited[row, column]:
                continue
            stack = [(row, column)]
            visited[row, column] = True
            pixels = 0
            while stack:
                current_row, current_column = stack.pop()
                pixels += 1
                for delta_row, delta_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_column = current_column + delta_column
                    if not (0 <= next_row < height and 0 <= next_column < width):
                        continue
                    if visited[next_row, next_column] or not reduced[next_row, next_column]:
                        continue
                    visited[next_row, next_column] = True
                    stack.append((next_row, next_column))
            if pixels >= min_pixels:
                components += 1
    return components


def compute_subject_mask(img: numpy.ndarray) -> numpy.ndarray:
    gray = rgb_to_gray_array(img)
    saliency = compute_edge_saliency(gray)
    brightness_centered = numpy.abs(gray - float(gray.mean()))
    subject_energy = saliency + (brightness_centered * 0.6)
    threshold = float(numpy.quantile(subject_energy, 0.88))
    return subject_energy >= threshold


def count_hue_clusters(img: numpy.ndarray, mask: numpy.ndarray) -> int:
    masked = mask & (img.max(axis=2) - img.min(axis=2) > 0.45)
    if not numpy.any(masked):
        return 0
    rgb = img[masked]
    red = rgb[:, 0]
    green = rgb[:, 1]
    blue = rgb[:, 2]
    max_channel = numpy.max(rgb, axis=1)
    min_channel = numpy.min(rgb, axis=1)
    delta = max_channel - min_channel + 1e-6
    hue = numpy.zeros_like(max_channel)

    red_mask = max_channel == red
    green_mask = max_channel == green
    blue_mask = max_channel == blue
    hue[red_mask] = ((green[red_mask] - blue[red_mask]) / delta[red_mask]) % 6.0
    hue[green_mask] = ((blue[green_mask] - red[green_mask]) / delta[green_mask]) + 2.0
    hue[blue_mask] = ((red[blue_mask] - green[blue_mask]) / delta[blue_mask]) + 4.0
    hue = (hue / 6.0) % 1.0

    buckets = numpy.unique(numpy.floor(hue * 6.0).astype(int))
    return int(len(buckets))


def subject_intrusion_ratio(mask: numpy.ndarray, box: list[float]) -> float:
    height, width = mask.shape
    x1 = max(0, min(width, int(round(float(box[0]) * width))))
    y1 = max(0, min(height, int(round(float(box[1]) * height))))
    x2 = max(0, min(width, int(round(float(box[2]) * width))))
    y2 = max(0, min(height, int(round(float(box[3]) * height))))
    if x2 <= x1 or y2 <= y1:
        return 0.0
    zone = mask[y1:y2, x1:x2]
    if zone.size == 0:
        return 0.0
    return float(zone.mean())


def mask_occupancy(mask: numpy.ndarray) -> float:
    if mask.size == 0:
        return 0.0
    return float((mask > 0).mean())


def mask_bounding_box(mask: numpy.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = numpy.nonzero(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def bbox_iou(first: tuple[int, int, int, int] | None, second: tuple[int, int, int, int] | None) -> float:
    if first is None or second is None:
        return 0.0
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    if right <= left or bottom <= top:
        return 0.0
    intersection = float((right - left) * (bottom - top))
    first_area = float(max(1, first[2] - first[0]) * max(1, first[3] - first[1]))
    second_area = float(max(1, second[2] - second[0]) * max(1, second[3] - second[1]))
    union = first_area + second_area - intersection
    return intersection / max(union, 1.0)


def detect_control_asset_leakage(
    image: Image.Image,
    *,
    composition_control: dict[str, Any],
) -> dict[str, Any]:
    if not bool(composition_control.get("active")):
        return {"active": False, "leaked": False}

    preview_path = str(composition_control.get("preview_path", "")).strip()
    if not preview_path:
        return {"active": True, "leaked": False, "reason": "missing preview_path"}

    try:
        preview_image = Image.open(Path(preview_path)).convert("RGB")
    except Exception:
        return {"active": True, "leaked": False, "reason": "unreadable preview_path"}

    if preview_image.size != image.size:
        preview_image = preview_image.resize(image.size, Image.Resampling.BICUBIC)

    final_rgb = normalize_rgb_image(image)
    preview_rgb = normalize_rgb_image(preview_image)
    preview_subject_mask = compute_subject_mask(preview_rgb)
    final_subject_mask = compute_subject_mask(final_rgb)

    preview_occupancy = mask_occupancy(preview_subject_mask)
    final_occupancy = mask_occupancy(final_subject_mask)
    preview_bbox = mask_bounding_box(preview_subject_mask)
    final_bbox = mask_bounding_box(final_subject_mask)
    overlap = bbox_iou(preview_bbox, final_bbox)

    diff = numpy.abs(final_rgb.astype(numpy.float32) - preview_rgb.astype(numpy.float32)) / 255.0
    preview_inside = preview_subject_mask > 0
    preview_outside = ~preview_inside
    inside_delta = float(diff[preview_inside].mean()) if bool(preview_inside.any()) else 1.0
    outside_delta = float(diff[preview_outside].mean()) if bool(preview_outside.any()) else 1.0
    final_gray = rgb_to_gray_array(final_rgb)
    outside_noise = (
        float(final_gray[preview_outside].std()) / 255.0 if bool(preview_outside.any()) else 0.0
    )

    leaked = bool(
        0.02 <= preview_occupancy <= 0.28
        and final_occupancy <= max(0.22, preview_occupancy * 1.6)
        and overlap >= 0.72
        and inside_delta <= 0.22
        and outside_delta <= 0.08
        and outside_noise <= 0.12
    )
    return {
        "active": True,
        "leaked": leaked,
        "metrics": {
            "preview_occupancy": round(preview_occupancy, 4),
            "final_occupancy": round(final_occupancy, 4),
            "bbox_iou": round(overlap, 4),
            "inside_delta": round(inside_delta, 4),
            "outside_delta": round(outside_delta, 4),
            "outside_noise": round(outside_noise, 4),
        },
    }


def evaluate_visual_contract(
    image: Image.Image,
    *,
    contract_config: dict[str, Any],
) -> dict[str, Any]:
    contract_metrics = dict(contract_config.get("contract_metrics", {}))
    if not contract_metrics:
        return {}

    img = normalize_rgb_image(image)
    gray = rgb_to_gray_array(img)
    saliency = compute_edge_saliency(gray)
    subject_mask = compute_subject_mask(img)

    asymmetry = score_asymmetry_ratio(gray, saliency)
    palette, accent_clusters = score_palette_discipline(img)
    focal = score_focal_clarity(img)
    noise = score_visual_noise_metric(img)
    symmetry = compute_symmetry_score(gray)
    center_mass = float(
        saliency[:, int(gray.shape[1] * 0.35) : int(gray.shape[1] * 0.65)].sum()
        / max(float(saliency.sum()), 1e-8)
    )
    subject_clusters = count_connected_components(subject_mask)

    weights = {entry["id"]: float(entry["weight"]) for entry in contract_metrics.get("metrics", []) if isinstance(entry, dict)}
    thresholds = {
        entry["id"]: float(entry["pass_threshold"])
        for entry in contract_metrics.get("metrics", [])
        if isinstance(entry, dict)
    }
    scores = {
        "asymmetry_ratio": round(asymmetry, 3),
        "palette_discipline": round(palette, 3),
        "focal_clarity": round(focal, 3),
        "visual_noise": round(noise, 3),
    }
    overall = 0.0
    for metric_id, value in scores.items():
        overall += float(value) * float(weights.get(metric_id, 0.0))

    caption_safe_zone = contract_config.get("caption_safe_zone") or contract_config.get("caption_safe_defaults") or {}
    subtitle_box = caption_safe_zone.get("subtitles", [0.08, 0.74, 0.92, 0.96])
    subtitle_intrusion = subject_intrusion_ratio(subject_mask, subtitle_box)
    leakage_summary = detect_control_asset_leakage(
        image,
        composition_control=dict(contract_config.get("composition_control", {})),
    )

    hard_fails: list[str] = []
    if accent_clusters > 1:
        hard_fails.append("more_than_one_saturated_accent")
    if center_mass >= 0.48:
        hard_fails.append("center_weighted_primary_subject")
    if symmetry >= 0.82:
        hard_fails.append("symmetry_too_high")
    if subject_clusters > int(contract_config.get("max_subject_clusters", 3) or 3):
        hard_fails.append("subject_count_exceeds_limit")
    if subtitle_intrusion >= 0.12:
        hard_fails.append("subtitle_band_intrusion")
    if bool(contract_config.get("detected_text", False)):
        hard_fails.append("detected_text")
    if leakage_summary.get("leaked"):
        hard_fails.append("control_asset_leakage")

    failing_metrics = [
        metric_id
        for metric_id, value in scores.items()
        if metric_id in thresholds and float(value) < float(thresholds[metric_id])
    ]
    failures = list(dict.fromkeys(hard_fails + [f"{metric_id}_below_threshold" for metric_id in failing_metrics]))
    summary = {
        "style_id": str(contract_metrics.get("style_id", contract_config.get("style_id", ""))).strip(),
        "scores": scores,
        "overall_score": round(float(overall), 3),
        "overall_pass_threshold": float(contract_metrics.get("overall_pass_threshold", 0.78) or 0.78),
        "pass": float(overall) >= float(contract_metrics.get("overall_pass_threshold", 0.78) or 0.78)
        and not failures,
        "hard_fail_checks": list(contract_metrics.get("hard_fail_checks", [])),
        "hard_fails": hard_fails,
        "failures": failures,
        "metrics": {
            "accent_clusters": accent_clusters,
            "center_mass": round(center_mass, 4),
            "symmetry_score": round(symmetry, 4),
            "subject_clusters": int(subject_clusters),
            "subtitle_intrusion": round(subtitle_intrusion, 4),
            "control_asset_leakage": leakage_summary.get("metrics", {}),
        },
    }
    return summary


def audit_visual_qc_artifact(
    image: Image.Image,
    *,
    ban_scanlines: bool = False,
    contract_config: dict[str, Any] | None = None,
    debug_dir: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    grayscale = image.convert("L")
    source_width, source_height = grayscale.size
    analysis_width = min(VISUAL_QC_MAX_WIDTH, source_width)
    if analysis_width != source_width:
        analysis_height = max(VISUAL_QC_MIN_DIM, round(source_height * (analysis_width / source_width)))
        grayscale = grayscale.resize((analysis_width, analysis_height), Image.Resampling.BICUBIC)
    analysis_width, analysis_height = grayscale.size
    if analysis_width < 16 or analysis_height < VISUAL_QC_MIN_DIM:
        raise WorkflowError(
            f"Visual QC requires an artifact at least 16x{VISUAL_QC_MIN_DIM}, got "
            f"{analysis_width}x{analysis_height} after normalization."
        )

    array = numpy.asarray(grayscale, dtype=numpy.float32)
    row_diff = numpy.abs(numpy.diff(array, axis=0)).mean(axis=1)
    col_diff = numpy.abs(numpy.diff(array, axis=1)).mean(axis=0)

    row_threshold = max(VISUAL_QC_ROW_DIFF_FLOOR, float(numpy.percentile(row_diff, 75)))
    flagged_rows = row_diff >= row_threshold
    stripe_coverage = float(flagged_rows.mean())
    row_median = float(numpy.median(row_diff))
    col_median = float(numpy.median(col_diff))
    row_p95 = float(numpy.percentile(row_diff, 95))
    col_p95 = float(numpy.percentile(col_diff, 95))
    median_ratio = row_median / max(col_median, 1e-6)
    p95_ratio = row_p95 / max(col_p95, 1e-6)
    score = stripe_coverage * median_ratio * p95_ratio

    failures: list[str] = []
    if ban_scanlines and score >= VISUAL_QC_SCORE_THRESHOLD:
        failures.append(
            "horizontal stripe amplification detected: "
            f"score {score:.2f} exceeds threshold {VISUAL_QC_SCORE_THRESHOLD:.2f}"
        )

    metrics = {
        "source_size": {"width": source_width, "height": source_height},
        "analysis_size": {"width": analysis_width, "height": analysis_height},
        "row_diff_threshold": round(row_threshold, 4),
        "stripe_coverage": round(stripe_coverage, 6),
        "row_median": round(row_median, 6),
        "col_median": round(col_median, 6),
        "row_p95": round(row_p95, 6),
        "col_p95": round(col_p95, 6),
        "median_ratio": round(median_ratio, 6),
        "p95_ratio": round(p95_ratio, 6),
        "flagged_row_count": int(flagged_rows.sum()),
    }
    summary = {
        "status": "failed" if failures else "ok",
        "score": round(float(score), 6),
        "threshold": VISUAL_QC_SCORE_THRESHOLD,
        "ban_scanlines": bool(ban_scanlines),
        "metrics": metrics,
        "warnings": [],
        "failures": failures,
        "contract": {},
    }
    if not ban_scanlines and score >= VISUAL_QC_SCORE_THRESHOLD:
        summary["warnings"].append(
            "horizontal stripe amplification detected but not enforced for this preset"
        )

    if contract_config:
        contract_summary = evaluate_visual_contract(
            image,
            contract_config=contract_config,
        )
        if contract_summary:
            summary["contract"] = contract_summary
            if contract_summary["failures"]:
                summary["failures"] = list(summary["failures"]) + list(contract_summary["failures"])
                summary["status"] = "failed"

    debug_artifacts: list[str] = []
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        normalized_path = debug_dir / "artifact__analysis_grayscale.png"
        ImageOps.autocontrast(grayscale).save(normalized_path)
        debug_artifacts.append(str(normalized_path))

        profile_path = debug_dir / "artifact__banding_profile.png"
        build_visual_qc_profile_image(
            row_diff,
            threshold=row_threshold,
            flagged_rows=flagged_rows,
        ).save(profile_path)
        debug_artifacts.append(str(profile_path))

        metrics_path = debug_dir / "visual_qc_metrics.json"
        metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        debug_artifacts.append(str(metrics_path))

    return summary, debug_artifacts


def cleanup_final_text_artifact(
    artifact_path: Path,
    output_path: Path,
    *,
    intent_path: Path | None,
    intent: dict[str, Any] | None,
    policy_path: Path,
    policy: dict[str, Any],
    repair_manifest_path: Path | None,
    repair_manifest: dict[str, Any] | None,
    debug_dir: Path | None,
) -> dict[str, Any]:
    cleanup_policy = dict(policy.get("post_final_cleanup") or REPAIR_POST_FINAL_CLEANUP_DEFAULTS)
    if not bool(cleanup_policy.get("enabled")):
        raise WorkflowError(f"Post-final cleanup is not enabled in repair policy {policy_path}.")
    if str(cleanup_policy.get("mode", "")).strip().lower() != "erase_only":
        raise WorkflowError(f"Unsupported post-final cleanup mode in {policy_path}: {cleanup_policy.get('mode')!r}")

    base_image = Image.open(artifact_path).convert("RGBA")
    approved_bounds: list[tuple[int, int, int, int]] = []
    if intent is not None:
        approved_bounds.extend(collect_approved_bounds(base_image, intent))
    if intent is not None and repair_manifest is not None:
        approved_bounds.extend(collect_repair_bounds(base_image, repair_manifest))
    debug_artifacts: list[str] = []
    current_image = base_image.copy()
    all_detected_leaks: list[dict[str, Any]] = []
    all_cleanup_regions: list[dict[str, Any]] = []
    rounds: list[dict[str, Any]] = []
    residual_validation: dict[str, Any] = {
        "policy": {"zone_ocr": "off", "unapproved_text": "fail"},
        "zone_results": [],
        "unapproved_text": [],
        "warnings": [],
        "failures": [],
        "status": "ok",
    }

    def run_residual_audit(image: Image.Image, round_debug_dir: Path | None) -> tuple[dict[str, Any], list[str]]:
        if intent is None:
            return audit_zero_letter_artifact(image, debug_dir=round_debug_dir)
        if repair_manifest is not None:
            return audit_repaired_text_artifact(image, repair_manifest, intent, debug_dir=round_debug_dir)
        return audit_source_text_artifact(image, intent, debug_dir=round_debug_dir)

    for round_index in range(int(cleanup_policy["max_rounds"])):
        round_label = f"round_{round_index + 1:02d}"
        round_debug_dir = debug_dir / round_label if debug_dir is not None else None
        leaks = detect_unapproved_text(current_image, approved_bounds)
        all_detected_leaks.extend(leaks)
        round_debug_artifacts = emit_text_audit_debug_artifacts(
            current_image,
            leaks,
            approved_bounds=approved_bounds,
            debug_dir=round_debug_dir,
        )
        debug_artifacts.extend(round_debug_artifacts)
        if not leaks:
            rounds.append(
                {
                    "round": round_index + 1,
                    "detected_leaks": [],
                    "cleanup_regions": [],
                    "residual_validation": residual_validation,
                    "debug_artifacts": round_debug_artifacts,
                }
            )
            break

        cleanup_regions = merge_leak_regions(
            leaks,
            image_size=current_image.size,
            max_regions=int(cleanup_policy["max_regions"]),
        )
        for region in cleanup_regions:
            bounds = region["bounds"]
            rect = (
                int(bounds["left"]),
                int(bounds["top"]),
                int(bounds["left"]) + int(bounds["width"]),
                int(bounds["top"]) + int(bounds["height"]),
            )
            current_image, mask = soft_inpaint_rectangle(current_image, rect)
            if round_debug_dir is not None:
                region_dir = round_debug_dir / region["region_id"]
                region_dir.mkdir(parents=True, exist_ok=True)
                mask_path = region_dir / "mask.png"
                mask.save(mask_path)
                region["mask_path"] = str(mask_path)
                round_debug_artifacts.append(str(mask_path))
                debug_artifacts.append(str(mask_path))
            else:
                region["mask_path"] = ""
        all_cleanup_regions.extend(cleanup_regions)

        cleaned_debug_path = None
        if round_debug_dir is not None:
            cleaned_debug_path = round_debug_dir / "artifact__cleaned.png"
            current_image.save(cleaned_debug_path)
            round_debug_artifacts.append(str(cleaned_debug_path))
            debug_artifacts.append(str(cleaned_debug_path))

        residual_debug_dir = round_debug_dir / "residual_audit" if round_debug_dir is not None else None
        residual_validation, residual_debug_artifacts = run_residual_audit(current_image, residual_debug_dir)
        round_debug_artifacts.extend(residual_debug_artifacts)
        debug_artifacts.extend(residual_debug_artifacts)
        rounds.append(
            {
                "round": round_index + 1,
                "detected_leaks": leaks,
                "cleanup_regions": cleanup_regions,
                "residual_validation": residual_validation,
                "debug_artifacts": round_debug_artifacts,
            }
        )
        if residual_validation["status"] == "ok":
            break

    output_path.parent.mkdir(parents=True, exist_ok=True)
    current_image.save(output_path)

    cleanup_manifest_path = (
        debug_dir / "cleanup_manifest.json"
        if debug_dir is not None
        else output_path.with_name(f"{output_path.stem}__cleanup.manifest.json")
    )
    summary = {
        "artifact_path": str(artifact_path),
        "output_artifact": str(output_path),
        "intent_path": str(intent_path) if intent_path is not None else "",
        "policy_path": str(policy_path),
        "policy": policy,
        "post_final_cleanup_policy": cleanup_policy,
        "repair_manifest_path": str(repair_manifest_path) if repair_manifest_path is not None else "",
        "artifact_size": {"width": current_image.width, "height": current_image.height},
        "detected_leaks": all_detected_leaks,
        "cleanup_regions": all_cleanup_regions,
        "rounds": rounds,
        "residual_validation": residual_validation,
        "debug_artifacts": debug_artifacts,
        "cleanup_manifest_path": str(cleanup_manifest_path),
        "status": str(residual_validation["status"]),
    }
    cleanup_manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def validate_artifact(
    image: Image.Image,
    intent: dict[str, Any],
    *,
    repair_manifest: dict[str, Any] | None,
    debug_dir: Path | None,
) -> tuple[dict[str, Any], list[str]]:
    approved_bounds: list[tuple[int, int, int, int]] = []
    zone_results: list[dict[str, Any]] = []
    debug_artifacts: list[str] = []

    for zone in intent["zones"]:
        quad_pixels = quad_to_pixels(zone["quad_norm"], image.width, image.height)
        approved_bounds.append(quad_bounds(quad_pixels, padding=12))
        zone_results.append(zone_ocr_result(image, zone, quad_pixels))
        if debug_dir is not None and (zone["debug_emit_crop"] or True):
            debug_artifacts.extend(emit_zone_debug_artifacts(image, zone, quad_pixels, debug_dir=debug_dir))

    repair_zone_results: list[dict[str, Any]] = []
    if repair_manifest is not None:
        approved_bounds.extend(collect_repair_bounds(image, repair_manifest))
        repair_zone_results = repair_region_ocr_results(image, repair_manifest)
    leaks = detect_unapproved_text(image, approved_bounds)
    validation = (
        evaluate_validation_with_repair(intent, zone_results, repair_zone_results, leaks)
        if repair_manifest is not None
        else evaluate_validation(intent, zone_results, leaks)
    )
    return validation, debug_artifacts


def apply_raster_typography(
    image_path: Path,
    output_path: Path,
    *,
    intent: dict[str, Any],
    repair_manifest: dict[str, Any] | None,
    debug_dir: Path | None,
) -> dict[str, Any]:
    base_image = Image.open(image_path).convert("RGBA")

    for zone in intent["zones"]:
        quad_pixels = quad_to_pixels(zone["quad_norm"], base_image.width, base_image.height)
        zone_size = quad_estimated_size(quad_pixels)
        base_image = neutralize_zone(base_image, zone, quad_pixels)
        base_image = add_zone_underlay(base_image, zone, quad_pixels)
        text_patch = build_text_patch(zone)
        zone_canvas = place_patch_on_canvas(
            text_patch,
            canvas_size=zone_size,
            fit_mode=str(zone["fit_mode"]),
            padding_px=float(zone["padding_px"]),
            align_x=str(zone["align_x"]),
            align_y=str(zone["align_y"]),
            shadow=zone["shadow"],
        )
        warped_patch = warp_patch_to_quad(zone_canvas, base_image.size, quad_pixels)
        base_image = blend_overlay(base_image, warped_patch, str(zone["blend_mode"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_image.save(output_path)

    validation, debug_artifacts = validate_artifact(
        base_image,
        intent,
        repair_manifest=repair_manifest,
        debug_dir=debug_dir,
    )
    return {
        "image": base_image,
        "validation": validation,
        "debug_artifacts": debug_artifacts,
    }


def validate_target(target: str, intent: dict[str, Any]) -> dict[str, str]:
    if target not in TARGET_COMPATIBILITY:
        raise WorkflowError(f"Typography target {target!r} is not implemented yet.")
    compatibility = TARGET_COMPATIBILITY[target]
    if str(intent["artifact_type"]) != compatibility["artifact_type"]:
        raise WorkflowError(
            f"Typography intent artifact_type={intent['artifact_type']!r} does not match target {target!r}."
        )
    if str(intent["application_phase"]) != compatibility["application_phase"]:
        raise WorkflowError(
            f"Typography intent application_phase={intent['application_phase']!r} does not match target {target!r}."
        )
    return compatibility


def make_summary(
    *,
    target: str,
    compatibility: dict[str, str],
    intent: dict[str, Any],
    intent_path: Path,
    artifact_path: Path,
    output_path: Path | None,
    validation: dict[str, Any],
    debug_artifacts: list[str],
) -> dict[str, Any]:
    summary = {
        "target": target,
        "adapter": compatibility["adapter"],
        "artifact_type": intent["artifact_type"],
        "application_phase": intent["application_phase"],
        "artifact_path": str(artifact_path),
        "intent_path": str(intent_path),
        "enabled": bool(intent["enabled"]),
        "mode": str(intent["mode"]),
        "zone_count": len(intent["zones"]),
        "zones": intent["zones"],
        "validation": validation,
        "debug_artifacts": debug_artifacts,
        "apply_stage_alias": str(intent["source"].get("legacy_apply_stage", "")),
    }
    if output_path is not None:
        summary["output_artifact"] = str(output_path)
    return summary


def repair_source_text_artifact(
    artifact_path: Path,
    output_path: Path,
    *,
    policy_path: Path,
    policy: dict[str, Any],
    debug_dir: Path | None,
) -> dict[str, Any]:
    ensure_ollama_runtime(str(policy["llm_model"]))
    base_image = Image.open(artifact_path).convert("RGBA")
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        source_path = debug_dir / "artifact.png"
        base_image.save(source_path)
    else:
        source_path = None

    regions = merge_candidate_regions(
        extract_candidate_tokens(base_image, confidence_floor=float(policy["ocr_confidence_floor"])),
        image_size=base_image.size,
        max_regions=int(policy["max_regions"]),
    )

    temp_root_context = tempfile.TemporaryDirectory(prefix="ce-repair-") if debug_dir is None else None
    temp_root = Path(temp_root_context.name) if temp_root_context is not None else debug_dir
    decisions: list[dict[str, Any]] = []
    debug_artifacts: list[str] = [str(source_path)] if source_path is not None else []
    try:
        for region in regions:
            bounds = region["bounds"]
            left = int(bounds["left"])
            top = int(bounds["top"])
            right = left + int(bounds["width"])
            bottom = top + int(bounds["height"])
            crop = base_image.crop((left, top, right, bottom))
            region_dir = temp_root / region["region_id"] if temp_root is not None else None
            if region_dir is not None:
                region_dir.mkdir(parents=True, exist_ok=True)
                crop_path = region_dir / "crop.png"
                crop.save(crop_path)
                if debug_dir is not None:
                    debug_artifacts.append(str(crop_path))
            else:
                crop_path = None

            ollama_prompt = ""
            ollama_response: dict[str, Any] | None = None
            llm_parsed: dict[str, Any] | None = None
            if region["ocr_confidence"] >= float(policy["ocr_confidence_floor"]) and crop_path is not None:
                ollama_prompt, ollama_response = classify_region_with_ollama(
                    crop_path=crop_path,
                    region=region,
                    policy=policy,
                )
                llm_parsed = dict(ollama_response["parsed"])
                if debug_dir is not None and region_dir is not None:
                    (region_dir / "ollama_prompt.txt").write_text(ollama_prompt, encoding="utf-8")
                    (region_dir / "ollama_response.json").write_text(
                        json.dumps(ollama_response, indent=2),
                        encoding="utf-8",
                    )
                    debug_artifacts.extend(
                        [str(region_dir / "ollama_prompt.txt"), str(region_dir / "ollama_response.json")]
                    )

            action_summary = choose_repair_action(region=region, policy=policy, llm_result=llm_parsed)
            decision = {
                "region_id": region["region_id"],
                "detected_text": region["detected_text"],
                "normalized_text": region["normalized_text"],
                "ocr_confidence": region["ocr_confidence"],
                "bounds": region["bounds"],
                "quad_norm": region["quad_norm"],
                "tokens": region["tokens"],
                "crop_path": str(crop_path) if crop_path is not None and debug_dir is not None else "",
                "ollama_prompt": ollama_prompt,
                "ollama_response": ollama_response["parsed"] if ollama_response is not None else None,
                "ollama_raw_response": ollama_response["raw_response"] if ollama_response is not None else "",
                "action": action_summary["action"],
                "surface_type": action_summary["surface_type"],
                "confidence": action_summary["confidence"],
                "corrected_text": action_summary["corrected_text"],
                "reason": action_summary["reason"],
                "mask_path": "",
                "redraw": None,
            }
            decisions.append(decision)

        cleared_image = base_image.copy()
        for decision in decisions:
            if decision["action"] not in {"erase", "rewrite"}:
                continue
            bounds = decision["bounds"]
            rect = (
                int(bounds["left"]),
                int(bounds["top"]),
                int(bounds["left"]) + int(bounds["width"]),
                int(bounds["top"]) + int(bounds["height"]),
            )
            cleared_image, mask = soft_inpaint_rectangle(cleared_image, rect)
            if debug_dir is not None and temp_root is not None:
                region_dir = temp_root / decision["region_id"]
                region_dir.mkdir(parents=True, exist_ok=True)
                mask_path = region_dir / "mask.png"
                mask.save(mask_path)
                decision["mask_path"] = str(mask_path)
                debug_artifacts.append(str(mask_path))

        cleared_path = None
        if debug_dir is not None:
            cleared_path = debug_dir / "artifact__cleared.png"
            cleared_image.save(cleared_path)
            debug_artifacts.append(str(cleared_path))

        final_image = cleared_image.copy()
        for decision in decisions:
            if decision["action"] != "rewrite" or not decision["corrected_text"]:
                continue
            final_image, redraw_details = apply_repair_redraw(
                final_image,
                decision,
                decision["corrected_text"],
            )
            decision["redraw"] = redraw_details

        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_image.save(output_path)

        rewrite_regions = [decision for decision in decisions if decision["action"] == "rewrite"]
        residual_debug_dir = debug_dir / "residual_audit" if debug_dir is not None else None
        residual_validation, residual_debug_artifacts = internal_residual_repair_validation(
            final_image,
            rewrite_regions,
            debug_dir=residual_debug_dir,
        )
        debug_artifacts.extend(residual_debug_artifacts)
        repair_manifest_path = (
            debug_dir / "repair_manifest.json"
            if debug_dir is not None
            else output_path.with_name(f"{output_path.stem}__repair.manifest.json")
        )
        summary = {
            "artifact_path": str(artifact_path),
            "output_artifact": str(output_path),
            "policy_path": str(policy_path),
            "policy": policy,
            "artifact_size": {"width": final_image.width, "height": final_image.height},
            "detected_regions": regions,
            "regions": decisions,
            "rewrite_regions": rewrite_regions,
            "erase_regions": [decision for decision in decisions if decision["action"] == "erase"],
            "ignored_regions": [decision for decision in decisions if decision["action"] == "ignore"],
            "inpaint_output_artifact": str(cleared_path) if cleared_path is not None else "",
            "residual_validation": residual_validation,
            "debug_artifacts": debug_artifacts,
            "repair_manifest_path": str(repair_manifest_path),
            "status": str(residual_validation["status"]),
        }
        repair_manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary
    finally:
        if temp_root_context is not None:
            temp_root_context.cleanup()


def command_apply(args: argparse.Namespace) -> int:
    target = str(args.target)
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    intent_path = resolve_absolute_path(args.intent, label="--intent")
    if not artifact_path.exists():
        raise WorkflowError(f"Input artifact for typography was not found: {artifact_path}")
    if not intent_path.exists():
        raise WorkflowError(f"Typography intent was not found: {intent_path}")
    output_path = resolve_absolute_path(args.output, label="--output") if args.output else default_output_path(artifact_path)
    repair_manifest_path = (
        resolve_absolute_path(args.repair_manifest, label="--repair-manifest") if args.repair_manifest else None
    )
    if repair_manifest_path is not None and not repair_manifest_path.exists():
        raise WorkflowError(f"Repair manifest was not found: {repair_manifest_path}")
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    try:
        intent = load_typography_intent(intent_path)
    except TypographyContractError as exc:
        raise WorkflowError(str(exc)) from exc
    compatibility = validate_target(target, intent)
    repair_manifest = load_repair_manifest(repair_manifest_path) if repair_manifest_path is not None else None

    result = apply_raster_typography(
        artifact_path,
        output_path,
        intent=intent,
        repair_manifest=repair_manifest,
        debug_dir=debug_dir,
    )
    summary = make_summary(
        target=target,
        compatibility=compatibility,
        intent=intent,
        intent_path=intent_path,
        artifact_path=artifact_path,
        output_path=output_path,
        validation=result["validation"],
        debug_artifacts=result["debug_artifacts"],
    )
    if repair_manifest_path is not None:
        summary["repair_manifest_path"] = str(repair_manifest_path)
    print(json.dumps(summary, indent=2))
    if result["validation"]["failures"]:
        failure_text = "; ".join(result["validation"]["failures"])
        raise WorkflowError(f"Typography validation failed for {output_path}: {failure_text}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    target = str(args.target)
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    intent_path = resolve_absolute_path(args.intent, label="--intent")
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for typography validation was not found: {artifact_path}")
    if not intent_path.exists():
        raise WorkflowError(f"Typography intent was not found: {intent_path}")
    repair_manifest_path = (
        resolve_absolute_path(args.repair_manifest, label="--repair-manifest") if args.repair_manifest else None
    )
    if repair_manifest_path is not None and not repair_manifest_path.exists():
        raise WorkflowError(f"Repair manifest was not found: {repair_manifest_path}")
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    try:
        intent = load_typography_intent(intent_path)
    except TypographyContractError as exc:
        raise WorkflowError(str(exc)) from exc
    compatibility = validate_target(target, intent)
    repair_manifest = load_repair_manifest(repair_manifest_path) if repair_manifest_path is not None else None

    image = Image.open(artifact_path).convert("RGBA")
    validation, debug_artifacts = validate_artifact(
        image,
        intent,
        repair_manifest=repair_manifest,
        debug_dir=debug_dir,
    )
    summary = make_summary(
        target=target,
        compatibility=compatibility,
        intent=intent,
        intent_path=intent_path,
        artifact_path=artifact_path,
        output_path=None,
        validation=validation,
        debug_artifacts=debug_artifacts,
    )
    if repair_manifest_path is not None:
        summary["repair_manifest_path"] = str(repair_manifest_path)
    print(json.dumps(summary, indent=2))
    if validation["failures"]:
        failure_text = "; ".join(validation["failures"])
        raise WorkflowError(f"Typography validation failed for {artifact_path}: {failure_text}")
    return 0


def command_audit_zero_letter(args: argparse.Namespace) -> int:
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for zero-letter audit was not found: {artifact_path}")
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    image = Image.open(artifact_path).convert("RGBA")
    validation, debug_artifacts = audit_zero_letter_artifact(image, debug_dir=debug_dir)
    summary = {
        "artifact_path": str(artifact_path),
        "status": validation["status"],
        "unapproved_text": validation["unapproved_text"],
        "warnings": validation["warnings"],
        "failures": validation["failures"],
        "debug_artifacts": debug_artifacts,
    }
    print(json.dumps(summary, indent=2))
    if validation["failures"]:
        failure_text = "; ".join(validation["failures"])
        raise WorkflowError(f"Zero-letter audit failed for {artifact_path}: {failure_text}")
    return 0


def command_audit_source_text(args: argparse.Namespace) -> int:
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    intent_path = resolve_absolute_path(args.intent, label="--intent")
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for source-text audit was not found: {artifact_path}")
    if not intent_path.exists():
        raise WorkflowError(f"Typography intent was not found: {intent_path}")
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    try:
        intent = load_typography_intent(intent_path)
    except TypographyContractError as exc:
        raise WorkflowError(str(exc)) from exc

    image = Image.open(artifact_path).convert("RGBA")
    validation, debug_artifacts = audit_source_text_artifact(image, intent, debug_dir=debug_dir)
    summary = {
        "artifact_path": str(artifact_path),
        "intent_path": str(intent_path),
        "status": validation["status"],
        "unapproved_text": validation["unapproved_text"],
        "warnings": validation["warnings"],
        "failures": validation["failures"],
        "debug_artifacts": debug_artifacts,
    }
    print(json.dumps(summary, indent=2))
    if validation["failures"]:
        failure_text = "; ".join(validation["failures"])
        raise WorkflowError(f"Source-text audit failed for {artifact_path}: {failure_text}")
    return 0


def command_repair_source_text(args: argparse.Namespace) -> int:
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    policy_path = resolve_absolute_path(args.policy, label="--policy")
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for source-text repair was not found: {artifact_path}")
    if not policy_path.exists():
        raise WorkflowError(f"Source-text repair policy was not found: {policy_path}")
    output_path = (
        resolve_absolute_path(args.output, label="--output") if args.output else default_repair_output_path(artifact_path)
    )
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    policy = load_repair_policy(policy_path)
    summary = repair_source_text_artifact(
        artifact_path,
        output_path,
        policy_path=policy_path,
        policy=policy,
        debug_dir=debug_dir,
    )
    print(json.dumps(summary, indent=2))
    return 0


def command_audit_repaired_text(args: argparse.Namespace) -> int:
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    repair_manifest_path = resolve_absolute_path(args.repair_manifest, label="--repair-manifest")
    intent_path = resolve_absolute_path(args.intent, label="--intent")
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for repaired-text audit was not found: {artifact_path}")
    if not repair_manifest_path.exists():
        raise WorkflowError(f"Repair manifest was not found: {repair_manifest_path}")
    if not intent_path.exists():
        raise WorkflowError(f"Typography intent was not found: {intent_path}")
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    try:
        intent = load_typography_intent(intent_path)
    except TypographyContractError as exc:
        raise WorkflowError(str(exc)) from exc
    repair_manifest = load_repair_manifest(repair_manifest_path)
    image = Image.open(artifact_path).convert("RGBA")
    validation, debug_artifacts = audit_repaired_text_artifact(
        image,
        repair_manifest,
        intent,
        debug_dir=debug_dir,
    )
    summary = {
        "artifact_path": str(artifact_path),
        "intent_path": str(intent_path),
        "repair_manifest_path": str(repair_manifest_path),
        "status": validation["status"],
        "unapproved_text": validation["unapproved_text"],
        "warnings": validation["warnings"],
        "failures": validation["failures"],
        "repair_region_results": validation.get("repair_region_results", []),
        "debug_artifacts": debug_artifacts,
    }
    print(json.dumps(summary, indent=2))
    if validation["failures"]:
        failure_text = "; ".join(validation["failures"])
        raise WorkflowError(f"Repaired-text audit failed for {artifact_path}: {failure_text}")
    return 0


def command_cleanup_final_text(args: argparse.Namespace) -> int:
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    intent_path = resolve_absolute_path(args.intent, label="--intent") if args.intent else None
    policy_path = resolve_absolute_path(args.policy, label="--policy")
    repair_manifest_path = (
        resolve_absolute_path(args.repair_manifest, label="--repair-manifest") if args.repair_manifest else None
    )
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for final-text cleanup was not found: {artifact_path}")
    if not policy_path.exists():
        raise WorkflowError(f"Source-text repair policy was not found: {policy_path}")
    if intent_path is not None and not intent_path.exists():
        raise WorkflowError(f"Typography intent was not found: {intent_path}")
    if repair_manifest_path is not None and not repair_manifest_path.exists():
        raise WorkflowError(f"Repair manifest was not found: {repair_manifest_path}")
    output_path = (
        resolve_absolute_path(args.output, label="--output") if args.output else default_cleanup_output_path(artifact_path)
    )
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    intent: dict[str, Any] | None = None
    if intent_path is not None:
        try:
            intent = load_typography_intent(intent_path)
        except TypographyContractError as exc:
            raise WorkflowError(str(exc)) from exc
    policy = load_repair_policy(policy_path)
    repair_manifest = load_repair_manifest(repair_manifest_path) if repair_manifest_path is not None else None
    summary = cleanup_final_text_artifact(
        artifact_path,
        output_path,
        intent_path=intent_path,
        intent=intent,
        policy_path=policy_path,
        policy=policy,
        repair_manifest_path=repair_manifest_path,
        repair_manifest=repair_manifest,
        debug_dir=debug_dir,
    )
    print(json.dumps(summary, indent=2))
    residual_validation = summary["residual_validation"]
    if residual_validation["failures"]:
        failure_text = "; ".join(residual_validation["failures"])
        raise WorkflowError(f"Post-final cleanup audit failed for {artifact_path}: {failure_text}")
    return 0


def command_process_research_source(args: argparse.Namespace) -> int:
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for research-source processing was not found: {artifact_path}")
    policy_path = resolve_absolute_path(args.policy, label="--policy") if args.policy else None
    if policy_path is not None and not policy_path.exists():
        raise WorkflowError(f"Source-text repair policy was not found: {policy_path}")
    output_path = (
        resolve_absolute_path(args.output, label="--output") if args.output else default_cleanup_output_path(artifact_path)
    )
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    image = Image.open(artifact_path).convert("RGBA")
    audit_debug_dir = debug_dir / "zero_letter_audit" if debug_dir is not None else None
    validation, debug_artifacts = audit_zero_letter_artifact(image, debug_dir=audit_debug_dir)
    audit_manifest_path = (
        debug_dir / "zero_letter_audit.json"
        if debug_dir is not None
        else default_zero_letter_audit_manifest_path(artifact_path)
    )
    audit_payload = {
        "artifact_path": str(artifact_path),
        "status": validation["status"],
        "unapproved_text": validation["unapproved_text"],
        "warnings": validation["warnings"],
        "failures": validation["failures"],
        "debug_artifacts": debug_artifacts,
        "text_detection_manifest_path": str(audit_manifest_path),
    }
    audit_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    audit_manifest_path.write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")
    if not validation["failures"]:
        print(
            json.dumps(
                {
                    "artifact_path": str(artifact_path),
                    "status": "clear",
                    "text_detection_manifest_path": str(audit_manifest_path),
                    "cleanup_manifest_path": "",
                    "output_artifact": "",
                    "blocked_reason": "",
                    "debug_artifacts": debug_artifacts,
                },
                indent=2,
            )
        )
        return 0

    if policy_path is None:
        print(
            json.dumps(
                {
                    "artifact_path": str(artifact_path),
                    "status": "blocked",
                    "text_detection_manifest_path": str(audit_manifest_path),
                    "cleanup_manifest_path": "",
                    "output_artifact": "",
                    "blocked_reason": "Readable text was detected and no cleanup policy was provided.",
                    "debug_artifacts": debug_artifacts,
                },
                indent=2,
            )
        )
        return 0

    policy = load_repair_policy(policy_path)
    cleanup_debug_dir = debug_dir / "cleanup" if debug_dir is not None else None
    cleanup_summary = cleanup_final_text_artifact(
        artifact_path,
        output_path,
        intent_path=None,
        intent=None,
        policy_path=policy_path,
        policy=policy,
        repair_manifest_path=None,
        repair_manifest=None,
        debug_dir=cleanup_debug_dir,
    )
    residual_validation = cleanup_summary["residual_validation"]
    blocked_reason = ""
    status = "cleaned"
    if residual_validation["failures"]:
        status = "blocked"
        blocked_reason = "; ".join(residual_validation["failures"])
    print(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "status": status,
                "text_detection_manifest_path": str(audit_manifest_path),
                "cleanup_manifest_path": str(cleanup_summary["cleanup_manifest_path"]),
                "output_artifact": str(cleanup_summary["output_artifact"]),
                "blocked_reason": blocked_reason,
                "debug_artifacts": list(dict.fromkeys(debug_artifacts + cleanup_summary.get("debug_artifacts", []))),
                "residual_validation": residual_validation,
            },
            indent=2,
        )
    )
    return 0


def command_audit_visual_qc(args: argparse.Namespace) -> int:
    artifact_path = resolve_absolute_path(args.artifact, label="--artifact")
    if not artifact_path.exists():
        raise WorkflowError(f"Artifact for visual QC was not found: {artifact_path}")
    debug_dir = resolve_absolute_path(args.debug_dir, label="--debug-dir") if args.debug_dir else None

    image = Image.open(artifact_path).convert("RGBA")
    contract_config: dict[str, Any] | None = None
    if args.contract_config_json:
        try:
            parsed_contract = json.loads(str(args.contract_config_json))
        except json.JSONDecodeError as exc:
            raise WorkflowError("--contract-config-json must be valid JSON.") from exc
        if not isinstance(parsed_contract, dict):
            raise WorkflowError("--contract-config-json must decode to an object.")
        contract_config = parsed_contract
    summary, debug_artifacts = audit_visual_qc_artifact(
        image,
        ban_scanlines=bool(args.ban_scanlines),
        contract_config=contract_config,
        debug_dir=debug_dir,
    )
    semantic_summary: dict[str, Any] = {}
    semantic_debug_artifacts: list[str] = []
    semantic_profile_name = str(args.semantic_profile or "").strip()
    family = str(args.family or "").strip()
    preset = str(args.preset or "").strip()
    if semantic_profile_name:
        policy = load_guardrail_policy(resolve_absolute_path(args.repo_root, label="--repo-root"))
        semantic_profile = semantic_qc_profile_for(
            policy,
            family=family,
            preset=preset,
            profile_name=semantic_profile_name,
        )
        if not semantic_profile:
            raise WorkflowError(
                f"Semantic QC profile {semantic_profile_name!r} was not found for {family}/{preset}."
            )
        semantic_debug_dir = debug_dir / "semantic_qc" if debug_dir is not None else None
        semantic_summary, semantic_debug_artifacts = audit_semantic_qc_artifact(
            artifact_path,
            profile=semantic_profile,
            family=family,
            preset=preset,
            stage=str(args.semantic_stage),
            debug_dir=semantic_debug_dir,
        )
        summary["warnings"] = list(summary["warnings"]) + list(semantic_summary.get("warnings", []))
        summary["failures"] = list(summary["failures"]) + list(semantic_summary.get("failures", []))
        if summary["failures"]:
            summary["status"] = "failed"
    payload = {
        "artifact_path": str(artifact_path),
        **summary,
        "semantic": semantic_summary,
        "debug_artifacts": list(dict.fromkeys(debug_artifacts + semantic_debug_artifacts)),
    }
    print(json.dumps(payload, indent=2))
    if payload["failures"]:
        failure_text = "; ".join(payload["failures"])
        raise WorkflowError(f"Visual QC failed for {artifact_path}: {failure_text}")
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "apply":
            return command_apply(args)
        if args.command == "validate":
            return command_validate(args)
        if args.command == "audit-zero-letter":
            return command_audit_zero_letter(args)
        if args.command == "audit-source-text":
            return command_audit_source_text(args)
        if args.command == "repair-source-text":
            return command_repair_source_text(args)
        if args.command == "audit-repaired-text":
            return command_audit_repaired_text(args)
        if args.command == "cleanup-final-text":
            return command_cleanup_final_text(args)
        if args.command == "process-research-source":
            return command_process_research_source(args)
        if args.command == "audit-visual-qc":
            return command_audit_visual_qc(args)
        raise WorkflowError(f"Unknown command {args.command!r}")
    except WorkflowError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
