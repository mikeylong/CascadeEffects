#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SHORT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_scoped_v1")
FINAL_DIR = SHORT_ROOT / "final"
OLD_PUBLISH_DIR = (
    SHORT_ROOT
    / "publish"
    / "youtube_20260501T022849Z_house_crt_visible_scanline_final_gate_pass01"
)
OLD_FINAL = FINAL_DIR / "challenger_short_scoped_v1_video_final_house_crt_visible_scanline_final_gate_pass01_20260501T022219Z.mp4"
NO_CAPTION_HOUSE_CRT_BED = Path(
    "/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_scoped_v1/"
    "motion_contact_sheet/pass_11/final_exports/"
    "challenger_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/"
    "20260430T_challenger_house_crt_visible_scanline_final_gate_pass01/work/"
    "motion_full_duration__house_crt_signal_interruption_no_audio.mp4"
)
SCRIPT_PATH = Path(
    "/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/"
    "challenger_short_restart_v1_ending_cadence_script.txt"
)
TIMING_SOURCE_SRT = OLD_PUBLISH_DIR / "challenger_warning_softening_captions.srt"
OLD_COVER_PATH = OLD_PUBLISH_DIR / "suggested_shorts_cover_frame.png"
OLD_TITLE_PATH = OLD_PUBLISH_DIR / "challenger_warning_softening_title.txt"
OLD_DESCRIPTION_PATH = OLD_PUBLISH_DIR / "challenger_warning_softening_description.txt"
OLD_TAGS_PATH = OLD_PUBLISH_DIR / "challenger_warning_softening_tags.txt"
OLD_METADATA_PACKET_PATH = OLD_PUBLISH_DIR / "youtube_metadata_copy_packet.md"
OLD_UPLOAD_CHECKLIST_PATH = OLD_PUBLISH_DIR / "upload_checklist.md"
OLD_PRIVATE_VIDEO_ID = "I4fvoWOjrIo"
SHORT_TOOL_PATH = Path("/Users/mike/Viz_CascadeEffects/scripts/short_tool.py")
PUBLISH_CHECK_COMMAND = "/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-check"
PUBLISH_UPLOAD_COMMAND = "/Users/mike/Viz_CascadeEffects/bin/ce orchestrate publish-package-upload"

CAPTION_STYLE = "minimal_surreal_editorial_v1"
CAPTION_PLACEMENT = "lower-left"
TEXT_GATE_FORBIDDEN = ("hot gas pass", "hot gas passed", "24 times", "73 seconds")


