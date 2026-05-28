from __future__ import annotations

import bisect
import copy
import hashlib
import html
import json
import math
import random
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

try:
    import pygltflib
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    pygltflib = None  # type: ignore[assignment]

try:
    import trimesh
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    trimesh = None  # type: ignore[assignment]


MODEL_SOURCE_PROVIDER_POLY_PIZZA = "poly_pizza"
MODEL_SOURCE_PROVIDER_NASA = "nasa_3d"
MODEL_SOURCE_PROVIDER_SMITHSONIAN = "smithsonian_open_access"
MODEL_SOURCE_PROVIDER_SKETCHFAB = "sketchfab"
MODEL_SOURCE_PROVIDER_BUILTIN = "builtin_curated"
MODEL_SOURCE_KIND_OPEN_ACCESS = "open_access"
MODEL_SOURCE_KIND_OPEN_LICENSE = "open_license"
MODEL_SOURCE_KIND_RESEARCH_ONLY = "research_only"
MODEL_SOURCE_CAPABILITY_ENABLED = "enabled"
MODEL_SOURCE_CAPABILITY_SEARCH_ONLY = "search_only"
MODEL_SOURCE_SUBJECT_FIT_REAL_WORLD = "real_world"
MODEL_SOURCE_SUBJECT_FIT_GENERIC = "generic"
MODEL_SOURCE_SUBJECT_FIT_CONDITIONAL = "conditional"
MODEL_SOURCE_STATUS_IDLE = "idle"
MODEL_SOURCE_STATUS_FETCHED = "fetched"
MODEL_SOURCE_STATUS_SELECTED = "selected"
MODEL_SOURCE_STATUS_CLEARED = "cleared"

PARTICLE_MOTION_ANCHOR_SHELL = 0
PARTICLE_MOTION_ANCHOR_ATTACHMENT = 1
PARTICLE_MOTION_EMISSION_PLUME = 2

POLY_PIZZA_SEARCH_TEMPLATE = "https://poly.pizza/search/{query}"
POLY_PIZZA_DETAIL_TEMPLATE = "https://poly.pizza/m/{remote_id}"
NASA_SEARCH_ENDPOINT = "https://science.nasa.gov/wp-json/smd/v1/content-list/"
NASA_DETAIL_ROOT = "https://science.nasa.gov"
SMITHSONIAN_SEARCH_TEMPLATE = "https://3d.si.edu/explore?edan_q={query}"
SMITHSONIAN_DETAIL_ROOT = "https://3d.si.edu"
SKETCHFAB_SEARCH_ENDPOINT = "https://api.sketchfab.com/v3/search"
SKETCHFAB_MODEL_DOWNLOAD_ENDPOINT = "https://api.sketchfab.com/v3/models/{uid}/download"
SKETCHFAB_MODEL_ROOT = "https://sketchfab.com"

SKETCHFAB_OPEN_LICENSES: dict[str, dict[str, str]] = {
    "cc0": {
        "license_summary": "CC0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    "by": {
        "license_summary": "CC BY",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
    },
}

NASA_REJECT_TERMS = (
    "logo",
    "logos",
    "insignia",
    "patch",
    "patches",
    "emblem",
    "badge",
    "seal",
)

EXTERNAL_MODEL_SOURCE_LIBRARY_SPECS: dict[str, dict[str, str]] = {
    "cgtrader": {
        "label": "CGTrader",
        "availability_note": "Large free-model catalog, but downloadability and reuse terms vary per listing.",
        "license_note": "Free does not imply open-license. Verify the asset page before reuse.",
        "search_url_template": "https://www.google.com/search?q=site%3Acgtrader.com%2Ffree-3d-models+{query}",
    },
    "blend_swap": {
        "label": "Blend Swap",
        "availability_note": "Useful for head basemeshes and sculpts, but downloads typically require login.",
        "license_note": "Blend Swap assets vary by license. Check the listing before reuse.",
        "search_url_template": "https://www.google.com/search?q=site%3Ablendswap.com+{query}",
    },
    "free3d": {
        "label": "Free3D",
        "availability_note": "Quick source for OBJ hits, though availability and download flows vary.",
        "license_note": "Free3D licenses are per asset. Confirm commercial and attribution terms yourself.",
        "search_url_template": "https://www.google.com/search?q=site%3Afree3d.com+{query}",
    },
    "turbosquid": {
        "label": "TurboSquid",
        "availability_note": "Broad catalog with some free assets, but the site has stronger gating and mixed formats.",
        "license_note": "Free assets still carry per-item license terms. Review the listing before reuse.",
        "search_url_template": "https://www.google.com/search?q=site%3Aturbosquid.com+{query}",
    },
}

MODEL_SOURCE_PROVIDER_POLICY: dict[str, dict[str, str]] = {
    MODEL_SOURCE_PROVIDER_BUILTIN: {
        "provider_label": "Built-in",
        "provider_kind": "curated_local",
        "provider_capability": MODEL_SOURCE_CAPABILITY_ENABLED,
        "subject_fit": "exact",
        "license_rule": "Curated local workbench default asset.",
        "license_summary": "Curated local",
        "eligibility_note": "Deterministic built-in model for default objective flows.",
    },
    MODEL_SOURCE_PROVIDER_NASA: {
        "provider_label": "NASA 3D",
        "provider_kind": MODEL_SOURCE_KIND_OPEN_ACCESS,
        "provider_capability": MODEL_SOURCE_CAPABILITY_ENABLED,
        "subject_fit": MODEL_SOURCE_SUBJECT_FIT_REAL_WORLD,
        "license_rule": "NASA media guidelines with current logo and insignia exclusions.",
        "license_summary": "NASA media guidelines",
        "eligibility_note": "Best for real-world and aerospace subjects.",
    },
    MODEL_SOURCE_PROVIDER_SMITHSONIAN: {
        "provider_label": "Smithsonian OA",
        "provider_kind": MODEL_SOURCE_KIND_OPEN_ACCESS,
        "provider_capability": MODEL_SOURCE_CAPABILITY_SEARCH_ONLY,
        "subject_fit": MODEL_SOURCE_SUBJECT_FIT_REAL_WORLD,
        "license_rule": "Only CC0 Open Access assets are eligible; the current local runtime is still search-only.",
        "license_summary": "CC0 Open Access",
        "eligibility_note": "Search-only in the current workbench runtime.",
    },
    MODEL_SOURCE_PROVIDER_POLY_PIZZA: {
        "provider_label": "Poly Pizza",
        "provider_kind": MODEL_SOURCE_KIND_OPEN_LICENSE,
        "provider_capability": MODEL_SOURCE_CAPABILITY_ENABLED,
        "subject_fit": MODEL_SOURCE_SUBJECT_FIT_CONDITIONAL,
        "license_rule": "Per-asset Creative Commons licensing; only CC0 assets are currently eligible here.",
        "license_summary": "Per-asset CC; CC0 only here",
        "eligibility_note": "Conditional generic-asset fallback, not the preferred generic default.",
    },
    MODEL_SOURCE_PROVIDER_SKETCHFAB: {
        "provider_label": "Sketchfab",
        "provider_kind": MODEL_SOURCE_KIND_OPEN_LICENSE,
        "provider_capability": MODEL_SOURCE_CAPABILITY_ENABLED,
        "subject_fit": MODEL_SOURCE_SUBJECT_FIT_CONDITIONAL,
        "license_rule": "Only downloadable CC0 and CC BY Sketchfab assets are eligible here, and fetch requires Sketchfab OAuth.",
        "license_summary": "CC0 or CC BY",
        "eligibility_note": "Downloadable open-license models; connect Sketchfab to fetch them.",
    },
}

BUILTIN_MODEL_CHALLENGER_STACK = "challenger_shuttle_stack"
BUILTIN_MODEL_CHALLENGER_ORBITER = "challenger_orbiter"

BUILTIN_MODEL_SPECS: dict[str, dict[str, str]] = {
    BUILTIN_MODEL_CHALLENGER_STACK: {
        "title": "Challenger Shuttle Stack",
        "points_path": "space_shuttle_stack_v1.points.json",
        "query": "challenger space shuttle",
    },
    BUILTIN_MODEL_CHALLENGER_ORBITER: {
        "title": "Challenger Orbiter",
        "points_path": "space_shuttle_orbiter_side_v1.points.json",
        "query": "challenger shuttle orbiter",
    },
}


class ModelSourceError(RuntimeError):
    pass


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def model_source_transform_defaults() -> dict[str, float]:
    return {
        "rotate_x_deg": 0.0,
        "rotate_y_deg": 0.0,
        "rotate_z_deg": 0.0,
    }


def normalize_model_source_transform(raw_transform: Any) -> dict[str, float]:
    defaults = model_source_transform_defaults()
    if not isinstance(raw_transform, dict):
        return defaults
    normalized: dict[str, float] = {}
    for key, default_value in defaults.items():
        try:
            value = float(raw_transform.get(key, default_value))
        except (TypeError, ValueError):
            value = default_value
        if not math.isfinite(value):
            value = default_value
        normalized[key] = round(value, 4)
    return normalized


