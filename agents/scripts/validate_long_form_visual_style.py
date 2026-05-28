#!/usr/bin/env python3
"""Preflight Cascade Effects video artifacts for Paper Architecture leakage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FORBIDDEN_PAPER_PATTERNS = [
    r"\bcascade-paper-architectures-ink-lit-v1\b",
    r"\bink-lit\s+paper architecture\b",
    r"\bpaper architecture\s+scene\b",
    r"\bfolded[- ]paper\b",
    r"\bfoam[- ]core\b",
    r"\bcream paper forms?\b",
    r"\bclean low-detail paper planes?\b",
    r"\bpaper cutaway\b",
    r"\bpaper aircraft\b",
    r"\bpaper architecture aircraft\b",
]

REQUIRED_STYLE_READ_GROUPS = [
    ("video_visual_style_scope_read", "long_form_source_art_lane_read"),
    ("paper_architecture_visual_style_read", "paper_architecture_resemblance_read"),
]

INVALIDATION_MARKERS = [
    "reject_wrong_longform_style",
    "rejected_wrong_longform_style",
    "invalidated_wrong_longform_style",
    "blocked_wrong_longform_style",
    "reject_wrong_video_visual_style",
    "rejected_wrong_video_visual_style",
    "invalidated_wrong_video_visual_style",
    "blocked_wrong_video_visual_style",
    "video_asset_used_paper_architecture",
    "source_art_generation_blocked_wrong_longform_style",
    "source_art_generation_blocked_wrong_video_visual_style",
    "tighten_required_wrong_longform_style_lane",
    "superseded_wrong_longform_style",
    "superseded_wrong_video_visual_style",
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def find_forbidden_terms(text: str) -> list[str]:
    found: list[str] = []
    for pattern in FORBIDDEN_PAPER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(pattern)
    return found


def read_json_if_possible(text: str) -> object | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def flattened_values(value: object) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            values.append(str(key))
            values.extend(flattened_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(flattened_values(item))
        return values
    return [str(value)]


def is_invalidation_artifact(text: str, parsed: object | None) -> bool:
    lower = text.lower()
    if any(marker in lower for marker in INVALIDATION_MARKERS):
        return True
    if isinstance(parsed, dict):
        values = " ".join(flattened_values(parsed)).lower()
        if any(marker in values for marker in INVALIDATION_MARKERS):
            return True
        reads = parsed.get("reads", {})
        if isinstance(reads, dict):
            values = [
                str(reads.get("paper_architecture_visual_style_read", "")).lower(),
                str(reads.get("paper_architecture_resemblance_read", "")).lower(),
            ]
            if any(value.startswith("reject") for value in values):
                return True
    return False


def missing_required_reads(text: str, parsed: object | None) -> list[str]:
    lower = text.lower()
    missing = []
    for group in REQUIRED_STYLE_READ_GROUPS:
        if not any(read in lower for read in group):
            missing.append(group[0])
    if isinstance(parsed, dict):
        reads = parsed.get("reads", {})
        if isinstance(reads, dict):
            missing = [
                read
                for read in missing
                if read not in reads
                and not (
                    read == "video_visual_style_scope_read"
                    and "long_form_source_art_lane_read" in reads
                )
                and not (
                    read == "paper_architecture_visual_style_read"
                    and "paper_architecture_resemblance_read" in reads
                )
            ]
    return missing


def validate_artifact(path: Path, require_reads: bool) -> dict[str, object]:
    text = read_text(path)
    parsed = read_json_if_possible(text)
    forbidden = find_forbidden_terms(text)
    invalidated = is_invalidation_artifact(text, parsed)
    missing_reads = missing_required_reads(text, parsed) if require_reads else []

    errors: list[str] = []
    if forbidden and not invalidated:
        errors.append(
            "active video artifact contains Paper Architecture visual style; "
            "Paper Architecture is allowed only for website assets, YouTube channel-brand assets, "
            "and CascadeEffects.tv website thumbnail-gallery images"
        )
    if missing_reads:
        errors.append(f"missing required style reads: {', '.join(missing_reads)}")

    return {
        "path": str(path),
        "status": "pass" if not errors else "fail",
        "forbidden_patterns": forbidden,
        "invalidated": invalidated,
        "missing_required_reads": missing_reads,
        "errors": errors,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that video artifacts do not advance Paper Architecture visual style.",
    )
    parser.add_argument("artifacts", nargs="+", type=Path)
    parser.add_argument(
        "--require-style-reads",
        action="store_true",
        help="Require video_visual_style_scope_read and paper_architecture_visual_style_read.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    results = []
    for artifact in args.artifacts:
        if not artifact.exists() or not artifact.is_file():
            results.append(
                {
                    "path": str(artifact),
                    "status": "fail",
                    "errors": [f"missing artifact: {artifact}"],
                }
            )
            continue
        results.append(validate_artifact(artifact, args.require_style_reads))

    ok = all(result["status"] == "pass" for result in results)
    print(json.dumps({"ok": ok, "results": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
