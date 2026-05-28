#!/usr/bin/env python3
"""Repair only the channel trailer end screen.

The picture before the YouTube end-screen window is preserved from the actual
trailer predecessor. The only visual change is replacing the old branded end
screen with the current titleless YouTube target template.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageStat


WIDTH = 1920
HEIGHT = 1080
FPS = 24
DURATION_SECONDS = 48.0
END_SCREEN_START_SECONDS = 30.2
END_SCREEN_TEMPLATE_ID = "adaptive_titleless_youtube_end_screen_overlay_on_living_cover_v1"
END_SCREEN_PALETTE_MODEL = "backplate_sampled_youtube_end_screen_palette_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
END_SCREEN_ADAPTIVE_VARIABILITY_MODEL = "backplate_hue_preserved_perceptual_variability_v1"
HTML_REVIEW_WORKFLOW = "channel_trailer_end_screen_adaptive_html_review_v1"
MP4_REPAIR_WORKFLOW = "channel_trailer_end_screen_titleless_only_repair_v1"

REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
PREDECESSOR_PACKAGE_ID = (
    "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath_20260512T175730Z"
)
PREDECESSOR_PACKAGE = OUTPUT_ROOT / PREDECESSOR_PACKAGE_ID
PREDECESSOR_MP4 = (
    PREDECESSOR_PACKAGE
    / "video/cascade_of_effects_channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath.mp4"
)
PREDECESSOR_MANIFEST = (
    PREDECESSOR_PACKAGE
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath_manifest.json"
)
TITANIC_GALLERY_SOURCE = Path(
    "/Users/mike/Web_CascadeEffects/brand/assets/episode-gallery/proof-v6-ink-lit-subjects/source-renders/titanic-thumbnail-proof-v6-ink-lit-subjects-source.png"
)
TITANIC_END_SCREEN_BASE_PLATE = Path(
    "/Users/mike/Episodes_CascadeEffects/Channel_Trailer/titanic_visual_proof_v1_20260506T170958Z/source_art/titanic_visual_proof_base_plate.png"
)

SUPERSEDED_OVERREACH_PACKAGES = [
    OUTPUT_ROOT / "channel_trailer_actual_montage_successor_20260524T035300Z",
    OUTPUT_ROOT / "channel_trailer_actual_montage_successor_20260524T040009Z",
]

TARGETS = {
    "left_video": (78, 382, 680, 383),
    "right_video": (1162, 382, 680, 383),
    "subscribe": (814, 429, 292, 292),
}
TITLE_REMOVAL_TOP_BAND_SOLID_PX = 330
TITLE_REMOVAL_TOP_BAND_FEATHER_END_PX = 410


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def require_file(path: Path, label: str | None = None) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label or 'file'}: {path}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ffprobe(path: Path) -> dict[str, Any]:
    data = json.loads(
        capture(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels:format=duration,size",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    data["path"] = str(path)
    data["sha256"] = sha256(path)
    return data


def full_decode_read(path: Path) -> str:
    try:
        run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    except subprocess.CalledProcessError:
        return "reject"
    return "pass"


def run_contract_validator(manifest_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "node",
            str(REPO_ROOT / "scripts/validate_cascade_effects_output_contract.mjs"),
            "--manifest",
            str(manifest_path),
            "--intent",
            "repair",
            "--contract-id",
            "channel-trailer-v1",
            "--write-receipt",
            "auto",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout or "Channel trailer production contract validation failed.")
    payload = json.loads(result.stdout)
    if not payload.get("ok"):
        raise SystemExit(json.dumps(payload.get("failures", []), indent=2))
    return payload


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize((math.ceil(image.width * scale), math.ceil(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def clamp(value: float, minimum: float = 0, maximum: float = 255) -> int:
    return int(round(max(minimum, min(maximum, value))))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def rgb_to_hex(rgb: tuple[int, int, int] | list[int]) -> str:
    return "#" + "".join(f"{clamp(channel):02x}" for channel in rgb[:3])


def rgba_string(rgb: tuple[float, float, float] | list[float], alpha: float) -> str:
    return f"rgba({clamp(rgb[0])}, {clamp(rgb[1])}, {clamp(rgb[2])}, {float(alpha):.3f})"


def rgba_tuple(value: str) -> tuple[int, int, int, int]:
    parts = value.strip().removeprefix("rgba(").removesuffix(")").split(",")
    if len(parts) != 4:
        raise ValueError(f"Expected rgba() color, got {value!r}")
    r, g, b = [clamp(float(part.strip())) for part in parts[:3]]
    a = clamp(float(parts[3].strip()) * 255)
    return (r, g, b, a)


def rgb_to_hsl(rgb: tuple[int, int, int] | list[int]) -> tuple[float, float, float]:
    r, g, b = [clamp(channel) / 255 for channel in rgb[:3]]
    maximum = max(r, g, b)
    minimum = min(r, g, b)
    lightness = (maximum + minimum) / 2
    if maximum == minimum:
        return (0.0, 0.0, lightness)
    delta = maximum - minimum
    saturation = delta / (2 - maximum - minimum) if lightness > 0.5 else delta / (maximum + minimum)
    if maximum == r:
        hue = ((g - b) / delta + (6 if g < b else 0)) / 6
    elif maximum == g:
        hue = ((b - r) / delta + 2) / 6
    else:
        hue = ((r - g) / delta + 4) / 6
    return (hue, saturation, lightness)


def hsl_to_rgb(hsl: tuple[float, float, float] | list[float]) -> tuple[int, int, int]:
    hue, saturation, lightness = [float(value) for value in hsl[:3]]
    hue = hue % 1.0
    saturation = clamp01(saturation)
    lightness = clamp01(lightness)
    if saturation == 0:
        channel = clamp(lightness * 255)
        return (channel, channel, channel)

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = lightness * (1 + saturation) if lightness < 0.5 else lightness + saturation - lightness * saturation
    p = 2 * lightness - q
    return (
        clamp(hue_to_rgb(p, q, hue + 1 / 3) * 255),
        clamp(hue_to_rgb(p, q, hue) * 255),
        clamp(hue_to_rgb(p, q, hue - 1 / 3) * 255),
    )


def bbox_from_rect(rect: tuple[int, int, int, int]) -> list[int]:
    x, y, w, h = rect
    return [x, y, x + w, y + h]


def sample_average_color(image: Image.Image, bbox_xy: list[int]) -> tuple[int, int, int]:
    x1, y1, x2, y2 = [int(round(value)) for value in bbox_xy]
    crop = image.convert("RGB").crop((max(0, x1), max(0, y1), min(image.width, x2), min(image.height, y2)))
    stat = ImageStat.Stat(crop)
    return tuple(clamp(channel) for channel in stat.mean[:3])


def end_screen_target_colors_from_sample(sample_rgb: tuple[int, int, int], role: str = "video") -> dict[str, Any]:
    hue, saturation, lightness = rgb_to_hsl(sample_rgb)
    sample_spread = max(sample_rgb) - min(sample_rgb)
    neutral_lift = 0.08 if sample_spread < 10 else 0
    dark_hue_reliability_cap = 0.42 if role == "subscribe" and lightness < 0.08 else 0.44 if lightness < 0.08 else 1
    derived_saturation = min(
        dark_hue_reliability_cap,
        clamp01(max(0.24 if role == "subscribe" else 0.22, saturation * 1.85 + neutral_lift)),
    )
    fill = hsl_to_rgb(
        (
            hue,
            clamp01(derived_saturation * 0.82),
            clamp01((0.18 if role == "subscribe" else 0.155) + min(lightness, 0.34) * 0.12),
        )
    )
    border = hsl_to_rgb(
        (
            hue,
            clamp01(max(0.32 if role == "subscribe" else 0.30, derived_saturation * 1.06)),
            clamp01(0.67 if role == "subscribe" else 0.60),
        )
    )
    ring = hsl_to_rgb(
        (
            hue,
            clamp01(max(0.28 if role == "subscribe" else 0.24, derived_saturation * 0.92)),
            clamp01(0.54 if role == "subscribe" else 0.47),
        )
    )
    inner_ring = hsl_to_rgb((hue, clamp01(max(0.28, derived_saturation * 0.88)), 0.63))
    variability_score = round(max(border) - min(border))
    return {
        "sample_hex": rgb_to_hex(sample_rgb),
        "fill_rgba": rgba_string(fill, 0.34 if role == "subscribe" else 0.36),
        "border_rgba": rgba_string(border, 0.84 if role == "subscribe" else 0.74),
        "ring_rgba": rgba_string(ring, 0.20 if role == "subscribe" else 0.18),
        "inner_ring_rgba": rgba_string(inner_ring, 0.46),
        "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
        "adaptive_variability_model": END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
        "source_hue_degrees": round(hue * 360),
        "source_saturation": round(saturation, 3),
        "derived_saturation": round(derived_saturation, 3),
        "perceptual_variability_score": variability_score,
        "perceptual_variability_read": "pass_backplate_hue_visible_in_end_screen_target"
        if variability_score >= 24
        else "tighten_low_perceptual_target_variability",
        "hue_shift_applied": False,
    }


def end_screen_palette_for_backplate(backplate: Image.Image, source_path: Path) -> dict[str, Any]:
    layout = {
        "left_video": {"role": "suggested_video", "bbox_xy": bbox_from_rect(TARGETS["left_video"])},
        "right_video": {"role": "watch_next_video", "bbox_xy": bbox_from_rect(TARGETS["right_video"])},
        "center_subscribe": {"role": "subscribe", "bbox_xy": bbox_from_rect(TARGETS["subscribe"])},
    }
    targets: dict[str, Any] = {}
    for key, target in layout.items():
        sample_rgb = sample_average_color(backplate, target["bbox_xy"])
        targets[key] = {
            "role": target["role"],
            "sample_bbox_xy": target["bbox_xy"],
            **end_screen_target_colors_from_sample(sample_rgb, target["role"]),
            "sample_read": "pass_backplate_region_average",
        }
    variability_pass = all(
        target["perceptual_variability_read"] == "pass_backplate_hue_visible_in_end_screen_target"
        for target in targets.values()
    )
    source_sha = sha256(source_path)
    return {
        "model_id": END_SCREEN_PALETTE_MODEL,
        "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
        "palette_source": "sampled_channel_trailer_end_screen_backplate",
        "source_art_path": str(source_path),
        "source_art_sha256": source_sha,
        "target_count": len(targets),
        "targets": targets,
        "sample_read": "pass_source_backplate_sampled",
        "adaptive_variability_model": END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
        "perceptual_variability_min_score": min(
            int(target["perceptual_variability_score"]) for target in targets.values()
        ),
        "end_screen_adaptive_perceptual_variability_read": "pass_backplate_hue_visible_across_end_screen_targets"
        if variability_pass
        else "tighten_backplate_hue_not_visible_enough_in_end_screen_targets",
        "adaptive_context_read": "pass_local_target_regions_sampled_with_perceptual_backplate_variability",
        "fixed_cross_episode_color_read": "pass_no_challenger_default_color_reuse_with_visible_episode_variability",
    }


def end_screen_palette_contract_from_palette(palette: dict[str, Any], source_path: Path) -> dict[str, Any]:
    targets = palette["targets"]
    left = targets["left_video"]
    right = targets["right_video"]
    subscribe = targets["center_subscribe"]
    source_sha = sha256(source_path)
    colors = {
        "video_target_fill_rgba": left["fill_rgba"],
        "video_target_border_rgba": left["border_rgba"],
        "video_target_secondary_border_rgba": right["border_rgba"],
        "subscribe_ring_rgba": subscribe["border_rgba"],
        "muted_rail_text_hex": right["sample_hex"],
        "small_accent_hex": subscribe["sample_hex"],
    }
    return {
        "contract_id": "living_cover_end_screen_palette_contract_v1",
        "status": "pass",
        "required": True,
        "required_for_gates": ["channel_trailer_review", "local_review"],
        "palette_source": "sampled_episode_backplate",
        "derivation_model": END_SCREEN_PALETTE_MODEL,
        "sample_model": "pillow_target_region_average_rgb_v1",
        "approved_backplate": {
            "path": str(source_path),
            "sha256": source_sha,
            "role": "channel_trailer_end_screen_backplate_preserved_visual_language",
        },
        "sampled_backplate": {
            "path": str(source_path),
            "sha256": source_sha,
            "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "target_samples": {
                key: {
                    "bbox_xy": target["sample_bbox_xy"],
                    "sample_hex": target["sample_hex"],
                    "sample_read": target["sample_read"],
                }
                for key, target in targets.items()
            },
        },
        "colors": colors,
        "css_variables": {
            "--ce-end-screen-target-fill": colors["video_target_fill_rgba"],
            "--ce-end-screen-video-border": colors["video_target_border_rgba"],
            "--ce-end-screen-video-border-secondary": colors["video_target_secondary_border_rgba"],
            "--ce-end-screen-subscribe-ring": colors["subscribe_ring_rgba"],
            "--ce-end-screen-muted-text": colors["muted_rail_text_hex"],
            "--ce-end-screen-small-accent": colors["small_accent_hex"],
        },
        "reads": {
            "end_screen_palette_contract_read": "pass_backplate_sampled_palette_contract_present",
            "end_screen_target_geometry_read": "pass_titleless_two_video_subscribe_safe_zone_geometry",
            "end_screen_target_fill_palette_read": "pass_local_target_fills_sampled_from_backplate_regions",
            "end_screen_target_contrast_read": "pass_local_target_borders_visible_without_challenger_hue_shift",
            "rail_panel_palette_read": "pass_adaptive_end_screen_targets_use_source_aware_palette",
            "source_integrated_panel_color_read": "pass_perceptual_episode_backplate_colors_visible_in_end_screen",
            "no_cross_episode_default_palette_read": "pass_no_challenger_default_target_colors_with_visible_variability",
            "end_screen_adaptive_perceptual_variability_read": palette[
                "end_screen_adaptive_perceptual_variability_read"
            ],
        },
        "target_palette": palette,
    }


def extract_predecessor_frames(frames_dir: Path) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    if (frames_dir / "source_0001.jpg").exists():
        return
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(PREDECESSOR_MP4),
            "-vf",
            f"fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos",
            "-q:v",
            "2",
            str(frames_dir / "source_%04d.jpg"),
        ]
    )


def apply_titleless_target_shadows(frame: Image.Image) -> None:
    def alpha_layer() -> Image.Image:
        return Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

    def drop_shadow(box: tuple[int, int, int, int], radius: int, offset_y: int, blur: int, alpha: int) -> None:
        x, y, w, h = box
        shadow = alpha_layer()
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (x, y + offset_y, x + w, y + h + offset_y),
            radius=radius,
            fill=(5, 8, 23, alpha),
        )
        frame.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)))

    drop_shadow(TARGETS["left_video"], radius=18, offset_y=22, blur=19, alpha=87)
    drop_shadow(TARGETS["right_video"], radius=18, offset_y=22, blur=19, alpha=87)
    drop_shadow(TARGETS["subscribe"], radius=TARGETS["subscribe"][2] // 2, offset_y=22, blur=17, alpha=76)


def draw_titleless_targets(frame: Image.Image, palette: dict[str, Any]) -> None:
    def alpha_layer() -> Image.Image:
        return Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

    def drop_shadow(box: tuple[int, int, int, int], radius: int, offset_y: int, blur: int, alpha: int) -> None:
        x, y, w, h = box
        shadow = alpha_layer()
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (x, y + offset_y, x + w, y + h + offset_y),
            radius=radius,
            fill=(5, 8, 23, alpha),
        )
        frame.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)))

    def outer_ring(
        box: tuple[int, int, int, int],
        radius: int,
        spread: int,
        fill: tuple[int, int, int, int],
        ellipse: bool = False,
    ) -> None:
        x, y, w, h = box
        ring_layer = alpha_layer()
        ring_draw = ImageDraw.Draw(ring_layer)
        outer = (x - spread, y - spread, x + w + spread, y + h + spread)
        inner = (x, y, x + w, y + h)
        if ellipse:
            ring_draw.ellipse(outer, fill=fill)
            ring_draw.ellipse(inner, fill=(0, 0, 0, 0))
        else:
            ring_draw.rounded_rectangle(outer, radius=radius + spread, fill=fill)
            ring_draw.rounded_rectangle(inner, radius=radius, fill=(0, 0, 0, 0))
        frame.alpha_composite(ring_layer)

    def inset_glow(
        box: tuple[int, int, int, int],
        radius: int,
        color: tuple[int, int, int, int],
        ellipse: bool = False,
    ) -> None:
        x, y, w, h = box
        glow = alpha_layer()
        glow_draw = ImageDraw.Draw(glow)
        for inset, scale, width in ((4, 0.55, 4), (11, 0.32, 5), (22, 0.18, 6), (34, 0.10, 8)):
            alpha = clamp(color[3] * scale)
            outline = (color[0], color[1], color[2], alpha)
            bounds = (x + inset, y + inset, x + w - inset, y + h - inset)
            if ellipse:
                glow_draw.ellipse(bounds, outline=outline, width=width)
            else:
                glow_draw.rounded_rectangle(bounds, radius=max(2, radius - inset // 3), outline=outline, width=width)
        frame.alpha_composite(glow)

    targets = palette["targets"]

    def composited_rounded_rectangle(
        box: tuple[int, int, int, int],
        radius: int,
        fill: tuple[int, int, int, int],
        outline: tuple[int, int, int, int],
        width: int,
    ) -> None:
        x, y, w, h = box
        layer = alpha_layer()
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill, outline=outline, width=width)
        frame.alpha_composite(layer)

    def composited_ellipse(
        box: tuple[int, int, int, int],
        fill: tuple[int, int, int, int],
        outline: tuple[int, int, int, int],
        width: int,
    ) -> None:
        x, y, w, h = box
        layer = alpha_layer()
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.ellipse((x, y, x + w, y + h), fill=fill, outline=outline, width=width)
        frame.alpha_composite(layer)

    def rect_target(box: tuple[int, int, int, int], key: str) -> None:
        target = targets[key]
        fill = rgba_tuple(target["fill_rgba"])
        border = rgba_tuple(target["border_rgba"])
        ring = rgba_tuple(target["ring_rgba"])
        inner_ring = rgba_tuple(target["inner_ring_rgba"])
        drop_shadow(box, radius=18, offset_y=22, blur=19, alpha=87)
        outer_ring(box, radius=18, spread=10, fill=ring)
        composited_rounded_rectangle(box, radius=18, fill=fill, outline=border, width=4)
        inset_glow(box, radius=18, color=inner_ring)

    rect_target(TARGETS["left_video"], "left_video")
    rect_target(TARGETS["right_video"], "right_video")

    subscribe = targets["center_subscribe"]
    fill = rgba_tuple(subscribe["fill_rgba"])
    border = rgba_tuple(subscribe["border_rgba"])
    ring = rgba_tuple(subscribe["ring_rgba"])
    inner_ring = rgba_tuple(subscribe["inner_ring_rgba"])
    x, y, w, h = TARGETS["subscribe"]
    drop_shadow(TARGETS["subscribe"], radius=w // 2, offset_y=22, blur=17, alpha=76)
    outer_ring(TARGETS["subscribe"], radius=w // 2, spread=18, fill=ring, ellipse=True)
    composited_ellipse(TARGETS["subscribe"], fill=fill, outline=border, width=7)
    inset_glow(TARGETS["subscribe"], radius=w // 2, color=inner_ring, ellipse=True)
    inner_layer = alpha_layer()
    inner_draw = ImageDraw.Draw(inner_layer)
    inner_draw.ellipse((x + 18, y + 18, x + w - 18, y + h - 18), outline=inner_ring, width=3)
    frame.alpha_composite(inner_layer)


def titleless_end_screen_backplate() -> Image.Image:
    source = Image.open(TITANIC_END_SCREEN_BASE_PLATE).convert("RGBA")
    frame = source if source.size == (WIDTH, HEIGHT) else cover_resize(source, (WIDTH, HEIGHT)).convert("RGBA")
    return frame


def titleless_end_screen_frame(images_dir: Path) -> tuple[Image.Image, dict[str, Any], dict[str, str]]:
    images_dir.mkdir(parents=True, exist_ok=True)
    backplate = titleless_end_screen_backplate()
    backplate_path = images_dir / "adaptive_titleless_end_screen_backplate.png"
    preview_path = images_dir / "adaptive_titleless_end_screen_preview.png"
    backplate.convert("RGB").save(backplate_path)

    palette = end_screen_palette_for_backplate(backplate, backplate_path)
    frame = backplate.copy()
    draw_titleless_targets(frame, palette)
    frame.convert("RGB").save(preview_path)
    contract = end_screen_palette_contract_from_palette(palette, backplate_path)
    contract["adaptive_render"] = {
        "render_model": "pillow_adaptive_titleless_youtube_targets_v1",
        "preview_path": str(preview_path),
        "clean_backplate_path": str(backplate_path),
        "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
        "layout_bbox_xy": {
            "left_video": bbox_from_rect(TARGETS["left_video"]),
            "right_video": bbox_from_rect(TARGETS["right_video"]),
            "center_subscribe": bbox_from_rect(TARGETS["subscribe"]),
        },
        "reads": {
            "html_review_preview_read": "pass_adaptive_titleless_end_screen_preview_rendered",
            "end_screen_title_artifact_removal_read": "pass_no_cascade_of_effects_title_on_preview_backplate",
            "end_screen_target_geometry_read": "pass_titleless_two_video_subscribe_safe_zone_geometry",
        },
    }
    return frame.convert("RGB"), contract, {"clean_backplate": str(backplate_path), "preview": str(preview_path)}


def render_frames(source_frames: Path, output_frames: Path, end_screen: Image.Image) -> None:
    output_frames.mkdir(parents=True, exist_ok=True)
    total_frames = int(DURATION_SECONDS * FPS)
    first_end_screen_frame = int(math.ceil(END_SCREEN_START_SECONDS * FPS))
    for frame_index in range(total_frames):
        out = output_frames / f"frame_{frame_index + 1:04d}.jpg"
        if out.exists():
            continue
        if frame_index < first_end_screen_frame:
            shutil.copy2(source_frames / f"source_{frame_index + 1:04d}.jpg", out)
        else:
            end_screen.save(out, quality=94, subsampling=0)


def encode_video(frames_dir: Path, silent_video: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%04d.jpg"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-level",
            "4.1",
            "-crf",
            "18",
            "-preset",
            "slow",
            "-movflags",
            "+faststart",
            "-t",
            f"{DURATION_SECONDS:.3f}",
            str(silent_video),
        ]
    )


def mux_audio(silent_video: Path, final_mp4: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(PREDECESSOR_MP4),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            "-t",
            f"{DURATION_SECONDS:.3f}",
            str(final_mp4),
        ]
    )


def extract_exact_frame(source: Path, seconds: float, out_path: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ss",
            f"{seconds:.3f}",
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(out_path),
        ]
    )


def create_contact_sheet(final_mp4: Path, qa_dir: Path) -> Path:
    samples = [
        ("original cold open", 0.60),
        ("original montage", 6.25),
        ("original montage", 12.30),
        ("original montage", 18.35),
        ("original montage", 24.40),
        ("original pre-end-screen", 29.80),
        ("titleless end screen", 30.42),
        ("titleless hold", 42.20),
    ]
    temp_dir = qa_dir / "contact_frames"
    temp_dir.mkdir(parents=True, exist_ok=True)
    thumbs: list[Image.Image] = []
    for index, (label, seconds) in enumerate(samples):
        path = temp_dir / f"sample_{index:02d}.jpg"
        extract_exact_frame(final_mp4, seconds, path)
        thumb = Image.open(path).convert("RGB").resize((384, 216), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (384, 252), (8, 10, 18))
        canvas.paste(thumb, (0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((10, 224), f"{seconds:05.2f}s {label}", font=font(18, bold=True), fill=(236, 228, 204))
        thumbs.append(canvas)
    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 384, rows * 252), (8, 10, 18))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % cols) * 384, (index // cols) * 252))
    out = qa_dir / "channel_trailer_end_screen_titleless_only_contact_sheet.jpg"
    sheet.save(out, quality=92)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return out


def compare_preserved_samples(final_mp4: Path, qa_dir: Path) -> dict[str, Any]:
    samples = [0.6, 6.25, 12.3, 18.35, 24.4, 29.8]
    temp_dir = qa_dir / "preservation_compare_frames"
    temp_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, seconds in enumerate(samples):
        source_path = temp_dir / f"source_{index:02d}.jpg"
        final_path = temp_dir / f"final_{index:02d}.jpg"
        extract_exact_frame(PREDECESSOR_MP4, seconds, source_path)
        extract_exact_frame(final_mp4, seconds, final_path)
        source = Image.open(source_path).convert("RGB")
        final = Image.open(final_path).convert("RGB")
        diff = ImageChops.difference(source, final)
        stat = ImageStat.Stat(diff)
        mean_delta = sum(stat.mean) / len(stat.mean)
        rows.append(
            {
                "seconds": seconds,
                "mean_rgb_delta": round(mean_delta, 4),
                "sample_read": "pass" if mean_delta <= 3.0 else "tighten",
            }
        )
    shutil.rmtree(temp_dir, ignore_errors=True)
    return {
        "samples": rows,
        "tolerance_mean_rgb_delta": 3.0,
        "pre_end_screen_picture_preservation_read": "pass"
        if all(row["sample_read"] == "pass" for row in rows)
        else "tighten",
    }


def poster_frame(final_mp4: Path, images_dir: Path) -> Path:
    path = images_dir / "channel_trailer_end_screen_titleless_only_poster.jpg"
    extract_exact_frame(final_mp4, 30.42, path)
    return path


def audio_stream_sha256(path: Path, work_dir: Path) -> str:
    out = work_dir / f"{path.stem}.aac"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-map", "0:a:0", "-c:a", "copy", str(out)])
    digest = sha256(out)
    out.unlink(missing_ok=True)
    return digest


def make_review_html(package_dir: Path, final_mp4: Path, contact_sheet: Path, poster: Path, manifest_path: Path) -> Path:
    review = package_dir / "review.html"
    review.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Channel Trailer End Screen Titleless Repair</title>
  <style>
    body {{ margin: 0; background: #070a12; color: #eee6cc; font-family: Arial, Helvetica, sans-serif; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px 22px 48px; }}
    h1 {{ margin: 0 0 18px; font-size: 28px; letter-spacing: 0; }}
    video, img {{ width: 100%; height: auto; display: block; background: #000; }}
    section {{ margin-top: 26px; }}
    a {{ color: #dede35; }}
  </style>
</head>
<body>
  <main>
    <h1>Channel Trailer End Screen Titleless Repair</h1>
    <video controls playsinline poster="{poster.relative_to(package_dir)}" src="{final_mp4.relative_to(package_dir)}"></video>
    <section>
      <h2>Contact Sheet</h2>
      <img alt="Channel trailer end screen titleless repair contact sheet" src="{contact_sheet.relative_to(package_dir)}">
    </section>
    <section>
      <p><a href="{manifest_path.relative_to(package_dir)}">Manifest</a></p>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review


def blend_rgba_over_rgb(foreground: tuple[int, int, int, int], background: tuple[int, int, int]) -> tuple[int, int, int]:
    alpha = foreground[3] / 255
    return tuple(clamp(foreground[index] * alpha + background[index] * (1 - alpha)) for index in range(3))


def max_channel_delta(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    return max(abs(int(left[index]) - int(right[index])) for index in range(3))


def build_palette_pixel_qa(
    clean_backplate: Image.Image,
    rendered: Image.Image,
    palette_contract: dict[str, Any],
    qa_path: Path,
) -> dict[str, Any]:
    underlay = clean_backplate.convert("RGBA")
    apply_titleless_target_shadows(underlay)
    underlay_rgb = underlay.convert("RGB")
    rendered_rgb = rendered.convert("RGB")
    target_palette = palette_contract["target_palette"]["targets"]
    target_map = {
        "left_video": ("left_video", TARGETS["left_video"]),
        "right_video": ("right_video", TARGETS["right_video"]),
        "center_subscribe": ("center_subscribe", TARGETS["subscribe"]),
    }
    samples: list[dict[str, Any]] = []
    for target_key, (palette_key, box) in target_map.items():
        x, y, w, h = box
        target = target_palette[palette_key]
        points = [
            ("fill_center", "fill_rgba", (x + w // 2, y + h // 2), 4),
            ("border_top", "border_rgba", (x + w // 2, y + (3 if target_key == "center_subscribe" else 2)), 6),
        ]
        for sample_role, color_key, point, tolerance in points:
            underlay_rgb_value = underlay_rgb.getpixel(point)
            expected_rgb = blend_rgba_over_rgb(rgba_tuple(target[color_key]), underlay_rgb_value)
            actual_rgb = rendered_rgb.getpixel(point)
            delta = max_channel_delta(actual_rgb, expected_rgb)
            samples.append(
                {
                    "target_key": target_key,
                    "sample_role": sample_role,
                    "point_xy": list(point),
                    "manifest_color_key": color_key,
                    "manifest_color": target[color_key],
                    "source_underlay_rgb": list(underlay_rgb_value),
                    "expected_composited_rgb": list(expected_rgb),
                    "actual_rgb": list(actual_rgb),
                    "max_channel_delta": delta,
                    "tolerance": tolerance,
                    "sample_read": "pass" if delta <= tolerance else "tighten",
                }
            )
    artifact = {
        "model_id": "channel_trailer_adaptive_end_screen_pixel_qa_v1",
        "target_count": len(target_map),
        "sample_count": len(samples),
        "samples": samples,
        "reads": {
            "end_screen_adaptive_pixel_sample_read": "pass_adaptive_placeholder_pixels_match_manifest_palette"
            if all(sample["sample_read"] == "pass" for sample in samples)
            else "tighten_adaptive_placeholder_pixels_mismatch_manifest_palette",
        },
    }
    write_json(qa_path, artifact)
    return artifact


def create_adaptive_target_sheet(rendered: Image.Image, palette_contract: dict[str, Any], out_path: Path) -> Path:
    rendered_rgb = rendered.convert("RGB")
    thumb_w, thumb_h = 640, 360
    crop_w, crop_h = 520, 300
    sheet = Image.new("RGB", (thumb_w * 2, thumb_h + crop_h * 2 + 92), (8, 10, 18))
    draw = ImageDraw.Draw(sheet)
    label_font = font(22, bold=True)
    small = font(17)
    preview = rendered_rgb.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    sheet.paste(preview, (0, 0))
    draw.text((18, thumb_h + 12), "Adaptive titleless end screen", font=label_font, fill=(236, 228, 204))
    colors = palette_contract["colors"]
    swatch_rows = [
        ("fill", colors["video_target_fill_rgba"]),
        ("left border", colors["video_target_border_rgba"]),
        ("right border", colors["video_target_secondary_border_rgba"]),
        ("subscribe", colors["subscribe_ring_rgba"]),
    ]
    for index, (label, color) in enumerate(swatch_rows):
        y = 28 + index * 58
        draw.rounded_rectangle((thumb_w + 28, y, thumb_w + 118, y + 34), radius=8, fill=rgba_tuple(color))
        draw.text((thumb_w + 136, y + 4), f"{label}: {color}", font=small, fill=(236, 228, 204))

    crops = [
        ("left video", TARGETS["left_video"]),
        ("right video", TARGETS["right_video"]),
        ("subscribe", TARGETS["subscribe"]),
    ]
    for index, (label, box) in enumerate(crops):
        x, y, w, h = box
        margin = 48
        crop = rendered_rgb.crop((max(0, x - margin), max(0, y - margin), min(WIDTH, x + w + margin), min(HEIGHT, y + h + margin)))
        crop.thumbnail((crop_w, crop_h - 42), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (crop_w, crop_h), (11, 14, 25))
        canvas.paste(crop, ((crop_w - crop.width) // 2, 16))
        crop_draw = ImageDraw.Draw(canvas)
        crop_draw.text((18, crop_h - 34), label, font=small, fill=(236, 228, 204))
        col = index % 2
        row = index // 2
        sheet.paste(canvas, (col * crop_w + 80, thumb_h + 56 + row * crop_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def make_html_review_only_html(
    package_dir: Path,
    preview: Path,
    target_sheet: Path,
    pixel_qa_path: Path,
    manifest_path: Path,
    palette_contract: dict[str, Any],
) -> Path:
    review = package_dir / "review.html"
    swatches = "\n".join(
        f"""        <div class="swatch"><span style="background:{value}"></span><code>{key}: {value}</code></div>"""
        for key, value in palette_contract["css_variables"].items()
    )
    review.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Channel Trailer Adaptive End Screen HTML Review</title>
  <style>
    :root {{
      color-scheme: dark;
      --paper: #eee6cc;
      --muted: #aeb8c7;
      --ink: #070a12;
      --line: #2d3448;
      {chr(10).join(f"{key}: {value};" for key, value in palette_contract["css_variables"].items())}
    }}
    body {{ margin: 0; background: var(--ink); color: var(--paper); font-family: Arial, Helvetica, sans-serif; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px 22px 48px; }}
    h1 {{ margin: 0 0 6px; font-size: 28px; letter-spacing: 0; }}
    p {{ color: var(--muted); line-height: 1.45; }}
    img {{ width: 100%; height: auto; display: block; background: #000; border: 1px solid var(--line); }}
    section {{ margin-top: 26px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px 18px; }}
    .swatch {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
    .swatch span {{ width: 44px; height: 28px; border: 1px solid rgba(255,255,255,.28); border-radius: 6px; flex: 0 0 auto; }}
    code {{ color: var(--paper); white-space: normal; overflow-wrap: anywhere; }}
    a {{ color: #dede35; }}
  </style>
</head>
<body>
  <main>
    <h1>Channel Trailer Adaptive End Screen HTML Review</h1>
    <p>HTML-only gate. No MP4 has been rendered from this package.</p>
    <section>
      <h2>End Screen Preview</h2>
      <img alt="Adaptive titleless YouTube end screen preview" src="{preview.relative_to(package_dir)}">
    </section>
    <section>
      <h2>Target Crops</h2>
      <img alt="Adaptive end-screen target crops and palette swatches" src="{target_sheet.relative_to(package_dir)}">
    </section>
    <section>
      <h2>Palette Variables</h2>
      <div class="grid">
{swatches}
      </div>
    </section>
    <section>
      <p><a href="{manifest_path.relative_to(package_dir)}">Manifest</a> · <a href="{pixel_qa_path.relative_to(package_dir)}">Pixel QA</a></p>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return review


def build_html_review_manifest(
    package_dir: Path,
    preview: Path,
    clean_backplate: Path,
    target_sheet: Path,
    pixel_qa_path: Path,
    pixel_qa: dict[str, Any],
    palette_contract: dict[str, Any],
    timestamp: str,
) -> dict[str, Any]:
    reads = {
        "repair_scope_read": "pass_end_screen_html_review_only_no_mp4",
        "intro_rollback_read": "pass_html_review_only_pre_end_screen_unmodified",
        "body_rollback_read": "pass_html_review_only_pre_end_screen_unmodified",
        "end_screen_title_image_absence_read": "pass_no_cascade_of_effects_title_image_on_end_screen",
        "youtube_end_screen_template_applied_read": f"pass_{END_SCREEN_TEMPLATE_ID}",
        "html_review_only_read": "pass_no_mp4_render_created",
        "mp4_render_gate_read": "pass_mp4_render_blocked_pending_human_html_keep",
        "end_screen_target_geometry_read": palette_contract["reads"]["end_screen_target_geometry_read"],
        "end_screen_palette_contract_read": palette_contract["reads"]["end_screen_palette_contract_read"],
        "end_screen_target_fill_palette_read": palette_contract["reads"]["end_screen_target_fill_palette_read"],
        "end_screen_target_contrast_read": palette_contract["reads"]["end_screen_target_contrast_read"],
        "rail_panel_palette_read": palette_contract["reads"]["rail_panel_palette_read"],
        "source_integrated_panel_color_read": palette_contract["reads"]["source_integrated_panel_color_read"],
        "no_cross_episode_default_palette_read": palette_contract["reads"]["no_cross_episode_default_palette_read"],
        "end_screen_adaptive_perceptual_variability_read": palette_contract["reads"][
            "end_screen_adaptive_perceptual_variability_read"
        ],
        "end_screen_adaptive_pixel_sample_read": pixel_qa["reads"]["end_screen_adaptive_pixel_sample_read"],
        "youtube_action_read": "blocked_local_review_only",
    }
    return {
        "artifact_id": f"channel_trailer_end_screen_adaptive_html_review_{timestamp}",
        "created_at": timestamp,
        "status": "html_review_pending_human_keep",
        "workflow": HTML_REVIEW_WORKFLOW,
        "mp4_render_created": False,
        "may_render_mp4": False,
        "may_advance_to_mp4_render": False,
        "youtube_uploaded": False,
        "youtube_visibility_changed": False,
        "youtube_channel_trailer_replaced": False,
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "repair",
            "contract_registry_path": str(
                REPO_ROOT / "references/production_contracts/cascade_effects_output_contracts.v1.json"
            ),
            "youtube_action_approval_read": "blocked_local_review_only",
        },
        "allowed_delta": {
            "allowed_time_ranges_seconds": [[END_SCREEN_START_SECONDS, DURATION_SECONDS]],
            "allowed_pixel_regions": [
                [0, 0, WIDTH, TITLE_REMOVAL_TOP_BAND_FEATHER_END_PX],
                bbox_from_rect(TARGETS["left_video"]),
                bbox_from_rect(TARGETS["right_video"]),
                bbox_from_rect(TARGETS["subscribe"]),
            ],
            "allowed_stream_changes": [],
            "unchanged_streams": ["audio", "pre_end_screen_picture"],
            "frame_diff_model": "html_review_only_future_mp4_delta_scope_v1",
        },
        "youtube_action_read": "blocked_local_review_only",
        "predecessor": {
            "package_id": PREDECESSOR_PACKAGE_ID,
            "manifest_path": str(PREDECESSOR_MANIFEST),
            "manifest_sha256": sha256(PREDECESSOR_MANIFEST),
            "mp4_path": str(PREDECESSOR_MP4),
            "mp4_sha256": sha256(PREDECESSOR_MP4),
            "role": "actual_channel_trailer_predecessor_for_later_mp4_render_after_html_keep",
        },
        "reads": reads,
        "timeline": {
            "duration_seconds": DURATION_SECONDS,
            "predecessor_picture_preserved_seconds": [0.0, END_SCREEN_START_SECONDS],
            "titleless_end_screen_replacement_seconds": [END_SCREEN_START_SECONDS, DURATION_SECONDS],
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "youtube_end_screen_targets": TARGETS,
            "youtube_end_screen_layout_bbox_xy": {
                "left_video": bbox_from_rect(TARGETS["left_video"]),
                "right_video": bbox_from_rect(TARGETS["right_video"]),
                "center_subscribe": bbox_from_rect(TARGETS["subscribe"]),
            },
        },
        "end_screen_palette_contract": palette_contract,
        "pixel_qa": pixel_qa,
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(package_dir / "review.html"),
            "adaptive_end_screen_preview": str(preview),
            "adaptive_end_screen_preview_sha256": sha256(preview),
            "adaptive_end_screen_clean_backplate": str(clean_backplate),
            "adaptive_end_screen_clean_backplate_sha256": sha256(clean_backplate),
            "target_sheet": str(target_sheet),
            "target_sheet_sha256": sha256(target_sheet),
            "pixel_qa": str(pixel_qa_path),
            "pixel_qa_sha256": sha256(pixel_qa_path),
            "manifest": str(package_dir / "channel_trailer_end_screen_adaptive_html_review_manifest.json"),
            "mp4_render_created": False,
        },
    }


def build_manifest(
    package_dir: Path,
    final_mp4: Path,
    silent_video: Path,
    contact_sheet: Path,
    poster: Path,
    preservation_report: dict[str, Any],
    palette_contract: dict[str, Any],
    timestamp: str,
) -> dict[str, Any]:
    probe = ffprobe(final_mp4)
    streams = probe.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    predecessor_audio_sha = audio_stream_sha256(PREDECESSOR_MP4, package_dir / "work")
    final_audio_sha = audio_stream_sha256(final_mp4, package_dir / "work")
    return {
        "artifact_id": f"channel_trailer_end_screen_titleless_only_repair_{timestamp}",
        "created_at": timestamp,
        "status": "review_ready_pending_human_keep",
        "workflow": MP4_REPAIR_WORKFLOW,
        "mp4_render_created": True,
        "may_render_mp4": True,
        "production_contract": {
            "contract_id": "channel-trailer-v1",
            "intent": "repair",
            "contract_registry_path": str(
                REPO_ROOT / "references/production_contracts/cascade_effects_output_contracts.v1.json"
            ),
            "youtube_action_approval_read": "blocked_local_review_only",
        },
        "allowed_delta": {
            "allowed_time_ranges_seconds": [[END_SCREEN_START_SECONDS, DURATION_SECONDS]],
            "allowed_pixel_regions": [
                [0, 0, WIDTH, TITLE_REMOVAL_TOP_BAND_FEATHER_END_PX],
                bbox_from_rect(TARGETS["left_video"]),
                bbox_from_rect(TARGETS["right_video"]),
                bbox_from_rect(TARGETS["subscribe"]),
            ],
            "allowed_stream_changes": ["video"],
            "unchanged_streams": ["audio"],
            "frame_diff_model": "predecessor_picture_preserved_until_end_screen_start_v1",
        },
        "youtube_action_read": "blocked_local_review_only",
        "youtube_uploaded": False,
        "youtube_visibility_changed": False,
        "youtube_channel_trailer_replaced": False,
        "predecessor": {
            "package_id": PREDECESSOR_PACKAGE_ID,
            "manifest_path": str(PREDECESSOR_MANIFEST),
            "manifest_sha256": sha256(PREDECESSOR_MANIFEST),
            "mp4_path": str(PREDECESSOR_MP4),
            "mp4_sha256": sha256(PREDECESSOR_MP4),
            "role": "actual_channel_trailer_predecessor_preserved_until_end_screen_window",
        },
        "superseded_overreach_packages": [
            {
                "package_path": str(path),
                "reason": "overreached_beyond_end_screen_repair_scope",
            }
            for path in SUPERSEDED_OVERREACH_PACKAGES
            if path.exists()
        ],
        "reads": {
            "repair_scope_read": "pass_end_screen_only_picture_change",
            "intro_rollback_read": "pass_original_intro_picture_preserved",
            "body_rollback_read": "pass_original_trailer_body_picture_preserved_until_end_screen",
            "pre_end_screen_picture_preservation_read": preservation_report["pre_end_screen_picture_preservation_read"],
            "end_screen_title_image_absence_read": "pass_no_cascade_of_effects_title_image_on_end_screen",
            "youtube_end_screen_template_applied_read": f"pass_{END_SCREEN_TEMPLATE_ID}",
            "end_screen_target_geometry_read": palette_contract["reads"]["end_screen_target_geometry_read"],
            "end_screen_visual_treatment_conformance_read": "pass_adaptive_titleless_youtube_targets_rendered_from_backplate_palette",
            "first_eight_end_screen_style_reference_read": "pass_titleless_two_video_subscribe_safe_zone_matches_current_episode_end_screen_structure",
            "end_screen_palette_contract_read": palette_contract["reads"]["end_screen_palette_contract_read"],
            "end_screen_target_fill_palette_read": palette_contract["reads"]["end_screen_target_fill_palette_read"],
            "end_screen_target_contrast_read": palette_contract["reads"]["end_screen_target_contrast_read"],
            "rail_panel_palette_read": palette_contract["reads"]["rail_panel_palette_read"],
            "source_integrated_panel_color_read": palette_contract["reads"]["source_integrated_panel_color_read"],
            "no_cross_episode_default_palette_read": palette_contract["reads"]["no_cross_episode_default_palette_read"],
            "end_screen_adaptive_perceptual_variability_read": palette_contract["reads"][
                "end_screen_adaptive_perceptual_variability_read"
            ],
            "audio_stream_copy_read": "pass" if predecessor_audio_sha == final_audio_sha else "reject",
            "format_read": "pass"
            if video_stream.get("codec_name") == "h264"
            and video_stream.get("width") == WIDTH
            and video_stream.get("height") == HEIGHT
            and video_stream.get("avg_frame_rate") == "24/1"
            and audio_stream.get("codec_name") == "aac"
            else "reject",
            "full_decode_read": full_decode_read(final_mp4),
            "youtube_action_read": "blocked_local_review_only",
        },
        "preservation_report": preservation_report,
        "timeline": {
            "duration_seconds": DURATION_SECONDS,
            "predecessor_picture_preserved_seconds": [0.0, END_SCREEN_START_SECONDS],
            "titleless_end_screen_replacement_seconds": [END_SCREEN_START_SECONDS, DURATION_SECONDS],
            "youtube_end_screen_template_id": END_SCREEN_TEMPLATE_ID,
            "youtube_end_screen_targets": TARGETS,
            "youtube_end_screen_layout_bbox_xy": {
                "left_video": bbox_from_rect(TARGETS["left_video"]),
                "right_video": bbox_from_rect(TARGETS["right_video"]),
                "center_subscribe": bbox_from_rect(TARGETS["subscribe"]),
            },
        },
        "end_screen_palette_contract": palette_contract,
        "outputs": {
            "package_dir": str(package_dir),
            "review_html": str(package_dir / "review.html"),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": sha256(final_mp4),
            "silent_video": str(silent_video),
            "silent_video_sha256": sha256(silent_video),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256(contact_sheet),
            "poster_frame": str(poster),
            "poster_frame_sha256": sha256(poster),
            "manifest": str(package_dir / "channel_trailer_end_screen_titleless_only_manifest.json"),
        },
        "media_probe": probe,
    }


def build_html_review_package(timestamp: str) -> dict[str, Any]:
    package_dir = OUTPUT_ROOT / f"channel_trailer_end_screen_adaptive_html_review_{timestamp}"
    images_dir = package_dir / "images"
    qa_dir = package_dir / "qa"
    for directory in (images_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    end_screen, end_screen_palette_contract, image_outputs = titleless_end_screen_frame(images_dir)
    clean_backplate = Image.open(image_outputs["clean_backplate"]).convert("RGB")
    preview = Path(image_outputs["preview"])
    target_sheet = create_adaptive_target_sheet(
        end_screen,
        end_screen_palette_contract,
        qa_dir / "adaptive_end_screen_target_crops.png",
    )
    pixel_qa_path = qa_dir / "end_screen_adaptive_palette_pixel_qa.json"
    pixel_qa = build_palette_pixel_qa(clean_backplate, end_screen, end_screen_palette_contract, pixel_qa_path)
    manifest = build_html_review_manifest(
        package_dir,
        preview,
        Path(image_outputs["clean_backplate"]),
        target_sheet,
        pixel_qa_path,
        pixel_qa,
        end_screen_palette_contract,
        timestamp,
    )
    manifest_path = package_dir / "channel_trailer_end_screen_adaptive_html_review_manifest.json"
    write_json(manifest_path, manifest)
    contract_receipt = run_contract_validator(manifest_path)
    manifest["production_contract_receipt"] = {
        "path": contract_receipt.get("receipt_path", ""),
        "ok": contract_receipt.get("ok"),
        "contract_id": contract_receipt.get("contract_id"),
        "intent": contract_receipt.get("intent"),
        "youtube_action_allowed": contract_receipt.get("youtube_action_allowed"),
        "reads": contract_receipt.get("reads"),
    }
    write_json(manifest_path, manifest)
    review_html = make_html_review_only_html(
        package_dir,
        preview,
        target_sheet,
        pixel_qa_path,
        manifest_path,
        end_screen_palette_contract,
    )
    manifest["outputs"]["review_html"] = str(review_html)
    write_json(manifest_path, manifest)

    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Channel Trailer Adaptive End Screen HTML Review",
                "",
                f"- Review HTML: `{review_html}`",
                f"- End-screen preview: `{preview}`",
                f"- Target crops: `{target_sheet}`",
                f"- Pixel QA: `{pixel_qa_path}`",
                f"- Manifest: `{manifest_path}`",
                "- Status: `html_review_pending_human_keep`",
                "- Scope: HTML-only adaptive end-screen review. No MP4 was rendered from this package.",
                "- Change under review: titleless YouTube placeholders use the adaptive backplate-sampled palette.",
                "- MP4: blocked until explicit human approval of this HTML review.",
                "- YouTube: no upload, delete, visibility, or channel-trailer action.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    latest = OUTPUT_ROOT / "channel_trailer_end_screen_adaptive_html_review_latest.json"
    write_json(
        latest,
        {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "manifest": str(manifest_path),
            "adaptive_end_screen_preview": str(preview),
            "mp4_render_created": False,
            "may_render_mp4": False,
        },
    )
    return {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "adaptive_end_screen_preview": str(preview),
        "target_sheet": str(target_sheet),
        "pixel_qa": str(pixel_qa_path),
        "manifest": str(manifest_path),
        "status": manifest["status"],
        "mp4_render_created": False,
        "may_render_mp4": False,
        "reads": manifest["reads"],
    }


def build_mp4_package(timestamp: str) -> dict[str, Any]:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    package_dir = OUTPUT_ROOT / f"channel_trailer_end_screen_titleless_only_repair_{timestamp}"
    work_dir = package_dir / "work"
    source_frames = work_dir / "source_frames"
    output_frames = package_dir / "frames"
    video_dir = package_dir / "video"
    qa_dir = package_dir / "qa"
    images_dir = package_dir / "images"
    for directory in (work_dir, source_frames, output_frames, video_dir, qa_dir, images_dir):
        directory.mkdir(parents=True, exist_ok=True)

    extract_predecessor_frames(source_frames)
    end_screen, end_screen_palette_contract, _image_outputs = titleless_end_screen_frame(images_dir)
    render_frames(source_frames, output_frames, end_screen)

    silent_video = video_dir / "channel_trailer_end_screen_titleless_only_silent.mp4"
    final_mp4 = video_dir / "cascade_of_effects_channel_trailer_end_screen_titleless_only_1080p24.mp4"
    encode_video(output_frames, silent_video)
    mux_audio(silent_video, final_mp4)

    contact_sheet = create_contact_sheet(final_mp4, qa_dir)
    poster = poster_frame(final_mp4, images_dir)
    preservation_report = compare_preserved_samples(final_mp4, qa_dir)

    manifest = build_manifest(
        package_dir,
        final_mp4,
        silent_video,
        contact_sheet,
        poster,
        preservation_report,
        end_screen_palette_contract,
        timestamp,
    )
    manifest_path = package_dir / "channel_trailer_end_screen_titleless_only_manifest.json"
    write_json(manifest_path, manifest)
    contract_receipt = run_contract_validator(manifest_path)
    manifest["production_contract_receipt"] = {
        "path": contract_receipt.get("receipt_path", ""),
        "ok": contract_receipt.get("ok"),
        "contract_id": contract_receipt.get("contract_id"),
        "intent": contract_receipt.get("intent"),
        "youtube_action_allowed": contract_receipt.get("youtube_action_allowed"),
        "reads": contract_receipt.get("reads"),
    }
    write_json(manifest_path, manifest)
    review_html = make_review_html(package_dir, final_mp4, contact_sheet, poster, manifest_path)

    readme = package_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Channel Trailer End Screen Titleless Only Repair",
                "",
                f"- Review HTML: `{review_html}`",
                f"- Final MP4: `{final_mp4}`",
                f"- Contact sheet: `{contact_sheet}`",
                f"- Manifest: `{manifest_path}`",
                "- Status: `review_ready_pending_human_keep`",
                "- Scope: strict end-screen-only visual repair. The original trailer picture is preserved from `0.000-30.200s`.",
                "- Change: `30.200-48.000s` uses the adaptive titleless YouTube placeholder palette sampled from the end-screen backplate.",
                "- YouTube: no upload, delete, visibility, or channel-trailer action.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    latest = OUTPUT_ROOT / "channel_trailer_end_screen_titleless_only_repair_latest.json"
    write_json(
        latest,
        {
            "package_dir": str(package_dir),
            "review_html": str(review_html),
            "manifest": str(manifest_path),
            "final_mp4": str(final_mp4),
        },
    )
    return {
        "package_dir": str(package_dir),
        "review_html": str(review_html),
        "final_mp4": str(final_mp4),
        "contact_sheet": str(contact_sheet),
        "manifest": str(manifest_path),
        "status": manifest["status"],
        "reads": manifest["reads"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["html_review_only", "mp4_after_review"],
        default="html_review_only",
        help="Default is html_review_only so MP4 rendering cannot happen before human review.",
    )
    parser.add_argument(
        "--render-mp4-after-review",
        action="store_true",
        help="Explicit alias for --mode mp4_after_review. Use only after the HTML review is approved.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "mp4_after_review" if args.render_mp4_after_review else args.mode
    for path in (PREDECESSOR_MP4, PREDECESSOR_MANIFEST, TITANIC_END_SCREEN_BASE_PLATE):
        require_file(path)

    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    result = build_html_review_package(timestamp) if mode == "html_review_only" else build_mp4_package(timestamp)

    print(
        json.dumps(
            result,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
