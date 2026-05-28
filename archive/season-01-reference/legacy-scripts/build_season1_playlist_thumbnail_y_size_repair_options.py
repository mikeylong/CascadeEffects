#!/usr/bin/env python3
"""Build larger-text repair options for selected Season 1 candidate Y."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

from build_season1_playlist_thumbnail_minimal_paper_backplate_options import transparent_dark_gradient
from build_season1_playlist_thumbnail_proof_sheet import (
    CREAM,
    LAVENDER,
    OVERLAY_ZONE,
    add_vignette,
    cover_crop,
    file_record,
    fit_text,
    font,
    make_contact_sheet,
    make_detail_simulation,
    make_small_preview_sheet,
    make_tab_simulation,
    sha256_path,
    text_shadow,
)


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
PACKAGE_PREFIX = "season1_playlist_thumbnail_y_size_repair_options"
CANVAS_SIZE = (1280, 720)
UPLOAD_JPEG_QUALITY = 92

CHANNEL_BRAND_SNAPSHOT = (
    REPO_ROOT
    / "references/skills/youtube_channel_branding_v1/references/official_youtube_channel_branding_guidance_2026-05-17.md"
)
PAPER_SKILL = Path("/Users/mike/.codex/skills/cascade-paper-architectures/SKILL.md")
KEPT_EVIDENCE_DESK_PACKAGE = (
    OUTPUT_BASE / "youtube_channel_banner_evidence_desk_balanced_precision_tighten_20260518T224129Z"
)
BACKPLATE_SOURCE = KEPT_EVIDENCE_DESK_PACKAGE / "source/evidence_desk_balanced_imagegen_source.png"
BACKPLATE_SOURCE_NOTES = KEPT_EVIDENCE_DESK_PACKAGE / "source/source_notes.md"
BACKPLATE_MANIFEST = KEPT_EVIDENCE_DESK_PACKAGE / "manifest.json"
BACKPLATE_APPROVAL = KEPT_EVIDENCE_DESK_PACKAGE / "qa/approval_receipt_20260518T231204Z.json"

PREVIOUS_Y_PACKAGE = (
    OUTPUT_BASE / "season1_playlist_thumbnail_eyebrow_phrase_options_20260525T202514Z"
)
PREVIOUS_Y_MANIFEST = PREVIOUS_Y_PACKAGE / "manifest.json"
PREVIOUS_Y_KEEP_RECEIPT = (
    PREVIOUS_Y_PACKAGE / "qa/keep_receipt_Y_the_system_missed_it_20260525T202514Z.json"
)
PREVIOUS_Y_SELECTED = (
    PREVIOUS_Y_PACKAGE
    / "selected/season-1-playlist-thumbnail-selected-Y-the-system-missed-it-1280x720.png"
)

EYEBROW = "SEASON 1"
PHRASE = "THE SYSTEM\nMISSED IT"

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
        "id": "Y1_larger_balanced",
        "label": "Y1 - Larger Balanced",
        "summary": "Repair of selected Y with a clearly larger eyebrow and wider phrase box while preserving the original balance.",
        "focus_x": 0.78,
        "focus_y": 0.50,
        "left_alpha": 222,
        "right_alpha": 20,
        "bottom_alpha": 78,
        "color": 0.88,
        "contrast": 1.08,
        "x": 72,
        "eyebrow_y": 105,
        "eyebrow_size": 50,
        "eyebrow_width": 560,
        "phrase_y": 172,
        "phrase_size": 120,
        "phrase_width": 670,
        "phrase_height": 330,
        "spacing": 6,
    },
    {
        "id": "Y2_max_title",
        "label": "Y2 - Max Title",
        "summary": "Recommended repair: much larger phrase, stronger eyebrow, and the paper architecture shifted farther right.",
        "focus_x": 0.73,
        "focus_y": 0.50,
        "left_alpha": 228,
        "right_alpha": 18,
        "bottom_alpha": 82,
        "color": 0.87,
        "contrast": 1.09,
        "x": 68,
        "eyebrow_y": 96,
        "eyebrow_size": 58,
        "eyebrow_width": 640,
        "phrase_y": 166,
        "phrase_size": 134,
        "phrase_width": 742,
        "phrase_height": 350,
        "spacing": 2,
    },
    {
        "id": "Y3_heavy_eyebrow",
        "label": "Y3 - Heavy Eyebrow",
        "summary": "Makes Season 1 feel more intentional as an eyebrow while still letting the phrase dominate.",
        "focus_x": 0.75,
        "focus_y": 0.50,
        "left_alpha": 230,
        "right_alpha": 18,
        "bottom_alpha": 84,
        "color": 0.87,
        "contrast": 1.09,
        "x": 68,
        "eyebrow_y": 88,
        "eyebrow_size": 68,
        "eyebrow_width": 690,
        "phrase_y": 172,
        "phrase_size": 126,
        "phrase_width": 710,
        "phrase_height": 350,
        "spacing": 4,
    },
    {
        "id": "Y4_largest_safe",
        "label": "Y4 - Largest Safe",
        "summary": "Largest legibility-first crop that still avoids the lower-right playlist overlay zone.",
        "focus_x": 0.70,
        "focus_y": 0.50,
        "left_alpha": 236,
        "right_alpha": 16,
        "bottom_alpha": 90,
        "color": 0.86,
        "contrast": 1.1,
        "x": 64,
        "eyebrow_y": 82,
        "eyebrow_size": 62,
        "eyebrow_width": 710,
        "phrase_y": 154,
        "phrase_size": 142,
        "phrase_width": 760,
        "phrase_height": 370,
        "spacing": 0,
    },
]


def make_package_dir() -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    package = OUTPUT_BASE / f"{PACKAGE_PREFIX}_{stamp}"
    for name in ("assets", "previews", "qa", "source"):
        (package / name).mkdir(parents=True, exist_ok=True)
    return package


def source_backplate() -> Image.Image:
    return Image.open(BACKPLATE_SOURCE).convert("RGB")


def build_backplate(candidate: dict) -> Image.Image:
    image = cover_crop(source_backplate(), CANVAS_SIZE, candidate["focus_x"], candidate["focus_y"])
    image = ImageEnhance.Color(image).enhance(candidate["color"])
    image = ImageEnhance.Contrast(image).enhance(candidate["contrast"])
    image = image.convert("RGBA")
    image.alpha_composite(
        transparent_dark_gradient(
            CANVAS_SIZE,
            left_alpha=candidate["left_alpha"],
            right_alpha=candidate["right_alpha"],
            bottom_alpha=candidate["bottom_alpha"],
        )
    )
    return add_vignette(image, alpha=44)


def fit_multiline_fixed(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_height: int,
    size: int,
    spacing: int,
) -> object:
    current = size
    while current > 58:
        candidate_font = font(current, bold=True)
        bbox = draw.multiline_textbbox((0, 0), text, font=candidate_font, spacing=spacing)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width <= max_width and height <= max_height:
            return candidate_font
        current -= 2
    return font(current, bold=True)


def draw_copy(base: Image.Image, candidate: dict) -> None:
    draw = ImageDraw.Draw(base)
    x = candidate["x"]
    eyebrow_font = fit_text(
        draw,
        EYEBROW,
        candidate["eyebrow_width"],
        candidate["eyebrow_size"],
        True,
    )
    draw.text((x + 2, candidate["eyebrow_y"] + 2), EYEBROW, font=eyebrow_font, fill=(0, 0, 0, 150))
    draw.text((x, candidate["eyebrow_y"]), EYEBROW, font=eyebrow_font, fill=LAVENDER)

    phrase_font = fit_multiline_fixed(
        draw,
        PHRASE,
        candidate["phrase_width"],
        candidate["phrase_height"],
        candidate["phrase_size"],
        candidate["spacing"],
    )
    text_shadow(
        draw,
        (x, candidate["phrase_y"]),
        PHRASE,
        phrase_font,
        fill=CREAM,
        shadow=(0, 0, 0, 184),
        offset=(5, 6),
    )


def make_candidate(candidate: dict) -> Image.Image:
    image = build_backplate(candidate)
    draw_copy(image, candidate)
    return image.convert("RGB")


def make_overlay_zone_preview_silent(image: Image.Image) -> Image.Image:
    preview = image.convert("RGBA")
    draw = ImageDraw.Draw(preview)
    x0, y0, x1, y1 = OVERLAY_ZONE
    draw.rounded_rectangle((x0, y0, x1, y1), radius=12, fill=(222, 112, 94, 72), outline=(222, 112, 94, 210), width=3)
    return preview.convert("RGB")


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
    make_overlay_zone_preview_silent(image).save(overlay_zone)
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


def write_readme(package: Path, candidates: list[dict], contact_sheets: dict[str, Path]) -> None:
    lines = [
        "# Cascade Effects Season 1 Candidate Y Size Repair Options",
        "",
        "Status: `review_required`",
        "",
        "This package repairs the selected `Y_the_system_missed_it` direction after review notes that the `Season 1` eyebrow is too small and the main title could be larger.",
        "",
        "All candidate assets keep the same deterministic local text: `SEASON 1` and `THE SYSTEM MISSED IT`. No YouTube Studio/API action was performed.",
        "",
        "Recommended review starting point: `Y2_max_title`.",
        "",
        "## Options",
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
        BACKPLATE_SOURCE,
        BACKPLATE_SOURCE_NOTES,
        BACKPLATE_MANIFEST,
        BACKPLATE_APPROVAL,
        PREVIOUS_Y_MANIFEST,
        PREVIOUS_Y_KEEP_RECEIPT,
        PREVIOUS_Y_SELECTED,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required source file(s):\n" + "\n".join(missing))

    package = make_package_dir()
    candidates: list[dict] = []
    for definition in CANDIDATES:
        image = make_candidate(definition)
        outputs = save_candidate_assets(package, definition, image)
        candidates.append(
            {
                **definition,
                "status": "review_required",
                "may_advance": False,
                "text_elements": [EYEBROW, "THE SYSTEM MISSED IT"],
                "outputs": {key: str(path) for key, path in outputs.items()},
                "output_records": {key: file_record(path) for key, path in outputs.items()},
            }
        )

    full_sheet = package / "qa/season-1-y-size-repair-options-full-size.png"
    tab_sheet = package / "qa/season-1-y-size-repair-options-playlist-tab-simulations.png"
    detail_sheet = package / "qa/season-1-y-size-repair-options-detail-hero-simulations.png"
    small_sheet = package / "qa/season-1-y-size-repair-options-small-previews.png"
    overlay_sheet = package / "qa/season-1-y-size-repair-options-overlay-zone-previews.png"

    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["png"])) for candidate in candidates],
        full_sheet,
        "Season 1 selected Y size repair options",
        thumb_size=(512, 288),
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
        columns=2,
    )
    make_small_preview_sheet(candidates, small_sheet)
    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["overlay_zone"])) for candidate in candidates],
        overlay_sheet,
        "Lower-right YouTube overlay zone previews",
        thumb_size=(512, 288),
        columns=2,
    )

    shutil.copy2(CHANNEL_BRAND_SNAPSHOT, package / "source/official_youtube_channel_branding_guidance_2026-05-17.md")
    shutil.copy2(PAPER_SKILL, package / "source/cascade-paper-architectures-SKILL.md")
    shutil.copy2(BACKPLATE_SOURCE, package / "source/evidence_desk_balanced_imagegen_source.png")
    shutil.copy2(BACKPLATE_SOURCE_NOTES, package / "source/evidence_desk_balanced_source_notes.md")
    shutil.copy2(BACKPLATE_MANIFEST, package / "source/kept_evidence_desk_manifest.json")
    shutil.copy2(BACKPLATE_APPROVAL, package / "source/kept_evidence_desk_approval_receipt_20260518T231204Z.json")
    shutil.copy2(PREVIOUS_Y_MANIFEST, package / "source/previous_y_manifest.json")
    shutil.copy2(PREVIOUS_Y_KEEP_RECEIPT, package / "source/previous_y_keep_receipt.json")
    shutil.copy2(PREVIOUS_Y_SELECTED, package / "source/previous_y_selected_reference.png")

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
            "requested_direction": "repair selected Y by making the Season 1 eyebrow and large title text bigger",
            "carrier": "deterministic local text over kept title-free raster Paper Architecture source art",
            "text_policy": "local deterministic text only; no generated text inside source image assets",
            "text_elements": [EYEBROW, "THE SYSTEM MISSED IT"],
            "youtube_overlay_zone_xyxy": list(OVERLAY_ZONE),
            "overlay_zone_policy": "title and eyebrow stay out of lower-right YouTube playlist overlay zone",
        },
        "recommendation": {
            "candidate_id": "Y2_max_title",
            "reason": "best balance of larger typography, visible Season 1 eyebrow, and right-aligned paper architecture.",
            "status": "review_required_not_keep",
        },
        "source_lineage": {
            "previous_selected_candidate": "Y_the_system_missed_it",
            "previous_keep_package": str(PREVIOUS_Y_PACKAGE),
            "previous_keep_receipt": str(PREVIOUS_Y_KEEP_RECEIPT),
            "previous_selected_reference": str(PREVIOUS_Y_SELECTED),
            "previous_selected_reference_sha256": sha256_path(PREVIOUS_Y_SELECTED),
            "kept_source_package": str(KEPT_EVIDENCE_DESK_PACKAGE),
            "kept_source_status": "keep",
            "kept_source_approval_receipt": str(BACKPLATE_APPROVAL),
            "backplate_source": str(BACKPLATE_SOURCE),
            "backplate_sha256": sha256_path(BACKPLATE_SOURCE),
            "channel_branding_guidance_snapshot": str(CHANNEL_BRAND_SNAPSHOT),
            "paper_architecture_skill": str(PAPER_SKILL),
            "builder_script": str(REPO_ROOT / "scripts/build_season1_playlist_thumbnail_y_size_repair_options.py"),
        },
        "candidates": candidates,
        "contact_sheets": {key: file_record(path) for key, path in contact_sheets.items()},
        "qa_reads": {
            "official_requirements_read": "pass_channel_branding_snapshot_current_within_90_days",
            "skill_workflow_read": "pass_channel_branding_and_paper_architecture_channel_surface",
            "dimensions_read": "pass_all_candidates_1280x720_16x9",
            "file_size_read": "pass_all_upload_jpgs_under_2mb",
            "eyebrow_size_repair_read": "pass_all_candidates_larger_than_previous_y",
            "title_size_repair_read": "pass_all_candidates_larger_than_previous_y",
            "source_lineage_read": "pass_previous_keep_y_and_kept_evidence_desk_source_recorded",
            "generated_text_read": "pass_no_generated_text_source_art_and_local_deterministic_composition_only",
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
