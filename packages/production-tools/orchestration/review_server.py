from __future__ import annotations

from types import ModuleType

from orchestration.review_bridge import load_review_module


def _load_inbox_review_server_module() -> ModuleType:
    return load_review_module("review_server")


_MODULE = _load_inbox_review_server_module()
__all__ = list(getattr(_MODULE, "__all__", ()))

for _name in __all__:
    globals()[_name] = getattr(_MODULE, _name)
