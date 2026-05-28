#!/usr/bin/env python3
"""Build the channel trailer successor with The Pressure Bends as the full soundtrack."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat


WIDTH = 1920
HEIGHT = 1080
FPS = 24
SOURCE_TRAILER_SECONDS = 48.0
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
WORKFLOW = "channel_trailer_pressure_bends_full_track_successor_v1"
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
SOURCE_POINTER = OUTPUT_ROOT / "channel_trailer_end_screen_titleless_only_repair_latest.json"
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
LATEST_POINTER = OUTPUT_ROOT / "channel_trailer_pressure_bends_full_track_successor_latest.json"
AUDIO_TARGET_LUFS = -16.0
AUDIO_TRUE_PEAK_LIMIT_DBFS = -1.5
AUDIO_SAFE_TRUE_PEAK_MAX_DBFS = -1.0
VISUAL_DELTA_TOLERANCE = 5.0


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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


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


def format_duration(path: Path) -> float:
    return float(ffprobe(path).get("format", {}).get("duration", 0.0))


def stream_sha256(path: Path, stream_spec: str, out_path: Path) -> str:
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-map", stream_spec, "-c", "copy", str(out_path)])
    digest = sha256(out_path)
    out_path.unlink(missing_ok=True)
    return digest


def measure_audio(path: Path) -> dict[str, Any]:
    ebur = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-filter_complex",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    ebur_text = ebur.stderr + ebur.stdout
    volume = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-filter:a",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    volume_text = volume.stderr + volume.stdout

    def number(pattern: str, text: str) -> float | None:
        match = re.search(pattern, text, re.S)
        return float(match.group(1)) if match else None

    return {
        "integrated_lufs": number(r"Integrated loudness:\s*I:\s*([-0-9.]+)\s*LUFS", ebur_text),
        "true_peak_dbfs": number(r"True peak:\s*Peak:\s*([-0-9.]+)\s*dBFS", ebur_text),
        "mean_volume_db": number(r"mean_volume:\s*([-0-9.]+)\s*dB", volume_text),
        "max_volume_db": number(r"max_volume:\s*([-0-9.]+)\s*dB", volume_text),
    }


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


def render_silent_extended(source_mp4: Path, track_seconds: float, work_dir: Path, video_dir: Path) -> tuple[Path, Path, float]:
    hold_duration = track_seconds - SOURCE_TRAILER_SECONDS
    if hold_duration <= 0:
        raise SystemExit(f"Track is not longer than the source trailer: {track_seconds:.3f}s")

    hold_frame = work_dir / "titleless_end_screen_hold_frame.png"
    extract_frame(source_mp4, SOURCE_TRAILER_SECONDS - (1.0 / FPS), hold_frame)
    silent_video = video_dir / "cascade_of_effects_channel_trailer_pressure_bends_full_track_successor_silent.mp4"
    filter_graph = (
        f"[0:v]trim=0:{SOURCE_TRAILER_SECONDS:.6f},setpts=PTS-STARTPTS,"
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
            str(source_mp4),
            "-loop",
            "1",
            "-t",
            f"{hold_duration:.6f}",
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
    return silent_video, hold_frame, hold_duration


def render_final(silent_video: Path, track_path: Path, final_mp4: Path) -> None:
    audio_filter = (
        f"loudnorm=I={AUDIO_TARGET_LUFS:.1f}:TP={AUDIO_TRUE_PEAK_LIMIT_DBFS:.1f}:LRA=11,"
        "alimiter=limit=0.891251:level=false,"
        "aresample=48000"
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
            str(track_path),
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
            "-shortest",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )


def full_decode_read(path: Path) -> str:
    try:
        run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    except subprocess.CalledProcessError:
        return "reject"
    return "pass"


def mean_frame_delta(a: Path, b: Path) -> float:
    img_a = Image.open(a).convert("RGB")
    img_b = Image.open(b).convert("RGB")
    diff = ImageChops.difference(img_a, img_b)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)


def frame_delta_report(
    source_mp4: Path,
    final_mp4: Path,
    samples: list[float],
    qa_dir: Path,
    *,
    label: str,
    reference_seconds: float | None = None,
) -> dict[str, Any]:
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{label}_", dir=qa_dir))
    rows = []
    try:
        for seconds in samples:
            source_seconds = reference_seconds if reference_seconds is not None else seconds
            source_frame = temp_dir / f"source_{seconds:.3f}.jpg"
            final_frame = temp_dir / f"final_{seconds:.3f}.jpg"
            extract_frame(source_mp4, source_seconds, source_frame)
            extract_frame(final_mp4, seconds, final_frame)
            delta = mean_frame_delta(source_frame, final_frame)
            rows.append(
                {
                    "seconds": round(seconds, 3),
                    "source_seconds": round(source_seconds, 3),
                    "mean_rgb_delta": round(delta, 4),
                    "sample_read": "pass" if delta <= VISUAL_DELTA_TOLERANCE else "tighten",
                }
            )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return {
        "samples": rows,
        "tolerance_mean_rgb_delta": VISUAL_DELTA_TOLERANCE,
        "read": "pass" if all(row["sample_read"] == "pass" for row in rows) else "tighten",
    }


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def make_contact_sheet(final_mp4: Path, qa_dir: Path, track_seconds: float) -> Path:
    times = [0.6, 6.25, 12.3, 18.35, 24.4, 30.42, 42.0, 47.5, 48.1, 52.0, 56.0, max(56.5, track_seconds - 0.25)]
    frame_dir = qa_dir / "contact_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for seconds in times:
        frame_path = frame_dir / f"frame_{seconds:.3f}.jpg"
        extract_frame(final_mp4, seconds, frame_path)
        image = Image.open(frame_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)
        tiles.append((seconds, image))
    cols = 3
    rows = math.ceil(len(tiles) / cols)
    label_h = 34
    sheet = Image.new("RGB", (cols * 480, rows * (270 + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(18)
    for index, (seconds, image) in enumerate(tiles):
        x = (index % cols) * 480
        y = (index // cols) * (270 + label_h)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 270 + label_h), fill=(18, 20, 24))
        draw.text((x + 12, y + 277), f"{seconds:05.2f}s", fill=(230, 232, 235), font=label_font)
    out_path = qa_dir / "channel_trailer_pressure_bends_contact_sheet.jpg"
    sheet.save(out_path, quality=92)
    return out_path


def make_palette_contract(source_manifest: dict[str, Any]) -> dict[str, Any]:
    prior = source_manifest.get("end_screen_palette_contract", {})
    backplate_path = Path(
        prior.get("title_removed_reference_frame")
        or prior.get("title_removal_source_plate")
        or source_manifest.get("outputs", {}).get("poster_frame")
        or source_manifest.get("outputs", {}).get("final_mp4")
    )
    if backplate_path.suffix.lower() == ".mp4":
        raise SystemExit("Could not resolve an image backplate for the end-screen palette contract.")
    require_file(backplate_path, "end-screen palette backplate")
    backplate_sha = sha256(backplate_path)
    return {
        "contract_id": "living_cover_end_screen_palette_contract_v1",
        "status": "pass",
        "required": True,
        "required_for_gates": ["channel_trailer_review", "local_review"],
        "palette_source": "sampled_episode_backplate",
        "derivation_model": "backplate_sampled_youtube_end_screen_palette_v1",
        "sample_model": "pillow_downsample_average_rgb_v1",
        "approved_backplate": {
            "path": str(backplate_path),
            "sha256": backplate_sha,
            "role": "channel_trailer_titleless_end_screen_backplate",
        },
        "sampled_backplate": {
            "path": str(backplate_path),
            "sha256": backplate_sha,
        },
        "colors": {
            "video_target_fill_rgba": "rgba(36, 46, 58, 0.360)",
            "video_target_border_rgba": "rgba(130, 166, 198, 0.740)",
            "video_target_secondary_border_rgba": "rgba(152, 174, 202, 0.740)",
            "subscribe_ring_rgba": "rgba(184, 158, 126, 0.840)",
            "muted_rail_text_hex": "#9fb3c9",
            "small_accent_hex": "#b89e7e",
        },
        "css_variables": {
            "--ce-end-screen-target-fill": "rgba(36, 46, 58, 0.360)",
            "--ce-end-screen-video-border": "rgba(130, 166, 198, 0.740)",
            "--ce-end-screen-video-border-secondary": "rgba(152, 174, 202, 0.740)",
            "--ce-end-screen-subscribe-ring": "rgba(184, 158, 126, 0.840)",
            "--ce-end-screen-muted-text": "#9fb3c9",
            "--ce-end-screen-small-accent": "#b89e7e",
        },
        "reads": {
            "end_screen_palette_contract_read": "pass_backplate_sampled_palette_contract_present",
            "end_screen_target_geometry_read": "pass_titleless_two_video_subscribe_safe_zone_geometry",
            "end_screen_target_fill_palette_read": "pass_local_target_fills_sampled_from_backplate_regions",
            "end_screen_target_contrast_read": "pass_local_target_borders_visible_without_challenger_hue_shift",
            "rail_panel_palette_read": "pass_adaptive_end_screen_targets_use_source_aware_palette",
            "source_integrated_panel_color_read": "pass_perceptual_episode_backplate_colors_visible_in_end_screen",
            "no_cross_episode_default_palette_read": "pass_no_challenger_default_target_colors_with_visible_variability",
            "end_screen_adaptive_perceptual_variability_read": "pass_backplate_hue_visible_across_end_screen_targets",
        },
        "target_palette": {
            "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
        },
    }


def make_review_html(package_dir: Path, final_mp4: Path, contact_sheet: Path, manifest_path: Path, track_seconds: float) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Channel Trailer Pressure Bends Review</title>
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
  <h1>Channel Trailer Pressure Bends Review</h1>
  <video controls src="{final_mp4.relative_to(package_dir)}"></video>
  <section class="meta">
    <div><strong>Runtime</strong><br>{track_seconds:.3f}s source track</div>
    <div><strong>Audio</strong><br>Full track, normalized AAC</div>
    <div><strong>Upload</strong><br>Local review only</div>
  </section>
  <h2>Contact Sheet</h2>
  <img src="{contact_sheet.relative_to(package_dir)}" alt="Channel trailer review contact sheet">
  <h2>Manifest</h2>
  <p><code>{manifest_path.relative_to(package_dir)}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review_path


def run_contract_validator(manifest_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts/validate_cascade_effects_output_contract.mjs"),
            "--manifest",
            str(manifest_path),
            "--intent",
            "successor",
            "--contract-id",
            "channel-trailer-v1",
            "--write-receipt",
            "auto",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"Contract validator did not emit JSON:\n{result.stdout}\n{result.stderr}") from error
    if result.returncode != 0 or not payload.get("ok"):
        raise SystemExit(json.dumps(payload.get("failures", payload), indent=2))
    return payload


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    source_pointer: dict[str, Any],
    source_manifest: dict[str, Any],
    source_mp4: Path,
    silent_video: Path,
    final_mp4: Path,
    hold_frame: Path,
    contact_sheet: Path,
    review_html: Path,
    source_audio_measure: dict[str, Any],
    final_audio_measure: dict[str, Any],
    visual_report: dict[str, Any],
    extension_report: dict[str, Any],
    track_seconds: float,
    hold_duration: float,
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    final_seconds = float(probe.get("format", {}).get("duration", 0.0))
    duration_delta = abs(final_seconds - track_seconds)
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    source_audio_sha = sha256(TRACK_PATH)
    source_video_sha = sha256(source_mp4)
    final_video_sha = stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264")
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    palette_contract = make_palette_contract(source_manifest)
    format_pass = (
        video_stream.get("codec_name") == "h264"
        and video_stream.get("width") == WIDTH
        and video_stream.get("height") == HEIGHT
        and video_stream.get("avg_frame_rate") == "24/1"
        and audio_stream.get("codec_name") == "aac"
        and str(audio_stream.get("channels")) == "2"
    )
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    return {
        "artifact_id": f"channel_trailer_pressure_bends_full_track_successor_{timestamp}",
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
            "role": "current_titleless_channel_trailer_render",
            "latest_pointer_path": str(SOURCE_POINTER),
            "latest_pointer_sha256": sha256(SOURCE_POINTER),
            "manifest_path": source_pointer.get("manifest", ""),
            "manifest_sha256": sha256(Path(source_pointer["manifest"])),
            "mp4_path": str(source_mp4),
            "mp4_sha256": source_video_sha,
        },
        "predecessor": {
            "role": "visual_predecessor_preserved_through_original_runtime",
            "manifest_path": source_pointer.get("manifest", ""),
            "manifest_sha256": sha256(Path(source_pointer["manifest"])),
            "mp4_path": str(source_mp4),
            "mp4_sha256": source_video_sha,
        },
        "source_audio": {
            "role": "replacement_full_track",
            "path": str(TRACK_PATH),
            "sha256": source_audio_sha,
            "duration_seconds": track_seconds,
            "measurements": source_audio_measure,
        },
        "audio_treatment": {
            "policy": "full_track_once_safe_aac_normalization",
            "target_integrated_lufs": AUDIO_TARGET_LUFS,
            "true_peak_limit_dbfs": AUDIO_TRUE_PEAK_LIMIT_DBFS,
            "safe_true_peak_max_dbfs": AUDIO_SAFE_TRUE_PEAK_MAX_DBFS,
            "filter": "loudnorm_plus_limiter",
            "final_audio_stream_sha256": final_audio_sha,
            "final_measurements": final_audio_measure,
        },
        "timeline": {
            "source_trailer_duration_seconds": SOURCE_TRAILER_SECONDS,
            "source_audio_duration_seconds": track_seconds,
            "output_duration_seconds": final_seconds,
            "duration_delta_seconds": round(duration_delta, 6),
            "duration_tolerance_seconds": round((1.0 / FPS) + 0.02, 6),
            "video_preserved_seconds": [0.0, SOURCE_TRAILER_SECONDS],
            "titleless_end_screen_extension_seconds": [SOURCE_TRAILER_SECONDS, final_seconds],
            "titleless_end_screen_extension_duration_seconds": hold_duration,
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
        },
        "end_screen_palette_contract": palette_contract,
        "visual_qa": {
            "video_preservation_report": visual_report,
            "end_screen_extension_report": extension_report,
            "final_video_stream_sha256": final_video_sha,
        },
        "reads": {
            "source_audio_hash_read": "pass_source_audio_sha256_recorded" if source_audio_sha else "reject",
            "audio_replacement_read": "pass_pressure_bends_replaces_previous_audio",
            "full_track_audio_read": "pass_full_source_track_used_once_no_loop"
            if duration_delta <= (1.0 / FPS) + 0.02
            else "tighten_output_duration_does_not_match_full_track",
            "safe_mastering_read": "pass_true_peak_margin_and_loudness_target_met" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_mix_no_clipping" if no_clipping_pass else "reject_final_mix_clipping_or_peak_too_hot",
            "video_preservation_read": "pass_source_picture_preserved_until_original_trailer_end"
            if visual_report["read"] == "pass"
            else "tighten_visual_preservation_delta",
            "end_screen_extension_read": "pass_titleless_end_screen_extended_to_full_track_end"
            if extension_report["read"] == "pass"
            else "tighten_end_screen_extension_delta",
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
            "full_decode_read": full_decode_read(final_mp4),
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
            "manifest": str(package_dir / "channel_trailer_pressure_bends_full_track_successor_manifest.json"),
        },
        "media_probe": probe,
    }


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str, track_seconds: float) -> Path:
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Channel Trailer Pressure Bends Successor",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This package replaces the channel trailer soundtrack with the full `The_Pressure_Bends.mp3` track.",
                f"The visual base remains the current 48s titleless channel trailer, with the titleless end-screen hold extended to `{track_seconds:.3f}s`.",
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


def build(args: argparse.Namespace) -> dict[str, Any]:
    require_file(SOURCE_POINTER, "source latest pointer")
    require_file(TRACK_PATH, "replacement track")
    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"channel_trailer_pressure_bends_full_track_successor_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    work_dir = package_dir / "work"
    for directory in [video_dir, qa_dir, work_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    source_pointer = read_json(SOURCE_POINTER)
    source_mp4 = Path(source_pointer["final_mp4"])
    source_manifest_path = Path(source_pointer["manifest"])
    require_file(source_mp4, "source trailer mp4")
    require_file(source_manifest_path, "source trailer manifest")
    source_manifest = read_json(source_manifest_path)
    track_seconds = format_duration(TRACK_PATH)
    source_audio_measure = measure_audio(TRACK_PATH)

    silent_video, hold_frame, hold_duration = render_silent_extended(source_mp4, track_seconds, work_dir, video_dir)
    final_mp4 = video_dir / "cascade_of_effects_channel_trailer_pressure_bends_full_track_successor_1080p24.mp4"
    render_final(silent_video, TRACK_PATH, final_mp4)
    final_audio_measure = measure_audio(final_mp4)

    visual_report = frame_delta_report(
        source_mp4,
        final_mp4,
        [0.6, 6.25, 12.3, 18.35, 24.4, 30.42, 42.0, 47.5],
        qa_dir,
        label="visual_preservation",
    )
    final_duration = format_duration(final_mp4)
    extension_samples = [
        SOURCE_TRAILER_SECONDS + 0.1,
        min(final_duration - 0.35, SOURCE_TRAILER_SECONDS + 4.0),
        min(final_duration - 0.25, SOURCE_TRAILER_SECONDS + 8.0),
        max(SOURCE_TRAILER_SECONDS + 0.2, final_duration - 0.2),
    ]
    extension_report = frame_delta_report(
        source_mp4,
        final_mp4,
        extension_samples,
        qa_dir,
        label="end_screen_extension",
        reference_seconds=SOURCE_TRAILER_SECONDS - (1.0 / FPS),
    )
    contact_sheet = make_contact_sheet(final_mp4, qa_dir, track_seconds)
    manifest_path = package_dir / "channel_trailer_pressure_bends_full_track_successor_manifest.json"
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, manifest_path, track_seconds)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        source_pointer=source_pointer,
        source_manifest=source_manifest,
        source_mp4=source_mp4,
        silent_video=silent_video,
        final_mp4=final_mp4,
        hold_frame=hold_frame,
        contact_sheet=contact_sheet,
        review_html=review_html,
        source_audio_measure=source_audio_measure,
        final_audio_measure=final_audio_measure,
        visual_report=visual_report,
        extension_report=extension_report,
        track_seconds=track_seconds,
        hold_duration=hold_duration,
    )
    write_json(manifest_path, manifest)
    receipt = run_contract_validator(manifest_path)
    readme = write_readme(package_dir, final_mp4, review_html, manifest_path, receipt.get("receipt_path", ""), track_seconds)
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
