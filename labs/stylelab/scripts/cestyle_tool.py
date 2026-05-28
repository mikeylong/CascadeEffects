from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from stylelab.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
