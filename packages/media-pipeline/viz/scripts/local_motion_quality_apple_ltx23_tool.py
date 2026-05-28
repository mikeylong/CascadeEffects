#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INFO_PREFIXES = {
    "staged_path": "INFO  Staged asset: ",
    "stage_manifest_path": "INFO  Manifest: ",
}
DEFAULT_CONFIG = "config/experiments/local_motion_quality_challenger_phase2_apple_ltx23.json"
BEAT_LOCAL_APPLE_EXCEPTION_OUTCOME = "beat-local Apple-native exception"
CONTACT_SHEET_FILTER = "fps=1,scale=176:-1,tile=6x1:padding=8:margin=8:color=black"
TIME_REAL_RE = re.compile(r"^\s*([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys\s*$")
TIME_RSS_RE = re.compile(r"^\s*([\d]+)\s+maximum resident set size\s*$")


class ExperimentError(RuntimeError):
    pass


@dataclass(frozen=True)
class BeatSpec:
    id: str
    role: str
    archetype: str
    frame_override: int


@dataclass(frozen=True)
class VariantSpec:
    id: str
    label: str
    model: str
    mode: str
    extra_args: list[str]


@dataclass(frozen=True)
class ShortBeat:
    id: str
    preset_id: str
    cue_start_seconds: float
    cue_end_seconds: float
    target_duration_seconds: float
    motion_prompt: str
    still_override_path: Path


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    title: str
    short_manifest_path: Path
    baseline_summary_path: Path
    output_root: Path
    review_note_path: Path
    runtime_root: Path
    runtime_repo: str
    width: int
    height: int
    primary_seed: int
    winner_seed: int
    max_wall_clock_multiplier: float
    fallback_to_q4_on_runtime_or_memory: bool
    beats: list[BeatSpec]
    variants: list[VariantSpec]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_stamp() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def resolve_absolute(path_text: str, *, label: str) -> Path:
    path = Path(str(path_text)).expanduser()
    if not path.is_absolute():
        raise ExperimentError(f"{label} must be an absolute path, got {path_text!r}")
    return path.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Apple-native LTX 2.3 local motion quality experiment.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--run-root", help="Optional absolute run root override.")
    return parser.parse_args()


def load_config(path: Path) -> ExperimentConfig:
    payload = read_json(path)
    beats = [BeatSpec(**item) for item in payload["beats"]]
    variants = [VariantSpec(**item) for item in payload["variants"]]
    config = ExperimentConfig(
        experiment_id=str(payload["experiment_id"]).strip(),
        title=str(payload["title"]).strip(),
        short_manifest_path=resolve_absolute(payload["short_manifest_path"], label=f"{path}: short_manifest_path"),
        baseline_summary_path=resolve_absolute(payload["baseline_summary_path"], label=f"{path}: baseline_summary_path"),
        output_root=resolve_absolute(payload["output_root"], label=f"{path}: output_root"),
        review_note_path=resolve_absolute(payload["review_note_path"], label=f"{path}: review_note_path"),
        runtime_root=resolve_absolute(payload["runtime_root"], label=f"{path}: runtime_root"),
        runtime_repo=str(payload["runtime_repo"]).strip(),
        width=int(payload["width"]),
        height=int(payload["height"]),
        primary_seed=int(payload["primary_seed"]),
        winner_seed=int(payload["winner_seed"]),
        max_wall_clock_multiplier=float(payload["max_wall_clock_multiplier"]),
        fallback_to_q4_on_runtime_or_memory=bool(payload["fallback_to_q4_on_runtime_or_memory"]),
        beats=beats,
        variants=variants,
    )
    if not config.beats or not config.variants:
        raise ExperimentError(f"{path}: beats and variants must be non-empty")
    return config


def load_short_beats(short_manifest_path: Path, selected_ids: set[str]) -> tuple[dict[str, ShortBeat], dict[str, Any]]:
    payload = read_json(short_manifest_path)
    resolved: dict[str, ShortBeat] = {}
    for item in payload["beats"]:
        beat_id = str(item["id"]).strip()
        if beat_id not in selected_ids:
            continue
        still_text = str(item.get("still_override_path", "")).strip()
        if not still_text:
            raise ExperimentError(f"{short_manifest_path}: beat {beat_id} is missing still_override_path")
        still_path = resolve_absolute(still_text, label=f"{short_manifest_path}: beat {beat_id} still_override_path")
        if not still_path.exists():
            raise ExperimentError(f"Still override not found for {beat_id}: {still_path}")
        resolved[beat_id] = ShortBeat(
            id=beat_id,
            preset_id=str(item["preset_id"]).strip(),
            cue_start_seconds=float(item["cue_start_seconds"]),
            cue_end_seconds=float(item["cue_end_seconds"]),
            target_duration_seconds=float(item["target_duration_seconds"]),
            motion_prompt=str(item["motion_prompt"]).strip(),
            still_override_path=still_path,
        )
    missing = sorted(selected_ids - set(resolved))
    if missing:
        raise ExperimentError(f"{short_manifest_path}: missing selected beats: {', '.join(missing)}")
    return resolved, payload


