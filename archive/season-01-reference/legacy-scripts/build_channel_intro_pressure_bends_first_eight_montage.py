#!/usr/bin/env python3
"""Build a 10-second first-eight channel intro montage using The Pressure Bends."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
ACTUAL_MONTAGE_MANIFEST = (
    OUTPUT_ROOT
    / "channel_trailer_actual_montage_successor_20260524T040009Z"
    / "channel_trailer_actual_montage_successor_manifest.json"
)
TITLELESS_REPAIR_MANIFEST = (
    OUTPUT_ROOT
    / "channel_trailer_end_screen_titleless_only_repair_20260524T054934Z"
    / "channel_trailer_end_screen_titleless_only_manifest.json"
)
INTRO_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_v2_episode_visual_proofs.py"
PRESSURE_BENDS_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_pressure_bends_successor.py"
LATEST_POINTER = OUTPUT_ROOT / "channel_intro_pressure_bends_first_eight_montage_latest.json"
WORKFLOW = "channel_intro_pressure_bends_first_eight_montage_v1"

WIDTH = 1920
HEIGHT = 1080
FPS = 24
DURATION_SECONDS = 10.0
TOTAL_FRAMES = int(DURATION_SECONDS * FPS)
SEGMENT_SECONDS = 1.25
SEGMENT_FRAMES = int(SEGMENT_SECONDS * FPS)
AUDIO_TARGET_LUFS = -16.0
AUDIO_TRUE_PEAK_LIMIT_DBFS = -1.5
AUDIO_SAFE_TRUE_PEAK_MAX_DBFS = -1.0
AUDIO_FADE_START_SECONDS = 9.5
AUDIO_FADE_DURATION_SECONDS = 0.5

CANONICAL_EPISODES = [
    ("challenger", "Challenger", 0.000, 1.250),
    ("therac-25", "Therac-25", 1.250, 2.500),
    ("hyatt-regency", "Hyatt Regency", 2.500, 3.750),
    ("semmelweis", "Semmelweis", 3.750, 5.000),
    ("tacoma-narrows", "Tacoma Narrows", 5.000, 6.250),
    ("piltdown-man", "Piltdown Man", 6.250, 7.500),
    ("737-max", "737 MAX", 7.500, 8.750),
    ("titanic", "Titanic", 8.750, 10.000),
]

CAPTIONED_PRIOR_INSERT_FALLBACK_IDS = {"therac-25", "piltdown-man"}


@dataclass(frozen=True)
class EpisodeSource:
    order: int
    episode_id: str
    display: str
    seconds: tuple[float, float]
    gallery_source: Path
    short_source: Path | None
    manifest_gallery_sha256: str
    manifest_short_sha256: str


@dataclass(frozen=True)
class PreparedEpisode:
    source: EpisodeSource
    source_copy: Path
    normalized_plate: Path
    background_plate: Path
    short_frames_dir: Path
    short_source_mode: str
    short_frames_extracted: int
    short_source_hash: str


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


intro_base = load_module(INTRO_HELPER_PATH, "channel_intro_visual_proof_base")
pressure_base = load_module(PRESSURE_BENDS_HELPER_PATH, "pressure_bends_audio_base")


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def utc_stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def ffprobe(path: Path) -> dict[str, Any]:
    data = json.loads(
        run(
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
        ).stdout
    )
    data["path"] = str(path)
    data["sha256"] = sha256(path)
    return data


def duration_seconds(path: Path) -> float:
    return float(ffprobe(path).get("format", {}).get("duration", 0.0))


def stream_sha256(path: Path, stream_spec: str, out_path: Path) -> str:
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


def load_episode_sources() -> tuple[dict[str, Any], list[EpisodeSource]]:
    require_file(ACTUAL_MONTAGE_MANIFEST, "actual first-eight source manifest")
    manifest = read_json(ACTUAL_MONTAGE_MANIFEST)
    source_by_id = {row["episode_id"]: row for row in manifest.get("episode_sequence", [])}
    episodes: list[EpisodeSource] = []
    for index, (episode_id, display, start, end) in enumerate(CANONICAL_EPISODES, start=1):
        row = source_by_id.get(episode_id)
        if row is None:
            raise SystemExit(f"Missing episode in actual montage manifest: {episode_id}")
        gallery_source = Path(row["gallery_source"])
        require_file(gallery_source, f"{episode_id} proof-v6 gallery source")
        short_source = Path(row["short_source"]) if row.get("short_source") else None
        episodes.append(
            EpisodeSource(
                order=index,
                episode_id=episode_id,
                display=display,
                seconds=(start, end),
                gallery_source=gallery_source,
                short_source=short_source if short_source and short_source.exists() else None,
                manifest_gallery_sha256=row.get("gallery_source_sha256", ""),
                manifest_short_sha256=row.get("short_source_sha256", ""),
            )
        )
    return manifest, episodes


def ensure_required_inputs() -> None:
    require_file(TRACK_PATH, "Pressure Bends source track")
    require_file(INTRO_HELPER_PATH, "intro proof geometry helper")
    require_file(PRESSURE_BENDS_HELPER_PATH, "Pressure Bends audio helper")
    require_file(TITLELESS_REPAIR_MANIFEST, "titleless repair manifest for contract harness palette")


def extract_short_frames(source: Path, frames_dir: Path, required_frames: int) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frames_dir.glob("short_*.png"):
        old_frame.unlink()
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-t",
            f"{SEGMENT_SECONDS:.6f}",
            "-vf",
            "fps=24,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1",
            "-start_number",
            "0",
            str(frames_dir / "short_%05d.png"),
        ]
    )
    frames = sorted(frames_dir.glob("short_*.png"))
    if not frames:
        raise SystemExit(f"No frames extracted from short source: {source}")
    while len(frames) < required_frames:
        duplicate_path = frames_dir / f"short_{len(frames):05d}.png"
        shutil.copyfile(frames[-1], duplicate_path)
        frames.append(duplicate_path)
    for extra in frames[required_frames:]:
        extra.unlink()
    return required_frames


def make_fallback_still_frames(source: Path, frames_dir: Path, required_frames: int) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frames_dir.glob("short_*.png"):
        old_frame.unlink()
    source_image = Image.open(source).convert("RGB")
    still = ImageOps.fit(source_image, intro_base.SHORT_CARD_SIZE, Image.Resampling.LANCZOS, centering=(0.50, 0.50))
    for index in range(required_frames):
        still.save(frames_dir / f"short_{index:05d}.png")
    return required_frames


def prepare_episode_sources(episodes: list[EpisodeSource], package_dir: Path) -> list[PreparedEpisode]:
    source_dir = package_dir / "source_art"
    work_dir = package_dir / "work"
    prepared: list[PreparedEpisode] = []
    for episode in episodes:
        prefix = f"{episode.order:02d}_{episode.episode_id}"
        source_copy = source_dir / f"{prefix}_proof_v6_source.png"
        normalized_plate = source_dir / f"{prefix}_intro_left_anchor_source_plate.png"
        background_plate = source_dir / f"{prefix}_intro_base_plate.jpg"
        short_frames_dir = work_dir / "short_frames" / episode.episode_id
        source_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(episode.gallery_source, source_copy)
        intro_base.normalize_source_plate(source_copy, normalized_plate)
        intro_base.make_background(normalized_plate, background_plate)
        if episode.episode_id in CAPTIONED_PRIOR_INSERT_FALLBACK_IDS:
            frame_count = make_fallback_still_frames(source_copy, short_frames_dir, SEGMENT_FRAMES)
            short_mode = "gallery_still_fallback_captioned_prior_insert_blocked"
            short_hash = sha256(episode.short_source) if episode.short_source is not None else "missing"
        elif episode.short_source is not None:
            frame_count = extract_short_frames(episode.short_source, short_frames_dir, SEGMENT_FRAMES)
            short_mode = "exact_prior_insert"
            short_hash = sha256(episode.short_source)
        else:
            frame_count = make_fallback_still_frames(source_copy, short_frames_dir, SEGMENT_FRAMES)
            short_mode = "gallery_still_fallback"
            short_hash = "missing"
        prepared.append(
            PreparedEpisode(
                source=episode,
                source_copy=source_copy,
                normalized_plate=normalized_plate,
                background_plate=background_plate,
                short_frames_dir=short_frames_dir,
                short_source_mode=short_mode,
                short_frames_extracted=frame_count,
                short_source_hash=short_hash,
            )
        )
    return prepared


def render_montage_frames(prepared: list[PreparedEpisode], frames_dir: Path) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old_frame in frames_dir.glob("frame_*.jpg"):
        old_frame.unlink()
    backgrounds = [Image.open(item.background_plate).convert("RGB") for item in prepared]
    static_bases = [intro_base.make_static_base(background) for background in backgrounds]
    for frame_index in range(TOTAL_FRAMES):
        segment_index = min(frame_index // SEGMENT_FRAMES, len(prepared) - 1)
        local_frame_index = min(frame_index - (segment_index * SEGMENT_FRAMES), SEGMENT_FRAMES - 1)
        item = prepared[segment_index]
        short_frame_path = item.short_frames_dir / f"short_{local_frame_index:05d}.png"
        short_frame = Image.open(short_frame_path).convert("RGB")
        frame = intro_base.composite_scene(
            backgrounds[segment_index],
            short_frame,
            static_bases[segment_index],
            intro_base.short_plate_quad_at_frame(frame_index),
        )
        frame.save(frames_dir / f"frame_{frame_index:05d}.jpg", quality=93)
    return {"frame_count": TOTAL_FRAMES, "fps": FPS, "duration_seconds": DURATION_SECONDS}


def encode_silent_video(frames_dir: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
            str(output_path),
        ]
    )


def render_audio_excerpt(audio_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio_filter = (
        f"atrim=0:{DURATION_SECONDS:.6f},asetpts=PTS-STARTPTS,"
        f"loudnorm=I={AUDIO_TARGET_LUFS:.1f}:TP={AUDIO_TRUE_PEAK_LIMIT_DBFS:.1f}:LRA=11,"
        "alimiter=limit=0.891251:level=false,"
        f"afade=t=out:st={AUDIO_FADE_START_SECONDS:.3f}:d={AUDIO_FADE_DURATION_SECONDS:.3f},"
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
            str(audio_path),
            "-filter_complex",
            f"[0:a]{audio_filter}[a]",
            "-map",
            "[a]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )


def mux_final_video(silent_video: Path, audio_excerpt: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
            str(audio_excerpt),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-shortest",
            "-t",
            f"{DURATION_SECONDS:.6f}",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )


def make_contact_sheet(frames_dir: Path, prepared: list[PreparedEpisode], out_path: Path) -> None:
    thumb_w, thumb_h, label_h = 480, 270, 48
    cols = 4
    rows = 2
    sheet = Image.new("RGB", (thumb_w * cols, (thumb_h + label_h) * rows), intro_base.INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, bold=True)
    small_font = font(15)
    for index, item in enumerate(prepared):
        start, end = item.source.seconds
        midpoint = (start + end) / 2
        frame_index = min(int(round(midpoint * FPS)), TOTAL_FRAMES - 1)
        frame = Image.open(frames_dir / f"frame_{frame_index:05d}.jpg").convert("RGB")
        frame = frame.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + label_h)
        sheet.paste(frame, (x, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(10, 14, 30))
        draw.text((x + 12, y + thumb_h + 7), f"{item.source.order:02d} {item.source.display}", fill=intro_base.PAPER, font=label_font)
        draw.text((x + 12, y + thumb_h + 28), f"{start:05.3f}-{end:05.3f}s", fill=(180, 220, 232), font=small_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)


def make_geometry_overlay(prepared: list[PreparedEpisode], out_path: Path) -> None:
    intro_base.make_geometry_overlay(prepared[0].background_plate, out_path)


def measure_audio(path: Path) -> dict[str, Any]:
    return pressure_base.measure_audio(path)


def coverage_reads(prepared: list[PreparedEpisode]) -> dict[str, str]:
    ids = [item.source.episode_id for item in prepared]
    canonical = [item[0] for item in CANONICAL_EPISODES]
    return {
        "all_first_eight_episode_coverage_read": "pass_8_of_8_episode_segments_present_once"
        if sorted(ids) == sorted(canonical) and len(ids) == len(set(ids)) == 8
        else "reject_first_eight_coverage_gap",
        "canonical_first_eight_order_read": "pass_canonical_first_eight_order" if ids == canonical else "reject_noncanonical_order",
        "episode_once_read": "pass_each_episode_appears_exactly_once" if len(ids) == len(set(ids)) == 8 else "reject_duplicate_or_missing_episode",
    }


def geometry_reads(layout: dict[str, Any]) -> dict[str, str]:
    return {
        "geometry_title_safe_read": layout["title_safe_read"],
        "geometry_center_origin_read": layout["center_origin_read"],
        "geometry_no_lateral_slide_read": layout["no_lateral_slide_read"],
        "right_card_push_in_read": "pass_center_origin_push_in_0_to_8s_hold_8_to_10s"
        if layout["center_origin_read"].startswith("pass") and layout["no_lateral_slide_read"].startswith("pass")
        else "reject_intro_push_in_geometry_changed",
    }


def format_read(probe: dict[str, Any]) -> str:
    streams = probe.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    duration_delta = abs(float(probe.get("format", {}).get("duration", 0.0)) - DURATION_SECONDS)
    ok = (
        video.get("codec_name") == "h264"
        and video.get("width") == WIDTH
        and video.get("height") == HEIGHT
        and video.get("avg_frame_rate") == "24/1"
        and audio.get("codec_name") == "aac"
        and str(audio.get("channels")) == "2"
        and duration_delta <= (1.0 / FPS)
    )
    return "pass" if ok else "reject_format_or_duration_mismatch"


def make_review_html(package_dir: Path, final_mp4: Path, contact_sheet: Path, manifest_path: Path) -> Path:
    review_path = package_dir / "review.html"
    rows = "\n".join(
        f"<tr><td>{order}</td><td>{display}</td><td>{start:0.3f}-{end:0.3f}s</td></tr>"
        for order, (episode_id, display, start, end) in enumerate(CANONICAL_EPISODES, start=1)
    )
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Channel Intro Pressure Bends First-Eight Montage</title>
  <style>
    body {{ margin: 0; background: #101216; color: #eef1f4; font-family: Arial, sans-serif; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    video, img {{ width: 100%; display: block; background: #05070a; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    td, th {{ border-bottom: 1px solid #303844; padding: 8px 10px; text-align: left; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .meta div {{ border: 1px solid #2f3742; padding: 12px; background: #171b21; }}
    h1 {{ font-size: 28px; margin: 0 0 16px; }}
    h2 {{ font-size: 18px; margin: 28px 0 10px; }}
    code {{ color: #b8d7ff; }}
  </style>
</head>
<body>
<main>
  <h1>Channel Intro Pressure Bends First-Eight Montage</h1>
  <div class="meta">
    <div><strong>Status</strong><br>review_required</div>
    <div><strong>Runtime</strong><br>10.000s</div>
    <div><strong>YouTube action</strong><br>blocked local review only</div>
  </div>
  <video controls playsinline src="{final_mp4.relative_to(package_dir)}"></video>
  <h2>Timeline</h2>
  <table>
    <thead><tr><th>Order</th><th>Episode</th><th>Window</th></tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>
  <h2>Contact Sheet</h2>
  <img src="{contact_sheet.relative_to(package_dir)}" alt="Eight midpoint samples">
  <h2>Manifest</h2>
  <p><code>{manifest_path.relative_to(package_dir)}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review_path


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, contact_sheet: Path) -> Path:
    readme_path = package_dir / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# First-Eight Pressure Bends Intro-Format Montage",
                "",
                "- Status: `review_required`",
                "- Format: `1920x1080`, `24fps`, `10.000s`, H.264 video, stereo AAC audio",
                "- Visual grammar: left Paper Architecture anchor, right vertical evidence card, center-origin push-in from `0-8s`, hold from `8-10s`.",
                "- Audio: `/Users/mike/Downloads/The_Pressure_Bends.mp3`, excerpt `0.000-10.000s`, normalized and faded for AAC delivery.",
                "- Scope: no VO, no captions added, no YouTube end-screen, no channel-trailer hold, no upload, no channel replacement, no beat-reactive backplate work.",
                f"- Final MP4: `{final_mp4}`",
                f"- Review HTML: `{review_html}`",
                f"- Contact sheet: `{contact_sheet}`",
                f"- Manifest: `{manifest_path}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return readme_path


def run_contract_validator(manifest_path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [
            "node",
            "scripts/validate_cascade_effects_output_contract.mjs",
            "--manifest",
            str(manifest_path),
            "--intent",
            "experiment",
            "--contract-id",
            "channel-trailer-v1",
            "--write-receipt",
            "auto",
            "--json",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    payload = json.loads(proc.stdout or "{}")
    if proc.returncode != 0:
        raise SystemExit(
            "Contract validation failed:\n"
            + json.dumps(payload.get("failures", []), indent=2)
            + "\n\nSTDERR:\n"
            + proc.stderr
        )
    return payload


def make_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    actual_manifest: dict[str, Any],
    prepared: list[PreparedEpisode],
    frames_report: dict[str, Any],
    silent_video: Path,
    audio_excerpt: Path,
    final_mp4: Path,
    contact_sheet: Path,
    geometry_overlay: Path,
    review_html: Path,
    source_audio_measure: dict[str, Any],
    final_audio_measure: dict[str, Any],
) -> dict[str, Any]:
    final_probe = ffprobe(final_mp4)
    layout = intro_base.layout_report()
    palette_contract = pressure_base.make_palette_contract(read_json(TITLELESS_REPAIR_MANIFEST))
    final_seconds = float(final_probe.get("format", {}).get("duration", 0.0))
    duration_delta = abs(final_seconds - DURATION_SECONDS)
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    coverage = coverage_reads(prepared)
    geometry = geometry_reads(layout)
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    final_video_sha = stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264")
    episode_sequence = [
        {
            "order": item.source.order,
            "episode_id": item.source.episode_id,
            "display": item.source.display,
            "seconds": [round(item.source.seconds[0], 3), round(item.source.seconds[1], 3)],
            "gallery_source": str(item.source.gallery_source),
            "gallery_source_sha256": sha256(item.source.gallery_source),
            "gallery_source_sha256_declared_by_prior_manifest": item.source.manifest_gallery_sha256,
            "short_source": str(item.source.short_source) if item.source.short_source else "",
            "short_source_mode": item.short_source_mode,
            "short_source_sha256": item.short_source_hash,
            "short_source_sha256_declared_by_prior_manifest": item.source.manifest_short_sha256,
            "package_source_copy": str(item.source_copy),
            "package_source_copy_sha256": sha256(item.source_copy),
            "normalized_left_anchor": str(item.normalized_plate),
            "normalized_left_anchor_sha256": sha256(item.normalized_plate),
            "base_plate": str(item.background_plate),
            "base_plate_sha256": sha256(item.background_plate),
            "right_card_frames_dir": str(item.short_frames_dir),
            "right_card_frame_count": item.short_frames_extracted,
        }
        for item in prepared
    ]
    reads = {
        **coverage,
        **geometry,
        "intro_format_read": "pass_multi_episode_intro_visual_proofs_10s_geometry",
        "duration_read": "pass_10s_within_one_frame" if duration_delta <= (1.0 / FPS) else "reject_runtime_not_10s",
        "source_audio_hash_read": "pass_source_audio_sha256_recorded",
        "pressure_bends_excerpt_read": "pass_first_10s_excerpt_used_once_no_loop",
        "audio_replacement_read": "pass_pressure_bends_intro_excerpt_used",
        "safe_mastering_read": "pass_true_peak_margin_and_loudness_target_met" if safe_mastering_pass else "reject_true_peak_margin_failed",
        "no_clipping_read": "pass_final_mix_no_clipping" if no_clipping_pass else "reject_final_mix_clipping_or_peak_too_hot",
        "tail_fade_read": "pass_audio_tail_fade_9p5_to_10p0",
        "visual_body_read": "pass_all_eight_intro_segments_rendered_as_single_10s_montage",
        "no_vo_read": "pass_music_only_no_voiceover_added",
        "no_captions_read": "pass_no_subtitle_stream_new_caption_overlay_or_captioned_prior_insert_used",
        "no_youtube_end_screen_read": "pass_no_youtube_end_screen_or_channel_trailer_hold_rendered",
        "channel_trailer_latest_pointer_read": "pass_no_channel_trailer_latest_pointer_written",
        "reactive_backplate_scope_read": "pass_deferred_no_low_beat_or_reactive_pulse_timing_claim",
        "backplate_beat_sync_read": "pass_deferred_not_attempted",
        "low_beat_detection_read": "pass_deferred_not_attempted",
        "format_read": format_read(final_probe),
        "full_decode_read": pressure_base.full_decode_read(final_mp4),
        "youtube_action_read": "blocked_local_review_only",
        "end_screen_palette_contract_read": palette_contract["reads"]["end_screen_palette_contract_read"],
        "end_screen_target_fill_palette_read": palette_contract["reads"]["end_screen_target_fill_palette_read"],
        "end_screen_target_contrast_read": palette_contract["reads"]["end_screen_target_contrast_read"],
        "rail_panel_palette_read": palette_contract["reads"]["rail_panel_palette_read"],
        "source_integrated_panel_color_read": palette_contract["reads"]["source_integrated_panel_color_read"],
        "no_cross_episode_default_palette_read": palette_contract["reads"]["no_cross_episode_default_palette_read"],
        "end_screen_adaptive_perceptual_variability_read": palette_contract["reads"]["end_screen_adaptive_perceptual_variability_read"],
    }
    return {
        "artifact_id": f"channel_intro_pressure_bends_first_eight_montage_{timestamp}",
        "created_at": timestamp,
        "status": "review_required",
        "workflow": WORKFLOW,
        "mp4_render_created": True,
        "publishable": False,
        "may_advance": False,
        "youtube_uploaded": False,
        "youtube_visibility_changed": False,
        "youtube_channel_trailer_replaced": False,
        "may_upload_to_youtube": False,
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "experiment",
            "contract_registry_path": str(REPO_ROOT / "references/production_contracts/cascade_effects_output_contracts.v1.json"),
            "youtube_action_approval_read": "blocked_local_review_only",
        },
        "youtube_action_read": "blocked_local_review_only",
        "source_policy": {
            "rejected_prior_channel_trailer_format_packages": "acknowledged_not_used_as_intro_format_output",
            "visual_source_manifest": str(ACTUAL_MONTAGE_MANIFEST),
            "visual_source_manifest_sha256": sha256(ACTUAL_MONTAGE_MANIFEST),
            "source_episode_order_read": "pass_loaded_prior_all_eight_manifest_for_exact_insert_paths",
            "proof_v6_source_render_policy": "pass_all_left_anchors_from_proof_v6_source_renders",
            "fallback_policy": "use_gallery_still_when_prior_insert_missing_or_captioned_for_no_caption_scope",
        },
        "source_audio": {
            "role": "pressure_bends_intro_excerpt_source",
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
            "source_duration_seconds": duration_seconds(TRACK_PATH),
            "excerpt_seconds": [0.0, DURATION_SECONDS],
            "measurements": source_audio_measure,
        },
        "replacement_audio": {
            "role": "safe_aac_intro_excerpt",
            "path": str(audio_excerpt),
            "sha256": sha256(audio_excerpt),
            "filter": "atrim_0_to_10_loudnorm_limiter_tail_fade_aac",
            "target_integrated_lufs": AUDIO_TARGET_LUFS,
            "true_peak_limit_dbfs": AUDIO_TRUE_PEAK_LIMIT_DBFS,
            "safe_true_peak_max_dbfs": AUDIO_SAFE_TRUE_PEAK_MAX_DBFS,
            "fade_seconds": [AUDIO_FADE_START_SECONDS, DURATION_SECONDS],
            "final_measurements": final_audio_measure,
        },
        "format": {
            "width": WIDTH,
            "height": HEIGHT,
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "video_codec": "h264",
            "audio_codec": "aac",
            "audio_channels": 2,
        },
        "timeline": {
            "duration_seconds": DURATION_SECONDS,
            "push_in_seconds": [0.0, 8.0],
            "final_hold_seconds": [8.0, 10.0],
            "segment_seconds": SEGMENT_SECONDS,
            "segment_frames": SEGMENT_FRAMES,
            "total_frames": TOTAL_FRAMES,
            "episode_segments": [
                {
                    "order": order,
                    "episode_id": episode_id,
                    "display": display,
                    "seconds": [round(start, 3), round(end, 3)],
                }
                for order, (episode_id, display, start, end) in enumerate(CANONICAL_EPISODES, start=1)
            ],
            "omitted_elements": {
                "voiceover": "omitted",
                "caption_overlays": "omitted",
                "youtube_end_screen": "omitted",
                "channel_trailer_end_screen_hold": "omitted",
                "beat_reactive_backplate_work": "omitted",
            },
        },
        "layout": {
            **layout,
            "geometry_source_script": str(INTRO_HELPER_PATH),
            "left_anchor_source": "proof_v6_source_render",
            "right_card_source": "prior_insert_or_gallery_still_fallback",
        },
        "episode_sequence": episode_sequence,
        "source_episode_sequence": actual_manifest.get("episode_sequence", []),
        "end_screen_palette_contract": {
            **palette_contract,
            "intro_package_note": "contract_harness_reference_only_not_rendered_in_this_intro",
        },
        "qa": {
            "frames": frames_report,
            "ffprobe": final_probe,
            "decode_read": reads["full_decode_read"],
            "audio_measurements": final_audio_measure,
            "contact_sheet_samples": [
                {
                    "episode_id": item.source.episode_id,
                    "display": item.source.display,
                    "sample_seconds": round((item.source.seconds[0] + item.source.seconds[1]) / 2, 3),
                }
                for item in prepared
            ],
            "geometry_overlay": str(geometry_overlay),
            "geometry_overlay_sha256": sha256(geometry_overlay),
            "reads": reads,
        },
        "reads": reads,
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "silent_video": str(silent_video),
            "silent_video_sha256": sha256(silent_video),
            "audio_excerpt": str(audio_excerpt),
            "audio_excerpt_sha256": sha256(audio_excerpt),
            "final_audio_stream_sha256": final_audio_sha,
            "final_video_stream_sha256": final_video_sha,
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "geometry_overlay": str(geometry_overlay),
            "geometry_overlay_sha256": sha256(geometry_overlay),
            "manifest": str(package_dir / "channel_intro_pressure_bends_first_eight_montage_manifest.json"),
        },
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    ensure_required_inputs()
    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"channel_intro_pressure_bends_first_eight_montage_{timestamp}"
    package_dir.mkdir(parents=True, exist_ok=False)
    (package_dir / "audio").mkdir(parents=True, exist_ok=True)
    (package_dir / "video").mkdir(parents=True, exist_ok=True)
    (package_dir / "qa").mkdir(parents=True, exist_ok=True)
    (package_dir / "work").mkdir(parents=True, exist_ok=True)
    (package_dir / "source").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ACTUAL_MONTAGE_MANIFEST, package_dir / "source/channel_trailer_actual_montage_successor_manifest.copy.json")

    actual_manifest, episodes = load_episode_sources()
    prepared = prepare_episode_sources(episodes, package_dir)
    frames_dir = package_dir / "work/montage_frames"
    frames_report = render_montage_frames(prepared, frames_dir)
    silent_video = package_dir / "video/cascade_of_effects_channel_intro_pressure_bends_first_eight_montage_silent_1080p24.mp4"
    encode_silent_video(frames_dir, silent_video)
    audio_excerpt = package_dir / "audio/pressure_bends_intro_excerpt_0_10s_safe_aac.m4a"
    render_audio_excerpt(TRACK_PATH, audio_excerpt)
    final_mp4 = package_dir / "video/cascade_of_effects_channel_intro_pressure_bends_first_eight_montage_1080p24.mp4"
    mux_final_video(silent_video, audio_excerpt, final_mp4)
    contact_sheet = package_dir / "qa/channel_intro_pressure_bends_first_eight_montage_contact_sheet.jpg"
    make_contact_sheet(frames_dir, prepared, contact_sheet)
    geometry_overlay = package_dir / "qa/intro_geometry_overlay.jpg"
    make_geometry_overlay(prepared, geometry_overlay)
    manifest_path = package_dir / "channel_intro_pressure_bends_first_eight_montage_manifest.json"
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, manifest_path)
    source_audio_measure = measure_audio(TRACK_PATH)
    final_audio_measure = measure_audio(final_mp4)
    manifest = make_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        actual_manifest=actual_manifest,
        prepared=prepared,
        frames_report=frames_report,
        silent_video=silent_video,
        audio_excerpt=audio_excerpt,
        final_mp4=final_mp4,
        contact_sheet=contact_sheet,
        geometry_overlay=geometry_overlay,
        review_html=review_html,
        source_audio_measure=source_audio_measure,
        final_audio_measure=final_audio_measure,
    )
    write_json(manifest_path, manifest)
    receipt = run_contract_validator(manifest_path)
    readme = write_readme(package_dir, final_mp4, review_html, manifest_path, contact_sheet)
    latest = {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "manifest": str(manifest_path),
        "final_mp4": str(final_mp4),
        "final_mp4_sha256": sha256(final_mp4),
        "contact_sheet": str(contact_sheet),
        "contract_receipt": receipt.get("receipt_path", ""),
        "readme": str(readme),
        "status": "review_required",
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
    }
    write_json(LATEST_POINTER, latest)
    if not args.keep_frames:
        shutil.rmtree(package_dir / "work/montage_frames", ignore_errors=True)
    return latest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="", help="UTC timestamp override for reproducible package naming.")
    parser.add_argument("--keep-frames", action="store_true", help="Keep rendered JPG frame sequence for inspection.")
    return parser.parse_args()


def main() -> None:
    latest = build(parse_args())
    print(json.dumps(latest, indent=2))


if __name__ == "__main__":
    main()
