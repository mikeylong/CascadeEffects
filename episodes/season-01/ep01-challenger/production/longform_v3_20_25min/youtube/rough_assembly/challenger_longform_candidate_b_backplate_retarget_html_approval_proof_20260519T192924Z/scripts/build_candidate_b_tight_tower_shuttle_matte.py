#!/usr/bin/env python3
"""Build the Candidate B ambient matte with only tower/shuttle exclusions.

The player treats matte alpha as the ambient-effect allow mask:
alpha > 0 permits fog/aircraft, alpha 0 blocks them. This repair removes the
previous floodlight, ground, astronaut, and right-rail exclusions while keeping
tight exclusions around the tower/service structure and shuttle stack.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PLATE = ROOT / "references" / "candidate_b_clean_rail_depth_exact_seven_1920x1080.png"
MASK_PATH = ROOT / "assets" / "masks" / "foreground_occlusion_matte.png"
QA_DIR = ROOT / "qa" / "matte"
RAIL_SAFE_LEFT_X = 1108

BLOCKED_PROBES = {
    "tower_beacon_pole": (365, 82),
    "tower_mid_hardware": (365, 260),
    "tower_lower_lattice": (292, 565),
    "service_arm": (515, 292),
    "external_tank": (604, 344),
    "orbiter_body": (579, 454),
    "left_booster": (544, 421),
    "right_booster": (651, 421),
}

ALLOWED_PROBES = {
    "left_floodlight": (82, 557),
    "mid_pad_floodlight": (769, 560),
    "crawlerway_light": (911, 662),
    "right_rail_region": (1400, 220),
    "rail_caption_region": (1520, 850),
    "left_open_sky": (95, 150),
    "right_open_sky_before_rail": (980, 210),
    "right_rail_sky": (1300, 210),
    "wet_ground": (1210, 915),
    "foreground_astronaut": (656, 840),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def alpha_at(alpha: Image.Image, xy: tuple[int, int]) -> float:
    return alpha.getpixel(xy) / 255


def draw_exclusions(alpha: Image.Image) -> None:
    draw = ImageDraw.Draw(alpha)

    # Tower and fixed service structure, including the top mast and lower legs.
    draw.rounded_rectangle((357, 42, 373, 178), radius=4, fill=0)
    draw.polygon(
        [
            (318, 155),
            (418, 158),
            (456, 248),
            (446, 364),
            (430, 516),
            (377, 654),
            (226, 654),
            (206, 610),
            (234, 518),
            (224, 440),
            (252, 338),
            (278, 232),
        ],
        fill=0,
    )
    draw.polygon([(226, 354), (468, 334), (470, 370), (218, 392)], fill=0)
    draw.polygon([(375, 250), (555, 260), (555, 302), (374, 294)], fill=0)
    draw.polygon([(360, 394), (524, 396), (525, 438), (354, 438)], fill=0)

    # Shuttle stack: external tank, solid rocket boosters, orbiter, wings, and base.
    draw.polygon([(584, 216), (620, 216), (647, 612), (556, 612)], fill=0)
    draw.rounded_rectangle((536, 306, 574, 616), radius=16, fill=0)
    draw.rounded_rectangle((637, 306, 676, 616), radius=16, fill=0)
    draw.polygon(
        [
            (585, 348),
            (610, 354),
            (626, 514),
            (617, 622),
            (557, 622),
            (548, 514),
            (564, 354),
        ],
        fill=0,
    )
    draw.polygon([(550, 472), (502, 582), (559, 604), (585, 514)], fill=0)
    draw.polygon([(614, 472), (662, 582), (607, 604), (583, 514)], fill=0)
    draw.rounded_rectangle((538, 588, 675, 640), radius=10, fill=0)


def build_mask() -> tuple[Image.Image, Image.Image]:
    source = Image.open(SOURCE_PLATE).convert("RGBA")
    alpha = Image.new("L", source.size, 255)
    draw_exclusions(alpha)
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    return source, alpha


def make_overlay(source: Image.Image, alpha: Image.Image) -> Image.Image:
    arr = np.asarray(alpha)
    blocked = arr <= 10
    allowed = arr > 10
    overlay = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    overlay[allowed] = [18, 183, 191, 58]
    overlay[blocked] = [220, 42, 34, 136]
    out = Image.alpha_composite(source, Image.fromarray(overlay, "RGBA"))
    draw = ImageDraw.Draw(out)
    draw.text(
        (34, 36),
        "Candidate B tight matte: red blocks tower/shuttle only; cyan permits lights, rail, sky, ground",
        fill=(255, 255, 255, 255),
    )
    return out


def write_outputs(source: Image.Image, alpha: Image.Image) -> dict[str, object]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    MASK_PATH.parent.mkdir(parents=True, exist_ok=True)

    matte = Image.new("RGBA", source.size, (255, 255, 255, 0))
    matte.putalpha(alpha)
    matte.save(MASK_PATH)

    alpha_path = QA_DIR / "candidate_b_tight_tower_shuttle_matte_alpha.png"
    overlay_path = QA_DIR / "candidate_b_tight_tower_shuttle_matte_overlay_for_review.png"
    ImageOps.colorize(alpha, black="black", white="white").save(alpha_path)
    make_overlay(source, alpha).save(overlay_path)

    blocked = {name: round(alpha_at(alpha, xy), 3) for name, xy in BLOCKED_PROBES.items()}
    allowed = {name: round(alpha_at(alpha, xy), 3) for name, xy in ALLOWED_PROBES.items()}
    reads = {
        "tower_shuttle_tight_matte_read": "pass" if all(value <= 0.05 for value in blocked.values()) else "tighten",
        "floodlight_matte_removed_read": "pass" if all(allowed[name] >= 0.85 for name in ("left_floodlight", "mid_pad_floodlight", "crawlerway_light")) else "tighten",
        "right_rail_matte_removed_read": "pass" if all(allowed[name] >= 0.85 for name in ("right_rail_region", "rail_caption_region", "right_rail_sky")) else "tighten",
        "open_air_and_ground_allowed_read": "pass" if all(value >= 0.85 for value in allowed.values()) else "tighten",
    }

    qa = {
        "status": "pass" if all(value == "pass" for value in reads.values()) else "tighten",
        "matte_semantics": "alpha > 0 permits ambient effects; alpha 0 blocks only the tower/service structure and shuttle stack",
        "source_plate_path": str(SOURCE_PLATE),
        "source_plate_sha256": sha256(SOURCE_PLATE),
        "mask_path": str(MASK_PATH),
        "mask_sha256": sha256(MASK_PATH),
        "dimensions": {"width": source.size[0], "height": source.size[1]},
        "blocked_probe_alpha": blocked,
        "allowed_probe_alpha": allowed,
        "qa_reads": reads,
        "qa_artifacts": {
            "alpha_path": str(alpha_path),
            "alpha_sha256": sha256(alpha_path),
            "overlay_path": str(overlay_path),
            "overlay_sha256": sha256(overlay_path),
        },
    }
    qa_path = QA_DIR / "candidate_b_tight_tower_shuttle_matte_qa.json"
    qa_path.write_text(json.dumps(qa, indent=2) + "\n")
    return {"qa_path": str(qa_path), "qa_sha256": sha256(qa_path), **qa}


def main() -> None:
    source, alpha = build_mask()
    result = write_outputs(source, alpha)
    print(json.dumps({"qa_path": result["qa_path"], "qa_sha256": result["qa_sha256"], "mask_sha256": result["mask_sha256"], "status": result["status"]}, indent=2))


if __name__ == "__main__":
    main()
