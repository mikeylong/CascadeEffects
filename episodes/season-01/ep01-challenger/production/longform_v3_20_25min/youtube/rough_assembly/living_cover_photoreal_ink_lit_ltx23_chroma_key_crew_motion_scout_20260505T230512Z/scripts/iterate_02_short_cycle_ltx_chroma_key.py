#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_SCRIPT = SCRIPT_DIR / "build_ltx23_chroma_key_crew_motion_scout.py"
spec = importlib.util.spec_from_file_location("chroma_builder", BASE_SCRIPT)
builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


ITERATION_ID = "iteration_02"
FRAMES_REQUESTED = 49
EXPECTED_RAW_FRAMES = 48
STEPS = 4
HALF_LOOP_FRAMES = 144
LOOP_FRAMES = 288
RAW_QA_FRAMES = [0, 12, 24, 36, 47]
LOOP_QA_FRAMES = [0, 72, 144, 216, 287]


@dataclass(frozen=True)
class IterCandidate:
    id: str
    label: str
    seed: int
    cfg_scale: float
    stg_scale: float
    prompt_variant_id: str
    motion_line: str


CANDIDATES = [
    IterCandidate(
        id="variant_a",
        label="A",
        seed=421337,
        cfg_scale=0.35,
        stg_scale=0.0,
        prompt_variant_id="short_cycle_nearly_still_posture_settle_a",
        motion_line="almost still; tiny independent posture settling only, barely detectable",
    ),
    IterCandidate(
        id="variant_b",
        label="B",
        seed=867530,
        cfg_scale=0.50,
        stg_scale=0.02,
        prompt_variant_id="short_cycle_minimal_detectable_posture_settle_b",
        motion_line="minimal detectable independent posture settling, very slight head set, arms remain down",
    ),
    IterCandidate(
        id="variant_c",
        label="C",
        seed=190721,
        cfg_scale=0.65,
        stg_scale=0.04,
        prompt_variant_id="short_cycle_upper_micro_posture_settle_c",
        motion_line="upper micro-motion; small independent stance settling only, no visible action",
    ),
]


def backup_iteration_01() -> None:
    backup_root = builder.PACKET_ROOT / "iterations" / "iteration_01_failed"
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


def prompt_for(candidate: IterCandidate) -> str:
    return (
        "Locked-off image-to-video of only a green-screen crew plate. Seven astronauts in blue flight suits are seen from behind, "
        "standing in one straight foreground group on a flat pure green background. Preserve the input image composition and silhouettes. "
        f"Motion target: {candidate.motion_line}. "
        "Feet stay planted in exactly the same positions. Arms stay down touching the sides of the body. Hands stay low. "
        "Each person remains facing away from the camera. Only tiny independent balance settling and tiny fabric settling may occur. "
        "The green background stays pure, flat, blank, and unchanged. "
        "Do not create a walk cycle. Do not step. Do not lift hands. Do not raise arms. Do not wave. Do not point. Do not salute. "
        "Do not sway together. Do not turn bodies. Do not turn toward camera. Do not add faces, logos, name patches, words, props, floor, smoke, fire, light effects, shimmer, or camera movement. "
        "No extra people, no missing people, no duplicates, no background scene."
    )


def run_ltx(candidate: IterCandidate, chroma_source_path: Path) -> Path:
    prompt = prompt_for(candidate)
    prompt_path = builder.PACKET_ROOT / "prompts" / ITERATION_ID / f"{candidate.id}_prompt.txt"
    builder.write_text(prompt_path, prompt + "\n")
    ltx_temp = (
        builder.PACKET_ROOT
        / "work"
        / ITERATION_ID
        / "ltx_raw_with_possible_audio"
        / f"{candidate.id}_{ITERATION_ID}_seed{candidate.seed}_raw_chroma_with_possible_audio.mp4"
    )
    raw_chroma = (
        builder.PACKET_ROOT
        / "clips"
        / "raw_chroma_crew"
        / f"{candidate.id}_{ITERATION_ID}_seed{candidate.seed}_raw_chroma_crew.mp4"
    )
    ltx_temp.parent.mkdir(parents=True, exist_ok=True)
    raw_chroma.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(builder.LTX_BIN),
        "generate",
        "--prompt",
        prompt,
        "--output",
        str(ltx_temp),
        "--model",
        builder.MODEL_REPO,
        "--gemma",
        builder.TEXT_ENCODER_REPO,
        "--seed",
        str(candidate.seed),
        "--height",
        str(builder.HEIGHT),
        "--width",
        str(builder.WIDTH),
        "--frames",
        str(FRAMES_REQUESTED),
        "--image",
        str(chroma_source_path),
        "--steps",
        str(STEPS),
        "--cfg-scale",
        str(candidate.cfg_scale),
        "--stg-scale",
        str(candidate.stg_scale),
    ]
    builder.run(
        command,
        cwd=builder.LTX_RUNTIME_ROOT,
        env=builder.ltx_env(),
        log_path=builder.PACKET_ROOT / "logs" / f"{candidate.id}_{ITERATION_ID}_ltx23_generate.log",
    )
    builder.strip_audio_and_normalize(ltx_temp, raw_chroma, width=builder.WIDTH, height=builder.HEIGHT, frames=EXPECTED_RAW_FRAMES)
    ltx_temp.unlink(missing_ok=True)
    return raw_chroma


