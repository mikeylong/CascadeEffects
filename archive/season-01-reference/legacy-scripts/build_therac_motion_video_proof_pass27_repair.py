#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


EPISODE_ID = "therac-25"
SHORT_ID = "therac_short_scoped_v1"
FPS = 30
WIDTH = 720
HEIGHT = 1280

EPISODE_PRODUCTION_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1/production"
)
VIZ_SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1"
)

ROOT_MANIFEST = VIZ_SHORT_ROOT / "manifest.json"
PASS26_MANIFEST = VIZ_SHORT_ROOT / (
    "motion_video_proof/pass_26_from_pass24_no_freeze/"
    "motion_video_proof_manifest_pass_26_from_pass24_no_freeze.json"
)
PASS26_FEEDBACK_ROOT = VIZ_SHORT_ROOT / "motion_video_proof/pass_26_review_feedback"
PASS26_FEEDBACK_JSON = PASS26_FEEDBACK_ROOT / "motion_video_proof_review_feedback_pass_26.json"
PASS26_FEEDBACK_PACKET = EPISODE_PRODUCTION_ROOT / "motion_video_proof_review_feedback_pass_26.md"

PASS27_ROOT = VIZ_SHORT_ROOT / "motion_video_proof/pass_27_from_pass26_tighten"
SEGMENTS_DIR = PASS27_ROOT / "segments"
FRAMES_DIR = PASS27_ROOT / "frames"
CONTACT_SHEETS_DIR = PASS27_ROOT / "contact_sheets"
LOGS_DIR = PASS27_ROOT / "logs"
MANIFEST_PATH = PASS27_ROOT / "motion_video_proof_manifest_pass_27_from_pass26_tighten.json"
MOTION_ONLY_PATH = PASS27_ROOT / "therac25_motion_video_proof_pass_27_motion_only_no_audio.mp4"
PROOF_VIDEO_PATH = PASS27_ROOT / "therac25_motion_video_proof_pass_27_audio_timed.mp4"
FRAME_SHEET_PATH = CONTACT_SHEETS_DIR / "therac25_motion_video_proof_pass_27_frame_sheet.png"
AFFECTED_SHEET_PATH = CONTACT_SHEETS_DIR / "therac25_motion_video_proof_pass_27_affected_rows_sheet.png"
BEAT_SHEET_PATH = EPISODE_PRODUCTION_ROOT / "motion_video_proof_beat_sheet_pass_27.md"
PROOF_PACKET_PATH = EPISODE_PRODUCTION_ROOT / "motion_video_proof_pass_27.md"
MOTION_PROOF_CANONICAL = EPISODE_PRODUCTION_ROOT / "motion_video_proof.md"

