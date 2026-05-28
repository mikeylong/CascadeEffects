#!/usr/bin/env python3
"""Build Challenger motion_contact_sheet/pass_08 from an explicit shot EDL.

This is intentionally production-specific. Pass08 repairs cadence at the
story-shot level and does not reopen LTX, source search, texture, proof, or
final export.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
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
PASS08_ROOT = SHORT_ROOT / "motion_contact_sheet/pass_08"
PASS07_MANIFEST = SHORT_ROOT / "motion_contact_sheet/pass_07/manifest.json"
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

FRAME_W = 576
FRAME_H = 1024
FPS = 30
STORY_MIN_SECONDS = 2.0


@dataclass
class ShotSpec:
    order: int
    shot_id: str
    parent_beat_id: str
    beat_order: int
    role: str
    source_path: Path
    source_span_in: str
    intended_duration_seconds: float
    crop_x: int | None = 220
    crop_width_px: int | None = 202
    source_mode: str = "direct_source_clip"
    framing_note: str = "full-bleed 9:16 source crop"
    continuous_event_motion_allowed: bool = False
    avoid_hidden_cut_note: str = "source span selected as one declared story shot"
    output_path: Path | None = None
    frame_paths: list[Path] = field(default_factory=list)
    actual_duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    audio_stream_count: int | None = None
    scene_cut_times: list[float] = field(default_factory=list)
    frame_diff_cut_candidates: list[float] = field(default_factory=list)
    no_internal_cut_read: str = "pending"
    duration_floor_read: str = "pending"


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    if capture:
        return subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return subprocess.run(cmd, check=True, text=True)


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


def duration_seconds(path: Path) -> float:
    data = ffprobe_json(path)
    return float(data["format"]["duration"])


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
    if value == "existing_selected_handle":
        return 0.0
    parts = value.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(value)


def seconds_to_hms(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_")


def crop_filter(shot: ShotSpec) -> str:
    if shot.crop_x is None or shot.crop_width_px is None:
        return f"scale={FRAME_W}:{FRAME_H}:flags=lanczos,fps={FPS},format=yuv420p"
    return (
        f"crop={shot.crop_width_px}:360:{shot.crop_x}:0,"
        f"scale={FRAME_W}:{FRAME_H}:flags=lanczos,fps={FPS},format=yuv420p"
    )


def make_clip(shot: ShotSpec, out_dir: Path, frame_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{shot.order:02d}_{shot.shot_id}__pass08_shot_timing__no_audio.mp4"
    shot.output_path = out_path

    if shot.source_mode == "existing_no_audio_handle":
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(shot.source_path),
                "-t",
                f"{shot.intended_duration_seconds:.3f}",
                "-vf",
                f"scale={FRAME_W}:{FRAME_H}:flags=lanczos,fps={FPS},format=yuv420p",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-movflags",
                "+faststart",
                str(out_path),
            ]
        )
    elif shot.source_mode == "direct_source_still_hold":
        frame_path = frame_dir / f"{shot.order:02d}_{shot.shot_id}__source_frame.png"
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
                crop_filter(shot).replace(f",fps={FPS},format=yuv420p", ""),
                str(frame_path),
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
                f"{shot.intended_duration_seconds:.3f}",
                "-i",
                str(frame_path),
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
                str(out_path),
            ]
        )
    else:
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
                f"{shot.intended_duration_seconds:.3f}",
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
                str(out_path),
            ]
        )

    shot.actual_duration_seconds = duration_seconds(out_path)
    shot.width, shot.height, shot.audio_stream_count = video_meta(out_path)
    shot.duration_floor_read = (
        "pass" if shot.actual_duration_seconds + 0.001 >= STORY_MIN_SECONDS else "reject"
    )


def detect_scene_cuts(path: Path, duration: float) -> list[float]:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-vf",
            "select='gt(scene,0.35)',showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    cuts: list[float] = []
    for line in proc.stderr.splitlines():
        match = re.search(r"pts_time:([0-9.]+)", line)
        if not match:
            continue
        t = float(match.group(1))
        if 0.20 < t < duration - 0.20:
            cuts.append(round(t, 3))
    return cuts


def extract_sample_frames(shot: ShotSpec, out_dir: Path, sample_count: int = 3) -> None:
    assert shot.output_path is not None
    dur = shot.actual_duration_seconds or duration_seconds(shot.output_path)
    times = [dur * (i + 1) / (sample_count + 1) for i in range(sample_count)]
    shot.frame_paths = []
    for idx, t in enumerate(times, start=1):
        frame_path = out_dir / f"{shot.order:02d}_{shot.shot_id}_sample_{idx}.jpg"
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
                str(frame_path),
            ]
        )
        shot.frame_paths.append(frame_path)


def frame_diff_candidates(frame_paths: list[Path]) -> list[float]:
    # The contact-sheet samples are sparse by design; dense scene detection above
    # is the authoritative hidden-cut audit. This lightweight diff is included
    # only as a sanity signal in the manifest.
    if len(frame_paths) < 2:
        return []
    values: list[float] = []
    prev = Image.open(frame_paths[0]).convert("L").resize((48, 85))
    for path in frame_paths[1:]:
        cur = Image.open(path).convert("L").resize((48, 85))
        diff = 0
        pix_prev = prev.load()
        pix_cur = cur.load()
        for y in range(cur.height):
            for x in range(cur.width):
                diff += abs(pix_cur[x, y] - pix_prev[x, y])
        values.append(diff / (cur.width * cur.height))
        prev = cur
    # Sparse frame differences above 45 usually indicate an obvious hidden
    # source cut in these low-res 1980s sources. This deliberately errs toward
    # rejecting the span so the contact sheet exposes actual story shots.
    return [round(v, 2) for v in values if v >= 45.0]


def audit_shot(shot: ShotSpec, sample_dir: Path) -> None:
    assert shot.output_path is not None
    shot.scene_cut_times = detect_scene_cuts(shot.output_path, shot.actual_duration_seconds or 0.0)
    extract_sample_frames(shot, sample_dir, sample_count=3)
    shot.frame_diff_cut_candidates = frame_diff_candidates(shot.frame_paths)
    if shot.source_mode == "direct_source_still_hold":
        shot.no_internal_cut_read = "pass"
    elif shot.scene_cut_times or (
        shot.frame_diff_cut_candidates and not shot.continuous_event_motion_allowed
    ):
        shot.no_internal_cut_read = "reject"
    else:
        shot.no_internal_cut_read = "pass"


def concat_clips(paths: list[Path], out_path: Path) -> None:
    concat_path = out_path.with_suffix(".ffconcat")
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
            str(out_path),
        ]
    )


def load_font(size: int) -> ImageFont.ImageFont:
    for candidate in [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_multiline(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont) -> None:
    x, y = xy
    for line in text.split("\n"):
        draw.text((x, y), line, fill=(235, 235, 235), font=font)
        y += int(font.size * 1.35) if hasattr(font, "size") else 14


def make_shot_contact_sheet(shots: list[ShotSpec], out_path: Path, page_dir: Path) -> list[Path]:
    font = load_font(18)
    small = load_font(14)
    label_w = 400
    thumb_w = 216
    thumb_h = 384
    gap = 14
    row_h = thumb_h + 38
    cols = 3
    sheet_w = label_w + cols * thumb_w + (cols + 1) * gap
    sheet_h = 58 + len(shots) * row_h
    sheet = Image.new("RGB", (sheet_w, sheet_h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass08 Shot Timing EDL Sheet - raw frames, shot-level timing", fill=(255, 255, 255), font=font)
    draw.text((label_w + gap, 20), "1", fill=(210, 210, 210), font=small)
    draw.text((label_w + gap + thumb_w + gap, 20), "2", fill=(210, 210, 210), font=small)
    draw.text((label_w + gap + 2 * (thumb_w + gap), 20), "3", fill=(210, 210, 210), font=small)
    for row, shot in enumerate(shots):
        y = 58 + row * row_h
        label = (
            f"{shot.order:02d} {shot.shot_id}\n"
            f"{shot.parent_beat_id}\n"
            f"{shot.actual_duration_seconds:.3f}s  cut={shot.no_internal_cut_read}\n"
            f"{shot.role}"
        )
        draw_multiline(draw, (16, y + 8), label, small)
        for idx, frame in enumerate(shot.frame_paths):
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            x = label_w + gap + idx * (thumb_w + gap)
            sheet.paste(im, (x, y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)

    page_dir.mkdir(parents=True, exist_ok=True)
    page_paths: list[Path] = []
    rows_per_page = 8
    page_count = math.ceil(len(shots) / rows_per_page)
    for page in range(page_count):
        start = 58 + page * rows_per_page * row_h
        end = min(sheet_h, 58 + (page + 1) * rows_per_page * row_h)
        crop = sheet.crop((0, 0 if page == 0 else start - 58, sheet_w, end))
        page_path = page_dir / f"{out_path.stem}__page_{page + 1:02d}.png"
        crop.save(page_path)
        page_paths.append(page_path)
    return page_paths


def make_beat_rollup(
    beat_handles: list[dict[str, Any]],
    out_path: Path,
    frame_dir: Path,
) -> None:
    font = load_font(18)
    small = load_font(14)
    label_w = 440
    thumb_w = 180
    thumb_h = 320
    gap = 12
    cols = 5
    row_h = thumb_h + 38
    sheet_w = label_w + cols * thumb_w + (cols + 1) * gap
    sheet_h = 58 + len(beat_handles) * row_h
    sheet = Image.new("RGB", (sheet_w, sheet_h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass08 15-Beat Rollup - secondary continuity view", fill=(255, 255, 255), font=font)
    for i in range(cols):
        draw.text((label_w + gap + i * (thumb_w + gap), 20), str(i + 1), fill=(210, 210, 210), font=small)

    frame_dir.mkdir(parents=True, exist_ok=True)
    for row, beat in enumerate(beat_handles):
        path = Path(beat["normalized_clip_path"])
        dur = float(beat["duration_seconds"])
        y = 58 + row * row_h
        label = (
            f"{beat['order']:02d} {beat['beat_id']}\n"
            f"{dur:.3f}s  shots={len(beat['shot_ids'])}\n"
            f"min_shot={beat['min_story_shot_seconds']:.3f}s\n"
            "secondary continuity view"
        )
        draw_multiline(draw, (16, y + 8), label, small)
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
            x = label_w + gap + idx * (thumb_w + gap)
            sheet.paste(im, (x, y + 8))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def shot_specs() -> list[ShotSpec]:
    specs = [
        # Routine/process
        ("beat_01a_routine_room", "fr_room_wide", "routine room scale", FR, "00:00:13.000", 2.5, 150, "direct_source_clip"),
        ("beat_01a_routine_room", "fr_console_row", "routine console rhythm", FR, "00:01:15.000", 2.5, 150, "direct_source_clip"),
        ("beat_02a_process_bank", "fr_operator_process", "operator process readable hold", FR, "00:01:31.000", 2.5, 95, "direct_source_clip"),
        ("beat_02a_process_bank", "fr_monitor_wall", "banked monitoring screens", FR, "00:00:47.000", 2.5, 155, "direct_source_clip"),
        # Hardware and normalized launches
        ("beat_03a_joint_context", "stack_side_source_hold", "centered shuttle/pad context source frame", CL, "00:01:08.000", 2.5, 220, "direct_source_still_hold"),
        ("beat_03a_joint_context", "stack_pad_wide", "pad-scale hardware context", CL, "00:02:45.000", 2.5, 220, "direct_source_clip"),
        ("beat_03b_seal_mechanism", "lower_stack_pre_ignition", "brief contextual mechanism area", CL, "00:02:52.000", 3.0, 220, "direct_source_clip"),
        ("beat_03b_seal_mechanism", "lower_stack_smoke", "mechanism context with ignition evidence", CL, "00:03:00.000", 2.0, 220, "direct_source_still_hold"),
        ("beat_04a_monitoring_distress", "fr_room_rear_monitors", "monitoring room continuity", FR, "00:01:45.000", 2.5, 115, "direct_source_clip"),
        ("beat_04a_monitoring_distress", "fr_operator_terminal", "process absorbed at console", FR, "00:03:07.000", 2.5, 110, "direct_source_clip"),
        ("beat_04b_survival_normalizes", "routine_liftoff_angle_a", "routine launch from one angle", CL, "00:03:08.000", 2.5, 220, "direct_source_clip"),
        ("beat_04b_survival_normalizes", "routine_ascent_angle_a", "routine ascent continuation", CL, "00:03:17.000", 2.5, 220, "direct_source_clip"),
        ("beat_04c_known_condition", "routine_ascent_angle_b", "second launch/ascent angle", CL, "00:03:20.000", 2.5, 220, "direct_source_clip"),
        ("beat_04c_known_condition", "routine_ascent_angle_c", "third launch/ascent angle", CL, "00:03:28.000", 2.5, 220, "direct_source_clip"),
        ("beat_04d_line_item", "routine_high_ascent", "normalized launch becomes line item", CL, "00:03:36.000", 2.5, 220, "direct_source_clip"),
        ("beat_04d_line_item", "routine_high_ascent_close", "normalized ascent pressure", CL, "00:03:44.000", 2.5, 220, "direct_source_clip"),
        # Decision/burden
        ("beat_05a_recommendation_enters", "fr_decision_room_wide", "decision space before recommendation", FR, "00:03:17.000", 2.6, 70, "direct_source_clip"),
        ("beat_05a_recommendation_enters", "fr_decision_handoff", "recommendation enters room", FR, "00:03:57.000", 2.6, 230, "direct_source_clip"),
        ("beat_06a_burden_shift_wide", "commission_room_wide", "wide institutional burden shift", RC, "00:00:38.000", 2.5, 125, "direct_source_clip"),
        ("beat_06a_burden_shift_wide", "commission_group_table", "group table burden shift", RC, "00:03:58.000", 2.5, 80, "direct_source_clip"),
        ("beat_06b_burden_shift_medium", "commission_panel_group", "medium group decision pressure", RC, "00:04:18.000", 2.5, 78, "direct_source_clip"),
        ("beat_06b_burden_shift_medium", "commission_cross_table", "cross-table response", RC, "00:05:38.000", 2.5, 78, "direct_source_clip"),
        # Commit and failure tail
        ("beat_07a_cold_commit", "final_pad_threshold", "actual launch pad threshold", CL, "00:02:45.000", 2.0, 220, "direct_source_clip"),
        ("beat_07a_cold_commit", "final_ignition_threshold", "actual ignition threshold", CL, "00:03:00.000", 2.0, 220, "direct_source_still_hold"),
        ("beat_07a_cold_commit", "final_liftoff_handoff", "liftoff handoff to ascent", CL, "00:03:12.000", 2.0, 220, "direct_source_clip"),
    ]
    beat_order = {
        "beat_01a_routine_room": 1,
        "beat_02a_process_bank": 2,
        "beat_03a_joint_context": 3,
        "beat_03b_seal_mechanism": 4,
        "beat_04a_monitoring_distress": 5,
        "beat_04b_survival_normalizes": 6,
        "beat_04c_known_condition": 7,
        "beat_04d_line_item": 8,
        "beat_05a_recommendation_enters": 9,
        "beat_06a_burden_shift_wide": 10,
        "beat_06b_burden_shift_medium": 11,
        "beat_07a_cold_commit": 12,
        "beat_08a_visible_failure": 13,
        "beat_09a_warning_not_missing": 14,
        "beat_09b_massive_consequence": 15,
    }
    shots: list[ShotSpec] = []
    for idx, item in enumerate(specs, start=1):
        beat, suffix, role, source, start, dur, crop_x, mode = item
        shots.append(
            ShotSpec(
                order=idx,
                shot_id=f"{beat}__{suffix}",
                parent_beat_id=beat,
                beat_order=beat_order[beat],
                role=role,
                source_path=source,
                source_span_in=start,
                intended_duration_seconds=dur,
                crop_x=crop_x,
                crop_width_px=202,
                source_mode=mode,
                continuous_event_motion_allowed=beat.startswith("beat_04") or beat.startswith("beat_07"),
            )
        )
    tail_specs = [
        ("beat_08a_visible_failure", "approved_tail_visible_failure", "approved continuous visible-failure event tail", TAIL_08A, "existing_selected_handle", 5.0, "existing_no_audio_handle"),
        ("beat_09a_warning_not_missing", "approved_tail_pre_breakup", "approved continuous pre-breakup escalation", TAIL_09A, "existing_selected_handle", 5.0, "existing_no_audio_handle"),
        ("beat_09b_massive_consequence", "breakup_close_plume", "explicit breakup burst close source shot", TAIL_09B, "00:00:00.000", 2.5, "direct_source_clip"),
        ("beat_09b_massive_consequence", "debris_close_progression", "explicit close debris/plume progression", TAIL_09B, "00:00:02.500", 2.0, "direct_source_clip"),
        ("beat_09b_massive_consequence", "legible_debris_endpoint_hold", "held legible breakup/debris endpoint", TAIL_09B, "00:00:04.600", 2.0, "direct_source_still_hold"),
    ]
    for beat, suffix, role, source, source_in, dur, mode in tail_specs:
        idx = len(shots) + 1
        shots.append(
            ShotSpec(
                order=idx,
                shot_id=f"{beat}__{suffix}",
                parent_beat_id=beat,
                beat_order=beat_order[beat],
                role=role,
                source_path=source,
                source_span_in=source_in,
                intended_duration_seconds=dur,
                crop_x=None,
                crop_width_px=None,
                source_mode=mode,
                framing_note="preserved approved pass05 tail handle",
                continuous_event_motion_allowed=True,
                avoid_hidden_cut_note="pass05 tail handle split into explicit EDL shots where the source-native breakup angle changes",
            )
        )
    return shots


def edl_rows(shots: list[ShotSpec]) -> list[dict[str, Any]]:
    rows = []
    timeline_cursor = 0.0
    for shot in shots:
        actual = float(shot.actual_duration_seconds or shot.intended_duration_seconds)
        src_start = hms_to_seconds(shot.source_span_in)
        source_span_out = (
            "existing_selected_handle"
            if shot.source_span_in == "existing_selected_handle"
            else seconds_to_hms(src_start + shot.intended_duration_seconds)
        )
        rows.append(
            {
                "order": shot.order,
                "shot_id": shot.shot_id,
                "parent_beat_id": shot.parent_beat_id,
                "beat_order": shot.beat_order,
                "source_path": str(shot.source_path),
                "source_span_in": shot.source_span_in,
                "source_span_out": source_span_out,
                "intended_duration_seconds": round(shot.intended_duration_seconds, 3),
                "actual_duration_seconds": round(actual, 3),
                "timeline_in_seconds": round(timeline_cursor, 3),
                "timeline_out_seconds": round(timeline_cursor + actual, 3),
                "source_mode": shot.source_mode,
                "crop_x": shot.crop_x,
                "crop_width_px": shot.crop_width_px,
                "framing_note": shot.framing_note,
                "role": shot.role,
                "output_path": str(shot.output_path),
                "sample_frame_paths": [str(p) for p in shot.frame_paths],
                "duration_floor_read": shot.duration_floor_read,
                "scene_cut_times": shot.scene_cut_times,
                "frame_diff_cut_candidates": shot.frame_diff_cut_candidates,
                "no_internal_cut_read": shot.no_internal_cut_read,
                "continuous_event_motion_allowed": shot.continuous_event_motion_allowed,
                "avoid_hidden_cut_note": shot.avoid_hidden_cut_note,
            }
        )
        timeline_cursor += actual
    return rows


def write_edl_md(rows: list[dict[str, Any]], path: Path, run_id: str) -> None:
    lines = [
        f"# Challenger Pass08 Shot Timing EDL",
        "",
        f"- run_id: `{run_id}`",
        "- stage: `motion_contact_sheet_pass_08`",
        "- disposition: `tighten` pending human review",
        "- supersedes: `motion_contact_sheet_pass_07`",
        "- normal_story_shot_minimum_seconds: `2.0`",
        "- implementation: source spans only from approved archival pool; no LTX, no image generation, no source search, no historical texture, no proof assembly",
        "",
        "| order | shot_id | parent_beat_id | duration | source_in | source_out | no_internal_cut_read | role |",
        "|---:|---|---|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {order} | `{shot_id}` | `{parent_beat_id}` | {actual_duration_seconds:.3f}s | `{source_span_in}` | `{source_span_out}` | `{no_internal_cut_read}` | {role} |".format(
                **row
            )
        )
    lines.append("")
    lines.append("## Gate")
    lines.append("")
    lines.append("- `motion_video_proof_pass_03`: blocked until pass08 is reviewed as `keep`.")
    lines.append("- Historical signal texture: blocked until pass08 timing is approved.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_manifest(
    run_id: str,
    shots: list[ShotSpec],
    beat_handles: list[dict[str, Any]],
    paths: dict[str, Path],
) -> dict[str, Any]:
    rejects = [
        s.shot_id
        for s in shots
        if s.duration_floor_read != "pass" or s.no_internal_cut_read != "pass"
    ]
    return {
        "stage": "motion_contact_sheet_pass_08",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "reason": "Shot-level timing repair after pass07 showed declared segment durations were not reliable actual story-shot durations.",
        "supersedes_motion_contact_sheet_pass07_manifest": str(PASS07_MANIFEST),
        "source_pool_policy": "approved archival source pool only; no LTX, image generation, source search, historical texture tuning, proof assembly, or final export used",
        "normal_story_shot_minimum_seconds": STORY_MIN_SECONDS,
        "source_native_edits_policy": "source-native cuts are real story cuts; every declared story shot is audited for hidden scene cuts",
        "shot_timing_edl_json_path": str(paths["edl_json"]),
        "shot_timing_edl_md_path": str(paths["edl_md"]),
        "shot_timing_contact_sheet_path": str(paths["shot_sheet"]),
        "shot_timing_contact_sheet_page_paths": [str(p) for p in paths["shot_sheet_pages"]],
        "beat_rollup_contact_sheet_path": str(paths["beat_sheet"]),
        "preview_reel_path": str(paths["preview"]),
        "timeline_ffconcat_path": str(paths["timeline"]),
        "candidate_count": len(beat_handles),
        "story_shot_count": len(shots),
        "completed_candidate_count": len(beat_handles),
        "render_completion_status": "complete",
        "video_geometry": f"{FRAME_W}x{FRAME_H}",
        "audio_stream_read": "pass",
        "duration_floor_read": "pass" if not any(s.duration_floor_read != "pass" for s in shots) else "reject",
        "hidden_cut_audit_read": "pass" if not any(s.no_internal_cut_read != "pass" for s in shots) else "reject",
        "shot_timing_read": "pending_human_review",
        "continuity_read": "pending_human_review",
        "repetition_read": "pending_human_review",
        "historical_signal_texture_status": "blocked until pass08 receives keep; not applied in this pass",
        "motion_video_proof_pass_03_status": "blocked until pass08 receives keep",
        "disposition": "tighten",
        "may_start_motion_video_proof_pass_03": False,
        "blockers": [
            "human review required for shot-level timing EDL and contact sheet",
            "historical signal texture must be re-applied only after pass08 timing is approved",
            "motion video proof pass03 remains blocked",
        ],
        "rejected_declared_shots": rejects,
        "motion_candidates": beat_handles,
        "shot_timing_edl": edl_rows(shots),
    }


def write_review(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Challenger Pass08 Shot-Timing Repair Review",
        "",
        f"- run_id: `{manifest['run_id']}`",
        "- stage: `motion_contact_sheet_pass_08`",
        "- disposition: `tighten` pending human review",
        "- gate: `motion_video_proof_pass_03` blocked",
        "",
        "## What Changed",
        "",
        "- Pass08 supersedes pass07 with a shot-level EDL instead of beat-level microsequence guessing.",
        "- Every declared story shot is at least `2.0s`.",
        "- Source-native edits are treated as actual story cuts; hidden-cut audit is recorded per shot.",
        "- 08A-09B remains the approved failure/breakup tail and still ends on the legible breakup/debris handle.",
        "- Historical signal texture was not applied; it stays blocked until this timing pass is approved.",
        "",
        "## Reads",
        "",
        f"- duration_floor_read: `{manifest['duration_floor_read']}`",
        f"- hidden_cut_audit_read: `{manifest['hidden_cut_audit_read']}`",
        "- shot_timing_read: `pending_human_review`",
        "- continuity_read: `pending_human_review`",
        "- repetition_read: `pending_human_review`",
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
    ]
    for blocker in manifest["blockers"]:
        lines.append(f"- {blocker}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_outputs(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for row in manifest["shot_timing_edl"]:
        path = Path(row["output_path"])
        if not path.exists():
            errors.append(f"missing shot handle {path}")
            continue
        width, height, audio_count = video_meta(path)
        dur = duration_seconds(path)
        if (width, height) != (FRAME_W, FRAME_H):
            errors.append(f"{path.name} geometry {width}x{height}")
        if audio_count != 0:
            errors.append(f"{path.name} has audio_count={audio_count}")
        if dur + 0.001 < STORY_MIN_SECONDS:
            errors.append(f"{path.name} duration {dur:.3f} < {STORY_MIN_SECONDS:.1f}")
        if row["no_internal_cut_read"] != "pass":
            errors.append(f"{path.name} hidden cut read {row['no_internal_cut_read']}")
    preview = Path(manifest["preview_reel_path"])
    if not preview.exists():
        errors.append(f"missing preview {preview}")
    else:
        width, height, audio_count = video_meta(preview)
        if (width, height) != (FRAME_W, FRAME_H):
            errors.append(f"preview geometry {width}x{height}")
        if audio_count != 0:
            errors.append(f"preview has audio_count={audio_count}")
    return {"validation_status": "pass" if not errors else "reject", "validation_errors": errors}


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PASS08_ROOT.mkdir(parents=True, exist_ok=True)
    shot_dir = PASS08_ROOT / "candidates/shot_handles"
    beat_dir = PASS08_ROOT / "candidates/beat_handles"
    sample_dir = PASS08_ROOT / "review_frames/shot_samples"
    source_frame_dir = PASS08_ROOT / "source_frames"
    beat_frame_dir = PASS08_ROOT / "review_frames/beat_rollup_samples"
    pages_dir = PASS08_ROOT / "pages"
    for directory in [shot_dir, beat_dir, sample_dir, source_frame_dir, beat_frame_dir, pages_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    for source in [FR, RC, CL, TAIL_08A, TAIL_09A, TAIL_09B]:
        if not source.exists():
            raise FileNotFoundError(source)

    shots = shot_specs()
    for shot in shots:
        make_clip(shot, shot_dir, source_frame_dir)
        audit_shot(shot, sample_dir)

    beat_handles: list[dict[str, Any]] = []
    for beat_order in range(1, 16):
        beat_shots = [shot for shot in shots if shot.beat_order == beat_order]
        if not beat_shots:
            raise RuntimeError(f"no shots for beat_order={beat_order}")
        beat_id = beat_shots[0].parent_beat_id
        out_path = beat_dir / f"{beat_order:02d}_{beat_id}__pass08_shot_timing_rollup__no_audio.mp4"
        concat_clips([Path(s.output_path) for s in beat_shots if s.output_path], out_path)
        width, height, audio_count = video_meta(out_path)
        dur = duration_seconds(out_path)
        beat_handles.append(
            {
                "order": beat_order,
                "beat_id": beat_id,
                "normalized_clip_path": str(out_path),
                "normalized_clip_sha256": sha256(out_path),
                "motion_strategy": "shot_timing_edl_rollup",
                "role": "secondary 15-beat continuity handle; timing authority is the shot EDL",
                "duration_seconds": round(dur, 3),
                "width": width,
                "height": height,
                "audio_stream_count": audio_count,
                "shot_ids": [s.shot_id for s in beat_shots],
                "min_story_shot_seconds": round(min(float(s.actual_duration_seconds or 0) for s in beat_shots), 3),
                "hidden_cut_audit_read": "pass" if all(s.no_internal_cut_read == "pass" for s in beat_shots) else "reject",
                "duration_floor_read": "pass" if all(s.duration_floor_read == "pass" for s in beat_shots) else "reject",
            }
        )

    timeline = PASS08_ROOT / f"timeline_pass08_{run_id}.ffconcat"
    preview = PASS08_ROOT / f"motion_contact_sheet_pass_08_{run_id}_shot_timing_preview.mp4"
    with timeline.open("w", encoding="utf-8") as fh:
        fh.write("ffconcat version 1.0\n")
        for shot in shots:
            fh.write(f"file '{shot.output_path}'\n")
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
            str(timeline),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(preview),
        ]
    )

    edl_json = PASS08_ROOT / f"shot_timing_edl_{run_id}.json"
    edl_md = PASS08_ROOT / f"shot_timing_edl_{run_id}.md"
    shot_sheet = PASS08_ROOT / f"motion_contact_sheet_pass_08_{run_id}_shot_timing.png"
    beat_sheet = PASS08_ROOT / f"motion_contact_sheet_pass_08_{run_id}_beat_rollup.png"
    shot_pages = make_shot_contact_sheet(shots, shot_sheet, pages_dir)
    make_beat_rollup(beat_handles, beat_sheet, beat_frame_dir)

    rows = edl_rows(shots)
    edl_payload = {
        "stage": "motion_contact_sheet_pass_08_shot_timing_edl",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "run_id": run_id,
        "normal_story_shot_minimum_seconds": STORY_MIN_SECONDS,
        "source_native_edits_policy": "every source-native cut must be an EDL row or avoided",
        "rows": rows,
    }
    edl_json.write_text(json.dumps(edl_payload, indent=2) + "\n", encoding="utf-8")
    write_edl_md(rows, edl_md, run_id)

    paths = {
        "edl_json": edl_json,
        "edl_md": edl_md,
        "shot_sheet": shot_sheet,
        "shot_sheet_pages": shot_pages,
        "beat_sheet": beat_sheet,
        "preview": preview,
        "timeline": timeline,
    }
    manifest = build_manifest(run_id, shots, beat_handles, paths)
    manifest.update(validate_outputs(manifest))

    manifest_path = PASS08_ROOT / f"manifest_pass08_shot_timing_repair_{run_id}.json"
    active_manifest_path = PASS08_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    active_manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    review_path = PASS08_ROOT / f"review_pass08_shot_timing_repair_{run_id}.md"
    write_review(review_path, manifest)

    print(json.dumps({
        "run_id": run_id,
        "manifest": str(active_manifest_path),
        "timestamped_manifest": str(manifest_path),
        "review": str(review_path),
        "shot_timing_edl_json": str(edl_json),
        "shot_timing_edl_md": str(edl_md),
        "shot_timing_contact_sheet": str(shot_sheet),
        "beat_rollup_contact_sheet": str(beat_sheet),
        "preview_reel": str(preview),
        "validation_status": manifest["validation_status"],
        "validation_errors": manifest["validation_errors"],
    }, indent=2))


if __name__ == "__main__":
    main()
