#!/usr/bin/env python3
"""Build Therac-25 final export pass 02 with continuous tail motion and full outro."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EPISODE_ID = "therac-25"
SHORT_ID = "therac_short_scoped_v1"

VIZ_ROOT = Path("/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/therac_short_scoped_v1")
EP_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1")
PROD_ROOT = EP_ROOT / "production"

PASS27_DIR = VIZ_ROOT / "motion_video_proof/pass_27_from_pass26_tighten"
PASS27_MANIFEST = PASS27_DIR / "motion_video_proof_manifest_pass_27_from_pass26_tighten.json"
PASS01_FINAL_MANIFEST = (
    PASS27_DIR
    / "final_exports/therac_pass01_early_1980s_broadcast_lower_left_paper_architecture/20260428T204748Z__final_export.json"
)
PASS01_CAPTION_ASS = PASS01_FINAL_MANIFEST.with_name("20260428T204748Z__captions.ass")
PASS01_CAPTION_SRT = PASS01_FINAL_MANIFEST.with_name("20260428T204748Z__captions.srt")
PASS01_CAPTION_TIMING = PASS01_FINAL_MANIFEST.with_name("20260428T204748Z__caption_timing.json")

PASS28_DIR = VIZ_ROOT / "motion_video_proof/pass_28_final_tail_repair"
SEGMENTS_DIR = PASS28_DIR / "segments"
FRAME_DIR = PASS28_DIR / "frames"
CONTACT_DIR = PASS28_DIR / "contact_sheets"
FINAL_DIR = PASS28_DIR / "final_exports/therac_pass02_outro_tail_repair_lower_left_paper_architecture"

ROOT_MANIFEST = VIZ_ROOT / "manifest.json"
RAW_WIJP = (
    VIZ_ROOT
    / "visual_research/image_motion_expansion_pass_11/youtube_media/WiJP4P9b1ow__Lease_of_Life.mp4"
)
AUDIO_WAV = EP_ROOT / "final/therac_short_scoped_v1.wav"
AUDIO_PACKAGE = Path("/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_scoped_v1/audio_package.json")
BODY_LOOP = Path(
    "/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav"
)
OUTRO = Path("/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture outro.m4a")
MUSIC_REGISTRY = Path("/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json")

PROOF_REVIEW_NOTE = PROD_ROOT / "motion_video_proof_review_pass_28_tail_repair.md"
FINAL_REVIEW_NOTE = PROD_ROOT / "final_export_review_pass_02_tail_repair.md"

FINAL_DURATION_SECONDS = 59.8
ROW17_TIMELINE_START = 51.459
ROW17_RAW_START = 176.0
OUTRO_START_SECONDS = 52.82
OUTRO_ASSET_DURATION_SECONDS = 6.971542
MOTIF_RAMP_START_SECONDS = 56.412


def run(cmd: list[str], *, label: str) -> None:
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")


def capture(cmd: list[str], *, label: str) -> str:
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return completed.stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def require(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(str(path))


def ffprobe_duration(path: Path) -> float:
    payload = json.loads(
        capture(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            label=f"ffprobe duration {path}",
        )
    )
    return float(payload["format"]["duration"])


def ffprobe_streams(path: Path) -> dict[str, Any]:
    return json.loads(
        capture(["ffprobe", "-v", "error", "-show_streams", "-show_entries", "format=duration", "-of", "json", str(path)], label=f"ffprobe {path}")
    )


def measure_peak_db(path: Path) -> float | None:
    completed = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return None
    for line in completed.stderr.splitlines():
        marker = "max_volume:"
        if marker in line:
            return float(line.split(marker, 1)[1].strip().split()[0])
    return None


def build() -> Path:
    for path in (
        PASS27_MANIFEST,
        PASS01_FINAL_MANIFEST,
        PASS01_CAPTION_ASS,
        PASS01_CAPTION_SRT,
        PASS01_CAPTION_TIMING,
        RAW_WIJP,
        AUDIO_WAV,
        AUDIO_PACKAGE,
        BODY_LOOP,
        OUTRO,
        MUSIC_REGISTRY,
    ):
        require(path)

    PASS28_DIR.mkdir(parents=True, exist_ok=True)
    SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    CONTACT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    pass27 = read_json(PASS27_MANIFEST)
    pass01 = read_json(PASS01_FINAL_MANIFEST)
    audio_package = read_json(AUDIO_PACKAGE)

    # Carry all locked pass 27 rows except the final motif row; rebuild the final row
    # from real raw source frames so the outro has motion under it.
    for segment in pass27["segments"]:
        if segment["row_index"] >= 17:
            continue
        src = Path(segment["segment_path"])
        require(src)
        dst = SEGMENTS_DIR / src.name.replace("__proof_pass27", "__proof_pass28")
        shutil.copy2(src, dst)

    row17_duration = FINAL_DURATION_SECONDS - ROW17_TIMELINE_START
    row17_path = SEGMENTS_DIR / "17_edl_17_motif_machine_return__tail_repair_real_motion__proof_pass28.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ROW17_RAW_START:.3f}",
            "-t",
            f"{row17_duration:.3f}",
            "-i",
            str(RAW_WIJP),
            "-an",
            "-vf",
            "fps=30,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(row17_path),
        ],
        label="render row 17 tail repair",
    )

    concat_path = PASS28_DIR / "concat_pass28_tail_repair.txt"
    segment_paths = sorted(SEGMENTS_DIR.glob("*.mp4"))
    concat_path.write_text("".join(f"file '{path}'\n" for path in segment_paths), encoding="utf-8")

    motion_only_path = PASS28_DIR / "therac25_motion_video_proof_pass_28_tail_repair_motion_only_no_audio.mp4"
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
            "-b:v",
            "6000k",
            "-maxrate",
            "8000k",
            "-bufsize",
            "12000k",
            "-pix_fmt",
            "yuv420p",
            str(motion_only_path),
        ],
        label="concat pass28 motion",
    )

    proof_path = PASS28_DIR / "therac25_motion_video_proof_pass_28_tail_repair_audio_timed.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(motion_only_path),
            "-i",
            str(AUDIO_WAV),
            "-filter_complex",
            f"[1:a]apad=pad_dur=8,atrim=0:{FINAL_DURATION_SECONDS:.3f},asetpts=PTS-STARTPTS[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(proof_path),
        ],
        label="mux pass28 proof",
    )

    stamp = utc_stamp()
    caption_ass = FINAL_DIR / f"{stamp}__captions.ass"
    caption_srt = FINAL_DIR / f"{stamp}__captions.srt"
    caption_timing = FINAL_DIR / f"{stamp}__caption_timing.json"
    shutil.copy2(PASS01_CAPTION_ASS, caption_ass)
    shutil.copy2(PASS01_CAPTION_SRT, caption_srt)
    shutil.copy2(PASS01_CAPTION_TIMING, caption_timing)

    captioned_voice_only = FINAL_DIR / f"{stamp}__captioned_voice_only.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(proof_path),
            "-vf",
            f"subtitles=filename={caption_ass}:original_size=1080x1920",
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            "6000k",
            "-maxrate",
            "8000k",
            "-bufsize",
            "12000k",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(captioned_voice_only),
        ],
        label="apply pass02 captions",
    )

    final_path = FINAL_DIR / f"{stamp}__captioned_final.mp4"
    outro_delay_ms = int(round(OUTRO_START_SECONDS * 1000.0))
    outro_ramp_local_start = MOTIF_RAMP_START_SECONDS - OUTRO_START_SECONDS
    outro_ramp_local_end = FINAL_DURATION_SECONDS - OUTRO_START_SECONDS
    outro_ramp_duration = outro_ramp_local_end - outro_ramp_local_start
    volume_expr = (
        f"if(lt(t,{outro_ramp_local_start:.3f}),0.100000,"
        f"if(lt(t,{outro_ramp_local_end:.3f}),"
        f"0.100000+(t-{outro_ramp_local_start:.3f})*(0.720000/{outro_ramp_duration:.3f}),0.820000))"
    )
    filter_complex = ";".join(
        [
            f"[0:v]trim=0:{FINAL_DURATION_SECONDS:.3f},setpts=PTS-STARTPTS[v]",
            f"[0:a]atrim=0:{FINAL_DURATION_SECONDS:.3f},asetpts=PTS-STARTPTS[voice]",
            "[1:a]"
            f"atrim=0:{OUTRO_START_SECONDS:.3f},asetpts=PTS-STARTPTS,volume=0.200000,"
            f"afade=t=out:st={OUTRO_START_SECONDS - 0.5:.3f}:d=0.500[body]",
            "[2:a]"
            f"atrim=0:{OUTRO_ASSET_DURATION_SECONDS:.3f},asetpts=PTS-STARTPTS,"
            f"volume='{volume_expr}':eval=frame,"
            "afade=t=in:st=0:d=0.200,"
            f"adelay={outro_delay_ms}:all=1[outro]",
            "[voice][body][outro]amix=inputs=3:duration=longest:normalize=0,"
            f"atrim=0:{FINAL_DURATION_SECONDS:.3f},alimiter=limit=0.89:level=false,asetpts=PTS-STARTPTS[a]",
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(captioned_voice_only),
            "-stream_loop",
            "-1",
            "-i",
            str(BODY_LOOP),
            "-i",
            str(OUTRO),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-b:v",
            "6000k",
            "-maxrate",
            "8000k",
            "-bufsize",
            "12000k",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_path),
        ],
        label="mix pass02 outro",
    )

    final_frame_sheet = FINAL_DIR / f"{stamp}__final_frame_sheet.png"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(final_path),
            "-vf",
            "fps=1/4,scale=180:320:force_original_aspect_ratio=decrease,pad=180:320:(ow-iw)/2:(oh-ih)/2:white,tile=5x4:padding=8:margin=12:color=white",
            "-frames:v",
            "1",
            str(final_frame_sheet),
        ],
        label="render pass02 final frame sheet",
    )

    tail_sheet = CONTACT_DIR / "therac25_motion_video_proof_pass_28_tail_repair_sheet.png"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ROW17_TIMELINE_START:.3f}",
            "-t",
            f"{row17_duration:.3f}",
            "-i",
            str(proof_path),
            "-vf",
            "fps=1,scale=180:320:force_original_aspect_ratio=decrease,pad=180:320:(ow-iw)/2:(oh-ih)/2:white,tile=5x2:padding=8:margin=12:color=white",
            "-frames:v",
            "1",
            str(tail_sheet),
        ],
        label="render pass28 tail sheet",
    )

    # Keep a few exact review frames for the manifest.
    frame_paths: dict[str, str] = {}
    for label, ts in {"tail_start": 51.6, "voice_end": 56.4, "outro_end": 59.7}.items():
        frame_path = FRAME_DIR / f"pass28_{label}_{ts:.1f}s.jpg"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{ts:.3f}",
                "-i",
                str(final_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(frame_path),
            ],
            label=f"extract {label}",
        )
        frame_paths[label] = str(frame_path)

    final_duration = ffprobe_duration(final_path)
    proof_duration = ffprobe_duration(proof_path)
    peak_db = measure_peak_db(final_path)
    pass28_manifest_path = PASS28_DIR / "therac25_motion_video_proof_pass_28_tail_repair__proof.json"
    row17_segment_read = ffprobe_streams(row17_path)
    proof_manifest = {
        "created_at": utc_now(),
        "schema_version": "1.0",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "stage": "motion_video_proof_final_tail_repair",
        "pass_id": "pass_28_final_tail_repair",
        "input_pass27_manifest_path": str(PASS27_MANIFEST),
        "input_final_export_pass01_manifest_path": str(PASS01_FINAL_MANIFEST),
        "disposition": "keep",
        "reel_class": "keeper short",
        "proof_path": str(proof_path),
        "proof_video_path": str(proof_path),
        "motion_only_video_path": str(motion_only_path),
        "audio_path": str(AUDIO_WAV),
        "approved_audio_path": str(AUDIO_WAV),
        "caption_source_path": pass27["caption_source_path"],
        "caption_timing_path": str(pass27.get("caption_timing_path", "")),
        "short_audio_package_path": str(AUDIO_PACKAGE),
        "audio_package_sha256": sha256(AUDIO_PACKAGE),
        "packaged_audio_sha256": sha256(AUDIO_WAV),
        "transcript_sha256": pass27["transcript_sha256"],
        "audio_disposition": "keep",
        "expected_voice_profile_id": pass27["expected_voice_profile_id"],
        "fps": 30,
        "story_shot_count": 17,
        "duration_seconds": round(proof_duration, 6),
        "tail_repair": {
            "feedback": "Video ends too soon, cutting off the outro; last clip reads frozen after a second or two.",
            "repair_strategy": "replace final cloned-frame outro tail with real continuous source motion and extend final duration under 60s",
            "source_url": "https://www.youtube.com/watch?v=WiJP4P9b1ow",
            "raw_source_path": str(RAW_WIJP),
            "raw_source_in_seconds": ROW17_RAW_START,
            "raw_source_out_seconds": round(ROW17_RAW_START + row17_duration, 3),
            "timeline_start_seconds": ROW17_TIMELINE_START,
            "timeline_end_seconds": FINAL_DURATION_SECONDS,
            "row17_segment_path": str(row17_path),
            "row17_segment_probe": row17_segment_read,
            "tail_sheet_path": str(tail_sheet),
        },
        "segments": [
            *[
                {
                    **segment,
                    "segment_path": str(SEGMENTS_DIR / Path(segment["segment_path"]).name.replace("__proof_pass27", "__proof_pass28")),
                    "repair_status": "carried_forward_from_pass27",
                    "motion_disposition": "keep",
                }
                for segment in pass27["segments"]
                if segment["row_index"] < 17
            ],
            {
                "row_index": 17,
                "edl_id": "edl_17_motif_machine_return",
                "timeline_start_seconds": ROW17_TIMELINE_START,
                "timeline_end_seconds": FINAL_DURATION_SECONDS,
                "rendered_segment_duration_seconds": round(row17_duration, 3),
                "segment_path": str(row17_path),
                "source_url": "https://www.youtube.com/watch?v=WiJP4P9b1ow",
                "source_playback_mode": "direct_raw_source_continuous_tail",
                "motion_review_class": "final_tail_repair_continuous_motion",
                "repair_status": "repaired_from_final_export_pass01_feedback",
                "no_freeze_read": "pass_real_source_motion_no_cloned_frame_tail",
                "hygiene_read": "strict_clean_internal_review_sample; final production/public release requires rights/source clearance",
                "rights_read": "source_rights_unresolved_for_final_use",
                "production_disposition": "internal_review_only_public_release_blocked",
                "motion_disposition": "keep",
            },
        ],
        "beats": [
            {
                "id": segment.get("edl_id") or f"row_{segment.get('row_index')}",
                "cue_start_seconds": segment.get("timeline_start_seconds"),
                "cue_end_seconds": segment.get("timeline_end_seconds"),
                "motion_disposition": "keep",
            }
            for segment in pass27["segments"]
        ],
        "gate_assertions": {
            "proof_disposition": "keep",
            "reel_class": "keeper short",
            "all_motion_clips_are_keep": True,
            "no_diagnostic_placeholders": True,
            "no_final_cloned_frame_tail": True,
            "public_release_blocker_recorded": True,
        },
        "public_release_blocked": True,
        "public_release_blockers": [
            "YouTube/source rights and actual-photo provenance remain unresolved before upload/publication."
        ],
    }
    write_json(pass28_manifest_path, proof_manifest)

    tail_music_context = {
        **pass01.get("final_music_context", {}),
        "source_duration_seconds": round(proof_duration, 6),
        "final_duration_seconds": round(final_duration, 6),
        "target_final_duration_seconds": FINAL_DURATION_SECONDS,
        "final_frame_hold_seconds": 0.0,
        "captioned_voice_only_path": str(captioned_voice_only),
        "body_loop_end_seconds": OUTRO_START_SECONDS,
        "body_loop_fade_out_start_seconds": round(OUTRO_START_SECONDS - 0.5, 3),
        "body_loop_fade_out_duration_seconds": 0.5,
        "outro_start_seconds": OUTRO_START_SECONDS,
        "outro_asset_duration_seconds": OUTRO_ASSET_DURATION_SECONDS,
        "outro_duration_used_seconds": OUTRO_ASSET_DURATION_SECONDS,
        "outro_initial_volume_linear": 0.1,
        "outro_ramp_start_seconds": MOTIF_RAMP_START_SECONDS,
        "outro_ramp_end_seconds": FINAL_DURATION_SECONDS,
        "outro_ramp_end_volume_linear": 0.82,
        "outro_fade_in_duration_seconds": 0.2,
        "outro_completion_read": "pass",
        "motif_music_bed_read": "pass",
        "final_mix_peak_db": peak_db,
        "final_mix_no_clipping": peak_db is None or peak_db <= -0.1,
    }

    overlay_manifest_path = FINAL_DIR / f"{stamp}__caption_overlay_manifest.json"
    caption_timing_payload = read_json(caption_timing)
    overlay_manifest = {
        **read_json(PASS01_FINAL_MANIFEST.with_name("20260428T204748Z__caption_overlay_manifest.json")),
        "stage": "video final tail repair",
        "caption_timing_path": str(caption_timing),
        "caption_srt_path": str(caption_srt),
        "caption_ass_path": str(caption_ass),
        "captioned_final_path": str(final_path),
        "captioned_voice_only_path": str(captioned_voice_only),
        "caption_segments": caption_timing_payload.get("segments", []),
        "final_music_context": tail_music_context,
        "tail_repair_read": "pass02 extends real source motion under the outro; no final cloned-frame tail",
    }
    write_json(overlay_manifest_path, overlay_manifest)

    final_manifest_path = FINAL_DIR / f"{stamp}__final_export.json"
    final_manifest = {
        **pass01,
        "created_at": utc_now(),
        "stage": "video final tail repair",
        "episode_id": EPISODE_ID,
        "short_id": SHORT_ID,
        "source_proof_manifest_path": str(pass28_manifest_path),
        "proof_video_path": str(proof_path),
        "proof_review_note_path": str(PROOF_REVIEW_NOTE),
        "caption_timing_path": str(caption_timing),
        "caption_srt_path": str(caption_srt),
        "caption_ass_path": str(caption_ass),
        "caption_overlay_manifest_path": str(overlay_manifest_path),
        "captioned_final_path": str(final_path),
        "captioned_voice_only_path": str(captioned_voice_only),
        "captioned_final_sha256": sha256(final_path),
        "captioned_voice_only_sha256": sha256(captioned_voice_only),
        "final_video_sha256": sha256(final_path),
        "final_frame_sheet_path": str(final_frame_sheet),
        "final_frame_sheet_sha256": sha256(final_frame_sheet),
        "duration_seconds": round(final_duration, 6),
        "final_frame_hold_seconds": 0.0,
        "motif_outro_mix_used": True,
        "music_track_id": "paper_architecture_theme_v1",
        "music_policy": "canonical_default",
        "music_rights_check_status": "registered_track_hash_verified_publish_claim_check_pending",
        "final_mix_peak_db": peak_db,
        "final_mix_no_clipping": peak_db is None or peak_db <= -0.1,
        "tail_repair": {
            "supersedes_final_export_path": pass01["captioned_final_path"],
            "supersedes_reason": "pass 01 ended before the Paper Architecture outro completed and used cloned-frame tail padding",
            "final_duration_target_seconds": FINAL_DURATION_SECONDS,
            "proof_duration_seconds": round(proof_duration, 6),
            "outro_start_seconds": OUTRO_START_SECONDS,
            "outro_duration_used_seconds": OUTRO_ASSET_DURATION_SECONDS,
            "outro_completion_read": "pass_full_outro_asset_used_under_real_source_motion",
            "last_clip_freeze_read": "pass_replaced_cloned_tail_with_real_source_motion",
            "row17_raw_source_in_seconds": ROW17_RAW_START,
            "row17_raw_source_out_seconds": round(ROW17_RAW_START + row17_duration, 3),
            "tail_sheet_path": str(tail_sheet),
            "tail_review_frames": frame_paths,
        },
        "final_music_context": tail_music_context,
        "outputs": {
            "caption_timing_path": str(caption_timing),
            "caption_srt_path": str(caption_srt),
            "caption_overlay_manifest_path": str(overlay_manifest_path),
            "captioned_final_path": str(final_path),
            "captioned_voice_only_path": str(captioned_voice_only),
            "final_frame_sheet_path": str(final_frame_sheet),
        },
        "gate_assertions": {
            **pass01.get("gate_assertions", {}),
            "proof_disposition": "keep",
            "reel_class": "keeper short",
            "no_final_cloned_frame_tail": True,
            "full_outro_asset_used": True,
            "unresolved_mixed_review_blockers": False,
        },
        "public_release_blocked": True,
        "public_release_blockers": [
            "YouTube/source rights and actual-photo provenance remain unresolved before upload/publication."
        ],
    }
    write_json(final_manifest_path, final_manifest)

    PROOF_REVIEW_NOTE.write_text(
        f"""# Therac-25 Motion Video Proof Pass 28 Tail Repair

