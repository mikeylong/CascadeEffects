#!/usr/bin/env python3
"""Analyze TTS sibilance hotspots and build comparison audition manifests."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

FRAME_MIN_RMS = -30.0
FRAME_SCORE_MIN = 10.5
CLUSTER_SUPPRESS_SECONDS = 0.35
DEFAULT_TOP_N = 8
DEFAULT_SEED_TOLERANCE = 1.0
FIRST_PASS_VARIANTS = (
    ("cedar", 0.95, False),
    ("marin", 0.95, False),
)
SECOND_PASS_VARIANTS = (
    (0.95, True),
    (0.93, True),
)
ANTI_SIBILANCE_SUFFIX = (
    "Consonants: keep S, SH, and CH soft and controlled; avoid sharp, bright, "
    "or hissy fricatives. Delivery: prefer rounded documentary diction over "
    "crisp edge; preserve clarity without exaggerated articulation."
)


@dataclass(frozen=True)
class ManifestJob:
    index: int
    out: str
    chunk_id: str
    input_text: str
    instructions: str
    response_format: str
    model: str | None
    voice: str | None
    speed: float | None
    duration: float
    start_time: float
    end_time: float


def _die(message: str) -> "NoReturn":
    raise SystemExit(message)


def _run_capture(cmd: Sequence[str], *, stderr: int | None = subprocess.PIPE) -> str:
    proc = subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=stderr,
        text=True,
    )
    return proc.stdout


def _ffprobe_duration(path: Path) -> float:
    return float(
        _run_capture(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            stderr=subprocess.DEVNULL,
        ).strip()
    )


def _normalize_time_token(raw: str) -> float:
    value = str(raw).strip()
    if not value:
        _die("Empty time token.")
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        return float(value)

    parts = value.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60.0 + float(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600.0 + float(minutes) * 60.0 + float(seconds)
    _die(f"Unsupported time format: {value}")


def format_timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def load_manifest_jobs(manifest_path: Path, render_dir: Path) -> list[ManifestJob]:
    if not manifest_path.exists():
        _die(f"Missing manifest: {manifest_path}")
    jobs: list[ManifestJob] = []
    start_time = 0.0
    for index, raw in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        job_data = json.loads(line)
        out = str(job_data["out"]).strip()
        input_text = str(job_data.get("input") or "").strip()
        if not input_text:
            _die(f"{manifest_path}:{index}: missing input text")
        rendered_path = render_dir / out
        if not rendered_path.exists():
            _die(f"Missing rendered chunk: {rendered_path}")
        duration = _ffprobe_duration(rendered_path)
        response_format = str(
            job_data.get("response_format") or job_data.get("format") or rendered_path.suffix.lstrip(".") or "wav"
        ).strip()
        chunk_id = Path(out).stem
        instructions = str(job_data.get("instructions") or "").strip()
        model = str(job_data["model"]).strip() if job_data.get("model") else None
        voice = str(job_data["voice"]).strip() if job_data.get("voice") else None
        speed_value = job_data.get("speed")
        speed = float(speed_value) if speed_value is not None else None
        jobs.append(
            ManifestJob(
                index=index,
                out=out,
                chunk_id=chunk_id,
                input_text=input_text,
                instructions=instructions,
                response_format=response_format,
                model=model,
                voice=voice,
                speed=speed,
                duration=duration,
                start_time=start_time,
                end_time=start_time + duration,
            )
        )
        start_time += duration
    if not jobs:
        _die(f"No jobs found in {manifest_path}")
    return jobs


def map_time_to_job(master_time: float, jobs: Sequence[ManifestJob]) -> ManifestJob:
    for job in jobs:
        if job.start_time <= master_time < job.end_time:
            return job
    if math.isclose(master_time, jobs[-1].end_time, rel_tol=0.0, abs_tol=0.001):
        return jobs[-1]
    _die(f"Could not map master time {master_time:.3f} to a chunk boundary.")


def _parse_frame_metadata(master_path: Path) -> list[dict[str, float]]:
    filter_graph = (
        "astats=metadata=1:reset=1,"
        "aspectralstats=measure=centroid+flatness+rolloff+spread+crest,"
        "ametadata=print:file=-"
    )
    output = _run_capture(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(master_path),
            "-af",
            filter_graph,
            "-f",
            "null",
            "-",
        ],
        stderr=subprocess.DEVNULL,
    )
    frames: list[dict[str, float]] = []
    current: dict[str, float] = {}
    for line in output.splitlines():
        if line.startswith("frame:"):
            if current:
                frames.append(current)
            match = re.search(r"pts_time:([0-9.]+)", line)
            current = {"time": float(match.group(1)) if match else 0.0}
            continue
        if "=" not in line or not current:
            continue
        key, value = line.split("=", 1)
        try:
            current[key.strip()] = float(value.strip())
        except ValueError:
            continue
    if current:
        frames.append(current)
    return frames


def _score_frame(frame: dict[str, float]) -> float | None:
    rms = frame.get("lavfi.astats.1.RMS_level")
    if rms is None or rms < FRAME_MIN_RMS:
        return None
    centroid = frame.get("lavfi.aspectralstats.1.centroid", 0.0)
    rolloff = frame.get("lavfi.aspectralstats.1.rolloff", 0.0)
    flatness = frame.get("lavfi.aspectralstats.1.flatness", 0.0)
    return (
        max(0.0, centroid - 2500.0) / 1000.0
        + max(0.0, rolloff - 5000.0) / 1500.0
        + flatness * 6.0
        + max(0.0, -18.0 - rms) * 0.15
    )


def analyze_master(
    master_path: Path,
    manifest_path: Path,
    render_dir: Path,
    *,
    top_n: int = DEFAULT_TOP_N,
    min_score: float = FRAME_SCORE_MIN,
    suppress_seconds: float = CLUSTER_SUPPRESS_SECONDS,
) -> dict[str, Any]:
    jobs = load_manifest_jobs(manifest_path, render_dir)
    hotspots: list[dict[str, Any]] = []
    for frame in _parse_frame_metadata(master_path):
        score = _score_frame(frame)
        if score is None or score < min_score:
            continue
        job = map_time_to_job(frame["time"], jobs)
        local_time = frame["time"] - job.start_time
        hotspots.append(
            {
                "master_time": frame["time"],
                "master_timestamp": format_timestamp(frame["time"]),
                "chunk_id": job.chunk_id,
                "chunk_out": job.out,
                "chunk_start_time": job.start_time,
                "chunk_local_time": local_time,
                "chunk_local_timestamp": format_timestamp(local_time),
                "score": score,
                "rms": frame.get("lavfi.astats.1.RMS_level"),
                "centroid": frame.get("lavfi.aspectralstats.1.centroid"),
                "rolloff": frame.get("lavfi.aspectralstats.1.rolloff"),
                "flatness": frame.get("lavfi.aspectralstats.1.flatness"),
            }
        )
    hotspots.sort(key=lambda item: item["score"], reverse=True)
    selected: list[dict[str, Any]] = []
    selected_times: list[float] = []
    for candidate in hotspots:
        if any(abs(candidate["master_time"] - prev) < suppress_seconds for prev in selected_times):
            continue
        selected_times.append(candidate["master_time"])
        selected.append(candidate)
        if len(selected) >= top_n:
            break
    for index, hotspot in enumerate(selected, start=1):
        hotspot["hotspot_id"] = f"hotspot_{index:02d}"
        for key in ("master_time", "chunk_start_time", "chunk_local_time", "score", "rms", "centroid", "rolloff", "flatness"):
            if hotspot.get(key) is not None:
                hotspot[key] = round(float(hotspot[key]), 6)
    return {
        "master_path": str(master_path),
        "manifest_path": str(manifest_path),
        "render_dir": str(render_dir),
        "top_n": top_n,
        "min_score": min_score,
        "suppress_seconds": suppress_seconds,
        "hotspots": selected,
    }


def _sentence_segments(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.replace("\u2014", " — ")).strip()
    if not normalized:
        return []
    segments = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", normalized) if segment.strip()]
    return segments or [normalized]


def select_excerpt(text: str, local_time: float, duration: float) -> str:
    segments = _sentence_segments(text)
    if not segments:
        return text.strip()
    if len(segments) == 1 or duration <= 0:
        return segments[0]

    lengths = [len(segment) for segment in segments]
    total = float(sum(lengths)) or 1.0
    target = min(max(local_time / duration, 0.0), 1.0) * total
    cumulative = 0.0
    centers: list[float] = []
    for length in lengths:
        centers.append(cumulative + (length / 2.0))
        cumulative += length
    center_index = min(range(len(segments)), key=lambda idx: abs(centers[idx] - target))
    start = end = center_index
    excerpt = segments[center_index]
    min_chars = 120
    max_chars = 420
    while len(excerpt) < min_chars and (start > 0 or end < len(segments) - 1):
        left_score = abs(centers[start - 1] - target) if start > 0 else float("inf")
        right_score = abs(centers[end + 1] - target) if end < len(segments) - 1 else float("inf")
        if left_score <= right_score and start > 0:
            start -= 1
        elif end < len(segments) - 1:
            end += 1
        else:
            break
        candidate = " ".join(segments[start : end + 1]).strip()
        if len(candidate) <= max_chars:
            excerpt = candidate
        else:
            break
    return excerpt


def _match_report_hotspot(seed_time: float, report_hotspots: Sequence[dict[str, Any]], tolerance: float) -> dict[str, Any] | None:
    nearest: dict[str, Any] | None = None
    best_delta = float("inf")
    for hotspot in report_hotspots:
        delta = abs(float(hotspot["master_time"]) - seed_time)
        if delta < best_delta:
            best_delta = delta
            nearest = hotspot
    if nearest is None or best_delta > tolerance:
        return None
    return dict(nearest)


def _synthesized_hotspot(seed_time: float, jobs: Sequence[ManifestJob], index: int) -> dict[str, Any]:
    job = map_time_to_job(seed_time, jobs)
    local_time = seed_time - job.start_time
    return {
        "hotspot_id": f"hotspot_{index:02d}",
        "master_time": round(seed_time, 6),
        "master_timestamp": format_timestamp(seed_time),
        "chunk_id": job.chunk_id,
        "chunk_out": job.out,
        "chunk_start_time": round(job.start_time, 6),
        "chunk_local_time": round(local_time, 6),
        "chunk_local_timestamp": format_timestamp(local_time),
        "score": None,
        "rms": None,
        "centroid": None,
        "rolloff": None,
        "flatness": None,
    }


def resolve_hotspots(
    jobs: Sequence[ManifestJob],
    *,
    report_path: Path | None,
    seed_times: Sequence[float],
    top_n: int,
    seed_tolerance: float,
) -> list[dict[str, Any]]:
    report_hotspots: list[dict[str, Any]] = []
    if report_path is not None and report_path.exists():
        report_data = json.loads(report_path.read_text(encoding="utf-8"))
        report_hotspots = list(report_data.get("hotspots") or [])

    if seed_times:
        resolved: list[dict[str, Any]] = []
        for index, seed_time in enumerate(seed_times, start=1):
            matched = _match_report_hotspot(seed_time, report_hotspots, seed_tolerance)
            hotspot = matched if matched is not None else _synthesized_hotspot(seed_time, jobs, index)
            hotspot["hotspot_id"] = f"hotspot_{index:02d}"
            resolved.append(hotspot)
        return resolved

    if not report_hotspots:
        _die("Hotspot report is required when seed times are not provided.")
    return [dict(item) for item in report_hotspots[:top_n]]


def build_audition_jobs(
    manifest_path: Path,
    render_dir: Path,
    *,
    report_path: Path | None,
    output_path: Path,
    stage: str,
    response_format: str,
    top_n: int,
    seed_times: Sequence[float],
    seed_tolerance: float,
    winner_voice: str | None,
    anti_sibilance_suffix: str,
) -> list[dict[str, Any]]:
    jobs = load_manifest_jobs(manifest_path, render_dir)
    jobs_by_id = {job.chunk_id: job for job in jobs}
    selected_hotspots = resolve_hotspots(
        jobs,
        report_path=report_path,
        seed_times=seed_times,
        top_n=top_n,
        seed_tolerance=seed_tolerance,
    )
    manifest_jobs: list[dict[str, Any]] = []
    for hotspot in selected_hotspots:
        chunk_id = hotspot["chunk_id"]
        source_job = jobs_by_id[chunk_id]
        excerpt = select_excerpt(
            source_job.input_text,
            float(hotspot["chunk_local_time"]),
            source_job.duration,
        )
        base_job: dict[str, Any] = {
            "input": excerpt,
            "response_format": response_format,
            "source_hotspot_id": hotspot["hotspot_id"],
            "source_master_time": hotspot["master_time"],
            "source_chunk_id": chunk_id,
            "source_chunk_local_time": hotspot["chunk_local_time"],
        }
        if source_job.model:
            base_job["model"] = source_job.model
        if stage == "first-pass":
            variants = [
                {
                    "voice": voice,
                    "speed": speed,
                    "instructions": source_job.instructions or None,
                    "suffix": None,
                }
                for voice, speed, _ in FIRST_PASS_VARIANTS
            ]
        elif stage == "second-pass":
            if winner_voice not in {"cedar", "marin"}:
                _die("second-pass auditions require --winner-voice of cedar or marin")
            variants = []
            for speed, add_suffix in SECOND_PASS_VARIANTS:
                instructions = source_job.instructions
                if add_suffix:
                    instructions = f"{instructions}\n{anti_sibilance_suffix}".strip() if instructions else anti_sibilance_suffix
                variants.append(
                    {
                        "voice": winner_voice,
                        "speed": speed,
                        "instructions": instructions or None,
                        "suffix": "anti-sibilance",
                    }
                )
        else:
            _die(f"Unsupported audition stage: {stage}")

        for variant_index, variant in enumerate(variants, start=1):
            speed = float(variant["speed"])
            speed_token = str(speed).replace(".", "p")
            voice = str(variant["voice"])
            out_name = (
                f"{hotspot['hotspot_id']}__{chunk_id}__{format_timestamp(float(hotspot['master_time'])).replace(':', '-')}"
                f"__{voice}__s{speed_token}.{response_format}"
            )
            job_data = dict(base_job)
            job_data["out"] = out_name
            job_data["voice"] = voice
            job_data["speed"] = speed
            instructions = variant["instructions"]
            if instructions:
                job_data["instructions"] = instructions
            manifest_jobs.append(job_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(job, ensure_ascii=True) + "\n" for job in manifest_jobs),
        encoding="utf-8",
    )
    return manifest_jobs


def parse_seed_times(values: Iterable[str]) -> list[float]:
    parsed: list[float] = []
    for raw in values:
        for token in str(raw).split(","):
            token = token.strip()
            if not token:
                continue
            parsed.append(_normalize_time_token(token))
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a packaged master for likely sibilance hotspots.")
    analyze.add_argument("--master", required=True, help="Packaged master WAV/FLAC to analyze.")
    analyze.add_argument("--jobs-manifest", required=True, help="Path to final_jobs.jsonl.")
    analyze.add_argument("--render-dir", required=True, help="Directory containing rendered chunk files.")
    analyze.add_argument("--output", required=True, help="Where to write the JSON report.")
    analyze.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help=f"Number of clustered hotspots to retain (default: {DEFAULT_TOP_N}).")
    analyze.add_argument("--min-score", type=float, default=FRAME_SCORE_MIN, help=f"Minimum frame score to consider (default: {FRAME_SCORE_MIN}).")
    analyze.add_argument("--suppress-seconds", type=float, default=CLUSTER_SUPPRESS_SECONDS, help=f"Merge candidate frames inside this time window (default: {CLUSTER_SUPPRESS_SECONDS}).")

    auditions = subparsers.add_parser("build-auditions", help="Build a hotspot audition JSONL manifest.")
    auditions.add_argument("--jobs-manifest", required=True, help="Path to final_jobs.jsonl.")
    auditions.add_argument("--render-dir", required=True, help="Directory containing rendered chunk files.")
    auditions.add_argument("--output", required=True, help="Path to the output audition JSONL manifest.")
    auditions.add_argument("--report", help="Optional hotspot JSON report from the analyze command.")
    auditions.add_argument("--stage", choices=("first-pass", "second-pass"), default="first-pass")
    auditions.add_argument("--response-format", default="wav", help="Output format to write into audition jobs.")
    auditions.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help=f"Top N report hotspots to use when seed times are omitted (default: {DEFAULT_TOP_N}).")
    auditions.add_argument("--seed-time", action="append", default=[], help="Seed hotspot times as HH:MM:SS.mmm or seconds. Repeatable or comma-separated.")
    auditions.add_argument("--seed-tolerance", type=float, default=DEFAULT_SEED_TOLERANCE, help=f"Nearest-report tolerance for seeded times in seconds (default: {DEFAULT_SEED_TOLERANCE}).")
    auditions.add_argument("--winner-voice", choices=("cedar", "marin"), help="Required for second-pass auditions.")
    auditions.add_argument("--anti-sibilance-suffix", default=ANTI_SIBILANCE_SUFFIX, help="Exact instruction suffix for second-pass variants.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        report = analyze_master(
            Path(args.master),
            Path(args.jobs_manifest),
            Path(args.render_dir),
            top_n=args.top_n,
            min_score=args.min_score,
            suppress_seconds=args.suppress_seconds,
        )
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output_path}")
        return 0

    if args.command == "build-auditions":
        report_path = Path(args.report) if args.report else None
        seed_times = parse_seed_times(args.seed_time)
        build_audition_jobs(
            Path(args.jobs_manifest),
            Path(args.render_dir),
            report_path=report_path,
            output_path=Path(args.output),
            stage=args.stage,
            response_format=str(args.response_format).strip().lower(),
            top_n=args.top_n,
            seed_times=seed_times,
            seed_tolerance=args.seed_tolerance,
            winner_voice=args.winner_voice,
            anti_sibilance_suffix=args.anti_sibilance_suffix,
        )
        print(f"Wrote {args.output}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
