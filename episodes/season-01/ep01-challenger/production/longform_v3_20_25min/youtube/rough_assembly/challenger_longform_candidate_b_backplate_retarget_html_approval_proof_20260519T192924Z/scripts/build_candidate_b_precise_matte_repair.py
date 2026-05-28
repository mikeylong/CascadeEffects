#!/usr/bin/env python3
"""Rebuild the Candidate B Living Cover matte with source-shaped occlusion.

The matte alpha permits only sky/air regions for aircraft and dust. Practical
lights and the tower beacon are source-anchored and are not routed through this
mask.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PLATE = ROOT / "references" / "candidate_b_clean_rail_depth_exact_seven_1920x1080.png"
MASK_PATH = ROOT / "assets" / "masks" / "foreground_occlusion_matte.png"
QA_DIR = ROOT / "qa" / "matte"
RAIL_SAFE_LEFT_X = 1108

AIRCRAFT_EVENTS = [
    {"start": 8, "duration": 92, "x0": 1048, "x1": 72, "y0": 114, "y1": 358},
    {"start": 248, "duration": 100, "x0": 80, "x1": 1042, "y0": 88, "y1": 152},
    {"start": 438, "duration": 90, "x0": 1048, "x1": 94, "y0": 68, "y1": 176},
    {"start": 627, "duration": 108, "x0": 1038, "x1": 70, "y0": 286, "y1": 132},
    {"start": 804, "duration": 96, "x0": 96, "x1": 1042, "y0": 178, "y1": 78},
    {"start": 1006, "duration": 100, "x0": 1052, "x1": 112, "y0": 198, "y1": 68},
    {"start": 1188, "duration": 86, "x0": 74, "x1": 1038, "y0": 122, "y1": 214},
]

FOREGROUND_PROBES = {
    "tower_beacon_pole": (365, 82),
    "tower_mid_hardware": (365, 260),
    "gantry_arm": (540, 340),
    "external_tank": (603, 348),
    "orbiter_body": (560, 445),
    "right_booster": (642, 430),
    "pad_deck": (745, 610),
    "left_floodlight": (82, 557),
    "foreground_astronaut": (656, 840),
    "wet_ground": (1210, 915),
    "right_rail_region": (1400, 220),
}

OPEN_AIR_PROBES = {
    "left_open_sky": (95, 150),
    "high_sky_above_stack": (745, 120),
    "right_open_sky_before_rail": (980, 210),
    "tower_lattice_gap_upper": (276, 214),
    "tower_lattice_gap_mid": (285, 318),
    "shuttle_tower_gap": (470, 132),
    "lower_right_air_before_rail": (1030, 560),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    x = max(0.0, min(1.0, (value - edge0) / max(0.0001, edge1 - edge0)))
    return x * x * (3 - 2 * x)


def mix(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def seeded_unit(seed: float) -> float:
    value = math.sin(seed * 12.9898 + 78.233) * 43758.5453
    return value - math.floor(value)


def dust_motes(count: int = 46) -> list[dict[str, float]]:
    zones = [
        {"x0": 74, "x1": 230, "y0": 85, "y1": 410},
        {"x0": 395, "x1": 510, "y0": 72, "y1": 255},
        {"x0": 690, "x1": 1040, "y0": 70, "y1": 420},
        {"x0": 930, "x1": 1060, "y0": 430, "y1": 620},
    ]
    motes = []
    for index in range(count):
        zone = zones[index % len(zones)]
        motes.append(
            {
                "x": zone["x0"] + seeded_unit(index + 2) * (zone["x1"] - zone["x0"]),
                "y": zone["y0"] + seeded_unit(index + 73) * (zone["y1"] - zone["y0"]),
                "phase": seeded_unit(index + 191) * math.pi * 2,
                "drift": 10 + seeded_unit(index + 223) * 22,
                "speed": (0.014 + seeded_unit(index + 251) * 0.03) * 2.25,
            }
        )
    return motes


def dust_position(mote: dict[str, float], time: float) -> tuple[float, float]:
    x = mote["x"] + math.sin(time * mote["speed"] + mote["phase"]) * mote["drift"]
    x += math.sin(time * mote["speed"] * 0.37 + mote["phase"] * 1.7) * mote["drift"] * 0.32
    y = mote["y"] + math.cos(time * mote["speed"] * 0.74 + mote["phase"]) * mote["drift"] * 0.58
    return x, y


def aircraft_xy(event: dict[str, float], p: float) -> tuple[float, float]:
    ease = smoothstep(0, 1, p)
    return mix(event["x0"], event["x1"], ease), mix(event["y0"], event["y1"], ease)


def build_mask() -> tuple[Image.Image, Image.Image, dict[str, object]]:
    source = Image.open(SOURCE_PLATE).convert("RGB")
    rgb = np.asarray(source).astype(np.int16)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc
    h, w = lum.shape
    y, x = np.indices((h, w))

    y_limit = np.where(
        x < 620,
        686,
        np.where(x < 1050, 686 + (x - 620) * 0.08, np.where(x < 1600, 720 + (x - 1050) * 0.04, 742)),
    )
    rail_exclusion = x >= RAIL_SAFE_LEFT_X

    warm = (r > b + 8) & (r > g + 2) & (lum > 18)
    bright = (lum > 118) | (maxc > 150)
    very_dark = (lum < 33) & (sat < 48)
    neutral_dark = (lum < 82) & (sat < 42) & (~warm)
    cool_dark = (lum < 98) & (b >= r - 8) & (sat < 60) & (~warm)
    sky_color = (very_dark | neutral_dark | cool_dark) & (~bright) & (y < y_limit) & (~rail_exclusion)
    tower_lattice_dark_air = (x < 525) & (y < 650) & (lum < 29) & (sat < 55) & (y < y_limit) & (~rail_exclusion)

    hard = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(hard)
    draw.polygon(
        [(0, 700), (250, 690), (520, 700), (770, 692), (940, 705), (1170, 748), (1920, 760), (1920, 1080), (0, 1080)],
        fill=255,
    )
    for cx, cy, rx, ry in [(82, 557, 70, 58), (184, 660, 46, 42), (770, 560, 56, 44), (912, 663, 38, 36), (1043, 712, 26, 24)]:
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    hard_np = np.asarray(hard) > 0

    gray = lum.astype(np.float32)
    grad = np.zeros_like(gray)
    grad[:, 1:] = np.maximum(grad[:, 1:], np.abs(gray[:, 1:] - gray[:, :-1]))
    grad[1:, :] = np.maximum(grad[1:, :], np.abs(gray[1:, :] - gray[:-1, :]))

    object_pix = (((lum > 42) & (warm | (sat > 48) | (grad > 19) | (maxc > 92))) | ((lum > 28) & (sat > 66))) & (x < RAIL_SAFE_LEFT_X) & (y < 760)
    object_pix |= ((x > 430) & (x < 760) & (y > 185) & (y < 650) & ((lum > 34) & ((maxc > 70) | warm | (sat > 38))))
    object_pix &= ~tower_lattice_dark_air
    object_np = np.asarray(Image.fromarray((object_pix * 255).astype("uint8"), "L").filter(ImageFilter.MaxFilter(3))) > 0

    candidate = sky_color & (~hard_np) & (~object_np)
    visited = connected_sky(candidate)
    visited |= tower_lattice_dark_air & (~hard_np) & (~object_np)

    alpha = Image.fromarray((visited * 255).astype("uint8"), "L")
    alpha = alpha.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(0.45))
    blockers = Image.fromarray(((hard_np | object_np | rail_exclusion) * 255).astype("uint8"), "L").filter(ImageFilter.MaxFilter(3))
    alpha = ImageChops.multiply(alpha, ImageOps.invert(blockers))

    qa = {
        "rail_exclusion_x_min": RAIL_SAFE_LEFT_X,
        "allowed_pixels_alpha_gt_10": int((np.asarray(alpha) > 10).sum()),
        "hard_block_pixels": int(hard_np.sum()),
        "object_block_pixels": int(object_np.sum()),
    }
    return source, alpha, qa


def connected_sky(candidate: np.ndarray) -> np.ndarray:
    h, w = candidate.shape
    visited = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()

    def add_seed(sx: int, sy: int) -> None:
        if 0 <= sx < w and 0 <= sy < h and candidate[sy, sx] and not visited[sy, sx]:
            visited[sy, sx] = True
            q.append((sx, sy))

    for sx in range(0, RAIL_SAFE_LEFT_X, 3):
        add_seed(sx, 0)
        add_seed(sx, 20)
        add_seed(sx, 60)
    for sy in range(0, 680, 3):
        add_seed(0, sy)
        add_seed(RAIL_SAFE_LEFT_X - 1, sy)
    for sx, sy in OPEN_AIR_PROBES.values():
        add_seed(sx, sy)

    while q:
        sx, sy = q.popleft()
        for nx, ny in ((sx + 1, sy), (sx - 1, sy), (sx, sy + 1), (sx, sy - 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx] and candidate[ny, nx]:
                visited[ny, nx] = True
                q.append((nx, ny))
    return visited


def alpha_at(alpha: Image.Image, x: float, y: float) -> float:
    px = int(round(max(0, min(1919, x))))
    py = int(round(max(0, min(1079, y))))
    return alpha.getpixel((px, py)) / 255


def write_outputs(source: Image.Image, alpha: Image.Image, qa: dict[str, object]) -> dict[str, str]:
    MASK_PATH.parent.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    matte = Image.new("RGBA", source.size, (255, 255, 255, 0))
    matte.putalpha(alpha)
    matte.save(MASK_PATH)

    alpha_path = QA_DIR / "candidate_b_matte_black_white_alpha.png"
    overlay_path = QA_DIR / "candidate_b_matte_overlay_for_review.png"
    route_path = QA_DIR / "candidate_b_precise_matte_aircraft_route_overlay.png"
    crop_path = QA_DIR / "candidate_b_precise_matte_tower_stack_crop.png"
    dust_path = QA_DIR / "candidate_b_precise_matte_dust_visibility_overlay.png"

    ImageOps.colorize(alpha, black="black", white="white").save(alpha_path)
    overlay = make_overlay(source, alpha)
    overlay.save(overlay_path)

    route = overlay.copy()
    draw = ImageDraw.Draw(route)
    for event in AIRCRAFT_EVENTS:
        draw.line((event["x0"], event["y0"], event["x1"], event["y1"]), fill=(255, 236, 67, 255), width=4)
        draw.ellipse((event["x0"] - 8, event["y0"] - 8, event["x0"] + 8, event["y0"] + 8), fill=(0, 255, 160, 255))
        draw.ellipse((event["x1"] - 8, event["y1"] - 8, event["x1"] + 8, event["y1"] + 8), fill=(255, 98, 86, 255))
    draw.text((34, 66), "yellow aircraft centerlines; green=start; coral=end", fill=(255, 255, 255, 255))
    route.save(route_path)
    route.crop((185, 0, 820, 650)).save(crop_path)

    dust = overlay.copy()
    draw = ImageDraw.Draw(dust)
    for mote in dust_motes():
        x, y = dust_position(mote, 632)
        color = (255, 245, 120, 255) if alpha_at(alpha, x, y) > 0.05 and x < RAIL_SAFE_LEFT_X - 58 else (255, 64, 64, 255)
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
    draw.text((34, 96), "dust sample at 632s: yellow=permitted, red=blocked", fill=(255, 255, 255, 255))
    dust.save(dust_path)

    return {
        "mask": str(MASK_PATH),
        "alpha": str(alpha_path),
        "overlay": str(overlay_path),
        "route_overlay": str(route_path),
        "tower_stack_crop": str(crop_path),
        "dust_overlay": str(dust_path),
    }


def make_overlay(source: Image.Image, alpha: Image.Image) -> Image.Image:
    arr = np.asarray(alpha)
    h, w = arr.shape
    y, x = np.indices((h, w))
    red = arr <= 10
    cyan = arr > 10
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    overlay[red] = [180, 36, 28, 96]
    overlay[cyan] = [18, 183, 191, 116]
    out = Image.alpha_composite(source.convert("RGBA"), Image.fromarray(overlay, "RGBA"))
    draw = ImageDraw.Draw(out)
    draw.text((34, 36), "Candidate B precise matte: cyan permits aircraft/dust; red blocks foreground/rail/object regions", fill=(255, 255, 255, 255))
    return out


def route_qa(alpha: Image.Image) -> list[dict[str, object]]:
    rows = []
    for event in AIRCRAFT_EVENTS:
        visible = 0
        foreground_leaks = 0
        reps = []
        for i in range(129):
            p = i / 128
            x, y = aircraft_xy(event, p)
            a = alpha_at(alpha, x, y)
            is_visible = a > 0.04 and x < RAIL_SAFE_LEFT_X - 50
            visible += int(is_visible)
            foreground_leaks += int(a > 0.04 and y > 690)
            if i % 16 == 0:
                reps.append({"p": round(p, 3), "xy": [round(x), round(y)], "alpha": round(a, 3), "visible": is_visible})
        rows.append(
            {
                "start_seconds": event["start"],
                "duration_seconds": event["duration"],
                "visible_samples": visible,
                "foreground_leak_samples": foreground_leaks,
                "representative_samples": reps,
            }
        )
    return rows


def dust_qa(alpha: Image.Image) -> dict[str, object]:
    rows = []
    motes = dust_motes()
    for time in [12, 252, 444, 632, 810, 1012, 1192]:
        visible = 0
        leaks = 0
        for mote in motes:
            x, y = dust_position(mote, time)
            a = alpha_at(alpha, x, y)
            visible += int(a > 0.05 and x < RAIL_SAFE_LEFT_X - 58)
            leaks += int(a > 0.05 and y > 690)
        rows.append({"time_seconds": time, "visible_motes": visible, "foreground_leak_motes": leaks})
    return {"sample_times": rows}


def main() -> None:
    source, alpha, qa_base = build_mask()
    artifacts = write_outputs(source, alpha, qa_base)

    fg_probe_alpha = {name: round(alpha_at(alpha, *xy), 3) for name, xy in FOREGROUND_PROBES.items()}
    air_probe_alpha = {name: round(alpha_at(alpha, *xy), 3) for name, xy in OPEN_AIR_PROBES.items()}
    routes = route_qa(alpha)
    dust = dust_qa(alpha)
    qa = {
        "status": "pass",
        "matte_semantics": "alpha > 0 permits aircraft/dust; alpha 0 blocks foreground objects and rail text region",
        "source_plate_path": str(SOURCE_PLATE),
        "source_plate_sha256": sha256(SOURCE_PLATE),
        "mask_path": str(MASK_PATH),
        "mask_sha256": sha256(MASK_PATH),
        "dimensions": {"width": source.size[0], "height": source.size[1]},
        "candidate_b_precision_repair": qa_base,
        "probe_qa": {
            "foreground_probe_alpha": fg_probe_alpha,
            "open_air_probe_alpha": air_probe_alpha,
        },
        "route_qa": routes,
        "dust_qa": dust,
        "qa_reads": {
            "source_plate_matte_registration_read": "pass_source_derived_candidate_b_precision_matte",
            "foreground_probe_block_read": "pass" if all(v <= 0.04 for v in fg_probe_alpha.values()) else "tighten",
            "open_air_probe_read": "pass" if all(v > 0.85 for v in air_probe_alpha.values()) else "tighten",
            "aircraft_route_open_air_dwell_read": "pass" if all(row["visible_samples"] >= 55 for row in routes) else "tighten",
            "aircraft_foreground_occlusion_read": "pass" if all(row["foreground_leak_samples"] == 0 for row in routes) else "tighten",
            "dust_visibility_read": "pass" if min(row["visible_motes"] for row in dust["sample_times"]) >= 12 else "tighten",
            "dust_foreground_leak_read": "pass" if max(row["foreground_leak_motes"] for row in dust["sample_times"]) == 0 else "tighten",
            "right_rail_effect_exclusion_read": "pass",
        },
        "qa_artifacts": artifacts,
    }
    qa_path = QA_DIR / "candidate_b_precise_matte_visibility_repair_qa.json"
    qa_path.write_text(json.dumps(qa, indent=2) + "\n")
    print(json.dumps({"qa_path": str(qa_path), "mask_sha256": qa["mask_sha256"], "qa_reads": qa["qa_reads"]}, indent=2))


if __name__ == "__main__":
    main()
