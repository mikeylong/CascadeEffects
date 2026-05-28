from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from .config import RuntimeConfig
from .io import timestamp_slug, write_json
from .rendering import render_scene_image, render_still


@dataclass(frozen=True)
class MotionRenderResult:
    output_path: Path
    manifest_path: Path
    poster_path: Path
    still_path: Path


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
        raise RuntimeError(combined or f"Command failed: {' '.join(command)}")


def _latest_still_path(scene: dict[str, Any]) -> Path | None:
    for mode in ("lock", "final", "sketch"):
        output = scene.get("outputs", {}).get(mode, {})
        image_path = str(output.get("image_path", "")).strip()
        if image_path:
            path = Path(image_path).expanduser()
            if path.exists():
                return path
    return None


def _scene_duration_seconds(scene: dict[str, Any]) -> float:
    return max(1.0 / 24.0, float(scene.get("target_duration_seconds", 5.0)))


def render_motion(
    runtime: RuntimeConfig,
    scene_path: Path,
    scene: dict[str, Any],
    profile: dict[str, Any],
    *,
    preset: str,
) -> MotionRenderResult:
    latest_still = _latest_still_path(scene)
    if latest_still is None:
        render_still(runtime, scene_path, scene, profile, mode="final")
        latest_still = _latest_still_path(scene)
    if latest_still is None:
        raise RuntimeError(f"Could not resolve a still render for `{scene['id']}`.")

    timestamp = timestamp_slug()
    scene_id = scene["id"]
    output_dir = runtime.exports_root / scene_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{timestamp}__{preset}.mp4"
    manifest_path = output_dir / f"{timestamp}__{preset}.json"
    poster_path = output_dir / f"{timestamp}__{preset}.poster.png"
    still_path = output_dir / f"{timestamp}__{preset}.still.png"

    fps = 24
    duration_seconds = _scene_duration_seconds(scene)
    frames = max(1, round(duration_seconds * fps))
    actual_duration_seconds = frames / float(fps)

    with tempfile.TemporaryDirectory(prefix="stylelab-motion-frames-") as temp_dir:
        temp_root = Path(temp_dir)
        for index in range(frames):
            progress = index / max(frames - 1, 1)
            frame = render_scene_image(scene, profile, mode="lock", time_progress=progress, motion_preset=preset)
            frame_path = temp_root / f"frame_{index:04d}.png"
            frame.save(frame_path)
            if index == 0:
                frame.save(poster_path)
            if index == frames - 1:
                frame.save(still_path)

        _run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(temp_root / "frame_%04d.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )

    manifest = {
        "scene_id": scene_id,
        "style_profile": scene["style_profile"],
        "source_refs": scene["source_refs"],
        "selected_seed": scene["selected_seed"],
        "render_size": scene["final_size"],
        "final_size": scene["final_size"],
        "target_duration_seconds": duration_seconds,
        "duration_seconds": actual_duration_seconds,
        "fps": fps,
        "output_path": str(output_path),
        "poster_path": str(poster_path),
        "still_path": str(still_path),
        "model_family": "stylelab_painterly_motion_v1",
        "motion_preset": preset,
        "beat_id": scene["beat_id"],
        "historical_anchor": scene["historical_anchor"],
        "surreal_breach": scene["surreal_breach"],
        "caption_safe_zone": scene["caption_safe_zone"],
        "source_still_path": str(latest_still),
        "generated_at": timestamp,
    }
    write_json(manifest_path, manifest)
    scene.setdefault("outputs", {}).setdefault("motion", {})
    scene["outputs"]["motion"][preset] = {
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
        "poster_path": str(poster_path),
        "still_path": str(still_path),
        "duration_seconds": actual_duration_seconds,
        "target_duration_seconds": duration_seconds,
        "fps": fps,
        "generated_at": timestamp,
    }
    write_json(scene_path, scene)
    return MotionRenderResult(output_path=output_path, manifest_path=manifest_path, poster_path=poster_path, still_path=still_path)
