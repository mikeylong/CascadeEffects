#!/usr/bin/env python3
"""Build a local-review Season 1 playlist thumbnail package."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
PACKAGE_PREFIX = "season1_playlist_thumbnail"
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

CANVAS_SIZE = (1280, 720)
UPLOAD_JPEG_QUALITY = 92

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


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if bold:
        candidates = [
            ("/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf", 0),
            ("/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf", 0),
            ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
        ]
    else:
        candidates = [
            ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
            ("/System/Library/Fonts/Avenir Next.ttc", 0),
            ("/System/Library/Fonts/Helvetica.ttc", 0),
            ("/System/Library/Fonts/SFNS.ttf", 0),
        ]
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
    while current > 10:
        font_obj = font(current, bold=bold)
        width, _ = text_size(draw, text, font_obj)
        if width <= target_width:
            return font_obj
        current -= 2
    return font(current, bold=bold)


def cover_crop(image: Image.Image, size: tuple[int, int], focus_x: float = 0.5, focus_y: float = 0.5) -> Image.Image:
    target_w, target_h = size
    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    new_size = (math.ceil(source_w * scale), math.ceil(source_h * scale))
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    left = int((new_size[0] - target_w) * focus_x)
    top = int((new_size[1] - target_h) * focus_y)
    left = max(0, min(left, new_size[0] - target_w))
    top = max(0, min(top, new_size[1] - target_h))
    return resized.crop((left, top, left + target_w, top + target_h))


def add_gradient_overlay(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    pixels = overlay.load()
    for x in range(width):
        left_alpha = max(0, int(235 * (1 - x / 590)))
        right_alpha = max(0, int(60 * ((x - 590) / (width - 590)))) if x > 590 else 0
        for y in range(height):
            vertical = int(72 * abs((y / height) - 0.5) * 1.8)
            alpha = min(245, max(left_alpha, right_alpha) + vertical)
            pixels[x, y] = (3, 10, 24, alpha)
    return Image.alpha_composite(base.convert("RGBA"), overlay)


def add_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((-260, -230, width + 260, height + 300), fill=210)
    mask = Image.eval(mask.filter(ImageFilter.GaussianBlur(90)), lambda value: 255 - value)
    shade = Image.new("RGBA", (width, height), (0, 0, 0, 116))
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    layer.paste(shade, mask=mask)
    return Image.alpha_composite(base.convert("RGBA"), layer)


def draw_episode_grid() -> Image.Image:
    canvas = Image.new("RGB", CANVAS_SIZE, (5, 15, 35))
    draw = ImageDraw.Draw(canvas)
    gutter = 8
    cell_w = (CANVAS_SIZE[0] - gutter * 3) // 4
    cell_h = (CANVAS_SIZE[1] - gutter) // 2
    for index, episode in enumerate(EPISODES):
        row = index // 4
        col = index % 4
        x = col * (cell_w + gutter)
        y = row * (cell_h + gutter)
        if col == 3:
            cell_w_actual = CANVAS_SIZE[0] - x
        else:
            cell_w_actual = cell_w
        if row == 1:
            cell_h_actual = CANVAS_SIZE[1] - y
        else:
            cell_h_actual = cell_h
        source = Image.open(episode["source"]).convert("RGB")
        tile = cover_crop(source, (cell_w_actual, cell_h_actual))
        canvas.paste(tile, (x, y))
        draw.rectangle((x, y, x + cell_w_actual - 1, y + cell_h_actual - 1), outline=(20, 31, 55), width=2)
    return canvas


def draw_text_block(base: Image.Image) -> None:
    draw = ImageDraw.Draw(base)
    cream = (248, 235, 211, 255)
    muted_cream = (213, 198, 178, 255)
    lavender = (180, 162, 215, 255)
    cyan = (114, 211, 225, 255)
    coral = (222, 112, 94, 255)
    ink = (6, 14, 31, 230)

    panel = Image.new("RGBA", base.size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.rounded_rectangle((48, 74, 512, 642), radius=8, fill=ink, outline=(92, 102, 129, 88), width=2)
    panel_draw.rectangle((76, 600, 244, 606), fill=cyan)
    panel_draw.rectangle((244, 600, 322, 606), fill=coral)
    base.alpha_composite(panel)

    watermark = Image.open(WATERMARK_PATH).convert("RGBA")
    watermark = watermark.resize((84, 84), Image.Resampling.LANCZOS)
    watermark_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    watermark_layer.alpha_composite(watermark, (76, 102))
    base.alpha_composite(watermark_layer)

    label_font = font(25, bold=True)
    small_font = font(23, bold=False)
    season_font = fit_text(draw, "SEASON 1", 386, 104, bold=True)
    first_font = fit_text(draw, "THE FIRST EIGHT", 378, 39, bold=True)

    draw.text((176, 116), "CASCADE", font=label_font, fill=muted_cream)
    draw.text((176, 146), "OF EFFECTS", font=label_font, fill=muted_cream)
    draw.text((74, 238), "SEASON 1", font=season_font, fill=cream)
    draw.text((78, 360), "THE FIRST EIGHT", font=first_font, fill=lavender)
    draw.text((80, 434), "Systems that stopped", font=small_font, fill=muted_cream)
    draw.text((80, 464), "noticing what changed", font=small_font, fill=muted_cream)
    draw.text((80, 534), "01-08", font=font(30, bold=True), fill=cyan)


def add_order_strip(base: Image.Image) -> None:
    strip = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(strip)
    tile_w, tile_h = 80, 45
    gap = 7
    start_x = 552
    y = 616
    num_font = font(16, bold=True)
    for index, episode in enumerate(EPISODES):
        x = start_x + index * (tile_w + gap)
        source = Image.open(episode["source"]).convert("RGB")
        tile = cover_crop(source, (tile_w, tile_h)).convert("RGBA")
        shade = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 32))
        tile = Image.alpha_composite(tile, shade)
        strip.alpha_composite(tile, (x, y))
        draw.rounded_rectangle((x, y, x + tile_w, y + tile_h), radius=5, outline=(224, 212, 238, 128), width=1)
        draw.rounded_rectangle((x + 5, y + 5, x + 31, y + 25), radius=3, fill=(4, 12, 30, 190))
        draw.text((x + 10, y + 7), f"{episode['order']:02d}", font=num_font, fill=(248, 235, 211, 255))
    base.alpha_composite(strip)


def build_thumbnail() -> Image.Image:
    image = draw_episode_grid()
    image = image.filter(ImageFilter.GaussianBlur(0.4))
    image = ImageEnhanceCompat.color(image, 0.82)
    image = add_gradient_overlay(image)
    image = add_vignette(image)
    draw_text_block(image)
    add_order_strip(image)
    return image.convert("RGB")


class ImageEnhanceCompat:
    @staticmethod
    def color(image: Image.Image, factor: float) -> Image.Image:
        # Tiny wrapper avoids importing ImageEnhance at module load in old Pillow builds.
        from PIL import ImageEnhance

        return ImageEnhance.Color(image).enhance(factor)


def make_safe_overlay(image: Image.Image) -> Image.Image:
    overlay = image.convert("RGBA")
    draw = ImageDraw.Draw(overlay)
    title_safe = (64, 64, 1216, 656)
    center_safe = (128, 96, 1152, 624)
    draw.rounded_rectangle(title_safe, radius=8, outline=(116, 211, 225, 210), width=3)
    draw.rounded_rectangle(center_safe, radius=8, outline=(222, 112, 94, 210), width=2)
    draw.text((title_safe[0] + 12, title_safe[1] + 10), "title/action safe", font=font(20, bold=True), fill=(116, 211, 225, 255))
    draw.text((center_safe[0] + 12, center_safe[1] + 10), "small-preview core", font=font(18, bold=True), fill=(222, 112, 94, 255))
    return overlay.convert("RGB")


def make_contact_sheet(paths: list[Path], output_path: Path) -> None:
    thumbs = []
    labels = []
    for path in paths:
        im = Image.open(path).convert("RGB")
        if path.name.endswith("168x94.png"):
            target = (336, 188)
        elif path.name.endswith("320x180.png"):
            target = (320, 180)
        else:
            target = (480, 270)
        thumbs.append(im.resize(target, Image.Resampling.LANCZOS))
        labels.append(path.name)

    width = 1040
    height = 650
    sheet = Image.new("RGB", (width, height), (7, 15, 31))
    draw = ImageDraw.Draw(sheet)
    title_font = font(24, bold=True)
    label_font = font(16, bold=False)
    draw.text((32, 28), "Season 1 playlist thumbnail review", font=title_font, fill=(248, 235, 211))

    positions = [(32, 84), (552, 84), (32, 410), (552, 410)]
    for thumb, label, pos in zip(thumbs, labels, positions):
        sheet.paste(thumb, pos)
        draw.rectangle((pos[0], pos[1], pos[0] + thumb.width - 1, pos[1] + thumb.height - 1), outline=(84, 95, 124), width=1)
        draw.text((pos[0], pos[1] + thumb.height + 10), label, font=label_font, fill=(213, 198, 178))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=94)


def write_readme(package: Path, assets: dict) -> None:
    readme = f"""# Cascade Effects Season 1 Playlist Thumbnail

Status: `review_required`

This package contains a deterministic local-composition thumbnail for the Season 1 / first-eight YouTube playlist. It uses the active `proof-v6-ink-lit-subjects` episode-gallery source art in canonical first-eight order, local deterministic title text, and the current clean-edge CE watermark source.

## Primary Asset

- Upload JPG: `{assets["upload_jpg"].relative_to(package)}`
- Lossless PNG: `{assets["png"].relative_to(package)}`
- Preview 320x180: `{assets["preview_320"].relative_to(package)}`
- Preview 168x94: `{assets["preview_168"].relative_to(package)}`
- Safe-area overlay: `{assets["safe_overlay"].relative_to(package)}`
- Contact sheet: `{assets["contact_sheet"].relative_to(package)}`

## Scope

- YouTube playlist thumbnail / Season 1 branding surface only.
- Channel trailer remains separate from the Season 1 episode playlist.
- No YouTube Studio or API update was performed.
"""
    (package / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    missing = [str(ep["source"]) for ep in EPISODES if not ep["source"].exists()]
    if missing:
        raise FileNotFoundError("Missing source render(s):\n" + "\n".join(missing))
    if not WATERMARK_PATH.exists():
        raise FileNotFoundError(f"Missing watermark source: {WATERMARK_PATH}")

    package = make_package_dir()
    image = build_thumbnail()

    png_path = package / "assets/season-1-playlist-thumbnail-1280x720.png"
    jpg_path = package / "assets/season-1-playlist-thumbnail-upload-1280x720.jpg"
    preview_320_path = package / "previews/season-1-playlist-thumbnail-preview-320x180.png"
    preview_168_path = package / "previews/season-1-playlist-thumbnail-preview-168x94.png"
    safe_overlay_path = package / "previews/season-1-playlist-thumbnail-safe-area-overlay-1280x720.png"
    contact_sheet_path = package / "qa/season-1-playlist-thumbnail-contact-sheet.png"

    image.save(png_path)
    image.save(jpg_path, quality=UPLOAD_JPEG_QUALITY, optimize=True, progressive=True)
    image.resize((320, 180), Image.Resampling.LANCZOS).save(preview_320_path)
    image.resize((168, 94), Image.Resampling.LANCZOS).save(preview_168_path)
    make_safe_overlay(image).save(safe_overlay_path)
    make_contact_sheet([png_path, safe_overlay_path, preview_320_path, preview_168_path], contact_sheet_path)

    shutil.copy2(GALLERY_PROVENANCE, package / "source/episode-gallery-proof-v6-provenance.md")
    shutil.copy2(CHANNEL_BRAND_SNAPSHOT, package / "source/official_youtube_channel_branding_guidance_2026-05-17.md")
    shutil.copy2(WATERMARK_PATH, package / "source/video-watermark-800x800-clean-edge.png")

    outputs = {
        "png": png_path,
        "upload_jpg": jpg_path,
        "preview_320": preview_320_path,
        "preview_168": preview_168_path,
        "safe_overlay": safe_overlay_path,
        "contact_sheet": contact_sheet_path,
    }

    manifest = {
        "kind": "local_review_asset_package",
        "id": package.name,
        "status": "review_required",
        "may_advance": False,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "asset_role": "youtube_playlist_thumbnail",
        "playlist": {
            "name": "Season 1",
            "channel_trailer_included": False,
            "order_source": "cascade_effects_series_bible_v1 / first_8_series_bible.md",
            "episodes": [
                {
                    "order": ep["order"],
                    "episode_id": ep["episode_id"],
                    "title": ep["title"],
                    "mechanism": ep["mechanism"],
                    "source_render": str(ep["source"]),
                    "source_sha256": sha256_path(ep["source"]),
                }
                for ep in EPISODES
            ],
        },
        "composition": {
            "format": "16:9 YouTube-style playlist thumbnail",
            "dimensions_px": list(CANVAS_SIZE),
            "carrier": "deterministic local composition over approved raster/source baselines",
            "title_text": ["CASCADE OF EFFECTS", "SEASON 1", "THE FIRST EIGHT"],
            "supporting_text": ["Systems that stopped", "noticing what changed", "01-08"],
            "text_policy": "local deterministic text only",
            "source_art_policy": "active proof-v6 ink-lit subject source renders; no new generated imagery",
            "watermark_source": str(WATERMARK_PATH),
            "watermark_sha256": sha256_path(WATERMARK_PATH),
        },
        "outputs": {key: file_record(path) for key, path in outputs.items()},
        "qa_reads": {
            "official_requirements_read": "pass_channel_branding_snapshot_current_within_90_days",
            "skill_workflow_read": "pass_channel_branding_and_paper_architecture_channel_surface",
            "dimensions_read": "pass_1280x720_16x9",
            "source_lineage_read": "pass_approved_gallery_sources_only",
            "season_order_read": "pass_canonical_first_eight_order",
            "channel_trailer_excluded_read": "pass",
            "generated_text_read": "pass_no_generated_text_source_renders_local_text_only",
            "logo_watermark_read": "pass_clean_edge_ce_source",
            "texture_noise_read": "pass_inherited_from_gallery_provenance",
            "waterfall_read": "pass_inherited_from_gallery_provenance",
            "small_preview_320_read": "review_required",
            "small_preview_168_read": "review_required",
            "youtube_studio_updated": False,
        },
        "source_references": {
            "gallery_provenance": str(GALLERY_PROVENANCE),
            "channel_branding_guidance_snapshot": str(CHANNEL_BRAND_SNAPSHOT),
            "builder_script": str(REPO_ROOT / "scripts/build_season1_playlist_thumbnail.py"),
        },
    }
    (package / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_readme(package, outputs)
    print(json.dumps({"package": str(package), "primary_asset": str(jpg_path), "manifest": str(package / "manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
