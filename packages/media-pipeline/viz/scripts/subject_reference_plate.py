#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SubjectReferencePlateError(RuntimeError):
    pass


PLATE_SCHEMA_VERSION = 1
BUILD_SCHEMA_VERSION = 5
DEFAULT_CANVAS_SIZE = [1024, 1792]
DEFAULT_BACKGROUND_MODE = "neutral_matte"
VALID_BACKGROUND_MODES = {"neutral_matte", "neutral_matte_knockout"}
TOP_UI_BAND = [0.0, 0.0, 1.0, 0.12]
SUBTITLE_BAND = [0.08, 0.74, 0.92, 0.96]
REQUIRED_PLATE_FIELDS = {
    "plate_id",
    "source_id",
    "source_image_path",
    "crop_box",
    "subject_box",
    "placement_box",
    "canvas_size",
    "background_mode",
    "allow_humans",
    "notes",
}
LOCKED_NO_HUMAN_EPISODES = {"challenger"}
NEUTRAL_MATTE_RGB = (236, 236, 232)
PALETTE_NEUTRAL_DARK_RGB = (44, 52, 64)
PALETTE_NEUTRAL_LIGHT_RGB = (220, 223, 228)
PALETTE_ACCENT_DARK_RGB = (108, 22, 22)
PALETTE_ACCENT_LIGHT_RGB = (224, 56, 54)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def plate_root_for_episode(references_root: Path, episode_id: str) -> Path:
    return references_root / "episodes" / episode_id / "subject_reference_plates"


def manifests_dir_for_episode(references_root: Path, episode_id: str) -> Path:
    return plate_root_for_episode(references_root, episode_id) / "manifests"


def generated_dir_for_episode(references_root: Path, episode_id: str) -> Path:
    return plate_root_for_episode(references_root, episode_id) / "generated"


def load_episode_manifest_paths(references_root: Path, episode_id: str) -> list[Path]:
    manifests_dir = manifests_dir_for_episode(references_root, episode_id)
    if not manifests_dir.exists():
        raise SubjectReferencePlateError(f"Missing subject-reference plate manifests directory: {manifests_dir}")
    paths = sorted(manifests_dir.glob("*.json"))
    if not paths:
        raise SubjectReferencePlateError(f"No subject-reference plate manifests were found in {manifests_dir}")
    return paths


def normalize_box(label: str, value: Any, *, path: Path) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        raise SubjectReferencePlateError(f"{path}: {label} must be a four-item normalized box.")
    try:
        left, top, right, bottom = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise SubjectReferencePlateError(f"{path}: {label} must contain numeric values.") from exc
    for number in (left, top, right, bottom):
        if number < 0.0 or number > 1.0:
            raise SubjectReferencePlateError(f"{path}: {label} values must stay within 0.0-1.0.")
    if right <= left or bottom <= top:
        raise SubjectReferencePlateError(f"{path}: {label} must describe a positive-area box.")
    return [left, top, right, bottom]


def normalize_optional_box(label: str, value: Any, *, path: Path) -> list[float] | None:
    if value is None:
        return None
    return normalize_box(label, value, path=path)


