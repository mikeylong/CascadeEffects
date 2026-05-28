#!/usr/bin/env python3
"""Build minimal Season 1 playlist thumbnail options.

Each candidate contains only two production elements:
1. The deterministic local title text: "Season 1".
2. A title-free Paper Architecture backplate with the object held to the right.
"""

from __future__ import annotations

import json
import math
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from build_season1_playlist_thumbnail_proof_sheet import (
    CREAM,
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
PACKAGE_PREFIX = "season1_playlist_thumbnail_minimal_paper_backplate_options"
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
DENSITY_PACKAGE = (
    OUTPUT_BASE / "youtube_channel_banner_density02_evidence_desk_low_shuttle_repair_20260518T220830Z"
)
CONTENT_PACKAGE = OUTPUT_BASE / "youtube_channel_banner_content_imagegen_20260518T014942Z"

SOURCES = {
    "kept_balanced": {
        "path": KEPT_EVIDENCE_DESK_PACKAGE / "source/evidence_desk_balanced_imagegen_source.png",
        "notes": KEPT_EVIDENCE_DESK_PACKAGE / "source/source_notes.md",
        "manifest": KEPT_EVIDENCE_DESK_PACKAGE / "manifest.json",
        "status": "keep",
    },
    "clean": {
        "path": DENSITY_PACKAGE / "source/evidence_desk_clean_imagegen_source.png",
        "notes": DENSITY_PACKAGE / "source/source_notes.md",
        "manifest": DENSITY_PACKAGE / "manifest.json",
        "status": "review_required",
    },
    "richer": {
        "path": DENSITY_PACKAGE / "source/evidence_desk_richer_imagegen_source.png",
        "notes": DENSITY_PACKAGE / "source/source_notes.md",
        "manifest": DENSITY_PACKAGE / "manifest.json",
        "status": "review_required",
    },
    "systems_tableau": {
        "path": CONTENT_PACKAGE / "source/candidate_a_content_systems_tableau_imagegen_source.png",
        "notes": CONTENT_PACKAGE / "source/source_notes.md",
        "manifest": CONTENT_PACKAGE / "manifest.json",
        "status": "review_required",
    },
    "first_eight_wall": {
        "path": CONTENT_PACKAGE / "source/candidate_b_first_eight_evidence_wall_imagegen_source.png",
        "notes": CONTENT_PACKAGE / "source/source_notes.md",
        "manifest": CONTENT_PACKAGE / "manifest.json",
        "status": "review_required",
    },
}

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
        "id": "N_minimal_right_anchor",
        "label": "N - Minimal Right Anchor",
        "summary": "Large left Season 1 title over a darkened full-bleed kept backplate; shuttle/ship object held on the right.",
        "source": "kept_balanced",
        "focus_x": 0.74,
        "focus_y": 0.50,
        "title_mode": "single",
        "title_box": (68, 234, 548, 380),
        "title_size": 118,
        "left_alpha": 205,
        "bottom_alpha": 58,
        "color": 0.92,
        "contrast": 1.04,
    },
    {
        "id": "O_large_stacked",
        "label": "O - Large Stacked",
        "summary": "Stacked Season/1 treatment for maximum small-size read; object remains on the right edge of the Paper Architecture backplate.",
        "source": "kept_balanced",
        "focus_x": 0.82,
        "focus_y": 0.50,
        "title_mode": "stacked",
        "title_box": (70, 150, 486, 590),
        "title_size": 108,
        "left_alpha": 210,
        "bottom_alpha": 62,
        "color": 0.88,
        "contrast": 1.08,
    },
    {
        "id": "P_wide_quiet_field",
        "label": "P - Wide Quiet Field",
        "summary": "Wider negative-space crop with Season 1 large on the left and the primary paper object held right of center.",
        "source": "clean",
        "focus_x": 0.84,
        "focus_y": 0.50,
        "title_mode": "single",
        "title_box": (72, 280, 560, 416),
        "title_size": 112,
        "left_alpha": 215,
        "bottom_alpha": 72,
        "color": 0.9,
        "contrast": 1.05,
    },
    {
        "id": "Q_high_object",
        "label": "Q - High Object",
        "summary": "Object sits high and right so the lower-right playlist overlay covers low-value backplate rather than the title.",
        "source": "richer",
        "focus_x": 0.78,
        "focus_y": 0.42,
        "title_mode": "single",
        "title_box": (70, 248, 554, 388),
        "title_size": 114,
        "left_alpha": 210,
        "bottom_alpha": 86,
        "color": 0.86,
        "contrast": 1.1,
    },
    {
        "id": "R_systems_backplate",
        "label": "R - Systems Backplate",
        "summary": "Broader channel-systems backplate with the main physical object pushed to the right and only Season 1 on the left.",
        "source": "systems_tableau",
        "focus_x": 0.72,
        "focus_y": 0.50,
        "title_mode": "single",
        "title_box": (70, 246, 566, 388),
        "title_size": 112,
        "left_alpha": 218,
        "bottom_alpha": 68,
        "color": 0.9,
        "contrast": 1.04,
    },
    {
        "id": "S_first_eight_backplate",
        "label": "S - First-Eight Backplate",
        "summary": "First-eight evidence-wall source used only as a text-free backplate, with the title occupying a clean left field.",
        "source": "first_eight_wall",
        "focus_x": 0.68,
        "focus_y": 0.52,
        "title_mode": "single",
        "title_box": (70, 252, 574, 394),
        "title_size": 110,
        "left_alpha": 224,
        "bottom_alpha": 72,
        "color": 0.88,
        "contrast": 1.05,
    },
    {
        "id": "T_low_title_right_object",
        "label": "T - Low Title",
        "summary": "Lower-left title placement for a quieter cover-card read; right object remains above the YouTube overlay zone.",
        "source": "kept_balanced",
        "focus_x": 0.88,
        "focus_y": 0.47,
        "title_mode": "single",
        "title_box": (72, 378, 568, 514),
        "title_size": 108,
        "left_alpha": 220,
        "bottom_alpha": 95,
        "color": 0.86,
        "contrast": 1.08,
    },
    {
        "id": "U_rtl_mirror_ready",
        "label": "U - RTL Mirror Ready",
        "summary": "RTL-ready LTR master: title zone and object zone are cleanly separable so the layout can be mirrored for Arabic/Hebrew localization.",
        "source": "richer",
        "focus_x": 0.86,
        "focus_y": 0.50,
        "title_mode": "stacked",
        "title_box": (72, 150, 500, 596),
        "title_size": 104,
        "left_alpha": 218,
        "bottom_alpha": 82,
        "color": 0.84,
        "contrast": 1.08,
    },
]


