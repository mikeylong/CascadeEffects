#!/usr/bin/env python3
"""Prepare and trim warm-up-prefixed TTS jobs."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PREROLL_MS = 120
DEFAULT_TRANSCRIBE_MODEL = "small"
FUZZY_MATCH_MIN_RATIO = 0.82
FUZZY_MATCH_MARGIN = 0.03


@dataclass
class Segment:
    start_s: float
    end_s: float
    text: str


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _read_jobs_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        _die(f"Manifest not found: {path}")

    jobs: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            _die(f"Invalid JSON on line {line_no} of {path}: {exc}")
        if not isinstance(item, dict):
            _die(f"Invalid job on line {line_no} of {path}: expected object")
        jobs.append(item)

    return jobs


def _write_jobs_jsonl(path: Path, jobs: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for job in jobs:
            handle.write(json.dumps(job, ensure_ascii=False) + "\n")


def _job_input(job: dict[str, Any]) -> str:
    value = job.get("input")
    if not isinstance(value, str) or not value.strip():
        _die("Job missing visible input text.")
    return value.strip()


def _warmup_prefix(job: dict[str, Any]) -> str | None:
    value = job.get("warmup_prefix")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _default_anchor_text(text: str) -> str:
    first_paragraph = text.split("\n\n", 1)[0].strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", first_paragraph, maxsplit=1)[0].strip()
    if first_sentence and len(first_sentence.split()) <= 18:
        return first_sentence
    return " ".join(first_paragraph.split()[:12]).strip()


def _anchor_text(job: dict[str, Any]) -> str:
    explicit = job.get("warmup_anchor_text")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return _default_anchor_text(_job_input(job))


def _normalize_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _build_effective_input(job: dict[str, Any]) -> str:
    prefix = _warmup_prefix(job)
    text = _job_input(job)
    if not prefix:
        return text
    return f"{prefix}\n\n{text}"


def _build_effective_elevenlabs_text(job: dict[str, Any]) -> str | None:
    prefix = _warmup_prefix(job)
    rendered = job.get("elevenlabs_text")
    if not isinstance(rendered, str) or not rendered.strip():
        return None
    if not prefix:
        return rendered.strip()
    return f"{prefix}\n\n{rendered.strip()}"


def _parse_srt_timestamp(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(millis) / 1000.0
    )


def _parse_srt(path: Path) -> list[Segment]:
    text = path.read_text(encoding="utf-8")
    segments: list[Segment] = []
    for block in re.split(r"\n\s*\n", text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        if "-->" not in lines[1]:
            continue
        start_text, end_text = [part.strip() for part in lines[1].split("-->", 1)]
        segments.append(
            Segment(
                start_s=_parse_srt_timestamp(start_text),
                end_s=_parse_srt_timestamp(end_text),
                text=" ".join(lines[2:]),
            )
        )
    if not segments:
        _die(f"No transcript segments found in {path}")
    return segments


def _find_anchor_start(segments: list[Segment], anchor_text: str) -> tuple[float, str, float]:
    anchor_tokens = _normalize_words(anchor_text)
    if not anchor_tokens:
        _die("Anchor text normalized to nothing.")

    transcript_tokens: list[str] = []
    token_times: list[float] = []
    for segment in segments:
        tokens = _normalize_words(segment.text)
        transcript_tokens.extend(tokens)
        token_times.extend([segment.start_s] * len(tokens))

    matches: list[int] = []
    window = len(anchor_tokens)
    for idx in range(0, len(transcript_tokens) - window + 1):
        if transcript_tokens[idx : idx + window] == anchor_tokens:
            matches.append(idx)

    if matches:
        if len(matches) > 1:
            _die(f"Anchor text matched multiple times and is ambiguous: {anchor_text!r}")
        return token_times[matches[0]], "exact", 1.0

    best: tuple[float, int] | None = None
    second_best: tuple[float, int] | None = None
    min_window = max(1, window - 2)
    max_window = min(len(transcript_tokens), window + 2)
    for candidate_window in range(min_window, max_window + 1):
        for idx in range(0, len(transcript_tokens) - candidate_window + 1):
            candidate_tokens = transcript_tokens[idx : idx + candidate_window]
            ratio = difflib.SequenceMatcher(None, anchor_tokens, candidate_tokens).ratio()
            candidate = (ratio, idx)
            if best is None or candidate > best:
                second_best = best
                best = candidate
            elif second_best is None or candidate > second_best:
                second_best = candidate

    if best is None or best[0] < FUZZY_MATCH_MIN_RATIO:
        _die(f"Could not align anchor text: {anchor_text!r}")

    if (
        second_best is not None
        and second_best[1] != best[1]
        and (best[0] - second_best[0]) < FUZZY_MATCH_MARGIN
    ):
        _die(f"Anchor text matched multiple times and is ambiguous: {anchor_text!r}")

    return token_times[best[1]], "fuzzy", best[0]


def _codec_args_for(audio_path: Path) -> list[str]:
    suffix = audio_path.suffix.lower()
    if suffix == ".mp3":
        return ["-c:a", "libmp3lame", "-b:a", "192k"]
    if suffix == ".wav":
        return ["-c:a", "pcm_s16le"]
    if suffix == ".flac":
        return ["-c:a", "flac"]
    _die(f"Unsupported warm-up trim format: {audio_path.suffix}")
    return []


def _run_prepare_manifest(args: argparse.Namespace) -> int:
    jobs = _read_jobs_jsonl(Path(args.manifest))
    prepared: list[dict[str, Any]] = []
    for job in jobs:
        updated = dict(job)
        effective_elevenlabs = _build_effective_elevenlabs_text(job)
        if effective_elevenlabs is not None:
            updated["elevenlabs_text"] = effective_elevenlabs
        else:
            updated["input"] = _build_effective_input(job)
        prepared.append(updated)
    _write_jobs_jsonl(Path(args.output), prepared)
    print(f"Wrote {args.output}")
    return 0


def _find_srt_file(transcript_dir: Path, stem: str) -> Path:
    preferred = transcript_dir / f"{stem}.diarized.srt"
    if preferred.exists():
        return preferred
    candidates = sorted(transcript_dir.glob(f"{stem}*.srt"))
    if not candidates:
        _die(f"No SRT transcript found in {transcript_dir} for {stem}")
    return candidates[0]


def _run_transcribe(audio_path: Path, transcript_dir: Path, model: str, log_path: Path) -> None:
    transcript_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "transcribe",
        "-m",
        model,
        "-o",
        str(transcript_dir),
        "--force",
        str(audio_path),
    ]
    with log_path.open("w", encoding="utf-8") as handle:
        result = subprocess.run(
            cmd,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        _die(f"transcribe failed for {audio_path}; see {log_path}")


def _trim_audio(audio_path: Path, trim_start_s: float, temp_path: Path, log_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-ss",
        f"{trim_start_s:.3f}",
        "-vn",
        *_codec_args_for(audio_path),
        str(temp_path),
    ]
    with log_path.open("w", encoding="utf-8") as handle:
        result = subprocess.run(
            cmd,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        _die(f"ffmpeg trim failed for {audio_path}; see {log_path}")


def _run_trim_rendered(args: argparse.Namespace) -> int:
    manifest = Path(args.manifest)
    render_dir = Path(args.render_dir)
    work_dir = Path(args.work_dir)
    jobs = _read_jobs_jsonl(manifest)

    warmup_jobs = [job for job in jobs if _warmup_prefix(job)]
    if not warmup_jobs:
        print(f"No warm-up jobs found in {manifest}")
        return 0

    for job in warmup_jobs:
        out_name = job.get("out")
        if not isinstance(out_name, str) or not out_name.strip():
            _die("Warm-up job is missing an output filename.")

        audio_path = render_dir / out_name
        if not audio_path.exists():
            _die(f"Rendered file not found for warm-up trim: {audio_path}")

        job_dir = work_dir / audio_path.stem
        transcript_dir = job_dir / "transcripts"
        transcribe_log = job_dir / "transcribe.log"
        trim_log = job_dir / "trim_ffmpeg.log"
        report_path = job_dir / "trim_report.json"
        temp_trim_path = job_dir / f"{audio_path.stem}.trimmed{audio_path.suffix}"

        _run_transcribe(audio_path, transcript_dir, args.transcribe_model, transcribe_log)
        srt_path = _find_srt_file(transcript_dir, audio_path.stem)
        segments = _parse_srt(srt_path)

        anchor_text = _anchor_text(job)
        anchor_start_s, anchor_match_mode, anchor_match_ratio = _find_anchor_start(segments, anchor_text)
        if anchor_start_s < 0.3:
            _die(
                f"Anchor for {audio_path.name} matched too close to the start ({anchor_start_s:.3f}s); refusing to trim."
            )

        preroll_ms = int(job.get("warmup_preroll_ms", DEFAULT_PREROLL_MS))
        trim_start_s = max(0.0, anchor_start_s - (preroll_ms / 1000.0))

        _trim_audio(audio_path, trim_start_s, temp_trim_path, trim_log)
        temp_trim_path.replace(audio_path)

        report = {
            "audio_path": str(audio_path),
            "anchor_text": anchor_text,
            "anchor_match_mode": anchor_match_mode,
            "anchor_match_ratio": round(anchor_match_ratio, 3),
            "anchor_start_s": round(anchor_start_s, 3),
            "trim_start_s": round(trim_start_s, 3),
            "preroll_ms": preroll_ms,
            "transcript_srt": str(srt_path),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Trimmed {audio_path} at {trim_start_s:.3f}s")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and trim warm-up-prefixed TTS jobs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-manifest", help="Create an effective manifest with warm-up prefixes prepended.")
    prepare.add_argument("--manifest", required=True, help="Original JSONL manifest path.")
    prepare.add_argument("--output", required=True, help="Output JSONL manifest path.")
    prepare.set_defaults(func=_run_prepare_manifest)

    trim = subparsers.add_parser("trim-rendered", help="Trim rendered outputs back to the visible script start.")
    trim.add_argument("--manifest", required=True, help="Original JSONL manifest path.")
    trim.add_argument("--render-dir", required=True, help="Directory containing rendered audio files.")
    trim.add_argument("--work-dir", required=True, help="Directory for transcripts, logs, and trim reports.")
    trim.add_argument(
        "--transcribe-model",
        default=DEFAULT_TRANSCRIBE_MODEL,
        help=f"Local transcribe model to use (default: {DEFAULT_TRANSCRIBE_MODEL}).",
    )
    trim.set_defaults(func=_run_trim_rendered)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