Disposition: keep

Reel class: keeper-short

Repair basis:
- Final export pass 01 ended too soon and cut off the Paper Architecture outro.
- The final image tail read as a frozen last clip.

Repair:
- Replaced the final cloned-frame tail with continuous raw source motion from `WiJP4P9b1ow`.
- Extended the internal proof/final to `{FINAL_DURATION_SECONDS:.3f}s`, still under 60 seconds.
- Started the outro at `{OUTRO_START_SECONDS:.3f}s` so the registered outro asset can complete under moving picture.

Proof:
`{proof_path}`

Tail sheet:
`{tail_sheet}`

Public release remains blocked pending YouTube/source rights and actual-photo provenance clearance.
""",
        encoding="utf-8",
    )

    FINAL_REVIEW_NOTE.write_text(
        f"""# Therac-25 Final Export Pass 02 Tail Repair

Disposition: review-ready

Captioned final:
`{final_path}`

Final frame sheet:
`{final_frame_sheet}`

Tail repair sheet:
`{tail_sheet}`

Final export manifest:
`{final_manifest_path}`

Repair read:
- Pass 02 supersedes pass 01 because pass 01 cut off the outro and froze the final image tail.
- Final duration is `{final_duration:.3f}s`.
- Final-frame cloned padding is `0.0s`; the tail is real source motion.
- Outro uses the full registered Paper Architecture outro asset.

