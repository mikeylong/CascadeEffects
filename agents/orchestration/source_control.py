from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from orchestration.io import Context

DEFAULT_MEDIA_AUDIT_REPORT_RELATIVE_PATH = Path("state/source_control_media_audit.json")
SOURCE_MEDIA_HOOK_MARKER = "Cascade Effects source-media-audit hook"
PREVIOUS_PRE_COMMIT_HOOK_NAME = "pre-commit.source-media-audit.previous"

BANNED_MEDIA_MODEL_EXTENSIONS = frozenset(
    {
        ".aiff",
        ".ckpt",
        ".flac",
        ".jpeg",
        ".jpg",
        ".m4a",
        ".mkv",
        ".mov",
        ".mp3",
        ".mp4",
        ".onnx",
        ".png",
        ".pt",
        ".pth",
        ".safetensor",
        ".safetensors",
        ".wav",
        ".webp",
    }
)

BANNED_MEDIA_SIDECAR_SUFFIXES = frozenset(
    {
        ".jpeg.json",
        ".jpg.json",
        ".m4a.json",
        ".mkv.json",
        ".mov.json",
        ".mp4.json",
        ".png.json",
        ".wav.json",
        ".webp.json",
    }
)


def _git_ls_files(repo_root: Path, *args: str) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip())
    return [part.decode("utf-8", errors="replace") for part in completed.stdout.split(b"\0") if part]


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _is_banned_path(path: str) -> bool:
    return Path(path).suffix.lower() in BANNED_MEDIA_MODEL_EXTENSIONS


def _is_banned_sidecar_path(path: str) -> bool:
    lowered = str(path).lower()
    return any(lowered.endswith(suffix) for suffix in BANNED_MEDIA_SIDECAR_SUFFIXES)


def _repo_roots(context: Context) -> dict[str, Path]:
    paths = context.channel.get("paths", {})
    return {
        "agents": Path(paths.get("agents_root", context.root)),
        "audio": Path(paths["audio_root"]),
        "viz": Path(paths["viz_root"]),
        "episodes": Path(paths["episodes_root"]),
    }


def _git_path(repo_root: Path, relative_git_path: str) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-path", relative_git_path],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    value = completed.stdout.strip()
    path = Path(value)
    if not path.is_absolute():
        path = repo_root / path
    return path


