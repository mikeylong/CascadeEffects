#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

UPSCALER_RE = re.compile(r"^ltx-[\d.]+-(?:spatial|temporal)-upscaler-.+\.safetensors$")
MONOLITHIC_RE = re.compile(r"^ltx-[\d.]+-\d+b-(distilled|dev)\.safetensors$")
MANIFEST_NAME = "backend_manifest.json"

REQUIRED_MODULAR_EXACT = [
    "transformer/config.json",
    "vae/encoder/config.json",
    "vae/decoder/config.json",
    "text_projections/model.safetensors",
    "text_encoder/config.json",
    "tokenizer/tokenizer_config.json",
]

REQUIRED_MODULAR_GLOBS = [
    "transformer/model*.safetensors",
    "vae/encoder/model*.safetensors",
    "vae/decoder/model*.safetensors",
]


@dataclass
class BackendStatus:
    source: str
    variant: str
    source_kind: str
    layout_type: str
    needs_preparation: bool
    prepared_path: Path
    source_snapshot: str | None = None
    message: str | None = None
    prepared_ready: bool = False


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def mlx_video_version() -> str:
    from mlx_video.version import __version__

    return __version__


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stable_slug(source: str, variant: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", source).strip("-")
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"{base[:72] or 'backend'}-{variant}-{digest}"


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def has_required_modular_files(root: Path) -> tuple[bool, list[str]]:
    missing: list[str] = []

    for rel in REQUIRED_MODULAR_EXACT:
        if not (root / rel).exists():
            missing.append(rel)

    for pattern in REQUIRED_MODULAR_GLOBS:
        if not list(root.glob(pattern)):
            missing.append(pattern)

    return (len(missing) == 0, missing)


def has_flat_monolithic_layout(root: Path, variant: str) -> bool:
    if not (root / "text_encoder" / "config.json").exists():
        return False
    if not (root / "tokenizer" / "tokenizer_config.json").exists():
        return False
    for candidate in root.iterdir():
        if candidate.is_file():
            match = MONOLITHIC_RE.match(candidate.name)
            if match and match.group(1) == variant:
                return True
    return False


def classify_local_source(source_path: Path, variant: str, prepared_path: Path) -> BackendStatus:
    resolved = source_path.expanduser().resolve()
    if resolved.is_file():
        match = MONOLITHIC_RE.match(resolved.name)
        parent = resolved.parent
        if match and match.group(1) == variant and has_flat_monolithic_layout(parent, variant):
            return BackendStatus(
                source=str(source_path),
                variant=variant,
                source_kind="local-path",
                layout_type="flat-monolithic",
                needs_preparation=True,
                prepared_path=prepared_path,
                source_snapshot=str(parent),
            )
        return BackendStatus(
            source=str(source_path),
            variant=variant,
            source_kind="local-path",
            layout_type="unsupported",
            needs_preparation=False,
            prepared_path=prepared_path,
            source_snapshot=str(parent),
            message=f"Unsupported local backend file at {resolved}",
        )

    modular_ok, _ = has_required_modular_files(resolved)
    if modular_ok:
        return BackendStatus(
            source=str(source_path),
            variant=variant,
            source_kind="local-path",
            layout_type="modular-compatible",
            needs_preparation=False,
            prepared_path=prepared_path,
            source_snapshot=str(resolved),
        )

    if has_flat_monolithic_layout(resolved, variant):
        return BackendStatus(
            source=str(source_path),
            variant=variant,
            source_kind="local-path",
            layout_type="flat-monolithic",
            needs_preparation=True,
            prepared_path=prepared_path,
            source_snapshot=str(resolved),
        )

    return BackendStatus(
        source=str(source_path),
        variant=variant,
        source_kind="local-path",
        layout_type="unsupported",
        needs_preparation=False,
        prepared_path=prepared_path,
        source_snapshot=str(resolved),
        message=f"Unsupported local backend layout at {resolved}",
    )


def matches_any(files: set[str], pattern: str) -> bool:
    regex = re.compile("^" + pattern.replace(".", r"\.").replace("*", ".*") + "$")
    return any(regex.match(item) for item in files)


def classify_hf_source(repo_id: str, variant: str, prepared_path: Path) -> BackendStatus:
    from huggingface_hub import list_repo_files
    from huggingface_hub.utils import HfHubHTTPError

    try:
        repo_files = set(list_repo_files(repo_id))
    except HfHubHTTPError as exc:
        return BackendStatus(
            source=repo_id,
            variant=variant,
            source_kind="hf-repo",
            layout_type="unsupported",
            needs_preparation=False,
            prepared_path=prepared_path,
            message=f"Unable to inspect Hugging Face repo {repo_id}: {exc}",
        )
    except Exception as exc:
        return BackendStatus(
            source=repo_id,
            variant=variant,
            source_kind="hf-repo",
            layout_type="unsupported",
            needs_preparation=False,
            prepared_path=prepared_path,
            message=f"Unable to inspect Hugging Face repo {repo_id}: {exc}",
        )

    modular_ok = all(item in repo_files for item in REQUIRED_MODULAR_EXACT) and all(
        matches_any(repo_files, pattern) for pattern in REQUIRED_MODULAR_GLOBS
    )
    if modular_ok:
        return BackendStatus(
            source=repo_id,
            variant=variant,
            source_kind="hf-repo",
            layout_type="modular-compatible",
            needs_preparation=False,
            prepared_path=prepared_path,
        )

    has_monolithic = any(
        MONOLITHIC_RE.match(name) and MONOLITHIC_RE.match(name).group(1) == variant
        for name in repo_files
    )
    if (
        has_monolithic
        and "text_encoder/config.json" in repo_files
        and "tokenizer/tokenizer_config.json" in repo_files
    ):
        return BackendStatus(
            source=repo_id,
            variant=variant,
            source_kind="hf-repo",
            layout_type="flat-monolithic",
            needs_preparation=True,
            prepared_path=prepared_path,
        )

    return BackendStatus(
        source=repo_id,
        variant=variant,
        source_kind="hf-repo",
        layout_type="unsupported",
        needs_preparation=False,
        prepared_path=prepared_path,
        message=f"Repo {repo_id} does not expose a supported LTX-2 layout for variant={variant}",
    )


def classify_source(source: str, variant: str, prepared_root: Path) -> BackendStatus:
    prepared_path = prepared_root / stable_slug(source, variant)
    source_path = Path(source).expanduser()
    if source_path.exists():
        return classify_local_source(source_path, variant, prepared_path)
    if "/" in source:
        status = classify_hf_source(source, variant, prepared_path)
        if status.layout_type != "unsupported":
            return status
        cached = find_matching_prepared_backend(prepared_root, source, variant)
        if cached is not None:
            cached_path, manifest = cached
            return BackendStatus(
                source=source,
                variant=variant,
                source_kind="hf-repo",
                layout_type=str(manifest.get("layout_type", "flat-monolithic")),
                needs_preparation=False,
                prepared_path=cached_path,
                source_snapshot=manifest.get("source_snapshot"),
                message=status.message or f"Using cached prepared backend for {source} variant={variant}",
            )
        return status
    return BackendStatus(
        source=source,
        variant=variant,
        source_kind="unknown",
        layout_type="unsupported",
        needs_preparation=False,
        prepared_path=prepared_path,
        message=f"Source is neither a readable local path nor a Hugging Face repo id: {source}",
    )


def validate_prepared_backend(root: Path) -> None:
    okay, missing = has_required_modular_files(root)
    if not okay:
        joined = ", ".join(missing)
        raise RuntimeError(f"Incomplete prepared backend at {root}: missing {joined}")


def load_manifest(path: Path) -> dict | None:
    manifest_path = path / MANIFEST_NAME
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_existing_prepared(path: Path, source: str, variant: str) -> bool:
    try:
        validate_prepared_backend(path)
    except Exception:
        return False
    manifest = load_manifest(path)
    if manifest is None:
        return False
    return (
        manifest.get("source_repo_or_path") == source
        and manifest.get("variant") == variant
        and manifest.get("status") == "ready"
    )


def prepared_manifest(path: Path, source: str, variant: str) -> dict | None:
    if not validate_existing_prepared(path, source, variant):
        return None
    return load_manifest(path)


def find_matching_prepared_backend(prepared_root: Path, source: str, variant: str) -> tuple[Path, dict] | None:
    if not prepared_root.exists():
        return None
    for candidate in sorted(prepared_root.iterdir()):
        if not candidate.is_dir():
            continue
        manifest = load_manifest(candidate)
        if manifest is None:
            continue
        if (
            manifest.get("source_repo_or_path") == source
            and manifest.get("variant") == variant
            and manifest.get("status") == "ready"
        ):
            try:
                validate_prepared_backend(candidate)
            except Exception:
                continue
            return candidate, manifest
    return None


def refresh_manifest_if_needed(path: Path, status: BackendStatus) -> None:
    manifest = prepared_manifest(path, status.source, status.variant)
    if manifest is None:
        return
    if manifest.get("prepared_path") == str(path):
        return
    write_manifest(
        path,
        status.source,
        status.variant,
        status.layout_type,
        manifest.get("source_snapshot") or status.source_snapshot,
    )


def infer_source_snapshot_from_prepared(prepared_root: Path, source: str) -> str | None:
    text_encoder = prepared_root / "text_encoder"
    if text_encoder.is_symlink():
        return str(text_encoder.resolve().parent)

    source_path = Path(source).expanduser()
    if source_path.exists():
        return str(source_path.resolve())

    return None


def write_manifest(
    prepared_path: Path,
    source: str,
    variant: str,
    layout_type: str,
    source_snapshot: str | None,
) -> None:
    data = {
        "source_repo_or_path": source,
        "source_snapshot": source_snapshot,
        "variant": variant,
        "runtime_version": mlx_video_version(),
        "layout_type": layout_type,
        "prepared_path": str(prepared_path),
        "created_at": now_utc(),
        "status": "ready",
    }
    (prepared_path / MANIFEST_NAME).write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def monolithic_filename_from_repo(repo_id: str, variant: str) -> str:
    from huggingface_hub import list_repo_files

    repo_files = list_repo_files(repo_id)
    candidates = [
        name
        for name in repo_files
        if MONOLITHIC_RE.match(name) and MONOLITHIC_RE.match(name).group(1) == variant
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No monolithic LTX file found in {repo_id} for variant={variant}"
        )
    return sorted(candidates)[0]


def resolve_hf_snapshot_for_flat_source(repo_id: str, variant: str) -> str | None:
    from huggingface_hub import hf_hub_download

    filename = monolithic_filename_from_repo(repo_id, variant)
    local_path = Path(hf_hub_download(repo_id=repo_id, filename=filename))
    return str(local_path.parent)


def resolve_modular_source_root(source: str) -> Path:
    from huggingface_hub import snapshot_download

    source_path = Path(source).expanduser()
    if source_path.exists():
        return source_path.resolve()

    snapshot_path = snapshot_download(
        repo_id=source,
        allow_patterns=[
            "transformer/*",
            "vae/*",
            "text_projections/*",
            "text_encoder/*",
            "tokenizer/*",
            "audio_vae/*",
            "vocoder/*",
            "ltx-*-upscaler-*.safetensors",
        ],
    )
    return Path(snapshot_path)


def link_tree(src: Path, dest: Path, names: Iterable[str]) -> None:
    for name in names:
        source_item = src / name
        if not source_item.exists():
            continue
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source_item.resolve())


