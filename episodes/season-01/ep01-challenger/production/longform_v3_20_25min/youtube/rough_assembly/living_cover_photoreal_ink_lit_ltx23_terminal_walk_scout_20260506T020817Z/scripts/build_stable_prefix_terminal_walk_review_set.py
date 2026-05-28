#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_SCRIPT = SCRIPT_DIR / "build_terminal_walk_scout.py"
spec = importlib.util.spec_from_file_location("terminal_builder", BASE_SCRIPT)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


ITERATION_ID = "stable_generated_walk_prefix"
NORMALIZED_FRAMES = 288
RAW_QA_FRAMES = [0, 36, 72, 144, 216, 287]
WALK_QA_FRAMES = [0, 36, 72, 144, 216, 287]
TRANSITION_QA_FRAMES = [0, 24, 47, 48, 60, 84, 120, 180, 240, 335]


@dataclass(frozen=True)
class PrefixCandidate:
    id: str
    label: str
    source_candidate: str
    source_seed: int
    prefix_last_frame: int
    cfg_scale: float
    stg_scale: float
    prompt_variant_id: str
    motion_note: str


CANDIDATES = [
    PrefixCandidate(
        id="variant_a",
        label="A",
        source_candidate="variant_a",
        source_seed=404101,
        prefix_last_frame=96,
        cfg_scale=1.15,
        stg_scale=0.20,
        prompt_variant_id="stable_prefix_restrained_first_step_a",
        motion_note="restrained first-step cue; minimal travel and no late drift",
    ),
    PrefixCandidate(
        id="variant_b",
        label="B",
        source_candidate="variant_b",
        source_seed=404203,
        prefix_last_frame=120,
        cfg_scale=1.35,
        stg_scale=0.32,
        prompt_variant_id="stable_prefix_clear_calm_walk_start_b",
        motion_note="recommended; clear calm asynchronous walk start with controlled travel",
    ),
    PrefixCandidate(
        id="variant_c",
        label="C",
        source_candidate="variant_b",
        source_seed=404203,
        prefix_last_frame=156,
        cfg_scale=1.35,
        stg_scale=0.32,
        prompt_variant_id="stable_prefix_upper_readable_walk_start_c",
        motion_note="upper readable option from the clean part of candidate B; more travel without using late raised-arm drift",
    ),
]


def backup_full_generation_set() -> None:
    backup_root = builder.PACKET_ROOT / "iterations" / "full_12s_generation_failed"
    for subdir in ["contact_sheets", "candidates"]:
        dest = backup_root / subdir
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
    manifest_path = builder.PACKET_ROOT / "terminal_walk_manifest.json"
    if manifest_path.exists():
        shutil.copyfile(manifest_path, backup_root / "terminal_walk_manifest_snapshot.json")
    for path in (builder.PACKET_ROOT / "qa" / "contact_sheets").glob("*.jpg"):
        shutil.copyfile(path, backup_root / "contact_sheets" / path.name)
    for path in (builder.PACKET_ROOT / "candidates").glob("*.json"):
        shutil.copyfile(path, backup_root / "candidates" / path.name)


def prefix_frames(candidate: PrefixCandidate) -> list[Path]:
    source_dir = builder.PACKET_ROOT / "work" / "raw_chroma_frames" / candidate.source_candidate
    frames = [source_dir / f"frame_{index:04d}.png" for index in range(candidate.prefix_last_frame + 1)]
    missing = [path for path in frames if not path.exists()]
    if missing:
        raise FileNotFoundError(missing[0])
    return frames


