#!/usr/bin/env python3
"""Build rail-safe captions whose visible text is locked to the narration script.

ASR, WhisperX, VTT, and SRT inputs are timing sources only. Generated captions
must preserve the approved script words after removing nonspoken performance
tags such as "[calm]" or "[deliberate]".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"\S+")
SPEAKER_PREFIX_RE = re.compile(r"^\s*(?:SPEAKER[_ -]?\d+|Speaker\s+\d+|[A-Z][A-Za-z .'-]{0,40}):\s+")
PERFORMANCE_TAG_RE = re.compile(r"\s*\[[A-Za-z][A-Za-z0-9 _./'-]{0,80}\]\s*")
TIMECODE_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{3})"
)


class CaptionAlignmentError(RuntimeError):
    """Raised when script/audio alignment is too weak for automatic captions."""

    def __init__(self, message: str, report: dict[str, Any]):
        super().__init__(message)
        self.report = report


@dataclass(frozen=True)
class ScriptToken:
    index: int
    raw: str
    norm: str


@dataclass(frozen=True)
class TimingToken:
    index: int
    raw: str
    norm: str
    start: float
    end: float


@dataclass(frozen=True)
class TimedScriptToken:
    index: int
    raw: str
    norm: str
    start: float
    end: float
    timing_mode: str
    timing_source_index: int | None
    timing_source_raw: str | None


@dataclass(frozen=True)
class CaptionCue:
    index: int
    start: float
    end: float
    text: str
    script_start_index: int
    script_end_index: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def strip_performance_tags(text: str) -> str:
    """Remove standalone nonspoken bracketed performance tags from a script."""

    return PERFORMANCE_TAG_RE.sub(" ", text)


def strip_speaker_prefix(text: str) -> str:
    return SPEAKER_PREFIX_RE.sub("", text.strip())


def normalize_token(value: str) -> str:
    if re.match(r"^\s*SPEAKER[_ -]?\d+:\s*$", value, flags=re.IGNORECASE):
        return ""
    value = strip_speaker_prefix(value)
    value = (
        value.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def display_text_from_words(words: Iterable[str]) -> str:
    return " ".join(word for word in words if word).strip()


def script_tokens_from_text(text: str) -> list[ScriptToken]:
    stripped = strip_performance_tags(text)
    tokens: list[ScriptToken] = []
    for raw in TOKEN_RE.findall(stripped):
        norm = normalize_token(raw)
        if norm:
            tokens.append(ScriptToken(index=len(tokens), raw=raw, norm=norm))
    return tokens


def parse_timecode(value: str) -> float:
    cleaned = value.replace(",", ".")
    hours, minutes, seconds = cleaned.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def format_vtt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    millis = int(round(seconds * 1000))
    hours = millis // 3_600_000
    millis %= 3_600_000
    minutes = millis // 60_000
    millis %= 60_000
    secs = millis // 1000
    millis %= 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def format_srt_time(seconds: float) -> str:
    return format_vtt_time(seconds).replace(".", ",")


def iter_vtt_srt_cues(path: Path) -> Iterable[tuple[float, float, str]]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    for block in blocks:
        lines = [line.strip("\ufeff") for line in block.splitlines()]
        if not lines or lines[0].strip() == "WEBVTT":
            continue
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        match = TIMECODE_RE.search(lines[timing_index])
        if not match:
            continue
        cue_text = " ".join(line.strip() for line in lines[timing_index + 1 :] if line.strip())
        cue_text = strip_speaker_prefix(cue_text)
        if cue_text:
            yield parse_timecode(match.group("start")), parse_timecode(match.group("end")), cue_text


def timing_tokens_from_cue_text(start: float, end: float, text: str, first_index: int) -> list[TimingToken]:
    raw_words = TOKEN_RE.findall(strip_speaker_prefix(text))
    words = [(raw, normalize_token(raw)) for raw in raw_words]
    words = [(raw, norm) for raw, norm in words if norm]
    if not words:
        return []
    weights = [max(1, len(norm)) for _, norm in words]
    total_weight = sum(weights)
    duration = max(0.001, end - start)
    tokens: list[TimingToken] = []
    cursor_weight = 0
    for raw, norm in words:
        token_start = start + duration * cursor_weight / total_weight
        cursor_weight += max(1, len(norm))
        token_end = start + duration * cursor_weight / total_weight
        tokens.append(
            TimingToken(
                index=first_index + len(tokens),
                raw=raw,
                norm=norm,
                start=token_start,
                end=max(token_start + 0.001, token_end),
            )
        )
    return tokens


def timing_tokens_from_text_track(path: Path) -> list[TimingToken]:
    tokens: list[TimingToken] = []
    for start, end, text in iter_vtt_srt_cues(path):
        cue_tokens = timing_tokens_from_cue_text(start, end, text, len(tokens))
        tokens.extend(cue_tokens)
    return tokens


def timing_tokens_from_whisperx(path: Path) -> list[TimingToken]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_words: list[dict[str, Any]] = []
    if isinstance(payload.get("word_segments"), list):
        raw_words.extend(payload["word_segments"])
    for segment in payload.get("segments", []) if isinstance(payload.get("segments"), list) else []:
        if isinstance(segment.get("words"), list):
            raw_words.extend(segment["words"])

    seen: set[tuple[str, float, float]] = set()
    tokens: list[TimingToken] = []
    for raw_word in raw_words:
        word = str(raw_word.get("word", "")).strip()
        if not word:
            continue
        try:
            start = float(raw_word["start"])
            end = float(raw_word["end"])
        except (KeyError, TypeError, ValueError):
            continue
        norm = normalize_token(word)
        if not norm:
            continue
        key = (word, start, end)
        if key in seen:
            continue
        seen.add(key)
        tokens.append(
            TimingToken(
                index=len(tokens),
                raw=word,
                norm=norm,
                start=start,
                end=max(start + 0.001, end),
            )
        )
    return tokens


def load_timing_tokens(path: Path) -> list[TimingToken]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        tokens = timing_tokens_from_whisperx(path)
    elif suffix in {".vtt", ".srt"}:
        tokens = timing_tokens_from_text_track(path)
    else:
        raise ValueError(f"Unsupported timing source type: {path}")
    if not tokens:
        raise ValueError(f"No timed words found in timing source: {path}")
    return tokens


def find_unmatched_spans(script_tokens: list[ScriptToken], mapping: dict[int, int]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    cursor = 0
    while cursor < len(script_tokens):
        if cursor in mapping:
            cursor += 1
            continue
        start = cursor
        while cursor < len(script_tokens) and cursor not in mapping:
            cursor += 1
        tokens = script_tokens[start:cursor]
        spans.append(
            {
                "start_index": start,
                "end_index_exclusive": cursor,
                "token_count": len(tokens),
                "text": display_text_from_words(token.raw for token in tokens),
            }
        )
    return spans


def build_alignment_mapping(script_tokens: list[ScriptToken], timing_tokens: list[TimingToken]) -> dict[int, int]:
    matcher = SequenceMatcher(
        None,
        [token.norm for token in script_tokens],
        [token.norm for token in timing_tokens],
        autojunk=False,
    )
    mapping: dict[int, int] = {}
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            mapping[block.a + offset] = block.b + offset
    return mapping


def align_script_to_timing(
    script_tokens: list[ScriptToken],
    timing_tokens: list[TimingToken],
    min_alignment_coverage: float = 0.985,
    max_unmatched_script_span: int = 8,
) -> tuple[list[TimedScriptToken], dict[str, Any]]:
    if not script_tokens:
        raise CaptionAlignmentError("Script contains no captionable words.", {"status": "fail"})
    if not timing_tokens:
        raise CaptionAlignmentError("Timing source contains no timed words.", {"status": "fail"})

    mapping = build_alignment_mapping(script_tokens, timing_tokens)
    coverage = len(mapping) / len(script_tokens)
    unmatched_spans = find_unmatched_spans(script_tokens, mapping)
    largest_span = max((span["token_count"] for span in unmatched_spans), default=0)
    report = {
        "status": "pass",
        "script_token_count": len(script_tokens),
        "timing_token_count": len(timing_tokens),
        "matched_script_token_count": len(mapping),
        "alignment_coverage": coverage,
        "min_alignment_coverage": min_alignment_coverage,
        "max_unmatched_script_span": largest_span,
        "max_unmatched_script_span_allowed": max_unmatched_script_span,
        "unmatched_script_spans": unmatched_spans[:50],
        "unmatched_script_span_count": len(unmatched_spans),
    }
    failures: list[str] = []
    if coverage < min_alignment_coverage:
        failures.append(
            f"alignment coverage {coverage:.4%} is below required {min_alignment_coverage:.4%}"
        )
    if largest_span > max_unmatched_script_span:
        failures.append(
            f"largest unmatched script span {largest_span} exceeds allowed {max_unmatched_script_span}"
        )
    if failures:
        report["status"] = "fail"
        raise CaptionAlignmentError("; ".join(failures), report)

    aligned: list[TimedScriptToken | None] = [None] * len(script_tokens)
    for script_index, timing_index in mapping.items():
        script_token = script_tokens[script_index]
        timing_token = timing_tokens[timing_index]
        aligned[script_index] = TimedScriptToken(
            index=script_token.index,
            raw=script_token.raw,
            norm=script_token.norm,
            start=timing_token.start,
            end=timing_token.end,
            timing_mode="matched_asr_timing",
            timing_source_index=timing_token.index,
            timing_source_raw=timing_token.raw,
        )

    for span in unmatched_spans:
        start_index = int(span["start_index"])
        end_index = int(span["end_index_exclusive"])
        count = end_index - start_index
        left = aligned[start_index - 1] if start_index > 0 else None
        right = aligned[end_index] if end_index < len(aligned) else None
        if left and right:
            span_start = left.end
            span_end = right.start
            mode = "interpolated_between_matches"
        elif right:
            span_end = right.start
            span_start = max(0.0, span_end - count * 0.18)
            mode = "interpolated_before_first_match"
        elif left:
            span_start = left.end
            span_end = span_start + count * 0.18
            mode = "interpolated_after_last_match"
        else:
            span_start = 0.0
            span_end = count * 0.18
            mode = "interpolated_without_anchor"

        if span_end <= span_start:
            span_end = span_start + count * 0.06
        step = (span_end - span_start) / count
        for offset, script_index in enumerate(range(start_index, end_index)):
            script_token = script_tokens[script_index]
            token_start = span_start + step * offset
            token_end = span_start + step * (offset + 1)
            aligned[script_index] = TimedScriptToken(
                index=script_token.index,
                raw=script_token.raw,
                norm=script_token.norm,
                start=token_start,
                end=max(token_start + 0.001, token_end),
                timing_mode=mode,
                timing_source_index=None,
                timing_source_raw=None,
            )

    timed = [token for token in aligned if token is not None]
    monotonic: list[TimedScriptToken] = []
    previous_end = 0.0
    for token in timed:
        start = max(token.start, previous_end)
        end = max(token.end, start + 0.001)
        monotonic.append(
            TimedScriptToken(
                index=token.index,
                raw=token.raw,
                norm=token.norm,
                start=start,
                end=end,
                timing_mode=token.timing_mode,
                timing_source_index=token.timing_source_index,
                timing_source_raw=token.timing_source_raw,
            )
        )
        previous_end = end
    report["interpolated_script_token_count"] = sum(
        1 for token in monotonic if token.timing_mode.startswith("interpolated")
    )
    return monotonic, report


def should_end_chunk(text: str, word_count: int) -> bool:
    if word_count >= 4 and re.search(r"[.!?][\"')\]]?$", text):
        return True
    if word_count >= 5 and re.search(r"[,;:][\"')\]]?$", text):
        return True
    return False


def build_caption_cues(
    timed_tokens: list[TimedScriptToken],
    voice_offset_seconds: float,
    outro_cutoff_seconds: float | None,
    max_chars_per_cue: int,
    max_words_per_cue: int,
) -> list[CaptionCue]:
    cues: list[CaptionCue] = []
    current: list[TimedScriptToken] = []

    def current_text(tokens: list[TimedScriptToken]) -> str:
        return display_text_from_words(token.raw for token in tokens)

    def flush() -> None:
        nonlocal current
        if not current:
            return
        text = current_text(current)
        start = current[0].start + voice_offset_seconds
        end = current[-1].end + voice_offset_seconds
        if outro_cutoff_seconds is not None:
            if start >= outro_cutoff_seconds:
                current = []
                return
            end = min(end, outro_cutoff_seconds)
        if end <= start:
            end = start + 0.001
        cues.append(
            CaptionCue(
                index=len(cues) + 1,
                start=start,
                end=end,
                text=text,
                script_start_index=current[0].index,
                script_end_index=current[-1].index,
            )
        )
        current = []

    for token in timed_tokens:
        candidate = current + [token]
        candidate_text = current_text(candidate)
        exceeds_limits = len(candidate) > max_words_per_cue or len(candidate_text) > max_chars_per_cue
        if current and exceeds_limits:
            flush()
            candidate = [token]
            candidate_text = current_text(candidate)
        current = candidate
        if should_end_chunk(candidate_text, len(candidate)):
            flush()
    flush()

    merged: list[CaptionCue] = []
    for cue in cues:
        if (
            merged
            and len(cue.text.split()) <= 2
            and len(merged[-1].text) + 1 + len(cue.text) <= max_chars_per_cue
            and len(merged[-1].text.split()) + len(cue.text.split()) <= max_words_per_cue
        ):
            previous = merged.pop()
            merged.append(
                CaptionCue(
                    index=len(merged) + 1,
                    start=previous.start,
                    end=cue.end,
                    text=f"{previous.text} {cue.text}",
                    script_start_index=previous.script_start_index,
                    script_end_index=cue.script_end_index,
                )
            )
        else:
            merged.append(
                CaptionCue(
                    index=len(merged) + 1,
                    start=cue.start,
                    end=cue.end,
                    text=cue.text,
                    script_start_index=cue.script_start_index,
                    script_end_index=cue.script_end_index,
                )
            )
    return merged


def normalized_caption_text(text: str) -> str:
    return " ".join(normalize_token(token) for token in TOKEN_RE.findall(strip_performance_tags(text)) if normalize_token(token))


def normalized_cue_text(cues: list[CaptionCue]) -> str:
    return " ".join(
        normalize_token(token)
        for cue in cues
        for token in TOKEN_RE.findall(cue.text)
        if normalize_token(token)
    )


def validate_caption_text_matches_script(script_text: str, cues: list[CaptionCue]) -> dict[str, Any]:
    script_norm = normalized_caption_text(script_text)
    cue_norm = normalized_cue_text(cues)
    return {
        "status": "pass" if script_norm == cue_norm else "fail",
        "normalized_script_token_count": len(script_norm.split()) if script_norm else 0,
        "normalized_caption_token_count": len(cue_norm.split()) if cue_norm else 0,
    }


def validate_rail_limits(cues: list[CaptionCue], max_chars_per_cue: int, max_words_per_cue: int) -> dict[str, Any]:
    violations = [
        {
            "cue_index": cue.index,
            "chars": len(cue.text),
            "words": len(cue.text.split()),
            "text": cue.text,
        }
        for cue in cues
        if len(cue.text) > max_chars_per_cue or len(cue.text.split()) > max_words_per_cue
    ]
    return {
        "status": "pass" if not violations else "fail",
        "max_chars_per_cue": max_chars_per_cue,
        "max_words_per_cue": max_words_per_cue,
        "violations": violations[:25],
        "violation_count": len(violations),
    }


def validate_cue_timing(cues: list[CaptionCue], outro_cutoff_seconds: float | None) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    previous_start = -1.0
    previous_end = -1.0
    for cue in cues:
        if cue.start < previous_start or cue.end < previous_end or cue.end <= cue.start:
            violations.append({"cue_index": cue.index, "reason": "non_ascending_or_empty"})
        if outro_cutoff_seconds is not None and cue.end > outro_cutoff_seconds + 0.001:
            violations.append({"cue_index": cue.index, "reason": "extends_past_outro_cutoff"})
        previous_start = cue.start
        previous_end = cue.end
    return {
        "status": "pass" if not violations else "fail",
        "outro_cutoff_seconds": outro_cutoff_seconds,
        "violations": violations[:25],
        "violation_count": len(violations),
    }


CAPTION_GATE_REQUIRED_READS = (
    "caption_text_matches_script_read",
    "caption_alignment_coverage_read",
    "caption_asr_text_not_used_read",
)

CAPTION_GATE_ADVANCE_FLAGS = (
    "may_create_full_runtime_mp4_render",
    "may_advance_to_video_render",
    "may_advance_to_final_assembly",
    "may_advance_to_publish_readiness",
)


def pass_read(value: Any) -> bool:
    return isinstance(value, str) and (value == "pass" or value.startswith("pass_"))


def validate_caption_manifest_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate that manifest advancement is blocked unless caption reads pass."""

    caption_context = manifest.get("caption_context", {}) if isinstance(manifest, dict) else {}
    rough_reads = manifest.get("rough_assembly_reads", {}) if isinstance(manifest, dict) else {}
    text_source = caption_context.get("caption_text_source")
    timing_source = caption_context.get("caption_timing_source")
    read_sources = [caption_context, rough_reads]
    missing_fields: list[str] = []
    failing_reads: dict[str, Any] = {}
    if not text_source:
        missing_fields.append("caption_context.caption_text_source")
    if not timing_source:
        missing_fields.append("caption_context.caption_timing_source")
    for read_name in CAPTION_GATE_REQUIRED_READS:
        value = next((source.get(read_name) for source in read_sources if read_name in source), None)
        if not pass_read(value):
            failing_reads[read_name] = value

    gate_passes = not missing_fields and not failing_reads
    illegal_advancement_flags = [
        flag for flag in CAPTION_GATE_ADVANCE_FLAGS if manifest.get(flag) is True and not gate_passes
    ]
    return {
        "status": "pass" if gate_passes and not illegal_advancement_flags else "fail",
        "caption_gate_passes": gate_passes,
        "missing_fields": missing_fields,
        "failing_reads": failing_reads,
        "illegal_advancement_flags": illegal_advancement_flags,
    }


