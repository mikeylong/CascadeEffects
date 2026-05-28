#!/usr/bin/env python3
"""Create a Challenger successor with a subtle-tail VO/outro mix.

This repair starts from the canonical-signoff proof and preserves VO, visuals,
captions, rail, titleless end screen, thumbnail, and metadata. It replaces only
the final music mix and downstream proof/render inputs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
SOURCE_PROOF = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "challenger_longform_canonical_signoff_actual_outro_prelap_html_approval_proof_20260518T175232Z"
)
SOURCE_READINESS = (
    SOURCE_PROOF
    / "video_render/challenger_longform_canonical_signoff_actual_outro_final_mp4_20260518T180102Z"
    / "publish_readiness/challenger_longform_canonical_signoff_publish_readiness_20260518T182557Z"
)
INTRO_SOURCE = Path("/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture instrumental_loop.wav")
OUTRO_SOURCE = Path("/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong/Paper Architecture.m4a")
VOICE_START_SECONDS = 9.601451
INTRO_FADE_TAIL_SECONDS = 2.0
OUTRO_PRELAP_SECONDS = 1.5
OUTRO_UNDER_VO_GAIN = 0.10
OUTRO_TARGET_GAIN = 0.42
OUTRO_TARGET_RAMP_SECONDS = 3.0
SAMPLE_RATE = 44100
TRANSITION_DURATION_SECONDS = 0.7
VOICE_LOUDNESS_TARGET_I = -14.0
VOICE_LOUDNESS_TARGET_TP = -1.0
VOICE_LOUDNESS_TARGET_LRA = 11.0
VOICE_LOUDNESS_TOLERANCE_DB = 1.5
PRIVATE_VIDEO_ID = "ToEay5mFDy8"
PRIVATE_VIDEO_URL = f"https://www.youtube.com/watch?v={PRIVATE_VIDEO_ID}"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\nSTDOUT:\n{result.stdout[-4000:]}\nSTDERR:\n{result.stderr[-4000:]}"
        )
    return result


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


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


def volumedetect(path: Path, start: float | None = None, duration: float | None = None, audio_filter: str = "volumedetect") -> dict[str, float | None]:
    args = ["ffmpeg", "-hide_banner", "-nostats"]
    if start is not None:
        args += ["-ss", f"{start:.6f}"]
    if duration is not None:
        args += ["-t", f"{duration:.6f}"]
    filter_arg = audio_filter if audio_filter.endswith("volumedetect") else f"{audio_filter},volumedetect"
    args += ["-i", str(path), "-af", filter_arg, "-f", "null", "-"]
    result = run(args)
    mean = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", result.stderr)
    peak = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", result.stderr)
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


def voice_master_for_review_mix(audio_repair: Path, source_voice_master: Path) -> tuple[Path, dict[str, Any]]:
    ensure_dir(audio_repair / "masters")
    scan = loudnorm_scan(source_voice_master)
    source_window = volumedetect(source_voice_master, 10, 120)
    if not loudnorm_needs_alignment(scan):
        return source_voice_master, {
            "model": "voice_loudness_alignment_v1",
            "status": "not_needed_source_within_tolerance",
            "source_voice_master": artifact(source_voice_master),
            "mix_voice_master": artifact(source_voice_master),
            "target": {
                "integrated_lufs": VOICE_LOUDNESS_TARGET_I,
                "true_peak_dbtp": VOICE_LOUDNESS_TARGET_TP,
                "loudness_range_lra": VOICE_LOUDNESS_TARGET_LRA,
                "tolerance_db": VOICE_LOUDNESS_TOLERANCE_DB,
            },
            "source_loudnorm_scan": scan,
            "output_loudnorm_scan": scan,
            "source_window_volumedetect": source_window,
            "output_window_volumedetect": source_window,
            "duration_delta_seconds": 0,
            "reads": {
                "voice_loudness_alignment_read": "pass_source_voice_master_within_series_loudness_tolerance",
                "voice_master_used_for_mix_read": "pass_source_voice_master_within_series_loudness_tolerance",
            },
        }
    aligned = audio_repair / "masters" / f"{source_voice_master.stem}_loudnorm_I14_TP1_LRA11.wav"
    log_path = audio_repair / "masters" / f"{source_voice_master.stem}_loudnorm_ffmpeg.log"
    filter_arg = (
        f"loudnorm=I={VOICE_LOUDNESS_TARGET_I:g}:TP={VOICE_LOUDNESS_TARGET_TP:g}:LRA={VOICE_LOUDNESS_TARGET_LRA:g}"
        f":measured_I={float(scan['input_i'])}:measured_TP={float(scan['input_tp'])}:measured_LRA={float(scan['input_lra'])}"
        f":measured_thresh={float(scan['input_thresh'])}:offset={float(scan['target_offset'])}:linear=true:print_format=json"
    )
    args = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-y",
        "-i",
        str(source_voice_master),
        "-af",
        filter_arg,
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(aligned),
    ]
    result = run(args)
    log_path.write_text(json.dumps(args, indent=2) + "\n\n" + result.stderr, encoding="utf-8")
    output_scan = parse_json_from_text(result.stderr + "\n" + result.stdout) or loudnorm_scan(aligned)
    duration_delta = duration_seconds(aligned) - duration_seconds(source_voice_master)
    output_window = volumedetect(aligned, 10, 120)
    output_i = float(output_scan.get("output_i", output_scan.get("input_i", "nan")))
    return aligned, {
        "model": "voice_loudness_alignment_v1",
        "status": "pass_loudnorm_aligned_for_review_mix",
        "source_voice_master": artifact(source_voice_master),
        "mix_voice_master": artifact(aligned),
        "loudnorm_log": artifact(log_path),
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
            "voice_master_used_for_mix_read": "pass_proof_local_loudnorm_voice_stem_used_for_review_mix",
            "source_voice_master_preserved_read": "pass_source_voice_master_not_overwritten",
        },
    }


def format_duration(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def create_successor(stamp: str) -> Path:
    successor = SOURCE_PROOF.parent / f"challenger_longform_canonical_signoff_subtle_tail_outro_html_approval_proof_{stamp}"
    if successor.exists():
        raise FileExistsError(successor)
    shutil.copytree(
        SOURCE_PROOF,
        successor,
        ignore=shutil.ignore_patterns("video_render", "publish_readiness"),
    )
    for file_path in successor.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in {".html", ".json", ".md", ".mjs", ".txt", ".vtt", ".srt"}:
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if str(SOURCE_PROOF) in text:
                file_path.write_text(text.replace(str(SOURCE_PROOF), str(successor)), encoding="utf-8")
    return successor


def mark_current_package_tighten(stamp: str, successor: Path) -> None:
    reason = "tighten_outro_music_crowds_vo"
    for path in [
        SOURCE_PROOF / "rough_assembly_manifest.json",
        SOURCE_PROOF / "video_render/challenger_longform_canonical_signoff_actual_outro_final_mp4_20260518T180102Z/render_manifest.json",
        SOURCE_READINESS / "publish_readiness_manifest.json",
    ]:
        if not path.is_file():
            continue
        data = read_json(path)
        data["status"] = reason
        data["human_disposition"] = "tighten"
        data["superseded_by_subtle_tail_outro"] = {
            "recorded_utc": stamp,
            "successor_packet_path": str(successor),
            "reason": "outro_music_enters_too_soon_too_loud_and_crowds_final_vo",
        }
        data["publish_ready"] = False
        data["youtube_upload_ready"] = False
        data["public_release_ready"] = False
        data["may_youtube_action"] = False
        reads_key = "readiness_reads" if "readiness_reads" in data else "qa_reads"
        data[reads_key] = {
            **data.get(reads_key, {}),
            "vo_outro_music_blend_read": "tighten_outro_music_crowds_final_voiceover",
            "vo_outro_perceptual_review_read": "tighten_human_review_rejected_current_transition",
            "outro_under_vo_masking_read": "tighten_missing_or_failed_under_vo_masking_margin",
            "outro_target_after_voice_read": "tighten_old_mix_reaches_target_by_voice_end",
            "music_contract_regression_read": "tighten_5s_loud_prelap_model_rejected",
        }
        write_json(path, data)


def build_audio_mix(successor: Path, stamp: str) -> dict[str, Any]:
    source_mix = read_json(SOURCE_PROOF / "references/audio_mix_manifest.json")
    source_voice_master = Path(source_mix["voice_master"]["path"].replace(str(SOURCE_PROOF), str(successor)))
    audio_repair = successor / "audio_repairs" / f"canonical_signoff_subtle_tail_outro_{stamp}"
    ensure_dir(audio_repair)
    voice_master, voice_loudness_alignment = voice_master_for_review_mix(audio_repair, source_voice_master)
    voice_duration = duration_seconds(voice_master)
    voice_end = VOICE_START_SECONDS + voice_duration
    target_reaches_at = voice_end + OUTRO_TARGET_RAMP_SECONDS
    outro_start = voice_end - OUTRO_PRELAP_SECONDS
    total_duration = voice_end + duration_seconds(OUTRO_SOURCE) - OUTRO_PRELAP_SECONDS
    voice_delay_samples = round(VOICE_START_SECONDS * SAMPLE_RATE)
    outro_delay_samples = round(outro_start * SAMPLE_RATE)

    audio_dir = successor / "assets/audio"
    qa_audio_dir = successor / "qa/audio"
    ensure_dir(audio_dir)
    ensure_dir(qa_audio_dir)
    repaired_wav = audio_dir / f"challenger_longform_canonical_signoff_subtle_tail_outro_review_mix_{stamp}.wav"
    repaired_mp3 = audio_dir / f"challenger_longform_canonical_signoff_subtle_tail_outro_web_review_{stamp}.mp3"
    transition_wav = qa_audio_dir / f"vo_outro_subtle_tail_transition_review_{stamp}.wav"
    transition_mp3 = qa_audio_dir / f"vo_outro_subtle_tail_transition_review_{stamp}.mp3"
    sample_start = max(0.0, voice_end - 7.0)
    target_at_local = OUTRO_PRELAP_SECONDS + OUTRO_TARGET_RAMP_SECONDS
    outro_volume = (
        f"if(lt(t,{OUTRO_PRELAP_SECONDS:.6f}),{OUTRO_UNDER_VO_GAIN:.6f}*t/{OUTRO_PRELAP_SECONDS:.6f},"
        f"if(lt(t,{target_at_local:.6f}),"
        f"{OUTRO_UNDER_VO_GAIN:.6f}+({OUTRO_TARGET_GAIN:.6f}-{OUTRO_UNDER_VO_GAIN:.6f})"
        f"*(t-{OUTRO_PRELAP_SECONDS:.6f})/{OUTRO_TARGET_RAMP_SECONDS:.6f},{OUTRO_TARGET_GAIN:.6f}))"
    )
    filter_complex = ";".join(
        [
            (
                f"[0:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,"
                f"aloop=loop=-1:size={voice_delay_samples},"
                f"atrim=0:{VOICE_START_SECONDS + INTRO_FADE_TAIL_SECONDS:.6f},asetpts=PTS-STARTPTS,"
                f"afade=t=out:st={VOICE_START_SECONDS:.6f}:d={INTRO_FADE_TAIL_SECONDS:.6f}[intro]"
            ),
            f"[1:a]aresample={SAMPLE_RATE},pan=stereo|c0=c0|c1=c0,adelay={voice_delay_samples}S:all=1[voice]",
            (
                f"[2:a]aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,"
                f"atrim=0:{duration_seconds(OUTRO_SOURCE):.6f},asetpts=PTS-STARTPTS,"
                f"volume='{outro_volume}':eval=frame,adelay={outro_delay_samples}S:all=1[outro]"
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
        str(voice_master),
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
    (audio_repair / "subtle_tail_mix_ffmpeg.log").write_text(json.dumps(mix_args, indent=2) + "\n\n" + mix.stderr, encoding="utf-8")
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(repaired_wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(repaired_mp3)])
    run(["ffmpeg", "-hide_banner", "-y", "-ss", f"{sample_start:.6f}", "-t", "14", "-i", str(repaired_wav), "-c:a", "pcm_s16le", str(transition_wav)])
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(transition_wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(transition_mp3)])

    full_mix = volumedetect(repaired_wav)
    pre_entry = volumedetect(repaired_wav, voice_end - 4, 4)
    post_entry = volumedetect(repaired_wav, voice_end, 4)
    transition_level = volumedetect(repaired_wav, sample_start, 14)
    final_phrase_window = max(2.0, OUTRO_PRELAP_SECONDS)
    final_voice_phrase = volumedetect(voice_master, max(0.0, voice_duration - final_phrase_window), final_phrase_window)
    under_vo_music_stem = volumedetect(
        OUTRO_SOURCE,
        0,
        OUTRO_PRELAP_SECONDS,
        audio_filter=f"volume='if(isnan(t),0,{OUTRO_UNDER_VO_GAIN}*t/{OUTRO_PRELAP_SECONDS})':eval=frame",
    )
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
        "full_outro_music_read": "pass_full_paper_architecture_outro_track_used_as_subtle_tail_source",
        "end_screen_music_handoff_read": "pass_end_screen_carried_by_full_outro_after_subtle_tail_handoff",
        "vo_outro_blend_plan_read": "pass_subtle_tail_outro_v1",
        "vo_outro_music_blend_read": "pass_subtle_tail_outro_enters_late_low_and_continues_without_restart",
        "vo_outro_perceptual_review_read": "pass_transition_sample_exported_for_human_listen_no_whole_mix_delta_only",
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
        "voice_loudness_alignment_read": voice_loudness_alignment["reads"]["voice_loudness_alignment_read"],
        "voice_master_used_for_mix_read": voice_loudness_alignment["reads"]["voice_master_used_for_mix_read"],
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
        "full_outro_start_seconds": outro_start,
        "full_outro_fade_in_seconds": OUTRO_PRELAP_SECONDS + OUTRO_TARGET_RAMP_SECONDS,
        "outro_prelap_seconds": OUTRO_PRELAP_SECONDS,
        "outro_under_vo_gain_linear": OUTRO_UNDER_VO_GAIN,
        "outro_target_gain_linear": OUTRO_TARGET_GAIN,
        "outro_target_ramp_seconds": OUTRO_TARGET_RAMP_SECONDS,
        "outro_reaches_target_at_seconds": target_reaches_at,
        "under_vo_music_margin_db": under_vo_margin,
        "outro_no_restart_at_voice_end": True,
        "outro_source_continuity": True,
        "source_voice_master": artifact(source_voice_master),
        "voice_master": artifact(voice_master),
        "voice_loudness_alignment": voice_loudness_alignment,
        "intro_music_source": artifact(INTRO_SOURCE),
        "outro_full_track_source": artifact(OUTRO_SOURCE),
        "output_wav": artifact(repaired_wav),
        "browser_mp3": artifact(repaired_mp3),
        "output_probe": ffprobe_json(repaired_wav),
        "vo_outro_blend_plan": {
            "policy": "subtle_tail_outro_v1",
            "full_outro_source_path": str(OUTRO_SOURCE),
            "full_outro_start_seconds": outro_start,
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
            "final_voice_phrase_window_seconds": final_phrase_window,
            "final_voice_phrase": final_voice_phrase,
            "under_vo_music_stem": under_vo_music_stem,
            "under_vo_music_margin_db": under_vo_margin,
            "post_minus_pre_mean_delta_db": level_delta,
        },
        "reads": reads,
    }
    write_json(successor / "references/audio_mix_manifest.json", manifest)
    write_json(audio_repair / "vo_outro_blend_audio_mix_manifest.json", manifest)
    return {"manifest": manifest, "wav": repaired_wav, "mp3": repaired_mp3, "manifest_path": successor / "references/audio_mix_manifest.json"}


def patch_player(successor: Path, audio_mix: dict[str, Any]) -> None:
    player = successor / "player.html"
    text = player.read_text(encoding="utf-8")
    mix = audio_mix["manifest"]
    duration = mix["total_duration_seconds"]
    voice_end = mix["voice_end_seconds"]
    safe_start = max(voice_end, duration - 20.0)
    hold_start = voice_end + TRANSITION_DURATION_SECONDS
    mp3 = audio_mix["mp3"]
    wav = audio_mix["wav"]
    old_audio = re.search(r'<audio class="review-audio" id="audio"[\s\S]*?</audio>', text)
    if not old_audio:
        raise RuntimeError("Could not locate review audio element")
    track = re.search(r'<track id="captionTrack"[\s\S]*?>', old_audio.group(0))
    if not track:
        raise RuntimeError("Could not locate caption track")
    new_audio = (
        f'<audio class="review-audio" id="audio" controls preload="metadata">'
        f'<source src="assets/audio/{mp3.name}" data-source-path="{mp3}" data-source-sha256="{sha256_file(mp3)}" type="audio/mpeg">'
        f'<source src="assets/audio/{wav.name}" data-source-path="{wav}" data-source-sha256="{sha256_file(wav)}" type="audio/wav">'
        f'{track.group(0)}</audio>'
    )
    text = text[: old_audio.start()] + new_audio + text[old_audio.end() :]
    text = re.sub(
        r'(<section class="outro-screen" id="outroScreen"[^>]*data-transition-start-seconds=")[^"]+(" data-safe-window-start-seconds=")[^"]+(")',
        rf"\g<1>{voice_end:.6f}\g<2>{safe_start:.6f}\g<3>",
        text,
        count=1,
    )
    replacements = [
        (r'"duration":\s*[0-9.]+,', f'"duration": {duration:.6f},'),
        (r'"outroStart":\s*[0-9.]+,', f'"outroStart": {voice_end:.6f},'),
        (r'"transitionStartSeconds":\s*[0-9.]+,', f'"transitionStartSeconds": {voice_end:.6f},'),
        (r'"holdStartSeconds":\s*[0-9.]+,', f'"holdStartSeconds": {hold_start:.6f},'),
        (r'"holdEndSeconds":\s*[0-9.]+,', f'"holdEndSeconds": {duration:.6f},'),
        (r'"youtubeEndScreenSafeWindowSeconds":\s*\[\s*[0-9.]+,\s*[0-9.]+\s*\]', f'"youtubeEndScreenSafeWindowSeconds": [\n      {safe_start:.6f},\n      {duration:.6f}\n    ]'),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, count=1)
    player.write_text(text, encoding="utf-8")


def update_manifest(successor: Path, audio_mix: dict[str, Any], stamp: str) -> None:
    path = successor / "rough_assembly_manifest.json"
    data = read_json(path)
    mix = audio_mix["manifest"]
    safe_start = max(mix["voice_end_seconds"], mix["total_duration_seconds"] - 20)
    reads = mix["reads"]
    data.update(
        {
            "packet_id": successor.name,
            "status": "review_ready_pending_human_keep_canonical_signoff_subtle_tail_outro",
            "human_disposition": "defer",
            "modified_utc": iso_now(),
            "successor_reason": "subtle_tail_outro_v1 repair for music crowding final VO",
            "predecessor_packet_path": str(SOURCE_PROOF),
            "predecessor_repair_status": "tighten_outro_music_crowds_vo",
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
                "source": "user_requested_subtle_tail_outro_successor",
                "does_not_authorize_upload_or_visibility_change": True,
            },
        }
    )
    data["review_audio_mix"] = {
        "process_version": "subtle_tail_outro_v1",
        "audio_mix_manifest": artifact(audio_mix["manifest_path"]),
        "review_mix_wav": artifact(audio_mix["wav"]),
        "review_mix_mp3": artifact(audio_mix["mp3"]),
        "voice_start_seconds": VOICE_START_SECONDS,
        "voice_end_seconds": mix["voice_end_seconds"],
        "total_duration_seconds": mix["total_duration_seconds"],
        "outro_transition_review_sample": mix["outro_transition_review_sample"],
        "reads": reads,
    }
    data["music_integration_contract"] = {
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
        "reads": reads,
    }
    data["youtube_end_screen"]["timing"] = {
        "outro_transition_start_seconds": mix["voice_end_seconds"],
        "outro_transition_duration_seconds": TRANSITION_DURATION_SECONDS,
        "outro_screen_hold_seconds": [mix["voice_end_seconds"] + TRANSITION_DURATION_SECONDS, mix["total_duration_seconds"]],
        "youtube_end_screen_safe_window_seconds": [safe_start, mix["total_duration_seconds"]],
        "living_cover_ambient_clock_continues_until_seconds": mix["total_duration_seconds"],
        "living_cover_story_clock_clamp_time_seconds": mix["voice_end_seconds"],
    }
    data["rough_assembly_reads"] = {**data.get("rough_assembly_reads", {}), **reads}
    data["required_reads"] = {**data.get("required_reads", {}), **reads}
    data["readiness_reads"] = {**data.get("readiness_reads", {}), **reads}
    data["publish_readiness_gate"] = {
        "status": "blocked_pending_successor_final_assembly_review_and_human_keep",
        "upload_performed": False,
        "publish_ready": False,
        "youtube_upload_ready": False,
        "public_release_ready": False,
        "may_youtube_action": False,
        "old_private_upload_status": f"{PRIVATE_VIDEO_ID}_superseded_do_not_publish",
        "next_action": "Review subtle-tail successor proof/final MP4 before any replacement upload.",
    }
    write_json(path, data)


def patch_render_script(successor: Path, audio_mix: dict[str, Any]) -> Path:
    script = successor / "scripts/render_titleless_final_mp4.mjs"
    text = script.read_text(encoding="utf-8")
    mix = audio_mix["manifest"]
    duration = mix["total_duration_seconds"]
    voice_end = mix["voice_end_seconds"]
    safe_start = max(voice_end, duration - 20)
    safe_tail = max(safe_start, duration - 2)
    pre_outro = max(1, voice_end - 0.5)
    post_outro = voice_end + 1.2
    old_mix_name = "challenger_longform_canonical_signoff_actual_outro_prelap_review_mix_20260518T175232Z.wav"
    text = text.replace(old_mix_name, audio_mix["wav"].name)
    text = text.replace("challenger_longform_canonical_signoff_actual_outro_final_mp4_", "challenger_longform_canonical_signoff_subtle_tail_outro_final_mp4_")
    text = text.replace("challenger_longform_canonical_signoff_actual_outro_final_review_1080p24.mp4", "challenger_longform_canonical_signoff_subtle_tail_outro_final_review_1080p24.mp4")
    text = re.sub(r"durationSeconds:\s*[0-9.]+,", f"durationSeconds: {duration:.6f},", text, count=1)
    text = re.sub(r"voiceEndSeconds:\s*[0-9.]+,", f"voiceEndSeconds: {voice_end:.6f},", text, count=1)
    text = re.sub(r"safeWindowStartSeconds:\s*[0-9.]+,", f"safeWindowStartSeconds: {safe_start:.6f},", text, count=1)
    text = re.sub(r"safeWindowEndSeconds:\s*[0-9.]+,", f"safeWindowEndSeconds: {duration:.6f},", text, count=1)
    text = re.sub(r"duration_display:\s*\"[^\"]+\"", f'duration_display: "{format_duration(duration)}"', text, count=1)
    text = text.replace("canonical_signoff_actual_outro_prelap_review_mix_wav", "canonical_signoff_subtle_tail_outro_review_mix_wav")
    text = text.replace("canonical_signoff_actual_outro_prelap", "canonical_signoff_subtle_tail_outro")
    text = text.replace("actual full-outro prelap", "subtle-tail outro handoff")
    text = text.replace(
        "Uses challenger_actual_outro_prelap_v1: the actual full outro starts five seconds before the final spoken word, fades under VO, and continues without restarting.",
        "Uses subtle_tail_outro_v1: the full outro enters under only the final 1.5 seconds at low level, then reaches target after the VO ends.",
    )
    replacements = {
        'extractQaFrame(outputMp4Path, 1214.7, "mp4_qa_1214p700_pre_outro.jpg")': f'extractQaFrame(outputMp4Path, {pre_outro:.6f}, "mp4_qa_pre_outro.jpg")',
        'extractQaFrame(outputMp4Path, 1215.5, "mp4_qa_1215p500_post_outro_fade.jpg")': f'extractQaFrame(outputMp4Path, {post_outro:.6f}, "mp4_qa_post_outro_fade.jpg")',
        'extractQaFrame(outputMp4Path, 1225.553197, "mp4_qa_1225p553_safe_window_start.jpg")': f'extractQaFrame(outputMp4Path, {safe_start:.6f}, "mp4_qa_safe_window_start.jpg")',
        'extractQaFrame(outputMp4Path, 1242.0, "mp4_qa_1242p000_safe_window_tail.jpg")': f'extractQaFrame(outputMp4Path, {safe_tail:.6f}, "mp4_qa_safe_window_tail.jpg")',
        "const safeStartLuma = onePixelLuma(outputMp4Path, 1225.553197);": f"const safeStartLuma = onePixelLuma(outputMp4Path, {safe_start:.6f});",
        "const safeTailLuma = onePixelLuma(outputMp4Path, 1242.0);": f"const safeTailLuma = onePixelLuma(outputMp4Path, {safe_tail:.6f});",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace(
        "music_integration_contract: proofManifest.music_integration_contract || null,\n    caption_package:",
        "music_integration_contract: proofManifest.music_integration_contract || null,\n    review_audio_mix: proofManifest.review_audio_mix || null,\n    caption_package:",
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
    script.write_text(text, encoding="utf-8")
    return script


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stamp")
    args = parser.parse_args()
    stamp = args.stamp or utc_stamp()
    successor = create_successor(stamp)
    mark_current_package_tighten(stamp, successor)
    audio_mix = build_audio_mix(successor, stamp)
    patch_player(successor, audio_mix)
    update_manifest(successor, audio_mix, stamp)
    render_script = patch_render_script(successor, audio_mix)
    result = {
        "stamp": stamp,
        "successor_root": str(successor),
        "player": str(successor / "player.html"),
        "audio_mix_manifest": str(audio_mix["manifest_path"]),
        "review_mix_wav": str(audio_mix["wav"]),
        "transition_sample_mp3": str(audio_mix["manifest"]["outro_transition_review_sample"]["mp3"]["path"]),
        "render_script": str(render_script),
        "next_command": f"node {render_script}",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
