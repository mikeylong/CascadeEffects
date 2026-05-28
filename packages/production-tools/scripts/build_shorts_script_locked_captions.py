#!/usr/bin/env python3
"""Build script-locked caption artifacts for YouTube Shorts.

WhisperX, ASR, SRT, and VTT files are timing evidence only. The emitted words
must come from the locked short script or an already script-locked caption file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_living_cover_script_locked_captions import (
    CaptionAlignmentError,
    build_script_locked_caption_package,
)


SCRIPT_LOCKED_CAPTION_MODEL = "script_locked_canonical_text_timing_from_asr_v1"
SCRIPT_LOCKED_TEXT_POLICY = "script_locked_canonical_text_only"
ASR_TIMING_POLICY = "asr_whisperx_timing_only"
BLOCKED_WORD_SOURCE_MARKERS = (
    ".diarized",
    "whisperx",
    "raw_asr",
    "asr_transcript",
    "transcripts_mastered",
    "transcripts_final",
)


class ShortsCaptionPolicyError(RuntimeError):
    pass


def looks_like_raw_asr_word_source(path: Path) -> bool:
    token = str(path).lower()
    if "script_locked" in token or "locked_script" in token or "canonical_script" in token:
        return False
    return any(marker in token for marker in BLOCKED_WORD_SOURCE_MARKERS)


def assert_allowed_caption_text_source(path: Path) -> None:
    if looks_like_raw_asr_word_source(path):
        raise ShortsCaptionPolicyError(
            f"{path}: ASR/WhisperX/diarized transcript files are timing evidence only; "
            "caption_text_source_path must be a locked script or script-locked caption output."
        )


def _artifact(path: Path) -> dict[str, Any]:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "sha256": digest.hexdigest()}


def build_shorts_script_locked_caption_package(
    *,
    caption_text_source_path: Path,
    caption_timing_source_path: Path,
    output_dir: Path,
    basename: str,
    voice_offset_seconds: float,
    outro_cutoff_seconds: float | None = None,
    story_cutoff_seconds: float | None = None,
    max_chars_per_cue: int = 42,
    max_words_per_cue: int = 7,
    min_alignment_coverage: float = 0.985,
    max_unmatched_script_span: int = 8,
) -> dict[str, Any]:
    caption_text_source_path = caption_text_source_path.expanduser().resolve()
    caption_timing_source_path = caption_timing_source_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    assert_allowed_caption_text_source(caption_text_source_path)

    qa = build_script_locked_caption_package(
        script_path=caption_text_source_path,
        timing_path=caption_timing_source_path,
        output_dir=output_dir,
        basename=basename,
        voice_offset_seconds=voice_offset_seconds,
        outro_cutoff_seconds=outro_cutoff_seconds,
        story_cutoff_seconds=story_cutoff_seconds,
        max_chars_per_cue=max_chars_per_cue,
        max_words_per_cue=max_words_per_cue,
        min_alignment_coverage=min_alignment_coverage,
        max_unmatched_script_span=max_unmatched_script_span,
    )
    policy_fields = {
        "caption_model": SCRIPT_LOCKED_CAPTION_MODEL,
        "caption_text_source_policy": SCRIPT_LOCKED_TEXT_POLICY,
        "caption_timing_source_policy": ASR_TIMING_POLICY,
        "caption_text_source_path": str(caption_text_source_path),
        "caption_text_source_sha256": _artifact(caption_text_source_path)["sha256"],
        "caption_timing_source_path": str(caption_timing_source_path),
        "caption_timing_source_sha256": _artifact(caption_timing_source_path)["sha256"],
        "caption_text_matches_script_read": qa["reads"]["caption_text_matches_script_read"],
        "caption_alignment_coverage_read": qa["reads"]["caption_alignment_coverage_read"],
        "caption_asr_text_not_used_read": qa["reads"]["caption_asr_text_not_used_read"],
        "publish_ready_blocked_if_caption_text_not_script_locked": True,
    }
    qa.update(policy_fields)
    qa["caption_text_source"] = _artifact(caption_text_source_path)
    qa["caption_timing_source"] = _artifact(caption_timing_source_path)
    qa_path = Path(str(qa["outputs"]["qa_json"]["path"]))
    qa_path.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    qa["outputs"]["qa_json"] = _artifact(qa_path)
    return qa


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caption-text-source-path", required=True, type=Path)
    parser.add_argument("--caption-timing-source-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--basename", required=True)
    parser.add_argument("--voice-offset-seconds", type=float, default=0.0)
    parser.add_argument("--outro-cutoff-seconds", type=float)
    parser.add_argument("--story-cutoff-seconds", type=float)
    parser.add_argument("--max-chars-per-cue", type=int, default=42)
    parser.add_argument("--max-words-per-cue", type=int, default=7)
    parser.add_argument("--min-alignment-coverage", type=float, default=0.985)
    parser.add_argument("--max-unmatched-script-span", type=int, default=8)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        qa = build_shorts_script_locked_caption_package(
            caption_text_source_path=args.caption_text_source_path,
            caption_timing_source_path=args.caption_timing_source_path,
            output_dir=args.output_dir,
            basename=args.basename,
            voice_offset_seconds=args.voice_offset_seconds,
            outro_cutoff_seconds=args.outro_cutoff_seconds,
            story_cutoff_seconds=args.story_cutoff_seconds,
            max_chars_per_cue=args.max_chars_per_cue,
            max_words_per_cue=args.max_words_per_cue,
            min_alignment_coverage=args.min_alignment_coverage,
            max_unmatched_script_span=args.max_unmatched_script_span,
        )
    except (CaptionAlignmentError, ShortsCaptionPolicyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if isinstance(exc, CaptionAlignmentError):
            print(json.dumps(exc.report, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"status": qa["status"], "reads": qa["reads"], "outputs": qa["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
