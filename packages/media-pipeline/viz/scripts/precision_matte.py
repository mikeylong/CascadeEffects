#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageFilter


PRECISION_MATTE_MODEL = "precision_matte_v1"
DEFAULT_CHOKE_PX = 2.0
DEFAULT_FEATHER_PX = 0.75
FALLBACK_CHOKE_PX = 1.0


class PrecisionMatteError(RuntimeError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def alpha_level_count(mask_image: Image.Image) -> int:
    histogram = mask_image.convert("L").histogram()
    return sum(1 for value in histogram if value > 0)


def has_intermediate_alpha(mask_image: Image.Image) -> bool:
    histogram = mask_image.convert("L").histogram()
    return any(histogram[index] > 0 for index in range(1, 255))


def apply_precision_matte(
    mask_image: Image.Image,
    *,
    choke_px: float = DEFAULT_CHOKE_PX,
    feather_px: float = DEFAULT_FEATHER_PX,
) -> Image.Image:
    """Apply the Cascade Effects tight-matte contract to an alpha mask."""
    mask = mask_image.convert("L")
    if mask.getbbox() is None:
        raise PrecisionMatteError("precision matte source mask is empty")

    choke_radius = max(0, int(round(float(choke_px))))
    if choke_radius > 0:
        mask = mask.filter(ImageFilter.MinFilter((choke_radius * 2) + 1))
    if float(feather_px) > 0.0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=float(feather_px)))
    return mask.convert("L")


def precision_matte_metrics(raw_mask: Image.Image, repaired_mask: Image.Image) -> dict[str, Any]:
    raw_l = raw_mask.convert("L")
    repaired_l = repaired_mask.convert("L")
    if raw_l.size != repaired_l.size:
        raise PrecisionMatteError("raw and repaired masks must share dimensions")
    changed = ImageChops.difference(raw_l, repaired_l)
    changed_pixels = sum(changed.histogram()[1:])
    return {
        "raw_alpha_level_count": alpha_level_count(raw_l),
        "repaired_alpha_level_count": alpha_level_count(repaired_l),
        "repaired_has_intermediate_alpha": has_intermediate_alpha(repaired_l),
        "changed_pixel_count": changed_pixels,
        "dimensions": [repaired_l.width, repaired_l.height],
    }


def write_edge_proof(raw_mask: Image.Image, repaired_mask: Image.Image, output_path: Path) -> Path:
    raw_l = raw_mask.convert("L")
    repaired_l = repaired_mask.convert("L")
    if raw_l.size != repaired_l.size:
        raise PrecisionMatteError("raw and repaired masks must share dimensions")

    union = ImageChops.lighter(raw_l, repaired_l)
    bbox = union.getbbox() or (0, 0, raw_l.width, raw_l.height)
    margin = 24
    left = max(0, bbox[0] - margin)
    top = max(0, bbox[1] - margin)
    right = min(raw_l.width, bbox[2] + margin)
    bottom = min(raw_l.height, bbox[3] + margin)
    before = raw_l.crop((left, top, right, bottom)).convert("RGB")
    after = repaired_l.crop((left, top, right, bottom)).convert("RGB")

    proof = Image.new("RGB", (before.width + after.width + 4, max(before.height, after.height)), (22, 22, 22))
    proof.paste(before, (0, 0))
    proof.paste(after, (before.width + 4, 0))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    proof.save(output_path)
    return output_path


