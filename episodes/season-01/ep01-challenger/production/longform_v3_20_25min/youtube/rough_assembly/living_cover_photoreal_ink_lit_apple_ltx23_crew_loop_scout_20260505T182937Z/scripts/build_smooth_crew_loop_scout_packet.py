#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CREATED_UTC = "2026-05-05T18:29:37Z"
PACKET_ID = "living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z"
PACKET_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_apple_ltx23_crew_loop_scout_20260505T182937Z"
)
CURRENT_SCOUT_ROOT = Path(
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/"
    "living_cover_photoreal_ink_lit_apple_ltx23_crew_motion_scout_20260505T174422Z"
)
CURRENT_SCOUT_MANIFEST = CURRENT_SCOUT_ROOT / "motion_scout_manifest.json"
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
FRAMES = 289
FPS = 24
TARGET_LOOP_SECONDS = 12.0
SEAM_BLEND_FRAMES = 12
CREW_CROP_BOX = (45, 392, 560, 576)
CREW_MASK_FEATHER = 18
RAW_QA_FRAMES = [0, 72, 144, 216, 276]
LOOP_QA_FRAMES = [0, 72, 144, 216, 276]
SEAM_QA_FRAMES = [252, 264, 276, 284, 287, 0, 6, 12]
PREVIEW_SEAM_QA_FRAMES = [276, 287, 288, 300, 564, 575, 576, 588]


@dataclass(frozen=True)
class Candidate:
    id: str
    label: str
    seed: int
    prompt_variant_id: str
    motion_direction: str


CANDIDATES = [
    Candidate(
        id="variant_a",
        label="A",
        seed=314159,
        prompt_variant_id="smallest_detectable_loop_a",
        motion_direction=(
            "smallest detectable living-cover movement: barely perceptible asynchronous weight shifts, "
            "tiny head settling, and slight cloth/contact-shadow motion"
        ),
    ),
    Candidate(
        id="variant_b",
        label="B",
        seed=271828,
        prompt_variant_id="recommended_subtle_sway_head_turn_b",
        motion_direction=(
            "recommended middle path: subtle asynchronous side-to-side body sway, slight head turns toward the shuttle, "
            "small shoulder settling, and restrained cloth/contact-shadow motion"
        ),
    ),
    Candidate(
        id="variant_c",
        label="C",
        seed=161803,
        prompt_variant_id="upper_detectability_restrained_c",
        motion_direction=(
            "upper bound for detectability while still restrained: visible but slow asynchronous weight shifts, "
            "small head turns, slight torso settling, and grounded contact-shadow motion"
        ),
    ),
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


def run(command: list[str], *, cwd: Path | None = None, log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    if log_path:
        ensure_dir(log_path.parent)
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if log_path:
        log_path.write_text(
            "$ " + " ".join(command) + "\n\nSTDOUT\n" + completed.stdout + "\nSTDERR\n" + completed.stderr,
            encoding="utf-8",
        )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"command failed: {' '.join(command)}"
        raise RuntimeError(detail)
    return completed


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


def build_prompt(candidate: Candidate) -> str:
    return (
        "Photorealistic ink-lit documentary image-to-video loop test for a Challenger launch pad living cover. "
        "Use the provided full-frame source still as the visual truth. This is a long-duration YouTube living-cover "
        "carrier for about twenty minutes of audio, with a separate right-rail chapter system later overlaid on the "
        "right side. The motion must be subtle, detectable, stable, and loopable. Preserve the exact composition, locked "
        "camera, right-side safe space, shuttle anatomy, launch tower, crawlerway, foreground ramp, pad lighting, and "
        "exactly seven back-view astronauts in blue flight suits. Create one slow twelve-second motion cycle that returns "
        "to the starting neutral posture at the end so the clip can loop smoothly. "
        f"Motion direction: {candidate.motion_direction}. "
        "The seven astronauts remain in place with their backs to the viewer, looking toward the shuttle. Movement is "
        "only restrained human presence: slight asynchronous swaying, small head turns still aimed toward the shuttle, "
        "tiny shoulder and torso settling, subtle cloth movement, and small contact-shadow changes. The figures should "
        "feel alive but not theatrical. Keep the shuttle, tower, pad hardware, ramp, background, and right-rail safe area "
        "visually stable. No walking. No stepping. No waving. No synchronized uniform swaying. No turning around. No "
        "looking at the viewer. No faces. No face detail. No name patches. No readable logos. No generated text. No "
        "watermarks. No extra people. No missing people. No duplicated people. No launch, ignition, smoke, fire, flame, "
        "plume, ascent, explosion, debris, camera push, camera pan, camera shake, dramatic action, or spectacle. Do not "
        "alter shuttle shape, SRBs, external tank, tower, pad hardware, or launch chronology."
    )


def extract_all_frames(clip_path: Path, output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    ensure_dir(output_dir)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(clip_path),
            "-vf",
            f"fps={FPS},scale={WIDTH}:{HEIGHT}:flags=lanczos",
            "-start_number",
            "0",
            str(output_dir / "frame_%04d.png"),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_dir.parent.name}_{output_dir.name}_extract.ffmpeg.log",
    )
    return sorted(output_dir.glob("frame_*.png"))


def encode_frames(input_dir: Path, output_path: Path, *, crf: int = 18) -> None:
    ensure_dir(output_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(input_dir / "frame_%04d.png"),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_path.stem}.encode.ffmpeg.log",
    )