P13 = VIZ_SHORT_ROOT / "visual_research/image_motion_source_pool_lock_pass_13/locked_clips"
REPAIRS = {
    "edl_07_machine_over_patient": {
        "source_path": P13 / "p13_p05__archival_machine_over_patient__gZIez0zNiU4__tail_safe_no_audio.mp4",
        "source_offset_seconds": 0.567,
        "source_url": "https://www.youtube.com/watch?v=gZIez0zNiU4",
        "source_asset_id": "P13_P05",
        "repair_strategy": "trim_past_source_native_cut",
        "feedback": "At 19s, source briefly changes and reads like an editor error.",
        "repair_note": "Start after the 0.4s source-native shot change; keep the stable machine-over-patient shot.",
    },
    "edl_11_operators_report_hold": {
        "source_path": P13 / "p13_p07__archival_patient_table_setup__RJcbDmom4BQ__tail_safe_no_audio.mp4",
        "source_offset_seconds": 2.0,
        "source_url": "https://www.youtube.com/watch?v=RJcbDmom4BQ",
        "source_asset_id": "P13_P07",
        "repair_strategy": "replace_static_hold_with_continuous_source_motion",
        "feedback": "At 30-34s, frozen frame reads as a mistake.",
        "repair_note": "Replace intentional frame hold with a continuous operator/table setup source span.",
    },
    "edl_16_wrong_software_hold": {
        "source_path": P13 / "p13_p06__archival_patient_setup__gZIez0zNiU4__tail_safe_no_audio.mp4",
        "source_offset_seconds": 2.0,
        "source_url": "https://www.youtube.com/watch?v=gZIez0zNiU4",
        "source_asset_id": "P13_P06",
        "repair_strategy": "replace_static_hold_with_more_visible_clinical_motion",
        "feedback": "At 48-51s, frozen frame reads as a mistake.",
        "repair_note": "Replace gauge frame hold with continuous clinical setup motion before the source-native cut.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    log_path.write_text(
        "$ " + " ".join(command) + "\n\n"
        + "STDOUT:\n" + (completed.stdout or "") + "\n"
        + "STDERR:\n" + (completed.stderr or "") + "\n",
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(f"command failed, see {log_path}")


def ffprobe(path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"ffprobe failed for {path}")
    return json.loads(completed.stdout)


def probe_read(path: Path) -> dict[str, Any]:
    meta = ffprobe(path)
    streams = meta.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    first_video = video[0] if video else {}
    return {
        "duration_seconds": round(float(meta.get("format", {}).get("duration", 0.0)), 3),
        "video_stream_count": len(video),
        "audio_stream_count": len(audio),
        "width": first_video.get("width"),
        "height": first_video.get("height"),
        "avg_frame_rate": first_video.get("avg_frame_rate"),
        "codec_name": first_video.get("codec_name"),
    }


def visual_filter(start: float, duration: float) -> str:
    return (
        f"trim=start={start:.3f}:duration={duration:.3f},setpts=PTS-STARTPTS,"
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},format=yuv420p"
    )


def render_segment(segment: dict[str, Any]) -> dict[str, Any]:
    edl_id = segment["edl_id"]
    row_index = int(segment["row_index"])
    duration = float(segment["target_story_duration_seconds"])
    repair = REPAIRS.get(edl_id)
    if repair:
        input_path = Path(repair["source_path"])
        offset = float(repair["source_offset_seconds"])
        source_url = repair["source_url"]
        segment_class = "repaired_continuous_motion"
        repair_status = "repaired_from_pass26_feedback"
    else:
        input_path = Path(segment["segment_path"])
        offset = 0.0
        source_url = segment["source_url"]
        segment_class = segment["motion_review_class"]
        repair_status = "carried_forward_from_pass26"

    output_path = SEGMENTS_DIR / f"{row_index:02d}_{edl_id}__proof_pass27.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(input_path),
            "-vf",
            visual_filter(offset, duration),
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
            str(output_path),
        ],
        LOGS_DIR / f"{row_index:02d}_{edl_id}__segment_pass27.log",
    )
    read = probe_read(output_path)
    return {
        **{k: segment[k] for k in [
            "row_index",
            "edl_id",
            "parent_shot_id",
            "visual_beat_id",
            "timeline_start_seconds",
            "timeline_end_seconds",
            "target_story_duration_seconds",
            "rights_read",
        ]},
        "rendered_segment_duration_seconds": read["duration_seconds"],
        "input_path": str(input_path),
        "segment_path": str(output_path),
        "source_url": source_url,
        "source_clip_offset_seconds": offset,
        "motion_review_class": segment_class,
        "source_playback_mode": "direct_source_clip" if repair else segment["source_playback_mode"],
        "repair_status": repair_status,
        "repair_strategy": repair["repair_strategy"] if repair else None,
        "repair_note": repair["repair_note"] if repair else None,
        "source_asset_id": repair["source_asset_id"] if repair else None,
        "pass26_feedback": repair["feedback"] if repair else None,
        "no_freeze_read": "pass_continuous_source_motion_no_static_hold" if repair else segment["no_freeze_read"],
        "hygiene_read": "strict_clean_internal_review_sample; final production requires rights/source clearance",
        "production_disposition": "internal_review_only_not_final_production_eligible",
        "probe_read": read,
    }


