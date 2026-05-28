#!/usr/bin/env python3
"""Manage ElevenLabs Professional Voice Clone samples and training."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "voice_profiles.toml"
DEFAULT_ENV_FILE = ROOT_DIR / ".env.local"
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_SAMPLE_EXTENSIONS = (".wav",)


@dataclass(frozen=True)
class VoiceProfile:
    name: str
    voice_id: str
    category: str
    language: str
    description: str
    sample_extensions: tuple[str, ...]
    target_training_models: tuple[str, ...]
    render_settings: dict[str, Any]
    sample_defaults: dict[str, Any]


@dataclass(frozen=True)
class LocalSample:
    path: Path
    file_name: str
    sha256: str
    size_bytes: int


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def load_env_file_if_present(path: Path | None) -> None:
    if path is None or not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


def _ensure_api_key() -> str:
    api_key = str(os.getenv("ELEVEN_LABS_API_KEY") or "").strip()
    if not api_key:
        _die("ELEVEN_LABS_API_KEY is not set; export it or provide a readable .env.local")
    return api_key


def _load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _die(f"File not found: {path}")
    except json.JSONDecodeError as exc:
        _die(f"{path}: invalid JSON ({exc})")


def _normalize_bool(value: Any, *, field: str, path: Path | None = None) -> bool:
    if isinstance(value, bool):
        return value
    location = f"{path}: " if path else ""
    _die(f"{location}{field} must be a boolean")


def _normalize_non_negative_int(value: Any, *, field: str, path: Path | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        location = f"{path}: " if path else ""
        _die(f"{location}{field} must be a non-negative integer")
    return value


def load_voice_profile(config_path: Path, voice_name: str) -> VoiceProfile:
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _die(f"Voice profile config not found: {config_path}")
    except tomllib.TOMLDecodeError as exc:
        _die(f"{config_path}: invalid TOML ({exc})")

    voices = config.get("voices")
    if not isinstance(voices, dict):
        _die(f"{config_path}: expected [voices.<name>] tables")
    raw_profile = voices.get(voice_name)
    if not isinstance(raw_profile, dict):
        _die(f"{config_path}: missing voice profile `{voice_name}`")

    voice_id = str(raw_profile.get("voice_id") or "").strip()
    if not voice_id:
        _die(f"{config_path}: voices.{voice_name}.voice_id is required")
    category = str(raw_profile.get("category") or "").strip() or "professional"
    language = str(raw_profile.get("language") or "").strip() or "en"
    description = str(raw_profile.get("description") or "").strip()

    sample_extensions = raw_profile.get("sample_extensions") or list(DEFAULT_SAMPLE_EXTENSIONS)
    if not isinstance(sample_extensions, list) or not sample_extensions:
        _die(f"{config_path}: voices.{voice_name}.sample_extensions must be a non-empty list")
    normalized_extensions: list[str] = []
    for item in sample_extensions:
        if not isinstance(item, str) or not item.strip():
            _die(f"{config_path}: voices.{voice_name}.sample_extensions entries must be non-empty strings")
        extension = item.strip().lower()
        if not extension.startswith("."):
            extension = f".{extension}"
        normalized_extensions.append(extension)

    raw_target_models = raw_profile.get("target_training_models") or []
    if not isinstance(raw_target_models, list):
        _die(f"{config_path}: voices.{voice_name}.target_training_models must be a list")
    target_training_models: list[str] = []
    for item in raw_target_models:
        if not isinstance(item, str) or not item.strip():
            _die(f"{config_path}: voices.{voice_name}.target_training_models entries must be non-empty strings")
        target_training_models.append(item.strip())

    render_settings = raw_profile.get("render_settings") or {}
    if not isinstance(render_settings, dict):
        _die(f"{config_path}: voices.{voice_name}.render_settings must be a table")
    sample_defaults = raw_profile.get("sample_defaults") or {}
    if not isinstance(sample_defaults, dict):
        _die(f"{config_path}: voices.{voice_name}.sample_defaults must be a table")

    return VoiceProfile(
        name=voice_name,
        voice_id=voice_id,
        category=category,
        language=language,
        description=description,
        sample_extensions=tuple(normalized_extensions),
        target_training_models=tuple(target_training_models),
        render_settings=dict(render_settings),
        sample_defaults=dict(sample_defaults),
    )


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


def _pick_request_id(headers: dict[str, str]) -> str | None:
    for key in ("request-id", "x-request-id", "xi-request-id"):
        value = headers.get(key)
        if value:
            return value
    return None


def _curl_request(
    *,
    method: str,
    url: str,
    api_key: str,
    json_payload: dict[str, Any] | None = None,
    form_fields: list[tuple[str, str]] | None = None,
    file_fields: list[tuple[str, Path]] | None = None,
) -> tuple[int, str, dict[str, str], str]:
    payload_path: Path | None = None
    with tempfile.NamedTemporaryFile("w+", suffix=".headers", encoding="utf-8", delete=False) as headers_handle:
        headers_path = Path(headers_handle.name)
    with tempfile.NamedTemporaryFile("w+", suffix=".body", encoding="utf-8", delete=False) as body_handle:
        body_path = Path(body_handle.name)

    if json_payload is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as payload_handle:
            json.dump(json_payload, payload_handle, ensure_ascii=False)
            payload_handle.flush()
            payload_path = Path(payload_handle.name)

    def run_with(api_ip: str | None) -> subprocess.CompletedProcess[str]:
        cmd = [
            "curl",
            "-sS",
            "-D",
            str(headers_path),
            "-o",
            str(body_path),
            "-w",
            "%{http_code}",
            "-X",
            method.upper(),
            url,
            "-H",
            f"xi-api-key: {api_key}",
        ]
        if json_payload is not None and payload_path is not None:
            cmd.extend(
                [
                    "-H",
                    "Content-Type: application/json",
                    "--data-binary",
                    f"@{payload_path}",
                ]
            )
        if form_fields:
            for field_name, field_value in form_fields:
                cmd.extend(["-F", f"{field_name}={field_value}"])
        if file_fields:
            for field_name, field_path in file_fields:
                cmd.extend(["-F", f"{field_name}=@{field_path}"])
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
            return 0, "", {}, proc.stderr.strip() or f"curl failed with code {proc.returncode}"
        try:
            http_code = int(proc.stdout.strip())
        except ValueError:
            return 0, "", {}, f"Unexpected HTTP status output: {proc.stdout!r}"
        body_text = body_path.read_text(encoding="utf-8", errors="ignore")
        headers = _read_headers(headers_path)
        return http_code, body_text, headers, ""
    finally:
        headers_path.unlink(missing_ok=True)
        body_path.unlink(missing_ok=True)
        if payload_path is not None:
            payload_path.unlink(missing_ok=True)


def _decode_response_body(body_text: str) -> Any:
    if not body_text.strip():
        return None
    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        return body_text.strip()


def _request_json(
    *,
    method: str,
    url: str,
    api_key: str,
    json_payload: dict[str, Any] | None = None,
    form_fields: list[tuple[str, str]] | None = None,
    file_fields: list[tuple[str, Path]] | None = None,
    expected_statuses: tuple[int, ...] = (200,),
) -> tuple[Any, dict[str, str]]:
    http_code, body_text, headers, error = _curl_request(
        method=method,
        url=url,
        api_key=api_key,
        json_payload=json_payload,
        form_fields=form_fields,
        file_fields=file_fields,
    )
    if http_code not in expected_statuses:
        detail = error or _decode_response_body(body_text)
        detail_text = detail if isinstance(detail, str) else json.dumps(detail, sort_keys=True)
        request_id = _pick_request_id(headers)
        request_suffix = f" request_id={request_id}" if request_id else ""
        _die(f"ElevenLabs request failed ({method} {url} -> HTTP {http_code or 'n/a'}{request_suffix}): {detail_text}")
    return _decode_response_body(body_text), headers


def fetch_voice(voice_id: str, api_key: str) -> dict[str, Any]:
    payload, _ = _request_json(
        method="GET",
        url=f"{ELEVENLABS_API_BASE}/voices/{voice_id}",
        api_key=api_key,
    )
    if not isinstance(payload, dict):
        _die(f"Expected voice object for {voice_id}")
    return payload


def upload_sample(
    *,
    voice_id: str,
    sample_path: Path,
    remove_background_noise: bool,
    api_key: str,
) -> dict[str, Any]:
    payload, _ = _request_json(
        method="POST",
        url=f"{ELEVENLABS_API_BASE}/voices/pvc/{voice_id}/samples",
        api_key=api_key,
        form_fields=[("remove_background_noise", str(remove_background_noise).lower())],
        file_fields=[("files", sample_path)],
        expected_statuses=(200,),
    )
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        _die(f"Unexpected sample upload response for {sample_path.name}")
    return payload[0]


def update_sample(
    *,
    voice_id: str,
    sample_id: str,
    payload: dict[str, Any],
    api_key: str,
) -> dict[str, Any]:
    response, _ = _request_json(
        method="POST",
        url=f"{ELEVENLABS_API_BASE}/voices/pvc/{voice_id}/samples/{sample_id}",
        api_key=api_key,
        json_payload=payload,
        expected_statuses=(200,),
    )
    if response is None:
        return {}
    if not isinstance(response, dict):
        _die(f"Unexpected sample update response for sample {sample_id}")
    return response


def start_speaker_separation(*, voice_id: str, sample_id: str, api_key: str) -> dict[str, Any]:
    response, _ = _request_json(
        method="POST",
        url=f"{ELEVENLABS_API_BASE}/voices/pvc/{voice_id}/samples/{sample_id}/speaker-separation",
        api_key=api_key,
        expected_statuses=(200,),
    )
    if response is None:
        return {}
    if not isinstance(response, dict):
        _die(f"Unexpected speaker separation response for sample {sample_id}")
    return response


def train_voice(*, voice_id: str, model_id: str, api_key: str) -> dict[str, Any]:
    response, _ = _request_json(
        method="POST",
        url=f"{ELEVENLABS_API_BASE}/voices/pvc/{voice_id}/train",
        api_key=api_key,
        json_payload={"model_id": model_id},
        expected_statuses=(200,),
    )
    if response is None:
        return {}
    if not isinstance(response, dict):
        _die(f"Unexpected training response for {voice_id} model {model_id}")
    return response


def _voice_samples(voice_payload: dict[str, Any]) -> list[dict[str, Any]]:
    samples = voice_payload.get("samples") or []
    return [sample for sample in samples if isinstance(sample, dict)]


def _fine_tuning_state(voice_payload: dict[str, Any]) -> dict[str, str]:
    fine_tuning = voice_payload.get("fine_tuning") or {}
    state = fine_tuning.get("state") or {}
    return {str(key): str(value) for key, value in state.items()}


def _settings_drift(local_settings: dict[str, Any], remote_settings: dict[str, Any]) -> dict[str, dict[str, Any]]:
    drift: dict[str, dict[str, Any]] = {}
    for key in sorted(set(local_settings) | set(remote_settings)):
        local_value = local_settings.get(key)
        remote_value = remote_settings.get(key)
        if local_value != remote_value:
            drift[key] = {"local": local_value, "remote": remote_value}
    return drift


def build_status_payload(profile: VoiceProfile, voice_payload: dict[str, Any]) -> dict[str, Any]:
    samples = _voice_samples(voice_payload)
    fine_tuning_state = _fine_tuning_state(voice_payload)
    remote_settings = voice_payload.get("settings") or {}
    if not isinstance(remote_settings, dict):
        remote_settings = {}
    missing_training_models = [
        model_id
        for model_id in profile.target_training_models
        if fine_tuning_state.get(model_id) != "fine_tuned"
    ]
    return {
        "voice": profile.name,
        "voice_id": str(voice_payload.get("voice_id") or profile.voice_id),
        "category": str(voice_payload.get("category") or profile.category),
        "sample_count": len(samples),
        "total_sample_seconds": round(
            sum(float(sample.get("duration_secs") or 0.0) for sample in samples),
            3,
        ),
        "fine_tuning_state": fine_tuning_state,
        "remote_voice_settings": remote_settings,
        "local_profile_settings": dict(profile.render_settings),
        "settings_drift": _settings_drift(profile.render_settings, remote_settings),
        "missing_training_models": missing_training_models,
        "samples": [
            {
                "sample_id": sample.get("sample_id"),
                "file_name": sample.get("file_name"),
                "hash": sample.get("hash"),
                "duration_secs": sample.get("duration_secs"),
                "remove_background_noise": sample.get("remove_background_noise"),
                "trim_start": sample.get("trim_start"),
                "trim_end": sample.get("trim_end"),
                "speaker_separation": sample.get("speaker_separation"),
            }
            for sample in samples
        ],
    }


def _print_status(payload: dict[str, Any]) -> None:
    print(f"Voice: {payload['voice']}")
    print(f"Voice ID: {payload['voice_id']}")
    print(f"Category: {payload['category']}")
    print(f"Sample count: {payload['sample_count']}")
    print(f"Total sample seconds: {payload['total_sample_seconds']}")
    missing_models = payload.get("missing_training_models") or []
    if missing_models:
        print("Missing training models:")
        for model_id in missing_models:
            print(f"  - {model_id}")
    else:
        print("Missing training models: none")
    print("Fine-tuning state:")
    fine_tuning_state = payload.get("fine_tuning_state") or {}
    for model_id in sorted(fine_tuning_state):
        print(f"  - {model_id}: {fine_tuning_state[model_id]}")
    print("Remote voice settings:")
    for key, value in sorted((payload.get("remote_voice_settings") or {}).items()):
        print(f"  - {key}: {value}")
    print("Local profile settings:")
    for key, value in sorted((payload.get("local_profile_settings") or {}).items()):
        print(f"  - {key}: {value}")
    settings_drift = payload.get("settings_drift") or {}
    if settings_drift:
        print("Settings drift:")
        for key, values in sorted(settings_drift.items()):
            print(f"  - {key}: local={values.get('local')} remote={values.get('remote')}")
    print("Samples:")
    for sample in payload.get("samples") or []:
        print(
            "  - "
            f"{sample.get('file_name')} "
            f"(id={sample.get('sample_id')}, "
            f"seconds={sample.get('duration_secs')}, "
            f"remove_background_noise={sample.get('remove_background_noise')})"
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_local_samples(samples_dir: Path, *, extensions: tuple[str, ...]) -> list[LocalSample]:
    if not samples_dir.exists() or not samples_dir.is_dir():
        _die(f"samples-dir does not exist or is not a directory: {samples_dir}")
    discovered: list[LocalSample] = []
    for path in sorted(samples_dir.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        discovered.append(
            LocalSample(
                path=path,
                file_name=path.name,
                sha256=_sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    if not discovered:
        _die(f"No curated sample files found under {samples_dir} matching {', '.join(extensions)}")
    return discovered


def _normalize_speaker_separation(value: Any, *, file_name: str, manifest_path: Path) -> dict[str, Any] | None:
    if value in (None, False):
        return None
    if value is True:
        return {"start": True, "selected_speaker_ids": None}
    if isinstance(value, list):
        selected_speaker_ids: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                _die(f"{manifest_path}: {file_name}.speaker_separation entries must be non-empty strings")
            selected_speaker_ids.append(item.strip())
        if not selected_speaker_ids:
            _die(f"{manifest_path}: {file_name}.speaker_separation must not be an empty list")
        return {"start": True, "selected_speaker_ids": selected_speaker_ids}
    if isinstance(value, dict):
        start = bool(value.get("start", False))
        selected_raw = value.get("selected_speaker_ids", value.get("speakers"))
        selected_speaker_ids: list[str] | None = None
        if selected_raw is not None:
            if not isinstance(selected_raw, list) or not selected_raw:
                _die(
                    f"{manifest_path}: {file_name}.speaker_separation.selected_speaker_ids "
                    "must be a non-empty list"
                )
            selected_speaker_ids = []
            for item in selected_raw:
                if not isinstance(item, str) or not item.strip():
                    _die(
                        f"{manifest_path}: {file_name}.speaker_separation.selected_speaker_ids "
                        "entries must be non-empty strings"
                    )
                selected_speaker_ids.append(item.strip())
            start = True
        if not start and selected_speaker_ids is None:
            _die(
                f"{manifest_path}: {file_name}.speaker_separation must set start=true or provide "
                "selected_speaker_ids"
            )
        return {"start": start, "selected_speaker_ids": selected_speaker_ids}
    _die(
        f"{manifest_path}: {file_name}.speaker_separation must be a boolean, list of speaker ids, "
        "or an object"
    )


def load_sample_manifest(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    payload = _load_json_file(path)
    if not isinstance(payload, dict):
        _die(f"{path}: sample manifest must be a JSON object keyed by filename")
    normalized: dict[str, dict[str, Any]] = {}
    for raw_file_name, raw_entry in payload.items():
        if not isinstance(raw_file_name, str) or not raw_file_name.strip():
            _die(f"{path}: sample manifest keys must be non-empty strings")
        file_name = raw_file_name.strip()
        if not isinstance(raw_entry, dict):
            _die(f"{path}: sample manifest entry for {file_name} must be an object")
        entry: dict[str, Any] = {}
        if "remove_background_noise" in raw_entry:
            entry["remove_background_noise"] = _normalize_bool(
                raw_entry["remove_background_noise"],
                field=f"{file_name}.remove_background_noise",
                path=path,
            )
        if "trim_start" in raw_entry:
            entry["trim_start"] = _normalize_non_negative_int(
                raw_entry["trim_start"],
                field=f"{file_name}.trim_start",
                path=path,
            )
        if "trim_end" in raw_entry:
            entry["trim_end"] = _normalize_non_negative_int(
                raw_entry["trim_end"],
                field=f"{file_name}.trim_end",
                path=path,
            )
        if "trim_start" in entry and "trim_end" in entry and entry["trim_end"] < entry["trim_start"]:
            _die(f"{path}: {file_name}.trim_end must be greater than or equal to trim_start")
        if "speaker_separation" in raw_entry:
            entry["speaker_separation"] = _normalize_speaker_separation(
                raw_entry["speaker_separation"],
                file_name=file_name,
                manifest_path=path,
            )
        if "notes" in raw_entry:
            notes = raw_entry["notes"]
            if not isinstance(notes, str):
                _die(f"{path}: {file_name}.notes must be a string")
            entry["notes"] = notes
        normalized[file_name] = entry
    return normalized


def _sample_default_remove_background_noise(profile: VoiceProfile) -> bool | None:
    if "remove_background_noise" not in profile.sample_defaults:
        return None
    return _normalize_bool(
        profile.sample_defaults["remove_background_noise"],
        field=f"{profile.name}.sample_defaults.remove_background_noise",
    )


def _desired_remove_background_noise(
    profile: VoiceProfile,
    manifest_entry: dict[str, Any],
) -> bool | None:
    if "remove_background_noise" in manifest_entry:
        return manifest_entry["remove_background_noise"]
    return _sample_default_remove_background_noise(profile)


def _speaker_separation_status(sample_payload: dict[str, Any]) -> str:
    speaker = sample_payload.get("speaker_separation")
    if isinstance(speaker, dict):
        status = str(speaker.get("status") or "").strip()
        if status:
            return status
    return "not_started"


def _selected_speaker_ids(sample_payload: dict[str, Any]) -> list[str]:
    speaker = sample_payload.get("speaker_separation")
    if not isinstance(speaker, dict):
        return []
    selected = speaker.get("selected_speaker_ids") or []
    if not isinstance(selected, list):
        return []
    return [str(item).strip() for item in selected if str(item).strip()]


def build_training_model_list(
    profile: VoiceProfile,
    fine_tuning_state: dict[str, str],
    *,
    explicit_model: str | None,
    all_missing: bool,
) -> list[str]:
    if explicit_model and all_missing:
        _die("Use either --model or --all-missing, not both")
    if explicit_model:
        return [explicit_model]
    if all_missing or not explicit_model:
        return [
            model_id
            for model_id in profile.target_training_models
            if fine_tuning_state.get(model_id) != "fine_tuned"
        ]
    return []


def _find_remote_sample(
    local_sample: LocalSample,
    remote_by_hash: dict[str, dict[str, Any]],
    remote_by_name: dict[str, dict[str, Any]],
    warnings: list[str],
) -> tuple[dict[str, Any] | None, str | None]:
    hash_match = remote_by_hash.get(local_sample.sha256)
    if hash_match is not None:
        return hash_match, "hash"
    name_match = remote_by_name.get(local_sample.file_name)
    if name_match is not None:
        remote_hash = str(name_match.get("hash") or "").strip()
        if remote_hash and remote_hash != local_sample.sha256:
            warnings.append(
                f"{local_sample.file_name}: remote sample hash differs; "
                "using filename fallback and skipping duplicate upload"
            )
        return name_match, "filename"
    return None, None


def _build_sample_update_payload(
    *,
    profile: VoiceProfile,
    sample_payload: dict[str, Any],
    manifest_entry: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    payload: dict[str, Any] = {}
    desired_remove_background_noise = _desired_remove_background_noise(profile, manifest_entry)
    current_remove_background_noise = sample_payload.get("remove_background_noise")
    if (
        desired_remove_background_noise is not None
        and current_remove_background_noise is not desired_remove_background_noise
    ):
        payload["remove_background_noise"] = desired_remove_background_noise

    if "trim_start" in manifest_entry and sample_payload.get("trim_start") != manifest_entry["trim_start"]:
        payload["trim_start_time"] = manifest_entry["trim_start"]
    if "trim_end" in manifest_entry and sample_payload.get("trim_end") != manifest_entry["trim_end"]:
        payload["trim_end_time"] = manifest_entry["trim_end"]

    return payload, manifest_entry.get("speaker_separation")


def sync_samples(
    *,
    profile: VoiceProfile,
    samples_dir: Path,
    sample_manifest: dict[str, dict[str, Any]],
    dry_run: bool,
    api_key: str,
) -> dict[str, Any]:
    voice_payload = fetch_voice(profile.voice_id, api_key)
    remote_samples = _voice_samples(voice_payload)
    local_samples = collect_local_samples(samples_dir, extensions=profile.sample_extensions)
    warnings: list[str] = []
    remote_by_hash = {
        str(sample.get("hash") or "").strip(): sample
        for sample in remote_samples
        if str(sample.get("hash") or "").strip()
    }
    remote_by_name = {
        str(sample.get("file_name") or "").strip(): sample
        for sample in remote_samples
        if str(sample.get("file_name") or "").strip()
    }

    for file_name in sorted(sample_manifest):
        if not any(sample.file_name == file_name for sample in local_samples):
            warnings.append(f"{file_name}: manifest entry has no matching local curated WAV")

    report: dict[str, Any] = {
        "voice": profile.name,
        "voice_id": profile.voice_id,
        "remote_sample_count_before": len(remote_samples),
        "local_sample_count": len(local_samples),
        "dry_run": dry_run,
        "uploaded": [],
        "matched_by_hash": [],
        "matched_by_filename": [],
        "updated": [],
        "speaker_separation_started": [],
        "warnings": warnings,
    }

    for local_sample in local_samples:
        manifest_entry = sample_manifest.get(local_sample.file_name, {})
        remote_sample, match_reason = _find_remote_sample(local_sample, remote_by_hash, remote_by_name, warnings)

        if remote_sample is None:
            desired_remove_background_noise = _desired_remove_background_noise(profile, manifest_entry)
            upload_remove_background_noise = bool(desired_remove_background_noise) if desired_remove_background_noise is not None else False
            if dry_run:
                remote_sample = {
                    "sample_id": "(pending upload)",
                    "file_name": local_sample.file_name,
                    "hash": local_sample.sha256,
                    "remove_background_noise": upload_remove_background_noise,
                    "trim_start": None,
                    "trim_end": None,
                }
                report["uploaded"].append(
                    {
                        "file_name": local_sample.file_name,
                        "dry_run": True,
                        "remove_background_noise": upload_remove_background_noise,
                    }
                )
            else:
                remote_sample = upload_sample(
                    voice_id=profile.voice_id,
                    sample_path=local_sample.path,
                    remove_background_noise=upload_remove_background_noise,
                    api_key=api_key,
                )
                report["uploaded"].append(
                    {
                        "file_name": local_sample.file_name,
                        "sample_id": remote_sample.get("sample_id"),
                        "remove_background_noise": upload_remove_background_noise,
                    }
                )
            remote_by_hash[local_sample.sha256] = remote_sample
            remote_by_name[local_sample.file_name] = remote_sample
        elif match_reason == "hash":
            report["matched_by_hash"].append(local_sample.file_name)
        else:
            report["matched_by_filename"].append(local_sample.file_name)

        update_payload, speaker_config = _build_sample_update_payload(
            profile=profile,
            sample_payload=remote_sample,
            manifest_entry=manifest_entry,
        )

        sample_id = str(remote_sample.get("sample_id") or "").strip()
        if update_payload:
            if not sample_id:
                _die(f"{local_sample.file_name}: missing sample_id for update")
            if dry_run:
                report["updated"].append(
                    {
                        "file_name": local_sample.file_name,
                        "sample_id": sample_id,
                        "payload": update_payload,
                        "dry_run": True,
                    }
                )
            else:
                update_sample(
                    voice_id=profile.voice_id,
                    sample_id=sample_id,
                    payload=update_payload,
                    api_key=api_key,
                )
                report["updated"].append(
                    {
                        "file_name": local_sample.file_name,
                        "sample_id": sample_id,
                        "payload": update_payload,
                    }
                )
                if "remove_background_noise" in update_payload:
                    remote_sample["remove_background_noise"] = update_payload["remove_background_noise"]
                if "trim_start_time" in update_payload:
                    remote_sample["trim_start"] = update_payload["trim_start_time"]
                if "trim_end_time" in update_payload:
                    remote_sample["trim_end"] = update_payload["trim_end_time"]

        if speaker_config:
            status = _speaker_separation_status(remote_sample)
            selected_speaker_ids = list(speaker_config.get("selected_speaker_ids") or [])
            if speaker_config.get("start") and status == "not_started":
                if not sample_id:
                    _die(f"{local_sample.file_name}: missing sample_id for speaker separation")
                if dry_run:
                    report["speaker_separation_started"].append(
                        {
                            "file_name": local_sample.file_name,
                            "sample_id": sample_id,
                            "dry_run": True,
                        }
                    )
                else:
                    start_speaker_separation(
                        voice_id=profile.voice_id,
                        sample_id=sample_id,
                        api_key=api_key,
                    )
                    report["speaker_separation_started"].append(
                        {
                            "file_name": local_sample.file_name,
                            "sample_id": sample_id,
                        }
                    )
                    remote_sample["speaker_separation"] = {"status": "pending"}
                    status = "pending"
            if selected_speaker_ids:
                if status != "completed":
                    if dry_run:
                        warnings.append(
                            f"{local_sample.file_name}: selected_speaker_ids requested but speaker separation "
                            f"is {status}; rerun after separation completes"
                        )
                    else:
                        _die(
                            f"{local_sample.file_name}: selected_speaker_ids require completed speaker separation "
                            f"(current status: {status})"
                        )
                elif _selected_speaker_ids(remote_sample) != selected_speaker_ids:
                    speaker_payload = {"selected_speaker_ids": selected_speaker_ids}
                    if dry_run:
                        report["updated"].append(
                            {
                                "file_name": local_sample.file_name,
                                "sample_id": sample_id,
                                "payload": speaker_payload,
                                "dry_run": True,
                            }
                        )
                    else:
                        update_sample(
                            voice_id=profile.voice_id,
                            sample_id=sample_id,
                            payload=speaker_payload,
                            api_key=api_key,
                        )
                        report["updated"].append(
                            {
                                "file_name": local_sample.file_name,
                                "sample_id": sample_id,
                                "payload": speaker_payload,
                            }
                        )

    report["warnings"] = warnings
    return report


def _print_sync_report(report: dict[str, Any]) -> None:
    print(f"Voice: {report['voice']} ({report['voice_id']})")
    print(f"Dry run: {report['dry_run']}")
    print(f"Remote samples before sync: {report['remote_sample_count_before']}")
    print(f"Local curated samples: {report['local_sample_count']}")
    print(f"Uploaded: {len(report['uploaded'])}")
    for item in report.get("uploaded", []):
        suffix = " [dry-run]" if item.get("dry_run") else ""
        print(f"  - {item['file_name']}{suffix}")
    print(f"Matched by hash: {len(report['matched_by_hash'])}")
    for file_name in report.get("matched_by_hash", []):
        print(f"  - {file_name}")
    print(f"Matched by filename: {len(report['matched_by_filename'])}")
    for file_name in report.get("matched_by_filename", []):
        print(f"  - {file_name}")
    print(f"Updated: {len(report['updated'])}")
    for item in report.get("updated", []):
        suffix = " [dry-run]" if item.get("dry_run") else ""
        print(f"  - {item['file_name']}: {json.dumps(item['payload'], sort_keys=True)}{suffix}")
    print(f"Speaker separation started: {len(report['speaker_separation_started'])}")
    for item in report.get("speaker_separation_started", []):
        suffix = " [dry-run]" if item.get("dry_run") else ""
        print(f"  - {item['file_name']}{suffix}")
    warnings = report.get("warnings") or []
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")


def run_training(
    *,
    profile: VoiceProfile,
    explicit_model: str | None,
    all_missing: bool,
    dry_run: bool,
    api_key: str,
) -> dict[str, Any]:
    voice_payload = fetch_voice(profile.voice_id, api_key)
    fine_tuning_state = _fine_tuning_state(voice_payload)
    selected_models = build_training_model_list(
        profile,
        fine_tuning_state,
        explicit_model=explicit_model,
        all_missing=all_missing,
    )
    report = {
        "voice": profile.name,
        "voice_id": profile.voice_id,
        "dry_run": dry_run,
        "requested": selected_models,
        "started": [],
        "skipped_already_fine_tuned": [],
    }
    for model_id in selected_models:
        current_state = fine_tuning_state.get(model_id)
        if current_state == "fine_tuned":
            report["skipped_already_fine_tuned"].append(model_id)
            continue
        if dry_run:
            report["started"].append({"model_id": model_id, "dry_run": True})
            continue
        train_voice(
            voice_id=profile.voice_id,
            model_id=model_id,
            api_key=api_key,
        )
        report["started"].append({"model_id": model_id})
    return report


def _print_training_report(report: dict[str, Any]) -> None:
    print(f"Voice: {report['voice']} ({report['voice_id']})")
    print(f"Dry run: {report['dry_run']}")
    requested = report.get("requested") or []
    if requested:
        print("Requested models:")
        for model_id in requested:
            print(f"  - {model_id}")
    else:
        print("Requested models: none")
    skipped = report.get("skipped_already_fine_tuned") or []
    if skipped:
        print("Skipped already fine-tuned models:")
        for model_id in skipped:
            print(f"  - {model_id}")
    started = report.get("started") or []
    if started:
        print("Training started:")
        for item in started:
            suffix = " [dry-run]" if item.get("dry_run") else ""
            print(f"  - {item['model_id']}{suffix}")
    elif not skipped:
        print("Training started: none")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage ElevenLabs PVC samples and model training.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to voice_profiles.toml.")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env.local file to load before reading ELEVEN_LABS_API_KEY.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_cmd = subparsers.add_parser("status", help="Inspect a configured PVC voice profile.")
    status_cmd.add_argument("--voice", required=True, help="Voice profile name from config/voice_profiles.toml.")
    status_cmd.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    status_cmd.set_defaults(func=_run_status)

    sync_cmd = subparsers.add_parser("sync-samples", help="Sync curated local WAV samples into a PVC voice.")
    sync_cmd.add_argument("--voice", required=True, help="Voice profile name from config/voice_profiles.toml.")
    sync_cmd.add_argument("--samples-dir", required=True, help="Directory containing curated local WAV samples.")
    sync_cmd.add_argument("--sample-manifest", help="Optional JSON manifest keyed by filename.")
    sync_cmd.add_argument("--dry-run", action="store_true", help="Report the sync plan without mutating remote samples.")
    sync_cmd.set_defaults(func=_run_sync_samples)

    train_cmd = subparsers.add_parser("train", help="Start PVC training for configured missing models.")
    train_cmd.add_argument("--voice", required=True, help="Voice profile name from config/voice_profiles.toml.")
    train_cmd.add_argument("--model", help="Train a specific model id.")
    train_cmd.add_argument("--all-missing", action="store_true", help="Train every configured target model that is not yet fine_tuned.")
    train_cmd.add_argument("--dry-run", action="store_true", help="Report the training plan without starting jobs.")
    train_cmd.set_defaults(func=_run_train)

    return parser


def _run_status(args: argparse.Namespace) -> int:
    load_env_file_if_present(Path(args.env_file) if args.env_file else None)
    api_key = _ensure_api_key()
    profile = load_voice_profile(Path(args.config), args.voice)
    payload = build_status_payload(profile, fetch_voice(profile.voice_id, api_key))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_status(payload)
    return 0


def _run_sync_samples(args: argparse.Namespace) -> int:
    load_env_file_if_present(Path(args.env_file) if args.env_file else None)
    api_key = _ensure_api_key()
    profile = load_voice_profile(Path(args.config), args.voice)
    sample_manifest = load_sample_manifest(Path(args.sample_manifest) if args.sample_manifest else None)
    report = sync_samples(
        profile=profile,
        samples_dir=Path(args.samples_dir),
        sample_manifest=sample_manifest,
        dry_run=args.dry_run,
        api_key=api_key,
    )
    _print_sync_report(report)
    return 0


def _run_train(args: argparse.Namespace) -> int:
    load_env_file_if_present(Path(args.env_file) if args.env_file else None)
    api_key = _ensure_api_key()
    profile = load_voice_profile(Path(args.config), args.voice)
    report = run_training(
        profile=profile,
        explicit_model=args.model,
        all_missing=args.all_missing,
        dry_run=args.dry_run,
        api_key=api_key,
    )
    _print_training_report(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
