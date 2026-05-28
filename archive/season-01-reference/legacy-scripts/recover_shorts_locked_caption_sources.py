#!/usr/bin/env python3
"""Recover Shorts locked caption text from approved TTS generation manifests.

The recovered text is the text sent to ElevenLabs for the approved voice audio.
It is allowed as caption wording provenance because it is generation input, not
ASR/WhisperX output. ASR remains timing-only evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_ROOT = Path("/Users/mike/Episodes_CascadeEffects/Shorts_Publish_Readiness")
SCRIPT_LOCKED_POLICY = "script_locked_text_recovered_from_approved_tts_generation_manifest_v1"
CAPTION_MODEL = "script_locked_canonical_text_timing_from_asr_v1"


@dataclass(frozen=True)
class AudioSource:
    slug: str
    label: str
    audio_package: Path
    canonical_script_path: Path | None = None


SOURCES: tuple[AudioSource, ...] = (
    AudioSource(
        slug="challenger",
        label="Challenger",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/selected/audio_package.json"),
        canonical_script_path=Path(
            "/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_ending_cadence_pass_01/"
            "challenger_short_restart_v1_ending_cadence_script.txt"
        ),
    ),
    AudioSource(
        slug="therac",
        label="Therac-25",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep2_therac25_short_scoped_v1/audio_package.json"),
    ),
    AudioSource(
        slug="hyatt",
        label="Hyatt Regency",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep3_hyatt_regency_short_scoped_v1/audio_package.json"),
    ),
    AudioSource(
        slug="tacoma",
        label="Tacoma Narrows",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_short_scoped_v1/audio_package.json"),
    ),
    AudioSource(
        slug="piltdown",
        label="Piltdown Man",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdown_man_short_scoped_v1/audio_package.json"),
    ),
    AudioSource(
        slug="737max",
        label="737 MAX",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_short_scoped_v1/audio_package.json"),
    ),
    AudioSource(
        slug="titanic",
        label="Titanic",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_short_scoped_v1/audio_package.json"),
    ),
    AudioSource(
        slug="semmelweis",
        label="Semmelweis",
        audio_package=Path("/Users/mike/Audio_CascadeEffects/tmp/ep4_semmelweis_short_scoped_v1/audio_package.json"),
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_symlink(target: Path, link: Path) -> None:
    if link.is_symlink() or link.exists():
        if link.is_dir() and not link.is_symlink():
            raise RuntimeError(f"Refusing to replace non-symlink directory: {link}")
        link.unlink()
    link.symlink_to(target)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSONL record") from exc
    if not records:
        raise ValueError(f"{path}: no JSONL records found")
    return records


def extract_tts_text(records: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    chunks: list[str] = []
    evidence: list[dict[str, Any]] = []
    for index, record in enumerate(records, 1):
        text_field = ""
        text = ""
        for candidate in ("spoken_input", "elevenlabs_text", "input"):
            value = record.get(candidate)
            if isinstance(value, str) and value.strip():
                text_field = candidate
                text = value.strip()
                break
        if not text:
            raise ValueError(f"Record {index} has no usable TTS text field")
        chunks.append(text)
        evidence.append(
            {
                "record_index": index,
                "text_field_used": text_field,
                "out": record.get("out", ""),
                "voice": record.get("voice", ""),
                "elevenlabs_model_id": record.get("elevenlabs_model_id", ""),
                "elevenlabs_seed": record.get("elevenlabs_seed", ""),
            }
        )
    return "\n\n".join(chunks).strip() + "\n", evidence


def word_count(text: str) -> int:
    import re

    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text))


def build_package(stamp: str) -> Path:
    package_dir = OUTPUT_ROOT / f"script_locked_caption_sources_{stamp}"
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest_sources: dict[str, Any] = {}

    for source in SOURCES:
        audio_package = read_json(source.audio_package)
        effective_manifest = Path(str(audio_package["effective_manifest_path"])).expanduser().resolve()
        if source.canonical_script_path is not None:
            text_path = source.canonical_script_path.expanduser().resolve()
            if not text_path.exists():
                raise FileNotFoundError(f"{source.label}: missing canonical script source {text_path}")
            status = "existing_canonical_locked_script"
            text_source_sha = sha256(text_path)
            extraction_evidence: list[dict[str, Any]] = []
            word_total = word_count(text_path.read_text(encoding="utf-8"))
        else:
            records = read_jsonl(effective_manifest)
            text, extraction_evidence = extract_tts_text(records)
            text_path = package_dir / f"{source.slug}_locked_caption_text_from_tts_manifest.txt"
            text_path.write_text(text, encoding="utf-8")
            status = "recovered_from_approved_tts_generation_manifest"
            text_source_sha = sha256(text_path)
            word_total = word_count(text)

        audio_path = Path(str(audio_package["packaged_path"])).expanduser().resolve()
        timing_transcript_path = Path(str(audio_package["transcript_path"])).expanduser().resolve()
        manifest_sources[source.slug] = {
            "label": source.label,
            "status": status,
            "caption_model": CAPTION_MODEL,
            "caption_text_source_policy": SCRIPT_LOCKED_POLICY,
            "locked_caption_text_source_path": str(text_path),
            "locked_caption_text_source_sha256": text_source_sha,
            "audio_package_path": str(source.audio_package),
            "audio_package_sha256": sha256(source.audio_package),
            "approved_audio_path": str(audio_path),
            "approved_audio_sha256": sha256(audio_path),
            "effective_tts_manifest_path": str(effective_manifest),
            "effective_tts_manifest_sha256": sha256(effective_manifest),
            "timing_source_policy": "asr_whisperx_timing_only",
            "audio_package_transcript_path": str(timing_transcript_path),
            "extraction_evidence": extraction_evidence,
            "human_script_lock_approval_required": False,
            "asr_or_diarized_text_used_as_caption_words": False,
            "word_count": word_total,
        }

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "package_type": "shorts_script_locked_caption_sources",
        "stamp": stamp,
        "caption_model": CAPTION_MODEL,
        "caption_text_source_policy": SCRIPT_LOCKED_POLICY,
        "caption_timing_source_policy": "asr_whisperx_timing_only",
        "source_count": len(manifest_sources),
        "sources": manifest_sources,
        "no_youtube_action": True,
        "public_release_boundary": "manual_youtube_studio_only",
    }
    write_json(package_dir / "locked_caption_sources_manifest.json", manifest)
    review_lines = [
        "# Script-Locked Caption Source Recovery",
        "",
        "Recovered caption word sources from approved TTS generation manifests. ASR/WhisperX remains timing-only evidence.",
        "",
    ]
    for slug, item in manifest_sources.items():
        review_lines.extend(
            [
                f"## {item['label']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Caption text source: `{item['locked_caption_text_source_path']}`",
                f"- Effective TTS manifest: `{item['effective_tts_manifest_path']}`",
                f"- Word count: {item['word_count']}",
                f"- ASR/diarized text used as caption words: `{item['asr_or_diarized_text_used_as_caption_words']}`",
                "",
            ]
        )
    (package_dir / "caption_source_recovery_review.md").write_text("\n".join(review_lines), encoding="utf-8")
    make_symlink(package_dir, OUTPUT_ROOT / "script_locked_caption_sources_latest")
    return package_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stamp", default=utc_stamp())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    package_dir = build_package(args.stamp)
    print(package_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