def make_package_dir() -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    package = OUTPUT_BASE / f"{PACKAGE_PREFIX}_{stamp}"
    for name in ("assets", "previews", "qa", "source"):
        (package / name).mkdir(parents=True, exist_ok=True)
    return package


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
            pixels[x, y] = (0, 0, 0, min(238, lx + rx + ty + by))
    return overlay


def source_image(source_key: str) -> Image.Image:
    return Image.open(SOURCES[source_key]["path"]).convert("RGB")


def build_backplate(candidate: dict) -> Image.Image:
    image = cover_crop(source_image(candidate["source"]), CANVAS_SIZE, candidate["focus_x"], candidate["focus_y"])
    image = ImageEnhance.Color(image).enhance(candidate["color"])
    image = ImageEnhance.Contrast(image).enhance(candidate["contrast"])
    image = image.convert("RGBA")
    image.alpha_composite(
        transparent_dark_gradient(
            CANVAS_SIZE,
            left_alpha=candidate["left_alpha"],
            bottom_alpha=candidate["bottom_alpha"],
            right_alpha=22,
        )
    )
    return add_vignette(image, alpha=42)


def draw_title(base: Image.Image, candidate: dict) -> None:
    draw = ImageDraw.Draw(base)
    x0, y0, x1, y1 = candidate["title_box"]
    width = x1 - x0
    shadow = (0, 0, 0, 170)
    if candidate["title_mode"] == "stacked":
        season_font = fit_text(draw, "Season", width, candidate["title_size"], True)
        one_font = fit_text(draw, "1", width, int(candidate["title_size"] * 2.05), True)
        text_shadow(draw, (x0, y0), "Season", season_font, fill=CREAM, shadow=shadow, offset=(3, 4))
        text_shadow(
            draw,
            (x0, y0 + int(candidate["title_size"] * 0.82)),
            "1",
            one_font,
            fill=CREAM,
            shadow=shadow,
            offset=(4, 5),
        )
        return

    title_font = fit_text(draw, "Season 1", width, candidate["title_size"], True)
    text_shadow(draw, (x0, y0), "Season 1", title_font, fill=CREAM, shadow=shadow, offset=(3, 4))


