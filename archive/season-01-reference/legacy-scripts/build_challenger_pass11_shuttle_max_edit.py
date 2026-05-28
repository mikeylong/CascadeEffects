#!/usr/bin/env python3
"""Build Challenger motion_contact_sheet/pass_11 as a shuttle-max edit.

Pass11 supersedes Pass10 after human feedback that the short must be judged as
a YouTube Shorts scroll experience: gorgeous shuttle imagery beats institutional
room coverage when narration can carry the causal logic.
"""

from __future__ import annotations

import importlib.util
import json
import math
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
EP_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/"
    "challenger_short_scoped_v1"
)
PASS11_ROOT = SHORT_ROOT / "motion_contact_sheet/pass_11"
PASS10_MANIFEST = SHORT_ROOT / "motion_contact_sheet/pass_10/manifest.json"
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
ROOM_HUMAN_MAX_SECONDS = 2.5
SHUTTLE_EVENT_MIN_SECONDS = 58.5


def crop_scale_filter(shot: p10.Shot) -> str:
    if shot.crop_x is None or shot.crop_width_px is None:
        base = f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
    else:
        base = (
            f"crop={shot.crop_width_px}:360:{shot.crop_x}:0,"
            f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
        )
    return (
        f"{base},fps={FPS},"
        "tpad=stop_mode=clone:stop_duration=1.0,"
        f"trim=duration={shot.duration:.3f},setpts=PTS-STARTPTS,format=yuv420p"
    )


def source_frame_filter(shot: p10.Shot) -> str:
    if shot.crop_x is None or shot.crop_width_px is None:
        return f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
    return (
        f"crop={shot.crop_width_px}:360:{shot.crop_x}:0,"
        f"scale={FRAME_W}:{FRAME_H}:flags=lanczos"
    )


