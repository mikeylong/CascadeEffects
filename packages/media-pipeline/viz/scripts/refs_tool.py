#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from subject_reference_plate import (
    SubjectReferencePlateError,
    build_subject_reference_plates_for_episode,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bin/ce refs")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--references-root", required=True)

    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("artifact", choices=["subject-plates"])
    build_parser.add_argument("episode_id")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    references_root = Path(args.references_root).resolve()
    try:
        if args.command == "build" and args.artifact == "subject-plates":
            summary = build_subject_reference_plates_for_episode(references_root, args.episode_id)
            print(f"INFO  subject-reference plates -> {summary['summary_path']}")
            for plate in summary["plates"]:
                print(f"INFO  built {plate['plate_id']} -> {plate['output_path']}")
            return 0
    except SubjectReferencePlateError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    raise SystemExit(f"Unsupported refs command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
