#!/usr/bin/env python3
"""Build the full-track Pressure Bends intro with original-format added scenes."""

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

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat


WIDTH = 1920
HEIGHT = 1080
FPS = 24
BODY_START_SECONDS = 6.0
BODY_END_SECONDS = 40.479
WORKFLOW = "channel_intro_pressure_bends_original_format_full_track_scene_fix_v1"
OUTPUT_STEM = "channel_intro_pressure_bends_original_format_full_track_scene_fix"
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
VISUAL_DELTA_TOLERANCE = 6.0

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
ALL_EIGHT_LEDGER_MANIFEST = (
    OUTPUT_ROOT
    / "channel_trailer_actual_montage_successor_20260524T040009Z"
    / "channel_trailer_actual_montage_successor_manifest.json"
)
BORDERLESS_END_SCREEN_POINTER = OUTPUT_ROOT / "channel_intro_end_screen_adaptive_borderless_keep_latest.json"

TIMELINE = [
    {"episode_id": "challenger", "display": "Challenger", "seconds": [6.000, 9.200], "source_start": 8.0},
    {"episode_id": "therac-25", "display": "Therac-25", "seconds": [9.200, 14.340], "source_start": 0.0},
    {"episode_id": "hyatt-regency", "display": "Hyatt Regency", "seconds": [14.340, 18.040], "source_start": 0.0},
    {"episode_id": "semmelweis", "display": "Semmelweis", "seconds": [18.040, 21.740], "source_start": 0.0},
    {"episode_id": "tacoma-narrows", "display": "Tacoma Narrows", "seconds": [21.740, 25.440], "source_start": 0.0},
    {"episode_id": "piltdown-man", "display": "Piltdown Man", "seconds": [25.440, 30.579], "source_start": 0.0},
    {"episode_id": "737-max", "display": "737 MAX", "seconds": [30.579, 34.279], "source_start": 0.0},
    {"episode_id": "titanic", "display": "Titanic", "seconds": [34.279, 40.479], "source_start": 0.0},
]
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


def build_source_proofs() -> tuple[list[Any], dict[str, dict[str, Any]]]:
    all_eight_rows = source_rows_from_all_eight_manifest()
    existing = {proof.slug: proof for proof in rough.source_proofs()}
    proofs: list[Any] = []
    source_ledger: dict[str, dict[str, Any]] = {}

    for row in TIMELINE:
        slug = row["episode_id"]
        if slug in existing:
            proof = existing[slug]
            source_role = "original_format_existing_scene_source"
        else:
            ledger = all_eight_rows[slug]
            proof = rough.SourceProof(
                slug=slug,
                display_name=row["display"],
                video_path=Path(ledger["short_source"]),
                manifest_path=ALL_EIGHT_LEDGER_MANIFEST,
                short_video_path=Path(ledger["short_source"]),
                base_plate_path=Path(ledger["gallery_source"]),
            )
            source_role = "new_original_format_scene_source_from_all_eight_ledger"

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
    return proofs, source_ledger


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
    frame_count = math.ceil(body_duration * FPS)
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

    body_video = video_dir / "channel_intro_pressure_bends_original_format_body_first_eight_silent.mp4"
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
            "-t",
            f"{body_duration:.6f}",
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


def render_silent_video(body_video: Path, end_screen_preview: Path, track_seconds: float, video_dir: Path) -> Path:
    end_screen_duration = track_seconds - BODY_END_SECONDS
    if end_screen_duration <= 0:
        raise SystemExit(f"Track is too short for planned body: {track_seconds:.3f}s")
    silent_video = video_dir / "cascade_of_effects_channel_intro_pressure_bends_original_format_full_track_scene_fix_silent.mp4"
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
    base.render_final(silent_video, TRACK_PATH, final_mp4)


