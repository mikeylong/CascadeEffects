from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from inbox_app.agents_bridge import Context


SIGNAL_STYLE_SYSTEM_FILENAME = "cascade-effects-signal.style-system.json"
SIGNAL_STYLE_SYSTEM_SCHEMA_FILENAME = "cascade-effects-signal.style-system.schema.json"
GENERIC_FONT_FAMILIES = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"}
TYPE_SIZE_HEADING = "14px"
TYPE_SIZE_BODY = "12px"
TYPE_SIZE_OVERLINE = "11px"
TYPE_WEIGHT_HEADING = "700"
TYPE_WEIGHT_BODY = "400"
TYPE_WEIGHT_OVERLINE = "400"
CONSUMED_TOKEN_PATHS: tuple[tuple[str, ...], ...] = (
    ("semantic", "surface", "page"),
    ("semantic", "surface", "ink"),
    ("semantic", "surface", "thumbnailFrame"),
    ("semantic", "surface", "artifactPanel"),
    ("semantic", "surface", "artifactOverlay"),
    ("semantic", "text", "primaryOnLight"),
    ("semantic", "text", "secondaryOnLight"),
    ("semantic", "text", "primaryOnDark"),
    ("semantic", "text", "secondaryOnDark"),
    ("semantic", "accent", "primary"),
    ("semantic", "accent", "wash"),
    ("semantic", "accent", "failure"),
    ("semantic", "accent", "failureWash"),
    ("color", "alpha", "white12"),
    ("color", "alpha", "white24"),
    ("color", "alpha", "ink08"),
    ("color", "alpha", "ink12"),
    ("color", "alpha", "ink24"),
    ("fontFamily", "display"),
    ("fontFamily", "body"),
    ("fontFamily", "ui"),
    ("fontWeight", "display"),
    ("fontWeight", "regular"),
    ("fontWeight", "medium"),
    ("fontWeight", "semibold"),
    ("fontWeight", "bold"),
    ("size", "font", "caption"),
    ("size", "font", "label"),
    ("size", "font", "body"),
    ("size", "font", "bodyLg"),
    ("size", "font", "cardTitle"),
    ("size", "font", "section"),
    ("size", "font", "hero"),
    ("size", "tracking", "ui"),
    ("size", "tracking", "caps"),
    ("size", "tracking", "wide"),
    ("size", "radius", "sm"),
    ("size", "radius", "md"),
    ("size", "radius", "lg"),
    ("size", "radius", "pill"),
    ("size", "shadow", "none"),
    ("size", "shadow", "panelOffsetY"),
    ("size", "shadow", "panelBlur"),
    ("size", "shadow", "slabOffsetY"),
    ("size", "shadow", "slabBlur"),
    ("layout", "cardPadding"),
    ("layout", "panelGap"),
    ("layout", "sectionGap"),
    ("layout", "thumbnailSafeInsetX"),
    ("duration", "fast"),
    ("duration", "base"),
    ("duration", "slowPan"),
    ("cubicBezier", "standard"),
    ("cubicBezier", "reveal"),
    ("cubicBezier", "decelerate"),
    ("shadow", "panel"),
    ("shadow", "thumbnailSlab"),
)


@dataclass(frozen=True)
class BrandTheme:
    source_path: str = ""
    css_variables: dict[str, str] = field(default_factory=dict)
    dark_css_variables: dict[str, str] = field(default_factory=dict)
    warning: str = ""


def signal_style_system_path(context: Context) -> Path:
    return Path(context.channel["paths"]["web_root"]) / "brand" / SIGNAL_STYLE_SYSTEM_FILENAME


def signal_style_system_schema_path(context: Context) -> Path:
    return Path(context.channel["paths"]["web_root"]) / "brand" / SIGNAL_STYLE_SYSTEM_SCHEMA_FILENAME