def extract_frame(clip_path: Path, frame_index: int, output_path: Path) -> None:
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


def make_static_background() -> Image.Image:
    return Image.open(SOURCE_ART_PATH).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def make_crew_mask() -> Image.Image:
    x1, y1, x2, y2 = CREW_CROP_BOX
    width = x2 - x1
    height = y2 - y1
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    inset = CREW_MASK_FEATHER
    draw.rounded_rectangle(
        (inset, inset // 2, width - inset, height - inset // 2),
        radius=18,
        fill=255,
    )
    return mask.filter(ImageFilter.GaussianBlur(radius=CREW_MASK_FEATHER / 2))


def composite_crew_zone(raw_frame_paths: list[Path], output_dir: Path) -> list[Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    ensure_dir(output_dir)
    bg = make_static_background()
    mask = make_crew_mask()
    x1, y1, x2, y2 = CREW_CROP_BOX
    frames: list[Image.Image] = []
    for frame_path in raw_frame_paths:
        raw = Image.open(frame_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        patch = raw.crop(CREW_CROP_BOX)
        composed = bg.copy()
        composed.paste(patch, (x1, y1), mask)
        frames.append(composed)

    usable_count = min(len(frames), int(TARGET_LOOP_SECONDS * FPS))
    frames = frames[:usable_count]
    if len(frames) < FPS * 4:
        raise RuntimeError(f"Not enough frames for loop normalization: {len(frames)}")

    first_frame = frames[0]
    blend_count = min(SEAM_BLEND_FRAMES, len(frames) // 4)
    for offset in range(blend_count):
        index = len(frames) - blend_count + offset
        alpha = (offset + 1) / blend_count
        frames[index] = Image.blend(frames[index], first_frame, alpha)

    output_paths: list[Path] = []
    for index, frame in enumerate(frames):
        output = output_dir / f"frame_{index:04d}.png"
        frame.save(output)
        output_paths.append(output)
    return output_paths


def make_three_loop_preview(loop_path: Path, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "2",
            "-i",
            str(loop_path),
            "-t",
            str(TARGET_LOOP_SECONDS * 3),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        log_path=PACKET_ROOT / "logs" / f"{output_path.stem}.ffmpeg.log",
    )


def make_contact_sheet(
    *,
    rows: list[tuple[str, list[Path]]],
    output_path: Path,
    title: str,
    crop_box: tuple[int, int, int, int] | None = None,
    thumb_w: int = 230,
    thumb_h: int = 130,
) -> None:
    ensure_dir(output_path.parent)
    columns = max(len(paths) for _, paths in rows)
    gutter = 10
    top_h = 54
    label_h = 38
    sheet_w = gutter + columns * (thumb_w + gutter)
    sheet_h = top_h + len(rows) * (label_h + thumb_h + gutter) + gutter
    canvas = Image.new("RGB", (sheet_w, sheet_h), (8, 14, 25))
    draw = ImageDraw.Draw(canvas)
    font_title = safe_font(23)
    font_label = safe_font(16)
    draw.text((gutter, 14), title, fill=(247, 235, 214), font=font_title)
    for row_index, (label, frame_paths) in enumerate(rows):
        row_y = top_h + row_index * (label_h + thumb_h + gutter)
        draw.text((gutter, row_y + 7), label, fill=(247, 235, 214), font=font_label)
        for col, frame_path in enumerate(frame_paths):
            image = Image.open(frame_path).convert("RGB")
            if crop_box is not None:
                image = image.crop(crop_box)
            image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb_w, thumb_h), (4, 10, 19))
            tile.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
            x = gutter + col * (thumb_w + gutter)
            y = row_y + label_h
            canvas.paste(tile, (x, y))
    canvas.save(output_path, quality=92)


def update_current_scout_tighten() -> None:
    manifest = read_json(CURRENT_SCOUT_MANIFEST)
    manifest["status"] = "tighten_motion_test_not_long_runtime_loop_carrier"
    manifest["human_disposition"] = "tighten"
    manifest["loop_carrier_tighten_record"] = {
        "disposition": "tighten",
        "disposition_utc": CREATED_UTC,
        "reviewer_text": (
            "The Apple LTX 2.3 direction is right, but the scout clips were motion tests rather than a smooth "
            "long-duration living-cover loop carrier. The next pass must make exactly seven back-view astronauts "
            "move subtly and detectably on a clean loop behind the right-rail chapter system."
        ),
        "required_next_action": "Create a loop-specific Apple LTX 2.3 crew-motion scout from kept Variant C.",
    }
    reads = manifest.setdefault("motion_scout_reads", {})
    reads["crew_loop_read"] = "tighten_not_loop_carrier"
    reads["loop_seam_read"] = "tighten_no_loop_seam_review"
    reads["long_runtime_carrier_read"] = "tighten_motion_test_not_twenty_minute_living_cover_carrier"
    reads["motion_subtlety_read"] = "tighten_needs_subtle_asynchronous_loop_motion"
    reads["motion_detectability_read"] = "tighten_needs_detectable_but_restrained_motion"
    reads["crew_liveliness_read"] = "tighten_directionally_right_needs_smooth_loop_context"
    reads["crew_motion_authenticity_read"] = "tighten_needs_loop_specific_motion_review"
    reads["uncanny_motion_read"] = "tighten_needs_loop_specific_artifact_review"
    manifest["crew_loop_scout_successor"] = {
        "packet_path": str(PACKET_ROOT),
        "manifest_path": str(PACKET_ROOT / "motion_scout_manifest.json"),
        "review_packet_path": str(PACKET_ROOT / "review" / "motion_scout_review_packet.md"),
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
    }
    for flag in [
        "may_select_motion_scout_candidate_after_human_keep",
        "may_create_full_runtime_html_proof",
        "may_create_full_runtime_mp4_render",
        "may_advance_to_final_assembly",
        "may_advance_to_shorts_work",
        "may_advance_to_publish_readiness",
        "may_youtube_action",
    ]:
        manifest[flag] = False
    manifest["next_review_question"] = (
        "Superseded by the loop-specific Apple LTX 2.3 crew scout. Review that packet and reply with keep A, "
        "keep B, keep C, tighten, or reject."
    )

    readme_path = CURRENT_SCOUT_ROOT / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        if "## Loop Carrier Tighten Record" not in readme:
            readme += (
                "\n## Loop Carrier Tighten Record\n\n"
                "Human disposition: `tighten`\n\n"
                "Reviewer note: the Apple LTX direction is right, but these clips were motion tests rather than a "
                "smooth long-duration living-cover loop carrier. The successor must keep exactly seven back-view "
                "astronauts in subtle, detectable, loopable motion behind the right-rail chapter system.\n\n"
                f"Superseding loop scout packet: `{PACKET_ROOT}`\n"
            )
            readme_path.write_text(readme, encoding="utf-8")

    review_path = CURRENT_SCOUT_ROOT / "review" / "motion_scout_review_packet.md"
    if review_path.exists():
        review = review_path.read_text(encoding="utf-8")
        if "## Loop Carrier Tighten Record" not in review:
            review += (
                "\n## Loop Carrier Tighten Record\n\n"
                "Disposition recorded: `tighten`.\n\n"
                "Reason: the clips were not reviewed as a smooth living-cover loop carrier for a ~20-minute video. "
                "The successor narrows the problem to seven subtle, detectable, back-view astronaut motions on a "
                "clean loop.\n\n"
                f"Next review artifact: `{PACKET_ROOT}`\n"
            )
            review_path.write_text(review, encoding="utf-8")

    manifest.setdefault("artifacts", {})
    if readme_path.exists():
        manifest["artifacts"]["readme"] = artifact(readme_path)
    if review_path.exists():
        manifest["artifacts"]["review_packet"] = artifact(review_path)
    write_json(CURRENT_SCOUT_MANIFEST, manifest)


def render_candidate(candidate: Candidate) -> dict[str, Any]:
    prompt_text = build_prompt(candidate)
    prompt_path = PACKET_ROOT / "prompts" / f"{candidate.id}_loop_prompt.txt"
    write_text(prompt_path, prompt_text + "\n")

    raw_path = PACKET_ROOT / "clips" / "raw" / f"{candidate.id}_apple_ltx23_seed{candidate.seed}_raw.mp4"
    raw_manifest_path = Path(str(raw_path) + ".json")
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

    raw_frames = extract_all_frames(raw_path, PACKET_ROOT / "work" / "raw_frames" / candidate.id)
    loop_frame_paths = composite_crew_zone(raw_frames, PACKET_ROOT / "work" / "loop_frames" / candidate.id)

    loop_path = PACKET_ROOT / "clips" / "loop_normalized" / f"{candidate.id}_crew_loop_seed{candidate.seed}_12s.mp4"
    preview_path = PACKET_ROOT / "clips" / "loop_preview_3x" / f"{candidate.id}_crew_loop_seed{candidate.seed}_3x_preview.mp4"
    encode_frames(PACKET_ROOT / "work" / "loop_frames" / candidate.id, loop_path)
    make_three_loop_preview(loop_path, preview_path)

    qa_raw_dir = PACKET_ROOT / "qa" / "frames" / "raw" / candidate.id
    qa_loop_dir = PACKET_ROOT / "qa" / "frames" / "loop_normalized" / candidate.id
    qa_seam_dir = PACKET_ROOT / "qa" / "frames" / "loop_seam" / candidate.id
    qa_preview_dir = PACKET_ROOT / "qa" / "frames" / "preview_3x_seam" / candidate.id
    raw_qa = []
    loop_qa = []
    seam_qa = []
    preview_qa = []
    for frame_index in RAW_QA_FRAMES:
        output = qa_raw_dir / f"{candidate.id}_raw_{frame_index:03d}.png"
        extract_frame(raw_path, frame_index, output)
        raw_qa.append(output)
    for frame_index in LOOP_QA_FRAMES:
        output = qa_loop_dir / f"{candidate.id}_loop_{frame_index:03d}.png"
        extract_frame(loop_path, frame_index, output)
        loop_qa.append(output)
    for position, frame_index in enumerate(SEAM_QA_FRAMES):
        source_frame = loop_frame_paths[frame_index]
        output = qa_seam_dir / f"{candidate.id}_seam_{position:02d}_frame_{frame_index:03d}.png"
        ensure_dir(output.parent)
        shutil.copyfile(source_frame, output)
        seam_qa.append(output)
    for frame_index in PREVIEW_SEAM_QA_FRAMES:
        output = qa_preview_dir / f"{candidate.id}_preview_{frame_index:03d}.png"
        extract_frame(preview_path, frame_index, output)
        preview_qa.append(output)

    payload = {
        "candidate_id": candidate.id,
        "label": candidate.label,
        "seed": candidate.seed,
        "prompt_variant_id": candidate.prompt_variant_id,
        "motion_direction": candidate.motion_direction,
        "motion_pipeline": PIPELINE,
        "model_repo": MODEL_REPO,
        "text_encoder_repo": TEXT_ENCODER_REPO,
        "source_still_path": str(SOURCE_ART_PATH),
        "source_still_sha256": sha256(SOURCE_ART_PATH),
        "source_still_variant_role": "kept_variant_c_visual_truth",
        "loop_contract": {
            "target_seconds": TARGET_LOOP_SECONDS,
            "fps": FPS,
            "requested_frames": FRAMES,
            "crew_crop_box_1024x576": list(CREW_CROP_BOX),
            "seam_blend_frames": SEAM_BLEND_FRAMES,
            "seam_blend_seconds": SEAM_BLEND_FRAMES / FPS,
            "normalized_method": "ltx_full_frame_raw_for_diagnosis_then_feathered_crew_zone_composite_over_static_variant_c_background",
        },
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256(prompt_path),
        "prompt_text": prompt_text,
        "raw_clip": video_summary(raw_path),
        "raw_handoff_manifest": artifact(raw_manifest_path) if raw_manifest_path.exists() else None,
        "loop_normalized_clip": video_summary(loop_path),
        "preview_3loop_clip": video_summary(preview_path),
        "qa_frames": {
            "raw_full_frame": [artifact(path) for path in raw_qa],
            "loop_normalized_full_frame": [artifact(path) for path in loop_qa],
            "loop_seam": [artifact(path) for path in seam_qa],
            "preview_3loop_seam": [artifact(path) for path in preview_qa],
        },
        "disposition": "defer",
        "selected_for_full_runtime_html_proof": False,
        "selected_for_full_runtime_html_proof_status": "pending_human_review",
    }
    write_json(PACKET_ROOT / "candidates" / f"{candidate.id}.json", payload)
    return payload


def make_contact_sheets(candidate_payloads: list[dict[str, Any]]) -> dict[str, Path]:
    by_candidate = {item["candidate_id"]: item for item in candidate_payloads}

    raw_rows = []
    crew_rows = []
    loop_rows = []
    seam_rows = []
    preview_rows = []
    for candidate in CANDIDATES:
        item = by_candidate[candidate.id]
        label = f"{candidate.label} seed {candidate.seed} - {candidate.prompt_variant_id}"
        raw_rows.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["raw_full_frame"]]))
        crew_rows.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["loop_normalized_full_frame"]]))
        loop_rows.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["loop_normalized_full_frame"]]))
        seam_rows.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["loop_seam"]]))
        preview_rows.append((label, [Path(frame["path"]) for frame in item["qa_frames"]["preview_3loop_seam"]]))

    contact_dir = PACKET_ROOT / "qa" / "contact_sheets"
    outputs = {
        "raw_full_frame": contact_dir / "apple_ltx23_crew_loop_raw_full_frame_contact_sheet.jpg",
        "loop_full_frame": contact_dir / "apple_ltx23_crew_loop_normalized_full_frame_contact_sheet.jpg",
        "loop_crew_crop": contact_dir / "apple_ltx23_crew_loop_normalized_crew_crop_contact_sheet.jpg",
        "loop_seam": contact_dir / "apple_ltx23_crew_loop_seam_contact_sheet.jpg",
        "preview_3loop_seam": contact_dir / "apple_ltx23_crew_loop_3x_preview_seam_contact_sheet.jpg",
    }
    make_contact_sheet(rows=raw_rows, output_path=outputs["raw_full_frame"], title="Apple LTX 2.3 Crew Loop Scout - Raw Full Frame")
    make_contact_sheet(rows=loop_rows, output_path=outputs["loop_full_frame"], title="Apple LTX 2.3 Crew Loop Scout - Loop-Normalized Full Frame")
    make_contact_sheet(
        rows=crew_rows,
        output_path=outputs["loop_crew_crop"],
        title="Apple LTX 2.3 Crew Loop Scout - Loop-Normalized Crew Crop",
        crop_box=CREW_CROP_BOX,
        thumb_w=256,
        thumb_h=112,
    )
    make_contact_sheet(
        rows=seam_rows,
        output_path=outputs["loop_seam"],
        title="Apple LTX 2.3 Crew Loop Scout - End-to-Start Seam Frames",
        crop_box=CREW_CROP_BOX,
        thumb_w=205,
        thumb_h=96,
    )
    make_contact_sheet(
        rows=preview_rows,
        output_path=outputs["preview_3loop_seam"],
        title="Apple LTX 2.3 Crew Loop Scout - 3x Preview Seam Checkpoints",
        crop_box=CREW_CROP_BOX,
        thumb_w=205,
        thumb_h=96,
    )
    return outputs