def run_source_control_media_audit(
    context: Context,
    *,
    output_path: Path | None = None,
) -> dict[str, Any]:
    report_path = output_path or (context.root / DEFAULT_MEDIA_AUDIT_REPORT_RELATIVE_PATH)
    errors: list[dict[str, Any]] = []
    repositories: list[dict[str, Any]] = []

    for name, repo_root in _repo_roots(context).items():
        repo_report: dict[str, Any] = {
            "name": name,
            "path": str(repo_root),
            "is_git_repo": _is_git_repo(repo_root),
            "tracked_banned_files": [],
            "tracked_banned_media_model_files": [],
            "tracked_banned_sidecar_files": [],
            "ignored_or_untracked_banned_files": [],
            "ignored_or_untracked_banned_media_model_files": [],
            "ignored_or_untracked_banned_sidecar_files": [],
        }
        if not repo_report["is_git_repo"]:
            repo_report["skipped_reason"] = "not_git_repo"
            repositories.append(repo_report)
            continue

        tracked_files = _git_ls_files(repo_root)
        ignored_or_untracked_files = _git_ls_files(repo_root, "--others", "--exclude-standard")
        tracked_media_model = [path for path in tracked_files if _is_banned_path(path)]
        tracked_sidecars = [path for path in tracked_files if _is_banned_sidecar_path(path)]
        ignored_or_untracked_media_model = [path for path in ignored_or_untracked_files if _is_banned_path(path)]
        ignored_or_untracked_sidecars = [path for path in ignored_or_untracked_files if _is_banned_sidecar_path(path)]
        tracked = sorted({*tracked_media_model, *tracked_sidecars})
        ignored_or_untracked = sorted({*ignored_or_untracked_media_model, *ignored_or_untracked_sidecars})
        repo_report["tracked_banned_files"] = tracked
        repo_report["tracked_banned_media_model_files"] = tracked_media_model
        repo_report["tracked_banned_sidecar_files"] = tracked_sidecars
        repo_report["ignored_or_untracked_banned_files"] = ignored_or_untracked
        repo_report["ignored_or_untracked_banned_media_model_files"] = ignored_or_untracked_media_model
        repo_report["ignored_or_untracked_banned_sidecar_files"] = ignored_or_untracked_sidecars
        repositories.append(repo_report)

        for path in tracked_media_model:
            errors.append(
                {
                    "code": "tracked_banned_media_or_model_asset",
                    "repo": name,
                    "path": str(repo_root / path),
                    "message": "Git tracks a media/model asset that should remain local, generated, or archived.",
                }
            )
        for path in tracked_sidecars:
            errors.append(
                {
                    "code": "tracked_generated_media_sidecar",
                    "repo": name,
                    "path": str(repo_root / path),
                    "message": "Git tracks a generated media sidecar manifest that should remain local, generated, or archived.",
                }
            )

    report = {
        "schema_version": "1.0",
        "report_path": str(report_path),
        "banned_extensions": sorted(BANNED_MEDIA_MODEL_EXTENSIONS),
        "banned_sidecar_suffixes": sorted(BANNED_MEDIA_SIDECAR_SUFFIXES),
        "repositories": repositories,
        "errors": errors,
        "error_count": len(errors),
        "ok": not errors,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _source_media_pre_commit_hook(agents_root: Path, previous_hook_path: Path) -> str:
    helper = agents_root / "bin" / "ce-orchestrate"
    return f"""#!/usr/bin/env bash
# {SOURCE_MEDIA_HOOK_MARKER}
set -euo pipefail

previous_hook={str(previous_hook_path)!r}
if [ -x "${{previous_hook}}" ]; then
  "${{previous_hook}}" "$@"
fi

exec {str(helper)!r} source-media-audit
"""


def install_source_media_pre_commit_hooks(context: Context) -> dict[str, Any]:
    agents_root = Path(context.channel.get("paths", {}).get("agents_root", context.root)).resolve()
    installed: list[dict[str, Any]] = []

    for name, repo_root in _repo_roots(context).items():
        repo_root = repo_root.resolve()
        repo_result: dict[str, Any] = {
            "name": name,
            "path": str(repo_root),
            "is_git_repo": _is_git_repo(repo_root),
            "hook_path": None,
            "previous_hook_path": None,
            "previous_hook_preserved": False,
            "installed": False,
        }
        if not repo_result["is_git_repo"]:
            repo_result["skipped_reason"] = "not_git_repo"
            installed.append(repo_result)
            continue

        hook_path = _git_path(repo_root, "hooks/pre-commit")
        previous_hook_path = hook_path.parent / PREVIOUS_PRE_COMMIT_HOOK_NAME
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        repo_result["hook_path"] = str(hook_path)
        repo_result["previous_hook_path"] = str(previous_hook_path)

        if hook_path.exists():
            existing = hook_path.read_text(encoding="utf-8", errors="replace")
            if SOURCE_MEDIA_HOOK_MARKER not in existing and not previous_hook_path.exists():
                shutil.copy2(hook_path, previous_hook_path)
                previous_hook_path.chmod(previous_hook_path.stat().st_mode | 0o111)
                repo_result["previous_hook_preserved"] = True

        hook_path.write_text(_source_media_pre_commit_hook(agents_root, previous_hook_path), encoding="utf-8")
        hook_path.chmod(hook_path.stat().st_mode | 0o111)
        repo_result["installed"] = True
        installed.append(repo_result)

    return {
        "schema_version": "1.0",
        "hook_marker": SOURCE_MEDIA_HOOK_MARKER,
        "repositories": installed,
        "installed_count": sum(1 for item in installed if item.get("installed")),
    }


__all__ = [
    "BANNED_MEDIA_MODEL_EXTENSIONS",
    "BANNED_MEDIA_SIDECAR_SUFFIXES",
    "install_source_media_pre_commit_hooks",
    "run_source_control_media_audit",
]
