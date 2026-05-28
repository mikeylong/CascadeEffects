#!/usr/bin/env python3
"""Compile and render ElevenLabs provider manifests for the audio pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pronunciation_preflight import (  # noqa: E402
    DEFAULT_LEXICON_PATH,
    apply_rules_to_text,
    lexicon_metadata,
    parse_dictionary_locators,
)


DEFAULT_MODEL_ENV_VAR = "ELEVENLABS_DEFAULT_MODEL"
DEFAULT_OUTPUT_FORMAT = "wav_44100"
DEFAULT_CONTINUITY_CHARS = 400
MAX_COMPILED_CHARS = 3000
DEFAULT_STABILITY = 0.6
DEFAULT_SIMILARITY_BOOST = 0.8
DEFAULT_STYLE = 0.0
DEFAULT_USE_SPEAKER_BOOST = True
DEFAULT_SPEED = 1.0

INTENSE_TAGS = {"sorrowful", "frustrated", "nervous", "flatly", "resigned"}
DIGIT_WORDS = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}
PROVIDER_FIELDS = {
    "elevenlabs_text",
    "elevenlabs_previous_text",
    "elevenlabs_next_text",
    "elevenlabs_seed",
    "elevenlabs_voice_id",
    "elevenlabs_model_id",
    "elevenlabs_apply_text_normalization",
    "elevenlabs_voice_settings",
    "elevenlabs_pronunciation_lexicon_path",
    "elevenlabs_pronunciation_lexicon_sha256",
    "elevenlabs_pronunciation_applied_rules",
    "elevenlabs_pronunciation_dictionary_locators",
}


def _model_supports_continuity(model_id: str) -> bool:
    normalized = str(model_id or "").strip().lower()
    if not normalized:
        return True
    return not normalized.startswith("eleven_v3")


def _model_uses_inline_tags(model_id: str) -> bool:
    return str(model_id or "").strip().lower().startswith("eleven_v3")


@dataclass
class SourceParagraph:
    tag: str
    text: str
    normalized: str


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def _read_jobs_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        _die(f"Manifest not found: {path}")
    jobs: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            _die(f"{path}:{line_no}: invalid JSON ({exc})")
        if not isinstance(item, dict):
            _die(f"{path}:{line_no}: expected object")
        jobs.append(item)
    if not jobs:
        _die(f"No jobs found in {path}")
    return jobs


def _write_jobs_jsonl(path: Path, jobs: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.dumps(job, ensure_ascii=False) for job in jobs]
    path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def _normalize_alignment_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.replace("\u2019", "'").replace("\u2018", "'")
    value = value.replace("\u2014", " ").replace("\u2013", " ")
    value = value.lower()
    tokens = re.findall(r"[a-z0-9']+", value)
    return " ".join(token.strip("'") for token in tokens if token.strip("'"))


def _strip_tag_prefix(text: str) -> tuple[str | None, str]:
    match = re.match(r"^\[([^]]+)\]\s*(.+)$", text.strip())
    if not match:
        return None, text.strip()
    return match.group(1).strip().lower(), match.group(2).strip()


def _parse_source_script(path: Path) -> list[SourceParagraph]:
    rows: list[SourceParagraph] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        tag, text = _strip_tag_prefix(line)
        if not tag:
            _die(f"{path}:{line_no}: expected cue-tagged source line")
        rows.append(SourceParagraph(tag=tag, text=text, normalized=_normalize_alignment_text(text)))
    if not rows:
        _die(f"No cue-tagged lines found in {path}")
    return rows


def _normalized_prefix_length(source: str, fragment: str) -> int | None:
    fragment_norm = _normalize_alignment_text(fragment)
    if not fragment_norm:
        return 0
    source_norm = _normalize_alignment_text(source)
    if not source_norm.startswith(fragment_norm):
        return None
    for index in range(1, len(source) + 1):
        if _normalize_alignment_text(source[:index]) == fragment_norm:
            return index
    return None


def _consume_source_fragment(
    *,
    source_rows: list[SourceParagraph],
    row_index: int,
    row_char_offset: int,
    paragraph_text: str,
    strict_source_alignment: bool,
    jobs_path: Path,
    job_index: int,
    out_name: str,
    paragraph_index: int,
) -> tuple[SourceParagraph | None, int, int]:
    if row_index >= len(source_rows):
        if strict_source_alignment:
            _die(f"{jobs_path}: job {job_index} ({out_name}): source script exhausted during alignment")
        return None, row_index, row_char_offset

    row = source_rows[row_index]
    remaining_raw = row.text[row_char_offset:]
    trimmed_remaining = remaining_raw.lstrip()
    trimmed_offset = row_char_offset + (len(remaining_raw) - len(trimmed_remaining))
    fragment = paragraph_text.strip()
    consumed_len: int | None = None

    if trimmed_remaining.startswith(fragment):
        consumed_len = len(fragment)
    else:
        consumed_len = _normalized_prefix_length(trimmed_remaining, fragment)

    if consumed_len is None:
        if strict_source_alignment:
            preview = fragment[:120].replace("\n", " ")
            _die(
                f"{jobs_path}: job {job_index} ({out_name}), paragraph {paragraph_index}: "
                f"could not align '{preview}' to source tag stream"
            )
        return None, row_index, row_char_offset

    new_offset = trimmed_offset + consumed_len
    next_row_index = row_index
    next_row_char_offset = new_offset
    if new_offset >= len(row.text):
        next_row_index += 1
        next_row_char_offset = 0

    return (
        SourceParagraph(
            tag=row.tag,
            text=fragment,
            normalized=_normalize_alignment_text(fragment),
        ),
        next_row_index,
        next_row_char_offset,
    )


def _job_input(job: dict[str, Any]) -> str:
    value = job.get("input")
    if not isinstance(value, str) or not value.strip():
        _die("Job missing non-empty input")
    return value.strip()


def _split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]


def _sentences(text: str) -> list[str]:
    pattern = re.compile(r".+?(?:[.!?]+(?:[\"'”’)\]]*)|$)", re.S)
    parts = []
    for match in pattern.finditer(text.strip()):
        chunk = match.group(0).strip()
        if chunk:
            parts.append(chunk)
    return parts or ([text.strip()] if text.strip() else [])


def _decimal_to_words(match: re.Match[str]) -> str:
    whole, fraction = match.group(1), match.group(2)
    whole_words = " ".join(DIGIT_WORDS[digit] for digit in whole) if len(whole) == 1 else whole
    fraction_words = " ".join(DIGIT_WORDS[digit] for digit in fraction)
    return f"{whole_words} point {fraction_words}"


def _degree_value_replacement(match: re.Match[str]) -> str:
    value = match.group(1)
    unit = (match.group(2) or "").strip().lower()
    if unit in {"f", "fahrenheit"}:
        return f"{value} degrees Fahrenheit"
    if unit in {"c", "celsius"}:
        return f"{value} degrees Celsius"
    return f"{value} degrees"


def normalize_spoken_text(text: str) -> str:
    normalized = text
    normalized = re.sub(
        r"\b(\d+)\s*°\s*([FCfc])\b",
        _degree_value_replacement,
        normalized,
    )
    normalized = re.sub(
        r"\b(\d+)\s+degrees?\s+([FCfc]|fahrenheit|celsius)\b",
        _degree_value_replacement,
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"\b(\d+)\s*°\b", _degree_value_replacement, normalized)
    normalized = re.sub(
        r"\b(\d{1,2}:\d{2})\s*(a\.m\.|p\.m\.)(?=\W|$)",
        lambda match: f"{match.group(1)} {'AM' if match.group(2).lower().startswith('a') else 'PM'}",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"\b(\d+)\.(\d+)\b", _decimal_to_words, normalized)
    return normalized


def _frustration_tag(text: str) -> str:
    lowered = text.lower()
    if "?" in text or "—" in text or "--" in text:
        return "[frustrated sigh]"
    if any(phrase in lowered for phrase in ("unsafe", "wrong", "pressure", "pushed back", "can you prove")):
        return "[frustrated sigh]"
    return "[frustrated]"


def _should_emit_calm(previous_tag: str | None, is_first_in_chunk: bool) -> bool:
    return is_first_in_chunk or previous_tag in INTENSE_TAGS


def _apply_pause_strategy(text: str) -> str:
    parts = _sentences(text)
    if len(parts) <= 1:
        return f"[short pause] {text}"
    return f"{parts[0]} [pause] {' '.join(parts[1:])}"


def _render_prefix(tag: str, text: str, previous_tag: str | None, is_first_in_chunk: bool) -> str | None:
    if tag == "calm":
        return "[calm]" if _should_emit_calm(previous_tag, is_first_in_chunk) else None
    if tag == "sorrowful":
        return "[sorrowful]"
    if tag == "frustrated":
        return _frustration_tag(text)
    if tag == "nervous":
        return "[nervous]"
    if tag == "flatly":
        return "[flatly]"
    if tag == "resigned":
        return "[resigned tone]"
    return None


def compile_tagged_paragraph(
    paragraph: SourceParagraph,
    *,
    previous_tag: str | None,
    is_first_in_chunk: bool,
    use_inline_tags: bool,
) -> tuple[str, str]:
    spoken = normalize_spoken_text(paragraph.text)
    if not use_inline_tags:
        return spoken, spoken
    if paragraph.tag == "pauses":
        return _apply_pause_strategy(spoken), spoken
    prefix = _render_prefix(paragraph.tag, spoken, previous_tag, is_first_in_chunk)
    if prefix:
        return f"{prefix} {spoken}", spoken
    return spoken, spoken


def _generic_render_text(text: str) -> tuple[str, str]:
    spoken = normalize_spoken_text(text)
    return spoken, spoken


def _stable_seed(job: dict[str, Any]) -> int:
    key = f"{job.get('out', '')}\n{job.get('input', '')}"
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _clamp_speed(value: float | int | None) -> float:
    if value is None:
        return DEFAULT_SPEED
    speed = float(value)
    if speed < 0.7:
        return 0.7
    if speed > 1.2:
        return 1.2
    return round(speed, 3)


def _default_voice_settings(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "stability": DEFAULT_STABILITY,
        "similarity_boost": DEFAULT_SIMILARITY_BOOST,
        "style": DEFAULT_STYLE,
        "use_speaker_boost": DEFAULT_USE_SPEAKER_BOOST,
        "speed": _clamp_speed(job.get("speed")),
    }


def _pronunciation_lexicon_path() -> Path:
    return Path(os.getenv("ELEVENLABS_PRONUNCIATION_LEXICON") or DEFAULT_LEXICON_PATH)


def _pronunciation_dictionary_locators() -> list[dict[str, Any]]:
    raw = os.getenv("ELEVENLABS_PRONUNCIATION_DICTIONARY_LOCATORS", "")
    if not raw.strip():
        return []
    return parse_dictionary_locators(raw)


def compile_manifest(
    *,
    jobs_path: Path,
    output_path: Path,
    script_path: Path | None,
    strict_source_alignment: bool,
    model_id: str,
    continuity_chars: int,
) -> list[dict[str, Any]]:
    jobs = _read_jobs_jsonl(jobs_path)
    source_rows = _parse_source_script(script_path) if script_path else []
    use_inline_tags = _model_uses_inline_tags(model_id)
    pronunciation_lexicon_path = _pronunciation_lexicon_path()
    pronunciation_lexicon = lexicon_metadata(pronunciation_lexicon_path)
    pronunciation_dictionary_locators = _pronunciation_dictionary_locators()
    row_index = 0
    row_char_offset = 0
    compiled_jobs: list[dict[str, Any]] = []

    for job_index, job in enumerate(jobs, start=1):
        input_text = _job_input(job)
        render_paragraphs: list[str] = []
        spoken_paragraphs: list[str] = []
        previous_tag: str | None = None
        matched_source = False

        if source_rows:
            paragraphs = _split_paragraphs(input_text)
            matched_rows: list[SourceParagraph] = []
            scan_row_index = row_index
            scan_row_char_offset = row_char_offset
            for para_index, paragraph_text in enumerate(paragraphs, start=1):
                matched_row, scan_row_index, scan_row_char_offset = _consume_source_fragment(
                    source_rows=source_rows,
                    row_index=scan_row_index,
                    row_char_offset=scan_row_char_offset,
                    paragraph_text=paragraph_text,
                    strict_source_alignment=strict_source_alignment,
                    jobs_path=jobs_path,
                    job_index=job_index,
                    out_name=str(job.get("out")),
                    paragraph_index=para_index,
                )
                if matched_row is None:
                    matched_rows = []
                    break
                matched_rows.append(matched_row)
            if matched_rows:
                matched_source = True
                row_index = scan_row_index
                row_char_offset = scan_row_char_offset
                for para_index, row in enumerate(matched_rows):
                    render_text, spoken_text = compile_tagged_paragraph(
                        row,
                        previous_tag=previous_tag,
                        is_first_in_chunk=para_index == 0,
                        use_inline_tags=use_inline_tags,
                    )
                    render_paragraphs.append(render_text)
                    spoken_paragraphs.append(spoken_text)
                    previous_tag = row.tag

        if not matched_source:
            generic_render, generic_spoken = _generic_render_text(input_text)
            render_paragraphs = [generic_render]
            spoken_paragraphs = [generic_spoken]

        render_text = "\n\n".join(render_paragraphs).strip()
        spoken_text = "\n\n".join(spoken_paragraphs).strip()
        render_text, pronunciation_applied_rules = apply_rules_to_text(
            render_text,
            lexicon_path=pronunciation_lexicon_path,
        )
        if len(render_text) > MAX_COMPILED_CHARS:
            _die(
                f"{jobs_path}: job {job_index} ({job.get('out')}): compiled ElevenLabs text exceeds "
                f"{MAX_COMPILED_CHARS} chars ({len(render_text)})"
            )

        compiled = dict(job)
        compiled["spoken_input"] = spoken_text
        compiled["elevenlabs_text"] = render_text
        compiled["elevenlabs_seed"] = _stable_seed(job)
        compiled["elevenlabs_model_id"] = model_id
        compiled["elevenlabs_apply_text_normalization"] = "on"
        compiled["elevenlabs_voice_settings"] = _default_voice_settings(job)
        compiled["elevenlabs_pronunciation_lexicon_path"] = pronunciation_lexicon["path"]
        compiled["elevenlabs_pronunciation_lexicon_sha256"] = pronunciation_lexicon["sha256"]
        compiled["elevenlabs_pronunciation_applied_rules"] = pronunciation_applied_rules
        if pronunciation_dictionary_locators:
            compiled["elevenlabs_pronunciation_dictionary_locators"] = pronunciation_dictionary_locators
        compiled_jobs.append(compiled)

    continuity_enabled = continuity_chars > 0 and _model_supports_continuity(model_id)
    if continuity_enabled:
        for index, compiled in enumerate(compiled_jobs):
            previous_text = ""
            next_text = ""
            if index > 0:
                previous_text = str(compiled_jobs[index - 1]["elevenlabs_text"])[-continuity_chars:]
            if index + 1 < len(compiled_jobs):
                next_text = str(compiled_jobs[index + 1]["elevenlabs_text"])[:continuity_chars]
            if previous_text:
                compiled["elevenlabs_previous_text"] = previous_text
            if next_text:
                compiled["elevenlabs_next_text"] = next_text

    _write_jobs_jsonl(output_path, compiled_jobs)
    return compiled_jobs


def _normalize_output_path(out_dir: Path, job: dict[str, Any]) -> Path:
    raw = str(job.get("out") or "").strip()
    if not raw:
        _die("Job missing out filename")
    out_path = Path(raw)
    if out_path.is_absolute():
        return out_dir / out_path.name
    return out_dir / out_path


def _ensure_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        _die(f"{var_name} is not set")
    return value


def _resolve_model(explicit_model: str | None) -> str:
    model = str(explicit_model or os.getenv(DEFAULT_MODEL_ENV_VAR) or "").strip()
    if not model:
        _die(f"{DEFAULT_MODEL_ENV_VAR} is not set; provide --model or export the env var")
    return model


def _pick_request_id(headers: dict[str, str]) -> str | None:
    for key in ("request-id", "x-request-id", "xi-request-id"):
        value = headers.get(key)
        if value:
            return value
    return None


def _read_headers(path: Path) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not path.exists():
        return headers
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def _resolve_api_ip() -> str | None:
    env_ip = os.getenv("ELEVEN_LABS_API_IP")
    if env_ip:
        return env_ip.strip()
    if shutil.which("dig") is None:
        return None
    proc = subprocess.run(
        ["dig", "+short", "api.elevenlabs.io", "@1.1.1.1"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return None
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if line:
            return line
    return None


def _curl_request(
    *,
    url: str,
    payload: dict[str, Any],
    output_path: Path,
    headers_path: Path,
    api_key: str,
    output_format: str,
) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False)
        handle.flush()
        payload_path = Path(handle.name)

    def run_with(api_ip: str | None) -> subprocess.CompletedProcess[str]:
        cmd = [
            "curl",
            "-sS",
            "-D",
            str(headers_path),
            "-o",
            str(output_path),
            "-w",
            "%{http_code}",
            "-X",
            "POST",
            url,
            "-H",
            f"xi-api-key: {api_key}",
            "-H",
            "Content-Type: application/json",
            "-H",
            "Accept: audio/wav",
            "--data-binary",
            f"@{payload_path}",
        ]
        if api_ip:
            cmd.extend(["--resolve", f"api.elevenlabs.io:443:{api_ip}"])
        return subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    try:
        proc = run_with(None)
        if proc.returncode == 6 and "Could not resolve host" in proc.stderr:
            api_ip = _resolve_api_ip()
            if api_ip:
                proc = run_with(api_ip)
        if proc.returncode != 0:
            return 0, proc.stderr.strip() or f"curl failed with code {proc.returncode}"
        try:
            http_code = int(proc.stdout.strip())
        except ValueError:
            return 0, f"Unexpected HTTP status output: {proc.stdout!r}"
        return http_code, ""
    finally:
        payload_path.unlink(missing_ok=True)


def render_batch(
    *,
    jobs_path: Path,
    out_dir: Path,
    model_id: str,
    voice_id: str,
    output_format: str,
    dry_run: bool,
    force: bool,
) -> int:
    if not output_format.startswith("wav_"):
        _die(f"ELEVENLABS output format must be WAV-based (got {output_format})")

    jobs = _read_jobs_jsonl(jobs_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    api_key = ""
    if not dry_run:
        api_key = _ensure_env("ELEVEN_LABS_API_KEY")

    for job in jobs:
        out_path = _normalize_output_path(out_dir, job)
        metadata_path = out_path.with_suffix(out_path.suffix + ".json")
        if out_path.exists() and not force and not dry_run:
            _die(f"Output already exists: {out_path} (use --force to overwrite)")

        text = str(job.get("elevenlabs_text") or job.get("input") or "").strip()
        if not text:
            _die(f"Job missing ElevenLabs text: {job.get('out')}")
        if len(text) > MAX_COMPILED_CHARS:
            _die(f"Job {job.get('out')} exceeds ElevenLabs cap with {len(text)} chars")

        job_model_id = str(job.get("elevenlabs_model_id") or model_id)
        payload: dict[str, Any] = {
            "text": text,
            "model_id": job_model_id,
            "apply_text_normalization": str(job.get("elevenlabs_apply_text_normalization") or "on"),
            "seed": int(job.get("elevenlabs_seed") or _stable_seed(job)),
        }
        voice_settings = job.get("elevenlabs_voice_settings")
        if isinstance(voice_settings, dict):
            payload["voice_settings"] = voice_settings
        dictionary_locators = job.get("elevenlabs_pronunciation_dictionary_locators")
        if isinstance(dictionary_locators, list) and dictionary_locators:
            payload["pronunciation_dictionary_locators"] = dictionary_locators
        previous_text = ""
        next_text = ""
        if _model_supports_continuity(job_model_id):
            previous_text = str(job.get("elevenlabs_previous_text") or "").strip()
            next_text = str(job.get("elevenlabs_next_text") or "").strip()
            if previous_text:
                payload["previous_text"] = previous_text
            if next_text:
                payload["next_text"] = next_text

        if dry_run:
            print(json.dumps(payload, indent=2, sort_keys=True))
            print(f"Would write {out_path}")
            continue

        headers_path = out_path.with_suffix(out_path.suffix + ".headers")
        http_code, error = _curl_request(
            url=f"https://api.elevenlabs.io/v1/text-to-speech/{job.get('elevenlabs_voice_id') or voice_id}?output_format={output_format}",
            payload=payload,
            output_path=out_path,
            headers_path=headers_path,
            api_key=api_key,
            output_format=output_format,
        )
        if http_code != 200:
            detail = ""
            if out_path.exists():
                try:
                    detail = out_path.read_text(encoding="utf-8", errors="ignore")[:500]
                except Exception:
                    detail = ""
                out_path.unlink(missing_ok=True)
            headers_path.unlink(missing_ok=True)
            _die(
                f"ElevenLabs request failed for {job.get('out')} "
                f"(HTTP {http_code or 'n/a'}): {error or detail or 'unknown error'}"
            )

        headers = _read_headers(headers_path)
        request_id = _pick_request_id(headers)
        metadata = {
            "out": job.get("out"),
            "audio_path": str(out_path),
            "spoken_input": job.get("spoken_input") or job.get("input"),
            "rendered_text": text,
            "previous_text": previous_text or None,
            "next_text": next_text or None,
            "seed": payload["seed"],
            "voice_id": job.get("elevenlabs_voice_id") or voice_id,
            "model_id": payload["model_id"],
            "request_id": request_id,
            "pronunciation_lexicon_path": job.get("elevenlabs_pronunciation_lexicon_path"),
            "pronunciation_lexicon_sha256": job.get("elevenlabs_pronunciation_lexicon_sha256"),
            "pronunciation_applied_rules": job.get("elevenlabs_pronunciation_applied_rules") or [],
            "pronunciation_dictionary_locators": dictionary_locators if isinstance(dictionary_locators, list) else [],
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        headers_path.unlink(missing_ok=True)
        print(f"Wrote {out_path}")

    return 0


def _run_compile_manifest(args: argparse.Namespace) -> int:
    model_id = _resolve_model(args.model)
    compile_manifest(
        jobs_path=Path(args.input),
        output_path=Path(args.output),
        script_path=Path(args.script_path) if args.script_path else None,
        strict_source_alignment=args.strict_source_alignment,
        model_id=model_id,
        continuity_chars=args.continuity_chars,
    )
    print(f"Wrote {args.output}")
    return 0


def _run_render_batch(args: argparse.Namespace) -> int:
    model_id = _resolve_model(args.model)
    voice_id = args.voice_id or os.getenv("ELEVEN_LABS_VOICE_ID")
    if not voice_id:
        _die("ELEVEN_LABS_VOICE_ID is not set; provide --voice-id or export the env var")
    output_format = args.output_format or os.getenv("ELEVENLABS_OUTPUT_FORMAT") or DEFAULT_OUTPUT_FORMAT
    return render_batch(
        jobs_path=Path(args.input),
        out_dir=Path(args.out_dir),
        model_id=model_id,
        voice_id=voice_id,
        output_format=output_format,
        dry_run=args.dry_run,
        force=args.force,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile and render ElevenLabs manifests for the audio pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_cmd = subparsers.add_parser("compile-manifest", help="Compile a JSONL manifest for ElevenLabs TTS.")
    compile_cmd.add_argument("--input", required=True)
    compile_cmd.add_argument("--output", required=True)
    compile_cmd.add_argument("--script-path")
    compile_cmd.add_argument("--strict-source-alignment", action="store_true")
    compile_cmd.add_argument("--model")
    compile_cmd.add_argument("--continuity-chars", type=int, default=DEFAULT_CONTINUITY_CHARS)
    compile_cmd.set_defaults(func=_run_compile_manifest)

    render_cmd = subparsers.add_parser("render-batch", help="Render a compiled JSONL manifest through ElevenLabs.")
    render_cmd.add_argument("--input", required=True)
    render_cmd.add_argument("--out-dir", required=True)
    render_cmd.add_argument("--model")
    render_cmd.add_argument("--voice-id")
    render_cmd.add_argument("--output-format", default=None)
    render_cmd.add_argument("--dry-run", action="store_true")
    render_cmd.add_argument("--force", action="store_true")
    render_cmd.set_defaults(func=_run_render_batch)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
