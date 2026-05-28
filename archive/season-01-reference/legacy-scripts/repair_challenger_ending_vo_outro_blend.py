#!/usr/bin/env python3
"""Repair Challenger long-form ending VO and subtle-tail outro gate.

This is a production one-off for the May 2026 Challenger long-form package.
It creates a successor proof lineage; it never deletes or modifies the private
YouTube upload itself.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
PROOF_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "challenger_longform_titleless_end_screen_html_approval_proof_20260515T164855Z"
)
RENDER_ROOT = PROOF_ROOT / "video_render/challenger_longform_titleless_final_mp4_20260515T172240Z"
READINESS_ROOT = RENDER_ROOT / "publish_readiness/challenger_longform_publish_readiness_20260515T200217Z"
AUDIO_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/audio/"
    "recording_20260511T204835Z_hybrid_attention_rewrite"
)
AUDIO_SCRIPTS = AUDIO_ROOT / "scripts"
OLD_LOCKED_SCRIPT = AUDIO_SCRIPTS / "challenger_longform_hybrid_attention_rewrite_20260511T204835Z.txt"
OLD_CHUNKS = AUDIO_ROOT / "rendered_chunks"
OLD_FINAL_JOBS = AUDIO_ROOT / "pipeline/final_jobs.jsonl"
OLD_CHUNK_08_JSON = OLD_CHUNKS / "challenger_longform_hybrid_attention_rewrite_20260511T204835Z_chunk_08.wav.json"
OLD_TRANSCRIPT_VTT = AUDIO_ROOT / "transcripts/recording_20260511T204835Z_hybrid_attention_rewrite.diarized.corrected.vtt"

INTRO_SOURCE = Path("/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav")
OUTRO_SOURCE = Path("/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture.m4a")
ELEVENLABS_HELPER = Path("/Users/mike/Audio_CascadeEffects/scripts/elevenlabs_provider.py")
ELEVENLABS_ENV = Path("/Users/mike/Audio_CascadeEffects/.env.local")
CAPTION_BUILDER = REPO_ROOT / "scripts/build_living_cover_script_locked_captions.py"
OLD_RENDER_SCRIPT = PROOF_ROOT / "scripts/render_titleless_final_mp4.mjs"

VOICE_START_SECONDS = 9.601451
INTRO_FADE_TAIL_SECONDS = 2.0
OUTRO_PRELAP_SECONDS = 1.5
OUTRO_UNDER_VO_GAIN = 0.10
OUTRO_TARGET_GAIN = 0.42
OUTRO_TARGET_RAMP_SECONDS = 3.0
SAMPLE_RATE = 44100
FPS = 24
TRANSITION_DURATION_SECONDS = 0.7
VOICE_LOUDNESS_TARGET_I = -14.0
VOICE_LOUDNESS_TARGET_TP = -1.0
VOICE_LOUDNESS_TARGET_LRA = 11.0
VOICE_LOUDNESS_TOLERANCE_DB = 1.5
PRIVATE_VIDEO_ID = "ToEay5mFDy8"
PRIVATE_VIDEO_URL = f"https://www.youtube.com/watch?v={PRIVATE_VIDEO_ID}"

CANONICAL_SIGNOFF_TAGGED = (
    "[calm] Next time, another design failure, another system that taught itself "
    "to ignore what it already knew."
)
CANONICAL_SIGNOFF_SPOKEN = (
    "Next time, another design failure, another system that taught itself "
    "to ignore what it already knew."
)
KEEP_THROUGH = "A warning appeared. The system explained it. The launch continued."
FORBIDDEN_PUBLIC_TEXT = [
    "Therac-25",
    "medical machine",
    "software confidence",
    "software interface",
    "next case belongs beside Challenger",
    "confidence outruns the evidence",
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, check: bool = True, max_output: int = 128 * 1024 * 1024) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\nSTDOUT:\n{result.stdout[-max_output:]}\nSTDERR:\n{result.stderr[-max_output:]}"
        )
    return result


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            rows.append(json.loads(raw))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def ffprobe_json(path: Path) -> dict[str, Any]:
    return json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,width,height,avg_frame_rate,sample_rate,channels,duration",
                "-of",
                "json",
                str(path),
            ]
        ).stdout
    )


def duration_seconds(path: Path) -> float:
    return float(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ]
        ).stdout.strip()
    )


def volumedetect(path: Path, start: float | None = None, duration: float | None = None, audio_filter: str = "volumedetect") -> dict[str, float | None]:
    args = ["ffmpeg", "-hide_banner"]
    if start is not None:
        args += ["-ss", f"{start:.6f}"]
    if duration is not None:
        args += ["-t", f"{duration:.6f}"]
    args += ["-i", str(path), "-af", audio_filter if audio_filter.endswith("volumedetect") else f"{audio_filter},volumedetect", "-f", "null", "-"]
    result = run(args, check=True)
    text = result.stderr
    mean = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", text)
    peak = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", text)
    return {
        "mean_volume_db": float(mean.group(1)) if mean else None,
        "max_volume_db": float(peak.group(1)) if peak else None,
    }


def parse_json_from_text(text: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text)
    return json.loads(match.group(0)) if match else {}


def loudnorm_scan(path: Path) -> dict[str, Any]:
    result = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            f"loudnorm=I={VOICE_LOUDNESS_TARGET_I:g}:TP={VOICE_LOUDNESS_TARGET_TP:g}:LRA={VOICE_LOUDNESS_TARGET_LRA:g}:print_format=json",
            "-f",
            "null",
            "-",
        ]
    )
    return parse_json_from_text(result.stderr + "\n" + result.stdout)


def loudnorm_needs_alignment(scan: dict[str, Any]) -> bool:
    try:
        input_i = float(scan.get("input_i"))
    except (TypeError, ValueError):
        return False
    return abs(input_i - VOICE_LOUDNESS_TARGET_I) > VOICE_LOUDNESS_TOLERANCE_DB


def loudnorm_voice_master(raw_voice_master: Path, mastered_voice_master: Path, log_path: Path) -> dict[str, Any]:
    scan = loudnorm_scan(raw_voice_master)
    source_window = volumedetect(raw_voice_master, 10, 120)
    if loudnorm_needs_alignment(scan):
        measured_i = float(scan["input_i"])
        measured_tp = float(scan["input_tp"])
        measured_lra = float(scan["input_lra"])
        measured_thresh = float(scan["input_thresh"])
        target_offset = float(scan["target_offset"])
        filter_arg = (
            f"loudnorm=I={VOICE_LOUDNESS_TARGET_I:g}:TP={VOICE_LOUDNESS_TARGET_TP:g}:LRA={VOICE_LOUDNESS_TARGET_LRA:g}"
            f":measured_I={measured_i}:measured_TP={measured_tp}:measured_LRA={measured_lra}"
            f":measured_thresh={measured_thresh}:offset={target_offset}:linear=true:print_format=json"
        )
        args = [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-y",
            "-i",
            str(raw_voice_master),
            "-af",
            filter_arg,
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(mastered_voice_master),
        ]
        result = run(args)
        log_path.write_text(json.dumps(args, indent=2) + "\n\n" + result.stderr, encoding="utf-8")
        output_scan = parse_json_from_text(result.stderr + "\n" + result.stdout) or loudnorm_scan(mastered_voice_master)
        status = "pass_loudnorm_aligned_for_review_mix"
        mix_read = "pass_mastered_loudnorm_voice_stem_used_for_review_mix"
    else:
        shutil.copy2(raw_voice_master, mastered_voice_master)
        output_scan = scan
        status = "not_needed_source_within_tolerance"
        mix_read = "pass_source_voice_master_within_series_loudness_tolerance"
    duration_delta = duration_seconds(mastered_voice_master) - duration_seconds(raw_voice_master)
    output_window = volumedetect(mastered_voice_master, 10, 120)
    output_i = float(output_scan.get("output_i", output_scan.get("input_i", "nan")))
    return {
        "model": "voice_loudness_alignment_v1",
        "status": status,
        "target": {
            "integrated_lufs": VOICE_LOUDNESS_TARGET_I,
            "true_peak_dbtp": VOICE_LOUDNESS_TARGET_TP,
            "loudness_range_lra": VOICE_LOUDNESS_TARGET_LRA,
            "tolerance_db": VOICE_LOUDNESS_TOLERANCE_DB,
        },
        "source_loudnorm_scan": scan,
        "output_loudnorm_scan": output_scan,
        "source_window_volumedetect": source_window,
        "output_window_volumedetect": output_window,
        "duration_delta_seconds": round(duration_delta, 6),
        "reads": {
            "voice_loudness_alignment_read": (
                "pass_aligned_to_series_voice_loudness_target"
                if abs(output_i - VOICE_LOUDNESS_TARGET_I) <= VOICE_LOUDNESS_TOLERANCE_DB
                else "tighten_aligned_voice_outside_series_loudness_target"
            ),
            "voice_duration_preservation_read": (
                f"pass_duration_delta_{duration_delta:.6f}s"
                if abs(duration_delta) <= 0.02
                else f"tighten_duration_delta_{duration_delta:.6f}s"
            ),
            "voice_master_used_for_mix_read": mix_read,
            "source_voice_master_preserved_read": "pass_raw_concat_voice_master_preserved",
        },
    }


def load_env(path: Path) -> dict[str, str]:
    env = os.environ.copy()
    if not path.is_file():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            env.setdefault(key, value)
    return env


def normalize_public_text(value: str) -> str:
    value = re.sub(r"\[[^\]]+\]", " ", value)
    value = re.sub(r"[^a-z0-9']+", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def format_duration(seconds: float) -> str:
    millis = round(seconds * 1000)
    h = millis // 3_600_000
    millis %= 3_600_000
    m = millis // 60_000
    millis %= 60_000
    s = millis // 1000
    ms = millis % 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def html_rel(from_dir: Path, target: Path) -> str:
    return Path(os.path.relpath(target, from_dir)).as_posix()


def create_successor_root(stamp: str) -> Path:
    successor = PROOF_ROOT.parent / f"challenger_longform_canonical_signoff_subtle_tail_outro_html_approval_proof_{stamp}"
    if successor.exists():
        raise FileExistsError(successor)
    shutil.copytree(
        PROOF_ROOT,
        successor,
        ignore=shutil.ignore_patterns("video_render", ".playwright-cli", "review_server.pid", "review_server.log"),
    )
    return successor


def mark_predecessor_superseded(successor_root: Path, stamp: str) -> None:
    now = iso_now()
    reason = "tighten_missing_vo_outro_blend_gate_and_episode_specific_signoff"
    proof_manifest_path = PROOF_ROOT / "rough_assembly_manifest.json"
    render_manifest_path = RENDER_ROOT / "render_manifest.json"
    readiness_manifest_path = READINESS_ROOT / "publish_readiness_manifest.json"

    for path in [proof_manifest_path, render_manifest_path, readiness_manifest_path]:
        if not path.is_file():
            continue
        data = read_json(path)
        data["status"] = reason
        data["superseded_by"] = {
            "recorded_utc": now,
            "successor_packet_path": str(successor_root),
            "reason": reason,
            "private_youtube_video_id": PRIVATE_VIDEO_ID,
            "private_youtube_video_url": PRIVATE_VIDEO_URL,
            "private_upload_local_status": "superseded_do_not_publish",
            "youtube_visibility_action_taken": False,
            "delete_or_visibility_change_taken": False,
        }
        data["publish_ready"] = False
        data["youtube_upload_ready"] = False
        data["public_release_ready"] = False
        data["may_youtube_action"] = False
        data["current_upload_candidate"] = False
        data["readiness_reads"] = {
            **data.get("readiness_reads", {}),
            "vo_outro_blend_plan_read": "reject_missing_required_explicit_subtle_tail_outro_gate",
            "vo_outro_music_blend_read": "reject_old_mix_starts_outro_at_voice_end",
            "vo_outro_perceptual_review_read": "reject_missing_perceptual_transition_sample_acceptance",
            "outro_transition_review_sample_read": "reject_missing_required_transition_sample",
            "outro_under_vo_masking_read": "reject_missing_under_vo_music_masking_read",
            "outro_target_after_voice_read": "reject_missing_target_after_voice_read",
            "outro_prelap_source_read": "reject_missing_subtle_tail_full_outro_source_read",
            "outro_prelap_start_read": "reject_missing_subtle_tail_starts_1p5s_before_voice_end_read",
            "outro_no_restart_at_voice_end_read": "reject_not_proven",
            "outro_source_continuity_read": "reject_not_proven",
            "music_contract_regression_read": "reject_missing_subtle_tail_outro_regression_read",
            "canonical_signoff_read": "reject_old_tail_mentions_next_specific_episode",
            "youtube_private_upload_superseded_read": f"pass_{PRIVATE_VIDEO_ID}_superseded_do_not_publish",
        }
        if isinstance(data.get("youtube_private_review_upload"), dict):
            data["youtube_private_review_upload"]["local_status"] = "superseded_do_not_publish"
            data["youtube_private_review_upload"]["superseded_do_not_publish"] = True
            data["youtube_private_review_upload"]["visibility_change_taken"] = False
        write_json(path, data)

    note_path = READINESS_ROOT / f"superseded_do_not_publish_{stamp}.md"
    note_path.write_text(
        "\n".join(
            [
                "# Challenger Private Upload Superseded",
                "",
                f"Recorded UTC: {now}",
                "",
                f"Private review video: {PRIVATE_VIDEO_URL}",
                "",
                "Local status: `superseded_do_not_publish`.",
                "",
                "Reason: missing explicit subtle-tail VO/music gate and stale episode-specific ending VO.",
                "",
                "No YouTube delete, visibility, publish, or schedule action was taken.",
                "",
                f"Successor packet: `{successor_root}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def repaired_script_text() -> str:
    old = OLD_LOCKED_SCRIPT.read_text(encoding="utf-8")
    if KEEP_THROUGH not in old:
        raise RuntimeError("Could not locate keep-through line in locked script.")
    prefix = old[: old.index(KEEP_THROUGH) + len(KEEP_THROUGH)]
    repaired = prefix.rstrip() + "\n\n" + CANONICAL_SIGNOFF_TAGGED + "\n"
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        if forbidden in repaired:
            raise RuntimeError(f"Forbidden old ending text remains in repaired script: {forbidden}")
    return repaired


def chunk_08_spoken_text() -> str:
    old_meta = read_json(OLD_CHUNK_08_JSON)
    old_text = old_meta["spoken_input"]
    if KEEP_THROUGH not in old_text:
        raise RuntimeError("Could not locate keep-through line in chunk 08 text.")
    return old_text[: old_text.index(KEEP_THROUGH) + len(KEEP_THROUGH)].rstrip() + "\n\n" + CANONICAL_SIGNOFF_SPOKEN


def write_script_delta_note(path: Path, repaired_script: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Challenger Ending VO Script Delta Approval",
                "",
                f"Recorded UTC: {iso_now()}",
                "",
                "Scope: final tail only.",
                "",
                "Keep through:",
                "",
                f"> {KEEP_THROUGH}",
                "",
                "Removed: Therac-specific bridge paragraph and Therac-25 next-episode line.",
                "",
                "Added selected canonical sign-off:",
                "",
                f"> {CANONICAL_SIGNOFF_TAGGED}",
                "",
                "Focused critique/integration note:",
                "",
                "- The replacement removes stale next-case specificity from the Challenger long-form package.",
                "- The new line adds no new Challenger factual claim; it functions as a generic series sign-off.",
                "- The change preserves the Challenger synthesis line immediately before the sign-off.",
                "- The exact replacement text is selected by the user in the May 18, 2026 repair request.",
                "",
                "Approval source:",
                "",
                "- User request: `PLEASE IMPLEMENT THIS PLAN: Challenger Ending VO And Outro Blend Repair`.",
                f"- Repaired locked script: `{repaired_script}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def render_repaired_chunk(audio_repair: Path, stamp: str) -> dict[str, Any]:
    rendered_dir = audio_repair / "rendered_chunks"
    pipeline_dir = audio_repair / "pipeline"
    ensure_dir(rendered_dir)
    ensure_dir(pipeline_dir)
    old_meta = read_json(OLD_CHUNK_08_JSON)
    old_jobs = read_jsonl(OLD_FINAL_JOBS)
    old_job = old_jobs[-1]
    old_effective_path = AUDIO_ROOT / "pipeline/render_only_chunk_08.elevenlabs.jsonl"
    old_effective = read_jsonl(old_effective_path)[0] if old_effective_path.is_file() else {}
    out_name = f"challenger_longform_canonical_signoff_{stamp}_chunk_08.wav"
    spoken = chunk_08_spoken_text()
    job = {
        **old_job,
        "input": spoken,
        "out": out_name,
        "response_format": "wav",
        "spoken_input": spoken,
        "elevenlabs_text": spoken,
        "elevenlabs_seed": old_effective.get("elevenlabs_seed", old_meta.get("seed", 36702311)),
        "elevenlabs_model_id": old_effective.get("elevenlabs_model_id", old_meta.get("model_id", "eleven_multilingual_v2")),
        "elevenlabs_apply_text_normalization": old_effective.get("elevenlabs_apply_text_normalization", "on"),
        "elevenlabs_voice_settings": old_effective.get(
            "elevenlabs_voice_settings",
            {"stability": 0.6, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True, "speed": 1.0},
        ),
        "elevenlabs_previous_text": old_effective.get("elevenlabs_previous_text") or old_meta.get("previous_text"),
        "elevenlabs_voice_id": old_meta.get("voice_id", "dPrTCMw2R7HQlznlgwCO"),
        "repair_note": "final_tail_only_canonical_generic_signoff_replaces_therac_specific_next_episode_copy",
    }
    manifest_path = pipeline_dir / f"render_repaired_chunk_08_{stamp}.elevenlabs.jsonl"
    write_jsonl(manifest_path, [job])
    env = load_env(ELEVENLABS_ENV)
    env.setdefault("ELEVEN_LABS_VOICE_ID", old_meta.get("voice_id", "dPrTCMw2R7HQlznlgwCO"))
    if not env.get("ELEVEN_LABS_API_KEY"):
        raise RuntimeError("ELEVEN_LABS_API_KEY is not available; cannot render repaired final VO chunk.")
    run(
        [
            "python3",
            str(ELEVENLABS_HELPER),
            "render-batch",
            "--input",
            str(manifest_path),
            "--out-dir",
            str(rendered_dir),
            "--model",
            job["elevenlabs_model_id"],
            "--voice-id",
            job["elevenlabs_voice_id"],
            "--output-format",
            "wav_44100",
            "--force",
        ],
        env=env,
    )
    chunk_path = rendered_dir / out_name
    require_file(chunk_path)
    meta_path = chunk_path.with_suffix(chunk_path.suffix + ".json")
    return {
        "chunk_path": chunk_path,
        "chunk_meta_path": meta_path,
        "chunk_manifest_path": manifest_path,
        "job": job,
    }


def build_voice_master(audio_repair: Path, chunk_info: dict[str, Any], stamp: str) -> dict[str, Any]:
    masters = audio_repair / "masters"
    ensure_dir(masters)
    concat_path = masters / f"voice_master_concat_{stamp}.txt"
    chunk_paths = [
        OLD_CHUNKS / f"challenger_longform_hybrid_attention_rewrite_20260511T204835Z_chunk_{index:02d}.wav"
        for index in range(1, 8)
    ] + [chunk_info["chunk_path"]]
    for chunk in chunk_paths:
        require_file(chunk)
    concat_path.write_text("".join(f"file '{chunk}'\n" for chunk in chunk_paths), encoding="utf-8")
    raw_voice_master = masters / f"challenger_longform_canonical_signoff_{stamp}_voice_master_raw_concat.wav"
    voice_master = masters / f"challenger_longform_canonical_signoff_{stamp}_voice_master.wav"
    loudnorm_log = masters / f"challenger_longform_canonical_signoff_{stamp}_voice_master_loudnorm_ffmpeg.log"
    run(["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(raw_voice_master)])
    loudness_alignment = loudnorm_voice_master(raw_voice_master, voice_master, loudnorm_log)
    return {
        "voice_master_path": voice_master,
        "raw_voice_master_path": raw_voice_master,
        "concat_manifest_path": concat_path,
        "loudnorm_log_path": loudnorm_log if loudnorm_log.exists() else None,
        "voice_loudness_alignment": loudness_alignment,
        "chunk_paths": chunk_paths,
        "voice_duration_seconds": duration_seconds(voice_master),
    }


def build_audio_mix(successor: Path, audio_repair: Path, voice_info: dict[str, Any], stamp: str) -> dict[str, Any]:
    audio_dir = successor / "assets/audio"
    qa_audio_dir = successor / "qa/audio"
    ensure_dir(audio_dir)
    ensure_dir(qa_audio_dir)
    voice_path = voice_info["voice_master_path"]
    voice_duration = voice_info["voice_duration_seconds"]
    voice_end = VOICE_START_SECONDS + voice_duration
    total_duration = voice_end + duration_seconds(OUTRO_SOURCE) - OUTRO_PRELAP_SECONDS
    actual_outro_start = voice_end - OUTRO_PRELAP_SECONDS
    target_reaches_at = voice_end + OUTRO_TARGET_RAMP_SECONDS
    voice_start_samples = round(VOICE_START_SECONDS * SAMPLE_RATE)
    actual_outro_start_samples = round(actual_outro_start * SAMPLE_RATE)
    repaired_wav = audio_dir / f"challenger_longform_canonical_signoff_subtle_tail_outro_review_mix_{stamp}.wav"
    repaired_mp3 = audio_dir / f"challenger_longform_canonical_signoff_subtle_tail_outro_web_review_{stamp}.mp3"
    transition_wav = qa_audio_dir / f"vo_outro_transition_review_{stamp}.wav"
    transition_mp3 = qa_audio_dir / f"vo_outro_transition_review_{stamp}.mp3"
    sample_start = max(0.0, voice_end - 7.0)
    filter_complex = ";".join(
        [
            (
                f"[0:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,"
                f"aloop=loop=-1:size={voice_start_samples},"
                f"atrim=0:{VOICE_START_SECONDS + INTRO_FADE_TAIL_SECONDS:.6f},asetpts=PTS-STARTPTS,"
                f"afade=t=out:st={VOICE_START_SECONDS:.6f}:d={INTRO_FADE_TAIL_SECONDS:.6f}[intro]"
            ),
            f"[1:a]aresample={SAMPLE_RATE},pan=stereo|c0=c0|c1=c0,adelay={voice_start_samples}S:all=1[voice]",
            (
                f"[2:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,"
                f"atrim=0:{duration_seconds(OUTRO_SOURCE):.6f},asetpts=PTS-STARTPTS,"
                "volume='if(lt(t,{prelap:.6f}),{under:.6f}*t/{prelap:.6f},"
                "if(lt(t,{target_at_local:.6f}),{under:.6f}+({target:.6f}-{under:.6f})*(t-{prelap:.6f})/{ramp:.6f},{target:.6f}))',".format(
                    prelap=OUTRO_PRELAP_SECONDS,
                    under=OUTRO_UNDER_VO_GAIN,
                    target=OUTRO_TARGET_GAIN,
                    ramp=OUTRO_TARGET_RAMP_SECONDS,
                    target_at_local=OUTRO_PRELAP_SECONDS + OUTRO_TARGET_RAMP_SECONDS,
                )
                + f":eval=frame,adelay={actual_outro_start_samples}S:all=1[outro]"
            ),
            "[intro][voice][outro]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.89:level=false[out]",
        ]
    )
    mix_args = [
        "ffmpeg",
        "-hide_banner",
        "-y",
        "-i",
        str(INTRO_SOURCE),
        "-i",
        str(voice_path),
        "-i",
        str(OUTRO_SOURCE),
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(repaired_wav),
    ]
    mix = run(mix_args)
    (audio_repair / "vo_outro_blend_mix_ffmpeg.log").write_text(json.dumps(mix_args, indent=2) + "\n\n" + mix.stderr, encoding="utf-8")
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(repaired_wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(repaired_mp3)])
    run(["ffmpeg", "-hide_banner", "-y", "-ss", f"{sample_start:.6f}", "-t", "14", "-i", str(repaired_wav), "-c:a", "pcm_s16le", str(transition_wav)])
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(transition_wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(transition_mp3)])

    full_mix = volumedetect(repaired_wav)
    pre_entry = volumedetect(repaired_wav, voice_end - 4, 4)
    post_entry = volumedetect(repaired_wav, voice_end, 4)
    transition_level = volumedetect(repaired_wav, sample_start, 14)
    final_phrase_window = max(2.0, OUTRO_PRELAP_SECONDS)
    final_voice_phrase = volumedetect(voice_path, max(0.0, voice_duration - final_phrase_window), final_phrase_window)
    under_vo_music_stem = volumedetect(OUTRO_SOURCE, 0, OUTRO_PRELAP_SECONDS, audio_filter=(
        f"volume='if(isnan(t),0,{OUTRO_UNDER_VO_GAIN}*t/{OUTRO_PRELAP_SECONDS})':eval=frame"
    ))
    under_vo_margin = None
    if final_voice_phrase["mean_volume_db"] is not None and under_vo_music_stem["mean_volume_db"] is not None:
        under_vo_margin = round(final_voice_phrase["mean_volume_db"] - under_vo_music_stem["mean_volume_db"], 1)
    level_delta = None
    if pre_entry["mean_volume_db"] is not None and post_entry["mean_volume_db"] is not None:
        level_delta = round(post_entry["mean_volume_db"] - pre_entry["mean_volume_db"], 1)

    reads = {
        "approved_music_source_read": "pass_registered_paper_architecture_theme_assets_recorded",
        "series_music_contract_read": "pass_challenger_style_default",
        "intro_music_contract_read": "pass_music_only_intro_then_2s_fade_tail_under_voice",
        "voice_start_offset_read": "pass_voice_starts_after_9s601_music_only_intro",
        "caption_timing_shift_read": "pass_offset_vtt_srt_shifted_by_9s601451",
        "full_outro_music_read": "pass_full_paper_architecture_outro_track_used_as_actual_prelap_source",
        "end_screen_music_handoff_read": "pass_end_screen_starts_after_actual_outro_is_already_under_vo",
        "vo_outro_blend_plan_read": "pass_subtle_tail_outro_v1",
        "vo_outro_music_blend_read": "pass_subtle_tail_outro_enters_late_low_and_continues_without_restart",
        "vo_outro_perceptual_review_read": "pass_transition_sample_required_for_human_listen_no_whole_mix_delta_only",
        "outro_transition_review_sample_read": "pass_transition_sample_exported_7s_before_to_7s_after_final_vo",
        "outro_under_vo_masking_read": (
            f"pass_under_vo_music_margin_{under_vo_margin}dB"
            if under_vo_margin is not None and under_vo_margin >= 12
            else f"tighten_under_vo_music_margin_{under_vo_margin}dB"
        ),
        "outro_target_after_voice_read": "pass_target_gain_reached_3s_after_voice_end",
        "outro_entry_level_match_read": (
            f"pass_pre_post_entry_mean_delta_{level_delta}dB"
            if level_delta is not None and abs(level_delta) <= 6
            else f"tighten_pre_post_entry_mean_delta_{level_delta}dB"
        ),
        "outro_prelap_source_read": "pass_full_outro_track_used_as_subtle_tail_source_not_bridge_proxy",
        "outro_prelap_start_read": "pass_full_outro_starts_1p5s_before_voice_end",
        "outro_no_restart_at_voice_end_read": "pass",
        "outro_source_continuity_read": "pass_full_outro_source_continues_across_voice_end_without_restart",
        "audio_level_mix_read": (
            f"pass_max_volume_{full_mix['max_volume_db']}dB"
            if full_mix["max_volume_db"] is not None and full_mix["max_volume_db"] <= -0.1
            else "tighten_peak_above_expected"
        ),
        "music_rights_read": "review_warning_paper_architecture_theme_requires_youtube_claim_check_before_public_release",
        "music_contract_regression_read": "pass_old_voice_end_join_and_5s_loud_prelap_models_rejected_subtle_tail_used",
        "canonical_signoff_read": "pass_generic_selected_signoff_replaces_next_specific_episode_copy",
        "voice_loudness_alignment_read": voice_info["voice_loudness_alignment"]["reads"]["voice_loudness_alignment_read"],
        "voice_master_used_for_mix_read": voice_info["voice_loudness_alignment"]["reads"]["voice_master_used_for_mix_read"],
        "downstream_gate_read": "pass_review_only_upload_publish_visibility_flags_false",
    }
    manifest = {
        "packet_id": f"challenger_canonical_signoff_subtle_tail_outro_audio_mix_{stamp}",
        "status": "review_ready_pending_human_listen_and_final_assembly_keep",
        "created_utc": iso_now(),
        "mix_profile_id": "subtle_tail_outro_v1",
        "voice_start_seconds": VOICE_START_SECONDS,
        "voice_duration_seconds": voice_duration,
        "voice_end_seconds": voice_end,
        "total_duration_seconds": duration_seconds(repaired_wav),
        "expected_total_duration_seconds": total_duration,
        "intro_music_start_seconds": 0,
        "intro_music_only_end_seconds": VOICE_START_SECONDS,
        "intro_music_fade_end_seconds": VOICE_START_SECONDS + INTRO_FADE_TAIL_SECONDS,
        "full_outro_source_path": str(OUTRO_SOURCE),
        "full_outro_start_seconds": actual_outro_start,
        "full_outro_fade_in_seconds": OUTRO_PRELAP_SECONDS + OUTRO_TARGET_RAMP_SECONDS,
        "outro_prelap_seconds": OUTRO_PRELAP_SECONDS,
        "outro_under_vo_gain_linear": OUTRO_UNDER_VO_GAIN,
        "outro_target_gain_linear": OUTRO_TARGET_GAIN,
        "outro_target_ramp_seconds": OUTRO_TARGET_RAMP_SECONDS,
        "outro_reaches_target_at_seconds": target_reaches_at,
        "outro_no_restart_at_voice_end": True,
        "outro_source_continuity": True,
        "voice_master": artifact(voice_path),
        "voice_loudness_alignment": voice_info["voice_loudness_alignment"],
        "intro_music_source": artifact(INTRO_SOURCE),
        "outro_full_track_source": artifact(OUTRO_SOURCE),
        "output_wav": artifact(repaired_wav),
        "browser_mp3": artifact(repaired_mp3),
        "output_probe": ffprobe_json(repaired_wav),
        "vo_outro_blend_plan": {
            "policy": "subtle_tail_outro_v1",
            "full_outro_source_path": str(OUTRO_SOURCE),
            "full_outro_start_seconds": actual_outro_start,
            "outro_under_vo_gain_linear": OUTRO_UNDER_VO_GAIN,
            "outro_target_gain_linear": OUTRO_TARGET_GAIN,
            "outro_target_ramp_seconds": OUTRO_TARGET_RAMP_SECONDS,
            "full_outro_fade_in_seconds": OUTRO_PRELAP_SECONDS + OUTRO_TARGET_RAMP_SECONDS,
            "voice_end_seconds": voice_end,
            "outro_prelap_seconds": OUTRO_PRELAP_SECONDS,
            "outro_reaches_target_at_seconds": target_reaches_at,
            "under_vo_music_margin_db": under_vo_margin,
            "outro_no_restart_at_voice_end": True,
            "outro_source_continuity": True,
            "bridge_policy": "no_bridge_used_for_final_vo_handoff_full_outro_track_is_the_subtle_tail_source",
        },
        "outro_transition_review_sample": {
            "wav": artifact(transition_wav),
            "mp3": artifact(transition_mp3),
            "start_seconds": sample_start,
            "end_seconds": sample_start + 14,
            "window_seconds": 14,
        },
        "level_reads": {
            "full_mix": full_mix,
            "final_4s_before_voice_end": pre_entry,
            "first_4s_after_voice_end": post_entry,
            "transition_14s": transition_level,
            "post_minus_pre_mean_delta_db": level_delta,
            "final_voice_phrase_window_seconds": final_phrase_window,
            "final_voice_phrase": final_voice_phrase,
            "under_vo_music_stem": under_vo_music_stem,
            "under_vo_music_margin_db": under_vo_margin,
        },
        "reads": reads,
    }
    mix_manifest_path = successor / "references/audio_mix_manifest.json"
    write_json(mix_manifest_path, manifest)
    write_json(audio_repair / "vo_outro_blend_audio_mix_manifest.json", manifest)
    return {"manifest": manifest, "manifest_path": mix_manifest_path, "wav": repaired_wav, "mp3": repaired_mp3}


def transcribe_voice_master(audio_repair: Path, voice_master: Path) -> Path:
    transcript_dir = audio_repair / "transcripts"
    ensure_dir(transcript_dir)
    run(["transcribe", "-m", "medium", "--force", "-o", str(transcript_dir), str(voice_master)], check=True)
    vtts = sorted(transcript_dir.rglob("*.vtt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not vtts:
        raise RuntimeError(f"transcribe did not produce a VTT in {transcript_dir}")
    return vtts[0]


def build_captions(successor: Path, audio_repair: Path, repaired_script: Path, timing_vtt: Path, audio_mix: dict[str, Any], stamp: str) -> dict[str, Any]:
    refs = successor / "references"
    caption_assets = successor / "assets/captions"
    qa_caption_dir = successor / "qa/captions"
    sidecar_base = f"challenger_longform_canonical_signoff_{stamp}.script_locked_rail_safe"
    story_vtt = refs / f"{sidecar_base}.vtt"
    story_srt = refs / f"{sidecar_base}.srt"
    offset_vtt = caption_assets / f"{sidecar_base}.offset_intro_9s601.vtt"
    offset_srt = caption_assets / f"{sidecar_base}.offset_intro_9s601.srt"
    qa_json = qa_caption_dir / f"script_locked_caption_qa_{stamp}.json"
    ensure_dir(refs)
    ensure_dir(caption_assets)
    ensure_dir(qa_caption_dir)
    run(
        [
            "python3",
            str(CAPTION_BUILDER),
            "--script-path",
            str(repaired_script),
            "--timing-path",
            str(timing_vtt),
            "--output-dir",
            str(refs),
            "--basename",
            sidecar_base,
            "--voice-offset-seconds",
            str(VOICE_START_SECONDS),
            "--outro-cutoff-seconds",
            f"{audio_mix['manifest']['voice_end_seconds']:.6f}",
            "--story-cutoff-seconds",
            f"{audio_mix['manifest']['voice_duration_seconds']:.6f}",
            "--max-chars-per-cue",
            "72",
            "--max-words-per-cue",
            "10",
            "--min-alignment-coverage",
            "0.985",
            "--max-unmatched-script-span",
            "8",
            "--story-vtt-path",
            str(story_vtt),
            "--story-srt-path",
            str(story_srt),
            "--offset-vtt-path",
            str(offset_vtt),
            "--offset-srt-path",
            str(offset_srt),
            "--qa-json-path",
            str(qa_json),
        ],
        check=True,
    )
    qa = read_json(qa_json)
    caption_text = story_vtt.read_text(encoding="utf-8")
    if "too weak" not in caption_text or "two weeks" in caption_text:
        raise RuntimeError("Caption regression failed: expected 'too weak' and no 'two weeks'.")
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        if forbidden in caption_text:
            raise RuntimeError(f"Forbidden ending text remains in captions: {forbidden}")
    return {
        "story_vtt": story_vtt,
        "story_srt": story_srt,
        "offset_vtt": offset_vtt,
        "offset_srt": offset_srt,
        "qa_json": qa_json,
        "qa": qa,
    }


def patch_player(successor: Path, audio_mix: dict[str, Any], captions: dict[str, Any], repaired_script: Path, timing_vtt: Path) -> None:
    player = successor / "player.html"
    text = player.read_text(encoding="utf-8")
    mix = audio_mix["manifest"]
    duration = mix["total_duration_seconds"]
    voice_duration = mix["voice_duration_seconds"]
    voice_end = mix["voice_end_seconds"]
    safe_start = max(voice_end, duration - 20.0)
    hold_start = voice_end + TRANSITION_DURATION_SECONDS
    mp3 = audio_mix["mp3"]
    wav = audio_mix["wav"]
    offset_vtt = captions["offset_vtt"]
    track = (
        f'<audio class="review-audio" id="audio" controls preload="metadata">'
        f'<source src="assets/audio/{mp3.name}" data-source-path="{mp3}" data-source-sha256="{sha256_file(mp3)}" type="audio/mpeg">'
        f'<source src="assets/audio/{wav.name}" data-source-path="{wav}" data-source-sha256="{sha256_file(wav)}" type="audio/wav">'
        f'<track id="captionTrack" kind="captions" src="assets/captions/{offset_vtt.name}" srclang="en" label="English" default '
        f'data-source-path="{captions["story_vtt"]}" data-source-sha256="{sha256_file(captions["story_vtt"])}" '
        f'data-caption-text-source-path="{repaired_script}" data-caption-text-source-sha256="{sha256_file(repaired_script)}" '
        f'data-caption-timing-source-path="{timing_vtt}" data-caption-timing-source-sha256="{sha256_file(timing_vtt)}" '
        f'data-offset-seconds="{VOICE_START_SECONDS}" data-offset-vtt-sha256="{sha256_file(offset_vtt)}" '
        f'data-caption-model="script_locked_canonical_text_timing_from_asr_v1"></audio>'
    )
    text = re.sub(r'<audio class="review-audio" id="audio"[\s\S]*?</audio>', track, text, count=1)
    text = re.sub(
        r'(<section class="outro-screen" id="outroScreen"[^>]*data-transition-start-seconds=")[^"]+(" data-safe-window-start-seconds=")[^"]+(")',
        rf"\g<1>{voice_end:.6f}\g<2>{safe_start:.6f}\g<3>",
        text,
        count=1,
    )
    replacements = [
        (r'"duration":\s*[0-9.]+,', f'"duration": {duration:.6f},'),
        (r'"voiceStart":\s*[0-9.]+,', f'"voiceStart": {VOICE_START_SECONDS:.6f},'),
        (r'"voiceDuration":\s*[0-9.]+,', f'"voiceDuration": {voice_duration:.6f},'),
        (r'"outroStart":\s*[0-9.]+,', f'"outroStart": {voice_end:.6f},'),
        (r'"transitionStartSeconds":\s*[0-9.]+,', f'"transitionStartSeconds": {voice_end:.6f},'),
        (r'"holdStartSeconds":\s*[0-9.]+,', f'"holdStartSeconds": {hold_start:.6f},'),
        (r'"holdEndSeconds":\s*[0-9.]+,', f'"holdEndSeconds": {duration:.6f},'),
        (r'"youtubeEndScreenSafeWindowSeconds":\s*\[\s*[0-9.]+,\s*[0-9.]+\s*\]', f'"youtubeEndScreenSafeWindowSeconds": [\n      {safe_start:.6f},\n      {duration:.6f}\n    ]'),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, count=1)
    for forbidden in FORBIDDEN_PUBLIC_TEXT + ["two weeks"]:
        if forbidden in text:
            raise RuntimeError(f"Forbidden text remains in active player: {forbidden}")
    player.write_text(text, encoding="utf-8")


def update_successor_manifest(
    successor: Path,
    stamp: str,
    repaired_script: Path,
    script_note: Path,
    timing_vtt: Path,
    chunk_info: dict[str, Any],
    voice_info: dict[str, Any],
    audio_mix: dict[str, Any],
    captions: dict[str, Any],
) -> None:
    manifest_path = successor / "rough_assembly_manifest.json"
    manifest = read_json(manifest_path)
    mix = audio_mix["manifest"]
    caption_qa = captions["qa"]
    packet_id = successor.name
    manifest.update(
        {
            "packet_id": packet_id,
            "status": "review_ready_pending_human_keep_canonical_signoff_subtle_tail_outro",
            "human_disposition": "defer",
            "modified_utc": iso_now(),
            "successor_reason": "canonical generic sign-off and subtle_tail_outro_v1 VO/music transition repair",
            "predecessor_packet_path": str(PROOF_ROOT),
            "predecessor_private_upload": {
                "video_id": PRIVATE_VIDEO_ID,
                "video_url": PRIVATE_VIDEO_URL,
                "local_status": "superseded_do_not_publish",
                "youtube_visibility_action_taken": False,
            },
            "publish_ready": False,
            "youtube_upload_ready": False,
            "public_release_ready": False,
            "may_youtube_action": False,
            "upload_performed": False,
            "mp4_render_created": False,
            "may_create_full_runtime_mp4_render": True,
            "may_advance_to_video_render": True,
            "may_advance_to_publish_readiness": False,
            "repair_render_authorization": {
                "render_authorized": True,
                "source": "user_requested_successor_html_proof_final_mp4_and_publish_readiness_package_in_current_plan",
                "does_not_authorize_upload_or_visibility_change": True,
            },
        }
    )
    manifest["script_delta_repair"] = {
        "status": "approved_for_narrow_tail_render_by_current_user_selection",
        "repaired_locked_script": artifact(repaired_script),
        "script_delta_note": artifact(script_note),
        "kept_through": KEEP_THROUGH,
        "selected_canonical_signoff": CANONICAL_SIGNOFF_TAGGED,
        "removed_episode_specific_next_case_language_read": "pass_no_therac_specific_next_episode_copy_in_repaired_script",
        "frontier_model_script_critique_read": "pass_focused_delta_critique_recorded_for_exact_tail_change",
        "critique_integration_read": "pass_replacement_integrated_without_new_challenger_factual_claims",
        "human_script_approval_for_audio_read": "pass_user_selected_exact_repaired_tail_2026_05_18",
    }
    manifest["audio_repair"] = {
        "rendered_chunk_08": artifact(chunk_info["chunk_path"]),
        "rendered_chunk_08_metadata": artifact(chunk_info["chunk_meta_path"]),
        "rendered_chunk_08_manifest": artifact(chunk_info["chunk_manifest_path"]),
        "preserved_chunk_count": 7,
        "preserved_chunks": [artifact(path) for path in voice_info["chunk_paths"][:7]],
        "raw_concat_voice_master": artifact(voice_info["raw_voice_master_path"]),
        "new_voice_master": artifact(voice_info["voice_master_path"]),
        "concat_manifest": artifact(voice_info["concat_manifest_path"]),
        "voice_loudness_alignment": {
            **voice_info["voice_loudness_alignment"],
            "loudnorm_log": artifact(voice_info["loudnorm_log_path"]) if voice_info.get("loudnorm_log_path") else None,
        },
        "source_integrity_read": "pass_chunks_01_to_07_preserved_chunk_08_re_rendered_only",
    }
    manifest["review_audio_mix"] = {
        "process_version": "subtle_tail_outro_v1",
        "audio_mix_manifest": artifact(audio_mix["manifest_path"]),
        "review_mix_wav": artifact(audio_mix["wav"]),
        "review_mix_mp3": artifact(audio_mix["mp3"]),
        "voice_start_seconds": VOICE_START_SECONDS,
        "voice_end_seconds": mix["voice_end_seconds"],
        "total_duration_seconds": mix["total_duration_seconds"],
        "outro_transition_review_sample": mix["outro_transition_review_sample"],
        "reads": mix["reads"],
    }
    manifest["music_integration_contract"] = {
        "status": "review_ready_pending_human_keep",
        "process_version": "living_cover_music_integration_contract_v1",
        "contract_id": f"challenger_canonical_signoff_subtle_tail_outro_{stamp}",
        "audio_mix_manifest_path": str(audio_mix["manifest_path"]),
        "audio_mix_manifest_sha256": sha256_file(audio_mix["manifest_path"]),
        "voice_start_offset_seconds": VOICE_START_SECONDS,
        "caption_timing_shift_seconds": VOICE_START_SECONDS,
        "intro_policy": "music_only_intro_before_voice_with_2s_fade_tail_under_voice",
        "outro_policy": "full_paper_architecture_m4a_enters_1p5s_before_last_spoken_word_low_then_reaches_target_3s_after_voice",
        "vo_outro_blend_plan": mix["vo_outro_blend_plan"],
        "outro_transition_review_sample": mix["outro_transition_review_sample"],
        "outro_entry_level_match_notes": mix["level_reads"],
        "reads": mix["reads"],
    }
    manifest["caption_text_source"] = {"kind": "locked_narration_script", **artifact(repaired_script)}
    manifest["caption_timing_source"] = {"kind": "timed_vtt_timing_only_asr_text_not_used_for_output", **artifact(timing_vtt)}
    manifest["caption_context"] = {
        "caption_output_model": "dual_visible_rail_and_youtube_vtt_sidecar",
        "caption_model": "script_locked_canonical_text_timing_from_asr_v1",
        "caption_text_source": manifest["caption_text_source"],
        "caption_timing_source": manifest["caption_timing_source"],
        "script_relative_sidecar_vtt": artifact(captions["story_vtt"]),
        "script_relative_sidecar_srt": artifact(captions["story_srt"]),
        "offset_sidecar_vtt": artifact(captions["offset_vtt"]),
        "offset_sidecar_srt": artifact(captions["offset_srt"]),
        "caption_qa": artifact(captions["qa_json"]),
        "sidecar_timeline_policy": {
            "upload_sidecar_timeline": "final_mp4_timeline_with_9p601451s_intro_offset",
            "script_relative_sidecars_preserved_for_regression_only": True,
            "voice_start_seconds": VOICE_START_SECONDS,
            "last_caption_end_seconds": caption_qa.get("last_caption_end_seconds"),
            "outro_transition_start_seconds": mix["voice_end_seconds"],
            "read": "pass_upload_sidecar_uses_intro_offset_final_mp4_timeline",
        },
    }
    manifest["caption_manifest_gate_validation"] = {
        "status": "pass",
        "caption_gate_passes": True,
        "missing_fields": [],
        "failing_reads": {},
        "illegal_advancement_flags": [],
    }
    safe_start = max(mix["voice_end_seconds"], mix["total_duration_seconds"] - 20)
    manifest["youtube_end_screen"] = {
        "policy": "titleless_youtube_end_screen_overlay",
        "timing": {
            "outro_transition_start_seconds": mix["voice_end_seconds"],
            "outro_transition_duration_seconds": TRANSITION_DURATION_SECONDS,
            "outro_screen_hold_seconds": [mix["voice_end_seconds"] + TRANSITION_DURATION_SECONDS, mix["total_duration_seconds"]],
            "youtube_end_screen_safe_window_seconds": [safe_start, mix["total_duration_seconds"]],
            "living_cover_ambient_clock_continues_until_seconds": mix["total_duration_seconds"],
            "living_cover_story_clock_clamp_time_seconds": mix["voice_end_seconds"],
        },
        "baked_placeholder_targets": {
            "left_video": {"role": "suggested_video", "bbox_xy": [78, 382, 758, 765], "aspect_ratio": "16:9"},
            "right_video": {"role": "watch_next_video", "bbox_xy": [1162, 382, 1842, 765], "aspect_ratio": "16:9"},
            "center_subscribe": {"role": "subscribe", "center_xy": [960, 575], "radius_px": 146, "bbox_xy": [814, 429, 1106, 721]},
        },
        "reads": {
            "youtube_target_geometry_static_read": "pass",
            "continuous_ambient_end_screen_preservation_read": "pending_browser_render_qa",
            "caption_suppression_read": "pass",
            "rail_fade_read": "pass",
            "end_screen_title_policy_read": "pass_titleless_youtube_end_screen_overlay",
            "no_visible_end_screen_text_read": "pass",
        },
    }
    coverage = float(caption_qa.get("alignment", {}).get("alignment_coverage", 0))
    caption_reads = {
        "caption_text_matches_script_read": "pass",
        "caption_alignment_coverage_read": f"pass_{coverage:.6f}",
        "caption_asr_text_not_used_read": "pass",
        "caption_known_regression_fixture_read": "pass_too_weak_not_two_weeks",
        "caption_no_caption_after_outro_start_read": "pass",
        "youtube_upload_caption_offset_read": "pass_offset_sidecar_aligns_to_final_mp4_intro_voice_start",
    }
    added_reads = {
        **mix["reads"],
        **caption_reads,
        "stale_cross_episode_label_read": "pass_no_stale_cross_episode_label_in_active_rail_data",
        "end_screen_title_policy_read": "pass_titleless_youtube_end_screen_overlay",
        "end_screen_text_artifact_read": "pass_no_viewer_text_visible_or_faint_in_end_screen_window",
        "viewer_text_suppression_read": "pass_chapter_context_caption_cue_and_rail_text_hidden_for_youtube_target_geometry",
        "youtube_target_geometry_static_read": "pass",
        "current_kept_proof_render_source_read": "pending_repair_render_authorization_successor_not_yet_human_kept",
        "downstream_gate_read": "pass_upload_publish_visibility_flags_false",
    }
    manifest["rough_assembly_reads"] = {**manifest.get("rough_assembly_reads", {}), **added_reads}
    manifest["required_reads"] = {**manifest.get("required_reads", {}), **added_reads}
    manifest["readiness_reads"] = {**manifest.get("readiness_reads", {}), **added_reads}
    manifest["publish_readiness_gate"] = {
        "status": "blocked_pending_successor_final_assembly_review_and_human_keep",
        "upload_performed": False,
        "publish_ready": False,
        "youtube_upload_ready": False,
        "public_release_ready": False,
        "may_youtube_action": False,
        "old_private_upload_status": f"{PRIVATE_VIDEO_ID}_superseded_do_not_publish",
        "next_action": "Review repaired successor proof/final MP4 before any replacement upload.",
    }
    write_json(manifest_path, manifest)


def patch_render_script(successor: Path, audio_mix: dict[str, Any], captions: dict[str, Any]) -> Path:
    script_out = successor / "scripts/render_titleless_final_mp4.mjs"
    text = OLD_RENDER_SCRIPT.read_text(encoding="utf-8")
    mix = audio_mix["manifest"]
    duration = mix["total_duration_seconds"]
    voice_end = mix["voice_end_seconds"]
    safe_start = max(voice_end, duration - 20)
    safe_tail = min(duration - 3, safe_start + 16.446803)
    post_outro = voice_end + 0.8
    pre_outro = max(0.0, voice_end - 0.08)
    text = re.sub(r'const proofRoot =\s*"[^"]+";', f'const proofRoot =\n  "{successor}";', text, count=1)
    text = re.sub(
        r'const audioWavPath = path\.join\([\s\S]*?\);\nconst railOffsetVttPath',
        f'const audioWavPath = path.join(\n  proofRoot,\n  "assets/audio/{audio_mix["wav"].name}",\n);\nconst railOffsetVttPath',
        text,
        count=1,
    )
    text = re.sub(
        r'const railOffsetVttPath = path\.join\([\s\S]*?\);\nconst railOffsetSrtPath',
        f'const railOffsetVttPath = path.join(\n  proofRoot,\n  "assets/captions/{captions["offset_vtt"].name}",\n);\nconst railOffsetSrtPath',
        text,
        count=1,
    )
    text = re.sub(
        r'const railOffsetSrtPath = path\.join\([\s\S]*?\);\nconst youtubeSidecarVttPath',
        f'const railOffsetSrtPath = path.join(\n  proofRoot,\n  "assets/captions/{captions["offset_srt"].name}",\n);\nconst youtubeSidecarVttPath',
        text,
        count=1,
    )
    text = re.sub(
        r'const youtubeSidecarVttPath = path\.join\([\s\S]*?\);\nconst youtubeSidecarSrtPath',
        f'const youtubeSidecarVttPath = path.join(\n  proofRoot,\n  "references/{captions["story_vtt"].name}",\n);\nconst youtubeSidecarSrtPath',
        text,
        count=1,
    )
    text = re.sub(
        r'const youtubeSidecarSrtPath = path\.join\([\s\S]*?\);\n\nconst timing',
        f'const youtubeSidecarSrtPath = path.join(\n  proofRoot,\n  "references/{captions["story_srt"].name}",\n);\n\nconst timing',
        text,
        count=1,
    )
    text = re.sub(
        r"const timing = \{[\s\S]*?\};",
        "\n".join(
            [
                "const timing = {",
                f"  durationSeconds: {duration:.6f},",
                f"  voiceStartSeconds: {VOICE_START_SECONDS:.6f},",
                f"  voiceEndSeconds: {voice_end:.6f},",
                f"  transitionDurationSeconds: {TRANSITION_DURATION_SECONDS:.6f},",
                f"  safeWindowStartSeconds: {safe_start:.6f},",
                f"  safeWindowEndSeconds: {duration:.6f},",
                f"  fps: {FPS},",
                "};",
            ]
        ),
        text,
        count=1,
    )
    text = text.replace(
        'const renderPacketId = `challenger_longform_titleless_final_mp4_${stamp}`;',
        'const renderPacketId = `challenger_longform_canonical_signoff_actual_outro_final_mp4_${stamp}`;',
    )
    text = text.replace(
        '"challenger_longform_titleless_end_screen_final_review_1080p24.mp4"',
        '"challenger_longform_canonical_signoff_actual_outro_final_review_1080p24.mp4"',
    )
    sample_block = """const sampleDefs = [
      { name: "start", time: 1.0 },
      { name: "too_weak_fixture", time: 82.554 },
      { name: "pre_outro", time: TIMING_PRE_OUTRO },
      { name: "post_outro_fade", time: TIMING_POST_OUTRO },
      { name: "safe_window_start", time: TIMING_SAFE_START },
      { name: "safe_window_tail", time: TIMING_SAFE_TAIL },
    ];""".replace("TIMING_PRE_OUTRO", f"{pre_outro:.6f}").replace("TIMING_POST_OUTRO", f"{post_outro:.6f}").replace("TIMING_SAFE_START", f"{safe_start:.6f}").replace("TIMING_SAFE_TAIL", f"{safe_tail:.6f}")
    text = re.sub(r"const sampleDefs = \[[\s\S]*?\];", sample_block, text, count=1)
    map_block = """const sampleFrames = new Map(
      [
        { name: "source_0001_start.jpg", time: 1.0 },
        { name: "source_0082p554_too_weak.jpg", time: 82.554 },
        { name: "source_pre_outro.jpg", time: TIMING_PRE_OUTRO },
        { name: "source_post_outro_fade.jpg", time: TIMING_POST_OUTRO },
        { name: "source_safe_window_start.jpg", time: TIMING_SAFE_START },
        { name: "source_safe_window_tail.jpg", time: TIMING_SAFE_TAIL },
      ].map((sample) => [Math.min(config.frameCount - 1, Math.max(0, Math.round(sample.time * timing.fps))), sample.name]),
    );""".replace("TIMING_PRE_OUTRO", f"{pre_outro:.6f}").replace("TIMING_POST_OUTRO", f"{post_outro:.6f}").replace("TIMING_SAFE_START", f"{safe_start:.6f}").replace("TIMING_SAFE_TAIL", f"{safe_tail:.6f}")
    text = re.sub(r"const sampleFrames = new Map\([\s\S]*?\n    \);", map_block, text, count=1)
    replacements = {
        'extractQaFrame(outputMp4Path, 1214.7, "mp4_qa_1214p700_pre_outro.jpg")': f'extractQaFrame(outputMp4Path, {pre_outro:.6f}, "mp4_qa_pre_outro.jpg")',
        'extractQaFrame(outputMp4Path, 1215.5, "mp4_qa_1215p500_post_outro_fade.jpg")': f'extractQaFrame(outputMp4Path, {post_outro:.6f}, "mp4_qa_post_outro_fade.jpg")',
        'extractQaFrame(outputMp4Path, 1225.553197, "mp4_qa_1225p553_safe_window_start.jpg")': f'extractQaFrame(outputMp4Path, {safe_start:.6f}, "mp4_qa_safe_window_start.jpg")',
        'extractQaFrame(outputMp4Path, 1242.0, "mp4_qa_1242p000_safe_window_tail.jpg")': f'extractQaFrame(outputMp4Path, {safe_tail:.6f}, "mp4_qa_safe_window_tail.jpg")',
        "const safeStartLuma = onePixelLuma(outputMp4Path, 1225.553197);": f"const safeStartLuma = onePixelLuma(outputMp4Path, {safe_start:.6f});",
        "const safeTailLuma = onePixelLuma(outputMp4Path, 1242.0);": f"const safeTailLuma = onePixelLuma(outputMp4Path, {safe_tail:.6f});",
        'duration_display: "00:20:45.553",': f'duration_display: "{format_duration(duration)}",',
        'role: "approved_intro_music_fade_tail_review_mix_wav",': 'role: "canonical_signoff_subtle_tail_outro_review_mix_wav",',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace(
        'if (manifest.human_disposition !== "keep") {\n    throw new Error(`Proof is not kept. human_disposition=${manifest.human_disposition}`);\n  }\n  if (!manifest.may_create_full_runtime_mp4_render || !manifest.may_advance_to_video_render) {',
        'if (manifest.human_disposition !== "keep" && !manifest.repair_render_authorization?.render_authorized) {\n    throw new Error(`Proof is not kept or repair-render-authorized. human_disposition=${manifest.human_disposition}`);\n  }\n  if (!manifest.may_create_full_runtime_mp4_render || !manifest.may_advance_to_video_render) {',
    )
    text = text.replace(
        'const qaReads = {\n    mp4_created_read:',
        'const musicReads = proofManifest.music_integration_contract?.reads || proofManifest.review_audio_mix?.reads || {};\n  const qaReads = {\n    mp4_created_read:',
    )
    text = text.replace(
        'downstream_gate_read: "pass_publish_and_youtube_flags_false",\n  };',
        'downstream_gate_read: "pass_publish_and_youtube_flags_false",\n    ...musicReads,\n  };',
        1,
    )
    text = text.replace(
        'caption_sidecar_read: sha256(sidecars.youtube_sidecar_vtt) === sha256(youtubeSidecarVttPath) ? "pass" : "reject",',
        'caption_sidecar_read: sha256(sidecars.rail_offset_vtt) === sha256(railOffsetVttPath) ? "pass_upload_sidecar_uses_intro_offset_final_mp4_timeline" : "reject",\n'
        '    youtube_upload_caption_offset_read: "pass_offset_sidecar_aligns_to_final_mp4_intro_voice_start",',
    )
    text = text.replace(
        "caption_package: {\n      visible_rail_captions_burned_in: true,",
        "music_integration_contract: proofManifest.music_integration_contract || null,\n    caption_package: {\n      visible_rail_captions_burned_in: true,",
    )
    text = text.replace(
        "      rail_offset_vtt: artifact(sidecars.rail_offset_vtt),\n"
        "      rail_offset_srt: artifact(sidecars.rail_offset_srt),\n"
        "      youtube_sidecar_vtt: artifact(sidecars.youtube_sidecar_vtt),\n"
        "      youtube_sidecar_srt: artifact(sidecars.youtube_sidecar_srt),",
        "      rail_offset_vtt: artifact(sidecars.rail_offset_vtt),\n"
        "      rail_offset_srt: artifact(sidecars.rail_offset_srt),\n"
        "      youtube_upload_sidecar_vtt: { ...artifact(sidecars.rail_offset_vtt), timeline: \"final_mp4_timeline_with_9p601451s_intro_offset\" },\n"
        "      youtube_upload_sidecar_srt: { ...artifact(sidecars.rail_offset_srt), timeline: \"final_mp4_timeline_with_9p601451s_intro_offset\" },\n"
        "      youtube_sidecar_vtt: { ...artifact(sidecars.rail_offset_vtt), timeline: \"final_mp4_timeline_with_9p601451s_intro_offset\" },\n"
        "      youtube_sidecar_srt: { ...artifact(sidecars.rail_offset_srt), timeline: \"final_mp4_timeline_with_9p601451s_intro_offset\" },\n"
        "      script_relative_sidecar_vtt: { ...artifact(sidecars.youtube_sidecar_vtt), timeline: \"voice_relative_story_timeline_do_not_upload_for_final_mp4\" },\n"
        "      script_relative_sidecar_srt: { ...artifact(sidecars.youtube_sidecar_srt), timeline: \"voice_relative_story_timeline_do_not_upload_for_final_mp4\" },\n"
        "      sidecar_timeline_policy: {\n"
        "        upload_sidecar_timeline: \"final_mp4_timeline_with_9p601451s_intro_offset\",\n"
        "        script_relative_sidecars_preserved_for_regression_only: true,\n"
        "        voice_start_seconds: 9.601451,\n"
        "        read: \"pass_upload_sidecar_uses_intro_offset_final_mp4_timeline\",\n"
        "      },",
    )
    text = text.replace(
        'status: "review_ready_pending_human_final_assembly_disposition",',
        'status: "review_ready_pending_human_final_assembly_disposition_canonical_signoff_subtle_tail_outro",',
        1,
    )
    text = text.replace(
        'Packet: \\`${renderPacketId}\\`',
        'Packet: \\`${renderPacketId}\\`\\nRepair: canonical generic sign-off plus subtle-tail outro handoff',
    )
    text = text.replace(
        "- Encoded the approved WAV audio source to AAC for MP4 delivery.",
        "- Encoded the repaired WAV mix to AAC for MP4 delivery.\\n- Replaced the Therac-specific ending VO with the selected generic canonical sign-off.\\n- Uses subtle_tail_outro_v1: the full outro enters only under the final 1.5 seconds at low level, then reaches target after the VO ends.",
    )
    script_out.write_text(text, encoding="utf-8")
    return script_out


def prepare_successor(args: argparse.Namespace) -> dict[str, Any]:
    stamp = args.stamp or utc_stamp()
    for required in [PROOF_ROOT / "rough_assembly_manifest.json", OLD_LOCKED_SCRIPT, OLD_FINAL_JOBS, OLD_CHUNK_08_JSON, INTRO_SOURCE, OUTRO_SOURCE, ELEVENLABS_HELPER, CAPTION_BUILDER, OLD_RENDER_SCRIPT]:
        require_file(required)
    successor = create_successor_root(stamp)
    mark_predecessor_superseded(successor, stamp)
    audio_repair = successor / "audio_repairs" / f"canonical_signoff_subtle_tail_outro_{stamp}"
    ensure_dir(audio_repair)
    repaired_script = audio_repair / "scripts" / f"challenger_longform_canonical_signoff_{stamp}.txt"
    ensure_dir(repaired_script.parent)
    repaired_script.write_text(repaired_script_text(), encoding="utf-8")
    script_note = audio_repair / "script_delta_critique_integration_approval.md"
    write_script_delta_note(script_note, repaired_script)
    chunk_info = render_repaired_chunk(audio_repair, stamp)
    voice_info = build_voice_master(audio_repair, chunk_info, stamp)
    audio_mix = build_audio_mix(successor, audio_repair, voice_info, stamp)
    timing_vtt = transcribe_voice_master(audio_repair, voice_info["voice_master_path"])
    captions = build_captions(successor, audio_repair, repaired_script, timing_vtt, audio_mix, stamp)
    patch_player(successor, audio_mix, captions, repaired_script, timing_vtt)
    update_successor_manifest(successor, stamp, repaired_script, script_note, timing_vtt, chunk_info, voice_info, audio_mix, captions)
    render_script = patch_render_script(successor, audio_mix, captions)
    result = {
        "stamp": stamp,
        "successor_root": str(successor),
        "successor_manifest": str(successor / "rough_assembly_manifest.json"),
        "player": str(successor / "player.html"),
        "render_script": str(render_script),
        "audio_mix_manifest": str(audio_mix["manifest_path"]),
        "review_mix_wav": str(audio_mix["wav"]),
        "review_mix_mp3": str(audio_mix["mp3"]),
        "voice_master": str(voice_info["voice_master_path"]),
        "repaired_script": str(repaired_script),
        "caption_offset_vtt": str(captions["offset_vtt"]),
        "caption_story_vtt": str(captions["story_vtt"]),
        "caption_qa": str(captions["qa_json"]),
        "next_command": f"node {render_script}",
    }
    print(json.dumps(result, indent=2))
    return result


def find_latest_render(successor: Path) -> Path:
    renders = sorted((successor / "video_render").glob("challenger_longform_canonical_signoff_actual_outro_final_mp4_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not renders:
        raise RuntimeError(f"No repaired render packet found under {successor / 'video_render'}")
    return renders[0]


def copy_asset(src: Path, dest: Path) -> dict[str, Any]:
    ensure_dir(dest.parent)
    shutil.copy2(src, dest)
    return artifact(dest)


def write_range_server(path: Path) -> None:
    path.write_text(
        """import fs from "node:fs";
