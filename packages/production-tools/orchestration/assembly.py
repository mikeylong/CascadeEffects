from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orchestration.io import Context, path_exists

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
TARGET_FPS = 30
TARGET_PIX_FMT = "yuv420p"
TARGET_VIDEO_CODEC = "libx264"
TARGET_CRF = "18"
ALLOWED_ASSEMBLY_RENDERERS = {"ffmpeg"}
ALLOWED_ASSEMBLY_STRATEGIES = {"act_spine"}
ALLOWED_VIDEO_TRANSITIONS = {"cut", "xfade"}
ALLOWED_AUDIO_TRANSITIONS = {"cut", "acrossfade"}
ALLOWED_OVERLAY_BLEND_MODES = {"normal"}
MAX_OVERLAYS_PER_COMPOSITION = 3


@dataclass(frozen=True)
class AssemblyTransition:
    from_act: str
    to_act: str
    video: str = "cut"
    audio: str = "cut"
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class AssemblySource:
    act_id: str
    asset_id: str
    kind: str
    asset_path: Path
    duration_seconds: float
    source_still_id: str = ""
    fallback_still_path: Path | None = None


@dataclass(frozen=True)
class AssemblyOverlay:
    motion_asset_id: str
    asset_path: Path
    start_seconds: float
    duration_seconds: float
    x: float | None = None
    y: float | None = None
    scale: float = 1.0
    opacity: float = 1.0
    blend_mode: str = "normal"
    hold_last_frame: bool = False


@dataclass(frozen=True)
class AssemblyComposition:
    act_id: str
    base_asset_id: str
    overlays: tuple[AssemblyOverlay, ...]


@dataclass(frozen=True)
class AssemblyActPlan:
    act_id: str
    title: str
    estimated_seconds: int
    sources: tuple[AssemblySource, ...]


@dataclass(frozen=True)
class AssemblyPlan:
    renderer: str
    strategy: str
    output_path: Path
    acts: tuple[AssemblyActPlan, ...]
    transitions: tuple[AssemblyTransition, ...]
    compositions: tuple[AssemblyComposition, ...]
    missing_act_ids: tuple[str, ...]
    opening_source: AssemblySource | None = None
    opening_duration_seconds: float = 0.0


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _coerce_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _distribute_duration(total_seconds: int, item_count: int) -> list[int]:
    if item_count <= 0:
        return []
    budget = max(int(total_seconds), item_count)
    base = budget // item_count
    remainder = budget % item_count
    return [base + (1 if index < remainder else 0) for index in range(item_count)]


def _scene_lookup(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id", "")).strip(): item
        for item in manifest.get("scene_stills", {}).get("items", [])
        if str(item.get("id", "")).strip()
    }


def _motion_lookup(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id", "")).strip(): item
        for item in manifest.get("motion_assets", {}).get("items", [])
        if str(item.get("id", "")).strip()
    }


def resolve_assembly_output_path(context: Context, manifest: dict[str, Any]) -> Path:
    episode_info = context.episodes_repo.get_episode_info(str(manifest.get("id", "")).strip())
    if episode_info:
        return episode_info.directory / "final" / f"{episode_info.folder_name}.mp4"
    script_raw = str(manifest.get("script", {}).get("path", "")).strip()
    if script_raw:
        script_path = Path(script_raw).expanduser()
        return script_path.parent / "final" / f"{script_path.parent.name}.mp4"
    episode_folder = str(manifest.get("aliases", {}).get("episode_folder", manifest.get("id", ""))).strip()
    if not episode_folder:
        raise SystemExit("Assembly output path cannot be derived because episode_folder is missing.")
    episodes_root = Path(context.channel["paths"]["episodes_root"])
    return episodes_root / episode_folder / "final" / f"{episode_folder}.mp4"


def resolve_assembly_transitions(manifest: dict[str, Any]) -> tuple[AssemblyTransition, ...]:
    normalized: list[AssemblyTransition] = []
    for item in manifest.get("assembly", {}).get("transitions", []):
        if not isinstance(item, dict):
            continue
        normalized.append(
            AssemblyTransition(
                from_act=str(item.get("from_act", "")).strip(),
                to_act=str(item.get("to_act", "")).strip(),
                video=str(item.get("video", "cut")).strip() or "cut",
                audio=str(item.get("audio", "cut")).strip() or "cut",
                duration_seconds=_coerce_float(item.get("duration_seconds", 0.0), 0.0),
            )
        )
    return tuple(normalized)