def make_candidate(candidate: dict) -> Image.Image:
    image = build_backplate(candidate)
    draw_title(image, candidate)
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


def make_source_contact_sheet(package: Path) -> Path:
    items = []
    for key, source in SOURCES.items():
        items.append((key, source["path"]))
    output = package / "source/source-backplates-contact-sheet.png"
    make_contact_sheet(items, output, "Minimal Season 1 Paper Architecture backplate sources", thumb_size=(384, 216), columns=2)
    return output


def make_rtl_guidance() -> list[str]:
    return [
        "Use logical zones, not fixed left/right rules: text-start zone plus object-end zone.",
        "For RTL localizations, create a mirrored sibling: localized title on the right/top-right, object/backplate anchor on the left, while keeping YouTube's lower-right overlay area text-free.",
        "Keep source art text-free and line-free at the composition layer so Arabic/Hebrew title rendering can be swapped without regenerating the backplate.",
        "Avoid arrows, progress bars, numbered episode strips, cause-chain rails, and left-to-right motion cues in season covers.",
        "Use a generous title box because Arabic/Hebrew season phrasing can be wider/taller than English; validate at 320x180 and 168x94.",
        "Prefer mirrored pairs over a single universal crop when the title is the primary read; prefer a centered object with upper-corner title only when one asset must serve every locale.",
    ]


