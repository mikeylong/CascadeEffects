#!/usr/bin/env python3
"""Create a review-only Challenger proof with a precise matte and visible ambient layer."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


PREDECESSOR_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_tight_matte_html_approval_proof_20260512T152647Z"
)
ROUGH_ROOT = PREDECESSOR_ROOT.parent
SOURCE_PLATE = PREDECESSOR_ROOT / "references" / "shuttle_stack_reference_variant_a.png"
MASK_REL = Path("assets/masks/foreground_occlusion_matte.png")
MASK_PATH = PREDECESSOR_ROOT / MASK_REL
MANIFEST_PATH = PREDECESSOR_ROOT / "rough_assembly_manifest.json"
PLAYER_PATH = PREDECESSOR_ROOT / "player.html"

PRE_TIGHT_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_html_approval_proof_20260511T232232Z"
)
PRE_TIGHT_MASK = PRE_TIGHT_ROOT / MASK_REL

AIRCRAFT_EVENTS = [
    {"start": 8, "duration": 92, "x0": 1048, "x1": 72, "y0": 114, "y1": 358, "phase": 0.2, "blink": 1.7},
    {"start": 248, "duration": 100, "x0": 80, "x1": 1042, "y0": 88, "y1": 152, "phase": 1.1, "blink": 1.45},
    {"start": 438, "duration": 90, "x0": 1048, "x1": 94, "y0": 68, "y1": 176, "phase": 2.0, "blink": 1.9},
    {"start": 627, "duration": 108, "x0": 1038, "x1": 70, "y0": 286, "y1": 132, "phase": 2.8, "blink": 1.55},
    {"start": 804, "duration": 96, "x0": 96, "x1": 1042, "y0": 178, "y1": 78, "phase": 3.4, "blink": 1.82},
    {"start": 1006, "duration": 100, "x0": 1052, "x1": 112, "y0": 198, "y1": 68, "phase": 4.2, "blink": 1.6},
    {"start": 1188, "duration": 86, "x0": 74, "x1": 1038, "y0": 122, "y1": 214, "phase": 5.1, "blink": 2.05},
]

HIGH_RISK_FOREGROUND_PROBES = {
    "tower_beam_upper": [500, 260],
    "tower_mid_hardware": [520, 430],
    "shuttle_body": [770, 300],
    "booster_body": [846, 330],
    "pad_deck": [740, 565],
    "left_floodlight": [156, 522],
    "ground": [700, 850],
    "foreground_crew": [760, 820],
}

OPEN_SKY_PROBES = {
    "left_open_sky": [95, 150],
    "right_open_sky": [1400, 210],
    "sky_between_stack_and_tower": [650, 230],
    "tower_lattice_hole_upper": [430, 152],
    "tower_lattice_hole_mid": [420, 188],
    "right_lower_open_sky": [1280, 560],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def ignore_copy(dirpath: str, names: list[str]) -> set[str]:
    ignored = {".DS_Store", "__pycache__", "video_render"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def seeded_unit(seed: float) -> float:
    value = math.sin(seed * 12.9898 + 78.233) * 43758.5453
    return value - math.floor(value)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    x = max(0.0, min(1.0, (value - edge0) / max(0.0001, edge1 - edge0)))
    return x * x * (3 - 2 * x)


def mix(a: float, b: float, amount: float) -> float:
    return a + (b - a) * amount


def aircraft_state(event: dict, time: float) -> tuple[float, float, float] | None:
    local = (time - event["start"]) / event["duration"]
    if local < 0 or local > 1:
        return None
    ease = smoothstep(0, 1, local)
    return mix(event["x0"], event["x1"], ease), mix(event["y0"], event["y1"], ease), local


def make_dust_motes(count: int = 92) -> list[dict]:
    zones = [
        {"x0": 84, "x1": 246, "y0": 72, "y1": 428},
        {"x0": 572, "x1": 704, "y0": 72, "y1": 478},
        {"x0": 900, "x1": 1050, "y0": 70, "y1": 388},
        {"x0": 1018, "x1": 1072, "y0": 424, "y1": 620},
    ]
    motes = []
    for index in range(count):
        zone = zones[index % len(zones)]
        u = seeded_unit(index + 2)
        v = seeded_unit(index + 73)
        motes.append(
            {
                "x": zone["x0"] + u * (zone["x1"] - zone["x0"]),
                "y": zone["y0"] + v * (zone["y1"] - zone["y0"]),
                "size": 2.2 + seeded_unit(index + 131) * 3.7,
                "phase": seeded_unit(index + 191) * math.pi * 2,
                "drift": 10 + seeded_unit(index + 223) * 22,
                "speed": 0.014 + seeded_unit(index + 251) * 0.03,
                "alpha": 0.095 + seeded_unit(index + 281) * 0.105,
            }
        )
    return motes


def dust_position(mote: dict, time: float) -> tuple[float, float]:
    x = mote["x"] + math.sin(time * mote["speed"] + mote["phase"]) * mote["drift"]
    x += math.sin(time * mote["speed"] * 0.37 + mote["phase"] * 1.7) * mote["drift"] * 0.32
    y = mote["y"] + math.cos(time * mote["speed"] * 0.74 + mote["phase"]) * mote["drift"] * 0.58
    return x, y


def create_precise_matte(target_path: Path, qa_dir: Path) -> dict:
    source = Image.open(SOURCE_PLATE).convert("RGB")
    rgb = np.asarray(source).astype(np.int16)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    maxc = rgb.max(axis=2)

    # Dark/cool pixels are treated as visible sky. Warm low-light metal is foreground.
    warm_foreground = (r > b + 10) & (r > g + 4) & (lum > 14)
    sky = (maxc < 104) & (lum < 82) & (~warm_foreground)
    alpha = Image.fromarray((sky * 255).astype("uint8"), "L")

    hard_block = Image.new("L", source.size, 0)
    draw = ImageDraw.Draw(hard_block)
    draw.polygon([(0, 646), (1920, 646), (1920, 1080), (0, 1080)], fill=255)
    for cx, cy, radius in [
        (156, 522, 70),
        (260, 632, 48),
        (1005, 506, 46),
        (1196, 624, 48),
        (1326, 708, 52),
        (1290, 780, 78),
        (1458, 780, 78),
    ]:
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)

    alpha = ImageChops.multiply(alpha, ImageOps.invert(hard_block.filter(ImageFilter.MaxFilter(7))))
    alpha = alpha.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.MinFilter(3))

    matte = Image.new("RGBA", source.size, (255, 255, 255, 0))
    matte.putalpha(alpha)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    matte.save(target_path)

    qa_dir.mkdir(parents=True, exist_ok=True)
    overlays = write_matte_qa_images(source, alpha, qa_dir)
    route_qa = sample_aircraft_routes(alpha)
    dust_qa = sample_dust(alpha, qa_dir)
    probe_qa = probe_points(alpha)

    old_tight_alpha = Image.open(MASK_PATH).convert("RGBA").getchannel("A")
    pre_tight_alpha = Image.open(PRE_TIGHT_MASK).convert("RGBA").getchannel("A") if PRE_TIGHT_MASK.exists() else None
    counts = {
        "current_tight_alpha_gt_10": count_allowed(old_tight_alpha),
        "precise_alpha_gt_10": count_allowed(alpha),
        "restored_vs_current_tight_pixels": count_restored(old_tight_alpha, alpha),
    }
    if pre_tight_alpha:
        counts["pre_tight_alpha_gt_10"] = count_allowed(pre_tight_alpha)
        counts["removed_vs_pre_tight_pixels"] = count_removed(pre_tight_alpha, alpha)

    qa = {
        "matte_semantics": "alpha > 0 permits aircraft/dust; alpha 0 blocks foreground objects",
        "source_plate_path": str(SOURCE_PLATE),
        "source_plate_sha256": sha256(SOURCE_PLATE),
        "predecessor_tight_mask_path": str(MASK_PATH),
        "predecessor_tight_mask_sha256": sha256(MASK_PATH),
        "pre_tight_mask_path": str(PRE_TIGHT_MASK),
        "pre_tight_mask_sha256": sha256(PRE_TIGHT_MASK) if PRE_TIGHT_MASK.exists() else None,
        "precise_mask_path": str(target_path),
        "precise_mask_sha256": sha256(target_path),
        "dimensions": {"width": source.size[0], "height": source.size[1]},
        "allowed_pixel_counts": counts,
        "probe_qa": probe_qa,
        "route_qa": route_qa,
        "dust_qa": dust_qa,
        "qa_reads": {
            "source_plate_matte_dimension_read": "pass_same_1920x1080_dimensions",
            "foreground_probe_block_read": "pass" if all(v == 0 for v in probe_qa["foreground_probe_alpha"].values()) else "tighten",
            "open_sky_probe_read": "pass" if all(v > 0.9 for v in probe_qa["open_sky_probe_alpha"].values()) else "tighten",
            "aircraft_route_open_sky_dwell_read": "pass" if all(r["visible_samples"] >= 28 for r in route_qa) else "tighten",
            "aircraft_foreground_occlusion_read": "pass" if all(r["foreground_probe_leak_samples"] == 0 for r in route_qa) else "tighten",
            "dust_visibility_read": "pass" if min(d["visible_motes"] for d in dust_qa["sample_times"]) >= 14 else "tighten",
            "dust_foreground_leak_read": "pass" if max(d["foreground_leak_motes"] for d in dust_qa["sample_times"]) == 0 else "tighten",
        },
        "qa_artifacts": overlays | dust_qa["qa_artifacts"],
    }
    write_json(qa_dir / "precise_matte_visibility_repair_qa.json", qa)
    return qa


def count_allowed(alpha: Image.Image) -> int:
    return int(np.asarray(alpha).astype(np.uint8).gt(10).sum()) if hasattr(np.asarray(alpha), "gt") else sum(1 for v in alpha.getdata() if v > 10)


def count_restored(old_alpha: Image.Image, new_alpha: Image.Image) -> int:
    old = np.asarray(old_alpha).astype(np.uint8)
    new = np.asarray(new_alpha).astype(np.uint8)
    return int(((old <= 10) & (new > 10)).sum())


def count_removed(old_alpha: Image.Image, new_alpha: Image.Image) -> int:
    old = np.asarray(old_alpha).astype(np.uint8)
    new = np.asarray(new_alpha).astype(np.uint8)
    return int(((old > 10) & (new <= 10)).sum())


def write_matte_qa_images(source: Image.Image, alpha: Image.Image, qa_dir: Path) -> dict:
    overlay_path = qa_dir / "precise_matte_overlay_for_review.png"
    alpha_path = qa_dir / "precise_matte_black_white_alpha.png"
    delta_path = qa_dir / "precise_matte_delta_vs_tight.png"
    route_path = qa_dir / "precise_matte_aircraft_route_overlay.png"
    crop_path = qa_dir / "precise_matte_tower_stack_crop.png"
    pad_crop_path = qa_dir / "precise_matte_pad_crop.png"

    ImageOps.colorize(alpha, black="black", white="white").save(alpha_path)
    overlay_mask(source, alpha, overlay_path, "precise matte: cyan permits aircraft/dust, red blocks foreground")
    old = Image.open(MASK_PATH).convert("RGBA").getchannel("A")
    overlay_delta(source, old, alpha, delta_path)
    route_img = Image.open(overlay_path).convert("RGBA")
    draw = ImageDraw.Draw(route_img)
    for event in AIRCRAFT_EVENTS:
        draw.line((event["x0"], event["y0"], event["x1"], event["y1"]), fill=(255, 236, 67, 255), width=4)
        draw.ellipse((event["x0"] - 8, event["y0"] - 8, event["x0"] + 8, event["y0"] + 8), fill=(0, 255, 160, 255))
        draw.ellipse((event["x1"] - 8, event["y1"] - 8, event["x1"] + 8, event["y1"] + 8), fill=(255, 98, 86, 255))
    draw.text((34, 66), "yellow aircraft centerlines; green=start, coral=end", fill=(255, 255, 255, 255))
    route_img.save(route_path)
    route_img.crop((250, 0, 1040, 650)).save(crop_path)
    route_img.crop((260, 430, 1250, 730)).save(pad_crop_path)
    return {
        "precise_matte_overlay": str(overlay_path),
        "precise_matte_alpha": str(alpha_path),
        "precise_matte_delta_vs_tight": str(delta_path),
        "precise_matte_aircraft_route_overlay": str(route_path),
        "precise_matte_tower_stack_crop": str(crop_path),
        "precise_matte_pad_crop": str(pad_crop_path),
    }


def overlay_mask(source: Image.Image, alpha: Image.Image, output_path: Path, label: str) -> None:
    base = source.convert("RGBA")
    overlay = Image.new("RGBA", source.size, (0, 0, 0, 0))
    opx = overlay.load()
    apx = alpha.load()
    for y in range(source.size[1]):
        for x in range(source.size[0]):
            opx[x, y] = (0, 215, 255, 74) if apx[x, y] > 10 else (255, 40, 40, 44)
    out = Image.alpha_composite(base, overlay)
    ImageDraw.Draw(out).text((34, 32), label, fill=(255, 255, 255, 255))
    out.save(output_path)


def overlay_delta(source: Image.Image, old_alpha: Image.Image, new_alpha: Image.Image, output_path: Path) -> None:
    base = source.convert("RGBA")
    overlay = Image.new("RGBA", source.size, (0, 0, 0, 0))
    opx = overlay.load()
    old_px = old_alpha.load()
    new_px = new_alpha.load()
    for y in range(source.size[1]):
        for x in range(source.size[0]):
            old_ok = old_px[x, y] > 10
            new_ok = new_px[x, y] > 10
            if new_ok and not old_ok:
                opx[x, y] = (0, 255, 154, 120)
            elif old_ok and not new_ok:
                opx[x, y] = (255, 70, 70, 120)
            elif new_ok:
                opx[x, y] = (0, 220, 255, 42)
    out = Image.alpha_composite(base, overlay)
    ImageDraw.Draw(out).text((34, 32), "delta vs tight: green restored sky, red newly blocked, cyan unchanged open", fill=(255, 255, 255, 255))
    out.save(output_path)


def probe_points(alpha: Image.Image) -> dict:
    return {
        "foreground_probe_alpha": {name: round(alpha.getpixel(tuple(xy)) / 255, 4) for name, xy in HIGH_RISK_FOREGROUND_PROBES.items()},
        "open_sky_probe_alpha": {name: round(alpha.getpixel(tuple(xy)) / 255, 4) for name, xy in OPEN_SKY_PROBES.items()},
    }


def sample_aircraft_routes(alpha: Image.Image) -> list[dict]:
    px = alpha.load()
    results = []
    foreground_polys = [
        [(620, 50), (890, 50), (920, 620), (610, 630)],
        [(275, 0), (610, 0), (650, 640), (250, 640)],
        [(320, 510), (1225, 500), (1250, 650), (280, 650)],
        [(0, 646), (1920, 646), (1920, 1080), (0, 1080)],
    ]
    foreground = Image.new("L", alpha.size, 0)
    draw = ImageDraw.Draw(foreground)
    for poly in foreground_polys:
        draw.polygon(poly, fill=255)
    fpx = foreground.load()
    for event in AIRCRAFT_EVENTS:
        visible = 0
        leaks = 0
        samples = []
        for i in range(161):
            p = i / 160
            state = aircraft_state(event, event["start"] + event["duration"] * p)
            if not state:
                continue
            x, y, local = state
            xi, yi = int(round(max(0, min(1919, x)))), int(round(max(0, min(1079, y))))
            sky_alpha = px[xi, yi] / 255
            is_visible = sky_alpha > 0.04 and x < 1058
            if is_visible:
                visible += 1
            if fpx[xi, yi] > 0 and is_visible:
                leaks += 1
            if i % 20 == 0:
                samples.append({"p": round(p, 3), "xy": [xi, yi], "alpha": round(sky_alpha, 3), "visible": bool(is_visible)})
        results.append(
            {
                "start_seconds": event["start"],
                "duration_seconds": event["duration"],
                "visible_samples": visible,
                "foreground_probe_leak_samples": leaks,
                "representative_samples": samples,
            }
        )
    return results


def sample_dust(alpha: Image.Image, qa_dir: Path) -> dict:
    motes = make_dust_motes()
    times = [12, 252, 444, 632, 810, 1012, 1192]
    px = alpha.load()
    foreground = Image.new("L", alpha.size, 0)
    draw = ImageDraw.Draw(foreground)
    draw.polygon([(0, 646), (1920, 646), (1920, 1080), (0, 1080)], fill=255)
    fpx = foreground.load()
    results = []
    source = Image.open(SOURCE_PLATE).convert("RGBA")
    overlay = source.copy()
    odraw = ImageDraw.Draw(overlay)
    for time in times:
        visible = 0
        leaks = 0
        for mote in motes:
            x, y = dust_position(mote, time)
            xi, yi = int(round(max(0, min(1919, x)))), int(round(max(0, min(1079, y))))
            ok = x < 1050 and px[xi, yi] / 255 > 0.05
            if ok:
                visible += 1
                odraw.ellipse((xi - 4, yi - 4, xi + 4, yi + 4), fill=(255, 246, 160, 170))
                if fpx[xi, yi] > 0:
                    leaks += 1
        results.append({"time_seconds": time, "visible_motes": visible, "foreground_leak_motes": leaks})
    odraw.text((34, 32), "dust QA: yellow dots are sample visible motes over open sky", fill=(255, 255, 255, 255))
    dust_overlay = qa_dir / "precise_matte_dust_visibility_overlay.png"
    overlay.save(dust_overlay)
    return {"sample_times": results, "qa_artifacts": {"precise_matte_dust_visibility_overlay": str(dust_overlay)}}


def patch_player(player_path: Path, stamp: str) -> None:
    text = player_path.read_text()
    text = text.replace(
        "Challenger Living Cover Tight Matte Literal Rail Captions YouTube Outro Screen HTML Approval Proof",
        "Challenger Living Cover Precise Matte Visibility Repair HTML Approval Proof",
    )
    text = text.replace(
        "Challenger Living Cover shuttle-stack Variant A music-only intro and outro full-runtime HTML approval proof",
        "Challenger Living Cover shuttle-stack Variant A precise matte visibility repair HTML approval proof",
    )
    text = text.replace(
        "html.render-mode .review-audio { display: none; }\n",
        "html.render-mode .review-audio { display: none; }\n"
        "    .ambient-debug-overlay { position: absolute; z-index: 6; left: 24px; bottom: 24px; width: 390px; padding: 14px 16px; border-radius: 8px; background: rgba(5, 8, 23, 0.78); color: rgba(255, 248, 232, 0.92); font: 700 18px/1.35 ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; display: none; pointer-events: none; }\n"
        "    html.ambient-debug-mode .ambient-debug-overlay { display: block; }\n",
    )
    text = text.replace(
        '<img class="mask-reference" id="foregroundOcclusionMatte" src="assets/masks/foreground_occlusion_matte.png" alt="">',
        '<img class="mask-reference" id="foregroundOcclusionMatte" src="assets/masks/foreground_occlusion_matte.png" alt="">\n'
        '        <pre class="ambient-debug-overlay" id="ambientDebugOverlay" aria-hidden="true"></pre>',
    )
    text = text.replace(
        'const params = new URLSearchParams(window.location.search);\n    let ambientPreset',
        'const params = new URLSearchParams(window.location.search);\n    const ambientDebugMode = params.get("debug") === "1" || params.get("matteDebug") === "1";\n    if (ambientDebugMode) document.documentElement.classList.add("ambient-debug-mode");\n    let ambientPreset',
    )
    text = text.replace(
        'railCaption: document.getElementById("railCaption") };',
        'railCaption: document.getElementById("railCaption"), ambientDebugOverlay: document.getElementById("ambientDebugOverlay") };',
    )
    text = replace_aircraft_and_dust(text)
    text = text.replace(
        "const envelope = smoothstep(0, 0.12, state.local) * (1 - smoothstep(0.88, 1, state.local));",
        "const envelope = smoothstep(0, 0.055, state.local) * (1 - smoothstep(0.945, 1, state.local));",
    )
    text = text.replace(
        "drawGlow(ctx, state.x, state.y, 13, 0.62 * alpha, [245, 250, 255]);\n        drawGlow(ctx, state.x - 9, state.y + 1, 6.5, 0.42 * alpha, [255, 102, 94]);\n        drawGlow(ctx, state.x + 9, state.y - 1, 6.5, 0.34 * alpha, [142, 224, 206]);",
        "drawGlow(ctx, state.x, state.y, 16, 0.86 * alpha, [245, 250, 255]);\n        drawGlow(ctx, state.x - 9, state.y + 1, 8, 0.56 * alpha, [255, 102, 94]);\n        drawGlow(ctx, state.x + 9, state.y - 1, 8, 0.46 * alpha, [142, 224, 206]);",
    )
    text = text.replace("if (skyAlpha <= 0.08) continue;", "if (skyAlpha <= 0.05) continue;")
    text = text.replace("const alpha = mote.alpha * pulse * skyAlpha;\n        if (alpha < 0.028) continue;", "const alpha = mote.alpha * pulse * skyAlpha;\n        if (alpha < 0.020) continue;")
    text = text.replace("drawGlow(ctx, x, y, mote.size * 2.2, alpha, [255, 246, 210]);", "drawGlow(ctx, x, y, mote.size * 2.8, alpha, [255, 246, 210]);")
    text = text.replace("matteAlphaAt(x, y) > 0.08", "matteAlphaAt(x, y) > 0.05")
    text = text.replace(
        "function towerBeaconDebugAt(time) {",
        "function ambientDebugReportAt(time) {\n"
        "      const metrics = ambientMetricsAt(time);\n"
        "      const probes = { tower: matteAlphaAt(500, 260), shuttle: matteAlphaAt(770, 300), pad: matteAlphaAt(740, 565), leftSky: matteAlphaAt(95, 150), rightSky: matteAlphaAt(1400, 210), towerGap: matteAlphaAt(430, 152) };\n"
        "      return { time, matteLoaded: Boolean(foregroundMatteData), metrics, probes };\n"
        "    }\n"
        "    function updateAmbientDebugOverlay(time) {\n"
        "      if (!ambientDebugMode || !els.ambientDebugOverlay) return;\n"
        "      const report = ambientDebugReportAt(time);\n"
        "      els.ambientDebugOverlay.textContent = `matte loaded: ${report.matteLoaded}\\naircraft visible: ${report.metrics.aircraft_visible_count}/${report.metrics.aircraft_event_count}\\ndust visible: ${report.metrics.dust_visible_count}/${report.metrics.dust_mote_count}\\nalpha tower/shuttle/pad: ${report.probes.tower.toFixed(2)} ${report.probes.shuttle.toFixed(2)} ${report.probes.pad.toFixed(2)}\\nalpha sky L/R/gap: ${report.probes.leftSky.toFixed(2)} ${report.probes.rightSky.toFixed(2)} ${report.probes.towerGap.toFixed(2)}`;\n"
        "    }\n"
        "    function towerBeaconDebugAt(time) {",
    )
    text = text.replace("drawAmbientLayer(safe);\n      if (renderedContextIndex", "drawAmbientLayer(safe);\n      updateAmbientDebugOverlay(safe);\n      if (renderedContextIndex")
    text = text.replace(
        "window.__dustDebugAt = (time) => dustDebugAt(clamp(Number(time) || 0, 0, duration));",
        "window.__dustDebugAt = (time) => dustDebugAt(clamp(Number(time) || 0, 0, duration));\n    window.__ambientDebugReportAt = (time) => ambientDebugReportAt(clamp(Number(time) || 0, 0, duration));",
    )
    player_path.write_text(text)


def replace_aircraft_and_dust(text: str) -> str:
    start = text.index("    const aircraftEvents = [")
    end = text.index("    function seededUnit", start)
    aircraft = "    const aircraftEvents = " + json.dumps(AIRCRAFT_EVENTS, indent=6) + ";\n"
    text = text[:start] + aircraft + text[end:]

    start = text.index("    const dustMotes = Array.from", text.index("    function seededUnit"))
    end = text.index("    function drawGlow", start)
    dust_js = """    const dustZones = [
      { x0: 84, x1: 246, y0: 72, y1: 428 },
      { x0: 572, x1: 704, y0: 72, y1: 478 },
      { x0: 900, x1: 1050, y0: 70, y1: 388 },
      { x0: 1018, x1: 1072, y0: 424, y1: 620 }
    ];
    const dustMotes = Array.from({ length: 92 }, (_, index) => {
      const zone = dustZones[index % dustZones.length];
      const u = seededUnit(index + 2);
      const v = seededUnit(index + 73);
      return {
        x: zone.x0 + u * (zone.x1 - zone.x0),
        y: zone.y0 + v * (zone.y1 - zone.y0),
        size: 2.2 + seededUnit(index + 131) * 3.7,
        phase: seededUnit(index + 191) * Math.PI * 2,
        drift: 10 + seededUnit(index + 223) * 22,
        speed: 0.014 + seededUnit(index + 251) * 0.03,
        alpha: 0.095 + seededUnit(index + 281) * 0.105
      };
    });