def run_command(
    command: list[str],
    *,
    label: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip() or f"{label} failed"
        raise ExperimentError(f"{label}: {details}")
    return completed


def extract_info_path(output: str, prefix: str, *, preserve_links: bool = False) -> Path:
    for line in output.splitlines():
        if line.startswith(prefix):
            raw_path = Path(line[len(prefix) :].strip()).expanduser()
            if not raw_path.is_absolute():
                raw_path = Path.cwd() / raw_path
            if preserve_links:
                return Path(os.path.abspath(str(raw_path)))
            return raw_path.resolve()
    raise ExperimentError(f"Could not find {prefix!r} in command output")


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def ffprobe_duration(path: Path) -> float:
    completed = run_command(
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
        label=f"ffprobe duration {path.name}",
    )
    return float(completed.stdout.strip())


def video_has_audio_stream(path: Path) -> bool:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ExperimentError(completed.stderr.strip() or completed.stdout.strip() or f"ffprobe failed for {path}")
    return bool(completed.stdout.strip())


def strip_video_audio_in_place(path: Path) -> None:
    temp_path = path.with_name(f".{path.name}.silent.mp4")
    temp_path.unlink(missing_ok=True)
    completed = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-c",
            "copy",
            "-map_metadata",
            "-1",
            "-movflags",
            "+faststart",
            str(temp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ExperimentError(completed.stderr.strip() or completed.stdout.strip() or f"Failed to strip audio from {path}")
    temp_path.replace(path)


def ensure_contact_sheet(video_path: Path, output_path: Path) -> Path:
    if output_path.exists():
        return output_path
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            CONTACT_SHEET_FILTER,
            "-frames:v",
            "1",
            str(output_path),
        ],
        label=f"contact sheet {video_path.name}",
    )
    return output_path.resolve()


def parse_time_metrics(path: Path) -> dict[str, float | int]:
    real = user = sys_time = None
    max_rss_bytes = None
    if not path.exists():
        return {
            "real_seconds": 0.0,
            "user_seconds": 0.0,
            "sys_seconds": 0.0,
            "max_resident_size_bytes": 0,
        }
    for line in path.read_text(encoding="utf-8").splitlines():
        if real is None:
            match = TIME_REAL_RE.match(line)
            if match:
                real = float(match.group(1))
                user = float(match.group(2))
                sys_time = float(match.group(3))
                continue
        if max_rss_bytes is None:
            match = TIME_RSS_RE.match(line)
            if match:
                max_rss_bytes = int(match.group(1))
    return {
        "real_seconds": 0.0 if real is None else real,
        "user_seconds": 0.0 if user is None else user,
        "sys_seconds": 0.0 if sys_time is None else sys_time,
        "max_resident_size_bytes": 0 if max_rss_bytes is None else max_rss_bytes,
    }


def baseline_control_metrics(summary_path: Path) -> tuple[dict[str, Any], float]:
    payload = read_json(summary_path)
    for entry in payload.get("entries", []):
        if entry.get("beat_id") == "beat_02a" and entry.get("variant_id") == "baseline":
            metrics = entry.get("time_metrics", {})
            return entry, float(metrics.get("real_seconds", 0.0) or 0.0)
    raise ExperimentError(f"{summary_path}: could not locate baseline beat_02a metrics")


def ensure_runtime(config: ExperimentConfig, run_root: Path) -> dict[str, str]:
    runtime_root = config.runtime_root
    repo_path = runtime_root
    venv_python = repo_path / ".venv" / "bin" / "python"
    if not repo_path.exists():
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        run_command(["git", "clone", config.runtime_repo, str(repo_path)], label="clone ltx-2-mlx")
    elif not (repo_path / ".git").exists():
        raise ExperimentError(f"{repo_path} exists but is not a git checkout")
    run_command(["git", "-C", str(repo_path), "rev-parse", "HEAD"], label="inspect ltx-2-mlx checkout")
    if not venv_python.exists():
        run_command(["uv", "sync", "--all-extras"], label="uv sync ltx-2-mlx", cwd=repo_path)
    if not venv_python.exists():
        raise ExperimentError(f"Expected runtime python after install: {venv_python}")
    install_manifest = {
        "runtime_root": str(repo_path),
        "python": str(venv_python),
        "git_head": run_command(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            label="ltx-2-mlx git head",
        ).stdout.strip(),
    }
    write_json(run_root / "runtime_install.json", install_manifest)
    return install_manifest