def normalize_optional_box_list(label: str, value: Any, *, path: Path) -> list[list[float]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise SubjectReferencePlateError(f"{path}: {label} must be a list of normalized boxes.")
    normalized: list[list[float]] = []
    for index, item in enumerate(value):
        normalized.append(normalize_box(f"{label}[{index}]", item, path=path))
    return normalized


def normalize_optional_path(label: str, value: Any, *, path: Path) -> Path | None:
    if value is None:
        return None
    raw_value = str(value).strip()
    if not raw_value:
        return None
    resolved = Path(raw_value).expanduser().resolve()
    if not resolved.exists():
        raise SubjectReferencePlateError(f"{path}: {label} was not found: {resolved}")
    return resolved


def box_area(box: list[float]) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def boxes_overlap(first: list[float], second: list[float]) -> bool:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    return right > left and bottom > top


def source_inventory_path_for_source_image(source_image_path: Path) -> Path:
    research_assets_root = source_image_path.parent
    if research_assets_root.name != "research_assets":
        raise SubjectReferencePlateError(
            f"{source_image_path}: source_image_path must live under a visual_research/research_assets directory."
        )
    return research_assets_root.parent / "source_inventory.json"


def load_source_inventory_entry(source_id: str, source_image_path: Path) -> dict[str, Any]:
    try:
        inventory_path = source_inventory_path_for_source_image(source_image_path)
    except SubjectReferencePlateError:
        return {
            "source_id": source_id,
            "raw_asset_path": str(source_image_path.resolve()),
            "candidate_label": source_image_path.stem.replace("_", " ").title(),
            "candidate_role": "local_subject_reference",
            "source_origin": "local_reference_lane",
        }
    if not inventory_path.exists():
        raise SubjectReferencePlateError(f"Missing source inventory: {inventory_path}")
    payload = read_json(inventory_path)
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise SubjectReferencePlateError(f"{inventory_path}: sources must be a list.")
    for entry in sources:
        if isinstance(entry, dict) and str(entry.get("source_id", "")).strip() == source_id:
            raw_asset_path = Path(str(entry.get("raw_asset_path", "")).strip()).expanduser().resolve()
            if raw_asset_path != source_image_path.resolve():
                raise SubjectReferencePlateError(
                    f"{inventory_path}: source_id {source_id!r} points to {raw_asset_path}, "
                    f"not {source_image_path.resolve()}."
                )
            return entry
    raise SubjectReferencePlateError(f"{inventory_path}: source_id {source_id!r} was not found.")


def load_plate_manifest(path: Path, *, episode_id: str | None = None) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SubjectReferencePlateError(f"{path}: subject-reference plate manifest must be an object.")
    missing = REQUIRED_PLATE_FIELDS - set(payload)
    if missing:
        raise SubjectReferencePlateError(f"{path}: missing fields: {', '.join(sorted(missing))}")
    if str(payload["plate_id"]).strip() != path.stem:
        raise SubjectReferencePlateError(f"{path}: plate_id must match the file stem {path.stem!r}.")

    source_image_path = Path(str(payload["source_image_path"]).strip()).expanduser().resolve()
    if not source_image_path.exists():
        raise SubjectReferencePlateError(f"{path}: source_image_path was not found: {source_image_path}")
    source_cutout_path = normalize_optional_path("source_cutout_path", payload.get("source_cutout_path"), path=path)
    source_mask_path = normalize_optional_path("source_mask_path", payload.get("source_mask_path"), path=path)

    crop_box = normalize_box("crop_box", payload["crop_box"], path=path)
    subject_box = normalize_box("subject_box", payload["subject_box"], path=path)
    placement_box = normalize_box("placement_box", payload["placement_box"], path=path)
    accent_box = normalize_optional_box("accent_box", payload.get("accent_box"), path=path)
    generation_allow_box = normalize_optional_box(
        "generation_allow_box",
        payload.get("generation_allow_box"),
        path=path,
    )
    generation_exclusion_boxes = normalize_optional_box_list(
        "generation_exclusion_boxes",
        payload.get("generation_exclusion_boxes"),
        path=path,
    )

    if box_area(subject_box) < 0.12:
        raise SubjectReferencePlateError(
            f"{path}: subject_box must isolate one dominant subject cluster; area is too small."
        )
    if box_area(subject_box) > 0.88:
        raise SubjectReferencePlateError(f"{path}: subject_box is too large to preserve documentary context.")

    if boxes_overlap(placement_box, TOP_UI_BAND):
        raise SubjectReferencePlateError(f"{path}: placement_box must stay out of the top UI band.")
    if boxes_overlap(placement_box, SUBTITLE_BAND):
        raise SubjectReferencePlateError(f"{path}: placement_box must stay out of the subtitle band.")
    if placement_box[3] > SUBTITLE_BAND[1]:
        raise SubjectReferencePlateError(f"{path}: placement_box must end above y=0.74.")

    canvas_size = payload["canvas_size"]
    if not isinstance(canvas_size, list) or len(canvas_size) != 2:
        raise SubjectReferencePlateError(f"{path}: canvas_size must be a two-item [width, height] array.")
    try:
        canvas_width, canvas_height = [int(item) for item in canvas_size]
    except (TypeError, ValueError) as exc:
        raise SubjectReferencePlateError(f"{path}: canvas_size values must be integers.") from exc
    if canvas_width <= 0 or canvas_height <= 0:
        raise SubjectReferencePlateError(f"{path}: canvas_size must contain positive integers.")

    background_mode = str(payload["background_mode"]).strip()
    if background_mode not in VALID_BACKGROUND_MODES:
        raise SubjectReferencePlateError(
            f"{path}: background_mode must be one of {', '.join(sorted(VALID_BACKGROUND_MODES))}."
        )

    allow_humans = bool(payload["allow_humans"])
    if episode_id in LOCKED_NO_HUMAN_EPISODES and allow_humans:
        raise SubjectReferencePlateError(f"{path}: allow_humans must stay false for locked {episode_id} manifests.")

    inventory_entry = load_source_inventory_entry(str(payload["source_id"]).strip(), source_image_path)

    return {
        "plate_id": str(payload["plate_id"]).strip(),
        "source_id": str(payload["source_id"]).strip(),
        "source_image_path": source_image_path,
        "source_cutout_path": source_cutout_path,
        "source_mask_path": source_mask_path,
        "crop_box": crop_box,
        "subject_box": subject_box,
        "placement_box": placement_box,
        "accent_box": accent_box,
        "generation_allow_box": generation_allow_box,
        "generation_exclusion_boxes": generation_exclusion_boxes,
        "canvas_size": [canvas_width, canvas_height],
        "background_mode": background_mode,
        "allow_humans": allow_humans,
        "notes": str(payload["notes"]).strip(),
        "inventory_entry": inventory_entry,
        "manifest_path": path.resolve(),
    }


def infer_plate_paths_from_output(output_path: Path) -> dict[str, Path] | None:
    resolved = output_path.expanduser().resolve()
    if resolved.suffix.lower() != ".png":
        return None
    if resolved.parent.name != "generated":
        return None
    plate_root = resolved.parent.parent
    if plate_root.name != "subject_reference_plates":
        return None
    manifest_path = plate_root / "manifests" / f"{resolved.stem}.json"
    build_manifest_path = resolved.with_name(f"{resolved.stem}.build.json")
    return {
        "plate_root": plate_root,
        "manifest_path": manifest_path,
        "build_manifest_path": build_manifest_path,
        "output_path": resolved,
    }


def build_status_for_output(output_path: Path) -> dict[str, Any] | None:
    inferred = infer_plate_paths_from_output(output_path)
    if inferred is None:
        return None

    result: dict[str, Any] = {
        "ready": False,
        "output_path": str(inferred["output_path"]),
        "manifest_path": str(inferred["manifest_path"]),
        "build_manifest_path": str(inferred["build_manifest_path"]),
    }
    if not inferred["output_path"].exists():
        result["reason"] = "generated plate PNG is missing"
        return result
    if not inferred["manifest_path"].exists():
        result["reason"] = "plate manifest is missing"
        return result
    if not inferred["build_manifest_path"].exists():
        result["reason"] = "plate build manifest is missing"
        return result

    try:
        build_manifest = read_json(inferred["build_manifest_path"])
    except json.JSONDecodeError as exc:
        result["reason"] = f"plate build manifest is unreadable: {exc}"
        return result

    if int(build_manifest.get("schema_version", -1)) != BUILD_SCHEMA_VERSION:
        result["reason"] = "plate build manifest schema is stale"
        return result

    if Path(str(build_manifest.get("output_path", ""))).expanduser().resolve() != inferred["output_path"]:
        result["reason"] = "plate build manifest output_path does not match the generated PNG"
        return result
    if Path(str(build_manifest.get("manifest_path", ""))).expanduser().resolve() != inferred["manifest_path"]:
        result["reason"] = "plate build manifest does not match the source manifest"
        return result

    try:
        manifest = load_plate_manifest(inferred["manifest_path"])
    except SubjectReferencePlateError as exc:
        result["reason"] = str(exc)
        return result

    source_image_path = Path(str(build_manifest.get("source_image_path", ""))).expanduser().resolve()
    if source_image_path != manifest["source_image_path"]:
        result["reason"] = "plate build manifest source_image_path does not match the manifest"
        return result
    source_cutout_path = build_manifest.get("source_cutout_path")
    manifest_cutout_path = manifest.get("source_cutout_path")
    if bool(source_cutout_path) != bool(manifest_cutout_path):
        result["reason"] = "plate build manifest source_cutout_path does not match the manifest"
        return result
    if source_cutout_path:
        if Path(str(source_cutout_path)).expanduser().resolve() != manifest_cutout_path:
            result["reason"] = "plate build manifest source_cutout_path does not match the manifest"
            return result
    source_mask_path = build_manifest.get("source_mask_path")
    manifest_mask_path = manifest.get("source_mask_path")
    if bool(source_mask_path) != bool(manifest_mask_path):
        result["reason"] = "plate build manifest source_mask_path does not match the manifest"
        return result
    if source_mask_path:
        if Path(str(source_mask_path)).expanduser().resolve() != manifest_mask_path:
            result["reason"] = "plate build manifest source_mask_path does not match the manifest"
            return result

    vision_ref_path = Path(str(build_manifest.get("vision_ref_path", ""))).expanduser().resolve()
    if not vision_ref_path.exists():
        result["reason"] = "generated vision reference is missing"
        return result
    layout_mask_path = Path(str(build_manifest.get("layout_mask_path", ""))).expanduser().resolve()
    if not layout_mask_path.exists():
        result["reason"] = "generated layout mask is missing"
        return result
    seed_rgba_path = Path(str(build_manifest.get("seed_rgba_path", ""))).expanduser().resolve()
    if not seed_rgba_path.exists():
        result["reason"] = "generated seed RGBA is missing"
        return result
    soft_mask_path = Path(str(build_manifest.get("soft_mask_path", ""))).expanduser().resolve()
    if not soft_mask_path.exists():
        result["reason"] = "generated soft mask is missing"
        return result

    manifest_mtime_ns = int(inferred["manifest_path"].stat().st_mtime_ns)
    source_mtime_ns = int(manifest["source_image_path"].stat().st_mtime_ns)
    if int(build_manifest.get("manifest_mtime_ns", -1)) != manifest_mtime_ns:
        result["reason"] = "plate manifest changed after the generated plate was built"
        return result
    if int(build_manifest.get("source_image_mtime_ns", -1)) != source_mtime_ns:
        result["reason"] = "source image changed after the generated plate was built"
        return result
    manifest_cutout_mtime_ns = (
        int(manifest["source_cutout_path"].stat().st_mtime_ns)
        if manifest.get("source_cutout_path") is not None
        else -1
    )
    if int(build_manifest.get("source_cutout_mtime_ns", -1)) != manifest_cutout_mtime_ns:
        result["reason"] = "source cutout changed after the generated plate was built"
        return result
    manifest_mask_mtime_ns = (
        int(manifest["source_mask_path"].stat().st_mtime_ns)
        if manifest.get("source_mask_path") is not None
        else -1
    )
    if int(build_manifest.get("source_mask_mtime_ns", -1)) != manifest_mask_mtime_ns:
        result["reason"] = "source mask changed after the generated plate was built"
        return result

    result.update(
        {
            "ready": True,
            "plate_id": manifest["plate_id"],
            "source_id": manifest["source_id"],
            "source_image_path": str(manifest["source_image_path"]),
            "preview_path": str(inferred["output_path"]),
            "vision_ref_path": str(vision_ref_path),
            "layout_mask_path": str(layout_mask_path),
            "seed_rgba_path": str(seed_rgba_path),
            "soft_mask_path": str(soft_mask_path),
        }
    )
    return result


def _box_to_pixels(box: list[float], size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    left = int(round(box[0] * width))
    top = int(round(box[1] * height))
    right = int(round(box[2] * width))
    bottom = int(round(box[3] * height))
    right = max(right, left + 1)
    bottom = max(bottom, top + 1)
    return left, top, right, bottom


def _interpolate_rgb(dark: tuple[int, int, int], light: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    normalized = min(1.0, max(0.0, amount))
    return tuple(
        int(round(dark[index] + ((light[index] - dark[index]) * normalized)))
        for index in range(3)
    )


def _apply_palette_lock(
    image: Any,
    *,
    subject_mask: Any,
    accent_pixels: tuple[int, int, int, int],
) -> Any:
    pixels = image.load()
    mask_pixels = subject_mask.load()
    matte = NEUTRAL_MATTE_RGB
    width, height = image.size
    accent_left, accent_top, accent_right, accent_bottom = accent_pixels

    for y in range(height):
        for x in range(width):
            if int(mask_pixels[x, y]) <= 0:
                continue
            current = pixels[x, y]
            if all(abs(int(current[channel]) - matte[channel]) <= 2 for channel in range(3)):
                continue
            luminance = (
                (0.2126 * float(current[0]))
                + (0.7152 * float(current[1]))
                + (0.0722 * float(current[2]))
            ) / 255.0
            tone_amount = max(0.0, min(1.0, luminance**0.9))
            if accent_left <= x < accent_right and accent_top <= y < accent_bottom:
                pixels[x, y] = _interpolate_rgb(PALETTE_ACCENT_DARK_RGB, PALETTE_ACCENT_LIGHT_RGB, tone_amount)
            else:
                pixels[x, y] = _interpolate_rgb(PALETTE_NEUTRAL_DARK_RGB, PALETTE_NEUTRAL_LIGHT_RGB, tone_amount)
    return image


def _meaningful_alpha(image: Any) -> bool:
    extrema = image.getchannel("A").getextrema()
    if extrema is None:
        return False
    return extrema[0] < 255 or extrema[1] < 255


def _resolve_subject_rgba(
    manifest: dict[str, Any],
    source_crop: Any,
    subject_box_pixels: tuple[int, int, int, int],
    *,
    Image: Any,
    knock_out_light_background: Any,
    trim_transparent_bounds: Any,
) -> tuple[Any, str]:
    if manifest["source_cutout_path"] is not None:
        with Image.open(manifest["source_cutout_path"]) as opened_cutout:
            cutout_rgba = opened_cutout.convert("RGBA")
        if cutout_rgba.size == source_crop.size:
            subject_rgba = cutout_rgba
        else:
            subject_rgba = cutout_rgba
        if manifest["background_mode"] == "neutral_matte_knockout":
            subject_rgba = (
                trim_transparent_bounds(subject_rgba)
                if _meaningful_alpha(subject_rgba)
                else trim_transparent_bounds(knock_out_light_background(subject_rgba))
            )
        return subject_rgba, "source_cutout"

    if manifest["source_mask_path"] is not None:
        with Image.open(manifest["source_mask_path"]) as opened_mask:
            if opened_mask.size == source_crop.size:
                subject_mask = opened_mask.convert("L")
            elif opened_mask.size == manifest["source_image_size"]:
                crop_pixels = _box_to_pixels(manifest["crop_box"], manifest["source_image_size"])
                subject_mask = opened_mask.convert("L").crop(crop_pixels)
            else:
                raise SubjectReferencePlateError(
                    f"{manifest['manifest_path']}: source_mask_path must match source_image_path or crop size."
                )
        masked_crop = source_crop.copy()
        masked_crop.putalpha(subject_mask)
        subject_rgba = trim_transparent_bounds(masked_crop.crop(subject_box_pixels))
        return subject_rgba, "source_mask"

    subject_rgba = source_crop.crop(subject_box_pixels)
    if manifest["background_mode"] == "neutral_matte_knockout":
        subject_rgba = trim_transparent_bounds(knock_out_light_background(subject_rgba))
    return subject_rgba, "subject_box_only"


def _build_subject_mask(subject_rgba: Any, *, Image: Any, ImageFilter: Any) -> Any:
    if _meaningful_alpha(subject_rgba):
        subject_mask = subject_rgba.getchannel("A")
    else:
        subject_mask = Image.new("L", subject_rgba.size, 255)
    blur_radius = max(1.0, float(min(subject_rgba.size)) * 0.006)
    return subject_mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))


def _trim_image_to_mask_bounds(image: Any, mask: Any) -> Any:
    bbox = mask.getbbox()
    if bbox is None:
        return image
    return image.crop(bbox)


def _build_region_mask(box: list[float], *, size: tuple[int, int], Image: Any, ImageDraw: Any) -> Any:
    region = Image.new("L", size, 0)
    draw = ImageDraw.Draw(region)
    left, top, right, bottom = _box_to_pixels(box, size)
    draw.rectangle((left, top, right, bottom), fill=255)
    return region


def build_subject_reference_plate(manifest_path: Path, *, output_path: Path | None = None) -> dict[str, Any]:
    manifest = load_plate_manifest(manifest_path)
    if output_path is None:
        generated_dir = manifest["manifest_path"].parent.parent / "generated"
        output_path = generated_dir / f"{manifest['plate_id']}.png"
    output_path = output_path.resolve()
    build_manifest_path = output_path.with_name(f"{output_path.stem}.build.json")

    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFilter
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SubjectReferencePlateError("Pillow is required to build subject-reference plates.") from exc
    try:
        from opening_tableau_tool import knock_out_light_background, trim_transparent_bounds
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SubjectReferencePlateError("opening_tableau_tool helpers are required for subject-reference plates.") from exc

    try:  # Pillow 9/10 compatibility
        resampling = Image.Resampling
    except AttributeError:  # pragma: no cover
        resampling = Image

    with Image.open(manifest["source_image_path"]) as source_image:
        crop_pixels = _box_to_pixels(manifest["crop_box"], source_image.size)
        source_crop = source_image.convert("RGBA").crop(crop_pixels)
        manifest["source_image_size"] = source_image.size
    subject_box_pixels = _box_to_pixels(manifest["subject_box"], source_crop.size)
    subject_image, preserved_crop_mode = _resolve_subject_rgba(
        manifest,
        source_crop,
        subject_box_pixels,
        Image=Image,
        knock_out_light_background=knock_out_light_background,
        trim_transparent_bounds=trim_transparent_bounds,
    )

    subject_width = max(1, subject_image.width)
    subject_height = max(1, subject_image.height)
    placement_pixels = _box_to_pixels(manifest["placement_box"], tuple(manifest["canvas_size"]))
    placement_width = max(1, placement_pixels[2] - placement_pixels[0])
    placement_height = max(1, placement_pixels[3] - placement_pixels[1])
    scale = min(placement_width / subject_width, placement_height / subject_height)

    resized_size = (
        max(1, int(round(subject_image.width * scale))),
        max(1, int(round(subject_image.height * scale))),
    )
    resized_subject = subject_image.resize(resized_size, resampling.LANCZOS)
    resized_mask = _build_subject_mask(subject_image, Image=Image, ImageFilter=ImageFilter).resize(
        resized_size,
        resampling.LANCZOS,
    )

    target_center_x = (placement_pixels[0] + placement_pixels[2]) / 2.0
    target_center_y = (placement_pixels[1] + placement_pixels[3]) / 2.0
    paste_origin = (
        int(round(target_center_x - (resized_subject.width / 2.0))),
        int(round(target_center_y - (resized_subject.height / 2.0))),
    )

    preview_canvas = Image.new("RGBA", tuple(manifest["canvas_size"]), NEUTRAL_MATTE_RGB + (255,))
    preview_canvas.paste(resized_subject, paste_origin, resized_mask)
    subject_canvas = Image.new("RGBA", tuple(manifest["canvas_size"]), (255, 255, 255, 0))
    subject_canvas.paste(resized_subject, paste_origin, resized_mask)
    placed_subject_mask = Image.new("L", tuple(manifest["canvas_size"]), 0)
    placed_subject_mask.paste(resized_mask, paste_origin)
    soft_mask_canvas = placed_subject_mask.copy()
    if manifest["generation_allow_box"] is not None:
        soft_mask_canvas = ImageChops.multiply(
            soft_mask_canvas,
            _build_region_mask(
                manifest["generation_allow_box"],
                size=tuple(manifest["canvas_size"]),
                Image=Image,
                ImageDraw=ImageDraw,
            ),
        )
    for exclusion_box in manifest["generation_exclusion_boxes"]:
        exclusion_mask = _build_region_mask(
            exclusion_box,
            size=tuple(manifest["canvas_size"]),
            Image=Image,
            ImageDraw=ImageDraw,
        )
        soft_mask_canvas = ImageChops.multiply(soft_mask_canvas, ImageChops.invert(exclusion_mask))
    soft_mask_canvas = soft_mask_canvas.filter(
        ImageFilter.GaussianBlur(radius=max(1.0, float(min(manifest["canvas_size"])) * 0.004))
    )

    preview_image = preview_canvas.convert("RGB")
    if manifest["accent_box"] is not None:
        accent_pixels = _box_to_pixels(manifest["accent_box"], tuple(manifest["canvas_size"]))
        preview_image = _apply_palette_lock(
            preview_image,
            subject_mask=placed_subject_mask,
            accent_pixels=accent_pixels,
        )
    vision_ref_rgba = preview_image.convert("RGBA")
    vision_ref_rgba.putalpha(placed_subject_mask)
    vision_ref_rgba = _trim_image_to_mask_bounds(vision_ref_rgba, placed_subject_mask)
    layout_mask_rgba = Image.new("RGBA", tuple(manifest["canvas_size"]), (255, 255, 255, 0))
    layout_mask_rgba.putalpha(soft_mask_canvas)
    final_image = preview_image
    vision_ref_path = output_path.with_name(f"{output_path.stem}__vision.png")
    layout_mask_path = output_path.with_name(f"{output_path.stem}__layout.png")
    seed_rgba_path = output_path.with_name(f"{output_path.stem}__seed.png")
    soft_mask_path = output_path.with_name(f"{output_path.stem}__mask.png")
    seed_rgba = final_image.convert("RGBA")
    seed_rgba.putalpha(soft_mask_canvas)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_image.save(output_path)
    vision_ref_rgba.save(vision_ref_path)
    layout_mask_rgba.save(layout_mask_path)
    seed_rgba.save(seed_rgba_path)
    soft_mask_canvas.save(soft_mask_path)

    build_manifest = {
        "schema_version": BUILD_SCHEMA_VERSION,
        "built_at": utc_now_iso(),
        "plate_id": manifest["plate_id"],
        "source_id": manifest["source_id"],
        "manifest_path": str(manifest["manifest_path"]),
        "output_path": str(output_path),
        "preview_path": str(output_path),
        "vision_ref_path": str(vision_ref_path),
        "layout_mask_path": str(layout_mask_path),
        "seed_rgba_path": str(seed_rgba_path),
        "soft_mask_path": str(soft_mask_path),
        "build_manifest_path": str(build_manifest_path),
        "source_image_path": str(manifest["source_image_path"]),
        "source_cutout_path": str(manifest["source_cutout_path"]) if manifest["source_cutout_path"] else "",
        "source_mask_path": str(manifest["source_mask_path"]) if manifest["source_mask_path"] else "",
        "manifest_mtime_ns": int(manifest["manifest_path"].stat().st_mtime_ns),
        "source_image_mtime_ns": int(manifest["source_image_path"].stat().st_mtime_ns),
        "source_cutout_mtime_ns": (
            int(manifest["source_cutout_path"].stat().st_mtime_ns) if manifest["source_cutout_path"] else -1
        ),
        "source_mask_mtime_ns": (
            int(manifest["source_mask_path"].stat().st_mtime_ns) if manifest["source_mask_path"] else -1
        ),
        "canvas_size": manifest["canvas_size"],
        "crop_box": manifest["crop_box"],
        "subject_box": manifest["subject_box"],
        "placement_box": manifest["placement_box"],
        "accent_box": manifest["accent_box"],
        "generation_allow_box": manifest["generation_allow_box"],
        "generation_exclusion_boxes": manifest["generation_exclusion_boxes"],
        "background_mode": manifest["background_mode"],
        "allow_humans": manifest["allow_humans"],
        "preserved_crop_mode": preserved_crop_mode,
        "palette_lock": {
            "active": manifest["accent_box"] is not None,
            "accent_box": manifest["accent_box"] or [],
        },
        "spatial_mask": {
            "active": bool(manifest["generation_allow_box"] or manifest["generation_exclusion_boxes"]),
            "allow_box": manifest["generation_allow_box"] or [],
            "exclusion_boxes": manifest["generation_exclusion_boxes"],
        },
        "inventory_entry": manifest["inventory_entry"],
    }
    write_json(build_manifest_path, build_manifest)
    return build_manifest


def build_subject_reference_plates_for_episode(references_root: Path, episode_id: str) -> dict[str, Any]:
    manifest_paths = load_episode_manifest_paths(references_root, episode_id)
    generated_dir = generated_dir_for_episode(references_root, episode_id)
    results: list[dict[str, Any]] = []
    for manifest_path in manifest_paths:
        build_manifest = build_subject_reference_plate(manifest_path, output_path=generated_dir / f"{manifest_path.stem}.png")
        results.append(build_manifest)

    summary = {
        "schema_version": BUILD_SCHEMA_VERSION,
        "episode_id": episode_id,
        "built_at": utc_now_iso(),
        "plate_count": len(results),
        "plates": results,
    }
    summary_path = generated_dir / "subject_reference_plates.build.json"
    write_json(summary_path, summary)
    summary["summary_path"] = str(summary_path)
    return summary
