from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageColor, ImageFilter, ImageOps, ImageStat

from .config import RuntimeConfig
from .io import read_json, write_json


def _distance(pixel: tuple[int, int, int], target: tuple[int, int, int]) -> int:
    return abs(pixel[0] - target[0]) + abs(pixel[1] - target[1]) + abs(pixel[2] - target[2])


def _downsample(image: Image.Image, *, max_width: int = 220) -> Image.Image:
    width, height = image.size
    if width <= max_width:
        return image.copy()
    scale = max_width / float(width)
    return image.resize((max_width, max(1, int(height * scale))), Image.Resampling.LANCZOS)


def _subject_box(scene: dict[str, Any], size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    scale = float(scene["subject_anchor"]["scale"])
    center_x = int(width * float(scene["subject_anchor"]["placement"][0]))
    center_y = int(height * float(scene["subject_anchor"]["placement"][1]))
    box_w = int(width * max(0.18, min(scale * 0.78, 0.42)))
    box_h = int(box_w * 1.35)
    left = max(0, center_x - (box_w // 2))
    top = max(0, center_y - (box_h // 2))
    return left, top, min(width, left + box_w), min(height, top + box_h)


def _normalized_box(scene: dict[str, Any], key: str) -> tuple[float, float, float, float]:
    zone = scene["caption_safe_zone"][key]
    return float(zone[0]), float(zone[1]), float(zone[2]), float(zone[3])


def _box_overlap_ratio(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    left = max(a[0], b[0])
    top = max(a[1], b[1])
    right = min(a[2], b[2])
    bottom = min(a[3], b[3])
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    area = max(1, (a[2] - a[0]) * (a[3] - a[1]))
    return intersection / float(area)


def _subtitle_intrusion(scene: dict[str, Any], size: tuple[int, int]) -> bool:
    box = _subject_box(scene, size)
    width, height = size
    zone = _normalized_box(scene, "subtitles")
    subtitle_box = (
        int(zone[0] * width),
        int(zone[1] * height),
        int(zone[2] * width),
        int(zone[3] * height),
    )
    return _box_overlap_ratio(box, subtitle_box) > 0.12


def score_asymmetry(img: Image.Image) -> float:
    gray = _downsample(img).convert("L")
    width, _ = gray.size
    left = gray.crop((0, 0, width // 2, gray.size[1]))
    right = gray.crop((width // 2, 0, width, gray.size[1]))
    left_mass = ImageStat.Stat(left).stddev[0]
    right_mass = ImageStat.Stat(right).stddev[0]
    total = left_mass + right_mass + 1e-8
    balance = abs(left_mass - right_mass) / total
    if balance < 0.08:
        return 0.2
    if balance > 0.9:
        return 0.4
    return min(1.0, 0.35 + (balance * 0.9))


def score_palette_discipline(img: Image.Image, accent_rgb: tuple[int, int, int]) -> float:
    sample = _downsample(img, max_width=180).convert("RGB")
    quantized = sample.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    histogram = quantized.histogram()
    total = sum(histogram) or 1
    meaningful = [count / total for count in histogram if (count / total) > 0.03]
    count_score = 1.0 if 2 <= len(meaningful) <= 4 else max(0.45, 1.0 - (0.12 * abs(len(meaningful) - 3)))

    saturated_matches = 0
    pixels = sample.load()
    sample_pixels = sample.size[0] * sample.size[1]
    for y in range(sample.size[1]):
        for x in range(sample.size[0]):
            pixel = pixels[x, y]
            saturation = max(pixel) - min(pixel)
            if saturation > 92 and _distance(pixel, accent_rgb) <= 120:
                saturated_matches += 1
    saturated_ratio = saturated_matches / float(sample_pixels or 1)
    if 0.0002 <= saturated_ratio <= 0.02:
        accent_score = 1.0
    elif saturated_ratio < 0.0002:
        accent_score = 0.88
    else:
        accent_score = max(0.35, 1.0 - (saturated_ratio * 10))
    return (count_score * 0.55) + (accent_score * 0.45)


def score_focal_clarity(img: Image.Image) -> float:
    gray = _downsample(img, max_width=180).convert("L")
    width, height = gray.size
    pixels = gray.load()
    saliency: list[int] = []
    for y in range(height):
        for x in range(width):
            value = 0
            if x > 0:
                value += abs(pixels[x, y] - pixels[x - 1, y])
            if y > 0:
                value += abs(pixels[x, y] - pixels[x, y - 1])
            saliency.append(value)
    saliency.sort()
    threshold = saliency[max(0, int(len(saliency) * 0.98) - 1)] if saliency else 0
    hotspot_density = sum(1 for value in saliency if value >= threshold and value > 0) / float(len(saliency) or 1)
    if hotspot_density < 0.001:
        return 0.52
    if hotspot_density <= 0.02:
        return 0.95
    if hotspot_density <= 0.08:
        return 0.84
    return max(0.35, 1.0 - (hotspot_density * 5.5))


def score_visual_noise(img: Image.Image) -> float:
    gray = _downsample(img, max_width=180).convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    variance = ImageStat.Stat(edges).var[0] / float(255 * 255)
    if variance <= 0.002:
        return 1.0
    if variance <= 0.02:
        return 0.9
    if variance <= 0.05:
        return 0.78
    return max(0.3, 1.0 - (variance * 8))


def _accent_component_count(img: Image.Image, accent_rgb: tuple[int, int, int]) -> int:
    sample = _downsample(img, max_width=160).convert("RGB")
    width, height = sample.size
    pixels = sample.load()
    mask = [[False for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if (max(pixel) - min(pixel)) > 92 and _distance(pixel, accent_rgb) <= 120:
                mask[y][x] = True
    seen = [[False for _ in range(width)] for _ in range(height)]
    components = 0
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or seen[y][x]:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            area = 0
            while stack:
                cx, cy = stack.pop()
                area += 1
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if area >= 6:
                components += 1
    return components


def _detect_text(img: Image.Image) -> bool:
    gray = _downsample(img, max_width=180).convert("L")
    contrast = ImageOps.autocontrast(gray)
    width, height = contrast.size
    pixels = contrast.load()
    mask = [[pixels[x, y] < 84 for x in range(width)] for y in range(height)]
    seen = [[False for _ in range(width)] for _ in range(height)]
    small_components = 0
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or seen[y][x]:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            area = 0
            min_x = max_x = x
            min_y = max_y = y
            while stack:
                cx, cy = stack.pop()
                area += 1
                min_x = min(min_x, cx)
                min_y = min(min_y, cy)
                max_x = max(max_x, cx)
                max_y = max(max_y, cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            box_w = max_x - min_x + 1
            box_h = max_y - min_y + 1
            if 6 <= area <= 180 and 2 <= box_h <= 18 and 2 <= box_w <= 28:
                small_components += 1
    return small_components >= 8


def _symmetry_too_high(img: Image.Image) -> bool:
    gray = _downsample(img, max_width=180).convert("L")
    mirrored = gray.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    diff = ImageChops.difference(gray, mirrored)
    mean = ImageStat.Stat(diff).mean[0] / 255.0
    return mean < 0.03


def _center_weighted_subject(scene: dict[str, Any]) -> bool:
    x = float(scene["subject_anchor"]["placement"][0])
    return 0.46 <= x <= 0.54


def evaluate_still(scene: dict[str, Any], image_path: Path, profile: dict[str, Any]) -> dict[str, Any]:
    image = Image.open(image_path).convert("RGB")
    thresholds = profile["contract_metrics"]["evaluator_thresholds"]
    accent_rgb = ImageColor.getrgb(profile["palette"]["accent"])
    metrics = {
        "asymmetry_ratio": round(score_asymmetry(image), 4),
        "palette_discipline": round(score_palette_discipline(image, accent_rgb), 4),
        "focal_clarity": round(score_focal_clarity(image), 4),
        "visual_noise": round(score_visual_noise(image), 4),
    }
    overall_score = round(
        (metrics["asymmetry_ratio"] * 0.35)
        + (metrics["palette_discipline"] * 0.2)
        + (metrics["focal_clarity"] * 0.3)
        + (metrics["visual_noise"] * 0.15),
        4,
    )
    hard_fail_checks = {
        "detected_text": _detect_text(image),
        "more_than_one_saturated_accent": _accent_component_count(image, accent_rgb) > 1,
        "center_weighted_primary_subject": _center_weighted_subject(scene),
        "symmetry_too_high": _symmetry_too_high(image),
        "subtitle_zone_intrusion": _subtitle_intrusion(scene, image.size),
    }
    threshold_failures = {
        key: metrics[key] < float(thresholds[key])
        for key in ("asymmetry_ratio", "palette_discipline", "focal_clarity", "visual_noise")
    }
    passed = (overall_score >= float(thresholds["overall_pass_threshold"])) and not any(hard_fail_checks.values()) and not any(threshold_failures.values())
    return {
        "metrics": metrics,
        "overall_score": overall_score,
        "hard_fail_checks": hard_fail_checks,
        "threshold_failures": threshold_failures,
        "pass": passed,
    }


def evaluate_motion_stability(scene: dict[str, Any], poster_path: Path, still_path: Path, profile: dict[str, Any]) -> float:
    poster = Image.open(poster_path).convert("RGB")
    still = Image.open(still_path).convert("RGB")
    diff = ImageChops.difference(poster, still)
    delta = ImageStat.Stat(diff.convert("L")).mean[0] / 255.0
    return round(max(0.0, 1.0 - min(delta / 0.24, 1.0)), 4)


def run_evaluation(runtime: RuntimeConfig, scene_paths: list[Path], profiles: dict[str, dict[str, Any]]) -> Path:
    summary: dict[str, Any] = {
        "scenes": {},
        "acceptance": {
            "stills_meeting_threshold": 0,
            "motion_clips_meeting_threshold": 0,
            "packaging_frames_meeting_threshold": 0,
        },
    }
    for scene_path in scene_paths:
        scene = read_json(scene_path)
        profile = profiles[scene["style_profile"]]
        scene_entry: dict[str, Any] = {
            "id": scene["id"],
            "style_profile": scene["style_profile"],
            "beat_id": scene.get("beat_id", ""),
        }
        still_outputs = scene.get("outputs", {})
        for mode in ("sketch", "final", "lock"):
            output = still_outputs.get(mode, {})
            image_path = str(output.get("image_path", "")).strip()
            if image_path:
                scene_entry.setdefault("stills", {})[mode] = evaluate_still(scene, Path(image_path), profile)
        motion_outputs = still_outputs.get("motion", {})
        for preset, payload in motion_outputs.items():
            poster_path = str(payload.get("poster_path", "")).strip()
            still_path = str(payload.get("still_path", "")).strip()
            if poster_path and still_path:
                stability = evaluate_motion_stability(scene, Path(poster_path), Path(still_path), profile)
                scene_entry.setdefault("motion", {})[preset] = {
                    "style_persistence_in_motion": stability,
                    "pass": stability >= 0.64,
                }
        summary["scenes"][scene["id"]] = scene_entry

    for scene_id, entry in summary["scenes"].items():
        final_payload = (entry.get("stills", {}) or {}).get("final") or (entry.get("stills", {}) or {}).get("lock")
        any_still_pass = any(payload.get("pass") for payload in (entry.get("stills", {}) or {}).values())
        if scene_id.startswith("scene_") and final_payload and final_payload["pass"]:
            summary["acceptance"]["stills_meeting_threshold"] += 1
        if (
            ("packaging" in scene_id or entry.get("beat_id") == "beat_07")
            and any_still_pass
        ):
            summary["acceptance"]["packaging_frames_meeting_threshold"] += 1
        for payload in (entry.get("motion", {}) or {}).values():
            if payload["pass"]:
                summary["acceptance"]["motion_clips_meeting_threshold"] += 1

    output_path = runtime.evaluations_root / "evaluation_summary.json"
    write_json(output_path, summary)
    return output_path
