#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


try:  # Pillow 9/10 compatibility
    RESAMPLING = Image.Resampling
except AttributeError:  # pragma: no cover
    RESAMPLING = Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="opening_tableau_tool.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compose = subparsers.add_parser("compose")
    compose.add_argument("--payload", required=True)
    compose.add_argument("--layout", required=True)
    compose.add_argument("--output", required=True)
    compose.add_argument("--plates-dir", required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def trim_transparent_bounds(image: Image.Image) -> Image.Image:
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)
    return image


def build_noise_alpha(size: tuple[int, int], *, amount: float, blur_radius: int = 0) -> Image.Image:
    width, height = size
    noise = Image.effect_noise((max(1, width), max(1, height)), 18).convert("L")
    if blur_radius > 0:
        noise = noise.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    scale = max(0.0, float(amount))
    return noise.point(lambda value: int(max(0, min(255, ((value - 128) * scale) + 128))))


def apply_editorial_grade(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    graded = rgba.convert("RGB")
    graded = ImageOps.autocontrast(graded, cutoff=1)
    graded = Image.blend(graded, ImageOps.colorize(graded.convert("L"), "#e7ddcf", "#8b7e72"), 0.16)
    graded = Image.blend(graded, Image.new("RGB", graded.size, "#f1eadf"), 0.08)
    graded_rgba = graded.convert("RGBA")
    graded_rgba.putalpha(alpha)
    return graded_rgba


def apply_plate_surface_finish(image: Image.Image, *, subject: bool) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    finished = rgba.convert("RGB")
    finished = ImageOps.autocontrast(finished, cutoff=2)
    finished = ImageOps.posterize(finished, 5 if subject else 4)
    finished = Image.blend(
        finished,
        ImageOps.colorize(finished.convert("L"), "#f3eadf", "#6c5d53"),
        0.26 if subject else 0.34,
    )
    finished = Image.blend(
        finished,
        Image.new("RGB", finished.size, "#efe4d4" if subject else "#eadfce"),
        0.14 if subject else 0.18,
    )
    finished = finished.filter(ImageFilter.UnsharpMask(radius=1.2, percent=105, threshold=2))

    texture_alpha = build_noise_alpha(finished.size, amount=0.7 if subject else 0.82, blur_radius=1)
    warm_fiber = Image.new("RGBA", finished.size, (118, 98, 82, 0))
    warm_fiber.putalpha(texture_alpha.point(lambda value: int(max(0, min(255, (value - 112) * 0.34)))))
    cool_fiber = Image.new("RGBA", finished.size, (153, 164, 173, 0))
    cool_fiber.putalpha(texture_alpha.point(lambda value: int(max(0, min(255, (148 - value) * 0.18)))))

    finished_rgba = finished.convert("RGBA")
    finished_rgba.putalpha(alpha)
    finished_rgba.alpha_composite(warm_fiber)
    finished_rgba.alpha_composite(cool_fiber)

    edge_mask = alpha.filter(ImageFilter.GaussianBlur(radius=2)).point(lambda value: int(value * 0.42))
    edge_wash = Image.new("RGBA", finished.size, (244, 237, 227, 0))
    edge_wash.putalpha(edge_mask)
    finished_rgba.alpha_composite(edge_wash)
    return finished_rgba


def fit_contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    contained = image.copy()
    contained.thumbnail((max(1, target_w), max(1, target_h)), RESAMPLING.LANCZOS)
    return contained


def has_meaningful_alpha(image: Image.Image) -> bool:
    if image.mode != "RGBA":
        return False
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return False
    full_area = image.width * image.height
    bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    return bbox_area < full_area * 0.97


def knock_out_light_background(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    corners = [
        rgba.getpixel((0, 0)),
        rgba.getpixel((rgba.width - 1, 0)),
        rgba.getpixel((0, rgba.height - 1)),
        rgba.getpixel((rgba.width - 1, rgba.height - 1)),
    ]
    light_corners = 0
    for red, green, blue, _alpha in corners:
        if min(red, green, blue) >= 232 and (max(red, green, blue) - min(red, green, blue)) <= 24:
            light_corners += 1
    if light_corners < 3:
        return rgba
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, alpha = pixels[x, y]
            minimum = min(red, green, blue)
            spread = max(red, green, blue) - minimum
            if minimum >= 246 and spread <= 18:
                pixels[x, y] = (red, green, blue, 0)
            elif minimum >= 232 and spread <= 28:
                fade = int(max(0, min(255, (246 - minimum) * 18)))
                pixels[x, y] = (red, green, blue, min(alpha, fade))
    return trim_transparent_bounds(rgba)


def build_paper_scrap(size: tuple[int, int], *, subject: bool) -> Image.Image:
    width, height = size
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    inset = max(6, int(min(width, height) * (0.06 if subject else 0.09)))
    shape = [
        (inset + int(width * 0.03), inset + int(height * 0.02)),
        (width - inset - int(width * 0.02), inset + int(height * 0.05)),
        (width - inset, int(height * 0.32)),
        (width - inset - int(width * 0.03), height - inset - int(height * 0.04)),
        (int(width * 0.52), height - inset),
        (inset + int(width * 0.05), height - inset - int(height * 0.03)),
        (inset, int(height * 0.44)),
    ]
    matte_mask = Image.new("L", (width, height), 0)
    matte_draw = ImageDraw.Draw(matte_mask)
    matte_draw.polygon(shape, fill=238)
    matte_mask = matte_mask.filter(ImageFilter.GaussianBlur(radius=max(2, int(min(width, height) * 0.015))))
    texture = build_noise_alpha((width, height), amount=0.55, blur_radius=1)
    matte_mask = ImageChops.multiply(matte_mask, texture)

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow.putalpha(matte_mask.point(lambda value: int(value * (0.22 if subject else 0.18))))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(6, int(min(width, height) * 0.04))))
    canvas.alpha_composite(shadow, dest=(6, 8))

    matte = Image.new("RGBA", (width, height), (246, 240, 230, 0))
    matte.putalpha(matte_mask)
    canvas.alpha_composite(matte)
    return canvas