def build_manifest(candidate_payloads: list[dict[str, Any]], contact_sheets: dict[str, Path]) -> dict[str, Any]:
    no_forbidden_sidecars = not any(
        path.suffix.lower() in {".wav", ".mp3", ".srt", ".vtt"}
        for path in PACKET_ROOT.rglob("*")
        if path.is_file()
    )
    all_no_audio = all(
        not item["raw_clip"]["has_audio"]
        and not item["loop_normalized_clip"]["has_audio"]
        and not item["preview_3loop_clip"]["has_audio"]
        for item in candidate_payloads
    )
    loop_durations_ok = all(
        11.9 <= float(item["loop_normalized_clip"]["duration_seconds"]) <= 12.1
        for item in candidate_payloads
    )
    preview_durations_ok = all(
        35.8 <= float(item["preview_3loop_clip"]["duration_seconds"]) <= 36.2
        for item in candidate_payloads
    )
    return {
        "packet_id": PACKET_ID,
        "gate": "rough_assembly_loop_motion_scout_gate",
        "status": "review_ready_pending_human_smooth_crew_loop_keep",
        "human_disposition": "defer",
        "created_utc": CREATED_UTC,
        "created_from_disposition": "tighten",
        "tightened_prior_motion_scout_packet_path": str(CURRENT_SCOUT_ROOT),
        "tightened_prior_motion_scout_manifest_path": str(CURRENT_SCOUT_MANIFEST),
        "review_only": True,
        "loop_motion_scout_only": True,
        "full_runtime_html_proof_created": False,
        "full_runtime_mp4_created": False,
        "final_assembly_created": False,
        "profileId": "cascade-ink-lit-photoreal-v1",
        "source_visual": {
            "carrier": "kept_variant_c_full_frame_source_art",
            "source_art_path": str(SOURCE_ART_PATH),
            "source_art_sha256": sha256(SOURCE_ART_PATH),
            "expected_source_art_sha256": EXPECTED_SOURCE_SHA256,
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "source_art_dimensions": {"width": 1920, "height": 1080, "aspect_ratio": "16:9"},
            "render_dimensions": {"width": WIDTH, "height": HEIGHT, "aspect_ratio": "16:9"},
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
            "fps": FPS,
            "typography": "off",
            "runtime_path_read": "pass" if LTX_RUNTIME_ROOT.exists() and (LTX_RUNTIME_ROOT / "pyproject.toml").exists() else "reject_missing_runtime",
        },
        "loop_contract": {
            "target_duration_seconds": TARGET_LOOP_SECONDS,
            "target_fps": FPS,
            "target_loop_frames": int(TARGET_LOOP_SECONDS * FPS),
            "seam_blend_frames": SEAM_BLEND_FRAMES,
            "seam_blend_seconds": SEAM_BLEND_FRAMES / FPS,
            "crew_crop_box_1024x576": list(CREW_CROP_BOX),
            "crew_mask_feather_pixels": CREW_MASK_FEATHER,
            "motion_target": "exactly_seven_back_view_astronauts_subtle_detectable_asynchronous_living_motion_on_smooth_loop",
            "right_rail_policy": "right_rail_safe_space_preserved_static_background_no_rail_rendered_in_motion_scout",
            "composite_policy": "raw_ltx_full_frame_for_diagnosis_loop_normalized_clips_composite_only_crew_zone_over_static_variant_c_background",
        },
        "candidates": candidate_payloads,
        "contact_sheets": {key: artifact(path) for key, path in contact_sheets.items()},
        "motion_scout_reads": {
            "source_art_hash_read": "pass" if sha256(SOURCE_ART_PATH) == EXPECTED_SOURCE_SHA256 else "reject_hash_mismatch",
            "apple_ltx23_runtime_read": "pass" if LTX_RUNTIME_ROOT.exists() and (LTX_RUNTIME_ROOT / "pyproject.toml").exists() else "reject_missing_runtime",
            "candidate_count_read": "pass_three_candidates" if len(candidate_payloads) == 3 else "reject_missing_candidates",
            "raw_clip_audio_read": "pass_no_audio" if all(not item["raw_clip"]["has_audio"] for item in candidate_payloads) else "reject_audio_present",
            "loop_clip_audio_read": "pass_no_audio" if all_no_audio else "reject_audio_present",
            "loop_duration_read": "pass_12s" if loop_durations_ok else "tighten_duration_not_12s",
            "preview_3loop_duration_read": "pass_36s" if preview_durations_ok else "tighten_duration_not_36s",
            "contact_sheet_read": "pass" if all(path.exists() for path in contact_sheets.values()) else "reject_missing_contact_sheet",
            "forbidden_media_copy_read": "pass_no_audio_caption_transcript_sidecars" if no_forbidden_sidecars else "reject_forbidden_sidecar_found",
            "full_runtime_html_proof_read": "pass_not_created",
            "full_runtime_mp4_read": "pass_not_created",
            "final_assembly_read": "pass_not_created",
            "crew_loop_read": "defer_pending_human_review",
            "loop_seam_read": "defer_pending_human_review",
            "motion_subtlety_read": "defer_pending_human_review",
            "motion_detectability_read": "defer_pending_human_review",
            "crew_count_read": "defer_pending_human_review",
            "crew_motion_authenticity_read": "defer_pending_human_review",
            "uncanny_motion_read": "defer_pending_human_review",
            "identity_logo_text_read": "defer_pending_human_review",
            "background_stability_read": "defer_pending_human_review",
            "pad_hardware_stability_read": "defer_pending_human_review",
            "shuttle_anatomy_stability_read": "defer_pending_human_review",
            "right_rail_safe_space_read": "defer_pending_human_review",
            "long_runtime_carrier_read": "defer_pending_human_review",
        },
        "may_select_loop_candidate_after_human_keep": False,
        "may_create_full_runtime_html_proof": False,
        "may_create_full_runtime_mp4_render": False,
        "may_advance_to_final_assembly": False,
        "may_advance_to_shorts_work": False,
        "may_advance_to_publish_readiness": False,
        "may_youtube_action": False,
        "next_review_question": "Review A/B/C and reply with exactly one response: keep A, keep B, keep C, tighten, or reject.",
    }