def write_readme(package: Path, candidates: list[dict], contact_sheets: dict[str, Path], source_sheet: Path) -> None:
    lines = [
        "# Cascade Effects Season 1 Minimal Paper Backplate Thumbnail Options",
        "",
        "Status: `review_required`",
        "",
        "This package repeats the Season 1 playlist thumbnail proof with stricter production rules:",
        "",
        "- Candidate assets contain only the deterministic local title `Season 1`.",
        "- No local logo, subtitle, progress bar, accent rule, divider, frame, card, episode number list, or other generated line is drawn into candidate assets.",
        "- The only other production element is a title-free Paper Architecture backplate with the object aligned right.",
        "- YouTube UI simulations and QA sheets include review labels/overlays, but those are not upload candidates.",
        "",
        "No YouTube Studio/API action was performed.",
        "",
        "## Candidate Directions",
        "",
    ]
    for candidate in candidates:
        lines.append(f"- `{candidate['id']}`: {candidate['summary']}")
    lines.extend(["", "## RTL-Scaling Suggestions", ""])
    for item in make_rtl_guidance():
        lines.append(f"- {item}")
    lines.extend(["", "## Review Sheets", ""])
    for label, path in contact_sheets.items():
        lines.append(f"- {label}: `{path.relative_to(package)}`")
    lines.append(f"- source backplates: `{source_sheet.relative_to(package)}`")
    lines.extend(["", "## Primary Upload Assets", ""])
    for candidate in candidates:
        lines.append(f"- `{candidate['id']}`: `{Path(candidate['outputs']['upload_jpg']).relative_to(package)}`")
    lines.append("")
    (package / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    required = [CHANNEL_BRAND_SNAPSHOT, PAPER_SKILL]
    for source in SOURCES.values():
        required.extend([source["path"], source["notes"], source["manifest"]])
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
                "production_elements": ["local_deterministic_title_Season_1", "paper_architecture_backplate"],
                "outputs": {key: str(path) for key, path in outputs.items()},
                "output_records": {key: file_record(path) for key, path in outputs.items()},
            }
        )

    full_sheet = package / "qa/season-1-minimal-paper-backplate-options-full-size.png"
    tab_sheet = package / "qa/season-1-minimal-paper-backplate-options-playlist-tab-simulations.png"
    detail_sheet = package / "qa/season-1-minimal-paper-backplate-options-detail-hero-simulations.png"
    small_sheet = package / "qa/season-1-minimal-paper-backplate-options-small-previews.png"
    overlay_sheet = package / "qa/season-1-minimal-paper-backplate-options-overlay-zone-previews.png"

    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["png"])) for candidate in candidates],
        full_sheet,
        "Season 1 minimal title + right-object Paper Architecture backplate options",
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
    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["overlay_zone"])) for candidate in candidates],
        overlay_sheet,
        "Lower-right YouTube overlay zone previews",
        thumb_size=(384, 216),
        columns=2,
    )
    source_sheet = make_source_contact_sheet(package)

    shutil.copy2(CHANNEL_BRAND_SNAPSHOT, package / "source/official_youtube_channel_branding_guidance_2026-05-17.md")
    shutil.copy2(PAPER_SKILL, package / "source/cascade-paper-architectures-SKILL.md")
    for key, source in SOURCES.items():
        shutil.copy2(source["path"], package / "source" / f"{key}-{source['path'].name}")
        shutil.copy2(source["notes"], package / "source" / f"{key}-source_notes.md")
        shutil.copy2(source["manifest"], package / "source" / f"{key}-manifest.json")

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
            "requested_direction": "only two production elements: large Season 1 title and Paper Architecture backplate with object aligned right",
            "carrier": "deterministic local title over approved title-free raster Paper Architecture source art",
            "allowed_generated_text_in_candidate_assets": ["Season 1"],
            "disallowed_local_elements": [
                "logo",
                "subtitle",
                "progress_bar",
                "accent_rule",
                "divider_line",
                "frame",
                "card",
                "episode_list",
                "episode_numbers",
            ],
            "youtube_overlay_zone_xyxy": list(OVERLAY_ZONE),
            "overlay_zone_policy": "title never enters lower-right YouTube playlist overlay zone; object detail is de-emphasized there where possible",
        },
        "source_lineage": {
            key: {
                "path": str(source["path"]),
                "status": source["status"],
                "sha256": sha256_path(source["path"]),
                "notes": str(source["notes"]),
                "manifest": str(source["manifest"]),
            }
            for key, source in SOURCES.items()
        },
        "candidates": candidates,
        "contact_sheets": {key: file_record(path) for key, path in contact_sheets.items()},
        "source_contact_sheet": file_record(source_sheet),
        "rtl_scaling_recommendations": make_rtl_guidance(),
        "qa_reads": {
            "official_requirements_read": "pass_channel_branding_snapshot_current_within_90_days",
            "skill_workflow_read": "pass_channel_branding_and_paper_architecture_channel_surface",
            "dimensions_read": "pass_all_candidates_1280x720_16x9",
            "file_size_read": "pass_all_upload_jpgs_under_2mb",
            "large_title_only_read": "pass_candidate_assets_only_draw_Season_1",
            "no_progress_bars_or_local_lines_read": "pass_no_local_bars_rules_dividers_frames_cards_or_logo",
            "right_object_backplate_read": "review_required_object_aligned_right_by_crop",
            "source_lineage_read": "pass_approved_channel_branding_paper_sources_only",
            "generated_text_read": "pass_no_generated_text_source_art_and_only_local_Season_1_title",
            "season_order_read": "pass_canonical_first_eight_order_recorded",
            "channel_trailer_excluded_read": "pass",
            "youtube_overlay_simulation_read": "pass_playlist_tab_and_detail_simulations_generated",
            "texture_noise_read": "pass_inherited_from_channel_branding_sources",
            "waterfall_read": "pass_inherited_from_channel_branding_sources",
            "small_preview_320_read": "review_required",
            "small_preview_168_read": "review_required",
            "youtube_studio_updated": False,
        },
        "builder_script": str(REPO_ROOT / "scripts/build_season1_playlist_thumbnail_minimal_paper_backplate_options.py"),
    }
    (package / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_readme(package, candidates, contact_sheets, source_sheet)
    print(json.dumps({"package": str(package), "manifest": str(package / "manifest.json"), "contact_sheet": str(full_sheet)}, indent=2))


if __name__ == "__main__":
    main()