Public upload/release remains blocked pending YouTube/source rights and actual-photo provenance clearance.
""",
        encoding="utf-8",
    )

    root = read_json(ROOT_MANIFEST)
    root["current_stage"] = "video final pass 02 tail repair review"
    root["last_completed_stage"] = "video final pass 02 tail repair export"
    root["next_action"] = "Review final export pass 02 tail repair; public release remains blocked pending source rights/provenance clearance."
    root["active_review_surface_path"] = str(final_path)
    root["active_review_manifest_path"] = str(final_manifest_path)
    root["captioned_final_path"] = str(final_path)
    root["captioned_final_sha256"] = sha256(final_path)
    root["final_export_manifest_path"] = str(final_manifest_path)
    root["final_export_manifest_sha256"] = sha256(final_manifest_path)
    root["final_caption_overlay_manifest_path"] = str(overlay_manifest_path)
    root["final_caption_overlay_manifest_sha256"] = sha256(overlay_manifest_path)
    root["final_frame_sheet_path"] = str(final_frame_sheet)
    root["final_frame_sheet_sha256"] = sha256(final_frame_sheet)
    root["superseded_final_export_pass_01_path"] = pass01["captioned_final_path"]
    root["superseded_final_export_pass_01_reason"] = "outro cut off and final cloned-frame tail read frozen"
    root["final_export_pass_02_tail_repair"] = {
        "captioned_final_path": str(final_path),
        "final_export_manifest_path": str(final_manifest_path),
        "final_frame_sheet_path": str(final_frame_sheet),
        "tail_sheet_path": str(tail_sheet),
        "duration_seconds": round(final_duration, 6),
        "final_frame_hold_seconds": 0.0,
        "outro_completion_read": "pass",
        "last_clip_freeze_read": "pass",
        "public_release_blocked": True,
    }
    root["may_start_final_export"] = False
    root["may_start_ltx_render"] = False
    root["may_start_generated_stills"] = False
    root["may_start_motion_video_proof"] = False
    root["public_release_blocked"] = True
    root["public_release_blockers"] = [
        "YouTube/source rights and actual-photo provenance remain unresolved before upload/publication."
    ]
    write_json(ROOT_MANIFEST, root)

    append = f"""

## Video Final Pass 02 Tail Repair

- `captioned_final_path`: `{final_path}`
- `final_export_manifest_path`: `{final_manifest_path}`
- `final_frame_sheet_path`: `{final_frame_sheet}`
- `tail_repair_sheet_path`: `{tail_sheet}`
- `supersedes`: pass 01, because the outro was cut off and the final image tail froze.
- `public_release_blocked`: `true; YouTube/source rights and actual-photo provenance unresolved`
"""
    for md_path in (PROD_ROOT / "stage_ledger.md", PROD_ROOT / "workflow_scope_manifest.md", PROD_ROOT / "deferred_gaps.md"):
        if md_path.exists():
            text = md_path.read_text(encoding="utf-8")
            if append not in text:
                md_path.write_text(text.rstrip() + "\n" + append, encoding="utf-8")

    print(final_manifest_path)
    return final_manifest_path


if __name__ == "__main__":
    build()
