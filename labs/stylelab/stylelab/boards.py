from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .config import RuntimeConfig
from .io import read_json


def build_still_contact_sheet(runtime: RuntimeConfig, scene_paths: list[Path]) -> Path:
    thumbs: list[tuple[str, Image.Image]] = []
    for scene_path in scene_paths:
        scene = read_json(scene_path)
        scene_id = str(scene["id"])
        if not scene_id.startswith("scene_"):
            continue
        latest = scene.get("outputs", {}).get("lock") or scene.get("outputs", {}).get("final") or scene.get("outputs", {}).get("sketch") or {}
        image_path = str(latest.get("image_path", "")).strip()
        if not image_path:
            continue
        image = Image.open(image_path).convert("RGB")
        thumbs.append((scene_id, ImageOps.fit(image, (420, 720), method=Image.Resampling.LANCZOS)))

    if not thumbs:
        raise RuntimeError("No still renders available for board build.")

    columns = 2
    rows = (len(thumbs) + columns - 1) // columns
    tile_w, tile_h = 420, 760
    board = Image.new("RGB", (columns * tile_w + 80, rows * tile_h + 80), (236, 226, 208))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    for index, (scene_id, thumb) in enumerate(thumbs):
        row = index // columns
        col = index % columns
        x = 40 + (col * tile_w)
        y = 40 + (row * tile_h)
        board.paste(thumb, (x, y))
        draw.text((x, y + 726), scene_id, fill=(18, 27, 45), font=font)
    output_path = runtime.boards_root / "still_contact_sheet.png"
    board.save(output_path)
    return output_path


def build_motion_reel(runtime: RuntimeConfig, scene_paths: list[Path]) -> Path:
    clips: list[Path] = []
    for scene_path in scene_paths:
        scene = read_json(scene_path)
        motion_outputs = scene.get("outputs", {}).get("motion", {})
        chosen = motion_outputs.get("stillness_breathe") or motion_outputs.get("vertical_glide") or {}
        output_path = str(chosen.get("output_path", "")).strip()
        if output_path:
            path = Path(output_path).expanduser()
            if path.exists():
                clips.append(path)
    if not clips:
        raise RuntimeError("No motion clips available for board build.")
    reel_path = runtime.boards_root / "motion_reel.mp4"
    with tempfile.TemporaryDirectory(prefix="stylelab-reel-") as temp_dir:
        concat_file = Path(temp_dir) / "inputs.txt"
        concat_file.write_text("".join(f"file '{clip.as_posix()}'\n" for clip in clips), encoding="utf-8")
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(reel_path),
            ],
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
        raise RuntimeError(combined or "ffmpeg concat failed.")
    return reel_path
