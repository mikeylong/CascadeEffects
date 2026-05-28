#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


APPLE_PIPELINE = "apple-ltx23-q8-one-stage"
VALID_PIPELINES = {"distilled", APPLE_PIPELINE}
VALID_SOURCE_STILL_ROLES = {"primary", "alternate"}
VALID_DISPOSITIONS = {"keep", "tighten", "diagnostic only", "reject"}

REQUIRED_SINGLE_FIELDS = (
    "beat_id",
    "source_still_path",
    "source_still_variant_role",
    "motion_pipeline",
    "model_repo",
    "seed",
    "prompt_variant_id",
    "disposition",
)
PROMPT_FIELDS = ("prompt_text", "prompt_path")
RAW_CLIP_FIELDS = ("raw_clip_path", "raw_clip_paths")
NORMALIZED_CLIP_FIELDS = ("normalized_clip_path", "normalized_clip_paths")
SELECTED_FIELDS = (
    "selected_for_motion_proof",
    "selected_for_motion_proof_status",
    "selected-for-motion-proof status",
)


class ContractError(ValueError):
    pass


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return any(_has_value(item) for item in value)
    if isinstance(value, dict):
        return bool(value)
    return True


def _has_any(candidate: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(key in candidate and _has_value(candidate[key]) for key in keys)


def _candidate_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        for key in ("motion_candidates", "candidates", "items"):
            if key in payload:
                items = payload[key]
                break
        else:
            items = [payload] if "beat_id" in payload else []
    else:
        items = []

    if not isinstance(items, list) or not items:
        raise ContractError("no motion candidate records found")

    candidates: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ContractError(f"candidate {index} is not an object")
        candidates.append(item)
    return candidates


def validate_json_contract(path: Path) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON: {exc}") from exc

    for index, candidate in enumerate(_candidate_items(payload), start=1):
        prefix = f"candidate {index}"
        missing = [
            key
            for key in REQUIRED_SINGLE_FIELDS
            if key not in candidate or not _has_value(candidate[key])
        ]
        if not _has_any(candidate, PROMPT_FIELDS):
            missing.append("prompt_text or prompt_path")
        if not _has_any(candidate, RAW_CLIP_FIELDS):
            missing.append("raw_clip_path or raw_clip_paths")
        if not _has_any(candidate, NORMALIZED_CLIP_FIELDS):
            missing.append("normalized_clip_path or normalized_clip_paths")
        if not _has_any(candidate, SELECTED_FIELDS):
            missing.append("selected_for_motion_proof status")
        if missing:
            raise ContractError(f"{prefix} missing required fields: {', '.join(missing)}")

        role = str(candidate["source_still_variant_role"])
        if role not in VALID_SOURCE_STILL_ROLES:
            raise ContractError(
                f"{prefix} source_still_variant_role must be one of "
                f"{sorted(VALID_SOURCE_STILL_ROLES)}"
            )

        pipeline = str(candidate["motion_pipeline"])
        if pipeline not in VALID_PIPELINES:
            raise ContractError(f"{prefix} motion_pipeline must be one of {sorted(VALID_PIPELINES)}")

        disposition = str(candidate["disposition"])
        if disposition not in VALID_DISPOSITIONS:
            raise ContractError(f"{prefix} disposition must be one of {sorted(VALID_DISPOSITIONS)}")

        if pipeline == APPLE_PIPELINE and not _has_value(candidate.get("text_encoder_repo")):
            raise ContractError(f"{prefix} apple-ltx23-q8-one-stage requires text_encoder_repo")


def _normalized_markdown_tokens(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _contains_any(normalized_text: str, keys: tuple[str, ...]) -> bool:
    return any(_normalized_markdown_tokens(key) in normalized_text for key in keys)


def validate_markdown_contract(path: Path) -> None:
    normalized = _normalized_markdown_tokens(path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_SINGLE_FIELDS if key not in normalized]
    if not _contains_any(normalized, PROMPT_FIELDS):
        missing.append("prompt_text or prompt_path")
    if not _contains_any(normalized, RAW_CLIP_FIELDS):
        missing.append("raw_clip_path or raw_clip_paths")
    if not _contains_any(normalized, NORMALIZED_CLIP_FIELDS):
        missing.append("normalized_clip_path or normalized_clip_paths")
    if not _contains_any(normalized, SELECTED_FIELDS):
        missing.append("selected_for_motion_proof status")
    if APPLE_PIPELINE.replace("-", "_") in normalized and "text_encoder_repo" not in normalized:
        missing.append("text_encoder_repo for apple-ltx23-q8-one-stage")
    if missing:
        raise ContractError(f"missing required fields: {', '.join(missing)}")


def validate_path(path: Path) -> None:
    if not path.exists():
        raise ContractError("file does not exist")
    if path.suffix.lower() == ".json":
        validate_json_contract(path)
    else:
        validate_markdown_contract(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Cascade Effects Shorts motion contact-sheet artifact contract fields."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="motion contact-sheet note or JSON path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    failed = False
    for path in args.paths:
        try:
            validate_path(path)
        except ContractError as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failed = True
        else:
            print(f"OK {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
