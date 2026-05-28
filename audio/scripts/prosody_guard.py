#!/usr/bin/env python3
from __future__ import annotations

import argparse
import array
import json
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from statistics import median
from typing import Any, Iterable, List

ANALYSIS_SAMPLE_RATE = 8_000
SHORT_SENTENCE_MAX_WORDS = 12
SHORT_SENTENCE_MAX_CHARS = 80
MIN_ALIGN_COVERAGE = 0.75
MIN_PARITY_COVERAGE = 0.88
MIN_PARITY_RATIO = 0.88
FINAL_SENTENCE_PREV_SPIKE = 1.20
FINAL_SENTENCE_GROUP_SPIKE = 1.15
FINAL_SENTENCE_MAX_WORDS = 4
ONSET_MAX_SECONDS = 0.9
ONSET_FRACTION = 0.45
PLACEHOLDER_DOT = "\u223f"
TRANSCRIBE_MODEL = "small"
EMPHASIS_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "had",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}
PROTECTED_ABBREVIATIONS = (
    "a.m.",
    "p.m.",
    "U.S.",
    "Mr.",
    "Mrs.",
    "Ms.",
    "Dr.",
    "Jr.",
    "Sr.",
)
PROSODY_ESCALATION_HINTS = (
    "crescendo",
    "lift",
    "build",
    "rising",
    "rise",
    "swell",
    "climb",
)


@dataclass
class SourceSentence:
    index: int
    text: str
    start_char: int
    end_char: int
    tokens: list[str]


@dataclass
class WordToken:
    token: str
    start: float
    end: float
    raw: str


@dataclass
class SentenceAlignment:
    source_index: int
    start: float | None
    end: float | None
    coverage: float
    matched_tokens: int
    total_tokens: int
    transcript_indexes: list[int]


@dataclass
class ProsodyFlag:
    job_index: int
    out: str
    start_sentence: int
    end_sentence: int
    reason: str
    metrics: dict[str, float]
    sentences: list[str]


def die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.replace("\u2019", "'").replace("\u2018", "'")
    value = value.replace("\u2014", " ").replace("\u2013", " ")
    value = value.lower()
    tokens = re.findall(r"[a-z0-9']+", value)
    return " ".join(token.strip("'") for token in tokens if token.strip("'"))


def tokenize(value: str) -> list[str]:
    normalized = normalize_text(value)
    return normalized.split() if normalized else []


def protect_abbreviations(text: str) -> str:
    protected = text
    for abbr in PROTECTED_ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", PLACEHOLDER_DOT))
    protected = re.sub(r"(?<=\d)\.(?=\d)", PLACEHOLDER_DOT, protected)
    return protected


def split_sentences(text: str) -> list[SourceSentence]:
    protected = protect_abbreviations(text)
    pattern = re.compile(r".+?(?:[.!?]+(?:[\"'”’)\]]*)|$)", re.S)
    sentences: list[SourceSentence] = []
    for match in pattern.finditer(protected):
        raw_start, raw_end = match.span()
        chunk = text[raw_start:raw_end]
        if not chunk.strip():
            continue
        leading = len(chunk) - len(chunk.lstrip())
        trailing = len(chunk) - len(chunk.rstrip())
        start = raw_start + leading
        end = raw_end - trailing
        sentence_text = text[start:end]
        if not sentence_text.strip():
            continue
        sentences.append(
            SourceSentence(
                index=len(sentences),
                text=sentence_text,
                start_char=start,
                end_char=end,
                tokens=tokenize(sentence_text),
            )
        )
    return sentences


def read_jobs(manifest_path: Path) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for line_no, raw in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
        except json.JSONDecodeError as exc:
            die(f"{manifest_path}:{line_no}: invalid JSON ({exc})")
        if not isinstance(job, dict):
            die(f"{manifest_path}:{line_no}: expected an object")
        jobs.append(job)
    if not jobs:
        die(f"No jobs found in {manifest_path}")
    return jobs


def write_jobs(path: Path, jobs: Iterable[dict[str, Any]]) -> None:
    rows = [json.dumps(job, ensure_ascii=False) for job in jobs]
    path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def load_transcript_words(whisperx_json_path: Path) -> list[WordToken]:
    obj = json.loads(whisperx_json_path.read_text(encoding="utf-8"))
    raw_words = obj.get("word_segments")
    if not isinstance(raw_words, list):
        raw_words = []
        for segment in obj.get("segments", []):
            raw_words.extend(segment.get("words", []))

    words: list[WordToken] = []
    for item in raw_words:
        raw = str(item.get("word", "")).strip()
        token = normalize_text(raw)
        if not raw or not token:
            continue
        start = item.get("start")
        end = item.get("end")
        if start is None or end is None:
            continue
        words.append(WordToken(token=token, start=float(start), end=float(end), raw=raw))
    return words


