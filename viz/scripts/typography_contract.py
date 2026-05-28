#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable


class TypographyContractError(ValueError):
    pass


HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")
LEGACY_REQUIRED_FIELDS = {
    "family",
    "preset",
    "enabled",
    "mode",
    "apply_stage",
    "max_zones",
    "zones",
}
SHARED_REQUIRED_FIELDS = {
    "schema_version",
    "artifact_type",
    "application_phase",
    "enabled",
    "mode",
    "zones",
    "validation_policy",
}
ZONE_REQUIRED_FIELDS = {
    "id",
    "text",
    "quad_norm",
    "font_family",
    "font_size_px",
    "tracking",
    "color",
    "opacity",
    "blend_mode",
    "blur_px",
    "glow_px",
    "noise_strength",
}
LEGACY_ZONE_REQUIRED_FIELDS = ZONE_REQUIRED_FIELDS | {"kind"}
LEGACY_ALLOWED_KINDS = {
    "wall_clock_strip",
    "wall_mark",
    "room_sign",
    "passive_display",
}
ALLOWED_ARTIFACT_TYPES = {"still", "handoff_asset", "image_sequence", "video"}
ALLOWED_APPLICATION_PHASES = {
    "post_generate",
    "post_refine",
    "post_upscale",
    "post_handoff",
    "post_encode",
}
ALLOWED_BLEND_MODES = {"normal", "screen", "add", "multiply"}
ALLOWED_MODES = {"overlay_first"}
ALLOWED_VALIDATION_POLICIES = {"off", "warn", "fail"}
ALLOWED_FIT_MODES = {"stretch", "contain"}
ALLOWED_ALIGN_X = {"start", "center", "end", "left", "right"}
ALLOWED_ALIGN_Y = {"start", "center", "end", "top", "bottom", "middle"}
ALLOWED_NEUTRALIZE_MODES = {"auto", "none", "soft_blur"}
ALLOWED_UNDERLAY_KINDS = {"auto", "none", "clock_strip"}
DEFAULT_VALIDATION_POLICY = {"zone_ocr": "warn", "unapproved_text": "fail"}
APPLICATION_PHASE_ALIASES = {
    "post_upscale": "final_upscale",
    "post_handoff": "handoff_stage",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_typography_intent(
    path: Path,
    *,
    expected_family: str | None = None,
    expected_preset: str | None = None,
    active_family_check: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    return normalize_typography_intent(
        read_json(path),
        path=path,
        expected_family=expected_family,
        expected_preset=expected_preset,
        active_family_check=active_family_check,
    )


def normalize_typography_intent(
    data: dict[str, Any],
    *,
    path: Path | None = None,
    expected_family: str | None = None,
    expected_preset: str | None = None,
    active_family_check: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise TypographyContractError(f"{format_label(path)}: typography intent must be an object.")
    if "schema_version" in data or "artifact_type" in data or "validation_policy" in data:
        return normalize_shared_intent(
            data,
            path=path,
            expected_family=expected_family,
            expected_preset=expected_preset,
            active_family_check=active_family_check,
        )
    return normalize_legacy_sidecar(
        data,
        path=path,
        expected_family=expected_family,
        expected_preset=expected_preset,
        active_family_check=active_family_check,
    )


def normalize_shared_intent(
    data: dict[str, Any],
    *,
    path: Path | None = None,
    expected_family: str | None = None,
    expected_preset: str | None = None,
    active_family_check: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    label = format_label(path)
    missing = SHARED_REQUIRED_FIELDS - set(data)
    if missing:
        raise TypographyContractError(f"{label}: missing typography fields: {', '.join(sorted(missing))}")

    schema_version = str(data["schema_version"]).strip()
    if schema_version not in {"1"}:
        raise TypographyContractError(f"{label}: schema_version must be '1'.")

    artifact_type = str(data["artifact_type"]).strip()
    if artifact_type not in ALLOWED_ARTIFACT_TYPES:
        raise TypographyContractError(
            f"{label}: artifact_type must be one of {', '.join(sorted(ALLOWED_ARTIFACT_TYPES))}."
        )

    application_phase = str(data["application_phase"]).strip()
    if application_phase not in ALLOWED_APPLICATION_PHASES:
        raise TypographyContractError(
            f"{label}: application_phase must be one of {', '.join(sorted(ALLOWED_APPLICATION_PHASES))}."
        )

    enabled = data["enabled"]
    if not isinstance(enabled, bool):
        raise TypographyContractError(f"{label}: enabled must be a boolean.")

    mode = str(data["mode"]).strip()
    if mode not in ALLOWED_MODES:
        raise TypographyContractError(f"{label}: mode must be one of {', '.join(sorted(ALLOWED_MODES))}.")

    family = normalize_optional_string(data.get("family"))
    preset = normalize_optional_string(data.get("preset"))
    validate_expected_family_and_preset(
        family=family,
        preset=preset,
        expected_family=expected_family,
        expected_preset=expected_preset,
        label=label,
    )
    if family and active_family_check is not None and not active_family_check(family):
        raise TypographyContractError(f"{label}: controlled typography is only supported for active workflow families.")

    zones = normalize_zones(
        data["zones"],
        label=label,
        is_legacy=False,
        max_zones=data.get("max_zones"),
    )
    validation_policy = normalize_validation_policy(data["validation_policy"], label=label)

    normalized = {
        "schema_version": schema_version,
        "artifact_type": artifact_type,
        "application_phase": application_phase,
        "enabled": enabled,
        "mode": mode,
        "zones": zones,
        "validation_policy": validation_policy,
        "source": {
            "format": "shared_intent",
            "path": str(path) if path else "",
            "legacy_apply_stage": APPLICATION_PHASE_ALIASES.get(application_phase, ""),
        },
    }
    if family:
        normalized["family"] = family
        normalized["source"]["family"] = family
    if preset:
        normalized["preset"] = preset
        normalized["source"]["preset"] = preset
    return normalized


def normalize_legacy_sidecar(
    data: dict[str, Any],
    *,
    path: Path | None = None,
    expected_family: str | None = None,
    expected_preset: str | None = None,
    active_family_check: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    label = format_label(path)
    missing = LEGACY_REQUIRED_FIELDS - set(data)
    if missing:
        raise TypographyContractError(f"{label}: missing typography fields: {', '.join(sorted(missing))}")

    family = str(data["family"]).strip()
    preset = str(data["preset"]).strip()
    validate_expected_family_and_preset(
        family=family,
        preset=preset,
        expected_family=expected_family,
        expected_preset=expected_preset,
        label=label,
    )
    if active_family_check is not None and not active_family_check(family):
        raise TypographyContractError(f"{label}: controlled typography is only supported for active workflow families.")

    enabled = data["enabled"]
    if not isinstance(enabled, bool):
        raise TypographyContractError(f"{label}: enabled must be a boolean.")

    mode = str(data["mode"]).strip()
    if mode not in ALLOWED_MODES:
        raise TypographyContractError(f"{label}: mode must be one of {', '.join(sorted(ALLOWED_MODES))}.")

    apply_stage = str(data["apply_stage"]).strip()
    if apply_stage != "final_upscale":
        raise TypographyContractError(f"{label}: apply_stage must be 'final_upscale'.")

    zones = normalize_zones(
        data["zones"],
        label=label,
        is_legacy=True,
        max_zones=data["max_zones"],
    )

    return {
        "schema_version": "1",
        "artifact_type": "still",
        "application_phase": "post_upscale",
        "enabled": enabled,
        "mode": mode,
        "zones": zones,
        "validation_policy": dict(DEFAULT_VALIDATION_POLICY),
        "family": family,
        "preset": preset,
        "source": {
            "format": "legacy_sidecar",
            "path": str(path) if path else "",
            "family": family,
            "preset": preset,
            "legacy_apply_stage": apply_stage,
        },
    }


def normalize_zones(
    zones: Any,
    *,
    label: str,
    is_legacy: bool,
    max_zones: Any,
) -> list[dict[str, Any]]:
    if max_zones is not None:
        if not isinstance(max_zones, int) or max_zones <= 0:
            raise TypographyContractError(f"{label}: max_zones must be a positive integer.")
    if not isinstance(zones, list) or not zones:
        raise TypographyContractError(f"{label}: zones must be a non-empty list.")
    if isinstance(max_zones, int) and len(zones) > max_zones:
        raise TypographyContractError(f"{label}: zone count {len(zones)} exceeds max_zones={max_zones}.")

    normalized: list[dict[str, Any]] = []
    seen_zone_ids: set[str] = set()
    for index, zone in enumerate(zones):
        zone_label = f"{label}: zones[{index}]"
        normalized_zone = normalize_zone(zone, label=zone_label, is_legacy=is_legacy)
        zone_id = normalized_zone["id"]
        if zone_id in seen_zone_ids:
            raise TypographyContractError(f"{zone_label}: duplicate zone id {zone_id!r}.")
        seen_zone_ids.add(zone_id)
        normalized.append(normalized_zone)
    return normalized


def normalize_zone(zone: Any, *, label: str, is_legacy: bool) -> dict[str, Any]:
    if not isinstance(zone, dict):
        raise TypographyContractError(f"{label} must be an object.")
    required_fields = LEGACY_ZONE_REQUIRED_FIELDS if is_legacy else ZONE_REQUIRED_FIELDS
    missing = required_fields - set(zone)
    if missing:
        raise TypographyContractError(f"{label} is missing fields: {', '.join(sorted(missing))}.")

    zone_id = str(zone["id"]).strip()
    if not zone_id:
        raise TypographyContractError(f"{label}: id must be non-empty.")

    if "kind" in zone and not is_legacy:
        raise TypographyContractError(f"{label}: kind is only supported through legacy sidecar compatibility.")

    kind = ""
    if is_legacy:
        kind = str(zone["kind"]).strip()
        if kind not in LEGACY_ALLOWED_KINDS:
            raise TypographyContractError(
                f"{label}: kind must be one of {', '.join(sorted(LEGACY_ALLOWED_KINDS))}."
            )

    text = str(zone["text"]).strip()
    if not text:
        raise TypographyContractError(f"{label}: text must be non-empty.")

    quad_norm = normalize_quad_norm(zone["quad_norm"], label=label)

    font_family = str(zone["font_family"]).strip()
    if not font_family:
        raise TypographyContractError(f"{label}: font_family must be non-empty.")
    if not isinstance(zone["font_size_px"], int) or zone["font_size_px"] <= 0:
        raise TypographyContractError(f"{label}: font_size_px must be a positive integer.")
    line_spacing_px = zone.get("line_spacing_px", max(4.0, float(zone["font_size_px"]) * 0.22))
    if not isinstance(line_spacing_px, (int, float)) or float(line_spacing_px) < 0.0:
        raise TypographyContractError(f"{label}: line_spacing_px must be a non-negative number.")
    if not isinstance(zone["tracking"], (int, float)):
        raise TypographyContractError(f"{label}: tracking must be numeric.")
    color = str(zone["color"]).strip()
    if not HEX_COLOR_RE.match(color):
        raise TypographyContractError(f"{label}: color must be a hex string like #RRGGBB or #RRGGBBAA.")
    if not isinstance(zone["opacity"], (int, float)) or not (0.0 <= float(zone["opacity"]) <= 1.0):
        raise TypographyContractError(f"{label}: opacity must be between 0.0 and 1.0.")
    blend_mode = str(zone["blend_mode"]).strip()
    if blend_mode not in ALLOWED_BLEND_MODES:
        raise TypographyContractError(
            f"{label}: blend_mode must be one of {', '.join(sorted(ALLOWED_BLEND_MODES))}."
        )
    if not isinstance(zone["blur_px"], (int, float)) or float(zone["blur_px"]) < 0.0:
        raise TypographyContractError(f"{label}: blur_px must be a non-negative number.")
    if not isinstance(zone["glow_px"], (int, float)) or float(zone["glow_px"]) < 0.0:
        raise TypographyContractError(f"{label}: glow_px must be a non-negative number.")
    if (
        not isinstance(zone["noise_strength"], (int, float))
        or float(zone["noise_strength"]) < 0.0
        or float(zone["noise_strength"]) > 1.0
    ):
        raise TypographyContractError(f"{label}: noise_strength must be between 0.0 and 1.0.")

    fit_mode = str(zone.get("fit_mode", "stretch")).strip()
    if fit_mode not in ALLOWED_FIT_MODES:
        raise TypographyContractError(f"{label}: fit_mode must be one of {', '.join(sorted(ALLOWED_FIT_MODES))}.")

    padding_px = zone.get("padding_px", 0)
    if not isinstance(padding_px, (int, float)) or float(padding_px) < 0.0:
        raise TypographyContractError(f"{label}: padding_px must be a non-negative number.")

    align_x = normalize_align_x(zone.get("align_x", "center"), label=label)
    align_y = normalize_align_y(zone.get("align_y", "center"), label=label)

    neutralize_mode = str(zone.get("neutralize_mode", "auto")).strip()
    if neutralize_mode not in ALLOWED_NEUTRALIZE_MODES:
        raise TypographyContractError(
            f"{label}: neutralize_mode must be one of {', '.join(sorted(ALLOWED_NEUTRALIZE_MODES))}."
        )

    underlay_kind = str(zone.get("underlay_kind", "auto")).strip()
    if underlay_kind not in ALLOWED_UNDERLAY_KINDS:
        raise TypographyContractError(
            f"{label}: underlay_kind must be one of {', '.join(sorted(ALLOWED_UNDERLAY_KINDS))}."
        )

    shadow = normalize_shadow(zone.get("shadow"), label=label)
    debug_emit_crop = zone.get("debug_emit_crop", False)
    if not isinstance(debug_emit_crop, bool):
        raise TypographyContractError(f"{label}: debug_emit_crop must be a boolean.")

    normalized = {
        "id": zone_id,
        "text": text,
        "quad_norm": quad_norm,
        "font_family": font_family,
        "font_size_px": int(zone["font_size_px"]),
        "line_spacing_px": float(line_spacing_px),
        "tracking": float(zone["tracking"]),
        "color": color,
        "opacity": float(zone["opacity"]),
        "blend_mode": blend_mode,
        "blur_px": float(zone["blur_px"]),
        "glow_px": float(zone["glow_px"]),
        "noise_strength": float(zone["noise_strength"]),
        "fit_mode": fit_mode,
        "padding_px": float(padding_px),
        "align_x": align_x,
        "align_y": align_y,
        "neutralize_mode": neutralize_mode,
        "underlay_kind": underlay_kind,
        "shadow": shadow,
        "debug_emit_crop": debug_emit_crop,
    }
    if is_legacy:
        normalized["kind"] = kind
    return normalized


def normalize_quad_norm(quad_norm: Any, *, label: str) -> list[list[float]]:
    if not isinstance(quad_norm, list) or len(quad_norm) != 4:
        raise TypographyContractError(f"{label}: quad_norm must contain four [x, y] points.")

    quad_points: list[tuple[float, float]] = []
    for point_index, point in enumerate(quad_norm, start=1):
        if (
            not isinstance(point, list)
            or len(point) != 2
            or not all(isinstance(value, (int, float)) for value in point)
        ):
            raise TypographyContractError(f"{label}: quad_norm point {point_index} must be a numeric [x, y] pair.")
        px = float(point[0])
        py = float(point[1])
        if px < 0.0 or px > 1.0 or py < 0.0 or py > 1.0:
            raise TypographyContractError(
                f"{label}: quad_norm point {point_index} must stay inside normalized bounds."
            )
        quad_points.append((px, py))

    polygon_area = 0.0
    for point_index, (ax, ay) in enumerate(quad_points):
        bx, by = quad_points[(point_index + 1) % len(quad_points)]
        polygon_area += (ax * by) - (bx * ay)
    if abs(polygon_area) <= 1e-6:
        raise TypographyContractError(f"{label}: quad_norm polygon area must be non-zero.")

    return [[px, py] for px, py in quad_points]


def normalize_validation_policy(value: Any, *, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise TypographyContractError(f"{label}: validation_policy must be an object.")
    normalized = dict(DEFAULT_VALIDATION_POLICY)
    for key in ("zone_ocr", "unapproved_text"):
        if key not in value:
            continue
        raw = str(value[key]).strip()
        if raw not in ALLOWED_VALIDATION_POLICIES:
            raise TypographyContractError(
                f"{label}: validation_policy.{key} must be one of "
                f"{', '.join(sorted(ALLOWED_VALIDATION_POLICIES))}."
            )
        normalized[key] = raw
    return normalized


def normalize_shadow(value: Any, *, label: str) -> dict[str, Any]:
    if value is None:
        return {
            "enabled": False,
            "color": "#000000",
            "opacity": 0.0,
            "blur_px": 0.0,
            "offset_x": 0.0,
            "offset_y": 0.0,
        }
    if not isinstance(value, dict):
        raise TypographyContractError(f"{label}: shadow must be an object.")

    enabled = value.get("enabled", True)
    if not isinstance(enabled, bool):
        raise TypographyContractError(f"{label}: shadow.enabled must be a boolean.")
    color = str(value.get("color", "#000000")).strip()
    if not HEX_COLOR_RE.match(color):
        raise TypographyContractError(f"{label}: shadow.color must be a hex string like #RRGGBB or #RRGGBBAA.")
    opacity = value.get("opacity", 0.0)
    if not isinstance(opacity, (int, float)) or not (0.0 <= float(opacity) <= 1.0):
        raise TypographyContractError(f"{label}: shadow.opacity must be between 0.0 and 1.0.")
    blur_px = value.get("blur_px", 0.0)
    if not isinstance(blur_px, (int, float)) or float(blur_px) < 0.0:
        raise TypographyContractError(f"{label}: shadow.blur_px must be a non-negative number.")
    offset_x = value.get("offset_x", 0.0)
    offset_y = value.get("offset_y", 0.0)
    if not isinstance(offset_x, (int, float)) or not isinstance(offset_y, (int, float)):
        raise TypographyContractError(f"{label}: shadow offsets must be numeric.")
    return {
        "enabled": enabled,
        "color": color,
        "opacity": float(opacity),
        "blur_px": float(blur_px),
        "offset_x": float(offset_x),
        "offset_y": float(offset_y),
    }


def normalize_align_x(value: Any, *, label: str) -> str:
    raw = str(value).strip()
    if raw not in ALLOWED_ALIGN_X:
        raise TypographyContractError(f"{label}: align_x must be one of {', '.join(sorted(ALLOWED_ALIGN_X))}.")
    if raw == "left":
        return "start"
    if raw == "right":
        return "end"
    return raw


def normalize_align_y(value: Any, *, label: str) -> str:
    raw = str(value).strip()
    if raw not in ALLOWED_ALIGN_Y:
        raise TypographyContractError(f"{label}: align_y must be one of {', '.join(sorted(ALLOWED_ALIGN_Y))}.")
    if raw == "top":
        return "start"
    if raw in {"bottom"}:
        return "end"
    if raw == "middle":
        return "center"
    return raw


def normalize_optional_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def validate_expected_family_and_preset(
    *,
    family: str,
    preset: str,
    expected_family: str | None,
    expected_preset: str | None,
    label: str,
) -> None:
    if expected_family is not None and family and family != expected_family:
        raise TypographyContractError(f"{label}: family must match directory family {expected_family!r}.")
    if expected_preset is not None and preset and preset != expected_preset:
        raise TypographyContractError(f"{label}: preset must match base preset {expected_preset!r}.")


def format_label(path: Path | None) -> str:
    return str(path) if path else "<typography-intent>"
