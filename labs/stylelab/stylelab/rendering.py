from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

from .config import RuntimeConfig
from .io import timestamp_slug, write_json
from .manifests import normalize_final_size
from .prompts import compile_negative_prompt, compile_prompt, model_family_for_mode


@dataclass(frozen=True)
class StillRenderResult:
    image_path: Path
    manifest_path: Path
    prompt: str


def _hex(color: str) -> tuple[int, int, int]:
    return ImageColor.getrgb(color)


def _noise_mask(size: tuple[int, int], seed: int, *, density: int, blur_radius: float) -> Image.Image:
    rng = random.Random(seed)
    texture = Image.new("L", size, 0)
    draw = ImageDraw.Draw(texture)
    width, height = size
    for _ in range(density):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        radius = rng.randint(1, 3)
        alpha = rng.randint(10, 34)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=alpha)
    return texture.filter(ImageFilter.GaussianBlur(radius=blur_radius))


def _build_mass_mask(size: tuple[int, int], seed: int, width_ratio: float) -> Image.Image:
    width, height = size
    rng = random.Random(seed)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    mass_width = int(width * max(0.24, min(width_ratio, 0.62)))
    left = width - mass_width
    control = int(width * (0.06 + (rng.random() * 0.09)))
    top_curve = int(height * (0.08 + (rng.random() * 0.08)))
    lower_curve = int(height * (0.76 + (rng.random() * 0.08)))
    points = [
        (left + control, 0),
        (width, 0),
        (width, height),
        (left + int(control * 0.5), height),
        (left - int(control * 0.25), lower_curve),
        (left + int(control * 0.35), int(height * 0.46)),
        (left - int(control * 0.18), top_curve),
    ]
    draw.polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(radius=6))