def align_sentences(sentences: list[SourceSentence], transcript_words: list[WordToken]) -> list[SentenceAlignment]:
    source_token_sentence_indexes: list[int] = []
    source_tokens: list[str] = []
    sentence_token_ranges: list[tuple[int, int]] = []
    cursor = 0
    for sentence in sentences:
        start = cursor
        source_tokens.extend(sentence.tokens)
        source_token_sentence_indexes.extend([sentence.index] * len(sentence.tokens))
        cursor += len(sentence.tokens)
        sentence_token_ranges.append((start, cursor))

    transcript_tokens = [word.token for word in transcript_words]
    mapping: dict[int, int] = {}
    matcher = SequenceMatcher(None, source_tokens, transcript_tokens, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            continue
        for offset in range(i2 - i1):
            mapping[i1 + offset] = j1 + offset

    alignments: list[SentenceAlignment] = []
    for sentence, (start, end) in zip(sentences, sentence_token_ranges):
        matched = [mapping[idx] for idx in range(start, end) if idx in mapping]
        total = end - start
        coverage = len(matched) / total if total else 0.0
        if matched:
            first_word = transcript_words[min(matched)]
            last_word = transcript_words[max(matched)]
            start_time = first_word.start
            end_time = last_word.end
        else:
            start_time = None
            end_time = None
        alignments.append(
            SentenceAlignment(
                source_index=sentence.index,
                start=start_time,
                end=end_time,
                coverage=coverage,
                matched_tokens=len(matched),
                total_tokens=total,
                transcript_indexes=matched,
            )
        )
    return alignments


def extract_audio_samples(audio_path: Path) -> array.array:
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(audio_path),
        "-f",
        "s16le",
        "-ac",
        "1",
        "-ar",
        str(ANALYSIS_SAMPLE_RATE),
        "-",
    ]
    raw = subprocess.check_output(cmd)
    samples = array.array("h")
    samples.frombytes(raw)
    return samples


def estimate_f0_values(samples: array.array, start_s: float, end_s: float) -> list[float]:
    start = max(0, int(start_s * ANALYSIS_SAMPLE_RATE))
    end = min(len(samples), int(end_s * ANALYSIS_SAMPLE_RATE))
    window = 1024
    hop = 256
    if end - start < window:
        return []

    min_lag = ANALYSIS_SAMPLE_RATE // 320
    max_lag = ANALYSIS_SAMPLE_RATE // 80
    values: list[float] = []

    for frame_start in range(start, end - window, hop):
        frame = samples[frame_start : frame_start + window]
        mean = sum(frame) / len(frame)
        centered = [sample - mean for sample in frame]
        energy = sum(value * value for value in centered) / len(centered)
        if energy < 500_000:
            continue

        best_lag = None
        best_corr = 0.0
        for lag in range(min_lag, max_lag + 1):
            numerator = 0.0
            denom_a = 0.0
            denom_b = 0.0
            limit = window - lag
            for idx in range(limit):
                a = centered[idx]
                b = centered[idx + lag]
                numerator += a * b
                denom_a += a * a
                denom_b += b * b
            if denom_a == 0.0 or denom_b == 0.0:
                continue
            corr = numerator / math.sqrt(denom_a * denom_b)
            if corr > best_corr:
                best_corr = corr
                best_lag = lag
        if best_lag is not None and best_corr > 0.35:
            values.append(ANALYSIS_SAMPLE_RATE / best_lag)
    return values


def sentence_pitch_stats(samples: array.array, alignment: SentenceAlignment) -> tuple[float | None, float | None]:
    if alignment.start is None or alignment.end is None or alignment.end <= alignment.start:
        return None, None
    sentence_values = estimate_f0_values(samples, alignment.start, alignment.end)
    if not sentence_values:
        return None, None
    duration = alignment.end - alignment.start
    onset_end = min(alignment.end, alignment.start + min(ONSET_MAX_SECONDS, max(duration * ONSET_FRACTION, 0.4)))
    onset_values = estimate_f0_values(samples, alignment.start, onset_end)
    if not onset_values:
        onset_values = sentence_values
    return median(sentence_values), median(onset_values)


