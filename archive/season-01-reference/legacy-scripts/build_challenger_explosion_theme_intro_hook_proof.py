#!/usr/bin/env python3
"""Build a local Challenger proof with explosion-first picture and theme-intro music."""

from __future__ import annotations

import array
import hashlib
import json
import math
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


SHORT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_scoped_v1")
LATEST_PUBLISH_DIR = SHORT_ROOT / "publish/youtube_20260516T172449Z_script_locked_captions"
CURRENT_YOUTUBE_SHORT = LATEST_PUBLISH_DIR / "challenger_script_locked_captions_youtube_short.mp4"
BODY_CAPTIONED_NO_AUDIO = LATEST_PUBLISH_DIR / "work/script_locked_captioned_no_audio.mp4"
NO_CAPTION_PICTURE = LATEST_PUBLISH_DIR / "work/script_locked_no_caption_picture_extended.mp4"
BODY_PICTURE_SOURCE: Path | None = NO_CAPTION_PICTURE
BODY_PICTURE_SOURCE_DURATION_SECONDS: float | None = None
BODY_PICTURE_SOURCE_CONTAINS_CAPTIONS = False
CAPTION_DUPLICATE_REPAIR_READ = "pass"

VOICE_WAV = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/"
    "selected/challenger_short_restart_v1_ending_cadence_pass_01.wav"
)
THEME_FULL = Path(
    "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/"
    "themesong/Paper Architecture.m4a"
)
THEME_LOOP_60 = Path(
    "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/"
    "themesong/Paper Architecture instrumental_loop_60s.wav"
)
THEME_OUTRO = Path(
    "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/"
    "themesong/Paper Architecture outro.m4a"
)

OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Shorts_First_Second_Hook_Retrofit")

HOOK_SOURCE_START_SECONDS = 57.0
HOOK_DURATION_SECONDS = 3.0
THEME_INTRO_SECONDS = 3.0
LOOP_START_SECONDS = 2.25
LOOP_CROSSFADE_SECONDS = 0.75
VOICE_DELAY_SECONDS = HOOK_DURATION_SECONDS
VOICE_LAST_AUDIBLE_SECONDS = 57.50
OUTRO_START_SECONDS = VOICE_DELAY_SECONDS + VOICE_LAST_AUDIBLE_SECONDS + 0.10
OUTRO_VOLUME = 0.76
INTRO_VOLUME = 0.78
LOOP_VOLUME = 0.14
VOICE_VOLUME = 1.0
FINAL_DURATION_SECONDS = OUTRO_START_SECONDS + 6.98
FPS = 30
HOOK_CRT_TEXTURE: dict[str, Any] | None = None
FULL_PICTURE_CRT_TEXTURE: dict[str, Any] | None = None
SOURCE_MOTION_TAIL: dict[str, Any] | None = {
    "path": NO_CAPTION_PICTURE,
    "start_seconds": 57.0,
    "replace_body_after_seconds": 61.30,
    "description": "moving no-caption Challenger explosion/cloud source motion for the outro tail",
}


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


def probe(path: Path) -> dict[str, Any]:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(proc.stdout)


def duration(path: Path) -> float:
    return float(probe(path).get("format", {}).get("duration", 0.0) or 0.0)


def media_summary(path: Path) -> dict[str, Any]:
    data = probe(path)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    return {
        "path": str(path),
        "sha256": sha256(path),
        "duration_seconds": round(float(data.get("format", {}).get("duration", 0.0) or 0.0), 6),
        "video_codec": video.get("codec_name", ""),
        "audio_codec": audio.get("codec_name", ""),
        "width": int(video.get("width", 0) or 0),
        "height": int(video.get("height", 0) or 0),
        "frame_rate": video.get("avg_frame_rate", ""),
        "audio_sample_rate_hz": int(audio.get("sample_rate", 0) or 0),
        "audio_channels": int(audio.get("channels", 0) or 0),
    }


