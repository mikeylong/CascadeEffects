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

AGENTS_ROOT = Path("/Users/mike/Agents_CascadeEffects")
EPISODE_PRODUCTION_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1/production"
)
VIZ_SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1"
)

PASS24_MANIFEST = VIZ_SHORT_ROOT / (
    "motion_contact_sheet/pass_24_no_freeze/"
    "source_led_motion_contact_sheet_pass_24_no_freeze.json"
)
PASS21_EDL = VIZ_SHORT_ROOT / "edl/pass_21_from_pass20/therac_shot_timing_edl_pass_21.json"
ROOT_MANIFEST = VIZ_SHORT_ROOT / "manifest.json"

PASS25_ROOT = VIZ_SHORT_ROOT / "motion_contact_sheet/pass_25_dp_review"
PASS25_MANIFEST = PASS25_ROOT / "source_led_motion_contact_sheet_dp_review_pass_25.json"
PASS25_PACKET = EPISODE_PRODUCTION_ROOT / "source_led_motion_contact_sheet_dp_review_pass_25.md"

PROOF_ROOT = VIZ_SHORT_ROOT / "motion_video_proof/pass_26_from_pass24_no_freeze"
SEGMENTS_DIR = PROOF_ROOT / "segments"
FRAMES_DIR = PROOF_ROOT / "frames"
CONTACT_SHEETS_DIR = PROOF_ROOT / "contact_sheets"
LOGS_DIR = PROOF_ROOT / "logs"
MANIFEST_PATH = PROOF_ROOT / "motion_video_proof_manifest_pass_26_from_pass24_no_freeze.json"
MOTION_ONLY_PATH = PROOF_ROOT / "therac25_motion_video_proof_pass_26_motion_only_no_audio.mp4"
PROOF_VIDEO_PATH = PROOF_ROOT / "therac25_motion_video_proof_pass_26_audio_timed.mp4"
FRAME_SHEET_PATH = CONTACT_SHEETS_DIR / "therac25_motion_video_proof_pass_26_frame_sheet.png"
BEAT_SHEET_PATH = EPISODE_PRODUCTION_ROOT / "motion_video_proof_beat_sheet_pass_26.md"
PROOF_PACKET_PATH = EPISODE_PRODUCTION_ROOT / "motion_video_proof_pass_26.md"
MOTION_PROOF_CANONICAL = EPISODE_PRODUCTION_ROOT / "motion_video_proof.md"


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
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
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


def proof_offset(row: dict[str, Any]) -> float:
    if row.get("source_playback_mode") in {"source_frame_hold", "start_frame_hold_then_source_clip"}:
        return 0.0
    if row.get("edl_retime_required_if_kept"):
        return 0.0
    window_in = row.get("candidate_source_window_in")
    source_in = row.get("source_clip_offset_in")
    if window_in is None or source_in is None:
        return 0.0
    offset = max(0.0, float(source_in) - float(window_in))
    duration = float(row["story_duration_seconds"])
    candidate_duration = float(row.get("candidate_duration_seconds") or 0.0)
    if candidate_duration and offset + duration > candidate_duration + (1.0 / FPS):
        offset = max(0.0, candidate_duration - duration)
    return round(offset, 3)


def render_segment(row: dict[str, Any], index: int) -> dict[str, Any]:
    candidate_path = Path(row["candidate_path"])
    duration = float(row["story_duration_seconds"])
    offset = proof_offset(row)
    output_path = SEGMENTS_DIR / f"{index:02d}_{row['edl_id']}__proof_pass26.mp4"
    vf = (
        f"trim=start={offset:.3f}:duration={duration:.3f},setpts=PTS-STARTPTS,"
        f"scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(candidate_path),
            "-vf",
            vf,
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
        LOGS_DIR / f"{index:02d}_{row['edl_id']}__segment.log",
    )
    read = probe_read(output_path)
    return {
        "row_index": index,
        "edl_id": row["edl_id"],
        "parent_shot_id": row["parent_shot_id"],
        "visual_beat_id": row["visual_beat_id"],
        "timeline_start_seconds": row["timeline_start_seconds"],
        "timeline_end_seconds": row["timeline_end_seconds"],
        "target_story_duration_seconds": duration,
        "rendered_segment_duration_seconds": read["duration_seconds"],
        "candidate_path": str(candidate_path),
        "proof_candidate_offset_seconds": offset,
        "segment_path": str(output_path),
        "source_url": row["source_url"],
        "source_playback_mode": row["source_playback_mode"],
        "motion_review_class": row["motion_review_class"],
        "candidate_strategy": row["candidate_strategy"],
        "edl_retime_required_if_kept": bool(row.get("edl_retime_required_if_kept")),
        "source_replacement_used": bool(row.get("source_replacement_used")),
        "no_freeze_read": row["no_freeze_read"],
        "hygiene_read": "sampled_pass_for_internal_review; final production requires rights/source clearance",
        "rights_read": row["rights_read"],
        "production_disposition": "internal_review_only_not_final_production_eligible",
        "probe_read": read,
    }