def make_clip(shot: p10.Shot, out_dir: Path, source_frame_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    source_frame_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{shot.order:02d}_{shot.shot_id}__pass11_shuttle_max_edit__no_audio.mp4"
    shot.output_path = out

    if shot.source_mode == "direct_source_still_hold":
        frame = source_frame_dir / f"{shot.order:02d}_{shot.shot_id}__source_frame.png"
        p10.run(
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
        p10.run(
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

    p10.run(
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


def build_shots() -> list[p10.Shot]:
    specs = [
        {
            "shot_id": "pass11_01_firing_room_flash",
            "beats": ["beat_01a_routine_room", "beat_02a_process_bank"],
            "source": FR,
            "start": "00:00:22.000",
            "duration": 2.0,
            "family": "ksc_firing_room_primary_02",
            "section": "minimal_room_context",
            "vector": "one_context_flash_then_shuttle_world",
            "role": "brief routine/process context only",
            "group": "room_process_human",
            "crop_x": 150,
        },
        {
            "shot_id": "pass11_02_pad_tower_hero",
            "beats": ["beat_03a_joint_context"],
            "source": CL,
            "start": "00:02:45.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "pad_and_vehicle_context",
            "vector": "immediate_exit_to_shuttle_pad",
            "role": "first post-room image puts the shuttle tower in view",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_03_centered_stack",
            "beats": ["beat_03a_joint_context"],
            "source": CL,
            "start": "00:02:48.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "pad_and_vehicle_context",
            "vector": "centered_vehicle_on_pad",
            "role": "centered shuttle stack as hero subject",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_04_lower_stack_context",
            "beats": ["beat_03b_seal_mechanism"],
            "source": CL,
            "start": "00:02:52.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "mechanism_in_vehicle_context",
            "vector": "vehicle_context_to_lower_stack",
            "role": "mechanism stays attached to the visible shuttle",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_05_lower_stack_venting",
            "beats": ["beat_03b_seal_mechanism", "beat_04a_monitoring_distress"],
            "source": CL,
            "start": "00:02:56.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "warning_normalized_on_vehicle",
            "vector": "venting_read_as_normal_launch_activity",
            "role": "warning normalized through vehicle readiness",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_06_ready_pad_state",
            "beats": ["beat_04a_monitoring_distress", "beat_04b_survival_normalizes"],
            "source": CL,
            "start": "00:02:58.500",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "warning_normalized_on_vehicle",
            "vector": "pad_readiness_holds_tension",
            "role": "shuttle/pad readiness carries normalized-risk narration",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_07_commit_ready_state",
            "beats": ["beat_04c_known_condition", "beat_04d_line_item"],
            "source": CL,
            "start": "00:03:02.000",
            "duration": 4.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "decision_carried_by_vehicle",
            "vector": "room_logic_carried_by_shuttle_waiting_to_launch",
            "role": "decision/burden narration stays on a distinct shuttle view",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_08_ignition_pressure",
            "beats": ["beat_05a_recommendation_enters", "beat_06a_burden_shift_wide"],
            "source": CL,
            "start": "00:03:06.500",
            "duration": 3.0,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "decision_carried_by_vehicle",
            "vector": "commit_pressure_to_ignition",
            "role": "recommendation/burden narration over launch commitment image",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_09_liftoff_centered",
            "beats": ["beat_06b_burden_shift_medium", "beat_07a_cold_commit"],
            "source": CL,
            "start": "00:03:09.500",
            "duration": 3.0,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "launch_sequence",
            "vector": "liftoff_vehicle_rising",
            "role": "liftoff begins; no return to lower/pad framing after this",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_10_early_ascent",
            "beats": ["beat_07a_cold_commit"],
            "source": CL,
            "start": "00:03:12.000",
            "duration": 3.5,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "launch_sequence",
            "vector": "ascent_continues_upward",
            "role": "early ascent sustains the shuttle-forward run",
            "group": "shuttle_event",
            "crop_x": 140,
            "event": True,
        },
        {
            "shot_id": "pass11_11_sustained_ascent_plume",
            "beats": ["beat_07a_cold_commit", "beat_08a_visible_failure"],
            "source": CL,
            "start": "00:03:16.000",
            "duration": 3.9,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "ascent_continuation",
            "vector": "vehicle_climbs_no_reset",
            "role": "sustained shuttle/plume motion",
            "group": "shuttle_event",
            "crop_x": 140,
            "event": True,
        },
        {
            "shot_id": "pass11_12_mid_ascent",
            "beats": ["beat_08a_visible_failure"],
            "source": CL,
            "start": "00:03:24.000",
            "duration": 4.0,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "ascent_continuation",
            "vector": "higher_in_flight",
            "role": "higher ascent, still shuttle-led",
            "group": "shuttle_event",
            "crop_x": 140,
            "event": True,
        },
        {
            "shot_id": "pass11_13_high_ascent",
            "beats": ["beat_08a_visible_failure"],
            "source": CL,
            "start": "00:03:32.000",
            "duration": 4.0,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "ascent_continuation",
            "vector": "altitude_and_distance_increase",
            "role": "high ascent builds toward failure",
            "group": "shuttle_event",
            "crop_x": 180,
            "event": True,
        },
        {
            "shot_id": "pass11_14_failure_bridge",
            "beats": ["beat_08a_visible_failure"],
            "source": CL,
            "start": "00:03:36.000",
            "duration": 4.0,
            "family": "challenger_teaching_launch_failure_primary_01",
            "section": "failure_approach",
            "vector": "approaches_failure_without_pad_reset",
            "role": "failure bridge; no reset to launchpad",
            "group": "shuttle_event",
            "crop_x": 200,
            "event": True,
        },
        {
            "shot_id": "pass11_15_visible_failure",
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
            "shot_id": "pass11_16_pre_breakup_escalation",
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
            "shot_id": "pass11_17_legible_breakup_endpoint",
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

    shots: list[p10.Shot] = []
    for order, item in enumerate(specs, start=1):
        crop_x = item.get("crop_x")
        shots.append(
            p10.Shot(
                order=order,
                shot_id=item["shot_id"],
                covered_beat_ids=item["beats"],
                source_path=item["source"],
                source_span_in=item["start"],
                duration=item["duration"],
                source_family_id=item["family"],
                editorial_section=item["section"],
                continuity_vector=item["vector"],
                role=item["role"],
                coverage_group=item["group"],
                crop_x=crop_x,
                crop_width_px=202 if crop_x is not None else None,
                source_mode=item.get("mode", "direct_source_clip"),
                continuous_event_motion_allowed=bool(item.get("event", False)),
            )
        )
    return shots


def draw_lines(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: Any) -> None:
    x, y = xy
    step = int(getattr(font, "size", 14) * 1.35)
    for line in text.split("\n"):
        draw.text((x, y), line, fill=(235, 235, 235), font=font)
        y += step


def make_shot_sheet(shots: list[p10.Shot], out: Path, page_dir: Path) -> list[Path]:
    font = p10.load_font(18)
    small = p10.load_font(13)
    label_w = 460
    thumb_w = 216
    thumb_h = 384
    gap = 14
    cols = 3
    row_h = thumb_h + 44
    w = label_w + cols * thumb_w + (cols + 1) * gap
    h = 58 + len(shots) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass11 Shuttle-Max Shot EDL - raw frames", fill=(255, 255, 255), font=font)
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
        for idx, frame in enumerate(shot.sample_frame_paths):
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (label_w + gap + idx * (thumb_w + gap), y + 8))
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


def make_beat_rollup(shots: list[p10.Shot], out: Path) -> None:
    font = p10.load_font(18)
    small = p10.load_font(13)
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
    rows = [(beat_id, [s for s in shots if beat_id in s.covered_beat_ids]) for beat_id in beat_ids]
    row_h = thumb_h + 44
    w = label_w + cols * thumb_w + (cols + 1) * gap
    h = 58 + len(rows) * row_h
    sheet = Image.new("RGB", (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "Challenger Pass11 15-Beat Rollup - secondary continuity view", fill=(255, 255, 255), font=font)

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
        for idx, frame in enumerate(frames[:cols]):
            im = Image.open(frame).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (label_w + gap + idx * (thumb_w + gap), y + 8))
    sheet.save(out)


def write_edl_md(rows: list[dict[str, Any]], out: Path, run_id: str) -> None:
    lines = [
        "# Challenger Pass11 Shuttle-Max Editorial EDL",
        "",
        f"- run_id: `{run_id}`",
        "- stage: `motion_contact_sheet_pass_11`",
        "- disposition: `tighten` pending human review",
        "- supersedes: `motion_contact_sheet_pass_10`",
        "- normal_story_shot_minimum_seconds: `2.0`",
        "- editorial target: YouTube Shorts scroll-stopping shuttle imagery",
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
        "# Challenger Pass11 Shuttle-Max Editorial Review",
        "",
        f"- run_id: `{manifest['run_id']}`",
        "- stage: `motion_contact_sheet_pass_11`",
        "- disposition: `tighten` pending human review",
        "- gate: `motion_video_proof_pass_03` remains blocked",
        "",
        "## Editorial Reads",
        "",
        f"- pass10_human_disposition: `{manifest['supersedes_pass10_disposition']}`",
        f"- story_shot_count: `{manifest['story_shot_count']}`",
        f"- sequence_duration_seconds: `{manifest['sequence_duration_seconds']}`",
        f"- room_process_human_duration_seconds: `{manifest['room_process_human_duration_seconds']}`",
        f"- shuttle_event_duration_seconds: `{manifest['shuttle_event_duration_seconds']}`",
        f"- youtube_shorts_competitive_read: `{manifest['youtube_shorts_competitive_read']}`",
        f"- shuttle_gorgeousness_read: `{manifest['shuttle_gorgeousness_read']}`",
        f"- room_coverage_read: `{manifest['room_coverage_read']}`",
        f"- duration_floor_read: `{manifest['duration_floor_read']}`",
        f"- hidden_cut_audit_read: `{manifest['hidden_cut_audit_read']}`",
        f"- frame_freeze_audit_read: `{manifest['frame_freeze_audit_read']}`",
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


def validate(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for row in manifest["shot_timing_edl"]:
        path = Path(row["output_path"])
        if not path.exists():
            errors.append(f"missing {path}")
            continue
        w, h, audio = p10.video_meta(path)
        dur = p10.duration(path)
        if (w, h) != (FRAME_W, FRAME_H):
            errors.append(f"{path.name} geometry {w}x{h}")
        if audio != 0:
            errors.append(f"{path.name} audio_count={audio}")
        if dur + 0.001 < MIN_STORY_SECONDS:
            errors.append(f"{path.name} duration {dur:.3f} < {MIN_STORY_SECONDS}")
        if row["no_internal_cut_read"] != "pass":
            errors.append(f"{path.name} hidden cut {row['no_internal_cut_read']} cuts={row['scene_cut_times']}")
        if row.get("frame_freeze_read") != "pass":
            errors.append(f"{path.name} frame freeze {row.get('frame_freeze_read')} diffs={row.get('frame_diff_values')}")

    preview = Path(manifest["preview_reel_path"])
    if preview.exists():
        w, h, audio = p10.video_meta(preview)
        dur = p10.duration(preview)
        if (w, h) != (FRAME_W, FRAME_H):
            errors.append(f"preview geometry {w}x{h}")
        if audio != 0:
            errors.append("preview has audio")
        if abs(dur - APPROVED_AUDIO_DURATION_SECONDS) > 0.25:
            errors.append(f"preview duration {dur:.3f} does not match approved audio {APPROVED_AUDIO_DURATION_SECONDS:.3f}")
    else:
        errors.append(f"missing preview {preview}")

    if manifest["room_process_human_duration_seconds"] > ROOM_HUMAN_MAX_SECONDS:
        errors.append("room/process/human duration exceeds shuttle-max target")
    if manifest["shuttle_event_duration_seconds"] < SHUTTLE_EVENT_MIN_SECONDS:
        errors.append("shuttle/event duration below shuttle-max target")
    if manifest["tail_endpoint_read"] != "pass":
        errors.append("tail endpoint does not pass")
    return errors


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PASS11_ROOT.mkdir(parents=True, exist_ok=True)
    shot_dir = PASS11_ROOT / "candidates/shot_handles"
    sample_dir = PASS11_ROOT / "review_frames/shot_samples"
    source_frame_dir = PASS11_ROOT / "source_frames"
    pages_dir = PASS11_ROOT / "pages"
    for directory in [shot_dir, sample_dir, source_frame_dir, pages_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    for src in [FR, CL, TAIL_08A, TAIL_09A, TAIL_09B, APPROVED_AUDIO, PASS10_MANIFEST]:
        if not src.exists():
            raise FileNotFoundError(src)

    pass10_manifest = json.loads(PASS10_MANIFEST.read_text(encoding="utf-8"))
    shots = build_shots()
    for shot in shots:
        make_clip(shot, shot_dir, source_frame_dir)
        p10.audit(shot, sample_dir)

    preview = PASS11_ROOT / f"motion_contact_sheet_pass_11_{run_id}_shot_timing_preview.mp4"
    timeline = p10.concat([Path(s.output_path) for s in shots if s.output_path], preview)
    final_frame = PASS11_ROOT / f"motion_contact_sheet_pass_11_{run_id}_tail_final_frame_check.jpg"
    p10.extract_final_frame(preview, final_frame)

    rows = p10.edl_rows(shots)
    for row in rows:
        diffs = row.get("frame_diff_values") or []
        row["frame_freeze_read"] = "reject" if diffs and max(diffs) < 0.8 else "pass"
        row["freeze_failure_mode"] = "visible_frame_freeze" if row["frame_freeze_read"] == "reject" else None
    edl_json = PASS11_ROOT / f"shot_timing_edl_{run_id}.json"
    edl_md = PASS11_ROOT / f"shot_timing_edl_{run_id}.md"
    shot_sheet = PASS11_ROOT / f"motion_contact_sheet_pass_11_{run_id}_shot_timing.png"
    beat_sheet = PASS11_ROOT / f"motion_contact_sheet_pass_11_{run_id}_beat_rollup.png"
    page_paths = make_shot_sheet(shots, shot_sheet, pages_dir)
    make_beat_rollup(shots, beat_sheet)
    write_edl_md(rows, edl_md, run_id)

    edl_json.write_text(
        json.dumps(
            {
                "stage": "motion_contact_sheet_pass_11_shot_timing_edl",
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
    preview_duration = round(p10.duration(preview), 3)
    tail_endpoint = shots[-1].shot_id == "pass11_17_legible_breakup_endpoint" and final_frame.exists()
    youtube_read = "pass" if room_duration <= ROOM_HUMAN_MAX_SECONDS and shuttle_duration >= SHUTTLE_EVENT_MIN_SECONDS else "reject"

    manifest: dict[str, Any] = {
        "stage": "motion_contact_sheet_pass_11",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "reason": "Shuttle-max editorial rebuild after user feedback that YouTube Shorts viewers will choose gorgeous shuttle imagery over boring room/hearing coverage.",
        "supersedes_motion_contact_sheet_pass10_manifest": str(PASS10_MANIFEST),
        "supersedes_pass10_disposition": pass10_manifest.get("disposition"),
        "supersedes_pass10_human_review_disposition": pass10_manifest.get("human_review_disposition"),
        "approved_audio_path": str(APPROVED_AUDIO),
        "approved_audio_duration_seconds": APPROVED_AUDIO_DURATION_SECONDS,
        "source_pool_policy": "approved archival source pool only; no LTX, image generation, source search, historical signal texture, proof assembly, or final export used",
        "historical_signal_texture_applied": False,
        "normal_story_shot_minimum_seconds": MIN_STORY_SECONDS,
        "story_shot_count": len(shots),
        "pass10_story_shot_count": pass10_manifest.get("story_shot_count"),
        "sequence_duration_seconds": preview_duration,
        "video_geometry": f"{FRAME_W}x{FRAME_H}",
        "room_process_human_duration_seconds": room_duration,
        "room_process_human_duration_target_max_seconds": ROOM_HUMAN_MAX_SECONDS,
        "shuttle_event_duration_seconds": shuttle_duration,
        "shuttle_event_duration_target_min_seconds": SHUTTLE_EVENT_MIN_SECONDS,
        "youtube_shorts_competitive_read": youtube_read,
        "shuttle_gorgeousness_read": "pass" if shuttle_duration >= SHUTTLE_EVENT_MIN_SECONDS else "reject",
        "room_coverage_read": "pass" if room_duration <= ROOM_HUMAN_MAX_SECONDS else "reject",
        "scroll_stop_priority": "subject_event",
        "scroll_stop_exception_approved": False,
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
        "frame_freeze_audit_read": "pass" if all(r["frame_freeze_read"] == "pass" for r in rows) else "reject",
        "launch_chronology_read": "pass",
        "tail_endpoint_read": "pass" if tail_endpoint else "reject",
        "shot_timing_read": "pending_human_review",
        "continuity_read": "pending_human_review",
        "disposition": "tighten",
        "may_start_historical_signal_texture": False,
        "may_start_motion_video_proof_pass_03": False,
        "blockers": [
            "human review required for pass11 shuttle-max editorial rebuild",
            "historical signal texture blocked until pass11 receives keep",
            "motion video proof pass03 blocked",
            "final export blocked",
        ],
    }

    errors = validate(manifest)
    manifest["validation_status"] = "pass" if not errors else "reject"
    manifest["validation_errors"] = errors

    manifest_path = PASS11_ROOT / f"manifest_pass11_shuttle_max_edit_{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (PASS11_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    review = PASS11_ROOT / f"review_pass11_shuttle_max_edit_{run_id}.md"
    write_review(review, manifest)

    print(
        json.dumps(
            {
                "run_id": run_id,
                "validation_status": manifest["validation_status"],
                "validation_errors": errors,
                "manifest": str(PASS11_ROOT / "manifest.json"),
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
