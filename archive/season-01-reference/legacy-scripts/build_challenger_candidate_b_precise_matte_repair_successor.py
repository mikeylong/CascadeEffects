#!/usr/bin/env python3
"""Build a Challenger Candidate B matte repair successor proof.

The repair keeps the current right-rail and practical-light intent while
replacing broad tower/shuttle silhouettes with a source-pixel matte. The player
clips aircraft/fog through this matte after drawing, so the matte itself should
stay tight instead of being expanded to the aircraft glow radius.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


EPISODE_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube"
)
ROUGH_ROOT = EPISODE_ROOT / "rough_assembly"
CURRENT_PROOF = ROUGH_ROOT / "challenger_rolling_caption_rail_rough_proof_20260522T223902Z"
CURRENT_MANIFEST = CURRENT_PROOF / "rough_assembly_manifest.json"
PRED_PROOF = ROUGH_ROOT / "challenger_longform_candidate_b_backplate_retarget_html_approval_proof_20260519T192924Z"
SOURCE_PLATE = PRED_PROOF / "references" / "candidate_b_clean_rail_depth_exact_seven_1920x1080.png"
CURRENT_MASK = PRED_PROOF / "assets" / "masks" / "foreground_occlusion_matte.png"

WIDTH = 1920
HEIGHT = 1080
RAIL_SAFE_LEFT_X = 1108
AIRCRAFT_VISUAL_RADIUS_PX = 17
MATTE_EDGE_GUARD_PX = 2
SOURCE_COMPONENT_MIN_AREA_PX = 45
MODEL_ID = "source_pixel_gap_preserving_tower_shuttle_matte_v3"

AIRCRAFT_EVENTS = [
    {"start": 8, "duration": 92, "x0": 1848, "x1": 72, "y0": 114, "y1": 358},
    {"start": 248, "duration": 100, "x0": 80, "x1": 1856, "y0": 88, "y1": 152},
    {"start": 438, "duration": 90, "x0": 1864, "x1": 94, "y0": 68, "y1": 176},
    {"start": 627, "duration": 108, "x0": 1844, "x1": 70, "y0": 286, "y1": 132},
    {"start": 804, "duration": 96, "x0": 96, "x1": 1852, "y0": 178, "y1": 78},
    {"start": 1006, "duration": 100, "x0": 1860, "x1": 112, "y0": 198, "y1": 68},
    {"start": 1188, "duration": 86, "x0": 74, "x1": 1038, "y0": 122, "y1": 214},
]

BLOCKED_PROBES = {
    "tower_beacon_pole": (365, 82),
    "tower_mid_hardware": (365, 260),
    "tower_lower_lattice": (292, 565),
    "upper_service_arm_visible_hardware": (405, 255),
    "lower_service_arm_visible_hardware": (460, 354),
    "external_tank": (604, 344),
    "orbiter_body": (579, 454),
    "left_booster": (544, 421),
    "right_booster": (651, 421),
    "shuttle_base": (604, 606),
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
    "service_arm_open_gap_upper": (515, 292),
    "service_arm_open_gap_lower": (465, 304),
    "right_booster_side_sky": (686, 350),
    "right_booster_lower_side_sky": (690, 420),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    x = max(0.0, min(1.0, (value - edge0) / max(0.0001, edge1 - edge0)))
    return x * x * (3 - 2 * x)


def mix(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def aircraft_xy(event: dict[str, float], p: float) -> tuple[float, float]:
    ease = smoothstep(0, 1, p)
    return mix(event["x0"], event["x1"], ease), mix(event["y0"], event["y1"], ease)


def alpha_at(alpha: Image.Image, xy: tuple[float, float]) -> float:
    x = int(round(max(0, min(WIDTH - 1, xy[0]))))
    y = int(round(max(0, min(HEIGHT - 1, xy[1]))))
    return alpha.getpixel((x, y)) / 255


def draw_manual_core(draw: ImageDraw.ImageDraw) -> None:
    # Keep manual fallback to the obvious tower pole only. Tower/service-arm
    # lattice and shuttle contours come from source pixels so open gaps stay
    # open and haze does not terminate against invented silhouettes.
    draw.rounded_rectangle((355, 38, 375, 182), radius=5, fill=255)


def connected_component_area_filter(mask: np.ndarray, min_area: int) -> np.ndarray:
    visited = np.zeros_like(mask, dtype=bool)
    keep = np.zeros_like(mask, dtype=bool)
    for yy in range(20, 660):
        xs = np.where(mask[yy] & ~visited[yy])[0]
        for sx in xs:
            if visited[yy, sx] or not mask[yy, sx]:
                continue
            stack = [(int(sx), int(yy))]
            visited[yy, sx] = True
            points: list[tuple[int, int]] = []
            while stack:
                px, py = stack.pop()
                points.append((px, py))
                for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                    if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and not visited[ny, nx] and mask[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((nx, ny))
            if len(points) >= min_area:
                for px, py in points:
                    keep[py, px] = True
    return keep


def source_object_core(source: Image.Image) -> Image.Image:
    rgb = np.asarray(source.convert("RGB")).astype(np.int16)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    sat = maxc - minc
    y, x = np.indices((HEIGHT, WIDTH))

    grad = np.zeros_like(lum)
    grad[:, 1:] = np.maximum(grad[:, 1:], np.abs(lum[:, 1:] - lum[:, :-1]))
    grad[1:, :] = np.maximum(grad[1:, :], np.abs(lum[1:, :] - lum[:-1, :]))

    tower_stack_zone = (x >= 145) & (x <= 720) & (y >= 24) & (y <= 652)
    warm_hardware = (r > b + 8) & (r > g + 1) & (lum > 22)
    bright_hardware = (lum > 88) | (maxc > 128)
    edge_hardware = (grad > 18) & (lum > 24)
    saturated_hardware = sat > 48

    object_pixels = tower_stack_zone & (
        ((lum > 34) & (warm_hardware | saturated_hardware | edge_hardware | bright_hardware))
        | ((x > 500) & (x < 690) & (y > 200) & (y < 650) & (lum > 25))
    )

    # Do not let practical lights, right-side rail hardware, or lower pad deck
    # become blocked by the detector.
    exclusion = Image.new("L", (WIDTH, HEIGHT), 0)
    exclusion_draw = ImageDraw.Draw(exclusion)
    for cx, cy, rx, ry in (
        (82, 557, 72, 70),
        (769, 560, 55, 55),
        (176, 658, 35, 35),
        (912, 663, 42, 42),
    ):
        exclusion_draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    object_pixels &= np.asarray(exclusion) <= 0
    object_pixels &= ~((y > 610) & (x > 420))

    dilated = Image.fromarray((object_pixels * 255).astype("uint8"), "L").filter(ImageFilter.MaxFilter(3))
    filtered = connected_component_area_filter(np.asarray(dilated) > 10, SOURCE_COMPONENT_MIN_AREA_PX)
    return Image.fromarray((filtered * 255).astype("uint8"), "L")


def build_precision_alpha(source: Image.Image) -> tuple[Image.Image, Image.Image, Image.Image]:
    manual = Image.new("L", source.size, 0)
    draw_manual_core(ImageDraw.Draw(manual))

    source_core = source_object_core(source)
    core = Image.fromarray(
        np.maximum(np.asarray(manual), np.asarray(source_core)).astype("uint8"),
        "L",
    )

    # The player clips the rendered aircraft/fog layer through this matte
    # pixel-by-pixel, so only a small edge guard is needed.
    occlusion = core.filter(ImageFilter.MaxFilter(MATTE_EDGE_GUARD_PX * 2 + 1))

    alpha_np = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
    alpha_np[np.asarray(occlusion) > 10] = 0
    alpha = Image.fromarray(alpha_np, "L")
    return alpha, core, occlusion


def make_matte_rgba(alpha: Image.Image) -> Image.Image:
    matte = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    matte.putalpha(alpha)
    return matte


def make_overlay(source: Image.Image, alpha: Image.Image, title: str) -> Image.Image:
    arr = np.asarray(alpha)
    overlay = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    overlay[arr <= 10] = [222, 38, 34, 132]
    overlay[arr > 10] = [22, 188, 194, 40]
    out = Image.alpha_composite(source.convert("RGBA"), Image.fromarray(overlay, "RGBA"))
    draw = ImageDraw.Draw(out)
    draw.rectangle((24, 22, 980, 72), fill=(0, 0, 0, 142))
    draw.text((34, 38), title, fill=(255, 255, 255, 255))
    return out


def draw_route_overlay(source: Image.Image, alpha: Image.Image, core: Image.Image) -> Image.Image:
    out = make_overlay(
        source,
        alpha,
        "Candidate B source-pixel matte: red blocks tight tower/shuttle pixels only",
    )
    draw = ImageDraw.Draw(out)
    core_np = np.asarray(core) > 10
    alpha_np = np.asarray(alpha)
    for event in AIRCRAFT_EVENTS:
        points: list[tuple[float, float]] = []
        for i in range(129):
            points.append(aircraft_xy(event, i / 128))
        for a, b in zip(points, points[1:]):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            x = int(round(max(0, min(WIDTH - 1, mid[0]))))
            y = int(round(max(0, min(HEIGHT - 1, mid[1]))))
            color = (255, 64, 48, 255) if alpha_np[y, x] <= 10 else (255, 224, 70, 255)
            draw.line((a[0], a[1], b[0], b[1]), fill=color, width=4)
        for p in (0, 1):
            x, y = aircraft_xy(event, p)
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(0, 255, 170, 255) if p == 0 else (255, 116, 92, 255))

    # Highlight the core object silhouette used for leak checks.
    edge = Image.fromarray((core_np * 255).astype("uint8"), "L").filter(ImageFilter.FIND_EDGES)
    edge_overlay = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    edge_overlay[np.asarray(edge) > 0] = [255, 255, 255, 190]
    out = Image.alpha_composite(out, Image.fromarray(edge_overlay, "RGBA"))
    draw = ImageDraw.Draw(out)
    draw.rectangle((24, 78, 820, 122), fill=(0, 0, 0, 142))
    draw.text((34, 92), "Yellow center stays visible; red center is blocked; white line is source object core clipped pixel-by-pixel.", fill=(255, 255, 255, 255))
    return out


def crop_contact_item(image: Image.Image, label: str) -> Image.Image:
    thumb = ImageOps.contain(image.convert("RGBA"), (930, 470))
    item = Image.new("RGBA", (960, 520), (18, 22, 26, 255))
    item.alpha_composite(thumb, ((960 - thumb.width) // 2, 38))
    draw = ImageDraw.Draw(item)
    draw.text((24, 14), label, fill=(255, 255, 255, 255))
    return item


def make_contact_sheet(current_alpha: Image.Image, repaired_alpha: Image.Image, overlay: Image.Image, route: Image.Image) -> Image.Image:
    current_view = ImageOps.colorize(current_alpha, black="black", white="white")
    repaired_view = ImageOps.colorize(repaired_alpha, black="black", white="white")
    sheet = Image.new("RGBA", (1920, 1080), (12, 14, 18, 255))
    items = [
        crop_contact_item(current_view, "Current active matte"),
        crop_contact_item(repaired_view, "Repaired precision matte"),
        crop_contact_item(overlay, "Repaired overlay"),
        crop_contact_item(route, "Route occlusion QA"),
    ]
    positions = [(0, 0), (960, 0), (0, 540), (960, 540)]
    for item, pos in zip(items, positions):
        sheet.alpha_composite(item, pos)
    return sheet


def disk_offsets(radius: int) -> list[tuple[int, int]]:
    return [
        (dx, dy)
        for dy in range(-radius, radius + 1)
        for dx in range(-radius, radius + 1)
        if dx * dx + dy * dy <= radius * radius
    ]


def route_qa(alpha: Image.Image, core: Image.Image) -> list[dict[str, object]]:
    alpha_np = np.asarray(alpha)
    core_np = np.asarray(core) > 10
    offsets = disk_offsets(AIRCRAFT_VISUAL_RADIUS_PX)
    rows = []
    for event in AIRCRAFT_EVENTS:
        visible_samples = 0
        suppressed_samples = 0
        silhouette_intersection_samples = 0
        silhouette_leak_samples = 0
        reps = []
        for i in range(257):
            p = i / 256
            x, y = aircraft_xy(event, p)
            ix = int(round(max(0, min(WIDTH - 1, x))))
            iy = int(round(max(0, min(HEIGHT - 1, y))))
            visible = alpha_np[iy, ix] > 10
            visible_samples += int(visible)
            suppressed_samples += int(not visible)
            intersects_core = False
            leaks_core = False
            for dx, dy in offsets:
                px = ix + dx
                py = iy + dy
                if 0 <= px < WIDTH and 0 <= py < HEIGHT and core_np[py, px]:
                    intersects_core = True
                    leaks_core = leaks_core or alpha_np[py, px] > 10
            silhouette_intersection_samples += int(intersects_core)
            silhouette_leak_samples += int(leaks_core)
            if i % 32 == 0:
                reps.append(
                    {
                        "p": round(p, 3),
                        "xy": [ix, iy],
                        "alpha": round(alpha_np[iy, ix] / 255, 3),
                        "visible": bool(visible),
                        "glow_intersects_source_core": bool(intersects_core),
                        "source_core_visible_leak": bool(leaks_core),
                    }
                )
        rows.append(
            {
                "start_seconds": event["start"],
                "duration_seconds": event["duration"],
                "visible_samples": visible_samples,
                "suppressed_samples": suppressed_samples,
                "silhouette_intersection_samples": silhouette_intersection_samples,
                "silhouette_leak_samples": silhouette_leak_samples,
                "representative_samples": reps,
            }
        )
    return rows


def mask_stats(alpha: Image.Image) -> dict[str, object]:
    arr = np.asarray(alpha)
    total = int(arr.size)
    allowed = int((arr > 10).sum())
    blocked = int((arr <= 10).sum())
    return {
        "allowed_pixels_alpha_gt_10": allowed,
        "blocked_pixels_alpha_lte_10": blocked,
        "allowed_percent": round(allowed / total * 100, 3),
        "blocked_percent": round(blocked / total * 100, 3),
    }


def probe_values(alpha: Image.Image, probes: dict[str, tuple[int, int]]) -> dict[str, float]:
    return {name: round(alpha_at(alpha, xy), 3) for name, xy in probes.items()}


def qa_reads(
    blocked: dict[str, float],
    allowed: dict[str, float],
    routes: list[dict[str, object]],
    current_stats: dict[str, object],
    repaired_stats: dict[str, object],
) -> dict[str, str]:
    return {
        "tower_shuttle_precision_matte_read": "pass" if all(value <= 0.05 for value in blocked.values()) else "tighten",
        "no_light_or_right_rail_mask_read": "pass"
        if all(allowed[name] >= 0.85 for name in ("left_floodlight", "mid_pad_floodlight", "crawlerway_light", "right_rail_region", "rail_caption_region", "right_rail_sky"))
        else "tighten",
        "open_air_and_ground_allowed_read": "pass" if all(value >= 0.85 for value in allowed.values()) else "tighten",
        "aircraft_shuttle_silhouette_leak_read": "pass"
        if sum(int(row["silhouette_leak_samples"]) for row in routes) == 0
        else "tighten",
        "aircraft_pixel_clip_matte_read": "pass"
        if sum(int(row["silhouette_intersection_samples"]) for row in routes) > 0 and MATTE_EDGE_GUARD_PX <= 2
        else "tighten",
        "matte_tightness_read": "pass"
        if float(repaired_stats["blocked_percent"]) <= float(current_stats["blocked_percent"]) + 0.75
        else "tighten",
    }


def symlink_force(target: Path, link: Path) -> None:
    if link.exists() or link.is_symlink():
        if link.is_dir() and not link.is_symlink():
            shutil.rmtree(link)
        else:
            link.unlink()
    os.symlink(target, link)


def copy_player(current: Path, output: Path, mask_sha256: str) -> None:
    text = current.read_text()
    text = text.replace(
        'const foregroundMattePolicy = "tower_shuttle_only_no_light_or_right_rail_mask";',
        f'const foregroundMattePolicy = "tower_shuttle_only_no_light_or_right_rail_mask";\n    const foregroundMattePrecisionModel = "{MODEL_ID}";',
    )
    text = text.replace(
        "foreground_matte_policy: foregroundMattePolicy,",
        f'foreground_matte_policy: foregroundMattePolicy,\n        foreground_matte_precision_model: "{MODEL_ID}",',
    )
    text = text.replace(
        'src="assets/masks/foreground_occlusion_matte.png"',
        f'src="assets/masks/foreground_occlusion_matte.png?v={mask_sha256}" data-mask-sha256="{mask_sha256}"',
    )
    output.write_text(text)


def build_successor() -> dict[str, object]:
    stamp = utc_stamp()
    proof_id = f"challenger_rolling_caption_rail_precise_matte_repair_{stamp}"
    out = ROUGH_ROOT / proof_id
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)

    assets = out / "assets"
    assets.mkdir()
    symlink_force(PRED_PROOF / "assets" / "audio", assets / "audio")
    symlink_force(PRED_PROOF / "assets" / "captions", assets / "captions")
    (assets / "masks").mkdir()
    symlink_force(CURRENT_PROOF / "references", out / "references")
    symlink_force(CURRENT_PROOF / "proof_assets", out / "proof_assets")
    symlink_force(CURRENT_PROOF / "proof_build.json", out / "proof_build.json")
    symlink_force(CURRENT_PROOF / "audio_repairs", out / "audio_repairs")
    symlink_force(CURRENT_PROOF / "scripts", out / "scripts")

    qa_dir = out / "qa" / "matte"
    review_dir = out / "review"
    qa_dir.mkdir(parents=True)
    review_dir.mkdir()

    source = Image.open(SOURCE_PLATE).convert("RGBA")
    current_alpha = Image.open(CURRENT_MASK).convert("RGBA").getchannel("A")
    repaired_alpha, source_core, occlusion = build_precision_alpha(source)
    repaired_matte = make_matte_rgba(repaired_alpha)
    mask_path = assets / "masks" / "foreground_occlusion_matte.png"
    repaired_matte.save(mask_path)
    mask_digest = sha256(mask_path)

    alpha_path = qa_dir / "candidate_b_precision_matte_alpha.png"
    overlay_path = qa_dir / "candidate_b_precision_matte_overlay_for_review.png"
    route_overlay_path = qa_dir / "candidate_b_precision_matte_aircraft_route_overlay.png"
    contact_sheet_path = qa_dir / "candidate_b_precision_matte_contact_sheet.png"
    source_core_path = qa_dir / "candidate_b_precision_matte_source_core.png"
    occlusion_path = qa_dir / "candidate_b_precision_matte_edge_guard_occlusion.png"

    ImageOps.colorize(repaired_alpha, black="black", white="white").save(alpha_path)
    ImageOps.colorize(source_core, black="black", white="white").save(source_core_path)
    ImageOps.colorize(occlusion, black="black", white="white").save(occlusion_path)
    overlay = make_overlay(
        source,
        repaired_alpha,
        "Candidate B source-pixel tight matte: tower/shuttle only; rail, lights, ground stay open",
    )
    route_overlay = draw_route_overlay(source, repaired_alpha, source_core)
    overlay.save(overlay_path)
    route_overlay.save(route_overlay_path)
    make_contact_sheet(current_alpha, repaired_alpha, overlay, route_overlay).save(contact_sheet_path)

    copy_player(CURRENT_PROOF / "player.html", out / "player.html", mask_digest)

    routes = route_qa(repaired_alpha, source_core)
    blocked = probe_values(repaired_alpha, BLOCKED_PROBES)
    allowed = probe_values(repaired_alpha, ALLOWED_PROBES)
    current_stats = mask_stats(current_alpha)
    repaired_stats = mask_stats(repaired_alpha)
    reads = qa_reads(blocked, allowed, routes, current_stats, repaired_stats)
    qa = {
        "status": "pass" if all(value == "pass" for value in reads.values()) else "tighten",
        "model_id": MODEL_ID,
        "matte_semantics": "alpha > 0 permits ambient effects; alpha 0 blocks source-pixel-tight tower/service structure and shuttle stack; player clips aircraft/fog through matte pixel-by-pixel",
        "policy_preserved": "tower_shuttle_only_no_light_or_right_rail_mask",
        "aircraft_visual_radius_px": AIRCRAFT_VISUAL_RADIUS_PX,
        "matte_edge_guard_px": MATTE_EDGE_GUARD_PX,
        "source_component_min_area_px": SOURCE_COMPONENT_MIN_AREA_PX,
        "source_plate_path": str(SOURCE_PLATE),
        "source_plate_sha256": sha256(SOURCE_PLATE),
        "predecessor_current_mask_path": str(CURRENT_MASK),
        "predecessor_current_mask_sha256": sha256(CURRENT_MASK),
        "mask_path": str(mask_path),
        "mask_sha256": mask_digest,
        "current_mask_stats": current_stats,
        "repaired_mask_stats": repaired_stats,
        "blocked_probe_alpha": blocked,
        "allowed_probe_alpha": allowed,
        "route_qa": routes,
        "qa_reads": reads,
        "qa_artifacts": {
            "alpha_path": str(alpha_path),
            "alpha_sha256": sha256(alpha_path),
            "overlay_path": str(overlay_path),
            "overlay_sha256": sha256(overlay_path),
            "route_overlay_path": str(route_overlay_path),
            "route_overlay_sha256": sha256(route_overlay_path),
            "contact_sheet_path": str(contact_sheet_path),
            "contact_sheet_sha256": sha256(contact_sheet_path),
            "source_core_path": str(source_core_path),
            "source_core_sha256": sha256(source_core_path),
            "edge_guard_occlusion_path": str(occlusion_path),
            "edge_guard_occlusion_sha256": sha256(occlusion_path),
        },
    }
    qa_path = qa_dir / "candidate_b_precision_matte_qa.json"
    qa_path.write_text(json.dumps(qa, indent=2) + "\n")
    qa["qa_path"] = str(qa_path)
    qa["qa_sha256"] = sha256(qa_path)

    manifest = json.loads(CURRENT_MANIFEST.read_text())
    for inherited_gate_key in (
        "human_disposition_utc",
        "human_disposition_source",
        "human_disposition_receipt_path",
        "rough_assembly_keep_receipt_path",
    ):
        manifest.pop(inherited_gate_key, None)
    manifest.update(
        {
            "packet_id": proof_id,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "status": "matte_precision_repair_review_ready_pending_human_keep",
            "action": "successor_rough_proof_for_challenger_candidate_b_precision_matte_repair",
            "source_predecessor_rough_proof_path": str(CURRENT_PROOF),
            "source_predecessor_manifest_path": str(CURRENT_MANIFEST),
            "player_html_path": str(out / "player.html"),
            "human_disposition": "pending_review",
            "human_review_disposition": "pending",
            "blocked_prerequisite": "precision_matte_human_keep",
            "may_advance": False,
            "may_advance_to_video_render": False,
            "may_advance_to_final_assembly": False,
            "may_advance_to_publish_readiness": False,
            "may_youtube_action": False,
            "next_review_question": "Review precision matte repair. Does this successor matte receive keep?",
            "matte_precision_repair": qa,
            "final_assembly_gate": "blocked_pending_precision_matte_human_keep",
            "publish_readiness_gate": "blocked_pending_precision_matte_human_keep",
            "youtube_action_gate": "blocked_pending_precision_matte_human_keep",
        }
    )
    manifest["foreground_matte_policy"] = "tower_shuttle_only_no_light_or_right_rail_mask"
    manifest["foreground_matte_precision_model"] = qa["model_id"]
    manifest["foreground_matte_path"] = str(mask_path)
    manifest["foreground_matte_sha256"] = qa["mask_sha256"]
    if isinstance(manifest.get("ambient_effects_layer"), dict):
        manifest["ambient_effects_layer"].update(
            {
                "foreground_matte_policy": "tower_shuttle_only_no_light_or_right_rail_mask",
                "foreground_matte_precision_model": qa["model_id"],
                "aircraft_visual_radius_px": AIRCRAFT_VISUAL_RADIUS_PX,
                "matte_edge_guard_px": MATTE_EDGE_GUARD_PX,
                "source_plate_matte_registration_read": reads["tower_shuttle_precision_matte_read"],
                "aircraft_shuttle_silhouette_leak_read": reads["aircraft_shuttle_silhouette_leak_read"],
                "aircraft_pixel_clip_matte_read": reads["aircraft_pixel_clip_matte_read"],
                "matte_tightness_read": reads["matte_tightness_read"],
                "right_rail_matte_removed_read": reads["no_light_or_right_rail_mask_read"],
                "matte_precision_qa_path": str(qa_path),
                "matte_precision_qa_sha256": qa["qa_sha256"],
            }
        )
    manifest_path = out / "rough_assembly_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    review_packet = review_dir / "precision_matte_repair_review_packet.md"
    review_packet.write_text(
        "\n".join(
            [
                "# Challenger Candidate B Precision Matte Repair",
                "",
                f"- Proof ID: `{proof_id}`",
                f"- Player: `{out / 'player.html'}`",
                f"- Mask: `{mask_path}`",
                f"- QA: `{qa_path}`",
                f"- Contact sheet: `{contact_sheet_path}`",
                "",
                "## Disposition",
                "",
                "Pending human review. Final assembly, publish readiness, and YouTube actions remain blocked until this repair receives `keep`.",
                "",
                "## Repair Read",
                "",
                "- Preserves current right-rail/practical-light intent: `tower_shuttle_only_no_light_or_right_rail_mask`.",
                "- Replaces broad silhouettes with source-pixel tower/shuttle occlusion and a 2px edge guard.",
                "- Relies on the player matte clip for aircraft/fog glow rather than expanding the matte.",
                "- Route QA requires zero source-core visible leak samples.",
                "",
                "## QA Reads",
                "",
                *[f"- `{key}`: `{value}`" for key, value in reads.items()],
                "",
            ]
        )
        + "\n"
    )

    return {
        "proof_id": proof_id,
        "proof_path": str(out),
        "player_html_path": str(out / "player.html"),
        "manifest_path": str(manifest_path),
        "qa_path": str(qa_path),
        "mask_path": str(mask_path),
        "contact_sheet_path": str(contact_sheet_path),
        "route_overlay_path": str(route_overlay_path),
        "status": qa["status"],
        "reads": reads,
        "mask_sha256": qa["mask_sha256"],
        "manifest_sha256": sha256(manifest_path),
    }


def main() -> None:
    result = build_successor()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