def _draw_launch_stack(mask_draw: ImageDraw.ImageDraw, line_draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    tank_w = int(width * 0.2)
    booster_w = int(width * 0.08)
    left = int(width * 0.42)
    top = int(height * 0.08)
    bottom = int(height * 0.92)
    mask_draw.rounded_rectangle((left, top + int(height * 0.08), left + tank_w, bottom), radius=tank_w // 2, fill=255)
    mask_draw.polygon(
        [
            (left + tank_w // 2, top),
            (left + tank_w, top + int(height * 0.12)),
            (left, top + int(height * 0.12)),
        ],
        fill=255,
    )
    booster_left = left + tank_w + int(width * 0.03)
    mask_draw.rounded_rectangle(
        (booster_left, top + int(height * 0.15), booster_left + booster_w, bottom - int(height * 0.03)),
        radius=booster_w // 2,
        fill=255,
    )
    orbiter = [
        (left - int(width * 0.08), top + int(height * 0.36)),
        (left + int(width * 0.06), top + int(height * 0.3)),
        (left + int(width * 0.12), top + int(height * 0.42)),
        (left + int(width * 0.02), top + int(height * 0.5)),
        (left - int(width * 0.12), top + int(height * 0.48)),
    ]
    mask_draw.polygon(orbiter, fill=255)
    line_draw.line((left + tank_w + int(width * 0.18), top + int(height * 0.2), left + tank_w + int(width * 0.18), bottom), fill=255, width=max(2, width // 90))
    line_draw.line((left + tank_w + int(width * 0.02), top + int(height * 0.45), left + tank_w + int(width * 0.18), top + int(height * 0.35)), fill=255, width=max(2, width // 120))


def _draw_control_bay(mask_draw: ImageDraw.ImageDraw, line_draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    outer = (int(width * 0.18), int(height * 0.16), int(width * 0.82), int(height * 0.82))
    inner = (int(width * 0.34), int(height * 0.26), int(width * 0.66), int(height * 0.62))
    console = (int(width * 0.22), int(height * 0.64), int(width * 0.78), int(height * 0.76))
    mask_draw.rounded_rectangle(outer, radius=int(width * 0.08), fill=255)
    mask_draw.rounded_rectangle(inner, radius=int(width * 0.03), fill=0)
    mask_draw.rounded_rectangle(console, radius=int(width * 0.03), fill=255)
    mask_draw.ellipse((int(width * 0.42), int(height * 0.52), int(width * 0.58), int(height * 0.68)), fill=255)
    line_draw.arc((int(width * 0.16), int(height * 0.12), int(width * 0.84), int(height * 0.4)), start=190, end=350, fill=255, width=max(2, width // 90))
    line_draw.line((int(width * 0.26), int(height * 0.7), int(width * 0.74), int(height * 0.7)), fill=255, width=max(2, width // 100))


def _draw_switch_plate(mask_draw: ImageDraw.ImageDraw, line_draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    plate = (int(width * 0.3), int(height * 0.2), int(width * 0.7), int(height * 0.84))
    slot = (int(width * 0.43), int(height * 0.38), int(width * 0.57), int(height * 0.66))
    knob = (int(width * 0.52), int(height * 0.16), int(width * 0.72), int(height * 0.34))
    mask_draw.rounded_rectangle(plate, radius=int(width * 0.05), fill=255)
    mask_draw.rounded_rectangle(slot, radius=int(width * 0.025), fill=0)
    mask_draw.ellipse(knob, fill=255)
    line_draw.line((int(width * 0.62), int(height * 0.24), int(width * 0.86), int(height * 0.12)), fill=255, width=max(2, width // 110))
    line_draw.line((int(width * 0.62), int(height * 0.24), int(width * 0.84), int(height * 0.46)), fill=255, width=max(2, width // 110))
    line_draw.rectangle((int(width * 0.36), int(height * 0.28), int(width * 0.64), int(height * 0.76)), outline=255, width=max(2, width // 120))


def _draw_seal_joint(mask_draw: ImageDraw.ImageDraw, line_draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    outer = (int(width * 0.18), int(height * 0.18), int(width * 0.82), int(height * 0.82))
    inner = (int(width * 0.33), int(height * 0.33), int(width * 0.67), int(height * 0.67))
    mask_draw.ellipse(outer, fill=255)
    mask_draw.ellipse(inner, fill=0)
    notch = [
        (int(width * 0.71), int(height * 0.24)),
        (int(width * 0.88), int(height * 0.31)),
        (int(width * 0.76), int(height * 0.45)),
    ]
    mask_draw.polygon(notch, fill=0)
    line_draw.arc((int(width * 0.22), int(height * 0.22), int(width * 0.78), int(height * 0.78)), start=18, end=336, fill=255, width=max(2, width // 60))
    line_draw.arc((int(width * 0.39), int(height * 0.39), int(width * 0.61), int(height * 0.61)), start=18, end=336, fill=255, width=max(2, width // 100))
    line_draw.line((int(width * 0.74), int(height * 0.32), int(width * 0.9), int(height * 0.28)), fill=255, width=max(2, width // 110))


def _draw_rocket_totem(mask_draw: ImageDraw.ImageDraw, line_draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    body = (int(width * 0.4), int(height * 0.12), int(width * 0.6), int(height * 0.86))
    mask_draw.rounded_rectangle(body, radius=int(width * 0.08), fill=255)
    mask_draw.polygon(
        [
            (int(width * 0.5), int(height * 0.04)),
            (int(width * 0.62), int(height * 0.18)),
            (int(width * 0.38), int(height * 0.18)),
        ],
        fill=255,
    )
    mask_draw.polygon(
        [
            (int(width * 0.4), int(height * 0.68)),
            (int(width * 0.28), int(height * 0.82)),
            (int(width * 0.4), int(height * 0.82)),
        ],
        fill=255,
    )
    mask_draw.polygon(
        [
            (int(width * 0.6), int(height * 0.68)),
            (int(width * 0.72), int(height * 0.82)),
            (int(width * 0.6), int(height * 0.82)),
        ],
        fill=255,
    )
    line_draw.ellipse((int(width * 0.455), int(height * 0.28), int(width * 0.545), int(height * 0.37)), outline=255, width=max(2, width // 120))
    line_draw.line((int(width * 0.5), int(height * 0.18), int(width * 0.5), int(height * 0.78)), fill=255, width=max(2, width // 130))


def _draw_breach_plume(mask_draw: ImageDraw.ImageDraw, line_draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    column = (int(width * 0.42), int(height * 0.12), int(width * 0.58), int(height * 0.9))
    mask_draw.rounded_rectangle(column, radius=int(width * 0.06), fill=255)
    flare = [
        (int(width * 0.56), int(height * 0.34)),
        (int(width * 0.86), int(height * 0.18)),
        (int(width * 0.72), int(height * 0.48)),
        (int(width * 0.88), int(height * 0.78)),
        (int(width * 0.58), int(height * 0.58)),
    ]
    mask_draw.polygon(flare, fill=255)
    rupture = [
        (int(width * 0.36), int(height * 0.48)),
        (int(width * 0.52), int(height * 0.42)),
        (int(width * 0.66), int(height * 0.56)),
        (int(width * 0.48), int(height * 0.66)),
    ]
    mask_draw.polygon(rupture, fill=0)
    line_draw.line((int(width * 0.4), int(height * 0.46), int(width * 0.68), int(height * 0.6)), fill=255, width=max(2, width // 90))
    line_draw.line((int(width * 0.52), int(height * 0.14), int(width * 0.8), int(height * 0.26)), fill=255, width=max(2, width // 100))


def _draw_generic_totem(mask_draw: ImageDraw.ImageDraw, line_draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    mask_draw.rounded_rectangle((int(width * 0.32), int(height * 0.16), int(width * 0.68), int(height * 0.84)), radius=int(width * 0.06), fill=255)
    line_draw.line((int(width * 0.38), int(height * 0.26), int(width * 0.62), int(height * 0.26)), fill=255, width=max(2, width // 120))
    line_draw.line((int(width * 0.38), int(height * 0.74), int(width * 0.62), int(height * 0.74)), fill=255, width=max(2, width // 120))


def _symbolic_subject_template(archetype: str, palette: dict[str, str], *, mode: str, seed: int) -> Image.Image:
    width, height = 480, 720
    mask = Image.new("L", (width, height), 0)
    lines = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    line_draw = ImageDraw.Draw(lines)

    if archetype == "launch_stack":
        _draw_launch_stack(mask_draw, line_draw, width, height)
    elif archetype == "control_bay":
        _draw_control_bay(mask_draw, line_draw, width, height)
    elif archetype == "switch_plate":
        _draw_switch_plate(mask_draw, line_draw, width, height)
    elif archetype == "seal_joint":
        _draw_seal_joint(mask_draw, line_draw, width, height)
    elif archetype == "rocket_totem":
        _draw_rocket_totem(mask_draw, line_draw, width, height)
    elif archetype == "breach_plume":
        _draw_breach_plume(mask_draw, line_draw, width, height)
    else:
        _draw_generic_totem(mask_draw, line_draw, width, height)

    blur_radius = 7 if mode == "lock" else 5
    mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius)).point(lambda value: min(255, int(value * 1.08)))
    line_alpha = lines.filter(ImageFilter.GaussianBlur(radius=2.4 if mode == "sketch" else 2.0))

    subject_fill = _hex(palette.get("subject", palette["anchor"]))
    subject = Image.new("RGBA", (width, height), subject_fill + (0,))
    subject.putalpha(mask.point(lambda value: min(232, value)))

    line_layer = Image.new("RGBA", (width, height), _hex(palette["shadow"]) + (0,))
    line_layer.putalpha(line_alpha.point(lambda value: min(172, int(value * (0.6 if mode == "sketch" else 0.52)))))
    subject = Image.alpha_composite(subject, line_layer)

    bleed = Image.new("RGBA", (width, height), _hex(palette["anchor_glow"]) + (0,))
    bleed.putalpha(mask.filter(ImageFilter.GaussianBlur(radius=10)).point(lambda value: min(16, int(value * 0.06))))
    subject = Image.alpha_composite(bleed, subject)
    return subject


def _subject_layer(size: tuple[int, int], anchor: dict[str, Any], palette: dict[str, str], *, seed: int, mode: str) -> Image.Image:
    subject = _symbolic_subject_template(str(anchor["archetype"]), palette, mode=mode, seed=seed)
    target_width = int(size[0] * float(anchor["scale"]))
    target_height = int(target_width * (subject.size[1] / max(subject.size[0], 1)))
    resized = subject.resize((max(48, target_width), max(48, target_height)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    center_x = int(size[0] * float(anchor["placement"][0]))
    center_y = int(size[1] * float(anchor["placement"][1]))
    origin = (center_x - (resized.size[0] // 2), center_y - (resized.size[1] // 2))
    shadow = Image.new("RGBA", resized.size, _hex(palette["shadow"]) + (0,))
    shadow_alpha = resized.getchannel("A").filter(ImageFilter.GaussianBlur(radius=10))
    shadow.putalpha(shadow_alpha.point(lambda value: min(62, int(value * 0.24))))
    canvas.alpha_composite(shadow, dest=(origin[0] + 12, origin[1] + 22))
    canvas.alpha_composite(resized, dest=origin)
    return canvas


def _anchor_center(anchor: dict[str, Any], size: tuple[int, int]) -> tuple[int, int]:
    return int(size[0] * float(anchor["placement"][0])), int(size[1] * float(anchor["placement"][1]))


def _environment_layer(scene: dict[str, Any], size: tuple[int, int], palette: dict[str, str], *, seed: int, mode: str) -> Image.Image:
    width, height = size
    horizon_y = float(scene["reflection_strategy"]["horizon_y"])
    rng = random.Random(seed)
    hero_x, hero_y = (float(scene["subject_anchor"]["placement"][0]), float(scene["subject_anchor"]["placement"][1]))
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    matte_mask = Image.new("L", size, 0)
    matte_draw = ImageDraw.Draw(matte_mask)
    matte_w = int(width * (0.14 + rng.random() * 0.06))
    matte_h = int(height * (0.16 + rng.random() * 0.06))
    matte_x = int(width * max(0.06, hero_x - 0.12))
    matte_y = int(height * max(0.14, hero_y - 0.16))
    matte_draw.rounded_rectangle(
        (matte_x, matte_y, matte_x + matte_w, matte_y + matte_h),
        radius=int(min(matte_w, matte_h) * 0.08),
        fill=255,
    )
    matte_mask = matte_mask.filter(ImageFilter.GaussianBlur(radius=18))
    matte = Image.new("RGBA", size, _hex(palette["anchor_glow"]) + (0,))
    matte.putalpha(matte_mask.point(lambda value: min(42, int(value * 0.18))))
    layer.alpha_composite(matte)

    band_mask = Image.new("L", size, 0)
    band_draw = ImageDraw.Draw(band_mask)
    band_top = int(height * (horizon_y - 0.02))
    band_draw.rounded_rectangle(
        (int(width * 0.08), band_top, int(width * 0.5), band_top + int(height * 0.035)),
        radius=int(height * 0.012),
        fill=255,
    )
    band_mask = band_mask.filter(ImageFilter.GaussianBlur(radius=24))
    band = Image.new("RGBA", size, _hex(palette["cool_fiber"]) + (0,))
    band.putalpha(band_mask.point(lambda value: min(30, int(value * 0.12))))
    layer.alpha_composite(band)
    return layer


def _surreal_breach_layer(scene: dict[str, Any], size: tuple[int, int], palette: dict[str, str], *, seed: int, mode: str) -> Image.Image:
    width, height = size
    kind = str(scene.get("surreal_breach", {}).get("kind", "")).strip()
    anchor = scene["subject_anchor"]
    center_x, center_y = _anchor_center(anchor, size)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = random.Random(seed)
    shadow = _hex(palette["shadow"])
    glow = _hex(palette["anchor_glow"])
    cool = _hex(palette["cool_fiber"])
    blue = _hex(palette["blue_highlight"])

    if kind == "boundary_pressure":
        mask = Image.new("L", size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rectangle((0, int(height * 0.08), int(width * 0.48), int(height * 0.2)), fill=255)
        mask_draw.rectangle((int(width * 0.16), 0, int(width * 0.26), int(height * 0.42)), fill=255)
        halo = Image.new("RGBA", size, glow + (0,))
        halo.putalpha(mask.filter(ImageFilter.GaussianBlur(radius=26)).point(lambda value: min(44, int(value * 0.15))))
        line = Image.new("RGBA", size, cool + (0,))
        line.putalpha(mask.filter(ImageFilter.GaussianBlur(radius=6)).point(lambda value: min(68, int(value * 0.22))))
        layer.alpha_composite(halo)
        layer.alpha_composite(line)
    elif kind == "open_ring":
        draw.arc(
            (center_x - int(width * 0.18), center_y - int(height * 0.12), center_x + int(width * 0.18), center_y + int(height * 0.12)),
            start=18,
            end=330,
            fill=shadow + (118,),
            width=max(6, width // 110),
        )
        draw.arc(
            (center_x - int(width * 0.21), center_y - int(height * 0.15), center_x + int(width * 0.21), center_y + int(height * 0.15)),
            start=18,
            end=330,
            fill=glow + (92,),
            width=max(3, width // 180),
        )
    elif kind == "threshold_division":
        x = int(width * 0.47)
        draw.rectangle((x - int(width * 0.015), int(height * 0.12), x + int(width * 0.015), int(height * 0.88)), fill=shadow + (42,))
        glow_mask = Image.new("L", size, 0)
        ImageDraw.Draw(glow_mask).rectangle((x - int(width * 0.01), int(height * 0.1), x + int(width * 0.01), int(height * 0.9)), fill=255)
        glow_layer = Image.new("RGBA", size, glow + (0,))
        glow_layer.putalpha(glow_mask.filter(ImageFilter.GaussianBlur(radius=14)).point(lambda value: min(34, int(value * 0.12))))
        layer.alpha_composite(glow_layer)
    elif kind == "joint_smoke":
        smoke = Image.new("L", size, 0)
        smoke_draw = ImageDraw.Draw(smoke)
        base_x = center_x + int(width * 0.08)
        base_y = center_y - int(height * 0.16)
        for index in range(5):
            drift_x = int(width * 0.02 * index)
            drift_y = -int(height * (0.02 + (index * 0.015)))
            radius_x = int(width * (0.03 + (index * 0.01)))
            radius_y = int(height * (0.02 + (index * 0.012)))
            smoke_draw.ellipse((base_x + drift_x - radius_x, base_y + drift_y - radius_y, base_x + drift_x + radius_x, base_y + drift_y + radius_y), fill=180 - (index * 18))
        smoke_layer = Image.new("RGBA", size, shadow + (0,))
        smoke_layer.putalpha(smoke.filter(ImageFilter.GaussianBlur(radius=18)).point(lambda value: min(78, int(value * 0.22))))
        layer.alpha_composite(smoke_layer)
    elif kind == "formal_split":
        draw.line(
            (
                center_x - int(width * 0.12),
                center_y - int(height * 0.18),
                center_x + int(width * 0.18),
                center_y + int(height * 0.12),
            ),
            fill=glow + (104,),
            width=max(4, width // 140),
        )
        draw.line(
            (
                center_x - int(width * 0.08),
                center_y - int(height * 0.22),
                center_x + int(width * 0.24),
                center_y + int(height * 0.16),
            ),
            fill=shadow + (88,),
            width=max(8, width // 90),
        )
    elif kind == "absorbed_signal":
        for index in range(4):
            x = int(width * (0.58 + (index * 0.08)))
            y = int(height * (0.28 + (index * 0.08)))
            radius = max(8, int(width * 0.012) + (index * 3))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=blue + (42 - (index * 6),), width=max(2, width // 200))
        band = Image.new("L", size, 0)
        band_draw = ImageDraw.Draw(band)
        band_draw.rounded_rectangle((int(width * 0.56), int(height * 0.3), int(width * 0.88), int(height * 0.78)), radius=int(width * 0.04), fill=255)
        band_layer = Image.new("RGBA", size, shadow + (0,))
        band_layer.putalpha(band.filter(ImageFilter.GaussianBlur(radius=18)).point(lambda value: min(20, int(value * 0.08))))
        layer.alpha_composite(band_layer)
    elif kind == "contained_glow":
        radius_x = int(width * 0.14)
        radius_y = int(height * 0.1)
        halo = Image.new("L", size, 0)
        halo_draw = ImageDraw.Draw(halo)
        halo_draw.ellipse((center_x - radius_x, center_y - radius_y, center_x + radius_x, center_y + radius_y), fill=255)
        halo_layer = Image.new("RGBA", size, glow + (0,))
        alpha_cap = 30 if mode == "lock" else 24
        halo_layer.putalpha(halo.filter(ImageFilter.GaussianBlur(radius=20)).point(lambda value: min(alpha_cap, int(value * 0.12))))
        layer.alpha_composite(halo_layer)
    else:
        draw.line(
            (
                center_x - int(width * 0.12),
                center_y - int(height * 0.12),
                center_x + int(width * 0.12),
                center_y + int(height * 0.12),
            ),
            fill=shadow + (70,),
            width=max(4, width // 150),
        )

    if mode == "sketch":
        return layer.filter(ImageFilter.GaussianBlur(radius=1.2))
    if rng.random() > 0.5:
        return layer
    return Image.alpha_composite(layer, Image.new("RGBA", size, cool + (0,)))


def _reflection_layer(subject_layer: Image.Image, size: tuple[int, int], palette: dict[str, str], horizon_y: float, *, mode: str) -> Image.Image:
    width, height = size
    reflection = Image.new("RGBA", size, (0, 0, 0, 0))
    lower = subject_layer.crop((0, int(height * horizon_y), width, height))
    flipped = ImageOps.flip(lower).filter(ImageFilter.GaussianBlur(radius=12 if mode == "sketch" else 16))
    tint = Image.new("RGBA", flipped.size, _hex(palette["cool_fiber"]) + ((18 if mode == "lock" else 14),))
    flipped = Image.alpha_composite(flipped, tint)
    mask = Image.linear_gradient("L").resize(flipped.size)
    flipped.putalpha(mask.point(lambda value: min(68, int(value * 0.24))))
    reflection.alpha_composite(flipped, dest=(0, int(height * horizon_y)))
    return reflection


def _accent_layer(size: tuple[int, int], accent: dict[str, Any], palette: dict[str, str], *, seed: int, mode: str) -> Image.Image:
    width, height = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x = int(width * float(accent["placement"][0]))
    y = int(height * float(accent["placement"][1]))
    radius = max(8, int(width * float(accent["size"])))
    color = _hex(palette["accent"])
    rng = random.Random(seed)
    if accent.get("kind") == "warning_light":
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + (228,))
        glow = Image.new("RGBA", size, color + (0,))
        glow_mask = Image.new("L", size, 0)
        glow_draw = ImageDraw.Draw(glow_mask)
        glow_draw.ellipse((x - (radius * 3), y - (radius * 3), x + (radius * 3), y + (radius * 3)), fill=255)
        glow.putalpha(glow_mask.filter(ImageFilter.GaussianBlur(radius=12)).point(lambda value: min(34, int(value * 0.13))))
        layer.alpha_composite(glow)
    else:
        trunk = max(4, radius // 5)
        draw.line((x, y + radius, x, y - radius), fill=color + (210,), width=trunk)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + ((180 if mode == "sketch" else 208),))
        draw.ellipse((x - radius // 2, y - radius - (radius // 2), x + radius // 2, y), fill=color + (168,))
        draw.line((x - radius, y, x + radius, y), fill=color + (90 + rng.randint(0, 30),), width=max(2, trunk // 2))
    return layer.filter(ImageFilter.GaussianBlur(radius=0.8 if mode == "sketch" else 1.2))


def _base_canvas(size: tuple[int, int], palette: dict[str, str], *, seed: int, horizon_y: float) -> Image.Image:
    width, height = size
    canvas = Image.new("RGBA", size, _hex(palette["ivory"]) + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, int(height * horizon_y), width, height), fill=_hex(palette["plane"]) + (255,))
    wash = Image.new("RGBA", size, _hex(palette["ivory"]) + (0,))
    wash_alpha = _noise_mask(size, seed + 17, density=max(180, (width * height) // 6200), blur_radius=15.0)
    wash.putalpha(wash_alpha.point(lambda value: min(16, value)))
    canvas.alpha_composite(wash)
    return canvas


def _mass_layer(size: tuple[int, int], mass: dict[str, Any], palette: dict[str, str], *, seed: int, horizon_y: float) -> Image.Image:
    width, height = size
    mask = _build_mass_mask(size, seed, float(mass["width_ratio"]))
    layer = Image.new("RGBA", size, _hex(palette["blue"]) + (0,))
    layer.putalpha(mask.point(lambda value: min(240, value)))
    bleed = Image.new("RGBA", size, _hex(palette["blue_highlight"]) + (0,))
    bleed.putalpha(mask.filter(ImageFilter.GaussianBlur(radius=22)).point(lambda value: min(26, int(value * 0.1))))
    layer = Image.alpha_composite(bleed, layer)
    reflection = ImageOps.flip(layer.crop((0, 0, width, int(height * horizon_y))))
    reflection = reflection.resize((width, height - int(height * horizon_y)), Image.Resampling.BICUBIC)
    reflection.putalpha(reflection.getchannel("A").point(lambda value: min(54, int(value * 0.16))))
    combined = Image.new("RGBA", size, (0, 0, 0, 0))
    combined.alpha_composite(layer)
    combined.alpha_composite(reflection, dest=(0, int(height * horizon_y)))
    return combined


def _texture_overlay(size: tuple[int, int], palette: dict[str, str], *, seed: int, mode: str) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    warm = Image.new("RGBA", size, _hex(palette["warm_fiber"]) + (0,))
    cool = Image.new("RGBA", size, _hex(palette["cool_fiber"]) + (0,))
    warm.putalpha(_noise_mask(size, seed + 101, density=120 if mode == "sketch" else 220, blur_radius=5.8).point(lambda value: min(14, value)))
    cool.putalpha(_noise_mask(size, seed + 211, density=90 if mode == "sketch" else 180, blur_radius=7.2).point(lambda value: min(10, value)))
    overlay.alpha_composite(warm)
    overlay.alpha_composite(cool)
    return overlay


def render_scene_image(
    scene: dict[str, Any],
    profile: dict[str, Any],
    *,
    mode: str,
    time_progress: float | None = None,
    motion_preset: str | None = None,
) -> Image.Image:
    width, height = normalize_final_size(scene)
    palette = profile["palette"]
    seed = int(scene["selected_seed"])
    horizon_y = float(scene["reflection_strategy"]["horizon_y"])
    working = _base_canvas((width, height), palette, seed=seed, horizon_y=horizon_y)
    time_progress = 0.0 if time_progress is None else time_progress

    environment = _environment_layer(scene, (width, height), palette, seed=seed + 333, mode=mode)
    mass = _mass_layer((width, height), scene["dominant_mass_strategy"], palette, seed=seed + int(time_progress * 1000), horizon_y=horizon_y)
    working.alpha_composite(environment)
    working.alpha_composite(mass)

    subject = _subject_layer((width, height), scene["subject_anchor"], palette, seed=seed, mode=mode)
    active_motion_preset = motion_preset or str(scene["motion_preset"])
    if time_progress:
        scale = 1.0 + (0.016 if active_motion_preset == "stillness_breathe" else 0.03) * math.sin(time_progress * math.tau)
        drift_y = int((6 if active_motion_preset == "stillness_breathe" else 22) * math.sin((time_progress * math.tau) / 2.0))
        subject = subject.resize(
            (max(1, int(subject.size[0] * scale)), max(1, int(subject.size[1] * scale))),
            Image.Resampling.BICUBIC,
        )
        padded = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        padded.alpha_composite(subject, dest=((width - subject.size[0]) // 2, ((height - subject.size[1]) // 2) + drift_y))
        subject = padded
    reflection = _reflection_layer(subject, (width, height), palette, horizon_y, mode=mode)
    accent = _accent_layer((width, height), scene["accent_strategy"], palette, seed=seed + 55 + int(time_progress * 1000), mode=mode)
    breach = _surreal_breach_layer(scene, (width, height), palette, seed=seed + 777 + int(time_progress * 300), mode=mode)
    if time_progress:
        accent = ImageChops.offset(accent, 0, int(10 * math.sin(time_progress * math.tau)))
    texture = _texture_overlay((width, height), palette, seed=seed + int(time_progress * 2000), mode=mode)

    working.alpha_composite(reflection)
    working.alpha_composite(subject)
    working.alpha_composite(breach)
    working.alpha_composite(accent)
    working.alpha_composite(texture)

    if mode == "sketch":
        working = working.filter(ImageFilter.GaussianBlur(radius=0.8))
    elif mode == "lock":
        working = Image.alpha_composite(working, Image.new("RGBA", working.size, _hex(palette["anchor_glow"]) + (12,)))
    return working.convert("RGB")


def update_scene_output(scene_path: Path, scene: dict[str, Any], mode: str, payload: dict[str, Any]) -> None:
    scene.setdefault("outputs", {}).setdefault(mode, {}).update(payload)
    write_json(scene_path, scene)


def render_still(
    runtime: RuntimeConfig,
    scene_path: Path,
    scene: dict[str, Any],
    profile: dict[str, Any],
    *,
    mode: str,
) -> StillRenderResult:
    scene_id = scene["id"]
    timestamp = timestamp_slug()
    output_dir = runtime.renders_root / scene_id
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{timestamp}__{mode}.png"
    manifest_path = output_dir / f"{timestamp}__{mode}.json"
    prompt = compile_prompt(scene, profile, mode=mode)
    negative_prompt = compile_negative_prompt(profile)
    image = render_scene_image(scene, profile, mode=mode)
    image.save(image_path)
    manifest = {
        "scene_id": scene_id,
        "beat_id": scene["beat_id"],
        "style_profile": scene["style_profile"],
        "source_refs": scene["source_refs"],
        "selected_seed": scene["selected_seed"],
        "render_size": {"width": image.width, "height": image.height},
        "final_size": scene["final_size"],
        "output_path": str(image_path),
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "historical_anchor": scene["historical_anchor"],
        "surreal_breach": scene["surreal_breach"],
        "caption_safe_zone": scene["caption_safe_zone"],
        "target_duration_seconds": scene["target_duration_seconds"],
        "mode": mode,
        "model_family": model_family_for_mode(mode),
        "render_backend": "stylelab_painterly_compositor_v1",
        "generated_at": timestamp,
    }
    write_json(manifest_path, manifest)
    update_scene_output(
        scene_path,
        scene,
        mode,
        {
            "image_path": str(image_path),
            "manifest_path": str(manifest_path),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "generated_at": timestamp,
            "model_family": manifest["model_family"],
        },
    )
    return StillRenderResult(image_path=image_path, manifest_path=manifest_path, prompt=prompt)


def build_title_card(text: str, size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGB", size, (12, 16, 20))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text_bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=6)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    draw.multiline_text(
        ((size[0] - text_w) / 2, (size[1] - text_h) / 2),
        text,
        fill=(236, 228, 216),
        font=font,
        spacing=6,
        align="center",
    )
    return image