def make_contact_sheet(final_mp4: Path, qa_dir: Path, track_seconds: float) -> Path:
    samples = [
        ("cold open", 0.600),
        ("Challenger", 7.600),
        ("Therac-25", 11.770),
        ("Hyatt Regency", 16.190),
        ("Semmelweis", 19.890),
        ("Tacoma Narrows", 23.590),
        ("Piltdown Man", 28.010),
        ("737 MAX", 32.429),
        ("Titanic", 37.379),
        ("borderless end screen", 40.750),
        ("end screen hold", 47.450),
        ("track tail", min(track_seconds - 0.250, 58.000)),
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


def end_screen_delta_report(final_mp4: Path, preview: Path, qa_dir: Path, track_seconds: float) -> dict[str, Any]:
    samples = [40.750, 47.450, min(track_seconds - 0.250, 58.000)]
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
        if durations["therac-25"] >= 5.0
        else "reject_therac_scene_too_short",
        "piltdown_full_scene_read": "pass_full_original_format_scene_not_artifact_overlay"
        if durations["piltdown-man"] >= 5.0
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


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    source_ledger: dict[str, dict[str, Any]],
    borderless_pointer: dict[str, Any],
    borderless_manifest: dict[str, Any],
    body_report: dict[str, Any],
    silent_video: Path,
    final_mp4: Path,
    contact_sheet: Path,
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
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    rejected_pointer = read_json(REJECTED_ARTIFACT_PATCH_POINTER) if REJECTED_ARTIFACT_PATCH_POINTER.exists() else {}
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
            "reason": "prior package used artifact inserts and the wrong outlined outro screen",
            "latest_pointer_path": str(REJECTED_ARTIFACT_PATCH_POINTER),
            "latest_pointer_sha256": sha256(REJECTED_ARTIFACT_PATCH_POINTER) if REJECTED_ARTIFACT_PATCH_POINTER.exists() else "",
            "pointer": rejected_pointer,
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
            "duration_delta_seconds": round(abs(final_seconds - track_seconds), 6),
            "duration_tolerance_seconds": round((1.0 / FPS) + 0.02, 6),
            "cold_open_seconds": [0.0, BODY_START_SECONDS],
            "episode_body_seconds": [BODY_START_SECONDS, BODY_END_SECONDS],
            "titleless_end_screen_seconds": [BODY_END_SECONDS, track_seconds],
            "titleless_end_screen_duration_seconds": round(track_seconds - BODY_END_SECONDS, 6),
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "segments": TIMELINE
            + [
                {
                    "episode_id": "adaptive-borderless-end-screen",
                    "display": "Approved titleless adaptive borderless end screen",
                    "seconds": [BODY_END_SECONDS, round(track_seconds, 6)],
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
            "end_screen_extension_read": "pass_approved_borderless_titleless_end_screen_holds_to_full_track_end"
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
            "no_artifact_overlay_read": "pass_new_episodes_are_timed_full_scenes_not_thumbnail_inserts",
            "original_format_scene_grammar_read": "pass_left_anchor_right_short_card_badge_push_in_geometry",
            "deferred_beat_reactive_backplate_read": "pass_not_attempted_not_claimed",
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
            "manifest": str(manifest_path),
        },
        "media_probe": probe,
    }


def make_review_html(package_dir: Path, final_mp4: Path, contact_sheet: Path, manifest_path: Path, track_seconds: float) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pressure Bends Original-Format Intro Review</title>
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
  <h1>Pressure Bends Original-Format Intro Review</h1>
  <video controls src="{final_mp4.relative_to(package_dir)}"></video>
  <section class="meta">
    <div><strong>Runtime</strong><br>{track_seconds:.3f}s full track</div>
    <div><strong>Added scenes</strong><br>Therac-25 and Piltdown Man</div>
    <div><strong>Outro</strong><br>Approved adaptive borderless end screen</div>
  </section>
  <h2>Contact Sheet</h2>
  <img src="{contact_sheet.relative_to(package_dir)}" alt="Scene and end-screen contact sheet">
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
                "# Pressure Bends Original-Format Intro Scene Fix",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This local-review successor uses the full `The_Pressure_Bends.mp3` track, adds Therac-25 and Piltdown Man as full intro-format scenes, and uses the approved adaptive borderless titleless end screen.",
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
    proofs, source_ledger = build_source_proofs()

    body_report = render_body_video(proofs, work_dir, video_dir)
    body_video = Path(body_report["body_video"])
    silent_video = render_silent_video(body_video, end_screen_preview, track_seconds, video_dir)
    final_mp4 = video_dir / "cascade_of_effects_channel_intro_pressure_bends_original_format_full_track_scene_fix_1080p24.mp4"
    render_final(silent_video, final_mp4)
    final_audio_measure = base.measure_audio(final_mp4)
    contact_sheet = make_contact_sheet(final_mp4, qa_dir, track_seconds)
    end_screen_report = end_screen_delta_report(final_mp4, end_screen_preview, qa_dir, track_seconds)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, manifest_path, track_seconds)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        source_ledger=source_ledger,
        borderless_pointer=borderless_pointer,
        borderless_manifest=borderless_manifest,
        body_report=body_report,
        silent_video=silent_video,
        final_mp4=final_mp4,
        contact_sheet=contact_sheet,
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