def prepare_modular_backend(status: BackendStatus) -> Path:
    final_path = status.prepared_path
    if validate_existing_prepared(final_path, status.source, status.variant):
        refresh_manifest_if_needed(final_path, status)
        eprint(f"Prepared backend already valid: {final_path}")
        return final_path

    if final_path.exists() or final_path.is_symlink():
        remove_path(final_path)

    partial_path = final_path.with_name(final_path.name + ".partial")
    remove_path(partial_path)
    partial_path.mkdir(parents=True, exist_ok=True)

    source_root = resolve_modular_source_root(status.source)
    link_tree(
        source_root,
        partial_path,
        [
            "transformer",
            "vae",
            "text_projections",
            "text_encoder",
            "tokenizer",
            "audio_vae",
            "vocoder",
        ],
    )
    for upscaler in source_root.glob("ltx-*-upscaler-*.safetensors"):
        (partial_path / upscaler.name).symlink_to(upscaler.resolve())

    validate_prepared_backend(partial_path)
    partial_path.rename(final_path)
    write_manifest(
        final_path,
        status.source,
        status.variant,
        status.layout_type,
        str(source_root),
    )
    return final_path


def prepare_flat_backend(status: BackendStatus) -> Path:
    from mlx_video.models.ltx_2.convert import convert as convert_ltx2

    final_path = status.prepared_path
    if validate_existing_prepared(final_path, status.source, status.variant):
        refresh_manifest_if_needed(final_path, status)
        eprint(f"Prepared backend already valid: {final_path}")
        return final_path

    if final_path.exists() or final_path.is_symlink():
        remove_path(final_path)

    partial_path = final_path.with_name(final_path.name + ".partial")
    remove_path(partial_path)
    partial_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with contextlib.redirect_stdout(sys.stderr):
            convert_ltx2(status.source, partial_path, variant=status.variant)
        validate_prepared_backend(partial_path)
        source_snapshot = status.source_snapshot
        if source_snapshot is None and status.source_kind == "hf-repo":
            source_snapshot = resolve_hf_snapshot_for_flat_source(
                status.source,
                status.variant,
            )
        if source_snapshot is None:
            source_snapshot = infer_source_snapshot_from_prepared(partial_path, status.source)
        partial_path.rename(final_path)
        write_manifest(
            final_path,
            status.source,
            status.variant,
            status.layout_type,
            source_snapshot,
        )
    except Exception:
        remove_path(partial_path)
        raise

    return final_path