def stage_beat(repo_root: Path, run_root: Path, beat: ShortBeat, width: int, height: int) -> dict[str, Any]:
    stage_record_path = run_root / "staged" / f"{beat.id}.json"
    if stage_record_path.exists():
        payload = read_json(stage_record_path)
        staged_path = Path(payload["staged_path"]).expanduser()
        manifest_path = Path(payload["stage_manifest_path"]).expanduser().resolve()
        if staged_path.exists() and manifest_path.exists():
            return payload
    completed = run_command(
        [
            str(repo_root / "scripts" / "handoff-stage.sh"),
            str(beat.still_override_path),
            "--from",
            "comfy",
            "--prompt",
            beat.motion_prompt,
            "--width",
            str(width),
            "--height",
            str(height),
        ],
        label=f"handoff-stage {beat.id}",
    )
    payload = {
        "beat_id": beat.id,
        "still_override_path": str(beat.still_override_path),
        "motion_prompt": beat.motion_prompt,
        "staged_path": str(extract_info_path(completed.stdout, INFO_PREFIXES["staged_path"], preserve_links=True)),
        "stage_manifest_path": str(extract_info_path(completed.stdout, INFO_PREFIXES["stage_manifest_path"])),
    }
    write_json(stage_record_path, payload)
    return payload


