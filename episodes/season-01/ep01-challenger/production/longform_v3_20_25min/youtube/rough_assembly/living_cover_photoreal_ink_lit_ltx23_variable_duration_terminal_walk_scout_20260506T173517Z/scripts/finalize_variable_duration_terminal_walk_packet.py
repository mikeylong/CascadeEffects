#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BUILDER_SCRIPT = SCRIPT_DIR / "build_variable_duration_terminal_walk_scout.py"
spec = importlib.util.spec_from_file_location("variable_duration_builder", BUILDER_SCRIPT)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


FAILED_CELL_ID = "two_stage_distilled_lora_12s"
FAILED_LOG = builder.PACKET_ROOT / "logs" / f"{FAILED_CELL_ID}_ltx23_generate.log"
PRESENTED_CELL_IDS = [
    "one_stage_q8_6s",
    "one_stage_q8_8s",
    "two_stage_distilled_lora_6s",
]


def load_completed_cells() -> list[dict[str, Any]]:
    cells = []
    for path in sorted((builder.PACKET_ROOT / "diagnostics").glob("*.json")):
        data = builder.read_json(path)
        if data.get("cell_id") != FAILED_CELL_ID:
            cells.append(data)
    return cells


def input_payload() -> dict[str, Any]:
    return {
        "no_crew_plate": builder.artifact(builder.PACKET_ROOT / "assets/background_plate/variant_c_aligned_no_crew_plate.png"),
        "no_crew_mask": builder.artifact(builder.PACKET_ROOT / "assets/background_plate/variant_c_no_crew_plate_mask.png"),
        "chroma_source": builder.artifact(builder.PACKET_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_green_screen_source.png"),
        "alpha_reference": builder.artifact(builder.PACKET_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_alpha_reference.png"),
        "source_mask": builder.artifact(builder.PACKET_ROOT / "assets/crew_chroma_source/variant_c_seven_astronauts_source_mask.png"),
        "static_prewalk_full_frame": builder.artifact(builder.PACKET_ROOT / "assets/static_prewalk_full_frame.png"),
    }


def failed_cell_record() -> dict[str, Any]:
    return {
        "cell_id": FAILED_CELL_ID,
        "pipeline_lane": "two_stage_distilled_lora",
        "pipeline_label": "Two-stage distilled-LoRA",
        "duration_seconds": 12,
        "frames_requested": 289,
        "fps": builder.FPS,
        "seed": 511204,
        "cfg_scale": 2.4,
        "stg_scale": 0.70,
        "stage1_steps": 15,
        "stage2_steps": 3,
        "true_duration_no_time_stretch": True,
        "terminal_timing": builder.terminal_start_for_duration(12),
        "diagnostic_disposition": "failed_runtime_after_guided_stage",
        "failure_read": "tighten_two_stage_12s_failed_before_output",
        "failure_note": (
            "The two-stage 12s LTX run completed all 15 guided stage-one denoising steps, then failed at the three-step refinement stage before writing an output. "
            "This is retained as evidence that the 12s horizon is materially harder for the two-stage pipeline at this crop size."
        ),
        "log_path": str(FAILED_LOG),
        "log_sha256": builder.sha256(FAILED_LOG) if FAILED_LOG.exists() else None,
    }


def write_failure_json() -> dict[str, Any]:
    failure = failed_cell_record()
    builder.write_json(builder.PACKET_ROOT / "diagnostics" / f"{FAILED_CELL_ID}.json", failure)
    return failure


def select_presented_cells(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["cell_id"]: item for item in cells}
    selected = [by_id[cell_id] for cell_id in PRESENTED_CELL_IDS]
    labels = ["A", "B", "C"]
    reasons = [
        "Best overall visual pre-screen: 6s one-stage has the clearest natural cadence and no large machine-detected crouch or raised-arm event.",
        "Longer one-stage comparison: 8s tests whether extra runway helps the action read, but it carries a crouch-risk flag for human review.",
        "Best completed distilled-lane diagnostic: 6s two-stage is included to answer the pipeline question; it must be checked for side-facing stride and crouch.",
    ]
    for label, reason, item in zip(labels, reasons, selected):
        item["selected_for_presented_abc"] = True
        item["presented_label"] = label
        item["diagnostic_disposition"] = "presented_for_human_review"
        item["selection_reason"] = reason
    for item in cells:
        if item["cell_id"] not in PRESENTED_CELL_IDS:
            item["selected_for_presented_abc"] = False
            item["presented_label"] = None
            item["diagnostic_disposition"] = "retained_diagnostic_not_presented"
    return selected


def correct_probed_frame_counts(cells: list[dict[str, Any]]) -> None:
    for cell in cells:
        clip = cell.get("composited_full_frame_clip", {})
        try:
            probed = int(clip.get("nb_frames"))
        except (TypeError, ValueError):
            probed = None
        cell["frames_after_normalization"] = probed
        cell["frames_after_normalization_source"] = "ffprobe_composited_full_frame_nb_frames"


def patch_docs(manifest: dict[str, Any]) -> None:
    readme_path = builder.PACKET_ROOT / "README.md"
    review_path = builder.PACKET_ROOT / "review" / "variable_duration_terminal_walk_review_packet.md"
    failure_note = (
        "\n## Diagnostic Failure\n\n"
        "- `two_stage_distilled_lora_12s` failed after completing the guided stage-one denoising and before stage-two output.\n"
        "- The packet remains review-ready because the failure is part of the duration/pipeline test, and the presented A/B/C candidates are selected only from completed true-duration cells.\n"
    )
    for path in [readme_path, review_path]:
        text = path.read_text(encoding="utf-8")
        if "## Diagnostic Failure" not in text:
            path.write_text(text + failure_note, encoding="utf-8")


def main() -> None:
    completed_cells = load_completed_cells()
    if len(completed_cells) != 7:
        raise RuntimeError(f"Expected 7 completed cells before finalizing, found {len(completed_cells)}")
    correct_probed_frame_counts(completed_cells)
    failure = write_failure_json()
    selected = select_presented_cells(completed_cells)
    for cell in completed_cells:
        builder.write_json(builder.PACKET_ROOT / "diagnostics" / f"{cell['cell_id']}.json", cell)
    presented = builder.build_presented_candidate_payloads(selected)
    inputs = input_payload()
    contact_sheets = builder.make_contact_sheets(completed_cells, selected, inputs)
    manifest = builder.build_manifest(inputs, completed_cells, selected, presented, contact_sheets)
    manifest["diagnostic_failures"] = [failure]
    manifest["diagnostic_matrix_contract"]["expected_cell_count"] = 8
    manifest["diagnostic_matrix_contract"]["completed_cell_count"] = len(completed_cells)
    manifest["diagnostic_matrix_contract"]["failed_cell_ids"] = [FAILED_CELL_ID]
    manifest["diagnostic_matrix_contract"]["all_cells_generated"] = False
    manifest["diagnostic_matrix_contract"]["requested_frames_by_duration"] = {"4": 97, "6": 145, "8": 193, "12": 289}
    manifest["diagnostic_matrix_contract"]["normalized_clip_frames_by_duration"] = {"4": 96, "6": 144, "8": 192, "12": 288}
    manifest["variable_duration_reads"]["diagnostic_cell_completion_read"] = "tighten_7_of_8_generated_two_stage_12s_failed"
    manifest["variable_duration_reads"]["two_stage_distilled_read"] = "tighten_4s_6s_8s_completed_12s_failed_at_refinement"
    manifest["variable_duration_reads"]["duration_pipeline_matrix_read"] = "tighten_full_matrix_attempted_two_stage_12s_failed"
    manifest["next_review_question"] = "Review A/B/C selected from completed true-duration cells and reply with exactly one response: keep A, keep B, keep C, tighten, or reject."

    manifest_path = builder.PACKET_ROOT / "variable_duration_terminal_walk_manifest.json"
    readme_path = builder.PACKET_ROOT / "README.md"
    review_path = builder.PACKET_ROOT / "review" / "variable_duration_terminal_walk_review_packet.md"
    builder.write_json(manifest_path, manifest)
    builder.write_text(readme_path, builder.build_readme(manifest))
    builder.write_text(review_path, builder.build_review(manifest))
    patch_docs(manifest)
    manifest["artifacts"] = {
        "manifest": {
            "path": str(manifest_path),
            "sha256": None,
            "bytes": None,
            "hash_note": "Self-referential manifest hash intentionally omitted; validate externally with shasum.",
        },
        "readme": builder.artifact(readme_path),
        "review_packet": builder.artifact(review_path),
        "builder_script": builder.artifact(BUILDER_SCRIPT),
        "finalizer_script": builder.artifact(Path(__file__)),
        **{key: builder.artifact(path) for key, path in contact_sheets.items()},
    }
    builder.write_json(manifest_path, manifest)
    print(json.dumps({"packet_root": str(builder.PACKET_ROOT), "manifest_path": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