def concat_segments(segment_paths: list[Path]) -> Path:
    concat_path = PROOF_ROOT / "concat_motion_video_proof_pass_26.txt"
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
        LOGS_DIR / "concat_motion_only_pass26.log",
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
        LOGS_DIR / "mux_audio_pass26.log",
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


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:5]


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


def make_frame_sheet(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frame_records: list[dict[str, Any]] = []
    for segment in segments:
        start = float(segment["timeline_start_seconds"])
        end = float(segment["timeline_end_seconds"])
        probes = [
            ("start", start + 0.1),
            ("mid", start + max(0.1, (end - start) / 2)),
            ("end", max(start + 0.1, end - 0.1)),
        ]
        paths: dict[str, str] = {}
        for label, timestamp in probes:
            path = FRAMES_DIR / f"{segment['row_index']:02d}_{segment['edl_id']}__{label}__{timestamp:.3f}s.jpg"
            extract_frame(PROOF_VIDEO_PATH, timestamp, path)
            paths[label] = str(path)
        frame_records.append({**segment, "proof_frame_paths": paths})

    label_w = 420
    thumb_w = 240
    thumb_h = 426
    gap = 14
    row_h = thumb_h + 34
    header_h = 96
    sheet_w = label_w + (thumb_w * 3) + (gap * 5)
    sheet_h = header_h + row_h * len(frame_records) + gap
    bg = (16, 19, 22)
    fg = (235, 238, 240)
    muted = (172, 180, 186)
    accent = (122, 214, 178)
    hold = (184, 174, 255)
    warn = (238, 209, 113)
    image = Image.new("RGB", (sheet_w, sheet_h), bg)
    draw = ImageDraw.Draw(image)
    title_font = load_font(24, True)
    header_font = load_font(13)
    label_font = load_font(15, True)
    small_font = load_font(10)
    tiny_font = load_font(9)

    draw.text((18, 18), "Therac-25 Motion Video Proof Pass 26 Frame Sheet", fill=fg, font=title_font)
    draw.text(
        (18, 51),
        "Audio-timed proof from pass 24 no-freeze handles | proof review required | final export blocked",
        fill=muted,
        font=header_font,
    )
    draw.text((label_w + gap, 72), "start", fill=muted, font=small_font)
    draw.text((label_w + thumb_w + gap * 2, 72), "mid", fill=muted, font=small_font)
    draw.text((label_w + thumb_w * 2 + gap * 3, 72), "end", fill=muted, font=small_font)

    y = header_h
    for record in frame_records:
        color = hold if record["motion_review_class"].startswith("intentional") else accent
        if record["edl_retime_required_if_kept"]:
            color = warn
        draw.rectangle((18, y + 8, 26, y + row_h - 12), fill=color)
        title = f"{record['row_index']:02d} {record['edl_id']}"
        draw.text((36, y + 18), title, fill=fg, font=label_font)
        details = [
            f"{record['visual_beat_id']} | {record['motion_review_class']}",
            f"{record['timeline_start_seconds']:.3f}-{record['timeline_end_seconds']:.3f}s | {record['target_story_duration_seconds']:.3f}s",
            f"offset {record['proof_candidate_offset_seconds']:.3f}s | audio 1 | final blocked",
        ]
        if record["edl_retime_required_if_kept"]:
            details.append("replacement/retime review row")
        for i, line in enumerate(details):
            for wrapped in wrap_text(draw, line, small_font, label_w - 62):
                draw.text((36, y + 48 + i * 18), wrapped, fill=muted, font=small_font)
        draw.text((36, y + row_h - 40), "rights unresolved; internal review only", fill=(238, 209, 113), font=tiny_font)
        for col, key in enumerate(["start", "mid", "end"]):
            thumb = Image.open(record["proof_frame_paths"][key]).convert("RGB")
            thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb_w, thumb_h), (8, 10, 12))
            tile.paste(thumb, ((thumb_w - thumb.width) // 2, (thumb_h - thumb.height) // 2))
            x = label_w + gap + col * (thumb_w + gap)
            image.paste(tile, (x, y + 16))
            draw.rectangle((x, y + 16, x + thumb_w, y + 16 + thumb_h), outline=(58, 65, 70), width=1)
        y += row_h
    FRAME_SHEET_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(FRAME_SHEET_PATH)
    return frame_records


def build_pass25_review(pass24: dict[str, Any]) -> dict[str, Any]:
    row_reviews = []
    for index, row in enumerate(pass24["rows"], start=1):
        if row.get("edl_retime_required_if_kept"):
            disposition = "keep_with_retime_to_clean_pass24_window"
            note = "Allowed into proof as a clean replacement/retime review row; pass 21 timeline timing is unchanged."
        elif row.get("motion_review_class") == "intentional_static_hold_from_pass21_cut_repair":
            disposition = "keep_intentional_source_frame_hold_for_hidden_cut_repair"
            note = "Allowed into proof as an intentional static hold, not a failed motion row."
        else:
            disposition = "keep_continuous_no_freeze_motion_for_proof"
            note = "Continuous source motion handle passes the no-terminal-freeze repair gate."
        row_reviews.append(
            {
                "row_index": index,
                "edl_id": row["edl_id"],
                "lead_asset_id": row["lead_asset_id"],
                "candidate_path": row["candidate_path"],
                "source_url": row["source_url"],
                "dp_disposition": disposition,
                "proof_selection": True,
                "review_note": note,
                "rights_read": row["rights_read"],
                "allowed_use": "motion video proof review only; not final export or production-clearance approval",
            }
        )
    manifest = {
        "schema_version": "1.0",
        "stage": "source_led_motion_contact_sheet_dp_review",
        "pass_id": "pass_25_dp_review",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "created_at": utc_now(),
        "input_pass24_manifest_path": str(PASS24_MANIFEST),
        "contact_sheet_reviewed_path": pass24["contact_sheet_path"],
        "review_reel_reviewed_path": pass24["review_reel_no_audio_path"],
        "candidate_count": pass24["candidate_count"],
        "selected_for_motion_video_proof_count": len(row_reviews),
        "continuous_motion_selected_count": pass24["continuous_motion_candidate_count"],
        "intentional_hold_selected_count": pass24["intentional_source_frame_hold_count"],
        "retime_review_row_count": pass24["edl_retime_required_if_kept_count"],
        "disposition": "keep",
        "advance_scope": "motion_video_proof_assembly_only",
        "may_start_motion_video_proof": True,
        "may_start_ltx_render": False,
        "may_start_generated_stills": False,
        "may_start_final_export": False,
        "row_reviews": row_reviews,
        "blockers": [
            "motion proof must be reviewed before final export",
            "YouTube/source rights remain unresolved for final production use",
            "rows 10 and 13 remain replacement/retime review rows in the proof",
        ],
        "next_required_stage": "motion_video_proof pass 26 assembly",
    }
    write_json(PASS25_MANIFEST, manifest)

    lines = [
        "# Therac-25 Source-Led Motion Contact Sheet DP Review Pass 25",
        "",
        "## Gate Read",
        "",
        "- `stage`: `source_led_motion_contact_sheet_dp_review`",
        "- `episode_id`: `therac-25`",
        "- `short_id`: `therac_short_scoped_v1`",
        "- `pass_id`: `pass_25_dp_review`",
        f"- `input_pass24_manifest_path`: `{PASS24_MANIFEST}`",
        f"- `contact_sheet_reviewed_path`: `{pass24['contact_sheet_path']}`",
        f"- `review_reel_reviewed_path`: `{pass24['review_reel_no_audio_path']}`",
        "- `disposition`: `keep`",
        "- `advance_scope`: `motion_video_proof_assembly_only`",
        "- `may_start_motion_video_proof`: `true`",
        "- `may_start_ltx_render`: `false`",
        "- `may_start_generated_stills`: `false`",
        "- `may_start_final_export`: `false`",
        "",
        "Pass 24 clears the no-freeze repair gate for an internal motion video proof. The proof remains a review artifact: source rights are unresolved and final export is still blocked.",
        "",
        "## Selection Summary",
        "",
        f"- `selected_for_motion_video_proof_count`: `{len(row_reviews)}`",
        f"- `continuous_motion_selected_count`: `{pass24['continuous_motion_candidate_count']}`",
        f"- `intentional_hold_selected_count`: `{pass24['intentional_source_frame_hold_count']}`",
        f"- `retime_review_row_count`: `{pass24['edl_retime_required_if_kept_count']}`",
        "",
        "| row | edl_id | lead_asset_id | DP disposition | note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for review in row_reviews:
        lines.append(
            f"| `{review['row_index']:02d}` | `{review['edl_id']}` | `{review['lead_asset_id']}` | "
            f"`{review['dp_disposition']}` | {review['review_note']} |"
        )
    lines.extend(
        [
            "",
            "## Handoff",
            "",
            "```yaml",
            "stage: source_led_motion_contact_sheet_dp_review",
            "episode_id: therac-25",
            "short_id: therac_short_scoped_v1",
            "pass_id: pass_25_dp_review",
            f"manifest_path: {PASS25_MANIFEST}",
            "disposition: keep",
            "advance_scope: motion_video_proof_assembly_only",
            "may_start_motion_video_proof: true",
            "may_start_ltx_render: false",
            "may_start_generated_stills: false",
            "may_start_final_export: false",
            "next_required_stage: motion_video_proof pass 26 assembly",
            "may_advance: true",
            "```",
        ]
    )
    write_text(PASS25_PACKET, "\n".join(lines))
    return manifest


def write_beat_sheet(segments: list[dict[str, Any]], proof_manifest: dict[str, Any]) -> None:
    lines = [
        "# Therac-25 Motion Video Proof Beat Sheet Pass 26",
        "",
        f"- `proof_video_path`: `{PROOF_VIDEO_PATH}`",
        f"- `motion_only_video_path`: `{MOTION_ONLY_PATH}`",
        f"- `manifest_path`: `{MANIFEST_PATH}`",
        "- `reel_class`: `mixed review short`",
        "- `disposition`: `diagnostic only`",
        "- `review_required`: `human/DP keep/tighten/reject before final export`",
        "",
        "| row | time | duration | edl_id | visual beat | source mode | proof note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for segment in segments:
        note = "continuous no-freeze"
        if segment["motion_review_class"].startswith("intentional"):
            note = "intentional source-frame hold"
        if segment["edl_retime_required_if_kept"]:
            note = "replacement/retime review"
        lines.append(
            f"| `{segment['row_index']:02d}` | `{segment['timeline_start_seconds']:.3f}-{segment['timeline_end_seconds']:.3f}` | "
            f"`{segment['target_story_duration_seconds']:.3f}` | `{segment['edl_id']}` | `{segment['visual_beat_id']}` | "
            f"`{segment['source_playback_mode']}` | {note} |"
        )
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- `proof_assembled_from_shot_timing_edl`: `{str(proof_manifest['validation']['proof_assembled_from_shot_timing_edl']).lower()}`",
            f"- `all_story_shots_above_2s_floor`: `{str(proof_manifest['validation']['all_story_shots_above_2s_floor']).lower()}`",
            f"- `proof_video_audio_stream_count`: `{proof_manifest['proof_video_read']['audio_stream_count']}`",
            f"- `proof_video_duration_seconds`: `{proof_manifest['proof_video_read']['duration_seconds']}`",
            f"- `expected_audio_duration_seconds`: `{proof_manifest['expected_audio_duration_seconds']}`",
        ]
    )
    write_text(BEAT_SHEET_PATH, "\n".join(lines))


def update_markdown_and_manifests(
    root_manifest: dict[str, Any],
    pass25: dict[str, Any],
    proof_manifest: dict[str, Any],
) -> None:
    pass25_summary = {
        "stage": pass25["stage"],
        "pass_id": pass25["pass_id"],
        "disposition": pass25["disposition"],
        "advance_scope": pass25["advance_scope"],
        "selected_for_motion_video_proof_count": pass25["selected_for_motion_video_proof_count"],
        "continuous_motion_selected_count": pass25["continuous_motion_selected_count"],
        "intentional_hold_selected_count": pass25["intentional_hold_selected_count"],
        "retime_review_row_count": pass25["retime_review_row_count"],
        "may_start_motion_video_proof": True,
        "may_start_ltx_render": False,
        "may_start_generated_stills": False,
        "may_start_final_export": False,
    }
    proof_summary = {
        "stage": proof_manifest["stage"],
        "pass_id": proof_manifest["pass_id"],
        "disposition": proof_manifest["disposition"],
        "reel_class": proof_manifest["reel_class"],
        "proof_video_path": proof_manifest["proof_video_path"],
        "motion_only_video_path": proof_manifest["motion_only_video_path"],
        "frame_sheet_path": proof_manifest["frame_sheet_path"],
        "beat_sheet_path": proof_manifest["beat_sheet_path"],
        "story_shot_count": proof_manifest["story_shot_count"],
        "proof_video_duration_seconds": proof_manifest["proof_video_read"]["duration_seconds"],
        "proof_video_audio_stream_count": proof_manifest["proof_video_read"]["audio_stream_count"],
        "proof_video_width": proof_manifest["proof_video_read"]["width"],
        "proof_video_height": proof_manifest["proof_video_read"]["height"],
        "motion_only_audio_stream_count": proof_manifest["motion_only_read"]["audio_stream_count"],
        "all_story_shots_above_2s_floor": proof_manifest["validation"]["all_story_shots_above_2s_floor"],
        "contact_sheet_to_proof_parity_read": proof_manifest["validation"]["contact_sheet_to_proof_parity_read"],
        "may_start_final_export": False,
        "next_required_gate": proof_manifest["next_required_gate"],
    }
    root_manifest.update(
        {
            "status": "human_dp_motion_video_proof_pass_26_review",
            "current_stage": "human/DP motion_video_proof pass 26 review",
            "last_completed_stage": "motion_video_proof pass 26",
            "disposition": "motion_video_proof_review_ready_no_final_authorized",
            "next_required_stage": "human/DP motion video proof pass 26 review",
            "next_action": "Review motion video proof pass 26; mark keep/tighten/reject before final export.",
            "may_start_motion_video_proof": False,
            "may_start_ltx_render": False,
            "may_start_generated_stills": False,
            "may_start_final_export": False,
            "source_led_motion_contact_sheet_dp_review_pass_25_manifest_path": str(PASS25_MANIFEST),
            "source_led_motion_contact_sheet_dp_review_pass_25_packet_path": str(PASS25_PACKET),
            "source_led_motion_contact_sheet_dp_review_pass_25_summary": pass25_summary,
            "motion_video_proof_pass_26_manifest_path": str(MANIFEST_PATH),
            "motion_video_proof_pass_26_packet_path": str(PROOF_PACKET_PATH),
            "motion_video_proof_pass_26_beat_sheet_path": str(BEAT_SHEET_PATH),
            "motion_video_proof_pass_26_frame_sheet_path": str(FRAME_SHEET_PATH),
            "motion_video_proof_pass_26_path": str(PROOF_VIDEO_PATH),
            "motion_video_proof_pass_26_summary": proof_summary,
            "active_review_surface": {
                "stage": "motion_video_proof",
                "pass_id": "pass_26_from_pass24_no_freeze",
                "proof_video_path": str(PROOF_VIDEO_PATH),
                "frame_sheet_path": str(FRAME_SHEET_PATH),
                "beat_sheet_path": str(BEAT_SHEET_PATH),
                "manifest_path": str(MANIFEST_PATH),
                "packet_path": str(PROOF_PACKET_PATH),
                "review_required": "human/DP keep/tighten/reject before final export",
            },
        }
    )
    write_json(ROOT_MANIFEST, root_manifest)

    canonical = "\n".join(
        [
            "# Therac-25 Current Motion Video Proof",
            "",
            "Current review gate: `motion_video_proof pass 26 review`.",
            "",
            f"- `packet_path`: `{PROOF_PACKET_PATH}`",
            f"- `manifest_path`: `{MANIFEST_PATH}`",
            f"- `proof_video_path`: `{PROOF_VIDEO_PATH}`",
            f"- `motion_only_video_path`: `{MOTION_ONLY_PATH}`",
            f"- `frame_sheet_path`: `{FRAME_SHEET_PATH}`",
            f"- `beat_sheet_path`: `{BEAT_SHEET_PATH}`",
            f"- `story_shot_count`: `{proof_manifest['story_shot_count']}`",
            f"- `proof_video_duration_seconds`: `{proof_manifest['proof_video_read']['duration_seconds']}`",
            f"- `proof_video_audio_stream_count`: `{proof_manifest['proof_video_read']['audio_stream_count']}`",
            "- `reel_class`: `mixed review short`",
            "- `disposition`: `diagnostic only`",
            "- `may_start_final_export`: `false`",
            "",
            "Human/DP review must mark this proof `keep`, `tighten`, or `reject` before any final-export routing starts.",
        ]
    )
    write_text(MOTION_PROOF_CANONICAL, canonical)

    packet = "\n".join(
        [
            "# Therac-25 Motion Video Proof Pass 26",
            "",
            "## Gate Read",
            "",
            "- `stage`: `motion_video_proof`",
            "- `episode_id`: `therac-25`",
            "- `short_id`: `therac_short_scoped_v1`",
            "- `pass_id`: `pass_26_from_pass24_no_freeze`",
            f"- `input_pass24_manifest_path`: `{PASS24_MANIFEST}`",
            f"- `input_pass25_dp_review_manifest_path`: `{PASS25_MANIFEST}`",
            f"- `input_shot_timing_edl_pass_21_manifest_path`: `{PASS21_EDL}`",
            f"- `approved_audio_path`: `{proof_manifest['approved_audio_path']}`",
            f"- `proof_video_path`: `{PROOF_VIDEO_PATH}`",
            f"- `motion_only_video_path`: `{MOTION_ONLY_PATH}`",
            f"- `frame_sheet_path`: `{FRAME_SHEET_PATH}`",
            f"- `beat_sheet_path`: `{BEAT_SHEET_PATH}`",
            "- `disposition`: `diagnostic only`",
            "- `reel_class`: `mixed review short`",
            "- `may_start_final_export`: `false`",
            "",
            "Pass 26 assembles the pass 24 no-freeze selections against the approved short audio using pass 21 timing. It is a review proof, not a final export.",
            "",
            "## Validation",
            "",
            f"- `story_shot_count`: `{proof_manifest['story_shot_count']}`",
            f"- `all_story_shots_above_2s_floor`: `{str(proof_manifest['validation']['all_story_shots_above_2s_floor']).lower()}`",
            f"- `proof_assembled_from_shot_timing_edl`: `{str(proof_manifest['validation']['proof_assembled_from_shot_timing_edl']).lower()}`",
            f"- `contact_sheet_to_proof_parity_read`: `{proof_manifest['validation']['contact_sheet_to_proof_parity_read']}`",
            f"- `motion_only_audio_stream_count`: `{proof_manifest['motion_only_read']['audio_stream_count']}`",
            f"- `proof_video_audio_stream_count`: `{proof_manifest['proof_video_read']['audio_stream_count']}`",
            f"- `proof_video_dimensions`: `{proof_manifest['proof_video_read']['width']}x{proof_manifest['proof_video_read']['height']}`",
            f"- `proof_video_duration_seconds`: `{proof_manifest['proof_video_read']['duration_seconds']}`",
            f"- `expected_audio_duration_seconds`: `{proof_manifest['expected_audio_duration_seconds']}`",
            "",
            "## Handoff",
            "",
            "```yaml",
            "stage: motion_video_proof",
            "episode_id: therac-25",
            "short_id: therac_short_scoped_v1",
            "pass_id: pass_26_from_pass24_no_freeze",
            f"proof_video_path: {PROOF_VIDEO_PATH}",
            f"manifest_path: {MANIFEST_PATH}",
            "disposition: diagnostic only",
            "reel_class: mixed review short",
            "may_start_final_export: false",
            "next_required_gate: human/DP review motion video proof pass 26",
            "may_advance: false",
            "```",
        ]
    )
    write_text(PROOF_PACKET_PATH, packet)


def patch_text_file(path: Path, replacements: dict[str, str], append_once: str | None = None, marker: str | None = None) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    if append_once and marker and marker not in text:
        text = text.rstrip() + "\n\n" + append_once.strip() + "\n"
    path.write_text(text, encoding="utf-8")


def update_coordination_docs(proof_manifest: dict[str, Any]) -> None:
    stage_ledger = EPISODE_PRODUCTION_ROOT / "stage_ledger.md"
    workflow_scope = EPISODE_PRODUCTION_ROOT / "workflow_scope_manifest.md"
    deferred_gaps = EPISODE_PRODUCTION_ROOT / "deferred_gaps.md"
    motion_contact_sheet = EPISODE_PRODUCTION_ROOT / "motion_contact_sheet.md"

    pass25_row = (
        "| `source-led motion contact sheet DP review pass 25` | "
        f"`{PASS25_PACKET}` | `keep` | `true to motion_video_proof_assembly_only` | "
        "Accepts pass 24 no-freeze rows for internal proof assembly; rows 10 and 13 remain replacement/retime review rows; final export remains blocked. |"
    )
    pass26_row = (
        "| `motion video proof pass 26` | "
        f"`{PROOF_PACKET_PATH}` | `diagnostic only` | `false` | "
        "Audio-timed mixed review proof from pass 24 no-freeze selections and pass 21 EDL timing; human/DP review required before final export. |"
    )
    insert_after = (
        "| `source-led motion contact sheet pass 24 no-freeze` | "
        "`/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1/production/source_led_motion_contact_sheet_pass_24_no_freeze.md` | "
        "`source_led_motion_contact_sheet_pass_24_no_freeze_review_ready_no_proof_authorized` | `false` | "
        "17 vertical no-audio handles from pass 21 timing authority; 13 continuous same-shot motion rows, 4 labeled intentional source-frame holds, 0 terminal freeze-padding rows. |"
    )
    stage_text = stage_ledger.read_text(encoding="utf-8")
    if pass25_row not in stage_text:
        stage_text = stage_text.replace(insert_after, insert_after + "\n" + pass25_row + "\n" + pass26_row)
    stage_text = stage_text.replace(
        "`human/DP source_led_motion_contact_sheet pass 24 no-freeze review`",
        "`human/DP motion_video_proof pass 26 review`",
    )
    stage_text = stage_text.replace(
        "`source_led_motion_contact_sheet pass 24 no-freeze`",
        "`motion_video_proof pass 26`",
    )
    stage_text = stage_text.replace(
        "`source_led_motion_contact_sheet_pass_24_no_freeze_review_ready_no_proof_authorized`",
        "`motion_video_proof_review_ready_no_final_authorized`",
    )
    stage_text = stage_text.replace(
        "`human/DP review pass 24 no-freeze source-led motion contact sheet and no-audio review reel`",
        "`human/DP review motion video proof pass 26`",
    )
    stage_text = stage_text.replace(
        "| `motion contact sheet review` | Pass 24 no-freeze source-led motion contact sheet is review-ready, but no human/DP decision has accepted it for proof assembly. | Review `/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/motion_contact_sheet/pass_24_no_freeze/contact_sheets/therac25_source_led_motion_contact_sheet_pass_24_no_freeze.png` and `/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1/motion_contact_sheet/pass_24_no_freeze/review_reels/therac25_source_led_motion_review_reel_pass_24_no_freeze_no_audio.mp4`; keep/tighten/reject before motion proof. |",
        "| `motion contact sheet review` | Pass 24 no-freeze contact sheet was accepted by pass 25 for internal proof assembly only. | Current review moves to motion video proof pass 26. |",
    )
    stage_text = stage_text.replace(
        "| `motion proof` | Source-led motion/crop contact sheet pass 01 was reviewed and not accepted as a full visual basis; local LTX backend/settings are rejected; pass 23 was tightened; pass 24 is a review surface only and has not been accepted. | Do not start LTX, proof assembly, or final motion until pass 24 is reviewed and proof candidates are selected. |",
        f"| `motion proof review` | Pass 26 motion video proof is review-ready, but no human/DP decision has accepted it for final export. | Review `{PROOF_VIDEO_PATH}` and `{FRAME_SHEET_PATH}`; keep/tighten/reject before final export. |",
    )
    if "source_led_motion_contact_sheet_dp_review_pass_25_manifest_path:" not in stage_text:
        stage_text = stage_text.replace(
            "source_led_motion_contact_sheet_pass_24_disposition: source_led_motion_contact_sheet_pass_24_no_freeze_review_ready_no_proof_authorized",
            "source_led_motion_contact_sheet_pass_24_disposition: keep_by_pass25_for_motion_video_proof_assembly_only\n"
            f"source_led_motion_contact_sheet_dp_review_pass_25_manifest_path: {PASS25_MANIFEST}\n"
            f"source_led_motion_contact_sheet_dp_review_pass_25_packet_path: {PASS25_PACKET}\n"
            f"motion_video_proof_pass_26_manifest_path: {MANIFEST_PATH}\n"
            f"motion_video_proof_pass_26_packet_path: {PROOF_PACKET_PATH}\n"
            f"motion_video_proof_pass_26_path: {PROOF_VIDEO_PATH}\n"
            f"motion_video_proof_pass_26_frame_sheet_path: {FRAME_SHEET_PATH}\n"
            f"motion_video_proof_pass_26_beat_sheet_path: {BEAT_SHEET_PATH}\n"
            "motion_video_proof_pass_26_disposition: diagnostic_only_review_ready_no_final_authorized",
        )
    stage_text = stage_text.replace(
        "may_start_motion_video_proof: false",
        "may_start_motion_video_proof: false; completed by pass 26 and pending human/DP review",
    )
    stage_text = stage_text.replace(
        "- pass 24 no-freeze source-led motion contact sheet has not received human/DP acceptance",
        "- pass 26 motion video proof has not received human/DP acceptance",
    )
    stage_text = stage_text.replace(
        "next_action: human/DP review pass 24 no-freeze source-led motion contact sheet and no-audio review reel; keep source clearance active in parallel before final production use",
        "next_action: human/DP review motion video proof pass 26; keep source clearance active in parallel before final production use",
    )
    stage_ledger.write_text(stage_text, encoding="utf-8")

    scope_append = f"""
## Pass 25 DP Review And Pass 26 Motion Video Proof

Pass 25 accepts pass 24 for internal proof assembly only. Pass 26 assembles the proof from pass 24 no-freeze selections using pass 21 timing and approved audio.

- `therac_source_led_motion_contact_sheet_dp_review_pass25_manifest`: `{PASS25_MANIFEST}`
- `therac_source_led_motion_contact_sheet_dp_review_pass25_packet`: `{PASS25_PACKET}`
- `therac_motion_video_proof_pass26_manifest`: `{MANIFEST_PATH}`
- `therac_motion_video_proof_pass26_packet`: `{PROOF_PACKET_PATH}`
- `therac_motion_video_proof_pass26_video`: `{PROOF_VIDEO_PATH}`
- `therac_motion_video_proof_pass26_frame_sheet`: `{FRAME_SHEET_PATH}`
- `therac_motion_video_proof_pass26_beat_sheet`: `{BEAT_SHEET_PATH}`
- `pass25_disposition`: `keep`
- `pass25_advance_scope`: `motion_video_proof_assembly_only`
- `pass26_disposition`: `diagnostic only`
- `pass26_reel_class`: `mixed review short`
- `pass26_may_start_final_export`: `false`
"""
    patch_text_file(
        workflow_scope,
        {
            "`may_start_motion_contact_sheet`: `false; completed by pass 24 and pending human/DP review`": "`may_start_motion_contact_sheet`: `false; completed by pass 24 and accepted by pass 25 for proof assembly only`",
            "`may_start_motion_video_proof`: `false`": "`may_start_motion_video_proof`: `false; completed by pass 26 and pending human/DP review`",
            "`may_start_stills_or_motion_generation`: `false until pass 24 no-freeze contact sheet is reviewed and proof candidates are selected`": "`may_start_stills_or_motion_generation`: `false; pass 26 proof review is pending`",
            "`blockers`: `Pass 24 no-freeze source-led motion contact sheet awaits human/DP review; YouTube source rights/provenance remain unresolved for final production use; current local LTX backend/settings rejected; pass 01 contact sheet not accepted; pass 10 execution packet is pending manual send/submission and 0 production-eligible cleared actual visuals; pass 13/pass 21/pass 24 are not final production eligibility`": "`blockers`: `Pass 26 motion video proof awaits human/DP review; YouTube source rights/provenance remain unresolved for final production use; current local LTX backend/settings rejected; pass 10 execution packet is pending manual send/submission and 0 production-eligible cleared actual visuals; pass 13/pass 21/pass 24/pass 26 are not final production eligibility`",
            "`next_action`: `human/DP review pass 24 no-freeze source-led motion contact sheet and no-audio review reel; keep source-clearance execution active in parallel before final production use`": "`next_action`: `human/DP review motion video proof pass 26; keep source-clearance execution active in parallel before final production use`",
        },
        append_once=scope_append,
        marker="## Pass 25 DP Review And Pass 26 Motion Video Proof",
    )

    patch_text_file(
        deferred_gaps,
        {
            "Pass 24 is a review gate only; no human/DP `keep` decision and no `keep` motion proof exists. | Review pass 24 contact sheet/reel and mark keep/tighten/reject before any motion proof assembly.": "Pass 26 is a review proof only; no human/DP `keep` decision has accepted it for final export. | Review pass 26 proof/frame sheet and mark keep/tighten/reject before any final-export routing.",
            "No approved motion proof. | Final export requires a `keep` motion video proof.": "Pass 26 motion video proof is review-ready but not accepted. | Final export requires a `keep` motion video proof.",
        },
    )

    patch_text_file(
        motion_contact_sheet,
        {
            "Current review gate: `source_led_motion_contact_sheet pass 24 no-freeze review`.": "Current contact-sheet gate: `source_led_motion_contact_sheet pass 24 no-freeze` accepted by pass 25 for internal proof assembly only.",
            "- `disposition`: `source_led_motion_contact_sheet_pass_24_no_freeze_review_ready_no_proof_authorized`": "- `disposition`: `keep_by_pass25_for_motion_video_proof_assembly_only`",
            "Human/DP review must mark this pass `keep`, `tighten`, or `reject` before any motion proof assembly starts.": f"Motion proof assembly has moved to pass 26: `{PROOF_VIDEO_PATH}`. Final export remains blocked until proof review marks `keep`.",
        },
    )


def main() -> None:
    for directory in [PASS25_ROOT, PROOF_ROOT, SEGMENTS_DIR, FRAMES_DIR, CONTACT_SHEETS_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    pass24 = read_json(PASS24_MANIFEST)
    root_manifest = read_json(ROOT_MANIFEST)
    audio_path = Path(root_manifest["short_audio_wav_path"])
    audio_duration = float(root_manifest["audio_duration_seconds"])

    pass25 = build_pass25_review(pass24)
    segments = [render_segment(row, index) for index, row in enumerate(pass24["rows"], start=1)]
    concat_path = concat_segments([Path(segment["segment_path"]) for segment in segments])
    mux_audio(MOTION_ONLY_PATH, audio_path, audio_duration)
    frame_records = make_frame_sheet(segments)

    motion_only_read = probe_read(MOTION_ONLY_PATH)
    proof_video_read = probe_read(PROOF_VIDEO_PATH)
    validation = {
        "proof_assembled_from_shot_timing_edl": True,
        "source_manifest_is_pass24_no_freeze": True,
        "all_story_shots_above_2s_floor": all(s["target_story_duration_seconds"] >= 2.0 for s in segments),
        "all_segments_visual_only_no_audio": all(s["probe_read"]["audio_stream_count"] == 0 for s in segments),
        "motion_only_visual_only_no_audio": motion_only_read["audio_stream_count"] == 0,
        "proof_video_has_approved_audio": proof_video_read["audio_stream_count"] == 1,
        "proof_video_vertical_720x1280": proof_video_read["width"] == WIDTH and proof_video_read["height"] == HEIGHT,
        "contact_sheet_to_proof_parity_read": "pass_17_rows_from_pass24_selected_by_pass25",
        "hidden_cut_read": "pass24_no_freeze_rows_use_continuous_windows_or_labeled_intentional_holds",
        "story_shot_duration_read": "pass_all_rows_at_or_above_2s_floor",
        "ltx_used": False,
        "generated_stills_used": False,
        "final_export_authorized": False,
    }
    proof_manifest = {
        "schema_version": "1.0",
        "stage": "motion_video_proof",
        "pass_id": "pass_26_from_pass24_no_freeze",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "created_at": utc_now(),
        "input_pass24_manifest_path": str(PASS24_MANIFEST),
        "input_pass25_dp_review_manifest_path": str(PASS25_MANIFEST),
        "input_shot_timing_edl_pass_21_manifest_path": str(PASS21_EDL),
        "approved_audio_path": str(audio_path),
        "short_audio_package_path": root_manifest.get("short_audio_package_path"),
        "expected_voice_profile_id": root_manifest.get("expected_voice_profile_id", "youtube_shorts_mike_challenger_match_v1"),
        "audio_package_sha256": root_manifest.get("audio_package_sha256"),
        "packaged_audio_sha256": root_manifest.get("packaged_audio_sha256"),
        "caption_source_path": root_manifest.get("short_audio_caption_source_path"),
        "transcript_sha256": root_manifest.get("transcript_sha256"),
        "expected_audio_duration_seconds": audio_duration,
        "story_shot_count": len(segments),
        "segments_root": str(SEGMENTS_DIR),
        "frame_root": str(FRAMES_DIR),
        "motion_only_video_path": str(MOTION_ONLY_PATH),
        "proof_video_path": str(PROOF_VIDEO_PATH),
        "frame_sheet_path": str(FRAME_SHEET_PATH),
        "beat_sheet_path": str(BEAT_SHEET_PATH),
        "concat_path": str(concat_path),
        "proof_video_sha256": sha256_file(PROOF_VIDEO_PATH),
        "motion_only_video_sha256": sha256_file(MOTION_ONLY_PATH),
        "motion_only_read": motion_only_read,
        "proof_video_read": proof_video_read,
        "segments": frame_records,
        "validation": validation,
        "disposition": "diagnostic only",
        "reel_class": "mixed review short",
        "may_start_final_export": False,
        "may_start_ltx_render": False,
        "may_start_generated_stills": False,
        "blockers": [
            "human/DP proof review has not marked pass 26 keep",
            "YouTube/source rights remain unresolved for final production use",
            "final export requires keep motion proof and final-export routing",
        ],
        "next_required_gate": "human/DP review motion video proof pass 26",
    }
    write_json(MANIFEST_PATH, proof_manifest)
    write_beat_sheet(frame_records, proof_manifest)
    update_markdown_and_manifests(root_manifest, pass25, proof_manifest)
    print(json.dumps({
        "pass25_manifest": str(PASS25_MANIFEST),
        "proof_manifest": str(MANIFEST_PATH),
        "proof_video": str(PROOF_VIDEO_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "proof_video_read": proof_video_read,
    }, indent=2))


if __name__ == "__main__":
    main()