def resolve_assembly_compositions(manifest: dict[str, Any]) -> tuple[AssemblyComposition, ...]:
    motion_lookup = _motion_lookup(manifest)
    normalized: list[AssemblyComposition] = []
    for item in manifest.get("assembly", {}).get("compositions", []):
        if not isinstance(item, dict):
            continue
        overlays: list[AssemblyOverlay] = []
        for overlay in item.get("overlays", []):
            if not isinstance(overlay, dict):
                continue
            motion_asset_id = str(overlay.get("motion_asset_id", "")).strip()
            if not motion_asset_id:
                continue
            motion_item = motion_lookup.get(motion_asset_id)
            output_path = str(motion_item.get("output_path", "")).strip() if motion_item else ""
            overlays.append(
                AssemblyOverlay(
                    motion_asset_id=motion_asset_id,
                    asset_path=Path(output_path).expanduser() if output_path else Path("."),
                    start_seconds=_coerce_float(overlay.get("start_seconds", 0.0), 0.0),
                    duration_seconds=_coerce_float(overlay.get("duration_seconds", 0.0), 0.0),
                    x=overlay.get("x") if isinstance(overlay.get("x"), (int, float)) else _coerce_float(overlay.get("x"), 0.0) if overlay.get("x") not in {None, ""} else None,
                    y=overlay.get("y") if isinstance(overlay.get("y"), (int, float)) else _coerce_float(overlay.get("y"), 0.0) if overlay.get("y") not in {None, ""} else None,
                    scale=max(0.01, _coerce_float(overlay.get("scale", 1.0), 1.0)),
                    opacity=min(1.0, max(0.0, _coerce_float(overlay.get("opacity", 1.0), 1.0))),
                    blend_mode=str(overlay.get("blend_mode", "normal")).strip() or "normal",
                    hold_last_frame=bool(overlay.get("hold_last_frame", False)),
                )
            )
        normalized.append(
            AssemblyComposition(
                act_id=str(item.get("act_id", "")).strip(),
                base_asset_id=str(item.get("base_asset_id", "")).strip(),
                overlays=tuple(overlays),
            )
        )
    return tuple(normalized)


def transition_for_boundary(manifest: dict[str, Any], from_act: str, to_act: str) -> AssemblyTransition:
    for transition in resolve_assembly_transitions(manifest):
        if transition.from_act == from_act and transition.to_act == to_act:
            return transition
    return AssemblyTransition(from_act=from_act, to_act=to_act)


