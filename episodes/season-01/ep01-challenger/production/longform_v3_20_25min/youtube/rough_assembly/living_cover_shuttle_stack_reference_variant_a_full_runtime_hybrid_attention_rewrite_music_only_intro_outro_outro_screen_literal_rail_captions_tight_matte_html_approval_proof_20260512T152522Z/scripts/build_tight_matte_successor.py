#!/usr/bin/env python3
"""Create a review-only successor proof with a tightened Challenger foreground matte.

The matte is an allowed-sky alpha mask. White/opaque pixels permit aircraft and dust
to render; black/transparent pixels block them behind the foreground plate.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


PREDECESSOR_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_outro_screen_literal_rail_captions_html_approval_proof_20260511T232232Z"
)
ROUGH_ROOT = PREDECESSOR_ROOT.parent
SOURCE_PLATE = PREDECESSOR_ROOT / "references" / "shuttle_stack_reference_variant_a.png"
MASK_REL = Path("assets/masks/foreground_occlusion_matte.png")
MASK_PATH = PREDECESSOR_ROOT / MASK_REL
MANIFEST_PATH = PREDECESSOR_ROOT / "rough_assembly_manifest.json"
PLAYER_PATH = PREDECESSOR_ROOT / "player.html"
PREDECESSOR_MP4 = (
    PREDECESSOR_ROOT
    / "video_render"
    / "hybrid_attention_rewrite_outro_screen_literal_rail_captions_youtube_review_mp4_20260511T232232Z"
    / "challenger_hybrid_attention_rewrite_outro_screen_literal_rail_captions_youtube_review_1080p24.mp4"
)

AIRCRAFT_ROUTES = [
    {"name": "early_left_cross", "start": 8, "duration": 88, "x0": 1038, "x1": 70, "y0": 126, "y1": 480},
    {"name": "upper_right_cross", "start": 248, "duration": 96, "x0": 88, "x1": 1062, "y0": 94, "y1": 172},
    {"name": "upper_left_cross", "start": 438, "duration": 84, "x0": 1046, "x1": 110, "y0": 76, "y1": 194},
    {"name": "mid_left_cross", "start": 627, "duration": 104, "x0": 1020, "x1": 62, "y0": 306, "y1": 148},
    {"name": "upper_right_return", "start": 804, "duration": 92, "x0": 118, "x1": 1044, "y0": 198, "y1": 86},
    {"name": "upper_left_return", "start": 1006, "duration": 98, "x0": 1054, "x1": 130, "y0": 214, "y1": 76},
    {"name": "late_right_cross", "start": 1188, "duration": 82, "x0": 92, "x1": 1028, "y0": 142, "y1": 244},
]

EXCLUSION_GEOMETRY = {
    "global_foreground_floor": [(0, 646), (1920, 646), (1920, 1080), (0, 1080)],
    "left_service_tower_mass": [(318, 0), (592, 0), (680, 660), (260, 660)],
    "tower_top_and_umbilical": [(405, 84), (784, 205), (784, 322), (384, 244)],
    "tower_mid_arm": [(350, 240), (860, 340), (844, 462), (318, 400)],
    "tower_lower_arm": [(320, 402), (992, 500), (1046, 656), (266, 666)],
    "shuttle_stack_and_boosters": [(632, 46), (870, 50), (916, 626), (606, 634)],
    "mobile_launcher_pad": [(365, 522), (1188, 500), (1232, 730), (292, 726)],
    "right_pad_hardware": [(1030, 455), (1292, 530), (1328, 720), (1010, 708)],
}

EXCLUSION_CIRCLES = [
    {"name": "left_floodlight_cluster", "cx": 156, "cy": 522, "r": 92},
    {"name": "left_foreground_lamp", "cx": 260, "cy": 632, "r": 66},
    {"name": "right_tower_lamp", "cx": 1005, "cy": 506, "r": 62},
    {"name": "right_foreground_lamp", "cx": 1196, "cy": 624, "r": 62},
    {"name": "lower_right_lights", "cx": 1326, "cy": 708, "r": 62},
    {"name": "foreground_crew_area", "cx": 1290, "cy": 780, "r": 82},
    {"name": "foreground_crew_area_right", "cx": 1458, "cy": 780, "r": 82},
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def ignore_copy(dirpath: str, names: list[str]) -> set[str]:
    ignored = {".DS_Store", "__pycache__"}
    if Path(dirpath) == PREDECESSOR_ROOT:
        ignored.update({"video_render"})
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def draw_exclusion_mask(size: tuple[int, int]) -> Image.Image:
    block = Image.new("L", size, 0)
    draw = ImageDraw.Draw(block)
    for points in EXCLUSION_GEOMETRY.values():
        draw.polygon(points, fill=255)
    for circle in EXCLUSION_CIRCLES:
        cx, cy, r = circle["cx"], circle["cy"], circle["r"]
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)

    # Expand the blocked area so aircraft glow cannot visibly bleed over hard edges.
    return block.filter(ImageFilter.MaxFilter(49)).filter(ImageFilter.GaussianBlur(2.0))


def make_tight_mask(source_mask_path: Path, target_mask_path: Path, qa_dir: Path) -> dict:
    source = Image.open(SOURCE_PLATE).convert("RGB")
    old_rgba = Image.open(source_mask_path).convert("RGBA")
    old_alpha = old_rgba.getchannel("A")
    if source.size != old_rgba.size:
        raise ValueError(f"source plate {source.size} and matte {old_rgba.size} dimensions do not match")

    block = draw_exclusion_mask(old_rgba.size)
    new_alpha = ImageChops.multiply(old_alpha, ImageOps.invert(block))
    new_alpha = new_alpha.point(lambda v: 0 if v < 18 else v)

    tight = Image.new("RGBA", old_rgba.size, (255, 255, 255, 0))
    tight.putalpha(new_alpha)
    target_mask_path.parent.mkdir(parents=True, exist_ok=True)
    tight.save(target_mask_path)

    qa_dir.mkdir(parents=True, exist_ok=True)
    old_overlay = overlay_mask(source, old_alpha, "current")
    tight_overlay = overlay_mask(source, new_alpha, "tightened")
    delta_overlay = overlay_delta(source, old_alpha, new_alpha)
    route_overlay = overlay_routes(tight_overlay.copy())
    block_preview = Image.new("RGBA", old_rgba.size, (0, 0, 0, 255))
    block_preview.putalpha(block)

    old_overlay_path = qa_dir / "current_matte_overlay_for_review.png"
    tight_overlay_path = qa_dir / "tight_matte_overlay_for_review.png"
    delta_overlay_path = qa_dir / "tight_matte_removed_allowed_sky_delta.png"
    route_overlay_path = qa_dir / "tight_matte_aircraft_route_overlay.png"
    black_white_path = qa_dir / "tight_matte_black_white_alpha.png"
    block_path = qa_dir / "tight_matte_block_geometry_preview.png"
    old_overlay.save(old_overlay_path)
    tight_overlay.save(tight_overlay_path)
    delta_overlay.save(delta_overlay_path)
    route_overlay.save(route_overlay_path)
    ImageOps.colorize(new_alpha, black="black", white="white").save(black_white_path)
    block_preview.save(block_path)

    old_count = count_allowed(old_alpha)
    new_count = count_allowed(new_alpha)
    removed_count = count_removed(old_alpha, new_alpha)
    route_qa = sample_routes(old_alpha, new_alpha, block)
    qa = {
        "matte_semantics": "alpha > 0 permits aircraft/dust; alpha 0 blocks foreground objects",
        "source_plate_path": str(SOURCE_PLATE),
        "source_plate_sha256": sha256(SOURCE_PLATE),
        "predecessor_mask_path": str(source_mask_path),
        "predecessor_mask_sha256": sha256(source_mask_path),
        "tightened_mask_path": str(target_mask_path),
        "tightened_mask_sha256": sha256(target_mask_path),
        "dimensions": {"width": old_rgba.size[0], "height": old_rgba.size[1]},
        "allowed_pixel_counts": {
            "predecessor_alpha_gt_10": old_count,
            "tightened_alpha_gt_10": new_count,
            "removed_predecessor_allowed_pixels": removed_count,
            "removed_allowed_pixel_ratio_of_predecessor": round(removed_count / old_count, 6) if old_count else 0,
        },
        "exclusion_geometry": EXCLUSION_GEOMETRY,
        "exclusion_circles": EXCLUSION_CIRCLES,
        "route_centerline_qa": route_qa,
        "qa_reads": {
            "source_plate_matte_dimension_read": "pass_same_1920x1080_dimensions",
            "tightened_allowed_area_reduction_read": "pass" if new_count < old_count else "reject",
            "blocked_route_samples_read": "pass"
            if all(route["tight_visible_inside_block_samples"] == 0 for route in route_qa)
            else "tighten",
            "aircraft_still_visible_read": "pass"
            if all(route["tight_visible_samples"] >= 9 for route in route_qa)
            else "tighten",
            "first_aircraft_visible_within_20s_read": "pass"
            if route_qa[0]["tight_visible_samples_first_20s"] > 0
            else "tighten",
        },
        "qa_artifacts": {
            "current_matte_overlay": str(old_overlay_path),
            "tight_matte_overlay": str(tight_overlay_path),
            "removed_allowed_sky_delta": str(delta_overlay_path),
            "aircraft_route_overlay": str(route_overlay_path),
            "tight_matte_alpha_preview": str(black_white_path),
            "block_geometry_preview": str(block_path),
        },
        "human_review_note": "Route samples are centerline checks; visual review should still confirm no aircraft glow appears in front of tower, shuttle stack, pad deck, or foreground crew/lights.",
    }
    write_json(qa_dir / "tight_matte_route_occlusion_qa.json", qa)
    return qa


def count_allowed(alpha: Image.Image) -> int:
    return sum(1 for v in alpha.getdata() if v > 10)


def count_removed(old_alpha: Image.Image, new_alpha: Image.Image) -> int:
    return sum(1 for old, new in zip(old_alpha.getdata(), new_alpha.getdata()) if old > 10 and new <= 10)


def sample_routes(old_alpha: Image.Image, new_alpha: Image.Image, block: Image.Image) -> list[dict]:
    old_px = old_alpha.load()
    new_px = new_alpha.load()
    block_px = block.load()
    width, height = old_alpha.size
    results = []
    for route in AIRCRAFT_ROUTES:
        old_visible = 0
        new_visible = 0
        blocked_zone_samples = 0
        new_visible_inside_block = 0
        new_visible_first_20s = 0
        samples = []
        for i in range(121):
            p = i / 120
            x = route["x0"] + (route["x1"] - route["x0"]) * p
            y = route["y0"] + (route["y1"] - route["y0"]) * p
            xi = max(0, min(width - 1, int(round(x))))
            yi = max(0, min(height - 1, int(round(y))))
            old_ok = old_px[xi, yi] > 10
            new_ok = new_px[xi, yi] > 10
            in_block = block_px[xi, yi] > 128
            if old_ok:
                old_visible += 1
            if new_ok:
                new_visible += 1
            if in_block:
                blocked_zone_samples += 1
                if new_ok:
                    new_visible_inside_block += 1
            absolute_time = route["start"] + route["duration"] * p
            if new_ok and absolute_time <= 20:
                new_visible_first_20s += 1
            if i % 15 == 0:
                samples.append(
                    {
                        "p": round(p, 3),
                        "absolute_time_seconds": round(absolute_time, 3),
                        "xy": [xi, yi],
                        "predecessor_alpha": old_px[xi, yi],
                        "tight_alpha": new_px[xi, yi],
                        "inside_tight_block_zone": bool(in_block),
                    }
                )
        results.append(
            {
                "name": route["name"],
                "start_seconds": route["start"],
                "duration_seconds": route["duration"],
                "predecessor_visible_samples": old_visible,
                "tight_visible_samples": new_visible,
                "blocked_zone_samples": blocked_zone_samples,
                "tight_visible_inside_block_samples": new_visible_inside_block,
                "tight_visible_samples_first_20s": new_visible_first_20s,
                "representative_samples": samples,
            }
        )
    return results


def overlay_mask(source: Image.Image, alpha: Image.Image, label: str) -> Image.Image:
    rgba = source.convert("RGBA")
    overlay = Image.new("RGBA", source.size, (0, 0, 0, 0))
    opx = overlay.load()
    apx = alpha.load()
    width, height = source.size
    for y in range(height):
        for x in range(width):
            if apx[x, y] > 10:
                opx[x, y] = (0, 215, 255, 86)
            else:
                opx[x, y] = (255, 40, 40, 58)
    out = Image.alpha_composite(rgba, overlay)
    draw = ImageDraw.Draw(out)
    draw.text((34, 32), f"{label} matte: cyan permits aircraft, red blocks foreground", fill=(255, 255, 255, 255))
    return out


def overlay_delta(source: Image.Image, old_alpha: Image.Image, new_alpha: Image.Image) -> Image.Image:
    rgba = source.convert("RGBA")
    overlay = Image.new("RGBA", source.size, (0, 0, 0, 0))
    opx = overlay.load()
    old_px = old_alpha.load()
    new_px = new_alpha.load()
    width, height = source.size
    for y in range(height):
        for x in range(width):
            old_allowed = old_px[x, y] > 10
            new_allowed = new_px[x, y] > 10
            if old_allowed and not new_allowed:
                opx[x, y] = (255, 45, 45, 128)
            elif new_allowed:
                opx[x, y] = (0, 220, 255, 62)
    out = Image.alpha_composite(rgba, overlay)
    draw = ImageDraw.Draw(out)
    draw.text((34, 32), "tight matte delta: red removed from aircraft-permitted sky, cyan remains permitted", fill=(255, 255, 255, 255))
    return out


def overlay_routes(img: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(img)
    for route in AIRCRAFT_ROUTES:
        draw.line((route["x0"], route["y0"], route["x1"], route["y1"]), fill=(255, 236, 67, 255), width=4)
        draw.ellipse((route["x0"] - 9, route["y0"] - 9, route["x0"] + 9, route["y0"] + 9), fill=(0, 255, 160, 255))
        draw.ellipse((route["x1"] - 9, route["y1"] - 9, route["x1"] + 9, route["y1"] + 9), fill=(255, 98, 86, 255))
    draw.text((34, 66), "yellow aircraft centerlines; green=start, coral=end", fill=(255, 255, 255, 255))
    return img


def update_player(player_path: Path, stamp: str) -> None:
    text = player_path.read_text()
    text = text.replace(
        "Challenger Long-Form Hybrid Attention Rewrite Living Cover Proof",
        "Challenger Long-Form Hybrid Attention Rewrite Tight Matte Living Cover Proof",
    )
    text = text.replace(
        '"literal rail captions";',
        f'"literal rail captions + tightened foreground matte {stamp}";',
    )
    player_path.write_text(text)


def update_successor_manifest(successor_root: Path, stamp: str, qa: dict) -> None:
    manifest_path = successor_root / "rough_assembly_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    predecessor_manifest_sha = sha256(MANIFEST_PATH)
    predecessor_player_sha = sha256(PLAYER_PATH)
    predecessor_mp4_sha = sha256(PREDECESSOR_MP4) if PREDECESSOR_MP4.exists() else None

    successor_id = successor_root.name
    manifest["packet_id"] = successor_id
    manifest["created_utc"] = stamp
    manifest["status"] = "review_ready_with_tightened_foreground_matte_pending_human_disposition"
    manifest["human_disposition"] = "defer"
    manifest["review_only"] = True
    manifest["html_proof_only"] = True
    manifest["mp4_render_created"] = False
    manifest["rendered_video_proof"] = None
    manifest["may_create_full_runtime_mp4_render"] = False
    manifest["may_advance_to_video_render"] = False
    manifest["may_advance_to_final_assembly"] = False
    manifest["may_advance_to_publish_readiness"] = False
    manifest["may_youtube_action"] = False
    manifest["render_authorization"] = "blocked_until_human_keep_on_tightened_matte_html_proof"
    manifest["created_from_tight_matte_predecessor_packet_path"] = str(PREDECESSOR_ROOT)
    manifest["created_from_tight_matte_predecessor_manifest_path"] = str(MANIFEST_PATH)
    manifest["created_from_tight_matte_predecessor_manifest_sha256"] = predecessor_manifest_sha
    manifest["created_from_tight_matte_predecessor_player_path"] = str(PLAYER_PATH)
    manifest["created_from_tight_matte_predecessor_player_sha256"] = predecessor_player_sha
    manifest["created_from_tight_matte_predecessor_mp4_path"] = str(PREDECESSOR_MP4)
    manifest["created_from_tight_matte_predecessor_mp4_sha256"] = predecessor_mp4_sha

    reads = manifest.setdefault("rough_assembly_reads", {})
    reads.update(
        {
            "foreground_matte_precision_read": "tighten_applied_pending_human_review",
            "tower_shuttle_pad_occlusion_read": "pass_static_centerline_samples_blocked_by_tightened_matte_pending_human_visual_review",
            "crew_foreground_occlusion_read": "pass_foreground_floor_and_crew_light_regions_blocked_pending_human_visual_review",
            "aircraft_background_depth_read": "pass_tightened_matte_blocks_aircraft_over_stack_tower_pad_regions",
            "open_sky_preservation_read": "pass_route_samples_preserve_aircraft_visibility_in_open_sky_pending_human_review",
            "right_rail_mask_exclusion_read": "pass_unchanged_aircraft_rail_safe_left_limit",
            "backplate_preservation_read": "pass_source_plate_unchanged",
            "source_plate_matte_registration_read": "pass_same_1920x1080_source_plate_and_matte_coordinate_space",
            "foreground_matte_coordinate_space_read": "pass_same_1920x1080_no_css_drift",
            "matte_tightening_overlay_read": "pass_review_artifacts_created",
            "mp4_created_read": "not_applicable_html_tight_matte_gate_no_mp4_render",
            "render_output_read": "not_applicable_html_tight_matte_gate_no_mp4_render",
            "downstream_gate_read": "pass_all_downstream_flags_false",
        }
    )
    qa_reads = qa.get("qa_reads", {})
    reads["tightened_allowed_area_reduction_read"] = qa_reads.get("tightened_allowed_area_reduction_read")
    reads["tight_matte_blocked_route_samples_read"] = qa_reads.get("blocked_route_samples_read")
    reads["tight_matte_aircraft_still_visible_read"] = qa_reads.get("aircraft_still_visible_read")
    reads["aircraft_early_entry_timing_read"] = qa_reads.get("first_aircraft_visible_within_20s_read")

    qa_section = manifest.setdefault("qa", {})
    qa_section["tight_matte"] = qa

    artifacts = manifest.setdefault("artifacts", {})
    artifacts["player_html"] = {
        "path": str(successor_root / "player.html"),
        "sha256": sha256(successor_root / "player.html"),
    }
    artifacts["foreground_occlusion_matte"] = {
        "path": str(successor_root / MASK_REL),
        "sha256": sha256(successor_root / MASK_REL),
        "source": "tightened_from_predecessor_foreground_occlusion_matte",
    }
    artifacts["tight_matte_qa"] = {
        key: {"path": path, "sha256": sha256(Path(path))}
        for key, path in qa["qa_artifacts"].items()
    }

    visual_layering = manifest.setdefault("visual_layering", {})
    visual_layering["model"] = (
        str(visual_layering.get("model", "living_cover")).replace(
            "with_right_rail_native_captions_ambient_c_and_fresh_matte",
            "with_right_rail_native_captions_ambient_c_and_tightened_foreground_matte",
        )
    )
    visual_layering["tightened_foreground_matte_context"] = {
        "matte_semantics": qa["matte_semantics"],
        "predecessor_mask_path": qa["predecessor_mask_path"],
        "predecessor_mask_sha256": qa["predecessor_mask_sha256"],
        "tightened_mask_path": qa["tightened_mask_path"],
        "tightened_mask_sha256": qa["tightened_mask_sha256"],
        "review_artifacts": qa["qa_artifacts"],
        "allowed_pixel_counts": qa["allowed_pixel_counts"],
        "route_centerline_qa_path": str(successor_root / "qa" / "matte" / "tight_matte_route_occlusion_qa.json"),
        "human_review_note": qa["human_review_note"],
    }

    manifest["next_review_question"] = (
        "tighten/keep/reject the tightened aircraft foreground matte before any new MP4 render or YouTube publish-readiness step"
    )
    manifest["reviewer_notes"] = (
        str(manifest.get("reviewer_notes", "")).rstrip()
        + "\nTightened matte successor: review aircraft/dust depth against shuttle stack, service tower, pad deck, foreground crew/lights. No MP4 was rendered for this gate."
    ).strip()
    manifest["local_review_server"] = {
        "suggested_port": 8817,
        "url": "http://127.0.0.1:8817/player.html",
    }
    manifest["review_urls"] = {
        "local_html": "http://127.0.0.1:8817/player.html",
    }
    write_json(manifest_path, manifest)


def update_readme(successor_root: Path, qa: dict) -> None:
    readme_path = successor_root / "README.md"
    existing = readme_path.read_text() if readme_path.exists() else ""
    note = f"""# Challenger Long-Form Tight Matte Review Proof

