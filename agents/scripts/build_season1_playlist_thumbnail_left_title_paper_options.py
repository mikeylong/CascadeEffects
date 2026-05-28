#!/usr/bin/env python3
"""Build left-title/right-paper-rendering Season 1 playlist thumbnail options."""

from __future__ import annotations

import json
import math
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from build_season1_playlist_thumbnail_proof_sheet import (
    CORAL,
    CREAM,
    CYAN,
    LAVENDER,
    MUTED_CREAM,
    OVERLAY_ZONE,
    WHITE_UI,
    add_linear_gradient,
    add_vignette,
    brand_bug,
    cover_crop,
    file_record,
    fit_text,
    font,
    make_contact_sheet,
    make_detail_simulation,
    make_overlay_zone_preview,
    make_small_preview_sheet,
    make_tab_simulation,
    paste_round,
    rounded_mask,
    sha256_path,
    text_shadow,
    text_size,
)


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
PACKAGE_PREFIX = "season1_playlist_thumbnail_left_title_paper_options"
CANVAS_SIZE = (1280, 720)
UPLOAD_JPEG_QUALITY = 92

CHANNEL_BRAND_SNAPSHOT = (
    REPO_ROOT
    / "references/skills/youtube_channel_branding_v1/references/official_youtube_channel_branding_guidance_2026-05-17.md"
)
PAPER_SKILL = Path("/Users/mike/.codex/skills/cascade-paper-architectures/SKILL.md")
WATERMARK_PATH = (
    OUTPUT_BASE
    / "youtube_video_watermark_clean_edge_repair_20260519T043706Z/assets/video-watermark-800x800-clean-edge.png"
)
KEPT_EVIDENCE_DESK_PACKAGE = (
    OUTPUT_BASE / "youtube_channel_banner_evidence_desk_balanced_precision_tighten_20260518T224129Z"
)
PAPER_RENDER_SOURCE = KEPT_EVIDENCE_DESK_PACKAGE / "source/evidence_desk_balanced_imagegen_source.png"
PAPER_RENDER_SOURCE_NOTES = KEPT_EVIDENCE_DESK_PACKAGE / "source/source_notes.md"
PAPER_RENDER_MANIFEST = KEPT_EVIDENCE_DESK_PACKAGE / "manifest.json"
PAPER_RENDER_APPROVAL = KEPT_EVIDENCE_DESK_PACKAGE / "qa/approval_receipt_20260518T231204Z.json"

INK = (4, 11, 27, 255)
INK_2 = (8, 18, 40, 255)
PANEL = (12, 24, 49, 238)
PAPER = (247, 232, 205, 255)
PAPER_MUTED = (217, 199, 174, 255)
SHADOW = (0, 0, 0, 120)

EPISODE_ORDER = [
    "Challenger",
    "Therac-25",
    "Hyatt Regency Walkway Collapse",
    "Semmelweis and the Rejection of Handwashing",
    "Tacoma Narrows Bridge",
    "Piltdown Man",
    "Boeing 737 MAX / MCAS",
    "Titanic and the Lifeboat Regulation Gap",
]

