#!/usr/bin/env python3
"""Build a local fail-closed caption source inventory for the first eight Shorts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")
OUTPUT_ROOT = EPISODES_ROOT / "Shorts_Publish_Readiness"
ASR_SOURCE_MARKERS = (".diarized", "whisperx", "transcripts_mastered", "transcripts_final", "raw_asr")
SCRIPT_LOCKED_MODEL = "script_locked_canonical_text_timing_from_asr_v1"


@dataclass(frozen=True)
class InventoryShort:
    label: str
    slug: str
    configured_locked_text_source_path: Path
    audio_package_path: Path
    candidate_roots: tuple[Path, ...]


SHORTS: tuple[InventoryShort, ...] = (
    InventoryShort(
        "Challenger",
        "challenger",
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/challenger_short_restart_v1_ending_cadence_script.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/selected/audio_package.json"),
        (
            Path("/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts"),
            Path("/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01"),
        ),
    ),
    InventoryShort(
        "Therac-25",
        "therac",
        Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts/therac_short_scoped_v1/therac_short_scoped_v1.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_scoped_v1/audio_package.json"),
        (Path("/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/shorts"),),
    ),
    InventoryShort(
        "Hyatt Regency",
        "hyatt",
        Path("/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/shorts/hyatt_short_scoped_v1/hyatt_short_scoped_v1.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep3_hyatt_regency_short_scoped_v1/audio_package.json"),
        (Path("/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/shorts"),),
    ),
    InventoryShort(
        "Tacoma Narrows",
        "tacoma",
        Path("/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts/tacoma_short_scoped_v1/tacoma_short_scoped_v1.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_short_scoped_v1/audio_package.json"),
        (Path("/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts"),),
    ),
    InventoryShort(
        "Piltdown Man",
        "piltdown",
        Path("/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts/piltdown_man_short_scoped_v1/piltdown_man_short_scoped_v1.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdown_man_short_scoped_v1/audio_package.json"),
        (Path("/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/shorts"),),
    ),
    InventoryShort(
        "737 MAX",
        "737max",
        Path("/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/shorts/737_max_short_scoped_v1/737_max_short_scoped_v1.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_short_scoped_v1/audio_package.json"),
        (Path("/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/shorts"),),
    ),
    InventoryShort(
        "Titanic",
        "titanic",
        Path("/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts/titanic_short_scoped_v1/titanic_short_scoped_v1.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_short_scoped_v1/audio_package.json"),
        (Path("/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/shorts"),),
    ),
    InventoryShort(
        "Semmelweis",
        "semmelweis",
        Path("/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/shorts/semmelweis_short_scoped_v1/semmelweis_short_scoped_v1.txt"),
        Path("/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_short_scoped_v1/audio_package.json"),
        (Path("/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/shorts"),),
    ),
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_looks_asr(path: Path) -> bool:
    token = str(path).lower()
    if "script_locked" in token or "locked_script" in token or "canonical_script" in token:
        return False
    return any(marker in token for marker in ASR_SOURCE_MARKERS)


def words_from_text(text: str) -> list[str]:
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\bSPEAKER_\d+\s*:\s*", " ", text)
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.lower())


def words_from_path(path: Path) -> list[str]:
    if not path.exists():
        return []
    return words_from_text(path.read_text(encoding="utf-8", errors="replace"))


def candidate_paths(short: InventoryShort) -> list[Path]:
    found: set[Path] = set()
    for root in short.candidate_roots:
        if not root.exists():
            continue
        for pattern in ("*.txt", "*.srt"):
            for path in root.rglob(pattern):
                token = str(path).lower()
                if any(part in token for part in ("/publish/", "/final_exports/", "/production/longform")):
                    continue
                if source_looks_asr(path):
                    continue
                if path == short.configured_locked_text_source_path:
                    continue
                found.add(path)
    return sorted(found)


def score_candidate(candidate: Path, timing_text_path: Path) -> dict[str, Any]:
    candidate_words = words_from_path(candidate)
    timing_words = words_from_path(timing_text_path)
    ratio = (
        SequenceMatcher(None, " ".join(candidate_words), " ".join(timing_words)).ratio()
        if candidate_words and timing_words
        else 0.0
    )
    return {
        "path": str(candidate),
        "sha256": sha256(candidate),
        "word_count": len(candidate_words),
        "similarity_to_timing_transcript": round(ratio, 6),
        "candidate_use": "review_candidate_only_not_locked",
    }


def build_inventory(stamp: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for short in SHORTS:
        audio_package = read_json(short.audio_package_path)
        timing_text_path = Path(str(audio_package.get("transcript_path", ""))).expanduser().resolve()
        raw_timing_srt = str(audio_package.get("transcript_srt_path") or audio_package.get("caption_source_path") or "").strip()
        if raw_timing_srt:
            timing_srt_path = Path(raw_timing_srt).expanduser()
        else:
            candidate_srt = timing_text_path.with_suffix(".srt")
            timing_srt_path = candidate_srt if candidate_srt.exists() else timing_text_path
        timing_srt_path = timing_srt_path.resolve()
        locked_path = short.configured_locked_text_source_path.expanduser().resolve()
        locked_exists = locked_path.exists()
        locked_allowed = locked_exists and not source_looks_asr(locked_path)
        candidates = [
            score_candidate(path, timing_text_path)
            for path in candidate_paths(short)
            if path.exists() and path.stat().st_size > 0
        ]
        candidates = sorted(candidates, key=lambda item: item["similarity_to_timing_transcript"], reverse=True)[:8]
        status = "locked_ready" if locked_allowed else ("candidate_review_required" if candidates else "missing_locked_source")
        rows.append(
            {
                "label": short.label,
                "slug": short.slug,
                "source_status": status,
                "can_rebuild_publish_ready": status == "locked_ready",
                "human_script_lock_approval_required": status != "locked_ready",
                "caption_model": SCRIPT_LOCKED_MODEL,
                "configured_locked_text_source_path": str(locked_path),
                "configured_locked_text_source_exists": locked_exists,
                "configured_locked_text_source_sha256": sha256(locked_path) if locked_exists else "",
                "configured_locked_text_source_word_count": len(words_from_path(locked_path)) if locked_exists else 0,
                "timing_text_source_path": str(timing_text_path),
                "timing_text_source_sha256": sha256(timing_text_path) if timing_text_path.exists() else "",
                "timing_text_source_policy": "timing_only_blocked_as_caption_words",
                "timing_srt_source_path": str(timing_srt_path),
                "timing_srt_source_sha256": sha256(timing_srt_path) if timing_srt_path.exists() else "",
                "blocked_as_caption_word_sources": [
                    str(path)
                    for path in (timing_text_path, timing_srt_path)
                    if path.exists() and source_looks_asr(path)
                ],
                "legacy_script_candidates": candidates,
            }
        )
    return {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stamp": stamp,
        "package_type": "shorts_script_locked_caption_source_inventory",
        "caption_model": SCRIPT_LOCKED_MODEL,
        "source_policy": "locked_script_words_asr_timing_only_fail_closed",
        "current_yellow_package_stamp_blocked": "20260521T070556Z",
        "all_sources_locked_ready": all(row["source_status"] == "locked_ready" for row in rows),
        "ready_count": sum(1 for row in rows if row["source_status"] == "locked_ready"),
        "review_required_count": sum(1 for row in rows if row["source_status"] != "locked_ready"),
        "shorts": rows,
        "no_youtube_action": True,
    }


def write_review_note(path: Path, inventory: dict[str, Any]) -> None:
    lines = [
        "# Script-Locked Caption Source Inventory",
        "",
        f"- Stamp: `{inventory['stamp']}`",
        f"- Caption model: `{inventory['caption_model']}`",
        f"- Ready: `{inventory['ready_count']}/8`",
        f"- Review required: `{inventory['review_required_count']}/8`",
        "- YouTube action: none",
        "",
        "## Per-Short Status",
        "",
    ]
    for row in inventory["shorts"]:
        lines.extend(
            [
                f"### {row['label']}",
                "",
                f"- Status: `{row['source_status']}`",
                f"- Configured locked text: `{row['configured_locked_text_source_path']}`",
                f"- Timing evidence: `{row['timing_text_source_path']}`",
                f"- Human script-lock approval required: `{row['human_script_lock_approval_required']}`",
            ]
        )
        if row["legacy_script_candidates"]:
            lines.append("- Candidate scripts for review:")
            for candidate in row["legacy_script_candidates"][:5]:
                lines.append(
                    f"  - `{candidate['path']}` "
                    f"(similarity `{candidate['similarity_to_timing_transcript']}`)"
                )
        else:
            lines.append("- Candidate scripts for review: none found locally")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def make_symlink(target: Path, link: Path) -> None:
    if link.is_symlink() or link.exists():
        if link.is_dir() and not link.is_symlink():
            raise RuntimeError(f"Refusing to replace non-symlink directory: {link}")
        link.unlink()
    link.symlink_to(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stamp", default=utc_stamp())
    args = parser.parse_args()
    package_dir = OUTPUT_ROOT / f"script_locked_caption_source_inventory_{args.stamp}"
    package_dir.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory(args.stamp)
    inventory_path = package_dir / "caption_source_inventory.json"
    review_path = package_dir / "caption_source_inventory_review.md"
    write_json(inventory_path, inventory)
    write_review_note(review_path, inventory)
    make_symlink(package_dir, OUTPUT_ROOT / "script_locked_caption_source_inventory_latest")
    print(json.dumps({"inventory_path": str(inventory_path), "review_path": str(review_path), "all_sources_locked_ready": inventory["all_sources_locked_ready"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