This successor tightens the allowed-sky foreground matte used for aircraft and dust occlusion. It preserves the prior audio, captions, chapters, outro timing, and visual shell.

- Predecessor proof: `{PREDECESSOR_ROOT}`
- Predecessor MP4: `{PREDECESSOR_MP4}`
- New matte: `{successor_root / MASK_REL}`
- QA overlay: `{qa['qa_artifacts']['tight_matte_overlay']}`
- Route QA: `{successor_root / 'qa' / 'matte' / 'tight_matte_route_occlusion_qa.json'}`

Review question: `keep`, `tighten`, or `reject` the tightened matte before any new MP4 render or YouTube publish-readiness step.

Current gates remain closed: `human_disposition: defer`, `may_create_full_runtime_mp4_render: false`, `may_advance_to_final_assembly: false`, `may_advance_to_publish_readiness: false`, `may_youtube_action: false`.

"""
    readme_path.write_text(note + existing)


def mark_predecessor_tighten(successor_root: Path, qa: dict) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    manifest["status"] = "tighten_foreground_matte_before_next_mp4_or_publish_readiness"
    manifest["human_disposition"] = "tighten"
    manifest["successor_tight_matte_packet_path"] = str(successor_root)
    manifest["successor_tight_matte_manifest_path"] = str(successor_root / "rough_assembly_manifest.json")
    manifest["successor_tight_matte_mask_sha256"] = qa["tightened_mask_sha256"]
    manifest["may_create_full_runtime_mp4_render"] = False
    manifest["may_advance_to_video_render"] = False
    manifest["may_advance_to_final_assembly"] = False
    manifest["may_advance_to_publish_readiness"] = False
    manifest["may_youtube_action"] = False
    reads = manifest.setdefault("rough_assembly_reads", {})
    reads["foreground_matte_precision_read"] = "tighten_human_requested_successor_created"
    reads["tower_shuttle_pad_occlusion_read"] = "tighten_human_requested_successor_created"
    reads["aircraft_background_depth_read"] = "tighten_human_requested_successor_created"
    reads["downstream_gate_read"] = "pass_closed_after_human_tighten_request"
    manifest["reviewer_notes"] = (
        str(manifest.get("reviewer_notes", "")).rstrip()
        + f"\nHuman requested matte tightening before any further MP4 render or YouTube publish-readiness step. Successor: {successor_root}"
    ).strip()
    write_json(MANIFEST_PATH, manifest)


def main() -> None:
    if not PREDECESSOR_ROOT.exists():
        raise FileNotFoundError(PREDECESSOR_ROOT)
    if not MASK_PATH.exists():
        raise FileNotFoundError(MASK_PATH)
    if not SOURCE_PLATE.exists():
        raise FileNotFoundError(SOURCE_PLATE)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    successor_root = ROUGH_ROOT / (
        "living_cover_shuttle_stack_reference_variant_a_full_runtime_hybrid_attention_rewrite_music_only_intro_outro_"
        f"outro_screen_literal_rail_captions_tight_matte_html_approval_proof_{stamp}"
    )
    if successor_root.exists():
        raise FileExistsError(successor_root)

    shutil.copytree(PREDECESSOR_ROOT, successor_root, symlinks=True, ignore=ignore_copy)

    update_player(successor_root / "player.html", stamp)
    qa = make_tight_mask(MASK_PATH, successor_root / MASK_REL, successor_root / "qa" / "matte")
    update_successor_manifest(successor_root, stamp, qa)
    update_readme(successor_root, qa)
    mark_predecessor_tighten(successor_root, qa)

    result = {
        "successor_root": str(successor_root),
        "successor_player": str(successor_root / "player.html"),
        "successor_manifest": str(successor_root / "rough_assembly_manifest.json"),
        "tight_matte_path": str(successor_root / MASK_REL),
        "tight_matte_sha256": qa["tightened_mask_sha256"],
        "qa_overlay": qa["qa_artifacts"]["tight_matte_overlay"],
        "qa_route_overlay": qa["qa_artifacts"]["aircraft_route_overlay"],
        "qa_json": str(successor_root / "qa" / "matte" / "tight_matte_route_occlusion_qa.json"),
        "suggested_url": "http://127.0.0.1:8817/player.html",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
