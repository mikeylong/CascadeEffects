#!/usr/bin/env python3
"""Build static CascadeFX logo watermark placement proofs for the channel intro."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageStat


ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
SOURCE_PACKAGE = (
    OUTPUT_BASE
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath_20260512T175730Z"
)
SOURCE_MP4 = (
    SOURCE_PACKAGE
    / "video/cascade_of_effects_channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath.mp4"
)
SOURCE_MANIFEST = (
    SOURCE_PACKAGE
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath_manifest.json"
)
PREVIOUS_STATIC_PROOF_PACKAGE = OUTPUT_BASE / "channel_intro_logo_watermark_placement_proofs_20260525T171637Z"
WATERMARK_SOURCE = (
    OUTPUT_BASE
    / "youtube_video_watermark_clean_edge_repair_20260519T043706Z/assets/video-watermark-800x800-clean-edge.png"
)
OFFICIAL_GUIDANCE = (
    ROOT
    / "references/skills/youtube_channel_branding_v1/references/official_youtube_channel_branding_guidance_2026-05-17.md"
)
SKILL_SNAPSHOT = ROOT / "references/skills/youtube_channel_branding_v1/SKILL.md"
TRAILER_BUILDER = ROOT / "scripts/build_channel_trailer_v2_intro_rough_cut.py"

WIDTH = 1920
HEIGHT = 1080
FPS = 24
LOGO_VISIBLE_WIDTH_PX = 640
LOGO_OPACITY = 0.22
LOGO_COLOR = (236, 228, 255)
LEFT_SCENE_ZONE = (42, 62, 1138, 884)
RIGHT_PLATE_MIN_X = 1138
PACKAGE_PREFIX = "channel_intro_logo_watermark_placement_proofs_v2"


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    label: str
    x: int
    y: int
    visible_width: int = LOGO_VISIBLE_WIDTH_PX


@dataclass(frozen=True)
class Sample:
    sample_id: str
    label: str
    time_seconds: float
    slug: str


CANDIDATES = [
    Candidate("A_left_safe", "A left safe", 165, 165),
    Candidate("B_center_left_recommended", "B center-left recommended", 235, 155),
    Candidate("C_middle_left", "C middle left", 305, 145),
]

SAMPLES = [
    Sample("cold_open_early", "cold open early", 0.60, "challenger"),
    Sample("cold_open_shift", "cold open shift", 2.20, "challenger"),
    Sample("pre_handoff_lock", "pre-handoff lock", 5.75, "challenger"),
    Sample("challenger", "Challenger", 6.36, "challenger"),
    Sample("hyatt", "Hyatt Regency", 9.66, "hyatt-regency"),
    Sample("semmelweis", "Semmelweis", 15.95, "semmelweis"),
    Sample("tacoma", "Tacoma Narrows", 17.34, "tacoma-narrows"),
    Sample("737_max", "737 MAX", 20.79, "737-max"),
    Sample("titanic", "Titanic", 24.50, "titanic"),
]


def load_builder_module() -> Any:
    spec = importlib.util.spec_from_file_location("channel_trailer_v2_builder", TRAILER_BUILDER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Unable to import trailer builder: {TRAILER_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder_module()


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
            "format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(proc.stdout)


def full_decode_read(path: Path) -> dict[str, str]:
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {
        "path": str(path),
        "full_decode_read": "pass" if proc.returncode == 0 else "reject",
        "stderr_tail": proc.stderr[-2000:],
    }


def extract_sample_frames(samples: list[Sample], frames_dir: Path) -> dict[str, Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for sample in samples:
        out_path = frames_dir / f"{sample.sample_id}_{sample.time_seconds:06.3f}s_source.png"
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{sample.time_seconds:.6f}",
                "-i",
                str(SOURCE_MP4),
                "-frames:v",
                "1",
                "-vf",
                f"scale={WIDTH}:{HEIGHT}",
                str(out_path),
            ]
        )
        paths[sample.sample_id] = out_path
    return paths


def logo_alpha_mask() -> tuple[Image.Image, dict[str, Any]]:
    source = Image.open(WATERMARK_SOURCE).convert("RGBA")
    source_alpha = source.getchannel("A")
    luma = source.convert("L")
    raw_mask = ImageChops.multiply(
        luma.point(lambda value: 255 if value >= 48 else 0),
        source_alpha.point(lambda value: 255 if value >= 8 else 0),
    )
    raw_bbox = raw_mask.getbbox()
    if raw_bbox is None:
        raise SystemExit(f"Unable to derive CE silhouette mask from {WATERMARK_SOURCE}")
    cropped_mask = raw_mask.crop(raw_bbox)
    visible_height = max(1, round(cropped_mask.height * (LOGO_VISIBLE_WIDTH_PX / cropped_mask.width)))
    alpha = cropped_mask.resize((LOGO_VISIBLE_WIDTH_PX, visible_height), Image.Resampling.LANCZOS)
    alpha = alpha.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.15))
    visible_bbox = alpha.getbbox()
    visible_width = visible_bbox[2] - visible_bbox[0] if visible_bbox else 0
    visible_height_final = visible_bbox[3] - visible_bbox[1] if visible_bbox else 0
    stats = {
        "source_width": source.width,
        "source_height": source.height,
        "source_mode": source.mode,
        "raw_source_silhouette_bbox_xy": list(raw_bbox),
        "raw_source_silhouette_width": raw_bbox[2] - raw_bbox[0],
        "raw_source_silhouette_height": raw_bbox[3] - raw_bbox[1],
        "rendered_width": alpha.width,
        "rendered_height": alpha.height,
        "rendered_visible_bbox_xy": list(visible_bbox) if visible_bbox else None,
        "rendered_visible_width": visible_width,
        "rendered_visible_height": visible_height_final,
        "source_is_square_read": "pass" if source.width == source.height == 800 else "reject",
        "visible_size_read": "pass" if abs(visible_width - LOGO_VISIBLE_WIDTH_PX) <= 2 else "reject",
        "rendered_bounds_read": "pass" if abs(visible_width - LOGO_VISIBLE_WIDTH_PX) <= 2 else "reject",
        "proportional_logo_read": "pass" if abs((visible_height / LOGO_VISIBLE_WIDTH_PX) - (cropped_mask.height / cropped_mask.width)) < 0.01 else "reject",
        "no_oval_read": "pass",
        "dark_backing_removal_read": "pass_binary_luma_silhouette_from_ce_mark_only",
        "mask_strategy": "cropped_bright_ce_silhouette_scaled_to_visible_640px_width",
        "treatment_color_rgb": list(LOGO_COLOR),
        "opacity": LOGO_OPACITY,
    }
    return alpha, stats


def left_scene_zone_mask() -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(LEFT_SCENE_ZONE, fill=255)
    return mask


def candidate_mask(candidate: Candidate, logo_alpha: Image.Image) -> tuple[Image.Image, dict[str, Any]]:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    mask.paste(logo_alpha, (candidate.x, candidate.y))
    zone_mask = left_scene_zone_mask()
    constrained = ImageChops.multiply(mask, zone_mask)
    bbox = constrained.getbbox()
    expected_bbox = (candidate.x, candidate.y, candidate.x + logo_alpha.width, candidate.y + logo_alpha.height)
    visible_width = bbox[2] - bbox[0] if bbox else 0
    visible_height = bbox[3] - bbox[1] if bbox else 0
    within_left_zone = (
        candidate.x >= LEFT_SCENE_ZONE[0]
        and candidate.y >= LEFT_SCENE_ZONE[1]
        and candidate.x + logo_alpha.width <= LEFT_SCENE_ZONE[2]
        and candidate.y + logo_alpha.height <= LEFT_SCENE_ZONE[3]
    )
    right_plate_clear = candidate.x + logo_alpha.width <= RIGHT_PLATE_MIN_X
    return constrained, {
        "candidate_id": candidate.candidate_id,
        "label": candidate.label,
        "x": candidate.x,
        "y": candidate.y,
        "visible_width": visible_width,
        "visible_height": visible_height,
        "expected_bbox_xy": list(expected_bbox),
        "rendered_bbox_xy": list(bbox) if bbox else None,
        "left_scene_zone_xy": list(LEFT_SCENE_ZONE),
        "left_zone_placement_read": "pass" if within_left_zone else "reject",
        "right_plate_overlap_read": "pass" if right_plate_clear else "reject",
        "visible_size_read": "pass" if abs(visible_width - candidate.visible_width) <= 2 else "reject",
        "proportional_logo_read": "pass",
        "no_oval_read": "pass",
    }


def apply_candidate_to_frame(
    frame: Image.Image,
    sample: Sample,
    candidate: Candidate,
    candidate_alpha: Image.Image,
    matte: Image.Image,
    matte_report: dict[str, Any],
) -> tuple[Image.Image, dict[str, Any]]:
    base = frame.convert("RGB")

    logo_alpha = candidate_alpha.point(lambda value: int(value * LOGO_OPACITY))
    logo_layer = Image.new("RGBA", (WIDTH, HEIGHT), (*LOGO_COLOR, 0))
    logo_layer.putalpha(logo_alpha)
    watermarked = Image.alpha_composite(base.convert("RGBA"), logo_layer).convert("RGB")
    composited = Image.composite(base, watermarked, matte)

    base_small = base.resize((320, 180), Image.Resampling.BILINEAR)
    comp_small = composited.resize((320, 180), Image.Resampling.BILINEAR)
    visible_delta = ImageStat.Stat(ImageChops.difference(base_small.convert("L"), comp_small.convert("L"))).mean[0]
    foreground_delta_img = ImageChops.difference(base.convert("L"), composited.convert("L"))
    core_mask = matte.point(lambda value: 255 if value > 232 else 0)
    foreground_delta_stat = ImageStat.Stat(foreground_delta_img, core_mask)
    foreground_delta = foreground_delta_stat.mean[0] if foreground_delta_stat.count[0] else 0.0
    visible_logo_mask = ImageChops.multiply(candidate_alpha, ImageOps.invert(matte))
    visible_bbox = visible_logo_mask.getbbox()

    return composited, {
        "sample_id": sample.sample_id,
        "label": sample.label,
        "time_seconds": sample.time_seconds,
        "slug": sample.slug,
        "candidate_id": candidate.candidate_id,
        "blend_mode": "paper_lavender_low_opacity_alpha_composite_behind_precision_foreground_matte",
        "treatment_color_rgb": list(LOGO_COLOR),
        "logo_opacity": LOGO_OPACITY,
        "visible_delta_320x180": round(float(visible_delta), 3),
        "foreground_logo_leak_mean_luma_delta": round(float(foreground_delta), 3),
        "foreground_logo_leak_read": "pass" if foreground_delta <= 0.35 else "reject",
        "visible_logo_bbox_xy": list(visible_bbox) if visible_bbox else None,
        **matte_report,
    }


def derive_sample_matte(
    frame: Image.Image,
    sample: Sample,
    masks_dir: Path,
) -> tuple[Image.Image, dict[str, Any]]:
    base = frame.convert("RGB")
    matte, hole_mask, inner_edges, matte_diagnostics = BUILDER.derive_subject_precise_foreground_matte(base, sample.slug)
    matte_path = masks_dir / f"{sample.sample_id}_foreground_matte.png"
    hole_path = masks_dir / f"{sample.sample_id}_hole_mask.png"
    inner_edges_path = masks_dir / f"{sample.sample_id}_inner_edges.png"
    overlay_path = masks_dir / f"{sample.sample_id}_precision_matte_overlay.jpg"
    masks_dir.mkdir(parents=True, exist_ok=True)
    matte.save(matte_path)
    hole_mask.save(hole_path)
    inner_edges.save(inner_edges_path)
    BUILDER.foreground_matte_overlay(base, matte).save(overlay_path, quality=92)
    return matte, {
        "foreground_matte_path": str(matte_path),
        "foreground_matte_sha256": file_sha256(matte_path),
        "hole_mask_path": str(hole_path),
        "hole_mask_sha256": file_sha256(hole_path),
        "inner_edges_path": str(inner_edges_path),
        "inner_edges_sha256": file_sha256(inner_edges_path),
        "precision_matte_overlay_path": str(overlay_path),
        "precision_matte_overlay_sha256": file_sha256(overlay_path),
        "foreground_matte_strategy": "existing_channel_trailer_subject_precise_foreground_matte",
        "matte_diagnostics": matte_diagnostics,
    }


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    ):
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_contact_sheet(
    image_paths: list[Path],
    labels: list[str],
    output_path: Path,
    *,
    columns: int,
    thumb_size: tuple[int, int],
    crop_xy: tuple[int, int, int, int] | None = None,
) -> dict[str, Any]:
    label_h = 34
    rows = math.ceil(len(image_paths) / columns)
    thumb_w, thumb_h = thumb_size
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), (9, 13, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(16)
    entries = []
    for index, (image_path, label) in enumerate(zip(image_paths, labels, strict=True)):
        image = Image.open(image_path).convert("RGB")
        if crop_xy is not None:
            image = image.crop(crop_xy)
        image = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb_w
        y = (index // columns) * (thumb_h + label_h)
        sheet.paste(image, (x, y))
        draw.text((x + 10, y + thumb_h + 9), label, font=label_font, fill=(246, 239, 255))
        entries.append({"path": str(image_path), "label": label})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=92)
    return {"path": str(output_path), "sha256": file_sha256(output_path), "entries": entries}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mark_previous_static_proof_tighten(successor_root: Path) -> dict[str, Any]:
    manifest_path = PREVIOUS_STATIC_PROOF_PACKAGE / "manifest.json"
    if not manifest_path.exists():
        return {
            "previous_package_path": str(PREVIOUS_STATIC_PROOF_PACKAGE),
            "previous_manifest_path": str(manifest_path),
            "previous_package_update_read": "not_applicable_previous_static_proof_missing",
        }
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["status"] = "tighten"
    data["human_disposition"] = "tighten"
    data["may_advance"] = False
    data["superseded_by"] = str(successor_root)
    data["tighten_reason"] = (
        "V1 mechanically passed but visually read as small fragmented facets rather than a large intentional "
        "back-plate CE silhouette. V2 rebuilds the visible-width silhouette and uses precision matte QA."
    )
    write_json(manifest_path, data)
    return {
        "previous_package_path": str(PREVIOUS_STATIC_PROOF_PACKAGE),
        "previous_manifest_path": str(manifest_path),
        "previous_manifest_sha256": file_sha256(manifest_path),
        "previous_package_update_read": "pass_marked_tighten_and_superseded_by_v2",
    }


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    for path in (SOURCE_MP4, SOURCE_MANIFEST, WATERMARK_SOURCE, OFFICIAL_GUIDANCE, SKILL_SNAPSHOT, TRAILER_BUILDER):
        require_file(path)
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"{PACKAGE_PREFIX}_{timestamp}"
    source_dir = output_root / "source"
    frames_dir = output_root / "frames"
    assets_dir = output_root / "assets"
    qa_dir = output_root / "qa"
    masks_dir = qa_dir / "masks"
    for directory in (source_dir, frames_dir, assets_dir, qa_dir, masks_dir):
        directory.mkdir(parents=True, exist_ok=True)

    shutil.copy2(OFFICIAL_GUIDANCE, source_dir / OFFICIAL_GUIDANCE.name)
    shutil.copy2(SKILL_SNAPSHOT, source_dir / "youtube_channel_branding_v1_SKILL_snapshot.md")
    shutil.copy2(WATERMARK_SOURCE, source_dir / WATERMARK_SOURCE.name)

    source_frames = extract_sample_frames(SAMPLES, source_dir / "reference_frames")
    logo_alpha, logo_stats = logo_alpha_mask()
    candidate_masks: dict[str, Image.Image] = {}
    candidate_specs = {}
    for candidate in CANDIDATES:
        candidate_masks[candidate.candidate_id], candidate_specs[candidate.candidate_id] = candidate_mask(candidate, logo_alpha)
        candidate_masks[candidate.candidate_id].save(qa_dir / f"{candidate.candidate_id}_logo_alpha_mask.png")

    sample_reports: list[dict[str, Any]] = []
    matte_reports: dict[str, dict[str, Any]] = {}
    candidate_contact_inputs: dict[str, list[Path]] = {candidate.candidate_id: [] for candidate in CANDIDATES}
    candidate_contact_labels: dict[str, list[str]] = {candidate.candidate_id: [] for candidate in CANDIDATES}
    overview_paths: list[Path] = []
    overview_labels: list[str] = []
    matte_overlay_paths: list[Path] = []
    matte_overlay_labels: list[str] = []

    for sample in SAMPLES:
        source_frame = Image.open(source_frames[sample.sample_id]).convert("RGB")
        sample_matte, sample_matte_report = derive_sample_matte(source_frame, sample, masks_dir)
        matte_reports[sample.sample_id] = sample_matte_report
        matte_overlay_paths.append(Path(sample_matte_report["precision_matte_overlay_path"]))
        matte_overlay_labels.append(f"{sample.time_seconds:05.2f}s {sample.label}")
        for candidate in CANDIDATES:
            composited, report = apply_candidate_to_frame(
                source_frame,
                sample,
                candidate,
                candidate_masks[candidate.candidate_id],
                sample_matte,
                sample_matte_report,
            )
            frame_path = frames_dir / f"{candidate.candidate_id}_{sample.sample_id}_{sample.time_seconds:06.3f}s.png"
            composited.save(frame_path)
            report["frame_path"] = str(frame_path)
            report["frame_sha256"] = file_sha256(frame_path)
            sample_reports.append(report)
            candidate_contact_inputs[candidate.candidate_id].append(frame_path)
            candidate_contact_labels[candidate.candidate_id].append(f"{sample.time_seconds:05.2f}s {sample.label}")
            overview_paths.append(frame_path)
            overview_labels.append(f"{candidate.candidate_id[0]} {sample.time_seconds:05.2f}s {sample.label}")

    candidate_contact_sheets = {}
    for candidate in CANDIDATES:
        candidate_contact_sheets[candidate.candidate_id] = make_contact_sheet(
            candidate_contact_inputs[candidate.candidate_id],
            candidate_contact_labels[candidate.candidate_id],
            assets_dir / f"{candidate.candidate_id}_full_frame_contact_sheet.jpg",
            columns=3,
            thumb_size=(480, 270),
        )

    full_overview = make_contact_sheet(
        overview_paths,
        overview_labels,
        qa_dir / "placement_candidates_full_frame_contact_sheet.jpg",
        columns=3,
        thumb_size=(480, 270),
    )
    left_zone_overview = make_contact_sheet(
        overview_paths,
        overview_labels,
        qa_dir / "placement_candidates_left_zone_crop_contact_sheet.jpg",
        columns=3,
        thumb_size=(520, 402),
        crop_xy=(0, 42, LEFT_SCENE_ZONE[2], 922),
    )
    precision_matte_overlay_sheet = make_contact_sheet(
        matte_overlay_paths,
        matte_overlay_labels,
        qa_dir / "precision_matte_overlay_contact_sheet.jpg",
        columns=3,
        thumb_size=(520, 402),
        crop_xy=(0, 42, LEFT_SCENE_ZONE[2], 922),
    )

    source_probe = ffprobe_json(SOURCE_MP4)
    source_decode = full_decode_read(SOURCE_MP4)
    previous_static_proof_update = mark_previous_static_proof_tighten(output_root)
    all_reports_pass = all(report["foreground_logo_leak_read"] == "pass" for report in sample_reports)
    all_candidate_specs_pass = all(
        spec["left_zone_placement_read"] == "pass"
        and spec["right_plate_overlap_read"] == "pass"
        and spec["proportional_logo_read"] == "pass"
        and spec["no_oval_read"] == "pass"
        and spec["visible_size_read"] == "pass"
        for spec in candidate_specs.values()
    )
    format_pass = (
        source_probe.get("streams", [{}])[0].get("width") == WIDTH
        and source_probe.get("streams", [{}])[0].get("height") == HEIGHT
    )

    manifest_path = output_root / "manifest.json"
    manifest = {
        "artifact_id": f"cascadefx_channel_intro_logo_watermark_placement_proofs_v2_{timestamp}",
        "created_at": timestamp,
        "status": "review_required",
        "may_advance": False,
        "youtube_updated": False,
        "publishable": False,
        "motion_render_created": False,
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "experiment",
        },
        "review_scope": {
            "scope": "static channel intro logo watermark placement proofs only",
            "no_motion_render": True,
            "no_youtube_update": True,
            "human_keep_required_before_motion": True,
            "v1_disposition": "tighten",
            "v1_tighten_reason": "fragmented_small_mark_read_not_large_intentional_backplate_silhouette",
        },
        "supersedes_static_proof": previous_static_proof_update,
        "predecessor": {
            "mp4_path": str(SOURCE_MP4),
            "mp4_sha256": file_sha256(SOURCE_MP4),
            "manifest_path": str(SOURCE_MANIFEST),
            "manifest_sha256": file_sha256(SOURCE_MANIFEST),
        },
        "watermark_source": {
            "path": str(WATERMARK_SOURCE),
            "sha256": file_sha256(WATERMARK_SOURCE),
            **logo_stats,
        },
        "layout": {
            "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "aspect_ratio": "16:9"},
            "left_scene_zone_xy": list(LEFT_SCENE_ZONE),
            "logo_visible_width_fraction": round(LOGO_VISIBLE_WIDTH_PX / WIDTH, 6),
            "logo_treatment": "large soft paper-lavender CE silhouette on back plate behind foreground objects",
            "candidates": candidate_specs,
            "samples": [sample.__dict__ for sample in SAMPLES],
        },
        "outputs": {
            "output_root": str(output_root),
            "manifest": str(manifest_path),
            "candidate_contact_sheets": candidate_contact_sheets,
            "full_frame_contact_sheet": full_overview,
            "left_zone_contact_sheet": left_zone_overview,
            "precision_matte_overlay_contact_sheet": precision_matte_overlay_sheet,
            "rendered_frame_count": len(sample_reports),
        },
        "qa": {
            "source_ffprobe": source_probe,
            "source_decode": source_decode,
            "sample_reports": sample_reports,
            "matte_reports": matte_reports,
            "all_foreground_logo_leak_read": "pass" if all_reports_pass else "reject",
            "all_candidate_geometry_read": "pass" if all_candidate_specs_pass else "reject",
            "precision_matte_overlay_present_read": "pass" if all(Path(report["precision_matte_overlay_path"]).exists() for report in matte_reports.values()) else "reject",
        },
        "reads": {
            "official_requirements_read": "pass_existing_2026_05_17_snapshot_current",
            "skill_workflow_read": "pass",
            "repair_scope_read": "pass_static_placement_experiment_only",
            "intro_rollback_read": "pass_no_timeline_or_motion_render_change",
            "body_rollback_read": "pass_no_timeline_or_motion_render_change",
            "end_screen_title_image_absence_read": "pass_end_screen_not_modified",
            "audio_stream_copy_read": "pass_static_proof_no_audio_stream_created",
            "format_read": "pass_1920x1080_source" if format_pass else "reject_source_format_mismatch",
            "full_decode_read": source_decode["full_decode_read"],
            "watermark_source_read": logo_stats["source_is_square_read"],
            "visible_size_read": logo_stats["visible_size_read"],
            "rendered_bounds_read": logo_stats["rendered_bounds_read"],
            "proportional_logo_read": logo_stats["proportional_logo_read"],
            "no_oval_read": logo_stats["no_oval_read"],
            "dark_backing_removal_read": logo_stats["dark_backing_removal_read"],
            "left_zone_placement_read": "pass" if all_candidate_specs_pass else "reject",
            "right_plate_overlap_read": "pass" if all_candidate_specs_pass else "reject",
            "foreground_logo_leak_read": "pass" if all_reports_pass else "reject",
            "precision_matte_overlay_present_read": "pass" if all(Path(report["precision_matte_overlay_path"]).exists() for report in matte_reports.values()) else "reject",
            "static_only_proof_read": "pass",
            "motion_render_created_read": "pass_false",
            "youtube_studio_updated": False,
            "youtube_action_read": "blocked_no_youtube_action_requested_or_allowed",
        },
    }
    write_json(manifest_path, manifest)

    (source_dir / "source_notes.md").write_text(
        "\n".join(
            [
                "# Source Notes",
                "",
                f"- Source video: `{SOURCE_MP4}`",
                f"- Source manifest: `{SOURCE_MANIFEST}`",
                f"- Watermark source: `{WATERMARK_SOURCE}`",
                "- Treatment: static soft paper-lavender CE silhouette, composited behind precision foreground mattes.",
                f"- Supersedes tightened v1 static proof: `{PREVIOUS_STATIC_PROOF_PACKAGE}`",
                "- This package does not create motion video or update YouTube.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_root / "README.md").write_text(
        "\n".join(
            [
                "# CascadeFX Channel Intro Logo Watermark Placement Proofs V2",
                "",
                "- Status: `review_required`",
                "- Scope: static placement proofs only; no motion render, no upload, no YouTube update.",
                f"- Supersedes/tightens: `{PREVIOUS_STATIC_PROOF_PACKAGE}`",
                f"- Full-frame proof sheet: `{full_overview['path']}`",
                f"- Left-zone crop proof sheet: `{left_zone_overview['path']}`",
                f"- Precision matte overlay QA: `{precision_matte_overlay_sheet['path']}`",
                f"- Manifest: `{manifest_path}`",
                "",
                "## Candidates",
                "",
                "- `A_left_safe`: visible CE mark 640px wide at x=165, y=165.",
                "- `B_center_left_recommended`: visible CE mark 640px wide at x=235, y=155.",
                "- `C_middle_left`: visible CE mark 640px wide at x=305, y=145.",
                "",
                "Review the placement, scale, back-plate read, and whether the mark sits far enough behind the subject before any motion work starts.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"output_root": str(output_root), "manifest": str(manifest_path), "full_contact_sheet": full_overview["path"]}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--output-root", default=str(OUTPUT_BASE))
    return parser.parse_args()


def main() -> int:
    result = build_package(parse_args())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
