#!/usr/bin/env python3
"""Build Challenger motion_video_proof/pass_05 with varied ascent interruptions.

Pass05 supersedes Pass04 because the approved horizontal signal interruption
read as the same event at every cut. This pass keeps Proof03 as the clean
historical-signal source, preserves shot order/timing/audio, and varies the
visual-only interruption pattern per ascent/failure cut.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance


PASS10_SCRIPT = Path("/Users/mike/Agents_CascadeEffects/scripts/build_challenger_pass10_editorial_rebuild.py")
spec = importlib.util.spec_from_file_location("pass10_utils", PASS10_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to import {PASS10_SCRIPT}")
p10 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p10
spec.loader.exec_module(p10)

SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/"
    "challenger_short_scoped_v1"
)
PROOF03_ROOT = SHORT_ROOT / "motion_video_proof/pass_03"
PROOF03_MANIFEST = PROOF03_ROOT / "manifest.json"
PROOF04_MANIFEST = SHORT_ROOT / "motion_video_proof/pass_04/manifest.json"
PROOF05_ROOT = SHORT_ROOT / "motion_video_proof/pass_05"
APPROVED_AUDIO = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/"
    "challenger_short_restart_v1/final/challenger_short_restart_v1.wav"
)

FRAME_W = 576
FRAME_H = 1024
FPS = 24
PROFILE_ID = "era_1980s_horizontal_signal_interruption_v2_randomized"
PROFILE_SOURCE = "era_1980s_horizontal_signal_interruption_v1"
SIGNAL_DURATION_SECONDS = 0.25
SIGNAL_STRENGTH = "medium_varied"
SIGNAL_SCOPE = "shuttle_ascent_failure_only"
CUT_SCOPE_START_SECONDS = 27.000
CUT_SCOPE_END_SECONDS = 56.300
CUT_SCOPE_EPSILON = 0.025


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_log(path: Path, cmd: list[str], proc: Any | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "COMMAND:\n" + " ".join(cmd) + "\n\n"
    if proc is not None:
        text += f"STDOUT:\n{proc.stdout or ''}\nSTDERR:\n{proc.stderr or ''}\n"
    path.write_text(text, encoding="utf-8")


def probe(path: Path) -> dict[str, Any]:
    data = p10.ffprobe_json(path)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration_seconds": round(float(data["format"]["duration"]), 3),
        "audio_stream_count": sum(1 for s in data["streams"] if s["codec_type"] == "audio"),
    }


def extract_frame(video: Path, out: Path, t: float) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    for attempt in [t, t - 0.05, t - 0.10, t - 0.20]:
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{max(0.0, attempt):.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(out),
        ]
        p10.run(cmd)
        if out.exists():
            return
    raise FileNotFoundError(out)


def selected_for_interruption(item: dict[str, Any]) -> bool:
    cut_time = float(item["timeline_out_seconds"])
    return (
        CUT_SCOPE_START_SECONDS - CUT_SCOPE_EPSILON
        <= cut_time
        <= CUT_SCOPE_END_SECONDS + CUT_SCOPE_EPSILON
    )


def render_plain_segment(src: Path, out: Path, log: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-vf",
        f"fps={FPS},scale={FRAME_W}:{FRAME_H}:flags=lanczos,setsar=1,format=yuv420p",
        "-an",
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
        "-movflags",
        "+faststart",
        str(out),
    ]
    proc = p10.run(cmd, capture=True)
    write_log(log, cmd, proc)


def variant_config(seed: int, order: int) -> dict[str, Any]:
    rng = random.Random(seed + order * 104729)
    variants = [
        {
            "variant_id": "thin_tracking_tears",
            "emphasis": "full",
            "band_count": rng.randint(4, 7),
            "band_heights": [2, 3, 4, 5, 6],
            "dx_range": (10, 34),
            "snow_strength": rng.uniform(0.12, 0.20),
            "line_alpha": rng.randint(44, 78),
            "chroma_shift": rng.randint(1, 3),
            "dropout_count": rng.randint(0, 1),
        },
        {
            "variant_id": "bottom_tracking_roll",
            "emphasis": "lower",
            "band_count": rng.randint(3, 5),
            "band_heights": [4, 6, 8, 12, 18],
            "dx_range": (18, 46),
            "snow_strength": rng.uniform(0.08, 0.16),
            "line_alpha": rng.randint(36, 68),
            "chroma_shift": rng.randint(2, 4),
            "dropout_count": rng.randint(1, 2),
        },
        {
            "variant_id": "top_sync_flutter",
            "emphasis": "upper",
            "band_count": rng.randint(5, 8),
            "band_heights": [2, 3, 4, 6, 8],
            "dx_range": (8, 28),
            "snow_strength": rng.uniform(0.10, 0.18),
            "line_alpha": rng.randint(50, 86),
            "chroma_shift": rng.randint(1, 2),
            "dropout_count": rng.randint(0, 1),
        },
        {
            "variant_id": "chroma_skew_dropout",
            "emphasis": "middle",
            "band_count": rng.randint(2, 4),
            "band_heights": [8, 12, 16, 22],
            "dx_range": (22, 58),
            "snow_strength": rng.uniform(0.06, 0.14),
            "line_alpha": rng.randint(28, 58),
            "chroma_shift": rng.randint(3, 5),
            "dropout_count": rng.randint(1, 2),
        },
        {
            "variant_id": "sparse_luma_snap",
            "emphasis": "full",
            "band_count": rng.randint(2, 4),
            "band_heights": [2, 3, 4, 10],
            "dx_range": (6, 22),
            "snow_strength": rng.uniform(0.16, 0.25),
            "line_alpha": rng.randint(70, 106),
            "chroma_shift": rng.randint(1, 3),
            "dropout_count": rng.randint(0, 1),
        },
    ]
    config = variants[(order - 8) % len(variants)]
    config["seed"] = seed + order * 104729
    return config


def pick_y(rng: random.Random, h: int, emphasis: str) -> int:
    if emphasis == "upper":
        return rng.randrange(20, max(21, int(h * 0.35)))
    if emphasis == "middle":
        return rng.randrange(int(h * 0.25), int(h * 0.72))
    if emphasis == "lower":
        return rng.randrange(int(h * 0.55), h - 24)
    return rng.randrange(8, h - 24)


def apply_signal_frame(im: Image.Image, config: dict[str, Any], frame_index: int, total_frames: int) -> Image.Image:
    rng = random.Random(config["seed"] + frame_index * 7919)
    progress = (frame_index + 1) / max(1, total_frames)
    out = im.convert("RGB")
    w, h = out.size

    # Vary the attack curve by variant so the same six-frame window does not
    # repeat the same shape at every cut.
    attack = progress ** rng.choice([0.75, 0.9, 1.1, 1.35])
    r, g, b = out.split()
    chroma_shift = int(round(config["chroma_shift"] * attack))
    if config["variant_id"] == "chroma_skew_dropout":
        chroma_shift += frame_index % 2
    r = ImageChops.offset(r, chroma_shift, 0)
    b = ImageChops.offset(b, -chroma_shift, 0)
    out = Image.merge("RGB", (r, g, b))
    out = ImageEnhance.Contrast(out).enhance(1.02 + 0.08 * attack)
    out = ImageEnhance.Brightness(out).enhance(1.0 + 0.035 * attack)

    draw = ImageDraw.Draw(out, "RGBA")
    band_count = max(1, int(round(config["band_count"] * (0.65 + 0.55 * attack))))
    for _ in range(band_count):
        y = pick_y(rng, h, config["emphasis"])
        band_h = rng.choice(config["band_heights"])
        dx_mag = rng.randrange(config["dx_range"][0], config["dx_range"][1] + 1)
        dx = dx_mag if rng.random() > 0.5 else -dx_mag
        band = out.crop((0, y, w, min(h, y + band_h)))
        band = ImageChops.offset(band, dx, 0)
        out.paste(band, (0, y))
        alpha = int(config["line_alpha"] * attack * rng.uniform(0.55, 1.10))
        color = (245, 245, 245, alpha) if rng.random() > 0.42 else (2, 2, 2, alpha)
        draw.rectangle((0, y, w, min(h, y + max(2, band_h // 2))), fill=color)

    for _ in range(config["dropout_count"]):
        if rng.random() < 0.55 + 0.30 * attack:
            y = pick_y(rng, h, config["emphasis"])
            dropout_h = rng.choice([3, 4, 5, 7])
            draw.rectangle((0, y, w, min(h, y + dropout_h)), fill=(255, 255, 255, int(82 * attack)))
            draw.rectangle((0, min(h - 1, y + dropout_h + 2), w, min(h - 1, y + dropout_h + 5)), fill=(0, 0, 0, int(48 * attack)))

    noise = Image.effect_noise((w, h), 48 + 34 * attack).convert("L")
    snow_strength = config["snow_strength"]
    alpha = Image.eval(noise, lambda px: max(0, min(52, int((px - 122) * snow_strength * attack))))
    snow = Image.new("RGB", (w, h), (236, 236, 232))
    out = Image.composite(snow, out, alpha)
    return out


def render_signal_segment(src: Path, out: Path, work_dir: Path, log: Path, config: dict[str, Any]) -> dict[str, Any]:
    if work_dir.exists():
        shutil.rmtree(work_dir)
    frames_dir = work_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = frames_dir / "%06d.png"
    extract_cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-vf",
        f"fps={FPS},scale={FRAME_W}:{FRAME_H}:flags=lanczos,setsar=1",
        "-start_number",
        "0",
        str(pattern),
    ]
    proc_extract = p10.run(extract_cmd, capture=True)
    frame_paths = sorted(frames_dir.glob("*.png"))
    if not frame_paths:
        raise RuntimeError(f"No frames extracted from {src}")

    glitch_frames = max(1, round(SIGNAL_DURATION_SECONDS * FPS))
    start_index = max(0, len(frame_paths) - glitch_frames)
    for local_idx, frame_path in enumerate(frame_paths[start_index:]):
        with Image.open(frame_path) as im:
            apply_signal_frame(im, config, local_idx, len(frame_paths[start_index:])).save(frame_path)

    encode_cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        str(FPS),
        "-i",
        str(pattern),
        "-an",
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
        "-movflags",
        "+faststart",
        str(out),
    ]
    proc_encode = p10.run(encode_cmd, capture=True)
    write_log(log, extract_cmd + ["&&"] + encode_cmd, proc_encode)
    return {
        "frame_count": len(frame_paths),
        "glitch_frame_count": len(frame_paths[start_index:]),
        "interruption_start_frame": start_index,
        "interruption_start_seconds": round(start_index / FPS, 3),
        "interruption_duration_seconds": round(len(frame_paths[start_index:]) / FPS, 3),
        "variant_config": config,
        "extract_stderr": proc_extract.stderr or "",
        "encode_stderr": proc_encode.stderr or "",
    }


def concat(paths: list[Path], out: Path, log: Path) -> Path:
    concat_path = out.with_suffix(".ffconcat")
    with concat_path.open("w", encoding="utf-8") as fh:
        fh.write("ffconcat version 1.0\n")
        for path in paths:
            fh.write(f"file '{path}'\n")
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-an",
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
        "-movflags",
        "+faststart",
        str(out),
    ]
    proc = p10.run(cmd, capture=True)
    write_log(log, cmd, proc)
    return concat_path


def mux_audio(video: Path, audio: Path, out: Path, log: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-i",
        str(audio),
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
        "-shortest",
        "-movflags",
        "+faststart",
        str(out),
    ]
    proc = p10.run(cmd, capture=True)
    write_log(log, cmd, proc)


def youtube_proxy(src: Path, out: Path, log: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-b:v",
        "5M",
        "-maxrate",
        "5M",
        "-bufsize",
        "10M",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(FPS),
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-colorspace",
        "bt709",
        "-movflags",
        "+faststart",
        "-an",
        str(out),
    ]
    proc = p10.run(cmd, capture=True)
    write_log(log, cmd, proc)


def trim_clip(src: Path, out: Path, start: float, duration: float, log: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{max(0.0, start):.3f}",
        "-i",
        str(src),
        "-t",
        f"{duration:.3f}",
        "-vf",
        f"fps={FPS},scale={FRAME_W}:{FRAME_H}:flags=lanczos,setsar=1,format=yuv420p",
        "-an",
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
        "-movflags",
        "+faststart",
        str(out),
    ]
    proc = p10.run(cmd, capture=True)
    write_log(log, cmd, proc)


def make_cut_review_reel(items: list[dict[str, Any]], affected: list[int], out: Path, tmp_dir: Path, logs_dir: Path) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    for idx in affected:
        outgoing = items[idx]
        incoming = items[idx + 1]
        out_dur = outgoing["pass05_segment_probe"]["duration_seconds"]
        tail = tmp_dir / f"{outgoing['order']:02d}_tail.mp4"
        head = tmp_dir / f"{incoming['order']:02d}_head.mp4"
        snippet = tmp_dir / f"{outgoing['order']:02d}_to_{incoming['order']:02d}.mp4"
        trim_clip(Path(outgoing["pass05_segment_path"]), tail, max(0.0, out_dur - 0.650), 0.650, logs_dir / f"cut_reel_{outgoing['order']:02d}_tail.log")
        trim_clip(Path(incoming["pass05_segment_path"]), head, 0.0, 0.450, logs_dir / f"cut_reel_{incoming['order']:02d}_head.log")
        concat([tail, head], snippet, logs_dir / f"cut_reel_{outgoing['order']:02d}_concat.log")
        pieces.append(snippet)
    return concat(pieces, out, logs_dir / "cut_review_reel_concat.log")


def make_cut_review_sheet(items: list[dict[str, Any]], affected: list[int], out: Path, frame_dir: Path) -> None:
    frame_dir.mkdir(parents=True, exist_ok=True)
    font = p10.load_font(18)
    small = p10.load_font(13)
    label_w = 440
    thumb_w = 150
    thumb_h = 267
    gap = 12
    cols = [("out -0.30s", "out", -0.300), ("glitch -0.12s", "out", -0.120), ("glitch -0.03s", "out", -0.030), ("next +0.08s", "in", 0.080)]
    row_h = thumb_h + 34
    sheet = Image.new("RGB", (label_w + len(cols) * thumb_w + (len(cols) + 1) * gap, 62 + len(affected) * row_h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass05 Randomized Signal Interruption - cut review", fill=(255, 255, 255), font=font)
    for c, (name, _, _) in enumerate(cols):
        draw.text((label_w + gap + c * (thumb_w + gap), 24), name, fill=(215, 215, 215), font=small)
    for row_i, idx in enumerate(affected):
        outgoing = items[idx]
        incoming = items[idx + 1]
        y = 62 + row_i * row_h
        variant = outgoing["signal_interruption_render_meta"]["variant_config"]["variant_id"]
        label = f"cut {outgoing['timeline_out_seconds']:.3f}s\n{outgoing['order']:02d} {outgoing['shot_id']} ->\n{incoming['order']:02d} {incoming['shot_id']}\n{variant}"
        for line_i, line in enumerate(label.splitlines()):
            draw.text((16, y + 8 + line_i * 18), line, fill=(235, 235, 235), font=small)
        out_dur = outgoing["pass05_segment_probe"]["duration_seconds"]
        for c, (_, side, offset) in enumerate(cols):
            src = Path(outgoing["pass05_segment_path"]) if side == "out" else Path(incoming["pass05_segment_path"])
            t = max(0.01, out_dur + offset) if side == "out" else offset
            frame = frame_dir / f"cut_{outgoing['order']:02d}_col_{c + 1}_{t:.3f}.png"
            extract_frame(src, frame, t)
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (label_w + gap + c * (thumb_w + gap), y + 8))
    sheet.save(out)


def make_frame_sheet(video: Path, out: Path) -> None:
    duration = p10.duration(video)
    font = p10.load_font(18)
    small = p10.load_font(13)
    cols = 5
    rows = 4
    thumb_w = 180
    thumb_h = 320
    gap = 12
    header_h = 54
    sheet = Image.new("RGB", (cols * thumb_w + (cols + 1) * gap, header_h + rows * (thumb_h + 34)), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 16), "Challenger Motion Proof Pass05 - sampled frames", fill=(255, 255, 255), font=font)
    frame_dir = out.parent / "review_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(cols * rows):
        t = duration * (idx + 1) / (cols * rows + 1)
        frame = frame_dir / f"proof_pass05_sample_{idx + 1:02d}_{t:.3f}.png"
        extract_frame(video, frame, t)
        im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = gap + (idx % cols) * (thumb_w + gap)
        y = header_h + (idx // cols) * (thumb_h + 34)
        sheet.paste(im, (x, y))
        draw.text((x, y + thumb_h + 4), f"{t:.1f}s", fill=(220, 220, 220), font=small)
    sheet.save(out)


def write_beat_sheet(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Motion Video Proof Pass 05 Beat Sheet",
        "",
        f"- `proof_id`: `{manifest['proof_id']}`",
        f"- `proof_video_path`: `{manifest['proof_video_path']}`",
        f"- `motion_only_video_path`: `{manifest['motion_only_video_path']}`",
        f"- `signal_interruption_profile_id`: `{PROFILE_ID}`",
        f"- `signal_interruption_strength`: `{SIGNAL_STRENGTH}`",
        "",
        "| order | shot_id | start | end | duration | interruption | variant | pass05_segment_path |",
        "| ---: | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for item in manifest["items"]:
        variant = "none"
        if item["signal_interruption_applied"]:
            variant = item["signal_interruption_render_meta"]["variant_config"]["variant_id"]
        lines.append(
            f"| {item['order']} | `{item['shot_id']}` | `{item['timeline_in_seconds']:.3f}` | "
            f"`{item['timeline_out_seconds']:.3f}` | `{item['pass05_segment_probe']['duration_seconds']:.3f}` | "
            f"`{item['signal_interruption_applied']}` | `{variant}` | `{item['pass05_segment_path']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate(items: list[dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for item in items:
        path = Path(item["pass05_segment_path"])
        meta = item["pass05_segment_probe"]
        if not path.exists():
            errors.append(f"missing segment {path}")
            continue
        if (meta["width"], meta["height"]) != (FRAME_W, FRAME_H):
            errors.append(f"{path.name} geometry {meta['width']}x{meta['height']}")
        if meta["audio_stream_count"] != 0:
            errors.append(f"{path.name} has audio")
        src_dur = float(item["proof03_segment_probe"]["duration_seconds"])
        if abs(meta["duration_seconds"] - src_dur) > 0.055:
            errors.append(f"{path.name} duration drift {meta['duration_seconds']} vs proof03 {src_dur}")
    for key, audio_expected in [("motion_only_video_path", 0), ("proof_video_path", 1), ("youtube_survival_proxy_path", 0)]:
        meta = probe(Path(manifest[key]))
        if (meta["width"], meta["height"]) != (FRAME_W, FRAME_H):
            errors.append(f"{key} geometry {meta['width']}x{meta['height']}")
        if meta["audio_stream_count"] != audio_expected:
            errors.append(f"{key} audio stream count {meta['audio_stream_count']} expected {audio_expected}")
    if abs(probe(Path(manifest["motion_only_video_path"]))["duration_seconds"] - float(manifest["input_proof03_motion_only_duration_seconds"])) > 0.055:
        errors.append("motion-only duration drift from proof03")
    return errors


def supersede_pass04(pass05_manifest_path: Path, run_id: str) -> None:
    if not PROOF04_MANIFEST.exists():
        return
    old = json.loads(PROOF04_MANIFEST.read_text(encoding="utf-8"))
    old.update(
        {
            "disposition": "tighten",
            "reel_class": "review proof",
            "may_start_video_final": False,
            "superseded_by_motion_video_proof_pass_05_manifest_path": str(pass05_manifest_path),
            "superseded_by_motion_video_proof_pass_05_run_id": run_id,
            "superseded_reason": "User approved the concept but requested randomized signal interruption because Pass04 felt repetitive.",
            "blockers": ["Pass04 signal interruption pattern repeats too visibly; review randomized Pass05 instead."],
        }
    )
    PROOF04_MANIFEST.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    seed = int(run_id.replace("T", "").replace("Z", "")) % 2_147_483_647
    for required in [PROOF03_MANIFEST, APPROVED_AUDIO]:
        if not required.exists():
            raise FileNotFoundError(required)

    proof03 = json.loads(PROOF03_MANIFEST.read_text(encoding="utf-8"))
    items03 = proof03["items"]
    segments_dir = PROOF05_ROOT / "segments"
    logs_dir = PROOF05_ROOT / "logs" / run_id
    work_dir = PROOF05_ROOT / "signal_interruption_work" / run_id
    cut_review_dir = PROOF05_ROOT / "cut_review" / run_id
    proxy_dir = PROOF05_ROOT / "youtube_proxy_5mbps" / run_id
    tail_dir = PROOF05_ROOT / "review_frames_tail"
    for d in [segments_dir, logs_dir, work_dir, cut_review_dir, proxy_dir, tail_dir]:
        d.mkdir(parents=True, exist_ok=True)

    items: list[dict[str, Any]] = []
    affected: list[int] = []
    for idx, item in enumerate(items03):
        order = int(item["order"])
        shot_id = item["shot_id"]
        src = Path(item["proof_segment_path"])
        out = segments_dir / f"{order:02d}_{shot_id}.mp4"
        apply_signal = idx < len(items03) - 1 and selected_for_interruption(item)
        if apply_signal:
            affected.append(idx)
            config = variant_config(seed, order)
            render_meta = render_signal_segment(src, out, work_dir / f"{order:02d}_{shot_id}", logs_dir / f"{order:02d}_{shot_id}__signal_interruption_v2.log", config)
        else:
            render_plain_segment(src, out, logs_dir / f"{order:02d}_{shot_id}__plain.log")
            render_meta = {
                "frame_count": None,
                "glitch_frame_count": 0,
                "interruption_start_frame": None,
                "interruption_start_seconds": None,
                "interruption_duration_seconds": 0.0,
                "variant_config": {"variant_id": "none"},
            }
        items.append(
            {
                **item,
                "proof03_segment_path": item["proof_segment_path"],
                "proof03_segment_probe": item["proof_segment_probe"],
                "pass05_segment_path": str(out),
                "pass05_segment_sha256": sha256(out),
                "pass05_segment_probe": probe(out),
                "signal_interruption_profile_id": PROFILE_ID if apply_signal else "none",
                "signal_interruption_applied": apply_signal,
                "signal_interruption_scope": SIGNAL_SCOPE if apply_signal else "none",
                "signal_interruption_strength": SIGNAL_STRENGTH if apply_signal else "none",
                "signal_interruption_duration_seconds": SIGNAL_DURATION_SECONDS if apply_signal else 0.0,
                "signal_interruption_timing": "final_0.25s_before_outgoing_cut" if apply_signal else "none",
                "signal_interruption_render_meta": render_meta,
                "duration_preservation_read": "pass",
                "audio_preservation_read": "pass",
            }
        )

    motion_only = PROOF05_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_05_motion_only_{run_id}.mp4"
    timeline = concat([Path(item["pass05_segment_path"]) for item in items], motion_only, logs_dir / "pass05_motion_only_concat.log")
    proof_video = PROOF05_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_05_audio_timed_{run_id}.mp4"
    mux_audio(motion_only, APPROVED_AUDIO, proof_video, logs_dir / "pass05_audio_mux.log")
    youtube_path = proxy_dir / f"challenger_short_scoped_v1_motion_video_proof_pass_05_motion_only_{run_id}_youtube_5mbps_proxy.mp4"
    youtube_proxy(motion_only, youtube_path, logs_dir / "pass05_youtube_proxy_5mbps.log")

    cut_sheet = PROOF05_ROOT / f"randomized_signal_interruption_cut_review_{run_id}.png"
    make_cut_review_sheet(items, affected, cut_sheet, cut_review_dir / "frames")
    cut_reel = PROOF05_ROOT / f"randomized_signal_interruption_cut_review_{run_id}.mp4"
    cut_concat = make_cut_review_reel(items, affected, cut_reel, cut_review_dir / "reel_pieces", logs_dir)
    frame_sheet = PROOF05_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_05_frame_sheet_{run_id}.jpg"
    make_frame_sheet(proof_video, frame_sheet)
    proof_duration = p10.duration(proof_video)
    tail_near = tail_dir / f"near_final_{run_id}.png"
    tail_final = tail_dir / f"final_frame_{run_id}.png"
    extract_frame(proof_video, tail_near, max(0.1, proof_duration - 0.5))
    extract_frame(proof_video, tail_final, max(0.1, proof_duration - 0.08))

    manifest = {
        "stage": "motion_video_proof_pass_05",
        "proof_id": "motion_video_proof_pass_05",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "source_proof_manifest_path": str(PROOF03_MANIFEST),
        "source_proof_run_id": proof03.get("run_id"),
        "supersedes_motion_video_proof_pass_04_manifest_path": str(PROOF04_MANIFEST),
        "supersedes_reason": "Randomize the ascent signal interruption because Pass04 felt like the same interrupt at every cut.",
        "input_audio_wav_path": str(APPROVED_AUDIO),
        "approved_audio_sha256": sha256(APPROVED_AUDIO),
        "timeline_mode": "proof03_pass11_historical_signal_segments_with_randomized_ascent_signal_interruption",
        "video_geometry": f"{FRAME_W}x{FRAME_H}",
        "fps": FPS,
        "historical_signal_profile_id": proof03.get("historical_signal_profile_id"),
        "historical_context_year_or_range": proof03.get("historical_context_year_or_range"),
        "source_media_era": proof03.get("source_media_era"),
        "signal_texture_strength": proof03.get("signal_texture_strength"),
        "signal_interruption_profile_id": PROFILE_ID,
        "signal_interruption_profile_source": PROFILE_SOURCE,
        "signal_interruption_scope": SIGNAL_SCOPE,
        "signal_interruption_strength": SIGNAL_STRENGTH,
        "signal_interruption_duration_seconds": SIGNAL_DURATION_SECONDS,
        "signal_interruption_random_seed": seed,
        "signal_interruption_cut_policy": "apply_to_outgoing_segments_with_cut_times_27.000_through_56.300_seconds",
        "affected_cut_times_seconds": [round(float(items[idx]["timeline_out_seconds"]), 3) for idx in affected],
        "affected_outgoing_shot_ids": [items[idx]["shot_id"] for idx in affected],
        "affected_variant_ids": [items[idx]["signal_interruption_render_meta"]["variant_config"]["variant_id"] for idx in affected],
        "no_ltx_or_image_generation_used": True,
        "shot_order_changed": False,
        "source_selection_changed": False,
        "audio_effect_added": False,
        "audio_ducking_added": False,
        "segments_dir": str(segments_dir),
        "timeline_ffconcat_path": str(timeline),
        "motion_only_video_path": str(motion_only),
        "proof_video_path": str(proof_video),
        "youtube_survival_proxy_path": str(youtube_path),
        "cut_review_sheet_path": str(cut_sheet),
        "cut_review_reel_path": str(cut_reel),
        "cut_review_ffconcat_path": str(cut_concat),
        "frame_sheet_path": str(frame_sheet),
        "beat_sheet_path": str(PROOF05_ROOT / "beat_sheet.md"),
        "proof_duration_seconds": round(p10.duration(proof_video), 3),
        "motion_only_duration_seconds": round(p10.duration(motion_only), 3),
        "input_proof03_duration_seconds": proof03.get("proof_duration_seconds"),
        "input_proof03_motion_only_duration_seconds": proof03.get("motion_only_duration_seconds"),
        "proof_video_sha256": sha256(proof_video),
        "motion_only_video_sha256": sha256(motion_only),
        "youtube_survival_proxy_sha256": sha256(youtube_path),
        "motion_only_audio_stream_count": probe(motion_only)["audio_stream_count"],
        "proof_audio_stream_count": probe(proof_video)["audio_stream_count"],
        "youtube_proxy_audio_stream_count": probe(youtube_path)["audio_stream_count"],
        "items": items,
        "tail_frame_check": {"requirement": "legible breakup/debris endpoint remains visible at tail", "read": "pending_human_review", "frame_paths": [str(tail_near), str(tail_final)]},
        "signal_interruption_read": "pending_human_review",
        "signal_interruption_variety_read": "pending_human_review",
        "cut_bridge_read": "pending_human_review",
        "readability_read": "pending_human_review",
        "cheese_read": "pending_human_review",
        "youtube_survival_read": "pending_human_review",
        "compression_artifact_read": "pending_human_review",
        "detail_survival_read": "pending_human_review",
        "duration_preservation_read": "pending_validation",
        "audio_preservation_read": "pending_validation",
        "disposition": "tighten",
        "reel_class": "review proof",
        "may_start_video_final": False,
        "blockers": ["human review required for motion_video_proof_pass_05 before final export", "final export remains blocked"],
    }
    errors = validate(items, manifest)
    manifest.update(
        {
            "validation_status": "pass" if not errors else "reject",
            "validation_errors": errors,
            "duration_preservation_read": "pass" if not errors else "reject",
            "audio_preservation_read": "pass" if not errors else "reject",
        }
    )
    manifest_path = PROOF05_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_beat_sheet(PROOF05_ROOT / "beat_sheet.md", manifest)
    supersede_pass04(manifest_path, run_id)

    review = PROOF05_ROOT / f"review_{run_id}.md"
    review.write_text(
        "\n".join(
            [
                "# Challenger Motion Video Proof Pass 05 Review",
                "",
                f"- `run_id`: `{run_id}`",
                "- `disposition`: `tighten` pending human review",
                f"- `source_proof_manifest_path`: `{PROOF03_MANIFEST}`",
                f"- `supersedes_motion_video_proof_pass_04_manifest_path`: `{PROOF04_MANIFEST}`",
                f"- `signal_interruption_profile_id`: `{PROFILE_ID}`",
                f"- `affected_cut_times_seconds`: `{', '.join(f'{x:.3f}' for x in manifest['affected_cut_times_seconds'])}`",
                f"- `affected_variant_ids`: `{', '.join(manifest['affected_variant_ids'])}`",
                f"- `proof_video`: `{proof_video}`",
                f"- `motion_only_video`: `{motion_only}`",
                f"- `cut_review_sheet`: `{cut_sheet}`",
                f"- `cut_review_reel`: `{cut_reel}`",
                f"- `youtube_survival_proxy_path`: `{youtube_path}`",
                f"- `frame_sheet`: `{frame_sheet}`",
                "- final export remains blocked until this randomized proof is reviewed as `keep`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "run_id": run_id,
                "manifest": str(manifest_path),
                "proof_video": str(proof_video),
                "motion_only_video": str(motion_only),
                "cut_review_sheet": str(cut_sheet),
                "cut_review_reel": str(cut_reel),
                "youtube_survival_proxy": str(youtube_path),
                "frame_sheet": str(frame_sheet),
                "tail_final_frame": str(tail_final),
                "affected_cut_times_seconds": manifest["affected_cut_times_seconds"],
                "affected_variant_ids": manifest["affected_variant_ids"],
                "validation_status": manifest["validation_status"],
                "validation_errors": errors,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
