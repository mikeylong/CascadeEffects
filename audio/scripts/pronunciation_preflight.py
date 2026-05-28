#!/usr/bin/env python3
"""Pronunciation preflight and local alias transforms for ElevenLabs renders."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEXICON_PATH = REPO_ROOT / "references" / "pronunciation" / "known_risks_v1.json"


@dataclass(frozen=True)
class PronunciationRule:
    id: str
    status: str
    severity: str
    mode: str
    match_type: str
    pattern: str
    replacement: str
    case_sensitive: bool
    pronunciation_note: str

    @property
    def is_required_alias(self) -> bool:
        return self.severity == "required" and self.mode == "local_alias"

    def compiled_pattern(self) -> re.Pattern[str]:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        if self.match_type == "literal":
            pattern = re.escape(self.pattern)
        elif self.match_type == "regex":
            pattern = self.pattern
        else:
            raise ValueError(f"{self.id}: unsupported match_type {self.match_type!r}")
        return re.compile(pattern, flags)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            loaded = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON ({exc})") from exc
        if not isinstance(loaded, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(loaded)
    if not rows:
        raise ValueError(f"{path}: no jobs found")
    return rows


def load_rules(path: Path = DEFAULT_LEXICON_PATH) -> list[PronunciationRule]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    raw_rules = loaded.get("rules", [])
    if not isinstance(raw_rules, list):
        raise ValueError(f"{path}: rules must be a list")
    rules: list[PronunciationRule] = []
    seen: set[str] = set()
    for index, raw_rule in enumerate(raw_rules, start=1):
        if not isinstance(raw_rule, dict):
            raise ValueError(f"{path}: rule {index} must be an object")
        rule = PronunciationRule(
            id=str(raw_rule.get("id") or "").strip(),
            status=str(raw_rule.get("status") or "").strip(),
            severity=str(raw_rule.get("severity") or "").strip(),
            mode=str(raw_rule.get("mode") or "").strip(),
            match_type=str(raw_rule.get("match_type") or "").strip(),
            pattern=str(raw_rule.get("pattern") or ""),
            replacement=str(raw_rule.get("replacement") or ""),
            case_sensitive=bool(raw_rule.get("case_sensitive", False)),
            pronunciation_note=str(raw_rule.get("pronunciation_note") or "").strip(),
        )
        if not rule.id:
            raise ValueError(f"{path}: rule {index} missing id")
        if rule.id in seen:
            raise ValueError(f"{path}: duplicate rule id {rule.id}")
        seen.add(rule.id)
        if rule.status != "approved":
            raise ValueError(f"{path}: rule {rule.id} is not approved")
        if rule.is_required_alias and not rule.replacement:
            raise ValueError(f"{path}: required alias rule {rule.id} missing replacement")
        rule.compiled_pattern()
        rules.append(rule)
    return rules


def lexicon_metadata(path: Path = DEFAULT_LEXICON_PATH) -> dict[str, str]:
    return {"path": str(path), "sha256": sha256_file(path)}


def _case_adjusted_replacement(match_text: str, replacement: str) -> str:
    if not match_text or not replacement:
        return replacement
    if match_text[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def apply_rules_to_text(
    text: str,
    *,
    lexicon_path: Path = DEFAULT_LEXICON_PATH,
) -> tuple[str, list[dict[str, Any]]]:
    rules = load_rules(lexicon_path)
    transformed = text
    applied: list[dict[str, Any]] = []

    for rule in rules:
        pattern = rule.compiled_pattern()
        matches = list(pattern.finditer(transformed))
        if not matches:
            continue
        if rule.mode == "review_marker":
            for match in matches:
                applied.append(
                    {
                        "rule_id": rule.id,
                        "mode": rule.mode,
                        "severity": rule.severity,
                        "match": match.group(0),
                        "replacement": "",
                        "pronunciation_note": rule.pronunciation_note,
                    }
                )
            continue
        if rule.mode != "local_alias":
            raise ValueError(f"{rule.id}: unsupported mode {rule.mode!r}")

        def replace(match: re.Match[str]) -> str:
            replacement = _case_adjusted_replacement(match.group(0), rule.replacement)
            applied.append(
                {
                    "rule_id": rule.id,
                    "mode": rule.mode,
                    "severity": rule.severity,
                    "match": match.group(0),
                    "replacement": replacement,
                    "pronunciation_note": rule.pronunciation_note,
                }
            )
            return replacement

        transformed = pattern.sub(replace, transformed)

    return transformed, applied


def scan_jobs(
    jobs: list[dict[str, Any]],
    *,
    text_key: str,
    lexicon_path: Path = DEFAULT_LEXICON_PATH,
) -> dict[str, Any]:
    rules = load_rules(lexicon_path)
    job_reports: list[dict[str, Any]] = []
    for index, job in enumerate(jobs, start=1):
        raw_text = str(job.get(text_key) or "")
        transformed, applied = apply_rules_to_text(raw_text, lexicon_path=lexicon_path)
        required_matches = [
            item
            for item in applied
            if item.get("severity") == "required" and item.get("mode") == "local_alias"
        ]
        review_matches = [item for item in applied if item.get("severity") == "review"]
        if required_matches or review_matches:
            job_reports.append(
                {
                    "job_index": index,
                    "out": job.get("out"),
                    "required_rule_ids": sorted({str(item["rule_id"]) for item in required_matches}),
                    "review_rule_ids": sorted({str(item["rule_id"]) for item in review_matches}),
                    "would_change_text": transformed != raw_text,
                }
            )

    return {
        "lexicon": lexicon_metadata(lexicon_path),
        "rule_count": len(rules),
        "job_count": len(jobs),
        "matched_job_count": len(job_reports),
        "jobs": job_reports,
        "blockers": [],
    }


def verify_compiled_jobs(
    jobs: list[dict[str, Any]],
    *,
    lexicon_path: Path = DEFAULT_LEXICON_PATH,
) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    job_reports: list[dict[str, Any]] = []

    for index, job in enumerate(jobs, start=1):
        source_text = str(job.get("spoken_input") or job.get("input") or "")
        rendered_text = str(job.get("elevenlabs_text") or "")
        expected_text, expected_applied = apply_rules_to_text(source_text, lexicon_path=lexicon_path)
        expected_required_ids = sorted(
            {
                str(item["rule_id"])
                for item in expected_applied
                if item.get("severity") == "required" and item.get("mode") == "local_alias"
            }
        )
        applied_items = job.get("elevenlabs_pronunciation_applied_rules")
        applied_ids = sorted(
            {
                str(item.get("rule_id"))
                for item in applied_items
                if isinstance(item, dict) and item.get("rule_id")
            }
        ) if isinstance(applied_items, list) else []

        missing_ids = [rule_id for rule_id in expected_required_ids if rule_id not in applied_ids]
        if missing_ids:
            blockers.append(
                {
                    "job_index": index,
                    "out": job.get("out"),
                    "missing_required_rule_ids": missing_ids,
                    "reason": "compiled_manifest_missing_required_pronunciation_rule_metadata",
                }
            )

        for rule in load_rules(lexicon_path):
            if not rule.is_required_alias:
                continue
            if rule.compiled_pattern().search(rendered_text):
                blockers.append(
                    {
                        "job_index": index,
                        "out": job.get("out"),
                        "rule_id": rule.id,
                        "reason": "compiled_elevenlabs_text_still_contains_required_risk_pattern",
                    }
                )

        if expected_required_ids or applied_ids:
            job_reports.append(
                {
                    "job_index": index,
                    "out": job.get("out"),
                    "expected_required_rule_ids": expected_required_ids,
                    "applied_rule_ids": applied_ids,
                    "expected_alias_text": expected_text if expected_text != source_text else "",
                }
            )

    return {
        "lexicon": lexicon_metadata(lexicon_path),
        "job_count": len(jobs),
        "matched_job_count": len(job_reports),
        "jobs": job_reports,
        "blockers": blockers,
    }


def parse_dictionary_locators(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        loaded = json.loads(raw)
        if not isinstance(loaded, list):
            raise ValueError("pronunciation dictionary locators JSON must be a list")
        return [item for item in loaded if isinstance(item, dict)]
    locators: list[dict[str, Any]] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        if ":" in token:
            dictionary_id, version_id = token.split(":", 1)
            locators.append({"pronunciation_dictionary_id": dictionary_id.strip(), "version_id": version_id.strip()})
        else:
            locators.append({"pronunciation_dictionary_id": token})
    return locators


def _print_summary(report: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(
        "pronunciation_preflight: "
        f"jobs={report.get('job_count', 0)} "
        f"matched={report.get('matched_job_count', 0)} "
        f"blockers={len(report.get('blockers', []))}"
    )
    for blocker in report.get("blockers", []):
        print(f"blocker: {json.dumps(blocker, sort_keys=True)}", file=sys.stderr)


def _run_scan(args: argparse.Namespace) -> int:
    report = scan_jobs(read_jsonl(Path(args.manifest)), text_key=args.text_key, lexicon_path=Path(args.lexicon))
    _print_summary(report, json_output=args.json)
    return 1 if report["blockers"] else 0


def _run_verify_compiled(args: argparse.Namespace) -> int:
    report = verify_compiled_jobs(read_jsonl(Path(args.manifest)), lexicon_path=Path(args.lexicon))
    _print_summary(report, json_output=args.json)
    return 1 if report["blockers"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan and verify ElevenLabs pronunciation-risk handling.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_cmd = subparsers.add_parser("scan", help="Scan a source manifest for known pronunciation risks.")
    scan_cmd.add_argument("--manifest", required=True)
    scan_cmd.add_argument("--text-key", default="input")
    scan_cmd.add_argument("--lexicon", default=str(DEFAULT_LEXICON_PATH))
    scan_cmd.add_argument("--json", action="store_true")
    scan_cmd.set_defaults(func=_run_scan)

    verify_cmd = subparsers.add_parser("verify-compiled", help="Verify a compiled ElevenLabs manifest applied required rules.")
    verify_cmd.add_argument("--manifest", required=True)
    verify_cmd.add_argument("--lexicon", default=str(DEFAULT_LEXICON_PATH))
    verify_cmd.add_argument("--json", action="store_true")
    verify_cmd.set_defaults(func=_run_verify_compiled)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