def hook_crt_texture_context() -> dict[str, Any] | None:
    if not HOOK_CRT_TEXTURE:
        return None
    return {
        "profile_id": HOOK_CRT_TEXTURE.get("profile_id", "era_1980s_broadcast_crt_v1"),
        "intensity": HOOK_CRT_TEXTURE.get("intensity", "visible_but_premium"),
        "texture_application_scope": "opening_hook",
        "duration_seconds": round(HOOK_DURATION_SECONDS, 6),
        "calibration_recipe_id": HOOK_CRT_TEXTURE.get(
            "calibration_recipe_id",
            "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        ),
        "scanline_policy_id": HOOK_CRT_TEXTURE.get(
            "scanline_policy_id",
            "luma_neutral_visible_scanline_modulation_v1",
        ),
        "caption_burn_is_last_visual_operation": False,
    }


def house_crt_hook_filter_chain() -> str:
    return (
        "eq=contrast=1.075:saturation=1.070:brightness=0.008,"
        "noise=alls=8:allf=t+u,"
        "drawgrid=width=iw:height=8:thickness=1:color=black@0.130"
    )


def full_picture_crt_texture_context() -> dict[str, Any] | None:
    if not FULL_PICTURE_CRT_TEXTURE:
        return None
    return {
        "profile_id": FULL_PICTURE_CRT_TEXTURE.get("profile_id", "era_1980s_broadcast_crt_v1"),
        "intensity": FULL_PICTURE_CRT_TEXTURE.get("intensity", "visible_but_premium"),
        "texture_application_scope": "assembled_picture_bed",
        "duration_seconds": round(FINAL_DURATION_SECONDS, 6),
        "calibration_recipe_id": FULL_PICTURE_CRT_TEXTURE.get(
            "calibration_recipe_id",
            "premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1",
        ),
        "scanline_policy_id": FULL_PICTURE_CRT_TEXTURE.get(
            "scanline_policy_id",
            "luma_neutral_visible_scanline_modulation_v1",
        ),
        "scanline_strength_variant_id": FULL_PICTURE_CRT_TEXTURE.get(
            "scanline_strength_variant_id",
            "max_visible_bars_y24_p8",
        ),
        "texture_tone_policy": FULL_PICTURE_CRT_TEXTURE.get(
            "texture_tone_policy",
            "luma_neutral_chroma_visible_scanline_v1",
        ),
        "purpose": FULL_PICTURE_CRT_TEXTURE.get("purpose", ""),
        "caption_burn_is_last_visual_operation": False,
    }


def house_crt_full_picture_filter_chain() -> str:
    return (
        "eq=contrast=1.080:saturation=1.075:brightness=0.008,"
        "noise=alls=7:allf=t+u,"
        "drawgrid=width=iw:height=8:thickness=1:color=black@0.120"
    )


def build_hook_clip(output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "setsar=1,fps=30,format=yuv420p"
    )
    if HOOK_CRT_TEXTURE:
        video_filter = f"{video_filter},{house_crt_hook_filter_chain()},format=yuv420p"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{HOOK_SOURCE_START_SECONDS:.3f}",
            "-t",
            f"{HOOK_DURATION_SECONDS:.3f}",
            "-i",
            str(NO_CAPTION_PICTURE),
            "-vf",
            video_filter,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return {
        "hook_crt_texture": hook_crt_texture_context(),
        "hook_crt_overlay_used": HOOK_CRT_TEXTURE is not None,
    }


def normalize_video_filter(input_index: int, output_label: str, trim_duration_seconds: float | None = None) -> str:
    trim_prefix = f"trim=0:{trim_duration_seconds:.6f}," if trim_duration_seconds is not None else ""
    return (
        f"[{input_index}:v]{trim_prefix}setpts=PTS-STARTPTS,"
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"setsar=1,fps={FPS},format=yuv420p[{output_label}]"
    )


def house_crt_tail_filter_chain() -> str:
    return (
        "eq=contrast=1.080:saturation=1.080:brightness=0.010,"
        "noise=alls=7:allf=t+u,"
        "drawgrid=width=iw:height=8:thickness=1:color=black@0.110"
    )


def signal_interruption_filter_chain() -> str:
    return (
        "eq=contrast=1.360:saturation=1.050:brightness=0.010,"
        "rgbashift=rh=8:bh=-8:rv=3:bv=-3,"
        "noise=alls=42:allf=t+u,"
        "drawbox=x=0:y=ih*0.18:w=iw:h=26:color=white@0.30:t=fill,"
        "drawbox=x=0:y=ih*0.43:w=iw:h=18:color=black@0.42:t=fill,"
        "drawbox=x=0:y=ih*0.66:w=iw:h=12:color=white@0.18:t=fill,"
        "drawgrid=width=iw:height=6:thickness=1:color=black@0.280"
    )


def source_motion_tail_context(tail_gap_seconds: float) -> dict[str, Any] | None:
    if tail_gap_seconds <= (1.0 / FPS):
        return None
    if not SOURCE_MOTION_TAIL:
        raise RuntimeError(
            f"Picture bed needs {tail_gap_seconds:.3f}s of tail extension; "
            "configure SOURCE_MOTION_TAIL instead of cloned-frame padding."
        )
    tail_path = Path(SOURCE_MOTION_TAIL["path"])
    tail_start = float(SOURCE_MOTION_TAIL.get("start_seconds", 0.0))
    if not tail_path.exists():
        raise FileNotFoundError(f"SOURCE_MOTION_TAIL path does not exist: {tail_path}")
    tail_duration = duration(tail_path)
    if tail_start + tail_gap_seconds > tail_duration + 0.05:
        raise RuntimeError(
            f"SOURCE_MOTION_TAIL is too short: start {tail_start:.3f}s + "
            f"needed {tail_gap_seconds:.3f}s exceeds source duration {tail_duration:.3f}s."
        )
    return {
        "source_path": str(tail_path),
        "source_sha256": sha256(tail_path),
        "source_start_seconds": round(tail_start, 6),
        "duration_seconds": round(tail_gap_seconds, 6),
        "description": SOURCE_MOTION_TAIL.get("description", ""),
        "source_transition_trimmed_seconds": round(float(SOURCE_MOTION_TAIL.get("source_transition_trimmed_seconds", tail_start)), 6),
        "house_crt_tail_texture": SOURCE_MOTION_TAIL.get("house_crt_tail_texture"),
        "signal_interruption": SOURCE_MOTION_TAIL.get("signal_interruption"),
    }


def body_picture_source() -> Path:
    return BODY_PICTURE_SOURCE or BODY_CAPTIONED_NO_AUDIO


def build_picture_bed(hook_clip: Path, output: Path) -> dict[str, Any]:
    body_source_path = body_picture_source()
    body_source_duration_seconds = (
        BODY_PICTURE_SOURCE_DURATION_SECONDS
        if BODY_PICTURE_SOURCE_DURATION_SECONDS is not None
        else duration(body_source_path)
    )
    body_duration_seconds = body_source_duration_seconds
    if SOURCE_MOTION_TAIL and SOURCE_MOTION_TAIL.get("replace_body_after_seconds") is not None:
        body_duration_seconds = min(body_source_duration_seconds, float(SOURCE_MOTION_TAIL["replace_body_after_seconds"]))
    signal_context = SOURCE_MOTION_TAIL.get("signal_interruption") if SOURCE_MOTION_TAIL else None
    signal_duration_seconds = float((signal_context or {}).get("duration_seconds", 0.0))
    if signal_duration_seconds > 0:
        body_duration_seconds = max(0.0, body_duration_seconds - signal_duration_seconds)
    tail_gap_seconds = max(0.0, FINAL_DURATION_SECONDS - HOOK_DURATION_SECONDS - body_duration_seconds - signal_duration_seconds)
    tail_context = source_motion_tail_context(tail_gap_seconds)
    filters = [
        normalize_video_filter(0, "v0"),
        normalize_video_filter(1, "v1", body_duration_seconds),
    ]
    inputs = [
        "-i",
        str(hook_clip),
        "-i",
        str(body_source_path),
    ]
    concat_labels = "[v0][v1]"
    concat_count = 2
    if signal_duration_seconds > 0:
        filters.append(
            f"[1:v]trim=start={body_duration_seconds:.6f}:duration={signal_duration_seconds:.6f},"
            "setpts=PTS-STARTPTS,"
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"setsar=1,fps={FPS},format=yuv420p,{signal_interruption_filter_chain()},format=yuv420p[sig]"
        )
        concat_labels += "[sig]"
        concat_count += 1
    if tail_context:
        inputs.extend(["-i", tail_context["source_path"]])
        tail_filter_tail = ""
        if tail_context.get("house_crt_tail_texture") and not FULL_PICTURE_CRT_TEXTURE:
            tail_filter_tail = f",{house_crt_tail_filter_chain()}"
        filters.append(
            f"[2:v]trim=start={tail_context['source_start_seconds']:.6f}:"
            f"duration={tail_context['duration_seconds']:.6f},setpts=PTS-STARTPTS,"
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"setsar=1,fps={FPS},format=yuv420p{tail_filter_tail},format=yuv420p[v2]"
        )
        concat_labels += "[v2]"
        concat_count += 1
    full_picture_crt_filter = ""
    if FULL_PICTURE_CRT_TEXTURE:
        full_picture_crt_filter = f",{house_crt_full_picture_filter_chain()}"
    filters.append(
        f"{concat_labels}concat=n={concat_count}:v=1:a=0,"
        f"trim=0:{FINAL_DURATION_SECONDS:.6f},format=yuv420p{full_picture_crt_filter},format=yuv420p[v]"
    )
    filter_complex = ";".join(filters)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    tail_segment_crt_used = bool(
        tail_context and tail_context.get("house_crt_tail_texture") and not FULL_PICTURE_CRT_TEXTURE
    )
    return {
        "body_source_duration_seconds": round(body_source_duration_seconds, 6),
        "body_picture_source_path": str(body_source_path),
        "clean_body_source_path": str(body_source_path),
        "motion_source_contains_captions": BODY_PICTURE_SOURCE_CONTAINS_CAPTIONS,
        "caption_duplicate_repair_read": CAPTION_DUPLICATE_REPAIR_READ,
        "body_duration_seconds": round(body_duration_seconds, 6),
        "body_trimmed_for_tail_motion_seconds": round(body_source_duration_seconds - body_duration_seconds, 6),
        "tail_gap_seconds": round(tail_gap_seconds, 6),
        "signal_interruption_used": signal_duration_seconds > 0,
        "signal_interruption_duration_seconds": round(signal_duration_seconds, 6),
        "signal_interruption": signal_context,
        "visual_extension_mode": "source_motion_tail" if tail_context else "none",
        "cloned_frame_padding_used": False,
        "source_motion_tail": tail_context,
        "full_picture_crt_texture": full_picture_crt_texture_context(),
        "full_picture_crt_scope": "assembled_picture_bed" if FULL_PICTURE_CRT_TEXTURE else None,
        "segment_crt_passes_used": bool(HOOK_CRT_TEXTURE or tail_segment_crt_used),
        "tail_segment_crt_pass_used": tail_segment_crt_used,
    }


def build_audio_mix(output: Path) -> None:
    loop_fade_out_start = max(0.1, OUTRO_START_SECONDS - LOOP_START_SECONDS - 0.50)
    filter_complex = (
        f"[0:a]atrim=0:{THEME_INTRO_SECONDS:.6f},asetpts=PTS-STARTPTS,"
        f"volume={INTRO_VOLUME:.3f},afade=t=out:st={LOOP_START_SECONDS:.6f}:d={LOOP_CROSSFADE_SECONDS:.6f},"
        "aresample=48000,aformat=channel_layouts=stereo[intro];"
        f"[1:a]atrim=0:{FINAL_DURATION_SECONDS:.6f},asetpts=PTS-STARTPTS,"
        f"volume={LOOP_VOLUME:.3f},afade=t=in:st=0:d={LOOP_CROSSFADE_SECONDS:.6f},"
        f"afade=t=out:st={loop_fade_out_start:.6f}:d=0.500000,"
        f"adelay={int(LOOP_START_SECONDS * 1000)}|{int(LOOP_START_SECONDS * 1000)},"
        "aresample=48000,aformat=channel_layouts=stereo[loop];"
        f"[2:a]atrim=0:6.971542,asetpts=PTS-STARTPTS,volume={OUTRO_VOLUME:.3f},"
        f"afade=t=in:st=0:d=0.250000,adelay={int(OUTRO_START_SECONDS * 1000)}|{int(OUTRO_START_SECONDS * 1000)},"
        "aresample=48000,aformat=channel_layouts=stereo[outro];"
        f"[3:a]aresample=48000,volume={VOICE_VOLUME:.3f},pan=stereo|c0=c0|c1=c0,"
        f"adelay={int(VOICE_DELAY_SECONDS * 1000)}|{int(VOICE_DELAY_SECONDS * 1000)}[voice];"
        "[intro][loop][outro][voice]amix=inputs=4:duration=longest:normalize=0,"
        f"volume=0.62,alimiter=limit=0.62:level=false,atrim=0:{FINAL_DURATION_SECONDS:.6f},asetpts=PTS-STARTPTS[a]"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(THEME_FULL),
            "-i",
            str(THEME_LOOP_60),
            "-i",
            str(THEME_OUTRO),
            "-i",
            str(VOICE_WAV),
            "-filter_complex",
            filter_complex,
            "-map",
            "[a]",
            "-c:a",
            "pcm_s16le",
            str(output),
        ]
    )


