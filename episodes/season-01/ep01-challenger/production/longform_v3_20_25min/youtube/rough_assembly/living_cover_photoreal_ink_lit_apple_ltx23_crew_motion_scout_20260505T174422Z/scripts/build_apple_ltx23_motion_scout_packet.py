#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


CREATED_UTC = "2026-05-05T17:44:22Z"
PACKET_ID = "living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z"
PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z"
)
REJECTED_PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_full_runtime_crew_liveliness_html_rough_proof_20260505T170441Z"
)
REJECTED_MANIFEST_PATH = REJECTED_PACKET_ROOT / "rough_assembly_manifest.json"
SOURCE_ART_PATH = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_repair/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_foreground_repair_20260504T215400Z/assets/source_art/"
    "living_cover_launch_pad_photoreal_ink_lit_crew_variant_c.png"
)
EXPECTED_SOURCE_SHA256 = "52f94150037d5aa40633d34b29c137c59c5868e987bc5f8b7f80903f6bc2ac8a"
CE_BIN = Path("/Users/mike/Viz_CascadeEffects/bin/ce")
LTX_RUNTIME_ROOT = Path("/Users/mike/AI/ltx-2-mlx")
MODEL_REPO = "dgrauet/ltx-2.3-mlx-q8"
TEXT_ENCODER_REPO = "mlx-community/gemma-3-12b-it-4bit"
PIPELINE = "apple-ltx23-q8-one-stage"
WIDTH = 1024
HEIGHT = 576
FRAMES = 121


@dataclass(frozen=True)
class Candidate:
    id: str
    label: str
    seed: int
    motion_direction: str
    prompt_variant_id: str


CANDIDATES = [
    Candidate("variant_a", "A", 314159, "subtle crew micro-motion, locked camera", "locked_micro_motion_a"),
    Candidate("variant_b", "B", 271828, "subtle crew motion plus minor pad-light and air shimmer", "pad_light_air_shimmer_b"),
    Candidate("variant_c", "C", 161803, "slightly more visible crew weight shifts, still restrained", "restrained_weight_shift_c"),
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_size(path: Path) -> int:
    return path.stat().st_size


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256(path), "bytes": bytes_size(path)}


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    ensure_dir(log_path.parent) if log_path else None
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if log_path:
        log_path.write_text(
            "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
            encoding="utf-8",
        )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"command failed: {' '.join(command)}"
        raise RuntimeError(detail)
    return completed


def build_prompt(candidate: Candidate) -> str:
    return (
        "Photorealistic ink-lit documentary image-to-video motion test for a Challenger launch pad living cover. "
        "Use the provided full-frame source still as the visual truth and preserve its composition, camera position, "
        "right-side safe space, shuttle anatomy, launch tower, crawlerway, foreground ramp, and exactly seven back-view "
        "astronauts in blue flight suits. "
        f"Motion direction: {candidate.motion_direction}. "
        "The astronauts remain small foreground human presence, looking toward the shuttle with their backs to the viewer. "
        "Animate only restrained natural human presence: tiny weight shifts, subtle shoulder/head settling, very small torso "
        "adjustments, cloth micro-movement, and contact-shadow changes. Keep motion slow, irregular, and observed. "
        "Keep camera locked. Preserve night launch-pad lighting with only gentle practical-light shimmer. "
        "No walking. No waving. No synchronized swaying. No turning around. No looking at the viewer. No faces. "
        "No name patches. No readable logos. No generated text. No watermarks. No extra people. No missing people. "
        "No launch, ignition, smoke, fire, flame, plume, ascent, explosion, debris, camera push, camera pan, camera shake, "
        "dramatic action, or spectacle. Do not alter shuttle shape, SRBs, external tank, tower, pad hardware, or chronology."
    )


def ffprobe(path: Path) -> dict[str, Any]:
    completed = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    return json.loads(completed.stdout)


def video_summary(path: Path) -> dict[str, Any]:
    data = ffprobe(path)
    streams = data.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    return {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": bytes_size(path),
        "duration_seconds": float(data.get("format", {}).get("duration") or 0),
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "codec_name": video_stream.get("codec_name"),
        "pix_fmt": video_stream.get("pix_fmt"),
        "avg_frame_rate": video_stream.get("avg_frame_rate"),
        "nb_frames": video_stream.get("nb_frames"),
        "has_audio": bool(audio_streams),
        "ffprobe": data,
    }


