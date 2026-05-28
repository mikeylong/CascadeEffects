#!/usr/bin/env python3
"""Build current first-eight long-form publish-readiness review packages.

The source of truth is the repaired rolling-caption rollout manifest. Each
episode must already have a kept final MP4 render. This script creates local
HTML-first publish-readiness packages only; it never uploads to YouTube.
"""

from __future__ import annotations

import argparse
import html
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import socketserver
import subprocess
import threading
import time
import tomllib
from hashlib import sha256
from urllib.request import Request, urlopen


REPO_ROOT = Path("/Users/mike/Agents_CascadeEffects")
EPISODES_ROOT = Path("/Users/mike/Episodes_CascadeEffects")
ROLLOUT_PATH = (
    REPO_ROOT
    / "references/skills/long_form_video_production_v1/references/episode_visual_system_baselines/rolling_caption_rail_rollout_20260520.json"
)
SERVER_ROOT = EPISODES_ROOT
DEFAULT_PORT = 8899

EPISODE_TOML = {
    "challenger": REPO_ROOT / "episodes/challenger.toml",
    "therac-25": REPO_ROOT / "episodes/therac-25.toml",
    "hyatt-regency": REPO_ROOT / "episodes/hyatt-regency.toml",
    "semmelweis": REPO_ROOT / "episodes/semmelweis.toml",
    "tacoma-narrows": REPO_ROOT / "episodes/tacoma-narrows.toml",
    "piltdown-man": REPO_ROOT / "episodes/piltdown-man.toml",
    "737-max": REPO_ROOT / "episodes/737-max.toml",
    "titanic": REPO_ROOT / "episodes/titanic.toml",
}

LONGFORM_TITLE_OVERRIDES = {
    "hyatt-regency": "Hyatt Regency",
    "tacoma-narrows": "Tacoma Narrows",
    "titanic": "Titanic and the Lifeboat Regulation Gap",
}

SUMMARY_FALLBACKS = {
    "challenger": "A chain of engineering warnings, schedule pressure, and normalized cold-weather risk turned one launch decision into catastrophe.",
    "therac-25": "Software assumptions, missing hardware interlocks, and institutional disbelief let lethal overdoses repeat.",
    "hyatt-regency": "A small connection change turned a public atrium into a hidden load-path failure.",
    "semmelweis": "A simple handwashing observation collided with medical authority, hierarchy, and disbelief.",
    "tacoma-narrows": "A bridge built at the edge of aerodynamic understanding exposed how structure, wind, and confidence can drift apart.",
    "piltdown-man": "A scientific certainty held together by prestige and expectation collapsed when the evidence was finally tested.",
    "737-max": "A familiar aircraft promise hid a new control problem inside software pilots were not prepared to see.",
    "titanic": "A maritime disaster exposed how regulation, design confidence, and lifeboat assumptions lagged behind scale.",
}

GENERIC_TAGS = {
    "challenger": ["Challenger", "NASA", "space shuttle", "engineering failure"],
    "therac-25": ["Therac-25", "medical device safety", "software safety", "radiation therapy"],
    "hyatt-regency": ["Hyatt Regency", "walkway collapse", "structural engineering", "Kansas City"],
    "semmelweis": ["Semmelweis", "medical history", "handwashing", "public health"],
    "tacoma-narrows": ["Tacoma Narrows", "Galloping Gertie", "bridge collapse", "aeroelastic flutter"],
    "piltdown-man": ["Piltdown Man", "scientific fraud", "paleoanthropology", "forgery"],
    "737-max": ["737 MAX", "aviation safety", "MCAS", "Boeing"],
    "titanic": ["Titanic", "lifeboats", "maritime safety", "regulation"],
}

EXPLICIT_CHAPTER_SOURCES = {
    "hyatt-regency": {
        "path": EPISODES_ROOT
        / "Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/metadata/hyatt_metadata_copy_20260517T_upload_readiness/youtube_metadata_copy_manifest.json",
        "format": "metadata_chapters",
        "expected_count": 6,
        "read": "pass_hyatt_metadata_copy_manifest_6_chapters",
    },
    "semmelweis": {
        "path": EPISODES_ROOT
        / "Ep4_Semmelweis/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_f_candidate_c_composition_texture_repair_20260519.json",
        "format": "living_cover_chapters",
        "expected_count": 8,
        "read": "pass_semmelweis_kept_living_cover_cue_map_8_chapters",
    },
    "tacoma-narrows": {
        "path": EPISODES_ROOT
        / "Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/motion_readiness/tacoma_living_cover_motion_readiness_candidate_g_20260517T163317Z/living_cover_cue_map.json",
        "format": "living_cover_chapters",
        "expected_count": 8,
        "read": "pass_tacoma_kept_motion_readiness_cue_map_8_chapters",
    },
    "piltdown-man": {
        "path": EPISODES_ROOT
        / "Ep6_Piltdown-Man/production/long_form_video_v1/living_cover_cue_map_candidate_g_active_microscope_analysis_manifest_20260519.json",
        "format": "section_time_ranges",
        "expected_count": 8,
        "read": "pass_piltdown_kept_cue_map_sections_8_chapters",
    },
    "titanic": {
        "path": EPISODES_ROOT
        / "Ep8_Titanic/production/long_form_video_v1/living_cover/cue_map/living_cover_cue_map_candidate_e_boat_deck_weather_readiness_20260519.json",
        "format": "living_cover_chapters",
        "expected_count": 8,
        "read": "pass_titanic_kept_living_cover_cue_map_8_chapters",
    },
}

INTERNAL_PUBLIC_COPY_TERMS = re.compile(
    r"\b(proof|render|sidecar|publish-readiness|publish readiness|review package|review surface|upload manifest|local package)\b",
    re.IGNORECASE,
)

DEFECTIVE_UPLOAD_REPAIR_EPISODES = {
    "therac-25",
    "hyatt-regency",
    "semmelweis",
    "tacoma-narrows",
    "piltdown-man",
    "titanic",
}