def run_with_timeout(
    command: list[str],
    *,
    label: str,
    cwd: Path,
    timeout_seconds: float | None,
    time_output_path: Path,
) -> tuple[subprocess.CompletedProcess[str] | None, float, bool]:
    time_output_path.parent.mkdir(parents=True, exist_ok=True)
    wrapped = ["/usr/bin/time", "-l", "-o", str(time_output_path), *command]
    started = time.monotonic()
    process = subprocess.Popen(
        wrapped,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    elapsed = time.monotonic() - started
    if timed_out:
        return None, elapsed, True
    completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip() or f"{label} failed"
        raise ExperimentError(f"{label}: {details}")
    return completed, elapsed, False


def runtime_info(runtime_root: Path) -> dict[str, Any]:
    python_path = runtime_root / ".venv" / "bin" / "python"
    return {
        "runtime_root": str(runtime_root),
        "python": str(python_path),
    }


def info_variant(runtime_root: Path, run_root: Path, variant: VariantSpec) -> dict[str, Any]:
    info_path = run_root / "info" / f"{variant.id}.json"
    stdout_path = run_root / "logs" / f"info__{variant.id}.stdout.log"
    stderr_path = run_root / "logs" / f"info__{variant.id}.stderr.log"
    if info_path.exists():
        return read_json(info_path)
    completed = run_command(
        ["uv", "run", "ltx-2-mlx", "info", "--model", variant.model],
        label=f"ltx-2-mlx info {variant.id}",
        cwd=runtime_root,
    )
    write_text(stdout_path, completed.stdout)
    write_text(stderr_path, completed.stderr)
    payload = {
        "variant_id": variant.id,
        "model": variant.model,
        "stdout_log_path": str(stdout_path),
        "stderr_log_path": str(stderr_path),
        "stdout": completed.stdout,
    }
    write_json(info_path, payload)
    return payload


def render_variant(
    *,
    runtime_root: Path,
    run_root: Path,
    beat_spec: BeatSpec,
    beat: ShortBeat,
    variant: VariantSpec,
    seed: int,
    width: int,
    height: int,
    timeout_seconds: float | None,
    staged_record: dict[str, Any],
    phase: str,
) -> dict[str, Any]:
    entry_slug = f"{phase}__{beat.id}__{variant.id}__seed{seed}"
    entry_path = run_root / "entries" / f"{entry_slug}.json"
    output_path = ensure_parent(run_root / "clips" / phase / beat.id / f"{variant.id}__seed{seed}.mp4")
    stdout_path = ensure_parent(run_root / "logs" / f"{entry_slug}.stdout.log")
    stderr_path = ensure_parent(run_root / "logs" / f"{entry_slug}.stderr.log")
    time_path = ensure_parent(run_root / "metrics" / f"{entry_slug}.time.txt")

    if entry_path.exists():
        payload = read_json(entry_path)
        existing_output = Path(payload.get("output_path", "")).expanduser()
        if existing_output.exists():
            return payload

    command = [
        "uv",
        "run",
        "ltx-2-mlx",
        "generate",
        "--prompt",
        beat.motion_prompt,
        "--output",
        str(output_path),
        "--model",
        variant.model,
        "--height",
        str(height),
        "--width",
        str(width),
        "--frames",
        str(beat_spec.frame_override),
        "--seed",
        str(seed),
        "--image",
        staged_record["staged_path"],
        *variant.extra_args,
    ]

    completed, elapsed, timed_out = run_with_timeout(
        command,
        label=f"ltx-2-mlx generate {entry_slug}",
        cwd=runtime_root,
        timeout_seconds=timeout_seconds,
        time_output_path=time_path,
    )
    stdout = "" if completed is None else completed.stdout
    stderr = "" if completed is None else completed.stderr
    write_text(stdout_path, stdout)
    write_text(stderr_path, stderr)

    payload = {
        "phase": phase,
        "beat_id": beat.id,
        "beat_role": beat_spec.role,
        "archetype": beat_spec.archetype,
        "preset_id": beat.preset_id,
        "cue_start_seconds": beat.cue_start_seconds,
        "cue_end_seconds": beat.cue_end_seconds,
        "target_duration_seconds": beat.target_duration_seconds,
        "frames": beat_spec.frame_override,
        "seed": seed,
        "variant_id": variant.id,
        "variant_label": variant.label,
        "mode": variant.mode,
        "model": variant.model,
        "extra_args": list(variant.extra_args),
        "still_override_path": str(beat.still_override_path),
        "staged_path": staged_record["staged_path"],
        "stage_manifest_path": staged_record["stage_manifest_path"],
        "output_path": str(output_path),
        "stdout_log_path": str(stdout_path),
        "stderr_log_path": str(stderr_path),
        "time_metrics_path": str(time_path),
        "observed_elapsed_seconds": round(elapsed, 2),
        "timed_out": timed_out,
        "status": "timed_out" if timed_out else "completed",
        "disposition": "pending",
        "review_note": "",
    }
    if output_path.exists() and not timed_out:
        if video_has_audio_stream(output_path):
            strip_video_audio_in_place(output_path)
        payload["duration_seconds"] = round(ffprobe_duration(output_path), 6)
        payload["contact_sheet_path"] = str(
            ensure_contact_sheet(output_path, ensure_parent(run_root / "contact_sheets" / f"{entry_slug}.png"))
        )
    else:
        payload["duration_seconds"] = 0.0
        payload["contact_sheet_path"] = ""
    payload["time_metrics"] = parse_time_metrics(time_path)
    write_json(entry_path, payload)
    return payload


def list_entries(run_root: Path) -> list[dict[str, Any]]:
    entries_dir = run_root / "entries"
    if not entries_dir.exists():
        return []
    entries = [read_json(path) for path in sorted(entries_dir.glob("*.json"))]
    entries.sort(
        key=lambda item: (
            item.get("phase", ""),
            item.get("beat_id", ""),
            item.get("variant_id", ""),
            int(item.get("seed", 0)),
        )
    )
    return entries


def emit_summary(config: ExperimentConfig, run_root: Path, short_manifest_payload: dict[str, Any], outcome: str) -> None:
    entries = list_entries(run_root)
    payload = {
        "experiment_id": config.experiment_id,
        "title": config.title,
        "created_at": utc_now().isoformat().replace("+00:00", "Z"),
        "short_manifest_path": str(config.short_manifest_path),
        "baseline_summary_path": str(config.baseline_summary_path),
        "short_id": short_manifest_payload.get("short_id", ""),
        "episode_id": short_manifest_payload.get("episode_id", ""),
        "run_root": str(run_root),
        "review_note_path": str(config.review_note_path),
        "outcome": outcome,
        "entries": entries,
    }
    write_json(run_root / "summary.json", payload)

    lines = [
        f"# {config.title}",
        "",
        f"- `experiment_id`: `{config.experiment_id}`",
        f"- `run_root`: `{run_root}`",
        f"- `outcome`: `{outcome}`",
        "",
        "## Entries",
        "",
    ]
    if not entries:
        lines.append("No entries recorded.")
    else:
        for entry in entries:
            metrics = entry.get("time_metrics", {})
            lines.extend(
                [
                    f"### {entry['phase']} / {entry['beat_id']} / {entry['variant_id']} / seed {entry['seed']}",
                    f"- `status`: `{entry.get('status', '')}`",
                    f"- `model`: `{entry.get('model', '')}`",
                    f"- `mode`: `{entry.get('mode', '')}`",
                    f"- `output_path`: `{entry.get('output_path', '')}`",
                    f"- `contact_sheet_path`: `{entry.get('contact_sheet_path', '')}`",
                    f"- `observed_elapsed_seconds`: `{entry.get('observed_elapsed_seconds', 0)}`",
                    f"- `real_seconds`: `{metrics.get('real_seconds', 0)}`",
                    f"- `max_resident_size_bytes`: `{metrics.get('max_resident_size_bytes', 0)}`",
                    f"- `disposition`: `{entry.get('disposition', 'pending')}`",
                    "",
                ]
            )
    write_text(run_root / "summary.md", "\n".join(lines).rstrip() + "\n")


def write_decision_note(
    *,
    config: ExperimentConfig,
    run_root: Path,
    baseline_entry: dict[str, Any],
    ceiling_seconds: float,
    q8_one_stage: dict[str, Any] | None,
    q8_hq: dict[str, Any] | None,
    q4_one_stage: dict[str, Any] | None,
    stress_entry: dict[str, Any] | None,
    winner_seed_control: dict[str, Any] | None,
    winner_seed_stress: dict[str, Any] | None,
    outcome: str,
) -> None:
    lines = [
        "# Local Motion Quality Decision",
        "",
        f"- `run_root`: `{run_root}`",
        f"- `decision_date`: `{utc_now().date().isoformat()}`",
        f"- `outcome`: `{outcome}`",
        f"- `control_runtime_ceiling_seconds`: `{round(ceiling_seconds, 2)}`",
        "",
        "## Baseline",
        "",
        f"- `baseline_output_path`: `{baseline_entry.get('output_path', '')}`",
        f"- `baseline_real_seconds`: `{baseline_entry.get('time_metrics', {}).get('real_seconds', 0)}`",
        f"- `baseline_max_resident_size_bytes`: `{baseline_entry.get('time_metrics', {}).get('max_resident_size_bytes', 0)}`",
        "",
        "## Candidates",
        "",
    ]
    for label, entry in (
        ("q8 one-stage", q8_one_stage),
        ("q8 HQ", q8_hq),
        ("q4 fallback", q4_one_stage),
    ):
        lines.append(f"### {label}")
        if entry is None:
            lines.append("No entry recorded.")
        else:
            metrics = entry.get("time_metrics", {})
            lines.extend(
                [
                    f"- `status`: `{entry.get('status', '')}`",
                    f"- `timed_out`: `{entry.get('timed_out', False)}`",
                    f"- `output_path`: `{entry.get('output_path', '') if entry.get('contact_sheet_path') else ''}`",
                    f"- `observed_elapsed_seconds`: `{entry.get('observed_elapsed_seconds', 0)}`",
                    f"- `real_seconds`: `{metrics.get('real_seconds', 0)}`",
                    f"- `max_resident_size_bytes`: `{metrics.get('max_resident_size_bytes', 0)}`",
                    "",
                ]
            )
        lines.append("")
    if stress_entry is not None:
        metrics = stress_entry.get("time_metrics", {})
        lines.extend(
            [
                "## Stress",
                "",
                f"- `variant_id`: `{stress_entry.get('variant_id', '')}`",
                f"- `status`: `{stress_entry.get('status', '')}`",
                f"- `output_path`: `{stress_entry.get('output_path', '') if stress_entry.get('contact_sheet_path') else ''}`",
                f"- `contact_sheet_path`: `{stress_entry.get('contact_sheet_path', '')}`",
                f"- `observed_elapsed_seconds`: `{stress_entry.get('observed_elapsed_seconds', 0)}`",
                f"- `real_seconds`: `{metrics.get('real_seconds', 0)}`",
                f"- `max_resident_size_bytes`: `{metrics.get('max_resident_size_bytes', 0)}`",
                "",
            ]
        )
    if winner_seed_control is not None or winner_seed_stress is not None:
        lines.extend(["## Winner Seed", ""])
        for label, entry in (
            ("control", winner_seed_control),
            ("stress", winner_seed_stress),
        ):
            lines.append(f"### {label}")
            if entry is None:
                lines.append("No entry recorded.")
            else:
                metrics = entry.get("time_metrics", {})
                lines.extend(
                    [
                        f"- `status`: `{entry.get('status', '')}`",
                        f"- `output_path`: `{entry.get('output_path', '') if entry.get('contact_sheet_path') else ''}`",
                        f"- `contact_sheet_path`: `{entry.get('contact_sheet_path', '')}`",
                        f"- `observed_elapsed_seconds`: `{entry.get('observed_elapsed_seconds', 0)}`",
                        f"- `real_seconds`: `{metrics.get('real_seconds', 0)}`",
                        f"- `max_resident_size_bytes`: `{metrics.get('max_resident_size_bytes', 0)}`",
                        "",
                    ]
                )
            lines.append("")
    write_text(run_root / "decision.md", "\n".join(lines).rstrip() + "\n")


def write_review_note(
    *,
    config: ExperimentConfig,
    run_root: Path,
    baseline_entry: dict[str, Any],
    ceiling_seconds: float,
    q8_one_stage: dict[str, Any] | None,
    q8_hq: dict[str, Any] | None,
    q4_one_stage: dict[str, Any] | None,
    stress_entry: dict[str, Any] | None,
    winner_seed_control: dict[str, Any] | None,
    winner_seed_stress: dict[str, Any] | None,
    outcome: str,
) -> None:
    def review_block(case_id: str, entry: dict[str, Any] | None, beat_label: str, disposition: str, failure_reason: str, next_action: str, note: str) -> list[str]:
        if entry is None:
            artifact_path = ""
            staged_asset = ""
        else:
            artifact_path = entry.get("output_path", "") if entry.get("contact_sheet_path") else ""
            staged_asset = entry.get("staged_path", "")
        return [
            f"### `{case_id}`",
            "",
            "- `review_type`: `motion`",
            "- `gate_level`: `motion`",
            "- `episode_id`: `challenger`",
            f"- `case_id`: `{case_id}`",
            f"- `archetype`: `{beat_label}`",
            f"- `source_asset`: `{baseline_entry.get('still_override_path', '') if entry is None else entry.get('still_override_path', '')}`",
            f"- `staged_asset`: `{staged_asset}`",
            "- `video_manifest`: ``",
            f"- `artifact_path`: `{artifact_path}`",
            f"- `motion_carrier`: `{case_id}`",
            "- `source_baked_issue`: `false`",
            f"- `disposition`: `{disposition}`",
            f"- `failure_reason`: `{failure_reason}`",
            f"- `next_action`: `{next_action}`",
            f"- `review_note`: `{note}`",
            "",
        ]

    lines = [
        "# Challenger Local Motion Quality Experiment Pass 02 Apple LTX 2.3",
        "",
        f"- `review_date`: `{utc_now().date().isoformat()}`",
        f"- `experiment_id`: `{config.experiment_id}`",
        f"- `run_root`: `{run_root}`",
        f"- `baseline_summary_path`: `{config.baseline_summary_path}`",
        f"- `result`: `{outcome}`",
        f"- `control_runtime_ceiling_seconds`: `{round(ceiling_seconds, 2)}`",
        "",
    ]
    lines.extend(
        review_block(
            "challenger_short__beat_02a_apple_ltx23_q8_one_stage",
            q8_one_stage,
            "field_joint_motion",
            "reject" if q8_one_stage and q8_one_stage.get("timed_out") else ("keep" if q8_one_stage and q8_one_stage.get("contact_sheet_path") else "reject"),
            "practical runtime gate failure before completion" if q8_one_stage and q8_one_stage.get("timed_out") else "",
            "fall back to q4 control-only or keep baseline" if q8_one_stage and q8_one_stage.get("timed_out") else "compare against baseline",
            "Apple-native q8 one-stage timed out on the control beat and therefore failed the practicality gate." if q8_one_stage and q8_one_stage.get("timed_out") else "Apple-native q8 one-stage completed and should be compared against the distilled baseline.",
        )
    )
    if q8_hq is not None:
        lines.extend(
            review_block(
                "challenger_short__beat_02a_apple_ltx23_q8_hq",
                q8_hq,
                "field_joint_motion",
                "keep" if q8_hq.get("contact_sheet_path") else "reject",
                "" if q8_hq.get("contact_sheet_path") else "did not complete",
                "compare against baseline and q8 one-stage" if q8_hq.get("contact_sheet_path") else "keep baseline",
                "Apple-native q8 HQ completed on the control beat." if q8_hq.get("contact_sheet_path") else "Apple-native q8 HQ did not produce a completed control clip.",
            )
        )
    if q4_one_stage is not None:
        lines.extend(
            review_block(
                "challenger_short__beat_02a_apple_ltx23_q4_one_stage",
                q4_one_stage,
                "field_joint_motion",
                "keep" if q4_one_stage.get("contact_sheet_path") else "reject",
                "" if q4_one_stage.get("contact_sheet_path") else "did not complete",
                "compare against baseline" if q4_one_stage.get("contact_sheet_path") else "phase 2 failed",
                "Apple-native q4 fallback completed on the control beat." if q4_one_stage.get("contact_sheet_path") else "Apple-native q4 fallback did not produce a completed control clip.",
            )
        )
    if stress_entry is not None:
        lines.extend(
            review_block(
                "challenger_short__beat_01b_apple_ltx23_q8_one_stage",
                stress_entry,
                "cold_launch_site_motion",
                "keep" if stress_entry.get("contact_sheet_path") else "reject",
                "" if stress_entry.get("contact_sheet_path") else "did not complete",
                "run winner-seed verification" if stress_entry.get("contact_sheet_path") else "keep baseline",
                "Apple-native q8 one-stage completed on the stress beat." if stress_entry.get("contact_sheet_path") else "Apple-native q8 one-stage did not produce a completed stress clip.",
            )
        )
    if winner_seed_control is not None:
        lines.extend(
            review_block(
                "challenger_short__beat_02a_apple_ltx23_q8_one_stage_seed314159",
                winner_seed_control,
                "field_joint_motion",
                "keep" if winner_seed_control.get("contact_sheet_path") else "reject",
                "" if winner_seed_control.get("contact_sheet_path") else "did not complete",
                "confirm robustness against the first-pass control clip" if winner_seed_control.get("contact_sheet_path") else "keep baseline",
                "Apple-native q8 one-stage completed the control rerun at the winner seed." if winner_seed_control.get("contact_sheet_path") else "Apple-native q8 one-stage did not complete the control rerun at the winner seed.",
            )
        )
    if winner_seed_stress is not None:
        lines.extend(
            review_block(
                "challenger_short__beat_01b_apple_ltx23_q8_one_stage_seed314159",
                winner_seed_stress,
                "cold_launch_site_motion",
                "keep" if winner_seed_stress.get("contact_sheet_path") else "reject",
                "" if winner_seed_stress.get("contact_sheet_path") else "did not complete",
                "record robustness result and compare against the first-pass stress clip" if winner_seed_stress.get("contact_sheet_path") else "keep baseline",
                "Apple-native q8 one-stage completed the stress rerun at the winner seed." if winner_seed_stress.get("contact_sheet_path") else "Apple-native q8 one-stage did not complete the stress rerun at the winner seed.",
            )
        )
    write_text(config.review_note_path, "\n".join(lines).rstrip() + "\n")


def main() -> int:
    args = parse_args()
    repo_root = resolve_absolute(args.repo_root, label="--repo-root")
    config_path = Path(args.config).expanduser()
    if not config_path.is_absolute():
        config_path = (repo_root / config_path).resolve()
    config = load_config(config_path)
    run_root = resolve_absolute(args.run_root, label="--run-root") if args.run_root else (config.output_root / utc_stamp()).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    selected_ids = {item.id for item in config.beats}
    short_beats, short_manifest_payload = load_short_beats(config.short_manifest_path, selected_ids)
    baseline_entry, baseline_real_seconds = baseline_control_metrics(config.baseline_summary_path)
    ceiling_seconds = baseline_real_seconds * config.max_wall_clock_multiplier

    write_json(
        run_root / "experiment_manifest.json",
        {
            "created_at": utc_now().isoformat().replace("+00:00", "Z"),
            "experiment_id": config.experiment_id,
            "title": config.title,
            "config_source_path": str(config_path),
            "run_root": str(run_root),
            "baseline_summary_path": str(config.baseline_summary_path),
            "ceiling_seconds": ceiling_seconds,
            "beats": [asdict(item) for item in config.beats],
            "variants": [asdict(item) for item in config.variants],
        },
    )

    install_manifest = ensure_runtime(config, run_root)
    runtime_root = Path(install_manifest["runtime_root"])

    q8_one_stage_variant = next(item for item in config.variants if item.id == "q8_one_stage")
    q8_hq_variant = next(item for item in config.variants if item.id == "q8_hq")
    q4_variant = next(item for item in config.variants if item.id == "q4_one_stage")

    info_variant(runtime_root, run_root, q8_one_stage_variant)

    beat_specs = {item.id: item for item in config.beats}
    staged_records = {
        beat_id: stage_beat(repo_root, run_root, short_beats[beat_id], config.width, config.height)
        for beat_id in selected_ids
    }

    q8_one_stage = render_variant(
        runtime_root=runtime_root,
        run_root=run_root,
        beat_spec=beat_specs["beat_02a"],
        beat=short_beats["beat_02a"],
        variant=q8_one_stage_variant,
        seed=config.primary_seed,
        width=config.width,
        height=config.height,
        timeout_seconds=ceiling_seconds,
        staged_record=staged_records["beat_02a"],
        phase="control",
    )

    q8_hq: dict[str, Any] | None = None
    q4_one_stage: dict[str, Any] | None = None
    stress_entry: dict[str, Any] | None = None
    winner_seed_control: dict[str, Any] | None = None
    winner_seed_stress: dict[str, Any] | None = None
    outcome = "phase 2 failed"
    winner_variant: VariantConfig | None = None

    q8_completed = bool(q8_one_stage.get("contact_sheet_path"))
    q8_timed_out = bool(q8_one_stage.get("timed_out"))

    if q8_completed and not q8_timed_out:
        q8_hq = render_variant(
            runtime_root=runtime_root,
            run_root=run_root,
            beat_spec=beat_specs["beat_02a"],
            beat=short_beats["beat_02a"],
            variant=q8_hq_variant,
            seed=config.primary_seed,
            width=config.width,
            height=config.height,
            timeout_seconds=ceiling_seconds,
            staged_record=staged_records["beat_02a"],
            phase="control",
        )
        if q8_hq.get("contact_sheet_path"):
            outcome = BEAT_LOCAL_APPLE_EXCEPTION_OUTCOME
            winner_variant = q8_hq_variant
        else:
            outcome = BEAT_LOCAL_APPLE_EXCEPTION_OUTCOME
            winner_variant = q8_one_stage_variant
    elif config.fallback_to_q4_on_runtime_or_memory and (q8_timed_out or not q8_completed):
        info_variant(runtime_root, run_root, q4_variant)
        q4_one_stage = render_variant(
            runtime_root=runtime_root,
            run_root=run_root,
            beat_spec=beat_specs["beat_02a"],
            beat=short_beats["beat_02a"],
            variant=q4_variant,
            seed=config.primary_seed,
            width=config.width,
            height=config.height,
            timeout_seconds=ceiling_seconds,
            staged_record=staged_records["beat_02a"],
            phase="control",
        )
        if q4_one_stage.get("contact_sheet_path"):
            outcome = BEAT_LOCAL_APPLE_EXCEPTION_OUTCOME
            winner_variant = q4_variant
        else:
            outcome = "keep baseline"
    else:
        outcome = "keep baseline"

    if outcome == BEAT_LOCAL_APPLE_EXCEPTION_OUTCOME and winner_variant is not None:
        stress_entry = render_variant(
            runtime_root=runtime_root,
            run_root=run_root,
            beat_spec=beat_specs["beat_01b"],
            beat=short_beats["beat_01b"],
            variant=winner_variant,
            seed=config.primary_seed,
            width=config.width,
            height=config.height,
            timeout_seconds=ceiling_seconds,
            staged_record=staged_records["beat_01b"],
            phase="stress",
        )
        if not stress_entry.get("contact_sheet_path"):
            outcome = "keep baseline"
        else:
            winner_seed_control = render_variant(
                runtime_root=runtime_root,
                run_root=run_root,
                beat_spec=beat_specs["beat_02a"],
                beat=short_beats["beat_02a"],
                variant=winner_variant,
                seed=config.winner_seed,
                width=config.width,
                height=config.height,
                timeout_seconds=ceiling_seconds,
                staged_record=staged_records["beat_02a"],
                phase="winner_seed",
            )
            winner_seed_stress = render_variant(
                runtime_root=runtime_root,
                run_root=run_root,
                beat_spec=beat_specs["beat_01b"],
                beat=short_beats["beat_01b"],
                variant=winner_variant,
                seed=config.winner_seed,
                width=config.width,
                height=config.height,
                timeout_seconds=ceiling_seconds,
                staged_record=staged_records["beat_01b"],
                phase="winner_seed",
            )

    if outcome == "phase 2 failed" and not (q4_one_stage and q4_one_stage.get("contact_sheet_path")):
        outcome = "keep baseline"

    write_decision_note(
        config=config,
        run_root=run_root,
        baseline_entry=baseline_entry,
        ceiling_seconds=ceiling_seconds,
        q8_one_stage=q8_one_stage,
        q8_hq=q8_hq,
        q4_one_stage=q4_one_stage,
        stress_entry=stress_entry,
        winner_seed_control=winner_seed_control,
        winner_seed_stress=winner_seed_stress,
        outcome=outcome,
    )
    write_review_note(
        config=config,
        run_root=run_root,
        baseline_entry=baseline_entry,
        ceiling_seconds=ceiling_seconds,
        q8_one_stage=q8_one_stage,
        q8_hq=q8_hq,
        q4_one_stage=q4_one_stage,
        stress_entry=stress_entry,
        winner_seed_control=winner_seed_control,
        winner_seed_stress=winner_seed_stress,
        outcome=outcome,
    )
    emit_summary(config, run_root, short_manifest_payload, outcome)
    print(f"INFO  Experiment run root: {run_root}")
    print(f"INFO  Experiment summary: {run_root / 'summary.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExperimentError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        raise SystemExit(1)