def normalize_clip(raw_path: Path, normalized_path: Path) -> None:
    if normalized_path.exists():
        return
    ensure_dir(normalized_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_path),
            "-vf",
            f"fps=24,scale={WIDTH}:{HEIGHT}:flags=lanczos",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(normalized_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{normalized_path.stem}.ffmpeg.log",
    )


def extract_frame(clip_path: Path, frame_index: int, output_path: Path) -> None:
    if output_path.exists():
        return
    ensure_dir(output_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(clip_path),
            "-vf",
            f"select=eq(n\\,{frame_index})",
            "-frames:v",
            "1",
            str(output_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_path.stem}.ffmpeg.log",
    )


def safe_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for item in candidates:
        if Path(item).exists():
            return ImageFont.truetype(item, size)
    return ImageFont.load_default()


def make_contact_sheet(
    *,
    frame_paths_by_candidate: dict[str, list[Path]],
    output_path: Path,
    crop_box: tuple[int, int, int, int] | None,
    title: str,
) -> None:
    ensure_dir(output_path.parent)
    columns = 5
    rows = len(CANDIDATES)
    label_h = 40
    thumb_w = 256 if crop_box is None else 256
    thumb_h = 144 if crop_box is None else 112
    gutter = 10
    top_h = 54
    sheet_w = gutter + columns * (thumb_w + gutter)
    sheet_h = top_h + rows * (label_h + thumb_h + gutter) + gutter
    canvas = Image.new("RGB", (sheet_w, sheet_h), (9, 16, 28))
    draw = ImageDraw.Draw(canvas)
    font_title = safe_font(24)
    font_label = safe_font(17)
    draw.text((gutter, 14), title, fill=(246, 234, 210), font=font_title)
    for row, candidate in enumerate(CANDIDATES):
        row_y = top_h + row * (label_h + thumb_h + gutter)
        draw.text(
            (gutter, row_y + 8),
            f"{candidate.label} seed {candidate.seed} - {candidate.motion_direction}",
            fill=(246, 234, 210),
            font=font_label,
        )
        for col, frame_path in enumerate(frame_paths_by_candidate[candidate.id]):
            image = Image.open(frame_path).convert("RGB")
            if crop_box is not None:
                image = image.crop(crop_box)
            image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            x = gutter + col * (thumb_w + gutter)
            y = row_y + label_h
            tile = Image.new("RGB", (thumb_w, thumb_h), (5, 12, 22))
            tile.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
            canvas.paste(tile, (x, y))
    canvas.save(output_path, quality=92)


def render_candidate(candidate: Candidate) -> dict[str, Any]:
    prompt_path = PACKET_ROOT / "prompts" / f"{candidate.id}_prompt.txt"
    prompt_text = build_prompt(candidate)
    write_text(prompt_path, prompt_text + "\n")
    raw_path = PACKET_ROOT / "clips" / "raw" / f"{candidate.id}_apple_ltx23_seed{candidate.seed}_raw.mp4"
    normalized_path = PACKET_ROOT / "clips" / "normalized" / f"{candidate.id}_apple_ltx23_seed{candidate.seed}_normalized.mp4"
    video_manifest_path = Path(str(raw_path) + ".json")
    if not raw_path.exists():
        command = [
            str(CE_BIN),
            "handoff-i2v",
            str(SOURCE_ART_PATH),
            "--prompt",
            prompt_text,
            "--frames",
            str(FRAMES),
            "--width",
            str(WIDTH),
            "--height",
            str(HEIGHT),
            "--seed",
            str(candidate.seed),
            "--pipeline",
            PIPELINE,
            "--model-repo",
            MODEL_REPO,
            "--text-encoder-repo",
            TEXT_ENCODER_REPO,
            "--output",
            str(raw_path),
            "--typography",
            "off",
        ]
        run(command, cwd=Path("/Users/mike/Viz_CascadeEffects"), log_path=PACKET_ROOT / "logs" / f"{candidate.id}_handoff_i2v.log")
    normalize_clip(raw_path, normalized_path)
    frames_dir = PACKET_ROOT / "qa" / "frames" / candidate.id
    frame_paths = []
    for frame_index in [0, 24, 48, 72, 96]:
        output = frames_dir / f"{candidate.id}_frame_{frame_index:03d}.png"
        extract_frame(normalized_path, frame_index, output)
        frame_paths.append(output)
    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "seed": candidate.seed,
        "prompt_variant_id": candidate.prompt_variant_id,
        "motion_pipeline": PIPELINE,
        "model_repo": MODEL_REPO,
        "text_encoder_repo": TEXT_ENCODER_REPO,
        "source_still_path": str(SOURCE_ART_PATH),
        "source_still_sha256": sha256(SOURCE_ART_PATH),
        "source_still_variant_role": "primary",
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256(prompt_path),
        "prompt_text": prompt_text,
        "raw_clip": video_summary(raw_path),
        "raw_handoff_manifest": artifact(video_manifest_path) if video_manifest_path.exists() else None,
        "normalized_clip": video_summary(normalized_path),
        "qa_frames": [artifact(path) for path in frame_paths],
        "disposition": "defer",
        "selected_for_motion_proof": False,
        "selected_for_motion_proof_status": "pending_human_review",
    }
    write_json(PACKET_ROOT / "candidates" / f"{candidate.id}.json", payload)
    return payload