def _lookup(node: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = node
    for part in path:
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Missing token path: {'.'.join(path)}")
        current = current[part]
    return current


def _resolve_value(tokens: dict[str, Any], raw: Any) -> Any:
    if isinstance(raw, str) and raw.startswith("{") and raw.endswith("}"):
        target = tuple(part for part in raw[1:-1].split(".") if part)
        target_node = _lookup(tokens, target)
        if not isinstance(target_node, dict) or "$value" not in target_node:
            raise KeyError(f"Token reference does not resolve to a value: {raw}")
        return _resolve_value(tokens, target_node["$value"])
    if isinstance(raw, dict):
        return {key: _resolve_value(tokens, value) for key, value in raw.items()}
    if isinstance(raw, list):
        return [_resolve_value(tokens, value) for value in raw]
    return raw


def _token_value(tokens: dict[str, Any], path: tuple[str, ...]) -> Any:
    node = _lookup(tokens, path)
    if not isinstance(node, dict) or "$value" not in node:
        raise KeyError(f"Token at {'.'.join(path)} does not expose $value")
    return _resolve_value(tokens, node["$value"])


def _format_float(value: float) -> str:
    rendered = f"{value:.3f}".rstrip("0").rstrip(".")
    return rendered or "0"


def _format_color(value: dict[str, Any], alpha_override: float | None = None) -> str:
    components = value.get("components")
    if not isinstance(components, list) or len(components) < 3:
        raise ValueError("Color token is missing RGB components")
    alpha = float(alpha_override if alpha_override is not None else value.get("alpha", 1.0))
    red, green, blue = (round(float(component) * 255) for component in components[:3])
    if alpha >= 0.999 and value.get("hex"):
        return str(value["hex"])
    return f"rgba({red}, {green}, {blue}, {_format_float(alpha)})"


def _format_dimension(value: dict[str, Any]) -> str:
    return f"{value['value']}{value['unit']}"


def _format_duration(value: dict[str, Any]) -> str:
    return f"{value['value']}{value['unit']}"


def _format_font_family(value: list[str]) -> str:
    rendered: list[str] = []
    for family in value:
        if family.lower() in GENERIC_FONT_FAMILIES:
            rendered.append(family)
        else:
            rendered.append(json.dumps(family))
    return ", ".join(rendered)


def _format_cubic_bezier(value: list[float]) -> str:
    return "cubic-bezier(" + ", ".join(_format_float(float(component)) for component in value) + ")"


def _format_shadow(value: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("offsetX", "offsetY", "blur", "spread", "color"):
        component = value[key]
        if isinstance(component, dict) and {"value", "unit"}.issubset(component):
            parts.append(_format_dimension(component))
            continue
        if isinstance(component, dict) and {"components", "alpha"}.issubset(component):
            parts.append(_format_color(component))
            continue
        parts.append(str(component))
    return " ".join(parts)


def _typography_css_variables(
    *,
    font_sans: str,
    font_ui: str,
    font_mono: str,
    font_display_family: str,
) -> dict[str, str]:
    return {
        "--font-sans": font_sans,
        "--font-ui": font_ui,
        "--font-mono": font_mono,
        "--font-display-family": font_display_family,
        "--font-display-weight": TYPE_WEIGHT_HEADING,
        "--font-card-weight": TYPE_WEIGHT_HEADING,
        "--font-section-weight": TYPE_WEIGHT_HEADING,
        "--font-ui-weight": TYPE_WEIGHT_BODY,
        "--font-tag-weight": TYPE_WEIGHT_OVERLINE,
        "--type-heading-size": TYPE_SIZE_HEADING,
        "--type-heading-weight": TYPE_WEIGHT_HEADING,
        "--type-body-size": TYPE_SIZE_BODY,
        "--type-body-weight": TYPE_WEIGHT_BODY,
        "--type-overline-size": TYPE_SIZE_OVERLINE,
        "--type-overline-weight": TYPE_WEIGHT_OVERLINE,
        "--font-caption": TYPE_SIZE_OVERLINE,
        "--font-label": TYPE_SIZE_BODY,
        "--font-body": TYPE_SIZE_BODY,
        "--font-body-lg": TYPE_SIZE_BODY,
        "--font-card": TYPE_SIZE_HEADING,
        "--font-section": TYPE_SIZE_HEADING,
        "--font-display": TYPE_SIZE_HEADING,
    }


def _fallback_css_variables() -> dict[str, str]:
    return {
        "--paper": "#ffffff",
        "--parchment": "#dde5ee",
        "--ink": "#0b1320",
        "--charcoal": "#576478",
        "--text-primary": "#0b1320",
        "--signal": "#b7ff4a",
        "--signal-soft": "rgba(183, 255, 74, 0.16)",
        "--alert": "#ff3b30",
        "--alert-soft": "rgba(255, 59, 48, 0.16)",
        "--white-12": "rgba(255, 255, 255, 0.12)",
        "--white-24": "rgba(255, 255, 255, 0.24)",
        "--white-60": "rgba(214, 220, 230, 1)",
        "--line": "rgba(11, 19, 32, 0.12)",
        "--line-strong": "rgba(11, 19, 32, 0.24)",
        "--muted": "rgba(11, 19, 32, 0.72)",
        "--muted-soft": "rgba(11, 19, 32, 0.72)",
        "--tracking-ui": "0.2px",
        "--tracking-caps": "0.8px",
        "--tracking-wide": "1.2px",
        "--radius-sm": "8px",
        "--radius-md": "16px",
        "--radius-lg": "20px",
        "--radius-pill": "999px",
        "--space-card": "24px",
        "--space-panel-gap": "24px",
        "--space-section-gap": "32px",
        "--space-content-inset": "56px",
        "--dur-fast": "120ms",
        "--dur-base": "220ms",
        "--dur-slow-pan": "900ms",
        "--ease-standard": "cubic-bezier(0.2, 0, 0, 1)",
        "--ease-emphasis": "cubic-bezier(0.16, 1, 0.3, 1)",
        "--ease-pan": "cubic-bezier(0, 0, 0.2, 1)",
        "--shadow-panel": "0px 8px 24px 0px rgba(11, 19, 32, 0.08)",
        "--shadow-focal": "0px 12px 32px 0px rgba(11, 19, 32, 0.24)",
        "--paper-soft": "rgba(255, 255, 255, 0.92)",
        "--paper-strong": "rgba(255, 255, 255, 0.98)",
        "--signal-wash": "rgba(183, 255, 74, 0.16)",
        "--stage-line": "rgba(255, 255, 255, 0.12)",
        "--stage-bg": "linear-gradient(180deg, #20314b 0%, #0b1320 100%)",
        "--body-bg": "linear-gradient(180deg, #ffffff 0%, #dde5ee 60%, #ffffff 100%)",
        "--text-inverse": "#ffffff",
        "--text-secondary-dark": "#d6dce6",
    } | _typography_css_variables(
        font_sans='"Inter", "Source Sans 3", "Helvetica Neue", Arial, sans-serif',
        font_ui='"Inter", "Source Sans 3", "Helvetica Neue", Arial, sans-serif',
        font_mono='"Inter", "Source Sans 3", "Helvetica Neue", Arial, sans-serif',
        font_display_family='"Bebas Neue", Anton, "Arial Narrow", Impact, sans-serif',
    )


def _fallback_dark_css_variables() -> dict[str, str]:
    return {
        "--paper": "#20314b",
        "--parchment": "#20314b",
        "--ink": "#0b1320",
        "--charcoal": "#576478",
        "--text-primary": "#ffffff",
        "--signal": "#b7ff4a",
        "--signal-soft": "rgba(183, 255, 74, 0.16)",
        "--alert": "#ff3b30",
        "--alert-soft": "rgba(255, 59, 48, 0.16)",
        "--white-12": "rgba(255, 255, 255, 0.12)",
        "--white-24": "rgba(255, 255, 255, 0.24)",
        "--white-60": "rgba(214, 220, 230, 1)",
        "--line": "rgba(255, 255, 255, 0.12)",
        "--line-strong": "rgba(255, 255, 255, 0.24)",
        "--muted": "rgba(214, 220, 230, 1)",
        "--muted-soft": "rgba(214, 220, 230, 1)",
        "--tracking-ui": "0.2px",
        "--tracking-caps": "0.8px",
        "--tracking-wide": "1.2px",
        "--radius-sm": "8px",
        "--radius-md": "16px",
        "--radius-lg": "20px",
        "--radius-pill": "999px",
        "--space-card": "24px",
        "--space-panel-gap": "24px",
        "--space-section-gap": "32px",
        "--space-content-inset": "56px",
        "--dur-fast": "120ms",
        "--dur-base": "220ms",
        "--dur-slow-pan": "900ms",
        "--ease-standard": "cubic-bezier(0.2, 0, 0, 1)",
        "--ease-emphasis": "cubic-bezier(0.16, 1, 0.3, 1)",
        "--ease-pan": "cubic-bezier(0, 0, 0.2, 1)",
        "--shadow-panel": "0px 8px 24px 0px rgba(11, 19, 32, 0.08)",
        "--shadow-focal": "0px 12px 32px 0px rgba(11, 19, 32, 0.24)",
        "--paper-soft": "rgba(87, 100, 120, 0.92)",
        "--paper-strong": "rgba(87, 100, 120, 0.98)",
        "--signal-wash": "rgba(183, 255, 74, 0.16)",
        "--stage-line": "rgba(255, 255, 255, 0.12)",
        "--stage-bg": "linear-gradient(180deg, #576478 0%, #0b1320 100%)",
        "--body-bg": "linear-gradient(180deg, #0b1320 0%, #20314b 60%, #0b1320 100%)",
        "--text-inverse": "#ffffff",
        "--text-secondary-dark": "#d6dce6",
    } | _typography_css_variables(
        font_sans='"Inter", "Source Sans 3", "Helvetica Neue", Arial, sans-serif',
        font_ui='"Inter", "Source Sans 3", "Helvetica Neue", Arial, sans-serif',
        font_mono='"Inter", "Source Sans 3", "Helvetica Neue", Arial, sans-serif',
        font_display_family='"Bebas Neue", Anton, "Arial Narrow", Impact, sans-serif',
    )


def _build_theme(tokens: dict[str, Any], source_path: Path) -> BrandTheme:
    page = _token_value(tokens, ("semantic", "surface", "page"))
    surface_ink = _token_value(tokens, ("semantic", "surface", "ink"))
    frame = _token_value(tokens, ("semantic", "surface", "thumbnailFrame"))
    stage = _token_value(tokens, ("semantic", "surface", "artifactPanel"))
    overlay = _token_value(tokens, ("semantic", "surface", "artifactOverlay"))
    text_primary = _token_value(tokens, ("semantic", "text", "primaryOnLight"))
    text_secondary = _token_value(tokens, ("semantic", "text", "secondaryOnLight"))
    text_inverse = _token_value(tokens, ("semantic", "text", "primaryOnDark"))
    text_secondary_dark = _token_value(tokens, ("semantic", "text", "secondaryOnDark"))
    signal = _token_value(tokens, ("semantic", "accent", "primary"))
    signal_wash = _token_value(tokens, ("semantic", "accent", "wash"))
    alert = _token_value(tokens, ("semantic", "accent", "failure"))
    alert_wash = _token_value(tokens, ("semantic", "accent", "failureWash"))
    white_12 = _token_value(tokens, ("color", "alpha", "white12"))
    white_24 = _token_value(tokens, ("color", "alpha", "white24"))
    line = _token_value(tokens, ("color", "alpha", "ink12"))
    line_strong = _token_value(tokens, ("color", "alpha", "ink24"))

    shared_css_variables = {
        "--ink": _format_color(surface_ink),
        "--charcoal": _format_color(overlay),
        "--signal": _format_color(signal),
        "--signal-soft": _format_color(signal_wash),
        "--alert": _format_color(alert),
        "--alert-soft": _format_color(alert_wash),
        "--white-12": _format_color(white_12),
        "--white-24": _format_color(white_24),
        "--white-60": _format_color(text_secondary_dark),
        "--line": _format_color(line),
        "--line-strong": _format_color(line_strong),
        "--muted": _format_color(text_secondary),
        "--muted-soft": _format_color(text_secondary),
        "--tracking-ui": _format_dimension(_token_value(tokens, ("size", "tracking", "ui"))),
        "--tracking-caps": _format_dimension(_token_value(tokens, ("size", "tracking", "caps"))),
        "--tracking-wide": _format_dimension(_token_value(tokens, ("size", "tracking", "wide"))),
        "--radius-sm": _format_dimension(_token_value(tokens, ("size", "radius", "sm"))),
        "--radius-md": _format_dimension(_token_value(tokens, ("size", "radius", "md"))),
        "--radius-lg": _format_dimension(_token_value(tokens, ("size", "radius", "lg"))),
        "--radius-pill": _format_dimension(_token_value(tokens, ("size", "radius", "pill"))),
        "--space-card": _format_dimension(_token_value(tokens, ("layout", "cardPadding"))),
        "--space-panel-gap": _format_dimension(_token_value(tokens, ("layout", "panelGap"))),
        "--space-section-gap": _format_dimension(_token_value(tokens, ("layout", "sectionGap"))),
        "--space-content-inset": _format_dimension(_token_value(tokens, ("layout", "thumbnailSafeInsetX"))),
        "--dur-fast": _format_duration(_token_value(tokens, ("duration", "fast"))),
        "--dur-base": _format_duration(_token_value(tokens, ("duration", "base"))),
        "--dur-slow-pan": _format_duration(_token_value(tokens, ("duration", "slowPan"))),
        "--ease-standard": _format_cubic_bezier(_token_value(tokens, ("cubicBezier", "standard"))),
        "--ease-emphasis": _format_cubic_bezier(_token_value(tokens, ("cubicBezier", "reveal"))),
        "--ease-pan": _format_cubic_bezier(_token_value(tokens, ("cubicBezier", "decelerate"))),
        "--shadow-panel": _format_shadow(_token_value(tokens, ("shadow", "panel"))),
        "--shadow-focal": _format_shadow(_token_value(tokens, ("shadow", "thumbnailSlab"))),
        "--text-inverse": _format_color(text_inverse),
        "--text-secondary-dark": _format_color(text_secondary_dark),
    } | _typography_css_variables(
        font_sans=_format_font_family(_token_value(tokens, ("fontFamily", "body"))),
        font_ui=_format_font_family(_token_value(tokens, ("fontFamily", "ui"))),
        font_mono=_format_font_family(_token_value(tokens, ("fontFamily", "ui"))),
        font_display_family=_format_font_family(_token_value(tokens, ("fontFamily", "display"))),
    )
    css_variables = shared_css_variables | {
        "--paper": _format_color(page),
        "--parchment": _format_color(frame),
        "--text-primary": _format_color(text_primary),
        "--line": _format_color(line),
        "--line-strong": _format_color(line_strong),
        "--muted": _format_color(text_secondary),
        "--muted-soft": _format_color(text_secondary),
        "--paper-soft": _format_color(page, alpha_override=0.92),
        "--paper-strong": _format_color(page, alpha_override=0.98),
        "--signal-wash": _format_color(signal_wash),
        "--stage-line": _format_color(white_12),
        "--stage-bg": f"linear-gradient(180deg, {_format_color(stage)} 0%, {_format_color(surface_ink)} 100%)",
        "--body-bg": f"linear-gradient(180deg, {_format_color(page)} 0%, {_format_color(frame)} 60%, {_format_color(page)} 100%)",
    }
    dark_css_variables = shared_css_variables | {
        "--paper": _format_color(stage),
        "--parchment": _format_color(stage),
        "--text-primary": _format_color(text_inverse),
        "--line": _format_color(white_12),
        "--line-strong": _format_color(white_24),
        "--muted": _format_color(text_secondary_dark),
        "--muted-soft": _format_color(text_secondary_dark),
        "--paper-soft": _format_color(overlay, alpha_override=0.92),
        "--paper-strong": _format_color(overlay, alpha_override=0.98),
        "--signal-wash": _format_color(signal_wash),
        "--stage-line": _format_color(white_12),
        "--stage-bg": f"linear-gradient(180deg, {_format_color(overlay)} 0%, {_format_color(surface_ink)} 100%)",
        "--body-bg": f"linear-gradient(180deg, {_format_color(surface_ink)} 0%, {_format_color(stage)} 60%, {_format_color(surface_ink)} 100%)",
    }
    return BrandTheme(source_path=str(source_path), css_variables=css_variables, dark_css_variables=dark_css_variables)


def load_signal_brand_theme(context: Context) -> BrandTheme:
    source_path = signal_style_system_path(context)
    try:
        tokens = json.loads(source_path.read_text(encoding="utf-8"))
        for path in CONSUMED_TOKEN_PATHS:
            _token_value(tokens, path)
        return _build_theme(tokens, source_path)
    except Exception as exc:  # pragma: no cover - exercised through server fallback tests
        warning = f"Brand token fallback in use. Unable to load signal style-system tokens from {source_path}: {exc}"
        return BrandTheme(
            source_path=str(source_path),
            css_variables=_fallback_css_variables(),
            dark_css_variables=_fallback_dark_css_variables(),
            warning=warning,
        )


# Backward-compatible aliases for the existing review server integration.
archive_tokens_path = signal_style_system_path
archive_schema_path = signal_style_system_schema_path
load_archive_brand_theme = load_signal_brand_theme


__all__ = [
    "BrandTheme",
    "CONSUMED_TOKEN_PATHS",
    "SIGNAL_STYLE_SYSTEM_FILENAME",
    "SIGNAL_STYLE_SYSTEM_SCHEMA_FILENAME",
    "archive_schema_path",
    "archive_tokens_path",
    "load_archive_brand_theme",
    "load_signal_brand_theme",
    "signal_style_system_path",
    "signal_style_system_schema_path",
]
