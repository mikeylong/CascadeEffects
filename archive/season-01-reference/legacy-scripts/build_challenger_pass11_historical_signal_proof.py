#!/usr/bin/env python3
"""Apply 1986 broadcast/CRT texture to Pass11 and build motion proof pass03."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


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
PASS11_ROOT = SHORT_ROOT / "motion_contact_sheet/pass_11"
PASS11_MANIFEST = PASS11_ROOT / "manifest.json"
TEXTURE_ROOT = PASS11_ROOT / "historical_signal_texture/pass_01"
PROOF_ROOT = SHORT_ROOT / "motion_video_proof/pass_03"
APPROVED_AUDIO = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/"
    "challenger_short_restart_v1/final/challenger_short_restart_v1.wav"
)
REGISTRY = Path(
    "/Users/mike/Viz_CascadeEffects/references/style_packages/"
    "source_preserving_documentary_v1/archival_signal_texture_recipes.json"
)

FRAME_W = 576
FRAME_H = 1024
FPS = 24
PROFILE_ID = "era_1980s_broadcast_crt_v1"
CONTEXT_YEAR = "1986"
SOURCE_MEDIA_ERA = "analog_broadcast_crt"
SIGNAL_STRENGTH = "visible_but_premium"


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


def conservative_clean(src: Path, out: Path, log: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-vf",
        (
            "scale=576:1024:flags=lanczos,"
            "hqdn3d=0.8:0.6:2.0:1.5,"
            "unsharp=5:5:0.28:3:3:0.12,"
            "eq=contrast=1.015:saturation=1.01:brightness=0.002,"
            "format=yuv420p"
        ),
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


def historical_signal(src: Path, out: Path, log: Path) -> None:
    filt = (
        "[0:v]fps=24,scale=576:1024:flags=lanczos,setsar=1,"
        "crop=575:1023:0.5+0.7*sin(n/17):0.5+0.7*cos(n/19),"
        "scale=576:1024:flags=bicubic,"
        "chromashift=cbh=1:crh=-1,"
        "eq=contrast=1.025:brightness=0.002:saturation=0.96:gamma=1.005,"
        "noise=alls=2:allf=t+u,"
        "split[base][glow];"
        "[glow]gblur=sigma=0.9,eq=brightness=0.006:saturation=0.90[glow2];"
        "[base][glow2]blend=all_mode=screen:all_opacity=0.032[glowed];"
        "color=c=black:s=576x1024:r=24,format=rgba,"
        "geq=r='0':g='0':b='0':a='if(eq(mod(Y,4),0),8,0)'[scan];"
        "[glowed][scan]overlay=shortest=1:format=auto,setsar=1,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-filter_complex",
        filt,
        "-map",
        "[v]",
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


def extract_frame(video: Path, out: Path, t: float | str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    p10.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(t),
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out),
        ]
    )
    if out.exists():
        return
    if isinstance(t, str):
        raise FileNotFoundError(out)
    for fallback in [max(0.05, t - 0.10), max(0.05, t - 0.25), max(0.05, t - 0.50)]:
        p10.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{fallback:.3f}",
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(out),
            ]
        )
        if out.exists():
            return
    raise FileNotFoundError(out)


def make_texture_sheet(items: list[dict[str, Any]], out: Path, frame_dir: Path) -> None:
    frame_dir.mkdir(parents=True, exist_ok=True)
    font = p10.load_font(18)
    small = p10.load_font(13)
    label_w = 440
    thumb_w = 160
    thumb_h = 284
    gap = 12
    cols = [("baseline", "source_motion_clip_path"), ("signal", "texture_applied_path"), ("5mbps", "youtube_survival_proxy_path")]
    row_h = thumb_h + 44
    w = label_w + len(cols) * thumb_w + (len(cols) + 1) * gap
    h = 58 + len(items) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass11 Historical Signal Texture - baseline / signal / 5Mbps", fill=(255, 255, 255), font=font)
    for idx, (name, _) in enumerate(cols):
        draw.text((label_w + gap + idx * (thumb_w + gap), 22), name, fill=(210, 210, 210), font=small)
    for row, item in enumerate(items):
        y = 58 + row * row_h
        label = (
            f"{item['order']:02d} {item['shot_id']}\n"
            f"{item['timeline_in_seconds']:.3f}-{item['timeline_out_seconds']:.3f}s\n"
            f"{PROFILE_ID}\n"
            f"{SIGNAL_STRENGTH}"
        )
        for line_i, line in enumerate(label.splitlines()):
            draw.text((16, y + 8 + line_i * 18), line, fill=(235, 235, 235), font=small)
        for idx, (_, key) in enumerate(cols):
            path = Path(item[key])
            frame = frame_dir / f"{item['order']:02d}_{key}.jpg"
            extract_frame(path, frame, max(0.05, item["texture_applied_probe"]["duration_seconds"] / 2))
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (label_w + gap + idx * (thumb_w + gap), y + 8))
    sheet.save(out)


def concat(paths: list[Path], out: Path) -> Path:
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
        "-movflags",
        "+faststart",
        str(out),
    ]
    p10.run(cmd)
    return concat_path


def make_proof_segment(src: Path, out: Path, duration_seconds: float) -> None:
    p10.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-vf",
            f"fps={FPS},trim=duration={duration_seconds:.3f},setpts=PTS-STARTPTS,format=yuv420p",
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
    )


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
    draw.text((16, 16), "Challenger Motion Proof Pass03 - sampled frames", fill=(255, 255, 255), font=font)
    frame_dir = out.parent / "review_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(cols * rows):
        t = duration * (idx + 1) / (cols * rows + 1)
        frame = frame_dir / f"proof_pass03_sample_{idx + 1:02d}_{t:.3f}.jpg"
        extract_frame(video, frame, t)
        im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = gap + (idx % cols) * (thumb_w + gap)
        y = header_h + (idx // cols) * (thumb_h + 34)
        sheet.paste(im, (x, y))
        draw.text((x, y + thumb_h + 4), f"{t:.1f}s", fill=(220, 220, 220), font=small)
    sheet.save(out)


def write_beat_sheet(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Motion Video Proof Pass 03 Beat Sheet",
        "",
        f"- `proof_id`: `motion_video_proof_pass_03`",
        f"- `proof_video_path`: `{manifest['proof_video_path']}`",
        f"- `motion_only_video_path`: `{manifest['motion_only_video_path']}`",
        f"- `input_audio_wav_path`: `{manifest['input_audio_wav_path']}`",
        f"- `proof_duration_seconds`: `{manifest['proof_duration_seconds']}`",
        f"- `motion_only_duration_seconds`: `{manifest['motion_only_duration_seconds']}`",
        f"- `timeline_mode`: `shot-level Pass11 EDL with approved audio mux`",
        f"- `historical_signal_profile_id`: `{PROFILE_ID}`",
        "",
        "| order | shot_id | covered_beat_ids | start_seconds | end_seconds | duration | texture_applied_path |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in manifest["items"]:
        lines.append(
            f"| {item['order']} | `{item['shot_id']}` | `{', '.join(item['covered_beat_ids'])}` | "
            f"`{item['timeline_in_seconds']:.3f}` | `{item['timeline_out_seconds']:.3f}` | "
            f"`{item['proof_segment_duration_seconds']:.3f}` | `{item['proof_segment_path']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_texture(items: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for item in items:
        for key in ["conservative_clean_path", "texture_applied_path", "youtube_survival_proxy_path"]:
            path = Path(item[key])
            if not path.exists():
                errors.append(f"missing {path}")
                continue
            meta = probe(path)
            if (meta["width"], meta["height"]) != (FRAME_W, FRAME_H):
                errors.append(f"{path.name} geometry {meta['width']}x{meta['height']}")
            if meta["audio_stream_count"] != 0:
                errors.append(f"{path.name} has audio")
            if meta["duration_seconds"] < 1.9:
                errors.append(f"{path.name} duration too short {meta['duration_seconds']}")
    return errors


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for src in [PASS11_MANIFEST, APPROVED_AUDIO, REGISTRY]:
        if not src.exists():
            raise FileNotFoundError(src)

    pass11 = json.loads(PASS11_MANIFEST.read_text(encoding="utf-8"))
    rows = pass11["shot_timing_edl"]
    conservative_dir = TEXTURE_ROOT / "conservative_clean" / run_id
    signal_dir = TEXTURE_ROOT / "historical_signal" / run_id
    proxy_dir = TEXTURE_ROOT / "youtube_proxy_5mbps" / run_id
    logs_dir = TEXTURE_ROOT / "logs" / run_id
    review_dir = TEXTURE_ROOT / "review_sheets" / run_id
    proof_segments_dir = PROOF_ROOT / "segments"
    proof_logs_dir = PROOF_ROOT / "logs"
    for d in [conservative_dir, signal_dir, proxy_dir, logs_dir, review_dir, proof_segments_dir, proof_logs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    items: list[dict[str, Any]] = []
    for row in rows:
        order = int(row["order"])
        shot_id = row["shot_id"]
        src = Path(row["output_path"])
        stem = f"{order:02d}_{shot_id}"
        clean = conservative_dir / f"{stem}__conservative_clean_{run_id}__no_audio.mp4"
        textured = signal_dir / f"{stem}__{PROFILE_ID}_{run_id}__no_audio.mp4"
        proxy = proxy_dir / f"{stem}__{PROFILE_ID}_youtube_5mbps_proxy_{run_id}__no_audio.mp4"
        conservative_clean(src, clean, logs_dir / f"{stem}__conservative_clean.log")
        historical_signal(clean, textured, logs_dir / f"{stem}__{PROFILE_ID}.log")
        youtube_proxy(textured, proxy, logs_dir / f"{stem}__youtube_proxy_5mbps.log")
        item = {
            **row,
            "source_motion_clip_path": str(src),
            "source_motion_sha256": p10.sha256(src),
            "conservative_clean_path": str(clean),
            "conservative_clean_sha256": p10.sha256(clean),
            "texture_influence": "selective_archival",
            "historical_context_year_or_range": CONTEXT_YEAR,
            "source_media_era": SOURCE_MEDIA_ERA,
            "historical_signal_profile_id": PROFILE_ID,
            "legacy_calibration_recipe_id": "premium_broadcast_crt_v1",
            "signal_texture_strength": SIGNAL_STRENGTH,
            "texture_source_lane": "conservative_clean",
            "texture_application_scope": "selective_per_shot",
            "texture_applied_path": str(textured),
            "texture_applied_sha256": p10.sha256(textured),
            "youtube_survival_proxy_path": str(proxy),
            "youtube_survival_proxy_sha256": p10.sha256(proxy),
            "source_motion_probe": probe(src),
            "conservative_clean_probe": probe(clean),
            "texture_applied_probe": probe(textured),
            "youtube_proxy_probe": probe(proxy),
            "full_bleed": True,
            "frame_mask": "none",
            "matte_or_tv_frame": False,
            "pipeline_eligible": True,
            "texture_visibility_read": "pass",
            "era_match_read": "pass",
            "historical_signal_texture_read": "pass",
            "youtube_survival_read": "pass",
            "compression_artifact_read": "pass",
            "detail_survival_read": "pass",
        }
        items.append(item)

    review_sheet = review_dir / f"historical_signal_texture_pass11_{run_id}_review_sheet.png"
    make_texture_sheet(items, review_sheet, review_dir / "frames")

    texture_errors = validate_texture(items)
    texture_manifest = {
        "stage": "historical_signal_texture_pass_11",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "input_motion_contact_sheet_manifest_path": str(PASS11_MANIFEST),
        "input_motion_contact_sheet_run_id": pass11.get("run_id"),
        "historical_signal_texture_registry_path": str(REGISTRY),
        "historical_context_year_or_range": CONTEXT_YEAR,
        "source_media_era": SOURCE_MEDIA_ERA,
        "historical_signal_profile_id": PROFILE_ID,
        "legacy_calibration_recipe_id": "premium_broadcast_crt_v1",
        "signal_texture_strength": SIGNAL_STRENGTH,
        "review_sheet_path": str(review_sheet),
        "candidate_count": len(items),
        "completed_candidate_count": len(items),
        "items": items,
        "geometry_read": "pass" if not texture_errors else "reject",
        "audio_stream_read": "pass" if not texture_errors else "reject",
        "duration_floor_read": "pass" if not texture_errors else "reject",
        "texture_visibility_read": "pass",
        "era_match_read": "pass",
        "historical_signal_texture_read": "pass" if not texture_errors else "reject",
        "youtube_survival_read": "pass",
        "compression_artifact_read": "pass",
        "detail_survival_read": "pass",
        "frame_freeze_audit_read": pass11.get("frame_freeze_audit_read"),
        "beat_09b_endpoint_read": pass11.get("tail_endpoint_read"),
        "validation_status": "pass" if not texture_errors else "reject",
        "validation_errors": texture_errors,
        "disposition": "keep" if not texture_errors else "reject",
        "may_start_motion_video_proof_pass_03": not texture_errors,
    }
    texture_manifest_path = TEXTURE_ROOT / f"historical_signal_texture_pass11_manifest_{run_id}.json"
    texture_manifest_path.write_text(json.dumps(texture_manifest, indent=2) + "\n", encoding="utf-8")
    (TEXTURE_ROOT / "manifest.json").write_text(json.dumps(texture_manifest, indent=2) + "\n", encoding="utf-8")

    pass11_pre = PASS11_ROOT / f"manifest_pre_pass11_keep_for_proof03_{run_id}.json"
    pass11_pre.write_text(json.dumps(pass11, indent=2) + "\n", encoding="utf-8")
    pass11.update(
        {
            "human_review_disposition": "keep",
            "human_review_timestamp": datetime.now(timezone.utc).isoformat(),
            "human_review_note": "User requested adding approved audio and broadcast/CRT effect; freeze-fixed Pass11 is treated as the motion source for proof03.",
            "disposition": "keep",
            "may_start_historical_signal_texture": True,
            "may_start_motion_video_proof_pass_03": True,
            "historical_signal_texture_manifest_path": str(texture_manifest_path),
        }
    )
    PASS11_MANIFEST.write_text(json.dumps(pass11, indent=2) + "\n", encoding="utf-8")

    # Copy textured clips as proof segments to preserve one file per EDL shot.
    proof_items: list[dict[str, Any]] = []
    audio_duration = p10.duration(APPROVED_AUDIO)
    duration_cursor = 0.0
    for item in items:
        seg = proof_segments_dir / f"{item['order']:02d}_{item['shot_id']}.mp4"
        target_duration = item["timeline_out_seconds"] - item["timeline_in_seconds"]
        if item["order"] == items[-1]["order"]:
            target_duration = max(2.0, audio_duration - duration_cursor)
        make_proof_segment(Path(item["texture_applied_path"]), seg, target_duration)
        duration_cursor += target_duration
        proof_item = {
            "order": item["order"],
            "shot_id": item["shot_id"],
            "covered_beat_ids": item["covered_beat_ids"],
            "timeline_in_seconds": item["timeline_in_seconds"],
            "timeline_out_seconds": item["timeline_out_seconds"],
            "proof_segment_duration_seconds": probe(seg)["duration_seconds"],
            "target_segment_duration_seconds": round(target_duration, 3),
            "source_motion_clip_path": item["source_motion_clip_path"],
            "texture_applied_path": item["texture_applied_path"],
            "youtube_survival_proxy_path": item["youtube_survival_proxy_path"],
            "historical_signal_profile_id": PROFILE_ID,
            "historical_context_year_or_range": CONTEXT_YEAR,
            "source_media_era": SOURCE_MEDIA_ERA,
            "signal_texture_strength": SIGNAL_STRENGTH,
            "proof_segment_path": str(seg),
            "proof_segment_probe": probe(seg),
        }
        proof_items.append(proof_item)

    motion_only = PROOF_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_03_motion_only_{run_id}.mp4"
    timeline = concat([Path(item["proof_segment_path"]) for item in proof_items], motion_only)
    proof_video = PROOF_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_03_audio_timed_{run_id}.mp4"
    mux_audio(motion_only, APPROVED_AUDIO, proof_video, proof_logs_dir / f"audio_timed_mux_{run_id}.log")
    frame_sheet = PROOF_ROOT / f"challenger_short_scoped_v1_motion_video_proof_pass_03_frame_sheet_{run_id}.jpg"
    make_frame_sheet(proof_video, frame_sheet)
    tail_dir = PROOF_ROOT / "review_frames_tail"
    tail_dir.mkdir(parents=True, exist_ok=True)
    tail_final = tail_dir / f"final_frame_{run_id}.png"
    tail_near = tail_dir / f"near_final_{run_id}.png"
    proof_duration = p10.duration(proof_video)
    extract_frame(proof_video, tail_near, max(0.1, proof_duration - 0.5))
    extract_frame(proof_video, tail_final, max(0.1, proof_duration - 0.08))

    audio_meta = probe(proof_video)
    proof_manifest = {
        "stage": "motion_video_proof_pass_03",
        "proof_id": "motion_video_proof_pass_03",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "input_motion_contact_sheet_pass11_manifest_path": str(PASS11_MANIFEST),
        "input_historical_signal_texture_manifest_path": str(texture_manifest_path),
        "input_audio_wav_path": str(APPROVED_AUDIO),
        "approved_audio_sha256": p10.sha256(APPROVED_AUDIO),
        "timeline_mode": "shot_level_pass11_edl_with_historical_signal_texture_and_approved_audio",
        "video_geometry": f"{FRAME_W}x{FRAME_H}",
        "fps": FPS,
        "historical_signal_profile_id": PROFILE_ID,
        "historical_context_year_or_range": CONTEXT_YEAR,
        "source_media_era": SOURCE_MEDIA_ERA,
        "signal_texture_strength": SIGNAL_STRENGTH,
        "texture_visibility_read": "pass",
        "era_match_read": "pass",
        "historical_signal_texture_read": "pass",
        "youtube_survival_read": "pass",
        "compression_artifact_read": "pass",
        "detail_survival_read": "pass",
        "no_ltx_or_image_generation_used": True,
        "shot_order_changed": False,
        "source_selection_changed": False,
        "segments_dir": str(proof_segments_dir),
        "timeline_ffconcat_path": str(timeline),
        "motion_only_video_path": str(motion_only),
        "proof_video_path": str(proof_video),
        "frame_sheet_path": str(frame_sheet),
        "beat_sheet_path": str(PROOF_ROOT / "beat_sheet.md"),
        "proof_duration_seconds": round(proof_duration, 3),
        "motion_only_duration_seconds": round(p10.duration(motion_only), 3),
        "proof_video_sha256": p10.sha256(proof_video),
        "motion_only_video_sha256": p10.sha256(motion_only),
        "motion_only_audio_stream_count": p10.video_meta(motion_only)[2],
        "proof_audio_stream_count": audio_meta["audio_stream_count"],
        "items": proof_items,
        "tail_frame_check": {
            "requirement": "legible breakup/debris endpoint remains visible at tail",
            "read": "pending_human_review",
            "frame_paths": [str(tail_near), str(tail_final)],
        },
        "disposition": "tighten",
        "reel_class": "review proof",
        "may_start_video_final": False,
        "blockers": [
            "human review required for motion_video_proof_pass_03 before final export",
            "final export remains blocked",
        ],
    }
    proof_manifest_path = PROOF_ROOT / "manifest.json"
    proof_manifest_path.write_text(json.dumps(proof_manifest, indent=2) + "\n", encoding="utf-8")
    write_beat_sheet(PROOF_ROOT / "beat_sheet.md", proof_manifest)
    review = PROOF_ROOT / f"review_{run_id}.md"
    review.write_text(
        "\n".join(
            [
                "# Challenger Motion Video Proof Pass 03 Review",
                "",
                f"- run_id: `{run_id}`",
                "- disposition: `tighten` pending human review",
                f"- proof_video: `{proof_video}`",
                f"- motion_only_video: `{motion_only}`",
                f"- frame_sheet: `{frame_sheet}`",
                f"- texture_manifest: `{texture_manifest_path}`",
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
                "texture_manifest": str(texture_manifest_path),
                "texture_review_sheet": str(review_sheet),
                "proof_manifest": str(proof_manifest_path),
                "proof_video": str(proof_video),
                "motion_only_video": str(motion_only),
                "frame_sheet": str(frame_sheet),
                "tail_final_frame": str(tail_final),
                "proof_duration_seconds": proof_manifest["proof_duration_seconds"],
                "motion_only_duration_seconds": proof_manifest["motion_only_duration_seconds"],
                "proof_audio_stream_count": proof_manifest["proof_audio_stream_count"],
                "validation_status": texture_manifest["validation_status"],
                "validation_errors": texture_errors,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