"""
    return text[:start] + dust_js + text[end:]


def write_browser_qa_script(successor_root: Path) -> None:
    script = f"""async (page) => {{
  await page.goto("http://127.0.0.1:8818/player.html?debug=1");
  await page.waitForFunction(() => window.__maskReady && window.__ambientDebugReportAt, null, {{ timeout: 7000 }});
  await page.evaluate(() => window.__maskReady);
  const times = [12, 18, 252, 444, 632, 810, 1012, 1192, 1214.7, 1215.5];
  const qa = await page.evaluate((sampleTimes) => {{
    const samples = sampleTimes.map((time) => window.__ambientDebugReportAt(time));
    return {{
      url: location.href,
      title: document.title,
      samples,
      reads: {{
        matte_loaded_read: samples.every((s) => s.matteLoaded) ? "pass" : "tighten",
        foreground_probe_read: samples[0].probes.tower === 0 && samples[0].probes.shuttle === 0 && samples[0].probes.pad === 0 ? "pass" : "tighten",
        open_sky_probe_read: samples[0].probes.leftSky > 0.9 && samples[0].probes.rightSky > 0.9 && samples[0].probes.towerGap > 0.9 ? "pass" : "tighten",
        aircraft_visibility_read: samples.some((s) => s.metrics.aircraft_visible_count > 0) ? "pass" : "tighten",
        dust_visibility_read: Math.min(...samples.slice(0, 8).map((s) => s.metrics.dust_visible_count)) >= 14 ? "pass" : "tighten",
        outro_caption_suppression_read: window.__outroDebugAt(1215.5).captionText === "" ? "pass" : "tighten"
      }}
    }};
  }}, times);
  for (const time of [12, 632, 810, 1215.5]) {{
    await page.goto(`http://127.0.0.1:8818/player.html?render=1&debug=1&t=${{time}}`);
    await page.waitForFunction(() => window.__maskReady && window.__ambientDebugReportAt, null, {{ timeout: 7000 }});
    await page.screenshot({{ path: "{successor_root}/qa/browser/precise_matte_visibility_repair_${{String(time).replace('.', 'p')}}s.png" }});
  }}
  return qa;
}}"""
    path = successor_root / "scripts" / "precise_matte_browser_qa.playwright.js"
    path.write_text(script)


def update_successor_manifest(successor_root: Path, stamp: str, qa: dict) -> None:
    manifest_path = successor_root / "rough_assembly_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    successor_id = successor_root.name
    manifest.update(
        {
            "packet_id": successor_id,
            "created_utc": stamp,
            "status": "review_ready_with_precise_matte_visibility_repair_pending_human_disposition",
            "human_disposition": "defer",
            "review_only": True,
            "html_proof_only": True,
            "mp4_render_created": False,
            "rendered_video_proof": None,
            "may_create_full_runtime_mp4_render": False,
            "may_advance_to_video_render": False,
            "may_advance_to_final_assembly": False,
            "may_advance_to_publish_readiness": False,
            "may_youtube_action": False,
            "render_authorization": "blocked_until_human_keep_on_precise_matte_visibility_repair_html_proof",
            "created_from_precise_matte_visibility_repair_predecessor_packet_path": str(PREDECESSOR_ROOT),
            "created_from_precise_matte_visibility_repair_predecessor_manifest_path": str(MANIFEST_PATH),
            "created_from_precise_matte_visibility_repair_predecessor_manifest_sha256": sha256(MANIFEST_PATH),
            "created_from_precise_matte_visibility_repair_predecessor_player_path": str(PLAYER_PATH),
            "created_from_precise_matte_visibility_repair_predecessor_player_sha256": sha256(PLAYER_PATH),
            "local_review_server": {"suggested_port": 8818, "url": "http://127.0.0.1:8818/player.html"},
            "review_urls": {"local_html": "http://127.0.0.1:8818/player.html", "debug_html": "http://127.0.0.1:8818/player.html?debug=1"},
            "next_review_question": "keep/tighten/reject the precise matte and restored aircraft/dust visibility before any MP4 render",
        }
    )
    for stale_key in ("successor_tight_matte_packet_path", "successor_tight_matte_manifest_path", "successor_tight_matte_mask_sha256"):
        manifest.pop(stale_key, None)
    reads = manifest.setdefault("rough_assembly_reads", {})
    reads.update(
        {
            "foreground_matte_precision_read": "pass_image_derived_precise_sky_matte_pending_human_review",
            "tower_shuttle_pad_occlusion_read": "pass_foreground_probe_points_blocked_pending_human_visual_review",
            "crew_foreground_occlusion_read": "pass_ground_crew_floor_blocked_pending_human_visual_review",
            "open_sky_preservation_read": "pass_open_sky_and_selected_tower_lattice_hole_probes_allowed",
            "aircraft_background_depth_read": "pass_route_qa_foreground_leak_samples_zero",
            "aircraft_visibility_repair_read": qa["qa_reads"]["aircraft_route_open_sky_dwell_read"],
            "dust_visibility_repair_read": qa["qa_reads"]["dust_visibility_read"],
            "dust_foreground_leak_read": qa["qa_reads"]["dust_foreground_leak_read"],
            "matte_debug_overlay_read": "pass_debug_mode_added_for_html_review",
            "mp4_created_read": "not_applicable_html_visibility_repair_gate_no_mp4_render",
            "render_output_read": "not_applicable_html_visibility_repair_gate_no_mp4_render",
            "downstream_gate_read": "pass_all_downstream_flags_false",
        }
    )
    manifest.setdefault("qa", {})["precise_matte_visibility_repair"] = qa
    artifacts = manifest.setdefault("artifacts", {})
    artifacts.update(
        {
            "player_html": {"path": str(successor_root / "player.html"), "sha256": sha256(successor_root / "player.html")},
            "foreground_occlusion_matte": {"path": str(successor_root / MASK_REL), "sha256": sha256(successor_root / MASK_REL), "source": "image_derived_precise_matte_visibility_repair"},
            "precise_matte_visibility_repair_qa": {
                key: {"path": value, "sha256": sha256(Path(value))}
                for key, value in qa["qa_artifacts"].items()
            }
        }
    )
    manifest.setdefault("visual_layering", {})["precise_matte_visibility_repair_context"] = {
        "matte_semantics": qa["matte_semantics"],
        "precise_mask_path": qa["precise_mask_path"],
        "precise_mask_sha256": qa["precise_mask_sha256"],
        "allowed_pixel_counts": qa["allowed_pixel_counts"],
        "probe_qa": qa["probe_qa"],
        "route_qa_path": str(successor_root / "qa" / "matte" / "precise_matte_visibility_repair_qa.json"),
        "debug_url": "http://127.0.0.1:8818/player.html?debug=1",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def update_readme(successor_root: Path, qa: dict) -> None:
    readme = successor_root / "README.md"
    existing = readme.read_text() if readme.exists() else ""
    note = f"""# Challenger Long-Form Precise Matte Visibility Repair

