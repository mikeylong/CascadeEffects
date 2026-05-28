#!/usr/bin/env python3
"""Validate that Cascade Effects video artifacts do not use Paper Architecture."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_long_form_visual_style import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