def derive_act_spine(context: Context, manifest: dict[str, Any]) -> AssemblyPlan:
    assembly = manifest.get("assembly", {})
    renderer = str(assembly.get("renderer", "ffmpeg")).strip() or "ffmpeg"
    strategy = str(assembly.get("strategy", "act_spine")).strip() or "act_spine"
    scene_lookup = _scene_lookup(manifest)
    motion_lookup = _motion_lookup(manifest)
    compositions = resolve_assembly_compositions(manifest)
    opening_sequence = manifest.get("visual_research", {}).get("opening_sequence", {})
    opening_timing = manifest.get("visual_research", {}).get("_opening_timing", {})
    opening_scene_id = str(opening_sequence.get("planned_scene_id", "")).strip()
    opening_motion_id = str(opening_sequence.get("planned_motion_id", "")).strip()
    opening_act_id = str(opening_sequence.get("act_id", "")).strip()
    opening_duration_seconds = _coerce_float(opening_timing.get("opening_duration_seconds", 0.0), 0.0)
    opener_budget_seconds = max(1, round(opening_duration_seconds)) if opening_duration_seconds > 0 else 0
    opening_source: AssemblySource | None = None
    if opening_scene_id and opening_duration_seconds > 0:
        opening_scene = scene_lookup.get(opening_scene_id, {})
        opening_scene_asset = str(opening_scene.get("selected_asset", "")).strip()
        opening_scene_path = (
            Path(opening_scene_asset)
            if opening_scene_asset
            and str(opening_scene.get("review_status", "")).strip() == "approved"
            and path_exists(opening_scene_asset)
            else None
        )
        opening_motion = motion_lookup.get(opening_motion_id, {}) if opening_motion_id else {}
        opening_motion_output = str(opening_motion.get("output_path", "")).strip()
        if (
            opening_motion
            and str(opening_motion.get("status", "")).strip() == "done"
            and opening_motion_output
            and path_exists(opening_motion_output)
        ):
            opening_source = AssemblySource(
                act_id="opening",
                asset_id=opening_motion_id,
                kind="motion",
                asset_path=Path(opening_motion_output),
                duration_seconds=opening_duration_seconds,
                source_still_id=opening_scene_id,
                fallback_still_path=opening_scene_path,
            )
        elif opening_scene_path is not None:
            opening_source = AssemblySource(
                act_id="opening",
                asset_id=opening_scene_id,
                kind="scene",
                asset_path=opening_scene_path,
                duration_seconds=opening_duration_seconds,
            )
    acts: list[AssemblyActPlan] = []
    missing_act_ids: list[str] = []

    for act in manifest.get("visual_research", {}).get("acts", []):
        act_id = str(act.get("id", "")).strip() or "unknown"
        title = str(act.get("title", "")).strip() or act_id
        estimated_seconds = max(1, _coerce_int(act.get("estimated_seconds", 0), 1))
        if opening_source is not None and act_id == opening_act_id and opener_budget_seconds:
            estimated_seconds = max(1, estimated_seconds - opener_budget_seconds)
        candidate_sources: list[AssemblySource] = []

        for motion_id in _normalize_string_list(act.get("planned_motion_ids")):
            motion_item = motion_lookup.get(motion_id)
            if not motion_item:
                continue
            output_path = str(motion_item.get("output_path", "")).strip()
            if str(motion_item.get("status", "")) != "done" or not output_path or not path_exists(output_path):
                continue
            source_still_id = str(motion_item.get("source_still_id", "")).strip()
            source_still = scene_lookup.get(source_still_id, {})
            fallback_still_path: Path | None = None
            selected_asset = str(source_still.get("selected_asset", "")).strip()
            if (
                selected_asset
                and str(source_still.get("review_status", "")).strip() == "approved"
                and path_exists(selected_asset)
            ):
                fallback_still_path = Path(selected_asset)
            candidate_sources.append(
                AssemblySource(
                    act_id=act_id,
                    asset_id=motion_id,
                    kind="motion",
                    asset_path=Path(output_path),
                    duration_seconds=0,
                    source_still_id=source_still_id,
                    fallback_still_path=fallback_still_path,
                )
            )

        for scene_id in _normalize_string_list(act.get("planned_scene_ids")):
            scene_item = scene_lookup.get(scene_id)
            if not scene_item:
                continue
            selected_asset = str(scene_item.get("selected_asset", "")).strip()
            if (
                str(scene_item.get("review_status", "")).strip() == "approved"
                and selected_asset
                and path_exists(selected_asset)
            ):
                candidate_sources.append(
                    AssemblySource(
                        act_id=act_id,
                        asset_id=scene_id,
                        kind="scene",
                        asset_path=Path(selected_asset),
                        duration_seconds=0,
                    )
                )

        if not candidate_sources:
            acts.append(AssemblyActPlan(act_id=act_id, title=title, estimated_seconds=estimated_seconds, sources=()))
            missing_act_ids.append(act_id)
            continue

        durations = _distribute_duration(estimated_seconds, len(candidate_sources))
        assigned_sources = tuple(
            AssemblySource(
                act_id=source.act_id,
                asset_id=source.asset_id,
                kind=source.kind,
                asset_path=source.asset_path,
                duration_seconds=duration_seconds,
                source_still_id=source.source_still_id,
                fallback_still_path=source.fallback_still_path,
            )
            for source, duration_seconds in zip(candidate_sources, durations, strict=True)
        )
        acts.append(AssemblyActPlan(act_id=act_id, title=title, estimated_seconds=estimated_seconds, sources=assigned_sources))

    valid_source_keys = {
        (act.act_id, source.asset_id)
        for act in acts
        for source in act.sources
    }
    seen_compositions: set[tuple[str, str]] = set()
    for composition in compositions:
        key = (composition.act_id, composition.base_asset_id)
        if key in seen_compositions:
            raise SystemExit(f"Duplicate assembly composition declared for `{composition.act_id}` / `{composition.base_asset_id}`.")
        seen_compositions.add(key)
        if key not in valid_source_keys:
            raise SystemExit(
                f"Assembly composition base `{composition.base_asset_id}` is not part of act `{composition.act_id}`."
            )
        if len(composition.overlays) > MAX_OVERLAYS_PER_COMPOSITION:
            raise SystemExit(
                f"Assembly composition `{composition.base_asset_id}` exceeds the v1 overlay limit of {MAX_OVERLAYS_PER_COMPOSITION}."
            )
        for overlay in composition.overlays:
            motion_item = motion_lookup.get(overlay.motion_asset_id)
            if not motion_item or str(motion_item.get("status", "")).strip() != "done":
                raise SystemExit(f"Assembly overlay `{overlay.motion_asset_id}` must reference a done motion item.")
            if not str(motion_item.get("output_path", "")).strip() or not overlay.asset_path.exists():
                raise SystemExit(f"Assembly overlay `{overlay.motion_asset_id}` is missing its output file.")
            if overlay.duration_seconds <= 0:
                raise SystemExit(f"Assembly overlay `{overlay.motion_asset_id}` must declare a positive duration_seconds.")
            if overlay.start_seconds < 0:
                raise SystemExit(f"Assembly overlay `{overlay.motion_asset_id}` cannot start before 0s.")
            if overlay.blend_mode not in ALLOWED_OVERLAY_BLEND_MODES:
                raise SystemExit(
                    f"Assembly overlay `{overlay.motion_asset_id}` uses unsupported blend_mode `{overlay.blend_mode}`."
                )

    return AssemblyPlan(
        renderer=renderer,
        strategy=strategy,
        output_path=resolve_assembly_output_path(context, manifest),
        acts=tuple(acts),
        transitions=resolve_assembly_transitions(manifest),
        compositions=compositions,
        missing_act_ids=tuple(missing_act_ids),
        opening_source=opening_source,
        opening_duration_seconds=opening_duration_seconds,
    )


