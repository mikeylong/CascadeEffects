from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from orchestration.io import Context

ACTIVE_SHORT_PROFILE_ID = "youtube_shorts_mike_challenger_match_v1"
DEFAULT_REGISTRY_RELATIVE_PATH = Path("references/shorts/audio_lane_registry.json")
DEFAULT_HISTORICAL_PROOF_ANNOTATIONS_RELATIVE_PATH = Path(
    "references/shorts/historical_proof_audio_provenance_annotations.json"
)
DEFAULT_REPORT_RELATIVE_PATH = Path("state/shorts_audio_audit.json")
REQUIRED_MANIFEST_PROVENANCE_FIELDS = {
    "short_audio_package_path",
    "expected_voice_profile_id",
    "audio_package_sha256",
    "audio_disposition",
    "caption_source_path",
    "transcript_sha256",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_disposition(value: Any) -> str:
    return " ".join(str(value or "").replace("-", " ").split()).strip().lower()


def normalize_path_token(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return str(Path(raw).expanduser().resolve(strict=False))


def default_registry_path(context: Context) -> Path:
    return context.root / DEFAULT_REGISTRY_RELATIVE_PATH


def load_registry(context: Context, registry_path: Path | None = None) -> dict[str, Any]:
    path = (registry_path or default_registry_path(context)).expanduser().resolve()
    payload = read_json(path)
    payload["_registry_path"] = str(path)
    return payload


def load_voice_profiles(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profile_path = Path(str(registry.get("voice_profiles_path", ""))).expanduser().resolve()
    payload = read_json(profile_path)
    profiles = payload.get("profiles", {})
    if not isinstance(profiles, dict):
        return {}
    return {str(profile_id): profile for profile_id, profile in profiles.items() if isinstance(profile, dict)}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def default_historical_proof_annotations_path(context: Context) -> Path:
    return context.root / DEFAULT_HISTORICAL_PROOF_ANNOTATIONS_RELATIVE_PATH


def load_historical_proof_annotations(context: Context) -> dict[str, dict[str, Any]]:
    path = default_historical_proof_annotations_path(context)
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except json.JSONDecodeError:
        return {}
    annotations = payload.get("annotations", [])
    if not isinstance(annotations, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for annotation in annotations:
        if not isinstance(annotation, dict):
            continue
        proof_path = normalize_path_token(annotation.get("proof_manifest_path"))
        if proof_path:
            indexed[proof_path] = annotation
    return indexed


def effective_job_settings(package_payload: dict[str, Any]) -> dict[str, Any]:
    effective_path = Path(str(package_payload.get("effective_manifest_path", ""))).expanduser()
    if not effective_path.exists():
        return {}
    for raw_line in effective_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
        except json.JSONDecodeError:
            return {}
        if not isinstance(job, dict):
            return {}
        voice_settings = job.get("elevenlabs_voice_settings")
        if not isinstance(voice_settings, dict):
            voice_settings = job.get("voice_settings") if isinstance(job.get("voice_settings"), dict) else {}
        speed = job.get("speed")
        if speed is None and isinstance(voice_settings, dict):
            speed = voice_settings.get("speed")
        return {
            "model": str(job.get("elevenlabs_model_id", "")).strip(),
            "speed": speed,
            "voice_settings": voice_settings if isinstance(voice_settings, dict) else {},
        }
    return {}


def _record(result: dict[str, Any], severity: str, code: str, message: str, *, path: str = "") -> None:
    result.setdefault(severity, []).append({"code": code, "message": message, "path": path})


def validate_lane_package(lane: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "lane_id": str(lane.get("lane_id", "")),
        "episode_id": str(lane.get("episode_id", "")),
        "short_id": str(lane.get("short_id", "")),
        "lane_type": str(lane.get("lane_type", "")),
        "status": str(lane.get("status", "")),
        "errors": [],
        "warnings": [],
        "resolved": {},
    }
    package_path_text = str(lane.get("short_audio_package_path", "")).strip()
    if not package_path_text:
        if str(lane.get("status", "")) == "no_short_audio_package_yet":
            result["resolved"]["future_short_stub"] = True
            return result
        _record(result, "errors", "missing_audio_package_path", "Lane has no short_audio_package_path.")
        return result

    package_path = Path(package_path_text).expanduser().resolve()
    result["resolved"]["short_audio_package_path"] = str(package_path)
    if not package_path.exists():
        _record(result, "errors", "missing_audio_package", "Audio package metadata is missing.", path=str(package_path))
        return result

    try:
        package_payload = read_json(package_path)
    except json.JSONDecodeError as exc:
        _record(result, "errors", "invalid_audio_package_json", f"Audio package JSON is invalid: {exc}", path=str(package_path))
        return result

    package_sha = sha256_path(package_path)
    result["resolved"]["audio_package_sha256"] = package_sha
    expected_package_sha = str(lane.get("audio_package_sha256", "")).strip()
    if expected_package_sha and package_sha != expected_package_sha:
        _record(result, "errors", "audio_package_sha256_mismatch", "audio_package.json digest does not match registry.", path=str(package_path))

    expected_profile_id = str(lane.get("expected_voice_profile_id", "")).strip()
    package_profile_id = str(package_payload.get("voice_profile_id", "")).strip()
    if package_profile_id and expected_profile_id and package_profile_id != expected_profile_id:
        _record(
            result,
            "errors",
            "voice_profile_id_mismatch",
            f"Audio package voice_profile_id `{package_profile_id}` does not match registry `{expected_profile_id}`.",
            path=str(package_path),
        )
    profile = profiles.get(expected_profile_id)
    if not profile:
        _record(result, "errors", "unknown_voice_profile", f"Unknown expected_voice_profile_id `{expected_profile_id}`.")
    else:
        for field in ("provider", "voice", "model"):
            actual = str(package_payload.get(field, "")).strip()
            expected = str(profile.get(field, "")).strip()
            if actual != expected:
                _record(
                    result,
                    "errors",
                    f"{field}_mismatch",
                    f"Audio package {field} `{actual or 'unset'}` does not match profile `{expected_profile_id}` `{expected}`.",
                    path=str(package_path),
                )
        lane_type = str(lane.get("lane_type", "")).strip()
        allowed_lane_types = profile.get("allowed_lane_types", [])
        if isinstance(allowed_lane_types, list) and lane_type not in {str(item) for item in allowed_lane_types}:
            _record(
                result,
                "errors",
                "profile_lane_type_mismatch",
                f"Profile `{expected_profile_id}` is not allowed for lane_type `{lane_type}`.",
            )
        if bool(lane.get("final_export_eligible", False)) and not bool(profile.get("final_export_eligible", False)):
            _record(result, "errors", "profile_not_final_export_eligible", f"Profile `{expected_profile_id}` cannot produce keeper Shorts finals.")
        settings = effective_job_settings(package_payload)
        expected_speed = profile.get("render_settings", {}).get("speed") if isinstance(profile.get("render_settings"), dict) else None
        actual_speed = settings.get("speed")
        if expected_speed is not None and actual_speed is not None and abs(float(actual_speed) - float(expected_speed)) > 0.001:
            _record(
                result,
                "errors",
                "speed_mismatch",
                f"Recorded speed `{actual_speed}` does not match profile `{expected_profile_id}` speed `{expected_speed}`.",
                path=str(package_payload.get("effective_manifest_path", "")),
            )
        elif expected_speed is not None and actual_speed is None and str(package_payload.get("provider", "")).strip() == "elevenlabs":
            result["resolved"]["profile_speed_recorded"] = False
            result["resolved"]["profile_speed_note"] = "Future packages must snapshot profile settings."

    audio_path = Path(str(package_payload.get("packaged_path", ""))).expanduser()
    if not audio_path.exists():
        _record(result, "errors", "missing_packaged_audio", "Packaged short WAV is missing.", path=str(audio_path))
    else:
        packaged_sha = sha256_path(audio_path)
        result["resolved"]["packaged_audio_sha256"] = packaged_sha
        expected_packaged_sha = str(package_payload.get("packaged_sha256", "")).strip()
        if expected_packaged_sha and packaged_sha != expected_packaged_sha:
            _record(result, "errors", "packaged_audio_sha256_mismatch", "Packaged WAV digest does not match audio_package.json.", path=str(audio_path))
        registry_packaged_sha = str(lane.get("packaged_audio_sha256", "")).strip()
        if registry_packaged_sha and packaged_sha != registry_packaged_sha:
            _record(result, "errors", "registry_packaged_audio_sha256_mismatch", "Packaged WAV digest does not match registry.", path=str(audio_path))

    transcript_path = Path(str(package_payload.get("transcript_path", ""))).expanduser()
    if not transcript_path.exists():
        _record(result, "errors", "missing_transcript", "QA transcript is missing.", path=str(transcript_path))
    else:
        transcript_sha = sha256_path(transcript_path)
        result["resolved"]["transcript_sha256"] = transcript_sha
        expected_transcript_sha = str(package_payload.get("transcript_sha256", "")).strip()
        if expected_transcript_sha and transcript_sha != expected_transcript_sha:
            _record(result, "errors", "transcript_sha256_mismatch", "Transcript digest does not match audio_package.json.", path=str(transcript_path))
        registry_transcript_sha = str(lane.get("transcript_sha256", "")).strip()
        if registry_transcript_sha and transcript_sha != registry_transcript_sha:
            _record(result, "errors", "registry_transcript_sha256_mismatch", "Transcript digest does not match registry.", path=str(transcript_path))

    expected_disposition = normalize_disposition(lane.get("audio_disposition"))
    package_disposition = normalize_disposition(package_payload.get("disposition")) or expected_disposition
    if expected_disposition and package_disposition != expected_disposition:
        _record(result, "errors", "audio_disposition_mismatch", f"Package disposition `{package_disposition}` does not match registry `{expected_disposition}`.", path=str(package_path))

    if bool(lane.get("final_export_eligible", False)) and expected_disposition != "keep":
        _record(result, "errors", "final_export_requires_keep_audio", "Final-export-eligible lanes must have keep audio.")
    if str(lane.get("lane_type", "")) == "long_form" and bool(lane.get("final_export_eligible", False)):
        _record(result, "errors", "longform_final_export_eligible", "Long-form audio cannot be Shorts final-export eligible.")
    return result


def _select_lane(lanes: list[Any], lane_key: str) -> dict[str, Any]:
    key = str(lane_key or "").strip()
    if not key:
        raise SystemExit("Lane id or short id is required.")
    exact = [
        lane
        for lane in lanes
        if isinstance(lane, dict) and str(lane.get("lane_id", "")).strip() == key
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise SystemExit(f"Multiple lanes matched lane_id `{key}`.")
    short_matches = [
        lane
        for lane in lanes
        if isinstance(lane, dict) and str(lane.get("short_id", "")).strip() == key
    ]
    if len(short_matches) == 1:
        return short_matches[0]
    if len(short_matches) > 1:
        matching_ids = ", ".join(str(lane.get("lane_id", "")) for lane in short_matches)
        raise SystemExit(f"Short id `{key}` matched multiple lanes: {matching_ids}")
    raise SystemExit(f"No Shorts audio lane matched `{key}`.")


def _required_package_file(package_payload: dict[str, Any], field: str, package_path: Path) -> Path:
    value = str(package_payload.get(field, "")).strip()
    if not value:
        raise SystemExit(f"{package_path}: missing required `{field}`.")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"{package_path}: `{field}` does not exist: {path}")
    return path


def _write_registry_payload(registry_path: Path, registry: dict[str, Any]) -> None:
    payload = {key: value for key, value in registry.items() if key != "_registry_path"}
    write_json(registry_path, payload)


def _sync_manifest_audio_provenance(
    manifest_path: Path,
    *,
    package_path: Path,
    expected_profile_id: str,
    audio_disposition: str,
    package_sha: str,
    packaged_path: Path,
    packaged_sha: str,
    transcript_path: Path,
    transcript_sha: str,
) -> bool:
    payload = read_json(manifest_path)
    before = json.dumps(payload, sort_keys=True)
    payload.update(
        {
            "audio_path": str(packaged_path),
            "short_audio_package_path": str(package_path),
            "expected_voice_profile_id": expected_profile_id,
            "audio_package_sha256": package_sha,
            "packaged_audio_sha256": packaged_sha,
            "audio_disposition": audio_disposition,
            "caption_source_path": str(transcript_path),
            "transcript_sha256": transcript_sha,
        }
    )
    after = json.dumps(payload, sort_keys=True)
    if before == after:
        return False
    write_json(manifest_path, payload)
    return True


def sync_shorts_audio_lane(
    context: Context,
    lane_key: str,
    *,
    update_manifests: bool = True,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    registry = load_registry(context, registry_path=registry_path)
    registry_file = Path(str(registry.get("_registry_path", ""))).expanduser().resolve()
    lanes = registry.get("lanes", [])
    if not isinstance(lanes, list):
        raise SystemExit(f"{registry_file}: `lanes` must be a list.")
    lane = _select_lane(lanes, lane_key)

    package_path = Path(str(lane.get("short_audio_package_path", "")).strip()).expanduser().resolve()
    if not package_path.exists():
        raise SystemExit(f"Audio package metadata is missing: {package_path}")
    package_payload = read_json(package_path)
    packaged_path = _required_package_file(package_payload, "packaged_path", package_path)
    transcript_path = _required_package_file(package_payload, "transcript_path", package_path)

    package_packaged_sha = str(package_payload.get("packaged_sha256", "")).strip()
    packaged_sha = sha256_path(packaged_path)
    if package_packaged_sha and package_packaged_sha != packaged_sha:
        raise SystemExit(f"{package_path}: packaged_sha256 does not match {packaged_path}")
    package_transcript_sha = str(package_payload.get("transcript_sha256", "")).strip()
    transcript_sha = sha256_path(transcript_path)
    if package_transcript_sha and package_transcript_sha != transcript_sha:
        raise SystemExit(f"{package_path}: transcript_sha256 does not match {transcript_path}")

    expected_profile_id = str(lane.get("expected_voice_profile_id", "")).strip()
    package_profile_id = str(package_payload.get("voice_profile_id", "")).strip()
    if package_profile_id:
        if expected_profile_id and package_profile_id != expected_profile_id:
            raise SystemExit(
                f"{package_path}: voice_profile_id `{package_profile_id}` does not match lane expected profile `{expected_profile_id}`."
            )
        expected_profile_id = package_profile_id
    if not expected_profile_id:
        raise SystemExit(f"{package_path}: cannot sync without expected_voice_profile_id or package voice_profile_id.")

    audio_disposition = (
        normalize_disposition(package_payload.get("audio_disposition"))
        or normalize_disposition(package_payload.get("disposition"))
        or normalize_disposition(lane.get("audio_disposition"))
    )
    if not audio_disposition:
        raise SystemExit(f"{package_path}: cannot sync without audio disposition.")

    package_sha = sha256_path(package_path)
    lane["short_audio_package_path"] = str(package_path)
    lane["expected_voice_profile_id"] = expected_profile_id
    lane["audio_disposition"] = audio_disposition
    lane["audio_package_sha256"] = package_sha
    lane["packaged_audio_sha256"] = packaged_sha
    lane["transcript_sha256"] = transcript_sha

    profiles = load_voice_profiles(registry)
    validation = validate_lane_package(lane, profiles)
    if validation.get("errors"):
        first_error = validation["errors"][0]
        raise SystemExit(f"Refusing to write invalid lane sync: {first_error['code']}: {first_error['message']}")

    manifest_results = []
    if update_manifests:
        for raw_manifest_path in lane.get("active_manifest_paths", []):
            manifest_path = Path(str(raw_manifest_path)).expanduser().resolve()
            if not manifest_path.exists():
                manifest_results.append({"path": str(manifest_path), "updated": False, "missing": True})
                continue
            updated = _sync_manifest_audio_provenance(
                manifest_path,
                package_path=package_path,
                expected_profile_id=expected_profile_id,
                audio_disposition=audio_disposition,
                package_sha=package_sha,
                packaged_path=packaged_path,
                packaged_sha=packaged_sha,
                transcript_path=transcript_path,
                transcript_sha=transcript_sha,
            )
            manifest_results.append({"path": str(manifest_path), "updated": updated, "missing": False})

    _write_registry_payload(registry_file, registry)
    return {
        "registry_path": str(registry_file),
        "lane_id": str(lane.get("lane_id", "")),
        "short_id": str(lane.get("short_id", "")),
        "short_audio_package_path": str(package_path),
        "audio_package_sha256": package_sha,
        "packaged_audio_sha256": packaged_sha,
        "transcript_sha256": transcript_sha,
        "expected_voice_profile_id": expected_profile_id,
        "audio_disposition": audio_disposition,
        "manifest_results": manifest_results,
        "updated_manifest_count": sum(1 for result in manifest_results if result.get("updated")),
        "missing_manifest_count": sum(1 for result in manifest_results if result.get("missing")),
    }


def audit_viz_short_manifest(manifest_path: Path, registry_by_package_path: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result = {"path": str(manifest_path), "errors": [], "warnings": []}
    try:
        payload = read_json(manifest_path)
    except json.JSONDecodeError as exc:
        _record(result, "errors", "invalid_short_manifest_json", f"Short manifest JSON is invalid: {exc}", path=str(manifest_path))
        return result
    if "audio_path" not in payload:
        return result
    missing = REQUIRED_MANIFEST_PROVENANCE_FIELDS - set(payload)
    for field in sorted(missing):
        _record(result, "errors", "missing_manifest_audio_provenance", f"Short manifest is missing `{field}`.", path=str(manifest_path))
    package_path = normalize_path_token(payload.get("short_audio_package_path"))
    lane = registry_by_package_path.get(package_path)
    if not lane:
        _record(result, "errors", "unregistered_audio_package", "Short manifest points to an audio package not present in the lane registry.", path=str(manifest_path))
        return result
    package_path_obj = Path(package_path)
    if package_path_obj.exists():
        package_payload = read_json(package_path_obj)
        if normalize_path_token(payload.get("audio_path")) != normalize_path_token(package_payload.get("packaged_path")):
            _record(result, "errors", "manifest_audio_path_mismatch", "`audio_path` does not match the package packaged_path.", path=str(manifest_path))
        if normalize_path_token(payload.get("caption_source_path")) != normalize_path_token(package_payload.get("transcript_path")):
            _record(result, "errors", "manifest_caption_source_mismatch", "`caption_source_path` must be the package QA transcript.", path=str(manifest_path))
    if normalize_disposition(payload.get("audio_disposition")) != normalize_disposition(lane.get("audio_disposition")):
        _record(result, "errors", "manifest_disposition_mismatch", "Manifest audio_disposition does not match registry.", path=str(manifest_path))
    if str(payload.get("expected_voice_profile_id", "")).strip() != str(lane.get("expected_voice_profile_id", "")).strip():
        _record(result, "errors", "manifest_profile_mismatch", "Manifest expected_voice_profile_id does not match registry.", path=str(manifest_path))
    if normalize_disposition(payload.get("audio_disposition")) != "keep" and "experiments" not in manifest_path.parts:
        _record(result, "errors", "diagnostic_manifest_not_quarantined", "Diagnostic/comparison short manifests must live under shorts/experiments.", path=str(manifest_path))
    return result


def audit_generated_proof_manifest(proof_manifest_path: Path) -> dict[str, Any]:
    result = {"path": str(proof_manifest_path), "errors": [], "warnings": []}
    try:
        payload = read_json(proof_manifest_path)
    except json.JSONDecodeError as exc:
        _record(result, "warnings", "invalid_historical_proof_json", f"Historical proof JSON is invalid: {exc}", path=str(proof_manifest_path))
        return result
    if "audio_path" not in payload:
        return result
    missing = REQUIRED_MANIFEST_PROVENANCE_FIELDS - set(payload)
    if missing:
        _record(
            result,
            "warnings",
            "historical_proof_missing_audio_provenance",
            f"Historical generated proof is missing provenance fields: {', '.join(sorted(missing))}.",
            path=str(proof_manifest_path),
        )
    return result


def audit_generated_proof_manifest_with_annotations(
    proof_manifest_path: Path,
    annotations_by_path: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    result = audit_generated_proof_manifest(proof_manifest_path)
    if not result.get("warnings"):
        return result
    annotation = annotations_by_path.get(normalize_path_token(proof_manifest_path))
    if not annotation or not bool(annotation.get("suppress_audit_warning", False)):
        return result
    acknowledged_codes = {
        str(code)
        for code in annotation.get("acknowledged_warning_codes", [])
        if str(code).strip()
    }
    retained_warnings = []
    suppressed_warnings = []
    for warning in result.get("warnings", []):
        if warning.get("code") in acknowledged_codes:
            suppressed_warnings.append(warning)
        else:
            retained_warnings.append(warning)
    result["warnings"] = retained_warnings
    result["suppressed_warnings"] = suppressed_warnings
    result["annotation_status"] = "suppressed" if suppressed_warnings else "present"
    return result


def registry_package_index(lanes: list[Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        package_path_text = str(lane.get("short_audio_package_path", "")).strip()
        if not package_path_text:
            continue
        package_path = Path(package_path_text).expanduser()
        if not package_path.exists():
            continue
        try:
            package_payload = read_json(package_path)
        except json.JSONDecodeError:
            continue
        packaged_path = normalize_path_token(package_payload.get("packaged_path"))
        if packaged_path:
            indexed[packaged_path] = {
                "lane": lane,
                "package_payload": package_payload,
                "package_path": str(package_path.resolve()),
            }
    return indexed


def build_historical_proof_annotation(
    proof_manifest_path: Path,
    registry_by_audio_path: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    try:
        payload = read_json(proof_manifest_path)
    except json.JSONDecodeError:
        return None
    if "audio_path" not in payload:
        return None
    missing = sorted(REQUIRED_MANIFEST_PROVENANCE_FIELDS - set(payload))
    if not missing:
        return None
    audio_path = normalize_path_token(payload.get("audio_path"))
    match = registry_by_audio_path.get(audio_path, {})
    lane = match.get("lane", {}) if isinstance(match.get("lane", {}), dict) else {}
    package_payload = match.get("package_payload", {}) if isinstance(match.get("package_payload", {}), dict) else {}
    package_path = str(match.get("package_path", ""))
    if not lane:
        return {
            "proof_manifest_path": str(proof_manifest_path.resolve()),
            "short_id": str(payload.get("short_id", "")),
            "episode_id": str(payload.get("episode_id", "")),
            "source_audio_path": audio_path,
            "missing_fields": missing,
            "acknowledged_warning_codes": [],
            "suppress_audit_warning": False,
            "annotation_reason": "historical proof has no registry match for its audio_path",
        }
    return {
        "proof_manifest_path": str(proof_manifest_path.resolve()),
        "short_id": str(payload.get("short_id", "")),
        "episode_id": str(payload.get("episode_id", "")),
        "source_audio_path": audio_path,
        "short_audio_package_path": package_path,
        "expected_voice_profile_id": str(lane.get("expected_voice_profile_id", "")),
        "audio_disposition": str(lane.get("audio_disposition", "")),
        "caption_source_path": str(package_payload.get("transcript_path", "")),
        "transcript_sha256": str(package_payload.get("transcript_sha256", "")),
        "missing_fields": missing,
        "acknowledged_warning_codes": ["historical_proof_missing_audio_provenance"],
        "suppress_audit_warning": True,
        "annotation_reason": "historical proof predates the Shorts audio provenance contract; do not rewrite generated proof manifests",
    }


def write_historical_proof_annotations(context: Context, *, output_path: Path | None = None) -> dict[str, Any]:
    registry = load_registry(context)
    lanes = registry.get("lanes", [])
    if not isinstance(lanes, list):
        lanes = []
    registry_by_audio_path = registry_package_index(lanes)
    viz_root = Path(context.channel["paths"]["viz_root"])
    annotations = []
    unresolved = []
    for proof_manifest_path in sorted((viz_root / "workflows" / "generated" / "shorts").glob("*/*/*__proof.json")):
        annotation = build_historical_proof_annotation(proof_manifest_path, registry_by_audio_path)
        if not annotation:
            continue
        if annotation.get("suppress_audit_warning"):
            annotations.append(annotation)
        else:
            unresolved.append(annotation)
    payload = {
        "schema_version": "1.0",
        "created_at": utc_now_iso(),
        "annotation_scope": "historical generated Shorts proof manifests only",
        "source_registry_path": registry.get("_registry_path", ""),
        "instructions": "These annotations suppress audit warnings for immutable generated proof manifests that predate the audio provenance contract. Do not use them for active manifests, new proofs, or final exports.",
        "annotations": annotations,
        "unresolved": unresolved,
    }
    resolved_output_path = (output_path or default_historical_proof_annotations_path(context)).expanduser().resolve()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "annotation_path": str(resolved_output_path),
        "annotation_count": len(annotations),
        "unresolved_count": len(unresolved),
    }


def run_shorts_audio_audit(
    context: Context,
    *,
    output_path: Path | None = None,
    use_historical_annotations: bool = True,
) -> dict[str, Any]:
    registry = load_registry(context)
    profiles = load_voice_profiles(registry)
    lanes = registry.get("lanes", [])
    if not isinstance(lanes, list):
        lanes = []
    lane_results = [validate_lane_package(lane, profiles) for lane in lanes if isinstance(lane, dict)]
    registry_by_package_path = {
        normalize_path_token(lane.get("short_audio_package_path")): lane
        for lane in lanes
        if isinstance(lane, dict) and str(lane.get("short_audio_package_path", "")).strip()
    }

    viz_root = Path(context.channel["paths"]["viz_root"])
    manifest_paths = sorted((viz_root / "references" / "episodes").glob("*/shorts/*.json"))
    manifest_paths.extend(sorted((viz_root / "references" / "episodes").glob("*/shorts/experiments/*.json")))
    active_manifest_results = [
        audit_viz_short_manifest(path, registry_by_package_path)
        for path in manifest_paths
    ]
    annotations_by_path = load_historical_proof_annotations(context) if use_historical_annotations else {}
    generated_proof_results = [
        audit_generated_proof_manifest_with_annotations(path, annotations_by_path)
        for path in sorted((viz_root / "workflows" / "generated" / "shorts").glob("*/*/*__proof.json"))
    ]

    errors = []
    warnings = []
    for bucket_name, results in (
        ("registry_lanes", lane_results),
        ("active_short_manifests", active_manifest_results),
    ):
        for result in results:
            for issue in result.get("errors", []):
                errors.append({"bucket": bucket_name, **issue})
            for issue in result.get("warnings", []):
                warnings.append({"bucket": bucket_name, **issue})
    for result in generated_proof_results:
        for issue in result.get("warnings", []):
            warnings.append({"bucket": "historical_generated_proofs", **issue})

    report = {
        "created_at": utc_now_iso(),
        "registry_path": registry.get("_registry_path", ""),
        "voice_profiles_path": registry.get("voice_profiles_path", ""),
        "ok": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "lane_results": lane_results,
        "active_short_manifest_results": active_manifest_results,
        "historical_generated_proof_count": len(generated_proof_results),
        "historical_annotation_count": len(annotations_by_path),
        "historical_suppressed_warning_count": sum(
            len(result.get("suppressed_warnings", []))
            for result in generated_proof_results
        ),
    }
    resolved_output_path = (output_path or (context.root / DEFAULT_REPORT_RELATIVE_PATH)).expanduser().resolve()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["report_path"] = str(resolved_output_path)
    return report