def make_stretched_pingpong(raw_frame_paths: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    usable = raw_frame_paths[:EXPECTED_RAW_FRAMES]
    if len(usable) != EXPECTED_RAW_FRAMES:
        raise RuntimeError(f"Expected {EXPECTED_RAW_FRAMES} raw frames, got {len(usable)}")
    half: list[Path] = []
    for index in range(HALF_LOOP_FRAMES):
        src_index = round(index * (EXPECTED_RAW_FRAMES - 1) / (HALF_LOOP_FRAMES - 1))
        output = output_dir / f"half_{index:04d}.png"
        shutil.copyfile(usable[src_index], output)
        half.append(output)
    sequence = half + list(reversed(half))
    loop_paths: list[Path] = []
    for index, frame_path in enumerate(sequence):
        output = output_dir / f"frame_{index:04d}.png"
        shutil.copyfile(frame_path, output)
        loop_paths.append(output)
    return loop_paths


def render_candidate(candidate: IterCandidate, chroma_source_path: Path, no_crew_plate_path: Path) -> dict[str, Any]:
    raw_chroma = run_ltx(candidate, chroma_source_path)
    raw_frames = builder.extract_all_frames(raw_chroma, builder.PACKET_ROOT / "work" / ITERATION_ID / "raw_chroma_frames" / candidate.id)
    loop_chroma_frames = make_stretched_pingpong(
        raw_frames,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_chroma_frames" / candidate.id,
    )
    keyed_dirs = builder.key_and_composite_frames(
        loop_chroma_frames,
        no_crew_plate_path,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_keyed_frames" / candidate.id,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_matte_frames" / candidate.id,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_full_frame_frames" / candidate.id,
        builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_crew_crop_frames" / candidate.id,
    )

    loop_chroma = builder.PACKET_ROOT / "clips" / "loop_chroma_crew" / f"{candidate.id}_{ITERATION_ID}_chroma_key_crew_loop_12s.mp4"
    loop_keyed = builder.PACKET_ROOT / "clips" / "loop_keyed_alpha_preview" / f"{candidate.id}_{ITERATION_ID}_keyed_alpha_preview_loop_12s.mp4"
    loop_composite = builder.PACKET_ROOT / "clips" / "loop_composited_full_frame" / f"{candidate.id}_{ITERATION_ID}_chroma_key_composited_full_frame_loop_12s.mp4"
    preview = builder.PACKET_ROOT / "clips" / "loop_preview_3x" / f"{candidate.id}_{ITERATION_ID}_chroma_key_composited_full_frame_3x_preview.mp4"
    builder.encode_frames(builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_chroma_frames" / candidate.id, loop_chroma, width=builder.WIDTH, height=builder.HEIGHT)
    builder.encode_frames(builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_keyed_frames" / candidate.id, loop_keyed, width=builder.WIDTH, height=builder.HEIGHT)
    builder.encode_frames(builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_full_frame_frames" / candidate.id, loop_composite, width=builder.FULL_WIDTH, height=builder.FULL_HEIGHT)
    builder.make_three_loop_preview(loop_composite, preview, width=builder.FULL_WIDTH, height=builder.FULL_HEIGHT)

    qa: dict[str, list[Path]] = {
        "raw_chroma_crew": [],
        "matte": [],
        "composited_full_frame": [],
        "crew_crop": [],
        "loop_seam": [],
        "preview_3loop_seam": [],
    }
    for frame_index in RAW_QA_FRAMES:
        output = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "raw_chroma_crew" / candidate.id / f"{candidate.id}_raw_chroma_{frame_index:03d}.png"
        builder.extract_frame(raw_chroma, frame_index, output)
        qa["raw_chroma_crew"].append(output)
    for frame_index in LOOP_QA_FRAMES:
        matte_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "matte" / candidate.id / f"{candidate.id}_matte_{frame_index:03d}.png"
        full_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "composited_full_frame" / candidate.id / f"{candidate.id}_full_{frame_index:03d}.png"
        crew_out = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "crew_crop" / candidate.id / f"{candidate.id}_crew_crop_{frame_index:03d}.png"
        builder.copy_sequence_frame(keyed_dirs["matte"], frame_index, matte_out)
        builder.copy_sequence_frame(keyed_dirs["full"], frame_index, full_out)
        builder.copy_sequence_frame(keyed_dirs["crew_crop"], frame_index, crew_out)
        qa["matte"].append(matte_out)
        qa["composited_full_frame"].append(full_out)
        qa["crew_crop"].append(crew_out)
    for index, frame_index in enumerate(builder.SEAM_QA_FRAMES):
        output = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "loop_seam" / candidate.id / f"{candidate.id}_seam_{index:02d}_frame_{frame_index:03d}.png"
        builder.copy_sequence_frame(keyed_dirs["crew_crop"], frame_index, output)
        qa["loop_seam"].append(output)
    for frame_index in builder.PREVIEW_SEAM_QA_FRAMES:
        output = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "preview_3loop_seam" / candidate.id / f"{candidate.id}_preview_{frame_index:03d}.png"
        full_tmp = builder.PACKET_ROOT / "work" / ITERATION_ID / "preview_extract" / candidate.id / f"{candidate.id}_preview_full_{frame_index:03d}.png"
        builder.extract_frame(preview, frame_index, full_tmp)
        output.parent.mkdir(parents=True, exist_ok=True)
        from PIL import Image

        Image.open(full_tmp).convert("RGB").crop(builder.CREW_CROP_BOX).save(output)
        qa["preview_3loop_seam"].append(output)

    prompt_path = builder.PACKET_ROOT / "prompts" / ITERATION_ID / f"{candidate.id}_prompt.txt"
    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "iteration": ITERATION_ID,
        "seed": candidate.seed,
        "prompt_variant_id": candidate.prompt_variant_id,
        "cfg_scale": candidate.cfg_scale,
        "stg_scale": candidate.stg_scale,
        "steps": STEPS,
        "frames_requested": FRAMES_REQUESTED,
        "raw_frames_after_normalization": EXPECTED_RAW_FRAMES,
        "loop_construction": "48_frame_ltx_generated_short_cycle_stretched_to_144_frame_half_cycle_then_forward_reverse_ping_pong",
        "prompt_text": prompt_path.read_text(encoding="utf-8").strip(),
        "prompt_path": str(prompt_path),
        "prompt_sha256": builder.sha256(prompt_path),
        "ltx_invocation": {
            "runtime": str(builder.LTX_BIN),
            "model": builder.MODEL_REPO,
            "gemma": builder.TEXT_ENCODER_REPO,
            "width": builder.WIDTH,
            "height": builder.HEIGHT,
            "frames": FRAMES_REQUESTED,
            "steps": STEPS,
            "cfg_scale": candidate.cfg_scale,
            "stg_scale": candidate.stg_scale,
            "enhance_prompt": False,
            "pipeline": "one_stage",
        },
        "raw_chroma_crew_clip": builder.video_summary(raw_chroma),
        "loop_chroma_crew_clip": builder.video_summary(loop_chroma),
        "loop_keyed_alpha_preview_clip": builder.video_summary(loop_keyed),
        "loop_composited_full_frame_clip": builder.video_summary(loop_composite),
        "preview_3loop_clip": builder.video_summary(preview),
        "qa_frames": {key: [builder.artifact(path) for path in paths] for key, paths in qa.items()},
        "machine_motion_probe": {
            "crew_crop_motion_delta_score": builder.motion_delta_score(qa["crew_crop"]),
            "hand_raise_probe": builder.hand_raise_probe(qa["crew_crop"]),
            "note": "Machine probes are coarse screening only; human review is authoritative for hand waving, synchronized motion, subtlety, and uncanny motion.",
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
        "- `iteration_01` failed internal visual review: LTX drifted into walking/raised-arm gestures and background noise.\n"
        "- `iteration_02` uses a shorter generated LTX cycle, lower CFG/STG, and a stretched forward/reverse loop to keep motion generated but constrained.\n"
    )
    review = builder.build_review(manifest)
    review = review.replace(
        "## What Changed\n\n",
        "## What Changed\n\n"
        "- Internal `iteration_01` was not presented as a keeper set because contact sheets showed waving/walking/action-scale drift.\n"
        "- This presented set is `iteration_02`, using a shorter generated LTX cycle and lower motion energy.\n",
    )
    builder.write_text(builder.PACKET_ROOT / "README.md", readme)
    builder.write_text(builder.PACKET_ROOT / "review" / "motion_scout_review_packet.md", review)


def main() -> None:
    backup_iteration_01()
    manifest_path = builder.PACKET_ROOT / "motion_scout_manifest.json"
    manifest = builder.read_json(manifest_path)
    chroma_source_path = Path(manifest["source_visual"]["crew_chroma_source"]["chroma_source"]["path"])
    no_crew_plate_path = Path(manifest["source_visual"]["no_crew_plate"]["plate"]["path"])
    no_crew_payload = manifest["source_visual"]["no_crew_plate"]
    chroma_payload = manifest["source_visual"]["crew_chroma_source"]
    candidate_payloads = [render_candidate(candidate, chroma_source_path, no_crew_plate_path) for candidate in CANDIDATES]
    contact_sheets = builder.make_contact_sheets(candidate_payloads, no_crew_payload, chroma_payload)

    manifest["candidates"] = candidate_payloads
    manifest["contact_sheets"] = {key: builder.artifact(path) for key, path in contact_sheets.items()}
    manifest["ltx_runtime"]["frames"] = FRAMES_REQUESTED
    manifest["ltx_runtime"]["steps"] = STEPS
    manifest["loop_contract"].update(
        {
            "raw_half_cycle_seconds": 2.0,
            "raw_half_cycle_frames_after_normalization": EXPECTED_RAW_FRAMES,
            "loop_method": "short_ltx_cycle_stretched_to_6s_then_forward_reverse_ping_pong",
            "loop_frames": LOOP_FRAMES,
            "iterations_attempted": 2,
            "presented_iteration": ITERATION_ID,
            "iteration_01_result": "failed_internal_visual_review_hand_gesture_and_walk_cycle_drift",
            "iteration_02_change": "lower_cfg_lower_stg_shorter_ltx_generation_to_avoid_late_sequence_action_drift",
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
            "iteration": ITERATION_ID,
            "result": "presented_for_human_review",
            "change": "short LTX generation window, lower motion energy, stretched generated motion into 12s loop",
        },
    ]
    all_no_audio = all(
        not item["raw_chroma_crew_clip"]["has_audio"]
        and not item["loop_chroma_crew_clip"]["has_audio"]
        and not item["loop_keyed_alpha_preview_clip"]["has_audio"]
        and not item["loop_composited_full_frame_clip"]["has_audio"]
        and not item["preview_3loop_clip"]["has_audio"]
        for item in candidate_payloads
    )
    loop_duration_ok = all(11.9 <= float(item["loop_composited_full_frame_clip"]["duration_seconds"]) <= 12.1 for item in candidate_payloads)
    preview_duration_ok = all(35.8 <= float(item["preview_3loop_clip"]["duration_seconds"]) <= 36.2 for item in candidate_payloads)
    manifest["motion_scout_reads"]["raw_chroma_audio_read"] = "pass_no_audio" if all_no_audio else "reject_audio_present"
    manifest["motion_scout_reads"]["loop_duration_read"] = "pass_12s" if loop_duration_ok else "tighten_duration_not_12s"
    manifest["motion_scout_reads"]["preview_3loop_duration_read"] = "pass_36s" if preview_duration_ok else "tighten_duration_not_36s"
    manifest["motion_scout_reads"]["contact_sheet_read"] = "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet"
    manifest["next_review_question"] = "Review A/B/C and reply with exactly one response: keep A, keep B, keep C, tighten, or reject."
    builder.write_json(manifest_path, manifest)
    update_docs(manifest)
    manifest["artifacts"]["readme"] = builder.artifact(builder.PACKET_ROOT / "README.md")
    manifest["artifacts"]["review_packet"] = builder.artifact(builder.PACKET_ROOT / "review" / "motion_scout_review_packet.md")
    manifest["artifacts"]["iteration_02_script"] = builder.artifact(Path(__file__))
    for key, path in contact_sheets.items():
        manifest["artifacts"][key] = builder.artifact(path)
    builder.write_json(manifest_path, manifest)
    print(json.dumps({"packet_root": str(builder.PACKET_ROOT), "presented_iteration": ITERATION_ID}, indent=2))


if __name__ == "__main__":
    main()
