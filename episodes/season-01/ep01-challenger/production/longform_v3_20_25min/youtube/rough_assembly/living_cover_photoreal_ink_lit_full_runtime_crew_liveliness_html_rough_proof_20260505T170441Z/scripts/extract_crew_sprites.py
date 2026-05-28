from __future__ import annotations

import colorsys
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


SOURCE_ART = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png"
)
PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/living_cover_photoreal_ink_lit_full_runtime_crew_liveliness_html_rough_proof_20260505T170441Z"
)
OUT_DIR = PACKET_ROOT / "assets" / "crew_motion"


CREW_SPECS = [
    {
        "id": "crew_01",
        "role": "left_anchor",
        "bbox": {"x": 176, "y": 770, "width": 120, "height": 260},
        "pivot": {"x": 0.52, "y": 0.96},
        "motion": {"period": 13.7, "phase": 0.10, "x": 2.6, "y": 1.0, "rotate": 0.62, "settle": 0.55},
    },
    {
        "id": "crew_02",
        "role": "left_center",
        "bbox": {"x": 282, "y": 770, "width": 118, "height": 260},
        "pivot": {"x": 0.50, "y": 0.96},
        "motion": {"period": 15.1, "phase": 0.58, "x": 2.1, "y": 0.8, "rotate": -0.52, "settle": 0.48},
    },
    {
        "id": "crew_03",
        "role": "curly_hair_center_left",
        "bbox": {"x": 388, "y": 770, "width": 126, "height": 260},
        "pivot": {"x": 0.50, "y": 0.96},
        "motion": {"period": 11.9, "phase": 1.08, "x": 3.0, "y": 1.2, "rotate": 0.74, "settle": 0.62},
    },
    {
        "id": "crew_04",
        "role": "center_left",
        "bbox": {"x": 490, "y": 770, "width": 124, "height": 260},
        "pivot": {"x": 0.50, "y": 0.96},
        "motion": {"period": 16.4, "phase": 0.33, "x": 2.4, "y": 0.7, "rotate": -0.68, "settle": 0.45},
    },
    {
        "id": "crew_05",
        "role": "center_gap",
        "bbox": {"x": 674, "y": 770, "width": 126, "height": 260},
        "pivot": {"x": 0.51, "y": 0.96},
        "motion": {"period": 14.2, "phase": 1.51, "x": 2.7, "y": 1.1, "rotate": 0.58, "settle": 0.56},
    },
    {
        "id": "crew_06",
        "role": "right_center",
        "bbox": {"x": 784, "y": 770, "width": 122, "height": 260},
        "pivot": {"x": 0.50, "y": 0.96},
        "motion": {"period": 12.8, "phase": 0.82, "x": 2.2, "y": 0.8, "rotate": -0.60, "settle": 0.50},
    },
    {
        "id": "crew_07",
        "role": "right_anchor",
        "bbox": {"x": 878, "y": 770, "width": 126, "height": 260},
        "pivot": {"x": 0.50, "y": 0.96},
        "motion": {"period": 17.0, "phase": 1.22, "x": 2.0, "y": 0.9, "rotate": 0.48, "settle": 0.42},
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def body_mask(width: int, height: int, spec: dict) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    hair_extra = 0.05 if "curly" in spec["role"] else 0.0
    shoulder = 0.78 if width >= 124 else 0.74
    body = [
        (width * 0.50, height * 0.02),
        (width * (0.62 + hair_extra), height * 0.08),
        (width * shoulder, height * 0.28),
        (width * 0.72, height * 0.72),
        (width * 0.84, height * 0.99),
        (width * 0.59, height * 0.99),
        (width * 0.51, height * 0.72),
        (width * 0.44, height * 0.99),
        (width * 0.18, height * 0.99),
        (width * 0.30, height * 0.72),
        (width * (1 - shoulder), height * 0.28),
        (width * (0.38 - hair_extra), height * 0.08),
    ]
    draw.polygon(body, fill=255)
    draw.ellipse(
        (
            width * (0.34 - hair_extra),
            height * 0.00,
            width * (0.66 + hair_extra),
            height * 0.17,
        ),
        fill=255,
    )
    draw.rectangle((width * 0.20, height * 0.92, width * 0.80, height), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(1.1))


def crew_alpha(crop: Image.Image, spec: dict) -> Image.Image:
    width, height = crop.size
    coarse = body_mask(width, height, spec)
    rgb = crop.convert("RGB")
    alpha = Image.new("L", (width, height), 0)
    src = rgb.load()
    coarse_px = coarse.load()
    out = alpha.load()

    for y in range(height):
        yn = y / height
        for x in range(width):
            if coarse_px[x, y] < 16:
                continue
            xn = x / width
            r, g, b = src[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            blue_suit = (0.52 <= h <= 0.70 and s > 0.22 and v > 0.08) or (s > 0.18 and b > r + 18 and b >= g * 0.82 and g >= r * 0.75)
            dark_head = v < 0.22 and yn < 0.20 and abs(xn - 0.5) < (0.20 if "curly" not in spec["role"] else 0.28)
            dark_body_detail = v < 0.16 and 0.22 < yn < 0.88 and 0.22 < xn < 0.78
            dark_feet = v < 0.18 and yn > 0.88 and 0.14 < xn < 0.86
            warm_hand_or_neck = (h < 0.13 or h > 0.92) and s > 0.14 and v > 0.18 and (
                (yn < 0.18 and abs(xn - 0.5) < 0.22) or (0.38 < yn < 0.76 and (xn < 0.32 or xn > 0.68))
            )
            if blue_suit or dark_head or dark_body_detail or dark_feet or warm_hand_or_neck:
                out[x, y] = 255

    alpha = alpha.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.75))
    return ImageChops.multiply(alpha, coarse)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE_ART).convert("RGBA")
    entries = []
    for spec in CREW_SPECS:
        box = spec["bbox"]
        crop = source.crop((box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"]))
        crop = crop.filter(ImageFilter.GaussianBlur(0.18))
        crop.putalpha(crew_alpha(crop, spec))
        output = OUT_DIR / f"{spec['id']}.png"
        crop.save(output)
        entries.append(
            {
                **spec,
                "path": str(output),
                "sha256": sha256(output),
                "bytes": output.stat().st_size,
                "transparent_png": True,
                "source_area": "lower-left/lower-center crew foreground from kept Variant C raster",
            }
        )

    manifest = {
        "source_art_path": str(SOURCE_ART),
        "source_art_sha256": sha256(SOURCE_ART),
        "sprite_count": len(entries),
        "identity_policy": "back-view flight-suit figures only; no new faces, name patches, readable logos, text, or likeness features added",
        "motion_policy": "restrained staggered weight shifts, shoulder/head settling, and contact-shadow changes; no synchronized swaying, waving, walking, or viewer acknowledgement",
        "sprites": entries,
    }
    manifest_path = OUT_DIR / "crew_sprite_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