def is_short_sentence(sentence: SourceSentence) -> bool:
    return len(sentence.tokens) <= SHORT_SENTENCE_MAX_WORDS and len(sentence.text) <= SHORT_SENTENCE_MAX_CHARS


def extract_emphasis_tokens(instructions: str) -> set[str]:
    emphasis_line = ""
    for line in instructions.splitlines():
        if line.lower().startswith("emphasis:"):
            emphasis_line = line.split(":", 1)[1]
            break
    tokens = {token for token in tokenize(emphasis_line) if token not in EMPHASIS_STOPWORDS}
    return tokens


def sentence_explicitly_emphasized(sentence: SourceSentence, emphasis_tokens: set[str]) -> bool:
    significant = {token for token in sentence.tokens if token not in EMPHASIS_STOPWORDS}
    if not significant:
        return False
    return significant.issubset(emphasis_tokens)


def instructions_allow_escalation(instructions: str) -> bool:
    lowered = instructions.lower()
    return any(keyword in lowered for keyword in PROSODY_ESCALATION_HINTS)


def spoken_text_for_job(job: dict[str, Any]) -> str:
    value = job.get("spoken_input")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return str(job.get("input") or "").strip()


def ends_paragraph_or_chunk(sentences: list[SourceSentence], source_text: str, end_index: int) -> bool:
    if end_index >= len(sentences) - 1:
        return True
    gap = source_text[sentences[end_index].end_char : sentences[end_index + 1].start_char]
    return "\n\n" in gap


def pick_flags_for_job(
    job_index: int,
    job: dict[str, Any],
    sentences: list[SourceSentence],
    alignments: list[SentenceAlignment],
    samples: array.array,
    *,
    source_text: str,
) -> list[ProsodyFlag]:
    instructions = str(job.get("instructions") or "")
    emphasis_tokens = extract_emphasis_tokens(instructions)
    allow_escalation = instructions_allow_escalation(instructions)
    candidates: list[tuple[float, ProsodyFlag]] = []
    pitch_cache: dict[int, tuple[float | None, float | None]] = {}

    def get_pitch(sentence_index: int) -> tuple[float | None, float | None]:
        if sentence_index not in pitch_cache:
            pitch_cache[sentence_index] = sentence_pitch_stats(samples, alignments[sentence_index])
        return pitch_cache[sentence_index]

    for end in range(len(sentences)):
        final_sentence = sentences[end]
        if not is_short_sentence(final_sentence):
            continue
        if len(final_sentence.tokens) > FINAL_SENTENCE_MAX_WORDS:
            continue
        if not ends_paragraph_or_chunk(sentences, source_text, end):
            continue
        if allow_escalation or sentence_explicitly_emphasized(final_sentence, emphasis_tokens):
            continue
        for size in range(3, 4):
            start = end - size + 1
            if start < 0:
                continue
            group = sentences[start : end + 1]
            if not all(is_short_sentence(sentence) for sentence in group):
                continue
            group_alignments = alignments[start : end + 1]
            if any(alignment.coverage < MIN_ALIGN_COVERAGE for alignment in group_alignments):
                continue

            medians: list[float] = []
            onset_last = None
            for offset, alignment in enumerate(group_alignments):
                sentence_median, onset_median = get_pitch(alignment.source_index)
                if sentence_median is None:
                    medians = []
                    break
                medians.append(sentence_median)
                if offset == len(group_alignments) - 1:
                    onset_last = onset_median
            if not medians or onset_last is None or len(medians) < 2:
                continue

            previous_median = medians[-2]
            group_median = median(medians)
            if previous_median <= 0.0 or group_median <= 0.0:
                continue
            prev_ratio = onset_last / previous_median
            group_ratio = onset_last / group_median
            if prev_ratio < FINAL_SENTENCE_PREV_SPIKE or group_ratio < FINAL_SENTENCE_GROUP_SPIKE:
                continue

            score = (prev_ratio - FINAL_SENTENCE_PREV_SPIKE) + (group_ratio - FINAL_SENTENCE_GROUP_SPIKE)
            candidates.append(
                (
                    score,
                    ProsodyFlag(
                        job_index=job_index,
                        out=str(job.get("out", "")),
                        start_sentence=start,
                        end_sentence=end,
                        reason="final sentence onset pitch spike",
                        metrics={
                            "previous_ratio": round(prev_ratio, 4),
                            "group_ratio": round(group_ratio, 4),
                            "onset_last_hz": round(onset_last, 3),
                            "previous_hz": round(previous_median, 3),
                            "group_hz": round(group_median, 3),
                        },
                        sentences=[sentence.text for sentence in group],
                    ),
                )
            )

    if not candidates:
        return []

    candidates.sort(key=lambda item: (item[1].end_sentence, item[0]), reverse=True)
    chosen: list[ProsodyFlag] = []
    used_ranges: list[tuple[int, int]] = []
    for _, candidate in candidates:
        if any(not (candidate.end_sentence < used_start or candidate.start_sentence > used_end) for used_start, used_end in used_ranges):
            continue
        used_ranges.append((candidate.start_sentence, candidate.end_sentence))
        chosen.append(candidate)
    chosen.sort(key=lambda candidate: candidate.start_sentence)
    return chosen


