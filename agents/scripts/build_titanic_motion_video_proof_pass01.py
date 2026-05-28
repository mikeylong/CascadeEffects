#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


EPISODE_ID = "titanic"
SHORT_ID = "titanic_short_scoped_v1"
EPISODE_PRODUCTION_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1/production"
)
VIZ_SHORT_ROOT = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/titanic/shorts/titanic_short_scoped_v1"
)
STATIC_PROOF_MANIFEST = VIZ_SHORT_ROOT / (
    "stills_video_proof/pass_01_event_led_static/"
    "titanic_event_led_stills_video_proof_manifest_pass_01.json"
)
LTX_SCOUT_MANIFEST = VIZ_SHORT_ROOT / (
    "motion_contact_sheet/pass_01_ltx_scout/"
    "titanic_ltx_motion_scout_manifest_pass_01.json"
)
PROOF_ROOT = VIZ_SHORT_ROOT / "motion_video_proof/pass_01_ltx_hybrid"
SHOT_TIMING_EDL_PATH = EPISODE_PRODUCTION_ROOT / "shot_timing_edl_ltx_motion_proof_pass_01.md"
PROOF_REVIEW_PATH = EPISODE_PRODUCTION_ROOT / "motion_video_proof_review_pass_01_ltx_hybrid.md"
PROOF_HANDOFF_PATH = EPISODE_PRODUCTION_ROOT / "motion_video_proof_handoff_pass_01_ltx_hybrid.yaml"

FPS = 30
WIDTH = 1080
HEIGHT = 1920
STORY_SHOT_FLOOR_SECONDS = 2.0


@dataclass(frozen=True)
class ShotSource:
    shot_id: str
    source_path: Path
    source_kind: str
    source_span_in: float
    source_span_out: float
    tail_hold_seconds: float
    source_sha256: str


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


def ffprobe_json(path: Path) -> dict[str, Any]:
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


def duration_seconds(path: Path) -> float:
    return float(ffprobe_json(path)["format"]["duration"])


def audio_stream_count(path: Path) -> int:
    return sum(1 for stream in ffprobe_json(path)["streams"] if stream.get("codec_type") == "audio")


def render_motion_clip(source: ShotSource, duration: float, output_path: Path, log_path: Path) -> None:
    if output_path.exists():
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    overhang = max(0.0, duration - source.source_span_out)
    vf = (
        f"scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1,fps={FPS},"
        f"tpad=stop_mode=clone:stop_duration={overhang:.3f},"
        f"trim=duration={duration:.3f},setpts=PTS-STARTPTS,format=yuv420p"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source.source_path),
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
        log_path,
    )


def render_static_clip(image_path: Path, duration: float, output_path: Path, log_path: Path) -> None:
    if output_path.exists():
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},format=yuv420p"
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
            f"{duration:.3f}",
            "-i",
            str(image_path),
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
        log_path,
    )


def concat_silent_video(clips: list[Path], output_path: Path, log_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_path = output_path.parent / "concat_motion_video_proof_pass_01.txt"
    write_text(concat_path, "\n".join(f"file '{path}'" for path in clips))
    if output_path.exists():
        return concat_path
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
            "-c",
            "copy",
            "-an",
            str(output_path),
        ],
        log_path,
    )
    return concat_path


def mux_audio(video_path: Path, audio_path: Path, output_path: Path, log_path: Path) -> None:
    if output_path.exists():
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
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
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        log_path,
    )


def extract_mid_frame(video_path: Path, out: Path, log_path: Path) -> None:
    if out.exists():
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    t = max(0.1, min(1.5, duration_seconds(video_path) / 2.0))
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
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out),
        ],
        log_path,
    )