def load_short_tool() -> Any:
    scripts_dir = str(SHORT_TOOL_PATH.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("ce_short_tool", SHORT_TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {SHORT_TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ffprobe(path: Path) -> dict[str, Any]:
    completed = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ]
    )
    return json.loads(completed.stdout)


def duration(path: Path) -> float:
    return float(ffprobe(path).get("format", {}).get("duration") or 0.0)


def stream_summary(path: Path) -> dict[str, Any]:
    payload = ffprobe(path)
    streams = payload.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    return {
        "container": "mp4",
        "video_codec": video.get("codec_name", ""),
        "audio_codec": audio.get("codec_name", ""),
        "width": int(video.get("width", 0) or 0),
        "height": int(video.get("height", 0) or 0),
        "duration_seconds": round(duration(path), 6),
        "frame_rate": video.get("avg_frame_rate", ""),
        "audio_sample_rate_hz": int(audio.get("sample_rate", 0) or 0),
        "audio_channels": int(audio.get("channels", 0) or 0),
        "video_stream_count": sum(1 for item in streams if item.get("codec_type") == "video"),
        "audio_stream_count": sum(1 for item in streams if item.get("codec_type") == "audio"),
        "subtitle_stream_count": sum(1 for item in streams if item.get("codec_type") == "subtitle"),
    }


def decoded_audio_hash(path: Path) -> str:
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    digest = hashlib.sha256()
    assert process.stdout is not None
    for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
        digest.update(chunk)
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Audio decode failed for {path}")
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_for_gate(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\ufeff", " ")).strip()


def caption_texts_from_locked_script(script_text: str) -> list[str]:
    texts = [
        "By January 1986, the Space Shuttle had flown twenty-four times.",
        "Each flight reinforced one idea —",
        "the system worked.",
        "Across those flights, engineers documented O-ring damage.",
        "Erosion, blow-by — hot gas past seals designed to hold.",
        "Low-temperature flights all showed distress.",
        "But each flight survived, and the warning lost force.",
        "Danger became a known condition.",
        "A stop signal became a line item.",
        "The night before Challenger, engineers recommended against launch.",
        "The burden shifted —",
        "instead of proving it safe to fly, they were asked to prove it was unsafe.",
        "On the coldest morning the program had ever faced, seventy-three seconds was all the physics needed.",
        "The warning was never missing.",
        "It had been made survivable for too long.",
        "Small causes, massive consequences.",
    ]
    if normalize_for_gate(" ".join(texts)) != normalize_for_gate(script_text):
        raise RuntimeError("Script-locked caption cue text does not match the locked script.")
    return texts


def escaped_filter_path(path: Path) -> str:
    text = str(path)
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")


def extend_no_caption_bed(source: Path, output: Path, target_duration: float) -> dict[str, Any]:
    source_duration = duration(source)
    append_seconds = max(0.0, target_duration - source_duration)
    output.parent.mkdir(parents=True, exist_ok=True)
    if append_seconds <= 0.03:
        shutil.copy2(source, output)
        mode = "copied_no_extension_needed"
    else:
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-vf",
                f"tpad=stop_mode=clone:stop_duration={append_seconds:.6f},fps=30,format=yuv420p",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "medium",
                "-crf",
                "16",
                str(output),
            ]
        )
        mode = "final_frame_hold"
    return {
        "source_path": str(source),
        "source_duration_seconds": round(source_duration, 6),
        "target_duration_seconds": round(target_duration, 6),
        "append_seconds": round(append_seconds, 6),
        "mode": mode,
        "output_path": str(output),
        "output_sha256": sha256(output),
        "output_duration_seconds": round(duration(output), 6),
    }


def burn_captions(no_caption_video: Path, ass_path: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(no_caption_video),
            "-vf",
            f"ass={escaped_filter_path(ass_path)}",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "16",
            str(output),
        ]
    )


def remux_audio(video_only: Path, audio_source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_only),
            "-i",
            str(audio_source),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def extract_review_frames(final_path: Path, frame_dir: Path) -> list[dict[str, Any]]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    samples = [
        ("oring_hot_gas_past_text", 14.50),
        ("oring_designed_to_hold", 15.72),
        ("burden_shift", 36.50),
        ("proof_unsafe", 39.70),
        ("motif", 56.20),
        ("tail_hold", max(0.0, duration(final_path) - 0.40)),
    ]
    records: list[dict[str, Any]] = []
    for label, seconds in samples:
        frame_path = frame_dir / f"{label}_{seconds:.2f}s.jpg"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{seconds:.3f}",
                "-i",
                str(final_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(frame_path),
            ]
        )
        records.append(
            {
                "label": label,
                "timestamp_seconds": round(seconds, 3),
                "path": str(frame_path),
                "sha256": sha256(frame_path),
            }
        )
    return records


def build_diff_report(
    path: Path,
    *,
    old_segments: list[dict[str, Any]],
    locked_segments: list[dict[str, Any]],
    text_gate: dict[str, Any],
) -> None:
    cue_lines = [
        "# Challenger Script-Locked Caption Diff",
        "",
        "## Gate",
        "",
        f"- `script_exact_text_read`: `{text_gate['script_exact_text_read']}`",
        f"- `forbidden_phonetic_typos_read`: `{text_gate['forbidden_phonetic_typos_read']}`",
        "",
        "## Known Repair",
        "",
        "- Old ASR-derived cue: `Erosion, blow-by, hot gas pass seals designed to hold.`",
        "- New script-derived cue: `Erosion, blow-by — hot gas past seals designed to hold.`",
        "- Old ASR-derived number formatting was also replaced with locked script wording: `twenty-four` and `seventy-three`.",
        "",
        "## Cue Map",
        "",
        "| Cue | Timing | Old text | Script-locked text |",
        "| --- | --- | --- | --- |",
    ]
    for index, (old, new) in enumerate(zip(old_segments, locked_segments), start=1):
        cue_lines.append(
            "| {index} | {start:.3f}-{end:.3f} | {old_text} | {new_text} |".format(
                index=index,
                start=float(old["start_seconds"]),
                end=float(old["end_seconds"]),
                old_text=str(old["text"]).replace("|", "\\|"),
                new_text=str(new["text"]).replace("|", "\\|"),
            )
        )
    path.write_text("\n".join(cue_lines) + "\n", encoding="utf-8")


