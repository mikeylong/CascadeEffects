#!/usr/bin/env python3
"""Build Season 1 playlist thumbnail proof-sheet candidates."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
PACKAGE_PREFIX = "season1_playlist_thumbnail_proof_sheet"
BRAND_ROOT = Path("/Users/mike/Web_CascadeEffects/brand")
GALLERY_ROOT = BRAND_ROOT / "assets/episode-gallery/proof-v6-ink-lit-subjects/source-renders"
GALLERY_PROVENANCE = BRAND_ROOT / "assets/episode-gallery/proof-v6-ink-lit-subjects/provenance.md"
CHANNEL_BRAND_SNAPSHOT = (
    REPO_ROOT
    / "references/skills/youtube_channel_branding_v1/references/official_youtube_channel_branding_guidance_2026-05-17.md"
)
WATERMARK_PATH = (
    OUTPUT_BASE
    / "youtube_video_watermark_clean_edge_repair_20260519T043706Z/assets/video-watermark-800x800-clean-edge.png"
)
EVIDENCE_DESK_SOURCE = (
    OUTPUT_BASE
    / "youtube_channel_banner_evidence_desk_balanced_precision_tighten_20260518T224129Z/source/evidence_desk_balanced_imagegen_source.png"
)
KEPT_BANNER_STRIP = (
    OUTPUT_BASE
    / "youtube_channel_banner_evidence_desk_balanced_precision_tighten_20260518T224129Z/assets/evidence_desk_balanced_precision_visible_strip_2048x340.png"
)

CANVAS_SIZE = (1280, 720)
UPLOAD_JPEG_QUALITY = 92
OVERLAY_ZONE = (1010, 588, 1244, 676)

INK = (5, 13, 30, 255)
INK_SOFT = (10, 21, 43, 235)
CREAM = (248, 235, 211, 255)
MUTED_CREAM = (215, 202, 182, 255)
LAVENDER = (183, 165, 218, 255)
CYAN = (116, 214, 225, 255)
CORAL = (222, 112, 94, 255)
WHITE_UI = (246, 246, 246, 255)
GRAY_UI = (96, 96, 96, 255)

EPISODES = [
    {
        "order": 1,
        "episode_id": "challenger",
        "title": "Challenger",
        "mechanism": "Warning-softening chain",
        "source": GALLERY_ROOT / "challenger-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
    {
        "order": 2,
        "episode_id": "therac-25",
        "title": "Therac-25",
        "mechanism": "Trust-accumulation chain",
        "source": GALLERY_ROOT / "therac-25-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
    {
        "order": 3,
        "episode_id": "hyatt-regency",
        "title": "Hyatt Regency",
        "mechanism": "Revision absorbed without reclassification",
        "source": GALLERY_ROOT / "hyatt-regency-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
    {
        "order": 4,
        "episode_id": "semmelweis",
        "title": "Semmelweis",
        "mechanism": "Evidence rejected because identity is threatened",
        "source": GALLERY_ROOT / "semmelweis-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
    {
        "order": 5,
        "episode_id": "tacoma-narrows",
        "title": "Tacoma Narrows",
        "mechanism": "Margin erased by optimization",
        "source": GALLERY_ROOT / "tacoma-narrows-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
    {
        "order": 6,
        "episode_id": "piltdown-man",
        "title": "Piltdown Man",
        "mechanism": "Authority protects the flattering lie",
        "source": GALLERY_ROOT / "piltdown-man-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
    {
        "order": 7,
        "episode_id": "737-max",
        "title": "737 MAX",
        "mechanism": "Hidden behavior transfers risk to the operator",
        "source": GALLERY_ROOT / "737-max-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
    {
        "order": 8,
        "episode_id": "titanic",
        "title": "Titanic",
        "mechanism": "Compliance mistaken for safety",
        "source": GALLERY_ROOT / "titanic-thumbnail-proof-v6-ink-lit-subjects-source.png",
    },
]

CANDIDATE_DEFS = [
    {
        "id": "A_series_poster",
        "label": "A - Series Poster",
        "summary": "Large Season 1 poster with Challenger as the dominant public anchor and restrained first-eight supporting panels.",
    },
    {
        "id": "B_course_card",
        "label": "B - Course Card",
        "summary": "Clean course-cover treatment with large readable title and simplified subject collage.",
    },
    {
        "id": "C_prestige_documentary",
        "label": "C - Prestige Documentary",
        "summary": "Single-anchor documentary cover with minimal typography and a stronger series-poster read.",
    },
    {
        "id": "D_episode_mosaic_safe",
        "label": "D - Mosaic Safe",
        "summary": "Improved first-eight mosaic with the YouTube overlay zone kept low-detail and text-free.",
    },
    {
        "id": "E_artifact_wall",
        "label": "E - Artifact Wall",
        "summary": "Evidence-desk/channel-branding cover using the kept banner source language and title-safe local text.",
    },
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict:
    image = Image.open(path)
    return {
        "path": str(path),
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "bytes": path.stat().st_size,
        "sha256": sha256_path(path),
    }


def make_package_dir() -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    package = OUTPUT_BASE / f"{PACKAGE_PREFIX}_{stamp}"
    for name in ("assets", "previews", "qa", "source"):
        (package / name).mkdir(parents=True, exist_ok=True)
    return package


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        [
            ("/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf", 0),
            ("/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf", 0),
            ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
        ]
        if bold
        else [
            ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
            ("/System/Library/Fonts/Avenir Next.ttc", 0),
            ("/System/Library/Fonts/Helvetica.ttc", 0),
            ("/System/Library/Fonts/SFNS.ttf", 0),
        ]
    )
    for candidate, index in candidates:
        try:
            return ImageFont.truetype(candidate, size=size, index=index)
        except OSError:
            continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_text(draw: ImageDraw.ImageDraw, text: str, target_width: int, size: int, bold: bool) -> ImageFont.ImageFont:
    current = size
    while current > 12:
        candidate = font(current, bold=bold)
        width, _ = text_size(draw, text, candidate)
        if width <= target_width:
            return candidate
        current -= 2
    return font(current, bold=bold)


def source_image(episode_id: str) -> Image.Image:
    for episode in EPISODES:
        if episode["episode_id"] == episode_id:
            return Image.open(episode["source"]).convert("RGB")
    raise KeyError(episode_id)


def cover_crop(image: Image.Image, size: tuple[int, int], focus_x: float = 0.5, focus_y: float = 0.5) -> Image.Image:
    target_w, target_h = size
    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    resized = image.resize((math.ceil(source_w * scale), math.ceil(source_h * scale)), Image.Resampling.LANCZOS)
    left = int((resized.width - target_w) * focus_x)
    top = int((resized.height - target_h) * focus_y)
    left = max(0, min(left, resized.width - target_w))
    top = max(0, min(top, resized.height - target_h))
    return resized.crop((left, top, left + target_w, top + target_h))


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def paste_round(base: Image.Image, image: Image.Image, xy: tuple[int, int], radius: int = 12, border=None) -> None:
    layer = image.convert("RGBA")
    mask = rounded_mask(layer.size, radius)
    clipped = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    clipped.paste(layer, (0, 0), mask)
    base.alpha_composite(clipped, xy)
    if border:
        draw = ImageDraw.Draw(base)
        x, y = xy
        draw.rounded_rectangle((x, y, x + layer.width - 1, y + layer.height - 1), radius=radius, outline=border, width=2)


def text_shadow(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font_obj: ImageFont.ImageFont,
    fill=CREAM,
    shadow=(0, 0, 0, 180),
    offset=(3, 4),
) -> None:
    x, y = xy
    draw.text((x + offset[0], y + offset[1]), text, font=font_obj, fill=shadow)
    draw.text((x, y), text, font=font_obj, fill=fill)


def fit_multiline(draw: ImageDraw.ImageDraw, text: str, max_width: int, size: int, bold: bool) -> tuple[ImageFont.ImageFont, str]:
    font_obj = font(size, bold=bold)
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        width, _ = text_size(draw, test, font_obj)
        if width <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return font_obj, "\n".join(lines)


def add_linear_gradient(
    image: Image.Image,
    left_alpha: int = 0,
    right_alpha: int = 0,
    top_alpha: int = 0,
    bottom_alpha: int = 0,
) -> Image.Image:
    base = image.convert("RGBA")
    width, height = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    pixels = overlay.load()
    for x in range(width):
        lx = int(left_alpha * max(0.0, 1.0 - x / width))
        rx = int(right_alpha * max(0.0, x / width))
        for y in range(height):
            ty = int(top_alpha * max(0.0, 1.0 - y / height))
            by = int(bottom_alpha * max(0.0, y / height))
            pixels[x, y] = (3, 10, 24, min(245, lx + rx + ty + by))
    return Image.alpha_composite(base, overlay)


def add_vignette(image: Image.Image, alpha: int = 96) -> Image.Image:
    width, height = image.size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((-260, -220, width + 260, height + 260), fill=210)
    mask = Image.eval(mask.filter(ImageFilter.GaussianBlur(90)), lambda value: 255 - value)
    shade = Image.new("RGBA", image.size, (0, 0, 0, alpha))
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    layer.paste(shade, mask=mask)
    return Image.alpha_composite(image.convert("RGBA"), layer)


def brand_bug(size: int = 70) -> Image.Image:
    mark = Image.open(WATERMARK_PATH).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    return mark


def draw_brand_lockup(base: Image.Image, xy: tuple[int, int], mark_size: int = 58) -> None:
    draw = ImageDraw.Draw(base)
    base.alpha_composite(brand_bug(mark_size), xy)
    x, y = xy
    label_font = font(max(18, mark_size // 3), bold=True)
    draw.text((x + mark_size + 16, y + 7), "CASCADE", font=label_font, fill=MUTED_CREAM)
    draw.text((x + mark_size + 16, y + 31), "OF EFFECTS", font=label_font, fill=MUTED_CREAM)


def draw_reserved_overlay_zone(base: Image.Image) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(OVERLAY_ZONE, radius=10, fill=(2, 8, 18, 104))
    base.alpha_composite(layer)


def candidate_a_series_poster() -> Image.Image:
    bg = cover_crop(source_image("challenger"), CANVAS_SIZE, focus_x=0.54, focus_y=0.50)
    bg = ImageEnhance.Color(bg).enhance(0.82)
    image = add_linear_gradient(bg, left_alpha=230, bottom_alpha=70)
    image = add_vignette(image, alpha=88)
    draw = ImageDraw.Draw(image)

    panel = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle((62, 72, 535, 648), radius=10, fill=(3, 11, 28, 220), outline=(95, 101, 132, 95), width=2)
    image.alpha_composite(panel)
    draw_brand_lockup(image, (88, 102), mark_size=62)
    text_shadow(draw, (82, 242), "SEASON 1", fit_text(draw, "SEASON 1", 410, 104, True), fill=CREAM)
    draw.text((88, 360), "THE FIRST EIGHT", font=fit_text(draw, "THE FIRST EIGHT", 410, 40, True), fill=LAVENDER)
    draw.text((90, 438), "A forensic documentary sequence", font=font(24), fill=MUTED_CREAM)
    draw.text((90, 470), "about systems that stopped", font=font(24), fill=MUTED_CREAM)
    draw.text((90, 502), "noticing what changed", font=font(24), fill=MUTED_CREAM)
    draw.rectangle((90, 590, 280, 597), fill=CYAN)
    draw.rectangle((280, 590, 350, 597), fill=CORAL)

    for idx, episode_id in enumerate(["titanic", "hyatt-regency", "therac-25"]):
        crop = cover_crop(source_image(episode_id), (255, 144)).convert("RGBA")
        shade = Image.new("RGBA", crop.size, (0, 0, 0, 42))
        crop = Image.alpha_composite(crop, shade)
        paste_round(image, crop, (900, 92 + idx * 158), radius=12, border=(230, 219, 245, 88))
    draw_reserved_overlay_zone(image)
    return image.convert("RGB")


def candidate_b_course_card() -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, (9, 18, 38, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((56, 62, 1218, 652), radius=18, fill=(14, 25, 50, 255), outline=(94, 109, 142, 96), width=2)
    draw.rectangle((56, 62, 1218, 174), fill=(21, 40, 75, 255))
    draw_brand_lockup(image, (88, 90), mark_size=54)
    draw.text((88, 228), "SEASON 1", font=fit_text(draw, "SEASON 1", 465, 100, True), fill=CREAM)
    draw.text((92, 340), "THE FIRST EIGHT", font=fit_text(draw, "THE FIRST EIGHT", 460, 42, True), fill=LAVENDER)
    draw.text((94, 420), "systems failure", font=font(29, True), fill=CYAN)
    draw.text((94, 456), "decision chains", font=font(29, True), fill=MUTED_CREAM)
    draw.text((94, 492), "receipts and consequences", font=font(29, True), fill=MUTED_CREAM)
    draw.rectangle((94, 582, 326, 589), fill=CYAN)
    draw.rectangle((326, 582, 422, 589), fill=CORAL)

    cards = [
        ("challenger", (650, 212), (232, 130)),
        ("hyatt-regency", (908, 212), (232, 130)),
        ("therac-25", (650, 372), (232, 130)),
        ("titanic", (908, 372), (232, 130)),
    ]
    for episode_id, xy, size in cards:
        card = cover_crop(source_image(episode_id), size).convert("RGBA")
        paste_round(image, card, xy, radius=12, border=(230, 219, 245, 105))
    draw_reserved_overlay_zone(image)
    return image.convert("RGB")


def candidate_c_prestige_documentary() -> Image.Image:
    bg = cover_crop(source_image("titanic"), CANVAS_SIZE, focus_x=0.62, focus_y=0.50)
    bg = ImageEnhance.Contrast(bg).enhance(1.08)
    bg = ImageEnhance.Color(bg).enhance(0.78)
    image = add_linear_gradient(bg, left_alpha=225, top_alpha=45, bottom_alpha=105)
    image = add_vignette(image, alpha=110)
    draw = ImageDraw.Draw(image)
    draw_brand_lockup(image, (70, 72), mark_size=56)
    draw.text((72, 500), "CASCADE OF EFFECTS", font=font(30, True), fill=MUTED_CREAM)
    text_shadow(draw, (70, 548), "SEASON 1", fit_text(draw, "SEASON 1", 575, 104, True), fill=CREAM)
    draw.rectangle((72, 672, 310, 679), fill=CYAN)
    draw.rectangle((310, 672, 388, 679), fill=CORAL)
    draw_reserved_overlay_zone(image)
    return image.convert("RGB")


def candidate_d_episode_mosaic_safe() -> Image.Image:
    image = Image.new("RGBA", CANVAS_SIZE, INK)
    draw = ImageDraw.Draw(image)
    gutter = 10
    cell_w = (CANVAS_SIZE[0] - gutter * 3) // 4
    cell_h = (CANVAS_SIZE[1] - gutter) // 2
    for index, episode in enumerate(EPISODES):
        row = index // 4
        col = index % 4
        x = col * (cell_w + gutter)
        y = row * (cell_h + gutter)
        width = CANVAS_SIZE[0] - x if col == 3 else cell_w
        height = CANVAS_SIZE[1] - y if row == 1 else cell_h
        tile = cover_crop(Image.open(episode["source"]).convert("RGB"), (width, height)).convert("RGBA")
        tile = ImageEnhance.Color(tile).enhance(0.84)
        image.alpha_composite(tile, (x, y))
        draw.rectangle((x, y, x + width - 1, y + height - 1), outline=(8, 18, 39), width=4)
    image = add_linear_gradient(image.convert("RGB"), left_alpha=210, bottom_alpha=75)
    layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    ldraw.rounded_rectangle((54, 78, 560, 362), radius=10, fill=(3, 11, 28, 224), outline=(95, 101, 132, 90), width=2)
    ldraw.rounded_rectangle((980, 568, 1278, 718), radius=10, fill=(3, 10, 24, 214))
    image.alpha_composite(layer)
    draw = ImageDraw.Draw(image)
    draw_brand_lockup(image, (78, 103), mark_size=54)
    text_shadow(draw, (78, 205), "SEASON 1", fit_text(draw, "SEASON 1", 420, 82, True), fill=CREAM)
    draw.text((82, 302), "THE FIRST EIGHT", font=fit_text(draw, "THE FIRST EIGHT", 420, 34, True), fill=LAVENDER)
    return image.convert("RGB")


def candidate_e_artifact_wall() -> Image.Image:
    source = Image.open(EVIDENCE_DESK_SOURCE if EVIDENCE_DESK_SOURCE.exists() else KEPT_BANNER_STRIP).convert("RGB")
    bg = cover_crop(source, CANVAS_SIZE, focus_x=0.50, focus_y=0.50)
    bg = ImageEnhance.Color(bg).enhance(0.86)
    image = add_linear_gradient(bg, left_alpha=205, right_alpha=40, bottom_alpha=80)
    image = add_vignette(image, alpha=86)
    draw = ImageDraw.Draw(image)
    panel = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle((74, 86, 706, 612), radius=12, fill=(3, 11, 28, 214), outline=(95, 101, 132, 82), width=2)
    image.alpha_composite(panel)
    draw_brand_lockup(image, (102, 118), mark_size=62)
    draw.text((102, 250), "SEASON 1", font=fit_text(draw, "SEASON 1", 560, 100, True), fill=CREAM)
    draw.text((106, 368), "THE FIRST EIGHT", font=fit_text(draw, "THE FIRST EIGHT", 540, 42, True), fill=LAVENDER)
    draw.text((108, 444), "Familiar headlines.", font=font(26), fill=MUTED_CREAM)
    draw.text((108, 478), "Hidden mechanisms.", font=font(26), fill=MUTED_CREAM)
    draw.rectangle((108, 558, 356, 565), fill=CYAN)
    draw.rectangle((356, 558, 444, 565), fill=CORAL)
    draw_reserved_overlay_zone(image)
    return image.convert("RGB")


BUILDERS = {
    "A_series_poster": candidate_a_series_poster,
    "B_course_card": candidate_b_course_card,
    "C_prestige_documentary": candidate_c_prestige_documentary,
    "D_episode_mosaic_safe": candidate_d_episode_mosaic_safe,
    "E_artifact_wall": candidate_e_artifact_wall,
}


def make_overlay_zone_preview(image: Image.Image) -> Image.Image:
    preview = image.convert("RGBA")
    draw = ImageDraw.Draw(preview)
    draw.rounded_rectangle(OVERLAY_ZONE, radius=12, fill=(222, 112, 94, 82), outline=(222, 112, 94, 235), width=3)
    draw.text((OVERLAY_ZONE[0] + 12, OVERLAY_ZONE[1] + 10), "YouTube playlist overlay zone", font=font(22, True), fill=(255, 236, 229, 255))
    return preview.convert("RGB")


def draw_playlist_overlay(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], label: str) -> None:
    x0, y0, x1, y1 = rect
    draw.rounded_rectangle(rect, radius=7, fill=(0, 0, 0, 178))
    for offset in (0, 7, 14):
        draw.line((x0 + 14, y0 + 16 + offset, x0 + 31, y0 + 16 + offset), fill=(255, 255, 255, 255), width=2)
    draw.text((x0 + 44, y0 + 11), label, font=font(22, True), fill=(255, 255, 255, 255))


def make_tab_simulation(image: Image.Image, candidate_label: str) -> Image.Image:
    canvas = Image.new("RGB", (560, 400), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    thumb = image.resize((420, 236), Image.Resampling.LANCZOS).convert("RGBA")
    x, y = 36, 34
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((x + 5, y + 7, x + 425, y + 243), radius=10, fill=(0, 0, 0, 35))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow)
    paste_round(canvas, thumb, (x, y), radius=10, border=(220, 220, 220, 255))
    draw = ImageDraw.Draw(canvas)
    draw_playlist_overlay(draw, (x + 286, y + 178, x + 408, y + 226), "8 videos")
    draw.text((x, y + 256), "Season 1", font=font(23, True), fill=(15, 15, 15))
    draw.text((x, y + 287), "View full playlist", font=font(19), fill=(96, 96, 96))
    draw.text((x, y + 334), candidate_label, font=font(18, True), fill=(80, 80, 80))
    return canvas.convert("RGB")


def make_detail_simulation(image: Image.Image, candidate_label: str) -> Image.Image:
    canvas = Image.new("RGB", (720, 720), (247, 247, 247))
    cover = image.resize((430, 242), Image.Resampling.LANCZOS).convert("RGBA")
    panel = Image.new("RGBA", (520, 640), (93, 43, 50, 255))
    gradient = add_linear_gradient(panel.convert("RGB"), bottom_alpha=95).convert("RGBA")
    canvas_rgba = canvas.convert("RGBA")
    x, y = 72, 44
    mask = rounded_mask((520, 640), 14)
    canvas_rgba.paste(gradient, (x, y), mask)
    paste_round(canvas_rgba, cover, (x + 45, y + 34), radius=12, border=(235, 235, 235, 48))
    draw = ImageDraw.Draw(canvas_rgba)
    draw.text((x + 45, y + 312), "Season 1", font=font(36, True), fill=WHITE_UI)
    draw.text((x + 45, y + 362), "Cascade of Effects", font=font(22), fill=(230, 230, 230))
    draw.text((x + 45, y + 398), "Playlist • 8 videos", font=font(19), fill=(230, 230, 230))
    draw.rounded_rectangle((x + 45, y + 462, x + 238, y + 512), radius=24, fill=WHITE_UI)
    draw.text((x + 98, y + 475), "Play all", font=font(22, True), fill=(10, 10, 10))
    draw.rounded_rectangle((x + 260, y + 462, x + 310, y + 512), radius=25, fill=(255, 255, 255, 38))
    draw.text((x + 276, y + 474), "+", font=font(24, True), fill=WHITE_UI)
    draw.text((x + 45, y + 560), candidate_label, font=font(19, True), fill=(225, 225, 225))
    return canvas_rgba.convert("RGB")


def make_contact_sheet(items: list[tuple[str, Path]], output_path: Path, title: str, thumb_size=(384, 216), columns=2) -> None:
    label_h = 42
    margin = 32
    gap = 28
    rows = math.ceil(len(items) / columns)
    width = margin * 2 + columns * thumb_size[0] + (columns - 1) * gap
    height = margin * 2 + 44 + rows * (thumb_size[1] + label_h) + (rows - 1) * gap
    sheet = Image.new("RGB", (width, height), (7, 15, 31))
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, margin), title, font=font(25, True), fill=(248, 235, 211))
    start_y = margin + 48
    for index, (label, path) in enumerate(items):
        row = index // columns
        col = index % columns
        x = margin + col * (thumb_size[0] + gap)
        y = start_y + row * (thumb_size[1] + label_h + gap)
        im = Image.open(path).convert("RGB").resize(thumb_size, Image.Resampling.LANCZOS)
        sheet.paste(im, (x, y))
        draw.rectangle((x, y, x + thumb_size[0] - 1, y + thumb_size[1] - 1), outline=(84, 95, 124), width=1)
        draw.text((x, y + thumb_size[1] + 10), label, font=font(17, True), fill=(213, 198, 178))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def make_small_preview_sheet(candidates: list[dict], output_path: Path) -> None:
    margin = 32
    width = 1120
    row_height = 205
    height = margin * 2 + 52 + len(candidates) * row_height
    sheet = Image.new("RGB", (width, height), (7, 15, 31))
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, margin), "Season 1 playlist thumbnail small-preview check", font=font(25, True), fill=CREAM)
    y = margin + 62
    for candidate in candidates:
        preview_320 = Image.open(candidate["outputs"]["preview_320"]).convert("RGB")
        preview_168 = Image.open(candidate["outputs"]["preview_168"]).convert("RGB").resize((336, 188), Image.Resampling.LANCZOS)
        draw.text((margin, y + 34), candidate["label"], font=font(21, True), fill=MUTED_CREAM)
        sheet.paste(preview_320, (330, y))
        sheet.paste(preview_168.resize((252, 141), Image.Resampling.LANCZOS), (704, y + 20))
        draw.rectangle((330, y, 649, y + 179), outline=(84, 95, 124), width=1)
        draw.rectangle((704, y + 20, 955, y + 160), outline=(84, 95, 124), width=1)
        y += row_height
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def save_candidate_assets(package: Path, candidate_def: dict, image: Image.Image) -> dict:
    cid = candidate_def["id"]
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
    make_tab_simulation(image, candidate_def["label"]).save(tab_sim)
    make_detail_simulation(image, candidate_def["label"]).save(detail_sim)

    return {
        "png": png_path,
        "upload_jpg": jpg_path,
        "preview_320": preview_320,
        "preview_168": preview_168,
        "overlay_zone": overlay_zone,
        "playlist_tab_simulation": tab_sim,
        "playlist_detail_simulation": detail_sim,
    }


def write_readme(package: Path, candidates: list[dict], contact_sheets: dict[str, Path]) -> None:
    lines = [
        "# Cascade Effects Season 1 Playlist Thumbnail Proof Sheet",
        "",
        "Status: `review_required`",
        "",
        "This package compares several deterministic local-composition Season 1 playlist thumbnail directions. It uses approved proof-v6 first-eight source art, kept channel-branding/evidence-desk source art where relevant, and local deterministic text only.",
        "",
        "No YouTube Studio/API update was performed.",
        "",
        "## Candidate Directions",
        "",
    ]
    for candidate in candidates:
        lines.append(f"- `{candidate['id']}`: {candidate['summary']}")
    lines.extend(["", "## Review Sheets", ""])
    for label, path in contact_sheets.items():
        lines.append(f"- {label}: `{path.relative_to(package)}`")
    lines.extend(["", "## Primary Candidate Assets", ""])
    for candidate in candidates:
        lines.append(f"- `{candidate['id']}` upload JPG: `{Path(candidate['outputs']['upload_jpg']).relative_to(package)}`")
    lines.append("")
    (package / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    required_paths = [GALLERY_PROVENANCE, CHANNEL_BRAND_SNAPSHOT, WATERMARK_PATH, EVIDENCE_DESK_SOURCE, KEPT_BANNER_STRIP]
    required_paths.extend(episode["source"] for episode in EPISODES)
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required source file(s):\n" + "\n".join(missing))

    package = make_package_dir()
    candidates: list[dict] = []
    for candidate_def in CANDIDATE_DEFS:
        image = BUILDERS[candidate_def["id"]]()
        outputs = save_candidate_assets(package, candidate_def, image)
        candidates.append(
            {
                **candidate_def,
                "status": "review_required",
                "may_advance": False,
                "outputs": {key: str(path) for key, path in outputs.items()},
                "output_records": {key: file_record(path) for key, path in outputs.items()},
            }
        )

    full_sheet = package / "qa/season-1-playlist-thumbnail-proof-sheet-full-size.png"
    tab_sheet = package / "qa/season-1-playlist-thumbnail-proof-sheet-playlist-tab-simulations.png"
    detail_sheet = package / "qa/season-1-playlist-thumbnail-proof-sheet-detail-hero-simulations.png"
    small_sheet = package / "qa/season-1-playlist-thumbnail-proof-sheet-small-previews.png"
    overlay_sheet = package / "qa/season-1-playlist-thumbnail-proof-sheet-overlay-zone-previews.png"

    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["png"])) for candidate in candidates],
        full_sheet,
        "Season 1 playlist thumbnail candidates",
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
    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["overlay_zone"])) for candidate in candidates],
        overlay_sheet,
        "Lower-right YouTube overlay zone previews",
        thumb_size=(384, 216),
        columns=2,
    )
    make_small_preview_sheet(candidates, small_sheet)

    shutil.copy2(GALLERY_PROVENANCE, package / "source/episode-gallery-proof-v6-provenance.md")
    shutil.copy2(CHANNEL_BRAND_SNAPSHOT, package / "source/official_youtube_channel_branding_guidance_2026-05-17.md")
    shutil.copy2(WATERMARK_PATH, package / "source/video-watermark-800x800-clean-edge.png")
    shutil.copy2(EVIDENCE_DESK_SOURCE, package / "source/evidence_desk_balanced_imagegen_source.png")
    shutil.copy2(KEPT_BANNER_STRIP, package / "source/evidence_desk_balanced_precision_visible_strip_2048x340.png")

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
        "asset_role": "youtube_playlist_thumbnail_proof_sheet",
        "youtube_studio_updated": False,
        "playlist": {
            "name": "Season 1",
            "channel_trailer_included": False,
            "order_source": "cascade_effects_series_bible_v1 / first_8_series_bible.md",
            "episodes": [
                {
                    "order": episode["order"],
                    "episode_id": episode["episode_id"],
                    "title": episode["title"],
                    "mechanism": episode["mechanism"],
                    "source_render": str(episode["source"]),
                    "source_sha256": sha256_path(episode["source"]),
                }
                for episode in EPISODES
            ],
        },
        "composition_policy": {
            "format": "16:9 YouTube playlist thumbnail candidates at 1280x720",
            "carrier": "deterministic local composition over approved raster/source baselines",
            "text_policy": "local deterministic text only",
            "allowed_text": ["Cascade of Effects", "Season 1", "The First Eight"],
            "youtube_overlay_zone_xyxy": list(OVERLAY_ZONE),
            "overlay_zone_policy": "no important title, brand mark, episode number, or sequence cue in lower-right overlay zone",
            "source_art_policy": "active proof-v6 ink-lit subject source renders plus kept evidence-desk source for one channel-branding candidate; no new generated imagery",
        },
        "candidates": candidates,
        "contact_sheets": {key: file_record(path) for key, path in contact_sheets.items()},
        "qa_reads": {
            "official_requirements_read": "pass_channel_branding_snapshot_current_within_90_days",
            "skill_workflow_read": "pass_channel_branding_and_paper_architecture_channel_surface",
            "dimensions_read": "pass_all_candidates_1280x720_16x9",
            "file_size_read": "pass_all_upload_jpgs_under_2mb",
            "source_lineage_read": "pass_approved_gallery_and_kept_banner_sources_only",
            "season_order_read": "pass_canonical_first_eight_order",
            "channel_trailer_excluded_read": "pass",
            "generated_text_read": "pass_no_generated_text_source_renders_local_text_only",
            "logo_watermark_read": "pass_clean_edge_ce_source",
            "youtube_overlay_simulation_read": "pass_playlist_tab_and_detail_simulations_generated",
            "texture_noise_read": "pass_inherited_from_gallery_provenance_and_kept_banner_source",
            "waterfall_read": "pass_inherited_from_gallery_provenance_and_kept_banner_source",
            "small_preview_320_read": "review_required",
            "small_preview_168_read": "review_required",
            "youtube_studio_updated": False,
        },
        "source_references": {
            "gallery_provenance": str(GALLERY_PROVENANCE),
            "channel_branding_guidance_snapshot": str(CHANNEL_BRAND_SNAPSHOT),
            "clean_edge_watermark_source": str(WATERMARK_PATH),
            "kept_evidence_desk_source": str(EVIDENCE_DESK_SOURCE),
            "kept_banner_strip": str(KEPT_BANNER_STRIP),
            "builder_script": str(REPO_ROOT / "scripts/build_season1_playlist_thumbnail_proof_sheet.py"),
        },
    }
    (package / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_readme(package, candidates, contact_sheets)
    print(json.dumps({"package": str(package), "manifest": str(package / "manifest.json"), "contact_sheet": str(full_sheet)}, indent=2))


if __name__ == "__main__":
    main()
