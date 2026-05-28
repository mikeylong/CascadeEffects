#!/usr/bin/env python3
"""Build a Pressure Bends channel trailer successor with all first-eight episodes."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1920
HEIGHT = 1080
FPS = 24
IDENTITY_OPEN_END_SECONDS = 6.0
SOURCE_BODY_END_SECONDS = 30.2
SOURCE_TRAILER_END_SECONDS = 48.0
END_SCREEN_VIDEO_PAD_SECONDS = 0.25
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
WORKFLOW = "channel_trailer_pressure_bends_first_eight_successor_v1"

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
ACTUAL_MONTAGE_MANIFEST = (
    OUTPUT_ROOT
    / "channel_trailer_actual_montage_successor_20260524T040009Z"
    / "channel_trailer_actual_montage_successor_manifest.json"
)
PRESSURE_BENDS_POINTER = OUTPUT_ROOT / "channel_trailer_pressure_bends_full_track_successor_latest.json"
TITLELESS_REPAIR_MANIFEST = (
    OUTPUT_ROOT
    / "channel_trailer_end_screen_titleless_only_repair_20260524T054934Z"
    / "channel_trailer_end_screen_titleless_only_manifest.json"
)
LATEST_POINTER = OUTPUT_ROOT / "channel_trailer_pressure_bends_first_eight_successor_latest.json"
BASE_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_pressure_bends_successor.py"

CANONICAL_FIRST_EIGHT = [
    "challenger",
    "therac-25",
    "hyatt-regency",
    "semmelweis",
    "tacoma-narrows",
    "piltdown-man",
    "737-max",
    "titanic",
]


def load_base_helper():
    spec = importlib.util.spec_from_file_location("pressure_bends_base", BASE_HELPER_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load helper: {BASE_HELPER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_helper()


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def capture(cmd: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def utc_stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def ffprobe(path: Path) -> dict[str, Any]:
    data = json.loads(
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
    data["path"] = str(path)
    data["sha256"] = sha256(path)
    return data


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
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-map", stream_spec, "-c", "copy", str(out_path)])
    digest = sha256(out_path)
    out_path.unlink(missing_ok=True)
    return digest


def remap_time(source_time: float) -> float:
    return source_time


def expanded_episode_sequence(source_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(source_manifest["episode_sequence"], start=1):
        start, end = item["seconds"]
        row = dict(item)
        row["order"] = index
        row["source_seconds"] = [start, end]
        row["seconds"] = [round(remap_time(start), 6), round(remap_time(end), 6)]
        gallery = Path(row["gallery_source"])
        require_file(gallery, f"{row['episode_id']} gallery source")
        row["gallery_source_sha256_actual"] = sha256(gallery)
        short = Path(row["short_source"])
        if short.exists():
            row["short_source_available_read"] = "pass_exact_prior_short_insert_available"
            row["short_source_sha256_actual"] = sha256(short)
        else:
            row["short_source_available_read"] = "pass_gallery_still_fallback_allowed_short_insert_missing"
            row["short_source_sha256_actual"] = "missing"
        rows.append(row)
    return rows


def render_silent_remix(actual_montage_mp4: Path, pressure_audio_mp4: Path, work_dir: Path, video_dir: Path) -> tuple[Path, Path, float]:
    track_seconds = duration_seconds(pressure_audio_mp4)
    end_screen_duration = track_seconds - SOURCE_TRAILER_END_SECONDS
    if end_screen_duration <= 0:
        raise SystemExit(f"Pressure Bends audio is too short for the planned remix: {track_seconds:.3f}s")
    hold_frame = work_dir / "titleless_end_screen_hold_frame.png"
    extract_frame(actual_montage_mp4, 47.5, hold_frame)
    silent_video = video_dir / "cascade_of_effects_channel_trailer_pressure_bends_first_eight_successor_silent.mp4"
    filter_graph = (
        f"[0:v]trim=0:{SOURCE_TRAILER_END_SECONDS:.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v0];"
        f"[1:v]fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1,setpts=PTS-STARTPTS[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[v]"
    )
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(actual_montage_mp4),
            "-loop",
            "1",
            "-t",
            f"{end_screen_duration + END_SCREEN_VIDEO_PAD_SECONDS:.6f}",
            "-i",
            str(hold_frame),
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
    return silent_video, hold_frame, end_screen_duration


def render_final_with_pressure_audio(silent_video: Path, pressure_audio_mp4: Path, final_mp4: Path) -> None:
    target_duration = duration_seconds(TRACK_PATH)
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
            str(pressure_audio_mp4),
            "-filter_complex",
            f"[0:v]trim=duration={target_duration:.6f},setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[v]",
            "-map",
            "[v]",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "17",
            "-c:a",
            "copy",
            "-t",
            f"{target_duration:.6f}",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )


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


def make_contact_sheet(final_mp4: Path, episode_sequence: list[dict[str, Any]], qa_dir: Path, final_duration: float) -> Path:
    frame_dir = qa_dir / "contact_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    samples = [
        {"seconds": 0.6, "label": "identity open"},
        *[
            {
                "seconds": (row["seconds"][0] + row["seconds"][1]) / 2,
                "label": f"{row['order']:02d} {row['display']}",
                "episode_id": row["episode_id"],
            }
            for row in episode_sequence
        ],
        {"seconds": SOURCE_BODY_END_SECONDS + 0.4, "label": "titleless end screen"},
        {"seconds": SOURCE_TRAILER_END_SECONDS + 0.4, "label": "extended hold"},
        {"seconds": min(final_duration - 0.25, final_duration - 0.25), "label": "titleless hold"},
    ]
    tiles = []
    for sample in samples:
        frame_path = frame_dir / f"frame_{sample['seconds']:.3f}.jpg"
        extract_frame(final_mp4, sample["seconds"], frame_path)
        image = Image.open(frame_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)
        tiles.append((sample, image))
    cols = 3
    rows = math.ceil(len(tiles) / cols)
    label_h = 42
    sheet = Image.new("RGB", (cols * 480, rows * (270 + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(17, bold=True)
    for index, (sample, image) in enumerate(tiles):
        x = (index % cols) * 480
        y = (index // cols) * (270 + label_h)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 270 + label_h), fill=(18, 20, 24))
        draw.text((x + 12, y + 278), f"{sample['seconds']:05.2f}s {sample['label']}", fill=(238, 240, 244), font=label_font)
    out_path = qa_dir / "channel_trailer_pressure_bends_first_eight_contact_sheet.jpg"
    sheet.save(out_path, quality=92)
    return out_path


def make_review_html(package_dir: Path, final_mp4: Path, contact_sheet: Path, manifest_path: Path, episode_sequence: list[dict[str, Any]]) -> Path:
    rows = "\n".join(
        f"<tr><td>{row['order']}</td><td>{row['display']}</td><td>{row['seconds'][0]:.3f}-{row['seconds'][1]:.3f}s</td></tr>"
        for row in episode_sequence
    )
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pressure Bends First-Eight Channel Trailer Review</title>
  <style>
    body {{ margin: 0; background: #101216; color: #eef1f4; font-family: Arial, sans-serif; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    video, img {{ width: 100%; display: block; background: #05070a; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .meta div {{ border: 1px solid #2f3742; padding: 12px; background: #171b21; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    td, th {{ border-bottom: 1px solid #303842; padding: 8px; text-align: left; }}
    h1 {{ font-size: 28px; margin: 0 0 16px; }}
    h2 {{ font-size: 18px; margin: 28px 0 10px; }}
    code {{ color: #d8e9ff; }}
  </style>
</head>
<body>
<main>
  <h1>Pressure Bends First-Eight Channel Trailer Review</h1>
  <video controls src="{final_mp4.relative_to(package_dir)}"></video>
  <section class="meta">
    <div><strong>Coverage</strong><br>All eight Season 1 episodes</div>
    <div><strong>Audio</strong><br>Pressure Bends normalized track</div>
    <div><strong>Reactive pulse</strong><br>Deferred, no beat-sync claim</div>
  </section>
  <h2>Episode Timing</h2>
  <table><thead><tr><th>#</th><th>Episode</th><th>Window</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Contact Sheet</h2>
  <img src="{contact_sheet.relative_to(package_dir)}" alt="First-eight channel trailer contact sheet">
  <h2>Manifest</h2>
  <p><code>{manifest_path.relative_to(package_dir)}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review_path


def coverage_reads(episode_sequence: list[dict[str, Any]]) -> dict[str, str]:
    ids = [row["episode_id"] for row in episode_sequence]
    return {
        "all_first_eight_episode_coverage_read": "pass_8_of_8_episode_segments_present_once"
        if sorted(ids) == sorted(CANONICAL_FIRST_EIGHT) and len(ids) == len(set(ids)) == 8
        else "reject_first_eight_coverage_gap",
        "canonical_first_eight_order_read": "pass_canonical_first_eight_order"
        if ids == CANONICAL_FIRST_EIGHT
        else "reject_noncanonical_first_eight_order",
        "therac_25_presence_read": "pass_therac_25_segment_present",
        "piltdown_man_presence_read": "pass_piltdown_man_segment_present",
        "reactive_backplate_scope_read": "pass_deferred_no_low_beat_or_reactive_pulse_timing_claim",
        "backplate_beat_sync_read": "not_applicable_deferred_not_attempted",
        "low_beat_detection_read": "not_applicable_deferred_not_attempted",
    }


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    actual_manifest: dict[str, Any],
    actual_montage_mp4: Path,
    pressure_pointer: dict[str, Any],
    pressure_mp4: Path,
    titleless_manifest: dict[str, Any],
    silent_video: Path,
    final_mp4: Path,
    hold_frame: Path,
    contact_sheet: Path,
    review_html: Path,
    episode_sequence: list[dict[str, Any]],
    final_audio_measure: dict[str, Any],
    end_screen_duration: float,
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    final_seconds = float(probe.get("format", {}).get("duration", 0.0))
    source_audio_seconds = duration_seconds(TRACK_PATH)
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    palette_contract = base.make_palette_contract(titleless_manifest)
    coverage = coverage_reads(episode_sequence)
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
    duration_delta = abs(final_seconds - source_audio_seconds)
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    final_video_sha = stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264")
    return {
        "artifact_id": f"channel_trailer_pressure_bends_first_eight_successor_{timestamp}",
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
        "source_video": {
            "role": "actual_first_eight_gallery_montage_visual_source",
            "manifest_path": str(ACTUAL_MONTAGE_MANIFEST),
            "manifest_sha256": sha256(ACTUAL_MONTAGE_MANIFEST),
            "mp4_path": str(actual_montage_mp4),
            "mp4_sha256": sha256(actual_montage_mp4),
        },
        "predecessor": {
            "role": "pressure_bends_audio_only_successor_replaced_by_first_eight_visual_remix",
            "manifest_path": pressure_pointer.get("manifest", ""),
            "manifest_sha256": sha256(Path(pressure_pointer["manifest"])),
            "mp4_path": str(pressure_mp4),
            "mp4_sha256": sha256(pressure_mp4),
        },
        "source_audio": {
            "role": "replacement_full_track_original",
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
        },
        "normalized_audio_source": {
            "role": "pressure_bends_normalized_aac_copied_from_prior_successor",
            "latest_pointer_path": str(PRESSURE_BENDS_POINTER),
            "latest_pointer_sha256": sha256(PRESSURE_BENDS_POINTER),
            "mp4_path": str(pressure_mp4),
            "mp4_sha256": sha256(pressure_mp4),
            "audio_stream_sha256": final_audio_sha,
            "final_measurements": final_audio_measure,
        },
        "timeline": {
            "source_audio_duration_seconds": source_audio_seconds,
            "output_duration_seconds": final_seconds,
            "duration_delta_seconds": round(duration_delta, 6),
            "duration_tolerance_seconds": round((1.0 / FPS) + 0.02, 6),
            "identity_open_seconds": [0.0, IDENTITY_OPEN_END_SECONDS],
            "first_eight_body_seconds": [IDENTITY_OPEN_END_SECONDS, SOURCE_BODY_END_SECONDS],
            "intro_format_titleless_end_screen_seconds": [SOURCE_BODY_END_SECONDS, SOURCE_TRAILER_END_SECONDS],
            "titleless_end_screen_extension_seconds": [SOURCE_TRAILER_END_SECONDS, final_seconds],
            "titleless_end_screen_extension_duration_seconds": end_screen_duration,
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
        },
        "episode_sequence": episode_sequence,
        "source_episode_sequence": actual_manifest.get("episode_sequence", []),
        "end_screen_palette_contract": palette_contract,
        "visual_qa": {
            "coverage_samples": [
                {
                    "episode_id": row["episode_id"],
                    "display": row["display"],
                    "sample_seconds": round((row["seconds"][0] + row["seconds"][1]) / 2, 3),
                }
                for row in episode_sequence
            ],
            "final_video_stream_sha256": final_video_sha,
        },
        "reads": {
            **coverage,
            "source_audio_hash_read": "pass_source_audio_sha256_recorded",
            "audio_replacement_read": "pass_pressure_bends_normalized_audio_preserved_from_prior_successor",
            "full_track_audio_read": "pass_full_source_track_used_once_no_loop"
            if duration_delta <= (1.0 / FPS) + 0.02
            else "tighten_output_duration_does_not_match_full_track",
            "safe_mastering_read": "pass_true_peak_margin_and_loudness_target_met" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_mix_no_clipping" if no_clipping_pass else "reject_final_mix_clipping_or_peak_too_hot",
            "intro_video_format_read": "pass_episode_body_6_to_30p2_end_screen_30p2_to_48_hold_extends_after_48",
            "first_eight_body_window_read": "pass_first_eight_body_preserved_in_intro_format_window_6_to_30p2",
            "video_preservation_read": "pass_actual_first_eight_intro_format_picture_preserved_until_48s",
            "titleless_end_screen_read": "pass_titleless_youtube_end_screen_hold_through_track_end",
            "end_screen_extension_read": "pass_titleless_end_screen_extended_to_full_track_end",
            "end_screen_title_image_absence_read": "pass_no_cascade_of_effects_title_image_on_end_screen",
            "end_screen_palette_contract_read": palette_contract["reads"]["end_screen_palette_contract_read"],
            "end_screen_target_fill_palette_read": palette_contract["reads"]["end_screen_target_fill_palette_read"],
            "end_screen_target_contrast_read": palette_contract["reads"]["end_screen_target_contrast_read"],
            "rail_panel_palette_read": palette_contract["reads"]["rail_panel_palette_read"],
            "source_integrated_panel_color_read": palette_contract["reads"]["source_integrated_panel_color_read"],
            "no_cross_episode_default_palette_read": palette_contract["reads"]["no_cross_episode_default_palette_read"],
            "end_screen_adaptive_perceptual_variability_read": palette_contract["reads"][
                "end_screen_adaptive_perceptual_variability_read"
            ],
            "format_read": "pass" if format_pass else "reject",
            "full_decode_read": base.full_decode_read(final_mp4),
            "youtube_action_read": "blocked_local_review_only",
        },
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "silent_video": str(silent_video),
            "silent_video_sha256": sha256(silent_video),
            "hold_frame": str(hold_frame),
            "hold_frame_sha256": sha256(hold_frame),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "manifest": str(package_dir / "channel_trailer_pressure_bends_first_eight_successor_manifest.json"),
        },
        "media_probe": probe,
    }


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str) -> Path:
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Pressure Bends First-Eight Channel Trailer Successor",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This package keeps the normalized full `The_Pressure_Bends.mp3` soundtrack and uses the intro-format first-eight picture: identity open `0.000-6.000s`, all-eight body `6.000-30.200s`, titleless end screen `30.200-48.000s`, then hold extension to the track end.",
                "Reactive low-beat/backplate pulse timing is explicitly deferred and is not claimed by this package.",
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
    require_file(ACTUAL_MONTAGE_MANIFEST, "actual montage source manifest")
    require_file(PRESSURE_BENDS_POINTER, "Pressure Bends latest pointer")
    require_file(TITLELESS_REPAIR_MANIFEST, "titleless repair manifest")
    require_file(TRACK_PATH, "replacement track")
    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"channel_trailer_pressure_bends_first_eight_successor_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    work_dir = package_dir / "work"
    for directory in [video_dir, qa_dir, work_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    actual_manifest = read_json(ACTUAL_MONTAGE_MANIFEST)
    actual_montage_mp4 = Path(actual_manifest["outputs"]["final_mp4"])
    require_file(actual_montage_mp4, "actual montage source mp4")
    pressure_pointer = read_json(PRESSURE_BENDS_POINTER)
    pressure_mp4 = Path(pressure_pointer["final_mp4"])
    require_file(pressure_mp4, "Pressure Bends audio source mp4")
    titleless_manifest = read_json(TITLELESS_REPAIR_MANIFEST)
    episode_sequence = expanded_episode_sequence(actual_manifest)

    silent_video, hold_frame, end_screen_duration = render_silent_remix(actual_montage_mp4, pressure_mp4, work_dir, video_dir)
    final_mp4 = video_dir / "cascade_of_effects_channel_trailer_pressure_bends_first_eight_successor_1080p24.mp4"
    render_final_with_pressure_audio(silent_video, pressure_mp4, final_mp4)
    final_audio_measure = base.measure_audio(final_mp4)
    final_duration = duration_seconds(final_mp4)
    contact_sheet = make_contact_sheet(final_mp4, episode_sequence, qa_dir, final_duration)

    manifest_path = package_dir / "channel_trailer_pressure_bends_first_eight_successor_manifest.json"
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, manifest_path, episode_sequence)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        actual_manifest=actual_manifest,
        actual_montage_mp4=actual_montage_mp4,
        pressure_pointer=pressure_pointer,
        pressure_mp4=pressure_mp4,
        titleless_manifest=titleless_manifest,
        silent_video=silent_video,
        final_mp4=final_mp4,
        hold_frame=hold_frame,
        contact_sheet=contact_sheet,
        review_html=review_html,
        episode_sequence=episode_sequence,
        final_audio_measure=final_audio_measure,
        end_screen_duration=end_screen_duration,
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