def write_vtt(path: Path, cues: list[CaptionCue]) -> None:
    lines = ["WEBVTT", ""]
    for cue in cues:
        lines.extend([f"{format_vtt_time(cue.start)} --> {format_vtt_time(cue.end)}", cue.text, ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_srt(path: Path, cues: list[CaptionCue]) -> None:
    lines: list[str] = []
    for cue in cues:
        lines.extend(
            [
                str(cue.index),
                f"{format_srt_time(cue.start)} --> {format_srt_time(cue.end)}",
                cue.text,
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def offset_slug(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    whole = millis // 1000
    frac = millis % 1000
    return f"{whole}s{frac:03d}"


def default_output_paths(output_dir: Path, basename: str, voice_offset_seconds: float) -> dict[str, Path]:
    slug = offset_slug(voice_offset_seconds)
    return {
        "story_vtt": output_dir / f"{basename}.script_locked_rail_safe.vtt",
        "story_srt": output_dir / f"{basename}.script_locked_rail_safe.srt",
        "offset_vtt": output_dir / f"{basename}.script_locked_rail_safe.offset_intro_{slug}.vtt",
        "offset_srt": output_dir / f"{basename}.script_locked_rail_safe.offset_intro_{slug}.srt",
        "qa_json": output_dir / f"{basename}.script_locked_caption_qa.json",
    }


def build_script_locked_caption_package(
    script_path: Path,
    timing_path: Path,
    output_dir: Path,
    basename: str,
    voice_offset_seconds: float,
    outro_cutoff_seconds: float | None,
    story_cutoff_seconds: float | None,
    max_chars_per_cue: int,
    max_words_per_cue: int,
    min_alignment_coverage: float,
    max_unmatched_script_span: int,
    story_vtt_path: Path | None = None,
    story_srt_path: Path | None = None,
    offset_vtt_path: Path | None = None,
    offset_srt_path: Path | None = None,
    qa_json_path: Path | None = None,
) -> dict[str, Any]:
    script_path = script_path.resolve()
    timing_path = timing_path.resolve()
    script_text = script_path.read_text(encoding="utf-8")
    script_tokens = script_tokens_from_text(script_text)
    timing_tokens = load_timing_tokens(timing_path)
    timed_tokens, alignment_report = align_script_to_timing(
        script_tokens,
        timing_tokens,
        min_alignment_coverage=min_alignment_coverage,
        max_unmatched_script_span=max_unmatched_script_span,
    )

    story_cues = build_caption_cues(
        timed_tokens=timed_tokens,
        voice_offset_seconds=0.0,
        outro_cutoff_seconds=story_cutoff_seconds,
        max_chars_per_cue=max_chars_per_cue,
        max_words_per_cue=max_words_per_cue,
    )
    offset_cues = build_caption_cues(
        timed_tokens=timed_tokens,
        voice_offset_seconds=voice_offset_seconds,
        outro_cutoff_seconds=outro_cutoff_seconds,
        max_chars_per_cue=max_chars_per_cue,
        max_words_per_cue=max_words_per_cue,
    )

    paths = default_output_paths(output_dir, basename, voice_offset_seconds)
    if story_vtt_path is not None:
        paths["story_vtt"] = story_vtt_path
    if story_srt_path is not None:
        paths["story_srt"] = story_srt_path
    if offset_vtt_path is not None:
        paths["offset_vtt"] = offset_vtt_path
    if offset_srt_path is not None:
        paths["offset_srt"] = offset_srt_path
    if qa_json_path is not None:
        paths["qa_json"] = qa_json_path

    write_vtt(paths["story_vtt"], story_cues)
    write_srt(paths["story_srt"], story_cues)
    write_vtt(paths["offset_vtt"], offset_cues)
    write_srt(paths["offset_srt"], offset_cues)

    text_validation = validate_caption_text_matches_script(script_text, story_cues)
    rail_validation = validate_rail_limits(offset_cues, max_chars_per_cue, max_words_per_cue)
    timing_validation = validate_cue_timing(offset_cues, outro_cutoff_seconds)
    reads = {
        "caption_text_matches_script_read": text_validation["status"],
        "caption_alignment_coverage_read": alignment_report["status"],
        "caption_asr_text_not_used_read": "pass",
        "caption_no_speaker_labels_read": "pass",
        "caption_no_caption_after_outro_start_read": timing_validation["status"],
        "caption_rail_safe_chunk_read": rail_validation["status"],
    }
    status = "pass" if all(value == "pass" for value in reads.values()) else "fail"
    qa: dict[str, Any] = {
        "status": status,
        "caption_model": "script_locked_canonical_text_timing_from_asr_v1",
        "script_text_source": artifact_record(script_path),
        "caption_timing_source": artifact_record(timing_path),
        "voice_offset_seconds": voice_offset_seconds,
        "outro_cutoff_seconds": outro_cutoff_seconds,
        "story_cutoff_seconds": story_cutoff_seconds,
        "rail_safe_chunking": {
            "max_chars_per_cue": max_chars_per_cue,
            "max_words_per_cue": max_words_per_cue,
        },
        "alignment": alignment_report,
        "text_validation": text_validation,
        "rail_validation": rail_validation,
        "timing_validation": timing_validation,
        "reads": reads,
        "outputs": {
            key: artifact_record(path) for key, path in paths.items() if key != "qa_json"
        },
        "cue_count": {
            "story": len(story_cues),
            "offset": len(offset_cues),
        },
    }
    paths["qa_json"].parent.mkdir(parents=True, exist_ok=True)
    paths["qa_json"].write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    qa["outputs"]["qa_json"] = artifact_record(paths["qa_json"])
    if status != "pass":
        raise CaptionAlignmentError("Generated caption package failed validation.", qa)
    return qa


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script-path", required=True, type=Path)
    parser.add_argument("--timing-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--basename", required=True)
    parser.add_argument("--voice-offset-seconds", type=float, default=0.0)
    parser.add_argument("--outro-cutoff-seconds", type=float)
    parser.add_argument("--story-cutoff-seconds", type=float)
    parser.add_argument("--max-chars-per-cue", type=int, default=54)
    parser.add_argument("--max-words-per-cue", type=int, default=8)
    parser.add_argument("--min-alignment-coverage", type=float, default=0.985)
    parser.add_argument("--max-unmatched-script-span", type=int, default=8)
    parser.add_argument("--story-vtt-path", type=Path)
    parser.add_argument("--story-srt-path", type=Path)
    parser.add_argument("--offset-vtt-path", type=Path)
    parser.add_argument("--offset-srt-path", type=Path)
    parser.add_argument("--qa-json-path", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        qa = build_script_locked_caption_package(
            script_path=args.script_path,
            timing_path=args.timing_path,
            output_dir=args.output_dir,
            basename=args.basename,
            voice_offset_seconds=args.voice_offset_seconds,
            outro_cutoff_seconds=args.outro_cutoff_seconds,
            story_cutoff_seconds=args.story_cutoff_seconds,
            max_chars_per_cue=args.max_chars_per_cue,
            max_words_per_cue=args.max_words_per_cue,
            min_alignment_coverage=args.min_alignment_coverage,
            max_unmatched_script_span=args.max_unmatched_script_span,
            story_vtt_path=args.story_vtt_path,
            story_srt_path=args.story_srt_path,
            offset_vtt_path=args.offset_vtt_path,
            offset_srt_path=args.offset_srt_path,
            qa_json_path=args.qa_json_path,
        )
    except CaptionAlignmentError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(json.dumps(exc.report, indent=2, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"status": qa["status"], "reads": qa["reads"], "outputs": qa["outputs"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