DEFECTIVE_UPLOAD_REPAIR_REQUIRED_QA_READS = {
    "full_decode_read": "pass",
    "dimensions_read": "pass",
    "fps_read": "pass",
    "duration_read": "pass",
    "render_mode_stage_only_read": "pass_stage_rect_matches_1920x1080_viewport",
    "render_mode_ui_chrome_absence_read": "pass_no_visible_review_chrome_controls",
    "forbidden_review_chrome_text_read": "pass_no_forbidden_review_ui_text_in_render_mode",
    "visible_form_controls_absence_read": "pass_no_visible_audio_form_controls_in_render_mode",
    "render_viewport_overflow_read": "pass_no_render_mode_viewport_overflow",
    "visual_nonblack_stage_read": "pass_stage_screenshots_nonblack_with_luma_variance",
    "source_art_visibility_read": "pass_source_art_visible_in_render_mode",
    "stage_luma_variance_read": "pass_stage_luma_and_variance_above_black_screen_floor",
    "mp4_black_frame_guard_read": "pass_mp4_sample_frames_nonblack_with_luma_variance",
    "youtube_upload_black_screen_block_read": "pass_black_screen_preflight_allows_render_continuation",
}


def utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path, role: str | None = None) -> dict:
    data = {
        "path": str(path),
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
    }
    if role:
        data["role"] = role
    return data


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def parse_selected_episode_ids(values: list[str]) -> set[str]:
    selected: set[str] = set()
    for value in values:
        for item in str(value).split(","):
            episode_id = item.strip()
            if episode_id:
                selected.add(episode_id)
    return selected


def parse_manifest_overrides(values: list[str]) -> dict[str, Path]:
    overrides: dict[str, Path] = {}
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        if "=" not in text:
            raise RuntimeError(f"--manifest-override must use episode_id=/absolute/path: {text}")
        episode_id, raw_path = text.split("=", 1)
        episode_id = episode_id.strip()
        path = Path(raw_path.strip())
        if not episode_id or not path.is_file():
            raise RuntimeError(f"Invalid manifest override: {text}")
        overrides[episode_id] = path
    return overrides


def rollout_entries_for_build(rollout: dict, selected: set[str], overrides: dict[str, Path]) -> list[dict]:
    source_entries = rollout.get("episodes")
    if not isinstance(source_entries, list):
        raise RuntimeError(f"Rollout manifest lacks episodes list: {ROLLOUT_PATH}")
    entries: list[dict] = []
    found: set[str] = set()
    for source_entry in source_entries:
        episode_id = str(source_entry.get("episode_id", "")).strip()
        if selected and episode_id not in selected:
            continue
        entry = dict(source_entry)
        if episode_id in overrides:
            manifest_path = overrides[episode_id]
            entry["manifest_path"] = str(manifest_path)
            entry["output_dir"] = str(manifest_path.parent)
            entry["player_path"] = str(manifest_path.parent / "player.html")
        entries.append(entry)
        found.add(episode_id)
    missing_selected = selected - found
    if missing_selected:
        raise RuntimeError(f"Selected episode ids not found in rollout: {', '.join(sorted(missing_selected))}")
    missing_overrides = set(overrides) - found
    if missing_overrides:
        raise RuntimeError(f"Manifest overrides were not selected: {', '.join(sorted(missing_overrides))}")
    if not entries:
        raise RuntimeError("No rollout entries selected for package build.")
    return entries