def build_readme(manifest: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        f"- {item['label']}: `{item['candidate_id']}`, seed `{item['seed']}`, `{item['prompt_variant_id']}`"
        for item in manifest["candidates"]
    )
    return f"""# Challenger Living Cover Smooth Crew Loop Scout

Packet: `{PACKET_ID}`
Status: `{manifest['status']}`
Human disposition: `defer`

This packet supersedes the prior Apple LTX 2.3 motion scout as a `tighten`. The prior clips proved the runtime path, but not the actual living-cover need: a reusable, smooth, subtle crew loop that can sit behind right-rail chapter motion for the full episode.

## Candidates

{candidate_rows}

## Review Surfaces

- Raw full-frame contact sheet: `{manifest['contact_sheets']['raw_full_frame']['path']}`
- Loop-normalized full-frame contact sheet: `{manifest['contact_sheets']['loop_full_frame']['path']}`
- Loop-normalized crew crop contact sheet: `{manifest['contact_sheets']['loop_crew_crop']['path']}`
- Loop seam contact sheet: `{manifest['contact_sheets']['loop_seam']['path']}`
- 3-loop preview seam contact sheet: `{manifest['contact_sheets']['preview_3loop_seam']['path']}`
- Raw clips: `clips/raw/`
- Loop-normalized clips: `clips/loop_normalized/`
- 3-loop preview clips: `clips/loop_preview_3x/`

## Loop Contract

- Source carrier: kept Variant C full-frame source art.
- Target loop: `12s`, `24fps`, no audio.
- Motion target: exactly seven back-view astronauts in subtle, detectable, asynchronous living motion.
- Composite target: raw LTX full-frame clips are diagnosis only; review loop clips composite the LTX crew zone over static Variant C so the shuttle, pad, and right rail safe space stay locked.
- No walking, waving, synchronized uniform swaying, turning around, faces, readable logos/name patches, generated text, launch, ignition, smoke, fire, camera motion, or pad motion.

No full-runtime HTML proof, full-runtime MP4, final assembly, Shorts work, publish readiness, or YouTube action is authorized from this packet.
"""


