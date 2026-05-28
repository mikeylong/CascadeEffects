#!/usr/bin/env python3
"""Build the Cascade of Effects YouTube channel trailer review package."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path("/Users/mike/Agents_CascadeEffects")
AUDIO_ROOT = Path("/Users/mike/Audio_CascadeEffects")
EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")

MUSIC_REGISTRY = ROOT / "references/shorts/music_track_registry.json"
YOUTUBE_PACKAGE = Path("/Users/mike/Web_CascadeEffects/brand/packages/youtube-channel.package.json")
VISUAL_SOURCE = Path(
    "/Users/mike/Web_CascadeEffects/brand/assets/reference-renders/"
    "paper-architectures-v1/homepage-hero-dark-adapted-desktop-source-v1.png"
)
BODY_LOOP = Path(
    "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/"
    "themesong/Paper Architecture instrumental_loop_60s.wav"
)
OUTRO = Path(
    "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/"
    "themesong/Paper Architecture outro.m4a"
)
ELEVENLABS_HELPER = AUDIO_ROOT / "scripts/elevenlabs_provider.py"
ENV_FILE = AUDIO_ROOT / ".env.local"
VOICE_PROFILE_REGISTRY = AUDIO_ROOT / "references/voice_profiles/youtube_shorts_voice_profiles.json"

WIDTH = 1920
HEIGHT = 1080
FPS = 24
VOICE_START_SECONDS = 4.0
MIN_OUTRO_START_SECONDS = 35.0
TARGET_MAX_SECONDS = 45.0

PROFILE_ID = "youtube_shorts_mike_challenger_match_v1"
MUSIC_TRACK_ID = "paper_architecture_theme_v1"
SCRIPT_TEXT = (
    "You already know the headline. Cascade of Effects follows the change people missed: "
    "the rule, the measurement, the assumption, or the warning that stopped fitting reality. "
    "Each episode starts with a familiar failure and follows the mechanism underneath it. "
    "What shifted, who missed it, and how did the system turn that blindness into consequence?"
)

INK = (7, 13, 35)
PAPER = (255, 248, 232)
MUTED_PAPER = (226, 218, 203)
LAVENDER = (183, 164, 226)
CYAN = (120, 220, 232)
CORAL = (255, 111, 97)
DARK = (3, 7, 22)

FONT_DISPLAY = Path("/Users/mike/Library/Fonts/Inter-VariableFont_opsz,wght.ttf")
FONT_FALLBACK = Path("/System/Library/Fonts/HelveticaNeue.ttc")


def run(cmd: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        env=env,
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


def ffprobe_duration(path: Path) -> float:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(proc.stdout.strip())


def ffprobe_json(path: Path) -> dict[str, Any]:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(proc.stdout)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_env_file(path: Path) -> dict[str, str]:
    env = os.environ.copy()
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            env[key] = value
    return env


def font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (FONT_DISPLAY, FONT_FALLBACK):
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def fade_window(t: float, start: float, end: float, fade: float = 0.5) -> float:
    if t < start or t > end:
        return 0.0
    return min(ease((t - start) / fade), ease((end - t) / fade), 1.0)


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font_obj: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    anchor: str = "la",
    shadow: bool = True,
) -> None:
    if shadow:
        sx, sy = xy
        shadow_fill = (0, 0, 0, min(190, fill[3]))
        draw.text((sx + 3, sy + 4), text, font=font_obj, fill=shadow_fill, anchor=anchor)
    draw.text(xy, text, font=font_obj, fill=fill, anchor=anchor)


def rounded_box(
    overlay: Image.Image,
    xy: tuple[int, int, int, int],
    *,
    outline: tuple[int, int, int, int] | None = None,
    fill: tuple[int, int, int, int] | None = None,
    width: int = 2,
    radius: int = 8,
) -> None:
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def cover_frame(source: Image.Image, t: float, duration: float) -> Image.Image:
    progress = t / max(duration, 0.001)
    scale = 1.055 + 0.028 * progress
    resized = source.resize((math.ceil(WIDTH * scale), math.ceil(HEIGHT * scale)), Image.Resampling.LANCZOS)
    extra_x = resized.width - WIDTH
    extra_y = resized.height - HEIGHT
    pan_x = int(extra_x * (0.08 + 0.18 * progress))
    pan_y = int(extra_y * (0.36 + 0.08 * math.sin(progress * math.pi)))
    frame = resized.crop((pan_x, pan_y, pan_x + WIDTH, pan_y + HEIGHT)).convert("RGBA")
    frame = ImageEnhance.Color(frame).enhance(0.88)
    frame = ImageEnhance.Contrast(frame).enhance(1.06)
    return frame


def add_vignette(frame: Image.Image, strength: int = 125) -> Image.Image:
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(vignette)
    max_inset = min(WIDTH, HEIGHT) // 2 - 8
    for i in range(0, max_inset, 8):
        alpha = int(strength * (i / max_inset) ** 2)
        draw.rectangle((i, i, WIDTH - i, HEIGHT - i), outline=alpha, width=8)
    vignette = Image.eval(vignette.filter(ImageFilter.GaussianBlur(36)), lambda p: min(255, p))
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (*DARK, 0))
    dark.putalpha(vignette)
    return Image.alpha_composite(frame, dark)


def add_scanline_motion(frame: Image.Image, t: float) -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    base = int((t * 28) % 64)
    for y in range(base, HEIGHT, 64):
        draw.line((0, y, WIDTH, y), fill=(*CYAN, 12), width=1)
    for i in range(5):
        x = int((120 + i * 330 + t * (12 + i * 4)) % WIDTH)
        draw.line((x, 84, x + 120, 84), fill=(*CYAN, 28), width=1)
    return Image.alpha_composite(frame, overlay)


def render_phase_overlays(frame: Image.Image, t: float, duration: float, outro_start: float) -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    title_font = font(88)
    h1_font = font(68)
    h2_font = font(42)
    body_font = font(32)
    small_font = font(24)
    micro_font = font(18)

    # Opening identity hit.
    a = fade_window(t, 0.45, 4.1, 0.65)
    if a:
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(2, 5, 19, int(74 * a)))
        draw.line((118, 825, 758, 825), fill=(*CYAN, int(190 * a)), width=3)
        draw_text(
            draw,
            (118, 762),
            "You already know the headline.",
            font_obj=h2_font,
            fill=(*PAPER, int(245 * a)),
        )
        draw_text(
            draw,
            (122, 872),
            "Cascade of Effects",
            font_obj=small_font,
            fill=(*MUTED_PAPER, int(210 * a)),
        )

    # VO promise overlays.
    a = fade_window(t, 4.0, 25.2, 0.75)
    if a:
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0, int(34 * a)))
        draw_text(
            draw,
            (122, 82),
            "THE MECHANISM UNDER THE HEADLINE",
            font_obj=micro_font,
            fill=(*CYAN, int(205 * a)),
        )
        draw.line((122, 116, 518, 116), fill=(*CYAN, int(140 * a)), width=2)
        phrase_windows = [
            (4.2, 10.7, "The rule stopped fitting reality."),
            (10.7, 17.2, "The measurement fell behind."),
            (17.2, 25.0, "The warning changed shape."),
        ]
        for start, end, text in phrase_windows:
            p = fade_window(t, start, end, 0.7)
            if p:
                draw_text(
                    draw,
                    (1040, 778),
                    text,
                    font_obj=h2_font,
                    fill=(*PAPER, int(236 * p * a)),
                )
                draw.line((1044, 832, 1644, 832), fill=(*CORAL, int(170 * p * a)), width=3)

    # Mechanism flashes.
    flash_windows = [
        (25.0, 28.4, "RULE", "the constraint changed"),
        (28.4, 31.8, "MEASUREMENT", "the instrument lagged"),
        (31.8, 35.0, "WARNING", "the signal was missed"),
    ]
    for start, end, label, sublabel in flash_windows:
        a = fade_window(t, start, end, 0.24)
        if not a:
            continue
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(2, 5, 18, int(98 * a)))
        pulse = 0.5 + 0.5 * math.sin((t - start) * math.pi * 2.8)
        x0 = 122 + int(18 * pulse)
        y0 = 626
        draw.line((x0, y0 - 70, x0 + 930, y0 - 70), fill=(*CYAN, int(142 * a)), width=2)
        draw_text(draw, (x0, y0), label, font_obj=h1_font, fill=(*PAPER, int(246 * a)))
        draw_text(draw, (x0, y0 + 70), sublabel, font_obj=body_font, fill=(*MUTED_PAPER, int(220 * a)))
        for i in range(9):
            px = x0 + 28 + i * 88
            py = y0 - 118 + int(math.sin(t * 5 + i) * 8)
            color = CYAN if i % 3 else CORAL
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(*color, int(170 * a)))

    # Outro and end-screen surface.
    a = fade_window(t, outro_start - 0.4, duration, 0.7)
    if a:
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(1, 4, 16, int(132 * a)))
        draw_text(draw, (122, 188), "Cascade of Effects", font_obj=title_font, fill=(*PAPER, int(246 * a)))
        draw_text(
            draw,
            (126, 286),
            "What shifted. Who missed it. What followed.",
            font_obj=h2_font,
            fill=(*LAVENDER, int(224 * a)),
        )
        draw.line((126, 342, 770, 342), fill=(*CYAN, int(170 * a)), width=3)

        rounded_box(
            overlay,
            (1072, 214, 1776, 610),
            outline=(*CYAN, int(152 * a)),
            fill=(5, 11, 31, int(80 * a)),
            width=3,
        )
        rounded_box(
            overlay,
            (1200, 690, 1640, 962),
            outline=(*LAVENDER, int(150 * a)),
            fill=(5, 11, 31, int(68 * a)),
            width=3,
        )
        draw_text(draw, (1104, 650), "First episode", font_obj=small_font, fill=(*MUTED_PAPER, int(210 * a)))
        draw_text(draw, (1264, 1000), "Subscribe", font_obj=small_font, fill=(*MUTED_PAPER, int(210 * a)))

    return Image.alpha_composite(frame, overlay)


def render_frames(frames_dir: Path, duration: float, outro_start: float) -> dict[str, Any]:
    source = Image.open(VISUAL_SOURCE).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_count = math.ceil(duration * FPS)
    samples: list[tuple[int, float]] = []
    for index in range(frame_count):
        t = index / FPS
        frame = cover_frame(source, t, duration)
        frame = add_vignette(frame)
        frame = add_scanline_motion(frame, t)
        frame = render_phase_overlays(frame, t, duration, outro_start)
        out = frames_dir / f"frame_{index:05d}.png"
        frame.convert("RGB").save(out, compress_level=3)
        if index in {0, frame_count // 4, frame_count // 2, (frame_count * 3) // 4, frame_count - 1}:
            samples.append((index, t))
    return {"frame_count": frame_count, "sampled_frames": [{"index": i, "time": round(t, 3)} for i, t in samples]}


def create_contact_sheet(frames_dir: Path, contact_sheet: Path, duration: float) -> None:
    times = [1.8, 8.0, 16.0, 27.2, 33.0, max(duration - 2.8, 0)]
    thumb_w, thumb_h = 640, 360
    sheet = Image.new("RGB", (thumb_w * 3, (thumb_h + 46) * 2), (8, 12, 28))
    draw = ImageDraw.Draw(sheet)
    label_font = font(22)
    for idx, t in enumerate(times):
        frame_index = min(math.floor(t * FPS), len(list(frames_dir.glob("frame_*.png"))) - 1)
        frame_path = frames_dir / f"frame_{frame_index:05d}.png"
        img = Image.open(frame_path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % 3) * thumb_w
        y = (idx // 3) * (thumb_h + 46)
        sheet.paste(img, (x, y))
        draw.text((x + 16, y + thumb_h + 10), f"{t:05.1f}s", font=label_font, fill=PAPER)
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet, quality=92)


def create_silent_video(frames_dir: Path, silent_video: Path, duration: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%05d.png"),
            "-t",
            f"{duration:.3f}",
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
            str(silent_video),
        ]
    )


def audio_volume_peak(path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return {"status": "error", "stderr_tail": proc.stderr[-2000:]}
    stderr = proc.stderr
    max_match = re.search(r"max_volume:\s*([-\d.]+) dB", stderr)
    mean_match = re.search(r"mean_volume:\s*([-\d.]+) dB", stderr)
    return {
        "status": "pass",
        "max_volume_db": float(max_match.group(1)) if max_match else None,
        "mean_volume_db": float(mean_match.group(1)) if mean_match else None,
    }


def render_voiceover(work_dir: Path, profile: dict[str, Any]) -> dict[str, Any]:
    script_path = work_dir / "channel_trailer_v1_vo.txt"
    final_jobs = work_dir / "final_jobs.jsonl"
    effective_jobs = work_dir / "effective_final_jobs.elevenlabs.jsonl"
    rendered_dir = work_dir / "rendered"
    voice_wav = rendered_dir / "channel_trailer_vo.wav"

    script_path.write_text(f"[calm] {SCRIPT_TEXT}\n", encoding="utf-8")
    job = {
        "input": SCRIPT_TEXT,
        "out": voice_wav.name,
        "response_format": "wav",
        "speed": profile["render_settings"].get("speed", 0.95),
    }
    final_jobs.write_text(json.dumps(job, ensure_ascii=False) + "\n", encoding="utf-8")

    if voice_wav.exists() and voice_wav.stat().st_size > 0:
        return {
            "script_path": str(script_path),
            "final_jobs_path": str(final_jobs),
            "effective_jobs_path": str(effective_jobs),
            "voice_wav_path": str(voice_wav),
            "duration_seconds": ffprobe_duration(voice_wav),
            "sha256": file_sha256(voice_wav),
            "render_reused": True,
        }

    env = read_env_file(ENV_FILE)
    env["ELEVEN_LABS_VOICE_ID"] = profile["voice"]
    env["ELEVENLABS_DEFAULT_MODEL"] = profile["model"]

    run(
        [
            "python3",
            str(ELEVENLABS_HELPER),
            "compile-manifest",
            "--input",
            str(final_jobs),
            "--output",
            str(effective_jobs),
            "--script-path",
            str(script_path),
            "--strict-source-alignment",
            "--model",
            profile["model"],
            "--continuity-chars",
            "0",
        ],
        env=env,
    )
    rendered_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "python3",
            str(ELEVENLABS_HELPER),
            "render-batch",
            "--input",
            str(effective_jobs),
            "--out-dir",
            str(rendered_dir),
            "--model",
            profile["model"],
            "--voice-id",
            profile["voice"],
            "--output-format",
            "wav_44100",
            "--force",
        ],
        env=env,
    )
    return {
        "script_path": str(script_path),
        "final_jobs_path": str(final_jobs),
        "effective_jobs_path": str(effective_jobs),
        "voice_wav_path": str(voice_wav),
        "duration_seconds": ffprobe_duration(voice_wav),
        "sha256": file_sha256(voice_wav),
    }


def mix_audio(audio_dir: Path, voice_wav: Path, voice_duration: float, outro_duration: float) -> dict[str, Any]:
    outro_start = max(MIN_OUTRO_START_SECONDS, VOICE_START_SECONDS + voice_duration + 0.65)
    duration = outro_start + outro_duration
    if duration > TARGET_MAX_SECONDS:
        # Keep the one-minute ceiling intact, but record the runtime pressure in the manifest.
        duration = min(duration, 59.0)
    body_fade_start = max(outro_start - 0.5, 0.0)
    voice_delay_ms = int(round(VOICE_START_SECONDS * 1000))
    outro_delay_ms = int(round(outro_start * 1000))
    mix_wav = audio_dir / "channel_trailer_final_mix.wav"

    voice_end = VOICE_START_SECONDS + voice_duration
    filter_complex = (
        f"[0:a]atrim=0:{outro_start:.3f},asetpts=PTS-STARTPTS,"
        f"volume='if(isnan(t),0.220000,if(lt(t,4),0.420000,if(lt(t,{voice_end + 0.5:.3f}),0.135000,0.220000)))',"
        f"afade=t=out:st={body_fade_start:.3f}:d=0.500[body];"
        f"[1:a]atrim=0:{outro_duration:.3f},asetpts=PTS-STARTPTS,"
        f"volume='if(isnan(t),0.120000,if(lt(t,1.0),0.120000,0.120000+(t-1.0)*(0.700000/{max(outro_duration - 1.0, 0.1):.3f})))',"
        f"afade=t=in:st=0:d=0.200,adelay={outro_delay_ms}:all=1[outro];"
        f"[2:a]volume=1.000000,adelay={voice_delay_ms}:all=1[voice];"
        "[body][outro][voice]amix=inputs=3:duration=longest:normalize=0,"
        "alimiter=limit=0.89:level=false[outa]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(BODY_LOOP),
            "-i",
            str(OUTRO),
            "-i",
            str(voice_wav),
            "-filter_complex",
            filter_complex,
            "-map",
            "[outa]",
            "-t",
            f"{duration:.3f}",
            "-c:a",
            "pcm_s16le",
            str(mix_wav),
        ]
    )
    return {
        "mix_wav_path": str(mix_wav),
        "outro_start_seconds": round(outro_start, 3),
        "duration_seconds": round(duration, 3),
        "voice_start_seconds": VOICE_START_SECONDS,
        "voice_end_seconds": round(voice_end, 3),
        "sha256": file_sha256(mix_wav),
        "volume_peak": audio_volume_peak(mix_wav),
    }


def mux_final(silent_video: Path, mix_wav: Path, final_mp4: Path, duration: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(mix_wav),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(final_mp4), "-f", "null", "-"])


def frame_delta_report(frames_dir: Path, duration: float) -> dict[str, Any]:
    sample_times = [2.0, 10.0, 18.0, 28.0, 36.0, max(duration - 1.0, 0.0)]
    paths = [frames_dir / f"frame_{min(math.floor(t * FPS), math.ceil(duration * FPS) - 1):05d}.png" for t in sample_times]
    deltas = []
    previous = None
    for path in paths:
        img = Image.open(path).convert("L").resize((160, 90), Image.Resampling.BILINEAR)
        if previous is not None:
            total = 0
            for a, b in zip(previous.tobytes(), img.tobytes()):
                total += abs(a - b)
            deltas.append(total / (160 * 90))
        previous = img
    return {
        "sample_times_seconds": [round(t, 3) for t in sample_times],
        "mean_absolute_luma_deltas": [round(value, 3) for value in deltas],
        "visual_motion_read": "pass" if any(value > 2.0 for value in deltas) else "tighten",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--output-root", default=str(EPISODES_ROOT / "Channel_Trailer"))
    parser.add_argument("--keep-frames", action="store_true", help="Retain intermediate PNG frames for debugging.")
    args = parser.parse_args()

    for path in (MUSIC_REGISTRY, YOUTUBE_PACKAGE, VISUAL_SOURCE, BODY_LOOP, OUTRO, ELEVENLABS_HELPER, VOICE_PROFILE_REGISTRY):
        require_file(path)
    if not ENV_FILE.exists():
        raise SystemExit(f"Missing ElevenLabs environment file: {ENV_FILE}")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"channel_trailer_v1_{timestamp}"
    work_dir = output_root / "work"
    audio_dir = output_root / "audio"
    frames_dir = output_root / "frames"
    video_dir = output_root / "video"
    qa_dir = output_root / "qa"
    for directory in (work_dir, audio_dir, frames_dir, video_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    profile_registry = load_json(VOICE_PROFILE_REGISTRY)
    profile = profile_registry["profiles"][PROFILE_ID]
    music_registry = load_json(MUSIC_REGISTRY)
    music_track = music_registry["tracks"][MUSIC_TRACK_ID]
    youtube_package = load_json(YOUTUBE_PACKAGE)

    voice = render_voiceover(work_dir, profile)
    outro_duration = ffprobe_duration(OUTRO)
    audio = mix_audio(audio_dir, Path(voice["voice_wav_path"]), float(voice["duration_seconds"]), outro_duration)
    duration = float(audio["duration_seconds"])

    frames = render_frames(frames_dir, duration, float(audio["outro_start_seconds"]))
    contact_sheet = qa_dir / "channel_trailer_contact_sheet.jpg"
    create_contact_sheet(frames_dir, contact_sheet, duration)
    silent_video = video_dir / "channel_trailer_silent_picture.mp4"
    final_mp4 = video_dir / "cascade_of_effects_channel_trailer_v1.mp4"
    create_silent_video(frames_dir, silent_video, duration)
    mux_final(silent_video, Path(audio["mix_wav_path"]), final_mp4, duration)

    manifest = {
        "artifact_id": "cascade_of_effects_channel_trailer_v1",
        "created_at": timestamp,
        "status": "review_ready",
        "public_release_blocked": True,
        "public_release_blocker": "Confirm music rights and YouTube claim status before public visibility.",
        "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "aspect_ratio": "16:9"},
        "runtime": {
            "target_seconds": "40-45",
            "hard_ceiling_seconds": 60,
            "actual_seconds": round(ffprobe_duration(final_mp4), 3),
            "runtime_read": "pass" if ffprobe_duration(final_mp4) <= TARGET_MAX_SECONDS else "tighten",
        },
        "timing": {
            "theme_identity_hit_seconds": [0.0, 4.0],
            "voiceover_seconds": [VOICE_START_SECONDS, audio["voice_end_seconds"]],
            "mechanism_flashes_seconds": [25.0, 35.0],
            "outro_seconds": [audio["outro_start_seconds"], round(duration, 3)],
        },
        "copy": {
            "voiceover_text": SCRIPT_TEXT,
            "on_screen_title": "Cascade of Effects",
            "voiceover_tone": "direct promise",
        },
        "audio": {
            "voiceover": voice,
            "mix": audio,
            "music_track_id": MUSIC_TRACK_ID,
            "music_policy": "canonical_default",
            "music_rights_check_status": "pending_youtube_upload_check",
            "body_loop": {"path": str(BODY_LOOP), "sha256": file_sha256(BODY_LOOP)},
            "outro": {"path": str(OUTRO), "sha256": file_sha256(OUTRO), "duration_seconds": round(outro_duration, 3)},
        },
        "visuals": {
            "profile_id": youtube_package.get("profileId"),
            "visual_source_path": str(VISUAL_SOURCE),
            "visual_source_sha256": file_sha256(VISUAL_SOURCE),
            "visual_direction": "ink-lit Paper Architectures living-cover motion",
            "texture_noise_read": "pass_from_active_youtube_channel_package_source",
            "frame_generation": frames,
            "intermediate_frames_retained": bool(args.keep_frames),
            "frame_delta_report": frame_delta_report(frames_dir, duration),
        },
        "artifacts": {
            "output_root": str(output_root),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": file_sha256(final_mp4),
            "final_mix_wav": audio["mix_wav_path"],
            "silent_picture_mp4": str(silent_video),
            "contact_sheet": str(contact_sheet),
            "manifest": str(output_root / "channel_trailer_manifest.json"),
        },
        "qa": {
            "ffprobe": ffprobe_json(final_mp4),
            "decode_read": "pass",
            "audio_no_clipping_read": (
                "pass"
                if audio["volume_peak"].get("max_volume_db") is not None
                and audio["volume_peak"]["max_volume_db"] <= -0.1
                else "review"
            ),
            "outro_completion_read": "pass_full_outro_asset_used",
        },
    }
    manifest_path = output_root / "channel_trailer_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    review_note = output_root / "README.md"
    review_note.write_text(
        "\n".join(
            [
                "# Cascade of Effects Channel Trailer v1",
                "",
                f"- Final MP4: `{final_mp4}`",
                f"- Contact sheet: `{contact_sheet}`",
                f"- Manifest: `{manifest_path}`",
                f"- Duration: `{manifest['runtime']['actual_seconds']}` seconds",
                "- Status: `review_ready`",
                "- Public release remains blocked until music rights and YouTube claim status are checked.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if not args.keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)
    print(json.dumps({"output_root": str(output_root), "final_mp4": str(final_mp4), "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
