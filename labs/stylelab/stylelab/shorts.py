from __future__ import annotations

import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

from .config import RuntimeConfig
from .io import timestamp_slug, write_json
from .manifests import load_scene, scene_path_for_id
from .motion import render_motion
from .rendering import render_still


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
        raise RuntimeError(combined or f"Command failed: {' '.join(command)}")


def _audio_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def _existing_still(scene: dict[str, Any], *, mode: str) -> Path | None:
    payload = scene.get("outputs", {}).get(mode, {})
    image_path = str(payload.get("image_path", "")).strip()
    if not image_path:
        return None
    path = Path(image_path).expanduser()
    if path.exists():
        return path
    return None


def _existing_motion(scene: dict[str, Any], *, preset: str, target_duration_seconds: float) -> Path | None:
    payload = scene.get("outputs", {}).get("motion", {}).get(preset, {})
    output_path = str(payload.get("output_path", "")).strip()
    if not output_path:
        return None
    path = Path(output_path).expanduser()
    actual_duration = float(payload.get("target_duration_seconds", payload.get("duration_seconds", 0.0)) or 0.0)
    if path.exists() and abs(actual_duration - target_duration_seconds) <= 0.05:
        return path
    return None


def _render_still_clip(short_dir: Path, beat_id: str, image_path: Path, duration_seconds: float) -> Path:
    output_path = short_dir / "clips" / f"{beat_id}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-t",
            f"{duration_seconds:.3f}",
            "-i",
            str(image_path),
            "-r",
            "24",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    return output_path


def build_short(
    runtime: RuntimeConfig,
    short_path: Path,
    short_manifest: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    timestamp = timestamp_slug()
    short_id = str(short_manifest["id"])
    output_dir = runtime.exports_root / "shorts" / short_id
    output_dir.mkdir(parents=True, exist_ok=True)
    assembled_path = output_dir / f"{timestamp}__picture.mp4"
    final_path = output_dir / f"{timestamp}__proof.mp4"
    manifest_path = output_dir / f"{timestamp}__proof.json"
    audio_path = Path(str(short_manifest["audio_path"])).expanduser()
    transcript_path = Path(str(short_manifest["transcript_path"])).expanduser()
    clip_payloads: list[dict[str, Any]] = []
    concat_inputs: list[Path] = []

    for beat in short_manifest["beats"]:
        beat_id = str(beat["id"])
        scene_path = scene_path_for_id(runtime.scenes_root, str(beat["scene_id"]))
        scene = load_scene(scene_path)
        profile = profiles[scene["style_profile"]]
        clip_duration = float(beat["clip_end_seconds"]) - float(beat["clip_start_seconds"])
        if abs(float(scene["target_duration_seconds"]) - clip_duration) > 0.05:
            raise RuntimeError(
                f"Scene `{scene['id']}` target_duration_seconds ({scene['target_duration_seconds']}) does not match short beat `{beat_id}` clip duration ({clip_duration:.3f})."
            )

        if beat["render_as"] == "motion":
            clip_path = _existing_motion(scene, preset=str(scene["motion_preset"]), target_duration_seconds=clip_duration)
            if clip_path is None:
                motion_result = render_motion(runtime, scene_path, scene, profile, preset=str(scene["motion_preset"]))
                clip_path = motion_result.output_path
            concat_inputs.append(clip_path)
        else:
            still_path = _existing_still(scene, mode="lock")
            if still_path is None:
                still_result = render_still(runtime, scene_path, scene, profile, mode="lock")
                still_path = still_result.image_path
            clip_path = _render_still_clip(output_dir, beat_id, still_path, clip_duration)
            concat_inputs.append(clip_path)

        clip_payloads.append(
            {
                "id": beat_id,
                "scene_id": beat["scene_id"],
                "render_as": beat["render_as"],
                "clip_start_seconds": beat["clip_start_seconds"],
                "clip_end_seconds": beat["clip_end_seconds"],
                "cue_start_seconds": beat["cue_start_seconds"],
                "cue_end_seconds": beat["cue_end_seconds"],
                "narration_text": beat["narration_text"],
                "clip_path": str(clip_path),
            }
        )

    with tempfile.TemporaryDirectory(prefix="stylelab-short-build-") as temp_dir:
        concat_path = Path(temp_dir) / "inputs.txt"
        concat_path.write_text("".join(f"file '{clip.as_posix()}'\n" for clip in concat_inputs), encoding="utf-8")
        _run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_path),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(assembled_path),
            ]
        )
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(assembled_path),
                "-i",
                str(audio_path),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(final_path),
            ]
        )

    packaging_scene_path = scene_path_for_id(runtime.scenes_root, str(short_manifest["packaging_frame_id"]))
    packaging_scene = load_scene(packaging_scene_path)
    packaging_profile = profiles[packaging_scene["style_profile"]]
    packaging_frame_path = _existing_still(packaging_scene, mode="lock")
    if packaging_frame_path is None:
        packaging_frame_path = render_still(runtime, packaging_scene_path, packaging_scene, packaging_profile, mode="lock").image_path

    payload = {
        "short_id": short_id,
        "title": short_manifest["title"],
        "audio_path": str(audio_path),
        "audio_duration_seconds": round(_audio_duration_seconds(audio_path), 3),
        "transcript_path": str(transcript_path),
        "packaging_frame_id": short_manifest["packaging_frame_id"],
        "packaging_frame_path": str(packaging_frame_path),
        "picture_path": str(assembled_path),
        "output_path": str(final_path),
        "beats": clip_payloads,
        "generated_at": timestamp,
    }
    write_json(manifest_path, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload
