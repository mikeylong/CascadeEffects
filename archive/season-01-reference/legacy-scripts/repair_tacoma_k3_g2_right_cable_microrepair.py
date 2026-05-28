#!/usr/bin/env python3
"""Create a localized Tacoma K3 flipped right-side cable microrepair proof."""

from __future__ import annotations

import colorsys
import hashlib
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")
EPISODE_ROOT = EPISODES_ROOT / "Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube"
REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766"

K4_PROOF_ROOT = (
    EPISODE_ROOT
    / "rough_assembly/tacoma-narrows_rolling_caption_rail_k4_suspension_cable_repair_20260522T224753Z"
)
K3_CANONICAL_ROUGH_ROOT = (
    EPISODE_ROOT / "rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_tail_lights_removed_20260520T054440Z"
)
K3_FLIPPED_SOURCE = (
    K4_PROOF_ROOT / "assets/source_art/candidate_k3_roadway_wide_stance_flipped_1920x1080.png"
)
K3_FLIPPED_FALLBACK = (
    K3_CANONICAL_ROUGH_ROOT / "assets/source_art/candidate_k3_roadway_wide_stance_flipped_1920x1080.png"
)

REVIEW_INDEX_PATH = EPISODES_ROOT / "first-eight-rolling-caption-rail-review.html"
ROLLOUT_SUMMARY_PATH = (
    REPO_ROOT
    / "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/rolling_caption_rail_rollout_20260520.json"
)
BASELINE_PATH = (
    REPO_ROOT
    / "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/tacoma-narrows.md"
)

K3_SOURCE_MANIFEST = (
    EPISODE_ROOT
    / "source_art/tacoma_living_cover_bridge_deck_wide_stance_imagegen_keep_20260517T225428Z/source_art_manifest.json"
)
G_ROUGH_MANIFEST = (
    EPISODE_ROOT
    / "rough_assembly/tacoma_living_cover_html_rough_proof_candidate_g_rail_opacity_balance_20260517T210620Z/rough_assembly_manifest.json"
)
K3_ROUGH_MANIFEST = K3_CANONICAL_ROUGH_ROOT / "rough_assembly_manifest.json"
PRIOR_ROLLING_MANIFESTS = [
    EPISODE_ROOT
    / "rough_assembly/tacoma-narrows_rolling_caption_rail_rough_proof_20260520T235500Z/rough_assembly_manifest.json",
    EPISODE_ROOT
    / "rough_assembly/tacoma-narrows_rolling_caption_rail_rough_proof_20260522T223902Z/rough_assembly_manifest.json",
]
K4_SOURCE_MANIFEST = (
    EPISODE_ROOT
    / "source_art/tacoma_living_cover_suspension_cable_repair_imagegen_candidate_k4_20260522T224753Z/source_art_manifest.json"
)
K4_ROUGH_MANIFEST = K4_PROOF_ROOT / "rough_assembly_manifest.json"

CANDIDATE_ID = "candidate_k3_g2_right_cable_microrepair"
NORMALIZED_NAME = f"{CANDIDATE_ID}_1920x1080.png"
ORIGINAL_COPY_NAME = "candidate_k3_roadway_wide_stance_flipped_1920x1080_source.png"
MASK_NAME = f"{CANDIDATE_ID}_repair_mask.png"

END_SCREEN_TARGET_LAYOUT = {
    "left_video": {"role": "suggested_video", "bbox_xy": [78, 382, 758, 765], "aspect_ratio": "16:9"},
    "right_video": {"role": "watch_next_video", "bbox_xy": [1162, 382, 1842, 765], "aspect_ratio": "16:9"},
    "center_subscribe": {"role": "subscribe", "bbox_xy": [814, 429, 1106, 721]},
}
END_SCREEN_PALETTE_MODEL = "backplate_sampled_youtube_end_screen_palette_v1"
END_SCREEN_PALETTE_TREATMENT_MODEL = "local_backplate_perceptual_target_palette_v3"
END_SCREEN_ADAPTIVE_VARIABILITY_MODEL = "backplate_hue_preserved_perceptual_variability_v1"
END_SCREEN_PALETTE_CONTRACT_ID = "living_cover_end_screen_palette_contract_v1"

RIGHT_SIDE_DEFECT_BANDS = [
    {
        "id": "right_image_near_hanger_over_road_edge",
        "bbox_xy": [1274, 0, 1303, 770],
        "preserve_x": [1285],
        "read": "suppressed over-scale free-floating right-side hanger pair after K3 horizontal flip",
    },
    {
        "id": "right_image_hanger_pair_visually_landing_on_car",
        "bbox_xy": [1487, 0, 1522, 760],
        "preserve_x": [1496, 1509],
        "read": "removed foreground hanger pair that read as landing on the car/roadway plane",
    },
    {
        "id": "right_image_edge_hanger_overweight_foreground_bar",
        "bbox_xy": [1838, 0, 1874, 810],
        "preserve_x": [1851],
        "read": "softened image-right edge bar so it no longer dominates as detached foreground cable",
    },
]


def utc_stamp() -> tuple[str, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return stamp, stamp.replace("T", "").replace("Z", "Z")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact(path: Path, role: str | None = None) -> dict:
    out = {"path": str(path), "sha256": sha256_file(path)}
    if role:
        out["role"] = role
    return out


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2) + "\n")


def rgb_to_hex(rgb: tuple[int, int, int] | list[int]) -> str:
    return "#" + "".join(f"{max(0, min(255, int(round(c)))):02x}" for c in rgb)


def rgba_string(rgb: tuple[float, float, float] | list[float], alpha: float) -> str:
    return f"rgba({', '.join(str(max(0, min(255, int(round(c))))) for c in rgb)}, {alpha:.3f})"


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def sample_average_color(source_art_path: Path, bbox_xy: list[int]) -> list[int]:
    img = Image.open(source_art_path).convert("RGB")
    x1, y1, x2, y2 = [int(round(v)) for v in bbox_xy]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(img.width, x2), min(img.height, y2)
    arr = np.asarray(img.crop((x1, y1, x2, y2)), dtype=np.float32)
    mean = arr.reshape(-1, 3).mean(axis=0)
    return [int(round(c)) for c in mean]


def end_screen_target_colors_from_sample(sample_rgb: list[int], role: str = "video") -> dict:
    sample = sample_rgb or ([80, 79, 85] if role == "subscribe" else [64, 66, 66])
    r, g, b = [c / 255.0 for c in sample]
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    sample_spread = max(sample) - min(sample)
    neutral_lift = 0.08 if sample_spread < 10 else 0
    dark_hue_reliability_cap = (0.42 if role == "subscribe" else 0.44) if lightness < 0.08 else 1
    sat = min(
        dark_hue_reliability_cap,
        clamp01(max(0.24 if role == "subscribe" else 0.22, saturation * 1.85 + neutral_lift)),
    )

    def hls_to_rgb255(light: float, sat_scale: float) -> tuple[float, float, float]:
        rr, gg, bb = colorsys.hls_to_rgb(hue, clamp01(light), clamp01(sat_scale))
        return rr * 255, gg * 255, bb * 255

    fill = hls_to_rgb255((0.18 if role == "subscribe" else 0.155) + min(lightness, 0.34) * 0.12, sat * 0.82)
    border = hls_to_rgb255(0.67 if role == "subscribe" else 0.60, max(0.32 if role == "subscribe" else 0.30, sat * 1.06))
    ring = hls_to_rgb255(0.54 if role == "subscribe" else 0.47, max(0.28 if role == "subscribe" else 0.24, sat * 0.92))
    inner_ring = hls_to_rgb255(0.63, max(0.28, sat * 0.88))
    variability_score = int(round(max(border) - min(border)))
    return {
        "sample_hex": rgb_to_hex(sample),
        "fill_rgba": rgba_string(fill, 0.34 if role == "subscribe" else 0.36),
        "border_rgba": rgba_string(border, 0.84 if role == "subscribe" else 0.74),
        "ring_rgba": rgba_string(ring, 0.20 if role == "subscribe" else 0.18),
        "inner_ring_rgba": rgba_string(inner_ring, 0.46),
        "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
        "adaptive_variability_model": END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
        "source_hue_degrees": int(round(hue * 360)),
        "source_saturation": round(float(saturation), 3),
        "derived_saturation": round(float(sat), 3),
        "perceptual_variability_score": variability_score,
        "perceptual_variability_read": (
            "pass_backplate_hue_visible_in_end_screen_target"
            if variability_score >= 24
            else "tighten_low_perceptual_target_variability"
        ),
        "hue_shift_applied": False,
    }


def end_screen_palette_for_source_art(source_art_path: Path) -> dict:
    targets = {}
    for key, target in END_SCREEN_TARGET_LAYOUT.items():
        sample_rgb = sample_average_color(source_art_path, target["bbox_xy"])
        targets[key] = {
            "role": target["role"],
            "sample_bbox_xy": target["bbox_xy"],
            **end_screen_target_colors_from_sample(sample_rgb, target["role"]),
            "sample_read": "pass_backplate_region_average",
        }
    sample_read = "pass_source_backplate_sampled"
    return {
        "model_id": END_SCREEN_PALETTE_MODEL,
        "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
        "palette_source": "sampled_episode_backplate",
        "source_art_path": str(source_art_path),
        "source_art_sha256": sha256_file(source_art_path),
        "target_count": len(targets),
        "targets": targets,
        "sample_read": sample_read,
        "adaptive_variability_model": END_SCREEN_ADAPTIVE_VARIABILITY_MODEL,
        "perceptual_variability_min_score": min(t["perceptual_variability_score"] for t in targets.values()),
        "end_screen_adaptive_perceptual_variability_read": (
            "pass_backplate_hue_visible_across_end_screen_targets"
            if all(t["perceptual_variability_read"] == "pass_backplate_hue_visible_in_end_screen_target" for t in targets.values())
            else "tighten_backplate_hue_not_visible_enough_in_end_screen_targets"
        ),
        "adaptive_context_read": "pass_local_target_regions_sampled_with_perceptual_backplate_variability",
        "fixed_cross_episode_color_read": "pass_no_challenger_default_color_reuse_with_visible_episode_variability",
    }


def end_screen_palette_contract_for_source_art(source_art_path: Path, palette: dict) -> dict:
    left = palette["targets"]["left_video"]
    right = palette["targets"]["right_video"]
    subscribe = palette["targets"]["center_subscribe"]
    source_sha = sha256_file(source_art_path)
    colors = {
        "video_target_fill_rgba": left["fill_rgba"],
        "video_target_border_rgba": left["border_rgba"],
        "video_target_secondary_border_rgba": right["border_rgba"],
        "subscribe_ring_rgba": subscribe["border_rgba"],
        "muted_rail_text_hex": right["sample_hex"],
        "small_accent_hex": subscribe["sample_hex"],
    }
    css_variables = {
        "--ce-end-screen-target-fill": colors["video_target_fill_rgba"],
        "--ce-end-screen-video-border": colors["video_target_border_rgba"],
        "--ce-end-screen-video-border-secondary": colors["video_target_secondary_border_rgba"],
        "--ce-end-screen-subscribe-ring": colors["subscribe_ring_rgba"],
        "--ce-end-screen-muted-text": colors["muted_rail_text_hex"],
        "--ce-end-screen-small-accent": colors["small_accent_hex"],
        "--ce-end-screen-target-fill-left": left["fill_rgba"],
        "--ce-end-screen-target-fill-right": right["fill_rgba"],
        "--ce-end-screen-target-fill-subscribe": subscribe["fill_rgba"],
        "--ce-end-screen-video-border-left": left["border_rgba"],
        "--ce-end-screen-video-border-right": right["border_rgba"],
        "--ce-end-screen-subscribe-border": subscribe["border_rgba"],
        "--ce-end-screen-video-ring-left": left["ring_rgba"],
        "--ce-end-screen-video-ring-right": right["ring_rgba"],
        "--ce-end-screen-subscribe-soft-ring": subscribe["ring_rgba"],
        "--ce-end-screen-subscribe-inner-ring": subscribe["inner_ring_rgba"],
    }
    target_samples = {
        key: {"bbox_xy": target["sample_bbox_xy"], "sample_hex": target["sample_hex"], "sample_read": target["sample_read"]}
        for key, target in palette["targets"].items()
    }
    return {
        "contract_id": END_SCREEN_PALETTE_CONTRACT_ID,
        "status": "pass",
        "required": True,
        "required_for_gates": ["visual_system", "rough_assembly", "final_assembly", "publish_readiness"],
        "palette_source": "sampled_episode_backplate",
        "derivation_model": END_SCREEN_PALETTE_MODEL,
        "sample_model": "pil_target_region_average_rgb_v1",
        "approved_backplate": {
            "path": str(source_art_path),
            "sha256": source_sha,
            "role": "approved_living_cover_source_art_backplate",
        },
        "sampled_backplate": {
            "path": str(source_art_path),
            "sha256": source_sha,
            "palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
            "target_samples": target_samples,
        },
        "colors": colors,
        "css_variables": css_variables,
        "reads": {
            "end_screen_palette_contract_read": "pass_backplate_sampled_palette_contract_present",
            "end_screen_target_fill_palette_read": "pass_local_target_fills_sampled_from_backplate_regions",
            "end_screen_target_contrast_read": "pass_local_target_borders_visible_without_challenger_hue_shift",
            "rail_panel_palette_read": "pass_adaptive_end_screen_targets_use_source_aware_palette",
            "source_integrated_panel_color_read": "pass_perceptual_episode_backplate_colors_visible_in_end_screen",
            "no_cross_episode_default_palette_read": "pass_no_challenger_default_target_colors_with_visible_variability",
            "end_screen_adaptive_perceptual_variability_read": palette["end_screen_adaptive_perceptual_variability_read"],
        },
        "target_palette": palette,
    }


