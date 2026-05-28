#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INFO_PREFIXES = {
    "staged_path": "INFO  Staged asset: ",
    "stage_manifest_path": "INFO  Manifest: ",
    "output_path": "INFO  Handoff video complete: ",
    "video_manifest_path": "INFO  Handoff video manifest: ",
}
DEFAULT_CONFIG = "config/experiments/local_motion_quality_challenger_phase1.json"
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


@dataclass(frozen=True)
class VariantSpec:
    id: str
    label: str
    pipeline: str
    model_repo: str
    backend_variant: str


@dataclass(frozen=True)
class ShortBeat:
    id: str
    preset_id: str
    cue_start_seconds: float
    cue_end_seconds: float
    target_duration_seconds: float
    motion_prompt: str
    motion_pipeline: str
    frames: int
    still_override_path: Path


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    title: str
    short_manifest_path: Path
    output_root: Path
    review_note_path: Path
    width: int
    height: int
    first_pass_seed: int
    second_pass_seed: int
    max_wall_clock_multiplier: float
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


def resolve_absolute(path_text: str, *, label: str) -> Path:
    path = Path(str(path_text)).expanduser()
    if not path.is_absolute():
        raise ExperimentError(f"{label} must be an absolute path, got {path_text!r}")
    return path.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local MLX motion quality experiment.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument(
        "--run-root",
        help="Absolute path to an existing or new experiment run root. Defaults to output_root/<UTC timestamp>.",
    )
    parser.add_argument(
        "--winner",
        help="Variant id to rerun for the second-pass seed. If omitted, only the first pass is rendered.",
    )
    parser.add_argument(
        "--skip-first-pass",
        action="store_true",
        help="Do not render the seed-42 matrix. Useful when resuming an existing run for the second pass.",
    )
    return parser.parse_args()


def load_config(path: Path) -> ExperimentConfig:
    payload = read_json(path)
    beats = [BeatSpec(**item) for item in payload["beats"]]
    variants = [VariantSpec(**item) for item in payload["variants"]]
    config = ExperimentConfig(
        experiment_id=str(payload["experiment_id"]).strip(),
        title=str(payload["title"]).strip(),
        short_manifest_path=resolve_absolute(payload["short_manifest_path"], label=f"{path}: short_manifest_path"),
        output_root=resolve_absolute(payload["output_root"], label=f"{path}: output_root"),
        review_note_path=resolve_absolute(payload["review_note_path"], label=f"{path}: review_note_path"),
        width=int(payload["width"]),
        height=int(payload["height"]),
        first_pass_seed=int(payload["first_pass_seed"]),
        second_pass_seed=int(payload["second_pass_seed"]),
        max_wall_clock_multiplier=float(payload["max_wall_clock_multiplier"]),
        beats=beats,
        variants=variants,
    )
    if config.width <= 0 or config.height <= 0:
        raise ExperimentError(f"{path}: width and height must be positive")
    if not config.beats:
        raise ExperimentError(f"{path}: beats must be non-empty")
    if not config.variants:
        raise ExperimentError(f"{path}: variants must be non-empty")
    return config


def duration_to_frames(duration_seconds: float, fps: int) -> int:
    if duration_seconds <= 0 or fps <= 0:
        raise ExperimentError(f"Invalid duration/fps: duration={duration_seconds} fps={fps}")
    return max(1, int(round(float(duration_seconds) * float(fps))))


