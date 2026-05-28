from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType


def _load_inbox_review_module() -> ModuleType:
    inbox_root = Path(__file__).resolve().parents[2] / "Inbox_CascadeEffects"
    if not inbox_root.exists():
        raise SystemExit(f"Inbox_CascadeEffects is missing: {inbox_root}")
    rendered = str(inbox_root)
    if rendered not in sys.path:
        sys.path.insert(0, rendered)
    return import_module("inbox_app.review")


_MODULE = _load_inbox_review_module()
__all__ = list(getattr(_MODULE, "__all__", ()))

for _name in __all__:
    globals()[_name] = getattr(_MODULE, _name)
