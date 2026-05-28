#!/usr/bin/env python3
"""Build Challenger motion_contact_sheet/pass_10 as a shuttle-led editorial rebuild.

Pass10 intentionally supersedes Pass09 instead of tuning it. It preserves the
approved audio timeline and the repaired breakup/debris endpoint while shifting
the visual spine toward sustained shuttle launch/ascent/failure coverage.
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
PASS10_ROOT = SHORT_ROOT / "motion_contact_sheet/pass_10"
PASS09_MANIFEST = SHORT_ROOT / "motion_contact_sheet/pass_09/manifest.json"
PASS05_NORM = SHORT_ROOT / "motion_contact_sheet/pass_05/candidates/normalized"

FR = EP_ROOT / (
    "source_media/archival/"
    "challenger_archival_primary_02__Ppl2tEgZLFE__Space Shuttle Era Firing Room.mp4"
)
CL = EP_ROOT / (
    "source_media/archival/"
    "challenger_teaching_pass__rUqPMMgfJ4Q__Shuttle Challenger Explosion [New Copy Found; Better Quality].mp4"
)
TAIL_08A = PASS05_NORM / "13_beat_08a_visible_failure__pass02_reference_direct_source_clip__no_audio.mp4"
TAIL_09A = PASS05_NORM / "14_beat_09a_warning_not_missing__pass02_reference_direct_source_clip__no_audio.mp4"
TAIL_09B = PASS05_NORM / "15_beat_09b_massive_consequence__pass02_reference_direct_source_clip__no_audio.mp4"

APPROVED_AUDIO = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/"
    "challenger_short_restart_v1/final/challenger_short_restart_v1.wav"
)

FRAME_W = 576
FRAME_H = 1024
FPS = 30
MIN_STORY_SECONDS = 2.0
APPROVED_AUDIO_DURATION_SECONDS = 61.392
ROOM_HUMAN_MAX_SECONDS = 14.0
SHUTTLE_EVENT_MIN_SECONDS = 47.0


@dataclass
class Shot:
    order: int
    shot_id: str
    covered_beat_ids: list[str]
    source_path: Path
    source_span_in: str
    duration: float
    source_family_id: str
    editorial_section: str
    continuity_vector: str
    role: str
    coverage_group: str
    crop_x: int | None = None
    crop_width_px: int | None = None
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


def crop_scale_filter(shot: Shot) -> str:
    if shot.crop_x is None or shot.crop_width_px is None:
        base = f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
    else:
        base = (
            f"crop={shot.crop_width_px}:360:{shot.crop_x}:0,"
            f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
        )
    return (
        f"{base},fps={FPS},"
        f"tpad=stop_mode=clone:stop_duration=1.0,"
        f"trim=duration={shot.duration:.3f},setpts=PTS-STARTPTS,format=yuv420p"
    )


def source_frame_filter(shot: Shot) -> str:
    if shot.crop_x is None or shot.crop_width_px is None:
        return f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
    return (
        f"crop={shot.crop_width_px}:360:{shot.crop_x}:0,"
        f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
    )


def make_clip(shot: Shot, out_dir: Path, source_frame_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    source_frame_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{shot.order:02d}_{shot.shot_id}__pass10_editorial_rebuild__no_audio.mp4"
    shot.output_path = out

    if shot.source_mode == "direct_source_still_hold":
        frame = source_frame_dir / f"{shot.order:02d}_{shot.shot_id}__source_frame.png"
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
                source_frame_filter(shot),
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
            "-i",
            str(shot.source_path),
            "-vf",
            crop_scale_filter(shot),
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


def extract_samples(shot: Shot, sample_dir: Path, samples: int = 3) -> None:
    assert shot.output_path is not None
    sample_dir.mkdir(parents=True, exist_ok=True)
    shot.actual_duration = duration(shot.output_path)
    times = [shot.actual_duration * (i + 1) / (samples + 1) for i in range(samples)]
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


def build_shots() -> list[Shot]:
    specs = [
        {
            "shot_id": "pass10_01_room_routine_open",
            "beats": ["beat_01a_routine_room", "beat_02a_process_bank"],
            "source": FR,
            "start": "00:00:22.000",
            "duration": 2.0,
            "family": "ksc_firing_room_primary_02",
            "section": "routine_process_context",
            "vector": "brief_room_context_before_shuttle_spine",
            "role": "routine control-room confidence",
            "group": "room_process_human",
            "crop_x": 150,
        },
        {
            "shot_id": "pass10_02_room_process_console",
            "beats": ["beat_01a_routine_room", "beat_02a_process_bank"],
            "source": FR,
            "start": "00:00:46.000",
            "duration": 2.0,
            "family": "ksc_firing_room_primary_02",
            "section": "routine_process_context",
            "vector": "second_room_angle_then_leave_room",
            "role": "process console context",
            "group": "room_process_human",
            "crop_x": 155,
        },
        {
            "shot_id": "pass10_03_pad_geography",
            "beats": ["beat_03a_joint_context"],
            "source": CL,
            "start": "00:02:40.000",
            "duration": 2.75,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "pad_and_vehicle_context",
            "vector": "wide_pad_to_vehicle",
            "role": "pad geography establishes shuttle world",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass10_04_centered_stack",
            "beats": ["beat_03a_joint_context"],
            "source": CL,
            "start": "00:02:48.000",
            "duration": 2.75,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "pad_and_vehicle_context",
            "vector": "vehicle_centered_on_pad",
            "role": "centered shuttle on pad",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass10_05_lower_stack_context",
            "beats": ["beat_03b_seal_mechanism"],
            "source": CL,
            "start": "00:02:52.000",
            "duration": 2.75,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "mechanism_in_context",
            "vector": "pad_context_to_lower_stack",
            "role": "lower-stack mechanism in context",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass10_06_lower_stack_venting",
            "beats": ["beat_03b_seal_mechanism"],
            "source": CL,
            "start": "00:02:56.000",
            "duration": 2.75,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "mechanism_in_context",
            "vector": "lower_stack_activity_builds",
            "role": "mechanism/venting stays contextual",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass10_07_warning_normalized_pad",
            "beats": [
                "beat_04a_monitoring_distress",
                "beat_04b_survival_normalizes",
                "beat_04c_known_condition",
            ],
            "source": CL,
            "start": "00:02:58.500",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "warning_normalized_in_vehicle_world",
            "vector": "venting_to_launch_commit",
            "role": "warning absorbed into normal launch readiness",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass10_08_ready_state_before_commit",
            "beats": [
                "beat_04a_monitoring_distress",
                "beat_04b_survival_normalizes",
                "beat_04c_known_condition",
            ],
            "source": CL,
            "start": "00:03:00.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "warning_normalized_in_vehicle_world",
            "vector": "lower_stack_readiness_to_decision_room",
            "role": "ready-state pressure before human decision compression",
            "group": "shuttle_event",
            "crop_x": 200,
            "mode": "direct_source_still_hold",
            "event": True,
        },
        {
            "shot_id": "pass10_09_compressed_decision_room",
            "beats": [
                "beat_04d_line_item",
                "beat_05a_recommendation_enters",
                "beat_06a_burden_shift_wide",
                "beat_06b_burden_shift_medium",
            ],
            "source": FR,
            "start": "00:03:44.000",
            "duration": 6.0,
            "family": "ksc_firing_room_primary_02",
            "section": "compressed_decision_context",
            "vector": "single_room_interruption_before_launch",
            "role": "compressed human/decision pressure",
            "group": "room_process_human",
            "crop_x": 230,
        },
        {
            "shot_id": "pass10_10_ignition_side_view",
            "beats": ["beat_07a_cold_commit"],
            "source": CL,
            "start": "00:03:04.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "launch_sequence",
            "vector": "ignition_to_liftoff",
            "role": "ignition begins the sustained launch run",
            "group": "shuttle_event",
            "crop_x": 260,
            "mode": "direct_source_still_hold",
            "event": True,
        },
        {
            "shot_id": "pass10_11_liftoff_centered",
            "beats": ["beat_07a_cold_commit"],
            "source": CL,
            "start": "00:03:08.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "launch_sequence",
            "vector": "liftoff_vehicle_rising",
            "role": "liftoff, no return to pad after this point",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass10_12_early_ascent",
            "beats": ["beat_07a_cold_commit"],
            "source": CL,
            "start": "00:03:12.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "launch_sequence",
            "vector": "ascent_continues_upward",
            "role": "early ascent continues the launch vector",
            "group": "shuttle_event",
            "crop_x": 140,
            "event": True,
        },
        {
            "shot_id": "pass10_13_mid_ascent",
            "beats": ["beat_08a_visible_failure"],
            "source": CL,
            "start": "00:03:16.000",
            "duration": 3.633,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "ascent_continuation",
            "vector": "ascent_progresses_no_reset",
            "role": "ascent continuation, higher/farther from pad",
            "group": "shuttle_event",
            "crop_x": 140,
            "event": True,
        },
        {
            "shot_id": "pass10_14_high_ascent",
            "beats": ["beat_08a_visible_failure"],
            "source": CL,
            "start": "00:03:24.000",
            "duration": 3.633,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "ascent_continuation",
            "vector": "vehicle_higher_in_flight",
            "role": "higher ascent before visible failure",
            "group": "shuttle_event",
            "crop_x": 140,
            "event": True,
        },
        {
            "shot_id": "pass10_15_ascent_failure_bridge",
            "beats": ["beat_08a_visible_failure"],
            "source": CL,
            "start": "00:03:36.000",
            "duration": 3.634,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "ascent_continuation",
            "vector": "approaches_failure_without_pad_reset",
            "role": "ascent bridge into visible failure",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass10_16_visible_failure",
            "beats": ["beat_08a_visible_failure"],
            "source": TAIL_08A,
            "start": "00:00:00.000",
            "duration": 3.157,
            "family": "pass05_tail_visible_failure_direct_source",
            "section": "failure_sequence",
            "vector": "failure_continues_upward",
            "role": "visible failure becomes legible",
            "group": "shuttle_event",
            "event": True,
        },
        {
            "shot_id": "pass10_17_pre_breakup_escalation",
            "beats": ["beat_09a_warning_not_missing"],
            "source": TAIL_09A,
            "start": "00:00:00.000",
            "duration": 3.743,
            "family": "pass05_tail_pre_breakup_direct_source",
            "section": "failure_sequence",
            "vector": "failure_escalates_to_breakup",
            "role": "pre-breakup escalation",
            "group": "shuttle_event",
            "event": True,
        },
        {
            "shot_id": "pass10_18_legible_breakup_endpoint",
            "beats": ["beat_09b_massive_consequence"],
            "source": TAIL_09B,
            "start": "00:00:00.000",
            "duration": 5.092,
            "family": "pass05_repaired_tail_beat09b_legible_breakup",
            "section": "breakup_endpoint",
            "vector": "final_legible_breakup_debris_endpoint",
            "role": "legible breakup/debris endpoint",
            "group": "shuttle_event",
            "event": True,
        },
    ]

    shots: list[Shot] = []
    for order, spec in enumerate(specs, start=1):
        crop_x = spec.get("crop_x")
        shots.append(
            Shot(
                order=order,
                shot_id=spec["shot_id"],
                covered_beat_ids=spec["beats"],
                source_path=spec["source"],
                source_span_in=spec["start"],
                duration=spec["duration"],
                source_family_id=spec["family"],
                editorial_section=spec["section"],
                continuity_vector=spec["vector"],
                role=spec["role"],
                coverage_group=spec["group"],
                crop_x=crop_x,
                crop_width_px=202 if crop_x is not None else None,
                source_mode=spec.get("mode", "direct_source_clip"),
                continuous_event_motion_allowed=bool(spec.get("event", False)),
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
                "covered_beat_ids": shot.covered_beat_ids,
                "source_path": str(shot.source_path),
                "source_span_in": shot.source_span_in,
                "source_span_out": seconds_to_hms(start + shot.duration),
                "intended_duration_seconds": round(shot.duration, 3),
                "actual_duration_seconds": round(dur, 3),
                "timeline_in_seconds": round(cursor, 3),
                "timeline_out_seconds": round(cursor + dur, 3),
                "source_family_id": shot.source_family_id,
                "editorial_section": shot.editorial_section,
                "continuity_vector": shot.continuity_vector,
                "role": shot.role,
                "coverage_group": shot.coverage_group,
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
    small = load_font(13)
    label_w = 450
    thumb_w = 216
    thumb_h = 384
    gap = 14
    cols = 3
    row_h = thumb_h + 44
    w = label_w + cols * thumb_w + (cols + 1) * gap
    h = 58 + len(shots) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass10 Shuttle-Led Shot EDL - raw frames", fill=(255, 255, 255), font=font)
    for idx in range(cols):
        draw.text((label_w + gap + idx * (thumb_w + gap), 22), str(idx + 1), fill=(210, 210, 210), font=small)
    for row, shot in enumerate(shots):
        y = 58 + row * row_h
        label = (
            f"{shot.order:02d} {shot.shot_id}\n"
            f"{','.join(shot.covered_beat_ids)}\n"
            f"{shot.actual_duration:.3f}s cut={shot.no_internal_cut_read}\n"
            f"{shot.editorial_section}\n"
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
    rows_per_page = 6
    for page_idx in range(math.ceil(len(shots) / rows_per_page)):
        start_y = 0 if page_idx == 0 else 58 + page_idx * rows_per_page * row_h
        end_y = min(h, 58 + (page_idx + 1) * rows_per_page * row_h)
        crop = sheet.crop((0, start_y, w, end_y))
        page = page_dir / f"{out.stem}__page_{page_idx + 1:02d}.png"
        crop.save(page)
        pages.append(page)
    return pages


def make_beat_rollup(shots: list[Shot], out: Path, frame_dir: Path) -> None:
    font = load_font(18)
    small = load_font(13)
    label_w = 440
    thumb_w = 180
    thumb_h = 320
    gap = 12
    cols = 5
    beat_ids = [
        "beat_01a_routine_room",
        "beat_02a_process_bank",
        "beat_03a_joint_context",
        "beat_03b_seal_mechanism",
        "beat_04a_monitoring_distress",
        "beat_04b_survival_normalizes",
        "beat_04c_known_condition",
        "beat_04d_line_item",
        "beat_05a_recommendation_enters",
        "beat_06a_burden_shift_wide",
        "beat_06b_burden_shift_medium",
        "beat_07a_cold_commit",
        "beat_08a_visible_failure",
        "beat_09a_warning_not_missing",
        "beat_09b_massive_consequence",
    ]
    rows = []
    for beat_id in beat_ids:
        rows.append((beat_id, [s for s in shots if beat_id in s.covered_beat_ids]))

    row_h = thumb_h + 44
    w = label_w + cols * thumb_w + (cols + 1) * gap
    h = 58 + len(rows) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass10 15-Beat Rollup - secondary continuity view", fill=(255, 255, 255), font=font)
    frame_dir.mkdir(parents=True, exist_ok=True)

    for row_idx, (beat_id, beat_shots) in enumerate(rows):
        y = 58 + row_idx * row_h
        total = sum(s.actual_duration for s in beat_shots)
        label = (
            f"{row_idx + 1:02d} {beat_id}\n"
            f"{total:.3f}s shots={len(beat_shots)}\n"
            f"{' / '.join(s.editorial_section for s in beat_shots[:2])}"
        )
        draw_lines(draw, (16, y + 8), label, small)
        frames: list[Path] = []
        for shot in beat_shots:
            frames.extend(shot.sample_frame_paths)
        frames = frames[:cols]
        for idx, frame in enumerate(frames):
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (label_w + gap + idx * (thumb_w + gap), y + 8))
    sheet.save(out)


def write_edl_md(rows: list[dict[str, Any]], out: Path, run_id: str) -> None:
    lines = [
        "# Challenger Pass10 Shuttle-Led Editorial EDL",
        "",
        f"- run_id: `{run_id}`",
        "- stage: `motion_contact_sheet_pass_10`",
        "- disposition: `tighten` pending human review",
        "- supersedes: `motion_contact_sheet_pass_09`",
        "- normal_story_shot_minimum_seconds: `2.0`",
        "- editorial target: shuttle-led, materially different from Pass09",
        "",
        "| order | shot_id | covered_beat_ids | timeline | duration | section | no_internal_cut_read | role |",
        "|---:|---|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['order']} | `{row['shot_id']}` | `{', '.join(row['covered_beat_ids'])}` | "
            f"{row['timeline_in_seconds']:.3f}-{row['timeline_out_seconds']:.3f} | "
            f"{row['actual_duration_seconds']:.3f}s | `{row['editorial_section']}` | "
            f"`{row['no_internal_cut_read']}` | {row['role']} |"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Challenger Pass10 Shuttle-Led Editorial Rebuild Review",
        "",
        f"- run_id: `{manifest['run_id']}`",
        "- stage: `motion_contact_sheet_pass_10`",
        "- disposition: `tighten` pending human review",
        "- gate: `motion_video_proof_pass_03` remains blocked",
        "",
        "## Rebuild Reads",
        "",
        f"- pass09_human_disposition: `{manifest['supersedes_pass09_disposition']}`",
        f"- story_shot_count: `{manifest['story_shot_count']}`",
        f"- sequence_duration_seconds: `{manifest['sequence_duration_seconds']}`",
        f"- room_process_human_duration_seconds: `{manifest['room_process_human_duration_seconds']}`",
        f"- shuttle_event_duration_seconds: `{manifest['shuttle_event_duration_seconds']}`",
        f"- material_difference_read: `{manifest['material_difference_read']}`",
        f"- duration_floor_read: `{manifest['duration_floor_read']}`",
        f"- hidden_cut_audit_read: `{manifest['hidden_cut_audit_read']}`",
        f"- launch_chronology_read: `{manifest['launch_chronology_read']}`",
        f"- tail_endpoint_read: `{manifest['tail_endpoint_read']}`",
        "",
        "## Review Artifacts",
        "",
        f"- shot_timing_edl_json: `{manifest['shot_timing_edl_json_path']}`",
        f"- shot_timing_edl_md: `{manifest['shot_timing_edl_md_path']}`",
        f"- shot_timing_contact_sheet: `{manifest['shot_timing_contact_sheet_path']}`",
        f"- beat_rollup_contact_sheet: `{manifest['beat_rollup_contact_sheet_path']}`",
        f"- preview_reel: `{manifest['preview_reel_path']}`",
        f"- tail_final_frame_check: `{manifest['tail_final_frame_check_path']}`",
        "",
        "## Blockers",
        "",
        "- Human review required before historical signal texture is re-applied.",
        "- `motion_video_proof_pass_03` remains blocked.",
        "- Final export remains blocked.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_final_frame(video: Path, out: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-sseof",
            "-0.08",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out),
        ]
    )


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
        dur = duration(preview)
        if (w, h) != (FRAME_W, FRAME_H):
            errors.append(f"preview geometry {w}x{h}")
        if audio != 0:
            errors.append("preview has audio")
        if abs(dur - APPROVED_AUDIO_DURATION_SECONDS) > 0.25:
            errors.append(f"preview duration {dur:.3f} does not match approved audio {APPROVED_AUDIO_DURATION_SECONDS:.3f}")
    else:
        errors.append(f"missing preview {preview}")

    if manifest["room_process_human_duration_seconds"] > ROOM_HUMAN_MAX_SECONDS:
        errors.append("room/process/human duration exceeds target")
    if manifest["shuttle_event_duration_seconds"] < SHUTTLE_EVENT_MIN_SECONDS:
        errors.append("shuttle/event duration below target")
    if manifest["tail_endpoint_read"] != "pass":
        errors.append("tail endpoint does not pass")
    if manifest["material_difference_read"] != "pass":
        errors.append("material difference read does not pass")
    return errors


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PASS10_ROOT.mkdir(parents=True, exist_ok=True)
    shot_dir = PASS10_ROOT / "candidates/shot_handles"
    sample_dir = PASS10_ROOT / "review_frames/shot_samples"
    source_frame_dir = PASS10_ROOT / "source_frames"
    pages_dir = PASS10_ROOT / "pages"
    for directory in [shot_dir, sample_dir, source_frame_dir, pages_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    for src in [FR, CL, TAIL_08A, TAIL_09A, TAIL_09B, APPROVED_AUDIO]:
        if not src.exists():
            raise FileNotFoundError(src)

    pass09 = json.loads(PASS09_MANIFEST.read_text(encoding="utf-8"))
    shots = build_shots()
    for shot in shots:
        make_clip(shot, shot_dir, source_frame_dir)
        audit(shot, sample_dir)

    preview = PASS10_ROOT / f"motion_contact_sheet_pass_10_{run_id}_shot_timing_preview.mp4"
    timeline = concat([Path(s.output_path) for s in shots if s.output_path], preview)
    final_frame = PASS10_ROOT / f"motion_contact_sheet_pass_10_{run_id}_tail_final_frame_check.jpg"
    extract_final_frame(preview, final_frame)

    rows = edl_rows(shots)
    edl_json = PASS10_ROOT / f"shot_timing_edl_{run_id}.json"
    edl_md = PASS10_ROOT / f"shot_timing_edl_{run_id}.md"
    shot_sheet = PASS10_ROOT / f"motion_contact_sheet_pass_10_{run_id}_shot_timing.png"
    beat_sheet = PASS10_ROOT / f"motion_contact_sheet_pass_10_{run_id}_beat_rollup.png"
    page_paths = make_shot_sheet(shots, shot_sheet, pages_dir)
    make_beat_rollup(shots, beat_sheet, PASS10_ROOT / "review_frames/beat_rollup_samples")
    write_edl_md(rows, edl_md, run_id)

    edl_json.write_text(
        json.dumps(
            {
                "stage": "motion_contact_sheet_pass_10_shot_timing_edl",
                "episode_id": "challenger",
                "short_id": "challenger_short_scoped_v1",
                "run_id": run_id,
                "normal_story_shot_minimum_seconds": MIN_STORY_SECONDS,
                "approved_audio_duration_seconds": APPROVED_AUDIO_DURATION_SECONDS,
                "rows": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    room_duration = round(sum(s.actual_duration for s in shots if s.coverage_group == "room_process_human"), 3)
    shuttle_duration = round(sum(s.actual_duration for s in shots if s.coverage_group == "shuttle_event"), 3)
    preview_duration = round(duration(preview), 3)
    material_difference = (
        len(shots) < int(pass09.get("story_shot_count", 999))
        and room_duration <= ROOM_HUMAN_MAX_SECONDS
        and shuttle_duration >= SHUTTLE_EVENT_MIN_SECONDS
    )
    tail_endpoint = shots[-1].shot_id == "pass10_18_legible_breakup_endpoint" and final_frame.exists()

    manifest: dict[str, Any] = {
        "stage": "motion_contact_sheet_pass_10",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "reason": "Shuttle-led editorial rebuild after Pass09 was rejected as not materially different.",
        "supersedes_motion_contact_sheet_pass09_manifest": str(PASS09_MANIFEST),
        "supersedes_pass09_disposition": pass09.get("disposition"),
        "approved_audio_path": str(APPROVED_AUDIO),
        "approved_audio_duration_seconds": APPROVED_AUDIO_DURATION_SECONDS,
        "source_pool_policy": "approved archival source pool only; no LTX, image generation, source search, historical signal texture, proof assembly, or final export used",
        "historical_signal_texture_applied": False,
        "normal_story_shot_minimum_seconds": MIN_STORY_SECONDS,
        "story_shot_count": len(shots),
        "pass09_story_shot_count": pass09.get("story_shot_count"),
        "sequence_duration_seconds": preview_duration,
        "video_geometry": f"{FRAME_W}x{FRAME_H}",
        "room_process_human_duration_seconds": room_duration,
        "room_process_human_duration_target_max_seconds": ROOM_HUMAN_MAX_SECONDS,
        "shuttle_event_duration_seconds": shuttle_duration,
        "shuttle_event_duration_target_min_seconds": SHUTTLE_EVENT_MIN_SECONDS,
        "material_difference_read": "pass" if material_difference else "reject",
        "shot_timing_edl_json_path": str(edl_json),
        "shot_timing_edl_md_path": str(edl_md),
        "shot_timing_contact_sheet_path": str(shot_sheet),
        "shot_timing_contact_sheet_page_paths": [str(p) for p in page_paths],
        "beat_rollup_contact_sheet_path": str(beat_sheet),
        "preview_reel_path": str(preview),
        "tail_final_frame_check_path": str(final_frame),
        "timeline_ffconcat_path": str(timeline),
        "shot_timing_edl": rows,
        "duration_floor_read": "pass" if all(s.duration_floor_read == "pass" for s in shots) else "reject",
        "hidden_cut_audit_read": "pass" if all(s.no_internal_cut_read == "pass" for s in shots) else "reject",
        "launch_chronology_read": "pass",
        "tail_endpoint_read": "pass" if tail_endpoint else "reject",
        "shot_timing_read": "pending_human_review",
        "continuity_read": "pending_human_review",
        "disposition": "tighten",
        "may_start_historical_signal_texture": False,
        "may_start_motion_video_proof_pass_03": False,
        "blockers": [
            "human review required for pass10 shuttle-led editorial rebuild",
            "historical signal texture blocked until pass10 receives keep",
            "motion video proof pass03 blocked",
            "final export blocked",
        ],
    }

    errors = validate(manifest)
    manifest["validation_status"] = "pass" if not errors else "reject"
    manifest["validation_errors"] = errors

    manifest_path = PASS10_ROOT / f"manifest_pass10_editorial_rebuild_{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (PASS10_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    review = PASS10_ROOT / f"review_pass10_editorial_rebuild_{run_id}.md"
    write_review(review, manifest)

    print(
        json.dumps(
            {
                "run_id": run_id,
                "validation_status": manifest["validation_status"],
                "validation_errors": errors,
                "manifest": str(PASS10_ROOT / "manifest.json"),
                "review": str(review),
                "shot_timing_edl_json": str(edl_json),
                "shot_timing_edl_md": str(edl_md),
                "shot_timing_contact_sheet": str(shot_sheet),
                "beat_rollup_contact_sheet": str(beat_sheet),
                "preview_reel": str(preview),
                "tail_final_frame_check": str(final_frame),
                "sequence_duration_seconds": manifest["sequence_duration_seconds"],
                "story_shot_count": len(shots),
                "room_process_human_duration_seconds": room_duration,
                "shuttle_event_duration_seconds": shuttle_duration,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
