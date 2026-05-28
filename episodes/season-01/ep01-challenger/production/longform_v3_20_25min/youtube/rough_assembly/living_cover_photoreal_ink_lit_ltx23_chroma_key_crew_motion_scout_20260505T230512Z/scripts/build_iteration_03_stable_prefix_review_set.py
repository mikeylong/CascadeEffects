#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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


ITERATION_ID = "iteration_03_stable_prefix"
HALF_LOOP_FRAMES = 144
LOOP_FRAMES = 288
PREFIX_RAW_QA_FRAMES = [0, 6, 12, 18, 23]
LOOP_QA_FRAMES = [0, 72, 144, 216, 287]


@dataclass(frozen=True)
class StablePrefixCandidate:
    id: str
    label: str
    source_raw_candidate: str
    prefix_len: int
    seed: int
    cfg_scale: float
    stg_scale: float
    prompt_variant_id: str
    motion_note: str


CANDIDATES = [
    StablePrefixCandidate(
        id="variant_a",
        label="A",
        source_raw_candidate="variant_a",
        prefix_len=4,
        seed=112358,
        cfg_scale=0.85,
        stg_scale=0.08,
        prompt_variant_id="stable_prefix_barely_detectable_a",
        motion_note="barely detectable generated posture settling; most conservative option",
    ),
    StablePrefixCandidate(
        id="variant_b",
        label="B",
        source_raw_candidate="variant_a",
        prefix_len=8,
        seed=112358,
        cfg_scale=0.85,
        stg_scale=0.08,
        prompt_variant_id="stable_prefix_subtle_detectable_b",
        motion_note="recommended middle path; subtle detectable generated posture settling",
    ),
    StablePrefixCandidate(
        id="variant_c",
        label="C",
        source_raw_candidate="variant_b",
        prefix_len=8,
        seed=271828,
        cfg_scale=0.95,
        stg_scale=0.10,
        prompt_variant_id="stable_prefix_upper_subtle_c",
        motion_note="upper subtle option from the second preserved LTX source; still avoids the later gesture drift",
    ),
]


def stable_prefix_frames(candidate: StablePrefixCandidate) -> list[Path]:
    source_dir = builder.PACKET_ROOT / "work" / "iteration_03" / "raw_chroma_frames" / candidate.source_raw_candidate
    frames = [source_dir / f"frame_{index:04d}.png" for index in range(candidate.prefix_len)]
    missing = [path for path in frames if not path.exists()]
    if missing:
        raise FileNotFoundError(missing[0])
    return frames