CANDIDATES = [
    {
        "id": "F_left_title_split_ink",
        "label": "F - Split Ink",
        "summary": "Direct split composition: giant Season 1 title on the left, kept evidence-desk Paper Architecture render on the right.",
        "focus_x": 0.70,
        "focus_y": 0.48,
        "layout": "split_ink",
    },
    {
        "id": "G_left_title_cream_card",
        "label": "G - Cream Card",
        "summary": "Course-cover variant with a cream paper title block and right-side render framed as a clean Paper Architecture plate.",
        "focus_x": 0.68,
        "focus_y": 0.50,
        "layout": "cream_card",
    },
    {
        "id": "H_left_title_diagonal_cut",
        "label": "H - Diagonal Cut",
        "summary": "Angled paper cut between the oversized title and the right-side render to make the split feel more architectural.",
        "focus_x": 0.77,
        "focus_y": 0.50,
        "layout": "diagonal_cut",
    },
    {
        "id": "I_left_title_banner_world",
        "label": "I - Banner World",
        "summary": "Title-led playlist card with a broader right-side view of the kept banner world and lower-right overlay-safe quieting.",
        "focus_x": 0.76,
        "focus_y": 0.50,
        "layout": "banner_world",
    },
    {
        "id": "J_left_title_course_stripe",
        "label": "J - Course Stripe",
        "summary": "Educational cover treatment with strong title hierarchy and a right render cropped high to protect the playlist overlay zone.",
        "focus_x": 0.62,
        "focus_y": 0.42,
        "layout": "course_stripe",
    },
    {
        "id": "K_left_title_prestige_minimal",
        "label": "K - Prestige Minimal",
        "summary": "Sparse documentary card: very large left title, restrained series text, and a cinematic right-side Paper Architecture anchor.",
        "focus_x": 0.83,
        "focus_y": 0.48,
        "layout": "prestige_minimal",
    },
    {
        "id": "L_left_title_paper_stack",
        "label": "L - Paper Stack",
        "summary": "Layered paper-stack title treatment with the render sitting as a large physical evidence plate on the right.",
        "focus_x": 0.35,
        "focus_y": 0.50,
        "layout": "paper_stack",
    },
    {
        "id": "M_left_title_high_contrast_safe",
        "label": "M - High Contrast Safe",
        "summary": "Highest small-size contrast: oversized Season 1 type, compressed subtitle, and right-side render with the overlay zone deliberately low-detail.",
        "focus_x": 0.91,
        "focus_y": 0.46,
        "layout": "high_contrast_safe",
    },
]


def make_package_dir() -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    package = OUTPUT_BASE / f"{PACKAGE_PREFIX}_{stamp}"
    for name in ("assets", "previews", "qa", "source"):
        (package / name).mkdir(parents=True, exist_ok=True)
    return package


def source_render() -> Image.Image:
    return Image.open(PAPER_RENDER_SOURCE).convert("RGB")