def split_repaired_job(
    job: dict[str, Any],
    visible_sentences: list[SourceSentence],
    spoken_sentences: list[SourceSentence],
    flags: list[ProsodyFlag],
) -> list[dict[str, Any]]:
    base_out = str(job["out"])
    out_path = Path(base_out)
    suffix = out_path.suffix
    stem = out_path.stem
    visible_source = str(job["input"])
    spoken_source = spoken_text_for_job(job)

    spans: list[tuple[int, int, bool]] = []
    cursor = 0
    for flag in flags:
        if cursor <= flag.start_sentence - 1:
            spans.append((cursor, flag.start_sentence - 1, False))
        spans.append((flag.start_sentence, flag.end_sentence, True))
        cursor = flag.end_sentence + 1
    if cursor <= len(visible_sentences) - 1:
        spans.append((cursor, len(visible_sentences) - 1, False))

    replacement_jobs: list[dict[str, Any]] = []
    for index, (start_sentence, end_sentence, is_repair) in enumerate(spans):
        visible_start = visible_sentences[start_sentence].start_char
        visible_end = visible_sentences[end_sentence].end_char
        spoken_start = spoken_sentences[start_sentence].start_char
        spoken_end = spoken_sentences[end_sentence].end_char
        visible_segment = visible_source[visible_start:visible_end].strip()
        spoken_segment = spoken_source[spoken_start:spoken_end].strip()
        if not visible_segment:
            continue
        replacement = dict(job)
        for key in list(replacement):
            if key.startswith("elevenlabs_"):
                replacement.pop(key, None)
        replacement["input"] = visible_segment
        if spoken_segment and spoken_segment != visible_segment:
            replacement["spoken_input"] = spoken_segment
        else:
            replacement.pop("spoken_input", None)
        replacement["out"] = f"{stem}__guard_{chr(ord('a') + index)}{suffix}"
        if is_repair:
            instructions = str(job.get("instructions") or "").rstrip()
            forced = (
                "Delivery: Keep this sentence group evenly weighted, matter-of-fact, "
                "and downward-final on the last sentence."
            )
            replacement["instructions"] = f"{instructions}\n{forced}" if instructions else forced
        replacement_jobs.append(replacement)
    return replacement_jobs


def build_guard_report(
    *,
    status: str,
    jobs_analyzed: int,
    flags: list[ProsodyFlag],
    repair_jobs: list[dict[str, Any]],
    message: str,
    parity_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "jobs_analyzed": jobs_analyzed,
        "flags": [asdict(flag) for flag in flags],
        "repair_job_count": len(repair_jobs),
        "repair_jobs": [{"out": job["out"], "input_chars": len(job["input"])} for job in repair_jobs],
        "parity_results": parity_results or [],
    }


def validate_parity(job: dict[str, Any], transcript_path: Path) -> dict[str, Any]:
    words = load_transcript_words(transcript_path)
    transcript_tokens = [word.token for word in words]
    source_tokens = tokenize(spoken_text_for_job(job))
    matcher = SequenceMatcher(None, source_tokens, transcript_tokens, autojunk=False)

    matched = 0
    for tag, i1, i2, _, _ in matcher.get_opcodes():
        if tag == "equal":
            matched += i2 - i1

    coverage = matched / len(source_tokens) if source_tokens else 1.0
    ratio = matcher.ratio()
    first_ok = bool(source_tokens) and bool(transcript_tokens) and source_tokens[0] == transcript_tokens[0]
    last_ok = bool(source_tokens) and bool(transcript_tokens) and source_tokens[-1] == transcript_tokens[-1]
    ok = coverage >= MIN_PARITY_COVERAGE and ratio >= MIN_PARITY_RATIO and first_ok and last_ok
    return {
        "out": job["out"],
        "coverage": round(coverage, 4),
        "ratio": round(ratio, 4),
        "first_token_ok": first_ok,
        "last_token_ok": last_ok,
        "ok": ok,
    }


