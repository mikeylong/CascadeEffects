#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
MEDIA_SCRIPTS_DIR = ROOT / "packages" / "media-pipeline" / "viz" / "scripts"
if str(MEDIA_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(MEDIA_SCRIPTS_DIR))

from precision_matte import PrecisionMatteError, validate_precision_matte_receipt  # noqa: E402


def _path_from_manifest(base: Path, value: Any) -> Path:
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path
    return (base.parent / path).resolve()


def _collect_receipts_from_manifest(manifest_path: Path) -> list[tuple[str, Path, bool]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipts: list[tuple[str, Path, bool]] = []

    def add(label: str, value: Any, *, require_final: bool = False) -> None:
        if isinstance(value, str) and value.strip():
            receipts.append((label, _path_from_manifest(manifest_path, value), require_final))

    add("precision_matte_receipt_path", payload.get("precision_matte_receipt_path"), require_final=True)

    precision = payload.get("precision_matte")
    if isinstance(precision, dict):
        add("precision_matte.receipt_path", precision.get("receipt_path"), require_final=bool(precision.get("final_composite_required", False)))
        add("precision_matte.export_receipt_path", precision.get("export_receipt_path"), require_final=True)

    mask = payload.get("mask")
    if isinstance(mask, dict):
        add("mask.precision_matte_receipt_path", mask.get("precision_matte_receipt_path"), require_final=True)

    if receipts:
        return receipts

    mask_like_fields = {
        "mask_sha256",
        "mask_source",
        "soft_mask_path",
        "layout_mask_path",
        "source_mask_path",
        "approved_mask_path",
    }
    if any(str(payload.get(field, "")).strip() for field in mask_like_fields):
        raise PrecisionMatteError(
            f"{manifest_path}: manifest references mask output but has no precision_matte receipt path"
        )
    return receipts


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Cascade Effects precision matte receipts.")
    parser.add_argument("--receipt", action="append", default=[], help="Precision matte receipt JSON path.")
    parser.add_argument("--manifest", action="append", default=[], help="Manifest containing precision matte receipt paths.")
    parser.add_argument("--require-final-composite", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checks: list[tuple[str, Path, bool]] = []
    for receipt in args.receipt:
        checks.append(("receipt", Path(receipt).expanduser().resolve(), bool(args.require_final_composite)))
    errors: list[str] = []
    for manifest in args.manifest:
        manifest_path = Path(manifest).expanduser().resolve()
        try:
            checks.extend(_collect_receipts_from_manifest(manifest_path))
        except (OSError, json.JSONDecodeError, PrecisionMatteError) as exc:
            errors.append(str(exc))

    if not checks and not errors:
        errors.append("at least one --receipt or --manifest is required")

    results: list[dict[str, Any]] = []
    for label, receipt_path, require_final in checks:
        try:
            payload = validate_precision_matte_receipt(
                receipt_path,
                require_final_composite=require_final or bool(args.require_final_composite),
            )
            results.append(
                {
                    "ok": True,
                    "label": label,
                    "receipt_path": str(receipt_path),
                    "model": payload.get("model"),
                    "repaired_mask_path": payload.get("repaired_mask_path"),
                }
            )
        except PrecisionMatteError as exc:
            errors.append(str(exc))
            results.append({"ok": False, "label": label, "receipt_path": str(receipt_path), "error": str(exc)})

    output = {"ok": not errors, "results": results, "errors": errors}
    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=True))
    else:
        if errors:
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
        else:
            print(f"precision matte validation passed ({len(results)} receipt(s))")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