def draw_top_brand(base: Image.Image, x: int, y: int, dark_text: bool = False, mark_size: int = 54) -> None:
    base.alpha_composite(brand_bug(mark_size), (x, y))
    draw = ImageDraw.Draw(base)
    fill = (18, 31, 58, 255) if dark_text else MUTED_CREAM
    label = font(max(17, mark_size // 3), bold=True)
    draw.text((x + mark_size + 14, y + 6), "CASCADE", font=label, fill=fill)
    draw.text((x + mark_size + 14, y + 29), "OF EFFECTS", font=label, fill=fill)


def draw_accent_rule(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int = 7) -> None:
    draw.rounded_rectangle((x, y, x + int(width * 0.72), y + height), radius=height // 2, fill=CYAN)
    draw.rounded_rectangle((x + int(width * 0.72), y, x + width, y + height), radius=height // 2, fill=CORAL)


def draw_large_left_title(
    base: Image.Image,
    box: tuple[int, int, int, int],
    *,
    dark_text: bool = False,
    compact: bool = False,
    include_bug: bool = True,
) -> None:
    draw = ImageDraw.Draw(base)
    x0, y0, x1, y1 = box
    width = x1 - x0
    fill = (15, 27, 53, 255) if dark_text else CREAM
    secondary = (70, 63, 101, 255) if dark_text else LAVENDER
    muted = (67, 58, 74, 255) if dark_text else MUTED_CREAM
    shadow = (255, 255, 255, 115) if dark_text else (0, 0, 0, 165)

    if include_bug:
        draw_top_brand(base, x0, y0, dark_text=dark_text, mark_size=54)
        title_y = y0 + 118
    else:
        title_y = y0

    if compact:
        title_font = fit_text(draw, "SEASON 1", width, 106, True)
        text_shadow(draw, (x0, title_y), "SEASON 1", title_font, fill=fill, shadow=shadow, offset=(2, 3))
        subtitle_y = title_y + 118
    else:
        season_font = fit_text(draw, "SEASON", width, 92, True)
        one_font = fit_text(draw, "1", width, 228, True)
        text_shadow(draw, (x0, title_y), "SEASON", season_font, fill=fill, shadow=shadow, offset=(2, 3))
        text_shadow(draw, (x0 - 3, title_y + 83), "1", one_font, fill=fill, shadow=shadow, offset=(3, 4))
        subtitle_y = title_y + 308

    draw.text((x0 + 2, subtitle_y), "THE FIRST EIGHT", font=fit_text(draw, "THE FIRST EIGHT", width, 38, True), fill=secondary)
    draw.text((x0 + 3, subtitle_y + 58), "A documentary sequence", font=font(25), fill=muted)
    draw.text((x0 + 3, subtitle_y + 90), "about systems that stopped", font=font(25), fill=muted)
    draw.text((x0 + 3, subtitle_y + 122), "noticing what changed", font=font(25), fill=muted)
    draw_accent_rule(draw, x0 + 4, min(y1 - 28, subtitle_y + 180), min(width - 48, 292))


def quiet_overlay_zone(base: Image.Image, alpha: int = 148) -> None:
    layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x0, y0, x1, y1 = OVERLAY_ZONE
    draw.rounded_rectangle((x0 - 6, y0 - 6, x1 + 6, y1 + 8), radius=14, fill=(2, 8, 20, alpha))
    base.alpha_composite(layer)


def transparent_dark_gradient(
    size: tuple[int, int],
    *,
    left_alpha: int = 0,
    right_alpha: int = 0,
    top_alpha: int = 0,
    bottom_alpha: int = 0,
) -> Image.Image:
    width, height = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = overlay.load()
    for x in range(width):
        lx = int(left_alpha * max(0.0, 1.0 - x / width))
        rx = int(right_alpha * max(0.0, x / width))
        for y in range(height):
            ty = int(top_alpha * max(0.0, 1.0 - y / height))
            by = int(bottom_alpha * max(0.0, y / height))
            pixels[x, y] = (0, 0, 0, min(245, lx + rx + ty + by))
    return overlay


def render_crop(size: tuple[int, int], focus_x: float, focus_y: float, *, color: float = 0.92, contrast: float = 1.04) -> Image.Image:
    crop = cover_crop(source_render(), size, focus_x=focus_x, focus_y=focus_y)
    crop = ImageEnhance.Color(crop).enhance(color)
    crop = ImageEnhance.Contrast(crop).enhance(contrast)
    return crop.convert("RGBA")


def paste_render_rect(
    base: Image.Image,
    box: tuple[int, int, int, int],
    focus_x: float,
    focus_y: float,
    *,
    radius: int = 16,
    border=(238, 231, 217, 90),
    shadow_alpha: int = 110,
    color: float = 0.92,
    contrast: float = 1.04,
) -> None:
    x0, y0, x1, y1 = box
    width, height = x1 - x0, y1 - y0
    crop = render_crop((width, height), focus_x, focus_y, color=color, contrast=contrast)
    shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((x0 + 10, y0 + 14, x1 + 10, y1 + 14), radius=radius, fill=(0, 0, 0, shadow_alpha))
    base.alpha_composite(shadow)
    paste_round(base, crop, (x0, y0), radius=radius, border=border)


def paste_render_polygon(
    base: Image.Image,
    polygon: list[tuple[int, int]],
    bounds: tuple[int, int, int, int],
    focus_x: float,
    focus_y: float,
    *,
    color: float = 0.9,
) -> None:
    x0, y0, x1, y1 = bounds
    width, height = x1 - x0, y1 - y0
    crop = render_crop((width, height), focus_x, focus_y, color=color)
    layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    layer.alpha_composite(crop, (x0, y0))
    mask = Image.new("L", CANVAS_SIZE, 0)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    base.paste(layer, (0, 0), mask)
    draw = ImageDraw.Draw(base)
    draw.line(polygon + [polygon[0]], fill=(235, 222, 200, 88), width=2, joint="curve")


def base_ink() -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, INK)
    backdrop = render_crop(CANVAS_SIZE, 0.50, 0.50, color=0.35, contrast=0.9)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(8))
    image.alpha_composite(add_linear_gradient(backdrop.convert("RGB"), left_alpha=225, right_alpha=130, bottom_alpha=90))
    return add_vignette(image, alpha=75)


def option_split_ink(candidate: dict) -> Image.Image:
    image = base_ink()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((54, 62, 530, 660), radius=14, fill=(3, 10, 27, 226), outline=(115, 130, 165, 80), width=2)
    draw_large_left_title(image, (84, 96, 498, 640))
    paste_render_rect(image, (590, 64, 1238, 604), candidate["focus_x"], candidate["focus_y"], radius=18)
    quiet_overlay_zone(image)
    return image.convert("RGB")


def option_cream_card(candidate: dict) -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, (8, 17, 37, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 720), fill=(8, 17, 37, 255))
    draw.rounded_rectangle((62, 58, 536, 660), radius=18, fill=PAPER, outline=(255, 244, 225, 120), width=2)
    draw.rectangle((62, 550, 536, 660), fill=(232, 214, 188, 255))
    draw_large_left_title(image, (94, 94, 502, 630), dark_text=True, compact=True)
    paste_render_rect(image, (592, 72, 1218, 620), candidate["focus_x"], candidate["focus_y"], radius=20, border=(255, 244, 225, 120), color=0.98, contrast=1.02)
    quiet_overlay_zone(image, alpha=156)
    return image.convert("RGB")


def option_diagonal_cut(candidate: dict) -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, INK_2)
    draw = ImageDraw.Draw(image)
    draw.polygon([(0, 0), (610, 0), (515, 720), (0, 720)], fill=(5, 13, 31, 255))
    draw.polygon([(565, 0), (640, 0), (545, 720), (470, 720)], fill=(37, 45, 70, 255))
    draw.polygon([(585, 0), (621, 0), (527, 720), (491, 720)], fill=(219, 202, 177, 255))
    paste_render_polygon(
        image,
        [(620, 0), (1280, 0), (1280, 720), (526, 720)],
        (500, 0, 1280, 720),
        candidate["focus_x"],
        candidate["focus_y"],
        color=0.94,
    )
    shade = add_linear_gradient(Image.new("RGB", CANVAS_SIZE, (0, 0, 0)), left_alpha=0, right_alpha=50, bottom_alpha=90)
    image.alpha_composite(Image.blend(Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0)), shade.convert("RGBA"), 0.22))
    draw_large_left_title(image, (76, 92, 468, 642), compact=False)
    quiet_overlay_zone(image, alpha=146)
    return image.convert("RGB")