def update_rejected_packet() -> None:
    manifest = read_json(REJECTED_MANIFEST_PATH)
    manifest["status"] = "reject_wrong_sprite_overlay_approach_apple_ltx23_motion_scout_created"
    manifest["human_disposition"] = "reject"
    manifest["sprite_overlay_reject_record"] = {
        "disposition": "reject",
        "disposition_utc": CREATED_UTC,
        "reviewer_text": "The sprite-overlay crew-liveliness proof is the wrong approach. It creates ghosted duplicate humans and background patches, making the people feel artificial.",
        "required_next_action": "Use an Apple LTX 2.3 image-to-video motion scout from the kept Variant C full-frame source carrier.",
    }
    reads = manifest.setdefault("rough_assembly_reads", {})
    reads["crew_liveliness_read"] = "reject_sprite_overlay_ghosting"
    reads["crew_motion_authenticity_read"] = "reject_duplicate_human_and_background_artifacts"
    reads["uncanny_motion_read"] = "reject_visible_ghosting"
    reads["crew_count_read"] = "reject_overlay_duplicates_create_count_ambiguity"
    reads["identity_logo_text_read"] = "pass_no_new_readable_identity_text"
    reads["render_output_read"] = "blocked_no_full_runtime_mp4_or_final_render_authorized"
    manifest["apple_ltx23_motion_scout_successor"] = {
        "packet_path": str(PACKET_ROOT),
        "manifest_path": str(PACKET_ROOT / "motion_scout_manifest.json"),
        "review_packet_path": str(PACKET_ROOT / "review" / "motion_scout_review_packet.md"),
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
    }
    for flag in [
        "may_advance_to_video_render",
        "may_create_full_runtime_mp4_render",
        "may_advance_to_final_assembly",
        "may_advance_to_shorts_work",
        "may_advance_to_publish_readiness",
        "may_youtube_action",
    ]:
        manifest[flag] = False
    manifest["next_review_question"] = "Review the Apple LTX 2.3 crew motion scout A/B/C contact sheet and reply with keep A, keep B, keep C, tighten, or reject."
    write_json(REJECTED_MANIFEST_PATH, manifest)

    readme_path = REJECTED_PACKET_ROOT / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        if "## Sprite Overlay Reject Record" not in readme:
            readme_path.write_text(
                readme
                + f"\n## Sprite Overlay Reject Record\n\nHuman disposition: `reject`\n\n"
                + "Reviewer note: the sprite-overlay approach is wrong because it creates ghosted duplicate humans and background patches.\n\n"
                + f"Superseding Apple LTX 2.3 motion-scout packet: `{PACKET_ROOT}`\n",
                encoding="utf-8",
            )
    review_path = REJECTED_PACKET_ROOT / "review" / "rough_assembly_review_packet.md"
    if review_path.exists():
        review = review_path.read_text(encoding="utf-8")
        if "## Sprite Overlay Reject Record" not in review:
            review_path.write_text(
                review
                + f"\n## Sprite Overlay Reject Record\n\nDisposition recorded: `reject`.\n\n"
                + "Reason: ghosted duplicate humans/background artifacts make the sprite overlay the wrong approach.\n\n"
                + f"Next review artifact: `{PACKET_ROOT}`\n",
                encoding="utf-8",
            )