def render_plate(asset_path: Path, frame_size: tuple[int, int], *, subject: bool) -> Image.Image:
    source = Image.open(asset_path).convert("RGBA")
    source = knock_out_light_background(source)
    source = trim_transparent_bounds(source)
    width, height = frame_size
    padding = max(18, int(min(width, height) * (0.08 if subject else 0.1)))
    plate = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    matte = build_paper_scrap((width, height), subject=subject)
    plate.alpha_composite(matte)
    content = fit_contain(source, (width - padding * 2, height - padding * 2))
    content = apply_editorial_grade(content)
    content = apply_plate_surface_finish(content, subject=subject)
    shadow = Image.new("RGBA", content.size, (0, 0, 0, 0))
    shadow_alpha = content.getchannel("A").point(lambda value: 120 if value > 0 else 0)
    shadow.putalpha(shadow_alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(6, int(min(content.size) * 0.04))))
    origin = ((width - content.width) // 2, (height - content.height) // 2)
    plate.alpha_composite(shadow, dest=(origin[0] + 8, origin[1] + 10))
    plate.alpha_composite(content, dest=origin)
    return plate


def build_background(width: int, height: int) -> Image.Image:
    background = Image.new("RGBA", (width, height), (240, 234, 224, 255))
    split = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    split_draw = ImageDraw.Draw(split)
    split_draw.rectangle((0, 0, width // 2, height), fill=(232, 226, 215, 110))
    split_draw.rectangle((width // 2, 0, width, height), fill=(245, 240, 232, 80))
    background.alpha_composite(split)
    wash = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash)
    wash_draw.ellipse(
        (int(width * 0.06), int(height * 0.16), int(width * 0.56), int(height * 0.96)),
        fill=(183, 92, 71, 30),
    )
    wash_draw.ellipse(
        (int(width * 0.40), int(height * 0.04), int(width * 0.94), int(height * 0.84)),
        fill=(127, 141, 154, 22),
    )
    wash_draw.ellipse(
        (int(width * 0.34), int(height * 0.18), int(width * 0.70), int(height * 0.96)),
        fill=(248, 244, 236, 72),
    )
    wash = wash.filter(ImageFilter.GaussianBlur(radius=max(18, int(min(width, height) * 0.045))))
    background.alpha_composite(wash)
    seam = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    seam_draw = ImageDraw.Draw(seam)
    seam_draw.rectangle(
        (int(width * 0.47), 0, int(width * 0.53), height),
        fill=(228, 219, 206, 120),
    )
    seam = seam.filter(ImageFilter.GaussianBlur(radius=max(14, int(min(width, height) * 0.03))))
    background.alpha_composite(seam)
    underpaint = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    underpaint_draw = ImageDraw.Draw(underpaint)
    underpaint_draw.rounded_rectangle(
        (int(width * 0.04), int(height * 0.08), int(width * 0.41), int(height * 0.92)),
        radius=int(min(width, height) * 0.04),
        fill=(228, 219, 205, 82),
    )
    underpaint_draw.rounded_rectangle(
        (int(width * 0.55), int(height * 0.05), int(width * 0.95), int(height * 0.90)),
        radius=int(min(width, height) * 0.05),
        fill=(236, 229, 218, 64),
    )
    underpaint = underpaint.filter(ImageFilter.GaussianBlur(radius=max(20, int(min(width, height) * 0.05))))
    background.alpha_composite(underpaint)
    grain_alpha = build_noise_alpha((width, height), amount=0.7, blur_radius=1)
    grain = Image.new("RGBA", (width, height), (118, 104, 86, 0))
    grain.putalpha(grain_alpha.point(lambda value: int(max(0, min(255, (value - 96) * 0.22)))))
    background.alpha_composite(grain)
    flecks = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fleck_alpha = build_noise_alpha((width, height), amount=0.95, blur_radius=0)
    flecks.putalpha(fleck_alpha.point(lambda value: int(max(0, min(255, (value - 176) * 0.15)))))
    flecks = Image.blend(
        Image.new("RGBA", (width, height), (255, 248, 239, 0)),
        Image.new("RGBA", (width, height), (96, 82, 66, 0)),
        0.45,
    )
    flecks.putalpha(fleck_alpha.point(lambda value: int(max(0, min(255, (value - 190) * 0.10)))))
    background.alpha_composite(flecks)
    vignette = Image.new("L", (width, height), 0)
    vignette_draw = ImageDraw.Draw(vignette)
    vignette_draw.ellipse(
        (-int(width * 0.08), -int(height * 0.12), int(width * 1.08), int(height * 1.14)),
        fill=170,
    )
    vignette = ImageChops.invert(vignette.filter(ImageFilter.GaussianBlur(radius=max(28, int(min(width, height) * 0.08)))))
    background.putalpha(Image.new("L", (width, height), 255))
    return Image.composite(background, Image.new("RGBA", (width, height), (233, 229, 220, 255)), vignette)


def paste_rotated(canvas: Image.Image, plate: Image.Image, placement: dict) -> None:
    rotation = float(placement.get("rotation_degrees", 0.0) or 0.0)
    rotated = plate.rotate(rotation, resample=RESAMPLING.BICUBIC, expand=True)
    x = int(placement["x"]) + max(0, (int(placement["width"]) - rotated.width) // 2)
    y = int(placement["y"]) + max(0, (int(placement["height"]) - rotated.height) // 2)
    canvas.alpha_composite(rotated, dest=(x, y))


def compose(payload_path: Path, layout_path: Path, output_path: Path, plates_dir: Path) -> dict:
    payload = read_json(payload_path)
    layout = read_json(layout_path)
    slots_by_id = {
        str(slot.get("slot_id", "")).strip(): slot
        for slot in payload.get("slots", [])
        if isinstance(slot, dict) and str(slot.get("slot_id", "")).strip()
    }
    canvas_width = int(layout.get("canvas", {}).get("width", 0) or 0)
    canvas_height = int(layout.get("canvas", {}).get("height", 0) or 0)
    if canvas_width <= 0 or canvas_height <= 0:
        raise SystemExit("Opening tableau layout is missing a positive canvas size.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plates_dir.mkdir(parents=True, exist_ok=True)

    canvas = build_background(canvas_width, canvas_height)
    plate_paths: dict[str, str] = {}
    used_assets: dict[str, str] = {}

    for placement in layout.get("supports", []):
        slot_id = str(placement.get("slot_id", "")).strip()
        slot = slots_by_id.get(slot_id)
        if slot is None:
            raise SystemExit(f"Opening tableau layout references unknown slot `{slot_id}`.")
        asset_path = Path(str(slot.get("asset_path", "")).strip()).expanduser()
        if not asset_path.exists():
            raise SystemExit(f"Opening tableau source asset is missing: {asset_path}")
        plate = render_plate(asset_path, (int(placement["width"]), int(placement["height"])), subject=False)
        plate_path = plates_dir / f"{slot_id}.png"
        plate.save(plate_path)
        plate_paths[slot_id] = str(plate_path)
        used_assets[slot_id] = str(asset_path)
        paste_rotated(canvas, plate, placement)

    subject_layout = layout.get("subject", {})
    subject_slot_id = str(subject_layout.get("slot_id", "")).strip()
    subject_slot = slots_by_id.get(subject_slot_id)
    if subject_slot is None:
        raise SystemExit(f"Opening tableau layout is missing subject slot `{subject_slot_id}`.")
    subject_asset = Path(str(subject_slot.get("asset_path", "")).strip()).expanduser()
    if not subject_asset.exists():
        raise SystemExit(f"Opening tableau subject asset is missing: {subject_asset}")
    subject_plate = render_plate(
        subject_asset,
        (int(subject_layout["width"]), int(subject_layout["height"])),
        subject=True,
    )
    subject_plate_path = plates_dir / f"{subject_slot_id}.png"
    subject_plate.save(subject_plate_path)
    plate_paths[subject_slot_id] = str(subject_plate_path)
    used_assets[subject_slot_id] = str(subject_asset)
    paste_rotated(canvas, subject_plate, subject_layout)

    subject_glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(subject_glow)
    sx = int(subject_layout["x"])
    sy = int(subject_layout["y"])
    sw = int(subject_layout["width"])
    sh = int(subject_layout["height"])
    glow_draw.ellipse((sx - 28, sy + 50, sx + sw + 28, sy + sh + 92), fill=(248, 239, 223, 72))
    subject_glow = subject_glow.filter(ImageFilter.GaussianBlur(radius=max(22, int(min(canvas.size) * 0.03))))
    canvas.alpha_composite(subject_glow)
    final_canvas = apply_editorial_grade(canvas)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_canvas.convert("RGB").save(output_path, quality=95)
    return {
        "output_path": str(output_path),
        "plate_paths": plate_paths,
        "used_assets": used_assets,
        "canvas_width": canvas_width,
        "canvas_height": canvas_height,
    }


def main() -> int:
    args = parse_args()
    try:
        if args.command == "compose":
            summary = compose(
                Path(args.payload).expanduser(),
                Path(args.layout).expanduser(),
                Path(args.output).expanduser(),
                Path(args.plates_dir).expanduser(),
            )
            json.dump(summary, sys.stdout, indent=2)
            sys.stdout.write("\n")
            return 0
        raise SystemExit(f"Unsupported command: {args.command}")
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - runtime safety
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
