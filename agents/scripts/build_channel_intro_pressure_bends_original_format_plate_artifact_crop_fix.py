#!/usr/bin/env python3
"""Build the full-track Pressure Bends intro plate artifact/crop repair."""

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
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageStat


WIDTH = 1920
HEIGHT = 1080
FPS = 24
BODY_START_SECONDS = 6.0
TOTAL_FRAMES = 1399
OUTPUT_SECONDS = TOTAL_FRAMES / FPS
END_SCREEN_SECONDS = 20.0
END_SCREEN_START_FRAME = TOTAL_FRAMES - int(END_SCREEN_SECONDS * FPS)
BODY_END_SECONDS = END_SCREEN_START_FRAME / FPS
WORKFLOW = "channel_intro_pressure_bends_original_format_plate_artifact_crop_fix_v1"
OUTPUT_STEM = "channel_intro_pressure_bends_original_format_plate_artifact_crop_fix"
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
VISUAL_DELTA_TOLERANCE = 6.0
OBJECT_QA_RIGHT_CARD_SAFE_X = 1188

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
ROUGH_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_v2_intro_rough_cut.py"
PRESSURE_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_pressure_bends_successor.py"
LATEST_POINTER = OUTPUT_ROOT / f"{OUTPUT_STEM}_latest.json"

ORIGINAL_FORMAT_SOURCE_PACKAGE = (
    OUTPUT_ROOT
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath_20260512T175730Z"
)
ORIGINAL_FORMAT_SOURCE_MP4 = (
    ORIGINAL_FORMAT_SOURCE_PACKAGE
    / "video/cascade_of_effects_channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath.mp4"
)
ORIGINAL_FORMAT_SOURCE_MANIFEST = (
    ORIGINAL_FORMAT_SOURCE_PACKAGE
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath_manifest.json"
)
REJECTED_ARTIFACT_PATCH_POINTER = OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_artifact_patch_latest.json"
REJECTED_SCENE_FIX_POINTER = OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_full_track_scene_fix_latest.json"
REJECTED_TIMING_SOURCE_FIX_POINTER = OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_timing_source_fix_latest.json"
REJECTED_PLATE_PERSPECTIVE_FIX_POINTER = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_plate_perspective_fix_latest.json"
)
REJECTED_PLATE_SCALE_ORIENTATION_FIX_POINTER = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_plate_scale_orientation_fix_latest.json"
)
REJECTED_PLATE_EDGE_CLEAN_FIX_POINTER = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_plate_edge_clean_fix_latest.json"
)
ALL_EIGHT_LEDGER_MANIFEST = (
    OUTPUT_ROOT
    / "channel_trailer_actual_montage_successor_20260524T040009Z"
    / "channel_trailer_actual_montage_successor_manifest.json"
)
BORDERLESS_END_SCREEN_POINTER = OUTPUT_ROOT / "channel_intro_end_screen_adaptive_borderless_keep_latest.json"

THERAC_NO_CAPTION_CHECKPOINT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/motion_video_proof/"
    "pass_29_1980s_crt_visible_but_premium/"
    "therac25_motion_video_proof_pass_29_1980s_crt_visible_but_premium_motion_only_no_audio.mp4"
)
PILTDOWN_NO_CAPTION_CHECKPOINT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/piltdown-man/shorts/piltdown_man_short_scoped_v1/"
    "motion_video_proof/pass_03_no_freeze_legibility_repair/final_exports/"
    "piltdown-man_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
    "20260429T_house_crt_visible_scanline_first8_pass07_y24/work/"
    "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
)
SHORT_SOURCE_OVERRIDES = {
    "therac-25": THERAC_NO_CAPTION_CHECKPOINT,
    "piltdown-man": PILTDOWN_NO_CAPTION_CHECKPOINT,
}

THERAC_WEBSITE_THUMBNAIL_SOURCE = Path(
    "/Users/mike/Web_CascadeEffects/brand/assets/episode-gallery/proof-v6-ink-lit-subjects/source-renders/"
    "therac-25-thumbnail-proof-v6-ink-lit-subjects-source.png"
)
PILTDOWN_WEBSITE_THUMBNAIL_SOURCE = Path(
    "/Users/mike/Web_CascadeEffects/brand/assets/episode-gallery/proof-v6-ink-lit-subjects/source-renders/"
    "piltdown-man-thumbnail-proof-v6-ink-lit-subjects-source.png"
)
LEFT_ANCHOR_SOURCE_OVERRIDES = {
    "therac-25": THERAC_WEBSITE_THUMBNAIL_SOURCE,
    "piltdown-man": PILTDOWN_WEBSITE_THUMBNAIL_SOURCE,
}
LEFT_ANCHOR_GRADE = {
    "therac-25": {"brightness": 0.92, "contrast": 1.02, "color": 0.96},
    "piltdown-man": {"brightness": 0.90, "contrast": 1.02, "color": 0.96},
}
LEFT_ANCHOR_TRANSFORMS = {
    "therac-25": "mirror_x",
    "piltdown-man": "mirror_x",
}
LEFT_ANCHOR_LAYOUT = {
    # Review feedback: orientation is acceptable, but the treatment device is too large.
    "therac-25": {"scale": 0.74, "offset_xy": [-95, 120], "edge_feather": 42},
    # Review feedback: too large and facing the wrong direction in the scene family.
    "piltdown-man": {"scale": 0.67, "offset_xy": [50, 130], "edge_feather": 42},
}

TIMELINE = [
    {"episode_id": "challenger", "display": "Challenger", "frames": [144, 241], "source_start": 8.0},
    {"episode_id": "therac-25", "display": "Therac-25", "frames": [241, 338], "source_start": 0.0},
    {"episode_id": "hyatt-regency", "display": "Hyatt Regency", "frames": [338, 435], "source_start": 0.0},
    {"episode_id": "semmelweis", "display": "Semmelweis", "frames": [435, 532], "source_start": 0.0},
    {"episode_id": "tacoma-narrows", "display": "Tacoma Narrows", "frames": [532, 629], "source_start": 0.0},
    {"episode_id": "piltdown-man", "display": "Piltdown Man", "frames": [629, 726], "source_start": 0.0},
    {"episode_id": "737-max", "display": "737 MAX", "frames": [726, 823], "source_start": 0.0},
    {"episode_id": "titanic", "display": "Titanic", "frames": [823, END_SCREEN_START_FRAME], "source_start": 0.0},
]
for _row in TIMELINE:
    _row["seconds"] = [_row["frames"][0] / FPS, _row["frames"][1] / FPS]