def make_stretched_walk(prefix: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output: list[Path] = []
    for index in range(NORMALIZED_FRAMES):
        src_index = round(index * (len(prefix) - 1) / (NORMALIZED_FRAMES - 1)) if len(prefix) > 1 else 0
        path = output_dir / f"frame_{index:04d}.png"
        shutil.copyfile(prefix[src_index], path)
        output.append(path)
    return output


def render_candidate(candidate: PrefixCandidate, no_crew_plate: Path, static_full_frame: Path) -> dict[str, Any]:
    prefix = prefix_frames(candidate)
    raw_dir = builder.PACKET_ROOT / "work" / ITERATION_ID / "raw_chroma_frames" / candidate.id
    raw_frames = make_stretched_walk(prefix, raw_dir)
    keyed_dirs = builder.key_and_composite_frames(
        raw_frames,
        no_crew_plate,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "keyed_frames" / candidate.id,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "matte_frames" / candidate.id,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "full_frame_frames" / candidate.id,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "crew_crop_frames" / candidate.id,
    )
    raw_chroma = builder.PACKET_ROOT / "clips" / "raw_chroma_crew" / f"{candidate.id}_{ITERATION_ID}_terminal_walk_raw_chroma_12s.mp4"
    keyed_clip = builder.PACKET_ROOT / "clips" / "keyed_alpha_preview" / f"{candidate.id}_{ITERATION_ID}_terminal_walk_keyed_alpha_preview_12s.mp4"
    composited_clip = builder.PACKET_ROOT / "clips" / "composited_full_frame" / f"{candidate.id}_{ITERATION_ID}_terminal_walk_composited_full_frame_12s.mp4"
    transition_dir = builder.PACKET_ROOT / "work" / ITERATION_ID / "transition_review_frames" / candidate.id
    transition_frames = builder.make_transition_review_frames(static_full_frame, keyed_dirs["full"], transition_dir)
    transition_clip = builder.PACKET_ROOT / "clips" / "transition_review" / f"{candidate.id}_{ITERATION_ID}_static_then_terminal_walk_review_14s.mp4"
    builder.encode_frames(raw_dir, raw_chroma, width=builder.WIDTH, height=builder.HEIGHT)
    builder.encode_frames(builder.PACKET_ROOT / "work" / ITERATION_ID / "keyed_frames" / candidate.id, keyed_clip, width=builder.WIDTH, height=builder.HEIGHT)
    builder.encode_frames(builder.PACKET_ROOT / "work" / ITERATION_ID / "full_frame_frames" / candidate.id, composited_clip, width=builder.FULL_WIDTH, height=builder.FULL_HEIGHT)
    builder.encode_frames(transition_dir, transition_clip, width=builder.FULL_WIDTH, height=builder.FULL_HEIGHT)

    qa: dict[str, list[Path]] = {
        "raw_chroma_crew": [],
        "matte": [],
        "composited_full_frame": [],
        "crew_crop": [],
        "still_to_walk_transition": [],
    }
    for frame_index in RAW_QA_FRAMES:
        raw_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "raw_chroma_crew" / candidate.id / f"{candidate.id}_raw_{frame_index:03d}.png"
        builder.copy_sequence_frame(raw_frames, frame_index, raw_out)
        qa["raw_chroma_crew"].append(raw_out)
    for frame_index in WALK_QA_FRAMES:
        matte_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "matte" / candidate.id / f"{candidate.id}_matte_{frame_index:03d}.png"
        full_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "composited_full_frame" / candidate.id / f"{candidate.id}_full_{frame_index:03d}.png"
        crop_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "crew_crop" / candidate.id / f"{candidate.id}_crew_crop_{frame_index:03d}.png"
        builder.copy_sequence_frame(keyed_dirs["matte"], frame_index, matte_out)
        builder.copy_sequence_frame(keyed_dirs["full"], frame_index, full_out)
        builder.copy_sequence_frame(keyed_dirs["crew_crop"], frame_index, crop_out)
        qa["matte"].append(matte_out)
        qa["composited_full_frame"].append(full_out)
        qa["crew_crop"].append(crop_out)
    for frame_index in TRANSITION_QA_FRAMES:
        transition_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "still_to_walk_transition" / candidate.id / f"{candidate.id}_transition_{frame_index:03d}.png"
        builder.copy_sequence_frame(transition_frames, frame_index, transition_out)
        qa["still_to_walk_transition"].append(transition_out)

    source_prompt = builder.PACKET_ROOT / "prompts" / f"{candidate.source_candidate}_terminal_walk_prompt.txt"
    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "iteration": ITERATION_ID,
        "source_ltx_candidate": candidate.source_candidate,
        "source_seed": candidate.source_seed,
        "source_prefix_first_frame": 0,
        "source_prefix_last_frame": candidate.prefix_last_frame,
        "source_prefix_frame_count": candidate.prefix_last_frame + 1,
        "prompt_variant_id": candidate.prompt_variant_id,
        "motion_note": candidate.motion_note,
        "cfg_scale": candidate.cfg_scale,
        "stg_scale": candidate.stg_scale,
        "steps": builder.STEPS,
        "frames_requested": builder.FRAMES_REQUESTED,
        "frames_after_normalization": NORMALIZED_FRAMES,
        "terminal_walk_duration_seconds": builder.WALK_SECONDS,
        "review_transition_duration_seconds": builder.REVIEW_SECONDS,
        "loop_construction": "stable LTX-generated walking prefix stretched once to 12s; not looped",
        "prompt_path": str(source_prompt),
        "prompt_sha256": builder.sha256(source_prompt) if source_prompt.exists() else None,
        "ltx_invocation": {
            "runtime": str(builder.LTX_BIN),
            "model": builder.MODEL_REPO,
            "gemma": builder.TEXT_ENCODER_REPO,
            "width": builder.WIDTH,
            "height": builder.HEIGHT,
            "frames": builder.FRAMES_REQUESTED,
            "steps": builder.STEPS,
            "cfg_scale": candidate.cfg_scale,
            "stg_scale": candidate.stg_scale,
            "enhance_prompt": False,
            "pipeline": "one_stage",
            "post_generation_selection": "stable walking prefix only, no in-place deformation or sprite overlay",
        },
        "raw_chroma_crew_clip": builder.video_summary(raw_chroma),
        "keyed_alpha_preview_clip": builder.video_summary(keyed_clip),
        "composited_full_frame_clip": builder.video_summary(composited_clip),
        "transition_review_clip": builder.video_summary(transition_clip),
        "qa_frames": {key: [builder.artifact(path) for path in paths] for key, paths in qa.items()},
        "machine_motion_probe": {
            "crew_crop_motion_delta_score": builder.motion_delta_score(qa["crew_crop"]),
            "hand_raise_probe": builder.hand_raise_probe(qa["crew_crop"]),
            "note": "Machine probes are coarse screening only; human review is authoritative for walking authenticity, crew count, hand waving, and synchronized stride.",
        },
        "disposition": "defer",
        "selected_for_full_runtime_html_proof": False,
        "selected_for_full_runtime_html_proof_status": "pending_human_review",
    }
    builder.write_json(builder.PACKET_ROOT / "candidates" / f"{candidate.id}.json", payload)
    return payload


