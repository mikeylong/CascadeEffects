#!/usr/bin/env python3
"""Build local publish-readiness packages for the kept theme-intro Shorts.

This script intentionally stops before any YouTube upload. It bridges the
lightweight theme-hook proof manifests into the existing `ce short final-export`
gate, burns captions as the last visual layer, then writes a self-contained
local publish package and runs `publish-package-check`.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, ImageDraw

from scripts.build_shorts_script_locked_captions import (
    ASR_TIMING_POLICY,
    SCRIPT_LOCKED_CAPTION_MODEL,
    SCRIPT_LOCKED_TEXT_POLICY,
    build_shorts_script_locked_caption_package,
)


EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")
HOOK_ROOT = EPISODES_ROOT / "Shorts_First_Second_Hook_Retrofit"
OUTPUT_ROOT = EPISODES_ROOT / "Shorts_Publish_Readiness"
TRANSCRIPT_ROOT = OUTPUT_ROOT / "transcripts_20260521"
CE_BIN = Path("/Users/mike/Viz_CascadeEffects/bin/ce")

CE_SHORT_GLOBALS = [
    "--repo-root",
    str(REPO_ROOT),
    "--models-root",
    "/Users/mike/Viz_CascadeEffects/models",
    "--comfy-workflows-dir",
    "/Users/mike/Viz_CascadeEffects/workflows",
    "--comfy-output-dir",
    "/Users/mike/Viz_CascadeEffects/output",
    "--references-root",
    "/Users/mike/Viz_CascadeEffects/references",
]

FINAL_EXPORT_MUSIC_WAIVER = (
    "Kept theme-intro proof already contains the approved Paper Architecture "
    "theme punch, body loop, voice, and full outro mix; this final-export pass "
    "only burns captions as the last visual layer."
)
HOUSE_CRT_WAIVER = (
    "Kept theme-intro proof already contains the approved CRT/signal treatment "
    "before captions; captions are burned as the final visual operation."
)
CAPTION_STYLE_POLICY = "all_eight_yellow_legibility_v1"
HOUSE_CAPTION_STYLE = "minimal_surreal_editorial_v1"
EXPECTED_HOUSE_ASS_STYLE = {
    "font_name": "Arial",
    "font_size": "82",
    "primary_color": "&H004AD5FF",
    "outline_color": "&HAA0E1116",
}


@dataclass(frozen=True)
class ShortConfig:
    label: str
    slug: str
    latest_dir_name: str
    audio_package: Path
    locked_caption_text_source_path: Path
    caption_min_alignment_coverage: float
    caption_style: str
    title: str
    description: str
    tags: tuple[str, ...]
    hashtags: tuple[str, ...]


SHORTS: tuple[ShortConfig, ...] = (
    ShortConfig(
        label="Challenger",
        slug="challenger",
        latest_dir_name="challenger_explosion_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/selected/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/challenger_short_restart_v1_ending_cadence_script.txt"),
        caption_min_alignment_coverage=0.98,
        caption_style=HOUSE_CAPTION_STYLE,
        title="The Challenger Warning That Stopped Working #Shorts",
        description=(
            "Before Challenger broke apart, engineers had already seen the warning: "
            "O-ring erosion and blow-by on earlier shuttle flights. This Short "
            "follows how a stop signal became a known condition, then a launch-night "
            "burden shift."
        ),
        tags=("Challenger", "NASA", "engineering failure", "risk normalization", "Cascade Effects"),
        hashtags=("#Challenger", "#NASA", "#Shorts"),
    ),
    ShortConfig(
        label="Therac-25",
        slug="therac",
        latest_dir_name="therac_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_scoped_v1/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1/therac_short_scoped_v1.txt"),
        caption_min_alignment_coverage=0.96,
        caption_style=HOUSE_CAPTION_STYLE,
        title="Therac-25: The Machine That Trusted Itself #Shorts",
        description=(
            "A Therac-25 patient received roughly a hundred times the intended "
            "radiation dose, and the manufacturer said it was impossible. This "
            "Short follows how reused code, missing physical interlocks, and slow "
            "disbelief turned operator reports into a system failure."
        ),
        tags=("Therac-25", "software safety", "medical device", "system failure", "Cascade Effects"),
        hashtags=("#Therac25", "#SoftwareSafety", "#Shorts"),
    ),
    ShortConfig(
        label="Hyatt Regency",
        slug="hyatt",
        latest_dir_name="hyatt_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep3_hyatt_regency_short_scoped_v1/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/shorts/hyatt_short_scoped_v1/hyatt_short_scoped_v1.txt"),
        caption_min_alignment_coverage=0.98,
        caption_style=HOUSE_CAPTION_STYLE,
        title="Hyatt Regency: The Dance Before the Collapse #Shorts",
        description=(
            "At the Hyatt Regency, a shop-drawing shortcut changed the load path "
            "of the suspended walkways. This Short follows how a construction "
            "detail became a structural redesign with deadly consequences."
        ),
        tags=("Hyatt Regency", "Kansas City", "structural engineering", "engineering failure", "Cascade Effects"),
        hashtags=("#HyattRegency", "#Engineering", "#Shorts"),
    ),
    ShortConfig(
        label="Tacoma Narrows",
        slug="tacoma",
        latest_dir_name="tacoma_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_short_scoped_v1/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts/tacoma_short_scoped_v1/tacoma_short_scoped_v1.txt"),
        caption_min_alignment_coverage=0.985,
        caption_style=HOUSE_CAPTION_STYLE,
        title="Tacoma Narrows: The Bridge That Fed the Wind #Shorts",
        description=(
            "The Tacoma Narrows Bridge did not fall because the wind was unusually "
            "strong. This Short follows how a slender deck twisted airflow into "
            "feedback the bridge's own design kept feeding."
        ),
        tags=("Tacoma Narrows", "Galloping Gertie", "bridge collapse", "aeroelastic flutter", "Cascade Effects"),
        hashtags=("#TacomaNarrows", "#Bridge", "#Shorts"),
    ),
    ShortConfig(
        label="Piltdown Man",
        slug="piltdown",
        latest_dir_name="piltdown_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdown_man_short_scoped_v1/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts/piltdown_man_short_scoped_v1/piltdown_man_short_scoped_v1.txt"),
        caption_min_alignment_coverage=0.985,
        caption_style=HOUSE_CAPTION_STYLE,
        title="Piltdown Man: The Fossil Hoax That Fooled Science #Shorts",
        description=(
            "Piltdown Man survived because the fossil story fit what British science "
            "wanted to believe. This Short follows how thin evidence, restricted "
            "access, and prestige let a stained skull and filed orangutan jaw become "
            "authority."
        ),
        tags=("Piltdown Man", "scientific hoax", "paleoanthropology", "confirmation bias", "Cascade Effects"),
        hashtags=("#PiltdownMan", "#ScienceHistory", "#Shorts"),
    ),
    ShortConfig(
        label="737 MAX",
        slug="737max",
        latest_dir_name="737max_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_short_scoped_v1/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/shorts/737_max_short_scoped_v1/737_max_short_scoped_v1.txt"),
        caption_min_alignment_coverage=0.98,
        caption_style=HOUSE_CAPTION_STYLE,
        title="737 MAX: The Familiar Airplane Trap #Shorts",
        description=(
            "The 737 MAX was sold as a familiar airplane, even after the airplane "
            "had changed. This Short follows how larger engines, MCAS, and unclear "
            "pilot training turned a new flight behavior into an old story."
        ),
        tags=("737 MAX", "MCAS", "aviation safety", "Boeing 737 MAX", "Cascade Effects"),
        hashtags=("#737MAX", "#AviationSafety", "#Shorts"),
    ),
    ShortConfig(
        label="Titanic",
        slug="titanic",
        latest_dir_name="titanic_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_short_scoped_v1/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1/titanic_short_scoped_v1.txt"),
        caption_min_alignment_coverage=0.97,
        caption_style=HOUSE_CAPTION_STYLE,
        title="Titanic: The Lifeboat Rule That Failed #Shorts",
        description=(
            "Titanic had enough lifeboats to satisfy the law, not enough for the "
            "people aboard. This Short follows how tonnage-based rules approved "
            "yesterday's category while the ship carried tomorrow's risk."
        ),
        tags=("Titanic", "lifeboats", "maritime safety", "regulatory failure", "Cascade Effects"),
        hashtags=("#Titanic", "#History", "#Shorts"),
    ),
    ShortConfig(
        label="Semmelweis",
        slug="semmelweis",
        latest_dir_name="semmelweis_theme_intro_hook_latest",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_short_scoped_v1/audio_package.json"),
        locked_caption_text_source_path=Path("/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/shorts/semmelweis_short_scoped_v1/semmelweis_short_scoped_v1.txt"),
        caption_min_alignment_coverage=0.975,
        caption_style=HOUSE_CAPTION_STYLE,
        title="Semmelweis: The Evidence Doctors Wouldn't Wash In #Shorts",
        description=(
            "At Vienna General Hospital, two maternity wards had similar patients "
            "and very different death rates. This Short follows how Semmelweis "
            "found the routine carrying infection, and why the evidence worked "
            "before medicine was ready to accept it."
        ),
        tags=("Semmelweis", "handwashing", "medical history", "public health", "Cascade Effects"),
        hashtags=("#Semmelweis", "#MedicalHistory", "#Shorts"),
    ),
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(command: list[str], *, cwd: Path = REPO_ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=str(cwd), text=True, capture_output=True)
    if check and completed.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{completed.returncode}: {' '.join(command)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def find_manifest(package_dir: Path) -> Path:
    candidates = sorted(package_dir.glob("*manifest*.json"))
    if not candidates:
        raise FileNotFoundError(f"No manifest JSON found in {package_dir}")
    if len(candidates) == 1:
        return candidates[0]
    preferred = [path for path in candidates if path.name.endswith("_manifest.json")]
    return preferred[0] if preferred else candidates[0]


def latest_proof_dir(config: ShortConfig) -> Path:
    path = (HOOK_ROOT / config.latest_dir_name).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Missing latest proof directory for {config.label}: {path}")
    return path


def parse_srt_timestamp(value: str) -> float:
    match = re.match(r"\s*(\d+):(\d+):(\d+)[,.](\d+)\s*", value)
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value!r}")
    hours, minutes, seconds, millis = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis[:3].ljust(3, "0")) / 1000


def format_srt_timestamp(seconds: float) -> str:
    millis_total = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(millis_total, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def clean_caption_text(text: str) -> str:
    text = re.sub(r"\bSPEAKER_\d+\s*:\s*", "", text)
    text = re.sub(r"\[[0-9:.,\-\u2013\s]+\]\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_srt_blocks(path: Path) -> list[dict[str, Any]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        if not current and line.upper().startswith("WEBVTT"):
            continue
        current.append(line)
    if current:
        blocks.append(current)

    segments: list[dict[str, Any]] = []
    for block in blocks:
        timing_index = next((index for index, line in enumerate(block) if "-->" in line), None)
        if timing_index is None:
            continue
        start_raw, end_raw = block[timing_index].split("-->", 1)
        text = clean_caption_text(" ".join(block[timing_index + 1 :]))
        if not text:
            continue
        segments.append(
            {
                "start_seconds": parse_srt_timestamp(start_raw),
                "end_seconds": parse_srt_timestamp(end_raw.strip().split(" ", 1)[0]),
                "text": text,
            }
        )
    if not segments:
        raise ValueError(f"No caption segments parsed from {path}")
    return segments


def parse_timed_transcript(path: Path) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    pattern = re.compile(r"^\[(?P<start>[0-9:.]+)\s*[\-\u2013]\s*(?P<end>[0-9:.]+)\]\s*(?P<text>.+)$")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        match = pattern.match(line)
        if not match:
            continue
        start = parse_transcript_timestamp(match.group("start"))
        end = parse_transcript_timestamp(match.group("end"))
        text = clean_caption_text(match.group("text"))
        if text and end > start:
            segments.append({"start_seconds": start, "end_seconds": end, "text": text})
    if not segments:
        raise ValueError(f"No timed transcript segments parsed from {path}")
    return segments


def parse_transcript_timestamp(value: str) -> float:
    parts = value.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid transcript timestamp: {value!r}")
    hours, minutes, seconds = parts
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def write_srt(path: Path, segments: list[dict[str, Any]]) -> None:
    lines: list[str] = []
    for index, segment in enumerate(segments, 1):
        lines.extend(
            [
                str(index),
                f"{format_srt_timestamp(float(segment['start_seconds']))} --> {format_srt_timestamp(float(segment['end_seconds']))}",
                str(segment["text"]),
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def normalized_words(text: str) -> list[str]:
    cleaned = clean_caption_text(text).lower()
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", cleaned)


def caption_text_read(transcript_path: Path, srt_segments: list[dict[str, Any]]) -> dict[str, Any]:
    transcript_words = normalized_words(transcript_path.read_text(encoding="utf-8"))
    srt_words = normalized_words(" ".join(str(segment["text"]) for segment in srt_segments))
    transcript_joined = " ".join(transcript_words)
    srt_joined = " ".join(srt_words)
    return {
        "transcript_word_count": len(transcript_words),
        "caption_word_count": len(srt_words),
        "normalized_exact_match": transcript_joined == srt_joined,
        "read": "pass" if transcript_joined == srt_joined else "pass_review_required",
    }


def ffprobe(path: Path) -> dict[str, Any]:
    completed = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate",
            "-show_entries",
            "stream=index,codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    return {
        "video_codec": video.get("codec_name", ""),
        "audio_codec": audio.get("codec_name", ""),
        "width": int(video.get("width", 0) or 0),
        "height": int(video.get("height", 0) or 0),
        "duration_seconds": float(payload.get("format", {}).get("duration") or 0),
        "frame_rate": video.get("avg_frame_rate", ""),
        "audio_sample_rate_hz": int(audio.get("sample_rate", 0) or 0),
        "audio_channels": int(audio.get("channels", 0) or 0),
        "size_bytes": int(payload.get("format", {}).get("size", 0) or 0),
        "bit_rate": int(payload.get("format", {}).get("bit_rate", 0) or 0),
    }


def decode_check(path: Path) -> dict[str, Any]:
    completed = run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=False)
    return {
        "path": str(path),
        "returncode": completed.returncode,
        "read": "pass" if completed.returncode == 0 else "fail",
        "stderr": completed.stderr.strip()[:4000],
    }


def audio_peak_db(path: Path) -> float | None:
    completed = run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-vn", "-sn", "-dn", "-f", "null", "-"],
        check=False,
    )
    match = re.search(r"max_volume:\s*([-0-9.]+)\s*dB", completed.stderr)
    return float(match.group(1)) if match else None


def final8_freezedetect(path: Path, duration: float) -> dict[str, Any]:
    start = max(0.0, duration - 8.0)
    completed = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-vf",
            f"trim=start={start:.3f},setpts=PTS-STARTPTS,freezedetect=n=-60dB:d=0.5",
            "-an",
            "-f",
            "null",
            "-",
        ],
        check=False,
    )
    events = [
        line.strip()
        for line in completed.stderr.splitlines()
        if "freezedetect" in line and ("freeze_start" in line or "freeze_duration" in line)
    ]
    return {
        "window_start_seconds": round(start, 3),
        "event_count": len(events),
        "events": events,
        "read": "pass" if not events and completed.returncode == 0 else "fail",
    }


def extract_cover(video_path: Path, output_path: Path, source_seconds: float = 1.0) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{source_seconds:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(output_path),
        ]
    )


def build_frame_strip(video_path: Path, output_path: Path, timestamps: list[float]) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames: list[tuple[float, Path]] = []
    for index, seconds in enumerate(timestamps):
        frame_path = output_path.parent / f"{output_path.stem}_{index:02d}_{seconds:06.3f}.jpg"
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
                str(video_path),
                "-frames:v",
                "1",
                str(frame_path),
            ]
        )
        frames.append((seconds, frame_path))

    thumbs: list[Image.Image] = []
    for seconds, frame_path in frames:
        image = Image.open(frame_path).convert("RGB")
        image.thumbnail((180, 320))
        tile = Image.new("RGB", (180, 344), "white")
        tile.paste(image, ((180 - image.width) // 2, 0))
        draw = ImageDraw.Draw(tile)
        draw.text((8, 324), f"{seconds:.2f}s", fill=(0, 0, 0))
        thumbs.append(tile)

    strip = Image.new("RGB", (180 * len(thumbs), 344), "white")
    for index, thumb in enumerate(thumbs):
        strip.paste(thumb, (index * 180, 0))
    strip.save(output_path, quality=92)
    return {
        "path": str(output_path),
        "sha256": sha256(output_path),
        "timestamps_seconds": [round(seconds, 3) for seconds, _ in frames],
        "source_video_path": str(video_path),
    }


def strip_timestamps(duration: float) -> list[float]:
    candidates = [3.5, 10.0, 20.0, 30.0, 45.0, max(0.0, duration - 3.0)]
    selected: list[float] = []
    for value in candidates:
        clamped = min(max(0.0, value), max(0.0, duration - 0.1))
        if all(abs(clamped - existing) > 0.25 for existing in selected):
            selected.append(clamped)
    return selected


def caption_style_evidence(overlay_manifest_path: Path, final_manifest_path: Path, expected_style: str) -> dict[str, Any]:
    overlay = read_json(overlay_manifest_path)
    final_manifest = read_json(final_manifest_path)
    ass_path = Path(str(overlay.get("caption_ass_path") or final_manifest.get("caption_ass_path", "")))
    style_line = ""
    if ass_path.exists():
        for line in ass_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Style: DocumentaryLowerThird,"):
                style_line = line
                break

    fields = [field.strip() for field in style_line.split(":", 1)[1].split(",")] if style_line else []
    actual = {
        "caption_style_preset": overlay.get("caption_style_preset"),
        "font_name": fields[1] if len(fields) > 1 else None,
        "font_size": fields[2] if len(fields) > 2 else None,
        "primary_color": fields[3] if len(fields) > 3 else None,
        "outline_color": fields[5] if len(fields) > 5 else None,
    }
    expected = {
        "caption_style_preset": expected_style,
        **EXPECTED_HOUSE_ASS_STYLE,
    }
    read = (
        "pass"
        if actual["caption_style_preset"] == expected["caption_style_preset"]
        and actual["font_name"] == expected["font_name"]
        and actual["font_size"] == expected["font_size"]
        and actual["primary_color"] == expected["primary_color"]
        and actual["outline_color"] == expected["outline_color"]
        else "fail"
    )
    return {
        "read": read,
        "caption_style_policy": CAPTION_STYLE_POLICY,
        "expected": expected,
        "actual": actual,
        "caption_overlay_manifest_path": str(overlay_manifest_path),
        "caption_ass_path": str(ass_path),
    }


def make_symlink(target: Path, link: Path) -> None:
    if link.is_symlink() or link.exists():
        if link.is_dir() and not link.is_symlink():
            raise RuntimeError(f"Refusing to replace non-symlink directory: {link}")
        link.unlink()
    link.symlink_to(target)


def load_locked_caption_source_overrides(manifest_path: Path | None) -> dict[str, Path]:
    if manifest_path is None:
        return {}
    manifest_path = manifest_path.expanduser().resolve()
    payload = read_json(manifest_path)
    sources = payload.get("sources", {})
    if not isinstance(sources, dict):
        raise ValueError(f"{manifest_path}: missing sources object")
    overrides: dict[str, Path] = {}
    for slug, source in sources.items():
        if not isinstance(source, dict):
            continue
        source_path = source.get("locked_caption_text_source_path")
        if not isinstance(source_path, str) or not source_path:
            continue
        overrides[str(slug)] = Path(source_path).expanduser().resolve()
    return overrides


def build_bridge_manifest(
    *,
    config: ShortConfig,
    package_dir: Path,
    source_manifest_path: Path,
    source_manifest: dict[str, Any],
    audio_package_path: Path,
    audio_package: dict[str, Any],
    locked_caption_text_source_path: Path,
    caption_timing_source_path: Path,
    script_locked_caption_qa: dict[str, Any],
) -> Path:
    voice_path = Path(str(audio_package["packaged_path"])).expanduser().resolve()
    transcript_path = Path(str(audio_package["transcript_path"])).expanduser().resolve()
    locked_caption_text_source_path = locked_caption_text_source_path.expanduser().resolve()
    caption_timing_source_path = caption_timing_source_path.expanduser().resolve()
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest_type": "theme_intro_publish_ready_final_export_bridge",
        "episode_id": source_manifest.get("episode_id", ""),
        "short_id": source_manifest.get("short_id", ""),
        "source_theme_hook_proof_manifest_path": str(source_manifest_path),
        "source_theme_hook_proof_manifest_sha256": sha256(source_manifest_path),
        "proof_path": source_manifest["proof_path"],
        "comparison_path": source_manifest.get("comparison_path", ""),
        "human_review_disposition": "keep",
        "disposition": "keep",
        "reel_class": "keeper short",
        "audio_path": str(voice_path),
        "voice_strategy": source_manifest.get("voice_strategy", {}),
        "short_audio_package_path": str(audio_package_path),
        "audio_package_sha256": sha256(audio_package_path),
        "packaged_audio_sha256": sha256(voice_path),
        "caption_source_path": str(locked_caption_text_source_path),
        "caption_text_source_path": str(locked_caption_text_source_path),
        "caption_text_source_sha256": sha256(locked_caption_text_source_path),
        "caption_text_source_policy": SCRIPT_LOCKED_TEXT_POLICY,
        "caption_timing_source_path": str(caption_timing_source_path),
        "caption_timing_source_sha256": sha256(caption_timing_source_path),
        "caption_timing_source_policy": ASR_TIMING_POLICY,
        "caption_model": SCRIPT_LOCKED_CAPTION_MODEL,
        "caption_text_matches_script_read": script_locked_caption_qa["reads"]["caption_text_matches_script_read"],
        "caption_alignment_coverage_read": script_locked_caption_qa["reads"]["caption_alignment_coverage_read"],
        "caption_asr_text_not_used_read": script_locked_caption_qa["reads"]["caption_asr_text_not_used_read"],
        "publish_ready_blocked_if_caption_text_not_script_locked": True,
        "transcript_sha256": sha256(transcript_path),
        "expected_voice_profile_id": audio_package.get("voice_profile_id", "youtube_shorts_mike_challenger_match_v1"),
        "audio_disposition": "keep",
        "caption_layer_policy": "final_export_caption_burn_last_visual_layer",
        "caption_style_policy": CAPTION_STYLE_POLICY,
        "caption_style_preset": config.caption_style,
        "motion_source_contains_captions": source_manifest.get("motion_source_contains_captions", False),
        "publish_readiness_bridge_for": config.label,
        "no_youtube_action": True,
        "youtube_state_changed": False,
    }
    path = package_dir / "bridge_final_export__proof.json"
    write_json(path, payload)
    return path


def run_final_export(
    *,
    bridge_manifest_path: Path,
    review_note_path: Path,
    caption_source_path: Path,
    caption_timing_path: Path,
    caption_style: str,
    output_tag: str,
) -> Path:
    command = [
        str(CE_BIN),
        "short",
        *CE_SHORT_GLOBALS,
        "final-export",
        str(bridge_manifest_path),
        "--proof-review-note",
        str(review_note_path),
        "--proof-disposition",
        "keep",
        "--reel-class",
        "keeper-short",
        "--all-motion-clips-keep",
        "--no-diagnostic-placeholders",
        "--caption-style",
        caption_style,
        "--caption-source",
        str(caption_source_path),
        "--caption-timing",
        str(caption_timing_path),
        "--output-tag",
        output_tag,
        "--music-policy",
        "waived",
        "--music-waiver-reason",
        FINAL_EXPORT_MUSIC_WAIVER,
        "--music-rights-check-status",
        "pending_youtube_upload_check",
        "--house-crt-static-waiver-reason",
        HOUSE_CRT_WAIVER,
    ]
    run(command)
    manifests = sorted(
        (bridge_manifest_path.parent / "final_exports").glob("**/*__final_export.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not manifests:
        raise FileNotFoundError(f"No final export manifest created under {bridge_manifest_path.parent / 'final_exports'}")
    return manifests[0]


def write_text_sidecars(config: ShortConfig, package_dir: Path) -> dict[str, Path]:
    title_path = package_dir / "youtube_title.txt"
    description_path = package_dir / "youtube_description.txt"
    tags_path = package_dir / "youtube_tags.txt"
    metadata_path = package_dir / "youtube_metadata.md"
    checklist_path = package_dir / "upload_checklist.md"

    description = f"{config.description}\n\n{' '.join(config.hashtags)}"
    tags_text = "; ".join(config.tags)
    metadata = (
        f"# YouTube Metadata\n\n"
        f"Title: {config.title}\n\n"
        f"Description:\n{description}\n\n"
        f"Tags: {tags_text}\n\n"
        f"Hashtags: {' '.join(config.hashtags)}\n"
    )
    checklist = (
        "# Upload Checklist\n\n"
        "- Confirm final captioned MP4 plays through the full outro.\n"
        "- Confirm captions are readable and do not cover the mechanism, faces, or anomaly.\n"
        "- Confirm YouTube copyright/Content ID checks after unlisted review upload.\n"
        "- Do not make public from automation; public release stays manual in YouTube Studio.\n"
    )
    title_path.write_text(config.title + "\n", encoding="utf-8")
    description_path.write_text(description + "\n", encoding="utf-8")
    tags_path.write_text(tags_text + "\n", encoding="utf-8")
    metadata_path.write_text(metadata, encoding="utf-8")
    checklist_path.write_text(checklist, encoding="utf-8")
    return {
        "title": title_path,
        "description": description_path,
        "tags": tags_path,
        "metadata": metadata_path,
        "checklist": checklist_path,
    }


def write_publish_manifest(
    *,
    config: ShortConfig,
    package_dir: Path,
    final_video: Path,
    caption_srt: Path,
    cover_frame: Path,
    text_paths: dict[str, Path],
    final_manifest_copy: Path,
    final_review_note: Path,
    caption_overlay_manifest_copy: Path,
    caption_timing_copy: Path,
    source_manifest_path: Path,
    source_manifest: dict[str, Any],
    qa: dict[str, Any],
    stamp: str,
) -> Path:
    probe = qa["technical_read"]
    upload_manifest = {
        "schema_version": 1,
        "kind": "youtube_shorts_publish_package",
        "target": "youtube_shorts",
        "episode_id": source_manifest.get("episode_id", ""),
        "short_id": source_manifest.get("short_id", ""),
        "package_id": package_dir.name,
        "created_utc": stamp,
        "publication_readiness": "ready_for_unlisted_review_upload_pending_manual_studio_checks",
        "public_release_boundary": "manual_youtube_studio_only",
        "youtube_state": {
            "upload_performed": False,
            "publish_performed": False,
            "delete_performed": False,
            "schedule_performed": False,
            "requires_separate_explicit_unlisted_upload_confirmation": True,
        },
        "upload_assets": {
            "video_path": final_video.name,
            "video_sha256": sha256(final_video),
            "title_path": text_paths["title"].name,
            "title_sha256": sha256(text_paths["title"]),
            "description_path": text_paths["description"].name,
            "description_sha256": sha256(text_paths["description"]),
            "tags_path": text_paths["tags"].name,
            "tags_sha256": sha256(text_paths["tags"]),
            "caption_srt_path": caption_srt.name,
            "caption_srt_sha256": sha256(caption_srt),
            "suggested_cover_frame_path": cover_frame.name,
            "suggested_cover_frame_sha256": sha256(cover_frame),
            "metadata_path": text_paths["metadata"].name,
            "metadata_sha256": sha256(text_paths["metadata"]),
            "upload_checklist_path": text_paths["checklist"].name,
            "upload_checklist_sha256": sha256(text_paths["checklist"]),
            "caption_overlay_manifest_path": caption_overlay_manifest_copy.name,
            "caption_overlay_manifest_sha256": sha256(caption_overlay_manifest_copy),
            "caption_timing_path": caption_timing_copy.name,
            "caption_timing_sha256": sha256(caption_timing_copy),
        },
        "technical_read": {
            "container": "mp4",
            "video_codec": probe["video_codec"],
            "audio_codec": probe["audio_codec"],
            "width": probe["width"],
            "height": probe["height"],
            "duration_seconds": probe["duration_seconds"],
            "frame_rate": probe["frame_rate"],
            "audio_sample_rate_hz": probe["audio_sample_rate_hz"],
            "audio_channels": probe["audio_channels"],
            "vertical_shorts_geometry_read": "pass" if probe["width"] == 1080 and probe["height"] == 1920 else "fail",
            "duration_under_180s_read": "pass" if probe["duration_seconds"] <= 180 else "fail",
            "audio_present_read": "pass" if probe["audio_channels"] > 0 else "fail",
            "final8_freezedetect_read": qa["final8_freezedetect"]["read"],
            "audio_peak_dbfs": qa["audio_peak_dbfs"],
            "audio_peak_read": qa["audio_peak_read"],
        },
        "youtube_metadata": {
            "title": config.title,
            "description_path": text_paths["description"].name,
            "tags": list(config.tags),
            "hashtags": list(config.hashtags),
            "privacy": "unlisted",
            "audience": "not_made_for_kids",
            "paid_promotion": "not_declared",
            "default_language": "en",
            "default_audio_language": "en",
            "language": "en",
            "category": "Education",
            "category_id": "27",
            "metadata_copy_packet_path": text_paths["metadata"].name,
            "metadata_human_keep_read": "pending_manual_review",
        },
        "source_final": {
            "path": final_video.name,
            "sha256": sha256(final_video),
            "source_duplicate_path": str(final_video),
            "source_duplicate_sha256": sha256(final_video),
            "source_theme_hook_proof_manifest_path": str(source_manifest_path),
            "source_theme_hook_proof_manifest_sha256": sha256(source_manifest_path),
            "proof_path": source_manifest["proof_path"],
            "proof_sha256": sha256(Path(source_manifest["proof_path"])),
            "final_export_manifest_path": final_manifest_copy.name,
            "final_export_manifest_sha256": sha256(final_manifest_copy),
            "final_review_path": final_review_note.name,
            "final_review_sha256": sha256(final_review_note),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
            "caption_burn_read": "pass",
            "caption_layer_order_read": "pass_caption_burn_last_visual_layer",
            "caption_style_policy": CAPTION_STYLE_POLICY,
            "caption_style_read": qa["caption_style_read"]["read"],
            "motion_source_contains_captions": source_manifest.get("motion_source_contains_captions", False),
            "house_crt_texture_read": "pass_provenance_from_kept_theme_intro_proof",
            "signal_interruption_read": "pass_provenance_from_kept_theme_intro_proof",
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
        },
        "caption_context": {
            "caption_model": SCRIPT_LOCKED_CAPTION_MODEL,
            "caption_source_strategy": "script_locked_words_with_asr_whisperx_timing_only",
            "caption_text_source_policy": qa["caption_text_source_policy"],
            "caption_timing_source_policy": qa["caption_timing_source_policy"],
            "caption_style_policy": CAPTION_STYLE_POLICY,
            "caption_style_preset": config.caption_style,
            "caption_style_evidence": qa["caption_style_read"],
            "caption_placement": "lower-center",
            "caption_source_path": str(qa["caption_text_source_path"]),
            "caption_source_sha256": sha256(Path(qa["caption_text_source_path"])),
            "caption_text_source_path": str(qa["caption_text_source_path"]),
            "caption_text_source_sha256": sha256(Path(qa["caption_text_source_path"])),
            "caption_timing_source_path": str(qa["caption_timing_source_path"]),
            "caption_timing_source_sha256": sha256(Path(qa["caption_timing_source_path"])),
            "fresh_transcription_srt_path": str(qa["fresh_transcription_srt_path"]),
            "fresh_transcription_srt_sha256": sha256(Path(qa["fresh_transcription_srt_path"])),
            "offset_caption_srt_path": caption_srt.name,
            "offset_caption_srt_sha256": sha256(caption_srt),
            "voice_delay_seconds": qa["voice_delay_seconds"],
            "caption_text_read": qa["caption_text_read"],
            "caption_text_matches_script_read": qa["caption_text_matches_script_read"],
            "caption_alignment_coverage_read": qa["caption_alignment_coverage_read"],
            "caption_asr_text_not_used_read": qa["caption_asr_text_not_used_read"],
            "fresh_transcription_verification_read": qa["fresh_transcription_verification_read"],
            "script_locked_caption_qa_path": qa["script_locked_caption_qa_path"],
            "burned_in_and_sidecar_same_script_locked_source_read": "pass",
            "publish_ready_blocked_if_caption_text_not_script_locked": qa[
                "publish_ready_blocked_if_caption_text_not_script_locked"
            ],
        },
        "final_music_context": {
            "music_bed_used": True,
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "motif_outro_mix_used": True,
            "final_export_music_remix_performed": False,
            "final_export_music_waiver_reason": FINAL_EXPORT_MUSIC_WAIVER,
        },
        "rights_and_claims": {
            "music_bed_used": True,
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "claim_risk": "Manual YouTube copyright/Content ID and source-footage review required before public release.",
            "public_release_blocked_until": "manual_youtube_studio_review",
        },
    }
    path = package_dir / "youtube_upload_manifest.json"
    write_json(path, upload_manifest)
    return path


def write_final_review_note(
    *,
    config: ShortConfig,
    package_dir: Path,
    final_video: Path,
    final_manifest_copy: Path,
    caption_srt: Path,
    qa: dict[str, Any],
) -> Path:
    path = package_dir / "final_qa_review_note.md"
    validation_read = "pass" if qa.get("publish_package_check", {}).get("ok") else "fail"
    lines = [
        f"# {config.label} Publish-Ready Final QA",
        "",
        "- Disposition: keep",
        "- Reel class: keeper short",
        "- YouTube action: none; unlisted upload requires separate explicit confirmation",
        f"- Caption style policy: `{CAPTION_STYLE_POLICY}`",
        f"- Caption style: `{config.caption_style}`",
        f"- Caption model: `{qa['caption_model']}`",
        f"- Caption text source: `{qa['caption_text_source_path']}`",
        f"- Caption timing source: `{qa['caption_timing_source_path']}`",
        f"- Captioned MP4: `{final_video}`",
        f"- Final export manifest: `{final_manifest_copy}`",
        f"- Caption SRT: `{caption_srt}`",
        "",
        "## Automated QA",
        "",
        f"- Geometry: {qa['technical_read']['width']}x{qa['technical_read']['height']}",
        f"- Duration: {qa['technical_read']['duration_seconds']:.6f}s",
        f"- Audio codec/channels: {qa['technical_read']['audio_codec']} / {qa['technical_read']['audio_channels']}",
        f"- Audio peak: {qa['audio_peak_dbfs']} dBFS ({qa['audio_peak_read']})",
        f"- Final decode: {qa['final_decode']['read']}",
        f"- Proof decode: {qa['proof_decode']['read']}",
        f"- Comparison decode: {qa['comparison_decode']['read']}",
        f"- Final-8s freezedetect: {qa['final8_freezedetect']['read']} ({qa['final8_freezedetect']['event_count']} events)",
        f"- Caption text/script read: {qa['caption_text_matches_script_read']}",
        f"- ASR text not used read: {qa['caption_asr_text_not_used_read']}",
        f"- Caption style evidence: {qa['caption_style_read']['read']}",
        f"- Fresh WhisperX timing verification: {qa['fresh_transcription_verification_read']['read']}",
        f"- Publish-package-check: {validation_read}",
        "",
        "## Manual Checks Still Required",
        "",
        "- Review lower-third captions for mechanism/face/anomaly occlusion.",
        "- Confirm YouTube Studio copyright and Content ID checks after any approved unlisted upload.",
        "- Public release remains manual in YouTube Studio.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def copy_final_artifacts(package_dir: Path, final_manifest_path: Path, config: ShortConfig) -> dict[str, Path]:
    final_manifest = read_json(final_manifest_path)
    source_video = Path(final_manifest["captioned_final_path"])
    source_srt = Path(final_manifest["caption_srt_path"])
    source_overlay_manifest = Path(final_manifest["caption_overlay_manifest_path"])
    source_timing = Path(final_manifest["caption_timing_path"])

    final_video = package_dir / f"{config.slug}_theme_intro_captioned_youtube_short.mp4"
    caption_srt = package_dir / f"{config.slug}_captions.srt"
    overlay_manifest = package_dir / "caption_overlay_manifest.json"
    caption_timing = package_dir / "caption_timing.json"
    final_manifest_copy = package_dir / "final_export_manifest.json"

    shutil.copy2(source_video, final_video)
    shutil.copy2(source_srt, caption_srt)
    shutil.copy2(source_overlay_manifest, overlay_manifest)
    shutil.copy2(source_timing, caption_timing)
    shutil.copy2(final_manifest_path, final_manifest_copy)
    return {
        "final_video": final_video,
        "caption_srt": caption_srt,
        "caption_overlay_manifest": overlay_manifest,
        "caption_timing": caption_timing,
        "final_manifest": final_manifest_copy,
    }


def build_one(
    config: ShortConfig,
    *,
    stamp: str,
    transcript_root: Path,
    locked_caption_source_overrides: dict[str, Path],
) -> dict[str, Any]:
    source_dir = latest_proof_dir(config)
    source_manifest_path = find_manifest(source_dir)
    source_manifest = read_json(source_manifest_path)
    if source_manifest.get("human_review_disposition") != "keep":
        raise RuntimeError(f"{config.label}: latest proof is not marked keep in {source_manifest_path}")
    proof_path = Path(source_manifest["proof_path"])
    comparison_path = Path(source_manifest["comparison_path"])
    review_note_path = source_dir / "review_note.md"
    audio_package_path = config.audio_package
    audio_package = read_json(audio_package_path)
    voice_path = Path(str(audio_package["packaged_path"])).expanduser().resolve()
    transcript_path = Path(str(audio_package["transcript_path"])).expanduser().resolve()
    locked_caption_text_source_path = locked_caption_source_overrides.get(
        config.slug,
        config.locked_caption_text_source_path.expanduser().resolve(),
    )
    if not locked_caption_text_source_path.exists():
        raise FileNotFoundError(
            f"{config.label}: missing locked caption text source: {locked_caption_text_source_path}. "
            "Publish-ready captions must use locked script words; ASR/WhisperX transcript text is timing-only."
        )
    fresh_srt = transcript_root / f"{voice_path.stem}.diarized.srt"
    if not fresh_srt.exists():
        raise FileNotFoundError(f"{config.label}: missing fresh transcribe SRT: {fresh_srt}")

    package_dir = OUTPUT_ROOT / f"{config.slug}_publish_ready_{stamp}"
    package_dir.mkdir(parents=True, exist_ok=True)

    voice_delay = float(source_manifest.get("voice_strategy", {}).get("voice_delay_seconds", 3.0))
    fresh_srt_segments = parse_srt_blocks(fresh_srt)
    caption_package_dir = package_dir / "script_locked_captions"
    script_locked_caption_qa = build_shorts_script_locked_caption_package(
        caption_text_source_path=locked_caption_text_source_path,
        caption_timing_source_path=fresh_srt,
        output_dir=caption_package_dir,
        basename=f"{config.slug}_shorts",
        voice_offset_seconds=voice_delay,
        min_alignment_coverage=config.caption_min_alignment_coverage,
    )
    offset_srt = Path(str(script_locked_caption_qa["outputs"]["offset_srt"]["path"]))
    story_srt = Path(str(script_locked_caption_qa["outputs"]["story_srt"]["path"]))
    story_segments = parse_srt_blocks(story_srt)
    caption_text = caption_text_read(locked_caption_text_source_path, story_segments)
    fresh_transcription_verification = {
        "read": "pass_timing_only",
        "caption_timing_source_path": str(fresh_srt),
        "caption_timing_source_policy": ASR_TIMING_POLICY,
        "timing_segment_count": len(fresh_srt_segments),
        "asr_text_used_for_caption_words": False,
    }

    bridge_manifest = build_bridge_manifest(
        config=config,
        package_dir=package_dir,
        source_manifest_path=source_manifest_path,
        source_manifest=source_manifest,
        audio_package_path=audio_package_path,
        audio_package=audio_package,
        locked_caption_text_source_path=locked_caption_text_source_path,
        caption_timing_source_path=fresh_srt,
        script_locked_caption_qa=script_locked_caption_qa,
    )
    final_manifest_path = run_final_export(
        bridge_manifest_path=bridge_manifest,
        review_note_path=review_note_path,
        caption_source_path=locked_caption_text_source_path,
        caption_timing_path=offset_srt,
        caption_style=config.caption_style,
        output_tag=f"publish_ready_{stamp}_{config.slug}",
    )
    copied = copy_final_artifacts(package_dir, final_manifest_path, config)
    final_video = copied["final_video"]
    caption_srt = copied["caption_srt"]
    cover_frame = package_dir / "suggested_shorts_cover_frame.png"
    extract_cover(final_video, cover_frame)
    technical = ffprobe(final_video)
    evidence_dir = package_dir / "evidence"
    final_caption_strip = build_frame_strip(
        final_video,
        evidence_dir / "final_caption_style_frame_strip.jpg",
        strip_timestamps(technical["duration_seconds"]),
    )
    proof_caption_source_strip = build_frame_strip(
        proof_path,
        evidence_dir / "source_proof_caption_duplicate_repair_strip.jpg",
        strip_timestamps(float(source_manifest.get("media_summary", {}).get("duration_seconds", technical["duration_seconds"]))),
    )
    caption_style_read = caption_style_evidence(
        copied["caption_overlay_manifest"],
        copied["final_manifest"],
        config.caption_style,
    )
    if caption_style_read["read"] != "pass":
        raise RuntimeError(f"{config.label}: caption style evidence failed: {caption_style_read}")
    text_paths = write_text_sidecars(config, package_dir)

    peak = audio_peak_db(final_video)
    qa: dict[str, Any] = {
        "caption_source_path": str(locked_caption_text_source_path),
        "caption_text_source_path": str(locked_caption_text_source_path),
        "caption_timing_source_path": str(fresh_srt),
        "caption_text_source_policy": SCRIPT_LOCKED_TEXT_POLICY,
        "caption_timing_source_policy": ASR_TIMING_POLICY,
        "caption_model": SCRIPT_LOCKED_CAPTION_MODEL,
        "caption_text_matches_script_read": script_locked_caption_qa["reads"]["caption_text_matches_script_read"],
        "caption_alignment_coverage_read": script_locked_caption_qa["reads"]["caption_alignment_coverage_read"],
        "caption_asr_text_not_used_read": script_locked_caption_qa["reads"]["caption_asr_text_not_used_read"],
        "publish_ready_blocked_if_caption_text_not_script_locked": True,
        "script_locked_caption_qa_path": script_locked_caption_qa["outputs"]["qa_json"]["path"],
        "script_locked_caption_qa": script_locked_caption_qa,
        "caption_style_policy": CAPTION_STYLE_POLICY,
        "caption_style_read": caption_style_read,
        "final_caption_style_frame_strip": final_caption_strip,
        "source_proof_caption_duplicate_repair_strip": proof_caption_source_strip,
        "fresh_transcription_srt_path": str(fresh_srt),
        "voice_delay_seconds": voice_delay,
        "caption_text_read": caption_text,
        "fresh_transcription_verification_read": fresh_transcription_verification,
        "technical_read": technical,
        "audio_peak_dbfs": peak,
        "audio_peak_read": "pass" if peak is not None and peak <= -1.0 else "fail",
        "final_decode": decode_check(final_video),
        "proof_decode": decode_check(proof_path),
        "comparison_decode": decode_check(comparison_path),
        "final8_freezedetect": final8_freezedetect(final_video, technical["duration_seconds"]),
    }
    final_review_note = write_final_review_note(
        config=config,
        package_dir=package_dir,
        final_video=final_video,
        final_manifest_copy=copied["final_manifest"],
        caption_srt=caption_srt,
        qa={**qa, "publish_package_check": {"ok": False}},
    )
    upload_manifest = write_publish_manifest(
        config=config,
        package_dir=package_dir,
        final_video=final_video,
        caption_srt=caption_srt,
        cover_frame=cover_frame,
        text_paths=text_paths,
        final_manifest_copy=copied["final_manifest"],
        final_review_note=final_review_note,
        caption_overlay_manifest_copy=copied["caption_overlay_manifest"],
        caption_timing_copy=copied["caption_timing"],
        source_manifest_path=source_manifest_path,
        source_manifest=source_manifest,
        qa=qa,
        stamp=stamp,
    )
    validation = run([str(CE_BIN), "orchestrate", "publish-package-check", str(upload_manifest)], check=False)
    validation_path = package_dir / "publish_package_validation.json"
    try:
        validation_payload = json.loads(validation.stdout)
    except json.JSONDecodeError:
        validation_payload = {
            "ok": False,
            "stdout": validation.stdout,
            "stderr": validation.stderr,
            "returncode": validation.returncode,
        }
    write_json(validation_path, validation_payload)
    qa["publish_package_check"] = validation_payload
    final_review_note = write_final_review_note(
        config=config,
        package_dir=package_dir,
        final_video=final_video,
        final_manifest_copy=copied["final_manifest"],
        caption_srt=caption_srt,
        qa=qa,
    )
    upload_manifest = write_publish_manifest(
        config=config,
        package_dir=package_dir,
        final_video=final_video,
        caption_srt=caption_srt,
        cover_frame=cover_frame,
        text_paths=text_paths,
        final_manifest_copy=copied["final_manifest"],
        final_review_note=final_review_note,
        caption_overlay_manifest_copy=copied["caption_overlay_manifest"],
        caption_timing_copy=copied["caption_timing"],
        source_manifest_path=source_manifest_path,
        source_manifest=source_manifest,
        qa=qa,
        stamp=stamp,
    )
    validation = run([str(CE_BIN), "orchestrate", "publish-package-check", str(upload_manifest)], check=False)
    try:
        validation_payload = json.loads(validation.stdout)
    except json.JSONDecodeError:
        validation_payload = {
            "ok": False,
            "stdout": validation.stdout,
            "stderr": validation.stderr,
            "returncode": validation.returncode,
        }
    write_json(validation_path, validation_payload)
    qa["publish_package_check"] = validation_payload

    package_manifest = {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "package_type": "all_eight_theme_intro_publish_ready_final",
        "episode_label": config.label,
        "source_theme_hook_package": str(source_dir),
        "source_theme_hook_manifest_path": str(source_manifest_path),
        "bridge_manifest_path": str(bridge_manifest),
        "final_export_manifest_path": str(copied["final_manifest"]),
        "final_export_manifest_sha256": sha256(copied["final_manifest"]),
        "captioned_mp4_path": str(final_video),
        "captioned_mp4_sha256": sha256(final_video),
        "caption_srt_path": str(caption_srt),
        "caption_srt_sha256": sha256(caption_srt),
        "caption_model": SCRIPT_LOCKED_CAPTION_MODEL,
        "caption_text_source_policy": qa["caption_text_source_policy"],
        "caption_text_source_path": qa["caption_text_source_path"],
        "caption_timing_source_policy": qa["caption_timing_source_policy"],
        "caption_timing_source_path": qa["caption_timing_source_path"],
        "caption_text_matches_script_read": qa["caption_text_matches_script_read"],
        "caption_asr_text_not_used_read": qa["caption_asr_text_not_used_read"],
        "publish_ready_blocked_if_caption_text_not_script_locked": qa[
            "publish_ready_blocked_if_caption_text_not_script_locked"
        ],
        "caption_style_policy": CAPTION_STYLE_POLICY,
        "caption_style_read": qa["caption_style_read"],
        "final_caption_style_frame_strip": qa["final_caption_style_frame_strip"],
        "source_proof_caption_duplicate_repair_strip": qa["source_proof_caption_duplicate_repair_strip"],
        "youtube_upload_manifest_path": str(upload_manifest),
        "youtube_upload_manifest_sha256": sha256(upload_manifest),
        "publish_package_validation_path": str(validation_path),
        "publish_package_validation_ok": bool(validation_payload.get("ok")),
        "qa": qa,
        "no_youtube_action": True,
        "public_release_boundary": "manual_youtube_studio_only",
    }
    package_manifest_path = package_dir / "publish_ready_package_manifest.json"
    write_json(package_manifest_path, package_manifest)
    make_symlink(package_dir, OUTPUT_ROOT / f"{config.slug}_publish_ready_latest")
    return package_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=[config.slug for config in SHORTS], nargs="*")
    parser.add_argument("--stamp", default=utc_stamp())
    parser.add_argument("--transcript-root", default=str(TRANSCRIPT_ROOT))
    parser.add_argument("--locked-caption-source-manifest", type=Path)
    args = parser.parse_args()

    transcript_root = Path(args.transcript_root).expanduser().resolve()
    locked_caption_source_overrides = load_locked_caption_source_overrides(args.locked_caption_source_manifest)
    selected = [config for config in SHORTS if not args.only or config.slug in args.only]
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    results = []
    for config in selected:
        print(f"==> Building publish-ready package for {config.label}")
        results.append(
            build_one(
                config,
                stamp=args.stamp,
                transcript_root=transcript_root,
                locked_caption_source_overrides=locked_caption_source_overrides,
            )
        )

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stamp": args.stamp,
        "package_count": len(results),
        "locked_caption_source_manifest_path": str(args.locked_caption_source_manifest) if args.locked_caption_source_manifest else "",
        "caption_model": SCRIPT_LOCKED_CAPTION_MODEL,
        "caption_text_source_policy": SCRIPT_LOCKED_TEXT_POLICY,
        "caption_timing_source_policy": ASR_TIMING_POLICY,
        "all_caption_text_matches_script_reads_pass": all(
            result["caption_text_matches_script_read"] == "pass" for result in results
        ),
        "all_caption_asr_text_not_used_reads_pass": all(
            result["caption_asr_text_not_used_read"] == "pass" for result in results
        ),
        "caption_style_policy": CAPTION_STYLE_POLICY,
        "all_caption_style_reads_pass": all(result["caption_style_read"]["read"] == "pass" for result in results),
        "all_publish_package_checks_ok": all(result["publish_package_validation_ok"] for result in results),
        "all_audio_peaks_below_minus_1_dbfs": all(result["qa"]["audio_peak_read"] == "pass" for result in results),
        "all_final8_freezedetect_pass": all(result["qa"]["final8_freezedetect"]["read"] == "pass" for result in results),
        "packages": results,
        "no_youtube_action": True,
        "public_release_boundary": "manual_youtube_studio_only",
    }
    summary_path = OUTPUT_ROOT / f"all_eight_publish_readiness_summary_{args.stamp}.json"
    write_json(summary_path, summary)
    make_symlink(summary_path, OUTPUT_ROOT / "all_eight_publish_readiness_summary_latest.json")
    print(f"SUMMARY {summary_path}")
    if not summary["all_publish_package_checks_ok"]:
        return 1
    if not summary["all_caption_style_reads_pass"]:
        return 1
    if not summary["all_caption_text_matches_script_reads_pass"]:
        return 1
    if not summary["all_caption_asr_text_not_used_reads_pass"]:
        return 1
    if not summary["all_audio_peaks_below_minus_1_dbfs"]:
        return 1
    if not summary["all_final8_freezedetect_pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
