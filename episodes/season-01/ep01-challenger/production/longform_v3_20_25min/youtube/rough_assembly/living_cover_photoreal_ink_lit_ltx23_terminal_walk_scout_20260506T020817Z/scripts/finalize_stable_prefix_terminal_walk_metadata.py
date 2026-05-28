#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_SCRIPT = SCRIPT_DIR / "build_terminal_walk_scout.py"
spec = importlib.util.spec_from_file_location("terminal_builder", BASE_SCRIPT)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def main() -> None:
    manifest_path = builder.PACKET_ROOT / "terminal_walk_manifest.json"
    manifest = builder.read_json(manifest_path)
    for item in manifest["candidates"]:
        if "seed" not in item and "source_seed" in item:
            item["seed"] = item["source_seed"]
    for candidate_path in (builder.PACKET_ROOT / "candidates").glob("variant_*.json"):
        data = builder.read_json(candidate_path)
        if "seed" not in data and "source_seed" in data:
            data["seed"] = data["source_seed"]
        builder.write_json(candidate_path, data)
    readme = builder.build_readme(manifest)
    readme += (
        "\n## Internal Iteration Notes\n\n"
        "- Full 12s LTX generations are retained as diagnostic metadata but are not the presented keeper set: late frames introduced green-screen background drift and raised-arm gestures.\n"
        "- The presented A/B/C set uses stable LTX-generated walking prefix frames, stretched once to the 12s terminal-walk duration.\n"
        "- This is still an LTX-generated terminal-walk carrier; no sprite overlay, deterministic deformation, full-runtime HTML proof, or full-runtime MP4 was created.\n"
    )
    review = builder.build_review(manifest)
    review = review.replace(
        "## What Changed\n\n",
        "## What Changed\n\n"
        "- Full 12s LTX generations were internally rejected as presentation candidates because the later frames drifted into background artifacts and raised-arm gestures.\n"
        "- This presented set uses stable LTX-generated walking prefix frames stretched once to the 12s terminal-walk duration.\n",
    )
    builder.write_text(builder.PACKET_ROOT / "README.md", readme)
    builder.write_text(builder.PACKET_ROOT / "review" / "terminal_walk_review_packet.md", review)
    manifest.setdefault("artifacts", {})
    manifest["artifacts"]["readme"] = builder.artifact(builder.PACKET_ROOT / "README.md")
    manifest["artifacts"]["review_packet"] = builder.artifact(builder.PACKET_ROOT / "review" / "terminal_walk_review_packet.md")
    manifest["artifacts"]["metadata_finalizer_script"] = builder.artifact(Path(__file__))
    builder.write_json(manifest_path, manifest)
    print({"manifest_path": str(manifest_path), "status": manifest["status"]})


if __name__ == "__main__":
    main()