def rotate_model_source_vector(
    vector: tuple[float, float, float],
    raw_transform: Any = None,
) -> tuple[float, float, float]:
    transform = normalize_model_source_transform(raw_transform)
    if all(abs(value) <= 1.0e-6 for value in transform.values()):
        return (
            float(vector[0]),
            float(vector[1]),
            float(vector[2]),
        )
    x, y, z = [float(component) for component in vector]
    rotate_x = math.radians(math.remainder(transform["rotate_x_deg"], 360.0))
    rotate_y = math.radians(math.remainder(transform["rotate_y_deg"], 360.0))
    rotate_z = math.radians(math.remainder(transform["rotate_z_deg"], 360.0))

    if abs(rotate_x) > 1.0e-9:
        cosine = math.cos(rotate_x)
        sine = math.sin(rotate_x)
        y, z = ((y * cosine) - (z * sine), (y * sine) + (z * cosine))
    if abs(rotate_y) > 1.0e-9:
        cosine = math.cos(rotate_y)
        sine = math.sin(rotate_y)
        x, z = ((x * cosine) + (z * sine), (-x * sine) + (z * cosine))
    if abs(rotate_z) > 1.0e-9:
        cosine = math.cos(rotate_z)
        sine = math.sin(rotate_z)
        x, y = ((x * cosine) - (y * sine), (x * sine) + (y * cosine))
    return (x, y, z)


def utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _browser_headers(*, referer: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _fetch_url(url: str, *, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers=headers or _browser_headers())
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read(240).decode("utf-8", "ignore").strip()
        raise ModelSourceError(f"Provider request failed for {url}: HTTP {exc.code} {body}".strip()) from exc
    except urllib.error.URLError as exc:
        raise ModelSourceError(f"Provider request failed for {url}: {exc.reason}") from exc


def _fetch_text(url: str, *, headers: dict[str, str] | None = None) -> str:
    return _fetch_url(url, headers=headers).decode("utf-8", "ignore")


def _fetch_json(url: str, *, headers: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        payload = json.loads(_fetch_text(url, headers=headers))
    except json.JSONDecodeError as exc:
        raise ModelSourceError(f"Provider returned invalid JSON for {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ModelSourceError(f"Provider returned an unexpected JSON payload for {url}.")
    return payload


def _sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip())
    cleaned = cleaned.strip("-._")
    return cleaned or "item"


def _license_class(raw_value: str) -> str:
    value = str(raw_value or "").strip().lower()
    if value.startswith("cc0"):
        return "cc0"
    if "nasa" in value:
        return "nasa_media_guidelines"
    return value or "unknown"


def _query_tokens(query: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", str(query or "").lower()) if len(token) >= 3]


def _query_match_score(query: str, *texts: str) -> float:
    tokens = _query_tokens(query)
    if not tokens:
        return 1.0
    haystack = " ".join(str(text or "").lower() for text in texts)
    score = 0.0
    for token in tokens:
        if token in haystack:
            score += 1.0
    return score / len(tokens)


def default_model_source_query(source_label: str, behavior: str) -> str:
    label = " ".join(re.findall(r"[A-Za-z0-9]+", str(source_label or "")))
    behavior_words = re.findall(r"[A-Za-z0-9]+", str(behavior or ""))
    behavior_hint = " ".join(behavior_words[:8])
    query = " ".join(part for part in (label, behavior_hint) if part).strip()
    return query or "space shuttle"


def global_model_source_cache_root() -> Path:
    return Path.home() / ".cache" / "cascade-effects" / "model-sources"


def model_source_defaults(*, query: str = "") -> dict[str, Any]:
    return {
        "query": str(query).strip(),
        "provider": "",
        "provider_label": "",
        "provider_kind": "",
        "provider_capability": "",
        "subject_fit": "",
        "remote_id": "",
        "remote_url": "",
        "license_class": "",
        "license_summary": "",
        "eligibility_note": "",
        "provider_policy": {},
        "status": MODEL_SOURCE_STATUS_IDLE,
        "fetched_at": "",
        "raw_asset_path": "",
        "decoded_asset_path": "",
        "normalized_asset_path": "",
        "point_cache_path": "",
        "title": "",
        "preview_url": "",
        "source_format": "",
        "author_name": "",
        "author_url": "",
        "license_url": "",
        "attribution_text": "",
        "requires_auth": False,
        "selection_eligible": False,
        "selection_error": "",
        "error": "",
        "transform": model_source_transform_defaults(),
    }


def available_builtin_model_ids() -> list[str]:
    return sorted(BUILTIN_MODEL_SPECS.keys())


def provider_policy(provider: str) -> dict[str, str]:
    return dict(MODEL_SOURCE_PROVIDER_POLICY.get(str(provider).strip(), {}))


def _attach_provider_policy(candidate: dict[str, Any]) -> dict[str, Any]:
    policy = provider_policy(str(candidate.get("provider", "")).strip())
    if not policy:
        return dict(candidate)
    attached = dict(candidate)
    attached["provider_label"] = str(attached.get("provider_label", "")).strip() or policy["provider_label"]
    attached["provider_kind"] = policy["provider_kind"]
    attached["provider_capability"] = policy["provider_capability"]
    attached["subject_fit"] = policy["subject_fit"]
    attached["license_summary"] = str(attached.get("license_summary", "")).strip() or policy["license_summary"]
    attached["eligibility_note"] = str(attached.get("eligibility_note", "")).strip() or policy["eligibility_note"]
    attached["provider_policy"] = dict(policy)
    return attached


def _best_thumbnail_url(payload: Any) -> str:
    images = payload.get("images") if isinstance(payload, dict) else None
    if not isinstance(images, list):
        return ""
    candidates = [entry for entry in images if isinstance(entry, dict) and str(entry.get("url", "")).strip()]
    if not candidates:
        return ""
    best = max(candidates, key=lambda entry: int(entry.get("width", 0) or 0) * int(entry.get("height", 0) or 0))
    return str(best.get("url", "")).strip()


def _normalize_sketchfab_license_key(raw_license: Any) -> str:
    def _candidate_values(value: Any) -> list[str]:
        if isinstance(value, dict):
            candidates: list[str] = []
            for field in ("slug", "code", "id", "uid", "label", "name", "url"):
                field_value = value.get(field)
                if field_value is not None:
                    candidates.append(str(field_value))
            return candidates
        if value is None:
            return []
        return [str(value)]

    def _classify(candidate: str) -> str:
        key = str(candidate or "").strip().lower()
        if not key:
            return ""
        if key in SKETCHFAB_OPEN_LICENSES:
            return key
        if "creativecommons.org/publicdomain/zero/" in key:
            return "cc0"
        if re.search(r"creativecommons\.org/licenses/by(?:/|$)", key):
            return "by"
        normalized = re.sub(r"[^a-z0-9]+", " ", key).strip()
        if not normalized:
            return ""
        if normalized in SKETCHFAB_OPEN_LICENSES:
            return normalized
        if normalized in {"cc attribution", "creative commons attribution"}:
            return "by"
        if normalized in {"cc0", "creative commons zero", "public domain", "public domain dedication"}:
            return "cc0"
        if "attribution" in normalized and not any(
            blocked_term in normalized for blocked_term in ("noncommercial", "noderivs", "sharealike")
        ):
            return "by"
        if "cc0" in normalized or "public domain" in normalized:
            return "cc0"
        return ""

    for candidate in _candidate_values(raw_license):
        resolved = _classify(candidate)
        if resolved:
            return resolved
    return ""


def _sketchfab_license_metadata(raw_license: Any) -> dict[str, str]:
    key = _normalize_sketchfab_license_key(raw_license)
    metadata = SKETCHFAB_OPEN_LICENSES.get(key)
    if metadata is None:
        return {
            "license_class": key or "unknown",
            "license_summary": key.upper() if key else "Unknown",
            "license_url": "",
        }
    return {
        "license_class": key,
        "license_summary": metadata["license_summary"],
        "license_url": metadata["license_url"],
    }


def _candidate_attribution_text(candidate: dict[str, Any]) -> str:
    title = str(candidate.get("title", "")).strip() or str(candidate.get("remote_id", "")).strip() or "Model"
    author_name = str(candidate.get("author_name", "")).strip()
    provider_label = str(candidate.get("provider_label", "")).strip() or title_case_provider(str(candidate.get("provider", "")).strip())
    license_summary = str(candidate.get("license_summary", "")).strip() or str(candidate.get("license_class", "")).strip()
    parts = [title]
    if author_name:
        parts.append(f"by {author_name}")
    if provider_label:
        parts.append(f"via {provider_label}")
    if license_summary:
        parts.append(f"({license_summary})")
    return " ".join(part for part in parts if part).strip()


def title_case_provider(value: str) -> str:
    return " ".join(part.capitalize() for part in re.findall(r"[A-Za-z0-9]+", str(value or "")))


def _builtin_model_spec(model_id: str) -> dict[str, str]:
    spec = BUILTIN_MODEL_SPECS.get(str(model_id).strip())
    if spec is None:
        raise ModelSourceError(f"Unknown built-in model: {model_id}")
    return dict(spec)


def _prior_points_path(repo_root: Path, relative_path: str) -> Path:
    return repo_root / "config" / "workbench_priors" / relative_path


def _load_builtin_prior_points(repo_root: Path, relative_path: str) -> dict[str, Any]:
    points_path = _prior_points_path(repo_root, relative_path)
    if not points_path.exists():
        raise ModelSourceError(f"Built-in model points are missing: {points_path}")
    try:
        payload = json.loads(points_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModelSourceError(f"Built-in model points are invalid: {points_path}: {exc}") from exc
    points = payload.get("points") if isinstance(payload, dict) else None
    if not isinstance(points, list) or not points:
        raise ModelSourceError(f"Built-in model points are invalid: {points_path}")
    return payload


def _mesh_from_builtin_points(points: list[list[float]]) -> Any:
    _require_mesh_runtime()
    base = trimesh.creation.icosphere(subdivisions=1, radius=1.0)
    spheres: list[Any] = []
    for entry in points:
        if not isinstance(entry, list) or len(entry) < 7:
            continue
        x, y, z = [float(value) for value in entry[:3]]
        weight = clamp(float(entry[6]), 0.0, 1.0)
        radius = 0.026 + (weight * 0.038)
        sphere = base.copy()
        sphere.apply_scale(radius)
        sphere.apply_translation((x, y, z))
        spheres.append(sphere)
    if not spheres:
        raise ModelSourceError("Built-in model points did not yield any mesh geometry.")
    mesh = trimesh.util.concatenate(tuple(spheres))
    mesh.remove_unreferenced_vertices()
    mesh.process(validate=False)
    if mesh.is_empty:
        raise ModelSourceError("Built-in model mesh is empty.")
    return mesh


def materialize_builtin_model_candidate(model_id: str, *, repo_root: Path, project_root: Path, seed: int) -> dict[str, Any]:
    spec = _builtin_model_spec(model_id)
    payload = _load_builtin_prior_points(repo_root, spec["points_path"])
    selection_root = project_root / "model_source" / f"{_sanitize_name(MODEL_SOURCE_PROVIDER_BUILTIN)}__{_sanitize_name(model_id)}"
    selection_root.mkdir(parents=True, exist_ok=True)
    raw_asset_path = selection_root / "raw.obj"
    if not raw_asset_path.exists():
        mesh = _mesh_from_builtin_points(payload.get("points") or [])
        _export_mesh(mesh, raw_asset_path)
    candidate = {
        "query": spec["query"],
        "provider": MODEL_SOURCE_PROVIDER_BUILTIN,
        "provider_label": "Built-in",
        "provider_kind": "curated_local",
        "provider_capability": MODEL_SOURCE_CAPABILITY_ENABLED,
        "subject_fit": "exact",
        "license_class": "curated_local",
        "license_summary": "Curated local",
        "eligibility_note": "Deterministic built-in workbench model.",
        "remote_id": str(model_id),
        "remote_url": "",
        "title": spec["title"],
        "status": MODEL_SOURCE_STATUS_SELECTED,
        "fetched_at": utc_now_iso(),
        "raw_asset_path": str(raw_asset_path),
        "source_format": "obj",
    }
    return normalize_fetched_model_candidate(candidate, project_root=project_root, seed=seed)


def _poly_pizza_bootstrap(html_text: str) -> dict[str, Any]:
    anchor = re.search(r"window\.__[^=]+=\s*\{", html_text)
    if not anchor:
        raise ModelSourceError("Poly Pizza search did not expose bootstrap data.")
    start = html_text.find("{", anchor.start())
    if start < 0:
        raise ModelSourceError("Poly Pizza search did not expose bootstrap data.")
    depth = 0
    in_string = False
    escape = False
    end = -1
    for index in range(start, len(html_text)):
        char = html_text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end < 0:
        raise ModelSourceError("Poly Pizza bootstrap data was truncated.")
    return json.loads(html_text[start:end])


def search_poly_pizza(query: str) -> list[dict[str, Any]]:
    encoded_query = urllib.parse.quote(str(query).strip())
    url = POLY_PIZZA_SEARCH_TEMPLATE.format(query=encoded_query)
    payload = _poly_pizza_bootstrap(_fetch_text(url, headers=_browser_headers(referer="https://poly.pizza/")))
    initial_data = payload.get("initialData", {})
    results = []
    for entry in initial_data.get("result", []) or []:
        license_class = _license_class(entry.get("licence", ""))
        if license_class != "cc0":
            continue
        public_id = str(entry.get("publicID", "")).strip()
        if not public_id:
            continue
        title = str(entry.get("title", "")).strip() or public_id
        score = _query_match_score(query, title, str(entry.get("alt", "")), public_id)
        if score <= 0.0:
            continue
        results.append(
            {
                "provider": MODEL_SOURCE_PROVIDER_POLY_PIZZA,
                "provider_label": "Poly Pizza",
                "remote_id": public_id,
                "remote_url": urllib.parse.urljoin("https://poly.pizza", str(entry.get("url", "")).strip()),
                "title": title,
                "preview_url": str(entry.get("previewUrl", "")).strip(),
                "license_class": license_class,
                "status": "search_result",
                "match_score": round(score, 4),
            }
        )
    return results


def _poly_pizza_asset_url(detail_html: str) -> str:
    meta_match = re.search(r'twitter:player"\s+content="([^"]+)"', detail_html)
    if meta_match:
        player_url = html.unescape(meta_match.group(1))
        parsed = urllib.parse.urlparse(player_url)
        query = urllib.parse.parse_qs(parsed.query)
        src = str((query.get("src") or [""])[0]).strip()
        if src:
            return src
    resource_match = re.search(r'"ResourceID":"([^"]+)"', detail_html)
    if resource_match:
        return f"https://static.poly.pizza/{resource_match.group(1)}.glb"
    raise ModelSourceError("Poly Pizza detail page did not expose a downloadable asset URL.")


def fetch_poly_pizza(candidate: dict[str, Any], cache_root: Path) -> dict[str, Any]:
    remote_id = str(candidate.get("remote_id", "")).strip()
    if not remote_id:
        raise ModelSourceError("Poly Pizza fetch is missing a remote id.")
    detail_url = str(candidate.get("remote_url") or POLY_PIZZA_DETAIL_TEMPLATE.format(remote_id=remote_id)).strip()
    detail_html = _fetch_text(detail_url, headers=_browser_headers(referer="https://poly.pizza/"))
    payload = _poly_pizza_bootstrap(detail_html)
    model = (payload.get("initialData", {}) or {}).get("model", {}) or {}
    license_class = _license_class(model.get("Licence", candidate.get("license_class", "")))
    if license_class != "cc0":
        raise ModelSourceError(f"Poly Pizza asset is not CC0: {model.get('Licence', 'unknown')}")
    asset_url = _poly_pizza_asset_url(detail_html)
    raw_format = Path(urllib.parse.urlparse(asset_url).path).suffix.lower() or ".glb"
    provider_root = cache_root / MODEL_SOURCE_PROVIDER_POLY_PIZZA / _sanitize_name(remote_id)
    provider_root.mkdir(parents=True, exist_ok=True)
    raw_path = provider_root / f"raw{raw_format}"
    if not raw_path.exists():
        raw_path.write_bytes(_fetch_url(asset_url, headers=_browser_headers(referer=detail_url)))
    return {
        **candidate,
        "title": str(model.get("Title", candidate.get("title", remote_id))).strip() or remote_id,
        "remote_url": detail_url,
        "license_class": license_class,
        "status": MODEL_SOURCE_STATUS_FETCHED,
        "fetched_at": utc_now_iso(),
        "raw_asset_path": str(raw_path),
        "preview_url": str(candidate.get("preview_url", "")).strip(),
        "source_format": raw_format.lstrip("."),
        "asset_url": asset_url,
    }


def _nasa_search_params(query: str) -> str:
    params = {
        "block_id": "content-list-9b8234fe-7f9c-4c6b-b6f1-d20260a330b0",
        "categories": "",
        "content_categories": "",
        "exclude_child_terms": "false",
        "exclude_child_pages": "false",
        "layout": "grid",
        "listing_page": "no",
        "listing_page_category_id": "0",
        "news_tags": "",
        "number_of_items": "15",
        "order": "ASC",
        "orderby": "title",
        "current_page": "1",
        "requesting_id": "447593",
        "science_only": "false",
        "search_query": str(query).strip(),
        "show_content_type_tags": "yes",
        "show_excerpts": "no",
        "show_pagination": "true",
        "show_publish_date": "no",
        "show_readtime": "no",
        "show_thumbnails": "yes",
        "science_org": "",
        "content_science_orgs": "",
        "internal_terms": "",
        "mission_programs": "",
        "mission_status": "",
        "mission_target": "",
        "mission_type": "",
        "response_format": "html",
        "show_drafts": "false",
        "related_content": "",
        "use_content_term_filters": "false",
        "filter_logic": "match_all",
        "base_terms": json.dumps({"category": "", "science-org": "6502,6484,6483,6487", "internal-terms": "6585", "news-tags": ""}),
        "post_types": "any",
    }
    return urllib.parse.urlencode(params)


def _nasa_rejects_title(title: str) -> bool:
    lowered = str(title or "").strip().lower()
    return any(term in lowered for term in NASA_REJECT_TERMS)


def search_nasa(query: str) -> list[dict[str, Any]]:
    url = f"{NASA_SEARCH_ENDPOINT}?{_nasa_search_params(query)}"
    payload = json.loads(_fetch_text(url, headers=_browser_headers(referer="https://science.nasa.gov/3d-resources/")))
    content_html = str(payload.get("content", "")).strip()
    pattern = re.compile(
        r'<a href="(?P<href>https://science\.nasa\.gov/3d-resources/[^"]+/)"[^>]*class="hds-content-item-thumbnail">.*?'
        r'<a href="(?P=href)"[^>]*class="hds-content-item-heading">\s*<div class="hds-a11y-heading-22">(?P<title>[^<]+)</div>',
        re.S,
    )
    preview_pattern = re.compile(r'src="([^"]+)"')
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for match in pattern.finditer(content_html):
        detail_url = html.unescape(match.group("href")).strip()
        title = html.unescape(match.group("title")).strip()
        score = _query_match_score(query, title, detail_url)
        if detail_url in seen_urls or not title or _nasa_rejects_title(title) or score <= 0.0:
            continue
        block = match.group(0)
        preview_match = preview_pattern.search(block)
        seen_urls.add(detail_url)
        results.append(
            {
                "provider": MODEL_SOURCE_PROVIDER_NASA,
                "provider_label": "NASA 3D",
                "remote_id": _sanitize_name(detail_url.rstrip("/").rsplit("/", 1)[-1]),
                "remote_url": detail_url,
                "title": title,
                "preview_url": html.unescape(preview_match.group(1)).strip() if preview_match else "",
                "license_class": "nasa_media_guidelines",
                "status": "search_result",
                "match_score": round(score, 4),
            }
        )
    return results


def fetch_nasa(candidate: dict[str, Any], cache_root: Path) -> dict[str, Any]:
    detail_url = str(candidate.get("remote_url", "")).strip()
    if not detail_url:
        raise ModelSourceError("NASA fetch is missing a detail URL.")
    detail_html = _fetch_text(detail_url, headers=_browser_headers(referer="https://science.nasa.gov/3d-resources/"))
    title = str(candidate.get("title", "")).strip()
    if _nasa_rejects_title(title):
        raise ModelSourceError(f"NASA asset is not allowed by current filters: {title}")
    model_match = re.search(r'<model-viewer\s+[^>]*src="([^"]+\.(?:glb|gltf|obj|fbx))"', detail_html, re.S)
    if not model_match:
        raise ModelSourceError("NASA detail page did not expose a downloadable 3D asset.")
    asset_url = html.unescape(model_match.group(1)).strip()
    raw_format = Path(urllib.parse.urlparse(asset_url).path).suffix.lower() or ".glb"
    provider_root = cache_root / MODEL_SOURCE_PROVIDER_NASA / _sanitize_name(str(candidate.get("remote_id", title)))
    provider_root.mkdir(parents=True, exist_ok=True)
    raw_path = provider_root / f"raw{raw_format}"
    if not raw_path.exists():
        raw_path.write_bytes(_fetch_url(asset_url, headers=_browser_headers(referer=detail_url)))
    return {
        **candidate,
        "remote_url": detail_url,
        "license_class": "nasa_media_guidelines",
        "status": MODEL_SOURCE_STATUS_FETCHED,
        "fetched_at": utc_now_iso(),
        "raw_asset_path": str(raw_path),
        "source_format": raw_format.lstrip("."),
        "asset_url": asset_url,
    }


def search_smithsonian(query: str) -> list[dict[str, Any]]:
    encoded_query = urllib.parse.quote(str(query).strip())
    url = SMITHSONIAN_SEARCH_TEMPLATE.format(query=encoded_query)
    html_text = _fetch_text(url, headers=_browser_headers(referer="https://3d.si.edu/explore"))
    pattern = re.compile(r'href="(/object/3d/[^"]+)"[^>]*>([^<]+)</a>')
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for href, raw_title in pattern.findall(html_text):
        detail_url = urllib.parse.urljoin(SMITHSONIAN_DETAIL_ROOT, href)
        title = html.unescape(raw_title).strip()
        score = _query_match_score(query, title, href)
        if not title or detail_url in seen_urls or score <= 0.0:
            continue
        seen_urls.add(detail_url)
        results.append(
            {
                "provider": MODEL_SOURCE_PROVIDER_SMITHSONIAN,
                "provider_label": "Smithsonian OA",
                "remote_id": href.rsplit(":", 1)[-1],
                "remote_url": detail_url,
                "title": title,
                "preview_url": "",
                "license_class": "candidate",
                "status": "search_result",
                "match_score": round(score, 4),
            }
        )
    return results


def fetch_smithsonian(candidate: dict[str, Any], _cache_root: Path) -> dict[str, Any]:
    detail_url = str(candidate.get("remote_url", "")).strip()
    if not detail_url:
        raise ModelSourceError("Smithsonian fetch is missing a detail URL.")
    detail_html = _fetch_text(detail_url, headers=_browser_headers(referer="https://3d.si.edu/explore"))
    if "CC0" not in detail_html or "Open Access" not in detail_html:
        raise ModelSourceError("Smithsonian asset is not clearly marked as CC0 Open Access.")
    raise ModelSourceError(
        "Smithsonian Open Access is currently search-only in the local workbench runtime; asset download is rejected when fetched from Python."
    )


def search_sketchfab(query: str) -> list[dict[str, Any]]:
    params = {
        "type": "models",
        "q": str(query).strip(),
        "downloadable": "true",
        "archives_flavours": "false",
    }
    url = f"{SKETCHFAB_SEARCH_ENDPOINT}?{urllib.parse.urlencode(params)}"
    payload = _fetch_json(
        url,
        headers={
            **_browser_headers(referer=SKETCHFAB_MODEL_ROOT),
            "Accept": "application/json",
        },
    )
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for entry in payload.get("results", []) or []:
        if not isinstance(entry, dict) or not entry.get("isDownloadable"):
            continue
        remote_id = str(entry.get("uid", "")).strip()
        if not remote_id or remote_id in seen_ids:
            continue
        license_key = _normalize_sketchfab_license_key(entry.get("license"))
        if license_key not in SKETCHFAB_OPEN_LICENSES:
            continue
        title = str(entry.get("name", "")).strip() or remote_id
        user = entry.get("user") if isinstance(entry.get("user"), dict) else {}
        author_name = str(user.get("displayName") or user.get("username") or "").strip()
        author_url = str(user.get("profileUrl", "")).strip()
        score = _query_match_score(query, title, author_name, author_url, remote_id)
        if score <= 0.0:
            score = 0.25
        seen_ids.add(remote_id)
        license_metadata = _sketchfab_license_metadata(license_key)
        candidate = {
            "provider": MODEL_SOURCE_PROVIDER_SKETCHFAB,
            "provider_label": "Sketchfab",
            "remote_id": remote_id,
            "remote_url": str(entry.get("viewerUrl", "")).strip() or urllib.parse.urljoin(SKETCHFAB_MODEL_ROOT, f"/3d-models/{remote_id}"),
            "title": title,
            "preview_url": _best_thumbnail_url(entry.get("thumbnails")),
            "license_class": license_metadata["license_class"],
            "license_summary": license_metadata["license_summary"],
            "license_url": license_metadata["license_url"],
            "author_name": author_name,
            "author_url": author_url,
            "attribution_text": "",
            "requires_auth": True,
            "status": "search_result",
            "match_score": round(score, 4),
        }
        candidate["attribution_text"] = _candidate_attribution_text(candidate)
        results.append(candidate)
    return results


def external_model_source_resources(query: str) -> list[dict[str, Any]]:
    resolved_query = str(query).strip() or "3d model"
    encoded_query = urllib.parse.quote_plus(resolved_query)
    resources: list[dict[str, Any]] = []
    for resource_id, spec in EXTERNAL_MODEL_SOURCE_LIBRARY_SPECS.items():
        resources.append(
            {
                "id": resource_id,
                "label": spec["label"],
                "availability_note": spec["availability_note"],
                "license_note": spec["license_note"],
                "search_url": spec["search_url_template"].format(query=encoded_query),
                "query": resolved_query,
            }
        )
    return resources


def search_model_candidates(query: str, *, category_hints: list[str] | None = None) -> list[dict[str, Any]]:
    del category_hints
    results: list[dict[str, Any]] = []
    for resolver in (search_poly_pizza, search_nasa, search_sketchfab, search_smithsonian):
        try:
            results.extend(_attach_provider_policy(candidate) for candidate in resolver(query))
        except ModelSourceError:
            continue
    results.sort(key=lambda item: (-float(item.get("match_score", 0.0)), str(item.get("title", "")).lower()))
    return results


def fetch_model_candidate(
    candidate: dict[str, Any],
    *,
    global_cache_root: Path | None = None,
    sketchfab_access_token: str | None = None,
) -> dict[str, Any]:
    cache_root = (global_cache_root or global_model_source_cache_root()).expanduser().resolve()
    cache_root.mkdir(parents=True, exist_ok=True)
    provider = str(candidate.get("provider", "")).strip()
    if provider == MODEL_SOURCE_PROVIDER_POLY_PIZZA:
        return _assess_fetched_candidate(_attach_provider_policy(fetch_poly_pizza(candidate, cache_root)))
    if provider == MODEL_SOURCE_PROVIDER_NASA:
        return _assess_fetched_candidate(_attach_provider_policy(fetch_nasa(candidate, cache_root)))
    if provider == MODEL_SOURCE_PROVIDER_SKETCHFAB:
        return _assess_fetched_candidate(
            _attach_provider_policy(fetch_sketchfab(candidate, cache_root, access_token=sketchfab_access_token))
        )
    if provider == MODEL_SOURCE_PROVIDER_SMITHSONIAN:
        return _assess_fetched_candidate(_attach_provider_policy(fetch_smithsonian(candidate, cache_root)))
    raise ModelSourceError(f"Unknown model-source provider: {provider}")


def _mesh_export_path(output_root: Path) -> Path:
    return output_root / "normalized.obj"


def _point_cache_path(output_root: Path) -> Path:
    return output_root / "points.json"


def _sha256_bytes(payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(payload)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _require_mesh_runtime() -> None:
    if trimesh is None:
        raise ModelSourceError("Model-source normalization requires the 'trimesh' package in the Viz Python environment.")
    if pygltflib is None:
        raise ModelSourceError("Model-source normalization requires the 'pygltflib' package in the Viz Python environment.")


def _gltf_required_extensions(raw_asset_path: Path) -> set[str]:
    suffix = raw_asset_path.suffix.lower()
    if suffix == ".gltf":
        try:
            payload = json.loads(raw_asset_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ModelSourceError(f"Unable to parse glTF asset manifest: {exc}") from exc
        values = payload.get("extensionsRequired") or []
        return {str(value).strip() for value in values if str(value).strip()}
    if suffix != ".glb":
        return set()
    try:
        raw_bytes = raw_asset_path.read_bytes()
        if len(raw_bytes) < 20 or raw_bytes[:4] != b"glTF":
            return set()
        json_length = int.from_bytes(raw_bytes[12:16], "little", signed=False)
        chunk_type = raw_bytes[16:20]
        if chunk_type != b"JSON":
            return set()
        json_bytes = raw_bytes[20:20 + json_length]
        payload = json.loads(json_bytes.decode("utf-8"))
    except Exception as exc:
        raise ModelSourceError(f"Unable to parse GLB manifest: {exc}") from exc
    values = payload.get("extensionsRequired") or []
    return {str(value).strip() for value in values if str(value).strip()}


def _validate_gltf_asset_support(raw_asset_path: Path) -> None:
    required_extensions = _gltf_required_extensions(raw_asset_path)
    if "KHR_draco_mesh_compression" in required_extensions:
        raise ModelSourceError(
            f"Unsupported model compression in {raw_asset_path.name}: glTF Draco meshes are not decodable in the local runtime yet."
        )


def _gltf_transform_copy(input_path: Path, output_path: Path, *, failure_label: str) -> Path:
    npx_path = shutil.which("npx")
    if not npx_path:
        raise ModelSourceError("glTF conversion requires 'npx' to be installed and available on PATH.")
    if output_path.exists():
        return output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        npx_path,
        "--yes",
        "@gltf-transform/cli",
        "copy",
        str(input_path),
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    if result.returncode != 0 or not output_path.exists():
        details = " ".join(
            part.strip()
            for part in (result.stderr or "", result.stdout or "")
            if part and part.strip()
        )
        raise ModelSourceError(f"{failure_label}: {details or f'exit code {result.returncode}'}")
    return output_path


def _decode_draco_asset(raw_asset_path: Path) -> Path:
    if raw_asset_path.suffix.lower() not in {".glb", ".gltf"}:
        raise ModelSourceError(f"Draco decode is only supported for glTF assets: {raw_asset_path.name}")
    decoded_path = raw_asset_path.with_name(f"{raw_asset_path.stem}.decoded.glb")
    return _gltf_transform_copy(
        raw_asset_path,
        decoded_path,
        failure_label="Failed to decode Draco-compressed glTF asset",
    )


def _sketchfab_api_headers(*, access_token: str | None = None) -> dict[str, str]:
    headers = {
        **_browser_headers(referer=SKETCHFAB_MODEL_ROOT),
        "Accept": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Token {access_token}"
    return headers


def _discover_sketchfab_archive_asset(unpack_root: Path) -> Path:
    preferred: list[Path] = []
    fallback: list[Path] = []
    for suffix in (".gltf", ".glb"):
        for path in unpack_root.rglob(f"*{suffix}"):
            if not path.is_file():
                continue
            if "__MACOSX" in path.parts:
                continue
            if suffix == ".gltf":
                preferred.append(path)
            else:
                fallback.append(path)
    candidates = preferred or fallback
    if not candidates:
        raise ModelSourceError("Sketchfab download archive did not contain a glTF or GLB asset.")
    candidates.sort(key=lambda path: (len(path.parts), len(str(path))))
    return candidates[0]


def _collapse_sketchfab_asset_to_glb(source_asset_path: Path, output_path: Path) -> Path:
    if source_asset_path.suffix.lower() == ".glb" and output_path.exists():
        return output_path
    return _gltf_transform_copy(
        source_asset_path,
        output_path,
        failure_label="Failed to collapse Sketchfab archive into a single GLB",
    )


def fetch_sketchfab(candidate: dict[str, Any], cache_root: Path, *, access_token: str | None = None) -> dict[str, Any]:
    remote_id = str(candidate.get("remote_id", "")).strip()
    if not remote_id:
        raise ModelSourceError("Sketchfab fetch is missing a remote id.")
    provider_root = cache_root / MODEL_SOURCE_PROVIDER_SKETCHFAB / _sanitize_name(remote_id)
    provider_root.mkdir(parents=True, exist_ok=True)
    raw_path = provider_root / "raw.glb"
    if not raw_path.exists():
        if not str(access_token or "").strip():
            raise ModelSourceError("Sketchfab fetch requires a personal API token. Connect Sketchfab before fetching this asset.")
        download_info = _fetch_json(
            SKETCHFAB_MODEL_DOWNLOAD_ENDPOINT.format(uid=urllib.parse.quote(remote_id)),
            headers=_sketchfab_api_headers(access_token=access_token),
        )
        archive_url = str(((download_info.get("gltf") or {}) if isinstance(download_info.get("gltf"), dict) else {}).get("url", "")).strip()
        if not archive_url:
            raise ModelSourceError("Sketchfab download API did not return a glTF archive URL.")
        archive_path = provider_root / "download.zip"
        unpack_root = provider_root / "unpacked"
        if not archive_path.exists():
            archive_path.write_bytes(_fetch_url(archive_url, headers=_browser_headers(referer=SKETCHFAB_MODEL_ROOT)))
        if not unpack_root.exists():
            unpack_root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(unpack_root)
        source_asset_path = _discover_sketchfab_archive_asset(unpack_root)
        _collapse_sketchfab_asset_to_glb(source_asset_path, raw_path)
    resolved = {
        **candidate,
        "provider": MODEL_SOURCE_PROVIDER_SKETCHFAB,
        "provider_label": "Sketchfab",
        "remote_url": str(candidate.get("remote_url", "")).strip() or urllib.parse.urljoin(SKETCHFAB_MODEL_ROOT, f"/3d-models/{remote_id}"),
        "status": MODEL_SOURCE_STATUS_FETCHED,
        "fetched_at": utc_now_iso(),
        "raw_asset_path": str(raw_path),
        "source_format": "glb",
        "requires_auth": True,
    }
    resolved["attribution_text"] = _candidate_attribution_text(_attach_provider_policy(resolved))
    return resolved


def _assess_fetched_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    assessed = dict(candidate)
    raw_asset_path = Path(str(assessed.get("raw_asset_path", ""))).expanduser()
    try:
        if not raw_asset_path.exists():
            raise ModelSourceError(f"Fetched model asset is missing: {raw_asset_path}")
        if raw_asset_path.suffix.lower() in {".glb", ".gltf"}:
            required_extensions = _gltf_required_extensions(raw_asset_path)
            if "KHR_draco_mesh_compression" in required_extensions:
                decoded_path = _decode_draco_asset(raw_asset_path)
                assessed["decoded_asset_path"] = str(decoded_path)
                _validate_gltf_asset_support(decoded_path)
            else:
                _validate_gltf_asset_support(raw_asset_path)
        assessed["selection_eligible"] = True
        assessed["selection_error"] = ""
    except ModelSourceError as exc:
        assessed["selection_eligible"] = False
        assessed["selection_error"] = str(exc)
        note = str(assessed.get("eligibility_note", "")).strip()
        assessed["eligibility_note"] = " · ".join(part for part in (note, str(exc)) if part)
    return assessed


def _load_mesh(raw_asset_path: Path) -> Any:
    _require_mesh_runtime()
    suffix = raw_asset_path.suffix.lower()
    if suffix not in {".glb", ".gltf", ".obj"}:
        raise ModelSourceError(f"Unsupported model format: {raw_asset_path.suffix}")
    if suffix in {".glb", ".gltf"} and pygltflib is not None:
        try:
            gltf = pygltflib.GLTF2()
            if suffix == ".glb":
                gltf.load_binary(str(raw_asset_path))
            else:
                gltf.load(str(raw_asset_path))
            _validate_gltf_asset_support(raw_asset_path)
        except Exception as exc:  # pragma: no cover - validation only
            if isinstance(exc, ModelSourceError):
                raise
            raise ModelSourceError(f"Unable to load glTF asset: {exc}") from exc
    loaded = trimesh.load(str(raw_asset_path), force="scene")
    if isinstance(loaded, trimesh.Trimesh):
        mesh = loaded.copy()
    elif isinstance(loaded, trimesh.Scene):
        geometries = [
            geometry.copy()
            for geometry in loaded.geometry.values()
            if isinstance(geometry, trimesh.Trimesh) and len(geometry.vertices) and len(geometry.faces)
        ]
        if not geometries:
            raise ModelSourceError("Loaded model does not contain any triangle meshes.")
        mesh = trimesh.util.concatenate(tuple(geometries))
    else:
        raise ModelSourceError("Loaded model is not a mesh scene.")
    mesh.remove_unreferenced_vertices()
    mesh.process(validate=False)
    if mesh.is_empty:
        raise ModelSourceError("Loaded model is empty.")
    return mesh


def _normalize_mesh(mesh: Any) -> Any:
    normalized = mesh.copy()
    bounds = normalized.bounds
    center = (bounds[0] + bounds[1]) / 2.0
    extents = normalized.extents
    max_extent = float(max(extents)) if len(extents) else 0.0
    if max_extent <= 1.0e-8:
        raise ModelSourceError("Loaded model has zero usable bounds.")
    normalized.vertices = (normalized.vertices - center) * (2.0 / max_extent)
    return normalized


def _export_mesh(mesh: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exported = mesh.export(file_type="obj")
    if isinstance(exported, bytes):
        path.write_bytes(exported)
    else:
        path.write_text(str(exported), encoding="utf-8")


def _sample_surface_points(mesh: Any, *, seed: int, count: int = 6400) -> list[list[float]]:
    vertices = mesh.vertices
    faces = mesh.faces
    face_normals = mesh.face_normals
    areas = mesh.area_faces
    total_area = float(sum(float(area) for area in areas))
    if total_area <= 0.0:
        raise ModelSourceError("Loaded model does not contain any measurable surface area.")
    cumulative: list[float] = []
    running = 0.0
    for area in areas:
        running += float(area)
        cumulative.append(running)
    rng = random.Random(int(seed))
    points: list[list[float]] = []
    for _ in range(count):
        target = rng.random() * total_area
        face_index = min(bisect.bisect_left(cumulative, target), len(faces) - 1)
        face = faces[face_index]
        triangle = vertices[face]
        sqrt_r1 = math.sqrt(rng.random())
        r2 = rng.random()
        u = 1.0 - sqrt_r1
        v = sqrt_r1 * (1.0 - r2)
        w = sqrt_r1 * r2
        point = (triangle[0] * u) + (triangle[1] * v) + (triangle[2] * w)
        normal = face_normals[face_index]
        normal_length = math.sqrt(float(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2)) or 1.0
        nx = float(normal[0] / normal_length)
        ny = float(normal[1] / normal_length)
        nz = float(normal[2] / normal_length)
        curvature = clamp((abs(nx) * 0.22) + (abs(ny) * 0.28) + (abs(nz) * 0.30) + (rng.random() * 0.18), 0.0, 1.0)
        points.append(
            [
                round(float(point[0]), 6),
                round(float(point[1]), 6),
                round(float(point[2]), 6),
                round(nx, 6),
                round(ny, 6),
                round(nz, 6),
                round(curvature, 6),
            ]
        )
    return points


def _bounds_for_points(points: list[list[float]]) -> dict[str, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    return {
        "min_x": round(min(xs), 6),
        "max_x": round(max(xs), 6),
        "min_y": round(min(ys), 6),
        "max_y": round(max(ys), 6),
        "min_z": round(min(zs), 6),
        "max_z": round(max(zs), 6),
    }


def _axis_name(index: int) -> str:
    return ("x", "y", "z")[int(index)]


def _axis_unit(index: int, sign: float = 1.0) -> tuple[float, float, float]:
    axis = [0.0, 0.0, 0.0]
    axis[int(index)] = -1.0 if float(sign) < 0.0 else 1.0
    return axis[0], axis[1], axis[2]


def _terminal_cross_section_breadth(
    points: list[list[float]],
    axis_a: int,
    axis_b: int,
) -> float:
    if not points:
        return 0.0
    values_a = [float(point[axis_a]) for point in points]
    values_b = [float(point[axis_b]) for point in points]
    span_a = max(values_a) - min(values_a)
    span_b = max(values_b) - min(values_b)
    return max(span_a, 1.0e-6) * max(span_b, 1.0e-6)


def infer_subject_frame_from_points(points: list[list[float]]) -> dict[str, Any]:
    valid_points = [point for point in points if isinstance(point, list) and len(point) >= 3]
    if not valid_points:
        raise ModelSourceError("Model point cache is missing usable point positions.")
    bounds = _bounds_for_points(valid_points)
    axis_extents = [
        float(bounds["max_x"]) - float(bounds["min_x"]),
        float(bounds["max_y"]) - float(bounds["min_y"]),
        float(bounds["max_z"]) - float(bounds["min_z"]),
    ]
    longitudinal_axis = max(range(3), key=lambda index: axis_extents[index])
    longitudinal_min = min(float(point[longitudinal_axis]) for point in valid_points)
    longitudinal_max = max(float(point[longitudinal_axis]) for point in valid_points)
    longitudinal_extent = max(longitudinal_max - longitudinal_min, 1.0e-6)
    terminal_band = max(longitudinal_extent * 0.18, 0.08)
    lower_terminal = [
        point for point in valid_points
        if float(point[longitudinal_axis]) <= (longitudinal_min + terminal_band)
    ]
    upper_terminal = [
        point for point in valid_points
        if float(point[longitudinal_axis]) >= (longitudinal_max - terminal_band)
    ]
    orthogonal_axes = [index for index in range(3) if index != longitudinal_axis]
    lower_breadth = _terminal_cross_section_breadth(lower_terminal, orthogonal_axes[0], orthogonal_axes[1])
    upper_breadth = _terminal_cross_section_breadth(upper_terminal, orthogonal_axes[0], orthogonal_axes[1])
    aft_sign = -1 if lower_breadth >= upper_breadth else 1
    aft_direction = _axis_unit(longitudinal_axis, aft_sign)
    return {
        "space": "model",
        "longitudinal_axis": _axis_name(longitudinal_axis),
        "orthogonal_axes": [_axis_name(index) for index in orthogonal_axes],
        "longitudinal_extent": round(longitudinal_extent, 6),
        "terminal_band": round(terminal_band, 6),
        "terminal_breadth": {
            "negative": round(lower_breadth, 6),
            "positive": round(upper_breadth, 6),
        },
        "aft_sign": int(aft_sign),
        "aft_direction": {
            "x": round(aft_direction[0], 6),
            "y": round(aft_direction[1], 6),
            "z": round(aft_direction[2], 6),
        },
        "default_emitter_direction": {
            "x": round(aft_direction[0], 6),
            "y": round(aft_direction[1], 6),
            "z": round(aft_direction[2], 6),
        },
    }


def transform_model_source_points(points: list[list[float]], raw_transform: Any = None) -> list[list[float]]:
    transform = normalize_model_source_transform(raw_transform)
    if all(abs(value) <= 1.0e-6 for value in transform.values()):
        return copy.deepcopy(points)
    transformed: list[list[float]] = []
    for entry in points:
        if not isinstance(entry, list) or len(entry) < 3:
            continue
        updated = list(entry)
        x, y, z = rotate_model_source_vector(
            (float(entry[0]), float(entry[1]), float(entry[2])),
            transform,
        )
        updated[0] = round(x, 6)
        updated[1] = round(y, 6)
        updated[2] = round(z, 6)
        if len(entry) >= 6:
            nx, ny, nz = rotate_model_source_vector(
                (float(entry[3]), float(entry[4]), float(entry[5])),
                transform,
            )
            nx, ny, nz = _normalize_vec3(nx, ny, nz)
            updated[3] = round(nx, 6)
            updated[4] = round(ny, 6)
            updated[5] = round(nz, 6)
        transformed.append(updated)
    return transformed


def load_subject_frame_from_point_cache(point_cache_path: Path, model_transform: Any = None) -> dict[str, Any]:
    try:
        point_cache = json.loads(point_cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModelSourceError(f"Model point cache is invalid: {point_cache_path}: {exc}") from exc
    points = point_cache.get("points") if isinstance(point_cache, dict) else None
    if not isinstance(points, list) or not points:
        raise ModelSourceError(f"Model point cache is missing or empty: {point_cache_path}")
    if not all(abs(value) <= 1.0e-6 for value in normalize_model_source_transform(model_transform).values()):
        return infer_subject_frame_from_points(transform_model_source_points(points, model_transform))
    cached = point_cache.get("subject_frame")
    if isinstance(cached, dict) and isinstance(cached.get("default_emitter_direction"), dict):
        return cached
    return infer_subject_frame_from_points(points)


def model_emitter_direction_from_point_cache(point_cache_path: Path, model_transform: Any = None) -> dict[str, float]:
    subject_frame = load_subject_frame_from_point_cache(point_cache_path, model_transform=model_transform)
    direction = subject_frame.get("default_emitter_direction") if isinstance(subject_frame, dict) else {}
    if not isinstance(direction, dict):
        raise ModelSourceError(f"Model point cache is missing emitter-direction defaults: {point_cache_path}")
    return {
        "direction_x": round(float(direction.get("x", 0.0) or 0.0), 4),
        "direction_y": round(float(direction.get("y", 0.0) or 0.0), 4),
        "direction_z": round(float(direction.get("z", 0.0) or 0.0), 4),
    }


def canonical_subject_view_vectors(subject_frame: dict[str, Any], raw_transform: Any = None) -> dict[str, Any]:
    longitudinal_axis = str(subject_frame.get("longitudinal_axis", "") or "").strip().lower()
    if longitudinal_axis not in {"x", "y", "z"}:
        raise ModelSourceError("Model subject frame is missing a usable longitudinal axis.")
    aft_direction_raw = subject_frame.get("aft_direction") if isinstance(subject_frame, dict) else None
    if isinstance(aft_direction_raw, dict):
        aft_direction = (
            float(aft_direction_raw.get("x", 0.0) or 0.0),
            float(aft_direction_raw.get("y", 0.0) or 0.0),
            float(aft_direction_raw.get("z", 0.0) or 0.0),
        )
    else:
        aft_sign = float(subject_frame.get("aft_sign", 1.0) or 1.0)
        aft_direction = _axis_unit("xyz".index(longitudinal_axis), aft_sign)
    if math.sqrt((aft_direction[0] ** 2) + (aft_direction[1] ** 2) + (aft_direction[2] ** 2)) <= 1.0e-8:
        raise ModelSourceError("Model subject frame is missing a usable aft direction.")
    preferred_up_axis = "y" if longitudinal_axis != "y" else ("z" if longitudinal_axis != "z" else "x")
    up_axis_vector = {
        "x": (1.0, 0.0, 0.0),
        "y": (0.0, 1.0, 0.0),
        "z": (0.0, 0.0, 1.0),
    }[preferred_up_axis]
    forward = rotate_model_source_vector(aft_direction, raw_transform)
    up = rotate_model_source_vector(up_axis_vector, raw_transform)
    return {
        "forward": _normalize_vec3(float(forward[0]), float(forward[1]), float(forward[2])),
        "up": _normalize_vec3(float(up[0]), float(up[1]), float(up[2])),
        "preferred_up_axis": preferred_up_axis,
    }


def _normalize_vec3(x: float, y: float, z: float) -> tuple[float, float, float]:
    length = math.sqrt(max((x * x) + (y * y) + (z * z), 1.0e-12))
    return x / length, y / length, z / length


def _cross_vec3(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        (a[1] * b[2]) - (a[2] * b[1]),
        (a[2] * b[0]) - (a[0] * b[2]),
        (a[0] * b[1]) - (a[1] * b[0]),
    )


def _tangent_basis(normal_x: float, normal_y: float, normal_z: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    normal = _normalize_vec3(normal_x, normal_y, normal_z)
    reference = (0.0, 0.0, 1.0) if abs(normal[2]) < 0.92 else (0.0, 1.0, 0.0)
    tangent_a = _cross_vec3(reference, normal)
    if math.sqrt(max((tangent_a[0] ** 2) + (tangent_a[1] ** 2) + (tangent_a[2] ** 2), 0.0)) <= 1.0e-8:
        tangent_a = _cross_vec3((1.0, 0.0, 0.0), normal)
    tangent_a = _normalize_vec3(*tangent_a)
    tangent_b = _normalize_vec3(*_cross_vec3(normal, tangent_a))
    return tangent_a, tangent_b


def _append_density_children(
    particles: list[dict[str, float]],
    parent: dict[str, float],
    *,
    density: float,
    layer_multiplier: float,
    rng: random.Random,
) -> None:
    extra_density = max(density - 1.0, 0.0)
    if extra_density <= 0.0 or layer_multiplier <= 0.0:
        return
    desired_children = extra_density * layer_multiplier
    child_count = int(desired_children)
    if rng.random() < (desired_children - child_count):
        child_count += 1
    if child_count <= 0:
        return
    tangent_a, tangent_b = _tangent_basis(parent["normal_x"], parent["normal_y"], parent["normal_z"])
    layer = str(parent.get("layer", "shell"))
    radial_gain = 0.92 if layer == "shell" else (0.62 if layer == "attachment" else 0.42)
    lift_gain = 0.18 if layer == "halo" else 0.38
    size_gain = 0.66 if layer == "shell" else (0.58 if layer == "attachment" else 0.48)
    alpha_gain = 0.74 if layer == "shell" else (0.66 if layer == "attachment" else 0.56)
    for _ in range(child_count):
        angle = rng.random() * math.pi * 2.0
        radial_distance = parent["world_radius"] * radial_gain * (0.55 + (rng.random() * 1.25))
        lift_distance = parent["world_radius"] * lift_gain * (0.04 + (rng.random() * 0.22))
        child = dict(parent)
        child["world_x"] = float(
            parent["world_x"]
            + ((tangent_a[0] * math.cos(angle)) + (tangent_b[0] * math.sin(angle))) * radial_distance
            + (parent["normal_x"] * lift_distance)
        )
        child["world_y"] = float(
            parent["world_y"]
            + ((tangent_a[1] * math.cos(angle)) + (tangent_b[1] * math.sin(angle))) * radial_distance
            + (parent["normal_y"] * lift_distance)
        )
        child["world_z"] = float(
            parent["world_z"]
            + ((tangent_a[2] * math.cos(angle)) + (tangent_b[2] * math.sin(angle))) * radial_distance
            + (parent["normal_z"] * lift_distance)
        )
        child["world_radius"] = float(max(parent["world_radius"] * (size_gain + (rng.random() * 0.10)), 0.0016))
        child["alpha"] = float(clamp(parent["alpha"] * alpha_gain, 0.08, 1.0))
        child["intensity"] = float(clamp(parent["intensity"] * (0.92 + (rng.random() * 0.08)), 0.0, 1.0))
        child["release_weight"] = float(clamp(parent["release_weight"] * (0.94 + (rng.random() * 0.10)), 0.0, 1.0))
        child["retain_weight"] = float(clamp(parent["retain_weight"] * (0.92 + (rng.random() * 0.06)), 0.0, 1.0))
        child["phase"] = float(parent["phase"] + (rng.random() * 1.1))
        child["drift_scale"] = float(parent["drift_scale"] * (0.96 + (rng.random() * 0.08)))
        child["shell_weight"] = float(clamp(parent["shell_weight"] * (0.94 + (rng.random() * 0.08)), 0.0, 1.0))
        child["halo_factor"] = float(clamp(parent["halo_factor"] * (0.92 + (rng.random() * 0.08)), 0.0, 1.0))
        particles.append(child)


def normalize_fetched_model_candidate(fetched_candidate: dict[str, Any], *, project_root: Path, seed: int) -> dict[str, Any]:
    if fetched_candidate.get("selection_eligible") is False:
        raise ModelSourceError(str(fetched_candidate.get("selection_error", "")).strip() or "Fetched model is not eligible for selection.")
    source_asset_path = Path(
        str(fetched_candidate.get("decoded_asset_path", "")).strip() or str(fetched_candidate.get("raw_asset_path", "")).strip()
    ).expanduser().resolve()
    if not source_asset_path.exists():
        raise ModelSourceError(f"Fetched model asset is missing: {source_asset_path}")
    selection_root = project_root / "model_source" / f"{_sanitize_name(str(fetched_candidate.get('provider', 'provider')))}__{_sanitize_name(str(fetched_candidate.get('remote_id', 'model')))}"
    selection_root.mkdir(parents=True, exist_ok=True)
    raw_copy_path = selection_root / f"raw{source_asset_path.suffix.lower()}"
    normalized_asset_path = _mesh_export_path(selection_root)
    point_cache_path = _point_cache_path(selection_root)
    asset_copied = False
    if raw_copy_path.resolve() != source_asset_path:
        if raw_copy_path.exists():
            source_stat = source_asset_path.stat()
            cached_stat = raw_copy_path.stat()
            asset_copied = (
                cached_stat.st_size != source_stat.st_size
                or cached_stat.st_mtime_ns < source_stat.st_mtime_ns
            )
        else:
            asset_copied = True
        if asset_copied:
            shutil.copy2(source_asset_path, raw_copy_path)
    if raw_copy_path.exists() and normalized_asset_path.exists() and point_cache_path.exists() and not asset_copied:
        try:
            payload_bytes = point_cache_path.read_bytes()
            point_cache_payload = json.loads(payload_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            point_cache_payload = None
            payload_bytes = b""
        if (
            isinstance(point_cache_payload, dict)
            and str(point_cache_payload.get("provider", "")).strip() == str(fetched_candidate.get("provider", "")).strip()
            and str(point_cache_payload.get("remote_id", "")).strip() == str(fetched_candidate.get("remote_id", "")).strip()
            and isinstance(point_cache_payload.get("subject_frame"), dict)
            and point_cache_payload.get("subject_frame")
        ):
            cached_raw_sha256 = str(point_cache_payload.get("raw_asset_sha256", "")).strip()
            if not cached_raw_sha256 or cached_raw_sha256 == _sha256_file(raw_copy_path):
                return _attach_provider_policy({
                    **fetched_candidate,
                    "status": MODEL_SOURCE_STATUS_SELECTED,
                    "raw_asset_path": str(raw_copy_path),
                    "decoded_asset_path": str(raw_copy_path),
                    "normalized_asset_path": str(normalized_asset_path),
                    "point_cache_path": str(point_cache_path),
                    "point_cache_sha256": _sha256_bytes(payload_bytes),
                    "subject_frame": point_cache_payload["subject_frame"],
                    "source_format": str(point_cache_payload.get("source_format", fetched_candidate.get("source_format", raw_copy_path.suffix.lstrip(".")))),
                })
    mesh = _normalize_mesh(_load_mesh(raw_copy_path))
    _export_mesh(mesh, normalized_asset_path)
    points = _sample_surface_points(mesh, seed=seed)
    subject_frame = infer_subject_frame_from_points(points)
    point_cache_payload = {
        "schema_version": 1,
        "provider": str(fetched_candidate.get("provider", "")),
        "remote_id": str(fetched_candidate.get("remote_id", "")),
        "remote_url": str(fetched_candidate.get("remote_url", "")),
        "source_format": str(fetched_candidate.get("source_format", raw_copy_path.suffix.lstrip("."))),
        "raw_asset_sha256": _sha256_file(raw_copy_path),
        "normalized_asset_path": str(normalized_asset_path),
        "point_count": len(points),
        "bounds": _bounds_for_points(points),
        "subject_frame": subject_frame,
        "points": points,
    }
    payload_bytes = (json.dumps(point_cache_payload, indent=2) + "\n").encode("utf-8")
    point_cache_path.write_bytes(payload_bytes)
    return _attach_provider_policy({
        **fetched_candidate,
        "status": MODEL_SOURCE_STATUS_SELECTED,
        "raw_asset_path": str(raw_copy_path),
        "decoded_asset_path": str(raw_copy_path),
        "normalized_asset_path": str(normalized_asset_path),
        "point_cache_path": str(point_cache_path),
        "point_cache_sha256": _sha256_bytes(payload_bytes),
        "subject_frame": subject_frame,
    })


def build_model_particles_from_cache(
    point_cache_path: Path,
    scene: dict[str, Any],
    model_transform: Any = None,
) -> list[dict[str, float]]:
    point_cache = json.loads(point_cache_path.read_text(encoding="utf-8"))
    base_points = point_cache.get("points") or []
    if not isinstance(base_points, list) or not base_points:
        raise ModelSourceError(f"Model point cache is missing or empty: {point_cache_path}")
    transformed_points = transform_model_source_points(base_points, model_transform)
    rng = random.Random(int(scene.get("seed", 42)) + 17)
    surface = scene["surface"]
    breakup = scene["breakup"]
    volume = scene.get("volume", {})
    density = clamp(float(surface.get("density", 1.0)), 0.2, 3.0)
    base_keep_probability = 1.0 if density >= 1.0 else clamp(0.12 + (density * 0.88), 0.10, 1.0)
    base_radius = 0.0044 + (float(surface.get("size", 0.22)) * 0.010)
    depth_scale = clamp(float(volume.get("depth_scale", 0.58)), 0.0, 1.5)
    particles: list[dict[str, float]] = []
    for index, entry in enumerate(transformed_points):
        if len(entry) < 7:
            continue
        x, y, z, nx, ny, nz, curvature = [float(value) for value in entry[:7]]
        if rng.random() > base_keep_probability:
            continue
        world_x = x
        world_y = y
        world_z = z * (0.86 + (depth_scale * 0.22))
        intensity = clamp(0.58 + (curvature * 0.22) + (max(nz, 0.0) * 0.16), 0.0, 1.0)
        shell_particle = {
            "source_x": float(index),
            "source_y": float(index),
            "world_x": world_x,
            "world_y": world_y,
            "world_z": world_z,
            "world_radius": float(max(base_radius * (0.90 + (curvature * 0.25)), 0.0028)),
            "luminance": float(intensity),
            "edge": float(clamp(0.44 + (curvature * 0.38), 0.0, 1.0)),
            "alpha": 0.84,
            "intensity": float(intensity),
            "release_weight": float(clamp(0.16 + (curvature * 0.12) + (max(nz, 0.0) * 0.06), 0.0, 1.0)),
            "retain_weight": float(clamp(float(breakup.get("retain", 0.9)) * 0.92, 0.0, 1.0)),
            "phase": float(rng.random() * math.pi * 2.0),
            "drift_scale": float(0.78 + (rng.random() * 0.24)),
            "depth": float(clamp(0.5 + (world_z * 0.36), 0.0, 1.0)),
            "normal_x": float(nx),
            "normal_y": float(ny),
            "normal_z": float(nz),
            "halo_factor": 0.0,
            "shell_weight": float(clamp(0.86 + (curvature * 0.12), 0.0, 1.0)),
            "travel_weight": 0.22,
            "emission_weight": 0.0,
            "layer": "shell",
            "motion_mode": PARTICLE_MOTION_ANCHOR_SHELL,
        }
        particles.append(shell_particle)
        if index % 9 == 0:
            attachment_particle = {
                **shell_particle,
                "world_x": world_x * 0.94,
                "world_y": world_y * 0.94,
                "world_z": world_z * 0.94,
                "world_radius": float(shell_particle["world_radius"] * 0.82),
                "alpha": 0.38,
                "release_weight": float(clamp(0.24 + (curvature * 0.14), 0.0, 1.0)),
                "retain_weight": float(clamp(float(breakup.get("retain", 0.9)) * 0.64, 0.0, 1.0)),
                "halo_factor": 0.0,
                "shell_weight": float(clamp(0.48 + (curvature * 0.18), 0.0, 1.0)),
                "travel_weight": 0.56,
                "emission_weight": 0.38,
                "layer": "attachment",
                "motion_mode": PARTICLE_MOTION_ANCHOR_ATTACHMENT,
            }
            particles.append(attachment_particle)
        if index % 6 == 0:
            emission_particle = {
                **shell_particle,
                "world_x": world_x + (nx * (0.026 + (curvature * 0.010))),
                "world_y": world_y + (ny * (0.026 + (curvature * 0.010))),
                "world_z": world_z + (nz * (0.048 + (depth_scale * 0.026))),
                "world_radius": float(shell_particle["world_radius"] * 0.56),
                "alpha": 0.14,
                "intensity": float(clamp(0.34 + (curvature * 0.10), 0.0, 1.0)),
                "release_weight": float(clamp(0.72 + (curvature * 0.12), 0.0, 1.0)),
                "retain_weight": float(clamp(float(breakup.get("retain", 0.9)) * 0.10, 0.0, 1.0)),
                "halo_factor": float(clamp(0.62 + (curvature * 0.18), 0.0, 1.0)),
                "shell_weight": 0.10,
                "travel_weight": 1.82,
                "emission_weight": 1.0,
                "layer": "emission",
                "motion_mode": PARTICLE_MOTION_EMISSION_PLUME,
            }
            particles.append(emission_particle)
            # Supplemental density should thicken the emitted plume, not duplicate the anchored silhouette.
            _append_density_children(
                particles,
                emission_particle,
                density=density,
                layer_multiplier=1.35,
                rng=rng,
            )
    if not particles:
        raise ModelSourceError("Model-backed point generation did not produce any particles.")
    return particles