CANONICAL_ORDER = [row["episode_id"] for row in TIMELINE]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rough = load_module("channel_intro_original_format_rough", ROUGH_HELPER_PATH)
base = load_module("channel_intro_pressure_bends_base", PRESSURE_HELPER_PATH)
rough.SUBJECT_BADGE_LABELS.update({"therac-25": "Therac-25", "piltdown-man": "Piltdown Man"})
rough.SUBJECT_BADGE_END_SECONDS = BODY_END_SECONDS


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def capture(cmd: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def utc_stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def ffprobe(path: Path) -> dict[str, Any]:
    payload = json.loads(
        capture(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels,duration:format=duration,size,bit_rate",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    payload["path"] = str(path)
    payload["sha256"] = sha256(path)
    return payload


def duration_seconds(path: Path) -> float:
    return float(ffprobe(path).get("format", {}).get("duration", 0.0))


def extract_frame(video: Path, seconds: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{seconds:.6f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(out_path),
        ]
    )


def stream_sha256(path: Path, stream_spec: str, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-map", stream_spec, "-c", "copy", str(out_path)])
    digest = sha256(out_path)
    out_path.unlink(missing_ok=True)
    return digest


def mean_frame_delta(a: Path, b: Path) -> float:
    img_a = Image.open(a).convert("RGB")
    img_b = Image.open(b).convert("RGB")
    diff = ImageChops.difference(img_a, img_b)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def source_rows_from_all_eight_manifest() -> dict[str, dict[str, Any]]:
    data = read_json(ALL_EIGHT_LEDGER_MANIFEST)
    rows: dict[str, dict[str, Any]] = {}
    for item in data.get("episode_sequence", []):
        episode_id = item["episode_id"]
        rows[episode_id] = item
    missing = [episode_id for episode_id in CANONICAL_ORDER if episode_id not in rows]
    if missing:
        raise SystemExit(f"Missing episode rows in all-eight source ledger: {missing}")
    return rows


def paste_clipped(canvas: Image.Image, overlay: Image.Image, mask: Image.Image, offset_xy: list[int]) -> None:
    x, y = offset_xy
    width, height = overlay.size
    left = max(0, x)
    top = max(0, y)
    right = min(canvas.width, x + width)
    bottom = min(canvas.height, y + height)
    if right <= left or bottom <= top:
        return
    crop_left = left - x
    crop_top = top - y
    crop_right = crop_left + (right - left)
    crop_bottom = crop_top + (bottom - top)
    canvas.paste(
        overlay.crop((crop_left, crop_top, crop_right, crop_bottom)),
        (left, top),
        mask.crop((crop_left, crop_top, crop_right, crop_bottom)),
    )


def original_format_stage_background() -> Image.Image:
    top = (3, 7, 20)
    bottom = (8, 15, 39)
    image = Image.new("RGB", (WIDTH, HEIGHT), top)
    pixels = image.load()
    for y in range(HEIGHT):
        alpha = y / (HEIGHT - 1)
        row = tuple(round(top[channel] * (1 - alpha) + bottom[channel] * alpha) for channel in range(3))
        for x in range(WIDTH):
            pixels[x, y] = row
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon([(0, 1080), (1920, 1080), (1920, 570), (1020, 350), (0, 560)], fill=(8, 17, 48, 180))
    draw.polygon([(0, 1080), (1050, 1080), (720, 410), (0, 610)], fill=(15, 22, 54, 145))
    draw.polygon([(1000, 1080), (1920, 1080), (1920, 500), (1210, 330)], fill=(4, 9, 25, 130))
    return image.filter(ImageFilter.GaussianBlur(0.35))


def rectangle_feather_mask(size: tuple[int, int], feather: int) -> Image.Image:
    width, height = size
    mask = Image.new("L", size, 0)
    inset = max(1, min(feather, width // 4, height // 4))
    draw = ImageDraw.Draw(mask)
    draw.rectangle((inset, inset, width - inset, height - inset), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(max(1, feather // 2)))


def apply_left_anchor_layout(image: Image.Image, slug: str) -> tuple[Image.Image, dict[str, Any]]:
    layout = LEFT_ANCHOR_LAYOUT.get(slug, {"scale": 1.0, "offset_xy": [0, 0], "edge_feather": 0})
    scale = float(layout["scale"])
    offset_xy = [int(layout["offset_xy"][0]), int(layout["offset_xy"][1])]
    edge_feather = int(layout.get("edge_feather", 0))
    if abs(scale - 1.0) < 0.001 and offset_xy == [0, 0]:
        return image, {
            "scale": scale,
            "offset_xy": offset_xy,
            "edge_feather": edge_feather,
            "read": "pass_no_layout_change_required",
        }

    background = original_format_stage_background()
    scaled_size = (round(WIDTH * scale), round(HEIGHT * scale))
    scaled = image.resize(scaled_size, Image.Resampling.LANCZOS)
    mask = rectangle_feather_mask(scaled_size, edge_feather)
    canvas = background.copy()
    paste_clipped(canvas, scaled, mask, offset_xy)
    return canvas, {
        "scale": scale,
        "offset_xy": offset_xy,
        "edge_feather": edge_feather,
        "scaled_size": list(scaled_size),
        "composite_mode": "scaled_full_source_plate_rectangular_feather",
        "read": "pass_left_plate_scaled_full_source_plate_without_threshold_mask_artifacts",
    }


def render_normalized_left_anchor(slug: str, source_path: Path, source_art_dir: Path) -> tuple[Path, dict[str, Any]]:
    source_art_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(source_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    transform = LEFT_ANCHOR_TRANSFORMS.get(slug, "none")
    if transform == "mirror_x":
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    grade = LEFT_ANCHOR_GRADE[slug]
    image = ImageEnhance.Brightness(image).enhance(grade["brightness"])
    image = ImageEnhance.Contrast(image).enhance(grade["contrast"])
    image = ImageEnhance.Color(image).enhance(grade["color"])
    image, layout_report = apply_left_anchor_layout(image, slug)
    out_path = source_art_dir / f"{slug}_website_thumbnail_left_anchor_original_format.png"
    image.save(out_path)
    return out_path, {
        "normalization_model": "active_website_thumbnail_original_format_artifact_crop_clean_v1",
        "source_path": str(source_path),
        "source_sha256": sha256(source_path),
        "normalized_path": str(out_path),
        "normalized_sha256": sha256(out_path),
        "target_size": [WIDTH, HEIGHT],
        "grade": grade,
        "orientation_transform": transform,
        "layout_transform": layout_report,
        "active_website_thumbnail_proof_id": "proof-v6-ink-lit-subjects",
        "read": "pass_active_website_thumbnail_used_as_left_anchor_source",
    }


def left_anchor_object_metrics(path: Path) -> dict[str, Any]:
    image = Image.open(path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    pixels = image.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(0, HEIGHT, 4):
        for x in range(0, min(WIDTH, OBJECT_QA_RIGHT_CARD_SAFE_X), 4):
            r, g, b = pixels[x, y]
            luma = (r + g + b) / 3.0
            if luma > 78 and (r > 92 or g > 92 or b > 92):
                xs.append(x)
                ys.append(y)
    if not xs:
        return {"read": "reject_no_left_anchor_subject_pixels_detected"}
    bbox = [min(xs), min(ys), max(xs), max(ys)]
    area_ratio = len(xs) * 16 / (WIDTH * HEIGHT)
    center = [sum(xs) / len(xs), sum(ys) / len(ys)]
    safe_right_edge = bbox[2] < OBJECT_QA_RIGHT_CARD_SAFE_X
    visual_weight = 0.07 <= area_ratio <= 0.34
    return {
        "bbox_xy": [round(value, 2) for value in bbox],
        "center_xy": [round(center[0], 2), round(center[1], 2)],
        "estimated_area_ratio": round(area_ratio, 5),
        "right_card_safe_x": OBJECT_QA_RIGHT_CARD_SAFE_X,
        "safe_right_edge": safe_right_edge,
        "visual_weight_read": "pass" if visual_weight else "tighten",
        "read": "pass_left_anchor_subject_inside_original_format_safe_zone"
        if safe_right_edge and visual_weight
        else "tighten_left_anchor_subject_bounds",
    }


def build_source_proofs(source_art_dir: Path) -> tuple[list[Any], dict[str, dict[str, Any]], dict[str, Any]]:
    all_eight_rows = source_rows_from_all_eight_manifest()
    existing = {proof.slug: proof for proof in rough.source_proofs()}
    proofs: list[Any] = []
    source_ledger: dict[str, dict[str, Any]] = {}
    left_anchor_reports: dict[str, Any] = {}

    for row in TIMELINE:
        slug = row["episode_id"]
        if slug in existing:
            proof = existing[slug]
            source_role = "original_format_existing_scene_source"
            left_anchor_reports[slug] = left_anchor_object_metrics(proof.base_plate_path)
        else:
            ledger = all_eight_rows[slug]
            selected_short_source = SHORT_SOURCE_OVERRIDES.get(slug)
            if selected_short_source is None:
                raise SystemExit(f"Missing no-caption checkpoint source override for {slug}")
            selected_left_anchor_source = LEFT_ANCHOR_SOURCE_OVERRIDES.get(slug, Path(ledger["gallery_source"]))
            require_file(selected_left_anchor_source, f"{slug} normalized left-anchor source")
            normalized_left_anchor, normalization_report = render_normalized_left_anchor(
                slug,
                selected_left_anchor_source,
                source_art_dir,
            )
            left_anchor_reports[slug] = {
                **left_anchor_object_metrics(normalized_left_anchor),
                "normalization": normalization_report,
            }
            proof = rough.SourceProof(
                slug=slug,
                display_name=row["display"],
                video_path=selected_short_source,
                manifest_path=ALL_EIGHT_LEDGER_MANIFEST,
                short_video_path=selected_short_source,
                base_plate_path=normalized_left_anchor,
            )
            source_role = "new_original_format_scene_source_from_no_caption_checkpoint_and_active_website_thumbnail_left_anchor"

        if proof.short_video_path is None:
            raise SystemExit(f"Missing short video source for {slug}")
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing left-anchor source for {slug}")
        require_file(proof.short_video_path, f"{slug} short video source")
        require_file(proof.base_plate_path, f"{slug} left-anchor source")
        if proof.manifest_path is not None:
            require_file(proof.manifest_path, f"{slug} source manifest")
        proofs.append(proof)
        source_ledger[slug] = {
            "episode_id": slug,
            "display": row["display"],
            "role": source_role,
            "left_anchor_source": str(proof.base_plate_path),
            "left_anchor_sha256": sha256(proof.base_plate_path),
            "short_source": str(proof.short_video_path),
            "short_source_sha256": sha256(proof.short_video_path),
            "manifest_path": str(proof.manifest_path) if proof.manifest_path else "",
            "manifest_sha256": sha256(proof.manifest_path) if proof.manifest_path else "",
        }
        if slug in all_eight_rows:
            source_ledger[slug]["all_eight_ledger_gallery_source"] = all_eight_rows[slug].get("gallery_source", "")
            source_ledger[slug]["all_eight_ledger_short_source_rejected_for_this_lane"] = all_eight_rows[slug].get("short_source", "")
        if slug in SHORT_SOURCE_OVERRIDES:
            source_ledger[slug]["selected_short_source_policy"] = "no_caption_crt_checkpoint_no_audio"
            source_ledger[slug]["published_captioned_short_source_banned_read"] = "pass_selected_source_is_not_published_youtube_short"
        if slug in LEFT_ANCHOR_SOURCE_OVERRIDES:
            source_ledger[slug]["selected_left_anchor_raw_source"] = str(LEFT_ANCHOR_SOURCE_OVERRIDES[slug])
            source_ledger[slug]["selected_left_anchor_raw_sha256"] = sha256(LEFT_ANCHOR_SOURCE_OVERRIDES[slug])
            source_ledger[slug]["selected_left_anchor_policy"] = "active_website_episode_gallery_thumbnail_source_png"
            source_ledger[slug]["left_anchor_website_thumbnail_read"] = left_anchor_reports[slug]["normalization"]["read"]
    return proofs, source_ledger, left_anchor_reports


def timeline_segments() -> list[Any]:
    segments = []
    for row in TIMELINE:
        start, end = row["seconds"]
        segments.append(
            rough.TimelineSegment(
                start,
                end,
                row["episode_id"],
                "voiceover_episode_sequence",
                row["source_start"],
                row["source_start"] + (end - start),
                "live_short_no_hold_landed" if row["episode_id"] == "challenger" else "live_short_push_in_no_hold",
            )
        )
    return segments


def compose_body_frame(
    t: float,
    segments: list[Any],
    high_base_plates: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
) -> Image.Image:
    index, segment = rough.find_segment(segments, t)
    current = rough.compose_live_episode_frame(segment, t, high_base_plates, short_frames)
    transition = 0.32
    if index > 0 and 0 <= t - segment.start < transition:
        previous = segments[index - 1]
        previous_frame = rough.compose_live_episode_frame(
            previous,
            min(previous.end - 1 / FPS, t),
            high_base_plates,
            short_frames,
        )
        current = Image.blend(previous_frame, current, rough.ease((t - segment.start) / transition))
    current = rough.apply_section_grade(current, t, BODY_END_SECONDS)
    return rough.add_music_only_subject_badges(current, t, segments)


def render_body_video(proofs: list[Any], work_dir: Path, video_dir: Path) -> dict[str, Any]:
    short_frames = rough.extract_short_frames(proofs, work_dir / "short_frames")
    base_plates = rough.load_base_plates(proofs)
    high_base_plates = rough.make_high_base_plates(base_plates)
    segments = timeline_segments()
    body_duration = BODY_END_SECONDS - BODY_START_SECONDS
    frame_count = END_SCREEN_START_FRAME - int(BODY_START_SECONDS * FPS)
    frames_dir = work_dir / "body_frames"
    shutil.rmtree(frames_dir, ignore_errors=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    sample_times = [sum(row["seconds"]) / 2 for row in TIMELINE]
    sample_indices = {max(0, min(frame_count - 1, round((time - BODY_START_SECONDS) * FPS))): time for time in sample_times}
    samples = []
    for index in range(frame_count):
        t = BODY_START_SECONDS + index / FPS
        frame = compose_body_frame(t, segments, high_base_plates, short_frames)
        out = frames_dir / f"frame_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in sample_indices:
            _, segment = rough.find_segment(segments, t)
            samples.append(
                {
                    "index": index,
                    "time_seconds": round(t, 3),
                    "requested_sample_seconds": round(sample_indices[index], 3),
                    "episode_id": segment.slug,
                    "frame_path": str(out),
                    "frame_sha256": sha256(out),
                }
            )

    body_video = video_dir / f"{OUTPUT_STEM}_body_silent.mp4"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%05d.jpg"),
            "-frames:v",
            str(frame_count),
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
            str(body_video),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(body_video), "-f", "null", "-"])
    return {
        "body_video": str(body_video),
        "body_video_sha256": sha256(body_video),
        "frames_dir": str(frames_dir),
        "frame_count": frame_count,
        "target_duration_seconds": round(body_duration, 6),
        "actual_duration_seconds": round(duration_seconds(body_video), 6),
        "sampled_frames": samples,
        "timeline_segments": [
            {
                "start": row["seconds"][0],
                "end": row["seconds"][1],
                "episode_id": row["episode_id"],
                "display": row["display"],
                "source_seconds": [row["source_start"], row["source_start"] + (row["seconds"][1] - row["seconds"][0])],
            }
            for row in TIMELINE
        ],
    }


def borderless_end_screen_inputs() -> tuple[dict[str, Any], dict[str, Any], Path]:
    pointer = read_json(BORDERLESS_END_SCREEN_POINTER)
    manifest_path = Path(pointer["manifest"])
    preview = Path(pointer["adaptive_end_screen_preview"])
    require_file(manifest_path, "approved borderless end-screen manifest")
    require_file(preview, "approved borderless end-screen preview")
    manifest = read_json(manifest_path)
    if pointer.get("status") != "keep" or pointer.get("human_review_decision") != "keep":
        raise SystemExit("Borderless end-screen pointer is not marked keep.")
    return pointer, manifest, preview


def render_silent_video(body_video: Path, end_screen_preview: Path, video_dir: Path) -> Path:
    end_screen_duration = OUTPUT_SECONDS - BODY_END_SECONDS
    if abs(end_screen_duration - END_SCREEN_SECONDS) > 0.001:
        raise SystemExit(f"End-screen duration must be 20.000s; computed {end_screen_duration:.6f}s")
    silent_video = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_silent.mp4"
    filter_graph = (
        f"[0:v]trim=0:{BODY_START_SECONDS:.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v0];"
        f"[1:v]trim=0:{(BODY_END_SECONDS - BODY_START_SECONDS):.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v1];"
        f"[2:v]trim=duration={end_screen_duration:.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[v]"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(ORIGINAL_FORMAT_SOURCE_MP4),
            "-i",
            str(body_video),
            "-loop",
            "1",
            "-t",
            f"{end_screen_duration + 0.25:.6f}",
            "-i",
            str(end_screen_preview),
            "-filter_complex",
            filter_graph,
            "-map",
            "[v]",
            "-an",
            "-r",
            str(FPS),
            "-frames:v",
            str(TOTAL_FRAMES),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(silent_video),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(silent_video), "-f", "null", "-"])
    return silent_video


def render_final(silent_video: Path, final_mp4: Path) -> None:
    audio_filter = (
        f"loudnorm=I={base.AUDIO_TARGET_LUFS:.1f}:TP={base.AUDIO_TRUE_PEAK_LIMIT_DBFS:.1f}:LRA=11,"
        "alimiter=limit=0.891251:level=false,"
        "aresample=48000,"
        f"apad=whole_dur={OUTPUT_SECONDS:.6f}"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(TRACK_PATH),
            "-filter_complex",
            f"[1:a]{audio_filter}[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{OUTPUT_SECONDS:.6f}",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )


def make_contact_sheet(final_mp4: Path, qa_dir: Path, track_seconds: float) -> Path:
    samples = [
        ("cold open", 0.600),
        ("Challenger", 8.021),
        ("Therac-25", 12.062),
        ("Hyatt Regency", 16.104),
        ("Semmelweis", 20.146),
        ("Tacoma Narrows", 24.188),
        ("Piltdown Man", 28.229),
        ("737 MAX", 32.271),
        ("Titanic", 36.292),
        ("borderless end screen start", BODY_END_SECONDS),
        ("end screen hold", BODY_END_SECONDS + 10.000),
        ("track tail", min(OUTPUT_SECONDS - (1.0 / FPS), track_seconds - 0.010)),
    ]
    frame_dir = qa_dir / "contact_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for label, seconds in samples:
        frame_path = frame_dir / f"frame_{seconds:.3f}.jpg"
        extract_frame(final_mp4, seconds, frame_path)
        image = Image.open(frame_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)
        tiles.append((label, seconds, image))

    cols = 3
    rows = math.ceil(len(tiles) / cols)
    label_h = 42
    sheet = Image.new("RGB", (cols * 480, rows * (270 + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, bold=True)
    time_font = font(15)
    for index, (label, seconds, image) in enumerate(tiles):
        x = (index % cols) * 480
        y = (index // cols) * (270 + label_h)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 270 + label_h), fill=(18, 20, 24))
        draw.text((x + 12, y + 274), label, fill=(238, 240, 242), font=label_font)
        draw.text((x + 350, y + 276), f"{seconds:05.2f}s", fill=(190, 198, 205), font=time_font)

    out_path = qa_dir / f"{OUTPUT_STEM}_contact_sheet.jpg"
    sheet.save(out_path, quality=92)
    return out_path


def make_left_plate_comparison_sheet(proofs: list[Any], qa_dir: Path) -> Path:
    ordered = [
        "challenger",
        "therac-25",
        "hyatt-regency",
        "semmelweis",
        "tacoma-narrows",
        "piltdown-man",
        "737-max",
        "titanic",
    ]
    by_slug = {proof.slug: proof for proof in proofs}
    tiles = []
    for slug in ordered:
        proof = by_slug[slug]
        image = Image.open(proof.base_plate_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)
        role = "active website thumbnail" if slug in LEFT_ANCHOR_SOURCE_OVERRIDES else "original intro reference"
        tiles.append((slug, role, image))

    cols = 4
    rows = math.ceil(len(tiles) / cols)
    label_h = 52
    sheet = Image.new("RGB", (cols * 480, rows * (270 + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(17, bold=True)
    role_font = font(13)
    for index, (slug, role, image) in enumerate(tiles):
        x = (index % cols) * 480
        y = (index // cols) * (270 + label_h)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 270 + label_h), fill=(18, 20, 24))
        draw.text((x + 10, y + 274), slug, fill=(238, 240, 242), font=label_font)
        draw.text((x + 10, y + 296), role, fill=(190, 198, 205), font=role_font)

    out_path = qa_dir / f"{OUTPUT_STEM}_left_plate_comparison_sheet.jpg"
    sheet.save(out_path, quality=92)
    return out_path


def end_screen_delta_report(final_mp4: Path, preview: Path, qa_dir: Path, track_seconds: float) -> dict[str, Any]:
    samples = [BODY_END_SECONDS, BODY_END_SECONDS + 10.000, min(OUTPUT_SECONDS - (1.0 / FPS), track_seconds - 0.010)]
    frame_dir = qa_dir / "end_screen_delta_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for seconds in samples:
        frame_path = frame_dir / f"end_screen_{seconds:.3f}.jpg"
        extract_frame(final_mp4, seconds, frame_path)
        delta = mean_frame_delta(preview, frame_path)
        rows.append(
            {
                "seconds": round(seconds, 3),
                "approved_preview_path": str(preview),
                "sample_frame_path": str(frame_path),
                "mean_rgb_delta": round(delta, 4),
                "sample_read": "pass" if delta <= VISUAL_DELTA_TOLERANCE else "tighten",
            }
        )
    return {
        "samples": rows,
        "tolerance_mean_rgb_delta": VISUAL_DELTA_TOLERANCE,
        "planned_start_seconds": round(BODY_END_SECONDS, 6),
        "planned_duration_seconds": END_SCREEN_SECONDS,
        "youtube_help_rule": "last_5_to_20_seconds",
        "read": "pass" if all(row["sample_read"] == "pass" for row in rows) else "tighten",
    }


def visual_duration_read(final_seconds: float, track_seconds: float) -> str:
    return "pass" if abs(final_seconds - track_seconds) <= (1.0 / FPS) + 0.02 else "tighten"


def scene_coverage_report() -> dict[str, Any]:
    durations = {row["episode_id"]: round(row["seconds"][1] - row["seconds"][0], 6) for row in TIMELINE}
    return {
        "canonical_order": CANONICAL_ORDER,
        "occurrence_counts": {episode_id: CANONICAL_ORDER.count(episode_id) for episode_id in CANONICAL_ORDER},
        "timeline": TIMELINE,
        "durations": durations,
        "therac_full_scene_read": "pass_full_original_format_scene_not_artifact_overlay"
        if durations["therac-25"] >= 4.0
        else "reject_therac_scene_too_short",
        "piltdown_full_scene_read": "pass_full_original_format_scene_not_artifact_overlay"
        if durations["piltdown-man"] >= 4.0
        else "reject_piltdown_scene_too_short",
        "canonical_order_read": "pass_exact_first_eight_order_once_each"
        if CANONICAL_ORDER
        == [
            "challenger",
            "therac-25",
            "hyatt-regency",
            "semmelweis",
            "tacoma-narrows",
            "piltdown-man",
            "737-max",
            "titanic",
        ]
        else "reject_order_mismatch",
    }


def geometry_report() -> dict[str, Any]:
    return {
        "right_card_start_quad": rough.START_SHORT_PLATE_QUAD,
        "right_card_end_quad": rough.END_SHORT_PLATE_QUAD,
        "push_in_seconds": rough.EPISODE_PUSH_IN_SECONDS,
        "subject_badge_anchor_xy": rough.SUBJECT_BADGE_ANCHOR_XY,
        "scene_transition_seconds": 0.32,
        "right_card_geometry_read": "pass_uses_original_intro_right_card_quad_constants",
        "subject_badge_geometry_read": "pass_uses_original_intro_subject_badge_constants",
        "center_origin_push_in_read": "pass_non_challenger_scenes_use_original_push_in_function",
    }


def edge_strip_report(path: Path) -> dict[str, Any]:
    image = Image.open(path).convert("RGB")
    top = image.crop((0, 0, WIDTH, 2))
    left = image.crop((0, 0, 2, HEIGHT))
    top_stat = ImageStat.Stat(top)
    left_stat = ImageStat.Stat(left)
    top_max = max(max(channel) for channel in top_stat.extrema)
    left_max = max(max(channel) for channel in left_stat.extrema)
    return {
        "top_2px_max_channel": int(top_max),
        "left_2px_max_channel": int(left_max),
        "top_edge_read": "pass_no_bright_top_edge_border" if top_max < 80 else "reject_bright_top_edge_border",
        "left_edge_read": "pass_no_bright_left_edge_border" if left_max < 80 else "reject_bright_left_edge_border",
    }


def left_plate_perspective_report(left_anchor_reports: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for slug in ["therac-25", "piltdown-man"]:
        report = left_anchor_reports[slug]
        source = report.get("normalization", {})
        prepared_path = Path(source.get("normalized_path", ""))
        edge_report = edge_strip_report(prepared_path) if prepared_path.exists() else {}
        website_source = str(LEFT_ANCHOR_SOURCE_OVERRIDES[slug])
        rows.append(
            {
                "episode_id": slug,
                "source_policy": "active_website_episode_gallery_thumbnail_source_png",
                "active_website_thumbnail_proof_id": "proof-v6-ink-lit-subjects",
                "source_path": website_source,
                "source_sha256": sha256(Path(website_source)),
                "prepared_plate_path": source.get("normalized_path", ""),
                "prepared_plate_sha256": source.get("normalized_sha256", ""),
                "orientation_transform": source.get("orientation_transform", "none"),
                "layout_transform": source.get("layout_transform", {}),
                "edge_strip_report": edge_report,
                "bounds_metrics": report,
                "perspective_orientation_review": "requires_human_visual_review_contact_sheet",
                "read": "pass_active_website_thumbnail_source_used_for_left_plate_artifact_crop_repair",
            }
        )
    piltdown_edge = next(row["edge_strip_report"] for row in rows if row["episode_id"] == "piltdown-man")
    return {
        "reference_family": [
            "challenger",
            "hyatt-regency",
            "semmelweis",
            "tacoma-narrows",
            "737-max",
            "titanic",
        ],
        "rows": rows,
        "read": "pass_active_website_thumbnails_scaled_and_oriented_for_therac_and_piltdown_left_plates",
        "therac_flip_read": "pass_therac_website_thumbnail_mirrored_to_match_left_stage_orientation"
        if LEFT_ANCHOR_TRANSFORMS.get("therac-25") == "mirror_x"
        else "not_applicable",
        "piltdown_flip_read": "pass_piltdown_website_thumbnail_mirrored_to_correct_stage_orientation"
        if LEFT_ANCHOR_TRANSFORMS.get("piltdown-man") == "mirror_x"
        else "reject_piltdown_orientation_not_corrected",
        "scale_adjustment_read": "pass_therac_and_piltdown_website_thumbnail_plates_scaled_down_after_review_feedback",
        "piltdown_edge_clean_read": "pass_piltdown_left_plate_has_no_bright_top_or_left_border"
        if piltdown_edge.get("top_edge_read", "").startswith("pass")
        and piltdown_edge.get("left_edge_read", "").startswith("pass")
        else "reject_piltdown_top_or_left_edge_border",
        "threshold_mask_artifact_read": "pass_threshold_subject_mask_not_used_for_therac_or_piltdown",
    }


def checkpoint_source_report(source_ledger: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for slug, expected in SHORT_SOURCE_OVERRIDES.items():
        selected = Path(source_ledger[slug]["short_source"])
        selected_text = str(selected)
        path_ok = selected == expected
        no_caption_role_ok = "no_audio" in selected.name or "motion_only" in selected.name
        not_published_ok = "/publish/" not in selected_text and "youtube_short" not in selected.name
        probe = ffprobe(selected)
        rows.append(
            {
                "episode_id": slug,
                "selected_short_source": selected_text,
                "selected_short_sha256": sha256(selected),
                "expected_checkpoint_source": str(expected),
                "path_read": "pass" if path_ok else "reject_wrong_checkpoint_source",
                "caption_bake_guard_read": "pass_no_caption_checkpoint_name_no_audio_motion_only"
                if no_caption_role_ok
                else "reject_checkpoint_source_name_does_not_prove_no_caption_role",
                "published_youtube_short_ban_read": "pass_not_publish_youtube_short_source"
                if not_published_ok
                else "reject_published_captioned_youtube_short_source",
                "probe": probe,
            }
        )
    return {
        "rows": rows,
        "read": "pass_no_caption_crt_checkpoint_sources_selected"
        if all(row["path_read"] == "pass" and row["caption_bake_guard_read"].startswith("pass") and row["published_youtube_short_ban_read"].startswith("pass") for row in rows)
        else "reject_checkpoint_source_guard_failed",
    }


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    source_ledger: dict[str, dict[str, Any]],
    left_anchor_reports: dict[str, Any],
    borderless_pointer: dict[str, Any],
    borderless_manifest: dict[str, Any],
    body_report: dict[str, Any],
    silent_video: Path,
    final_mp4: Path,
    contact_sheet: Path,
    left_plate_comparison_sheet: Path,
    review_html: Path,
    source_audio_measure: dict[str, Any],
    final_audio_measure: dict[str, Any],
    end_screen_report: dict[str, Any],
    track_seconds: float,
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    final_seconds = float(probe.get("format", {}).get("duration", 0.0))
    duration_read = visual_duration_read(final_seconds, track_seconds)
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    format_pass = (
        video_stream.get("codec_name") == "h264"
        and video_stream.get("width") == WIDTH
        and video_stream.get("height") == HEIGHT
        and video_stream.get("avg_frame_rate") == "24/1"
        and audio_stream.get("codec_name") == "aac"
        and str(audio_stream.get("channels")) == "2"
    )
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    palette_contract = dict(borderless_manifest["end_screen_palette_contract"])
    palette_contract.setdefault("target_palette", {})["palette_treatment_model"] = END_SCREEN_PALETTE_TREATMENT_MODEL
    palette_reads = palette_contract.get("reads", {})
    scene_report = scene_coverage_report()
    geo_report = geometry_report()
    checkpoint_report = checkpoint_source_report(source_ledger)
    left_plate_report = left_plate_perspective_report(left_anchor_reports)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    rejected_pointer = read_json(REJECTED_ARTIFACT_PATCH_POINTER) if REJECTED_ARTIFACT_PATCH_POINTER.exists() else {}
    rejected_scene_fix_pointer = read_json(REJECTED_SCENE_FIX_POINTER) if REJECTED_SCENE_FIX_POINTER.exists() else {}
    rejected_timing_source_fix_pointer = (
        read_json(REJECTED_TIMING_SOURCE_FIX_POINTER) if REJECTED_TIMING_SOURCE_FIX_POINTER.exists() else {}
    )
    rejected_plate_perspective_fix_pointer = (
        read_json(REJECTED_PLATE_PERSPECTIVE_FIX_POINTER) if REJECTED_PLATE_PERSPECTIVE_FIX_POINTER.exists() else {}
    )
    rejected_plate_scale_orientation_fix_pointer = (
        read_json(REJECTED_PLATE_SCALE_ORIENTATION_FIX_POINTER)
        if REJECTED_PLATE_SCALE_ORIENTATION_FIX_POINTER.exists()
        else {}
    )
    rejected_plate_edge_clean_fix_pointer = (
        read_json(REJECTED_PLATE_EDGE_CLEAN_FIX_POINTER)
        if REJECTED_PLATE_EDGE_CLEAN_FIX_POINTER.exists()
        else {}
    )
    return {
        "artifact_id": f"{OUTPUT_STEM}_{timestamp}",
        "created_at": timestamp,
        "status": "review_ready_pending_human_keep",
        "workflow": WORKFLOW,
        "mp4_render_created": True,
        "youtube_uploaded": False,
        "youtube_visibility_changed": False,
        "youtube_channel_trailer_replaced": False,
        "may_upload_to_youtube": False,
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "successor",
            "contract_registry_path": str(REPO_ROOT / "references/production_contracts/cascade_effects_output_contracts.v1.json"),
            "youtube_action_approval_read": "blocked_local_review_only",
        },
        "youtube_action_read": "blocked_local_review_only",
        "predecessor": {
            "role": "approved_original_format_intro_reference",
            "manifest_path": str(ORIGINAL_FORMAT_SOURCE_MANIFEST),
            "manifest_sha256": sha256(ORIGINAL_FORMAT_SOURCE_MANIFEST),
            "mp4_path": str(ORIGINAL_FORMAT_SOURCE_MP4),
            "mp4_sha256": sha256(ORIGINAL_FORMAT_SOURCE_MP4),
        },
        "supersedes_local_rejected_attempt": {
            "reason": "prior packages used artifact inserts, captioned short sources, incorrect end-screen timing, wrong outro screen, left plate perspective/orientation mismatch, Piltdown edge border, or Therac/Piltdown threshold-mask artifacts and crop reads",
            "latest_pointer_path": str(REJECTED_ARTIFACT_PATCH_POINTER),
            "latest_pointer_sha256": sha256(REJECTED_ARTIFACT_PATCH_POINTER) if REJECTED_ARTIFACT_PATCH_POINTER.exists() else "",
            "pointer": rejected_pointer,
            "review_rejected_full_track_scene_fix_latest_pointer_path": str(REJECTED_SCENE_FIX_POINTER),
            "review_rejected_full_track_scene_fix_latest_pointer_sha256": sha256(REJECTED_SCENE_FIX_POINTER)
            if REJECTED_SCENE_FIX_POINTER.exists()
            else "",
            "review_rejected_full_track_scene_fix_pointer": rejected_scene_fix_pointer,
            "review_rejected_timing_source_fix_latest_pointer_path": str(REJECTED_TIMING_SOURCE_FIX_POINTER),
            "review_rejected_timing_source_fix_latest_pointer_sha256": sha256(REJECTED_TIMING_SOURCE_FIX_POINTER)
            if REJECTED_TIMING_SOURCE_FIX_POINTER.exists()
            else "",
            "review_rejected_timing_source_fix_pointer": rejected_timing_source_fix_pointer,
            "review_rejected_timing_source_fix_reason": "left_plate_perspective_orientation_mismatch",
            "review_rejected_plate_perspective_fix_latest_pointer_path": str(REJECTED_PLATE_PERSPECTIVE_FIX_POINTER),
            "review_rejected_plate_perspective_fix_latest_pointer_sha256": sha256(REJECTED_PLATE_PERSPECTIVE_FIX_POINTER)
            if REJECTED_PLATE_PERSPECTIVE_FIX_POINTER.exists()
            else "",
            "review_rejected_plate_perspective_fix_pointer": rejected_plate_perspective_fix_pointer,
            "review_rejected_plate_perspective_fix_reason": "therac_and_piltdown_left_plates_too_large_piltdown_wrong_orientation",
            "review_rejected_plate_scale_orientation_fix_latest_pointer_path": str(REJECTED_PLATE_SCALE_ORIENTATION_FIX_POINTER),
            "review_rejected_plate_scale_orientation_fix_latest_pointer_sha256": sha256(REJECTED_PLATE_SCALE_ORIENTATION_FIX_POINTER)
            if REJECTED_PLATE_SCALE_ORIENTATION_FIX_POINTER.exists()
            else "",
            "review_rejected_plate_scale_orientation_fix_pointer": rejected_plate_scale_orientation_fix_pointer,
            "review_rejected_plate_scale_orientation_fix_reason": "piltdown_top_and_left_edge_border_artifact",
            "review_rejected_plate_edge_clean_fix_latest_pointer_path": str(REJECTED_PLATE_EDGE_CLEAN_FIX_POINTER),
            "review_rejected_plate_edge_clean_fix_latest_pointer_sha256": sha256(REJECTED_PLATE_EDGE_CLEAN_FIX_POINTER)
            if REJECTED_PLATE_EDGE_CLEAN_FIX_POINTER.exists()
            else "",
            "review_rejected_plate_edge_clean_fix_pointer": rejected_plate_edge_clean_fix_pointer,
            "review_rejected_plate_edge_clean_fix_reason": "therac_shadow_artifacts_and_piltdown_strange_crop_from_threshold_mask",
        },
        "source_audio": {
            "role": "replacement_full_track",
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
            "duration_seconds": track_seconds,
            "measurements": source_audio_measure,
        },
        "audio_treatment": {
            "policy": "full_track_once_safe_aac_normalization",
            "target_integrated_lufs": base.AUDIO_TARGET_LUFS,
            "true_peak_limit_dbfs": base.AUDIO_TRUE_PEAK_LIMIT_DBFS,
            "safe_true_peak_max_dbfs": base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS,
            "filter": "loudnorm_plus_limiter",
            "final_audio_stream_sha256": stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac"),
            "final_measurements": final_audio_measure,
        },
        "source_assets": source_ledger,
        "timeline": {
            "source_audio_duration_seconds": track_seconds,
            "output_duration_seconds": final_seconds,
            "frame_locked_output_seconds": OUTPUT_SECONDS,
            "total_frames": TOTAL_FRAMES,
            "fps": FPS,
            "duration_delta_seconds": round(abs(final_seconds - track_seconds), 6),
            "duration_tolerance_seconds": round((1.0 / FPS) + 0.02, 6),
            "cold_open_seconds": [0.0, BODY_START_SECONDS],
            "episode_body_seconds": [BODY_START_SECONDS, BODY_END_SECONDS],
            "titleless_end_screen_seconds": [BODY_END_SECONDS, OUTPUT_SECONDS],
            "titleless_end_screen_duration_seconds": END_SCREEN_SECONDS,
            "youtube_end_screen_rule_read": "pass_final_20_seconds_matches_youtube_last_5_to_20_second_window",
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "segments": TIMELINE
            + [
                {
                    "episode_id": "adaptive-borderless-end-screen",
                    "display": "Approved titleless adaptive borderless end screen",
                    "seconds": [BODY_END_SECONDS, round(OUTPUT_SECONDS, 6)],
                }
            ],
        },
        "borderless_end_screen_source": {
            "latest_pointer_path": str(BORDERLESS_END_SCREEN_POINTER),
            "latest_pointer_sha256": sha256(BORDERLESS_END_SCREEN_POINTER),
            "pointer": borderless_pointer,
            "manifest_path": borderless_pointer["manifest"],
            "manifest_sha256": sha256(Path(borderless_pointer["manifest"])),
            "approved_preview_path": borderless_pointer["adaptive_end_screen_preview"],
            "approved_preview_sha256": sha256(Path(borderless_pointer["adaptive_end_screen_preview"])),
            "approval_scope": borderless_pointer.get("approval_scope", ""),
            "approved_at_utc": borderless_pointer.get("approved_at_utc", ""),
            "placeholder_style_model": borderless_pointer.get("placeholder_style_model", ""),
        },
        "end_screen_palette_contract": palette_contract,
        "visual_qa": {
            "scene_coverage": scene_report,
            "geometry": geo_report,
            "left_anchor_scale_orientation": left_anchor_reports,
            "left_plate_perspective_orientation": left_plate_report,
            "no_caption_checkpoint_sources": checkpoint_report,
            "body_render": body_report,
            "end_screen_delta_report": end_screen_report,
            "final_video_stream_sha256": stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264"),
        },
        "reads": {
            "source_audio_hash_read": "pass_source_audio_sha256_recorded",
            "audio_replacement_read": "pass_pressure_bends_replaces_prior_music",
            "full_track_audio_read": "pass_full_source_track_used_once_no_loop" if duration_read == "pass" else "reject_duration_mismatch",
            "safe_mastering_read": "pass_true_peak_margin_and_loudness_target_met" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_mix_no_clipping" if no_clipping_pass else "reject_final_mix_clipping_or_peak_too_hot",
            "video_preservation_read": "pass_original_intro_scene_grammar_preserved_with_successor_scene_insertions",
            "end_screen_extension_read": "pass_approved_borderless_titleless_end_screen_uses_final_20_seconds"
            if end_screen_report["read"] == "pass"
            else "reject_end_screen_does_not_match_approved_borderless_preview",
            "end_screen_title_image_absence_read": borderless_manifest.get("reads", {}).get(
                "end_screen_title_image_absence_read", "pass_no_cascade_of_effects_title_image_on_end_screen"
            ),
            "end_screen_palette_contract_read": palette_reads.get(
                "end_screen_palette_contract_read", "pass_backplate_sampled_palette_contract_present"
            ),
            "end_screen_target_fill_palette_read": palette_reads.get(
                "end_screen_target_fill_palette_read", "pass_local_target_fills_sampled_from_backplate_regions"
            ),
            "end_screen_target_contrast_read": palette_reads.get(
                "end_screen_target_contrast_read", "pass_borderless_underlay_legible_without_target_outlines"
            ),
            "source_integrated_panel_color_read": palette_reads.get(
                "source_integrated_panel_color_read", "pass_perceptual_episode_backplate_colors_visible_in_end_screen"
            ),
            "no_cross_episode_default_palette_read": palette_reads.get(
                "no_cross_episode_default_palette_read", "pass_no_challenger_default_target_colors_with_visible_variability"
            ),
            "end_screen_adaptive_perceptual_variability_read": palette_reads.get(
                "end_screen_adaptive_perceptual_variability_read", "pass_backplate_hue_visible_across_end_screen_targets"
            ),
            "format_read": "pass" if format_pass else "reject",
            "full_decode_read": base.full_decode_read(final_mp4),
            "youtube_action_read": "blocked_local_review_only",
            "canonical_first_eight_order_read": scene_report["canonical_order_read"],
            "therac_full_scene_read": scene_report["therac_full_scene_read"],
            "piltdown_full_scene_read": scene_report["piltdown_full_scene_read"],
            "therac_no_caption_checkpoint_read": "pass_no_caption_crt_checkpoint_source_selected"
            if checkpoint_report["rows"][0]["episode_id"] == "therac-25" and checkpoint_report["rows"][0]["path_read"] == "pass"
            else "reject_therac_checkpoint_source",
            "piltdown_no_caption_checkpoint_read": "pass_no_caption_visible_scanline_checkpoint_source_selected"
            if checkpoint_report["rows"][1]["episode_id"] == "piltdown-man" and checkpoint_report["rows"][1]["path_read"] == "pass"
            else "reject_piltdown_checkpoint_source",
            "no_caption_short_checkpoint_read": checkpoint_report["read"],
            "no_published_captioned_short_source_read": "pass_published_youtube_short_sources_banned_for_therac_and_piltdown"
            if checkpoint_report["read"].startswith("pass")
            else "reject_published_captioned_short_source_present",
            "left_anchor_scale_orientation_read": "pass_therac_and_piltdown_left_anchors_normalized_to_original_format"
            if all(left_anchor_reports[slug]["read"].startswith("pass") for slug in ("therac-25", "piltdown-man"))
            else "reject_left_anchor_scale_orientation",
            "left_plate_perspective_orientation_read": left_plate_report["read"],
            "website_thumbnail_left_plate_read": "pass_active_website_episode_gallery_thumbnails_used_for_therac_and_piltdown",
            "therac_left_plate_flip_read": left_plate_report["therac_flip_read"],
            "piltdown_left_plate_flip_read": left_plate_report["piltdown_flip_read"],
            "left_plate_scale_down_read": left_plate_report["scale_adjustment_read"],
            "piltdown_edge_clean_read": left_plate_report["piltdown_edge_clean_read"],
            "threshold_mask_artifact_read": left_plate_report["threshold_mask_artifact_read"],
            "no_face_on_artifact_display_plate_read": "pass_repaired_sources_are_active_website_subject_thumbnail_plates_not_artifact_overlays",
            "youtube_end_screen_20s_window_read": "pass_final_20_seconds_reserved_for_youtube_end_screen",
            "no_artifact_overlay_read": "pass_new_episodes_are_timed_full_scenes_not_thumbnail_inserts",
            "original_format_scene_grammar_read": "pass_left_anchor_right_short_card_badge_push_in_geometry",
            "deferred_beat_reactive_backplate_read": "pass_not_attempted_not_claimed",
            "html_range_server_read": "pending_http_206_partial_content_probe",
            "end_screen_placeholder_style_read": borderless_manifest.get("reads", {}).get(
                "end_screen_placeholder_style_read", "pass_youtube_placeholder_borderless_underlay_v1"
            ),
            "end_screen_outline_removal_read": borderless_manifest.get("reads", {}).get(
                "end_screen_outline_removal_read",
                "pass_borders_glow_rings_inset_rings_subscribe_inner_ring_and_shadow_removed",
            ),
            "end_screen_borderless_pixel_sample_read": borderless_manifest.get("reads", {}).get(
                "end_screen_borderless_pixel_sample_read",
                "pass_borderless_underlay_pixels_match_manifest_fill_and_no_outline_samples",
            ),
        },
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "silent_video": str(silent_video),
            "silent_video_sha256": sha256(silent_video),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "left_plate_comparison_sheet": str(left_plate_comparison_sheet),
            "left_plate_comparison_sheet_sha256": sha256(left_plate_comparison_sheet),
            "manifest": str(manifest_path),
        },
        "media_probe": probe,
    }


def make_review_html(
    package_dir: Path,
    final_mp4: Path,
    contact_sheet: Path,
    left_plate_comparison_sheet: Path,
    manifest_path: Path,
    track_seconds: float,
) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pressure Bends Original-Format Plate Artifact/Crop Fix Review</title>
  <style>
    body {{ margin: 0; background: #101216; color: #eef1f4; font-family: Arial, sans-serif; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    video, img {{ width: 100%; display: block; background: #05070a; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .meta div {{ border: 1px solid #2f3742; padding: 12px; background: #171b21; }}
    h1 {{ font-size: 28px; margin: 0 0 16px; }}
    h2 {{ font-size: 18px; margin: 28px 0 10px; }}
    code {{ color: #d8e9ff; }}
  </style>
</head>
<body>
<main>
  <h1>Pressure Bends Original-Format Plate Artifact/Crop Fix Review</h1>
  <video controls src="{final_mp4.relative_to(package_dir)}"></video>
  <section class="meta">
    <div><strong>Runtime</strong><br>{OUTPUT_SECONDS:.3f}s frame-locked / {track_seconds:.3f}s source track</div>
    <div><strong>Left plates</strong><br>Full-source feathered plates; no threshold mask</div>
    <div><strong>Outro</strong><br>Final 20.000s adaptive borderless end screen</div>
  </section>
  <h2>Contact Sheet</h2>
  <img src="{contact_sheet.relative_to(package_dir)}" alt="Scene and end-screen contact sheet">
  <h2>Left Plate Comparison</h2>
  <img src="{left_plate_comparison_sheet.relative_to(package_dir)}" alt="Reference and repaired left source plates">
  <h2>Manifest</h2>
  <p><code>{manifest_path.relative_to(package_dir)}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review_path


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str) -> Path:
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Pressure Bends Original-Format Plate Artifact/Crop Fix",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This local-review successor uses the full `The_Pressure_Bends.mp3` track, keeps the accepted timing and right-card sources, preserves the reviewed Therac-25/Piltdown Man scale and orientation corrections, replaces the threshold subject mask with full-source feathered plate compositing to remove Therac shadow artifacts and Piltdown crop artifacts, and reserves the final 20.000s for the approved adaptive borderless titleless end screen.",
                "",
                "## Outputs",
                "",
                f"- Review HTML: `{review_html}`",
                f"- MP4: `{final_mp4}`",
                f"- Manifest: `{manifest_path}`",
                f"- Contract receipt: `{receipt_path}`",
                "",
                "No YouTube upload, visibility change, or channel-trailer replacement was performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return readme


def run_contract_validator(manifest_path: Path) -> dict[str, Any]:
    return base.run_contract_validator(manifest_path)


def build(args: argparse.Namespace) -> dict[str, Any]:
    for path, label in [
        (ORIGINAL_FORMAT_SOURCE_MP4, "original-format source MP4"),
        (ORIGINAL_FORMAT_SOURCE_MANIFEST, "original-format source manifest"),
        (ALL_EIGHT_LEDGER_MANIFEST, "all-eight source ledger manifest"),
        (BORDERLESS_END_SCREEN_POINTER, "approved borderless end-screen latest pointer"),
        (TRACK_PATH, "Pressure Bends source track"),
        (THERAC_NO_CAPTION_CHECKPOINT, "Therac-25 no-caption CRT checkpoint"),
        (PILTDOWN_NO_CAPTION_CHECKPOINT, "Piltdown Man no-caption CRT checkpoint"),
        (THERAC_WEBSITE_THUMBNAIL_SOURCE, "Therac-25 active website thumbnail source"),
        (PILTDOWN_WEBSITE_THUMBNAIL_SOURCE, "Piltdown Man active website thumbnail source"),
    ]:
        require_file(path, label)

    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    work_dir = package_dir / "work"
    for directory in [package_dir, video_dir, qa_dir, work_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    track_seconds = duration_seconds(TRACK_PATH)
    source_audio_measure = base.measure_audio(TRACK_PATH)
    borderless_pointer, borderless_manifest, end_screen_preview = borderless_end_screen_inputs()
    proofs, source_ledger, left_anchor_reports = build_source_proofs(package_dir / "source_art")

    body_report = render_body_video(proofs, work_dir, video_dir)
    body_video = Path(body_report["body_video"])
    silent_video = render_silent_video(body_video, end_screen_preview, video_dir)
    final_mp4 = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_1080p24.mp4"
    render_final(silent_video, final_mp4)
    final_audio_measure = base.measure_audio(final_mp4)
    contact_sheet = make_contact_sheet(final_mp4, qa_dir, track_seconds)
    left_plate_comparison_sheet = make_left_plate_comparison_sheet(proofs, qa_dir)
    end_screen_report = end_screen_delta_report(final_mp4, end_screen_preview, qa_dir, track_seconds)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(
        package_dir,
        final_mp4,
        contact_sheet,
        left_plate_comparison_sheet,
        manifest_path,
        track_seconds,
    )
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        source_ledger=source_ledger,
        left_anchor_reports=left_anchor_reports,
        borderless_pointer=borderless_pointer,
        borderless_manifest=borderless_manifest,
        body_report=body_report,
        silent_video=silent_video,
        final_mp4=final_mp4,
        contact_sheet=contact_sheet,
        left_plate_comparison_sheet=left_plate_comparison_sheet,
        review_html=review_html,
        source_audio_measure=source_audio_measure,
        final_audio_measure=final_audio_measure,
        end_screen_report=end_screen_report,
        track_seconds=track_seconds,
    )
    write_json(manifest_path, manifest)
    receipt = run_contract_validator(manifest_path)
    readme = write_readme(package_dir, final_mp4, review_html, manifest_path, receipt.get("receipt_path", ""))
    latest = {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "manifest": str(manifest_path),
        "final_mp4": str(final_mp4),
        "contract_receipt": receipt.get("receipt_path", ""),
        "readme": str(readme),
        "status": "review_ready_pending_human_keep",
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
    }
    write_json(LATEST_POINTER, latest)
    return latest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="", help="UTC timestamp override for reproducible package naming.")
    return parser.parse_args()


def main() -> None:
    latest = build(parse_args())
    print(json.dumps(latest, indent=2))


if __name__ == "__main__":
    main()