def render_status(status: BackendStatus) -> str:
    manifest = prepared_manifest(status.prepared_path, status.source, status.variant)
    prepared_state = "ready" if manifest else (
        "needs-preparation" if status.needs_preparation else "not-prepared"
    )
    source_snapshot = status.source_snapshot or (manifest or {}).get("source_snapshot", "")
    return "\n".join(
        [
            f"source: {status.source}",
            f"source_kind: {status.source_kind}",
            f"variant: {status.variant}",
            f"layout_type: {status.layout_type}",
            f"prepared_path: {status.prepared_path}",
            f"prepared_state: {prepared_state}",
            f"needs_preparation: {'yes' if status.needs_preparation else 'no'}",
            f"runtime_version: {mlx_video_version()}",
            f"source_snapshot: {source_snapshot}",
            f"message: {status.message or ''}",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cascade Effects MLX video backend helper")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--mlx-video-dir", required=True)
    parser.add_argument("--prepared-root", required=True)
    parser.add_argument("--hf-home", required=True)
    parser.add_argument("--hf-hub-cache", required=True)

    subparsers = parser.add_subparsers(dest="command", required=True)
    backend = subparsers.add_parser("backend")
    backend_sub = backend.add_subparsers(dest="backend_command", required=True)

    for name in ("status", "prepare"):
        sub = backend_sub.add_parser(name)
        sub.add_argument(
            "--model-repo",
            default=os.environ.get("CE_MLX_VIDEO_MODEL_REPO", "mlx-community/LTX-2-distilled-bf16"),
        )
        sub.add_argument(
            "--variant",
            choices=("distilled", "dev"),
            default="distilled",
        )
        sub.add_argument("--json", action="store_true")

    backend_sub.choices["prepare"].add_argument("--print-path-only", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["HF_HOME"] = args.hf_home
    os.environ["HF_HUB_CACHE"] = args.hf_hub_cache

    prepared_root = Path(args.prepared_root)
    prepared_root.mkdir(parents=True, exist_ok=True)

    if args.command != "backend":
        raise SystemExit(f"Unsupported command: {args.command}")

    status = classify_source(args.model_repo, args.variant, prepared_root)

    if args.backend_command == "status":
        manifest = prepared_manifest(status.prepared_path, status.source, status.variant)
        if args.json:
            print(
                json.dumps(
                    {
                        "source": status.source,
                        "source_kind": status.source_kind,
                        "variant": status.variant,
                        "layout_type": status.layout_type,
                        "prepared_path": str(status.prepared_path),
                        "needs_preparation": status.needs_preparation,
                        "source_snapshot": status.source_snapshot or (manifest or {}).get("source_snapshot"),
                        "message": status.message,
                        "runtime_version": mlx_video_version(),
                    },
                    indent=2,
                )
            )
        else:
            print(render_status(status))
        return 0 if status.layout_type != "unsupported" else 1

    if status.layout_type == "unsupported":
        raise SystemExit(status.message or f"Unsupported backend source: {status.source}")

    if status.layout_type == "flat-monolithic":
        prepared_path = prepare_flat_backend(status)
    else:
        prepared_path = prepare_modular_backend(status)

    if args.json:
        print(
            json.dumps(
                {
                    "source": status.source,
                    "variant": status.variant,
                    "layout_type": status.layout_type,
                    "prepared_path": str(prepared_path),
                    "runtime_version": mlx_video_version(),
                },
                indent=2,
            )
        )
    elif args.print_path_only:
        print(str(prepared_path))
    else:
        print(render_status(status))
        print(f"resolved_prepared_path: {prepared_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