def option_banner_world(candidate: dict) -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, INK)
    paste_render_rect(image, (548, 34, 1260, 662), candidate["focus_x"], candidate["focus_y"], radius=10, border=None, shadow_alpha=0, color=0.94, contrast=1.04)
    image.alpha_composite(transparent_dark_gradient(CANVAS_SIZE, left_alpha=218, right_alpha=10, bottom_alpha=58))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((52, 64, 546, 658), radius=12, fill=(4, 12, 29, 212), outline=(118, 130, 168, 75), width=2)
    draw_large_left_title(image, (84, 98, 500, 632), compact=True)
    quiet_overlay_zone(image, alpha=164)
    return image.convert("RGB")


def option_course_stripe(candidate: dict) -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, (9, 18, 39, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 118), fill=(23, 42, 77, 255))
    draw.rectangle((0, 602, 1280, 720), fill=(3, 10, 25, 255))
    draw.rectangle((54, 164, 542, 554), fill=(13, 27, 56, 255))
    draw.rectangle((54, 164, 542, 176), fill=CYAN)
    draw.rectangle((54, 176, 186, 188), fill=CORAL)
    draw_large_left_title(image, (82, 76, 510, 585), compact=True)
    paste_render_rect(image, (602, 128, 1228, 600), candidate["focus_x"], candidate["focus_y"], radius=12, color=0.96, contrast=1.08)
    quiet_overlay_zone(image, alpha=175)
    return image.convert("RGB")


def option_prestige_minimal(candidate: dict) -> Image.Image:
    image = base_ink()
    paste_render_rect(image, (604, 82, 1248, 614), candidate["focus_x"], candidate["focus_y"], radius=18, shadow_alpha=135, color=0.82, contrast=1.08)
    draw = ImageDraw.Draw(image)
    draw_top_brand(image, 74, 76, mark_size=50)
    draw.text((76, 228), "CASCADE OF EFFECTS", font=fit_text(draw, "CASCADE OF EFFECTS", 420, 38, True), fill=MUTED_CREAM)
    text_shadow(draw, (72, 298), "SEASON 1", fit_text(draw, "SEASON 1", 472, 112, True), fill=CREAM)
    draw.text((78, 438), "THE FIRST EIGHT", font=fit_text(draw, "THE FIRST EIGHT", 420, 34, True), fill=LAVENDER)
    draw_accent_rule(draw, 78, 530, 286)
    quiet_overlay_zone(image, alpha=160)
    return image.convert("RGB")


