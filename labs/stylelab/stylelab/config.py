from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    repo_root: Path
    ai_root: Path
    models_root: Path
    renders_root: Path
    exports_root: Path
    boards_root: Path
    evaluations_root: Path
    scenes_root: Path
    profiles_root: Path
    references_root: Path
    shorts_root: Path
    stylelab_python: Path


def load_runtime(repo_root: Path) -> RuntimeConfig:
    ai_root = Path(os.environ.get("CE_HOME", "/Users/mike/AI")).expanduser()
    return RuntimeConfig(
        repo_root=repo_root,
        ai_root=ai_root,
        models_root=Path(os.environ.get("CE_MODELS_ROOT", str(ai_root / "models"))).expanduser(),
        renders_root=repo_root / "renders",
        exports_root=repo_root / "exports",
        boards_root=repo_root / "boards",
        evaluations_root=repo_root / "evaluations",
        scenes_root=repo_root / "scenes",
        profiles_root=repo_root / "profiles",
        references_root=repo_root / "references",
        shorts_root=repo_root / "shorts",
        stylelab_python=Path(
            os.environ.get("CE_STYLELAB_PYTHON", "/Users/mike/AI/mlx-video/.venv/bin/python")
        ).expanduser(),
    )


def ensure_runtime_dirs(runtime: RuntimeConfig) -> None:
    for path in (
        runtime.renders_root,
        runtime.exports_root,
        runtime.boards_root,
        runtime.evaluations_root,
        runtime.references_root,
        runtime.shorts_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
