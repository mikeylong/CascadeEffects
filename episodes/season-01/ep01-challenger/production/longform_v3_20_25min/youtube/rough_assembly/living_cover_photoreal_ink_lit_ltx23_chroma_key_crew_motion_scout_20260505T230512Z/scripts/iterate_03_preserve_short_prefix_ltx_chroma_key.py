#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ITER2_SCRIPT = SCRIPT_DIR / "iterate_02_short_cycle_ltx_chroma_key.py"
spec = importlib.util.spec_from_file_location("iter2", ITER2_SCRIPT)
iter2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = iter2
spec.loader.exec_module(iter2)
builder = iter2.builder


def backup_current_iteration_02() -> None:
    backup_root = builder.PACKET_ROOT / "iterations" / "iteration_02_failed"
    for subdir in ["contact_sheets", "candidates"]:
        dest = backup_root / subdir
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
    if (builder.PACKET_ROOT / "motion_scout_manifest.json").exists():
        shutil.copyfile(builder.PACKET_ROOT / "motion_scout_manifest.json", backup_root / "motion_scout_manifest_snapshot.json")
    for path in (builder.PACKET_ROOT / "qa" / "contact_sheets").glob("*.jpg"):
        shutil.copyfile(path, backup_root / "contact_sheets" / path.name)
    for path in (builder.PACKET_ROOT / "candidates").glob("*.json"):
        shutil.copyfile(path, backup_root / "candidates" / path.name)


def write_iteration_03_docs(manifest: dict) -> None:
    readme = builder.build_readme(manifest)
    readme += (
        "\n## Internal Iteration Notes\n\n"
        "- `iteration_01` failed internal visual review: LTX drifted into walking/raised-arm gestures and background noise.\n"
        "- `iteration_02` failed internal visual review: very low CFG/STG collapsed the crew plate into chroma/noise artifacts.\n"
        "- `iteration_03` is the presented set: higher image preservation, a one-second LTX-generated stable prefix, and a stretched forward/reverse 12s loop.\n"
    )
    review = builder.build_review(manifest)
    review = review.replace(
        "## What Changed\n\n",
        "## What Changed\n\n"
        "- Internal `iteration_01` was not presented as a keeper set because contact sheets showed waving/walking/action-scale drift.\n"
        "- Internal `iteration_02` was not presented because lower guidance collapsed the keyed crew layer into noise.\n"
        "- This presented A/B/C set is `iteration_03`, using a shorter LTX-generated stable prefix with stronger image preservation.\n",
    )
    builder.write_text(builder.PACKET_ROOT / "README.md", readme)
    builder.write_text(builder.PACKET_ROOT / "review" / "motion_scout_review_packet.md", review)


def patch_manifest() -> None:
    manifest_path = builder.PACKET_ROOT / "motion_scout_manifest.json"
    manifest = builder.read_json(manifest_path)
    manifest["loop_contract"].update(
        {
            "raw_half_cycle_seconds": 1.0,
            "raw_half_cycle_frames_after_normalization": 24,
            "loop_method": "short_ltx_stable_prefix_stretched_to_6s_then_forward_reverse_ping_pong",
            "iterations_attempted": 3,
            "presented_iteration": "iteration_03",
            "iteration_01_result": "failed_internal_visual_review_hand_gesture_and_walk_cycle_drift",
            "iteration_02_result": "failed_internal_visual_review_chroma_noise_collapse",
            "iteration_03_change": "higher_image_preservation_shorter_ltx_generated_stable_prefix",
        }
    )
    manifest["internal_iterations"] = [
        {
            "iteration": "iteration_01",
            "result": "failed_internal_visual_review",
            "blockers": [
                "hand_waving_or_raised_arm_drift",
                "walking_or_step_cycle_drift",
                "background_noise_inside_chroma_source",
            ],
            "metadata_snapshot": str(builder.PACKET_ROOT / "iterations" / "iteration_01_failed" / "motion_scout_manifest_snapshot.json"),
            "contact_sheet_backup_dir": str(builder.PACKET_ROOT / "iterations" / "iteration_01_failed" / "contact_sheets"),
        },
        {
            "iteration": "iteration_02",
            "result": "failed_internal_visual_review",
            "blockers": [
                "chroma_noise_collapse",
                "matte_noise",
                "crew_layer_not_reviewable_after_first_frames",
            ],
            "metadata_snapshot": str(builder.PACKET_ROOT / "iterations" / "iteration_02_failed" / "motion_scout_manifest_snapshot.json"),
            "contact_sheet_backup_dir": str(builder.PACKET_ROOT / "iterations" / "iteration_02_failed" / "contact_sheets"),
        },
        {
            "iteration": "iteration_03",
            "result": "presented_for_human_review",
            "change": "short LTX-generated stable prefix, stronger image preservation, stretched generated motion into 12s loop",
        },
    ]
    manifest["artifacts"]["readme"] = builder.artifact(builder.PACKET_ROOT / "README.md")
    manifest["artifacts"]["review_packet"] = builder.artifact(builder.PACKET_ROOT / "review" / "motion_scout_review_packet.md")
    manifest["artifacts"]["iteration_03_script"] = builder.artifact(Path(__file__))
    builder.write_json(manifest_path, manifest)
    write_iteration_03_docs(manifest)
    manifest["artifacts"]["readme"] = builder.artifact(builder.PACKET_ROOT / "README.md")
    manifest["artifacts"]["review_packet"] = builder.artifact(builder.PACKET_ROOT / "review" / "motion_scout_review_packet.md")
    builder.write_json(manifest_path, manifest)


def main() -> None:
    backup_current_iteration_02()
    iter2.ITERATION_ID = "iteration_03"
    iter2.FRAMES_REQUESTED = 25
    iter2.EXPECTED_RAW_FRAMES = 24
    iter2.STEPS = 8
    iter2.RAW_QA_FRAMES = [0, 6, 12, 18, 23]
    iter2.CANDIDATES = [
        iter2.IterCandidate(
            id="variant_a",
            label="A",
            seed=112358,
            cfg_scale=0.85,
            stg_scale=0.08,
            prompt_variant_id="preserve_short_prefix_barely_detectable_a",
            motion_line="barely detectable idle posture settling; preserve the input silhouettes",
        ),
        iter2.IterCandidate(
            id="variant_b",
            label="B",
            seed=271828,
            cfg_scale=0.95,
            stg_scale=0.10,
            prompt_variant_id="preserve_short_prefix_minimal_living_motion_b",
            motion_line="minimal independent living-cover posture settling; tiny head set only, arms remain down",
        ),
        iter2.IterCandidate(
            id="variant_c",
            label="C",
            seed=314159,
            cfg_scale=1.05,
            stg_scale=0.12,
            prompt_variant_id="preserve_short_prefix_upper_micro_motion_c",
            motion_line="upper micro-motion but still planted; tiny shoulder and stance settling only",
        ),
    ]
    iter2.backup_iteration_01 = lambda: None
    iter2.main()
    patch_manifest()


if __name__ == "__main__":
    main()