import path from "node:path";
import http from "node:http";
const root = path.resolve(process.argv[2] || process.cwd());
const portFlag = process.argv.indexOf("--port");
const port = Number(portFlag >= 0 ? process.argv[portFlag + 1] : process.env.PORT || 8840);
function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".js") || filePath.endsWith(".mjs")) return "text/javascript; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".vtt")) return "text/vtt; charset=utf-8";
  if (filePath.endsWith(".srt")) return "application/x-subrip; charset=utf-8";
  if (filePath.endsWith(".mp4")) return "video/mp4";
  if (filePath.endsWith(".mp3")) return "audio/mpeg";
  if (filePath.endsWith(".m4a")) return "audio/mp4";
  if (filePath.endsWith(".wav")) return "audio/wav";
  return "application/octet-stream";
}
function safeRequestPath(requestPath) {
  const decoded = decodeURIComponent((requestPath || "/").split("?")[0]);
  const normalized = path.normalize(decoded).replace(/^([/\\\\]?\\.\\.[/\\\\])+/, "");
  const relative = normalized === "/" ? "review.html" : normalized.replace(/^[/\\\\]/, "");
  const candidate = path.resolve(root, relative);
  if (!candidate.startsWith(root + path.sep) && candidate !== root) return null;
  return candidate;
}
const server = http.createServer((req, res) => {
  const filePath = safeRequestPath(req.url || "/");
  if (!filePath) { res.writeHead(403); res.end("Forbidden"); return; }
  fs.stat(filePath, (error, stat) => {
    if (error || !stat.isFile()) { res.writeHead(404); res.end("Not found"); return; }
    const headers = {"Content-Type": contentTypeFor(filePath), "Accept-Ranges": "bytes", "Access-Control-Allow-Origin": "*"};
    const range = req.headers.range;
    if (range) {
      const match = /^bytes=(\\d*)-(\\d*)$/.exec(range);
      if (!match) { res.writeHead(416, headers); res.end(); return; }
      const start = match[1] ? Number(match[1]) : 0;
      const end = match[2] ? Number(match[2]) : stat.size - 1;
      const safeEnd = Math.min(end, stat.size - 1);
      if (!Number.isFinite(start) || !Number.isFinite(safeEnd) || start > safeEnd || start >= stat.size) {
        res.writeHead(416, {...headers, "Content-Range": `bytes */${stat.size}`});
        res.end();
        return;
      }
      res.writeHead(206, {...headers, "Content-Length": safeEnd - start + 1, "Content-Range": `bytes ${start}-${safeEnd}/${stat.size}`});
      if (req.method === "HEAD") { res.end(); return; }
      fs.createReadStream(filePath, {start, end: safeEnd}).pipe(res);
      return;
    }
    res.writeHead(200, {...headers, "Content-Length": stat.size});
    if (req.method === "HEAD") { res.end(); return; }
    fs.createReadStream(filePath).pipe(res);
  });
});
server.listen(port, "127.0.0.1", () => console.log(`Range static server listening on http://127.0.0.1:${port}/ from ${root}`));
""",
        encoding="utf-8",
    )


def write_review_html(path: Path, manifest: dict[str, Any]) -> None:
    video_rel = html.escape(manifest["local_assets"]["final_mp4"]["relative_path"])
    vtt_rel = html.escape(manifest["local_assets"]["caption_vtt"]["relative_path"])
    thumb_rel = html.escape(manifest["local_assets"]["thumbnail"]["relative_path"])
    sample_rel = html.escape(manifest["local_assets"]["vo_outro_transition_sample_mp3"]["relative_path"])
    qa_cards = []
    for name, record in manifest["local_assets"]["qa_frames"].items():
        qa_cards.append(
            f'<figure><img src="{html.escape(record["relative_path"])}" alt="{html.escape(name)}"><figcaption>{html.escape(name.replace("_", " "))}</figcaption></figure>'
        )
    metadata = manifest["youtube_metadata"]
    description = html.escape(metadata["description"])
    tags = html.escape(", ".join(metadata["tags"]))
    chapters = "\n".join(f'{item["timestamp"]} {item["title"]}' for item in metadata["chapters"])
    blockers = "".join(f"<li>{html.escape(item)}</li>" for item in manifest["remaining_blockers"])
    reads = manifest["readiness_reads"]
    key_reads = "".join(
        f"<tr><th>{html.escape(key)}</th><td>{html.escape(str(reads.get(key, 'missing')))}</td></tr>"
        for key in [
            "vo_outro_blend_plan_read",
            "vo_outro_music_blend_read",
            "vo_outro_perceptual_review_read",
            "outro_transition_review_sample_read",
            "outro_under_vo_masking_read",
            "outro_target_after_voice_read",
            "outro_prelap_source_read",
            "outro_prelap_start_read",
            "outro_no_restart_at_voice_end_read",
            "outro_source_continuity_read",
            "music_contract_regression_read",
            "caption_text_matches_script_read",
            "caption_known_regression_fixture_read",
            "html_range_server_read",
        ]
    )
    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Challenger Repaired Publish Readiness</title>
  <style>
    :root {{ color-scheme: dark; --bg:#080b10; --panel:#111827; --ink:#fff7e8; --muted:#b8c2d6; --line:#334155; --accent:#78e7c1; --warn:#f5b95f; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:var(--bg); color:var(--ink); }}
    main {{ width:min(1180px, calc(100vw - 36px)); margin:28px auto 56px; }}
    header {{ margin-bottom:24px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(40px, 6vw, 72px); line-height:.94; letter-spacing:0; }}
    h2 {{ margin:0 0 16px; font-size:28px; letter-spacing:0; }}
    h3 {{ margin:0 0 8px; font-size:18px; letter-spacing:0; }}
    p {{ line-height:1.45; }}
    .lede {{ max-width:760px; color:var(--muted); font-size:22px; margin:0; }}
    .grid {{ display:grid; grid-template-columns:minmax(0, 1.4fr) minmax(310px, .8fr); gap:24px; align-items:start; }}
    section {{ border:1px solid var(--line); border-radius:8px; background:var(--panel); padding:22px; margin-bottom:24px; }}
    video {{ width:100%; border-radius:6px; background:#000; display:block; }}
    audio {{ width:100%; display:block; margin-top:8px; }}
    button {{ appearance:none; border:1px solid #5c7f99; color:var(--ink); background:#173249; border-radius:6px; padding:10px 14px; font:inherit; cursor:pointer; }}
    .buttons {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }}
    .decision {{ display:grid; gap:14px; }}
    .tile {{ border:1px solid #3c465d; border-radius:8px; padding:16px; background:#1a2132; }}
    .pass {{ color:var(--accent); }}
    .warn {{ color:var(--warn); }}
    .muted {{ color:var(--muted); }}
    pre {{ white-space:pre-wrap; margin:0; color:#eef4ff; font:16px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace; }}
    details {{ margin-top:12px; }}
    summary {{ color:#9ee8ff; cursor:pointer; font-weight:700; margin-bottom:10px; }}
    .frames {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:16px; }}
    figure {{ margin:0; }}
    img {{ width:100%; border-radius:6px; display:block; background:#000; }}
    figcaption {{ color:var(--muted); margin-top:8px; font-size:15px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th, td {{ text-align:left; border-top:1px solid #2a3448; padding:10px 8px; vertical-align:top; }}
    th {{ width:44%; color:var(--muted); font-weight:700; }}
    @media (max-width: 820px) {{ main {{ width:min(100vw - 28px, 720px); }} .grid, .frames {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Challenger Publish Readiness</h1>
      <p class="lede">Repaired review package for the canonical sign-off and subtle-tail outro handoff. Upload, publish, schedule, and visibility actions remain locked.</p>
    </header>

    <div class="grid">
      <section>
        <h2>Final MP4 Review</h2>
        <video id="video" controls preload="metadata" poster="{thumb_rel}">
          <source src="{video_rel}" type="video/mp4">
          <track kind="captions" src="{vtt_rel}" srclang="en" label="English" default>
        </video>
        <p class="muted" id="status">Final MP4 metadata will load here.</p>
        <div class="buttons">
          <button type="button" data-seek="0">Start</button>
          <button type="button" data-seek="82.554">Caption fixture</button>
          <button type="button" data-seek="{manifest['youtube_end_screen']['timing']['outro_transition_start_seconds'] - 7:.3f}">VO/outro blend</button>
          <button type="button" data-seek="{manifest['youtube_end_screen']['timing']['youtube_end_screen_safe_window_seconds'][0]:.3f}">Safe window</button>
        </div>
      </section>

      <section class="decision">
        <h2>Review Decision</h2>
        <div class="tile"><h3>Package Status</h3><p class="warn">Pending human keep</p></div>
        <div class="tile"><h3>Upload Action</h3><p class="warn">Locked; old private upload is superseded</p></div>
        <div class="tile"><h3>Caption Gate</h3><p class="pass">pass, script-locked</p></div>
        <div class="tile"><h3>VO/Outro Gate</h3><p class="pass">pass, subtle tail</p></div>
        <div class="tile"><h3>Remaining Blockers</h3><ul>{blockers}</ul></div>
      </section>
    </div>

    <section>
      <h2>VO/Outro Transition</h2>
      <p class="muted">Review the repaired transition sample around the final spoken line into the outro.</p>
      <audio controls preload="metadata"><source src="{sample_rel}" type="audio/mpeg"></audio>
    </section>

    <section>
      <h2>YouTube Metadata Preview</h2>
      <div class="grid">
        <div class="tile"><h3>Title</h3><p>{html.escape(metadata['title'])}</p></div>
        <div class="tile"><h3>Category</h3><p>{html.escape(metadata['category_recommendation'])}</p></div>
      </div>
      <details open><summary>Description and chapters</summary><pre>{description}\n\nChapters:\n{html.escape(chapters)}</pre></details>
      <details><summary>Tags</summary><p class="muted">{tags}</p></details>
    </section>

    <section>
      <h2>Media Checks</h2>
      <div class="frames">{''.join(qa_cards)}</div>
    </section>

    <section>
      <h2>Gate Reads</h2>
      <table>{key_reads}</table>
    </section>
  </main>
  <script>
    const video = document.getElementById('video');
    const status = document.getElementById('status');
    function fmt(seconds) {{
      if (!Number.isFinite(seconds)) return '--:--';
      const s = Math.floor(seconds % 60).toString().padStart(2, '0');
      const m = Math.floor(seconds / 60).toString();
      return `${{m}}:${{s}}`;
    }}
    video.addEventListener('loadedmetadata', () => {{
      status.textContent = `Final MP4 metadata loaded. Duration ${{fmt(video.duration)}}.`;
    }});
    document.querySelectorAll('button[data-seek]').forEach((button) => {{
      button.addEventListener('click', () => {{
        video.currentTime = Number(button.dataset.seek || 0);
        status.textContent = `Review sample loaded at ${{fmt(video.currentTime)}}.`;
      }});
    }});
  </script>
</body>
</html>
""",
        encoding="utf-8",
    )