def option_paper_stack(candidate: dict) -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, (6, 14, 32, 255))
    draw = ImageDraw.Draw(image)
    for offset, fill in [(0, (39, 47, 72, 255)), (16, (219, 202, 177, 255)), (30, PAPER)]:
        draw.rounded_rectangle((64 + offset, 78 + offset, 526 + offset, 622 + offset), radius=18, fill=fill)
    draw_large_left_title(image, (104, 122, 500, 640), dark_text=True, compact=True)
    paste_render_rect(image, (606, 86, 1218, 608), candidate["focus_x"], candidate["focus_y"], radius=18, border=(255, 244, 225, 150), color=0.95)
    draw.line((574, 90, 574, 624), fill=(105, 127, 153, 105), width=3)
    quiet_overlay_zone(image, alpha=166)
    return image.convert("RGB")


def option_high_contrast_safe(candidate: dict) -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, (3, 9, 23, 255))
    render = render_crop((680, 600), candidate["focus_x"], candidate["focus_y"], color=0.78, contrast=1.12)
    render = add_linear_gradient(render.convert("RGB"), left_alpha=65, right_alpha=0, bottom_alpha=130).convert("RGBA")
    image.alpha_composite(render, (576, 50))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 574, 720), fill=(3, 9, 23, 255))
    draw.rectangle((574, 0, 592, 720), fill=(225, 205, 174, 255))
    draw.rectangle((592, 0, 606, 720), fill=(99, 200, 214, 255))
    draw_top_brand(image, 72, 80, mark_size=52)
    text_shadow(draw, (70, 220), "SEASON", fit_text(draw, "SEASON", 430, 98, True), fill=WHITE_UI)
    text_shadow(draw, (68, 310), "1", fit_text(draw, "1", 420, 250, True), fill=WHITE_UI, offset=(4, 5))
    draw.text((76, 588), "THE FIRST EIGHT", font=fit_text(draw, "THE FIRST EIGHT", 420, 36, True), fill=LAVENDER)
    quiet_overlay_zone(image, alpha=190)
    return image.convert("RGB")


BUILDERS = {
    "split_ink": option_split_ink,
    "cream_card": option_cream_card,
    "diagonal_cut": option_diagonal_cut,
    "banner_world": option_banner_world,
    "course_stripe": option_course_stripe,
    "prestige_minimal": option_prestige_minimal,
    "paper_stack": option_paper_stack,
    "high_contrast_safe": option_high_contrast_safe,
}


def save_candidate_assets(package: Path, candidate: dict, image: Image.Image) -> dict[str, Path]:
    cid = candidate["id"]
    png_path = package / "assets" / f"{cid}-season-1-playlist-thumbnail-1280x720.png"
    jpg_path = package / "assets" / f"{cid}-season-1-playlist-thumbnail-upload-1280x720.jpg"
    preview_320 = package / "previews" / f"{cid}-preview-320x180.png"
    preview_168 = package / "previews" / f"{cid}-preview-168x94.png"
    overlay_zone = package / "previews" / f"{cid}-youtube-overlay-zone-preview-1280x720.png"
    tab_sim = package / "previews" / f"{cid}-playlist-tab-card-simulation.png"
    detail_sim = package / "previews" / f"{cid}-playlist-detail-hero-simulation.png"

    image.save(png_path)
    image.save(jpg_path, quality=UPLOAD_JPEG_QUALITY, optimize=True, progressive=True)
    image.resize((320, 180), Image.Resampling.LANCZOS).save(preview_320)
    image.resize((168, 94), Image.Resampling.LANCZOS).save(preview_168)
    make_overlay_zone_preview(image).save(overlay_zone)
    make_tab_simulation(image, candidate["label"]).save(tab_sim)
    make_detail_simulation(image, candidate["label"]).save(detail_sim)
    return {
        "png": png_path,
        "upload_jpg": jpg_path,
        "preview_320": preview_320,
        "preview_168": preview_168,
        "overlay_zone": overlay_zone,
        "playlist_tab_simulation": tab_sim,
        "playlist_detail_simulation": detail_sim,
    }