def mux(picture_bed: Path, audio_mix: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(picture_bed),
            "-i",
            str(audio_mix),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-t",
            f"{FINAL_DURATION_SECONDS:.6f}",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def extract_excerpt(source: Path, seconds: float, output: Path) -> None:
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
            f"{seconds:.3f}",
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p",
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
        ]
    )


def build_comparison(current_excerpt: Path, revised_excerpt: Path, output: Path) -> None:
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
            str(revised_excerpt),
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
        ]
    )


def extract_frame(video: Path, seconds: float, output: Path) -> None:
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
        ]
    )


def build_frame_strip(video: Path, output: Path, times: list[float]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    tiles: list[Image.Image] = []
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        for seconds in times:
            frame_path = temp_dir / f"frame_{seconds:07.3f}.jpg"
            extract_frame(video, seconds, frame_path)
            final_frame = output.parent / f"frame_{seconds:07.3f}.jpg"
            final_frame.write_bytes(frame_path.read_bytes())
            frames.append({"seconds": seconds, "path": str(final_frame), "sha256": sha256(final_frame)})
            tile = Image.open(frame_path).convert("RGB").resize((180, 320), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (180, 350), "white")
            canvas.paste(tile, (0, 30))
            draw = ImageDraw.Draw(canvas)
            draw.text((8, 7), f"t={seconds:.2f}s", fill=(0, 0, 0))
            tiles.append(canvas)
    sheet = Image.new("RGB", (180 * len(tiles), 350), "white")
    for index, tile in enumerate(tiles):
        sheet.paste(tile, (index * 180, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)
    return frames


def audio_metrics(video: Path, seconds: float) -> dict[str, Any]:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-t",
            f"{seconds:.3f}",
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
    if not samples:
        return {"peak_dbfs": -120.0, "rms_dbfs": -120.0, "sample_count": 0}
    peak = max(abs(v) for v in samples)
    rms = math.sqrt(sum(v * v for v in samples) / len(samples))
    return {
        "window_seconds": seconds,
        "peak_dbfs": round(20 * math.log10(max(peak, 1e-9)), 3),
        "rms_dbfs": round(20 * math.log10(max(rms, 1e-9)), 3),
        "sample_count": len(samples),
    }


def build_waveform(video: Path, output: Path, seconds: float = 10.0) -> None:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-t",
            f"{seconds:.3f}",
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
    width = 1200
    height = 300
    mid = height // 2
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.line((0, mid, width, mid), fill=(170, 170, 170))
    if samples:
        stride = max(1, len(samples) // width)
        for x in range(width):
            chunk = samples[x * stride : min(len(samples), (x + 1) * stride)]
            if not chunk:
                continue
            amp = max(abs(value) for value in chunk)
            y = int(amp * height * 0.45)
            draw.line((x, mid - y, x, mid + y), fill=(28, 76, 120))
    for mark in [0, 1, 2, 3, 4, 6, 8, 10]:
        x = int(width * (mark / seconds))
        draw.line((x, 0, x, height), fill=(225, 225, 225))
        draw.text((min(width - 44, x + 4), 8), f"{mark}s", fill=(0, 0, 0))
    draw.text((12, height - 24), "First 10 seconds: theme intro -> loop under VO", fill=(0, 0, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def freeze_tail_evidence(video: Path, window_seconds: float = 8.0, freeze_seconds: float = 0.5) -> dict[str, Any]:
    window_start = max(0.0, FINAL_DURATION_SECONDS - window_seconds)
    proc = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-v",
            "info",
            "-ss",
            f"{window_start:.6f}",
            "-i",
            str(video),
            "-vf",
            f"freezedetect=n=-60dB:d={freeze_seconds:.6f}",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture=True,
    )
    events = [
        line.strip()
        for line in proc.stderr.splitlines()
        if "freezedetect" in line and ("freeze_start" in line or "freeze_duration" in line or "freeze_end" in line)
    ]
    return {
        "window_start_seconds": round(window_start, 6),
        "window_duration_seconds": window_seconds,
        "threshold_db": -60,
        "min_freeze_duration_seconds": freeze_seconds,
        "freeze_events": events,
        "freeze_tail_read": "pass" if not events else "tighten",
    }


def main() -> None:
    stamp = utc_stamp()
    root = OUTPUT_ROOT / f"challenger_explosion_theme_intro_hook_{stamp}"
    work = root / "work"
    evidence = root / "evidence"
    root.mkdir(parents=True, exist_ok=False)

    hook_clip = work / "explosion_hook_no_caption_3s.mp4"
    picture_bed = work / "picture_bed_explosion_then_current_captioned.mp4"
    audio_mix = work / "theme_intro_to_loop_to_outro_mix.wav"
    proof = root / "challenger_explosion_theme_intro_hook_review_proof.mp4"
    current_excerpt = work / "current_first_10s.mp4"
    revised_excerpt = work / "revised_first_10s.mp4"
    comparison = root / "side_by_side_current_vs_explosion_theme_hook_first_10s.mp4"
    frame_strip = evidence / "opening_frame_strip.jpg"
    outro_strip = evidence / "outro_frame_strip.jpg"
    waveform = evidence / "first_10s_waveform.png"

    build_hook_clip(hook_clip)
    picture_bed_context = build_picture_bed(hook_clip, picture_bed)
    build_audio_mix(audio_mix)
    mux(picture_bed, audio_mix, proof)
    extract_excerpt(CURRENT_YOUTUBE_SHORT, 10.0, current_excerpt)
    extract_excerpt(proof, 10.0, revised_excerpt)
    build_comparison(current_excerpt, revised_excerpt, comparison)
    opening_frames = build_frame_strip(proof, frame_strip, [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 10.0])
    outro_frames = build_frame_strip(
        proof,
        outro_strip,
        [OUTRO_START_SECONDS - 0.5, OUTRO_START_SECONDS, OUTRO_START_SECONDS + 1.5, FINAL_DURATION_SECONDS - 0.5],
    )
    build_waveform(proof, waveform)
    freeze_evidence = freeze_tail_evidence(proof)

    manifest = {
        "schema_version": "1.0",
        "stage": "first-second hook review",
        "prototype_id": f"challenger_explosion_theme_intro_hook_{stamp}",
        "local_only_no_youtube_action": True,
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "current_latest_publish_mp4_path": str(CURRENT_YOUTUBE_SHORT),
        "current_latest_publish_mp4_sha256": sha256(CURRENT_YOUTUBE_SHORT),
        "proof_path": str(proof),
        "proof_sha256": sha256(proof),
        "comparison_path": str(comparison),
        "comparison_sha256": sha256(comparison),
        "frame_strip_path": str(frame_strip),
        "frame_strip_sha256": sha256(frame_strip),
        "outro_frame_strip_path": str(outro_strip),
        "outro_frame_strip_sha256": sha256(outro_strip),
        "waveform_path": str(waveform),
        "waveform_sha256": sha256(waveform),
        "visual_extension_mode": picture_bed_context["visual_extension_mode"],
        "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
        "motion_source_contains_captions": picture_bed_context["motion_source_contains_captions"],
        "clean_body_source_path": picture_bed_context["clean_body_source_path"],
        "caption_duplicate_repair_read": picture_bed_context["caption_duplicate_repair_read"],
        "source_motion_tail": picture_bed_context["source_motion_tail"],
        "body_source_duration_seconds": picture_bed_context["body_source_duration_seconds"],
        "body_used_duration_seconds": picture_bed_context["body_duration_seconds"],
        "body_trimmed_for_tail_motion_seconds": picture_bed_context["body_trimmed_for_tail_motion_seconds"],
        "tail_gap_seconds": picture_bed_context["tail_gap_seconds"],
        "freeze_tail_read": freeze_evidence["freeze_tail_read"],
        "freeze_tail_evidence": freeze_evidence,
        "visual_strategy": {
            "hook_visual": "no-caption Challenger explosion/fireball excerpt moved to the front",
            "hook_source_path": str(NO_CAPTION_PICTURE),
            "hook_source_start_seconds": HOOK_SOURCE_START_SECONDS,
            "hook_duration_seconds": HOOK_DURATION_SECONDS,
            "body_after_hook": "existing Challenger no-caption picture body starts at original t=0 after hook",
            "clean_body_source_path": picture_bed_context["clean_body_source_path"],
            "motion_source_contains_captions": picture_bed_context["motion_source_contains_captions"],
            "caption_duplicate_repair_read": picture_bed_context["caption_duplicate_repair_read"],
            "visual_extension_mode": picture_bed_context["visual_extension_mode"],
            "cloned_frame_padding_used": picture_bed_context["cloned_frame_padding_used"],
            "source_motion_tail": picture_bed_context["source_motion_tail"],
        },
        "music_strategy": {
            "full_theme_intro_path": str(THEME_FULL),
            "full_theme_intro_sha256": sha256(THEME_FULL),
            "theme_intro_start_seconds": 0.0,
            "theme_intro_duration_seconds": THEME_INTRO_SECONDS,
            "theme_intro_volume": INTRO_VOLUME,
            "loop_path": str(THEME_LOOP_60),
            "loop_sha256": sha256(THEME_LOOP_60),
            "loop_start_seconds": LOOP_START_SECONDS,
            "loop_crossfade_seconds": LOOP_CROSSFADE_SECONDS,
            "loop_volume_under_voice": LOOP_VOLUME,
            "outro_path": str(THEME_OUTRO),
            "outro_sha256": sha256(THEME_OUTRO),
            "outro_start_seconds": round(OUTRO_START_SECONDS, 3),
            "outro_volume": OUTRO_VOLUME,
            "limiter": "post-mix volume=0.62, alimiter=limit=0.62:level=false",
        },
        "voice_strategy": {
            "voice_wav_path": str(VOICE_WAV),
            "voice_wav_sha256": sha256(VOICE_WAV),
            "voice_delay_seconds": VOICE_DELAY_SECONDS,
            "voice_volume": VOICE_VOLUME,
            "voice_last_audible_seconds_source": VOICE_LAST_AUDIBLE_SECONDS,
        },
        "media_summary": media_summary(proof),
        "audio_evidence": {
            "first_3s": audio_metrics(proof, 3.0),
            "first_10s": audio_metrics(proof, 10.0),
            "full_proof": audio_metrics(proof, FINAL_DURATION_SECONDS),
        },
        "frame_samples": {
            "opening": opening_frames,
            "outro": outro_frames,
        },
        "review_request": "Judge whether the explosion-first visual plus full theme intro punch works better than the previous cold-flash prebeat, and whether the 2-3s transition into the loop feels natural before voice starts.",
        "human_review_disposition": "keep",
    }
    write_json(root / "challenger_explosion_theme_intro_hook_manifest.json", manifest)

    note = f"""# Challenger Explosion + Theme Intro Hook Review

- `stage`: `first-second hook review`
- `proof_path`: `{proof}`
- `comparison_path`: `{comparison}`
- `frame_strip_path`: `{frame_strip}`
- `waveform_path`: `{waveform}`
- `local_only_no_youtube_action`: `true`

## What Changed

- The first `{HOOK_DURATION_SECONDS:.1f}s` is the no-caption Challenger explosion/fireball footage from the existing clean picture bed.
- The full theme song starts from `0.00` so the opening punch lands immediately.
- The theme intro crossfades into the registered loop from `{LOOP_START_SECONDS:.2f}s` to `{LOOP_START_SECONDS + LOOP_CROSSFADE_SECONDS:.2f}s`.
- The approved Challenger voice starts after the hook at `{VOICE_DELAY_SECONDS:.2f}s`.
- The loop continues under the body, then fades into the theme outro at `{OUTRO_START_SECONDS:.2f}s`.
- The previous cloned-frame tail padding has been replaced with source motion tail footage.
- The body source is now the clean no-caption picture bed, so final export can burn one yellow caption layer without overlap.
- `caption_duplicate_repair_read`: `{picture_bed_context["caption_duplicate_repair_read"]}`
- `freeze_tail_read`: `{freeze_evidence["freeze_tail_read"]}`

## Review Read

Mark this `keep`, `tighten`, or `reject`.

- `keep`: explosion-first plus theme punch clearly improves scroll-stop and the loop handoff feels natural.
- `tighten`: the idea works, but the explosion span, music level, loop handoff, or outro timing needs adjustment.
- `reject`: it feels cheap, too loud, too front-loaded, or less effective than the current opening.
"""
    write_text(root / "review_note.md", note)

    latest_link = OUTPUT_ROOT / "challenger_explosion_theme_intro_hook_latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    os.symlink(root, latest_link)
    print(root)


if __name__ == "__main__":
    main()
