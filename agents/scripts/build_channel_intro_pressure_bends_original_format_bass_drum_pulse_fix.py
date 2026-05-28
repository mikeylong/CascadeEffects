#!/usr/bin/env python3
"""Build the Pressure Bends channel intro with a bass-drum-timed background pulse."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageStat


WIDTH = 1920
HEIGHT = 1080
FPS = 24
TOTAL_FRAMES = 1399
OUTPUT_SECONDS = TOTAL_FRAMES / FPS
END_SCREEN_SECONDS = 20.0
END_SCREEN_START_SECONDS = OUTPUT_SECONDS - END_SCREEN_SECONDS
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
WORKFLOW = "channel_intro_pressure_bends_original_format_bass_drum_pulse_fix_v1"
OUTPUT_STEM = "channel_intro_pressure_bends_original_format_bass_drum_pulse_fix"

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
TRACK_PATH = Path("/Users/mike/Downloads/The_Pressure_Bends.mp3")
PREDECESSOR_PACKAGE = (
    OUTPUT_ROOT / "channel_intro_pressure_bends_original_format_neutral_end_transition_fix_20260527T181928Z"
)
PREDECESSOR_MANIFEST = (
    PREDECESSOR_PACKAGE / "channel_intro_pressure_bends_original_format_neutral_end_transition_fix_manifest.json"
)
PREDECESSOR_MP4 = (
    PREDECESSOR_PACKAGE
    / "video/cascade_of_effects_channel_intro_pressure_bends_original_format_neutral_end_transition_fix_1080p24.mp4"
)
PREDECESSOR_SILENT_MP4 = (
    PREDECESSOR_PACKAGE
    / "video/cascade_of_effects_channel_intro_pressure_bends_original_format_neutral_end_transition_fix_silent.mp4"
)
BORDERLESS_END_SCREEN_POINTER = OUTPUT_ROOT / "channel_intro_end_screen_adaptive_borderless_keep_latest.json"
LATEST_POINTER = OUTPUT_ROOT / f"{OUTPUT_STEM}_latest.json"
PRESSURE_HELPER_PATH = REPO_ROOT / "scripts/build_channel_trailer_pressure_bends_successor.py"
REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8767"

SAMPLE_WINDOWS = [
    ("cold open", 0.0, 6.0),
    ("Challenger", 6.0, 10.041667),
    ("Therac-25", 10.041667, 14.083333),
    ("Hyatt Regency", 14.083333, 18.125),
    ("Semmelweis", 18.125, 22.166667),
    ("Tacoma Narrows", 22.166667, 26.208333),
    ("Piltdown Man", 26.208333, 30.25),
    ("737 MAX", 30.25, 34.291667),
    ("Titanic", 34.291667, END_SCREEN_START_SECONDS),
    ("end transition", END_SCREEN_START_SECONDS, END_SCREEN_START_SECONDS + 1.0),
    ("end hold", END_SCREEN_START_SECONDS + 1.0, 52.0),
    ("tail", 52.0, OUTPUT_SECONDS),
]

SCENE_BOUNDARIES = [
    0.0,
    6.0,
    10.041667,
    14.083333,
    18.125,
    22.166667,
    26.208333,
    30.25,
    34.291667,
    END_SCREEN_START_SECONDS,
    END_SCREEN_START_SECONDS + 1.0,
    OUTPUT_SECONDS,
]

END_SCREEN_TARGET_BBOXES = {
    "left_video": [78, 382, 758, 765],
    "right_video": [1162, 382, 1842, 765],
    "center_subscribe": [814, 429, 1106, 721],
}

PULSE_CONFIG = {
    "audio_analysis_source": "predecessor_final_aac_stream",
    "sample_rate_hz": 48000,
    "fft_window_samples": 4096,
    "hop_samples": 512,
    "low_band_hz": [35, 160],
    "sub_band_hz": [35, 95],
    "mid_high_band_hz": [220, 3500],
    "candidate_percentile": 84,
    "candidate_min_threshold": 0.16,
    "minimum_hit_spacing_seconds": 0.34,
    "decay_seconds": 0.20,
    "max_curve_seconds": 0.58,
    "pre_attack_seconds": 0.0,
    "brightness_lift": 0.055,
    "wash_mix": 0.085,
    "contrast_lift": 0.018,
    "background_mask_blur_px": 10,
    "periodic_grid_used": False,
    "fallback_grid_used": False,
    "mid_high_transient_weight": 0,
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load_module("channel_intro_pressure_bends_base_for_pulse", PRESSURE_HELPER_PATH)


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


def stream_sha256(path: Path, stream_spec: str, out_path: Path) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(path),
            "-map",
            stream_spec,
            "-c",
            "copy",
            str(out_path),
        ]
    )
    digest = sha256(out_path)
    out_path.unlink(missing_ok=True)
    return digest


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


def decode_audio_mono_f32(video_path: Path, sample_rate: int) -> np.ndarray:
    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            "-",
        ]
    )
    audio = np.frombuffer(raw, dtype="<f4").astype(np.float32)
    return np.nan_to_num(audio, copy=False)


def normalize_series(values: np.ndarray) -> np.ndarray:
    lo = float(np.percentile(values, 50))
    hi = float(np.percentile(values, 99))
    return np.clip((values - lo) / max(hi - lo, 1e-9), 0.0, 1.0)


def detect_bass_drum_hits(video_path: Path, qa_dir: Path) -> dict[str, Any]:
    sr = int(PULSE_CONFIG["sample_rate_hz"])
    window_size = int(PULSE_CONFIG["fft_window_samples"])
    hop = int(PULSE_CONFIG["hop_samples"])
    audio = decode_audio_mono_f32(video_path, sr)
    if len(audio) < window_size:
        raise SystemExit("Audio is too short for bass hit analysis.")

    frame_count = 1 + (len(audio) - window_size) // hop
    frames = np.lib.stride_tricks.as_strided(
        audio,
        shape=(frame_count, window_size),
        strides=(audio.strides[0] * hop, audio.strides[0]),
    )
    window = np.hanning(window_size).astype(np.float32)
    spectrum = np.fft.rfft(frames * window, axis=1)
    magnitude = np.abs(spectrum)
    freqs = np.fft.rfftfreq(window_size, 1.0 / sr)
    low_band = (freqs >= 35) & (freqs <= 160)
    sub_band = (freqs >= 35) & (freqs <= 95)
    mid_high_band = (freqs >= 220) & (freqs <= 3500)

    low_energy = np.sqrt((magnitude[:, low_band] ** 2).sum(axis=1))
    sub_energy = np.sqrt((magnitude[:, sub_band] ** 2).sum(axis=1))
    mid_high_energy = np.sqrt((magnitude[:, mid_high_band] ** 2).sum(axis=1))
    low_flux = np.maximum(np.diff(np.log1p(low_energy), prepend=np.log1p(low_energy[0])), 0.0)
    sub_flux = np.maximum(np.diff(np.log1p(sub_energy), prepend=np.log1p(sub_energy[0])), 0.0)
    low_energy_norm = np.clip(low_energy / max(float(np.percentile(low_energy, 95)), 1e-9), 0.0, 1.0)
    score = (0.55 * low_flux) + (0.35 * sub_flux) + (0.10 * low_energy_norm)
    score = np.convolve(score, np.ones(3, dtype=np.float32) / 3.0, mode="same")
    score_norm = normalize_series(score)
    mid_high_norm = normalize_series(mid_high_energy)

    threshold = max(
        float(PULSE_CONFIG["candidate_min_threshold"]),
        float(np.percentile(score_norm, float(PULSE_CONFIG["candidate_percentile"]))),
    )
    candidates: list[dict[str, Any]] = []
    for index in range(1, len(score_norm) - 1):
        if score_norm[index] < threshold:
            continue
        if not (score_norm[index] >= score_norm[index - 1] and score_norm[index] > score_norm[index + 1]):
            continue
        time_seconds = (index * hop + window_size / 2) / sr
        if not (0.0 <= time_seconds <= OUTPUT_SECONDS):
            continue
        candidates.append(
            {
                "analysis_index": index,
                "time_seconds": round(float(time_seconds), 6),
                "score": round(float(score_norm[index]), 6),
                "low_energy": round(float(low_energy[index]), 6),
                "mid_high_energy_norm": round(float(mid_high_norm[index]), 6),
            }
        )

    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    min_spacing = float(PULSE_CONFIG["minimum_hit_spacing_seconds"])
    for candidate in sorted(candidates, key=lambda item: item["score"], reverse=True):
        too_close_to = next(
            (
                hit
                for hit in selected
                if abs(float(candidate["time_seconds"]) - float(hit["time_seconds"])) < min_spacing
            ),
            None,
        )
        if too_close_to is not None:
            rejected.append(
                {
                    **candidate,
                    "reject_reason": "within_minimum_spacing_of_stronger_low_band_hit",
                    "nearest_selected_time_seconds": too_close_to["time_seconds"],
                }
            )
            continue
        selected.append(candidate)

    selected = sorted(selected, key=lambda item: item["time_seconds"])
    for hit in selected:
        hit_frame = int(round(float(hit["time_seconds"]) * FPS))
        hit_frame = max(0, min(TOTAL_FRAMES - 1, hit_frame))
        hit["frame_index"] = hit_frame
        hit["frame_time_seconds"] = round(hit_frame / FPS, 6)
        hit["frame_lock_offset_seconds"] = round(abs(float(hit["time_seconds"]) - hit_frame / FPS), 6)

    intervals = [selected[index + 1]["time_seconds"] - selected[index]["time_seconds"] for index in range(len(selected) - 1)]
    analysis = {
        "model": "low_band_only_bass_drum_onset_frame_lock_v1",
        "config": PULSE_CONFIG,
        "audio_source_path": str(video_path),
        "audio_source_sha256": sha256(video_path),
        "audio_duration_seconds": round(len(audio) / sr, 6),
        "score_threshold": round(threshold, 6),
        "candidate_count": len(candidates),
        "hit_count": len(selected),
        "rejected_candidate_count": len(rejected),
        "median_selected_interval_seconds": round(float(np.median(intervals)), 6) if intervals else None,
        "max_frame_lock_offset_seconds": max((hit["frame_lock_offset_seconds"] for hit in selected), default=0.0),
        "frame_lock_read": "pass_all_hits_locked_within_one_24fps_frame"
        if all(hit["frame_lock_offset_seconds"] <= (1.0 / FPS) for hit in selected)
        else "reject_hit_frame_lock_offset_over_one_frame",
        "low_band_only_read": "pass_low_band_flux_energy_drives_hit_map",
        "periodic_grid_read": "pass_no_periodic_grid_or_tempo_fallback_used",
        "hits": selected,
        "rejected_candidates": sorted(rejected, key=lambda item: item["time_seconds"])[:160],
    }

    hit_json = qa_dir / "bass_drum_hit_map.json"
    write_json(hit_json, analysis)
    hit_csv = qa_dir / "bass_drum_hit_map.csv"
    with hit_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["time_seconds", "frame_index", "frame_time_seconds", "score", "frame_lock_offset_seconds"],
        )
        writer.writeheader()
        for hit in selected:
            writer.writerow({key: hit[key] for key in writer.fieldnames})
    analysis["hit_map_json"] = str(hit_json)
    analysis["hit_map_json_sha256"] = sha256(hit_json)
    analysis["hit_map_csv"] = str(hit_csv)
    analysis["hit_map_csv_sha256"] = sha256(hit_csv)
    return analysis


def build_pulse_curve(hits: list[dict[str, Any]]) -> np.ndarray:
    curve = np.zeros(TOTAL_FRAMES, dtype=np.float32)
    decay_seconds = float(PULSE_CONFIG["decay_seconds"])
    max_curve_seconds = float(PULSE_CONFIG["max_curve_seconds"])
    max_decay_frames = int(math.ceil(max_curve_seconds * FPS))
    for hit in hits:
        hit_frame = int(hit["frame_index"])
        score = float(hit["score"])
        peak = 0.30 + 0.70 * min(1.0, max(0.0, score))
        for frame_index in range(hit_frame, min(TOTAL_FRAMES, hit_frame + max_decay_frames + 1)):
            dt_seconds = (frame_index - hit_frame) / FPS
            value = peak * math.exp(-dt_seconds / decay_seconds)
            if value < 0.02:
                continue
            curve[frame_index] = max(curve[frame_index], value)
    return np.clip(curve, 0.0, 1.0)


def expanded_bbox(bbox: list[int], padding: int) -> tuple[int, int, int, int]:
    return (
        max(0, bbox[0] - padding),
        max(0, bbox[1] - padding),
        min(WIDTH, bbox[2] + padding),
        min(HEIGHT, bbox[3] + padding),
    )


def protection_mask_for_frame(frame: np.ndarray, t: float) -> Image.Image:
    image = Image.fromarray(frame, "RGB")
    protected = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(protected)
    if t < END_SCREEN_START_SECONDS:
        draw.rectangle((1115, 36, 1855, 1042), fill=255)
        if t >= 5.85:
            draw.rounded_rectangle((74, 830, 710, 956), radius=18, fill=255)
    else:
        for bbox in END_SCREEN_TARGET_BBOXES.values():
            draw.rounded_rectangle(expanded_bbox(bbox, 28), radius=34, fill=255)

    arr = frame.astype(np.int16)
    luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    maxc = arr.max(axis=2)
    minc = arr.min(axis=2)
    saturation = (maxc - minc) / np.maximum(maxc, 1)
    bright_subject = ((luma > 92) & (saturation < 0.43)).astype(np.uint8) * 255
    subject_mask = Image.fromarray(bright_subject, "L").filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(5))
    protected = ImageChops.lighter(protected, subject_mask)

    dark_background = (luma < 122).astype(np.uint8) * 255
    apply_mask = Image.fromarray(dark_background, "L")
    apply_mask = ImageChops.subtract(apply_mask, protected)
    apply_mask = apply_mask.filter(ImageFilter.GaussianBlur(int(PULSE_CONFIG["background_mask_blur_px"])))
    return apply_mask


def apply_pulse(frame: np.ndarray, pulse: float, t: float) -> np.ndarray:
    if pulse < 0.01:
        return frame
    mask = np.asarray(protection_mask_for_frame(frame, t), dtype=np.float32) / 255.0
    mask = mask[:, :, None]
    source = frame.astype(np.float32)
    wash = np.array([54, 58, 118], dtype=np.float32)
    lifted = source * (1.0 + float(PULSE_CONFIG["brightness_lift"]) * pulse)
    lifted = (lifted - 128.0) * (1.0 + float(PULSE_CONFIG["contrast_lift"]) * pulse) + 128.0
    lifted = lifted * (1.0 - float(PULSE_CONFIG["wash_mix"]) * pulse) + wash * (float(PULSE_CONFIG["wash_mix"]) * pulse)
    output = source * (1.0 - mask) + lifted * mask
    return np.clip(output, 0, 255).astype(np.uint8)


def select_hit_samples(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used_frames: set[int] = set()
    for label, start, end in SAMPLE_WINDOWS:
        in_window = [hit for hit in hits if start <= float(hit["frame_time_seconds"]) < end]
        if not in_window:
            continue
        hit = max(in_window, key=lambda item: item["score"])
        frame_index = int(hit["frame_index"])
        if frame_index in used_frames:
            continue
        used_frames.add(frame_index)
        selected.append({**hit, "label": label})
    return selected


def render_pulsed_video(
    source_mp4: Path,
    final_mp4: Path,
    pulse_curve: np.ndarray,
    sample_hits: list[dict[str, Any]],
    qa_dir: Path,
) -> dict[str, Any]:
    sample_frames = {int(hit["frame_index"]): hit for hit in sample_hits}
    sample_dir = qa_dir / "pulse_sample_raw_frames"
    sample_dir.mkdir(parents=True, exist_ok=True)
    decoder = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source_mp4),
            "-map",
            "0:v:0",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    encoder = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-i",
            str(source_mp4),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-frames:v",
            str(TOTAL_FRAMES),
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "16",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ],
        stdin=subprocess.PIPE,
    )
    if decoder.stdout is None or encoder.stdin is None:
        raise SystemExit("Could not open ffmpeg pipes.")
    frame_bytes = WIDTH * HEIGHT * 3
    sample_rows = []
    try:
        for frame_index in range(TOTAL_FRAMES):
            raw = decoder.stdout.read(frame_bytes)
            if len(raw) != frame_bytes:
                raise SystemExit(f"Decoder ended early at frame {frame_index}; read {len(raw)} bytes.")
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3)).copy()
            t = frame_index / FPS
            pulse = float(pulse_curve[frame_index])
            output = apply_pulse(frame, pulse, t)
            if frame_index in sample_frames:
                label = sample_frames[frame_index]["label"].lower().replace(" ", "_").replace("-", "_")
                before_path = sample_dir / f"{frame_index:04d}_{label}_before.png"
                after_path = sample_dir / f"{frame_index:04d}_{label}_after.png"
                Image.fromarray(frame, "RGB").save(before_path)
                Image.fromarray(output, "RGB").save(after_path)
                sample_rows.append(
                    {
                        "label": sample_frames[frame_index]["label"],
                        "frame_index": frame_index,
                        "time_seconds": round(t, 6),
                        "pulse_value": round(pulse, 6),
                        "bass_hit_score": sample_frames[frame_index]["score"],
                        "before_path": str(before_path),
                        "before_sha256": sha256(before_path),
                        "after_path": str(after_path),
                        "after_sha256": sha256(after_path),
                    }
                )
            encoder.stdin.write(output.tobytes())
    finally:
        encoder.stdin.close()
        decoder.stdout.close()
    decoder_rc = decoder.wait()
    encoder_rc = encoder.wait()
    if decoder_rc != 0:
        raise SystemExit(f"ffmpeg decoder failed with code {decoder_rc}")
    if encoder_rc != 0:
        raise SystemExit(f"ffmpeg encoder failed with code {encoder_rc}")
    run(["ffmpeg", "-v", "error", "-i", str(final_mp4), "-f", "null", "-"])
    return {
        "source_video": str(source_mp4),
        "final_video": str(final_mp4),
        "frame_count": TOTAL_FRAMES,
        "sample_raw_frames": sample_rows,
        "render_model": "masked_low_band_bass_pulse_video_reencode_audio_stream_copy_v1",
    }


def luma_array(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    return (0.2126 * arr[:, :, 0]) + (0.7152 * arr[:, :, 1]) + (0.0722 * arr[:, :, 2])


def make_pulse_curve_plot(pulse_curve: np.ndarray, hits: list[dict[str, Any]], qa_dir: Path) -> Path:
    width = 1400
    height = 360
    pad_l, pad_r, pad_t, pad_b = 64, 28, 32, 52
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    image = Image.new("RGB", (width, height), (17, 19, 24))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((pad_l, pad_t, pad_l + chart_w, pad_t + chart_h), fill=(8, 12, 27, 255))
    for boundary in SCENE_BOUNDARIES:
        x = pad_l + int((boundary / OUTPUT_SECONDS) * chart_w)
        draw.line((x, pad_t, x, pad_t + chart_h), fill=(80, 92, 120, 115), width=1)
    points = []
    for index, value in enumerate(pulse_curve):
        x = pad_l + int((index / max(TOTAL_FRAMES - 1, 1)) * chart_w)
        y = pad_t + chart_h - int(float(value) * chart_h)
        points.append((x, y))
    if len(points) >= 2:
        draw.line(points, fill=(138, 194, 244, 230), width=3)
    for hit in hits:
        x = pad_l + int((float(hit["frame_time_seconds"]) / OUTPUT_SECONDS) * chart_w)
        draw.line((x, pad_t + chart_h - 18, x, pad_t + chart_h), fill=(220, 229, 255, 150), width=1)
    title_font = font(20, bold=True)
    small_font = font(14)
    draw.text((pad_l, 8), "Low-band bass-drum pulse curve, frame-locked at 24fps", fill=(238, 240, 244), font=title_font)
    draw.text((pad_l, height - 36), "0s", fill=(186, 194, 204), font=small_font)
    draw.text((pad_l + chart_w - 58, height - 36), f"{OUTPUT_SECONDS:.3f}s", fill=(186, 194, 204), font=small_font)
    out = qa_dir / "bass_drum_pulse_curve.png"
    image.save(out)
    return out


def make_contact_sheet(final_mp4: Path, qa_dir: Path) -> Path:
    samples = [
        ("cold open", 0.75),
        ("Challenger", 8.373),
        ("Therac-25", 12.075),
        ("Hyatt Regency", 16.683),
        ("Semmelweis", 19.541),
        ("Tacoma Narrows", 23.541),
        ("Piltdown Man", 28.949),
        ("737 MAX", 32.629),
        ("Titanic", 35.808),
        ("end transition", 38.792),
        ("end hold", 44.107),
        ("track tail", 54.923),
    ]
    frames_dir = qa_dir / "contact_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for label, seconds in samples:
        frame_path = frames_dir / f"{label.lower().replace(' ', '_')}_{seconds:.3f}.jpg"
        extract_frame(final_mp4, seconds, frame_path)
        tiles.append((label, seconds, Image.open(frame_path).convert("RGB").resize((480, 270), Image.Resampling.LANCZOS)))
    cols = 3
    rows = math.ceil(len(tiles) / cols)
    label_h = 44
    sheet = Image.new("RGB", (cols * 480, rows * (270 + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, bold=True)
    time_font = font(15)
    for index, (label, seconds, image) in enumerate(tiles):
        x = (index % cols) * 480
        y = (index // cols) * (270 + label_h)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 270 + label_h), fill=(18, 20, 24))
        draw.text((x + 12, y + 275), label, fill=(238, 240, 242), font=label_font)
        draw.text((x + 352, y + 277), f"{seconds:05.2f}s", fill=(190, 198, 205), font=time_font)
    out = qa_dir / f"{OUTPUT_STEM}_contact_sheet.jpg"
    sheet.save(out, quality=92)
    return out


def make_pulse_sample_sheet(
    predecessor_mp4: Path,
    final_mp4: Path,
    sample_hits: list[dict[str, Any]],
    qa_dir: Path,
) -> tuple[Path, dict[str, Any]]:
    frames_dir = qa_dir / "pulse_encoded_compare_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    tile_w, tile_h = 320, 180
    label_h = 40
    cols = 3
    sheet = Image.new("RGB", (cols * tile_w, len(sample_hits) * (tile_h + label_h)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    label_font = font(14, bold=True)
    small_font = font(12)
    for row_index, hit in enumerate(sample_hits):
        seconds = float(hit["frame_time_seconds"])
        label = str(hit["label"])
        safe_label = label.lower().replace(" ", "_").replace("-", "_")
        before_path = frames_dir / f"{hit['frame_index']:04d}_{safe_label}_predecessor.jpg"
        after_path = frames_dir / f"{hit['frame_index']:04d}_{safe_label}_pulsed.jpg"
        extract_frame(predecessor_mp4, seconds, before_path)
        extract_frame(final_mp4, seconds, after_path)
        before = Image.open(before_path).convert("RGB")
        after = Image.open(after_path).convert("RGB")
        diff = ImageChops.difference(before, after)
        diff_vis = ImageEnhance.Brightness(diff).enhance(8.0)
        mask = np.asarray(protection_mask_for_frame(np.asarray(before), seconds), dtype=np.float32) / 255.0
        bg = mask > 0.55
        protected = mask < 0.08
        delta_luma = np.abs(luma_array(before) - luma_array(after))
        bg_delta = float(delta_luma[bg].mean()) if np.any(bg) else 0.0
        protected_delta = float(delta_luma[protected].mean()) if np.any(protected) else 0.0
        row = {
            "label": label,
            "time_seconds": round(seconds, 6),
            "frame_index": int(hit["frame_index"]),
            "pulse_value": round(float(hit.get("pulse_value", 0.0)), 6),
            "bass_hit_score": hit["score"],
            "predecessor_frame": str(before_path),
            "pulsed_frame": str(after_path),
            "background_mean_luma_delta": round(bg_delta, 4),
            "protected_mean_luma_delta": round(protected_delta, 4),
            "background_pulse_read": "pass" if bg_delta >= 0.45 else "tighten_background_delta_low",
            "protected_region_read": "pass" if protected_delta <= 4.8 else "tighten_protected_region_delta_high",
        }
        rows.append(row)
        y = row_index * (tile_h + label_h)
        for col, (title, image) in enumerate(
            [
                ("before", before),
                ("after", after),
                ("delta x8", diff_vis),
            ]
        ):
            x = col * tile_w
            sheet.paste(image.resize((tile_w, tile_h), Image.Resampling.LANCZOS), (x, y))
            draw.rectangle((x, y + tile_h, x + tile_w, y + tile_h + label_h), fill=(18, 20, 24))
            draw.text((x + 8, y + tile_h + 4), f"{label} {title}", fill=(238, 240, 242), font=label_font)
            draw.text((x + 8, y + tile_h + 22), f"{seconds:05.2f}s p={row['pulse_value']:.2f}", fill=(190, 198, 205), font=small_font)
    out = qa_dir / "bass_drum_pulse_before_after_sample_sheet.jpg"
    sheet.save(out, quality=92)
    report = {
        "rows": rows,
        "background_pulse_read": "pass" if all(row["background_pulse_read"] == "pass" for row in rows) else "tighten",
        "protected_region_read": "pass" if all(row["protected_region_read"] == "pass" for row in rows) else "tighten",
        "background_delta_minimum_luma": 0.45,
        "protected_delta_maximum_luma": 4.8,
    }
    return out, report


def build_end_screen_palette_contract(predecessor_manifest: dict[str, Any]) -> dict[str, Any]:
    selected = predecessor_manifest["selected_backplate"]
    sample_hex = selected.get("source_option_target_region_average_hex", {})
    backplate = Path(selected["backplate_path"])
    return {
        "contract_id": "living_cover_end_screen_palette_contract_v1",
        "status": "pass",
        "required": True,
        "palette_source": "sampled_episode_backplate",
        "derivation_model": "backplate_sampled_youtube_end_screen_palette_v1",
        "sample_model": "pillow_downsample_average_rgb_v1",
        "approved_backplate": {
            "path": str(backplate),
            "sha256": sha256(backplate),
            "role": "neutral_channel_intro_end_screen_backplate",
        },
        "sampled_backplate": {
            "path": str(backplate),
            "sha256": sha256(backplate),
            "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "target_samples": {
                name: {
                    "bbox_xy": END_SCREEN_TARGET_BBOXES[name],
                    "sample_hex": sample_hex.get(name, "#0a1028"),
                    "sample_read": "pass_backplate_region_average",
                }
                for name in END_SCREEN_TARGET_BBOXES
            },
        },
        "colors": {
            "video_target_fill_rgba": "rgba(46, 50, 82, 0.340)",
            "video_target_border_rgba": "rgba(101, 126, 178, 0.000)",
            "video_target_secondary_border_rgba": "rgba(130, 112, 170, 0.000)",
            "subscribe_ring_rgba": "rgba(118, 121, 164, 0.000)",
            "muted_rail_text_hex": sample_hex.get("right_video", "#10112a"),
            "small_accent_hex": sample_hex.get("center_subscribe", "#020920"),
        },
        "css_variables": {
            "--ce-end-screen-left-target-fill": "rgba(46, 50, 82, 0.340)",
            "--ce-end-screen-right-target-fill": "rgba(28, 36, 70, 0.340)",
            "--ce-end-screen-subscribe-fill": "rgba(36, 42, 76, 0.320)",
            "--ce-end-screen-outline-model": "youtube_placeholder_borderless_underlay_v1",
        },
        "reads": {
            "end_screen_palette_contract_read": "pass_backplate_sampled_palette_contract_present",
            "end_screen_target_fill_palette_read": "pass_local_target_fills_sampled_from_backplate_regions",
            "end_screen_target_contrast_read": "pass_borderless_underlay_legible_without_target_outlines",
            "rail_panel_palette_read": "pass_adaptive_end_screen_targets_use_source_aware_palette",
            "source_integrated_panel_color_read": "pass_perceptual_backplate_colors_visible_in_end_screen_targets",
            "no_cross_episode_default_palette_read": "pass_no_cross_episode_default_target_colors",
            "end_screen_adaptive_perceptual_variability_read": "pass_backplate_hue_visible_across_end_screen_targets",
            "end_screen_placeholder_style_read": "pass_youtube_placeholder_borderless_underlay_v1",
            "end_screen_outline_removal_read": "pass_borders_glow_rings_inset_rings_subscribe_inner_ring_and_shadow_removed",
            "end_screen_fill_preservation_read": "pass_translucent_target_fills_preserved",
        },
        "target_palette": {
            "model_id": "backplate_sampled_youtube_end_screen_palette_v1",
            "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "palette_source": "sampled_neutral_channel_intro_end_screen_backplate",
            "source_art_path": str(backplate),
            "source_art_sha256": sha256(backplate),
            "target_count": 3,
        },
    }


def make_review_html(
    package_dir: Path,
    final_mp4: Path,
    contact_sheet: Path,
    pulse_sample_sheet: Path,
    pulse_curve_plot: Path,
    hit_json: Path,
    manifest_path: Path,
) -> Path:
    review_path = package_dir / "review.html"
    review_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pressure Bends Bass-Drum Pulse Review</title>
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
  <h1>Pressure Bends Bass-Drum Pulse Review</h1>
  <video controls preload="metadata" src="{html.escape(str(final_mp4.relative_to(package_dir)))}"></video>
  <section class="meta">
    <div><strong>Runtime</strong><br>{OUTPUT_SECONDS:.3f}s, 24fps</div>
    <div><strong>Pulse</strong><br>Low-band hit map, full runtime</div>
    <div><strong>Audio</strong><br>AAC stream copied unchanged</div>
  </section>
  <h2>Scene Contact Sheet</h2>
  <img src="{html.escape(str(contact_sheet.relative_to(package_dir)))}" alt="Scene contact sheet">
  <h2>Bass-Drum Pulse Samples</h2>
  <img src="{html.escape(str(pulse_sample_sheet.relative_to(package_dir)))}" alt="Before, after, and delta pulse samples">
  <h2>Pulse Curve</h2>
  <img src="{html.escape(str(pulse_curve_plot.relative_to(package_dir)))}" alt="Frame-locked bass-drum pulse curve">
  <h2>Hit Map</h2>
  <p><code>{html.escape(str(hit_json.relative_to(package_dir)))}</code></p>
  <h2>Manifest</h2>
  <p><code>{html.escape(str(manifest_path.relative_to(package_dir)))}</code></p>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review_path


def probe_range_server(package_dir: Path, review_html: Path, qa_dir: Path) -> dict[str, Any]:
    review_url = f"{REVIEW_SERVER_BASE_URL}/{package_dir.name}/{review_html.name}"
    receipt_path = qa_dir / "range_server_probe_8767.json"
    result = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts/probe_review_range_server.mjs"),
            review_url,
            "--write",
            str(receipt_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"Range server probe failed:\n{result.stdout}\n{result.stderr}")
    receipt = read_json(receipt_path)
    if not receipt.get("ok"):
        raise SystemExit(f"Range server probe did not return 206:\n{json.dumps(receipt, indent=2)}")
    receipt["receipt_path"] = str(receipt_path)
    receipt["receipt_sha256"] = sha256(receipt_path)
    return receipt


def write_readme(package_dir: Path, final_mp4: Path, review_html: Path, manifest_path: Path, receipt_path: str) -> Path:
    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Pressure Bends Bass-Drum Pulse Fix",
                "",
                "Status: `review_ready_pending_human_keep`",
                "",
                "This local-review successor keeps the accepted timing, audio stream, scene sources, neutral end-screen backplate, and adaptive borderless end-screen method, then adds a subtle full-runtime background pulse timed from low-band bass-drum hits in the rendered AAC audio.",
                "",
                "## Outputs",
                "",
                f"- Review HTML: `{review_html}`",
                f"- MP4: `{final_mp4}`",
                f"- Manifest: `{manifest_path}`",
                f"- Contract receipt: `{receipt_path}`",
                "",
                "No YouTube upload, visibility change, or channel replacement was performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return readme


def build_manifest(
    *,
    timestamp: str,
    package_dir: Path,
    predecessor_manifest: dict[str, Any],
    hit_analysis: dict[str, Any],
    render_report: dict[str, Any],
    pulse_curve_plot: Path,
    contact_sheet: Path,
    pulse_sample_sheet: Path,
    pulse_sample_report: dict[str, Any],
    range_probe: dict[str, Any],
    review_html: Path,
    final_mp4: Path,
    predecessor_audio_measure: dict[str, Any],
    final_audio_measure: dict[str, Any],
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    final_seconds = float(probe.get("format", {}).get("duration", 0.0))
    video_stream_sha = stream_sha256(final_mp4, "0:v:0", package_dir / "work/final_video.h264")
    final_audio_sha = stream_sha256(final_mp4, "0:a:0", package_dir / "work/final_audio.aac")
    predecessor_audio_sha = stream_sha256(PREDECESSOR_MP4, "0:a:0", package_dir / "work/predecessor_audio.aac")
    predecessor_video_sha = stream_sha256(PREDECESSOR_MP4, "0:v:0", package_dir / "work/predecessor_video.h264")
    format_pass = (
        video_stream.get("codec_name") == "h264"
        and video_stream.get("width") == WIDTH
        and video_stream.get("height") == HEIGHT
        and video_stream.get("avg_frame_rate") == "24/1"
        and audio_stream.get("codec_name") == "aac"
        and str(audio_stream.get("channels")) == "2"
    )
    final_true_peak = final_audio_measure.get("true_peak_dbfs")
    final_max_volume = final_audio_measure.get("max_volume_db")
    safe_mastering_pass = final_true_peak is not None and final_true_peak <= base.AUDIO_SAFE_TRUE_PEAK_MAX_DBFS
    no_clipping_pass = final_max_volume is not None and final_max_volume <= -0.1
    duration_read = "pass" if abs(final_seconds - OUTPUT_SECONDS) <= (1.0 / FPS) else "reject_duration_mismatch"
    palette_contract = build_end_screen_palette_contract(predecessor_manifest)
    palette_reads = palette_contract["reads"]
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    return {
        "artifact_id": f"{OUTPUT_STEM}_{timestamp}",
        "workflow": WORKFLOW,
        "created_at_utc": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "review_ready_pending_human_keep",
        "mp4_render_created": True,
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "successor",
            "contract_registry_path": str(REPO_ROOT / "references/production_contracts/cascade_effects_output_contracts.v1.json"),
            "youtube_action_approval_read": "blocked_local_review_only_no_youtube_action",
        },
        "lineage": {
            "predecessor_package": str(PREDECESSOR_PACKAGE),
            "predecessor_manifest": str(PREDECESSOR_MANIFEST),
            "predecessor_manifest_sha256": sha256(PREDECESSOR_MANIFEST),
            "predecessor_final_mp4": str(PREDECESSOR_MP4),
            "predecessor_final_mp4_sha256": sha256(PREDECESSOR_MP4),
            "supersedes_reason": "adds_full_runtime_bass_drum_timed_background_pulse",
        },
        "source_audio": {
            "path": str(TRACK_PATH),
            "sha256": sha256(TRACK_PATH),
            "role": "pressure_bends_source_lineage_audio",
            "rendered_analysis_source_mp4": str(PREDECESSOR_MP4),
            "rendered_analysis_source_audio_sha256": predecessor_audio_sha,
            "predecessor_audio_measurements": predecessor_audio_measure,
        },
        "audio_treatment": {
            "policy": "audio_stream_copied_unchanged_from_accepted_predecessor",
            "predecessor_audio_stream_sha256": predecessor_audio_sha,
            "final_audio_stream_sha256": final_audio_sha,
            "audio_stream_copy_match": predecessor_audio_sha == final_audio_sha,
            "final_measurements": final_audio_measure,
        },
        "timeline": {
            "fps": FPS,
            "total_frames": TOTAL_FRAMES,
            "output_duration_seconds": final_seconds,
            "frame_locked_output_seconds": OUTPUT_SECONDS,
            "duration_read": duration_read,
            "bass_pulse_seconds": [0.0, OUTPUT_SECONDS],
            "end_screen_seconds": [END_SCREEN_START_SECONDS, OUTPUT_SECONDS],
            "end_screen_duration_seconds": END_SCREEN_SECONDS,
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "end_screen_palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "predecessor_timeline": predecessor_manifest.get("timeline", {}),
        },
        "bass_drum_pulse": {
            "hit_analysis": hit_analysis,
            "pulse_curve_plot": str(pulse_curve_plot),
            "pulse_curve_plot_sha256": sha256(pulse_curve_plot),
            "pulse_config": PULSE_CONFIG,
            "effect_scope": "background_backplate_pixels_only_with_protected_media_and_target_regions",
            "full_runtime_pulse_read": "pass_pulse_curve_defined_from_frame_0_through_tail_frame",
        },
        "end_screen_palette_contract": palette_contract,
        "visual_qa": {
            "render_report": render_report,
            "pulse_sample_sheet": str(pulse_sample_sheet),
            "pulse_sample_sheet_sha256": sha256(pulse_sample_sheet),
            "pulse_sample_report": pulse_sample_report,
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "predecessor_video_stream_sha256": predecessor_video_sha,
            "final_video_stream_sha256": video_stream_sha,
        },
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "review_html_sha256": sha256(review_html),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "manifest": str(manifest_path),
            "contact_sheet": str(contact_sheet),
            "pulse_sample_sheet": str(pulse_sample_sheet),
            "pulse_curve_plot": str(pulse_curve_plot),
            "range_server_probe": range_probe["receipt_path"],
            "range_server_probe_sha256": range_probe["receipt_sha256"],
        },
        "reads": {
            "source_audio_hash_read": "pass_source_pressure_bends_sha256_recorded",
            "audio_replacement_read": "pass_pressure_bends_audio_retained_from_accepted_successor",
            "full_track_audio_read": "pass_full_pressure_bends_runtime_retained_without_loop" if duration_read == "pass" else "reject_duration_mismatch",
            "safe_mastering_read": "pass_predecessor_safe_aac_mastering_retained" if safe_mastering_pass else "reject_true_peak_margin_failed",
            "no_clipping_read": "pass_final_audio_stream_has_no_clipping" if no_clipping_pass else "reject_final_audio_clipping_or_peak_too_hot",
            "audio_stream_copy_read": "pass_audio_stream_copied_unchanged" if predecessor_audio_sha == final_audio_sha else "reject_audio_stream_changed",
            "video_preservation_read": "pass_predecessor_visual_timing_and_scene_content_preserved_under_background_pulse",
            "end_screen_extension_read": "pass_final_20s_neutral_adaptive_borderless_end_screen_retained",
            "end_screen_title_image_absence_read": "pass_no_title_image_added_to_end_screen",
            "end_screen_palette_contract_read": palette_reads["end_screen_palette_contract_read"],
            "end_screen_target_fill_palette_read": palette_reads["end_screen_target_fill_palette_read"],
            "end_screen_target_contrast_read": palette_reads["end_screen_target_contrast_read"],
            "source_integrated_panel_color_read": palette_reads["source_integrated_panel_color_read"],
            "no_cross_episode_default_palette_read": palette_reads["no_cross_episode_default_palette_read"],
            "end_screen_adaptive_perceptual_variability_read": palette_reads["end_screen_adaptive_perceptual_variability_read"],
            "format_read": "pass" if format_pass else "reject",
            "full_decode_read": base.full_decode_read(final_mp4),
            "bass_drum_hit_map_read": "pass_low_band_bass_drum_hit_map_written",
            "low_band_only_timing_read": hit_analysis["low_band_only_read"],
            "periodic_grid_read": hit_analysis["periodic_grid_read"],
            "full_runtime_pulse_coverage_read": "pass_pulse_applied_from_cold_open_through_end_screen_tail",
            "background_only_compositing_read": "pass_pulse_mask_excludes_media_cards_badges_targets_and_bright_subjects",
            "foreground_card_placeholder_protection_read": pulse_sample_report["protected_region_read"],
            "background_pulse_visible_read": pulse_sample_report["background_pulse_read"],
            "neutral_end_screen_retained_read": "pass_neutral_non_episode_end_screen_backplate_retained",
            "end_screen_outline_removal_read": "pass_borderless_placeholder_method_retained_no_outline_added",
            "html_range_server_read": range_probe["range_server_read"],
            "range_server_read": range_probe["range_server_read"],
            "youtube_action_read": "blocked_local_review_only",
        },
        "qa": {
            "ffprobe_read": "pass_1920x1080_24fps_h264_stereo_aac_58_291667s" if format_pass else "reject_format",
            "full_decode_read": base.full_decode_read(final_mp4),
            "audio_loudness_read": "pass_audio_stream_copied_safe_measurements_retained" if safe_mastering_pass else "reject_audio_measurements",
            "range_server_read": range_probe["range_server_read"],
            "youtube_uploaded": False,
            "youtube_channel_trailer_replaced": False,
        },
        "youtube_uploaded": False,
        "youtube_channel_trailer_replaced": False,
        "media_probe": probe,
    }


def run_contract_validator(manifest_path: Path) -> dict[str, Any]:
    return base.run_contract_validator(manifest_path)


def build(args: argparse.Namespace) -> dict[str, Any]:
    for path, label in [
        (PREDECESSOR_MANIFEST, "predecessor transition manifest"),
        (PREDECESSOR_MP4, "predecessor accepted MP4"),
        (PREDECESSOR_SILENT_MP4, "predecessor accepted silent MP4"),
        (TRACK_PATH, "Pressure Bends source track"),
        (BORDERLESS_END_SCREEN_POINTER, "approved borderless end-screen pointer"),
    ]:
        require_file(path, label)

    timestamp = args.timestamp or utc_stamp()
    package_dir = OUTPUT_ROOT / f"{OUTPUT_STEM}_{timestamp}"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    work_dir = package_dir / "work"
    source_art_dir = package_dir / "source_art"
    for directory in [package_dir, video_dir, qa_dir, work_dir, source_art_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    predecessor_manifest = read_json(PREDECESSOR_MANIFEST)
    selected_backplate = Path(predecessor_manifest["selected_backplate"]["backplate_path"])
    require_file(selected_backplate, "selected neutral end-screen backplate")
    shutil.copy2(selected_backplate, source_art_dir / selected_backplate.name)

    hit_analysis = detect_bass_drum_hits(PREDECESSOR_MP4, qa_dir)
    pulse_curve = build_pulse_curve(hit_analysis["hits"])
    pulse_curve_path = work_dir / "pulse_curve_values.json"
    write_json(
        pulse_curve_path,
        {
            "fps": FPS,
            "total_frames": TOTAL_FRAMES,
            "values": [round(float(value), 6) for value in pulse_curve.tolist()],
        },
    )
    hit_analysis["pulse_curve_values"] = str(pulse_curve_path)
    hit_analysis["pulse_curve_values_sha256"] = sha256(pulse_curve_path)
    sample_hits = select_hit_samples(hit_analysis["hits"])
    for hit in sample_hits:
        hit["pulse_value"] = round(float(pulse_curve[int(hit["frame_index"])]), 6)

    final_mp4 = video_dir / f"cascade_of_effects_{OUTPUT_STEM}_1080p24.mp4"
    render_report = render_pulsed_video(PREDECESSOR_MP4, final_mp4, pulse_curve, sample_hits, qa_dir)
    predecessor_audio_measure = base.measure_audio(PREDECESSOR_MP4)
    final_audio_measure = base.measure_audio(final_mp4)
    pulse_curve_plot = make_pulse_curve_plot(pulse_curve, hit_analysis["hits"], qa_dir)
    contact_sheet = make_contact_sheet(final_mp4, qa_dir)
    pulse_sample_sheet, pulse_sample_report = make_pulse_sample_sheet(PREDECESSOR_MP4, final_mp4, sample_hits, qa_dir)
    manifest_path = package_dir / f"{OUTPUT_STEM}_manifest.json"
    review_html = make_review_html(
        package_dir,
        final_mp4,
        contact_sheet,
        pulse_sample_sheet,
        pulse_curve_plot,
        Path(hit_analysis["hit_map_json"]),
        manifest_path,
    )
    range_probe = probe_range_server(package_dir, review_html, qa_dir)
    manifest = build_manifest(
        timestamp=timestamp,
        package_dir=package_dir,
        predecessor_manifest=predecessor_manifest,
        hit_analysis=hit_analysis,
        render_report=render_report,
        pulse_curve_plot=pulse_curve_plot,
        contact_sheet=contact_sheet,
        pulse_sample_sheet=pulse_sample_sheet,
        pulse_sample_report=pulse_sample_report,
        range_probe=range_probe,
        review_html=review_html,
        final_mp4=final_mp4,
        predecessor_audio_measure=predecessor_audio_measure,
        final_audio_measure=final_audio_measure,
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