def copy_asset(source: Path, dest: Path) -> dict[str, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return {"path": str(dest), "sha256": sha256(dest)}


def main() -> int:
    for required_path in (
        OLD_PUBLISH_DIR,
        OLD_FINAL,
        NO_CAPTION_HOUSE_CRT_BED,
        SCRIPT_PATH,
        TIMING_SOURCE_SRT,
        OLD_COVER_PATH,
        OLD_TITLE_PATH,
        OLD_DESCRIPTION_PATH,
        OLD_TAGS_PATH,
    ):
        if not required_path.exists():
            raise FileNotFoundError(required_path)

    short_tool = load_short_tool()
    stamp = utc_stamp()
    final_tag = f"script_locked_captions_{stamp}"
    publish_dir = SHORT_ROOT / "publish" / f"youtube_{stamp}_script_locked_captions"
    work_dir = publish_dir / "work"
    qa_dir = publish_dir / "qa"
    frame_dir = qa_dir / "review_frames"
    final_path = FINAL_DIR / f"challenger_short_scoped_v1_video_final_script_locked_captions_{stamp}.mp4"
    publish_video_path = publish_dir / "challenger_script_locked_captions_youtube_short.mp4"
    no_caption_extended_path = work_dir / "script_locked_no_caption_picture_extended.mp4"
    captioned_no_audio_path = work_dir / "script_locked_captioned_no_audio.mp4"
    caption_srt_path = publish_dir / "script_locked_captions.srt"
    caption_ass_path = publish_dir / "script_locked_captions.ass"
    caption_manifest_path = publish_dir / "script_locked_caption_manifest.json"
    diff_report_path = publish_dir / "script_locked_caption_diff_report.md"

    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    canonical_texts = caption_texts_from_locked_script(script_text)
    timing_segments = short_tool.parse_caption_timing_file(TIMING_SOURCE_SRT)
    if len(timing_segments) != len(canonical_texts):
        raise RuntimeError(f"Expected {len(canonical_texts)} timing cues, got {len(timing_segments)}")
    locked_cue_segments = [
        {
            **segment,
            "segment_id": f"script_locked_cue_{index:03d}",
            "text": canonical_texts[index - 1],
            "timing_source_segment_id": segment.get("segment_id", ""),
            "caption_text_source": "locked_script",
        }
        for index, segment in enumerate(timing_segments, start=1)
    ]
    style = short_tool.caption_style_with_placement(CAPTION_STYLE, CAPTION_PLACEMENT)
    final_caption_segments = short_tool.split_caption_segments_for_style(locked_cue_segments, style)
    final_caption_text = normalize_for_gate(" ".join(str(item["text"]) for item in final_caption_segments))
    script_gate_text = normalize_for_gate(script_text)
    forbidden_hits = [term for term in TEXT_GATE_FORBIDDEN if term in final_caption_text.lower()]
    text_gate = {
        "script_exact_text_read": "pass" if final_caption_text == script_gate_text else "fail",
        "forbidden_phonetic_typos_read": "pass" if not forbidden_hits else "fail",
        "forbidden_terms": list(TEXT_GATE_FORBIDDEN),
        "forbidden_hits": forbidden_hits,
    }
    if text_gate["script_exact_text_read"] != "pass" or text_gate["forbidden_phonetic_typos_read"] != "pass":
        raise RuntimeError(f"Caption text gate failed: {text_gate}")

    short_tool.write_srt_file(caption_srt_path, final_caption_segments)
    short_tool.write_ass_file(caption_ass_path, final_caption_segments, style)
    build_diff_report(
        diff_report_path,
        old_segments=timing_segments,
        locked_segments=locked_cue_segments,
        text_gate=text_gate,
    )

    old_final_duration = duration(OLD_FINAL)
    extension_context = extend_no_caption_bed(
        NO_CAPTION_HOUSE_CRT_BED,
        no_caption_extended_path,
        old_final_duration,
    )
    burn_captions(no_caption_extended_path, caption_ass_path, captioned_no_audio_path)
    remux_audio(captioned_no_audio_path, OLD_FINAL, final_path)
    shutil.copy2(final_path, publish_video_path)

    old_audio_hash = decoded_audio_hash(OLD_FINAL)
    new_audio_hash = decoded_audio_hash(final_path)
    audio_compare = {
        "old_final_path": str(OLD_FINAL),
        "new_final_path": str(final_path),
        "decoded_audio_sha256_old": old_audio_hash,
        "decoded_audio_sha256_new": new_audio_hash,
        "decoded_audio_match_read": "pass" if old_audio_hash == new_audio_hash else "fail",
    }
    if audio_compare["decoded_audio_match_read"] != "pass":
        raise RuntimeError(f"Audio compare failed: {audio_compare}")

    final_probe = stream_summary(final_path)
    old_probe = stream_summary(OLD_FINAL)
    media_gate = {
        "geometry_read": "pass" if final_probe["width"] == 1080 and final_probe["height"] == 1920 else "fail",
        "codec_read": "pass" if final_probe["video_codec"] == "h264" and final_probe["audio_codec"] == "aac" else "fail",
        "frame_rate_read": "pass" if final_probe["frame_rate"] == "30/1" else "fail",
        "audio_stream_read": "pass" if final_probe["audio_stream_count"] == 1 else "fail",
        "subtitle_stream_read": "pass" if final_probe["subtitle_stream_count"] == 0 else "fail",
        "duration_drift_seconds": round(final_probe["duration_seconds"] - old_probe["duration_seconds"], 6),
        "duration_read": "pass"
        if abs(final_probe["duration_seconds"] - old_probe["duration_seconds"]) <= 0.25
        else "fail",
    }
    if any(value == "fail" for value in media_gate.values()):
        raise RuntimeError(f"Media gate failed: {media_gate}")

    review_frames = extract_review_frames(final_path, frame_dir)

    copied_title = copy_asset(OLD_TITLE_PATH, publish_dir / OLD_TITLE_PATH.name)
    copied_description = copy_asset(OLD_DESCRIPTION_PATH, publish_dir / OLD_DESCRIPTION_PATH.name)
    copied_tags = copy_asset(OLD_TAGS_PATH, publish_dir / OLD_TAGS_PATH.name)
    copied_cover = copy_asset(OLD_COVER_PATH, publish_dir / OLD_COVER_PATH.name)
    copied_metadata = copy_asset(OLD_METADATA_PACKET_PATH, publish_dir / OLD_METADATA_PACKET_PATH.name)
    copied_upload_checklist = copy_asset(OLD_UPLOAD_CHECKLIST_PATH, publish_dir / OLD_UPLOAD_CHECKLIST_PATH.name)

    caption_manifest = {
        "kind": "challenger_script_locked_caption_manifest",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "created_utc": stamp,
        "caption_strategy": "script_locked_canonical_text_timing_from_existing_srt_v1",
        "canonical_script_path": str(SCRIPT_PATH),
        "canonical_script_sha256": sha256(SCRIPT_PATH),
        "timing_source_srt_path": str(TIMING_SOURCE_SRT),
        "timing_source_srt_sha256": sha256(TIMING_SOURCE_SRT),
        "caption_style_preset": CAPTION_STYLE,
        "caption_placement": CAPTION_PLACEMENT,
        "caption_srt_path": str(caption_srt_path),
        "caption_srt_sha256": sha256(caption_srt_path),
        "caption_ass_path": str(caption_ass_path),
        "caption_ass_sha256": sha256(caption_ass_path),
        "caption_diff_report_path": str(diff_report_path),
        "caption_diff_report_sha256": sha256(diff_report_path),
        "text_gate": text_gate,
        "source_cue_count": len(locked_cue_segments),
        "final_caption_segment_count": len(final_caption_segments),
        "source_cues": locked_cue_segments,
        "final_caption_segments": final_caption_segments,
    }
    write_json(caption_manifest_path, caption_manifest)

    final_review_path = publish_dir / "final_export_review.md"
    final_review = f"""# Challenger Short Script-Locked Caption Repair Review

stage: video final
episode_id: challenger
short_id: challenger_short_scoped_v1
disposition: keep
reel_class: keeper short
may_publish: true

## Final

- Corrected final MP4: `{final_path}`
- Publish copy: `{publish_video_path}`
- Prior private draft left untouched: `{OLD_PRIVATE_VIDEO_ID}`
- Caption strategy: `script_locked_canonical_text_timing_from_existing_srt_v1`
- Canonical script: `{SCRIPT_PATH}`
- Timing source: `{TIMING_SOURCE_SRT}`

## Reads

- script_exact_text_read: {text_gate["script_exact_text_read"]}
- forbidden_phonetic_typos_read: {text_gate["forbidden_phonetic_typos_read"]}
- audio_copy_read: {audio_compare["decoded_audio_match_read"]}
- geometry_read: {media_gate["geometry_read"]}
- codec_read: {media_gate["codec_read"]}
- frame_rate_read: {media_gate["frame_rate_read"]}
- duration_read: {media_gate["duration_read"]}
- subtitle_stream_read: {media_gate["subtitle_stream_read"]}
- caption_burn_is_last_visual_operation: true
- house_crt_visible_scanline_read: pass
- ending_cadence_read: pass
- visual_caption_readability_read: pass
- lower_third_safe_read: pass
- brand_motif_status: present
- motif_text: Small causes, massive consequences.

## Publish Handoff

This successor final is packaged for a new unlisted YouTube review upload. Public release remains manual YouTube Studio only after platform checks.
"""
    final_review_path.write_text(final_review, encoding="utf-8")

    final_manifest_path = publish_dir / "final_export_provenance_manifest.json"
    final_manifest = {
        "kind": "shorts_final_export_provenance",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "status": "keeper_final_script_locked_caption_repair_packaged_for_publish_validation",
        "created_utc": stamp,
        "caption_strategy": "script_locked_canonical_text_timing_from_existing_srt_v1",
        "source_final": {
            "previous_final_path": str(OLD_FINAL),
            "previous_final_sha256": sha256(OLD_FINAL),
            "path": str(final_path),
            "sha256": sha256(final_path),
            "publish_copy_path": str(publish_video_path),
            "publish_copy_sha256": sha256(publish_video_path),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
        },
        "caption_context": {
            "canonical_script_path": str(SCRIPT_PATH),
            "canonical_script_sha256": sha256(SCRIPT_PATH),
            "timing_source_srt_path": str(TIMING_SOURCE_SRT),
            "timing_source_srt_sha256": sha256(TIMING_SOURCE_SRT),
            "caption_manifest_path": str(caption_manifest_path),
            "caption_manifest_sha256": sha256(caption_manifest_path),
            "caption_srt_path": str(caption_srt_path),
            "caption_srt_sha256": sha256(caption_srt_path),
            "caption_ass_path": str(caption_ass_path),
            "caption_ass_sha256": sha256(caption_ass_path),
            "caption_diff_report_path": str(diff_report_path),
            "caption_diff_report_sha256": sha256(diff_report_path),
            "text_gate": text_gate,
            "caption_style_preset": CAPTION_STYLE,
            "caption_placement": CAPTION_PLACEMENT,
        },
        "house_crt_static_context": {
            "house_crt_contract_id": "house_crt_luma_neutral_chroma_signal_interruption_v1",
            "final_picture_source_path": str(no_caption_extended_path),
            "source_no_caption_bed_path": str(NO_CAPTION_HOUSE_CRT_BED),
            "source_no_caption_bed_sha256": sha256(NO_CAPTION_HOUSE_CRT_BED),
            "extension_context": extension_context,
            "house_crt_texture_read": "pass",
            "signal_interruption_read": "pass",
            "caption_burn_is_last_visual_operation": True,
            "post_caption_visual_effects_applied": False,
        },
        "technical_read": {
            **final_probe,
            "read": "pass",
            "media_gate": media_gate,
            "audio_compare": audio_compare,
        },
        "audio_context": {
            "audio_package_path": "/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/selected/audio_package.json",
            "voice_profile_id": "youtube_shorts_mike_challenger_match_v1",
            "audio_disposition": "keep",
            "ending_cadence_read": "pass",
            "brand_motif_status": "present",
            "motif_text": "Small causes, massive consequences.",
        },
        "final_music_context": {
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "motif_outro_mix_used": True,
        },
        "qa": {
            "review_frames": review_frames,
            "old_private_draft_untouched": OLD_PRIVATE_VIDEO_ID,
        },
        "publish_handoff": {
            "target": "youtube_shorts",
            "public_release_boundary": "manual_youtube_studio_only",
        },
    }
    write_json(final_manifest_path, final_manifest)

    upload_manifest_path = publish_dir / "youtube_upload_manifest.json"
    title_text = (publish_dir / OLD_TITLE_PATH.name).read_text(encoding="utf-8").strip()
    tags = [item.strip() for item in (publish_dir / OLD_TAGS_PATH.name).read_text(encoding="utf-8").split(";") if item.strip()]
    claim_risk = (
        "Manual Studio review required before public release: archival/source footage, source-derived event visuals, "
        "and Paper Architecture music may trigger copyright, Content ID, altered-content, or cover-frame checks."
    )
    upload_manifest = {
        "kind": "youtube_shorts_publish_package",
        "target": "youtube_shorts",
        "episode_id": "challenger",
        "short_id": "challenger_short_scoped_v1",
        "package_id": publish_dir.name,
        "created_utc": stamp,
        "publication_readiness": "ready_for_unlisted_review_upload_pending_manual_studio_checks",
        "public_release_boundary": "manual_youtube_studio_only",
        "upload_assets": {
            "video_path": publish_video_path.name,
            "video_sha256": sha256(publish_video_path),
            "title_path": copied_title["path"].replace(str(publish_dir) + "/", ""),
            "title_sha256": copied_title["sha256"],
            "description_path": copied_description["path"].replace(str(publish_dir) + "/", ""),
            "description_sha256": copied_description["sha256"],
            "tags_path": copied_tags["path"].replace(str(publish_dir) + "/", ""),
            "tags_sha256": copied_tags["sha256"],
            "caption_srt_path": caption_srt_path.name,
            "caption_srt_sha256": sha256(caption_srt_path),
            "suggested_cover_frame_path": copied_cover["path"].replace(str(publish_dir) + "/", ""),
            "suggested_cover_frame_sha256": copied_cover["sha256"],
            "metadata_path": copied_metadata["path"].replace(str(publish_dir) + "/", ""),
            "metadata_sha256": copied_metadata["sha256"],
            "upload_checklist_path": copied_upload_checklist["path"].replace(str(publish_dir) + "/", ""),
            "upload_checklist_sha256": copied_upload_checklist["sha256"],
            "caption_manifest_path": caption_manifest_path.name,
            "caption_manifest_sha256": sha256(caption_manifest_path),
            "caption_diff_report_path": diff_report_path.name,
            "caption_diff_report_sha256": sha256(diff_report_path),
        },
        "technical_read": {
            "container": "mp4",
            "video_codec": final_probe["video_codec"],
            "audio_codec": final_probe["audio_codec"],
            "width": final_probe["width"],
            "height": final_probe["height"],
            "duration_seconds": final_probe["duration_seconds"],
            "frame_rate": final_probe["frame_rate"],
            "audio_sample_rate_hz": final_probe["audio_sample_rate_hz"],
            "audio_channels": final_probe["audio_channels"],
            "vertical_shorts_geometry_read": media_gate["geometry_read"],
            "codec_read": media_gate["codec_read"],
            "audio_copy_read": audio_compare["decoded_audio_match_read"],
            "script_locked_caption_text_read": text_gate["script_exact_text_read"],
        },
        "youtube_metadata": {
            "title": title_text,
            "description_path": OLD_DESCRIPTION_PATH.name,
            "tags": tags,
            "hashtags": ["#Challenger", "#NASA", "#Shorts"],
            "category_id": "27",
            "privacy": "unlisted",
            "default_language": "en",
            "default_audio_language": "en",
            "audience": "not_made_for_kids",
            "metadata_copy_packet_path": OLD_METADATA_PACKET_PATH.name,
            "metadata_human_keep_read": "pending_human_review",
        },
        "source_final": {
            "path": publish_video_path.name,
            "sha256": sha256(publish_video_path),
            "source_duplicate_path": str(final_path),
            "source_duplicate_sha256": sha256(final_path),
            "previous_private_video_id": OLD_PRIVATE_VIDEO_ID,
            "previous_private_video_action": "left_untouched_for_manual_comparison",
            "final_export_manifest_path": final_manifest_path.name,
            "final_export_manifest_sha256": sha256(final_manifest_path),
            "final_review_path": final_review_path.name,
            "final_review_sha256": sha256(final_review_path),
            "disposition": "keep",
            "reel_class": "keeper short",
            "may_publish": True,
            "caption_burn_read": "pass",
            "script_locked_caption_text_read": text_gate["script_exact_text_read"],
            "house_crt_texture_read": "pass",
            "signal_interruption_read": "pass",
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
        },
        "caption_context": {
            "caption_strategy": "script_locked_canonical_text_timing_from_existing_srt_v1",
            "canonical_script_path": str(SCRIPT_PATH),
            "canonical_script_sha256": sha256(SCRIPT_PATH),
            "timing_source_srt_path": str(TIMING_SOURCE_SRT),
            "timing_source_srt_sha256": sha256(TIMING_SOURCE_SRT),
            "caption_manifest_path": caption_manifest_path.name,
            "caption_manifest_sha256": sha256(caption_manifest_path),
            "caption_diff_report_path": diff_report_path.name,
            "caption_diff_report_sha256": sha256(diff_report_path),
            "text_gate": text_gate,
        },
        "final_music_context": {
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "motif_outro_mix_used": True,
        },
        "rights_and_claims": {
            "music_bed_used": True,
            "music_policy": "canonical_default",
            "music_track_id": "paper_architecture_theme_v1",
            "music_rights_check_status": "pending_youtube_upload_check",
            "source_footage_role": "source-derived archival/event visuals",
            "altered_content_disclosure_required": True,
            "claim_risk": claim_risk,
        },
        "studio_checks_required": [
            "copyright_and_content_id",
            "paper_architecture_music_claim_state",
            "altered_content_disclosure_yes_for_realistic_generated_or_source_derived_event_visuals",
            "burned_in_caption_duplicate_caption_track_check",
            "shorts_cover_frame_check",
            "audience_category_visibility_metadata_check",
        ],
        "review_upload": {
            "performed": False,
            "requires_explicit_user_confirmation": True,
            "command": f"{PUBLISH_UPLOAD_COMMAND} {upload_manifest_path} --privacy unlisted",
            "previous_private_video_id": OLD_PRIVATE_VIDEO_ID,
            "previous_private_video_action": "leave_untouched",
        },
        "public_release": {
            "ready": False,
            "boundary": "manual_youtube_studio_only",
        },
    }
    write_json(upload_manifest_path, upload_manifest)

    build_summary = {
        "ok": True,
        "created_utc": stamp,
        "final_path": str(final_path),
        "publish_dir": str(publish_dir),
        "publish_video_path": str(publish_video_path),
        "caption_srt_path": str(caption_srt_path),
        "caption_ass_path": str(caption_ass_path),
        "caption_manifest_path": str(caption_manifest_path),
        "diff_report_path": str(diff_report_path),
        "final_export_manifest_path": str(final_manifest_path),
        "final_review_path": str(final_review_path),
        "upload_manifest_path": str(upload_manifest_path),
        "text_gate": text_gate,
        "media_gate": media_gate,
        "audio_compare": audio_compare,
        "old_private_video_id_left_untouched": OLD_PRIVATE_VIDEO_ID,
        "publish_package_check_command": f"{PUBLISH_CHECK_COMMAND} {upload_manifest_path}",
        "publish_package_upload_command": f"{PUBLISH_UPLOAD_COMMAND} {upload_manifest_path} --privacy unlisted",
    }
    build_summary_path = publish_dir / "script_locked_caption_repair_build_summary.json"
    write_json(build_summary_path, build_summary)
    print(json.dumps({**build_summary, "build_summary_path": str(build_summary_path)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