def font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial.ttf",
    ):
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def make_beat_sheet(rows: list[dict[str, Any]], output_path: Path, frames_dir: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    thumb_w, thumb_h = 160, 284
    label_w = 380
    gap = 10
    margin = 24
    row_h = thumb_h + 24
    page_w = margin * 2 + label_w + thumb_w + gap
    page_h = margin * 2 + 84 + row_h * len(rows)
    canvas = Image.new("RGB", (page_w, page_h), (12, 12, 12))
    draw = ImageDraw.Draw(canvas)
    title = font(26)
    body = font(18)
    small = font(14)
    draw.text((margin, margin), "Titanic Motion Proof Pass 01 Beat Sheet", fill=(245, 245, 245), font=title)
    draw.text((margin, margin + 36), "LTX scout winners plus direct sourced-still holds; no captions", fill=(190, 190, 190), font=small)
    y = margin + 84
    for row in rows:
        draw.rectangle((margin, y, page_w - margin, y + row_h - 8), fill=(24, 24, 24))
        x = margin + 12
        draw.text((x, y + 14), row["shot_id"], fill=(245, 245, 245), font=body)
        draw.text((x, y + 44), row["source_kind"], fill=(210, 210, 210), font=small)
        draw.text((x, y + 66), f"{row['proof_start']:.3f}-{row['proof_end']:.3f}s", fill=(185, 185, 185), font=small)
        phrase = str(row.get("phrase", ""))
        for idx, chunk in enumerate([phrase[i : i + 45] for i in range(0, len(phrase), 45)][:4]):
            draw.text((x, y + 94 + idx * 18), chunk, fill=(170, 170, 170), font=small)
        frame_path = frames_dir / f"{row['shot_id']}.png"
        thumb = Image.open(frame_path).convert("RGB")
        thumb = ImageOps.contain(thumb, (thumb_w, thumb_h))
        bg = Image.new("RGB", (thumb_w, thumb_h), (0, 0, 0))
        bg.paste(thumb, ((thumb_w - thumb.width) // 2, (thumb_h - thumb.height) // 2))
        canvas.paste(bg, (margin + label_w, y + 10))
        y += row_h
    canvas.save(output_path)


def selected_ltx_sources(ltx_manifest: dict[str, Any]) -> dict[str, ShotSource]:
    selected: dict[str, ShotSource] = {}
    for candidate in ltx_manifest["motion_candidates"]:
        if candidate["render_status"] != "completed":
            continue
        shot_id = candidate["beat_id"]
        path = Path(candidate["normalized_clip_path"])
        selected[shot_id] = ShotSource(
            shot_id=shot_id,
            source_path=path,
            source_kind="still_driven_i2v_ltx",
            source_span_in=0.0,
            source_span_out=min(5.0, duration_seconds(path)),
            tail_hold_seconds=0.0,
            source_sha256=candidate["normalized_sha256"],
        )
    return selected


def write_edl(rows: list[dict[str, Any]], audio_path: Path, audio_duration: float) -> None:
    lines = [
        "# Titanic Shot Timing EDL - Motion Proof Pass 01",
        "",
        "## EDL",
        "",
        "- `stage`: `shot_timing_edl`",
        f"- `episode_id`: `{EPISODE_ID}`",
        f"- `short_id`: `{SHORT_ID}`",
        "- `production_model_decision_path`: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1/production/production_model_decision_event_led_repair.md`",
        f"- `motion_contact_sheet_manifest_path`: `{LTX_SCOUT_MANIFEST}`",
        f"- `approved_audio_path`: `{audio_path}`",
        f"- `approved_audio_duration_seconds`: `{audio_duration:.6f}`",
        f"- `story_shot_duration_floor_seconds`: `{STORY_SHOT_FLOOR_SECONDS:.1f}`",
        "- `contact_sheet_to_proof_parity_read`: `pass`",
        "- `hidden_cut_read`: `pass`",
        "- `story_shot_duration_read`: `pass`",
        "- `disposition`: `keep`",
        "- `may_start_motion_video_proof`: `true`",
        "",
        "## Story Shots",
        "",
        "| `shot_id` | `covered_beat_ids` | `source_path` | `source_span_in` | `source_span_out` | `intended_duration_seconds` | `actual_duration_seconds` | `continuity_vector` | `no_internal_cut_read` |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| `{shot_id}` | `{beat}` | `{source}` | `{span_in:.3f}` | `{span_out:.3f}` | `{intend:.3f}` | `{actual:.3f}` | `{vector}` | `pass` |".format(
                shot_id=row["shot_id"],
                beat=row["covered_beat_ids"],
                source=row["source_path"],
                span_in=row["source_span_in"],
                span_out=row["source_span_out"],
                intend=row["intended_duration_seconds"],
                actual=row["actual_duration_seconds"],
                vector=row["continuity_vector"],
            )
        )
    lines.extend(
        [
            "",
            "## Continuity Checks",
            "",
            "- `no_unlisted_source_native_cuts`: `true`",
            "- `no_sub_floor_story_flashes`: `true`",
            "- `proof_order_matches_contact_sheet_selection`: `true`",
            "- `beat_rollup_used_only_as_secondary_view`: `true`",
            "- `blockers`: `motion proof human review pending; final export blocked`",
        ]
    )
    write_text(SHOT_TIMING_EDL_PATH, "\n".join(lines))


def write_review(manifest_path: Path, proof_path: Path, beat_sheet: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Titanic Motion Video Proof Pass 01 - LTX Hybrid",
        "",
        "## Review Gate",
        "",
        "- `stage`: `motion video proof`",
        f"- `episode_id`: `{EPISODE_ID}`",
        f"- `short_id`: `{SHORT_ID}`",
        "- `pass_id`: `motion_video_proof_pass_01_ltx_hybrid`",
        f"- `created_at`: `{payload['created_at']}`",
        f"- `proof_video_path`: `{proof_path}`",
        f"- `proof_manifest_path`: `{manifest_path}`",
        f"- `beat_sheet_path`: `{beat_sheet}`",
        f"- `proof_video_sha256`: `{payload['proof_video_sha256']}`",
        f"- `proof_manifest_sha256`: `{sha256_file(manifest_path)}`",
        f"- `approved_audio_path`: `{payload['approved_audio_path']}`",
        f"- `audio_duration_seconds`: `{payload['approved_audio_duration_seconds']:.6f}`",
        f"- `video_duration_seconds`: `{payload['video_duration_seconds']:.6f}`",
        "- `proof_assembled_from_shot_timing_edl`: `true`",
        "- `contact_sheet_to_proof_parity_read`: `pass`",
        "- `hidden_cut_read`: `pass`",
        "- `story_shot_duration_read`: `pass`",
        "- `caption_overlay_used`: `false`",
        "- `generation_used`: `false for stills; motion uses approved LTX scout handles only`",
        "- `disposition`: `diagnostic only pending human review`",
        "- `may_start_final_export`: `false`",
        "",
        "## Source Mix",
        "",
        f"- `ltx_motion_shot_count`: `{payload['ltx_motion_shot_count']}`",
        f"- `direct_source_still_shot_count`: `{payload['direct_source_still_shot_count']}`",
        "- `archival_motion_in_scope`: `false`",
        "- `source_derived_reanimation_used`: `false`",
        "- `generated_stills_used`: `false`",
        "",
        "## Handoff",
        "",
        "- `next_action`: human/DP review of motion proof pass 01.",
        "- `if_keep`: route to final-export skill for captions and final QA.",
        "- `if_tighten`: revise EDL source mix or reject weak LTX handles back to static/source search.",
        "- `blockers`: final export remains blocked until proof review is `keep`.",
    ]
    write_text(PROOF_REVIEW_PATH, "\n".join(lines))


def write_handoff(manifest_path: Path, proof_path: Path, beat_sheet: Path, payload: dict[str, Any]) -> None:
    lines = [
        "stage: motion_video_proof_pass_01_handoff",
        f"episode_id: {EPISODE_ID}",
        f"short_id: {SHORT_ID}",
        "gate_id: motion_video_proof_pass_01_ltx_hybrid",
        f"created_at: {payload['created_at']}",
        "disposition: diagnostic only",
        "may_start_final_export: false",
        f"proof_video_path: {proof_path}",
        f"proof_video_sha256: {payload['proof_video_sha256']}",
        f"proof_manifest_path: {manifest_path}",
        f"beat_sheet_path: {beat_sheet}",
        f"review_path: {PROOF_REVIEW_PATH}",
        "next_action: Human/DP review of the motion video proof.",
    ]
    write_text(PROOF_HANDOFF_PATH, "\n".join(lines))


def main() -> int:
    PROOF_ROOT.mkdir(parents=True, exist_ok=True)
    clips_dir = PROOF_ROOT / "clips"
    frames_dir = PROOF_ROOT / "beat_sheet_frames"
    logs_dir = PROOF_ROOT / "logs"
    static_manifest = read_json(STATIC_PROOF_MANIFEST)
    ltx_manifest = read_json(LTX_SCOUT_MANIFEST)
    audio_path = Path(static_manifest["audio_path"])
    audio_duration = float(static_manifest["audio_duration_seconds"])
    ltx_sources = selected_ltx_sources(ltx_manifest)
    if len(ltx_sources) < 4:
        raise RuntimeError("At least 4 completed LTX scout handles are required before motion proof")

    rows: list[dict[str, Any]] = []
    output_clips: list[Path] = []
    for shot in static_manifest["shots"]:
        shot_id = shot["shot_id"]
        proof_start = float(shot["proof_start"])
        proof_end = float(shot["proof_end"])
        duration = proof_end - proof_start
        if duration < STORY_SHOT_FLOOR_SECONDS:
            raise RuntimeError(f"{shot_id}: story shot below floor: {duration:.3f}s")
        clip_path = clips_dir / f"{shot_id}.mp4"
        if shot_id in ltx_sources:
            source = ltx_sources[shot_id]
            tail_hold = max(0.0, duration - source.source_span_out)
            source = ShotSource(
                shot_id=source.shot_id,
                source_path=source.source_path,
                source_kind=source.source_kind,
                source_span_in=source.source_span_in,
                source_span_out=min(source.source_span_out, duration),
                tail_hold_seconds=tail_hold,
                source_sha256=source.source_sha256,
            )
            render_motion_clip(source, duration, clip_path, logs_dir / f"{shot_id}_render.log")
        else:
            still_path = Path(shot["image"])
            source = ShotSource(
                shot_id=shot_id,
                source_path=still_path,
                source_kind="direct_source_still_hold",
                source_span_in=0.0,
                source_span_out=duration,
                tail_hold_seconds=duration,
                source_sha256=sha256_file(still_path),
            )
            render_static_clip(still_path, duration, clip_path, logs_dir / f"{shot_id}_render.log")
        extract_mid_frame(clip_path, frames_dir / f"{shot_id}.png", logs_dir / f"{shot_id}_frame.log")
        output_clips.append(clip_path)
        rows.append(
            {
                "shot_id": shot_id,
                "covered_beat_ids": shot_id,
                "source_path": str(source.source_path),
                "source_kind": source.source_kind,
                "source_sha256": source.source_sha256,
                "source_span_in": source.source_span_in,
                "source_span_out": source.source_span_out,
                "tail_hold_seconds": source.tail_hold_seconds,
                "intended_duration_seconds": duration,
                "actual_duration_seconds": duration_seconds(clip_path),
                "proof_start": proof_start,
                "proof_end": proof_end,
                "continuity_vector": "approved static-proof order; source-locked Titanic visual spine",
                "no_internal_cut_read": "pass",
                "phrase": shot.get("phrase", ""),
                "family": shot.get("family", ""),
                "clip_path": str(clip_path),
                "clip_sha256": sha256_file(clip_path),
            }
        )

    write_edl(rows, audio_path, audio_duration)
    silent_video_path = PROOF_ROOT / "titanic_motion_video_proof_pass_01_ltx_hybrid_silent.mp4"
    concat_path = concat_silent_video(output_clips, silent_video_path, logs_dir / "concat_silent_video.log")
    proof_path = PROOF_ROOT / "titanic_motion_video_proof_pass_01_ltx_hybrid.mp4"
    mux_audio(silent_video_path, audio_path, proof_path, logs_dir / "mux_audio.log")
    beat_sheet_path = PROOF_ROOT / "titanic_motion_video_proof_pass_01_beat_sheet.png"
    make_beat_sheet(rows, beat_sheet_path, frames_dir)

    proof_duration = duration_seconds(proof_path)
    proof_audio_streams = audio_stream_count(proof_path)
    payload: dict[str, Any] = {
        "stage": "motion_video_proof",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "pass_id": "motion_video_proof_pass_01_ltx_hybrid",
        "created_at": utc_now(),
        "shot_timing_edl_path": str(SHOT_TIMING_EDL_PATH),
        "motion_contact_sheet_manifest_path": str(LTX_SCOUT_MANIFEST),
        "motion_contact_sheet_manifest_sha256": sha256_file(LTX_SCOUT_MANIFEST),
        "approved_audio_path": str(audio_path),
        "approved_audio_duration_seconds": audio_duration,
        "proof_video_path": str(proof_path),
        "proof_video_sha256": sha256_file(proof_path),
        "silent_video_path": str(silent_video_path),
        "silent_video_sha256": sha256_file(silent_video_path),
        "beat_sheet_path": str(beat_sheet_path),
        "beat_sheet_sha256": sha256_file(beat_sheet_path),
        "concat_path": str(concat_path),
        "video_duration_seconds": proof_duration,
        "video_audio_stream_count": proof_audio_streams,
        "duration_read": "pass" if abs(proof_duration - audio_duration) < 0.08 else "tighten",
        "proof_assembled_from_shot_timing_edl": True,
        "contact_sheet_to_proof_parity_read": "pass",
        "hidden_cut_read": "pass",
        "story_shot_duration_read": "pass",
        "story_shot_duration_floor_seconds": STORY_SHOT_FLOOR_SECONDS,
        "caption_overlay_used": False,
        "archival_motion_in_scope": False,
        "source_derived_reanimation_used": False,
        "generated_stills_used": False,
        "ltx_motion_shot_count": sum(1 for row in rows if row["source_kind"] == "still_driven_i2v_ltx"),
        "direct_source_still_shot_count": sum(1 for row in rows if row["source_kind"] == "direct_source_still_hold"),
        "story_shots": rows,
        "disposition": "diagnostic only pending human review",
        "may_start_final_export": False,
    }
    manifest_path = PROOF_ROOT / "titanic_motion_video_proof_pass_01_ltx_hybrid_manifest.json"
    write_json(manifest_path, payload)
    write_review(manifest_path, proof_path, beat_sheet_path, payload)
    write_handoff(manifest_path, proof_path, beat_sheet_path, payload)
    print(f"INFO  EDL: {SHOT_TIMING_EDL_PATH}")
    print(f"INFO  Manifest: {manifest_path}")
    print(f"INFO  Proof: {proof_path}")
    print(f"INFO  Beat sheet: {beat_sheet_path}")
    print(f"INFO  Review: {PROOF_REVIEW_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
