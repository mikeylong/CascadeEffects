#!/usr/bin/env python3
"""Build Challenger motion_video_proof/pass_04 with ascent-only signal interruption.

This pass starts from the approved Proof03 timed historical-signal segments. It
does not change shot order, source selection, historical CRT texture, or audio.
It only bakes a short visual-only horizontal signal interruption into the final
0.25s of selected shuttle ascent/failure outgoing segments.
"""

from __future__ import annotations

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
PROOF04_ROOT = SHORT_ROOT / "motion_video_proof/pass_04"
APPROVED_AUDIO = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/"
    "challenger_short_restart_v1/final/challenger_short_restart_v1.wav"
)

FRAME_W = 576
FRAME_H = 1024
FPS = 24
SIGNAL_PROFILE_ID = "era_1980s_horizontal_signal_interruption_v1"
SIGNAL_DURATION_SECONDS = 0.25
SIGNAL_STRENGTH = "medium"
SIGNAL_SCOPE = "shuttle_ascent_failure_only"
CUT_SCOPE_START_SECONDS = 27.000
CUT_SCOPE_END_SECONDS = 56.300
CUT_SCOPE_EPSILON = 0.025


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
        "codec_type": video["codec_type"],
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
        ]
        if out.suffix.lower() in {".jpg", ".jpeg"}:
            cmd.extend(["-q:v", "2"])
        cmd.append(str(out))
        p10.run(cmd)
        if out.exists():
            return
    raise FileNotFoundError(out)


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