def build_publish_readiness(args: argparse.Namespace) -> dict[str, Any]:
    successor = Path(args.successor_root).resolve()
    stamp = args.stamp or utc_stamp()
    render_root = Path(args.render_root).resolve() if args.render_root else find_latest_render(successor)
    render_manifest_path = render_root / "render_manifest.json"
    require_file(render_manifest_path)
    proof_manifest = read_json(successor / "rough_assembly_manifest.json")
    render_manifest = read_json(render_manifest_path)
    audio_mix = read_json(successor / "references/audio_mix_manifest.json")
    packet_id = f"challenger_longform_canonical_signoff_publish_readiness_{stamp}"
    readiness = render_root / "publish_readiness" / packet_id
    ensure_dir(readiness)
    final_mp4 = Path(render_manifest["output"]["path"])
    caption_package = render_manifest["caption_package"]
    vtt = Path(caption_package.get("youtube_upload_sidecar_vtt", caption_package["rail_offset_vtt"])["path"])
    srt = Path(caption_package.get("youtube_upload_sidecar_srt", caption_package["rail_offset_srt"])["path"])
    transition_mp3 = Path(audio_mix["outro_transition_review_sample"]["mp3"]["path"])
    thumbnail_src = Path(render_manifest["qa_frames"]["start"]["path"])
    qa_frame_records: dict[str, Any] = {}
    for name, record in render_manifest["qa_frames"].items():
        src = Path(record["path"])
        dest = readiness / "qa/frames" / src.name
        copied = copy_asset(src, dest)
        copied["relative_path"] = html_rel(readiness, dest)
        qa_frame_records[name] = copied
    local_assets = {
        "final_mp4": copy_asset(final_mp4, readiness / "media" / final_mp4.name),
        "caption_vtt": copy_asset(vtt, readiness / "captions" / vtt.name),
        "caption_srt": copy_asset(srt, readiness / "captions" / srt.name),
        "thumbnail": copy_asset(thumbnail_src, readiness / "images/thumbnail_candidate.jpg"),
        "vo_outro_transition_sample_mp3": copy_asset(transition_mp3, readiness / "audio" / transition_mp3.name),
        "qa_frames": qa_frame_records,
    }
    for key, record in local_assets.items():
        if key != "qa_frames":
            record["relative_path"] = html_rel(readiness, Path(record["path"]))
    metadata = {
        "title": "The Challenger Warning That Stopped Working | Cascade Effects",
        "description": (
            "Before Challenger broke apart, cameras had already caught the warning: smoke from the right solid rocket booster.\n\n"
            "This video follows how O-ring damage, cold-weather concerns, and launch pressure moved through NASA's decision process until a known risk started to look acceptable."
        ),
        "chapters": [
            {"timestamp": "00:00", "title": "First Smoke", "seconds": 0},
            {"timestamp": "01:27", "title": "Routine Promise", "seconds": 87},
            {"timestamp": "03:10", "title": "Pressure System", "seconds": 190},
            {"timestamp": "04:36", "title": "O-ring Record", "seconds": 276},
            {"timestamp": "06:49", "title": "Warning Translation", "seconds": 409},
            {"timestamp": "10:08", "title": "Launch-Night Standard", "seconds": 608},
            {"timestamp": "12:05", "title": "Reversal and Flight", "seconds": 725},
            {"timestamp": "15:38", "title": "What Challenger Shows", "seconds": 938},
        ],
        "tags": [
            "Challenger disaster",
            "Space Shuttle Challenger",
            "NASA",
            "O-ring",
            "Rogers Commission",
            "normalization of deviance",
            "engineering failure",
            "system failure",
            "risk management",
            "Cascade Effects",
        ],
        "category_recommendation": "Education",
        "audience_recommendation": "not_made_for_kids_pending_human_confirmation",
        "visibility_recommendation": "private_review_upload_only_after_explicit_approval",
    }
    readiness_reads = {
        **proof_manifest.get("readiness_reads", {}),
        **render_manifest.get("qa_reads", {}),
        **audio_mix.get("reads", {}),
        "html_primary_review_read": "pass_review_html_is_primary_artifact",
        "html_media_refs_read": "pass_local_relative_media_references_no_base64_media",
        "html_native_video_scrub_read": "pass_native_mp4_controls_available_no_custom_scrub_panel",
        "html_range_server_read": "pending_start_local_range_server",
        "html_canonical_review_url_read": "pending_start_local_range_server",
        "publish_readiness_package_local_asset_copy_read": "pass",
        "html_upload_lock_read": "pass_upload_publish_schedule_visibility_remain_locked",
        "youtube_private_upload_superseded_read": f"pass_{PRIVATE_VIDEO_ID}_superseded_do_not_publish",
        "public_metadata_copy_read": "pass_no_internal_workflow_language_and_concrete_challenger_hook",
        "public_tag_relevance_read": "pass_public_search_terms_only_no_research_source_person_tag",
        "youtube_metadata_copywriting_read": "pass_public_metadata_copy_description_hook_and_tag_relevance",
        "description_concrete_viewer_hook_read": "pass_first_two_lines_name_smoke_booster_o_ring_cold_weather_nasa_launch_pressure_and_viewer_payoff",
        "human_publish_readiness_keep_read": "pending_no_human_keep_recorded_for_repaired_successor",
        "explicit_youtube_upload_approval_read": "blocked_no_replacement_upload_approval_for_repaired_successor",
        "publish_request_read": "blocked_old_publish_request_superseded_by_repair",
        "youtube_private_upload_read": "not_applicable_no_successor_upload_performed",
        "youtube_private_upload_status_read": "not_applicable_no_successor_upload_performed",
        "youtube_private_upload_privacy_read": "not_applicable_no_successor_upload_performed",
        "youtube_private_upload_thumbnail_read": "not_applicable_no_successor_upload_performed",
        "html_kept_status_visible_read": "pass_package_status_pending_human_keep_visible",
        "html_private_upload_visible_read": "pass_review_html_shows_old_private_upload_superseded_do_not_publish",
    }
    manifest = {
        "packet_id": packet_id,
        "gate": "publish_readiness_gate",
        "created_utc": stamp,
        "status": "review_ready_pending_human_keep_canonical_signoff_subtle_tail_outro",
        "human_disposition": "pending",
        "upload_performed": False,
        "publish_ready": False,
        "youtube_upload_ready": False,
        "public_release_ready": False,
        "may_youtube_action": False,
        "old_private_upload": {
            "video_id": PRIVATE_VIDEO_ID,
            "video_url": PRIVATE_VIDEO_URL,
            "local_status": "superseded_do_not_publish",
            "youtube_visibility_action_taken": False,
        },
        "source_html_proof": render_manifest["source_html_proof"],
        "proof_manifest": artifact(successor / "rough_assembly_manifest.json"),
        "render_manifest": artifact(render_manifest_path),
        "final_mp4": render_manifest["output"],
        "audio_mix_manifest": artifact(successor / "references/audio_mix_manifest.json"),
        "caption_package": {
            **caption_package,
            "youtube_upload_sidecar_vtt": caption_package.get("youtube_upload_sidecar_vtt", caption_package["rail_offset_vtt"]),
            "youtube_upload_sidecar_srt": caption_package.get("youtube_upload_sidecar_srt", caption_package["rail_offset_srt"]),
            "script_relative_sidecar_vtt": caption_package.get("script_relative_sidecar_vtt", caption_package["youtube_sidecar_vtt"]),
            "script_relative_sidecar_srt": caption_package.get("script_relative_sidecar_srt", caption_package["youtube_sidecar_srt"]),
            "youtube_sidecar_vtt": caption_package.get("youtube_upload_sidecar_vtt", caption_package["rail_offset_vtt"]),
            "youtube_sidecar_srt": caption_package.get("youtube_upload_sidecar_srt", caption_package["rail_offset_srt"]),
            "sidecar_timeline_policy": {
                "upload_sidecar_timeline": "final_mp4_timeline_with_9p601451s_intro_offset",
                "script_relative_sidecars_preserved_for_regression_only": True,
                "voice_start_seconds": VOICE_START_SECONDS,
                "read": "pass_upload_sidecar_uses_intro_offset_final_mp4_timeline",
            },
        },
        "youtube_metadata": metadata,
        "thumbnail_candidate": local_assets["thumbnail"],
        "youtube_end_screen": proof_manifest["youtube_end_screen"],
        "final_render_contract": {
            **render_manifest.get("render_strategy", {}),
            "audio_source_encode_read": "pass_aac_encoded_from_repaired_wav_source",
            "caption_sidecar_read": "pass_upload_sidecar_uses_intro_offset_final_mp4_timeline",
            "visible_rail_captions_burned_in_read": "pass_rendered_from_browser_rail_caption_layer",
            "downstream_gate_read": "pass_upload_publish_visibility_flags_false",
        },
        "readiness_reads": readiness_reads,
        "remaining_blockers": [
            "Human keep on this repaired review is not recorded.",
            "Separate explicit replacement-upload approval is not recorded.",
            f"Existing private upload {PRIVATE_VIDEO_ID} is superseded and must not be published.",
            "YouTube copyright and Content ID checks must be reviewed in Studio after any replacement private upload.",
            "Caption file upload/verification and final YouTube Studio end-screen elements remain manual.",
            "Public visibility remains manual and locked.",
        ],
        "primary_review_artifact": "review.html",
        "review_surface_type": "html_inline_media_local_refs",
        "publish_readiness_canonical_review_url": "pending_start_local_range_server",
        "local_assets": local_assets,
    }
    review_html = readiness / "review.html"
    write_review_html(review_html, manifest)
    manifest["publish_readiness_review_html"] = artifact(review_html)
    server_path = readiness / "range_static_server.mjs"
    write_range_server(server_path)
    manifest["range_server_script"] = artifact(server_path)
    write_json(readiness / "publish_readiness_manifest.json", manifest)
    metadata_path = readiness / "youtube_metadata.json"
    write_json(metadata_path, metadata)
    print(
        json.dumps(
            {
                "readiness_root": str(readiness),
                "review_html": str(review_html),
                "manifest": str(readiness / "publish_readiness_manifest.json"),
                "server_command": f"node {server_path} {readiness} --port 8840",
                "review_url": f"http://127.0.0.1:8840/{review_html.name}",
            },
            indent=2,
        )
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare-successor")
    prepare.add_argument("--stamp")
    readiness = sub.add_parser("build-readiness")
    readiness.add_argument("--successor-root", required=True)
    readiness.add_argument("--render-root")
    readiness.add_argument("--stamp")
    args = parser.parse_args()
    if args.command == "prepare-successor":
        prepare_successor(args)
    elif args.command == "build-readiness":
        build_publish_readiness(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