def write_precision_matte_receipt(
    *,
    receipt_path: Path,
    raw_mask_path: Path,
    repaired_mask_path: Path,
    before_after_edge_proof_path: Path,
    choke_px: float = DEFAULT_CHOKE_PX,
    feather_px: float = DEFAULT_FEATHER_PX,
    fallback_reason: str = "",
    final_composite_path: Path | None = None,
    final_composite_sha256: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with Image.open(raw_mask_path) as opened_raw:
        raw_mask = opened_raw.convert("L")
    with Image.open(repaired_mask_path) as opened_repaired:
        repaired_mask = opened_repaired.convert("L")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "model": PRECISION_MATTE_MODEL,
        "created_at": utc_now_iso(),
        "raw_mask_path": str(raw_mask_path),
        "raw_mask_sha256": sha256_path(raw_mask_path),
        "raw_mask_usage": "proposal_only",
        "repaired_mask_path": str(repaired_mask_path),
        "repaired_mask_sha256": sha256_path(repaired_mask_path),
        "approved_compositing_alpha_path": str(repaired_mask_path),
        "choke_px": float(choke_px),
        "feather_px": float(feather_px),
        "fallback_reason": fallback_reason,
        "before_after_edge_proof_path": str(before_after_edge_proof_path),
        "before_after_edge_proof_sha256": sha256_path(before_after_edge_proof_path)
        if before_after_edge_proof_path.exists()
        else "",
        "final_composite_path": str(final_composite_path) if final_composite_path is not None else "",
        "final_composite_sha256": final_composite_sha256,
        "qa": precision_matte_metrics(raw_mask, repaired_mask),
    }
    if extra:
        payload.update(extra)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return payload


def validate_precision_matte_receipt(
    receipt_path: Path,
    *,
    require_final_composite: bool = False,
) -> dict[str, Any]:
    if not receipt_path.exists():
        raise PrecisionMatteError(f"missing precision matte receipt: {receipt_path}")
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PrecisionMatteError(f"{receipt_path}: receipt is not valid JSON") from exc
    if payload.get("model") != PRECISION_MATTE_MODEL:
        raise PrecisionMatteError(f"{receipt_path}: model must be {PRECISION_MATTE_MODEL}")

    raw_path = Path(str(payload.get("raw_mask_path", ""))).expanduser()
    repaired_path = Path(str(payload.get("repaired_mask_path", ""))).expanduser()
    proof_path = Path(str(payload.get("before_after_edge_proof_path", ""))).expanduser()
    for label, path in (("raw_mask_path", raw_path), ("repaired_mask_path", repaired_path), ("before_after_edge_proof_path", proof_path)):
        if not path.exists():
            raise PrecisionMatteError(f"{receipt_path}: {label} is missing: {path}")

    if sha256_path(raw_path) != str(payload.get("raw_mask_sha256", "")):
        raise PrecisionMatteError(f"{receipt_path}: raw mask SHA mismatch")
    if sha256_path(repaired_path) != str(payload.get("repaired_mask_sha256", "")):
        raise PrecisionMatteError(f"{receipt_path}: repaired mask SHA mismatch")
    if sha256_path(proof_path) != str(payload.get("before_after_edge_proof_sha256", "")):
        raise PrecisionMatteError(f"{receipt_path}: edge proof SHA mismatch")

    with Image.open(repaired_path) as opened:
        repaired = opened.convert("L")
    if repaired.getbbox() is None:
        raise PrecisionMatteError(f"{receipt_path}: repaired mask is empty")
    if not has_intermediate_alpha(repaired):
        raise PrecisionMatteError(f"{receipt_path}: repaired mask is binary-only")

    choke_px = float(payload.get("choke_px", 0.0))
    fallback_reason = str(payload.get("fallback_reason", "")).strip()
    if abs(choke_px - FALLBACK_CHOKE_PX) <= 0.01 and not fallback_reason:
        raise PrecisionMatteError(f"{receipt_path}: 1px fallback requires a thin-detail reason")
    if choke_px < FALLBACK_CHOKE_PX - 0.01:
        raise PrecisionMatteError(f"{receipt_path}: choke_px must be at least 1px")

    if require_final_composite:
        final_path = Path(str(payload.get("final_composite_path", ""))).expanduser()
        if not final_path.exists():
            raise PrecisionMatteError(f"{receipt_path}: final_composite_path is missing")
        if sha256_path(final_path) != str(payload.get("final_composite_sha256", "")):
            raise PrecisionMatteError(f"{receipt_path}: final composite SHA mismatch")

    return payload