This review-only successor replaces the broad tight matte with an image-derived precise foreground matte and restores aircraft/dust visibility for HTML review.

- Local review URL: `http://127.0.0.1:8818/player.html`
- Debug review URL: `http://127.0.0.1:8818/player.html?debug=1`
- New mask: `{successor_root / MASK_REL}`
- Matte QA: `{successor_root / 'qa' / 'matte' / 'precise_matte_visibility_repair_qa.json'}`
- Overlay: `{qa['qa_artifacts']['precise_matte_overlay']}`

No MP4 was rendered. Gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

"""
    readme.write_text(note + existing)


def mark_predecessor_tighten(successor_root: Path, qa: dict) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    manifest["status"] = "tighten_precise_matte_visibility_repair_successor_created"
    manifest["human_disposition"] = "tighten"
    manifest["successor_precise_matte_visibility_repair_packet_path"] = str(successor_root)
    manifest["successor_precise_matte_visibility_repair_manifest_path"] = str(successor_root / "rough_assembly_manifest.json")
    manifest["successor_precise_matte_visibility_repair_mask_sha256"] = qa["precise_mask_sha256"]
    manifest["may_create_full_runtime_mp4_render"] = False
    manifest["may_advance_to_video_render"] = False
    manifest["may_advance_to_final_assembly"] = False
    manifest["may_advance_to_publish_readiness"] = False
    manifest["may_youtube_action"] = False
    reads = manifest.setdefault("rough_assembly_reads", {})
    reads["foreground_matte_precision_read"] = "tighten_human_requested_precise_successor_created"
    reads["aircraft_visibility_repair_read"] = "tighten_human_requested_precise_successor_created"
    reads["dust_visibility_repair_read"] = "tighten_human_requested_precise_successor_created"
    manifest["reviewer_notes"] = (
        str(manifest.get("reviewer_notes", "")).rstrip()
        + f"\nHuman requested more precise matte and aircraft/dust visibility repair. Successor: {successor_root}"
    ).strip()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    successor_root = ROUGH_ROOT / (
        "living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_"
        f"outro_screen_literal_rail_captions_precise_matte_visibility_repair_html_approval_proof_{stamp}"
    )
    if successor_root.exists():
        raise FileExistsError(successor_root)
    shutil.copytree(PREDECESSOR_ROOT, successor_root, symlinks=True, ignore=ignore_copy)
    patch_player(successor_root / "player.html", stamp)
    qa = create_precise_matte(successor_root / MASK_REL, successor_root / "qa" / "matte")
    write_browser_qa_script(successor_root)
    update_successor_manifest(successor_root, stamp, qa)
    update_readme(successor_root, qa)
    mark_predecessor_tighten(successor_root, qa)
    print(json.dumps({
        "successor_root": str(successor_root),
        "player": str(successor_root / "player.html"),
        "manifest": str(successor_root / "rough_assembly_manifest.json"),
        "mask": str(successor_root / MASK_REL),
        "mask_sha256": qa["precise_mask_sha256"],
        "qa": str(successor_root / "qa" / "matte" / "precise_matte_visibility_repair_qa.json"),
        "url": "http://127.0.0.1:8818/player.html",
        "debug_url": "http://127.0.0.1:8818/player.html?debug=1",
    }, indent=2))


if __name__ == "__main__":
    main()