def load_short_beats(short_manifest_path: Path, selected_ids: set[str]) -> tuple[dict[str, ShortBeat], dict[str, Any]]:
    payload = read_json(short_manifest_path)
    fps = int(payload["fps"])
    beats_payload = payload["beats"]
    resolved: dict[str, ShortBeat] = {}
    for item in beats_payload:
        beat_id = str(item["id"]).strip()
        if beat_id not in selected_ids:
            continue
        still_text = str(item.get("still_override_path", "")).strip()
        if not still_text:
            raise ExperimentError(f"{short_manifest_path}: beat {beat_id} is missing still_override_path")
        still_path = resolve_absolute(still_text, label=f"{short_manifest_path}: beat {beat_id} still_override_path")
        if not still_path.exists():
            raise ExperimentError(f"Still override not found for {beat_id}: {still_path}")
        target_duration = float(item["target_duration_seconds"])
        resolved[beat_id] = ShortBeat(
            id=beat_id,
            preset_id=str(item["preset_id"]).strip(),
            cue_start_seconds=float(item["cue_start_seconds"]),
            cue_end_seconds=float(item["cue_end_seconds"]),
            target_duration_seconds=target_duration,
            motion_prompt=str(item["motion_prompt"]).strip(),
            motion_pipeline=str(item["motion_pipeline"]).strip(),
            frames=duration_to_frames(target_duration, fps),
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
    time_output_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    wrapped = list(command)
    if time_output_path is not None:
        time_output_path.parent.mkdir(parents=True, exist_ok=True)
        wrapped = ["/usr/bin/time", "-l", "-o", str(time_output_path), *wrapped]
    completed = subprocess.run(
        wrapped,
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


def parse_time_metrics(path: Path) -> dict[str, float | int]:
    real = user = sys_time = None
    max_rss_bytes = None
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
    if not output_path.exists():
        raise ExperimentError(f"Contact sheet was not created: {output_path}")
    return output_path.resolve()


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ensure_backend_metadata(
    *,
    repo_root: Path,
    run_root: Path,
    variant: VariantSpec,
) -> dict[str, Any]:
    metadata_path = run_root / "backends" / f"{variant.id}.json"
    if metadata_path.exists():
        return read_json(metadata_path)
    completed = run_command(
        [
            str(repo_root / "scripts" / "video.sh"),
            "backend",
            "prepare",
            "--model-repo",
            variant.model_repo,
            "--variant",
            variant.backend_variant,
            "--json",
        ],
        label=f"prepare backend {variant.id}",
    )
    payload = json.loads(completed.stdout)
    payload["variant_id"] = variant.id
    payload["label"] = variant.label
    write_json(metadata_path, payload)
    return payload


def stage_beat(
    *,
    repo_root: Path,
    run_root: Path,
    beat: ShortBeat,
    experiment_width: int,
    experiment_height: int,
) -> dict[str, Any]:
    stage_record_path = run_root / "staged" / f"{beat.id}.json"
    if stage_record_path.exists():
        payload = read_json(stage_record_path)
        staged_path = Path(payload["staged_path"]).expanduser().resolve()
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
            str(experiment_width),
            "--height",
            str(experiment_height),
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


def render_variant(
    *,
    repo_root: Path,
    run_root: Path,
    beat_spec: BeatSpec,
    beat: ShortBeat,
    variant: VariantSpec,
    seed: int,
    phase: str,
    experiment_width: int,
    experiment_height: int,
    prepared_backend_path: str,
    staged_record: dict[str, Any],
) -> dict[str, Any]:
    entry_slug = f"{phase}__{beat.id}__{variant.id}__seed{seed}"
    entry_path = run_root / "entries" / f"{entry_slug}.json"
    if entry_path.exists():
        payload = read_json(entry_path)
        output_path = Path(payload["output_path"]).expanduser().resolve()
        video_manifest_path = Path(payload["video_manifest_path"]).expanduser().resolve()
        if output_path.exists() and video_manifest_path.exists():
            return payload

    output_path = ensure_parent(run_root / "clips" / phase / beat.id / f"{variant.id}__seed{seed}.mp4")
    time_path = ensure_parent(run_root / "metrics" / f"{entry_slug}.time.txt")
    stdout_path = ensure_parent(run_root / "logs" / f"{entry_slug}.stdout.log")
    stderr_path = ensure_parent(run_root / "logs" / f"{entry_slug}.stderr.log")

    command = [
        str(repo_root / "scripts" / "handoff-i2v.sh"),
        staged_record["staged_path"],
        "--prompt",
        beat.motion_prompt,
        "--frames",
        str(beat.frames),
        "--width",
        str(experiment_width),
        "--height",
        str(experiment_height),
        "--seed",
        str(seed),
        "--pipeline",
        variant.pipeline,
        "--model-repo",
        variant.model_repo,
        "--typography",
        "off",
        "--output",
        str(output_path),
    ]
    completed = run_command(
        command,
        label=f"handoff-i2v {entry_slug}",
        time_output_path=time_path,
    )
    write_text(stdout_path, completed.stdout)
    write_text(stderr_path, completed.stderr)

    resolved_output_path = extract_info_path(completed.stdout, INFO_PREFIXES["output_path"])
    video_manifest_path = extract_info_path(completed.stdout, INFO_PREFIXES["video_manifest_path"])
    if not resolved_output_path.exists():
        raise ExperimentError(f"Expected output clip was not created: {resolved_output_path}")
    if not video_manifest_path.exists():
        raise ExperimentError(f"Expected video manifest was not created: {video_manifest_path}")

    contact_sheet_path = ensure_contact_sheet(
        resolved_output_path,
        ensure_parent(run_root / "contact_sheets" / f"{entry_slug}.png"),
    )
    video_manifest = read_json(video_manifest_path)
    duration_seconds = float(video_manifest.get("duration_seconds") or ffprobe_duration(resolved_output_path))
    metrics = parse_time_metrics(time_path)
    payload = {
        "phase": phase,
        "beat_id": beat.id,
        "beat_role": beat_spec.role,
        "archetype": beat_spec.archetype,
        "preset_id": beat.preset_id,
        "cue_start_seconds": beat.cue_start_seconds,
        "cue_end_seconds": beat.cue_end_seconds,
        "target_duration_seconds": beat.target_duration_seconds,
        "frames": beat.frames,
        "seed": seed,
        "variant_id": variant.id,
        "variant_label": variant.label,
        "pipeline": variant.pipeline,
        "model_repo": variant.model_repo,
        "backend_variant": variant.backend_variant,
        "prepared_backend_path": prepared_backend_path,
        "still_override_path": str(beat.still_override_path),
        "staged_path": staged_record["staged_path"],
        "stage_manifest_path": staged_record["stage_manifest_path"],
        "output_path": str(resolved_output_path),
        "video_manifest_path": str(video_manifest_path),
        "contact_sheet_path": str(contact_sheet_path),
        "stdout_log_path": str(stdout_path),
        "stderr_log_path": str(stderr_path),
        "time_metrics_path": str(time_path),
        "duration_seconds": duration_seconds,
        "time_metrics": metrics,
        "disposition": "pending",
        "review_note": "",
    }
    write_json(entry_path, payload)
    return payload


def list_entries(run_root: Path) -> list[dict[str, Any]]:
    entries_dir = run_root / "entries"
    if not entries_dir.exists():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted(entries_dir.glob("*.json")):
        entries.append(read_json(path))
    entries.sort(
        key=lambda item: (
            item.get("phase", ""),
            item.get("beat_role", ""),
            item.get("beat_id", ""),
            item.get("variant_id", ""),
            int(item.get("seed", 0)),
        )
    )
    return entries


def emit_summary(
    *,
    config: ExperimentConfig,
    run_root: Path,
    short_manifest_payload: dict[str, Any],
    winner_variant_id: str | None,
) -> None:
    entries = list_entries(run_root)
    summary_payload = {
        "experiment_id": config.experiment_id,
        "title": config.title,
        "created_at": utc_now().isoformat().replace("+00:00", "Z"),
        "config_path": str(run_root / "experiment_manifest.json"),
        "short_manifest_path": str(config.short_manifest_path),
        "short_id": short_manifest_payload.get("short_id", ""),
        "episode_id": short_manifest_payload.get("episode_id", ""),
        "run_root": str(run_root),
        "review_note_path": str(config.review_note_path),
        "winner_variant_id": winner_variant_id or "",
        "entries": entries,
    }
    write_json(run_root / "summary.json", summary_payload)

    lines = [
        f"# {config.title}",
        "",
        f"- `experiment_id`: `{config.experiment_id}`",
        f"- `short_manifest_path`: `{config.short_manifest_path}`",
        f"- `run_root`: `{run_root}`",
        f"- `review_note_path`: `{config.review_note_path}`",
        f"- `winner_variant_id`: `{winner_variant_id or 'pending'}`",
        "",
        "## Entries",
        "",
    ]
    if not entries:
        lines.append("No entries rendered yet.")
    else:
        for entry in entries:
            metrics = entry["time_metrics"]
            lines.extend(
                [
                    f"### {entry['phase']} / {entry['beat_id']} / {entry['variant_id']} / seed {entry['seed']}",
                    f"- `beat_role`: `{entry['beat_role']}`",
                    f"- `pipeline`: `{entry['pipeline']}`",
                    f"- `model_repo`: `{entry['model_repo']}`",
                    f"- `prepared_backend_path`: `{entry['prepared_backend_path']}`",
                    f"- `output_path`: `{entry['output_path']}`",
                    f"- `video_manifest_path`: `{entry['video_manifest_path']}`",
                    f"- `contact_sheet_path`: `{entry['contact_sheet_path']}`",
                    f"- `real_seconds`: `{metrics['real_seconds']}`",
                    f"- `max_resident_size_bytes`: `{metrics['max_resident_size_bytes']}`",
                    f"- `disposition`: `{entry.get('disposition', 'pending')}`",
                    "",
                ]
            )
    write_text(run_root / "summary.md", "\n".join(lines).rstrip() + "\n")


def write_experiment_manifest(
    *,
    config: ExperimentConfig,
    config_path: Path,
    run_root: Path,
    short_manifest_payload: dict[str, Any],
    winner_variant_id: str | None,
) -> None:
    payload = {
        "created_at": utc_now().isoformat().replace("+00:00", "Z"),
        "config_source_path": str(config_path),
        "experiment_id": config.experiment_id,
        "title": config.title,
        "short_manifest_path": str(config.short_manifest_path),
        "output_root": str(config.output_root),
        "review_note_path": str(config.review_note_path),
        "width": config.width,
        "height": config.height,
        "first_pass_seed": config.first_pass_seed,
        "second_pass_seed": config.second_pass_seed,
        "max_wall_clock_multiplier": config.max_wall_clock_multiplier,
        "beats": [asdict(item) for item in config.beats],
        "variants": [asdict(item) for item in config.variants],
        "winner_variant_id": winner_variant_id or "",
        "short_id": short_manifest_payload.get("short_id", ""),
        "episode_id": short_manifest_payload.get("episode_id", ""),
        "run_root": str(run_root),
    }
    write_json(run_root / "experiment_manifest.json", payload)


def winner_lookup(config: ExperimentConfig, winner_variant_id: str | None) -> VariantSpec | None:
    if not winner_variant_id:
        return None
    for variant in config.variants:
        if variant.id == winner_variant_id:
            return variant
    allowed = ", ".join(variant.id for variant in config.variants)
    raise ExperimentError(f"Unknown --winner {winner_variant_id!r}; expected one of: {allowed}")


def main() -> int:
    args = parse_args()
    repo_root = resolve_absolute(args.repo_root, label="--repo-root")
    config_path = Path(args.config).expanduser()
    if not config_path.is_absolute():
        config_path = (repo_root / config_path).resolve()
    config = load_config(config_path)
    selected_ids = {beat.id for beat in config.beats}
    short_beats, short_manifest_payload = load_short_beats(config.short_manifest_path, selected_ids)
    winner_variant = winner_lookup(config, args.winner)

    run_root = (
        resolve_absolute(args.run_root, label="--run-root")
        if args.run_root
        else (config.output_root / utc_stamp()).resolve()
    )
    run_root.mkdir(parents=True, exist_ok=True)

    write_experiment_manifest(
        config=config,
        config_path=config_path,
        run_root=run_root,
        short_manifest_payload=short_manifest_payload,
        winner_variant_id=winner_variant.id if winner_variant else None,
    )

    backend_payloads: dict[str, dict[str, Any]] = {}
    for variant in config.variants:
        if variant.backend_variant == "dev" or variant.id == "baseline":
            backend_payloads[variant.id] = ensure_backend_metadata(
                repo_root=repo_root,
                run_root=run_root,
                variant=variant,
            )

    staged_records: dict[str, dict[str, Any]] = {}
    for beat_spec in config.beats:
        staged_records[beat_spec.id] = stage_beat(
            repo_root=repo_root,
            run_root=run_root,
            beat=short_beats[beat_spec.id],
            experiment_width=config.width,
            experiment_height=config.height,
        )

    try:
        if not args.skip_first_pass:
            for beat_spec in config.beats:
                beat = short_beats[beat_spec.id]
                for variant in config.variants:
                    backend_payload = backend_payloads.get(variant.id)
                    if backend_payload is None:
                        backend_payload = ensure_backend_metadata(
                            repo_root=repo_root,
                            run_root=run_root,
                            variant=variant,
                        )
                        backend_payloads[variant.id] = backend_payload
                    render_variant(
                        repo_root=repo_root,
                        run_root=run_root,
                        beat_spec=beat_spec,
                        beat=beat,
                        variant=variant,
                        seed=config.first_pass_seed,
                        phase="first_pass",
                        experiment_width=config.width,
                        experiment_height=config.height,
                        prepared_backend_path=str(backend_payload["prepared_path"]),
                        staged_record=staged_records[beat_spec.id],
                    )

        if winner_variant is not None:
            backend_payload = backend_payloads.get(winner_variant.id)
            if backend_payload is None:
                backend_payload = ensure_backend_metadata(
                    repo_root=repo_root,
                    run_root=run_root,
                    variant=winner_variant,
                )
                backend_payloads[winner_variant.id] = backend_payload
            for beat_spec in config.beats:
                beat = short_beats[beat_spec.id]
                render_variant(
                    repo_root=repo_root,
                    run_root=run_root,
                    beat_spec=beat_spec,
                    beat=beat,
                    variant=winner_variant,
                    seed=config.second_pass_seed,
                    phase="second_pass",
                    experiment_width=config.width,
                    experiment_height=config.height,
                    prepared_backend_path=str(backend_payload["prepared_path"]),
                    staged_record=staged_records[beat_spec.id],
                )
    finally:
        emit_summary(
            config=config,
            run_root=run_root,
            short_manifest_payload=short_manifest_payload,
            winner_variant_id=winner_variant.id if winner_variant else None,
        )
    print(f"INFO  Experiment run root: {run_root}")
    print(f"INFO  Experiment summary: {run_root / 'summary.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExperimentError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        raise SystemExit(1)