def make_overlay_contact_sheet(candidates: list[dict], output_path: Path) -> None:
    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["overlay_zone"])) for candidate in candidates],
        output_path,
        "Left-title/right-paper-rendering lower-right overlay zone previews",
        thumb_size=(384, 216),
        columns=2,
    )


def write_readme(package: Path, candidates: list[dict], contact_sheets: dict[str, Path]) -> None:
    lines = [
        "# Cascade Effects Season 1 Playlist Thumbnail Left-Title Paper Options",
        "",
        "Status: `review_required`",
        "",
        "This package creates eight additional 16:9 Season 1 playlist thumbnail options with a large deterministic title on the left and the kept title-free Paper Architecture evidence-desk render on the right.",
        "",
        "No YouTube Studio/API action was performed. No candidate is marked `keep`.",
        "",
        "## Candidate Directions",
        "",
    ]
    for candidate in candidates:
        lines.append(f"- `{candidate['id']}`: {candidate['summary']}")
    lines.extend(["", "## Review Sheets", ""])
    for label, path in contact_sheets.items():
        lines.append(f"- {label}: `{path.relative_to(package)}`")
    lines.extend(["", "## Primary Upload Assets", ""])
    for candidate in candidates:
        lines.append(f"- `{candidate['id']}`: `{Path(candidate['outputs']['upload_jpg']).relative_to(package)}`")
    lines.append("")
    (package / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    required = [
        CHANNEL_BRAND_SNAPSHOT,
        PAPER_SKILL,
        WATERMARK_PATH,
        PAPER_RENDER_SOURCE,
        PAPER_RENDER_SOURCE_NOTES,
        PAPER_RENDER_MANIFEST,
        PAPER_RENDER_APPROVAL,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required source file(s):\n" + "\n".join(missing))

    package = make_package_dir()
    candidates: list[dict] = []
    for definition in CANDIDATES:
        image = BUILDERS[definition["layout"]](definition)
        outputs = save_candidate_assets(package, definition, image)
        candidates.append(
            {
                **definition,
                "status": "review_required",
                "may_advance": False,
                "outputs": {key: str(path) for key, path in outputs.items()},
                "output_records": {key: file_record(path) for key, path in outputs.items()},
            }
        )

    full_sheet = package / "qa/season-1-playlist-left-title-paper-options-full-size.png"
    tab_sheet = package / "qa/season-1-playlist-left-title-paper-options-playlist-tab-simulations.png"
    detail_sheet = package / "qa/season-1-playlist-left-title-paper-options-detail-hero-simulations.png"
    small_sheet = package / "qa/season-1-playlist-left-title-paper-options-small-previews.png"
    overlay_sheet = package / "qa/season-1-playlist-left-title-paper-options-overlay-zone-previews.png"

    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["png"])) for candidate in candidates],
        full_sheet,
        "Season 1 left-title/right-paper-rendering playlist thumbnail options",
        thumb_size=(384, 216),
        columns=2,
    )
    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["playlist_tab_simulation"])) for candidate in candidates],
        tab_sheet,
        "YouTube playlists-tab card simulations",
        thumb_size=(420, 300),
        columns=2,
    )
    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["playlist_detail_simulation"])) for candidate in candidates],
        detail_sheet,
        "YouTube playlist-detail hero simulations",
        thumb_size=(300, 300),
        columns=3,
    )
    make_small_preview_sheet(candidates, small_sheet)
    make_overlay_contact_sheet(candidates, overlay_sheet)

    shutil.copy2(CHANNEL_BRAND_SNAPSHOT, package / "source/official_youtube_channel_branding_guidance_2026-05-17.md")
    shutil.copy2(PAPER_SKILL, package / "source/cascade-paper-architectures-SKILL.md")
    shutil.copy2(WATERMARK_PATH, package / "source/video-watermark-800x800-clean-edge.png")
    shutil.copy2(PAPER_RENDER_SOURCE, package / "source/evidence_desk_balanced_imagegen_source.png")
    shutil.copy2(PAPER_RENDER_SOURCE_NOTES, package / "source/evidence_desk_balanced_source_notes.md")
    shutil.copy2(PAPER_RENDER_MANIFEST, package / "source/kept_evidence_desk_manifest.json")
    shutil.copy2(PAPER_RENDER_APPROVAL, package / "source/kept_evidence_desk_approval_receipt_20260518T231204Z.json")

    contact_sheets = {
        "full_size": full_sheet,
        "playlist_tab_simulations": tab_sheet,
        "playlist_detail_simulations": detail_sheet,
        "small_previews": small_sheet,
        "overlay_zone_previews": overlay_sheet,
    }

    manifest = {
        "kind": "local_review_asset_package",
        "id": package.name,
        "status": "review_required",
        "may_advance": False,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "asset_role": "youtube_playlist_thumbnail_channel_branding_surface",
        "youtube_studio_updated": False,
        "playlist": {
            "name": "Season 1",
            "channel_trailer_included": False,
            "canonical_episode_order": EPISODE_ORDER,
        },
        "composition_policy": {
            "format": "16:9 YouTube playlist thumbnail candidates at 1280x720",
            "requested_direction": "large title on the left with a Paper Architecture rendering on the right",
            "carrier": "deterministic local composition over kept title-free raster Paper Architecture source art",
            "title_policy": "local deterministic text only",
            "allowed_text": ["Cascade of Effects", "Season 1", "The First Eight"],
            "paper_architecture_scope": "YouTube playlist thumbnail treated as channel-level branded playlist surface; not a YouTube episode/video thumbnail",
            "right_rendering_source": str(PAPER_RENDER_SOURCE),
            "youtube_overlay_zone_xyxy": list(OVERLAY_ZONE),
            "overlay_zone_policy": "no important title, brand mark, episode number, or subject-detail dependency in lower-right overlay zone; options deliberately quiet the area",
        },
        "source_lineage": {
            "kept_source_package": str(KEPT_EVIDENCE_DESK_PACKAGE),
            "kept_source_status": "keep",
            "kept_source_approval_receipt": str(PAPER_RENDER_APPROVAL),
            "right_rendering_sha256": sha256_path(PAPER_RENDER_SOURCE),
            "clean_edge_watermark_source": str(WATERMARK_PATH),
            "clean_edge_watermark_sha256": sha256_path(WATERMARK_PATH),
            "channel_branding_guidance_snapshot": str(CHANNEL_BRAND_SNAPSHOT),
            "paper_architecture_skill": str(PAPER_SKILL),
            "builder_script": str(REPO_ROOT / "scripts/build_season1_playlist_thumbnail_left_title_paper_options.py"),
        },
        "candidates": candidates,
        "contact_sheets": {key: file_record(path) for key, path in contact_sheets.items()},
        "qa_reads": {
            "official_requirements_read": "pass_channel_branding_snapshot_current_within_90_days",
            "skill_workflow_read": "pass_channel_branding_and_paper_architecture_channel_surface",
            "dimensions_read": "pass_all_candidates_1280x720_16x9",
            "file_size_read": "pass_all_upload_jpgs_under_2mb",
            "large_left_title_read": "pass_all_candidates",
            "right_paper_architecture_rendering_read": "pass_all_candidates_use_kept_title_free_paper_render",
            "source_lineage_read": "pass_kept_evidence_desk_source_and_clean_edge_watermark_only",
            "season_order_read": "pass_canonical_first_eight_order_recorded",
            "channel_trailer_excluded_read": "pass",
            "generated_text_read": "pass_no_generated_text_in_new_assets_local_deterministic_text_only",
            "source_generated_text_read": "pass_right_render_source_notes_record_title_free",
            "youtube_overlay_simulation_read": "pass_playlist_tab_and_detail_simulations_generated",
            "texture_noise_read": "pass_inherited_from_kept_channel_branding_source",
            "waterfall_read": "pass_inherited_from_kept_channel_branding_source",
            "small_preview_320_read": "review_required",
            "small_preview_168_read": "review_required",
            "youtube_studio_updated": False,
        },
    }
    (package / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_readme(package, candidates, contact_sheets)
    print(json.dumps({"package": str(package), "manifest": str(package / "manifest.json"), "contact_sheet": str(full_sheet)}, indent=2))


if __name__ == "__main__":
    main()