def _run_checked_command(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
    if result.returncode != 0:
        raise SystemExit(combined or f"Command failed with exit code {result.returncode}: {' '.join(args)}")
    return combined


def _ffmpeg_path() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required for `ce orchestrate assemble`.")
    return ffmpeg


def _ffprobe_path() -> str:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SystemExit("ffprobe is required for `ce orchestrate assemble`.")
    return ffprobe


def probe_media_duration_seconds(path: Path) -> float:
    output = _run_checked_command(
        [
            _ffprobe_path(),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    try:
        return float(output.strip())
    except ValueError as exc:
        raise SystemExit(f"Could not determine media duration for `{path}`.") from exc


def _house_video_filter() -> str:
    return (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,fps={TARGET_FPS},format={TARGET_PIX_FMT}"
    )


def _overlay_intermediate_filter(scale: float) -> str:
    return (
        f"scale=iw*{scale:.6f}:ih*{scale:.6f}:flags=lanczos,"
        f"fps={TARGET_FPS},format=rgba"
    )


def _write_ffconcat(path: Path, clips: list[Path]) -> None:
    lines = ["ffconcat version 1.0"]
    for clip in clips:
        escaped = str(clip).replace("'", r"'\''")
        lines.append(f"file '{escaped}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _copy_or_concat(clips: list[Path], output_path: Path) -> Path:
    if not clips:
        raise SystemExit("Assembly timeline is empty.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 1:
        if clips[0].resolve() != output_path.resolve():
            shutil.copy2(clips[0], output_path)
        return output_path
    timeline_path = output_path.with_suffix(".ffconcat")
    _write_ffconcat(timeline_path, clips)
    _run_checked_command(
        [
            _ffmpeg_path(),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(timeline_path),
            "-an",
            "-c:v",
            "copy",
            str(output_path),
        ]
    )
    return output_path


def _render_still_segment(source_path: Path, duration_seconds: float, output_path: Path) -> Path:
    _run_checked_command(
        [
            _ffmpeg_path(),
            "-y",
            "-framerate",
            str(TARGET_FPS),
            "-loop",
            "1",
            "-i",
            str(source_path),
            "-t",
            f"{duration_seconds:.3f}",
            "-vf",
            _house_video_filter(),
            "-an",
            "-c:v",
            TARGET_VIDEO_CODEC,
            "-crf",
            TARGET_CRF,
            "-pix_fmt",
            TARGET_PIX_FMT,
            str(output_path),
        ]
    )
    return output_path


def _render_motion_segment(source_path: Path, duration_seconds: float, output_path: Path) -> Path:
    _run_checked_command(
        [
            _ffmpeg_path(),
            "-y",
            "-i",
            str(source_path),
            "-t",
            f"{duration_seconds:.3f}",
            "-vf",
            _house_video_filter(),
            "-an",
            "-c:v",
            TARGET_VIDEO_CODEC,
            "-crf",
            TARGET_CRF,
            "-pix_fmt",
            TARGET_PIX_FMT,
            str(output_path),
        ]
    )
    return output_path


def _render_last_frame_hold(source_path: Path, duration_seconds: float, output_path: Path) -> Path:
    frame_path = output_path.with_suffix(".png")
    _run_checked_command(
        [
            _ffmpeg_path(),
            "-y",
            "-sseof",
            "-0.04",
            "-i",
            str(source_path),
            "-frames:v",
            "1",
            str(frame_path),
        ]
    )
    return _render_still_segment(frame_path, max(1.0, round(duration_seconds)), output_path)


def _render_source_segments(temp_root: Path, source: AssemblySource, index: int) -> list[Path]:
    primary_output = temp_root / f"segment_{index:03d}.mp4"
    if source.kind == "scene":
        return [_render_still_segment(source.asset_path, source.duration_seconds, primary_output)]

    clip_duration = probe_media_duration_seconds(source.asset_path)
    target_duration = float(source.duration_seconds)
    if clip_duration >= target_duration:
        return [_render_motion_segment(source.asset_path, target_duration, primary_output)]

    rendered: list[Path] = []
    rendered.append(_render_motion_segment(source.asset_path, clip_duration, primary_output))
    remainder = max(0.0, target_duration - clip_duration)
    if remainder <= 0:
        return rendered
    filler_output = temp_root / f"segment_{index:03d}_fill.mp4"
    if source.fallback_still_path and path_exists(source.fallback_still_path):
        rendered.append(_render_still_segment(source.fallback_still_path, max(1, round(remainder)), filler_output))
    else:
        rendered.append(_render_last_frame_hold(source.asset_path, remainder, filler_output))
    return rendered


def _normalize_overlay_intermediate(
    source_path: Path,
    duration_seconds: float,
    output_path: Path,
    *,
    scale: float = 1.0,
    hold_last_frame: bool = False,
) -> Path:
    clip_duration = probe_media_duration_seconds(source_path)
    if clip_duration + 1e-6 < duration_seconds and not hold_last_frame:
        raise SystemExit(
            f"Assembly overlay `{source_path.name}` is shorter than its requested window "
            f"({clip_duration:.3f}s < {duration_seconds:.3f}s)."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        _ffmpeg_path(),
        "-y",
        "-i",
        str(source_path),
        "-vf",
        _overlay_intermediate_filter(scale),
    ]
    if hold_last_frame and clip_duration + 1e-6 < duration_seconds:
        command[-1] = f"{command[-1]},tpad=stop_mode=clone:stop_duration={max(0.0, duration_seconds - clip_duration):.3f}"
    command.extend(
        [
            "-t",
            f"{duration_seconds:.3f}",
            "-an",
            "-c:v",
            "qtrle",
            "-pix_fmt",
            "argb",
            str(output_path),
        ]
    )
    _run_checked_command(command)
    return output_path


def _compose_base_fx_clip(
    temp_root: Path,
    base_clip: Path,
    shot_duration: float,
    composition: AssemblyComposition,
    index: int,
) -> Path:
    for overlay in composition.overlays:
        if overlay.start_seconds + overlay.duration_seconds > shot_duration + 1e-6:
            raise SystemExit(
                f"Assembly overlay `{overlay.motion_asset_id}` exceeds the shot duration for `{composition.base_asset_id}`."
            )
    output_path = temp_root / f"composite_{index:03d}.mp4"
    command = [
        _ffmpeg_path(),
        "-y",
        "-i",
        str(base_clip),
    ]
    overlay_inputs: list[Path] = []
    for overlay_index, overlay in enumerate(composition.overlays, start=1):
        overlay_output = temp_root / f"overlay_{index:03d}_{overlay_index:02d}.mov"
        overlay_inputs.append(
            _normalize_overlay_intermediate(
                overlay.asset_path,
                overlay.duration_seconds,
                overlay_output,
                scale=overlay.scale,
                hold_last_frame=overlay.hold_last_frame,
            )
        )
        command.extend(["-i", str(overlay_output)])

    filter_parts: list[str] = ["[0:v]format=rgba[base0]"]
    current_label = "base0"
    for overlay_index, overlay in enumerate(composition.overlays, start=1):
        input_label = f"{overlay_index}:v"
        timed_label = f"ov{overlay_index}pts"
        next_label = f"base{overlay_index}"
        x_expr = f"{overlay.x:.3f}" if overlay.x is not None else "(main_w-overlay_w)/2"
        y_expr = f"{overlay.y:.3f}" if overlay.y is not None else "(main_h-overlay_h)/2"
        filter_parts.append(f"[{input_label}]setpts=PTS+{overlay.start_seconds:.6f}/TB[{timed_label}]")
        overlay_input_label = timed_label
        if overlay.opacity < 1.0:
            opacity_label = f"ov{overlay_index}a"
            filter_parts.append(
                f"[{timed_label}]format=rgba,colorchannelmixer=aa={overlay.opacity:.6f}[{opacity_label}]"
            )
            overlay_input_label = opacity_label
        overlay_chain = f"[{current_label}][{overlay_input_label}]overlay=x={x_expr}:y={y_expr}:enable='between(t,{overlay.start_seconds:.3f},{(overlay.start_seconds + overlay.duration_seconds):.3f})'"
        filter_parts.append(f"{overlay_chain}[{next_label}]")
        current_label = next_label
    filter_parts.append(f"[{current_label}]format={TARGET_PIX_FMT}[outv]")
    command.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[outv]",
            "-an",
            "-c:v",
            TARGET_VIDEO_CODEC,
            "-crf",
            TARGET_CRF,
            "-pix_fmt",
            TARGET_PIX_FMT,
            str(output_path),
        ]
    )
    _run_checked_command(command)
    return output_path


def _render_source_clip(
    temp_root: Path,
    source: AssemblySource,
    index: int,
    composition_lookup: dict[tuple[str, str], AssemblyComposition],
) -> Path:
    source_segments = _render_source_segments(temp_root, source, index)
    base_output = temp_root / f"source_{index:03d}.mp4"
    base_clip = _copy_or_concat(source_segments, base_output)
    composition = composition_lookup.get((source.act_id, source.asset_id))
    if composition is None or not composition.overlays:
        return base_clip
    return _compose_base_fx_clip(temp_root, base_clip, float(source.duration_seconds), composition, index)


def _render_act_clip(
    temp_root: Path,
    act: AssemblyActPlan,
    act_index: int,
    composition_lookup: dict[tuple[str, str], AssemblyComposition],
) -> Path:
    clips: list[Path] = []
    for source_index, source in enumerate(act.sources):
        segment_index = (act_index * 100) + source_index
        clips.append(_render_source_clip(temp_root, source, segment_index, composition_lookup))
    act_output = temp_root / f"act_{act_index:03d}.mp4"
    return _copy_or_concat(clips, act_output)


def _apply_xfade(current_clip: Path, next_clip: Path, duration_seconds: float, output_path: Path) -> Path:
    current_duration = probe_media_duration_seconds(current_clip)
    next_duration = probe_media_duration_seconds(next_clip)
    if duration_seconds <= 0:
        raise SystemExit("Assembly xfade duration must be greater than zero.")
    if duration_seconds >= current_duration or duration_seconds >= next_duration:
        raise SystemExit(
            f"Assembly xfade duration {duration_seconds:.3f}s is too long for `{current_clip.name}` and `{next_clip.name}`."
        )
    offset = current_duration - duration_seconds
    _run_checked_command(
        [
            _ffmpeg_path(),
            "-y",
            "-i",
            str(current_clip),
            "-i",
            str(next_clip),
            "-filter_complex",
            f"[0:v][1:v]xfade=transition=fade:duration={duration_seconds:.3f}:offset={offset:.3f},format={TARGET_PIX_FMT}",
            "-an",
            "-c:v",
            TARGET_VIDEO_CODEC,
            "-crf",
            TARGET_CRF,
            "-pix_fmt",
            TARGET_PIX_FMT,
            str(output_path),
        ]
    )
    return output_path


def _build_video_timeline(temp_root: Path, plan: AssemblyPlan, act_clips: list[Path]) -> Path:
    if not act_clips:
        raise SystemExit("Assembly plan produced no act clips.")
    transition_lookup = {(item.from_act, item.to_act): item for item in plan.transitions}
    current_clip = act_clips[0]
    current_act = plan.acts[0]
    for index, next_clip in enumerate(act_clips[1:], start=1):
        next_act = plan.acts[index]
        transition = transition_lookup.get((current_act.act_id, next_act.act_id), AssemblyTransition(current_act.act_id, next_act.act_id))
        merged_output = temp_root / f"timeline_{index:03d}.mp4"
        if transition.video == "xfade":
            current_clip = _apply_xfade(current_clip, next_clip, transition.duration_seconds, merged_output)
        else:
            current_clip = _copy_or_concat([current_clip, next_clip], merged_output)
        current_act = next_act
    return current_clip


def _mux_master_audio(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run_checked_command(
        [
            _ffmpeg_path(),
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-filter_complex",
            "[1:a]apad[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output_path),
        ]
    )
    return output_path


def assemble_episode_cut(context: Context, manifest: dict[str, Any]) -> Path:
    plan = derive_act_spine(context, manifest)
    if plan.renderer not in ALLOWED_ASSEMBLY_RENDERERS:
        raise SystemExit(f"Unsupported assembly renderer `{plan.renderer}`.")
    if plan.strategy not in ALLOWED_ASSEMBLY_STRATEGIES:
        raise SystemExit(f"Unsupported assembly strategy `{plan.strategy}`.")
    if plan.missing_act_ids:
        raise SystemExit(
            "Assembly requires approved scene or motion coverage for every act. Missing: "
            + ", ".join(plan.missing_act_ids)
        )
    audio_path = Path(str(manifest.get("audio", {}).get("master_path", "")).strip())
    if not audio_path.exists():
        raise SystemExit(f"Assembly audio master is missing: {audio_path}")
    with tempfile.TemporaryDirectory(prefix=f"ce-assembly-{manifest.get('id', 'episode')}-") as temp_dir:
        temp_root = Path(temp_dir)
        composition_lookup = {(item.act_id, item.base_asset_id): item for item in plan.compositions}
        act_clips = [_render_act_clip(temp_root, act, index, composition_lookup) for index, act in enumerate(plan.acts, start=1)]
        video_timeline = _build_video_timeline(temp_root, plan, act_clips)
        if plan.opening_source is not None and plan.opening_duration_seconds > 0:
            opening_clip = _render_source_clip(temp_root, plan.opening_source, 0, composition_lookup)
            video_timeline = _copy_or_concat([opening_clip, video_timeline], temp_root / "timeline_opening.mp4")
        return _mux_master_audio(video_timeline, audio_path, plan.output_path)


__all__ = [
    "ALLOWED_ASSEMBLY_RENDERERS",
    "ALLOWED_ASSEMBLY_STRATEGIES",
    "ALLOWED_AUDIO_TRANSITIONS",
    "ALLOWED_VIDEO_TRANSITIONS",
    "AssemblyActPlan",
    "AssemblyComposition",
    "AssemblyOverlay",
    "AssemblyPlan",
    "AssemblySource",
    "AssemblyTransition",
    "assemble_episode_cut",
    "derive_act_spine",
    "probe_media_duration_seconds",
    "resolve_assembly_output_path",
    "resolve_assembly_compositions",
    "resolve_assembly_transitions",
    "transition_for_boundary",
]