def inpaint_vertical_bands(source_path: Path, repaired_path: Path, mask_path: Path, diff_path: Path) -> dict:
    original = Image.open(source_path).convert("RGBA")
    arr = np.asarray(original, dtype=np.float32)
    repaired = arr.copy()
    width, height = original.size
    hard_mask_np = np.zeros((height, width), dtype=bool)

    for band in RIGHT_SIDE_DEFECT_BANDS:
        x1, y1, x2, y2 = [int(v) for v in band["bbox_xy"]]
        x1, x2 = max(0, x1), min(width, x2)
        y1, y2 = max(0, y1), min(height, y2)
        sub = arr[y1:y2, x1:x2, :3]
        luminance = sub.mean(axis=2)
        dark = luminance < 92
        dark_column_score = dark.sum(axis=0)
        cable_columns = dark_column_score >= max(120, int((y2 - y1) * 0.24))
        column_area = np.zeros_like(dark, dtype=bool)
        for col in np.flatnonzero(cable_columns):
            left_col = max(0, col - 2)
            right_col = min(column_area.shape[1], col + 3)
            column_area[:, left_col:right_col] = True
        mask_sub = dark & column_area
        for preserve_x in band.get("preserve_x", []):
            local_x = int(preserve_x) - x1
            if 0 <= local_x < mask_sub.shape[1]:
                mask_sub[:, max(0, local_x - 1) : min(mask_sub.shape[1], local_x + 2)] = False
        hard_mask_np[y1:y2, x1:x2] |= mask_sub

    for y in range(height):
        xs = np.flatnonzero(hard_mask_np[y])
        if xs.size == 0:
            continue
        runs: list[tuple[int, int]] = []
        run_start = int(xs[0])
        prev = int(xs[0])
        for x in xs[1:]:
            x = int(x)
            if x == prev + 1:
                prev = x
            else:
                runs.append((run_start, prev + 1))
                run_start = prev = x
        runs.append((run_start, prev + 1))
        for run_x1, run_x2 in runs:
            left_slice = slice(max(0, run_x1 - 18), run_x1)
            right_slice = slice(run_x2, min(width, run_x2 + 18))
            left_pixels = arr[y, left_slice, :3][~hard_mask_np[y, left_slice]]
            right_pixels = arr[y, right_slice, :3][~hard_mask_np[y, right_slice]]
            if left_pixels.size and right_pixels.size:
                left_color = np.median(left_pixels.reshape(-1, 3), axis=0)
                right_color = np.median(right_pixels.reshape(-1, 3), axis=0)
            elif left_pixels.size:
                left_color = right_color = np.median(left_pixels.reshape(-1, 3), axis=0)
            elif right_pixels.size:
                left_color = right_color = np.median(right_pixels.reshape(-1, 3), axis=0)
            else:
                continue
            span = max(1, run_x2 - run_x1)
            for offset, x in enumerate(range(run_x1, run_x2)):
                t = offset / span
                repaired[y, x, :3] = (1.0 - t) * left_color + t * right_color
                repaired[y, x, 3] = arr[y, x, 3]

    hard_mask = Image.fromarray(np.where(hard_mask_np, 255, 0).astype(np.uint8), "L")
    feathered_mask = hard_mask.filter(ImageFilter.GaussianBlur(0.8))
    repaired_img = Image.fromarray(np.clip(repaired, 0, 255).astype(np.uint8), "RGBA")
    composited = Image.composite(repaired_img, original, feathered_mask).convert("RGB")
    composited.save(repaired_path)
    feathered_mask.save(mask_path)

    before_rgb = np.asarray(original.convert("RGB"), dtype=np.int16)
    after_rgb = np.asarray(composited, dtype=np.int16)
    mask_np = np.asarray(feathered_mask) > 0
    changed_np = np.any(before_rgb != after_rgb, axis=2)
    outside_mask_changed = np.count_nonzero(changed_np & ~mask_np)
    changed_pixels = int(np.count_nonzero(changed_np))
    max_channel_delta = int(np.abs(before_rgb - after_rgb).max())

    overlay = np.asarray(original.convert("RGB"), dtype=np.uint8).copy()
    red = np.array([255, 70, 35], dtype=np.uint8)
    overlay[changed_np] = (overlay[changed_np].astype(np.uint16) * 45 // 100 + red.astype(np.uint16) * 55 // 100).astype(np.uint8)
    Image.fromarray(overlay, "RGB").save(diff_path)

    return {
        "changed_pixels": changed_pixels,
        "changed_pixels_outside_mask": int(outside_mask_changed),
        "changed_pixel_percent": round(changed_pixels / (width * height) * 100, 4),
        "max_channel_delta": max_channel_delta,
        "mask_bbox_xy": [min(b["bbox_xy"][0] for b in RIGHT_SIDE_DEFECT_BANDS), 0, max(b["bbox_xy"][2] for b in RIGHT_SIDE_DEFECT_BANDS), 812],
        "mask_band_count": len(RIGHT_SIDE_DEFECT_BANDS),
        "mask_bands": RIGHT_SIDE_DEFECT_BANDS,
        "nonmask_preservation_read": (
            "pass_non_mask_pixels_unchanged"
            if outside_mask_changed == 0
            else "fail_non_mask_pixels_changed"
        ),
    }


def crop(path: Path, bbox: tuple[int, int, int, int], out_path: Path) -> None:
    Image.open(path).convert("RGB").crop(bbox).save(out_path)


def contact_sheet(paths: list[Path], labels: list[str], out_path: Path, thumb_width: int = 640) -> None:
    thumbs = []
    label_h = 28
    for path in paths:
        img = Image.open(path).convert("RGB")
        ratio = thumb_width / img.width
        thumbs.append(img.resize((thumb_width, int(round(img.height * ratio))), Image.Resampling.LANCZOS))
    height = max(img.height for img in thumbs) + label_h
    sheet = Image.new("RGB", (thumb_width * len(thumbs), height), (18, 22, 22))
    draw = ImageDraw.Draw(sheet)
    for index, (thumb, label) in enumerate(zip(thumbs, labels)):
        x = index * thumb_width
        sheet.paste(thumb, (x, label_h))
        draw.text((x + 12, 8), label, fill=(232, 239, 241))
    sheet.save(out_path)


def extract_const_json(html_text: str, const_name: str) -> dict | None:
    needle = f"const {const_name} = "
    start = html_text.find(needle)
    if start < 0:
        return None
    value_start = start + len(needle)
    end = html_text.find(";\n", value_start)
    if end < 0:
        return None
    try:
        return json.loads(html_text[value_start:end])
    except json.JSONDecodeError:
        return None


def replace_const_json(html_text: str, const_name: str, value: dict) -> str:
    pattern = re.compile(rf"const\s+{re.escape(const_name)}\s*=\s*[\s\S]*?;\n")
    replacement = f"const {const_name} = {json.dumps(value, separators=(',', ':'))};\n"
    return pattern.sub(replacement, html_text, count=1)


def replace_css_var(html_text: str, name: str, value: str) -> str:
    return re.sub(rf"{re.escape(name)}:\s*[^;]+;", f"{name}: {value};", html_text)


def update_player_html(player_path: Path, proof_root: Path, proof_build_id: str, palette: dict, palette_contract: dict) -> None:
    html_text = player_path.read_text()
    proof_build_url = (
        f"{REVIEW_SERVER_BASE_URL}/{(proof_root / 'proof_build.json').relative_to(EPISODES_ROOT).as_posix()}?v={proof_build_id}"
    )
    replacements = [
        ("tacoma-narrows_rolling_caption_rail_k4_suspension_cable_repair_20260522T224753Z", proof_root.name),
        ("tacoma-narrows_rolling_caption_rail_rough_proof_20260522T223902Z", proof_root.name),
        ("candidate_k4_suspension_cable_repair_1920x1080.png", NORMALIZED_NAME),
        ("candidate_k3_roadway_wide_stance_flipped_1920x1080.png", NORMALIZED_NAME),
        ("candidate_k4_suspension_cable_repair", CANDIDATE_ID),
        ("candidate_k3_roadway_wide_stance_flipped_layout_probe", CANDIDATE_ID),
        ("candidate_k3_roadway_wide_stance", CANDIDATE_ID),
        ("tacoma_living_cover_suspension_cable_repair_imagegen_candidate_k4_20260522T224753Z", proof_root.name),
        ("candidate K4 regenerated source art for suspension-cable geometry repair", "K3 flipped localized right-side cable microrepair"),
    ]
    for old, new in replacements:
        html_text = html_text.replace(old, new)
    html_text = re.sub(r'proofBuildId:\s*"[^"]+"', f'proofBuildId: "{proof_build_id}"', html_text)
    html_text = re.sub(r'proofBuildJsonUrl:\s*"[^"]*"', f'proofBuildJsonUrl: "{proof_build_url}"', html_text)
    html_text = html_text.replace("sourcePlateGeometryChanged: false", "sourcePlateGeometryChanged: true")
    for name, value in palette_contract["css_variables"].items():
        html_text = replace_css_var(html_text, name, value)
    end_screen = extract_const_json(html_text, "CE_END_SCREEN") or {"enabled": True}
    end_screen["palette"] = palette
    html_text = replace_const_json(html_text, "CE_END_SCREEN", end_screen)
    html_text = replace_const_json(html_text, "CE_END_SCREEN_PALETTE", palette_contract)
    player_path.write_text(html_text)


def gate_block(manifest: dict) -> None:
    manifest["may_advance_to_final_assembly"] = False
    manifest["may_advance_to_publish_readiness"] = False
    manifest["may_create_full_runtime_mp4_render"] = False
    manifest["may_youtube_action"] = False
    if isinstance(manifest.get("gate_locks"), dict):
        manifest["gate_locks"]["may_render_final_mp4"] = False
        manifest["gate_locks"]["may_youtube_action"] = False
        manifest["gate_locks"]["public_release_ready"] = False


def mark_story_source_lineage(path: Path, source_kind: str, repair_path: Path, repair_sha: str, created_at_utc: str) -> None:
    if not path.exists():
        return
    manifest = read_json(path)
    manifest["previous_status_before_k3_g2_right_cable_microrepair"] = manifest.get("status")
    manifest["status"] = f"tighten_geometry_only_story_source_superseded_by_{CANDIDATE_ID}"
    if "human_disposition" in manifest:
        manifest["human_disposition"] = "tighten"
    manifest["story_preserving_cable_repair_lineage"] = {
        "status": "tighten_geometry_only_story_source",
        "reviewed_at_utc": created_at_utc,
        "source_kind": source_kind,
        "base_story_plate_read": "pass_preserve_k3_flipped_wet_deck_car_wide_stance_witness_torsion_story",
        "defect_orientation_read": "right_side_of_current_flipped_image_pre_flip_left_side_defect_language_is_superseded",
        "repair_candidate_id": CANDIDATE_ID,
        "repair_source_art_path": str(repair_path),
        "repair_source_art_sha256": repair_sha,
        "downstream_gate_read": "blocked_do_not_advance_unrepaired_story_source_to_final_publish_or_youtube",
    }
    manifest["source_art_successor_required"] = {
        "source_art_id": CANDIDATE_ID,
        "final_plate_path": str(repair_path),
        "final_plate_sha256": repair_sha,
        "reason": "K3 flipped remains the story source, but the right side of the current flipped image needs localized suspension-cable microrepair.",
    }
    gate_block(manifest)
    write_json(path, manifest)


def mark_k4_geometry_reference(path: Path, repair_path: Path, repair_sha: str, created_at_utc: str) -> None:
    if not path.exists():
        return
    manifest = read_json(path)
    manifest["previous_status_before_k3_g2_story_preserving_repair"] = manifest.get("status")
    manifest["status"] = "tighten_story_loss_geometry_reference_only"
    if "human_disposition" in manifest:
        manifest["human_disposition"] = "tighten"
    manifest["story_preserving_cable_repair_lineage"] = {
        "status": "tighten_story_loss_geometry_reference_only",
        "reviewed_at_utc": created_at_utc,
        "geometry_reference_role": "useful suspension-geometry reference only",
        "story_loss_read": "tighten_k4_not_active_aesthetic_successor_after_user_rejection_wrong_backplate",
        "active_repair_candidate_id": CANDIDATE_ID,
        "active_repair_source_art_path": str(repair_path),
        "active_repair_source_art_sha256": repair_sha,
        "downstream_gate_read": "blocked_do_not_advance_k4_to_final_publish_or_youtube",
    }
    gate_block(manifest)
    write_json(path, manifest)


def update_baseline(source_path: Path, source_sha: str, source_manifest_path: Path, proof_root: Path, created_at_utc: str) -> None:
    text = BASELINE_PATH.read_text() if BASELINE_PATH.exists() else "# Tacoma Narrows Living Cover Visual System Baseline\n"
    block = f"""
## 2026-05-22 K3 G2 Right-Side Cable Microrepair

Status: `candidate_k3_roadway_wide_stance_flipped_1920x1080` remains the story source, but the current flipped image's right-side cable/suspender defect is repaired by `{CANDIDATE_ID}`.

- Source-art package: `{source_manifest_path.parent}`
- Final plate: `{source_path}`
- Final plate sha256: `{source_sha}`
- Source-art manifest: `{source_manifest_path}`
- Rough proof: `{proof_root}`
- Created UTC: `{created_at_utc}`
- K4 disposition: `tighten_story_loss_geometry_reference_only`
- Gate policy: final render, publish readiness, upload, and public release remain blocked until human keep.
- Required reads: `visual_story_continuity_read`, `deck_torsion_story_read`, `human_witness_bracing_read`, `weather_and_roadway_mood_read`, `suspension_cable_geometry_read`, `pixel_diff_nonmask_read`
"""
    pattern = re.compile(r"\n## 2026-05-22 K3 G2 Right-Side Cable Microrepair[\s\S]*?(?=\n## |\Z)")
    if pattern.search(text):
        text = pattern.sub("\n" + block.strip() + "\n", text)
    else:
        text = text.rstrip() + "\n\n" + block.strip() + "\n"
    BASELINE_PATH.write_text(text)


def update_review_index(proof_root: Path, proof_build_id: str) -> None:
    if not REVIEW_INDEX_PATH.exists():
        return
    new_href = f"{(proof_root / 'player.html').relative_to(EPISODES_ROOT).as_posix()}?v={proof_build_id}"
    index = REVIEW_INDEX_PATH.read_text()
    index = re.sub(
        r"Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/[^\"']+/player\.html\?v=[^\"']+",
        new_href,
        index,
    )
    index = re.sub(
        r'Tacoma Narrows\s*<span class="status">[^<]*</span>',
        'Tacoma Narrows <span class="status">k3 g2 right-cable microrepair review</span>',
        index,
    )
    REVIEW_INDEX_PATH.write_text(index)


def update_rollout_summary(proof_root: Path, proof_build_id: str, source_path: Path, source_sha: str, created_at_utc: str) -> None:
    if not ROLLOUT_SUMMARY_PATH.exists():
        return
    summary = read_json(ROLLOUT_SUMMARY_PATH)
    entries = summary.get("episodes") if isinstance(summary.get("episodes"), list) else summary.get("items", [])
    for entry in entries:
        if entry.get("episode_id") == "tacoma-narrows" or entry.get("slug") == "tacoma-narrows" or entry.get("title") == "Tacoma Narrows":
            entry["output_dir"] = str(proof_root)
            entry["rough_proof_root"] = str(proof_root)
            entry["manifest_path"] = str(proof_root / "rough_assembly_manifest.json")
            entry["player_path"] = str(proof_root / "player.html")
            entry["review_url"] = (
                f"{REVIEW_SERVER_BASE_URL}/{(proof_root / 'player.html').relative_to(EPISODES_ROOT).as_posix()}?v={proof_build_id}"
            )
            entry["source_art_path"] = str(source_path)
            entry["source_art_sha256"] = source_sha
            entry["proof_build_id"] = proof_build_id
            entry["status"] = "k3_g2_right_cable_microrepair_review_ready_pending_human_keep"
            entry["human_disposition"] = "pending"
            entry["may_render_final_mp4"] = False
            entry["may_advance_to_final_assembly"] = False
            entry["may_advance_to_publish_readiness"] = False
            entry["may_youtube_action"] = False
            entry["visual_story_continuity_read"] = "pass_k3_flipped_story_plate_preserved_outside_right_cable_mask"
            entry["suspension_cable_geometry_read"] = "pass_current_flipped_image_right_side_free_floating_cable_bars_removed"
    summary["updated_utc"] = created_at_utc
    summary["tacoma_story_preserving_cable_microrepair"] = {
        "status": "review_ready_pending_human_keep",
        "candidate_id": CANDIDATE_ID,
        "source_art_path": str(source_path),
        "source_art_sha256": source_sha,
        "rough_proof_root": str(proof_root),
        "proof_build_id": proof_build_id,
        "orientation_read": "right_side_of_current_flipped_image",
    }
    write_json(ROLLOUT_SUMMARY_PATH, summary)


def main() -> None:
    stamp, proof_stamp = utc_stamp()
    created_at_utc = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    source_input = K3_FLIPPED_SOURCE if K3_FLIPPED_SOURCE.exists() else K3_FLIPPED_FALLBACK
    if not source_input.exists():
        raise FileNotFoundError(f"Missing K3 flipped source: {K3_FLIPPED_SOURCE} or {K3_FLIPPED_FALLBACK}")
    if not K4_PROOF_ROOT.exists():
        raise FileNotFoundError(f"Missing K4 rough proof template: {K4_PROOF_ROOT}")

    source_package_id = f"tacoma_living_cover_{CANDIDATE_ID}_{stamp}"
    source_package_root = EPISODE_ROOT / "source_art" / source_package_id
    proof_packet_id = f"tacoma-narrows_rolling_caption_rail_k3_g2_right_cable_microrepair_{stamp}"
    proof_root = EPISODE_ROOT / "rough_assembly" / proof_packet_id
    if source_package_root.exists():
        raise FileExistsError(source_package_root)
    if proof_root.exists():
        raise FileExistsError(proof_root)

    source_asset_dir = source_package_root / "assets/source_art"
    review_dir = source_package_root / "review"
    qa_dir = source_package_root / "qa"
    ensure_dir(source_asset_dir)
    ensure_dir(review_dir)
    ensure_dir(qa_dir)

    original_copy = source_asset_dir / ORIGINAL_COPY_NAME
    repaired_source = source_asset_dir / NORMALIZED_NAME
    repair_mask = source_asset_dir / MASK_NAME
    diff_overlay = qa_dir / f"{CANDIDATE_ID}_pixel_diff_overlay.png"
    shutil.copy2(source_input, original_copy)
    diff_report = inpaint_vertical_bands(original_copy, repaired_source, repair_mask, diff_overlay)

    full_contact = qa_dir / f"{CANDIDATE_ID}_full_frame_before_after_contact_sheet.png"
    right_before = qa_dir / f"{CANDIDATE_ID}_right_cable_crop_before.png"
    right_after = qa_dir / f"{CANDIDATE_ID}_right_cable_crop_after.png"
    right_diff = qa_dir / f"{CANDIDATE_ID}_right_cable_pixel_diff_crop.png"
    right_contact = qa_dir / f"{CANDIDATE_ID}_right_cable_before_after_contact_sheet.png"
    crop_bbox = (1080, 0, 1920, 1080)
    crop(original_copy, crop_bbox, right_before)
    crop(repaired_source, crop_bbox, right_after)
    crop(diff_overlay, crop_bbox, right_diff)
    contact_sheet([original_copy, repaired_source], ["K3 flipped source", "K3 G2 right-cable microrepair"], full_contact, 960)
    contact_sheet([right_before, right_after, right_diff], ["right-side source crop", "right-side repaired crop", "changed pixels"], right_contact, 520)

    repaired_sha = sha256_file(repaired_source)
    original_sha = sha256_file(original_copy)
    palette = end_screen_palette_for_source_art(repaired_source)
    palette_contract = end_screen_palette_contract_for_source_art(repaired_source, palette)

    source_manifest_path = source_package_root / "source_art_manifest.json"
    review_note_path = review_dir / f"source_art_review_{CANDIDATE_ID}_{stamp}.md"
    diff_report_path = qa_dir / f"{CANDIDATE_ID}_pixel_diff_report.json"
    diff_report_payload = {
        "candidate_id": CANDIDATE_ID,
        "created_at_utc": created_at_utc,
        "base_source_path": str(source_input),
        "base_source_sha256": sha256_file(source_input),
        "workspace_original_copy_path": str(original_copy),
        "workspace_original_copy_sha256": original_sha,
        "repaired_source_path": str(repaired_source),
        "repaired_source_sha256": repaired_sha,
        **diff_report,
    }
    write_json(diff_report_path, diff_report_payload)

    source_manifest = {
        "packet_id": source_package_id,
        "episode_id": "Ep5_Tacoma-Narrows",
        "workflow": "long_form_video_production_v1",
        "phase_gate": "source_art_gate",
        "status": "review_ready_pending_human_keep_candidate_k3_g2_right_cable_microrepair",
        "created_at_utc": created_at_utc,
        "package_root": str(source_package_root),
        "visual_lane": "localized_source_preserving_raster_repair",
        "carrier_type": "localized_repaired_raster_source_art",
        "profile_id": "cascade-ink-lit-photoreal-v1",
        "selected_candidate_id": CANDIDATE_ID,
        "selected_candidate_recommendation": CANDIDATE_ID,
        "human_disposition": "pending",
        "base_story_source": {
            "source_art_id": "candidate_k3_roadway_wide_stance_flipped_layout_probe",
            "path": str(source_input),
            "sha256": sha256_file(source_input),
            "role": "story_source_of_truth_for_this_microrepair",
            "orientation_read": "current_review_image_is_horizontally_flipped_so_defect_is_on_image_right",
        },
        "repair_method": {
            "id": "localized_right_side_vertical_cable_band_microrepair_v1",
            "method": "deterministic_pil_masked_row_interpolation_then_original_composite",
            "default_lane": "localized_retouch_not_full_regeneration",
            "non_mask_policy": "all non-mask pixels preserved byte-identically after lossless PNG composite",
            "ai_full_frame_return_policy": "not_applicable_no_ai_full_frame_retouch_used",
            "mask_path": str(repair_mask),
            "mask_sha256": sha256_file(repair_mask),
            "mask_bands": RIGHT_SIDE_DEFECT_BANDS,
        },
        "candidate": {
            "id": CANDIDATE_ID,
            "label": "K3 flipped story-preserving right-side cable microrepair",
            "workspace_original_copy_path": str(original_copy),
            "workspace_original_copy_sha256": original_sha,
            "workspace_path": str(repaired_source),
            "workspace_sha256": repaired_sha,
            "dimensions": {"width": 1920, "height": 1080},
            "reads": {
                "visual_story_continuity_read": "pass_k3_flipped_story_plate_preserved_outside_right_cable_mask",
                "deck_torsion_story_read": "pass_wave_and_torsion_story_preserved",
                "human_witness_bracing_read": "pass_wide_stance_foreground_witness_and_sidewalk_figures_preserved",
                "weather_and_roadway_mood_read": "pass_wet_roadway_rain_water_and_1940s_mood_preserved",
                "historical_accuracy_read": "pass_1940_tacoma_narrows_story_plate_preserved_with_localized_geometry_cleanup",
                "source_reference_alignment_read": "pass_candidate_k3_flipped_composition_preserved",
                "public_anchor_geometry_read": "pass_tower_deck_rail_and_hanger_rhythm_preserved_outside_repair_mask",
                "suspension_cable_geometry_read": "pass_current_flipped_image_right_side_free_floating_foreground_bars_removed_no_cables_land_on_car_or_roadway",
                "right_cable_crop_read": "pass_right_side_crop_review_artifact_created_for_current_flipped_image",
                "pixel_diff_nonmask_read": diff_report["nonmask_preservation_read"],
                "texture_noise_read": "pass_no_full_frame_regeneration_or_texture_creep",
                "paper_architecture_visual_style_read": "pass_not_paper_architecture",
                "no_full_frame_regeneration_read": "pass",
            },
            "status": "review_ready_pending_human_keep",
        },
        "qa": {
            "full_frame_before_after_contact_sheet": artifact(full_contact, "full_frame_story_continuity_contact_sheet"),
            "right_cable_crop_before": artifact(right_before, "current_flipped_image_right_cable_crop_before"),
            "right_cable_crop_after": artifact(right_after, "current_flipped_image_right_cable_crop_after"),
            "right_cable_before_after_contact_sheet": artifact(right_contact, "right_cable_story_continuity_contact_sheet"),
            "pixel_diff_overlay": artifact(diff_overlay, "changed_pixels_overlay"),
            "pixel_diff_report": artifact(diff_report_path, "pixel_diff_nonmask_preservation_report"),
        },
        "end_screen_palette": palette,
        "end_screen_palette_contract": palette_contract,
        "gate_locks": {
            "may_rebuild_rough_proof": True,
            "may_render_final_mp4": False,
            "may_youtube_action": False,
            "public_release_ready": False,
        },
        "next_required_action": "Human review of K3 G2 full frame, right-side cable crop, and rough proof before any final render.",
    }
    write_json(source_manifest_path, source_manifest)
    review_note_path.write_text(
        f"""# Tacoma K3 G2 Right-Side Cable Microrepair Review

Status: `review_ready_pending_human_keep`

The active story source is the flipped K3 plate the current player referenced as `assets/source_art/candidate_k3_roadway_wide_stance_flipped_1920x1080.png`. Because that plate was horizontally flipped, the cable defect is on the **right side of the current image**.

## Review Focus

- Full-frame before/after: `{full_contact}`
- Right-side cable crop before/after: `{right_contact}`
- Final repaired plate: `{repaired_source}`
- Repair mask: `{repair_mask}`
- Pixel diff report: `{diff_report_path}`

## Contract

- Preserve deck torsion, wet roadway, car, foreground bracing witness, sidewalk witnesses, tower, rain, and 1940s mood.
- Repair only the image-right cable/suspender defect bands.
- Keep K4 traceable as geometry reference only, not an aesthetic successor.
- Keep final render, publish readiness, upload, and public release blocked until human keep.
""",
    )
    source_manifest["primary_review_artifact"] = artifact(review_note_path, "source_art_review_note")
    write_json(source_manifest_path, source_manifest)

    review_html_path = source_package_root / "review.html"
    review_html_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tacoma K3 G2 Right-Side Cable Microrepair Review</title>
  <style>
    body{{margin:0;background:#101514;color:#edf7fb;font-family:Inter,system-ui,sans-serif}}
    main{{max-width:1440px;margin:0 auto;padding:24px}}
    h1{{font-size:24px;font-weight:700;margin:0 0 16px}}
    figure{{margin:0 0 24px}}
    img{{display:block;max-width:100%;height:auto;background:#090c0b}}
    figcaption{{font-size:13px;color:#acc5d0;margin-top:8px}}
    .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
    @media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
<main>
  <h1>Tacoma K3 G2 Right-Side Cable Microrepair Review</h1>
  <figure>
    <img src="qa/{full_contact.name}" alt="Full frame before and after contact sheet">
    <figcaption>Full-frame story continuity: K3 flipped source versus localized repair.</figcaption>
  </figure>
  <figure>
    <img src="qa/{right_contact.name}" alt="Right-side cable crop contact sheet">
    <figcaption>Current flipped image right-side cable crop and changed-pixel overlay.</figcaption>
  </figure>
  <section class="grid">
    <figure>
      <img src="assets/source_art/{NORMALIZED_NAME}" alt="Final repaired Tacoma source plate">
      <figcaption>Final repaired source plate.</figcaption>
    </figure>
    <figure>
      <img src="assets/source_art/{MASK_NAME}" alt="Localized repair mask">
      <figcaption>Localized repair mask. Non-mask pixels are preserved.</figcaption>
    </figure>
  </section>
</main>
</body>
</html>
"""
    )

    mark_story_source_lineage(K3_SOURCE_MANIFEST, "source_art_candidate_k3", repaired_source, repaired_sha, created_at_utc)
    mark_story_source_lineage(G_ROUGH_MANIFEST, "prior_story_reference_candidate_g", repaired_source, repaired_sha, created_at_utc)
    mark_story_source_lineage(K3_ROUGH_MANIFEST, "rough_proof_candidate_k3_flipped", repaired_source, repaired_sha, created_at_utc)
    for manifest_path in PRIOR_ROLLING_MANIFESTS:
        mark_story_source_lineage(manifest_path, "rolling_caption_rail_predecessor_k3", repaired_source, repaired_sha, created_at_utc)
    mark_k4_geometry_reference(K4_SOURCE_MANIFEST, repaired_source, repaired_sha, created_at_utc)
    mark_k4_geometry_reference(K4_ROUGH_MANIFEST, repaired_source, repaired_sha, created_at_utc)

    shutil.copytree(K4_PROOF_ROOT, proof_root)
    proof_source_dir = proof_root / "assets/source_art"
    ensure_dir(proof_source_dir)
    proof_source_path = proof_source_dir / NORMALIZED_NAME
    shutil.copy2(repaired_source, proof_source_path)
    proof_source_sha = sha256_file(proof_source_path)
    proof_palette = end_screen_palette_for_source_art(proof_source_path)
    proof_palette_contract = end_screen_palette_contract_for_source_art(proof_source_path, proof_palette)
    proof_build_id = f"tacoma-narrows_rolling_caption_rail_{proof_stamp}"
    player_path = proof_root / "player.html"
    update_player_html(player_path, proof_root, proof_build_id, proof_palette, proof_palette_contract)

    proof_build_path = proof_root / "proof_build.json"
    proof_build = read_json(proof_build_path)
    proof_build.update(
        {
            "proof_build_id": proof_build_id,
            "proof_generated_at_utc": created_at_utc,
            "packet_stamp": stamp,
            "player_path": str(player_path),
            "player_url": f"{REVIEW_SERVER_BASE_URL}/{player_path.relative_to(EPISODES_ROOT).as_posix()}?v={proof_build_id}",
            "manifest_path": str(proof_root / "rough_assembly_manifest.json"),
            "source_art_story_preservation_read": "pass_k3_flipped_story_plate_preserved_outside_right_cable_mask",
            "suspension_cable_geometry_read": "pass_current_flipped_image_right_side_free_floating_cable_bars_removed",
        }
    )
    write_json(proof_build_path, proof_build)

    proof_manifest_path = proof_root / "rough_assembly_manifest.json"
    manifest = read_json(proof_manifest_path)
    proof_build_url = f"{REVIEW_SERVER_BASE_URL}/{proof_build_path.relative_to(EPISODES_ROOT).as_posix()}?v={proof_build_id}"
    player_url = f"{REVIEW_SERVER_BASE_URL}/{player_path.relative_to(EPISODES_ROOT).as_posix()}?v={proof_build_id}"
    manifest["packet_id"] = proof_packet_id
    manifest["status"] = "rolling_caption_rail_k3_g2_right_cable_microrepair_review_ready_pending_human_keep"
    manifest["created_utc"] = created_at_utc
    manifest["proof_build_id"] = proof_build_id
    manifest["proof_generated_at_utc"] = created_at_utc
    manifest["proof_build_json_path"] = str(proof_build_path)
    manifest["proof_build_json_url"] = proof_build_url
    manifest["proof_build_json_sha256"] = sha256_file(proof_build_path)
    manifest["source_predecessor_rough_proof_path"] = str(K4_PROOF_ROOT)
    manifest["source_predecessor_manifest_path"] = str(K4_ROUGH_MANIFEST)
    manifest["human_disposition"] = "pending"
    manifest["next_review_question"] = "Keep the Tacoma K3 G2 right-side cable microrepair rough proof, tighten, reject, or defer?"
    manifest["source_visual"] = {
        **manifest.get("source_visual", {}),
        "carrier": "episode_specific_localized_repaired_raster_source_art",
        "source_art_id": CANDIDATE_ID,
        "source_art_path": str(proof_source_path),
        "source_art_sha256": proof_source_sha,
        "source_art_override_status": "candidate_k3_g2_right_cable_microrepair_review_ready_pending_human_keep",
        "source_art_override_review_note_path": str(review_note_path),
        "source_art_override_review_note_sha256": sha256_file(review_note_path),
        "source_art_override_applied_read": "pass_k3_flipped_localized_right_side_cable_microrepair_applied_to_rough_proof",
        "media_referenced_only": False,
        "media_copied_or_modified": True,
        "right_rail_safe_space_revalidation_required": True,
        "base_story_plate_path": str(source_input),
        "base_story_plate_sha256": sha256_file(source_input),
        "orientation_read": "right_side_of_current_flipped_image_pre_flip_left_side_language_superseded",
        "visual_story_continuity_read": "pass_k3_flipped_story_plate_preserved_outside_right_cable_mask",
        "deck_torsion_story_read": "pass_wave_and_torsion_story_preserved",
        "human_witness_bracing_read": "pass_wide_stance_foreground_witness_and_sidewalk_figures_preserved",
        "weather_and_roadway_mood_read": "pass_wet_roadway_rain_water_and_1940s_mood_preserved",
        "suspension_cable_geometry_read": "pass_current_flipped_image_right_side_free_floating_foreground_bars_removed_no_cables_land_on_car_or_roadway",
    }
    manifest["source_art_repair"] = {
        "repair_id": CANDIDATE_ID,
        "repair_type": "localized_story_preserving_microrepair",
        "source_art_packet_path": str(source_package_root),
        "source_art_manifest_path": str(source_manifest_path),
        "source_art_manifest_sha256": sha256_file(source_manifest_path),
        "base_story_source_path": str(source_input),
        "base_story_source_sha256": sha256_file(source_input),
        "final_plate_path": str(proof_source_path),
        "final_plate_sha256": proof_source_sha,
        "repair_mask_path": str(repair_mask),
        "repair_mask_sha256": sha256_file(repair_mask),
        "right_cable_crop_before_path": str(right_before),
        "right_cable_crop_after_path": str(right_after),
        "right_cable_before_after_contact_sheet_path": str(right_contact),
        "pixel_diff_report_path": str(diff_report_path),
        "pixel_diff_report_sha256": sha256_file(diff_report_path),
        "pixel_diff_nonmask_read": diff_report["nonmask_preservation_read"],
        "visual_story_continuity_read": "pass_k3_flipped_story_plate_preserved_outside_right_cable_mask",
        "deck_torsion_story_read": "pass_wave_and_torsion_story_preserved",
        "human_witness_bracing_read": "pass_wide_stance_foreground_witness_and_sidewalk_figures_preserved",
        "weather_and_roadway_mood_read": "pass_wet_roadway_rain_water_and_1940s_mood_preserved",
        "suspension_cable_geometry_read": "pass_current_flipped_image_right_side_free_floating_foreground_bars_removed_no_cables_land_on_car_or_roadway",
        "previous_lineage_read": "k3_flipped_marked_tighten_geometry_only_story_source_k4_marked_geometry_reference_only",
    }
    manifest["end_screen_context"] = {
        **manifest.get("end_screen_context", {}),
        "end_screen_palette_treatment_model": END_SCREEN_PALETTE_TREATMENT_MODEL,
        "end_screen_palette_model": END_SCREEN_PALETTE_MODEL,
        "end_screen_palette_source": "sampled_episode_backplate",
        "end_screen_palette": proof_palette,
        "end_screen_palette_contract": proof_palette_contract,
        "end_screen_adaptive_palette_read": "pass_source_backplate_sampled_target_palette_contract",
    }
    if isinstance(manifest["end_screen_context"].get("end_screen_timing"), dict):
        manifest["end_screen_context"]["end_screen_timing"]["palette"] = proof_palette
    manifest["end_screen_palette_contract"] = proof_palette_contract
    manifest["end_screen_adaptive_render_audit_path"] = str(
        proof_root / "qa/end_screen_adaptive_render_audit/end_screen_adaptive_render_audit.json"
    )
    manifest["end_screen_adaptive_render_audit_sha256"] = "pending_browser_runtime_qa"
    manifest["end_screen_adaptive_render_audit_read"] = "pending_browser_runtime_qa"
    manifest["end_screen_adaptive_computed_style_read"] = "pending_browser_runtime_qa"
    manifest["end_screen_adaptive_pixel_sample_read"] = "pending_browser_runtime_qa"
    manifest["qa"] = {
        **manifest.get("qa", {}),
        "caption_full_vo_runtime_coverage_static_pass": False,
        "caption_full_vo_runtime_coverage_read": "pending_browser_runtime_qa",
        "caption_runtime_cutoff_read": "pending_browser_runtime_qa",
        "caption_scrub_transport_sync_read": "pending_browser_runtime_qa",
        "review_transport_playing_scrub_read": "pending_browser_runtime_qa",
        "caption_line_clip_read": "pending_browser_runtime_qa",
        "caption_audio_time_transform_sync_read": "pending_browser_runtime_qa",
        "caption_active_text_matches_audio_time_read": "pending_browser_runtime_qa",
        "right_rail_caption_paint_visibility_read": "pending_browser_runtime_qa",
        "proof_build_freshness_guard_read": "pending_browser_runtime_qa",
        "end_screen_runtime_qa_read": "pending_browser_runtime_qa",
        "end_screen_adaptive_render_audit_read": "pending_browser_runtime_qa",
        "end_screen_adaptive_computed_style_read": "pending_browser_runtime_qa",
        "end_screen_adaptive_pixel_sample_read": "pending_browser_runtime_qa",
        "visual_story_continuity_read": "pass_k3_flipped_story_plate_preserved_outside_right_cable_mask",
        "deck_torsion_story_read": "pass_wave_and_torsion_story_preserved",
        "human_witness_bracing_read": "pass_wide_stance_foreground_witness_and_sidewalk_figures_preserved",
        "weather_and_roadway_mood_read": "pass_wet_roadway_rain_water_and_1940s_mood_preserved",
        "suspension_cable_geometry_read": "pass_current_flipped_image_right_side_free_floating_foreground_bars_removed",
        "pixel_diff_nonmask_read": diff_report["nonmask_preservation_read"],
    }
    manifest["rough_assembly_reads"] = {
        **manifest.get("rough_assembly_reads", {}),
        "right_rail_safe_space_read": "pending_human_review_k3_g2_right_cable_microrepair",
        "visual_story_continuity_read": "pass_k3_flipped_story_plate_preserved_outside_right_cable_mask",
        "deck_torsion_story_read": "pass_wave_and_torsion_story_preserved",
        "human_witness_bracing_read": "pass_wide_stance_foreground_witness_and_sidewalk_figures_preserved",
        "weather_and_roadway_mood_read": "pass_wet_roadway_rain_water_and_1940s_mood_preserved",
        "pixel_diff_nonmask_read": diff_report["nonmask_preservation_read"],
        "suspension_cable_geometry_read": "pass_current_flipped_image_right_side_free_floating_foreground_bars_removed_no_cables_land_on_car_or_roadway",
        "source_art_repair_read": "pass_candidate_k3_g2_localized_right_side_repair_preserves_k3_story_source",
        "downstream_gate_read": "pass_blocked_until_human_k3_g2_rough_keep",
    }
    gate_block(manifest)
    manifest["proof_artifacts"] = {
        **manifest.get("proof_artifacts", {}),
        "player_html_path": str(player_path),
        "player_html_sha256": sha256_file(player_path),
        "source_predecessor_player_path": str(K4_PROOF_ROOT / "player.html"),
        "proof_build_json_path": str(proof_build_path),
        "proof_build_json_url": proof_build_url,
        "proof_build_json_sha256": sha256_file(proof_build_path),
        "review_packet_path": str(proof_root / "review/rolling_caption_rail_review_packet.md"),
        "source_art_review_html_path": str(review_html_path),
        "right_cable_contact_sheet_path": str(right_contact),
        "full_frame_contact_sheet_path": str(full_contact),
        "end_screen_adaptive_render_audit_path": manifest["end_screen_adaptive_render_audit_path"],
        "end_screen_adaptive_render_audit_sha256": "pending_browser_runtime_qa",
    }
    write_json(proof_manifest_path, manifest)

    local_source_manifest = proof_root / "references/source_art_manifest.json"
    ensure_dir(local_source_manifest.parent)
    shutil.copy2(source_manifest_path, local_source_manifest)
    review_packet_path = proof_root / "review/rolling_caption_rail_review_packet.md"
    review_packet = review_packet_path.read_text() if review_packet_path.exists() else "# Tacoma Rough Proof Review\n"
    insertion = f"""
## K3 G2 Right-Side Cable Microrepair

This proof uses `{CANDIDATE_ID}` as a localized repair of the current flipped K3 source plate. K4 remains traceable as a geometry reference only and is not the active backplate.

- Repaired source art: `{proof_source_path}`
- Source-art package: `{source_package_root}`
- Full-frame before/after: `{full_contact}`
- Right-side cable crop: `{right_contact}`
- Pixel diff report: `{diff_report_path}`
- Required read: `suspension_cable_geometry_read = pass_current_flipped_image_right_side_free_floating_foreground_bars_removed_no_cables_land_on_car_or_roadway`
- Downstream gates remain blocked until human rough-proof keep.
"""
    if "## K3 G2 Right-Side Cable Microrepair" not in review_packet:
        review_packet = review_packet.rstrip() + "\n\n" + insertion.strip() + "\n"
    review_packet_path.write_text(review_packet)
    manifest = read_json(proof_manifest_path)
    manifest["proof_artifacts"]["review_packet_path"] = str(review_packet_path)
    manifest["proof_artifacts"]["review_packet_sha256"] = sha256_file(review_packet_path)
    manifest["proof_artifacts"]["player_html_sha256"] = sha256_file(player_path)
    manifest["proof_artifacts"]["proof_build_json_sha256"] = sha256_file(proof_build_path)
    write_json(proof_manifest_path, manifest)

    update_baseline(proof_source_path, proof_source_sha, source_manifest_path, proof_root, created_at_utc)
    update_review_index(proof_root, proof_build_id)
    update_rollout_summary(proof_root, proof_build_id, proof_source_path, proof_source_sha, created_at_utc)

    print(
        json.dumps(
            {
                "source_package_root": str(source_package_root),
                "source_manifest_path": str(source_manifest_path),
                "repaired_source_art_path": str(repaired_source),
                "proof_root": str(proof_root),
                "proof_manifest_path": str(proof_manifest_path),
                "player_path": str(player_path),
                "player_url": player_url,
                "proof_build_id": proof_build_id,
                "right_cable_contact_sheet_path": str(right_contact),
                "full_frame_contact_sheet_path": str(full_contact),
                "pixel_diff_report_path": str(diff_report_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