def copy_artifact(source: Path, dest: Path, role: str | None = None) -> dict:
    if not source.is_file():
        raise FileNotFoundError(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return artifact(dest, role)


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def load_episode_toml(episode_id: str) -> dict:
    path = EPISODE_TOML[episode_id]
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    data["_toml_path"] = str(path)
    return data


def parse_publish_notes(path: str | None) -> tuple[str, str]:
    if not path:
        return "", ""
    note_path = Path(path)
    if not note_path.is_file():
        return "", ""
    text = note_path.read_text(errors="replace")
    summary = extract_markdown_section(text, "Summary")
    description = extract_markdown_section(text, "Description")
    if "TODO:" in summary:
        summary = ""
    if "TODO:" in description:
        description = ""
    return summary.strip(), description.strip()


def extract_markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def episode_title(episode_id: str, episode: dict) -> str:
    release_youtube = episode.get("release", {}).get("youtube", {})
    title = release_youtube.get("title") or episode.get("title") or episode_id
    if "#Shorts" in title or "short" in title.lower():
        title = LONGFORM_TITLE_OVERRIDES.get(episode_id, episode.get("title") or episode_id)
    return LONGFORM_TITLE_OVERRIDES.get(episode_id, title)


def episode_summary(episode_id: str, episode: dict) -> str:
    release_youtube = episode.get("release", {}).get("youtube", {})
    notes_summary, _ = parse_publish_notes(release_youtube.get("description_path"))
    return notes_summary or episode.get("summary") or SUMMARY_FALLBACKS[episode_id]


def episode_description(episode_id: str, episode: dict, duration_seconds: float) -> str:
    release_youtube = episode.get("release", {}).get("youtube", {})
    _, notes_description = parse_publish_notes(release_youtube.get("description_path"))
    if notes_description:
        return notes_description
    title = episode_title(episode_id, episode)
    summary = episode_summary(episode_id, episode)
    minutes = max(1, round(duration_seconds / 60))
    return (
        f"{title} is a Cascade Effects episode about how small signals become system consequences.\n\n"
        f"{summary}\n\n"
        f"Runtime: about {minutes} minutes.\n\n"
        "Cascade Effects traces failures through mechanism, incentives, and institutional blind spots."
    )


def timestamp_to_seconds(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    if "-" in text:
        text = text.split("-", 1)[0].strip()
    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        return float(text)
    except ValueError as exc:
        raise RuntimeError(f"Could not parse chapter timestamp `{value}`") from exc


def normalize_chapter(seconds: float, label: object) -> dict:
    safe_seconds = max(0.0, float(seconds))
    safe_label = str(label or "").strip()
    if not safe_label:
        raise RuntimeError("Chapter label is empty.")
    return {
        "time": seconds_to_stamp(safe_seconds),
        "seconds": round(safe_seconds, 3),
        "label": safe_label,
    }


def chapters_from_explicit_source(episode_id: str) -> tuple[list[dict], dict]:
    spec = EXPLICIT_CHAPTER_SOURCES[episode_id]
    source_path = Path(spec["path"])
    if not source_path.is_file():
        raise FileNotFoundError(f"Missing explicit chapter source for {episode_id}: {source_path}")
    payload = read_json(source_path)
    chapters: list[dict] = []
    if spec["format"] == "metadata_chapters":
        for item in payload.get("chapters", []):
            chapters.append(normalize_chapter(timestamp_to_seconds(item.get("time") or item.get("timestamp")), item.get("label") or item.get("title")))
    elif spec["format"] == "living_cover_chapters":
        for item in payload.get("chapters", []):
            start = item.get("story_start_seconds")
            if start is None:
                start = timestamp_to_seconds(item.get("story_start_timecode") or item.get("start_time") or item.get("timecode"))
            chapters.append(normalize_chapter(float(start), item.get("title") or item.get("label")))
    elif spec["format"] == "section_time_ranges":
        for item in payload.get("sections", []):
            chapters.append(normalize_chapter(timestamp_to_seconds(item.get("time_range")), item.get("rail_title") or item.get("title")))
    else:
        raise RuntimeError(f"Unsupported explicit chapter source format for {episode_id}: {spec['format']}")

    expected_count = int(spec["expected_count"])
    if len(chapters) != expected_count:
        raise RuntimeError(f"{episode_id} chapter source yielded {len(chapters)} chapters; expected {expected_count}: {source_path}")
    if [chapter["label"] for chapter in chapters] == ["Opening", "Main episode", "Closing"]:
        raise RuntimeError(f"{episode_id} explicit chapter source unexpectedly yielded the fallback chapter set.")
    reads = {
        "chapter_source_read": str(spec["read"]),
        "chapter_source_path": str(source_path),
        "chapter_source_sha256": file_sha256(source_path),
        "chapter_fallback_read": "pass_explicit_full_chapter_source_used_no_fallback",
        "youtube_description_chapter_count_read": f"pass_{len(chapters)}_chapter_lines_available_for_youtube_description",
    }
    return chapters, reads


def derive_chapters(episode_id: str, episode: dict, duration_seconds: float) -> tuple[list[dict], dict]:
    if episode_id in EXPLICIT_CHAPTER_SOURCES:
        return chapters_from_explicit_source(episode_id)

    acts = episode.get("visual_research", {}).get("acts") or []
    if not acts:
        chapters = [
            {"time": "0:00", "seconds": 0, "label": "Opening"},
            {"time": seconds_to_stamp(4), "seconds": 4, "label": "Main episode"},
            {"time": seconds_to_stamp(max(0, duration_seconds - 60)), "seconds": max(0, duration_seconds - 60), "label": "Closing"},
        ]
        return chapters, {
            "chapter_source_read": "fallback_no_explicit_full_chapter_source_declared",
            "chapter_fallback_read": "pass_fallback_allowed_for_episode_without_declared_full_source",
            "youtube_description_chapter_count_read": f"pass_{len(chapters)}_chapter_lines_available_for_youtube_description",
        }
    estimates = [float(act.get("estimated_seconds") or 0) for act in acts]
    total = sum(estimates) or duration_seconds
    cursor = 0.0
    chapters = [{"time": "0:00", "seconds": 0, "label": "Opening"}]
    for index, act in enumerate(acts):
        if index == 0:
            start = 4.0
        else:
            start = min(duration_seconds - 1, (cursor / total) * duration_seconds)
        label = str(act.get("title") or f"Chapter {index + 1}")
        chapters.append({"time": seconds_to_stamp(start), "seconds": round(start, 3), "label": label})
        cursor += estimates[index]
    closing = max(0, duration_seconds - 60)
    if closing > chapters[-1]["seconds"] + 30:
        chapters.append({"time": seconds_to_stamp(closing), "seconds": round(closing, 3), "label": "Closing"})
    return chapters, {
        "chapter_source_read": "pass_episode_toml_visual_research_acts",
        "chapter_fallback_read": "pass_visual_research_acts_used_no_three_chapter_fallback",
        "youtube_description_chapter_count_read": f"pass_{len(chapters)}_chapter_lines_available_for_youtube_description",
    }


def seconds_to_stamp(seconds: float) -> str:
    seconds = int(max(0, round(seconds)))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def vtt_to_srt(vtt_path: Path, srt_path: Path) -> None:
    lines = vtt_path.read_text(errors="replace").splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip("\ufeff")
        if not stripped:
            if current:
                blocks.append(current)
                current = []
            continue
        if stripped == "WEBVTT" or stripped.startswith("NOTE"):
            continue
        current.append(stripped)
    if current:
        blocks.append(current)

    output: list[str] = []
    index = 1
    for block in blocks:
        timing_index = next((i for i, item in enumerate(block) if "-->" in item), -1)
        if timing_index < 0:
            continue
        cue_text = block[timing_index + 1 :]
        if not cue_text:
            continue
        timing = block[timing_index].replace(".", ",")
        output.append(str(index))
        output.append(timing)
        output.extend(cue_text)
        output.append("")
        index += 1
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.write_text("\n".join(output), encoding="utf-8")


def public_copy_read(metadata: dict) -> str:
    text = "\n".join(
        [
            metadata.get("title", ""),
            metadata.get("description", ""),
            "\n".join(metadata.get("tags", [])),
            "\n".join(metadata.get("hashtags", [])),
            "\n".join(chapter.get("label", "") for chapter in metadata.get("chapters", [])),
        ]
    )
    if INTERNAL_PUBLIC_COPY_TERMS.search(text):
        return "tighten_internal_terms_found_in_public_metadata"
    return "pass_generated_public_metadata_no_internal_terms"


def ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def run_contract_validator(
    *,
    manifest_path: Path,
    intent: str,
    contract_id: str = "first-eight-longform-v1",
    youtube_action: str = "",
) -> dict:
    command = [
        "node",
        str(REPO_ROOT / "scripts/validate_cascade_effects_output_contract.mjs"),
        "--manifest",
        str(manifest_path),
        "--intent",
        intent,
        "--contract-id",
        contract_id,
        "--write-receipt",
        "auto",
        "--json",
    ]
    if youtube_action:
        command.extend(["--youtube-action", youtube_action])
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Production contract validation failed:\n"
            f"COMMAND: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return json.loads(result.stdout)


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "CascadeRangeHTTP/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def send_head(self):  # noqa: ANN201
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / "index.html"
        if not path.is_file():
            self.send_error(404, "File not found")
            return None
        ctype = self.guess_type(str(path))
        size = path.stat().st_size
        range_header = self.headers.get("Range")
        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else size - 1
                end = min(end, size - 1)
                if start >= size or end < start:
                    self.send_error(416, "Requested Range Not Satisfiable")
                    return None
                self.send_response(206)
                self.send_header("Content-type", ctype)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.end_headers()
                handle = path.open("rb")
                handle.seek(start)
                self.range_remaining = end - start + 1
                return handle
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        return path.open("rb")

    def copyfile(self, source, outputfile) -> None:  # noqa: ANN001
        remaining = getattr(self, "range_remaining", None)
        if remaining is None:
            shutil.copyfileobj(source, outputfile)
            return
        while remaining > 0:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def start_validation_server(root: Path, port: int):
    handler = lambda *args, **kwargs: RangeRequestHandler(*args, directory=str(root), **kwargs)
    server = ReusableThreadingTCPServer(("127.0.0.1", port), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def http_status(url: str, range_header: str | None = None) -> int:
    request = Request(url)
    if range_header:
        request.add_header("Range", range_header)
    with urlopen(request, timeout=10) as response:
        response.read(32)
        return response.status


def local_url(path: Path, port: int) -> str:
    return f"http://127.0.0.1:{port}/{rel(SERVER_ROOT, path)}"


def build_review_html(package: dict, package_root: Path) -> str:
    metadata = package["youtube_metadata"]
    chapters = metadata.get("chapters", [])
    qa_frames = package["local_assets"].get("qa_frames", {})
    chapter_items = "\n".join(
        f"<li><button type=\"button\" data-seconds=\"{chapter['seconds']}\">{html.escape(chapter['time'])}</button> {html.escape(chapter['label'])}</li>"
        for chapter in chapters
    )
    frame_items = "\n".join(
        f"<figure><img src=\"{html.escape(frame['rel'])}\" alt=\"{html.escape(name)}\"><figcaption>{html.escape(name)}</figcaption></figure>"
        for name, frame in qa_frames.items()
    )
    tag_items = ", ".join(html.escape(tag) for tag in metadata.get("tags", []))
    reads = package["reads"]
    read_rows = "\n".join(
        f"<tr><th>{html.escape(key)}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in sorted(reads.items())
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(package['episode_title'])} Publish Readiness</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #111318; color: #f4f0e8; }}
    body {{ margin: 0; background: #111318; color: #f4f0e8; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 30px; line-height: 1.1; margin: 0 0 8px; }}
    h2 {{ font-size: 18px; margin: 28px 0 12px; }}
    p {{ color: #cbc4b9; line-height: 1.5; }}
    video {{ width: 100%; aspect-ratio: 16 / 9; background: #000; border: 1px solid #3e4652; }}
    .locks {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; margin: 18px 0; }}
    .lock {{ border: 1px solid #3e4652; padding: 10px 12px; background: #171b22; }}
    .lock b {{ display: block; font-size: 12px; color: #aab4c0; }}
    button {{ background: #273243; color: #f4f0e8; border: 1px solid #56657a; padding: 6px 10px; cursor: pointer; }}
    button:hover {{ background: #334258; }}
    ul {{ padding-left: 20px; }}
    li {{ margin: 8px 0; }}
    .frames {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    figure {{ margin: 0; border: 1px solid #3e4652; background: #171b22; }}
    figure img {{ display: block; width: 100%; height: auto; }}
    figcaption {{ padding: 8px 10px; color: #aab4c0; font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #303741; padding: 7px 8px; vertical-align: top; }}
    th {{ width: 320px; color: #aab4c0; font-weight: 600; }}
    code {{ color: #f2c46d; }}
  </style>
</head>
<body>
<main>
  <h1>{html.escape(package['episode_title'])}</h1>
  <p>{html.escape(metadata.get('description', ''))}</p>
  <video id="episodeVideo" controls preload="metadata" poster="{html.escape(package['local_assets']['thumbnail_candidate']['rel'])}">
    <source src="{html.escape(package['local_assets']['mp4']['rel'])}" type="video/mp4">
    <track kind="captions" src="{html.escape(package['local_assets']['vtt']['rel'])}" srclang="en" label="English" default>
  </video>
  <section class="locks">
    <div class="lock"><b>Final assembly</b>{html.escape(package['final_assembly_disposition'])}</div>
    <div class="lock"><b>Publish readiness</b>{html.escape(package['human_disposition'])}</div>
    <div class="lock"><b>YouTube action</b>{html.escape(str(package['upload_locks']['may_youtube_action']))}</div>
    <div class="lock"><b>Upload performed</b>{html.escape(str(package['upload_locks']['upload_performed']))}</div>
  </section>
  <h2>Chapters</h2>
  <ul>{chapter_items}</ul>
  <h2>Public Metadata</h2>
  <p><strong>Title:</strong> {html.escape(metadata.get('title', ''))}</p>
  <p><strong>Tags:</strong> {tag_items}</p>
  <h2>QA Frames</h2>
  <div class="frames">{frame_items}</div>
  <h2>Reads</h2>
  <table>{read_rows}</table>
</main>
<script>
  const video = document.getElementById('episodeVideo');
  document.querySelectorAll('[data-seconds]').forEach((button) => {{
    button.addEventListener('click', () => {{
      video.currentTime = Number(button.dataset.seconds || 0);
      video.play();
    }});
  }});
</script>
</body>
</html>
"""


def semmelweis_corrective_replacement_allowed(episode_id: str, proof_manifest: dict, render_manifest: dict) -> bool:
    if episode_id != "semmelweis":
        return False
    qa_reads = render_manifest.get("qa_reads", {}) if isinstance(render_manifest.get("qa_reads"), dict) else {}
    required_reads = {
        "full_decode_read": "pass",
        "dimensions_read": "pass",
        "fps_read": "pass",
        "duration_read": "pass",
        "render_mode_stage_only_read": "pass_stage_rect_matches_1920x1080_viewport",
        "render_mode_ui_chrome_absence_read": "pass_no_visible_review_chrome_controls",
        "forbidden_review_chrome_text_read": "pass_no_forbidden_review_ui_text_in_render_mode",
        "visible_form_controls_absence_read": "pass_no_visible_audio_form_controls_in_render_mode",
        "render_viewport_overflow_read": "pass_no_render_mode_viewport_overflow",
    }
    if not all(qa_reads.get(key) == expected for key, expected in required_reads.items()):
        return False
    source_html = render_manifest.get("source_html_proof", {}) if isinstance(render_manifest.get("source_html_proof"), dict) else {}
    return bool(source_html.get("corrective_review_render_from_unkept_proof") or proof_manifest.get("human_disposition") == "defer")


def defective_upload_repair_replacement_allowed(episode_id: str, proof_manifest: dict, render_manifest: dict) -> bool:
    if episode_id not in DEFECTIVE_UPLOAD_REPAIR_EPISODES:
        return False
    qa_reads = render_manifest.get("qa_reads", {}) if isinstance(render_manifest.get("qa_reads"), dict) else {}
    for key, expected in DEFECTIVE_UPLOAD_REPAIR_REQUIRED_QA_READS.items():
        if qa_reads.get(key) != expected:
            return False
    if episode_id == "semmelweis" and qa_reads.get("semmelweis_deterministic_ambient_read") != "pass_deterministic_ambient_state_time_locked_no_css_animation_loop":
        return False

    source_repair = proof_manifest.get("defective_upload_source_repair", {})
    source_repair_reads = source_repair.get("reads", {}) if isinstance(source_repair, dict) else {}
    source_html = render_manifest.get("source_html_proof", {}) if isinstance(render_manifest.get("source_html_proof"), dict) else {}
    source_html_reads = source_html.get("reads", {}) if isinstance(source_html, dict) else {}
    reads = {
        **(proof_manifest.get("reads", {}) if isinstance(proof_manifest.get("reads"), dict) else {}),
        **source_repair_reads,
        **source_html_reads,
    }
    if episode_id == "semmelweis":
        player_path = Path(str(source_html.get("player_path") or proof_manifest.get("player_path") or ""))
        if not player_path.is_file():
            return False
        player_text = player_path.read_text(errors="replace")
        return (
            "ce-semmelweis-deterministic-ambient-style" in player_text
            and "ce-semmelweis-deterministic-ambient-runtime" in player_text
            and "--ce-ambient-seconds" in player_text
        )
    preservation_read = reads.get("render_mode_stage_child_preservation_read")
    return preservation_read in {
        "pass_unsafe_render_mode_main_child_hiding_selector_removed",
        "pass_stage_children_not_hidden_by_review_chrome_guard",
    }


def build_package(entry: dict, stamp: str, port: int, approve_unlisted_upload: bool) -> dict:
    episode_id = entry["episode_id"]
    episode = load_episode_toml(episode_id)
    proof_manifest_path = Path(entry["manifest_path"])
    proof_manifest = read_json(proof_manifest_path)
    render_manifest_path = Path(proof_manifest["rendered_video_proof"]["manifest_path"])
    render_manifest = read_json(render_manifest_path)
    final_mp4_path = Path(proof_manifest["rendered_video_proof"]["mp4_path"])

    semmelweis_corrective_replacement = semmelweis_corrective_replacement_allowed(episode_id, proof_manifest, render_manifest)
    defective_upload_repair_replacement = defective_upload_repair_replacement_allowed(episode_id, proof_manifest, render_manifest)
    corrective_replacement = semmelweis_corrective_replacement or defective_upload_repair_replacement

    if proof_manifest.get("human_disposition") != "keep" and not corrective_replacement:
        raise RuntimeError(f"{episode_id} proof manifest is not kept")
    if render_manifest.get("human_disposition") != "keep" and not corrective_replacement:
        raise RuntimeError(f"{episode_id} render manifest is not kept")
    if not proof_manifest.get("may_advance_to_publish_readiness") and not corrective_replacement:
        raise RuntimeError(f"{episode_id} publish-readiness gate is closed")
    if render_manifest.get("qa_reads", {}).get("full_decode_read") != "pass":
        raise RuntimeError(f"{episode_id} render manifest lacks full decode pass")

    youtube_root = proof_manifest_path.parent
    while youtube_root.name != "youtube" and youtube_root != youtube_root.parent:
        youtube_root = youtube_root.parent
    if youtube_root.name != "youtube":
        raise RuntimeError(f"Could not find youtube root for {proof_manifest_path}")

    package_id = f"{episode_id}_publish_readiness_{stamp}"
    package_root = youtube_root / "publish_readiness" / package_id
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True)

    media_dir = package_root / "media"
    caption_dir = package_root / "captions"
    qa_dir = package_root / "qa_frames"
    provenance_dir = package_root / "provenance"
    metadata_dir = package_root / "metadata"
    source_dir = package_root / "source_factcheck"
    thumb_dir = package_root / "thumbnail"

    mp4_dest = media_dir / final_mp4_path.name
    copied_mp4 = copy_artifact(final_mp4_path, mp4_dest, "kept_final_assembly_mp4")

    vtt_source = Path(render_manifest["caption_package"]["youtube_upload_sidecar_vtt"]["path"])
    vtt_dest = caption_dir / vtt_source.name
    copied_vtt = copy_artifact(vtt_source, vtt_dest, "youtube_caption_sidecar_vtt")
    srt_dest = caption_dir / (vtt_source.stem + ".srt")
    vtt_to_srt(vtt_dest, srt_dest)
    copied_srt = artifact(srt_dest, "generated_youtube_caption_sidecar_srt")

    copied_render_manifest = copy_artifact(render_manifest_path, provenance_dir / "render_manifest.json", "render_manifest_copy")
    copied_proof_manifest = copy_artifact(proof_manifest_path, provenance_dir / "rough_assembly_manifest.json", "rough_assembly_manifest_copy")
    final_review = proof_manifest["rendered_video_proof"].get("review_packet_path")
    copied_final_review = (
        copy_artifact(Path(final_review), provenance_dir / "final_assembly_review_packet.md", "final_assembly_review_packet_copy")
        if final_review and Path(final_review).is_file()
        else None
    )

    qa_frames = {}
    for name, frame in sorted((render_manifest.get("qa_frames") or {}).items()):
        source = Path(frame["path"])
        frame_dest = qa_dir / f"{name}_{source.name}"
        qa_frames[name] = copy_artifact(source, frame_dest, f"qa_frame_{name}")

    browser_qa_path = render_manifest.get("caption_package", {}).get("browser_caption_qa_path")
    copied_browser_qa = None
    if browser_qa_path and Path(browser_qa_path).is_file():
        copied_browser_qa = copy_artifact(Path(browser_qa_path), provenance_dir / "browser_caption_qa.json", "browser_caption_qa_copy")

    thumbnail_source = next(
        (
            Path(frame["path"])
            for key, frame in (render_manifest.get("qa_frames") or {}).items()
            if key in ("voice_start", "start")
        ),
        next(iter([Path(frame["path"]) for frame in (render_manifest.get("qa_frames") or {}).values()]), None),
    )
    if thumbnail_source is None:
        raise RuntimeError(f"{episode_id} has no QA frame for thumbnail candidate")
    thumbnail_dest = thumb_dir / f"{episode_id}_thumbnail_candidate.jpg"
    copied_thumbnail = copy_artifact(thumbnail_source, thumbnail_dest, "thumbnail_candidate_from_kept_mp4_frame")

    duration = float(render_manifest["output"]["duration_seconds"])
    title = episode_title(episode_id, episode)
    chapters, chapter_reads = derive_chapters(episode_id, episode, duration)
    metadata = {
        "title": title,
        "description": episode_description(episode_id, episode, duration),
        "chapters": chapters,
        "tags": sorted(set(["Cascade Effects", "systems failure", "documentary", *GENERIC_TAGS[episode_id]])),
        "hashtags": ["#CascadeEffects"],
        "category": "Education",
        "language": "en",
        "made_for_kids": False,
        "paid_promotion": False,
        "privacy_after_explicit_approval": "unlisted",
        "public_release_policy": "manual_youtube_studio_only",
    }
    metadata_path = metadata_dir / "youtube_metadata.json"
    write_json(metadata_path, metadata)
    metadata_artifact = artifact(metadata_path, "generated_youtube_metadata")

    source_factcheck = {
        "status": "pending_current_long_form_source_factcheck_backfill",
        "episode_id": episode_id,
        "note": "No current long-form source-factcheck manifest was found for this rolling-caption MP4 package. Review can continue, but publish-readiness keep should not waive this without a named human decision.",
        "source_factcheck_status_read": "pending_current_source_factcheck_manifest_missing",
    }
    if episode_id == "hyatt-regency":
        source_manifest = (
            EPISODES_ROOT
            / "Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/source_factcheck/hyatt_source_factcheck_packet_20260517T_upload_readiness/source_factcheck_manifest.json"
        )
        source_review = source_manifest.parent / "source_factcheck_review_packet.md"
        if source_manifest.is_file():
            copied_source_manifest = copy_artifact(source_manifest, source_dir / "source_factcheck_manifest.json", "source_factcheck_manifest")
            source_factcheck = read_json(source_manifest)
            source_factcheck["packaged_manifest"] = copied_source_manifest
            if source_review.is_file():
                source_factcheck["packaged_review_packet"] = copy_artifact(
                    source_review, source_dir / "source_factcheck_review_packet.md", "source_factcheck_review_packet"
                )
    write_json(source_dir / "source_factcheck_manifest.json", source_factcheck)

    ffprobe_data = ffprobe(mp4_dest)
    video_stream = next((stream for stream in ffprobe_data.get("streams", []) if stream.get("codec_type") == "video"), None)
    audio_stream = next((stream for stream in ffprobe_data.get("streams", []) if stream.get("codec_type") == "audio"), None)
    metadata_read = public_copy_read(metadata)
    source_factcheck_read = (
        "pass_verified_for_publish_readiness"
        if source_factcheck.get("status") == "verified_for_publish_readiness"
        else source_factcheck.get("source_factcheck_status_read", "pending_current_source_factcheck_manifest_missing")
    )

    upload_locks = {
        "publish_ready": False,
        "youtube_upload_ready": False,
        "public_release_ready": False,
        "may_youtube_action": False,
        "upload_allowed": False,
        "upload_performed": False,
        "upload_action_enabled_in_review_html": False,
        "public_release": False,
        "review_upload_privacy_after_approval": "unlisted_after_publish_readiness_keep_and_explicit_upload_approval",
    }
    blockers = [
        "Publish-readiness package human keep is required before any YouTube review upload.",
        "Explicit upload authorization is required after publish-readiness keep.",
        "YouTube Content ID/music claim status must be checked after upload processing.",
        "Public release remains manual.",
    ]
    if not str(source_factcheck_read).startswith("pass"):
        blockers.insert(0, "Current long-form source/fact-check manifest is pending or missing.")

    reads = {
        **(render_manifest.get("qa_reads") or {}),
        "html_primary_review_read": "pass_review_html_created_as_primary_publish_readiness_artifact",
        "html_media_refs_read": "pending_package_local_media_ref_check",
        "html_native_video_scrub_read": "pass_native_mp4_controls_and_chapter_jump_buttons_present",
        "html_range_server_read": "pending_http_range_probe",
        "html_canonical_review_url_read": "pending_http_review_url_probe",
        "publish_readiness_package_local_asset_copy_read": "pass_package_local_assets_copied",
        "html_upload_lock_read": "pass_upload_locks_visible_and_false",
        "youtube_metadata_copywriting_read": metadata_read,
        "public_metadata_copy_read": metadata_read,
        **chapter_reads,
        "public_tag_relevance_read": "pass_episode_specific_tags_present",
        "source_factcheck_status_read": source_factcheck_read,
        "caption_sidecar_packaged_read": "pass_vtt_and_generated_srt_packaged",
        "final_mp4_packaged_read": "pass",
        "ffprobe_stream_read": "pass_video_and_audio_streams_present" if video_stream and audio_stream else "reject_missing_video_or_audio_stream",
        "youtube_upload_ready_read": "blocked_pending_publish_readiness_package_keep_and_explicit_upload_authorization",
        "youtube_public_release_read": "blocked_manual_youtube_studio_only",
    }
    if approve_unlisted_upload:
        reads["unlisted_review_upload_approval_read"] = "pass_user_requested_defective_upload_repair_replacement_unlisted_upload_2026_05_26"
    if semmelweis_corrective_replacement:
        reads["semmelweis_corrective_replacement_read"] = "pass_clean_ui_chrome_replacement_render_user_requested_upload"
    if defective_upload_repair_replacement:
        reads["defective_upload_repair_replacement_read"] = "pass_user_requested_replacement_render_passed_black_screen_source_art_preflight"

    package = {
        "packet_id": package_id,
        "episode_id": episode_id,
        "production_contract": {
            "contract_id": "first-eight-longform-v1",
            "intent": "successor",
            "contract_registry_path": str(REPO_ROOT / "references/production_contracts/cascade_effects_output_contracts.v1.json"),
            "youtube_action_approval_read": "pass_user_requested_defective_upload_repair_replacement_unlisted_upload_2026_05_26"
            if approve_unlisted_upload
            else "blocked_pending_publish_readiness_keep_and_explicit_upload_authorization",
        },
        "episode_title": title,
        "workflow": "long_form_video_production_v1",
        "stage": "publish_readiness",
        "lifecycle_stage": "publish_readiness",
        "current_gate": "publish_readiness_review",
        "status": "review_ready_pending_human_publish_readiness_keep",
        "human_disposition": "pending",
        "final_assembly_disposition": "keep",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "primary_review_artifact": {"path": "review.html", "sha256": "TBD", "bytes": 0},
        "publish_readiness_review_html_path": str(package_root / "review.html"),
        "publish_readiness_canonical_review_url": local_url(package_root / "review.html", port),
        "remote_review": {
            "status": "not_published",
            "remote_review_url": f"https://cascadeeffects.tv/reviews/publish-readiness/{episode_id}",
            "storage_policy": "normalized_manifest_and_small_evidence_assets_only",
            "large_video_upload_allowed": False,
            "video_host": "youtube_unlisted_after_explicit_approval_only",
        },
        "source_final_render": {
            "manifest_path": str(render_manifest_path),
            "manifest_sha256": file_sha256(render_manifest_path),
            "mp4_path": str(final_mp4_path),
            "mp4_sha256": file_sha256(final_mp4_path),
        },
        "source_html_proof": render_manifest.get("source_html_proof", {}),
        "local_assets": {
            "mp4": {**copied_mp4, "rel": rel(package_root, mp4_dest)},
            "vtt": {**copied_vtt, "rel": rel(package_root, vtt_dest)},
            "srt": {**copied_srt, "rel": rel(package_root, srt_dest)},
            "thumbnail_candidate": {**copied_thumbnail, "rel": rel(package_root, thumbnail_dest)},
            "qa_frames": {name: {**frame, "rel": rel(package_root, Path(frame["path"]))} for name, frame in qa_frames.items()},
            "render_manifest": {**copied_render_manifest, "rel": rel(package_root, provenance_dir / "render_manifest.json")},
            "rough_assembly_manifest": {**copied_proof_manifest, "rel": rel(package_root, provenance_dir / "rough_assembly_manifest.json")},
            "final_assembly_review_packet": (
                {**copied_final_review, "rel": rel(package_root, provenance_dir / "final_assembly_review_packet.md")}
                if copied_final_review
                else None
            ),
            "browser_caption_qa": (
                {**copied_browser_qa, "rel": rel(package_root, provenance_dir / "browser_caption_qa.json")}
                if copied_browser_qa
                else None
            ),
        },
        "media": {
            "final_mp4": {"path": rel(package_root, mp4_dest), "sha256": copied_mp4["sha256"], "bytes": copied_mp4["bytes"]},
            "caption_vtt": {"path": rel(package_root, vtt_dest), "sha256": copied_vtt["sha256"], "bytes": copied_vtt["bytes"]},
            "caption_srt": {"path": rel(package_root, srt_dest), "sha256": copied_srt["sha256"], "bytes": copied_srt["bytes"]},
            "thumbnail_candidate": {
                "path": rel(package_root, thumbnail_dest),
                "sha256": copied_thumbnail["sha256"],
                "bytes": copied_thumbnail["bytes"],
            },
        },
        "youtube_metadata": {
            **metadata,
            "metadata_path": rel(package_root, metadata_path),
            "metadata_sha256": metadata_artifact["sha256"],
        },
        "source_factcheck": source_factcheck,
        "ffprobe": {
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "duration_seconds": float(ffprobe_data.get("format", {}).get("duration", 0)),
        },
        "reads": reads,
        "blockers": blockers,
        "locks": upload_locks,
        "upload_locks": upload_locks,
        "publish_ready": False,
        "youtube_upload_ready": False,
        "public_release_ready": False,
        "may_youtube_action": False,
        "may_advance_to_upload": False,
        "upload_allowed": False,
        "upload_performed": False,
        "next_review_question": "Review publish readiness and reply with exactly one disposition: keep, tighten, or reject.",
    }

    review_html = build_review_html(package, package_root)
    review_path = package_root / "review.html"
    review_path.write_text(review_html)
    package["primary_review_artifact"] = {
        "path": "review.html",
        "sha256": file_sha256(review_path),
        "bytes": review_path.stat().st_size,
    }
    package["publish_readiness_review_html_sha256"] = package["primary_review_artifact"]["sha256"]

    upload_manifest = {
        "episode_id": episode_id,
        "status": "blocked_pending_publish_readiness_keep_and_explicit_upload_authorization",
        "privacy_after_explicit_approval": "unlisted",
        "video": package["media"]["final_mp4"],
        "captions": {
            "vtt": package["media"]["caption_vtt"],
            "srt": package["media"]["caption_srt"],
        },
        "thumbnail": package["media"]["thumbnail_candidate"],
        "metadata": package["youtube_metadata"],
        "locks": upload_locks,
        "may_youtube_action": False,
        "upload_allowed": False,
        "upload_performed": False,
    }
    write_json(package_root / "youtube_upload_manifest.json", upload_manifest)
    write_json(package_root / "publish_readiness_manifest.json", package)

    # Update source manifests with package pointer while preserving upload locks.
    proof_manifest["publish_readiness_package"] = {
        "packet_path": str(package_root),
        "manifest_path": str(package_root / "publish_readiness_manifest.json"),
        "review_html_path": str(review_path),
        "canonical_review_url": package["publish_readiness_canonical_review_url"],
        "status": package["status"],
        "human_disposition": "pending",
        "created_utc": package["created_utc"],
    }
    proof_manifest["publish_ready"] = False
    proof_manifest["youtube_upload_ready"] = False
    proof_manifest["may_youtube_action"] = False
    proof_manifest["upload_allowed"] = False
    proof_manifest["upload_performed"] = False
    write_json(proof_manifest_path, proof_manifest)

    render_manifest["publish_readiness_package"] = proof_manifest["publish_readiness_package"]
    render_manifest["publish_ready"] = False
    render_manifest["youtube_upload_ready"] = False
    render_manifest["may_youtube_action"] = False
    render_manifest["upload_allowed"] = False
    render_manifest["upload_performed"] = False
    write_json(render_manifest_path, render_manifest)

    package["source_final_render"]["manifest_sha256"] = file_sha256(render_manifest_path)
    write_json(package_root / "publish_readiness_manifest.json", package)
    contract_receipt = run_contract_validator(
        manifest_path=package_root / "publish_readiness_manifest.json",
        intent="successor",
        contract_id="first-eight-longform-v1",
    )
    package["production_contract_receipt"] = {
        "path": contract_receipt.get("receipt_path", ""),
        "ok": contract_receipt.get("ok") is True,
        "contract_id": contract_receipt.get("contract_id", ""),
        "intent": contract_receipt.get("intent", ""),
        "youtube_action_allowed": contract_receipt.get("youtube_action_allowed") is True,
        "reads": contract_receipt.get("reads", {}),
    }
    upload_manifest["production_contract_receipt"] = package["production_contract_receipt"]
    if approve_unlisted_upload:
        action_receipt = run_contract_validator(
            manifest_path=package_root / "publish_readiness_manifest.json",
            intent="successor",
            contract_id="first-eight-longform-v1",
            youtube_action="unlisted_review_upload",
        )
        package["production_contract_action_receipt"] = {
            "path": action_receipt.get("receipt_path", ""),
            "ok": action_receipt.get("ok") is True,
            "contract_id": action_receipt.get("contract_id", ""),
            "intent": action_receipt.get("intent", ""),
            "youtube_action_requested": action_receipt.get("youtube_action_requested", ""),
            "youtube_action_allowed": action_receipt.get("youtube_action_allowed") is True,
            "reads": action_receipt.get("reads", {}),
        }
        upload_manifest["production_contract_action_receipt"] = package["production_contract_action_receipt"]
    write_json(package_root / "youtube_upload_manifest.json", upload_manifest)
    write_json(package_root / "publish_readiness_manifest.json", package)

    entry["publish_readiness_package"] = proof_manifest["publish_readiness_package"]
    entry["status"] = "publish_readiness_package_review_ready_pending_human_keep"
    entry["publish_ready"] = False
    entry["youtube_upload_ready"] = False
    entry["may_youtube_action"] = False
    entry["upload_allowed"] = False
    entry["upload_performed"] = False

    return {
        "episode_id": episode_id,
        "packet_path": str(package_root),
        "manifest_path": str(package_root / "publish_readiness_manifest.json"),
        "review_html_path": str(review_path),
        "review_url": package["publish_readiness_canonical_review_url"],
        "youtube_upload_manifest_path": str(package_root / "youtube_upload_manifest.json"),
        "blockers": blockers,
    }


def validate_package(summary: dict, port: int) -> dict:
    manifest_path = Path(summary["manifest_path"])
    manifest = read_json(manifest_path)
    package_root = manifest_path.parent
    review_path = package_root / manifest["primary_review_artifact"]["path"]
    mp4_path = package_root / manifest["media"]["final_mp4"]["path"]
    vtt_path = package_root / manifest["media"]["caption_vtt"]["path"]
    srt_path = package_root / manifest["media"]["caption_srt"]["path"]
    for path in [review_path, mp4_path, vtt_path, srt_path]:
        if not path.is_file():
            raise FileNotFoundError(path)
    review_status = http_status(local_url(review_path, port))
    mp4_range_status = http_status(local_url(mp4_path, port), "bytes=0-1023")
    reads = manifest["reads"]
    reads["html_media_refs_read"] = "pass_package_local_relative_media_refs_exist"
    reads["html_range_server_read"] = "pass_mp4_http_range_probe_206"
    reads["html_canonical_review_url_read"] = "pass_http_review_url_200"
    reads["html_native_video_scrub_read"] = "pass_native_video_controls_and_range_server_available"
    manifest["review_server"] = {
        "type": "byte_range_capable_local_http",
        "root": str(SERVER_ROOT),
        "port": port,
        "url": local_url(review_path, port),
        "review_probe_status": review_status,
        "mp4_range_probe_status": mp4_range_status,
    }
    write_json(manifest_path, manifest)
    return {
        "episode_id": summary["episode_id"],
        "review_status": review_status,
        "mp4_range_status": mp4_range_status,
        "html_range_server_read": reads["html_range_server_read"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--stamp", default=utc_stamp())
    parser.add_argument("--serve-only", action="store_true")
    parser.add_argument("--only", action="append", default=[], help="Episode id to build; may be repeated or comma-separated.")
    parser.add_argument(
        "--approve-unlisted-upload",
        action="store_true",
        help="Record explicit user approval for an unlisted review upload in the generated replacement packages.",
    )
    parser.add_argument(
        "--manifest-override",
        action="append",
        default=[],
        help="Override one selected rollout entry as episode_id=/absolute/path/to/rough_assembly_manifest.json.",
    )
    args = parser.parse_args()

    if args.serve_only:
        server = start_validation_server(SERVER_ROOT, args.port)
        print(
            json.dumps(
                {
                    "status": "serving",
                    "server_root": str(SERVER_ROOT),
                    "port": args.port,
                    "url_base": f"http://127.0.0.1:{args.port}/",
                },
                indent=2,
            ),
            flush=True,
        )
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            server.shutdown()
            server.server_close()
        return

    rollout = read_json(ROLLOUT_PATH)
    selected = parse_selected_episode_ids(args.only)
    overrides = parse_manifest_overrides(args.manifest_override)
    entries = rollout_entries_for_build(rollout, selected, overrides)
    summaries = [build_package(entry, args.stamp, args.port, args.approve_unlisted_upload) for entry in entries]
    if not selected and not overrides:
        write_json(ROLLOUT_PATH, rollout)

    server = start_validation_server(SERVER_ROOT, args.port)
    try:
        validation = [validate_package(summary, args.port) for summary in summaries]
    finally:
        server.shutdown()
        server.server_close()

    all_summary = {
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stamp": args.stamp,
        "server_root": str(SERVER_ROOT),
        "port": args.port,
        "count": len(summaries),
        "packages": summaries,
        "validation": validation,
        "upload_locks": {
            "may_youtube_action": False,
            "upload_allowed": False,
            "upload_performed": False,
            "public_release_ready": False,
        },
    }
    summary_path = EPISODES_ROOT / f"first_eight_longform_publish_readiness_packages_{args.stamp}.json"
    write_json(summary_path, all_summary)
    latest_path = EPISODES_ROOT / "first_eight_longform_publish_readiness_packages_latest.json"
    write_json(latest_path, all_summary)
    print(json.dumps({"summary_path": str(summary_path), "latest_path": str(latest_path), **all_summary}, indent=2))


if __name__ == "__main__":
    main()
