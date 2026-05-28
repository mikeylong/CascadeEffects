#!/usr/bin/env python3
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Please install Pillow: pip install pillow")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("Please install numpy: pip install numpy")
    sys.exit(1)


def load_image(path):
    img = Image.open(path).convert("RGB")
    return np.asarray(img).astype(np.float32) / 255.0


def rgb_to_gray(img):
    return 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]


def score_asymmetry(img):
    gray = rgb_to_gray(img)
    _h, w = gray.shape
    left = gray[:, : w // 2]
    right = gray[:, w // 2 :]

    left_mass = np.mean(np.abs(left - left.mean()))
    right_mass = np.mean(np.abs(right - right.mean()))
    total = left_mass + right_mass + 1e-8
    balance = abs(left_mass - right_mass) / total

    if balance < 0.05:
        return 0.55
    if balance > 0.95:
        return 0.55
    return min(1.0, 0.6 + balance * 0.45)


def quantize_palette(img, bins=6):
    arr = np.clip((img * bins).astype(int), 0, bins - 1)
    flat = arr.reshape(-1, 3)
    unique, counts = np.unique(flat, axis=0, return_counts=True)
    proportions = counts / counts.sum()
    return unique, proportions


def score_palette_discipline(img):
    _unique, proportions = quantize_palette(img, bins=6)
    meaningful = proportions[proportions > 0.03]
    count_score = 1.0 if 2 <= len(meaningful) <= 5 else max(0.2, 1.0 - 0.12 * abs(len(meaningful) - 3))

    hsv_like_sat = img.max(axis=2) - img.min(axis=2)
    saturated = (hsv_like_sat > 0.45).mean()
    if 0.0 <= saturated <= 0.18:
        accent_score = 1.0
    else:
        accent_score = max(0.2, 1.0 - saturated * 3)

    return float((count_score * 0.55) + (accent_score * 0.45))


def score_focal_clarity(img):
    gray = rgb_to_gray(img)
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)
    gx[:, 1:] = np.abs(gray[:, 1:] - gray[:, :-1])
    gy[1:, :] = np.abs(gray[1:, :] - gray[:-1, :])
    saliency = gx + gy

    threshold = np.quantile(saliency, 0.98)
    hotspots = saliency > threshold
    hotspot_density = hotspots.mean()

    if hotspot_density < 0.002:
        return 0.35
    if hotspot_density <= 0.02:
        return 0.95
    if hotspot_density <= 0.05:
        return 0.75
    return max(0.2, 1.0 - hotspot_density * 8)


def score_visual_noise(img):
    gray = rgb_to_gray(img)
    lap = np.zeros_like(gray)
    lap[1:-1, 1:-1] = (
        -4 * gray[1:-1, 1:-1]
        + gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
    )
    variance = float(np.var(lap))

    if variance <= 0.002:
        return 1.0
    if variance <= 0.008:
        return 0.85
    if variance <= 0.02:
        return 0.65
    return max(0.1, 1.0 - variance * 15)


def evaluate_image(path):
    img = load_image(path)
    asymmetry = score_asymmetry(img)
    palette = score_palette_discipline(img)
    focal = score_focal_clarity(img)
    noise = score_visual_noise(img)

    overall = (
        asymmetry * 0.12
        + palette * 0.20
        + focal * 0.43
        + noise * 0.25
    )

    return {
        "filename": Path(path).name,
        "scores": {
            "asymmetry_ratio": round(asymmetry, 3),
            "palette_discipline": round(palette, 3),
            "focal_clarity": round(focal, 3),
            "visual_noise": round(noise, 3)
        },
        "overall_score": round(overall, 3),
        "pass": overall >= 0.74
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python starter_evaluator.py /path/to/image.png")
        sys.exit(1)

    result = evaluate_image(sys.argv[1])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