def update_docs(manifest: dict[str, Any]) -> None:
    readme = builder.build_readme(manifest)
    readme += (
        "\n## Internal Iteration Notes\n\n"
        "- Full 12s LTX generations were retained as diagnostic metadata but not presented as the keeper set: late frames introduced green-screen background drift and raised-arm gestures.\n"
        "- The presented A/B/C set uses only stable LTX-generated walking prefix frames, stretched once to the 12s terminal-walk duration.\n"
        "- This is still an LTX-generated terminal-walk carrier; no sprite overlay, deterministic deformation, or full-runtime render was created.\n"
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


def main() -> None:
    backup_full_generation_set()
    manifest_path = builder.PACKET_ROOT / "terminal_walk_manifest.json"
    manifest = builder.read_json(manifest_path)
    input_payload = manifest["source_visual"]["reused_chroma_key_inputs"]
    no_crew_plate = Path(input_payload["no_crew_plate"]["path"])
    static_full_frame = Path(input_payload["static_prewalk_full_frame"]["path"])
    candidate_payloads = [render_candidate(candidate, no_crew_plate, static_full_frame) for candidate in CANDIDATES]
    contact_sheets = builder.make_contact_sheets(candidate_payloads, input_payload)
    manifest["candidates"] = candidate_payloads
    manifest["contact_sheets"] = {key: builder.artifact(path) for key, path in contact_sheets.items()}
    manifest["terminal_walk_contract"]["presented_iteration"] = ITERATION_ID
    manifest["terminal_walk_contract"]["presented_iteration_note"] = "Stable LTX-generated walking prefixes are stretched once to 12s; full generated late frames are not advancement sources."
    manifest["internal_iterations"] = [
        {
            "iteration": "full_12s_generation",
            "result": "failed_internal_visual_review",
            "blockers": [
                "late green-screen background drift",
                "raised-arm_or_waving_gesture_drift",
                "matte grows to include generated background artifacts",
            ],
            "metadata_snapshot": str(builder.PACKET_ROOT / "iterations" / "full_12s_generation_failed" / "terminal_walk_manifest_snapshot.json"),
            "contact_sheet_backup_dir": str(builder.PACKET_ROOT / "iterations" / "full_12s_generation_failed" / "contact_sheets"),
        },
        {
            "iteration": ITERATION_ID,
            "result": "presented_for_human_review",
            "change": "stable generated walking prefixes only, stretched to 12s terminal action",
        },
    ]
    all_no_audio = all(
        not item["raw_chroma_crew_clip"]["has_audio"]
        and not item["keyed_alpha_preview_clip"]["has_audio"]
        and not item["composited_full_frame_clip"]["has_audio"]
        and not item["transition_review_clip"]["has_audio"]
        for item in candidate_payloads
    )
    walk_duration_ok = all(11.9 <= item["composited_full_frame_clip"]["duration_seconds"] <= 12.1 for item in candidate_payloads)
    review_duration_ok = all(13.9 <= item["transition_review_clip"]["duration_seconds"] <= 14.1 for item in candidate_payloads)
    manifest["terminal_walk_reads"]["raw_chroma_audio_read"] = "pass_no_audio" if all_no_audio else "reject_audio_present"
    manifest["terminal_walk_reads"]["terminal_walk_duration_read"] = "pass_12s" if walk_duration_ok else "tighten_duration_not_12s"
    manifest["terminal_walk_reads"]["transition_review_duration_read"] = "pass_14s" if review_duration_ok else "tighten_duration_not_14s"
    manifest["terminal_walk_reads"]["contact_sheet_read"] = "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet"
    builder.write_json(manifest_path, manifest)
    update_docs(manifest)
    manifest["artifacts"]["readme"] = builder.artifact(builder.PACKET_ROOT / "README.md")
    manifest["artifacts"]["review_packet"] = builder.artifact(builder.PACKET_ROOT / "review" / "terminal_walk_review_packet.md")
    manifest["artifacts"]["stable_prefix_review_builder_script"] = builder.artifact(Path(__file__))
    for key, path in contact_sheets.items():
        manifest["artifacts"][key] = builder.artifact(path)
    builder.write_json(manifest_path, manifest)
    print({"packet_root": str(builder.PACKET_ROOT), "presented_iteration": ITERATION_ID})


if __name__ == "__main__":
    main()