def clear_guard_outputs(guard_dir: Path) -> None:
    for path in (
        guard_dir / "guard_report.json",
        guard_dir / "repair_jobs.jsonl",
        guard_dir / "effective_jobs.jsonl",
    ):
        if path.exists():
            path.unlink()
    (guard_dir / "transcripts" / "original").mkdir(parents=True, exist_ok=True)
    repair_dir = guard_dir / "transcripts" / "repair"
    if repair_dir.exists():
        shutil.rmtree(repair_dir)
    repair_dir.mkdir(parents=True, exist_ok=True)


def run_transcribe(output_dir: Path, audio_paths: list[Path]) -> None:
    if not audio_paths:
        return
    cmd = ["transcribe", "-m", TRANSCRIBE_MODEL, "-o", str(output_dir)]
    cmd.extend(str(path) for path in audio_paths)
    subprocess.run(cmd, check=True)


def run_tts_batch(
    *,
    manifest_path: Path,
    render_dir: Path,
    provider: str,
    model: str,
    voice: str,
    response_format: str,
    tts_gen: Path,
    openai_python_spec: str,
    elevenlabs_helper: Path,
    elevenlabs_output_format: str,
) -> None:
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            die("OPENAI_API_KEY is not set; cannot auto-repair flagged prosody spans.")
        cmd = [
            "uv",
            "run",
            "--with",
            openai_python_spec,
            "python",
            str(tts_gen),
            "speak-batch",
            "--input",
            str(manifest_path),
            "--out-dir",
            str(render_dir),
            "--model",
            model,
            "--voice",
            voice,
            "--response-format",
            response_format,
            "--force",
        ]
    elif provider == "elevenlabs":
        if not os.getenv("ELEVEN_LABS_API_KEY"):
            die("ELEVEN_LABS_API_KEY is not set; cannot auto-repair flagged prosody spans.")
        if not os.getenv("ELEVEN_LABS_VOICE_ID"):
            die("ELEVEN_LABS_VOICE_ID is not set; cannot auto-repair flagged prosody spans.")
        cmd = [
            "python3",
            str(elevenlabs_helper),
            "render-batch",
            "--input",
            str(manifest_path),
            "--out-dir",
            str(render_dir),
            "--model",
            model,
            "--output-format",
            elevenlabs_output_format,
            "--force",
        ]
    else:
        die(f"Unsupported provider: {provider}")
    subprocess.run(cmd, check=True)


def chunk_transcript_path(transcript_dir: Path, out_name: str) -> Path:
    return transcript_dir / f"{Path(out_name).stem}.whisperx.json"