def build_manifest(candidates: list[dict[str, Any]], contact_sheets: dict[str, Path]) -> dict[str, Any]:
    no_forbidden_media = not any(
        path.suffix.lower() in {".wav", ".mp3", ".srt", ".vtt"}
        for path in PACKET_ROOT.rglob("*")
        if path.is_file()
    )
    return {
        "packet_id": PACKET_ID,
        "gate": "rough_assembly_motion_scout_gate",
        "status": "review_ready_pending_human_apple_ltx23_motion_scout_keep",
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
        "created_from_disposition": "reject",
        "rejected_sprite_overlay_packet_path": str(REJECTED_PACKET_ROOT),
        "rejected_sprite_overlay_manifest_path": str(REJECTED_MANIFEST_PATH),
        "review_only": True,
        "motion_scout_only": True,
        "full_runtime_html_proof_created": False,
        "full_runtime_mp4_created": False,
        "profileId": "cascade-ink-lit-photoreal-v1",
        "source_visual": {
            "carrier": "kept_variant_c_full_frame_source_art",
            "source_art_path": str(SOURCE_ART_PATH),
            "source_art_sha256": sha256(SOURCE_ART_PATH),
            "expected_source_art_sha256": EXPECTED_SOURCE_SHA256,
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "dimensions": {"width": 1920, "height": 1080, "aspect_ratio": "16:9"},
        },
        "apple_ltx23_runtime": {
            "command_path": str(CE_BIN),
            "pipeline": PIPELINE,
            "runtime_root": str(LTX_RUNTIME_ROOT),
            "model_repo": MODEL_REPO,
            "text_encoder_repo": TEXT_ENCODER_REPO,
            "frames": FRAMES,
            "width": WIDTH,
            "height": HEIGHT,
            "typography": "off",
            "runtime_path_read": "pass" if LTX_RUNTIME_ROOT.exists() and (LTX_RUNTIME_ROOT / "pyproject.toml").exists() else "reject_missing_runtime",
        },
        "candidates": candidates,
        "contact_sheets": {key: artifact(path) for key, path in contact_sheets.items()},
        "motion_scout_reads": {
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "apple_ltx23_runtime_read": "pass" if LTX_RUNTIME_ROOT.exists() and (LTX_RUNTIME_ROOT / "pyproject.toml").exists() else "reject_missing_runtime",
            "candidate_count_read": "pass_three_candidates" if len(candidates) == 3 else "reject_missing_candidates",
            "raw_clip_audio_read": "pass_no_audio" if all(not item["raw_clip"]["has_audio"] for item in candidates) else "reject_audio_present",
            "normalized_clip_audio_read": "pass_no_audio" if all(not item["normalized_clip"]["has_audio"] for item in candidates) else "reject_audio_present",
            "contact_sheet_read": "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet",
            "forbidden_media_copy_read": "pass_no_audio_caption_transcript_sidecars" if no_forbidden_media else "reject_forbidden_sidecar_found",
            "crew_liveliness_read": "defer_pending_human_review",
            "crew_motion_authenticity_read": "defer_pending_human_review",
            "uncanny_motion_read": "defer_pending_human_review",
            "crew_count_read": "defer_pending_human_review",
            "identity_logo_text_read": "defer_pending_human_review",
            "pad_hardware_stability_read": "defer_pending_human_review",
            "shuttle_anatomy_stability_read": "defer_pending_human_review",
            "launch_chronology_read": "defer_pending_human_review",
        },
        "may_select_motion_scout_candidate_after_human_keep": False,
        "may_create_full_runtime_html_proof": False,
        "may_create_full_runtime_mp4_render": False,
        "may_advance_to_final_assembly": False,
        "may_advance_to_shorts_work": False,
        "may_advance_to_publish_readiness": False,
        "may_youtube_action": False,
        "next_review_question": "Review A/B/C and reply with exactly one response: keep A, keep B, keep C, tighten, or reject.",
    }


def build_readme(manifest: dict[str, Any]) -> str:
    rows = "\n".join(
        f"- {item['label']}: `{item['candidate_id']}`, seed `{item['seed']}`, prompt `{item['prompt_variant_id']}`"
        for item in manifest["candidates"]
    )
    return f"""# Challenger Living Cover Apple LTX 2.3 Crew Motion Scout

Packet: `{PACKET_ID}`
Status: `{manifest['status']}`
Human disposition: `defer`

This packet supersedes the rejected sprite-overlay crew-liveliness proof. The old overlay method is not an advancement source because it created ghosted duplicate humans and background patches.

## Candidates

{rows}

## Review Surfaces

- Full-frame contact sheet: `{manifest['contact_sheets']['full_frame']['path']}`
- Crew-crop contact sheet: `{manifest['contact_sheets']['crew_crop']['path']}`
- Candidate clips: `clips/raw/` and `clips/normalized/`

## Constraints

- Source carrier: kept Variant C full-frame source art.
- Pipeline: `{PIPELINE}`
- Model: `{MODEL_REPO}`
- Text encoder: `{TEXT_ENCODER_REPO}`
- Typography: `off`
- No walking, waving, synchronized swaying, turning around, looking at viewer, launch, ignition, smoke, fire, faces, readable logos, name patches, or generated text.

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.
"""


