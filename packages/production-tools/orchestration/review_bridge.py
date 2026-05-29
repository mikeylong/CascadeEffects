from __future__ import annotations

import os
import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType


PRODUCTION_TOOLS_ROOT = Path(__file__).resolve().parents[1]
MONOREPO_ROOT = PRODUCTION_TOOLS_ROOT.parents[1]
REVIEW_APP_ROOT = MONOREPO_ROOT / "apps" / "review"
REVIEW_CLI_HELPER_PATH = REVIEW_APP_ROOT / "bin" / "ce-inbox"


def ensure_review_bridge_paths() -> None:
    if not REVIEW_APP_ROOT.exists():
        raise SystemExit(f"Review app is missing: {REVIEW_APP_ROOT}")
    for root in (PRODUCTION_TOOLS_ROOT, REVIEW_APP_ROOT):
        rendered = str(root)
        if rendered not in sys.path:
            sys.path.insert(0, rendered)


def load_review_module(module_name: str) -> ModuleType:
    ensure_review_bridge_paths()
    return import_module(f"inbox_app.{module_name}")


def review_cli_helper_path() -> Path:
    return REVIEW_CLI_HELPER_PATH


def review_cli_environment() -> dict[str, str]:
    env = os.environ.copy()
    python_paths = [str(REVIEW_APP_ROOT), str(PRODUCTION_TOOLS_ROOT)]
    existing = env.get("PYTHONPATH")
    if existing:
        python_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    return env