def transcripts_are_current(transcript_dir: Path, audio_paths: list[Path]) -> bool:
    if not audio_paths:
        return True
    for audio_path in audio_paths:
        transcript_path = chunk_transcript_path(transcript_dir, audio_path.name)
        if not transcript_path.exists():
            return False
        if transcript_path.stat().st_mtime < audio_path.stat().st_mtime:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect and repair unintended prosody spikes before merge.")
    parser.add_argument("--final-jobs", required=True)
    parser.add_argument("--render-dir", required=True)
    parser.add_argument("--guard-dir", required=True)
    parser.add_argument("--provider", choices=("openai", "elevenlabs"), default="openai")
    parser.add_argument("--model", required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--response-format", required=True)
    parser.add_argument("--tts-gen", required=True)
    parser.add_argument("--openai-python-spec", required=True)
    parser.add_argument("--elevenlabs-helper", required=True)
    parser.add_argument("--elevenlabs-output-format", required=True)
    args = parser.parse_args()

    final_jobs_path = Path(args.final_jobs)
    render_dir = Path(args.render_dir)
    guard_dir = Path(args.guard_dir)
    guard_dir.mkdir(parents=True, exist_ok=True)
    clear_guard_outputs(guard_dir)

    original_transcript_dir = guard_dir / "transcripts" / "original"
    repair_transcript_dir = guard_dir / "transcripts" / "repair"

    jobs = read_jobs(final_jobs_path)
    render_audio_paths: list[Path] = []
    for job in jobs:
        audio_path = render_dir / str(job["out"])
        if not audio_path.exists():
            die(f"Missing rendered chunk: {audio_path}")
        render_audio_paths.append(audio_path)

    if not transcripts_are_current(original_transcript_dir, render_audio_paths):
        run_transcribe(original_transcript_dir, render_audio_paths)

    all_flags: list[ProsodyFlag] = []
    flags_by_job: dict[int, list[ProsodyFlag]] = {}
    for job_index, job in enumerate(jobs):
        visible_sentences = split_sentences(str(job["input"]))
        if len(visible_sentences) < 2:
            continue
        spoken_source = spoken_text_for_job(job)
        spoken_sentences = split_sentences(spoken_source)
        if len(spoken_sentences) != len(visible_sentences):
            die(
                f"Visible and spoken sentence counts differ for {job.get('out')}: "
                f"{len(visible_sentences)} vs {len(spoken_sentences)}"
            )
        if len(spoken_sentences) < 2:
            continue
        whisperx_json = chunk_transcript_path(original_transcript_dir, str(job["out"]))
        if not whisperx_json.exists():
            die(f"Missing transcript JSON for rendered chunk: {whisperx_json}")
        transcript_words = load_transcript_words(whisperx_json)
        alignments = align_sentences(spoken_sentences, transcript_words)
        samples = extract_audio_samples(render_dir / str(job["out"]))
        flags = pick_flags_for_job(
            job_index,
            job,
            spoken_sentences,
            alignments,
            samples,
            source_text=spoken_source,
        )
        if flags:
            flags_by_job[job_index] = flags
            all_flags.extend(flags)

    guard_report_path = guard_dir / "guard_report.json"
    repair_jobs_path = guard_dir / "repair_jobs.jsonl"
    effective_jobs_path = guard_dir / "effective_jobs.jsonl"

    if not all_flags:
        guard_report_path.write_text(
            json.dumps(
                build_guard_report(
                    status="ok_no_repairs",
                    jobs_analyzed=len(jobs),
                    flags=[],
                    repair_jobs=[],
                    message="No likely unintended prosody spikes were detected.",
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("No likely unintended prosody spikes detected.")
        return 0

    repair_jobs: list[dict[str, Any]] = []
    effective_jobs: list[dict[str, Any]] = []
    for job_index, job in enumerate(jobs):
        flags = flags_by_job.get(job_index)
        if not flags:
            effective_jobs.append(job)
            continue
        visible_sentences = split_sentences(str(job["input"]))
        spoken_sentences = split_sentences(spoken_text_for_job(job))
        replacements = split_repaired_job(job, visible_sentences, spoken_sentences, flags)
        repair_jobs.extend(replacements)
        effective_jobs.extend(replacements)

    write_jobs(repair_jobs_path, repair_jobs)
    run_tts_batch(
        manifest_path=repair_jobs_path,
        render_dir=render_dir,
        provider=args.provider,
        model=args.model,
        voice=args.voice,
        response_format=args.response_format,
        tts_gen=Path(args.tts_gen),
        openai_python_spec=args.openai_python_spec,
        elevenlabs_helper=Path(args.elevenlabs_helper),
        elevenlabs_output_format=args.elevenlabs_output_format,
    )
    run_transcribe(repair_transcript_dir, [render_dir / str(job["out"]) for job in repair_jobs])

    parity_results = []
    failed_parity = False
    for job in repair_jobs:
        transcript_path = chunk_transcript_path(repair_transcript_dir, str(job["out"]))
        if not transcript_path.exists():
            die(f"Missing transcript JSON for repaired subchunk: {transcript_path}")
        result = validate_parity(job, transcript_path)
        parity_results.append(result)
        if not result["ok"]:
            failed_parity = True

    if failed_parity:
        guard_report_path.write_text(
            json.dumps(
                build_guard_report(
                    status="failed_text_parity",
                    jobs_analyzed=len(jobs),
                    flags=all_flags,
                    repair_jobs=repair_jobs,
                    message="Repair generation completed, but transcript parity failed for at least one repaired subchunk.",
                    parity_results=parity_results,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("Prosody guard detected issues, but repaired subchunk parity failed. See guard_report.json.", file=sys.stderr)
        return 1

    write_jobs(effective_jobs_path, effective_jobs)
    guard_report_path.write_text(
        json.dumps(
            build_guard_report(
                status="ok_repaired",
                jobs_analyzed=len(jobs),
                flags=all_flags,
                repair_jobs=repair_jobs,
                message="Prosody guard detected likely unintended spikes and generated a repaired effective manifest.",
                parity_results=parity_results,
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Detected {len(all_flags)} likely unintended prosody spikes.")
    print(f"Wrote repaired manifest {effective_jobs_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
