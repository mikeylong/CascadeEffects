#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - runtime dependency guard
    Image = None
    ImageOps = None


NEUTRAL_MATTE_RGBA = (226, 228, 232, 255)
ADAPTER_LAYOUT_TEMPLATES = {
    "cover_weighted_triptych",
    "detail_left_bias_triptych",
}
ADAPTER_STEER_TARGETS = {
    "single_severe_warning_object",
    "cold_pipe_winter_signal",
    "accurate_shuttle_documentary",
}
ADAPTER_RANKING_BIAS_TAGS = {
    "single_object_severity",
    "compressed_monolith",
    "one_accent_only",
    "cold_pipe_detail",
    "winter_haze",
    "industrial_frost_signal",
    "accurate_shuttle_stack",
}


class MidjourneyPackageError(Exception):
    pass


@dataclass(frozen=True)
class MidjourneyPackageShot:
    package_manifest_path: Path
    package_root: Path
    package_id: str
    shot_id: str
    prompt_text: str
    negative_terms: tuple[str, ...]
    reference_files: tuple[str, ...]
    prompt_doc_path: str
    references_manifest_path: str
    reference_provenance: tuple[dict[str, Any], ...] = ()

    def reference_paths(self) -> list[Path]:
        return [(self.package_root / relative_path).resolve() for relative_path in self.reference_files]


@dataclass(frozen=True)
class MidjourneyPackageAdapter:
    adapter_path: Path
    shot_id: str
    included_reference_indices: tuple[int, ...]
    reference_crops: dict[int, tuple[float, float, float, float]]
    grid_layout_template: str
    prompt_adapter_append: tuple[str, ...]
    negative_adapter_terms: tuple[str, ...]
    draft_visual_softpass: dict[str, Any]
    steer_target: str
    steer_keep_traits: tuple[str, ...]
    steer_avoid_traits: tuple[str, ...]
    ranking_bias_tags: tuple[str, ...]