def build_review(manifest: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        f"| {item['label']} | `{item['seed']}` | `{item['prompt_variant_id']}` | `{item['normalized_clip']['path']}` |"
        for item in manifest["candidates"]
    )
    read_rows = "\n".join(f"| `{key}` | `{value}` |" for key, value in manifest["motion_scout_reads"].items())
    return f"""# Challenger Living Cover Apple LTX 2.3 Crew Motion Scout Review

Packet: `{PACKET_ID}`
Gate: `rough_assembly_motion_scout_gate`
Human disposition: `defer`

## What Changed

- The sprite-overlay crew proof is recorded as `reject`.
- This packet uses Apple-native LTX 2.3 image-to-video from the kept Variant C full-frame still.
- A/B/C are short motion-scout clips only, not a rough proof or final render.

## Contact Sheets

- Full frame: `{manifest['contact_sheets']['full_frame']['path']}`
- Crew crop: `{manifest['contact_sheets']['crew_crop']['path']}`

## Candidates

| Candidate | Seed | Prompt Variant | Normalized Clip |
|---|---:|---|---|
{candidate_rows}

## Reads

| Read | Result |
|---|---:|
{read_rows}

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected LTX video carrier behind the existing staged right rail. No full-runtime MP4 or downstream assembly is authorized by this scout packet.
"""


def main() -> None:
    ensure_dir(PACKET_ROOT)
    for subdir in ["prompts", "candidates", "clips/raw", "clips/normalized", "qa/frames", "qa/contact_sheets", "logs", "review", "scripts"]:
        ensure_dir(PACKET_ROOT / subdir)
    if not SOURCE_ART_PATH.exists():
        raise FileNotFoundError(SOURCE_ART_PATH)
    if sha256(SOURCE_ART_PATH) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Kept Variant C source-art hash mismatch")
    if not CE_BIN.exists():
        raise FileNotFoundError(CE_BIN)
    if not (LTX_RUNTIME_ROOT / "pyproject.toml").exists():
        raise FileNotFoundError(LTX_RUNTIME_ROOT / "pyproject.toml")

    update_rejected_packet()
    candidate_payloads = [render_candidate(candidate) for candidate in CANDIDATES]

    frame_paths_by_candidate = {
        item["candidate_id"]: [Path(frame["path"]) for frame in item["qa_frames"]]
        for item in candidate_payloads
    }
    full_contact = PACKET_ROOT / "qa" / "contact_sheets" / "apple_ltx23_abc_full_frame_contact_sheet.jpg"
    crop_contact = PACKET_ROOT / "qa" / "contact_sheets" / "apple_ltx23_abc_crew_crop_contact_sheet.jpg"
    make_contact_sheet(
        frame_paths_by_candidate=frame_paths_by_candidate,
        output_path=full_contact,
        crop_box=None,
        title="Challenger Living Cover Apple LTX 2.3 A/B/C - Full Frame",
    )
    make_contact_sheet(
        frame_paths_by_candidate=frame_paths_by_candidate,
        output_path=crop_contact,
        crop_box=(45, 392, 560, 576),
        title="Challenger Living Cover Apple LTX 2.3 A/B/C - Crew Crop",
    )

    manifest = build_manifest(candidate_payloads, {"full_frame": full_contact, "crew_crop": crop_contact})
    manifest_path = PACKET_ROOT / "motion_scout_manifest.json"
    readme_path = PACKET_ROOT / "README.md"
    review_path = PACKET_ROOT / "review" / "motion_scout_review_packet.md"
    write_json(manifest_path, manifest)
    write_text(readme_path, build_readme(manifest))
    write_text(review_path, build_review(manifest))
    manifest["artifacts"] = {
        "manifest": artifact(manifest_path),
        "readme": artifact(readme_path),
        "review_packet": artifact(review_path),
        "full_frame_contact_sheet": artifact(full_contact),
        "crew_crop_contact_sheet": artifact(crop_contact),
        "builder_script": artifact(Path(__file__)),
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"packet_root": str(PACKET_ROOT), "manifest_path": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
