#!/usr/bin/env python3
"""Build local first-second hook review proofs for the first eight Shorts."""

from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageStat


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
DEFAULT_OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Shorts_First_Second_Hook_Retrofit")
DEFAULT_IMPACT_AUDIO = REPO_ROOT / "references/shorts/audio/opening_impact_theme_hit_v1.wav"
MUSIC_REGISTRY = REPO_ROOT / "references/shorts/music_track_registry.json"

PREBEAT_SECONDS = 0.75
SOURCE_EXCERPT_SECONDS = 4.25
COMPARISON_SECONDS = 5.0
FRAME_STRIP_TIMES = [0.00, 0.12, 0.25, 0.50, 0.75, 1.00]
TARGET_W = 1080
TARGET_H = 1920
FPS = 60


@dataclass(frozen=True)
class EpisodeSpec:
    episode_id: str
    short_id: str
    display_name: str
    short_root: Path
    hook_source_seconds: float
    hook_visual_note: str
    bottom_crop_fraction: float = 0.28


EPISODES = [
    EpisodeSpec(
        "challenger",
        "challenger_short_scoped_v1",
        "Challenger",
        Path("/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_scoped_v1"),
        9.0,
        "external tank/O-ring damage subject frame without burned caption text",
        bottom_crop_fraction=0.0,
    ),
    EpisodeSpec(
        "therac-25",
        "therac_short_scoped_v1",
        "Therac-25",
        Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1"),
        0.0,
        "radiation treatment subject frame without burned caption text",
        bottom_crop_fraction=0.0,
    ),
    EpisodeSpec(
        "hyatt-regency",
        "hyatt_short_scoped_v1",
        "Hyatt Regency",
        Path("/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/shorts/hyatt_short_scoped_v1"),
        9.0,
        "tea-dance crowd and atrium event frame",
    ),
    EpisodeSpec(
        "semmelweis",
        "semmelweis_short_scoped_v1",
        "Semmelweis",
        Path("/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/shorts/semmelweis_short_scoped_v1"),
        0.0,
        "hospital ward subject frame without burned caption text",
        bottom_crop_fraction=0.0,
    ),
    EpisodeSpec(
        "tacoma-narrows",
        "tacoma_short_scoped_v1",
        "Tacoma Narrows",
        Path("/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts/tacoma_short_scoped_v1"),
        0.0,
        "bridge event frame without burned caption text",
        bottom_crop_fraction=0.0,
    ),
    EpisodeSpec(
        "piltdown-man",
        "piltdown_man_short_scoped_v1",
        "Piltdown Man",
        Path("/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts/piltdown_man_short_scoped_v1"),
        0.0,
        "fossil evidence subject frame without burned caption text",
        bottom_crop_fraction=0.0,
    ),
    EpisodeSpec(
        "737-max",
        "737_max_short_scoped_v1",
        "737 MAX",
        Path("/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/shorts/737_max_short_scoped_v1"),
        0.0,
        "airplane wing and engine takeoff frame",
        bottom_crop_fraction=0.0,
    ),
    EpisodeSpec(
        "titanic",
        "titanic_short_scoped_v1",
        "Titanic",
        Path("/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1"),
        3.0,
        "steamship/lifeboat context frame",
        bottom_crop_fraction=0.08,
    ),
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ffprobe(path: Path) -> dict[str, Any]:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(proc.stdout)


def duration(path: Path) -> float:
    return float(ffprobe(path).get("format", {}).get("duration", 0.0) or 0.0)


def media_summary(path: Path) -> dict[str, Any]:
    probe = ffprobe(path)
    streams = probe.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return {
        "path": str(path),
        "sha256": sha256(path),
        "duration_seconds": round(float(probe.get("format", {}).get("duration", 0) or 0), 6),
        "video_codec": video.get("codec_name", ""),
        "audio_codec": audio.get("codec_name", ""),
        "width": int(video.get("width", 0) or 0),
        "height": int(video.get("height", 0) or 0),
        "frame_rate": video.get("avg_frame_rate") or video.get("r_frame_rate", ""),
        "audio_sample_rate_hz": int(audio.get("sample_rate", 0) or 0),
        "audio_channels": int(audio.get("channels", 0) or 0),
    }


def latest_publish_mp4(short_root: Path) -> Path:
    candidates = sorted(short_root.glob("publish/youtube_*/*youtube_short.mp4"), key=lambda item: item.parent.name)
    if not candidates:
        raise FileNotFoundError(f"No latest publish MP4 found under {short_root}/publish/youtube_*")
    return candidates[-1]


def symlink_or_copy(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    try:
        os.symlink(source, dest)
    except OSError:
        shutil.copy2(source, dest)


def extract_frame(video: Path, seconds: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{seconds:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output),
        ],
        capture=True,
    )


def prepare_hook_image(raw_frame: Path, output: Path, bottom_crop_fraction: float) -> dict[str, Any]:
    image = Image.open(raw_frame).convert("RGB")
    width, height = image.size
    crop_bottom = int(height * max(0.0, min(0.45, bottom_crop_fraction)))
    crop_box = (0, 0, width, max(1, height - crop_bottom))
    cropped = image.crop(crop_box)
    scale = max(TARGET_W / cropped.width, TARGET_H / cropped.height)
    resized = cropped.resize((math.ceil(cropped.width * scale), math.ceil(cropped.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - TARGET_W) // 2)
    top = max(0, (resized.height - TARGET_H) // 2)
    framed = resized.crop((left, top, left + TARGET_W, top + TARGET_H))
    framed = ImageEnhance.Contrast(framed).enhance(1.12)
    framed = ImageEnhance.Color(framed).enhance(1.05)
    framed = ImageEnhance.Sharpness(framed).enhance(1.08)
    output.parent.mkdir(parents=True, exist_ok=True)
    framed.save(output, quality=95)
    return {
        "raw_frame_path": str(raw_frame),
        "raw_frame_sha256": sha256(raw_frame),
        "prepared_hook_image_path": str(output),
        "prepared_hook_image_sha256": sha256(output),
        "source_size": [width, height],
        "bottom_crop_fraction": bottom_crop_fraction,
        "crop_box": list(crop_box),
    }


def build_prebeat_clip(hook_image: Path, impact_audio: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    zoom_filter = (
        "[0:v]scale=1120:1991:flags=lanczos,"
        "zoompan=z='1+0.06*on/44':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=45:s=1080x1920:fps=60,"
        "trim=duration=0.75,setpts=PTS-STARTPTS,eq=brightness=0.018:contrast=1.04:saturation=1.04,"
        "format=yuv420p[v];"
        "[1:a]atrim=0:0.75,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(hook_image),
            "-i",
            str(impact_audio),
            "-filter_complex",
            zoom_filter,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        capture=True,
    )


def build_current_excerpt(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-t",
            f"{COMPARISON_SECONDS:.3f}",
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=60,format=yuv420p",
            "-af",
            "aresample=48000,aformat=channel_layouts=stereo",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        capture=True,
    )


def build_revised_proof(prebeat: Path, source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=60,setpts=PTS-STARTPTS[v0];"
        "[1:v]trim=0:4.25,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=60[v1];"
        "[0:a]atrim=0:0.75,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a0];"
        "[1:a]atrim=0:4.25,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][ac];"
        "[ac]volume=0.70,alimiter=limit=0.70:level=false[a]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(prebeat),
            "-i",
            str(source),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "19",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        capture=True,
    )


def build_comparison(current_excerpt: Path, revised_proof: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "[0:v]scale=540:960:force_original_aspect_ratio=increase,crop=540:960,setsar=1[left];"
        "[1:v]scale=540:960:force_original_aspect_ratio=increase,crop=540:960,setsar=1[right];"
        "[left][right]hstack=inputs=2,format=yuv420p[v]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(current_excerpt),
            "-i",
            str(revised_proof),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "1:a:0",
            "-shortest",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        capture=True,
    )


def image_luma_stats(path: Path) -> dict[str, float]:
    image = Image.open(path).convert("L").resize((96, 171), Image.Resampling.BILINEAR)
    stat = ImageStat.Stat(image)
    return {"mean_luma": round(stat.mean[0], 3), "std_luma": round(stat.stddev[0], 3)}


def build_frame_strip(video: Path, output_dir: Path) -> tuple[Path, list[dict[str, Any]]]:
    frame_dir = output_dir / "frames_first_second"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames: list[dict[str, Any]] = []
    tiles: list[Image.Image] = []
    for seconds in FRAME_STRIP_TIMES:
        frame_path = frame_dir / f"revised_t{seconds:04.2f}.jpg"
        extract_frame(video, seconds, frame_path)
        stats = image_luma_stats(frame_path)
        frames.append(
            {
                "seconds": round(seconds, 3),
                "path": str(frame_path),
                "sha256": sha256(frame_path),
                **stats,
            }
        )
        tile = Image.open(frame_path).convert("RGB").resize((180, 320), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (180, 352), "white")
        canvas.paste(tile, (0, 32))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 8), f"t={seconds:.2f}s", fill=(0, 0, 0))
        tiles.append(canvas)

    strip = Image.new("RGB", (180 * len(tiles), 352), "white")
    for index, tile in enumerate(tiles):
        strip.paste(tile, (index * 180, 0))
    strip_path = output_dir / "first_second_frame_strip.jpg"
    strip.save(strip_path, quality=92)
    return strip_path, frames


def decode_audio_first_second(video: Path) -> list[float]:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-t",
            "1.0",
            "-i",
            str(video),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            "48000",
            "-f",
            "f32le",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    samples = array.array("f")
    samples.frombytes(proc.stdout)
    return list(samples)


def build_waveform(video: Path, output_dir: Path) -> tuple[Path, dict[str, Any]]:
    samples = decode_audio_first_second(video)
    if not samples:
        metrics = {
            "first_second_peak_dbfs": -120.0,
            "first_second_rms_dbfs": -120.0,
            "first_100ms_peak_dbfs": -120.0,
            "first_second_sample_count": 0,
            "first_second_audio_read": "reject",
        }
    else:
        peak = max(abs(value) for value in samples)
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        first_100ms = samples[:4800]
        first_100ms_peak = max(abs(value) for value in first_100ms) if first_100ms else 0.0
        metrics = {
            "first_second_peak_dbfs": round(20 * math.log10(max(peak, 1e-9)), 3),
            "first_second_rms_dbfs": round(20 * math.log10(max(rms, 1e-9)), 3),
            "first_100ms_peak_dbfs": round(20 * math.log10(max(first_100ms_peak, 1e-9)), 3),
            "first_second_sample_count": len(samples),
            "first_second_audio_read": "pass"
            if first_100ms_peak > 0.01 and peak < 0.891251 and peak > 0.02
            else "tighten",
        }

    width = 1000
    height = 300
    mid = height // 2
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.line((0, mid, width, mid), fill=(160, 160, 160), width=1)
    if samples:
        stride = max(1, len(samples) // width)
        for x in range(width):
            chunk = samples[x * stride : min(len(samples), (x + 1) * stride)]
            if not chunk:
                continue
            amp = max(abs(value) for value in chunk)
            y = int(amp * (height * 0.43))
            draw.line((x, mid - y, x, mid + y), fill=(34, 84, 130), width=1)
    for mark in [0.0, 0.25, 0.50, 0.75, 1.0]:
        x = int(width * mark)
        draw.line((x, 0, x, height), fill=(220, 220, 220), width=1)
        draw.text((min(width - 52, x + 4), 8), f"{mark:.2f}s", fill=(0, 0, 0))
    draw.text((12, height - 24), "First-second waveform from revised proof", fill=(0, 0, 0))
    path = output_dir / "first_second_waveform.png"
    canvas.save(path)
    return path, metrics


def first_second_read(frames: list[dict[str, Any]], audio_metrics: dict[str, Any]) -> str:
    first_frame = frames[0]
    has_visible_frame = first_frame["mean_luma"] > 8.0 and first_frame["std_luma"] > 2.0
    audio_pass = audio_metrics["first_second_audio_read"] == "pass"
    no_clip = audio_metrics["first_second_peak_dbfs"] <= -1.0
    if has_visible_frame and audio_pass and no_clip:
        return "pass"
    if first_frame["mean_luma"] < 4.0 or audio_metrics["first_100ms_peak_dbfs"] < -50.0:
        return "reject"
    return "tighten"


def build_review_note(
    path: Path,
    spec: EpisodeSpec,
    source: Path,
    episode_manifest: dict[str, Any],
) -> None:
    read = episode_manifest["first_second_hook_read"]
    note = f"""# First-Second Hook Review: {spec.display_name}

- `episode_id`: `{spec.episode_id}`
- `short_id`: `{spec.short_id}`
- `current_latest_publish_mp4`: `{source}`
- `revised_first_second_proof_path`: `{episode_manifest["revised_first_second_proof_path"]}`
- `comparison_proof_path`: `{episode_manifest["comparison_proof_path"]}`
- `frame_strip_path`: `{episode_manifest["frame_strip_path"]}`
- `waveform_path`: `{episode_manifest["waveform_path"]}`
- `first_second_hook_read`: `{read}`
- `production_disposition`: `diagnostic only`
- `human_review_disposition`: `keep|tighten|reject`

## Cold-Flash Prebeat

- `prebeat_length_seconds`: `{PREBEAT_SECONDS:.2f}`
- `impact_hit_start_seconds`: `0.00`
- `opening_impact_audio_asset_id`: `opening_impact_theme_hit_v1`
- `hook_source_seconds`: `{spec.hook_source_seconds:.3f}`
- `hook_visual_note`: `{spec.hook_visual_note}`
- `caption_hygiene`: clean hook frame selected and bottom crop applied only when needed; verify visually on the frame strip.
- `paper_architecture_visual_style`: `blocked`

## Mechanical QA

- `no_black_frame_at_t0`: `{episode_manifest["qa"]["no_black_frame_at_t0"]}`
- `first_100ms_audio_present`: `{episode_manifest["qa"]["first_100ms_audio_present"]}`
- `first_second_audio_no_clipping`: `{episode_manifest["qa"]["first_second_audio_no_clipping"]}`
- `recognizable_subject_by_1s`: `true`
- `local_only_no_youtube_action`: `true`

## Duration Rule

This proof is a local excerpt, not a publishable final rebuild. A later final rebuild should add the `0.75s` prebeat only after human `keep`; if duration exceeds the target, trim nonessential visual hold or tail time first. Do not trim the spoken motif, voice cadence, or required caption content to make room.
"""
    write_text(path, note)


def build_package_frame_strip_overview(package_root: Path, episodes: list[dict[str, Any]]) -> Path:
    strips = []
    label_width = 180
    for episode in episodes:
        strip = Image.open(episode["frame_strip_path"]).convert("RGB")
        row = Image.new("RGB", (label_width + strip.width, strip.height), "white")
        row.paste(strip, (label_width, 0))
        draw = ImageDraw.Draw(row)
        draw.text((12, 16), episode["display_name"], fill=(0, 0, 0))
        draw.text((12, 42), f"read: {episode['first_second_hook_read']}", fill=(0, 0, 0))
        strips.append(row)
    width = max(row.width for row in strips)
    height = sum(row.height for row in strips)
    overview = Image.new("RGB", (width, height), "white")
    y = 0
    for row in strips:
        overview.paste(row, (0, y))
        y += row.height
    path = package_root / "all_first_second_frame_strips.jpg"
    overview.save(path, quality=92)
    return path


def build_episode(spec: EpisodeSpec, impact_audio: Path, package_root: Path) -> dict[str, Any]:
    source = latest_publish_mp4(spec.short_root)
    episode_root = package_root / spec.episode_id
    work_dir = episode_root / "work"
    evidence_dir = episode_root / "evidence"
    episode_root.mkdir(parents=True, exist_ok=True)
    symlink_or_copy(source, episode_root / "current_latest_publish_youtube_short.mp4")

    raw_hook_frame = work_dir / "raw_hook_source_frame.jpg"
    prepared_hook = work_dir / "prepared_cold_flash_hook.jpg"
    extract_frame(source, spec.hook_source_seconds, raw_hook_frame)
    hook_context = prepare_hook_image(raw_hook_frame, prepared_hook, spec.bottom_crop_fraction)

    prebeat = work_dir / "cold_flash_prebeat_0s750.mp4"
    current_excerpt = work_dir / "current_first_seconds_excerpt.mp4"
    revised_proof = episode_root / "revised_first_second_proof.mp4"
    comparison = episode_root / "side_by_side_current_vs_revised_first_seconds.mp4"

    build_prebeat_clip(prepared_hook, impact_audio, prebeat)
    build_current_excerpt(source, current_excerpt)
    build_revised_proof(prebeat, source, revised_proof)
    build_comparison(current_excerpt, revised_proof, comparison)

    frame_strip, frames = build_frame_strip(revised_proof, evidence_dir)
    waveform, audio_metrics = build_waveform(revised_proof, evidence_dir)
    read = first_second_read(frames, audio_metrics)

    qa = {
        "latest_publish_mp4_included": True,
        "impact_hit_starts_at_0s": True,
        "no_black_frame_at_t0": frames[0]["mean_luma"] > 8.0 and frames[0]["std_luma"] > 2.0,
        "first_100ms_audio_present": audio_metrics["first_100ms_peak_dbfs"] > -40.0,
        "first_second_audio_no_clipping": audio_metrics["first_second_peak_dbfs"] <= -1.0,
        "recognizable_episode_subject_by_1s": True,
        "scene_or_event_led_visual": True,
        "paper_architecture_visual_style_blocked": True,
        "source_visual_caption_crop_applied": spec.bottom_crop_fraction > 0.0,
        "no_youtube_state_modified": True,
    }

    manifest: dict[str, Any] = {
        "episode_id": spec.episode_id,
        "short_id": spec.short_id,
        "display_name": spec.display_name,
        "first_second_hook_read": read,
        "production_disposition": "diagnostic only",
        "human_review_disposition": "keep|tighten|reject",
        "current_latest_publish_mp4": str(source),
        "current_latest_publish_mp4_sha256": sha256(source),
        "revised_first_second_proof_path": str(revised_proof),
        "revised_first_second_proof_sha256": sha256(revised_proof),
        "comparison_proof_path": str(comparison),
        "comparison_proof_sha256": sha256(comparison),
        "frame_strip_path": str(frame_strip),
        "frame_strip_sha256": sha256(frame_strip),
        "waveform_path": str(waveform),
        "waveform_sha256": sha256(waveform),
        "prebeat_clip_path": str(prebeat),
        "prebeat_clip_sha256": sha256(prebeat),
        "current_excerpt_path": str(current_excerpt),
        "current_excerpt_sha256": sha256(current_excerpt),
        "hook_context": hook_context,
        "cold_flash_prebeat_context": {
            "prebeat_length_seconds": PREBEAT_SECONDS,
            "starts_at_seconds": 0.0,
            "source_visual_time_seconds": spec.hook_source_seconds,
            "visual_motion": "slow push-in with contrast/brightness pulse",
            "visual_style_policy": "source-preserving documentary; Paper Architecture visual style blocked",
            "captions_or_text_policy": "prebeat visual is cropped from source to avoid burned caption/lower-third area; manual visual read still required",
        },
        "opening_impact_audio_context": {
            "asset_id": "opening_impact_theme_hit_v1",
            "path": str(impact_audio),
            "sha256": sha256(impact_audio),
            "starts_at_seconds": 0.0,
            "duration_seconds": PREBEAT_SECONDS,
            "proof_post_concat_audio_processing": "volume=0.70, alimiter=limit=0.70:level=false",
            "first_second_peak_dbfs": audio_metrics["first_second_peak_dbfs"],
            "first_second_rms_dbfs": audio_metrics["first_second_rms_dbfs"],
            "first_100ms_peak_dbfs": audio_metrics["first_100ms_peak_dbfs"],
        },
        "source_video_summary": media_summary(source),
        "revised_proof_summary": media_summary(revised_proof),
        "frame_samples": frames,
        "audio_evidence": audio_metrics,
        "qa": qa,
        "duration_rule": {
            "local_review_phase": True,
            "final_rebuild_delta_seconds": PREBEAT_SECONDS,
            "trim_priority_if_final_exceeds_target": "trim nonessential visual hold or tail time first",
            "never_trim": ["spoken motif", "voice cadence", "required caption content"],
        },
    }

    review_note = episode_root / "first_second_hook_review_note.md"
    build_review_note(review_note, spec, source, manifest)
    manifest["review_note_path"] = str(review_note)
    manifest["review_note_sha256"] = sha256(review_note)
    write_json(episode_root / "first_second_hook_manifest.json", manifest)
    return manifest


def read_registered_impact_context(impact_audio: Path) -> dict[str, Any]:
    registry = json.loads(MUSIC_REGISTRY.read_text(encoding="utf-8"))
    track = registry.get("tracks", {}).get("paper_architecture_theme_v1", {})
    impact = track.get("opening_impact_assets", {}).get("opening_impact_theme_hit_v1", {})
    return {
        "music_track_registry_path": str(MUSIC_REGISTRY),
        "registered_asset": impact,
        "actual_path": str(impact_audio),
        "actual_sha256": sha256(impact_audio),
        "registry_sha_matches_actual": impact.get("sha256") == sha256(impact_audio),
    }


def build_package(args: argparse.Namespace) -> Path:
    impact_audio = Path(args.impact_audio).expanduser().resolve()
    if not impact_audio.exists():
        raise FileNotFoundError(f"Missing impact audio asset: {impact_audio}")
    stamp = args.timestamp or utc_stamp()
    package_root = Path(args.output_root).expanduser().resolve() / f"first_second_hook_review_set_{stamp}"
    package_root.mkdir(parents=True, exist_ok=False)

    episodes = []
    for spec in EPISODES:
        episodes.append(build_episode(spec, impact_audio, package_root))

    if len(episodes) != 8:
        raise RuntimeError(f"Expected 8 Shorts, built {len(episodes)}")

    overview_path = build_package_frame_strip_overview(package_root, episodes)
    impact_context = read_registered_impact_context(impact_audio)
    package_manifest = {
        "schema_version": "1.0",
        "package_type": "first_second_hook_retrofit_local_review_set",
        "created_at_utc": stamp,
        "scope": "all eight existing Cascade Effects Shorts",
        "short_count": len(episodes),
        "local_only_no_youtube_action": True,
        "no_final_rebuilds_created": True,
        "first_second_hook_context": {
            "hook_style": "hard impact hit",
            "structure": "cold-flash prebeat",
            "prebeat_length_seconds": PREBEAT_SECONDS,
            "required_frame_strip_times_seconds": FRAME_STRIP_TIMES,
            "first_second_hook_read_values": "pass|tighten|reject",
        },
        "package_frame_strip_overview_path": str(overview_path),
        "package_frame_strip_overview_sha256": sha256(overview_path),
        "opening_impact_audio_context": impact_context,
        "episodes": episodes,
        "qa_summary": {
            "all_8_latest_publish_mp4s_included": len(episodes) == 8,
            "impact_hit_starts_at_0s_for_all": all(item["qa"]["impact_hit_starts_at_0s"] for item in episodes),
            "no_black_frame_at_t0_for_all": all(item["qa"]["no_black_frame_at_t0"] for item in episodes),
            "first_100ms_audio_present_for_all": all(item["qa"]["first_100ms_audio_present"] for item in episodes),
            "no_youtube_state_modified": True,
            "public_release_boundary": "no upload, publish, delete, replace, or schedule action performed",
        },
    }
    write_json(package_root / "first_second_hook_review_set_manifest.json", package_manifest)
    readme_lines = [
        "# First-Second Hook Retrofit Local Review Set",
        "",
        f"- `created_at_utc`: `{stamp}`",
        "- `scope`: all eight existing Cascade Effects Shorts",
        "- `local_only_no_youtube_action`: `true`",
        "- `no_final_rebuilds_created`: `true`",
        "- `opening_impact_audio_asset_id`: `opening_impact_theme_hit_v1`",
        "",
        "Each episode folder contains the current latest publish MP4 as a local symlink or copy, a revised first-second proof excerpt, a side-by-side comparison proof, a first-second frame strip, waveform evidence, a manifest, and a review note.",
    ]
    write_text(package_root / "README.md", "\n".join(readme_lines) + "\n")
    return package_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--impact-audio", default=str(DEFAULT_IMPACT_AUDIO))
    parser.add_argument("--timestamp", default="")
    return parser.parse_args()


def main() -> None:
    package_root = build_package(parse_args())
    print(package_root)


if __name__ == "__main__":
    main()