def make_stretched_half(prefix: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    half: list[Path] = []
    for index in range(HALF_LOOP_FRAMES):
        src_index = round(index * (len(prefix) - 1) / (HALF_LOOP_FRAMES - 1)) if len(prefix) > 1 else 0
        output = output_dir / f"half_{index:04d}.png"
        shutil.copyfile(prefix[src_index], output)
        half.append(output)
    loop = half + list(reversed(half))
    loop_paths: list[Path] = []
    for index, frame_path in enumerate(loop):
        output = output_dir / f"frame_{index:04d}.png"
        shutil.copyfile(frame_path, output)
        loop_paths.append(output)
    return loop_paths


def make_raw_prefix_clip(prefix: list[Path], output_path: Path) -> list[Path]:
    raw_dir = builder.PACKET_ROOT / "work" / ITERATION_ID / "raw_prefix_24f" / output_path.stem
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    stretched: list[Path] = []
    for index in range(24):
        src_index = round(index * (len(prefix) - 1) / 23) if len(prefix) > 1 else 0
        output = raw_dir / f"frame_{index:04d}.png"
        shutil.copyfile(prefix[src_index], output)
        stretched.append(output)
    builder.encode_frames(raw_dir, output_path, width=builder.WIDTH, height=builder.HEIGHT)
    return stretched


def render_candidate(candidate: StablePrefixCandidate, no_crew_plate_path: Path) -> dict[str, Any]:
    prefix = stable_prefix_frames(candidate)
    raw_chroma = (
        builder.PACKET_ROOT
        / "clips"
        / "raw_chroma_crew"
        / f"{candidate.id}_{ITERATION_ID}_seed{candidate.seed}_raw_chroma_crew_prefix.mp4"
    )
    raw_stretched_frames = make_raw_prefix_clip(prefix, raw_chroma)
    loop_chroma_frames = make_stretched_half(prefix, builder.PACKET_ROOT / "work" / ITERATION_ID / "loop_chroma_frames" / candidate.id)
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
    for frame_index in PREFIX_RAW_QA_FRAMES:
        output = builder.PACKET_ROOT / "qa" / "frames" / ITERATION_ID / "raw_chroma_crew" / candidate.id / f"{candidate.id}_raw_prefix_{frame_index:03d}.png"
        builder.copy_sequence_frame(raw_stretched_frames, frame_index, output)
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

    prompt_path = builder.PACKET_ROOT / "prompts" / "iteration_03" / f"{candidate.source_raw_candidate}_prompt.txt"
    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "iteration": ITERATION_ID,
        "seed": candidate.seed,
        "source_raw_candidate": candidate.source_raw_candidate,
        "source_prefix_frames_used": candidate.prefix_len,
        "prompt_variant_id": candidate.prompt_variant_id,
        "motion_note": candidate.motion_note,
        "cfg_scale": candidate.cfg_scale,
        "stg_scale": candidate.stg_scale,
        "steps": 8,
        "frames_requested": 25,
        "raw_frames_after_normalization": 24,
        "loop_construction": "selected stable LTX-generated prefix frames stretched to 144-frame half-cycle, then forward/reverse ping-pong",
        "prompt_path": str(prompt_path),
        "prompt_sha256": builder.sha256(prompt_path) if prompt_path.exists() else None,
        "ltx_invocation": {
            "runtime": str(builder.LTX_BIN),
            "model": builder.MODEL_REPO,
            "gemma": builder.TEXT_ENCODER_REPO,
            "width": builder.WIDTH,
            "height": builder.HEIGHT,
            "frames": 25,
            "steps": 8,
            "cfg_scale": candidate.cfg_scale,
            "stg_scale": candidate.stg_scale,
            "enhance_prompt": False,
            "pipeline": "one_stage",
            "post_generation_selection": "stable_prefix_only_no_deformation",
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


def write_docs(manifest: dict[str, Any]) -> None:
    readme = builder.build_readme(manifest)
    readme += (
        "\n## Internal Iteration Notes\n\n"
        "- `iteration_01` failed internal visual review: LTX drifted into walking/raised-arm gestures and background noise.\n"
        "- `iteration_02` failed internal visual review: very low CFG/STG collapsed the crew plate into chroma/noise artifacts.\n"
        "- `iteration_03` generated usable early micro-motion but drifted later; the presented A/B/C set uses only the stable LTX-generated prefix frames.\n"
    )
    review = builder.build_review(manifest)
    review = review.replace(
        "## What Changed\n\n",
        "## What Changed\n\n"
        "- Internal `iteration_01` failed because full generated clips drifted into walking and raised-arm gestures.\n"
        "- Internal `iteration_02` failed because lower guidance collapsed the chroma layer into noise.\n"
        "- The presented set uses stable prefix frames from `iteration_03`; no deformation, sprite animation, or clean-plate motion trick was used.\n",
    )
    builder.write_text(builder.PACKET_ROOT / "README.md", readme)
    builder.write_text(builder.PACKET_ROOT / "review" / "motion_scout_review_packet.md", review)


def main() -> None:
    manifest_path = builder.PACKET_ROOT / "motion_scout_manifest.json"
    manifest = builder.read_json(manifest_path)
    no_crew_payload = manifest["source_visual"]["no_crew_plate"]
    chroma_payload = manifest["source_visual"]["crew_chroma_source"]
    no_crew_plate_path = Path(no_crew_payload["plate"]["path"])
    candidate_payloads = [render_candidate(candidate, no_crew_plate_path) for candidate in CANDIDATES]
    contact_sheets = builder.make_contact_sheets(candidate_payloads, no_crew_payload, chroma_payload)

    manifest["candidates"] = candidate_payloads
    manifest["contact_sheets"] = {key: builder.artifact(path) for key, path in contact_sheets.items()}
    manifest["loop_contract"].update(
        {
            "raw_half_cycle_seconds": "stable_prefix_0.125_to_0.292s_stretched_to_6s",
            "raw_half_cycle_frames_after_normalization": 24,
            "loop_method": "stable_ltx_generated_prefix_stretched_to_6s_then_forward_reverse_ping_pong",
            "loop_frames": LOOP_FRAMES,
            "iterations_attempted": 3,
            "presented_iteration": ITERATION_ID,
            "iteration_03_result": "presented_stable_prefix_only_after_later_frame_drift",
        }
    )
    manifest["internal_iterations"] = [
        {
            "iteration": "iteration_01",
            "result": "failed_internal_visual_review",
            "blockers": ["hand_waving_or_raised_arm_drift", "walking_or_step_cycle_drift", "background_noise_inside_chroma_source"],
            "metadata_snapshot": str(builder.PACKET_ROOT / "iterations" / "iteration_01_failed" / "motion_scout_manifest_snapshot.json"),
            "contact_sheet_backup_dir": str(builder.PACKET_ROOT / "iterations" / "iteration_01_failed" / "contact_sheets"),
        },
        {
            "iteration": "iteration_02",
            "result": "failed_internal_visual_review",
            "blockers": ["chroma_noise_collapse", "matte_noise", "crew_layer_not_reviewable_after_first_frames"],
            "metadata_snapshot": str(builder.PACKET_ROOT / "iterations" / "iteration_02_failed" / "motion_scout_manifest_snapshot.json"),
            "contact_sheet_backup_dir": str(builder.PACKET_ROOT / "iterations" / "iteration_02_failed" / "contact_sheets"),
        },
        {
            "iteration": "iteration_03",
            "result": "partially_usable_ltx_generation",
            "blocker": "later generated frames still drift into gestures",
            "retained_for_review": "stable_prefix_frames_only",
        },
        {
            "iteration": ITERATION_ID,
            "result": "presented_for_human_review",
            "change": "stable generated prefix frames stretched into 12s loop; no in-place deformation or sprite overlay",
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
    builder.write_json(manifest_path, manifest)
    write_docs(manifest)
    manifest["artifacts"]["readme"] = builder.artifact(builder.PACKET_ROOT / "README.md")
    manifest["artifacts"]["review_packet"] = builder.artifact(builder.PACKET_ROOT / "review" / "motion_scout_review_packet.md")
    manifest["artifacts"]["iteration_03_stable_prefix_script"] = builder.artifact(Path(__file__))
    for key, path in contact_sheets.items():
        manifest["artifacts"][key] = builder.artifact(path)
    builder.write_json(manifest_path, manifest)
    print({"packet_root": str(builder.PACKET_ROOT), "presented_iteration": ITERATION_ID})


if __name__ == "__main__":
    main()
