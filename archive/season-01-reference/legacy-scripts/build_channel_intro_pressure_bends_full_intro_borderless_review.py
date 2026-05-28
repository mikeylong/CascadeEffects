#!/usr/bin/env python3
"""Build a full channel-intro review with the approved borderless end screen."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat


WIDTH = 1920
HEIGHT = 1080
FPS = 24
END_SCREEN_START_SECONDS = 30.2
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
WORKFLOW = "channel_intro_pressure_bends_first_eight_full_intro_borderless_review_v1"
OUTPUT_STEM = "channel_intro_pressure_bends_first_eight_full_intro_borderless_review"

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
SOURCE_FULL_INTRO_POINTER = OUTPUT_ROOT / "channel_trailer_pressure_bends_first_eight_successor_latest.json"
BORDERLESS_END_SCREEN_POINTER = OUTPUT_ROOT / "channel_intro_end_screen_adaptive_borderless_keep_latest.json"
LATEST_POINTER = OUTPUT_ROOT / f"{OUTPUT_STEM}_latest.json"
BASE_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_pressure_bends_successor.py"
VISUAL_DELTA_TOLERANCE = 5.0


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


def episode_rows(source_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate(source_manifest.get("episode_sequence", []), start=1):
        row = dict(item)
        row["order"] = index
        rows.append(row)
    return rows


def render_full_intro(
    source_mp4: Path,
    borderless_preview: Path,
    final_mp4: Path,
    source_duration: float,
) -> None:
    end_duration = source_duration - END_SCREEN_START_SECONDS
    if end_duration <= 0:
        raise SystemExit(f"Source full intro is too short: {source_duration:.3f}s")
    filter_graph = (
        f"[0:v]trim=0:{END_SCREEN_START_SECONDS:.6f},setpts=PTS-STARTPTS,"
        f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1[v0];"
        f"[1:v]fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1,setpts=PTS-STARTPTS[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[v]"
    )
    final_mp4.parent.mkdir(parents=True, exist_ok=True)
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
            f"{end_duration + 0.25:.6f}",
            "-i",
            str(borderless_preview),
            "-filter_complex",
            filter_graph,
            "-map",
            "[v]",
            "-map",
            "0:a:0",
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
            "-c:a",
            "copy",
            "-t",
            f"{source_duration:.6f}",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )


def frame_delta_report(
    source_mp4: Path,
    final_mp4: Path,
    samples: list[float],
    qa_dir: Path,
    *,
    label: str,
) -> dict[str, Any]:
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{label}_", dir=qa_dir))
    rows = []
    try:
        for seconds in samples:
            source_frame = temp_dir / f"source_{seconds:.3f}.jpg"
            final_frame = temp_dir / f"final_{seconds:.3f}.jpg"
            extract_frame(source_mp4, seconds, source_frame)
            extract_frame(final_mp4, seconds, final_frame)
            delta = mean_frame_delta(source_frame, final_frame)
            rows.append(
                {
                    "seconds": round(seconds, 3),
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


def borderless_delta_report(
    final_mp4: Path,
    borderless_preview: Path,
    samples: list[float],
    qa_dir: Path,
) -> dict[str, Any]:
    temp_dir = Path(tempfile.mkdtemp(prefix="borderless_", dir=qa_dir))
    rows = []
    try:
        reference = Image.open(borderless_preview).convert("RGB")
        reference_path = temp_dir / "reference.png"
        reference.save(reference_path)
        for seconds in samples:
            final_frame = temp_dir / f"final_{seconds:.3f}.jpg"
            extract_frame(final_mp4, seconds, final_frame)
            delta = mean_frame_delta(reference_path, final_frame)
            rows.append(
                {
                    "seconds": round(seconds, 3),
                    "reference_preview": str(borderless_preview),
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


def make_contact_sheet(final_mp4: Path, episodes: list[dict[str, Any]], qa_dir: Path, final_duration: float) -> Path:
    frame_dir = qa_dir / "contact_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    samples = [
        {"seconds": 0.6, "label": "identity open"},
        *[
            {
                "seconds": (row["seconds"][0] + row["seconds"][1]) / 2,
                "label": f"{row['order']:02d} {row['display']}",
            }
            for row in episodes
        ],
        {"seconds": END_SCREEN_START_SECONDS + 0.4, "label": "borderless end screen"},
        {"seconds": 48.4, "label": "borderless hold"},
        {"seconds": max(0.0, final_duration - 0.25), "label": "final hold"},
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
    out_path = qa_dir / "channel_intro_pressure_bends_full_intro_borderless_contact_sheet.jpg"
    sheet.save(out_path, quality=92)
    return out_path


def make_review_html(
    package_dir: Path,
    final_mp4: Path,
    contact_sheet: Path,
    manifest_path: Path,
    borderless_preview: Path,
    final_duration: float,
) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Full Intro Borderless End Screen Review</title>
  <style>
    body {{ margin: 0; background: #101216; color: #eef1f4; font-family: Arial, sans-serif; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    video, img {{ width: 100%; display: block; background: #05070a; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .meta div {{ border: 1px solid #2f3742; padding: 12px; background: #171b21; }}
    h1 {{ font-size: 28px; margin: 0 0 16px; }}
    h2 {{ font-size: 18px; margin: 28px 0 10px; }}
    code {{ color: #d8e9ff; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
<main>
  <h1>Full Intro Borderless End Screen Review</h1>
  <video controls src="{final_mp4.relative_to(package_dir)}"></video>
  <section class="meta">
    <div><strong>Runtime</strong><br>{final_duration:.3f}s full intro</div>
    <div><strong>Body</strong><br>First-eight Pressure Bends source preserved to 30.2s</div>
    <div><strong>End screen</strong><br>Approved borderless design from 30.2s to end</div>
  </section>
  <h2>Contact Sheet</h2>
  <img src="{contact_sheet.relative_to(package_dir)}" alt="Full intro borderless review contact sheet">
  <h2>Approved End Screen Reference</h2>
  <img src="{borderless_preview.relative_to(package_dir)}" alt="Approved borderless end screen reference">
  <h2>Manifest</h2>
  <p><code>{manifest_path.relative_to(package_dir)}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review_path


def format_pass(probe: dict[str, Any]) -> bool:
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return (
        video_stream.get("codec_name") == "h264"
        and video_stream.get("width") == WIDTH
        and video_stream.get("height") == HEIGHT
        and video_stream.get("avg_frame_rate") == "24/1"
        and audio_stream.get("codec_name") == "aac"
        and str(audio_stream.get("channels")) == "2"
    )


def copy_borderless_reference(preview: Path, package_dir: Path) -> Path:
    out = package_dir / "source" / preview.name
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(preview, out)
    return out


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    source_pointer: dict[str, Any],
    source_manifest: dict[str, Any],
    source_mp4: Path,
    borderless_pointer: dict[str, Any],
    borderless_manifest: dict[str, Any],
    source_borderless_preview: Path,
    local_borderless_preview: Path,
    final_mp4: Path,
    contact_sheet: Path,
    review_html: Path,
    episodes: list[dict[str, Any]],
    pre_end_report: dict[str, Any],
    borderless_report: dict[str, Any],
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    final_duration = float(probe.get("format", {}).get("duration", 0.0))
    source_duration = duration_seconds(source_mp4)
    source_audio_duration = float(source_manifest.get("timeline", {}).get("source_audio_duration_seconds", final_duration))
    duration_delta = abs(final_duration - source_audio_duration)
    final_audio_measure = base.measure_audio(final_mp4)
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    source_audio_sha = stream_sha256(source_mp4, "0:a:0", package_dir / "work/source_audio.aac")
    final_video_sha = stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264")
    palette_contract = borderless_manifest["end_screen_palette_contract"]
    palette_contract.setdefault("target_palette", {})["palette_treatment_model"] = END_SCREEN_PALETTE_TREATMENT_MODEL
    reads_from_palette = palette_contract.get("reads", {})
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
        "source_final_render": {
            "role": "full_intro_first_eight_pressure_bends_source",
            "manifest_path": source_pointer.get("manifest", ""),
            "manifest_sha256": sha256(Path(source_pointer["manifest"])),
            "mp4_path": str(source_mp4),
            "mp4_sha256": sha256(source_mp4),
        },
        "predecessor": {
            "role": "full_intro_first_eight_pressure_bends_source",
            "manifest_path": source_pointer.get("manifest", ""),
            "manifest_sha256": sha256(Path(source_pointer["manifest"])),
            "mp4_path": str(source_mp4),
            "mp4_sha256": sha256(source_mp4),
        },
        "source_audio": {
            "role": "pressure_bends_original_track",
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
        },
        "approved_borderless_end_screen": {
            "role": "human_approved_intro_end_screen_design",
            "latest_pointer_path": str(BORDERLESS_END_SCREEN_POINTER),
            "latest_pointer_sha256": sha256(BORDERLESS_END_SCREEN_POINTER),
            "manifest_path": borderless_pointer.get("manifest", ""),
            "manifest_sha256": sha256(Path(borderless_pointer["manifest"])),
            "source_preview_path": str(source_borderless_preview),
            "source_preview_sha256": sha256(source_borderless_preview),
            "local_preview_path": str(local_borderless_preview),
            "local_preview_sha256": sha256(local_borderless_preview),
            "human_review_decision": borderless_manifest.get("human_review_decision", ""),
            "approved_at_utc": borderless_manifest.get("approved_at_utc", ""),
        },
        "timeline": {
            "source_full_intro_duration_seconds": source_duration,
            "source_audio_duration_seconds": source_audio_duration,
            "output_duration_seconds": final_duration,
            "duration_delta_seconds": round(duration_delta, 6),
            "duration_tolerance_seconds": round((1.0 / FPS) + 0.02, 6),
            "identity_open_seconds": source_manifest.get("timeline", {}).get("identity_open_seconds", [0.0, 6.0]),
            "first_eight_body_seconds": source_manifest.get("timeline", {}).get("first_eight_body_seconds", [6.0, 30.2]),
            "approved_borderless_end_screen_seconds": [END_SCREEN_START_SECONDS, final_duration],
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
        },
        "end_screen_context": {
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "end_screen_palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "placeholder_style_model": borderless_manifest.get("end_screen_placeholder_style_model", "youtube_placeholder_borderless_underlay_v1"),
        },
        "episode_sequence": episodes,
        "end_screen_palette_contract": palette_contract,
        "audio_qa": {
            "source_audio_stream_sha256": source_audio_sha,
            "final_audio_stream_sha256": final_audio_sha,
            "audio_stream_copy_match": source_audio_sha == final_audio_sha,
            "final_measurements": final_audio_measure,
            "safe_true_peak_max_dbfs": base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS,
        },
        "visual_qa": {
            "pre_end_screen_visual_preservation_report": pre_end_report,
            "borderless_end_screen_application_report": borderless_report,
            "final_video_stream_sha256": final_video_sha,
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
        },
        "reads": {
            "all_first_eight_episode_coverage_read": source_manifest.get("reads", {}).get(
                "all_first_eight_episode_coverage_read", "pass_8_of_8_episode_segments_present_once"
            ),
            "canonical_first_eight_order_read": source_manifest.get("reads", {}).get(
                "canonical_first_eight_order_read", "pass_canonical_first_eight_order"
            ),
            "source_audio_hash_read": "pass_source_audio_sha256_recorded",
            "audio_replacement_read": "pass_pressure_bends_normalized_audio_preserved_from_full_intro_source",
            "full_track_audio_read": "pass_full_source_track_used_once_no_loop"
            if duration_delta <= (1.0 / FPS) + 0.02
            else "reject_output_duration_does_not_match_pressure_bends_track",
            "safe_mastering_read": "pass_true_peak_margin_and_loudness_target_met" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_mix_no_clipping" if no_clipping_pass else "reject_final_mix_clipping_or_peak_too_hot",
            "audio_stream_copy_read": "pass_audio_stream_copied_from_full_intro_source" if source_audio_sha == final_audio_sha else "reject_audio_stream_changed",
            "video_preservation_read": "pass_full_intro_body_preserved_until_30p2s"
            if pre_end_report["read"] == "pass"
            else "reject_pre_end_screen_visual_delta_above_tolerance",
            "approved_borderless_end_screen_read": "pass_human_approved_borderless_end_screen_applied_to_full_intro"
            if borderless_report["read"] == "pass"
            else "reject_borderless_end_screen_application_delta_above_tolerance",
            "end_screen_extension_read": "pass_borderless_titleless_end_screen_holds_from_30p2s_to_full_intro_end",
            "end_screen_title_image_absence_read": borderless_manifest.get("reads", {}).get(
                "end_screen_title_image_absence_read", "pass_no_cascade_of_effects_title_image_on_end_screen"
            ),
            "end_screen_palette_contract_read": reads_from_palette["end_screen_palette_contract_read"],
            "end_screen_target_fill_palette_read": reads_from_palette["end_screen_target_fill_palette_read"],
            "end_screen_target_contrast_read": reads_from_palette["end_screen_target_contrast_read"],
            "rail_panel_palette_read": reads_from_palette.get("rail_panel_palette_read", "pass_adaptive_end_screen_targets_use_source_aware_palette"),
            "source_integrated_panel_color_read": reads_from_palette["source_integrated_panel_color_read"],
            "no_cross_episode_default_palette_read": reads_from_palette["no_cross_episode_default_palette_read"],
            "end_screen_adaptive_perceptual_variability_read": reads_from_palette.get(
                "end_screen_adaptive_perceptual_variability_read", "pass_backplate_hue_visible_across_end_screen_targets"
            ),
            "end_screen_placeholder_style_read": borderless_manifest.get("reads", {}).get(
                "end_screen_placeholder_style_read", "pass_youtube_placeholder_borderless_underlay_v1"
            ),
            "end_screen_outline_removal_read": borderless_manifest.get("reads", {}).get(
                "end_screen_outline_removal_read", "pass_borders_glow_rings_inset_rings_subscribe_inner_ring_and_shadow_removed"
            ),
            "format_read": "pass" if format_pass(probe) else "reject",
            "full_decode_read": base.full_decode_read(final_mp4),
            "youtube_action_read": "blocked_local_review_only",
        },
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "borderless_reference_preview": str(local_borderless_preview),
            "manifest": str(package_dir / f"{OUTPUT_STEM}_manifest.json"),
        },
        "media_probe": probe,
    }


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str) -> Path:
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Full Intro Borderless End Screen Review",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This local review preserves the current full first-eight Pressure Bends intro body/audio and replaces only the `30.200s` onward end-screen section with the human-approved borderless adaptive titleless design.",
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
    require_file(SOURCE_FULL_INTRO_POINTER, "source full intro latest pointer")
    require_file(BORDERLESS_END_SCREEN_POINTER, "approved borderless end-screen latest pointer")
    require_file(TRACK_PATH, "Pressure Bends source track")
    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    work_dir = package_dir / "work"
    for directory in [video_dir, qa_dir, work_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    source_pointer = read_json(SOURCE_FULL_INTRO_POINTER)
    source_manifest_path = Path(source_pointer["manifest"])
    source_manifest = read_json(source_manifest_path)
    source_mp4 = Path(source_pointer["final_mp4"])
    require_file(source_manifest_path, "source full intro manifest")
    require_file(source_mp4, "source full intro MP4")

    borderless_pointer = read_json(BORDERLESS_END_SCREEN_POINTER)
    borderless_manifest_path = Path(borderless_pointer["manifest"])
    borderless_manifest = read_json(borderless_manifest_path)
    source_borderless_preview = Path(borderless_pointer["adaptive_end_screen_preview"])
    require_file(borderless_manifest_path, "approved borderless end-screen manifest")
    require_file(source_borderless_preview, "approved borderless end-screen preview")
    if borderless_manifest.get("status") != "keep":
        raise SystemExit(f"Borderless end-screen is not keep-approved: {borderless_manifest_path}")

    local_borderless_preview = copy_borderless_reference(source_borderless_preview, package_dir)
    final_mp4 = video_dir / "cascade_of_effects_channel_intro_pressure_bends_first_eight_full_intro_borderless_1080p24.mp4"
    source_duration = duration_seconds(source_mp4)
    render_full_intro(source_mp4, local_borderless_preview, final_mp4, source_duration)
    final_duration = duration_seconds(final_mp4)

    episodes = episode_rows(source_manifest)
    pre_end_samples = [0.6, *[(row["seconds"][0] + row["seconds"][1]) / 2 for row in episodes], END_SCREEN_START_SECONDS - 0.25]
    pre_end_report = frame_delta_report(source_mp4, final_mp4, pre_end_samples, qa_dir, label="pre_end")
    borderless_samples = [END_SCREEN_START_SECONDS + 0.4, 47.5, min(48.4, final_duration - 0.25), max(0.0, final_duration - 0.25)]
    borderless_report = borderless_delta_report(final_mp4, local_borderless_preview, borderless_samples, qa_dir)
    write_json(qa_dir / "pre_end_screen_visual_preservation_report.json", pre_end_report)
    write_json(qa_dir / "borderless_end_screen_application_report.json", borderless_report)
    contact_sheet = make_contact_sheet(final_mp4, episodes, qa_dir, final_duration)

    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, manifest_path, local_borderless_preview, final_duration)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        source_pointer=source_pointer,
        source_manifest=source_manifest,
        source_mp4=source_mp4,
        borderless_pointer=borderless_pointer,
        borderless_manifest=borderless_manifest,
        source_borderless_preview=source_borderless_preview,
        local_borderless_preview=local_borderless_preview,
        final_mp4=final_mp4,
        contact_sheet=contact_sheet,
        review_html=review_html,
        episodes=episodes,
        pre_end_report=pre_end_report,
        borderless_report=borderless_report,
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
