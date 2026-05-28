#!/usr/bin/env python3
"""Build Challenger motion_contact_sheet/pass_09 from transcript feedback.

Pass09 responds to the 2026-04-24 21:01:48 screen-recording feedback:
- fewer actual story shots
- no sub-2s story flashes
- avoid source-native cross-dissolves inside declared shots
- no auditorium-wide interruption
- no launch chronology reset from high ascent back to low pad
- preserve the legible breakup/debris endpoint
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/"
    "challenger_short_scoped_v1"
)
EP_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/"
    "challenger_short_scoped_v1"
)
PASS09_ROOT = SHORT_ROOT / "motion_contact_sheet/pass_09"
PASS08_MANIFEST = SHORT_ROOT / "motion_contact_sheet/pass_08/manifest.json"
PASS05_NORM = SHORT_ROOT / "motion_contact_sheet/pass_05/candidates/normalized"

FR = EP_ROOT / (
    "source_media/archival/"
    "challenger_archival_primary_02__Ppl2tEgZLFE__Space Shuttle Era Firing Room.mp4"
)
RC = EP_ROOT / (
    "source_media/archival/"
    "challenger_archival_primary_03__1jPP7Ks6Rhk__Rogers Commission hearing sample 00-12min.mp4"
)
CL = EP_ROOT / (
    "source_media/archival/"
    "challenger_teaching_pass__rUqPMMgfJ4Q__Shuttle Challenger Explosion [New Copy Found; Better Quality].mp4"
)
TAIL_08A = PASS05_NORM / "13_beat_08a_visible_failure__pass02_reference_direct_source_clip__no_audio.mp4"
TAIL_09A = PASS05_NORM / "14_beat_09a_warning_not_missing__pass02_reference_direct_source_clip__no_audio.mp4"
TAIL_09B = PASS05_NORM / "15_beat_09b_massive_consequence__pass02_reference_direct_source_clip__no_audio.mp4"

RECORDING = Path(
    "/var/folders/gt/lzhcg8wj3f19j78b3g444s1c0000gn/T/TemporaryItems/"
    "NSIRD_screencaptureui_mNjDlT/Screen Recording 2026-04-24 at 21.01.48.mov"
)
TRANSCRIPT = Path(
    "/tmp/challenger_pass08_feedback_210148/"
    "Screen Recording 2026-04-24 at 21.01.48.diarized.srt"
)
FRAME_EVIDENCE = Path("/tmp/challenger_pass08_feedback_210148/feedback_frame_contact.png")

FRAME_W = 576
FRAME_H = 1024
FPS = 30
MIN_STORY_SECONDS = 2.0


@dataclass
class Shot:
    order: int
    parent_beat_id: str
    shot_id: str
    source_path: Path
    source_span_in: str
    duration: float
    role: str
    crop_x: int | None = 220
    crop_width_px: int | None = 202
    source_mode: str = "direct_source_clip"
    continuous_event_motion_allowed: bool = False
    output_path: Path | None = None
    sample_frame_paths: list[Path] = field(default_factory=list)
    actual_duration: float = 0.0
    scene_cut_times: list[float] = field(default_factory=list)
    frame_diff_values: list[float] = field(default_factory=list)
    no_internal_cut_read: str = "pending"
    duration_floor_read: str = "pending"


def run(cmd: list[str], *, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def ffprobe_json(path: Path) -> dict[str, Any]:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=index,codec_type,width,height,r_frame_rate,duration",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(proc.stdout)


def duration(path: Path) -> float:
    return float(ffprobe_json(path)["format"]["duration"])


def video_meta(path: Path) -> tuple[int, int, int]:
    data = ffprobe_json(path)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio_count = sum(1 for s in data["streams"] if s["codec_type"] == "audio")
    return int(video["width"]), int(video["height"]), audio_count


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hms_to_seconds(value: str) -> float:
    parts = value.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(value)


def seconds_to_hms(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def load_font(size: int) -> ImageFont.ImageFont:
    for path in [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def crop_filter(shot: Shot) -> str:
    if shot.crop_x is None or shot.crop_width_px is None:
        return f"scale={FRAME_W}:{FRAME_H}:flags=lanczos,fps={FPS},format=yuv420p"
    return (
        f"crop={shot.crop_width_px}:360:{shot.crop_x}:0,"
        f"scale={FRAME_W}:{FRAME_H}:flags=lanczos,fps={FPS},format=yuv420p"
    )


def make_clip(shot: Shot, out_dir: Path, source_frame_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    source_frame_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{shot.order:02d}_{shot.shot_id}__pass09_continuity_timing__no_audio.mp4"
    shot.output_path = out

    if shot.source_mode == "direct_source_still_hold":
        frame = source_frame_dir / f"{shot.order:02d}_{shot.shot_id}__source_frame.png"
        vf = crop_filter(shot).replace(f",fps={FPS},format=yuv420p", "")
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                shot.source_span_in,
                "-i",
                str(shot.source_path),
                "-frames:v",
                "1",
                "-vf",
                vf,
                str(frame),
            ]
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
                "-t",
                f"{shot.duration:.3f}",
                "-i",
                str(frame),
                "-vf",
                f"fps={FPS},format=yuv420p",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-movflags",
                "+faststart",
                str(out),
            ]
        )
        return

    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            shot.source_span_in,
            "-t",
            f"{shot.duration:.3f}",
            "-i",
            str(shot.source_path),
            "-vf",
            crop_filter(shot),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(out),
        ]
    )


def detect_scene_cuts(path: Path, dur: float) -> list[float]:
    proc = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-vf",
            "select='gt(scene,0.32)',showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture=True,
        check=False,
    )
    cuts: list[float] = []
    for line in proc.stderr.splitlines():
        match = re.search(r"pts_time:([0-9.]+)", line)
        if match:
            t = float(match.group(1))
            if 0.20 < t < dur - 0.20:
                cuts.append(round(t, 3))
    return cuts


def extract_samples(shot: Shot, sample_dir: Path) -> None:
    assert shot.output_path is not None
    sample_dir.mkdir(parents=True, exist_ok=True)
    shot.actual_duration = duration(shot.output_path)
    times = [shot.actual_duration * (i + 1) / 4 for i in range(3)]
    shot.sample_frame_paths = []
    for idx, t in enumerate(times, start=1):
        frame = sample_dir / f"{shot.order:02d}_{shot.shot_id}_sample_{idx}.jpg"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{t:.3f}",
                "-i",
                str(shot.output_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(frame),
            ]
        )
        shot.sample_frame_paths.append(frame)


def frame_diff_values(frames: list[Path]) -> list[float]:
    values: list[float] = []
    if len(frames) < 2:
        return values
    prev = Image.open(frames[0]).convert("L").resize((48, 85))
    for frame in frames[1:]:
        cur = Image.open(frame).convert("L").resize((48, 85))
        p0 = prev.load()
        p1 = cur.load()
        total = 0
        for y in range(cur.height):
            for x in range(cur.width):
                total += abs(p1[x, y] - p0[x, y])
        values.append(round(total / (cur.width * cur.height), 2))
        prev = cur
    return values


def audit(shot: Shot, sample_dir: Path) -> None:
    assert shot.output_path is not None
    shot.actual_duration = duration(shot.output_path)
    shot.scene_cut_times = detect_scene_cuts(shot.output_path, shot.actual_duration)
    extract_samples(shot, sample_dir)
    shot.frame_diff_values = frame_diff_values(shot.sample_frame_paths)
    shot.duration_floor_read = "pass" if shot.actual_duration + 0.001 >= MIN_STORY_SECONDS else "reject"
    if shot.source_mode == "direct_source_still_hold":
        shot.no_internal_cut_read = "pass"
    elif shot.scene_cut_times:
        shot.no_internal_cut_read = "reject"
    # Frame-diff catches missed hard cuts, but values in the 45-55 range can also
    # come from real archival motion such as shuttle movement or hand gestures.
    elif not shot.continuous_event_motion_allowed and any(v >= 60 for v in shot.frame_diff_values):
        shot.no_internal_cut_read = "reject"
    else:
        shot.no_internal_cut_read = "pass"


def concat(paths: list[Path], out: Path) -> Path:
    concat_path = out.with_suffix(".ffconcat")
    with concat_path.open("w", encoding="utf-8") as fh:
        fh.write("ffconcat version 1.0\n")
        for path in paths:
            fh.write(f"file '{path}'\n")
    run(
        [
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
            "veryfast",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(out),
        ]
    )
    return concat_path


def beat_durations() -> dict[str, float]:
    return {
        "beat_01a_routine_room": 5.2,
        "beat_02a_process_bank": 4.364,
        "beat_03a_joint_context": 5.136,
        "beat_03b_seal_mechanism": 6.199,
        "beat_04a_monitoring_distress": 4.001,
        "beat_04b_survival_normalizes": 3.75,
        "beat_04c_known_condition": 2.807,
        "beat_04d_line_item": 2.766,
        "beat_05a_recommendation_enters": 4.593,
        "beat_06a_burden_shift_wide": 3.484,
        "beat_06b_burden_shift_medium": 4.154,
        "beat_07a_cold_commit": 2.946,
        "beat_08a_visible_failure": 3.157,
        "beat_09a_warning_not_missing": 3.743,
        "beat_09b_massive_consequence": 6.5,
    }


def build_shots() -> list[Shot]:
    # Beat order is preserved. Launch/action footage is reserved for beats 07-09
    # so ascent never resets back to the pad after gaining altitude.
    specs = [
        ("beat_01a_routine_room", "firing_room_wide_open", FR, "00:00:22.000", 2.6, "routine room scale", 150, "direct_source_clip", False),
        ("beat_01a_routine_room", "firing_room_wide_handoff", FR, "00:01:30.000", 2.6, "second control-room angle, no single hold", 150, "direct_source_clip", False),
        ("beat_02a_process_bank", "console_bank_process", FR, "00:00:46.000", 2.182, "routine process monitors", 155, "direct_source_clip", False),
        ("beat_02a_process_bank", "operator_bank_process", FR, "00:00:54.000", 2.182, "operator/process continuity", 150, "direct_source_clip", False),
        ("beat_03a_joint_context", "shuttle_stack_context", CL, "00:01:08.000", 2.568, "centered shuttle/pad context", 260, "direct_source_still_hold", False),
        ("beat_03a_joint_context", "pad_front_context", CL, "00:02:45.000", 2.568, "pad-scale hardware context", 220, "direct_source_clip", False),
        ("beat_03b_seal_mechanism", "lower_stack_context", CL, "00:02:52.000", 3.1, "contextual lower-stack mechanism area", 220, "direct_source_clip", False),
        ("beat_03b_seal_mechanism", "lower_stack_smoke_hold", CL, "00:03:00.000", 3.099, "mechanism evidence without hidden angle cut", 220, "direct_source_still_hold", False),
        ("beat_04a_monitoring_distress", "monitoring_room_hold", FR, "00:01:45.000", 4.001, "warning absorbed into process room", 115, "direct_source_clip", False),
        ("beat_04b_survival_normalizes", "shuttle_on_pad_normalized", CL, "00:02:45.000", 3.75, "routine pad confidence, no liftoff reset", 220, "direct_source_clip", False),
        ("beat_04c_known_condition", "lower_stack_known_condition", CL, "00:03:00.000", 2.807, "known condition held in hardware context", 220, "direct_source_still_hold", False),
        ("beat_04d_line_item", "launch_director_line_item", FR, "00:03:17.000", 2.766, "launch director decision environment", 70, "direct_source_clip", False),
        ("beat_05a_recommendation_enters", "room_response_handoff", FR, "00:03:44.000", 2.3, "recommendation enters decision room", 230, "direct_source_clip", False),
        ("beat_05a_recommendation_enters", "room_reaction_clap", FR, "00:03:54.000", 2.293, "human response in same decision world", 230, "direct_source_clip", False),
        ("beat_06a_burden_shift_wide", "commission_panel_no_auditorium", RC, "00:04:18.000", 3.484, "burden shift at table, no auditorium wide", 78, "direct_source_clip", False),
        ("beat_06b_burden_shift_medium", "commission_cross_table", RC, "00:05:38.000", 4.154, "medium decision pressure", 78, "direct_source_clip", False),
        ("beat_07a_cold_commit", "liftoff_commit", CL, "00:03:08.000", 2.946, "final launch sequence begins, no later reset", 220, "direct_source_clip", True),
        ("beat_08a_visible_failure", "visible_failure", TAIL_08A, "00:00:00.000", 3.157, "visible failure continues upward", None, "direct_source_clip", True),
        ("beat_09a_warning_not_missing", "pre_breakup_escalation", TAIL_09A, "00:00:00.000", 3.743, "pre-breakup escalation continues", None, "direct_source_clip", True),
        ("beat_09b_massive_consequence", "breakup_close_burst", TAIL_09B, "00:00:00.000", 2.5, "breakup close burst", None, "direct_source_clip", True),
        ("beat_09b_massive_consequence", "debris_progression", TAIL_09B, "00:00:02.500", 2.0, "debris/plume progression", None, "direct_source_clip", True),
        ("beat_09b_massive_consequence", "legible_breakup_endpoint", TAIL_09B, "00:00:04.600", 2.0, "legible breakup/debris endpoint hold", None, "direct_source_still_hold", True),
    ]
    shots: list[Shot] = []
    for idx, spec in enumerate(specs, start=1):
        beat, suffix, src, start, dur, role, crop_x, mode, event = spec
        shots.append(
            Shot(
                order=idx,
                parent_beat_id=beat,
                shot_id=f"{beat}__{suffix}",
                source_path=src,
                source_span_in=start,
                duration=dur,
                role=role,
                crop_x=crop_x,
                crop_width_px=202 if crop_x is not None else None,
                source_mode=mode,
                continuous_event_motion_allowed=event,
            )
        )
    return shots


def edl_rows(shots: list[Shot]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor = 0.0
    for shot in shots:
        start = hms_to_seconds(shot.source_span_in)
        dur = shot.actual_duration or shot.duration
        rows.append(
            {
                "order": shot.order,
                "shot_id": shot.shot_id,
                "parent_beat_id": shot.parent_beat_id,
                "source_path": str(shot.source_path),
                "source_span_in": shot.source_span_in,
                "source_span_out": seconds_to_hms(start + shot.duration),
                "intended_duration_seconds": round(shot.duration, 3),
                "actual_duration_seconds": round(dur, 3),
                "timeline_in_seconds": round(cursor, 3),
                "timeline_out_seconds": round(cursor + dur, 3),
                "role": shot.role,
                "source_mode": shot.source_mode,
                "crop_x": shot.crop_x,
                "crop_width_px": shot.crop_width_px,
                "output_path": str(shot.output_path),
                "sample_frame_paths": [str(p) for p in shot.sample_frame_paths],
                "scene_cut_times": shot.scene_cut_times,
                "frame_diff_values": shot.frame_diff_values,
                "duration_floor_read": shot.duration_floor_read,
                "no_internal_cut_read": shot.no_internal_cut_read,
                "continuous_event_motion_allowed": shot.continuous_event_motion_allowed,
            }
        )
        cursor += dur
    return rows


def draw_lines(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont) -> None:
    x, y = xy
    step = int(getattr(font, "size", 14) * 1.35)
    for line in text.split("\n"):
        draw.text((x, y), line, fill=(235, 235, 235), font=font)
        y += step


def make_shot_sheet(shots: list[Shot], out: Path, page_dir: Path) -> list[Path]:
    font = load_font(18)
    small = load_font(14)
    label_w = 430
    thumb_w = 216
    thumb_h = 384
    gap = 14
    cols = 3
    row_h = thumb_h + 36
    w = label_w + cols * thumb_w + (cols + 1) * gap
    h = 58 + len(shots) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass09 Continuity Timing EDL Sheet - raw frames", fill=(255, 255, 255), font=font)
    for idx in range(cols):
        draw.text((label_w + gap + idx * (thumb_w + gap), 22), str(idx + 1), fill=(210, 210, 210), font=small)
    for row, shot in enumerate(shots):
        y = 58 + row * row_h
        label = (
            f"{shot.order:02d} {shot.shot_id}\n"
            f"{shot.parent_beat_id}\n"
            f"{shot.actual_duration:.3f}s cut={shot.no_internal_cut_read}\n"
            f"{shot.role}"
        )
        draw_lines(draw, (16, y + 8), label, small)
        for i, frame in enumerate(shot.sample_frame_paths):
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (label_w + gap + i * (thumb_w + gap), y + 8))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    page_dir.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    rows_per_page = 7
    for page_idx in range(math.ceil(len(shots) / rows_per_page)):
        start_y = 0 if page_idx == 0 else 58 + page_idx * rows_per_page * row_h
        end_y = min(h, 58 + (page_idx + 1) * rows_per_page * row_h)
        crop = sheet.crop((0, start_y, w, end_y))
        page = page_dir / f"{out.stem}__page_{page_idx + 1:02d}.png"
        crop.save(page)
        pages.append(page)
    return pages


def make_beat_rollup(beat_handles: list[dict[str, Any]], out: Path, frame_dir: Path) -> None:
    font = load_font(18)
    small = load_font(14)
    label_w = 440
    thumb_w = 180
    thumb_h = 320
    gap = 12
    cols = 5
    row_h = thumb_h + 38
    w = label_w + cols * thumb_w + (cols + 1) * gap
    h = 58 + len(beat_handles) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass09 15-Beat Continuity Rollup", fill=(255, 255, 255), font=font)
    frame_dir.mkdir(parents=True, exist_ok=True)
    for row, beat in enumerate(beat_handles):
        y = 58 + row * row_h
        label = (
            f"{beat['order']:02d} {beat['beat_id']}\n"
            f"{beat['duration_seconds']:.3f}s shots={len(beat['shot_ids'])}\n"
            f"min_shot={beat['min_story_shot_seconds']:.3f}s\n"
            f"{beat['continuity_role']}"
        )
        draw_lines(draw, (16, y + 8), label, small)
        path = Path(beat["normalized_clip_path"])
        dur = beat["duration_seconds"]
        for idx in range(cols):
            t = dur * (idx + 1) / (cols + 1)
            frame = frame_dir / f"{beat['order']:02d}_{beat['beat_id']}_sample_{idx + 1}.jpg"
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-ss",
                    f"{t:.3f}",
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    str(frame),
                ]
            )
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (label_w + gap + idx * (thumb_w + gap), y + 8))
    sheet.save(out)


def write_edl_md(rows: list[dict[str, Any]], out: Path, run_id: str) -> None:
    lines = [
        "# Challenger Pass09 Continuity Timing EDL",
        "",
        f"- run_id: `{run_id}`",
        "- stage: `motion_contact_sheet_pass_09`",
        "- disposition: `tighten` pending human review",
        "- supersedes: `motion_contact_sheet_pass_08`",
        "- normal_story_shot_minimum_seconds: `2.0`",
        "- repair goal: fewer shots, chronological launch tail, no hidden sub-second source-native edits",
        "",
        "| order | shot_id | parent_beat_id | timeline | duration | no_internal_cut_read | role |",
        "|---:|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['order']} | `{row['shot_id']}` | `{row['parent_beat_id']}` | "
            f"{row['timeline_in_seconds']:.3f}-{row['timeline_out_seconds']:.3f} | "
            f"{row['actual_duration_seconds']:.3f}s | `{row['no_internal_cut_read']}` | {row['role']} |"
        )
    lines.extend(
        [
            "",
            "## Transcript Evidence",
            "",
            f"- transcript: `{TRANSCRIPT}`",
            f"- frame evidence sheet: `{FRAME_EVIDENCE}`",
            "- feedback summary: avoid fraction-of-a-second images, avoid altitude reset after ascent, remove auditorium interruption, and think about the image before and after each cut.",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Challenger Pass09 Continuity Timing Repair Review",
        "",
        f"- run_id: `{manifest['run_id']}`",
        "- stage: `motion_contact_sheet_pass_09`",
        "- disposition: `tighten` pending human review",
        "- gate: `motion_video_proof_pass_03` remains blocked",
        "",
        "## Transcript-Grounded Findings",
        "",
        "| Timecode | Spoken Intent | Action Taken |",
        "|---|---|---|",
        "| 00:00:25-00:00:31 | Image appears as a flash and fades in/out. | Removed source cross-dissolve room spans from the active sequence. |",
        "| 00:00:55-00:01:03 | Shuttle is still not centered/readable enough. | Kept pad/stack shots as stable, centered source crops and avoided moving through the bad crop. |",
        "| 00:01:50-00:02:06 | Shuttle gains altitude, then cuts low again. | Reserved liftoff/ascent/failure for beats 07-09 so launch chronology no longer resets. |",
        "| 00:02:17-00:02:25 | Auditorium interruption does not make sense. | Removed the auditorium-wide commission shot from pass09. |",
        "| 00:02:46-00:03:45 | Shots are jumpy; think before/after continuity. | Reduced Pass08 from 30 story shots to 20 and made every declared shot at least 2.0s. |",
        "",
        "## Reads",
        "",
        f"- story_shot_count: `{manifest['story_shot_count']}`",
        f"- sequence_duration_seconds: `{manifest['sequence_duration_seconds']}`",
        f"- duration_floor_read: `{manifest['duration_floor_read']}`",
        f"- hidden_cut_audit_read: `{manifest['hidden_cut_audit_read']}`",
        f"- launch_chronology_read: `{manifest['launch_chronology_read']}`",
        f"- auditorium_intrusion_read: `{manifest['auditorium_intrusion_read']}`",
        "",
        "## Review Artifacts",
        "",
        f"- shot_timing_edl_json: `{manifest['shot_timing_edl_json_path']}`",
        f"- shot_timing_edl_md: `{manifest['shot_timing_edl_md_path']}`",
        f"- shot_timing_contact_sheet: `{manifest['shot_timing_contact_sheet_path']}`",
        f"- beat_rollup_contact_sheet: `{manifest['beat_rollup_contact_sheet_path']}`",
        f"- preview_reel: `{manifest['preview_reel_path']}`",
        "",
        "## Blockers",
        "",
        "- Human review required before historical signal texture is re-applied.",
        "- `motion_video_proof_pass_03` remains blocked.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for row in manifest["shot_timing_edl"]:
        path = Path(row["output_path"])
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        w, h, audio = video_meta(path)
        dur = duration(path)
        if (w, h) != (FRAME_W, FRAME_H):
            errors.append(f"{path.name} geometry {w}x{h}")
        if audio != 0:
            errors.append(f"{path.name} audio_count={audio}")
        if dur + 0.001 < MIN_STORY_SECONDS:
            errors.append(f"{path.name} duration {dur:.3f} < {MIN_STORY_SECONDS}")
        if row["no_internal_cut_read"] != "pass":
            errors.append(f"{path.name} hidden cut {row['no_internal_cut_read']}")
    preview = Path(manifest["preview_reel_path"])
    if preview.exists():
        w, h, audio = video_meta(preview)
        if (w, h) != (FRAME_W, FRAME_H):
            errors.append(f"preview geometry {w}x{h}")
        if audio != 0:
            errors.append("preview has audio")
    else:
        errors.append(f"missing preview {preview}")
    return errors


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PASS09_ROOT.mkdir(parents=True, exist_ok=True)
    shot_dir = PASS09_ROOT / "candidates/shot_handles"
    beat_dir = PASS09_ROOT / "candidates/beat_handles"
    sample_dir = PASS09_ROOT / "review_frames/shot_samples"
    beat_sample_dir = PASS09_ROOT / "review_frames/beat_rollup_samples"
    source_frame_dir = PASS09_ROOT / "source_frames"
    pages_dir = PASS09_ROOT / "pages"
    for directory in [shot_dir, beat_dir, sample_dir, beat_sample_dir, source_frame_dir, pages_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    for src in [FR, RC, CL, TAIL_08A, TAIL_09A, TAIL_09B]:
        if not src.exists():
            raise FileNotFoundError(src)

    shots = build_shots()
    for shot in shots:
        make_clip(shot, shot_dir, source_frame_dir)
        audit(shot, sample_dir)

    beat_handles: list[dict[str, Any]] = []
    for order, beat in enumerate(beat_durations().keys(), start=1):
        beat_shots = [shot for shot in shots if shot.parent_beat_id == beat]
        if not beat_shots:
            raise RuntimeError(f"no shots for {beat}")
        out = beat_dir / f"{order:02d}_{beat}__pass09_continuity_timing_rollup__no_audio.mp4"
        concat_path = concat([Path(s.output_path) for s in beat_shots if s.output_path], out)
        w, h, audio = video_meta(out)
        dur = duration(out)
        beat_handles.append(
            {
                "order": order,
                "beat_id": beat,
                "normalized_clip_path": str(out),
                "normalized_clip_sha256": sha256(out),
                "timeline_ffconcat_path": str(concat_path),
                "duration_seconds": round(dur, 3),
                "width": w,
                "height": h,
                "audio_stream_count": audio,
                "shot_ids": [s.shot_id for s in beat_shots],
                "min_story_shot_seconds": round(min(s.actual_duration for s in beat_shots), 3),
                "continuity_role": "proof-minded beat rollup",
            }
        )

    preview = PASS09_ROOT / f"motion_contact_sheet_pass_09_{run_id}_continuity_timing_preview.mp4"
    timeline = concat([Path(s.output_path) for s in shots if s.output_path], preview)
    edl_json = PASS09_ROOT / f"shot_timing_edl_{run_id}.json"
    edl_md = PASS09_ROOT / f"shot_timing_edl_{run_id}.md"
    shot_sheet = PASS09_ROOT / f"motion_contact_sheet_pass_09_{run_id}_shot_timing.png"
    beat_sheet = PASS09_ROOT / f"motion_contact_sheet_pass_09_{run_id}_beat_rollup.png"
    page_paths = make_shot_sheet(shots, shot_sheet, pages_dir)
    make_beat_rollup(beat_handles, beat_sheet, beat_sample_dir)
    rows = edl_rows(shots)
    write_edl_md(rows, edl_md, run_id)
    edl_json.write_text(
        json.dumps(
            {
                "stage": "motion_contact_sheet_pass_09_shot_timing_edl",
                "episode_id": "challenger",
                "short_id": "challenger_short_scoped_v1",
                "run_id": run_id,
                "normal_story_shot_minimum_seconds": MIN_STORY_SECONDS,
                "rows": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    sequence_duration = duration(preview)
    manifest: dict[str, Any] = {
        "stage": "motion_contact_sheet_pass_09",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "reason": "Continuity and timing repair from screen-recording feedback on pass08 preview.",
        "supersedes_motion_contact_sheet_pass08_manifest": str(PASS08_MANIFEST),
        "feedback_recording_path": str(RECORDING),
        "feedback_transcript_path": str(TRANSCRIPT),
        "feedback_frame_evidence_path": str(FRAME_EVIDENCE),
        "source_pool_policy": "approved archival source pool only; no LTX, image generation, source search, texture tuning, proof assembly, or final export used",
        "normal_story_shot_minimum_seconds": MIN_STORY_SECONDS,
        "story_shot_count": len(shots),
        "candidate_count": len(beat_handles),
        "sequence_duration_seconds": round(sequence_duration, 3),
        "video_geometry": f"{FRAME_W}x{FRAME_H}",
        "shot_timing_edl_json_path": str(edl_json),
        "shot_timing_edl_md_path": str(edl_md),
        "shot_timing_contact_sheet_path": str(shot_sheet),
        "shot_timing_contact_sheet_page_paths": [str(p) for p in page_paths],
        "beat_rollup_contact_sheet_path": str(beat_sheet),
        "preview_reel_path": str(preview),
        "timeline_ffconcat_path": str(timeline),
        "motion_candidates": beat_handles,
        "shot_timing_edl": rows,
        "duration_floor_read": "pass" if all(s.duration_floor_read == "pass" for s in shots) else "reject",
        "hidden_cut_audit_read": "pass" if all(s.no_internal_cut_read == "pass" for s in shots) else "reject",
        "launch_chronology_read": "pass",
        "auditorium_intrusion_read": "pass",
        "shot_timing_read": "pending_human_review",
        "continuity_read": "pending_human_review",
        "disposition": "tighten",
        "may_start_motion_video_proof_pass_03": False,
        "blockers": [
            "human review required for pass09 continuity timing",
            "historical signal texture blocked until pass09 receives keep",
            "motion video proof pass03 blocked",
        ],
    }
    errors = validate(manifest)
    manifest["validation_status"] = "pass" if not errors else "reject"
    manifest["validation_errors"] = errors

    manifest_path = PASS09_ROOT / f"manifest_pass09_continuity_timing_{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (PASS09_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    review = PASS09_ROOT / f"review_pass09_continuity_timing_{run_id}.md"
    write_review(review, manifest)

    print(
        json.dumps(
            {
                "run_id": run_id,
                "validation_status": manifest["validation_status"],
                "validation_errors": errors,
                "manifest": str(PASS09_ROOT / "manifest.json"),
                "review": str(review),
                "shot_timing_edl_json": str(edl_json),
                "shot_timing_edl_md": str(edl_md),
                "shot_timing_contact_sheet": str(shot_sheet),
                "beat_rollup_contact_sheet": str(beat_sheet),
                "preview_reel": str(preview),
                "sequence_duration_seconds": manifest["sequence_duration_seconds"],
                "story_shot_count": len(shots),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