def build_review(manifest: dict[str, Any]) -> str:
    candidate_rows = "\n".join(
        "| {label} | `{seed}` | `{variant}` | `{loop}` | `{preview}` |".format(
            label=item["label"],
            seed=item["seed"],
            variant=item["prompt_variant_id"],
            loop=item["loop_normalized_clip"]["path"],
            preview=item["preview_3loop_clip"]["path"],
        )
        for item in manifest["candidates"]
    )
    read_rows = "\n".join(f"| `{key}` | `{value}` |" for key, value in manifest["motion_scout_reads"].items())
    return f"""# Challenger Living Cover Smooth Crew Loop Scout Review

Packet: `{PACKET_ID}`
Gate: `rough_assembly_loop_motion_scout_gate`
Human disposition: `defer`

## What Changed

- The previous Apple LTX scout is recorded as `tighten`, not `keep`.
- This packet narrows the task to a reusable living-cover loop: exactly seven back-view astronauts, subtle detectable motion, smooth repeat.
- Raw LTX full-frame clips are included for diagnosis; loop-normalized review clips composite only the crew zone over the static kept Variant C background.

## Contact Sheets

- Raw full frame: `{manifest['contact_sheets']['raw_full_frame']['path']}`
- Loop-normalized full frame: `{manifest['contact_sheets']['loop_full_frame']['path']}`
- Loop-normalized crew crop: `{manifest['contact_sheets']['loop_crew_crop']['path']}`
- Loop seam: `{manifest['contact_sheets']['loop_seam']['path']}`
- 3-loop preview seam: `{manifest['contact_sheets']['preview_3loop_seam']['path']}`

## Candidates

| Candidate | Seed | Prompt Variant | 12s Loop Clip | 3x Preview Clip |
|---|---:|---|---|---|
{candidate_rows}

## Reads

| Read | Result |
|---|---:|
{read_rows}

## Human Review Options

Reply with exactly one response: `keep A`, `keep B`, `keep C`, `tighten`, or `reject`.

If one candidate is kept, the next artifact should be a full-runtime HTML proof that loops the selected crew-motion carrier behind the existing staged right rail. No full-runtime MP4, final assembly, Shorts, publish readiness, or YouTube action is authorized by this scout packet.
"""


def main() -> None:
    for subdir in [
        "prompts",
        "candidates",
        "clips/raw",
        "clips/loop_normalized",
        "clips/loop_preview_3x",
        "qa/frames",
        "qa/contact_sheets",
        "logs",
        "review",
        "scripts",
        "work",
    ]:
        ensure_dir(PACKET_ROOT / subdir)
    if not SOURCE_ART_PATH.exists():
        raise FileNotFoundError(SOURCE_ART_PATH)
    if sha256(SOURCE_ART_PATH) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Kept Variant C source-art hash mismatch")
    if not CE_BIN.exists():
        raise FileNotFoundError(CE_BIN)
    if not (LTX_RUNTIME_ROOT / "pyproject.toml").exists():
        raise FileNotFoundError(LTX_RUNTIME_ROOT / "pyproject.toml")

    update_current_scout_tighten()
    candidate_payloads = [render_candidate(candidate) for candidate in CANDIDATES]
    contact_sheets = make_contact_sheets(candidate_payloads)

    manifest = build_manifest(candidate_payloads, contact_sheets)
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
        "builder_script": artifact(Path(__file__)),
        **{key: artifact(path) for key, path in contact_sheets.items()},
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"packet_root": str(PACKET_ROOT), "manifest_path": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