def resolve_package_manifest_path(raw_path: str | Path, *, repo_root: Path) -> Path:
    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    else:
        path = path.resolve()
    if not path.exists():
        raise MidjourneyPackageError(f"MidJourney package manifest was not found: {path}")
    return path


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MidjourneyPackageError(f"MidJourney package manifest is invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise MidjourneyPackageError(f"MidJourney package manifest must be an object: {path}")
    return payload


def normalize_negative_terms(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    terms: list[str] = []
    seen: set[str] = set()
    for raw in value:
        text = str(raw).strip()
        if not text:
            continue
        normalized = text if text.lower().startswith("no ") else f"no {text}"
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        terms.append(normalized)
    return terms


def load_midjourney_package_shot(
    package_manifest_path: str | Path,
    *,
    shot_id: str,
    repo_root: Path,
) -> MidjourneyPackageShot:
    manifest_path = resolve_package_manifest_path(package_manifest_path, repo_root=repo_root)
    payload = _read_json(manifest_path)
    package_root = manifest_path.parent
    normalized_shot_id = str(shot_id).strip()
    if not normalized_shot_id:
        raise MidjourneyPackageError(f"{manifest_path}: midjourney_shot_id must be non-empty.")

    shot_entry: dict[str, Any] | None = None
    if normalized_shot_id == "cover":
        candidate = payload.get("cover")
        if isinstance(candidate, dict):
            shot_entry = candidate
    if shot_entry is None:
        for candidate in payload.get("shots", []):
            if isinstance(candidate, dict) and str(candidate.get("shot_id", "")).strip() == normalized_shot_id:
                shot_entry = candidate
                break
    if shot_entry is None:
        raise MidjourneyPackageError(
            f"{manifest_path}: no MidJourney package shot matched midjourney_shot_id={normalized_shot_id!r}."
        )

    package_id = str(payload.get("package_id", "")).strip()
    if not package_id:
        raise MidjourneyPackageError(f"{manifest_path}: package_id must be non-empty.")
    prompt_text = str(shot_entry.get("prompt_text", "")).strip()
    if not prompt_text:
        raise MidjourneyPackageError(
            f"{manifest_path}: shot {normalized_shot_id!r} is missing prompt_text."
        )
    reference_files = [str(item).strip() for item in shot_entry.get("reference_files", []) if str(item).strip()]
    if not reference_files:
        raise MidjourneyPackageError(
            f"{manifest_path}: shot {normalized_shot_id!r} is missing reference_files."
        )

    resolved_reference_paths: list[Path] = []
    for relative_path in reference_files:
        resolved_path = (package_root / relative_path).resolve()
        if not resolved_path.exists():
            raise MidjourneyPackageError(
                f"{manifest_path}: shot {normalized_shot_id!r} reference file was not found: {resolved_path}"
            )
        resolved_reference_paths.append(resolved_path)

    return MidjourneyPackageShot(
        package_manifest_path=manifest_path,
        package_root=package_root,
        package_id=package_id,
        shot_id=normalized_shot_id,
        prompt_text=prompt_text,
        negative_terms=tuple(str(item).strip() for item in shot_entry.get("negative_terms", []) if str(item).strip()),
        reference_files=tuple(reference_files),
        prompt_doc_path=str(shot_entry.get("prompt_doc_path", "")).strip(),
        references_manifest_path=str(shot_entry.get("references_manifest_path", "")).strip(),
        reference_provenance=tuple(
            item for item in shot_entry.get("reference_provenance", []) if isinstance(item, dict)
        ),
    )


def _normalize_reference_crop(
    *,
    label: str,
    value: Any,
    adapter_path: Path,
) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise MidjourneyPackageError(f"{adapter_path}: {label} must be a list of four normalized coordinates.")
    try:
        x1, y1, x2, y2 = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise MidjourneyPackageError(f"{adapter_path}: {label} must contain only numeric coordinates.") from exc
    coordinates = (x1, y1, x2, y2)
    if any(item < 0.0 or item > 1.0 for item in coordinates):
        raise MidjourneyPackageError(f"{adapter_path}: {label} coordinates must stay within 0.0-1.0.")
    if x2 <= x1 or y2 <= y1:
        raise MidjourneyPackageError(f"{adapter_path}: {label} must define a positive-area box.")
    return coordinates


def _normalize_adapter_crop_map(raw_value: Any, *, adapter_path: Path) -> dict[int, tuple[float, float, float, float]]:
    normalized: dict[int, tuple[float, float, float, float]] = {}
    if isinstance(raw_value, dict):
        iterable = raw_value.items()
        for raw_index, raw_crop in iterable:
            try:
                reference_index = int(str(raw_index).strip())
            except ValueError as exc:
                raise MidjourneyPackageError(
                    f"{adapter_path}: reference_crops keys must be integer indices."
                ) from exc
            normalized[reference_index] = _normalize_reference_crop(
                label=f"reference_crops[{reference_index}]",
                value=raw_crop,
                adapter_path=adapter_path,
            )
        return normalized
    if isinstance(raw_value, list):
        for entry in raw_value:
            if not isinstance(entry, dict):
                raise MidjourneyPackageError(
                    f"{adapter_path}: reference_crops list entries must be objects."
                )
            try:
                reference_index = int(entry.get("reference_index"))
            except (TypeError, ValueError) as exc:
                raise MidjourneyPackageError(
                    f"{adapter_path}: reference_crops entries require integer reference_index."
                ) from exc
            normalized[reference_index] = _normalize_reference_crop(
                label=f"reference_crops[{reference_index}]",
                value=entry.get("crop_box"),
                adapter_path=adapter_path,
            )
        return normalized
    raise MidjourneyPackageError(f"{adapter_path}: reference_crops must be an object or list.")


def load_midjourney_package_adapter(
    raw_path: str | Path,
    *,
    shot: MidjourneyPackageShot,
    repo_root: Path,
) -> MidjourneyPackageAdapter:
    adapter_path = resolve_package_manifest_path(raw_path, repo_root=repo_root)
    payload = _read_json(adapter_path)
    shot_id = str(payload.get("shot_id", "")).strip()
    if shot_id != shot.shot_id:
        raise MidjourneyPackageError(
            f"{adapter_path}: shot_id must match package shot {shot.shot_id!r}, got {shot_id!r}."
        )
    raw_indices = payload.get("included_reference_indices")
    if not isinstance(raw_indices, list) or not raw_indices:
        raise MidjourneyPackageError(f"{adapter_path}: included_reference_indices must be a non-empty list.")
    included_reference_indices: list[int] = []
    seen: set[int] = set()
    for raw_index in raw_indices:
        try:
            reference_index = int(raw_index)
        except (TypeError, ValueError) as exc:
            raise MidjourneyPackageError(
                f"{adapter_path}: included_reference_indices must contain only integers."
            ) from exc
        if reference_index < 0 or reference_index >= len(shot.reference_files):
            raise MidjourneyPackageError(
                f"{adapter_path}: included reference index {reference_index} is outside the package range."
            )
        if reference_index in seen:
            continue
        seen.add(reference_index)
        included_reference_indices.append(reference_index)

    grid_layout_template = str(payload.get("grid_layout_template", "")).strip()
    if grid_layout_template not in ADAPTER_LAYOUT_TEMPLATES:
        raise MidjourneyPackageError(
            f"{adapter_path}: grid_layout_template must be one of {', '.join(sorted(ADAPTER_LAYOUT_TEMPLATES))}."
        )
    if len(included_reference_indices) != 3:
        raise MidjourneyPackageError(
            f"{adapter_path}: {grid_layout_template} requires exactly 3 included_reference_indices."
        )

    reference_crops = _normalize_adapter_crop_map(payload.get("reference_crops"), adapter_path=adapter_path)
    missing_crops = [index for index in included_reference_indices if index not in reference_crops]
    if missing_crops:
        raise MidjourneyPackageError(
            f"{adapter_path}: reference_crops missing entries for indices {missing_crops}."
        )

    prompt_adapter_append = tuple(
        item for item in (str(raw).strip() for raw in payload.get("prompt_adapter_append", [])) if item
    )
    negative_adapter_terms = tuple(normalize_negative_terms(payload.get("negative_adapter_terms", [])))
    softpass = payload.get("draft_visual_softpass")
    if not isinstance(softpass, dict):
        raise MidjourneyPackageError(f"{adapter_path}: draft_visual_softpass must be an object.")
    allowed_visual_failures = [
        str(item).strip()
        for item in softpass.get("allowed_visual_failures", [])
        if str(item).strip()
    ]
    normalized_softpass = {
        "enabled": bool(softpass.get("enabled", True)),
        "allowed_visual_failures": list(dict.fromkeys(allowed_visual_failures)),
    }
    steer_target = str(payload.get("steer_target", "")).strip()
    if steer_target not in ADAPTER_STEER_TARGETS:
        raise MidjourneyPackageError(
            f"{adapter_path}: steer_target must be one of {', '.join(sorted(ADAPTER_STEER_TARGETS))}."
        )
    steer_keep_traits = tuple(
        item for item in (str(raw).strip() for raw in payload.get("steer_keep_traits", [])) if item
    )
    if not steer_keep_traits:
        raise MidjourneyPackageError(f"{adapter_path}: steer_keep_traits must be a non-empty list.")
    steer_avoid_traits = tuple(
        item for item in (str(raw).strip() for raw in payload.get("steer_avoid_traits", [])) if item
    )
    if not steer_avoid_traits:
        raise MidjourneyPackageError(f"{adapter_path}: steer_avoid_traits must be a non-empty list.")
    ranking_bias_tags = tuple(
        item for item in (str(raw).strip() for raw in payload.get("ranking_bias_tags", [])) if item
    )
    if not ranking_bias_tags:
        raise MidjourneyPackageError(f"{adapter_path}: ranking_bias_tags must be a non-empty list.")
    unsupported_tags = sorted(set(ranking_bias_tags) - ADAPTER_RANKING_BIAS_TAGS)
    if unsupported_tags:
        raise MidjourneyPackageError(
            f"{adapter_path}: ranking_bias_tags contains unsupported tags: {', '.join(unsupported_tags)}."
        )

    return MidjourneyPackageAdapter(
        adapter_path=adapter_path,
        shot_id=shot_id,
        included_reference_indices=tuple(included_reference_indices),
        reference_crops=reference_crops,
        grid_layout_template=grid_layout_template,
        prompt_adapter_append=prompt_adapter_append,
        negative_adapter_terms=negative_adapter_terms,
        draft_visual_softpass=normalized_softpass,
        steer_target=steer_target,
        steer_keep_traits=steer_keep_traits,
        steer_avoid_traits=steer_avoid_traits,
        ranking_bias_tags=tuple(dict.fromkeys(ranking_bias_tags)),
    )


def grid_runtime_filename(*, shot_id: str) -> str:
    return f"{shot_id}__reference_grid.png"


def _grid_cells(count: int, *, width: int, height: int) -> list[tuple[int, int, int, int]]:
    if count <= 0:
        raise MidjourneyPackageError("MidJourney package shots require at least one reference image.")
    if count == 1:
        return [(0, 0, width, height)]
    if count == 2:
        midpoint = height // 2
        return [(0, 0, width, midpoint), (0, midpoint, width, height)]
    midpoint_x = width // 2
    midpoint_y = height // 2
    return [
        (0, 0, midpoint_x, midpoint_y),
        (midpoint_x, 0, width, midpoint_y),
        (0, midpoint_y, midpoint_x, height),
        (midpoint_x, midpoint_y, width, height),
    ]


def _normalized_crop_to_pixels(
    crop: tuple[float, float, float, float],
    *,
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = crop
    left = max(0, min(width - 1, int(round(x1 * width))))
    top = max(0, min(height - 1, int(round(y1 * height))))
    right = max(left + 1, min(width, int(round(x2 * width))))
    bottom = max(top + 1, min(height, int(round(y2 * height))))
    return left, top, right, bottom


def _adapter_grid_cells(template: str, *, width: int, height: int) -> list[tuple[int, int, int, int]]:
    if template == "cover_weighted_triptych":
        split_x = int(round(width * 0.62))
    elif template == "detail_left_bias_triptych":
        split_x = int(round(width * 0.60))
    else:  # pragma: no cover - guarded by loader validation
        raise MidjourneyPackageError(f"Unsupported MidJourney adapter layout template: {template}")
    split_y = height // 2
    return [
        (0, 0, split_x, height),
        (split_x, 0, width, split_y),
        (split_x, split_y, width, height),
    ]


def build_reference_grid(
    shot: MidjourneyPackageShot,
    *,
    output_path: Path,
    width: int,
    height: int,
    adapter: MidjourneyPackageAdapter | None = None,
) -> dict[str, Any]:
    if Image is None or ImageOps is None:
        raise MidjourneyPackageError("Pillow is required to build MidJourney reference grids.")
    if width <= 0 or height <= 0:
        raise MidjourneyPackageError(f"Reference grid dimensions must be positive, got {width}x{height}.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGBA", (int(width), int(height)), NEUTRAL_MATTE_RGBA)
    reference_paths = shot.reference_paths()
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    grid_tiles: list[dict[str, Any]] = []

    if adapter is None:
        cells = _grid_cells(len(reference_paths), width=int(width), height=int(height))
        for index, reference_path in enumerate(reference_paths):
            if index >= len(cells):
                break
            left, top, right, bottom = cells[index]
            cell_width = max(1, right - left)
            cell_height = max(1, bottom - top)
            with Image.open(reference_path) as source_image:
                prepared = ImageOps.exif_transpose(source_image).convert("RGBA")
                contained = ImageOps.contain(prepared, (cell_width, cell_height), method=resampling)
            offset_x = left + max(0, (cell_width - contained.width) // 2)
            offset_y = top + max(0, (cell_height - contained.height) // 2)
            canvas.alpha_composite(contained, (offset_x, offset_y))
            grid_tiles.append(
                {
                    "reference_index": index,
                    "reference_file": shot.reference_files[index],
                    "reference_path": str(reference_path),
                    "crop_box": [0.0, 0.0, 1.0, 1.0],
                    "tile_box": [left, top, right, bottom],
                }
            )
    else:
        cells = _adapter_grid_cells(adapter.grid_layout_template, width=int(width), height=int(height))
        for tile_index, reference_index in enumerate(adapter.included_reference_indices):
            reference_path = reference_paths[reference_index]
            left, top, right, bottom = cells[tile_index]
            cell_width = max(1, right - left)
            cell_height = max(1, bottom - top)
            crop_box = adapter.reference_crops[reference_index]
            with Image.open(reference_path) as source_image:
                prepared = ImageOps.exif_transpose(source_image).convert("RGBA")
                crop_rect = _normalized_crop_to_pixels(crop_box, width=prepared.width, height=prepared.height)
                cropped = prepared.crop(crop_rect)
                fitted = ImageOps.fit(cropped, (cell_width, cell_height), method=resampling)
            canvas.alpha_composite(fitted, (left, top))
            grid_tiles.append(
                {
                    "reference_index": reference_index,
                    "reference_file": shot.reference_files[reference_index],
                    "reference_path": str(reference_path),
                    "crop_box": [round(value, 6) for value in crop_box],
                    "tile_box": [left, top, right, bottom],
                }
            )

    canvas.save(output_path)
    manifest = {
        "package_manifest_path": str(shot.package_manifest_path),
        "package_id": shot.package_id,
        "shot_id": shot.shot_id,
        "prompt_text": shot.prompt_text,
        "negative_terms": list(shot.negative_terms),
        "reference_files": list(shot.reference_files),
        "reference_paths": [str(path) for path in reference_paths],
        "grid_layout": (
            adapter.grid_layout_template
            if adapter is not None
            else "single" if len(reference_paths) == 1 else "two_up" if len(reference_paths) == 2 else "two_by_two"
        ),
        "grid_path": str(output_path.resolve()),
        "width": int(width),
        "height": int(height),
        "prompt_doc_path": shot.prompt_doc_path,
        "references_manifest_path": shot.references_manifest_path,
        "grid_tiles": grid_tiles,
    }
    if adapter is not None:
        manifest["adapter"] = {
            "active": True,
            "adapter_path": str(adapter.adapter_path),
            "shot_id": adapter.shot_id,
            "included_reference_indices": list(adapter.included_reference_indices),
            "reference_crops": {
                str(index): [round(value, 6) for value in crop]
                for index, crop in sorted(adapter.reference_crops.items())
            },
            "grid_layout_template": adapter.grid_layout_template,
            "prompt_adapter_append": list(adapter.prompt_adapter_append),
            "negative_adapter_terms": list(adapter.negative_adapter_terms),
            "draft_visual_softpass": {
                "enabled": bool(adapter.draft_visual_softpass.get("enabled", False)),
                "allowed_visual_failures": list(adapter.draft_visual_softpass.get("allowed_visual_failures", [])),
            },
            "steer_target": adapter.steer_target,
            "steer_keep_traits": list(adapter.steer_keep_traits),
            "steer_avoid_traits": list(adapter.steer_avoid_traits),
            "ranking_bias_tags": list(adapter.ranking_bias_tags),
        }
    return manifest