def concat_segments(segment_paths: list[Path]) -> Path:
    concat_path = PASS27_ROOT / "concat_motion_video_proof_pass_27.txt"
    write_text(concat_path, "\n".join(f"file '{path}'" for path in segment_paths))
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
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-movflags",
            "+faststart",
            str(MOTION_ONLY_PATH),
        ],
        LOGS_DIR / "concat_motion_only_pass27.log",
    )
    return concat_path


def mux_audio(motion_only: Path, audio_path: Path, audio_duration: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(motion_only),
            "-i",
            str(audio_path),
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
            "-t",
            f"{audio_duration:.6f}",
            "-movflags",
            "+faststart",
            str(PROOF_VIDEO_PATH),
        ],
        LOGS_DIR / "mux_audio_pass27.log",
    )


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def extract_frame(video_path: Path, timestamp: float, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{max(0.0, timestamp):.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ],
        LOGS_DIR / f"extract_{output_path.stem}.log",
    )


def make_frame_records(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for segment in segments:
        start = float(segment["timeline_start_seconds"])
        end = float(segment["timeline_end_seconds"])
        probes = [
            ("start", start + 0.1),
            ("mid", start + max(0.1, (end - start) / 2)),
            ("end", max(start + 0.1, end - 0.1)),
        ]
        paths = {}
        for label, timestamp in probes:
            path = FRAMES_DIR / f"{segment['row_index']:02d}_{segment['edl_id']}__{label}__{timestamp:.3f}s.jpg"
            extract_frame(PROOF_VIDEO_PATH, timestamp, path)
            paths[label] = str(path)
        records.append({**segment, "proof_frame_paths": paths})
    return records


def draw_sheet(records: list[dict[str, Any]], path: Path, title: str) -> None:
    label_w = 420
    thumb_w = 240
    thumb_h = 426
    gap = 14
    row_h = thumb_h + 34
    header_h = 96
    sheet_w = label_w + (thumb_w * 3) + (gap * 5)
    sheet_h = header_h + row_h * len(records) + gap
    image = Image.new("RGB", (sheet_w, sheet_h), (16, 19, 22))
    draw = ImageDraw.Draw(image)
    title_font = load_font(24, True)
    header_font = load_font(13)
    label_font = load_font(15, True)
    small_font = load_font(10)
    draw.text((18, 18), title, fill=(235, 238, 240), font=title_font)
    draw.text(
        (18, 51),
        "Pass 26 tighten repairs: row 7 hidden cut removed; rows 11/16 static holds replaced",
        fill=(172, 180, 186),
        font=header_font,
    )
    for i, label in enumerate(["start", "mid", "end"]):
        draw.text((label_w + gap + i * (thumb_w + gap), 72), label, fill=(172, 180, 186), font=small_font)

    y = header_h
    for record in records:
        repaired = record["repair_status"] == "repaired_from_pass26_feedback"
        color = (238, 154, 97) if repaired else (122, 214, 178)
        draw.rectangle((18, y + 8, 26, y + row_h - 12), fill=color)
        draw.text((36, y + 18), f"{record['row_index']:02d} {record['edl_id']}", fill=(235, 238, 240), font=label_font)
        detail_lines = [
            f"{record['timeline_start_seconds']:.3f}-{record['timeline_end_seconds']:.3f}s | {record['motion_review_class']}",
            record["repair_strategy"] or "carried forward",
            record["repair_note"] or "unchanged from pass 26",
            "final export blocked; rights unresolved",
        ]
        for i, line in enumerate(detail_lines):
            draw.text((36, y + 48 + i * 22), str(line)[:58], fill=(172, 180, 186), font=small_font)
        for col, key in enumerate(["start", "mid", "end"]):
            thumb = Image.open(record["proof_frame_paths"][key]).convert("RGB")
            thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb_w, thumb_h), (8, 10, 12))
            tile.paste(thumb, ((thumb_w - thumb.width) // 2, (thumb_h - thumb.height) // 2))
            x = label_w + gap + col * (thumb_w + gap)
            image.paste(tile, (x, y + 16))
            draw.rectangle((x, y + 16, x + thumb_w, y + 16 + thumb_h), outline=(58, 65, 70), width=1)
        y += row_h
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def write_packets(proof: dict[str, Any]) -> None:
    feedback_lines = [
        "# Therac-25 Motion Video Proof Pass 26 Feedback",
        "",
        "- `disposition`: `tighten`",
        "- `basis`: `human/DP review notes`",
        "- `input_proof_path`: `" + proof["input_pass26_proof_video_path"] + "`",
        "",
        "| time | row | issue | pass 27 repair |",
        "| --- | --- | --- | --- |",
    ]
    for item in proof["pass26_feedback_items"]:
        feedback_lines.append(
            f"| `{item['time_range']}` | `{item['edl_id']}` | {item['issue']} | {item['pass27_repair']} |"
        )
    write_text(PASS26_FEEDBACK_PACKET, "\n".join(feedback_lines))

    beat_lines = [
        "# Therac-25 Motion Video Proof Beat Sheet Pass 27",
        "",
        f"- `proof_video_path`: `{PROOF_VIDEO_PATH}`",
        f"- `motion_only_video_path`: `{MOTION_ONLY_PATH}`",
        f"- `manifest_path`: `{MANIFEST_PATH}`",
        "- `disposition`: `diagnostic only`",
        "- `review_required`: `human/DP keep/tighten/reject before final export`",
        "",
        "| row | time | edl_id | source mode | repair status | note |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for segment in proof["segments"]:
        beat_lines.append(
            f"| `{segment['row_index']:02d}` | `{segment['timeline_start_seconds']:.3f}-{segment['timeline_end_seconds']:.3f}` | "
            f"`{segment['edl_id']}` | `{segment['source_playback_mode']}` | `{segment['repair_status']}` | "
            f"{segment['repair_note'] or 'carried forward'} |"
        )
    write_text(BEAT_SHEET_PATH, "\n".join(beat_lines))

    packet = "\n".join(
        [
            "# Therac-25 Motion Video Proof Pass 27",
            "",
            "## Gate Read",
            "",
            "- `stage`: `motion_video_proof_repair`",
            "- `episode_id`: `therac-25`",
            "- `short_id`: `therac_short_scoped_v1`",
            "- `pass_id`: `pass_27_from_pass26_tighten`",
            "- `input_pass26_manifest_path`: `" + str(PASS26_MANIFEST) + "`",
            "- `input_pass26_feedback_path`: `" + str(PASS26_FEEDBACK_PACKET) + "`",
            "- `proof_video_path`: `" + str(PROOF_VIDEO_PATH) + "`",
            "- `frame_sheet_path`: `" + str(FRAME_SHEET_PATH) + "`",
            "- `affected_rows_sheet_path`: `" + str(AFFECTED_SHEET_PATH) + "`",
            "- `disposition`: `diagnostic only`",
            "- `reel_class`: `mixed review short`",
            "- `may_start_final_export`: `false`",
            "",
            "Pass 27 repairs the three pass 26 review notes without changing approved audio timing.",
            "",
            "## Validation",
            "",
            f"- `story_shot_count`: `{proof['story_shot_count']}`",
            f"- `repaired_row_count`: `{proof['repaired_row_count']}`",
            f"- `motion_only_audio_stream_count`: `{proof['motion_only_read']['audio_stream_count']}`",
            f"- `proof_video_audio_stream_count`: `{proof['proof_video_read']['audio_stream_count']}`",
            f"- `proof_video_duration_seconds`: `{proof['proof_video_read']['duration_seconds']}`",
            f"- `all_segments_visual_only_no_audio`: `{str(proof['validation']['all_segments_visual_only_no_audio']).lower()}`",
            f"- `final_export_authorized`: `{str(proof['validation']['final_export_authorized']).lower()}`",
            "",
            "## Handoff",
            "",
            "```yaml",
            "stage: motion_video_proof_repair",
            "episode_id: therac-25",
            "short_id: therac_short_scoped_v1",
            "pass_id: pass_27_from_pass26_tighten",
            f"proof_video_path: {PROOF_VIDEO_PATH}",
            f"manifest_path: {MANIFEST_PATH}",
            "disposition: diagnostic only",
            "reel_class: mixed review short",
            "next_required_gate: human/DP review motion video proof pass 27",
            "may_start_final_export: false",
            "may_advance: false",
            "```",
        ]
    )
    write_text(PROOF_PACKET_PATH, packet)

    canonical = "\n".join(
        [
            "# Therac-25 Current Motion Video Proof",
            "",
            "Current review gate: `motion_video_proof pass 27 repair review`.",
            "",
            f"- `packet_path`: `{PROOF_PACKET_PATH}`",
            f"- `manifest_path`: `{MANIFEST_PATH}`",
            f"- `proof_video_path`: `{PROOF_VIDEO_PATH}`",
            f"- `motion_only_video_path`: `{MOTION_ONLY_PATH}`",
            f"- `frame_sheet_path`: `{FRAME_SHEET_PATH}`",
            f"- `affected_rows_sheet_path`: `{AFFECTED_SHEET_PATH}`",
            f"- `beat_sheet_path`: `{BEAT_SHEET_PATH}`",
            f"- `story_shot_count`: `{proof['story_shot_count']}`",
            f"- `proof_video_duration_seconds`: `{proof['proof_video_read']['duration_seconds']}`",
            f"- `proof_video_audio_stream_count`: `{proof['proof_video_read']['audio_stream_count']}`",
            "- `disposition`: `diagnostic only`",
            "- `may_start_final_export`: `false`",
            "",
            "Human/DP review must mark this proof `keep`, `tighten`, or `reject` before final-export routing starts.",
        ]
    )
    write_text(MOTION_PROOF_CANONICAL, canonical)


def update_root_manifest(root: dict[str, Any], proof: dict[str, Any]) -> None:
    root.update(
        {
            "status": "human_dp_motion_video_proof_pass_27_repair_review",
            "current_stage": "human/DP motion_video_proof pass 27 repair review",
            "last_completed_stage": "motion_video_proof pass 27 repair",
            "disposition": "motion_video_proof_pass_27_repair_review_ready_no_final_authorized",
            "next_required_stage": "human/DP motion video proof pass 27 review",
            "next_action": "Review motion video proof pass 27; mark keep/tighten/reject before final export.",
            "may_start_motion_video_proof": False,
            "may_start_ltx_render": False,
            "may_start_generated_stills": False,
            "may_start_final_export": False,
            "motion_video_proof_pass_26_feedback_path": str(PASS26_FEEDBACK_JSON),
            "motion_video_proof_pass_26_feedback_packet_path": str(PASS26_FEEDBACK_PACKET),
            "motion_video_proof_pass_26_review_disposition": "tighten",
            "motion_video_proof_pass_27_manifest_path": str(MANIFEST_PATH),
            "motion_video_proof_pass_27_packet_path": str(PROOF_PACKET_PATH),
            "motion_video_proof_pass_27_beat_sheet_path": str(BEAT_SHEET_PATH),
            "motion_video_proof_pass_27_frame_sheet_path": str(FRAME_SHEET_PATH),
            "motion_video_proof_pass_27_affected_rows_sheet_path": str(AFFECTED_SHEET_PATH),
            "motion_video_proof_pass_27_path": str(PROOF_VIDEO_PATH),
            "motion_video_proof_pass_27_summary": {
                "stage": proof["stage"],
                "pass_id": proof["pass_id"],
                "disposition": proof["disposition"],
                "reel_class": proof["reel_class"],
                "proof_video_path": proof["proof_video_path"],
                "motion_only_video_path": proof["motion_only_video_path"],
                "frame_sheet_path": proof["frame_sheet_path"],
                "affected_rows_sheet_path": proof["affected_rows_sheet_path"],
                "beat_sheet_path": proof["beat_sheet_path"],
                "story_shot_count": proof["story_shot_count"],
                "repaired_row_count": proof["repaired_row_count"],
                "proof_video_duration_seconds": proof["proof_video_read"]["duration_seconds"],
                "proof_video_audio_stream_count": proof["proof_video_read"]["audio_stream_count"],
                "motion_only_audio_stream_count": proof["motion_only_read"]["audio_stream_count"],
                "may_start_final_export": False,
                "next_required_gate": proof["next_required_gate"],
            },
            "active_review_surface": {
                "stage": "motion_video_proof",
                "pass_id": "pass_27_from_pass26_tighten",
                "proof_video_path": str(PROOF_VIDEO_PATH),
                "frame_sheet_path": str(FRAME_SHEET_PATH),
                "affected_rows_sheet_path": str(AFFECTED_SHEET_PATH),
                "beat_sheet_path": str(BEAT_SHEET_PATH),
                "manifest_path": str(MANIFEST_PATH),
                "packet_path": str(PROOF_PACKET_PATH),
                "review_required": "human/DP keep/tighten/reject before final export",
            },
        }
    )
    write_json(ROOT_MANIFEST, root)


def main() -> None:
    for directory in [PASS26_FEEDBACK_ROOT, PASS27_ROOT, SEGMENTS_DIR, FRAMES_DIR, CONTACT_SHEETS_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    root = read_json(ROOT_MANIFEST)
    pass26 = read_json(PASS26_MANIFEST)
    audio_path = Path(root["short_audio_wav_path"])
    audio_duration = float(root["audio_duration_seconds"])

    feedback_items = [
        {
            "time_range": "18.6-21.6s",
            "edl_id": "edl_07_machine_over_patient",
            "issue": "brief source-native change near 19s reads like editor error",
            "pass27_repair": REPAIRS["edl_07_machine_over_patient"]["repair_note"],
        },
        {
            "time_range": "30.304-34.3s",
            "edl_id": "edl_11_operators_report_hold",
            "issue": "frozen frame",
            "pass27_repair": REPAIRS["edl_11_operators_report_hold"]["repair_note"],
        },
        {
            "time_range": "47.8-51.459s",
            "edl_id": "edl_16_wrong_software_hold",
            "issue": "frozen frame",
            "pass27_repair": REPAIRS["edl_16_wrong_software_hold"]["repair_note"],
        },
    ]
    feedback = {
        "schema_version": "1.0",
        "stage": "motion_video_proof_review",
        "pass_id": "pass_26_feedback",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "created_at": utc_now(),
        "input_pass26_manifest_path": str(PASS26_MANIFEST),
        "input_pass26_proof_video_path": pass26["proof_video_path"],
        "disposition": "tighten",
        "items": feedback_items,
        "may_start_final_export": False,
        "next_required_stage": "motion_video_proof pass 27 repair",
    }
    write_json(PASS26_FEEDBACK_JSON, feedback)

    segments = [render_segment(segment) for segment in pass26["segments"]]
    concat_path = concat_segments([Path(segment["segment_path"]) for segment in segments])
    mux_audio(MOTION_ONLY_PATH, audio_path, audio_duration)
    frame_records = make_frame_records(segments)
    affected_records = [record for record in frame_records if record["repair_status"] == "repaired_from_pass26_feedback"]
    draw_sheet(frame_records, FRAME_SHEET_PATH, "Therac-25 Motion Video Proof Pass 27 Frame Sheet")
    draw_sheet(affected_records, AFFECTED_SHEET_PATH, "Therac-25 Pass 27 Repaired Rows")

    motion_only_read = probe_read(MOTION_ONLY_PATH)
    proof_video_read = probe_read(PROOF_VIDEO_PATH)
    validation = {
        "proof_assembled_from_shot_timing_edl": True,
        "pass26_feedback_disposition": "tighten",
        "pass26_flagged_rows_repaired": sorted(REPAIRS.keys()) == sorted(r["edl_id"] for r in affected_records),
        "all_story_shots_above_2s_floor": all(s["target_story_duration_seconds"] >= 2.0 for s in segments),
        "all_segments_visual_only_no_audio": all(s["probe_read"]["audio_stream_count"] == 0 for s in segments),
        "motion_only_visual_only_no_audio": motion_only_read["audio_stream_count"] == 0,
        "proof_video_has_approved_audio": proof_video_read["audio_stream_count"] == 1,
        "proof_video_vertical_720x1280": proof_video_read["width"] == WIDTH and proof_video_read["height"] == HEIGHT,
        "ltx_used": False,
        "generated_stills_used": False,
        "final_export_authorized": False,
    }
    proof = {
        "schema_version": "1.0",
        "stage": "motion_video_proof_repair",
        "pass_id": "pass_27_from_pass26_tighten",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "created_at": utc_now(),
        "input_pass26_manifest_path": str(PASS26_MANIFEST),
        "input_pass26_feedback_manifest_path": str(PASS26_FEEDBACK_JSON),
        "input_pass26_proof_video_path": pass26["proof_video_path"],
        "approved_audio_path": str(audio_path),
        "short_audio_package_path": root.get("short_audio_package_path"),
        "expected_voice_profile_id": root.get("expected_voice_profile_id") or "youtube_shorts_mike_challenger_match_v1",
        "audio_package_sha256": root.get("audio_package_sha256"),
        "packaged_audio_sha256": root.get("packaged_audio_sha256"),
        "caption_source_path": root.get("short_audio_caption_source_path"),
        "transcript_sha256": root.get("transcript_sha256"),
        "expected_audio_duration_seconds": audio_duration,
        "story_shot_count": len(segments),
        "repaired_row_count": len(affected_records),
        "segments_root": str(SEGMENTS_DIR),
        "frame_root": str(FRAMES_DIR),
        "motion_only_video_path": str(MOTION_ONLY_PATH),
        "proof_video_path": str(PROOF_VIDEO_PATH),
        "frame_sheet_path": str(FRAME_SHEET_PATH),
        "affected_rows_sheet_path": str(AFFECTED_SHEET_PATH),
        "beat_sheet_path": str(BEAT_SHEET_PATH),
        "concat_path": str(concat_path),
        "proof_video_sha256": sha256_file(PROOF_VIDEO_PATH),
        "motion_only_video_sha256": sha256_file(MOTION_ONLY_PATH),
        "motion_only_read": motion_only_read,
        "proof_video_read": proof_video_read,
        "pass26_feedback_items": feedback_items,
        "repair_specs": {
            key: {**value, "source_path": str(value["source_path"])}
            for key, value in REPAIRS.items()
        },
        "segments": frame_records,
        "validation": validation,
        "disposition": "diagnostic only",
        "reel_class": "mixed review short",
        "may_start_final_export": False,
        "may_start_ltx_render": False,
        "may_start_generated_stills": False,
        "blockers": [
            "human/DP proof review has not marked pass 27 keep",
            "YouTube/source rights remain unresolved for final production use",
            "final export requires keep motion proof and final-export routing",
        ],
        "next_required_gate": "human/DP review motion video proof pass 27",
    }
    write_json(MANIFEST_PATH, proof)
    write_packets(proof)
    update_root_manifest(root, proof)
    print(json.dumps({
        "pass26_feedback": str(PASS26_FEEDBACK_JSON),
        "proof_manifest": str(MANIFEST_PATH),
        "proof_video": str(PROOF_VIDEO_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "affected_rows_sheet": str(AFFECTED_SHEET_PATH),
        "proof_video_read": proof_video_read,
    }, indent=2))


if __name__ == "__main__":
    main()
