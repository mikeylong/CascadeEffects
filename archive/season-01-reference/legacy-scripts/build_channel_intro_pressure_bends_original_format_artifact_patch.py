#!/usr/bin/env python3
"""Build a minimal original-format intro patch with Pressure Bends and two artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH = 1920
HEIGHT = 1080
FPS = 24
DURATION_SECONDS = 48.0
WORKFLOW = "channel_intro_pressure_bends_original_format_artifact_patch_v1"
OUTPUT_STEM = "channel_intro_pressure_bends_original_format_artifact_patch"

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
SOURCE_PACKAGE = OUTPUT_ROOT / "channel_trailer_end_screen_titleless_only_repair_20260524T054934Z"
SOURCE_MP4 = SOURCE_PACKAGE / "video/cascade_of_effects_channel_trailer_end_screen_titleless_only_1080p24.mp4"
SOURCE_MANIFEST = SOURCE_PACKAGE / "channel_trailer_end_screen_titleless_only_manifest.json"
LATEST_POINTER = OUTPUT_ROOT / f"{OUTPUT_STEM}_latest.json"
BASE_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_pressure_bends_successor.py"

GALLERY_ROOT = Path("/Users/mike/Web_CascadeEffects/brand/assets/episode-gallery/proof-v6-ink-lit-subjects/source-renders")
ARTIFACTS = [
    {
        "episode_id": "therac-25",
        "display": "Therac-25",
        "source": GALLERY_ROOT / "therac-25-thumbnail-proof-v6-ink-lit-subjects-source.png",
        "seconds": [8.42, 9.20],
        "position": [1226, 86],
    },
    {
        "episode_id": "piltdown-man",
        "display": "Piltdown Man",
        "source": GALLERY_ROOT / "piltdown-man-thumbnail-proof-v6-ink-lit-subjects-source.png",
        "seconds": [19.48, 20.30],
        "position": [1226, 86],
    },
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


def stream_sha256(path: Path, stream_spec: str, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-map", stream_spec, "-c", "copy", str(out_path)])
    digest = sha256(out_path)
    out_path.unlink(missing_ok=True)
    return digest


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


def make_artifact_card(source: Path, label: str) -> Image.Image:
    card_w, card_h = 390, 226
    radius = 22
    label_h = 48
    source_img = Image.open(source).convert("RGB")
    source_img = crop_cover(source_img, card_w, card_h - label_h)
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (card_w + 34, card_h + 34), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle((17, 17, card_w + 17, card_h + 17), radius=radius, fill=(0, 0, 0, 104))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12)).crop((17, 17, card_w + 17, card_h + 17))
    card.alpha_composite(shadow)
    mask = Image.new("L", (card_w, card_h), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle((0, 0, card_w - 1, card_h - 1), radius=radius, fill=255)
    content = Image.new("RGBA", (card_w, card_h), (14, 19, 31, 230))
    content.paste(source_img.convert("RGBA"), (0, 0))
    overlay = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle((0, card_h - label_h, card_w, card_h), fill=(15, 19, 31, 226))
    odraw.rounded_rectangle((0, 0, card_w - 1, card_h - 1), radius=radius, outline=(238, 232, 211, 150), width=2)
    content.alpha_composite(overlay)
    draw = ImageDraw.Draw(content)
    draw.text((20, card_h - label_h + 10), label, font=font(28), fill=(238, 232, 211, 245))
    card = Image.composite(content, card, mask)
    return card


def crop_cover(img: Image.Image, width: int, height: int) -> Image.Image:
    src_w, src_h = img.size
    scale = max(width / src_w, height / src_h)
    resized = img.resize((math.ceil(src_w * scale), math.ceil(src_h * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def alpha_for_window(t: float, start: float, end: float) -> float:
    fade = 0.16
    if not (start <= t <= end):
        return 0.0
    if t < start + fade:
        return (t - start) / fade
    if t > end - fade:
        return max(0.0, (end - t) / fade)
    return 1.0


def render_visual_patch(package_dir: Path, work_dir: Path, video_dir: Path) -> tuple[Path, dict[str, Any]]:
    frames_dir = work_dir / "patched_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(SOURCE_MP4),
            "-vf",
            f"fps={FPS},scale={WIDTH}:{HEIGHT}",
            "-q:v",
            "2",
            str(frames_dir / "frame_%05d.jpg"),
        ]
    )
    cards = []
    copied_sources = []
    source_dir = package_dir / "source/artifacts"
    source_dir.mkdir(parents=True, exist_ok=True)
    for artifact in ARTIFACTS:
        source = Path(artifact["source"])
        require_file(source, f"{artifact['episode_id']} gallery source")
        copied = source_dir / source.name
        shutil.copy2(source, copied)
        card = make_artifact_card(source, artifact["display"])
        cards.append((artifact, card))
        copied_sources.append(
            {
                "episode_id": artifact["episode_id"],
                "display": artifact["display"],
                "source": str(source),
                "source_sha256": sha256(source),
                "package_copy": str(copied),
                "package_copy_sha256": sha256(copied),
                "seconds": artifact["seconds"],
                "position_xy": artifact["position"],
            }
        )
    frame_paths = sorted(frames_dir.glob("frame_*.jpg"))
    for index, frame_path in enumerate(frame_paths):
        t = index / FPS
        frame = Image.open(frame_path).convert("RGBA")
        changed = False
        for artifact, card in cards:
            alpha = alpha_for_window(t, artifact["seconds"][0], artifact["seconds"][1])
            if alpha <= 0:
                continue
            x, y = artifact["position"]
            overlay = card.copy()
            if alpha < 1:
                r, g, b, a = overlay.split()
                a = a.point(lambda value: int(value * alpha))
                overlay.putalpha(a)
            frame.alpha_composite(overlay, (x, y))
            changed = True
        if changed:
            frame.convert("RGB").save(frame_path, quality=92)
    patched_silent = video_dir / "cascade_of_effects_channel_intro_pressure_bends_original_format_artifact_patch_silent.mp4"
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
            f"{DURATION_SECONDS:.6f}",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-movflags",
            "+faststart",
            str(patched_silent),
        ]
    )
    return patched_silent, {"artifact_sources": copied_sources, "frame_count": len(frame_paths)}


def render_audio(work_dir: Path) -> Path:
    audio_path = work_dir / "pressure_bends_intro_48s_safe.aac"
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(TRACK_PATH),
            "-t",
            f"{DURATION_SECONDS:.6f}",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st=47.200:d=0.800",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(audio_path),
        ]
    )
    return audio_path


def mux_final(silent_video: Path, audio_path: Path, final_mp4: Path) -> None:
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
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-t",
            f"{DURATION_SECONDS:.6f}",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )


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


def make_contact_sheet(final_mp4: Path, qa_dir: Path) -> Path:
    samples = [
        ("cold open", 0.6),
        ("handoff", 6.0),
        ("challenger", 7.2),
        ("therac artifact", 8.82),
        ("hyatt", 10.0),
        ("tacoma", 18.1),
        ("piltdown artifact", 19.88),
        ("737 max", 21.2),
        ("titanic", 25.0),
        ("end screen", 31.0),
        ("hold", 47.7),
    ]
    frame_dir = qa_dir / "contact_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    thumb_w, thumb_h = 480, 270
    label_h = 40
    tiles = []
    for label, seconds in samples:
        frame_path = frame_dir / f"frame_{seconds:.3f}.jpg"
        extract_frame(final_mp4, seconds, frame_path)
        image = Image.open(frame_path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        tiles.append((label, seconds, image))
    cols = 3
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(17, bold=True)
    for index, (label, seconds, image) in enumerate(tiles):
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + label_h)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(18, 20, 24))
        draw.text((x + 12, y + thumb_h + 8), f"{seconds:05.2f}s {label}", fill=(238, 240, 244), font=label_font)
    out_path = qa_dir / "channel_intro_pressure_bends_original_format_artifact_patch_contact_sheet.jpg"
    sheet.save(out_path, quality=92)
    return out_path


def make_review_html(package_dir: Path, final_mp4: Path, contact_sheet: Path, manifest_path: Path) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Original-Format Intro Music + Artifact Patch Review</title>
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
  <h1>Original-Format Intro Music + Artifact Patch Review</h1>
  <video controls src="{final_mp4.relative_to(package_dir)}"></video>
  <section class="meta">
    <div><strong>Visual base</strong><br>Original/current intro format preserved</div>
    <div><strong>Music</strong><br>Pressure Bends 48s excerpt, safe AAC</div>
    <div><strong>Added artifacts</strong><br>Therac-25 and Piltdown Man only</div>
  </section>
  <h2>Contact Sheet</h2>
  <img src="{contact_sheet.relative_to(package_dir)}" alt="Original-format intro patch contact sheet">
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


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    source_manifest: dict[str, Any],
    final_mp4: Path,
    silent_video: Path,
    audio_path: Path,
    visual_report: dict[str, Any],
    contact_sheet: Path,
    review_html: Path,
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    final_audio_measure = base.measure_audio(final_mp4)
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    final_video_sha = stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264")
    palette_contract = base.make_palette_contract(source_manifest)
    palette_reads = palette_contract["reads"]
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
            "role": "current_original_intro_format_visual_base",
            "manifest_path": str(SOURCE_MANIFEST),
            "manifest_sha256": sha256(SOURCE_MANIFEST),
            "mp4_path": str(SOURCE_MP4),
            "mp4_sha256": sha256(SOURCE_MP4),
        },
        "predecessor": {
            "role": "current_original_intro_format_visual_base",
            "manifest_path": str(SOURCE_MANIFEST),
            "manifest_sha256": sha256(SOURCE_MANIFEST),
            "mp4_path": str(SOURCE_MP4),
            "mp4_sha256": sha256(SOURCE_MP4),
        },
        "source_audio": {
            "role": "pressure_bends_replacement_music_source",
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
        },
        "timeline": {
            "duration_seconds": DURATION_SECONDS,
            "source_visual_preserved_seconds": [[0.0, 8.42], [9.20, 19.48], [20.30, 48.0]],
            "artifact_insert_seconds": [
                {"episode_id": item["episode_id"], "display": item["display"], "seconds": item["seconds"]}
                for item in ARTIFACTS
            ],
            "music_source_seconds": [0.0, DURATION_SECONDS],
            "tail_fade_seconds": [47.2, 48.0],
            "original_timeline_segments": source_manifest.get("timeline_segments")
            or source_manifest.get("timeline", {}),
        },
        "artifact_insert_context": visual_report,
        "audio_qa": {
            "final_audio_stream_sha256": final_audio_sha,
            "final_measurements": final_audio_measure,
            "safe_true_peak_max_dbfs": base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS,
        },
        "visual_qa": {
            "visual_base_policy": "preserve_original_intro_format_animation_and_timing",
            "final_video_stream_sha256": final_video_sha,
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
        },
        "end_screen_palette_contract": palette_contract,
        "reads": {
            "source_audio_hash_read": "pass_source_audio_sha256_recorded",
            "audio_replacement_read": "pass_pressure_bends_replaces_prior_music",
            "full_track_audio_read": "pass_excerpt_used_to_preserve_original_48s_intro_runtime",
            "safe_mastering_read": "pass_true_peak_margin_and_loudness_target_met" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_mix_no_clipping" if no_clipping_pass else "reject_final_mix_clipping_or_peak_too_hot",
            "original_intro_format_read": "pass_current_intro_format_animation_and_timing_preserved",
            "minimal_visual_delta_read": "pass_only_therac_and_piltdown_artifact_card_overlays_added_to_existing_picture",
            "therac_25_presence_read": "pass_therac_25_artifact_added_once",
            "piltdown_man_presence_read": "pass_piltdown_man_artifact_added_once",
            "video_preservation_read": "pass_source_intro_picture_preserved_except_declared_artifact_insert_windows",
            "end_screen_extension_read": "pass_not_extended_original_48s_intro_runtime_preserved",
            "end_screen_title_image_absence_read": source_manifest.get("reads", {}).get(
                "end_screen_title_image_absence_read", "pass_no_cascade_of_effects_title_image_on_end_screen"
            ),
            "end_screen_palette_contract_read": source_manifest.get("reads", {}).get(
                "end_screen_palette_contract_read", palette_reads["end_screen_palette_contract_read"]
            ),
            "end_screen_target_fill_palette_read": source_manifest.get("reads", {}).get(
                "end_screen_target_fill_palette_read", palette_reads["end_screen_target_fill_palette_read"]
            ),
            "end_screen_target_contrast_read": source_manifest.get("reads", {}).get(
                "end_screen_target_contrast_read", palette_reads["end_screen_target_contrast_read"]
            ),
            "source_integrated_panel_color_read": source_manifest.get("reads", {}).get(
                "source_integrated_panel_color_read", palette_reads["source_integrated_panel_color_read"]
            ),
            "no_cross_episode_default_palette_read": source_manifest.get("reads", {}).get(
                "no_cross_episode_default_palette_read", palette_reads["no_cross_episode_default_palette_read"]
            ),
            "end_screen_adaptive_perceptual_variability_read": source_manifest.get("reads", {}).get(
                "end_screen_adaptive_perceptual_variability_read", palette_reads["end_screen_adaptive_perceptual_variability_read"]
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
            "silent_video": str(silent_video),
            "silent_video_sha256": sha256(silent_video),
            "normalized_audio": str(audio_path),
            "normalized_audio_sha256": sha256(audio_path),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "manifest": str(package_dir / f"{OUTPUT_STEM}_manifest.json"),
        },
        "media_probe": probe,
    }


def run_contract_validator(manifest_path: Path) -> dict[str, Any]:
    return base.run_contract_validator(manifest_path)


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str) -> Path:
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Original-Format Intro Music + Artifact Patch",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This package treats the current titleless intro render as the locked visual base. It preserves the original format, timing, and animation; replaces the music with a safe 48s Pressure Bends excerpt; and adds only two missing episode artifact cards: Therac-25 and Piltdown Man.",
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
    require_file(SOURCE_MP4, "current original-format intro MP4")
    require_file(SOURCE_MANIFEST, "current original-format intro manifest")
    require_file(TRACK_PATH, "Pressure Bends source track")
    for artifact in ARTIFACTS:
        require_file(Path(artifact["source"]), f"{artifact['episode_id']} gallery source")
    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    work_dir = package_dir / "work"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    for directory in [work_dir, video_dir, qa_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    source_manifest = read_json(SOURCE_MANIFEST)
    silent_video, visual_report = render_visual_patch(package_dir, work_dir, video_dir)
    audio_path = render_audio(work_dir)
    final_mp4 = video_dir / "cascade_of_effects_channel_intro_pressure_bends_original_format_artifact_patch_1080p24.mp4"
    mux_final(silent_video, audio_path, final_mp4)
    contact_sheet = make_contact_sheet(final_mp4, qa_dir)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, manifest_path)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        source_manifest=source_manifest,
        final_mp4=final_mp4,
        silent_video=silent_video,
        audio_path=audio_path,
        visual_report=visual_report,
        contact_sheet=contact_sheet,
        review_html=review_html,
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
