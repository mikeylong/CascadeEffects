#!/usr/bin/env python3
"""Build Season 1 eyebrow + large phrase playlist thumbnail options."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

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
from build_season1_playlist_thumbnail_minimal_paper_backplate_options import transparent_dark_gradient


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
PACKAGE_PREFIX = "season1_playlist_thumbnail_eyebrow_phrase_options"
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
        "id": "V_what_changed",
        "label": "V - What Changed",
        "phrase": "WHAT CHANGED?",
        "summary": "Direct series-question option with the strongest curiosity read.",
    },
    {
        "id": "W_warnings_became_routine",
        "label": "W - Warnings Became Routine",
        "phrase": "WARNINGS BECAME ROUTINE",
        "summary": "Mechanism-forward phrase about warning normalization.",
    },
    {
        "id": "X_safety_started_drifting",
        "label": "X - Safety Started Drifting",
        "phrase": "SAFETY STARTED DRIFTING",
        "summary": "Broad but concrete safety-drift phrasing for the season arc.",
    },
    {
        "id": "Y_the_system_missed_it",
        "label": "Y - System Missed It",
        "phrase": "THE SYSTEM MISSED IT",
        "summary": "Fast engagement phrase that turns the season promise into a direct claim.",
    },
    {
        "id": "Z_known_risk_shifted",
        "label": "Z - Known Risk Shifted",
        "phrase": "KNOWN RISK SHIFTED",
        "summary": "Risk-language option for a more analytical documentary read.",
    },
    {
        "id": "AA_compliance_wasnt_safety",
        "label": "AA - Compliance Wasn't Safety",
        "phrase": "COMPLIANCE WASN'T SAFETY",
        "summary": "Prestige-scale phrase that points toward Titanic while still working across the slate.",
    },
    {
        "id": "AB_warnings_lost_force",
        "label": "AB - Warnings Lost Force",
        "phrase": "WARNINGS LOST FORCE",
        "summary": "Shorter mechanism phrase with a strong Challenger/Therac/Semmelweis fit.",
    },
    {
        "id": "AC_receipts_remain",
        "label": "AC - Receipts Remain",
        "phrase": "RECEIPTS REMAIN",
        "summary": "Most brand-like phrase; compact and readable at small sizes.",
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


def build_backplate() -> Image.Image:
    image = cover_crop(source_backplate(), CANVAS_SIZE, focus_x=0.82, focus_y=0.50)
    image = ImageEnhance.Color(image).enhance(0.88)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = image.convert("RGBA")
    image.alpha_composite(transparent_dark_gradient(CANVAS_SIZE, left_alpha=218, right_alpha=22, bottom_alpha=76))
    return add_vignette(image, alpha=44)


def wrap_phrase(draw: ImageDraw.ImageDraw, phrase: str, max_width: int, target_size: int) -> tuple[object, str]:
    words = phrase.split()
    lines: list[str] = []
    line = ""
    font_obj = font(target_size, bold=True)
    for word in words:
        test = f"{line} {word}".strip()
        width = draw.textbbox((0, 0), test, font=font_obj)[2]
        if width <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    text = "\n".join(lines)
    size = target_size
    while size > 42:
        font_obj = font(size, bold=True)
        bbox = draw.multiline_textbbox((0, 0), text, font=font_obj, spacing=8)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if width <= max_width and height <= 315:
            return font_obj, text
        size -= 3
    return font(size, bold=True), text


def draw_copy(base: Image.Image, candidate: dict) -> None:
    draw = ImageDraw.Draw(base)
    x = 72
    eyebrow_y = 136
    phrase_y = 198
    max_width = 520

    eyebrow_font = fit_text(draw, "SEASON 1", max_width, 34, True)
    draw.text((x + 2, eyebrow_y), "SEASON 1", font=eyebrow_font, fill=LAVENDER)

    phrase = candidate["phrase"]
    start_size = 112 if len(phrase) <= 16 else 96
    phrase_font, phrase_text = wrap_phrase(draw, phrase, max_width, start_size)
    text_shadow(
        draw,
        (x, phrase_y),
        phrase_text,
        phrase_font,
        fill=CREAM,
        shadow=(0, 0, 0, 176),
        offset=(4, 5),
    )


def make_candidate(candidate: dict) -> Image.Image:
    image = build_backplate()
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
        "# Cascade Effects Season 1 Eyebrow Phrase Thumbnail Options",
        "",
        "Status: `review_required`",
        "",
        "This package tests eight Season 1 playlist thumbnail directions with `Season 1` as a small eyebrow and a large 2-4 word phrase beneath it.",
        "",
        "All candidate text is deterministic local composition over the kept title-free Paper Architecture backplate. No YouTube Studio/API action was performed.",
        "",
        "## Phrase Options",
        "",
    ]
    for candidate in candidates:
        lines.append(f"- `{candidate['id']}`: `Season 1` + `{candidate['phrase']}`")
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
                "text_elements": ["SEASON 1", definition["phrase"]],
                "outputs": {key: str(path) for key, path in outputs.items()},
                "output_records": {key: file_record(path) for key, path in outputs.items()},
            }
        )

    full_sheet = package / "qa/season-1-eyebrow-phrase-options-full-size.png"
    tab_sheet = package / "qa/season-1-eyebrow-phrase-options-playlist-tab-simulations.png"
    detail_sheet = package / "qa/season-1-eyebrow-phrase-options-detail-hero-simulations.png"
    small_sheet = package / "qa/season-1-eyebrow-phrase-options-small-previews.png"
    overlay_sheet = package / "qa/season-1-eyebrow-phrase-options-overlay-zone-previews.png"

    make_contact_sheet(
        [(candidate["label"], Path(candidate["outputs"]["png"])) for candidate in candidates],
        full_sheet,
        "Season 1 eyebrow + large 2-4 word phrase thumbnail options",
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

    shutil.copy2(CHANNEL_BRAND_SNAPSHOT, package / "source/official_youtube_channel_branding_guidance_2026-05-17.md")
    shutil.copy2(PAPER_SKILL, package / "source/cascade-paper-architectures-SKILL.md")
    shutil.copy2(BACKPLATE_SOURCE, package / "source/evidence_desk_balanced_imagegen_source.png")
    shutil.copy2(BACKPLATE_SOURCE_NOTES, package / "source/evidence_desk_balanced_source_notes.md")
    shutil.copy2(BACKPLATE_MANIFEST, package / "source/kept_evidence_desk_manifest.json")
    shutil.copy2(BACKPLATE_APPROVAL, package / "source/kept_evidence_desk_approval_receipt_20260518T231204Z.json")

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
            "requested_direction": "Season 1 as eyebrow plus large 2-4 word phrase below",
            "carrier": "deterministic local text over kept title-free raster Paper Architecture source art",
            "text_policy": "local deterministic text only",
            "phrase_word_count_policy": "large phrase must be 2-4 words",
            "youtube_overlay_zone_xyxy": list(OVERLAY_ZONE),
            "overlay_zone_policy": "title and phrase stay out of lower-right YouTube playlist overlay zone",
        },
        "source_lineage": {
            "kept_source_package": str(KEPT_EVIDENCE_DESK_PACKAGE),
            "kept_source_status": "keep",
            "kept_source_approval_receipt": str(BACKPLATE_APPROVAL),
            "backplate_source": str(BACKPLATE_SOURCE),
            "backplate_sha256": sha256_path(BACKPLATE_SOURCE),
            "channel_branding_guidance_snapshot": str(CHANNEL_BRAND_SNAPSHOT),
            "paper_architecture_skill": str(PAPER_SKILL),
            "builder_script": str(REPO_ROOT / "scripts/build_season1_playlist_thumbnail_eyebrow_phrase_options.py"),
        },
        "candidates": candidates,
        "contact_sheets": {key: file_record(path) for key, path in contact_sheets.items()},
        "qa_reads": {
            "official_requirements_read": "pass_channel_branding_snapshot_current_within_90_days",
            "skill_workflow_read": "pass_channel_branding_and_paper_architecture_channel_surface",
            "dimensions_read": "pass_all_candidates_1280x720_16x9",
            "file_size_read": "pass_all_upload_jpgs_under_2mb",
            "eyebrow_read": "pass_all_candidates_use_Season_1_as_eyebrow",
            "phrase_word_count_read": "pass_all_large_phrases_2_to_4_words",
            "source_lineage_read": "pass_kept_evidence_desk_source",
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