def add_signal_interruption_to_image(im: Image.Image, *, seed: int, frame_index: int, total_glitch_frames: int) -> Image.Image:
    rng = random.Random(seed + frame_index * 7919)
    out = im.convert("RGB")
    w, h = out.size
    progress = (frame_index + 1) / max(1, total_glitch_frames)

    # Slight chroma displacement sells analog signal break without changing geometry.
    r, g, b = out.split()
    shift = 1 + int(progress * 3)
    r = ImageChops.offset(r, shift, 0)
    b = ImageChops.offset(b, -shift, 0)
    out = Image.merge("RGB", (r, g, b))
    out = ImageEnhance.Contrast(out).enhance(1.04 + 0.08 * progress)
    out = ImageEnhance.Brightness(out).enhance(1.0 + 0.04 * progress)

    # Horizontal tear bands: copy source rows, offset them, and add brief luma bars.
    draw = ImageDraw.Draw(out, "RGBA")
    band_count = 4 + int(progress * 3)
    for _ in range(band_count):
        y = rng.randrange(0, h - 10)
        band_h = rng.choice([4, 6, 8, 10, 14, 18])
        dx = rng.choice([-28, -20, -14, 14, 20, 28])
        band = out.crop((0, y, w, min(h, y + band_h)))
        band = ImageChops.offset(band, dx, 0)
        out.paste(band, (0, y))
        alpha = int(rng.randrange(28, 76) * progress)
        color = (245, 245, 245, alpha) if rng.random() > 0.45 else (5, 5, 5, alpha)
        draw.rectangle((0, y, w, min(h, y + max(2, band_h // 2))), fill=color)

    # Sparse snow only during the interruption; keep opacity restrained.
    noise = Image.effect_noise((w, h), 58 + 18 * progress).convert("L")
    alpha = Image.eval(noise, lambda px: max(0, min(42, int((px - 124) * 0.22 * progress))))
    snow = Image.new("RGB", (w, h), (236, 236, 232))
    out = Image.composite(snow, out, alpha)

    # One or two stronger horizontal dropouts near the end of the interruption.
    draw = ImageDraw.Draw(out, "RGBA")
    for _ in range(1 + int(progress > 0.6)):
        y = rng.randrange(40, h - 40)
        draw.rectangle((0, y, w, y + rng.choice([2, 3, 4])), fill=(255, 255, 255, int(72 * progress)))
        draw.rectangle((0, min(h - 1, y + 5), w, min(h - 1, y + 8)), fill=(0, 0, 0, int(42 * progress)))
    return out


def render_signal_segment(src: Path, out: Path, work_dir: Path, log: Path, *, seed: int) -> dict[str, Any]:
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
            out_im = add_signal_interruption_to_image(
                im,
                seed=seed,
                frame_index=local_idx,
                total_glitch_frames=len(frame_paths[start_index:]),
            )
            out_im.save(frame_path)

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


def make_cut_review_reel(items: list[dict[str, Any]], affected_indexes: list[int], out: Path, tmp_dir: Path, logs_dir: Path) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    for idx in affected_indexes:
        outgoing = items[idx]
        incoming = items[idx + 1]
        outgoing_path = Path(outgoing["pass04_segment_path"])
        incoming_path = Path(incoming["pass04_segment_path"])
        out_dur = outgoing["pass04_segment_probe"]["duration_seconds"]
        tail = tmp_dir / f"{outgoing['order']:02d}_tail.mp4"
        head = tmp_dir / f"{incoming['order']:02d}_head.mp4"
        snippet = tmp_dir / f"{outgoing['order']:02d}_to_{incoming['order']:02d}.mp4"
        trim_clip(outgoing_path, tail, max(0.0, out_dur - 0.650), 0.650, logs_dir / f"cut_reel_{outgoing['order']:02d}_tail.log")
        trim_clip(incoming_path, head, 0.0, 0.450, logs_dir / f"cut_reel_{incoming['order']:02d}_head.log")
        concat([tail, head], snippet, logs_dir / f"cut_reel_{outgoing['order']:02d}_concat.log")
        pieces.append(snippet)
    return concat(pieces, out, logs_dir / "cut_review_reel_concat.log")


def make_cut_review_sheet(items: list[dict[str, Any]], affected_indexes: list[int], out: Path, frame_dir: Path) -> None:
    frame_dir.mkdir(parents=True, exist_ok=True)
    font = p10.load_font(18)
    small = p10.load_font(13)
    label_w = 420
    thumb_w = 150
    thumb_h = 267
    gap = 12
    cols = [
        ("out -0.30s", "out", -0.300),
        ("glitch -0.12s", "out", -0.120),
        ("glitch -0.03s", "out", -0.030),
        ("next +0.08s", "in", 0.080),
    ]
    row_h = thumb_h + 34
    w = label_w + len(cols) * thumb_w + (len(cols) + 1) * gap
    h = 62 + len(affected_indexes) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass04 Ascent Signal Interruption - cut review", fill=(255, 255, 255), font=font)
    for c, (name, _, _) in enumerate(cols):
        draw.text((label_w + gap + c * (thumb_w + gap), 24), name, fill=(215, 215, 215), font=small)
    for row_i, idx in enumerate(affected_indexes):
        outgoing = items[idx]
        incoming = items[idx + 1]
        y = 62 + row_i * row_h
        label = (
            f"cut {outgoing['timeline_out_seconds']:.3f}s\n"
            f"{outgoing['order']:02d} {outgoing['shot_id']} ->\n"
            f"{incoming['order']:02d} {incoming['shot_id']}\n"
            f"{SIGNAL_PROFILE_ID} / {SIGNAL_DURATION_SECONDS:.2f}s"
        )
        for line_i, line in enumerate(label.splitlines()):
            draw.text((16, y + 8 + line_i * 18), line, fill=(235, 235, 235), font=small)
        out_dur = outgoing["pass04_segment_probe"]["duration_seconds"]
        for c, (_, side, offset) in enumerate(cols):
            src = Path(outgoing["pass04_segment_path"]) if side == "out" else Path(incoming["pass04_segment_path"])
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
    draw.text((16, 16), "Challenger Motion Proof Pass04 - sampled frames", fill=(255, 255, 255), font=font)
    frame_dir = out.parent / "review_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(cols * rows):
        t = duration * (idx + 1) / (cols * rows + 1)
        frame = frame_dir / f"proof_pass04_sample_{idx + 1:02d}_{t:.3f}.png"
        extract_frame(video, frame, t)
        im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = gap + (idx % cols) * (thumb_w + gap)
        y = header_h + (idx // cols) * (thumb_h + 34)
        sheet.paste(im, (x, y))
        draw.text((x, y + thumb_h + 4), f"{t:.1f}s", fill=(220, 220, 220), font=small)
    sheet.save(out)


def write_beat_sheet(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Motion Video Proof Pass 04 Beat Sheet",
        "",
        f"- `proof_id`: `{manifest['proof_id']}`",
        f"- `proof_video_path`: `{manifest['proof_video_path']}`",
        f"- `motion_only_video_path`: `{manifest['motion_only_video_path']}`",
        f"- `input_audio_wav_path`: `{manifest['input_audio_wav_path']}`",
        f"- `proof_duration_seconds`: `{manifest['proof_duration_seconds']}`",
        f"- `motion_only_duration_seconds`: `{manifest['motion_only_duration_seconds']}`",
        f"- `timeline_mode`: `{manifest['timeline_mode']}`",
        f"- `signal_interruption_profile_id`: `{SIGNAL_PROFILE_ID}`",
        f"- `signal_interruption_scope`: `{SIGNAL_SCOPE}`",
        f"- `signal_interruption_duration_seconds`: `{SIGNAL_DURATION_SECONDS}`",
        "",
        "| order | shot_id | covered_beat_ids | start_seconds | end_seconds | duration | interruption | pass04_segment_path |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for item in manifest["items"]:
        lines.append(
            f"| {item['order']} | `{item['shot_id']}` | `{', '.join(item['covered_beat_ids'])}` | "
            f"`{item['timeline_in_seconds']:.3f}` | `{item['timeline_out_seconds']:.3f}` | "
            f"`{item['pass04_segment_probe']['duration_seconds']:.3f}` | "
            f"`{item['signal_interruption_applied']}` | `{item['pass04_segment_path']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def selected_for_interruption(item: dict[str, Any]) -> bool:
    cut_time = float(item["timeline_out_seconds"])
    return (
        CUT_SCOPE_START_SECONDS - CUT_SCOPE_EPSILON
        <= cut_time
        <= CUT_SCOPE_END_SECONDS + CUT_SCOPE_EPSILON
    )


def validate(items: list[dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for item in items:
        path = Path(item["pass04_segment_path"])
        if not path.exists():
            errors.append(f"missing segment {path}")
            continue
        meta = item["pass04_segment_probe"]
        if (meta["width"], meta["height"]) != (FRAME_W, FRAME_H):
            errors.append(f"{path.name} geometry {meta['width']}x{meta['height']}")
        if meta["audio_stream_count"] != 0:
            errors.append(f"{path.name} has audio")
        src_dur = float(item["proof03_segment_probe"]["duration_seconds"])
        if abs(meta["duration_seconds"] - src_dur) > 0.055:
            errors.append(f"{path.name} duration drift {meta['duration_seconds']} vs proof03 {src_dur}")
    motion = probe(Path(manifest["motion_only_video_path"]))
    proof = probe(Path(manifest["proof_video_path"]))
    proxy = probe(Path(manifest["youtube_survival_proxy_path"]))
    if (motion["width"], motion["height"]) != (FRAME_W, FRAME_H):
        errors.append(f"motion-only geometry {motion['width']}x{motion['height']}")
    if motion["audio_stream_count"] != 0:
        errors.append("motion-only proof has audio")
    if proof["audio_stream_count"] != 1:
        errors.append(f"audio-timed proof audio stream count {proof['audio_stream_count']}")
    if proxy["audio_stream_count"] != 0:
        errors.append("youtube proxy has audio")
    proof03_motion_duration = float(manifest["input_proof03_motion_only_duration_seconds"])
    if abs(motion["duration_seconds"] - proof03_motion_duration) > 0.055:
        errors.append(f"motion-only duration drift {motion['duration_seconds']} vs proof03 {proof03_motion_duration}")
    return errors


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for required in [PROOF03_MANIFEST, APPROVED_AUDIO]:
        if not required.exists():
            raise FileNotFoundError(required)

    proof03 = json.loads(PROOF03_MANIFEST.read_text(encoding="utf-8"))
    items03 = proof03["items"]
    segments_dir = PROOF04_ROOT / "segments"
    logs_dir = PROOF04_ROOT / "logs" / run_id
    work_dir = PROOF04_ROOT / "signal_interruption_work" / run_id
    cut_review_dir = PROOF04_ROOT / "cut_review" / run_id
    proxy_dir = PROOF04_ROOT / "youtube_proxy_5mbps" / run_id
    tail_dir = PROOF04_ROOT / "review_frames_tail"
    for d in [segments_dir, logs_dir, work_dir, cut_review_dir, proxy_dir, tail_dir]:
        d.mkdir(parents=True, exist_ok=True)

    pass04_items: list[dict[str, Any]] = []
    affected_indexes: list[int] = []
    for idx, item in enumerate(items03):
        order = int(item["order"])
        shot_id = item["shot_id"]
        src = Path(item["proof_segment_path"])
        if not src.exists():
            raise FileNotFoundError(src)
        out = segments_dir / f"{order:02d}_{shot_id}.mp4"
        apply_signal = idx < len(items03) - 1 and selected_for_interruption(item)
        render_meta: dict[str, Any]
        if apply_signal:
            affected_indexes.append(idx)
            render_meta = render_signal_segment(
                src,
                out,
                work_dir / f"{order:02d}_{shot_id}",
                logs_dir / f"{order:02d}_{shot_id}__signal_interruption.log",
                seed=1986 + order,
            )
        else:
            render_plain_segment(src, out, logs_dir / f"{order:02d}_{shot_id}__plain.log")
            render_meta = {
                "frame_count": None,
                "glitch_frame_count": 0,
                "interruption_start_frame": None,
                "interruption_start_seconds": None,
                "interruption_duration_seconds": 0.0,
            }
        pass04_item = {
            **item,
            "proof03_segment_path": item["proof_segment_path"],
            "proof03_segment_probe": item["proof_segment_probe"],
            "pass04_segment_path": str(out),
            "pass04_segment_sha256": p10.sha256(out),
            "pass04_segment_probe": probe(out),
            "signal_interruption_profile_id": SIGNAL_PROFILE_ID if apply_signal else "none",
            "signal_interruption_applied": apply_signal,
            "signal_interruption_scope": SIGNAL_SCOPE if apply_signal else "none",
            "signal_interruption_strength": SIGNAL_STRENGTH if apply_signal else "none",
            "signal_interruption_duration_seconds": SIGNAL_DURATION_SECONDS if apply_signal else 0.0,
            "signal_interruption_timing": "final_0.25s_before_outgoing_cut" if apply_signal else "none",
            "signal_interruption_render_meta": render_meta,
            "duration_preservation_read": "pass",
            "audio_preservation_read": "pass",
        }
        pass04_items.append(pass04_item)

    motion_only = PROOF04_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_04_motion_only_{run_id}.mp4"
    timeline = concat([Path(item["pass04_segment_path"]) for item in pass04_items], motion_only, logs_dir / "pass04_motion_only_concat.log")
    proof_video = PROOF04_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_04_audio_timed_{run_id}.mp4"
    mux_audio(motion_only, APPROVED_AUDIO, proof_video, logs_dir / "pass04_audio_mux.log")
    youtube_proxy_path = proxy_dir / f"challenger_short_scoped_v1_motion_video_proof_pass_04_motion_only_{run_id}_youtube_5mbps_proxy.mp4"
    youtube_proxy(motion_only, youtube_proxy_path, logs_dir / "pass04_youtube_proxy_5mbps.log")

    cut_review_sheet = PROOF04_ROOT / f"ascent_signal_interruption_cut_review_{run_id}.png"
    make_cut_review_sheet(pass04_items, affected_indexes, cut_review_sheet, cut_review_dir / "frames")
    cut_review_reel = PROOF04_ROOT / f"ascent_signal_interruption_cut_review_{run_id}.mp4"
    cut_review_concat = make_cut_review_reel(pass04_items, affected_indexes, cut_review_reel, cut_review_dir / "reel_pieces", logs_dir)
    frame_sheet = PROOF04_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_04_frame_sheet_{run_id}.jpg"
    make_frame_sheet(proof_video, frame_sheet)

    proof_duration = p10.duration(proof_video)
    tail_near = tail_dir / f"near_final_{run_id}.png"
    tail_final = tail_dir / f"final_frame_{run_id}.png"
    extract_frame(proof_video, tail_near, max(0.1, proof_duration - 0.5))
    extract_frame(proof_video, tail_final, max(0.1, proof_duration - 0.08))

    manifest = {
        "stage": "motion_video_proof_pass_04",
        "proof_id": "motion_video_proof_pass_04",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "source_proof_manifest_path": str(PROOF03_MANIFEST),
        "source_proof_run_id": proof03.get("run_id"),
        "input_audio_wav_path": str(APPROVED_AUDIO),
        "approved_audio_sha256": p10.sha256(APPROVED_AUDIO),
        "timeline_mode": "proof03_pass11_historical_signal_segments_with_ascent_only_signal_interruption",
        "video_geometry": f"{FRAME_W}x{FRAME_H}",
        "fps": FPS,
        "historical_signal_profile_id": proof03.get("historical_signal_profile_id"),
        "historical_context_year_or_range": proof03.get("historical_context_year_or_range"),
        "source_media_era": proof03.get("source_media_era"),
        "signal_texture_strength": proof03.get("signal_texture_strength"),
        "signal_interruption_profile_id": SIGNAL_PROFILE_ID,
        "signal_interruption_scope": SIGNAL_SCOPE,
        "signal_interruption_strength": SIGNAL_STRENGTH,
        "signal_interruption_duration_seconds": SIGNAL_DURATION_SECONDS,
        "signal_interruption_cut_policy": "apply_to_outgoing_segments_with_cut_times_27.000_through_56.300_seconds",
        "affected_cut_times_seconds": [
            round(float(pass04_items[idx]["timeline_out_seconds"]), 3) for idx in affected_indexes
        ],
        "affected_outgoing_shot_ids": [pass04_items[idx]["shot_id"] for idx in affected_indexes],
        "no_ltx_or_image_generation_used": True,
        "shot_order_changed": False,
        "source_selection_changed": False,
        "audio_effect_added": False,
        "audio_ducking_added": False,
        "segments_dir": str(segments_dir),
        "timeline_ffconcat_path": str(timeline),
        "motion_only_video_path": str(motion_only),
        "proof_video_path": str(proof_video),
        "youtube_survival_proxy_path": str(youtube_proxy_path),
        "cut_review_sheet_path": str(cut_review_sheet),
        "cut_review_reel_path": str(cut_review_reel),
        "cut_review_ffconcat_path": str(cut_review_concat),
        "frame_sheet_path": str(frame_sheet),
        "beat_sheet_path": str(PROOF04_ROOT / "beat_sheet.md"),
        "proof_duration_seconds": round(p10.duration(proof_video), 3),
        "motion_only_duration_seconds": round(p10.duration(motion_only), 3),
        "input_proof03_duration_seconds": proof03.get("proof_duration_seconds"),
        "input_proof03_motion_only_duration_seconds": proof03.get("motion_only_duration_seconds"),
        "proof_video_sha256": p10.sha256(proof_video),
        "motion_only_video_sha256": p10.sha256(motion_only),
        "youtube_survival_proxy_sha256": p10.sha256(youtube_proxy_path),
        "motion_only_audio_stream_count": probe(motion_only)["audio_stream_count"],
        "proof_audio_stream_count": probe(proof_video)["audio_stream_count"],
        "youtube_proxy_audio_stream_count": probe(youtube_proxy_path)["audio_stream_count"],
        "items": pass04_items,
        "tail_frame_check": {
            "requirement": "legible breakup/debris endpoint remains visible at tail",
            "read": "pending_human_review",
            "frame_paths": [str(tail_near), str(tail_final)],
        },
        "signal_interruption_read": "pending_human_review",
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
        "blockers": [
            "human review required for motion_video_proof_pass_04 before final export",
            "final export remains blocked",
        ],
    }
    validation_errors = validate(pass04_items, manifest)
    manifest.update(
        {
            "validation_status": "pass" if not validation_errors else "reject",
            "validation_errors": validation_errors,
            "duration_preservation_read": "pass" if not validation_errors else "reject",
            "audio_preservation_read": "pass" if not validation_errors else "reject",
        }
    )
    manifest_path = PROOF04_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_beat_sheet(PROOF04_ROOT / "beat_sheet.md", manifest)

    review = PROOF04_ROOT / f"review_{run_id}.md"
    review.write_text(
        "\n".join(
            [
                "# Challenger Motion Video Proof Pass 04 Review",
                "",
                f"- `run_id`: `{run_id}`",
                "- `disposition`: `tighten` pending human review",
                f"- `source_proof_manifest_path`: `{PROOF03_MANIFEST}`",
                f"- `signal_interruption_profile_id`: `{SIGNAL_PROFILE_ID}`",
                f"- `signal_interruption_scope`: `{SIGNAL_SCOPE}`",
                f"- `signal_interruption_strength`: `{SIGNAL_STRENGTH}`",
                f"- `signal_interruption_duration_seconds`: `{SIGNAL_DURATION_SECONDS}`",
                f"- `affected_cut_times_seconds`: `{', '.join(f'{float(pass04_items[idx]['timeline_out_seconds']):.3f}' for idx in affected_indexes)}`",
                f"- `proof_video`: `{proof_video}`",
                f"- `motion_only_video`: `{motion_only}`",
                f"- `cut_review_sheet`: `{cut_review_sheet}`",
                f"- `cut_review_reel`: `{cut_review_reel}`",
                f"- `youtube_survival_proxy_path`: `{youtube_proxy_path}`",
                f"- `frame_sheet`: `{frame_sheet}`",
                "- final export remains blocked until this proof is reviewed as `keep`.",
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
                "cut_review_sheet": str(cut_review_sheet),
                "cut_review_reel": str(cut_review_reel),
                "youtube_survival_proxy": str(youtube_proxy_path),
                "frame_sheet": str(frame_sheet),
                "tail_final_frame": str(tail_final),
                "affected_cut_times_seconds": manifest["affected_cut_times_seconds"],
                "proof_duration_seconds": manifest["proof_duration_seconds"],
                "motion_only_duration_seconds": manifest["motion_only_duration_seconds"],
                "proof_audio_stream_count": manifest["proof_audio_stream_count"],
                "validation_status": manifest["validation_status"],
                "validation_errors": validation_errors,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
